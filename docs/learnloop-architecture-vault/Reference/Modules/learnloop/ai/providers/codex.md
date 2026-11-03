---
title: "learnloop.ai.providers.codex"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/providers/codex.py"
source_paths:
  - "src/learnloop/ai/providers/codex.py"
source_commit: "182e5c55a2ddf8d411166c8a02bfd0373f71ebf4"
source_commit_timestamp: "2026-10-27T09:58:20-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
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
| Source lines | 2116 |
| Owning package | [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `182e5c55a2ddf8d411166c8a02bfd0373f71ebf4` |
| Commit timestamp | `2026-10-27T09:58:20-04:00` |

## Public API

- `isolated_turn_overrides(readable_root: Path, *, shell: bool, mcp_server_ids: tuple[str, ...] | list[str]=(), extra_disabled_features: tuple[str, ...] | list[str]=(), model_catalog: Path | str | None=None, skills: tuple[tuple[str, str], ...] | list[tuple[str, str]]=()) -> list[str]` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 291) — ``codex -c key=value`` overrides that confine one turn (the locked-down profile).
- `class SdkCodexClient(TokenUsageAccounting)` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 427) — Codex Python SDK-backed client.
  - `__init__(self, config: CodexConfig, vault_root: Path)` (line 435; internal)
  - `_codex_command(self) -> list[str]` (line 455; internal) — The argv that runs this client's Codex CLI before a subcommand.
  - `_launch(self, root: Path, sandbox: ToolIsolation | None=None) -> _Launch` (line 478; internal) — The turn's Codex subprocesses as they start in ``root`` (hardening round 2, H2).
  - `_verified_isolated_overrides(self, root: Path, *, shell: bool, sandbox: ToolIsolation | None=None, deadline: _Deadline | None=None) -> list[str]` (line 496; internal) — The isolated turn's overrides, checked on the CLI that will run it.
  - `_refuse_reenabled_features(launch: tuple[str, ...] | None, overrides: list[str]) -> None` (line 691; internal) — Refuse a launch command whose ``--enable`` turns a feature ``overrides`` switch off back on (F2).
  - `_mcp_server_states(self, cwd: Path, overrides: list[str], **context: Any) -> dict[str, bool]` (line 703; internal) — Each server ``codex mcp list --json`` lists under ``overrides``: on?
  - `_feature_listing(self, cwd: Path, overrides: list[str], **context: Any) -> tuple[dict[str, bool], dict[str, str]]` (line 729; internal) — ``codex features list`` under ``overrides``: ``name stage true|false`` rows, as states and stages.
  - `_cli_version(self, cwd: Path, **context: Any) -> str | None` (line 745; internal) — ``codex --version`` for a refusal's message; ``None`` when it cannot be read.
  - `_raise_if_stopped(self, deadline: _Deadline | None, where: str) -> None` (line 756; internal) — Interrupted, or past the request's deadline: stop before the next step.
  - `_codex_probe(self, cwd: Path, overrides: list[str], *subcommand: str, sandbox: ToolIsolation | None=None, deadline: _Deadline | None=None, launch: _Launch | None=None) -> str` (line 764; internal) — The stdout of ``codex -c <override>...
  - `workspace_activity(self) -> list[str] | None` (line 854; public) — What the last read-only-workspace turn reported reading, if anything.
  - `interrupt(self) -> bool` (line 864; public) — Interrupt this client's active SDK turn without killing the sidecar.
  - `_expire_turn(self, turn: Any, codex: Any) -> None` (line 884; internal) — Deadline callback: request a clean interrupt, then force-close if needed.
  - `_schedule_turn_stop(self, turn: Any, codex: Any) -> None` (line 893; internal) — Stop an SDK turn without blocking the palette or deadline thread.
  - `complete(self, request: StructuredRequest[Any]) -> Any` (line 919; public) — Execute one structured request with Codex's existing repair policy.
  - `supports(self, capability: str) -> bool` (line 949; public)
  - `_complete_validated(self, prompt: str, model_type: type[BaseModel], *, purpose: str, workspace: Path | None=None, isolated: bool=False) -> Any` (line 966; internal) — Run one structured turn and repair malformed/schema-invalid JSON once.
  - `_run_structured(self, prompt: str, output_schema: dict[str, Any], *, purpose: str, timeout_seconds: float | None=None, workspace: Path | None=None, isolated: bool=False) -> str` (line 1063; internal) — Run one SDK turn, always locked down.
  - `_inline_workspace(self, workspace: Path, prompt: str) -> str` (line 1146; internal) — ``prompt`` followed by every file of ``workspace``, each recorded as served (round 3).
  - `_run_sdk_turn(self, prompt: str, output_schema: dict[str, Any], *, purpose: str, timeout_seconds: float | None, cwd: str, root: Path, isolated: bool, workspace: Path | None, sandbox: ToolIsolation | None=None) -> str` (line 1170; internal)
  - `_run_verified_sdk_turn(self, prompt: str, output_schema: dict[str, Any], *, purpose: str, cwd: str, root: Path, isolated: bool, workspace: Path | None, sandbox: ToolIsolation | None, deadline: _Deadline, turn_timeout: float, overrides: list[str], launch_args: tuple[str, ...] | None, config_kwargs: dict[str, Any], sdk: tuple[Any, ...]) -> str` (line 1242; internal) — The turn itself, after its launch check passed (split from :meth:`_run_sdk_turn` so the sandboxed turn's catalog pin is removed on every exit).
  - `_report_turn_usage(self, result: Any, lockdown: TurnLockdown) -> None` (line 1493; internal) — Meter one turn: its own thread plus every other thread the SDK reported.
- `class CodexHealthChecker(Protocol)` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1775)
  - `__call__(self, checkout_path: Path, config: CodexConfig) -> None` (line 1776; internal)
- `class CodexStartupProcess(Protocol)` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1780)
  - `poll(self) -> int | None` (line 1781; public)
- `class CodexStartupRunner(Protocol)` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1785)
  - `__call__(self, checkout_path: Path, config: CodexConfig) -> CodexStartupProcess` (line 1786; internal)
- `class CodexAuthRequired(RuntimeError)` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1790)
- `class CodexHealthUnavailable(RuntimeError)` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1794)
- `class CodexRuntimeReport` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1799)
  - `ready(self) -> bool` (line 1807; public)
  - `as_dict(self) -> dict[str, str | bool | None]` (line 1810; public)
- `check_codex_runtime(vault_root: Path, config: CodexConfig, *, healthcheck: CodexHealthChecker | None=None, startup: CodexStartupRunner | None=None) -> CodexRuntimeReport` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1821)
- `default_startup(checkout_path: Path, config: CodexConfig) -> subprocess.Popen` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1937)
- `default_http_healthcheck(_checkout_path: Path, config: CodexConfig) -> None` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1978)
- `default_sdk_healthcheck(checkout_path: Path, config: CodexConfig) -> None` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 2012)
- `codex_config_from_ai_profile(profile: AIProviderConfig) -> CodexConfig` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 2064)
- `class CodexSDKProviderClient(SdkCodexClient)` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 2095)
  - `__init__(self, provider_name: str, profile: AIProviderConfig, vault_root: Path)` (line 2098; internal)
- `make_codex_client(config: CodexConfig, vault_root: Path) -> Any` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 2105) — Build the legacy Codex selection from the relocated providers.

### Module constants

- `LOG` ([src/learnloop/ai/providers/codex.py](../../../../../../../src/learnloop/ai/providers/codex.py), line 107)
- `EVENT_FIELDS_ATTR` ([src/learnloop/ai/providers/codex.py](../../../../../../../src/learnloop/ai/providers/codex.py), line 108)
- `_ISOLATION_DISABLED_FEATURES` ([src/learnloop/ai/providers/codex.py](../../../../../../../src/learnloop/ai/providers/codex.py), line 125)
- `_ADDRESSABLE_MCP_SERVER` ([src/learnloop/ai/providers/codex.py](../../../../../../../src/learnloop/ai/providers/codex.py), line 130)
- `_REJECTED_MCP_TABLE` ([src/learnloop/ai/providers/codex.py](../../../../../../../src/learnloop/ai/providers/codex.py), line 132)
- `_CODEX_PROBE_TIMEOUT_SECONDS` ([src/learnloop/ai/providers/codex.py](../../../../../../../src/learnloop/ai/providers/codex.py), line 135)
- `_CODEX_CONFIG_OPTIONS` ([src/learnloop/ai/providers/codex.py](../../../../../../../src/learnloop/ai/providers/codex.py), line 141)
- `_APP_SERVER_OPTIONS_WITH_VALUE` ([src/learnloop/ai/providers/codex.py](../../../../../../../src/learnloop/ai/providers/codex.py), line 145)
- `_APP_SERVER_SWITCHES` ([src/learnloop/ai/providers/codex.py](../../../../../../../src/learnloop/ai/providers/codex.py), line 146)
- `_CATALOG_PIN_DIR` ([src/learnloop/ai/providers/codex.py](../../../../../../../src/learnloop/ai/providers/codex.py), line 379)
- `_CATALOG_PIN_LOCK` ([src/learnloop/ai/providers/codex.py](../../../../../../../src/learnloop/ai/providers/codex.py), line 380)
- `_SANDBOX_PIN_PREFIX` ([src/learnloop/ai/providers/codex.py](../../../../../../../src/learnloop/ai/providers/codex.py), line 414)
- `_TEXT_ONLY_TURN_ITEMS` ([src/learnloop/ai/providers/codex.py](../../../../../../../src/learnloop/ai/providers/codex.py), line 1592)
- `UNACCOUNTED_TURN_ITEM` ([src/learnloop/ai/providers/codex.py](../../../../../../../src/learnloop/ai/providers/codex.py), line 1598)
- `PINNED_REVISION_PLACEHOLDER` ([src/learnloop/ai/providers/codex.py](../../../../../../../src/learnloop/ai/providers/codex.py), line 1772)

## Internal implementation anchors

- `class _RejectedMcpTable(CodexUnavailable)` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 149) — Codex refused to load the config because of one ``mcp_servers`` table.
- `class _Deadline` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 158) — One request's wall-clock bound, shared by the launch check and the turn.
- `_stop_probe(process: subprocess.Popen) -> None` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 179) — Kill a launch-check probe and what it started in its session.
- `_isolated_launch_parts(launch: tuple[str, ...] | list[str]) -> tuple[list[str], list[str]]` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 199) — An ``sdk_launch_command`` as an isolated turn runs it: ``(command, app_server_args)``.
- `_reenabled_isolation_features(command: list[str], overrides: list[str]) -> list[str]` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 262) — Features ``overrides`` turn off that a ``--enable`` in ``command`` turns back on.
- `_toml_string(value: str) -> str` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 287)
- `class _Launch` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 364) — How a Codex subprocess of one turn starts, resolved as it will resolve it (H2).
- `_write_catalog_pin(catalog: str, sandbox: ToolIsolation | None) -> Path` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 383) — The validated catalog's exact text as a file the turn's app server can read.
- `_remove_sandbox_catalog_pin(overrides: list[str] | None, sandbox: ToolIsolation | None) -> None` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 417) — Remove a sandboxed turn's catalog directory, leaving the working directory as it was.
- `_receipt_fields_from_breakdown(breakdown: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1526) — Receipt token fields of one ``TokenUsageBreakdown`` (model or camelCase dict).
- `_turn_made_several_requests(result: Any) -> bool` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1544) — Whether a finished turn's own usage shows more than one model request.
- `_tool_use_refusal(violations: list[str], purpose: str) -> CodexToolUseRefused` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1567)
- `_sdk_accepts(config_type: Any, field_name: str) -> bool` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1576) — Whether the SDK's app-server config type takes ``field_name``.
- `_workspace_activity(result: Any) -> list[str] | None` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1601) — Commands or paths the agent's tool items reported, when exposed.
- `_is_structured_json_transport_error(exc: BaseException) -> bool` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1633) — Whether app-server failed before returning malformed structured output.
- `_bundled_codex_path() -> str | None` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1650)
- `_isolated_launch(isolation: Any, codex_bin: str | None, launch_args: tuple[str, ...] | None, launcher_dir: Path) -> tuple[str | None, tuple[str, ...] | None]` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1659) — The SDK launch settings that run the app-server inside the sandbox.
- `_sdk_reasoning_effort(reasoning_effort_type: Any, value: str | None) -> Any` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1681)
- `_sdk_reasoning_summary(reasoning_summary_type: Any, value: str | None) -> Any` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1692)
- `_ensure_sdk_importable(sdk_python_path: Path) -> None` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1703)
- `_sdk_launch_args(command: str) -> tuple[str, ...] | None` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1710)
- `_resolved_sdk_codex_bin(configured: str | None) -> str | None` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1716) — Prefer an explicit/pinned SDK runtime, with a source-checkout fallback.
- `_resolve_checkout_path(vault_root: Path, checkout_path: str) -> Path` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1737)
- `_resolve_sdk_python_path(checkout_path: Path, sdk_python_path: str) -> Path` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1744)
- `_log_codex_debug(event: str, **fields: Any) -> None` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1751) — Emit full Codex request/response data into sidecar debug logs.
- `_wait_for_startup_health(checkout_path: Path, config: CodexConfig, healthcheck: CodexHealthChecker, process: CodexStartupProcess) -> None` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 1952)
- `_url(base_url: str, path: str) -> str` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 2024)
- `_resolve_checkout_path(vault_root: Path, checkout_path: str) -> Path` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 2028)
- `_requires_revision_match(revision: str) -> bool` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 2035)
- `_read_checkout_revision(checkout_path: Path) -> str | None` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 2039)
- `_resolve_sdk_python_path(checkout_path: Path, sdk_python_path: str) -> Path` ([source](../../../../../../../src/learnloop/ai/providers/codex.py), line 2058)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `CodexSDKProviderClient`; statically calls `CodexSDKProviderClient`
- [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]] — imports `_log_codex_debug`, `codex_config_from_ai_profile`; statically calls `_log_codex_debug`, `codex_config_from_ai_profile`
- [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]] — imports `check_codex_runtime`, `codex_config_from_ai_profile`; statically calls `check_codex_runtime`, `codex_config_from_ai_profile`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `CodexRuntimeReport`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `CodexRuntimeReport`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/boundary|learnloop.experiments.contextual_embeddings.boundary]] — imports `module`; statically calls `isolated_turn_overrides`
- [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]] — imports `CodexRuntimeReport`

### Repository tooling consumers

- [scripts/benchmark_chatgpt_plan_latency.py](../../../../../../../scripts/benchmark_chatgpt_plan_latency.py); calls `SdkCodexClient`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/chatgpt_plan/workspace|learnloop.ai.chatgpt_plan.workspace]] — imports `INSTRUCTIONS_INLINE`, `ServedWorkspace`, `WorkspaceTooLarge`; calls `ServedWorkspace`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIOutputTruncated`, `AIProviderUnavailable`, `AITurnTimeout`, `CodexInterrupted`, `CodexTurnTimeout`, `CodexUnavailable`; calls `AIInvalidOutput`, `AIOutputTruncated`, `AIProviderUnavailable`, `CodexInterrupted`, `CodexTurnTimeout`, `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `generation_limit`, `observed_sdk_turn`, `output_limit`, `report_call_usage`, `single_request_active`; calls `generation_limit`, `output_limit`, `report_call_usage`, `single_request_active`
- [[Reference/Modules/learnloop/ai/isolation|learnloop.ai.isolation]] — imports `TOOL_ISOLATION`, `ToolIsolation`, `ToolIsolationUnavailable`, `agent_home`, `current_tool_isolation`, `sandboxed_command`, `write_launcher`; calls `ToolIsolationUnavailable`, `agent_home`, `current_tool_isolation`, `sandboxed_command`, `write_launcher`
- [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]] — imports `HttpCodexClient`; calls `HttpCodexClient`
- [[Reference/Modules/learnloop/ai/providers/codex_lockdown|learnloop.ai.providers.codex_lockdown]] — imports `CodexHttpTransportRefused`, `CodexLockdownUnavailable`, `CodexToolUseRefused`, `ISOLATED_PROFILE`, `LOCKDOWN_DISABLED_FEATURES`, `TurnLockdown`, `advertised_tool_violations`, `cached_check`, `catalog_pin_override`, `catalog_pin_path`, `catalog_violations`, `check_fingerprint`, `cli_version_text`, `disabled_features`, `feature_refusal`, `feature_violations`, `install_on_sdk`, `item_violations`, `lockdown_config_overrides`, `model_metadata_violations`, `module`, `permission_profile_violations`, `readback_overrides`, `remember_check`, `rendered_skills`, `resolve_codex_home`, `resolve_executable`, `shell_environment_overrides`, `skill_disable_overrides`, `tool_free_catalog`, `tool_free_violations`, `unclassified_features_on`; calls `CodexLockdownUnavailable`, `CodexToolUseRefused`, `TurnLockdown`, `advertised_tool_violations`, `cached_check`, `catalog_pin_override`, `catalog_pin_path`, `catalog_violations`, `check_fingerprint`, `cli_version_text`, `disabled_features`, `feature_refusal`, `feature_violations`, `install_on_sdk`, `item_violations`, `lockdown_config_overrides`, `model_metadata_violations`, `permission_profile_violations`, `readback_overrides`, `refuse_legacy_http_transport`, `remember_check`, `rendered_skills`, `resolve_codex_home`, `resolve_executable`, `shell_environment_overrides`, `skill_disable_overrides`, `tool_free_catalog`, `tool_free_violations`, `unclassified_features_on`
- [[Reference/Modules/learnloop/ai/providers/structured_output|learnloop.ai.providers.structured_output]] — imports `structured_output_regeneration_prompt`, `structured_output_repair_prompt`; calls `structured_output_regeneration_prompt`, `structured_output_repair_prompt`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `describe_wire_validation_error`; calls `describe_wire_validation_error`
- [[Reference/Modules/learnloop/ai/strict_schema|learnloop.ai.strict_schema]] — imports `strict_output_schema`; calls `strict_output_schema`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `INTERRUPT`, `ISOLATED_TURN`, `READ_ONLY_WORKSPACE`, `STRUCTURED_COMPLETION`, `StructuredRequest`
- [[Reference/Modules/learnloop/ai/usage|learnloop.ai.usage]] — imports `TokenUsageAccounting`, `UsageMeter`, `receipt_fields_from_codex_turn`, `usage_from_codex_turn`; calls `UsageMeter`, `receipt_fields_from_codex_turn`, `usage_from_codex_turn`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `AIProviderConfig`, `CodexConfig`; calls `CodexConfig`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `inspect`, `json`, `logging`, `os`, `pathlib`, `re`, `shlex`, `shutil`, `signal`, `subprocess`, `sys`, `tempfile`, `threading`, `time`, `typing`, `urllib`
- Third party: `codex_cli_bin`, `openai_codex`, `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]], [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]], [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/codex_cli_fakes.py](../../../../../../../tests/codex_cli_fakes.py) — direct import
- [tests/test_ai_config.py](../../../../../../../tests/test_ai_config.py) — direct import
  - `test_sparse_codex_ai_profile_uses_current_codex_defaults`
- [tests/test_ai_single_request.py](../../../../../../../tests/test_ai_single_request.py) — direct import
  - `test_codex_single_request_disables_regeneration_and_repair_only_in_scope`
  - `test_codex_single_request_fails_closed_before_sdk_startup`
- [tests/test_ai_tool_isolation.py](../../../../../../../tests/test_ai_tool_isolation.py) — direct import
  - `test_a_workspace_outside_the_sandbox_is_inlined_and_never_mounted`
  - `test_an_isolated_turn_passes_its_profile_through_the_sandbox_launcher`
  - `test_an_isolated_turn_runs_its_permission_profile_inside_the_sandbox`
  - `test_codex_refuses_an_isolated_request_without_bubblewrap`
  - `test_the_codex_app_server_launches_inside_the_sandbox`
- [tests/test_codex_attempt_flow.py](../../../../../../../tests/test_codex_attempt_flow.py) — direct import
  - `test_attempt_orchestration_falls_back_when_runtime_not_ready`
- [tests/test_codex_cli_0164_lockdown.py](../../../../../../../tests/test_codex_cli_0164_lockdown.py) — direct import
- [tests/test_codex_cli_0165_lockdown.py](../../../../../../../tests/test_codex_cli_0165_lockdown.py) — direct import
  - `test_every_launch_sends_both_switches_and_the_bundled_skills_switch`
- [tests/test_codex_cli_0166_lockdown.py](../../../../../../../tests/test_codex_cli_0166_lockdown.py) — direct import
  - `test_every_launch_sends_all_eight_switches`
- [tests/test_codex_http_client.py](../../../../../../../tests/test_codex_http_client.py) — direct import
  - `test_http_codex_client_health_and_grading_round_trip`
- [tests/test_codex_isolation_mcp_check.py](../../../../../../../tests/test_codex_isolation_mcp_check.py) — direct import
  - `test_a_check_that_fails_or_times_out_refuses_the_turn`
  - `test_a_read_only_workspace_turn_is_checked_under_its_own_overrides`
  - `test_a_turn_that_did_not_ask_for_isolation_is_checked_and_locked_down_too`
  - `test_an_interrupt_during_the_check_stops_it_and_nothing_launches`
  - `test_an_interrupt_stops_a_check_running_inside_the_sandbox`
  - `test_plugin_servers_are_disabled_by_feature_and_config_servers_by_name`
  - `test_the_check_runs_inside_the_request_deadline`
  - `test_the_check_runs_inside_the_sandbox_in_the_turns_own_directory`
  - `test_the_installed_codex_addresses_path_characters_but_not_dots`
  - `test_the_installed_codex_passes_the_launch_check`
  - `test_the_installed_codex_pins_a_server_only_an_unseen_ancestor_project_disables`
  - `test_the_installed_codex_rejects_a_name_override_for_a_plugin_server`
  - `test_without_servers_the_first_listing_is_the_check`
- [tests/test_codex_lockdown_frozen.py](../../../../../../../tests/test_codex_lockdown_frozen.py) — direct import
  - `test_an_inherited_notifier_cannot_run_after_a_locked_down_turn`
  - `test_every_launch_clears_the_legacy_notifier`
- [tests/test_codex_lockdown_round2.py](../../../../../../../tests/test_codex_lockdown_round2.py) — direct import
  - `test_a_layer_that_names_the_turns_profile_is_caught_by_the_readback`
  - `test_a_lower_layer_cannot_widen_the_turns_permission_profile`
  - `test_the_http_runtime_check_never_runs_its_health_request_or_startup_command`
  - `test_the_legacy_provider_http_is_refused_by_the_lockdown`
  - `test_the_profile_name_is_fresh_and_never_the_fixed_one`
- [tests/test_codex_lockdown_round3.py](../../../../../../../tests/test_codex_lockdown_round3.py) — direct import
  - `test_a_skill_that_stays_listed_refuses_the_turn`
  - `test_a_snapshot_diagnosis_on_codex_is_inlined_and_gives_the_same_structured_output`
  - `test_an_export_over_the_inline_budget_refuses_before_launch`
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
- [tests/test_codex_tool_lockdown.py](../../../../../../../tests/test_codex_tool_lockdown.py) — direct import
  - `test_a_workspace_command_cannot_see_inherited_credentials`
  - `test_an_enable_flag_for_an_unclassified_feature_refuses_the_turn`
  - `test_every_request_runs_the_locked_down_profile_with_approvals_denied`
  - `test_every_turn_pins_the_command_environment_and_turns_shell_snapshots_off`
- [tests/test_deferred_regrade.py](../../../../../../../tests/test_deferred_regrade.py) — direct import
  - `test_deferred_regrade_skips_when_runtime_not_ready`
- [tests/test_diagnosis_history_modes.py](../../../../../../../tests/test_diagnosis_history_modes.py) — direct import
  - `test_codex_workspace_replaces_the_vault_root`
- [tests/test_diagnosis_input_provenance.py](../../../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_the_export_s_entries_map_to_what_they_serve`
  - `test_the_transport_reports_every_tool_item_it_cannot_read`
- [tests/test_diagnosis_isolation.py](../../../../../../../tests/test_diagnosis_isolation.py) — direct import
  - `test_a_launch_override_gets_the_overrides_before_app_server`
  - `test_a_snapshot_turn_runs_under_the_profile_never_the_builtin_sandbox`
  - `test_a_turn_that_did_not_ask_for_isolation_never_starts_in_the_vault`
  - `test_an_isolated_turn_cannot_read_a_sentinel_outside_its_workspace`
  - `test_an_isolated_turn_without_a_workspace_starts_in_an_empty_directory`
  - `test_configured_mcp_servers_are_listed_and_disabled`
  - `test_isolated_overrides_switch_the_tools_off`
  - `test_the_app_server_starts_the_thread_under_the_learnloop_profile`
- [tests/test_e0_review_round4_followup.py](../../../../../../../tests/test_e0_review_round4_followup.py) — direct import
  - `test_the_label_passes_never_reach_a_codex_turn`
  - `test_the_paid_cli_refuses_when_the_lockdown_is_not_in_force`
- [tests/test_e2e_codex_mock.py](../../../../../../../tests/test_e2e_codex_mock.py) — direct import
- [tests/test_ingestion_checkpoints.py](../../../../../../../tests/test_ingestion_checkpoints.py) — direct import
  - `test_codex_does_not_repair_when_reported_output_consumed_the_budget`
- [tests/test_learner_review_system_entries.py](../../../../../../../tests/test_learner_review_system_entries.py) — direct import
- [tests/test_lo_general.py](../../../../../../../tests/test_lo_general.py) — direct import
  - `test_rebuild_deterministic_and_no_external_io`
- [tests/test_openai_chat_client.py](../../../../../../../tests/test_openai_chat_client.py) — direct import
  - `test_structured_providers_share_one_transport_surface`
- [tests/test_output_budget.py](../../../../../../../tests/test_output_budget.py) — direct import
  - `test_codex_turns_take_the_routes_effort_for_that_turn_only`
- [tests/test_pf_generation.py](../../../../../../../tests/test_pf_generation.py) — direct import
  - `test_a_codex_pf_turn_starts_outside_the_vault_with_tools_off_and_never_reuses_unisolated_work`
- [tests/test_project_cli.py](../../../../../../../tests/test_project_cli.py) — direct import
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
