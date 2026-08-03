# LeadDock project start

## 1. Restart boundary

- repository: `portfolio_demos/lead_dock`
- baseline branch and commit: upstream `main` at `01383a9419a1b72cff553ec887501b9d82907be9`
- implementation branch: `agent/lead-dock-mre`
- assigned isolated worktree: `portfolio_demos/worktrees/lead_dock_mre`
- owner/session: current Codex session
- repositories/worktrees that are read-only: every other portfolio repository; ContextSidecar is owned and completed by another agent and must not be touched
- exact next action: implement the deterministic domain contracts before the UI

Never share this worktree or switch its branch.

## 2. Client outcome and non-duplication

- one client-purchased outcome this project proves: a web lead is validated,
  deduplicated, qualified, approved, upserted through a CRM contract, booked in
  a valid timezone-aware slot, and handed off with retry and audit evidence;
- existing portfolio evidence closest to it: Relay supplies governed actions,
  retries, receipts, and approval concepts;
- genuinely new mechanism/deliverable: importable n8n lead-intake workflow plus
  reusable CRM, availability, booking, and outbound-handoff contracts;
- coverage reason: this creates direct lead-to-booking RevOps evidence instead
  of implying that a support workflow is also a sales/booking implementation.

## 3. GitHub foundation comparison

License was deliberately not researched or used as a selection factor. These
are private working projects and the user explicitly ruled license work out.

| Candidate | Repository | Activity/version checked | Central behavior reusable for this MRE | Adaptation cost/risk | Decision |
| --- | --- | --- | --- | --- | --- |
| AmplifyAutomation n8n templates | `https://github.com/AmplifyAutomation/n8n-templates` | `01383a9`, committed 2026-01-12; checked 2026-08-01 | `n8n-contact-form-to-instant-response.json` supplies form intake, validation branch, CRM-style upsert and response; `basic-website-chatbot.json` supplies availability and calendar booking tools | Named services and AI nodes require credentials; qualification, idempotency and local contracts must be made deterministic | **Selected** |
| Qualifying Appointment Requests with AI & n8n Forms | `https://github.com/enescingoz/awesome-n8n-templates` | repository `d8f2731`; workflow blob `32c2527`; checked 2026-08-01 | 25-node form, qualification, terms, acknowledgement, human approval, rejection and Google Calendar booking flow | Strong single appointment path but no CRM/dedupe core; provider-specific Gmail/OpenAI/Calendar nodes make no-key execution expensive | Rejected |

Selected foundation:

- repository URL: `https://github.com/AmplifyAutomation/n8n-templates`
- pinned commit: `01383a9419a1b72cff553ec887501b9d82907be9`
- reused surfaces: the two upstream JSON workflows named above, including form
  intake, validation routing, update/upsert shape, availability lookup, and
  calendar-create flow;
- upstream history/identity preservation: the portfolio repository is a clone,
  the remote is named `upstream`, and the source workflows remain unchanged;
- why faster/safer than blank: the import format, node wiring, form semantics,
  validation branch, and scheduling tool boundaries already exist and can be
  exercised rather than invented from a blank scaffold.

## 4. Distinct visual direction

Rendered working states inspected on 2026-08-01:

| Existing project | Screenshot inspected | Spatial model / dominant interaction | Candidate difference |
| --- | --- | --- | --- |
| Atlas | `knowledge_assistant/docs/screenshots/atlas-answer.png` | editorial three-column answer/evidence workbench | no question canvas or citation ledger |
| Relay | `support_automation/docs/screenshots/relay-case-workspace.png` | dark rail + queue + selected case + action inspector | no left navigation, case inbox, or AI inspector |
| Ledger Lens | `document_extraction/docs/screenshots/document-review.png` | dark rail + document viewer + extracted-fields inspector | no source document or field correction split |
| SignalRoom | `retention_decisioning/docs/screenshots/signalroom-decision-room.png` | broad analytical page with hero, curve and ranked table | no KPI/decision hero or chart-led analysis |
| Website Assistant | locally rendered 1440 px storefront on 2026-08-01 | oversized editorial commerce page with floating chat launcher | dense operator schedule rather than a marketing page |
| Printline | `generative_workflow/docs/screenshots/printline-workstation-1440.png` | dark artboard workstation + recipe deck + filmstrip | no artboard, transport, or image-dominant frame |
| Gauge | `vision_inspection/docs/screenshots/gauge-station-1440.png` | industrial optical stage + infeed rail + disposition console | no machine-stage metaphor, black/yellow safety language, or inspection lens |

- product/audience metaphor: a dispatch book used by a small sales/operations
  team to turn arrivals into confirmed appointments;
- layout structure: full-width arrival tape above a chronological appointment
  ledger; the selected intake slip and booking receipt open inline beside the
  relevant time slot, not in a permanent inspector column;
- palette: aubergine ink, pale lilac paper, coral arrival markers, and mint
  confirmation stamps;
- typography character: condensed, tabular dispatch labels paired with a plain
  humanist body; deliberately unlike Atlas editorial serif and Gauge mono/HMI;
- primary interaction: choose an arrival, approve it into a valid time slot,
  then inspect its chronological receipt trail;
- explicitly avoided: left navigation rails, KPI rows, workflow graphs,
  document splits, chat panels, artboards, and machine-control consoles;
- responsive rule: at 1024 px the ledger remains dominant and the arrival tape
  scrolls horizontally; at 390 px the day becomes a single vertical route with
  arrivals in a top drawer and receipts directly under their slot;
- closest visual neighbor: Relay because both expose approval and audit state;
  LeadDock differs structurally through a time-led appointment book, no sidebar,
  no case queue, inline receipts, a different density, and different typography.

The first UI slice must render at 1440, 1024, and 390 px. The gate fails if it
falls back to a queue/center/inspector composition.

## 5. Minimum referenceable evidence contract

| Gate | Observable acceptance evidence | Status |
| --- | --- | --- |
| Central similarity | HTTP/n8n lead reaches the appointment ledger; browser and HTTP tests | PASS |
| Working vertical slice | validate -> dedupe -> qualify -> approve -> CRM -> book -> handoff; 22-test suite | PASS |
| No-key deterministic proof | `python -m leaddock.server`; four seeded leads and local adapters | PASS |
| Invalid input and abuse behavior | typed invalid-field/timezone errors; duplicate intake idempotency tests | PASS |
| Provider/tool failure and retry/refusal/handoff | browser exercised retry -> DLQ -> replay; `docs/leaddock-failure-replay.png` | PASS |
| Focused mechanism tests | `python -m unittest discover -s tests -v`: 22 passed | PASS |
| Clean-checkout quickstart | standard-library Python command and README | PASS |
| Cover-letter claim ledger | `docs/COVER_LETTER_EVIDENCE.md` | PASS |
| Honest unsupported-claim boundary | README, state API, workflow metadata, and evidence ledger name unsupported providers | PASS |

## 6. Verification and handback

- static/type/lint command: `python -m compileall -q leaddock tests`; `python -m json.tool workflows/leaddock-intake-booking.json`
- focused tests: `python -m unittest discover -s tests -v` -> 22 passed
- integration/demo command: `python -m leaddock.server`; exercised browser booking and dead-letter replay
- build/package command: n8n 2.30.5 Docker import -> one workflow imported
- branch and application commit: `agent/lead-dock-mre` at `d77362d`
- clean state: clean after application commit; detached clean-checkout verification passed
- known boundaries: no named CRM, calendar, messaging, or production n8n claim
- exact next portfolio action: voice receptionist after this MRE passes
