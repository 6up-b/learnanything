---
title: "learnloop.ai.providers.codex_lockdown"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/providers/codex_lockdown.py"
source_paths:
  - "src/learnloop/ai/providers/codex_lockdown.py"
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
  - "learnloop.ai.providers.codex_lockdown module"
  - "src/learnloop/ai/providers/codex_lockdown.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai-providers"
---

# `learnloop.ai.providers.codex_lockdown`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.providers.codex_lockdown` exists within [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] to own the behavior summarized by its module contract: The locked-down Codex turn: no tool that can read, write, run, reach or spawn.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py) |
| Source lines | 1325 |
| Owning package | [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `lockdown_config_overrides() -> list[str]` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 260) — ``-c`` keys (beyond features) that remove tools from every locked-down turn.
- `shell_environment_overrides() -> list[str]` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 286) — ``-c`` keys that give a command only :data:`SHELL_ENVIRONMENT_ALLOWLIST` (Codex review F1).
- `disabled_features(*, shell: bool) -> tuple[str, ...]` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 311)
- `permitted_features(*, shell: bool) -> frozenset[str]` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 315)
- `retired_features_permitted(stages: Mapping[str, str]) -> frozenset[str]` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 319) — The reviewed retired features (:data:`REVIEWED_RETIRED_FEATURES`) ``stages`` lists as ``removed``.
- `feature_violations(states: Mapping[str, bool], *, shell: bool, stages: Mapping[str, str] | None=None) -> list[str]` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 325) — Features ``states`` (``features list``) shows on that a locked-down turn may not have.
- `feature_refusal(left_on: Iterable[str], stages: Mapping[str, str], cli_version: str | None) -> str` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 345) — The launch check's refusal for features that stay on, naming what the owner has to review.
- `cli_version_text(stdout: str) -> str | None` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 375) — ``codex --version``'s first line (``codex-cli 0.164.0``) when it looks like one, else ``None``.
- `unclassified_features_on(states: Mapping[str, bool], *, shell: bool) -> list[str]` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 383) — Features on that this module neither switches off nor permits (a newer CLI's).
- `model_metadata_violations(catalog: Any, model: str | None) -> list[str]` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 437) — What the bundled catalog advertises for ``model`` that no override removes or neutralizes.
- `catalog_pin_override(path: Path | str) -> str` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 493)
- `catalog_pin_path(overrides: Iterable[str]) -> str | None` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 497) — The catalog file a turn's overrides pin (the last ``model_catalog_json``), if any.
- `catalog_violations(validated: Any, effective_stdout: str) -> list[str]` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 511) — Why the catalog the turn would use is not the validated bundled one (empty: it is).
- `tool_free_catalog(bundled_text: str) -> str` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 562) — The bundled catalog (``debug models --bundled``) with every tool removed from every entry.
- `tool_free_violations(catalog: Any, model: str | None) -> list[str]` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 580) — Tool metadata of ``model``'s entry (every entry when empty) that is not :data:`TOOL_FREE_METADATA`.
- `readback_overrides(model: str | None) -> list[str]` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 606)
- `advertised_tool_violations(prompt_input_stdout: str, catalog: Any, model: str | None) -> list[str]` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 621) — Every tool the turn would offer, read back from ``debug prompt-input`` (empty: none).
- `rendered_skills(prompt_input_stdout: str) -> list[tuple[str, str]] | None` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 678) — The skills the turn's context lists, as ``(name, absolute SKILL.md path)``; None when unreadable.
- `skill_disable_overrides(skills: Iterable[tuple[str, str]]) -> list[str]` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 703) — ``-c`` keys that leave a turn no skill: bundled skills off, and every listed skill disabled by name and by path (a later ``-c`` layer's rule beats every config file's, codex-cli 0.163.0 ``skill_config_rules_from_stack``), so no ``$name`` or ``SKILL.md`` link in a prompt can expa…
- `permission_profile_violations(prompt_input_stdout: str, *, root: Path, codex_home: Path) -> list[str]` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 765) — What the turn's effective permission profile allows beyond the lockdown's (empty: nothing).
- `resolve_codex_home(environ: Mapping[str, str], cwd: Path) -> tuple[Path, bool]` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 823) — ``$CODEX_HOME`` as a Codex process started in ``cwd`` with ``environ`` resolves it.
- `resolve_executable(program: str, environ: Mapping[str, str], cwd: Path) -> str` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 854) — The absolute file ``subprocess`` would execute for ``program`` started in ``cwd``.
- `item_kind(item: Any) -> str` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 886) — An SDK turn item's type, lower-cased without ``_``/``-`` (``agentMessage`` -> ``agentmessage``).
- `item_violations(items: Iterable[Any] | None, *, workspace: bool) -> list[str]` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 901) — Kinds of ``items`` a locked-down turn may not produce (fix 4).
- `class CodexLockdownUnavailable(AIProviderUnavailable)` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 927) — The locked-down profile cannot be put in force, so the turn is refused before it starts.
- `class CodexToolUseRefused(AIProviderUnavailable)` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 931) — A locked-down turn used a tool, a sub-agent or an extra request: its answer is refused.
  - `__init__(self, message: str, violations: list[str])` (line 934; internal)
- `class CodexHttpTransportRefused(CodexLockdownUnavailable)` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 939) — The legacy Codex HTTP adapter is refused by the tool lockdown, for every operation (H3).
- `refuse_legacy_http_transport(where: str) -> NoReturn` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 943) — Refuse the legacy endpoint-per-operation Codex HTTP transport (hardening round 2, H3).
- `class TurnLockdown` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 983) — What one locked-down turn did, seen from every app-server message.
  - `_violate(self, what: str) -> None` (line 1009; internal)
  - `handle_server_request(self, method: str, params: dict[str, Any] | None) -> dict[str, Any]` (line 1022; public) — The SDK approval handler: decline everything the model asks for.
  - `observe(self, notification: Any) -> None` (line 1032; public) — One app-server notification (called on the SDK's reader thread).
  - `model_requests(self) -> int` (line 1090; public) — Model requests the SDK reported across every thread (at least 1 once usage arrived).
  - `reported_usage(self) -> bool` (line 1096; public) — Whether the SDK reported any thread's usage during the turn.
  - `child_usage(self) -> list[Any]` (line 1102; public) — The latest cumulative usage of every thread other than the turn's own.
  - `parent_usage(self) -> Any` (line 1108; public)
  - `summary(self) -> dict[str, Any]` (line 1112; public)
- `install_on_sdk(codex: Any, lockdown: TurnLockdown) -> None` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 1124) — Put ``lockdown`` between the SDK client and the app server, or refuse.
- `check_fingerprint(*, command: Iterable[str], root: Path, shell: bool, model: str | None, sandbox_workdir: str | None, environ: Mapping[str, str] | None=None, codex_home: Path | None=None) -> str` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 1181) — What the launch check's verdict depends on, as one key.
- `cached_check(key: str) -> tuple[tuple[str, ...], tuple[str, ...], str, tuple[tuple[str, str], ...]] | None` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 1257) — A passed launch check under ``key``: (servers pinned off, extra features off, pinned catalog, skills off).
- `remember_check(key: str, pinned_servers: Iterable[str], extra_features: Iterable[str], catalog: str, skills: Iterable[tuple[str, str]]=()) -> None` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 1264) — Remember a launch check that passed (a refusal is never cached).
- `clear_check_cache() -> None` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 1272) — Forget every cached launch check (tests; a config change the fingerprint misses).

### Module constants

- `ISOLATED_PROFILE` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 71)
- `LOCKDOWN_DISABLED_FEATURES` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 81)
- `SHELL_FEATURES` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 183)
- `SHELL_ENVIRONMENT_ALLOWLIST` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 190)
- `REQUIRED_OFF_FEATURES` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 195)
- `PERMITTED_FEATURES` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 201)
- `REMOVED_STAGE` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 230)
- `REVIEWED_RETIRED_FEATURES` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 246)
- `_NEUTRALIZED_METADATA` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 394)
- `NEUTRALIZED_EXPERIMENTAL_TOOLS` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 421)
- `_INERT_METADATA` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 423)
- `_TOOLISH_FIELD` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 434)
- `CATALOG_PIN_KEY` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 490)
- `TOOL_FREE_METADATA` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 547)
- `READBACK_OVERRIDES` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 603)
- `_SKILLS_BLOCK` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 673)
- `_SKILL_ROOT` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 674)
- `_SKILL_ENTRY` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 675)
- `_PERMISSION_PROFILE` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 726)
- `_FILE_SYSTEM` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 727)
- `_ENTRY` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 728)
- `_NETWORK_RESTRICTED` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 733)
- `TEXT_ITEMS` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 881)
- `WORKSPACE_ITEMS` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 883)
- `_DECLINES` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 912)
- `_CLIENT_REQUESTS` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 924)
- `_CHECK_CACHE` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 1161)
- `_CHECK_CACHE_LOCK` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 1162)
- `_SYSTEM_LAYERS` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 1164)
- `_HOME_LAYERS` ([src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 1165)

### Explicit exports

`__all__` declares:

- `READBACK_OVERRIDES`
- `TOOL_FREE_METADATA`
- `advertised_tool_violations`
- `readback_overrides`
- `rendered_skills`
- `skill_disable_overrides`
- `tool_free_catalog`
- `tool_free_violations`
- `CATALOG_PIN_KEY`
- `CodexHttpTransportRefused`
- `CodexLockdownUnavailable`
- `CodexToolUseRefused`
- `ISOLATED_PROFILE`
- `LOCKDOWN_DISABLED_FEATURES`
- `PERMITTED_FEATURES`
- `REMOVED_STAGE`
- `REQUIRED_OFF_FEATURES`
- `REVIEWED_RETIRED_FEATURES`
- `SHELL_ENVIRONMENT_ALLOWLIST`
- `SHELL_FEATURES`
- `TEXT_ITEMS`
- `TurnLockdown`
- `WORKSPACE_ITEMS`
- `catalog_pin_override`
- `catalog_pin_path`
- `catalog_violations`
- `check_fingerprint`
- `clear_check_cache`
- `cli_version_text`
- `disabled_features`
- `feature_refusal`
- `feature_violations`
- `install_on_sdk`
- `item_kind`
- `item_violations`
- `lockdown_config_overrides`
- `model_metadata_violations`
- `permission_profile_violations`
- `permitted_features`
- `refuse_legacy_http_transport`
- `resolve_codex_home`
- `resolve_executable`
- `retired_features_permitted`
- `shell_environment_overrides`
- `unclassified_features_on`

## Internal implementation anchors

- `_hashable(value: Any) -> bool` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 470)
- `_prompt_items(prompt_input_stdout: str) -> list[Any] | None` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 613)
- `_tool_names(tools: Any) -> list[str]` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 659)
- `_message_texts(prompt_input: Any) -> list[str]` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 736)
- `_attribute(attributes: str, name: str) -> str | None` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 746)
- `_is_codex_helper(path: Path, codex_homes: Iterable[Path]) -> bool` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 751) — Codex's own read root for its re-exec helpers: ``$CODEX_HOME/tmp/arg0*/codex-arg0*``.
- `_field(payload: Any, *names: str) -> Any` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 962)
- `_tokens(breakdown: Any, *names: str) -> int` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 975)
- `_stat_signature(path: Path) -> tuple[Any, ...]` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 1168) — Identity of a file or directory without opening it (it may hold credentials).
- `_skill_roots(environ: Mapping[str, str]) -> list[Path]` ([source](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py), line 1247) — Skill roots outside ``$CODEX_HOME`` that codex-cli 0.163.0 discovers (``ext/skills`` ``host_roots``).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `module`; statically calls `refuse_legacy_http_transport`
- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `CodexHttpTransportRefused`, `CodexLockdownUnavailable`, `CodexToolUseRefused`, `ISOLATED_PROFILE`, `LOCKDOWN_DISABLED_FEATURES`, `TurnLockdown`, `advertised_tool_violations`, `cached_check`, `catalog_pin_override`, `catalog_pin_path`, `catalog_violations`, `check_fingerprint`, `cli_version_text`, `disabled_features`, `feature_refusal`, `feature_violations`, `install_on_sdk`, `item_violations`, `lockdown_config_overrides`, `model_metadata_violations`, `module`, `permission_profile_violations`, `readback_overrides`, `remember_check`, `rendered_skills`, `resolve_codex_home`, `resolve_executable`, `shell_environment_overrides`, `skill_disable_overrides`, `tool_free_catalog`, `tool_free_violations`, `unclassified_features_on`; statically calls `CodexLockdownUnavailable`, `CodexToolUseRefused`, `TurnLockdown`, `advertised_tool_violations`, `cached_check`, `catalog_pin_override`, `catalog_pin_path`, `catalog_violations`, `check_fingerprint`, `cli_version_text`, `disabled_features`, `feature_refusal`, `feature_violations`, `install_on_sdk`, `item_violations`, `lockdown_config_overrides`, `model_metadata_violations`, `permission_profile_violations`, `readback_overrides`, `refuse_legacy_http_transport`, `remember_check`, `rendered_skills`, `resolve_codex_home`, `resolve_executable`, `shell_environment_overrides`, `skill_disable_overrides`, `tool_free_catalog`, `tool_free_violations`, `unclassified_features_on`
- [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]] — imports `module`; statically calls `refuse_legacy_http_transport`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/boundary|learnloop.experiments.contextual_embeddings.boundary]] — imports `module`; statically calls `disabled_features`, `lockdown_config_overrides`, `shell_environment_overrides`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `html`, `json`, `os`, `pathlib`, `re`, `secrets`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]], [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]], [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/boundary|learnloop.experiments.contextual_embeddings.boundary]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/conftest.py](../../../../../../../tests/conftest.py) — direct import
- [tests/test_codex_cli_0164_lockdown.py](../../../../../../../tests/test_codex_cli_0164_lockdown.py) — direct import
  - `test_a_core_feature_reported_removed_and_on_still_refuses`
  - `test_a_newer_cli_s_retired_unreviewed_feature_refuses_and_names_what_to_review`
  - `test_a_retired_flag_may_read_on_only_at_stage_removed`
  - `test_a_reviewed_flag_left_on_at_another_stage_refuses_the_turn`
  - `test_a_version_probe_that_fails_still_refuses_with_the_features_named`
  - `test_an_unreviewed_feature_at_stage_removed_still_refuses`
  - `test_only_a_version_shaped_line_reaches_the_message`
  - `test_the_refusal_names_the_version_the_stages_and_where_to_classify`
  - `test_the_reviewed_retired_features_are_exactly_the_two_0164_flags`
- [tests/test_codex_cli_0165_lockdown.py](../../../../../../../tests/test_codex_cli_0165_lockdown.py) — direct import
  - `test_a_0165_cli_with_an_unknown_new_feature_left_on_still_refuses`
  - `test_a_0165_feature_whose_switch_is_ignored_refuses_the_turn`
  - `test_bundled_skills_no_switch_removes_refuse_the_turn`
  - `test_every_launch_sends_both_switches_and_the_bundled_skills_switch`
  - `test_the_0165_defaults_are_switched_off_and_never_tolerated`
- [tests/test_codex_cli_0166_lockdown.py](../../../../../../../tests/test_codex_cli_0166_lockdown.py) — direct import
  - `test_a_0166_cli_with_an_unknown_new_feature_left_on_still_refuses`
  - `test_a_0166_feature_whose_switch_is_ignored_refuses_the_turn`
  - `test_a_cli_that_keeps_plugins_on_refuses_the_turn_whatever_the_prefetch_says`
  - `test_the_0166_features_are_switched_off_and_never_tolerated`
  - `test_the_flag_0166_retired_is_not_classified_and_a_layer_cannot_leave_it_on`
  - `test_the_flag_0166_retired_left_on_with_its_switch_ignored_refuses`
  - `test_the_prefetch_retired_later_with_its_switch_ignored_still_refuses`
  - `test_the_real_lock_on_plugin_startup_stays_required`
- [tests/test_codex_isolation_mcp_check.py](../../../../../../../tests/test_codex_isolation_mcp_check.py) — direct import
  - `test_a_read_only_workspace_turn_is_checked_under_its_own_overrides`
  - `test_a_turn_that_did_not_ask_for_isolation_is_checked_and_locked_down_too`
  - `test_configuration_flags_after_app_server_are_checked_and_launched_as_one_set`
  - `test_plugin_servers_are_disabled_by_feature_and_config_servers_by_name`
  - `test_the_check_runs_inside_the_sandbox_in_the_turns_own_directory`
  - `test_the_installed_codex_passes_the_launch_check`
  - `test_without_servers_the_first_listing_is_the_check`
- [tests/test_codex_lockdown_round2.py](../../../../../../../tests/test_codex_lockdown_round2.py) — direct import
  - `test_a_layer_that_names_the_turns_profile_is_caught_by_the_readback`
  - `test_every_legacy_operation_is_refused_even_on_an_existing_client`
  - `test_the_launch_check_refuses_a_widened_profile_before_any_turn`
- [tests/test_codex_lockdown_round3.py](../../../../../../../tests/test_codex_lockdown_round3.py) — direct import
- [tests/test_codex_tool_lockdown.py](../../../../../../../tests/test_codex_tool_lockdown.py) — direct import
  - `test_a_tool_bearing_feature_the_cli_leaves_on_refuses_the_turn`
  - `test_every_request_runs_the_locked_down_profile_with_approvals_denied`
- [tests/test_diagnosis_isolation.py](../../../../../../../tests/test_diagnosis_isolation.py) — direct import
  - `test_a_snapshot_turn_runs_under_the_profile_never_the_builtin_sandbox`
  - `test_a_turn_that_did_not_ask_for_isolation_never_starts_in_the_vault`
  - `test_an_isolated_turn_without_a_workspace_starts_in_an_empty_directory`
  - `test_configured_mcp_servers_are_listed_and_disabled`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/providers/codex_lockdown.py](../../../../../../../src/learnloop/ai/providers/codex_lockdown.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
