---
title: "learnloop.hints.map_seeds"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/hints/map_seeds.py"
source_paths:
  - "src/learnloop/hints/map_seeds.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.hints"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.hints.map_seeds module"
  - "src/learnloop/hints/map_seeds.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-hints"
---

# `learnloop.hints.map_seeds`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.hints.map_seeds` exists within [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] to own the behavior summarized by its module contract: Adaptive hints H1: what an approach map is built from (spec §4.3 items 1-3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/hints/map_seeds.py](../../../../../../src/learnloop/hints/map_seeds.py) |
| Source lines | 327 |
| Owning package | [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SeedSpan` ([source](../../../../../../src/learnloop/hints/map_seeds.py), line 58)
  - `key(self) -> str` (line 67; public)
- `class SeedAttempt` ([source](../../../../../../src/learnloop/hints/map_seeds.py), line 72)
- `class MapSeeds` ([source](../../../../../../src/learnloop/hints/map_seeds.py), line 82)
  - `structure_hash(self) -> str` (line 97; public)
  - `checkpoint_ids(self) -> frozenset[str]` (line 101; public)
  - `recipe_ids(self) -> frozenset[str]` (line 111; public)
  - `span_refs(self) -> dict[str, str]` (line 114; public)
  - `attempt_refs(self) -> dict[str, str]` (line 117; public)
  - `seeds_hash(self) -> str` (line 121; public)
  - `record(self) -> dict[str, Any]` (line 129; public) — ``seeds_json``: which seeds the map was built from (ids, never texts).
- `item_skeletons(connection: Any, item: PracticeItem) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/hints/map_seeds.py), line 162) — PF's persisted solution skeletons of the item's current text (paid output, read only).
- `rubric_seed(vault: LoadedVault, item: PracticeItem) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/hints/map_seeds.py), line 175) — The rubric the builder reads: the item's own, else its practice mode's default (``vault.rubric_for_item``), as the criteria the prompt carries.
- `structure_hash(item: PracticeItem, skeletons: Sequence[Mapping[str, Any]], rubric: Sequence[Mapping[str, Any]]) -> str` ([source](../../../../../../src/learnloop/hints/map_seeds.py), line 184) — The item-side seeds ``practice_item_hash`` does not cover: the trace contract, the PF skeletons and the resolved rubric (an inherited default rubric changes without the item changing), and the authored hints, which it does.
- `item_revision(vault: LoadedVault, connection: Any, item: PracticeItem) -> tuple[str, str]` ([source](../../../../../../src/learnloop/hints/map_seeds.py), line 200) — ``(practice_item_hash, structure_hash)``: the cheap revision key a serve checks.
- `family_items(vault: LoadedVault, item: PracticeItem) -> list[PracticeItem]` ([source](../../../../../../src/learnloop/hints/map_seeds.py), line 206)
- `qualifying_attempts(vault: LoadedVault, connection: Any, item: PracticeItem, *, limit: int=MAX_ATTEMPTS) -> list[SeedAttempt]` ([source](../../../../../../src/learnloop/hints/map_seeds.py), line 212) — The learner's own correct solutions to the item and its family siblings, newest first: graded fully correct, or a PF-c valid alternative; never a grade held for review, never a non-answer (G-H9).
- `source_worked_examples(vault: LoadedVault, repository: Any, item: PracticeItem, *, find: Callable[..., Any] | None=None) -> tuple[list[SeedSpan], dict[str, Any]]` ([source](../../../../../../src/learnloop/hints/map_seeds.py), line 247) — The learner's own books' worked examples for the item's LO (T6, consumed).
- `item_side(vault: LoadedVault, connection: Any, item: PracticeItem) -> MapSeeds` ([source](../../../../../../src/learnloop/hints/map_seeds.py), line 274) — Seeds from the item alone (no retrieval, no attempts).
- `assemble_seeds(vault: LoadedVault, repository: Any, item: PracticeItem, *, retrieve: bool=True, find: Callable[..., Any] | None=None) -> MapSeeds` ([source](../../../../../../src/learnloop/hints/map_seeds.py), line 290) — Every seed of the item.

### Module constants

- `MAX_SPANS` ([src/learnloop/hints/map_seeds.py](../../../../../../src/learnloop/hints/map_seeds.py), line 48)
- `SPAN_CHARS` ([src/learnloop/hints/map_seeds.py](../../../../../../src/learnloop/hints/map_seeds.py), line 49)
- `MAX_ATTEMPTS` ([src/learnloop/hints/map_seeds.py](../../../../../../src/learnloop/hints/map_seeds.py), line 50)
- `ATTEMPT_CHARS` ([src/learnloop/hints/map_seeds.py](../../../../../../src/learnloop/hints/map_seeds.py), line 51)
- `_NOT_OWN_ROUTE` ([src/learnloop/hints/map_seeds.py](../../../../../../src/learnloop/hints/map_seeds.py), line 53)

### Explicit exports

`__all__` declares:

- `ATTEMPT_CHARS`
- `MAX_ATTEMPTS`
- `MAX_SPANS`
- `SPAN_CHARS`
- `MapSeeds`
- `SeedAttempt`
- `SeedSpan`
- `assemble_seeds`
- `family_items`
- `item_revision`
- `item_side`
- `item_skeletons`
- `qualifying_attempts`
- `rubric_seed`
- `source_worked_examples`
- `structure_hash`

## Internal implementation anchors

- `_sha(text: str) -> str` ([source](../../../../../../src/learnloop/hints/map_seeds.py), line 152)
- `_checkpoint_id(checkpoint: Any) -> str` ([source](../../../../../../src/learnloop/hints/map_seeds.py), line 156)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `MAX_ATTEMPTS`, `MAX_SPANS`, `MapSeeds`, `SPAN_CHARS`, `SeedAttempt`, `SeedSpan`, `assemble_seeds`, `item_revision`, `item_side`, `qualifying_attempts`; statically calls `SeedAttempt`, `SeedSpan`, `assemble_seeds`, `item_revision`, `item_side`, `qualifying_attempts`
- [[Reference/Modules/learnloop/hints/map_report|learnloop.hints.map_report]] — imports `item_revision`; statically calls `item_revision`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/approach_maps|learnloop.db.stores.approach_maps]] — imports `module`; calls `family_template`
- [[Reference/Modules/learnloop/db/stores/pf|learnloop.db.stores.pf]] — imports `skeletons_for_hashes`; calls `skeletons_for_hashes`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_for_review_attempts`; calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `pfc_unverified_attempt_ids`; calls `pfc_unverified_attempt_ids`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `find_sources_for_caller`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `CallerContext`; calls `CallerContext`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `practice_item_hash`, `skeleton_content_hash`; calls `practice_item_hash`, `skeleton_content_hash`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]], [[Reference/Modules/learnloop/hints/map_report|learnloop.hints.map_report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_approach_maps.py](../../../../../../tests/test_approach_maps.py) — direct import
  - `test_f5_an_inherited_rubric_change_is_a_new_revision`
  - `test_only_the_learners_own_correct_or_pfc_valid_solutions_in_the_family_are_seeds`
  - `test_worked_examples_come_from_t6_under_the_item_bound_policy`

## Modification guidance

- Make changes here when the responsibility remains map seeds within learnloop.hints; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/hints/map_seeds.py](../../../../../../src/learnloop/hints/map_seeds.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
