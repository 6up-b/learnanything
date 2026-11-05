"""Router objective RO2 §6.5: protection on every rung of ``ad-forecast-state-v3`` and the leak test.

* Held-out material (an item made from a held-out unit, and every row naming it: its attempts, help,
  questions, reveals, the gaps named from its answers; a help row citing a held-out span) never reaches
  any rung; exam work shows its result only and a diagnostic probe no question and no answer
  (``learner_protection``); no reference solution reaches a card.
* Content marked held out after the serve: the frozen rungs expire (the protection epoch moved) and
  the job sends nothing and records nothing.
* The leak test: no event with ``available_at > served_at`` reaches a card; a backdated import (an
  exam imported after the serve, dated before it) is the case, at the RO1 tag and below it.

Fakes only; no model call.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing

import pytest

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad_fakes import ForecastLLM, rows

SENTINEL = "SENTINEL-HELD-OUT-RO2"
SERVED = "2026-10-12T09:00:00Z"
BEFORE = "2026-10-11T09:00:00Z"


def _cards(paths, item_id: str, served_at: str) -> dict[str, dict]:
    """Every rung's card for ``item_id`` at ``served_at``, built inside an AD operation (its guard on:
    a refused read poisons the operation and raises)."""

    from learnloop.adaptive_difficulty import history_card as HC
    from learnloop.adaptive_difficulty.operation import ad_operation

    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    with ad_operation(vault, repository, read_only=True) as op:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            item = op.view.item(item_id)
            built = HC.build_sections(op.vault, connection, item, served_at=served_at, view=op.view)
            return {rung: HC.rung_card(op.vault, item, built, rung, budget=10 ** 7)[0] for rung in HC.RUNGS}


def _insert(connection, table: str, values: dict) -> None:
    connection.execute(f"INSERT INTO {table}({', '.join(values)}) VALUES ({', '.join('?' for _ in values)})",
                       tuple(values.values()))


def _textbook(tmp_path):
    from learnloop.content.synthesis.source_unit_selection import save_unit_selection
    from learnloop.vault.models import CanonicalExercise
    from learnloop.vault.writer import upsert_practice_item
    from tests.source_service_fakes import build_textbook_vault

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"exercises": "held_out_evaluation"})
    vault = load_vault(paths.root)
    base = vault.practice_items["pi_eigen_1"]
    for item_id, prompt, unit in (("pi_held", f"{SENTINEL}: find the eigenvalues.", "exercises"),
                                  ("pi_late", "LATE-STEM: diagonalize.", "worked")):
        upsert_practice_item(paths.root, base.model_copy(update={
            "id": item_id, "prompt": prompt, "expected_answer": f"{SENTINEL} reference {item_id}",
            "canonical_exercise": CanonicalExercise(source_id="src_text", extraction_id="ext_text",
                                                    span_ids=[spans[unit][1]]),
        }).model_dump(mode="json"))
    vault = load_vault(paths.root)
    lo = base.learning_object_id
    with sqlite3.connect(paths.sqlite_path) as connection:
        for attempt_id, item_id, kind, answer in (
                ("att_held", "pi_held", "independent_attempt", f"{SENTINEL} answer"),
                ("att_pub", "pi_eigen_1", "independent_attempt", "PUBLIC-ANSWER"),
                ("att_late", "pi_late", "independent_attempt", "LATE-ANSWER"),
                ("att_exam", "pi_eigen_1", "exam_attempt", "EXAM-ANSWER-TEXT"),
                ("att_tb", "pi_eigen_1", "teach_back", "TEACH-BACK-TEXT")):
            _insert(connection, "practice_attempts", {
                "id": attempt_id, "practice_item_id": item_id, "learning_object_id": lo,
                "practice_mode": base.practice_mode, "attempt_type": kind, "correctness": 1.0,
                "learner_answer_md": answer, "answer_confidence": 4, "created_at": BEFORE})
        for help_id, attempt_id, item_id, body, manifest in (
                ("ha_held", "att_held", "pi_held", f"{SENTINEL} hint", None),
                ("ha_pub", "att_pub", "pi_eigen_1", "PUBLIC-HINT", None),
                ("ha_cited", "att_pub", "pi_eigen_1", "CITED-HINT",
                 json.dumps({"extraction_id": "ext_text", "span_ids": [spans["exercises"][1]]}))):
            _insert(connection, "help_assists", {
                "id": help_id, "surface": "practice", "assist_kind": "hint", "practice_item_id": item_id,
                "attempt_id": attempt_id, "hint_kind": "next_step", "level": 2, "body_md": body, "chooser": "none",
                "shown": 1, "requested_at": BEFORE, "shown_at": BEFORE, "retrieval_manifest_json": manifest})
        for question_id, item_id, text in (("qe_held", "pi_held", f"{SENTINEL} question"),
                                           ("qe_pub", "pi_eigen_1", "PUBLIC-QUESTION")):
            _insert(connection, "question_events", {
                "id": question_id, "context": "practice", "practice_item_id": item_id, "question_md": text,
                "answer_md": f"{SENTINEL} tutor answer", "created_at": BEFORE,
                "reveal_state_json": json.dumps({"visible_now": "unknown"})})
        _insert(connection, "reveal_events", {"id": "rv_held", "practice_item_id": "pi_held", "learning_object_id": lo,
                                              "source_kind": "answer_display", "amount": 1.0,
                                              "basis": f"{SENTINEL} basis", "created_at": BEFORE})
        _insert(connection, "learner_text_gaps", {
            "id": "gap_held", "source_kind": "tutor_question", "source_id": "qe_held", "attempt_id": "att_held",
            "practice_item_id": "pi_held", "anchor_learning_object_id": lo, "learner_text": f"{SENTINEL} gap",
            "chooser": "decider", "context_judge": "tutor", "kind": "prerequisite", "action": "none",
            "algorithm_version": "v", "pipeline_version": "v", "created_at": BEFORE})
    return paths, repository, spans, vault


def test_held_out_material_reaches_no_rung(tmp_path):
    """Every rung (H0-H3) carries the public history and none of the held-out item's: no stem, answer,
    hint, question, reveal or gap of it, no hint citing a held-out span, no exam answer, no reference
    solution and no tutor answer (fails before RO2: there is no card)."""

    paths, _repository, _spans, vault = _textbook(tmp_path)
    cards = _cards(paths, "pi_eigen_2", SERVED)
    for rung, state in cards.items():
        text = json.dumps(state)
        assert SENTINEL not in text, rung
        assert "CITED-HINT" not in text and "EXAM-ANSWER-TEXT" not in text, rung
        assert vault.practice_items["pi_eigen_2"].expected_answer not in text
    assert "PUBLIC-ANSWER" in json.dumps(cards["H0"]["history"]["recent_attempts"]) or not vault.config.adaptive_difficulty.history_answer_excerpts
    h1 = cards["H1"]["history"]
    assert "PUBLIC-ANSWER" in json.dumps(h1["whole_answers"])
    assert [e["confidence_tap"] for e in h1["whole_answers"] if e["evidence_id"] == "attempt:att_pub"] == [4]
    assert [e["text"] for e in h1["help"] if e.get("text")] == ["PUBLIC-HINT"]
    assert [e.get("question") for e in h1["questions"]] == ["PUBLIC-QUESTION"]
    h3 = cards["H3"]["history"]
    assert [(e["evidence_id"], set(e) & {"answer", "item", "explanation"}) for e in h3["exams"]] == [
        ("attempt:att_exam", set())]
    assert [e.get("explanation") for e in h3["teach_backs"]] == ["TEACH-BACK-TEXT"]
    # Every entry carries an evidence id and its days before the serve.
    for state in cards.values():
        for entries in state["history"].values():
            for entry in entries:
                assert entry["evidence_id"] and entry["days_before"] >= 0


def test_content_held_out_after_the_serve_is_never_sent(tmp_path):
    """A rung frozen before its content was marked held out is refused at the send: nothing is sent and
    nothing recorded (fails before RO2: there is no such job)."""

    from learnloop.adaptive_difficulty.history_forecast import forecast_history_presentation
    from learnloop.adaptive_difficulty.outside import Clients
    from learnloop.adaptive_difficulty.serve import record_plan_serve
    from learnloop.content.synthesis.source_unit_selection import save_unit_selection

    paths, repository, spans, vault = _textbook(tmp_path)
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute("INSERT INTO attention_blocks(id, action, budget_minutes, content_hash, created_at) "
                           "VALUES ('blk', 'practice', 10, 'hash', ?)", (SERVED,))
        connection.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at) "
                           "VALUES ('pp_1', 'blk', 'pi_eigen_2', 'chooser', ?)", (SERVED,))
    with repository.atomic():
        record = record_plan_serve(vault, repository, presentation_id="pp_1", practice_item_id="pi_eigen_2",
                                   served_at=SERVED)
    assert record.history_draw
    frozen = rows(paths.sqlite_path, "SELECT content_json FROM item_forecast_payloads WHERE owner_key LIKE "
                                     "'ad_llm_history_state:%'")
    assert len(frozen) == 2 and all("LATE-ANSWER" in row["content_json"] for row in frozen)
    assert all(SENTINEL not in row["content_json"] for row in frozen)
    save_unit_selection(repository, "ext_text", list(spans),
                        exam_use_modes={"exercises": "held_out_evaluation", "worked": "held_out_evaluation"})
    llm = ForecastLLM()
    outcomes = forecast_history_presentation(load_vault(paths.root), repository, "pp_1", clients=Clients(llm=llm))
    assert outcomes and {o.status for o in outcomes} == {"protected"}
    assert llm.prompts == []
    assert rows(paths.sqlite_path, "SELECT * FROM forecast_receipts WHERE forecaster LIKE 'llm_history_v1:%'") == []


@pytest.mark.parametrize("version", ["mvp-0.22", "mvp-0.46"], ids=["below_tag", "tag"])
def test_no_event_known_after_the_serve_reaches_a_card(tmp_path, version):
    """The leak test: an exam imported after the serve and dated before it, and help, questions and
    reveals recorded after it, reach no rung; once the import arrived it shows, dated when it happened
    (fails before RO2: there is no card)."""

    from tests.ad_fakes import ad_plan_vault

    paths = ad_plan_vault(tmp_path, version=version)
    imported = "2026-10-12T15:00:00Z"
    with sqlite3.connect(paths.sqlite_path) as connection:
        _insert(connection, "practice_attempts", {
            "id": "att_import", "practice_item_id": "pi_m1b", "learning_object_id": "lo_m1",
            "practice_mode": "short_answer", "attempt_type": "exam_evidence", "correctness": 0.0,
            "created_at": "2026-10-05T09:00:00Z", "received_at": imported, "received_at_source": "recorded"})
        _insert(connection, "practice_attempts", {
            "id": "att_known", "practice_item_id": "pi_m1c", "learning_object_id": "lo_m1",
            "practice_mode": "short_answer", "attempt_type": "independent_attempt", "correctness": 1.0,
            "learner_answer_md": "KNOWN", "created_at": BEFORE})
        _insert(connection, "help_assists", {
            "id": "ha_late", "surface": "practice", "assist_kind": "hint", "practice_item_id": "pi_m1c",
            "attempt_id": "att_known", "body_md": "LATE-HINT", "chooser": "none", "shown": 1,
            "requested_at": "2026-10-12T10:00:00Z", "shown_at": "2026-10-12T10:00:00Z"})
        _insert(connection, "question_events", {"id": "qe_late", "context": "practice", "practice_item_id": "pi_m1c",
                                                "question_md": "LATE-QUESTION", "created_at": "2026-10-12T10:00:00Z"})
        _insert(connection, "reveal_events", {"id": "rv_late", "practice_item_id": "pi_m1c", "learning_object_id": "lo_m1",
                                              "source_kind": "answer_display", "amount": 1.0,
                                              "created_at": "2026-10-12T10:00:00Z"})
    cards = _cards(paths, "pi_m1a", SERVED)
    for rung, state in cards.items():
        text = json.dumps(state)
        assert "att_import" not in text and "LATE-" not in text, rung
    assert "attempt:att_known" in json.dumps(cards["H3"])
    later = _cards(paths, "pi_m1a", "2026-10-13T09:00:00Z")
    exams = later["H3"]["history"]["exams"]
    assert [(e["evidence_id"], e["days_before"]) for e in exams] == [("attempt:att_import", 8.0)]
    assert "LATE-HINT" in json.dumps(later["H1"])


def test_the_budget_trims_oldest_first_within_each_rung_and_says_so(tmp_path):
    """Over the token budget, each rung loses its oldest entries first and the card states what it left
    out; the reads are bounded by row limits before that (fails before RO2)."""

    from learnloop.adaptive_difficulty import history_card as HC
    from learnloop.adaptive_difficulty.operation import ad_operation
    from tests.ad_fakes import ad_plan_vault

    paths = ad_plan_vault(tmp_path)
    with sqlite3.connect(paths.sqlite_path) as connection:
        for index in range(40):
            _insert(connection, "practice_attempts", {
                "id": f"att_{index:02d}", "practice_item_id": "pi_m1b", "learning_object_id": "lo_m1",
                "practice_mode": "short_answer", "attempt_type": "independent_attempt", "correctness": 1.0,
                "learner_answer_md": "word " * 300, "created_at": f"2026-09-{(index % 28) + 1:02d}T09:00:00Z"})
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    with ad_operation(vault, repository, read_only=True) as op:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            item = op.view.item("pi_m1a")
            built = HC.build_sections(op.vault, connection, item, served_at=SERVED, view=op.view)
            full, _ = HC.rung_card(op.vault, item, built, "H1", budget=10 ** 7)
            state, left_out = HC.rung_card(op.vault, item, built, "H1", budget=20_000)
    assert HC._size(state) <= 20_000 < HC._size(full)
    assert left_out["H1"]["whole_answers"]["entries"] > 0 and state["left_out"] == left_out
    kept = state["history"]["whole_answers"]
    dropped_oldest = left_out["H1"]["whole_answers"]["oldest_days_before"]
    assert all(entry["days_before"] <= dropped_oldest for entry in kept)
    assert max(e["days_before"] for e in full["history"]["whole_answers"]) == dropped_oldest
