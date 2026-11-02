---
title: "learnloop.teacher.brief"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/brief.py"
source_paths:
  - "src/learnloop/teacher/brief.py"
source_commit: "41a9038d4311ee89a9d90df0270b31c03e496bba"
source_commit_timestamp: "2026-11-02T09:44:47-05:00"
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
  - "learnloop.teacher.brief module"
  - "src/learnloop/teacher/brief.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.brief`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.brief` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: ``LessonBriefV1``: the lesson's opening context, built deterministically from the ledger (spec_teacher_v1 §8.1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/brief.py](../../../../../../src/learnloop/teacher/brief.py) |
| Source lines | 763 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `41a9038d4311ee89a9d90df0270b31c03e496bba` |
| Commit timestamp | `2026-11-02T09:44:47-05:00` |

## Public API

- `class LessonRefused(ValueError)` ([source](../../../../../../src/learnloop/teacher/brief.py), line 56) — A lesson that may not open (protected material, an unknown topic), with one plain line.
  - `__init__(self, code: str, message: str) -> None` (line 59; internal)
- `class SourceBook` ([source](../../../../../../src/learnloop/teacher/brief.py), line 65) — The passages delivered to the teacher, by alias (citation validation and reveals read it).
  - `available(self, alias: str) -> bool` (line 75; public)
  - `alias_for(self, extraction_id: str, span_id: str, text: str, *, section_ref: str | None=None) -> str` (line 78; public)
  - `as_dict(self) -> dict[str, Any]` (line 87; public)
  - `from_dict(cls, value: Mapping[str, Any] | None) -> 'SourceBook'` (line 91; public)
- `passage_teachable(library: Any, extraction_id: str, span_id: str) -> bool` ([source](../../../../../../src/learnloop/teacher/brief.py), line 96) — Whether a delivered passage may still reach the teacher NOW: its reading is in the section library (not left out), its span is not protected, and its section is not withheld (the same protection the brief and ``read_source`` apply when they first deliver it).
- `revoke_unteachable(library: Any, book: SourceBook) -> set[str]` ([source](../../../../../../src/learnloop/teacher/brief.py), line 110) — Recompute ``book.revoked`` against the library as it is now; returns the revoked aliases.
- `protection_state(vault: Any, repository: Any, brief: Mapping[str, Any] | None=None) -> dict[str, str] | None` ([source](../../../../../../src/learnloop/teacher/brief.py), line 142) — The vault's protection state as a lesson relies on it, or None when it cannot be read (fail closed).
- `resolve_goal(vault: Any, repository: Any, *, entry: str, learning_object_ids: Sequence[str]=(), selection: Mapping[str, Any] | None=None) -> tuple[list[str], dict[str, str], dict[str, Any] | None]` ([source](../../../../../../src/learnloop/teacher/brief.py), line 177) — The lesson's LOs, how each was resolved, and the Reader selection's section (if any).
- `prerequisite_nodes(vault: Any, goal: Sequence[str], depth: int) -> list[tuple[str, str, int]]` ([source](../../../../../../src/learnloop/teacher/brief.py), line 241) — ``(lo, "goal" | "prerequisite", depth)`` for the goal LOs and their closure to ``depth``.
- `downstream_learning_objects(vault: Any, learning_object_ids: Iterable[str]) -> list[str]` ([source](../../../../../../src/learnloop/teacher/brief.py), line 266) — Active LOs whose concept has one of these LOs' concepts as a prerequisite (transfer candidates).
- `lo_prediction(vault: Any, repository: Any, learning_object_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/brief.py), line 280) — The active predictor's predicted unassisted success on the LO, with its interval, in words.
- `ad_readiness(vault: Any, repository: Any, learning_object_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/brief.py), line 307) — Adaptive difficulty's readiness line for the LO when AD serves (its own read-only entry, its own guarded operation); None when AD is off, below its tag or denied (the brief says which).
- `recap_admissible(vault: Any, repository: Any, lesson_id: str, *, current: Any=_UNREAD) -> bool` ([source](../../../../../../src/learnloop/teacher/brief.py), line 477) — Whether an earlier lesson's recap may enter a brief or a ``read_history`` result NOW.
- `admitted_recap(vault: Any, repository: Any, lesson_id: str, recap: Any, *, current: Any=_UNREAD) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/brief.py), line 507) — ``{"recap": ...}`` when :func:`recap_admissible`, else the recap left out and said so.
- `c4_active(vault: Any) -> bool` ([source](../../../../../../src/learnloop/teacher/brief.py), line 617)
- `deliverable_for(vault: Any, repository: Any, learning_object_ids: Sequence[str]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/brief.py), line 621) — The nearest active deliverable whose resolution names one of the lesson's LOs, with its sentence, the resolution's phrase per LO and the path's primaries and alternates (C4, §8.2).
- `build_brief(vault: Any, repository: Any, *, learning_object_ids: Sequence[str], how: Mapping[str, str], goal_text: str, selection: Mapping[str, Any] | None, driver: str, lesson_id: str | None, constraints: Mapping[str, Any], notes_provider: Any=None) -> tuple[dict[str, Any], SourceBook]` ([source](../../../../../../src/learnloop/teacher/brief.py), line 669) — ``(LessonBriefV1, the delivered passages)``.

### Module constants

- `STEM_CHARS` ([src/learnloop/teacher/brief.py](../../../../../../src/learnloop/teacher/brief.py), line 51)
- `INTERVAL_Z` ([src/learnloop/teacher/brief.py](../../../../../../src/learnloop/teacher/brief.py), line 53)
- `PROTECTION_VERSION` ([src/learnloop/teacher/brief.py](../../../../../../src/learnloop/teacher/brief.py), line 120)
- `_COLD_TYPES` ([src/learnloop/teacher/brief.py](../../../../../../src/learnloop/teacher/brief.py), line 361)
- `RECAP_OMITTED` ([src/learnloop/teacher/brief.py](../../../../../../src/learnloop/teacher/brief.py), line 436)
- `_UNREAD` ([src/learnloop/teacher/brief.py](../../../../../../src/learnloop/teacher/brief.py), line 437)

### Explicit exports

`__all__` declares:

- `LessonRefused`
- `RECAP_OMITTED`
- `SourceBook`
- `ad_readiness`
- `admitted_recap`
- `build_brief`
- `c4_active`
- `deliverable_for`
- `downstream_learning_objects`
- `lo_prediction`
- `prerequisite_nodes`
- `protection_state`
- `recap_admissible`
- `resolve_goal`

## Internal implementation anchors

- `_brief_item_ids(repository: Any, brief: Mapping[str, Any] | None) -> list[str]` ([source](../../../../../../src/learnloop/teacher/brief.py), line 123) — The vault items a brief names: its probes, and the items of its history entries (an attempt's, a tutor question's), whose results ``read_history`` may deliver later.
- `_concept_los(vault: Any) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/teacher/brief.py), line 220)
- `_prerequisite_concepts(vault: Any) -> dict[str, set[str]]` ([source](../../../../../../src/learnloop/teacher/brief.py), line 229) — Concept -> its prerequisite concepts (LO declarations and ``prerequisite`` edges).
- `_retrievability(repository: Any, vault: Any, learning_object_id: str) -> float | None` ([source](../../../../../../src/learnloop/teacher/brief.py), line 328)
- `_misconceptions(repository: Any, learning_object_id: str) -> list[str]` ([source](../../../../../../src/learnloop/teacher/brief.py), line 340)
- `_attempt_rows(repository: Any, learning_object_ids: Sequence[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/brief.py), line 348)
- `_cold(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/teacher/brief.py), line 364)
- `_result_words(row: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/teacher/brief.py), line 368)
- `_history(vault: Any, repository: Any, learning_object_ids: Sequence[str], withheld: Any, hedges: Mapping[str, str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/brief.py), line 379)
- `_probe_headers(vault: Any, repository: Any, learning_object_id: str, withheld: Any, attempted: set[str], prediction: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/brief.py), line 418)
- `_lesson_exposure(repository: Any, lesson_id: str) -> tuple[dict[str, Any], SourceBook, set[str]]` ([source](../../../../../../src/learnloop/teacher/brief.py), line 440) — An earlier lesson's recorded protection, the passages it delivered (its brief's and every read's additions: everything its recap may quote or cite) and the vault items it was shown while they were not withheld (its brief's probes and tutor questions, its unprotected history, ``f…
- `_last_lessons(vault: Any, repository: Any, learning_object_ids: Sequence[str], exclude: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/brief.py), line 518)
- `_delayed_result(connection: Any, entry: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/brief.py), line 543)
- `_section_refs(vault: Any, library: Any, learning_object_ids: Sequence[str], selection: Mapping[str, Any] | None) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/teacher/brief.py), line 558)
- `_render_sources(library: Any, book: SourceBook, primaries: Sequence[tuple[str, str]], outline_only: Sequence[tuple[str, str]], budget_tokens: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/brief.py), line 570) — Whole sections (model-safe passages) under the budget, else the outline; ``outline_only`` sections (a deliverable's alternates) are listed by title.
- `_resolution_phrases(resolution: Any) -> dict[str, str]` ([source](../../../../../../src/learnloop/teacher/brief.py), line 656) — The resolution receipt's phrase per LO (C0b's ``learning_objects`` rows).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]] — imports `admitted_recap`, `passage_teachable`, `protection_state`; statically calls `admitted_recap`, `passage_teachable`, `protection_state`
- [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]] — imports `SourceBook`, `lo_prediction`; statically calls `lo_prediction`
- [[Reference/Modules/learnloop/teacher/delayed|learnloop.teacher.delayed]] — imports `downstream_learning_objects`, `lo_prediction`; statically calls `downstream_learning_objects`, `lo_prediction`
- [[Reference/Modules/learnloop/teacher/guards|learnloop.teacher.guards]] — imports `SourceBook`
- [[Reference/Modules/learnloop/teacher/notes|learnloop.teacher.notes]] — imports `STEM_CHARS`, `c4_active`; statically calls `c4_active`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `LessonRefused`, `SourceBook`, `build_brief`, `lo_prediction`, `protection_state`, `resolve_goal`, `revoke_unteachable`; statically calls `build_brief`, `lo_prediction`, `protection_state`, `resolve_goal`, `revoke_unteachable`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/readiness|learnloop.adaptive_difficulty.readiness]] — imports `card_fields`, `lo_readiness`; calls `card_fields`, `lo_readiness`
- [[Reference/Modules/learnloop/adf_numeric|learnloop.adf_numeric]] — imports `sigmoid`; calls `sigmoid`
- [[Reference/Modules/learnloop/attempts/grading_admission|learnloop.attempts.grading_admission]] — imports `estimated_prompt_tokens`; calls `estimated_prompt_tokens`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/lessons|learnloop.db.stores.lessons]] — imports `module`; calls `checks`, `lessons_on`, `receipt`, `turns`
- [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]] — imports `predicted_success`, `read_hedges`; calls `predicted_success`, `read_hedges`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `initial_mastery_state_for_learning_object`, `item_irt_params`; calls `initial_mastery_state_for_learning_object`, `item_irt_params`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `WITHHELD_EXAM`, `WITHHELD_RESERVED`, `attempt_protection`, `withheld_items`; calls `attempt_protection`, `withheld_items`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `module`; calls `nearest_deliverables`, `path_view`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `module`; calls `enabled`, `latest_resolution`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `lo_statuses`; calls `lo_statuses`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `CoverageError`, `Library`, `read_protection`; calls `Library`, `read_protection`
- [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]] — imports `BRIEF_VERSION`, `READ_ACTIONS`
- [[Reference/Modules/learnloop/teacher/doctrines|learnloop.teacher.doctrines]] — imports `doctrine_identity`; calls `doctrine_identity`
- [[Reference/Modules/learnloop/vault/lifecycle|learnloop.vault.lifecycle]] — imports `practice_item_serving_block`; calls `practice_item_serving_block`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]], [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]], [[Reference/Modules/learnloop/teacher/delayed|learnloop.teacher.delayed]], [[Reference/Modules/learnloop/teacher/guards|learnloop.teacher.guards]], [[Reference/Modules/learnloop/teacher/notes|learnloop.teacher.notes]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followups_batch5_recap_protection.py](../../../../../../tests/test_followups_batch5_recap_protection.py) — direct import
  - `test_a_lesson_with_no_recorded_protection_rechecks_its_passages`
  - `test_a_recap_quoting_a_passage_held_out_since_is_not_in_the_fresh_lesson_s_prompt`
  - `test_read_history_cannot_fetch_that_recap_either`
  - `test_unreadable_protection_drops_the_recap_only`

## Modification guidance

- Make changes here when the responsibility remains brief within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/brief.py](../../../../../../src/learnloop/teacher/brief.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
