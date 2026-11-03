"""What the phone may call: a frozen mapping, default-deny (spec §4.5, T3).

Each entry names a method that exists in ``METHOD_REGISTRY`` and says how the host
runs it: ``short`` on the RPC worker, ``long`` as a durable accepted job (§6.3).
``retry_safe`` is the client's retry policy (§6.2). Constraints run in the adapter
before dispatch and raise :class:`ParamRejected` (422 ``validation_error``).

Constraints name parameters by their field name; both spellings the sidecar's
``ParamsModel`` accepts (``notes_md_path``, ``notesMdPath``) are the same field.
Anything a phone sends that the method's model does not declare is refused by the
model itself (``extra="forbid"``), so an unknown parameter never reaches a handler.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from types import MappingProxyType
from typing import Any, Callable, Literal, Mapping


class ParamRejected(ValueError):
    """A parameter the phone may not send; the host answers 422 validation_error."""

    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field
        self.message = message


def _snake(name: str) -> str:
    return re.sub(r"(?<=[a-z0-9])([A-Z])", lambda match: "_" + match.group(1).lower(), name)


def _fields(params: Mapping[str, Any]) -> dict[str, Any]:
    return {_snake(str(key)): value for key, value in params.items()}


#: §4.5, last constraint: a parameter naming a vault path, file or directory is
#: rejected for every method. Matched on the field name's words, so ``notes_md_path``
#: matches and ``practice_item_id`` does not.
_PATH_WORDS = frozenset({"path", "paths", "file", "files", "filename", "dir", "directory", "folder", "vault", "root"})


def reject_path_parameters(params: Mapping[str, Any]) -> None:
    for name in _fields(params):
        if _PATH_WORDS.intersection(name.split("_")):
            raise ParamRejected(name, f"{name} is not available from the phone")


def _no_constraint(_params: Mapping[str, Any]) -> None:
    return None


def _reject(*names: str) -> Callable[[Mapping[str, Any]], None]:
    def check(params: Mapping[str, Any]) -> None:
        fields = _fields(params)
        for name in names:
            if fields.get(name) is not None:
                raise ParamRejected(name, f"{name} is not available from the phone")

    return check


def _submission_required(params: Mapping[str, Any]) -> None:
    value = _fields(params).get("submission_id")
    if not isinstance(value, str) or not value.strip():
        raise ParamRejected("submission_id", "submission_id is required")


def _all(*checks: Callable[[Mapping[str, Any]], None]) -> Callable[[Mapping[str, Any]], None]:
    def check(params: Mapping[str, Any]) -> None:
        for one in checks:
            one(params)

    return check


#: The phone has no self-grading UI (§4.5); a stuck or answered submit is graded on
#: the desktop's routes or fails with ``grading_fallback_required``. Photo and voice
#: transcriptions (``answer_transcription_id``) are M2b's and its model has no field yet.
#: A diagnostic probe is never answered on the phone in M2 (§1, §6.4), so no phone answer
#: names a presentation, and neither of the host's workers can add a qualifying probe
#: observation: that is how G10's cap boundary holds for them.
_SUBMIT = _all(_submission_required, _reject("self_grade", "probe_presentation_id"))


@dataclass(frozen=True)
class MobileMethod:
    name: str
    milestone: str
    kind: Literal["short", "long"]
    retry_safe: bool
    param_constraints: Callable[[Mapping[str, Any]], None]


def _short(name: str, *, retry_safe: bool, constraints=_no_constraint) -> MobileMethod:
    return MobileMethod(name, "M2", "short", retry_safe, constraints)


def _long(name: str, constraints=_no_constraint) -> MobileMethod:
    # A long method's acceptance is keyed by request_id, so it is always safe to retry (§6.2).
    return MobileMethod(name, "M2", "long", True, constraints)


_M2 = (
    # Sessions. Starting, adopting and ending are not retried automatically; §6.5's
    # compare-and-swap makes a manual retry safe.
    # ``notes_md_path`` falls to the path rule below; ``replace`` is §6.5's start fresh.
    _short("start_session", retry_safe=False),
    _short("adopt_session", retry_safe=False),
    _short("get_session", retry_safe=True),
    _short("end_session", retry_safe=False),
    _short("update_session_checkpoint", retry_safe=True),
    _short("clear_session_checkpoint", retry_safe=True),
    # Serving: eligibility comes from the origin, never a parameter (§6.4, §6.8).
    # A proposal pick belongs to Find practice, which the phone does not have.
    _short("get_today_queue", retry_safe=True),
    _short("open_queue_item", retry_safe=True),
    _short("get_practice_item", retry_safe=True, constraints=_reject("proposal_id", "source_exercise_import_id")),
    _short("get_probe_contract", retry_safe=True),
    # Answering.
    _short("save_practice_draft", retry_safe=True),
    _long("submit_attempt", _SUBMIT),
    _long("submit_dont_know", _SUBMIT),
    _short("skip_practice_item", retry_safe=False),
    _short("acknowledge_practice_submission", retry_safe=True),
    # Feedback.
    _short("get_feedback", retry_safe=True),
    _short("get_attempt", retry_safe=True),
    _short("get_grading_clarification", retry_safe=True),
    _long("answer_grading_clarification"),
    # Slice 1 landed, so §4.5's "once Slice 1 lands" holds.
    _short("diagnosis_status", retry_safe=True),
)

ALLOWLIST: Mapping[str, MobileMethod] = MappingProxyType({entry.name: entry for entry in _M2})


def validate_envelope(value: object) -> dict:
    if (
        not isinstance(value, dict)
        or set(value) - {"method", "params", "request_id"}
        or not isinstance(value.get("method"), str)
        or not value["method"].strip()
        or not isinstance(value.get("params", {}), dict)
        or ("request_id" in value and (
            not isinstance(value["request_id"], str)
            or not value["request_id"].strip()
            or len(value["request_id"]) > 256
        ))
    ):
        raise ValueError("invalid RPC envelope")
    return value


def check_parameters(method: MobileMethod, params: Mapping[str, Any]) -> None:
    """Every constraint on one call (§4.5), before anything is dispatched."""

    reject_path_parameters(params)
    method.param_constraints(params)
