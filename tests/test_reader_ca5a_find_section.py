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


# -- Codex review F1, F2: the peek ---------------------------------------------------------------------

LAY_CHAR = {"extraction_id": "ext_lay", "section_id": "lay_char"}


def _exposed(repository, extraction_id="ext_lay"):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT span_id, context FROM source_exposure_events WHERE extraction_id = ? ORDER BY rowid",
            (extraction_id,))]


def test_f1_the_generic_span_read_runs_on_into_the_held_out_unit(tmp_path):
    """The reproduction: Lay §5.2 is short and §5.9 (held out) follows it, so the
    span read the peek used to make returns the held-out sentinel among its neighbours."""

    from tests.section_coverage_fixtures import HELD_OUT_SENTINEL

    paths, _repository = build_coverage_vault(tmp_path / "vault")
    out = call(_ctx(paths), "get_span_view", {"extraction_id": "ext_lay", "span_id": "s5", "context": "library"})
    assert HELD_OUT_SENTINEL in [span["text"] for span in out["spanView"]["nextSpans"]]


def test_f1_a_peek_shows_only_the_hits_own_section(tmp_path):
    from tests.section_coverage_fixtures import HELD_OUT_SENTINEL

    paths, _repository = build_coverage_vault(tmp_path / "vault")
    peek = call(_ctx(paths), "reader.correspondent_peek", LAY_CHAR)["peek"]
    assert [block["spanId"] for block in peek["blocks"]] == ["s5", "s6"]
    assert peek["jumpSpanId"] == "s5" and peek["title"] == "5.2 The characteristic equation"
    assert all(HELD_OUT_SENTINEL not in block["text"] for block in peek["blocks"])
    assert peek["sourceTitle"] == "Lay"


def test_f1_a_peek_is_bounded_to_the_first_blocks(tmp_path):
    paths, _repository = build_coverage_vault(tmp_path / "vault")
    peek = call(_ctx(paths), "reader.correspondent_peek", {"extraction_id": "ext_lay", "section_id": "lay_eigen"})["peek"]
    assert [block["spanId"] for block in peek["blocks"]] == ["s1", "s2", "s3"][: SC.PEEK_BLOCKS]


def test_f1_protection_marked_after_the_search_refuses_the_peek(tmp_path):
    from learnloop_sidecar.errors import SidecarError
    from tests.section_coverage_fixtures import hold_out

    import pytest

    paths, repository = build_coverage_vault(tmp_path / "vault")
    ctx = _ctx(paths)
    call(ctx, "reader.correspondents", FIND)
    assert call(ctx, "reader.correspondent_peek", LAY_CHAR)["peek"]["blocks"]
    hold_out(repository, "lay_char")
    before = _exposed(repository)
    with pytest.raises(SidecarError) as refused:
        call(ctx, "reader.correspondent_peek", LAY_CHAR)
    assert refused.value.code == "withheld"
    # Nothing was shown, so nothing is recorded.
    assert _exposed(repository) == before
    # A held-out unit, an exam reading: never peeked.
    for target in ({"extraction_id": "ext_lay", "section_id": "lay_held"},
                   {"extraction_id": "ext_exam", "section_id": "exam_q"}):
        with pytest.raises(SidecarError) as refused:
            call(ctx, "reader.correspondent_peek", target)
        assert refused.value.code == "withheld", target


def test_f1_the_peek_is_off_with_the_presentations_switch(tmp_path):
    from learnloop_sidecar.errors import SidecarError

    import pytest

    paths, repository = build_coverage_vault(tmp_path / "vault", config="[reader.correspondence]\nenabled = false")
    with pytest.raises(SidecarError) as refused:
        call(_ctx(paths), "reader.correspondent_peek", LAY_CHAR)
    assert refused.value.code == "correspondence_disabled"
    assert _exposed(repository) == []


def test_f2_every_block_the_peek_shows_is_recorded_as_exposure(tmp_path):
    paths, repository = build_coverage_vault(tmp_path / "vault")
    peek = call(_ctx(paths), "reader.correspondent_peek", LAY_CHAR)["peek"]
    assert _exposed(repository) == [("s5", "library"), ("s6", "library")]
    assert len(peek["exposureEventIds"]) == 2


def test_f2_a_peeked_paragraph_that_is_a_cold_items_source_makes_the_receipt_see_it(tmp_path):
    """The jump is the heading s5; the peek also shows the paragraph s6. A cold
    item authored from s6 must see that exposure (the scan matches exact spans)."""

    from learnloop.attempts.coldness_receipt import _scan_exposures
    from learnloop.vault.loader import load_vault
    from learnloop.vault.models import Provenance, SourceRef

    paths, repository = build_coverage_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    item_id = sorted(vault.practice_items)[0]
    vault.practice_items[item_id] = vault.practice_items[item_id].model_copy(update={"provenance": Provenance(
        origin="canonical_extract",
        source_refs=[SourceRef(ref_type="canonical_source", ref_id="src_lay", extraction_id="ext_lay", span_ids=["s6"])],
    )})

    def scan():
        out = _scan_exposures(vault, repository, interval_start="2000-01-01T00:00:00Z",
                              interval_end="2999-01-01T00:00:00Z", source_attempt=None, cold_item_id=item_id,
                              case_ref=None, exclude_attempt_ids=set())
        return [event["why"] for event in out["events"] if event["ledger"] == "source_exposure_events"]

    # The old peek's record (the requested span only) misses the paragraph shown.
    call(_ctx(paths), "get_span_view", {"extraction_id": "ext_lay", "span_id": "s5", "context": "library"})
    assert scan() == []
    call(_ctx(paths), "reader.correspondent_peek", LAY_CHAR)
    assert scan() == ["cold_item_source_span_viewed"]


# -- Codex review F3, F6: not about this as one operation ------------------------------------------------


def _dismiss(ctx, target, operation_id, *, origin=FIND, undo_of=None):
    return call(ctx, "reader.correspondent_dismiss", {
        "extraction_id": origin["extraction_id"], "section_id": origin["section_id"],
        "target_extraction_id": target["extractionId"], "target_section_id": target["sectionId"],
        "operation_id": operation_id, "undo_of": undo_of})["operation"]


def _learner_rows(repository, target):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT learning_object_id, learner_override FROM section_coverage WHERE extraction_id = ? "
            "AND section_id = ? AND origin = 'learner' ORDER BY created_at, rowid",
            (target["extractionId"], target["sectionId"]))]


def test_f3_not_about_this_is_one_operation_and_a_repeat_writes_nothing(tmp_path):
    paths, repository = build_coverage_vault(tmp_path / "vault", big=True)
    ctx = _ctx(paths)
    view = call(ctx, "reader.correspondents", FIND)
    first = view["search"]["sources"][0]["sections"][0]
    before = table_counts(repository)
    record = _dismiss(ctx, first, "op_first_0001")
    assert record["choice"] == "not_about" and record["learningObjectIds"] == ["lo_eigen"]
    assert record["replayed"] is False
    after = table_counts(repository)
    changed = {name: after[name] - before[name] for name in after if after[name] != before.get(name)}
    # C0a's row and verdict per LO, plus the operation's own pair verdict.
    assert changed == {"section_coverage": 1, "judgment_ledger": 2}
    assert (first["sourceId"], first["sectionId"]) not in _hits(call(ctx, "reader.correspondents", FIND))
    # A lost reply: the same request again answers from the record and writes nothing.
    again = _dismiss(ctx, first, "op_first_0001")
    assert again["replayed"] is True and again["operationId"] == "op_first_0001"
    assert table_counts(repository) == after
    # Undo is its own operation over the one it names, idempotent too.
    undo = _dismiss(ctx, first, "op_undo_00001", undo_of="op_first_0001")
    assert undo["choice"] == "none" and undo["undoOf"] == "op_first_0001"
    assert _learner_rows(repository, first) == [("lo_eigen", "not_about"), ("lo_eigen", "none")]
    settled = table_counts(repository)
    assert _dismiss(ctx, first, "op_undo_00001", undo_of="op_first_0001")["replayed"] is True
    assert table_counts(repository) == settled
    assert _hits(call(ctx, "reader.correspondents", FIND)) == _hits(view)


def test_f3_a_failure_inside_the_operation_leaves_nothing(tmp_path, monkeypatch):
    """Interrupted after the first LO's rows: the transaction rolls back whole."""

    import pytest

    paths, repository = build_coverage_vault(tmp_path / "vault", big=True)
    ctx = _ctx(paths)
    first = call(ctx, "reader.correspondents", FIND)["search"]["sources"][0]["sections"][0]
    monkeypatch.setattr(SC, "section_learning_objects", lambda *args, **kwargs: ["lo_eigen", "lo_eigen"])
    real = SC._write_correction
    calls = []

    def flaky(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            raise RuntimeError("the app went away")
        return real(*args, **kwargs)

    monkeypatch.setattr(SC, "_write_correction", flaky)
    before = table_counts(repository)
    with pytest.raises(RuntimeError):
        _dismiss(ctx, first, "op_crash_0001")
    assert table_counts(repository) == before and len(calls) == 2
    monkeypatch.undo()
    # The hit is still listed, and the same operation can be sent again.
    assert (first["sourceId"], first["sectionId"]) in _hits(call(ctx, "reader.correspondents", FIND))
    assert _dismiss(ctx, first, "op_crash_0001")["replayed"] is False


def test_f3_an_operation_id_is_never_reused_for_another_correction(tmp_path):
    from learnloop_sidecar.errors import SidecarError

    import pytest

    paths, repository = build_coverage_vault(tmp_path / "vault", big=True)
    ctx = _ctx(paths)
    sections = [section for source in call(ctx, "reader.correspondents", FIND)["search"]["sources"]
                for section in source["sections"]]
    _dismiss(ctx, sections[0], "op_shared_001")
    before = table_counts(repository)
    with pytest.raises(SidecarError) as refused:
        _dismiss(ctx, sections[1], "op_shared_001")
    assert refused.value.code == "validation_error" and table_counts(repository) == before
    with pytest.raises(SidecarError) as refused:
        _dismiss(ctx, sections[1], "op_undo_none1", undo_of="op_never_made")
    assert refused.value.code == "not_found"


def test_f6_an_unmapped_section_can_say_not_about_this_and_undo_it(tmp_path):
    """A section with no LO (no provenance, no coverage rows) still gets its
    hits, and *not about this* records the pair verdict only: no LO is inferred."""

    paths, repository = build_coverage_vault(tmp_path / "vault", big=True)
    ctx = _ctx(paths)
    origin = {"extraction_id": "ext_lay", "section_id": "lay_ortho"}
    view = call(ctx, "reader.correspondents", origin)
    assert view["search"]["correctableLearningObjectIds"] == []
    hits = [section for source in view["search"]["sources"] for section in source["sections"]]
    assert hits, "the unmapped section needs a search hit for this test"
    target = hits[0]
    before = table_counts(repository)
    record = _dismiss(ctx, target, "op_unmapped01", origin=origin)
    assert record["learningObjectIds"] == []
    after = table_counts(repository)
    assert {name: after[name] - before[name] for name in after if after[name] != before.get(name)} == {
        "judgment_ledger": 1}
    with repository.connection() as connection:
        verdict = connection.execute(
            "SELECT task, left_id, right_id, judge, verdict FROM judgment_ledger WHERE id = 'scd_op_unmapped01'").fetchone()
    assert tuple(verdict) == (SC.PAIR_TASK, "ext_lay/lay_ortho", f"{target['extractionId']}/{target['sectionId']}",
                              "learner_card", "not_about")
    # Reload: the hit stays gone. Undo: it is back.
    reloaded = call(ctx, "reader.correspondents", origin)
    assert (target["sourceId"], target["sectionId"]) not in _hits(reloaded)
    _dismiss(ctx, target, "op_unmapped02", origin=origin, undo_of="op_unmapped01")
    assert _hits(call(ctx, "reader.correspondents", origin)) == _hits(view)


def test_f6_dismissing_is_off_with_the_presentations_switch_and_refuses_protected_sections(tmp_path):
    from learnloop_sidecar.errors import SidecarError

    import pytest

    paths, repository = build_coverage_vault(tmp_path / "vault", config="[reader.correspondence]\nenabled = false")
    held = {"extractionId": "ext_lay", "sectionId": "lay_char"}
    with pytest.raises(SidecarError) as refused:
        _dismiss(_ctx(paths), held, "op_off_000001")
    assert refused.value.code == "correspondence_disabled"
    paths, repository = build_coverage_vault(tmp_path / "on")
    ctx = _ctx(paths)
    before = table_counts(repository)
    with pytest.raises(SidecarError) as refused:
        _dismiss(ctx, {"extractionId": "ext_lay", "sectionId": "lay_held"}, "op_held_00001")
    assert refused.value.code == "withheld" and table_counts(repository) == before


# -- Landing onto mvp-0.38: the peek and the cold-retry reschedule -----------------------------------------


def test_a_peeked_paragraph_that_is_the_replacement_surfaces_source_is_skipped_by_the_reschedule(
        tmp_path, monkeypatch):
    """The cold-retry reschedule (mvp-0.38, its Codex review F1) skips a candidate
    surface already hard-contaminated since the primed attempt, through the
    final receipt's own exposure scan. A correspondent peek shows a paragraph,
    records it (Codex review F2), and that row must reach the scan: the repair's
    one spare surface was authored from the peeked paragraph, so help on the due
    cold retry withdraws it and schedules nothing on that surface."""

    import json
    from datetime import timedelta

    from learnloop import clock as clock_module
    from learnloop.vault.loader import load_vault
    from learnloop.vault.models import Provenance, SourceRef
    from learnloop.vault.writer import upsert_source_set
    from tests.helpers import NOW
    from tests.section_coverage_fixtures import LAY
    from tests.source_retrieval_fakes import seed_source
    from tests.test_cold_retry_reschedule import ASSISTED_AT, _answer, _repair, _spare, _table, _tasks
    from tests.ux_phase1_support import set_config

    vault, repository, episode, _primed, cold_item = _repair(tmp_path)
    spare = _spare(repository, episode)
    [old] = _tasks(repository, episode["id"])
    seed_source(repository, source_id="src_lay", revision_id="rev_lay", extraction_id="ext_lay", title="Lay",
                units=LAY, furniture=False)
    upsert_source_set(vault.root, {"id": "sset_lay", "subject_id": "linear-algebra", "title": "Lay",
                                   "members": [{"source_id": "src_lay", "revision_id": "rev_lay",
                                                "default_role": "primary_textbook"}]})
    set_config(vault.root, {("curriculum", "enabled"): True, ("tutor_qa", "reader_enabled"): True})
    vault = load_vault(vault.root)
    # The spare surface was authored from lay_char's paragraph s6 (the peek's jump is its heading s5).
    vault.practice_items[spare] = vault.practice_items[spare].model_copy(update={"provenance": Provenance(
        origin="canonical_extract",
        source_refs=[SourceRef(ref_type="canonical_source", ref_id="src_lay", extraction_id="ext_lay",
                               span_ids=["s6"])],
    )})

    # The peek, between the primed attempt and the assisted cold retry.
    with monkeypatch.context() as patch:
        patch.setattr(clock_module.SystemClock, "now", lambda _self: NOW + timedelta(hours=12))
        peek = call(context(vault.root, coverage_inline=True), "reader.correspondent_peek", LAY_CHAR)["peek"]
    assert [block["spanId"] for block in peek["blocks"]] == ["s5", "s6"]
    shown_s6 = peek["exposureEventIds"][1]

    _answer(vault, repository, cold_item, ASSISTED_AT, hints=1)
    [withdrawn] = _tasks(repository, episode["id"])
    assert withdrawn["id"] == old["id"] and withdrawn["status"] == "expired"
    [decision] = _table(repository, "SELECT d.* FROM cold_measurement_opportunity_decisions d JOIN "
                                    "cold_measurement_opportunities o ON o.id = d.measurement_opportunity_id "
                                    f"WHERE o.trigger_kind = 'assisted_cold_retry' AND o.trigger_ref = '{old['id']}'")
    assert (decision["decision"], decision["reason"]) == ("structurally_refused", "no_uncontaminated_surface")
    summary = json.loads(decision["candidate_summary_json"])
    assert summary["cold_item_id"] is None
    assert summary["contaminated"] == {spare: {"reason": "cold_item_answer_revealed_post_primed",
                                               "event_ids": [shown_s6]}}
    assert repository.remediation_episode(episode["id"])["cold_item_id"] == cold_item
