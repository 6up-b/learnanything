"""Slip or gap (SG; ``docs/specs/spec_slip_vs_gap_v1.md``): what the router knows about a miss's cause, per topic.

**SG1, the sensor** (:func:`sensor`). For a candidate topic with a missed cold check since its last lesson (instruct
hand-off §7d's definition, the same rows ``lesson_suggestion.build_candidates`` reads: a cold attempt type, unprimed,
no hints, graded, not fully right, not classified as a lesson probe answered after its lesson showed text, after the
topic's last lesson ended), read through THE availability predicate at the decision:

* **which miss**: the latest such miss. No older miss is read past it (instruct hand-off's third review, M1): if its
  diagnosis is still being written, or failed, the status says so;
* **the cause probabilities** ``p_gap``, ``p_slip``, ``p_unknown`` over the diagnosis's causal classes
  (``learner_state``, ``transient_execution``, ``unknown``; ``diagnosis.split.validation.CAUSAL_CAUSE_SCOPES``): a
  probe episode's posterior on that miss's factor where one is on record (each hypothesis's mass by its class, the
  open-set mass ``unknown``), else the diagnosis's own verbalized prior weights, normalized per error event as
  ``diagnosis.forecast_receipts`` normalizes them (a cause with no weight takes the mean of the others) and averaged
  over the attempt's events;
* **the learner's marks**: hypotheses the learner marked ``my_gap``, recorded beside the probabilities as their own
  statement (their keys and classes, never their text), and never folded in (instruct hand-off IH4's line between
  statements and evidence);
* **the surprise** as stored on the attempt (``attempt_surprise``: Bayesian and predictive surprise, direction);
* **the status**: ``diagnosed``, ``pending``, ``failed``, ``none`` (no diagnosis was queued or written) or
  ``not_applicable`` (one ran and found nothing to explain, or named no cause), so an absent diagnosis is visible
  and never read as a slip.

Computed from the ledger, with no model call. Nothing here writes.

**SG2, the value's inputs** (:func:`value_inputs`). The surprise calibrates ``p_gap``: ``logit p̃_gap = logit p_gap +
β·s``, ``s`` the miss's Bayesian surprise standardized over the learner's own cold misses on record, ``β`` a learned
coefficient with a seeded prior centred at 0 (:data:`BETA_PRIOR`), fitted (:func:`beta_fit`) on whether the topic's next
cold check after a diagnosed miss came out not fully right, when nothing else happened on the topic in between (no
lesson opened, no other attempt). The remaining mass keeps the diagnosis's split between slip and unknown. At ``β = 0``
the sensor is the diagnosis's alone. The fit reads the diagnosis's prior weights only, never a probe posterior (the next
check is often one of that episode's own probes, so the label would be inside the input). Those follow-ups are
self-selected, which the record says (:data:`SELF_SELECTED`); nothing here enters the mix weight's scoring.

The lesson's and the repair's effect slopes split by cause (:func:`cause_slopes`): ``γ_gap`` and ``γ_slip``, each with
a seeded prior (``γ_gap``'s is ``γ``'s; ``γ_slip``'s is centred at 0 with ``γ``'s variance: the owner's default of Nov 9,
spec §6), learned from the first later cold outcome after a lesson whose offer froze this sensor (a one-step Laplace
update per lesson, in time order). No threshold anywhere: no probability cut-off, no surprise cut-off, no rule for
slips (a static test reads this module for comparisons against fixed numbers).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import json
import math
from typing import Any

VERSION = "miss_cause_v1"
CALIBRATION_VERSION = "miss_cause_calibration_v1"
SLOPES_VERSION = "miss_cause_slopes_v1"

#: The diagnosis's causal classes (``diagnosis.split.validation.CAUSAL_CAUSE_SCOPES``): a gap, a slip, or unknown.
GAP = "learner_state"
SLIP = "transient_execution"
UNKNOWN = "unknown"
CLASSES: tuple[str, ...] = (GAP, SLIP, UNKNOWN)
#: The words a class is named by on the card and in the report.
CLASS_WORDS = {GAP: "gap", SLIP: "slip", UNKNOWN: "unknown"}

#: The statuses (spec §3, SG1 item 1).
DIAGNOSED = "diagnosed"
PENDING = "pending"
FAILED = "failed"
NONE = "none"
NOT_APPLICABLE = "not_applicable"
STATUSES: tuple[str, ...] = (DIAGNOSED, PENDING, FAILED, NONE, NOT_APPLICABLE)

#: Where the probabilities came from.
BASIS_POSTERIOR = "probe_posterior"
BASIS_PRIOR = "diagnosis_prior_weights"

#: Instruct hand-off §7d's definition of a miss: a cold check that was not fully right (``correctness < 1.0``, the
#: predecessor's own definition, ``lesson_suggestion.missed_since``; a test pins the two equal). Not a threshold on
#: the miss's size: any partial credit is a miss.
FULLY_RIGHT = 1.0

#: ``β``'s seeded prior (mean, variance) on the standardized surprise: centred at 0 (no effect until data move it),
#: unit variance on a standardized covariate (the LP spec's "no information" width, as ``lesson_weight``'s
#: ``HEDGE_INTERCEPT_PRIOR``). A prior, not a threshold.
BETA_PRIOR: tuple[float, float] = (0.0, 1.0)
#: Newton's method on ``β``'s one-dimensional log posterior (concave: a logistic likelihood and a Gaussian prior):
#: iterations, numerical resolution only.
_NEWTON_STEPS = 50

SELF_SELECTED = ("self-selected: the next cold check after a miss is whatever the learner and the plan did next (often "
                 "the diagnosis's own follow-up), never a randomized check, so beta is a calibration of the "
                 "diagnosis against what happened next, not a causal effect; it never enters the mix weight's scoring")
OBSERVATIONAL = ("observational: later cold results by cause class describe what followed; they are not randomized "
                 "and say nothing causal about lessons")


def _table(connection: Any, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                              (name,)).fetchone() is not None


def _loads(raw: Any, default: Any) -> Any:
    if raw is None or raw == "":
        return default
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return default


def _logit(p: float) -> float:
    return math.log(p) - math.log1p(-p)


def _log_sigmoid(x: float) -> float:
    """``log σ(x)``, stable on both tails."""

    return -math.log1p(math.exp(-x)) if x >= 0 else x - math.log1p(math.exp(x))


def _sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    z = math.exp(x)
    return z / (1.0 + z)


# -- which miss -------------------------------------------------------------------------------------------------


def _cold_filter_sql() -> tuple[str, tuple[Any, ...]]:
    from learnloop.learner.lesson_weight import COLD_ATTEMPT_TYPES

    marks = ",".join("?" for _ in COLD_ATTEMPT_TYPES)
    return (f"a.attempt_type IN ({marks}) AND a.primed = 0 AND a.hints_used = 0 AND a.correctness IS NOT NULL",
            tuple(COLD_ATTEMPT_TYPES))


def _exposed(connection: Any) -> set[str]:
    from learnloop.causal_activity_policy import LESSON_PROBE_EXPOSED_SOURCE
    from learnloop.db.stores import router_suggestions as store

    return store.attempts_classified_by(connection, LESSON_PROBE_EXPOSED_SOURCE)


def _lessons_ended(connection: Any, now_iso: str) -> dict[str, str]:
    """Per LO, when its last lesson known at the decision ended (``router_suggestions.last_lesson_ended_by_learning_object``,
    bounded at the decision: a lesson opened after it is not there)."""

    out: dict[str, str] = {}
    if not _table(connection, "lessons"):
        return out
    # A close after the decision is not known at it: the lesson then counts as open, ending at its opening (Codex F4).
    for raw, ended in connection.execute(
            "SELECT learning_object_ids_json, CASE WHEN closed_at IS NOT NULL AND closed_at <= ? THEN closed_at "
            "ELSE opened_at END FROM lessons WHERE opened_at <= ?", (now_iso, now_iso)):
        for lo in _loads(raw, []) or []:
            if str(ended) > out.get(str(lo), ""):
                out[str(lo)] = str(ended)
    return out


def latest_misses(connection: Any, config: Any, learning_object_ids: Iterable[str], now_iso: str) -> dict[str, dict[str, Any]]:
    """Per topic, its latest missed cold check since its last lesson ended, known at ``now_iso`` (THE availability
    predicate); topics with none are absent."""

    from learnloop.router_objective_switches import attempt_time_sql

    ids = sorted({str(lo) for lo in learning_object_ids if lo})
    if not ids or not _table(connection, "practice_attempts"):
        return {}
    cold, params = _cold_filter_sql()
    known = attempt_time_sql(config, connection, alias="a")
    rows = connection.execute(
        f"SELECT a.id, a.learning_object_id, a.practice_item_id, a.attempt_type, a.correctness, a.created_at "
        f"FROM practice_attempts a WHERE a.learning_object_id IN ({','.join('?' for _ in ids)}) AND {cold} "
        f"AND a.correctness < ? AND a.created_at <= ? AND {known} <= ? ORDER BY a.created_at, a.id",
        (*ids, *params, FULLY_RIGHT, now_iso, now_iso)).fetchall()
    exposed = _exposed(connection) if rows else set()
    ended = _lessons_ended(connection, now_iso) if rows else {}
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        attempt_id, lo, item, kind, correctness, created = (str(row[0]), str(row[1]), row[2], str(row[3]),
                                                             float(row[4]), str(row[5]))
        if attempt_id in exposed:
            continue
        last = ended.get(lo)
        if last is not None and not created > last:
            continue
        out[lo] = {"attempt_id": attempt_id, "learning_object_id": lo, "practice_item_id": item,
                   "attempt_type": kind, "correctness": correctness, "at": created}
    return out


# -- the diagnosis ----------------------------------------------------------------------------------------------


def _pending(connection: Any, attempt_id: str) -> bool:
    if not _table(connection, "post_attempt_jobs"):
        return False
    for _state, payload in connection.execute(
            "SELECT state, payload_json FROM post_attempt_jobs WHERE attempt_id = ? AND kind = 'diagnose' "
            "AND state IN ('queued', 'leased')", (attempt_id,)):
        if (_loads(payload, {}) or {}).get("mode", "live") == "live":
            return True
    return False


def diagnosis_state(connection: Any, attempt_id: str, now_iso: str) -> tuple[str, dict[str, Any] | None]:
    """The miss's status and its live diagnosis in force (THE eligibility rule,
    ``DiagnosisStoreMixin._diagnosis_in_force``), both as known at ``now_iso``."""

    from learnloop.db.stores.diagnoses import DiagnosisStoreMixin

    if _pending(connection, attempt_id):
        return PENDING, None
    if not _table(connection, "attempt_diagnoses"):
        return NONE, None
    row = connection.execute(
        "SELECT id, status, error, blind_grade_record_id, proposal_json, created_at FROM attempt_diagnoses "
        "WHERE attempt_id = ? AND mode = 'live' AND created_at <= ? ORDER BY created_at DESC, id DESC LIMIT 1",
        (attempt_id, now_iso)).fetchone()
    if row is None:
        return NONE, None
    if row[1] == "skipped" and row[2] == "not_needed":
        return NOT_APPLICABLE, None
    current = None
    if _table(connection, "blind_grade_records"):
        found = connection.execute(
            "SELECT id FROM blind_grade_records WHERE attempt_id = ? AND created_at <= ? "
            "ORDER BY created_at DESC, id DESC LIMIT 1", (attempt_id, now_iso)).fetchone()
        current = str(found[0]) if found is not None else None
    if not DiagnosisStoreMixin._diagnosis_in_force(row[1], row[3], current):
        return FAILED, {"id": str(row[0]), "status": str(row[1])}
    return DIAGNOSED, {"id": str(row[0]), "status": str(row[1]), "proposal": _loads(row[4], {}) or {},
                       "created_at": str(row[5])}


def _class(scope: Any) -> str:
    text = str(scope or UNKNOWN)
    return text if text in CLASSES else UNKNOWN


def prior_weights(proposal: Mapping[str, Any]) -> tuple[dict[str, float], int] | None:
    """The diagnosis's normalized prior weights by causal class, averaged over its events (each event's candidate
    causes normalized as ``diagnosis.forecast_receipts`` does: a cause with no weight takes the mean of the others).
    None: no event names a cause."""

    totals = {name: 0.0 for name in CLASSES}
    events = 0
    for event in proposal.get("event_diagnoses") or ():
        if not isinstance(event, Mapping):
            continue
        causes = [cause for cause in event.get("candidate_causes") or () if isinstance(cause, Mapping)]
        if not causes:
            continue
        weights: list[float | None] = []
        for cause in causes:
            try:
                weights.append(max(float(cause["prior_weight"]), 0.0) if cause.get("prior_weight") is not None else None)
            except (TypeError, ValueError):
                weights.append(None)
        known = [w for w in weights if w is not None]
        fill = (sum(known) / len(known)) if known else 1.0
        resolved = [fill if w is None else w for w in weights]
        total = sum(resolved)
        if not total:
            resolved, total = [1.0] * len(causes), float(len(causes))
        for cause, weight in zip(causes, resolved):
            totals[_class(cause.get("cause_scope"))] += weight / total
        events += 1
    if not events:
        return None
    return {name: totals[name] / events for name in CLASSES}, events


def _factors(connection: Any, attempt_id: str) -> list[str]:
    if not _table(connection, "unresolved_cause_factors"):
        return []
    return [str(row[0]) for row in connection.execute(
        "SELECT id FROM unresolved_cause_factors WHERE attempt_id = ? ORDER BY created_at, id", (attempt_id,))]


def probe_posterior(connection: Any, attempt_id: str, now_iso: str) -> dict[str, Any] | None:
    """A probe episode's posterior on the miss's factor, by causal class, as known at ``now_iso``: the latest of the
    episode's completion posterior and its observations' posteriors. Each hypothesis's mass goes to its class; the
    open-set mass (and any key that names no causal hypothesis) to ``unknown``. None: no episode on the miss's factor
    has a posterior on record."""

    if not (_table(connection, "probe_episodes") and _table(connection, "causal_hypotheses")):
        return None
    origins = [f"causal_factor:{factor}" for factor in _factors(connection, attempt_id)]
    if not origins:
        return None
    found: tuple[str, str, str, Any] | None = None  # (at, episode, source, posterior)
    marks = ",".join("?" for _ in origins)
    for episode_id, completed_at, completion in connection.execute(
            f"SELECT id, completed_at, completion_posterior_json FROM probe_episodes WHERE origin IN ({marks}) "
            "AND created_at <= ? ORDER BY created_at, id", (*origins, now_iso)):
        posterior = _loads(completion, None)
        if isinstance(posterior, Mapping) and posterior and completed_at and str(completed_at) <= now_iso:
            if found is None or str(completed_at) > found[0]:
                found = (str(completed_at), str(episode_id), "completion", posterior)
        if _table(connection, "probe_observations") and _table(connection, "probe_presentations"):
            row = connection.execute(
                "SELECT o.created_at, o.posterior_after_json FROM probe_observations o "
                "JOIN practice_attempts a ON a.id = o.attempt_id "
                "JOIN probe_presentations p ON p.id = a.probe_presentation_id "
                "WHERE p.probe_episode_id = ? AND o.created_at <= ? ORDER BY o.created_at DESC, o.id DESC LIMIT 1",
                (episode_id, now_iso)).fetchone()
            if row is not None:
                observed = _loads(row[1], None)
                if isinstance(observed, Mapping) and observed and (found is None or str(row[0]) > found[0]):
                    found = (str(row[0]), str(episode_id), "observation", observed)
    if found is None:
        return None
    _at, episode_id, source, posterior = found
    keys = [str(key) for key in posterior]
    scopes = {str(row[0]): _class(row[1]) for row in connection.execute(
        f"SELECT id, cause_scope FROM causal_hypotheses WHERE id IN ({','.join('?' for _ in keys)})", keys)}
    totals = {name: 0.0 for name in CLASSES}
    for key, mass in posterior.items():
        try:
            value = max(float(mass), 0.0)
        except (TypeError, ValueError):
            continue
        totals[scopes.get(str(key), UNKNOWN)] += value
    total = sum(totals.values())
    if not total:
        return None
    return {"p": {name: totals[name] / total for name in CLASSES}, "episode_id": episode_id, "source": source,
            "at": found[0]}


def my_gap_marks(connection: Any, attempt_id: str, now_iso: str) -> list[dict[str, Any]]:
    """Hypotheses the learner marked ``my_gap`` on the miss (the latest mark per hypothesis counts), as known at
    ``now_iso``: their key and causal class, never their statement."""

    from learnloop.db.stores import hypothesis_marks as marks_store
    from learnloop.followup_serve import marks as opinion

    if not marks_store.present(connection):
        return []
    rows = [row for row in marks_store.marks_for_attempt(connection, attempt_id)
            if str(row.get("created_at") or "") <= now_iso]
    marked = {str(key): row for key, row in opinion.latest_marks(rows).items()
              if key is not None and row.get("mark") == opinion.MY_GAP}
    if not marked:
        return []
    out: list[dict[str, Any]] = []
    for key in sorted(marked):
        # The class of the version the learner marked (Codex F4), else the episode's latest version known then.
        scope = None
        version_id = marked[key].get("hypothesis_version_id")
        if _table(connection, "causal_hypotheses"):
            row = (connection.execute("SELECT cause_scope FROM causal_hypotheses WHERE id = ?", (version_id,)).fetchone()
                   if version_id else None)
            if row is None:
                row = connection.execute(
                    "SELECT cause_scope FROM causal_hypotheses WHERE episode_key = ? AND created_at <= ? "
                    "ORDER BY version DESC LIMIT 1", (key, now_iso)).fetchone()
            scope = row[0] if row is not None else None
        out.append({"hypothesis_key": key, "class": _class(scope)})
    return out


def stored_surprise(connection: Any, attempt_id: str, now_iso: str | None = None) -> dict[str, Any] | None:
    """The attempt's stored surprise, as written by ``now_iso`` (None: whatever is on record)."""

    if not _table(connection, "attempt_surprise"):
        return None
    row = connection.execute(
        "SELECT bayesian_surprise, predictive_surprise, surprise_direction FROM attempt_surprise WHERE attempt_id = ?"
        + (" AND created_at <= ?" if now_iso is not None else ""),
        (attempt_id, *((now_iso,) if now_iso is not None else ()))).fetchone()
    if row is None:
        return None
    return {"bayesian": None if row[0] is None else float(row[0]),
            "predictive": None if row[1] is None else float(row[1]),
            "direction": None if row[2] is None else str(row[2])}


def record_for(connection: Any, miss: Mapping[str, Any], now_iso: str) -> dict[str, Any]:
    """One topic's sensor, from its latest miss."""

    attempt_id = str(miss["attempt_id"])
    status, diagnosis = diagnosis_state(connection, attempt_id, now_iso)
    record: dict[str, Any] = {
        "version": VERSION, "status": status, "learning_object_id": miss["learning_object_id"],
        "attempt_id": attempt_id, "attempt_at": miss["at"], "attempt_type": miss["attempt_type"],
        "diagnosis_id": (diagnosis or {}).get("id"), "episode_id": None, "basis": None,
        "p_gap": None, "p_slip": None, "p_unknown": None, "events": 0,
        "surprise": stored_surprise(connection, attempt_id, now_iso),
        "learner_marked_my_gap": my_gap_marks(connection, attempt_id, now_iso),
    }
    if status != DIAGNOSED or diagnosis is None:
        return record
    weighted = prior_weights(diagnosis.get("proposal") or {})
    if weighted is None:
        record["status"] = NOT_APPLICABLE
        return record
    p, events = weighted
    record["events"] = events
    record["prior"] = {CLASS_WORDS[name]: p[name] for name in CLASSES}
    posterior = probe_posterior(connection, attempt_id, now_iso)
    if posterior is not None:
        p = posterior["p"]
        record.update(episode_id=posterior["episode_id"], basis=BASIS_POSTERIOR,
                      posterior_source=posterior["source"], posterior_at=posterior["at"])
    else:
        record["basis"] = BASIS_PRIOR
    total = sum(p.values())  # renormalized, so a rounded sum never puts a class above 1 (Codex F6)
    p = {name: p[name] / total for name in CLASSES}
    record.update(p_gap=p[GAP], p_slip=p[SLIP], p_unknown=p[UNKNOWN])
    return record


def sensor(connection: Any, config: Any, learning_object_ids: Iterable[str], now_iso: str) -> dict[str, dict[str, Any]]:
    """SG1: per candidate topic with a missed cold check since its last lesson, its record (module docstring)."""

    return {lo: record_for(connection, miss, now_iso)
            for lo, miss in sorted(latest_misses(connection, config, learning_object_ids, now_iso).items())}


def mark(records: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """What a prefetch boundary's identity names so a change in a sensor (a diagnosis landing, a probe answered)
    starts a new job. Excluded from the numeric policy's seed (``objective_chooser.numeric_seed``)."""

    return {lo: [record.get("status"), record.get("attempt_id"), record.get("diagnosis_id"), record.get("episode_id"),
                 record.get("posterior_at"), len(record.get("learner_marked_my_gap") or ())]
            for lo, record in sorted(records.items())}


def ledger_mark(connection: Any) -> list[Any]:
    """SG2 (Codex F1): what ``β``'s and the cause slopes' fits read beyond a new attempt (which the boundary's ``as_of``
    already names): the live diagnoses on record, the lessons' openings and closes, and the stored surprises, each as a
    count and the latest write. A diagnosis landing on any topic, or a lesson closing, starts a new job. Excluded from
    the numeric policy's seed like the rest of the sensor's mark."""

    out: list[Any] = []
    for table, column, where in (("attempt_diagnoses", "created_at", "WHERE mode = 'live'"),
                                 ("lessons", "coalesce(closed_at, opened_at)", ""),
                                 ("attempt_surprise", "created_at", "")):
        if _table(connection, table):
            row = connection.execute(f"SELECT count(*), max({column}) FROM {table} {where}").fetchone()
            out.append([table, int(row[0] or 0), row[1]])
    return out


# -- the surprise, standardized, and words ---------------------------------------------------------------------


def surprise_reference(connection: Any, config: Any, now_iso: str) -> list[float]:
    """The Bayesian surprise of every missed cold check on record at ``now_iso`` (any topic): the learner's own
    distribution a miss's surprise is standardized and ranked against."""

    from learnloop.router_objective_switches import attempt_time_sql

    if not (_table(connection, "attempt_surprise") and _table(connection, "practice_attempts")):
        return []
    cold, params = _cold_filter_sql()
    known = attempt_time_sql(config, connection, alias="a")
    return [float(row[0]) for row in connection.execute(
        f"SELECT s.bayesian_surprise FROM attempt_surprise s JOIN practice_attempts a ON a.id = s.attempt_id "
        f"WHERE s.bayesian_surprise IS NOT NULL AND {cold} AND a.correctness < ? AND a.created_at <= ? "
        f"AND {known} <= ?", (*params, FULLY_RIGHT, now_iso, now_iso))]


def moments(reference: Sequence[float]) -> tuple[float, float] | None:
    """The reference's mean and standard deviation, computed once per decision (Codex F8); None with no spread."""

    if not reference:
        return None
    mean = sum(reference) / len(reference)
    variance = sum((x - mean) ** 2 for x in reference) / len(reference)
    return (mean, math.sqrt(variance)) if variance else None


def standardized(value: float | None, reference: Sequence[float] | tuple[float, float] | None) -> float:
    """``(value − mean) / sd`` over ``reference`` (the values, or their :func:`moments`); 0 when there is no spread to
    standardize by (then ``β`` has nothing to act on) or no value."""

    if value is None or reference is None:
        return 0.0
    stats = reference if isinstance(reference, tuple) else moments(reference)
    if stats is None:
        return 0.0
    return (float(value) - stats[0]) / stats[1]


_DIRECTION_WORDS = {"negative": "worse than the mastery model expected",
                    "positive": "better than the mastery model expected",
                    "none": "no clear direction against what the mastery model expected"}


def surprise_words(surprise: Mapping[str, Any] | None, reference: Sequence[float]) -> str:
    """The surprise in words: its direction (the surprise module's own label) and where its Bayesian surprise ranks
    among the learner's recorded misses (a rank, never a cut-off)."""

    if not surprise or surprise.get("bayesian") is None:
        return "no surprise was recorded for this answer"
    direction = _DIRECTION_WORDS.get(str(surprise.get("direction") or "none"), _DIRECTION_WORDS["none"])
    value = float(surprise["bayesian"])
    if not reference:
        return f"{direction}; no other recorded misses to compare it with"
    below = sum(1 for x in reference if x < value)
    return (f"{direction}; it moved the model more than {below} of the {len(reference)} recorded missed checks did")


# -- SG2: beta, the calibration and the cause slopes -----------------------------------------------------------


def _between(connection: Any, config: Any, lo: str, after: str, before: str, after_id: str, before_id: str,
             now_iso: str) -> bool:
    """Whether anything happened on the topic strictly between two attempts: another attempt known at ``now_iso``
    (RO1's availability predicate, landing ruling R1: an attempt imported later is not there yet; the window
    itself stays by when the work happened), or a lesson opened."""

    from learnloop.router_objective_switches import attempt_time_sql

    known = attempt_time_sql(config, connection, alias="a")
    row = connection.execute(
        "SELECT 1 FROM practice_attempts a WHERE a.learning_object_id = ? "
        "AND ((a.created_at > ? OR (a.created_at = ? AND a.id > ?)) "
        f"AND (a.created_at < ? OR (a.created_at = ? AND a.id < ?))) AND {known} <= ? LIMIT 1",
        (lo, after, after, after_id, before, before, before_id, now_iso)).fetchone()
    if row is not None:
        return True
    if not _table(connection, "lessons"):
        return False
    for raw, opened in connection.execute("SELECT learning_object_ids_json, opened_at FROM lessons "
                                          "WHERE opened_at >= ? AND opened_at <= ?", (after, before)):
        if lo in {str(value) for value in _loads(raw, []) or []}:
            return True
    return False


def beta_rows(connection: Any, config: Any, now_iso: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """``β``'s data (module docstring): each diagnosed missed cold check known at ``now_iso`` whose topic's next
    attempt was a cold check, with nothing on the topic in between. Rows whose diagnosis puts all its mass on one
    side (``p_gap`` 0 or 1: ``logit p_gap`` infinite) carry no information about ``β`` and are counted apart."""

    from learnloop.router_objective_switches import attempt_time_sql

    counts = {"misses": 0, "undiagnosed": 0, "no_next_check": 0, "intervening": 0, "uninformative": 0,
              "no_surprise": 0, "rows": 0}
    if not _table(connection, "practice_attempts"):
        return [], counts
    cold, params = _cold_filter_sql()
    known = attempt_time_sql(config, connection, alias="a")
    misses = connection.execute(
        f"SELECT a.id, a.learning_object_id, a.created_at FROM practice_attempts a WHERE {cold} AND a.correctness < ? "
        f"AND a.created_at <= ? AND {known} <= ? ORDER BY a.created_at, a.id",
        (*params, FULLY_RIGHT, now_iso, now_iso)).fetchall()
    exposed = _exposed(connection) if misses else set()
    stats = moments(surprise_reference(connection, config, now_iso)) if misses else None
    rows: list[dict[str, Any]] = []
    for attempt_id, lo, created in misses:
        attempt_id, lo, created = str(attempt_id), str(lo), str(created)
        counts["misses"] += 1
        status, diagnosis = diagnosis_state(connection, attempt_id, now_iso)
        weighted = prior_weights((diagnosis or {}).get("proposal") or {}) if status == DIAGNOSED else None
        if weighted is None:
            counts["undiagnosed"] += 1
            continue
        nxt = connection.execute(
            f"SELECT a.id, a.created_at, a.correctness FROM practice_attempts a WHERE a.learning_object_id = ? "
            f"AND (a.created_at > ? OR (a.created_at = ? AND a.id > ?)) AND {cold} AND a.created_at <= ? "
            f"AND {known} <= ? ORDER BY a.created_at, a.id LIMIT 1",
            (lo, created, created, attempt_id, *params, now_iso, now_iso)).fetchone()
        if nxt is None or str(nxt[0]) in exposed:
            counts["no_next_check"] += 1
            continue
        if _between(connection, config, lo, created, str(nxt[1]), attempt_id, str(nxt[0]), now_iso):
            counts["intervening"] += 1
            continue
        p_gap = weighted[0][GAP]
        if not 0.0 < p_gap < 1.0:
            counts["uninformative"] += 1
            continue
        surprise = stored_surprise(connection, attempt_id, now_iso)
        if surprise is None or surprise.get("bayesian") is None:
            counts["no_surprise"] += 1
            continue
        rows.append({"attempt_id": attempt_id, "next_attempt_id": str(nxt[0]), "p_gap": p_gap,
                     "s": standardized(surprise["bayesian"], stats),
                     "missed_again": 1.0 if float(nxt[2]) < FULLY_RIGHT else 0.0})
    counts["rows"] = len(rows)
    return rows, counts


def beta_fit(connection: Any, config: Any, now_iso: str) -> dict[str, Any]:
    """``β``'s Laplace posterior: ``P(the next cold check is missed) = σ(logit p_gap + β·s)`` with the prior
    :data:`BETA_PRIOR`, by Newton's method (the log posterior is concave). With no rows, the prior."""

    rows, counts = beta_rows(connection, config, now_iso)
    return {**fit_beta(rows), "counts": counts}


def fit_beta(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """:func:`beta_fit`'s arithmetic on its rows (each ``p_gap`` in (0, 1), ``s``, ``missed_again``): pure."""

    m0, v0 = BETA_PRIOR
    offsets = [(_logit(row["p_gap"]), row["s"], row["missed_again"]) for row in rows]

    def log_posterior(b: float) -> float:
        total = -0.5 * (b - m0) ** 2 / v0
        for offset, s, y in offsets:
            eta = offset + b * s
            total += y * _log_sigmoid(eta) + (1.0 - y) * _log_sigmoid(-eta)  # log σ(η), log(1 − σ(η))
        return total

    def derivatives(b: float) -> tuple[float, float]:
        gradient, precision = -(b - m0) / v0, 1.0 / v0
        for offset, s, y in offsets:
            p = _sigmoid(offset + b * s)
            gradient += (y - p) * s
            precision += p * (1.0 - p) * s * s
        return gradient, precision

    # Damped Newton (Codex F5): the log posterior is concave, so a step is halved until it does not lower it; the
    # curvature reported is the one at the returned coefficient.
    beta, converged = m0, not offsets
    current = log_posterior(beta)
    for _ in range(_NEWTON_STEPS):
        if converged:
            break
        gradient, precision = derivatives(beta)
        step = gradient / precision
        for _halving in range(_NEWTON_STEPS):
            trial = beta + step
            value = log_posterior(trial)
            if value >= current:
                break
            step /= 2.0
        else:
            converged = True
            break
        converged = trial == beta
        beta, current = trial, value
    _gradient, precision = derivatives(beta)
    return {"version": CALIBRATION_VERSION, "mean": beta, "variance": 1.0 / precision, "prior": list(BETA_PRIOR),
            "n": len(rows), "label": SELF_SELECTED, "converged": converged,
            "model": "P(next cold check missed) = sigmoid(logit p_gap + beta * s), s the standardized Bayesian surprise"}


def calibrated(record: Mapping[str, Any], beta: float, s: float) -> tuple[float, float, float]:
    """``(p̃_gap, p̃_slip, p̃_unknown)``: ``logit p̃_gap = logit p_gap + β·s``, the rest of the mass split between slip
    and unknown in the diagnosis's own proportion. At ``β·s = 0`` exactly the record's probabilities."""

    p_gap, p_slip, p_unknown = float(record["p_gap"]), float(record["p_slip"]), float(record["p_unknown"])
    shift = beta * s
    rest = p_slip + p_unknown
    # No mass on one side (exactly, or by rounding of a sum: Codex F6) leaves nothing to move between them.
    if not shift or not rest or not 0.0 < p_gap < 1.0:
        return p_gap, p_slip, p_unknown
    calibrated_gap = _sigmoid(_logit(p_gap) + shift)
    scale = (1.0 - calibrated_gap) / rest
    return calibrated_gap, p_slip * scale, p_unknown * scale


def _offer_rows(connection: Any, config: Any, now_iso: str) -> list[dict[str, Any]]:
    """Lessons that ran from an offer whose card froze this sensor (diagnosed), closed by ``now_iso``, with the
    first qualifying cold outcome after their close (``lesson_weight.qualifying_outcomes``), counted only once that
    outcome is known at the decision (THE availability predicate; Codex F3): until then the lesson is unresolved."""

    from learnloop.learner.lesson_weight import qualifying_outcomes
    from learnloop.router_objective_switches import attempt_time_sql

    if not (_table(connection, "lessons") and _table(connection, "router_decisions")):
        return []
    known = attempt_time_sql(config, connection, alias="a")
    out: list[dict[str, Any]] = []
    for lesson_id, origin_ref, raw, closed in connection.execute(
            "SELECT id, origin_ref, learning_object_ids_json, closed_at FROM lessons WHERE origin = 'router' "
            "AND origin_ref IS NOT NULL AND closed_at IS NOT NULL AND closed_at <= ? ORDER BY closed_at, id",
            (now_iso,)):
        decision = connection.execute("SELECT detail_json FROM router_decisions WHERE id = ?", (origin_ref,)).fetchone()
        offer = (_loads(decision[0], {}) or {}).get("lesson_offer") if decision is not None else None
        if not isinstance(offer, Mapping):
            continue
        frozen = offer.get("miss_cause")
        lo = str(offer.get("learning_object_id") or "")
        if not isinstance(frozen, Mapping) or frozen.get("status") != DIAGNOSED or not lo:
            continue
        if lo not in {str(value) for value in _loads(raw, []) or []}:
            continue
        candidates = ((offer.get("card") or {}).get("candidates") or [{}])
        predicted = candidates[0].get("predicted_success") if candidates else None
        mass = (offer.get("mass") or {}).get("mean")
        if predicted is None or mass is None or not 0.0 < float(predicted) < 1.0:
            continue
        outcomes = [row for row in qualifying_outcomes(connection, [lo], str(closed), until=now_iso)]
        if not outcomes:
            continue
        seen = connection.execute(f"SELECT {known} FROM practice_attempts a WHERE a.id = ?",
                                  (outcomes[0]["id"],)).fetchone()
        if seen is None or str(seen[0]) > now_iso:
            continue
        out.append({"lesson_id": str(lesson_id), "learning_object_id": lo, "p_gap": float(frozen["p_gap"]),
                    "p_slip": float(frozen["p_slip"]), "p_unknown": float(frozen["p_unknown"]),
                    "predicted": float(predicted), "mass": float(mass), "y": float(outcomes[0]["correctness"]),
                    "outcome_attempt_id": str(outcomes[0]["id"])})
    return out


def cause_slopes(connection: Any, gamma: tuple[float, float], now_iso: str, config: Any = None) -> dict[str, Any]:
    """``(γ_gap, γ_slip)``'s posterior. The seeded prior: ``γ_gap ~ N(γ̄, v)``, ``γ_slip ~ N(0, v)``, independent, with
    ``(γ̄, v)`` the ``γ`` the decision reads (the owner's default, spec §6). Each lesson that ran from an offer that froze
    a diagnosed sensor, with its first later qualifying cold outcome ``y`` (the grade, continuous), is one Laplace step
    (an extended Kalman update) on ``y ~ σ(logit p₀ + m·(p_gap·γ_gap + p_slip·γ_slip + p_unknown·γ̄))``, ``p₀`` the
    mastery model's predicted success the offer froze and ``m`` its lesson-check mass, in time order. With none, the
    prior."""

    gm, gv = float(gamma[0]), max(float(gamma[1]), 0.0)
    mean = [gm, 0.0]
    cov = [[gv, 0.0], [0.0, gv]]
    prior = {"gap": [gm, gv], "slip": [0.0, gv]}
    rows = _offer_rows(connection, config, now_iso)
    for row in rows:
        m = row["mass"]
        eta = _logit(row["predicted"]) + m * (row["p_gap"] * mean[0] + row["p_slip"] * mean[1] + row["p_unknown"] * gm)
        p = _sigmoid(eta)
        r = p * (1.0 - p)
        h = [r * m * row["p_gap"], r * m * row["p_slip"]]
        ph = [cov[0][0] * h[0] + cov[0][1] * h[1], cov[1][0] * h[0] + cov[1][1] * h[1]]
        s = h[0] * ph[0] + h[1] * ph[1] + r
        if not s:
            continue
        k = [ph[0] / s, ph[1] / s]
        innovation = row["y"] - p
        mean = [mean[0] + k[0] * innovation, mean[1] + k[1] * innovation]
        cov = [[cov[i][j] - k[i] * ph[j] for j in (0, 1)] for i in (0, 1)]
    return {"version": SLOPES_VERSION, "gap": [mean[0], cov[0][0]], "slip": [mean[1], cov[1][1]],
            "cov": [list(cov[0]), list(cov[1])], "prior": prior, "n": len(rows),
            "lessons": [row["lesson_id"] for row in rows],
            "prior_basis": "gamma_gap's prior is gamma's; gamma_slip's is centred at 0 with gamma's variance (owner, Nov 9)"}


def value_inputs(connection: Any, config: Any, records: Mapping[str, Mapping[str, Any]], gamma: tuple[float, float],
                 now_iso: str) -> tuple[dict[str, tuple[float, float, float]], dict[str, Any]]:
    """SG2: each diagnosed topic's calibrated ``(p_gap, p_slip, p_unknown)`` and the record of how (``β``'s fit, each
    topic's ``s``, the cause slopes)."""

    diagnosed = {lo: record for lo, record in records.items() if record.get("status") == DIAGNOSED
                 and record.get("p_gap") is not None}
    if not diagnosed:
        # Nothing to split: no fit is run on the decision path (Codex F8) and every topic keeps gamma.
        return {}, {"topics": {}, "fitted": False,
                    "why": "no candidate topic's latest miss has a diagnosis in force"}
    beta = beta_fit(connection, config, now_iso)
    reference = surprise_reference(connection, config, now_iso)
    stats = moments(reference)
    weights: dict[str, tuple[float, float, float]] = {}
    topics: dict[str, Any] = {}
    for lo, record in sorted(diagnosed.items()):
        s = standardized((record.get("surprise") or {}).get("bayesian"), stats)
        weights[lo] = calibrated(record, float(beta["mean"]), s)
        topics[lo] = {"s": s, "calibrated": list(weights[lo]),
                      "diagnosis": [record["p_gap"], record["p_slip"], record["p_unknown"]]}
    slopes = cause_slopes(connection, gamma, now_iso, config)
    return weights, {"beta": beta, "slopes": slopes, "topics": topics, "fitted": True,
                     "surprise_reference": {"n": len(reference)}}


# -- the card ----------------------------------------------------------------------------------------------------


def card_entry(record: Mapping[str, Any], *, topic: str, days_before: float | None,
               reference: Sequence[float]) -> dict[str, Any]:
    """What the LLM policy's card shows of one topic's sensor: the cause class probabilities, the surprise in words
    and the status. Never a hypothesis's statement (it can restate the expected answer), never the answer."""

    status = str(record.get("status"))
    entry: dict[str, Any] = {"evidence_id": f"attempt:{record.get('attempt_id')}", "days_before": days_before,
                             "topic": topic, "diagnosis_status": status,
                             "surprise": surprise_words(record.get("surprise"), reference)}
    if status == DIAGNOSED:
        entry["cause"] = {CLASS_WORDS[GAP]: round(float(record["p_gap"]), 3),
                          CLASS_WORDS[SLIP]: round(float(record["p_slip"]), 3),
                          CLASS_WORDS[UNKNOWN]: round(float(record["p_unknown"]), 3)}
        entry["cause_from"] = ("the follow-up probes' posterior" if record.get("basis") == BASIS_POSTERIOR
                               else "the diagnosis's own weights")
    else:
        entry["cause"] = {PENDING: "the diagnosis is still being written", FAILED: "the diagnosis failed or no longer applies",
                          NONE: "no diagnosis was made for this answer",
                          NOT_APPLICABLE: "the diagnosis found no cause to name"}.get(status, status)
    marked = record.get("learner_marked_my_gap") or ()
    if marked:
        entry["learner_said_my_gap"] = sorted({CLASS_WORDS.get(str(m.get("class")), "unknown") for m in marked})
    return entry


CARD_NOTE = ("Each entry of history.miss_causes is the latest missed cold check on a topic the plan could offer a lesson "
             "or a repair for: whether the diagnosis reads it as a gap (something to learn), a slip (a lapse on that "
             "occasion) or unknown, with probabilities, how surprising the miss was to the mastery model, and the "
             "diagnosis's status. A pending or failed diagnosis says nothing either way. learner_said_my_gap is the "
             "learner's own statement, not evidence.")


__all__ = [
    "BASIS_POSTERIOR", "BASIS_PRIOR", "BETA_PRIOR", "CALIBRATION_VERSION", "CARD_NOTE", "CLASSES", "CLASS_WORDS",
    "DIAGNOSED", "FAILED", "FULLY_RIGHT", "GAP", "NONE", "NOT_APPLICABLE", "OBSERVATIONAL", "PENDING", "SELF_SELECTED",
    "SLIP", "SLOPES_VERSION", "STATUSES", "UNKNOWN", "VERSION", "beta_fit", "beta_rows", "calibrated", "card_entry",
    "cause_slopes", "diagnosis_state", "fit_beta", "latest_misses", "ledger_mark", "mark", "moments", "my_gap_marks",
    "prior_weights", "probe_posterior",
    "record_for", "sensor", "standardized", "stored_surprise", "surprise_reference", "surprise_words", "value_inputs",
]
