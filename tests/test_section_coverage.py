"""Curriculum C0a: section coverage and reader.correspondents (spec_deliverable_curriculum_v1 §6, §9, §12.3).

Every model is a fake (``CoverageJudgeFake``); no test reaches a network.
"""
from __future__ import annotations

import json

import pytest

from learnloop.curriculum import section_coverage as SC
from learnloop.db.stores import section_coverage as store
from learnloop.vault.loader import load_vault
from tests.section_coverage_fixtures import (
    BOOK_EIGEN,
    HELD_OUT_SENTINEL,
    CoverageJudgeFake,
    build_coverage_vault,
    table_counts,
)
from tests.source_retrieval_fakes import EXAM_QUESTION


@pytest.fixture
def vault_paths(tmp_path):
    return build_coverage_vault(tmp_path / "vault")


def _rows(repository, lo_id="lo_eigen"):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM section_coverage WHERE learning_object_id = ? ORDER BY candidate_rank, id", (lo_id,))]


# -- the library a model may read -------------------------------------------------------------------


def test_the_library_leaves_out_exam_and_held_out_material(vault_paths):
    paths, repository = vault_paths
    vault = load_vault(paths.root)
    library = SC.Library(vault, repository)
    assert "ext_exam" in library.left_out and "ext_exam" not in library.extractions
    lay = library.reading("ext_lay")
    assert "lay_held" in lay.withheld and "lay_held" not in lay.sections
    assert library.section("ext_lay", "lay_held") is None
    assert not any(HELD_OUT_SENTINEL in text for text in lay.texts.values())
    # The headers are the titles, never a passage.
    eigen = library.section("ext_book", BOOK_EIGEN)
    assert eigen.title == "Chapter 5 Eigenvalues" and "s1" not in eigen.span_ids


def test_candidates_are_provenance_then_retrieval_per_source(vault_paths):
    paths, repository = vault_paths
    vault = load_vault(paths.root)
    library = SC.Library(vault, repository)
    found = SC.candidates_for(vault, repository, library, "lo_eigen")
    assert found[0].key == ("ext_book", BOOK_EIGEN) and found[0].origin == "provenance"
    keys = [candidate.key for candidate in found]
    assert ("ext_lay", "lay_eigen") in keys and ("ext_lay", "lay_char") in keys
    assert all(candidate.extraction_id != "ext_exam" for candidate in found)
    assert ("ext_lay", "lay_held") not in keys
    assert [candidate.rank for candidate in found] == list(range(len(found)))
    assert len(set(keys)) == len(keys)


def test_a_big_book_never_crowds_out_a_small_one(tmp_path):
    paths, repository = build_coverage_vault(tmp_path / "vault", big=True)
    vault = load_vault(paths.root)
    library = SC.Library(vault, repository)
    found = SC.candidates_for(vault, repository, library, "lo_eigen")
    retrieved = [candidate for candidate in found if candidate.origin == "retrieval"]
    per_source: dict[str, int] = {}
    for candidate in retrieved:
        source = library.extractions[candidate.extraction_id].source_id
        per_source[source] = per_source.get(source, 0) + 1
    assert per_source.get("src_big") == SC.SECTIONS_PER_SOURCE
    assert per_source.get("src_lay", 0) >= 1
    assert max(per_source.values()) <= SC.SECTIONS_PER_SOURCE


# -- one judgment ------------------------------------------------------------------------------------


def test_one_listwise_judgment_writes_one_row_per_candidate_and_caches(vault_paths):
    paths, repository = vault_paths
    vault = load_vault(paths.root)
    judge = CoverageJudgeFake(treatments={"5.2 The characteristic equation": "introduces"}, notation="uses t for λ")
    result = SC.judge(vault, repository, "lo_eigen", client=judge)
    assert result.status == "ready" and judge.calls == 1
    rows = _rows(repository)
    assert len(rows) == result.candidates == len(judge.contexts[0]["candidates"])
    by_section = {(row["extraction_id"], row["section_id"]): row for row in rows}
    assert by_section[("ext_lay", "lay_char")]["treatment"] == "introduces"
    assert by_section[("ext_book", BOOK_EIGEN)]["origin"] == "provenance"
    assert by_section[("ext_book", BOOK_EIGEN)]["notation_md"] == "uses t for λ"
    assert {row["state_key"] for row in rows} == {result.state_key}
    assert all(row["ledger_id"].startswith("scv_") and row["learner_override"] is None for row in rows)
    with repository.connection() as connection:
        ledger = connection.execute("SELECT COUNT(*) FROM judgment_ledger WHERE task = 'section_coverage' "
                                    "AND judge = 'llm'").fetchone()[0]
    assert ledger == len(rows)
    # The same state again: no call, no new row.
    again = SC.judge(vault, repository, "lo_eigen", client=judge)
    assert again.status == "fresh" and judge.calls == 1 and len(_rows(repository)) == len(rows)


def test_no_exam_or_held_out_text_reaches_the_judge(vault_paths):
    """G-C1: the exam source's question and the held-out unit's text are sentinels."""

    paths, repository = vault_paths
    vault = load_vault(paths.root)
    judge = CoverageJudgeFake()
    SC.judge(vault, repository, "lo_eigen", client=judge)
    for lo_id in ("lo_matrices", "lo_inner"):
        SC.judge(vault, repository, lo_id, client=judge)
    assert judge.prompts
    for prompt in judge.prompts:
        assert EXAM_QUESTION not in prompt and "Exam question" not in prompt
        assert "HELDOUTSENTINEL" not in prompt
    with repository.connection() as connection:
        named = {row[0] for row in connection.execute("SELECT DISTINCT extraction_id || '/' || section_id "
                                                      "FROM section_coverage")}
    assert not any(name.startswith("ext_exam/") for name in named) and "ext_lay/lay_held" not in named


def test_rw4e_proposals_are_written_by_the_coverage_judge(vault_paths):
    paths, repository = vault_paths
    vault = load_vault(paths.root)
    SC.judge(vault, repository, "lo_eigen", client=CoverageJudgeFake())
    with repository.connection() as connection:
        judges = {json.loads(row[0]).get("judge") for row in connection.execute(
            "SELECT content_json FROM source_object_versions WHERE json_extract(content_json, '$.kind') = "
            "'instructional_role'")}
    assert judges == {"section_coverage_judge"}


def test_a_changed_statement_makes_old_rows_stale_until_rejudged(vault_paths):
    from learnloop.vault.yaml_io import read_yaml, write_yaml

    paths, repository = vault_paths
    vault = load_vault(paths.root)
    SC.judge(vault, repository, "lo_eigen", client=CoverageJudgeFake())
    library = SC.Library(vault, repository)
    assert SC.standing(vault, repository, library, ["lo_eigen"])["lo_eigen"]
    path = paths.learning_object_path("linear-algebra", "lo_eigen")
    lo = read_yaml(path)
    lo["summary"] = "An eigenvalue t of A has a nonzero x with Ax = tx."
    write_yaml(path, lo)
    vault = load_vault(paths.root)
    assert SC.standing(vault, repository, SC.Library(vault, repository), ["lo_eigen"])["lo_eigen"] == {}
    judge = CoverageJudgeFake()
    assert SC.judge(vault, repository, "lo_eigen", client=judge).status == "ready" and judge.calls == 1


def test_models_off_and_an_unrouted_judge_make_no_call(vault_paths, monkeypatch):
    paths, repository = vault_paths
    vault = load_vault(paths.root)
    result = SC.judge(vault, repository, "lo_eigen")
    assert result.status == "unavailable" and result.reason == "models_off"
    assert _rows(repository) == []


def test_a_failed_judgment_writes_nothing(vault_paths):
    from learnloop.ai.errors import AIProviderUnavailable

    paths, repository = vault_paths
    vault = load_vault(paths.root)
    result = SC.judge(vault, repository, "lo_eigen", client=CoverageJudgeFake(fail=AIProviderUnavailable("down")))
    assert result.status == "failed" and _rows(repository) == []


def test_an_answer_that_skips_a_section_is_never_stored(vault_paths):
    paths, repository = vault_paths
    vault = load_vault(paths.root)
    result = SC.judge(vault, repository, "lo_eigen", client=CoverageJudgeFake(omit=("5.2 The characteristic equation",)))
    assert result.status == "failed" and _rows(repository) == []


# -- reader.correspondents ---------------------------------------------------------------------------


def test_correspondents_join_on_the_lo_and_are_symmetric(vault_paths):
    paths, repository = vault_paths
    vault = load_vault(paths.root)
    SC.judge(vault, repository, "lo_eigen", client=CoverageJudgeFake(
        treatments={"5.2 The characteristic equation": "introduces", "6.1 Inner product and orthogonality": "not_about"}))
    before = table_counts(repository)
    view = SC.correspondents(vault, repository, "ext_book", BOOK_EIGEN, search_fallback=False)
    assert table_counts(repository) == before  # no write
    assert view["status"] == "judged"
    group = view["learning_objects"][0]
    assert group["learning_object_id"] == "lo_eigen" and group["title"] == "Eigenvalues"
    (lay,) = [source for source in group["sources"] if source["source_id"] == "src_lay"]
    titles = [section["title"] for section in lay["sections"]]
    # introduces before develops; not_about never listed; the origin's own book never listed.
    assert titles[0] == "5.2 The characteristic equation" and "6.1 Inner product and orthogonality" not in titles
    assert all(source["source_id"] != "src_book" for source in group["sources"])
    first = lay["sections"][0]
    assert first["treatment_words"] == "introduces it"
    assert first["jump"] == {"extraction_id": "ext_lay", "section_id": "lay_char", "span_id": "s5"}
    # From the other side: the origin is listed.
    back = SC.correspondents(vault, repository, "ext_lay", "lay_char", search_fallback=False)
    names = [section["section_id"] for group in back["learning_objects"] for source in group["sources"]
             for section in source["sections"]]
    assert BOOK_EIGEN in names


def test_the_search_fallback_is_labelled_unchecked_and_writes_nothing(vault_paths):
    paths, repository = vault_paths
    vault = load_vault(paths.root)
    before = table_counts(repository)
    view = SC.correspondents(vault, repository, "ext_book", BOOK_EIGEN)
    assert table_counts(repository) == before
    assert view["status"] == "unchecked" and view["learning_objects"] == []
    sources = view["search"]["sources"]
    assert sources and all(source["source_id"] not in ("src_book", "src_exam") for source in sources)
    for source in sources:
        for section in source["sections"]:
            assert section["label"] == SC.UNCHECKED_LABEL and section["treatment"] is None
            assert section["section_id"] != "lay_held"
    assert view["search"]["correctable_learning_object_ids"] == ["lo_eigen"]
    # Off, the quiet read shows nothing.
    assert SC.correspondents(vault, repository, "ext_book", BOOK_EIGEN, search_fallback=False)["status"] == "none"


def test_a_protected_section_has_no_correspondents(vault_paths):
    paths, repository = vault_paths
    vault = load_vault(paths.root)
    assert SC.correspondents(vault, repository, "ext_lay", "lay_held")["status"] == "withheld"
    assert SC.correspondents(vault, repository, "ext_exam", "exam_q")["status"] == "withheld"


def test_a_changed_section_drops_its_row(vault_paths):
    paths, repository = vault_paths
    vault = load_vault(paths.root)
    SC.judge(vault, repository, "lo_eigen", client=CoverageJudgeFake())
    with repository.connection() as connection:
        connection.execute("UPDATE source_document_blocks SET content_hash = 'changed' "
                           "WHERE extraction_id = 'ext_lay' AND span_id = 's6'")
        connection.commit()
    library = SC.Library(vault, repository)
    rows = SC.standing(vault, repository, library, ["lo_eigen"])["lo_eigen"]
    assert ("ext_lay", "lay_char") not in rows and ("ext_book", BOOK_EIGEN) in rows


# -- corrections -------------------------------------------------------------------------------------


def test_corrections_stand_over_the_judge_across_rejudgments(vault_paths):
    paths, repository = vault_paths
    vault = load_vault(paths.root)
    SC.judge(vault, repository, "lo_eigen", client=CoverageJudgeFake())
    SC.correct(vault, repository, "ext_lay", "lay_char", "lo_eigen", "not_about", clock=None)
    SC.correct(vault, repository, "ext_lay", "lay_ortho", "lo_eigen", "is_about", text="really about eigen-bases")
    library = SC.Library(vault, repository)
    rows = SC.standing(vault, repository, library, ["lo_eigen"])["lo_eigen"]
    assert rows[("ext_lay", "lay_char")].treatment == "not_about" and rows[("ext_lay", "lay_char")].by == "learner"
    assert rows[("ext_lay", "lay_ortho")].about and rows[("ext_lay", "lay_ortho")].learner_text == "really about eigen-bases"
    view = SC.correspondents(vault, repository, "ext_book", BOOK_EIGEN, search_fallback=False)
    listed = [section["section_id"] for group in view["learning_objects"] for source in group["sources"]
              for section in source["sections"]]
    assert "lay_char" not in listed and "lay_ortho" in listed
    # A learner link is a candidate of the next judgment; the correction still stands after it.
    SC.correct(vault, repository, "ext_lay", "lay_eigen", "lo_eigen", "none")
    judge = CoverageJudgeFake(treatments={"5.2 The characteristic equation": "introduces"})
    SC.judge(vault, repository, "lo_eigen", client=judge)
    titles = [candidate["title"] for candidate in judge.contexts[-1]["candidates"]] if judge.contexts else []
    rows = SC.standing(vault, repository, SC.Library(vault, repository), ["lo_eigen"])["lo_eigen"]
    assert rows[("ext_lay", "lay_char")].treatment == "not_about"
    with repository.connection() as connection:
        learner = connection.execute("SELECT COUNT(*) FROM judgment_ledger WHERE task = 'section_coverage' "
                                     "AND judge = 'learner_card'").fetchone()[0]
    assert learner == 3
    assert "6.1 Inner product and orthogonality" in titles or not judge.contexts


def test_a_correction_on_protected_material_is_refused(vault_paths):
    paths, repository = vault_paths
    vault = load_vault(paths.root)
    with pytest.raises(SC.CoverageError) as caught:
        SC.correct(vault, repository, "ext_lay", "lay_held", "lo_eigen", "is_about")
    assert caught.value.code == "withheld"
    with pytest.raises(SC.CoverageError):
        SC.correct(vault, repository, "ext_lay", "lay_eigen", "lo_eigen", "maybe")


def test_the_table_is_append_only(vault_paths):
    import sqlite3

    paths, repository = vault_paths
    vault = load_vault(paths.root)
    SC.correct(vault, repository, "ext_lay", "lay_eigen", "lo_eigen", "is_about")
    with repository.connection() as connection:
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("UPDATE section_coverage SET learner_text = 'x'")
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("DELETE FROM section_coverage")
        assert store.counts(connection)["learner_rows"] == 1
