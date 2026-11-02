"""Follow-ups batch 5 (H): the C5 audit. A note read as learner text writes its ``judgment_ledger`` verdicts
through the same shared writers as every other learner text (``judges.log_reading`` for the reader's
``learner_gap_kind``, the Decider's kind verdict, ``matching.judge.judge_pairs`` for the pair tasks), so
each row carries a verdict and a rationale in the same shape as an ordinary text's on the same task, and
the learner-text-gaps report reads the note's gap and its pair verdicts. C5 added no ledger writer of its
own (``git show`` of its commits: no new ``append_judgment`` call). Every model is a fake; synthetic vault.
"""

from __future__ import annotations

import json

from learnloop.diagnosis.text_gaps.contract import KIND_TASK
from learnloop.diagnosis.text_gaps.report import build_report
from learnloop.tutor.ai_contracts import LearnerGap
from learnloop.vault.loader import load_vault
from tests.test_notes_as_learner_text import TYPED, _clients, _linked, _run, _snapshots
from tests.text_gap_fakes import ChoiceDecider, GapLLMFake, word_match

#: The columns every judge's verdict fills (the shared writers' shape).
FILLED = ("task", "left_kind", "left_id", "judge", "judge_model", "prompt_version", "input_hash", "verdict",
          "rationale")


def _ledger(repository):
    with repository.connection() as connection:
        cursor = connection.execute("SELECT * FROM judgment_ledger ORDER BY rowid")
        names = [d[0] for d in cursor.description]
        return [dict(zip(names, row)) for row in cursor.fetchall()]


def test_a_notes_ledger_verdicts_have_the_shared_shape_and_the_report_reads_them(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    reader = GapLLMFake(reading=LearnerGap(kind="prerequisite", prerequisite_name="the determinant of a matrix",
                                           prerequisite_line="Uses det(A - lI) without knowing determinants."),
                        decide=word_match("determinant"))
    decider = ChoiceDecider(kind="prerequisite", pair=word_match("determinant"))
    outcome = _run(paths, repository, _clients(reader, decider=decider), source=("learner_note", snapshots[TYPED]))
    assert outcome.state == "done"
    rows = _ledger(repository)
    note_rows = [row for row in rows if row["left_kind"] == "learner_note" or row["right_kind"] == "learner_note"]
    kinds = [row for row in note_rows if row["task"] == KIND_TASK]
    assert {row["judge"] for row in kinds} >= {"llm", "decider"}
    reading = next(row for row in kinds if row["judge"] == "llm")
    # The reader's verdict and its rationale (the gap it named), as for every learner text.
    assert reading["verdict"] == "prerequisite"
    assert json.loads(reading["rationale"])["prerequisite_name"] == "the determinant of a matrix"
    for row in note_rows:
        missing = [name for name in FILLED if row[name] in (None, "")]
        assert not missing, (row["task"], row["judge"], missing)
    # The pair verdicts the note's gap took part in (judge_pairs: verdict and rationale on every row).
    pairs = [row for row in rows if row["task"] != KIND_TASK and row["judge"] in ("llm", "decider")]
    assert pairs and all(row["verdict"] for row in pairs)
    assert all(row["rationale"] is not None for row in pairs)
    report = build_report(load_vault(paths.root), repository)
    assert report["by_source"].get("learner_note") == 1
    assert report["by_kind_and_chooser"]
