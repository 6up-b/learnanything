"""RW4d: "Keep this comparison" (spec_reader_workbench_v1 §7.8, §3.4 item 15; G18, G43).

* **No keep, no write** (G18): comparing writes nothing to ``source_objects``
  or their relations (a table diff over every table); only the press does.
* **Kept comparisons are proposals** (G43): Keep writes ``source_objects``
  (claim or definition) with ``status = 'proposed'`` and ``authorship = 'ai'``
  and one span-and-quote citation each, and ``source_object_relations`` with
  ``review_status = 'proposed'`` and ``authorship = 'ai'``, typed by §3.4 item
  15's mapping with the fine label kept on ``library_asks.kept_json``; *your
  take* is a ``learner_connects`` relation with ``authorship = 'learner'``,
  never read for gaps. No concept edge, facet merge, prerequisite or LO
  change (the vault's YAML is unchanged) and no learning state.
* Only lines that passed the comparison's quote check are kept, and only while
  their quote is still in the passage; held-out (or exam) material is never
  kept or reopened, including material held out after the comparison.
* *Remove* supersedes, never deletes. A second Keep only adds new takes.
* The tutor's comparison: kept only after it was pressed and shown, with only
  the sources its run showed.
* ``⇄`` marks, reopen and "you compared these on …"; the router card's pure read.
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import json

import pytest

from learnloop.db.connection import connect
from learnloop.db.stores.source_block_fts import blocks_by_key
from learnloop.db.stores.source_service import insert_comparison
from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.source_retrieval import kept_comparisons as KC
from learnloop.source_retrieval.compare import Comparison
from learnloop_sidecar.errors import SidecarError
from tests.library_ask_fixtures import ask_rows, build_library_vault, call, context, set_config, table_counts
from tests.source_service_fakes import FakeServiceLLM, learning_state_tables

QUESTION = "why does the determinant change sign when two rows are swapped"
PROPOSAL_TABLES = ["source_objects", "source_object_versions", "source_object_citations", "source_object_relations"]
#: What a keep may change: the proposals, the ask row's keep, one salience-only event.
KEEP_WRITES = set(PROPOSAL_TABLES) | {"interaction_events"}
PINS = ["ext_book:s6", "ext_text:t3"]


def _all_counts(repository) -> dict[str, int]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        names = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        return {name: connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0] for name in names}


def _changed(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
    return {name: after[name] - before.get(name, 0) for name in after if after[name] != before.get(name, 0)}


def _vault_hash(root) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.yaml")):
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _rows(repository, sql: str, *args) -> list[dict]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        connection.row_factory = __import__("sqlite3").Row
        return [dict(row) for row in connection.execute(sql, args)]


def _fake_service(monkeypatch, llm=None):
    import learnloop.instructional.sources as service

    real = service.propose_comparison
    llm = llm or FakeServiceLLM()
    monkeypatch.setattr(service, "propose_comparison", lambda *a, **k: real(*a, client=llm, verify_client=llm, **k))
    return llm


@pytest.fixture
def library(tmp_path):
    paths, repository, spans = build_library_vault(tmp_path / "vault")
    ctx = context(paths.root)
    asked = call(ctx, "reader.library_ask", {"query": QUESTION, "extractionId": "ext_text", "spanIds": ["t3"],
                                             "learningObjectIds": ["lo_matrices"]})
    return paths, ctx, repository, spans, asked


@pytest.fixture
def compared(library, monkeypatch):
    paths, ctx, repository, spans, asked = library
    _fake_service(monkeypatch)
    table = call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": PINS})
    assert table["status"] == "ok" and table["comparisonId"] and table["kept"] is None
    return paths, ctx, repository, spans, asked, table


def _block_text(repository, key: str) -> str:
    extraction, span = key.split(":", 1)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return blocks_by_key(connection, [(extraction, span)])[(extraction, span)].text


def _stored(monkeypatch, ctx, repository, ask_id: str, relations: list[dict], *, keys=PINS, extra_sources=()):
    """A stored comparison with the given relations between the two pinned
    passages (quotes are each passage's own first words), surfaced through a
    faked ``compare_sources`` so the ask row refers to it."""

    import learnloop.instructional.sources as service

    sources = []
    for index, key in enumerate([*keys, *extra_sources], start=1):
        extraction, span = key.split(":", 1)
        text = _block_text(repository, key)
        sources.append({"ref": f"s{index}", "source_id": {"ext_book": "src_book", "ext_text": "src_text",
                                                          "ext_exam": "src_exam"}[extraction],
                        "source_title": extraction, "extraction_id": extraction, "span_id": span, "page": 1,
                        "passage": text, "authorship": "source", "label": "source-authored",
                        "contributions": [{"contribution": f"{extraction} says it its way", "perspective": "own",
                                           "quote": " ".join(text.split()[:5]), "authorship": "ai"}]})
    quote = {source["ref"]: " ".join(source["passage"].split()[:4]) for source in sources}
    rels = [{"left_ref": "s1", "right_ref": "s2", "statement": f"{fine} line", "relation": fine,
             "left_quote": quote["s1"], "right_quote": quote["s2"], "authorship": "ai"} for fine in relations]
    comparison_id = "scmp_test" + str(len(ask_rows(repository)))
    with repository.connection() as connection:
        insert_comparison(connection, id=comparison_id, created_at="2026-10-03T09:00:00Z", query_hash="h",
                          query_md=QUESTION, requested_perspectives=[], counterpart_keys=[k.split(":") for k in keys],
                          comparison={"sources": sources, "relations": rels, "missing_perspectives": []},
                          dropped_lines=[], dropped_pins=[], unverified_sources=[], policy="reading",
                          caller_context={"kind": "reader"}, model="fake-compare", prompt_version="source_compare.v1",
                          ledger_ids=["jl_1"], caller="reader", caller_ref=None)
        connection.commit()
    monkeypatch.setattr(service, "propose_comparison", lambda *a, **k: Comparison(
        status="ok", policy="reading", comparison_id=comparison_id, sources=sources, relations=rels))
    return call(ctx, "reader.library_compare", {"askId": ask_id, "pinnedSpanKeys": list(keys)})


# -- G18 / G43: no keep, no write; keep writes only proposals ---------------------------------


def test_comparing_writes_no_proposal_and_keep_writes_only_proposals(library, monkeypatch):
    paths, ctx, repository, _spans, asked = library
    _fake_service(monkeypatch)
    files = _vault_hash(paths.root)
    before_compare = _all_counts(repository)
    table = call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": PINS})
    after_compare = _all_counts(repository)
    # Without "Keep" the Reader writes nothing to source_objects or relations (table diff).
    assert not set(_changed(before_compare, after_compare)) & set(PROPOSAL_TABLES)
    assert all(after_compare[table_name] == 0 for table_name in PROPOSAL_TABLES)
    # Nothing to reopen and no mark until Keep.
    assert call(ctx, "reader.kept_comparisons", {"extractionId": "ext_text"})["marks"] == []
    with pytest.raises(SidecarError):
        call(ctx, "reader.library_compare_reopen", {"askId": asked["askId"]})

    learning = learning_state_tables(repository)
    learning_before = table_counts(repository, learning)
    kept = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    after_keep = _all_counts(repository)
    changed = _changed(after_compare, after_keep)
    assert set(changed) <= KEEP_WRITES, changed
    rows = len(table["rows"])
    assert changed["source_objects"] == rows and changed["source_object_versions"] == rows
    assert changed["source_object_citations"] == rows
    assert changed["source_object_relations"] == sum(len(row["differs"]) + len(row["assumes"])
                                                     for row in table["rows"]) // 2
    assert changed["interaction_events"] == 1
    assert table_counts(repository, learning) == learning_before
    # No concept edge, facet merge, prerequisite or LO change: the vault's files are unchanged.
    assert _vault_hash(paths.root) == files

    versions = _rows(repository, "SELECT * FROM source_object_versions")
    assert {(v["status"], v["authorship"], v["object_type"]) for v in versions} == {("proposed", "ai", "claim")}
    citations = _rows(repository, "SELECT * FROM source_object_citations")
    by_key = {row["key"]: row for row in table["rows"]}
    for citation in citations:
        assert citation["span_id"] and citation["exact_quote"] and citation["revision_id"] in {"rev_book", "rev_text"}
        assert citation["block_content_hash"]
        extraction = "ext_book" if citation["revision_id"] == "rev_book" else "ext_text"
        assert citation["exact_quote"] in _block_text(repository, f"{extraction}:{citation['span_id']}")
        assert f"{extraction}:{citation['span_id']}" in by_key
    relations = _rows(repository, "SELECT * FROM source_object_relations")
    assert {(r["authorship"], r["review_status"], r["relation_type"]) for r in relations} == {("ai", "proposed",
                                                                                               "refines")}
    state = kept["kept"]
    assert state["status"] == "proposed" and {rel["fine"] for rel in state["relations"]} == {"different_notation"}
    row = [r for r in ask_rows(repository) if r["id"] == asked["askId"]][0]
    assert row["kept_at"] and json.loads(row["kept_json"])["comparison_id"] == table["comparisonId"]


def test_keep_reads_the_stored_comparison_never_the_clients_table(compared):
    _paths, ctx, repository, _spans, asked, _table = compared
    # The RPC takes no table: lines come from the stored row, which holds only verified lines.
    with pytest.raises(Exception):
        call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "rows": [{"line": "made up"}]})
    kept = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    contents = [json.loads(v["content_json"]) for v in _rows(repository, "SELECT * FROM source_object_versions")]
    assert all(line["quote"] for content in contents for line in content["lines"])
    assert kept["alreadyKept"] is False


def test_lines_that_failed_quote_verification_are_never_kept(library, monkeypatch):
    _paths, ctx, repository, _spans, asked = library
    _fake_service(monkeypatch, FakeServiceLLM(bad_comparison_quote=True))
    table = call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": PINS})
    assert table["droppedLineCount"] >= 1
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    kept_text = json.dumps(_rows(repository, "SELECT content_json, exact_text FROM source_object_versions"))
    assert "words that are nowhere in the passage" not in kept_text and "invented" not in kept_text


# -- §3.4 item 15: the mapping and the fine labels --------------------------------------------


@pytest.mark.parametrize("fine,left,right,coarse", [
    ("equivalent", "claim", "claim", "supports"),
    ("equivalent", "definition", "claim", "supports"),
    ("equivalent", "definition", "definition", "alternate_definition"),
    ("different_assumptions", "claim", "claim", "refines"),
    ("different_notation", "definition", "definition", "refines"),
    ("complementary", "claim", "claim", "refines"),
    ("disagreement", "claim", "claim", "contradicts"),
    ("unclear", "claim", "claim", "unresolved"),
    ("consensus", "claim", "claim", None),
])
def test_the_relation_mapping_table(fine, left, right, coarse):
    assert KC.coarse_relation(fine, left, right) == coarse


def test_every_fine_label_round_trips_through_kept_json(library, monkeypatch):
    _paths, ctx, repository, _spans, asked = library
    labels = ["equivalent", "different_assumptions", "different_notation", "complementary", "disagreement",
              "unclear", "consensus"]
    _stored(monkeypatch, ctx, repository, asked["askId"], labels)
    kept = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    row = [r for r in ask_rows(repository) if r["id"] == asked["askId"]][0]
    stored = json.loads(row["kept_json"])
    fine_to_id = {rel["fine"]: rel for rel in stored["relations"]}
    assert set(fine_to_id) == set(labels) - {"consensus"}  # an unknown label is not kept (fail closed)
    assert any("consensus" in entry["reason"] for entry in stored["not_kept"])
    relations = {r["id"]: r for r in _rows(repository, "SELECT * FROM source_object_relations")}
    for fine, entry in fine_to_id.items():
        assert relations[entry["id"]]["relation_type"] == KC.RELATION_MAP[fine] == entry["relation_type"]
        assert entry["statement"] == f"{fine} line" and entry["left_quote"] and entry["right_quote"]
    assert {rel["fine"] for rel in kept["kept"]["relations"]} == set(fine_to_id)


def test_equivalent_definitions_are_alternate_definitions(library, monkeypatch):
    _paths, ctx, repository, _spans, asked = library
    monkeypatch.setattr(KC, "block_roles", lambda connection, keys: {tuple(key): "definition" for key in keys})
    _stored(monkeypatch, ctx, repository, asked["askId"], ["equivalent", "disagreement"])
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    versions = _rows(repository, "SELECT object_type FROM source_object_versions")
    assert {v["object_type"] for v in versions} == {"definition"}
    types = {r["relation_type"] for r in _rows(repository, "SELECT relation_type FROM source_object_relations")}
    assert types == {"alternate_definition", "contradicts"}


# -- your take ----------------------------------------------------------------------------------


def test_your_take_is_the_learners_own_relation_and_is_not_read_for_gaps(compared):
    _paths, ctx, repository, _spans, asked, table = compared
    keys = [row["key"] for row in table["rows"]]
    gap_tables = [name for name in _all_counts(repository) if "gap" in name or name == "question_events"]
    before = table_counts(repository, gap_tables)
    kept = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "takes": [
        {"text": "both are the same sign rule, one in words", "keys": keys},
        {"text": "this one never says square", "keys": keys[:1]},
    ]})
    takes = _rows(repository, "SELECT * FROM source_object_relations WHERE relation_type = 'learner_connects'")
    assert len(takes) == 2
    assert {(t["authorship"], t["review_status"]) for t in takes} == {("learner", "proposed")}
    pair = next(t for t in takes if t["learner_text"].startswith("both"))
    claim = next(t for t in takes if t["learner_text"].startswith("this one"))
    assert pair["related_object_id"] and claim["related_object_id"] is None
    # The three voices stay separate rows with separate authorship (W2).
    authorship = {r["authorship"] for r in _rows(repository, "SELECT authorship FROM source_object_relations")}
    assert authorship == {"ai", "learner"}
    assert [take["learnerText"] for take in kept["kept"]["takes"]] == [pair["learner_text"], claim["learner_text"]]
    # Never read for gaps (UX §4.10) and never a question.
    assert table_counts(repository, gap_tables) == before


def test_a_take_on_a_passage_not_in_the_comparison_is_refused_and_writes_nothing(compared):
    _paths, ctx, repository, _spans, asked, _table = compared
    before = _all_counts(repository)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_compare_keep", {"askId": asked["askId"],
                                                  "takes": [{"text": "x", "keys": ["ext_book:s99"]}]})
    assert caught.value.code == "validation_error"
    after = _all_counts(repository)
    assert not set(_changed(before, after)) & set(PROPOSAL_TABLES)


def test_a_second_keep_adds_only_new_takes(compared):
    _paths, ctx, repository, _spans, asked, table = compared
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    first = table_counts(repository, PROPOSAL_TABLES)
    again = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    assert again["alreadyKept"] is True and table_counts(repository, PROPOSAL_TABLES) == first
    later = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "takes": [
        {"text": "added after keeping", "keys": [table["rows"][0]["key"]]}]})
    assert later["addedTakes"] == 1
    after = table_counts(repository, PROPOSAL_TABLES)
    assert after["source_object_relations"] == first["source_object_relations"] + 1
    assert after["source_objects"] == first["source_objects"]


def test_compare_shows_whether_its_comparison_is_kept(compared):
    _paths, ctx, _repository, _spans, asked, _table = compared
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    again = call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": PINS})
    assert again["kept"]["status"] == "proposed" and again["kept"]["askId"] == asked["askId"]


# -- remove -------------------------------------------------------------------------------------


def test_remove_supersedes_and_never_deletes(compared):
    _paths, ctx, repository, _spans, asked, table = compared
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "takes": [
        {"text": "mine", "keys": [table["rows"][0]["key"]]}]})
    kept = table_counts(repository, PROPOSAL_TABLES)
    removed = call(ctx, "reader.library_compare_remove", {"askId": asked["askId"]})
    assert removed["removed"] is True
    after = table_counts(repository, PROPOSAL_TABLES)
    # Append-only: every claim gains a superseded version, every relation a superseded successor.
    assert after["source_objects"] == kept["source_objects"]
    assert after["source_object_versions"] == kept["source_object_versions"] + kept["source_objects"]
    assert after["source_object_relations"] == 2 * kept["source_object_relations"]
    heads = _rows(repository, "SELECT v.status FROM source_object_versions v WHERE v.version_ordinal = "
                              "(SELECT MAX(version_ordinal) FROM source_object_versions w "
                              "WHERE w.source_object_id = v.source_object_id)")
    assert {h["status"] for h in heads} == {"superseded"}
    successors = _rows(repository, "SELECT * FROM source_object_relations WHERE version_ordinal = 2")
    assert len(successors) == kept["source_object_relations"]
    assert {s["review_status"] for s in successors} == {"superseded"}
    assert any(s["learner_text"] == "mine" and s["authorship"] == "learner" for s in successors)
    row = [r for r in ask_rows(repository) if r["id"] == asked["askId"]][0]
    assert row["kept_at"] is None and json.loads(row["kept_json"])["removed"]
    assert call(ctx, "reader.kept_comparisons", {"extractionId": "ext_text"})["marks"] == []
    with pytest.raises(SidecarError):
        call(ctx, "reader.library_compare_reopen", {"askId": asked["askId"]})
    # Kept again: new proposals, the removal kept in the history.
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    row = [r for r in ask_rows(repository) if r["id"] == asked["askId"]][0]
    assert row["kept_at"] and json.loads(row["kept_json"])["removed"]


# -- held out -----------------------------------------------------------------------------------


def _hold_out_chapter(repository, spans) -> None:
    # ext_text's chapter 5 (t1-t3, the pinned t3 among them) held out for an exam.
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"ch5": "held_out_evaluation"})


def test_material_held_out_after_the_comparison_is_not_kept(compared):
    _paths, ctx, repository, spans, asked, _table = compared
    _hold_out_chapter(repository, spans)
    before = _all_counts(repository)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "takes": [
            {"text": "x", "keys": ["ext_text:t3"]}]})
    assert caught.value.code == "exam_material"
    after = _all_counts(repository)
    assert _changed(before, after) == {}
    row = [r for r in ask_rows(repository) if r["id"] == asked["askId"]][0]
    assert row["kept_json"] is None


def test_a_kept_comparison_held_out_later_is_neither_marked_nor_reopened(compared):
    _paths, ctx, repository, spans, asked, _table = compared
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    assert call(ctx, "reader.kept_comparisons", {"extractionId": "ext_book"})["marks"]
    reopened = call(ctx, "reader.library_compare_reopen", {"askId": asked["askId"]})
    assert reopened["rows"] and reopened["kept"]["status"] == "proposed"
    _hold_out_chapter(repository, spans)
    for extraction in ("ext_book", "ext_text"):
        assert call(ctx, "reader.kept_comparisons", {"extractionId": extraction})["marks"] == []
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_compare_reopen", {"askId": asked["askId"]})
    assert caught.value.code == "exam_material"
    assert "Swapping two rows" not in json.dumps(caught.value.__dict__, default=str)


def test_a_comparison_holding_exam_material_is_refused(library, monkeypatch):
    _paths, ctx, repository, _spans, asked = library
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        (exam_span,) = connection.execute(
            "SELECT span_id FROM source_document_blocks WHERE extraction_id = 'ext_exam' AND text != '' "
            "ORDER BY ordinal LIMIT 1").fetchone()
    _stored(monkeypatch, ctx, repository, asked["askId"], ["unclear"], extra_sources=[f"ext_exam:{exam_span}"])
    before = table_counts(repository, PROPOSAL_TABLES)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    assert caught.value.code == "exam_material"
    assert table_counts(repository, PROPOSAL_TABLES) == before


def test_the_held_out_predicate_fails_closed(compared, monkeypatch):
    _paths, ctx, repository, _spans, asked, _table = compared

    def broken(*_args, **_kwargs):
        raise RuntimeError("predicate unreadable")

    monkeypatch.setattr(KC.EM, "exam_withheld", broken)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    assert caught.value.code == "exam_material"
    assert table_counts(repository, PROPOSAL_TABLES) == {table: 0 for table in PROPOSAL_TABLES}


def test_a_line_whose_quote_left_the_passage_is_not_kept(compared):
    _paths, ctx, repository, _spans, asked, table = compared
    moved = table["rows"][0]["key"]
    extraction, span = moved.split(":", 1)
    with repository.connection() as connection:
        connection.execute("UPDATE source_document_blocks SET text = 'A re-extracted passage with other words.' "
                           "WHERE extraction_id = ? AND span_id = ?", (extraction, span))
        connection.commit()
    kept = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    keys = {obj["key"] for obj in kept["kept"]["objects"]}
    assert moved not in keys and keys == {row["key"] for row in table["rows"]} - {moved}
    assert kept["kept"]["relations"] == [] and kept["kept"]["notKept"] >= 1


# -- the tutor's comparison ----------------------------------------------------------------------


def test_the_tutors_comparison_is_kept_only_after_its_press_with_what_it_showed(tmp_path, monkeypatch):
    import learnloop.instructional.tools as tools
    from tests.reader_tutor_fakes import LookupTutor, ask, reader_ctx

    tutor = LookupTutor(tool_requests=[{"tool": "compare_sources", "query": "determinant sign when rows are swapped",
                                        "reason": "How do your books treat this?", "facet_ids": []}],
                        cite=lambda context: [("ext_text", "t3")])
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    verifier = ctx.reader_tutor_rerank_client
    real = tools.run_requested_tool
    monkeypatch.setattr(tools, "run_requested_tool", lambda vault, repo, request_id, **kw: real(
        vault, repo, request_id, **{**kw, "clients": {"source_rerank": verifier, "source_compare": FakeServiceLLM()}}))
    answer = ask(ctx)
    (request,) = [r for r in answer["toolRequests"] if r["tool"] == "compare_sources"]
    # Not pressed: no comparison ran, so there is nothing to keep (and no model call).
    assert table_counts(repository, ["source_comparisons"]) == {"source_comparisons": 0}
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_compare_keep", {"toolCallId": request["toolCallId"]})
    assert caught.value.code == "validation_error"
    assert table_counts(repository, PROPOSAL_TABLES) == {table: 0 for table in PROPOSAL_TABLES}
    pressed = call(ctx, "run_source_tool", {"toolCallId": request["toolCallId"]})
    shown = {f"{s['extractionId']}:{s['spanId']}" for s in pressed["result"]["sources"]}
    assert len(shown) >= 2
    before = table_counts(repository, ["library_asks"])
    kept = call(ctx, "reader.library_compare_keep", {"toolCallId": request["toolCallId"], "extractionId": "ext_text",
                                                     "takes": [{"text": "my own reading", "keys": sorted(shown)[:2]}]})
    assert {obj["key"] for obj in kept["kept"]["objects"]} <= shown
    assert table_counts(repository, ["library_asks"])["library_asks"] == before["library_asks"] + 1
    row = [r for r in ask_rows(repository) if r["id"] == kept["askId"]][0]
    assert row["caller"] == "tutor" and row["comparison_id"] == pressed["result"]["comparisonId"]
    assert row["question_event_id"] == answer["eventId"]
    # Pressed twice: the same row, nothing new.
    again = call(ctx, "reader.library_compare_keep", {"toolCallId": request["toolCallId"]})
    assert again["askId"] == kept["askId"] and again["alreadyKept"] is True
    assert call(ctx, "reader.kept_comparisons", {"extractionId": "ext_text"})["marks"]


def test_a_tutor_keep_keeps_only_the_sources_its_run_showed(tmp_path, monkeypatch):
    from learnloop.db.stores import source_service as store

    paths, repository, _spans = build_library_vault(tmp_path / "vault")
    ctx = context(paths.root)
    vault, _repo = ctx.require_vault()
    texts = {key: _block_text(repository, key) for key in PINS}
    sources = [{"ref": f"s{i}", "source_id": "src_book" if key.startswith("ext_book") else "src_text",
                "source_title": key, "extraction_id": key.split(":")[0], "span_id": key.split(":")[1], "page": 1,
                "passage": texts[key], "contributions": [{"contribution": "c", "perspective": "p",
                                                          "quote": " ".join(texts[key].split()[:5])}]}
               for i, key in enumerate(PINS, start=1)]
    with repository.connection() as connection:
        store.insert_comparison(connection, id="scmp_t", created_at="2026-10-03T09:00:00Z", query_hash="h",
                                query_md=QUESTION, requested_perspectives=[], counterpart_keys=[],
                                comparison={"sources": sources, "relations": []}, dropped_lines=[], dropped_pins=[],
                                unverified_sources=[], policy="reading", caller_context={}, model="m",
                                prompt_version="source_compare.v1", ledger_ids=[], caller="tutor", caller_ref="qe_1")
        store.insert_tool_call(connection, id="stc_req", created_at="2026-10-03T09:00:00Z", row_kind="request",
                               caller_kind="tutor", caller_ref="qe_1", context={}, policy="reading",
                               tool="compare_sources", arguments={}, status="requested")
        # The view withheld the second source (say, answer overlap): only the first was shown.
        store.insert_tool_call(connection, id="stc_run", parent_id="stc_req", created_at="2026-10-03T09:00:01Z",
                               row_kind="run", caller_kind="tutor", caller_ref="qe_1", context={}, policy="reading",
                               tool="compare_sources", arguments={}, status="ran", result_ref="scmp_t",
                               result_keys=[PINS[0]])
        connection.commit()
    kept = KC.keep_tutor(vault, repository, "stc_req")
    assert [obj["key"] for obj in kept["kept"]["objects"]] == [PINS[0]]
    assert PINS[1] not in json.dumps(_rows(repository, "SELECT * FROM source_object_citations"))


def test_the_comparison_switch_and_the_services_switch_turn_keep_off(tmp_path):
    for section, values in (("reader_compare", {"enabled": False}), ("source_service", {"compare": False})):
        paths, _repository, _spans = build_library_vault(tmp_path / f"v_{section}")
        set_config(paths, section, **values)
        ctx = context(paths.root)
        with pytest.raises(SidecarError) as caught:
            call(ctx, "reader.library_compare_keep", {"askId": "la_x"})
        assert caught.value.code == "reader_compare_keep_disabled"
        assert "compareKeep" not in call(ctx, "reader.prompt_contract", {})


# -- marks, reopen, "you compared these on …", the card ----------------------------------------


def test_marks_reopen_and_compared_on(compared):
    _paths, ctx, repository, _spans, asked, table = compared
    kept = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    keys = [obj["key"] for obj in kept["kept"]["objects"]]
    for key in keys:
        extraction, span = key.split(":", 1)
        marks = call(ctx, "reader.kept_comparisons", {"extractionId": extraction})
        assert span in {mark["spanId"] for mark in marks["marks"]}
        mark = next(m for m in marks["marks"] if m["spanId"] == span)
        assert mark["askIds"] == [asked["askId"]] and mark["otherSources"]
    reopened = call(ctx, "reader.library_compare_reopen", {"askId": asked["askId"]})
    assert {row["key"] for row in reopened["rows"]} == set(keys)
    assert reopened["header"] == "differences kept · each line quotes its own source"
    assert reopened["keptRelations"][0]["fine"] == "different_notation"
    # A later library ask on the same passages says when they were compared.
    later = call(ctx, "reader.library_ask", {"query": QUESTION, "extractionId": "ext_text", "spanIds": ["t3"],
                                             "learningObjectIds": ["lo_matrices"]})
    shared = {key for entry in later["comparedOn"] for key in entry["keys"]}
    assert shared and shared <= set(keys) and later["comparedOn"][0]["askId"] == asked["askId"]


def test_perspectives_are_passed_stored_and_reported(library, monkeypatch):
    _paths, ctx, repository, _spans, asked = library
    llm = _fake_service(monkeypatch)
    table = call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": PINS,
                                                  "requestedPerspectives": [" geometric view ", "application",
                                                                            "Geometric view"]})
    assert table["requestedPerspectives"] == ["geometric view", "application"]
    assert table["missingPerspectives"] == ["application"]  # the fake satisfies only the first
    row = [r for r in ask_rows(repository) if r["id"] == asked["askId"]][0]
    assert json.loads(row["requested_perspectives_json"]) == ["geometric view", "application"]
    assert any(name == "SourceComparison" for _purpose, name in llm.calls)


def test_a_second_comparison_of_a_kept_question_is_kept_on_its_own_row(compared, monkeypatch):
    _paths, ctx, repository, _spans, asked, _table = compared
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    _stored(monkeypatch, ctx, repository, asked["askId"], ["disagreement"])
    second = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    assert second["askId"] != asked["askId"] and second["alreadyKept"] is False
    again = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    assert again["askId"] == second["askId"] and again["alreadyKept"] is True
    kept_rows = [r for r in ask_rows(repository) if r["kept_at"]]
    assert len(kept_rows) == 2
    assert len({json.loads(r["kept_json"])["comparison_id"] for r in kept_rows}) == 2


def test_the_router_cards_read_is_typed_and_pure(compared):
    _paths, ctx, repository, _spans, asked, _table = compared
    assert KC.kept_comparisons_for_card(repository, learning_object_ids=["lo_matrices"]) == []
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "takes": [
        {"text": "mine", "keys": [_table["rows"][0]["key"]]}]})
    before = _all_counts(repository)
    row = [r for r in ask_rows(repository) if r["id"] == asked["askId"]][0]
    los = json.loads(row["kept_json"])["learning_object_ids"]
    assert los
    card = KC.kept_comparisons_for_card(repository, learning_object_ids=los, as_of="2999-01-01T00:00:00Z")
    assert len(card) == 1 and card[0]["status"] == "proposed" and card[0]["takes"] == 1
    assert card[0]["relations"][0] == {"relation_type": "refines", "fine": "different_notation",
                                       "relation_id": card[0]["relations"][0]["relation_id"]}
    assert "mine" not in json.dumps(card)  # no prose: the take is counted, never quoted
    assert KC.kept_comparisons_for_card(repository, learning_object_ids=los, as_of="2000-01-01T00:00:00Z") == []
    assert KC.kept_comparisons_for_card(repository, learning_object_ids=["lo_unrelated"]) == []
    assert _all_counts(repository) == before  # a pure read


def test_every_rw4d_event_is_salience_only(compared):
    from learnloop.attempts import salience_firewall as SF

    _paths, ctx, repository, _spans, asked, _table = compared
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    call(ctx, "reader.library_compare_reopen", {"askId": asked["askId"]})
    call(ctx, "reader.library_compare_remove", {"askId": asked["askId"]})
    events = [event for event in repository.reader_interaction_events(kind="reader_action_invoked")
              if (event.get("payload") or {}).get("event") in KC.EVENTS]
    assert {event["payload"]["event"] for event in events} == set(KC.EVENTS)
    for event in events:
        assert SF.is_salience_only(event["payload"])


def test_the_report_counts_keeps_takes_and_relations_without_quoting(compared):
    from learnloop.reader.reader_report import build_reader_report

    _paths, ctx, repository, _spans, asked, table = compared
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "takes": [
        {"text": "a private thought", "keys": [table["rows"][0]["key"]]}]})
    report = build_reader_report(repository.sqlite_path)
    assert report["comparisons"] == {"kept": 1, "removed": 0, "by_caller": {"learner": 1}, "takes": 1,
                                     "relations_by_type": {"refines": 1},
                                     "relations_by_label": {"different_notation": 1}}
    assert "a private thought" not in json.dumps(report, default=str)
    assert report["library"]["asks"] == 1


# -- review fixes (reader-rw4d Codex review F1, F2, F4-F7, F9) ------------------------------------


def _keep_counts(repository) -> dict[str, int]:
    return table_counts(repository, PROPOSAL_TABLES)


def _ask(repository, ask_id: str) -> dict:
    return [r for r in ask_rows(repository) if r["id"] == ask_id][0]


def _stored_relations(monkeypatch, ctx, repository, ask_id: str, relations: list[dict]):
    """A stored comparison of the two pins with exactly these relations (each
    may override the quotes or the statement of the default s1-s2 relation)."""

    import learnloop.instructional.sources as service

    table = _stored(monkeypatch, ctx, repository, ask_id, [])
    stored_id = table["comparisonId"]
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        comparison = json.loads(connection.execute(
            "SELECT comparison_json FROM source_comparisons WHERE id = ?", (stored_id,)).fetchone()[0])
    sources = comparison["sources"]
    quote = {source["ref"]: " ".join(source["passage"].split()[:4]) for source in sources}
    rels = [{"left_ref": "s1", "right_ref": "s2", "statement": f"{rel['relation']} line",
             "left_quote": quote["s1"], "right_quote": quote["s2"], "authorship": "ai", **rel} for rel in relations]
    with repository.connection() as connection:
        connection.execute("UPDATE source_comparisons SET comparison_json = ? WHERE id = ?",
                           (json.dumps({**comparison, "relations": rels}), stored_id))
        connection.commit()
    monkeypatch.setattr(service, "propose_comparison", lambda *a, **k: Comparison(
        status="ok", policy="reading", comparison_id=stored_id, sources=sources, relations=rels))
    return call(ctx, "reader.library_compare", {"askId": ask_id, "pinnedSpanKeys": PINS})


def test_a_keep_interrupted_after_its_proposals_writes_nothing_and_a_retry_keeps_once(compared, monkeypatch):
    """F1: the proposals, the keep record and its event are one transaction."""

    _paths, ctx, repository, _spans, asked, table = compared
    vault, _repo = ctx.require_vault()
    real = KC.SO.link_relation

    def crash(*args, **kwargs):
        raise RuntimeError("the process died here")

    monkeypatch.setattr(KC.SO, "link_relation", crash)
    before = _all_counts(repository)
    with pytest.raises(RuntimeError):
        KC.keep(vault, repository, asked["askId"])
    assert _all_counts(repository) == before  # no orphaned object, citation, relation or event
    assert _ask(repository, asked["askId"])["kept_json"] is None
    monkeypatch.setattr(KC.SO, "link_relation", real)
    kept = KC.keep(vault, repository, asked["askId"])
    assert kept["already_kept"] is False
    assert _keep_counts(repository)["source_objects"] == len(table["rows"])


def test_an_interrupted_remove_leaves_the_keep_whole(compared, monkeypatch):
    """F1: Remove's supersessions and the cleared keep commit together."""

    _paths, ctx, repository, _spans, asked, table = compared
    vault, _repo = ctx.require_vault()
    KC.keep(vault, repository, asked["askId"], takes=[{"text": "mine", "keys": [table["rows"][0]["key"]]}])
    before = _all_counts(repository)

    def crash(*args, **kwargs):
        raise RuntimeError("the process died here")

    monkeypatch.setattr(KC.SO, "supersede_relation", crash)
    with pytest.raises(RuntimeError):
        KC.remove(vault, repository, asked["askId"])
    assert _all_counts(repository) == before  # no object superseded without its relations
    assert _ask(repository, asked["askId"])["kept_at"]
    heads = {row["status"] for row in _rows(repository, "SELECT status FROM source_object_versions")}
    assert heads == {"proposed"}


def test_concurrent_keeps_of_one_comparison_write_one_set(compared, monkeypatch):
    """F1: a second keep that starts while the first is writing waits for it,
    then reads the keep (no second set of proposals, no lost keep)."""

    import threading
    import time

    _paths, ctx, repository, _spans, asked, table = compared
    vault, _repo = ctx.require_vault()
    real = KC.SO.author_source_object
    results: dict[str, object] = {}
    started = threading.Event()

    def second() -> None:
        started.set()
        try:
            results["second"] = KC.keep(vault, repository, asked["askId"])
        except Exception as exc:  # noqa: BLE001 - recorded for the assertion
            results["second"] = exc

    def slow(*args, **kwargs):
        if "thread" not in results:
            results["thread"] = threading.Thread(target=second)
            results["thread"].start()
            started.wait(5)
            time.sleep(0.3)  # the second keep is now at its first read
        return real(*args, **kwargs)

    monkeypatch.setattr(KC.SO, "author_source_object", slow)
    first = KC.keep(vault, repository, asked["askId"])
    results["thread"].join(30)
    second_result = results["second"]
    assert not isinstance(second_result, Exception), second_result
    assert first["already_kept"] is False and second_result["already_kept"] is True
    assert _keep_counts(repository)["source_objects"] == len(table["rows"])
    assert second_result["ask_id"] == first["ask_id"]


def test_a_take_on_an_older_kept_comparison_stays_on_it(compared, monkeypatch):
    """F2: the take names the comparison it was typed under, not the ask's newest."""

    _paths, ctx, repository, _spans, asked, table = compared
    vault, _repo = ctx.require_vault()
    first_id = table["comparisonId"]
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "comparisonId": first_id})
    newer = _stored(monkeypatch, ctx, repository, asked["askId"], ["disagreement"])
    assert newer["comparisonId"] != first_id and newer["kept"] is None
    rows_before = len(ask_rows(repository))
    take = {"text": "on the first comparison", "keys": [table["rows"][0]["key"]]}
    added = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "comparisonId": first_id,
                                                      "takes": [take]})
    assert added["askId"] == asked["askId"] and added["alreadyKept"] is True and added["addedTakes"] == 1
    assert len(ask_rows(repository)) == rows_before  # nothing forked, the newer comparison not kept
    kept = json.loads(_ask(repository, asked["askId"])["kept_json"])
    assert kept["comparison_id"] == first_id and [t["learner_text"] for t in kept["takes"]] == [take["text"]]
    # Keeping the newer comparison names it, and it gets its own row.
    newer_kept = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"],
                                                           "comparisonId": newer["comparisonId"]})
    assert newer_kept["askId"] != asked["askId"] and newer_kept["alreadyKept"] is False
    # A comparison the ask no longer shows (and nothing keeps) is refused, writing nothing.
    before = _all_counts(repository)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "comparisonId": "scmp_elsewhere"})
    assert caught.value.code == "stale_comparison"
    assert _all_counts(repository) == before
    # Remove names its comparison too: the older keep's own row.
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_compare_remove", {"askId": asked["askId"], "comparisonId": newer["comparisonId"]})
    assert caught.value.code == "stale_comparison"


def test_replaying_a_take_does_not_duplicate_it_even_at_the_limit(compared):
    """F4: a take's key is its passages and its words; a replay adds nothing."""

    _paths, ctx, repository, _spans, asked, table = compared
    key = table["rows"][0]["key"]
    take = {"text": "the same words", "keys": [key]}
    first = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "takes": [take]})
    counts = _keep_counts(repository)
    replay = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "takes": [take]})
    assert replay["addedTakes"] == 0 and _keep_counts(repository) == counts
    assert [t["id"] for t in replay["kept"]["takes"]] == [t["id"] for t in first["kept"]["takes"]]
    # Twice in one request is one take, too.
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "takes": [
        {"text": "twice", "keys": [key]}, {"text": " twice ", "keys": [key]}]})
    assert _keep_counts(repository)["source_object_relations"] == counts["source_object_relations"] + 1
    rest = [{"text": f"take {n}", "keys": [key]} for n in range(KC.MAX_TAKES - 2)]
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "takes": rest})
    full = _keep_counts(repository)
    # At the limit, replaying a take that is kept succeeds and writes nothing.
    again = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "takes": [rest[-1]]})
    assert again["addedTakes"] == 0 and len(again["kept"]["takes"]) == KC.MAX_TAKES
    assert _keep_counts(repository) == full
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "takes": [{"text": "new", "keys": [key]}]})
    assert caught.value.code == "validation_error"


def test_reopen_shows_only_the_relations_kept_among_same_labelled_pairs(library, monkeypatch):
    """F5: two relations on the same pair with the same label; one fails Keep's recheck."""

    _paths, ctx, repository, _spans, asked = library
    _stored_relations(monkeypatch, ctx, repository, asked["askId"], [
        {"relation": "disagreement", "statement": "the surviving statement"},
        {"relation": "disagreement", "statement": "the rejected statement",
         "left_quote": "words that are nowhere in the passage"},
    ])
    kept = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    assert len(kept["kept"]["relations"]) == 1
    reopened = call(ctx, "reader.library_compare_reopen", {"askId": asked["askId"]})
    shown = json.dumps(reopened)
    assert "the surviving statement" in shown
    assert "the rejected statement" not in shown and "words that are nowhere in the passage" not in shown


def test_the_card_reads_keeps_takes_and_removals_as_of(compared):
    """F6: a historical card does not change with later takes or a remove."""

    from datetime import datetime, UTC

    from learnloop.clock import FrozenClock

    _paths, ctx, repository, _spans, asked, table = compared
    vault, _repo = ctx.require_vault()
    on = lambda day: FrozenClock(datetime(2026, 10, day, 9, tzinfo=UTC))  # noqa: E731
    key = table["rows"][0]["key"]
    KC.keep(vault, repository, asked["askId"], takes=[{"text": "first", "keys": [key]}], clock=on(3))
    los = json.loads(_ask(repository, asked["askId"])["kept_json"])["learning_object_ids"]

    def card(day: int | None):
        as_of = None if day is None else f"2026-10-{day:02d}T12:00:00Z"
        return KC.kept_comparisons_for_card(repository, learning_object_ids=los, as_of=as_of)

    before = card(4)
    assert len(before) == 1 and before[0]["takes"] == 1
    KC.keep(vault, repository, asked["askId"], takes=[{"text": "second", "keys": [key]}], clock=on(5))
    assert card(4) == before and card(5)[0]["takes"] == 2
    KC.remove(vault, repository, asked["askId"], clock=on(6))
    assert card(4) == before and card(5)[0]["takes"] == 2
    assert card(6) == [] and card(None) == []
    # Kept again on the 7th: the card of the 4th is still the first keep; the 7th's is the new one.
    KC.keep(vault, repository, asked["askId"], clock=on(7))
    assert card(4) == before and card(6) == []
    latest = card(7)
    assert len(latest) == 1 and latest[0]["takes"] == 0 and latest[0]["kept_at"] == "2026-10-07T09:00:00Z"
    assert card(None) == latest


def test_relation_successors_record_what_they_supersede(library, monkeypatch):
    """F7: two indistinguishable relations (both 'refines', same endpoints, no
    wording) each have their own head after a remove, a re-keep and a remove."""

    _paths, ctx, repository, _spans, asked = library
    vault, _repo = ctx.require_vault()
    _stored(monkeypatch, ctx, repository, asked["askId"], ["different_assumptions", "complementary"])
    kept = KC.keep(vault, repository, asked["askId"])
    first_ids = [rel["id"] for rel in kept["kept"]["relations"]]
    rows = {r["id"]: r for r in _rows(repository, "SELECT * FROM source_object_relations")}
    assert {rows[i]["relation_type"] for i in first_ids} == {"refines"}
    assert all(KC.relation_head(repository, rid)["id"] == rid for rid in first_ids)  # a proposal is its own head
    KC.remove(vault, repository, asked["askId"])
    heads = [KC.relation_head(repository, rid) for rid in first_ids]
    assert len({head["id"] for head in heads}) == 2 and not set(first_ids) & {head["id"] for head in heads}
    assert {(head["review_status"], head["version_ordinal"]) for head in heads} == {("superseded", 2)}
    lineage = KC.relation_lineage(repository)
    assert {lineage[head["id"]] for head in heads} == set(first_ids)
    again = KC.keep(vault, repository, asked["askId"])
    second_ids = [rel["id"] for rel in again["kept"]["relations"]]
    KC.remove(vault, repository, asked["askId"])
    assert [KC.relation_head(repository, rid)["id"] for rid in first_ids] == [head["id"] for head in heads]
    second_heads = {KC.relation_head(repository, rid)["id"] for rid in second_ids}
    assert len(second_heads) == 2 and not second_heads & {head["id"] for head in heads}


def test_a_passages_mark_lists_every_comparison_kept_on_it(compared, monkeypatch):
    """F9: two kept comparisons share a passage; its mark names both."""

    _paths, ctx, repository, _spans, asked, _table = compared
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    _stored(monkeypatch, ctx, repository, asked["askId"], ["disagreement"])
    second = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    marks = call(ctx, "reader.kept_comparisons", {"extractionId": "ext_text"})["marks"]
    (mark,) = [m for m in marks if m["spanId"] == "t3"]
    assert set(mark["askIds"]) == {asked["askId"], second["askId"]}
    assert {entry["askId"] for entry in mark["comparisons"]} == {asked["askId"], second["askId"]}
    assert all(entry["keptAt"] and entry["query"] == QUESTION for entry in mark["comparisons"])
