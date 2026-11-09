---
title: "learnloop.instructional.discriminating"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/instructional/discriminating.py"
source_paths:
  - "src/learnloop/instructional/discriminating.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.instructional"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.instructional.discriminating module"
  - "src/learnloop/instructional/discriminating.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-instructional"
---

# `learnloop.instructional.discriminating`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.instructional.discriminating` exists within [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] to own the behavior summarized by its module contract: The valuer ``find_practice`` is given for the value intents (spec §8.3; S2a).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/instructional/discriminating.py](../../../../../../src/learnloop/instructional/discriminating.py) |
| Source lines | 230 |
| Owning package | [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `make_valuer(*, estimator: Callable[..., Any] | None=None, screen_client: Any | None=None, judge_client: Any | None=None, channel_resolver: Callable[..., Any] | None=None) -> Callable[..., dict[str, Any]]` ([source](../../../../../../src/learnloop/instructional/discriminating.py), line 43) — A valuer for ``find_practice(valuer=...)``.
- `value_request(vault: LoadedVault, repository: Repository, constraints: Any, *, items: Sequence[str], exercises: Sequence[Mapping[str, Any]], caller_kind: str='learner', system_initiated: bool=False, estimator: Callable[..., Any] | None=None, screen_client: Any | None=None, judge_client: Any | None=None, channel_resolver: Callable[..., Any] | None=None, pending_decision: Mapping[str, Any] | None=None, familiarity: bool=False, eligibility: Callable[..., dict[str, Any]] | None=None, already_chosen: Sequence[str]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/discriminating.py), line 63) — One request's valuation receipt.
- `presentation_order(receipt: Mapping[str, Any], eligibility: Mapping[str, Mapping[str, Any]]) -> list[str]` ([source](../../../../../../src/learnloop/instructional/discriminating.py), line 204) — Checks that clear the stop (check order), then each problem's valued group in value order under the reading-exposure dominance rule (§5.4), then the bounded and the unvalued.

### Module constants

- `TRANSLATION` ([src/learnloop/instructional/discriminating.py](../../../../../../src/learnloop/instructional/discriminating.py), line 34)

### Explicit exports

`__all__` declares:

- `TRANSLATION`
- `make_valuer`
- `presentation_order`
- `value_request`

## Internal implementation anchors

- `_discount_familiar(vault: LoadedVault, repository: Repository, problem: Any, entry: Any, cache: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/instructional/discriminating.py), line 171) — Compose the item's attempt-familiarity discount into its members (G35).
- `_key_statuses(vault: LoadedVault, repository: Repository, item_ids: Sequence[str]) -> dict[str, str]` ([source](../../../../../../src/learnloop/instructional/discriminating.py), line 193) — Each imported item's effective key status for its CURRENT content (§7.3a).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `module`; statically calls `value_request`
- [[Reference/Modules/learnloop/instructional/wiring|learnloop.instructional.wiring]] — imports `make_valuer`; statically calls `make_valuer`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `VERIFIED_STATUSES`, `effective_key_status`, `exercise_import_ids`; calls `effective_key_status`, `exercise_import_ids`
- [[Reference/Modules/learnloop/instructional/exposure|learnloop.instructional.exposure]] — imports `apply_dominance`, `independent_check_eligibility`; calls `apply_dominance`, `independent_check_eligibility`
- [[Reference/Modules/learnloop/instructional/screen|learnloop.instructional.screen]] — imports `screen_exercises`; calls `screen_exercises`
- [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]] — imports `discount_members`, `exercise_input`, `item_input`, `open_hypotheses`, `value_candidates`; calls `discount_members`, `exercise_input`, `item_input`, `open_hypotheses`, `value_candidates`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `familiarity_discount`; calls `familiarity_discount`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]], [[Reference/Modules/learnloop/instructional/wiring|learnloop.instructional.wiring]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_discriminating_search.py](../../../../../../tests/test_discriminating_search.py) — direct import
  - `test_presentation_order_applies_dominance_inside_the_valued_group`
- [tests/test_reader_followups_review.py](../../../../../../tests/test_reader_followups_review.py) — direct import
  - `test_f12_the_production_valuer_composes_the_attempt_familiarity_discount`
  - `test_f5_revaluation_never_reaches_the_exposure_judge`
  - `test_f7_revaluation_passes_the_stored_pending_decision`
  - `test_f9_a_formative_only_retention_question_reaches_a_valuation_problem`

## Modification guidance

- Make changes here when the responsibility remains discriminating within learnloop.instructional; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/instructional/discriminating.py](../../../../../../src/learnloop/instructional/discriminating.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
