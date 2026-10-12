"""Practice-index RPCs: find_practice proposes; nothing here serves or grades."""
from __future__ import annotations

from typing import Any

from pydantic import Field

from learnloop.practice_index.coverage import coverage_report
from learnloop.practice_index.retrieval import PracticeConstraints, find_practice
from learnloop.practice_index.usage import LEARNER_SIGNALS, record_practice_usage
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


class PracticeUsageInput(ParamsModel):
    proposal_id: str
    practice_item_id: str
    signal: str


class PracticeCoverageInput(ParamsModel):
    min_eligible: int | None = Field(default=None, ge=0)


@method("find_practice", FindPracticeInput)
def find_practice_rpc(ctx: SidecarContext, params: FindPracticeInput) -> dict[str, Any]:
    """Ranked practice proposals for a request; the scheduler still serves."""
    vault, repository = ctx.require_vault()
    try:
        constraints = PracticeConstraints.from_mapping(params.model_dump(exclude={"query"}))
        result = find_practice(vault, repository, params.query, constraints, origin="rpc")
    except ValueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)


@method("record_practice_usage", PracticeUsageInput)
def record_practice_usage_rpc(ctx: SidecarContext, params: PracticeUsageInput) -> dict[str, Any]:
    """A learner tap on a proposal (practised, skipped, too easy, not what I asked)."""
    _vault, repository = ctx.require_vault()
    if params.signal not in LEARNER_SIGNALS:
        raise SidecarError("validation_error", f"signal must be one of {', '.join(LEARNER_SIGNALS)}")
    try:
        result = record_practice_usage(repository, proposal_id=params.proposal_id,
                                       practice_item_id=params.practice_item_id,
                                       signal=params.signal)
    except ValueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)


@method("get_practice_coverage", PracticeCoverageInput)
def get_practice_coverage(ctx: SidecarContext, params: PracticeCoverageInput) -> dict[str, Any]:
    """Facets with few admissible items (targets for more practice)."""
    vault, repository = ctx.require_vault()
    return versioned(coverage_report(vault, repository, min_eligible=params.min_eligible))
