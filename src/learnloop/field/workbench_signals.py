"""RW2d: workbench signals in the learner field (spec_reader_workbench_v1 §5.11, G41).

Two sources join the field's interaction-signal derivation
(:func:`learnloop.field.signals.load_interaction_signals`) at the successor
``WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION`` with
``workbench.field_signals_enabled`` on:

* **A mid-work stuck step.** A workbench stuck step with text says where the
  learner is stuck, like an "I'm stuck" answer the grader read as confusion,
  so it is a ``stuck_confusion`` row on the problem's LO. One per step chain
  (an edit or an undo continues the chain), observed when the chain first
  held text: the ledger is append-only, so a later edit or delete never
  takes back that the learner was stuck then. An empty stuck step says
  nothing about understanding (the owner's ruling for an empty stuck answer,
  2026-10-12), so it is no signal. A session submitted with no ordinary step
  submitted its stuck text AS the stuck answer (``declared_stuck``), which the
  derivation already reads through the grader's reading; its steps are not
  read again here.
* **Help before the first step.** A help request on the workbench (a hint,
  the bridge to the book, a worked example) whose logged step snapshot
  (``help_assists.step_snapshot_json``, the steps as they stood at the
  request) holds no ordinary step with text. One per session, at its first
  such request. As for the practice screen, only the logged snapshot counts:
  a row without one is not evidence of help before work.

**Never the record (F2).** Each row has no outcome, no mass and no attempt
link: no predictor observes it, no attempt's hint outcome or assistance is
capped by it and the report's question strata do not count it
(``signals.enrich_attempts``). It blocks fast-track
(:func:`signals.blocks_fast_track`: a stuck row by its type, an early-help
row by its flag), so the LO is taught first and never fast-tracked on early
answers alone; "I know this" still works. Abandoned sessions contribute only
through these two sources, never as a failure.

**Targets.** A submitted session's attempt gives the LO and subject (the rows
meet the attempt rows). An open or abandoned session bound to an item gives
the item's own LO and first subject, as a submit would record them; a session
not yet bound to an item (its import pending or failed) has no target and is
counted as unmapped.

The workbench tables are read by SQL here, never through the workbench's
modules (the ``evidence-never-reads-the-workbench`` import contract), and only
when the successor is live: below the tag or switched off, nothing here runs.
The pure part (:func:`derive_workbench_signals`) takes plain rows.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from typing import Any

from learnloop.algorithm_versions import WORKBENCH_FIELD_SIGNALS_VERSIONS
from learnloop.field.types import SignalRow

#: Recorded in the derivation's diagnostics and on every receipt.
WORKBENCH_SIGNAL_VERSION = "workbench-field-signals-v1"
#: ``signal_type`` of a mid-work stuck step: the field's existing confusion
#: type (``signals.STUCK_CONFUSION_SIGNAL``), so it blocks as a stuck answer does.
STUCK_CONFUSION_SIGNAL = "stuck_confusion"
#: ``signal_type`` of help asked for before the first step; it blocks through
#: ``help_before_work``, the flag the practice screen's early help sets.
WORKBENCH_HELP_SIGNAL = "workbench_help_before_work"
STUCK_PREFIX = "workbench_stuck:"
HELP_PREFIX = "workbench_help:"
#: Help the learner asked for (``help_assists.assist_kind``). A check of their
#: work, an answer to a discriminating question, a reply about a hint and a
#: method comparison after a correct answer are not requests for help.
HELP_ASSIST_KINDS: tuple[str, ...] = ("hint", "bridge", "example")


def workbench_field_signals_live(vault: Any) -> bool:
    """At the successor (or later) with ``workbench.field_signals_enabled`` on."""

    config = getattr(vault, "config", None)
    version = getattr(getattr(config, "algorithms", None), "algorithm_version", None)
    if version not in WORKBENCH_FIELD_SIGNALS_VERSIONS:
        return False
    section = getattr(config, "workbench", None)
    return bool(getattr(section, "field_signals_enabled", False))


def is_workbench_signal(signal: SignalRow) -> bool:
    """A row only the successor's derivation produces (the predecessor's are the rest)."""

    return signal.signal_id.startswith((STUCK_PREFIX, HELP_PREFIX))


def _has_text(value: Any) -> bool:
    return bool(str(value or "").strip())


def _chain_roots(steps: Iterable[Mapping[str, Any]]) -> dict[str, str]:
    """Each step row's chain root: an edit, tombstone or undo supersedes the head."""

    parent = {str(step["id"]): (str(step["supersedes_id"]) if step.get("supersedes_id") else None)
              for step in steps}
    roots: dict[str, str] = {}
    for step_id in parent:
        seen = []
        current = step_id
        while parent.get(current) and current not in seen:
            seen.append(current)
            current = parent[current]  # type: ignore[assignment]
        roots[step_id] = current
    return roots


def _snapshot_has_work(raw: Any) -> bool | None:
    """Whether a logged step snapshot holds an ordinary step with text; None if unreadable."""

    try:
        entries = json.loads(raw) if isinstance(raw, str) else raw
    except ValueError:
        return None
    if not isinstance(entries, list):
        return None
    return any(isinstance(entry, Mapping) and entry.get("kind") == "step" and _has_text(entry.get("body_md"))
               for entry in entries)


def derive_workbench_signals(
    sessions: Iterable[Mapping[str, Any]],
    steps: Iterable[Mapping[str, Any]],
    assists: Iterable[Mapping[str, Any]],
    *,
    attempts: Mapping[str, Mapping[str, Any]],
    item_targets: Mapping[str, tuple[str, str]],
    diagnostics: dict[str, Any] | None = None,
) -> tuple[SignalRow, ...]:
    """The two workbench sources as zero-mass signal rows (pure).

    ``sessions`` are ``workbench_sessions`` rows (``id``, ``practice_item_id``,
    ``attempt_id``); ``steps`` ``workbench_steps`` rows; ``assists`` the
    workbench's ``help_assists`` rows (``id``, ``workbench_session_id``,
    ``assist_kind``, ``step_snapshot_json``, ``requested_at``). ``attempts``
    maps an attempt id to its ``learning_object_id``, ``subject`` and
    ``declared_stuck``; ``item_targets`` an item id to ``(lo, subject)``.
    """

    targets: dict[str, tuple[str, str]] = {}
    stuck_answer_sessions: set[str] = set()
    unmapped = 0
    for session in sessions:
        session_id = str(session["id"])
        attempt = attempts.get(str(session.get("attempt_id") or ""))
        if attempt is not None:
            targets[session_id] = (str(attempt["learning_object_id"]), str(attempt.get("subject") or "default"))
            if attempt.get("declared_stuck"):
                stuck_answer_sessions.add(session_id)
        elif session.get("practice_item_id") and str(session["practice_item_id"]) in item_targets:
            targets[session_id] = item_targets[str(session["practice_item_id"])]
        else:
            unmapped += 1
    signals: list[SignalRow] = []
    steps = sorted(steps, key=lambda s: (str(s["created_at"]), str(s["id"])))
    roots = _chain_roots(steps)
    first_stuck: dict[str, Mapping[str, Any]] = {}
    for step in steps:
        root = roots[str(step["id"])]
        if (root not in first_stuck and step.get("kind") == "stuck" and not step.get("deleted")
                and _has_text(step.get("body_md"))):
            first_stuck[root] = step
    for root, step in sorted(first_stuck.items(), key=lambda pair: (str(pair[1]["created_at"]), pair[0])):
        session_id = str(step["session_id"])
        target = targets.get(session_id)
        if target is None or session_id in stuck_answer_sessions:
            continue
        signals.append(SignalRow(
            signal_id=f"{STUCK_PREFIX}{root}", lo_id=target[0], observed_at=str(step["created_at"]),
            signal_type=STUCK_CONFUSION_SIGNAL, subject_id=target[1],
        ))
    early: dict[str, Mapping[str, Any]] = {}
    for assist in sorted(assists, key=lambda a: (str(a["requested_at"]), str(a["id"]))):
        session_id = str(assist.get("workbench_session_id") or "")
        if (not session_id or session_id in early or assist.get("assist_kind") not in HELP_ASSIST_KINDS
                or assist.get("step_snapshot_json") is None):
            continue
        if _snapshot_has_work(assist["step_snapshot_json"]) is False:
            early[session_id] = assist
    for session_id, assist in early.items():
        target = targets.get(session_id)
        if target is None:
            continue
        signals.append(SignalRow(
            signal_id=f"{HELP_PREFIX}{session_id}", lo_id=target[0], observed_at=str(assist["requested_at"]),
            signal_type=WORKBENCH_HELP_SIGNAL, subject_id=target[1], help_before_work=True,
        ))
    if diagnostics is not None:
        diagnostics.update(
            workbench_signal_version=WORKBENCH_SIGNAL_VERSION,
            workbench_stuck_rows=sum(s.signal_id.startswith(STUCK_PREFIX) for s in signals),
            workbench_help_before_work_rows=sum(s.signal_id.startswith(HELP_PREFIX) for s in signals),
            workbench_unmapped_sessions=unmapped,
        )
    return tuple(signals)


def _table_present(connection: Any, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone() is not None


def _rows(connection: Any, sql: str) -> list[dict[str, Any]]:
    cursor = connection.execute(sql)
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor]


def load_workbench_signals(
    connection: Any, vault: Any, *, diagnostics: dict[str, Any] | None = None,
) -> tuple[SignalRow, ...]:
    """The workbench rows for a live successor (empty otherwise). Read-only; never migrates."""

    if not workbench_field_signals_live(vault) or not _table_present(connection, "workbench_sessions"):
        return ()
    sessions = _rows(connection, "SELECT id, practice_item_id, attempt_id FROM workbench_sessions")
    if not sessions:
        if diagnostics is not None:
            derive_workbench_signals((), (), (), attempts={}, item_targets={}, diagnostics=diagnostics)
        return ()
    steps = _rows(
        connection,
        "SELECT id, session_id, kind, body_md, supersedes_id, deleted, created_at FROM workbench_steps",
    )
    assists = _rows(
        connection,
        "SELECT id, workbench_session_id, assist_kind, step_snapshot_json, requested_at FROM help_assists "
        "WHERE surface = 'workbench' AND workbench_session_id IS NOT NULL",
    ) if _table_present(connection, "help_assists") else []
    stuck_column = any(row[1] == "declared_stuck" for row in connection.execute("PRAGMA table_info(practice_attempts)"))
    attempt_ids = sorted({str(s["attempt_id"]) for s in sessions if s.get("attempt_id")})
    attempts: dict[str, dict[str, Any]] = {}
    for start in range(0, len(attempt_ids), 500):
        chunk = attempt_ids[start:start + 500]
        for row in connection.execute(
            f"SELECT id, learning_object_id, subject, {'declared_stuck' if stuck_column else '0'} "
            f"FROM practice_attempts WHERE id IN ({','.join('?' for _ in chunk)})", chunk,
        ):
            attempts[str(row[0])] = {"learning_object_id": row[1], "subject": row[2], "declared_stuck": bool(row[3])}
    item_targets: dict[str, tuple[str, str]] = {}
    items = getattr(vault, "practice_items", {}) or {}
    for session in sessions:
        item_id = session.get("practice_item_id")
        item = items.get(str(item_id)) if item_id else None
        if item is None or not getattr(item, "learning_object_id", None):
            continue
        subjects = vault.subjects_for_item(item) if hasattr(vault, "subjects_for_item") else []
        item_targets[str(item_id)] = (str(item.learning_object_id), str(subjects[0]) if subjects else "default")
    return derive_workbench_signals(
        sessions, steps, assists, attempts=attempts, item_targets=item_targets, diagnostics=diagnostics,
    )


__all__ = [
    "HELP_ASSIST_KINDS",
    "WORKBENCH_HELP_SIGNAL",
    "WORKBENCH_SIGNAL_VERSION",
    "derive_workbench_signals",
    "is_workbench_signal",
    "load_workbench_signals",
    "workbench_field_signals_live",
]
