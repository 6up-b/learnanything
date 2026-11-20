"""A section offers each durable part immediately, preserving applied rows on retry."""
from __future__ import annotations

from dataclasses import replace

import pytest

from learnloop.content.authoring.practice_generation import generate_post_probe_practice_proposal
from learnloop.content.proposals import proposals
from tests.section_question_parts_helpers import (
    TOPICS, Writer, comparable_rows, enqueue, held_writer, jobs_for, live_questions, request_digest, section,
)


@pytest.fixture(autouse=True)
def fixed_request_root(monkeypatch):
    build = proposals.build_authoring_context
    monkeypatch.setattr(proposals, "build_authoring_context", lambda *a, **kw: replace(
        build(*a, **kw), vault_root="/synthetic-vault"))


def test_first_of_eight_topics_is_served_while_the_second_is_being_written(tmp_path):
    from learnloop.clock import FrozenClock
    from learnloop.scheduling.scheduler import build_due_queue
    from learnloop.vault.loader import load_vault
    from tests.helpers import NOW

    paths, repo = section(tmp_path)
    writer = Writer()
    observed = []

    def during_call():
        if len(writer.calls) == 2:
            queue = build_due_queue(load_vault(paths.root), repo, clock=FrozenClock(NOW))
            observed.extend(row.practice_item_id for row in queue)
            assert f"pi_{TOPICS[0]}" in observed
            assert live_questions(paths) == {f"pi_{TOPICS[0]}"}

    writer.before = during_call
    batch = enqueue(jobs_for(paths, repo, writer))
    assert repo.ingest_jobs_for_batch(batch)[0]["status"] == "completed"
    assert observed
    assert writer.calls == [[lo] for lo in TOPICS]


def test_invalid_fifth_topic_does_not_stop_the_rest_and_try_again_only_asks_it(tmp_path):
    paths, repo = section(tmp_path)
    writer = Writer(bad_topics={TOPICS[4]})
    jobs = jobs_for(paths, repo, writer)
    mixed = []

    def during_sixth():
        if len(writer.calls) == 6:
            active = repo.ingest_jobs_by_types(["practice_expansion"])[0]
            assert active["status"] == "running"
            assert (active["current_window"], active["total_windows"]) == (4, 8)
            assert active["payload"]["question_parts"][4]["error"]
            mixed.append(live_questions(paths))

    writer.before = during_sixth
    batch = enqueue(jobs)
    assert mixed == [{f"pi_{lo}" for lo in TOPICS[:4]}]
    job = repo.ingest_jobs_for_batch(batch)[0]
    assert job["status"] == "failed"
    assert writer.calls == [[lo] for lo in TOPICS] + [[TOPICS[4]]]
    assert live_questions(paths) == {f"pi_{lo}" for lo in TOPICS if lo != TOPICS[4]}
    assert TOPICS[4] in job["error"]["message"]
    assert (job["current_window"], job["total_windows"]) == (7, 8)
    from learnloop.clock import FrozenClock
    from learnloop.vault.loader import add_note
    from tests.helpers import NOW

    add_note(paths.root, "linear-algebra", "unrelated", "Unrelated", "New context during retry.",
             clock=FrozenClock(NOW))
    writer.bad_topics.clear()
    jobs.resume_batch(batch)
    assert writer.calls == [[lo] for lo in TOPICS] + [[TOPICS[4]]] * 2
    assert repo.ingest_jobs_for_batch(batch)[0]["status"] == "completed"
    assert len(live_questions(paths)) == 8
    assert request_digest(writer.requests[4]) == request_digest(writer.requests[8]) == request_digest(writer.requests[9])


def test_crash_after_apply_reuses_the_same_proposal_and_applies_nothing_twice(tmp_path, monkeypatch):
    paths, repo = section(tmp_path)
    writer = Writer()
    jobs = jobs_for(paths, repo, writer)
    original = proposals.auto_apply_rows
    seen = []

    def crash(root, patch, rows):
        original(root, patch, rows)
        seen.append(patch)
        raise RuntimeError("crash after apply before recording progress")

    monkeypatch.setattr(proposals, "auto_apply_rows", crash)
    batch = enqueue(jobs)
    assert repo.ingest_jobs_for_batch(batch)[0]["status"] == "failed"
    assert live_questions(paths) == {f"pi_{TOPICS[0]}"}
    assert len(writer.calls) == 1
    retried = []

    def track(root, patch, rows):
        retried.append(patch)
        original(root, patch, rows)

    monkeypatch.setattr(proposals, "auto_apply_rows", track)
    jobs.resume_batch(batch)
    assert seen[0] not in retried
    assert len(retried) == 7
    assert repo.ingest_jobs_for_batch(batch)[0]["status"] == "completed"
    assert writer.calls == [[lo] for lo in TOPICS]
    assert len(repo.proposal_batches()) == 8
    rows = repo.proposal_items(seen[0])
    assert all(row["decision"] == "accepted" for row in rows)


def test_later_rebuild_reuses_the_finished_section(tmp_path, monkeypatch):
    paths, repo = section(tmp_path)
    writer = Writer()
    jobs = jobs_for(paths, repo, writer)
    first = enqueue(jobs)
    assert repo.ingest_jobs_for_batch(first)[0]["status"] == "completed"
    calls = len(writer.calls)
    patches = repo.proposal_batches()
    assert len(patches) == 8
    monkeypatch.setattr(proposals, "auto_apply_rows", lambda *args: pytest.fail("rebuild applied again"))
    second = enqueue(jobs)
    assert repo.proposal_batches() == patches
    assert len(writer.calls) == calls
    assert repo.ingest_jobs_for_batch(first)[0]["result"] == repo.ingest_jobs_for_batch(second)[0]["result"]


def test_one_topic_request_bytes_and_checkpoint_reuse(tmp_path):
    paths, repo = section(tmp_path, 1)
    writer = Writer()
    jobs = jobs_for(paths, repo, writer)
    enqueue(jobs, 1)
    assert request_digest(writer.requests[0]) == "3ee763d8f71b89d1638787d9d5fa1328cfcd14aff21ba29f8b20c752fed72897"
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
    assert job["status"] == "failed", job
    assert live_questions(paths) == {f"pi_{TOPICS[0]}"}
    patches = [part["patch_id"] for part in job["payload"]["question_parts"]]
    assert "duplicate_prompt" in repo.proposal_items(patches[1])[0]["validation_errors"]
    assert repo.proposal_items(patches[0])[0]["decision"] == "accepted"


def test_automatic_retry_asks_only_for_unsaved_topics(tmp_path):
    paths, repo = section(tmp_path)
    writer = Writer(fail={3})
    jobs = jobs_for(paths, repo, writer)
    batch = enqueue(jobs)
    assert repo.ingest_jobs_for_batch(batch)[0]["status"] == "completed"
    assert writer.calls == [[lo] for lo in TOPICS + TOPICS[2:3]]


def test_two_timeouts_keep_progress_for_try_again(tmp_path):
    paths, repo = section(tmp_path)
    writer = Writer(fail={3, 9})
    jobs = jobs_for(paths, repo, writer)
    batch = enqueue(jobs)
    job = repo.ingest_jobs_for_batch(batch)[0]
    assert job["status"] == "failed"
    assert (job["current_window"], job["total_windows"]) == (7, 8)
    assert len(live_questions(paths)) == 7
    jobs.resume_batch(batch)
    assert writer.calls == [[lo] for lo in TOPICS + TOPICS[2:3] * 2]
    job = repo.ingest_jobs_for_batch(batch)[0]
    assert job["status"] == "completed"
    assert (job["current_window"], job["total_windows"]) == (8, 8)


def test_each_part_matches_whole_answer_for_independent_rows(tmp_path):
    paths, repo = section(tmp_path / "parts")
    writer = Writer()
    batch = enqueue(jobs_for(paths, repo, writer))
    patches = repo.ingest_jobs_for_batch(batch)[0]["result"]["patch_ids"]
    old_paths, old_repo = section(tmp_path / "whole")
    old = generate_post_probe_practice_proposal(old_paths.root, Writer(), learning_object_ids=TOPICS,
                                              require_completed_probe=False, target_items_per_lo=3)
    rows = sorted([row for patch in patches for row in comparable_rows(repo, patch)],
                  key=lambda row: row["client_item_id"])
    assert rows == comparable_rows(old_repo, old.patch_id)
    assert len(patches) == 8
    assert live_questions(paths) == live_questions(old_paths)
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


def test_the_request_states_when_a_grounded_question_applies_without_review(tmp_path):
    paths, repo = section(tmp_path, 1)
    writer = Writer()
    enqueue(jobs_for(paths, repo, writer), 1)
    lines = writer.contexts[0].instructions.splitlines()
    (rule,) = [line for line in lines if "review_route=" in line]
    # The policy the review route applies: grounded in the supplied passages and audited means
    # auto_apply; review_required is the exception, and says why.
    assert "review_route='auto_apply' on an item when every one of its source_ref_ids" in rule
    assert "note or canonical_source reference supplied in context.source_refs" in rule
    assert "audit is passed (or not_applicable_with_trace with a trace)" in rule
    assert "review_required' only for an item you could not fully check against the passages it cites" in rule
    assert "relies on something outside them" in rule
    assert "say in its rationale what is unchecked" in rule
    assert "review_required' unless" not in rule


def _rows(repo, job):
    return [row for part in job["payload"]["question_parts"] for row in repo.proposal_items(part["patch_id"])]


def test_grounded_questions_the_model_holds_for_review_wait_for_a_look_and_the_section_completes(tmp_path):
    paths, repo = section(tmp_path, 3)
    writer = held_writer()
    progress = []
    writer.before = lambda: progress.append(
        (lambda job: (job["current_window"], job["total_windows"]))(repo.ingest_jobs_by_types(["practice_expansion"])[0]))
    batch = enqueue(jobs_for(paths, repo, writer), 3)
    job = repo.ingest_jobs_for_batch(batch)[0]
    rows = _rows(repo, job)
    assert [(row["validation_status"], row["decision"]) for row in rows] == [("valid", "pending")] * 9
    assert live_questions(paths) == set()
    # Written and valid, waiting for a look: the writing is done, nothing failed, nothing to ask again.
    assert job["status"] == "completed", job["error"]
    assert [part.get("error") for part in job["payload"]["question_parts"]] == [None] * 3
    assert (job["current_window"], job["total_windows"]) == (3, 3)
    assert progress[1:] == [(1, 3), (2, 3)]
    assert writer.calls == [[lo] for lo in TOPICS[:3]]


def test_one_question_of_three_held_for_review_leaves_two_applied_and_the_topic_finished(tmp_path):
    paths, repo = section(tmp_path, 1)
    writer = held_writer(held=(2,))
    batch = enqueue(jobs_for(paths, repo, writer), 1)
    job = repo.ingest_jobs_for_batch(batch)[0]
    assert job["status"] == "completed", job["error"]
    assert live_questions(paths) == {f"pi_{TOPICS[0]}", f"pi_{TOPICS[0]}_1"}
    assert [row["decision"] for row in _rows(repo, job)] == ["accepted", "accepted", "pending"]
    assert "error" not in job["payload"]["question_parts"][0]
    assert (job["current_window"], job["total_windows"]) == (1, 1)


def test_a_held_question_beside_a_refused_one_still_fails_its_topic(tmp_path):
    paths, repo = section(tmp_path, 2)
    writer = Writer(per_topic=2, held={1}, repeated={0})
    batch = enqueue(jobs_for(paths, repo, writer), 2)
    job = repo.ingest_jobs_for_batch(batch)[0]
    first, second = job["payload"]["question_parts"]
    # The first topic: one applied, one held for review, finished. The second repeats the
    # first's applied prompt: that row is refused, so the topic keeps the failed treatment.
    assert "error" not in first
    assert "duplicate_prompt" in second["error"]
    assert job["status"] == "failed"
    assert TOPICS[1] in job["error"]["message"] and TOPICS[0] not in job["error"]["message"]
    assert (job["current_window"], job["total_windows"]) == (1, 2)
    assert live_questions(paths) == {f"pi_{TOPICS[0]}"}


def test_queue_revision_reload_sees_each_part_before_the_job_finishes(tmp_path, monkeypatch):
    from learnloop.vault.loader import load_vault
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.handlers.queue import get_queue_revision, QueueRevisionInput

    paths, repo = section(tmp_path)
    writer = Writer()
    jobs = jobs_for(paths, repo, writer)
    ctx = SidecarContext()
    ctx.vault, ctx.repository, ctx.ingest_jobs = load_vault(paths.root), repo, jobs
    reloads = []

    def reload(**kwargs):
        ctx.vault = load_vault(paths.root)
        reloads.append(len(live_questions(paths)))

    monkeypatch.setattr(ctx, "reload", reload)

    def during_call():
        if len(writer.calls) > 1:
            result = get_queue_revision(ctx, QueueRevisionInput())
            assert result.get("reloaded"), result
            assert f"pi_{writer.calls[-2][0]}" in ctx.vault.practice_items
            assert not get_queue_revision(ctx, QueueRevisionInput()).get("reloaded")

    writer.before = during_call
    batch = enqueue(jobs)
    assert repo.ingest_jobs_for_batch(batch)[0]["status"] == "completed"
    assert reloads == list(range(1, 8))
