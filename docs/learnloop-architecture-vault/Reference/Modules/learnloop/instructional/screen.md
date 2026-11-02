---
title: "learnloop.instructional.screen"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/instructional/screen.py"
source_paths:
  - "src/learnloop/instructional/screen.py"
source_commit: "2802437abacd50fe33ade8228bb0d56735a97622"
source_commit_timestamp: "2026-10-13T13:29:11-04:00"
source_worktree_state: "clean"
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
  - "learnloop.instructional.screen module"
  - "src/learnloop/instructional/screen.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-instructional"
---

# `learnloop.instructional.screen`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.instructional.screen` exists within [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] to own the behavior summarized by its module contract: Screening unimported textbook exercises against rival hypotheses (spec §8.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/instructional/screen.py](../../../../../../src/learnloop/instructional/screen.py) |
| Source lines | 223 |
| Owning package | [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2802437abacd50fe33ade8228bb0d56735a97622` |
| Commit timestamp | `2026-10-13T13:29:11-04:00` |

## Public API

- `class HypothesisSignature(WireModel)` ([source](../../../../../../src/learnloop/instructional/screen.py), line 51)
- `class ExerciseScreen(WireModel)` ([source](../../../../../../src/learnloop/instructional/screen.py), line 57)
- `class ExerciseScreens(WireModel)` ([source](../../../../../../src/learnloop/instructional/screen.py), line 64)
- `slot_description(repository: Repository, slot: str) -> str` ([source](../../../../../../src/learnloop/instructional/screen.py), line 68)
- `classify(screen: ExerciseScreen, slots: Sequence[str], refs: Mapping[str, str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/screen.py), line 83)
- `screen_exercises(vault: LoadedVault, repository: Repository, problem: Any, exercises: Sequence[Mapping[str, Any]], *, client: Any | None=None, owner_id: str='exercise_discrimination', clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/screen.py), line 111) — ``{"status", "screens": {exercise key: classification}}``; never raises for a route failure.
- `persisted_screen(repository: Repository, judgment_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/instructional/screen.py), line 203) — A screen as its ``judgment_ledger`` row recorded it (no model call): the classification, the exercise and the hypothesis space it was read in.

### Module constants

- `SCREEN_PROMPT_VERSION` ([src/learnloop/instructional/screen.py](../../../../../../src/learnloop/instructional/screen.py), line 38)
- `_INSTRUCTIONS` ([src/learnloop/instructional/screen.py](../../../../../../src/learnloop/instructional/screen.py), line 41)

### Explicit exports

`__all__` declares:

- `ExerciseScreens`
- `SCREEN_PROMPT_VERSION`
- `classify`
- `persisted_screen`
- `screen_exercises`
- `slot_description`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/instructional/discriminating|learnloop.instructional.discriminating]] — imports `screen_exercises`; statically calls `screen_exercises`
- [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]] — imports `persisted_screen`; statically calls `persisted_screen`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `persisted_screen`; statically calls `persisted_screen`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`; calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`; calls `SpendBudget`, `SpendCaps`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]] — imports `judgments_by_ids`; calls `judgments_by_ids`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `route_skip`; calls `route_skip`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `plan_route`, `resolve_client`, `transport_problem`; calls `PaidCalls`, `plan_route`, `resolve_client`, `transport_problem`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `service_spend`; calls `service_spend`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/instructional/discriminating|learnloop.instructional.discriminating]], [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]], [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/source_service_fakes.py](../../../../../../tests/source_service_fakes.py) — direct import
- [tests/test_discriminating_search.py](../../../../../../tests/test_discriminating_search.py) — direct import
  - `test_screens_are_noiseless_bounds_or_structural`

## Modification guidance

- Make changes here when the responsibility remains screen within learnloop.instructional; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/instructional/screen.py](../../../../../../src/learnloop/instructional/screen.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
