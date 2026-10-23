"""E0's experiment-only Anthropic Messages API transport (re-plan 2026-10-22).

Orchestrator ruling: E0's LLM roles move off Codex to the Anthropic Messages
API DIRECTLY: one HTTPS POST to ``https://api.anthropic.com/v1/messages``
per admitted request, never ``claude -p`` (an agent harness, even bare). A
direct call is tool-free by construction, and this module keeps it so:

* **Body grammar.** A request body's keys are a subset of
  :data:`ALLOWED_BODY_KEYS` (``model``, ``max_tokens``, ``system``,
  ``messages``, ``temperature``, ``stop_sequences``); E0 sends only the
  first four. ``tools`` (and every other key: ``tool_choice``,
  ``mcp_servers``, ``container``, ``output_config``...) is refused before
  anything is sent (:func:`check_body`). ``messages`` is one user turn of
  plain text. With ``anthropic-version: 2026-10-21`` a sampling parameter
  would be rejected, so ``temperature`` is never sent.
* **Admission.** Every POST runs inside ``learnloop.ai.execution.model_call``
  under the role's ``callers.E0RequestGate``: the E0 ledger admits it BEFORE
  it is sent, at its hard maximum charge: the input upper bound of exactly
  what is sent (``[system, user text]``) plus the ``max_tokens`` sent, at the
  pin's verified price (the long-prompt tier when the input bound passes
  it). A retry of a transient failure is another admitted POST.
* **Usage.** Only the response's ``usage`` (``input_tokens``,
  ``output_tokens``) is reported for settlement; a response without it keeps
  the whole reservation (``budget.reconciled_usd``, Codex re-review F21).
* **The key.** ``ANTHROPIC_API_KEY`` (configurable) is read from the process
  environment, which only ``--env-file`` loads (``credentials``): it is sent in
  the ``x-api-key`` header and nowhere else. No header, key or body ever
  reaches a log, a receipt or an exception: a failure is an
  :class:`~budget.E0ProviderFailure` with an allowlisted classification, the
  HTTP status and a safe request id (fix round 4, High 8); the HTTP transport
  never reads an error body.
* **Isolation.** Production never imports this module (the import-linter
  contract ``experiments-stay-outside-production`` forbids
  ``learnloop.experiments`` everywhere outside the CLI, and
  ``tests/test_e0_isolation.py`` scans every source file).
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
import json
import re
import time
from types import SimpleNamespace
from typing import Any

from pydantic import BaseModel

from learnloop.experiments.contextual_embeddings import credentials, pins
from learnloop.experiments.contextual_embeddings.budget import E0BudgetExceeded, E0ProviderFailure
from learnloop.experiments.contextual_embeddings.pins import RolePin

#: The only keys a request body may carry (the ruling's grammar).
ALLOWED_BODY_KEYS = frozenset({"model", "max_tokens", "system", "messages", "temperature", "stop_sequences"})
#: What E0 actually sends.
SENT_BODY_KEYS = ("model", "max_tokens", "system", "messages")
_SAFE_ID = re.compile(r"[A-Za-z0-9_.:-]{1,80}")


class BodyGrammarError(ValueError):
    """A request body outside the grammar; nothing was sent."""


def check_body(body: Mapping[str, Any]) -> None:
    """Refuse any body outside the grammar: an unknown key (``tools`` above
    all), a wrong type, more than one user turn, or non-text content."""

    keys = set(body)
    if "tools" in keys:
        raise BodyGrammarError("a request body never carries tools")
    extra = keys - ALLOWED_BODY_KEYS
    if extra:
        raise BodyGrammarError("a request body carries keys outside the grammar")
    if not {"model", "max_tokens", "messages"} <= keys:
        raise BodyGrammarError("a request body needs model, max_tokens and messages")
    if not isinstance(body["model"], str) or not body["model"]:
        raise BodyGrammarError("the model is a non-empty string")
    if isinstance(body["max_tokens"], bool) or not isinstance(body["max_tokens"], int) or body["max_tokens"] <= 0:
        raise BodyGrammarError("max_tokens is a positive integer")
    if "system" in body and not isinstance(body["system"], str):
        raise BodyGrammarError("the system prompt is plain text")
    messages = body["messages"]
    if (not isinstance(messages, list) or len(messages) != 1 or not isinstance(messages[0], Mapping)
            or set(messages[0]) != {"role", "content"} or messages[0]["role"] != "user"
            or not isinstance(messages[0]["content"], str)):
        raise BodyGrammarError("messages is one user turn of plain text")


def _classify(status: int | None) -> str:
    if status in (401, 403):
        return "auth"
    if status == 429:
        return "rate_limited"
    if status in (408, 504):
        return "timeout"
    if status is not None and (status >= 500 or status == 529):
        return "unavailable"
    if status is None:
        return "network"
    return "contract"


TRANSIENT = frozenset({"rate_limited", "timeout", "unavailable", "network"})
#: The Messages API's documented ``stop_reason`` values and content block types
#: (what a safe failure detail may name; anything else is ``other``).
STOP_REASONS = frozenset({"end_turn", "max_tokens", "stop_sequence", "tool_use", "pause_turn", "refusal"})
BLOCK_TYPES = frozenset({"text", "thinking", "redacted_thinking", "tool_use"})


def json_instructions(result_model: type[BaseModel]) -> str:
    """The system prompt: answer with one JSON object of the result schema
    (no ``output_config``: the body grammar has no structured-output key)."""

    schema = json.dumps(result_model.model_json_schema(), sort_keys=True, separators=(",", ":"))
    return ("Answer with exactly one JSON object and nothing else (no prose, no code fence). It must validate "
            f"against this JSON Schema: {schema}")


def extract_json(text: str) -> str:
    """The JSON object in a text answer (a stray code fence tolerated)."""

    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        stripped = stripped[stripped.find("{"):] if "{" in stripped else stripped
    start, end = stripped.find("{"), stripped.rfind("}")
    if start < 0 or end < start:
        raise E0ProviderFailure("invalid_output", reason="no JSON object")
    return stripped[start:end + 1]


#: At most this many JSON objects are tried in one answer.
MAX_CANDIDATES = 16


def schema_fields(result_model: type[BaseModel]) -> frozenset[str]:
    """Every field name of the result schema, nested models included: the
    names a safe validation reason may print (anything else is ``?``)."""

    names: set[str] = set()
    pending: list[Any] = [result_model]
    seen: set[Any] = set()
    while pending:
        model = pending.pop()
        if model in seen:
            continue
        seen.add(model)
        for name, field in getattr(model, "model_fields", {}).items():
            names.add(name)
            stack = [field.annotation]
            while stack:
                annotation = stack.pop()
                if isinstance(annotation, type) and issubclass(annotation, BaseModel):
                    pending.append(annotation)
                stack.extend(getattr(annotation, "__args__", ()) or ())
    return frozenset(names)


def validation_reason(error: Any, fields: frozenset[str]) -> str:
    """A pydantic ``ValidationError`` as ``loc:type`` codes (no input, no message)."""

    codes = []
    for item in error.errors()[:6]:
        loc = ".".join(str(part) if isinstance(part, int) else (part if part in fields else "?")
                       for part in item.get("loc", ()))
        kind = item.get("type") if isinstance(item.get("type"), str) and re.fullmatch(r"[a-z_.]{1,40}",
                                                                                        item["type"]) else "other"
        codes.append(f"{loc or 'root'}:{kind}")
    extra = error.error_count() - len(codes)
    return "validation " + ", ".join(codes) + (f" (+{extra} more)" if extra > 0 else "")


def parse_answer(text: str, result_model: type[BaseModel]) -> BaseModel:
    """The ONE result object in a text answer (paid-run round 2).

    Every top-level JSON object in the text is decoded in turn (prose, a
    code fence or a second object around it no longer breaks the parse).
    Exactly one object that validates is the answer; several that validate
    are accepted only when they are equal. Otherwise ``invalid_output`` with
    a SAFE reason: ``no JSON object``, the decoder's fixed message and
    position, ``N different objects validate``, or the first candidate's
    ``loc:type`` validation codes (schema field names only)."""

    fields = schema_fields(result_model)
    decoder = json.JSONDecoder()
    position, objects, decode_error = 0, [], None
    while len(objects) < MAX_CANDIDATES:
        start = text.find("{", position)
        if start < 0:
            break
        try:
            value, end = decoder.raw_decode(text, start)
        except json.JSONDecodeError as exc:
            decode_error = decode_error or f"json {exc.msg} at char {exc.pos} of {len(text)}"
            position = start + 1
            continue
        if isinstance(value, dict):
            objects.append(value)
        position = end
    valid, first_error = [], None
    for value in objects:
        try:
            valid.append(result_model.model_validate(value))
        except Exception as exc:  # noqa: BLE001 - only its codes are kept
            if first_error is None and hasattr(exc, "errors"):
                first_error = validation_reason(exc, fields)
    if valid:
        dumps = {json.dumps(item.model_dump(mode="json"), sort_keys=True) for item in valid}
        if len(dumps) == 1:
            return valid[0]
        raise E0ProviderFailure("invalid_output", reason=f"{len(dumps)} different JSON objects validate")
    if first_error is not None:
        raise E0ProviderFailure("invalid_output", reason=first_error)
    raise E0ProviderFailure("invalid_output", reason=decode_error or "no JSON object")


def repair_prompt(text: str, reason: str) -> str:
    """The one repair request (paid-run round 2): the model's own answer back
    with the SAFE reason it failed, asking for exactly one valid object. As
    the production providers' JSON repair does, it carries no other text."""

    return ("Your previous answer could not be used: " + reason + ". Rewrite it as exactly one JSON object that "
            "validates against the JSON Schema in the system prompt. Keep every judgment it made; if it holds "
            "more than one answer, keep only your final one. No prose, no code fence.\n\nPrevious answer:\n" + text)


class AnthropicMessagesClient:
    """One role's client: its pin's model, the Messages API, one POST per
    admitted request. ``transport`` is ``adapters.UrllibTransport`` (status
    only on an error, never its body) or a test fake."""

    provider_type = "anthropic_messages"

    def __init__(self, pin: RolePin, *, key_env: str | None = None, environ: Mapping[str, str] | None = None,
                 transport: Any = None, url: str = pins.ANTHROPIC_MESSAGES_URL,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        from learnloop.experiments.contextual_embeddings.adapters import UrllibTransport

        if pin.transport != "anthropic_api":
            raise ValueError("an Anthropic client serves an anthropic_api pin only")
        self.pin = pin
        self.provider_name = pin.provider_profile
        self.model = pin.model
        self.profile = SimpleNamespace(base_url=pins.ANTHROPIC_PROFILES[pin.provider_profile]["base_url"],
                                       model=pin.model, reasoning_effort=None, max_tokens=None)
        self.key_env = key_env or pins.ANTHROPIC_KEY_ENV
        self.environ = environ
        self.transport = transport or UrllibTransport()
        self.url = url
        self.sleep = sleep

    def supports(self, capability: str) -> bool:
        return False  # never a production structured transport: E0 calls ``structured`` itself

    # -- the wire ---------------------------------------------------------------------
    def body(self, system: str, prompt: str, max_tokens: int) -> dict[str, Any]:
        body = {"model": self.pin.model, "max_tokens": int(max_tokens), "system": system,
                "messages": [{"role": "user", "content": prompt}]}
        check_body(body)
        return body

    def wire_prompt(self, prompt: str, result_model: type[BaseModel]) -> list[str]:
        """What a request sends as text, in order: the admission's input bound
        and the receipt's prompt identity."""

        return [json_instructions(result_model), prompt]

    def _headers(self) -> dict[str, str]:
        key = credentials.read_key(self.key_env, environ=self.environ)
        if not key:
            raise E0ProviderFailure("auth")
        return {"x-api-key": key, "anthropic-version": pins.ANTHROPIC_VERSION, "content-type": "application/json"}

    def send(self, body: Mapping[str, Any], *, purpose: str, prompt_identity: Any) -> Mapping[str, Any]:
        """ONE admitted POST: the active request gate admits it inside
        ``model_call`` before it is sent and settles it from ``usage``."""

        from learnloop.ai.execution import active_request_gate, model_call, report_call_usage

        check_body(body)
        if active_request_gate() is None:
            # Fail closed (pre-paid verify L4): a POST nobody admits is never sent.
            raise E0BudgetExceeded("no E0 request gate is active; the Messages API request was not sent")
        headers = self._headers()
        with model_call(self, purpose=purpose, prompt=prompt_identity, budget=int(body["max_tokens"])):
            try:
                response = self.transport.post(self.url, headers=headers, body=dict(body),
                                               timeout=pins.ANTHROPIC_TIMEOUT_S)
            except E0ProviderFailure:
                raise
            except Exception:  # the transport's own error carries no body; classify only
                raise E0ProviderFailure("network") from None
            request_id = response.request_id if isinstance(response.request_id, str) and _SAFE_ID.fullmatch(
                response.request_id) else None
            payload = response.body if isinstance(response.body, Mapping) else None
            if not 200 <= int(response.status) < 300 or payload is None:
                raise E0ProviderFailure(_classify(int(response.status)), status_code=int(response.status),
                                        request_id=request_id)
            usage = payload.get("usage") if isinstance(payload.get("usage"), Mapping) else {}
            text = "".join(str(block.get("text") or "") for block in payload.get("content") or []
                           if isinstance(block, Mapping) and block.get("type") == "text")
            # Only the response's own usage settles the reservation (missing: kept whole).
            report_call_usage({"input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
                               "provider_response_id": request_id, "resolved_model": payload.get("model"),
                               "finish_reason": payload.get("stop_reason"), "output_text": text})
        if payload.get("model") != self.pin.model:
            raise E0ProviderFailure("contract", status_code=int(response.status), request_id=request_id)
        return payload

    # -- a role call ----------------------------------------------------------------
    def structured(self, *, purpose: str, prompt: str, result_model: type[BaseModel], max_tokens: int) -> BaseModel:
        """The role's answer: one admitted POST (plus admitted retries of a
        transient failure), parsed and validated against ``result_model``."""

        system, user = self.wire_prompt(prompt, result_model)
        payload = self._post_with_retries(self.body(system, user, max_tokens), purpose=purpose,
                                          prompt_identity=[system, user])
        text = self._answer_text(payload, max_tokens)
        try:
            return parse_answer(text, result_model)
        except E0ProviderFailure as failure:
            if failure.classification != "invalid_output":
                raise
            first = failure
        # ONE admitted repair (paid-run round 2): the production providers'
        # JSON repair, under the same request gate, at the same max_tokens.
        repair = repair_prompt(text, first.reason or "it did not validate")
        payload = self._post_with_retries(self.body(system, repair, max_tokens), purpose=f"{purpose}_repair",
                                          prompt_identity=[system, repair])
        repaired_text = self._answer_text(payload, max_tokens, repaired=True)
        try:
            return parse_answer(repaired_text, result_model)
        except E0ProviderFailure as failure:
            raise E0ProviderFailure("invalid_output", reason=f"{first.reason}; after one repair: {failure.reason}",
                                    details={**self._details(payload, max_tokens), "repaired": True}) from None

    def _post_with_retries(self, body: Mapping[str, Any], *, purpose: str, prompt_identity: Any) -> Mapping[str, Any]:
        attempt = 0
        while True:
            try:
                return self.send(body, purpose=purpose, prompt_identity=prompt_identity)
            except E0ProviderFailure as failure:
                if failure.classification not in TRANSIENT or attempt >= pins.TRANSIENT_RETRIES:
                    raise
                attempt += 1
                self.sleep(min(30.0, 2.0 ** attempt))

    @staticmethod
    def _details(payload: Mapping[str, Any], max_tokens: int) -> dict[str, Any]:
        """Safe numbers of a response: its stop_reason (allowlisted), token
        counts, the max_tokens sent and the content block types."""

        usage = payload.get("usage") if isinstance(payload.get("usage"), Mapping) else {}
        stop = payload.get("stop_reason")
        blocks = [block.get("type") for block in payload.get("content") or [] if isinstance(block, Mapping)]
        return {"stop_reason": stop if stop in STOP_REASONS else ("other" if stop is not None else None),
                "output_tokens": usage.get("output_tokens") if isinstance(usage.get("output_tokens"), int) else None,
                "input_tokens": usage.get("input_tokens") if isinstance(usage.get("input_tokens"), int) else None,
                "max_tokens": int(max_tokens),
                "blocks": sorted({block if block in BLOCK_TYPES else "other" for block in blocks})}

    def _answer_text(self, payload: Mapping[str, Any], max_tokens: int, *, repaired: bool = False) -> str:
        """The text blocks of a finished answer; a refusal or a ``max_tokens``
        stop is raised with its safe details (thinking counts against
        ``max_tokens`` on these models: the documented adaptive default)."""

        details = {**self._details(payload, max_tokens), "repaired": repaired}
        if payload.get("stop_reason") == "refusal":
            raise E0ProviderFailure("refusal", reason="stop_reason refusal", details=details)
        if payload.get("stop_reason") == "max_tokens":
            raise E0ProviderFailure("truncated", reason=f"stop_reason max_tokens at {int(max_tokens)} output tokens "
                                                        "(thinking included)", details=details)
        return "".join(str(block.get("text") or "") for block in payload.get("content") or []
                       if isinstance(block, Mapping) and block.get("type") == "text")

    def canary(self) -> dict[str, Any]:
        """The model id's check before any bulk work: one tiny admitted
        request must be answered as a Messages API ``message`` by exactly the
        pinned model, with usage."""

        body = self.body("Answer with the single word: ok", "ok?", 256)
        payload = self.send(body, purpose=f"e0_canary_{self.pin.provider_profile}",
                            prompt_identity=[body["system"], "ok?"])
        usage = payload.get("usage") if isinstance(payload.get("usage"), Mapping) else {}
        if payload.get("type") != "message" or not isinstance(usage.get("input_tokens"), int):
            raise E0ProviderFailure("contract")
        return {"status": "ok", "model": self.pin.model}
