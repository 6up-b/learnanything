"""What other test files use from ``tests/test_route_rules_in_grader.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.algorithm_versions import ROUTE_RULES_ALGORITHM_VERSION
from learnloop.attempts.ai_contracts import CriterionEvidence
from learnloop.attempts.blind_grading import BlindGradingProposal
from learnloop.attempts.grading_support import RouteCheck
from learnloop.clock import FrozenClock
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.models import Rubric

from tests.diagnosis_fakes import ReviewFakeClient
from tests.split_live_helpers import submit


VERSION = ROUTE_RULES_ALGORITHM_VERSION
ITEM = "pi_svd_compute_001"  # setup (2) + result (2)
#: A route the default fake grades 0/4: ``setup`` with no located error,
#: ``result`` with the located quote "Take the eigenvectors".
ALTERNATIVE = "Take the eigenvectors of A^T A for V, then U = A V Sigma^{-1}."
CLOCK = FrozenClock(datetime(2026, 11, 1, 12, 0, tzinfo=UTC))


class DivergentGrader(ReviewFakeClient):
    """The default fake's grade on a route it reads as divergent
    (``route_check.divergent_route``): ``setup`` marked down with nothing
    located, ``result`` marked down with a quote from the answer (naming no
    facet, so the grade carries no review concern of its own)."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        attributions = [
            row.model_copy(update={"target_evidence_families": [], "target_criterion_ids": ["result"]})
            for row in result.error_attributions
        ]
        update = {"error_attributions": attributions}
        if hasattr(result, "route_check"):
            update["route_check"] = RouteCheck(divergent_route=True, rederivation_md="re-derived")
        return result.model_copy(update=update)


class DivergentUnlocatedGrader(DivergentGrader):
    """0 on every criterion on a divergent route, locating no error."""

    def _blind_grading(self, request, context):
        return super()._blind_grading(request, context).model_copy(update={"error_attributions": []})


class FullCreditGrader(DivergentGrader):
    """Every criterion at full points on a divergent route (validates it)."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        evidence = [row.model_copy(update={"points_awarded": 2.0}) for row in result.criterion_evidence]
        return result.model_copy(update={
            "criterion_evidence": evidence, "rubric_score": 4, "error_attributions": [],
        })


def _support(repository, attempt_id):
    return repository.latest_blind_grade_record(attempt_id)["record"]["grading_support"]


def _schedule(repository):
    state = repository.practice_item_state(ITEM)
    return (state.difficulty, state.stability, state.due_at)


def _first_scheduled_attempt(vault, repository):
    """A validated attempt (full credit: 4/4) that schedules the item, rebuilt
    once so the baseline schedule is replay's (a rebuild of the seeded vault
    alone moves this item's due date by minutes)."""

    first = submit(vault, repository, FullCreditGrader(), answer=ALTERNATIVE, when=CLOCK.now())
    assert repository.fetch_practice_attempt(first.attempt_id)["rubric_score"] == 4
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    return first


def _projection(repository):
    return sorted(
        (cell.facet_id, cell.capability, round(cell.direct_positive_mass, 12),
         round(cell.direct_negative_mass, 12), round(cell.certification_credit, 12))
        for cell in repository.facet_capability_evidence_all()
    )


RUBRIC = Rubric.model_validate({
    "id": "r", "max_points": 4,
    "criteria": [{"id": "setup", "description": "Sets up", "points": 2},
                 {"id": "result", "description": "Concludes", "points": 2}],
})
ANSWER = "Let x be fixed. Then x squared is positive. So the claim holds."


def _proposal(points, attributions=(), fatal=()):
    return BlindGradingProposal(
        local_analysis_md="a", attempt_id="a1", practice_item_id="i",
        criterion_evidence=[CriterionEvidence(criterion_id=cid, points_awarded=p, evidence=f"grader on {cid}")
                            for cid, p in points.items()],
        rubric_score=int(sum(points.values())), fatal_errors=list(fatal),
        error_attributions=list(attributions), grader_confidence=0.9,
    )
