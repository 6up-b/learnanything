from __future__ import annotations

import pytest
pytestmark = pytest.mark.durability

from learnloop.clock import utc_now_iso
from learnloop.content.pipeline.jobs import DurableIngestJobs
from learnloop.content.pipeline.runner import JobSpec
from learnloop.db.repositories import Repository
from learnloop.db.scopes import JobOwnershipLost, guard_ingest_writes
from learnloop.db.stores.ingest_queue import JobOwner
from learnloop.vault_lock import vault_mutation_lock
from tests.test_ingest_runner import _clock, _ok_handler, _runner


def _claim(repository, worker, seconds):
    return repository.claim_next_ingest_job(
        worker_id=worker, now_iso=utc_now_iso(_clock(seconds)),
        lease_cutoff_iso=utc_now_iso(_clock(seconds - 120)),
    )


def test_stale_worker_cannot_finish_or_publish_after_replacement(tmp_path):
    runner = _runner(tmp_path, handlers={'fake': _ok_handler({})})
    batch = runner.enqueue_batch('import', [JobSpec('fake')])
    old = _claim(runner.repo, 'old', 0)
    replacement = _runner(tmp_path, worker_id='new', clock=_clock(180), handlers={'fake': _ok_handler({})})
    replacement.resume_batch(batch)
    replacement.drain()
    completed = replacement.repo.get_ingest_job(old['id'])
    assert completed['status'] == 'completed'
    assert completed['attempt_count'] == 2
    assert not runner.repo.finish_ingest_job(
        old['id'], worker_id='old', attempt_count=1, expected_status='running',
        status='completed', result={'stale': True}, clock=_clock(181),
    )
    assert not runner.repo.heartbeat_ingest_job(old['id'], owner=JobOwner('old', 1))
    with guard_ingest_writes(runner.repo.sqlite_path, old['id'], 'old', 1):
        # A service-created repository must inherit the fence too.
        other = Repository.attach(runner.repo.sqlite_path)
        with pytest.raises(JobOwnershipLost):
            other.update_ingest_job_payload(old['id'], {'stale': True})
        with pytest.raises(JobOwnershipLost):
            with vault_mutation_lock(tmp_path, purpose='late_apply'):
                (tmp_path / 'stale.yaml').write_text('must not publish')
    assert not (tmp_path / 'stale.yaml').exists()
    assert runner.repo.get_ingest_job(old['id']) == completed


def test_recovery_rechecks_a_heartbeat_renewed_after_candidate_read(tmp_path, monkeypatch):
    runner = _runner(tmp_path, handlers={'fake': _ok_handler({})})
    runner.enqueue_batch('import', [JobSpec('fake')])
    old = _claim(runner.repo, 'alive', 0)
    runner.clock = _clock(180)
    original = runner.repo.expired_running_ingest_jobs

    def interleave(cutoff):
        expired = original(cutoff)
        assert runner.repo.heartbeat_ingest_job(
            old['id'], owner=JobOwner('alive', 1), clock=runner.clock,
        )
        return expired

    monkeypatch.setattr(runner.repo, 'expired_running_ingest_jobs', interleave)
    assert runner.recover_stale_leases() == []
    assert runner.repo.get_ingest_job(old['id'])['status'] == 'running'


def test_late_usage_is_retained_after_takeover_without_restoring_publication_authority(tmp_path):
    runner = _runner(tmp_path, handlers={"fake": _ok_handler({})})
    runner.enqueue_batch("import", [JobSpec("fake")])
    old = _claim(runner.repo, "old", 0)
    with guard_ingest_writes(runner.repo.sqlite_path, old["id"], "old", 1):
        runner.repo.record_model_event("start", {"id": "paid-call", "purpose": "chat_request", "started_at": utc_now_iso(_clock(0))}, owner_kind="ingest_job", owner_id=old["id"])
    runner.clock = _clock(180)
    runner.recover_stale_leases()
    with guard_ingest_writes(runner.repo.sqlite_path, old["id"], "old", 1):
        event = {"id": "paid-call", "status": "completed", "finished_at": utc_now_iso(_clock(181)), "output_tokens": 50, "cost": 0.01}
        runner.repo.record_model_event("finish", event, owner_kind="ingest_job", owner_id="different-job")
        runner.repo.record_model_event("finish", event, owner_kind="ingest_job", owner_id=old["id"])
        with pytest.raises(JobOwnershipLost):
            runner.repo.update_ingest_job_payload(old["id"], {"stale": True})
    with runner.repo.connection() as connection:
        row = connection.execute("SELECT status,output_tokens,cost FROM model_call_receipts WHERE id='paid-call'").fetchone()
    assert tuple(row) == ("completed", 50, 0.01)


@pytest.mark.parametrize('survives', [False, True])
def test_fast_restart_reconciles_later_expiry_without_replacing_live_work(tmp_path, survives):
    runner = _runner(tmp_path, handlers={'fake': _ok_handler({})})
    batch = runner.enqueue_batch('import', [JobSpec('fake')])
    claimed = _claim(runner.repo, 'previous', 0)
    host = DurableIngestJobs()
    host.bind(runner.repo, tmp_path, clock=_clock(30), background=False)
    host._runner.handlers['fake'] = _ok_handler({})
    assert runner.repo.get_ingest_job(claimed['id'])['status'] == 'running'
    host._runner.clock = _clock(180)
    if survives:
        runner.repo.heartbeat_ingest_job(claimed['id'], owner=JobOwner('previous', 1), clock=_clock(180))
    host.drain_foreground()
    assert runner.repo.get_ingest_job(claimed['id'])['status'] == ('running' if survives else 'failed')
    if not survives:
        host._runner.resume_batch(batch)
        assert host.drain_foreground() == 1
        assert runner.repo.get_ingest_job(claimed['id'])['status'] == 'completed'


def test_heartbeat_keeps_renewing_after_a_transient_database_error(tmp_path, monkeypatch):
    import sqlite3
    import threading

    from learnloop.content.pipeline.runner import IngestRunner

    repo = Repository(tmp_path / 'state.sqlite')
    renewals_after_failure = threading.Event()
    attempts = []
    original = repo.heartbeat_ingest_job

    def flaky_heartbeat(job_id, **kwargs):
        attempts.append(job_id)
        if len(attempts) == 1:
            raise sqlite3.OperationalError('database is locked')
        if len(attempts) >= 3:
            renewals_after_failure.set()
        return original(job_id, **kwargs)

    monkeypatch.setattr(repo, 'heartbeat_ingest_job', flaky_heartbeat)

    def long_provider_call(ctx):
        # No ctx.report() here: only the heartbeat thread renews the lease.
        assert renewals_after_failure.wait(5), 'heartbeat stopped after one failed renewal'
        return {}

    runner = IngestRunner(
        repo, vault_root=tmp_path, worker_id='w', clock=_clock(0),
        handlers={'fake': long_provider_call}, heartbeat_interval_seconds=0.01,
    )
    batch = runner.enqueue_batch('import', [JobSpec('fake')])
    runner.drain()
    assert repo.ingest_jobs_for_batch(batch)[0]['status'] == 'completed'


def test_recovery_in_the_same_process_never_fails_a_live_attempt(tmp_path):
    import threading

    outcome = {}

    def long_provider_call(ctx):
        # Another lane of this process runs recovery long after the lease
        # expired; no heartbeat renewed it in between.
        other_lane = _runner(tmp_path, worker_id=ctx.worker_id, clock=_clock(600), handlers={})
        lane = threading.Thread(target=lambda: outcome.update(recovered=other_lane.recover_stale_leases()))
        lane.start()
        lane.join()
        ctx.repo.update_ingest_job_payload(ctx.job_id, {'published': True})
        return {}

    runner = _runner(tmp_path, handlers={'fake': long_provider_call})
    runner.heartbeat_interval_seconds = 3600
    batch = runner.enqueue_batch('import', [JobSpec('fake')])
    runner.drain()
    job = runner.repo.ingest_jobs_for_batch(batch)[0]
    assert outcome['recovered'] == []
    assert job['status'] == 'completed'
    assert job['payload'] == {'published': True}


def test_a_replaced_attempt_interrupts_only_its_own_transport(tmp_path):
    import threading

    from learnloop.ai.transport import INTERRUPT

    class Transport:
        def __init__(self):
            self.interrupted = False

        def interrupt(self):
            self.interrupted = True

        def supports(self, capability):
            return capability == INTERRUPT

    runner = _runner(tmp_path, handlers={'fake': _ok_handler({})})
    batch = runner.enqueue_batch('import', [JobSpec('fake')])
    first = _claim(runner.repo, runner.worker_id, 0)
    stale_transport = Transport()
    runner._bind_job_interruptible(first['id'], 1, stale_transport)
    # The first attempt's lease expires; another lane of the same runner
    # claims the resumed job as attempt 2.
    runner.clock = _clock(180)
    runner.resume_batch(batch)
    second = _claim(runner.repo, runner.worker_id, 180)
    assert second['attempt_count'] == 2
    live_transport = Transport()
    runner._bind_job_interruptible(second['id'], 2, live_transport)

    # The first attempt's heartbeat observes the loss and stops its own call.
    runner.heartbeat_interval_seconds = 0.01
    stop = threading.Event()
    runner._heartbeat_while_running(first['id'], stop, JobOwner(runner.worker_id, 1))
    runner._clear_job_interruptible(first['id'], 1)
    assert stale_transport.interrupted
    assert not live_transport.interrupted

    # Cancelling the job still reaches the live attempt's transport.
    assert runner.interrupt_job(second['id'])
    assert live_transport.interrupted


def test_a_replaced_attempt_still_saves_its_paid_checkpoint(tmp_path):
    runner = _runner(tmp_path, handlers={'fake': _ok_handler({})})
    runner.enqueue_batch('import', [JobSpec('fake')])
    old = _claim(runner.repo, 'old', 0)
    runner.clock = _clock(180)
    assert runner.recover_stale_leases() == [old['id']]
    with guard_ingest_writes(runner.repo.sqlite_path, old['id'], 'old', 1):
        runner.repo.save_model_checkpoint('window-key', purpose='inventory_window', result={'paid': True})
        with pytest.raises(JobOwnershipLost):
            runner.repo.update_ingest_job_payload(old['id'], {'stale': True})
    assert runner.repo.model_checkpoint('window-key') == {'result': {'paid': True}, 'usage': {}}


def test_a_cte_read_is_not_fenced_but_a_cte_write_is(tmp_path):
    runner = _runner(tmp_path, handlers={'fake': _ok_handler({})})
    runner.enqueue_batch('import', [JobSpec('fake')])
    old = _claim(runner.repo, 'old', 0)
    runner.clock = _clock(180)
    runner.recover_stale_leases()
    with guard_ingest_writes(runner.repo.sqlite_path, old['id'], 'old', 1):
        with runner.repo.connection() as connection:
            rows = connection.execute(
                "WITH ids AS (SELECT id FROM ingest_jobs) "
                "SELECT replace(id, 'ijob_', '') FROM ids WHERE 'update' <> 'delete from'"
            ).fetchall()
            assert len(rows) == 1
            # A read takes no write lock, so it cannot wait behind a writer.
            assert not connection.in_transaction
            with pytest.raises(JobOwnershipLost):
                connection.execute(
                    "WITH ids AS (SELECT id FROM ingest_jobs) "
                    "UPDATE ingest_jobs SET message = 'stale' WHERE id IN (SELECT id FROM ids)"
                )


def test_a_busy_vault_lock_defers_lease_work_instead_of_failing(tmp_path, monkeypatch):
    from learnloop.content.pipeline import runner as runner_module

    monkeypatch.setattr(runner_module, '_LEASE_LOCK_TIMEOUT_S', 0.2)
    monkeypatch.setattr(runner_module, '_TICK_EXPIRY_LOCK_TIMEOUT_S', 0.05)
    runner = _runner(tmp_path, handlers={'fake': _ok_handler({})})
    batch = runner.enqueue_batch('import', [JobSpec('fake')])
    stale = _claim(runner.repo, 'previous', 0)
    host = DurableIngestJobs()
    with vault_mutation_lock(tmp_path, purpose='long_apply'):
        # Opening the vault, draining and resuming all tolerate the busy lock.
        host.bind(runner.repo, tmp_path, clock=_clock(180), background=False)
        host._runner.handlers['fake'] = _ok_handler({})
        assert host._runner.run_next() is False
        host._runner.resume_batch(batch)
        assert runner.repo.get_ingest_job(stale['id'])['status'] == 'running'
    host._runner.resume_batch(batch)
    assert host.drain_foreground() == 1
    assert runner.repo.get_ingest_job(stale['id'])['status'] == 'completed'


def test_synthesis_run_hygiene_runs_at_startup_but_not_on_drain_ticks(tmp_path):
    from datetime import UTC, datetime

    from learnloop.clock import FrozenClock
    from learnloop.content.synthesis.synthesis_manifests import build_manifest, persist_manifest
    from learnloop.vault.loader import load_vault
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / 'vault')
    repository = Repository(paths.sqlite_path)
    manifest_id = persist_manifest(repository, build_manifest(load_vault(paths.root), source_set_id='ss1'))
    # A synchronous RPC/CLI synthesis has a run row but no ingest job lease.
    in_flight = repository.insert_synthesis_run(
        manifest_id=manifest_id, mode='bootstrap', clock=FrozenClock(datetime(2026, 7, 13, 11, 0, tzinfo=UTC)),
    )
    runner = _runner(paths.root, handlers={})
    assert runner.repo.sqlite_path == paths.sqlite_path
    for seconds in (0, 5, 10):
        runner.clock = _clock(seconds)
        assert runner.run_next() is False
    assert repository.synthesis_run(in_flight)['status'] == 'created'
    assert runner.recover_stale_leases() == []
    assert repository.synthesis_run(in_flight)['status'] == 'failed'


def test_a_replaced_ingest_cannot_publish_its_source_note_or_goal_linkage(tmp_path):
    from learnloop.content.pipeline import source_ingestion
    from tests.helpers import create_basic_vault
    from tests.test_source_ingestion import _youtube_source

    paths = create_basic_vault(tmp_path / 'vault')
    runner = _runner(paths.root, handlers={'fake': _ok_handler({})})
    runner.enqueue_batch('legacy_ingest', [JobSpec('fake')])
    old = _claim(runner.repo, 'old', 0)
    runner.clock = _clock(180)
    runner.recover_stale_leases()
    goals_before = paths.goals_path.read_text() if paths.goals_path.exists() else None
    notes_before = sorted(paths.root.rglob('*.md'))
    source = _youtube_source()
    with guard_ingest_writes(runner.repo.sqlite_path, old['id'], 'old', 1):
        with pytest.raises(JobOwnershipLost):
            source_ingestion.register_canonical_source(
                paths.root, 'linear-algebra', source, b'raw transcript', 'sha256:late', clock=_clock(181),
            )
        with pytest.raises(JobOwnershipLost):
            source_ingestion._establish_goal_linkage(
                paths.root, 'linear-algebra', 'Late source', None,
                goal_id=None, default_priority=1.0, clock=_clock(181),
            )
    assert sorted(paths.root.rglob('*.md')) == notes_before
    assert (paths.goals_path.read_text() if paths.goals_path.exists() else None) == goals_before
