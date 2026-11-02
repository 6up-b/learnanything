---
title: "learnloop.vault.lifecycle"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault/lifecycle.py"
source_paths:
  - "src/learnloop/vault/lifecycle.py"
source_commit: "beaea47c7cbfc3c34dfa2d418977b26cf4d8ce88"
source_commit_timestamp: "2026-11-01T18:59:57-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.vault"
layer: "infrastructure"
concepts:
  - "State and Persistence"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.vault.lifecycle module"
  - "src/learnloop/vault/lifecycle.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-vault"
---

# `learnloop.vault.lifecycle`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.vault.lifecycle` exists within [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] to own the behavior summarized by its module contract: Serving lifecycle of a practice item and its owning Learning Object.

The authoritative system-level explanation remains in [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault/lifecycle.py](../../../../../../src/learnloop/vault/lifecycle.py) |
| Source lines | 179 |
| Owning package | [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `beaea47c7cbfc3c34dfa2d418977b26cf4d8ce88` |
| Commit timestamp | `2026-11-01T18:59:57-05:00` |

## Public API

- `created_from_learner_text(learning_object: Any) -> bool` ([source](../../../../../../src/learnloop/vault/lifecycle.py), line 51)
- `learner_text_gap_creations(learning_objects: Iterable[Any]) -> frozenset[tuple[str, str]]` ([source](../../../../../../src/learnloop/vault/lifecycle.py), line 62) — (concept, learner text) of every LO the learner-text gap pipeline created.
- `learner_text_gap_edge_origin(edge: Any, creations: Collection[tuple[str, str]]=frozenset()) -> str | None` ([source](../../../../../../src/learnloop/vault/lifecycle.py), line 75) — ``match`` or ``creation`` for an edge the learner-text gap pipeline added; None for every other edge.
- `learner_text_gap_edge_in_effect(config: Any, edge: Any, creations: Collection[tuple[str, str]]=frozenset()) -> bool` ([source](../../../../../../src/learnloop/vault/lifecycle.py), line 96) — Is this relation edge part of the loaded vault (Codex review F10)?
- `adopted_by_reference_sweep(item: PracticeItem) -> bool` ([source](../../../../../../src/learnloop/vault/lifecycle.py), line 125) — True for a card the reader's reference-question sweep adopted.
- `learning_object_serving_block(vault: LoadedVault, learning_object_id: str | None) -> str | None` ([source](../../../../../../src/learnloop/vault/lifecycle.py), line 132) — Why the LO's items may not be served now, or ``None`` when they may.
- `learning_object_servable(vault: LoadedVault, learning_object_id: str | None) -> bool` ([source](../../../../../../src/learnloop/vault/lifecycle.py), line 149)
- `practice_item_serving_block(vault: LoadedVault, item: PracticeItem) -> str | None` ([source](../../../../../../src/learnloop/vault/lifecycle.py), line 153) — Why this item may not be served now, or ``None`` when it may.
- `minted_for_lesson(item: PracticeItem) -> bool` ([source](../../../../../../src/learnloop/vault/lifecycle.py), line 171) — True for a lesson check's held item (teacher TE1).
- `practice_item_servable(vault: LoadedVault, item: PracticeItem) -> bool` ([source](../../../../../../src/learnloop/vault/lifecycle.py), line 178)

### Module constants

- `SERVABLE_LEARNING_OBJECT_STATUS` ([src/learnloop/vault/lifecycle.py](../../../../../../src/learnloop/vault/lifecycle.py), line 29)
- `REFERENCE_ADOPTION_MECHANISM` ([src/learnloop/vault/lifecycle.py](../../../../../../src/learnloop/vault/lifecycle.py), line 35)
- `REFERENCE_ADOPTION_DISABLED` ([src/learnloop/vault/lifecycle.py](../../../../../../src/learnloop/vault/lifecycle.py), line 36)
- `LEARNER_TEXT_GAP_MECHANISM` ([src/learnloop/vault/lifecycle.py](../../../../../../src/learnloop/vault/lifecycle.py), line 41)
- `LEARNER_TEXT_GAP_DISABLED` ([src/learnloop/vault/lifecycle.py](../../../../../../src/learnloop/vault/lifecycle.py), line 42)
- `TEACHER_LESSON_MECHANISM` ([src/learnloop/vault/lifecycle.py](../../../../../../src/learnloop/vault/lifecycle.py), line 47)
- `LESSON_HOLD` ([src/learnloop/vault/lifecycle.py](../../../../../../src/learnloop/vault/lifecycle.py), line 48)

## Internal implementation anchors

- `_learner_text_gap_creations_on(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/vault/lifecycle.py), line 57)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/ad_slot|learnloop.daily_plan.ad_slot]] — imports `practice_item_serving_block`; statically calls `practice_item_serving_block`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `practice_item_servable`; statically calls `practice_item_servable`
- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `learning_object_servable`; statically calls `learning_object_servable`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `learning_object_servable`; statically calls `learning_object_servable`
- [[Reference/Modules/learnloop/diagnosis/quick_check|learnloop.diagnosis.quick_check]] — imports `practice_item_servable`; statically calls `practice_item_servable`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/contract|learnloop.diagnosis.text_gaps.contract]] — imports `LEARNER_TEXT_GAP_MECHANISM`
- [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]] — imports `practice_item_servable`; statically calls `practice_item_servable`
- [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]] — imports `created_from_learner_text`; statically calls `created_from_learner_text`
- [[Reference/Modules/learnloop/practice_index/admission|learnloop.practice_index.admission]] — imports `REFERENCE_ADOPTION_DISABLED`, `learning_object_servable`, `practice_item_serving_block`; statically calls `learning_object_servable`, `practice_item_serving_block`
- [[Reference/Modules/learnloop/reader/reader_authoring|learnloop.reader.reader_authoring]] — imports `REFERENCE_ADOPTION_MECHANISM`, `learning_object_servable`; statically calls `learning_object_servable`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `practice_item_servable`; statically calls `practice_item_servable`
- [[Reference/Modules/learnloop/scheduling/serving_exclusions|learnloop.scheduling.serving_exclusions]] — imports `practice_item_servable`; statically calls `practice_item_servable`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `practice_item_serving_block`; statically calls `practice_item_serving_block`
- [[Reference/Modules/learnloop/teacher/delayed|learnloop.teacher.delayed]] — imports `practice_item_serving_block`; statically calls `practice_item_serving_block`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `learner_text_gap_creations`, `learner_text_gap_edge_in_effect`; statically calls `learner_text_gap_creations`, `learner_text_gap_edge_in_effect`
- [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] — imports `LEARNER_TEXT_GAP_DISABLED`, `REFERENCE_ADOPTION_DISABLED`, `learning_object_serving_block`, `practice_item_serving_block`; statically calls `learning_object_serving_block`, `practice_item_serving_block`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/ad_slot|learnloop.daily_plan.ad_slot]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]], [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]], [[Reference/Modules/learnloop/diagnosis/quick_check|learnloop.diagnosis.quick_check]] and 11 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_learner_text_gaps.py](../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_switching_creation_off_stops_serving_created_los`
- [tests/test_quick_check.py](../../../../../../tests/test_quick_check.py) — direct import
  - `test_quick_check_skips_what_find_practice_skips_outside_the_schedulers_timing`
- [tests/test_teacher_te1_lesson.py](../../../../../../tests/test_teacher_te1_lesson.py) — direct import
  - `test_the_minted_check_item_is_held_to_its_lesson`

## Modification guidance

- Make changes here when the responsibility remains lifecycle within learnloop.vault; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/vault/lifecycle.py](../../../../../../src/learnloop/vault/lifecycle.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
