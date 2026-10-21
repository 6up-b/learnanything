"""The locked-down Codex turn: no tool that can read, write, run, reach or spawn.

Security stage 2026-10-21 (docs/reviews/security-codex-tool-lockdown.md). Every
turn LearnLoop starts on the Codex SDK runs this one profile. Its pieces, each
pure here and wired in by :mod:`learnloop.ai.providers.codex`:

* **configuration** (:func:`lockdown_config_overrides`): the ``-c`` keys that
  switch off sub-agents, user-input and plan tools and web search, on top of
  the permission profile and feature switches of the isolated turn;
* **features** (:func:`feature_violations`): what ``codex features list`` may
  still report on. Only the reviewed non-tool features of codex-cli 0.163.0
  (:data:`PERMITTED_FEATURES`); any other feature reported on is switched off
  by the caller and must then read off, or the turn is refused;
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

Why config cannot remove everything (fix 5 of the investigation, not built):
codex-cli 0.163.0 takes ``apply_patch`` and code mode (``exec``/``wait``) from
the model's catalog entry, not from any feature. They are neutralized instead:
a patch cannot write (the profile has no writable root, approvals are
``never`` and every file-change request is declined) and any patch or code-mode
round trip is a second model request or a tool item, which refuses the turn.
Replacing the catalog would replace the model's served metadata (base
instructions, reasoning defaults) on every route.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from learnloop.ai.errors import AIProviderUnavailable

#: Tools and integrations that run outside the command sandbox, bring outside
#: context, or offer the model a tool, all off in every locked-down turn
#: (codex-cli 0.163.0 ``features list``; each key checked to take effect under
#: ``-c features.<key>=false``). Unknown keys are ignored by Codex.
LOCKDOWN_DISABLED_FEATURES = (
    "apps",
    "auth_elicitation",
    "agent_message_board",
    "artifact",
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
SHELL_FEATURES = ("shell_tool", "unified_exec", "unified_exec_tty", "shell_snapshot")
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


def lockdown_config_overrides() -> list[str]:
    """``-c`` keys (beyond features) that remove tools from every locked-down turn.

    In codex-cli 0.163.0 ``agents.enabled=false`` is what removes sub-agents:
    ``multi_agent_version_for_model`` takes it before the model's own
    ``multi_agent_version`` (``features.multi_agent`` does not govern v2), as
    long as ``features.multi_agent_v2`` is off. ``request_user_input`` is on by
    default; ``update_plan`` is off by default and pinned off here.
    """

    return [
        "agents.enabled=false",
        "tools.experimental_request_user_input.enabled=false",
        "tools.update_plan.enabled=false",
        "tools.web_search=false",
    ]


def disabled_features(*, shell: bool) -> tuple[str, ...]:
    return LOCKDOWN_DISABLED_FEATURES + (() if shell else SHELL_FEATURES)


def permitted_features(*, shell: bool) -> frozenset[str]:
    return PERMITTED_FEATURES | (frozenset(SHELL_FEATURES) if shell else frozenset())


def feature_violations(states: Mapping[str, bool], *, shell: bool) -> list[str]:
    """Features ``states`` (``features list``) shows on that a locked-down turn may not have.

    A feature this list switches off, or one the CLI requires to know
    (:data:`REQUIRED_OFF_FEATURES`), that does not read exactly ``false``; and
    any feature on that is not permitted (:func:`permitted_features`)."""

    allowed = permitted_features(shell=shell)
    named = [feature for feature in REQUIRED_OFF_FEATURES if states.get(feature) is not False]
    # Everything else on must be permitted. ``unified_exec`` is switched off
    # and permitted at once: codex-cli 0.163.0 ignores its override, and it
    # offers no tool without ``shell_tool`` (which must read off).
    named += sorted(feature for feature, on in states.items() if on and feature not in allowed and feature not in named)
    return named


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
                    if tokens > 0:  # a usage update before any request carries no request
                        totals.add(tokens)
                    requests = len(totals)
                if not child and not self.workspace and requests > 1:
                    self._violate("a second model request in the turn (a tool round trip)")
        if child:
            self._violate(f"sub-agent thread activity ({method})")
            return
        if method in ("item/started", "item/completed"):
            kind = item_kind(_field(payload, "item") or {})
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
            "its accept-all approval default cannot be declined; refusing the Codex turn."
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

#: fingerprint -> (MCP servers pinned off by name, unclassified features switched off)
_CHECK_CACHE: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {}
_CHECK_CACHE_LOCK = threading.Lock()
#: Codex configuration layers a launch can load besides the project ones.
_SYSTEM_LAYERS = ("/etc/codex/config.toml", "/etc/codex/managed_config.toml", "/etc/codex/requirements.toml")
_HOME_LAYERS = ("config.toml", "managed_config.toml", "requirements.toml", "plugins", "skills", ".tmp")


def _stat_signature(path: Path) -> tuple[Any, ...]:
    """Identity of a file or directory without opening it (it may hold credentials)."""

    try:
        stat = path.stat()
    except OSError:
        return (str(path), None)
    return (str(path), stat.st_ino, stat.st_size, stat.st_mtime_ns)


def check_fingerprint(
    *,
    command: Iterable[str],
    root: Path,
    shell: bool,
    model: str | None,
    sandbox_workdir: str | None,
    environ: Mapping[str, str] | None = None,
) -> str:
    """What the launch check's verdict depends on, as one key.

    The CLI argv and binary, the turn's tool set and model, the bubblewrap
    sandbox, the environment Codex reads (``CODEX_*``, ``HOME``), and the
    identity (inode, size, mtime; never the content) of every configuration
    layer it can load: ``$CODEX_HOME``'s files and plugin/skill directories,
    the system ones, and ``.codex/`` in the turn directory's parent and each
    ancestor (project layers). The turn directory itself is new each turn
    and so left out; its parent stands for where it is made."""

    environ = os.environ if environ is None else environ
    argv = list(command)
    binary = Path(argv[0]) if argv else None
    codex_home = Path(environ.get("CODEX_HOME") or Path(environ.get("HOME") or "~").expanduser() / ".codex")
    parts: list[Any] = [
        tuple(argv), _stat_signature(binary) if binary is not None else None, shell, model or "", sandbox_workdir,
        tuple(sorted((key, value) for key, value in environ.items() if key.startswith("CODEX_") or key == "HOME")),
        tuple(_stat_signature(codex_home / name) for name in _HOME_LAYERS),
        tuple(_stat_signature(Path(name)) for name in _SYSTEM_LAYERS),
    ]
    resolved = Path(root).resolve()
    parts.append((resolved / ".codex").exists())  # the turn's own directory: whether, not where
    for directory in resolved.parents:
        parts.append(_stat_signature(directory / ".codex"))
        parts.append(_stat_signature(directory / ".codex" / "config.toml"))
    return hashlib.sha256(json.dumps(parts, default=str).encode("utf-8")).hexdigest()


def cached_check(key: str) -> tuple[tuple[str, ...], tuple[str, ...]] | None:
    """A passed launch check under ``key``: (servers pinned off, extra features off)."""

    with _CHECK_CACHE_LOCK:
        return _CHECK_CACHE.get(key)


def remember_check(key: str, pinned_servers: Iterable[str], extra_features: Iterable[str]) -> None:
    """Remember a launch check that passed (a refusal is never cached)."""

    with _CHECK_CACHE_LOCK:
        _CHECK_CACHE[key] = (tuple(pinned_servers), tuple(extra_features))


def clear_check_cache() -> None:
    """Forget every cached launch check (tests; a config change the fingerprint misses)."""

    with _CHECK_CACHE_LOCK:
        _CHECK_CACHE.clear()


__all__ = [
    "CodexLockdownUnavailable",
    "CodexToolUseRefused",
    "LOCKDOWN_DISABLED_FEATURES",
    "PERMITTED_FEATURES",
    "REQUIRED_OFF_FEATURES",
    "SHELL_FEATURES",
    "TEXT_ITEMS",
    "TurnLockdown",
    "WORKSPACE_ITEMS",
    "check_fingerprint",
    "clear_check_cache",
    "disabled_features",
    "feature_violations",
    "install_on_sdk",
    "item_kind",
    "item_violations",
    "lockdown_config_overrides",
    "model_metadata_violations",
    "permitted_features",
    "unclassified_features_on",
]
