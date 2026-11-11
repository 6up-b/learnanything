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
from datetime import datetime, timedelta, timezone

import pytest

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad_fakes import ForecastLLM, rows
from tests.ro2_history_protection_helpers import BEFORE, SENTINEL, SERVED, _insert, _textbook

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


def _gap(connection, gap_id: str, source_kind: str, source_id: str, lo: str, text: str, **extra) -> None:
    _insert(connection, "learner_text_gaps", {
        "id": gap_id, "source_kind": source_kind, "source_id": source_id, "anchor_learning_object_id": lo,
        "learner_text": text, "chooser": "decider", "context_judge": "gap_reader", "kind": "prerequisite",
        "action": "none", "algorithm_version": "v", "pipeline_version": "v", "created_at": BEFORE, **extra})


def _gap_texts(cards) -> list[str]:
    return sorted(str(entry.get("learner_text")) for entry in cards["H3"]["history"]["gaps"] if entry.get("learner_text"))


def test_a_gap_is_withheld_with_the_source_it_was_named_from(tmp_path):
    """Codex review F1: a gap stands or falls by the learner text it was named from, through that
    source's own rule: a Reader formative answer on a reading the held-out material touches, a hint reply
    to a help row citing a held-out span, and any source kind the registry cannot judge are withheld,
    while a gap from a visible attempt's stuck answer stays (fails before the fix: only a tutor question
    source was resolved, so the first two and the unknown kind reached H3)."""

    paths, _repository, spans, vault = _textbook(tmp_path)
    lo = vault.practice_items["pi_eigen_1"].learning_object_id
    with sqlite3.connect(paths.sqlite_path) as connection:
        _insert(connection, "reader_authored_questions", {
            "id": "rq_text", "extraction_id": "ext_text", "section_id": "sec", "question_md": "why?",
            "expected_answer_md": "because", "anchor_span_ids_json": json.dumps([spans["worked"][1]]),
            "prompt_version": "v", "status": "answered", "response_md": "my answer", "answered_at": BEFORE,
            "created_at": BEFORE, "updated_at": BEFORE})
        _gap(connection, "gap_reader", "reader_formative", "rq_text", lo, f"{SENTINEL} formative")
        _gap(connection, "gap_hint", "hint_feedback", "ha_cited", lo, f"{SENTINEL} hint reply",
             attempt_id="att_pub", practice_item_id="pi_eigen_1")
        _gap(connection, "gap_stuck", "stuck_answer", "att_pub", lo, "PUBLIC-STUCK", attempt_id="att_pub",
             practice_item_id="pi_eigen_1")
        connection.execute("PRAGMA ignore_check_constraints = ON")
        _gap(connection, "gap_unknown", "a_future_source", "x", lo, f"{SENTINEL} unknown source")
    cards = _cards(paths, "pi_eigen_2", SERVED)
    assert _gap_texts(cards) == ["PUBLIC-STUCK"]
    assert SENTINEL not in json.dumps(cards["H3"])


def test_a_gap_whose_source_is_marked_held_out_after_it_was_named_is_withheld(tmp_path):
    """Codex review F1's regression: a formative answer's gap shows while its passage is public, and is
    withheld once the passage's unit is marked held out after the gap was recorded."""

    from learnloop.content.synthesis.source_unit_selection import save_unit_selection
    from tests.source_service_fakes import build_textbook_vault

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    lo = vault.practice_items["pi_eigen_1"].learning_object_id
    with sqlite3.connect(paths.sqlite_path) as connection:
        _insert(connection, "reader_authored_questions", {
            "id": "rq_text", "extraction_id": "ext_text", "section_id": "sec", "question_md": "why?",
            "expected_answer_md": "because", "anchor_span_ids_json": json.dumps([spans["worked"][1]]),
            "prompt_version": "v", "status": "answered", "response_md": "my answer", "answered_at": BEFORE,
            "created_at": BEFORE, "updated_at": BEFORE})
        _gap(connection, "gap_reader", "reader_formative", "rq_text", lo, "FORMATIVE-GAP")
        # Figure predictions: one on a figure anchored on the passage, one on a figure with no passage of
        # its own (grounded in retrieved passages AD never reads: withheld, fail closed).
        for figure_id, anchored in (("fig_anchored", [spans["worked"][1]]), ("fig_grounded", [])):
            _insert(connection, "interactive_figures", {
                "id": figure_id, "extraction_id": "ext_text", "span_ids_json": json.dumps(anchored),
                "origin": "selection", "spec_version": "v", "verification": "failed", "prompt_version": "v",
                "input_hash": figure_id, "created_at": BEFORE})
            _insert(connection, "figure_predictions", {
                "id": f"fpr_{figure_id}", "figure_id": figure_id, "extraction_id": "ext_text", "prediction_index": 0,
                "learner_answer": "rises", "observed_json": "{}", "matched": 0, "created_at": BEFORE})
        _gap(connection, "gap_fig", "reader_formative", "fpr_fig_anchored:explained", lo, "FIGURE-GAP")
        _gap(connection, "gap_fig_grounded", "reader_formative", "fpr_fig_grounded", lo, "GROUNDED-FIGURE-GAP")
    assert _gap_texts(_cards(paths, "pi_eigen_2", SERVED)) == ["FIGURE-GAP", "FORMATIVE-GAP"]
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"worked": "held_out_evaluation"})
    assert _gap_texts(_cards(paths, "pi_eigen_2", SERVED)) == []


def test_the_registry_restates_the_figure_source_grammar():
    """AD imports nothing of the diagnosis package (a contract), so the figure-prediction source id's
    grammar is restated in the material view: pinned equal here."""

    from learnloop.adaptive_difficulty import material_view as MV
    from learnloop.adaptive_difficulty.protected_tables import GAP_SOURCES
    from learnloop.diagnosis.text_gaps import sources as S

    assert (MV._FIGURE_PREDICTION_PREFIX, MV._FIGURE_EXPLANATION_SUFFIX) == (
        S.FIGURE_PREDICTION_PREFIX, S.FIGURE_EXPLANATION_SUFFIX)
    # Every source kind the gap pipeline reads is judged by the registry (a new one fails here first).
    import inspect

    kinds = set(__import__("re").findall(r'source_kind == "([a-z_]+)"', inspect.getsource(S.learner_text)))
    assert kinds == set(GAP_SOURCES)


def test_h2_carries_open_inquiries_by_their_status_at_the_serve(tmp_path):
    """Codex review F6: H2's inquiries are the learner's Reader questions on the LO, read directly (not
    only through the receipts of completed exchanges), each with its inquiry's status at the serve: the
    root question's learner-owned ``resolution`` as the logged status changes place it, never whether the
    tutor answered. A tutor-answered inquiry the learner left open is open; an unanswered one is there,
    open; one resolved before the serve and reopened after it was resolved at the serve; a branch carries
    its root's status; a question asked after the serve is absent (fails before the fix: H2 found
    inquiries only through reading receipts and read "open" from the tutor's answer)."""

    from tests.ad_fakes import ad_plan_vault

    paths = ad_plan_vault(tmp_path)
    context = json.dumps({"candidate_learning_object_ids": ["lo_m1"], "extraction_id": "ext_any"})
    with sqlite3.connect(paths.sqlite_path) as connection:
        for question_id, status, answered, created in (
                ("qe_open", "answered", BEFORE, BEFORE), ("qe_pending", "pending", None, BEFORE),
                ("qe_reopened", "answered", BEFORE, BEFORE), ("qe_branch", "answered", BEFORE, BEFORE),
                ("qe_after", "pending", None, "2026-10-12T10:00:00Z")):
            _insert(connection, "question_events", {
                "id": question_id, "context": "reader", "question_md": f"INQUIRY {question_id}",
                "answer_md": "TUTOR-ANSWER-TEXT", "answer_status": status, "answered_at": answered,
                "source_context_json": context, "resolution": "open", "created_at": created})
        for event_id, question_id, parent in (("ex_open", "qe_open", None), ("ex_reopened", "qe_reopened", None),
                                               ("ex_branch", "qe_branch", "ex_open")):
            _insert(connection, "interaction_events", {
                "id": event_id, "kind": "reader_answer_submitted", "origin": "system", "subject_type": "reader_span",
                "subject_id": "span:ext_any/sp_1", "created_at": BEFORE,
                "payload_json": json.dumps({"question_event_id": question_id, "parent_exchange_id": parent,
                                            "extraction_id": "ext_any", "span_id": "sp_1"})})
        for event_id, resolution, previous, at in (("st_1", "resolved", "open", "2026-10-11T12:00:00Z"),
                                                   ("st_2", "open", "resolved", "2026-10-12T12:00:00Z")):
            _insert(connection, "interaction_events", {
                "id": event_id, "kind": "reader_action_invoked", "origin": "learner", "subject_type": "reader_inquiry",
                "subject_id": "ex_reopened", "created_at": at,
                "payload_json": json.dumps({"event": "inquiry_status_set", "extraction_id": "ext_any",
                                            "root_exchange_id": "ex_reopened", "question_event_id": "qe_reopened",
                                            "resolution": resolution, "previous_resolution": previous})})
    cards = _cards(paths, "pi_m1a", SERVED)
    inquiries = {entry["evidence_id"]: entry for entry in cards["H2"]["history"]["inquiries"]}
    assert set(inquiries) == {"question:qe_open", "question:qe_pending", "question:qe_reopened", "question:qe_branch"}
    assert (inquiries["question:qe_open"]["status"], inquiries["question:qe_open"]["open"]) == ("open", True)
    assert inquiries["question:qe_open"]["tutor_answered"] is True
    assert (inquiries["question:qe_pending"]["open"], inquiries["question:qe_pending"]["tutor_answered"]) == (True, False)
    assert (inquiries["question:qe_reopened"]["status"], inquiries["question:qe_reopened"]["open"]) == ("resolved", False)
    assert inquiries["question:qe_branch"]["root"] == "question:qe_open" and inquiries["question:qe_branch"]["open"]
    assert inquiries["question:qe_pending"]["question"] == "INQUIRY qe_pending"
    assert "TUTOR-ANSWER-TEXT" not in json.dumps(cards["H3"])


def _reader_question(connection, question_id: str, los: list[str], created: str, **extra) -> None:
    _insert(connection, "question_events", {
        "id": question_id, "context": "reader", "question_md": f"INQUIRY {question_id}", "answer_status": "answered",
        "answered_at": created, "resolution": "open", "created_at": created,
        "source_context_json": json.dumps({"candidate_learning_object_ids": los, "extraction_id": "ext_any"}), **extra})


def _exchange(connection, event_id: str, question_id: str, parent: str | None, created: str) -> None:
    _insert(connection, "interaction_events", {
        "id": event_id, "kind": "reader_answer_submitted", "origin": "system", "subject_type": "reader_span",
        "subject_id": "span:ext_any/sp_1", "created_at": created,
        "payload_json": json.dumps({"question_event_id": question_id, "parent_exchange_id": parent,
                                    "extraction_id": "ext_any", "span_id": "sp_1"})})


def _built(paths, item_id: str, served_at: str, statements: list[str] | None = None) -> dict:
    """``build_sections``' output, every statement its connection ran collected in ``statements``."""

    from learnloop.adaptive_difficulty import history_card as HC
    from learnloop.adaptive_difficulty.operation import ad_operation

    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    with ad_operation(vault, repository, read_only=True) as op:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            if statements is not None:
                connection.set_trace_callback(statements.append)
            return HC.build_sections(op.vault, connection, op.view.item(item_id), served_at=served_at, view=op.view)


def test_unrelated_inquiries_never_displace_the_scopes_inquiries(tmp_path):
    """Codex re-review F7: the inquiry read selects the scope's inquiries before its row limit, so a
    hundred newer Reader questions on another LO leave the target LO's one in H2, with the reading it
    was asked on (fails before the fix: the newest 100 across every LO were read and filtered after)."""

    from learnloop.adaptive_difficulty import history_card as HC
    from tests.ad_fakes import ad_plan_vault

    paths = ad_plan_vault(tmp_path)
    limit = HC.ROW_LIMITS["inquiries"]
    with sqlite3.connect(paths.sqlite_path) as connection:
        _reader_question(connection, "qe_target", ["lo_m1"], "2026-10-01T09:00:00Z")
        for index in range(limit):
            _reader_question(connection, f"qe_other_{index:03d}", ["lo_elsewhere"], BEFORE)
    built = _built(paths, "pi_m1a", SERVED)
    inquiries = [entry["evidence_id"] for entry in built["sections"]["inquiries"]]
    assert inquiries == ["question:qe_target"]
    assert inquiries == [e["evidence_id"] for e in _cards(paths, "pi_m1a", SERVED)["H2"]["history"]["inquiries"]]


def test_inquiry_ancestry_reads_within_a_shared_budget_and_says_unknown_past_it(tmp_path):
    """Codex re-review F8: a branch chain longer than the ancestry budget costs a bounded number of
    reads, records the truncation, and gives the scoped inquiry an unknown root and status (never the
    furthest ancestor read as if it were the root); a short chain still resolves to its root (fails
    before the fix: one read per ancestor, 300 ancestors 300 reads)."""

    from learnloop.adaptive_difficulty import history_card as HC
    from tests.ad_fakes import ad_plan_vault

    paths = ad_plan_vault(tmp_path)
    with sqlite3.connect(paths.sqlite_path) as connection:
        depth = 300
        for index in range(depth + 1):  # q_000 is the root; q_300, the newest branch, is on the scope
            stamp = (datetime(2026, 10, 1, tzinfo=timezone.utc) + timedelta(minutes=index)).strftime("%Y-%m-%dT%H:%M:%SZ")
            _reader_question(connection, f"q_{index:03d}", ["lo_m1"] if index == depth else ["lo_elsewhere"], stamp)
            _exchange(connection, f"ex_{index:03d}", f"q_{index:03d}", f"ex_{index - 1:03d}" if index else None, stamp)
        _reader_question(connection, "q_short_root", ["lo_m1"], BEFORE)
        _exchange(connection, "ex_short_root", "q_short_root", None, BEFORE)
        _reader_question(connection, "q_short_branch", ["lo_m1"], BEFORE)
        _exchange(connection, "ex_short_branch", "q_short_branch", "ex_short_root", BEFORE)
    statements: list[str] = []
    built = _built(paths, "pi_m1a", SERVED, statements)
    exchange_reads = [s for s in statements if "reader_answer_submitted" in s and "FROM interaction_events" in s]
    assert len(exchange_reads) <= HC.ANCESTRY_ROUNDS + 1, len(exchange_reads)
    assert "inquiry_ancestry" in built["row_limits_reached"]
    inquiries = {entry["evidence_id"]: entry for entry in built["sections"]["inquiries"]}
    assert (inquiries["question:q_300"]["root"], inquiries["question:q_300"]["status"],
            inquiries["question:q_300"]["open"]) == ("unknown", "unknown", False)
    assert (inquiries["question:q_short_branch"]["root"], inquiries["question:q_short_branch"]["status"]) == (
        "question:q_short_root", "open")


def test_a_capped_ancestry_read_leaves_its_unread_parents_unknown(tmp_path):
    """Codex final verify F9 (landing ruling R1), Codex's reproduction: 60 independent four-question
    threads on the target LO, each parent earlier than its child. The newest 100 inquiries are kept and
    the exchange reads return 100, 60 and 40 rows, the last capped by the shared 200-row budget. A parent
    the capped read left unread is unresolved ancestry: every inquiry whose walk reaches one has an
    unknown root and status and ``open`` false, and ``inquiry_ancestry`` is among the reads that hit
    their limit; an inquiry whose whole chain was read keeps its true root (fails before the fix: the
    whole requested batch counted as visited, and 40 inquiries got a false intermediate root, open)."""

    from learnloop.adaptive_difficulty import history_card as HC
    from tests.ad_fakes import ad_plan_vault

    paths = ad_plan_vault(tmp_path)
    threads, depth = 60, 4
    with sqlite3.connect(paths.sqlite_path) as connection:
        for level in range(depth):  # level 0 is each thread's root; every level after the one before
            for thread in range(threads):
                stamp = (datetime(2026, 10, 1, tzinfo=timezone.utc) + timedelta(days=level, minutes=thread)
                         ).strftime("%Y-%m-%dT%H:%M:%SZ")
                question = f"q_{thread:02d}_{level}"
                _reader_question(connection, question, ["lo_m1"], stamp)
                _exchange(connection, f"ex_{thread:02d}_{level}", question,
                          f"ex_{thread:02d}_{level - 1}" if level else None, stamp)
    statements: list[str] = []
    built = _built(paths, "pi_m1a", SERVED, statements)
    exchange_reads = [s for s in statements if "reader_answer_submitted" in s and "FROM interaction_events" in s]
    assert len(exchange_reads) == 3, len(exchange_reads)
    assert len(built["sections"]["inquiries"]) == HC.ROW_LIMITS["inquiries"]
    assert "inquiry_ancestry" in built["row_limits_reached"]
    known, unknown = 0, 0
    for entry in built["sections"]["inquiries"]:
        thread = entry["evidence_id"].split("_")[1]
        if entry["root"] == "unknown":
            unknown += 1
            assert (entry["status"], entry["open"]) == ("unknown", False), entry
        else:
            known += 1
            assert entry["root"] == f"question:q_{thread}_0", entry
            assert (entry["status"], entry["open"]) == ("open", True), entry
    assert unknown > 0 and known > 0, (known, unknown)
    assert "inquiry_ancestry" in _cards(paths, "pi_m1a", SERVED)["H2"]["row_limits_reached"]


def test_an_anchor_mapped_inquiry_behind_the_recent_limit_is_missing_and_the_card_says_so(tmp_path, monkeypatch):
    """Codex final verify F7 (landing ruling R2, accepted as Low), Codex's reproduction: an older
    inquiry whose recorded candidates exclude the target LO, placed on the scope only by its anchor's
    current mapping, behind 100 newer unrelated inquiries, is missing from the card, and the card lists
    ``recent_inquiries`` among the reads that hit their limit. Without the newer inquiries it is there
    and the read is not listed. Model input only: nothing a learner sees changes."""

    from learnloop.adaptive_difficulty import history_card as HC
    from learnloop.adaptive_difficulty.reading import VaultReadingMap
    from tests.ad_fakes import ad_plan_vault

    original = VaultReadingMap.los_for_note
    # The anchor's mapping at the serve (a note the vault holds no record of, so the scoped read cannot
    # name it) places the inquiry on the target LO.
    monkeypatch.setattr(VaultReadingMap, "los_for_note",
                        lambda self, note_id: ["lo_m1"] if note_id == "note_anchor" else original(self, note_id))
    paths = ad_plan_vault(tmp_path)
    with sqlite3.connect(paths.sqlite_path) as connection:
        _reader_question(connection, "qe_anchor", ["lo_elsewhere"], "2026-10-01T09:00:00Z", note_id="note_anchor")
    alone = _cards(paths, "pi_m1a", SERVED)["H2"]
    assert [e["evidence_id"] for e in alone["history"]["inquiries"]] == ["question:qe_anchor"]
    assert "recent_inquiries" not in alone["row_limits_reached"]
    with sqlite3.connect(paths.sqlite_path) as connection:
        for index in range(HC.ROW_LIMITS["recent_inquiries"]):
            _reader_question(connection, f"qe_other_{index:03d}", ["lo_elsewhere"], BEFORE)
    behind = _cards(paths, "pi_m1a", SERVED)["H2"]
    assert behind["history"]["inquiries"] == []
    assert "recent_inquiries" in behind["row_limits_reached"]


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
