---
title: "learnloop.goals.exam_seeding"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/goals/exam_seeding.py"
source_paths:
  - "src/learnloop/goals/exam_seeding.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.goals"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.goals.exam_seeding module"
  - "src/learnloop/goals/exam_seeding.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-goals"
---

# `learnloop.goals.exam_seeding`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.goals.exam_seeding` exists within [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] to own the behavior summarized by its module contract: Exam seeding: import a past practice exam's per-question outcomes.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/goals/exam_seeding.py](../../../../../../src/learnloop/goals/exam_seeding.py) |
| Source lines | 467 |
| Owning package | [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ExamSeedingError(ValueError)` ([source](../../../../../../src/learnloop/goals/exam_seeding.py), line 74)
- `exam_ingest_instructions(extra_instructions: str | None=None) -> str` ([source](../../../../../../src/learnloop/goals/exam_seeding.py), line 78) — Canonical-ingestor instructions for ingesting a past practice exam.
- `class ExamOutcome` ([source](../../../../../../src/learnloop/goals/exam_seeding.py), line 106)
- `class ExamOutcomesFile` ([source](../../../../../../src/learnloop/goals/exam_seeding.py), line 114)
- `class ExamSeedEntry` ([source](../../../../../../src/learnloop/goals/exam_seeding.py), line 120)
  - `as_dict(self) -> dict[str, Any]` (line 131; public)
- `class ExamSeedingResult` ([source](../../../../../../src/learnloop/goals/exam_seeding.py), line 146)
  - `as_dict(self) -> dict[str, Any]` (line 156; public)
- `parse_exam_outcomes(payload: Mapping[str, Any], *, exam_date_override: str | None=None) -> ExamOutcomesFile` ([source](../../../../../../src/learnloop/goals/exam_seeding.py), line 169) — Parse an outcomes file payload.
- `exam_question_from_tags(item: PracticeItem) -> str | None` ([source](../../../../../../src/learnloop/goals/exam_seeding.py), line 244)
- `find_exam_items(vault: LoadedVault, *, subject: str | None=None) -> dict[str, PracticeItem]` ([source](../../../../../../src/learnloop/goals/exam_seeding.py), line 253) — Map exam question number -> practice item (tagged ``exam_q:<n>``).
- `seed_exam_attempts(vault: LoadedVault, repository: Repository, *, outcomes: ExamOutcomesFile, subject: str | None=None, dry_run: bool=False, clock: Clock | None=None) -> ExamSeedingResult` ([source](../../../../../../src/learnloop/goals/exam_seeding.py), line 290) — Seed backdated ``exam_evidence`` attempts from per-question outcomes.

### Module constants

- `EXAM_ATTEMPT_TYPE` ([src/learnloop/goals/exam_seeding.py](../../../../../../src/learnloop/goals/exam_seeding.py), line 65)
- `EXAM_QUESTION_TAG` ([src/learnloop/goals/exam_seeding.py](../../../../../../src/learnloop/goals/exam_seeding.py), line 66)
- `EXAM_QUESTION_TAG_PREFIX` ([src/learnloop/goals/exam_seeding.py](../../../../../../src/learnloop/goals/exam_seeding.py), line 67)
- `_EXAM_SEED_HOUR_UTC` ([src/learnloop/goals/exam_seeding.py](../../../../../../src/learnloop/goals/exam_seeding.py), line 71)

## Internal implementation anchors

- `_validated_score(question: str, value: Any) -> float` ([source](../../../../../../src/learnloop/goals/exam_seeding.py), line 234)
- `_question_sort_key(question: str) -> tuple[int, float | str, str]` ([source](../../../../../../src/learnloop/goals/exam_seeding.py), line 273)
- `_has_exam_attempt_on_date(repository: Repository, practice_item_id: str, exam_date: date) -> bool` ([source](../../../../../../src/learnloop/goals/exam_seeding.py), line 280)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `ExamSeedingError`, `exam_ingest_instructions`, `parse_exam_outcomes`, `seed_exam_attempts`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `exam_ingest_instructions`; statically calls `exam_ingest_instructions`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `ApplyAttemptInput`, `AttemptDraft`, `ResolvedGrade`, `apply_attempt`, `calculate_rubric_score`; calls `ApplyAttemptInput`, `AttemptDraft`, `ResolvedGrade`, `apply_attempt`, `calculate_rubric_score`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `resolved_rubric`; calls `resolved_rubric`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `FrozenClock`, `utc_now_iso`; calls `FrozenClock`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `RebuildResult`, `rebuild_derived_state`; calls `rebuild_derived_state`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/exam_seeding_helpers.py](../../../../../../tests/exam_seeding_helpers.py) — direct import
- [tests/ro1_availability_reads_helpers.py](../../../../../../tests/ro1_availability_reads_helpers.py) — direct import
- [tests/test_exam_seeding.py](../../../../../../tests/test_exam_seeding.py) — direct import
  - `test_dry_run_writes_nothing`
  - `test_exam_date_required_when_absent_everywhere`
  - `test_exam_item_without_outcome_warns_and_skips`
  - `test_ingest_exam_instructions_reach_context_and_tags_apply`
  - `test_migration_018_allows_exam_evidence_on_existing_db`
  - `test_parse_accepts_flat_mapping_and_date_override`
  - `test_rebuild_after_seeding_is_stable`
  - `test_seed_creates_backdated_discounted_attempts`
  - `test_seed_rerun_is_idempotent`
  - `test_seeded_exam_interleaves_before_later_live_attempt`
  - `test_subject_scoping_excludes_other_subjects`
  - `test_unmatched_outcome_key_errors`
- [tests/test_ro1_availability.py](../../../../../../tests/test_ro1_availability.py) — direct import
  - `test_the_weeks_activity_counts_an_import_inside_its_week_once_it_is_known`
- [tests/test_ro1_projection.py](../../../../../../tests/test_ro1_projection.py) — direct import
  - `test_availability_moves_no_due_date_or_mastery`
- [tests/test_serve_eligibility.py](../../../../../../tests/test_serve_eligibility.py) — direct import
  - `test_q33_an_exam_seeded_before_a_later_reveal_is_not_primed`
- [tests/test_serve_eligibility_review.py](../../../../../../tests/test_serve_eligibility_review.py) — direct import
  - `test_f4_q33s_bounded_window_is_the_successors`

## Modification guidance

- Change exam seeding policy here when goals owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/goals/exam_seeding.py](../../../../../../src/learnloop/goals/exam_seeding.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
