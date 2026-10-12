"""Append-only verdict inputs. Corrections supersede, never rewrite history."""
from __future__ import annotations

from datetime import datetime, timezone
import math
import sqlite3
from uuid import uuid4


def append_judgment(connection: sqlite3.Connection, *, task: str, left_kind: str,
                    left_id: str, judge: str, input_hash: str, verdict: str,
                    right_kind: str | None = None, right_id: str | None = None,
                    judge_model: str | None = None, prompt_version: str | None = None,
                    score: float | None = None, rationale: str = "",
                    supersedes_id: str | None = None, id: str | None = None,
                    created_at: str | None = None) -> str:
    """Append within the caller's transaction; SQL enforces supersession identity.

    A question is the ordered (task, left_kind/id, right_kind/id) tuple.
    A different judge, model, prompt or input revision may correct that question.
    """
    if not all((task, left_kind, left_id, judge, input_hash, verdict)):
        raise ValueError("judgment identity, producer and verdict must be nonempty")
    if judge in {"llm", "diagnoser"} and not (judge_model and prompt_version):
        raise ValueError("llm/diagnoser judgments require nonempty judge_model and prompt_version")
    if score is not None and not math.isfinite(score):
        raise ValueError("score must be finite")
    judgment_id = id or str(uuid4())
    connection.execute(
        "INSERT INTO judgment_ledger "
        "(id,created_at,supersedes_id,task,left_kind,left_id,right_kind,right_id,"
        "judge,judge_model,prompt_version,input_hash,verdict,score,rationale) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (judgment_id, created_at or datetime.now(timezone.utc).isoformat(), supersedes_id,
         task, left_kind, left_id, right_kind, right_id, judge, judge_model,
         prompt_version, input_hash, verdict, score, rationale),
    )
    return judgment_id
