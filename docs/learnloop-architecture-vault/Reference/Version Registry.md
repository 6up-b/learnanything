---
title: Version Registry
aliases:
  - Current Versions
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-09-23
source_commit: 2a218baead1b47a34debd9464568936ff58f1c28
source_commit_timestamp: "2026-09-23T15:42:12-04:00"
source_paths:
  - pyproject.toml
  - src/learnloop/algorithm_versions.py
  - src/learnloop/config/schema.py
  - migrations
  - src/learnloop/outcome_contract.py
  - src/learnloop/scheduling/scheduler.py
  - src/learnloop/substrate/dataset.py
  - src/learnloop/substrate/data_quality.py
tags:
  - learnloop/reference
  - learnloop/version
  - learnloop/status
---

# Version Registry

| Version axis | Current value | Meaning |
|---|---|---|
| Python package | `0.1.0` | distribution version in `pyproject.toml` |
| Python runtime | `>=3.12` | supported interpreter floor |
| algorithm | `mvp-0.20` (new vaults: `LATEST_ALGORITHM_VERSION`, owner decision 2026-10-12) | `mvp-0.9`: persisted reveal-aware learning semantics; linear successors reached by `learnloop upgrade` (existing vaults keep their version until then): `mvp-0.10` adds the Slice 1 blind-grading/diagnosis split (`diagnosis.split_enabled`), `mvp-0.11` adds F2 placement serving on top of it (`placement.enabled`), its first review and maintenance lapses decided by the diagnosis, `mvp-0.12` (gated by the same-answer/different-cause guard) adds Slice 2 T1 recurrence groups with authority (`recurrence.enabled`), `mvp-0.13` replaces "I don't know" with "I'm stuck" (`stuck_prompt.enabled`), `mvp-0.14` adds the daily-loop DL1 finite daily plan (`plan.enabled`), `mvp-0.15` admits probe near-ties, teach-back items included, to the Today queue's seeded exploration with a logged propensity (router R1, `router.probe_tie_admission`), `mvp-0.16` brings an assumed or maintenance LO's next check forward when a prerequisite gap named in the learner's own text matches it, and reads the gap's target as a weak signal (learner-text gaps, `learner_text_gaps.sooner_check_enabled`), `mvp-0.17` re-derived the learner's own route on proof-like items with an independent check (the proofs-and-explanations route check; removed from serving on 2026-10-13, so it now grades as `mvp-0.16`, its records replaying as written; `mvp-0.18` and `mvp-0.19` grade the same way), `mvp-0.18` makes certification follow the answer key (an attempt on an imported textbook exercise with an unverified key schedules and teaches but never certifies; canonical sources S1), `mvp-0.19` fulfils intervention needs from the learner's sources before generating (canonical sources S2b, `source_service.source_first_needs`), and `mvp-0.20` (the default upgrade target) moves the route check's protection into the grader's one call: own-route rules in the prompt and a deterministic rule that leaves a divergent route's unquoted mark-down unassessed and holds a grade with nothing assessed and nothing validated (route-check-in-grader, built as `mvp-0.18` and relabelled at its merge; `proof_check.enabled`) |
| canonical projection base | `mvp-0.8` semantics | inherited by every successor, mvp-0.9 through mvp-0.20 (`P0_SUCCESSOR_VERSIONS`, the `SUCCESSOR_CHAIN`) |
| knowledge-model activation | `mvp-0.7` | canonical state/contracts boundary |
| config schema | `2` | emitted `learnloop.toml`; schema 1 accepted |
| SQLite migration head | `197` | current schema ledger maximum |
| collection | `learnloop-events-v1` | `COLLECTION_VERSION` stamped on attempts, slates, offer receipts, submission intents, completion work, model-call receipts and adjudications; attempt and slate rows written before migration 161 read `legacy-unversioned` |
| outcome labels | `learnloop-outcomes-v1` | `LABEL_VERSION` of the exported R_next/R_cold/Q/B/F labels and of adjudications |
| selection policy | `composed_offer_v2` | `selection_policy` on every persisted slate; candidates carry `propensity_kind = unavailable_composed_offer` |
| selection feature schema | `selection_features_v1` | shape of `decision_features` selection rows |
| router decision log | `router_decisions_v1` | shape of a `router_decisions` row (router R1): Today offers, staged P2 decisions, learner picks and daily-plan block decisions (`plan_block`) with their candidate sets and true propensities |
| router outcomes | `router_outcomes_v1` | derivation of `router_outcomes` (R_next, R_cold, S = 0.75 R_cold + 0.25 R_next, right-censored; the one-day R_cold rule is provisional and each outcome records its coldness covariates, owner decision D12) |
| dataset export | `2` | `dataset_version` in an export's `manifest.json`; version 2 records `split_policy`, and a manifest without it split by content family |
| data-quality report | `1` | `report_version` of `learnloop data-quality` output |
| documentation | `1.0.0` | initial architecture-vault release |
| source inventory commit | `62fd1f6404cc…` | baseline commit plus current refactor worktree |

> [!important] Independent axes
> Package, schema, config, algorithm, prompt, contract, and documentation versions solve different problems. Never infer one from another.

## Per-artifact versions

Assessment contracts, prompt contracts, AI prompt versions, probe families, goal terminal contracts, and source revisions carry their own identities. Their module/table notes link to the exact owner.

## Change guidance

- Algorithm semantics: [[Algorithm Versions and Reproducibility#Change protocol]].
- Config/schema: [[Configuration]] and [[ADR-006 Schema-v2 config with one-way compatibility]].
- SQLite: [[State and Persistence#Open modes and migrations]].
- Collection, label, selection and export versions: [[Collection and Dataset Contract]].
- Documentation metadata: [[Documentation Conventions#Frontmatter contract]].

