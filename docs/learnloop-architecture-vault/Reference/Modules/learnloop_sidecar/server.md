---
title: "learnloop_sidecar.server"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/server.py"
source_paths:
  - "src/learnloop_sidecar/server.py"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop_sidecar"
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
  - "learnloop_sidecar.server module"
  - "src/learnloop_sidecar/server.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.server`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps server behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]]. Its public surface centers on `serve`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/server.py](../../../../../src/learnloop_sidecar/server.py) |
| Source lines | 153 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `serve(stdin: TextIO, stdout: TextIO) -> None` ([source](../../../../../src/learnloop_sidecar/server.py), line 24)

### Module constants

- `LOG` ([src/learnloop_sidecar/server.py](../../../../../src/learnloop_sidecar/server.py), line 16)
- `_INTERNAL_ERROR_MESSAGE` ([src/learnloop_sidecar/server.py](../../../../../src/learnloop_sidecar/server.py), line 18)

## Internal implementation anchors

- `_handle(ctx: SidecarContext, request: Any) -> dict[str, Any] | None` ([source](../../../../../src/learnloop_sidecar/server.py), line 42)
- `_elapsed_ms(started: float) -> float` ([source](../../../../../src/learnloop_sidecar/server.py), line 105)
- `_write(stdout: TextIO, response: dict[str, Any]) -> None` ([source](../../../../../src/learnloop_sidecar/server.py), line 109)
- `_request_id(request: Any) -> Any` ([source](../../../../../src/learnloop_sidecar/server.py), line 133)
- `_safe_validation_errors(exc: ValidationError) -> list[dict[str, Any]]` ([source](../../../../../src/learnloop_sidecar/server.py), line 137) — Return actionable Pydantic diagnostics without echoing request values.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/__main__|learnloop_sidecar.__main__]] — imports `serve`; statically calls `serve`

### Repository tooling consumers

- [scripts/gen_goldenpath_fixtures.py](../../../../../scripts/gen_goldenpath_fixtures.py); calls `serve`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`; calls `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`, `json_rpc_error`, `sidecar_error`; calls `json_rpc_error`, `sidecar_error`
- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/logging|learnloop_sidecar.logging]] — imports `log_event`; calls `log_event`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `METHOD_REGISTRY`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `logging`, `time`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/__main__|learnloop_sidecar.__main__]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_probe_orchestration_remainder.py](../../../../../tests/test_probe_orchestration_remainder.py) — direct import
- [tests/test_probe_remint.py](../../../../../tests/test_probe_remint.py) — direct import
- [tests/test_provenance_service.py](../../../../../tests/test_provenance_service.py) — direct import
- [tests/test_question_queue.py](../../../../../tests/test_question_queue.py) — direct import
  - `test_sidecar_queue_roundtrip`
  - `test_sidecar_reader_question_transcript_can_be_resumed`
- [tests/test_reveal_ledger.py](../../../../../tests/test_reveal_ledger.py) — direct import
  - `test_reopening_feedback_does_not_charge_again`
- [tests/test_settings_sidecar.py](../../../../../tests/test_settings_sidecar.py) — direct import
- [tests/test_sidecar_animation.py](../../../../../tests/test_sidecar_animation.py) — direct import
- [tests/test_sidecar_append.py](../../../../../tests/test_sidecar_append.py) — direct import
- [tests/test_sidecar_blueprint_picker.py](../../../../../tests/test_sidecar_blueprint_picker.py) — direct import
- [tests/test_sidecar_contract.py](../../../../../tests/test_sidecar_contract.py) — direct import
- [tests/test_sidecar_diagnostic.py](../../../../../tests/test_sidecar_diagnostic.py) — direct import
- [tests/test_sidecar_golden_path.py](../../../../../tests/test_sidecar_golden_path.py) — direct import
- [tests/test_sidecar_golden_path_assessment.py](../../../../../tests/test_sidecar_golden_path_assessment.py) — direct import
- [tests/test_sidecar_ingest_m3.py](../../../../../tests/test_sidecar_ingest_m3.py) — direct import
- [tests/test_sidecar_item_authoring.py](../../../../../tests/test_sidecar_item_authoring.py) — direct import
- [tests/test_sidecar_knowledge_model.py](../../../../../tests/test_sidecar_knowledge_model.py) — direct import
- [tests/test_sidecar_ladder.py](../../../../../tests/test_sidecar_ladder.py) — direct import
- [tests/test_sidecar_probe.py](../../../../../tests/test_sidecar_probe.py) — direct import
- [tests/test_sidecar_quick_add.py](../../../../../tests/test_sidecar_quick_add.py) — direct import
- [tests/test_sidecar_reader.py](../../../../../tests/test_sidecar_reader.py) — direct import
- [tests/test_sidecar_reader_p3.py](../../../../../tests/test_sidecar_reader_p3.py) — direct import
- [tests/test_sidecar_registry.py](../../../../../tests/test_sidecar_registry.py) — direct import
- [tests/test_sidecar_span_view.py](../../../../../tests/test_sidecar_span_view.py) — direct import
- [tests/test_sidecar_synthesis.py](../../../../../tests/test_sidecar_synthesis.py) — direct import
- [tests/test_sidecar_teach_back.py](../../../../../tests/test_sidecar_teach_back.py) — direct import
- [tests/test_sidecar_transport.py](../../../../../tests/test_sidecar_transport.py) — direct import
  - `test_non_serializable_handler_result_becomes_a_protocol_error_response`
  - `test_unexpected_handler_failure_marks_the_commit_outcome_unknown`
- [tests/test_sidecar_tutor_qa.py](../../../../../tests/test_sidecar_tutor_qa.py) — direct import
- [tests/test_source_deletion.py](../../../../../tests/test_source_deletion.py) — direct import

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/server.py](../../../../../src/learnloop_sidecar/server.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
