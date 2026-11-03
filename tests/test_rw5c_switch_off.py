"""Reader RW5c (G23g): with ``figures.checked_labels_enabled`` off, everything is RW5a/RW5d's exactly.

The golden was recorded on an export of main (``9c594465a8``) by :mod:`tests.rw5c_golden_source`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from learnloop.db.stores import figures as store
from learnloop.figures import service as FS
from learnloop.figures import source_check as SC
from learnloop.vault.loader import load_vault
from tests.figure_fixtures import AuthorFake, build, call, context, rows
from tests.rw5c_fixtures import EXTRACTION, build_check_vault, plot, set_switch
from tests.rw5c_golden_source import golden

GOLDEN = Path(__file__).parent / "fixtures" / "rw5c_switch_off_golden.json"


def test_the_views_report_clis_reuse_keys_and_prompt_equal_mains(tmp_path):
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert golden(tmp_path / "vault", switch=True) == expected


def _checked_row(figure_id: str, outcome: str, elements: list[dict[str, Any]]) -> dict[str, Any]:
    return {"id": "fsc_planted", "figure_id": figure_id, "certification_version": SC.CERTIFICATION_VERSION, "trigger": "recheck",
            "outcome": outcome, "definitions": [], "elements": elements, "reasons": {}, "harness_sha256": "x",
            "reader_version": "x", "sympy_version": "x", "duration_ms": 1, "judgment_id": "j_planted",
            "created_at": "2026-11-02T00:00:00Z"}


def test_nothing_reads_the_ledger_while_the_switch_is_off(tmp_path, monkeypatch):
    paths, repository = build_check_vault(tmp_path / "vault", [("s5", "Text", "$f(x)=x$")])
    set_switch(paths, False)
    author = AuthorFake([plot("x", label="the model's own name")])
    ctx = context(paths.root, author=author)
    figure = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["s5"]})["figure"]
    assert "elements" not in figure and "sourceCheck" not in figure
    assert rows(repository, "figure_source_checks") == []  # no check ran, no row was written
    assert [row for row in rows(repository, "judgment_ledger") if row["task"] == SC.LEDGER_TASK] == []
    # A row left from when it was on: not read, whatever it says (a rejected figure shows as before too).
    with repository.connection() as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        store.insert_source_check(connection, _checked_row(figure["figureId"], "differs", []))
        connection.commit()

    def never(*_args: Any, **_kwargs: Any):
        raise AssertionError("the ledger was read with the switch off")

    monkeypatch.setattr(store, "latest_source_check", never)
    monkeypatch.setattr(SC, "current_row", never)
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"][0]
    assert listed["verification"] == "illustrative" and "the model's own name" in listed["specJson"]
    assert "elements" not in listed and "sourceCheck" not in listed
    vault = load_vault(paths.root)
    assert FS.source_rejected(vault, repository, store.figure(repository.connection(), figure["figureId"])) is False
    assert FS.shown_figure(vault, repository, figure["figureId"])


def test_a_row_written_just_before_a_switch_off_is_never_shown_while_it_is_off(tmp_path):
    paths, repository = build_check_vault(tmp_path / "vault", [("s5", "Text", "$f(x)=x$")])
    ctx = context(paths.root, author=AuthorFake([plot("x", label="the model's own name")]))
    figure = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["s5"]})["figure"]
    book = {"id": "panels.0.series.0", "path": "panels.0.series.0", "role": "book", "tex": "f(x)", "plain": "f(x)",
            "voice": "source", "definition": "f", "equation": "f(x)=x"}
    with repository.connection() as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        store.insert_source_check(connection, _checked_row(figure["figureId"], "checked", [book]))
        connection.commit()
    shown = call(context(paths.root), "reader.figures", {"extractionId": EXTRACTION})["figures"][0]
    assert shown["sourceCheck"]["status"] == "checked" and "the model's own name" not in shown["specJson"]
    set_switch(paths, False)
    off = call(context(paths.root), "reader.figures", {"extractionId": EXTRACTION})["figures"][0]
    assert "elements" not in off and "sourceCheck" not in off and "the model's own name" in off["specJson"]
    # Back on: it shows again, its certification version current.
    set_switch(paths, True)
    back = call(context(paths.root), "reader.figures", {"extractionId": EXTRACTION})["figures"][0]
    assert back["sourceCheck"]["status"] == "checked"
