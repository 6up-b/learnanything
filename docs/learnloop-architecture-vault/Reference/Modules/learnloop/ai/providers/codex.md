---
title: "learnloop.ai.providers.codex"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/providers/codex.py"
source_paths:
  - "src/learnloop/ai/providers/codex.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.ai.providers"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.providers.codex module"
  - "src/learnloop/ai/providers/codex.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai-providers"
---

# `learnloop.ai.providers.codex`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.providers.codex` exists within [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] to own the behavior summarized by its module contract: Codex SDK structured transport and runtime integration.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/providers/codex.py](../../../../../../../src/learnloop/ai/providers/codex.py) |
| Source lines | 805 |
| Owning package | [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class SdkCodexClient(TokenUsageAccounting)` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 47) — Codex Python SDK-backed client.
  - `__init__(self, config: CodexConfig, vault_root: Path)` (line 55; internal)
  - `interrupt(self) -> bool` (line 72; public) — Interrupt this client's active SDK turn without killing the sidecar.
  - `_expire_turn(self, turn: Any, codex: Any) -> None` (line 89; internal) — Deadline callback: request a clean interrupt, then force-close if needed.
  - `_schedule_turn_stop(self, turn: Any, codex: Any) -> None` (line 98; internal) — Stop an SDK turn without blocking the palette or deadline thread.
  - `complete(self, request: StructuredRequest[Any]) -> Any` (line 124; public) — Execute one structured request with Codex's existing repair policy.
  - `supports(self, capability: str) -> bool` (line 143; public)
  - `_complete_validated(self, prompt: str, model_type: type[BaseModel], *, purpose: str) -> Any` (line 151; internal) — Run one structured turn and repair malformed/schema-invalid JSON once.
  - `_run_structured(self, prompt: str, output_schema: dict[str, Any], *, purpose: str, timeout_seconds: float | None=None) -> str` (line 220; internal)
- `class CodexHealthChecker(Protocol)` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 480)
  - `__call__(self, checkout_path: Path, config: CodexConfig) -> None` (line 481; internal)
- `class CodexStartupProcess(Protocol)` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 485)
  - `poll(self) -> int | None` (line 486; public)
- `class CodexStartupRunner(Protocol)` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 490)
  - `__call__(self, checkout_path: Path, config: CodexConfig) -> CodexStartupProcess` (line 491; internal)
- `class CodexAuthRequired(RuntimeError)` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 495)
- `class CodexHealthUnavailable(RuntimeError)` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 499)
- `class CodexRuntimeReport` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 504)
  - `ready(self) -> bool` (line 512; public)
  - `as_dict(self) -> dict[str, str | bool | None]` (line 515; public)
- `check_codex_runtime(vault_root: Path, config: CodexConfig, *, healthcheck: CodexHealthChecker | None=None, startup: CodexStartupRunner | None=None) -> CodexRuntimeReport` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 526)
- `default_startup(checkout_path: Path, config: CodexConfig) -> subprocess.Popen` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 630)
- `default_http_healthcheck(_checkout_path: Path, config: CodexConfig) -> None` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 669)
- `default_sdk_healthcheck(checkout_path: Path, config: CodexConfig) -> None` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 702)
- `codex_config_from_ai_profile(profile: AIProviderConfig) -> CodexConfig` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 754)
- `class CodexSDKProviderClient(SdkCodexClient)` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 785)
  - `__init__(self, provider_name: str, profile: AIProviderConfig, vault_root: Path)` (line 788; internal)
- `make_codex_client(config: CodexConfig, vault_root: Path) -> Any` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 795) — Build the legacy Codex selection from the relocated providers.

### Module constants

- `LOG` ([src/learnloop/ai/providers/codex.py](../../../../../../../src/learnloop/ai/providers/codex.py), line 44)
- `EVENT_FIELDS_ATTR` ([src/learnloop/ai/providers/codex.py](../../../../../../../src/learnloop/ai/providers/codex.py), line 45)
- `PINNED_REVISION_PLACEHOLDER` ([src/learnloop/ai/providers/codex.py](../../../../../../../src/learnloop/ai/providers/codex.py), line 477)

## Internal implementation anchors

- `_is_structured_json_transport_error(exc: BaseException) -> bool` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 369) — Whether app-server failed before returning malformed structured output.
- `_sdk_reasoning_effort(reasoning_effort_type: Any, value: str | None) -> Any` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 386)
- `_sdk_reasoning_summary(reasoning_summary_type: Any, value: str | None) -> Any` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 397)
- `_ensure_sdk_importable(sdk_python_path: Path) -> None` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 408)
- `_sdk_launch_args(command: str) -> tuple[str, ...] | None` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 415)
- `_resolved_sdk_codex_bin(configured: str | None) -> str | None` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 421) — Prefer an explicit/pinned SDK runtime, with a source-checkout fallback.
- `_resolve_checkout_path(vault_root: Path, checkout_path: str) -> Path` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 442)
- `_resolve_sdk_python_path(checkout_path: Path, sdk_python_path: str) -> Path` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 449)
- `_log_codex_debug(event: str, **fields: Any) -> None` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 456) — Emit full Codex request/response data into sidecar debug logs.
- `_wait_for_startup_health(checkout_path: Path, config: CodexConfig, healthcheck: CodexHealthChecker, process: CodexStartupProcess) -> None` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 643)
- `_url(base_url: str, path: str) -> str` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 714)
- `_resolve_checkout_path(vault_root: Path, checkout_path: str) -> Path` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 718)
- `_requires_revision_match(revision: str) -> bool` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 725)
- `_read_checkout_revision(checkout_path: Path) -> str | None` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 729)
- `_resolve_sdk_python_path(checkout_path: Path, sdk_python_path: str) -> Path` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 748)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `CodexSDKProviderClient`; statically calls `CodexSDKProviderClient`
- [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]] — imports `_log_codex_debug`, `codex_config_from_ai_profile`; statically calls `_log_codex_debug`, `codex_config_from_ai_profile`
- [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]] — imports `check_codex_runtime`, `codex_config_from_ai_profile`; statically calls `check_codex_runtime`, `codex_config_from_ai_profile`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `CodexRuntimeReport`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `CodexRuntimeReport`
- [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]] — imports `CodexRuntimeReport`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`, `AITurnTimeout`, `CodexInterrupted`, `CodexTurnTimeout`, `CodexUnavailable`; calls `AIInvalidOutput`, `AIProviderUnavailable`, `CodexInterrupted`, `CodexTurnTimeout`, `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]] — imports `HttpCodexClient`; calls `HttpCodexClient`
- [[Reference/Modules/learnloop/ai/providers/structured_output|learnloop.ai.providers.structured_output]] — imports `structured_output_regeneration_prompt`, `structured_output_repair_prompt`; calls `structured_output_regeneration_prompt`, `structured_output_repair_prompt`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `describe_wire_validation_error`; calls `describe_wire_validation_error`
- [[Reference/Modules/learnloop/ai/strict_schema|learnloop.ai.strict_schema]] — imports `strict_output_schema`; calls `strict_output_schema`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `INTERRUPT`, `STRUCTURED_COMPLETION`, `StructuredRequest`
- [[Reference/Modules/learnloop/ai/usage|learnloop.ai.usage]] — imports `TokenUsageAccounting`, `usage_from_codex_turn`; calls `usage_from_codex_turn`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `AIProviderConfig`, `CodexConfig`; calls `CodexConfig`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `logging`, `os`, `pathlib`, `shlex`, `shutil`, `subprocess`, `sys`, `threading`, `time`, `typing`, `urllib`
- Third party: `codex_cli_bin`, `openai_codex`, `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]], [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]], [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ai_config.py](../../../../../../../tests/test_ai_config.py) — direct import
  - `test_sparse_codex_ai_profile_uses_current_codex_defaults`
- [tests/test_codex_attempt_flow.py](../../../../../../../tests/test_codex_attempt_flow.py) — direct import
  - `test_attempt_orchestration_falls_back_when_runtime_not_ready`
- [tests/test_codex_http_client.py](../../../../../../../tests/test_codex_http_client.py) — direct import
  - `test_http_codex_client_health_and_grading_round_trip`
- [tests/test_codex_output_schema.py](../../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_sdk_authoring_path_passes_strict_schema_to_codex`
  - `test_sdk_codex_client_logs_full_prompt_and_response`
  - `test_sdk_codex_turn_timeout_interrupts_and_returns`
  - `test_sdk_reader_preset_regenerates_when_app_server_rejects_hex_escape`
  - `test_sdk_reader_preset_repairs_invalid_unicode_json_once`
  - `test_sdk_runtime_prefers_bundle_and_falls_back_for_source_checkout`
  - `test_sdk_teach_back_authoring_passes_source_and_quest_to_prompt`
- [tests/test_codex_runtime.py](../../../../../../../tests/test_codex_runtime.py) — direct import
  - `test_codex_runtime_ready_when_checkout_revision_and_health_pass`
  - `test_codex_runtime_reports_auth_required`
  - `test_codex_runtime_reports_missing_checkout`
  - `test_codex_runtime_reports_revision_mismatch`
  - `test_codex_runtime_reports_startup_timeout`
  - `test_codex_runtime_reports_unavailable_without_transport_or_failed_health`
  - `test_codex_runtime_starts_app_server_after_initial_health_failure`
- [tests/test_deferred_regrade.py](../../../../../../../tests/test_deferred_regrade.py) — direct import
  - `test_deferred_regrade_skips_when_runtime_not_ready`
- [tests/test_e2e_codex_mock.py](../../../../../../../tests/test_e2e_codex_mock.py) — direct import
- [tests/test_learner_review_system_entries.py](../../../../../../../tests/test_learner_review_system_entries.py) — direct import
- [tests/test_openai_chat_client.py](../../../../../../../tests/test_openai_chat_client.py) — direct import
  - `test_structured_providers_share_one_transport_surface`
- [tests/test_provider_resolution_parity.py](../../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_diagnostic_fire_uses_the_structured_completion_path`
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — direct import
  - `test_sdk_transport_executes_every_feature_operation`
  - `test_structured_providers_expose_no_feature_named_methods`
- [tests/test_teach_back.py](../../../../../../../tests/test_teach_back.py) — direct import

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/providers/codex.py](../../../../../../../src/learnloop/ai/providers/codex.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
