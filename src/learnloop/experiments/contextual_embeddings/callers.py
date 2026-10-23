"""Paid LLM roles for E0 (writer, context, labels, adjudicator, tutor, judges).

Each role has one pinned route (``pins.ROLE_PINS``): provider profile,
transport, model, effort, expected output, price bound and prompt version. A
call is one isolated, tool-free structured turn through the existing client
stack (``learnloop.ai.routing.client_for_provider`` and
``learnloop.ai.transport.execute_structured_operation``), so prompts never
reach the vault, files or tools.

**The resolved route must be the pin (Codex review F3).** Before any
request, the client a role resolves to is checked against its pin: transport
(provider type), model, billing class (a subscription pin must resolve to a
subscription transport and a metered one to a metered transport) and, for a
metered route, the experiment's own endpoint. A mismatch (a copy overriding
``codex_luna`` with a metered profile, or another model) is refused before
anything is sent. The experiment's metered profile is added to an in-memory
copy of the vault's config only, and a copy that already defines that name
differently is refused rather than silently used. The resolved identity is
part of every checkpoint key, so a changed identity never reuses a result.

**Output bounds (Codex review F2).** Every request runs under the normal
output-budget policy (``learnloop.ai.output_budget.output_budget`` for the
role's profile: ``ai.output_tokens`` 16,384 unless the profile or route sets
otherwise; spec §6: "keep the existing output-budget policy"). The bound is
installed with ``generation_limit``, so the physical request is sent with
it as ``max_tokens``, and the gate reserves exactly the bound the request is
sent with (a truncation retry at double the bound is admitted at its own
bound). A metered request without an output bound is refused.

**Admission per physical request.** ``E0RequestGate`` is installed with the
existing ``learnloop.ai.execution.gate_model_requests``: the transport
consults it immediately before EVERY physical request (a transport retry or a
JSON repair included) and settles it with the usage the request reported. The
gate admits through the E0 ledger: metered routes reserve their input upper
bound (``pins.token_upper_bound``) plus the request's output bound at the
pin's upper-bound prices; subscription routes (Codex) are admitted at $0 and
tallied ``estimated_only``.

**Resume.** A validated result is checkpointed under a content key of the
role pin, the resolved identity, the output bound, the prompt and the schema
in the run's private directory, together with its ORIGINAL measured latency
and receipt ids; a resumed run reads it instead of paying again and reports
the original measurement, marked cached (Codex review F9).
"""
from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
import fcntl
import hashlib
import json
import os
from pathlib import Path
import threading
import time
from typing import Any, Protocol

from pydantic import BaseModel

from learnloop.ai.execution import gate_model_requests
from learnloop.ai.spend import is_subscription_transport

from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.budget import (
    E0BudgetExceeded,
    E0Ledger,
    E0PriceUnverified,
    E0ProviderFailure,
    E0RequestBlocked,
    E0Stop,
    Request,
    reconciled_usd,
)
from learnloop.experiments.contextual_embeddings.pins import RolePin, token_upper_bound

#: Structured-output schema allowance added to every input bound.
SCHEMA_ALLOWANCE_TOKENS = 512
#: A pin's transport name -> the provider types its client may report.
TRANSPORT_TYPES = {"codex_sdk": frozenset({"codex_sdk"}), "openrouter": frozenset({"openrouter"}),
                   "anthropic_api": frozenset({"anthropic_messages"})}


class PinMismatch(E0Stop, RuntimeError):
    """The client a role resolved to is not its frozen pin; nothing was sent
    (an E0 stop: its message is built from pins only, never provider text)."""

    kind = "pin_mismatch"


class RoleCaller(Protocol):
    def call(self, role: str, *, prompt: str, result_model: type[BaseModel], arm: str | None = None) -> Any: ...


@dataclass
class CallRecord:
    """What one role call did: measured latency (the original one on a
    resume), whether it came from a checkpoint, its receipts and identity."""

    role: str
    checkpoint_key: str
    latency_s: float | None
    cached: bool
    model: str | None
    prompt_version: str
    receipts: list[str] = field(default_factory=list)


def role_cost(pin: RolePin, input_tokens: int, output_tokens: int) -> float:
    """The pin's upper-bound price for a request (subscription: $0 billed)."""

    if pin.billing == "subscription":
        return 0.0
    # The long-prompt tier applies past its threshold (Claude Haiku 5.5 above 100k).
    input_price, output_price = pin.prices_for(input_tokens)
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000


def estimate_input_tokens(prompt: Any) -> int:
    """The input UPPER bound admission reserves (bytes, not the bytes/3 estimate)."""

    text = prompt if isinstance(prompt, str) else json.dumps(prompt, ensure_ascii=False, default=str)
    return token_upper_bound(text) + SCHEMA_ALLOWANCE_TOKENS


def resolved_identity(client: Any) -> dict[str, Any]:
    """What a client will actually call: transport, model, endpoint, effort, billing."""

    profile = getattr(client, "profile", None) or getattr(client, "config", None)
    return {
        "provider_type": getattr(client, "provider_type", None),
        "model": getattr(client, "model", None) or getattr(profile, "model", None),
        "endpoint": getattr(profile, "base_url", None),
        "profile_effort": getattr(profile, "reasoning_effort", None),
        "billing": "subscription" if is_subscription_transport(client=client) else "metered",
    }


def check_pin(pin: RolePin, client: Any) -> dict[str, Any]:
    """The resolved identity, or ``PinMismatch`` before any request."""

    identity = resolved_identity(client)
    problems = []
    allowed = TRANSPORT_TYPES.get(pin.transport, frozenset({pin.transport}))
    if identity["provider_type"] not in allowed:
        problems.append(f"transport {identity['provider_type']!r} is not the pinned {pin.transport!r}")
    if identity["model"] != pin.model:
        problems.append(f"model {identity['model']!r} is not the pinned {pin.model!r}")
    if identity["billing"] != pin.billing:
        problems.append(f"billing {identity['billing']!r} is not the pinned {pin.billing!r}")
    if pin.billing == "metered":
        expected = (pins.EXPERIMENT_PROFILES.get(pin.provider_profile)
                    or pins.ANTHROPIC_PROFILES.get(pin.provider_profile) or {}).get("base_url")
        if expected is None or str(identity["endpoint"] or "").rstrip("/") != expected.rstrip("/"):
            problems.append("the metered endpoint is not the experiment's pinned endpoint")
    if problems:
        raise PinMismatch(f"role {pin.role}: " + "; ".join(problems))
    return identity


@dataclass
class _Admission:
    reservation: str
    pin: RolePin
    started: float
    #: The output tokens reserved (charged when the request reports none).
    output_bound: int = 0


class E0RequestGate:
    """A ``learnloop.ai.execution`` request gate admitting through the E0 ledger.

    Billing comes from the resolved client (never assumed from the pin): a
    client whose billing class differs from the pin's is refused."""

    def __init__(self, ledger: E0Ledger, pin: RolePin, *, arm: str | None = None,
                 request_key: str | None = None) -> None:
        self.ledger = ledger
        self.pin = pin
        self.arm = arm
        #: The role call's complete identity (its checkpoint key), on every entry.
        self.request_key = request_key
        self.admitted = 0
        self._lock = threading.Lock()

    def admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> _Admission:
        billing = self.pin.billing if client is None else resolved_identity(client)["billing"]
        if billing != self.pin.billing:
            raise PinMismatch(f"role {self.pin.role}: the request's transport bills {billing}, "
                              f"the pin {self.pin.billing}")
        if billing == "metered" and (budget is None or int(budget) <= 0):
            # An unbounded metered request cannot be reserved: refused before sending.
            raise E0BudgetExceeded(f"{self.pin.role}: a metered request without an output bound is refused")
        problem = pins.price_problem(self.pin)
        if problem is not None:
            # No reservation on an unverified price: it cannot be a hard maximum (High 2).
            raise E0PriceUnverified(problem)
        output = int(budget) if budget is not None else self.pin.output_tokens
        tokens_in = estimate_input_tokens(prompt)
        usd = 0.0 if billing == "subscription" else role_cost(self.pin, tokens_in, output)
        with self._lock:
            attempt = self.admitted
            self.admitted += 1
        reservation = self.ledger.reserve(Request(
            category=self.pin.category, provider=self.pin.provider_profile, route=self.pin.model,
            purpose=f"{self.pin.role}:{purpose}", arm=self.arm, billing=billing, estimated_usd=usd,
            estimated_tokens=tokens_in + output, attempt=attempt, request_key=self.request_key))
        return _Admission(reservation, self.pin, time.monotonic(), output)

    def settle(self, admission: _Admission | None, usage: Mapping[str, Any]) -> None:
        if admission is None:
            return
        cost = usage.get("cost")
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        # An explicit cost or reported input tokens only; anything less is
        # unknown billing and the reservation stands (Codex re-review F21).
        pin = admission.pin
        actual = reconciled_usd(usage, lambda tokens_in, tokens_out: role_cost(pin, tokens_in, tokens_out),
                                output_bound=admission.output_bound)
        self.ledger.settle(admission.reservation, actual_usd=actual,
                           usage={"input_tokens": input_tokens, "output_tokens": output_tokens, "cost": cost},
                           latency_s=round(time.monotonic() - admission.started, 4))


def checkpoint_key(pin: RolePin, prompt: str, result_model: type[BaseModel], *,
                   identity: Mapping[str, Any] | None = None, output_bound: int | None = None) -> str:
    return hashlib.sha256(json.dumps({"pin": pin.as_dict(), "prompt": prompt,
                                      "schema": result_model.model_json_schema(),
                                      "identity": dict(identity or {}), "output_bound": output_bound},
                                     sort_keys=True, default=str).encode()).hexdigest()


class Checkpoints:
    """Validated results by content key (private run directory), each with
    the original measurement (latency, receipts) of the call that paid for it."""

    def __init__(self, directory: Path | None) -> None:
        self.directory = Path(directory) if directory is not None else None
        self._memory: dict[str, Any] = {}
        self._failed: dict[str, Any] = {}

    def get(self, key: str, *, refresh: bool = False) -> dict[str, Any] | None:
        if key in self._memory and not (refresh and self.directory is not None):
            return self._memory[key]
        if self.directory is not None:
            path = self.directory / f"{key}.json"
            if path.exists():
                value = json.loads(path.read_text(encoding="utf-8"))
                if not (isinstance(value, dict) and "result" in value):
                    value = {"result": value, "latency_s": None, "receipts": []}  # an earlier layout
                self._memory[key] = value
                return value
        return None

    def put(self, key: str, value: Mapping[str, Any]) -> None:
        """Durable: the file and its directory are fsynced before returning
        (fix round 4, Medium 11), so a recorded result survives a crash."""

        self._memory[key] = dict(value)
        if self.directory is not None:
            self.directory.mkdir(parents=True, exist_ok=True)
            temporary = self.directory / f".{key}.{os.getpid()}.{threading.get_ident()}.tmp"
            with open(temporary, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(dict(value), sort_keys=True, default=str))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.directory / f"{key}.json")
            directory = os.open(self.directory, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)

    def mark_failed(self, key: str, reservations: Sequence[str], *, failure: Mapping[str, Any] | None = None) -> None:
        """Record, durably, that these admissions of ``key`` ended in a failure
        (nothing to recover: a later run may send the request again), with
        the failure's SAFE record (paid-run round 2): its classification,
        reason, status and details (stop_reason, token counts, max_tokens),
        never provider or model text."""

        known = sorted(set(self.failed_reservations(key)) | {str(item) for item in reservations})
        record = {"reservations": known, "failure": dict(failure) if failure else self.failure(key)}
        self._failed[key] = record
        if self.directory is not None:
            self._durable_write(self.directory / f".{key}.failed.json", json.dumps(record, sort_keys=True))

    def _failed_record(self, key: str) -> dict[str, Any]:
        if key not in self._failed and self.directory is not None:
            path = self.directory / f".{key}.failed.json"
            if path.exists():
                self._failed[key] = json.loads(path.read_text(encoding="utf-8"))
        value = self._failed.get(key)
        if isinstance(value, list):  # the first paid run's format: reservations only
            return {"reservations": [str(item) for item in value], "failure": None}
        return dict(value or {"reservations": [], "failure": None})

    def failed_reservations(self, key: str) -> list[str]:
        return [str(item) for item in self._failed_record(key).get("reservations") or []]

    def failure(self, key: str) -> dict[str, Any] | None:
        """The safe record of this key's last failure (None: none recorded)."""

        value = self._failed_record(key).get("failure")
        return dict(value) if value else None

    def _durable_write(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        with open(temporary, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)

    @contextmanager
    def claim(self, key: str) -> Iterator[None]:
        """An exclusive cross-process claim on one request identity, held
        while it executes (an ``flock`` that the OS releases if the process
        dies). A second worker waits, then finds the first one's checkpoint."""

        if self.directory is None:
            with self._local_lock(key):
                yield
            return
        self.directory.mkdir(parents=True, exist_ok=True)
        with self._local_lock(key), open(self.directory / f".{key}.claim", "a+") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    _locks: dict[str, threading.Lock] = {}
    _locks_guard = threading.Lock()

    @contextmanager
    def _local_lock(self, key: str) -> Iterator[None]:
        with Checkpoints._locks_guard:
            lock = Checkpoints._locks.setdefault(key, threading.Lock())
        with lock:
            yield


@contextmanager
def _collect_receipts(found: list[str]) -> Iterator[None]:
    from learnloop.ai.execution import tee_model_calls

    def observe(action: str, event: Mapping[str, Any]) -> None:
        if action == "start" and event.get("id"):
            found.append(str(event["id"]))

    with tee_model_calls(observe):
        yield


class _Recording:
    """Judgment recording shared by the live and fake callers."""

    records: Any = None
    last: CallRecord | None = None

    def record_judgment(self, *, task: str, left_id: str, right_kind: str | None = None, right_id: str | None = None,
                        verdict: str, score: float | None = None, details: Mapping[str, Any] | None = None,
                        call: CallRecord | None = None) -> str | None:
        """Append one verdict to the experiment repository's ``judgment_ledger``
        (idempotent on resume); None when the caller has no repository."""

        call = call or self.last
        if self.records is None or call is None:
            return None
        return self.records.judgment(task=task, left_id=left_id, right_kind=right_kind, right_id=right_id,
                                     verdict=verdict, score=score, details=details or {}, call=call)


class LiveRoleCaller(_Recording):
    """The real caller (paid run only; tests use fake clients)."""

    def __init__(self, vault_root: Path, config: Any, ledger: E0Ledger, *,
                 checkpoints: Checkpoints, role_pins: Mapping[str, RolePin] | None = None,
                 client_factory: Callable[[str], Any] | None = None, records: Any = None,
                 key_envs: Mapping[str, str | None] | None = None, environ: Mapping[str, str] | None = None,
                 anthropic_transport: Any = None) -> None:
        self.vault_root = Path(vault_root)
        self.key_envs = dict(key_envs or {})
        self.environ = environ
        self.anthropic_transport = anthropic_transport
        self.config = with_experiment_profiles(config)
        self.ledger = ledger
        self.checkpoints = checkpoints
        self.role_pins = dict(role_pins or pins.ROLE_PINS)
        self._client_factory = client_factory
        self._clients: dict[str, tuple[Any, dict[str, Any]]] = {}
        self.records = records
        self.cached = 0
        self.calls = 0
        self.last = None

    def _client(self, pin: RolePin) -> tuple[Any, dict[str, Any]]:
        key = f"{pin.provider_profile}:{pin.role}"
        if key not in self._clients:
            if self._client_factory is not None:
                client = self._client_factory(pin.provider_profile)
            elif pin.transport == "anthropic_api":
                # The experiment-only Messages API transport (re-plan 2026-10-22).
                from learnloop.experiments.contextual_embeddings.anthropic_api import AnthropicMessagesClient

                client = AnthropicMessagesClient(pin, key_env=self.key_envs.get("anthropic") or pins.ANTHROPIC_KEY_ENV,
                                                 environ=self.environ, transport=self.anthropic_transport)
            else:
                from learnloop.ai.routing import client_for_provider

                client = client_for_provider(self.vault_root, self.config, pin.provider_profile,
                                             timeout_seconds=int(pins.REQUEST_TIMEOUT_S))
            self._clients[key] = (client, check_pin(pin, client))
        return self._clients[key]

    def output_bound(self, pin: RolePin) -> int:
        """The pin's hard ``max_tokens`` (Anthropic roles), else the normal
        output-budget policy for the role's profile (never lowered)."""

        from learnloop.ai.output_budget import output_budget

        if pin.max_output_tokens:
            return int(pin.max_output_tokens)

        return int(output_budget(self.config, None, provider=pin.provider_profile))

    def call(self, role: str, *, prompt: str, result_model: type[BaseModel], arm: str | None = None) -> Any:
        from learnloop.ai.execution import generation_limit, requested_reasoning_effort, truncation_retry_allowed
        from learnloop.ai.transport import execute_structured_operation

        from learnloop.experiments.contextual_embeddings.boundary import provider_failure, quiet_provider_logs

        pin = self.role_pins[role]
        try:
            client, identity = self._client(pin)
        except E0Stop:
            raise
        except Exception as exc:  # an absent key, a pin mismatch: sanitized, nothing sent
            failure = provider_failure(exc)
            raise failure from None
        bound = self.output_bound(pin)
        key = checkpoint_key(pin, prompt, result_model, identity=identity, output_bound=bound)
        saved = self.checkpoints.get(key)
        if saved is not None:
            return self._from_checkpoint(role, pin, key, identity, saved, result_model)
        # One claim per complete request identity across threads and processes
        # (fix round 4, Medium 11): a second worker waits, then reuses the result.
        with self.checkpoints.claim(key):
            saved = self.checkpoints.get(key, refresh=True)
            if saved is not None:
                return self._from_checkpoint(role, pin, key, identity, saved, result_model)
            explained = self.checkpoints.failed_reservations(key)
            known = self.checkpoints.failure(key)
            entries = self.ledger.entries_for(key)
            # A failure recorded before failures carried their reason (the first
            # paid run): an admission whose reported output reached the bound
            # stopped at max_tokens by definition.
            hit_bound = any(int((entry.get("usage") or {}).get("output_tokens") or 0) >= bound for entry in entries)
            truncated = (known.get("classification") == "truncated"
                         and (known.get("details") or {}).get("max_tokens") == bound) if known else hit_bound
            if truncated and entries and all(entry["reservation"] in explained for entry in entries):
                known = known or {"details": {"max_tokens": bound, "stop_reason": "max_tokens",
                                              "inferred_from": "ledger output_tokens"}}
                # The same request already stopped at this max_tokens: re-sending
                # it would pay to truncate again (paid-run round 2). The caller
                # splits the work instead (R3: fewer refs per request).
                raise E0ProviderFailure("truncated", reason="known truncated at this max_tokens; not re-sent",
                                        details=known.get("details"))
            if any(entry["reservation"] not in explained for entry in self.ledger.entries_for(key)):
                # Admitted before, neither recorded nor known to have failed (a
                # crash between the charge and the checkpoint): recover the settled
                # response from the receipts, else block; never re-send.
                wire = client.wire_prompt(prompt, result_model) if hasattr(client, "wire_prompt") else prompt
                recovered = self._recover(wire, result_model)
                if recovered is None:
                    raise E0RequestBlocked(f"role {role}: an earlier attempt of this request was admitted but its "
                                           "result was never recorded; pending reconciliation, not re-sent")
                self.checkpoints.put(key, {"result": recovered.model_dump(mode="json"), "latency_s": None,
                                           "receipts": [], "identity": identity, "recovered": True})
                self.last = CallRecord(role, key, None, True, identity.get("model"), pin.prompt_version, [])
                return recovered
            gate = E0RequestGate(self.ledger, pin, arm=arm, request_key=key)
            receipts: list[str] = []
            started = time.monotonic()
            try:
                with ExitStack() as stack:
                    stack.enter_context(quiet_provider_logs())
                    stack.enter_context(gate_model_requests(gate))
                    stack.enter_context(generation_limit(bound))
                    stack.enter_context(truncation_retry_allowed())
                    stack.enter_context(requested_reasoning_effort(pin.reasoning_effort))
                    stack.enter_context(_collect_receipts(receipts))
                    if hasattr(client, "structured"):
                        # The Messages API transport: one admitted POST per request, no tools.
                        result = client.structured(purpose=f"e0_{role}", prompt=prompt, result_model=result_model,
                                                   max_tokens=bound)
                    else:
                        result = execute_structured_operation(client, purpose=f"e0_{role}", prompt=prompt,
                                                              result_model=result_model, isolated=True)
            except BaseException as exc:
                # The attempt's outcome IS recorded (it failed): a later run may retry it.
                self.checkpoints.mark_failed(key, [entry["reservation"] for entry in self.ledger.entries_for(key)],
                                             failure=failure_record(role, exc))
                if isinstance(exc, E0Stop) or not isinstance(exc, Exception):
                    raise
                failure = provider_failure(exc)  # provider text never leaves this boundary (High 8)
                raise failure from None
            latency = round(time.monotonic() - started, 4)
            self.calls += 1
            self.checkpoints.put(key, {"result": result.model_dump(mode="json"), "latency_s": latency,
                                       "receipts": receipts, "identity": identity})
            self.last = CallRecord(role, key, latency, False, identity.get("model"), pin.prompt_version, receipts)
            return result

    def _from_checkpoint(self, role: str, pin: RolePin, key: str, identity: Mapping[str, Any],
                         saved: Mapping[str, Any], result_model: type[BaseModel]) -> Any:
        self.cached += 1
        self.last = CallRecord(role, key, saved.get("latency_s"), True, identity.get("model"),
                               pin.prompt_version, list(saved.get("receipts") or []))
        return result_model.model_validate(saved["result"])

    def _recover(self, prompt: Any, result_model: type[BaseModel]) -> Any | None:
        """A settled response of this exact prompt from the experiment's own
        receipts (a completed receipt whose input is the prompt and whose
        output validates), or None."""

        if self.records is None or not hasattr(self.records, "completed_outputs"):
            return None
        for text in self.records.completed_outputs(prompt):
            candidates = [text]
            if "{" in text and "}" in text:
                candidates.append(text[text.find("{"):text.rfind("}") + 1])
            for candidate in candidates:
                try:
                    return result_model.model_validate_json(candidate)
                except Exception:  # noqa: BLE001 - an unparseable output recovers nothing
                    continue
        return None


def failure_record(role: str, exc: BaseException) -> dict[str, Any]:
    """The SAFE record of a failed role call (paid-run round 2): the role, the
    allowlisted classification, the harness-built reason, the HTTP status
    and the response's safe details; an exception that is not an E0 provider
    failure is named by its type only."""

    if isinstance(exc, E0ProviderFailure):
        return {"role": role, "classification": exc.classification, "reason": exc.reason,
                "status_code": exc.status_code, "request_id": exc.request_id, "details": dict(exc.details)}
    return {"role": role, "classification": getattr(exc, "kind", None) or "unknown", "reason": None,
            "status_code": None, "request_id": None, "details": {}, "type": type(exc).__name__}


def with_experiment_profiles(config: Any) -> Any:
    """A copy of ``config`` with E0's metered profiles added (in memory only).

    A copy that already defines one of those profile names differently is
    refused: the experiment's billing and pins assume its own profile."""

    from learnloop.config import AIProviderConfig

    providers = dict(config.ai.providers)
    for name, profile in pins.EXPERIMENT_PROFILES.items():
        wanted = AIProviderConfig.model_validate(profile)
        existing = providers.get(name)
        if existing is not None and existing != wanted:
            raise PinMismatch(f"the copy already defines the profile {name!r} differently; E0 needs its own")
        providers[name] = wanted
    ai = config.ai.model_copy(update={"providers": providers})
    return config.model_copy(update={"ai": ai})


class FakeRoleCaller(_Recording):
    """Test double: answers from ``respond(role, prompt, result_model)`` and
    still admits every call through the ledger at the pin's estimate.
    ``latency(role, prompt)`` gives each call's simulated latency."""

    def __init__(self, respond: Callable[[str, str, type[BaseModel]], Any], ledger: E0Ledger | None = None, *,
                 role_pins: Mapping[str, RolePin] | None = None, records: Any = None,
                 latency: Callable[[str, str], float] | None = None) -> None:
        self.respond = respond
        self.ledger = ledger
        self.role_pins = dict(role_pins or pins.ROLE_PINS)
        self.calls: list[tuple[str, str]] = []
        self.records = records
        self.latency = latency
        self.last = None

    def call(self, role: str, *, prompt: str, result_model: type[BaseModel], arm: str | None = None) -> Any:
        pin = self.role_pins[role]
        if self.ledger is not None:
            gate = E0RequestGate(self.ledger, pin, arm=arm)
            admission = gate.admit(None, purpose=role, prompt=prompt, budget=16_384)
            gate.settle(admission, {"input_tokens": estimate_input_tokens(prompt), "output_tokens": pin.output_tokens})
        self.calls.append((role, prompt))
        value = self.respond(role, prompt, result_model)
        latency = self.latency(role, prompt) if self.latency is not None else 0.001
        self.last = CallRecord(role, checkpoint_key(pin, prompt, result_model), latency, False, pin.model,
                               pin.prompt_version)
        return value if isinstance(value, BaseModel) else result_model.model_validate(value)


def canary_models(caller: LiveRoleCaller) -> dict[str, Any]:
    """Each pinned Anthropic model id checked before any bulk work (re-plan
    2026-10-22): one tiny admitted request per distinct model, answered as a
    Messages API ``message`` by exactly that model. A client without a
    canary (a test fake) is skipped. A failure raises (an ``E0Stop``)."""

    from learnloop.experiments.contextual_embeddings.boundary import quiet_provider_logs

    checked: dict[str, Any] = {}
    for pin in caller.role_pins.values():
        if pin.transport != "anthropic_api" or pin.model in checked:
            continue
        client, _identity = caller._client(pin)
        if not hasattr(client, "canary"):
            checked[pin.model] = {"status": "skipped", "reason": "no canary on this client"}
            continue
        with quiet_provider_logs(), gate_model_requests(E0RequestGate(caller.ledger, pin, arm="canary")):
            checked[pin.model] = client.canary()
    return checked
