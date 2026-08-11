# LeadDock research decision

Date: 2026-08-05

## Outcome

The systematic evidence gate is `PASS`. Experiment and overall technique-ceiling gates remain `PARTIAL`: D0-D4 are frozen designs, not results.

The current deterministic service remains the honest baseline. The first depth experiment is D0 and then D1: exact identity stays the automatic fast path while RapidFuzz and Splink compete only on noisy candidates. D2 uses scikit-learn for a calibrated scoring workflow; D3 admits OR-Tools only on coupled scheduling cases. D4 proves that identity, booking idempotency and integration recovery are separate controls.

There is no evidence-based reason to add a transformer matcher, XGBoost, a Java solver, a bidirectional CRM engine or a durable workflow runtime now.

## Retained decisions

| Decision | Disposition |
| --- | --- |
| validation, exact normalized identifier, explicit approval and local idempotency | invariant control |
| RapidFuzz field similarities | D1 thin deterministic challenger |
| Splink Fellegi-Sunter/DuckDB | D1 preferred probabilistic challenger |
| Dedupe active learning | deferred until representative ambiguous labels/review exist |
| Ditto/LLM matcher | rejected unless classical profiles fail a documented semantic case |
| current additive score | transparent policy baseline; never call it probability |
| scikit-learn logistic + calibration | D2 first learned profile |
| histogram gradient boost/XGBoost | at most one nonlinear challenger after baseline |
| ranking/survival/uplift | distinct deferred outcomes with separate data admission gates |
| first-fit greedy | mandatory simple scheduling control/fallback |
| assignment/min-cost flow | conditional intermediate arm |
| OR-Tools CP-SAT | D3 maintained constrained-scheduling challenger |
| robust/stochastic/RL scheduling | deferred until deterministic value and credible uncertainty data exist |
| n8n/provider adapters | retain as integration boundary, not source of truth |
| outbox/Debezium and Toxiproxy | D4 conditional atomicity pattern and shared fault tool |

## Exact next controlled work

1. D0 common manifest, machine-readable current-state evidence and mutation oracle.
2. D1 exact/RapidFuzz/Splink identity comparison using public generated plus controlled corruption fixtures.
3. D2 only after feature-availability and temporal split contracts are frozen.
4. D3 only on generated cases with coupled constraints; retain greedy fallback.
5. D4 only after a persistent experiment boundary exists and shared reliability components can be reused.

No experiment, implementation, UI work, visual polish, merge, push or publication was performed in this slice.

## Eleven systematic evidence gates

| Gate | Status | Evidence |
| --- | --- | --- |
| Problem decomposition | PASS | normalization through evaluation layers in `TECHNIQUE_TAXONOMY.md` |
| Search protocol | PASS | dated primary/official sources and eight reproducible iterations |
| Survey coverage | PASS | classical, probabilistic, supervised, deep and review identity; rule/calibrated/ranking/causal score; deterministic/robust scheduling; sync families |
| Benchmark coverage | PASS | public generated fixtures plus D0-D4 controlled designs |
| Existing-answer search | PASS | component/architecture decisions separated from local winners |
| Technique-family saturation | PASS | iterations 6 and 7 added no top-level family |
| Candidate comparison | PASS | `EVIDENCE_MATRIX.csv` |
| Contrary evidence | PASS | correlation/unseen-entity/label, leakage/domain-transfer, solver-complexity and at-least-once limits |
| Implementation evidence | PASS | exact pins and component seams in `GITHUB_IMPLEMENTATION_AUDIT.md` |
| Portfolio fit | PASS | adds defensible identity/calibration/optimization depth without pretending one “AI score” solves all three |
| Review status | PASS | claims are labelled and experiment results remain explicitly unknown |

## Claim boundary

Defensible now: LeadDock proves its existing bounded deterministic intake/approval/booking/handoff path and now has a systematic, GitHub-first plan for noisy identity, calibrated capacity scoring, constrained scheduling and race-safe integration.

Not defensible now: noisy-match accuracy, calibrated conversion probability, lift caused by contact, optimized scheduling gains, persistent/concurrent correctness, provider-specific CRM/calendar behavior, production scale, security/multi-tenancy or exactly-once external effects.
