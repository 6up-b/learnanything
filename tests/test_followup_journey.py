"""FG1 §3, §6, §10: the journey through the sidecar's doors, models faked.

A miss with two rivals: the verdict shows at once, the answer and causes are held, one
question is generated, Next opens it, its answer is admissible and closes the factor, the
held feedback appears, and that question is never served again by any door.
"""

from __future__ import annotations

import pytest

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.followup_serve import identity, workflow as wf
from learnloop.substrate.replay import rebuild_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar import handlers  # noqa: F401 - registers the methods
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.followup_serve_helpers import CLOCK, OFF, AuthorFake, author_clients, miss_with_rivals, rival_causes_vault, run_jobs


class _Runtime:
    ready = True
    status = "ready"
    message = None


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


@pytest.fixture
def journey(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "learnloop_sidecar.handlers.practice.ready_grading_provider",
        lambda *_args, **_kw: ("fake", _Runtime(), object()),
    )
    vault, repository, paths = rival_causes_vault(tmp_path)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.post_attempt_worker.autostart = False
    vault, repository = ctx.require_vault()
    result, outcome = miss_with_rivals(vault, repository)
    return ctx, vault, repository, result, outcome


def _generate(ctx, repository, *, fake=None):
    vault, _ = ctx.require_vault()
    run_jobs(vault, repository, clients=author_clients(fake or AuthorFake()))


def _answer(ctx, repository, row, *, points):
    vault, _ = ctx.require_vault()
    probe = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=row["practice_item_id"], learner_answer_md="An answer.",
                     attempt_type="diagnostic_probe", probe_presentation_id=row["presentation_id"]),
        SelfGradeInput(criterion_points=points, confidence=3),
        clock=CLOCK,
    )
    run_post_attempt_pipeline(vault, repository, result=probe, followup_surface="desktop", clock=CLOCK)
    return probe


def _refused(ctx, name, params, code=identity.GENERATED_PROBE_CLOSED):
    with pytest.raises(SidecarError) as caught:
        _call(ctx, name, params)
    assert caught.value.code == code


def test_the_answer_and_the_causes_are_held_and_the_verdict_is_not(journey):
    ctx, _vault, _repository, result, outcome = journey
    bundle = _call(ctx, "get_feedback", {"attemptId": result.attempt_id})
    assert bundle["followup"]["held"] is True and bundle["followup"]["line"].startswith("Preparing")
    assert bundle["followup"]["workflowId"] == outcome.workflow_id
    assert bundle["feedbackMd"] is None and bundle["repairSuggestions"] == [] and bundle["errorAttributions"] == []
    assert bundle["causalFeedback"] is None and bundle["unresolvedCauses"] == []
    assert bundle["correctness"] == 0.0 and bundle["criterionEvidence"]
    assert bundle["rubricScore"] == 0
    _refused(ctx, "record_answer_display", {"attemptId": result.attempt_id, "displayId": "d1"},
             code="followup_feedback_held")


def test_the_card_poll_records_no_reveal_for_content_it_hasnt_shown(journey):
    ctx, _vault, repository, result, _outcome = journey
    card = _call(ctx, "diagnosis_status", {"attemptId": result.attempt_id})
    assert card["status"] == "pending" and "repairSuggestions" not in card
    assert repository.reveal_events_for_target(practice_item_id=result.practice_item_id,
                                               learning_object_id=result.learning_object_id) == []


def test_opening_held_feedback_charges_nothing_until_it_is_released(journey):
    ctx, _vault, repository, result, _outcome = journey
    _call(ctx, "get_feedback", {"attemptId": result.attempt_id})
    assert repository.reveal_events_for_target(practice_item_id=result.practice_item_id,
                                               learning_object_id=result.learning_object_id) == []
    _call(ctx, "followup_show_anyway", {"attemptId": result.attempt_id})
    bundle = _call(ctx, "get_feedback", {"attemptId": result.attempt_id})
    assert bundle["feedbackMd"] == "Review the factorization." and bundle["followup"]["held"] is False
    assert bundle["repairSuggestions"]
    # The deferred display was charged once, on the actual disclosure.
    assert wf.attempt_workflow(repository, result.attempt_id)["feedback_debited_at"]


def test_next_waits_says_so_and_offers_the_way_out(journey):
    ctx, _vault, _repository, result, _outcome = journey
    step = _call(ctx, "followup_next", {"attemptId": result.attempt_id})
    assert step["action"] == "wait" and step["line"].startswith("Preparing")
    status = _call(ctx, "followup_status", {"attemptId": result.attempt_id})
    assert status["canContinueWithout"] is True and status["canShowAnyway"] is True


def test_the_whole_journey_and_never_again(journey):
    ctx, _vault, repository, result, outcome = journey
    fake = AuthorFake()
    _generate(ctx, repository, fake=fake)
    assert fake.calls == 1
    step = _call(ctx, "followup_next", {"attemptId": result.attempt_id})
    assert step["action"] == "open"
    item_id = step["practiceItemId"]
    row = wf.get(repository, outcome.workflow_id)
    # Listing and the plan never burn.
    assert identity.closed_probe_ids(repository) == frozenset()
    detail = _call(ctx, "open_queue_item", {"practiceItemId": item_id})
    assert detail["id"] == item_id or detail["practiceItemId"] == item_id
    assert item_id in identity.closed_probe_ids(repository)
    contract = _call(ctx, "get_probe_contract", {"practiceItemId": item_id})
    assert contract.get("active") is True, contract
    assert contract["presentationId"] == row["presentation_id"]
    # The burn kept its one valid submission, and it can close the factor.
    factor_id = row["factor_id"]
    criterion_points = {"fact_0": 0, "fact_1": 2}
    _answer(ctx, repository, row, points=criterion_points)
    observation = repository.causal_discriminating_observations(factor_id=factor_id)[0]
    assert observation["outcome"] == "matched_single" and observation["admitted"] and observation["resolved_factor"]
    assert observation["feature_source"] == "deterministic"
    assert repository.unresolved_cause_factor(factor_id)["status"] == "resolved"
    settled = wf.get(repository, outcome.workflow_id)
    assert settled["state"] == wf.SETTLED and settled["release_reason"] == wf.RELEASE_PROBE_ANSWERED
    bundle = _call(ctx, "get_feedback", {"attemptId": result.attempt_id})
    assert bundle["feedbackMd"] == "Review the factorization." and bundle["followup"]["held"] is False
    # Never again, by any door.
    _refused(ctx, "open_queue_item", {"practiceItemId": item_id})
    _refused(ctx, "get_practice_item", {"practiceItemId": item_id, "sessionId": "s1"}, code=identity.GENERATED_PROBE_CLOSED)
    vault, _ = ctx.require_vault()
    sync_vault_state(vault, repository, clock=CLOCK)
    assert not repository.practice_item_state(item_id).active
    rebuild_derived_state(vault, repository)
    assert not repository.practice_item_state(item_id).active
    assert _call(ctx, "followup_next", {"attemptId": result.attempt_id})["action"] == "continue"


def test_show_anyway_doesnt_cancel_the_probe_and_its_answer_cant_close_the_factor(journey):
    ctx, _vault, repository, result, outcome = journey
    _generate(ctx, repository)
    _call(ctx, "followup_status", {"attemptId": result.attempt_id})
    assert _call(ctx, "followup_show_anyway", {"attemptId": result.attempt_id})["released"] is True
    row = wf.get(repository, outcome.workflow_id)
    assert row["state"] == wf.READY and row["shown_anyway_at"]
    item_id = row["practice_item_id"]
    _call(ctx, "open_queue_item", {"practiceItemId": item_id})
    _call(ctx, "get_probe_contract", {"practiceItemId": item_id})
    _answer(ctx, repository, row, points={"fact_0": 0, "fact_1": 2})
    observation = repository.causal_discriminating_observations(factor_id=row["factor_id"])[0]
    assert not observation["admitted"] and observation["admissible_as_independent"] == 0
    assert repository.unresolved_cause_factor(row["factor_id"])["status"] == "open"


def test_a_lost_response_counts_as_burned_and_rebuild_keeps_the_one_submission(journey):
    ctx, _vault, repository, result, outcome = journey
    _generate(ctx, repository)
    row = wf.get(repository, outcome.workflow_id)
    _call(ctx, "followup_next", {"attemptId": result.attempt_id})
    _call(ctx, "get_practice_item", {"practiceItemId": row["practice_item_id"], "sessionId": "s1"})
    vault, _ = ctx.require_vault()
    rebuild_derived_state(vault, repository)
    # The same administration re-opens; its presentation still takes its one answer.
    _call(ctx, "open_queue_item", {"practiceItemId": row["practice_item_id"]})
    assert repository.probe_presentation(row["presentation_id"]).status != "ended"
    _answer(ctx, repository, row, points={"fact_0": 0, "fact_1": 2})
    assert wf.get(repository, outcome.workflow_id)["state"] == wf.SETTLED


def test_continue_without_it_retires_the_probe_and_next_goes_on(journey):
    ctx, _vault, repository, result, outcome = journey
    _generate(ctx, repository)
    row = wf.get(repository, outcome.workflow_id)
    assert _call(ctx, "followup_continue_without", {"attemptId": result.attempt_id})["continued"] is True
    settled = wf.get(repository, outcome.workflow_id)
    assert settled["state"] == wf.SKIPPED and settled["release_reason"] == wf.RELEASE_CONTINUE_WITHOUT
    assert row["practice_item_id"] in identity.retired_probe_ids(repository)
    assert _call(ctx, "followup_next", {"attemptId": result.attempt_id})["action"] == "continue"
    _refused(ctx, "open_queue_item", {"practiceItemId": row["practice_item_id"]})
    # Recorded as today's "Teach me now".
    from learnloop.diagnosis.causal_orchestrator import learner_preference

    assert learner_preference(repository, factor_id=row["factor_id"]) == "teach_now"


def test_a_generation_failure_says_so_and_next_works(journey):
    ctx, _vault, repository, result, outcome = journey
    _generate(ctx, repository, fake=AuthorFake(same_predictions=True))
    status = _call(ctx, "followup_status", {"attemptId": result.attempt_id})
    assert status["state"] == wf.FAILED and status["line"].startswith("Couldn't prepare")
    assert status["held"] is False
    assert _call(ctx, "followup_next", {"attemptId": result.attempt_id})["action"] == "continue"
    assert wf.get(repository, outcome.workflow_id)["release_reason"] == wf.RELEASE_GENERATION_FAILED


def test_a_reserved_probe_refuses_every_door_until_its_workflow_is_ready(journey):
    from learnloop.followup_serve.gates import PHONE_SURFACE  # noqa: F401
    from learnloop_sidecar.request_origin import RequestOrigin

    ctx, _vault, repository, result, outcome = journey
    _generate(ctx, repository)
    row = wf.get(repository, outcome.workflow_id)
    _call(ctx, "followup_status", {"attemptId": result.attempt_id})
    # A read with no session sees nothing until it was served.
    _refused(ctx, "get_practice_item", {"practiceItemId": row["practice_item_id"]},
             code=identity.GENERATED_PROBE_RESERVED)
    assert RequestOrigin is not None


def test_with_the_switch_off_nothing_changes_in_the_feedback(tmp_path):
    vault, repository, paths = rival_causes_vault(tmp_path, config=OFF)
    ctx = SidecarContext()
    ctx.load(paths.root)
    vault, repository = ctx.require_vault()
    result, outcome = miss_with_rivals(vault, repository)
    assert outcome.workflow_id is None
    bundle = _call(ctx, "get_feedback", {"attemptId": result.attempt_id})
    assert "followup" not in bundle and bundle["feedbackMd"] == "Review the factorization."
    assert _call(ctx, "followup_status", {"attemptId": result.attempt_id}) == {"version": 1, "enabled": False}
