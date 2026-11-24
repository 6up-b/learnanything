"""Publish practice written by an ingest job, including on lease recovery."""

import hashlib
import json
from pathlib import Path

PRACTICE_WRITERS = ("legacy_ingest", "exam_ingest", "source_exercise_import")


def practice_snapshot(root):
    files = {}
    for path in Path(root).glob("subjects/*/practice-items/*.yaml"):
        try:
            with path.open("rb") as stream:
                files[str(path.relative_to(root))] = hashlib.file_digest(stream, "sha256").hexdigest()
        except FileNotFoundError:
            continue
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def begin_practice_write(repo, root, job, owner):
    if job["job_type"] not in PRACTICE_WRITERS:
        return True
    with repo.atomic():
        current = repo.get_ingest_job(job["id"])
        if not current or (current["status"], current["worker_id"], current["attempt_count"]) != (
            "running", owner.worker_id, owner.attempt_count
        ):
            return False
        repo.update_ingest_job_payload(job["id"], {**current["payload"], "practice_snapshot": practice_snapshot(root),
                                                  "practice_start_revision": repo.queue_revision()["revision"]})
        return True


def publish_practice(repo, root, job_id, clock):
    """Called inside the terminal transition's transaction. An older running job has no baseline."""
    job = repo.get_ingest_job(job_id)
    before = job["payload"].get("practice_snapshot")
    current = practice_snapshot(root)
    if current != before:
        last_id = repo.latest_practice_snapshot_job(PRACTICE_WRITERS, published_only=True)
        last = repo.get_ingest_job(last_id)["payload"] if last_id else {}
        if last.get("practice_published") == current and last["practice_revision"] > job["payload"].get("practice_start_revision", -1):
            revision = last["practice_revision"]
        else:
            revision = repo.bump_queue_revision(clock=clock)
        repo.update_ingest_job_payload(job_id, {**job["payload"], "practice_snapshot": current,
                                               "practice_published": current, "practice_revision": revision})
    return repo.queue_revision()["revision"]


def publish_watched_practice(repo, root):
    with repo.atomic():
        job_id = repo.latest_practice_snapshot_job(PRACTICE_WRITERS)
        if job_id is None:
            return repo.bump_queue_revision()
        return publish_practice(repo, root, job_id, None)
