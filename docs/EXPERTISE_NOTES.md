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

## Reject transformer entity matching until the classical baselines actually fail

- **Trigger:** entity matching is a published deep-learning problem, so reaching for a transformer matcher looks like the modern default.
- **Failure:** Ditto and its successors do win on difficult benchmark pairs, but those gains are demonstrated on long textual product records, and WDC Products shows that modern systems still struggle on **unseen entities** — which is exactly the case a lead intake faces. LeadDock's fields are short and structured and there is no labelled production corpus, so adding GPU serving and a new class of semantic failure would buy benchmark relevance rather than accuracy.
- **Decision:** keep exact identifiers, deterministic fuzzy rules and probabilistic linkage as the ordered path, and admit a neural matcher only if a real semantic field defeats all three. The rejection is recorded with its condition rather than as a preference.
- **Control:** D1 measures blocking recall, pair and cluster quality, candidates per record and high-cost false merges across controlled corruptions, so a neural challenger would have to beat a measured number rather than an impression.
- **Boundary:** no LeadDock matching experiment has run; this is an admission decision, not a comparison result.
- **Evidence:** the Ditto results and the WDC Products unseen-entity finding, the deep/LLM family in `TECHNIQUE_TAXONOMY.md`, and D1 in `BENCHMARK_DESIGN.md`.
- **Proposal-safe insight:** I match the technique to the data shape, and short structured fields with no labels do not justify a transformer — so I state the condition under which I would change my mind.
- **Central index disposition:** add card **Reject transformer entity matching until classical baselines fail**.

## Split by entity, never at random, when evaluating a matcher

- **Trigger:** a pair classifier needs a train and test split and `train_test_split` is one line away.
- **Failure:** a random split over pairs leaks the same entity into both sides, so the model is scored partly on entities it has already seen and the reported accuracy is inflated by an amount nobody can quantify afterwards. The number looks ordinary, which is what makes it dangerous.
- **Decision:** split by entity or by time, never by pair, and keep the clerical-review adjudication loop outside the training data. Active learning may reduce label volume but does not remove adjudication, class imbalance or drift work.
- **Control:** D0 freezes data, seeds, corruptions, split boundaries, hardware and dependency pins across arms, and the contract forbids tuning on the final identity test.
- **Boundary:** no supervised matcher has been trained here; this constrains how one would be evaluated if labels appear.
- **Evidence:** the supervised/active-learning family in `TECHNIQUE_TAXONOMY.md`, and the confounder rules in `BENCHMARK_DESIGN.md`.
- **Proposal-safe insight:** I split on the entity rather than the row, because leakage in a matcher inflates the headline metric and cannot be detected from the metric itself.
- **Central index disposition:** add card **Split by entity, not at random, when evaluating a matcher**.

## Report calibration and ranking separately, because they answer different questions

- **Trigger:** a lead score is wanted and one number is expected to serve both "who do we call first" and "how likely is this to convert".
- **Failure:** a model can rank well and be badly calibrated, or be well calibrated and rank poorly. Presenting a similarity or score band as a conversion probability is the specific error, and a tier labelled "hot" is not a probability no matter how it was produced.
- **Decision:** use a regularised logistic pipeline as the first learned baseline, calibrate on disjoint data as scikit-learn requires, and report both families of metric — calibration curves with Brier and log loss alongside ranking quality — rather than collapsing them. Split by time, because lead policy and markets drift.
- **Control:** D2 evaluates thresholds against actual review and booking capacity rather than aesthetic score bands, and holds the fixed additive score as the baseline that may remain the delivery policy if labels are absent.
- **Boundary:** D2 has not run; the current score is transparent and deterministic and is not calibrated.
- **Evidence:** scikit-learn's calibration documentation on disjoint data and sigmoid/isotonic methods, the fixed-rules and logistic families in `TECHNIQUE_TAXONOMY.md`, and D2.
- **Proposal-safe insight:** I keep ranking and probability as separate claims, so a score used for ordering is never quoted to a client as a likelihood.
- **Central index disposition:** add card **Report calibration and ranking as separate claims**.

## A pair decision is not a safe canonical record

- **Trigger:** the matcher agrees two records are the same entity, and merging them into one lead looks like the obvious next step.
- **Failure:** overwriting source records on the strength of a pair decision destroys information that cannot be recovered if the decision was wrong, and a merge is far harder to reverse than it is to make. Cluster-level constraints can also contradict pairwise ones, so a chain of individually plausible matches can merge two genuinely different companies.
- **Decision:** keep cluster constraints, source lineage, reversible merges and field-level survivorship rules between the match decision and the canonical record. Preserve the unresolved region for review rather than forcing a binary outcome.
- **Control:** D1 reports cluster quality rather than pair accuracy alone, and counts high-cost false merges as their own outcome; D4 requires one canonical lead per accepted identity decision with no silent conflict overwrite.
- **Boundary:** D1 and D4 have not run, so the reversibility is designed rather than demonstrated.
- **Evidence:** the clustering/canonicalisation family in `TECHNIQUE_TAXONOMY.md`, and D1/D4 in `BENCHMARK_DESIGN.md`.
- **Proposal-safe insight:** I separate deciding that two records match from rewriting the record, because the second step is the one that loses data.
- **Central index disposition:** add card **A pair decision is not a safe canonical record**.

## Record infeasible scheduling instances instead of averaging them away

- **Trigger:** a constrained booking solver runs over many instances and the natural summary is a mean objective value.
- **Failure:** an aggregate objective hides the instances where no feasible booking existed at all. Those are the cases a client cares about most, because they are the ones where someone has to be told no, and a mean that silently excludes them reports a solver as healthier than it is.
- **Decision:** count and report infeasible instances as a first-class outcome, never folded into an aggregate, and keep greedy assignment as the control so the constrained solver has to earn its complexity on a declared coupling requirement.
- **Control:** D3 covers deterministic constrained booking, and the stopping rules require infeasible instances to be recorded explicitly; D4 additionally requires at most one appointment per capacity unit under raced approvals.
- **Boundary:** D3 has not run, so no claim is made about feasibility rates or solver quality.
- **Evidence:** the greedy and CP-SAT/MILP scheduling families in `TECHNIQUE_TAXONOMY.md`, and D3 with the confounder and stopping rules in `BENCHMARK_DESIGN.md`.
- **Proposal-safe insight:** I report the instances a scheduler could not satisfy separately from the ones it could, because that count is the operational answer and an average erases it.
- **Central index disposition:** add card **Record infeasible scheduling instances separately**.

## Use a linkage tool inside the limits its own authors state

- **Trigger:** Splink is the strongest available fit for probabilistic linkage, so applying it broadly across all available fields looks like the way to get the most from it.
- **Failure:** Splink's own guidance says correlated fields are problematic for the Fellegi-Sunter independence assumptions, and that a single bag-of-words field is a poor fit. Ignoring both produces agreement weights that look principled and rest on an assumption the data violates.
- **Decision:** give probabilistic linkage only the candidates that exact identifiers did not close, choose partially independent structured fields deliberately, use term-frequency adjustments where identifier frequency is skewed, and abstain around the review threshold rather than forcing a decision.
- **Control:** D1 measures blocking recall and candidates per record alongside pair and cluster quality, so a configuration that inflates agreement weight while degrading review load is visible.
- **Boundary:** no Splink result exists for LeadDock; it is the preferred noisy-data challenger, not an adopted winner.
- **Evidence:** Splink's official guidance on correlated fields and bag-of-words inputs, the Fellegi-Sunter family in `TECHNIQUE_TAXONOMY.md`, and D1.
- **Proposal-safe insight:** I read a tool's stated limitations as part of its interface, and configure inside them rather than discovering them from a bad result.
- **Central index disposition:** add card **Use a linkage tool inside its stated limits**.
