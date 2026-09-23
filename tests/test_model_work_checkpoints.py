"""Model-work checkpoints: stale results are discarded, and every path keys a
window the same way for the same inputs."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from learnloop.ai.errors import AITurnTimeout
from learnloop.content.pipeline.runner import IngestRunner, JobSpec, RunnerServices
from learnloop.content.synthesis import source_unit_inventory as inventory
from learnloop.content.synthesis.source_set_synthesis import StudyMapError, create_study_map
from learnloop.db.repositories import Repository
from tests.test_source_inventory import FakeInventoryClient, _block, _ir, _persist, _register_revision, _CLOCK
from tests.test_source_set_synthesis import FakeSynthesisClient, _default_payload, _setup


def _checkpoint_rows(repo, purpose):
    with repo.connection() as connection:
        return connection.execute(
            "SELECT cache_key, result_json FROM model_work_checkpoints WHERE purpose = ?", (purpose,)
        ).fetchall()


def _one_unit_document(repo):
    _register_revision(repo)
    document = _ir([("u1", "Chapter", [_block("s1", "An eigenvector scales under a matrix.")], "hash1", 1)])
    _persist(repo, document, revision_id="rev1", extraction_id="ext1")
    return document


def test_inventory_window_checkpoint_that_no_longer_validates_is_discarded(tmp_path, monkeypatch):
    repo = Repository(tmp_path / "state.sqlite")
    document = _one_unit_document(repo)
    window = inventory.build_inventory_windows(document, "u1", input_budget_tokens=20000)[0]
    monkeypatch.setattr(inventory, "build_inventory_windows", lambda *_args, **_kwargs: [{**window, "window_ordinal": 1}, {**window, "window_ordinal": 2}])
    original = inventory.request_source_unit_inventory
    interrupted = False

    def request(client, context):
        nonlocal interrupted
        if context.unit_view["window_ordinal"] == 2 and not interrupted:
            interrupted = True
            raise AITurnTimeout("interrupted window")
        return original(client, context)

    monkeypatch.setattr(inventory, "request_source_unit_inventory", request)
    client = FakeInventoryClient()
    with pytest.raises(AITurnTimeout):
        inventory.run_unit_inventory(repo, "ext1", "u1", role="reference", client=client, clock=_CLOCK)
    [(key, _result)] = _checkpoint_rows(repo, "inventory_window")
    # The saved window now cites a span the unit no longer has.
    with repo.connection() as connection:
        connection.execute(
            "UPDATE model_work_checkpoints SET result_json = ? WHERE cache_key = ?",
            ('{"concept_mentions": [{"name": "eigenvector", "span_ids": ["s_gone"]}]}', key),
        )

    result = inventory.run_unit_inventory(repo, "ext1", "u1", role="reference", client=client, clock=_CLOCK)

    assert result.usage["reused_windows"] == 0
    assert result.usage["calls"] == 2
    assert all("s_gone" not in row[1] for row in _checkpoint_rows(repo, "inventory_window"))


def test_synthesis_pass_checkpoint_that_no_longer_validates_is_discarded(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)

    def builder(context, _n):
        return _default_payload(context).model_copy(update={"summary": "long summary " * 400})

    client = FakeSynthesisClient(builder=builder)
    with pytest.raises(StudyMapError, match="exceeded its output budget"):
        create_study_map(root, "set_la", client=client, repository=repo, clock=_CLOCK,
                         budget_overrides={"synthesis_shard_output_tokens": 100})
    [(key, _result)] = _checkpoint_rows(repo, "synthesis_pass")
    with repo.connection() as connection:
        connection.execute(
            "UPDATE model_work_checkpoints SET result_json = ? WHERE cache_key = ?",
            ('{"span_requests": "not a list"}', key),
        )

    result = create_study_map(root, "set_la", client=client, repository=repo, clock=_CLOCK)

    assert result.proposal_id is not None
    assert len(client.calls) == 2
    assert all("not a list" not in row[1] for row in _checkpoint_rows(repo, "synthesis_pass"))


class _ConfiguredInventoryClient(FakeInventoryClient):
    """An inventory client whose provider settings go beyond its model slug."""

    profile = SimpleNamespace(
        model="fake-model-1", base_url="https://inventory.example/v1",
        reasoning_effort="high", thinking=None, response_format=None,
    )


def test_ingest_job_and_direct_inventory_key_windows_identically(tmp_path):
    repo = Repository(tmp_path / "state.sqlite")
    _one_unit_document(repo)
    direct = inventory.prepare_unit_inventory(
        repo, "ext1", "u1", role="reference", client=_ConfiguredInventoryClient(),
        input_budget_tokens=20000, clock=_CLOCK,
    )
    assert direct.window_keys

    runner = IngestRunner(
        repo, vault_root=tmp_path, worker_id="worker", clock=_CLOCK,
        services=RunnerServices(inventory_client_factory=lambda ctx: _ConfiguredInventoryClient()),
    )
    batch = runner.enqueue_batch("import_inventory", [JobSpec("inventory", {
        "extraction_id": "ext1", "input_budget_tokens": 20000,
        "units": [{"unit_id": "u1", "role": "reference"}],
    })])
    runner.drain()

    assert repo.ingest_jobs_for_batch(batch)[0]["status"] == "completed"
    assert sorted(row[0] for row in _checkpoint_rows(repo, "inventory_window")) == sorted(direct.window_keys)
