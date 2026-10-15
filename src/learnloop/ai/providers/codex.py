"""Codex SDK structured transport and runtime integration."""

from __future__ import annotations

import dataclasses
import inspect
import json
import logging
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ValidationError

from learnloop.ai.errors import (
    AIInvalidOutput,
    AIOutputTruncated,
    AIInterrupted,
    AIProviderUnavailable,
    AITurnTimeout,
    CodexInterrupted,
    CodexTurnTimeout,
    CodexUnavailable,
)
from learnloop.ai.providers.structured_output import (
    structured_output_regeneration_prompt,
    structured_output_repair_prompt,
)
from learnloop.ai.schemas import (
    describe_wire_validation_error,
)
from learnloop.ai.strict_schema import strict_output_schema
from learnloop.ai.transport import (
    INTERRUPT,
    ISOLATED_TURN,
    READ_ONLY_WORKSPACE,
    STRUCTURED_COMPLETION,
    StructuredRequest,
)
from learnloop.ai.execution import (
    generation_limit,
    observed_sdk_turn,
    output_limit,
    report_call_usage,
    single_request_active,
)
from learnloop.ai.isolation import (
    TOOL_ISOLATION,
    ToolIsolation,
    ToolIsolationUnavailable,
    current_tool_isolation,
    sandboxed_command,
    write_launcher,
)
from learnloop.ai.usage import TokenUsageAccounting, UsageMeter, receipt_fields_from_codex_turn, usage_from_codex_turn
from learnloop.config import AIProviderConfig, CodexConfig

# Keep the established logger name while legacy imports are shims.
LOG = logging.getLogger("learnloop.ai.providers.codex")
EVENT_FIELDS_ATTR = "event_fields"

#: The Codex permission profile every isolated turn runs under (Slice 1 §4,
#: §5.6). Codex's built-in ``read-only`` sandbox grants full-disk READ access,
#: so it is never used for isolation: this profile reads only the turn's own
#: directory plus the platform minimum, and writes nowhere.
ISOLATED_PROFILE = "learnloop_isolated_turn"
#: Tools and integrations that run outside the command sandbox (connectors,
#: MCP, browser/computer use, plugins, sub-agents) or bring in outside context
#: (memories, hooks, skills, web search): all off in an isolated turn. Unknown
#: feature keys are ignored by Codex, so older/newer CLIs accept the list.
_ISOLATION_DISABLED_FEATURES = (
    "apps",
    "browser_use",
    "browser_use_external",
    "computer_use",
    "in_app_browser",
    "image_generation",
    "plugins",
    "remote_plugin",
    "multi_agent",
    "hooks",
    "memories",
    "view_image",
    "tool_suggest",
    "skill_search",
    "skill_mcp_dependency_install",
    "goals",
)


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def isolated_turn_overrides(
    readable_root: Path,
    *,
    shell: bool,
    mcp_server_ids: tuple[str, ...] | list[str] = (),
) -> list[str]:
    """``codex -c key=value`` overrides that confine one turn.

    The turn runs under :data:`ISOLATED_PROFILE`: read access to
    ``readable_root`` and the platform minimum only, no writes, no network;
    approvals never prompt; web search, connectors, MCP servers (each named
    one disabled), memories, hooks and project docs are off. With
    ``shell=False`` (no workspace to read) the command tools are off too, so
    the model has nothing but its prompt.
    """

    root = str(Path(readable_root).resolve())
    overrides = [
        f"default_permissions={_toml_string(ISOLATED_PROFILE)}",
        f'permissions.{ISOLATED_PROFILE}.filesystem={{":minimal"="read", {_toml_string(root)}="read"}}',
        f"permissions.{ISOLATED_PROFILE}.network.enabled=false",
        'approval_policy="never"',
        'web_search="disabled"',
        "project_doc_max_bytes=0",
        "tools.view_image=false",
    ]
    overrides += [f"features.{feature}=false" for feature in _ISOLATION_DISABLED_FEATURES]
    if not shell:
        overrides += ["features.shell_tool=false", "features.unified_exec=false"]
    overrides += [f"mcp_servers.{server}.enabled=false" for server in sorted(set(mcp_server_ids))]
    return overrides

class SdkCodexClient(TokenUsageAccounting):
    """Codex Python SDK-backed client.

    The SDK speaks the real Codex app-server v2 JSON-RPC protocol over stdio.
    LearnLoop still owns the learning-specific schemas and validates the final
    model output before anything can be persisted.
    """

    def __init__(self, config: CodexConfig, vault_root: Path):
        self.config = config
        self.provider_name = "codex"
        self.provider_type = "codex_sdk"
        self.model = config.model
        self.vault_root = vault_root.resolve()
        self.checkout_path = _resolve_checkout_path(self.vault_root, config.checkout_path)
        self.sdk_python_path = _resolve_sdk_python_path(self.checkout_path, config.sdk_python_path)
        self._turn_lock = threading.RLock()
        self._active_turn: Any = None
        self._active_codex: Any = None
        self._active_deadline_timer: threading.Timer | None = None
        self._active_force_close_timer: threading.Timer | None = None
        self._active_stop_scheduled = False
        self._interrupt_requested = threading.Event()
        self._deadline_expired = threading.Event()
        self._last_workspace_activity: list[str] | None = None

    def _codex_command(self) -> list[str]:
        """The argv prefix that runs this client's Codex CLI (before a subcommand)."""

        launch = _sdk_launch_args(self.config.sdk_launch_command)
        if launch:
            if "app-server" not in launch:
                raise CodexUnavailable(
                    "sdk_launch_command does not name `app-server`; an isolated turn cannot pass its sandbox overrides."
                )
            return list(launch[: launch.index("app-server")])
        configured = _resolved_sdk_codex_bin(self.config.sdk_codex_bin)
        if configured:
            return [configured]
        try:
            from codex_cli_bin import bundled_codex_path

            return [str(bundled_codex_path())]
        except (ImportError, FileNotFoundError):
            found = shutil.which("codex.cmd" if os.name == "nt" else "codex")
            if found:
                return [found]
        raise CodexUnavailable("No Codex CLI found to configure an isolated turn.")

    def _configured_mcp_server_ids(self, cwd: Path) -> tuple[str, ...]:
        """MCP servers the app server would load in ``cwd``, to disable each.

        An MCP tool runs outside the command sandbox, so an isolated turn must
        disable every configured server by name. Listing fails closed.
        """

        command = [*self._codex_command(), "mcp", "list", "--json"]
        try:
            result = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True, timeout=60, check=False)
            servers = json.loads(result.stdout) if result.returncode == 0 else None
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            raise CodexUnavailable(f"Cannot list Codex MCP servers to disable them: {exc}") from exc
        if not isinstance(servers, list):
            raise CodexUnavailable(
                "Cannot list Codex MCP servers to disable them for an isolated turn "
                f"(exit {result.returncode})."
            )
        return tuple(str(server["name"]) for server in servers if isinstance(server, dict) and server.get("name"))

    def workspace_activity(self) -> list[str] | None:
        """What the last read-only-workspace turn reported reading, if anything.

        Best effort: populated only when the SDK's turn result exposes the
        agent's tool items. ``None`` means the transport reported nothing, which
        receipts must record as unknown rather than as "opened no files".
        """

        return list(self._last_workspace_activity) if self._last_workspace_activity is not None else None

    def interrupt(self) -> bool:
        """Interrupt this client's active SDK turn without killing the sidecar.

        The cancellation flag is set before looking up the turn handle so a
        request racing with turn startup still prevents that call from running.
        Clients are scoped to one ingest job, so the flag intentionally remains
        set for the rest of that job attempt.
        """

        self._interrupt_requested.set()
        with self._turn_lock:
            turn = self._active_turn
            codex = self._active_codex
        if turn is not None:
            self._schedule_turn_stop(turn, codex)
        return True

    def _expire_turn(self, turn: Any, codex: Any) -> None:
        """Deadline callback: request a clean interrupt, then force-close if needed."""

        with self._turn_lock:
            if self._active_turn is not turn:
                return
            self._deadline_expired.set()
        self._schedule_turn_stop(turn, codex)

    def _schedule_turn_stop(self, turn: Any, codex: Any) -> None:
        """Stop an SDK turn without blocking the palette or deadline thread."""

        with self._turn_lock:
            if self._active_turn is not turn or self._active_stop_scheduled:
                return
            self._active_stop_scheduled = True
            close = getattr(codex, "close", None)
            if callable(close):
                force_close = threading.Timer(0.25, close)
                force_close.daemon = True
                self._active_force_close_timer = force_close
                force_close.start()

        def request_interrupt() -> None:
            try:
                turn.interrupt()
            except Exception:  # noqa: BLE001 - force-close is the bounded fallback
                return

        threading.Thread(
            target=request_interrupt,
            name="learnloop-codex-interrupt",
            daemon=True,
        ).start()

    def complete(self, request: StructuredRequest[Any]) -> Any:
        """Execute one structured request with Codex's existing repair policy."""

        marker = object()
        previous_timeout = self.__dict__.get("_request_timeout_seconds", marker)
        previous_effort = self.__dict__.get("_request_reasoning_effort", marker)
        if request.timeout_seconds is not None:
            self._request_timeout_seconds = request.timeout_seconds
        # A route's requested effort (ai.route_reasoning_effort) replaces the
        # profile's for this turn only.
        self._request_reasoning_effort = request.reasoning_effort
        try:
            with generation_limit(request.output_budget_tokens):
                return self._complete_validated(
                    request.prompt,
                    request.result_model,
                    purpose=request.purpose,
                    workspace=request.workspace,
                    isolated=request.isolated or request.workspace is not None,
                )
        finally:
            if previous_timeout is marker:
                self.__dict__.pop("_request_timeout_seconds", None)
            else:
                self._request_timeout_seconds = previous_timeout
            if previous_effort is marker:
                self.__dict__.pop("_request_reasoning_effort", None)
            else:
                self._request_reasoning_effort = previous_effort

    def supports(self, capability: str) -> bool:
        return capability in {
            STRUCTURED_COMPLETION,
            "complete",
            "structured",
            INTERRUPT,
            # Under learnloop.ai.isolation.tool_isolation the app-server runs
            # in a bubblewrap sandbox (see _isolated_launch).
            TOOL_ISOLATION,
            # Both enforced per turn by the ISOLATED_PROFILE permission profile
            # (and fail closed when the installed SDK cannot pass it). They
            # compose with TOOL_ISOLATION: the profile then confines the turn
            # inside the bubblewrap sandbox.
            ISOLATED_TURN,
            READ_ONLY_WORKSPACE,
        }

    def _complete_validated(
        self,
        prompt: str,
        model_type: type[BaseModel],
        *,
        purpose: str,
        workspace: Path | None = None,
        isolated: bool = False,
    ) -> Any:
        """Run one structured turn and repair malformed/schema-invalid JSON once.

        The OpenAI-compatible provider already has this bounded repair pass.
        Keeping the same behavior here prevents a transient invalid escape or
        lone Unicode surrogate in model-authored Markdown from failing an
        otherwise retryable background job.
        """

        output_schema = strict_output_schema(model_type)
        remaining = output_limit()

        def run_turn(turn_prompt, *, turn_purpose):
            nonlocal remaining
            if remaining is not None and remaining <= 0:
                raise AIOutputTruncated("No generation budget remains for Codex JSON repair.")
            meter = UsageMeter(self)
            result = None
            try:
                with generation_limit(remaining):
                    if workspace is None and not isolated:
                        result = self._run_structured(turn_prompt, output_schema, purpose=turn_purpose)
                    else:
                        # JSON repairs and regenerations stay isolated too.
                        result = self._run_structured(
                            turn_prompt, output_schema, purpose=turn_purpose, workspace=workspace, isolated=True,
                        )
                return result
            finally:
                if remaining is not None:
                    estimate = max(1, (len(result) + 3) // 4) if result is not None else 0
                    remaining = max(0, remaining - meter.output_charge(estimate))

        try:
            text = run_turn(prompt, turn_purpose=purpose)
        except CodexUnavailable as first_exc:
            # Some app-server/model combinations reject malformed structured
            # output before exposing a final_response to the SDK. In that case
            # the ordinary validation repair below never gets a chance to run.
            # Retry only the narrow family of JSON string/escape failures; a
            # genuinely unavailable provider must retain its original error.
            if single_request_active() or not _is_structured_json_transport_error(first_exc):
                raise
            _log_codex_debug(
                "codex.structured_output_regenerate",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                error=str(first_exc),
            )
            text = run_turn(
                structured_output_regeneration_prompt(prompt),
                turn_purpose=f"{purpose}_json_regenerate",
            )
        try:
            return model_type.model_validate_json(text)
        except (ValidationError, ValueError, json.JSONDecodeError) as first_exc:
            reason = describe_wire_validation_error(model_type, first_exc)
            if single_request_active():
                raise AIInvalidOutput(
                    f"Codex returned invalid {model_type.__name__} JSON: {reason}"
                ) from first_exc
            _log_codex_debug(
                "codex.structured_output_repair",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                error=str(first_exc),
                reason=reason,
            )
            repaired = run_turn(
                structured_output_repair_prompt(text, model_type, reason=reason),
                turn_purpose=f"{purpose}_json_repair",
            )
            try:
                return model_type.model_validate_json(repaired)
            except (ValidationError, ValueError, json.JSONDecodeError) as second_exc:
                # Name the model and the offending field. A forbidden extra is
                # a contract divergence someone has to resolve in
                # the feature-owned AI contract; a raw pydantic dump buried in a generic
                # "invalid JSON" is what let F2 hide for 43 attempts.
                raise AIInvalidOutput(
                    f"Codex returned invalid {model_type.__name__} JSON after one repair "
                    f"attempt: {describe_wire_validation_error(model_type, second_exc)}"
                ) from second_exc

    @observed_sdk_turn
    def _run_structured(
        self,
        prompt: str,
        output_schema: dict[str, Any],
        *,
        purpose: str,
        timeout_seconds: float | None = None,
        workspace: Path | None = None,
        isolated: bool = False,
    ) -> str:
        """Run one SDK turn.

        An isolated turn (``isolated``, implied by ``workspace``) never starts
        in ``vault_root``: the app server, thread and turn start in the
        workspace, or in a fresh empty directory removed afterwards, under
        :data:`ISOLATED_PROFILE` (:func:`isolated_turn_overrides`), which can
        read only that directory and the platform minimum. A workspace turn
        keeps the shell tool to read its files; any other isolated turn has no
        tools. The thread is never given a sandbox mode, which would replace
        the profile with Codex's full-disk-read ``read-only`` mode, and the turn
        fails closed when the installed SDK cannot pass the overrides.

        Under :func:`learnloop.ai.isolation.tool_isolation` (project routes)
        the app server also runs in that bubblewrap sandbox, which mounts only
        its working directory from the host. A turn there starts in that
        directory; an isolated turn's empty directory is made inside it, and a
        workspace outside it is refused (the sandbox could not show it).
        """
        if single_request_active():
            # A Python SDK turn delegates model requests to the app-server.
            # This adapter has no verified per-physical-request retry control;
            # bounding our turn count cannot bound its paid model attempts.
            raise CodexUnavailable(
                "Codex SDK cannot guarantee a single physical model request; "
                "use an OpenAI-compatible chat provider for caller-budgeted requests."
            )
        budget = output_limit()
        if budget is not None:
            # The app-server protocol has no hard per-turn output-token cap.
            # Keep the target explicit; domain gates enforce the returned
            # artifact limit and receipts retain the actual billed usage.
            prompt += f"\n\nKeep the complete JSON response within {budget} output tokens."
        if self._interrupt_requested.is_set():
            raise CodexInterrupted("Codex turn interrupted by the learner.")
        sandbox = current_tool_isolation()
        sandbox_root = Path(sandbox.workdir).resolve() if sandbox is not None else None
        isolated = isolated or workspace is not None
        scratch_root: Path | None = None
        if workspace is not None:
            workspace = Path(workspace).resolve()
            if not workspace.is_dir():
                raise CodexUnavailable(f"Read-only workspace {workspace} is not a directory.")
            if sandbox_root is not None and workspace != sandbox_root and sandbox_root not in workspace.parents:
                raise CodexUnavailable(
                    f"Read-only workspace {workspace} is outside the sandboxed working directory "
                    f"{sandbox_root}, so the sandboxed turn could not read it."
                )
            self._last_workspace_activity = None
            root = workspace
        elif isolated:
            # Nothing to read: an empty directory of its own, never the vault.
            # Sandboxed, it must sit in the one host directory bubblewrap mounts.
            scratch_root = Path(tempfile.mkdtemp(prefix="learnloop-isolated-turn-", dir=sandbox_root)).resolve()
            root = scratch_root
        elif sandbox is not None:
            root = Path(sandbox.workdir)
        else:
            root = self.vault_root
        cwd = str(root)
        try:
            return self._run_sdk_turn(
                prompt, output_schema, purpose=purpose, timeout_seconds=timeout_seconds,
                cwd=cwd, root=root, isolated=isolated, workspace=workspace, sandbox=sandbox,
            )
        finally:
            if scratch_root is not None:
                shutil.rmtree(scratch_root, ignore_errors=True)

    def _run_sdk_turn(
        self,
        prompt: str,
        output_schema: dict[str, Any],
        *,
        purpose: str,
        timeout_seconds: float | None,
        cwd: str,
        root: Path,
        isolated: bool,
        workspace: Path | None,
        sandbox: ToolIsolation | None = None,
    ) -> str:
        requested_timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else self.__dict__.get("_request_timeout_seconds")
        )
        turn_timeout = (
            float(self.config.timeout_seconds)
            if requested_timeout is None
            else max(0.001, float(requested_timeout))
        )
        _ensure_sdk_importable(self.sdk_python_path)
        try:
            from openai_codex import Codex
            from openai_codex import CodexConfig as SdkAppConfig
            from openai_codex.types import Personality, ReasoningEffort, ReasoningSummary
        except ImportError as exc:
            raise CodexUnavailable(
                f"Codex Python SDK is not importable from {self.sdk_python_path}."
            ) from exc

        # Slice 1's permission profile first: its ``--config`` overrides go
        # into the Codex command (or the SDK's config_overrides, which the SDK
        # appends to the program it launches). The project bubblewrap sandbox
        # (below) then wraps that whole command, so a sandboxed isolated turn
        # runs under both: bubblewrap bounds the app-server process, and the
        # profile bounds the turn's tools within it.
        launch_args = _sdk_launch_args(self.config.sdk_launch_command)
        config_kwargs: dict[str, Any] = {}
        if isolated:
            overrides = isolated_turn_overrides(
                root, shell=workspace is not None, mcp_server_ids=self._configured_mcp_server_ids(root),
            )
            if launch_args:
                position = launch_args.index("app-server") if "app-server" in launch_args else -1
                if position < 0:
                    raise CodexUnavailable(
                        "sdk_launch_command does not name `app-server`; an isolated turn cannot pass its sandbox overrides."
                    )
                flags = tuple(part for override in overrides for part in ("--config", override))
                launch_args = (*launch_args[:position], *flags, *launch_args[position:])
            elif _sdk_accepts(SdkAppConfig, "config_overrides"):
                config_kwargs["config_overrides"] = tuple(overrides)
            else:
                raise CodexUnavailable(
                    "The installed Codex SDK cannot pass config overrides; "
                    "an isolated turn (read boundary, tools off) is unavailable."
                )

        launcher_dir = tempfile.mkdtemp(prefix="learnloop-codex-launch-") if sandbox is not None else None
        try:
            effort = _sdk_reasoning_effort(
                ReasoningEffort, self.__dict__.get("_request_reasoning_effort") or self.config.reasoning_effort)
            summary = _sdk_reasoning_summary(ReasoningSummary, self.config.reasoning_summary)
            codex_bin = _resolved_sdk_codex_bin(self.config.sdk_codex_bin)
            if sandbox is not None and launcher_dir is not None:
                codex_bin, launch_args = _isolated_launch(sandbox, codex_bin, launch_args, Path(launcher_dir))
            app_config = SdkAppConfig(
                codex_bin=codex_bin,
                launch_args_override=launch_args,
                cwd=cwd,
                client_name="learnloop",
                client_title="LearnLoop",
                **config_kwargs,
            )
            _log_codex_debug(
                "codex.prompt",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                cwd=cwd,
                read_only_workspace=workspace is not None,
                isolated=isolated,
                sandboxed=sandbox is not None,
                service_name=f"learnloop:{purpose}",
                reasoning_effort=self.__dict__.get("_request_reasoning_effort") or self.config.reasoning_effort,
                reasoning_summary=self.config.reasoning_summary,
                prompt=prompt,
                prompt_length=len(prompt),
                output_schema=output_schema,
            )
            with Codex(config=app_config) as codex:
                # Never a ``sandbox`` here: a sandbox mode on thread start
                # replaces the isolated permission profile with Codex's
                # full-disk-read built-in mode.
                thread = codex.thread_start(
                    cwd=cwd,
                    model=self.config.model or None,
                    service_name=f"learnloop:{purpose}",
                )
                turn = thread.turn(
                    prompt,
                    cwd=cwd,
                    model=self.config.model or None,
                    effort=effort,
                    output_schema=output_schema,
                    personality=Personality.pragmatic,
                    summary=summary,
                )
                with self._turn_lock:
                    self._active_turn = turn
                    self._active_codex = codex
                    self._active_stop_scheduled = False
                    self._deadline_expired.clear()
                    deadline_timer = threading.Timer(
                        turn_timeout,
                        self._expire_turn,
                        args=(turn, codex),
                    )
                    deadline_timer.daemon = True
                    self._active_deadline_timer = deadline_timer
                    deadline_timer.start()
                try:
                    if self._interrupt_requested.is_set():
                        self._schedule_turn_stop(turn, codex)
                    result = turn.run()
                finally:
                    with self._turn_lock:
                        if self._active_turn is turn:
                            self._active_turn = None
                            self._active_codex = None
                            if self._active_deadline_timer is not None:
                                self._active_deadline_timer.cancel()
                            if self._active_force_close_timer is not None:
                                self._active_force_close_timer.cancel()
                            self._active_deadline_timer = None
                            self._active_force_close_timer = None
                            self._active_stop_scheduled = False
        except CodexInterrupted:
            raise
        except CodexTurnTimeout:
            raise
        except ToolIsolationUnavailable as exc:
            # Fail closed: an isolated request never runs unconfined.
            raise CodexUnavailable(str(exc)) from exc
        except Exception as exc:
            if self._deadline_expired.is_set():
                raise CodexTurnTimeout(
                    f"Codex SDK turn exceeded its {turn_timeout:g}-second deadline."
                ) from exc
            if self._interrupt_requested.is_set():
                raise CodexInterrupted("Codex turn interrupted by the learner.") from exc
            _log_codex_debug(
                "codex.error",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                cwd=cwd,
                error=str(exc),
            )
            raise CodexUnavailable(str(exc)) from exc
        finally:
            if launcher_dir is not None:
                shutil.rmtree(launcher_dir, ignore_errors=True)

        # A7 (spec_diagnostic_augmentation_v1.md §2): meter before the
        # deadline/interrupt/empty-response checks below. A turn the learner
        # interrupted or that timed out still burned tokens, and a cost meter
        # that only counts clean completions understates every ratio built on it.
        report_call_usage(receipt_fields_from_codex_turn(result))
        self.record_token_usage(*usage_from_codex_turn(result))
        if workspace is not None:
            self._last_workspace_activity = _workspace_activity(result)

        if self._deadline_expired.is_set():
            raise CodexTurnTimeout(
                f"Codex SDK turn exceeded its {turn_timeout:g}-second deadline."
            )
        if self._interrupt_requested.is_set():
            raise CodexInterrupted("Codex turn interrupted by the learner.")

        final_response = result.final_response
        _log_codex_debug(
            "codex.response",
            provider="codex",
            provider_type=self.provider_type,
            purpose=purpose,
            model=self.config.model,
            cwd=cwd,
            response=final_response,
            response_length=len(final_response) if final_response is not None else None,
        )
        if final_response is None:
            raise CodexUnavailable("Codex SDK turn completed without a final response.")
        return final_response.strip()

def _sdk_accepts(config_type: Any, field_name: str) -> bool:
    """Whether the SDK's app-server config type takes ``field_name``."""

    if dataclasses.is_dataclass(config_type):
        return any(field.name == field_name for field in dataclasses.fields(config_type))
    try:
        parameters = inspect.signature(config_type).parameters
    except (TypeError, ValueError):
        return False
    return field_name in parameters or any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD for parameter in parameters.values()
    )


#: Turn items that carry text only (no tool ran, nothing was read), by their
#: type with case, ``_`` and ``-`` dropped.
_TEXT_ONLY_TURN_ITEMS = frozenset(
    {"agentmessage", "reasoning", "usermessage", "plan", "todolist", "error", "contextcompaction"}
)
#: Reported for a turn item that names no command or path and is not text
#: only: a tool this extractor cannot read. A snapshot diagnosis's record
#: counts it as reading the whole workspace (diagnosis input provenance).
UNACCOUNTED_TURN_ITEM = "unaccounted turn item"


def _workspace_activity(result: Any) -> list[str] | None:
    """Commands or paths the agent's tool items reported, when exposed.

    Fail closed (diagnosis input provenance): an item that names no command
    or path and is not text only is reported as :data:`UNACCOUNTED_TURN_ITEM`
    with its type, never dropped, so what it read is never recorded as
    nothing."""

    items = getattr(result, "items", None)
    if not isinstance(items, (list, tuple)):
        return None
    activity: list[str] = []
    for item in items:
        # A typed SDK item may arrive wrapped (a pydantic root model).
        item = getattr(item, "root", item)
        named = False
        for key in ("command", "path", "file_path"):
            value = item.get(key) if isinstance(item, dict) else getattr(item, key, None)
            if isinstance(value, (list, tuple)):
                value = " ".join(str(part) for part in value)
            if isinstance(value, str) and value.strip():
                activity.append(value.strip())
                named = True
        if named:
            continue
        kind = item.get("type") if isinstance(item, dict) else getattr(item, "type", None)
        label = str(kind or type(item).__name__)
        if label.replace("_", "").replace("-", "").lower() not in _TEXT_ONLY_TURN_ITEMS:
            activity.append(f"{UNACCOUNTED_TURN_ITEM}: {label}")
    return activity


def _is_structured_json_transport_error(exc: BaseException) -> bool:
    """Whether app-server failed before returning malformed structured output."""

    message = str(exc).lower()
    return any(
        marker in message
        for marker in (
            "hex escape",
            "invalid escape",
            "unicode escape",
            "invalid json",
            "json parse",
            "json syntax",
        )
    )


def _bundled_codex_path() -> str | None:
    try:
        from codex_cli_bin import bundled_codex_path

        return str(bundled_codex_path())
    except (ImportError, FileNotFoundError):
        return None


def _isolated_launch(
    isolation: Any,
    codex_bin: str | None,
    launch_args: tuple[str, ...] | None,
    launcher_dir: Path,
) -> tuple[str | None, tuple[str, ...] | None]:
    """The SDK launch settings that run the app-server inside the sandbox.

    A full launch command (``sdk_launch_command``) is wrapped as a whole. A
    program path gets a launcher that execs bubblewrap around it, so the SDK
    can still append its own app-server arguments. Raises
    ``ToolIsolationUnavailable`` rather than launching unconfined.
    """

    if launch_args:
        return None, tuple(sandboxed_command(isolation, list(launch_args)))
    program = codex_bin or _bundled_codex_path() or shutil.which("codex.cmd" if os.name == "nt" else "codex")
    if not program:
        raise ToolIsolationUnavailable("the Codex executable was not found, so it cannot be sandboxed")
    return str(write_launcher(launcher_dir, isolation, program)), None


def _sdk_reasoning_effort(reasoning_effort_type: Any, value: str | None) -> Any:
    normalized = (value or "").strip().lower()
    if not normalized:
        return None
    try:
        return reasoning_effort_type(normalized)
    except ValueError as exc:
        valid = ", ".join(item.value for item in reasoning_effort_type)
        raise CodexUnavailable(f"Invalid codex.reasoning_effort {value!r}; expected one of: {valid}") from exc


def _sdk_reasoning_summary(reasoning_summary_type: Any, value: str | None) -> Any:
    normalized = (value or "").strip().lower()
    if not normalized:
        return None
    try:
        return reasoning_summary_type.model_validate(normalized)
    except Exception as exc:
        raise CodexUnavailable(
            f"Invalid codex.reasoning_summary {value!r}; expected none, auto, concise, or detailed"
        ) from exc

def _ensure_sdk_importable(sdk_python_path: Path) -> None:
    if sdk_python_path.exists():
        value = str(sdk_python_path)
        if value not in sys.path:
            sys.path.insert(0, value)


def _sdk_launch_args(command: str) -> tuple[str, ...] | None:
    if not command.strip():
        return None
    return tuple(shlex.split(command, posix=os.name != "nt"))


def _resolved_sdk_codex_bin(configured: str | None) -> str | None:
    """Prefer an explicit/pinned SDK runtime, with a source-checkout fallback.

    LearnLoop can import the SDK straight from a Codex source checkout. Such a
    checkout does not necessarily install the SDK's optional
    ``openai-codex-cli-bin`` package, so leaving ``codex_bin`` unset would make
    every tutor/authoring call fail before launch. When the pinned package is
    present the SDK resolves it itself; otherwise use the installed CLI.
    """

    if (configured or "").strip():
        return str(configured).strip()
    try:
        from codex_cli_bin import bundled_codex_path

        bundled_codex_path()
        return None
    except (ImportError, FileNotFoundError):
        return shutil.which("codex.cmd" if os.name == "nt" else "codex")


def _resolve_checkout_path(vault_root: Path, checkout_path: str) -> Path:
    raw = Path(checkout_path)
    if raw.is_absolute():
        return raw.resolve()
    return (vault_root / raw).resolve()


def _resolve_sdk_python_path(checkout_path: Path, sdk_python_path: str) -> Path:
    raw = Path(sdk_python_path)
    if raw.is_absolute():
        return raw.resolve()
    return (checkout_path / raw).resolve()


def _log_codex_debug(event: str, **fields: Any) -> None:
    """Emit full Codex request/response data into sidecar debug logs.

    The sidecar JSONL formatter treats ``event_fields`` specially. Keeping this
    helper in the core client avoids coupling Codex transport code back to the
    Tauri sidecar package while still making debug logs capture each prompt and
    response when sidecar debug logging is enabled.
    """

    if not LOG.isEnabledFor(logging.DEBUG):
        return
    LOG.debug(event, extra={EVENT_FIELDS_ATTR: {k: v for k, v in fields.items() if v is not None}})

CodexRuntimeState = Literal[
    "codex_missing",
    "codex_revision_mismatch",
    "codex_unavailable",
    "codex_auth_required",
    "ready",
]

PINNED_REVISION_PLACEHOLDER = "<pinned-commit>"


class CodexHealthChecker(Protocol):
    def __call__(self, checkout_path: Path, config: CodexConfig) -> None:
        ...


class CodexStartupProcess(Protocol):
    def poll(self) -> int | None:
        ...


class CodexStartupRunner(Protocol):
    def __call__(self, checkout_path: Path, config: CodexConfig) -> CodexStartupProcess:
        ...


class CodexAuthRequired(RuntimeError):
    pass


class CodexHealthUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class CodexRuntimeReport:
    status: CodexRuntimeState
    checkout_path: str
    configured_revision: str
    actual_revision: str | None = None
    message: str | None = None

    @property
    def ready(self) -> bool:
        return self.status == "ready"

    def as_dict(self) -> dict[str, str | bool | None]:
        return {
            "status": self.status,
            "ready": self.ready,
            "checkout_path": self.checkout_path,
            "configured_revision": self.configured_revision,
            "actual_revision": self.actual_revision,
            "message": self.message,
        }


def check_codex_runtime(
    vault_root: Path,
    config: CodexConfig,
    *,
    healthcheck: CodexHealthChecker | None = None,
    startup: CodexStartupRunner | None = None,
) -> CodexRuntimeReport:
    configured_revision = config.revision
    if not (config.checkout_path or "").strip():
        return CodexRuntimeReport(
            status="codex_missing",
            checkout_path="",
            configured_revision=configured_revision,
            message=(
                "Codex checkout path is not configured. Set "
                "LEARNLOOP_CODEX_CHECKOUT_PATH in your global learnloop settings "
                "(~/.config/learnloop/settings.env)."
            ),
        )
    checkout_path = _resolve_checkout_path(vault_root, config.checkout_path)
    if not checkout_path.exists():
        return CodexRuntimeReport(
            status="codex_missing",
            checkout_path=str(checkout_path),
            configured_revision=configured_revision,
            message="Codex checkout path does not exist.",
        )
    if not checkout_path.is_dir():
        return CodexRuntimeReport(
            status="codex_missing",
            checkout_path=str(checkout_path),
            configured_revision=configured_revision,
            message="Codex checkout path is not a directory.",
        )

    actual_revision = _read_checkout_revision(checkout_path)
    if _requires_revision_match(configured_revision):
        if actual_revision is None:
            return CodexRuntimeReport(
                status="codex_unavailable",
                checkout_path=str(checkout_path),
                configured_revision=configured_revision,
                actual_revision=None,
                message="Could not determine Codex checkout revision.",
            )
        if not actual_revision.startswith(configured_revision):
            return CodexRuntimeReport(
                status="codex_revision_mismatch",
                checkout_path=str(checkout_path),
                configured_revision=configured_revision,
                actual_revision=actual_revision,
                message="Codex checkout revision does not match configuration.",
            )

    healthcheck = healthcheck or (default_sdk_healthcheck if config.provider.lower() == "sdk" else default_http_healthcheck)
    startup = startup or default_startup

    try:
        healthcheck(checkout_path, config)
    except CodexAuthRequired as exc:
        return CodexRuntimeReport(
            status="codex_auth_required",
            checkout_path=str(checkout_path),
            configured_revision=configured_revision,
            actual_revision=actual_revision,
            message=str(exc) or "Codex authentication is required.",
        )
    except (CodexHealthUnavailable, TimeoutError, OSError, subprocess.SubprocessError) as exc:
        if config.provider.lower() == "sdk" or not config.startup_command:
            return CodexRuntimeReport(
                status="codex_unavailable",
                checkout_path=str(checkout_path),
                configured_revision=configured_revision,
                actual_revision=actual_revision,
                message=str(exc) or "Codex healthcheck failed.",
            )
        try:
            process = startup(checkout_path, config)
            _wait_for_startup_health(checkout_path, config, healthcheck, process)
        except CodexAuthRequired as startup_exc:
            return CodexRuntimeReport(
                status="codex_auth_required",
                checkout_path=str(checkout_path),
                configured_revision=configured_revision,
                actual_revision=actual_revision,
                message=str(startup_exc) or "Codex authentication is required.",
            )
        except (CodexHealthUnavailable, TimeoutError, OSError, subprocess.SubprocessError) as startup_exc:
            return CodexRuntimeReport(
                status="codex_unavailable",
                checkout_path=str(checkout_path),
                configured_revision=configured_revision,
                actual_revision=actual_revision,
                message=str(startup_exc) or str(exc) or "Codex startup or healthcheck failed.",
            )
    return CodexRuntimeReport(
        status="ready",
        checkout_path=str(checkout_path),
        configured_revision=configured_revision,
        actual_revision=actual_revision,
        message="Codex runtime is ready.",
    )


def default_startup(checkout_path: Path, config: CodexConfig) -> subprocess.Popen:
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.Popen(
        config.startup_command,
        cwd=checkout_path,
        shell=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )


def _wait_for_startup_health(
    checkout_path: Path,
    config: CodexConfig,
    healthcheck: CodexHealthChecker,
    process: CodexStartupProcess,
) -> None:
    deadline = time.monotonic() + max(0, config.startup_timeout_seconds)
    last_error: Exception | None = None
    while True:
        try:
            healthcheck(checkout_path, config)
            return
        except CodexAuthRequired:
            raise
        except (CodexHealthUnavailable, TimeoutError, OSError, subprocess.SubprocessError) as exc:
            last_error = exc

        return_code = process.poll()
        if return_code is not None:
            raise CodexHealthUnavailable(f"Codex startup command exited with status {return_code}.")
        if time.monotonic() >= deadline:
            suffix = f": {last_error}" if last_error else "."
            raise CodexHealthUnavailable(f"Codex startup or healthcheck timed out{suffix}")
        time.sleep(min(0.2, max(0.0, deadline - time.monotonic())))


def default_http_healthcheck(_checkout_path: Path, config: CodexConfig) -> None:
    request = urllib.request.Request(
        _url(config.base_url, config.healthcheck_path),
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=config.healthcheck_timeout_seconds) as response:
            payload = response.read(65536)
            status_code = response.status
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403}:
            raise CodexAuthRequired("Codex app-server authentication is required.") from exc
        raise CodexHealthUnavailable(f"Codex healthcheck HTTP {exc.code}.") from exc
    except urllib.error.URLError as exc:
        raise CodexHealthUnavailable(str(exc.reason)) from exc

    if status_code >= 400:
        raise CodexHealthUnavailable(f"Codex healthcheck HTTP {status_code}.")
    if not payload:
        return
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexHealthUnavailable("Codex healthcheck returned invalid JSON.") from exc
    state = str(data.get("status") or data.get("state") or "ready").lower()
    if state in {"ready", "ok", "healthy"}:
        return
    if state in {"auth_required", "unauthorized", "login_required"}:
        raise CodexAuthRequired(data.get("message") or "Codex authentication is required.")
    raise CodexHealthUnavailable(data.get("message") or f"Codex runtime is not ready: {state}")


def default_sdk_healthcheck(checkout_path: Path, config: CodexConfig) -> None:
    sdk_path = _resolve_sdk_python_path(checkout_path, config.sdk_python_path)
    if sdk_path.exists():
        value = str(sdk_path)
        if value not in sys.path:
            sys.path.insert(0, value)
    try:
        from openai_codex import Codex, CodexConfig  # noqa: F401
    except ImportError as exc:
        raise CodexHealthUnavailable(f"Codex Python SDK is not importable from {sdk_path}.") from exc


def _url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def _resolve_checkout_path(vault_root: Path, checkout_path: str) -> Path:
    raw = Path(checkout_path)
    if raw.is_absolute():
        return raw.resolve()
    return (vault_root / raw).resolve()


def _requires_revision_match(revision: str) -> bool:
    return bool(revision and revision != PINNED_REVISION_PLACEHOLDER)


def _read_checkout_revision(checkout_path: Path) -> str | None:
    git_dir = checkout_path / ".git"
    if not git_dir.exists():
        head = checkout_path / "HEAD"
        if head.exists():
            return head.read_text(encoding="utf-8").strip() or None
        return None
    result = subprocess.run(
        ["git", "-C", str(checkout_path), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _resolve_sdk_python_path(checkout_path: Path, sdk_python_path: str) -> Path:
    raw = Path(sdk_python_path)
    if raw.is_absolute():
        return raw.resolve()
    return (checkout_path / raw).resolve()

def codex_config_from_ai_profile(profile: AIProviderConfig) -> CodexConfig:
    provider = "http" if profile.type in {"http", "http_adapter"} else "sdk"
    return CodexConfig(
        provider=provider,
        # Left blank when unset so the runtime check surfaces a clear
        # "configure LEARNLOOP_CODEX_CHECKOUT_PATH" message instead of silently
        # resolving a stale relative default.
        checkout_path=profile.checkout_path or "",
        revision=profile.revision or "<pinned-commit>",
        startup_command=profile.startup_command or "",
        startup_timeout_seconds=profile.startup_timeout_seconds or 20,
        healthcheck_timeout_seconds=profile.healthcheck_timeout_seconds or profile.timeout_seconds or 5,
        timeout_seconds=profile.timeout_seconds or 180,
        model=profile.model or "gpt-5.6-sol",
        reasoning_effort=profile.reasoning_effort or "low",
        reasoning_summary=profile.reasoning_summary or "none",
        sdk_python_path=profile.sdk_python_path or "sdk/python/src",
        sdk_codex_bin=profile.sdk_codex_bin or "",
        sdk_launch_command=profile.sdk_launch_command or "",
        base_url=profile.base_url or "http://127.0.0.1:8765",
        healthcheck_path=profile.healthcheck_path or "/health",
        authoring_path=profile.authoring_path or "/authoring-proposal",
        canonical_ingest_path=profile.canonical_ingest_path or "/canonical-ingest",
        grading_path=profile.grading_path or "/grading-proposal",
        tutor_qa_path=profile.tutor_qa_path or "/tutor-qa",
        teach_back_path=profile.teach_back_path or "/teach-back",
        teach_back_authoring_path=profile.teach_back_authoring_path or "/teach-back-authoring",
        misconception_match_path=profile.misconception_match_path or "/misconception-match",
    )


class CodexSDKProviderClient(SdkCodexClient):
    provider_type = "codex_sdk"

    def __init__(self, provider_name: str, profile: AIProviderConfig, vault_root: Path):
        super().__init__(codex_config_from_ai_profile(profile), vault_root)
        # Preserve the configured profile identity (codex_low/codex_medium/etc.)
        # in run provenance; the transport base names only the implementation.
        self.provider_name = provider_name
        self.model = profile.model or self.config.model

def make_codex_client(config: CodexConfig, vault_root: Path) -> Any:
    """Build the legacy Codex selection from the relocated providers."""

    provider = config.provider.lower()
    if provider == "http":
        from learnloop.ai.providers.codex_http import HttpCodexClient

        return HttpCodexClient(config)
    if provider == "sdk":
        return SdkCodexClient(config, vault_root)
    raise AIProviderUnavailable(f"Unsupported Codex provider {config.provider!r}")
