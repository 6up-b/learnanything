"""Reader CA3 landing onto main: its interactions with Reader CA5a (find this section in my other books).

(i) With CA3 on, CA5a's Compare on a hit is CA3's one request through the
    selection door (anchored on the open section, narrowed to the hit's book;
    the frontend side is pinned in findSectionReader.test.tsx and
    libraryAskJobs.test.tsx). Here: the server answers that request.
(ii) A withheld (held-out) or exam anchor or counterpart is refused on both
    paths: CA5a's peek (its exposure rows) and CA3's anchor without pins.
(iii) The switch matrix ``reader_compare.scope_enabled`` x
    ``reader.correspondence.enabled``: the prompt contract and the palette are
    what each switch alone specifies.

Every model is a fake; nothing leaves the machine.
"""
from __future__ import annotations

import copy
from typing import Any

import pytest

from learnloop_sidecar.errors import SidecarError
from tests.library_ask_fixtures import ask_rows, call, set_config
from tests.reading_path_fixtures import context
from tests.section_coverage_fixtures import BOOK_EIGEN, BOOK_EIGEN_SPAN, HELD_OUT_SENTINEL, build_coverage_vault, hold_out
from tests.source_service_fakes import FakeServiceLLM

FIND = {"extraction_id": "ext_book", "section_id": BOOK_EIGEN}
LAY_CHAR = {"extraction_id": "ext_lay", "section_id": "lay_char"}


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


def _ctx(paths):
    return context(paths.root, coverage_inline=True)


def _span(repository, extraction_id: str, text: str) -> str:
    with repository.connection() as connection:
        (span_id,) = connection.execute(
            "SELECT span_id FROM source_document_blocks WHERE extraction_id = ? AND text LIKE ? ORDER BY ordinal LIMIT 1",
            (extraction_id, f"%{text}%")).fetchone()
    return span_id


def _exam_span(repository) -> str:
    with repository.connection() as connection:
        (span_id,) = connection.execute(
            "SELECT span_id FROM source_document_blocks WHERE extraction_id = 'ext_exam' ORDER BY ordinal DESC LIMIT 1"
        ).fetchone()
    return span_id


def _exposed(repository) -> list[tuple[str, str]]:
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT extraction_id, span_id FROM source_exposure_events ORDER BY rowid")]


# -- (i) the find-section door through CA3's one request ------------------------------------------------


def test_i_a_hits_compare_is_the_selection_door_anchored_here_narrowed_to_the_hits_book(tmp_path, monkeypatch):
    paths, repository = build_coverage_vault(tmp_path / "vault")
    seen = _spy(monkeypatch)
    ctx = _ctx(paths)
    view = call(ctx, "reader.correspondents", {**FIND, "search_fallback": True})
    lay = next(source for source in view["search"]["sources"] if source["sourceId"] == "src_lay")
    table = call(ctx, "reader.library_compare", {
        "door": "selection", "question": "Eigenvalues", "extractionId": "ext_book", "anchorSpanIds": [BOOK_EIGEN_SPAN],
        "sourceIds": [lay["sourceId"]], "openSourceId": "src_book"})
    (request,) = seen
    assert request["anchor_span_keys"] == [f"ext_book:{BOOK_EIGEN_SPAN}"] and request["source_ids"] == ["src_lay"]
    assert request["pinned_span_keys"] == []
    assert table["scope"]["door"] == "selection" and table["rows"][0]["key"] == f"ext_book:{BOOK_EIGEN_SPAN}"
    # Only the anchor's book and the hit's book are compared; the held-out unit never is.
    held = _span(repository, "ext_lay", "HELDOUTSENTINEL")
    assert {row["sourceId"] for row in table["rows"]} == {"src_book", "src_lay"}
    assert f"ext_lay:{held}" not in [row["key"] for row in table["rows"]]
    assert ("ext_lay", held) not in _exposed(repository)
    assert all(HELD_OUT_SENTINEL not in str(cell) for row in table["rows"] for cell in row.values())


# -- (ii) a withheld or exam anchor or counterpart is refused on both paths ----------------------------


def test_ii_a_held_out_or_exam_anchor_is_refused_like_the_peek_and_writes_nothing(tmp_path, monkeypatch):
    paths, repository = build_coverage_vault(tmp_path / "vault")
    seen = _spy(monkeypatch)
    ctx = _ctx(paths)
    held = _span(repository, "ext_lay", "HELDOUTSENTINEL")
    char = _span(repository, "ext_lay", "characteristic equation det")
    exposed = _exposed(repository)
    # The held-out unit and the exam paper: CA5a's peek refuses them ...
    for target in ({"extraction_id": "ext_lay", "section_id": "lay_held"},
                   {"extraction_id": "ext_exam", "section_id": "exam_q"}):
        with pytest.raises(SidecarError) as refused:
            call(ctx, "reader.correspondent_peek", target)
        assert refused.value.code == "withheld", target
    # ... and CA3's anchor without pins refuses them before anything is read.
    for extraction_id, span_id in (("ext_lay", held), ("ext_exam", _exam_span(repository))):
        with pytest.raises(SidecarError) as refused:
            call(ctx, "reader.library_compare", {"door": "selection", "question": "Eigenvalues",
                                                 "extractionId": extraction_id, "anchorSpanIds": [span_id]})
        assert refused.value.code == "exam_material", extraction_id
    # Protection marked after the search: both paths refuse the section now.
    assert call(ctx, "reader.correspondent_peek", LAY_CHAR)["peek"]["blocks"]
    hold_out(repository, "lay_char")
    exposed_after_peek = _exposed(repository)
    with pytest.raises(SidecarError) as refused:
        call(ctx, "reader.correspondent_peek", LAY_CHAR)
    assert refused.value.code == "withheld"
    with pytest.raises(SidecarError) as refused:
        call(ctx, "reader.library_compare", {"door": "selection", "question": "Eigenvalues",
                                             "extractionId": "ext_lay", "anchorSpanIds": [char]})
    assert refused.value.code == "exam_material"
    assert seen == [] and ask_rows(repository) == []
    # Only the one allowed peek wrote exposure rows; no refusal did.
    assert _exposed(repository) == exposed_after_peek
    assert all(row[1] not in (held,) for row in exposed_after_peek[len(exposed):])


def test_ii_a_held_out_counterpart_is_never_compared_on_either_path(tmp_path, monkeypatch):
    """The hit's book holds a held-out unit on the very topic: CA3's narrowed
    request and CA5a's library-ask path (CA3 off, two pins) both leave it out."""

    paths, repository = build_coverage_vault(tmp_path / "vault")
    held = _span(repository, "ext_lay", "HELDOUTSENTINEL")
    char = _span(repository, "ext_lay", "characteristic equation det")

    def shown(table):
        return [row["key"] for row in table["rows"]]

    _spy(monkeypatch)
    ctx = _ctx(paths)
    on = call(ctx, "reader.library_compare", {
        "door": "selection", "question": "eigenvalues of the held-out midterm matrix", "extractionId": "ext_book",
        "anchorSpanIds": [BOOK_EIGEN_SPAN], "sourceIds": ["src_lay"], "openSourceId": "src_book"})
    assert f"ext_lay:{held}" not in shown(on)

    set_config(paths, "reader_compare", scope_enabled=False)
    ctx = _ctx(paths)
    asked = call(ctx, "reader.library_ask", {"query": "Eigenvalues", "extractionId": "ext_book",
                                             "spanIds": [BOOK_EIGEN_SPAN], "entry": "where_else_explained"})
    # CA5a's path pins the hit's passage: a held-out one is refused whole (RW4d's withholding).
    with pytest.raises(SidecarError) as refused:
        call(ctx, "reader.library_compare", {"askId": asked["askId"], "openSourceId": "src_book",
                                             "pinnedSpanKeys": [f"ext_book:{BOOK_EIGEN_SPAN}", f"ext_lay:{held}"]})
    assert refused.value.code == "comparison_withheld"
    ok = call(ctx, "reader.library_compare", {"askId": asked["askId"], "openSourceId": "src_book",
                                              "pinnedSpanKeys": [f"ext_book:{BOOK_EIGEN_SPAN}", f"ext_lay:{char}"]})
    assert "scope" not in ok
    assert ("ext_lay", held) not in _exposed(repository)


# -- (iii) the switch matrix ----------------------------------------------------------------------------


def _contract(tmp_path, name, *, scope: bool, correspondence: bool) -> dict[str, Any]:
    paths, _repository = build_coverage_vault(tmp_path / name)
    if not scope:
        set_config(paths, "reader_compare", scope_enabled=False)
    if not correspondence:
        set_config(paths, "reader.correspondence", enabled=False)
    return call(_ctx(paths), "reader.prompt_contract", {})


def _palette_ids(contract) -> list[str]:
    return [action["id"] for group in contract["intent"]["palette"] for action in group["actions"]]


def _without_both(contract: dict[str, Any]) -> dict[str, Any]:
    contract = copy.deepcopy(contract)
    contract.pop("correspondence", None)
    contract["libraryAsk"].pop("compareScope", None)
    for group in contract["intent"]["palette"]:
        group["actions"] = [action for action in group["actions"] if action["id"] != "compare_books"]
    return contract


def test_iii_each_switch_moves_only_its_own_contract_key_and_palette_action(tmp_path):
    matrix = {(scope, corr): _contract(tmp_path, f"s{int(scope)}c{int(corr)}", scope=scope, correspondence=corr)
              for scope in (True, False) for corr in (True, False)}
    for (scope, corr), contract in matrix.items():
        assert ("compareScope" in contract["libraryAsk"]) is scope, (scope, corr)
        if scope:
            assert contract["libraryAsk"]["compareScope"] is True
        assert ("compare_books" in _palette_ids(contract)) is scope, (scope, corr)
        if corr:
            assert contract["correspondence"] == {"enabled": True, "findSection": True}
        else:
            assert "correspondence" not in contract, (scope, corr)
    # Nothing else differs between the four.
    base = _without_both(matrix[(False, False)])
    for key, contract in matrix.items():
        assert _without_both(contract) == base, key
    assert matrix[(False, False)] == base
