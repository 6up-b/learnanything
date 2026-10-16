"""The ``chatgpt_plan`` transport: OpenAI models billed to the owner's ChatGPT plan.

A structured call is one streamed Responses request (``store=false``, no
tools, no files): an isolated turn by construction, with none of Codex's
process start-up. Structured output uses the Responses ``text.format``
(``json_schema``, strict) by default, or JSON mode plus one repair
(``response_format = "json_object"``).

A read-only-workspace call (a snapshot diagnosis) is the one exception: the
workspace is served by LearnLoop (``learnloop.ai.chatgpt_plan.workspace``),
by function calling (one request per round of calls, at most
``max_tool_rounds`` rounds, then one request asking for the answer) or inline.
Every file served is recorded as the call runs, so
:meth:`ChatGPTPlanProviderClient.workspace_activity` names exactly what the
model was given. Each round is its own physical request and receipt.

Billing is ``subscription`` (Slice A plan §5 rule 6): there is no marginal
dollar cost, so callers estimate cost from the usage reported here and keep
their call caps. Every physical request is its own child receipt naming the
provider, the profile's model and the model that answered.

A caller's output budget (``generation_limit``) goes with every physical
request of a call: the plan route takes no ``max_output_tokens``, so each
prompt states it once and each request's receipt records it as that
request's ``output_budget_tokens``. The JSON repair is sent with the budget
of the request it repairs, never without one (final verification F9).

Under ``single_request()`` one ``complete()`` sends at most one request: no
retry, no token-refresh retry and no JSON repair. An interrupt or the deadline
stops a call at every step, including while it waits for a token refresh; a
request is never sent after either. Otherwise a transient
failure (network, 5xx, ``subscription_sharing_usage_unavailable``) is retried
with bounded backoff inside the caller's deadline, and a 401 refreshes the
token once. A usage-limit error pauses the plan (``plan usage exhausted``):
later requests are refused locally until the pause ends, so routes that allow
fallback fall back and a retrying caller never hammers the plan.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
import random
import threading
import time
from typing import Any

from pydantic import BaseModel, ValidationError

from learnloop.ai.chatgpt_plan.oauth import EndpointUnreachable, urllib_call
from learnloop.ai.chatgpt_plan.responses import (
    ResponsesError,
    ResponsesStream,
    StreamCancelled,
    StreamIncomplete,
    StreamResult,
    echo_items,
    error_fields,
    function_calls,
    request_body,
)
from learnloop.ai.chatgpt_plan.workspace import (
    INSTRUCTIONS_INLINE,
    INSTRUCTIONS_TOOLS,
    NAMESPACE,
    ServedWorkspace,
    WorkspaceTooLarge,
)
from learnloop.ai.chatgpt_plan.session import (
    MANAGE_USAGE_URL,
    ChatGPTPlanNotEligible,
    ChatGPTPlanUsageExhausted,
    PlanSession,
)
from learnloop.ai.errors import AIInterrupted, AIInvalidOutput, AIOutputTruncated, AIProviderUnavailable, AITurnTimeout
from learnloop.ai.execution import model_call, report_call_usage, single_request_active
from learnloop.ai.isolation import TOOL_FREE
from learnloop.ai.strict_schema import strict_output_schema
from learnloop.ai.transport import (
    BOUNDED_STRUCTURED_COMPLETION,
    INTERRUPT,
    ISOLATED_TURN,
    READ_ONLY_WORKSPACE,
    STRUCTURED_COMPLETION,
    StructuredRequest,
)
from learnloop.ai.usage import TokenUsageAccounting
from learnloop.config import AIProviderConfig
from learnloop.config.schema import CHATGPT_PLAN_API_BASE_URL

logger = logging.getLogger(__name__)

PROVIDER_TYPE = "chatgpt_plan"
DEFAULT_TIMEOUT_SECONDS = 180.0
_MAX_ATTEMPTS = 3
_BACKOFF_SECONDS = (1.0, 2.0)
_MIN_ATTEMPT_SECONDS = 1.0
_JSON_ONLY = "Return only valid JSON. Do not include Markdown fences."
_TRANSIENT_CODES = frozenset({
    "subscription_sharing_usage_unavailable", "subscription_sharing_user_unavailable",
    "server_error", "rate_limit_exceeded", "stream_ended",
})
_TRANSIENT_STATUSES = frozenset({408, 409, 429, 500, 502, 503, 504})
_CONFIG_CODES = frozenset({
    "subscription_sharing_unsupported_capability", "subscription_sharing_route_not_supported",
    "chatpass_v2_scope_not_authorized", "chatpass_v2_invalid_authorization_context",
})

# Module-level so tests can replace time and randomness.
_sleep = time.sleep
_monotonic = time.monotonic
_random = random.random


class ChatGPTPlanRequestRejected(AIProviderUnavailable):
    """The route refused this request's shape or this client; retrying the same body cannot help."""


class ChatGPTPlanTransient(AIProviderUnavailable):
    """A network, server or availability failure; the credentials are kept."""


class ChatGPTPlanUnauthorized(AIProviderUnavailable):
    """The access token was not accepted (401); the next request refreshes it first."""


class ChatGPTPlanProviderClient(TokenUsageAccounting):
    provider_type = PROVIDER_TYPE

    def __init__(self, provider_name: str, profile: AIProviderConfig, *, session: PlanSession | None = None) -> None:
        self.provider_name = provider_name
        self.profile = profile
        self.model = profile.model
        if not self.model:
            raise AIProviderUnavailable(
                f"AI provider {provider_name!r} is missing model; pick one from `learnloop ai models chatgpt`."
            )
        if getattr(profile, "enabled", True) is False:
            raise AIProviderUnavailable(f"AI provider {provider_name!r} is disabled (enabled = false).")
        self.base_url = (profile.base_url or CHATGPT_PLAN_API_BASE_URL).rstrip("/")
        self.default_base_url = self.base_url
        self.response_format = getattr(profile, "response_format", None) or "json_schema"
        self.pause_minutes = int(getattr(profile, "usage_limit_pause_minutes", None) or 15)
        self.workspace_mode = getattr(profile, "workspace_mode", None) or "tools"
        self.max_tool_rounds = int(getattr(profile, "max_tool_rounds", None) or 16)
        self.max_entry_chars = int(getattr(profile, "max_entry_chars", None) or 24_000)
        self.max_workspace_chars = int(getattr(profile, "max_workspace_chars", None) or 400_000)
        self.session = session or PlanSession()
        self._interrupted = threading.Event()
        self._active: ResponsesStream | None = None
        self._active_lock = threading.Lock()
        #: The last read-only-workspace turn's record (None before the first).
        self._workspace: ServedWorkspace | None = None
        #: Timing of the last physical request (seconds), for `learnloop ai latency`.
        self.last_timing: dict[str, float | None] | None = None

    # -- capabilities ----------------------------------------------------
    def supports(self, capability: str) -> bool:
        # A Responses request sees the prompt and nothing else; a workspace
        # turn adds only the files LearnLoop serves (no shell, no network).
        return capability in {
            STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION, "complete", "structured",
            ISOLATED_TURN, TOOL_FREE, INTERRUPT, READ_ONLY_WORKSPACE,
        }

    def workspace_activity(self) -> list[str] | None:
        """The paths (relative to the workspace root) the last workspace turn served.

        Exact by construction: LearnLoop served every file the model was given
        and recorded it as the call ran (``ServedWorkspace``). A listing is
        names only and a refused call serves nothing, so neither appears.
        ``None`` before any workspace turn.
        """

        return self._workspace.activity() if self._workspace is not None else None

    def workspace_record(self) -> dict[str, Any] | None:
        """The last workspace turn's full record: every call and every served range."""

        workspace = self._workspace
        if workspace is None:
            return None
        return {
            "mode": self.workspace_mode,
            **workspace.summary(),
            "served": [entry.as_dict() for entry in workspace.served],
            "calls": [call.as_dict() for call in workspace.calls],
        }

    def interrupt(self) -> bool:
        self._interrupted.set()
        with self._active_lock:
            active = self._active
        if active is not None:
            active.cancel("interrupt")
        return True

    # -- structured completion --------------------------------------------
    def complete(self, request: StructuredRequest[Any]) -> Any:
        timeout = float(request.timeout_seconds or self.profile.timeout_seconds or DEFAULT_TIMEOUT_SECONDS)
        deadline = _monotonic() + timeout
        model_type = request.result_model
        budget = request.output_budget_tokens
        if budget is not None and budget <= 0:
            raise AIOutputTruncated("No generation budget remains.")
        prompt = _with_budget(request.prompt, budget)
        # A route's requested effort (ai.route_reasoning_effort) replaces the
        # profile's for this request, as on Codex and OpenRouter.
        effort = getattr(request, "reasoning_effort", None) or None
        if request.workspace is not None:
            text = self._workspace_turn(Path(request.workspace), self._instructions(model_type), prompt, model_type,
                                        deadline=deadline, effort=effort, budget=budget)
        else:
            text = self._respond(self._instructions(model_type), prompt, model_type, deadline=deadline,
                                 effort=effort, budget=budget)
        try:
            return model_type.model_validate_json(text)
        except (ValidationError, ValueError) as first:
            if single_request_active():
                raise AIInvalidOutput(f"{self.provider_name} returned invalid {model_type.__name__} JSON") from first
            # The repair is tool-free: it sees the output to repair, never the
            # workspace. It is sent with the budget of the request it repairs
            # (the same sentence, the same recorded allowance): the repaired
            # answer is the same complete JSON response (final verification F9).
            repaired = self._respond(_JSON_ONLY, _with_budget(_repair_prompt(text, model_type), budget), model_type,
                                     deadline=deadline, effort=effort, budget=budget)
            try:
                return model_type.model_validate_json(repaired)
            except (ValidationError, ValueError) as second:
                raise AIInvalidOutput(
                    f"{self.provider_name} returned invalid {model_type.__name__} JSON after one repair"
                ) from second

    def _instructions(self, model_type: type[BaseModel]) -> str:
        if self.response_format == "json_schema":
            return _JSON_ONLY
        schema = json.dumps(_prompt_schema(model_type), sort_keys=True, ensure_ascii=False)
        return (f"{_JSON_ONLY} The JSON object must validate against this JSON schema; emit every declared "
                f"field and no others.\n\nSchema:\n{schema}")

    def _text_format(self, model_type: type[BaseModel]) -> dict[str, Any]:
        if self.response_format == "json_schema":
            return {"type": "json_schema", "name": model_type.__name__[:64], "schema": strict_output_schema(model_type),
                    "strict": True}
        return {"type": "json_object"}

    def _respond(self, instructions: str, prompt: str, model_type: type[BaseModel], *, deadline: float,
                 effort: str | None = None, extra: dict[str, Any] | None = None, budget: int | None = None) -> str:
        body = request_body(
            model=str(self.model), instructions=instructions, prompt=prompt,
            text_format=self._text_format(model_type),
            reasoning_effort=(effort or self.profile.reasoning_effort or None),
        )
        return self._send(body, deadline=deadline, extra=extra, budget=budget).text.strip()

    # -- the read-only workspace -------------------------------------------
    def _workspace_turn(self, root: Path, instructions: str, prompt: str, model_type: type[BaseModel], *,
                        deadline: float, effort: str | None, budget: int | None = None) -> str:
        """Serve ``root`` to the model (function calls or inline); returns the final text."""

        if single_request_active():
            # Each round of workspace calls is a physical request of its own.
            raise AIProviderUnavailable(
                f"{self.provider_name}: a read-only workspace turn sends one request per round of workspace "
                "calls, so it cannot run under a single-request budget."
            )
        self._stop_if_due(deadline)
        try:
            workspace = ServedWorkspace(root, max_entry_chars=self.max_entry_chars,
                                        max_workspace_chars=self.max_workspace_chars)
        except (NotADirectoryError, OSError) as exc:
            raise AIProviderUnavailable(f"{self.provider_name}: {exc}") from None
        # Published before anything is served, so the record survives a failure.
        self._workspace = workspace
        if self.workspace_mode == "inline":
            try:
                block = workspace.inline_block()
            except WorkspaceTooLarge as exc:
                raise AIProviderUnavailable(f"{self.provider_name}: {exc}") from None
            return self._respond(f"{instructions}\n\n{INSTRUCTIONS_INLINE}", f"{prompt}\n\n{block}", model_type,
                                 deadline=deadline, effort=effort, budget=budget,
                                 extra={"workspace": {"mode": "inline", "served": workspace.activity()}})
        return self._tool_loop(workspace, f"{instructions}\n\n{INSTRUCTIONS_TOOLS}", prompt, model_type,
                               deadline=deadline, effort=effort, budget=budget)

    def _tool_loop(self, workspace: ServedWorkspace, instructions: str, prompt: str, model_type: type[BaseModel],
                   *, deadline: float, effort: str | None, budget: int | None = None) -> str:
        """Rounds of function calls over ``workspace``, then the final answer.

        Up to ``max_tool_rounds`` responses that call workspace functions are
        served; the next one's calls are answered "answer now" (nothing
        served); a response after that which still calls is invalid output.
        With ``store: false`` every request resends the whole history.
        """

        items: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
        tools = [ServedWorkspace.namespace_tool()]
        text_format = self._text_format(model_type)
        reasoning = effort or self.profile.reasoning_effort or None
        carried = 0
        for round_index in range(1, self.max_tool_rounds + 3):
            self._stop_if_due(deadline)
            body = request_body(model=str(self.model), instructions=instructions, input_items=items,
                                text_format=text_format, reasoning_effort=reasoning, tools=tools)
            # The files this request carries to the model for the first time.
            carries = [entry.path for entry in workspace.served[carried:]]
            carried = len(workspace.served)
            result = self._send(body, deadline=deadline, budget=budget, extra={"workspace": {
                "mode": "tools", "round": round_index, "carries": carries,
            }})
            calls = function_calls(result.output)
            if not calls:
                return result.text.strip()
            if round_index > self.max_tool_rounds + 1:
                raise AIInvalidOutput(
                    f"{self.provider_name} kept calling workspace functions after {self.max_tool_rounds} rounds "
                    "and a request to answer."
                )
            exhausted = round_index > self.max_tool_rounds
            items.extend(echo_items(result.output))
            for call in calls:
                call_id = call.get("call_id")
                if not isinstance(call_id, str) or not call_id:
                    raise AIInvalidOutput(f"{self.provider_name} made a function call without a call_id.")
                name = str(call.get("name") or "")
                arguments = call.get("arguments") if isinstance(call.get("arguments"), str) else ""
                namespace = call.get("namespace")
                if namespace not in (None, "", NAMESPACE):
                    output = workspace.refuse(f"{namespace}.{name}", arguments, call_id=call_id,
                                              round_index=round_index,
                                              reason=f"there is no namespace {namespace!r}; use {NAMESPACE}")
                elif exhausted:
                    output = workspace.refuse_exhausted(name, arguments, call_id=call_id, round_index=round_index)
                else:
                    output = workspace.call(name, arguments, call_id=call_id, round_index=round_index)
                items.append({"type": "function_call_output", "call_id": call_id, "output": output})
        raise AIInvalidOutput(f"{self.provider_name} did not answer within its workspace rounds.")  # pragma: no cover

    # -- one physical request, with retries --------------------------------
    def _send(self, body: dict[str, Any], *, deadline: float, extra: dict[str, Any] | None = None,
              budget: int | None = None) -> StreamResult:
        """One physical request, resent on a transient failure or after a token refresh.

        ``budget`` is the call's output budget, already stated in the prompt;
        each attempt's receipt records it (the route takes no wire cap).
        """

        refreshed = False
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            self._stop_if_due(deadline)
            # Local refusals (signed out, paused, ineligible) send nothing.
            observed_pause = self.session.check_usable(pause_minutes=self.pause_minutes)
            try:
                return self._send_once(body, deadline=deadline, observed_pause=observed_pause, extra=extra,
                                       budget=budget)
            except ChatGPTPlanUnauthorized:
                if single_request_active() or refreshed:
                    raise
                refreshed = True
            except ChatGPTPlanTransient as failure:
                delay = None if single_request_active() or attempt >= _MAX_ATTEMPTS else (
                    _BACKOFF_SECONDS[attempt - 1] * (0.5 + 0.5 * _random()))
                if delay is None or _monotonic() + delay + _MIN_ATTEMPT_SECONDS > deadline:
                    raise
                logger.warning("ChatGPT plan %s request failed transiently; retrying in %.1fs: %s",
                               self.provider_name, delay, failure)
                _sleep(delay)
        raise ChatGPTPlanUnauthorized(f"{self.provider_name}: the refreshed access token was not accepted either.")

    def _stop_if_due(self, deadline: float) -> None:
        if self._interrupted.is_set():
            raise AIInterrupted("ChatGPT plan request interrupted.")
        if deadline - _monotonic() <= 0:
            raise AITurnTimeout("The ChatGPT plan request ran out of time.")

    def _send_once(self, body: dict[str, Any], *, deadline: float, observed_pause: dict[str, Any] | None,
                   extra: dict[str, Any] | None = None, budget: int | None = None) -> StreamResult:
        """One physical request under its own receipt (the token step sends no model request)."""

        stream = ResponsesStream(self.base_url)
        # Published first: an interrupt from here on cancels this stream, and
        # one that came earlier set the flag checked below.
        with self._active_lock:
            self._active = stream
        try:
            self._stop_if_due(deadline)
            try:
                token = self.session.access_token(
                    timeout=deadline - _monotonic(),
                    cancelled=lambda: self._interrupted.is_set() or deadline - _monotonic() <= 0,
                )
            except AIProviderUnavailable:
                self._stop_if_due(deadline)  # an interrupt or the deadline, not the credentials
                raise
            # The credential step may have outlived the deadline or an interrupt.
            self._stop_if_due(deadline)
            remaining = deadline - _monotonic()
            # The receipt records the output allowance this request is sent
            # with: the budget its prompt states, the route taking no cap.
            with model_call(self, purpose="responses_request", prompt=body.get("input"),
                            schema=body.get("text"), budget=budget) as receipt:
                try:
                    result = stream.send(body, access_token=token, timeout=remaining)
                except StreamCancelled as cancelled:
                    if cancelled.reason == "interrupt":
                        raise AIInterrupted("ChatGPT plan request interrupted.") from None
                    raise AITurnTimeout("The ChatGPT plan request exceeded its deadline.") from None
                except StreamIncomplete as incomplete:
                    self._meter(incomplete.response, None, extra=extra)
                    if incomplete.reason in {"max_output_tokens", "max_tokens"}:
                        raise AIOutputTruncated(f"{self.provider_name} exhausted its output budget.") from None
                    raise AIProviderUnavailable(
                        f"{self.provider_name} returned an incomplete response ({incomplete.reason or 'unknown'})."
                    ) from None
                except ResponsesError as error:
                    if error.response:
                        self._meter(error.response, error.request_id, extra=extra)
                    receipt.update(finish_reason=error.code or (f"http_{error.status}" if error.status else "network"))
                    raise self._classify(error) from None
                self.last_timing = {
                    "headers": result.seconds_to_headers, "first_event": result.seconds_to_first_event,
                    "total": result.seconds_total,
                }
                calls = function_calls(result.output)
                self._meter(result.response, result.request_id, text=result.text, extra={
                    **(extra or {}), **({"function_calls": len(calls)} if calls else {}),
                })
                self.session.note_success(observed_pause)
                if calls:
                    # A round of workspace calls: the answer comes later.
                    return result
                if result.refusal and not result.text.strip():
                    raise AIInvalidOutput(f"{self.provider_name} refused: {result.refusal[:200]}")
                if not result.text.strip():
                    raise AIProviderUnavailable(f"{self.provider_name} returned an empty response.")
                return result
        finally:
            with self._active_lock:
                if self._active is stream:
                    self._active = None

    def _meter(self, response: dict[str, Any], request_id: str | None, *, text: str | None = None,
               extra: dict[str, Any] | None = None) -> None:
        """Record usage on the receipt and the run before anything inspects the body.

        ``usage_json.chatgpt_plan`` names the request id and the billing class
        (``subscription``: Slice A plan §5 rule 6) and, on a workspace turn,
        the round and the files the request carried.
        """

        usage = response.get("usage") if isinstance(response.get("usage"), dict) else None
        input_tokens = _count(usage.get("input_tokens")) if usage else None
        output_tokens = _count(usage.get("output_tokens")) if usage else None
        input_details = usage.get("input_tokens_details") if usage and isinstance(usage.get("input_tokens_details"), dict) else {}
        output_details = usage.get("output_tokens_details") if usage and isinstance(usage.get("output_tokens_details"), dict) else {}
        report_call_usage({
            "provider_response_id": response.get("id") if isinstance(response.get("id"), str) else None,
            "resolved_model": response.get("model") if isinstance(response.get("model"), str) else None,
            "finish_reason": response.get("status") if isinstance(response.get("status"), str) else None,
            "usage_json": json.dumps({**(usage or {}), "chatgpt_plan": {
                "request_id": request_id, "billing": "subscription", **(extra or {}),
            }}, sort_keys=True, default=str),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cached_input_tokens": _count(input_details.get("cached_tokens")),
            "reasoning_tokens": _count(output_details.get("reasoning_tokens")),
            **({"output_text": text} if text is not None else {}),
        })
        self.record_token_usage(input_tokens or 0, output_tokens or 0)

    def _classify(self, error: ResponsesError) -> Exception:
        """Map a ChatGPT-plan error to LearnLoop's taxonomy; records pause/eligibility state.

        The exception also carries the error's structured fields as
        ``provider_error`` (status, code, param, request id and the local
        remedy, if any), so a report can keep codes without the provider's
        prose, which may quote the request (``learnloop ai compare``).
        """

        exc, remedy = self._classified(error)
        exc.provider_error = {  # type: ignore[attr-defined]
            "status": error.status, "code": error.code or None, "param": error.param or None,
            "request_id": error.request_id, "remedy": remedy,
        }
        return exc

    def _classified(self, error: ResponsesError) -> tuple[Exception, str | None]:
        code = error.code or ""
        where = f"HTTP {error.status}" if error.status not in (None, 200) else (
            "stream" if error.status == 200 else "network")
        reference = f", request id {error.request_id}" if error.request_id else ""
        detail = f"{where}{', ' + code if code else ''}{reference}"
        if code == "subscription_sharing_usage_limit_exceeded":
            self.session.note_usage_limit(code=code, request_id=error.request_id)
            return ChatGPTPlanUsageExhausted(
                f"ChatGPT plan usage exhausted ({detail}): LearnLoop pauses plan requests for "
                f"{self.pause_minutes} minutes. Manage usage: {MANAGE_USAGE_URL}"
            ), None
        if code == "subscription_sharing_user_not_eligible":
            self.session.note_not_eligible(code=code, request_id=error.request_id)
            return ChatGPTPlanNotEligible(
                f"ChatGPT plan usage is unavailable for this account, workspace or policy ({detail})."
            ), None
        if code == "subscription_sharing_invalid_user" or error.status == 401:
            self.session.note_unauthorized()
            return ChatGPTPlanUnauthorized(
                f"The ChatGPT plan did not accept the access token ({detail}); LearnLoop refreshes it before the "
                "next request. If this repeats, sign in again: `learnloop ai signin chatgpt`."
            ), None
        if code in _CONFIG_CODES or (error.status == 403 and not code) or error.status == 400:
            hint = ""
            remedy = None
            param_name = error.param or ""
            if code == "subscription_sharing_unsupported_capability" and param_name.startswith("text"):
                hint = (f' This route rejected structured output; set response_format = "json_object" on '
                        f"[ai.providers.{self.provider_name}].")
                remedy = "json_object"
            elif param_name.startswith(("tools", "include")) or (
                    param_name.startswith("input") and "function call" in str(error).lower()):
                # Only a read-only-workspace turn declares tools or resends calls.
                hint = (f" This route rejected the read-only workspace's function calls; set workspace_mode = "
                        f'"inline" on [ai.providers.{self.provider_name}] to send the workspace in the request.')
                remedy = "workspace_inline"
            param = f" param {error.param!r}." if error.param else ""
            return ChatGPTPlanRequestRejected(
                f"The ChatGPT plan rejected this request ({detail}): {error}.{param}{hint}"
            ), remedy
        if code in _TRANSIENT_CODES or error.status is None or (error.status in _TRANSIENT_STATUSES):
            return ChatGPTPlanTransient(f"The ChatGPT plan request failed ({detail}): {error}"), None
        return AIProviderUnavailable(f"The ChatGPT plan request failed ({detail}): {error}"), None


def list_plan_models(base_url: str = CHATGPT_PLAN_API_BASE_URL, *, session: PlanSession | None = None,
                     timeout: float = 20.0) -> list[dict[str, str]]:
    """The signed-in account's model picker: ``GET {base_url}/models``, ``visibility == "list"``.

    One unbilled request with the plan's access token; the server's order is kept.
    """

    session = session or PlanSession()
    token = session.access_token(timeout=timeout)
    try:
        status, headers, raw = urllib_call("GET", base_url.rstrip("/") + "/models", {
            "Authorization": f"Bearer {token}", "Accept": "application/json", "User-Agent": "LearnLoop",
        }, None, timeout)
    except EndpointUnreachable as exc:
        raise ChatGPTPlanTransient(f"The model list could not be fetched ({exc}).") from None
    if status == 401:
        session.note_unauthorized()
        raise ChatGPTPlanUnauthorized("The model list refused the access token (HTTP 401); try again to refresh it.")
    if status != 200:
        try:
            code, message, _param = error_fields(json.loads(raw.decode("utf-8")))
        except (UnicodeDecodeError, ValueError):
            code, message = None, None
        raise AIProviderUnavailable(f"The model list failed (HTTP {status}{', ' + code if code else ''}): "
                                    f"{message or 'no detail'}")
    try:
        models = json.loads(raw.decode("utf-8")).get("models")
    except (UnicodeDecodeError, ValueError, AttributeError):
        models = None
    if not isinstance(models, list):
        raise AIProviderUnavailable("The model list had no `models` array.")
    return [
        {"slug": str(model["slug"]), "display_name": str(model.get("display_name") or model["slug"])}
        for model in models
        if isinstance(model, dict) and model.get("visibility") == "list" and model.get("slug")
    ]


def _count(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return int(value) if value >= 0 else None


def _prompt_schema(model_type: type[BaseModel]) -> dict[str, Any]:
    try:
        return strict_output_schema(model_type)
    except TypeError:
        return model_type.model_json_schema()


def _with_budget(prompt: str, budget: int | None) -> str:
    """``prompt`` with the output budget stated once at its end (the route takes no ``max_output_tokens``)."""

    if budget is None:
        return prompt
    return f"{prompt}\n\nKeep the complete JSON response within {budget} output tokens."


def _repair_prompt(text: str, model_type: type[BaseModel]) -> str:
    schema = json.dumps(model_type.model_json_schema(), sort_keys=True, ensure_ascii=False)
    return ("Repair the following model output into a JSON object that validates against "
            f"this JSON schema. Return only JSON.\n\nSchema:\n{schema}\n\nOutput:\n{text}")


__all__ = [
    "ChatGPTPlanProviderClient",
    "list_plan_models",
    "ChatGPTPlanRequestRejected",
    "ChatGPTPlanTransient",
    "ChatGPTPlanUnauthorized",
    "PROVIDER_TYPE",
]
