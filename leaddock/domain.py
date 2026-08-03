from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LeadDockError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


@dataclass(frozen=True)
class Booking:
    id: str
    lead_id: str
    start_utc: str
    end_utc: str
    timezone: str
    idempotency_key: str


class LocalCrmAdapter:
    """Provider-neutral CRM contract with deterministic field mapping."""

    def __init__(self) -> None:
        self.records: dict[str, dict[str, Any]] = {}

    def upsert(self, lead: dict[str, Any]) -> dict[str, Any]:
        crm_id = f"crm_{lead['id'][5:]}"
        record = {
            "id": crm_id,
            "external_key": lead["identity_key"],
            "fields": {
                "full_name": lead["name"],
                "email_address": lead["email"],
                "phone_e164ish": lead["phone"],
                "organization": lead["company"],
                "qualification_tier": lead["qualification"]["tier"],
                "qualification_score": lead["qualification"]["score"],
            },
        }
        self.records[lead["identity_key"]] = record
        return deepcopy(record)


class LocalCalendarAdapter:
    """UTC-backed booking contract with collision and idempotency protection."""

    def __init__(self) -> None:
        self.bookings: dict[str, Booking] = {}
        self.by_idempotency: dict[str, Booking] = {}

    @staticmethod
    def parse_slot(value: str) -> datetime:
        try:
            slot = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise LeadDockError("invalid_slot", "slot_start must be ISO 8601") from exc
        if slot.tzinfo is None:
            raise LeadDockError("invalid_slot", "slot_start must include a UTC offset")
        if slot.minute not in (0, 30) or slot.second or slot.microsecond:
            raise LeadDockError("invalid_slot", "appointments start on a 30-minute boundary")
        return slot.astimezone(timezone.utc)

    def book(self, lead_id: str, slot_start: str, tz_name: str) -> tuple[Booking, bool]:
        start = self.parse_slot(slot_start)
        end = start + timedelta(minutes=30)
        key = f"{lead_id}:{start.isoformat()}"
        if key in self.by_idempotency:
            return self.by_idempotency[key], True
        for existing in self.bookings.values():
            e_start = datetime.fromisoformat(existing.start_utc)
            e_end = datetime.fromisoformat(existing.end_utc)
            if start < e_end and end > e_start:
                raise LeadDockError("slot_conflict", "the selected slot is already booked", 409)
        booking = Booking(
            id=f"book_{hashlib.sha1(key.encode()).hexdigest()[:10]}",
            lead_id=lead_id,
            start_utc=start.isoformat(),
            end_utc=end.isoformat(),
            timezone=tz_name,
            idempotency_key=key,
        )
        self.bookings[booking.id] = booking
        self.by_idempotency[key] = booking
        return booking, False

    def availability(self, tz_name: str) -> list[dict[str, str]]:
        try:
            tz = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError as exc:
            raise LeadDockError("invalid_timezone", "unknown IANA timezone") from exc
        base = datetime(2026, 8, 3, 9, 0, tzinfo=ZoneInfo("Europe/Vilnius"))
        slots = []
        for day in range(3):
            for hour in (9, 10, 11, 14, 15):
                local = base.replace(hour=hour) + timedelta(days=day)
                utc = local.astimezone(timezone.utc)
                if any(datetime.fromisoformat(b.start_utc) == utc for b in self.bookings.values()):
                    continue
                slots.append({"start": utc.isoformat(), "label": local.astimezone(tz).strftime("%a %d %b · %H:%M"), "timezone": tz_name})
        return slots


class LocalMessagingAdapter:
    def send(self, lead: dict[str, Any], booking: Booking, attempt: int) -> dict[str, Any]:
        if "+fail" in lead["email"] and attempt <= 3:
            raise RuntimeError("injected local messaging outage")
        return {
            "id": f"msg_{hashlib.sha1((booking.id + str(attempt)).encode()).hexdigest()[:10]}",
            "channel": "email-contract",
            "recipient": lead["email"],
            "attempt": attempt,
            "status": "delivered",
        }


class LeadDockService:
    """Deterministic lead-to-booking pipeline used by HTTP, tests, and the UI."""

    def __init__(self, seed: bool = False) -> None:
        self.leads: dict[str, dict[str, Any]] = {}
        self.identity_index: dict[str, str] = {}
        self.crm = LocalCrmAdapter()
        self.calendar = LocalCalendarAdapter()
        self.messaging = LocalMessagingAdapter()
        self.dead_letters: dict[str, dict[str, Any]] = {}
        self.audit: list[dict[str, Any]] = []
        self._event_no = 0
        if seed:
            self.seed_demo()

    def _record(self, event: str, subject: str, **details: Any) -> None:
        self._event_no += 1
        self.audit.append({"seq": self._event_no, "event": event, "subject": subject, "details": details})

    @staticmethod
    def _normalize(payload: dict[str, Any]) -> dict[str, Any]:
        required = ("name", "email", "company", "need", "budget", "company_size", "timezone")
        missing = [key for key in required if payload.get(key) in (None, "")]
        if missing:
            raise LeadDockError("invalid_lead", f"missing required fields: {', '.join(missing)}")
        email = str(payload["email"]).strip().lower()
        if not EMAIL.match(email):
            raise LeadDockError("invalid_email", "email is not valid")
        phone = re.sub(r"[^0-9+]", "", str(payload.get("phone", "")))
        try:
            budget = int(payload["budget"])
            size = int(payload["company_size"])
        except (TypeError, ValueError) as exc:
            raise LeadDockError("invalid_number", "budget and company_size must be integers") from exc
        if budget < 0 or size < 1:
            raise LeadDockError("invalid_number", "budget must be nonnegative and company_size positive")
        tz_name = str(payload["timezone"])
        try:
            ZoneInfo(tz_name)
        except ZoneInfoNotFoundError as exc:
            raise LeadDockError("invalid_timezone", "unknown IANA timezone") from exc
        return {
            "name": str(payload["name"]).strip(),
            "email": email,
            "phone": phone,
            "company": str(payload["company"]).strip(),
            "need": str(payload["need"]).strip(),
            "budget": budget,
            "company_size": size,
            "timeline": str(payload.get("timeline", "flexible")).strip().lower(),
            "timezone": tz_name,
        }

    @staticmethod
    def qualify(lead: dict[str, Any]) -> dict[str, Any]:
        budget = 35 if lead["budget"] >= 10_000 else 25 if lead["budget"] >= 5_000 else 15 if lead["budget"] >= 2_000 else 5
        size = 25 if lead["company_size"] >= 50 else 18 if lead["company_size"] >= 10 else 8
        need = 25 if re.search(r"automation|integration|booking|crm|agent|ai", lead["need"], re.I) else 10
        timeline = 15 if re.search(r"urgent|30|month|now", lead["timeline"], re.I) else 5
        score = budget + size + need + timeline
        tier = "hot" if score >= 75 else "warm" if score >= 50 else "cold"
        return {"score": score, "tier": tier, "reasons": {"budget": budget, "company_size": size, "need": need, "timeline": timeline}}

    def intake(self, payload: dict[str, Any]) -> dict[str, Any]:
        clean = self._normalize(payload)
        identity = clean["email"] or clean["phone"]
        if identity in self.identity_index:
            lead = self.leads[self.identity_index[identity]]
            self._record("lead.duplicate", lead["id"], identity_key=identity)
            return {"duplicate": True, "lead": deepcopy(lead)}
        lead_id = f"lead_{hashlib.sha1(identity.encode()).hexdigest()[:10]}"
        qualification = self.qualify(clean)
        status = "needs_approval" if qualification["tier"] in ("hot", "warm") else "nurture"
        lead = {"id": lead_id, "identity_key": identity, **clean, "qualification": qualification, "status": status, "crm": None, "booking": None, "handoff": None}
        self.leads[lead_id] = lead
        self.identity_index[identity] = lead_id
        self._record("lead.accepted", lead_id, score=qualification["score"], tier=qualification["tier"], status=status)
        return {"duplicate": False, "lead": deepcopy(lead)}

    def approve(self, lead_id: str, slot_start: str) -> dict[str, Any]:
        lead = self._lead(lead_id)
        if lead["status"] == "nurture":
            raise LeadDockError("approval_not_allowed", "cold leads require nurture rather than booking", 409)
        if lead["status"] == "rejected":
            raise LeadDockError("approval_not_allowed", "rejected lead cannot be booked", 409)
        crm = self.crm.upsert(lead)
        self._record("crm.upserted", lead_id, crm_id=crm["id"], adapter="local-fake")
        booking, replayed = self.calendar.book(lead_id, slot_start, lead["timezone"])
        self._record("booking.replayed" if replayed else "booking.created", lead_id, booking_id=booking.id, slot=booking.start_utc)
        lead["crm"] = crm
        lead["booking"] = booking.__dict__
        lead["status"] = "booked"
        if not lead["handoff"]:
            self._deliver(lead, booking)
        return {"replayed": replayed, "lead": deepcopy(lead)}

    def reject(self, lead_id: str, reason: str) -> dict[str, Any]:
        lead = self._lead(lead_id)
        if lead["booking"]:
            raise LeadDockError("reject_not_allowed", "a booked lead cannot be rejected", 409)
        lead["status"] = "rejected"
        self._record("lead.rejected", lead_id, reason=reason or "not specified")
        return deepcopy(lead)

    def _deliver(self, lead: dict[str, Any], booking: Booking, start_attempt: int = 1) -> None:
        last_error = ""
        for attempt in range(start_attempt, 4):
            try:
                receipt = self.messaging.send(lead, booking, attempt)
                lead["handoff"] = receipt
                self._record("handoff.delivered", lead["id"], message_id=receipt["id"], attempt=attempt)
                return
            except RuntimeError as exc:
                last_error = str(exc)
                self._record("handoff.retry", lead["id"], attempt=attempt, error=last_error)
        dlq_id = f"dlq_{hashlib.sha1(booking.id.encode()).hexdigest()[:10]}"
        letter = {"id": dlq_id, "lead_id": lead["id"], "booking_id": booking.id, "attempts": 3, "error": last_error, "status": "pending"}
        self.dead_letters[dlq_id] = letter
        lead["handoff"] = {"status": "dead_letter", "id": dlq_id}
        self._record("handoff.dead_lettered", lead["id"], dead_letter_id=dlq_id)

    def replay_dead_letter(self, dlq_id: str) -> dict[str, Any]:
        if dlq_id not in self.dead_letters:
            raise LeadDockError("not_found", "dead letter not found", 404)
        letter = self.dead_letters[dlq_id]
        lead = self._lead(letter["lead_id"])
        booking = self.calendar.bookings[letter["booking_id"]]
        receipt = self.messaging.send(lead, booking, 4)
        letter["status"] = "replayed"
        lead["handoff"] = receipt
        self._record("handoff.replayed", lead["id"], dead_letter_id=dlq_id, message_id=receipt["id"])
        return {"dead_letter": deepcopy(letter), "lead": deepcopy(lead)}

    def _lead(self, lead_id: str) -> dict[str, Any]:
        if lead_id not in self.leads:
            raise LeadDockError("not_found", "lead not found", 404)
        return self.leads[lead_id]

    def state(self, tz_name: str = "Europe/Vilnius") -> dict[str, Any]:
        return {
            "leads": deepcopy(list(self.leads.values())),
            "availability": self.calendar.availability(tz_name),
            "bookings": [b.__dict__ for b in self.calendar.bookings.values()],
            "dead_letters": deepcopy(list(self.dead_letters.values())),
            "audit": deepcopy(self.audit),
            "boundaries": ["local deterministic adapters", "no named SaaS provider claim", "no external credentials"],
        }

    def seed_demo(self) -> None:
        examples = [
            {"name": "Mira Chen", "email": "mira@northstar.example", "phone": "+370 600 10001", "company": "Northstar Labs", "need": "CRM and booking automation", "budget": 12000, "company_size": 64, "timeline": "within 30 days", "timezone": "Europe/Vilnius"},
            {"name": "Jon Bell", "email": "jon@fieldnote.example", "phone": "+44 7700 900111", "company": "Fieldnote", "need": "lead intake integration", "budget": 6000, "company_size": 18, "timeline": "this month", "timezone": "Europe/London"},
            {"name": "Asha Rao", "email": "asha@orbit.example", "phone": "+1 202 555 0139", "company": "Orbit Studio", "need": "website refresh", "budget": 900, "company_size": 3, "timeline": "flexible", "timezone": "America/New_York"},
            {"name": "Failure Fixture", "email": "ops+fail@relay.example", "phone": "+370 600 10004", "company": "Retry Works", "need": "booking automation", "budget": 9000, "company_size": 25, "timeline": "urgent", "timezone": "Europe/Vilnius"},
        ]
        for item in examples:
            self.intake(item)
