"""A section writes bounded, durable answers and applies one jointly judged proposal."""
from __future__ import annotations

from dataclasses import replace

import pytest

from learnloop.content.authoring.practice_generation import generate_post_probe_practice_proposal
from learnloop.content.proposals import proposals
from tests.section_question_parts_helpers import (
    TOPICS, Writer, comparable_rows, enqueue, jobs_for, live_questions, request_digest, section,
)


@pytest.fixture(autouse=True)
def fixed_request_root(monkeypatch):
    build = proposals.build_authoring_context
    monkeypatch.setattr(proposals, "build_authoring_context", lambda *a, **kw: replace(
        build(*a, **kw), vault_root="/synthetic-vault"))


def test_six_topics_resume_at_the_third_answer_and_match_the_old_proposal(tmp_path, monkeypatch):
    monkeypatch.setattr("learnloop.content.pipeline.runner.retries_on_its_own", lambda job: False)
    paths, repo = section(tmp_path / "parts")
    writer = Writer(fail={3})
    jobs = jobs_for(paths, repo, writer)

    def no_early_apply():
        assert not live_questions(paths)

    writer.before = no_early_apply
    batch = enqueue(jobs)
    job = repo.ingest_jobs_for_batch(batch)[0]
    assert job["status"] == "failed"
    assert writer.calls == [[lo] for lo in TOPICS[:3]]
    assert not live_questions(paths)
    from learnloop.clock import FrozenClock
    from learnloop.vault.loader import add_note
    from tests.helpers import NOW

    add_note(paths.root, "linear-algebra", "unrelated", "Unrelated", "New context during the retry.",
             clock=FrozenClock(NOW))
    jobs.resume_batch(batch)
    job = repo.ingest_jobs_for_batch(batch)[0]
    assert job["status"] == "completed", job
    assert writer.calls == [[lo] for lo in TOPICS[:3] + TOPICS[2:]]

    old_paths, old_repo = section(tmp_path / "whole")
    old = generate_post_probe_practice_proposal(old_paths.root, Writer(), learning_object_ids=TOPICS,
                                              require_completed_probe=False, target_items_per_lo=3)
    assert comparable_rows(repo, job["result"]["patch_id"]) == comparable_rows(old_repo, old.patch_id)
    assert live_questions(paths) == live_questions(old_paths)
    assert len(live_questions(paths)) == 6


def test_later_rebuild_reuses_the_finished_section(tmp_path):
    paths, repo = section(tmp_path)
    writer = Writer()
    jobs = jobs_for(paths, repo, writer)
    first = enqueue(jobs)
    assert repo.ingest_jobs_for_batch(first)[0]["status"] == "completed"
    calls = len(writer.calls)
    second = enqueue(jobs)
    assert len(writer.calls) == calls
    assert repo.ingest_jobs_for_batch(first)[0]["result"] == repo.ingest_jobs_for_batch(second)[0]["result"]


def test_one_topic_request_bytes_and_checkpoint_reuse(tmp_path):
    paths, repo = section(tmp_path, 1)
    writer = Writer()
    jobs = jobs_for(paths, repo, writer)
    enqueue(jobs, 1)
    assert request_digest(writer.requests[0]) == "37a5f8e07262bc797fe344c59601ad0387b65a895e24cb10e92678d4a0208c4b"
    enqueue(jobs, 1)
    assert len(writer.requests) == 1


def test_repair_answer_is_saved_before_downstream_failure(tmp_path, monkeypatch):
    paths, repo = section(tmp_path, 1)
    writer = Writer(invalid=True)
    jobs = jobs_for(paths, repo, writer)
    original = proposals.auto_apply_rows
    monkeypatch.setattr(proposals, "auto_apply_rows", lambda *a: (_ for _ in ()).throw(RuntimeError("lost apply")))
    batch = enqueue(jobs, 1)
    assert repo.ingest_jobs_for_batch(batch)[0]["status"] == "failed"
    assert writer.calls == [[TOPICS[0]], []]
    monkeypatch.setattr(proposals, "auto_apply_rows", original)
    jobs.resume_batch(batch)
    assert repo.ingest_jobs_for_batch(batch)[0]["status"] == "completed"
    assert writer.calls == [[TOPICS[0]], []]


def test_duplicate_prompts_across_parts_are_not_auto_applied(tmp_path):
    paths, repo = section(tmp_path, 2)
    writer = Writer(duplicate=True)
    jobs = jobs_for(paths, repo, writer)
    batch = enqueue(jobs, 2)
    job = repo.ingest_jobs_for_batch(batch)[0]
    assert job["status"] == "completed", job
    assert not live_questions(paths)
    rows = repo.proposal_items(job["result"]["patch_id"])
    assert all("duplicate_prompt" in row["validation_errors"] for row in rows)


def test_automatic_retry_asks_only_for_unsaved_topics(tmp_path):
    paths, repo = section(tmp_path)
    writer = Writer(fail={3})
    jobs = jobs_for(paths, repo, writer)
    batch = enqueue(jobs)
    assert repo.ingest_jobs_for_batch(batch)[0]["status"] == "completed"
    assert writer.calls == [[lo] for lo in TOPICS[:3] + TOPICS[2:]]


def test_two_timeouts_keep_progress_for_try_again(tmp_path):
    paths, repo = section(tmp_path)
    writer = Writer(fail={3, 4})
    jobs = jobs_for(paths, repo, writer)
    batch = enqueue(jobs)
    job = repo.ingest_jobs_for_batch(batch)[0]
    assert job["status"] == "failed"
    assert (job["current_window"], job["total_windows"]) == (2, 6)
    assert not live_questions(paths)
    jobs.resume_batch(batch)
    assert writer.calls == [[lo] for lo in TOPICS[:3] + TOPICS[2:3] + TOPICS[2:]]
    job = repo.ingest_jobs_for_batch(batch)[0]
    assert job["status"] == "completed"
    assert (job["current_window"], job["total_windows"]) == (6, 6)


def test_collected_proposal_matches_whole_answer_before_apply(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(proposals, "auto_apply_rows", lambda root, patch, rows: seen.append(rows))
    paths, repo = section(tmp_path / "parts")
    writer = Writer()
    batch = enqueue(jobs_for(paths, repo, writer))
    patch = repo.ingest_jobs_for_batch(batch)[0]["result"]["patch_id"]
    old_paths, old_repo = section(tmp_path / "whole")
    old = generate_post_probe_practice_proposal(old_paths.root, Writer(), learning_object_ids=TOPICS,
                                              require_completed_probe=False, target_items_per_lo=3)
    assert comparable_rows(repo, patch) == comparable_rows(old_repo, old.patch_id)
    assert len(seen) == 2
    assert all(row["_auto_apply"] for rows in seen for row in rows)
    assert writer.calls == [[lo] for lo in TOPICS]


def test_topic_order_follows_first_cited_span(tmp_path):
    from learnloop.reader.section_generation import section_generation_candidates
    from learnloop.vault.models import SourceRef
    from tests.reader_guidance_helpers import _setup

    vault, repo = _setup(tmp_path)
    template = vault.learning_objects["lo_svd_definition"]
    vault.learning_objects.clear()
    for lo, span in [("lo_a", "s2"), ("lo_z", "s0"), ("lo_m", "s1")]:
        topic = template.model_copy(deep=True, update={"id": lo})
        topic.provenance.source_refs = [SourceRef(ref_type="canonical_source", ref_id="src1",
                                               locator=f"span:ext1/{span}", source_id="src1", extraction_id="ext1")]
        vault.learning_objects[lo] = topic
    assert section_generation_candidates(vault, repo, extraction_id="ext1", section_id="u1") == ["lo_z", "lo_m", "lo_a"]
