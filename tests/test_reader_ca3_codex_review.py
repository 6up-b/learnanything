"""Reader CA3, Codex review (codex-job 20261027-181031-WuQtZY): the backend findings.

* F3: with named books, a pin from another book is dropped with its reason
  before verification (Q13: only the named books, and the anchor's, are
  compared); the anchor stays the one exception.
* F4: an anchor of several blocks keeps every block: the stored entry and
  the cache identity name the whole span set, Keep rechecks (and cites) a
  quote against the block that holds it, and the table row gives the tutor
  every block of the passage.

Every model is a fake (no network).
"""
from __future__ import annotations

import json
import pytest

from learnloop.source_retrieval.compare import compare_sources
from learnloop.source_retrieval.policy import CallerContext
from tests.library_ask_fixtures import ask_rows, build_library_vault, call, context
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, loaded, seed_textbook, set_config

QUESTION = "why does the determinant change sign when two rows are swapped"


class LastWordsLLM(FakeServiceLLM):
    """The service fake, except that every comparison line quotes the last
    words of its passage (so an anchor's quote comes from its last block)."""

    def _SourceComparison(self, request, context):
        from learnloop.source_retrieval.compare import Contribution, PairRelation, SourceComparison

        sources = context["sources"]

        def quote(text: str, words: int = 6) -> str:
            return " ".join(text.split()[-words:])

        contributions = [Contribution(source_ref=src["ref"], contribution=f"{src['source']} states it its way",
                                      perspective="its own view", quote=quote(src["passage"])) for src in sources]
        relations = [PairRelation(left_ref=left["ref"], right_ref=right["ref"], relation="different_notation",
                                  statement="same idea, different notation", left_quote=quote(left["passage"], 5),
                                  right_quote=quote(right["passage"], 5))
                     for left, right in zip(sources, sources[1:])]
        return SourceComparison(contributions=contributions, relations=relations, missing_perspectives=[])


@pytest.fixture
def textbook(tmp_path):
    return build_textbook_vault(tmp_path / "vault")


def _third(repository) -> str:
    spans = seed_textbook(repository, source_id="src_third", revision_id="rev_third", extraction_id="ext_third",
                          title="Third Book", units={"c1": ("Determinants", [
                              ("Swapping two rows of a matrix changes the sign of its determinant, by the "
                               "alternating property of determinants.", 1)])})
    return f"ext_third:{spans['c1'][1]}"


# -- F3: pins obey the named-book restriction ---------------------------------------------------------


def test_f3_a_pin_from_a_book_not_named_is_dropped_before_verification(textbook):
    paths, repository, _spans = textbook
    pin = _third(repository)
    llm = FakeServiceLLM()
    result = compare_sources(loaded(paths), repository, QUESTION, caller=CallerContext(kind="reader"),
                             source_ids=["src_text", "src_book"], pinned_span_keys=[pin], client=llm,
                             verify_client=llm)
    compared = {entry["source_id"] for entry in result.sources}
    assert "src_third" not in compared
    assert compared <= {"src_text", "src_book"}
    extraction, span = pin.split(":")
    assert {"extraction_id": extraction, "span_id": span,
            "reason": "its book is not among the books you chose"} in result.dropped_pins
    # It reached no model: no verification candidate and no stored counterpart is the third book's.
    assert result.manifest["verification"]["sources_with_hits"] <= 2
    assert all(key[0] != "ext_third" for key in result.manifest.get("counterpart_keys") or [])
    assert all(entry["source_id"] != "src_third" for entry in result.unverified_sources)


def test_f3_the_anchor_stays_the_one_exception(textbook):
    paths, repository, spans = textbook
    llm = FakeServiceLLM()
    result = compare_sources(loaded(paths), repository, QUESTION, caller=CallerContext(kind="reader"),
                             anchor_span_keys=[f"ext_text:{spans['ch5'][2]}"], source_ids=["src_book"],
                             client=llm, verify_client=llm)
    assert result.status == "ok"
    assert [entry["source_id"] for entry in result.sources][0] == "src_text"
    assert result.sources[0]["anchor"] is True and not result.dropped_pins


def test_f3_without_named_books_a_pin_is_compared_as_today(textbook):
    paths, repository, _spans = textbook
    pin = _third(repository)
    llm = FakeServiceLLM()
    result = compare_sources(loaded(paths), repository, QUESTION, caller=CallerContext(kind="reader"),
                             pinned_span_keys=[pin], client=llm, verify_client=llm)
    assert not result.dropped_pins
    assert "src_third" in {entry["source_id"] for entry in result.sources}


# -- F4: a multi-block anchor is the whole passage ----------------------------------------------------


def test_f4_the_stored_entry_and_cache_identity_name_every_anchor_block(textbook):
    paths, repository, spans = textbook
    llm = LastWordsLLM()
    first_block, second_block = spans["ch5"][1], spans["ch5"][2]
    first = compare_sources(loaded(paths), repository, QUESTION, caller=CallerContext(kind="reader"),
                            anchor_span_keys=[f"ext_text:{first_block}", f"ext_text:{second_block}"],
                            client=llm, verify_client=llm)
    assert first.status == "ok" and first.comparison_id
    anchor = first.sources[0]
    assert anchor["anchor"] is True and anchor["span_id"] == first_block
    assert anchor["span_ids"] == [first_block, second_block]
    # The anchor's line quotes its second block, and it passed the comparison's check.
    assert anchor["contributions"] and "changes sign" in anchor["contributions"][0]["quote"]
    assert ["ext_text", second_block] in first.manifest["counterpart_keys"]

    # The same question and counterpart with another second block is another comparison.
    other_block = spans["worked"][1]
    second = compare_sources(loaded(paths), repository, QUESTION, caller=CallerContext(kind="reader"),
                             anchor_span_keys=[f"ext_text:{first_block}", f"ext_text:{other_block}"],
                             client=llm, verify_client=llm)
    assert second.status == "ok"
    assert second.reused is False and second.comparison_id != first.comparison_id
    assert second.sources[0]["span_ids"] == [first_block, other_block]
    # And the very same anchor is reused (never paid for twice).
    again = compare_sources(loaded(paths), repository, QUESTION, caller=CallerContext(kind="reader"),
                            anchor_span_keys=[f"ext_text:{first_block}", f"ext_text:{second_block}"],
                            client=llm, verify_client=llm)
    assert again.reused is True and again.comparison_id == first.comparison_id


def test_f4_a_one_block_anchor_is_stored_as_before(textbook):
    paths, repository, spans = textbook
    llm = FakeServiceLLM()
    result = compare_sources(loaded(paths), repository, QUESTION, caller=CallerContext(kind="reader"),
                             anchor_span_keys=[f"ext_text:{spans['ch5'][2]}"], client=llm, verify_client=llm)
    assert "span_ids" not in result.sources[0]
    assert result.manifest["counterpart_keys"][0] == ["ext_text", spans["ch5"][2]]


@pytest.fixture
def library(tmp_path, monkeypatch):
    paths, repository, _spans = build_library_vault(tmp_path / "vault")
    # CA3's keep by source (Reader CA4's cells are pinned in its own tests).
    set_config(paths, "reader_compare", by_point=False)
    import learnloop.instructional.sources as service

    real = service.propose_comparison
    llm = LastWordsLLM()
    monkeypatch.setattr(service, "propose_comparison",
                        lambda *a, **k: real(*a, client=llm, verify_client=llm, **k))
    return paths, context(paths.root), repository


def _blocks(repository, extraction_id: str) -> list[str]:
    with repository.connection() as connection:
        return [row[0] for row in connection.execute(
            "SELECT span_id FROM source_document_blocks WHERE extraction_id = ? AND block_type = 'Text' "
            "ORDER BY ordinal", (extraction_id,))]


def test_f4_keep_rechecks_and_cites_a_quote_from_the_anchors_later_block(library):
    _paths, ctx, repository = library
    first_block, second_block = _blocks(repository, "ext_text")[:2]
    table = call(ctx, "reader.library_compare", {
        "door": "selection", "question": QUESTION, "extractionId": "ext_text",
        "anchorSpanIds": [first_block, second_block]})
    assert table["status"] == "ok"
    anchor_row = table["rows"][0]
    assert anchor_row["isOpenSource"] is True and anchor_row["key"] == f"ext_text:{first_block}"
    # The tutor is grounded in the whole passage: every block of the anchor.
    assert anchor_row["spanKeys"] == [f"ext_text:{first_block}", f"ext_text:{second_block}"]
    assert all("spanKeys" not in row for row in table["rows"][1:])

    kept = call(ctx, "reader.library_compare_keep", {"askId": table["askId"]})
    row = next(r for r in ask_rows(repository) if r["id"] == table["askId"])
    stored = json.loads(row["kept_json"])
    anchor_objects = [obj for obj in stored["objects"] if obj["extraction_id"] == "ext_text"]
    assert anchor_objects, stored["not_kept"]
    assert not [entry for entry in stored["not_kept"]
                if entry.get("key") == f"ext_text:{first_block}"], stored["not_kept"]
    with repository.connection() as connection:
        citations = [dict(zip(("span_id", "exact_quote"), r)) for r in connection.execute(
            "SELECT span_id, exact_quote FROM source_object_citations WHERE source_object_version_id = ?",
            (anchor_objects[0]["version_id"],))]
    # Cited to the block that holds the quote, never to the first block alone.
    assert citations and citations[0]["span_id"] == second_block
    assert kept["kept"]["status"] == "proposed"
