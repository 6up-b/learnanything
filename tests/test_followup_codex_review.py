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

from tests.daily_plan_fakes import record_attempt
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
from tests.test_causal_p2_acceptance import LO_ID, SOURCE_ITEM
from tests.test_followup_router import ITEM, _env, _gate, _ready, _workflow
from tests.test_probe_surface_mint import FakeSurfacesClient

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


# -- F5: exam text through a hypothesis -------------------------------------------------------------


def _exam_material(monkeypatch, item_id=SOURCE_ITEM):
    real = learner_protection.withheld_items

    def withheld(vault_arg, repository_arg):
        seen = real(vault_arg, repository_arg)
        return learner_protection.Withheld(
            reasons={**seen.reasons, item_id: learner_protection.WITHHELD_EXAM}, available=True,
            known_items=seen.known_items, unknowns=seen.unknowns, exam=seen.exam,
        )

    monkeypatch.setattr(learner_protection, "withheld_items", withheld)


def test_f5_a_cause_written_from_exam_work_reaches_neither_request(tmp_path, monkeypatch):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    _exam_material(monkeypatch)
    real_hypothesis = repository.causal_hypothesis

    def quoting(hypothesis_id):
        # What a diagnoser writes from an exam answer: the question's own matrix, in its words.
        found = real_hypothesis(hypothesis_id)
        return {**found, "statement": f"Believes {SENTINEL} is invertible"} if found else found

    monkeypatch.setattr(repository, "causal_hypothesis", quoting)
    fake = AuthorFake()
    facts = []
    real_facts = router._card_facts
    monkeypatch.setattr(router, "_card_facts", lambda *args: facts.extend(real_facts(*args)) or facts)
    outcomes = run_jobs(vault, repository, clients=author_clients(fake))
    assert SENTINEL not in repr(fake.contexts) and SENTINEL not in repr(facts)
    assert [job.state for job in outcomes] == ["done"]
    assert fake.calls == 0
    row = wf.get(repository, outcome.workflow_id)
    # Not a failure: the practice lane, with what was held released and Next going on.
    assert row["state"] == wf.SETTLED and row["lane"] == wf.LANE_PRACTICE and row["feedback_released_at"]
    assert row["settled_reason"] is None or "exam" in str(row["settled_reason"])
    assert identity.generated_probe_ids(repository) == frozenset()


def test_f5_the_author_builder_itself_refuses_them_for_entry_and_need_work(tmp_path, monkeypatch):
    from learnloop.followup_run import admission

    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    row = wf.get(repository, outcome.workflow_id)
    factor = repository.unresolved_cause_factors_for_attempt(row["source_attempt_id"])[0]
    _exam_material(monkeypatch)
    fake = AuthorFake()
    clients = author_clients(fake)
    with pytest.raises(admission.AdmissionFailed) as caught:
        admission.author_probe(vault, repository, workflow=row, factor_id=str(factor["id"]),
                               decision={"chosen": "background", "timing": "later"}, client=clients.author)
    assert caught.value.reason == "causes_from_exam_material"
    assert fake.calls == 0


def test_f5_exam_attempt_work_is_exam_material_whatever_its_item(tmp_path):
    from learnloop.followup_run.authoring import hypotheses_exam_reason

    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    row = wf.get(repository, outcome.workflow_id)
    factor = repository.unresolved_cause_factors_for_attempt(row["source_attempt_id"])[0]
    ids = [str(value["hypothesis_id"]) for value in factor["candidate_causes"] if not value.get("open_set")]
    assert hypotheses_exam_reason(vault, repository, ids) is None
    with repository.connection() as connection:
        connection.execute("UPDATE practice_attempts SET attempt_type = 'exam_attempt' WHERE id = ?",
                           (row["source_attempt_id"],))
        connection.commit()
    assert hypotheses_exam_reason(vault, repository, ids) == learner_protection.WITHHELD_EXAM


def test_f5_what_the_writer_recorded_reading_counts(tmp_path, monkeypatch):
    from learnloop.db.stores import write_provenance
    from learnloop.followup_run.authoring import hypotheses_exam_reason

    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    row = wf.get(repository, outcome.workflow_id)
    factor = repository.unresolved_cause_factors_for_attempt(row["source_attempt_id"])[0]
    ids = [str(value["hypothesis_id"]) for value in factor["candidate_causes"] if not value.get("open_set")]
    _exam_material(monkeypatch, "pi_an_exam_question")
    assert hypotheses_exam_reason(vault, repository, ids) is None
    read_exam = SimpleNamespace(record=SimpleNamespace(inputs=write_provenance.Inputs(items=frozenset({"pi_an_exam_question"}))))
    monkeypatch.setattr(write_provenance, "stored_record", lambda *_a, **_k: read_exam)
    assert hypotheses_exam_reason(vault, repository, ids) == learner_protection.WITHHELD_EXAM


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
    from tests.test_causal_p2_acceptance import _divergent_failure

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
    run_jobs(vault, repository)
    assert wf.get(repository, outcome.workflow_id)["state"] != wf.PENDING
    assert serving.next_action(vault, repository, result.attempt_id, plan_serves=False, clock=CLOCK).action == "continue"


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
    from tests.test_causal_p2_acceptance import _divergent_failure

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
