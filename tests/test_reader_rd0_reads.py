"""The workbench's reads (spec §7.6, §8.5, §12.6.1): the per-span union, the companion's history by day and desk,
and the due checks with their hosts."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from learnloop.clock import FrozenClock
from learnloop.companion.history import companion_history, record_exchange_context
from learnloop.curriculum import commitments as C
from learnloop.db.repositories import Repository
from learnloop.intent.inline_checks import due_checks
from learnloop.passage_union.union import UnionError, union_range
from learnloop.substrate.passage_spans import project_gap, project_question_event
from learnloop.vault.loader import load_vault
from tests.desk_helpers import (
    BOOK,
    Batches,
    record_alias,
    seed_annotation,
    seed_gap,
    seed_reader_exchange,
    seed_reading,
    seed_union_kinds,
)
from tests.helpers import create_basic_vault

LO = "lo_svd_definition"
SPANS = ["s1", "s2", "s3", "s4"]
SECTION = f"{BOOK}_u1"


@pytest.fixture
def seeded(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    vault = load_vault(paths.root)
    # An older reading of the same book, and the current one, with an exact alias s3 -> s3.
    seed_reading(repository, source_id="src_book", revision_id="rev_book", extraction_id="ext_old", spans=["s3"])
    seed_reading(repository, source_id="src_book", revision_id="rev_book", extraction_id=BOOK, spans=SPANS)
    record_alias(repository, from_extraction_id="ext_old", from_span_id="s3", to_extraction_id=BOOK, to_span_id="s3")
    seed_annotation(repository, annotation_id="ann_1", source_id="src_book", revision_id="rev_book",
                    extraction_id=BOOK, span_id="s3")
    with repository.connection() as connection:
        # An exchange asked on the older reading, and its question read as a misconception.
        seed_reader_exchange(connection, question_event_id="qe_old", extraction_id="ext_old", anchor="s3")
        seed_gap(connection, gap_id="g_old", source_kind="tutor_question", source_id="qe_old", kind="misconception")
        seed_union_kinds(connection, extraction_id=BOOK, span_id="s3", section_id=SECTION, learning_object_id=LO)
        project_question_event(connection, vault, "qe_old")
        project_gap(connection, vault, "g_old")
    batches = Batches(repository)
    batches.pad("p1", {"op": "create_pad", "kind": "named"},
                {"op": "insert_block", "block_id": "b1", "kind": "text", "provenance": "learner", "position_key": "a0",
                 "body_md": "why s3?"},
                {"op": "link_anchor", "block_id": "b1", "extraction_id": BOOK, "span_id": "s3", "event_id": "e1"})
    return vault, repository


def test_the_union_returns_every_kind_for_a_passage_across_readings(seeded):
    vault, repository = seeded
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO entity_source_links (id, entity_type, entity_id, locator, relation, created_at) "
            "VALUES ('esl_1', 'learning_object', ?, ?, 'primary', '2026-05-19T09:00:00Z')", (LO, f"span:{BOOK}/s3"))
        connection.commit()
    C.create_commitment(repository, action="test_me_later", intent_text="check me on this",
                        targets=[{"target_kind": "learning_object", "target_ref": LO, "role": "required"}],
                        depth_preset="keep_in_touch", due_hint="2026-05-20T09:00:00Z",
                        clock=FrozenClock(datetime(2026, 5, 19, 9, tzinfo=UTC)))
    clock = FrozenClock(datetime(2026, 5, 22, 9, tzinfo=UTC))
    notes = {"s3": [{"note_title": "my take"}], "s9": [{"note_title": "not in range"}]}
    union = union_range(vault, repository, extraction_id=BOOK, from_span_id="s4", to_span_id="s1",
                        notes_by_span=notes, clock=clock)
    assert [entry["span_id"] for entry in union["spans"]] == ["s1", "s2", "s3", "s4"]
    s1, s2, s3, _s4 = union["spans"]
    assert s3["section_id"] == SECTION
    assert [(a["annotation_id"], a["type"], a["placement"]) for a in s3["annotations"]] == [("ann_1", "highlight", "here")]
    assert [(b["block_id"], b["pad_id"], b["kind"]) for b in s3["pad_blocks"]] == [("b1", "p1", "text")]
    # The exchange was asked on the older reading: it lands here through the exact alias.
    assert [(e["question_event_id"], e["quality"], e["alias"]) for e in s3["exchanges"]] == [
        ("qe_old", "exact_selection", "exact")]
    assert s3["adjustments"] == [{"question_event_id": "qe_old", "gap_id": "g_old"}]
    assert [(g["gap_id"], g["quality"]) for g in s3["gaps"]] == [("g_old", "exact_selection")]
    assert [(link["link_id"], link["relation"]) for link in s3["passage_links"]] == [("pl_1", "clarifies_distinction")]
    assert [f["figure_id"] for f in s3["figures"]] == ["fig_1"]
    assert [q["question_id"] for q in s3["authored_questions"]] == ["raq_union"]
    assert s3["notes"] == [{"note_title": "my take"}]
    assert s3["exposure"] == {"times_shown": 2, "last_shown_at": "2026-05-19T02:00:00Z", "withheld": False}
    # A due check of the passage's learning object is hosted where its section starts, and the union names
    # nothing of it but its commitment.
    assert s3["checks_due"] == []
    assert len(s1["checks_due"]) == 1 and set(s1["checks_due"][0]) == {"commitment_id"}
    assert union["sections"] == [{"section_id": SECTION, "title": f"Section {SECTION}", "learning_objects": [
        {"learning_object_id": LO, "treatment": "introduces", "learner_override": None}]}]
    assert not any(s2[key] for key in ("annotations", "pad_blocks", "exchanges", "gaps", "figures", "checks_due"))


def test_a_same_place_alias_is_flagged_never_shown_as_the_cited_text(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    vault = load_vault(paths.root)
    seed_reading(repository, source_id="src_book", revision_id="rev_book", extraction_id="ext_old", spans=["s3"])
    seed_reading(repository, source_id="src_book", revision_id="rev_book", extraction_id=BOOK, spans=SPANS)
    record_alias(repository, from_extraction_id="ext_old", from_span_id="s3", to_extraction_id=BOOK, to_span_id="s2",
                 match_kind="geometry_section")
    with repository.connection() as connection:
        seed_reader_exchange(connection, question_event_id="qe_old", extraction_id="ext_old", anchor="s3")
        project_question_event(connection, vault, "qe_old")
    union = union_range(vault, repository, extraction_id=BOOK, from_span_id="s1", to_span_id="s4")
    by_span = {entry["span_id"]: entry for entry in union["spans"]}
    assert [(e["question_event_id"], e["alias"]) for e in by_span["s2"]["exchanges"]] == [("qe_old", "needs_reanchor")]


def test_a_time_range_reads_a_transcripts_cues_and_a_bad_range_is_refused(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    vault = load_vault(paths.root)
    seed_reading(repository, source_id="src_video", revision_id="rev_video", extraction_id="ext_video",
                 spans=["c1", "c2", "c3", "c4"], timed=True)
    union = union_range(vault, repository, extraction_id="ext_video", t0=12.0, t1=25.0)
    assert [entry["span_id"] for entry in union["spans"]] == ["c2", "c3"]
    with pytest.raises(UnionError) as missing:
        union_range(vault, repository, extraction_id="ext_video", from_span_id="c1", to_span_id="nope")
    assert missing.value.code == "span_not_found"
    with pytest.raises(UnionError) as unknown:
        union_range(vault, repository, extraction_id="ext_none", from_span_id="c1", to_span_id="c2")
    assert unknown.value.code == "extraction_not_found"


# -- the companion's history ---------------------------------------------------------------------------


def test_history_groups_by_day_then_desk_newest_first_with_an_honest_origin(seeded):
    _vault, repository = seeded
    with repository.connection() as connection:
        seed_reader_exchange(connection, question_event_id="qe_desk", extraction_id=BOOK, anchor="s2",
                             created_at="2026-05-20T15:00:00Z", question_md="What is a kernel?",
                             answer_md="It is the null space. More follows.")
        connection.commit()
    record_exchange_context(repository, question_event_id="qe_desk", surface="desk", desk_id="d1",
                            pad_block_ids=["b1"], goal_id="goal_linear_algebra_ml")
    # A second record of the same exchange changes nothing.
    assert record_exchange_context(repository, question_event_id="qe_desk", surface="lesson", desk_id="d2") is False
    history = companion_history(repository)
    exchanges = [e for day in history["days"] for desk in day["desks"] for e in desk["exchanges"]]
    assert [e["question_event_id"] for e in exchanges] == ["qe_desk", "qe_old"]
    newest, oldest = exchanges
    assert newest["origin"] == "live" and newest["surface"] == "desk" and newest["where"] == "on a desk"
    assert newest["answer_first_sentence"] == "It is the null space."
    assert newest["pad_block_ids"] == ["b1"] and newest["goal_id"] == "goal_linear_algebra_ml"
    assert newest["anchor"] is None  # its passages were never projected in this test
    assert oldest["origin"] == "backfill" and oldest["surface"] == "reader" and oldest["where"] == "in the Reader"
    assert oldest["anchor"] == {"extraction_id": "ext_old", "span_id": "s3", "quality": "exact_selection"}
    assert history["days"][0]["desks"][0]["desk_id"] == "d1"
    assert companion_history(repository, desk_id="d1")["days"][0]["desks"][0]["exchanges"][0]["question_event_id"] == (
        "qe_desk")
    assert [e["question_event_id"] for day in companion_history(repository, query="null space")["days"]
            for desk in day["desks"] for e in desk["exchanges"]] == ["qe_desk"]
    assert companion_history(repository, date_from="2026-05-21")["days"] == []


def test_history_pages_by_cursor_and_reaches_every_exchange(tmp_path, monkeypatch):
    import learnloop.companion.history as H

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    with repository.connection() as connection:
        for n in range(5):
            seed_reader_exchange(connection, question_event_id=f"qe_{n}", extraction_id=BOOK, anchor="s1",
                                 created_at=f"2026-05-19T1{n}:00:00Z")
        connection.commit()
    monkeypatch.setattr(H, "PAGE_SIZE", 2)
    seen, cursor = [], None
    while True:
        page = companion_history(repository, cursor=cursor)
        seen += [e["question_event_id"] for day in page["days"] for desk in day["desks"] for e in desk["exchanges"]]
        cursor = page["cursor"]
        if cursor is None:
            break
    assert seen == ["qe_4", "qe_3", "qe_2", "qe_1", "qe_0"]


# -- due checks ----------------------------------------------------------------------------------------


def test_due_checks_name_their_host_and_nothing_of_the_item(seeded):
    vault, repository = seeded
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO deliverable_path_sections (id, goal_id, depth, learning_object_id, extraction_id, section_id, "
            "label, ordinal, reason, state_key, ledger_id, model, prompt_version, created_at) VALUES "
            "('dps_1', 'goal_linear_algebra_ml', 'learn_to_use_it', ?, ?, ?, 'core', 1, 'why', 'k', 'jl_link', 'm', "
            "'p', '2026-05-19T09:00:00Z')", (LO, BOOK, SECTION))
        connection.commit()
    commitment = C.create_commitment(
        repository, action="test_me_later", intent_text="check me", provenance={"origin": "reader", "item": "secret"},
        targets=[{"target_kind": "learning_object", "target_ref": LO, "role": "required"}],
        depth_preset="keep_in_touch", due_hint="2026-05-20T09:00:00Z",
        clock=FrozenClock(datetime(2026, 5, 19, 9, tzinfo=UTC)))
    before = FrozenClock(datetime(2026, 5, 19, 12, tzinfo=UTC))
    after = FrozenClock(datetime(2026, 5, 22, 9, tzinfo=UTC))
    assert due_checks(vault, repository, clock=before) == []  # not yet due
    checks = due_checks(vault, repository, goal_id="goal_linear_algebra_ml", clock=after)
    assert checks == [{"commitment_id": commitment.id, "lo_id": LO, "due": "2026-05-20T09:00:00Z",
                       "host": {"extraction_id": BOOK, "section_id": SECTION, "span_id": "s1"},
                       "provenance": {"origin": "reader"}}]
    assert due_checks(vault, repository, goal_id="goal_linear_algebra_ml", extraction_id=BOOK, span_id="s4",
                      clock=after) == checks
    assert due_checks(vault, repository, learning_object_ids=["lo_other"], clock=after) == []
    # Without a goal and without a primary passage, the check is listed with no host.
    assert due_checks(vault, repository, clock=after)[0]["host"] is None
