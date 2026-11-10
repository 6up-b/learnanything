"""R9: a new miss with two or more distinct concrete causes gets a factor on the FG1 workflow path, at
the tag, even where the repair lane's own gate would have opened none. Weak cases are the router's.
"""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from learnloop.db.stores import followup_serve as store
from learnloop.diagnosis.causal_attribution import OPEN_SET_CAUSE_ID
from learnloop.diagnosis.split.jobs import drain
from learnloop.followup_run import jobs, router
from learnloop.followup_serve import identity, workflow as wf
from learnloop_sidecar import handlers  # noqa: F401 - registers the methods
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.followup_serve_helpers import (
    LIVE_ITEM,
    OFF,
    TAG,
    AuthorFake,
    BlindRivalClient,
    author_clients,
    live_miss,
    live_shape_vault,
    run_jobs,
)

SHAPES = ["no_target", "no_repair", "other_criterion", "trivial"]


class _Ready:
    ready = True
    status = "ready"
    active_provider = "fake"
    provider_type = "codex_sdk"
    model = "fake-model"
    provider_revision = None
    message = None


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _reasons(repository, workflow_id):
    with repository.connection() as connection:
        return [event["reason"] for event in store.workflow_events(connection, workflow_id)]


@pytest.fixture
def desk(tmp_path, monkeypatch):
    """The sidecar over a blind vault, every model faked, the workers driven by hand."""

    paths, _vault, _repository = live_shape_vault(tmp_path)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.post_attempt_worker.autostart = False
    client = BlindRivalClient()
    monkeypatch.setattr("learnloop_sidecar.handlers.practice.ready_grading_provider",
                        lambda *_a, **_k: ("fake", _Ready(), client))
    session = _call(ctx, "start_session", {"available_minutes": 30})
    return SimpleNamespace(ctx=ctx, client=client, session=session.get("sessionId") or session["session_id"], paths=paths)


def _miss(desk, shape):
    desk.client.shape = shape
    vault, repository = desk.ctx.require_vault()
    result = _call(desk.ctx, "submit_attempt", {
        "sessionId": desk.session, "practiceItemId": LIVE_ITEM, "answerMd": "A = U Sigma V wrong",
        "attemptType": "independent_attempt", "latencySeconds": 60,
    })
    attempt_id = result.get("attemptId") or result["attempt_id"]
    drain(vault, repository, client_factory=lambda: desk.client, embedding_factory=lambda: None)
    return attempt_id


def _generate(desk, fake=None):
    vault, repository = desk.ctx.require_vault()
    fake = fake or AuthorFake()
    while jobs.process_next_job(vault, repository, owner="test", clients=author_clients(fake)) is not None:
        pass
    return fake


def _factors(repository, attempt_id, status="open"):
    return repository.unresolved_cause_factors_for_attempt(attempt_id, status=status)


@pytest.mark.parametrize("shape", SHAPES)
def test_each_shape_opens_a_factor_serves_a_question_and_its_answer_closes_it(desk, shape):
    attempt_id = _miss(desk, shape)
    _vault, repository = desk.ctx.require_vault()
    assert not _factors(repository, attempt_id)  # the repair lane's gate opened none
    fake = _generate(desk)
    assert fake.calls == 1
    row = wf.attempt_workflow(repository, attempt_id)
    assert row["state"] == wf.READY and row["lane"] == wf.LANE_PROBE
    factor = _factors(repository, attempt_id)[0]
    assert any(cause.get("hypothesis_id") == OPEN_SET_CAUSE_ID or cause.get("open_set") for cause in factor["candidate_causes"])
    held = _call(desk.ctx, "get_feedback", {"attemptId": attempt_id})
    assert held["followup"]["held"] is True

    action = _call(desk.ctx, "followup_next", {"attemptId": attempt_id})
    assert action["action"] in {"open", "continue"}
    desk.ctx.reload(maintenance=False)
    vault, repository = desk.ctx.require_vault()
    _call(desk.ctx, "open_queue_item", {"practiceItemId": row["practice_item_id"]})
    contract = _call(desk.ctx, "get_probe_contract", {"practiceItemId": row["practice_item_id"]})
    assert contract["active"] is True
    _call(desk.ctx, "submit_attempt", {
        "sessionId": desk.session, "practiceItemId": row["practice_item_id"], "answerMd": "An answer.",
        "attemptType": "diagnostic_probe", "latencySeconds": 40, "probePresentationId": contract["presentationId"],
    })
    assert wf.get(repository, row["id"])["state"] == wf.SETTLED
    assert repository.unresolved_cause_factor(factor["id"])["status"] == "resolved"
    # Nothing downstream waits on a repair class: no mapping owed, no cold retry or remediation opened.
    assert not repository.causal_machine_checks(status="pending", factor_id=factor["id"])
    assert not repository.open_followup_tasks_of_kind("cold_retry")
    released = _call(desk.ctx, "get_feedback", {"attemptId": attempt_id})
    assert released["followup"]["held"] is False
    assert released["answeredExpectedAnswer"] and released["causalFeedback"]
    assert _call(desk.ctx, "followup_next", {"attemptId": attempt_id})["action"] == "continue"
    assert row["practice_item_id"] in identity.closed_probe_ids(repository)


@pytest.mark.parametrize("shape", SHAPES)
def test_no_intervention_declines_it_and_leaves_no_open_factor_behind(desk, shape, monkeypatch):
    real = router.decide
    monkeypatch.setattr(router, "decide", lambda *a, **k: replace(
        real(*a, **k), chosen_ref=router.NO_INTERVENTION, reason=router.NO_INTERVENTION))
    attempt_id = _miss(desk, shape)
    fake = _generate(desk)
    _vault, repository = desk.ctx.require_vault()
    assert fake.calls == 0  # nothing paid for a question the router declined
    row = wf.attempt_workflow(repository, attempt_id)
    assert row["state"] == wf.SETTLED and row["feedback_released_at"]
    assert not _factors(repository, attempt_id)
    assert [factor["resolution_kind"] for factor in _closed(repository, attempt_id)] == [wf.FACTOR_DECLINED]
    assert _call(desk.ctx, "followup_next", {"attemptId": attempt_id})["action"] == "continue"


def _closed(repository, attempt_id):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT status, resolution_kind FROM unresolved_cause_factors WHERE attempt_id = ? AND status != 'open'",
            (attempt_id,))]


def test_one_concrete_cause_stays_as_it_was(desk):
    desk.client.causes = 1
    attempt_id = _miss(desk, "no_target")
    fake = _generate(desk)
    _vault, repository = desk.ctx.require_vault()
    assert fake.calls == 0 and not _factors(repository, attempt_id)
    row = wf.attempt_workflow(repository, attempt_id)
    assert row["state"] == wf.SETTLED and row["lane"] == wf.LANE_PRACTICE


def test_a_factor_the_repair_lane_opened_is_used_and_not_doubled(desk):
    attempt_id = _miss(desk, "")
    _vault, repository = desk.ctx.require_vault()
    before = [factor["id"] for factor in _factors(repository, attempt_id)]
    assert len(before) == 1
    _generate(desk)
    assert [factor["id"] for factor in _factors(repository, attempt_id)] == before


def _no_rival_factor(tmp_path, *, version=TAG, config=""):
    paths, vault, repository = live_shape_vault(tmp_path, version=version, config=config)
    client = BlindRivalClient()
    client.shape = "no_target"
    result, _outcome = live_miss(vault, repository, client)
    return vault, repository, result


def test_below_the_tag_and_with_the_switch_off_nothing_opens(tmp_path):
    from learnloop.followup_run.lanes import open_rival_factor

    for name, version, config in (("below", "mvp-0.44", ""), ("off", TAG, OFF)):
        vault, repository, result = _no_rival_factor(tmp_path / name, version=version, config=config)
        row = {"id": "fw", "source_attempt_id": result.attempt_id}
        assert open_rival_factor(vault, repository, row) is None
        assert not _factors(repository, result.attempt_id)


def test_a_retry_opens_nothing_more_and_a_closed_factor_doesnt_come_back(tmp_path):
    from learnloop.followup_run.lanes import open_rival_factor

    vault, repository, result = _no_rival_factor(tmp_path)
    row = {"id": "fw", "source_attempt_id": result.attempt_id}
    first = open_rival_factor(vault, repository, row)
    assert first and open_rival_factor(vault, repository, row) is None
    repository.close_unresolved_cause_factor(first, status="retired", resolution_kind="test")
    assert open_rival_factor(vault, repository, row) is None


def test_opening_the_factor_moves_no_measurement(tmp_path):
    from learnloop.followup_run.lanes import open_rival_factor

    vault, repository, result = _no_rival_factor(tmp_path)
    before = _state(vault, repository)
    assert open_rival_factor(vault, repository, {"id": "fw", "source_attempt_id": result.attempt_id})
    assert _state(vault, repository) == before


def _state(vault, repository):
    """Facet, mastery and schedule, as a rebuild compares them, and certification's own rows."""

    from learnloop.substrate.shadow_rebuild import _learner_state_snapshot

    snapshot = _learner_state_snapshot(repository)
    with repository.connection() as connection:
        rows = connection.execute("SELECT COUNT(*) FROM certification_cold_probe_outcomes").fetchone()[0]
    return {**snapshot, "certification": rows}


def test_an_answered_probe_moves_the_same_measurement_with_or_without_a_mapped_repair(tmp_path, monkeypatch):
    """Whatever an answered probe does, a factor opened this way does no more and no less. The clock
    is frozen, because mastery decays by the wall clock and the two runs are moments apart."""

    from datetime import timedelta

    from learnloop.clock import SystemClock

    instant = SystemClock().now()
    monkeypatch.setattr(SystemClock, "now", lambda self: instant + timedelta(days=1))
    states = {}
    for shape in ("", "no_target"):
        paths, _vault, _repository = live_shape_vault(tmp_path / (shape or "mapped"))
        ctx = SidecarContext()
        ctx.load(paths.root)
        ctx.post_attempt_worker.autostart = False
        client = BlindRivalClient()
        monkeypatch.setattr("learnloop_sidecar.handlers.practice.ready_grading_provider",
                            lambda *_a, **_k: ("fake", _Ready(), client))  # noqa: B023  called within this iteration, before the loop rebinds it
        session = _call(ctx, "start_session", {"available_minutes": 30})
        desk = SimpleNamespace(ctx=ctx, client=client, session=session.get("sessionId") or session["session_id"], paths=paths)
        attempt_id = _miss(desk, shape)
        _generate(desk)
        ctx.reload(maintenance=False)
        vault, repository = ctx.require_vault()
        row = wf.attempt_workflow(repository, attempt_id)
        before = _shape_of_state(repository)
        _call(ctx, "open_queue_item", {"practiceItemId": row["practice_item_id"]})
        contract = _call(ctx, "get_probe_contract", {"practiceItemId": row["practice_item_id"]})
        _call(ctx, "submit_attempt", {
            "sessionId": desk.session, "practiceItemId": row["practice_item_id"], "answerMd": "An answer.",
            "attemptType": "diagnostic_probe", "latencySeconds": 40, "probePresentationId": contract["presentationId"],
        })
        states[shape] = _shape_of_state(repository)
        # So this can't pass vacuously: the answer does move measurement, and it does schedule.
        assert states[shape]["mastery"] != before["mastery"] or states[shape]["facet"] != before["facet"]
        assert states[shape]["schedule"] != before["schedule"]
    assert states[""] == states["no_target"]


def _shape_of_state(repository):
    """The learner's state with ids and times out of it: what a mapped repair could change."""

    from learnloop.substrate.shadow_rebuild import _learner_state_snapshot

    snapshot = _learner_state_snapshot(repository)
    drop = ("updated_at", "created_at", "last_", "due", "_at", "id")
    out = {}
    for family in ("mastery", "facet", "schedule"):
        out[family] = sorted(
            repr((key if family != "schedule" or not str(key[-1]).startswith("pi_gen_") else (key[0], "pi_gen"),
                  sorted((name, str(value)) for name, value in row.items()
                         if not any(mark in name for mark in drop) and name != "content_hash")))
            for key, row in snapshot[family].items()
        )
    with repository.connection() as connection:
        out["certification"] = connection.execute("SELECT COUNT(*) FROM certification_cold_probe_outcomes").fetchone()[0]
    return out


def test_a_sweep_queues_no_mapping_this_factor_doesnt_need_and_a_retry_still_asks(desk):
    from datetime import timedelta

    from learnloop.clock import FrozenClock
    from learnloop.diagnosis.causal_orchestrator import sweep_machine_checks

    from tests.followup_serve_helpers import CLOCK

    attempt_id = _miss(desk, "no_target")
    _generate(desk, AuthorFake(error=RuntimeError("provider down")))
    vault, repository = desk.ctx.require_vault()
    row = wf.attempt_workflow(repository, attempt_id)
    assert row["state"] == wf.PENDING and row["factor_id"]
    sweep_machine_checks(vault, repository, row["learning_object_id"])
    assert not repository.causal_machine_checks(status="pending", factor_id=row["factor_id"])
    fake = AuthorFake()
    run_jobs(vault, repository, clients=author_clients(fake), clock=FrozenClock(CLOCK.now() + timedelta(days=400)))
    assert fake.calls == 1 and wf.get(repository, row["id"])["state"] == wf.READY


def test_a_cause_matching_a_reserved_question_closes_the_factor_this_lane_opened(desk, monkeypatch):
    from learnloop.followup_run import authoring

    monkeypatch.setattr(authoring, "causes_match_reserved", lambda *_a, **_k: True)
    attempt_id = _miss(desk, "no_target")
    _generate(desk)
    _vault, repository = desk.ctx.require_vault()
    assert wf.attempt_workflow(repository, attempt_id)["lane"] == wf.LANE_PRACTICE
    assert not _factors(repository, attempt_id)


def test_continue_without_it_closes_it_and_a_failure_keeps_it_for_its_need(desk):
    attempt_id = _miss(desk, "trivial")
    _generate(desk)
    _vault, repository = desk.ctx.require_vault()
    assert _call(desk.ctx, "followup_continue_without", {"attemptId": attempt_id})["continued"] is True
    assert not _factors(repository, attempt_id)
    second = _miss(desk, "no_repair")
    _generate(desk, AuthorFake(same_predictions=True))
    row = wf.attempt_workflow(repository, second)
    assert row["state"] == wf.FAILED and _factors(repository, second)
    assert _call(desk.ctx, "followup_next", {"attemptId": second})["action"] == "continue"


def test_a_later_miss_on_the_topic_runs_with_this_factor_open(desk):
    first = _miss(desk, "no_target")
    _generate(desk)
    second = _miss(desk, "no_repair")
    _vault, repository = desk.ctx.require_vault()
    assert wf.attempt_workflow(repository, first)["state"] == wf.READY
    assert wf.attempt_workflow(repository, second)["state"] == wf.PENDING
    _generate(desk)
    assert wf.attempt_workflow(repository, second)["state"] in {wf.READY, wf.REFUSED}


@pytest.mark.parametrize("shape", SHAPES)
def test_what_the_learner_sees_when_no_repair_exists(desk, shape, capsys):
    attempt_id = _miss(desk, shape)
    _generate(desk)
    desk.ctx.reload(maintenance=False)
    _vault, repository = desk.ctx.require_vault()
    row = wf.attempt_workflow(repository, attempt_id)
    _call(desk.ctx, "open_queue_item", {"practiceItemId": row["practice_item_id"]})
    contract = _call(desk.ctx, "get_probe_contract", {"practiceItemId": row["practice_item_id"]})
    probe = _call(desk.ctx, "submit_attempt", {
        "sessionId": desk.session, "practiceItemId": row["practice_item_id"], "answerMd": "An answer.",
        "attemptType": "diagnostic_probe", "latencySeconds": 40, "probePresentationId": contract["presentationId"],
    })
    bundle = _call(desk.ctx, "get_feedback", {"attemptId": attempt_id})
    # The worked answer is released whatever the mapping; a repair offer is only what exists.
    assert bundle["answeredExpectedAnswer"]
    assert not bundle.get("commonRepair")
    with capsys.disabled():
        print("\nSEES", shape, {key: (bool(bundle.get(key)) if not isinstance(bundle.get(key), (bool, str)) else str(bundle.get(key))[:30])
                                for key in ("answeredExpectedAnswer", "feedbackMd", "repairSuggestions", "causalFeedback",
                                            "unresolvedCauses", "commonRepair", "guidedRedoAvailable", "interventionNeed")},
              "probe_keys", {key: bool(probe.get(key)) for key in ("followup", "followupSource")})
