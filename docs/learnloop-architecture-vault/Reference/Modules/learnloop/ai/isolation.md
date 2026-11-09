---
title: "learnloop.ai.isolation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/isolation.py"
source_paths:
  - "src/learnloop/ai/isolation.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ai"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.isolation module"
  - "src/learnloop/ai/isolation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.isolation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.isolation` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: Tool and filesystem isolation for model calls that must stay closed-book.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/isolation.py](../../../../../../src/learnloop/ai/isolation.py) |
| Source lines | 526 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class ToolIsolation` ([source](../../../../../../src/learnloop/ai/isolation.py), line 121) — What an isolated call may see: one empty working directory, nothing else.
- `tool_isolation(isolation: ToolIsolation) -> Iterator[ToolIsolation]` ([source](../../../../../../src/learnloop/ai/isolation.py), line 132)
- `current_tool_isolation() -> ToolIsolation | None` ([source](../../../../../../src/learnloop/ai/isolation.py), line 140)
- `class ToolIsolationUnavailable(RuntimeError)` ([source](../../../../../../src/learnloop/ai/isolation.py), line 144) — The transport cannot confine its tools here; the call must not run.
- `bubblewrap_path() -> str | None` ([source](../../../../../../src/learnloop/ai/isolation.py), line 148)
- `isolation_unavailable_reason() -> str | None` ([source](../../../../../../src/learnloop/ai/isolation.py), line 154)
- `isolation_mode(client: Any) -> tuple[str | None, str | None]` ([source](../../../../../../src/learnloop/ai/isolation.py), line 162) — ``(mode, reason)``: how ``client`` would honour an isolation request.
- `agent_home() -> Path` ([source](../../../../../../src/learnloop/ai/isolation.py), line 179)
- `executable_assets(executable: Path) -> Path` ([source](../../../../../../src/learnloop/ai/isolation.py), line 197) — What an executable needs mounted: the file itself, or its Node package.
- `sandbox_arguments(isolation: ToolIsolation, *, executables: Iterable[Path]=(), home: Path | None=None, arguments: Iterable[str]=(), chdir: Path | None=None) -> list[str]` ([source](../../../../../../src/learnloop/ai/isolation.py), line 367) — bubblewrap options (without the program) for one isolated process.
- `sandboxed_command(isolation: ToolIsolation, command: list[str], *, home: Path | None=None, chdir: Path | None=None) -> list[str]` ([source](../../../../../../src/learnloop/ai/isolation.py), line 466) — ``command`` wrapped in bubblewrap, started in ``chdir`` (default: the working directory); raises when bubblewrap is unavailable.
- `write_launcher(directory: Path, isolation: ToolIsolation, executable: str, *, home: Path | None=None) -> Path` ([source](../../../../../../src/learnloop/ai/isolation.py), line 494) — A ``#!/bin/sh`` launcher that runs ``executable "$@"`` inside the sandbox.

### Module constants

- `TOOL_FREE` ([src/learnloop/ai/isolation.py](../../../../../../src/learnloop/ai/isolation.py), line 97)
- `TOOL_ISOLATION` ([src/learnloop/ai/isolation.py](../../../../../../src/learnloop/ai/isolation.py), line 98)
- `_SYSTEM_READ_ONLY` ([src/learnloop/ai/isolation.py](../../../../../../src/learnloop/ai/isolation.py), line 100)
- `_SYSTEM_LINKS` ([src/learnloop/ai/isolation.py](../../../../../../src/learnloop/ai/isolation.py), line 101)
- `AGENT_HOME_WRITABLE` ([src/learnloop/ai/isolation.py](../../../../../../src/learnloop/ai/isolation.py), line 107)
- `AGENT_HOME_READ_ONLY` ([src/learnloop/ai/isolation.py](../../../../../../src/learnloop/ai/isolation.py), line 108)
- `AGENT_ENV_PINNED_TO_HOME` ([src/learnloop/ai/isolation.py](../../../../../../src/learnloop/ai/isolation.py), line 112)
- `AGENT_ENV_UNSET` ([src/learnloop/ai/isolation.py](../../../../../../src/learnloop/ai/isolation.py), line 113)
- `AGENT_STATE_SETTINGS` ([src/learnloop/ai/isolation.py](../../../../../../src/learnloop/ai/isolation.py), line 114)
- `AGENT_SYSTEM_CONFIG` ([src/learnloop/ai/isolation.py](../../../../../../src/learnloop/ai/isolation.py), line 117)

### Explicit exports

`__all__` declares:

- `TOOL_FREE`
- `TOOL_ISOLATION`
- `ToolIsolation`
- `ToolIsolationUnavailable`
- `agent_home`
- `bubblewrap_path`
- `current_tool_isolation`
- `executable_assets`
- `isolation_mode`
- `isolation_unavailable_reason`
- `sandbox_arguments`
- `sandboxed_command`
- `tool_isolation`
- `write_launcher`

## Internal implementation anchors

- `_inside(path: Path, roots: Iterable[str]) -> bool` ([source](../../../../../../src/learnloop/ai/isolation.py), line 184)
- `_is_node_launcher(path: Path) -> bool` ([source](../../../../../../src/learnloop/ai/isolation.py), line 188)
- `_contains(outer: Path, inner: Path) -> bool` ([source](../../../../../../src/learnloop/ai/isolation.py), line 212)
- `_refuse_if_it_covers_the_home(what: str, mount: Path, home: Path) -> None` ([source](../../../../../../src/learnloop/ai/isolation.py), line 216) — A bind that follows the in-memory home must not contain it (see the module docstring).
- `_refuse_if_it_is_inside_the_home(what: str, mount: Path, home: Path) -> None` ([source](../../../../../../src/learnloop/ai/isolation.py), line 227) — A writable host bind inside the in-memory home would receive what the agent keeps there.
- `_setting(path: Path, key: str) -> tuple[bool, Any]` ([source](../../../../../../src/learnloop/ai/isolation.py), line 238) — ``(present, value)`` of the top-level ``key`` in the TOML file at ``path``.
- `_override_name(override: str) -> str | None` ([source](../../../../../../src/learnloop/ai/isolation.py), line 265) — The key of a ``key=value`` override as Codex reads it: before the first ``=``, trimmed.
- `_command_line_settings(arguments: Iterable[str], key: str) -> Iterator[tuple[str, Any]]` ([source](../../../../../../src/learnloop/ai/isolation.py), line 272) — Each ``-c``/``--config`` override of ``key``, parsed as Codex parses it.
- `_refuse_state_outside_the_home(home: Path, workdir: Path, mounted: Iterable[Path], binds_over_home: Iterable[Path], arguments: Iterable[str], start: Path | None=None) -> None` ([source](../../../../../../src/learnloop/ai/isolation.py), line 313) — Refuse a launch whose configuration moves the agent's run state out of its private home.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]] — imports `TOOL_FREE`
- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `TOOL_ISOLATION`, `ToolIsolation`, `ToolIsolationUnavailable`, `agent_home`, `current_tool_isolation`, `sandboxed_command`, `write_launcher`; statically calls `ToolIsolationUnavailable`, `agent_home`, `current_tool_isolation`, `sandboxed_command`, `write_launcher`
- [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] — imports `TOOL_FREE`
- [[Reference/Modules/learnloop/projects/ai_runtime|learnloop.projects.ai_runtime]] — imports `ToolIsolation`, `isolation_mode`, `tool_isolation`; statically calls `ToolIsolation`, `isolation_mode`, `tool_isolation`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `dataclasses`, `os`, `pathlib`, `shlex`, `shutil`, `sys`, `tomllib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]], [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]], [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]], [[Reference/Modules/learnloop/projects/ai_runtime|learnloop.projects.ai_runtime]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad23_fakes.py](../../../../../../tests/ad23_fakes.py) — direct import
- [tests/ad_fakes.py](../../../../../../tests/ad_fakes.py) — direct import
- [tests/approach_map_fakes.py](../../../../../../tests/approach_map_fakes.py) — direct import
- [tests/deliverable_fixtures.py](../../../../../../tests/deliverable_fixtures.py) — direct import
- [tests/figure_fixtures.py](../../../../../../tests/figure_fixtures.py) — direct import
- [tests/hint_fakes.py](../../../../../../tests/hint_fakes.py) — direct import
- [tests/notes_fixtures.py](../../../../../../tests/notes_fixtures.py) — direct import
- [tests/reading_path_fixtures.py](../../../../../../tests/reading_path_fixtures.py) — direct import
- [tests/section_coverage_fixtures.py](../../../../../../tests/section_coverage_fixtures.py) — direct import
- [tests/structured_ai.py](../../../../../../tests/structured_ai.py) — direct import
- [tests/teacher_fakes.py](../../../../../../tests/teacher_fakes.py) — direct import
- [tests/test_adaptive_difficulty_ad1.py](../../../../../../tests/test_adaptive_difficulty_ad1.py) — direct import
- [tests/test_ai_tool_isolation.py](../../../../../../tests/test_ai_tool_isolation.py) — direct import
  - `test_a_config_file_tomllib_cannot_parse_is_refused_only_when_it_could_name_the_setting`
  - `test_a_hidden_path_holding_the_working_directory_or_agent_home_is_refused`
  - `test_a_hidden_path_inside_a_mounted_package_is_masked`
  - `test_a_hidden_path_inside_the_working_directory_is_masked`
  - `test_a_launcher_inside_a_hidden_repo_is_refused_not_exposed`
  - `test_a_launcher_passes_its_arguments_through_the_sandbox`
  - `test_a_state_location_under_any_host_bind_in_the_home_is_refused`
  - `test_a_working_directory_that_holds_the_agent_home_is_refused`
  - `test_a_workspace_outside_the_sandbox_is_inlined_and_never_mounted`
  - `test_an_argument_that_names_the_setting_in_an_unread_form_is_refused`
  - `test_an_escaped_setting_name_in_toml_1_0_is_read`
  - `test_an_executable_package_that_holds_the_agent_home_is_refused`
  - `test_an_isolated_turn_passes_its_profile_through_the_sandbox_launcher`
  - `test_an_isolated_turn_runs_its_permission_profile_inside_the_sandbox`
  - `test_an_unparseable_config_that_could_spell_the_setting_with_an_escape_is_refused`
  - `test_codex_refuses_an_isolated_request_without_bubblewrap`
  - `test_command_line_overrides_of_the_state_databases_are_parsed_like_codex`
  - `test_every_config_layer_that_moves_the_state_databases_is_checked`
  - `test_isolation_fails_closed_without_bubblewrap`
  - `test_only_the_executable_itself_is_mounted_not_its_directory`
  - `test_short_option_overrides_with_an_equals_sign_are_read_like_clap`
  - `test_the_agent_keeps_its_credentials_and_its_working_directory`
  - `test_the_codex_app_server_launches_inside_the_sandbox`
  - `test_the_sandbox_pins_the_agent_home_and_state_locations`
- [tests/test_chatgpt_plan_provider.py](../../../../../../tests/test_chatgpt_plan_provider.py) — direct import
  - `test_capabilities_isolated_tool_free_and_bounded`
- [tests/test_codex_isolation_mcp_check.py](../../../../../../tests/test_codex_isolation_mcp_check.py) — direct import
  - `test_a_check_the_sandbox_refuses_refuses_the_turn`
  - `test_an_interrupt_stops_a_check_running_inside_the_sandbox`
  - `test_the_check_runs_inside_the_sandbox_in_the_turns_own_directory`
  - `test_the_installed_codex_pins_a_server_only_an_unseen_ancestor_project_disables`
- [tests/test_figures_final_round.py](../../../../../../tests/test_figures_final_round.py) — direct import
- [tests/test_hint_outcome.py](../../../../../../tests/test_hint_outcome.py) — direct import
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_unavailable_offers_openrouter_only_when_configured_and_sends_nothing_unasked`
- [tests/test_reader_digest_narrative.py](../../../../../../tests/test_reader_digest_narrative.py) — direct import
- [tests/text_gap_fakes.py](../../../../../../tests/text_gap_fakes.py) — direct import
- [tests/workbench_help_fakes.py](../../../../../../tests/workbench_help_fakes.py) — direct import

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/isolation.py](../../../../../../src/learnloop/ai/isolation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
