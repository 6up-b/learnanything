"""A section's quick check whose writing failed is said by the guide plan.

The Reader polled the guide plan while a section's check was written, and the
plan carried no failed state: a failed job read as "still writing" until the
poll gave up minutes later, and after the Reader reopened as nothing at all.
``reader.guide_plan`` now names the sections whose newest section-check job
failed (``checkFailedSectionIds``), so the Reader says so with Try again, at
the next poll and after reopening. A read of the job queue only.
"""

from __future__ import annotations

from learnloop.reader.reader_guidance import build_guide_plan
from learnloop_sidecar.context import SidecarContext
from tests.reader_guidance_helpers import _setup


def _plan(tmp_path) -> dict:
    import learnloop_sidecar.handlers  # noqa: F401 - registers the methods
    from learnloop_sidecar.registry import METHOD_REGISTRY

    ctx = SidecarContext()
    ctx.load(tmp_path / "vault")
    spec = METHOD_REGISTRY["reader.guide_plan"]
    return spec.handler(ctx, spec.params_model.model_validate({"extractionId": "ext1"}))


def _job(repository, job_id: str, payload: dict, status: str) -> None:
    batch_id = f"batch_{job_id}"
    repository.insert_ingest_batch(id=batch_id, workflow_type="reader_quick_check")
    repository.insert_ingest_job(id=job_id, batch_id=batch_id, ordinal=0, job_type="reader_quick_check", payload=payload)
    if status != "queued":
        repository.transition_unleased_ingest_job(
            job_id, status=status, error={"code": "provider_error", "message": "overloaded"} if status == "failed" else None,
        )


def _section(vault, repository) -> str:
    return build_guide_plan(vault, repository, extraction_id="ext1")["sections"][0]["id"]


def test_a_section_whose_check_failed_is_named(tmp_path):
    vault, repository = _setup(tmp_path)
    section = _section(vault, repository)
    _job(repository, "job_1", {"extraction_id": "ext1", "section_id": section}, "failed")

    assert _plan(tmp_path)["checkFailedSectionIds"] == [section]


def test_a_newer_try_for_the_section_replaces_the_failure(tmp_path):
    vault, repository = _setup(tmp_path)
    section = _section(vault, repository)
    _job(repository, "job_1", {"extraction_id": "ext1", "section_id": section}, "failed")
    # Try again queues a new job; until it ends the section is being written, not failed.
    with repository.connection() as connection:
        connection.execute("UPDATE ingest_jobs SET created_at = '2000-01-01T00:00:00Z' WHERE id = 'job_1'")
        connection.commit()
    _job(repository, "job_2", {"extraction_id": "ext1", "section_id": section}, "queued")

    assert _plan(tmp_path)["checkFailedSectionIds"] == []


def test_other_checks_failing_name_no_section(tmp_path):
    vault, repository = _setup(tmp_path)
    section = _section(vault, repository)
    # A passage check (no section), the same section id of another reading, and a section check that completed.
    _job(repository, "job_inquiry", {"scope_kind": "inquiry", "extraction_id": "ext1", "inquiry_root_event_id": "ev_1",
                                     "anchor_span_ids": ["s1"]}, "failed")
    _job(repository, "job_other", {"extraction_id": "ext_other", "section_id": section}, "failed")
    _job(repository, "job_done", {"extraction_id": "ext1", "section_id": "no_such_section"}, "completed")

    assert _plan(tmp_path)["checkFailedSectionIds"] == []
