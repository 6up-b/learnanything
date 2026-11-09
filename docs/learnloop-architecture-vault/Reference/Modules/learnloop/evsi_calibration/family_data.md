---
title: "learnloop.evsi_calibration.family_data"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/evsi_calibration/family_data.py"
source_paths:
  - "src/learnloop/evsi_calibration/family_data.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.evsi_calibration"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.evsi_calibration.family_data module"
  - "src/learnloop/evsi_calibration/family_data.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-evsi-calibration"
---

# `learnloop.evsi_calibration.family_data`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.evsi_calibration.family_data` exists within [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] to own the behavior summarized by its module contract: Eedi 2020 answers arranged for the simulator families (stage ``evsi-multisim``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/evsi_calibration/family_data.py](../../../../../../src/learnloop/evsi_calibration/family_data.py) |
| Source lines | 289 |
| Owning package | [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `is_held_out(users: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/evsi_calibration/family_data.py), line 42)
- `is_fit(users: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/evsi_calibration/family_data.py), line 46)
- `class TripleData` ([source](../../../../../../src/learnloop/evsi_calibration/family_data.py), line 51) — One misconception triple's answers (odd ``UserId``s only).
  - `split(self, held_out: bool) -> 'TripleData'` (line 63; public)
  - `n(self) -> int` (line 69; public)
  - `categories(self) -> np.ndarray` (line 72; public) — (n, 3) answer categories: CORRECT, DESIGNATED or OTHER.
  - `role_options(self) -> np.ndarray` (line 82; public) — (n, 3) answers in role space: 0 correct, 1 designated, 2/3 the other two distractors in option-letter order.
  - `time_order(self) -> tuple[np.ndarray, np.ndarray]` (line 95; public) — Per student, the items in answer order and the two gap types.
- `item_roles(correct: int, designated: int) -> dict[int, int]` ([source](../../../../../../src/learnloop/evsi_calibration/family_data.py), line 112) — Option (1..4) -> role: 0 correct, 1 designated, 2/3 other in letter order.
- `class SubjectData` ([source](../../../../../../src/learnloop/evsi_calibration/family_data.py), line 123) — A subject's triple items as one test (fit split, missing allowed).
  - `items(self) -> int` (line 137; public)
  - `attributes(self) -> int` (line 141; public)
- `build_triple_data(responses: NeuripsResponses, triples: Sequence[TripleFit]) -> list[TripleData]` ([source](../../../../../../src/learnloop/evsi_calibration/family_data.py), line 170) — The answers of every triple's three questions, odd users only.
- `build_subject_data(responses: NeuripsResponses, triples: Sequence[TripleData], *, min_answered: int=2) -> list[SubjectData]` ([source](../../../../../../src/learnloop/evsi_calibration/family_data.py), line 213) — Per subject, its triples' items as one test over the fit split.
- `category_counts(table: np.ndarray) -> Mapping[tuple[int, int, int], int]` ([source](../../../../../../src/learnloop/evsi_calibration/family_data.py), line 267) — (n, 3) categories -> {(c1, c2, c3): count} for the latent class EM.

### Module constants

- `SESSION_GAP_MINUTES` ([src/learnloop/evsi_calibration/family_data.py](../../../../../../src/learnloop/evsi_calibration/family_data.py), line 36)

### Explicit exports

`__all__` declares:

- `CORRECT`
- `DESIGNATED`
- `OTHER`
- `GAP_LATER`
- `GAP_SAME_SESSION`
- `SESSION_GAP_MINUTES`
- `SubjectData`
- `TripleData`
- `build_subject_data`
- `build_triple_data`
- `category_counts`
- `is_fit`
- `is_held_out`
- `item_roles`

## Internal implementation anchors

- `_first_answers(responses: NeuripsResponses, questions: Sequence[int]) -> dict[int, tuple[np.ndarray, np.ndarray, np.ndarray]]` ([source](../../../../../../src/learnloop/evsi_calibration/family_data.py), line 145) — question -> (users sorted, option, minute) over odd users, first answer each.
- `_correct_options(responses: NeuripsResponses, questions: Sequence[int]) -> dict[int, int]` ([source](../../../../../../src/learnloop/evsi_calibration/family_data.py), line 204)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/evsi|learnloop.cli.evsi]] — imports `build_subject_data`, `build_triple_data`; statically calls `build_subject_data`, `build_triple_data`
- [[Reference/Modules/learnloop/evsi_calibration/family_fit|learnloop.evsi_calibration.family_fit]] — imports `GAP_LATER`, `GAP_SAME_SESSION`, `SubjectData`, `TripleData`, `category_counts`, `item_roles`; statically calls `category_counts`, `item_roles`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/evsi_calibration/eedi|learnloop.evsi_calibration.eedi]] — imports `NeuripsResponses`
- [[Reference/Modules/learnloop/evsi_calibration/response_fit|learnloop.evsi_calibration.response_fit]] — imports `CORRECT`, `DESIGNATED`, `OTHER`, `TripleFit`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/evsi|learnloop.cli.evsi]], [[Reference/Modules/learnloop/evsi_calibration/family_fit|learnloop.evsi_calibration.family_fit]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_evsi_multisim.py](../../../../../../tests/test_evsi_multisim.py) — direct import
  - `test_the_learning_family_recovers_a_planted_within_session_transition`
  - `test_the_splits_are_disjoint_and_the_roles_and_order_are_read_from_the_answers`

## Modification guidance

- Make changes here when the responsibility remains family data within learnloop.evsi_calibration; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/evsi_calibration/family_data.py](../../../../../../src/learnloop/evsi_calibration/family_data.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
