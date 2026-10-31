"""Reader CA6: side by side (ux_reader_compare_ask_v1 §6.4, §6.5, X9, K14, C5).

The second pane reads one section of the other book at a time through
``reader.side_by_side_section``: the whole section from its jump locator,
under protection read now (exam and held-out material refused, never shown),
with its neighbouring readable sections, and one ``source_exposure`` row per
block shown. The Reader records ``side_by_side_opened``, ``follow_along_moved``
and CA5a's deferred ``corresponding_section_peeked`` / ``_opened`` as
salience-only ``reader_action_invoked`` events. Kill switch
``reader.side_by_side.enabled``, respecting ``curriculum.enabled``.

Every model is a fake; nothing leaves the machine.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from learnloop.attempts import salience_firewall as SF
from learnloop.attempts.attempts import apply_attempt
from learnloop.config.schema import LearnLoopConfig
from learnloop.reader import reader_inquiry as RI
from learnloop_sidecar.errors import SidecarError
from tests.reading_path_fixtures import call, context
from tests.section_coverage_fixtures import HELD_OUT_SENTINEL, CoverageJudgeFake, build_coverage_vault, hold_out, table_counts

LAY_CHAR = {"extraction_id": "ext_lay", "section_id": "lay_char"}
LAY_EIGEN = {"extraction_id": "ext_lay", "section_id": "lay_eigen"}
CA6_EVENTS = ("corresponding_section_peeked", "corresponding_section_opened", "side_by_side_opened",
              "side_by_side_closed", "follow_along_moved", "follow_along_undone")


def _ctx(paths, **attrs):
    return context(paths.root, coverage_inline=True, **attrs)


def _exposed(repository, extraction_id="ext_lay"):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT span_id, context FROM source_exposure_events WHERE extraction_id = ? ORDER BY rowid",
            (extraction_id,))]


# -- the switch ---------------------------------------------------------------------------------------


def test_the_switch_is_on_by_default():
    assert LearnLoopConfig().reader.side_by_side.enabled is True


def test_the_prompt_contract_carries_side_by_side_only_while_its_switch_and_curriculum_are_on(tmp_path):
    paths, _repository = build_coverage_vault(tmp_path / "on")
    assert call(_ctx(paths), "reader.prompt_contract", {})["sideBySide"] == {"enabled": True}

    for name, config in (("off", "[reader.side_by_side]\nenabled = false"),
                         ("curriculum_off", "[curriculum]\nenabled = false")):
        paths, _repository = build_coverage_vault(tmp_path / name, config=config)
        assert "sideBySide" not in call(_ctx(paths), "reader.prompt_contract", {}), name

    # Independent of CA5a's presentation switch: Ctrl+\ opens side by side without the find list.
    paths, _repository = build_coverage_vault(tmp_path / "ca5a_off", config="[reader.correspondence]\nenabled = false")
    contract = call(_ctx(paths), "reader.prompt_contract", {})
    assert contract["sideBySide"] == {"enabled": True} and "correspondence" not in contract


@pytest.mark.parametrize("config,code", [
    ("[reader.side_by_side]\nenabled = false", "side_by_side_disabled"),
    ("[curriculum]\nenabled = false", "side_by_side_disabled"),
])
def test_switched_off_the_section_read_refuses_and_records_nothing(tmp_path, config, code):
    paths, repository = build_coverage_vault(tmp_path / "vault", config=config)
    ctx = _ctx(paths)
    call(ctx, "reader.prompt_contract", {})  # opening the vault settles its projections first
    before = table_counts(repository)
    with pytest.raises(SidecarError) as refused:
        call(ctx, "reader.side_by_side_section", LAY_CHAR)
    assert refused.value.code == code
    assert table_counts(repository) == before


# -- the second pane's section -------------------------------------------------------------------------


def test_the_section_is_whole_from_its_jump_with_its_readable_neighbours(tmp_path):
    paths, _repository = build_coverage_vault(tmp_path / "vault")
    section = call(_ctx(paths), "reader.side_by_side_section", LAY_EIGEN)["section"]
    assert section["title"] == "5.1 Eigenvectors and eigenvalues" and section["sourceTitle"] == "Lay"
    assert section["sourceId"] == "src_lay" and section["jumpSpanId"] == section["blocks"][0]["spanId"]
    assert [block["spanId"] for block in section["blocks"]] == ["s1", "s2", "s3"]
    assert section["previous"] is None
    assert section["next"] == {"sectionId": "lay_char", "title": "5.2 The characteristic equation"}

    # Lay 5.2 is followed by the held-out 5.9: the pane never runs on into it,
    # and the next section offered skips it.
    char = call(_ctx(paths), "reader.side_by_side_section", LAY_CHAR)["section"]
    assert [block["spanId"] for block in char["blocks"]] == ["s5", "s6"]
    assert all(HELD_OUT_SENTINEL not in block["text"] for block in char["blocks"])
    assert char["previous"] == {"sectionId": "lay_eigen", "title": "5.1 Eigenvectors and eigenvalues"}
    assert char["next"] == {"sectionId": "lay_ortho", "title": "6.1 Inner product and orthogonality"}


def test_every_block_shown_is_recorded_as_exposure_and_nothing_else_is_written(tmp_path):
    paths, repository = build_coverage_vault(tmp_path / "vault")
    judge = CoverageJudgeFake()
    ctx = _ctx(paths, coverage_judge_client=judge)
    call(ctx, "reader.prompt_contract", {})  # opening the vault settles its projections first
    before = table_counts(repository)
    section = call(ctx, "reader.side_by_side_section", LAY_CHAR)["section"]
    assert _exposed(repository) == [("s5", "library"), ("s6", "library")]
    assert len(section["exposureEventIds"]) == 2
    after = table_counts(repository)
    changed = {name: after[name] - before[name] for name in after if after[name] != before.get(name)}
    assert changed == {"source_exposure_events": 2}
    assert judge.calls == 0


def test_protected_sections_are_never_shown(tmp_path):
    paths, repository = build_coverage_vault(tmp_path / "vault")
    ctx = _ctx(paths)
    assert call(ctx, "reader.side_by_side_section", LAY_CHAR)["section"]["blocks"]
    # A held-out unit, an exam reading: refused, nothing recorded.
    for target in ({"extraction_id": "ext_lay", "section_id": "lay_held"},
                   {"extraction_id": "ext_exam", "section_id": "exam_q"}):
        before = table_counts(repository)
        with pytest.raises(SidecarError) as refused:
            call(ctx, "reader.side_by_side_section", target)
        assert refused.value.code == "withheld", target
        assert table_counts(repository) == before
    # Protection marked after the pane opened: the next read refuses.
    hold_out(repository, "lay_char")
    before = _exposed(repository)
    with pytest.raises(SidecarError) as refused:
        call(ctx, "reader.side_by_side_section", LAY_CHAR)
    assert refused.value.code == "withheld"
    assert _exposed(repository) == before
    # And a neighbour that became protected is skipped by the one before it.
    eigen = call(ctx, "reader.side_by_side_section", LAY_EIGEN)["section"]
    assert eigen["next"] == {"sectionId": "lay_ortho", "title": "6.1 Inner product and orthogonality"}


def test_an_unknown_section_is_a_validation_error(tmp_path):
    paths, _repository = build_coverage_vault(tmp_path / "vault")
    with pytest.raises(SidecarError) as refused:
        call(_ctx(paths), "reader.side_by_side_section", {"extraction_id": "ext_lay", "section_id": "nope"})
    assert refused.value.code == "validation_error"


# -- the records: salience only ------------------------------------------------------------------------


def test_the_ca6_events_are_client_events_and_server_owned_ones_stay_refused():
    assert set(CA6_EVENTS) <= set(RI.CLIENT_ACTION_EVENTS)
    for owned in (RI.SERVER_ACTION_EVENTS, RI.RW1B_SERVER_EVENTS, RI.RW4A_SERVER_EVENTS,
                  RI.RW5A_SERVER_EVENTS, RI.RW5D_SERVER_EVENTS):
        assert not set(owned) & set(CA6_EVENTS)


@pytest.mark.parametrize("event", CA6_EVENTS)
def test_each_ca6_event_is_salience_only_keeps_ids_and_drops_words(tmp_path, event):
    paths, repository = build_coverage_vault(tmp_path / "vault")
    before = table_counts(repository)
    payload = {"visitId": "v1", "extractionId": "ext_book", "sourceId": "src_book", "sectionId": "ch_eigen",
               "targetSourceId": "src_lay", "targetExtractionId": "ext_lay", "targetSectionId": "lay_char",
               "targetSpanId": "s5", "by": "judged", "leader": "main", "via": "follow_along",
               "quote": "the learner's words never travel"}
    (event_id,) = RI.record_activity(repository, [{"kind": "reader_action_invoked", "event": event, "payload": payload}])
    (row,) = [e for e in repository.reader_interaction_events(kind="reader_action_invoked") if e["id"] == event_id]
    body = row["payload"]
    assert body["event"] == event and body["authority_class"] == SF.SALIENCE_ONLY
    assert {key: body[key] for key in ("section_id", "target_source_id", "target_extraction_id",
                                       "target_section_id", "target_span_id", "by", "leader", "via")} == {
        "section_id": "ch_eigen", "target_source_id": "src_lay", "target_extraction_id": "ext_lay",
        "target_section_id": "lay_char", "target_span_id": "s5", "by": "judged", "leader": "main",
        "via": "follow_along"}
    assert "quote" not in body
    with pytest.raises(SF.SalienceEvidenceRejected):
        SF.reject_salience(row)
    with pytest.raises(SF.SalienceEvidenceRejected):
        apply_attempt(None, None, SimpleNamespace(**row))  # type: ignore[arg-type]
    after = table_counts(repository)
    assert {name: after[name] - before[name] for name in after if after[name] != before.get(name)} == {
        "interaction_events": 1}


def test_the_reader_records_them_through_log_activity(tmp_path):
    paths, repository = build_coverage_vault(tmp_path / "vault")
    out = call(_ctx(paths), "reader.log_activity", {"events": [
        {"kind": "reader_action_invoked", "event": "side_by_side_opened",
         "payload": {"extractionId": "ext_book", "sectionId": "ch_eigen", "targetExtractionId": "ext_lay",
                     "targetSectionId": "lay_char", "by": "judged", "via": "find_list"}},
        {"kind": "reader_action_invoked", "event": "follow_along_moved",
         "payload": {"extractionId": "ext_book", "sectionId": "ch_eigen", "targetExtractionId": "ext_lay",
                     "targetSectionId": "lay_ortho", "leader": "main"}},
    ]})
    events = {row["payload"]["event"] for row in repository.reader_interaction_events(kind="reader_action_invoked")}
    assert {"side_by_side_opened", "follow_along_moved"} <= events
    assert out


def test_a_side_by_side_session_keeps_its_id_and_minutes_for_the_evaluation(tmp_path):
    """Codex review F8: §14 counts side-by-side minutes and follow-along moves
    the learner undid; the session id, seconds open and the undo's timing are
    kept (ids and timings only)."""

    paths, repository = build_coverage_vault(tmp_path / "vault")
    RI.record_activity(repository, [
        {"kind": "reader_action_invoked", "event": "side_by_side_opened",
         "payload": {"visitId": "v1", "sideBySideId": "sbs1", "detourId": "d1", "targetSectionId": "lay_char"}},
        {"kind": "reader_action_invoked", "event": "follow_along_undone",
         "payload": {"visitId": "v1", "sideBySideId": "sbs1", "leader": "side", "sectionId": "lay_eigen",
                     "targetSectionId": "lay_char", "secondsAfter": 4}},
        {"kind": "reader_action_invoked", "event": "side_by_side_closed",
         "payload": {"visitId": "v1", "sideBySideId": "sbs1", "secondsOpen": 1200, "via": "close",
                     "quote": "never kept"}},
    ])
    rows = {row["payload"]["event"]: row["payload"]
            for row in repository.reader_interaction_events(kind="reader_action_invoked")}
    assert rows["side_by_side_opened"]["side_by_side_id"] == "sbs1"
    assert rows["side_by_side_opened"]["visit_id"] == "v1"
    assert rows["follow_along_undone"]["seconds_after"] == 4
    assert rows["follow_along_undone"]["target_section_id"] == "lay_char"
    closed = rows["side_by_side_closed"]
    assert (closed["side_by_side_id"], closed["seconds_open"], closed["via"]) == ("sbs1", 1200, "close")
    assert "quote" not in closed


def test_a_highlight_made_in_the_second_pane_goes_to_its_own_book(tmp_path):
    """Codex review F1: "notes and highlights go to their own book". The
    section read names the reading's revision, so the second pane's highlight
    or note is the ordinary reader.capture on that book."""

    paths, repository = build_coverage_vault(tmp_path / "vault")
    ctx = _ctx(paths)
    section = call(ctx, "reader.side_by_side_section", LAY_CHAR)["section"]
    run = repository.get_extraction_run("ext_lay")
    assert section["revisionId"] == run["revision_id"]
    receipt = call(ctx, "reader.capture", {
        "source_id": section["sourceId"], "revision_id": section["revisionId"], "extraction_id": section["extractionId"],
        "action": "annotate", "client_idempotency_key": "sbs-note-1", "learner_text": "compare with 6.2",
        "raw_selection": {"nodes": [{"spanId": "s5", "quote": section["blocks"][0]["text"][:20]}]},
    })
    assert receipt["annotationId"]
    listed = call(ctx, "reader.source_annotations", {"source_id": "src_lay", "extraction_id": "ext_lay"})["annotations"]
    assert [row["annotation"]["id"] for row in listed] == [receipt["annotationId"]]
    assert {segment["spanId"] for segment in listed[0]["segments"]} == {"s5"}
