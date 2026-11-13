---
title: Version Registry
aliases:
  - Current Versions
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-11-12
source_commit: 2a218baead1b47a34debd9464568936ff58f1c28
source_commit_timestamp: "2026-09-23T15:42:12-04:00"
source_paths:
  - pyproject.toml
  - src/learnloop/algorithm_versions.py
  - src/learnloop/version_floor.py
  - src/learnloop/ops/upgrades.py
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
| algorithm | `mvp-0.59` (`LATEST_ALGORITHM_VERSION`, the last tag of `SUCCESSOR_CHAIN`; new vaults start there, owner decision 2026-10-12) | `mvp-0.9`: persisted reveal-aware learning semantics; each later tag is an immediate successor meaning its predecessor's semantics plus its own change, behind its kill switch. Each tag's meaning is in [[Algorithm Versions and Reproducibility]] and in the comment above its constant in `src/learnloop/algorithm_versions.py`. Existing vaults keep their tag until the owner runs `learnloop upgrade` |
| oldest supported tag | `mvp-0.58` (`OLDEST_SUPPORTED`) | a vault below it, or naming no tag, is refused at every door, `learnloop upgrade` included, with the route through the code tagged `pre-floor` ([[ADR-019 The oldest supported tag]]) |
| upgrade table | one row, `mvp-0.59` (`whole_vault_rebuild`) | `learnloop.ops.upgrades.UPGRADES`: a `Link(tag, activate)` per successor from the floor up, each activated in one transaction with the journal before the config's publication and the publication last; `learnloop upgrade` walks it ([[Algorithm Versions and Reproducibility#The upgrade table]]) |
| canonical projection base | `mvp-0.8` semantics | inherited by every successor, mvp-0.9 through the latest (`P0_SUCCESSOR_VERSIONS`, the `SUCCESSOR_CHAIN`) |
| knowledge-model activation | `mvp-0.7` | canonical state/contracts boundary |
| config schema | `2` | emitted `learnloop.toml`; schema 1 accepted |
| SQLite migration head | `202` | current schema ledger maximum |
| collection | `learnloop-events-v1` | `COLLECTION_VERSION` stamped on attempts, slates, offer receipts, submission intents, completion work, model-call receipts and adjudications; attempt and slate rows written before migration 161 read `legacy-unversioned` |
| outcome labels | `learnloop-outcomes-v1` | `LABEL_VERSION` of the exported R_next/R_cold/Q/B/F labels and of adjudications |
| selection policy | `composed_offer_v2` | `selection_policy` on every persisted slate; candidates carry `propensity_kind = unavailable_composed_offer` |
| selection feature schema | `selection_features_v1` | shape of `decision_features` selection rows |
| router decision log | `router_decisions_v1` | shape of a `router_decisions` row (router R1): Today offers, staged P2 decisions, learner picks and daily-plan block decisions (`plan_block`) with their candidate sets and true propensities; router R2a adds a staged block's `card_hash` and named refusals (`exclusions_json.named`), the exact `plan_presentations` receipts and the stored learner-state card (`router_decision_payloads`); router R2b + R2c (no migration: R1 reserved the columns) add the mixture's block decisions (`policy = router_mixture_v1`: the weights, both models' distributions, the sensors, the model ids, latency, cost and the similar decisions shown), the `plan_interrupt` restraint decisions, and both models' requests and raw answers beside the card in `router_decision_payloads` |
| router outcomes | `router_outcomes_v2` | derivation of `router_outcomes` (R_next, R_cold, S = 0.75 R_cold + 0.25 R_next, right-censored; the one-day R_cold rule is provisional and each outcome records its coldness covariates, owner decision D12). v2 (router R2a) binds each action by the most exact receipt that exists (`action_binding`: the plan presentation an attempt answered, then R1's candidate binding, then R1's session rule as a labelled fallback) and records the answer key's status of the R_next and R_cold attempts. Router R2c binds a `plan_interrupt` decision through its follow-up's own presentation, which names that decision (rows R2a wrote derive as before, so the label is unchanged) |
| router model requests | `router_qs_v1` / `router_qs_v2`, `router_restraint_v1`, `router_llm_v1` / `router_llm_v2` / `router_llm_restraint_v1`, `router_why_v2`, `router_teach_back_summary_v1`, `decision/context` v1 | router R2b + R2c (`mvp-0.24`): the Decider's question sets (block choice; v2 adds the logged-only `teach_first` and `will_pass_next` sensors; the follow-up's `intervene_now`), the router LLM's answer schemas, the mixture's plain why, the teach-back summary in the card, and the embedding recipe of a decision's context for similar-decision retrieval; each is recorded on the row or payload it shaped |
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

