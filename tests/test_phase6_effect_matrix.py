"""Phase 6 effect oracle for LeadDock.

Same six observables as Relay's matrix — final durable state, target apply
count, target request count, ordered attempt classifications, receipt
completeness, and exit outcome — but exercised through the provider's
``DeliveryExecutor`` loop rather than the bare store, because LeadDock's
handoff retry has always been intra-call.

The "target" is the local messaging contract. It is the external system in this
composition, so it deliberately survives a simulated worker restart: only the
LeadDock process is recreated, never the thing that received the effect.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from deliveryguard import ActionState

from leaddock.domain import LeadDockService, LocalMessagingAdapter

HOT = {
    "name": "Mira Chen",
    "email": "mira@example.com",
    "phone": "+370 600 10001",
    "company": "Northstar",
    "need": "CRM and booking automation",
    "budget": 12000,
    "company_size": 64,
    "timeline": "within 30 days",
    "timezone": "Europe/Vilnius",
}


class ScriptedMessaging(LocalMessagingAdapter):
    """The messaging contract with an injectable fault script."""

    def __init__(self, script=None, default="apply"):
        super().__init__()
        self.script = list(script or [])
        self.default = default

    def send(self, lead, booking, *, idempotency_key):
        behaviour = self.script.pop(0) if self.script else self.default
        if behaviour == "crash_before_send":
            # BaseException: never normalised into a receipt, so the durable
            # row stays `running` exactly as an abrupt kill would leave it.
            raise KeyboardInterrupt("worker killed before the handoff was sent")
        if behaviour == "outage":
            self.requests.append({"idempotency_key": idempotency_key, "lead_id": lead["id"]})
            raise RuntimeError("scripted messaging outage")
        result = super().send(lead, booking, idempotency_key=idempotency_key)
        if behaviour == "crash_after_apply":
            raise KeyboardInterrupt("worker killed after the handoff was applied")
        return result


class Phase6EffectMatrix(unittest.TestCase):
    def setUp(self):
        self.db = Path(tempfile.mkdtemp(prefix="leaddock-phase6-")) / "deliveries.sqlite3"
        self.target = ScriptedMessaging()

    def service(self, script=None, default="apply") -> LeadDockService:
        service = LeadDockService(delivery_db=self.db)
        self.target.script = list(script or [])
        self.target.default = default
        service.messaging = self.target
        return service

    def book(self, service: LeadDockService, email: str = "mira@example.com"):
        lead = service.intake({**HOT, "email": email})["lead"]
        slot = service.state()["availability"][0]["start"]
        return lead, slot

    # -- observation helpers ------------------------------------------

    def record_for(self, service: LeadDockService, lead_id: str, booking_id: str):
        key = LeadDockService.handoff_key(lead_id, booking_id)
        action = service.deliveries.get_by_key(key)
        return action, service.deliveries.attempts(action.id)

    def assert_receipts_complete(self, attempts):
        for attempt in attempts:
            self.assertTrue(attempt.classification)
            self.assertIsInstance(attempt.retryable, bool)
            self.assertGreaterEqual(attempt.latency_ms, 0)
            self.assertTrue(attempt.request)
            self.assertTrue(attempt.correlation_id)
            self.assertTrue(attempt.response or attempt.error)

    def assert_case(
        self,
        action,
        attempts,
        *,
        final_state,
        apply_count,
        request_count,
        classifications,
        attempt_count,
        cycle,
    ):
        self.assertEqual(action.state, final_state)
        self.assertEqual(self.target.apply_count, apply_count)
        self.assertEqual(self.target.request_count, request_count)
        self.assertEqual(
            [attempt.classification.value for attempt in attempts], classifications
        )
        self.assertEqual(action.attempt_count, attempt_count)
        self.assertEqual(action.cycle, cycle)
        self.assert_receipts_complete(attempts)
        # One effect identity across every attempt is what makes a duplicate
        # apply impossible rather than merely unlikely.
        self.assertLessEqual(
            len({item["idempotency_key"] for item in self.target.requests}), 1
        )

    # -- case 1 --------------------------------------------------------

    def test_case_1_outage_before_apply_then_success(self):
        service = self.service(script=["outage"])
        lead, slot = self.book(service)
        booked = service.approve(lead["id"], slot)["lead"]

        self.assertEqual(booked["handoff"]["status"], "delivered")
        action, attempts = self.record_for(service, lead["id"], booked["booking"]["id"])
        self.assert_case(
            action,
            attempts,
            final_state=ActionState.DELIVERED,
            apply_count=1,
            request_count=2,
            classifications=["network_error", "success"],
            attempt_count=2,
            cycle=1,
        )

    # -- case 2 --------------------------------------------------------

    def test_case_2_duplicate_submit_adds_no_effect(self):
        service = self.service()
        lead, slot = self.book(service)
        booked = service.approve(lead["id"], slot)["lead"]
        booking_id = booked["booking"]["id"]

        # Product layer: re-approving is a no-op for the reviewer.
        again = service.approve(lead["id"], slot)
        self.assertTrue(again["replayed"])

        # Provider layer: the identical key and payload return the durable
        # record without touching the target.
        key = LeadDockService.handoff_key(lead["id"], booking_id)
        record = service.executor.deliver(
            idempotency_key=key,
            destination="messaging:local-email-contract",
            payload={
                "lead_id": lead["id"],
                "booking_id": booking_id,
                "recipient": lead["email"],
            },
            correlation_id=lead["id"],
        )
        self.assertEqual(record.state, ActionState.DELIVERED)

        action, attempts = self.record_for(service, lead["id"], booking_id)
        self.assert_case(
            action,
            attempts,
            final_state=ActionState.DELIVERED,
            apply_count=1,
            request_count=1,
            classifications=["success"],
            attempt_count=1,
            cycle=1,
        )

    # -- case 3 (load bearing) -----------------------------------------

    def test_case_3_crash_after_effect_before_receipt(self):
        """The restart must not re-apply an effect the target already took."""

        crashing = self.service(script=["crash_after_apply"])
        lead, slot = self.book(crashing)
        with self.assertRaises(KeyboardInterrupt):
            crashing.approve(lead["id"], slot)

        booking_id = next(iter(crashing.calendar.bookings))
        action, _ = self.record_for(crashing, lead["id"], booking_id)
        self.assertEqual(action.state, ActionState.RUNNING)
        self.assertEqual(self.target.apply_count, 1)
        self.assertEqual(self.target.request_count, 1)

        # Only the worker restarts. The target — the external system — does
        # not, so it still recognises the idempotency key.
        restarted = self.service()
        lead2, slot2 = self.book(restarted)
        self.assertEqual(lead2["id"], lead["id"], "identity must survive the restart")
        booked = restarted.approve(lead2["id"], slot2)["lead"]
        self.assertEqual(booked["handoff"]["status"], "delivered")

        action, attempts = self.record_for(restarted, lead["id"], booking_id)
        self.assert_case(
            action,
            attempts,
            final_state=ActionState.ALREADY_APPLIED,
            apply_count=1,
            request_count=2,
            classifications=["worker_interrupted", "already_applied"],
            attempt_count=2,
            cycle=1,
        )

    # -- case 4 --------------------------------------------------------

    def test_case_4_crash_before_request_reaches_target(self):
        crashing = self.service(script=["crash_before_send"])
        lead, slot = self.book(crashing)
        with self.assertRaises(KeyboardInterrupt):
            crashing.approve(lead["id"], slot)

        booking_id = next(iter(crashing.calendar.bookings))
        action, _ = self.record_for(crashing, lead["id"], booking_id)
        self.assertEqual(action.state, ActionState.RUNNING)
        self.assertEqual(self.target.request_count, 0)

        restarted = self.service()
        lead2, slot2 = self.book(restarted)
        booked = restarted.approve(lead2["id"], slot2)["lead"]
        self.assertEqual(booked["handoff"]["status"], "delivered")

        action, attempts = self.record_for(restarted, lead["id"], booking_id)
        self.assert_case(
            action,
            attempts,
            final_state=ActionState.DELIVERED,
            apply_count=1,
            request_count=1,
            classifications=["worker_interrupted", "success"],
            attempt_count=2,
            cycle=1,
        )

    # -- cases 5, 6 and 7 ----------------------------------------------

    def test_cases_5_6_7_exhaustion_then_terminal_then_replay(self):
        service = self.service(script=["outage", "outage", "outage"])
        lead, slot = self.book(service)

        # Case 5: the provider's bounded loop spends the whole budget in one
        # approval, which is LeadDock's own product cadence.
        booked = service.approve(lead["id"], slot)["lead"]
        booking_id = booked["booking"]["id"]
        self.assertEqual(booked["handoff"]["status"], "dead_letter")
        dlq_id = booked["handoff"]["id"]

        action, attempts = self.record_for(service, lead["id"], booking_id)
        self.assert_case(
            action,
            attempts,
            final_state=ActionState.DEAD_LETTER,
            apply_count=0,
            request_count=3,
            classifications=["network_error", "network_error", "network_error"],
            attempt_count=3,
            cycle=1,
        )
        self.assertTrue(action.last_error, "an exhausted action needs a failure receipt")
        self.assertEqual(service.dead_letters[dlq_id]["status"], "pending")

        # Case 6: dead letter is terminal — re-entering fires nothing.
        key = LeadDockService.handoff_key(lead["id"], booking_id)
        repeated = service.executor.deliver(
            idempotency_key=key,
            destination="messaging:local-email-contract",
            payload={
                "lead_id": lead["id"],
                "booking_id": booking_id,
                "recipient": lead["email"],
            },
            correlation_id=lead["id"],
        )
        self.assertEqual(repeated.state, ActionState.DEAD_LETTER)
        action, attempts = self.record_for(service, lead["id"], booking_id)
        self.assert_case(
            action,
            attempts,
            final_state=ActionState.DEAD_LETTER,
            apply_count=0,
            request_count=3,
            classifications=["network_error", "network_error", "network_error"],
            attempt_count=3,
            cycle=1,
        )

        # Case 7: replay opens a new cycle and succeeds exactly once.
        replayed = service.replay_dead_letter(dlq_id)
        self.assertEqual(replayed["lead"]["handoff"]["status"], "delivered")
        self.assertEqual(replayed["dead_letter"]["status"], "replayed")

        action, attempts = self.record_for(service, lead["id"], booking_id)
        self.assert_case(
            action,
            attempts,
            final_state=ActionState.DELIVERED,
            apply_count=1,
            request_count=4,
            classifications=[
                "network_error",
                "network_error",
                "network_error",
                "success",
            ],
            attempt_count=1,
            cycle=2,
        )
        self.assertEqual(attempts[-1].cycle, 2)
        self.assertEqual(attempts[-1].cycle_attempt, 1)

    # -- retry theater control -----------------------------------------

    def test_regenerated_key_would_duplicate_the_effect(self):
        """Show the oracle can actually observe a duplicate effect."""

        service = self.service()
        lead, slot = self.book(service)
        booked = service.approve(lead["id"], slot)["lead"]
        booking = service.calendar.bookings[booked["booking"]["id"]]

        # A composition that re-derived its key each attempt would look like
        # this to the target: a second, unrecognised effect.
        self.target.send(
            service.leads[lead["id"]], booking, idempotency_key="regenerated-key-0001"
        )
        self.assertEqual(self.target.apply_count, 2)
        self.assertEqual(self.target.request_count, 2)


if __name__ == "__main__":
    unittest.main()
