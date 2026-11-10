"""Why x and not y: the decision record, the trace id, and the one read (ADR-017).

A decision-producing function returns a :class:`DecisionRecord`; the imperative
shell writes it with :func:`write`. The record sits at meaningful boundaries
(a plan block chosen, a model answer discarded, an offer withdrawn, an
exclusion), points to the rich domain row where one exists, and is the row
where none does (failures, exclusions, refusals). ``learnloop why`` reads it
back with :func:`read`.

Three rules make it safe to write from anywhere:

* **A record never changes a decision.** :func:`write` never raises: a record
  it cannot write (a prose value, an unknown status, a storage error, a vault
  below migration 253) logs a warning with the trace id and is dropped. It
  writes inside a savepoint, so a failed insert leaves the caller's
  transaction exactly as it was.
* **A record holds no prose.** Its fields are ids, numbers and code constants
  (:func:`check_no_prose`); learner text, item text, prompts and model output
  stay in their own tables (``model_call_receipts`` holds the payloads).
* **Nothing replays it.** ``decision_records`` is a RECEIPT that no rebuild,
  replay or upgrade path imports or names (``tests/test_provenance.py``).

The trace id names one learner-visible action and its background work. It is
born by the entry points (the sidecar per RPC, the phone host per request, the
MCP server per tool call, the CLI per command) with :func:`trace_scope` and
carried by a ``ContextVar``, so threads started in a copied context inherit it.

This module is a leaf: it imports only the primitives (``learnloop.ids``).
"""

from __future__ import annotations

import json
import logging
import math
import re
import sqlite3
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any

from learnloop import ids

LOG = logging.getLogger(__name__)

TABLE = "decision_records"

#: The statuses a record may carry (the migration's CHECK holds the same list).
STATUSES = frozenset({
    "chosen", "fallback", "excluded", "withdrawn", "timeout", "discarded", "failed", "refused", "deferred",
})

#: Subject kinds ``why <kind>:<id>`` looks up. A writer may name another kind;
#: only these are read as a ``kind:id`` target.
SUBJECT_KINDS = frozenset({"attempt", "item", "block", "offer", "figure", "job", "presentation", "decision"})

#: Alternatives kept per record; the rest are counted per losing rule in
#: ``facts["alternatives_overflow"]``.
MAX_ALTERNATIVES = 50

# A code constant: an id, a rule name, a version, a model id, an ISO time. No
# whitespace, so a sentence (learner or item text, a prompt, an error message)
# cannot pass.
_TOKEN = re.compile(r"[A-Za-z0-9_.:/@+#=\-]{1,160}")

_COLUMNS = (
    "id", "trace_id", "parent_id", "kind", "status", "subject_kind", "subject_id", "chosen_ref", "decided_by",
    "rule", "alternatives_json", "facts_json", "versions_json", "detail_table", "detail_id", "error_type",
    "error_where", "created_at",
)

_TRACE: ContextVar[str | None] = ContextVar("learnloop_trace_id", default=None)


@dataclass(frozen=True)
class DecisionRecord:
    """One decision at a meaningful boundary: what won, what lost and why, as of then.

    ``id``, ``trace_id`` and ``created_at`` are filled at write time when left
    ``None`` (a new ULID, the current trace, the wall clock).
    """

    kind: str
    status: str
    subject_kind: str | None = None
    subject_id: str | None = None
    chosen_ref: str | None = None
    decided_by: str | None = None
    rule: str | None = None
    alternatives: Sequence[Mapping[str, Any]] = ()
    facts: Mapping[str, Any] = field(default_factory=dict)
    versions: Mapping[str, Any] = field(default_factory=dict)
    detail_table: str | None = None
    detail_id: str | None = None
    error_type: str | None = None
    error_where: str | None = None
    parent_id: str | None = None
    trace_id: str | None = None
    id: str | None = None
    created_at: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "trace_id": self.trace_id, "parent_id": self.parent_id, "kind": self.kind,
            "status": self.status, "subject_kind": self.subject_kind, "subject_id": self.subject_id,
            "chosen_ref": self.chosen_ref, "decided_by": self.decided_by, "rule": self.rule,
            "alternatives": [dict(item) for item in self.alternatives], "facts": dict(self.facts),
            "versions": dict(self.versions), "detail_table": self.detail_table, "detail_id": self.detail_id,
            "error_type": self.error_type, "error_where": self.error_where, "created_at": self.created_at,
        }


# -- the trace -----------------------------------------------------------------------------------------------


def current_trace() -> str | None:
    """The trace this code runs under, or ``None`` outside every entry point."""

    return _TRACE.get()


def new_trace_id() -> str:
    return ids.new_ulid()


@contextmanager
def trace_scope(trace_id: str | None = None) -> Iterator[str]:
    """Run the block under ``trace_id``, or under a new trace when it is ``None``.

    An entry point births one per learner-visible action; a worker continuing
    known work passes that work's trace. The previous trace comes back on exit,
    so a long-lived thread never keeps an action's trace after it ends.
    """

    value = trace_id or new_trace_id()
    token = _TRACE.set(value)
    try:
        yield value
    finally:
        _TRACE.reset(token)


# -- writing -------------------------------------------------------------------------------------------------


def where(exc: BaseException) -> str | None:
    """``module:function:line`` of the frame that raised ``exc``: the record's ``error_where``.

    The message is never recorded (a traceback can quote what the code read);
    it goes to the log at DEBUG with the trace id.
    """

    tb = exc.__traceback__
    if tb is None:
        return None
    while tb.tb_next is not None:
        tb = tb.tb_next
    frame = tb.tb_frame
    module = frame.f_globals.get("__name__", "?")
    return f"{module}:{frame.f_code.co_name}:{tb.tb_lineno}"


def is_code(value: Any) -> bool:
    """Whether ``value`` is a string :func:`write` keeps as it is: an id, a rule name, a version (no whitespace)."""

    return isinstance(value, str) and _TOKEN.fullmatch(value) is not None


def cap_alternatives(
    alternatives: Sequence[Mapping[str, Any]], *, limit: int = MAX_ALTERNATIVES,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """The first ``limit`` alternatives, and how many more lost by each rule."""

    kept = [dict(item) for item in alternatives[:limit]]
    overflow: dict[str, int] = {}
    for item in alternatives[limit:]:
        rule = str(item.get("lost_by") or "unspecified")
        overflow[rule] = overflow.get(rule, 0) + 1
    return kept, overflow


def check_no_prose(record: DecisionRecord) -> list[str]:
    """Paths of the record's values that are not an id, a number or a code constant (empty when clean)."""

    problems: list[str] = []

    def visit(value: Any, path: str) -> None:
        if value is None or isinstance(value, bool):
            return
        if isinstance(value, (int, float)):
            if isinstance(value, float) and not math.isfinite(value):
                problems.append(path)
            return
        if isinstance(value, str):
            if not _TOKEN.fullmatch(value):
                problems.append(path)
            return
        if isinstance(value, Mapping):
            for key, item in value.items():
                if not isinstance(key, str) or not _TOKEN.fullmatch(key):
                    problems.append(f"{path}.<key>")
                else:
                    visit(item, f"{path}.{key}")
            return
        if isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                visit(item, f"{path}[{index}]")
            return
        problems.append(path)

    for name in ("kind", "status", "subject_kind", "subject_id", "chosen_ref", "decided_by", "rule",
                 "detail_table", "detail_id", "error_type", "error_where", "parent_id", "trace_id", "id",
                 "created_at"):
        visit(getattr(record, name), name)
    visit(list(record.alternatives), "alternatives")
    visit(dict(record.facts), "facts")
    visit(dict(record.versions), "versions")
    return problems


def _completed(record: DecisionRecord) -> DecisionRecord:
    alternatives, overflow = cap_alternatives(record.alternatives)
    facts = dict(record.facts)
    if overflow:
        facts["alternatives_overflow"] = overflow
    return replace(
        record,
        id=record.id or ids.new_ulid(),
        trace_id=record.trace_id or current_trace() or new_trace_id(),
        created_at=record.created_at or datetime.now(timezone.utc).isoformat(),
        alternatives=tuple(alternatives),
        facts=facts,
    )


def write(connection: Any, record: DecisionRecord) -> str | None:
    """Insert ``record`` on the caller's connection; its id, or ``None`` when it was not written.

    Never raises: a record that fails a check or a write logs a warning with
    its trace id and is dropped, because a record must never change the
    decision it describes. The insert runs in a savepoint, which joins the
    caller's transaction when there is one and is its own short transaction
    otherwise; a failed insert is rolled back to the savepoint alone.
    """

    trace = record.trace_id or current_trace()
    try:
        completed = _completed(record)
        trace = completed.trace_id
        if completed.status not in STATUSES:
            raise ValueError(f"status {completed.status!r} is not one of {sorted(STATUSES)}")
        problems = check_no_prose(completed)
        if problems:
            raise ValueError(f"not an id, number or code: {', '.join(problems[:5])}")
        row = (
            completed.id, completed.trace_id, completed.parent_id, completed.kind, completed.status,
            completed.subject_kind, completed.subject_id, completed.chosen_ref, completed.decided_by,
            completed.rule, json.dumps(list(completed.alternatives), sort_keys=True),
            json.dumps(dict(completed.facts), sort_keys=True), json.dumps(dict(completed.versions), sort_keys=True),
            completed.detail_table, completed.detail_id, completed.error_type, completed.error_where,
            completed.created_at,
        )
    except Exception as exc:  # noqa: BLE001 - a record never changes the decision it describes
        LOG.warning("decision record %r not written (trace %s): %s: %s", record.kind, trace,
                    type(exc).__name__, exc)
        return None
    try:
        connection.execute("SAVEPOINT decision_record")
    except Exception as exc:  # noqa: BLE001 - a closed or read-only connection: the decision stands
        LOG.warning("decision record %r not written (trace %s): %s", record.kind, trace, type(exc).__name__)
        return None
    try:
        connection.execute(
            f"INSERT INTO {TABLE} ({', '.join(_COLUMNS)}) VALUES ({', '.join('?' for _ in _COLUMNS)})", row,
        )
    except Exception as exc:  # noqa: BLE001 - a record never changes the decision it describes
        try:
            connection.execute("ROLLBACK TO SAVEPOINT decision_record")
            connection.execute("RELEASE SAVEPOINT decision_record")
        except Exception:  # noqa: BLE001 - the warning below is all that is left to do
            pass
        LOG.warning("decision record %r not written (trace %s): %s", record.kind, trace, type(exc).__name__)
        return None
    try:
        connection.execute("RELEASE SAVEPOINT decision_record")
    except Exception as exc:  # noqa: BLE001 - the savepoint's own commit failed: the decision stands
        LOG.warning("decision record %r not written (trace %s): %s", record.kind, trace, type(exc).__name__)
        return None
    return completed.id


# -- reading -------------------------------------------------------------------------------------------------


def _record(row: Sequence[Any]) -> DecisionRecord:
    values = dict(zip(_COLUMNS, row, strict=True))
    return DecisionRecord(
        kind=values["kind"], status=values["status"], subject_kind=values["subject_kind"],
        subject_id=values["subject_id"], chosen_ref=values["chosen_ref"], decided_by=values["decided_by"],
        rule=values["rule"], alternatives=tuple(json.loads(values["alternatives_json"] or "[]")),
        facts=json.loads(values["facts_json"] or "{}"), versions=json.loads(values["versions_json"] or "{}"),
        detail_table=values["detail_table"], detail_id=values["detail_id"], error_type=values["error_type"],
        error_where=values["error_where"], parent_id=values["parent_id"], trace_id=values["trace_id"],
        id=values["id"], created_at=values["created_at"],
    )


def read(connection: Any, target: str = "latest", *, kind: str | None = None,
         limit: int = 500) -> list[DecisionRecord]:
    """The records ``target`` names, oldest first; empty when none (or the vault is below migration 253).

    ``target`` is ``latest`` (the newest record's trace, of ``kind`` when
    given), ``<subject_kind>:<id>`` (the records about that subject), a record
    id (that record's trace) or a trace id. ``kind`` also filters the result.
    """

    select = f"SELECT {', '.join(_COLUMNS)} FROM {TABLE}"
    order = f" ORDER BY created_at, id LIMIT {int(limit)}"
    kind_clause = " AND kind = ?" if kind else ""
    kind_args: tuple[Any, ...] = (kind,) if kind else ()
    try:
        prefix, _, rest = target.partition(":")
        if target == "latest":
            row = connection.execute(
                f"SELECT trace_id FROM {TABLE} WHERE 1=1{kind_clause} ORDER BY created_at DESC, id DESC LIMIT 1",
                kind_args,
            ).fetchone()
            if row is None:
                return []
            trace = row[0]
            rows = connection.execute(f"{select} WHERE trace_id = ?{kind_clause}{order}", (trace, *kind_args))
        elif rest and prefix in SUBJECT_KINDS:
            rows = connection.execute(
                f"{select} WHERE subject_kind = ? AND subject_id = ?{kind_clause}{order}", (prefix, rest, *kind_args),
            )
        else:
            row = connection.execute(f"SELECT trace_id FROM {TABLE} WHERE id = ?", (target,)).fetchone()
            trace = row[0] if row is not None else target
            rows = connection.execute(f"{select} WHERE trace_id = ?{kind_clause}{order}", (trace, *kind_args))
        return [_record(tuple(item)) for item in rows.fetchall()]
    except sqlite3.OperationalError as exc:
        if "no such table" in str(exc):
            return []
        raise
