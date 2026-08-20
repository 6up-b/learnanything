---
title: "learnloop.diagnosis.diagnosis_adjudication"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/diagnosis_adjudication.py"
source_paths:
  - "src/learnloop/diagnosis/diagnosis_adjudication.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.diagnosis_adjudication module"
  - "src/learnloop/diagnosis/diagnosis_adjudication.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.diagnosis_adjudication`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.diagnosis_adjudication` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Diagnosis adjudication: the ground-truth store for diagnostic quality.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/diagnosis_adjudication.py](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py) |
| Source lines | 865 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class DiagnosisSnapshot` ([source](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 138) — What the system produced, frozen at adjudication time.
  - `as_dict(self) -> dict[str, Any]` (line 173; public)
- `anchor_key(anchor: Mapping[str, Any] | None) -> str` ([source](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 203) — A comparable key for a first-divergence anchor.
- `diagnosis_snapshot(repository: Repository, attempt_id: str) -> DiagnosisSnapshot | None` ([source](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 271) — Freeze the system's diagnosis for one attempt, or None if it has none.
- `class AdjudicationQueueEntry` ([source](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 402)
  - `as_dict(self) -> dict[str, Any]` (line 413; public)
- `latest_learner_report(repository: Repository, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 427) — The most recent §5.6 typed self-report for an attempt, any factor status.
- `adjudication_queue(repository: Repository, *, learning_object_id: str | None=None, reasons: Sequence[str] | None=None, limit: int | None=20) -> list[AdjudicationQueueEntry]` ([source](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 479) — Attempts worth a verdict, highest information first.
- `append_diagnosis_adjudication(repository: Repository, *, attempt_id: str, verdict: str, adjudicated_anchor: Mapping[str, Any] | None=None, adjudicated_repair_md: str | None=None, adjudicated_repair_class_id: str | None=None, queue_reason: str | None=None, adjudicator_source: str='human_owner', rationale: str | None=None, learner_report_id: str | None=None, supersedes_id: str | None=None, vault: LoadedVault | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 547) — Append one verdict on one diagnosis.
- `diagnosis_adjudication_scoreboard(repository: Repository, *, group_by: str | None='version', attempt_ids: Sequence[str] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 760) — The §3 B5 metrics this store owns, over the active verdicts.
- `adjudicated_ground_truth(repository: Repository, *, attempt_ids: Sequence[str] | None=None) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 832) — Adjudicated labels keyed by attempt — the join key for §3 B4.

### Module constants

- `ADJUDICATION_STORE_VERSION` ([src/learnloop/diagnosis/diagnosis_adjudication.py](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 56)
- `VERDICTS` ([src/learnloop/diagnosis/diagnosis_adjudication.py](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 60)
- `ABSTENTION_VERDICTS` ([src/learnloop/diagnosis/diagnosis_adjudication.py](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 70)
- `FILLED_VERDICTS` ([src/learnloop/diagnosis/diagnosis_adjudication.py](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 72)
- `ANCHOR_REQUIRED_VERDICTS` ([src/learnloop/diagnosis/diagnosis_adjudication.py](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 77)
- `ANCHOR_SCORED_VERDICTS` ([src/learnloop/diagnosis/diagnosis_adjudication.py](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 82)
- `ANCHOR_CORRECT_VERDICTS` ([src/learnloop/diagnosis/diagnosis_adjudication.py](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 84)
- `QUEUE_REASONS` ([src/learnloop/diagnosis/diagnosis_adjudication.py](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 86)
- `_QUEUE_PRIORITY` ([src/learnloop/diagnosis/diagnosis_adjudication.py](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 100)
- `ADJUDICATOR_SOURCES` ([src/learnloop/diagnosis/diagnosis_adjudication.py](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 112)
- `ANCHOR_KINDS` ([src/learnloop/diagnosis/diagnosis_adjudication.py](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 118)
- `_CONFIRMING_REPORT` ([src/learnloop/diagnosis/diagnosis_adjudication.py](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 127)
- `_WHITESPACE` ([src/learnloop/diagnosis/diagnosis_adjudication.py](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 129)

## Internal implementation anchors

- `_abstention_state(receipt: Mapping[str, Any], telemetry: Mapping[str, Any]) -> tuple[bool, str]` ([source](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 231) — Did the diagnosis decline to name a cause, and on what basis?
- `_queue_reason(snapshot: DiagnosisSnapshot, report: Mapping[str, Any] | None) -> tuple[str, str]` ([source](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 451)
- `_empty_group(**identity: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 710)
- `_finalize(group: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py), line 724)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/diagnosis|learnloop.cli.diagnosis]] — imports `adjudication_queue`, `append_diagnosis_adjudication`, `diagnosis_adjudication_scoreboard`; statically calls `adjudication_queue`, `append_diagnosis_adjudication`, `diagnosis_adjudication_scoreboard`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `anchor_key`; statically calls `anchor_key`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `FILLED_VERDICTS`, `adjudicated_ground_truth`, `diagnosis_adjudication_scoreboard`; statically calls `adjudicated_ground_truth`, `diagnosis_adjudication_scoreboard`
- [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]] — imports `ABSTENTION_VERDICTS`, `ADJUDICATOR_SOURCES`, `ANCHOR_KINDS`, `FILLED_VERDICTS`, `QUEUE_REASONS`, `VERDICTS`, `adjudication_queue`, `append_diagnosis_adjudication`, `diagnosis_adjudication_scoreboard`, `diagnosis_snapshot`; statically calls `adjudication_queue`, `append_diagnosis_adjudication`, `diagnosis_adjudication_scoreboard`, `diagnosis_snapshot`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `causal_episode_for_attempt`; calls `causal_episode_for_attempt`
- [[Reference/Modules/learnloop/tutor/durable_promotion|learnloop.tutor.durable_promotion]] — imports `apply_adjudicated_belief_effects`; calls `apply_adjudicated_belief_effects`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/diagnosis|learnloop.cli.diagnosis]], [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]], [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]], [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_diagnosis_adjudication.py](../../../../../../tests/test_diagnosis_adjudication.py) — direct import
  - `test_abstention_precision_and_recall_watch_both_tails`
  - `test_abstentions_outrank_the_unflagged_stratum`
  - `test_anchor_asserting_verdicts_require_an_anchor`
  - `test_attempt_without_a_diagnosis_receipt_cannot_be_adjudicated`
  - `test_cli_scoreboard_warns_when_no_abstention_case_exists`
  - `test_contest_leads_the_queue_and_is_provenance_never_the_verdict`
  - `test_correct_verdict_inherits_the_system_choice_and_pins_every_version`
  - `test_empty_denominators_report_null_not_a_flattering_one`
  - `test_ground_truth_export_is_shaped_for_the_planted_overlap`
  - `test_queue_reason_is_persisted_so_selection_bias_is_auditable`
  - `test_repair_class_outside_the_offered_set_is_rejected`
  - `test_scoreboard_groups_by_prompt_version_and_model`
  - `test_store_is_append_only_and_a_second_opinion_supersedes`
  - `test_verdict_must_agree_with_what_the_system_actually_did`
- [tests/test_durable_promotion_arms.py](../../../../../../tests/test_durable_promotion_arms.py) — direct import
  - `test_a_promoted_belief_is_not_resolved_away_by_the_next_posterior_pass`
  - `test_a_verdict_against_an_abstention_never_promotes`
  - `test_a_verdict_recorded_without_a_vault_is_picked_up_by_the_sweep`
  - `test_a_withdrawn_belief_is_not_quietly_re_promoted`
  - `test_adjudicated_promotion_is_idempotent`
  - `test_an_ambiguous_cause_set_promotes_nothing`
  - `test_an_overturned_belief_the_learner_never_saw_is_retracted_but_not_narrated`
  - `test_an_overturning_verdict_withdraws_a_surfaced_belief_once`
  - `test_correct_verdict_promotes_the_cause_the_system_asserted`
  - `test_every_verdict_has_a_promotion_decision`
  - `test_replay_reproduces_the_same_belief_state`
  - `test_the_trace_consistency_veto_outranks_a_human_verdict`
  - `test_wrong_repair_is_neutral_because_the_anchor_was_ruled_correct`
- [tests/test_scoreboard.py](../../../../../../tests/test_scoreboard.py) — direct import
  - `test_adjudication_metrics_are_composed_not_recomputed`
  - `test_adjudication_metrics_track_the_real_store`
  - `test_agreement_is_computed_once_a_planted_side_exists`
  - `test_harmful_write_rate_reports_both_arms`
  - `test_planted_side_absent_reports_no_producer_not_zero_overlap`
- [tests/test_sidecar_adjudication.py](../../../../../../tests/test_sidecar_adjudication.py) — direct import
  - `test_queue_carries_the_words_the_learner_was_shown`
  - `test_queue_is_stratified_contests_first_then_abstentions`
  - `test_record_refuses_a_verdict_the_partition_forbids`
  - `test_record_reports_the_belief_effect_the_backend_confirms`
  - `test_scoreboard_keeps_enum_keys_and_refuses_a_flattering_rate`

## Modification guidance

- Change diagnosis adjudication policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/diagnosis_adjudication.py](../../../../../../src/learnloop/diagnosis/diagnosis_adjudication.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
