"""Reader CA5a: find this section in my other books (ux_reader_compare_ask_v1 §6.2, §6.3, §13).

The Guide's pressed action reads C0a's ``reader.correspondents``: for a
section with no judged coverage, the live search hits grouped by book, each
"found by search, not checked", with no treatment words, no model call and no
write. *Not about this* on a hit is C0a's correction. The presentation's kill
switch is ``reader.correspondence.enabled``, respecting ``curriculum.enabled``.

Every model is a fake; nothing leaves the machine.
"""
from __future__ import annotations

from learnloop.config.schema import LearnLoopConfig
from learnloop.source_retrieval import section_coverage as SC
from tests.reading_path_fixtures import call, context
from tests.section_coverage_fixtures import BOOK_EIGEN, CoverageJudgeFake, build_coverage_vault, table_counts

FIND = {"extraction_id": "ext_book", "section_id": BOOK_EIGEN}


def _ctx(paths, **attrs):
    return context(paths.root, coverage_inline=True, **attrs)


def _hits(view):
    return [(source["sourceId"], section["sectionId"]) for source in view["search"]["sources"]
            for section in source["sections"]]


# -- the switch ---------------------------------------------------------------------------------------


def test_the_switch_is_on_by_default():
    assert LearnLoopConfig().reader.correspondence.enabled is True


def test_the_prompt_contract_carries_the_action_only_while_both_switches_are_on(tmp_path):
    paths, _repository = build_coverage_vault(tmp_path / "on")
    contract = call(_ctx(paths), "reader.prompt_contract", {})
    assert contract["correspondence"] == {"enabled": True, "findSection": True}

    for name, config in (("reader_off", "[reader.correspondence]\nenabled = false"),
                         ("curriculum_off", "[curriculum]\nenabled = false")):
        paths, _repository = build_coverage_vault(tmp_path / name, config=config)
        contract = call(_ctx(paths), "reader.prompt_contract", {})
        assert "correspondence" not in contract, name


def test_switched_off_the_rpcs_keep_c0a_behaviour(tmp_path):
    """The presentation's switch hides the action; the data stays curriculum.enabled's."""

    paths, repository = build_coverage_vault(tmp_path / "vault", config="[reader.correspondence]\nenabled = false")
    ctx = _ctx(paths)
    before = table_counts(repository)
    view = call(ctx, "reader.correspondents", FIND)
    assert view["status"] == "unchecked" and table_counts(repository) == before


# -- the pressed read: unchecked hits grouped by book --------------------------------------------------


def test_the_hits_are_grouped_by_book_unchecked_and_write_nothing(tmp_path):
    paths, repository = build_coverage_vault(tmp_path / "vault", big=True)
    judge = CoverageJudgeFake()
    ctx = _ctx(paths, coverage_judge_client=judge)
    before = table_counts(repository)
    view = call(ctx, "reader.correspondents", FIND)
    assert table_counts(repository) == before and judge.calls == 0
    assert view["status"] == "unchecked" and view["learningObjects"] == []
    sources = view["search"]["sources"]
    # One group per other book, each book once, never the open book or the exam.
    ids = [source["sourceId"] for source in sources]
    assert len(ids) == len(set(ids)) >= 2
    assert set(ids) <= {"src_lay", "src_big"}
    for source in sources:
        assert source["sourceTitle"] in ("Lay", "Big Book")
        assert source["sections"]
        for section in source["sections"]:
            # Grouped under its own book, labelled unchecked, no treatment words.
            assert section["sourceId"] == source["sourceId"]
            assert section["sourceTitle"] == source["sourceTitle"]
            assert section["label"] == SC.UNCHECKED_LABEL == "found by search, not checked"
            assert section["treatment"] is None and "treatmentWords" not in section
            assert section["by"] == "search" and section["title"]
            assert section["sectionId"] != "lay_held"
            # Where peek and go there land: the section's first readable passage.
            assert section["jump"]["extractionId"] == section["extractionId"]
            assert section["jump"]["sectionId"] == section["sectionId"] and section["jump"]["spanId"]
    assert view["search"]["label"] == SC.UNCHECKED_LABEL
    assert view["search"]["correctableLearningObjectIds"] == ["lo_eigen"]


def test_judged_coverage_is_what_the_quiet_read_reports(tmp_path):
    """The Reader hides the action when the quiet read (no fallback) finds judged coverage."""

    paths, repository = build_coverage_vault(tmp_path / "vault")
    ctx = _ctx(paths, coverage_judge_client=CoverageJudgeFake(treatments={"5.2 The characteristic equation":
                                                                          "introduces"}))
    quiet = call(ctx, "reader.correspondents", {**FIND, "search_fallback": False})
    assert quiet["status"] == "none" and quiet["search"] is None
    call(ctx, "curriculum.cover", FIND)
    quiet = call(ctx, "reader.correspondents", {**FIND, "search_fallback": False})
    assert quiet["status"] == "judged"
    # Pressed on a judged section, the read is the judged list, never search hits.
    pressed = call(ctx, "reader.correspondents", FIND)
    assert pressed["status"] == "judged" and pressed["search"] is None


# -- not about this ----------------------------------------------------------------------------------


def test_not_about_this_on_a_hit_is_a_c0a_correction_with_undo(tmp_path):
    paths, repository = build_coverage_vault(tmp_path / "vault", big=True)
    ctx = _ctx(paths)
    view = call(ctx, "reader.correspondents", FIND)
    first = view["search"]["sources"][0]["sections"][0]
    los = view["search"]["correctableLearningObjectIds"]
    before = table_counts(repository)
    for lo_id in los:
        out = call(ctx, "curriculum.coverage_correct", {
            "extraction_id": first["extractionId"], "section_id": first["sectionId"],
            "learning_object_id": lo_id, "choice": "not_about"})
        assert out["correction"]["learnerOverride"] == "not_about"
    after = table_counts(repository)
    # Exactly C0a's correction: one learner row and one learner_card verdict per LO, nothing else.
    changed = {name: after[name] - before[name] for name in after if after[name] != before.get(name)}
    assert changed == {"section_coverage": len(los), "judgment_ledger": len(los)}
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT origin, learner_override, treatment FROM section_coverage WHERE extraction_id = ? "
            "AND section_id = ?", (first["extractionId"], first["sectionId"])).fetchall()
        judges = {row[0] for row in connection.execute(
            "SELECT judge FROM judgment_ledger WHERE task = 'section_coverage'")}
    assert [tuple(row) for row in rows] == [("learner", "not_about", None)] * len(los)
    assert judges == {"learner_card"}
    # The line goes, and only it.
    again = call(ctx, "reader.correspondents", FIND)
    assert (first["sourceId"], first["sectionId"]) not in _hits(again)
    assert set(_hits(again)) == set(_hits(view)) - {(first["sourceId"], first["sectionId"])}
    # Undo clears the correction (choice none) and the hit comes back.
    for lo_id in los:
        call(ctx, "curriculum.coverage_correct", {
            "extraction_id": first["extractionId"], "section_id": first["sectionId"],
            "learning_object_id": lo_id, "choice": "none"})
    assert _hits(call(ctx, "reader.correspondents", FIND)) == _hits(view)
