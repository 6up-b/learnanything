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
| algorithm | `mvp-0.25` (new vaults: `LATEST_ALGORITHM_VERSION`, owner decision 2026-10-12) | `mvp-0.9`: persisted reveal-aware learning semantics; linear successors reached by `learnloop upgrade` (existing vaults keep their version until then): `mvp-0.10` adds the Slice 1 blind-grading/diagnosis split (`diagnosis.split_enabled`), `mvp-0.11` adds F2 placement serving on top of it (`placement.enabled`), its first review and maintenance lapses decided by the diagnosis, `mvp-0.12` (gated by the same-answer/different-cause guard) adds Slice 2 T1 recurrence groups with authority (`recurrence.enabled`), `mvp-0.13` replaces "I don't know" with "I'm stuck" (`stuck_prompt.enabled`), `mvp-0.14` adds the daily-loop DL1 finite daily plan (`plan.enabled`), `mvp-0.15` admits probe near-ties, teach-back items included, to the Today queue's seeded exploration with a logged propensity (router R1, `router.probe_tie_admission`), `mvp-0.16` brings an assumed or maintenance LO's next check forward when a prerequisite gap named in the learner's own text matches it, and reads the gap's target as a weak signal (learner-text gaps, `learner_text_gaps.sooner_check_enabled`), `mvp-0.17` re-derived the learner's own route on proof-like items with an independent check (the proofs-and-explanations route check; removed from serving on 2026-10-13, so it now grades as `mvp-0.16`, its records replaying as written; `mvp-0.18` and `mvp-0.19` grade the same way), `mvp-0.18` makes certification follow the answer key (an attempt on an imported textbook exercise with an unverified key schedules and teaches but never certifies; canonical sources S1), `mvp-0.19` fulfils intervention needs from the learner's sources before generating (canonical sources S2b, `source_service.source_first_needs`), `mvp-0.20` moves the route check's protection into the grader's one call: own-route rules in the prompt and a deterministic rule that leaves a divergent route's unquoted mark-down unassessed and holds a grade with nothing assessed and nothing validated (route-check-in-grader, built as `mvp-0.18` and relabelled at its merge; `proof_check.enabled`), `mvp-0.21` lifts four count caps onto value of information (a probe episode asks, a follow-up is queued, a teach-back is kept and a due project probe enters the plan while the next observation's value pays for its minutes; `voi_stopping.enabled`, a sub-switch per site, the multi-family EVSI study's ranks 1-3 behind their own switches) and makes the probe hypothesis lane read the diagnoser's verdict (`diagnosis.probe_lane_reads_diagnosis`; value-of-information stopping, built as `mvp-0.17` with migrations 187/188 and relabelled at its merge with migrations 200/201), `mvp-0.22` lets the Decider decide the small judgments `[decider_routes]` names (learner-text gap pairs, "needed?" and kind; misconception matching; the offline review's pattern links; question classification; contamination leak and reveal verdicts) by the argmax of one typed choice, each with its LLM as fallback and its own kill switch (Tier 1, the Decider migration, built as `mvp-0.20` and relabelled at its merge; no migration; the facet span-support check, `decider_routes.facet_span_support`, is a content path at every version), `mvp-0.23` composes Today with the staged frame: DL1's lanes and `lane_quota_v1` over the set the P4 constraint engine admits, so a block loses only the items a named hard constraint refuses (a seen quick check, a surface reserved for an assessment, an inactive or unrenderable item) and its order is otherwise DL1's, with `golden_path.advance` through the P2 bridge (router R2a, `router.enabled`; built as `mvp-0.23` with migration 205 and landed with migration 202, keeping its tag; no model is called), `mvp-0.24` draws Today's next block from the logged model mixture: the staged rule's pick, the Decider's and the router LLM's distributions over the top-k reversible candidates, with an exact propensity and a floor for each, a model that does not answer giving its weight to the rule, and decides a placeable mid-block follow-up by a logged `plan_interrupt` decision (join the current block now or wait for the next) after the P4 constraint engine has checked it; the models' sensors, similar past decisions and teach-back summaries are context and receipts (router R2b + R2c, `router.mode = "mixture"` and `router.restraint`, `router.max_daily_cost_usd` the metered daily guard; built as `mvp-0.24` and landed keeping its tag; no migration), and `mvp-0.25` (the default upgrade target) grades a criterion tied to an item's required method, frozen with its assessment contract and rendered as "Use {method} in your answer." from the field, on use of that method, so another route fails it with no quoted step (method-explicit items, `own-route-v2`, `required_method.enabled`; built as `mvp-0.22-placeholder` and relabelled at its merge; no migration) |
| canonical projection base | `mvp-0.8` semantics | inherited by every successor, mvp-0.9 through mvp-0.25 (`P0_SUCCESSOR_VERSIONS`, the `SUCCESSOR_CHAIN`) |
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

