"""Provider-neutral local CRM and appointment-booking contracts.

These deterministic adapters are the credential-free boundary used by
LeadDock and external portfolio consumers. They deliberately do not claim a
named CRM, calendar service, network transport, or production persistence.
"""

from __future__ import annotations

import hashlib
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class LeadDockError(ValueError):
    """Domain error with a stable code and HTTP-oriented status."""

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
            raise LeadDockError(
                "invalid_slot", "appointments start on a 30-minute boundary"
            )
        return slot.astimezone(timezone.utc)

    def book(self, lead_id: str, slot_start: str, tz_name: str) -> tuple[Booking, bool]:
        start = self.parse_slot(slot_start)
        end = start + timedelta(minutes=30)
        key = f"{lead_id}:{start.isoformat()}"
        if key in self.by_idempotency:
            return self.by_idempotency[key], True
        for existing in self.bookings.values():
            existing_start = datetime.fromisoformat(existing.start_utc)
            existing_end = datetime.fromisoformat(existing.end_utc)
            if start < existing_end and end > existing_start:
                raise LeadDockError(
                    "slot_conflict", "the selected slot is already booked", 409
                )
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
                if any(
                    datetime.fromisoformat(booking.start_utc) == utc
                    for booking in self.bookings.values()
                ):
                    continue
                slots.append(
                    {
                        "start": utc.isoformat(),
                        "label": local.astimezone(tz).strftime("%a %d %b · %H:%M"),
                        "timezone": tz_name,
                    }
                )
        return slots


__all__ = ["Booking", "LeadDockError", "LocalCalendarAdapter", "LocalCrmAdapter"]
