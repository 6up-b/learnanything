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


def test_finished_report_carries_per_item_feedback_and_repairs(tmp_path):
    """The graded answer's feedback and repair reach the learner's report.

    Both were already written at grading time and persisted on the exam answer;
    the report DTO simply never serialized them, so a validator-passed repair
    suggestion was unreachable from any screen. Post-sitting only — this DTO is
    built by ``finish_exam`` and by nothing the learner can reach mid-exam.
    """

    root = create_basic_vault(tmp_path / "vault").root
    ctx = SidecarContext()
    ctx.load(root)
    vault, repository = ctx.require_vault()
    reserve_exam_pool(vault, repository, vault.goals[0], item_count=1)
    session = _call(ctx, "start_exam", {"goalId": "goal_linear_algebra_ml"})
    item_id = session["items"][0]["practiceItemId"]
    answer_md = "I know we need a transformation function"

    graded = ResolvedGrade(
        rubric_score=1,
        criterion_points={"correctness": 1.0},
        evidence_rows=[],
        error_attributions=[],
        grader_confidence=0.9,
        confidence=2,
        manual_review_reason=None,
        feedback_md="The missing step is to choose L(x)=log x.",
        repair_suggestions=[
            {
                "practice_mode": "guided_completion",
                "rationale": "Complete the method the learner already recognized.",
                "operator": "complete_log_transport",
                "expected_minutes": 3.0,
                "learning_object_id": None,
                "repair_validation": {"id": "rv_internal", "status": "valid"},
                "repaired_trace": {
                    "learner_work_prefix": answer_md,
                    "minimal_edit": "Append the choice L(x)=log x.",
                    "regenerated_work": "\n\nTake L(x)=log x.",
                    "repaired_answer_md": answer_md + "\n\nTake L(x)=log x.",
                    "changed_latent_claims": ["The transformation is the logarithm."],
                    "changed_checkpoint_ids": ["select_logarithm"],
                    "prefix_basis": "derived_from_preserve_refs",
                },
            }
        ],
    )
    try:
        record_exam_answer(
            vault,
            repository,
            session["sessionId"],
            item_id,
            answer_md=answer_md,
            resolved_grade=graded,
        )
        report = _call(ctx, "finish_exam", {"sessionId": session["sessionId"]})
    finally:
        ctx.exam_grading.shutdown()
        ctx.ingest_jobs.shutdown()

    outcome = next(
        entry
        for entry in report["itemOutcomes"]
        if entry["practiceItemId"] == item_id
    )
    assert outcome["answerMd"] == answer_md
    assert outcome["feedbackMd"] == "The missing step is to choose L(x)=log x."
    assert outcome["rubricScore"] == 1
    assert outcome["maxPoints"] == 4
    assert outcome["prompt"]

    repair = outcome["repairSuggestions"][0]
    assert repair["rationale"].startswith("Complete the method")
    assert repair["practiceMode"] == "guided_completion"
    assert repair["operator"] == "complete_log_transport"
    trace = repair["repairedTrace"]
    # The parts stay separate so the review pane can label them.
    assert trace["learnerWorkPrefix"] == answer_md
    assert trace["regeneratedWork"] == "\n\nTake L(x)=log x."
    assert trace["repairedAnswerMd"] == answer_md + "\n\nTake L(x)=log x."
    assert trace["minimalEdit"] == "Append the choice L(x)=log x."
    # Internal audit structure stays server-side.
    assert "repairValidation" not in repair
    assert "changedCheckpointIds" not in trace
    assert "prefixBasis" not in trace
