"""Parallel inventory: workers hand SQL to the runner thread through a mailbox."""

from __future__ import annotations

from learnloop.db.repositories import Repository
from tests.test_source_inventory import FakeInventoryClient, _block, _ir, _persist, _register_revision, _CLOCK


def test_keyboard_interrupt_during_parallel_inventory_releases_waiting_workers(tmp_path, monkeypatch):
    import threading
    from learnloop.content.pipeline import jobs
    from learnloop.content.pipeline.runner import IngestRunner, JobSpec, RunnerServices
    repo = Repository(tmp_path / "state.sqlite")
    _register_revision(repo)
    document = _ir([(f"u{n}", f"Chapter {n}", [_block(f"s{n}", f"Eigenvector section {n}.")], f"hash{n}", n) for n in range(1, 3)])
    _persist(repo, document, revision_id="rev1", extraction_id="ext1")
    monkeypatch.setattr(jobs, "_MAX_INVENTORY_WORKERS", 2)
    in_provider = threading.Semaphore(0)
    release_providers = threading.Event()
    interrupt_runner = threading.Event()

    class Client(FakeInventoryClient):
        def run_source_unit_inventory(self, context):
            in_provider.release()
            release_providers.wait(5)
            return super().run_source_unit_inventory(context)

    real_answer_pending = jobs._RunnerMailbox.answer_pending

    def answer_pending(self, **kwargs):
        # Ctrl-C lands on the runner thread while it waits on its workers.
        if interrupt_runner.is_set():
            interrupt_runner.clear()
            raise KeyboardInterrupt()
        return real_answer_pending(self, **kwargs)

    monkeypatch.setattr(jobs._RunnerMailbox, "answer_pending", answer_pending)
    runner = IngestRunner(repo, vault_root=tmp_path, worker_id="worker", clock=_CLOCK, services=RunnerServices(inventory_client_factory=lambda ctx: Client()))
    runner.enqueue_batch("import_inventory", [JobSpec("inventory", {"extraction_id": "ext1", "units": [{"unit_id": "u1", "role": "reference"}, {"unit_id": "u2", "role": "reference"}]})])
    finished = threading.Event()
    raised = []

    def drain():
        try:
            runner.drain()
        except BaseException as exc:
            raised.append(type(exc))
        finally:
            finished.set()

    runner_thread = threading.Thread(target=drain, daemon=True)
    runner_thread.start()
    assert in_provider.acquire(timeout=5) and in_provider.acquire(timeout=5)
    interrupt_runner.set()
    threading.Event().wait(0.3)
    # The workers' next step asks the runner to record their call and save
    # their checkpoint; nothing on the runner thread answers any more.
    release_providers.set()
    assert finished.wait(10), "inventory workers waited forever for a stopped runner"
    assert raised == [KeyboardInterrupt]


def test_parallel_inventory_notices_cancellation_without_polling_the_database_constantly(tmp_path, monkeypatch):
    import threading
    from learnloop.content.pipeline import jobs
    from learnloop.content.pipeline.runner import IngestRunner, JobContext, JobSpec, RunnerServices
    repo = Repository(tmp_path / "state.sqlite")
    _register_revision(repo)
    document = _ir([(f"u{n}", f"Chapter {n}", [_block(f"s{n}", f"Eigenvector section {n}.")], f"hash{n}", n) for n in range(1, 3)])
    _persist(repo, document, revision_id="rev1", extraction_id="ext1")
    monkeypatch.setattr(jobs, "_MAX_INVENTORY_WORKERS", 2)
    both_in_provider = threading.Barrier(3)
    cancel_seen = threading.Event()
    cancellation_checks = []
    original_cancelled = JobContext.cancelled

    def counting_cancelled(self):
        cancellation_checks.append(threading.current_thread().name)
        cancelled = original_cancelled(self)
        if cancelled:
            cancel_seen.set()
        return cancelled

    monkeypatch.setattr(JobContext, "cancelled", counting_cancelled)

    class Client(FakeInventoryClient):
        def run_source_unit_inventory(self, context):
            both_in_provider.wait(5)
            assert cancel_seen.wait(5), "the runner never noticed the cancellation"
            return super().run_source_unit_inventory(context)

    runner = IngestRunner(repo, vault_root=tmp_path, worker_id="worker", clock=_CLOCK, services=RunnerServices(inventory_client_factory=lambda ctx: Client()))
    batch = runner.enqueue_batch("import_inventory", [JobSpec("inventory", {"extraction_id": "ext1", "units": [{"unit_id": "u1", "role": "reference"}, {"unit_id": "u2", "role": "reference"}]})])
    drain = threading.Thread(target=runner.drain, name="runner")
    drain.start()
    both_in_provider.wait(5)
    threading.Event().wait(1.0)
    checks_while_idle = len(cancellation_checks)
    runner.cancel_batch(batch)
    drain.join(10)
    assert not drain.is_alive()
    assert repo.ingest_jobs_for_batch(batch)[0]["status"] == "cancelled"
    # One second of waiting on provider calls costs a handful of checks, not twenty.
    assert checks_while_idle <= 8
