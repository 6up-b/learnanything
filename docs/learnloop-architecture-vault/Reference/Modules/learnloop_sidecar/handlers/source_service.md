---
title: "learnloop_sidecar.handlers.source_service"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/source_service.py"
source_paths:
  - "src/learnloop_sidecar/handlers/source_service.py"
source_commit: "20402f4e3f41b01dab1bcc6b580ae0bf032b093f"
source_commit_timestamp: "2026-11-01T09:43:59-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop_sidecar.handlers.source_service module"
  - "src/learnloop_sidecar/handlers/source_service.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.source_service`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.source_service` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Canonical-sources service RPCs (spec_source_practice_and_probes_v1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/source_service.py](../../../../../../src/learnloop_sidecar/handlers/source_service.py) |
| Source lines | 311 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `20402f4e3f41b01dab1bcc6b580ae0bf032b093f` |
| Commit timestamp | `2026-11-01T09:43:59-05:00` |

## Public API

- `class ImpressionKey(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/source_service.py), line 31)
- `class RecordImpressionsInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/source_service.py), line 38)
- `record_proposal_impressions_rpc(ctx: SidecarContext, params: RecordImpressionsInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/source_service.py), line 46) — Fire-and-forget after render: which proposals a surface showed (§6.5).
- `class ImportSourceExerciseInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/source_service.py), line 61)
- `class GetSourceExerciseImportInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/source_service.py), line 68)
- `import_source_exercise_rpc(ctx: SidecarContext, params: ImportSourceExerciseInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/source_service.py), line 73) — A learner picked a textbook exercise proposal: queue its import (S1, §6.3).
- `queue_source_exercise_import(ctx: SidecarContext, vault: Any, repository: Any, *, proposal_id: str, extraction_id: str, span_ids: list[str]) -> dict[str, str]` ([source](../../../../../../src/learnloop_sidecar/handlers/source_service.py), line 88) — The learner's pick of a textbook exercise proposal, queued (S1, §7.2): the import row, the selection's usage verdict and the job.
- `get_source_exercise_import_rpc(ctx: SidecarContext, params: GetSourceExerciseImportInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/source_service.py), line 128) — An import's status, its key's honest label and, once written, the item id.
- `class CallerInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/source_service.py), line 151) — Who is asking: a kind and a reference only.
- `class FindSourcesInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/source_service.py), line 161)
- `class CompareSourcesInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/source_service.py), line 181)
- `server_caller(ctx: SidecarContext, caller: CallerInput) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/source_service.py), line 195)
- `find_sources_rpc(ctx: SidecarContext, params: FindSourcesInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/source_service.py), line 213) — Verbatim passages for an intent, under the caller's derived policy (S3, §9).
- `compare_sources_rpc(ctx: SidecarContext, params: CompareSourcesInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/source_service.py), line 238) — How the learner's sources treat one question: quote-verified, no consensus (S3, §9.4).
- `class RunSourceToolInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/source_service.py), line 263)
- `run_source_tool_rpc(ctx: SidecarContext, params: RunSourceToolInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/source_service.py), line 268) — Run a tool request a tutor answer carried (S4, §10.3), under the caller context stored with the request: the policy cannot change between the answer and the run.
- `class RecordSourceOfferShownInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/source_service.py), line 289)
- `record_source_offer_shown_rpc(ctx: SidecarContext, params: RecordSourceOfferShownInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/source_service.py), line 296) — Fire-and-forget when a passage offer is opened or a comparison is shown (S5, §11.1).

### Module constants

- `SOURCE_SERVICE_RPCS` ([src/learnloop_sidecar/handlers/source_service.py](../../../../../../src/learnloop_sidecar/handlers/source_service.py), line 20)
- `SOURCE_CALLER_KINDS` ([src/learnloop_sidecar/handlers/source_service.py](../../../../../../src/learnloop_sidecar/handlers/source_service.py), line 192)

### Explicit exports

`__all__` declares:

- `SOURCE_SERVICE_RPCS`
- `queue_source_exercise_import`
- `server_caller`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `queue_source_exercise_import`; statically calls `queue_source_exercise_import`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `KEY_STATUS_LABELS`, `effective_key_status`, `import_row`, `insert_import`; calls `effective_key_status`, `import_row`, `insert_import`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]] — imports `offer_shown`; calls `offer_shown`
- [[Reference/Modules/learnloop/instructional/policy|learnloop.instructional.policy]] — imports `caller_for`, `caller_for_question_event`; calls `caller_for`, `caller_for_question_event`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `interactive_import_request`, `proposed_exercise`, `record_exercise_pick`, `record_proposal_impressions`; calls `interactive_import_request`, `proposed_exercise`, `record_exercise_pick`, `record_proposal_impressions`
- [[Reference/Modules/learnloop/instructional/sources|learnloop.instructional.sources]] — imports `propose_comparison`, `propose_sources`, `refuse_withheld_comparison`; calls `propose_comparison`, `propose_sources`, `refuse_withheld_comparison`
- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `ToolArgumentsInvalid`, `run_requested_tool`; calls `run_requested_tool`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `IntentUnavailable`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `PolicyRefused`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/practice_index|learnloop_sidecar.handlers.practice_index]] — imports `_injected`, `plan_minutes_estimator`; calls `_injected`, `plan_minutes_estimator`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_ad23_rpcs_are_all_of_them`
  - `test_the_pinned_daily_plan_rpcs_are_all_of_them`
  - `test_the_pinned_intent_rpcs_are_all_of_them`
  - `test_the_pinned_source_service_rpcs_are_all_of_them`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/source_service.py](../../../../../../src/learnloop_sidecar/handlers/source_service.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
