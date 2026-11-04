"""RO0 rows 9 and 13 (spec_router_objective_v1 §4): what the router believed at one decision.

Belief tables hold current values only, so this is the only record of the state a decision saw:

* per candidate item: FSRS S, D, R and due; its predicted minutes and their source;
* per candidate LO: mastery mean and variance, adaptive difficulty's ``p̄`` and ``P_band``, open factors and the
  hypothesis posteriors the ledgers hold;
* ``ad_state_hash``, the goals, contract versions and dates in force, the model and config versions;
* session and day active minutes, pending reports, the stop on offer and not taken, the VOI verdicts in force.

Like the prefilter receipt (:mod:`learnloop.data_capture.prefilter`), it is built before the decision's transaction
opens (:func:`prepare`: a slow read never holds the write lock) and linked inside it (:func:`record`), so it commits
with the decision. Ids and numbers only, never a statement or an answer. Nothing serving, scheduling or certification
reads it. Never raises: off, below the migration or refused, nothing is written and the decision stands.

A misconception's posterior is a stateless recompute from persisted attempts (``diagnosis.misconceptions``), so it is
re-derivable as of the decision's time and is not copied here; the row names which ones are open.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
from typing import Any

from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.data_capture.gates import objective_receipts_on
from learnloop.data_capture.prefilter import canonical, code_revision, content_hash
from learnloop.db.stores import router_objective as store
from learnloop.ids import new_ulid
from learnloop.params.fitted_params import resolve_fsrs_weights

logger = logging.getLogger(__name__)

RECEIPT_VERSION = "decision_state_v1"
#: Decimal places of a stored number: receipt size only, never a decision.
_ROUND_DIGITS = 5
#: Numbers in an AD field or a VOI verdict are copied as they are (they are already rounded where they were made).
AD_NOT_READ = "not_read_on_this_path"
AD_UNAVAILABLE = "unavailable"
#: The fields of a value-of-information verdict kept here; its whole forecast is in A1's ``upstream`` part.
_VOI_FIELDS: tuple[str, ...] = ("site", "learning_object_id", "decision", "reason", "subject_ref", "chosen_ref",
                                "recommended_ref", "admitted", "forecast_version", "calibration_label")
_ACTIVE_BASIS = "attempt_latency_plus_reader_active_seconds"

AdFields = Callable[[Sequence[str]], Mapping[str, Any]]


@dataclass(frozen=True)
class Material:
    """One decision's state, canonical, ready to link when the decision commits."""

    content: str
    session_id: str | None
    ad_state_hash: str | None
    session_active_minutes: float | None
    day_active_minutes: float | None
    pending_reports: int | None
    candidate_items: int
    candidate_los: int


def _round(value: Any) -> Any:
    return round(float(value), _ROUND_DIGITS) if isinstance(value, (int, float)) and not isinstance(value, bool) else value


def _marks(values: Sequence[Any]) -> str:
    return ",".join("?" for _ in values)


def candidate_ids(vault: Any, candidates: Iterable[Mapping[str, Any]], *, extra_items: Iterable[str] = (),
                  extra_los: Iterable[str] = ()) -> tuple[list[str], list[str]]:
    """The items and LOs a decision's candidates name, in any of the shapes the ledger holds."""

    items: dict[str, None] = dict.fromkeys(str(item) for item in extra_items if item)
    los: dict[str, None] = dict.fromkeys(str(lo) for lo in extra_los if lo)
    for entry in candidates:
        for item in entry.get("item_ids") or ():
            if item:
                items.setdefault(str(item))
        if entry.get("kind") == "item" and entry.get("ref"):
            items.setdefault(str(entry["ref"]))
        for lo in entry.get("learning_object_ids") or ():
            if lo:
                los.setdefault(str(lo))
        if entry.get("learning_object_id"):
            los.setdefault(str(entry["learning_object_id"]))
    known = getattr(vault, "practice_items", {})
    for item in items:
        found = known.get(item)
        if found is not None and getattr(found, "learning_object_id", None):
            los.setdefault(str(found.learning_object_id))
    return list(items), list(los)


def _item_rows(connection: Any, items: Sequence[str], now: datetime, weights: Any, forgetting_curve: Callable[..., float],
               minutes: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {item: {**dict(minutes.get(item) or {})} for item in items}
    if not items:
        return out
    for row in connection.execute(
            f"SELECT practice_item_id, difficulty, stability, due_at, last_attempt_at FROM practice_item_state "
            f"WHERE practice_item_id IN ({_marks(items)})", list(items)):
        last = parse_utc(row["last_attempt_at"]) if row["last_attempt_at"] else None
        retrievability = None
        if row["stability"] is not None and last is not None:
            elapsed = max((now - last).total_seconds() / 86400.0, 0.0)
            retrievability = forgetting_curve(float(row["stability"]), elapsed, weights)
        out[str(row["practice_item_id"])].update({
            "s": _round(row["stability"]), "d": _round(row["difficulty"]), "r": _round(retrievability),
            "due": row["due_at"], "last": row["last_attempt_at"],
        })
    return out


def _lo_rows(connection: Any, los: Sequence[str], ad: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {lo: {} for lo in los}
    if not los:
        return out
    marks = _marks(los)
    for row in connection.execute(
            f"SELECT learning_object_id, logit_mean, logit_variance, evidence_count FROM learning_object_mastery "
            f"WHERE learning_object_id IN ({marks})", list(los)):
        out[str(row[0])].update({"logit_mean": _round(row[1]), "logit_variance": _round(row[2]), "evidence": int(row[3])})
    for row in connection.execute(
            f"SELECT a.learning_object_id, f.id FROM unresolved_cause_factors f JOIN practice_attempts a ON a.id = f.attempt_id "
            f"WHERE f.status = 'open' AND a.learning_object_id IN ({marks}) ORDER BY f.created_at, f.id", list(los)):
        out[str(row[0])].setdefault("open_factors", []).append(str(row[1]))
    for row in connection.execute(
            f"SELECT h.learning_object_id, h.id, h.status FROM causal_hypotheses h WHERE h.cause_scope = 'learner_state' "
            f"AND h.status IN ('candidate', 'validated') AND h.learning_object_id IN ({marks}) AND h.version = ("
            f"SELECT MAX(head.version) FROM causal_hypotheses head WHERE head.episode_key = h.episode_key) "
            f"ORDER BY h.created_at, h.id", list(los)):
        out[str(row[0])].setdefault("hypotheses", []).append({"id": str(row[1]), "status": str(row[2])})
    for row in connection.execute(
            f"SELECT learning_object_id, id, status, severity FROM misconceptions "
            f"WHERE status != 'resolved' AND learning_object_id IN ({marks}) ORDER BY created_at, id", list(los)):
        out[str(row[0])].setdefault("misconceptions", []).append(
            {"id": str(row[1]), "status": str(row[2]), "severity": _round(row[3])})
    # The stored posterior of each open episode: its newest observation's, else what its newest presentation selected on.
    for row in connection.execute(
            f"SELECT e.learning_object_id, e.id, e.status, e.hypothesis_set_id, ("
            f"SELECT o.posterior_after_json FROM probe_presentations p JOIN practice_attempts a ON a.probe_presentation_id = p.id "
            f"JOIN probe_observations o ON o.attempt_id = a.id WHERE p.probe_episode_id = e.id "
            f"ORDER BY o.created_at DESC, o.id DESC LIMIT 1), ("
            f"SELECT p.posterior_at_selection_json FROM probe_presentations p WHERE p.probe_episode_id = e.id "
            f"ORDER BY p.created_at DESC, p.id DESC LIMIT 1) "
            f"FROM probe_episodes e WHERE e.status IN ('pending_items', 'in_progress') AND e.learning_object_id IN ({marks}) "
            f"ORDER BY e.created_at, e.id", list(los)):
        posterior = row[4] or row[5]
        out[str(row[0])].setdefault("episodes", []).append({
            "id": str(row[1]), "status": str(row[2]), "hypothesis_set_id": row[3],
            "posterior": {str(key): _round(value) for key, value in json.loads(posterior).items()} if posterior else None,
        })
    by_lo = ad.get("los") or {}
    for lo in los:
        if lo in by_lo:
            out[lo]["ad"] = dict(by_lo[lo])
    return out


def _active_minutes(connection: Any, session_id: str | None, day_start: str) -> tuple[float | None, float]:
    """Session and day active minutes: attempts' latency and Reader visits' active seconds, two clocks apart from
    elapsed time. A visit still open has reported nothing yet."""

    day_attempts = connection.execute(
        "SELECT COALESCE(SUM(latency_seconds), 0) FROM practice_attempts WHERE created_at >= ?", (day_start,)).fetchone()[0]
    day_reading = connection.execute(
        "SELECT COALESCE(SUM(json_extract(payload_json, '$.active_seconds')), 0) FROM interaction_events "
        "WHERE kind = 'reader_view_closed' AND created_at >= ?", (day_start,)).fetchone()[0]
    day = (float(day_attempts or 0) + float(day_reading or 0)) / 60.0
    if not session_id:
        return None, day
    session = connection.execute("SELECT started_at FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if session is None:
        return None, day
    attempts = connection.execute(
        "SELECT COALESCE(SUM(latency_seconds), 0) FROM practice_attempts WHERE created_at >= ? AND session_id = ?",
        (session[0], session_id)).fetchone()[0]
    reading = connection.execute(
        "SELECT COALESCE(SUM(json_extract(payload_json, '$.active_seconds')), 0) FROM interaction_events "
        "WHERE kind = 'reader_view_closed' AND created_at >= ?", (session[0],)).fetchone()[0]
    return (float(attempts or 0) + float(reading or 0)) / 60.0, day


def _pending_reports(connection: Any, now_iso: str) -> dict[str, int | None]:
    """What the learner or the router is still waiting to hear: each count None where the table is absent."""

    def count(table: str, sql: str, *parameters: Any) -> int | None:
        if not store.table_present(connection, table):
            return None
        return int(connection.execute(sql, parameters).fetchone()[0])

    return {
        "diagnosis_jobs": count("post_attempt_jobs",
                                "SELECT COUNT(*) FROM post_attempt_jobs WHERE kind = 'diagnose' AND state IN ('queued', 'leased')"),
        "followup_workflows": count("followup_workflows",
                                    "SELECT COUNT(*) FROM followup_workflows WHERE state IN ('pending', 'ready', 'waiting')"),
        "clarifications": count("grading_clarifications",
                                "SELECT COUNT(*) FROM grading_clarifications c WHERE c.expires_at > ? AND NOT EXISTS ("
                                "SELECT 1 FROM grading_clarification_responses r WHERE r.clarification_id = c.id)", now_iso),
    }


def _goals(vault: Any) -> list[dict[str, Any]]:
    goals = getattr(vault, "goals", None) or ()
    values = goals.values() if isinstance(goals, Mapping) else goals
    return [
        {"id": str(goal.id), "status": goal.status, "due": goal.due_at, "contract": goal.confirmed_contract_head_id,
         "contract_hash": goal.confirmed_contract_hash}
        for goal in values if goal.status == "active"
    ]


_config_seen: tuple[Any, str] | None = None


def _config_hash(config: Any) -> str:
    """The config's hash, once per loaded config: a large dump, read at every decision."""

    global _config_seen
    if _config_seen is None or _config_seen[0] is not config:
        _config_seen = (config, content_hash(canonical(config.model_dump(mode="json"))))
    return _config_seen[1]


def _voi(decisions: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [{key: row[key] for key in _VOI_FIELDS if row.get(key) is not None} for row in decisions]


def _pick_verdict(verdicts: Sequence[Mapping[str, Any]], pick: tuple[str | None, str | None] | None) -> dict[str, Any] | None:
    """For a pick, the verdict in force on what was picked: on the item, else on its LO."""

    if pick is None:
        return None
    item, lo = pick
    for row in verdicts:
        if item and item in (row.get("subject_ref"), row.get("chosen_ref"), row.get("recommended_ref")):
            return dict(row)
    for row in verdicts:
        if lo and row.get("learning_object_id") == lo:
            return dict(row)
    return {"verdict": "none_in_force"}


def prepare(vault: Any, repository: Any, *, candidates: Iterable[Mapping[str, Any]], session_id: str | None,
            forgetting_curve: Callable[..., float], item_minutes: Mapping[str, Mapping[str, Any]] | None = None, block_minutes: Mapping[str, Any] | None = None,
            stop: Mapping[str, Any] | None = None, voi: Iterable[Mapping[str, Any]] = (),
            pick: tuple[str | None, str | None] | None = None, extra_items: Iterable[str] = (), extra_los: Iterable[str] = (),
            ad_fields: AdFields | Mapping[str, Any] | None = None, versions: Mapping[str, Any] | None = None,
            omitted: Mapping[str, Any] | None = None, clock: Clock | None = None) -> Material | None:
    """Read one decision's state. None off, below the migration, or when it cannot be read: it never touches the decision.

    ``ad_fields``: the LOs' AD fields, or the reader of them (it runs before anything is written); None says the path
    read none. ``item_minutes``: each candidate item's predicted minutes and source. ``forgetting_curve``:
    ``scheduling.fsrs``'s, handed in because scheduling is itself a caller (this package stays below it)."""

    config = getattr(vault, "config", None)
    if not objective_receipts_on(config):
        return None
    try:
        candidate_rows = list(candidates)
        items, los = candidate_ids(vault, candidate_rows, extra_items=extra_items, extra_los=extra_los)
        if callable(ad_fields):
            try:
                ad = dict(ad_fields(los))
            except Exception:  # noqa: BLE001 - AD unavailable: said, and everything else still read
                logger.warning("router objective: adaptive difficulty's fields were not read", exc_info=True)
                ad = {"status": AD_UNAVAILABLE}
        else:
            ad = dict(ad_fields) if ad_fields is not None else {"status": AD_NOT_READ}
        now = (clock or SystemClock()).now()
        now_iso = utc_now_iso(clock)
        day_start = now.astimezone().replace(hour=0, minute=0, second=0, microsecond=0).astimezone(now.tzinfo)
        weights = resolve_fsrs_weights(repository)
        with repository.connection() as connection:
            if not store.table_present(connection, store.DECISION_STATE):
                return None
            session_minutes, day_minutes = _active_minutes(connection, session_id, day_start.strftime("%Y-%m-%dT%H:%M:%SZ"))
            pending = _pending_reports(connection, now_iso)
            item_rows = _item_rows(connection, items, now, weights, forgetting_curve, item_minutes or {})
            lo_rows = _lo_rows(connection, los, ad)
        verdicts = _voi(voi)
        state: dict[str, Any] = {
            "version": RECEIPT_VERSION,
            "items": item_rows,
            "los": lo_rows,
            "ad": {key: value for key, value in ad.items() if key != "los"},
            "goals": _goals(vault),
            "versions": {
                "algorithm": str(config.algorithms.algorithm_version), "config": _config_hash(config),
                "code": code_revision(), "fsrs_weights": content_hash(canonical(list(weights))), **dict(versions or {}),
            },
            "active_minutes": {"session": _round(session_minutes), "day": _round(day_minutes), "basis": _ACTIVE_BASIS},
            "pending_reports": pending,
            **({"block_minutes": {str(ref): _round(value) for ref, value in block_minutes.items()}} if block_minutes else {}),
            **({"omitted": dict(omitted)} if omitted else {}),
            **({"stop": dict(stop)} if stop else {}),
            **({"voi": verdicts} if verdicts else {}),
            **({"pick_voi": _pick_verdict(verdicts, pick)} if pick is not None else {}),
        }
        total = sum(value for value in pending.values() if value is not None)
        return Material(content=canonical(state), session_id=session_id, ad_state_hash=ad.get("state_hash"),
                        session_active_minutes=_round(session_minutes), day_active_minutes=_round(day_minutes),
                        pending_reports=total, candidate_items=len(items), candidate_los=len(los))
    except Exception:  # noqa: BLE001 - a receipt never blocks a plan
        logger.warning("router objective: a decision's state was not read", exc_info=True)
        return None


def record(connection: Any, *, decision_id: str, decision_kind: str, material: Material | None, config: Any, at: str) -> bool:
    """Link ``material`` into a committed decision, on the caller's transaction. Refused, it rolls back alone."""

    if material is None or not objective_receipts_on(config):
        return False
    try:
        if not store.table_present(connection, store.DECISION_STATE):
            return False
        return store.insert_decision_state(connection, {
            "id": new_ulid(), "decision_id": decision_id, "decision_kind": decision_kind,
            "receipt_version": RECEIPT_VERSION, "algorithm_version": str(config.algorithms.algorithm_version),
            "session_id": material.session_id, "ad_state_hash": material.ad_state_hash,
            "session_active_minutes": material.session_active_minutes, "day_active_minutes": material.day_active_minutes,
            "pending_reports": material.pending_reports, "candidate_items": material.candidate_items,
            "candidate_los": material.candidate_los, "created_at": at,
        }, material.content)
    except Exception:  # noqa: BLE001 - a receipt never blocks a plan
        logger.warning("router objective: the state of decision %s was not written", decision_id, exc_info=True)
        return False


__all__ = ["AD_NOT_READ", "AD_UNAVAILABLE", "AdFields", "Material", "RECEIPT_VERSION", "candidate_ids", "prepare", "record"]
