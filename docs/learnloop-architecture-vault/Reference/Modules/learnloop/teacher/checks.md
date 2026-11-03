---
title: "learnloop.teacher.checks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/checks.py"
source_paths:
  - "src/learnloop/teacher/checks.py"
source_commit: "a27561ff43fab9cfe5e6aae8236eaa139a6f742f"
source_commit_timestamp: "2026-11-01T22:10:57-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.teacher"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.teacher.checks module"
  - "src/learnloop/teacher/checks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.checks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.checks` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: Lesson checks (spec_teacher_v1 §12, §12.1, §12.2): minted, held, graded blind, entered at a learned mass.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/checks.py](../../../../../../src/learnloop/teacher/checks.py) |
| Source lines | 317 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a27561ff43fab9cfe5e6aae8236eaa139a6f742f` |
| Commit timestamp | `2026-11-01T22:10:57-05:00` |

## Public API

- `class CheckError(ValueError)` ([source](../../../../../../src/learnloop/teacher/checks.py), line 45)
  - `__init__(self, code: str, message: str) -> None` (line 46; internal)
- `check_item_id(lesson_id: str, check_ref: str) -> str` ([source](../../../../../../src/learnloop/teacher/checks.py), line 51)
- `render_prompt(check: CheckV1) -> str` ([source](../../../../../../src/learnloop/teacher/checks.py), line 55) — The item's prompt: the question, and its options for a choices check.
- `mint_check_item(root: Path, *, lesson_id: str, check_ref: str, check: CheckV1, learning_object_id: str, book: SourceBook, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/teacher/checks.py), line 64) — Write the check's held item (vault YAML) and return its id.
- `lesson_item(item: Any) -> bool` ([source](../../../../../../src/learnloop/teacher/checks.py), line 105)
- `cold_reference(vault: Any, repository: Any, learning_object_id: str, *, lesson_id: str, exclude: Sequence[str], lesson_item_ids: Sequence[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/checks.py), line 113) — The committed cold item a node's retention forecast is about, as of now (§12.2; review F5): the item the delayed retention check would commit (``teacher.delayed``'s candidate rule and picker, excluding the lesson's own and shown items and their lineage), its IRT parameters (the…
- `check_mass(vault: Any, repository: Any, *, learning_object_id: str, tap: int | None, hedge: str | None, correctness: float, item: Any, as_of: str, p_teacher_retained: float | None, family: str, reference: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/checks.py), line 135) — The mass this check enters mastery at, with every input (``weight_inputs``).
- `grade_answer(vault: Any, repository: Any, client: Any, *, item: Any, attempt_id: str, answer: str, runtime: Any=None, clock: Clock | None=None) -> tuple[Any, str]` ([source](../../../../../../src/learnloop/teacher/checks.py), line 197) — The blind grader's validated grade of ``answer`` (the answer only), as a ResolvedGrade, and its run id.
- `record_answered_check(vault: Any, repository: Any, *, lesson_id: str, node_id: str, check_ref: str, item: Any, attempt_id: str, answer: str, grade: Any, grading_run_id: str, grading_source: str, tap: int | None, mass: Mapping[str, Any], created_at: str, forecast_correct_key: str | None, forecast_retained_key: str | None, clock: Clock | None=None) -> Any` ([source](../../../../../../src/learnloop/teacher/checks.py), line 259) — One transaction: the ``lesson_checks`` row (the mass the attempt step reads), then the attempt.
- `withdraw_check(repository: Any, *, lesson_id: str, node_id: str, check_ref: str, item: Any, overlap: float, created_at: str) -> str` ([source](../../../../../../src/learnloop/teacher/checks.py), line 293)

### Module constants

- `LESSON_MECHANISM` ([src/learnloop/teacher/checks.py](../../../../../../src/learnloop/teacher/checks.py), line 39)
- `CHECK_ATTEMPT_TYPE` ([src/learnloop/teacher/checks.py](../../../../../../src/learnloop/teacher/checks.py), line 40)
- `ENTRY_SURFACE` ([src/learnloop/teacher/checks.py](../../../../../../src/learnloop/teacher/checks.py), line 41)
- `EVIDENCE_ORIGIN` ([src/learnloop/teacher/checks.py](../../../../../../src/learnloop/teacher/checks.py), line 42)

### Explicit exports

`__all__` declares:

- `CHECK_ATTEMPT_TYPE`
- `CheckError`
- `LESSON_MECHANISM`
- `check_item_id`
- `check_mass`
- `grade_answer`
- `lesson_item`
- `mint_check_item`
- `record_answered_check`
- `render_prompt`
- `withdraw_check`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `module`; statically calls `check_mass`, `cold_reference`, `grade_answer`, `lesson_item`, `mint_check_item`, `record_answered_check`, `withdraw_check`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/runs|learnloop.ai.runs]] — imports `finish_agent_run`; calls `finish_agent_run`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `ApplyAttemptInput`, `AttemptDraft`, `AttemptValidationError`, `GradeAttribution`, `ResolvedGrade`, `agent_run_provider_fields`, `apply_attempt`; calls `ApplyAttemptInput`, `AttemptDraft`, `AttemptValidationError`, `GradeAttribution`, `ResolvedGrade`, `agent_run_provider_fields`, `apply_attempt`
- [[Reference/Modules/learnloop/attempts/evidence|learnloop.attempts.evidence]] — imports `attempt_evidence_mass`; calls `attempt_evidence_mass`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `GradingValidationError`, `build_grading_context`, `request_vault_grading_proposal`, `validate_codex_grading_proposal`, `vault_grading_calibration_identity`, `vault_grading_run_identity`; calls `build_grading_context`, `request_vault_grading_proposal`, `validate_codex_grading_proposal`, `vault_grading_calibration_identity`, `vault_grading_run_identity`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/lessons|learnloop.db.stores.lessons]] — imports `module`; calls `insert_check`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `BLOCK_SPAN_V1`, `format_block_span`; calls `format_block_span`
- [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]] — imports `module`; calls `CheckSensitivity`, `confidence_term`, `pool_implied_mass`, `posterior_after`, `predicted_success`, `prediction_term`, `replay_state`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `initial_mastery_state_for_learning_object`, `item_irt_params`; calls `initial_mastery_state_for_learning_object`, `item_irt_params`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `withheld_items`; calls `withheld_items`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `SourceBook`, `lo_prediction`; calls `lo_prediction`
- [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]] — imports `CheckV1`
- [[Reference/Modules/learnloop/teacher/delayed|learnloop.teacher.delayed]] — imports `module`; calls `_attempted`, `_revealed`, `candidates`, `due_days`, `lineage`, `pick`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_practice_item`; calls `upsert_practice_item`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/teacher_fakes.py](../../../../../../tests/teacher_fakes.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_figures_prefetch.py](../../../../../../tests/test_figures_prefetch.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch5_lesson.py](../../../../../../tests/test_followups_batch5_lesson.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch5_recap_dependencies.py](../../../../../../tests/test_followups_batch5_recap_dependencies.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch5_recap_protection.py](../../../../../../tests/test_followups_batch5_recap_protection.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch6_review_fixes.py](../../../../../../tests/test_followups_batch6_review_fixes.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch6_router_report.py](../../../../../../tests/test_followups_batch6_router_report.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch7_prefetch_capped_resume.py](../../../../../../tests/test_followups_batch7_prefetch_capped_resume.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_nov2_figure_provenance.py](../../../../../../tests/test_followups_nov2_figure_provenance.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_teacher_te1_curriculum_c4.py](../../../../../../tests/test_teacher_te1_curriculum_c4.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]

## Modification guidance

- Make changes here when the responsibility remains checks within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/checks.py](../../../../../../src/learnloop/teacher/checks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
