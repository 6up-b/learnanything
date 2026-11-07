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
import hashlib
import json
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
    # The diagnosis's follow-up questions. Each call writes a new report, so it is not retried.
    _short("submit_eliciting_response", retry_safe=False),
)

def _v2_short(name: str, *, retry_safe: bool, constraints=_no_constraint) -> MobileMethod:
    return MobileMethod(name, "V2", "short", retry_safe, constraints)


def _v2_long(name: str, constraints=_no_constraint) -> MobileMethod:
    return MobileMethod(name, "V2", "long", True, constraints)


def _contest_required(params: Mapping[str, Any]) -> None:
    """The phone's regrade is "I think I was right" (UX Phase 4 §7.5): a reason, possibly empty, and
    the contest's own key, which is the job's request id, so a retry records and queues it once."""

    fields = _fields(params)
    if not isinstance(fields.get("learner_reason"), str):
        raise ParamRejected("learner_reason", "learner_reason is required")
    contest = fields.get("contest_id")
    if not isinstance(contest, str) or not contest.strip():
        raise ParamRejected("contest_id", "contest_id is required")


#: Mobile v2 stage V2 (spec §8): Today is the shared plan (J1, J5, J6, owner decision D1), the
#: router's visible decisions (J4), feedback parity without probes (J2, J3 partial) and the item's
#: own hints (J16 partial). ``next_plan_item`` is long-capable (§2.2): a decision at a boundary can
#: call a model (RO4's LLM policy), so it is a job with the 15 s wait. Every plan write that names a
#: session checks its owner in the shared handler (§5.6); the phone's eligibility is the origin's.
#: No generated probe is served or answered (V3), so ``followup_next`` is not here.
_V2 = (
    # J1: Today and the plan with Next.
    _v2_short("get_daily_plan", retry_safe=True),
    _v2_short("get_today_headline", retry_safe=True),
    _v2_short("get_start_summary", retry_safe=True),
    _v2_long("next_plan_item"),
    _v2_short("set_plan_minutes", retry_safe=False),
    _v2_short("plan_keep_going", retry_safe=False),
    _v2_short("plan_more_new", retry_safe=False),
    _v2_short("plan_reading_ended", retry_safe=False),
    # A proposal pick belongs to Find practice, which the phone does not have.
    _v2_short("plan_learner_pick", retry_safe=False,
              constraints=_reject("proposal_id", "source_exercise_import_id")),
    # J4: read only.
    _v2_short("router_objective_explain", retry_safe=True),
    # J2: reveals, the diagnosis card's tap, the contest and the follow-up rating.
    _v2_short("record_answer_display", retry_safe=True),
    _v2_short("record_diagnosis_feedback", retry_safe=False),
    _v2_long("trigger_regrade", _contest_required),
    _v2_short("rate_followup", retry_safe=False),
    # J3 without probes: the held feedback and its ways out, and the optional marks.
    _v2_short("followup_status", retry_safe=True),
    _v2_short("followup_continue_without", retry_safe=False),
    _v2_short("followup_show_anyway", retry_safe=False),
    _v2_short("record_hypothesis_exposure", retry_safe=False),
    _v2_short("record_hypothesis_mark", retry_safe=False),
    # J16 partial: an item's own hint, revealed on the phone (telemetry; submit counts it).
    _v2_short("practice.record_hint_reveal", retry_safe=False),
)

ALLOWLIST: Mapping[str, MobileMethod] = MappingProxyType({entry.name: entry for entry in (*_M2, *_V2)})

#: The plan's methods (J1): the kill switch ``phone_plan`` in ``mobile.toml`` refuses them
#: (``phone_plan_off``), and the phone's Today is M2a's queue again.
PLAN_METHODS = frozenset({
    "get_daily_plan", "get_today_headline", "get_start_summary", "next_plan_item", "set_plan_minutes",
    "plan_keep_going", "plan_more_new", "plan_reading_ended", "plan_learner_pick",
})

#: The phone's API generation (mobile v2 §5.2). v2 adds methods and endpoints and changes no
#: existing contract, so it stays 1; a breaking change would add ``/api/v2/``.
API_VERSION = 1


def allowlist_digest() -> str:
    """What the client was built against, as one hash (mobile v2 §5.2).

    ``GET /api/v1/meta`` answers it and the PWA build embeds it (``phoneMethods.ts``); a
    mismatch is a stale cached app, which offers a reload. It covers what the client's own
    code depends on: each method's name, kind and retry policy, and the API generation.
    The constraints are the host's alone, so a stricter one does not ask the phone to reload.
    """

    rows = [[entry.name, entry.kind, entry.retry_safe] for entry in sorted(ALLOWLIST.values(), key=lambda one: one.name)]
    encoded = json.dumps({"api_version": API_VERSION, "methods": rows}, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


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
