from __future__ import annotations

import unittest
from datetime import datetime

from leaddock.contracts import LeadDockError, LocalCalendarAdapter, LocalCrmAdapter

LEAD = {
    "id": "lead_1234567890",
    "identity_key": "mira@example.test",
    "name": "Mira Chen",
    "email": "mira@example.test",
    "phone": "+37060010001",
    "company": "Northstar",
    "qualification": {"tier": "hot", "score": 92},
}


class ContractTests(unittest.TestCase):
    def test_slot_requires_offset(self) -> None:
        with self.assertRaisesRegex(LeadDockError, "UTC offset"):
            LocalCalendarAdapter.parse_slot("2026-08-03T09:00:00")

    def test_slot_requires_half_hour_boundary(self) -> None:
        with self.assertRaisesRegex(LeadDockError, "30-minute"):
            LocalCalendarAdapter.parse_slot("2026-08-03T09:17:00+03:00")

    def test_repeated_booking_replays_same_record(self) -> None:
        calendar = LocalCalendarAdapter()
        slot = "2026-08-03T06:00:00+00:00"
        first, first_replay = calendar.book("lead_one", slot, "Europe/Vilnius")
        second, second_replay = calendar.book("lead_one", slot, "Europe/Vilnius")
        self.assertFalse(first_replay)
        self.assertTrue(second_replay)
        self.assertEqual(first, second)
        self.assertEqual(len(calendar.bookings), 1)

    def test_overlapping_booking_is_refused(self) -> None:
        calendar = LocalCalendarAdapter()
        calendar.book("lead_one", "2026-08-03T06:00:00+00:00", "Europe/Vilnius")
        with self.assertRaisesRegex(LeadDockError, "already booked"):
            calendar.book("lead_two", "2026-08-03T06:00:00+00:00", "Europe/Vilnius")

    def test_adjacent_booking_does_not_overlap(self) -> None:
        calendar = LocalCalendarAdapter()
        first, _ = calendar.book(
            "lead_one", "2026-08-03T06:00:00+00:00", "Europe/Vilnius"
        )
        second, _ = calendar.book(
            "lead_two", "2026-08-03T06:30:00+00:00", "Europe/Vilnius"
        )
        self.assertEqual(
            datetime.fromisoformat(first.end_utc),
            datetime.fromisoformat(second.start_utc),
        )

    def test_booking_duration_is_thirty_minutes(self) -> None:
        booking, _ = LocalCalendarAdapter().book(
            "lead_one", "2026-08-03T06:00:00+00:00", "Europe/Vilnius"
        )
        duration = datetime.fromisoformat(booking.end_utc) - datetime.fromisoformat(
            booking.start_utc
        )
        self.assertEqual(duration.total_seconds(), 30 * 60)

    def test_availability_is_timezone_labelled_and_excludes_booking(self) -> None:
        calendar = LocalCalendarAdapter()
        before = calendar.availability("America/New_York")
        calendar.book("lead_one", before[0]["start"], "America/New_York")
        after = calendar.availability("America/New_York")
        self.assertEqual(len(before), 15)
        self.assertEqual(len(after), 14)
        self.assertNotIn(before[0]["start"], {slot["start"] for slot in after})
        self.assertEqual(before[0]["timezone"], "America/New_York")
        self.assertTrue(before[0]["label"].endswith("02:00"))

    def test_crm_mapping_is_stable_and_defensively_copied(self) -> None:
        crm = LocalCrmAdapter()
        result = crm.upsert(LEAD)
        self.assertEqual(result["external_key"], LEAD["identity_key"])
        self.assertEqual(result["fields"]["full_name"], LEAD["name"])
        result["fields"]["full_name"] = "mutated consumer value"
        self.assertEqual(
            crm.records[LEAD["identity_key"]]["fields"]["full_name"], LEAD["name"]
        )


if __name__ == "__main__":
    unittest.main()
