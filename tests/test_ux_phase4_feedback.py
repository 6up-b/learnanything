"""UX Phase 4: practice and feedback (``docs/specs/ux_learnloop_v1.md`` §7.4, §7.5, §10).

The sidecar half of the phase. Everything here is display or learner-initiated
bookkeeping that replay never reads, so it is a live change behind the
``[ui] practice_feedback`` kill switch, with no algorithm successor:

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


def _next_attempt_primed(repository, *, submission_id=None, answer="a later answer") -> bool:
    from learnloop.attempts.attempts import auto_primed_draft

    draft, _total = auto_primed_draft(
        repository,
        AttemptDraft(practice_item_id=ITEM, learner_answer_md=answer, submission_id=submission_id),
    )
    return draft.primed


# -- F1: the full answer on feedback is an exposure ------------------------------------------


def test_f1_the_full_answer_shown_on_feedback_is_charged_once_to_the_reveal_ledger(ctx):
    """Feedback's "A full answer" panel is the expected answer itself: showing
    it debits the reveal ledger (once per attempt), so a retry taken with it in
    view is primed and an unaided response after it is not independent."""

    from learnloop.attempts.reveal_ledger import production_admissibility

    vault, repository = ctx.require_vault()
    attempt_id = _self_graded(ctx, points=0)
    assert not _next_attempt_primed(repository)

    _call(ctx, "record_answer_display", {"attemptId": attempt_id})
    _call(ctx, "record_answer_display", {"attemptId": attempt_id})

    rows = _reveals(repository, source_kind="answer_display")
    assert [(row["attempt_id"], row["amount"]) for row in rows] == [(attempt_id, 1.0)]
    assert _next_attempt_primed(repository)
    item = vault.practice_items[ITEM]
    later = production_admissibility(
        repository, practice_item_id=ITEM, learning_object_id=item.learning_object_id,
        produced_at="2999-01-01T00:00:00Z",
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
        _call(ctx, "record_answer_display", {"attemptId": attempt_id})

    result = _call(ctx, "submit_eliciting_response", {
        "attemptId": attempt_id, "suggestionIndex": 0, "responseMd": "The rows swap.",
    })

    assert result["admissibleAsIndependent"] is (not shown)


def test_f1_an_unknown_attempt_records_no_display(ctx):
    with pytest.raises(SidecarError) as raised:
        _call(ctx, "record_answer_display", {"attemptId": "att_missing"})
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
    assert bundle["answeredCriteria"] == {"correctness": {"description": "Correct definition.", "pointsPossible": 4.0}}


def _set_canonical_state(paths):
    from learnloop.learner.assessment_contracts import CANONICAL_STATE_VERSIONS
    from tests.helpers import set_algorithm_version

    set_algorithm_version(paths, sorted(CANONICAL_STATE_VERSIONS)[0])


def test_f5_an_answer_with_no_contract_carries_no_frozen_key(ctx):
    vault, repository = ctx.require_vault()
    attempt_id = _self_graded(ctx, answer="U Sigma V^T")
    bundle = feedback_bundle(vault, repository, attempt_id)
    assert bundle["answeredExpectedAnswer"] is None
    assert bundle["answeredCriteria"] is None


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
    assert bundle["answeredCriteria"] == {
        criterion.id: {"description": criterion.description, "pointsPossible": float(criterion.points)}
    }
