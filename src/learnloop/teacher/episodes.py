"""Teacher TE2-log: item 5's logging for lessons (spec_teacher_v1 §11.3, §11.6, §11.7, §11.9; §20 row TE2-log).

Behind ``teacher.episode_log`` (default on at every algorithm version; no successor, as RO0's receipts):

* **The turn grows** (§8.2, §9): ``note_detour {node, hypothesis, repair, p}`` and ``write_plan`` nodes'
  ``p_held``, with the doctrine's versioned episode paragraph (``doctrine/episodes/v1.md``) and the prompt
  version :data:`PROMPT_SUFFIX`. A turn under the paragraph is a new doctrine version, so its forecasts are a new
  §12.2 forecaster family (:func:`doctrine_family`): the pool weight λ starts from its seeded prior for it.
* **The episode log** (``lesson_episodes``, §11.9): one row per detour (a ``note_detour``, or ``unlogged`` for a
  plan that inserts a node before the ones it had with no note in the same turn), opened with the prior belief and
  the origin ids, closed once with its minutes and outcome refs (the re-check on its node, or the lesson's close).
  Probes, gaps and goal LOs are TE2's actions: they write the same row (:func:`open_episode`) when TE2 builds them.
* **Minutes** (``lesson_activity_intervals``, §11.6): the lesson screen's own intervals through ``lesson.activity``
  (:func:`record_intervals`); :func:`minutes` sums the foreground ones (active) apart from ``closed − opened``
  (elapsed), never blending the two, and reports the elapsed time no interval covers and the seqs that never
  arrived as missing, never filled in.
* **Placement forecasts** (§11.3): a plan node's ``p_held`` is a ``lesson_node_held`` forecast receipt on the node's
  LO (:func:`node_held_receipts`).

Ids and numbers only in every row: a hypothesis's words stay in the turn's payload (``lesson_turn_payloads``),
after the output guards ran on them (``service._call_teacher``); the row keeps their count, a hash and the payload's
turn id. The model's ids a row copies are resolved first (Codex review F1): a note's node must name a plan node or a
brief LO; a node id, an ``lo_id`` and the note's node pass the same guards as a hypothesis and the identifier guard
against every key the vault records (:func:`logged_fields`, landing ruling R1), refused by location, never by text;
and an LO is a vault LO or none (:func:`outline_lo`). Every row, each placement forecast included, is written in its own savepoint of the action's
transaction: a refused row rolls back alone with a warning and never blocks a turn. Nothing serving, scheduling, certification or replay reads any of it.

Off: nothing here runs, the prompt, the turn schema, the forecaster family and the receipt are TE1's exactly.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Collection, Iterable, Mapping, Sequence
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from learnloop.clock import parse_utc
from learnloop.db.stores import lessons as store
from learnloop.ids import new_ulid
from learnloop.teacher.contracts import (
    TeacherTurnEpisodesV1,
    TeacherTurnV1,
    TeacherTurnVisualsEpisodesV1,
)

LOG = logging.getLogger(__name__)

#: The episode paragraph's version (recorded on every turn and forecast written under it).
EPISODES_VERSION = "teacher_episodes_v1"
#: Added to the teacher prompt's version while the paragraph is on.
PROMPT_SUFFIX = "+episodes-v1"
#: The rows' versions.
EPISODE_ROW_VERSION = "lesson_episode_v1"
INTERVAL_VERSION = "lesson_activity_interval_v1"
KINDS: tuple[str, ...] = ("probe", "detour", "gap", "goal_lo")
UNLOGGED = "unlogged"
_PARAGRAPH = Path(__file__).resolve().parent / "doctrine" / "episodes" / "v1.md"
#: A causal hypothesis still open on its LO (neither retired nor demoted).
_OPEN_HYPOTHESIS_STATUSES = ("candidate", "validated", "open_set")


def on(vault: Any) -> bool:
    """``teacher.episode_log`` (on without a teacher section)."""

    config = getattr(getattr(vault, "config", None), "teacher", None)
    return bool(getattr(config, "episode_log", True)) if config is not None else True


@lru_cache(maxsize=1)
def paragraph() -> str:
    return _PARAGRAPH.read_text(encoding="utf-8").strip() + "\n"


def instructions(text: str, episodes: bool) -> str:
    return text if not episodes else f"{text}\n{paragraph()}"


def prompt_version(base: str, episodes: bool) -> str:
    return f"{base}{PROMPT_SUFFIX}" if episodes else base


def turn_model(base: type[TeacherTurnV1], episodes: bool) -> type[TeacherTurnV1]:
    """The turn's strict schema: ``base`` (TE1's or the visuals turn) off, with ``note_detour`` and ``p_held`` on."""

    if not episodes:
        return base
    return TeacherTurnEpisodesV1 if base is TeacherTurnV1 else TeacherTurnVisualsEpisodesV1


def doctrine_family(doctrine: str, episodes: bool) -> str:
    """§12.2: a turn under the episode paragraph is a different forecaster (its own λ posterior)."""

    return f"{doctrine}+{EPISODES_VERSION}" if episodes else doctrine


def text_hash(texts: Sequence[str]) -> str:
    return hashlib.sha256("\n\x1f".join(texts).encode("utf-8")).hexdigest()


# =============================================================================
# The prior belief and the origin ids at an episode's opening
# =============================================================================


def has_table(connection: Any, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone() \
        is not None


_table = has_table


def prior_belief(repository: Any, brief: Mapping[str, Any], learning_object_id: str | None) -> dict[str, Any]:
    """At the opening: the brief's predicted success for the node's LO with its interval and its source (the
    active predictor, named as the brief names it; no new read of any item parameter), the LO's mastery mean and
    variance now, and the open misconceptions and causal hypotheses on it (counts, and ids apart)."""

    out: dict[str, Any] = {"predicted_success": None, "predicted_low": None, "predicted_high": None,
                           "predicted_source": None, "mastery_mean": None, "mastery_variance": None,
                           "open_misconceptions": None, "open_hypotheses": None, "open_ids": {}}
    if not learning_object_id:
        return out
    node = next((n for n in brief.get("nodes") or [] if n.get("id") == learning_object_id), None)
    prediction = (node or {}).get("prediction") or {}
    if prediction.get("p") is not None:
        interval = prediction.get("interval") or [None, None]
        out.update(predicted_success=float(prediction["p"]), predicted_source=str(prediction.get("source")),
                   predicted_low=None if interval[0] is None else float(interval[0]),
                   predicted_high=None if interval[1] is None else float(interval[1]))
    state = repository.mastery_state(learning_object_id)
    if state is not None:
        out.update(mastery_mean=float(state.logit_mean), mastery_variance=float(state.logit_variance))
    with repository.connection() as connection:
        misconceptions = [str(row[0]) for row in connection.execute(
            "SELECT id FROM misconceptions WHERE learning_object_id = ? AND status != 'resolved' ORDER BY created_at, id",
            (learning_object_id,)).fetchall()] if _table(connection, "misconceptions") else []
        hypotheses: list[str] = []
        if _table(connection, "causal_hypotheses"):
            marks = ", ".join("?" for _ in _OPEN_HYPOTHESIS_STATUSES)
            hypotheses = [str(row[0]) for row in connection.execute(
                f"SELECT id FROM causal_hypotheses h WHERE learning_object_id = ? AND status IN ({marks}) "
                "AND NOT EXISTS (SELECT 1 FROM causal_hypotheses s WHERE s.supersedes_id = h.id) "
                "ORDER BY created_at, id", (learning_object_id, *_OPEN_HYPOTHESIS_STATUSES)).fetchall()]
    out.update(open_misconceptions=len(misconceptions), open_hypotheses=len(hypotheses),
               open_ids={"misconceptions": misconceptions, "hypotheses": hypotheses})
    return out


def _local_day_start(at: datetime) -> datetime:
    local = at.astimezone()
    return local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(UTC)


def origin_ids(repository: Any, lesson: Mapping[str, Any], opened_at: str) -> dict[str, Any]:
    """The lesson's origin (``learner_pick``, or ``router`` with the accepted offer's decision id), that decision's
    ``router_objective_traces`` id when there is one, and every RO5 assignment (stop coin, randomized checks, open
    picks) in force for the lesson's day: made on the opening's local day, no later than the opening."""

    from learnloop.router_objective.assignments import EXPERIMENTS, TABLE

    origin = str(lesson.get("origin") or "learner_pick")
    decision = str(lesson["origin_ref"]) if origin == "router" and lesson.get("origin_ref") else None
    out: dict[str, Any] = {"origin": origin, "origin_decision_id": decision, "objective_trace_id": None,
                           "experiment_assignment_ids": []}
    at = parse_utc(opened_at)
    with repository.connection() as connection:
        if decision and _table(connection, "router_objective_traces"):
            row = connection.execute("SELECT id FROM router_objective_traces WHERE decision_id = ?",
                                     (decision,)).fetchone()
            out["objective_trace_id"] = None if row is None else str(row[0])
        if at is not None and _table(connection, TABLE):
            start = _local_day_start(at)
            marks = ", ".join("?" for _ in EXPERIMENTS)
            rows = connection.execute(
                f"SELECT id, created_at FROM {TABLE} WHERE experiment_id IN ({marks}) ORDER BY created_at, id",
                EXPERIMENTS).fetchall()
            for assignment_id, created in rows:
                made = parse_utc(str(created))
                if made is not None and start <= made <= at:
                    out["experiment_assignment_ids"].append(str(assignment_id))
    return out


# =============================================================================
# Writing rows, each in its own savepoint
# =============================================================================


def _guarded(repository: Any, what: str, write: Any) -> Any:
    """One row's write in its own savepoint of the caller's transaction: refused, it rolls back alone with a
    warning and the caller goes on (the turn is never blocked)."""

    try:
        with repository.atomic():
            connection = repository.connection()
            if not store.episode_tables_present(connection):
                return None
            return write(connection)
    except Exception:  # noqa: BLE001 - a log row never breaks its lesson
        LOG.warning("teacher episode log: %s not recorded", what, exc_info=True)
        return None


def open_episode(repository: Any, *, lesson: Mapping[str, Any], brief: Mapping[str, Any], kind: str,
                 opened_by: str, opened_at: str, node_id: str | None, learning_object_id: str | None,
                 hypotheses: Sequence[str] = (), hypothesis_payload_id: str | None = None,
                 repair_class: str | None = None, teacher_p: float | None = None,
                 teacher_forecast_receipt_id: str | None = None,
                 refs: Mapping[str, Any] | None = None) -> str | None:
    """Insert one episode at its opening (``kind`` in :data:`KINDS`); its id, or None (refused, or its opening
    action already has one). ``hypotheses``' words are hashed and counted, never stored here."""

    if kind not in KINDS:
        raise ValueError(f"unknown episode kind {kind!r}")
    episode_id = f"lep_{new_ulid().lower()}"
    texts = [str(text) for text in hypotheses if str(text).strip()]
    row = {
        "id": episode_id, "lesson_id": str(lesson["id"]), "kind": kind, "opened_by": opened_by, "node_id": node_id,
        "learning_object_id": learning_object_id, "opened_at": opened_at,
        "hypothesis_count": len(texts) if kind != "goal_lo" else None,
        "hypothesis_hash": text_hash(texts) if texts else None,
        "hypothesis_payload_id": hypothesis_payload_id if texts else None,
        "repair_class": repair_class, "teacher_p": None if teacher_p is None else float(teacher_p),
        "teacher_forecast_receipt_id": teacher_forecast_receipt_id,
        **prior_belief(repository, brief, learning_object_id),
        **origin_ids(repository, lesson, opened_at),
        **{key: value for key, value in dict(refs or {}).items()
           if key in ("generation_job_id", "generated_item_id", "gap_job_id", "created_lo_id")},
        "episode_version": EPISODE_ROW_VERSION, "created_at": opened_at,
    }
    written = _guarded(repository, f"the {kind} episode of {lesson['id']}",
                       lambda connection: store.insert_episode(connection, row))
    return episode_id if written else None


def close_episodes(repository: Any, lesson_id: str, *, closed_at: str, reason: str,
                   node_id: str | None = None, kind: str | None = None,
                   outcome: Mapping[str, Any] | None = None) -> list[str]:
    """Close every open episode of the lesson (on ``node_id`` and of ``kind`` when given) once, with its minutes
    from opening to ``closed_at`` and the outcome refs; the ids closed."""

    def write(connection: Any) -> list[str]:
        rows = [row for row in store.episodes(connection, lesson_id) if row["closed_at"] is None
                and (node_id is None or row["node_id"] == node_id) and (kind is None or row["kind"] == kind)]
        if not rows:
            return []
        spans = store.intervals(connection, lesson_id)
        closed = []
        for row in rows:
            counted = minutes(spans, str(row["opened_at"]), closed_at)
            fields = {"closed_at": closed_at, "close_reason": reason, "active_seconds": counted["active_seconds"],
                      "elapsed_seconds": counted["elapsed_seconds"],
                      "unreported_seconds": counted["unreported_seconds"],
                      "missing_intervals": counted["missing_intervals"], "minutes_source": counted["source"],
                      **{key: value for key, value in dict(outcome or {}).items()
                         if key in store.EPISODE_CLOSE_COLUMNS}}
            # Each row in its own savepoint too: one refused close leaves the others.
            if _guarded(repository, f"closing episode {row['id']}",
                        lambda c, row_id=str(row["id"]), f=fields: store.close_episode(c, row_id, f)):
                closed.append(str(row["id"]))
        return closed

    return _guarded(repository, f"closing the episodes of {lesson_id}", write) or []


def close_one(repository: Any, lesson_id: str, opened_by: str, *, closed_at: str, reason: str,
              outcome: Mapping[str, Any] | None = None) -> bool:
    """Close the one open episode its action opened (teacher TE2: a probe, a gap, an added topic), once, with its
    minutes and outcome refs (its own savepoint)."""

    def write(connection: Any) -> bool:
        row = next((row for row in store.episodes(connection, lesson_id) if str(row["opened_by"]) == opened_by
                    and row["closed_at"] is None), None)
        if row is None:
            return False
        counted = minutes(store.intervals(connection, lesson_id), str(row["opened_at"]), closed_at)
        fields = {"closed_at": closed_at, "close_reason": reason, "active_seconds": counted["active_seconds"],
                  "elapsed_seconds": counted["elapsed_seconds"], "unreported_seconds": counted["unreported_seconds"],
                  "missing_intervals": counted["missing_intervals"], "minutes_source": counted["source"],
                  **{key: value for key, value in dict(outcome or {}).items() if key in store.EPISODE_CLOSE_COLUMNS}}
        return store.close_episode(connection, str(row["id"]), fields)

    return bool(_guarded(repository, f"closing the episode of {opened_by}", write))


# =============================================================================
# Minutes: active and elapsed, never blended (§11.6)
# =============================================================================


def _overlap(start: datetime, end: datetime, lo: datetime, hi: datetime) -> tuple[datetime, datetime] | None:
    a, b = max(start, lo), min(end, hi)
    return (a, b) if b > a else None


def minutes(spans: Iterable[Mapping[str, Any]], opened_at: str, closed_at: str | None) -> dict[str, Any]:
    """Over ``[opened_at, closed_at]``: ``elapsed_seconds`` (the wall clock), ``active_seconds`` (the foreground
    intervals inside it), ``unreported_seconds`` (elapsed time no interval, foreground or not, covers: missing,
    never filled in), ``missing_intervals`` (seqs absent between a screen session's first and last received) and
    the count of intervals read. The two clocks are reported side by side and never combined."""

    rows = list(spans)
    opened, closed = parse_utc(opened_at), parse_utc(closed_at) if closed_at else None
    out: dict[str, Any] = {"elapsed_seconds": None, "active_seconds": None, "unreported_seconds": None,
                           "missing_intervals": _missing(rows), "intervals": 0,
                           "source": "lesson_activity" if rows else "no_intervals"}
    if opened is None or closed is None or closed < opened:
        return out
    elapsed = (closed - opened).total_seconds()
    pieces: list[tuple[datetime, datetime, bool]] = []
    for row in rows:
        start, end = parse_utc(str(row["started_at"])), parse_utc(str(row["ended_at"]))
        if start is None or end is None:
            continue
        clipped = _overlap(start, end, opened, closed)
        if clipped is not None:
            pieces.append((clipped[0], clipped[1], bool(row["foreground"])))
    active = _union_seconds([(a, b) for a, b, foreground in pieces if foreground])
    covered = _union_seconds([(a, b) for a, b, _foreground in pieces])
    out.update(elapsed_seconds=round(elapsed, 3), active_seconds=round(active, 3) if rows else None,
               unreported_seconds=round(max(elapsed - covered, 0.0), 3), intervals=len(pieces))
    return out


def _union_seconds(spans: Sequence[tuple[datetime, datetime]]) -> float:
    total, current = 0.0, None
    for start, end in sorted(spans):
        if current is None or start > current[1]:
            if current is not None:
                total += (current[1] - current[0]).total_seconds()
            current = [start, end]
        else:
            current[1] = max(current[1], end)
    if current is not None:
        total += (current[1] - current[0]).total_seconds()
    return total


def _missing(rows: Sequence[Mapping[str, Any]]) -> int:
    by_session: dict[str, set[int]] = {}
    for row in rows:
        by_session.setdefault(str(row["screen_session"]), set()).add(int(row["seq"]))
    return sum(max(seqs) - len(seqs) for seqs in by_session.values())


def lesson_minutes(repository: Any, lesson: Mapping[str, Any], *, closed_at: str | None = None) -> dict[str, Any]:
    """The lesson's minutes (§8.3 ``minutes``): from ``opened_at`` to its close (or ``closed_at``)."""

    with repository.connection() as connection:
        spans = store.intervals(connection, str(lesson["id"])) if store.episode_tables_present(connection) else []
    counted = minutes(spans, str(lesson["opened_at"]), closed_at or lesson.get("closed_at"))

    def as_minutes(value: Any) -> float | None:
        return None if value is None else round(float(value) / 60.0, 3)

    return {"active_minutes": as_minutes(counted["active_seconds"]),
            "elapsed_minutes": as_minutes(counted["elapsed_seconds"]),
            "unreported_minutes": as_minutes(counted["unreported_seconds"]),
            "missing_intervals": counted["missing_intervals"], "intervals": counted["intervals"],
            "source": counted["source"]}


# =============================================================================
# lesson.activity: the lesson screen's intervals
# =============================================================================


class ActivityRefused(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _stamp(value: Any, name: str) -> datetime:
    parsed = parse_utc(str(value)) if value else None
    if parsed is None:
        raise ActivityRefused("validation_error", f"{name} is not a time")
    return parsed


def record_intervals(vault: Any, repository: Any, *, lesson_id: str, intervals: Sequence[Mapping[str, Any]],
                     occurred_at: str | None, received_at: str) -> dict[str, Any]:
    """Append the screen's intervals (one row per (lesson, screen session, seq); a resend writes nothing), each in
    its own savepoint. Off, or before the tables exist, nothing is written. Never evidence, never a decision."""

    if not on(vault):
        return {"recorded": 0, "enabled": False}
    with repository.connection() as connection:
        if not store.episode_tables_present(connection):
            return {"recorded": 0, "enabled": False}
        if store.lesson(connection, lesson_id) is None:
            raise ActivityRefused("not_found", f"No lesson {lesson_id}.")
    reported = str(occurred_at or received_at)
    recorded = 0
    refused = 0
    with repository.atomic():
        for interval in intervals:
            try:
                start = _stamp(interval.get("started_at"), "started_at")
                end = _stamp(interval.get("ended_at"), "ended_at")
                seq = int(interval.get("seq") or 0)
                session = str(interval.get("screen_session") or "").strip()
                if end < start or seq < 1 or not session:
                    raise ActivityRefused("validation_error", "an interval needs a session, a seq and start <= end")
            except (ActivityRefused, TypeError, ValueError):
                refused += 1
                continue
            row = {"lesson_id": lesson_id, "screen_session": session[:80], "seq": seq,
                   "started_at": start.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                   "ended_at": end.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                   "seconds": round((end - start).total_seconds(), 3), "foreground": bool(interval.get("foreground")),
                   "occurred_at": reported, "received_at": received_at, "receipt_version": INTERVAL_VERSION}
            if _guarded(repository, f"an interval of {lesson_id}", lambda c, r=row: store.insert_interval(c, r)):
                recorded += 1
    return {"recorded": recorded, "refused": refused, "enabled": True}


# =============================================================================
# Placement forecasts: p_held on plan nodes (§11.3)
# =============================================================================


def node_held_receipts(state: Any, outline: Sequence[Mapping[str, Any]], *, learning_objects: Collection[str],
                       version: int, family: str, prompt: str, doctrine: str, now: str) -> list[Any]:
    """One ``lesson_node_held`` forecast per plan node with ``p_held`` on a vault LO (the node's ``lo_id``, or a node
    named by its LO; an ``lo_id`` that is no vault LO writes none): bound to the first qualifying cold outcome on the
    LO, as ``lesson_step_retained`` is."""

    from learnloop.scheduling.forecast_receipts import LESSON_COLD_OUTCOME, LESSON_NODE_HELD, ForecastReceipt

    receipts = []
    for node in outline:
        p = node.get("p_held")
        if p is None:
            continue
        lo = outline_lo(outline, str(node.get("id")), learning_objects)
        if not lo:
            continue
        key = f"{LESSON_NODE_HELD}:{state.lesson_id}:{version}:{node['id']}"
        receipts.append(ForecastReceipt(
            receipt_key=key, kind=LESSON_NODE_HELD, forecaster="teacher", forecaster_version=family,
            scope="lesson_node", decision_kind="lesson", binding_kind=LESSON_COLD_OUTCOME, event="cold_success",
            forecast={"emission_alphabet": ["success", "failure"],
                      "predicted_outcomes": {"success": round(float(p), 8), "failure": round(1.0 - float(p), 8)}},
            inputs={"lesson_id": state.lesson_id, "node_id": str(node["id"]), "plan_version": int(version),
                    "learning_object_id": str(lo), "family": family},
            parameters=[{"name": "p_held", "value": float(p), "provenance": "model"}],
            versions={"doctrine": doctrine, "prompt": prompt, "episodes": EPISODES_VERSION},
            inputs_as_of=now, p=float(p), columns={"decision_ref": state.lesson_id, "learning_object_id": str(lo)}))
    return receipts


# =============================================================================
# The model's ids, resolved before any row holds one (Codex review F1)
# =============================================================================


def turn_plans(turn_obj: Any) -> list[list[dict[str, Any]]]:
    """The outlines a turn's ``write_plan`` requests write, in request order."""

    return [[node.model_dump() for node in request.plan] for request in getattr(turn_obj, "requests", None) or []
            if request.action == "write_plan"]


def logged_fields(turn_obj: Any) -> list[tuple[str, str]]:
    """``(location, text)`` of every field a turn's model wrote that a log row, a receipt or a note's payload may
    copy: a note's ``hypothesis`` and ``node`` (episode turns only), each plan node's ``id`` and ``lo_id`` (every turn:
    they reach the lesson receipt's ``nodes``). Each passes the output
    guards and the vault-wide identifier guard before the turn is accepted (Codex review F1; landing ruling R1), and
    a refusal names it by its location (``requests[i].plan[j].id``), never by its text. An ``lo_id`` is still copied
    only when it is a vault LO (:func:`outline_lo`)."""

    out: list[tuple[str, str]] = []
    for index, request in enumerate(getattr(turn_obj, "requests", None) or []):
        at = f"requests[{index}]"
        if request.action == "note_detour":
            out.append((f"{at}.hypothesis", str(getattr(request, "hypothesis", None) or "")))
            out.append((f"{at}.node", str(request.node or "")))
        elif request.action == "write_plan":
            for position, node in enumerate(request.plan):
                out.append((f"{at}.plan[{position}].id", str(node.id or "")))
                out.append((f"{at}.plan[{position}].lo_id", str(getattr(node, "lo_id", None) or "")))
    return [(location, text) for location, text in out if text]


def node_known(state: Any, turn_obj: Any, node_id: str | None) -> bool:
    """A note's node names a node of the lesson's latest plan, of a plan its own turn writes (before or after the
    note), or a brief LO."""

    if not node_id:
        return False
    latest = state.plans[-1]["outline"] if state.plans else []
    ids = {str(node.get("id")) for outline in (latest, *turn_plans(turn_obj)) for node in outline}
    return node_id in ids or node_id in state.los


def outline_lo(outline: Sequence[Mapping[str, Any]], node_id: str, learning_objects: Collection[str]) -> str | None:
    """The node's LO in ``outline``: its ``lo_id`` when that is a vault LO, else the node's id when that is one; None
    otherwise (never a guess such as the goal's LO)."""

    for node in outline:
        if str(node.get("id")) == node_id:
            lo = node.get("lo_id")
            if lo and str(lo) in learning_objects:
                return str(lo)
            break
    return node_id if node_id in learning_objects else None


def node_lo(learning_objects: Collection[str], state: Any, turn_obj: Any, node_id: str) -> str | None:
    """A note's node's LO: from the newest plan holding the node (a plan its own turn writes first), else the node
    as an LO; :func:`outline_lo`'s rule."""

    latest = state.plans[-1]["outline"] if state.plans else []
    for outline in (*reversed(turn_plans(turn_obj)), latest):
        if any(str(node.get("id")) == node_id for node in outline):
            return outline_lo(outline, node_id, learning_objects)
    return node_id if node_id in learning_objects else None


def inserted_nodes(previous: Sequence[Mapping[str, Any]] | None, outline: Sequence[Mapping[str, Any]]) -> list[str]:
    """Nodes a revised plan inserts before a node the previous plan had (a foundation stepped back to), in order;
    none for a first plan or for nodes only appended after them."""

    if not previous:
        return []
    before = {str(node.get("id")) for node in previous}
    out: list[str] = []
    for index, node in enumerate(outline):
        node_id = str(node.get("id"))
        if node_id in before:
            continue
        if any(str(later.get("id")) in before for later in outline[index + 1:]):
            out.append(node_id)
    return out


def receipt_episodes(repository: Any, lesson_id: str) -> dict[str, list[str]]:
    """§8.3 ``episodes``: the lesson's episode ids by kind."""

    with repository.connection() as connection:
        rows = store.episodes(connection, lesson_id) if store.episode_tables_present(connection) else []
    out: dict[str, list[str]] = {kind: [] for kind in KINDS}
    for row in rows:
        out.setdefault(str(row["kind"]), []).append(str(row["id"]))
    return out


__all__ = [
    "ActivityRefused",
    "EPISODES_VERSION",
    "EPISODE_ROW_VERSION",
    "INTERVAL_VERSION",
    "KINDS",
    "PROMPT_SUFFIX",
    "UNLOGGED",
    "close_episodes",
    "doctrine_family",
    "has_table",
    "inserted_nodes",
    "instructions",
    "lesson_minutes",
    "logged_fields",
    "minutes",
    "node_held_receipts",
    "node_known",
    "node_lo",
    "on",
    "open_episode",
    "origin_ids",
    "outline_lo",
    "paragraph",
    "prior_belief",
    "prompt_version",
    "receipt_episodes",
    "record_intervals",
    "text_hash",
    "turn_model",
    "turn_plans",
]
