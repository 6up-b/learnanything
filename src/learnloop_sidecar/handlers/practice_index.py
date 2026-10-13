"""Practice-index RPCs: find_practice proposes; nothing here serves or grades."""
from __future__ import annotations

from typing import Any

from pydantic import Field

from learnloop.instructional.policy import caller_for, caller_for_question_event
from learnloop.instructional.practice import propose_practice, service_enabled
from learnloop.practice_index.coverage import coverage_report
from learnloop.practice_index.retrieval import IntentUnavailable, PracticeConstraints, find_practice
from learnloop.practice_index.usage import LEARNER_SIGNALS, record_practice_usage
from learnloop.source_retrieval.policy import PolicyRefused
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


class FindPracticeInput(ParamsModel):
    query: str = Field(min_length=1, max_length=2000)
    limit: int | None = Field(default=None, ge=1, le=20)
    learning_object_ids: list[str] = Field(default_factory=list)
    subjects: list[str] = Field(default_factory=list)
    facet_ids: list[str] = Field(default_factory=list)
    practice_modes: list[str] = Field(default_factory=list)
    exclude_item_ids: list[str] = Field(default_factory=list)
    min_difficulty: float | None = Field(default=None, ge=0, le=1)
    max_difficulty: float | None = Field(default=None, ge=0, le=1)
    rerank: bool | None = None
    # Canonical sources S0-S2a: what the request is for, which arms answer it,
    # the rival hypotheses it targets and the exact filters (§8.1).
    intent: str | None = None
    kinds: str | None = None
    target_hypotheses: list[dict[str, str]] = Field(default_factory=list)
    unattempted_only: bool = False
    exclude_family_ids: list[str] = Field(default_factory=list)
    exclude_revealed_families: bool = False
    facet_match: str = "any"
    allow_generated: bool = True
    max_estimated_minutes: float | None = Field(default=None, gt=0)


class CallerInput(ParamsModel):
    """Who is asking. Only the kind and a reference: the server rebuilds the
    context (item, attempt, cold status) from its own records."""

    kind: str
    ref: str | None = None


class FindPracticeRpcInput(FindPracticeInput):
    caller: CallerInput | None = None
    cursor: dict[str, Any] | None = None


class PracticeUsageInput(ParamsModel):
    proposal_id: str
    practice_item_id: str
    signal: str
    #: The learner's optional words with the tap ("not what I asked: ...").
    text: str | None = Field(default=None, max_length=4000)


class PracticeCoverageInput(ParamsModel):
    min_eligible: int | None = Field(default=None, ge=0)


#: Caller kinds a frontend may name; the server derives the context for each.
FRONTEND_CALLER_KINDS = frozenset({"tutor", "plan", "dl3_box", "reader"})


@method("find_practice", FindPracticeRpcInput)
def find_practice_rpc(ctx: SidecarContext, params: FindPracticeRpcInput) -> dict[str, Any]:
    """Ranked practice proposals for a request; the scheduler still serves.

    With a ``caller`` (the tutor's "Practice this", the plan, DL3's box, the
    Reader), the server rebuilds the caller's context from its own records,
    so a request can narrow but never widen what that context allows."""
    vault, repository = ctx.require_vault()
    values = params.model_dump(exclude={"query", "caller", "cursor"})
    for key in ("intent", "kinds"):
        if values.get(key) is None:
            values.pop(key, None)
    try:
        constraints = PracticeConstraints.from_mapping(values)
        if params.caller is None or not service_enabled(vault):
            result = find_practice(vault, repository, params.query, constraints, origin="rpc")
        else:
            if params.caller.kind not in FRONTEND_CALLER_KINDS:
                raise SidecarError("validation_error", f"Unknown caller kind {params.caller.kind!r}.")
            if params.caller.kind == "tutor":
                if not params.caller.ref:
                    raise SidecarError("validation_error", "A tutor caller names its question event.")
                caller = caller_for_question_event(vault, repository, params.caller.ref)
            else:
                caller = caller_for(repository, params.caller.kind, params.caller.ref)
            result = propose_practice(vault, repository, params.query, constraints, caller=caller,
                                      origin="rpc", cursor=params.cursor, **_injected(vault, repository))
    except PolicyRefused as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    except IntentUnavailable as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    except ValueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)


def _injected(vault: Any, repository: Any = None) -> dict[str, Any]:
    """The service's arms and valuer, injected (practice_index never imports them),
    with the daily plan's minutes estimator built here (the service never imports
    the plan)."""

    from learnloop.instructional.wiring import find_practice_injections

    estimator = None
    if repository is not None:
        from learnloop.daily_plan.estimates import Estimator, load_duration_evidence

        evidence = load_duration_evidence(repository, latency_cap_minutes=vault.config.plan.latency_cap_minutes)
        estimator = Estimator(evidence, read_words_per_minute=vault.config.plan.read_words_per_minute).estimate
    return find_practice_injections(vault, estimator=estimator)


@method("record_practice_usage", PracticeUsageInput)
def record_practice_usage_rpc(ctx: SidecarContext, params: PracticeUsageInput) -> dict[str, Any]:
    """A learner tap on a proposal (practised, skipped, too easy, not what I asked)."""
    _vault, repository = ctx.require_vault()
    if params.signal not in LEARNER_SIGNALS:
        raise SidecarError("validation_error", f"signal must be one of {', '.join(LEARNER_SIGNALS)}")
    try:
        result = record_practice_usage(repository, proposal_id=params.proposal_id,
                                       practice_item_id=params.practice_item_id,
                                       signal=params.signal, text=params.text)
    except ValueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)


@method("get_practice_coverage", PracticeCoverageInput)
def get_practice_coverage(ctx: SidecarContext, params: PracticeCoverageInput) -> dict[str, Any]:
    """Facets with few admissible items (targets for more practice)."""
    vault, repository = ctx.require_vault()
    return versioned(coverage_report(vault, repository, min_eligible=params.min_eligible))
