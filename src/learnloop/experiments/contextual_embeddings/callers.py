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

from collections.abc import Callable, Iterator, Mapping
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import threading
import time
from typing import Any, Protocol

from pydantic import BaseModel

from learnloop.ai.execution import gate_model_requests
from learnloop.ai.spend import is_subscription_transport

from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.budget import E0BudgetExceeded, E0Ledger, Request, reconciled_usd
from learnloop.experiments.contextual_embeddings.pins import RolePin, token_upper_bound

#: Structured-output schema allowance added to every input bound.
SCHEMA_ALLOWANCE_TOKENS = 512
#: A pin's transport name -> the provider types its client may report.
TRANSPORT_TYPES = {"codex_sdk": frozenset({"codex_sdk"}), "openrouter": frozenset({"openrouter"})}


class PinMismatch(RuntimeError):
    """The client a role resolved to is not its frozen pin; nothing was sent."""


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
    return (input_tokens * pin.input_price_per_million + output_tokens * pin.output_price_per_million) / 1_000_000


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
        expected = (pins.EXPERIMENT_PROFILES.get(pin.provider_profile) or {}).get("base_url")
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

    def __init__(self, ledger: E0Ledger, pin: RolePin, *, arm: str | None = None) -> None:
        self.ledger = ledger
        self.pin = pin
        self.arm = arm
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
        output = int(budget) if budget is not None else self.pin.output_tokens
        tokens_in = estimate_input_tokens(prompt)
        usd = 0.0 if billing == "subscription" else role_cost(self.pin, tokens_in, output)
        with self._lock:
            attempt = self.admitted
            self.admitted += 1
        reservation = self.ledger.reserve(Request(
            category=self.pin.category, provider=self.pin.provider_profile, route=self.pin.model,
            purpose=f"{self.pin.role}:{purpose}", arm=self.arm, billing=billing, estimated_usd=usd,
            estimated_tokens=tokens_in + output, attempt=attempt))
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

    def get(self, key: str) -> dict[str, Any] | None:
        if key in self._memory:
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
        self._memory[key] = dict(value)
        if self.directory is not None:
            self.directory.mkdir(parents=True, exist_ok=True)
            temporary = self.directory / f".{key}.{threading.get_ident()}.tmp"
            temporary.write_text(json.dumps(dict(value), sort_keys=True, default=str), encoding="utf-8")
            temporary.replace(self.directory / f"{key}.json")


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
                 client_factory: Callable[[str], Any] | None = None, records: Any = None) -> None:
        self.vault_root = Path(vault_root)
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
            else:
                from learnloop.ai.routing import client_for_provider

                client = client_for_provider(self.vault_root, self.config, pin.provider_profile,
                                             timeout_seconds=int(pins.REQUEST_TIMEOUT_S))
            self._clients[key] = (client, check_pin(pin, client))
        return self._clients[key]

    def output_bound(self, pin: RolePin) -> int:
        """The normal output-budget policy for the role's profile (never lowered)."""

        from learnloop.ai.output_budget import output_budget

        return int(output_budget(self.config, None, provider=pin.provider_profile))

    def call(self, role: str, *, prompt: str, result_model: type[BaseModel], arm: str | None = None) -> Any:
        from learnloop.ai.execution import generation_limit, requested_reasoning_effort, truncation_retry_allowed
        from learnloop.ai.transport import execute_structured_operation

        pin = self.role_pins[role]
        client, identity = self._client(pin)
        bound = self.output_bound(pin)
        key = checkpoint_key(pin, prompt, result_model, identity=identity, output_bound=bound)
        saved = self.checkpoints.get(key)
        if saved is not None:
            self.cached += 1
            self.last = CallRecord(role, key, saved.get("latency_s"), True, identity.get("model"),
                                   pin.prompt_version, list(saved.get("receipts") or []))
            return result_model.model_validate(saved["result"])
        gate = E0RequestGate(self.ledger, pin, arm=arm)
        receipts: list[str] = []
        started = time.monotonic()
        with ExitStack() as stack:
            stack.enter_context(gate_model_requests(gate))
            stack.enter_context(generation_limit(bound))
            stack.enter_context(truncation_retry_allowed())
            stack.enter_context(requested_reasoning_effort(pin.reasoning_effort))
            stack.enter_context(_collect_receipts(receipts))
            result = execute_structured_operation(client, purpose=f"e0_{role}", prompt=prompt,
                                                  result_model=result_model, isolated=True)
        latency = round(time.monotonic() - started, 4)
        self.calls += 1
        self.checkpoints.put(key, {"result": result.model_dump(mode="json"), "latency_s": latency,
                                   "receipts": receipts, "identity": identity})
        self.last = CallRecord(role, key, latency, False, identity.get("model"), pin.prompt_version, receipts)
        return result


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
