---
title: "learnloop_sidecar.handlers.library_exercises"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/library_exercises.py"
source_paths:
  - "src/learnloop_sidecar/handlers/library_exercises.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.library_exercises module"
  - "src/learnloop_sidecar/handlers/library_exercises.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.library_exercises`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.library_exercises` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench RW4b RPCs: exercises from my sources (spec_reader_workbench_v1 §7.4; UX §4.6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/library_exercises.py](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py) |
| Source lines | 510 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `exercises_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 88) — The candidate view exists: its own switch inside RW4a's library answer.
- `fallback_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 96)
- `prompt_contract_fields(vault: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 100) — What the Reader's prompt contract adds for RW4b (absent while off).
- `exposure_view(vault: Any, repository: Any, candidate: dict[str, Any], *, proposal_id: str | None, own_listing_event_ids: frozenset[str]=frozenset()) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 120) — The sources service's exposure rule for one exercise, as the Reader shows it.
- `pick_exposure(vault: Any, repository: Any, pick: dict[str, Any], *, practice_item_id: str | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 205) — The exposure rule read again for a picked exercise (Codex review F3): at the pick, which decides how it opens, and at admission, which the problem then shows.
- `pick_entry(exposure: dict[str, Any] | None, requested: str) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 261) — How a picked exercise opens, from the server's verdict: exposed, as practice beside the book (``work_through``); unexposed, as your own attempt with the book hidden (``practice_this``).
- `class CandidateKey(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 275)
- `class ExerciseCandidatesInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 280)
- `deliver_exercise_result(ctx: SidecarContext, result: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 298) — A finished exercise job's result as it may go out NOW (Reader RW4b fix round 6, F7): each candidate's region is read again through the one statement reader, at delivery.
- `reader_exercise_candidates(ctx: SidecarContext, params: ExerciseCandidatesInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 327) — The proposal's textbook exercises the Reader may show, each with its exposure (the sources service's rule) and how "use this one" offers it.
- `class FindExercisesInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 380)
- `reader_find_exercises(ctx: SidecarContext, params: FindExercisesInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 389) — "Find an exercise in my sources" (§7.4's fallback): exercise regions of the teaching scope over the question's learning objects, each with the request "use this one" sends to the Reader's own import.

### Module constants

- `LIBRARY_EXERCISE_RPCS` ([src/learnloop_sidecar/handlers/library_exercises.py](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 60)
- `EXPOSURE_INTENT` ([src/learnloop_sidecar/handlers/library_exercises.py](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 70)
- `EXPOSURE_LABELS` ([src/learnloop_sidecar/handlers/library_exercises.py](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 73)
- `RELATED_NOTE` ([src/learnloop_sidecar/handlers/library_exercises.py](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 83)
- `FALLBACK_LIMIT` ([src/learnloop_sidecar/handlers/library_exercises.py](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 85)
- `UNCHECKED_EXPOSURE_LABEL` ([src/learnloop_sidecar/handlers/library_exercises.py](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 183)

### Explicit exports

`__all__` declares:

- `EXPOSURE_INTENT`
- `EXPOSURE_LABELS`
- `LIBRARY_EXERCISE_RPCS`
- `exercises_enabled`
- `exposure_view`
- `fallback_enabled`
- `ExerciseStatement`
- `exercise_region_spans`
- `pick_entry`
- `pick_exposure`
- `prompt_contract_fields`
- `read_exercise_statement`

## Internal implementation anchors

- `_require(ctx: SidecarContext, *, fallback: bool=False)` ([source](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 108)
- `_proposal_lo_ids(found: dict[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 152) — The request's learning objects: they scope the rule's studied worked examples.
- `_proposal_candidate(entry: dict[str, Any], span_ids: list[str], lo_ids: list[str], read: ExerciseStatement) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 158) — A proposal's exercise as the exposure rule reads it: the same input at display, at the pick and at admission, so the rule's one judge answers a second reading from its ledger.
- `_preview(text: str) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 169) — A candidate's statement as a list shows it (the arm's display bound).
- `_own_listing_events(repository: Any, event_ids: list[str], extraction_id: str, span_ids: list[str]) -> frozenset[str]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 186) — Of the ids a fallback candidate came back with, those that really are its own listing's exposure rows (``library_exercises``, its spans): anything else the client names is ignored.
- `_start_job(ctx: SidecarContext, kind: str, work: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 285) — RW4a's library job runner: the work runs off the request path, on its own repository.
- `_fallback_candidates(vault: Any, repository: Any, hits: Any, lo_ids: list[str], limit: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py), line 417)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `prompt_contract_fields`; statically calls `prompt_contract_fields`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `module`; statically calls `pick_entry`, `pick_exposure`, `read_exercise_statement`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `selection_for_region`; calls `selection_for_region`
- [[Reference/Modules/learnloop/content/sources/exercise_statements|learnloop.content.sources.exercise_statements]] — imports `ExerciseStatement`, `exercise_region_spans`, `read_exercise_statement`; calls `exercise_region_spans`, `read_exercise_statement`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]] — imports `proposal`; calls `proposal`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `exercise_key`; calls `exercise_key`
- [[Reference/Modules/learnloop/instructional/exercises|learnloop.instructional.exercises]] — imports `STATEMENT_CHARS`, `exercise_label`, `imported_span_keys`; calls `exercise_label`, `imported_span_keys`
- [[Reference/Modules/learnloop/instructional/exposure|learnloop.instructional.exposure]] — imports `EXPOSURE_RULE_VERSION`, `independent_check_eligibility`; calls `independent_check_eligibility`
- [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]] — imports `record_shown_spans`; calls `record_shown_spans`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `proposed_exercise`; calls `proposed_exercise`
- [[Reference/Modules/learnloop/instructional/sources|learnloop.instructional.sources]] — imports `propose_sources`; calls `propose_sources`
- [[Reference/Modules/learnloop/router_objective/exposure|learnloop.router_objective.exposure]] — imports `module`; calls `fields`, `get`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `module`; calls `library_ask_enabled`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `PolicyRefused`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `_job_payload`, `_jobs`, `reader_caller`; calls `_job_payload`, `_jobs`, `reader_caller`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]], [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_library_exercises.py](../../../../../../tests/test_library_exercises.py) — direct import
  - `test_a_fallback_pick_is_not_exposed_by_its_own_listing_and_its_request_reaches_the_import_unchanged`
  - `test_r2_contract_no_workbench_or_reader_exercise_rpc_returns_a_held_out_statement`
  - `test_r2_the_shared_reader_lives_where_s1_and_the_reader_import_it`
  - `test_r4_the_statement_reader_fails_closed`
  - `test_the_new_rpcs_take_no_policy_and_the_workbench_view_of_other_problems_is_unchanged`
- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_rw4b_rpcs_are_all_of_them`
- [tests/test_reader_rw4b_admission_idempotency.py](../../../../../../tests/test_reader_rw4b_admission_idempotency.py) — direct import
- [tests/test_reader_rw4b_fix6.py](../../../../../../tests/test_reader_rw4b_fix6.py) — direct import

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/library_exercises.py](../../../../../../src/learnloop_sidecar/handlers/library_exercises.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
