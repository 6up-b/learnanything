"""Reader CA4 landing onto main: its interactions with Reader CA3 and CA5a.

(i) CA5a's Compare on a found section, under ``reader_compare.by_point`` on
    and off: with CA3 off it is CA5a's library-ask path (both passages
    pinned), with CA3 on CA3's selection door narrowed to the hit's book. On,
    the server asks ``source_compare.v2`` and the table carries its points;
    off, v1 is asked and the table is CA3's landing's exactly. (The frontend
    side, the right table rendered and a retry keeping the pins or the
    request, is pinned in findSectionByPoint.test.tsx.)
(ii) CA3's tutor about the comparison shown (``comparisonId`` for a stored
    comparison, ``passagesId`` for one that was not) and the named-book scope,
    with v2 tables; "compare again by point" (CA3's pins door with the books
    the v1 table shows) keeps those books.
(iii) The switch matrix ``reader_compare.by_point`` x
    ``reader_compare.scope_enabled`` x ``reader.correspondence.enabled``: the
    prompt contract and the palette are what each switch alone specifies.

Every model is a fake; nothing leaves the machine.
"""
from __future__ import annotations

import copy
import json
from typing import Any

import pytest

from tests.library_ask_fixtures import build_library_vault, call, context, set_config, tutor_with_citations
from tests.reading_path_fixtures import context as coverage_context
from tests.section_coverage_fixtures import BOOK_EIGEN, BOOK_EIGEN_SPAN, build_coverage_vault
from tests.source_service_fakes import FakeServiceLLM, seed_textbook

FIND = {"extraction_id": "ext_book", "section_id": BOOK_EIGEN}
QUESTION = "why does the determinant change sign when two rows are swapped"
V2 = "source_compare.v2"


def _spy(monkeypatch) -> list[dict[str, Any]]:
    import learnloop.instructional.sources as service

    seen: list[dict[str, Any]] = []
    real = service.propose_comparison
    llm = FakeServiceLLM()

    def spy(vault, repository, query, *, caller, **kwargs):
        seen.append({"query": query, **kwargs})
        return real(vault, repository, query, caller=caller, client=llm, verify_client=llm, **kwargs)

    monkeypatch.setattr(service, "propose_comparison", spy)
    return seen


def _assert_by_point(table: dict[str, Any]) -> None:
    assert table["status"] == "ok" and table["contract"] == V2, table
    columns = [row["key"] for row in table["rows"]]
    assert table["points"]
    for point in table["points"]:
        assert [cell["key"] for cell in point["cells"]] == columns
        for relation in point["relations"]:
            assert {relation["leftKey"], relation["rightKey"]} <= set(columns)


def _assert_by_book(table: dict[str, Any]) -> None:
    assert "points" not in table and "contract" not in table, table
    assert all(row["contributes"] for row in table["rows"])


# -- (i) CA5a's compare on a found section, by point and by book ----------------------------------------


@pytest.mark.parametrize("by_point", [True, False])
def test_i_ca5a_pinned_compare_is_v2_by_point_and_v1_by_book_when_off(tmp_path, monkeypatch, by_point):
    """CA3 off: the hit's compare is CA5a's library ask anchored on the
    section, both passages pinned (CA5a F5/F8: a retry reruns the same pins)."""

    paths, _repository = build_coverage_vault(tmp_path / "vault")
    set_config(paths, "reader_compare", scope_enabled=False, **({} if by_point else {"by_point": False}))
    seen = _spy(monkeypatch)
    ctx = coverage_context(paths.root, coverage_inline=True)
    view = call(ctx, "reader.correspondents", {**FIND, "search_fallback": True})
    lay = next(source for source in view["search"]["sources"] if source["sourceId"] == "src_lay")
    hit = lay["sections"][0]["jump"]
    asked = call(ctx, "reader.library_ask", {"query": "Eigenvalues", "extractionId": "ext_book",
                                             "spanIds": [BOOK_EIGEN_SPAN], "entry": "where_else_explained"})
    pins = [f"ext_book:{BOOK_EIGEN_SPAN}", f"{hit['extractionId']}:{hit['spanId']}"]
    request = {"askId": asked["askId"], "openSourceId": "src_book", "pinnedSpanKeys": pins}
    first = call(ctx, "reader.library_compare", request)
    again = call(ctx, "reader.library_compare", request)  # the retry: the same pins
    assert [entry["pinned_span_keys"] for entry in seen] == [pins, pins]
    assert "scope" not in first and first["rows"][0]["key"] == pins[0]
    assert {row["sourceId"] for row in first["rows"]} == {"src_book", "src_lay"}
    if by_point:
        assert all(entry["by_point"] is True for entry in seen)
        _assert_by_point(first)
    else:
        assert all("by_point" not in entry for entry in seen)
        _assert_by_book(first)
    # The rerun is the same comparison (its own cache identity: v2 on, v1 off).
    assert again["verification"]["status"] == "cached"
    volatile = {"verification", "exposureEventIds"}
    assert {k: v for k, v in again.items() if k not in volatile} == {k: v for k, v in first.items() if k not in volatile}


@pytest.mark.parametrize("by_point", [True, False])
def test_i_ca3_selection_door_on_a_hit_is_v2_by_point_and_v1_by_book_when_off(tmp_path, monkeypatch, by_point):
    paths, _repository = build_coverage_vault(tmp_path / "vault")
    if not by_point:
        set_config(paths, "reader_compare", by_point=False)
    seen = _spy(monkeypatch)
    ctx = coverage_context(paths.root, coverage_inline=True)
    request = {"door": "selection", "question": "Eigenvalues", "extractionId": "ext_book",
               "anchorSpanIds": [BOOK_EIGEN_SPAN], "sourceIds": ["src_lay"], "openSourceId": "src_book"}
    table = call(ctx, "reader.library_compare", request)
    (asked,) = seen
    assert asked["anchor_span_keys"] == [f"ext_book:{BOOK_EIGEN_SPAN}"] and asked["source_ids"] == ["src_lay"]
    assert table["scope"]["door"] == "selection" and table["rows"][0]["key"] == f"ext_book:{BOOK_EIGEN_SPAN}"
    assert {row["sourceId"] for row in table["rows"]} == {"src_book", "src_lay"}
    if by_point:
        assert asked["by_point"] is True
        _assert_by_point(table)
    else:
        # CA3's landing exactly: no by_point in the request, no points in the table.
        assert "by_point" not in asked
        _assert_by_book(table)


# -- (ii) CA3's tutor paths and named books with v2 tables ----------------------------------------------


@pytest.fixture
def long_library(tmp_path, monkeypatch):
    paths, repository, _spans = build_library_vault(tmp_path / "vault")
    rows = [(f"Swapping two rows changes the sign of the determinant, step {n} of the alternating "
             "argument for rows of a matrix. Each elementary row operation acts on the determinant "
             "in its own way, and a swap reverses its orientation.", 1) for n in range(4)]
    spans = seed_textbook(repository, source_id="src_long", revision_id="rev_long", extraction_id="ext_long",
                          title="Long Book", units={"c1": ("Determinants and row swaps", rows)})
    import learnloop_sidecar.handlers.ai_providers as providers

    seen = _spy(monkeypatch)
    tutor = tutor_with_citations([])

    class Ready:
        ready = True

    monkeypatch.setattr(providers, "ready_tutor_qa_provider", lambda vault: ("fake", Ready(), tutor))
    return paths, repository, spans["c1"][1:], tutor, seen


def _shown_keys(table: dict) -> list[str]:
    return list(dict.fromkeys(key for row in table["rows"] for key in (row.get("spanKeys") or [row["key"]])))


def _left_out(answer: dict) -> set[str]:
    return {f"{pin['extractionId']}:{pin['spanId']}" for pin in answer["droppedPins"]}


def test_ii_the_tutor_about_a_stored_v2_comparison_reads_every_passage_it_compared(long_library):
    paths, _repository, blocks, tutor, _seen = long_library
    ctx = context(paths.root)
    table = call(ctx, "reader.library_compare", {
        "door": "selection", "question": QUESTION, "extractionId": "ext_long", "anchorSpanIds": blocks})
    _assert_by_point(table)
    assert table["comparisonId"] and "passagesId" not in table
    answer = call(ctx, "reader.library_ask_tutor", {"askId": table["askId"], "comparisonId": table["comparisonId"]})
    assert set(answer["groundedKeys"]) | _left_out(answer) == set(_shown_keys(table))
    prompt = tutor.prompts[0]
    spans = json.loads(prompt[prompt.index("{"):])["context"]["source_spans"]
    assert {f"{s['extraction_id']}:{s['span_id']}" for s in spans} == set(answer["groundedKeys"])


def test_ii_an_unstored_comparison_is_asked_about_by_its_passages_id_while_by_point_is_on(long_library):
    paths, _repository, blocks, _tutor, _seen = long_library
    ctx = context(paths.root)
    assert call(ctx, "reader.prompt_contract", {})["libraryAsk"]["compareByPoint"] is True
    table = call(ctx, "reader.library_compare", {
        "door": "selection", "question": QUESTION, "extractionId": "ext_long", "anchorSpanIds": blocks,
        "sourceIds": ["src_long"]})
    assert table["status"] == "too_few_sources" and not table.get("comparisonId") and table["passagesId"]
    assert "points" not in table  # nothing was compared, so nothing by point
    answer = call(ctx, "reader.library_ask_tutor", {"askId": table["askId"], "passagesId": table["passagesId"]})
    assert set(answer["groundedKeys"]) | _left_out(answer) == set(_shown_keys(table))


def test_ii_named_books_narrow_the_v2_table_to_their_columns(long_library):
    paths, _repository, blocks, _tutor, seen = long_library
    ctx = context(paths.root)
    table = call(ctx, "reader.library_compare", {
        "door": "selection", "question": QUESTION, "extractionId": "ext_long", "anchorSpanIds": blocks[:1],
        "sourceIds": ["src_book"]})
    _assert_by_point(table)
    assert seen[-1]["source_ids"] == ["src_book"]
    assert {row["sourceId"] for row in table["rows"]} == {"src_long", "src_book"}
    cell_keys = {cell["key"] for point in table["points"] for cell in point["cells"]}
    assert cell_keys <= {row["key"] for row in table["rows"]}
    assert not any(key.startswith("ext_text:") for key in cell_keys)


def test_ii_compare_again_by_point_keeps_the_books_the_v1_table_shows(long_library):
    """A v1 comparison of named books (shown while by_point was off), then
    "compare again by point ▸": the frontend sends CA3's pins door with the
    table's passages and the books it shows (comparePointTableCodexReview F6);
    the v2 table has those books' columns and no other."""

    paths, _repository, blocks, _tutor, seen = long_library
    set_config(paths, "reader_compare", by_point=False)
    ctx = context(paths.root)
    old = call(ctx, "reader.library_compare", {
        "door": "selection", "question": QUESTION, "extractionId": "ext_long", "anchorSpanIds": blocks[:1],
        "sourceIds": ["src_book"]})
    _assert_by_book(old)
    shown_books = sorted({row["sourceId"] for row in old["rows"]})
    assert shown_books == ["src_book", "src_long"]
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text(encoding="utf-8").replace("by_point = false", "by_point = true"), encoding="utf-8")
    ctx = context(paths.root)
    again = call(ctx, "reader.library_compare", {
        "door": "pins", "askId": old["askId"], "pinnedSpanKeys": [row["key"] for row in old["rows"]],
        "sourceIds": shown_books})
    _assert_by_point(again)
    assert seen[-1]["by_point"] is True and sorted(seen[-1]["source_ids"]) == shown_books
    assert sorted({row["sourceId"] for row in again["rows"]}) == shown_books


# -- (iii) the switch matrix ------------------------------------------------------------------------------


def _contract(tmp_path, name, *, by_point: bool, scope: bool, correspondence: bool) -> dict[str, Any]:
    paths, _repository = build_coverage_vault(tmp_path / name)
    compare_off = {**({} if by_point else {"by_point": False}), **({} if scope else {"scope_enabled": False})}
    if compare_off:
        set_config(paths, "reader_compare", **compare_off)
    if not correspondence:
        set_config(paths, "reader.correspondence", enabled=False)
    return call(coverage_context(paths.root, coverage_inline=True), "reader.prompt_contract", {})


def _palette_ids(contract) -> list[str]:
    return [action["id"] for group in contract["intent"]["palette"] for action in group["actions"]]


def _without_all(contract: dict[str, Any]) -> dict[str, Any]:
    contract = copy.deepcopy(contract)
    contract.pop("correspondence", None)
    contract["libraryAsk"].pop("compareScope", None)
    contract["libraryAsk"].pop("compareByPoint", None)
    for group in contract["intent"]["palette"]:
        group["actions"] = [action for action in group["actions"] if action["id"] != "compare_books"]
    return contract


def test_iii_each_of_the_three_switches_moves_only_its_own_contract_key_and_palette_action(tmp_path):
    matrix = {
        (bp, scope, corr): _contract(tmp_path, f"b{int(bp)}s{int(scope)}c{int(corr)}", by_point=bp, scope=scope,
                                     correspondence=corr)
        for bp in (True, False) for scope in (True, False) for corr in (True, False)
    }
    for (bp, scope, corr), contract in matrix.items():
        key = (bp, scope, corr)
        assert contract["libraryAsk"].get("compareByPoint", None) is (True if bp else None), key
        assert contract["libraryAsk"].get("compareScope", None) is (True if scope else None), key
        assert ("compare_books" in _palette_ids(contract)) is scope, key
        if corr:
            assert contract["correspondence"] == {"enabled": True, "findSection": True}, key
        else:
            assert "correspondence" not in contract, key
    base = matrix[(False, False, False)]
    assert _without_all(base) == base
    for key, contract in matrix.items():
        assert _without_all(contract) == base, key
