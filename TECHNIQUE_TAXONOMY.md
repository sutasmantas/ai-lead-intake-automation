# LeadDock technique taxonomy

Date: 2026-08-05

Status: systematic research dossier; no experiment or implementation is authorized in this slice. Conclusions use `established`, `provisional`, `contested`, or `unknown`.

## Decision boundary

LeadDock currently proves a bounded, deterministic, in-memory lead path: required-field validation, normalized exact-email deduplication, a fixed additive qualification score, approval/rejection, deterministic timezone-labelled slots, one local calendar collision check, CRM upsert, bounded handoff retries, dead letter and explicit replay. The 22-test suite does not prove noisy identity resolution, calibrated conversion probability, optimized multi-resource scheduling, persistent or concurrent correctness, provider contracts, bidirectional CRM sync, source-write atomicity, authentication, tenancy, production throughput or business uplift.

The paid outcome is not “AI lead scoring.” It is safe lead intake and prioritization that avoids duplicate people and duplicate effects, spends scarce follow-up/booking capacity well, and leaves a recoverable integration trail. Identity, propensity/ranking, scheduling and synchronization are therefore separate decisions with separate labels and failure costs.

## Problem decomposition

| Layer | Independent decision | Serious families | Current boundary |
| --- | --- | --- | --- |
| input quality | make fields comparable without erasing evidence | validation; canonicalization; field-specific normalization; provenance | basic validation and normalization |
| candidate generation | avoid all-pairs matching while retaining true matches | exact keys; phonetic/prefix blocks; sorted neighbourhood; locality-sensitive/embedding retrieval | exact normalized email lookup |
| pair matching | estimate whether two records refer to one entity | deterministic rules; fuzzy thresholds; Fellegi-Sunter; supervised classical; transformer/LLM matcher | exact email equality |
| cluster/entity resolution | turn pair links into stable entities | connected components; correlation/graph clustering; constrained clustering; canonicalization and lineage | one identity string maps to one lead |
| review policy | handle ambiguous or high-cost merges | two thresholds/abstention; clerical review; active learning; override/audit | no ambiguous region |
| lead outcome | define what the score predicts and by when | fixed rules; binary propensity; ranking; time-to-event; uplift/causal effect | undocumented additive tier score |
| probability quality | make scores interpretable for decisions | native logistic probability; sigmoid/isotonic calibration; temporal recalibration; drift monitoring | score is not a probability |
| capacity policy | select work under a scarce review/contact budget | score threshold; top-k; cost-sensitive policy; constrained ranking | hot/warm approval queue |
| booking feasibility | satisfy calendars and hard requirements | first-fit greedy; bipartite/min-cost assignment; MILP; CP-SAT | one fixed 30-minute local calendar |
| booking objective | choose among feasible schedules | earliest slot; weighted priority; wait/utilization/fairness; rescheduling stability | earliest available choice by caller |
| uncertainty | account for arrivals, duration, cancellation/no-show | buffers/heuristics; simulation optimization; stochastic/robust optimization; online/RL policy | none |
| CRM/calendar authority | decide who owns state and conflict resolution | synchronous adapter; webhook; polling; CDC/outbox; one-way/bidirectional sync | local in-memory adapters |
| effect safety | prevent retries/races from duplicating outcomes | database uniqueness; idempotency keys; transactions/outbox; leases; reconciliation | process-local maps and booking key |
| evaluation | distinguish model quality from workflow quality | labelled holdout; controlled corruption; capacity simulation; race/fault reconciliation | deterministic contract tests only |

## Technique families and operating regions

### Exact normalized identifiers — `established fast path`

Exact normalized email or phone is cheap, explainable and high precision when the identifier is present, correctly captured and stable. It should remain the first path. It cannot resolve typos, changed addresses, shared phones or contradictory fields, and aggressive normalization can create false merges. Exact identity also does not make the later booking or CRM effect idempotent.

### Field similarities and deterministic fuzzy rules — `established bounded option`

RapidFuzz supplies maintained string similarity primitives; field-aware rules can combine email username/domain, phone suffix, person/company name and other evidence. This is appropriate for a small, well-understood schema and gives an interpretable challenger. Thresholds are data-specific and transitive clustering can turn plausible pairs into an incorrect large entity, so pair and cluster quality must both be scored.

### Fellegi-Sunter probabilistic linkage — `established family`, `preferred noisy-data challenger`

Splink estimates match/non-match agreement evidence, supports term-frequency adjustments, blocking, unsupervised parameter estimation and cluster evaluation. It is a strong fit when several partially independent structured fields exist and labelled pairs are scarce. Its own guidance says correlated fields are problematic and a single bag-of-words field is a poor fit. For LeadDock, probabilistic matching should handle only candidates not closed by exact identifiers and should abstain around the review threshold.

### Supervised and active-learning pair classifiers — `conditional`

Dedupe learns blocking and pair classification from human labels; classical scikit-learn models can learn field similarities directly. These become attractive after representative match/non-match labels and a clerical-review loop exist. Random pair splits are invalid when the same entity leaks across train and test. Active learning reduces label volume but does not remove adjudication, class imbalance or drift work.

### Deep/transformer/LLM entity matching — `established research family`, `rejected first implementation`

Ditto and later systems show gains on difficult benchmark pairs, especially textual product records. WDC Products also shows that modern systems struggle on unseen entities. LeadDock has short structured fields and no labelled production corpus; adding GPU/model serving and semantic failure modes before classical baselines would be disproportionate. Retain only if exact/fuzzy/probabilistic approaches fail on a real semantic field.

### Clustering, canonicalization and privacy — `established downstream concerns`

Pair decisions do not automatically yield a safe canonical lead. Cluster constraints, source lineage, reversible merges and field-level survivorship rules are needed before overwriting source records. Privacy-preserving linkage and graph/Bayesian approaches are valid families but outside this portfolio experiment until cross-owner sensitive data creates that requirement.

### Fixed rules — `established policy baseline`, `not calibrated`

The current additive score is transparent and deterministic. It remains the baseline and may remain the delivery policy if labels are absent. A tier such as “hot” cannot be described as conversion probability, and thresholds should be evaluated against actual review/booking capacity rather than aesthetic score bands.

### Logistic probability plus calibration — `preferred first learned baseline`

A regularized logistic pipeline with one-hot encoding gives an interpretable propensity baseline. scikit-learn documents disjoint calibration data and provides sigmoid/isotonic calibration, calibration curves, Brier loss and log loss. Time-based train/calibration/test splits are required because lead policy and markets drift. Calibration and ranking answer different questions and both must be reported.

### Gradient boosting — `established challenger`, `conditional on measured win`

Histogram gradient boosting or XGBoost can capture nonlinear tabular interactions. It costs more tuning and explanation and may still require calibration. Start with scikit-learn's maintained stack; add XGBoost only if a frozen nonlinear challenger materially improves held-out capacity precision or proper scores without unacceptable instability.

### Ranking, survival and uplift — `distinct outcome families`, `deferred`

Ranking directly optimizes order under scarce capacity; survival models address time to conversion and censoring; uplift estimates the incremental effect of contacting a lead. They are not interchangeable with conversion propensity. Uplift requires treatment/control or defensible causal assumptions, and survival needs timestamps/censoring. Record these as admission paths, not as claims supported by UCI Bank Marketing.

### Greedy/assignment scheduling — `established simple region`

First-fit or earliest-fit is correct and cheap when one homogeneous calendar, one duration and no coupled objective exist. A bipartite or min-cost assignment covers independent lead-to-slot choices with capacities and costs. These should remain controls; optimization is unnecessary if every feasible method returns the same schedule.

### CP-SAT/MILP scheduling — `established constrained region`, `preferred complex challenger`

OR-Tools exposes CP-SAT interval and scheduling primitives suited to no-overlap, resource, availability, priority and soft-penalty constraints. It becomes useful when bookings are coupled across staff/resources or rescheduling has an objective. Hard feasibility is the first gate; solve status, bound/gap and time budget must be recorded. Timefold is a maintained Java/Kotlin alternative but would add a separate runtime for no demonstrated advantage here.

### Robust, stochastic and online scheduling — `established research families`, `deferred`

Appointment research treats uncertain duration, no-shows and arrivals through simulation, stochastic/distributionally robust optimization and adaptive policies. Those families require credible distributions or online feedback. LeadDock should first prove deterministic constraint value; an RL or robust scheduler without a realistic simulator would be theatre.

### CRM/calendar synchronization — `established integration families`

Synchronous upsert is the smallest one-way boundary. Webhooks reduce inbound latency; polling supplies reconciliation; CDC/outbox closes source transaction gaps when the application owns the database. Bidirectional sync additionally needs field ownership, origin/version metadata, loop prevention, tombstones and an explicit conflict rule. No synchronization mechanism removes the need for idempotent consumers because relays can duplicate delivery.

## Search protocol

- Search date: 2026-08-05.
- Sources: Splink/Record Linkage Toolkit/scikit-learn/OR-Tools documentation, UCI, Debezium, primary papers and maintained GitHub repositories.
- Main window: 2024-2026, retaining older standards, algorithms and datasets where still authoritative.
- Excluded: license research or ranking, popularity-only recommendations, vendor outcome claims without a reproducible comparator, and unrelated health-care-specific objectives presented as LeadDock evidence.

| Iteration | Query family | New decision-relevant family |
| ---: | --- | --- |
| 0 | plan-derived exact/fuzzy/probabilistic linkage, scoring and CP scheduling | initial family map |
| 1 | Splink, Dedupe, Record Linkage Toolkit, blocking and cluster evaluation | blocking, active learning and cluster evaluation |
| 2 | probability calibration, Brier/log loss and Bank Marketing | calibrated propensity and dataset leakage boundary |
| 3 | OR-Tools/Timefold scheduling and solver primitives | assignment/CP-SAT operating regions |
| 4 | outbox, CDC, idempotent consumer and fault injection | synchronization/effect-safety layer |
| 5 | entity/lead/scheduling/sync expansion | ranking/uplift/survival; robust/stochastic/online; canonicalization/privacy/CRDT |
| 6 | 2026 hybrid ER, two-stage lead profiling, robust/RL scheduling and sync | no top-level family; refinements only |
| 7 | explicit alternatives to retained families | no top-level family; refinements only |

Iterations 6 and 7 added no top-level family after the deferred families from iteration 5 were incorporated. Saturation is `PASS` for the dated LeadDock scope.

## Primary anchors

- [Splink repository and documentation](https://github.com/moj-analytical-services/splink)
- [Splink blocking guidance](https://moj-analytical-services.github.io/splink/topic_guides/blocking/blocking_rules.html)
- [Splink evaluation overview](https://moj-analytical-services.github.io/splink/topic_guides/evaluation/overview.html)
- [(Almost) all of entity resolution](https://pmc.ncbi.nlm.nih.gov/articles/PMC11636688/)
- [WDC Products benchmark](https://arxiv.org/abs/2301.09521)
- [NAACL 2024 entity-blocking reproducibility study](https://aclanthology.org/2024.naacl-long.483/)
- [scikit-learn probability calibration](https://scikit-learn.org/stable/modules/calibration.html)
- [UCI Bank Marketing](https://archive.ics.uci.edu/dataset/222/bank+marketing)
- [OR-Tools scheduling reference](https://github.com/google/or-tools/blob/stable/ortools/sat/docs/scheduling.md)
- [OR-Tools employee scheduling](https://developers.google.com/optimization/scheduling/employee_scheduling)
- [Debezium outbox event router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html)
- [Transactional outbox](https://microservices.io/patterns/data/transactional-outbox)
- [Toxiproxy](https://github.com/Shopify/toxiproxy)
