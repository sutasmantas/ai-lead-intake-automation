# LeadDock expertise notes

Date: 2026-08-05

These are research-backed operating rules. Their D-series comparisons have not run.

## Escalate identity evidence instead of replacing exact keys

- **Trigger:** intake records can contain typos, missing identifiers, shared phone numbers or changed email addresses.
- **Failure:** exact-only matching creates duplicate leads, while one broad fuzzy threshold can silently merge different people or companies.
- **Decision:** preserve exact normalized identifiers as a high-confidence fast path; block and score only unresolved candidates; use separate automatic-match, review and non-match regions with reversible lineage.
- **Delivery control:** D1 measures blocking recall, pair and cluster quality, candidates per record, review load and high-cost false merges across controlled corruptions.
- **Boundary:** no noisy LeadDock experiment has run; Splink is a candidate, not an adopted winner.
- **Evidence:** `TECHNIQUE_TAXONOMY.md`, D1 in `BENCHMARK_DESIGN.md`, Splink evaluation guidance and the WDC unseen-entity result.
- **Proposal-safe insight:** I keep reliable identifiers deterministic and spend probabilistic matching only on the ambiguous region, with a review threshold rather than presenting a similarity score as truth.
- **Central index disposition:** add distinct card **Escalate identity evidence instead of replacing exact keys**.

## Calibrate lead decisions against the capacity they consume

- **Trigger:** a team can contact or review only a fixed number of leads and wants score tiers to mean something stable.
- **Failure:** an additive “hot” score or a high AUC can still allocate scarce capacity poorly and can be badly miscalibrated.
- **Decision:** retain rules as the transparent control; train on features available at decision time; use temporal/entity-disjoint validation; report proper probability scores and precision/lift at the actual capacity threshold.
- **Delivery control:** D2 freezes a calibration window, excludes post-contact leakage, and gates on held-out Brier loss plus precision at capacity.
- **Boundary:** UCI Bank Marketing is an outbound 2008-2010 bank-call workflow fixture, not evidence of inbound B2B conversion or business lift.
- **Evidence:** D2 in `BENCHMARK_DESIGN.md`, scikit-learn calibration guidance and the UCI dataset's explicit `duration` warning.
- **Proposal-safe insight:** I separate probability quality from ranking quality and tune the operating threshold to the team's real follow-up capacity, not an arbitrary hot/warm label.
- **Central index disposition:** add distinct card **Calibrate lead decisions against the capacity they consume**.

## Admit constraint scheduling only when bookings are coupled

- **Trigger:** multiple staff, skills, resources, blackouts, priorities or rescheduling penalties make one booking affect another.
- **Failure:** first-fit can waste priority capacity, but adding an optimizer to one homogeneous calendar creates complexity without value.
- **Decision:** keep greedy earliest-fit as the control and fallback; use assignment for simple lead-slot costs; admit OR-Tools CP-SAT only for coupled hard/soft constraints with a solver budget.
- **Delivery control:** D3 first requires zero hard violations, then compares scheduled demand, wait, priority, fairness, churn, objective, solve status/bound and runtime.
- **Boundary:** no solver has been integrated or benchmarked in LeadDock, and stochastic/no-show policy is deferred until credible data exists.
- **Evidence:** D3 in `BENCHMARK_DESIGN.md` and OR-Tools scheduling documentation.
- **Proposal-safe insight:** I use constraint optimization where bookings compete for coupled resources and preserve a deterministic fallback where first-fit is already sufficient.
- **Central index disposition:** add distinct card **Admit constraint scheduling only when bookings are coupled**.

## Keep identity and external-effect idempotency separate

- **Trigger:** duplicate intake, repeated approval or a lost acknowledgement can replay different stages of the lead workflow.
- **Failure:** one canonical lead may still create two CRM rows or appointments; conversely, two genuinely different leads can collide on a shared contact field.
- **Decision:** retain distinct stable identities for the lead decision, CRM upsert, booking capacity and handoff event; persist conflicts and reconcile every retry/effect.
- **Delivery control:** D4 races each boundary and requires exact lead/CRM/booking/handoff reconciliation.
- **Boundary:** current maps are process-local; persistent/concurrent correctness and provider behavior are unproven.
- **Evidence:** D4 in `BENCHMARK_DESIGN.md`, transactional-outbox and idempotent-consumer guidance, and the existing duplicate/booking tests.
- **Proposal-safe insight:** deduplication decides which records describe one lead; idempotency decides whether retrying a particular external action repeats its effect. I test both independently.
- **Central index disposition:** no new card; this deepens the existing **Lead deduplication and booking idempotency are different controls** entry.
