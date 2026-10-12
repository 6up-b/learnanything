"""Slice 2 T6: `learnloop sources search` and `learnloop sources suggest-lo`."""
from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from tests.source_retrieval_fakes import build_retrieval_vault


def test_sources_search_and_suggest_lo(tmp_path):
    paths, _repository = build_retrieval_vault(tmp_path / "vault")
    runner = CliRunner()
    found = runner.invoke(app, ["sources", "search", "cofactor expansion", "--vault", str(paths.root), "--json"])
    assert found.exit_code == 0, found.output
    report = json.loads(found.stdout)
    assert report["hits"][0]["span_id"] == "s8" and report["basis"] == "keyword"
    text = runner.invoke(app, ["sources", "search", "dot product", "--vault", str(paths.root)])
    assert text.exit_code == 0 and "basis: keyword" in text.stdout and "ext_book/s12" in text.stdout
    suggested = runner.invoke(app, ["sources", "suggest-lo", "--vault", str(paths.root), "--extraction",
                                    "ext_book", "--span", "s12"])
    assert suggested.exit_code == 0
    assert "suggestion (not a provenance link): lo_inner" in suggested.stdout
