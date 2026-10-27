"""The locked-down Codex turn: no tool that can read, write, run, reach or spawn.

Security stage 2026-10-21 (docs/reviews/security-codex-tool-lockdown.md). Every
turn LearnLoop starts on the Codex SDK runs this one profile. Its pieces, each
pure here and wired in by :mod:`learnloop.ai.providers.codex`:

* **configuration** (:func:`lockdown_config_overrides`): the ``-c`` keys that
  switch off sub-agents, user-input and plan tools and web search, on top of
  the permission profile and feature switches of the isolated turn;
* **command environment** (:func:`shell_environment_overrides`): a workspace
  command sees only :data:`SHELL_ENVIRONMENT_ALLOWLIST`, never the API keys in
  the environment the app server inherits from this process;
* **features** (:func:`feature_violations`): what ``codex features list`` may
  still report on. Only the reviewed non-tool features of codex-cli 0.163.0
  (:data:`PERMITTED_FEATURES`), and the reviewed flags codex-cli 0.164.0
  retired (:data:`REVIEWED_RETIRED_FEATURES`, only at stage ``removed``); any
  other feature reported on is switched off by the caller and must then read
  off, or the turn is refused, naming the CLI version (:func:`feature_refusal`);
* **model metadata** (:func:`model_metadata_violations`): what ``codex debug
  models --bundled`` (the catalog in the binary: no network, no model call)
  advertises for the turn's model. A tool the configuration removes or
  neutralizes passes; anything else refuses the turn;
* **approvals** (:class:`TurnLockdown.handle_server_request`): every request the
  app server sends the client (command, file change, permissions, user input,
  MCP elicitation, dynamic tool call) is declined and recorded;
* **what the turn did** (:class:`TurnLockdown`, :func:`item_violations`): every
  notification of the app server is observed. Any tool item, sub-agent thread,
  Guardian review or second model request of a locked-down turn is a
  violation: the turn is stopped and its answer refused, never returned.
  Tokens of every thread are counted.

Tool-free by construction (hardening round 3, 2026-10-21; the investigation's
fix 5, built): codex-cli 0.163.0 takes ``apply_patch`` and code mode
(``exec``/``wait``) from the model's catalog entry, not from any feature, so
LearnLoop owns the catalog. Every turn is pinned (``model_catalog_json``) to
the validated bundled catalog with every tool removed from every entry
(:data:`TOOL_FREE_METADATA`, :func:`tool_free_catalog`); the model's
instructions and other metadata are the bundled ones. The launch check reads
the turn back: ``debug models`` must return exactly that catalog, and ``debug
prompt-input`` in incremental form (:data:`READBACK_OVERRIDES`) must declare no
tool, list no skill (:func:`skill_disable_overrides`) and show the permission
profile. No route keeps a shell: a read-only workspace (the snapshot
diagnosis) is inlined into the prompt by the transport. With no tool there is
no tool call and no continuation; the item checks, the request count and the
early stop stay as a backstop.
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import secrets
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, NoReturn

from learnloop.ai.errors import AIProviderUnavailable

#: The permission profile every locked-down turn runs under: a name of
#: LearnLoop's own, fresh in every process (hardening round 2, H1). Codex
#: merges ``permissions.<name>`` tables recursively across its layers and
#: honours a lower layer's ``extends``, so a fixed name let any user, profile
#: or project layer that defined it (``extends = ":read-only"``, an extra read
#: or write root) widen the turn's sandbox, and no ``-c`` can delete a key. No
#: layer can name this one, and the launch check reads the effective profile
#: back before any turn (:func:`permission_profile_violations`).
ISOLATED_PROFILE = f"learnloop_isolated_turn_{secrets.token_hex(8)}"

#: Tools and integrations that run outside the command sandbox, bring outside
#: context, or offer the model a tool, all off in every locked-down turn
#: (codex-cli 0.163.0 ``features list``; each key checked to take effect under
#: ``-c features.<key>=false``; 0.164.0's three new defaults checked the same
#: way, 2026-10-27). Unknown keys are ignored by Codex, and so are retired ones
#: (:data:`REVIEWED_RETIRED_FEATURES`).
LOCKDOWN_DISABLED_FEATURES = (
    "apps",
    "auth_elicitation",
    "agent_message_board",
    "artifact",
    # codex-cli 0.164.0, on by default (2026-10-27): Amazon Bedrock sign-in
    # onboarding in the TUI; no turn needs it.
    "bedrock_setup_wizard",
    "browser_annotation_api",
    "browser_use",
    "browser_use_external",
    "browser_use_full_cdp_access",
    "chronicle",
    "code_mode",
    "code_mode_only",
    "computer_use",
    "default_mode_request_user_input",
    "enable_mcp_apps",
    "exec_permission_approvals",
    "goals",
    "guardian_approval",
    "guardianv2",
    "hooks",
    "image_generation",
    "in_app_browser",
    "in_app_chat",
    "in_app_dictation",
    "in_app_local_automation",
    "in_app_updates",
    "in_app_voice",
    # codex-cli 0.164.0, on by default: tool definitions sent as incremental
    # context updates. Off keeps the turn's tool declaration as on 0.163.0;
    # the readback still renders it on (READBACK_OVERRIDES), to list every tool.
    "incremental_tools",
    # codex-cli 0.164.0, on by default: OAuth refresh for MCP servers, none of
    # which an isolated turn has.
    "mcp_oauth_refresh_coordination",
    "memories",
    "multi_agent",
    "multi_agent_v2",
    "multi_agent_v2_dynamic_tools",
    "network_proxy",
    "plugin_sharing",
    "plugins",
    "realtime_conversation",
    "remote_plugin",
    "request_permissions_tool",
    "send_message_to_user_async",
    # Off in workspace turns too (Codex review F1, 2026-10-21): a snapshot
    # replays the user's login-shell environment into every command.
    "shell_snapshot",
    "skill_mcp_dependency_install",
    "skill_search",
    "sleep_tool",
    "standalone_web_search",
    "tool_call_mcp_elicitation",
    "tool_suggest",
    "view_image",
    "workspace_dependencies",
    "worktrees",
)
#: The command tools. Off unless the turn has a read-only workspace (the
#: snapshot diagnosis), whose shell reads it under the permission profile.
SHELL_FEATURES = ("shell_tool", "unified_exec", "unified_exec_tty")
#: The only variables a workspace command may see (Codex review F1, 2026-10-21).
#: The SDK starts the app server with this process's whole environment, which
#: holds the API keys LearnLoop loaded, and codex-cli 0.163.0's default policy
#: (``inherit = "all"``, default excludes ignored) hands all of it to every
#: command: a prompt-injected ``printenv`` would read them. Codex's "core" set
#: for Unix: paths and locale, no credential.
SHELL_ENVIRONMENT_ALLOWLIST = (
    "PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "TEMP", "TMP", "SHELL", "USER", "LOGNAME",
)
#: Must be listed by ``features list`` and read off: the CLI is expected to
#: know these, so a missing row means a renamed key, not an absent feature.
REQUIRED_OFF_FEATURES = ("apps", "plugins", "multi_agent")
#: Features ``features list`` may report on in a locked-down turn: none offers
#: the model a tool or reaches outside the turn (reviewed on codex-cli 0.163.0,
#: 2026-10-21). ``removed`` flags are inert; ``unified_exec`` ignores its
#: ``-c`` override (only managed requirements disable it) and has no tool
#: without ``shell_tool``; ``write_stdin_approval`` only adds an approval.
PERMITTED_FEATURES = frozenset({
    "api_key_cyber_access_programs",
    "api_key_model_discovery",
    "cli_daybreak",
    "code_mode_host",
    "code_mode_interrupt",
    "collaboration_modes",
    "compaction_image_budget",
    "content_item_kinds",
    "daemon_auto_start",
    "enable_request_compression",
    "fast_mode",
    "guardian_reuse_parent_compaction",
    "instant_interrupt",
    "item_ids",
    "mentions_v2",
    "resize_all_images",
    "sqlite",
    "steer",
    "system_proxy_fallback",
    "terminal_resize_reflow",
    "tool_search_always_defer_mcp_tools",
    "tui_app_server",
    "ultrafast_mode",
    "unbounded_connection_retries",
    "unified_exec",
    "write_stdin_approval",
})
#: The stage ``codex features list`` prints for a retired flag.
REMOVED_STAGE = "removed"
#: Switched-off features Codex has since retired, reviewed one by one: on a
#: CLI that lists one at stage ``removed`` it may read on, because Codex no
#: longer reads its switch and what it once gated offers this turn nothing.
#: On any other stage it must read off like the rest of
#: :data:`LOCKDOWN_DISABLED_FEATURES` (where each stays, for the CLIs whose
#: switch still works, 0.163.0 among them). An unreviewed feature reported on
#: at stage ``removed`` still refuses the turn: retired is no review.
#:
#: Reviewed on codex-cli 0.164.0 (2026-10-27, docs/reviews/codex-cli-0164-lockdown.md):
#: ``features/src/lib.rs`` ``Features::apply_map`` skips both keys
#: (``"tui_app_server" | "worktrees" | "realtime_conversation" => continue``),
#: so ``-c features.<key>=false`` and ``--disable`` cannot change them, and no
#: code reads ``Feature::Worktrees`` or ``Feature::RealtimeConversation``.
REVIEWED_RETIRED_FEATURES: dict[str, str] = {
    "realtime_conversation": (
        "voice sessions start only on a client's thread/realtime/start request, which LearnLoop's client never "
        "sends; the turn's model gets no realtime tool (the prompt-input readback declares none)"
    ),
    "worktrees": (
        "the managed-worktree tools (create_worktree, list_worktrees, get_worktree_creation_status) are dynamic "
        "tools the TUI registers as a client; LearnLoop registers none, declines every dynamic tool call, and the "
        "prompt-input readback declares no tool"
    ),
}


def lockdown_config_overrides() -> list[str]:
    """``-c`` keys (beyond features) that remove tools from every locked-down turn.

    In codex-cli 0.163.0 ``agents.enabled=false`` is what removes sub-agents:
    ``multi_agent_version_for_model`` takes it before the model's own
    ``multi_agent_version`` (``features.multi_agent`` does not govern v2), as
    long as ``features.multi_agent_v2`` is off. ``request_user_input`` is on by
    default; ``update_plan`` is off by default and pinned off here.

    ``notify=[]`` (frozen round, verify uuB5X5 High 3): a legacy ``notify``
    command inherited from any layer runs after every turn with the turn's
    input messages and answer, unsandboxed and with the app server's whole
    environment (codex-cli 0.163.0 ``hooks/src/legacy_notify.rs``), whatever
    ``features.hooks`` says. An empty argv registers no command, and arrays
    replace lower layers' wholesale.
    """

    return [
        "agents.enabled=false",
        "tools.experimental_request_user_input.enabled=false",
        "tools.update_plan.enabled=false",
        "tools.web_search=false",
        "notify=[]",
    ]


def shell_environment_overrides() -> list[str]:
    """``-c`` keys that give a command only :data:`SHELL_ENVIRONMENT_ALLOWLIST` (Codex review F1).

    Codex builds a command's environment (``protocol/src/shell_environment.rs``
    ``populate_env``, codex-cli 0.163.0) as: the ``inherit`` set, minus the
    ``*KEY*``/``*SECRET*``/``*TOKEN*`` default excludes unless ignored, minus
    ``exclude``, plus ``set``, then only names matching ``include_only``. So
    ``inherit = "core"`` drops what the app server inherited, the default
    excludes go back on, and ``include_only`` (applied after ``set``) drops any
    ``set`` entry a user's config adds under another name. A legacy
    ``include_only`` here also displaces a lower layer's ``filters`` table
    (``config/src/merge.rs``), so a config ``"*KEY*" = "include"`` filter
    cannot widen it, and an ``include_only`` of the user's is replaced
    wholesale (arrays are). ``experimental_use_profile=false`` keeps commands
    from sourcing the login profile; ``features.shell_snapshot`` is off for
    the same reason (:data:`LOCKDOWN_DISABLED_FEATURES`)."""

    return [
        'shell_environment_policy.inherit="core"',
        "shell_environment_policy.ignore_default_excludes=false",
        f"shell_environment_policy.include_only={json.dumps(list(SHELL_ENVIRONMENT_ALLOWLIST))}",
        "shell_environment_policy.experimental_use_profile=false",
    ]


def disabled_features(*, shell: bool) -> tuple[str, ...]:
    return LOCKDOWN_DISABLED_FEATURES + (() if shell else SHELL_FEATURES)


def permitted_features(*, shell: bool) -> frozenset[str]:
    return PERMITTED_FEATURES | (frozenset(SHELL_FEATURES) if shell else frozenset())


def retired_features_permitted(stages: Mapping[str, str]) -> frozenset[str]:
    """The reviewed retired features (:data:`REVIEWED_RETIRED_FEATURES`) ``stages`` lists as ``removed``."""

    return frozenset(feature for feature in REVIEWED_RETIRED_FEATURES if stages.get(feature) == REMOVED_STAGE)


def feature_violations(
    states: Mapping[str, bool], *, shell: bool, stages: Mapping[str, str] | None = None,
) -> list[str]:
    """Features ``states`` (``features list``) shows on that a locked-down turn may not have.

    A feature this list switches off, or one the CLI requires to know
    (:data:`REQUIRED_OFF_FEATURES`), that does not read exactly ``false``; and
    any feature on that is not permitted (:func:`permitted_features`). A
    reviewed retired feature may read on only where ``stages`` (the same
    listing's stage column) says ``removed``; without stages, none may."""

    allowed = permitted_features(shell=shell) | retired_features_permitted(stages or {})
    named = [feature for feature in REQUIRED_OFF_FEATURES if states.get(feature) is not False]
    # Everything else on must be permitted. ``unified_exec`` is switched off
    # and permitted at once: codex-cli 0.163.0 ignores its override, and it
    # offers no tool without ``shell_tool`` (which must read off).
    named += sorted(feature for feature, on in states.items() if on and feature not in allowed and feature not in named)
    return named


def feature_refusal(left_on: Iterable[str], stages: Mapping[str, str], cli_version: str | None) -> str:
    """The launch check's refusal for features that stay on, naming what the owner has to review.

    Fail closed and nothing more: it names the CLI version, each feature with
    the stage the CLI reports, and where a feature is classified; it never
    tolerates one."""

    names = list(left_on)
    shown = ", ".join(f"{name} ({stages[name]})" if stages.get(name) else name for name in names)
    message = (
        f"Codex ({cli_version or 'version unknown'}) does not report feature {shown} off under the isolated "
        "turn's overrides (a tool, connector, plugin or sub-agent could load); refusing the isolated turn."
    )
    retired = [name for name in names if stages.get(name) == REMOVED_STAGE]
    if retired:
        message += (
            f" Codex no longer reads the switch of a removed feature ({', '.join(retired)}), so no override "
            "turns it off."
        )
    unreviewed = [name for name in names if name not in REQUIRED_OFF_FEATURES]
    if unreviewed:
        message += (
            f" Isolated Codex turns stay refused on this CLI until {', '.join(unreviewed)} "
            f"{'is' if len(unreviewed) == 1 else 'are'} reviewed for it and classified in "
            "learnloop/ai/providers/codex_lockdown.py (PERMITTED_FEATURES for a non-tool feature, "
            "REVIEWED_RETIRED_FEATURES for a removed flag that offers the turn nothing)."
        )
    return message


def cli_version_text(stdout: str) -> str | None:
    """``codex --version``'s first line (``codex-cli 0.164.0``) when it looks like one, else ``None``."""

    lines = (stdout or "").strip().splitlines()
    line = lines[0].strip() if lines else ""
    return line if re.fullmatch(r"[\w.+-]{1,40} [\w.+-]{1,40}", line) else None


def unclassified_features_on(states: Mapping[str, bool], *, shell: bool) -> list[str]:
    """Features on that this module neither switches off nor permits (a newer CLI's)."""

    known = set(disabled_features(shell=shell)) | permitted_features(shell=shell)
    return sorted(feature for feature, on in states.items() if on and feature not in known)


# -- model metadata (codex debug models --bundled) ----------------------------------

#: How each tool-bearing metadata field of a catalog entry is handled, with the
#: values it may take. A value outside its set refuses the turn.
_NEUTRALIZED_METADATA: dict[str, tuple[frozenset[Any], str]] = {
    "tool_mode": (
        frozenset({None, "direct", "code_mode", "code_mode_only"}),
        "code mode's exec/wait dispatch only the tools left on (V8 with no file or network access); "
        "every round trip is a second model request, which refuses the turn",
    ),
    "apply_patch_tool_type": (
        frozenset({None, "freeform", "function"}),
        "the permission profile has no writable root, approvals are never and every file change is declined; "
        "a patch item refuses the turn",
    ),
    "multi_agent_version": (
        frozenset({None, "disabled", "v1", "v2"}),
        "removed by agents.enabled=false with features.multi_agent_v2 off",
    ),
    "shell_type": (
        frozenset({None, "default", "local", "unified_exec", "shell_command", "disabled"}),
        "governed by features.shell_tool (off) or, in a workspace turn, the read-only permission profile",
    ),
    "web_search_tool_type": (
        frozenset({None, "text", "text_and_image"}),
        "web_search=\"disabled\" and tools.web_search=false",
    ),
    "supports_search_tool": (frozenset({None, False, True}), "web search is disabled"),
}
#: Model-listed experimental tools that do no I/O (a clock read, a message to
#: the client); a call is still a tool item or second request, refusing the turn.
NEUTRALIZED_EXPERIMENTAL_TOOLS = frozenset({"clock", "send_user_message_async"})
#: Catalog fields that only shape instructions or turn metadata, never a tool.
_INERT_METADATA = frozenset({
    "include_apps_usage_instructions",
    "include_plugin_usage_instructions",
    "include_skills_usage_instructions",
    "multi_agent_reasoning_effort",
    "node_repl_auto_review_required",
    "node_repl_disabled",
    "supports_image_detail_original",
})
#: A catalog field name that may describe a tool. One this module does not
#: know, with a set value, refuses the turn (a newer CLI's tool).
_TOOLISH_FIELD = re.compile(r"tool|agent|repl|exec|shell|search|browser|computer|mcp|plugin|patch|skill|connector|apps?_")


def model_metadata_violations(catalog: Any, model: str | None) -> list[str]:
    """What the bundled catalog advertises for ``model`` that no override removes or neutralizes.

    ``model`` empty means Codex's default model: every entry is checked. A
    model the catalog does not list cannot be checked and refuses the turn."""

    entries = catalog.get("models") if isinstance(catalog, dict) else None
    if not isinstance(entries, list):
        return ["`codex debug models --bundled` did not return a model catalog"]
    slug = (model or "").strip()
    chosen = [entry for entry in entries if isinstance(entry, dict) and (not slug or entry.get("slug") == slug)]
    if not chosen:
        return [f"model {slug!r} is not in the bundled catalog, so its tools cannot be checked"]
    problems: list[str] = []
    for entry in chosen:
        name = entry.get("slug")
        for key, value in entry.items():
            if key in _NEUTRALIZED_METADATA:
                allowed, _why = _NEUTRALIZED_METADATA[key]
                if not _hashable(value) or value not in allowed:
                    problems.append(f"{name}: {key}={value!r}")
            elif key == "experimental_supported_tools":
                tools = value if isinstance(value, list) else [value]
                unknown = [tool for tool in tools if tool not in NEUTRALIZED_EXPERIMENTAL_TOOLS]
                if value is not None and (not isinstance(value, list) or unknown):
                    problems.append(f"{name}: experimental_supported_tools={unknown or value!r}")
            elif key in _INERT_METADATA:
                continue
            elif _TOOLISH_FIELD.search(key) and value not in (None, False, "", [], {}):
                problems.append(f"{name}: {key}={value!r} (a tool field this check does not know)")
    return problems


def _hashable(value: Any) -> bool:
    try:
        hash(value)
    except TypeError:
        return False
    return True


# -- the model catalog the turn uses (hardening round 2, H4) ---------------------------

#: The app server's catalog is the bundled one only when nothing replaces it:
#: a ``model_catalog_json`` in any layer, or (without one) the remote catalog
#: Codex refreshes and caches in ``$CODEX_HOME``, can give the same model slug
#: other tool metadata (``experimental_supported_tools`` naming a tool the
#: CLI implements). The launch check validates ``debug models --bundled``,
#: writes exactly that output to a file of LearnLoop's, and pins every turn to
#: it with ``model_catalog_json``: codex-cli 0.163.0 then serves a static,
#: authoritative catalog (``StaticModelsManager``: no refresh, no cache). A
#: layer that beats the pin shows in ``debug models`` (no ``--bundled``)
#: under the turn's overrides, which must return the validated catalog.
CATALOG_PIN_KEY = "model_catalog_json"


def catalog_pin_override(path: Path | str) -> str:
    return f"{CATALOG_PIN_KEY}={json.dumps(str(path), ensure_ascii=False)}"


def catalog_pin_path(overrides: Iterable[str]) -> str | None:
    """The catalog file a turn's overrides pin (the last ``model_catalog_json``), if any."""

    pinned = None
    for override in overrides:
        key, _sep, value = override.partition("=")
        if key.strip() == CATALOG_PIN_KEY:
            try:
                pinned = json.loads(value)
            except ValueError:
                pinned = value
    return pinned if isinstance(pinned, str) else None


def catalog_violations(validated: Any, effective_stdout: str) -> list[str]:
    """Why the catalog the turn would use is not the validated bundled one (empty: it is)."""

    try:
        effective = json.loads(effective_stdout)
    except ValueError:
        return ["`codex debug models` under the turn's overrides did not return a model catalog"]
    if effective == validated:
        return []

    def tools(catalog: Any) -> dict[Any, Any]:
        entries = catalog.get("models") if isinstance(catalog, dict) else None
        return {entry.get("slug"): entry.get("experimental_supported_tools")
                for entry in entries or () if isinstance(entry, dict)}

    changed = sorted(str(slug) for slug, value in tools(effective).items() if tools(validated).get(slug) != value)
    detail = f" (experimental tools differ for {', '.join(changed)})" if changed else ""
    return [
        "the model catalog the turn would use is not the catalog the launch check pinned (the validated bundled "
        "catalog with every tool removed): a configuration layer replaces it (model_catalog_json, a remote or "
        f"cached catalog){detail}"
    ]


# -- tool-free by construction (hardening round 3) --------------------------------------

#: The catalog values that give a model no tool at all in codex-cli 0.163.0
#: (``protocol/src/openai_models.rs`` ``ModelInfo``; ``core/src/tools``):
#: ``tool_mode = direct`` (no code mode: ``requested_tool_mode`` takes the
#: entry's value before any feature), no ``apply_patch``, ``shell_type =
#: disabled``, no experimental tools, no tool search, sub-agents disabled, no
#: Node REPL, and no usage instructions for skills, plugins or apps. Every
#: other tool source is switched off by configuration
#: (:data:`LOCKDOWN_DISABLED_FEATURES`, :func:`lockdown_config_overrides`). The
#: catalog LearnLoop pins every turn to is the bundled one with these values
#: in every entry; its instructions and other metadata are the bundled ones.
TOOL_FREE_METADATA: dict[str, Any] = {
    "tool_mode": "direct",
    "apply_patch_tool_type": None,
    "shell_type": "disabled",
    "experimental_supported_tools": [],
    "supports_search_tool": False,
    "multi_agent_version": "disabled",
    "node_repl_disabled": True,
    "node_repl_auto_review_required": False,
    "include_skills_usage_instructions": False,
    "include_plugin_usage_instructions": False,
    "include_apps_usage_instructions": False,
}


def tool_free_catalog(bundled_text: str) -> str:
    """The bundled catalog (``debug models --bundled``) with every tool removed from every entry."""

    try:
        catalog = json.loads(bundled_text)
    except ValueError:
        catalog = None
    entries = catalog.get("models") if isinstance(catalog, dict) else None
    if not isinstance(entries, list) or not entries or not all(isinstance(entry, dict) for entry in entries):
        raise CodexLockdownUnavailable(
            "`codex debug models --bundled` did not return a model catalog to remove the tools from; "
            "refusing the isolated turn."
        )
    for entry in entries:
        entry.update(TOOL_FREE_METADATA)
    return json.dumps(catalog, ensure_ascii=False, sort_keys=True)


def tool_free_violations(catalog: Any, model: str | None) -> list[str]:
    """Tool metadata of ``model``'s entry (every entry when empty) that is not :data:`TOOL_FREE_METADATA`."""

    entries = catalog.get("models") if isinstance(catalog, dict) else None
    if not isinstance(entries, list):
        return ["the pinned catalog is not a model catalog"]
    slug = (model or "").strip()
    chosen = [entry for entry in entries if isinstance(entry, dict) and (not slug or entry.get("slug") == slug)]
    if not chosen:
        return [f"model {slug!r} is not in the pinned catalog"]
    return [f"{entry.get('slug')}: {key}={entry.get(key, '<absent>')!r}"
            for entry in chosen for key, value in TOOL_FREE_METADATA.items()
            if key not in entry or entry[key] != value]


#: Probe-only overrides of ``debug prompt-input`` (hardening round 3): with
#: ``incremental_tools`` codex-cli 0.163.0 declares the model-visible tools as
#: an ``additional_tools`` input item and moves the base instructions into the
#: input, so the rendered input shows every tool the turn would offer, with
#: no model request (``core/src/session/turn.rs`` ``build_prompt``). Only for
#: models served through Responses Lite; for any other the tool list cannot be
#: read back and the turn is refused. ``skills.max_context_tokens`` lets the
#: skills catalog render in full, so every skill can be named and disabled.
READBACK_OVERRIDES = ("features.incremental_tools=true", "skills.max_context_tokens=10000")


def readback_overrides(model: str | None) -> list[str]:
    overrides = list(READBACK_OVERRIDES)
    if (model or "").strip():
        overrides.append(f"model={json.dumps(model.strip())}")
    return overrides


def _prompt_items(prompt_input_stdout: str) -> list[Any] | None:
    try:
        items = json.loads(prompt_input_stdout)
    except ValueError:
        return None
    return items if isinstance(items, list) else None


def advertised_tool_violations(prompt_input_stdout: str, catalog: Any, model: str | None) -> list[str]:
    """Every tool the turn would offer, read back from ``debug prompt-input`` (empty: none).

    ``prompt_input_stdout`` is rendered with :func:`readback_overrides`. The
    read-back counts only when it is in incremental form, which shows as the
    first developer message being exactly the model's ``base_instructions``
    from ``catalog`` (the pinned one); otherwise the tools were not rendered
    and cannot be checked, which refuses too."""

    items = _prompt_items(prompt_input_stdout)
    if items is None:
        return ["`codex debug prompt-input` did not return the turn's prompt input"]
    entries = catalog.get("models") if isinstance(catalog, dict) else None
    slug = (model or "").strip()
    instructions = {entry.get("base_instructions") for entry in entries or ()
                    if isinstance(entry, dict) and (not slug or entry.get("slug") == slug)
                    and entry.get("use_responses_lite") is True and isinstance(entry.get("base_instructions"), str)}
    problems: list[str] = []
    first = next((item for item in items if isinstance(item, dict) and item.get("type") == "message"), None)
    first_text = "".join(content.get("text", "") for content in (first or {}).get("content") or ()
                         if isinstance(content, dict))
    if first is None or first.get("role") != "developer" or first_text not in instructions:
        problems.append(
            "the turn's tools could not be read back (no incremental rendering: the model is not served through "
            "Responses Lite, or its instructions are not the pinned catalog's)"
        )
    for item in items:
        kind = item.get("type") if isinstance(item, dict) else None
        if kind == "additional_tools":
            names = _tool_names(item.get("tools"))
            if names or item.get("tools"):
                listed = ", ".join(names) or repr(item.get("tools"))
                problems.append(f"the turn would offer tools: {listed}")
        elif kind != "message":
            problems.append(f"an input item of type {kind!r} this check does not know")
    return problems


def _tool_names(tools: Any) -> list[str]:
    names: list[str] = []
    for tool in tools if isinstance(tools, list) else ():
        if not isinstance(tool, dict):
            names.append(repr(tool))
            continue
        nested = tool.get("tools")
        if isinstance(nested, list) and nested:
            names += [f"{tool.get('name')}.{name}" for name in _tool_names(nested)]
        else:
            names.append(str(tool.get("name") or tool.get("type")))
    return names


_SKILLS_BLOCK = re.compile(r"<skills_instructions>(.*?)</skills_instructions>", re.S)
_SKILL_ROOT = re.compile(r"^- `(r\d+)` = `([^`]+)`\s*$", re.M)
_SKILL_ENTRY = re.compile(r"^- ([^:\n]+?): .*?\(file: (r\d+)/([^)\n]+)\)\s*$", re.M)


def rendered_skills(prompt_input_stdout: str) -> list[tuple[str, str]] | None:
    """The skills the turn's context lists, as ``(name, absolute SKILL.md path)``; None when unreadable.

    A ``<skills_instructions>`` block whose entries this parser cannot read
    returns None too (the caller refuses)."""

    items = _prompt_items(prompt_input_stdout)
    if items is None:
        return None
    skills: list[tuple[str, str]] = []
    for text in _message_texts(items):
        for block in _SKILLS_BLOCK.finditer(text):
            body = block.group(1)
            roots = dict(_SKILL_ROOT.findall(body))
            entries = _SKILL_ENTRY.findall(body)
            listed = [line for line in body.splitlines() if line.startswith("- ") and not _SKILL_ROOT.match(line)]
            if len(entries) != len(listed):
                return None
            for name, root, relative in entries:
                if root not in roots:
                    return None
                skills.append((name.strip(), str(Path(roots[root]) / relative)))
    return skills


def skill_disable_overrides(skills: Iterable[tuple[str, str]]) -> list[str]:
    """``-c`` keys that leave a turn no skill: bundled skills off, and every listed skill disabled
    by name and by path (a later ``-c`` layer's rule beats every config file's, codex-cli 0.163.0
    ``skill_config_rules_from_stack``), so no ``$name`` or ``SKILL.md`` link in a prompt can expand one."""

    overrides = ["skills.bundled.enabled=false"]
    rules: list[str] = []
    for name, path in sorted(set(skills)):
        rules.append(f"{{name={json.dumps(name)}, enabled=false}}")
        rules.append(f"{{path={json.dumps(path)}, enabled=false}}")
    if rules:
        overrides.append(f"skills.config=[{', '.join(rules)}]")
    return overrides


# -- the effective permission profile (hardening round 2, H1) ---------------------------

_PERMISSION_PROFILE = re.compile(r"<permission_profile\b([^>]*)>(.*?)</permission_profile>", re.S)
_FILE_SYSTEM = re.compile(r"<file_system\b([^>]*)>(.*?)</file_system>", re.S)
_ENTRY = re.compile(
    r'<entry access="(?P<access>[^"]*)">\s*(?:<path>(?P<path>[^<]*)</path>|<special>(?P<special>[^<]*)</special>)'
    r"\s*</entry>",
    re.S,
)
_NETWORK_RESTRICTED = "Network access is restricted."


def _message_texts(prompt_input: Any) -> list[str]:
    texts: list[str] = []
    for message in prompt_input if isinstance(prompt_input, list) else ():
        for content in (message.get("content") if isinstance(message, dict) else None) or ():
            text = content.get("text") if isinstance(content, dict) else None
            if isinstance(text, str):
                texts.append(text)
    return texts


def _attribute(attributes: str, name: str) -> str | None:
    found = re.search(rf'\b{name}="([^"]*)"', attributes)
    return found.group(1) if found else None


def _is_codex_helper(path: Path, codex_homes: Iterable[Path]) -> bool:
    """Codex's own read root for its re-exec helpers: ``$CODEX_HOME/tmp/arg0*/codex-arg0*``."""

    for home in codex_homes:
        try:
            relative = path.relative_to(home / "tmp")
        except ValueError:
            continue
        parts = relative.parts
        if len(parts) == 2 and parts[0].startswith("arg0") and parts[1].startswith("codex-arg0"):
            return True
    return False


def permission_profile_violations(prompt_input_stdout: str, *, root: Path, codex_home: Path) -> list[str]:
    """What the turn's effective permission profile allows beyond the lockdown's (empty: nothing).

    ``prompt_input_stdout`` is ``codex debug prompt-input`` under the turn's
    overrides, in the turn's directory: the model-visible context Codex builds
    for a thread, with no model request. Its environment context renders the
    effective filesystem policy, and its permissions instructions the network
    policy. The profile must be exactly: read ``root``, read ``:minimal``,
    Codex's own helper directory under ``codex_home``, nothing else, and
    network restricted. Anything else (``:root`` from an inherited
    ``extends``, an extra read or write root of a lower layer, a policy this
    parser does not know, no rendering at all) refuses the turn."""

    try:
        prompt_input = json.loads(prompt_input_stdout)
    except ValueError:
        return ["`codex debug prompt-input` did not return the turn's prompt input"]
    texts = _message_texts(prompt_input)
    profiles = [match for text in texts for match in _PERMISSION_PROFILE.finditer(text)]
    if len(profiles) != 1:
        return [f"`codex debug prompt-input` rendered {len(profiles)} permission profiles, not exactly one"]
    body = profiles[0].group(2)
    systems = list(_FILE_SYSTEM.finditer(body))
    if len(systems) != 1 or _FILE_SYSTEM.sub("", body).strip():
        return ["the effective permission profile holds something besides one filesystem policy"]
    problems: list[str] = []
    kind = _attribute(systems[0].group(1), "type")
    if kind != "restricted":
        problems.append(f"the effective filesystem policy is {kind!r}, not 'restricted'")
    entries_text = systems[0].group(2)
    if _ENTRY.sub("", entries_text).strip():
        problems.append("the effective filesystem policy holds an entry this check cannot read")
    expected_root = str(Path(root).resolve())
    homes = {Path(codex_home), Path(os.path.realpath(codex_home))}
    seen: set[tuple[str, str]] = set()
    for entry in _ENTRY.finditer(entries_text):
        access = html.unescape(entry.group("access"))
        if entry.group("special") is not None:
            target = ("special", html.unescape(entry.group("special")).strip())
        else:
            target = ("path", html.unescape(entry.group("path") or "").strip())
        if access != "read":
            problems.append(f"{access} access to {target[1]}")
        elif target in (("special", ":minimal"), ("path", expected_root)):
            seen.add(target)
        elif not (target[0] == "path" and _is_codex_helper(Path(target[1]), homes)):
            problems.append(f"read access to {target[1]}")
    for missing in sorted({("special", ":minimal"), ("path", expected_root)} - seen):
        problems.append(f"no read entry for {missing[1]} (the profile is not the one the turn passed)")
    permissions = [text for text in texts if "<permissions instructions>" in text]
    if len(permissions) != 1 or _NETWORK_RESTRICTED not in permissions[0] or "Network access is enabled" in permissions[0]:
        problems.append("the effective profile does not report network access restricted")
    return problems


# -- where the subprocess runs: CODEX_HOME and the executable (hardening round 2, H2) ----


def resolve_codex_home(environ: Mapping[str, str], cwd: Path) -> tuple[Path, bool]:
    """``$CODEX_HOME`` as a Codex process started in ``cwd`` with ``environ`` resolves it.

    codex-cli 0.163.0 (``utils/home-dir``): a non-empty ``CODEX_HOME`` must be
    an existing directory and is canonicalized, a relative one against the
    process's working directory (the turn's, not LearnLoop's); unset, it is
    ``$HOME/.codex``. Returns the path and whether ``CODEX_HOME`` was set (the
    caller then pins the subprocess to the absolute path). A relative
    ``CODEX_HOME`` that does not exist from ``cwd``, or a relative ``HOME``,
    refuses: Codex would fail or load another home than the one checked."""

    raw = (environ.get("CODEX_HOME") or "").strip()
    if raw:
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = Path(cwd) / candidate
        if not candidate.is_dir():
            raise CodexLockdownUnavailable(
                f"CODEX_HOME {raw!r} is not a directory seen from the turn's directory {cwd}, where Codex resolves "
                "it; set an absolute CODEX_HOME. Refusing the isolated turn."
            )
        return candidate.resolve(), True
    home = (environ.get("HOME") or "").strip()
    if not home or not Path(home).is_absolute():
        raise CodexLockdownUnavailable(
            "Neither CODEX_HOME nor an absolute HOME is set, so the Codex home the turn would load cannot be "
            "checked; refusing the isolated turn."
        )
    return Path(home) / ".codex", False


def resolve_executable(program: str, environ: Mapping[str, str], cwd: Path) -> str:
    """The absolute file ``subprocess`` would execute for ``program`` started in ``cwd``.

    A path with a separator is taken relative to ``cwd`` (the child's working
    directory); a bare name is searched in ``environ``'s ``PATH``, an empty or
    relative entry against ``cwd``, the first executable file winning, as
    ``execvpe`` does after the child changed directory. Not found refuses."""

    if not program:
        raise CodexLockdownUnavailable("The Codex launch command is empty; refusing the isolated turn.")
    candidates: list[Path]
    if os.sep in program or (os.altsep and os.altsep in program):
        candidates = [Path(program).expanduser()]
    else:
        candidates = [Path(entry or ".") / program for entry in (environ.get("PATH") or os.defpath).split(os.pathsep)]
    for candidate in candidates:
        path = candidate if candidate.is_absolute() else Path(cwd) / candidate
        if path.is_file() and os.access(path, os.X_OK):
            return os.path.abspath(path)
    raise CodexLockdownUnavailable(
        f"The Codex executable {program!r} is not found from the turn's directory {cwd}; refusing the isolated turn."
    )


# -- turn items -----------------------------------------------------------------------

#: Item types a locked-down turn may produce: the prompt, the answer, reasoning.
TEXT_ITEMS = frozenset({"usermessage", "agentmessage", "reasoning"})
#: A workspace turn (the snapshot diagnosis) also runs commands to read it.
WORKSPACE_ITEMS = TEXT_ITEMS | {"commandexecution"}


def item_kind(item: Any) -> str:
    """An SDK turn item's type, lower-cased without ``_``/``-`` (``agentMessage`` -> ``agentmessage``).

    An item that names no type but carries a command is a command execution;
    anything else without a type is ``unknown`` (never text)."""

    item = getattr(item, "root", item)
    kind = item.get("type") if isinstance(item, dict) else getattr(item, "type", None)
    kind = getattr(kind, "value", kind)
    if not kind:
        command = item.get("command") if isinstance(item, dict) else getattr(item, "command", None)
        return "commandexecution" if command else "unknown"
    return str(kind).replace("_", "").replace("-", "").lower()


def item_violations(items: Iterable[Any] | None, *, workspace: bool) -> list[str]:
    """Kinds of ``items`` a locked-down turn may not produce (fix 4)."""

    allowed = WORKSPACE_ITEMS if workspace else TEXT_ITEMS
    return [kind for kind in (item_kind(item) for item in (items or ())) if kind not in allowed]


# -- approvals and notifications --------------------------------------------------------

#: The declining answer to each server request the app server can send
#: (app-server protocol v2 ``ServerRequest``; v1 ``*Approval`` use ``denied``).
_DECLINES: dict[str, dict[str, Any]] = {
    "item/commandExecution/requestApproval": {"decision": "decline"},
    "item/fileChange/requestApproval": {"decision": "decline"},
    "item/permissions/requestApproval": {"permissions": {}, "scope": "turn"},
    "item/tool/requestUserInput": {"answers": {}},
    "mcpServer/elicitation/request": {"action": "decline"},
    "item/tool/call": {"contentItems": [], "success": False},
    "applyPatchApproval": {"decision": "denied"},
    "execCommandApproval": {"decision": "denied"},
}
#: Server requests that are not the model's (auth refresh, attestation): left
#: as the SDK's own default answers them (an empty result).
_CLIENT_REQUESTS = frozenset({"account/chatgptAuthTokens/refresh", "attestation/generate"})


class CodexLockdownUnavailable(AIProviderUnavailable):
    """The locked-down profile cannot be put in force, so the turn is refused before it starts."""


class CodexToolUseRefused(AIProviderUnavailable):
    """A locked-down turn used a tool, a sub-agent or an extra request: its answer is refused."""

    def __init__(self, message: str, violations: list[str]):
        super().__init__(message)
        self.violations = list(violations)


class CodexHttpTransportRefused(CodexLockdownUnavailable):
    """The legacy Codex HTTP adapter is refused by the tool lockdown, for every operation (H3)."""


def refuse_legacy_http_transport(where: str) -> NoReturn:
    """Refuse the legacy endpoint-per-operation Codex HTTP transport (hardening round 2, H3).

    It posts LearnLoop's context to a server LearnLoop does not start (or
    starts with an arbitrary ``startup_command``), whose approvals, tools, MCP
    servers and permission profile nothing here can set, verify or observe:
    none of the lockdown applies. Every entry (``provider = "http"``, the
    ``http``/``http_adapter`` profiles, each legacy operation, the runtime
    check and its startup command) calls this first, through this module's
    attribute (so the e2e tests' in-process HTTP double can stand in for a
    provider; no configuration, variable or flag reaches it)."""

    raise CodexHttpTransportRefused(
        f"The legacy Codex HTTP transport ({where}) is refused by the Codex tool lockdown (security stage "
        "codex-tool-lockdown): LearnLoop cannot switch off or observe the tools of an app server it does not "
        'launch. Use the Codex SDK provider (type = "codex_sdk").'
    )


def _field(payload: Any, *names: str) -> Any:
    for name in names:
        value = payload.get(name) if isinstance(payload, dict) else getattr(payload, name, None)
        if value is not None:
            return value
    params = getattr(payload, "params", None)
    if isinstance(params, dict):
        for name in names:
            if params.get(name) is not None:
                return params[name]
    return None


def _tokens(breakdown: Any, *names: str) -> int:
    value = _field(breakdown, *names)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0
    return max(0, int(value))


@dataclass
class TurnLockdown:
    """What one locked-down turn did, seen from every app-server message.

    ``workspace`` turns may run commands (and so make a model request per
    command round); other turns may make exactly one model request and produce
    only text. ``on_violation`` is called (once) at the first violation so the
    caller can stop the turn: the tool-round cap is 0."""

    parent_thread: str | None
    workspace: bool = False
    on_violation: Callable[[], None] | None = None
    violations: list[str] = field(default_factory=list)
    server_requests: list[str] = field(default_factory=list)
    tool_items: list[str] = field(default_factory=list)
    guardian_reviews: int = 0
    #: Each thread's latest cumulative usage, and the distinct totals it went
    #: through (one per model request: a fresh thread starts at zero).
    thread_usage: dict[str, Any] = field(default_factory=dict)
    thread_totals: dict[str, set[int]] = field(default_factory=dict)
    threads: set[str] = field(default_factory=set)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _stopped: bool = False
    #: Whether the request in flight has completed an assistant message that
    #: may be the answer (phase ``final_answer``, or no phase reported).
    _answered: bool = False

    def _violate(self, what: str) -> None:
        stop = None
        with self._lock:
            self.violations.append(what)
            if not self._stopped:
                self._stopped = True
                stop = self.on_violation
        if stop is not None:
            try:
                stop()
            except Exception:  # noqa: BLE001 - the refusal stands whether or not the stop lands
                pass

    def handle_server_request(self, method: str, params: dict[str, Any] | None) -> dict[str, Any]:
        """The SDK approval handler: decline everything the model asks for."""

        if method in _CLIENT_REQUESTS:
            return {}
        with self._lock:
            self.server_requests.append(method)
        self._violate(f"server request {method}")
        return dict(_DECLINES.get(method, {}))

    def observe(self, notification: Any) -> None:
        """One app-server notification (called on the SDK's reader thread)."""

        method = getattr(notification, "method", None) or _field(notification, "method")
        payload = getattr(notification, "payload", notification)
        thread = _field(payload, "thread_id", "threadId")
        if thread is None and method == "thread/started":
            thread = _field(_field(payload, "thread") or {}, "id")
        if isinstance(thread, str):
            with self._lock:
                self.threads.add(thread)
        child = isinstance(thread, str) and self.parent_thread is not None and thread != self.parent_thread
        if method == "thread/tokenUsage/updated":
            usage = _field(payload, "token_usage", "tokenUsage")
            total = _field(usage, "total") if usage is not None else None
            if isinstance(thread, str) and total is not None:
                tokens = _tokens(total, "total_tokens", "totalTokens")
                with self._lock:
                    self.thread_usage[thread] = total
                    totals = self.thread_totals.setdefault(thread, set())
                    finished = tokens > 0 and tokens not in totals  # a request ended (0 or a repeat: none)
                    if finished:
                        totals.add(tokens)
                    requests = len(totals)
                    answered, self._answered = self._answered, (self._answered and not finished)
                if not child and not self.workspace and requests > 1:
                    self._violate("a second model request in the turn (a tool round trip)")
                elif not child and not self.workspace and finished and not answered:
                    # The request ended without an answer: the model called a
                    # tool (code mode's exec leaves no item). Stopped here, before
                    # the tool's round trip becomes a second request.
                    self._violate("a model response that ended in a tool call (no final answer)")
        if child:
            self._violate(f"sub-agent thread activity ({method})")
            return
        if method in ("item/started", "item/completed"):
            item = _field(payload, "item") or {}
            kind = item_kind(item)
            if method == "item/completed" and kind == "agentmessage":
                phase = _field(getattr(item, "root", item), "phase")
                phase = getattr(phase, "value", phase)
                if phase in (None, "final_answer"):  # an answer, or a model that reports no phases
                    with self._lock:
                        self._answered = True
            allowed = WORKSPACE_ITEMS if self.workspace else TEXT_ITEMS
            if kind not in allowed:
                with self._lock:
                    if method == "item/started" or kind not in self.tool_items:
                        self.tool_items.append(kind)
                self._violate(f"tool item {kind}")
        elif method in ("item/autoApprovalReview/started", "item/autoApprovalReview/completed"):
            if method.endswith("started"):
                with self._lock:
                    self.guardian_reviews += 1
            self._violate("a Guardian approval review")
        elif method in ("hook/started",):
            self._violate("a hook ran")

    def model_requests(self) -> int:
        """Model requests the SDK reported across every thread (at least 1 once usage arrived)."""

        with self._lock:
            return sum(len(totals) for totals in self.thread_totals.values())

    def reported_usage(self) -> bool:
        """Whether the SDK reported any thread's usage during the turn."""

        with self._lock:
            return bool(self.thread_usage)

    def child_usage(self) -> list[Any]:
        """The latest cumulative usage of every thread other than the turn's own."""

        with self._lock:
            return [usage for thread, usage in self.thread_usage.items() if thread != self.parent_thread]

    def parent_usage(self) -> Any:
        with self._lock:
            return self.thread_usage.get(self.parent_thread) if self.parent_thread is not None else None

    def summary(self) -> dict[str, Any]:
        with self._lock:
            return {
                "threads": len(self.threads | ({self.parent_thread} if self.parent_thread else set())),
                "model_requests": sum(len(totals) for totals in self.thread_totals.values()),
                "tool_items": list(self.tool_items),
                "server_requests": list(self.server_requests),
                "guardian_reviews": self.guardian_reviews,
                "violations": list(self.violations),
            }


def install_on_sdk(codex: Any, lockdown: TurnLockdown) -> None:
    """Put ``lockdown`` between the SDK client and the app server, or refuse.

    The SDK's ``Codex`` builds its client with the default approval handler,
    which ACCEPTS every command and file-change request (openai_codex
    ``CodexClient._default_approval_handler``), and routes notifications of
    other threads (sub-agents) to queues nobody reads. Both are replaced on the
    live client: the handler by :meth:`TurnLockdown.handle_server_request`, and
    the router's ``route_notification`` by a tap that shows every
    notification to :meth:`TurnLockdown.observe` first. An SDK without those
    seams cannot be locked down."""

    client = getattr(codex, "_client", None)
    router = getattr(client, "_router", None)
    route = getattr(router, "route_notification", None)
    if client is None or not hasattr(client, "_approval_handler") or not callable(route):
        raise CodexLockdownUnavailable(
            "The installed Codex SDK has no approval-handler or notification seam LearnLoop can replace, so "
            "its accept-all approval default cannot be declined; refusing the isolated turn."
        )

    def tapped(notification: Any) -> Any:
        try:
            lockdown.observe(notification)
        except Exception:  # noqa: BLE001 - observation never breaks the SDK's reader thread
            lockdown._violate("a notification the lockdown could not read")
        return route(notification)

    client._approval_handler = lockdown.handle_server_request
    router.route_notification = tapped


# -- the launch check's cache ----------------------------------------------------------

#: fingerprint -> (MCP servers pinned off by name, unclassified features switched
#: off, the tool-free catalog's exact text the turns are pinned to, the skills
#: disabled by name and path)
_CHECK_CACHE: dict[str, tuple[tuple[str, ...], tuple[str, ...], str, tuple[tuple[str, str], ...]]] = {}
_CHECK_CACHE_LOCK = threading.Lock()
#: Codex configuration layers a launch can load besides the project ones.
_SYSTEM_LAYERS = ("/etc/codex/config.toml", "/etc/codex/managed_config.toml", "/etc/codex/requirements.toml")
_HOME_LAYERS = ("config.toml", "managed_config.toml", "requirements.toml", "plugins", "skills", ".tmp")


def _stat_signature(path: Path) -> tuple[Any, ...]:
    """Identity of a file or directory without opening it (it may hold credentials).

    ``st_ctime_ns`` too: any write or rename moves it, and unlike the mtime it
    cannot be set back."""

    try:
        stat = path.stat()
    except OSError:
        return (str(path), None)
    return (str(path), stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)


def check_fingerprint(
    *,
    command: Iterable[str],
    root: Path,
    shell: bool,
    model: str | None,
    sandbox_workdir: str | None,
    environ: Mapping[str, str] | None = None,
    codex_home: Path | None = None,
) -> str:
    """What the launch check's verdict depends on, as one key.

    The CLI argv and binary, the turn's tool set and model, the bubblewrap
    sandbox, the environment Codex reads (``CODEX_*``, ``HOME``), and the
    identity (inode, size, mtime; never the content) of every configuration
    layer it can load: ``$CODEX_HOME``'s files and plugin/skill directories,
    the system ones, and ``.codex/`` in the turn directory and each ancestor
    (project layers). A fresh turn directory without ``.codex/`` (every
    scratch turn, the diagnosis export) adds only that it has none, so those
    turns share one check; one that has a ``.codex/`` (a supplied workspace
    carrying its own project layer) adds its path and the identity of
    ``.codex/`` and ``.codex/config.toml``, so editing that file, or turning
    in a sibling workspace with another one, runs the check again (Codex
    review F2, 2026-10-21: the cached server list missed a workspace-local
    MCP server, which then started without its ``enabled=false``).

    ``command`` and ``codex_home`` are what the subprocess uses, resolved from
    the turn's directory and pinned by the caller (hardening round 2, H2:
    a relative ``CODEX_HOME`` or a bare ``codex`` was fingerprinted from
    LearnLoop's own directory, not the one the subprocess resolves it in).
    The binary is fingerprinted as named and as its real file."""

    environ = os.environ if environ is None else environ
    argv = list(command)
    binary = Path(argv[0]) if argv else None
    if codex_home is None:
        codex_home = Path(environ.get("CODEX_HOME") or Path(environ.get("HOME") or "~").expanduser() / ".codex")
    parts: list[Any] = [
        tuple(argv), _stat_signature(binary) if binary is not None else None,
        _stat_signature(Path(os.path.realpath(binary))) if binary is not None else None,
        str(codex_home), shell, model or "", sandbox_workdir,
        tuple(sorted((key, value) for key, value in environ.items() if key.startswith("CODEX_") or key == "HOME")),
        tuple(_stat_signature(codex_home / name) for name in _HOME_LAYERS),
        tuple(_stat_signature(Path(name)) for name in _SYSTEM_LAYERS),
        # Skill roots (round 3): a skill added to any of them changes its
        # directory, so the check finds and disables it before the next turn.
        tuple(_stat_signature(path) for path in _skill_roots(environ)),
    ]
    resolved = Path(root).resolve()
    own = resolved / ".codex"
    if os.path.lexists(own):
        parts.append(("workspace layer", str(resolved), _stat_signature(own), _stat_signature(own / "config.toml")))
    else:
        parts.append(("workspace layer", None))
    # The turn directory's own skill roots count only when present, so fresh
    # scratch turns still share one check.
    parts += [("workspace skills", name, _stat_signature(resolved / name))
              for name in (".codex/skills", ".agents", ".agents/skills") if os.path.lexists(resolved / name)]
    for directory in resolved.parents:
        parts.append(_stat_signature(directory / ".codex"))
        parts.append(_stat_signature(directory / ".codex" / "config.toml"))
        for name in (".codex/skills", ".agents", ".agents/skills"):
            parts.append(_stat_signature(directory / name))
    return hashlib.sha256(json.dumps(parts, default=str).encode("utf-8")).hexdigest()


def _skill_roots(environ: Mapping[str, str]) -> list[Path]:
    """Skill roots outside ``$CODEX_HOME`` that codex-cli 0.163.0 discovers (``ext/skills`` ``host_roots``)."""

    roots = [Path("/etc/codex/skills")]
    home = (environ.get("HOME") or "").strip()
    if home:
        roots += [Path(home) / ".agents", Path(home) / ".agents" / "skills"]
    return roots


def cached_check(key: str) -> tuple[tuple[str, ...], tuple[str, ...], str, tuple[tuple[str, str], ...]] | None:
    """A passed launch check under ``key``: (servers pinned off, extra features off, pinned catalog, skills off)."""

    with _CHECK_CACHE_LOCK:
        return _CHECK_CACHE.get(key)


def remember_check(key: str, pinned_servers: Iterable[str], extra_features: Iterable[str], catalog: str,
                   skills: Iterable[tuple[str, str]] = ()) -> None:
    """Remember a launch check that passed (a refusal is never cached)."""

    with _CHECK_CACHE_LOCK:
        _CHECK_CACHE[key] = (tuple(pinned_servers), tuple(extra_features), catalog, tuple(skills))


def clear_check_cache() -> None:
    """Forget every cached launch check (tests; a config change the fingerprint misses)."""

    with _CHECK_CACHE_LOCK:
        _CHECK_CACHE.clear()


__all__ = [
    "READBACK_OVERRIDES",
    "TOOL_FREE_METADATA",
    "advertised_tool_violations",
    "readback_overrides",
    "rendered_skills",
    "skill_disable_overrides",
    "tool_free_catalog",
    "tool_free_violations",
    "CATALOG_PIN_KEY",
    "CodexHttpTransportRefused",
    "CodexLockdownUnavailable",
    "CodexToolUseRefused",
    "ISOLATED_PROFILE",
    "LOCKDOWN_DISABLED_FEATURES",
    "PERMITTED_FEATURES",
    "REMOVED_STAGE",
    "REQUIRED_OFF_FEATURES",
    "REVIEWED_RETIRED_FEATURES",
    "SHELL_ENVIRONMENT_ALLOWLIST",
    "SHELL_FEATURES",
    "TEXT_ITEMS",
    "TurnLockdown",
    "WORKSPACE_ITEMS",
    "catalog_pin_override",
    "catalog_pin_path",
    "catalog_violations",
    "check_fingerprint",
    "clear_check_cache",
    "cli_version_text",
    "disabled_features",
    "feature_refusal",
    "feature_violations",
    "install_on_sdk",
    "item_kind",
    "item_violations",
    "lockdown_config_overrides",
    "model_metadata_violations",
    "permission_profile_violations",
    "permitted_features",
    "refuse_legacy_http_transport",
    "resolve_codex_home",
    "resolve_executable",
    "retired_features_permitted",
    "shell_environment_overrides",
    "unclassified_features_on",
]
