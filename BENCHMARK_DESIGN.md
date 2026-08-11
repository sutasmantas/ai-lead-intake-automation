# LeadDock benchmark design

Date: 2026-08-05

Status: design only. No dataset download, model fitting, solver run, provider integration or fault experiment was performed in this slice.

## Questions closed by external evidence

| Question | Closed decision |
| --- | --- |
| Is exact normalized email enough for noisy lead identity? | no; retain it as the fast path and measure a bounded ambiguous path |
| Should LeadDock implement record-linkage algorithms from scratch? | no; use RapidFuzz and Splink behind project-owned interfaces |
| Is a fixed additive tier a calibrated conversion probability? | no; it remains a policy baseline only |
| Is random train/test splitting sufficient for historical leads? | no; freeze temporal/entity-disjoint splits and feature availability |
| Can UCI Bank Marketing prove performance on inbound B2B leads? | no; use it only to exercise the calibration workflow and disclose domain/leakage limits |
| Is CP-SAT inherently better than greedy booking? | no; admit it only for coupled constraints/objectives and compare feasibility, quality and time |
| Does lead deduplication prevent duplicate CRM/calendar effects? | no; identity and effect idempotency need separate persistent keys and race tests |
| Can a workflow retry prove exactly-once external effects? | no; reconcile stable identities and require receiver/provider idempotency |

## Common evidence contract

Every run records dataset/fixture digest, code and dependency pins, seed, split entity/time boundaries, corruption profile, candidate rules, model/solver parameters, threshold/capacity policy, wall/CPU time and hardware. Identity runs retain pair labels, predicted edges, clusters, review decisions and canonicalization lineage. Scoring runs retain feature-availability declarations, raw and calibrated probabilities, selected top-k and outcomes. Scheduling runs retain UTC instants, local labels, constraints, objective terms, status/bound and fallback. End-to-end runs reconcile lead identity, CRM record, appointment, handoff attempt, DLQ/replay and observed effect.

## D0 — harness and current-control freeze

Create one deterministic scenario manifest around the existing service and adapters. Preserve all 22 tests, add machine-readable receipts for current exact identity, score decomposition, slot/booking keys and handoff state, and mutation checks that remove a lead, duplicate a CRM effect, double-book a slot and strand a handoff. PASS requires the scorer to detect every mutation and reproduce identical results from the same seed.

Budget: standard-library control, local CPU, four hours, no external endpoint.

## D1 — noisy lead identity

### Data

- Record Linkage Toolkit FEBRL datasets for a public generated baseline.
- Splink synthetic data for implementation-aligned diagnostics.
- A frozen LeadDock generator with person/company/email/phone fields and independently controlled typos, transpositions, missingness, shared identifiers, domain changes, abbreviations and conflicting fields.
- Entity-disjoint development/test partitions; never split pairs randomly when the same entity can cross partitions.

### Arms

1. exact normalized email/phone fast path;
2. RapidFuzz field-aware deterministic rules;
3. Splink Fellegi-Sunter with frozen blocking and two thresholds: auto-link/review/non-link.

### Metrics and gates

Report blocking recall, candidate pairs and largest block; pair precision/recall/F1; B-cubed cluster precision/recall/F1; false-merge and false-split counts; review fraction; p50/p95 latency and peak memory. Automatic merges require zero high-cost false merges in the frozen test and at least 0.98 pair precision; the ambiguous band may trade automation for review. A challenger must improve noisy-case recall by at least 10 percentage points over exact matching without violating the auto-merge precision gate. Otherwise retain exact-only automation.

Use five corruption seeds and bootstrap confidence intervals for non-exact metrics. Inspect clusters, not only pair F1. Stop before supervised/deep matching unless at least 500 adjudicated ambiguous pairs exist or the classical profiles fail a documented semantic case.

## D2 — calibrated lead prioritization

### Data and split

Use UCI Bank Marketing solely to exercise a reproducible tabular/calibration pipeline. Exclude `duration` and any feature unavailable before contact; use the chronological full dataset ordering for train, calibration and final test windows. State prominently that 2008-2010 Portuguese outbound bank calls are not inbound B2B leads. A later client/portfolio run must use lead-created-time features and a fixed outcome horizon with entity/time separation.

### Arms

1. current fixed additive rules and hot/warm policy;
2. regularized logistic regression with one-hot encoding;
3. one nonlinear challenger: scikit-learn histogram gradient boosting first, XGBoost only if a concrete compatibility/performance need appears;
4. sigmoid/isotonic calibration selected only on the calibration window.

### Metrics and gates

Report prevalence, ROC-AUC and average precision for context; Brier loss, log loss, calibration intercept/slope and reliability table; precision, recall, lift and captured positives at 5%, 10% and a frozen operator capacity; inference time and feature stability. Promotion requires lower held-out Brier loss than rules, no worse precision at frozen capacity, and calibration slope 0.8-1.2 with absolute intercept no more than 0.1. If no model passes, retain transparent rules and relabel tiers as policy priorities rather than probabilities.

Do not infer contact uplift from conversion propensity. Admit uplift only with treatment/control evidence, survival only with censored time-to-event data, and learning-to-rank only when ranking labels or a defensible listwise objective exist.

## D3 — deterministic constrained booking

Generate controlled cases across 1/5/20 staff, 20/200/2,000 leads and 1/5/20 days with 15/30/60-minute durations, skills, resource capacities, staff calendars, blackouts, priority, maximum wait, fairness penalties and rescheduling-cost penalties. Include IANA timezone cases around DST gaps and folds; convert to UTC before solving and retain requested local labels.

Compare first-fit greedy, assignment/min-cost flow when the case is bipartite, and OR-Tools CP-SAT for coupled constraints. Report hard-feasibility violations, scheduled/unscheduled count, weighted wait, priority lateness, staff-load dispersion, schedule churn, objective value, best bound/gap, p50/p95 solve time and fallback use.

Every arm must produce zero hard violations. CP-SAT is promoted only when it improves the frozen weighted objective by at least 10% or schedules at least 5% more priority-weighted demand on coupled cases, returns a feasible solution within two seconds for the interactive profile and 30 seconds for batch, and exact greedy remains the simple-case fallback. If greedy is equivalent on all representative cases, do not add a solver.

## D4 — duplicate and partial-failure races

Move only the experiment profile to a persistent database and reuse the DeliveryGuard/transactional-outbox patterns rather than writing ad hoc distributed state. Race simultaneous equivalent intakes, same email with conflicting payloads, two approvals for one lead, two leads for one slot, CRM success followed by calendar timeout, calendar success followed by lost acknowledgement, process kill at every boundary, workflow redelivery and DLQ replay. Add Toxiproxy for latency/reset/timeout; process/database faults remain explicit harness actions.

PASS requires one canonical lead per accepted identity decision, no silent conflict overwrite, at most one appointment per capacity unit, at most one CRM record per stable external key, no lost accepted action, no duplicate business effect when the receiver honors idempotency, and exact reconciliation of every attempt/state. Measure duplicate side-effect rate, conflict/review rate, recovery time, queue age and unexplained rows/effects. This does not establish production scale or exactly-once behavior at an uncooperative provider.

## Confounders and stopping rules

- Freeze data, seeds, corruptions, split boundaries, hardware and dependency pins across arms.
- Do not tune on the final identity/scoring test or booking stress cases.
- Separate false identity merges, duplicate intake requests and duplicate external effects.
- Separate ranking quality from probability calibration and prediction from causal lift.
- Record infeasible scheduling instances; never hide them in aggregate objective values.
- Stop after D1/D2/D3 when a simpler control satisfies the paid decision. Custom algorithms are not a portfolio objective.
- No SaaS credentials or client data enter the public evidence bundle; provider adapters require separate contract fixtures and secrets.
