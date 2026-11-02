---
title: "learnloop_sidecar.handlers.first_run"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/first_run.py"
source_paths:
  - "src/learnloop_sidecar/handlers/first_run.py"
source_commit: "207bb0738f7dfb722c0e6868b764c55788eca767"
source_commit_timestamp: "2026-10-24T09:50:26-04:00"
source_worktree_state: "clean"
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
  - "learnloop_sidecar.handlers.first_run module"
  - "src/learnloop_sidecar/handlers/first_run.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.first_run`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.first_run` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: UX Phase 1 RPCs: one Add, the AI connection sheet, and the book card's actions.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/first_run.py](../../../../../../src/learnloop_sidecar/handlers/first_run.py) |
| Source lines | 490 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `207bb0738f7dfb722c0e6868b764c55788eca767` |
| Commit timestamp | `2026-10-24T09:50:26-04:00` |

## Public API

- `authoring_route_for(vault) -> core.AuthoringRoute` ([source](../../../../../../src/learnloop_sidecar/handlers/first_run.py), line 45)
- `chatgpt_plan_ready() -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/first_run.py), line 65)
- `chatgpt_plan_models() -> list[str]` ([source](../../../../../../src/learnloop_sidecar/handlers/first_run.py), line 74)
- `class AddSourceInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/first_run.py), line 85)
- `add_source_rpc(ctx: SidecarContext, params: AddSourceInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/first_run.py), line 94) — Add one or more sources; the first that can open is ``opened``.
- `get_ai_connection(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/first_run.py), line 156) — Can an AI write questions in this library, and has the learner said OK?
- `class ConnectAiInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/first_run.py), line 162)
- `connect_ai(ctx: SidecarContext, params: ConnectAiInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/first_run.py), line 195) — Connect an AI for every use case and record the learner's one OK.
- `class SourceActionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/first_run.py), line 282)
- `source_action(ctx: SidecarContext, params: SourceActionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/first_run.py), line 333) — Run the one action a book card's status line (or its details) offers.

### Module constants

- `_CONNECT_USE_CASES` ([src/learnloop_sidecar/handlers/first_run.py](../../../../../../src/learnloop_sidecar/handlers/first_run.py), line 40)
- `_DEFAULT_OPENROUTER_MODEL` ([src/learnloop_sidecar/handlers/first_run.py](../../../../../../src/learnloop_sidecar/handlers/first_run.py), line 41)

## Internal implementation anchors

- `_status_route(vault) -> core.AuthoringRoute` ([source](../../../../../../src/learnloop_sidecar/handlers/first_run.py), line 49) — The build's route for a status read: no "Use OpenRouter instead" offer (re-review F1).
- `_connection_payload(ctx: SidecarContext) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/first_run.py), line 119)
- `_route_every_use_case(updates: dict[tuple[str, ...], Any], target: str, tiers: dict[str, str] | None=None) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/first_run.py), line 168)
- `_written_plan_model(vault) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/first_run.py), line 178) — The slug written under ``[ai.providers.chatgpt] model`` in the vault's file ("" when unset).
- `_allow_file_upload(ctx: SidecarContext, flow: str | None=None) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/first_run.py), line 306) — The separate OK for sending whole files out (spec §6.6, review F1), recorded once with its date like the connection's OK.
- `_latest_import_pages(repository, source_id: str) -> list[int] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/first_run.py), line 464)
- `_reread_plan(ctx: SidecarContext, vault, repository, source_id: str, artifact) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/first_run.py), line 470) — What reading this book again reads, costs and carries; refuses at once when its original file changed or went missing (re-read safety E1).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/chatgpt_plan/session|learnloop.ai.chatgpt_plan.session]] — imports `PlanSession`; calls `PlanSession`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `status_as`
- [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]] — imports `list_plan_models`; calls `list_plan_models`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `global_ai_defaults_path`; calls `global_ai_defaults_path`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `DEFAULT_CHATGPT_PLAN_MODEL`, `DEFAULT_SERVING_TASK_ROUTES`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `module`; calls `AddSourceOptions`, `_completed_extraction`, `add_source`, `authoring_route_for`, `consent_label`, `file_upload_allowed`, `import_jobs`, `latest_add_batch`, `latest_planner`, `learner_title`, `outline_chapters`, `pending_upload_flow`, `release_waiting_builds`, `request_auto_build`, `retry_build`, `text_recognition_available`, `undo_source_questions`, `upload_consent_key`, `what_leaves`
- [[Reference/Modules/learnloop/content/pipeline/exam_marking|learnloop.content.pipeline.exam_marking]] — imports `module`; calls `mark_exam_material`, `mark_plan`
- [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]] — imports `module`, `restore_readable_revision`; calls `carry_owed`, `finish_carry_over`, `original_bytes`, `reread_plan`, `restore_readable_revision`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `IngestRunnerError`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `build_source_outline`; calls `build_source_outline`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `connection_note`; calls `connection_note`
- [[Reference/Modules/learnloop/ingest/extractors/glm_ocr|learnloop.ingest.extractors.glm_ocr]] — imports `selected_backend`; calls `selected_backend`
- [[Reference/Modules/learnloop/ops/settings_store|learnloop.ops.settings_store]] — imports `SettingsStoreError`, `USE_CASE_ROUTES`, `apply_config_updates`, `save_ai_settings_to`; calls `apply_config_updates`, `save_ai_settings_to`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `EmptyParams`, `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `_parse_page_selection`; calls `_parse_page_selection`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `logging`, `os`, `tomllib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_decider_landing.py](../../../../../../tests/test_decider_landing.py) — direct import
- [tests/test_exam_protection_identity.py](../../../../../../tests/test_exam_protection_identity.py) — direct import
- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_source_action_actions_are_all_of_them`
- [tests/test_ux_phase1_connect_ai.py](../../../../../../tests/test_ux_phase1_connect_ai.py) — direct import
  - `test_an_openrouter_key_connects_every_use_case`
  - `test_connecting_releases_books_that_were_waiting`
  - `test_continue_with_chatgpt_needs_a_sign_in_first`
  - `test_continue_with_chatgpt_routes_every_use_case_to_the_plan`
  - `test_one_ok_records_consent_for_the_connected_provider`
  - `test_without_a_ready_route_the_sheet_asks_to_connect`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/first_run.py](../../../../../../src/learnloop_sidecar/handlers/first_run.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
