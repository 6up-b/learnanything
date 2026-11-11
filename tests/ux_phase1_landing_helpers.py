"""What other test files use from ``tests/test_ux_phase1_landing.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.content.pipeline.add_source import AddSourceOptions, add_source, outline_chapters
from learnloop.content.sources.source_outline import build_source_outline, resolve_extraction_id
from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.vault.loader import load_vault

from tests.ux_phase1_support import (
    CLOCK,
    fake_services,
    fresh_library,
    grant_consent,
    repository,
    set_config,
    write_book,
)


def _added_book(tmp_path):
    from learnloop.content.pipeline.jobs import DurableIngestJobs

    root = fresh_library(tmp_path)
    grant_consent(root)
    set_config(root, {("ingest", "auto_build"): False})
    repo = repository(root)
    jobs = DurableIngestJobs()
    jobs.bind(repo, root, background=False, clock=CLOCK, services=fake_services())
    item = add_source(load_vault(root), jobs, str(write_book(tmp_path)), AddSourceOptions(), clock=CLOCK)
    set_config(root, {("ingest", "auto_build"): True})
    return root, repo, item["source_id"]


def _hold_out(repo, source_id, label):
    extraction_id = resolve_extraction_id(repo, source_id)
    outline = build_source_outline(repo, extraction_id)
    chapter = next(chapter for chapter in outline_chapters(outline) if chapter.label == label)
    save_unit_selection(repo, extraction_id, [unit.unit_id for unit in outline.units],
                        exam_use_modes={chapter.unit_id: "held_out_evaluation"}, clock=CLOCK)
    return chapter


def _reading_book(tmp_path):
    from learnloop.db.repositories import Repository
    from tests.helpers import create_daily_plan_vault
    from tests.ux_phase1_round2_review_helpers import _section_ids, _seed_book

    paths = create_daily_plan_vault(tmp_path / "vault")
    extraction_id = _seed_book(paths)
    repo = Repository(paths.sqlite_path)
    return paths, repo, extraction_id, _section_ids(repo, extraction_id)


def _section_spans(repo, extraction_id, section_id):
    from learnloop.reader.reader_guidance import extraction_sections

    rows, _blocks, _spans = extraction_sections(repo.load_document_ir(extraction_id))
    return next(list(row["span_ids"]) for row in rows if str(row["id"]) == section_id)
