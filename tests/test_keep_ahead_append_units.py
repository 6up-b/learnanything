"""Keep-ahead appends send only the chapter just planned (refactor K3.2).

The planner chose the new chapter's units, but the append it queued carried no
unit filter, so every chapter's append re-sent the inventory of every chapter
built so far: input grew with each chapter read.
"""

from __future__ import annotations

from learnloop.content.pipeline.add_source import AddSourceOptions, add_source, advance_reading_build, outline_chapters
from learnloop.content.sources.source_outline import build_source_outline, resolve_extraction_id
from learnloop.content.synthesis.source_append import select_new_inventories
from learnloop.vault.loader import load_vault

from tests.ux_phase1_auto_build_helpers import _jobs
from tests.ux_phase1_support import CLOCK, fake_services, fresh_library, grant_consent, write_book


def _entry(revision_id: str, unit_id: str, source_unit_ids: list[str] | None = None) -> dict:
    return {"revision_id": revision_id, "unit_id": unit_id, "source_unit_ids": source_unit_ids or [unit_id]}


def test_the_second_build_appends_only_its_own_chapter(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    sent = []
    repo, jobs = _jobs(root, fake_services(on_append=sent.append))
    item = add_source(load_vault(root), jobs, str(write_book(tmp_path)), AddSourceOptions(), clock=CLOCK)
    extraction_id = resolve_extraction_id(repo, item["source_id"])
    by_label = {chapter.label: chapter.unit_id
                for chapter in outline_chapters(build_source_outline(repo, extraction_id))}

    started = advance_reading_build(jobs, extraction_id, by_label["2 Conditional probability"])

    assert started is not None and started["chapters"] == ["3 Random variables"]
    assert len(sent) == 1
    assert [entry["unit_id"] for entry in sent[0].new_inventories] == [by_label["3 Random variables"]]
    build = next(job for job in repo.ingest_jobs_by_types(("bootstrap_synthesis",))
                 if job["payload"].get("auto_build", {}).get("chapters") == ["3 Random variables"])
    source_set = next(s for s in load_vault(root).source_sets if s.id == f"sset_quickadd_{item['source_id']}")
    revision_id = source_set.members[0].revision_id
    assert build["payload"]["new_unit_ids"] == {revision_id: [by_label["3 Random variables"]]}


def test_the_unit_filter_applies_per_revision():
    entries = [
        _entry("rev_a", "u1"), _entry("rev_a", "u2"), _entry("rev_a", "u2+u3", ["u2", "u3"]),
        _entry("rev_b", "u1"), _entry("rev_c", "u1"),
    ]

    # No filter: every unit of the chosen revisions, as before.
    assert select_new_inventories(entries, {"rev_a", "rev_b"}, None) == entries[:4]
    # A revision named in the filter sends only its listed units (a merged unit
    # joins when any member is new); a revision not named sends all of its own.
    chosen = select_new_inventories(entries, {"rev_a", "rev_b"}, {"rev_a": ["u3"]})
    assert [(entry["revision_id"], entry["unit_id"]) for entry in chosen] == [("rev_a", "u2+u3"), ("rev_b", "u1")]
