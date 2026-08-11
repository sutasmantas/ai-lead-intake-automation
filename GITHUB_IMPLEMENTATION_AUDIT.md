# LeadDock GitHub implementation audit

Date: 2026-08-05

Purpose: inspect maintained implementations before writing consequential identity, scoring, scheduling or synchronization logic. Decision value comes from fit, maintenance, known boundaries and integration cost.

## Current seams

- `leaddock/domain.py::_normalize` owns validation and field normalization.
- `LeadDockService.intake` owns identity lookup and lead creation.
- `_qualify` owns the fixed score and tier policy.
- `LocalCrmAdapter` owns deterministic external-record mapping.
- `LocalCalendarAdapter` owns available slots, collisions and booking idempotency.
- `LeadDockService.approve`, handoff retry/DLQ and replay own effect sequencing.
- `leaddock/server.py` and the n8n JSON expose the HTTP/workflow boundaries.

Keep those contracts stable during experiments. Add candidate generators, matchers, scorers and schedulers behind interfaces; do not paste algorithms into the service path.

## Repository comparison

| Repository and inspected pin | Health on 2026-08-05 | Reusable component | Important boundary | Decision |
| --- | --- | --- | --- | --- |
| [moj-analytical-services/splink](https://github.com/moj-analytical-services/splink) `f89da14` | active 2026-08-04; 223 open issues | DuckDB-backed blocking, comparisons, Fellegi-Sunter estimation, clustering and diagnostics | requires multiple useful structured fields, model settings and threshold review; not ideal for one text field | preferred probabilistic challenger; refit configuration and adapters, never reimplement Fellegi-Sunter |
| [dedupeio/dedupe](https://github.com/dedupeio/dedupe) `3f61e79` | last push 2025-07-29; 90 open issues | active-learning labelling, learned blocking and clustering | needs a real reviewer loop and representative labels; project activity is slower than selected stack | defer until ambiguity labels exist; reference review workflow |
| [rapidfuzz/RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) `03a5137` | active 2026-08-03; 31 open issues | optimized field-level string similarities and candidate extraction | supplies distances, not entity decisions, calibration or clusters | adopt as thin fuzzy feature component in D1 |
| [J535D165/recordlinkage](https://github.com/J535D165/recordlinkage) `b93d976` | last push 2024-02-21; 64 open issues | FEBRL fixtures, indexing/comparison/classification pipeline | slower maintenance and synthetic/older fixtures | use fixture/baseline helpers only; not the runtime matcher |
| [megagonlabs/ditto](https://github.com/megagonlabs/ditto) `5298556` | last push 2024-04-17; 26 open issues | transformer entity-matching reference and benchmark data | research-oriented older stack, model/label cost, no advantage established for short lead fields | explicit non-adoption unless classical profiles fail on semantic text |
| [scikit-learn/scikit-learn](https://github.com/scikit-learn/scikit-learn) `7cb1868` | active 2026-08-04; 2111 open issues | preprocessing, logistic and histogram-gradient models, calibration, metrics and temporal/group split tools | correct split, leakage controls and decision policy remain project-owned | adopt one coherent D2 scoring/calibration stack |
| [dmlc/xgboost](https://github.com/dmlc/xgboost) `9922908` | active 2026-08-04; 417 open issues | optimized nonlinear gradient boosting | extra dependency/tuning; probabilities may need post-calibration | one conditional challenger only if sklearn baseline leaves a material nonlinear gap |
| [google/or-tools](https://github.com/google/or-tools) `98c165a` | active 2026-08-04; 115 open issues | assignment/min-cost-flow and CP-SAT interval/resource scheduling | model construction, objective weights, solver budget and timezone conversion remain local | preferred maintained D3 scheduling component; do not write a solver |
| [TimefoldAI/timefold-solver](https://github.com/TimefoldAI/timefold-solver) `01be36b` | active 2026-08-04; 102 open issues | rich Java/Kotlin constraint-planning stack | separate runtime and broad framework for a Python portfolio service | comparison evidence only; do not integrate |
| [n8n-io/n8n](https://github.com/n8n-io/n8n) `3d68c29` | active 2026-08-05; 1399 open issues | existing workflow/runtime and connector surface | workflow execution does not own LeadDock identity, transaction or provider truth | retain workflow adapter; no custom orchestration engine |
| [debezium/debezium](https://github.com/debezium/debezium) `1397c91` | active 2026-08-04; 118 open issues | outbox event router and CDC | duplicates remain; Kafka Connect/engine operations; only closes a transaction it can observe | conditional source-owned sync profile, not default |
| [Shopify/toxiproxy](https://github.com/Shopify/toxiproxy) `94d6d4b` | active 2026-08-04; 104 open issues | TCP latency, timeout, reset and bandwidth faults | no process, database or semantic-race faults | adopt in shared D4 fault harness |

## Reuse map before custom logic

| Need | First source to reuse | Project-owned adapter/check |
| --- | --- | --- |
| field similarity | RapidFuzz | LeadDock normalization, field weights, candidate policy and threshold evidence |
| probabilistic identity | Splink/DuckDB | schema mapping, blocking rules, two thresholds, canonical lead/lineage and review surface |
| labelled review loop | Dedupe design | adjudication UI, label provenance and entity-disjoint evaluation |
| calibrated lead score | scikit-learn | feature availability time, temporal split, calibration set, capacity decision and drift report |
| nonlinear score | sklearn histogram boosting, then XGBoost only if needed | identical folds/calibration/capacity gates and explanation boundary |
| constrained booking | OR-Tools CP-SAT/assignment | timezone-to-UTC boundary, domain constraints, objective weights, solver limits and fallback |
| workflow/provider calls | existing n8n plus thin CRM/calendar adapters | versioned payload mapping, idempotency, secret references and reconciliation |
| source-write atomicity | source-owned outbox plus Debezium pattern | stable event ID, ownership and duplicate consumer handling |
| network faults | Toxiproxy | deterministic scenario manifest and exact state/effect reconciliation |

## Explicit non-adoptions

- Do not hand-write fuzzy distance algorithms, Fellegi-Sunter estimation, probability calibration or a constraint solver.
- Do not import an entire CRM, scheduler, agent framework or entity-resolution service to replace LeadDock's bounded contracts.
- Do not add Splink, Dedupe, Ditto and a custom matcher together. D1 compares an exact control, one RapidFuzz rule profile and Splink; supervised/deep profiles require a later admission gate.
- Do not call a fuzzy score or model probability an entity truth. Preserve source records, evidence and reversible review decisions.
- Do not use UCI `duration` or any field unavailable at decision time. Do not describe Bank Marketing performance as inbound B2B lead performance.
- Do not add XGBoost until a regularized logistic/scikit-learn profile is measured. Do not equate ranking, propensity and uplift.
- Do not use CP-SAT where first-fit has no coupled constraint to optimize. Do not claim optimality without solver status/bound and a frozen time limit.
- Do not build bidirectional sync without field ownership, origin/version metadata, loop prevention, tombstones and reconciliation.

## Minimal integration checks

1. Preserve all 22 validation, exact-dedupe, tier, approval, collision, timezone, retry, DLQ/replay, HTTP and workflow tests.
2. Make candidate generation observable: candidates per record, blocking recall on labelled pairs and worst block size.
3. Keep exact auto-match, ambiguous review and definite non-match paths separate; score both pair links and resulting clusters.
4. Fit, calibrate and test on disjoint time/entity groups; log feature availability and omit post-contact fields.
5. Compare rules/logistic/nonlinear profiles with Brier/log loss and precision/recall/lift at frozen capacity, not accuracy alone.
6. Convert all availability to UTC instants before optimization; test DST gaps/folds, hard constraints, infeasibility and deterministic fallback.
7. Race duplicate intake, repeated approval, booking collision and retry-after-effect against a persistent store; reconcile lead, CRM, booking, handoff and DLQ identities.
8. Optional candidates must be removable while the existing deterministic demo and workflow remain usable.
