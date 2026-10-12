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
| algorithm | `mvp-0.9` (new vaults) | persisted reveal-aware learning semantics; linear successors reached by `learnloop upgrade`: `mvp-0.10` adds the Slice 1 blind-grading/diagnosis split (`diagnosis.split_enabled`), `mvp-0.11` adds F2 placement serving on top of it (`placement.enabled`), `mvp-0.12` (the default upgrade target) admits probe near-ties to the Today queue's seeded epsilon tie-break with a logged propensity (router R1, `router.probe_tie_admission`) |
| canonical projection base | `mvp-0.8` semantics | inherited by mvp-0.9, mvp-0.10, mvp-0.11 and mvp-0.12 |
| knowledge-model activation | `mvp-0.7` | canonical state/contracts boundary |
| config schema | `2` | emitted `learnloop.toml`; schema 1 accepted |
| SQLite migration head | `176` | current schema ledger maximum |
| collection | `learnloop-events-v1` | `COLLECTION_VERSION` stamped on attempts, slates, offer receipts, submission intents, completion work, model-call receipts and adjudications; attempt and slate rows written before migration 161 read `legacy-unversioned` |
| outcome labels | `learnloop-outcomes-v1` | `LABEL_VERSION` of the exported R_next/R_cold/Q/B/F labels and of adjudications |
| selection policy | `composed_offer_v2` | `selection_policy` on every persisted slate; candidates carry `propensity_kind = unavailable_composed_offer` |
| selection feature schema | `selection_features_v1` | shape of `decision_features` selection rows |
| router decision log | `router_decisions_v1` | shape of a `router_decisions` row (router R1): Today offers, staged P2 decisions and learner picks with their candidate sets and true propensities |
| router outcomes | `router_outcomes_v1` | derivation of `router_outcomes` (R_next, R_cold, S = 0.75 R_cold + 0.25 R_next, right-censored) |
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

