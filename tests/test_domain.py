import unittest

from leaddock import LeadDockError, LeadDockService


HOT = {
    "name": "Mira Chen", "email": "MIRA@EXAMPLE.COM", "phone": "+370 600 10001",
    "company": "Northstar", "need": "CRM and booking automation", "budget": 12000,
    "company_size": 64, "timeline": "within 30 days", "timezone": "Europe/Vilnius",
}


class LeadDockDomainTests(unittest.TestCase):
    def setUp(self):
        self.svc = LeadDockService()

    def test_intake_normalizes_and_qualifies(self):
        result = self.svc.intake(HOT)
        self.assertFalse(result["duplicate"])
        self.assertEqual(result["lead"]["email"], "mira@example.com")
        self.assertEqual(result["lead"]["qualification"]["tier"], "hot")
        self.assertEqual(result["lead"]["status"], "needs_approval")

    def test_duplicate_intake_is_idempotent(self):
        first = self.svc.intake(HOT)
        second = self.svc.intake({**HOT, "email": "mira@example.com", "budget": 1})
        self.assertTrue(second["duplicate"])
        self.assertEqual(first["lead"]["id"], second["lead"]["id"])
        self.assertEqual(len(self.svc.leads), 1)

    def test_invalid_email_is_rejected(self):
        with self.assertRaisesRegex(LeadDockError, "email is not valid"):
            self.svc.intake({**HOT, "email": "bad"})

    def test_missing_input_is_rejected(self):
        with self.assertRaisesRegex(LeadDockError, "missing required fields"):
            self.svc.intake({"name": "Only"})

    def test_invalid_timezone_is_rejected(self):
        with self.assertRaisesRegex(LeadDockError, "unknown IANA timezone"):
            self.svc.intake({**HOT, "timezone": "Mars/Olympus"})

    def test_cold_lead_goes_to_nurture(self):
        result = self.svc.intake({**HOT, "email": "cold@example.com", "need": "website", "budget": 100, "company_size": 1, "timeline": "later"})
        self.assertEqual(result["lead"]["qualification"]["tier"], "cold")
        self.assertEqual(result["lead"]["status"], "nurture")

    def test_approve_upserts_crm_books_and_hands_off(self):
        lead = self.svc.intake(HOT)["lead"]
        slot = self.svc.state()["availability"][0]["start"]
        result = self.svc.approve(lead["id"], slot)
        self.assertEqual(result["lead"]["status"], "booked")
        self.assertEqual(result["lead"]["crm"]["fields"]["qualification_tier"], "hot")
        self.assertEqual(result["lead"]["handoff"]["status"], "delivered")

    def test_repeating_approval_returns_same_booking(self):
        lead = self.svc.intake(HOT)["lead"]
        slot = self.svc.state()["availability"][0]["start"]
        first = self.svc.approve(lead["id"], slot)
        second = self.svc.approve(lead["id"], slot)
        self.assertTrue(second["replayed"])
        self.assertEqual(first["lead"]["booking"]["id"], second["lead"]["booking"]["id"])

    def test_double_booking_is_blocked(self):
        one = self.svc.intake(HOT)["lead"]
        two = self.svc.intake({**HOT, "email": "two@example.com"})["lead"]
        slot = self.svc.state()["availability"][0]["start"]
        self.svc.approve(one["id"], slot)
        with self.assertRaisesRegex(LeadDockError, "already booked"):
            self.svc.approve(two["id"], slot)

    def test_slot_requires_offset_and_half_hour_boundary(self):
        lead = self.svc.intake(HOT)["lead"]
        with self.assertRaisesRegex(LeadDockError, "UTC offset"):
            self.svc.approve(lead["id"], "2026-08-03T09:00:00")
        with self.assertRaisesRegex(LeadDockError, "30-minute"):
            self.svc.approve(lead["id"], "2026-08-03T09:17:00+03:00")

    def test_message_failure_retries_then_dead_letters_and_replays(self):
        lead = self.svc.intake({**HOT, "email": "ops+fail@example.com"})["lead"]
        slot = self.svc.state()["availability"][0]["start"]
        booked = self.svc.approve(lead["id"], slot)["lead"]
        self.assertEqual(booked["handoff"]["status"], "dead_letter")
        dlq_id = booked["handoff"]["id"]
        replay = self.svc.replay_dead_letter(dlq_id)
        self.assertEqual(replay["lead"]["handoff"]["status"], "delivered")
        self.assertEqual(replay["dead_letter"]["status"], "replayed")

    def test_cold_lead_cannot_be_approved(self):
        lead = self.svc.intake({**HOT, "email": "cold@example.com", "need": "website", "budget": 1, "company_size": 1, "timeline": "later"})["lead"]
        with self.assertRaisesRegex(LeadDockError, "nurture"):
            self.svc.approve(lead["id"], "2026-08-03T09:00:00+03:00")

    def test_reject_branch_is_audited(self):
        lead = self.svc.intake(HOT)["lead"]
        rejected = self.svc.reject(lead["id"], "outside scope")
        self.assertEqual(rejected["status"], "rejected")
        self.assertEqual(self.svc.audit[-1]["event"], "lead.rejected")

    def test_state_exposes_honest_boundary(self):
        self.assertIn("no named SaaS provider claim", self.svc.state()["boundaries"])


if __name__ == "__main__":
    unittest.main()
