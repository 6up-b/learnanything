"""Paid LLM roles for E0 (writer, context, labels, adjudicator, tutor, judges).

Each role has one pinned route (``pins.ROLE_PINS``): provider profile,
transport, model, effort, output bound, price bound and prompt version. A
call is one isolated, tool-free structured turn through the existing client
stack (``learnloop.ai.routing.client_for_provider`` and
``learnloop.ai.transport.execute_structured_operation``), so prompts never
reach the vault, files or tools.

**Admission per physical request.** ``E0RequestGate`` is installed with the
existing ``learnloop.ai.execution.gate_model_requests``: the transport
consults it immediately before EVERY physical request (a transport retry or a
JSON repair included) and settles it with the usage the request reported. The
gate admits through the E0 ledger: metered routes reserve their input bound
plus the full output bound at the pin's upper-bound prices; subscription
routes (Codex) are admitted at $0 and tallied ``estimated_only``.

**Resume.** A validated result is checkpointed under a content key of the
role pin, prompt and schema in the run's private directory; a resumed run
reads it instead of paying again. The metered roles' OpenRouter profile is
added to an in-memory copy of the vault's config only.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Protocol

from pydantic import BaseModel

from learnloop.ai.execution import gate_model_requests
from learnloop.ai.spend import is_subscription_transport

from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.budget import E0Ledger, Request
from learnloop.experiments.contextual_embeddings.pins import RolePin, conservative_tokens

#: Structured-output schema allowance added to every input estimate.
SCHEMA_ALLOWANCE_TOKENS = 512


class RoleCaller(Protocol):
    def call(self, role: str, *, prompt: str, result_model: type[BaseModel], arm: str | None = None) -> Any: ...


def role_cost(pin: RolePin, input_tokens: int, output_tokens: int) -> float:
    """The pin's upper-bound price for a request (subscription: $0 billed)."""

    if pin.billing == "subscription":
        return 0.0
    return (input_tokens * pin.input_price_per_million + output_tokens * pin.output_price_per_million) / 1_000_000


def estimate_input_tokens(prompt: Any) -> int:
    text = prompt if isinstance(prompt, str) else json.dumps(prompt, ensure_ascii=False, default=str)
    return conservative_tokens(text) + SCHEMA_ALLOWANCE_TOKENS


@dataclass
class _Admission:
    reservation: str
    pin: RolePin
    started: float


class E0RequestGate:
    """A ``learnloop.ai.execution`` request gate admitting through the E0 ledger."""

    def __init__(self, ledger: E0Ledger, pin: RolePin, *, arm: str | None = None) -> None:
        self.ledger = ledger
        self.pin = pin
        self.arm = arm
        self.admitted = 0

    def admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> _Admission:
        output = int(budget) if budget is not None else self.pin.output_tokens
        tokens_in = estimate_input_tokens(prompt)
        billing = "subscription" if (self.pin.billing == "subscription"
                                     or is_subscription_transport(client=client)) else "metered"
        usd = 0.0 if billing == "subscription" else role_cost(self.pin, tokens_in, output)
        reservation = self.ledger.reserve(Request(
            category=self.pin.category, provider=self.pin.provider_profile, route=self.pin.model,
            purpose=f"{self.pin.role}:{purpose}", arm=self.arm, billing=billing, estimated_usd=usd,
            estimated_tokens=tokens_in + output, attempt=self.admitted))
        self.admitted += 1
        return _Admission(reservation, self.pin, time.monotonic())

    def settle(self, admission: _Admission | None, usage: Mapping[str, Any]) -> None:
        if admission is None:
            return
        cost = usage.get("cost")
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        actual: float | None
        if isinstance(cost, (int, float)) and not isinstance(cost, bool) and cost >= 0:
            actual = float(cost)
        elif isinstance(input_tokens, int) or isinstance(output_tokens, int):
            actual = role_cost(admission.pin, int(input_tokens or 0), int(output_tokens or 0))
        else:
            actual = None  # unknown billing: the reservation stands
        self.ledger.settle(admission.reservation, actual_usd=actual,
                           usage={"input_tokens": input_tokens, "output_tokens": output_tokens, "cost": cost},
                           latency_s=round(time.monotonic() - admission.started, 4))


def checkpoint_key(pin: RolePin, prompt: str, result_model: type[BaseModel]) -> str:
    return hashlib.sha256(json.dumps({"pin": pin.as_dict(), "prompt": prompt,
                                      "schema": result_model.model_json_schema()},
                                     sort_keys=True, default=str).encode()).hexdigest()


class Checkpoints:
    """Validated results by content key (private run directory)."""

    def __init__(self, directory: Path | None) -> None:
        self.directory = Path(directory) if directory is not None else None
        self._memory: dict[str, Any] = {}

    def get(self, key: str) -> Any | None:
        if key in self._memory:
            return self._memory[key]
        if self.directory is not None:
            path = self.directory / f"{key}.json"
            if path.exists():
                self._memory[key] = json.loads(path.read_text(encoding="utf-8"))
                return self._memory[key]
        return None

    def put(self, key: str, value: Any) -> None:
        self._memory[key] = value
        if self.directory is not None:
            self.directory.mkdir(parents=True, exist_ok=True)
            temporary = self.directory / f".{key}.tmp"
            temporary.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
            temporary.replace(self.directory / f"{key}.json")


class LiveRoleCaller:
    """The real caller (paid run only; never used in this stage's tests)."""

    def __init__(self, vault_root: Path, config: Any, ledger: E0Ledger, *,
                 checkpoints: Checkpoints, role_pins: Mapping[str, RolePin] | None = None,
                 client_factory: Callable[[str], Any] | None = None) -> None:
        self.vault_root = Path(vault_root)
        self.config = with_experiment_profiles(config)
        self.ledger = ledger
        self.checkpoints = checkpoints
        self.role_pins = dict(role_pins or pins.ROLE_PINS)
        self._client_factory = client_factory
        self._clients: dict[str, Any] = {}
        self.cached = 0
        self.calls = 0

    def _client(self, profile: str) -> Any:
        if profile not in self._clients:
            if self._client_factory is not None:
                self._clients[profile] = self._client_factory(profile)
            else:
                from learnloop.ai.routing import client_for_provider

                self._clients[profile] = client_for_provider(self.vault_root, self.config, profile,
                                                             timeout_seconds=int(pins.REQUEST_TIMEOUT_S))
        return self._clients[profile]

    def call(self, role: str, *, prompt: str, result_model: type[BaseModel], arm: str | None = None) -> Any:
        from learnloop.ai.transport import execute_structured_operation

        pin = self.role_pins[role]
        key = checkpoint_key(pin, prompt, result_model)
        saved = self.checkpoints.get(key)
        if saved is not None:
            self.cached += 1
            return result_model.model_validate(saved)
        client = self._client(pin.provider_profile)
        gate = E0RequestGate(self.ledger, pin, arm=arm)
        with gate_model_requests(gate):
            result = execute_structured_operation(client, purpose=f"e0_{role}", prompt=prompt,
                                                  result_model=result_model, isolated=True)
        self.calls += 1
        self.checkpoints.put(key, result.model_dump(mode="json"))
        return result


def with_experiment_profiles(config: Any) -> Any:
    """A copy of ``config`` with E0's metered profiles added (in memory only)."""

    from learnloop.config import AIProviderConfig

    providers = dict(config.ai.providers)
    for name, profile in pins.EXPERIMENT_PROFILES.items():
        providers.setdefault(name, AIProviderConfig.model_validate(profile))
    ai = config.ai.model_copy(update={"providers": providers})
    return config.model_copy(update={"ai": ai})


class FakeRoleCaller:
    """Test double: answers from ``respond(role, prompt, result_model)`` and
    still admits every call through the ledger at the pin's estimate."""

    def __init__(self, respond: Callable[[str, str, type[BaseModel]], Any], ledger: E0Ledger | None = None, *,
                 role_pins: Mapping[str, RolePin] | None = None) -> None:
        self.respond = respond
        self.ledger = ledger
        self.role_pins = dict(role_pins or pins.ROLE_PINS)
        self.calls: list[tuple[str, str]] = []

    def call(self, role: str, *, prompt: str, result_model: type[BaseModel], arm: str | None = None) -> Any:
        pin = self.role_pins[role]
        if self.ledger is not None:
            gate = E0RequestGate(self.ledger, pin, arm=arm)
            admission = gate.admit(None, purpose=role, prompt=prompt, budget=None)
            gate.settle(admission, {"input_tokens": estimate_input_tokens(prompt), "output_tokens": pin.output_tokens})
        self.calls.append((role, prompt))
        value = self.respond(role, prompt, result_model)
        return value if isinstance(value, BaseModel) else result_model.model_validate(value)
