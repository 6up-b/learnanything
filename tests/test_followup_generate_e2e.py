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
    from tests.test_causal_p2_acceptance import COLD_ITEM, PROBE_ITEM

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
            wf.move(repository, outcome.workflow_id, to_state=wf.SKIPPED, reason="continue_without_it",
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
