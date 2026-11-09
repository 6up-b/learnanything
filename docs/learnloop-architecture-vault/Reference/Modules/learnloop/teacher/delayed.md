---
title: "learnloop.teacher.delayed"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/delayed.py"
source_paths:
  - "src/learnloop/teacher/delayed.py"
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
  - "learnloop.teacher.delayed module"
  - "src/learnloop/teacher/delayed.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.delayed`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.delayed` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: Delayed cold and transfer checks (spec_teacher_v1 §13): code picks the items and the dates, never the model.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/delayed.py](../../../../../../src/learnloop/teacher/delayed.py) |
| Source lines | 263 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `question_overlap(shown: str, question: str) -> float` ([source](../../../../../../src/learnloop/teacher/delayed.py), line 66) — The share of a question's word pairs (numbers kept: a matrix is part of the question) that the shown text contains, in 0..1: 1 for a question reproduced as it stands, near 0 for teaching that only shares its topic's vocabulary.
- `shown_vault_items(vault: Any, texts: Iterable[str]) -> list[str]` ([source](../../../../../../src/learnloop/teacher/delayed.py), line 77) — Vault items whose question the lesson's displayed text reproduces (a vault question reused as a check, or quoted in teaching), at the house exposure threshold (the auto-prime rule), in id order.
- `taught_facets(vault: Any, learning_object_ids: Iterable[str]) -> set[str]` ([source](../../../../../../src/learnloop/teacher/delayed.py), line 96)
- `measures_facet(vault: Any, item: Any, facets: set[str]) -> bool` ([source](../../../../../../src/learnloop/teacher/delayed.py), line 107) — Whether a criterion of the item's rubric measures one of ``facets`` (its targets, else the item's declared facets: KM §9.3's "a criterion that visibly exercises it").
- `presentation(item: Any) -> str | None` ([source](../../../../../../src/learnloop/teacher/delayed.py), line 128)
- `pick(vault: Any, repository: Any, items: Sequence[Any], *, seed_key: str='') -> Any | None` ([source](../../../../../../src/learnloop/teacher/delayed.py), line 134) — The candidate pitched nearest the band's middle (the house prior); module docstring.
- `retention_seed_key(lesson_id: str, learning_object_id: str) -> str` ([source](../../../../../../src/learnloop/teacher/delayed.py), line 151) — The retention check's draw: its commit and the lesson forecast about it share it (§12.2).
- `commit_checks(vault: Any, repository: Any, *, lesson_id: str, landed: Sequence[Mapping[str, Any]], goal_learning_object_ids: Sequence[str], lesson_items_by_lo: Mapping[str, Sequence[str]], shown_items: Iterable[str], taught_learning_objects: Sequence[str]=(), clock: Clock | None=None) -> tuple[list[dict[str, Any]], list[str]]` ([source](../../../../../../src/learnloop/teacher/delayed.py), line 157) — Commit one retention check per landed node with an LO and one transfer check; returns ``(delayed_checks, warnings)`` for the receipt.

### Module constants

- `PURPOSES` ([src/learnloop/teacher/delayed.py](../../../../../../src/learnloop/teacher/delayed.py), line 56)
- `DEPTH_PRESET` ([src/learnloop/teacher/delayed.py](../../../../../../src/learnloop/teacher/delayed.py), line 57)
- `VIA` ([src/learnloop/teacher/delayed.py](../../../../../../src/learnloop/teacher/delayed.py), line 58)

### Explicit exports

`__all__` declares:

- `PICK_VERSION`
- `PURPOSES`
- `candidates`
- `commit_checks`
- `due_days`
- `lineage`
- `measures_facet`
- `pick`
- `pick_with_receipt`
- `presentation`
- `retention_seed_key`
- `shown_vault_items`
- `taught_facets`

## Internal implementation anchors

- `_bigrams(text: str) -> set[tuple[str, str]]` ([source](../../../../../../src/learnloop/teacher/delayed.py), line 61)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]] — imports `module`; statically calls `_attempted`, `_revealed`, `candidates`, `due_days`, `lineage`, `pick`, `retention_seed_key`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `module`; statically calls `commit_checks`, `shown_vault_items`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `resolved_rubric`; calls `resolved_rubric`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `create_commitment`
- [[Reference/Modules/learnloop/data_capture/gates|learnloop.data_capture.gates]] — imports `serving_on`; calls `serving_on`
- [[Reference/Modules/learnloop/delayed_checks|learnloop.delayed_checks]] — imports `PICK_VERSION`, `attempted_items`, `candidates`, `due_days`, `lineage`, `pick_with_receipt`, `revealed_items`; calls `attempted_items`, `candidates`, `due_days`, `lineage`, `pick_with_receipt`, `revealed_items`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `withheld_items`; calls `withheld_items`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `AUTO_PRIME_REVEAL_THRESHOLD`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `downstream_learning_objects`, `lo_prediction`; calls `downstream_learning_objects`, `lo_prediction`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `learning_object_facet_union`; calls `learning_object_facet_union`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]], [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_data_capture_a6_delayed_pick.py](../../../../../../tests/test_data_capture_a6_delayed_pick.py) — direct import
  - `test_a_near_tie_is_no_tie`
  - `test_an_exact_tie_is_a_logged_uniform_draw_with_probability_one_over_n`
  - `test_below_the_tag_or_switched_off_the_smallest_id_wins_as_before`
  - `test_commit_checks_carry_the_delayed_check_receipt_fields`
  - `test_the_lessons_forecast_reference_is_the_item_the_check_would_commit`
  - `test_the_pick_is_the_item_nearest_the_band_not_the_smallest_id`
- [tests/test_teacher_te1_review_fixes.py](../../../../../../tests/test_teacher_te1_review_fixes.py) — direct import
  - `test_f8_a_downstream_edge_alone_is_not_transfer`
  - `test_f8_a_downstream_item_whose_rubric_measures_a_taught_facet_is_transfer`

## Modification guidance

- Make changes here when the responsibility remains delayed within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/delayed.py](../../../../../../src/learnloop/teacher/delayed.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
