"""UX Phase 4: practice and feedback (``docs/specs/ux_learnloop_v1.md`` §7.4, §7.5, §10).

The sidecar half of the phase. Everything here is display or learner-initiated
bookkeeping that replay never reads, so it is a live change behind the
``[ui] practice_feedback`` kill switch, with no algorithm successor. The one
write that later answers read is the reveal ledger's record of the full answer
the plain surface shows (Codex review F1): an existing ledger, counted within
the cold retrieval delay, read only at write time (replay keeps the recorded
``primed`` and admissibility):

* the switch itself reaches the app (``config_dto``);
* the feedback bundle says when a grade is held for review (the surface shows
  "held for review", never a score) and carries the learner's own answer, so
  feedback can show it beside a full answer;
* a regrade shows one rubric row per criterion (usability round 1, M-b: ``r``
  duplicated the row);
* "I think I was right" records the learner's reason through the presentation-
  only claim store and regrades in place through the existing regrade; the
  reason never reaches the grader;
* released short-check feedback marks held grades;
* the session finish names the topics practised, in the ○ ◌ ● vocabulary.

Fakes only; no network, no paid call.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.attempts.regrade import regrade_attempt
from learnloop.attempts.trace_evidence import compose_learner_trace
from learnloop.clock import FrozenClock
from learnloop.config.schema import LearnLoopConfig
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import config_dto
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.serializers import feedback_bundle
from tests.diagnosis_fakes import ReviewFakeClient
from tests.helpers import create_basic_vault, seed_due_item
from tests.split_live_helpers import ReadyRuntime, split_vault
from tests.test_held_grade_evidence import T, _graded_apply, _held_apply
from tests.test_route_rules_in_grader import ITEM as SPLIT_ITEM
from tests.test_route_rules_in_grader import VERSION, FullCreditGrader

ITEM = "pi_svd_define_001"


@pytest.fixture()
def ctx(tmp_path):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    paths = create_basic_vault(tmp_path / "vault")
    seed_due_item(paths)
    context = SidecarContext()
    context.load(paths.root)
    # Never a real grading provider: "manual" is a never-ready runtime.
    context.grading_provider_override = "manual"
    context.paths = paths
    return context


def _call(ctx, name: str, params: dict):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _self_graded(ctx, *, answer="my answer", explanation=None, session_id=None, hints=0,
                 attempt_type="independent_attempt", points=2) -> str:
    vault, repository = ctx.require_vault()
    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM,
            learner_answer_md=compose_learner_trace(answer, explanation),
            elicited_explanation_md=explanation,
            attempt_type=attempt_type,
            hints_used=hints,
            session_id=session_id,
        ),
        SelfGradeInput(criterion_points={"correctness": points}, confidence=3),
    )
    return result.attempt_id


# -- the kill switch -------------------------------------------------------------------------


def test_the_practice_feedback_switch_defaults_to_simple_and_reaches_the_app(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    assert vault.config.ui.practice_feedback == "simple"
    assert config_dto(vault)["ui"] == {"practiceFeedback": "simple"}

    with open(paths.root / "learnloop.toml", "a", encoding="utf-8") as handle:
        handle.write('\n[ui]\npractice_feedback = "classic"\n')
    assert config_dto(load_vault(paths.root))["ui"] == {"practiceFeedback": "classic"}


def test_the_switch_accepts_only_its_two_presentations():
    with pytest.raises(ValueError):
        LearnLoopConfig.model_validate({"ui": {"practice_feedback": "fancy"}})


# -- the feedback bundle ---------------------------------------------------------------------


def test_the_bundle_says_when_a_grade_is_held_for_review(tmp_path):
    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    _graded_apply(vault, repository, SPLIT_ITEM, {"setup": 2.0, "result": 2.0}, attempt_id="att_ok", when=T)
    _held_apply(vault, repository, SPLIT_ITEM, {"setup": 0.0, "result": 0.0},
                attempt_id="att_held", when=T + timedelta(minutes=5))

    assert feedback_bundle(vault, repository, "att_held")["heldForReview"] is True
    assert feedback_bundle(vault, repository, "att_ok")["heldForReview"] is False


def test_the_bundle_carries_the_learners_own_answer_apart_from_the_volunteered_line(ctx):
    vault, repository = ctx.require_vault()
    plain = _self_graded(ctx, answer="Sigma holds the singular values.")
    explained = _self_graded(ctx, answer="U Sigma V^T", explanation="it is the standard factorisation")

    bundle = feedback_bundle(vault, repository, plain)
    assert bundle["learnerAnswerMd"] == "Sigma holds the singular values."
    assert bundle["learnerExplanationMd"] is None
    bundle = feedback_bundle(vault, repository, explained)
    assert bundle["learnerAnswerMd"] == "U Sigma V^T"
    assert bundle["learnerExplanationMd"] == "it is the standard factorisation"


def test_the_bundle_carries_the_question_as_it_was_given(tmp_path):
    """Feedback shows the question beside the answers (§7.5). A method-explicit
    answer is shown against the question it was given, its rendered
    instruction included (method-explicit-3 F3), even after the item's
    required method changed; an ordinary answer carries none (the screen then
    shows the item's own presentation)."""

    from learnloop.db.repositories import Repository
    from learnloop.vault.writer import upsert_practice_item
    from tests.test_durable_promotion_arms import _failure
    from tests.test_km2_write_path import build_mvp07_vault

    paths = build_mvp07_vault(tmp_path / "vault")

    def upsert(**fields):
        data = load_vault(paths.root).practice_items[ITEM].model_dump(mode="json")
        data.update(fields)
        upsert_practice_item(paths.root, data)

    stem = load_vault(paths.root).practice_items[ITEM].prompt
    upsert(required_method={"name": "cofactor expansion", "criterion_ids": ["correctness"]})
    repository = Repository(paths.sqlite_path)
    _failure(load_vault(paths.root), repository, attempt_id="att_method")
    upsert(required_method=None)
    vault = load_vault(paths.root)

    blocks = feedback_bundle(vault, repository, "att_method")["answeredPresentation"]["blocks"]
    shown = [block["markdown"] for block in blocks if block["kind"] in ("prompt", "required_method_instruction")]
    assert shown == [stem, "Use cofactor expansion in your answer."]


def test_an_ordinary_answer_carries_no_answered_presentation(ctx):
    vault, repository = ctx.require_vault()
    attempt_id = _self_graded(ctx, answer="Sigma holds the singular values.")
    assert feedback_bundle(vault, repository, attempt_id)["answeredPresentation"] is None


def test_a_regrade_shows_one_rubric_row_per_criterion(tmp_path):
    """Usability round 1, M-b: ``r`` regraded and the rubric showed every
    criterion twice (the original model rows beside the regrade's)."""

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    _graded_apply(vault, repository, SPLIT_ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_g", when=T)
    regrade_attempt(
        vault, repository, repository.fetch_practice_attempt("att_g"),
        runtime=ReadyRuntime(), client=FullCreditGrader(), grading_source="ai",
        clock=FrozenClock(T + timedelta(days=1)),
    )

    rows = feedback_bundle(vault, repository, "att_g")["criterionEvidence"]
    assert sorted(row["criterionId"] for row in rows) == ["result", "setup"]
    # The rows shown are the regrade's, the grade the attempt now carries.
    assert {row["criterionId"]: row["pointsAwarded"] for row in rows} == {"setup": 2.0, "result": 2.0}


# -- "I think I was right" -------------------------------------------------------------------


def _contest_events(repository):
    return [
        event for event in repository.list_hypothesis_events()
        if event.get("claim_type") == "grade_contest"
    ]


def test_i_think_i_was_right_keeps_the_reason_even_when_the_grader_is_unavailable(ctx):
    _vault, repository = ctx.require_vault()
    attempt_id = _self_graded(ctx, points=0)

    # Codex review F7: a grader that cannot run is not an error once the
    # reason is kept; the bundle says what happened.
    bundle = _call(ctx, "trigger_regrade", {"attemptId": attempt_id, "learnerReason": "I did use the SVD"})
    assert bundle["contest"]["recorded"] is True
    assert bundle["contest"]["regraded"] is False

    responded = [event for event in _contest_events(repository) if event["event_type"] == "responded"]
    assert len(responded) == 1
    payload = responded[0]["response_payload"]
    if isinstance(payload, str):
        import json

        payload = json.loads(payload)
    assert payload == {"response": "i_think_i_was_right", "reason": "I did use the SVD"}


def test_i_think_i_was_right_regrades_in_place_and_never_hands_the_reason_to_the_grader(ctx, monkeypatch):
    import learnloop.attempts.regrade as regrade_module
    import learnloop_sidecar.handlers.ai_providers as providers

    _vault, repository = ctx.require_vault()
    attempt_id = _self_graded(ctx, points=0)
    calls: list[dict] = []
    monkeypatch.setattr(
        providers, "ready_grading_provider", lambda vault, override=None: ("fake", ReadyRuntime(), object())
    )
    monkeypatch.setattr(providers, "grading_source_for_provider", lambda name: "ai")
    monkeypatch.setattr(regrade_module, "regrade_attempt", lambda *args, **kwargs: calls.append(kwargs))

    bundle = _call(ctx, "trigger_regrade", {"attemptId": attempt_id, "learnerReason": "the second line is right"})

    assert bundle["attemptId"] == attempt_id
    assert len(calls) == 1
    # The grader is blind to the learner's argument: the regrade gets no reason.
    assert not any("reason" in key for key in calls[0])
    assert len([e for e in _contest_events(repository) if e["event_type"] == "responded"]) == 1


def test_a_plain_regrade_records_no_contest(ctx):
    _vault, repository = ctx.require_vault()
    attempt_id = _self_graded(ctx, points=0)
    with pytest.raises(SidecarError):
        _call(ctx, "trigger_regrade", {"attemptId": attempt_id})
    assert _contest_events(repository) == []


# -- a short check's released feedback -------------------------------------------------------


def test_released_short_check_feedback_marks_held_grades(tmp_path):
    from learnloop_sidecar.handlers.practice import mark_released_held

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    _graded_apply(vault, repository, SPLIT_ITEM, {"setup": 2.0, "result": 2.0}, attempt_id="att_ok", when=T)
    _held_apply(vault, repository, SPLIT_ITEM, {"setup": 0.0, "result": 0.0},
                attempt_id="att_held", when=T + timedelta(minutes=5))
    payload = {
        "attemptId": "att_ok",
        "probeBlockEnd": {"releasedFeedback": [{"attemptId": "att_ok"}, {"attemptId": "att_held"}]},
    }

    mark_released_held(payload, repository)

    released = payload["probeBlockEnd"]["releasedFeedback"]
    assert [entry["heldForReview"] for entry in released] == [False, True]
    # A result with no block end is left alone.
    untouched = {"attemptId": "att_ok"}
    mark_released_held(untouched, repository)
    assert untouched == {"attemptId": "att_ok"}


# -- the session finish ----------------------------------------------------------------------


def test_the_session_finish_names_a_topic_practised_with_help(ctx):
    vault, _repository = ctx.require_vault()
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    _self_graded(ctx, session_id=session_id, hints=1, attempt_type="hinted_attempt", points=2)

    summary = _call(ctx, "end_session", {"sessionId": session_id})

    item = vault.practice_items[ITEM]
    assert summary["topics"] == [
        {
            "learningObjectId": item.learning_object_id,
            "title": vault.learning_objects[item.learning_object_id].title,
            "evidence": "with_help",
        }
    ]
    # The facet and attempt ids behind it stay out of the payload.
    assert "demonstratedFacetIds" not in summary
    assert "demonstratedAttemptIds" not in summary


def test_the_session_finish_names_a_topic_shown_on_your_own(ctx, monkeypatch):
    import learnloop.learner.session_learning_diff as diff_module

    vault, _repository = ctx.require_vault()
    item = vault.practice_items[ITEM]
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    attempt_id = _self_graded(ctx, session_id=session_id, points=2)
    real = diff_module.session_learning_diff

    def with_credit(vault_arg, repository_arg, sid):
        diff = dict(real(vault_arg, repository_arg, sid))
        diff["demonstrated_facet_ids"] = sorted(item.evidence_facets)
        diff["demonstrated_attempt_ids"] = [attempt_id]
        return diff

    monkeypatch.setattr(diff_module, "session_learning_diff", with_credit)

    summary = _call(ctx, "end_session", {"sessionId": session_id})

    assert [(topic["learningObjectId"], topic["evidence"]) for topic in summary["topics"]] == [
        (item.learning_object_id, "on_your_own")
    ]


def test_a_missed_unassisted_answer_names_no_topic(ctx):
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    _self_graded(ctx, session_id=session_id, points=0)
    assert _call(ctx, "end_session", {"sessionId": session_id})["topics"] == []


def test_the_learning_diff_names_the_facets_it_counts(ctx):
    from learnloop.learner.session_learning_diff import session_learning_diff

    vault, repository = ctx.require_vault()
    diff = session_learning_diff(vault, repository, "no_such_session")
    assert diff["demonstrated_facet_ids"] == []
    assert diff["demonstrated_attempt_ids"] == []
    assert diff["facets_demonstrated"] == 0


def test_display_only_switch_needs_no_successor():
    """The switch is read by the desktop only: no Python module outside the
    config and the app snapshot reads ``config.ui``."""

    import pathlib
    import re

    root = pathlib.Path(__file__).resolve().parents[1] / "src"
    readers = sorted(
        str(path.relative_to(root))
        for path in root.rglob("*.py")
        if re.search(r"config\.ui\b", path.read_text(encoding="utf-8"))
    )
    assert readers == ["learnloop_sidecar/context.py"]


def test_the_optional_line_asks_about_any_question_not_a_case():
    """Usability round 1, m13: "what made this case fit?" sat under questions
    that are not about a case. The one-line prompt now reads for any question
    (display copy only: the grader reads the learner's line, never the prompt)."""

    from learnloop.attempts.trace_evidence import UNDERDETERMINED_CAPABILITIES, decide_elicitation

    [capability] = sorted(UNDERDETERMINED_CAPABILITIES - {"method_selection"})[:1]
    item = type("Item", (), {"capability": capability, "trace_contract": None})()
    config = type("Config", (), {"elicitation_enabled": True, "max_elicitations_per_session": 3})()
    decision = decide_elicitation(item, config=config, elicitations_this_session=0)
    assert decision.elicit
    assert "case" not in decision.prompt.lower()
    assert decision.prompt.startswith("Optional, one line:")


# == Codex review (docs/reviews/ux-phase4-feedback-codex-review.md) ============================


def _reveals(repository, **filters):
    return repository.reveal_events(practice_item_id=ITEM, **filters)


def _next_attempt_primed(repository, *, submission_id=None, answer="a later answer", clock=None) -> bool:
    from learnloop.attempts.attempts import auto_primed_draft

    draft, _total = auto_primed_draft(
        repository,
        AttemptDraft(practice_item_id=ITEM, learner_answer_md=answer, submission_id=submission_id),
        clock=clock,
    )
    return draft.primed


def _later(**delta) -> FrozenClock:
    """A clock ``delta`` after now (the ledger rows here are stamped now)."""

    from datetime import UTC, datetime

    return FrozenClock(datetime.now(UTC) + timedelta(**delta))


def _iso(clock: FrozenClock) -> str:
    from learnloop.clock import utc_now_iso

    return utc_now_iso(clock)


# -- F1: the full answer on feedback is an exposure ------------------------------------------


def test_f1_the_full_answer_shown_on_feedback_is_charged_once_to_the_reveal_ledger(ctx):
    """Feedback's "A full answer" panel is the expected answer itself: showing
    it debits the reveal ledger (once per visit: a retry of the visit's write
    records nothing new), so a retry taken with it in view is primed and an
    unaided response after it is not independent."""

    from learnloop.attempts.reveal_ledger import production_admissibility

    vault, repository = ctx.require_vault()
    attempt_id = _self_graded(ctx, points=0)
    assert not _next_attempt_primed(repository)

    _call(ctx, "record_answer_display", {"attemptId": attempt_id, "displayId": "visit_1"})
    _call(ctx, "record_answer_display", {"attemptId": attempt_id, "displayId": "visit_1"})

    rows = _reveals(repository, source_kind="answer_display")
    assert [(row["attempt_id"], row["amount"]) for row in rows] == [(attempt_id, 1.0)]
    assert _next_attempt_primed(repository)
    item = vault.practice_items[ITEM]
    later = production_admissibility(
        repository, practice_item_id=ITEM, learning_object_id=item.learning_object_id,
        produced_at=_iso(_later(hours=1)),
    )
    assert later.admissible is False


@pytest.mark.parametrize("shown", [False, True])
def test_f1_an_unaided_answer_after_the_full_answer_is_not_independent(ctx, shown):
    """The finding's scenario end to end through the RPCs: feedback shows the
    full answer, then the learner answers "One question, unaided" (the
    eliciting repair). The response is kept, stamped as produced after the
    answer was seen, never as independent evidence."""

    _vault, repository = ctx.require_vault()
    attempt_id = _self_graded(ctx, points=0)
    hypothesis = repository.append_causal_hypothesis(
        episode_key=f"{attempt_id}:seed", attempt_id=attempt_id, learning_object_id="lo_svd_definition",
        cause_scope="learner_state", statement="The transpose rule was not available.",
        statement_normalized="the transpose rule was not available", applicability={"practice_item_id": ITEM},
        status="candidate",
    )
    repository.insert_unresolved_cause_factor(
        attempt_id=attempt_id,
        candidate_causes=[{"hypothesis_id": hypothesis["id"], "version": hypothesis["version"]},
                          {"hypothesis_id": "H_OTHER", "open_set": True}],
        algorithm_version="causal_attribution_p2",
    )
    if shown:
        _call(ctx, "record_answer_display", {"attemptId": attempt_id, "displayId": "visit_1"})

    result = _call(ctx, "submit_eliciting_response", {
        "attemptId": attempt_id, "suggestionIndex": 0, "responseMd": "The rows swap.",
    })

    assert result["admissibleAsIndependent"] is (not shown)


def test_f1_an_unknown_attempt_records_no_display(ctx):
    with pytest.raises(SidecarError) as raised:
        _call(ctx, "record_answer_display", {"attemptId": "att_missing", "displayId": "visit_1"})
    assert raised.value.code == "not_found"


# -- F1: the plain self-grade freezes the trace before it shows a full answer ----------------


def _draft(ctx, session_id, *, submission_id, answer="U Sigma V^T", item=ITEM):
    _call(ctx, "save_practice_draft", {
        "sessionId": session_id, "practiceItemId": item, "answerMd": answer, "submissionId": submission_id,
    })


def _disclose(ctx, session_id, *, submission_id, answer="U Sigma V^T", explanation=None):
    return _call(ctx, "record_self_grade_disclosure", {
        "sessionId": session_id, "practiceItemId": ITEM, "submissionId": submission_id,
        "answerMd": answer, "explanationMd": explanation,
    })


def _submit_self_graded(ctx, session_id, *, submission_id, answer="U Sigma V^T", explanation=None, points=4):
    return _call(ctx, "submit_attempt", {
        "sessionId": session_id, "practiceItemId": ITEM, "answerMd": answer, "explanationMd": explanation,
        "attemptType": "independent_attempt", "submissionId": submission_id,
        "selfGrade": {"criterionPoints": {"correctness": points}, "confidence": 3},
    })


def _checkpoint(ctx, session_id):
    from learnloop_sidecar.context import checkpoint_dto

    _vault, repository = ctx.require_vault()
    return checkpoint_dto(repository.fetch_session_checkpoint(session_id))


def test_f1_the_disclosed_trace_is_kept_in_the_checkpoint_for_a_resume(ctx):
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    _draft(ctx, session_id, submission_id="sub_a")
    _disclose(ctx, session_id, submission_id="sub_a", explanation="it factorises")

    disclosure = _checkpoint(ctx, session_id)["selfGradeDisclosure"]
    assert disclosure == {"submissionId": "sub_a", "answerMd": "U Sigma V^T", "explanationMd": "it factorises"}
    # Later saves of the same draft keep the boundary; nothing reopens it.
    _draft(ctx, session_id, submission_id="sub_a", answer="U Sigma V^T")
    assert _checkpoint(ctx, session_id)["selfGradeDisclosure"] == disclosure


def test_f1_the_frozen_trace_commits_clean_and_charges_the_next_attempt(ctx):
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    _draft(ctx, session_id, submission_id="sub_a")
    _disclose(ctx, session_id, submission_id="sub_a", explanation="it factorises")

    result = _submit_self_graded(ctx, session_id, submission_id="sub_a", explanation="it factorises")

    _vault, repository = ctx.require_vault()
    attempt = repository.fetch_practice_attempt(result["attemptId"])
    # The trace was frozen before the answer was shown: independent, as before.
    assert not attempt["primed"]
    _call(ctx, "acknowledge_practice_submission", {
        "sessionId": session_id, "practiceItemId": ITEM, "submissionId": "sub_a",
    })
    # The answer it was graded against was seen: the next attempt is primed.
    assert [row["attempt_id"] for row in _reveals(repository)] == [result["attemptId"]]
    assert _next_attempt_primed(repository)


@pytest.mark.parametrize("changed", ["answer", "explanation"])
def test_f1_a_trace_changed_after_the_full_answer_was_shown_is_primed(ctx, changed):
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    _draft(ctx, session_id, submission_id="sub_a")
    _disclose(ctx, session_id, submission_id="sub_a", explanation="it factorises")

    result = _submit_self_graded(
        ctx, session_id, submission_id="sub_a",
        answer="A = U Sigma V^T with orthogonal U, V" if changed == "answer" else "U Sigma V^T",
        explanation="it factorises" if changed == "answer" else "the full answer says orthogonal factors",
    )

    _vault, repository = ctx.require_vault()
    assert repository.fetch_practice_attempt(result["attemptId"])["primed"]


@pytest.mark.parametrize("leave", ["another_item", "a_new_draft", "cleared", "session_end"])
def test_f1_an_abandoned_disclosure_primes_the_next_attempt_on_the_item(ctx, leave):
    from tests.helpers import add_followup_item

    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    _draft(ctx, session_id, submission_id="sub_a")
    _disclose(ctx, session_id, submission_id="sub_a")
    _vault, repository = ctx.require_vault()
    assert _reveals(repository) == []

    if leave == "another_item":
        add_followup_item(ctx.paths.root)
        ctx.load(ctx.paths.root)
        _draft(ctx, session_id, submission_id="sub_b", item="pi_svd_define_002")
    elif leave == "a_new_draft":
        _draft(ctx, session_id, submission_id="sub_b")
    elif leave == "cleared":
        _call(ctx, "clear_session_checkpoint", {"sessionId": session_id})
    else:
        _call(ctx, "end_session", {"sessionId": session_id})

    _vault, repository = ctx.require_vault()
    rows = _reveals(repository, source_kind="answer_display")
    assert [(row["attempt_id"], row["amount"]) for row in rows] == [(None, 1.0)]
    assert _next_attempt_primed(repository, submission_id="sub_c")


def test_f1_an_unattempted_disclosed_item_counts_as_shown_for_exam_protection(ctx):
    from learnloop.db.stores.source_service import shown_items

    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    _draft(ctx, session_id, submission_id="sub_a")
    _disclose(ctx, session_id, submission_id="sub_a")
    _call(ctx, "clear_session_checkpoint", {"sessionId": session_id})

    vault, repository = ctx.require_vault()
    with repository.connection() as connection:
        shown = shown_items(connection, [vault.practice_items[ITEM]])
    assert "revealed" in shown.get(ITEM, [])


# -- F3: an unresolved contest enters the grade-review queue ---------------------------------


def _pending_review_attempts(repository) -> list[str]:
    return [row["attempt_id"] for row in repository.pending_grade_reviews()]


def test_f3_an_unresolved_contest_is_queued_for_review_and_adjudication_clears_it(ctx):
    from learnloop.attempts.grade_resolution import append_adjudication

    vault, repository = ctx.require_vault()
    attempt_id = _self_graded(ctx, points=0)
    assert _pending_review_attempts(repository) == []
    head_before = repository.active_interpretation_for_observation(
        repository.observation_by_attempt(attempt_id)["id"]
    )

    bundle = _call(ctx, "trigger_regrade", {
        "attemptId": attempt_id, "learnerReason": "I did use the SVD", "contestId": "contest_1",
    })

    assert bundle["contest"] == {"recorded": True, "regraded": False, "reviewRequested": True}
    assert _pending_review_attempts(repository) == [attempt_id]
    # The flag is append-only and keeps the head's authority exactly.
    observation_id = repository.observation_by_attempt(attempt_id)["id"]
    head = repository.active_interpretation_for_observation(observation_id)
    assert head["id"] != head_before["id"]
    for column in ("response_posterior_json", "certainty_discount", "quarantine_state", "raw_grade_event_id"):
        assert head[column] == head_before[column]
    # A retry of the same contest neither records nor queues it twice.
    _call(ctx, "trigger_regrade", {
        "attemptId": attempt_id, "learnerReason": "I did use the SVD", "contestId": "contest_1",
    })
    assert len([e for e in _contest_events(repository) if e["event_type"] == "responded"]) == 1
    assert _pending_review_attempts(repository) == [attempt_id]
    # The owner's adjudication (``learnloop grading adjudicate``) settles it.
    append_adjudication(
        repository, observation_id=observation_id, administration_id=head["administration_id"],
        reviewed_raw_event_ids=[head["raw_grade_event_id"]], adjudicator_source="human_owner",
        resolved_class=None, resolved_distribution={"correct": 1.0}, vault=vault,
    )
    assert _pending_review_attempts(repository) == []


def test_f3_a_contest_the_regrade_upholds_needs_no_review(ctx, monkeypatch):
    import learnloop.attempts.regrade as regrade_module
    import learnloop_sidecar.handlers.ai_providers as providers

    _vault, repository = ctx.require_vault()
    attempt_id = _self_graded(ctx, points=0)
    monkeypatch.setattr(
        providers, "ready_grading_provider", lambda vault, override=None: ("fake", ReadyRuntime(), object())
    )
    monkeypatch.setattr(providers, "grading_source_for_provider", lambda name: "ai")

    def regrade_to_right(vault, repository_arg, attempt, **kwargs):
        with repository_arg.connection() as connection:
            connection.execute(
                "UPDATE practice_attempts SET rubric_score = 4, correctness = 1.0 WHERE id = ?", (attempt["id"],)
            )
            connection.commit()

    monkeypatch.setattr(regrade_module, "regrade_attempt", regrade_to_right)

    bundle = _call(ctx, "trigger_regrade", {"attemptId": attempt_id, "learnerReason": "", "contestId": "c2"})

    assert bundle["contest"] == {"recorded": True, "regraded": True, "reviewRequested": False}
    assert _pending_review_attempts(repository) == []


def test_f3_a_contest_the_regrade_does_not_uphold_is_queued(ctx, monkeypatch):
    import learnloop.attempts.regrade as regrade_module
    import learnloop_sidecar.handlers.ai_providers as providers

    _vault, repository = ctx.require_vault()
    attempt_id = _self_graded(ctx, points=2)
    monkeypatch.setattr(
        providers, "ready_grading_provider", lambda vault, override=None: ("fake", ReadyRuntime(), object())
    )
    monkeypatch.setattr(providers, "grading_source_for_provider", lambda name: "ai")
    monkeypatch.setattr(regrade_module, "regrade_attempt", lambda *args, **kwargs: None)

    bundle = _call(ctx, "trigger_regrade", {"attemptId": attempt_id, "learnerReason": "x", "contestId": "c3"})

    assert bundle["contest"] == {"recorded": True, "regraded": True, "reviewRequested": True}
    assert _pending_review_attempts(repository) == [attempt_id]


# -- F7: a contest that was never recorded says so -------------------------------------------


def test_f7_a_contest_that_fails_before_any_write_reports_not_recorded(ctx, monkeypatch):
    import learnloop.learner.hypothesis_claims as claims

    _vault, repository = ctx.require_vault()
    attempt_id = _self_graded(ctx, points=0)

    def broken(*args, **kwargs):
        raise RuntimeError("database is locked")

    monkeypatch.setattr(claims, "present_claims", broken)
    with pytest.raises(SidecarError) as raised:
        _call(ctx, "trigger_regrade", {"attemptId": attempt_id, "learnerReason": "x", "contestId": "c4"})
    assert raised.value.code == "contest_not_recorded"
    assert _contest_events(repository) == []
    assert _pending_review_attempts(repository) == []

    with pytest.raises(SidecarError) as raised:
        _call(ctx, "trigger_regrade", {"attemptId": "att_missing", "learnerReason": "x", "contestId": "c5"})
    assert raised.value.code == "not_found"


# -- F4: the session finish credits the attempts that earned the credit ----------------------


def _second_topic(ctx) -> str:
    """A second topic whose question exercises the same facet as ITEM's."""

    from learnloop.vault.writer import upsert_practice_item
    from learnloop.vault.yaml_io import write_yaml

    paths = ctx.paths
    lo = load_vault(paths.root).learning_objects["lo_svd_definition"].model_dump(mode="json")
    lo.update({"id": "lo_svd_compute", "title": "Computing an SVD"})
    write_yaml(paths.learning_object_path("linear-algebra", "lo_svd_compute"), lo)
    item = load_vault(paths.root).practice_items[ITEM].model_dump(mode="json")
    item.update({"id": "pi_svd_compute_001", "learning_object_id": "lo_svd_compute", "prompt": "Compute one."})
    upsert_practice_item(paths.root, item)
    ctx.load(paths.root)
    return "pi_svd_compute_001"


def _graded_on(ctx, item_id, *, session_id, points, hints=0, attempt_type="independent_attempt", primed=False):
    vault, repository = ctx.require_vault()
    return complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="work", attempt_type=attempt_type,
                     hints_used=hints, session_id=session_id, primed=primed),
        SelfGradeInput(criterion_points={"correctness": points}, confidence=3),
    ).attempt_id


@pytest.mark.parametrize("other", ["missed", "held", "assisted"])
def test_f4_a_shared_facet_credits_only_the_topic_whose_answer_earned_it(ctx, monkeypatch, other):
    import learnloop.learner.session_learning_diff as diff_module
    import learnloop.held_grades as held_module

    second = _second_topic(ctx)
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    earned = _graded_on(ctx, ITEM, session_id=session_id, points=4)
    if other == "assisted":
        other_id = _graded_on(ctx, second, session_id=session_id, points=4, hints=1, attempt_type="hinted_attempt")
    else:
        other_id = _graded_on(ctx, second, session_id=session_id, points=0 if other == "missed" else 3)
    if other == "held":
        real_held = held_module.held_attempt_ids
        monkeypatch.setattr(
            held_module, "held_attempt_ids",
            lambda repository, ids=None: frozenset(real_held(repository, ids)) | {other_id},
        )
    real = diff_module.session_learning_diff

    def with_credit(vault_arg, repository_arg, sid):
        # The facet ("recall") is shared by both topics; only `earned` moved it.
        diff = dict(real(vault_arg, repository_arg, sid))
        diff["demonstrated_facet_ids"] = ["recall"]
        diff["demonstrated_attempt_ids"] = [earned]
        return diff

    monkeypatch.setattr(diff_module, "session_learning_diff", with_credit)

    topics = {t["learningObjectId"]: t["evidence"] for t in _call(ctx, "end_session", {"sessionId": session_id})["topics"]}

    expected = {"lo_svd_definition": "on_your_own"}
    if other == "assisted":
        expected["lo_svd_compute"] = "with_help"
    assert topics == expected


def test_f4_the_learning_diff_names_the_attempts_whose_points_raised_a_demonstrated_facet(ctx, monkeypatch):
    import learnloop.learner.session_learning_diff as diff_module
    from learnloop.learner.facet_evidence_timeline import TimelinePoint

    vault, repository = ctx.require_vault()
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    _call(ctx, "end_session", {"sessionId": session_id})
    session = repository.fetch_session(session_id)
    at = session["started_at"]

    def point(attempt_id, delta, *, assisted=False):
        return TimelinePoint(t=at, demonstrated=0.0, delta=delta, kind="observation", is_correction=False,
                             attempt_id=attempt_id, surface_group="g", assisted=assisted,
                             demonstrated_capabilities=())

    monkeypatch.setattr(diff_module, "facet_evidence_timelines", lambda *args, **kwargs: {
        "recall": [point("att_up", 0.4), point("att_flat", 0.0), point("att_helped", 0.2, assisted=True)],
        "other": [point("att_up_then_down", 0.3), point("att_correction", -0.5)],
    })

    diff = diff_module.session_learning_diff(vault, repository, session_id)

    assert diff["demonstrated_facet_ids"] == ["recall"]
    assert diff["demonstrated_attempt_ids"] == ["att_up"]


# -- F5: the question, its answer key and rubric all come from the graded contract -----------


def test_f5_historical_feedback_shows_the_frozen_question_answer_key_and_rubric(ctx):
    from learnloop.vault.writer import upsert_practice_item

    paths = ctx.paths
    _set_canonical_state(paths)
    ctx.load(paths.root)
    vault, repository = ctx.require_vault()
    detail = _call(ctx, "get_practice_item", {"practiceItemId": ITEM})
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    result = _call(ctx, "submit_attempt", {
        "sessionId": session_id, "practiceItemId": ITEM, "answerMd": "U Sigma V^T",
        "attemptType": "independent_attempt", "submissionId": "sub_f5",
        "assessmentContractVersionId": detail["assessmentContractVersionId"],
        "selfGrade": {"criterionPoints": {"correctness": 4}, "confidence": 3},
    })
    attempt_id = result["attemptId"]

    data = load_vault(paths.root).practice_items[ITEM].model_dump(mode="json")
    data["prompt"] = "Define SVD for a 3x2 matrix."
    data["expected_answer"] = "A = U Sigma V^T, U is 3x3."
    data["grading_rubric"]["max_points"] = 8
    data["grading_rubric"]["criteria"] = [{"id": "correctness", "points": 8, "description": "Names all three factors."}]
    upsert_practice_item(paths.root, data)
    ctx.load(paths.root)
    vault, repository = ctx.require_vault()

    bundle = feedback_bundle(vault, repository, attempt_id)

    prompts = [b["markdown"] for b in bundle["answeredPresentation"]["blocks"] if b["kind"] == "prompt"]
    assert prompts == ["Define SVD."]
    assert bundle["answeredExpectedAnswer"] == "A matrix factorization into U, Sigma, and V transpose."
    assert bundle["answeredCriteria"] == [
        {"criterionId": "correctness", "description": "Correct definition.", "pointsPossible": 4.0}
    ]


def _set_canonical_state(paths):
    from learnloop.learner.assessment_contracts import CANONICAL_STATE_VERSIONS
    from tests.helpers import set_algorithm_version

    set_algorithm_version(paths, sorted(CANONICAL_STATE_VERSIONS)[0])


def test_f5_an_answer_with_no_contract_is_unrecorded(ctx):
    """An answer graded before contracts cites none, and nothing recorded says
    what it was graded against (round 3 F9: no inference from the item as it
    is now): no key, criteria or maximum presented as graded."""

    vault, repository = ctx.require_vault()
    attempt_id = _self_graded(ctx, answer="U Sigma V^T")
    bundle = feedback_bundle(vault, repository, attempt_id)
    assert bundle["answeredSource"] == "unrecorded"
    assert bundle["answeredExpectedAnswer"] is None
    assert bundle["answeredCriteria"] is None
    assert bundle["answeredMaxPoints"] is None


# -- F6: a released hold never shows its provisional score in the history --------------------


def test_f6_the_regrade_history_says_the_grade_it_replaced_was_held(tmp_path):
    from tests.test_held_grade_evidence import VALIDATING, _held_live

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    held = _held_live(vault, repository)
    regrade_attempt(
        vault, repository, repository.fetch_practice_attempt(held.attempt_id),
        runtime=ReadyRuntime(), client=VALIDATING(), grading_source="ai",
        clock=FrozenClock(T + timedelta(days=5)),
    )

    bundle = feedback_bundle(vault, repository, held.attempt_id)

    assert bundle["heldForReview"] is False
    assert bundle["regrade"]["oldHeld"] is True


def test_f6_an_ordinary_regrade_history_was_not_held(tmp_path):
    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    _graded_apply(vault, repository, SPLIT_ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_g", when=T)
    regrade_attempt(
        vault, repository, repository.fetch_practice_attempt("att_g"),
        runtime=ReadyRuntime(), client=FullCreditGrader(), grading_source="ai",
        clock=FrozenClock(T + timedelta(days=1)),
    )
    assert feedback_bundle(vault, repository, "att_g")["regrade"]["oldHeld"] is False


def test_f5_a_method_explicit_answer_keeps_its_question_key_and_rubric_together(tmp_path):
    """The finding's scenario: a method-explicit answer, then the item's
    statement, answer key and rubric are all edited. Feedback shows the frozen
    statement (method-explicit-3 F3) and, from the same contract, the frozen
    key and criteria, never today's key beside yesterday's question."""

    from learnloop.db.repositories import Repository
    from learnloop.vault.writer import upsert_practice_item
    from tests.test_durable_promotion_arms import _failure
    from tests.test_km2_write_path import build_mvp07_vault

    paths = build_mvp07_vault(tmp_path / "vault")

    def upsert(**fields):
        data = load_vault(paths.root).practice_items[ITEM].model_dump(mode="json")
        data.update(fields)
        upsert_practice_item(paths.root, data)

    before = load_vault(paths.root).practice_items[ITEM]
    upsert(required_method={"name": "cofactor expansion", "criterion_ids": ["correctness"]})
    repository = Repository(paths.sqlite_path)
    _failure(load_vault(paths.root), repository, attempt_id="att_method")
    rubric = load_vault(paths.root).practice_items[ITEM].model_dump(mode="json")["grading_rubric"]
    rubric["criteria"] = [{**rubric["criteria"][0], "description": "A new criterion wording.", "points": 8}]
    rubric["max_points"] = 8
    upsert(prompt="A different matrix.", expected_answer="A different answer.", grading_rubric=rubric)
    vault = load_vault(paths.root)

    bundle = feedback_bundle(vault, repository, "att_method")

    prompts = [b["markdown"] for b in bundle["answeredPresentation"]["blocks"] if b["kind"] == "prompt"]
    assert prompts == [before.prompt]
    assert bundle["answeredExpectedAnswer"] == before.expected_answer
    [criterion] = before.grading_rubric.criteria
    assert bundle["answeredCriteria"] == [
        {"criterionId": criterion.id, "description": criterion.description, "pointsPossible": float(criterion.points)}
    ]


# -- F1: a routine full-answer display counts within the cold retrieval delay ----------------
#
# The plain surface shows the full answer on EVERY feedback (spec §7.5), so the
# ledger's two readers that had no time bound would otherwise mark every later
# attempt on the item "with help" (auto-prime) and every later production on
# its learning object as not independent (probes, placement, eliciting), a week
# later as much as a minute later. A routine display counts within the cold
# retrieval delay, the horizon every other exposure reader already uses
# (serving exclusions, cold-task deferral, the independent-check rule).


def test_f1_the_routine_display_horizon_is_the_cold_retrieval_delay():
    from learnloop.attempts.reveal_ledger import ROUTINE_ANSWER_DISPLAY_HORIZON
    from learnloop.diagnosis.remediation import COLD_RETRIEVAL_DELAY

    assert ROUTINE_ANSWER_DISPLAY_HORIZON == COLD_RETRIEVAL_DELAY


def _routine_display(ctx, display: str) -> None:
    """One routine full-answer display on ITEM, stamped now."""

    if display == "feedback":
        attempt_id = _self_graded(ctx, points=0)
        _call(ctx, "record_answer_display", {"attemptId": attempt_id, "displayId": "visit_1"})
        return
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    _draft(ctx, session_id, submission_id="sub_r")
    _disclose(ctx, session_id, submission_id="sub_r")
    if display == "self_grade_committed":
        _submit_self_graded(ctx, session_id, submission_id="sub_r")
        _call(ctx, "acknowledge_practice_submission", {
            "sessionId": session_id, "practiceItemId": ITEM, "submissionId": "sub_r",
        })
    else:
        _call(ctx, "clear_session_checkpoint", {"sessionId": session_id})


@pytest.mark.parametrize("display", ["feedback", "self_grade_committed", "self_grade_abandoned"])
def test_f1_a_routine_display_primes_a_retry_but_not_a_review_after_the_cold_delay(ctx, display):
    _routine_display(ctx, display)
    _vault, repository = ctx.require_vault()
    assert len(_reveals(repository, source_kind="answer_display")) == 1

    assert _next_attempt_primed(repository, clock=_later(hours=1))
    assert _next_attempt_primed(repository, clock=_later(hours=23))
    assert not _next_attempt_primed(repository, clock=_later(days=2))


def _review_now(ctx) -> bool:
    """A self-graded answer on ITEM submitted now (the real clock, as the app
    submits); whether it was recorded primed."""

    vault, repository = ctx.require_vault()
    result = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=ITEM, learner_answer_md="U Sigma V^T", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=3),
    )
    return bool(repository.fetch_practice_attempt(result.attempt_id)["primed"])


@pytest.mark.parametrize(("ago", "primed"), [(timedelta(days=3), False), (timedelta(minutes=5), True)])
def test_f1_a_review_after_the_cold_delay_is_recorded_unprimed_a_retry_before_it_primed(ctx, ago, primed):
    """End to end: the earlier attempt and its feedback's full answer are
    stamped ``ago``. A review the scheduler serves days later is a retrieval,
    as every feedback before Phase 4 left it; the same answer minutes later is
    a retry with the answer in view."""

    from datetime import UTC, datetime

    from learnloop.attempts.reveal_ledger import record_feedback_answer_display_reveal

    vault, repository = ctx.require_vault()
    then = FrozenClock(datetime.now(UTC) - ago)
    earlier = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=ITEM, learner_answer_md="my answer", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=3),
        clock=then,
    ).attempt_id
    record_feedback_answer_display_reveal(
        repository, attempt_id=earlier, practice_item_id=ITEM,
        learning_object_id=vault.practice_items[ITEM].learning_object_id,
        display_id="visit_then", clock=then,
    )

    assert _review_now(ctx) is primed


@pytest.mark.parametrize("display", ["feedback", "self_grade_committed", "self_grade_abandoned"])
@pytest.mark.parametrize("target", ["item", "sibling"])
def test_f1_a_production_after_the_cold_delay_is_independent_again(ctx, display, target):
    """An unaided production (an eliciting answer, a probe, a placement check)
    on the item, or on another question of its learning object, is not
    independent while the routine display is fresh, and is again once the
    cold retrieval delay has passed."""

    from learnloop.attempts.reveal_ledger import production_admissibility

    vault, repository = ctx.require_vault()
    _routine_display(ctx, display)
    learning_object_id = vault.practice_items[ITEM].learning_object_id
    item_id = ITEM if target == "item" else "pi_other_question"

    def admissible(clock) -> bool:
        return production_admissibility(
            repository, practice_item_id=item_id, learning_object_id=learning_object_id,
            produced_at=_iso(clock),
        ).admissible

    assert admissible(_later(hours=2)) is False
    assert admissible(_later(days=2)) is True


@pytest.mark.parametrize("kind", ["worked_answer", "tutor_answer"])
def test_f1_other_reveals_keep_their_window(ctx, kind):
    """Only the plain surface's routine displays lapse: the stuck answer's
    worked answer (stuck-prompt F8) and every other reveal kind count exactly
    as before, however long ago."""

    from learnloop.attempts.reveal_ledger import (
        production_admissibility,
        record_answer_display_reveal,
        record_reveal,
    )

    vault, repository = ctx.require_vault()
    attempt_id = _self_graded(ctx, points=0)
    learning_object_id = vault.practice_items[ITEM].learning_object_id
    if kind == "worked_answer":
        record_answer_display_reveal(
            repository, attempt_id=attempt_id, practice_item_id=ITEM,
            learning_object_id=learning_object_id, basis="worked_answer:stuck_empty:tui",
        )
    else:
        # A few seconds after the attempt: an unlinked kind's window starts
        # after the attempt's own second (stuck-prompt open question 5).
        record_reveal(
            repository, practice_item_id=ITEM, learning_object_id=learning_object_id,
            source_kind="tutor_answer", amount=1.0, basis="tutor_answer", clock=_later(seconds=5),
        )

    assert _next_attempt_primed(repository, clock=_later(days=5))
    assert production_admissibility(
        repository, practice_item_id=ITEM, learning_object_id=learning_object_id,
        produced_at=_iso(_later(days=5)),
    ).admissible is False


# == Codex re-review (docs/reviews/ux-phase4-feedback-codex-review.md §7) =====================


# -- F1 (reopened): each feedback visit that shows the full answer is an exposure ------------


def test_f1r_feedback_reopened_after_the_cold_delay_is_a_fresh_exposure(ctx):
    """The re-review's scenario: the answer's feedback first showed the full
    answer two days ago (that display has lapsed), then the learner reopens
    it and reads the full answer again. The reopened visit is a fresh
    exposure: a retry right after it is primed and an unaided production is
    not independent. A retry of the same visit's write records nothing new,
    and the expiry runs from the latest exposure."""

    from datetime import UTC, datetime

    from learnloop.attempts.reveal_ledger import production_admissibility, record_feedback_answer_display_reveal

    vault, repository = ctx.require_vault()
    learning_object_id = vault.practice_items[ITEM].learning_object_id
    then = FrozenClock(datetime.now(UTC) - timedelta(days=2))
    attempt_id = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=ITEM, learner_answer_md="my answer", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=3),
        clock=then,
    ).attempt_id
    record_feedback_answer_display_reveal(
        repository, attempt_id=attempt_id, practice_item_id=ITEM, learning_object_id=learning_object_id,
        display_id="visit_first", clock=then,
    )
    assert not _next_attempt_primed(repository)

    _call(ctx, "record_answer_display", {"attemptId": attempt_id, "displayId": "visit_reopened"})
    _call(ctx, "record_answer_display", {"attemptId": attempt_id, "displayId": "visit_reopened"})

    rows = _reveals(repository, source_kind="answer_display")
    assert [row["attempt_id"] for row in rows] == [attempt_id, attempt_id]
    assert _next_attempt_primed(repository)
    assert production_admissibility(
        repository, practice_item_id=ITEM, learning_object_id=learning_object_id,
        produced_at=_iso(_later(minutes=5)),
    ).admissible is False
    assert not _next_attempt_primed(repository, clock=_later(days=2))


def test_f1r_a_display_needs_its_visit(ctx):
    """The desktop names the visit; a write without one is refused rather than
    guessed at (a guess either drops a fresh exposure or doubles a retry)."""

    from pydantic import ValidationError

    attempt_id = _self_graded(ctx, points=0)
    with pytest.raises(ValidationError):
        _call(ctx, "record_answer_display", {"attemptId": attempt_id})
    with pytest.raises(ValidationError):
        _call(ctx, "record_answer_display", {"attemptId": attempt_id, "displayId": ""})


def test_f1r_a_display_that_lapses_never_stands_in_for_one_that_does_not(ctx):
    """Once-per-attempt writers dedupe by their own basis: a feedback visit's
    routine (lapsing) row on the attempt does not suppress the TUI's worked
    answer, which keeps its window however long ago (stuck-prompt F8)."""

    from learnloop.attempts.reveal_ledger import record_answer_display_reveal

    vault, repository = ctx.require_vault()
    attempt_id = _self_graded(ctx, points=0)
    _call(ctx, "record_answer_display", {"attemptId": attempt_id, "displayId": "visit_1"})
    for _reopen in range(2):
        record_answer_display_reveal(
            repository, attempt_id=attempt_id, practice_item_id=ITEM,
            learning_object_id=vault.practice_items[ITEM].learning_object_id,
            basis="worked_answer:stuck_empty:tui",
        )

    assert len(_reveals(repository, source_kind="answer_display")) == 2
    assert _next_attempt_primed(repository, clock=_later(days=5))


# -- F8: frozen criteria keep their ids --------------------------------------------------------


def _contract_answer(ctx, *, criteria=None, points=None, submission_id="sub_rr") -> str:
    """A self-graded answer submitted under its assessment contract (the
    canonical-state path F5 uses), the item's rubric replaced first when
    ``criteria`` is given."""

    from learnloop.vault.writer import upsert_practice_item

    paths = ctx.paths
    _set_canonical_state(paths)
    if criteria is not None:
        data = load_vault(paths.root).practice_items[ITEM].model_dump(mode="json")
        data["grading_rubric"]["criteria"] = criteria
        data["grading_rubric"]["max_points"] = int(sum(c["points"] for c in criteria))
        upsert_practice_item(paths.root, data)
    ctx.load(paths.root)
    detail = _call(ctx, "get_practice_item", {"practiceItemId": ITEM})
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    result = _call(ctx, "submit_attempt", {
        "sessionId": session_id, "practiceItemId": ITEM, "answerMd": "U Sigma V^T",
        "attemptType": "independent_attempt", "submissionId": submission_id,
        "assessmentContractVersionId": detail["assessmentContractVersionId"],
        "selfGrade": {"criterionPoints": points or {"correctness": 4}, "confidence": 3},
    })
    return result["attemptId"]


def test_f8_frozen_criteria_keep_their_original_ids_through_serialization(ctx):
    """An underscored criterion id (as existing fixtures use) survives the
    bundle's camel-case conversion: the frozen criteria are data rows carrying
    their id, so each evidence row finds its own."""

    criteria = [{"id": "criterion_correct_selection", "points": 4, "description": "Selects the SVD."}]
    attempt_id = _contract_answer(ctx, criteria=criteria, points={"criterion_correct_selection": 3})
    vault, repository = ctx.require_vault()

    bundle = feedback_bundle(vault, repository, attempt_id)

    assert bundle["answeredCriteria"] == [
        {"criterionId": "criterion_correct_selection", "description": "Selects the SVD.", "pointsPossible": 4.0}
    ]
    assert [row["criterionId"] for row in bundle["criterionEvidence"]] == ["criterion_correct_selection"]


# -- F9: a regrade's feedback shows what the regrade graded against ----------------------------


class _SixPointGrader(ReviewFakeClient):
    """A grader fake that awards six points on each criterion (at most its worth)."""

    def _grade_parts(self, context):
        parts = super()._grade_parts(context)
        parts["evidence"] = [
            {**row, "points_awarded": min(6.0, float(criterion["points"]))}
            for row, criterion in zip(parts["evidence"], parts["criteria"])
        ]
        parts["correct"] = False
        return parts


CORRECTED_KEY = "A = U Sigma V^T: U and V orthogonal, Sigma diagonal and non-negative."


def _correct_the_item(ctx, *, prompt=None) -> None:
    from learnloop.vault.writer import upsert_practice_item

    paths = ctx.paths
    data = load_vault(paths.root).practice_items[ITEM].model_dump(mode="json")
    if prompt is not None:
        data["prompt"] = prompt
    data["expected_answer"] = CORRECTED_KEY
    data["grading_rubric"]["max_points"] = 8
    data["grading_rubric"]["criteria"] = [{"id": "correctness", "points": 8, "description": "Names all three factors."}]
    upsert_practice_item(paths.root, data)
    ctx.load(paths.root)


@pytest.mark.parametrize("after", [timedelta(seconds=5), timedelta(0)], ids=["later", "same_second"])
def test_f9_a_regrade_outside_the_screen_is_the_current_grade_and_unrecorded(ctx, after):
    """An ordinary answer graded under its contract (4 points), the item then
    corrected (8 points) and regraded outside the feedback screen (the CLI,
    the deferred self-grade regrades). The regrade is the current grade, also
    when stamped in the original's own second (its rows carry no grading
    revision to order them by), and it cites no contract, so nothing recorded
    says what it read (round 3 F9): no key or criteria presented as graded,
    never the superseded 4-point ones, and the maximum only as the blind
    regrade recorded it. The question stays the one the learner was given."""

    from learnloop.clock import parse_utc

    attempt_id = _contract_answer(ctx, points={"correctness": 2})
    _correct_the_item(ctx, prompt="Define SVD for a 3x2 matrix.")
    vault, repository = ctx.require_vault()
    attempt = repository.fetch_practice_attempt(attempt_id)
    regrade_attempt(
        vault, repository, attempt, runtime=ReadyRuntime(), client=_SixPointGrader(), grading_source="ai",
        clock=FrozenClock(parse_utc(attempt["created_at"]) + after),
    )

    bundle = feedback_bundle(vault, repository, attempt_id)

    assert bundle["rubricScore"] == 6
    [row] = bundle["criterionEvidence"]
    assert row["pointsAwarded"] == 6.0
    assert bundle["answeredSource"] == "unrecorded"
    assert (bundle["answeredExpectedAnswer"], bundle["answeredCriteria"]) == (None, None)
    assert bundle["answeredMaxPoints"] == 8
    prompts = [b["markdown"] for b in bundle["answeredPresentation"]["blocks"] if b["kind"] == "prompt"]
    assert prompts == ["Define SVD."]


def test_f9_an_answer_not_regraded_keeps_the_key_and_maximum_it_was_graded_under(ctx):
    """The control: the same correction without a regrade leaves the answer's
    grade under its contract, so feedback shows the frozen key, criteria and
    maximum together (F5)."""

    attempt_id = _contract_answer(ctx, points={"correctness": 4})
    _correct_the_item(ctx)
    vault, repository = ctx.require_vault()

    bundle = feedback_bundle(vault, repository, attempt_id)

    assert bundle["answeredSource"] == "contract"
    assert bundle["answeredExpectedAnswer"] == "A matrix factorization into U, Sigma, and V transpose."
    assert bundle["answeredCriteria"] == [
        {"criterionId": "correctness", "description": "Correct definition.", "pointsPossible": 4.0}
    ]
    assert bundle["answeredMaxPoints"] == 4


# -- F10: a contest key is bound to its reason --------------------------------------------------


def _contest_reasons(repository) -> list[str]:
    import json

    reasons = []
    for event in _contest_events(repository):
        if event["event_type"] != "responded":
            continue
        payload = event["response_payload"]
        payload = json.loads(payload) if isinstance(payload, str) else payload
        reasons.append(payload["reason"])
    return reasons


def test_f10_a_contest_key_resent_with_an_edited_reason_is_refused_never_dropped(ctx):
    """The reason was recorded but its response was lost; the learner edits it
    and the same key is sent again. The sidecar refuses the mismatch (the
    client keeps the edited reason) instead of answering success over the
    original one; the edited reason under its own key is recorded."""

    _vault, repository = ctx.require_vault()
    attempt_id = _self_graded(ctx, points=0)
    _call(ctx, "trigger_regrade", {"attemptId": attempt_id, "learnerReason": "I did use the SVD", "contestId": "c10"})

    with pytest.raises(SidecarError) as raised:
        _call(ctx, "trigger_regrade", {
            "attemptId": attempt_id, "learnerReason": "Sigma is diagonal, as I wrote", "contestId": "c10",
        })
    assert raised.value.code == "contest_key_conflict"
    assert _contest_reasons(repository) == ["I did use the SVD"]

    # A retry of the same reason under the same key is still idempotent.
    _call(ctx, "trigger_regrade", {"attemptId": attempt_id, "learnerReason": " I did use the SVD ", "contestId": "c10"})
    _call(ctx, "trigger_regrade", {
        "attemptId": attempt_id, "learnerReason": "Sigma is diagonal, as I wrote", "contestId": "c11",
    })
    assert _contest_reasons(repository) == ["I did use the SVD", "Sigma is diagonal, as I wrote"]


# == Final verification reopen (docs/reviews/ux-phase4-feedback-codex-review.md §8) ============


# -- F1: an exposure is renewed while the feedback stays mounted -------------------------------
#
# The desktop renews the exposure whenever the full answer comes back on screen
# (the document visible again, the window refocused, an overlay over it closed),
# at least hourly while it stays on screen, and when it leaves the screen after
# more than a minute (``screens/feedback/answerExposure.ts``). Each renewal is a
# new display id; a retry of one renewal's write reuses its id. These tests replay
# the rows that schedule writes through the production readers.


def _feedback_answer(ctx, *, then: FrozenClock) -> str:
    vault, repository = ctx.require_vault()
    return complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=ITEM, learner_answer_md="my answer", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=3),
        clock=then,
    ).attempt_id


def _exposure(ctx, attempt_id: str, display_id: str, *, clock: FrozenClock) -> None:
    from learnloop.attempts.reveal_ledger import record_feedback_answer_display_reveal

    vault, repository = ctx.require_vault()
    record_feedback_answer_display_reveal(
        repository, attempt_id=attempt_id, practice_item_id=ITEM,
        learning_object_id=vault.practice_items[ITEM].learning_object_id,
        display_id=display_id, clock=clock,
    )


def _admissible_now(ctx, *, clock: FrozenClock | None = None) -> bool:
    from learnloop.attempts.reveal_ledger import production_admissibility

    vault, repository = ctx.require_vault()
    return production_admissibility(
        repository, practice_item_id=ITEM, learning_object_id=vault.practice_items[ITEM].learning_object_id,
        produced_at=_iso(clock or _later(minutes=1)),
    ).admissible


def test_f1f_feedback_returned_to_after_the_cold_delay_is_a_renewed_exposure(ctx):
    """The verifier's scenario: feedback showed the full answer, the app was
    backgrounded without unmounting it, two days passed, and the learner came
    back to the still-mounted screen and read the answer. Before the return the
    readers say clean (the reproduction); the return renews the exposure under a
    new display id, so the next attempt is primed and an unaided production is
    not independent. A retry of the return's write records nothing new."""

    _vault, repository = ctx.require_vault()
    two_days_ago = _later(days=-2)
    attempt_id = _feedback_answer(ctx, then=two_days_ago)
    _exposure(ctx, attempt_id, "display_mounted", clock=two_days_ago)
    assert not _next_attempt_primed(repository)
    assert _admissible_now(ctx)

    _call(ctx, "record_answer_display", {"attemptId": attempt_id, "displayId": "display_returned"})
    _call(ctx, "record_answer_display", {"attemptId": attempt_id, "displayId": "display_returned"})

    rows = _reveals(repository, source_kind="answer_display")
    assert [row["basis"].rsplit(":", 1)[-1] for row in rows] == ["display_mounted", "display_returned"]
    assert _next_attempt_primed(repository)
    assert not _admissible_now(ctx)


@pytest.mark.parametrize("renewed", [True, False], ids=["renewed_hourly", "mount_only"])
def test_f1f_a_full_answer_left_on_screen_past_the_cold_delay_stays_an_exposure(ctx, renewed):
    """Feedback mounted 50 hours ago and on screen since. With the hourly
    renewals the open screen writes, the next attempt is primed and an unaided
    production is not independent, until the coverage (the cold delay plus the
    renewal grace, round 3) has passed since the last renewal. With only the
    mount's row (the reopened finding), the exposure had silently expired."""

    _vault, repository = ctx.require_vault()
    mounted = _later(hours=-50)
    attempt_id = _feedback_answer(ctx, then=mounted)
    _exposure(ctx, attempt_id, "display_0", clock=mounted)
    if renewed:
        for hour in range(1, 50):
            _exposure(ctx, attempt_id, f"display_{hour}", clock=_later(hours=hour - 50))

    assert _next_attempt_primed(repository) is renewed
    assert _admissible_now(ctx) is (not renewed)
    if renewed:
        assert _next_attempt_primed(repository, clock=_later(hours=23))
        assert not _next_attempt_primed(repository, clock=_later(hours=25))


def test_f1f_a_retry_within_one_exposure_writes_once(ctx):
    """A write retried after a lost confirmation reuses its display id: one row,
    stamped when the exposure began."""

    _vault, repository = ctx.require_vault()
    attempt_id = _self_graded(ctx, points=0)
    for _retry in range(3):
        _call(ctx, "record_answer_display", {"attemptId": attempt_id, "displayId": "display_one"})
    assert len(_reveals(repository, source_kind="answer_display")) == 1


# -- F9: the key, criteria and maximum a grade stands on ----------------------------------------


LATER_KEY = "A = U Sigma V^T, with the singular values in Sigma in decreasing order."


def _ready_grader(monkeypatch, client) -> None:
    import learnloop_sidecar.handlers.ai_providers as providers

    monkeypatch.setattr(providers, "ready_grading_provider", lambda vault, override=None: ("fake", ReadyRuntime(), client))
    monkeypatch.setattr(providers, "grading_source_for_provider", lambda name: "ai")


def _change_the_item_again(ctx) -> None:
    from learnloop.vault.writer import upsert_practice_item

    paths = ctx.paths
    data = load_vault(paths.root).practice_items[ITEM].model_dump(mode="json")
    data["expected_answer"] = LATER_KEY
    data["grading_rubric"]["max_points"] = 10
    data["grading_rubric"]["criteria"] = [
        {"id": "correctness", "points": 10, "description": "Names all three factors and orders Sigma."}
    ]
    upsert_practice_item(paths.root, data)
    ctx.load(paths.root)


def _reopened_later(ctx, attempt_id: str) -> dict:
    """The feedback reopened a day later: the screen serves the item as it is
    then (which snapshots it, as every serve does), then reads the bundle."""

    from learnloop.learner.assessment_contracts import snapshot_for_presentation

    vault, repository = ctx.require_vault()
    snapshot_for_presentation(repository, vault, vault.practice_items[ITEM], clock=_later(days=1))
    return _call(ctx, "get_feedback", {"attemptId": attempt_id})


def _regraded_under_the_corrected_item(ctx, monkeypatch, how: str) -> tuple[str, dict]:
    """An answer graded under its 4-point contract, its feedback loaded, the
    item then corrected (8 points), then regraded from the feedback screen."""

    attempt_id = _contract_answer(ctx, points={"correctness": 2})
    _call(ctx, "get_feedback", {"attemptId": attempt_id})
    _correct_the_item(ctx)
    _ready_grader(monkeypatch, _SixPointGrader())
    params = {"attemptId": attempt_id}
    if how == "contest":
        params.update({"learnerReason": "All three factors are there", "contestId": "contest_f9"})
    return attempt_id, _call(ctx, "trigger_regrade", params)


@pytest.mark.parametrize("how", ["regrade", "contest"])
def test_f9f_a_regrade_in_place_returns_the_key_criteria_and_maximum_it_graded_against(ctx, monkeypatch, how):
    """The live reproduction: the regrade's response itself carries what that
    regrade read (the corrected item), source ``live``, so the screen never
    keeps the item it loaded with. The regrade history scores each side out of
    its own grade's maximum."""

    _attempt_id, bundle = _regraded_under_the_corrected_item(ctx, monkeypatch, how)

    assert bundle["rubricScore"] == 6
    assert bundle["answeredExpectedAnswer"] == CORRECTED_KEY
    assert bundle["answeredSource"] == "live"
    assert bundle["answeredCriteria"] == [
        {"criterionId": "correctness", "description": "Names all three factors.", "pointsPossible": 8.0}
    ]
    assert bundle["answeredMaxPoints"] == 8
    assert (bundle["regrade"]["oldMaxPoints"], bundle["regrade"]["newMaxPoints"]) == (4, 8)


@pytest.mark.parametrize("grading", ["blind", "joint"])
def test_f9f_a_question_changed_after_its_regrade_is_labelled_never_scored_out_of_the_later_maximum(
    ctx, monkeypatch, grading
):
    """The historical reproduction: regraded to 6 under the 8-point item, then
    the item changes again (10 points, another key) with no regrade. Nothing
    recorded gives the 8-point key back exactly (an ordinary regrade cites no
    contract), so the bundle says the question changed since it was graded and
    carries no key or criteria of the later item, and never its maximum. A
    blind regrade (this vault's default) recorded its maximum, 8, in its blind
    record; a joint one (the kill switch) recorded none."""

    if grading == "joint":
        from tests.split_live_helpers import append_config

        append_config(ctx.paths.root, "[diagnosis]\nsplit_enabled = false")
    attempt_id, _bundle = _regraded_under_the_corrected_item(ctx, monkeypatch, "regrade")
    _change_the_item_again(ctx)

    bundle = _reopened_later(ctx, attempt_id)

    recorded = 8 if grading == "blind" else None
    assert bundle["answeredSource"] == "unrecorded"
    assert bundle["answeredExpectedAnswer"] is None
    assert bundle["answeredCriteria"] is None
    assert bundle["answeredMaxPoints"] == recorded
    assert (bundle["rubricScore"], bundle["maxPoints"]) == (6, 10)
    assert (bundle["regrade"]["oldMaxPoints"], bundle["regrade"]["newMaxPoints"]) == (4, recorded)


def test_f9f_an_ordinary_regrade_reopened_later_is_unrecorded_even_unchanged(ctx, monkeypatch):
    """Regraded under the item as it was answered, reopened a day later with
    nothing changed. Nothing recorded proves the item now is what the regrade
    read (round 3 F9: content-addressed first-seen stamps do not establish
    which version was in force), so the bundle claims neither "unchanged" nor
    "changed": ``unrecorded``, with the maximum the blind regrade recorded."""

    attempt_id = _contract_answer(ctx, points={"correctness": 2})
    _ready_grader(monkeypatch, _SixPointGrader())
    live = _call(ctx, "trigger_regrade", {"attemptId": attempt_id})
    assert live["answeredSource"] == "live"

    bundle = _reopened_later(ctx, attempt_id)

    assert bundle["answeredSource"] == "unrecorded"
    assert (bundle["answeredExpectedAnswer"], bundle["answeredCriteria"]) == (None, None)
    assert bundle["answeredMaxPoints"] == 4
    assert (bundle["regrade"]["oldMaxPoints"], bundle["regrade"]["newMaxPoints"]) == (4, 4)


def test_f9f_a_blind_regrade_keeps_the_maximum_recorded_with_it_after_the_question_changed(tmp_path):
    """A split vault's regrade writes its maximum into its blind record. After
    the item's rubric doubles, the bundle says the question changed and scores
    the grade out of that recorded maximum, never the item's new one."""

    from learnloop.vault.writer import upsert_practice_item
    from tests.test_held_grade_evidence import _graded_apply

    paths, vault, repository = split_vault(tmp_path, version=VERSION)
    _graded_apply(vault, repository, SPLIT_ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_g", when=T)
    regrade_attempt(
        vault, repository, repository.fetch_practice_attempt("att_g"),
        runtime=ReadyRuntime(), client=FullCreditGrader(), grading_source="ai",
        clock=FrozenClock(T + timedelta(days=1)),
    )
    assert feedback_bundle(vault, repository, "att_g")["answeredMaxPoints"] == 4

    data = load_vault(paths.root).practice_items[SPLIT_ITEM].model_dump(mode="json")
    rubric = data["grading_rubric"]
    rubric["criteria"] = [{**criterion, "points": 2 * criterion["points"]} for criterion in rubric["criteria"]]
    rubric["max_points"] = 8
    upsert_practice_item(paths.root, data)
    vault = load_vault(paths.root)

    bundle = feedback_bundle(vault, repository, "att_g")

    assert bundle["answeredSource"] == "unrecorded"
    assert (bundle["rubricScore"], bundle["answeredMaxPoints"], bundle["maxPoints"]) == (4, 4, 8)


# == Round 3 (docs/reviews/ux-phase4-feedback-codex-review.md §9) ==============================


# -- F1: one invariant -------------------------------------------------------------------------
#
# For any attempt or admissibility read at T, if the full answer was on screen in
# any window at some moment in [T - D, T] (D = the routine display horizon), the
# ledger already holds a committed row the reader counts at T. It is the
# conjunction of two properties, each tested on its own side:
#
# * the readers (here): a committed routine display row stamped s counts at every
#   T in [s, s + D + G], whatever attempts came between (G = the renewal grace);
# * the screen (vitest, ``answerExposure.test.ts``): the full answer is on screen
#   at v only while a committed row stamped s <= v with v < s + G exists.
#
# Then for v in [T - D, T]: s <= v <= T and T <= v + D < s + G + D.


def _stamp(clock: FrozenClock):
    from learnloop.clock import parse_utc

    return parse_utc(_iso(clock))


def test_f1g_the_screen_and_the_ledger_share_one_exposure_contract():
    """The desktop's gate and the readers' coverage read the same numbers."""

    import json
    from pathlib import Path

    from learnloop.attempts.reveal_ledger import (
        ROUTINE_ANSWER_DISPLAY_COVERAGE,
        ROUTINE_ANSWER_DISPLAY_HORIZON,
        ROUTINE_DISPLAY_RENEWAL_GRACE,
    )

    contract_path = Path(__file__).resolve().parents[1] / "apps/learnloop-tauri/src/screens/feedback/exposureContract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    assert contract["horizonMs"] == ROUTINE_ANSWER_DISPLAY_HORIZON.total_seconds() * 1000
    assert contract["renewalGraceMs"] == ROUTINE_DISPLAY_RENEWAL_GRACE.total_seconds() * 1000
    assert ROUTINE_ANSWER_DISPLAY_COVERAGE == ROUTINE_ANSWER_DISPLAY_HORIZON + ROUTINE_DISPLAY_RENEWAL_GRACE
    # The screen hides the answer before a row's grace ends, renews well before.
    assert contract["showMarginMs"] > 0
    assert contract["renewAfterMs"] + contract["showMarginMs"] < contract["renewalGraceMs"]


def test_f1g_reading_until_a_crash_is_covered_until_the_delay_after_the_last_look(ctx):
    """The verifier's first reproduction: renewals through hour 50, reading
    until 50:59, then the app is killed (no closing row). At 74:30, 23 h 31 min
    after the last look, a retry is primed and an unaided production is not
    independent: the 50:00 row covers until 75:00."""

    _vault, repository = ctx.require_vault()
    start = _later(hours=-74, minutes=-30)
    attempt_id = _feedback_answer(ctx, then=start)
    for hour in range(0, 51):
        _exposure(ctx, attempt_id, f"display_{hour}", clock=FrozenClock(_stamp(start) + timedelta(hours=hour)))

    assert _next_attempt_primed(repository)
    assert not _admissible_now(ctx, clock=_later(seconds=1))


def test_f1g_a_short_visit_closed_without_a_closing_row_is_covered(ctx):
    """The second reproduction: feedback shown for 30 seconds and closed (no
    closing row), then an attempt 24 h 0 min 15 s after it opened."""

    _vault, repository = ctx.require_vault()
    opened = _later(hours=-24, seconds=-15)
    attempt_id = _feedback_answer(ctx, then=opened)
    _exposure(ctx, attempt_id, "display_short", clock=opened)

    assert _next_attempt_primed(repository)
    assert not _admissible_now(ctx, clock=_later(seconds=1))


def test_f1g_a_display_that_failed_to_persist_is_never_acknowledged(ctx, monkeypatch):
    """The false acknowledgement: the insert raises, so the RPC reports a
    retryable failure and nothing is recorded (both readers still clean, as
    they must be, since nothing was written). The retry under the same id
    records it once and says when; a further retry says it was already."""

    import sqlite3

    from learnloop.db.repositories import Repository

    _vault, repository = ctx.require_vault()
    attempt_id = _self_graded(ctx, points=0)
    real_insert = Repository.insert_reveal_event

    def failing(self, event, *, clock=None):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(Repository, "insert_reveal_event", failing)
    with pytest.raises(SidecarError) as raised:
        _call(ctx, "record_answer_display", {"attemptId": attempt_id, "displayId": "display_x"})
    assert raised.value.code == "display_not_recorded"
    assert raised.value.retryable is True
    assert _reveals(repository, source_kind="answer_display") == []

    monkeypatch.setattr(Repository, "insert_reveal_event", real_insert)
    first = _call(ctx, "record_answer_display", {"attemptId": attempt_id, "displayId": "display_x"})
    again = _call(ctx, "record_answer_display", {"attemptId": attempt_id, "displayId": "display_x"})

    [row] = _reveals(repository, source_kind="answer_display")
    assert (first["recorded"], first["alreadyRecorded"], first["recordedAt"]) == (True, False, row["created_at"])
    assert (again["recorded"], again["alreadyRecorded"], again["recordedAt"]) == (True, True, row["created_at"])
    assert _next_attempt_primed(repository)


def _shown_disclosure(ctx, session_id: str, *, submission_id: str, display_id: str = "display_sg") -> dict:
    """A plain self-grade froze its trace and is showing the key: the freeze,
    then the display row the screen writes before the key appears."""

    _draft(ctx, session_id, submission_id=submission_id)
    _disclose(ctx, session_id, submission_id=submission_id)
    return _call(ctx, "record_self_grade_disclosure", {
        "sessionId": session_id, "practiceItemId": ITEM, "submissionId": submission_id,
        "answerMd": "U Sigma V^T", "explanationMd": None, "displayId": display_id,
    })


def test_f1g_a_pending_self_grade_disclosure_is_an_exposure_for_every_other_production(ctx):
    """The third reproduction: the key is on screen and the draft still
    pending. Another window's attempt on the item is primed and an unaided
    production on its learning object is not independent; the frozen trace's
    own commit stays clean (it was written before the key was shown)."""

    _vault, repository = ctx.require_vault()
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    receipt = _shown_disclosure(ctx, session_id, submission_id="sub_pending")

    [row] = _reveals(repository, source_kind="answer_display")
    assert receipt["recordedAt"] == row["created_at"]
    assert _next_attempt_primed(repository, submission_id="sub_other_window")
    assert not _admissible_now(ctx, clock=_later(seconds=1))
    # The frozen trace commits clean, and stays admissible as its own production.
    result = _submit_self_graded(ctx, session_id, submission_id="sub_pending")
    committed = repository.fetch_practice_attempt(result["attemptId"])
    assert not committed["primed"]
    from learnloop.attempts.reveal_ledger import production_admissibility

    vault, _repository = ctx.require_vault()
    assert production_admissibility(
        repository, practice_item_id=ITEM, learning_object_id=vault.practice_items[ITEM].learning_object_id,
        produced_at=committed["created_at"], production_id=committed["id"],
    ).admissible
    # And it counts against the next attempt.
    assert _next_attempt_primed(repository, submission_id="sub_next")


def test_f1g_a_disclosure_display_needs_its_pending_draft(ctx):
    """A display write for a draft that is no longer pending (committed,
    abandoned, or never frozen) is refused: the screen then hides the key."""

    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    _draft(ctx, session_id, submission_id="sub_nf")
    with pytest.raises(SidecarError) as raised:
        _call(ctx, "record_self_grade_disclosure", {
            "sessionId": session_id, "practiceItemId": ITEM, "submissionId": "sub_nf",
            "answerMd": "U Sigma V^T", "explanationMd": None, "displayId": "display_nf",
        })
    assert raised.value.code == "disclosure_not_pending"


@pytest.mark.parametrize("seed", range(10))
def test_f1g_every_committed_display_row_counts_until_its_coverage_ends(ctx, seed):
    """The readers' half of the invariant, on random timelines: attempts on the
    item, feedback display rows written at random moments, and reads at random
    later moments (each read sees only what was written by then). A read at T
    is primed, and an unaided production at T is not independent, exactly when
    some row stamped s has s <= T <= s + D + G, whatever attempts came between,
    and with or without a window start (``since``) as placement passes."""

    import random

    from learnloop.attempts.reveal_ledger import ROUTINE_ANSWER_DISPLAY_COVERAGE, production_admissibility

    rng = random.Random(seed)
    vault, repository = ctx.require_vault()
    learning_object_id = vault.practice_items[ITEM].learning_object_id
    start = _stamp(_later(days=-6))
    moment = start
    stamps: list = []
    latest_attempt: str | None = None
    checked = 0
    for step in range(40):
        moment += timedelta(minutes=rng.choice([1, 7, 40, 90, 300, 900, 1300, 1450, 1500, 1600]))
        clock = FrozenClock(moment)
        if moment >= _stamp(_later(minutes=-1)):
            break
        kind = rng.random()
        if kind < 0.25 or latest_attempt is None:
            latest_attempt = complete_self_graded_attempt(
                vault, repository,
                AttemptDraft(practice_item_id=ITEM, learner_answer_md=f"answer {step}", attempt_type="independent_attempt"),
                SelfGradeInput(criterion_points={"correctness": 0}, confidence=3), clock=clock,
            ).attempt_id
        elif kind < 0.55:
            _exposure(ctx, latest_attempt, f"display_{seed}_{step}", clock=clock)
            stamps.append(_stamp(clock))
        else:
            boundary = min(
                [abs((moment - (stamp + ROUTINE_ANSWER_DISPLAY_COVERAGE)).total_seconds()) for stamp in stamps] or [9e9]
            )
            if boundary < 5:
                continue
            covered = any(stamp <= moment <= stamp + ROUTINE_ANSWER_DISPLAY_COVERAGE for stamp in stamps)
            assert _next_attempt_primed(repository, submission_id=f"probe_{seed}_{step}", clock=clock) is covered
            since = _iso(FrozenClock(moment - timedelta(minutes=rng.choice([5, 120, 2000]))))
            for window in (None, since):
                assert production_admissibility(
                    repository, practice_item_id=ITEM, learning_object_id=learning_object_id,
                    produced_at=_iso(clock), since=window,
                ).admissible is (not covered)
            checked += 1
    assert checked > 0


# -- F9: no inference about which version a grade read ----------------------------------------


def _set_item_key(ctx, key: str) -> None:
    from learnloop.vault.writer import upsert_practice_item

    data = load_vault(ctx.paths.root).practice_items[ITEM].model_dump(mode="json")
    data["expected_answer"] = key
    upsert_practice_item(ctx.paths.root, data)
    ctx.load(ctx.paths.root)


def test_f9g_the_a_b_a_b_sequence_never_presents_a_version_as_graded_without_a_record(ctx, monkeypatch):
    """The verifier's reproduction with the production snapshot writer:
    key A is served (snapshotted), then key B; A is restored and the answer
    regraded against A (A's snapshot keeps its first-seen stamp); then B is
    restored without a regrade. The regrade's own response is ``live`` with
    A's key, what it read; every later bundle is ``unrecorded``, so neither
    "changed" right after grading unchanged A nor B presented as graded."""

    key_a = "A matrix factorization into U, Sigma, and V transpose."
    key_b = "A = U Sigma V^T with U, V orthogonal."
    attempt_id = _contract_answer(ctx, points={"correctness": 2})  # serves A
    _set_item_key(ctx, key_b)
    _call(ctx, "get_practice_item", {"practiceItemId": ITEM})  # serves B
    _set_item_key(ctx, key_a)
    _ready_grader(monkeypatch, _SixPointGrader())

    live = _call(ctx, "trigger_regrade", {"attemptId": attempt_id})
    assert (live["answeredSource"], live["answeredExpectedAnswer"]) == ("live", key_a)
    assert _call(ctx, "get_feedback", {"attemptId": attempt_id})["answeredSource"] == "unrecorded"

    _set_item_key(ctx, key_b)
    later = _reopened_later(ctx, attempt_id)
    assert later["answeredSource"] == "unrecorded"
    assert later["answeredExpectedAnswer"] is None


def test_f9g_a_contract_cited_epoch_stays_exact_whatever_was_served_since(ctx):
    """An answer graded under its contract keeps its contract's key, criteria
    and maximum (``contract``) after other versions were served."""

    attempt_id = _contract_answer(ctx, points={"correctness": 3})
    _correct_the_item(ctx)
    _call(ctx, "get_practice_item", {"practiceItemId": ITEM})
    vault, repository = ctx.require_vault()

    bundle = feedback_bundle(vault, repository, attempt_id)

    assert bundle["answeredSource"] == "contract"
    assert bundle["answeredExpectedAnswer"] == "A matrix factorization into U, Sigma, and V transpose."
    assert bundle["answeredMaxPoints"] == 4


# == Round 4 (docs/reviews/ux-phase4-feedback-codex-review.md §10) ==============================


# -- F1-2: the frozen trace's exemption matches exact identity ----------------------------------


def test_f1i_a_changed_trace_under_the_frozen_key_is_primed_once_the_checkpoint_moved_on(ctx):
    """The verifier's (a): the key was shown for draft ``sub_a``, the checkpoint
    then moved to another item (settling the disclosure as abandoned), and a
    CHANGED trace is sent under ``sub_a``. Nothing in the checkpoint compares
    it any more, so the exemption itself must: it covers only rows naming the
    hash of the trace that was frozen, which this trace does not have."""

    from tests.helpers import add_followup_item

    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    _shown_disclosure(ctx, session_id, submission_id="sub_a")
    add_followup_item(ctx.paths.root)
    ctx.load(ctx.paths.root)
    _draft(ctx, session_id, submission_id="sub_b", item="pi_svd_define_002")
    _vault, repository = ctx.require_vault()

    result = _submit_self_graded(ctx, session_id, submission_id="sub_a", answer="Rewritten with the key in view")

    assert repository.fetch_practice_attempt(result["attemptId"])["primed"]


def test_f1i_the_unchanged_frozen_trace_stays_exempt_after_the_checkpoint_moved_on(ctx):
    """The control: the frozen trace itself, sent under its key after the
    checkpoint moved on, was written before the key was shown: clean."""

    from tests.helpers import add_followup_item

    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    _shown_disclosure(ctx, session_id, submission_id="sub_a")
    add_followup_item(ctx.paths.root)
    ctx.load(ctx.paths.root)
    _draft(ctx, session_id, submission_id="sub_b", item="pi_svd_define_002")
    _vault, repository = ctx.require_vault()

    result = _submit_self_graded(ctx, session_id, submission_id="sub_a")

    assert not repository.fetch_practice_attempt(result["attemptId"])["primed"]


def test_f1i_only_the_commit_itself_is_exempt_never_another_response_in_its_second(ctx):
    """The verifier's (b): after the clean frozen commit, a DIFFERENT response
    on the item assessed in the same second is not independent; the commit,
    named by its attempt id, is."""

    from learnloop.attempts.reveal_ledger import production_admissibility

    vault, repository = ctx.require_vault()
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    _shown_disclosure(ctx, session_id, submission_id="sub_p")
    committed = repository.fetch_practice_attempt(
        _submit_self_graded(ctx, session_id, submission_id="sub_p")["attemptId"]
    )
    learning_object_id = vault.practice_items[ITEM].learning_object_id

    another = production_admissibility(
        repository, practice_item_id=ITEM, learning_object_id=learning_object_id,
        produced_at=committed["created_at"],
    )
    assert another.admissible is False

    itself = production_admissibility(
        repository, practice_item_id=ITEM, learning_object_id=learning_object_id,
        produced_at=committed["created_at"], production_id=committed["id"],
    )
    assert itself.admissible is True


# -- F1-3: a row stamped ahead of the clock is never invisible ----------------------------------


def test_f1i_a_display_stamped_ahead_of_the_clock_still_covers(ctx):
    """The verifier's clock rollback: a row was written, then the wall clock
    went back two minutes. A production now is still not independent (the
    row is stamped after it, but no later than... the clock that wrote it)."""

    from learnloop.attempts.reveal_ledger import production_admissibility

    vault, repository = ctx.require_vault()
    attempt_id = _self_graded(ctx, points=0)
    _exposure(ctx, attempt_id, "display_ahead", clock=_later(minutes=2))

    assert _next_attempt_primed(repository)
    assert production_admissibility(
        repository, practice_item_id=ITEM, learning_object_id=vault.practice_items[ITEM].learning_object_id,
        produced_at=_iso(_later(seconds=1)),
    ).admissible is False


def test_f1i_a_display_after_a_production_does_not_count_against_it(ctx):
    """The control: a past production judged later is not contaminated by a
    display written after it (its own feedback's, say) once the clock has
    passed that display's stamp."""

    from learnloop.attempts.reveal_ledger import production_admissibility

    vault, repository = ctx.require_vault()
    attempt_id = _feedback_answer(ctx, then=_later(hours=-2))
    _exposure(ctx, attempt_id, "display_after", clock=_later(hours=-1))

    assert production_admissibility(
        repository, practice_item_id=ITEM, learning_object_id=vault.practice_items[ITEM].learning_object_id,
        produced_at=_iso(_later(hours=-2)),
    ).admissible is True


# -- NEW: serving agrees with submit on routine displays ----------------------------------------


@pytest.mark.parametrize("seed", range(6))
def test_f1i_the_scheduler_never_serves_a_cold_retry_that_submit_would_refuse(tmp_path, seed):
    """A property over display and cold-task timings: routine display rows on
    the cold item at random moments around the cold task's creation, and the
    queue built at random later moments. Whenever the cold lane serves the
    task, a submission at that moment is not primed, so it is not refused
    ("a cold retry must be unassisted and unprimed"). One coverage, D + G,
    for both."""

    import random

    from learnloop.attempts.attempts import auto_primed_draft
    from tests.test_remediation_cold_retry import NOW, _cold_lane_ids, _drive_to_cold_scheduled, _setup

    rng = random.Random(seed)
    vault, repository, misconception_id = _setup(tmp_path)
    _episode, _primed, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    displays = [NOW + timedelta(minutes=rng.randint(-600, 3000)) for _ in range(rng.randint(1, 4))]
    events = [("display", moment) for moment in displays]
    events += [("serve", NOW + timedelta(minutes=rng.randint(1440, 4400))) for _ in range(8)]
    # And inside each display's last hour of coverage, where serve and submit
    # disagreed (the cold delay is D, the coverage D + G).
    events += [("serve", moment + timedelta(days=1, minutes=rng.randint(1, 59))) for moment in displays]
    for index, (kind, moment) in enumerate(sorted(events, key=lambda event: event[1])):
        clock = FrozenClock(moment)
        if kind == "display":
            repository.insert_reveal_event(
                {
                    "practice_item_id": cold_item, "learning_object_id": "lo_svd_definition",
                    "source_kind": "answer_display", "amount": 1.0,
                    "basis": f"feedback_full_answer:desktop:display_{seed}_{index}",
                },
                clock=clock,
            )
            continue
        if cold_item in _cold_lane_ids(vault, repository, clock):
            draft, _total = auto_primed_draft(
                repository, AttemptDraft(practice_item_id=cold_item, learner_answer_md="U Sigma V^T"), clock=clock,
            )
            assert not draft.primed, f"served at {moment} but submit would be primed"


def test_f1i_an_independent_check_is_not_offered_inside_a_display_s_coverage(ctx):
    """Another server-side eligibility read: a full answer shown 24 h 30 min ago
    still covers the item (D + G), so it is not offered as an independent
    check, as submit would not count it as one."""

    from learnloop.instructional.exposure import independent_check_eligibility

    vault, repository = ctx.require_vault()
    attempt_id = _feedback_answer(ctx, then=_later(days=-3))
    _exposure(ctx, attempt_id, "display_old", clock=_later(hours=-24, minutes=-30))

    verdict = independent_check_eligibility(
        vault, repository, {"practice_item_id": ITEM}, intent="retention", at=_stamp(_later()),
    )

    assert "revealed" in verdict["reasons"]


# == Round 5 (docs/reviews/ux-phase4-feedback-codex-review.md §11) ==============================


# -- F1-2: the disclosure's identity is structured, compared field by field ---------------------


def _shown_disclosure_of(ctx, session_id: str, *, submission_id: str, answer: str, display_id: str = "display_sg") -> None:
    _draft(ctx, session_id, submission_id=submission_id, answer=answer)
    _disclose(ctx, session_id, submission_id=submission_id, answer=answer)
    _call(ctx, "record_self_grade_disclosure", {
        "sessionId": session_id, "practiceItemId": ITEM, "submissionId": submission_id,
        "answerMd": answer, "explanationMd": None, "displayId": display_id,
    })


def _move_checkpoint_on(ctx, session_id: str) -> None:
    from tests.helpers import add_followup_item

    add_followup_item(ctx.paths.root)
    ctx.load(ctx.paths.root)
    _draft(ctx, session_id, submission_id="sub_elsewhere", item="pi_svd_define_002")


def _committed(ctx, session_id: str, *, submission_id: str, answer: str) -> dict:
    _vault, repository = ctx.require_vault()
    result = _submit_self_graded(ctx, session_id, submission_id=submission_id, answer=answer)
    return repository.fetch_practice_attempt(result["attemptId"])


def _admissible_as_itself(ctx, attempt: dict) -> bool:
    from learnloop.attempts.reveal_ledger import production_admissibility

    vault, repository = ctx.require_vault()
    return production_admissibility(
        repository, practice_item_id=ITEM, learning_object_id=vault.practice_items[ITEM].learning_object_id,
        produced_at=attempt["created_at"], production_id=attempt["id"],
    ).admissible


def test_f1j_a_key_that_ends_in_a_trace_hash_never_exempts_another_draft(ctx):
    """The verifier's collision: with H the hash of trace T, a DIFFERENT trace
    Q is frozen and shown under the key "k:H", then T is submitted under the
    key "k". Prefix matching read the Q rows as T's own; the structured
    identity (key "k:H", trace hash(Q)) is not T's (key "k", trace H)."""

    from learnloop.attempts.reveal_ledger import trace_hash
    from learnloop.attempts.trace_evidence import compose_learner_trace

    answer_t = "U Sigma V^T"
    hash_t = trace_hash(compose_learner_trace(answer_t, None))
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    _shown_disclosure_of(ctx, session_id, submission_id=f"k:{hash_t}", answer="A different trace, Q")
    _move_checkpoint_on(ctx, session_id)

    attempt = _committed(ctx, session_id, submission_id="k", answer=answer_t)

    assert attempt["primed"]
    assert _admissible_as_itself(ctx, attempt) is False


def test_f1j_a_legacy_row_whose_display_id_is_the_hash_gets_no_exemption(ctx):
    """An unversioned row (the round-3 shape, ``self_grade_disclosure:<key>:
    <display id>``) whose display id happens to equal the trace's hash is not a
    hashed row: legacy and unversioned rows get no exemption."""

    from learnloop.attempts.reveal_ledger import trace_hash
    from learnloop.attempts.trace_evidence import compose_learner_trace

    vault, repository = ctx.require_vault()
    answer_t = "U Sigma V^T"
    hash_t = trace_hash(compose_learner_trace(answer_t, None))
    repository.insert_reveal_event({
        "practice_item_id": ITEM, "learning_object_id": vault.practice_items[ITEM].learning_object_id,
        "source_kind": "answer_display", "amount": 1.0, "basis": f"self_grade_disclosure:k:{hash_t}",
    })
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]

    attempt = _committed(ctx, session_id, submission_id="k", answer=answer_t)

    assert attempt["primed"]
    assert _admissible_as_itself(ctx, attempt) is False


@pytest.mark.parametrize("key", ["a:b", 'a|b"c', "a:{b}:c", "self_grade_disclosure:x:y", "k:"])
def test_f1j_keys_with_separators_keep_exactly_their_own_exemption(ctx, key):
    """Keys may contain colons and other separators: the frozen trace committed
    under its own key stays clean and admissible as itself; the same trace
    under a key that is a prefix of it is primed and not independent."""

    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    _shown_disclosure_of(ctx, session_id, submission_id=key, answer="U Sigma V^T")

    own = _committed(ctx, session_id, submission_id=key, answer="U Sigma V^T")
    assert not own["primed"]
    assert _admissible_as_itself(ctx, own) is True

    prefix = _committed(ctx, session_id, submission_id=key[:-1] or "k0", answer="U Sigma V^T")
    assert prefix["primed"]
    assert _admissible_as_itself(ctx, prefix) is False


@pytest.mark.parametrize("variant", ["whitespace", "another_key", "no_hash"])
def test_f1j_the_confirmed_controls_still_get_no_exemption(ctx, variant):
    """The controls the verifier confirmed: a whitespace-changed answer primes;
    distinct keys sharing a trace stay separate; a row without a hash exempts
    nothing."""

    vault, repository = ctx.require_vault()
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    if variant == "no_hash":
        repository.insert_reveal_event({
            "practice_item_id": ITEM, "learning_object_id": vault.practice_items[ITEM].learning_object_id,
            "source_kind": "answer_display", "amount": 1.0, "basis": "self_grade_disclosure:k",
        })
        attempt = _committed(ctx, session_id, submission_id="k", answer="U Sigma V^T")
    else:
        _shown_disclosure_of(ctx, session_id, submission_id="k", answer="U Sigma V^T")
        _move_checkpoint_on(ctx, session_id)
        if variant == "whitespace":
            attempt = _committed(ctx, session_id, submission_id="k", answer="U Sigma V^T ")
        else:
            attempt = _committed(ctx, session_id, submission_id="k2", answer="U Sigma V^T")

    assert attempt["primed"]
    assert _admissible_as_itself(ctx, attempt) is False


# -- Boundary: one endpoint convention, the exact second, every reader ---------------------------


def _boundary_reads(ctx, moment) -> dict[str, bool]:
    """Every reader's verdict at ``moment``: True when it holds the item back."""

    from contextlib import closing

    from learnloop.attempts.reveal_ledger import production_admissibility
    from learnloop.db.connection import connect
    from learnloop.db.stores.source_service import serve_time_exposure
    from learnloop.diagnosis.remediation import COLD_RETRIEVAL_DELAY
    from learnloop.instructional.exposure import independent_check_eligibility
    from learnloop.practice_index.retrieval import PracticeConstraints, filter_context
    from learnloop.scheduling.scheduler import _cold_task_reveals
    from learnloop.scheduling.serving_exclusions import out_of_timing_serving_exclusions

    vault, repository = ctx.require_vault()
    clock = FrozenClock(moment)
    at = _iso(clock)
    lo = vault.practice_items[ITEM].learning_object_id
    since = _iso(FrozenClock(moment - COLD_RETRIEVAL_DELAY))
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        serve_time = "revealed" in serve_time_exposure(
            connection, practice_item_id=ITEM, family_item_ids=(), extraction_id=None, span_ids=(), since=since,
        )["reasons"]
    return {
        "auto_prime": _next_attempt_primed(repository, submission_id="boundary", clock=clock),
        "admissibility": not production_admissibility(
            repository, practice_item_id=ITEM, learning_object_id=lo, produced_at=at, clock=clock,
        ).admissible,
        "cold_deferral": bool(_cold_task_reveals(
            repository, item_id=ITEM, learning_object_id=lo, since="", now_iso=at,
        )),
        "serving_exclusions": ITEM in out_of_timing_serving_exclusions(
            vault, repository, cold_followup_kinds=(), reveal_window=COLD_RETRIEVAL_DELAY, clock=clock,
        ).revealed_recently_item_ids,
        "independent_check": "revealed" in independent_check_eligibility(
            vault, repository, {"practice_item_id": ITEM}, intent="retention", at=moment,
        )["reasons"],
        "serve_time_exposure": serve_time,
        "practice_index": ITEM in filter_context(
            vault, repository, PracticeConstraints(exclude_revealed_families=True), clock=clock,
        ).revealed_items,
    }


def test_f1j_every_reader_agrees_at_the_exact_boundary_second(ctx):
    """A routine display stamped s covers every T with s <= T <= s + D + G
    (``reveal_coverage``, inclusive). At exactly s + 25 h every reader holds the
    item back; one second later every reader lets it go."""

    from learnloop.reveal_coverage import ROUTINE_DISPLAY_COVERAGE

    vault, repository = ctx.require_vault()
    attempt_id = _feedback_answer(ctx, then=_later(days=-3))
    stamp = _stamp(_later(hours=-26))
    _exposure(ctx, attempt_id, "display_boundary", clock=FrozenClock(stamp))

    at_end = _boundary_reads(ctx, stamp + ROUTINE_DISPLAY_COVERAGE)
    after = _boundary_reads(ctx, stamp + ROUTINE_DISPLAY_COVERAGE + timedelta(seconds=1))

    assert at_end == {name: True for name in at_end}, at_end
    assert after == {name: False for name in after}, after


# -- Cold checks: every serve path revalidates against the one coverage ------------------------


def _plan_with_a_cold_check(tmp_path, name: str):
    """A daily plan whose pool holds a due cold retry on ``pi_cold`` (a real
    open task) beside ordinary reviews, at 10:00."""

    from datetime import UTC, datetime

    from tests.daily_plan_fakes import MovableClock, make_env, scheduled, seed_due
    from tests.helpers import create_daily_plan_vault

    start = datetime(2026, 10, 12, 10, 0, tzinfo=UTC)
    paths = create_daily_plan_vault(
        tmp_path / name, learning_objects={"lo_c": [("pi_cold", 1.0)], "lo_a": [("pi_a", 1.0), ("pi_b", 1.0)]},
    )
    items = [
        scheduled("pi_cold", "lo_c", priority=0.9, followup_kind="cold_retry"),
        scheduled("pi_a", "lo_a", forgetting_risk=0.5),
        scheduled("pi_b", "lo_a", forgetting_risk=0.5),
    ]
    clock = MovableClock(start)
    env = make_env(paths.root, items, clock=clock, session_id="s_cold")
    for item_id in ("pi_a", "pi_b", "pi_cold"):
        seed_due(env.repository, item_id, due=start - timedelta(days=2), last=start - timedelta(days=9))
    env.repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref="ep_cold",
        not_before=_iso(FrozenClock(start - timedelta(hours=1))),
        expires_at=_iso(FrozenClock(start + timedelta(days=30))),
        selected_item_id="pi_cold", clock=FrozenClock(start - timedelta(days=1)),
    )
    return env, clock


def _served_items(env) -> list[str]:
    import json

    with env.repository.connection() as connection:
        rows = connection.execute(
            "SELECT detail_json FROM attention_block_events WHERE kind = 'item_served' ORDER BY created_at, event_ordinal"
        ).fetchall()
    return [json.loads(row[0])["practice_item_id"] for row in rows]


def _would_be_primed(env, item_id: str, clock) -> bool:
    from learnloop.attempts.attempts import auto_primed_draft

    draft, _total = auto_primed_draft(
        env.repository, AttemptDraft(practice_item_id=item_id, learner_answer_md="an answer"),
        clock=FrozenClock(clock.instant),
    )
    return draft.primed


def _display_on(env, item_id: str, clock, display_id: str) -> None:
    env.repository.insert_reveal_event(
        {"practice_item_id": item_id, "learning_object_id": "lo_c", "source_kind": "answer_display",
         "amount": 1.0, "basis": f"feedback_full_answer:desktop:{display_id}"},
        clock=FrozenClock(clock.instant),
    )


def test_f1j_a_planned_cold_check_revealed_before_it_is_served_is_not_served(tmp_path):
    """The verifier's scenario: the cold item is planned at 10:00, its answer
    is shown in another window at 10:01, and the plan advances at 10:05. The
    plan must not serve it (submit would prime it, and refuse it as a cold
    retry); the control plan, with no display, serves it."""

    from learnloop.daily_plan.engine import advance, get_or_create_today

    control, control_clock = _plan_with_a_cold_check(tmp_path, "control")
    get_or_create_today(control)
    control_clock.advance(5)
    advance(control, serve=True)
    assert "pi_cold" in _served_items(control)

    env, clock = _plan_with_a_cold_check(tmp_path, "revealed")
    get_or_create_today(env)
    clock.advance(1)
    _display_on(env, "pi_cold", clock, "display_other_window")
    clock.advance(4)
    assert _would_be_primed(env, "pi_cold", clock)
    for _step in range(3):
        advance(env, serve=True)

    assert "pi_cold" not in _served_items(env)


@pytest.mark.parametrize("seed", range(5))
def test_f1j_no_serve_path_serves_a_cold_check_submit_would_prime(tmp_path, seed):
    """A property over display timings and serve moments: displays of the cold
    item's answer at random moments, and the plan advanced or the queue built
    at random moments. Whenever a path serves the cold check (the plan emits
    item_served for it, the queue serves the cold lane), a submission at that
    moment is not primed."""

    import random

    from learnloop.daily_plan.engine import advance, get_or_create_today
    from learnloop.scheduling.scheduler import build_due_queue

    rng = random.Random(seed)
    env, clock = _plan_with_a_cold_check(tmp_path, f"property_{seed}")
    get_or_create_today(env)
    for step_index in range(12):
        clock.advance(rng.choice([1, 3, 20, 200, 1500]))
        if rng.random() < 0.5:
            _display_on(env, "pi_cold", clock, f"display_{seed}_{step_index}")
            clock.advance(rng.choice([0.5, 2, 30]))
        primed_now = _would_be_primed(env, "pi_cold", clock)
        if rng.random() < 0.6:
            served_before = len(_served_items(env))
            advance(env, serve=True)
            served = _served_items(env)
            if len(served) > served_before and served[-1] == "pi_cold":
                assert not primed_now, f"the plan served the cold check primed at {clock.instant}"
        else:
            cold_lane = [
                item.practice_item_id
                for item in build_due_queue(env.vault, env.repository, clock=FrozenClock(clock.instant))
                if item.followup_kind == "cold_retry"
            ]
            if "pi_cold" in cold_lane:
                assert not primed_now, f"the queue served the cold check primed at {clock.instant}"


def test_f1j_opening_a_revealed_cold_check_defers_it_instead_of_administering_it(ctx):
    """The direct open (``get_practice_item``: a stale list, a restored
    session, a deep link) revalidates too: a due cold retry whose answer was
    just shown is deferred at the open, so no cold administration is recorded
    and the answer is an ordinary one, never refused."""

    vault, repository = ctx.require_vault()
    # The earlier answer whose feedback showed the key (before the task: an
    # answer on the item would consume it).
    _exposure(ctx, _feedback_answer(ctx, then=_later(days=-2)), "display_open", clock=_later(minutes=-1))
    task = repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref="ep_open",
        not_before=_iso(_later(hours=-1)), expires_at=_iso(_later(days=30)), selected_item_id=ITEM,
        clock=_later(days=-1),
    )
    assert repository.active_followup_task_for_item(ITEM, kind="cold_retry") is not None

    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    _call(ctx, "get_practice_item", {"practiceItemId": ITEM, "sessionId": session_id})

    assert repository.active_followup_task_for_item(ITEM, kind="cold_retry") is None
    assert repository.followup_task(task["id"])["not_before"] > _iso(_later())


# == Round 6 (docs/reviews/ux-phase4-feedback-codex-review.md §12) ==============================


# -- B: a duplicated or mistyped identity field exempts nothing ----------------------------------


@pytest.mark.parametrize(
    "identity",
    [
        '{{"display":null,"submission":"other","submission":"k","trace":"{h}","v":2}}',
        '{{"display":null,"submission":"k","trace":"x","trace":"{h}","v":2}}',
        '{{"display":null,"submission":"k","trace":"{h}","v":2.0}}',
        '{{"display":null,"submission":"k","trace":"{h}","v":true}}',
    ],
    ids=["duplicate_submission", "duplicate_trace", "float_version", "bool_version"],
)
def test_f1k_a_malformed_identity_exempts_nothing(ctx, identity):
    """Duplicate keys (json.loads would keep the last) and a version that is
    not the integer 2 make a row malformed: it counts like any routine
    display and exempts nothing."""

    from learnloop.attempts.reveal_ledger import trace_hash
    from learnloop.attempts.trace_evidence import compose_learner_trace

    vault, repository = ctx.require_vault()
    hash_t = trace_hash(compose_learner_trace("U Sigma V^T", None))
    repository.insert_reveal_event({
        "practice_item_id": ITEM, "learning_object_id": vault.practice_items[ITEM].learning_object_id,
        "source_kind": "answer_display", "amount": 1.0,
        "basis": "self_grade_disclosure:v2:" + identity.format(h=hash_t),
    })
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]

    attempt = _committed(ctx, session_id, submission_id="k", answer="U Sigma V^T")

    assert attempt["primed"]
    assert _admissible_as_itself(ctx, attempt) is False


# -- C: a read-only detail never opens a cold administration ------------------------------------


def _administration_receipts(repository) -> int:
    with repository.connection() as connection:
        return int(connection.execute(
            "SELECT COUNT(*) FROM coldness_receipts WHERE stage = 'administration'"
        ).fetchone()[0])


def _due_cold_task(ctx, *, case_ref: str = "ep_detail") -> dict:
    _vault, repository = ctx.require_vault()
    return repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref=case_ref,
        not_before=_iso(_later(hours=-1)), expires_at=_iso(_later(days=30)), selected_item_id=ITEM,
        clock=_later(days=-1),
    )


def test_f1k_a_read_only_detail_never_opens_a_cold_administration(ctx):
    """Feedback and the inspector read an item's detail without a session: no
    cold administration is opened and no receipt written, whatever the item's
    cold task. Only a session serve, behind the guard, opens one."""

    _vault, repository = ctx.require_vault()
    _due_cold_task(ctx)

    _call(ctx, "get_practice_item", {"practiceItemId": ITEM})
    assert _administration_receipts(repository) == 0

    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    _call(ctx, "get_practice_item", {"practiceItemId": ITEM, "sessionId": session_id})
    assert _administration_receipts(repository) == 1


def test_f1k_a_session_serve_inside_routine_coverage_opens_no_administration(ctx):
    """The verifier's case at a real serve: a due cold retry and a recent
    full-answer display. The guard defers it; no administration is opened."""

    _vault, repository = ctx.require_vault()
    _exposure(ctx, _feedback_answer(ctx, then=_later(days=-2)), "display_detail", clock=_later(minutes=-1))
    _due_cold_task(ctx)
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]

    _call(ctx, "get_practice_item", {"practiceItemId": ITEM, "sessionId": session_id})

    assert _administration_receipts(repository) == 0
    assert repository.active_followup_task_for_item(ITEM, kind="cold_retry") is None


# -- D: no probe is committed for an item inside routine-display coverage ----------------------


@pytest.mark.parametrize("covered", [False, True], ids=["control", "covered"])
def test_f1k_no_probe_is_committed_for_an_item_inside_routine_display_coverage(tmp_path, covered):
    """The shared commit (``probe_episodes.commit_presentation``, every probe and
    placement presentation) refuses an item inside routine-display coverage: a
    self-grade disclosure of it was shown an hour ago and abandoned (so it is
    still never attempted, a probe candidate)."""

    from learnloop.diagnosis.probe_episodes import commit_item_presentation, enter_episode, episode_hypothesis_set
    from tests.test_probe_orchestration_remainder import CLOCK, ITEM_ID, LO_ID, _setup

    _root, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    if covered:
        repository.insert_reveal_event(
            {"practice_item_id": ITEM_ID, "learning_object_id": LO_ID, "source_kind": "answer_display",
             "amount": 1.0, "basis": "self_grade_disclosure:v2:" + '{"display":"d","submission":"s","trace":"t","v":2}'},
            clock=FrozenClock(CLOCK.now() - timedelta(hours=1)),
        )

    presentation = commit_item_presentation(
        loaded, repository, episode, loaded.practice_items[ITEM_ID], episode_hypothesis_set(repository, episode),
        clock=CLOCK,
    )

    assert (presentation is None) is covered


# -- E: a future task never masks a due one -------------------------------------------------------


@pytest.mark.parametrize("displayed", [False, True], ids=["no_display", "displayed"])
def test_f1k_a_future_task_never_masks_a_due_one(ctx, displayed):
    """Two cold tasks on the item, one due and one for later: the due one is
    judged first. With no routine display it is served; with one, it is held
    (and deferred)."""

    from learnloop.scheduling.scheduler import cold_check_serve_hold

    vault, repository = ctx.require_vault()
    if displayed:
        _exposure(ctx, _feedback_answer(ctx, then=_later(days=-2)), "display_mask", clock=_later(minutes=-1))
    _due_cold_task(ctx, case_ref="ep_due")
    repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref="ep_later",
        not_before=_iso(_later(days=3)), expires_at=_iso(_later(days=30)), selected_item_id=ITEM,
        clock=_later(days=-1),
    )

    hold = cold_check_serve_hold(vault, repository, ITEM)

    assert (hold is not None) is displayed


# -- F: the plan holds only for routine-display coverage, which clears by itself ----------------


def test_f1k_a_non_routine_reveal_never_starves_the_plan(tmp_path):
    """The verifier's case: one eligible item with a due cold retry and a
    tutor answer revealed 26 hours ago (a non-routine reveal). The plan's
    round-5 filter held it until the task expired and the plan finished with
    its minutes unused; main's serving behaviour is restored: the plan serves
    it (what submit then does with it is main's, unchanged, §12)."""

    from datetime import UTC, datetime

    from learnloop.daily_plan.engine import advance, get_or_create_today
    from tests.daily_plan_fakes import MovableClock, make_env, scheduled, seed_due
    from tests.helpers import create_daily_plan_vault

    start = datetime(2026, 10, 12, 10, 0, tzinfo=UTC)
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_c": [("pi_cold", 1.0)]})
    clock = MovableClock(start)
    env = make_env(paths.root, [scheduled("pi_cold", "lo_c", priority=0.9, followup_kind="cold_retry")],
                   clock=clock, session_id="s_one")
    seed_due(env.repository, "pi_cold", due=start - timedelta(days=2), last=start - timedelta(days=9))
    env.repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref="ep_one",
        not_before=_iso(FrozenClock(start - timedelta(hours=1))), expires_at=_iso(FrozenClock(start + timedelta(days=30))),
        selected_item_id="pi_cold", clock=FrozenClock(start - timedelta(days=1)),
    )
    env.repository.insert_reveal_event(
        {"practice_item_id": "pi_cold", "learning_object_id": "lo_c", "source_kind": "tutor_answer",
         "amount": 1.0, "basis": "tutor_answer"},
        clock=FrozenClock(start - timedelta(hours=26)),
    )
    get_or_create_today(env)
    _record, step = advance(env, serve=True)

    assert step.get("practice_item_id") == "pi_cold"


def test_f1k_a_routine_display_hold_clears_by_itself(tmp_path):
    """A routine display holds the planned cold check; once its coverage ends
    (D + G, then one second) the same plan serves it, with no other change."""

    from learnloop.daily_plan.engine import advance, get_or_create_today
    from learnloop.reveal_coverage import ROUTINE_DISPLAY_COVERAGE

    env, clock = _plan_with_a_cold_check(tmp_path, "clears")
    get_or_create_today(env)
    _display_on(env, "pi_cold", clock, "display_clears")
    clock.advance(1)
    advance(env, serve=True)
    assert "pi_cold" not in _served_items(env)

    clock.instant = clock.instant + ROUTINE_DISPLAY_COVERAGE
    for _step in range(4):
        advance(env, serve=True)
        if "pi_cold" in _served_items(env):
            break
    assert "pi_cold" in _served_items(env)


def test_f1k_the_tui_open_defers_a_cold_check_a_routine_display_covers(tmp_path):
    """The TUI's open is its serve: a due cold retry whose answer was shown
    (on the desktop, after the TUI built its list) is deferred when the item
    opens, so no cold check is administered."""

    import asyncio
    from datetime import UTC, datetime

    from learnloop.db.repositories import Repository
    from learnloop.tui.app import LearnLoopApp
    from learnloop.tui.screens.practice import PracticeScreen
    from tests.helpers import begin_session

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    repository = Repository(paths.sqlite_path)
    now = datetime.now(UTC).replace(microsecond=0)
    task = repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref="ep_tui",
        not_before=_iso(FrozenClock(now - timedelta(hours=1))), expires_at=_iso(FrozenClock(now + timedelta(days=30))),
        selected_item_id=ITEM, clock=FrozenClock(now - timedelta(days=1)),
    )

    async def scenario() -> None:
        app = LearnLoopApp(vault_root)
        async with app.run_test() as pilot:
            await pilot.pause()
            today = await begin_session(app, pilot)
            repository.insert_reveal_event({
                "practice_item_id": ITEM, "learning_object_id": "lo_svd_definition", "source_kind": "answer_display",
                "amount": 1.0, "basis": "feedback_full_answer:display_tui",
            })
            await today.open_practice()
            await pilot.pause()
            assert isinstance(app.screen, PracticeScreen)
            assert app.screen.item.practice_item_id == ITEM
            assert app.screen.item.followup_kind == "cold_retry"
            # Judged at the open itself (the list, built before the display,
            # still names it a cold check; leaving the app rebuilds it).
            assert repository.active_followup_task_for_item(ITEM, kind="cold_retry") is None
            assert repository.followup_task(task["id"])["not_before"] > _iso(FrozenClock(datetime.now(UTC)))

    asyncio.run(scenario())


# == Round 7 (docs/reviews/ux-phase4-feedback-codex-review.md §13) ==============================


def _routine_disclosure(repository, item_id: str, *, clock, learning_object_id: str = "lo_svd_definition") -> None:
    """A routine self-grade disclosure of ``item_id`` (an abandoned plain
    self-grade: the item stays never attempted, a probe candidate)."""

    repository.insert_reveal_event(
        {"practice_item_id": item_id, "learning_object_id": learning_object_id, "source_kind": "answer_display",
         "amount": 1.0, "basis": "self_grade_disclosure:v2:" + '{"display":"d","submission":"s","trace":"t","v":2}'},
        clock=clock,
    )


# -- D: every presentation writer is guarded, the scheduler's too --------------------------------


@pytest.mark.parametrize("covered", [False, True], ids=["control", "covered"])
def test_f1l_the_scheduler_never_commits_or_serves_a_covered_probe(tmp_path, monkeypatch, covered):
    """The verifier's reproduction: an in-progress episode with one eligible,
    never-attempted instrument whose routine self-grade disclosure was shown
    an hour ago. The named-session queue commits no presentation (it serves
    the item as ordinary practice), and the contract is not a probe."""

    from types import SimpleNamespace

    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop.db.repositories import Repository
    from learnloop.diagnosis.probe_episodes import enter_episode
    from learnloop.scheduling.scheduler import SchedulerSession, build_due_queue
    from learnloop.substrate.state_sync import sync_vault_state
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.handlers import practice as practice_handlers
    from tests.helpers import admit_probe_instrument_card

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository)
    loaded = load_vault(paths.root)
    sync_vault_state(loaded, repository)
    episode = enter_episode(loaded, repository, "lo_svd_definition")
    assert episode.status == "in_progress"
    if covered:
        _routine_disclosure(repository, ITEM, clock=_later(hours=-1))

    queue = build_due_queue(loaded, repository, session=SchedulerSession(session_id="probe_session"), limit=1)

    assert queue and queue[0].practice_item_id == ITEM
    assert (repository.active_probe_presentation(episode.id) is None) is covered
    monkeypatch.setattr(
        practice_handlers, "ready_grading_provider",
        lambda _vault, override=None: ("test", SimpleNamespace(ready=True), object()),
    )
    context = SidecarContext()
    context.load(paths.root)
    contract = _call(context, "get_probe_contract", {"practiceItemId": ITEM, "sessionId": "probe_session"})
    assert contract["active"] is (not covered)
    if covered:
        # Said why, as the causal offer does (not the generic "no_instrument").
        assert contract["reason"] == "probe_item_answer_shown"
    served = [row for row in repository.probe_presentations_for_episode(episode.id) if row.status == "served"]
    assert (not served) is covered


@pytest.mark.parametrize("covered", [False, True], ids=["control", "covered"])
def test_f1l_a_presentation_committed_before_a_display_is_not_served_inside_its_coverage(tmp_path, covered):
    """The serve itself (``serve_presentation``, the only path to ``served``):
    a presentation committed before the answer was shown is ended, not served."""

    from learnloop.diagnosis.probe_episodes import (
        RoutineDisplayCovered,
        commit_presentation,
        eligible_instruments,
        enter_episode,
        serve_presentation,
    )
    from tests.test_probe_orchestration_remainder import CLOCK, ITEM_ID, LO_ID, _setup

    _root, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    eligible = next(entry for entry in eligible_instruments(loaded, repository, episode) if entry.item.id == ITEM_ID)
    presentation = commit_presentation(loaded, repository, episode, eligible, clock=CLOCK)
    if covered:
        _routine_disclosure(repository, ITEM_ID, clock=FrozenClock(CLOCK.now() + timedelta(minutes=1)))

    later = FrozenClock(CLOCK.now() + timedelta(minutes=2))
    if covered:
        with pytest.raises(RoutineDisplayCovered):
            serve_presentation(repository, presentation.id, clock=later)
    else:
        serve_presentation(repository, presentation.id, clock=later)

    after = repository.probe_presentation(presentation.id)
    assert after.status == ("ended" if covered else "served")


@pytest.mark.parametrize("basis", ["tutor_answer", "routine_display"])
def test_f1l_the_quick_check_never_presents_an_item_inside_routine_display_coverage(tmp_path, basis):
    """Placement's own presentations (``placement_quick_check_items``) are
    excluded upstream: the candidates read the serving exclusions, which read
    routine displays by their coverage. Shown 24 h 30 min ago, a tutor answer
    has left the one-day window (control: presented first) while a routine
    display still covers the item (never presented)."""

    from tests.helpers import NOW
    from tests.test_assumed_known import _answer, _setup as placement_setup
    from tests.test_quick_check import _best_item, _progress, _start

    _paths, vault, repository = placement_setup(tmp_path)
    best = _best_item(vault, repository, ["lo_diag"])
    lo = vault.practice_items[best].learning_object_id
    stamp = FrozenClock(NOW - timedelta(hours=24, minutes=30))
    if basis == "tutor_answer":
        repository.insert_reveal_event(
            {"practice_item_id": best, "learning_object_id": lo, "source_kind": "tutor_answer",
             "amount": 1.0, "basis": "tutor_answer"},
            clock=stamp,
        )
    else:
        _routine_disclosure(repository, best, clock=stamp, learning_object_id=lo)

    session_id, progress = _start(vault, repository, ["lo_diag"])
    if basis == "tutor_answer":
        assert progress["next_target"]["practice_item_id"] == best
        return
    presented = []
    for minutes in (2, 4, 6, 8):
        target = progress["next_target"]
        if target is None:
            break
        presented.append(target["practice_item_id"])
        _answer(vault, repository, target["practice_item_id"], 4.0, minutes=minutes, session_id=session_id)
        progress = _progress(vault, repository, progress, minutes + 0.5)
    assert presented and best not in presented


def test_f1l_the_sim_skips_a_covered_instrument_instead_of_aborting_the_run(tmp_path, monkeypatch):
    """``sim.diagnostic_validation``'s loop commits presentations on a frozen
    clock (2026-02-02), so on a kept-state copy every later routine display
    would cover. A refused instrument is skipped, as production callers do,
    and the run goes on."""

    from learnloop.diagnosis import probe_episodes
    from learnloop.sim.diagnostic_validation import PLANTED_TYPES, run_probe_validation
    from tests.test_sim_probe_validation import _vault_with_confusable

    refused: list[str] = []
    original = probe_episodes.refuse_routine_display_covered

    def refuse_first(repository, practice_item_id, *, clock=None):
        if not refused or practice_item_id == refused[0]:
            refused.append(practice_item_id)
            raise probe_episodes.RoutineDisplayCovered(practice_item_id)
        return original(repository, practice_item_id, clock=clock)

    monkeypatch.setattr(probe_episodes, "refuse_routine_display_covered", refuse_first)
    vault_root = _vault_with_confusable(tmp_path)

    report = run_probe_validation(vault_root, tmp_path / "runs", planted_types=PLANTED_TYPES[:1], seeds=(11,))

    assert refused and report.results
    assert report.results[0].observations_used >= 1


# -- NEW 1: a refused causal offer changes nothing ------------------------------------------------


@pytest.mark.parametrize("race", [False, True], ids=["checked_first", "refused_at_commit"])
def test_f1l_a_refused_causal_offer_leaves_the_episode_and_its_presentation_unchanged(tmp_path, monkeypatch, race):
    """An observation-free episode holds an unconsumed presentation for item
    A; a causal probe is offered on item B, whose answer was just shown. The
    offer is refused before anything changes (and, if the display lands
    between the check and the commit, the commit's refusal rolls the relock
    back): the episode's lock and A's presentation are as they were."""

    from learnloop.diagnosis import causal_orchestrator
    from learnloop.diagnosis.causal_orchestrator import accept_probe_offer
    from learnloop.diagnosis.probe_episodes import commit_item_presentation, enter_episode, episode_hypothesis_set
    from tests.helpers import admit_probe_instrument_card
    from tests.test_causal_orchestrator import CLOCK, LO_ID, PROBE_ITEM, _activate_probe_candidate, _seed_factor, _vault

    vault, repository, _root = _vault(tmp_path, with_probe_item=True)
    factor_id, first_id, second_id = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM, ITEM))
    _activate_probe_candidate(repository, factor_id, first_id, second_id)
    plain = enter_episode(vault, repository, LO_ID, trigger="initial", clock=CLOCK)
    presentation_a = commit_item_presentation(
        vault, repository, plain, vault.practice_items[ITEM], episode_hypothesis_set(repository, plain), clock=CLOCK,
    )
    assert presentation_a is not None
    later = FrozenClock(CLOCK.now() + timedelta(days=1))
    _routine_disclosure(repository, PROBE_ITEM, clock=FrozenClock(later.now() - timedelta(hours=1)), learning_object_id=LO_ID)
    if race:
        monkeypatch.setattr(causal_orchestrator, "_answer_shown", lambda *_args, **_kwargs: False)

    offer = accept_probe_offer(vault, repository, factor_id=factor_id, clock=later)

    assert offer.accepted is False and offer.reason == "probe_item_answer_shown"
    after = repository.probe_episode(plain.id)
    assert (after.hypothesis_set_id, after.origin, after.entered_at, after.status) == (
        plain.hypothesis_set_id, plain.origin, plain.entered_at, plain.status,
    )
    kept = repository.probe_presentation(presentation_a.id)
    assert (kept.status, kept.end_reason) == ("served", None)
    assert [row.id for row in repository.probe_presentations_for_episode(plain.id)] == [presentation_a.id]


# -- NEW 2: a block's size and indices are its surviving members' --------------------------------


def test_f1l_a_precommitted_block_stamps_its_surviving_members_size_and_indices(tmp_path):
    """Two candidate members, one whose answer was just shown: the block holds
    the other alone, stamped block_size 1 and block_index 0, so its completion
    target is reachable."""

    from learnloop.diagnosis.probe_episodes import enter_episode, plan_precommitted_block
    from tests.test_probe_policy import CLOCK, ITEM_2, ITEM_ID, LO_ID, _setup as policy_setup

    loaded, repository = policy_setup(tmp_path, items=(ITEM_ID, ITEM_2))
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    _routine_disclosure(repository, ITEM_ID, clock=FrozenClock(CLOCK.now() - timedelta(hours=1)), learning_object_id=LO_ID)

    block = plan_precommitted_block(loaded, repository, episode, block_size=2, clock=CLOCK)

    assert [presentation.practice_item_id for presentation in block] == [ITEM_2]
    components = block[0].selection_components
    assert (components["block_size"], components["block_index"]) == (1, 0)


# -- F: a temporary hold never finishes the plan ------------------------------------------------


def _one_item_plan(tmp_path, display_age: timedelta):
    from datetime import UTC, datetime

    from tests.daily_plan_fakes import MovableClock, make_env, scheduled, seed_due
    from tests.helpers import create_daily_plan_vault

    start = datetime(2026, 10, 12, 10, 0, tzinfo=UTC)
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_c": [("pi_cold", 1.0)]})
    clock = MovableClock(start)
    env = make_env(paths.root, [scheduled("pi_cold", "lo_c", priority=0.9, followup_kind="cold_retry")],
                   clock=clock, session_id="s_wait")
    seed_due(env.repository, "pi_cold", due=start - timedelta(days=2), last=start - timedelta(days=9))
    env.repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref="ep_wait",
        not_before=_iso(FrozenClock(start - timedelta(hours=1))), expires_at=_iso(FrozenClock(start + timedelta(days=30))),
        selected_item_id="pi_cold", clock=FrozenClock(start - timedelta(days=1)),
    )
    env.repository.insert_reveal_event(
        {"practice_item_id": "pi_cold", "learning_object_id": "lo_c", "source_kind": "answer_display",
         "amount": 1.0, "basis": "feedback_full_answer:desktop:display_wait"},
        clock=FrozenClock(start - display_age),
    )
    return env, clock


def test_f1l_a_hold_that_lifts_today_waits_instead_of_finishing_the_plan(tmp_path):
    """The verifier's reproduction: one eligible item, a due cold retry, and a
    routine display stamped 25 h less 30 s ago. The plan is not finished: it
    waits, naming when the hold lifts; 31 seconds later the same plan serves
    the item."""

    from learnloop.daily_plan.engine import advance, get_or_create_today
    from learnloop.scheduling.scheduler import cold_check_serve_hold

    env, clock = _one_item_plan(tmp_path, timedelta(hours=25) - timedelta(seconds=30))
    record = get_or_create_today(env)
    assert record.status == "open"
    record, step = advance(env, serve=False)
    assert step["kind"] == "waiting"
    assert step["until"] == _iso(FrozenClock(clock.instant + timedelta(seconds=31)))
    assert step["minutes"] == 1
    assert step["learning_object_title"]
    # The view says so (not "choosing the next block").
    from learnloop.daily_plan.view import plan_view

    view = plan_view(env, record, context=None, next_step=step)["plan"]
    assert view["status"] == "open" and view["deciding"] is False
    assert view["waiting"] == {
        "until": step["until"], "minutes": 1, "practice_item_id": "pi_cold",
        "learning_object_title": step["learning_object_title"],
    }

    clock.instant = clock.instant + timedelta(seconds=31)
    assert cold_check_serve_hold(env.vault, env.repository, "pi_cold", clock=env.clock, persist=False) is None
    record, step = advance(env, serve=True)
    assert step["kind"] == "item" and step["practice_item_id"] == "pi_cold"
    assert record.id == get_or_create_today(env).id
    assert "pi_cold" in _served_items(env)


def test_f1l_a_hold_that_lifts_after_today_finishes_the_plan_as_before(tmp_path):
    """Control: a display shown just now holds the item past the plan's day,
    so there is nothing to wait for today and the plan finishes as before."""

    from learnloop.daily_plan.engine import advance, get_or_create_today

    env, _clock = _one_item_plan(tmp_path, timedelta(0))
    record = get_or_create_today(env)
    assert record.status == "complete"
    _record, step = advance(env, serve=False)
    assert step["kind"] == "done"


# == Round 8 (docs/reviews/ux-phase4-feedback-codex-review.md §14) ==============================


def _held_plan_env(tmp_path, others, *, lift_in=timedelta(minutes=60), policy=None, plan_toml=None, reentry=False,
                   cold_minutes=1.0, cold_lane="repair"):
    """A plan pool with ``pi_cold`` (a due cold retry whose answer a routine
    display covers until ``lift_in`` from now) beside ordinary reviews
    ``others`` = [(item_id, expected_minutes)]."""

    from learnloop.daily_plan.engine import DEFAULT_POLICY
    from tests.daily_plan_fakes import NOW, MovableClock, iso, make_env, scheduled, seed_due
    from tests.helpers import create_daily_plan_vault

    los = {"lo_c": [("pi_cold", cold_minutes)], **{f"lo_{item_id}": [(item_id, minutes)] for item_id, minutes in others}}
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=los, plan_toml=plan_toml)
    clock = MovableClock(NOW)
    # The scheduler names a cold retry a follow-up (the repair lane); the hold
    # reads the open task either way, so ``cold_lane="maintain"`` puts the same
    # held check in a lane the other work leaves room in.
    cold = (
        scheduled("pi_cold", "lo_c", forgetting_risk=0.9, followup_kind="cold_retry")
        if cold_lane == "repair"
        else scheduled("pi_cold", "lo_c", forgetting_risk=0.9)
    )
    items = [cold] + [
        scheduled(item_id, f"lo_{item_id}", forgetting_risk=0.7) for item_id, _minutes in others
    ]
    env = make_env(paths.root, items, clock=clock, session_id="s_held", policy=policy or DEFAULT_POLICY)
    for item_id in ["pi_cold", *[item_id for item_id, _minutes in others]]:
        seed_due(env.repository, item_id, due=NOW - timedelta(days=2), last=NOW - timedelta(days=9))
    if reentry:
        with env.repository.connection() as connection:
            connection.execute(
                "INSERT INTO sessions(id, started_at, ended_at, available_minutes) VALUES ('s_old', ?, ?, 40)",
                (iso(NOW - timedelta(days=12, minutes=30)), iso(NOW - timedelta(days=12))),
            )
            connection.commit()
    env.repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref="ep_held",
        not_before=_iso(FrozenClock(NOW - timedelta(hours=1))), expires_at=_iso(FrozenClock(NOW + timedelta(days=30))),
        selected_item_id="pi_cold", clock=FrozenClock(NOW - timedelta(days=1)),
    )
    env.repository.insert_reveal_event(
        {"practice_item_id": "pi_cold", "learning_object_id": "lo_c", "source_kind": "answer_display",
         "amount": 1.0, "basis": "feedback_full_answer:desktop:display_held"},
        clock=FrozenClock(NOW - timedelta(hours=25) + lift_in),
    )
    return env, clock


def _answer_through(env, clock, item_ids):
    from learnloop.daily_plan.engine import advance
    from tests.daily_plan_fakes import record_attempt

    for expected in item_ids:
        _record, step = advance(env, serve=True)
        assert step["kind"] == "item" and step["practice_item_id"] == expected, step
        clock.advance(2)
        # No latency: the plan's estimates stay as built (an answer's latency
        # would re-estimate the remaining items).
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], clock.now(),
                       latency_seconds=None, session_id="s_held")
        clock.advance(1)
    return advance(env, serve=False)


def test_f1m_a_plan_with_no_minutes_left_finishes_instead_of_waiting(tmp_path):
    """(a) A normal plan whose minutes are spent: the held item could not fit
    when its hold lifts, so the plan finishes as before (not "waiting")."""

    from learnloop.daily_plan.engine import build_plan

    env, clock = _held_plan_env(tmp_path, [("pi_a", 2.5)])
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    record, step = _answer_through(env, clock, ["pi_a"])

    assert record.minutes_left() == pytest.approx(0.0)
    assert step["kind"] == "done" and record.status == "complete"


def test_f1m_a_reentry_plan_with_no_item_slots_left_finishes_instead_of_waiting(tmp_path):
    """(b) A re-entry plan whose item allowance is used up: the held item
    could not be placed when its hold lifts, so the plan finishes."""

    from learnloop.daily_plan.engine import get_or_create_today

    env, clock = _held_plan_env(tmp_path, [("pi_a", 1.0)], plan_toml="[plan]\nreentry_max_items = 1\n", reentry=True)
    record = get_or_create_today(env)
    assert record.kind == "reentry"
    record, step = _answer_through(env, clock, ["pi_a"])

    assert record.minutes_left() > 2.0
    assert step["kind"] == "done" and record.status == "complete"


def test_f1m_a_valid_stop_with_work_feasible_is_kept(tmp_path):
    """(c) Four minutes left, one feasible ordinary item, and a valid sampled
    stop_for_today (propensity 0.5): the stop is the decision, closed and
    logged as before, not replaced by waiting."""

    from dataclasses import dataclass

    from learnloop.daily_plan.engine import PlanPolicy, build_plan, legacy_source
    from learnloop.daily_plan.types import STOP_FOR_TODAY, BlockChoice

    @dataclass
    class StoppingChooser:
        name: str = "fake_router"

        def choose(self, state, feasible):
            return BlockChoice(STOP_FOR_TODAY, "mixture", 0.5, "stop here", "model_written", "rd_stop")

    env, _clock = _held_plan_env(
        tmp_path, [("pi_s", 3.0)], policy=PlanPolicy("fake_source", StoppingChooser(), legacy_source),
    )
    record = build_plan(env, kind="normal", budget=4.0, remembered=4, minutes_source="chip")

    assert record.status == "complete" and not record.blocks
    (stop,) = record.stops()
    assert stop.chosen["candidate_id"] == STOP_FOR_TODAY and stop.chosen["propensity"] == 0.5
    assert stop.chosen["feasible_ids"]


@pytest.mark.parametrize("after_other_work", [False, True], ids=["only_item", "after_other_work"])
def test_f1m_a_plan_waits_when_coverage_is_the_only_obstacle_then_serves_it(tmp_path, after_other_work):
    """The positive case: minutes, slots and lane room are left, and the only
    thing between the plan and the held item is its coverage (alone in the
    plan, or after an ordinary item is done). The plan waits, then serves it
    once the hold lifts."""

    from learnloop.daily_plan.engine import advance, build_plan

    others = [("pi_a", 1.0)] if after_other_work else []
    env, clock = _held_plan_env(
        tmp_path, others, lift_in=timedelta(minutes=10), cold_lane="maintain" if after_other_work else "repair",
    )
    # 20 minutes: the maintain lane's share (30 %) still holds the check after
    # the ordinary item.
    build_plan(env, kind="normal", budget=20.0, remembered=20, minutes_source="chip")
    record, step = _answer_through(env, clock, [item_id for item_id, _minutes in others])

    assert step["kind"] == "waiting" and step["practice_item_id"] == "pi_cold" and record.status == "open"
    assert step["minutes"] == (8 if after_other_work else 11)
    clock.instant = clock.instant + timedelta(minutes=11)
    record, step = advance(env, serve=True)
    assert step["kind"] == "item" and step["practice_item_id"] == "pi_cold"
