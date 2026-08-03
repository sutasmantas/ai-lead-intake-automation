# LeadDock cover-letter evidence

Use only claims supported below. The project is a provider-neutral MRE, not a
named SaaS implementation.

| Safe claim | Evidence |
| --- | --- |
| Built a lead-to-booking automation with deterministic validation, deduplication, qualification, approval, CRM upsert, booking, and handoff | `python -m unittest discover -s tests -v`; `leaddock/domain.py`; browser working-state screenshot `docs/leaddock-1440.png` |
| Prevented duplicate leads and double-booked calendar slots with idempotency keys and UTC-backed collision checks | domain tests `test_duplicate_intake_is_idempotent`, `test_repeating_approval_returns_same_booking`, and `test_double_booking_is_blocked` |
| Implemented bounded messaging retry, dead-letter handling, replay, and an auditable receipt trail | domain failure/replay test; exercised browser artifact `docs/leaddock-failure-replay.png` |
| Delivered an importable n8n workflow for intake and approval orchestration | `docker run --rm -v "${PWD}:/data" n8nio/n8n:2.30.5 import:workflow --input=/data/workflows/leaddock-intake-booking.json` -> `Successfully imported 1 workflow.` |
| Created generic CRM, calendar, and messaging extension contracts with a no-key local demo | `LocalCrmAdapter`, `LocalCalendarAdapter`, `LocalMessagingAdapter`; HTTP tests and `python -m leaddock.server` |

## Claim limits

Do not claim HubSpot, Salesforce, Calendly, Google Calendar, Twilio, WhatsApp,
or another named integration. The upstream templates contain named nodes, but
LeadDock's exercised path calls tested local contracts only. Do not claim a
hosted n8n deployment, production persistence, distributed locking,
authentication, multi-tenancy, measured lead-conversion improvement, or client
usage.

## Verification snapshot

- date: 2026-08-01
- Python: 3.11+
- focused suite: 22 tests passed
- n8n import runtime: Docker image `n8nio/n8n:2.30.5`
- browser flow: seeded Retry Works lead -> approval -> local CRM receipt -> UTC
  booking -> 3 failed handoff attempts -> dead letter -> replay -> delivered
- rendered viewports: 1440x1000, 1024x900, and 390x844
