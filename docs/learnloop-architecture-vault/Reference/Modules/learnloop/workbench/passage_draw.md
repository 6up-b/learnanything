---
title: "learnloop.workbench.passage_draw"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/workbench/passage_draw.py"
source_paths:
  - "src/learnloop/workbench/passage_draw.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.workbench"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.workbench.passage_draw module"
  - "src/learnloop/workbench/passage_draw.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-workbench"
---

# `learnloop.workbench.passage_draw`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.workbench.passage_draw` exists within [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] to own the behavior summarized by its module contract: Reader workbench RW2c: a logged choice where it costs nothing (spec_reader_workbench_v1 §5.10, G39).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/workbench/passage_draw.py](../../../../../../src/learnloop/workbench/passage_draw.py) |
| Source lines | 279 |
| Owning package | [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `new_seed() -> str` ([source](../../../../../../src/learnloop/workbench/passage_draw.py), line 46) — A fresh seed for one draw (logged; :func:`draw` reproduces from it).
- `option_id(passage: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/workbench/passage_draw.py), line 56)
- `option_record(passage: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/workbench/passage_draw.py), line 60) — What a row keeps of an option: its identity and label, never its text.
- `best_class(passages: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]` ([source](../../../../../../src/learnloop/workbench/passage_draw.py), line 76) — The passages of the best verdict present (worked examples: the route first), in the judge's order; passages without a verdict are one class.
- `class Draw` ([source](../../../../../../src/learnloop/workbench/passage_draw.py), line 88)
  - `drawn(self) -> dict[str, Any]` (line 96; public)
  - `columns(self) -> dict[str, Any]` (line 99; public) — The ``help_assists`` columns that log the draw.
- `draw(passages: Sequence[Mapping[str, Any]], *, seed: str) -> Draw | None` ([source](../../../../../../src/learnloop/workbench/passage_draw.py), line 114) — One uniform draw over the options, or None when fewer than two (then the first passage is shown as before, with nothing logged).
- `options_of(row: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/workbench/passage_draw.py), line 128)
- `next_option(options: Sequence[Mapping[str, Any]], current_id: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/workbench/passage_draw.py), line 137) — The option after ``current_id``, wrapping round; None with fewer than two.
- `alternatives_view(row: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/workbench/passage_draw.py), line 155) — "another passage" on a shown bridge or example: present only when its row logged a draw (or is a pick among one), so with the draw switched off a view is exactly what it was.
- `class NoAlternative(Exception)` ([source](../../../../../../src/learnloop/workbench/passage_draw.py), line 169) — The row has no other passage to show.
- `option_withheld(vault: Any, repository: Any, item: Any, option: Mapping[str, Any], *, workbench_session_id: str) -> str | None` ([source](../../../../../../src/learnloop/workbench/passage_draw.py), line 173) — Why a cached draw option may NOT be shown now, or None (fix round 2, 2).
- `another_passage(repository: Any, *, workbench_session_id: str, assist_id: str, line_for: Any, shown_at: str, withheld: Any | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/workbench/passage_draw.py), line 223) — Show the next option of a shown bridge or example (no search, no call): a new row, ``chooser = 'learner_pick'``, no propensity, counted by nothing.

### Module constants

- `POLICY_VERSION` ([src/learnloop/workbench/passage_draw.py](../../../../../../src/learnloop/workbench/passage_draw.py), line 38)
- `MAX_OPTIONS` ([src/learnloop/workbench/passage_draw.py](../../../../../../src/learnloop/workbench/passage_draw.py), line 41)
- `EXAMPLE_VERDICTS` ([src/learnloop/workbench/passage_draw.py](../../../../../../src/learnloop/workbench/passage_draw.py), line 43)

### Explicit exports

`__all__` declares:

- `Draw`
- `EXAMPLE_VERDICTS`
- `MAX_OPTIONS`
- `NoAlternative`
- `POLICY_VERSION`
- `alternatives_view`
- `another_passage`
- `best_class`
- `draw`
- `new_seed`
- `next_option`
- `option_id`
- `option_record`
- `option_withheld`
- `options_of`

## Internal implementation anchors

- `_rng(seed: str) -> random.Random` ([source](../../../../../../src/learnloop/workbench/passage_draw.py), line 52)
- `_placement(row: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/workbench/passage_draw.py), line 147)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/workbench/bridge|learnloop.workbench.bridge]] — imports `module`; statically calls `draw`, `new_seed`, `option_id`
- [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]] — imports `alternatives_view`; statically calls `alternatives_view`
- [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]] — imports `module`; statically calls `alternatives_view`, `best_class`, `draw`, `new_seed`, `option_id`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]] — imports `module`; statically calls `another_passage`, `option_withheld`, `options_of`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] — imports `module`; calls `assist`, `insert_assist`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/block_roles|learnloop.ingest.block_roles]] — imports `lead_role`; calls `lead_role`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `exam_withheld`, `item_exclusions`, `teaching_exclusions`; calls `exam_withheld`, `item_exclusions`, `teaching_exclusions`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `derive_policy`; calls `derive_policy`
- [[Reference/Modules/learnloop/tutor/context_delivery|learnloop.tutor.context_delivery]] — imports `BlockSource`; calls `BlockSource`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `span_leaks_expected`; calls `span_leaks_expected`
- [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]] — imports `caller_for_session`; calls `caller_for_session`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `random`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/workbench/bridge|learnloop.workbench.bridge]], [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]], [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]], [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_rw2c_fix_round2.py](../../../../../../tests/test_rw2c_fix_round2.py) — direct import
  - `test_fr2_2_an_option_that_is_now_the_items_own_passage_or_reproduces_its_answer_is_withheld`
- [tests/test_workbench_passage_draw.py](../../../../../../tests/test_workbench_passage_draw.py) — direct import
  - `test_a_worked_example_is_drawn_only_within_the_best_verdict_class`
  - `test_the_bridge_logs_its_draw_and_shows_the_drawn_passage`
  - `test_the_draw_is_uniform_logged_and_reproduces_from_its_seed`
- [tests/test_workbench_route_example.py](../../../../../../tests/test_workbench_route_example.py) — direct import
  - `test_review_f1_an_example_in_another_book_carries_that_books_identity`

## Modification guidance

- Make changes here when the responsibility remains passage draw within learnloop.workbench; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/workbench/passage_draw.py](../../../../../../src/learnloop/workbench/passage_draw.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
