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

    with pytest.raises(SidecarError) as raised:
        _call(ctx, "trigger_regrade", {"attemptId": attempt_id, "learnerReason": "I did use the SVD"})
    assert raised.value.code == "ai_unavailable"

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
    # The facet ids behind it stay out of the payload.
    assert "demonstratedFacetIds" not in summary


def test_the_session_finish_names_a_topic_shown_on_your_own(ctx, monkeypatch):
    import learnloop.learner.session_learning_diff as diff_module

    vault, _repository = ctx.require_vault()
    item = vault.practice_items[ITEM]
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    _self_graded(ctx, session_id=session_id, points=2)
    real = diff_module.session_learning_diff

    def with_credit(vault_arg, repository_arg, sid):
        diff = dict(real(vault_arg, repository_arg, sid))
        diff["demonstrated_facet_ids"] = sorted(item.evidence_facets)
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
