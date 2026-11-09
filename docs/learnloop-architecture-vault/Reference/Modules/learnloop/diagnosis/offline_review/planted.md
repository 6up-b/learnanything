---
title: "learnloop.diagnosis.offline_review.planted"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/offline_review/planted.py"
source_paths:
  - "src/learnloop/diagnosis/offline_review/planted.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.offline_review"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.offline_review.planted module"
  - "src/learnloop/diagnosis/offline_review/planted.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-offline-review"
---

# `learnloop.diagnosis.offline_review.planted`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.offline_review.planted` exists within [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] to own the behavior summarized by its module contract: Planted learners with known truth (Slice 1 §12 S1.0).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/offline_review/planted.py](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py) |
| Source lines | 471 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class PlantedAttemptDraft(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 55)
- `class PlantedScenarioDraft(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 68)
- `class PlantedAttempt` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 126)
- `class PlantedCase` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 139)
  - `target_cause(self) -> str` (line 150; public)
  - `expected_link_ids(self) -> tuple[str, ...]` (line 153; public)
  - `forbidden_link_ids(self) -> tuple[str, ...]` (line 162; public)
  - `truth(self) -> dict[str, Any]` (line 169; public)
  - `as_record(self) -> dict[str, Any]` (line 182; public)
  - `from_record(cls, record: Mapping[str, Any]) -> 'PlantedCase'` (line 195; public)
- `class PlantedCaseInvalid(ValueError)` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 208)
- `case_from_draft(shape: str, draft: PlantedScenarioDraft, *, vault: LoadedVault, learning_object_id: str, allowed_items: set[str], start: datetime, source: str='generated') -> PlantedCase` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 263) — Validate a draft and mint real-looking ids and timestamps.
- `candidate_items(vault: LoadedVault, learning_object_id: str) -> list[PracticeItem]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 310) — Items on the LO and its one-hop neighbours (cross-surface material).
- `plantable_learning_objects(vault: LoadedVault, preferred: Sequence[str]=()) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 334) — LOs with at least two candidate items, preferred ones first.
- `scenario_request(vault: LoadedVault, shape: str, learning_object_id: str, *, max_items: int=8) -> tuple[str, set[str]]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 346)
- `request_planted_scenario(client: OperationClient, prompt: str) -> PlantedScenarioDraft` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 352)
- `cases_from_manifest(payload: Any, *, vault: LoadedVault, start: datetime) -> list[PlantedCase]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 362) — Authored cases: ``[{"shape", "learning_object_id", "scenario": <draft>}]``.
- `planted_history_store(vault: LoadedVault, case: PlantedCase) -> StaticHistoryStore` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 427)
- `default_start() -> datetime` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 451)

### Module constants

- `PLANTED_PROMPT_VERSION` ([src/learnloop/diagnosis/offline_review/planted.py](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 49)
- `SHAPES` ([src/learnloop/diagnosis/offline_review/planted.py](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 50)
- `_PLANTED_ERROR_TYPE` ([src/learnloop/diagnosis/offline_review/planted.py](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 52)
- `_SHAPE_RULES` ([src/learnloop/diagnosis/offline_review/planted.py](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 76)

### Explicit exports

`__all__` declares:

- `PLANTED_PROMPT_VERSION`
- `SHAPES`
- `PlantedAttempt`
- `PlantedAttemptDraft`
- `PlantedCase`
- `PlantedCaseInvalid`
- `PlantedScenarioDraft`
- `candidate_items`
- `case_from_draft`
- `cases_from_manifest`
- `default_start`
- `plantable_learning_objects`
- `planted_history_store`
- `request_planted_scenario`
- `scenario_request`

## Internal implementation anchors

- `_scenario_prompt(shape: str, learning_object_id: str, items: Sequence[Mapping[str, Any]]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 100)
- `_validate_draft(shape: str, draft: PlantedScenarioDraft, vault: LoadedVault, allowed_items: set[str]) -> None` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 212)
- `_item_payload(vault: LoadedVault, item: PracticeItem) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 321)
- `_history_attempt(vault: LoadedVault, attempt: PlantedAttempt) -> HistoryAttempt` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py), line 394) — A planted past attempt, graded by construction (blind-equivalent).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `PLANTED_PROMPT_VERSION`, `PlantedCase`, `PlantedCaseInvalid`, `SHAPES`, `case_from_draft`, `cases_from_manifest`, `default_start`, `plantable_learning_objects`, `planted_history_store`, `request_planted_scenario`, `scenario_request`; statically calls `case_from_draft`, `cases_from_manifest`, `default_start`, `plantable_learning_objects`, `planted_history_store`, `request_planted_scenario`, `scenario_request`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `OperationClient`, `execute_structured_operation`, `render_structured_prompt`; calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `resolve_quote_anchor`, `resolved_rubric`; calls `resolve_quote_anchor`, `resolved_rubric`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `HistoryAttempt`, `HypothesisRecord`, `StaticHistoryStore`, `learning_object_neighborhood`; calls `HistoryAttempt`, `HypothesisRecord`, `StaticHistoryStore`, `learning_object_neighborhood`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `presented_prompt`; calls `presented_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `json`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/diagnosis_fakes.py](../../../../../../../tests/diagnosis_fakes.py) — direct import
- [tests/test_required_method_round3_review.py](../../../../../../../tests/test_required_method_round3_review.py) — direct import
  - `test_f4_model_readers_and_review_exports_render_the_instruction`

## Modification guidance

- Change planted policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/offline_review/planted.py](../../../../../../../src/learnloop/diagnosis/offline_review/planted.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
