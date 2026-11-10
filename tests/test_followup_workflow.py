"""FG1 §5 item 1, §3.1: one durable workflow owns a miss's intervention."""

from __future__ import annotations

from learnloop.attempts.post_attempt import EXAM_SITTING_CAP_REASON, run_exam_sitting_pipeline, run_post_attempt_pipeline
from learnloop.db.stores import followup_serve as store
from learnloop.followup_run.lanes import settle_practice_lane
from learnloop.followup_serve import workflow as wf
from learnloop.followup_serve.gates import effective_auto_generate_on_entry, generate_and_serve_on

from tests.followup_serve_helpers import CLOCK, BlindRivalClient, OFF, TAG, miss_with_rivals, rival_causes_vault, run_jobs
from tests.split_live_helpers import drain_jobs, split_vault, submit
from tests.test_causal_p2_acceptance import _divergent_failure


def _workflows(repository):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM followup_workflows")]


def test_a_miss_at_the_tag_opens_one_workflow_and_withholds_the_predecessors_insertion(tmp_path):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    result, outcome = miss_with_rivals(vault, repository)
    assert generate_and_serve_on(vault.config)
    rows = _workflows(repository)
    assert [row["id"] for row in rows] == [outcome.workflow_id]
    assert rows[0]["state"] == wf.PENDING and rows[0]["feedback_held"] == 1
    assert rows[0]["source_attempt_id"] == result.attempt_id
    assert outcome.followup.practice_item_id is None and outcome.followup.need_id is None
    assert any(wf.WORKFLOW_OWNS_REASON in entry for entry in outcome.followup.suppressed_actions)


def test_the_identity_is_stable_and_a_resumed_completion_reuses_it(tmp_path):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    result, outcome = miss_with_rivals(vault, repository)
    assert outcome.workflow_id == wf.workflow_id_for(result.attempt_id, "joint")
    with repository.atomic():
        again = wf.open_for_attempt(vault, repository, result=result, surface="desktop", session_id=None,
                                    grade=(True, "joint"), clock=CLOCK)
    assert again["id"] == outcome.workflow_id
    assert len(_workflows(repository)) == 1


def test_the_tui_stays_on_the_predecessors_path(tmp_path):
    # A door with no pending and skip UI names no surface. The phone has them from mobile v2 V2
    # (surface "phone"): tests/test_mobile_v2_followup.py.
    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository, surface=None)
    assert outcome.workflow_id is None and _workflows(repository) == []
    _result, outcome = miss_with_rivals(vault, repository, surface="tui", attempt_id="att_tui")
    assert outcome.workflow_id is None and _workflows(repository) == []


def test_below_the_tag_or_with_the_switch_off_no_workflow_opens(tmp_path):
    vault, repository, _paths = rival_causes_vault(tmp_path / "old", version="mvp-0.44")
    _result, outcome = miss_with_rivals(vault, repository)
    assert outcome.workflow_id is None and _workflows(repository) == []
    vault, repository, _paths = rival_causes_vault(tmp_path / "off", config=OFF)
    _result, outcome = miss_with_rivals(vault, repository)
    assert not generate_and_serve_on(vault.config)
    assert outcome.workflow_id is None and _workflows(repository) == []


def test_auto_generate_on_entry_is_effectively_true_only_while_fg1_is_on(tmp_path):
    vault, _repository, _paths = rival_causes_vault(tmp_path / "on")
    assert vault.config.probe.generation.auto_generate_on_entry is False  # the stored value stays
    assert effective_auto_generate_on_entry(vault.config) is True
    vault, _repository, _paths = rival_causes_vault(tmp_path / "off", config=OFF)
    assert effective_auto_generate_on_entry(vault.config) is False


def test_a_practice_lane_fallback_runs_the_predecessors_chooser_once(tmp_path):
    _paths, vault, repository = split_vault(tmp_path, version=TAG)
    client = BlindRivalClient()  # one cause: rivals would take the probe lane (R9)
    client.causes, client.shape = 1, "no_target"
    result = submit(vault, repository, client, pipeline=False)
    outcome = run_post_attempt_pipeline(vault, repository, result=result, followup_surface="desktop", clock=CLOCK)
    assert outcome.workflow_id is not None
    # No diagnosis has run: the worker has nothing to do yet.
    assert run_jobs(vault, repository) == []
    drain_jobs(vault, repository, client)
    assert wf.get(repository, outcome.workflow_id)["state"] == wf.PENDING
    assert [job.state for job in run_jobs(vault, repository)] == ["done"]
    row = wf.get(repository, outcome.workflow_id)
    assert row["state"] == wf.SETTLED and row["lane"] == wf.LANE_PRACTICE
    assert row["feedback_released_at"] is not None
    actions = repository.fetch_attempt_feedback_metadata(result.attempt_id)
    assert actions is not None
    # Its job is one row: a second drain finds nothing.
    assert run_jobs(vault, repository) == []


def test_a_settled_workflow_takes_nothing_more(tmp_path):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    assert wf.finish(repository, outcome.workflow_id, to_state=wf.SKIPPED, reason="continue_without_it",
                     release=wf.RELEASE_CONTINUE_WITHOUT, clock=CLOCK)
    row = wf.get(repository, outcome.workflow_id)
    assert row["release_reason"] == wf.RELEASE_CONTINUE_WITHOUT
    # A late generator or diagnosis loses the compare-and-set.
    assert not wf.move(repository, outcome.workflow_id, to_state=wf.READY, reason="late", clock=CLOCK)
    assert not settle_practice_lane(vault, repository, row, reason="late", clock=CLOCK)
    wf.diagnosis_ended(vault, repository, attempt_id=row["source_attempt_id"], clock=CLOCK)
    with repository.connection() as connection:
        assert store.generation_job(connection, f"workflow:{outcome.workflow_id}")["state"] == "skipped"
        moves = [event["to_state"] for event in store.workflow_events(connection, outcome.workflow_id)]
    assert moves == ["pending", "skipped"]


def test_the_switch_off_settles_open_workflows_as_skipped(tmp_path):
    vault, repository, paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository)
    from learnloop.vault.loader import load_vault
    from tests.helpers import append_config_toml

    append_config_toml(paths.root, OFF)
    off = load_vault(paths.root)
    assert wf.settle_open_when_off(off, repository, clock=CLOCK) == 1
    row = wf.get(repository, outcome.workflow_id)
    assert row["state"] == wf.SKIPPED and row["settled_reason"] is None
    assert row["release_reason"] == wf.RELEASE_SWITCH_OFF


def test_an_exam_sitting_records_eligibility_inside_its_cap(tmp_path):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    results = [_divergent_failure(vault, repository, attempt_id=f"att_exam_{index}") for index in range(5)]
    outcomes = run_exam_sitting_pipeline(vault, repository, results=results, followup_surface="desktop", clock=CLOCK)
    owned = [outcome for outcome in outcomes if outcome.workflow_id]
    assert len(owned) == 3
    assert all(not row["feedback_held"] and row["origin"] == "exam" for row in _workflows(repository))
    assert sum(EXAM_SITTING_CAP_REASON in outcome.notes for outcome in outcomes) == 2


def test_a_generated_probe_attempt_opens_no_workflow(tmp_path):
    from learnloop.followup_serve import identity
    from tests.test_causal_p2_acceptance import SOURCE_ITEM

    vault, repository, _paths = rival_causes_vault(tmp_path)
    identity.register(repository, practice_item_id=SOURCE_ITEM, revision="r", source="manual", clock=CLOCK)
    _result, outcome = miss_with_rivals(vault, repository)
    assert outcome.workflow_id is None and _workflows(repository) == []
