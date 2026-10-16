"""The regrade and replay contract mismatch (UX Phase 4 Codex review §8.4).

Fail-first reproductions of the three cases the review recorded, in a split
vault at the latest algorithm version: ``pi_svd_compute_001`` (``setup`` 2 +
``result`` 2), its ``result`` criterion raised to 6 points (maximum 8) and
later lowered. Below the regrade-contract successor an ordinary regrade cited
no assessment contract and replay took the contract from the FIRST live row
citing one, so:

1. a model-graded answer regraded above its original maximum could not be
   saved (replay computed correctness 6/4 = 1.5 and the CHECK rolled the
   regrade back);
2. one regraded within the original maximum was saved but replayed against
   the original maximum (3/4 = 0.75, not the 3/8 = 0.375 the regrade wrote);
3. a self-graded answer regraded under the raised rubric made
   ``rebuild_all_derived_state`` fail the ``correctness <= 1`` CHECK once the
   rubric was lowered (and every later regrade on its learning object failed
   too), or silently rescored it when the lowered rubric still fit.

This module imports only names that exist before the successor, so the same
file runs against the predecessor's code (where every test here fails) and
after it (where every test passes). Fakes only; no network.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    apply_attempt,
    calculate_rubric_score,
)
from learnloop.attempts.grading import resolved_rubric
from learnloop.attempts.regrade import regrade_attempt
from learnloop.clock import FrozenClock
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.diagnosis_fakes import ReviewFakeClient
from tests.split_live_helpers import ReadyRuntime, split_vault
from tests.test_held_grade_evidence import T, _graded_apply, _iso
from tests.test_route_rules_in_grader import ITEM

#: Another item of the same learning object (``lo_svd``), for "every later
#: regrade on that learning object fails too".
SIBLING_ITEM = "pi_svd_compute_002"


class PointsGrader(ReviewFakeClient):
    """A grader fake that awards exactly ``points`` (criterion -> points),
    attributing no error (every mark-down is assessed: the route is not
    divergent, so no own-route rule applies)."""

    def __init__(self, points: dict[str, float], **kwargs) -> None:
        super().__init__(**kwargs)
        self.points = dict(points)

    def _grade_parts(self, context):
        parts = super()._grade_parts(context)
        parts["evidence"] = [
            {**row, "points_awarded": float(self.points.get(row["criterion_id"], 0.0))}
            for row in parts["evidence"]
        ]
        parts["correct"] = True  # no attribution: the mark-downs are the grade
        return parts


def _set_result_points(paths, points: float) -> None:
    """Rewrite ``result``'s worth on the item (the maximum follows the criteria)."""

    data = load_vault(paths.root).practice_items[ITEM].model_dump(mode="json")
    rubric = data["grading_rubric"]
    rubric["criteria"] = [
        {**criterion, "points": points} if criterion["id"] == "result" else criterion
        for criterion in rubric["criteria"]
    ]
    rubric["max_points"] = int(sum(float(criterion["points"]) for criterion in rubric["criteria"]))
    upsert_practice_item(paths.root, data)


def _self_graded_apply(vault, repository, item_id, points, *, attempt_id, when):
    """A self-graded (tier 1) answer through the shared attempt step."""

    rubric = resolved_rubric(vault, vault.practice_items[item_id])
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id, learner_answer_md="an answer", attempt_type="independent_attempt",
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=calculate_rubric_score(rubric, dict(points), []),
                criterion_points=dict(points),
                evidence_rows=[
                    {
                        "id": f"ge_{attempt_id}_{cid}", "criterion_id": cid,
                        "points_awarded": float(value), "evidence": "self", "notes": None,
                        "local_grader_id": "learner", "grader_tier": 1, "created_at": _iso(when),
                    }
                    for cid, value in points.items()
                ],
                error_attributions=[],
                grader_confidence=1.0,
                confidence=3,
                manual_review_reason=None,
                feedback_md="self-graded",
            ),
            grading_source="self",
        ),
        clock=FrozenClock(when),
    )


def _regrade(vault, repository, attempt_id, points, *, when):
    return regrade_attempt(
        vault, repository, repository.fetch_practice_attempt(attempt_id),
        runtime=ReadyRuntime(), client=PointsGrader(points), grading_source="ai",
        clock=FrozenClock(when),
    )


def _grade(repository, attempt_id) -> tuple[int, float]:
    attempt = repository.fetch_practice_attempt(attempt_id)
    return int(attempt["rubric_score"]), float(attempt["correctness"])


@pytest.fixture()
def latest(tmp_path):
    """(paths, vault, repository): a split vault at the latest version."""

    paths, vault, repository = split_vault(tmp_path, version=LATEST_ALGORITHM_VERSION)
    return paths, vault, repository


# -- case 1: a model grade regraded above its original maximum ---------------------------------


def test_case1_a_model_grade_regraded_above_its_original_maximum_is_saved(latest):
    """2/4 under its contract, ``result`` raised to 6 (maximum 8), regraded to
    6 (2 + 4): the regrade commits, and its grade is 6/8 now and after a
    rebuild. Before the successor replay read the original's 4-point contract
    (6/4 = 1.5) and the CHECK rolled the regrade back."""

    paths, vault, repository = latest
    _graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_c1", when=T)
    _set_result_points(paths, 6)
    vault = load_vault(paths.root)

    _regrade(vault, repository, "att_c1", {"setup": 2.0, "result": 4.0}, when=T + timedelta(days=1))

    assert _grade(repository, "att_c1") == (6, 0.75)
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(T + timedelta(days=2)))
    assert _grade(repository, "att_c1") == (6, 0.75)


def test_case1_a_contest_of_a_model_grade_above_its_original_maximum_looks_again(latest):
    """The same regrade from the feedback screen's "I think I was right": the
    grader looked again (before the successor the contest said it could not)."""

    import learnloop_sidecar.handlers  # noqa: F401
    import learnloop_sidecar.handlers.ai_providers as providers
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    paths, vault, repository = latest
    _graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_c1c", when=T)
    _set_result_points(paths, 6)
    ctx = SidecarContext()
    ctx.load(paths.root)
    grader = PointsGrader({"setup": 2.0, "result": 4.0})
    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setattr(providers, "ready_grading_provider",
                            lambda vault, override=None: ("fake", ReadyRuntime(), grader))
        monkeypatch.setattr(providers, "grading_source_for_provider", lambda name: "ai")
        spec = METHOD_REGISTRY["trigger_regrade"]
        bundle = spec.handler(ctx, spec.params_model.model_validate({
            "attemptId": "att_c1c", "learnerReason": "Both steps are there", "contestId": "contest_c1",
        }))
    finally:
        monkeypatch.undo()

    assert bundle["contest"]["regraded"] is True
    assert (bundle["rubricScore"], bundle["correctness"]) == (6, 0.75)


# -- case 2: a model grade regraded within its original maximum --------------------------------


def test_case2_a_model_grade_regraded_within_its_original_maximum_replays_its_own_maximum(latest):
    """Regraded to 3 (1 + 2) under the 8-point rubric: 3/8 = 0.375, as the
    regrade wrote it, now and after a rebuild. Before the successor replay
    resolved the original's 4-point contract and recorded 3/4 = 0.75."""

    paths, vault, repository = latest
    _graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_c2", when=T)
    _set_result_points(paths, 6)
    vault = load_vault(paths.root)

    _regrade(vault, repository, "att_c2", {"setup": 1.0, "result": 2.0}, when=T + timedelta(days=1))

    assert _grade(repository, "att_c2") == (3, 0.375)
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(T + timedelta(days=2)))
    assert _grade(repository, "att_c2") == (3, 0.375)


# -- case 3: a self-graded answer regraded, then the rubric lowered -----------------------------


def _self_graded_regraded_to_six(paths, vault, repository, attempt_id):
    _self_graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id=attempt_id, when=T)
    _set_result_points(paths, 6)
    vault = load_vault(paths.root)
    _regrade(vault, repository, attempt_id, {"setup": 2.0, "result": 4.0}, when=T + timedelta(days=1))
    assert _grade(repository, attempt_id) == (6, 0.75)
    return vault


def test_case3_lowering_the_rubric_after_a_regrade_never_fails_the_rebuild(latest):
    """Self-graded, regraded to 6/8, then ``result`` lowered to 2 (maximum 4):
    the rebuild succeeds and the regraded answer keeps 6/8. Before the
    successor no live row cited a contract, replay read the item (6/4) and
    the rebuild failed the CHECK; every later regrade on the learning object
    failed with it."""

    paths, vault, repository = latest
    _self_graded_regraded_to_six(paths, vault, repository, "att_c3")
    _set_result_points(paths, 2)
    vault = load_vault(paths.root)

    rebuild_all_derived_state(vault, repository, clock=FrozenClock(T + timedelta(days=2)))

    assert _grade(repository, "att_c3") == (6, 0.75)
    # A later regrade of another answer on the same learning object replays
    # this one again, and saves.
    _graded_apply(vault, repository, SIBLING_ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_sib",
                  when=T + timedelta(days=3))
    _regrade(vault, repository, "att_sib", {"setup": 2.0, "result": 2.0}, when=T + timedelta(days=4))
    assert _grade(repository, "att_sib") == (4, 1.0)
    assert _grade(repository, "att_c3") == (6, 0.75)


def test_case3_a_lowered_rubric_that_still_fits_never_rescores_the_regrade(latest):
    """``result`` lowered to 4 instead (maximum 6): the regrade's 6/8 stands.
    Before the successor the rebuild silently rescored it to 6/6 = 1.0."""

    paths, vault, repository = latest
    _self_graded_regraded_to_six(paths, vault, repository, "att_c3b")
    _set_result_points(paths, 4)
    vault = load_vault(paths.root)

    rebuild_all_derived_state(vault, repository, clock=FrozenClock(T + timedelta(days=2)))

    assert _grade(repository, "att_c3b") == (6, 0.75)
