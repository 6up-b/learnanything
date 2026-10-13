"""Fail-first tests for the Codex review of UX Phase 1 usability round 2
(docs/reviews/ux-phase1-round2-codex-review.md), the backend half:

* F1 — every reading-progress update ran the real "keep one chapter ahead"
  planner on the sidecar's serial RPC path, and that planner built the full
  outline, which loads the book's text once per unit (630 loads for one update
  of a 630-unit book) and parsed the whole vault.
* F2 — the reading step's new selection (from the furthest section read,
  skipping front matter) changed what Today serves under ``mvp-0.14`` with no
  way back to DL1's selection.
* F6 — collection membership alone, or a completed but never applied study-map
  build, silenced a book's "No questions for this book yet · Build them".
"""

from __future__ import annotations

import pytest

from learnloop.content.sources.source_outline import resolve_extraction_id

from tests.test_ux_phase1_add_source import _draining_ctx, call
from tests.ux_phase1_support import fresh_library, grant_consent, set_config, write_book


def _added_book(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    ctx = _draining_ctx(root)
    source_id = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]["sourceId"]
    return root, ctx, source_id, resolve_extraction_id(ctx.repository, source_id)


def _count_text_loads(monkeypatch, repo) -> list[str]:
    loads: list[str] = []
    real = repo.load_document_ir

    def counting(extraction_id, *args, **kwargs):
        loads.append(extraction_id)
        return real(extraction_id, *args, **kwargs)

    monkeypatch.setattr(repo, "load_document_ir", counting)
    return loads


# ---------------------------------------------------------------------------
# F1 — reading progress stays off the expensive outline
# ---------------------------------------------------------------------------


def test_f1_keeping_a_chapter_ahead_never_loads_the_books_text(tmp_path, monkeypatch):
    from learnloop.content.pipeline.add_source import advance_reading_build

    _root, ctx, _source_id, extraction_id = _added_book(tmp_path)
    # The planning job it queues runs on the worker, off the RPC path.
    ctx.ingest_jobs._ensure_worker = lambda: None
    loads = _count_text_loads(monkeypatch, ctx.repository)

    # u3 is "2 Conditional probability": Ch. 1-2 are built, so Ch. 3 is planned.
    started = advance_reading_build(ctx.ingest_jobs, extraction_id, "u3")

    assert started is not None and started["chapters"] == ["3 Random variables"]
    # The chapter list comes from the unit tree, never the outline (which
    # loaded the whole text once for the book and once more per unit).
    assert loads == []


def test_f1_keeping_a_chapter_ahead_reads_the_config_not_the_whole_vault(tmp_path, monkeypatch):
    import learnloop.vault.loader as loader
    from learnloop.content.pipeline.add_source import advance_reading_build

    _root, ctx, _source_id, extraction_id = _added_book(tmp_path)

    def no_full_load(*args, **kwargs):
        raise AssertionError("the progress path parsed the whole vault")

    monkeypatch.setattr(loader, "load_vault", no_full_load)

    assert advance_reading_build(ctx.ingest_jobs, extraction_id, "u2") is None  # Ch. 1-2 already built


def test_f1_keeping_a_chapter_ahead_still_honours_the_switch_in_the_config(tmp_path):
    from learnloop.content.pipeline.add_source import advance_reading_build

    root, ctx, _source_id, extraction_id = _added_book(tmp_path)
    set_config(root, {("ingest", "auto_build"): False})

    assert advance_reading_build(ctx.ingest_jobs, extraction_id, "u3") is None


def test_f1_progress_within_a_section_already_reached_plans_nothing_again(tmp_path, monkeypatch):
    from learnloop.content.pipeline import add_source as core

    _root, ctx, _source_id, extraction_id = _added_book(tmp_path)
    calls: list[str] = []
    real = core.advance_reading_build

    def counting(jobs, ext, section):
        calls.append(section)
        return real(jobs, ext, section)

    monkeypatch.setattr(core, "advance_reading_build", counting)
    planners = len(ctx.repository.ingest_jobs_by_types((core.AUTO_STUDY_MAP_JOB,)))

    for seen in (1, 2, 3):
        call(ctx, "reader.mark_section_progress",
             {"extractionId": extraction_id, "sectionId": "u3", "spansSeen": seen, "spanCount": 4})

    # Reaching the section plans once (the real planner ran: Ch. 3 is queued);
    # reading on inside it is coalesced.
    assert calls == ["u3"]
    assert len(ctx.repository.ingest_jobs_by_types((core.AUTO_STUDY_MAP_JOB,))) == planners + 1


# ---------------------------------------------------------------------------
# F2 — the reading step's selection has a switch back to DL1's
# ---------------------------------------------------------------------------

_WORDS = " ".join(f"word{i}" for i in range(240))
_BOOK_WITH_CONTENTS = "\n\n".join(
    [
        "# Contents",
        "1 Vectors. 2 Matrices. 3 Maps. " + _WORDS,
        "# 1 Vectors",
        _WORDS,
        "# 2 Matrices",
        _WORDS + "\n\n" + _WORDS,
        "# 3 Maps",
        _WORDS,
    ]
) + "\n"


def _seed_book(paths) -> str:
    import json
    from datetime import UTC, datetime

    from learnloop.clock import FrozenClock
    from learnloop.content.sources.source_library import register_source_revision
    from learnloop.db.repositories import Repository
    from learnloop.ingest.extractors.normalizers import markdown_to_ir
    from learnloop.ingest.hashing import extraction_request_hash, extraction_result_hash
    from learnloop.ingest.ir import IR_SCHEMA_VERSION

    clock = FrozenClock(datetime(2026, 10, 1, 9, 0, tzinfo=UTC))
    repo = Repository(paths.sqlite_path)
    registered = register_source_revision(
        repo, acquisition_kind="textfile", canonical_uri="file:///book.md", raw_bytes=_BOOK_WITH_CONTENTS.encode(),
        original_uri="file:///book.md", clock=clock,
    )
    ir = markdown_to_ir(_BOOK_WITH_CONTENTS, title="Book", extractor_name="text")
    request_hash = extraction_request_hash(
        revision_id=registered.revision_id, extractor="text", extractor_version="1", ir_schema_version=IR_SCHEMA_VERSION
    )
    repo.insert_extraction_run(
        id="ext_book", revision_id=registered.revision_id, extractor="text", extractor_version="1",
        extraction_request_hash=request_hash, ir_schema_version=IR_SCHEMA_VERSION, status="running", clock=clock,
    )
    repo.persist_document_ir("ext_book", ir)
    repo.complete_extraction_run("ext_book", extraction_result_hash=extraction_result_hash(request_hash, ir), clock=clock)
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO synthesis_manifests(id, manifest_hash, extraction_ids_json, brief_json, created_at) VALUES (?, ?, ?, ?, ?)",
            ("man_1", "hash_1", json.dumps(["ext_book"]), json.dumps({"practice_items": "as_you_read"}), "2026-10-01T09:00:00Z"),
        )
        connection.execute(
            "INSERT INTO synthesis_runs(id, manifest_id, mode, status, created_at, completed_at) "
            "VALUES ('run_1', 'man_1', 'bootstrap', 'completed', ?, ?)",
            ("2026-10-01T09:00:00Z", "2026-10-01T09:05:00Z"),
        )
        connection.commit()
    return "ext_book"


def _dl1_first_unfinished(repository, extraction_id):
    """mvp-0.14's reading selection exactly as DL1 shipped it (``67ece2c7``):
    the first section in book order that is not completed and has words left."""

    from learnloop.reader.reader_guidance import extraction_sections

    ir = repository.load_document_ir(extraction_id)
    progress = {str(row["section_id"]): row for row in repository.reader_section_progress_for(extraction_id)}
    sections, _blocks, _spans = extraction_sections(ir)
    by_span = {block.span_id: block for block in ir.blocks}
    for section in sections:
        row = progress.get(str(section["id"]))
        if row is not None and row.get("completed_at"):
            continue
        words = sum(len(str(by_span[s].text or "").split()) for s in section["span_ids"] if s in by_span)
        if words <= 0:
            continue
        seen = int((row or {}).get("spans_seen") or 0)
        count = int((row or {}).get("span_count") or 0)
        if int(round(words * (1.0 - (min(seen, count) / count if count > 0 else 0.0)))) <= 0:
            continue
        return str(section["id"])
    return None


def _section_ids(repo, extraction_id):
    """Section ids by label (Markdown labels are heading slugs)."""

    from learnloop.reader.reader_guidance import extraction_sections

    rows, _blocks, _spans = extraction_sections(repo.load_document_ir(extraction_id))
    return {str(row["label"]): str(row["id"]) for row in rows}


# Reading histories where the two selections differ, and where they agree.
_HISTORIES = [
    {},                                                    # a new book
    {"2-matrices": (1, 2, False)},                         # read into Ch. 2, skipping Contents and Ch. 1
    {"1-vectors": (1, 1, True), "3-maps": (1, 1, False)},  # jumped ahead after Ch. 1
    {"contents": (1, 1, True), "1-vectors": (1, 1, True)},  # read in order
]


@pytest.mark.parametrize("history", _HISTORIES)
def test_f2_the_switch_off_restores_dl1s_reading_selection_exactly(tmp_path, history):
    from learnloop.daily_plan.reading import next_reading_target
    from learnloop.db.repositories import Repository
    from tests.helpers import create_daily_plan_vault

    paths = create_daily_plan_vault(tmp_path / "vault")
    extraction_id = _seed_book(paths)
    repo = Repository(paths.sqlite_path)
    ids = _section_ids(repo, extraction_id)
    for label, (seen, count, done) in history.items():
        repo.upsert_reader_section_progress(extraction_id=extraction_id, section_id=ids[label],
                                            spans_seen=seen, span_count=count, completed=done)

    target = next_reading_target(repo, from_furthest=False)

    assert (target.section_id if target else None) == _dl1_first_unfinished(repo, extraction_id)


def test_f2_the_successor_continues_from_the_furthest_section_and_skips_contents(tmp_path):
    from learnloop.daily_plan.reading import next_reading_target
    from learnloop.db.repositories import Repository
    from tests.helpers import create_daily_plan_vault

    paths = create_daily_plan_vault(tmp_path / "vault")
    extraction_id = _seed_book(paths)
    repo = Repository(paths.sqlite_path)
    ids = _section_ids(repo, extraction_id)

    assert next_reading_target(repo).section_id == ids["1-vectors"]  # never Contents
    repo.upsert_reader_section_progress(extraction_id=extraction_id, section_id=ids["2-matrices"], spans_seen=1, span_count=2)
    assert next_reading_target(repo).section_id == ids["2-matrices"]
    # DL1's selection would have gone back to the skipped Contents.
    assert next_reading_target(repo, from_furthest=False).section_id == ids["contents"]


@pytest.mark.parametrize(("toml", "expected"), [("", "2-matrices"), ("[plan]\nreading_from_furthest = false\n", "contents")])
def test_f2_todays_plan_follows_the_switch(tmp_path, monkeypatch, toml, expected):
    from datetime import UTC, datetime

    import learnloop.clock as clock_module
    from learnloop.db.repositories import Repository
    from learnloop_sidecar.context import SidecarContext
    from tests.helpers import create_daily_plan_vault

    paths = create_daily_plan_vault(tmp_path / "vault", plan_toml=toml or None)
    extraction_id = _seed_book(paths)
    repo = Repository(paths.sqlite_path)
    repo.upsert_reader_section_progress(extraction_id=extraction_id, section_id=_section_ids(repo, extraction_id)["2-matrices"],
                                        spans_seen=1, span_count=2)
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: datetime(2026, 10, 12, 9, 0, tzinfo=UTC))
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"

    plan = call(ctx, "set_plan_minutes", {"minutes": 60})["plan"]

    titles = [row["readingTitle"] for row in plan["projected"] if row["readingTitle"]]
    assert titles == [expected]


def test_f2_the_switch_is_on_by_default_and_documented():
    from learnloop.config.schema import PlanConfig

    assert PlanConfig().reading_from_furthest is True


# ---------------------------------------------------------------------------
# F6 — a book's "No questions … Build them" depends on applied questions
# ---------------------------------------------------------------------------

_NO_QUESTIONS = {
    "text": "No questions for this book yet",
    "tone": "quiet",
    "action": {"kind": "retry", "label": "Build them"},
    "details": None,
}


def _imported_book(tmp_path):
    """A book imported through Ingest (no automatic build)."""

    root = fresh_library(tmp_path)
    ctx = _draining_ctx(root)
    call(ctx, "start_import_batch", {"sources": [str(write_book(tmp_path))]})
    card = call(ctx, "get_source_library", {})["sources"][0]
    return root, ctx, card


def _line(ctx, source_id):
    return next(c for c in call(ctx, "get_source_library", {})["sources"] if c["sourceId"] == source_id)["statusLine"]


def _study_map_build(ctx, source_id, *, run_status, decision=None, applied=False):
    """A study-map build (Ingest's own, not Add's) that read this book: its
    manifest, its run and, when it got that far, its proposal."""

    repo = ctx.repository
    extraction_id = resolve_extraction_id(repo, source_id)
    manifest_id = repo.insert_synthesis_manifest({
        "manifest_hash": f"hash_{source_id}_{run_status}_{decision}_{applied}",
        "source_set_id": "set_prob", "extraction_ids": [extraction_id],
        "brief": {"practice_items": "upfront"}, "created_at": "2026-10-13T09:00:00Z",
    })
    proposal_id = None
    if decision is not None:
        proposal_id = repo.persist_proposal_batch(
            {"agent_run_id": "agent_1", "purpose": "bootstrap_synthesis", "created_at": "2026-10-13T09:05:00Z"},
            [{"client_item_id": "lo_1", "item_type": "learning_object", "operation": "create",
              "target_entity_type": "learning_object", "target_entity_id": "lo_counting",
              "payload": {"id": "lo_counting"}, "decision": decision,
              "applied_change_batch_id": "cb_1" if applied else None,
              "created_at": "2026-10-13T09:05:00Z"}],
        )
    run_id = repo.insert_synthesis_run(manifest_id=manifest_id, mode="bootstrap", status="running")
    repo.complete_synthesis_run(run_id, status=run_status, proposal_id=proposal_id)


def _file_in_collection(root, ctx, card):
    from learnloop.vault.loader import add_subject
    from learnloop.vault.writer import upsert_source_set

    add_subject(root, "probability", "Probability")
    upsert_source_set(root, {
        "id": "set_prob", "subject_id": "probability", "title": "Probability",
        "members": [{"source_id": card["sourceId"], "revision_id": card["currentRevisionId"],
                     "default_role": "primary_textbook", "scope": [], "priority": 1}],
    })
    ctx.reload(maintenance=False)


def test_f6_a_book_filed_in_a_collection_but_never_built_still_offers_its_questions(tmp_path):
    root, ctx, card = _imported_book(tmp_path)

    _file_in_collection(root, ctx, card)

    assert _line(ctx, card["sourceId"]) == _NO_QUESTIONS


def test_f6_a_failed_study_map_build_leaves_the_offer(tmp_path):
    root, ctx, card = _imported_book(tmp_path)
    _file_in_collection(root, ctx, card)

    _study_map_build(ctx, card["sourceId"], run_status="failed")

    assert _line(ctx, card["sourceId"]) == _NO_QUESTIONS


def test_f6_a_finished_build_whose_questions_were_never_applied_asks_for_a_look(tmp_path):
    root, ctx, card = _imported_book(tmp_path)
    _file_in_collection(root, ctx, card)

    _study_map_build(ctx, card["sourceId"], run_status="completed", decision="pending")

    line = _line(ctx, card["sourceId"])
    # Not silence, and not a second build of the same chapters either.
    assert line["text"] == "Questions for this book need a look"
    assert line["action"] == {"kind": "open_changes", "label": "Review"}


def test_f6_a_finished_build_whose_questions_were_all_turned_down_offers_them_again(tmp_path):
    _root, ctx, card = _imported_book(tmp_path)

    _study_map_build(ctx, card["sourceId"], run_status="completed", decision="rejected")

    assert _line(ctx, card["sourceId"]) == _NO_QUESTIONS


def test_f6_a_book_whose_study_map_questions_were_applied_stays_quiet(tmp_path):
    root, ctx, card = _imported_book(tmp_path)
    _file_in_collection(root, ctx, card)

    _study_map_build(ctx, card["sourceId"], run_status="completed", decision="accepted", applied=True)

    assert _line(ctx, card["sourceId"]) is None
