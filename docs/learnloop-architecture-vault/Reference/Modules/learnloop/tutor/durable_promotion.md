---
title: "learnloop.tutor.durable_promotion"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tutor/durable_promotion.py"
source_paths:
  - "src/learnloop/tutor/durable_promotion.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.tutor"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Tutor and Teach-Back Workflow"
aliases:
  - "learnloop.tutor.durable_promotion module"
  - "src/learnloop/tutor/durable_promotion.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-tutor"
---

# `learnloop.tutor.durable_promotion`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.tutor.durable_promotion` exists within [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] to own the behavior summarized by its module contract: Durable-promotion arms (c) and (d) — the late-evidence path (§5.6).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tutor/durable_promotion.py](../../../../../../src/learnloop/tutor/durable_promotion.py) |
| Source lines | 674 |
| Owning package | [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class BeliefEffect` ([source](../../../../../../src/learnloop/tutor/durable_promotion.py), line 119) — What one late-evidence arm did to durable belief state.
  - `changed(self) -> bool` (line 135; public)
  - `as_dict(self) -> dict[str, Any]` (line 138; public)
- `apply_adjudicated_belief_effects(vault: LoadedVault, repository: Repository, *, attempt_id: str, clock: Clock | None=None) -> BeliefEffect` ([source](../../../../../../src/learnloop/tutor/durable_promotion.py), line 322) — §5.6 arm (d): route the active verdict on ``attempt_id`` into belief state.
- `apply_proved_and_confirmed_promotion(vault: LoadedVault, repository: Repository, *, attempt_id: str, clock: Clock | None=None) -> BeliefEffect` ([source](../../../../../../src/learnloop/tutor/durable_promotion.py), line 516) — §5.6 arm (c): deterministic proof AND learner confirmation, conjunctively.
- `apply_late_promotion_evidence(vault: LoadedVault, repository: Repository, *, attempt_id: str, clock: Clock | None=None) -> list[BeliefEffect]` ([source](../../../../../../src/learnloop/tutor/durable_promotion.py), line 594) — Run both late arms for one attempt.
- `sweep_late_promotion_evidence(vault: LoadedVault, repository: Repository, *, learning_object_id: str, clock: Clock | None=None) -> list[BeliefEffect]` ([source](../../../../../../src/learnloop/tutor/durable_promotion.py), line 620) — Catch up on late evidence for one learning object.

### Module constants

- `PROMOTION_REASON_ADJUDICATED` ([src/learnloop/tutor/durable_promotion.py](../../../../../../src/learnloop/tutor/durable_promotion.py), line 67)
- `PROMOTION_REASON_PROVED_AND_CONFIRMED` ([src/learnloop/tutor/durable_promotion.py](../../../../../../src/learnloop/tutor/durable_promotion.py), line 68)
- `AFFIRMING_VERDICTS` ([src/learnloop/tutor/durable_promotion.py](../../../../../../src/learnloop/tutor/durable_promotion.py), line 77)
- `OVERTURNING_VERDICTS` ([src/learnloop/tutor/durable_promotion.py](../../../../../../src/learnloop/tutor/durable_promotion.py), line 89)
- `NEUTRAL_VERDICTS` ([src/learnloop/tutor/durable_promotion.py](../../../../../../src/learnloop/tutor/durable_promotion.py), line 105)
- `ANY_BELIEF_STATUS` ([src/learnloop/tutor/durable_promotion.py](../../../../../../src/learnloop/tutor/durable_promotion.py), line 115)

## Internal implementation anchors

- `_asserted_hypotheses(repository: Repository, adjudication: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/durable_promotion.py), line 154) — The concrete causes the adjudicated diagnosis actually asserted.
- `_promote_hypothesis(vault: LoadedVault, repository: Repository, hypothesis: Mapping[str, Any], *, reason: str, attempt_id: str, clock: Clock | None) -> tuple[str | None, str | None]` ([source](../../../../../../src/learnloop/tutor/durable_promotion.py), line 191) — Promote the holding-pen candidate behind ``hypothesis``.
- `_withdraw_hypothesis(repository: Repository, hypothesis: Mapping[str, Any], *, clock: Clock | None) -> tuple[str | None, str | None]` ([source](../../../../../../src/learnloop/tutor/durable_promotion.py), line 276) — Retract the durable belief this hypothesis was promoted into.
- `_verified_repair_class_ids(repository: Repository, attempt_id: str) -> set[str]` ([source](../../../../../../src/learnloop/tutor/durable_promotion.py), line 416) — Repair classes this attempt's diagnosis DETERMINISTICALLY proved.
- `_confirmed_hypotheses(repository: Repository, attempt_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/durable_promotion.py), line 477) — Hypotheses the learner said "I believed this" about, on this attempt.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/diagnosis_adjudication|learnloop.diagnosis.diagnosis_adjudication]] — imports `apply_adjudicated_belief_effects`; statically calls `apply_adjudicated_belief_effects`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `sweep_late_promotion_evidence`; statically calls `sweep_late_promotion_evidence`
- [[Reference/Modules/learnloop/learner/independence_audit|learnloop.learner.independence_audit]] — imports `ANY_BELIEF_STATUS`
- [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]] — imports `apply_adjudicated_belief_effects`; statically calls `apply_adjudicated_belief_effects`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `apply_proved_and_confirmed_promotion`; statically calls `apply_proved_and_confirmed_promotion`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `OPEN_SET_CAUSE_ID`, `causal_episode_for_attempt`, `trace_consistent`; calls `causal_episode_for_attempt`, `trace_consistent`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `normalize_text`, `promote_candidate`; calls `normalize_text`, `promote_candidate`
- [[Reference/Modules/learnloop/learner/surfaced_beliefs|learnloop.learner.surfaced_beliefs]] — imports `record_belief_withdrawal`; calls `record_belief_withdrawal`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/diagnosis_adjudication|learnloop.diagnosis.diagnosis_adjudication]], [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]], [[Reference/Modules/learnloop/learner/independence_audit|learnloop.learner.independence_audit]], [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]], [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_durable_promotion_arms.py](../../../../../../tests/test_durable_promotion_arms.py) — direct import
  - `test_a_contest_is_not_a_confirmation`
  - `test_a_deterministic_proof_without_confirmation_does_not_promote`
  - `test_a_verdict_against_an_abstention_never_promotes`
  - `test_a_verdict_recorded_without_a_vault_is_picked_up_by_the_sweep`
  - `test_a_withdrawn_belief_is_not_quietly_re_promoted`
  - `test_adjudicated_promotion_is_idempotent`
  - `test_an_ambiguous_cause_set_promotes_nothing`
  - `test_an_overturning_verdict_withdraws_a_surfaced_belief_once`
  - `test_confirmation_without_a_deterministic_proof_does_not_promote`
  - `test_correct_verdict_promotes_the_cause_the_system_asserted`
  - `test_every_verdict_has_a_promotion_decision`
  - `test_no_verdict_is_a_declined_arm_not_a_crash`
  - `test_proof_plus_confirmation_promotes`
  - `test_replay_reproduces_the_same_belief_state`
  - `test_the_proof_must_be_about_the_confirmed_belief`
  - `test_the_sweep_also_finds_a_confirmation_on_a_superseded_version`
  - `test_the_sweep_reports_nothing_when_there_is_no_late_evidence`
  - `test_the_trace_consistency_veto_outranks_a_human_verdict`
  - `test_wrong_repair_is_neutral_because_the_anchor_was_ruled_correct`

## Modification guidance

- Change durable promotion policy here when tutor owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/tutor/durable_promotion.py](../../../../../../src/learnloop/tutor/durable_promotion.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
