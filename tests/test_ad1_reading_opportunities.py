"""Adaptive difficulty AD1, G-AD1-11: reading opportunities frozen and ordered by source time.

Spec §5.11 (D20, D22), §11.2: each listed source writes one
``ad_reading_opportunities`` row per LO, inside its cap, with its kind,
subkind, doses, source id, source write time and the authority class
``salience_only``: a completed section and a span view (``reading``), an
answered reader tutor question, a worked example shown or in a completed
section, an answered quick check of each in-passage style, and an answered
owner-placed reading question. A span view of a worked-example block is a
``worked_example`` only. A ``reconstruct`` question, a skipped or dismissed
question and an unanswered prompt write nothing. A source row written after a
serve is never recorded by that serve's sweep. Deleting the extraction leaves
the receipts. A judged in-passage question also writes one verdict row from
its first self-check verdict; a later changed verdict writes nothing. No
dwell, scroll, highlight, skip, visibility, active-time or answer value is
read. With ``forecast_receipts`` off no row is written.

Fails before AD1: there is no ``ad_reading_opportunities`` table and no sweep.
The LO mapping is the Reader's own (``learning_objects_for_section`` /
``_span``); these tests hand the sweep a fixed map so each cap and kind is
exact, and one test drives the vault's own map end to end.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.reader import reader_dialogue as RD
from learnloop.reader import reader_quick_check as RQC
from learnloop.vault.loader import load_vault

from tests.ad_fakes import rows
from tests.helpers import append_config_toml, create_basic_vault
from tests.test_source_inventory import _persist, _register_revision

T0 = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
LO_A, LO_B = "lo_svd_definition", "lo_other"
ITEM = "pi_svd_define_001"


def at(minutes: float) -> FrozenClock:
    return FrozenClock(T0 + timedelta(minutes=minutes))


def iso(minutes: float) -> str:
    return (T0 + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


class FakeMap:
    """The Reader's mapping, fixed: sec1 holds s1, s2 and the worked example we1."""

    def __init__(self) -> None:
        self.sections = {("ext1", "u1"): [LO_A]}
        self.spans = {("ext1", "s1"): [LO_A], ("ext1", "s2"): [LO_A, LO_B], ("ext1", "we1"): [LO_A]}
        self.section_span_ids = {("ext1", "u1"): ["s1", "s2", "we1"]}
        self.examples = {"ext1": {"we1"}}
        self.facets = {LO_A: ["fa1", "fa2"], LO_B: ["fb1"]}
        self.items = {ITEM: LO_A}
        self.held: set[tuple[str, str | None]] = set()

    def los_for_section(self, extraction_id, section_id):
        return list(self.sections.get((extraction_id, section_id), []))

    def los_for_span(self, extraction_id, span_id):
        return list(self.spans.get((extraction_id, span_id), []))

    def section_spans(self, extraction_id, section_id):
        return list(self.section_span_ids.get((extraction_id, section_id), []))

    def worked_example_spans(self, extraction_id):
        return set(self.examples.get(extraction_id, set()))

    def withheld(self, extraction_id, span_id):
        return (extraction_id, span_id) in self.held

    def los_for_note(self, note_id):
        return []

    def lo_for_item(self, practice_item_id):
        return self.items.get(practice_item_id)

    def facets_for_lo(self, learning_object_id):
        return list(self.facets.get(learning_object_id, []))


def _ir() -> DocumentIR:
    blocks = [
        DocumentBlock.build(span_id=span, block_type="Text", text=f"Block {span}.", ordinal=index, page=1,
                            section_path=["Ch1"])
        for index, span in enumerate(("s1", "s2", "we1"))
    ]
    unit = DocumentUnit(unit_id="u1", label="Ch1", ordinal=0, semantic_hash="sha256:u1", page_start=1,
                        page_end=1, span_ids=["s1", "s2", "we1"])
    return DocumentIR(extractor="marker", extractor_version="1", units=[unit], blocks=blocks, assets=[],
                      health=ExtractionHealth())


def _setup(tmp_path, *, config: str = ""):
    paths = create_basic_vault(tmp_path / "vault")
    if config:
        append_config_toml(paths.root, config)
    vault = load_vault(paths.root)
    repo = Repository(paths.sqlite_path)
    _register_revision(repo, source_id="src1", revision_id="rev1")
    _persist(repo, _ir(), revision_id="rev1", extraction_id="ext1")
    return paths, vault, repo


def _view(repo, span, minutes, *, context="reader"):
    return repo.insert_source_exposure_event(
        {"context": context, "extraction_id": "ext1", "span_id": span, "revision_id": "rev1", "source_id": "src1",
         "entity_type": "reader", "entity_id": "visit1"}, clock=at(minutes))


def _tutor(repo, minutes, *, facets=None, answered=True):
    return repo.insert_question_event(
        {"context": "reader", "note_id": "span:ext1/s1", "question_md": "why?", "answer_md": "because",
         "answer_status": "answered" if answered else "pending", "facets": list(facets or [])},
        clock=at(minutes))


def _question(repo, style, minutes, *, answer=True, dismiss=False):
    question_id = repo.insert_reader_authored_question(fields={
        "extraction_id": "ext1", "section_id": "u1", "source_id": "src1", "question_md": f"A {style} question?",
        "expected_answer_md": "The answer.", "span_ids": ["s1"], "prompt_version": "qc-v1",
        "scope_kind": "inquiry", "question_style": style, "anchor_span_ids": ["s1"],
        "inquiry_root_event_id": f"root-{style}-{minutes}",
    }, clock=at(minutes))
    if answer:
        RQC.record_inquiry_action(repo, question_id=question_id, action="answered", response_md="my words",
                                  clock=at(minutes))
    if dismiss:
        RQC.record_inquiry_action(repo, question_id=question_id, action="dismissed", clock=at(minutes))
    return question_id


def _sweep(vault, repo, minutes, *, mapping=None, kind="serve"):
    from learnloop.adaptive_difficulty.reading import sweep

    return sweep(vault, repo, as_of=iso(minutes), sweep_kind=kind, reading_map=mapping or FakeMap(),
                 clock=at(minutes))


def _opportunities(paths):
    return rows(paths.sqlite_path, "SELECT * FROM ad_reading_opportunities ORDER BY source_written_at, id")


def _by(opportunities, kind, subkind=None):
    return [row for row in opportunities if row["kind"] == kind and (subkind is None or row["subkind"] == subkind)]


def test_reading_opportunities_frozen_and_ordered_by_source_time(tmp_path):
    import json

    paths, vault, repo = _setup(tmp_path)
    # A completed section (with a worked example in it), and span views.
    repo.upsert_reader_section_progress(extraction_id="ext1", section_id="u1", spans_seen=3, span_count=3,
                                        completed=True, clock=at(1))
    _view(repo, "s1", 2)
    _view(repo, "s2", 3)            # LO_A's passage view of the day is taken; LO_B's is not
    _view(repo, "we1", 4)           # a worked example only, already studied in the completed section
    _view(repo, "s1", 4.5, context="registry_review")   # the owner's tooling is not reading
    # Reader tutor exchanges: three per LO per day; a pending one is no exchange.
    for minute in (5, 6, 7, 8):
        _tutor(repo, minute, facets=["fa2"] if minute == 5 else None)
    _tutor(repo, 8.5, answered=False)
    # In-passage questions: one of each style, and the ones that write nothing.
    styles = {style: _question(repo, style, 9 + index)
              for index, style in enumerate(("recall", "next_step", "why_step", "assumptions"))}
    _question(repo, "reconstruct", 14)
    _question(repo, "recall", 15, answer=False)
    _question(repo, "recall", 16, answer=True, dismiss=True)
    # An owner-placed reading question answered, and one skipped.
    item = vault.practice_items[ITEM]
    answered = RD.administer_reading_question(vault, repo, item, reading_phase="after_section", clock=at(17))
    RD.submit_reading_question(repo, administration_id=answered["administration_id"], response_md="ANSWER-TEXT",
                               outcome_class="correct", clock=at(17))
    skipped = RD.administer_reading_question(vault, repo, item, reading_phase="after_section", clock=at(18))
    RD.skip_reading_question(repo, administration_id=skipped["administration_id"], clock=at(18))
    # Salience magnitudes that must never be read.
    from learnloop.substrate.activities import log_interaction_event

    for kind in ("reader_dwell", "reader_scroll", "reader_highlight", "reader_span_visible"):
        log_interaction_event(repo, kind=kind, origin="learner", subject_type="visit", subject_id="visit1",
                              payload={"dwell_ms": 99999, "active_seconds": 777}, clock=at(18.5))
    # D22: a judged quick check: its first verdict, then a changed one.
    RQC.record_inquiry_action(repo, question_id=styles["recall"], action="self_checked", self_check="partly",
                              clock=at(19))

    result = _sweep(vault, repo, 20)
    opportunities = _opportunities(paths)
    assert result.written == len(opportunities)

    section = _by(opportunities, "reading", "section_read")
    assert [(row["learning_object_id"], row["source_id"]) for row in section] == [(LO_A, "ext1/u1")]
    assert json.loads(section[0]["facet_doses_json"]) == {"fa1": 0.5, "fa2": 0.5}
    passages = _by(opportunities, "reading", "passage_viewed")
    assert [row["learning_object_id"] for row in passages] == [LO_A, LO_B]
    examples = _by(opportunities, "worked_example")
    assert [(row["subkind"], row["learning_object_id"]) for row in examples] == [("in_completed_section", LO_A)]
    tutor = _by(opportunities, "reader_tutor_exchange", "reader")
    assert len(tutor) == 3, "three exchanges per LO per day"
    assert json.loads(tutor[0]["facet_doses_json"]) == {"fa2": 1.0}, "a named facet takes dose 1"
    in_passage = _by(opportunities, "in_passage_question")
    assert sorted(row["subkind"] for row in in_passage) == sorted(
        ["recall", "next_step", "why_step", "assumptions", "owner_placed", "self_check:missed"])
    owner = _by(opportunities, "in_passage_question", "owner_placed")[0]
    assert owner["source_table"] == "interaction_events" and owner["learning_object_id"] == LO_A
    verdict = _by(opportunities, "in_passage_question", "self_check:missed")[0]
    assert verdict["source_table"] == "judgment_ledger"
    assert all(row["authority_class"] == "salience_only" for row in opportunities)
    assert all(row["mapping_version"] == "ad_reading_map_v1" for row in opportunities)
    assert [row["source_written_at"] for row in opportunities] == sorted(row["source_written_at"]
                                                                          for row in opportunities)
    # No magnitude or answer value is held anywhere in a receipt.
    columns = set(opportunities[0])
    assert not columns & {"dwell_ms", "active_seconds", "payload_json", "response_md", "answer_md", "scroll",
                          "visibility"}
    text = json.dumps(opportunities)
    assert "99999" not in text and "777" not in text and "ANSWER-TEXT" not in text and "my words" not in text

    # A changed verdict writes nothing; a second sweep writes nothing new.
    RQC.record_inquiry_action(repo, question_id=styles["recall"], action="self_checked", self_check="matches",
                              clock=at(21))
    assert _sweep(vault, repo, 22).written == 0
    assert len(_by(_opportunities(paths), "in_passage_question", "self_check:matched")) == 0

    # A source row written after a serve is never recorded by that serve's sweep.
    late = _question(repo, "recall", 30)
    assert _sweep(vault, repo, 25).written == 0
    assert not [row for row in _opportunities(paths) if row["source_id"] == late]
    assert _sweep(vault, repo, 31).written == 1
    recorded = [row for row in _opportunities(paths) if row["source_id"] == late][0]
    assert recorded["source_written_at"].startswith("2026-10-12T09:30:00")

    # Deleting the extraction leaves the receipts.
    before = _opportunities(paths)
    repo.delete_source_artifact("src1")
    assert rows(paths.sqlite_path, "SELECT COUNT(*) AS n FROM reader_section_progress")[0]["n"] == 0
    assert _opportunities(paths) == before


def test_a_span_view_of_a_worked_example_is_a_worked_example_only(tmp_path):
    paths, vault, repo = _setup(tmp_path)
    _view(repo, "we1", 1)
    _sweep(vault, repo, 2)
    opportunities = _opportunities(paths)
    assert [(row["kind"], row["subkind"]) for row in opportunities] == [("worked_example", "shown")]


def test_held_out_material_is_never_a_reading_opportunity(tmp_path):
    paths, vault, repo = _setup(tmp_path)
    mapping = FakeMap()
    mapping.held.add(("ext1", "s1"))
    _view(repo, "s1", 1)
    _tutor(repo, 2)
    repo.upsert_reader_section_progress(extraction_id="ext1", section_id="u1", completed=True, clock=at(3))
    _sweep(vault, repo, 4, mapping=mapping)
    assert _opportunities(paths) == []


def test_reading_receipts_are_off_with_forecast_receipts_off(tmp_path):
    paths, vault, repo = _setup(tmp_path, config="[adaptive_difficulty]\nforecast_receipts = false\n")
    repo.upsert_reader_section_progress(extraction_id="ext1", section_id="u1", completed=True, clock=at(1))
    _view(repo, "s1", 2)
    _question(repo, "recall", 3)
    assert _sweep(vault, repo, 4).written == 0
    assert _sweep(vault, repo, 4, kind="backfill").written == 0
    assert _opportunities(paths) == []


def test_reading_receipts_are_append_only(tmp_path):
    import sqlite3

    paths, vault, repo = _setup(tmp_path)
    _view(repo, "s1", 1)
    _sweep(vault, repo, 2)
    with sqlite3.connect(paths.sqlite_path) as connection:
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("UPDATE ad_reading_opportunities SET learning_object_id = 'x'")
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("DELETE FROM ad_reading_opportunities")


def test_the_vault_map_reads_the_readers_own_section_rule(tmp_path):
    """End to end with the vault's own map: an LO whose provenance cites a span
    of the completed section gets the section; its item's facet takes the dose."""

    import yaml

    from learnloop.adaptive_difficulty.reading import sweep

    paths, _vault, repo = _setup(tmp_path)
    lo_path = paths.learning_object_path("linear-algebra", LO_A)
    payload = yaml.safe_load(lo_path.read_text(encoding="utf-8"))
    payload["provenance"] = {"origin": "human", "source_refs": [
        {"ref_type": "canonical_source", "ref_id": "src1", "source_id": "src1", "revision_id": "rev1",
         "extraction_id": "ext1", "span_ids": ["s1"], "locator": "span:ext1/s1"}]}
    lo_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    vault = load_vault(paths.root)
    repo.upsert_reader_section_progress(extraction_id="ext1", section_id="u1", completed=True, clock=at(1))
    result = sweep(vault, repo, as_of=iso(2), sweep_kind="backfill", clock=at(2))
    section = _by(_opportunities(paths), "reading", "section_read")
    assert result.written >= 1
    assert [row["learning_object_id"] for row in section] == [LO_A]
    import json

    assert json.loads(section[0]["facet_doses_json"]) == {"recall": 1.0}
