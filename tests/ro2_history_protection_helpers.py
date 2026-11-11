"""What other test files use from ``tests/test_ro2_history_protection.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
import sqlite3

from learnloop.vault.loader import load_vault


SENTINEL = "SENTINEL-HELD-OUT-RO2"
SERVED = "2026-10-12T09:00:00Z"
BEFORE = "2026-10-11T09:00:00Z"


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
