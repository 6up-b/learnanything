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
  2026-10-12), so it is no signal. The row stands whatever the session's
  submit later says (review F2): a session submitted as a stuck answer
  (``declared_stuck``) keeps its step-time row, from the step's own time, so
  what blocked routing before the submit still blocks it after (a deleted
  stuck step leaves an empty stuck answer, which says nothing, and never
  erases what the step said). The stuck answer's own grader row
  (``stuck:<attempt>``) is the predecessor's and stays beside it unchanged;
  both are zero-mass and blocking is per LO, so nothing is counted twice.
* **Help before the first step.** A help request on the workbench (a hint,
  the bridge to the book, a worked example) whose logged step snapshot
  (``help_assists.step_snapshot_json``, the steps as they stood at the
  request) holds no ordinary step with text. One per session, at its first
  such request. As for the practice screen, only the logged snapshot counts:
  a row without one is not evidence of help before work. A snapshot entry
  that carries no kind and text (the worked example logs identity only:
  chain, step row id, number, hash) is read through the step row it names,
  which the append-only ledger never changes; an entry whose row cannot be
  found leaves the snapshot unknown, never "no work" (review F1).

**Never the record (F2).** Each row has no outcome, no mass and no attempt
link: no predictor observes it, no attempt's hint outcome or assistance is
capped by it and the report's question strata do not count it
(``signals.enrich_attempts``). It blocks fast-track
(:func:`signals.blocks_fast_track`: a stuck row by its type, an early-help
row by its flag), so the LO is taught first and never fast-tracked on early
answers alone; "I know this" still works. Abandoned sessions contribute only
through these two sources, never as a failure.

**Targets.** A submitted session's attempt gives the LO and subject (the rows
meet the attempt rows). An open or abandoned session gives the LO of the
assessment contract it froze when it opened on (or bound to) its item
(``workbench_sessions.assessment_contract_version_id``), never today's item:
an item later moved to another LO, or removed, leaves the signal on the LO
the learner was working on (review F3). Its subject is the one recorded with
that contract (``workbench_sessions.contract_subject_id``, migration 219: what
a submit then would have recorded), never today's label (re-review F3); a
session whose subject was never recorded (its contract frozen before 219) has
the explicit ``SUBJECT_UNRECORDED``, which no subject-aware check matches, and
is counted (``workbench_subject_unrecorded_sessions``). Live routing blocks
per LO only, so it still blocks there. A session without a readable contract
for its own item (not yet bound, its import pending or failed, or opened
before contracts were snapshotted) has no target and is counted as unmapped.

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
#: ``subject_id`` of an unsubmitted session's row whose subject was never
#: recorded with its contract (frozen before migration 219): missing
#: provenance, said as such, never today's label (re-review F3). Not a
#: subject id any vault can name, so no subject-aware check matches it.
SUBJECT_UNRECORDED = "workbench:subject-unrecorded"


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


def _chain_roots(steps: Iterable[Mapping[str, Any]], wanted: Iterable[str]) -> dict[str, str]:
    """The chain root of each ``wanted`` step row: an edit, tombstone or undo
    supersedes the head. Memoized with path compression, so a long autosaved
    history costs linear time in the rows walked (review F4); a cycle (never
    written by the ledger) stops at the first repeated row."""

    parent = {str(step["id"]): (str(step["supersedes_id"]) if step.get("supersedes_id") else None)
              for step in steps}
    roots: dict[str, str] = {}
    for step_id in wanted:
        path: list[str] = []
        on_path: set[str] = set()
        current = step_id
        while current not in roots and parent.get(current) and current not in on_path:
            path.append(current)
            on_path.add(current)
            current = parent[current]  # type: ignore[assignment]
        root = roots.get(current, current)
        for node in path:
            roots[node] = root
        roots.setdefault(current, root)
    return roots


def _snapshot_has_work(raw: Any, step_rows: Mapping[str, Mapping[str, Any]] | None = None) -> bool | None:
    """Whether a logged step snapshot holds an ordinary step with text.

    An entry with its own ``kind`` and ``body_md`` (a hint's or a check's
    snapshot) is read as logged. An identity-only entry (the worked example's:
    ``chain_id``, ``step_id``, ``number``, ``hash``) is read through the
    immutable step row its ``step_id`` names in ``step_rows``. True as soon as
    one entry is work; None (unknown, never "no work") when the snapshot is
    unreadable or an entry that is not work could not be read (review F1)."""

    try:
        entries = json.loads(raw) if isinstance(raw, str) else raw
    except ValueError:
        return None
    if not isinstance(entries, list):
        return None
    unknown = False
    for entry in entries:
        if not isinstance(entry, Mapping):
            unknown = True
            continue
        if "kind" in entry and "body_md" in entry:
            kind, body = entry.get("kind"), entry.get("body_md")
        else:
            row = (step_rows or {}).get(str(entry.get("step_id") or ""))
            if row is None:
                unknown = True
                continue
            kind, body = row.get("kind"), row.get("body_md")
        if kind == "step" and _has_text(body):
            return True
    return None if unknown else False


def derive_workbench_signals(
    sessions: Iterable[Mapping[str, Any]],
    steps: Iterable[Mapping[str, Any]],
    assists: Iterable[Mapping[str, Any]],
    *,
    attempts: Mapping[str, Mapping[str, Any]],
    contract_targets: Mapping[str, str],
    diagnostics: dict[str, Any] | None = None,
) -> tuple[SignalRow, ...]:
    """The two workbench sources as zero-mass signal rows (pure).

    ``sessions`` are ``workbench_sessions`` rows (``id``, ``practice_item_id``,
    ``attempt_id``, ``assessment_contract_version_id``, ``contract_subject_id``); ``steps``
    ``workbench_steps`` rows; ``assists`` the workbench's ``help_assists``
    rows (``id``, ``workbench_session_id``, ``assist_kind``,
    ``step_snapshot_json``, ``requested_at``). ``attempts`` maps an attempt id
    to its ``learning_object_id`` and ``subject``; ``contract_targets`` a
    contract version id to the LO frozen in that contract (only contracts
    snapshotted for the session's own item).
    """

    targets: dict[str, tuple[str, str]] = {}
    unmapped = 0
    unrecorded: set[str] = set()
    for session in sessions:
        session_id = str(session["id"])
        attempt = attempts.get(str(session.get("attempt_id") or ""))
        contract = str(session.get("assessment_contract_version_id") or "")
        if attempt is not None:
            targets[session_id] = (str(attempt["learning_object_id"]), str(attempt.get("subject") or "default"))
        elif contract and contract in contract_targets:
            subject = str(session.get("contract_subject_id") or "")
            if not subject:
                unrecorded.add(session_id)
            targets[session_id] = (str(contract_targets[contract]), subject or SUBJECT_UNRECORDED)
        else:
            unmapped += 1
    signals: list[SignalRow] = []
    steps = sorted(steps, key=lambda s: (str(s["created_at"]), str(s["id"])))
    step_rows = {str(step["id"]): step for step in steps}
    # Only the chains a stuck step with text is on are resolved (review F4).
    stuck_steps = [step for step in steps if step.get("kind") == "stuck" and not step.get("deleted")
                   and _has_text(step.get("body_md"))]
    roots = _chain_roots(steps, (str(step["id"]) for step in stuck_steps))
    first_stuck: dict[str, Mapping[str, Any]] = {}
    for step in stuck_steps:
        first_stuck.setdefault(roots[str(step["id"])], step)
    for root, step in sorted(first_stuck.items(), key=lambda pair: (str(pair[1]["created_at"]), pair[0])):
        session_id = str(step["session_id"])
        target = targets.get(session_id)
        if target is None:
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
        if _snapshot_has_work(assist["step_snapshot_json"], step_rows) is False:
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
            workbench_subject_unrecorded_sessions=len(unrecorded),
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
    # The successor runs on a migrated vault; a database without 219's column
    # (never written by the app) reads every subject as unrecorded.
    subject_column = "contract_subject_id" if any(
        row[1] == "contract_subject_id" for row in connection.execute("PRAGMA table_info(workbench_sessions)")
    ) else "NULL AS contract_subject_id"
    sessions = _rows(
        connection,
        "SELECT id, practice_item_id, attempt_id, assessment_contract_version_id, "
        f"{subject_column} FROM workbench_sessions",
    )
    if not sessions:
        if diagnostics is not None:
            derive_workbench_signals((), (), (), attempts={}, contract_targets={}, diagnostics=diagnostics)
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
    attempt_ids = sorted({str(s["attempt_id"]) for s in sessions if s.get("attempt_id")})
    attempts: dict[str, dict[str, Any]] = {}
    for start in range(0, len(attempt_ids), 500):
        chunk = attempt_ids[start:start + 500]
        for row in connection.execute(
            "SELECT id, learning_object_id, subject "
            f"FROM practice_attempts WHERE id IN ({','.join('?' for _ in chunk)})", chunk,
        ):
            attempts[str(row[0])] = {"learning_object_id": row[1], "subject": row[2]}
    return derive_workbench_signals(
        sessions, steps, assists, attempts=attempts,
        contract_targets=_contract_targets(connection, sessions, attempts), diagnostics=diagnostics,
    )


def _contract_targets(
    connection: Any, sessions: Iterable[Mapping[str, Any]], attempts: Mapping[str, Any],
) -> dict[str, str]:
    """The LO per contract version an unsubmitted session froze (review F3).

    The contract's own ``learning_object_id``, read only from a contract
    snapshotted for the session's item; nothing here reads today's vault (the
    subject is the one recorded with the contract, re-review F3)."""

    wanted: dict[str, str] = {}
    for session in sessions:
        contract = session.get("assessment_contract_version_id")
        if contract and session.get("practice_item_id") and str(session.get("attempt_id") or "") not in attempts:
            wanted[str(contract)] = str(session["practice_item_id"])
    if not wanted or not _table_present(connection, "assessment_contract_versions"):
        return {}
    ids = sorted(wanted)
    targets: dict[str, str] = {}
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        for version_id, item_id, raw in connection.execute(
            "SELECT id, practice_item_id, contract_json FROM assessment_contract_versions "
            f"WHERE id IN ({','.join('?' for _ in chunk)})", chunk,
        ):
            try:
                contract = json.loads(raw) if isinstance(raw, str) else None
            except ValueError:
                contract = None
            lo = contract.get("learning_object_id") if isinstance(contract, Mapping) else None
            if str(item_id) != wanted[str(version_id)] or not lo:
                continue
            targets[str(version_id)] = str(lo)
    return targets


__all__ = [
    "HELP_ASSIST_KINDS",
    "SUBJECT_UNRECORDED",
    "WORKBENCH_HELP_SIGNAL",
    "WORKBENCH_SIGNAL_VERSION",
    "derive_workbench_signals",
    "is_workbench_signal",
    "load_workbench_signals",
    "workbench_field_signals_live",
]
