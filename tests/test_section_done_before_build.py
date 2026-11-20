"""A section finished before its book's topics are in still gets its questions, once.

A learner may press "Done with this section" (or finish its quick check) while the book's build is still
running, waiting for a look, or stopped. The section's questions are written from the topics citing it, so at
that moment there is nothing to write them from yet. The completion then waits for the build; when the build's
topics are applied (bootstrap, an append, a retry that works), the section's question writing starts once. A
finished section is "none needed" only once its chapter's build has settled and no topic citing it needs
questions. A row an older version stamped "none needed" too early is picked up the next time the books are
read. Every model call is a house fake; nothing is written twice.
"""

from __future__ import annotations

import pytest

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.ai.errors import AITurnTimeout
from learnloop.content.pipeline import add_source as core
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop_sidecar.context import SidecarContext

from tests.ux_phase1_add_source_helpers import call
from tests.ux_phase1_support import CLOCK, FakeBookSynthesisClient, fake_services, fresh_library, grant_consent, write_book

#: In the house book's first build (chapters 1-2), one topic cites section u2; none cites u3, which the build
#: also covers; u4 is a chapter no build has covered yet.
CITED, UNCITED, UNBUILT = "u2", "u3", "u4"


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)


def _ctx(root, services=None):
    """A sidecar whose queue runs only when the test drains it, one job at a time."""

    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=services or fake_services())
    ctx.ingest_jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    return ctx


def _drain(ctx, max_jobs=1):
    return ctx.ingest_jobs._require_runner().drain(max_jobs=max_jobs)


def _jobs(ctx):
    return [job for batch in ctx.repository.list_ingest_batches() for job in ctx.repository.ingest_jobs_for_batch(batch["id"])]


def _book(tmp_path, services=None, *, scope_cap=150):
    root = fresh_library(tmp_path, scope_cap=scope_cap)
    grant_consent(root)
    ctx = _ctx(root, services)
    source_id = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]["sourceId"]
    return ctx, source_id


def _until_synthesis_is_next(ctx):
    """Run the import, the planner and the inventory: the build's synthesis (its topics) is all that is left."""

    for _ in range(10):
        if any(job["job_type"] == "inventory" and job["status"] == "completed" for job in _jobs(ctx)):
            synthesis = [job for job in _jobs(ctx) if job["job_type"] == "bootstrap_synthesis"]
            assert [job["status"] for job in synthesis] == ["queued"]
            return
        assert _drain(ctx), "the queue ran dry before the build's inventory finished"
    pytest.fail("the build's inventory never finished")


def _finish(ctx, source_id, section_id):
    extraction_id = resolve_extraction_id(ctx.repository, source_id)
    return call(ctx, "reader.mark_section_progress",
                {"extractionId": extraction_id, "sectionId": section_id, "spansSeen": 3, "spanCount": 3,
                 "completed": True})


def _stamp(ctx, source_id, section_id):
    row = ctx.repository.reader_section_progress_row(resolve_extraction_id(ctx.repository, source_id), section_id)
    return (row or {}).get("generation_batch_id")


def _section_batches(ctx, section_id):
    """The question-writing batches queued for one finished section."""

    return [
        batch for batch in ctx.repository.list_ingest_batches()
        if batch["workflow_type"] == "practice_expansion"
        and any((job.get("payload") or {}).get("reason") == f"reader_section_completed:{section_id}"
                for job in ctx.repository.ingest_jobs_for_batch(batch["id"]))
    ]


def _card(ctx, source_id):
    return next(card for card in call(ctx, "get_source_library", {})["sources"] if card["sourceId"] == source_id)


def _label(ctx, source_id, section_id):
    with ctx.repository.connection() as connection:
        row = connection.execute(
            "SELECT label FROM source_document_units WHERE extraction_id = ? AND unit_id = ?",
            (resolve_extraction_id(ctx.repository, source_id), section_id),
        ).fetchone()
    return str(row["label"])


def _reads_again(ctx, source_id):
    """Every place that reads a book's sections again: the library (Today, the shelf) and the Reader."""

    _card(ctx, source_id)
    call(ctx, "reader.get_progress", {"extractionId": resolve_extraction_id(ctx.repository, source_id)})


# -- finished before the build applies -----------------------------------------------------------


def test_a_section_finished_before_the_build_applies_gets_its_questions_when_it_does_once(tmp_path):
    ctx, source_id = _book(tmp_path)
    _until_synthesis_is_next(ctx)

    done = _finish(ctx, source_id, CITED)

    assert done["enqueuedGeneration"] is False
    assert done["waitingForBuild"] is True
    assert _stamp(ctx, source_id, CITED) == "waiting_for_build"
    _reads_again(ctx, source_id)
    assert _section_batches(ctx, CITED) == []  # nothing to write from yet, and nothing started

    assert _drain(ctx) == 1  # the build's synthesis: its topics are applied

    batches = _section_batches(ctx, CITED)
    assert len(batches) == 1
    job = ctx.repository.ingest_jobs_for_batch(batches[0]["id"])[0]
    assert job["status"] == "queued"
    assert "lo_diagonalize_symmetric" in job["payload"]["learning_object_ids"]
    assert _stamp(ctx, source_id, CITED) == batches[0]["id"]
    # Read again, everywhere, and again: never a second writing.
    _reads_again(ctx, source_id)
    _reads_again(ctx, source_id)
    _finish(ctx, source_id, CITED)
    assert len(_section_batches(ctx, CITED)) == 1
    questions = _card(ctx, source_id)["statusLine"]["questions"]
    assert questions["writing"] == [_label(ctx, source_id, CITED)]
    assert questions["waiting"] == []


class _Flaky(FakeBookSynthesisClient):
    failing = True

    def run_source_set_synthesis(self, context):
        if _Flaky.failing:
            raise AITurnTimeout("The model took too long.")
        return super().run_source_set_synthesis(context)


def test_a_section_finished_before_a_build_that_stops_gets_its_questions_when_a_retry_works(tmp_path):
    _Flaky.failing = True
    ctx, source_id = _book(tmp_path, fake_services(synthesis_client_factory=lambda ctx=None: _Flaky()))
    _until_synthesis_is_next(ctx)
    _finish(ctx, source_id, CITED)

    _drain(ctx)  # the synthesis fails, and fails again on its own retry: the build stops

    build = ctx.repository.get_ingest_batch(core.latest_auto_outcome(ctx.repository, source_id)["build_batch_id"])
    assert build["status"] == "failed"
    card = _card(ctx, source_id)
    assert card["statusLine"]["action"] == {"kind": "retry", "label": "Retry"}
    assert card["statusLine"]["questions"]["waiting"] == [_label(ctx, source_id, CITED)]
    assert _stamp(ctx, source_id, CITED) == "waiting_for_build"
    assert _section_batches(ctx, CITED) == []

    _Flaky.failing = False
    call(ctx, "source_action", {"sourceId": source_id, "action": "retry"})
    _drain(ctx)  # the retried synthesis applies

    assert ctx.repository.get_ingest_batch(build["id"])["status"] == "completed"
    assert len(_section_batches(ctx, CITED)) == 1
    _reads_again(ctx, source_id)
    assert len(_section_batches(ctx, CITED)) == 1


def test_a_section_the_phone_finished_before_the_build_waits_for_it_too(tmp_path):
    """The phone host leaves a finished section's questions to the desktop; the desktop's Reader, finding the
    book's topics not in yet, keeps it waiting instead of settling it as needing none."""

    ctx, source_id = _book(tmp_path)
    _until_synthesis_is_next(ctx)
    extraction_id = resolve_extraction_id(ctx.repository, source_id)
    # What the phone host's completion writes (it enqueues nothing itself).
    ctx.repository.upsert_reader_section_progress(extraction_id=extraction_id, section_id=CITED, spans_seen=3,
                                                  span_count=3, completed=True, clock=CLOCK)
    assert ctx.repository.mark_section_generation(extraction_id=extraction_id, section_id=CITED,
                                                  batch_id="deferred_to_primary")

    _reads_again(ctx, source_id)

    assert _stamp(ctx, source_id, CITED) == "waiting_for_build"
    assert _section_batches(ctx, CITED) == []
    _drain(ctx)
    assert len(_section_batches(ctx, CITED)) == 1
    _reads_again(ctx, source_id)
    assert len(_section_batches(ctx, CITED)) == 1


def test_a_section_no_topic_cites_settles_as_needing_none_once_the_build_applies(tmp_path):
    ctx, source_id = _book(tmp_path)
    _until_synthesis_is_next(ctx)
    _finish(ctx, source_id, UNCITED)
    assert _stamp(ctx, source_id, UNCITED) == "waiting_for_build"

    _drain(ctx)
    _reads_again(ctx, source_id)

    assert _section_batches(ctx, UNCITED) == []
    assert _stamp(ctx, source_id, UNCITED) == "none_needed_after_build"
    questions = core.reading_questions(ctx.repository, ctx.vault, source_id)
    assert questions["waiting"] == [] and questions["writing"] == [] and questions["count"] == 0


# -- finished after the build applies: as before --------------------------------------------------


def test_a_section_finished_after_the_build_applies_is_as_before(tmp_path):
    ctx, source_id = _book(tmp_path)
    _drain(ctx, max_jobs=None)
    _card(ctx, source_id)  # the shelf's poll reloads the vault the build applied to

    cited = _finish(ctx, source_id, CITED)
    uncited = _finish(ctx, source_id, UNCITED)

    assert cited["enqueuedGeneration"] is True and cited["waitingForBuild"] is False
    assert len(_section_batches(ctx, CITED)) == 1
    assert uncited["enqueuedGeneration"] is False and uncited["waitingForBuild"] is False
    assert _section_batches(ctx, UNCITED) == []
    _reads_again(ctx, source_id)
    assert len(_section_batches(ctx, CITED)) == 1 and _section_batches(ctx, UNCITED) == []


def test_a_completion_read_on_a_vault_loaded_before_the_build_applied_still_finds_its_topics(tmp_path):
    """The sidecar's vault is reloaded when a read notices an applied build; a completion that comes first reads
    the snapshot from before it. The section is never settled as needing nothing on that snapshot alone."""

    ctx, source_id = _book(tmp_path)
    _drain(ctx, max_jobs=None)  # applied in the background; nothing has reloaded the sidecar's vault yet
    assert "lo_diagonalize_symmetric" not in ctx.vault.learning_objects

    done = _finish(ctx, source_id, CITED)

    assert done["enqueuedGeneration"] is True
    assert len(_section_batches(ctx, CITED)) == 1


def test_a_section_in_a_chapter_no_build_covers_yet_waits_for_one(tmp_path):
    ctx, source_id = _book(tmp_path)
    _drain(ctx, max_jobs=None)

    done = _finish(ctx, source_id, UNBUILT)

    assert done["enqueuedGeneration"] is False and done["waitingForBuild"] is True
    assert _card(ctx, source_id)["statusLine"]["questions"]["waiting"] == [_label(ctx, source_id, UNBUILT)]


# -- rows an older version stamped "none needed" ---------------------------------------------------


def _legacy(ctx, source_id, section_id, completed_at):
    """A completion an older version settled as needing none, whatever the build's state then."""

    extraction_id = resolve_extraction_id(ctx.repository, source_id)
    ctx.repository.upsert_reader_section_progress(extraction_id=extraction_id, section_id=section_id, spans_seen=3,
                                                  span_count=3, completed=True, clock=CLOCK)
    assert ctx.repository.mark_section_generation(extraction_id=extraction_id, section_id=section_id,
                                                  batch_id="none_needed")
    with ctx.repository.connection() as connection:
        connection.execute("UPDATE reader_section_progress SET completed_at = ? WHERE extraction_id = ? AND section_id = ?",
                           (completed_at, extraction_id, section_id))
        connection.commit()


def test_an_old_none_needed_row_with_topics_citing_it_now_is_picked_up_once(tmp_path):
    ctx, source_id = _book(tmp_path)
    _drain(ctx, max_jobs=None)
    built = ctx.repository.get_ingest_batch(core.latest_auto_outcome(ctx.repository, source_id)["build_batch_id"])
    assert built["finished_at"] == "2026-10-13T09:00:00Z"
    _legacy(ctx, source_id, CITED, "2026-10-13T08:59:00Z")  # finished while the build ran

    _card(ctx, source_id)  # the next time the books are read

    assert len(_section_batches(ctx, CITED)) == 1
    _reads_again(ctx, source_id)
    _reads_again(ctx, source_id)
    assert len(_section_batches(ctx, CITED)) == 1


def test_an_old_none_needed_row_that_was_right_stays_without_questions(tmp_path):
    ctx, source_id = _book(tmp_path)
    _drain(ctx, max_jobs=None)
    _legacy(ctx, source_id, UNCITED, "2026-10-13T08:59:00Z")  # no topic cites it, then or now
    _legacy(ctx, source_id, CITED, "2026-10-13T09:30:00Z")  # finished after the build: settled when the topics were in

    _reads_again(ctx, source_id)

    assert _section_batches(ctx, UNCITED) == [] and _section_batches(ctx, CITED) == []
    assert _stamp(ctx, source_id, UNCITED) == "none_needed_after_build"
    assert _stamp(ctx, source_id, CITED) == "none_needed_after_build"


# -- the status line's fact ----------------------------------------------------------------------


def test_the_status_lines_fact_tells_waiting_from_nothing_finished(tmp_path):
    ctx, source_id = _book(tmp_path)
    _until_synthesis_is_next(ctx)

    building = _card(ctx, source_id)["statusLine"]
    assert building["tone"] == "working"
    assert "questions" not in building  # no section finished: nothing to say on a building line

    _finish(ctx, source_id, CITED)
    waiting = _card(ctx, source_id)["statusLine"]
    assert waiting["tone"] == "working"
    assert waiting["questions"]["waiting"] == [_label(ctx, source_id, CITED)]
    assert waiting["questions"]["writing"] == [] and waiting["questions"]["count"] == 0


# -- "Build questions for the whole book at once" ---------------------------------------------------


def _planners(ctx):
    return len(ctx.repository.ingest_jobs_by_types((core.AUTO_STUDY_MAP_JOB,)))


def test_the_whole_book_press_on_a_book_already_built_says_so_and_queues_nothing(tmp_path):
    ctx, source_id = _book(tmp_path, scope_cap=None)  # the first build is the whole book
    _drain(ctx, max_jobs=None)
    planners = _planners(ctx)

    result = call(ctx, "source_action", {"sourceId": source_id, "action": "build_whole_book"})

    assert result.get("batchId") is None
    assert result["notice"] == ("All of this book is ready for questions. "
                                "Each section's questions are written when you finish it.")
    assert _planners(ctx) == planners
    assert "come up as you read" in _card(ctx, source_id)["statusLine"]["text"]


def test_the_whole_book_press_while_the_whole_book_is_being_built_says_so(tmp_path):
    ctx, source_id = _book(tmp_path, scope_cap=None)
    _until_synthesis_is_next(ctx)
    planners = _planners(ctx)

    result = call(ctx, "source_action", {"sourceId": source_id, "action": "build_whole_book"})

    assert result.get("batchId") is None
    assert result["notice"] == ("All of this book is already being got ready for questions. "
                                "Each section's questions are written when you finish it.")
    assert _planners(ctx) == planners


def test_the_whole_book_press_with_chapters_left_starts_and_shows_it(tmp_path):
    ctx, source_id = _book(tmp_path)  # the first build covers chapters 1-2 of 4
    _drain(ctx, max_jobs=None)

    result = call(ctx, "source_action", {"sourceId": source_id, "action": "build_whole_book"})

    assert result["batchId"] and "notice" not in result
    assert _card(ctx, source_id)["statusLine"]["tone"] == "working"


def test_a_planner_that_found_nothing_to_build_never_hides_the_books_line(tmp_path):
    ctx, source_id = _book(tmp_path, scope_cap=None)
    _drain(ctx, max_jobs=None)
    before = _card(ctx, source_id)["statusLine"]

    core.request_auto_build(ctx.ingest_jobs, source_id, chapter_ids=["u2"])  # every chapter is built already
    _drain(ctx, max_jobs=None)

    skipped = ctx.repository.ingest_jobs_by_types((core.AUTO_STUDY_MAP_JOB,))[0]
    assert (skipped["result"] or {}).get("reason") == "nothing_to_build"
    assert _card(ctx, source_id)["statusLine"] == before
