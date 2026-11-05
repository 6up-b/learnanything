"""RO6 (spec_router_objective_v1 §10): the learned tail's data, read as of a moment. Reads only.

**What a decision was** (:func:`logged`). Every ``plan_block`` trace known at the moment (THE availability predicate,
``router_objective_switches.known_at``, over the trace row and over RO0's receipt row: a row received later never
enters a feature) becomes a :class:`Logged`: its generator version, its support, the logger's exact served
distribution (the mix's ``μ`` under the stop coin, §9.1), the tail's ``Q̄`` per candidate, and each candidate's
features (:mod:`learnloop.router_objective.learned_tail`). At RO6's tag the features are the ones the decision froze
in its trace (the same function over the same numbers at serve time); for an earlier trace they are rebuilt from the
trace's frozen belief numbers and RO0's decision-time snapshot (§4 row 9: its pending reports and the candidates'
mastery), the same function again.

**Generator versions** (:func:`generator`): the objective's, tail's and terminal's versions, the horizon, the LLM
policy's schema, the mix's seeds and floor, and the algorithm version. A change is a change point: a transition
whose two ends are under different versions is censored ``change_point``, so a version's evaluation reads only its
own transitions and refitting on a later version cannot move it.

**Trajectories** (:func:`transitions`): §4 row 12's links (``router_objective.trajectory``: the ledger's next
decision, with censoring) walked from each logged decision to the next logged one. The reward of ``(t_i, t_{i+1}]``
is this objective's ``R`` (§3.2), never ``S``: minus the attention cost the objective charges over the interval
(``scores.window_cost``, the objective's own clock), plus every completed randomized check administered in it at
``c_L·Y/r`` (``r`` the day's exact assignment probability times the running completion rate as it stood at the
interval's end: unbiased for the undated uses' ``Σ c_L·P``), plus every dated use whose moment falls in it (its
``due_at``, so an exam later the same day counts: Codex review F2) at ``ω·Y`` from the result imported for its date
by the moment (availability, ``attempt_time_sql``). Censored, by reason: ``no_later_decision``, ``change_point``,
``value_missing`` (a policy's ``Q̄`` was not computed), ``past_cutoff`` (the next decision lies past the decision's
cutoff ``C``), ``reward_open`` (a check in the interval still open), ``no_result`` (a dated use with no result yet),
``cutoff_unmatched``. The next state is valued at the decision's own cutoff (§3.2: one ``C`` per decision; Codex
re-review F3): with the same cutoff, the next decision's ``Q̄``; otherwise the next decision valued its candidates a
second time with every rollout run at ``C`` (``residual.previous.q``, :func:`learnloop.router_objective.tail_serve.
previous_cutoff`), so ``V(x′; C) = Σ_a′ π(a′|x′)·Q_tail(x′, a′; C)``, and the next state's features are taken at
``C``'s span (``residual.previous.features``). A next decision that did not value this one's cutoff is
``cutoff_unmatched``, never trimmed or moved back by an average terminal rate.

**Feature versions** (Codex re-review F7): a trace's frozen features are read only at this build's features
version and width; another build's are rebuilt with this build's function from the trace's frozen belief numbers
and RO0's receipt, and the version a decision's residual served with is part of its generator version, so a fit
never mixes two versions' vectors or two loggers.

A leaf over the vault's tables and the router objective's modules.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json
import math
from typing import Any
import zlib

from learnloop.router_objective import checks as C
from learnloop.router_objective import learned_tail as LT
from learnloop.router_objective import scores as S
from learnloop.router_objective import stop_coin as SC
from learnloop.router_objective import trajectory as TJ

VERSION = "ro6_tail_data_v3"
STOP = SC.STOP

NO_LATER_DECISION = "no_later_decision"
CHANGE_POINT = "change_point"
VALUE_MISSING = "value_missing"
PAST_CUTOFF = "past_cutoff"
REWARD_OPEN = "reward_open"
NO_RESULT = "no_result"
CUTOFF_UNMATCHED = "cutoff_unmatched"

#: Two cutoffs this close are one (the trace keeps ``cutoff_days`` to six places, about 0.09 s; numerical only).
_SAME_CUTOFF_SECONDS = 1.0

#: Parsed traces kept by (id, content hash): a trace never changes, so it is parsed once a process (an upper bound
#: on what is kept, a resource guard only).
_CACHE: dict[tuple[str, str], "Logged"] = {}
_CACHE_LIMIT = 50_000


def _parse(stamp: str) -> datetime:
    return datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))


def _round(value: Any) -> Any:
    from learnloop.router_objective import trace as T

    return T._round(value)


def generator_payload(*, algorithm_version: str, objective: Any, tail: Any, terminal: Any, horizon_days: Any,
                      llm_schema: Any, seeds: Mapping[str, Any] | None, epsilon: Any,
                      features: str | None = None) -> dict[str, Any]:
    """``features``: the features version the logger served with (None: this build's, :data:`LT.FEATURES_VERSION`)."""

    return _round({"algorithm": str(algorithm_version), "objective": objective, "tail": tail, "terminal": terminal,
                   "horizon_days": float(horizon_days) if horizon_days is not None else None,
                   "llm_schema": llm_schema, "seeds": dict(seeds or {}),
                   "epsilon": float(epsilon) if epsilon is not None else None,
                   "features": features or LT.FEATURES_VERSION})


def served_features_version(trace: Mapping[str, Any]) -> str:
    """The features version a decision's residual served with (Codex re-review F7): its record's, else its fit's
    (an earlier RO6 build's trace), else ``unversioned``; a decision with no applied residual never read features,
    so this build's version stands for it (its features are rebuilt with this build's function)."""

    residual = trace.get("residual")
    if not isinstance(residual, Mapping) or residual.get("status") != "applied":
        return LT.FEATURES_VERSION
    fit = residual.get("fit") if isinstance(residual.get("fit"), Mapping) else {}
    return str(residual.get("features_version") or fit.get("features_version") or "unversioned")


def generator_key(payload: Mapping[str, Any]) -> str:
    content = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def generator(trace: Mapping[str, Any], algorithm_version: str) -> str:
    """A logged decision's generator version (module docstring)."""

    versions = trace.get("versions") or {}
    mixing = trace.get("mixing") or {}
    return generator_key(generator_payload(
        algorithm_version=algorithm_version, objective=versions.get("objective"), tail=versions.get("tail"),
        terminal=versions.get("terminal"), horizon_days=versions.get("horizon_days"),
        llm_schema=versions.get("llm_schema"), seeds=mixing.get("seeds"), epsilon=mixing.get("epsilon"),
        features=served_features_version(trace)))


# -- one logged decision ----------------------------------------------------------------------------------


@dataclass(frozen=True)
class Logged:
    decision_id: str
    trace_id: str
    created_at: str
    local_date: str
    window_closes_at: str | None
    algorithm_version: str
    generator: str
    support: tuple[str, ...]
    served: str
    served_dist: Mapping[str, float]
    mu: Mapping[str, float]
    q_tail: Mapping[str, float] | None
    phi: Mapping[str, tuple[float, ...]]
    features_source: str
    cutoff_at: datetime | None
    horizon_days: float
    population: Mapping[str, float]
    #: each frozen dated use: (goal id, LO, its calendar date for the import's join, ω, its moment)
    dated: tuple[tuple[str, str, str, float, datetime], ...]
    kappa0: float
    remembered: float
    coin: Mapping[str, Any] | None
    residual: Mapping[str, Any] | None
    numeric_choice: str | None
    effective: Mapping[str, float]
    epsilon: float
    row: Mapping[str, Any] = field(default_factory=dict)
    #: §3.2 for the backup (Codex re-review F3): the earlier decision this one's candidates were also valued for at
    #: its cutoff (``residual.previous``: its id and ``C_prev − t`` in days), each candidate's ``Q_tail(x, a; C_prev)``
    #: from the evaluation run at that cutoff and its features at that cutoff's span (None unless every candidate of
    #: the support has both)
    previous_id: str | None = None
    previous_cutoff_days: float | None = None
    q_at_previous: Mapping[str, float] | None = None
    phi_at_previous: Mapping[str, tuple[float, ...]] | None = None


def _topic_map(entry: Mapping[str, Any]) -> dict[str, LT.TopicNumbers]:
    """A candidate's topics as its trace froze them (its sensors: the value's ``Topic`` numbers), by LO."""

    out: dict[str, LT.TopicNumbers] = {}
    for lo, sensor in (entry.get("sensors") or {}).items():
        if lo == "llm_forecast" or not isinstance(sensor, Mapping) or sensor.get("ad_eta") is None:
            continue
        out[str(lo)] = LT.TopicNumbers(eta=float(sensor["ad_eta"]), eta_var=float(sensor.get("ad_eta_var") or 0.0),
                                       practiced=bool(sensor.get("practiced")),
                                       stability=float(sensor.get("fsrs_stability") or 0.0),
                                       elapsed_days=float(sensor.get("fsrs_elapsed_days") or 0.0))
    return out


def _topics(entry: Mapping[str, Any]) -> tuple[LT.TopicNumbers, ...]:
    return tuple(_topic_map(entry).values())


def _candidate_topics(candidates: Mapping[str, Any]) -> dict[str, LT.TopicNumbers]:
    out: dict[str, LT.TopicNumbers] = {}
    for entry in candidates.values():
        for lo, topic in _topic_map(entry).items():
            out.setdefault(lo, topic)
    return out


def nearest_goal_days(trace: Mapping[str, Any]) -> float | None:
    """Days to the nearest active dated goal the decision valued (RO5's ``goal_dates``, else the window's uses)."""

    uses = (trace.get("goal_dates") or {}).get("uses")
    if uses is None:
        uses = ((trace.get("evaluation") or {}).get("uses") or {}).get("dated") or []
    days = [float(use["at_days"]) for use in uses if use.get("at_days") is not None]
    return min(days) if days else None


def rebuilt_features(trace: Mapping[str, Any], receipt: Mapping[str, Any] | None) -> dict[str, tuple[float, ...]]:
    """Each candidate's features from the trace's frozen belief numbers and RO0's decision-time snapshot."""

    candidates = trace.get("candidates") or {}
    session = trace.get("session") or {}
    remembered = session.get("remembered_minutes")
    state = (receipt or {}).get("state") or {}
    topics = _candidate_topics(candidates)
    belief = LT.belief(session_minutes=session.get("minutes"), remembered=remembered,
                       nearest_goal_days=nearest_goal_days(trace),
                       horizon_days=float((trace.get("versions") or {}).get("horizon_days") or 90.0),
                       pending_reports=(receipt or {}).get("pending_reports"),
                       mastery=snapshot_mastery(state.get("los") or {}, list(topics)), topics=list(topics.values()),
                       cutoff_days=(float(trace["cutoff_days"]) if trace.get("cutoff_days") is not None else None))
    return {ref: LT.vector(belief, LT.ActionView(ref=ref, kind=str(entry.get("kind") or ""),
                                                 minutes=float(entry.get("minutes") or 0.0), topics=_topics(entry)),
                           remembered=remembered)
            for ref, entry in candidates.items()}


def snapshot_mastery(snapshot: Mapping[str, Any], los: Sequence[str]) -> list[tuple[float, float]]:
    """RO0 row 9's mastery numbers of ``los`` (logit mean, logit variance), those it holds."""

    return [(float(snapshot[lo]["logit_mean"]), float(snapshot[lo].get("logit_variance") or 0.0)) for lo in los
            if isinstance(snapshot.get(lo), Mapping) and snapshot[lo].get("logit_mean") is not None]


def _served(trace: Mapping[str, Any]) -> tuple[dict[str, float], str]:
    mixing = trace.get("mixing") or {}
    mu = {str(k): float(v) for k, v in (mixing.get("mu") or {}).items()}
    coin = trace.get("stop_coin") or {}
    support = list(mu)
    dist = SC.served_distribution(mu, float(coin["rate"]), support) if coin.get("rate") else dict(mu)
    return dist, str(mixing.get("chosen") or "")


def _receipt(connection: Any, decision_id: str, config: Any, at: str) -> dict[str, Any] | None:
    """RO0's decision-time snapshot of one decision, if it was known at ``at`` (the availability predicate)."""

    from learnloop.router_objective_switches import known_at

    row = connection.execute(
        "SELECT pending_reports, state_z, created_at FROM decision_state_receipts WHERE decision_id = ?",
        (decision_id,)).fetchone()
    if row is None:
        return None
    found = {"pending_reports": row[0], "created_at": row[2]}
    known = known_at(found, config)
    if known is None or known > at:
        return None
    found["state"] = json.loads(zlib.decompress(row[1]).decode("utf-8"))
    return found


def use_moment(trace: Mapping[str, Any], created: datetime, use: Mapping[str, Any]) -> datetime:
    """The moment a frozen dated use falls at (Codex review of RO6, F2): the goal's ``due_at`` as the rollouts parse
    it (``clock.parse_utc``, the use's own or the goal's frozen in the trace), else the decision's moment plus the
    use's exact delay. The calendar date (``scores.dated_use_date``) stays the join key for an imported result."""

    from learnloop.clock import parse_utc

    due = use.get("due_at") or (((trace.get("inputs_sources") or {}).get("goals") or {}).get(
        str(use.get("goal_id"))) or {}).get("due_at")
    if due:
        try:
            moment = parse_utc(str(due))
        except ValueError:
            moment = None
        if moment is not None:
            return moment
    return created + timedelta(days=float(use.get("at_days") or 0.0))


def _logged(connection: Any, row: Mapping[str, Any], trace: Mapping[str, Any], config: Any, at: str,
            receipts: bool) -> Logged:
    candidates = trace.get("candidates") or {}
    support = tuple(str(ref) for ref in (trace.get("mixing") or {}).get("mu") or candidates)
    served_dist, served = _served(trace)
    q = {ref: float((entry.get("terms") or {})["q"]) for ref, entry in candidates.items()
         if (entry.get("terms") or {}).get("q") is not None}
    q_tail = q if support and all(ref in q for ref in support) else None
    residual = trace.get("residual") if isinstance(trace.get("residual"), Mapping) else None
    frozen = (residual or {}).get("candidates") or {}
    width = len(LT.NAMES)
    # Frozen features are read only at this build's features version and width (Codex re-review F7: an earlier
    # build's thirteen are another function); any other trace's are rebuilt with this build's function from its
    # frozen belief numbers and RO0's decision-time receipt, so every vector a fit reads is one version's.
    current = served_features_version(trace) == LT.FEATURES_VERSION
    if (current and frozen and all(isinstance(frozen.get(ref), Mapping) and frozen[ref].get("features")
                                   and len(frozen[ref]["features"]) == width for ref in support)):
        phi = {ref: tuple(float(v) for v in frozen[ref]["features"]) for ref in support}
        source = "frozen"
    else:
        receipt = _receipt(connection, str(row["decision_id"]), config, at) if receipts else None
        phi = rebuilt_features(trace, receipt)
        source = "rebuilt" + ("" if receipt is not None else ":no_receipt")
    evaluation = trace.get("evaluation") or {}
    population = {str(use["lo"]): float(use.get("c") or 0.0) for use in (evaluation.get("uses") or {}).get("topics") or ()}
    dated = []
    goals = (trace.get("inputs_sources") or {}).get("goals") or {}
    created = _parse(str(row["created_at"]))
    for use in ((trace.get("goal_dates") or {}).get("uses") or (evaluation.get("uses") or {}).get("dated") or ()):
        on = S.dated_use_date(trace, row, use)
        weight = use.get("omega")
        if weight is None:
            # ω as the decision froze it: the goal's per-topic weight, else its dated weight (§8.5).
            goal = goals.get(str(use.get("goal_id"))) or {}
            weight = (goal.get("per_lo") or {}).get(str(use.get("lo")), goal.get("dated"))
        if weight is None:
            continue  # no frozen weight: not a use this decision valued
        dated.append((str(use.get("goal_id")), str(use.get("lo")), on, float(weight),
                      use_moment(trace, created, use)))
    cutoff_days = trace.get("cutoff_days")
    horizon = float((trace.get("versions") or {}).get("horizon_days") or 90.0)
    mixing = trace.get("mixing") or {}
    previous = (residual or {}).get("previous") if isinstance((residual or {}).get("previous"), Mapping) else None
    # The candidates' value and features at the earlier decision's carried cutoff (Codex re-review F3): the
    # evaluation run at it and the features taken at its span, both for every candidate of the support, at this
    # build's features version; anything less leaves the transition into this decision cutoff_unmatched.
    carried_q = (previous or {}).get("q") if isinstance((previous or {}).get("q"), Mapping) else {}
    carried_phi = (previous or {}).get("features") if isinstance((previous or {}).get("features"), Mapping) else {}
    q_at_previous = ({ref: float(carried_q[ref]) for ref in support}
                     if previous and current and support and all(carried_q.get(ref) is not None for ref in support)
                     else None)
    phi_at_previous = ({ref: tuple(float(v) for v in carried_phi[ref]) for ref in support}
                       if q_at_previous is not None and all(isinstance(carried_phi.get(ref), Sequence)
                                                            and len(carried_phi[ref]) == width for ref in support)
                       else None)
    if phi_at_previous is None:
        q_at_previous = None
    return Logged(
        decision_id=str(row["decision_id"]), trace_id=str(row["id"]), created_at=str(row["created_at"]),
        local_date=str(row["local_date"]), window_closes_at=row.get("window_closes_at"),
        algorithm_version=str(row["algorithm_version"]), generator=generator(trace, str(row["algorithm_version"])),
        support=support, served=served, served_dist=served_dist,
        mu={str(k): float(v) for k, v in (mixing.get("mu") or {}).items()}, q_tail=q_tail, phi=phi,
        features_source=source,
        cutoff_at=(created + timedelta(days=float(cutoff_days))) if cutoff_days is not None else None,
        horizon_days=horizon, population=population, dated=tuple(dated),
        kappa0=float(row.get("kappa0") or 0.0), remembered=max(float(row.get("remembered_minutes") or 1.0), 1e-9),
        coin=trace.get("stop_coin") if isinstance(trace.get("stop_coin"), Mapping) else None, residual=residual,
        numeric_choice=((trace.get("policies") or {}).get("numeric") or {}).get("choice"),
        effective={str(k): float(v) for k, v in (mixing.get("effective") or {}).items()},
        epsilon=float(mixing.get("epsilon") or 0.0),
        row={key: row[key] for key in ("decision_id", "created_at", "local_date", "window_closes_at", "kappa0",
                                       "remembered_minutes", "llm_status", "numeric_status")},
        previous_id=str(previous["decision_id"]) if previous and previous.get("decision_id") else None,
        previous_cutoff_days=(float(previous["cutoff_days"]) if previous and previous.get("cutoff_days") is not None
                              else None),
        q_at_previous=q_at_previous, phi_at_previous=phi_at_previous)


def logged(connection: Any, config: Any, *, at: str) -> list[Logged]:
    """Every ``plan_block`` trace known at ``at``, oldest first (module docstring)."""

    from learnloop.db.stores import router_objective as store
    from learnloop.router_objective_switches import known_at

    if not store.table_present(connection, store.TRACES):
        return []
    receipts = store.table_present(connection, store.DECISION_STATE)
    out: list[Logged] = []
    for raw in connection.execute(
            "SELECT id, decision_id, created_at, local_date, window_closes_at, algorithm_version, kappa0, "
            "remembered_minutes, llm_status, numeric_status, content_hash FROM router_objective_traces "
            "WHERE decision_kind = 'plan_block' ORDER BY created_at, id"):
        row = dict(raw)
        known = known_at(row, config)
        if known is None or known > at:
            continue
        key = (str(row["id"]), str(row["content_hash"]))
        found = _CACHE.get(key)
        if found is None:
            body = connection.execute("SELECT trace_json FROM router_objective_traces WHERE id = ?",
                                      (row["id"],)).fetchone()[0]
            found = _logged(connection, row, json.loads(body), config, at, receipts)
            # A receipt is written in its decision's transaction, at its moment: known with the trace, so a parse
            # that read one stands at every moment the trace is known. One that found none is not kept.
            if found.features_source in ("frozen", "rebuilt"):
                if len(_CACHE) >= _CACHE_LIMIT:
                    _CACHE.clear()
                _CACHE[key] = found
        out.append(found)
    return out


# -- the trajectories -------------------------------------------------------------------------------------


def _next_links(connection: Any, logged_ids: set[str]) -> tuple[dict[str, str | None], dict[str, Any]]:
    """§4 row 12's links: from each logged decision, the next logged decision along the ledger's next-decision
    chain (None: censored, no later one), and the return's censoring for the report."""

    rows = TJ.rows(connection)
    following = {str(row["decision_id"]): row.get("next_decision_id") for row in rows}
    returns = {str(row["decision_id"]): row.get("return_censored") for row in rows if str(row["decision_id"]) in logged_ids}
    out: dict[str, str | None] = {}
    for decision_id in logged_ids:
        cursor = following.get(decision_id)
        seen = 0
        while cursor is not None and str(cursor) not in logged_ids and seen <= len(following):
            cursor = following.get(str(cursor))
            seen += 1
        out[decision_id] = str(cursor) if cursor is not None and str(cursor) in logged_ids else None
    return out, returns


def _exam_result_known(connection: Any, config: Any, lo: str, on: str, at: str) -> float | None:
    """A dated use's ``Y``: the results imported for the goal's date, known by ``at`` (THE availability predicate;
    the one reader the contrasts' returns share, ``scores.exam_result_known``), and admitted through RO5's closure
    at ``at`` on its occurrence and received time (RO6's landing ruling R4)."""

    return S.exam_result_known(connection, config, lo, on, at, C.Closure.at(at))


@dataclass(frozen=True)
class Steps:
    transitions: tuple[LT.Transition, ...]
    censored: Mapping[str, int]
    change_points: tuple[Mapping[str, Any], ...]
    returns_censored: Mapping[str, int]


def transitions(connection: Any, config: Any, rows: Sequence[Logged], *, at: str) -> Steps:
    """Every logged decision's step to the next one, with its reward (module docstring)."""

    ordered = sorted(rows, key=lambda row: (row.created_at, row.decision_id))
    by_id = {row.decision_id: row for row in ordered}
    nxt, returns = _next_links(connection, set(by_id)) if ordered else ({}, {})
    # RO6's landing ruling R4: every read of RO5's checks and prices goes through RO5's landed closure (the as-of
    # cutoff on occurrence and received time, :class:`checks.Closure`): the checks as they stood at ``at`` (an
    # answer received later is still open), and each interval's completion rate and daily prices as of its own end.
    ledger = C.Ledger(connection) if ordered else None
    reading = C.Closure.at(at)
    resolved = ledger.resolve(reading) if ledger is not None else []
    planned = C.administered(connection) if ordered else {}
    checks = []
    for entry in resolved:
        when = (planned.get(entry.assignment_id) or {}).get("planned_at")
        if when is not None and reading.admits(when):
            checks.append((str(when), entry))
    price_rows = S._price_rows(connection) if ordered else []
    by_end: dict[str, tuple[float | None, dict[str, tuple[float, float]]]] = {}

    def as_of_end(end: str) -> tuple[float | None, dict[str, tuple[float, float]]]:
        """The interval's completion rate and daily prices as of its end (never later than ``at``)."""

        cut = min(str(end), str(at))
        if cut not in by_end:
            closure = C.Closure.at(cut)
            by_end[cut] = (ledger.completion(closure).get("rate") if ledger is not None else None,
                           S._day_prices(connection, closure, price_rows))
        return by_end[cut]

    gap = float(config.router_objective.session_gap_minutes)
    censored: Counter[str] = Counter()
    change_points: list[dict[str, Any]] = []
    steps: list[LT.Transition] = []
    for row in ordered:
        following = nxt.get(row.decision_id)
        later = by_id.get(following) if following else None
        if later is None:
            censored[NO_LATER_DECISION] += 1
            continue
        if later.generator != row.generator:
            censored[CHANGE_POINT] += 1
            change_points.append({"before": row.decision_id, "after": later.decision_id, "at": later.created_at,
                                  "from": row.generator, "to": later.generator,
                                  "algorithm": [row.algorithm_version, later.algorithm_version]})
            continue
        if row.q_tail is None or later.q_tail is None or row.served not in row.q_tail or row.served not in row.phi:
            censored[VALUE_MISSING] += 1
            continue
        if row.cutoff_at is not None and _parse(later.created_at) >= row.cutoff_at:
            censored[PAST_CUTOFF] += 1
            continue
        start, end = row.created_at, later.created_at
        rate_at_end, prices = as_of_end(end)
        reward = -S.window_cost(connection, start=start, end=end, gap_minutes=gap, prices=prices,
                                own=(row.kappa0, row.remembered))
        observed = 0
        is_open = False
        for when, entry in checks:
            if not (start < when <= end):
                continue
            if entry.status == C.OPEN:
                is_open = True
                break
            if entry.status != C.COMPLETED or entry.outcome is None:
                continue
            r = float(entry.r) * float(rate_at_end or 0.0)
            c = float(row.population.get(entry.topic, 0.0))
            if r > 0 and c > 0:
                reward += c * float(entry.outcome) / r
                observed += 1
        if is_open:
            censored[REWARD_OPEN] += 1
            continue
        missing = False
        opened, closed = _parse(start), _parse(end)
        for _goal_id, lo, on, omega, moment in row.dated:
            # The use's own moment in (t_i, t_{i+1}] (F2: an exam later the same day falls in this interval, not in
            # none); its calendar date joins the import.
            if opened < moment <= closed:
                result = _exam_result_known(connection, config, lo, on, at)
                if result is None:
                    missing = True
                    break
                reward += omega * result
        if missing:
            censored[NO_RESULT] += 1
            continue
        # §3.2: the next state valued at this decision's own cutoff C (Codex re-review F3). With the same cutoff the
        # next decision's own Q̄ and features are that value's; otherwise the next decision must have valued its
        # candidates with every rollout run at C (``residual.previous.q``) and taken their features at C's span
        # (``residual.previous.features``). Anything else is censored, never trimmed or moved back.
        shift_days = 0.0
        if row.cutoff_at is not None and later.cutoff_at is not None:
            shift_days = (later.cutoff_at - row.cutoff_at).total_seconds() / 86400.0
        if abs(shift_days) * 86400.0 <= _SAME_CUTOFF_SECONDS:
            values, vectors, basis = later.q_tail, later.phi, "same_cutoff"
        elif (later.previous_id == row.decision_id and later.q_at_previous is not None
              and later.phi_at_previous is not None):
            values, vectors, basis = later.q_at_previous, later.phi_at_previous, "previous_cutoff"
        else:
            censored[CUTOFF_UNMATCHED] += 1
            continue
        next_v = sum(float(later.served_dist.get(ref, 0.0)) * values[ref] for ref in later.support)
        width = len(LT.NAMES)
        next_phi = tuple(sum(float(later.served_dist.get(ref, 0.0)) * vectors[ref][k] for ref in later.support
                             if ref in vectors) for k in range(width))
        steps.append(LT.Transition(
            decision_id=row.decision_id, generator=row.generator, decided_at=row.created_at,
            phi=tuple(row.phi[row.served]), next_phi=next_phi, reward=reward, q_taken=row.q_tail[row.served],
            next_v_tail=next_v, detail={"next": later.decision_id, "checks": observed, "shift_days": shift_days,
                                        "cutoff": basis}))
    return Steps(transitions=tuple(steps), censored=dict(censored), change_points=tuple(change_points),
                 returns_censored=dict(Counter(str(value) for value in returns.values() if value)))


# -- the fits -----------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Fits:
    by_generator: Mapping[str, LT.Fit]
    order: tuple[str, ...]
    steps: Steps
    decisions: int

    def for_serving(self, generator_now: str) -> tuple[LT.Fit | None, str]:
        """The current version's own fit; with none of its transitions yet, the latest earlier version's ("version
        k+1 uses the result"); else none."""

        if generator_now in self.by_generator:
            return self.by_generator[generator_now], "own_version"
        for key in reversed(self.order):
            if key != generator_now and key in self.by_generator:
                return self.by_generator[key], "previous_version"
        return None, "no_transition"


def fits(connection: Any, config: Any, *, at: str, rows: Sequence[Logged] | None = None) -> Fits:
    """One fit per generator version from its own transitions as of ``at`` (frozen-logger evaluation)."""

    rows = list(rows) if rows is not None else logged(connection, config, at=at)
    steps = transitions(connection, config, rows, at=at)
    prior = float(config.router_objective.residual_prior_sd)
    groups: dict[str, list[LT.Transition]] = {}
    for step in steps.transitions:
        groups.setdefault(step.generator, []).append(step)
    order = tuple(dict.fromkeys(row.generator for row in sorted(rows, key=lambda r: (r.created_at, r.decision_id))))
    by_generator = {key: LT.fit(groups[key], prior_sd=prior, generator=key) for key in order if key in groups}
    return Fits(by_generator=by_generator, order=order, steps=steps, decisions=len(rows))


# -- the randomized contrasts and the cross-check ------------------------------------------------------------


def _frozen_residual(row: Logged) -> dict[str, float] | None:
    frozen = (row.residual or {}).get("candidates") or {}
    values = {ref: float(frozen[ref]["v_residual"]) for ref in row.support
              if isinstance(frozen.get(ref), Mapping) and frozen[ref].get("v_residual") is not None}
    return values if len(values) == len(row.support) and values else None


def _with_traces(connection: Any, rows: Sequence[Logged]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        body = connection.execute("SELECT trace_json FROM router_objective_traces WHERE id = ?",
                                  (row.trace_id,)).fetchone()[0]
        out.append({**dict(row.row), "trace": json.loads(body)})
    return out


def contrasts(connection: Any, config: Any, rows: Sequence[Logged], *, at: str) -> tuple[list[LT.Contrast], dict[str, Any]]:
    """Every stop-coin decision with a frozen residual whose window closed before ``at``: its realized contrast
    (the coin's, times the window's observed return) and its frozen predicted ones (tail and residual).

    The cohort is chosen on what was fixed before the coin (a frozen residual, stop in the support, a predicted
    contrast, a closed window), never on whether the return was observed afterwards: every draw stays, each window's
    return read with its missing terms carried as missing and bounded (``scores.observed_return``'s ``complete``, a
    ``scores.Bounded``; RO6's landing ruling R1), and :func:`learned_tail.residual_weight` reads them at the fill
    least favourable to the residual. The record says how many were left out before the coin and why, each arm's
    notes on its returns, and each forced window's missing terms with their bounds."""

    eligible = [row for row in rows if row.coin and row.q_tail is not None and _frozen_residual(row) is not None
                and row.window_closes_at and str(row.window_closes_at) < at and STOP in row.support]
    # Every window's return with its missing terms bounded (R1): no term is ever filled as zero.
    returns = S.observed_returns(connection, config, at=at, rows=_with_traces(connection, eligible), complete=True)
    draws: list[LT.CoinDraw] = []
    before_coin: Counter[str] = Counter()
    for row in eligible:
        tail = LT.predicted_contrast(row.q_tail or {}, row.mu, STOP)
        residual = LT.predicted_contrast(_frozen_residual(row) or {}, row.mu, STOP)
        if tail is None or residual is None:
            before_coin["no_block_in_support"] += 1  # frozen before the coin: not a selection on the outcome
            continue
        found = returns.get(row.decision_id)
        if isinstance(found, tuple):  # a (value, reason) pair: no missing term
            found = S.Bounded(value=found[0], reason=found[1])
        if not isinstance(found, S.Bounded):
            found = S.Bounded(value=None, reason="window_open")
        draws.append(LT.CoinDraw(decision_id=row.decision_id, decided_at=row.created_at,
                                 window_closes_at=str(row.window_closes_at), arm=(row.coin or {}).get("arm"),
                                 rate=float((row.coin or {}).get("rate") or 0.0),
                                 value=float(found.value) if found.value is not None else None, reason=found.reason,
                                 tail=tail, residual=residual, lo=float(found.lo), hi=float(found.hi),
                                 missing=int(found.missing)))
    out, record = LT.coin_contrasts(draws)
    record["before_coin"] = dict(before_coin)
    return out, record


def improvement_ratio(row: Logged) -> float | None:
    """The improvement step's probability of the served action over the logger's: the mix with the numeric
    policy's argmax taken on ``Q_tail + ρ`` (the frozen residual at full weight), under the same coin."""

    values = _frozen_residual(row)
    if values is None or row.q_tail is None or row.numeric_choice not in row.support:
        return None
    improved = max(row.support, key=lambda ref: (row.q_tail[ref] + values[ref], -row.support.index(ref)))
    share = float(row.effective.get("numeric", 0.0)) * (1.0 - len(row.support) * row.epsilon)
    mu_new = {ref: row.mu.get(ref, 0.0) + share * ((1.0 if ref == improved else 0.0)
                                                   - (1.0 if ref == row.numeric_choice else 0.0))
              for ref in row.support}
    rate = float((row.coin or {}).get("rate") or 0.0)
    served_new = SC.served_distribution(mu_new, rate, list(row.support)) if rate else mu_new
    logged_p = float(row.served_dist.get(row.served, 0.0))
    if logged_p <= 0:
        return None
    return float(served_new.get(row.served, 0.0)) / logged_p


def cross_check(connection: Any, config: Any, rows: Sequence[Logged], *, at: str) -> dict[str, Any]:
    """The partial-history weights' estimate of the improvement step, beside the fit (report only).

    The windows evaluated are those closed before ``at`` with a ratio and an observed return; each window's product
    runs over the complete logged sequence (Codex review of RO6, F6: every decision inside the window, its own
    window open or not), and a window holding a decision with no computable ratio is censored, never shortened."""

    ratios = {row.decision_id: improvement_ratio(row) for row in rows}
    sequence = [LT.Ratio(decision_id=row.decision_id, decided_at=row.created_at, ratio=ratios[row.decision_id])
                for row in rows]
    eligible = [row for row in rows if row.window_closes_at and str(row.window_closes_at) < at
                and ratios[row.decision_id] is not None]
    returns = S.observed_returns(connection, config, at=at, rows=_with_traces(connection, eligible))
    weighted = []
    for row in eligible:
        value, _reason = returns.get(row.decision_id, (None, None))
        ratio = ratios[row.decision_id]
        if value is None or ratio is None:
            continue
        weighted.append(LT.WeightedRow(decision_id=row.decision_id, decided_at=row.created_at, ratio=ratio,
                                       realized=float(value), window_closes_at=str(row.window_closes_at)))
    return LT.partial_history(weighted, window_days=int(config.router_objective.evaluation_window_days),
                              sequence=sequence)


def predicted_improvement(rows: Sequence[Logged]) -> dict[str, Any]:
    """The fit's own forecast of the same step: ``Σ_a (μ_new − μ)(a)·(Q_tail + ρ)(a)``, the mean over decisions with a
    frozen residual (a projection, labelled; on the cutoff's horizon, not the window's)."""

    values = []
    for row in rows:
        residual = _frozen_residual(row)
        ratio_ok = improvement_ratio(row)
        if residual is None or ratio_ok is None or row.q_tail is None:
            continue
        improved = max(row.support, key=lambda ref: (row.q_tail[ref] + residual[ref], -row.support.index(ref)))
        share = float(row.effective.get("numeric", 0.0)) * (1.0 - len(row.support) * row.epsilon)
        delta = share * ((row.q_tail[improved] + residual[improved])
                         - (row.q_tail[row.numeric_choice] + residual[row.numeric_choice]))  # type: ignore[index]
        values.append(delta)
    return {"n": len(values), "mean": (sum(values) / len(values)) if values else None,
            "label": "a projection by the fit itself, on the cutoff's horizon; never evidence for it"}


def is_finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


__all__ = [
    "CHANGE_POINT", "CUTOFF_UNMATCHED", "Fits", "Logged", "NO_LATER_DECISION", "NO_RESULT", "PAST_CUTOFF",
    "REWARD_OPEN", "Steps", "VALUE_MISSING", "VERSION", "contrasts", "cross_check", "fits", "generator",
    "generator_key", "generator_payload", "improvement_ratio", "logged", "nearest_goal_days", "predicted_improvement",
    "rebuilt_features", "transitions", "use_moment",
]
