"""Sidecar surface for Meas §3.A6 trace evidence and §3.A8 clarification.

Implementation-plan items 6.2 / 6.3. The services themselves are covered by
``test_conjunctive_instruments.py``; what is tested here is the boundary the
desktop actually consumes, and specifically the three places where a careless
RPC would undo the property the service is protecting:

* an elicitation offered for a *read* rather than a serve, which would put a
  learner-facing event in the record where nothing happened;
* a budget counted from offers rather than from lines actually written, which
  would let rule 4 drift;
* an unavailable grader losing the learner's clarification answer, which is the
  one half of that exchange that cannot be re-run.
"""

from __future__ import annotations

from tests.structured_ai import StructuredClientFake

from datetime import timedelta

import pytest

from learnloop.clock import parse_utc, utc_now_iso
from learnloop.ids import new_ulid
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.attempts.trace_evidence import compose_learner_trace
from learnloop_sidecar.errors import SidecarError
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.helpers import create_basic_vault, seed_due_item

ITEM = "pi_svd_define_001"


@pytest.fixture()
def ctx(tmp_path):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    paths = create_basic_vault(tmp_path / "vault")
    seed_due_item(paths)
    context = SidecarContext()
    context.load(paths.root)
    # Never let a test reach for a real grading provider: "manual" resolves to a
    # never-ready runtime with no client and no subprocess probe.
    context.grading_provider_override = "manual"
    context.paths = paths
    return context


def _call(ctx, name: str, params: dict):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _make_item_underdetermined(ctx) -> None:
    """Stamp the item with a capability whose answer underdetermines the reasoning."""

    path = ctx.paths.practice_item_path("linear-algebra", ITEM)
    document = read_yaml(path)
    document["capability"] = "method_selection"
    write_yaml(path, document)
    ctx.reload(maintenance=False)
    ctx.grading_provider_override = "manual"


def _attempt(
    ctx,
    *,
    session_id: str | None = None,
    answer_md: str = "an answer",
    explanation_md: str | None = None,
) -> str:
    """One recorded attempt, composed the way the submission path composes it.

    ``explanation_md`` is the §3.A6 structured field. The trace is built by the
    module that owns the format, never by pasting a heading into the answer here
    — a test that hand-rolls the delimiter is a test that keeps working after the
    submission path stops producing it.
    """

    vault, repository = ctx.require_vault()
    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM,
            learner_answer_md=compose_learner_trace(answer_md, explanation_md),
            elicited_explanation_md=explanation_md,
            attempt_type="independent_attempt",
            session_id=session_id,
        ),
        SelfGradeInput(criterion_points={"correctness": 2}, confidence=3),
    )
    return result.attempt_id


def _clarify(ctx, attempt_id: str, *, hours: int = 48) -> str:
    _vault, repository = ctx.require_vault()
    now = parse_utc(utc_now_iso())
    assert now is not None
    clarification_id = new_ulid()
    repository.insert_grading_clarification(
        {
            "id": clarification_id,
            "attempt_id": attempt_id,
            "criterion_id": "correctness",
            "reason": "ambiguous_notation",
            "trigger": "hedged_criterion",
            "question_md": "Which of the two readings of your second line did you mean?",
            "expires_at": (now + timedelta(hours=hours)).isoformat().replace("+00:00", "Z"),
        }
    )
    return clarification_id


# ---------------------------------------------------------------------------
# §3.A6 — the elicitation travels on the serve, and only on a serve
# ---------------------------------------------------------------------------


def test_a_read_only_open_makes_no_elicitation_decision_at_all(ctx):
    """No session means no budget to spend, so the honest answer is "none made"
    rather than a fabricated refusal that reads as a declined offer."""

    _make_item_underdetermined(ctx)

    detail = _call(ctx, "get_practice_item", {"practiceItemId": ITEM})

    assert detail["elicitation"] is None


def test_serving_an_underdetermined_item_offers_the_decision_point_prompt(ctx):
    _make_item_underdetermined(ctx)
    session = _call(ctx, "start_session", {"energy": "medium"})

    detail = _call(
        ctx, "get_practice_item", {"practiceItemId": ITEM, "sessionId": session["sessionId"]}
    )

    assert detail["elicitation"]["elicit"] is True
    assert detail["elicitation"]["reason"] == "answer_underdetermines_reasoning"
    assert "why this approach" in detail["elicitation"]["prompt"].lower()


def test_an_item_whose_work_is_its_explanation_is_never_elicited(ctx):
    """The stock item declares no capability, so it falls through to the arm
    that says the answer already shows the reasoning."""

    session = _call(ctx, "start_session", {"energy": "medium"})

    detail = _call(
        ctx, "get_practice_item", {"practiceItemId": ITEM, "sessionId": session["sessionId"]}
    )

    assert detail["elicitation"]["elicit"] is False
    assert detail["elicitation"]["reason"] == "capability_shows_its_work"
    assert detail["elicitation"]["prompt"] is None


def test_the_session_budget_counts_lines_written_not_offers_made(ctx):
    """Two offers the learner ignored must not exhaust the budget; two attempts
    that actually carried a volunteered line must."""

    _make_item_underdetermined(ctx)
    session = _call(ctx, "start_session", {"energy": "medium"})
    session_id = session["sessionId"]
    def served():
        return _call(
            ctx, "get_practice_item", {"practiceItemId": ITEM, "sessionId": session_id}
        )["elicitation"]

    _attempt(ctx, session_id=session_id, answer_md="a plain answer")
    _attempt(ctx, session_id=session_id, answer_md="another plain answer")
    assert served()["elicit"] is True

    _attempt(
        ctx,
        session_id=session_id,
        explanation_md="it was the only method that fits.",
    )
    assert served()["elicit"] is True

    _attempt(
        ctx,
        session_id=session_id,
        explanation_md="the other one needs a square matrix.",
    )
    exhausted = served()
    assert exhausted["elicit"] is False
    assert exhausted["reason"] == "session_budget_exhausted"


def test_a_blank_volunteered_line_spends_no_budget_and_leaves_no_trace(ctx):
    """Rule 3 made structural: an offer the learner ignored produces an answer
    body byte-identical to that of a learner who was never asked, so there is
    nothing for the budget — or anything else — to read as a declined offer."""

    _make_item_underdetermined(ctx)
    session_id = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    _vault, repository = ctx.require_vault()

    for blank in ("", "   ", None):
        _attempt(ctx, session_id=session_id, answer_md="an answer", explanation_md=blank)

    assert repository.session_learner_answers(session_id) == ["an answer"] * 3
    assert _call(
        ctx, "get_practice_item", {"practiceItemId": ITEM, "sessionId": session_id}
    )["elicitation"]["elicit"] is True


def test_the_submission_path_composes_the_trace_so_no_client_knows_the_delimiter(ctx):
    """`explanationMd` is its own submission field. The sidecar joins it into the
    ONE trace the grader reads — which is the point of A6 — but the join happens
    server-side, so the heading is not a contract any surface has to reproduce."""

    _make_item_underdetermined(ctx)
    session_id = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]

    result = _call(
        ctx,
        "submit_attempt",
        {
            "sessionId": session_id,
            "practiceItemId": ITEM,
            "answerMd": "the pseudoinverse",
            "explanationMd": "the matrix is not square",
            "attemptType": "independent_attempt",
            "selfGrade": {"criterionPoints": {"correctness": 2}, "confidence": 3},
        },
    )

    _vault, repository = ctx.require_vault()
    stored = repository.fetch_practice_attempt(result["attemptId"])["learner_answer_md"]
    assert stored.startswith("the pseudoinverse")
    assert "the matrix is not square" in stored
    # And it counts against the budget, from the structured field alone.
    assert len(repository.session_learner_answers(session_id)) == 1


def test_another_sessions_volunteered_lines_do_not_spend_this_sessions_budget(ctx):
    _make_item_underdetermined(ctx)
    spent = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    for _ in range(4):
        _attempt(ctx, session_id=spent, explanation_md="because.")
    fresh = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]

    detail = _call(ctx, "get_practice_item", {"practiceItemId": ITEM, "sessionId": fresh})

    assert detail["elicitation"]["elicit"] is True


# ---------------------------------------------------------------------------
# §3.A6 — the reward is absent, never zero
# ---------------------------------------------------------------------------


def test_trace_evidence_read_withholds_a_reward_when_nothing_extra_was_seen(ctx):
    _vault, repository = ctx.require_vault()
    attempt_id = _attempt(ctx)
    repository.insert_trace_exercised_facets(
        attempt_id, [{"facet_id": "recall", "observation_scope": "declared"}]
    )

    result = _call(ctx, "get_attempt_trace_evidence", {"attemptId": attempt_id})

    assert result["reward"] is None
    assert [row["observationScope"] for row in result["observations"]] == ["declared"]


def test_trace_evidence_read_reports_only_opportunistic_facets_as_the_reward(ctx):
    _vault, repository = ctx.require_vault()
    attempt_id = _attempt(ctx, explanation_md="because it is linear")
    repository.insert_trace_exercised_facets(
        attempt_id,
        [
            {"facet_id": "recall", "observation_scope": "declared"},
            {"facet_id": "f_algebra", "observation_scope": "opportunistic"},
        ],
    )

    result = _call(ctx, "get_attempt_trace_evidence", {"attemptId": attempt_id})

    assert result["reward"] == "Your explanation also demonstrated 1 additional facet."
    assert len(result["observations"]) == 2


def test_the_reward_never_credits_an_explanation_the_learner_did_not_write(ctx):
    """`observation_scope` says whether the ITEM declared the facet, not whether
    the LEARNER volunteered anything. An attempt that was never offered
    elicitation can still carry opportunistic observations — the grader saw an
    extra facet in the ordinary working — and telling that learner "your
    explanation also demonstrated…" claims an explanation that does not exist."""

    _vault, repository = ctx.require_vault()
    attempt_id = _attempt(ctx, answer_md="an answer with no volunteered line")
    repository.insert_trace_exercised_facets(
        attempt_id, [{"facet_id": "f_algebra", "observation_scope": "opportunistic"}]
    )

    result = _call(ctx, "get_attempt_trace_evidence", {"attemptId": attempt_id})

    assert result["reward"] is None
    assert [row["observationScope"] for row in result["observations"]] == ["opportunistic"]


def test_trace_evidence_read_rejects_an_unknown_attempt(ctx):
    with pytest.raises(SidecarError) as exc:
        _call(ctx, "get_attempt_trace_evidence", {"attemptId": "att_missing"})

    assert exc.value.code == "not_found"


# ---------------------------------------------------------------------------
# §3.A8 — the question, and what answering it may and may not do
# ---------------------------------------------------------------------------


def test_an_attempt_with_no_question_reports_none_rather_than_erroring(ctx):
    attempt_id = _attempt(ctx)

    result = _call(ctx, "get_grading_clarification", {"attemptId": attempt_id})

    assert result["clarification"] is None


def test_a_pending_question_is_served_with_its_typed_reason_and_trigger(ctx):
    attempt_id = _attempt(ctx)
    clarification_id = _clarify(ctx, attempt_id)

    result = _call(ctx, "get_grading_clarification", {"attemptId": attempt_id})

    assert result["clarification"]["id"] == clarification_id
    assert result["clarification"]["status"] == "pending"
    assert result["clarification"]["reason"] == "ambiguous_notation"
    assert result["clarification"]["trigger"] == "hedged_criterion"


def test_a_timed_out_question_is_not_re_offered(ctx):
    """The grade has already resolved to the abstention that triggered it, so
    an answer could no longer change anything — offering the box would spend
    learner effort for nothing."""

    attempt_id = _attempt(ctx)
    _clarify(ctx, attempt_id, hours=-1)

    result = _call(ctx, "get_grading_clarification", {"attemptId": attempt_id})

    assert result["clarification"] is None


def test_an_empty_answer_is_refused_rather_than_burning_the_one_question(ctx):
    attempt_id = _attempt(ctx)
    _clarify(ctx, attempt_id)

    with pytest.raises(SidecarError) as exc:
        _call(
            ctx,
            "answer_grading_clarification",
            {"attemptId": attempt_id, "answerMd": "   "},
        )

    assert exc.value.code == "validation_error"
    _vault, repository = ctx.require_vault()
    assert repository.grading_clarification_for_attempt(attempt_id)["answer_md"] is None


def test_an_unavailable_grader_still_persists_the_learners_words(ctx):
    """The answer is the un-backfillable half of the exchange; the re-grade can
    always be re-run. An outage must lose the second and never the first."""

    attempt_id = _attempt(ctx)
    _clarify(ctx, attempt_id)

    result = _call(
        ctx,
        "answer_grading_clarification",
        {"attemptId": attempt_id, "answerMd": "I meant the transpose, not the inverse."},
    )

    assert result["regraded"] is False
    assert result["outcome"] is None
    assert "unavailable" in result["error"]
    assert result["feedback"]["attemptId"] == attempt_id
    _vault, repository = ctx.require_vault()
    stored = repository.grading_clarification_for_attempt(attempt_id)
    assert stored["answer_md"] == "I meant the transpose, not the inverse."


def test_answering_the_same_question_twice_is_a_typed_refusal(ctx):
    attempt_id = _attempt(ctx)
    _clarify(ctx, attempt_id)
    _call(ctx, "answer_grading_clarification", {"attemptId": attempt_id, "answerMd": "the first"})

    with pytest.raises(SidecarError) as exc:
        _call(
            ctx,
            "answer_grading_clarification",
            {"attemptId": attempt_id, "answerMd": "the second"},
        )

    assert exc.value.code == "clarification_unanswerable"


def test_answering_a_question_that_was_never_asked_is_a_typed_refusal(ctx):
    attempt_id = _attempt(ctx)

    with pytest.raises(SidecarError) as exc:
        _call(
            ctx,
            "answer_grading_clarification",
            {"attemptId": attempt_id, "answerMd": "unprompted"},
        )

    assert exc.value.code == "clarification_unanswerable"


# ---------------------------------------------------------------------------
# Maintenance surface: both revert criteria, with their unavailable arms intact
# ---------------------------------------------------------------------------


def test_measurement_health_carries_both_revert_criteria(ctx):
    result = _call(ctx, "get_measurement_health", {})

    assert {"traceEvidence", "clarificationRate"} <= set(result)
    assert result["traceEvidence"]["opportunisticObservations"] == 0
    # Abstains rather than reporting 1.0 (or 0.0) off a handful of rows.
    assert result["traceEvidence"]["opportunisticConcentration"] is None


def test_measurement_health_carries_every_instrument_class_revert_criterion(ctx):
    """Plan item 6.4's four producers shipped CLI-only. A revert criterion only a
    terminal can read is a rung kept on judgement, which §3 forbids."""

    audit = _call(ctx, "get_measurement_health", {})["instrumentAudit"]

    assert [metric["name"] for metric in audit["metrics"]] == [
        "laddered_stem_cross_column_agreement",
        "error_hunt_constructed_response_agreement",
        "contrast_pair_order_effect",
        "discrimination_profile_rejection_rate",
    ]
    assert {"contrastPairCommissioning", "errorHuntOutcomes", "ladderedStems"} <= set(audit)


def test_an_empty_vault_leaves_every_instrument_arm_unavailable_never_zero(ctx):
    """The screen's standing rule, pinned at the producer: a rate over no data
    reports its availability word with its counts beside it. A rendered 0.0 would
    say "this instrument is failing its revert criterion", which is a different —
    and false — claim than "nothing has been measured yet"."""

    audit = _call(ctx, "get_measurement_health", {})["instrumentAudit"]

    for metric in audit["metrics"]:
        assert metric["available"] is False, metric["name"]
        assert metric["value"] is None, metric["name"]
        assert metric["availability"] != "available"
    # Same shape of honesty on the companion counts.
    assert audit["errorHuntOutcomes"]["cleanRotationShare"] is None


def test_a_thin_clarification_denominator_is_unavailable_and_never_zero(ctx):
    attempt_id = _attempt(ctx)
    _clarify(ctx, attempt_id)

    rate = _call(ctx, "get_measurement_health", {})["clarificationRate"]

    assert rate["available"] is False
    assert rate["unavailableReason"] == "no_data"
    assert "rate" not in rate
    assert rate["clarifications"] == 1


# ---------------------------------------------------------------------------
# §3.A8 — an answer whose re-grade never ran is recoverable, not stranded
# ---------------------------------------------------------------------------


def test_an_answer_recorded_without_a_grader_is_awaiting_regrade_not_answered(ctx):
    """The state an earlier version could not represent.

    The learner's answer is persisted BEFORE the re-grade is attempted — the
    answer is the un-backfillable half and the re-grade can always be re-run. A
    provider outage between the two used to leave a clarification reading
    `answered` with no resolved grade behind it: the learner could not resubmit
    (an answer exists) and nothing retried (every other route looks for *pending*
    work). The exchange sat complete and unconsumed.
    """

    from learnloop.clock import utc_now_iso as _now
    from learnloop.attempts.clarification import (
        answer_clarification,
        pending_clarification,
        row_to_clarification,
    )

    vault, repository = ctx.require_vault()
    attempt_id = _attempt(ctx)
    _clarify(ctx, attempt_id)

    result = answer_clarification(
        vault, repository, attempt_id=attempt_id, answer_md="I meant the second reading."
    )

    assert result["regraded"] is False
    assert result["status"] == "awaiting_regrade"
    row = repository.grading_clarification_for_attempt(attempt_id)
    assert row_to_clarification(row).status(now=_now()) == "awaiting_regrade"
    # Not offered again: re-asking would make the answer they already gave worthless.
    assert pending_clarification(repository, attempt_id) is None
    # And it is on the retry queue, which is what makes it recoverable.
    assert len(repository.grading_clarifications_awaiting_regrade()) == 1


def test_the_retry_queue_rebuilds_the_exchange_from_the_stored_question(ctx):
    """A retry must not re-ask, and must not guess at what was asked.

    Both halves are persisted immutably (migration 142) precisely so the re-grade
    can be reconstructed: re-asking would waste the answer already given, and
    inventing the question would attribute the resolved grade to an exchange that
    never happened.
    """

    from learnloop.attempts.clarification import (
        answer_clarification,
        resolve_awaiting_regrades,
    )

    vault, repository = ctx.require_vault()
    attempt_id = _attempt(ctx)
    _clarify(ctx, attempt_id)
    answer_clarification(
        vault, repository, attempt_id=attempt_id, answer_md="the second reading"
    )

    seen: dict[str, object] = {}

    class _RecordingGrader(StructuredClientFake):
        """Captures the context the retry hands the grader, then fails.

        Failing on purpose: this test is about what the retry RECONSTRUCTS, and a
        failure keeps the answer on the queue so the recoverability assertion
        below is about the real state rather than a cleaned-up one.
        """

        provider_name = "test"
        model = "test"

        def run_grading_proposal(self, context):
            seen["exchange"] = context.clarification_exchange
            raise RuntimeError("grader still unavailable")

    results = resolve_awaiting_regrades(
        vault, repository, runtime=None, client=_RecordingGrader()
    )

    exchange = seen["exchange"]
    assert exchange["question_md"].startswith("Which of the two readings")
    assert exchange["answer_md"] == "the second reading"
    assert results[0]["outcome"] == "regrade_failed"
    # Still recoverable: a failed retry keeps the answer, it does not consume it.
    assert len(repository.grading_clarifications_awaiting_regrade()) == 1


def test_the_retry_queue_is_empty_without_a_grader_rather_than_erroring(ctx):
    from learnloop.attempts.clarification import resolve_awaiting_regrades

    vault, repository = ctx.require_vault()

    assert resolve_awaiting_regrades(vault, repository, client=None) == []
