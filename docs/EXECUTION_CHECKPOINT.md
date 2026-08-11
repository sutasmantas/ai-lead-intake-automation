# LeadDock execution checkpoint

Last updated: 2026-08-05

## Restart point

- baseline: LeadDock `main` at `6cee9e6dc9f5e02f6688b0335e71a67c9075af7a`
- branch: `agent/lead-dock-technique-dossier`
- worktree: `portfolio_demos/worktrees/lead_dock_technique_dossier`
- phase: systematic technique-ceiling evidence
- status: systematic gate `PASS`; experiments/overall technique ceiling `PARTIAL`; paused before D0-D4, implementation, depth or polish
- dossier commit: `754d4b1`
- application changes: none

## Systematic evidence gate

| Requirement | Status | Evidence |
| --- | --- | --- |
| problem decomposition and family taxonomy | PASS | `TECHNIQUE_TAXONOMY.md` |
| dated search protocol and saturation | PASS | eight iterations; final two added no top-level family |
| candidate/evidence comparison | PASS | `EVIDENCE_MATRIX.csv` |
| GitHub-first component audit | PASS | exact pins and reuse boundaries in `GITHUB_IMPLEMENTATION_AUDIT.md` |
| frozen experiment design | PASS | D0-D4 in `BENCHMARK_DESIGN.md` |
| explicit decision and claim boundary | PASS | `RESEARCH_DECISION.md` |
| project expertise dispositions | PASS | `docs/EXPERTISE_NOTES.md` |
| baseline verification | PASS | `python -m compileall -q leaddock tests`; workflow JSON parse; 22/22 unit tests |

## Exact next action

Stop this repository. Do not run D0-D4, implement a matcher/model/solver, add provider integrations, polish, merge or push in this slice. The portfolio-wide exact next item is FirstRing's systematic technique dossier, starting from its authoritative clean base and a new isolated worktree.

## Remaining limitations

- D0-D4 are designs only; no identity, calibration, optimization or race result exists.
- Exact normalized email remains the only implemented identity rule; it does not handle noisy identity.
- The additive score is a fixed policy and is not a calibrated conversion probability or causal effect.
- Booking is a local single-calendar collision check, not optimized multi-resource scheduling.
- CRM/calendar/handoff state is in memory; persistence, concurrency, provider contracts and source-write atomicity are unproven.
- No production scale, security, tenancy or exactly-once external-effect claim is supported.

## Previous MRE checkpoint (2026-08-01)

- baseline: AmplifyAutomation `n8n-templates` at `01383a9`
- branch: `agent/lead-dock-mre`
- worktree: `portfolio_demos/worktrees/lead_dock_mre`
- phase: MRE handback
- status: MRE complete; paused before visual polish and named providers
- application commit: `d77362d`
- clean-checkout verification: detached worktree at `d77362d`; 22 tests,
  compileall, and workflow JSON validation passed; verification worktree removed

### MRE gate

| Requirement | Status | Evidence |
| --- | --- | --- |
| GitHub foundation comparison | PASS | `docs/PROJECT_START.md` |
| Isolated worktree and upstream identity | PASS | branch/worktree/remote recorded in `docs/PROJECT_START.md` |
| Rendered portfolio comparison | PASS | seven working states inspected; structural identity recorded |
| Deterministic domain slice | PASS | 22 tests across domain, HTTP, and workflow contracts |
| Importable n8n workflow | PASS | `n8nio/n8n:2.30.5 import:workflow` successfully imported one workflow |
| No-key UI | PASS | `python -m leaddock.server`; seeded arrivals and local adapters |
| Functional and responsive verification | PASS | browser booking/failure/replay; 1440/1024/390 screenshots |
| Cover-letter evidence ledger | PASS | `docs/COVER_LETTER_EVIDENCE.md` |
