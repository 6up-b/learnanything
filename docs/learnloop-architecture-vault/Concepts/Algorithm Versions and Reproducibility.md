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
| `mvp-0.22-placeholder` | successor to `mvp-0.20` (method-explicit items, owner rule 2026-10-13; a placeholder tag relabelled at its merge after VOI v2's `mvp-0.21` and the Decider migration): rubric criteria name the fact a step establishes, and an item whose target IS a method states it ("Use {method} in your answer.") and records it as `PracticeItem.required_method`. The own-route rules become `own-route-v2`: the policy carries the required method the answer's assessment contract froze when the item was presented (never one the item gained later, at grading or regrading; a contract that froze none gives none; a regrade of a required-method item reads the statement and rubric from that same contract and its rows cite it) when the prompt the learner answered requires it, and a criterion tied to it is graded on use of that method, so on a route the grader reads as divergent its mark-down needs no quoted wrong step (the route is the evidence) and neither PF-c's gate nor the unlocated rule unassesses it (the grader's own "cannot verify" still does); every other criterion keeps `mvp-0.20`'s rules. The blind record's `proof_route_check` adds `required_method` and `method_route_criterion_ids`; prompt and calibration identity gain `+own-route-v2`; replay reads every record as written; the projection namespace is unchanged (kill switch `required_method.enabled`, off grading exactly as `mvp-0.20`). Generation phrasing criteria by fact, doctor's `criterion:method_phrased` and `learnloop grading method-phrasing`'s repair proposals are content paths behind no tag |

The chain is linear: each successor means its predecessor's semantics plus its own change, so a gate asks "is this version at or after X" through an explicit set derived from `SUCCESSOR_CHAIN` (`DIAGNOSIS_SPLIT_VERSIONS` = `mvp-0.10` to `mvp-0.22-placeholder`; `PLACEMENT_VERSIONS` = `mvp-0.11` to `mvp-0.22-placeholder`; `RECURRENCE_GROUP_VERSIONS` = `mvp-0.12` to `mvp-0.22-placeholder`; `STUCK_PROMPT_VERSIONS` = `mvp-0.13` to `mvp-0.22-placeholder`; `DAILY_PLAN_VERSIONS` = `mvp-0.14` to `mvp-0.22-placeholder`; `PROBE_TIE_VERSIONS` = `mvp-0.15` to `mvp-0.22-placeholder`; `LEARNER_TEXT_GAP_VERSIONS` = `mvp-0.16` to `mvp-0.22-placeholder`; `SOURCE_REFERENCE_GATE_VERSIONS` = `mvp-0.18` to `mvp-0.22-placeholder`; `SOURCE_FIRST_NEEDS_VERSIONS` = `mvp-0.19` to `mvp-0.22-placeholder`; `ROUTE_RULES_VERSIONS` = `mvp-0.20`, `mvp-0.22-placeholder`; `METHOD_EXPLICIT_VERSIONS` = `mvp-0.22-placeholder`; mvp-0.17's separate check has no gate any more), never by equality. New vaults start at `LATEST_ALGORITHM_VERSION`, the chain's last tag (`mvp-0.22-placeholder` on this branch, a placeholder relabelled at its merge; owner decision 2026-10-12), so a successor merge appends its tag to `SUCCESSOR_CHAIN` (one line; LATEST, every gate and the template follow) and records its defaults snapshot; existing vaults keep their version until the owner runs `learnloop upgrade`, which targets `mvp-0.22-placeholder` by default (from `mvp-0.20`, or from `mvp-0.9` to `mvp-0.19` through the chain; T1's same-cause guard at `mvp-0.12` is advisory unless `recurrence.require_guard = true`); `--to mvp-0.10` to `--to mvp-0.20` still reach those tags.

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

