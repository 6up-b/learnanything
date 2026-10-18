"""RW4a's compare table over the sources spec's compare_sources (spec_reader_workbench_v1 §7.3; G18).

* The Reader calls the service's ``compare_sources`` (faked here, then
  present) with its own caller and shows only lines that passed the service's
  quote verification: a line whose quote is not in its source's passage never
  reaches the table.
* One row per source, the open source's passage first; every cell is a line
  with its own source's quote; there is no consensus row or heading.
* Display only: without RW4d's keep, nothing is written to ``source_objects``
  or their relations, and no concept edge, facet, prerequisite or LO changes;
  the ask row records only the comparison's id.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from learnloop.source_retrieval import library_ask as LA
from learnloop.source_retrieval.compare import Comparison
from learnloop_sidecar.errors import SidecarError
from tests.library_ask_fixtures import ask_rows, build_library_vault, call, context, set_config, table_counts
from tests.source_service_fakes import FakeServiceLLM

QUESTION = "why does the determinant change sign when two rows are swapped"
PROPOSAL_TABLES = ["source_objects", "source_object_versions", "source_object_citations", "source_object_relations"]


def _faked() -> Comparison:
    return Comparison(
        status="ok", policy="reading", comparison_id=None,
        sources=[
            {"ref": "s1", "source_id": "src_book", "source_title": "Linear Algebra Notes", "extraction_id": "ext_book",
             "span_id": "s6", "page": 1, "passage": "The determinant changes sign when two rows of a matrix are swapped.",
             "contributions": [{"contribution": "states the sign rule", "perspective": "rule",
                                "quote": "changes sign when two rows", "authorship": "ai"}]},
            {"ref": "s2", "source_id": "src_text", "source_title": "Matrix Theory", "extraction_id": "ext_text",
             "span_id": "t3", "page": 7, "passage": "Swapping two rows of a matrix multiplies its determinant by -1.",
             "contributions": [{"contribution": "gives the factor", "perspective": "computation",
                                "quote": "multiplies its determinant by -1", "authorship": "ai"}]},
        ],
        relations=[{"left_ref": "s1", "right_ref": "s2", "relation": "different_notation",
                    "statement": "one says sign change, the other says times -1",
                    "left_quote": "changes sign when two rows", "right_quote": "multiplies its determinant by -1",
                    "authorship": "ai"},
                   {"left_ref": "s2", "right_ref": "s1", "relation": "different_assumptions",
                    "statement": "only one names a square matrix", "left_quote": "Swapping two rows of a matrix",
                    "right_quote": "two rows of a matrix are swapped", "authorship": "ai"}],
        also_discussed_in=[{"source_title": "Lecture notes"}],
    )


def _vault_hash(root) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.yaml")):
        digest.update(path.read_bytes())
    return digest.hexdigest()


@pytest.fixture
def library(tmp_path):
    paths, repository, _spans = build_library_vault(tmp_path / "vault")
    ctx = context(paths.root)
    asked = call(ctx, "reader.library_ask", {"query": QUESTION, "extractionId": "ext_text", "spanIds": ["t3"],
                                             "learningObjectIds": ["lo_matrices"]})
    return paths, ctx, asked


def test_the_table_has_a_row_per_source_with_its_own_quotes_and_no_consensus(library, monkeypatch):
    paths, ctx, asked = library
    import learnloop.instructional.sources as service

    seen = {}

    def fake(vault, repository, query, *, caller, **kwargs):
        seen.update(caller=caller, query=query, **kwargs)
        return _faked()

    monkeypatch.setattr(service, "propose_comparison", fake)
    table = call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": ["ext_book:s6", "ext_text:t3"],
                                                  "openSourceId": "src_text"})
    assert seen["caller"].kind == "reader" and seen["pinned_span_keys"] == ["ext_book:s6", "ext_text:t3"]
    assert "policy" not in seen
    assert table["header"] == "differences kept · each line quotes its own source"
    rows = table["rows"]
    assert [row["sourceTitle"] for row in rows] == ["Matrix Theory", "Linear Algebra Notes"]  # the open source first
    assert rows[0]["isOpenSource"] is True
    assert rows[0]["contributes"][0]["quote"] == "multiplies its determinant by -1"
    assert rows[0]["assumes"][0]["quote"] == "Swapping two rows of a matrix"  # its own side of the relation
    assert rows[1]["differs"][0]["quote"] == "changes sign when two rows"
    assert rows[1]["assumes"][0]["quote"] == "two rows of a matrix are swapped"
    text = json.dumps(table).casefold()
    assert "consensus" not in text and "summary" not in text
    assert table["alsoDiscussedIn"] == [{"sourceTitle": "Lecture notes"}]


def test_lines_that_failed_quote_verification_never_reach_the_table(library, monkeypatch):
    paths, ctx, asked = library
    _vault, repository = ctx.require_vault()
    import learnloop.instructional.sources as service

    real = service.propose_comparison
    llm = FakeServiceLLM(bad_comparison_quote=True)
    monkeypatch.setattr(service, "propose_comparison",
                        lambda *a, **k: real(*a, client=llm, verify_client=llm, **k))
    before = table_counts(repository, PROPOSAL_TABLES)
    files = _vault_hash(paths.root)
    table = call(ctx, "reader.library_compare", {"askId": asked["askId"],
                                                  "pinnedSpanKeys": ["ext_book:s6", "ext_text:t3"]})
    assert table["status"] == "ok" and table["comparisonId"]
    assert table["droppedLineCount"] >= 1  # the invented quote was dropped by the service
    for row in table["rows"]:
        for cell in row["contributes"]:
            assert cell["quote"]  # every line shown quotes its own passage
    # Display only: no proposals, no concept or LO change; the row keeps the id.
    assert table_counts(repository, PROPOSAL_TABLES) == before
    assert _vault_hash(paths.root) == files
    row = [r for r in ask_rows(repository) if r["id"] == asked["askId"]][0]
    assert row["comparison_id"] == table["comparisonId"] and row["kept_json"] is None


def test_compare_needs_two_pins_and_its_switch(library, monkeypatch):
    paths, ctx, asked = library
    vault, repository = ctx.require_vault()
    with pytest.raises(LA.LibraryAskError):
        LA.compare(vault, repository, asked["askId"], pinned_keys=["ext_book:s6"], compare_sources=lambda *a, **k: None)
    set_config(paths, "reader_compare", enabled=False)
    ctx = context(paths.root)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": ["ext_book:s6", "ext_text:t3"]})
    assert caught.value.code == "reader_compare_disabled"


def test_the_services_compare_switch_also_removes_it(library):
    paths, _ctx, asked = library
    set_config(paths, "source_service", compare=False)
    ctx = context(paths.root)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": ["ext_book:s6", "ext_text:t3"]})
    assert caught.value.code == "reader_compare_disabled"
