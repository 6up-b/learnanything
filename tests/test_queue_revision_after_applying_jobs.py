"""A client that polls only the queue revision learns of the practice an applying job wrote.

The phone polls ``/api/v1/queue-revision``, a read-only read of ``Repository.queue_revision`` that never reloads
(``learnloop_mobile.host``); only the desktop's ``get_queue_revision`` reloads after an applying job and answers
``reloaded``. So a job that writes scheduler-visible practice must bump the revision when it completes, or the
phone keeps its Today without the new item. Each test runs a job type that writes practice through the ingest
runner and reads only the revision, as the phone does.
"""

from __future__ import annotations

from typing import Any

import pytest

from learnloop.content.pipeline.runner import IngestRunner, JobSpec, RunnerServices
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from tests.helpers import add_followup_item, create_basic_vault


class _Applied:
    codex_calls = 0

    def as_dict(self) -> dict[str, Any]:
        return {"proposal_id": "patch_test", "auto_applied_count": 1}


@pytest.mark.parametrize("job_type", ["legacy_ingest", "exam_ingest"])
def test_a_legacy_ingest_that_applies_practice_moves_the_revision(tmp_path, job_type):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)

    def run_legacy(*, vault_root, **_kwargs):
        # What ingest_canonical_source's auto-apply does to the vault: a practice item written.
        add_followup_item(vault_root, "pi_applied_by_ingest")
        return _Applied()

    runner = IngestRunner(repository, vault_root=paths.root, worker_id="w",
                          services=RunnerServices(run_legacy_ingest=run_legacy))
    runner.enqueue_batch(job_type, [JobSpec(job_type, {"source": "notes.md", "subject_id": "linear-algebra",
                                                       "mode": "exam" if job_type == "exam_ingest" else "canonical"})])
    before = repository.queue_revision()["revision"]
    runner.drain()
    (job,) = repository.ingest_jobs_by_types((job_type,))
    assert job["status"] == "completed", job.get("error")
    assert "pi_applied_by_ingest" in load_vault(paths.root).practice_items
    assert repository.queue_revision()["revision"] > before


def test_a_picked_source_exercise_written_as_practice_moves_the_revision(tmp_path, monkeypatch):
    from learnloop.content.pipeline.jobs import DurableIngestJobs
    from learnloop.instructional.exercises import exercise_key
    from tests.source_exercise_rpcs_helpers import proposal_row
    from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, call

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    span = spans["exercises"][1]
    exercise = {"kind": "source_exercise", "key": exercise_key("ext_text", [span]), "extraction_id": "ext_text",
                "span_ids": [span], "source_id": "src_text", "revision_id": "rev_text", "label": "Exercise 1",
                "page": 9, "statement": "1. An eigenvalue t satisfies 3t + 5 = 20", "relevance": "relevant",
                "rationale": "fits", "provisional": {"facets": ["facet_determinant"], "practice_mode": "short_answer"}}
    proposal_row(repository, proposal_id="pp_pick", constraints={"facet_ids": ["facet_determinant"]},
                 intent="practice", exercise=exercise)
    queued: dict[str, Any] = {}
    monkeypatch.setattr(DurableIngestJobs, "enqueue_source_exercise_import",
                        lambda self, **kwargs: queued.update(kwargs) or "batch_1")
    call(paths.root, "import_source_exercise", {"proposalId": "pp_pick", "extractionId": "ext_text",
                                                "spanIds": [span]})
    runner = IngestRunner(repository, vault_root=paths.root, worker_id="w", services=RunnerServices(
        exercise_import_client_factory=lambda _ctx: FakeServiceLLM(), background_key_checks=False))
    runner.enqueue_batch("source_exercise_import",
                         [JobSpec("source_exercise_import", {**queued, "caller": "learner"})])
    before = repository.queue_revision()["revision"]
    items_before = set(load_vault(paths.root).practice_items)
    runner.drain()
    (job,) = repository.ingest_jobs_by_types(("source_exercise_import",))
    assert job["status"] == "completed", job.get("error")
    assert job["result"]["status"] == "written"
    assert set(load_vault(paths.root).practice_items) - items_before == {job["result"]["practice_item_id"]}
    assert repository.queue_revision()["revision"] > before


def test_completed_practice_and_revision_are_visible_together(tmp_path, monkeypatch):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    observer = Repository(paths.sqlite_path)
    observations = []
    before = observer.queue_revision()["revision"]
    finish = repository.finish_owned_ingest_job

    def observe_terminal(job_id, **kwargs):
        result = finish(job_id, **kwargs)
        if observer.get_ingest_job(job_id)["status"] == "completed":
            observations.append(observer.queue_revision()["revision"])
        return result

    def ingest(*, vault_root, **_):
        add_followup_item(vault_root, "pi_new")
        return _Applied()

    monkeypatch.setattr(repository, "finish_owned_ingest_job", observe_terminal)
    runner = IngestRunner(repository, vault_root=paths.root, worker_id="w",
                          services=RunnerServices(run_legacy_ingest=ingest))
    runner.enqueue_batch("legacy_ingest", [JobSpec("legacy_ingest", {"source": "notes.md",
                                                                    "subject_id": "linear-algebra"})])
    runner.drain()
    assert observer.queue_revision()["revision"] > before
    assert before not in observations


def test_identical_legacy_source_does_not_publish_another_revision(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repo = Repository(paths.sqlite_path)

    def reused(**_):
        return {"reused_existing": True, "auto_applied_count": 0}

    runner = IngestRunner(repo, vault_root=paths.root, worker_id="w", services=RunnerServices(run_legacy_ingest=reused))
    runner.enqueue_batch("legacy_ingest", [JobSpec("legacy_ingest", {"source": "notes.md",
                                                                    "subject_id": "linear-algebra"})])
    before = repo.queue_revision()["revision"]
    runner.drain()
    assert repo.ingest_jobs_by_types(("legacy_ingest",))[0]["status"] == "completed"
    assert repo.queue_revision()["revision"] == before


def test_cancellation_after_the_legacy_write_publishes_the_new_practice(tmp_path):
    from learnloop.content.pipeline.runner import JobCancelled

    paths = create_basic_vault(tmp_path / "vault")
    repo = Repository(paths.sqlite_path)

    def ingest(*, vault_root, **_):
        add_followup_item(vault_root, "pi_cancelled_ingest")
        raise JobCancelled("cancel after the write")

    runner = IngestRunner(repo, vault_root=paths.root, worker_id="w", services=RunnerServices(run_legacy_ingest=ingest))
    runner.enqueue_batch("legacy_ingest", [JobSpec("legacy_ingest", {"source": "notes.md",
                                                                    "subject_id": "linear-algebra"})])
    before = repo.queue_revision()["revision"]
    runner.drain()
    assert repo.ingest_jobs_by_types(("legacy_ingest",))[0]["status"] == "cancelled"
    assert "pi_cancelled_ingest" in load_vault(paths.root).practice_items
    assert repo.queue_revision()["revision"] > before


@pytest.mark.parametrize("watch_during_job", [False, True])
def test_watcher_and_job_publish_the_same_new_practice_once(tmp_path, watch_during_job):
    from learnloop_sidecar.context import SidecarContext

    paths = create_basic_vault(tmp_path / "vault")
    ctx = SidecarContext()
    ctx.load(paths.root, maintenance=False)
    repo = ctx.repository
    filename = paths.practice_item_path("linear-algebra", "pi_shared").relative_to(paths.root).as_posix()

    def ingest(*, vault_root, **_):
        add_followup_item(vault_root, "pi_shared")
        if watch_during_job:
            ctx.refresh_vault_files([filename])
        return _Applied()

    runner = IngestRunner(repo, vault_root=paths.root, worker_id="w", services=RunnerServices(run_legacy_ingest=ingest))
    runner.enqueue_batch("legacy_ingest", [JobSpec("legacy_ingest", {"source": "notes.md", "subject_id": "linear-algebra"})])
    before = repo.queue_revision()["revision"]
    runner.drain()
    if not watch_during_job:
        ctx.refresh_vault_files([filename])
    assert repo.ingest_jobs_by_types(("legacy_ingest",))[0]["status"] == "completed"
    assert repo.queue_revision()["revision"] == before + 1


def test_overlapping_imports_publish_one_shared_write(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repo = Repository(paths.sqlite_path)
    payload = {"source": "notes.md", "subject_id": "linear-algebra"}

    def second_import(*, vault_root, **_):
        add_followup_item(vault_root, "pi_shared")
        return _Applied()

    def first_import(**_):
        second = IngestRunner(Repository(paths.sqlite_path), vault_root=paths.root, worker_id="second",
                              services=RunnerServices(run_legacy_ingest=second_import))
        second.enqueue_batch("exam_ingest", [JobSpec("exam_ingest", {**payload, "mode": "exam"})])
        second.drain(max_jobs=1, eligible_job_types=("exam_ingest",), allow_parallel=True)
        return _Applied()

    first = IngestRunner(repo, vault_root=paths.root, worker_id="first", services=RunnerServices(run_legacy_ingest=first_import))
    first.enqueue_batch("legacy_ingest", [JobSpec("legacy_ingest", payload)])
    before = repo.queue_revision()["revision"]
    first.drain(max_jobs=1)
    assert [j["status"] for j in repo.ingest_jobs_by_types(("legacy_ingest", "exam_ingest"))] == ["completed"] * 2
    assert repo.queue_revision()["revision"] == before + 1


def test_import_rewriting_identical_practice_bytes_keeps_the_revision(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repo = Repository(paths.sqlite_path)
    add_followup_item(paths.root, "pi_same")
    practice = paths.practice_item_path("linear-algebra", "pi_same")

    def rewrite(**_):
        practice.write_bytes(practice.read_bytes())
        return _Applied()

    runner = IngestRunner(repo, vault_root=paths.root, worker_id="w", services=RunnerServices(run_legacy_ingest=rewrite))
    runner.enqueue_batch("legacy_ingest", [JobSpec("legacy_ingest", {"source": "notes.md", "subject_id": "linear-algebra"})])
    before = repo.queue_revision()["revision"]
    runner.drain()
    assert repo.ingest_jobs_by_types(("legacy_ingest",))[0]["status"] == "completed"
    assert repo.queue_revision()["revision"] == before
