"""Mobile PR-3: the abandoned-synthesis sweep belongs to primary hosts only.

``spec_mobile_tailnet_v1`` §3.3 PR-3 and §10 G6a: a synchronous synthesis run
(the desktop's RPC, a CLI command) holds no ingest lease, so the startup sweep
``_finalize_abandoned_synthesis_runs_locked`` cannot tell one the desktop is
still executing from one an earlier process abandoned. A secondary host binds
with ``sweep_abandoned_synthesis=False``: it still fences expired leases, and a
desktop run older than the lease cutoff survives its start. The primary's
default is unchanged.

Durability lane: production pragmas and WAL on a fresh vault, the
configuration the desktop and the host share.
"""

from __future__ import annotations

import multiprocessing
import traceback
from datetime import UTC, datetime
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.content.pipeline.jobs import DurableIngestJobs
from learnloop.content.pipeline.runner import IngestRunner, JobSpec
from learnloop.content.synthesis.synthesis_manifests import build_manifest, persist_manifest
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault

pytestmark = pytest.mark.durability

OLD = FrozenClock(datetime(2020, 1, 1, tzinfo=UTC))


def _seed(tmp_path: Path):
    """A leaseless synchronous synthesis run and a leased job, both long past the lease cutoff."""

    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    repository = Repository.attach(paths.sqlite_path)
    manifest = persist_manifest(repository, build_manifest(load_vault(paths.root), source_set_id="ss1"))
    run_id = repository.insert_synthesis_run(manifest_id=manifest, mode="bootstrap", clock=OLD)
    IngestRunner(repository, vault_root=paths.root, worker_id="desktop", clock=OLD).enqueue_batch(
        "legacy_ingest", [JobSpec("fake")]
    )
    lease = repository.claim_next_ingest_job(
        worker_id="desktop", now_iso="2020-01-01T00:00:00Z", lease_cutoff_iso="2019-12-31T23:58:00Z",
    )
    assert lease is not None
    return paths, repository, run_id, lease["id"]


def _bind(sqlite_path: Path, root: Path, **kwargs) -> None:
    jobs = DurableIngestJobs()
    try:
        jobs.bind(Repository.attach(sqlite_path), root, background=False, **kwargs)
    finally:
        jobs.shutdown()


def _secondary_bind_process(sqlite_path: str, root: str, pipe) -> None:
    try:
        _bind(Path(sqlite_path), Path(root), sweep_abandoned_synthesis=False)
        pipe.send(("bound",))
    except BaseException:
        pipe.send(("error", traceback.format_exc()))
    finally:
        pipe.close()


def test_a_secondary_bind_fences_expired_leases_and_never_sweeps_synthesis(tmp_path):
    paths, repository, run_id, job_id = _seed(tmp_path)

    _bind(paths.sqlite_path, paths.root, sweep_abandoned_synthesis=False)

    assert repository.synthesis_run(run_id)["status"] == "created"
    job = repository.get_ingest_job(job_id)
    assert job["status"] == "failed"
    assert job["error"]["code"] == "interrupted"


def test_the_primary_default_still_sweeps_abandoned_synthesis_runs(tmp_path):
    paths, repository, run_id, job_id = _seed(tmp_path)

    _bind(paths.sqlite_path, paths.root)

    assert repository.synthesis_run(run_id)["status"] == "failed"
    assert repository.get_ingest_job(job_id)["status"] == "failed"


def test_recover_stale_leases_skips_only_the_sweep_when_asked(tmp_path):
    paths, repository, run_id, job_id = _seed(tmp_path)
    runner = IngestRunner(repository, vault_root=paths.root, worker_id="mobile-host-1")

    assert runner.recover_stale_leases(sweep_abandoned_synthesis=False) == [job_id]
    assert repository.synthesis_run(run_id)["status"] == "created"

    # The sweep itself is untouched: the primary's recovery still finalizes the run.
    IngestRunner(repository, vault_root=paths.root, worker_id="desktop").recover_stale_leases()
    assert repository.synthesis_run(run_id)["status"] == "failed"


def test_a_desktop_synchronous_run_survives_a_secondary_start_in_another_process(tmp_path):
    """G6a's synthesis clause, with a real second process on WAL."""

    paths, repository, run_id, job_id = _seed(tmp_path)
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe()
    process = context.Process(
        target=_secondary_bind_process, args=(str(paths.sqlite_path), str(paths.root), child)
    )
    process.start()
    child.close()
    try:
        assert parent.poll(60), "the secondary process did not reply within 60 seconds"
        reply = parent.recv()
        assert reply == ("bound",), reply
        process.join(timeout=10)
        assert process.exitcode == 0
    finally:
        if process.is_alive():
            process.terminate()
        parent.close()

    assert repository.synthesis_run(run_id)["status"] == "created"
    assert repository.get_ingest_job(job_id)["status"] == "failed"
