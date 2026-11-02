---
title: "learnloop.attempts.stuck"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/stuck.py"
source_paths:
  - "src/learnloop/attempts/stuck.py"
source_commit: "dcb96638dc5d8b8a968192f860d17075d578ea1f"
source_commit_timestamp: "2026-10-13T00:46:15-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.stuck module"
  - "src/learnloop/attempts/stuck.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.stuck`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.stuck` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: "Write what you can" replaces "I don't know" (``mvp-0.13``).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/stuck.py](../../../../../../src/learnloop/attempts/stuck.py) |
| Source lines | 506 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `dcb96638dc5d8b8a968192f860d17075d578ea1f` |
| Commit timestamp | `2026-10-13T00:46:15-04:00` |

## Public API

- `stuck_prompt_active(vault: Any) -> bool` ([source](../../../../../../src/learnloop/attempts/stuck.py), line 70) — Does this vault offer "I'm stuck" for NEW answers?
- `stuck_answer_prompt() -> dict[str, str]` ([source](../../../../../../src/learnloop/attempts/stuck.py), line 84) — What the blind grader is told about how the answer was asked for.
- `stuck_attempt_type(allowed: list[str] | tuple[str, ...] | None, *, hints_used: int=0, probe: bool=False) -> str` ([source](../../../../../../src/learnloop/attempts/stuck.py), line 94) — The ordinary attempt type a stuck answer records on this item.
- `is_empty_stuck(draft: Any) -> bool` ([source](../../../../../../src/learnloop/attempts/stuck.py), line 115) — A declared-stuck draft with nothing written (the deterministic zero).
- `class StuckReading(WireModel)` ([source](../../../../../../src/learnloop/attempts/stuck.py), line 123) — How the grader read an answer written under the stuck prompt.
- `verified_stuck_reading(reading: StuckReading, learner_answer_md: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/stuck.py), line 169) — The persisted marker: the reading plus whether its quote is verbatim.
- `record_stuck_reading_judgment(connection: Any, *, attempt_id: str, marker: Mapping[str, Any], judge_model: str | None, prompt_version: str, input_hash: str, created_at: str) -> str` ([source](../../../../../../src/learnloop/attempts/stuck.py), line 209) — Append the grader's reading of a stuck answer to ``judgment_ledger``.
- `stuck_answers(connection: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/attempts/stuck.py), line 338) — Every stuck answer, its text and its CURRENT grader reading (read-only).
- `stuck_answer(connection: Any, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/attempts/stuck.py), line 383) — One stuck answer by its id: the row :func:`stuck_answers` gives it.
- `stuck_answer_summary(connection: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/stuck.py), line 433) — Aggregate-only owner view: what to watch after mvp-0.13 goes live.

### Module constants

- `STUCK_CONTROL_LABEL` ([src/learnloop/attempts/stuck.py](../../../../../../src/learnloop/attempts/stuck.py), line 43)
- `STUCK_PROMPT_TEXT` ([src/learnloop/attempts/stuck.py](../../../../../../src/learnloop/attempts/stuck.py), line 44)
- `STUCK_ANSWER_PROMPT_KIND` ([src/learnloop/attempts/stuck.py](../../../../../../src/learnloop/attempts/stuck.py), line 46)
- `STUCK_PROMPT_VERSION_SUFFIX` ([src/learnloop/attempts/stuck.py](../../../../../../src/learnloop/attempts/stuck.py), line 48)
- `STUCK_READING_KEY` ([src/learnloop/attempts/stuck.py](../../../../../../src/learnloop/attempts/stuck.py), line 51)
- `STUCK_READING_VERSION` ([src/learnloop/attempts/stuck.py](../../../../../../src/learnloop/attempts/stuck.py), line 52)
- `STUCK_READING_JUDGMENT_TASK` ([src/learnloop/attempts/stuck.py](../../../../../../src/learnloop/attempts/stuck.py), line 57)
- `EMPTY_STUCK_LOCAL_GRADER_ID` ([src/learnloop/attempts/stuck.py](../../../../../../src/learnloop/attempts/stuck.py), line 61)
- `EMPTY_STUCK_GRADER_TIER` ([src/learnloop/attempts/stuck.py](../../../../../../src/learnloop/attempts/stuck.py), line 62)
- `EMPTY_STUCK_EVIDENCE` ([src/learnloop/attempts/stuck.py](../../../../../../src/learnloop/attempts/stuck.py), line 63)
- `EMPTY_STUCK_FEEDBACK` ([src/learnloop/attempts/stuck.py](../../../../../../src/learnloop/attempts/stuck.py), line 64)
- `STUCK_PROMPT_RULES` ([src/learnloop/attempts/stuck.py](../../../../../../src/learnloop/attempts/stuck.py), line 152)
- `_STUCK_ATTEMPT_COLUMNS` ([src/learnloop/attempts/stuck.py](../../../../../../src/learnloop/attempts/stuck.py), line 273)

### Explicit exports

`__all__` declares:

- `EMPTY_STUCK_EVIDENCE`
- `EMPTY_STUCK_FEEDBACK`
- `EMPTY_STUCK_GRADER_TIER`
- `EMPTY_STUCK_LOCAL_GRADER_ID`
- `STUCK_ANSWER_PROMPT_KIND`
- `STUCK_CONTROL_LABEL`
- `STUCK_PROMPT_RULES`
- `STUCK_PROMPT_TEXT`
- `STUCK_PROMPT_VERSION_SUFFIX`
- `STUCK_READING_JUDGMENT_TASK`
- `STUCK_READING_KEY`
- `STUCK_READING_VERSION`
- `StuckReading`
- `is_empty_stuck`
- `record_stuck_reading_judgment`
- `stuck_answer`
- `stuck_answer_prompt`
- `stuck_answer_summary`
- `stuck_answers`
- `stuck_attempt_type`
- `stuck_prompt_active`
- `verified_stuck_reading`

## Internal implementation anchors

- `_squash(text: str) -> str` ([source](../../../../../../src/learnloop/attempts/stuck.py), line 165)
- `_current_stuck_judgment(connection: Any, attempt_id: str) -> Any` ([source](../../../../../../src/learnloop/attempts/stuck.py), line 190) — The attempt's current stuck-reading judgment row (None when there is none).
- `_has_table(connection: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/attempts/stuck.py), line 254)
- `_has_stuck_column(connection: Any) -> bool` ([source](../../../../../../src/learnloop/attempts/stuck.py), line 263)
- `_judged_reading(row: Any) -> _Reading` ([source](../../../../../../src/learnloop/attempts/stuck.py), line 281) — (judgment id, graded at, reading) from a current stuck-reading judgment.
- `_blind_reading(record_id: Any, created_at: Any, record_json: Any) -> _Reading` ([source](../../../../../../src/learnloop/attempts/stuck.py), line 291) — (blind record id, graded at, reading) from a blind grade record.
- `_stuck_row(attempt: Any, blind: _Reading | None, judged: _Reading | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/stuck.py), line 302)
- `_seconds_between(start: str | None, end: str | None) -> float | None` ([source](../../../../../../src/learnloop/attempts/stuck.py), line 420)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] — imports `STUCK_PROMPT_RULES`, `STUCK_PROMPT_VERSION_SUFFIX`, `StuckReading`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `EMPTY_STUCK_EVIDENCE`, `EMPTY_STUCK_FEEDBACK`, `EMPTY_STUCK_GRADER_TIER`, `EMPTY_STUCK_LOCAL_GRADER_ID`, `STUCK_READING_KEY`, `is_empty_stuck`, `record_stuck_reading_judgment`, `stuck_answer_prompt`, `stuck_prompt_active`, `verified_stuck_reading`; statically calls `is_empty_stuck`, `record_stuck_reading_judgment`, `stuck_answer_prompt`, `stuck_prompt_active`, `verified_stuck_reading`
- [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]] — imports `STUCK_PROMPT_RULES`, `STUCK_PROMPT_VERSION_SUFFIX`, `StuckReading`
- [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] — imports `StuckReading`
- [[Reference/Modules/learnloop/attempts/hint_fold|learnloop.attempts.hint_fold]] — imports `stuck_attempt_type`; statically calls `stuck_attempt_type`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `STUCK_READING_KEY`, `record_stuck_reading_judgment`, `stuck_answer_prompt`, `verified_stuck_reading`; statically calls `record_stuck_reading_judgment`, `stuck_answer_prompt`, `verified_stuck_reading`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `stuck_attempt_type`, `stuck_prompt_active`; statically calls `stuck_attempt_type`, `stuck_prompt_active`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]] — imports `module`; statically calls `stuck_answer`, `stuck_answers`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `stuck_answer_summary`; statically calls `stuck_answer_summary`
- [[Reference/Modules/learnloop/field/signals|learnloop.field.signals]] — imports `stuck_answers`; statically calls `stuck_answers`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `STUCK_CONTROL_LABEL`, `STUCK_PROMPT_TEXT`, `stuck_prompt_active`; statically calls `stuck_prompt_active`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `stuck_prompt_active`; statically calls `stuck_prompt_active`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `stuck_attempt_type`, `stuck_prompt_active`; statically calls `stuck_attempt_type`, `stuck_prompt_active`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `stuck_attempt_type`; statically calls `stuck_attempt_type`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `STUCK_PROMPT_VERSIONS`
- [[Reference/Modules/learnloop/attempt_types|learnloop.attempt_types]] — imports `default_attempt_type`; calls `default_attempt_type`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `json`, `re`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]], [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]], [[Reference/Modules/learnloop/attempts/hint_fold|learnloop.attempts.hint_fold]] and 9 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_learner_text_gaps_composition.py](../../../../../../tests/test_learner_text_gaps_composition.py) — direct import
  - `test_stuck_answer_reads_one_attempt_exactly_as_stuck_answers_does`
  - `test_the_default_adapter_reads_mains_stuck_module_by_id_without_a_scan`
- [tests/test_learner_text_gaps_rereview.py](../../../../../../tests/test_learner_text_gaps_rereview.py) — direct import
  - `test_rr_f1_a_job_stopped_after_a_write_logs_the_write_as_failed_and_undoable`
  - `test_rr_f1_a_stuck_retry_finishes_the_recorded_creation_whatever_the_second_reading`
  - `test_rr_f4_the_stuck_modules_own_per_attempt_reader_is_preferred`
- [tests/test_learner_text_gaps_review.py](../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f8_a_stuck_answer_is_queued_at_recording_without_a_diagnosis`
  - `test_f8_the_adapter_reads_the_marker_before_scanning`
- [tests/test_mvp011_upgrade.py](../../../../../../tests/test_mvp011_upgrade.py) — direct import
  - `test_new_vaults_start_at_the_latest_version`
- [tests/test_mvp013_upgrade.py](../../../../../../tests/test_mvp013_upgrade.py) — direct import
  - `test_an_earlier_vault_goes_through_mvp012s_guard`
  - `test_kill_switch_keeps_the_version_and_every_predecessor`
  - `test_only_mvp013_offers_the_stuck_control`
  - `test_upgrade_from_mvp012_flips_rebuilds_and_preserves_raw_history`
- [tests/test_mvp014_upgrade.py](../../../../../../tests/test_mvp014_upgrade.py) — direct import
  - `test_an_earlier_vault_goes_through_mvp012s_guard`
  - `test_the_plan_serves_only_at_the_successor_with_the_switch_on`
  - `test_upgrade_from_mvp013_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp015_upgrade.py](../../../../../../tests/test_mvp015_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
- [tests/test_mvp016_upgrade.py](../../../../../../tests/test_mvp016_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
- [tests/test_mvp017_upgrade.py](../../../../../../tests/test_mvp017_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
- [tests/test_mvp020_upgrade.py](../../../../../../tests/test_mvp020_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
- [tests/test_reading_step_switch.py](../../../../../../tests/test_reading_step_switch.py) — direct import
  - `test_the_reading_step_acts_wherever_the_plan_acts_behind_its_switch`
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — direct import
  - `test_a_joint_regrade_rereads_the_stuck_answer_and_supersedes`
  - `test_a_partial_stuck_answer_is_graded_blind_at_standard_mass_and_diagnosed`
  - `test_a_quote_that_is_not_verbatim_is_dropped_but_the_flag_stands`
  - `test_a_regrade_appends_a_superseding_stuck_judgment`
  - `test_a_stuck_answer_on_a_choice_item_goes_to_the_grader_not_the_letter_shortcut`
  - `test_an_empty_stuck_answer_scores_zero_without_a_model_call`
  - `test_an_ordinary_answer_keeps_its_prompt_and_context_exactly`
  - `test_confusion_is_read_and_signalled_in_both_grading_modes`
  - `test_confusion_text_is_marked_and_becomes_a_fast_track_blocking_signal`
  - `test_stuck_attempt_type_matches_the_answer_box`
  - `test_the_owner_summary_counts_text_share_confusion_and_grading_runs`
  - `test_the_stuck_reading_appends_a_judgment_with_the_blind_record`
  - `test_the_successor_gates_the_control_and_the_switch_restores_it`
- [tests/test_stuck_prompt_composition.py](../../../../../../tests/test_stuck_prompt_composition.py) — direct import
  - `test_a_stuck_answers_pfc_unverified_criteria_are_unassessed`
- [tests/test_stuck_prompt_replay.py](../../../../../../tests/test_stuck_prompt_replay.py) — direct import

## Modification guidance

- Change stuck policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/stuck.py](../../../../../../src/learnloop/attempts/stuck.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
