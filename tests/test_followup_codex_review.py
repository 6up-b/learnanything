"""FG1's Codex review (docs/reviews/followup-fg1-codex-review.md): each finding's failure, reproduced.

Crashes are injected with a BaseException, which the generation job's typed-failure handler
doesn't catch, so what is left behind is what a dead process would leave.
"""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

import pytest

from learnloop import learner_protection
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.clock import FrozenClock
from learnloop.daily_plan.engine import advance
from learnloop.daily_plan.router_runtime import GUARDED_OWNERS, RouterSpend, SpendRefused
from learnloop.db.stores import followup_serve as store
from learnloop.followup_run import jobs, router, serving
from learnloop.followup_run.decision_view import decision_view
from learnloop.followup_serve import identity, workflow as wf
from learnloop.followup_serve.gates import generate_and_serve_on
from learnloop.scheduling.scheduler import build_due_queue
from learnloop.substrate.replay import rebuild_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop_sidecar import handlers  # noqa: F401 - registers the methods
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.followup_serve_helpers import (
    CLOCK,
    OFF,
    TAG,
    AuthorFake,
    author_clients,
    miss_with_rivals,
    rival_causes_vault,
    run_jobs,
)
from tests.helpers import append_config_toml
from tests.router_model_fakes import fake_runtime
from tests.split_live_helpers import drain_jobs, fake_client, split_vault, submit
from tests.causal_p2_acceptance_helpers import LO_ID, SOURCE_ITEM
from tests.followup_router_helpers import ITEM, _env, _gate, _ready, _workflow
from tests.probe_surface_mint_helpers import FakeSurfacesClient

LATER = FrozenClock(CLOCK.now() + timedelta(hours=2))
SENTINEL = "SENTINEL_MATRIX_7"


class Died(BaseException):
    """The process, gone: no handler in the job catches this."""


class _Runtime:
    ready = True
    status = "ready"
    message = None


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _refused(ctx, name, params, code=identity.GENERATED_PROBE_CLOSED):
    with pytest.raises(SidecarError) as caught:
        _call(ctx, name, params)
    assert caught.value.code == code


@pytest.fixture
def journey(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "learnloop_sidecar.handlers.practice.ready_grading_provider",
        lambda *_args, **_kw: ("fake", _Runtime(), object()),
    )
    _vault, _repository, paths = rival_causes_vault(tmp_path)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.post_attempt_worker.autostart = False
    vault, repository = ctx.require_vault()
    result, outcome = miss_with_rivals(vault, repository)
    return SimpleNamespace(ctx=ctx, vault=vault, repository=repository, result=result, workflow_id=outcome.workflow_id,
                           paths=paths)


def _job(repository, workflow_id):
    with repository.connection() as connection:
        return store.generation_job(connection, f"workflow:{workflow_id}")


# -- F1: generation counts in the shared daily total ------------------------------------------------


class _Metered:
    def __init__(self, usd, *, fail=False):
        self.usd, self.fail, self.sent = usd, fail, 0

    def estimated_cost(self, _input_tokens):
        return self.usd

    def send(self):
        from learnloop.ai.execution import model_call, report_call_usage

        with model_call(self, purpose="followup_probe_authoring", prompt="x"):
            self.sent += 1
            if self.fail:
                raise RuntimeError("provider down")
            report_call_usage({"cost": self.usd})


def _capped(vault, cap):
    vault.config.router.max_daily_cost_usd = cap
    return vault.config


def test_f1_generation_receipts_are_in_the_daily_total(tmp_path):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    config = _capped(vault, 0.30)
    assert jobs.RECEIPT_OWNER in GUARDED_OWNERS
    spend = RouterSpend()
    with spend.metered(repository, config, owner_kind=jobs.RECEIPT_OWNER, owner_id="job1"):
        _Metered(0.29).send()
    late = _Metered(0.02)
    with pytest.raises(SpendRefused), spend.metered(repository, config, owner_kind=jobs.RECEIPT_OWNER, owner_id="job2"):
        late.send()
    assert late.sent == 0


def test_f1_a_failed_generation_keeps_its_reservation(tmp_path):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    config = _capped(vault, 0.30)
    spend = RouterSpend()
    with pytest.raises(RuntimeError), spend.metered(repository, config, owner_kind=jobs.RECEIPT_OWNER, owner_id="job1"):
        _Metered(0.29, fail=True).send()
    late = _Metered(0.02)
    with pytest.raises(SpendRefused), spend.metered(repository, config, owner_kind=jobs.RECEIPT_OWNER, owner_id="job2"):
        late.send()
    assert late.sent == 0


def test_f1_an_in_flight_generation_reserves_against_the_next(tmp_path):
    from learnloop.ai.execution import model_call

    vault, repository, _paths = rival_causes_vault(tmp_path)
    config = _capped(vault, 0.30)
    spend = RouterSpend()
    first, second = _Metered(0.29), _Metered(0.02)
    with spend.metered(repository, config, owner_kind=jobs.RECEIPT_OWNER, owner_id="job1"):
        with model_call(first, purpose="followup_probe_authoring", prompt="x"):
            # Started and unfinished: only its reservation stands for it.
            with pytest.raises(SpendRefused):
                second.send()
    assert second.sent == 0


def test_f1_generation_spend_refuses_the_routers_own_next_request(tmp_path):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    config = _capped(vault, 0.30)
    spend = RouterSpend()
    with spend.metered(repository, config, owner_kind=jobs.RECEIPT_OWNER, owner_id="job1"):
        _Metered(0.29).send()
    router_request = _Metered(0.02)
    with pytest.raises(SpendRefused), spend.metered(repository, config, owner_kind="router_decision", owner_id="k"):
        router_request.send()
    assert router_request.sent == 0


# -- F2: details while the causes are held ----------------------------------------------------------


def _held_decision(tmp_path):
    env, record = _env(tmp_path, fake_runtime())
    row = _workflow(env)
    outcome = _gate(env).decide_followup(record, record.current_block(), row, wait_feasible=True)
    decision = router.FollowupDecision(
        router.ASK_NOW, router.ASK_NOW, "mixture", propensity=outcome.record["mixture"]["pi"][router.ASK_NOW],
        record=dict(outcome.record), block_id=record.current_block().id, plan_id=record.id, plan_kind=record.kind,
        local_date="2026-11-03",
    )
    return env, row, router.record_decision(env.vault, env.repository, row, decision, clock=env.clock)


def test_f2_details_leave_out_the_held_causes_until_they_are_released(tmp_path):
    env, row, decision = _held_decision(tmp_path)
    attempt_id = row["source_attempt_id"]
    seen = serving.view(env.vault, env.repository, attempt_id)
    assert seen["held"] is True
    details = seen["router_decision"]["details"]
    assert details["held"] is True and details["card_summary"] is None and details["rationale"] is None
    assert details["observational"] is None
    # The line and the numbers stay: it is the same decision.
    assert seen["router_decision"]["line"].startswith("Router: ask now") and details["models"] is not None
    # No exposure happened, so nothing marks the probe's answer.
    assert wf.get(env.repository, row["id"])["shown_anyway_at"] is None
    # The one exit that records the exposure gives the card back.
    assert serving.show_anyway(env.repository, attempt_id, clock=env.clock)
    released = serving.view(env.vault, env.repository, attempt_id)["router_decision"]["details"]
    assert released["held"] is False and released["card_summary"]


def test_f2_another_decisions_card_is_held_too_since_cards_list_open_problems(tmp_path):
    env, _row, decision = _held_decision(tmp_path)
    # The plan's line reads the same view for the block's own decision.
    assert decision_view(env.repository, decision.decision_id)["details"]["card_summary"] is None
    with env.repository.atomic(), env.repository.connection() as connection:
        store.update_workflow(connection, "fw_test", at=env.now_iso(), feedback_released_at=env.now_iso())
    assert decision_view(env.repository, decision.decision_id)["details"]["card_summary"]


# -- F3: a publication a crash interrupted ----------------------------------------------------------


def _writes_then_dies(monkeypatch):
    from learnloop.vault import writer

    real = writer.upsert_practice_item

    def dying(root, payload, **kwargs):
        real(root, payload, **kwargs)
        raise Died()

    monkeypatch.setattr(writer, "upsert_practice_item", dying)
    return real


def _the_file_alone_after_the_crash(journey, monkeypatch):
    fake = AuthorFake()
    real = _writes_then_dies(monkeypatch)
    with pytest.raises(Died):
        jobs.process_next_job(journey.vault, journey.repository, owner="dead", clients=author_clients(fake), clock=CLOCK)
    monkeypatch.setattr("learnloop.vault.writer.upsert_practice_item", real)
    vault = load_vault(journey.paths.root)
    sync_vault_state(vault, journey.repository, clock=CLOCK)
    orphan = next(item.id for item in vault.practice_items.values() if item.surface_family and "followup_" in item.surface_family)
    return vault, orphan, fake


def test_f3_a_crash_after_the_file_leaves_an_identified_parked_item(journey, monkeypatch):
    vault, orphan, _fake = _the_file_alone_after_the_crash(journey, monkeypatch)
    repository = journey.repository
    assert identity.is_generated_probe(repository, orphan)
    assert repository.probe_item_family_links(orphan)
    assert not repository.practice_item_state(orphan).active  # the sync parked it
    assert orphan not in {item.practice_item_id for item in build_due_queue(vault, repository, limit=None)}
    journey.ctx.reload(maintenance=False)
    _refused(journey.ctx, "open_queue_item", {"practiceItemId": orphan}, code=identity.GENERATED_PROBE_RESERVED)
    _refused(journey.ctx, "get_practice_item", {"practiceItemId": orphan, "sessionId": "s1"},
             code=identity.GENERATED_PROBE_RESERVED)
    assert identity.closed_probe_ids(repository) == frozenset()  # a refused door burned nothing


def test_f3_the_retry_retires_the_orphan_and_serves_its_own_question(journey, monkeypatch):
    vault, orphan, fake = _the_file_alone_after_the_crash(journey, monkeypatch)
    repository = journey.repository
    outcomes = run_jobs(vault, repository, clients=author_clients(fake), clock=LATER)  # the lease has lapsed
    assert [job.state for job in outcomes] == ["done"]
    row = wf.get(repository, journey.workflow_id)
    assert row["state"] == wf.READY and row["practice_item_id"] != orphan
    assert orphan in identity.retired_probe_ids(repository)
    assert repository.practice_item_state(row["practice_item_id"]).active
    rebuild_derived_state(load_vault(journey.paths.root), repository)
    assert not repository.practice_item_state(orphan).active


def test_f3_a_crash_after_the_pin_ends_the_pin_with_the_retired_item(journey, monkeypatch):
    from learnloop.followup_run import admission

    repository = journey.repository
    real = admission.commission_and_pin
    pinned = {}

    def pins_then_dies(*args, **kwargs):
        pinned["admitted"] = real(*args, **kwargs)
        raise Died()

    monkeypatch.setattr(admission, "commission_and_pin", pins_then_dies)
    fake = AuthorFake()
    with pytest.raises(Died):
        jobs.process_next_job(journey.vault, repository, owner="dead", clients=author_clients(fake), clock=CLOCK)
    monkeypatch.setattr(admission, "commission_and_pin", real)
    vault = load_vault(journey.paths.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    first = pinned["admitted"]
    # Admitted and pinned, and its workflow never named it: its reservation holds.
    journey.ctx.reload(maintenance=False)
    _refused(journey.ctx, "open_queue_item", {"practiceItemId": first.practice_item_id},
             code=identity.GENERATED_PROBE_RESERVED)
    outcomes = run_jobs(vault, repository, clients=author_clients(fake), clock=LATER)
    assert [job.state for job in outcomes] == ["done"]
    row = wf.get(repository, journey.workflow_id)
    assert row["state"] == wf.READY and row["practice_item_id"] != first.practice_item_id
    assert first.practice_item_id in identity.retired_probe_ids(repository)
    assert repository.probe_presentation(first.presentation_id).status == "ended"
    assert repository.probe_presentation(row["presentation_id"]).status != "ended"


def test_f3_a_failed_file_write_serves_nothing_and_the_retry_goes_on(journey, monkeypatch):
    from learnloop.vault import writer

    repository = journey.repository
    real = writer.upsert_practice_item

    def full_disk(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(writer, "upsert_practice_item", full_disk)
    fake = AuthorFake()
    first = jobs.process_next_job(journey.vault, repository, owner="w", clients=author_clients(fake), clock=CLOCK)
    assert first.state == "retry"
    monkeypatch.setattr(writer, "upsert_practice_item", real)
    orphans = identity.generated_probe_ids(repository)
    assert len(orphans) == 1
    outcomes = run_jobs(journey.vault, repository, clients=author_clients(fake), clock=LATER)
    assert [job.state for job in outcomes] == ["done"]
    assert orphans <= identity.retired_probe_ids(repository)
    assert wf.get(repository, journey.workflow_id)["state"] == wf.READY


@pytest.mark.parametrize("via", ["mint", "batch"])
def test_f3_the_mint_and_the_batch_write_the_identity_before_the_file(tmp_path, monkeypatch, via):
    from learnloop.diagnosis import probe_instance_generation as pig
    from learnloop.diagnosis.probe_episodes import enter_episode

    vault, repository, paths = rival_causes_vault(tmp_path)
    existing = repository.open_probe_episode(LO_ID)
    if existing is not None:
        repository.update_probe_episode_status(existing.id, status="abandoned", clock=CLOCK)
    episode = enter_episode(vault, repository, LO_ID, trigger="manual", clock=CLOCK, ai_client=None)
    repository.update_probe_episode_status(episode.id, status="pending_items", clock=CLOCK)
    seen = {}
    real = pig.upsert_practice_item

    def checks_then_dies(root, payload, **kwargs):
        seen["identified"] = identity.is_generated_probe(repository, payload["id"])
        seen["item"] = payload["id"]
        real(root, payload, **kwargs)
        raise Died()

    monkeypatch.setattr(pig, "upsert_practice_item", checks_then_dies)
    with pytest.raises(Died):
        if via == "mint":
            pig.mint_single_use_probe_surface(repository, vault, episode.id, ai_client=FakeSurfacesClient(), clock=CLOCK)
        else:
            pig.generate_instances_for_episode(repository, vault, episode.id, ai_client=FakeSurfacesClient(), clock=CLOCK)
    assert seen["identified"] is True
    monkeypatch.setattr(pig, "upsert_practice_item", real)
    fresh = load_vault(paths.root)
    sync_vault_state(fresh, repository, clock=CLOCK)
    assert seen["item"] in fresh.practice_items and identity.is_generated_probe(repository, seen["item"])


# -- F4: abandonment and the burn's administration --------------------------------------------------


def _entry_probe(journey):
    """A generated probe with no workflow, and an episode it can be measured in."""

    from tests.followup_serve_helpers import generated_item

    item_id = "pi_entry_probe"
    generated_item(journey.paths.root, journey.repository, item_id, source="entry")
    journey.ctx.reload(maintenance=False)
    return item_id


def _session(ctx):
    return _call(ctx, "start_session", {"availableMinutes": 30})["sessionId"]


def test_f4_a_workflowless_probe_skipped_is_never_served_again(journey):
    ctx = journey.ctx
    item_id = _entry_probe(journey)
    session_id = _session(ctx)
    _call(ctx, "get_practice_item", {"practiceItemId": item_id, "sessionId": session_id})
    assert item_id in identity.closed_probe_ids(journey.repository)
    _call(ctx, "skip_practice_item", {"practiceItemId": item_id, "sessionId": session_id})
    assert item_id in identity.retired_probe_ids(journey.repository)
    assert not journey.repository.practice_item_state(item_id).active
    _refused(ctx, "open_queue_item", {"practiceItemId": item_id})
    _refused(ctx, "get_practice_item", {"practiceItemId": item_id, "sessionId": session_id})
    _refused(ctx, "get_probe_contract", {"practiceItemId": item_id, "sessionId": session_id})


def test_f4_skipping_one_the_plan_listed_abandons_it_unserved_too(journey):
    item_id = _entry_probe(journey)
    assert serving.abandon(journey.repository, item_id, clock=CLOCK)
    assert item_id in identity.retired_probe_ids(journey.repository)
    _refused(journey.ctx, "open_queue_item", {"practiceItemId": item_id})


def test_f4_a_skip_of_an_ordinary_item_changes_nothing(journey):
    assert not serving.abandon(journey.repository, SOURCE_ITEM, clock=CLOCK)


def _workflow_probe(journey):
    run_jobs(journey.vault, journey.repository, clients=author_clients(AuthorFake()))
    journey.ctx.reload(maintenance=False)
    return wf.get(journey.repository, journey.workflow_id)


def test_f4_the_burn_binds_to_the_open_presentation_and_ends_with_it(journey):
    ctx, repository = journey.ctx, journey.repository
    row = _workflow_probe(journey)
    item_id = row["practice_item_id"]
    _call(ctx, "open_queue_item", {"practiceItemId": item_id})
    burn = identity.closed_probe_ids(repository)
    assert item_id in burn
    with repository.connection() as connection:
        assert store.burns_for_item(connection, item_id)["served"]["presentation_id"] == row["presentation_id"]
    # The same administration re-opens with no id from its caller, while it stands.
    _call(ctx, "open_queue_item", {"practiceItemId": item_id})
    repository.end_probe_presentation(row["presentation_id"], end_reason="expired", clock=CLOCK)
    _refused(ctx, "open_queue_item", {"practiceItemId": item_id})
    _refused(ctx, "get_practice_item", {"practiceItemId": item_id, "sessionId": "s1"})


def test_f4_next_doesnt_offer_a_served_probe_whose_presentation_ended(journey):
    ctx, repository = journey.ctx, journey.repository
    row = _workflow_probe(journey)
    _call(ctx, "open_queue_item", {"practiceItemId": row["practice_item_id"]})
    repository.end_probe_presentation(row["presentation_id"], end_reason="invalidated", clock=CLOCK)
    assert _call(ctx, "followup_next", {"attemptId": journey.result.attempt_id})["action"] == "continue"
    settled = wf.get(repository, journey.workflow_id)
    assert settled["state"] == wf.SKIPPED and settled["feedback_released_at"]


def test_f4_the_claim_has_no_wildcard_for_a_missing_presentation(journey):
    item_id = _entry_probe(journey)
    repository = journey.repository
    assert identity.claim_serve(repository, item_id, surface="desktop", presentation_id="pp_1", clock=CLOCK).first
    missing = identity.claim_serve(repository, item_id, surface="desktop", presentation_id=None, clock=CLOCK)
    assert not missing.granted and missing.reason == identity.GENERATED_PROBE_CLOSED


def test_f4_a_burn_before_any_presentation_ends_when_one_has_ended(journey):
    item_id = _entry_probe(journey)
    repository = journey.repository
    assert identity.claim_serve(repository, item_id, surface="desktop", presentation_id=None, clock=CLOCK).first
    # A remount before anything was committed is the same administration.
    assert identity.claim_serve(repository, item_id, surface="desktop", presentation_id=None, clock=CLOCK).granted
    row = _workflow_probe(journey)
    with repository.atomic(), repository.connection() as connection:
        connection.execute("UPDATE probe_presentations SET practice_item_id = ? WHERE id = ?",
                           (item_id, row["presentation_id"]))
    assert identity.claim_serve(repository, item_id, surface="desktop", presentation_id=row["presentation_id"],
                                clock=CLOCK).granted
    repository.end_probe_presentation(row["presentation_id"], end_reason="abandoned", clock=CLOCK)
    for presentation in (None, row["presentation_id"], "pp_new"):
        assert not identity.claim_serve(repository, item_id, surface="desktop", presentation_id=presentation,
                                        clock=CLOCK).granted


# -- F5: exam text through a hypothesis; the owner's ruling of Nov 4 replaced this rule (test_followup_reserved_only.py) -------------------------------------------------------------


def test_f5_a_check_waiting_on_the_item_doesnt_stop_the_probe_lane(tmp_path, monkeypatch):
    real = learner_protection.withheld_items

    def withheld(vault_arg, repository_arg):
        seen = real(vault_arg, repository_arg)
        return learner_protection.Withheld(
            reasons={**seen.reasons, SOURCE_ITEM: learner_protection.WITHHELD_COLD}, available=True,
            known_items=seen.known_items, unknowns=seen.unknowns, exam=seen.exam,
        )

    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    monkeypatch.setattr(learner_protection, "withheld_items", withheld)
    fake = AuthorFake()
    run_jobs(vault, repository, clients=author_clients(fake))
    assert fake.calls == 1 and wf.get(repository, outcome.workflow_id)["state"] == wf.READY


# -- F6: the handoffs ------------------------------------------------------------------------------


def test_f6_a_crash_right_after_completion_still_has_the_job(tmp_path, monkeypatch):
    from learnloop.attempts import post_attempt
    from tests.causal_p2_acceptance_helpers import _divergent_failure

    vault, repository, _paths = rival_causes_vault(tmp_path)
    result = _divergent_failure(vault, repository, attempt_id="att_crash")

    def dies(*_a, **_k):
        raise Died()

    monkeypatch.setattr(post_attempt, "enqueue_post_attempt_learner_text", dies)
    with pytest.raises(Died):
        run_post_attempt_pipeline(vault, repository, result=result, followup_surface="desktop", clock=CLOCK)
    assert repository.attempt_completion("att_crash")["status"] == "completed"
    row = wf.attempt_workflow(repository, "att_crash")
    assert _job(repository, row["id"])["state"] == "queued"


def test_f6_a_crash_right_after_a_probe_answer_has_settled_its_workflow(journey, monkeypatch):
    from learnloop.attempts import post_attempt

    ctx, repository = journey.ctx, journey.repository
    row = _workflow_probe(journey)
    vault, _ = ctx.require_vault()
    _call(ctx, "open_queue_item", {"practiceItemId": row["practice_item_id"]})
    probe = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=row["practice_item_id"], learner_answer_md="An answer.",
                     attempt_type="diagnostic_probe", probe_presentation_id=row["presentation_id"]),
        SelfGradeInput(criterion_points={"fact_0": 0, "fact_1": 2}, confidence=3),
        clock=CLOCK,
    )

    def dies(*_a, **_k):
        raise Died()

    monkeypatch.setattr(post_attempt, "enqueue_post_attempt_learner_text", dies)
    with pytest.raises(Died):
        run_post_attempt_pipeline(vault, repository, result=probe, followup_surface="desktop", clock=CLOCK)
    settled = wf.get(repository, journey.workflow_id)
    assert settled["state"] == wf.SETTLED and settled["release_reason"] == wf.RELEASE_PROBE_ANSWERED


def test_f6_a_crash_after_the_diagnosis_ended_is_recovered_by_next(tmp_path, monkeypatch):
    _paths, vault, repository = split_vault(tmp_path, version=TAG)
    client = fake_client()
    result = submit(vault, repository, client, pipeline=False)
    outcome = run_post_attempt_pipeline(vault, repository, result=result, followup_surface="desktop", clock=CLOCK)
    monkeypatch.setattr(wf, "diagnosis_ended", lambda *_a, **_k: None)
    drain_jobs(vault, repository, client)
    assert _job(repository, outcome.workflow_id) is None  # the hook never ran
    action = serving.next_action(vault, repository, result.attempt_id, plan_serves=False, clock=CLOCK)
    assert action.action == "wait" and _job(repository, outcome.workflow_id)["state"] == "queued"
    # R9: this diagnosis names two causes, so the recovered job prepares a question.
    run_jobs(vault, repository, clients=author_clients(AuthorFake()))
    assert wf.get(repository, outcome.workflow_id)["state"] != wf.PENDING
    assert serving.next_action(load_vault(vault.root), repository, result.attempt_id, plan_serves=False,
                               clock=CLOCK).action == "open"


def test_f6_startup_recovery_needs_no_click(tmp_path, monkeypatch):
    _paths, vault, repository = split_vault(tmp_path, version=TAG)
    client = fake_client()
    result = submit(vault, repository, client, pipeline=False)
    outcome = run_post_attempt_pipeline(vault, repository, result=result, followup_surface="desktop", clock=CLOCK)
    # Still diagnosing: nothing to recover, so the ordered worker isn't overtaken.
    assert jobs.recover_pending_workflows(vault, repository, clock=CLOCK) == 0
    monkeypatch.setattr(wf, "diagnosis_ended", lambda *_a, **_k: None)
    drain_jobs(vault, repository, client)
    assert jobs.recover_pending_workflows(vault, repository, clock=CLOCK) == 1
    assert _job(repository, outcome.workflow_id)["state"] == "queued"
    assert jobs.recover_pending_workflows(vault, repository, clock=CLOCK) == 0  # idempotent


def test_f6_a_job_that_ended_with_its_workflow_pending_says_it_failed(journey):
    repository = journey.repository
    with repository.atomic(), repository.connection() as connection:
        connection.execute("UPDATE followup_generation_jobs SET state = 'done' WHERE workflow_id = ?",
                           (journey.workflow_id,))
    action = serving.next_action(journey.vault, repository, journey.result.attempt_id, plan_serves=False, clock=CLOCK)
    assert action.action == "continue"
    row = wf.get(repository, journey.workflow_id)
    assert row["state"] == wf.FAILED and row["release_reason"] == wf.RELEASE_GENERATION_FAILED


def test_f6_a_shadow_vault_has_its_workflows_job_at_once(tmp_path, monkeypatch):
    from learnloop.attempts import post_attempt
    from tests.causal_p2_acceptance_helpers import _divergent_failure

    vault, repository, _paths = rival_causes_vault(tmp_path)
    monkeypatch.setattr(post_attempt, "_shadow_diagnosis_enabled", lambda _vault: True)
    monkeypatch.setattr(post_attempt, "enqueue_post_attempt_diagnosis", lambda *_a, **_k: None)
    result = _divergent_failure(vault, repository, attempt_id="att_shadow")
    outcome = run_post_attempt_pipeline(vault, repository, result=result, followup_surface="desktop", clock=CLOCK)
    assert _job(repository, outcome.workflow_id)["state"] == "queued"


# -- F7: the switch off, with a probe already prepared --------------------------------------------


def _switched_off(journey):
    append_config_toml(journey.paths.root, OFF)
    ctx = SidecarContext()
    ctx.load(journey.paths.root)  # the reopen: startup maintenance settles it
    ctx.post_attempt_worker.autostart = False
    return ctx


def test_f7_a_prepared_probe_closes_with_the_switch(journey):
    row = _workflow_probe(journey)
    repository = journey.repository
    assert row["state"] == wf.READY
    ctx = _switched_off(journey)
    assert not generate_and_serve_on(ctx.require_vault()[0].config)
    settled = wf.get(repository, journey.workflow_id)
    assert settled["state"] == wf.SKIPPED and settled["release_reason"] == wf.RELEASE_SWITCH_OFF
    assert row["practice_item_id"] in identity.retired_probe_ids(repository)
    assert repository.probe_presentation(row["presentation_id"]).status == "ended"
    assert repository.probe_episode(row["probe_episode_id"]).status == "abandoned"
    assert not repository.practice_item_state(row["practice_item_id"]).active
    _refused(ctx, "open_queue_item", {"practiceItemId": row["practice_item_id"]})


def test_f7_a_served_probe_keeps_its_burn_after_the_rollback(journey):
    row = _workflow_probe(journey)
    repository = journey.repository
    _call(journey.ctx, "open_queue_item", {"practiceItemId": row["practice_item_id"]})
    ctx = _switched_off(journey)
    with repository.connection() as connection:
        assert set(store.burns_for_item(connection, row["practice_item_id"])) == {"served", "retired"}
    _refused(ctx, "open_queue_item", {"practiceItemId": row["practice_item_id"]})


def test_f7_a_standing_plan_doesnt_strand_next_on_a_switched_off_probe(tmp_path):
    env, _record = _env(tmp_path, fake_runtime())
    _ready(env)
    env.clock.advance(1)
    record, step = advance(env, serve=False)
    assert step["kind"] == "item" and step["practice_item_id"] == ITEM  # plan prefetch placed it
    assert not identity.closed_probe_ids(env.repository)

    append_config_toml(env.vault.root, OFF)
    off = load_vault(env.vault.root)
    env.vault = off
    assert wf.settle_open_when_off(off, env.repository, clock=env.clock) == 1
    assert ITEM in identity.retired_probe_ids(env.repository)
    env.clock.advance(1)
    record, step = advance(env, serve=False)
    assert step is None or step.get("practice_item_id") != ITEM
    planned = next(item for item in record.items() if item.practice_item_id == ITEM)
    assert planned.displaced_at is not None


def test_f7_next_through_the_sidecar_after_the_switch(tmp_path):
    env, _record = _env(tmp_path, fake_runtime())
    _ready(env)
    env.clock.advance(1)
    advance(env, serve=False)
    append_config_toml(env.vault.root, OFF)
    ctx = SidecarContext()
    ctx.load(env.vault.root)
    ctx.post_attempt_worker.autostart = False
    assert wf.get(env.repository, "fw_test")["state"] == wf.SKIPPED
    reply = _call(ctx, "next_plan_item", {"sessionId": env.session_id, "serve": True})
    assert reply["enabled"] is True
    assert (reply.get("step") or {}).get("practice_item_id") != ITEM
    assert ITEM not in identity.closed_probe_ids(env.repository) or ITEM in identity.retired_probe_ids(env.repository)


# -- F8: one decision per workflow -----------------------------------------------------------------


def _counting_decide(monkeypatch, *, chosen=router.ASK_NOW, seen=None):
    """A logged, plan-shaped decision each time it is asked, as the real one is."""

    calls = [] if seen is None else seen

    def decide(_vault, _repository, _row, **_kwargs):
        calls.append(1)
        picked = chosen if len(calls) == 1 else router.NO_INTERVENTION
        return router.FollowupDecision(picked, picked, "mixture", propensity=0.5, plan_id="plan_x", plan_kind="normal",
                                       local_date="2026-11-03", block_id="block_x")

    monkeypatch.setattr(router, "decide", decide)
    return calls


def _decisions(repository):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT id, chosen_ref, receipt_key FROM router_decisions WHERE decision_kind = 'plan_interrupt'")]


def test_f8_a_transport_failure_retries_under_the_decision_it_drew(tmp_path, monkeypatch):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    calls = _counting_decide(monkeypatch)
    down = AuthorFake(error=RuntimeError("provider down"))
    assert [job.state for job in run_jobs(vault, repository, clients=author_clients(down))] == ["retry"]
    first = wf.get(repository, outcome.workflow_id)
    assert first["chosen_ref"] == router.ASK_NOW and first["decision_id"]
    outcomes = run_jobs(vault, repository, clients=author_clients(AuthorFake()), clock=LATER)
    assert [job.state for job in outcomes] == ["done"]
    assert calls == [1]  # no fresh draw
    row = wf.get(repository, outcome.workflow_id)
    assert row["state"] == wf.READY and row["decision_id"] == first["decision_id"]
    assert row["chosen_ref"] == router.ASK_NOW
    assert [entry["id"] for entry in _decisions(repository)] == [first["decision_id"]]
    with repository.connection() as connection:
        bound = store.bindings_for_decision(connection, first["decision_id"])
    assert bound["item"]["practice_item_id"] == row["practice_item_id"]


def test_f8_a_crash_after_the_decision_keeps_it_through_the_lease_recovery(tmp_path, monkeypatch):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    calls = _counting_decide(monkeypatch, chosen=router.WAIT)

    class DiesWriting(AuthorFake):
        def run_followup_probe_authoring(self, context):
            raise Died()

    with pytest.raises(Died):
        jobs.process_next_job(vault, repository, owner="dead", clients=author_clients(DiesWriting()), clock=CLOCK)
    first = wf.get(repository, outcome.workflow_id)
    assert first["chosen_ref"] == router.WAIT and first["exposed_at"]
    run_jobs(vault, repository, clients=author_clients(AuthorFake()), clock=LATER)
    row = wf.get(repository, outcome.workflow_id)
    assert calls == [1] and row["state"] == wf.WAITING and row["decision_id"] == first["decision_id"]


def test_f8_a_no_plan_decision_is_kept_too(tmp_path, monkeypatch):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    down = AuthorFake(error=RuntimeError("provider down"))
    run_jobs(vault, repository, clients=author_clients(down))
    assert wf.get(repository, outcome.workflow_id)["chosen_ref"] == router.ASK_NOW

    def must_not_run(*_a, **_k):
        raise AssertionError("redrawn")

    monkeypatch.setattr(router, "decide", must_not_run)
    run_jobs(vault, repository, clients=author_clients(AuthorFake()), clock=LATER)
    assert wf.get(repository, outcome.workflow_id)["state"] == wf.READY


def test_f8_a_duplicate_receipt_resolves_to_the_decision_logged(tmp_path):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    row = wf.get(repository, outcome.workflow_id)
    fields = {"plan_id": "plan_x", "plan_kind": "normal", "local_date": "2026-11-03", "block_id": "block_x",
              "propensity": 0.5}
    first = router.record_decision(vault, repository, row, router.FollowupDecision(
        router.ASK_NOW, router.ASK_NOW, "mixture", **fields), clock=CLOCK)
    second = router.record_decision(vault, repository, row, router.FollowupDecision(
        router.NO_INTERVENTION, router.NO_INTERVENTION, "mixture", **fields), clock=CLOCK)
    assert first.decision_id and second.decision_id == first.decision_id
    assert second.chosen_ref == router.ASK_NOW and second.propensity == 0.5
    current = wf.get(repository, outcome.workflow_id)
    assert current["decision_id"] == first.decision_id and current["chosen_ref"] == router.ASK_NOW
    assert len(_decisions(repository)) == 1


def test_f8_naming_the_decision_commits_with_it(tmp_path, monkeypatch):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    row = wf.get(repository, outcome.workflow_id)
    fields = {"plan_id": "plan_x", "plan_kind": "normal", "local_date": "2026-11-03", "block_id": "block_x",
              "propensity": 0.5}
    real = store.update_workflow

    def dies(*_a, **_k):
        raise Died()

    monkeypatch.setattr(store, "update_workflow", dies)
    with pytest.raises(Died):
        router.record_decision(vault, repository, row, router.FollowupDecision(
            router.ASK_NOW, router.ASK_NOW, "mixture", **fields), clock=CLOCK)
    monkeypatch.setattr(store, "update_workflow", real)
    assert _decisions(repository) == []  # neither committed
    assert not wf.get(repository, outcome.workflow_id)["chosen_ref"]


# -- Shared by the review's tests ----------------------------------------------------------------


def _last_reason(repository, workflow_id):
    with repository.connection() as connection:
        return connection.execute(
            "SELECT reason FROM followup_workflow_events WHERE workflow_id = ? ORDER BY rowid DESC LIMIT 1", (workflow_id,),
        ).fetchone()[0]


def _rivals(repository, row):
    factor = repository.unresolved_cause_factors_for_attempt(row["source_attempt_id"])[0]
    return [str(value["hypothesis_id"]) for value in factor["candidate_causes"] if not value.get("open_set")]

# -- Re-review F7: a move and what it closes are one commit -------------------------------------------


_DOORS = {
    "switch_off": lambda journey, _row, clock: wf.settle_open_when_off(
        SimpleNamespace(config=load_vault(journey.paths.root).config), journey.repository, clock=clock),
    "retire_waiting": lambda journey, row, clock: wf.retire_waiting(
        journey.repository, row, reason="hypotheses_changed", clock=clock),
    "continue_without": lambda journey, _row, clock: serving.continue_without(
        journey.repository, journey.result.attempt_id, clock=clock),
    "abandon": lambda journey, row, clock: serving.abandon(
        journey.repository, row["practice_item_id"], clock=clock),
}


@pytest.mark.parametrize("door", sorted(_DOORS))
@pytest.mark.parametrize("dies_in", ["end_probe_presentation", "update_probe_episode_status"])
def test_f7_rereview_a_crash_in_cleanup_leaves_the_workflow_open_for_recovery(journey, monkeypatch, door, dies_in):
    row = _workflow_probe(journey)
    repository = journey.repository
    if door == "switch_off":
        append_config_toml(journey.paths.root, OFF)

    def dies(*_a, **_k):
        raise Died()

    real = getattr(repository, dies_in)
    monkeypatch.setattr(repository, dies_in, dies)
    with pytest.raises(Died):
        _DOORS[door](journey, row, CLOCK)
    monkeypatch.setattr(repository, dies_in, real)

    # Neither half stands: the workflow is what recovery reads, so it must still be open.
    after = wf.get(repository, journey.workflow_id)
    assert after["state"] == wf.READY and not after["feedback_released_at"]
    assert not identity.closed_probe_ids(repository)
    assert repository.practice_item_state(row["practice_item_id"]).active

    _DOORS[door](journey, row, CLOCK)  # the next startup, or the learner's next click
    after = wf.get(repository, journey.workflow_id)
    assert after["state"] == wf.SKIPPED
    assert row["practice_item_id"] in identity.retired_probe_ids(repository)
    assert not repository.practice_item_state(row["practice_item_id"]).active
    assert repository.probe_presentation(row["presentation_id"]).status == "ended"
    assert repository.probe_episode(row["probe_episode_id"]).status == "abandoned"


def test_f7_rereview_a_startup_crash_doesnt_leave_a_standing_plan_holding_the_item(tmp_path, monkeypatch):
    env, _record = _env(tmp_path, fake_runtime())
    _ready(env)
    env.clock.advance(1)
    advance(env, serve=False)
    append_config_toml(env.vault.root, OFF)
    off = load_vault(env.vault.root)
    env.vault = off

    def dies(*_a, **_k):
        raise Died()

    real = wf.close_probe
    monkeypatch.setattr(wf, "close_probe", dies)
    with pytest.raises(Died):
        wf.settle_open_when_off(off, env.repository, clock=env.clock)
    monkeypatch.setattr(wf, "close_probe", real)
    assert wf.settle_open_when_off(off, env.repository, clock=env.clock) == 1  # the terminal state didn't hide it
    assert ITEM in identity.retired_probe_ids(env.repository)
    env.clock.advance(1)
    record, _step = advance(env, serve=False)
    assert next(item for item in record.items() if item.practice_item_id == ITEM).displaced_at is not None


def test_f7_rereview_continue_without_commits_its_preference_and_outcome_with_the_move(tmp_path, monkeypatch):
    from learnloop.db.stores import followup_serve

    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    _counting_decide(monkeypatch)
    run_jobs(vault, repository, clients=author_clients(AuthorFake()))
    row = wf.get(repository, outcome.workflow_id)

    def dies(*_a, **_k):
        raise Died()

    real = followup_serve.append_binding
    monkeypatch.setattr(followup_serve, "append_binding", dies)
    with pytest.raises(Died):
        serving.continue_without(repository, row["source_attempt_id"], clock=CLOCK)
    monkeypatch.setattr(followup_serve, "append_binding", real)
    assert wf.get(repository, outcome.workflow_id)["state"] == wf.READY
    assert serving.continue_without(repository, row["source_attempt_id"], clock=CLOCK)
    with repository.connection() as connection:
        assert store.bindings_for_decision(connection, row["decision_id"])["outcome"]["outcome"] == "skipped"


def test_f7_rereview_skipping_a_workflows_probe_through_the_sidecar_closes_it(journey):
    """The workflow branch of ``abandon`` read a name its module didn't have, so this skip raised."""

    row = _workflow_probe(journey)
    ctx = journey.ctx
    session_id = _session(ctx)
    _call(ctx, "skip_practice_item", {"practiceItemId": row["practice_item_id"], "sessionId": session_id})
    after = wf.get(journey.repository, journey.workflow_id)
    assert after["state"] == wf.SKIPPED and after["feedback_released_at"]
    assert row["practice_item_id"] in identity.retired_probe_ids(journey.repository)
    assert journey.repository.causal_probe_candidate(row["probe_candidate_id"])["status"] == "rejected"
    _refused(ctx, "open_queue_item", {"practiceItemId": row["practice_item_id"]})


# -- Re-review F9: a recorded decision doesn't outrank a refusal that came after it ---------------


def _not_now(repository, factor_id, session_id):
    from learnloop.diagnosis.causal_orchestrator import record_learner_preference

    record_learner_preference(repository, preference="decline", factor_id=factor_id, session_id=session_id,
                              source="learner_action", clock=CLOCK)


def _blocking_check(repository, factor_id):
    from learnloop.diagnosis.causal_orchestrator import MACHINE_CHECK_REPAIR_MAPPING

    repository.enqueue_causal_machine_check(check_id="mc_blocks", kind=MACHINE_CHECK_REPAIR_MAPPING, payload={},
                                            source="test", factor_id=factor_id, clock=CLOCK)


@pytest.mark.parametrize("arrives, reason", [("not_now", "learner_decline"), ("check", "pending_machine_checks")])
@pytest.mark.parametrize("drawn", [router.ASK_NOW, router.WAIT])
def test_f9_a_retry_rechecks_the_hard_refusals_and_keeps_the_draw(tmp_path, monkeypatch, arrives, reason, drawn):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    calls = _counting_decide(monkeypatch, chosen=drawn)
    down = AuthorFake(error=RuntimeError("provider down"))
    assert [job.state for job in run_jobs(vault, repository, clients=author_clients(down))] == ["retry"]
    first = wf.get(repository, outcome.workflow_id)
    assert first["chosen_ref"] == drawn and first["decision_id"] and first["factor_id"]
    if arrives == "not_now":
        _not_now(repository, first["factor_id"], first["session_id"])
    else:
        _blocking_check(repository, first["factor_id"])

    fake = AuthorFake()
    assert [job.state for job in run_jobs(vault, repository, clients=author_clients(fake), clock=LATER)] == ["done"]
    assert fake.calls == 0 and calls == [1]  # no request, no fresh draw
    row = wf.get(repository, outcome.workflow_id)
    assert row["state"] == wf.REFUSED and _last_reason(repository, outcome.workflow_id) == reason
    assert row["feedback_released_at"]
    # The draw stands as drawn; what happened to it is an outcome against that decision.
    assert row["chosen_ref"] == drawn and row["decision_id"] == first["decision_id"]
    logged = _decisions(repository)
    assert [(entry["id"], entry["chosen_ref"]) for entry in logged] == [(first["decision_id"], drawn)]
    with repository.connection() as connection:
        assert store.bindings_for_decision(connection, first["decision_id"])["outcome"]["outcome"] == "refused"
    assert identity.generated_probe_ids(repository) == frozenset()


def test_f9_a_no_plan_retry_is_refused_too(tmp_path):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    run_jobs(vault, repository, clients=author_clients(AuthorFake(error=RuntimeError("provider down"))))
    first = wf.get(repository, outcome.workflow_id)
    assert first["chosen_ref"] == router.ASK_NOW and not first["decision_id"]
    _not_now(repository, first["factor_id"], first["session_id"])
    fake = AuthorFake()
    run_jobs(vault, repository, clients=author_clients(fake), clock=LATER)
    assert fake.calls == 0 and wf.get(repository, outcome.workflow_id)["state"] == wf.REFUSED


def test_f9_a_refusal_that_arrives_during_authoring_stops_the_offer(tmp_path):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)

    class LearnerSaysNotNow(AuthorFake):
        def run_followup_probe_authoring(self, context):
            row = wf.get(repository, outcome.workflow_id)
            _not_now(repository, row["factor_id"], row["session_id"])
            return super().run_followup_probe_authoring(context)

    fake = LearnerSaysNotNow()
    run_jobs(vault, repository, clients=author_clients(fake))
    assert fake.calls == 1
    row = wf.get(repository, outcome.workflow_id)
    assert row["state"] == wf.REFUSED and _last_reason(repository, outcome.workflow_id) == "learner_decline"
    assert not row["practice_item_id"] and not row["presentation_id"]
    assert not identity.generated_probe_ids(repository) - identity.retired_probe_ids(repository)


def test_f9_a_refused_retry_doesnt_leave_what_the_crash_pinned(journey, monkeypatch):
    first = _crash_after_the_pin(journey, monkeypatch)
    repository = journey.repository
    row = wf.get(repository, journey.workflow_id)
    _not_now(repository, row["factor_id"], row["session_id"])
    fake = AuthorFake()
    run_jobs(load_vault(journey.paths.root), repository, clients=author_clients(fake), clock=LATER)
    assert fake.calls == 0
    assert wf.get(repository, journey.workflow_id)["state"] == wf.REFUSED
    assert first.practice_item_id in identity.retired_probe_ids(repository)
    assert repository.probe_presentation(first.presentation_id).status == "ended"
    assert repository.causal_probe_candidate(first.candidate_id)["status"] == "rejected"


# -- Re-review F10: a withdrawal finishes, whatever interrupts it -----------------------------------


def _crash_after_the_pin(journey, monkeypatch, fake=None):
    from learnloop.followup_run import admission

    repository = journey.repository
    real = admission.commission_and_pin
    pinned = {}

    def pins_then_dies(*args, **kwargs):
        pinned["admitted"] = real(*args, **kwargs)
        raise Died()

    monkeypatch.setattr(admission, "commission_and_pin", pins_then_dies)
    with pytest.raises(Died):
        jobs.process_next_job(journey.vault, repository, owner="dead", clients=author_clients(fake or AuthorFake()),
                              clock=CLOCK)
    monkeypatch.setattr(admission, "commission_and_pin", real)
    sync_vault_state(load_vault(journey.paths.root), repository, clock=CLOCK)
    return pinned["admitted"]


@pytest.mark.parametrize("dies_in", ["end_probe_presentation", "update_causal_probe_candidate"])
def test_f10_an_interrupted_withdrawal_is_redone_whole(journey, monkeypatch, dies_in):
    fake = AuthorFake()  # one author, so the retry's question is a new one
    first = _crash_after_the_pin(journey, monkeypatch, fake)
    repository = journey.repository

    def dies(*_a, **_k):
        raise Died()

    real = getattr(repository, dies_in)
    monkeypatch.setattr(repository, dies_in, dies)
    with pytest.raises(Died):
        identity.retire_unbound(repository, journey.workflow_id, clock=CLOCK)
    monkeypatch.setattr(repository, dies_in, real)
    # All of it rolled back, so the next recovery still selects this item.
    assert first.practice_item_id not in identity.closed_probe_ids(repository)
    assert repository.causal_probe_candidate(first.candidate_id)["status"] == "active"

    outcomes = run_jobs(load_vault(journey.paths.root), repository, clients=author_clients(fake), clock=LATER)
    assert [job.state for job in outcomes] == ["done"]
    row = wf.get(repository, journey.workflow_id)
    # The replacement commissioned: no duplicate_instrument_class against the leftover.
    assert row["state"] == wf.READY and row["practice_item_id"] != first.practice_item_id
    assert first.practice_item_id in identity.retired_probe_ids(repository)
    assert repository.probe_presentation(first.presentation_id).status == "ended"
    assert repository.causal_probe_candidate(first.candidate_id)["status"] == "rejected"


def test_f10_recovery_redoes_a_withdrawal_a_crash_cut_at_the_job_boundary(journey, monkeypatch):
    first = _crash_after_the_pin(journey, monkeypatch)
    repository = journey.repository
    real = repository.update_causal_probe_candidate

    def dies(*_a, **_k):
        raise Died()

    monkeypatch.setattr(repository, "update_causal_probe_candidate", dies)
    with pytest.raises(Died):
        jobs.process_next_job(load_vault(journey.paths.root), repository, owner="dead2",
                              clients=author_clients(AuthorFake()), clock=LATER)
    monkeypatch.setattr(repository, "update_causal_probe_candidate", real)
    assert repository.causal_probe_candidate(first.candidate_id)["status"] == "active"
    identity.retire_unbound(repository, journey.workflow_id, clock=LATER)
    assert repository.causal_probe_candidate(first.candidate_id)["status"] == "rejected"
    assert repository.probe_presentation(first.presentation_id).status == "ended"


def test_f10_a_closed_probes_candidate_leaves_the_factors_active_set(journey):
    """Serving accepts only ``active`` candidates, so a retired probe's mustn't stay one: the
    predecessor's offer would pin a question every door refuses, after the switch goes off."""

    from learnloop.diagnosis.causal_orchestrator import accept_probe_offer

    row = _workflow_probe(journey)
    repository = journey.repository
    ctx = _switched_off(journey)
    assert repository.causal_probe_candidate(row["probe_candidate_id"])["status"] == "rejected"
    vault, _repository = ctx.require_vault()
    offer = accept_probe_offer(vault, repository, factor_id=row["factor_id"], decision_receipt_id=None, clock=LATER)
    assert not offer.accepted and offer.reason == "no_reviewed_active_candidate"


def test_f10_a_failed_workflow_withdraws_what_its_last_run_left(journey, monkeypatch):
    first = _crash_after_the_pin(journey, monkeypatch)
    repository = journey.repository
    jobs.fail_workflow(journey.vault, repository, journey.workflow_id, reason="generation_job_ended", clock=LATER)
    assert wf.get(repository, journey.workflow_id)["state"] == wf.FAILED
    assert first.practice_item_id in identity.retired_probe_ids(repository)
    assert repository.causal_probe_candidate(first.candidate_id)["status"] == "rejected"


# -- Final verify (job 20261104-030053-ASNG4N), F7: ruling R1, one function for every terminal move ---


TERMINAL_NAMES = {"REFUSED", "FAILED", "SKIPPED", "SETTLED"}


def _newer_grade(repository, attempt_id):
    repository.insert_blind_grade_record(
        attempt_id=attempt_id, agent_run_id=None, grading_prompt_version="test", output_schema_version="test",
        context_hash="newer", record={"grade": "newer"}, queue_diagnosis=False, clock=LATER,
    )


def _nothing_left_open(repository, first, *, episode=True):
    """What every exit owes: no burn or retirement missing, no state, candidate or pin left live."""

    item = first.practice_item_id
    assert item in identity.retired_probe_ids(repository)
    assert not repository.practice_item_state(item).active
    assert repository.causal_probe_candidate(first.candidate_id)["status"] == "rejected"
    assert repository.probe_presentation(first.presentation_id).status == "ended"
    assert repository.active_probe_presentation_for_item(item) is None
    if episode:
        assert repository.probe_episode(first.episode_id).status == "abandoned"


def _exit_newer_grade(journey, monkeypatch):
    _newer_grade(journey.repository, journey.result.attempt_id)
    run_jobs(load_vault(journey.paths.root), journey.repository, clients=author_clients(AuthorFake()), clock=LATER)
    return wf.SKIPPED, "newer_grade"


def _exit_cause_matches_reserved(journey, monkeypatch):
    from learnloop.followup_run import authoring

    monkeypatch.setattr(authoring, "causes_match_reserved", lambda *_a, **_k: True)
    run_jobs(load_vault(journey.paths.root), journey.repository, clients=author_clients(AuthorFake()), clock=LATER)
    return wf.SETTLED, authoring.CAUSE_MATCHES_RESERVED


def _exit_one_hypothesis(journey, monkeypatch):
    from learnloop.followup_run import lanes

    monkeypatch.setattr(lanes, "select_lane", lambda *_a, **_k: lanes.LaneChoice(wf.LANE_PRACTICE, "one_hypothesis"))
    run_jobs(load_vault(journey.paths.root), journey.repository, clients=author_clients(AuthorFake()), clock=LATER)
    return wf.SETTLED, "one_hypothesis"


def _exit_timeout(journey, _monkeypatch):
    from learnloop.followup_run import lanes

    row = wf.get(journey.repository, journey.workflow_id)
    lanes.settle_practice_lane(journey.vault, journey.repository, row, reason="diagnosis_timeout",
                               release=wf.RELEASE_FALLBACK, clock=LATER)
    return wf.SETTLED, "diagnosis_timeout"


def _exit_refused(journey, _monkeypatch):
    row = wf.get(journey.repository, journey.workflow_id)
    _not_now(journey.repository, row["factor_id"], row["session_id"])
    run_jobs(load_vault(journey.paths.root), journey.repository, clients=author_clients(AuthorFake()), clock=LATER)
    return wf.REFUSED, "learner_decline"


def _exit_no_intervention(journey, _monkeypatch):
    wf.set_fields(journey.repository, journey.workflow_id, chosen_ref=router.NO_INTERVENTION, clock=LATER)
    run_jobs(load_vault(journey.paths.root), journey.repository, clients=author_clients(AuthorFake()), clock=LATER)
    return wf.SETTLED, "no_intervention"


def _exit_failed(journey, _monkeypatch):
    jobs.fail_workflow(journey.vault, journey.repository, journey.workflow_id, reason="generation_job_ended", clock=LATER)
    return wf.FAILED, "generation_job_ended"


def _exit_continue_without(journey, _monkeypatch):
    serving.continue_without(journey.repository, journey.result.attempt_id, clock=LATER)
    return wf.SKIPPED, "continue_without_it"


_EXITS = {
    "newer_grade": _exit_newer_grade,
    "cause_matches_reserved": _exit_cause_matches_reserved,
    "one_hypothesis": _exit_one_hypothesis,
    "diagnosis_timeout": _exit_timeout,
    "refused": _exit_refused,
    "no_intervention": _exit_no_intervention,
    "failed": _exit_failed,
    "continue_without": _exit_continue_without,
}


@pytest.mark.parametrize("name", sorted(_EXITS))
def test_f7_verify_every_exit_closes_what_an_interrupted_run_prepared(journey, monkeypatch, name):
    """Codex's two reproductions (newer grade, the settled exit before the probe lane), and every other way out."""

    first = _crash_after_the_pin(journey, monkeypatch)
    repository = journey.repository
    assert repository.probe_presentation(first.presentation_id).status == "selected"
    state, reason = _EXITS[name](journey, monkeypatch)
    row = wf.get(repository, journey.workflow_id)
    assert row["state"] == state and _last_reason(repository, journey.workflow_id) == reason
    assert row["feedback_released_at"]
    assert row["practice_item_id"] is None  # it was never bound: nothing but the ledger could find it
    _nothing_left_open(repository, first)
    # Nothing recovers a terminal workflow, so this is the last word; Next goes on.
    assert not jobs.recover_workflow(journey.vault, repository, row, clock=LATER)
    assert serving.next_action(journey.vault, repository, journey.result.attempt_id, plan_serves=False,
                               clock=LATER).action == "continue"


@pytest.mark.parametrize("name", ["newer_grade", "cause_matches_reserved"])
@pytest.mark.parametrize("dies_in", ["end_probe_presentation", "update_causal_probe_candidate",
                                     "update_probe_episode_status"])
def test_f7_verify_a_crash_in_the_exit_leaves_all_of_it_open_for_the_next_run(journey, monkeypatch, name, dies_in):
    first = _crash_after_the_pin(journey, monkeypatch)
    repository = journey.repository

    def dies(*_a, **_k):
        raise Died()

    real = getattr(repository, dies_in)
    monkeypatch.setattr(repository, dies_in, dies)
    with pytest.raises(Died):
        _EXITS[name](journey, monkeypatch)
    monkeypatch.setattr(repository, dies_in, real)
    row = wf.get(repository, journey.workflow_id)
    assert row["state"] == wf.PENDING and not row["feedback_released_at"]
    assert first.practice_item_id not in identity.retired_probe_ids(repository)

    run_jobs(load_vault(journey.paths.root), repository, clients=author_clients(AuthorFake()),
             clock=FrozenClock(LATER.now() + timedelta(hours=2)))
    assert wf.get(repository, journey.workflow_id)["state"] in store.TERMINAL_STATES
    _nothing_left_open(repository, first)


def test_f7_verify_the_settled_exit_adds_no_question_of_its_own(journey, monkeypatch):
    first = _crash_after_the_pin(journey, monkeypatch)
    repository = journey.repository
    from learnloop.followup_run import authoring

    fake = AuthorFake()
    monkeypatch.setattr(authoring, "causes_match_reserved", lambda *_a, **_k: True)
    run_jobs(load_vault(journey.paths.root), repository, clients=author_clients(fake), clock=LATER)
    assert fake.calls == 0
    assert identity.generated_probe_ids(repository) == {first.practice_item_id}


def test_f7_verify_an_answer_keeps_its_own_question_and_closes_only_the_leftovers(journey):
    row = _workflow_probe(journey)
    repository = journey.repository
    identity.register(repository, practice_item_id="pi_gen_left_behind", revision="r", source="workflow",
                      workflow_id=journey.workflow_id, clock=CLOCK)
    assert wf.probe_answered(repository, row["practice_item_id"], attempt_id="att_probe", clock=LATER)
    assert wf.get(repository, journey.workflow_id)["state"] == wf.SETTLED
    retired = identity.retired_probe_ids(repository)
    assert "pi_gen_left_behind" in retired and row["practice_item_id"] not in retired
    assert repository.probe_presentation(row["presentation_id"]).status != "ended"
    assert repository.probe_episode(row["probe_episode_id"]).status == "in_progress"


def test_f7_verify_an_episode_another_presentation_still_holds_stays_open(journey, monkeypatch):
    row = _workflow_probe(journey)
    repository = journey.repository
    monkeypatch.setattr(repository, "probe_presentations_for_episode",
                        lambda _episode_id: [SimpleNamespace(status="selected")])
    serving.continue_without(repository, journey.result.attempt_id, clock=LATER)
    assert wf.get(repository, journey.workflow_id)["state"] == wf.SKIPPED
    assert repository.probe_episode(row["probe_episode_id"]).status == "in_progress"


def test_f7_verify_a_late_generator_closes_the_episode_it_pinned(tmp_path):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)

    class SkipsMidway(AuthorFake):
        def run_followup_probe_authoring(self, context):
            serving_row = wf.get(repository, outcome.workflow_id)
            assert wf.finish(repository, serving_row["id"], to_state=wf.SKIPPED, reason="continue_without_it",
                             release=wf.RELEASE_CONTINUE_WITHOUT, clock=CLOCK)
            return super().run_followup_probe_authoring(context)

    run_jobs(vault, repository, clients=author_clients(SkipsMidway()))
    generated = identity.generated_probe_ids(repository)
    assert len(generated) == 1 and generated <= identity.retired_probe_ids(repository)
    with repository.connection() as connection:
        episodes = [row[0] for row in connection.execute(
            "SELECT DISTINCT probe_episode_id FROM probe_presentations WHERE practice_item_id = ?", (next(iter(generated)),))]
    assert episodes and all(repository.probe_episode(value).status == "abandoned" for value in episodes)


def test_f7_verify_move_refuses_a_terminal_state_and_finish_refuses_any_other(journey):
    for state in store.TERMINAL_STATES:
        with pytest.raises(ValueError):
            wf.move(journey.repository, journey.workflow_id, to_state=state, reason="test", clock=CLOCK)
    with pytest.raises(ValueError):
        wf.finish(journey.repository, journey.workflow_id, to_state=wf.READY, reason="test", clock=CLOCK)
    assert wf.get(journey.repository, journey.workflow_id)["state"] == wf.PENDING


def _terminal_state_writers(source: str, *, relative: str) -> list[str]:
    """Every place in this module that could write a terminal state without :func:`workflow.finish`."""

    import ast
    import re

    found: list[str] = []
    tree = ast.parse(source)

    def is_store_module() -> bool:
        return relative == "learnloop/db/stores/followup_serve.py"

    def is_workflow_module() -> bool:
        return relative == "learnloop/followup_serve/workflow.py"

    def constants(value: ast.AST) -> list[str | None]:
        """The states this expression can name; None for one it doesn't spell out."""

        if isinstance(value, ast.IfExp):
            return constants(value.body) + constants(value.orelse)
        if isinstance(value, ast.Attribute):
            return [value.attr]
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            return [value.value.upper()]
        return [None]

    owners: dict[ast.AST, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for child in ast.walk(node):
                owners.setdefault(child, node.name) if child is not node else None

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", None)
            keywords = {keyword.arg: keyword.value for keyword in node.keywords}
            if name == "move" and "to_state" in keywords:
                for state in constants(keywords["to_state"]):
                    if state is None or state in TERMINAL_NAMES:
                        found.append(f"{relative}:{node.lineno} move to {state}")
            if name == "_apply_move" and not (is_workflow_module() and owners.get(node) in {"move", "finish"}):
                found.append(f"{relative}:{node.lineno} _apply_move")
        if isinstance(node, (ast.Name, ast.Attribute)):
            name = node.attr if isinstance(node, ast.Attribute) else node.id
            if name == "move_workflow" and not (is_workflow_module() and owners.get(node) == "_apply_move"):
                found.append(f"{relative}:{node.lineno} move_workflow")
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value
            if re.search(r"UPDATE\s+followup_workflows\s+SET\s[^;]*\bstate\s*=", text, re.I) and not (
                    is_store_module() and owners.get(node) == "move_workflow"):
                found.append(f"{relative}:{node.lineno} UPDATE of state")
            if re.search(r"(INSERT|REPLACE)\s+(OR\s+\w+\s+)?INTO\s+followup_workflows\b", text, re.I) and not (
                    is_store_module() and owners.get(node) == "insert_workflow"):
                found.append(f"{relative}:{node.lineno} INSERT")
    return found


def test_f7_verify_no_other_writer_of_a_terminal_state():
    """R1. Anything else that writes one fails here; ``move`` also refuses a terminal state when it runs."""

    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "src"
    found: list[str] = []
    for path in sorted(root.rglob("*.py")):
        found += _terminal_state_writers(path.read_text(encoding="utf-8"), relative=path.relative_to(root).as_posix())
    assert found == []
    # The one UPDATE that could spell a state through its fields can't.
    assert "state" not in store.WORKFLOW_FIELDS
    assert not store.TERMINAL_STATES & store.OPEN_STATES


@pytest.mark.parametrize("source", [
    "wf.move(r, i, to_state=wf.SKIPPED, reason='x')",
    "WF.move(r, i, to_state=WF.SETTLED, reason='x')",
    "followup_workflow.move(r, i, to_state=followup_workflow.FAILED, reason='x')",
    "move(r, i, to_state='refused', reason='x')",
    "wf.move(r, i, to_state=whichever, reason='x')",
    "wf.move(r, i, to_state=wf.READY if a else wf.REFUSED, reason='x')",
    "wf._apply_move(r, i, to_state=wf.READY, reason='x')",
    "store.move_workflow(c, i, from_states=(), to_state='failed', reason='x', at='t')",
    "c.execute('UPDATE followup_workflows SET state = ? WHERE id = ?', a)",
    "c.execute('update followup_workflows set lane = ?, state = ? where id = ?', a)",
    "c.execute('INSERT OR REPLACE INTO followup_workflows (state) VALUES (?)', a)",
])
def test_f7_verify_the_scan_catches_each_kind_of_writer(source):
    assert _terminal_state_writers(source, relative="learnloop/elsewhere.py")


@pytest.mark.parametrize("source", [
    "wf.move(r, i, to_state=wf.READY, reason='x')",
    "wf.move(r, i, to_state=wf.WAITING if a else wf.READY, reason='x')",
    "shutil.move(a, b)",
    "c.execute('UPDATE followup_workflows SET lane = ? WHERE id = ?', a)",
])
def test_f7_verify_the_scan_leaves_what_isnt_a_writer(source):
    assert _terminal_state_writers(source, relative="learnloop/elsewhere.py") == []


# -- Final verify, F9: ruling R2, the blocking-check lookup gets the workflow's learning object -------


def _blocking_check_on_the_object(repository, learning_object_id):
    from learnloop.diagnosis.causal_orchestrator import MACHINE_CHECK_REPAIR_MAPPING

    repository.enqueue_causal_machine_check(check_id="mc_blocks_object", kind=MACHINE_CHECK_REPAIR_MAPPING, payload={},
                                            source="test", learning_object_id=learning_object_id, clock=CLOCK)


def test_f9_verify_a_retry_is_refused_by_a_check_on_the_whole_learning_object(tmp_path):
    """Codex's reproduction: the check names the object and no factor, and the retry reached authoring."""

    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    run_jobs(vault, repository, clients=author_clients(AuthorFake(error=RuntimeError("provider down"))))
    first = wf.get(repository, outcome.workflow_id)
    assert first["chosen_ref"] == router.ASK_NOW and first["factor_id"]
    _blocking_check_on_the_object(repository, first["learning_object_id"])

    fake = AuthorFake()
    run_jobs(vault, repository, clients=author_clients(fake), clock=LATER)
    assert fake.calls == 0
    assert wf.get(repository, outcome.workflow_id)["state"] == wf.REFUSED
    assert _last_reason(repository, outcome.workflow_id) == "pending_machine_checks"
    assert not identity.generated_probe_ids(repository)


def test_f9_verify_a_check_on_the_object_that_arrives_during_authoring_stops_the_offer(tmp_path):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)

    class CheckArrives(AuthorFake):
        def run_followup_probe_authoring(self, context):
            _blocking_check_on_the_object(repository, wf.get(repository, outcome.workflow_id)["learning_object_id"])
            return super().run_followup_probe_authoring(context)

    fake = CheckArrives()
    run_jobs(vault, repository, clients=author_clients(fake))
    assert fake.calls == 1
    row = wf.get(repository, outcome.workflow_id)
    assert row["state"] == wf.REFUSED and not row["practice_item_id"] and not row["presentation_id"]
    assert _last_reason(repository, outcome.workflow_id) == "pending_machine_checks"
    assert not identity.generated_probe_ids(repository) - identity.retired_probe_ids(repository)


def test_f9_verify_a_check_on_another_object_or_of_a_non_blocking_kind_refuses_nothing(tmp_path):
    from learnloop.diagnosis.causal_orchestrator import MACHINE_CHECK_INSTRUMENT_COMMISSIONING

    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    row = wf.get(repository, outcome.workflow_id)
    _blocking_check_on_the_object(repository, "lo_some_other_topic")
    repository.enqueue_causal_machine_check(check_id="mc_debt", kind=MACHINE_CHECK_INSTRUMENT_COMMISSIONING, payload={},
                                            source="test", learning_object_id=row["learning_object_id"], clock=CLOCK)
    fake = AuthorFake()
    run_jobs(vault, repository, clients=author_clients(fake))
    assert fake.calls == 1 and wf.get(repository, outcome.workflow_id)["state"] == wf.READY
