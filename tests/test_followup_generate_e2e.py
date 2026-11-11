"""FG1 §4.1, §5.1, §10: a miss with two rivals leads to one generated item, admitted by machine."""

from __future__ import annotations

from learnloop.diagnosis.causal_orchestrator import pinned_causal_probe
from learnloop.followup_serve import identity, workflow as wf

from tests.followup_serve_helpers import AuthorFake, author_clients, CLOCK, miss_with_rivals, rival_causes_vault, run_jobs


def test_a_miss_with_two_rivals_generates_one_pinned_probe(tmp_path):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    fake = AuthorFake()
    outcomes = run_jobs(vault, repository, clients=author_clients(fake))
    assert [job.state for job in outcomes] == ["done"]
    assert fake.calls == 1
    row = wf.get(repository, outcome.workflow_id)
    assert row["state"] == wf.READY, row
    assert row["lane"] == wf.LANE_PROBE
    item_id = row["practice_item_id"]
    assert identity.is_generated_probe(repository, item_id)
    assert identity.closed_probe_ids(repository) == frozenset()
    pin = pinned_causal_probe(repository, row["presentation_id"])
    assert pin["followup_workflow_id"] == row["id"] and len(pin["blind_bundle_ids"]) == 2
    candidate = repository.causal_probe_candidate(row["probe_candidate_id"])
    assert candidate["status"] == "active"
    assert candidate["reviewer"].startswith("system:followup_machine_admission")
    assert repository.practice_item_state(item_id).active


def test_protected_and_reserved_items_never_reach_the_prompt(tmp_path, monkeypatch):
    from learnloop import learner_protection
    from learnloop.diagnosis import ai_contracts
    from tests.causal_p2_acceptance_helpers import COLD_ITEM, PROBE_ITEM

    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    real = learner_protection.withheld_items

    def withheld(vault_arg, repository_arg):
        seen = real(vault_arg, repository_arg)
        return learner_protection.Withheld(
            reasons={**seen.reasons, COLD_ITEM: "exam_material"}, available=True,
            known_items=seen.known_items, unknowns=seen.unknowns,
        )

    monkeypatch.setattr(learner_protection, "withheld_items", withheld)
    prompts = []
    real_prompt = ai_contracts.followup_probe_prompt

    def recording(context):
        text = real_prompt(context)
        prompts.append(text)
        return text

    monkeypatch.setattr("learnloop.followup_run.authoring.followup_probe_prompt", recording)
    fake = AuthorFake()
    run_jobs(vault, repository, clients=author_clients(fake))
    assert len(prompts) == 1
    assert vault.practice_items[COLD_ITEM].prompt not in prompts[0]
    assert vault.practice_items[PROBE_ITEM].prompt in prompts[0]
    assert wf.get(repository, outcome.workflow_id)["state"] == wf.READY


def test_no_learner_answer_reaches_the_author(tmp_path):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    miss_with_rivals(vault, repository)
    fake = AuthorFake()
    run_jobs(vault, repository, clients=author_clients(fake))
    assert "I multiplied the eigenvectors" not in repr(fake.contexts[0])
    assert all(set(row) == {"hypothesis_ref", "statement", "cause_scope", "target_ref"} for row in fake.contexts[0].hypotheses)


def test_protection_that_cannot_be_read_sends_no_prompt(tmp_path, monkeypatch):
    from learnloop import learner_protection

    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    monkeypatch.setattr(learner_protection, "withheld_items",
                        lambda *_args: learner_protection.Withheld(available=False))
    fake = AuthorFake()
    run_jobs(vault, repository, clients=author_clients(fake))
    assert fake.calls == 0
    row = wf.get(repository, outcome.workflow_id)
    assert row["state"] == wf.FAILED and row["feedback_released_at"] is not None


def test_predictions_that_do_not_separate_the_rivals_serve_nothing(tmp_path):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    fake = AuthorFake(same_predictions=True)
    run_jobs(vault, repository, clients=author_clients(fake))
    row = wf.get(repository, outcome.workflow_id)
    assert fake.calls == 1 and row["state"] == wf.FAILED and row["practice_item_id"] is None
    assert row["release_reason"] == wf.RELEASE_GENERATION_FAILED


def test_a_transport_failure_retries_once_and_then_fails_with_next_working(tmp_path):
    from datetime import timedelta

    from learnloop.clock import FrozenClock

    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    fake = AuthorFake(error=RuntimeError("provider down"))
    clients = author_clients(fake)
    first = run_jobs(vault, repository, clients=clients)
    assert [job.state for job in first] == ["retry"] and fake.calls == 1
    assert wf.get(repository, outcome.workflow_id)["state"] == wf.PENDING
    later = FrozenClock(CLOCK.now() + timedelta(minutes=5))
    second = run_jobs(vault, repository, clients=clients, clock=later)
    assert [job.state for job in second][0] == "failed" and fake.calls == 2
    assert wf.get(repository, outcome.workflow_id)["state"] == wf.FAILED


def test_a_late_generator_adds_nothing_after_a_skip(tmp_path):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)

    class SkipsMidway(AuthorFake):
        def run_followup_probe_authoring(self, context):
            wf.finish(repository, outcome.workflow_id, to_state=wf.SKIPPED, reason="continue_without_it",
                      release=wf.RELEASE_CONTINUE_WITHOUT, clock=CLOCK)
            return super().run_followup_probe_authoring(context)

    run_jobs(vault, repository, clients=author_clients(SkipsMidway()))
    row = wf.get(repository, outcome.workflow_id)
    assert row["state"] == wf.SKIPPED and row["practice_item_id"] is None
    generated = identity.generated_probe_ids(repository)
    assert len(generated) == 1 and generated <= identity.retired_probe_ids(repository)


def test_the_authoring_route_is_not_the_decider():
    from learnloop.ai.routing import ROUTE_FOR_OPERATION

    assert ROUTE_FOR_OPERATION["followup_probe_authoring"] == "followup_probe_author"


# -- §4.3: entry and need work ------------------------------------------------------------


def _entered(vault, repository, lo_id):
    from learnloop.diagnosis.probe_episodes import enter_episode

    existing = repository.open_probe_episode(lo_id)
    if existing is not None:
        repository.update_probe_episode_status(existing.id, status="abandoned", clock=CLOCK)
    return enter_episode(vault, repository, lo_id, trigger="manual", clock=CLOCK, ai_client=None)


def test_entry_enqueues_deduplicated_work_and_never_calls_a_model_inline(tmp_path):
    from learnloop.db.stores import followup_serve as store
    from learnloop.diagnosis.probe_episodes import enter_episode
    from tests.causal_p2_acceptance_helpers import LO_ID

    vault, repository, _paths = rival_causes_vault(tmp_path)
    fake = AuthorFake()
    episode = _entered(vault, repository, LO_ID)
    assert fake.calls == 0
    if episode.status == "pending_items":
        with repository.connection() as connection:
            job = store.generation_job(connection, f"entry:{episode.id}")
        assert job is not None and job["state"] == "queued"
        again = enter_episode(vault, repository, LO_ID, trigger="manual", clock=CLOCK)
        assert again.id == episode.id
        with repository.connection() as connection:
            count = connection.execute("SELECT COUNT(*) FROM followup_generation_jobs").fetchone()[0]
        assert count == 1


def test_a_mint_under_fg1_is_model_written_single_use_and_needs_no_review(tmp_path):
    from learnloop.followup_serve import queue
    from tests.causal_p2_acceptance_helpers import LO_ID
    from tests.probe_surface_mint_helpers import FakeSurfacesClient

    vault, repository, _paths = rival_causes_vault(tmp_path)
    episode = repository.open_probe_episode(LO_ID) or _entered(vault, repository, LO_ID)
    repository.update_probe_episode_status(episode.id, status="pending_items", clock=CLOCK)
    assert queue.enqueue_entry(repository, episode.id, clock=CLOCK)
    client = FakeSurfacesClient()
    from types import SimpleNamespace

    jobs = run_jobs(vault, repository, clients=SimpleNamespace(author=client))
    assert [job.state for job in jobs] == ["done"]
    assert len(client.calls) == 1  # one generation per deduplicated need
    generated = identity.generated_probe_ids(repository)
    assert len(generated) == 1
    item_id = next(iter(generated))
    assert repository.practice_item_state(item_id).active  # no human review
    assert "gen_" in item_id and "llm" in repr(repository.probe_item_family_links(item_id)[0].generator_id)


def test_a_failed_lanes_need_is_deduplicated_and_cancelled_when_the_factor_closes(tmp_path):
    from learnloop.followup_serve import queue

    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    run_jobs(vault, repository, clients=author_clients(AuthorFake(same_predictions=True)))
    row = wf.get(repository, outcome.workflow_id)
    assert row["state"] == wf.FAILED
    # One queued need already exists for the factor, keyed on it.
    assert queue.enqueue_factor(repository, row["factor_id"], workflow_id=row["id"], clock=CLOCK) is None


def _need(repository):
    return {"id": "need_1", "learning_object_id": "lo", "target_facets": [], "diagnostic_focus": {},
            "candidate_requirements": {}}


def test_a_recorded_need_fills_textbook_first_without_a_click(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from learnloop.content.authoring import practice_generation
    from learnloop.content.proposals import proposals
    from learnloop.followup_serve import queue
    from learnloop.instructional import needs

    vault, repository, _paths = rival_causes_vault(tmp_path)
    monkeypatch.setattr(repository, "pending_intervention_needs", lambda _lo=None: [_need(repository)])
    monkeypatch.setattr(needs, "pending_causal_decision", lambda *_args, **_kw: None)
    generated = []
    monkeypatch.setattr(practice_generation, "generate_diagnostic_practice_proposal",
                        lambda root, client, **kw: generated.append(kw) or SimpleNamespace(patch_id="p"))
    accepted = []
    monkeypatch.setattr(proposals, "accept_items", lambda root, patch: accepted.append(patch))

    monkeypatch.setattr(needs, "fulfil_need_from_sources", lambda *_a, **_k: {"outcome": "fulfilled"})
    assert queue.enqueue_need(repository, "need_1", clock=CLOCK)
    assert queue.enqueue_need(repository, "need_1", clock=CLOCK) is None
    run_jobs(vault, repository, clients=SimpleNamespace(authoring=object()))
    assert generated == [] and accepted == []

    monkeypatch.setattr(needs, "fulfil_need_from_sources", lambda *_a, **_k: {"outcome": "generate"})
    assert queue.enqueue_need(repository, "need_2", clock=CLOCK)
    monkeypatch.setattr(repository, "pending_intervention_needs",
                        lambda _lo=None: [{**_need(repository), "id": "need_2"}])
    run_jobs(vault, repository, clients=SimpleNamespace(authoring=object()))
    assert generated == [{"learning_object_id": "lo", "max_needs": 1}] and accepted == ["p"]
