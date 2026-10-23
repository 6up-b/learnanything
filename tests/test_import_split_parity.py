"""S1 (G5): the import split composes to today's Reader import; the Reader job records its key status."""
from __future__ import annotations

import itertools
from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.content.authoring import exercise_authoring as EX
from learnloop.content.authoring.source_exercise_import import selection_for_region
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_service import effective_key_status, imports_for_item
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, loaded

CLOCK = FrozenClock(datetime(2026, 10, 12, 12, 0, tzinfo=UTC))


def _deterministic_ids(monkeypatch):
    counter = itertools.count(1)
    monkeypatch.setattr(EX, "new_ulid", lambda: f"01PARITY{next(counter):018d}")


def _item_file(root, item_id):
    return read_yaml(next((root / "subjects").glob(f"*/practice-items/{item_id}.yaml")))


def test_author_then_write_writes_what_import_exercises_writes(tmp_path, monkeypatch):
    paths, repository, spans = build_textbook_vault(tmp_path / "a")
    other_root = tmp_path / "b"
    copy_tree_with_databases(paths.root, other_root)
    other = Repository(VaultPaths(other_root, paths.config).sqlite_path)
    selection = selection_for_region(repository, "ext_text", [spans["exercises"][1]], vault=load_vault(paths.root))

    _deterministic_ids(monkeypatch)
    whole = EX.import_exercises(paths.root, repository, FakeServiceLLM(), extraction_id="ext_text",
                                raw_selection=selection, source_id="src_text", clock=CLOCK)
    _deterministic_ids(monkeypatch)
    batch = EX.author_exercises(other_root, other, FakeServiceLLM(), extraction_id="ext_text",
                                raw_selection=selection, source_id="src_text", clock=CLOCK)
    split = EX.write_exercises(other_root, other, batch, clock=CLOCK)
    assert whole == split
    item_id = whole["items"][0]["practice_item_id"]
    assert _item_file(paths.root, item_id) == _item_file(other_root, item_id)
    # The Reader's path writes no canonical_exercise and keeps the verbatim stem.
    written = _item_file(paths.root, item_id)
    assert "canonical_exercise" not in written
    assert written["prompt"].startswith("1. An eigenvalue t satisfies")


def test_selection_for_region_spans_whole_blocks(tmp_path):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    selection = selection_for_region(repository, "ext_text", spans["exercises"][1:3], vault=load_vault(paths.root))
    assert [node["span_id"] for node in selection["nodes"]] == spans["exercises"][1:3]
    assert all(node["start"] == 0 and node["end"] > 0 for node in selection["nodes"])
    from learnloop.reader.annotations import translate_selection

    translated = translate_selection(repository, extraction_id="ext_text", raw_selection=selection)
    assert translated["status"] == "exact" and len(translated["segments"]) == 2


def test_the_reader_job_records_an_import_row_and_leaves_the_item_unchanged(tmp_path, monkeypatch):
    from learnloop.content.pipeline import jobs
    from learnloop.content.pipeline.runner import JobContext, RunnerServices

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    selection = selection_for_region(repository, "ext_text", [spans["exercises"][1]], vault=load_vault(paths.root))
    ctx = JobContext(repo=repository, vault_root=paths.root,
                     job={"id": "job_1", "attempt_count": 1,
                          "payload": {"extraction_id": "ext_text", "raw_selection": selection,
                                      "source_id": "src_text"}},
                     clock=CLOCK, worker_id="w",
                     services=RunnerServices(exercise_import_client_factory=lambda ctx: FakeServiceLLM(),
                                             background_key_checks=False))
    monkeypatch.setattr(JobContext, "report", lambda self, *a, **k: None)
    result = jobs.handle_reader_exercise_import(ctx)
    item_id = result["items"][0]["practice_item_id"]
    written = _item_file(paths.root, item_id)
    assert "canonical_exercise" not in written
    with repository.connection() as connection:
        rows = imports_for_item(connection, item_id)
        assert [(row["caller"], row["key_status"], row["status"]) for row in rows] == [
            ("reader", "model_answer", "written")]
        assert effective_key_status(connection, loaded(paths).practice_items[item_id]) == "model_answer"
