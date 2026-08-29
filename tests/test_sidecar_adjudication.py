"""The diagnosis-adjudication overlay's three sidecar methods (A4).

The store is covered by `test_diagnosis_adjudication.py` and the belief arm by
`test_durable_promotion_arms.py`; this file covers only what the handlers add —
the hydrated case context, the verdict/abstention partition surfaced as typed
errors, the stratified order the overlay presents, and the after-verdict line,
which must report what `durable_promotion` actually returned rather than what
the verdict implies.

Every attempt goes through the real `apply_attempt` path, reusing the fixtures
that already drive the arm tests. A hand-built receipt cannot tell a wired
handler from an inert one.
"""

from __future__ import annotations

import pytest

from learnloop.diagnosis.causal_attribution import record_causal_diagnosis_contest
from learnloop.diagnosis.diagnosis_adjudication import (
    ABSTENTION_VERDICTS,
    FILLED_VERDICTS,
    QUEUE_REASONS,
)
from learnloop_sidecar.errors import SidecarError

from tests.test_durable_promotion_arms import CLOCK, LO_ID, STATEMENT, _failure
from tests.test_km2_write_path import build_mvp07_vault


@pytest.fixture()
def ctx(tmp_path):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    paths = build_mvp07_vault(tmp_path / "vault")
    context = SidecarContext()
    context.load(paths.root)
    return context


def _call(ctx, name: str, params: dict):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _case(result, attempt_id: str) -> dict:
    return next(case for case in result["cases"] if case["attemptId"] == attempt_id)


def test_queue_carries_the_words_the_learner_was_shown(ctx):
    _failure(ctx.vault, ctx.repository, attempt_id="att_named")

    result = _call(ctx, "adjudication.queue", {})

    assert result["version"] == 1
    assert result["total"] == 1
    assert [row["reason"] for row in result["countsByReason"]] == list(QUEUE_REASONS)
    case = _case(result, "att_named")
    # The judgeable material: the item, the learner's work (which the anchor's
    # offsets are computed against), and the sentence the learner actually read.
    assert case["prompt"]
    assert case["learnerAnswerMd"] == "Sigma holds eigenvalues."
    assert case["shownToLearner"]["feedbackMd"] == "Sigma holds singular values."
    assert case["learningObjectId"] == LO_ID
    # The system's own claim, frozen — never edited by the adjudicator.
    assert case["systemAbstained"] is False
    assert case["systemAnchor"]["anchorKind"] == "span"
    assert case["systemAnchor"]["quote"] == "eigenvalues"
    assert case["systemRepairClassId"]
    assert case["systemRepairClassId"] in {
        option["id"] for option in case["repairClassOptions"]
    }
    # The partition, stated by the side that enforces it, so the overlay never
    # renders a verdict the store would refuse.
    assert case["allowedVerdicts"] == sorted(FILLED_VERDICTS)

    # A count-only read for a badge: the strata still total, no case is hydrated.
    counted = _call(ctx, "adjudication.queue", {"limit": 0})
    assert counted["total"] == 1
    assert counted["cases"] == []


def test_queue_is_stratified_contests_first_then_abstentions(ctx):
    _failure(ctx.vault, ctx.repository, attempt_id="att_sampled")
    _failure(ctx.vault, ctx.repository, attempt_id="att_abstained", abstain=True)
    _failure(ctx.vault, ctx.repository, attempt_id="att_contested")
    record_causal_diagnosis_contest(
        ctx.vault,
        ctx.repository,
        attempt_id="att_contested",
        response="diagnosis_wrong",
        clock=CLOCK,
    )

    result = _call(ctx, "adjudication.queue", {})

    assert result["total"] == 3
    reasons = [case["queueReason"] for case in result["cases"]]
    # The learner already paid the attention cost; an eval set without
    # abstentions selects toward over-filling. Both lead, in that order.
    assert reasons[0] == "learner_contest"
    assert reasons[1] == "system_abstention"
    assert [case["priority"] for case in result["cases"]] == sorted(
        case["priority"] for case in result["cases"]
    )
    contested = _case(result, "att_contested")
    assert contested["learnerReport"]["response"] == "diagnosis_wrong"
    abstained = _case(result, "att_abstained")
    assert abstained["systemAbstained"] is True
    assert abstained["allowedVerdicts"] == sorted(ABSTENTION_VERDICTS)

    # A stratum filter is a queue filter, not a verdict filter.
    filtered = _call(ctx, "adjudication.queue", {"reasons": ["system_abstention"]})
    assert [case["attemptId"] for case in filtered["cases"]] == ["att_abstained"]
    with pytest.raises(SidecarError) as excinfo:
        _call(ctx, "adjudication.queue", {"reasons": ["not_a_stratum"]})
    assert excinfo.value.code == "invalid_queue_filter"


def test_record_refuses_a_verdict_the_partition_forbids(ctx):
    _failure(ctx.vault, ctx.repository, attempt_id="att_named")
    _failure(ctx.vault, ctx.repository, attempt_id="att_abstained", abstain=True)

    with pytest.raises(SidecarError) as filled:
        _call(
            ctx,
            "adjudication.record",
            {"attemptId": "att_abstained", "verdict": "wrong_anchor"},
        )
    assert filled.value.code == "verdict_requires_filled_diagnosis"
    assert filled.value.details["allowed_verdicts"] == sorted(ABSTENTION_VERDICTS)

    with pytest.raises(SidecarError) as abstention:
        _call(
            ctx,
            "adjudication.record",
            {"attemptId": "att_named", "verdict": "correctly_abstained"},
        )
    assert abstention.value.code == "verdict_requires_abstention"
    assert abstention.value.details["allowed_verdicts"] == sorted(FILLED_VERDICTS)

    # ...and the rest of the store's refusals stay typed rather than internal.
    with pytest.raises(SidecarError) as unknown:
        _call(
            ctx,
            "adjudication.record",
            {"attemptId": "att_named", "verdict": "mostly_right"},
        )
    assert unknown.value.code == "unknown_verdict"
    with pytest.raises(SidecarError) as missing:
        _call(
            ctx,
            "adjudication.record",
            {"attemptId": "att_nonexistent", "verdict": "correct"},
        )
    assert missing.value.code == "no_diagnosis"
    with pytest.raises(SidecarError) as anchorless:
        _call(
            ctx,
            "adjudication.record",
            {"attemptId": "att_named", "verdict": "wrong_anchor"},
        )
    assert anchorless.value.code == "invalid_adjudication"

    # No verdict was recorded by any of the refusals.
    assert _call(ctx, "adjudication.scoreboard", {})["overall"]["records"] == 0


def test_record_reports_the_belief_effect_the_backend_confirms(ctx):
    from learnloop.diagnosis.misconceptions import normalize_text

    _failure(ctx.vault, ctx.repository, attempt_id="att_correct")
    assert ctx.repository.misconceptions_for_learning_object(LO_ID) == []

    result = _call(
        ctx, "adjudication.record", {"attemptId": "att_correct", "verdict": "correct"}
    )

    assert result["adjudication"]["verdict"] == "correct"
    # `correct` asserts the system's anchor and repair WERE right, so they are
    # inherited as the adjudicated ground truth with no extra arguments.
    assert result["adjudication"]["adjudicatedAnchor"]["anchorKind"] == "span"
    assert result["adjudication"]["adjudicatedRepairClassId"]
    assert result["adjudication"]["queueReason"] in QUEUE_REASONS

    durable = ctx.repository.misconceptions_for_learning_object(LO_ID)
    assert len(durable) == 1
    assert normalize_text(durable[0].statement) == normalize_text(STATEMENT)
    # The line the overlay shows is the arm's own report, not an inference from
    # the verdict.
    assert result["effect"]["promoted"] == [durable[0].id]
    assert result["outcome"]["status"] == "promoted"
    assert result["outcome"]["beliefIds"] == [durable[0].id]
    assert result["outcome"]["message"] == "Promoted to a durable belief."

    # The adjudicated case leaves the queue.
    assert _call(ctx, "adjudication.queue", {})["total"] == 0


def test_an_overturning_verdict_says_whether_a_correction_is_owed(ctx):
    _failure(ctx.vault, ctx.repository, attempt_id="att_overturned")
    _call(
        ctx,
        "adjudication.record",
        {"attemptId": "att_overturned", "verdict": "correct"},
    )

    result = _call(
        ctx,
        "adjudication.record",
        {
            "attemptId": "att_overturned",
            "verdict": "wrong_anchor",
            "anchor": {"anchorKind": "whole_answer", "criterionId": "correctness"},
            "repairMd": "Re-derive the factorization from the definition.",
            "rationale": "The divergence is upstream of the naming.",
        },
    )

    assert result["adjudication"]["supersedesId"]
    assert result["outcome"]["status"] == "withdrawn"
    assert result["effect"]["withdrawn"] == result["outcome"]["beliefIds"]
    # The belief was never surfaced to this learner, so A6 owes no correction —
    # and the overlay must not promise one.
    assert result["outcome"]["learnerCorrectionPending"] is False
    assert "never shown to the learner" in result["outcome"]["message"]


def test_a_neutral_verdict_reports_no_belief_change_instead_of_silence(ctx):
    _failure(ctx.vault, ctx.repository, attempt_id="att_neutral")

    result = _call(
        ctx,
        "adjudication.record",
        {
            "attemptId": "att_neutral",
            "verdict": "wrong_repair",
            "repairMd": "Contrast Sigma with the eigenvalue matrix directly.",
        },
    )

    assert result["outcome"]["status"] == "no_belief_change"
    assert result["outcome"]["beliefIds"] == []
    assert "does not move belief state" in result["outcome"]["message"]


def test_scoreboard_keeps_enum_keys_and_refuses_a_flattering_rate(ctx):
    _failure(ctx.vault, ctx.repository, attempt_id="att_board")
    _call(
        ctx, "adjudication.record", {"attemptId": "att_board", "verdict": "correct"}
    )

    board = _call(ctx, "adjudication.scoreboard", {})

    assert board["overall"]["records"] == 1
    # Count maps travel as lists: camelCasing a map keyed by verdict would
    # rename `should_have_abstained` into something the store does not accept.
    assert {row["verdict"]: row["count"] for row in board["overall"]["byVerdict"]}[
        "correct"
    ] == 1
    assert {row["reason"] for row in board["overall"]["byQueueReason"]} == set(
        QUEUE_REASONS
    )
    assert board["overall"]["firstDivergenceAnchorAccuracy"] == 1.0
    # Null, never 1.0, on an empty denominator: this eval set contains no
    # abstention case at all, and the scoreboard says so outright.
    assert board["overall"]["abstentionPrecision"] is None
    assert board["overall"]["abstentionCasesPresent"] is False

    by_reason = _call(ctx, "adjudication.scoreboard", {"groupBy": "queue_reason"})
    assert by_reason["groupBy"] == "queue_reason"
    assert len(by_reason["groups"]) == 1
    with pytest.raises(SidecarError) as excinfo:
        _call(ctx, "adjudication.scoreboard", {"groupBy": "grader_mood"})
    assert excinfo.value.code == "invalid_grouping"
