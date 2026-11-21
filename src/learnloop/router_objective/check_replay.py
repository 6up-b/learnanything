"""A lesson-offer decision's lossless numeric replay payload (the committed-check credit, ``mvp-0.62``): every number
the numeric policy valued the decision's candidates on, as one canonical JSON string with its SHA-256 digest, so a
later report can recompute the decision's values exactly, under the old pricing of committed checks and the new.

Why a string: the trace rounds every float it holds to six decimals (``trace.assemble``), so the numbers cannot be
kept as numbers there. ``json.dumps`` writes each float as its shortest round-trip representation, so decoding gives
back the same bits. No NaN or infinity is accepted (a payload holding one is not written: :func:`record` answers
None and the decision is simply not replayable).

What it holds (:func:`record`): the frozen :class:`types.Inputs`, every candidate :class:`types.Action` with its
branches (an offer's declined branch, a probe's repair, a sequence's steps) as the decision valued them (``proposed``)
and with each typed check turned back into the predecessor's ``(LO, days)`` pair (``old``), the numeric seed, the
final draw count with the first batch's and the ceiling, the rollout options, the clock the inputs were read at, the
versions, and each check's delivery sensors as the offer recorded them. Only numbers, ids and version names: no
question, answer or title.

A leaf over :mod:`types`, :mod:`memory` and :mod:`ad_link` (the dataclasses it encodes) and the standard library.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass, replace
import hashlib
import json
from typing import Any

from learnloop.router_objective.ad_link import AdLink, LessonCurve
from learnloop.router_objective.memory import Combiner
from learnloop.router_objective.types import (
    Action,
    CauseSplit,
    CheckCommitment,
    DatedUse,
    EffectSlope,
    Inputs,
    Learning,
    Price,
    Topic,
)

#: The live writer's payload format (a changed format is a new version).
REPLAY_VERSION = "check_credit_replay_v1"
#: The trace key the payload is written under.
TRACE_KEY = "check_credit_replay"
_CLASSES = (Inputs, Action, Topic, DatedUse, Price, Learning, EffectSlope, CauseSplit, CheckCommitment, AdLink,
            LessonCurve, Combiner)
_REGISTRY = {cls.__name__: cls for cls in _CLASSES}


def encode(value: Any) -> Any:
    """``value`` as plain JSON values: each supported dataclass as ``{"type", "fields"}`` with every field."""

    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _CLASSES:
            raise ValueError(f"unsupported numeric type {type(value).__name__}")
        return {"type": type(value).__name__, "fields": {f.name: encode(getattr(value, f.name)) for f in fields(value)}}
    if isinstance(value, Mapping):
        return {str(key): encode(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [encode(item) for item in value]
    return value


def decode(value: Any) -> Any:
    """:func:`encode`'s inverse (lists come back as tuples); a dataclass missing any field is refused."""

    if isinstance(value, Mapping):
        if set(value) == {"type", "fields"} and value["type"] in _REGISTRY:
            cls = _REGISTRY[value["type"]]
            if set(value["fields"]) != {f.name for f in fields(cls)}:
                raise ValueError("incomplete numeric snapshot")
            return cls(**{key: decode(item) for key, item in value["fields"].items()})
        return {key: decode(item) for key, item in value.items()}
    if isinstance(value, list):
        return tuple(decode(item) for item in value)
    return value


def untyped(action: Action) -> Action:
    """``action`` priced the predecessor's way: each typed check its ``(LO, days)`` pair, through every branch."""

    def back(part: Action | None) -> Action | None:
        if part is None:
            return None
        return replace(part, checks=(),
                       commitments=part.commitments or tuple((check.lo, float(check.days)) for check in part.checks),
                       repair=back(part.repair), declined=back(part.declined),
                       steps=tuple(back(step) for step in part.steps))  # type: ignore[misc]

    out = back(action)
    assert out is not None
    return out


def carries_typed_checks(actions: Sequence[Action]) -> bool:
    """Whether any candidate (or a branch of one) carries typed committed checks."""

    def has(part: Action | None) -> bool:
        return part is not None and (bool(part.checks) or has(part.repair) or has(part.declined)
                                     or any(has(step) for step in part.steps))

    return any(has(action) for action in actions)


def canonical(body: Mapping[str, Any]) -> str:
    return json.dumps(encode(body), sort_keys=True, separators=(",", ":"), allow_nan=False)


def record(inputs: Inputs, actions: Sequence[Action], *, seed: str, draws: int, first_draws: int, max_draws: int,
           as_of: str, options: Mapping[str, Any], versions: Mapping[str, Any],
           sensors: Mapping[str, Any]) -> dict[str, Any] | None:
    """The payload for one decision's numeric answer, or None when a number cannot be written exactly (NaN or an
    infinity) or a type is not one this format knows: such a decision is not replayable, and says nothing else."""

    body = {"inputs": inputs, "proposed_actions": tuple(actions),
            "old_actions": tuple(untyped(action) for action in actions), "seed": seed, "draws": int(draws),
            "first_draws": int(first_draws), "max_draws": int(max_draws), "as_of": as_of,
            "options": dict(options), "versions": dict(versions), "sensors": dict(sensors)}
    try:
        payload = canonical(body)
    except (TypeError, ValueError):
        return None
    return {"version": REPLAY_VERSION, "payload": payload, "sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest()}


def read(stored: Mapping[str, Any]) -> dict[str, Any]:
    """A stored payload decoded, after its version and digest are checked (``ValueError`` otherwise)."""

    if stored.get("version") != REPLAY_VERSION:
        raise ValueError("unsupported replay version")
    payload = stored.get("payload")
    if not isinstance(payload, str) or hashlib.sha256(payload.encode("utf-8")).hexdigest() != stored.get("sha256"):
        raise ValueError("invalid replay digest")
    body = decode(json.loads(payload))
    if not isinstance(body, dict):
        raise ValueError("invalid replay body")
    return body


__all__ = ["REPLAY_VERSION", "TRACE_KEY", "canonical", "carries_typed_checks", "decode", "encode", "read", "record",
           "untyped"]
