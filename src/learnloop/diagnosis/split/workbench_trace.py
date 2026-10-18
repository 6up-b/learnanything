"""Reader workbench RW2b: the step trace the diagnoser reads at Submit (spec_reader_workbench_v1 §5.4, G37, G38).

For an attempt submitted from the workbench, the diagnoser's context gains,
for this attempt only, the assists in the order they were shown (each check
with its verdicts, step graph and error-kind guess, labelled as the check's
guess; each hint with its kind and level; each discriminating question with
the learner's answer) and the work before each assist, under the prompt
version suffix :data:`SUFFIX`. Every other attempt's context renders and
hashes exactly as before (the stuck-reading precedent).

Read from the ``help_assists`` rows of the attempt's submission (the step
texts are their snapshots), by SQL through the store: never the workbench's
modules (``evidence-never-reads-the-workbench``) and never an approach map
(``graders-never-read-approach-maps``): map nodes and routes are left out.
The guesses are context, never a diagnosis or an error event; the grader
never sees any of it (W8).
"""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import closing
import json
from typing import Any

from learnloop.db.connection import connect

SUFFIX = "+workbench-v1"
#: ``practice_attempts.entry_surface`` of a workbench submit.
WORKBENCH_SURFACES = ("desktop_reader_workbench", "desktop_practice_workbench")
NOTE = (
    "The learner worked this problem in numbered steps and was shown the assists below before submitting "
    "(help, never evidence: the grade is the blind grader's). An error-kind guess is the check's guess, not a "
    "diagnosis; a discriminating answer is the learner's answer to a question meant to tell two explanations "
    "apart."
)
#: Prompt-size bounds (never judgments).
MAX_ASSISTS = 24
STEP_CHARS = 1_200


def _json(value: Any, default: Any) -> Any:
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


def trace_for_attempt(repository: Any, attempt: Mapping[str, Any]) -> dict[str, Any] | None:
    """The trace of a workbench attempt, or None (any other attempt, or a
    workbench attempt with no shown assist)."""

    if str(attempt.get("entry_surface") or "") not in WORKBENCH_SURFACES:
        return None
    submission = attempt.get("submission_id")
    if not submission:
        return None
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'help_assists'"
                              ).fetchone() is None:
            return None
        cursor = connection.execute(
            "SELECT * FROM help_assists WHERE surface = 'workbench' AND submission_id = ? AND shown = 1 "
            "AND assist_kind IN ('check', 'hint', 'discriminate_answer') ORDER BY COALESCE(shown_at, requested_at), rowid",
            (str(submission),))
        names = [column[0] for column in cursor.description]
        rows = [dict(zip(names, raw)) for raw in cursor.fetchall()]
    if not rows:
        return None
    assists: list[dict[str, Any]] = []
    numbers: dict[str, int] = {}
    last_work: list[Any] | None = None
    questions = {row["id"]: row for row in rows if row["assist_kind"] == "hint"}
    for row in rows[:MAX_ASSISTS]:
        snapshot = _json(row.get("step_snapshot_json"), [])
        for entry in snapshot:
            numbers[str(entry.get("chain_id"))] = int(entry.get("number") or 0)
        work = [{"step": entry.get("number"), "kind": entry.get("kind"),
                 "text": str(entry.get("body_md") or "")[:STEP_CHARS]} for entry in snapshot]
        entry: dict[str, Any] = {"order": len(assists) + 1}
        if work and work != last_work:
            entry["work_before"] = work
            last_work = work
        if row["assist_kind"] == "check":
            verdicts = _json(row.get("step_verdicts_json"), [])
            entry.update({
                "assist": "check",
                "verdicts": [{"step": numbers.get(str(v.get("chain_id"))), "verdict": v.get("verdict"),
                              "method": v.get("method"),
                              "depends_on_steps": [numbers.get(str(c)) for c in v.get("depends_on") or ()],
                              "assumption": v.get("assumption") or ""} for v in verdicts],
                "first_questionable_step": numbers.get(str(row.get("first_questionable_step_id"))),
            })
            if row.get("error_kind_guess"):
                entry["error_kind_guess"] = f"{row['error_kind_guess']} (the check's guess, not a diagnosis)"
                entry["rival_readings"] = [{"kind": r.get("kind"), "statement": r.get("statement")}
                                           for r in _json(row.get("alternatives_json"), [])]
        elif row["assist_kind"] == "hint":
            entry.update({"assist": "hint", "kind": row.get("hint_kind"), "level": row.get("level"),
                          "about_step": numbers.get(str(row.get("about_step_id"))),
                          "continues_from_step": numbers.get(str(row.get("continue_from_step_id"))),
                          "text": str(row.get("body_md") or "")[:STEP_CHARS] if row.get("hint_kind") != "authored"
                          else "(one of the item's own hints)"})
            if row.get("feedback_shortcut"):
                entry["after_reply"] = row["feedback_shortcut"]
        else:
            question = questions.get(str(_json(row.get("placement_json"), {}).get("question_assist_id") or ""))
            entry.update({"assist": "discriminating_answer",
                          "question": str((question or {}).get("body_md") or "")[:STEP_CHARS],
                          "answer": str(row.get("feedback_text") or "")[:STEP_CHARS],
                          "settled": bool(_json(row.get("placement_json"), {}).get("settled"))})
        assists.append(entry)
    return {"note": NOTE, "assists": assists}


__all__ = ["NOTE", "SUFFIX", "WORKBENCH_SURFACES", "trace_for_attempt"]
