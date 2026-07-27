from __future__ import annotations

import threading
from types import SimpleNamespace

from learnloop.services.attempts import ResolvedGrade
from learnloop.services.exam_pool import reserve_exam_pool
from learnloop.services.exam_session import record_exam_answer
from learnloop_sidecar.context import SidecarContext

from tests.helpers import create_basic_vault


def _call(ctx: SidecarContext, name: str, params: dict):
    import learnloop_sidecar.handlers  # noqa: F401 - register methods
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _grade() -> ResolvedGrade:
    return ResolvedGrade(
        rubric_score=4,
        criterion_points={"correctness": 4.0},
        evidence_rows=[],
        error_attributions=[],
        grader_confidence=1.0,
        confidence=4,
        manual_review_reason=None,
    )


def test_exam_submit_advances_before_background_grade_finishes(
    tmp_path, monkeypatch
):
    import learnloop_sidecar.handlers.exams as exams

    root = create_basic_vault(tmp_path / "vault").root
    ctx = SidecarContext()
    ctx.load(root)
    vault, repository = ctx.require_vault()
    reserve_exam_pool(vault, repository, vault.goals[0], item_count=1)
    session = _call(ctx, "start_exam", {"goalId": "goal_linear_algebra_ml"})
    item_id = session["items"][0]["practiceItemId"]
    started = threading.Event()
    release = threading.Event()

    monkeypatch.setattr(
        exams,
        "ready_grading_provider",
        lambda vault, override=None: (
            "test",
            SimpleNamespace(ready=True),
            object(),
        ),
    )

    def delayed_grade(
        vault,
        repository,
        client,
        *,
        session_id,
        practice_item_id,
        answer_md,
    ):
        started.set()
        assert release.wait(timeout=5)
        record_exam_answer(
            vault,
            repository,
            session_id,
            practice_item_id,
            answer_md=answer_md,
            resolved_grade=_grade(),
        )

    monkeypatch.setattr(exams, "_grade_and_record_exam_answer", delayed_grade)
    try:
        submitted = _call(
            ctx,
            "submit_exam_answer",
            {
                "sessionId": session["sessionId"],
                "practiceItemId": item_id,
                "answerMd": "A = U Sigma V^T",
            },
        )
        assert started.wait(timeout=1)
        assert submitted["gradingStatus"] == "pending"

        durable = repository.exam_answer(session["sessionId"], item_id)
        assert durable is not None
        assert durable["answer_md"] == "A = U Sigma V^T"
        assert durable["grade"] is None

        resumed = _call(
            ctx, "start_exam", {"goalId": "goal_linear_algebra_ml"}
        )
        assert item_id in resumed["answeredItemIds"]
        assert item_id in resumed["pendingItemIds"]

        release.set()
        ctx.exam_grading.wait_for_session(session["sessionId"])
        assert repository.exam_answer(session["sessionId"], item_id)["grade"] is not None

        finished = _call(
            ctx, "finish_exam", {"sessionId": session["sessionId"]}
        )
        assert finished["sessionId"] == session["sessionId"]
        assert finished["scoreFraction"] == 1.0
    finally:
        release.set()
        ctx.exam_grading.shutdown()
        ctx.ingest_jobs.shutdown()
