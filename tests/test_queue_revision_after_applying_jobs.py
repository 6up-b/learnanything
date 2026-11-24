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
