"""Merged-section inventory batching + concurrent inventory execution.

Learner ``merge_with_next`` overrides (§5.3) fold adjacent same-role units into
ONE inventory call over the merged view (cached under the composite ``u1+u2``
identity), and cache-missed units execute their model calls concurrently while
all SQLite access stays on the runner thread.

No LLM: the codex ``run_source_unit_inventory`` method is stubbed (house
fake-client pattern from tests.test_source_inventory).
"""

from __future__ import annotations

import threading

from tests.test_source_inventory import (
    _CLOCK,
    FakeInventoryClient,
    _block,
    _ir,
    _persist,
    _register_revision,
    _repo,
)

from learnloop.content.synthesis.source_unit_selection import save_unit_selection


def _three_unit_ir():
    return _ir(
        [
            ("u1", "Ch1", [_block("s1", "Eigenvectors scale under A.")], "sha256:h1", 1),
            ("u2", "Ch2", [_block("s2", "Eigenvalues solve det(A - lambda I) = 0.")], "sha256:h2", 2),
            ("u3", "Ch3", [_block("s3", "Diagonalization uses an eigenbasis.")], "sha256:h3", 3),
        ]
    )


def _runner(repo, tmp_path, client):
    from learnloop.content.pipeline.runner import IngestRunner, RunnerServices

    services = RunnerServices(inventory_client_factory=lambda ctx: client)
    return IngestRunner(repo, vault_root=tmp_path, worker_id="w1", clock=_CLOCK, services=services)


def test_merged_units_inventory_as_one_call_and_cache_composite(tmp_path):
    from learnloop.content.pipeline.runner import JobSpec

    repo = _repo(tmp_path)
    _register_revision(repo)
    _persist(repo, _three_unit_ir(), revision_id="rev1", extraction_id="ext1")
    save_unit_selection(
        repo,
        "ext1",
        ["u1", "u2", "u3"],
        boundary_overrides=[{"op": "merge_with_next", "unit_id": "u1"}],
        clock=_CLOCK,
    )

    client = FakeInventoryClient()
    runner = _runner(repo, tmp_path, client)
    payload = {
        "extraction_id": "ext1",
        "units": [
            {"unit_id": "u1", "role": "primary_textbook", "profile": "combined"},
            {"unit_id": "u2", "role": "primary_textbook", "profile": "combined"},
            {"unit_id": "u3", "role": "primary_textbook", "profile": "combined"},
        ],
    }
    batch = runner.enqueue_batch("import_inventory", [JobSpec("inventory", payload)])
    runner.drain()
    job = runner.repo.ingest_jobs_for_batch(batch)[0]
    assert job["status"] == "completed"

    # u1+u2 fold into one call; u3 stays its own call.
    assert len(client.calls) == 2
    result_units = job["result"]["units"]
    assert [entry["unit_id"] for entry in result_units] == ["u1+u2", "u3"]
    assert result_units[0]["unit_ids"] == ["u1", "u2"]

    # The merged view carried BOTH members' spans in one window.
    merged_call = next(c for c in client.calls if c.unit_id == "u1+u2")
    merged_spans = [b["span_id"] for b in merged_call.unit_view["blocks"]]
    assert merged_spans == ["s1", "s2"]

    # Stored under the composite identity.
    rows = repo.unit_inventories_for_revision("rev1")
    assert sorted(row["unit_id"] for row in rows) == ["u1+u2", "u3"]

    # A second identical batch is a full cache hit — ZERO new calls.
    batch2 = runner.enqueue_batch("import_inventory", [JobSpec("inventory", payload)])
    runner.drain()
    job2 = runner.repo.ingest_jobs_for_batch(batch2)[0]
    assert job2["status"] == "completed"
    assert job2["result"]["cache_hits"] == 2
    assert len(client.calls) == 2


def test_mixed_role_merge_group_does_not_fold(tmp_path):
    from learnloop.content.pipeline.runner import JobSpec

    repo = _repo(tmp_path)
    _register_revision(repo)
    _persist(repo, _three_unit_ir(), revision_id="rev1", extraction_id="ext1")
    save_unit_selection(
        repo,
        "ext1",
        ["u1", "u2"],
        boundary_overrides=[{"op": "merge_with_next", "unit_id": "u1"}],
        clock=_CLOCK,
    )

    client = FakeInventoryClient()
    runner = _runner(repo, tmp_path, client)
    payload = {
        "extraction_id": "ext1",
        "units": [
            {"unit_id": "u1", "role": "primary_textbook", "profile": "combined"},
            {"unit_id": "u2", "role": "reference", "profile": "combined"},
        ],
    }
    batch = runner.enqueue_batch("import_inventory", [JobSpec("inventory", payload)])
    runner.drain()
    job = runner.repo.ingest_jobs_for_batch(batch)[0]
    assert job["status"] == "completed"
    assert [entry["unit_id"] for entry in job["result"]["units"]] == ["u1", "u2"]
    assert len(client.calls) == 2


def test_exam_role_merge_group_does_not_fold(tmp_path):
    from learnloop.content.pipeline.runner import JobSpec

    repo = _repo(tmp_path)
    _register_revision(repo)
    _persist(repo, _three_unit_ir(), revision_id="rev1", extraction_id="ext1")
    save_unit_selection(
        repo,
        "ext1",
        ["u1", "u2"],
        boundary_overrides=[{"op": "merge_with_next", "unit_id": "u1"}],
        clock=_CLOCK,
    )

    client = FakeInventoryClient()
    runner = _runner(repo, tmp_path, client)
    payload = {
        "extraction_id": "ext1",
        "units": [
            {"unit_id": "u1", "role": "exam"},
            {"unit_id": "u2", "role": "exam"},
        ],
    }
    batch = runner.enqueue_batch("import_inventory", [JobSpec("inventory", payload)])
    runner.drain()
    job = runner.repo.ingest_jobs_for_batch(batch)[0]
    assert job["status"] == "completed"
    assert [entry["unit_id"] for entry in job["result"]["units"]] == ["u1", "u2"]


class BarrierInventoryClient(FakeInventoryClient):
    """Proves concurrency: each call blocks until BOTH calls have arrived. A
    sequential handler would deadlock (barrier timeout → job fails)."""

    def __init__(self):
        super().__init__()
        self.barrier = threading.Barrier(2, timeout=30)

    def run_source_unit_inventory(self, context):
        self.barrier.wait()
        return super().run_source_unit_inventory(context)


def test_cache_missed_units_inventory_concurrently(tmp_path):
    from learnloop.content.pipeline.runner import JobSpec

    repo = _repo(tmp_path)
    _register_revision(repo)
    _persist(repo, _three_unit_ir(), revision_id="rev1", extraction_id="ext1")

    client = BarrierInventoryClient()
    runner = _runner(repo, tmp_path, client)
    payload = {
        "extraction_id": "ext1",
        "units": [
            {"unit_id": "u1", "role": "primary_textbook", "profile": "combined"},
            {"unit_id": "u2", "role": "primary_textbook", "profile": "combined"},
        ],
    }
    batch = runner.enqueue_batch("import_inventory", [JobSpec("inventory", payload)])
    runner.drain()
    job = runner.repo.ingest_jobs_for_batch(batch)[0]
    assert job["status"] == "completed"
    assert len(client.calls) == 2
    # Result order follows the payload order even though completion order raced.
    assert [entry["unit_id"] for entry in job["result"]["units"]] == ["u1", "u2"]


def test_full_inventory_cache_hit_never_constructs_provider(tmp_path):
    from learnloop.content.pipeline.runner import IngestRunner, JobSpec, RunnerServices
    from learnloop.content.synthesis.source_unit_inventory import run_unit_inventory

    repo = _repo(tmp_path)
    _register_revision(repo)
    _persist(repo, _three_unit_ir(), revision_id="rev1", extraction_id="ext1")
    client = FakeInventoryClient()
    run_unit_inventory(
        repo,
        "ext1",
        "u1",
        role="primary_textbook",
        profile="combined",
        client=client,
        clock=_CLOCK,
    )

    factory_calls = 0

    def client_factory(_ctx):
        nonlocal factory_calls
        factory_calls += 1
        return FakeInventoryClient()

    services = RunnerServices(
        inventory_client_factory=client_factory,
        inventory_identity_factory=lambda _ctx: ("codex", "fake-model-1"),
    )
    runner = IngestRunner(
        repo,
        vault_root=tmp_path,
        worker_id="w1",
        clock=_CLOCK,
        services=services,
    )
    batch = runner.enqueue_batch(
        "import_inventory",
        [
            JobSpec(
                "inventory",
                {
                    "extraction_id": "ext1",
                    "units": [
                        {
                            "unit_id": "u1",
                            "role": "primary_textbook",
                            "profile": "combined",
                        }
                    ],
                },
            )
        ],
    )
    runner.drain()

    job = runner.repo.ingest_jobs_for_batch(batch)[0]
    assert job["status"] == "completed"
    assert job["result"]["cache_hits"] == 1
    assert factory_calls == 0


def test_synthesis_gather_folds_merged_group_once_with_member_fallback(tmp_path):
    from learnloop.content.synthesis.source_set_synthesis import _collect_inputs
    from learnloop.content.synthesis.source_unit_inventory import run_unit_inventory
    from learnloop.vault.loader import add_subject, init_vault, load_vault
    from learnloop.vault.writer import upsert_source_set

    root = tmp_path / "vault"
    init_vault(root, clock=_CLOCK)
    add_subject(root, "linear-algebra", "Linear Algebra", clock=_CLOCK)
    repo = _repo(root)
    _register_revision(repo)
    _persist(repo, _three_unit_ir(), revision_id="rev1", extraction_id="ext1")
    save_unit_selection(
        repo,
        "ext1",
        ["u1", "u2", "u3"],
        boundary_overrides=[{"op": "merge_with_next", "unit_id": "u1"}],
        clock=_CLOCK,
    )
    upsert_source_set(
        root,
        {
            "id": "set_la",
            "subject_id": "linear-algebra",
            "title": "LA",
            "members": [
                {
                    "source_id": "src1",
                    "revision_id": "rev1",
                    "default_role": "primary_textbook",
                    "scope": [{"unit_id": "u1"}, {"unit_id": "u2"}, {"unit_id": "u3"}],
                    "priority": 1,
                }
            ],
        },
        clock=_CLOCK,
    )
    vault = load_vault(root)
    source_set = next(s for s in vault.source_sets if s.id == "set_la")
    client = FakeInventoryClient()

    # Pre-merge per-unit rows only → the merged group falls back to member rows.
    for unit_id in ("u1", "u2", "u3"):
        run_unit_inventory(repo, "ext1", unit_id, role="primary_textbook",
                           profile="combined", client=client, clock=_CLOCK)
    inputs = _collect_inputs(repo, vault, source_set)
    assert [entry["unit_id"] for entry in inputs.unit_inventories] == ["u1", "u2", "u3"]

    # With the composite row present, the merged group enters ONCE and the
    # composite id becomes a valid unit designator for span requests/gates.
    run_unit_inventory(repo, "ext1", "u1", unit_ids=["u1", "u2"], role="primary_textbook",
                       profile="combined", client=client, clock=_CLOCK)
    inputs = _collect_inputs(repo, vault, source_set)
    assert [entry["unit_id"] for entry in inputs.unit_inventories] == ["u1+u2", "u3"]
    assert "u1+u2" in inputs.extraction_units["ext1"]


def test_merged_inventory_marker_covers_member_units(tmp_path):
    from learnloop.content.pipeline.runner import JobSpec
    from learnloop.content.synthesis.source_unit_inventory import inventory_marker

    repo = _repo(tmp_path)
    _register_revision(repo)
    _persist(repo, _three_unit_ir(), revision_id="rev1", extraction_id="ext1")
    save_unit_selection(
        repo,
        "ext1",
        ["u1", "u2"],
        boundary_overrides=[{"op": "merge_with_next", "unit_id": "u1"}],
        clock=_CLOCK,
    )

    client = FakeInventoryClient()
    runner = _runner(repo, tmp_path, client)
    payload = {
        "extraction_id": "ext1",
        "units": [
            {"unit_id": "u1", "role": "primary_textbook", "profile": "combined"},
            {"unit_id": "u2", "role": "primary_textbook", "profile": "combined"},
        ],
    }
    runner.enqueue_batch("import_inventory", [JobSpec("inventory", payload)])
    runner.drain()

    # The composite row marks each member unit inventoried (outline badge), and
    # the composite id itself resolves (build-plan cached check).
    assert inventory_marker(repo, "ext1", "u1")["inventoried"] is True
    assert inventory_marker(repo, "ext1", "u2")["inventoried"] is True
    assert inventory_marker(repo, "ext1", "u1+u2")["inventoried"] is True
    assert inventory_marker(repo, "ext1", "u3")["inventoried"] is False
