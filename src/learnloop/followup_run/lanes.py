"""Which lane a miss takes (spec §4), read after its diagnosis.

**Probe:** the diagnosis leaves two or more current concrete rival causes in the selected
factor (``H_OTHER`` stays in the set and is not counted). **Practice:** the cause is known,
or one hypothesis, or no diagnosis.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.followup_serve import workflow as WF
from learnloop.followup_serve.queue import enqueue_need


@dataclass(frozen=True)
class LaneChoice:
    lane: str
    reason: str
    factor_id: str | None = None
    hypothesis_ids: tuple[str, ...] = field(default_factory=tuple)


def concrete_rivals(repository: Repository, factor: dict[str, Any]) -> tuple[str, ...]:
    """The factor's concrete cause hypotheses that still exist, in its own order."""

    from learnloop.diagnosis.causal_attribution import OPEN_SET_CAUSE_ID

    out: list[str] = []
    for value in factor.get("candidate_causes") or []:
        if not isinstance(value, dict) or value.get("open_set"):
            continue
        hypothesis_id = value.get("hypothesis_id")
        if not hypothesis_id or hypothesis_id == OPEN_SET_CAUSE_ID:
            continue
        if repository.causal_hypothesis(str(hypothesis_id)) is not None:
            out.append(str(hypothesis_id))
    return tuple(dict.fromkeys(out))


def open_rival_factor(vault: Any, repository: Repository, workflow: Mapping[str, Any], *,
                      clock: Clock | None = None) -> str | None:
    """R9, just before :func:`select_lane`: rival causes are all this lane needs, so a miss that
    has them and no factor gets one. Weak cases are the router's to decline. Below the tag and with
    the switch off, nothing changes."""

    from learnloop.diagnosis.causal_attribution import open_rival_causes_factor
    from learnloop.followup_serve.gates import generate_and_serve_on

    if not generate_and_serve_on(vault.config):
        return None
    return open_rival_causes_factor(repository, str(workflow["source_attempt_id"]), clock=clock)


def select_lane(repository: Repository, workflow: dict[str, Any]) -> LaneChoice:
    """The probe lane needs an open factor with two rivals; anything else is practice."""

    factors = repository.unresolved_cause_factors_for_attempt(str(workflow["source_attempt_id"]))
    best: LaneChoice | None = None
    for factor in factors:
        rivals = concrete_rivals(repository, factor)
        if len(rivals) >= 2:
            return LaneChoice("probe", "rival_causes", str(factor["id"]), rivals)
        if best is None and rivals:
            best = LaneChoice("practice", "one_hypothesis", str(factor["id"]), rivals)
    return best or LaneChoice("practice", "no_open_factor" if factors == [] else "no_concrete_cause")


def settle_practice_lane(
    vault: Any,
    repository: Repository,
    row: Mapping[str, Any],
    *,
    reason: str,
    release: str = WF.RELEASE_PRACTICE_LANE,
    clock: Clock | None = None,
) -> bool:
    """The practice lane, or the one fallback: the predecessor's chooser runs once.

    The move, what it closes and the insertion commit together, so a crash leaves none of
    them and a retry runs all of it once; a workflow something else settled inserts nothing.
    """

    from learnloop.attempts.attempts import AttemptResult
    from learnloop.diagnosis.followups import evaluate_attempt_intervention_followup

    workflow_id = str(row["id"])
    attempt_id = str(row["source_attempt_id"])
    work = repository.attempt_completion(attempt_id)
    decision = None
    with repository.atomic():
        if not WF.finish(repository, workflow_id, to_state=WF.SETTLED, reason=reason, release=release,
                         lane=WF.LANE_PRACTICE, from_states=(WF.PENDING,), clock=clock):
            return False
        if work is not None:
            decision = evaluate_attempt_intervention_followup(
                vault, repository, result=AttemptResult.from_dict(work["result"]),
                session_id=row.get("session_id"), normalization_prepared=True,
                applied_probe_episode_id=work.get("applied_probe_episode_id"),
                defer_diagnosis_hooks=True, insertion_only=True, clock=clock,
            )
    if decision is not None and decision.need_id:
        # §4: a recorded need fills in the background, textbook first (S2b).
        enqueue_need(repository, str(decision.need_id), clock=clock)
    return True


__all__ = ["LaneChoice", "concrete_rivals", "open_rival_factor", "select_lane", "settle_practice_lane"]
