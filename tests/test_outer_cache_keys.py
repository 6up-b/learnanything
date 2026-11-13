"""The outer caches of ingestion answer only for the request they were paid for.

Two caches answer before the per-call checkpoints: a unit's inventory row and a
synthesis shard's completed result. Each is reused only when the request it
answered is the one that would be sent now (its rendered prompt, schema and
settings), whatever label it was recorded under; a request that changed under
an unchanged label is paid once, and an unchanged one is not paid again.

No LLM: house fake clients count every call.
"""

from __future__ import annotations

import pytest

from learnloop.content.pipeline.runner import IngestRunner, JobSpec, RunnerServices
from learnloop.content.synthesis import ai_contracts
from learnloop.content.synthesis import source_set_synthesis as synthesis
from learnloop.content.synthesis.source_set_synthesis import StudyMapError, create_study_map
from learnloop.content.synthesis.source_unit_inventory import (
    PreparedInventory,
    prepare_unit_inventory,
    run_unit_inventory,
)
from tests.source_inventory_helpers import (
    _CLOCK,
    FakeInventoryClient,
    _block,
    _ir,
    _persist,
    _register_revision,
    _repo,
)
from tests.source_set_synthesis_helpers import FakeSynthesisClient, _setup_two_chapters


def _one_unit(tmp_path):
    repo = _repo(tmp_path)
    _register_revision(repo)
    _persist(repo, _ir([("u1", "Ch1", [_block("s1", "An eigenvector of A is a nonzero vector.")], "sha256:h1", 1)]),
             revision_id="rev1", extraction_id="ext1")
    return repo


def _edit_inventory_prompt(monkeypatch):
    monkeypatch.setattr(ai_contracts, "SOURCE_UNIT_INVENTORY_PROMPT",
                        ai_contracts.SOURCE_UNIT_INVENTORY_PROMPT + "\nPrefer the shortest faithful wording.")


# --- the inventory row ------------------------------------------------------


def test_an_inventory_row_answers_a_request_recorded_under_another_label(tmp_path):
    repo = _one_unit(tmp_path)
    client = FakeInventoryClient()
    first = run_unit_inventory(repo, "ext1", "u1", role="reference", client=client, clock=_CLOCK,
                               prompt_version="label-a")

    again = run_unit_inventory(repo, "ext1", "u1", role="reference", client=client, clock=_CLOCK,
                               prompt_version="label-b")

    assert again.cache_hit
    assert again.inventory_id == first.inventory_id
    assert len(client.calls) == 1
    assert [row["id"] for row in repo.unit_inventories_for_revision("rev1")] == [first.inventory_id]


def test_an_inventory_prompt_edited_under_the_same_label_is_paid_once(tmp_path, monkeypatch):
    repo = _one_unit(tmp_path)
    client = FakeInventoryClient()
    run_unit_inventory(repo, "ext1", "u1", role="reference", client=client, clock=_CLOCK)
    _edit_inventory_prompt(monkeypatch)

    edited = run_unit_inventory(repo, "ext1", "u1", role="reference", client=client, clock=_CLOCK)
    again = run_unit_inventory(repo, "ext1", "u1", role="reference", client=client, clock=_CLOCK)

    assert not edited.cache_hit
    assert again.cache_hit
    assert len(client.calls) == 2
    # The edited request's answer replaced the row's, under the same label.
    [row] = repo.unit_inventories_for_revision("rev1")
    assert row["id"] == again.inventory_id
    assert edited.inventory_id == row["id"]  # the id the update returned is the one stored


def test_an_inventory_rewritten_under_its_key_returns_and_marks_the_stored_id(tmp_path):
    from learnloop.content.synthesis.ai_contracts import InventoryAssessmentSignal, SourceUnitInventory

    repo = _one_unit(tmp_path)

    def write(inventory_id: str, spans: list[str]) -> str:
        inventory = SourceUnitInventory(unit_id="u1", semantic_hash="h1", assessment_signals=[
            InventoryAssessmentSignal(held_out=True, task_family="proof", span_ids=spans)])
        return repo.insert_unit_inventory(
            id=inventory_id, source_revision_id="rev1", extraction_id="ext1", unit_id="u1", unit_semantic_hash="h1",
            inventory_profile="assessment", inventory_schema_version=1, prompt_version="label-a", provider="fake",
            model="fake", inventory=inventory.model_dump(), made_as_role="exam", clock=_CLOCK)

    first = write("inv_first", ["s1"])
    second = write("inv_second", ["s1", "s2"])

    assert first == second == "inv_first"
    assert {mark["inventory_id"] for mark in repo.held_out_signal_marks()} == {"inv_first"}


def test_a_changed_inventory_model_is_paid_and_not_answered_by_the_old_row(tmp_path):
    repo = _one_unit(tmp_path)
    run_unit_inventory(repo, "ext1", "u1", role="reference", client=FakeInventoryClient(), clock=_CLOCK)

    class OtherModel(FakeInventoryClient):
        model = "fake-model-2"

    other = OtherModel()
    result = run_unit_inventory(repo, "ext1", "u1", role="reference", client=other, clock=_CLOCK)

    assert not result.cache_hit
    assert len(other.calls) == 1


def test_an_inventory_row_from_before_the_request_key_keeps_its_label_match(tmp_path):
    repo = _one_unit(tmp_path)
    fresh = run_unit_inventory(repo, "ext1", "u1", role="reference", client=FakeInventoryClient(), clock=_CLOCK)
    # A row written before rows recorded what they were asked: no request key in its usage.
    with repo.connection() as connection:
        connection.execute("UPDATE source_unit_inventories SET usage_json = '{\"calls\": 1}'")
        connection.commit()

    same_label = prepare_unit_inventory(repo, "ext1", "u1", role="reference", provider="codex",
                                        model="fake-model-1")
    other_label = prepare_unit_inventory(repo, "ext1", "u1", role="reference", provider="codex",
                                         model="fake-model-1", prompt_version="label-b")

    assert same_label.cache_hit and same_label.inventory_id == fresh.inventory_id
    assert isinstance(other_label, PreparedInventory)  # a miss: work to run, not a result


def test_an_inventory_job_pays_again_for_an_edited_prompt_and_not_for_an_unchanged_one(tmp_path, monkeypatch):
    repo = _one_unit(tmp_path)
    client = FakeInventoryClient()
    runner = IngestRunner(repo, vault_root=tmp_path, worker_id="w1", clock=_CLOCK,
                          services=RunnerServices(inventory_client_factory=lambda ctx: client))
    payload = {"extraction_id": "ext1", "units": [{"unit_id": "u1", "role": "reference"}]}

    def inventory_job():
        batch = runner.enqueue_batch("import_inventory", [JobSpec("inventory", payload)])
        runner.drain()
        [job] = runner.repo.ingest_jobs_for_batch(batch)
        assert job["status"] == "completed"
        return job["result"]["cache_hits"]

    assert inventory_job() == 0
    assert inventory_job() == 1
    _edit_inventory_prompt(monkeypatch)
    assert inventory_job() == 0
    assert inventory_job() == 1
    assert len(client.calls) == 2


# --- the completed shard ----------------------------------------------------


def _two_shards(root, repo, client):
    return create_study_map(root, "set_la", client=client, brief={"depth": "intro"}, repository=repo,
                            clock=_CLOCK, budget_overrides={"synthesis_shard_input_tokens": 1})


def _fail_after_the_shards(monkeypatch, root, repo, client):
    """Run both shards, then fail before the run completes: the shards are saved, the run is not."""

    def fail(result):
        raise StudyMapError("injected_failure", "failed after the shards were saved")

    with monkeypatch.context() as patch:
        patch.setattr(synthesis, "_consolidate_same_title_concepts", fail)
        with pytest.raises(StudyMapError, match="shards were saved"):
            _two_shards(root, repo, client)


def test_a_shard_prompt_edited_under_the_same_label_is_paid_once(tmp_path, monkeypatch):
    root, repo = _setup_two_chapters(tmp_path)
    client = FakeSynthesisClient()
    _fail_after_the_shards(monkeypatch, root, repo, client)
    assert len(client.calls) == 2
    monkeypatch.setattr(ai_contracts, "SOURCE_SET_SYNTHESIS_PROMPT",
                        ai_contracts.SOURCE_SET_SYNTHESIS_PROMPT + "\nPrefer fewer, broader concepts.")

    result = _two_shards(root, repo, client)

    assert len(client.calls) == 4
    usage = repo.synthesis_run(result.synthesis_run_id)["actual_usage"]
    assert (usage["reused_shards"], usage["calls"]) == (0, 2)


def test_a_shard_answers_from_its_pass_checkpoint_without_its_completed_row(tmp_path, monkeypatch):
    root, repo = _setup_two_chapters(tmp_path)
    client = FakeSynthesisClient()
    _fail_after_the_shards(monkeypatch, root, repo, client)
    # A completed shard saved under an earlier key is never found again.
    with repo.connection() as connection:
        connection.execute("DELETE FROM synthesis_shard_results")
        connection.commit()

    result = _two_shards(root, repo, client)

    assert len(client.calls) == 2
    usage = repo.synthesis_run(result.synthesis_run_id)["actual_usage"]
    assert (usage["reused_shards"], usage["calls"]) == (0, 0)


def test_an_unchanged_shard_is_read_from_its_completed_row(tmp_path, monkeypatch):
    root, repo = _setup_two_chapters(tmp_path)
    client = FakeSynthesisClient()
    _fail_after_the_shards(monkeypatch, root, repo, client)

    result = _two_shards(root, repo, client)

    assert len(client.calls) == 2
    usage = repo.synthesis_run(result.synthesis_run_id)["actual_usage"]
    assert (usage["reused_shards"], usage["calls"]) == (2, 0)
