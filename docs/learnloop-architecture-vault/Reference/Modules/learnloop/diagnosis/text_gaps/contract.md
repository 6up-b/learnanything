---
title: "learnloop.diagnosis.text_gaps.contract"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/text_gaps/contract.py"
source_paths:
  - "src/learnloop/diagnosis/text_gaps/contract.py"
source_commit: "b7ea2b2856d7d66e82ebc13a850d701dc2d7cc90"
source_commit_timestamp: "2026-11-02T00:59:12-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.text_gaps"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.text_gaps.contract module"
  - "src/learnloop/diagnosis/text_gaps/contract.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-text-gaps"
---

# `learnloop.diagnosis.text_gaps.contract`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.text_gaps.contract` exists within [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] to own the behavior summarized by its module contract: What a learner text is, how it is read, and the typed questions about it.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py) |
| Source lines | 405 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `b7ea2b2856d7d66e82ebc13a850d701dc2d7cc90` |
| Commit timestamp | `2026-11-02T00:59:12-05:00` |

## Public API

- `class GapReading` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 115) — One reading of a learner text: the kind and the gap as named.
  - `from_gap(cls, gap: LearnerGap | Mapping[str, Any], **extra: Any) -> 'GapReading'` (line 135; public)
  - `named(self) -> dict[str, Any]` (line 146; public)
  - `as_progress(self) -> dict[str, Any]` (line 153; public) — JSON for the job's progress: a retry acts on this reading, never a second one (re-review F1).
  - `from_progress(cls, data: Mapping[str, Any]) -> 'GapReading'` (line 165; public)
  - `names(self, kind: str) -> bool` (line 175; public) — Does this reading name a gap of ``kind`` (so it can be matched)?
- `class LearnerText` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 191) — One learner text the pipeline reads.
  - `anchor(self) -> str | None` (line 233; public)
  - `subject_key(self) -> str` (line 237; public)
- `class NeededVerdict(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 287) — "Is this prerequisite needed to do this item?" (one isolated call).
- `class PrerequisiteDraft(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 294) — The missing prerequisite as a concept, one learning objective and its edge.

### Module constants

- `PIPELINE_VERSION` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 29)
- `PROVENANCE_MECHANISM` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 32)
- `SOURCE_KINDS` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 33)
- `READABLE_SOURCE_KINDS` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 47)
- `NON_SERVING_SOURCE_KINDS` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 62)
- `NOTE_SOURCE_KINDS` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 71)
- `NOTE_UNCHECKPOINTED_FIELDS` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 78)
- `KINDS` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 81)
- `UNREAD` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 82)
- `CHOOSERS` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 83)
- `KIND_TASK` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 86)
- `SAME_PREREQUISITE_TASK` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 87)
- `SAME_BELIEF_TASK` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 88)
- `NEEDED_TASK` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 89)
- `DECIDER_KIND_QUESTION_SET` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 92)
- `DECIDER_PAIR_QUESTION_SET` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 93)
- `DECIDER_NEEDED_QUESTION_SET` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 94)
- `READER_PROMPT_VERSION` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 95)
- `READER_FORMATIVE_PROMPT_VERSION` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 97)
- `READER_NOTE_PROMPT_VERSION` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 99)
- `NEEDED_PROMPT_VERSION` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 100)
- `DRAFT_PROMPT_VERSION` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 101)
- `READER_PURPOSE` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 104)
- `NEEDED_PURPOSE` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 105)
- `DRAFT_PURPOSE` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 106)
- `JUDGE_ROUTE` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 107)
- `READER_ROUTE` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 108)
- `DECIDER_ROUTE` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 109)
- `DRAFT_ROUTE` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 110)
- `EMBEDDING_ROUTE` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 111)
- `KIND_OPTIONS` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 243)
- `KIND_QUESTION` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 251)
- `PAIR_QUESTION_INSTRUCTIONS` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 260)
- `PAIR_OPTIONS` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 264)
- `NEEDED_OPTIONS` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 270)
- `NEEDED_QUESTION` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 275)
- `READER_TASK` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 308)
- `READER_FORMATIVE_TASK` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 318)
- `READER_NOTE_TASK` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 331)
- `NEEDED_TASK_TEXT` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 342)
- `DRAFT_TASK` ([src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 349)

### Explicit exports

`__all__` declares:

- `CHOOSERS`
- `DECIDER_KIND_QUESTION_SET`
- `DECIDER_NEEDED_QUESTION_SET`
- `DECIDER_PAIR_QUESTION_SET`
- `DECIDER_ROUTE`
- `DRAFT_PROMPT_VERSION`
- `DRAFT_PURPOSE`
- `DRAFT_ROUTE`
- `DRAFT_TASK`
- `EMBEDDING_ROUTE`
- `GapReading`
- `JUDGE_ROUTE`
- `KINDS`
- `KIND_OPTIONS`
- `KIND_QUESTION`
- `KIND_TASK`
- `LearnerText`
- `NEEDED_OPTIONS`
- `NEEDED_PROMPT_VERSION`
- `NEEDED_PURPOSE`
- `NEEDED_QUESTION`
- `NEEDED_TASK`
- `NEEDED_TASK_TEXT`
- `NeededVerdict`
- `PAIR_OPTIONS`
- `PAIR_QUESTION_INSTRUCTIONS`
- `PIPELINE_VERSION`
- `PROVENANCE_MECHANISM`
- `PrerequisiteDraft`
- `READER_PROMPT_VERSION`
- `READER_PURPOSE`
- `READER_ROUTE`
- `READER_FORMATIVE_PROMPT_VERSION`
- `READER_FORMATIVE_TASK`
- `NON_SERVING_SOURCE_KINDS`
- `NOTE_SOURCE_KINDS`
- `NOTE_UNCHECKPOINTED_FIELDS`
- `READER_NOTE_PROMPT_VERSION`
- `READER_NOTE_TASK`
- `READABLE_SOURCE_KINDS`
- `READER_TASK`
- `SAME_BELIEF_TASK`
- `SAME_PREREQUISITE_TASK`
- `SOURCE_KINDS`
- `UNREAD`

## Internal implementation anchors

- `_clean(value: Any) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py), line 185)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `LearnerText`, `NEEDED_TASK`, `PROVENANCE_MECHANISM`, `SAME_BELIEF_TASK`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/candidates|learnloop.diagnosis.text_gaps.candidates]] — imports `LearnerText`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `LearnerText`, `NOTE_SOURCE_KINDS`, `NOTE_UNCHECKPOINTED_FIELDS`; statically calls `LearnerText`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `DECIDER_KIND_QUESTION_SET`, `DECIDER_NEEDED_QUESTION_SET`, `DECIDER_PAIR_QUESTION_SET`, `DECIDER_ROUTE`, `DRAFT_PROMPT_VERSION`, `DRAFT_PURPOSE`, `DRAFT_ROUTE`, `DRAFT_TASK`, `EMBEDDING_ROUTE`, `GapReading`, `JUDGE_ROUTE`, `KIND_QUESTION`, `KIND_TASK`, `LearnerText`, `NEEDED_PROMPT_VERSION`, `NEEDED_PURPOSE`, `NEEDED_QUESTION`, `NEEDED_TASK`, `NEEDED_TASK_TEXT`, `NeededVerdict`, `PAIR_OPTIONS`, `PAIR_QUESTION_INSTRUCTIONS`, `PrerequisiteDraft`, `READER_FORMATIVE_PROMPT_VERSION`, `READER_FORMATIVE_TASK`, `READER_NOTE_PROMPT_VERSION`, `READER_NOTE_TASK`, `READER_PROMPT_VERSION`, `READER_PURPOSE`, `READER_ROUTE`, `READER_TASK`; statically calls `GapReading`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/kinds|learnloop.diagnosis.text_gaps.kinds]] — imports `JUDGE_ROUTE`, `LearnerText`, `SAME_BELIEF_TASK`, `SAME_PREREQUISITE_TASK`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `DRAFT_ROUTE`, `GapReading`, `LearnerText`, `NON_SERVING_SOURCE_KINDS`, `NOTE_SOURCE_KINDS`, `NOTE_UNCHECKPOINTED_FIELDS`, `PIPELINE_VERSION`, `PrerequisiteDraft`, `UNREAD`; statically calls `GapReading`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/report|learnloop.diagnosis.text_gaps.report]] — imports `NEEDED_TASK`, `SAME_BELIEF_TASK`, `SAME_PREREQUISITE_TASK`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]] — imports `GapReading`, `LearnerText`; statically calls `GapReading`, `LearnerText`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/tier1|learnloop.diagnosis.text_gaps.tier1]] — imports `DECIDER_PAIR_QUESTION_SET`, `DECIDER_ROUTE`, `GapReading`, `KIND_QUESTION`, `LearnerText`, `NEEDED_QUESTION`, `NEEDED_TASK`; statically calls `GapReading`
- [[Reference/Modules/learnloop/field/signals|learnloop.field.signals]] — imports `NON_SERVING_SOURCE_KINDS`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `ChoiceQuestion`; calls `ChoiceQuestion`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]] — imports `LEARNER_GAP_KINDS`, `LEARNER_GAP_RULES`, `LearnerGap`
- [[Reference/Modules/learnloop/vault/lifecycle|learnloop.vault.lifecycle]] — imports `LEARNER_TEXT_GAP_MECHANISM`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]], [[Reference/Modules/learnloop/diagnosis/text_gaps/candidates|learnloop.diagnosis.text_gaps.candidates]], [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]], [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]], [[Reference/Modules/learnloop/diagnosis/text_gaps/kinds|learnloop.diagnosis.text_gaps.kinds]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_diagnosis_input_provenance.py](../../../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_f2_the_drafter_folds_a_generated_topic_only_under_the_name_it_was_shown`
  - `test_rereview_f2_the_drafter_checks_its_anchor_and_prerequisite_names`
- [tests/test_diagnosis_input_provenance_landing.py](../../../../../../../tests/test_diagnosis_input_provenance_landing.py) — direct import
- [tests/test_followups_batch5_c5_ledger.py](../../../../../../../tests/test_followups_batch5_c5_ledger.py) — direct import
  - `test_a_notes_ledger_verdicts_have_the_shared_shape_and_the_report_reads_them`
- [tests/test_hint_feedback_texts.py](../../../../../../../tests/test_hint_feedback_texts.py) — direct import
  - `test_hint_feedback_is_readable_and_non_serving`
- [tests/test_learner_text_gaps.py](../../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_the_draft_contract_is_strict`
- [tests/test_learner_text_gaps_review.py](../../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f10_the_cycle_is_rechecked_on_the_file_inside_the_lock`
  - `test_f4_without_a_grounded_subject_only_the_anchors_are_judged_and_nothing_is_created`
- [tests/test_notes_as_learner_text.py](../../../../../../../tests/test_notes_as_learner_text.py) — direct import
  - `test_a_note_is_read_on_the_ordinary_routes_with_the_decider`
  - `test_learner_note_is_a_readable_tier_2_kind_read_like_other_learner_text`
  - `test_reading_a_note_is_tier_2_only_and_keeps_its_words_like_any_learner_text`
  - `test_step0_a_legacy_checkpointed_note_reading_is_cleared_on_requeue_and_ignored_on_retry`
- [tests/test_reader_formative_texts.py](../../../../../../../tests/test_reader_formative_texts.py) — direct import
  - `test_reading_it_writes_only_gap_rows_and_names_the_observations_hypothesis`
  - `test_the_widened_kinds_reach_the_salience_firewall_unchanged`
- [tests/test_t6_followup_composition.py](../../../../../../../tests/test_t6_followup_composition.py) — direct import
  - `test_the_seed_unit_is_admitted_at_the_policy_budget`
- [tests/test_tier1_decider.py](../../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_needed_is_the_deciders_and_its_refusal_falls_back`
  - `test_the_gaps_report_skips_decider_failure_rows`
- [tests/test_workbench_text_gaps.py](../../../../../../../tests/test_workbench_text_gaps.py) — direct import
  - `test_each_boxs_where_this_goes_matches_where_its_text_goes`
  - `test_the_kind_is_readable_and_non_serving_and_the_switches_hold`
- [tests/text_gap_fakes.py](../../../../../../../tests/text_gap_fakes.py) — direct import

## Modification guidance

- Change contract policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/text_gaps/contract.py](../../../../../../../src/learnloop/diagnosis/text_gaps/contract.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
