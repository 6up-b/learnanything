from __future__ import annotations

import pytest
pytestmark = pytest.mark.durability

from learnloop.clock import utc_now_iso
from learnloop.content.pipeline.jobs import DurableIngestJobs
from learnloop.content.pipeline.runner import JobSpec
from learnloop.db.repositories import Repository
from learnloop.db.scopes import JobOwnershipLost, guard_ingest_writes
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
    assert not runner.repo.heartbeat_ingest_job(old['id'], worker_id='old', attempt_count=1)
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
            old['id'], worker_id='alive', attempt_count=1, clock=runner.clock,
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
        runner.repo.heartbeat_ingest_job(claimed['id'], worker_id='previous', attempt_count=1, clock=_clock(180))
    host.drain_foreground()
    assert runner.repo.get_ingest_job(claimed['id'])['status'] == ('running' if survives else 'failed')
    if not survives:
        host._runner.resume_batch(batch)
        assert host.drain_foreground() == 1
        assert runner.repo.get_ingest_job(claimed['id'])['status'] == 'completed'
