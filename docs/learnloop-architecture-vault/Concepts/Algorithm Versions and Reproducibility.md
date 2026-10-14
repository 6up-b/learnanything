---
title: Algorithm Versions and Reproducibility
aliases:
  - Algorithm Versioning
  - Reproducibility
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/algorithm_versions.py
  - docs/algorithm-change-playbook.md
  - src/learnloop/ops/vault_upgrade.py
  - src/learnloop/substrate/rebuild_orchestrator.py
  - src/learnloop/substrate/shadow_rebuild.py
tags:
  - learnloop/concept
  - learnloop/algorithm
  - learnloop/reproducibility
---

# Algorithm Versions and Reproducibility

Algorithm versions identify persisted meaning, not package releases.

## Current vocabulary

| Version | Meaning |
|---|---|
| `mvp-0.7` | canonical knowledge-model state and assessment contracts |
| `mvp-0.8` | authority-propagation projection with robust composition/reliability discounting |
| `mvp-0.9` | successor retaining mvp-0.8 projection semantics and adding cross-channel reveal accounting |
| `mvp-0.10` | successor retaining that projection and splitting grading: a learner-blind grader plus an asynchronous history-aware diagnoser (Slice 1 M2; kill switch `diagnosis.split_enabled`) |
| `mvp-0.11` | successor to `mvp-0.10` keeping its split and changing serving only: no opening probe per new LO, new material as learning, "assumed known (not tested)" checked in the first review (learner field F2; kill switch `placement.enabled`) |
| `mvp-0.12` | successor to `mvp-0.11` keeping the split and placement: holding-pen promotion and the K=3 escalation group hypotheses by recurrence group (exact statement classes joined by validated diagnoser citations and `same_cause` verdicts) instead of by exact statement, and a group's K-th recurrence shows an escalated repair (Slice 2 T1 / M3; kill switch `recurrence.enabled`; the upgrade reports the same-answer/different-cause guard's status for the configured judge and proceeds, refusing until the guard passes only with `recurrence.require_guard = true`, owner decision 2026-10-12) |
| `mvp-0.13` | successor to `mvp-0.12`: "I'm stuck" (write what you can) replaces "I don't know"; a stuck answer with text is an ordinary graded and diagnosed attempt, an empty one a deterministic zero with no model call and no error tag (kill switch `stuck_prompt.enabled`) |
| `mvp-0.14` | successor to `mvp-0.13` changing serving only: Today serves the finite daily plan of remembered minutes split across repair, maintain, new and push, chosen block by block (daily-loop DL1; kill switch `plan.enabled`) |
| `mvp-0.15` | successor to `mvp-0.14` changing serving only: PROBE-intent near-ties (in-episode diagnostic probes and teach-back items, owner decision D11) join the Today queue's seeded exploration, so their decisions log a true propensity (router R1, built as `mvp-0.12` and relabelled at its merge; kill switch `router.probe_tie_admission`). Router decision logging (`router.log_decisions`) is not a serving change and runs at every version |
| `mvp-0.16` | successor to `mvp-0.15` changing serving only: a prerequisite gap named in the learner's own text (a tutor question, a stuck answer, a diagnosis) and matched to an LO assumed known or in maintenance brings that LO's next check forward (no sooner than `learner_text_gaps.sooner_check_delay_hours` after the gap, never later than it was), and the gap's target is a weak interaction signal on that LO (learner-text gaps, built as `mvp-0.13` and relabelled at its merge; kill switch `learner_text_gaps.sooner_check_enabled`). The rest of the pipeline (named gaps, matches, edges, created prerequisites, holding-pen sightings) is a live change behind its own switches at every version |
| `mvp-0.17` | successor to `mvp-0.16` changing what new blind grades persist on proof-like items: an LLM reads each item once (cached per item content) for whether its rubric credits the learner's own reasoning, and on those items an independent re-derivation of the learner's route on `ai.routing.proof_check` (else a route with a model other than the grader's) feeds a deterministic gate that restores an unlocated mark-down on a valid route, leaves a quoted-but-valid step not assessed, flags a refuted full-credit step, and holds a grade with nothing assessed and nothing validated for review (the grader's own score, no FSRS review). Replay reads the blind record as written; the projection namespace is unchanged (the proofs-and-explanations route check, built as `mvp-0.15`, a placeholder tag, and relabelled at its merge; kill switch `proof_check.enabled`). Removed from serving on 2026-10-13 (route-check-in-grader): an `mvp-0.17` vault (and an `mvp-0.18` or `mvp-0.19` vault) now grades new answers as its kill switch defined (as `mvp-0.16`); its records keep their meaning and replay exactly (`fixtures/mvp017_route_check_replay`) |
| `mvp-0.18` | successor to `mvp-0.17`: certification follows the answer key. An attempt on an imported textbook exercise records `practice_attempts.reference_status` from the served item's effective key status (the latest check of its current prompt, key and rubric); an `unverified` attempt schedules and teaches but earns no certification credit (owner decision C3), and exam pools and certification cold probes skip unverified imports. Never retroactive (earlier attempts keep `not_applicable`; replay reads the stored column), no kill switch re-enables certification (canonical sources S1, built as `mvp-0.15`, a placeholder tag, and relabelled at its merge) |
| `mvp-0.19` | successor to `mvp-0.18` changing serving only: intervention needs (the primed-retry handler, `learnloop generate-diagnostics`) are fulfilled from the learner's textbook exercises (key-checked, validated and, for discriminate, through the follow-up chooser's own gate) before generating (canonical sources S2b, built as `mvp-0.16` and relabelled at its merge; kill switch `source_service.source_first_needs`) |
| `mvp-0.20` | successor to `mvp-0.19` folding the route check's protective core into the blind grader's one call: the prompt's own-route rules (each criterion graded on the learner's own route; a criterion phrased in one method is met by any valid method; mark down only by quoting the failing step verbatim; say so rather than mark down a route it cannot verify) and one deterministic rule over the grader's output (on a route the grader reads as divergent, a mark-down with no verbatim quote in the learner's words — the answer, or the learner's clarification reply, never the question — an omitted criterion, and a mark-down the grader itself declares it cannot verify are unassessed; nothing then assessed and nothing validated holds the grade for review; a conclusion that differs from the reference and fatal errors keep their mark-downs; each ruled grade's verdict appends to `judgment_ledger`, task `own_route_rule`, a regrade superseding it — as `not_checked` when the rule did not run over the new grade, which also closes an mvp-0.17 `proof_route_check` verdict). Prompt and calibration identity gain `+own-route-v1`; replay reads the blind record as written; the projection namespace is unchanged (route-check-in-grader, built as `mvp-0.18`, a placeholder tag, and relabelled at its merge; kill switch `proof_check.enabled`) |
| `mvp-0.21` | successor to `mvp-0.20` changing serving only (value-of-information stopping, built as `mvp-0.17`, a placeholder tag, with migrations 187/188, and relabelled `mvp-0.21` with migrations 200/201 at its merge). Part 1 lifts four count caps onto value of information (`diagnosis/voi_stopping.py`): a probe episode keeps asking (and, when its next observation no longer pays, closes its block and completes with `value_of_information_stop`, migration 200), a further follow-up on an LO in a session is queued, a further teach-back is kept and a due project probe enters the daily plan while the next observation's value pays for its minutes (robust EVSI and `rank_feasible`'s stop rule where the plausible hypotheses route to different repairs, otherwise the robust EIG at `robust_composition`'s heuristic 60 minutes a nat), each decision logged as a forecast (its own receipts, and main's `voi_forecasts` behind `evsi.forecast_logging`); kill switch `voi_stopping.enabled` with a sub-switch per site, the former caps the switched-off path; the multi-family EVSI study's ranks 1-3 behind `voi_stopping.robust_gate_with_value`, `lookahead_max_checks` and `robust_quantile`, and rank 4 (the measured unresolved cost) behind `evsi.measured_loss_enabled` (off). Part 2 makes the probe hypothesis lane read the diagnoser's verdict through the diagnosis overlay and hold out an event whose diagnosis is pending (kill switch `diagnosis.probe_lane_reads_diagnosis`, pending rule `diagnosis.probe_lane_pending`). Migration 200 only widens `probe_episodes` (the new completion reason and `completion_detail_json`); migration 201 adds the `followup_value_decisions` receipt; no projection change |
| `mvp-0.22` | successor to `mvp-0.21` changing serving only (Tier 1, the Decider migration, owner decision 2026-10-13; built as `mvp-0.20`, a placeholder tag, and relabelled at its merge): the Decider, a fast typed decision model, decides the small judgments `[decider_routes]` names (learner-text gap pairs, "needed?" and kind; misconception matching; the offline review's pattern links; question classification; contamination leak and reveal verdicts) by the argmax of one typed choice (a tie for the top option is no answer), each with its LLM as fallback when the Decider is unavailable, refused for spend, failing or tied, and its own kill switch (false: that judgment's `mvp-0.21` path). Recorded history keeps its meaning; a Decider link joins T1's recurrence groups only when it was recorded authoritative at `mvp-0.22` or later. The facet span-support check (`decider_routes.facet_span_support`) is a content path at every version |
| `mvp-0.23` | successor to `mvp-0.22` changing serving only (router R2a, the staged frame on Today, owner-directed 2026-10-13; built as `mvp-0.23`, a placeholder tag, with migration 205, and landed keeping its tag with migration 202): Today is composed by the staged frame, DL1's lanes and `lane_quota_v1` over the set the P4 constraint engine admits against one bounded controller snapshot, so a block loses only the items a named hard constraint refuses (a quick check on a surface already seen or of unknown freshness, a surface reserved for an assessment, an inactive or unrenderable item; each refusal logged under `exclusions_json.named`) and is otherwise DL1's block in DL1's order, and `golden_path.advance` goes through the P2 bridge (D13: a requested state other than the canonical successor is the learner's own choice, a staged veto defers the step in one plain sentence). Kill switch `router.enabled` (off: `mvp-0.22`'s serving exactly). No model is called. Its receipts act at every version: the exact `plan_presentations` row an answer binds to (`practice_attempts.plan_presentation_id`), outcomes v2 (`action_binding`), the EVSI report v6's exact staged join and the stored learner-state card (`router_decision_payloads`, never sent). Migration 202 rebuilds `router_decisions` (the `plan_interrupt` kind for R2c) and adds those tables and columns; no projection change |
| `mvp-0.24` | successor to `mvp-0.23` changing serving only (router R2b + R2c under one successor, owner decisions 2026-10-13; built as `mvp-0.24`, a placeholder tag, and landed keeping its tag after RW3a, the tutor delivery fixes and GLM-OCR, which took no successor; no migration): Today's next block is a logged draw from the model mixture (`model_mixture`, `router_mixture_v1`): the staged rule's pick, the Decider's and the router LLM's distributions over the top-k reversible candidates mixed with a floor for each, π = (1 − kε)(w_s·δ_staged + w_d·p_decider + w_l·p_llm) + ε, the draw seeded and its propensity exact and recomputable from the row; a model that times out, fails, answers outside its contract or is refused for spend gives its weight to the rule (`fallback`). The models are asked off the hot path: a read never waits (the plan says the block is being chosen), a serving step waits at most `router.timeout_seconds`. A placeable mid-block follow-up is a logged `plan_interrupt` decision (join now or wait for the next block) from each model's `intervene_now`, after the P4 constraint engine has checked it (`router.restraint`). The models' `teach_first` / `will_pass_next` sensors are logged only; graded teach-back dialogues are summarized into the card's typed evidence; similar past decisions (`decision/context` embeddings, matured and from another session and plan) are retrieved and shown to the models on a logged random half. Every metered request (the query embedding and the summaries included) is admitted by the `$5/day` guard `router.max_daily_cost_usd` in its own start receipt; subscription routes are recorded, never refused. Kill switches `router.mode = "staged"` (`mvp-0.23`'s serving exactly), `router.restraint = false`, `router.enabled = false` (`mvp-0.22`'s plan). Replay never asks a model: the decisions are raw ledger rows; no projection change |

The chain is linear: each successor means its predecessor's semantics plus its own change, so a gate asks "is this version at or after X" through an explicit set derived from `SUCCESSOR_CHAIN` (`DIAGNOSIS_SPLIT_VERSIONS` = `mvp-0.10` to `mvp-0.24`; `PLACEMENT_VERSIONS` = `mvp-0.11` to `mvp-0.24`; `RECURRENCE_GROUP_VERSIONS` = `mvp-0.12` to `mvp-0.24`; `STUCK_PROMPT_VERSIONS` = `mvp-0.13` to `mvp-0.24`; `DAILY_PLAN_VERSIONS` = `mvp-0.14` to `mvp-0.24`; `PROBE_TIE_VERSIONS` = `mvp-0.15` to `mvp-0.24`; `LEARNER_TEXT_GAP_VERSIONS` = `mvp-0.16` to `mvp-0.24`; `SOURCE_REFERENCE_GATE_VERSIONS` = `mvp-0.18` to `mvp-0.24`; `SOURCE_FIRST_NEEDS_VERSIONS` = `mvp-0.19` to `mvp-0.24`; `ROUTE_RULES_VERSIONS` = `mvp-0.20` to `mvp-0.24`; `VOI_STOPPING_VERSIONS` = `mvp-0.21` to `mvp-0.24`; `DECIDER_TIER1_VERSIONS` = `mvp-0.22` to `mvp-0.24`; `ROUTER_STAGED_FRAME_VERSIONS` = `mvp-0.23`, `mvp-0.24`; `ROUTER_MIXTURE_VERSIONS` = `mvp-0.24`; mvp-0.17's separate check has no gate any more), never by equality. New vaults start at `LATEST_ALGORITHM_VERSION`, the chain's last tag (`mvp-0.24` today; owner decision 2026-10-12), so a successor merge appends its tag to `SUCCESSOR_CHAIN` (one line; LATEST, every gate and the template follow) and records its defaults snapshot; existing vaults keep their version until the owner runs `learnloop upgrade`, which targets `mvp-0.24` by default (from `mvp-0.23`, or from `mvp-0.9` to `mvp-0.22` through the chain; T1's same-cause guard at `mvp-0.12` is advisory unless `recurrence.require_guard = true`); `--to mvp-0.10` to `--to mvp-0.23` still reach those tags.

Successor sets are explicit so a new version does not accidentally fall back to a legacy projection through an equality check.

## Defaults fingerprint

Omitted configuration defaults are frozen per algorithm version by a CI fingerprint. A minimal vault therefore remains reproducible without writing every default into `learnloop.toml`. Changing a behavior-bearing default requires an explicit version/fingerprint decision. Each recorded fingerprint is the decision-only template rendered at its own version (`config.template.defaults_fingerprint_for_version`), so every version keeps its snapshot whichever version new vaults start at.

## Change protocol

1. Decide whether persisted meaning changes; if yes, add an immediate-successor algorithm version.
2. Keep raw ledgers and receipts immutable; append correction/reinterpretation events.
3. Implement an explicit upgrade that prepares candidate projection before atomic config replacement.
4. Update the effective-default fingerprint.
5. Classify new tables and assign derived rebuild ownership.
6. Extend replay-completeness and exact golden rebuild tests.
7. Run a shadow rebuild and inspect mastery/facet/schedule deltas while proving the live hash unchanged.
8. Exercise predecessor-to-successor fixture upgrade, FK checks, doctor, and idempotent second rebuild.

^change-protocol

## Schema versus algorithm version

Migration schema version describes storage shape; algorithm version describes interpretation. A migration may prepare tables for a future algorithm without activating it. An algorithm upgrade may reuse the same schema but rebuild projections under new semantics.

## Compatibility

`learnloop.substrate.compat` is frozen old-vault machinery. A behavior change there requires a separate compatibility decision and historical fixture; it is never incidental cleanup inside an algorithm bump.

## Evaluation

Rebuild equality proves reproducibility, not benefit. Candidate policy needs simulation/prequential metrics, shadow diffs, and explicit owner review. See [[Testing and Invariants#When changing algorithms]].

## Tests

- `tests/test_mvp09_upgrade.py`
- `tests/test_rebuild_orchestrator.py`
- `tests/test_shadow_rebuild.py`
- default/config fingerprint tests
- historical fixture migration/replay suites

