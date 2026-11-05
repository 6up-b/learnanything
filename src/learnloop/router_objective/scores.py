"""RO5 §9 item 2 into §8.7: each closed decision's comparison score ``D̂_i`` from the randomized checks, so ``w``
can move off its prior (RO4's weight posterior, :mod:`learnloop.router_objective.weight`, unchanged).

For decision ``i`` (its trace frozen before the draw): the uses are its population's topic-days ``(L, d)``, ``d`` the
``B`` calendar days after the decision's local date, each weighted ``v = c_L`` with the frozen baseline ``m⁰_{L,d}``,
plus each dated use in the window at ``ω``. A topic-day is observed when that day's randomized check of ``L``
completed (§6.2's label is ``Y``); its observation probability is ``r = r_L(d) × the running completion rate``:
``r_L(d)`` the day's exact assignment probability (``1/N_d``; the last earlier draw's on a day with no session, which
counts toward the completion gap as an assigned, uncompleted check), the completion rate pooled over every check and
never conditioned on the action; it is the rate as it stood when the window closed, so a closed score does not move
with later completions. A dated use's ``Y`` is the imported result on the goal's date (the goal's own date, frozen
with its ``due_at``: Codex review F6) with ``r = 1``; a date in the window with no import censors the score
(``no_result``). The cost is the realized attention cost over the window on the objective's own clock (Codex review
F4: attempts and Reader visits, ``price.activity_spans``; each session's ``κ0·((m + d)² − m²)/(2m̄)`` from the
minutes ``m`` it had when the window opened, at the day's ``κ0``) against the frozen ``C⁰``.

What carries no score is RO4's rule (a fallback, agreement, no valued use with ``r > 0``) plus RO5's: a decision whose
stop coin served something other than the mix's draw (``stop_coin_forced``). ``A_i`` is the mix's draw and ``μ_i``
its exact distribution (the coin is independent of it).

Reads only; nothing serving writes here. A leaf over the vault's tables, the router objective's modules and the
standard library.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
import json
from typing import Any

from learnloop.router_objective import checks as C
from learnloop.router_objective import price as P
from learnloop.router_objective import stop_coin as SC
from learnloop.router_objective import weight as W

VERSION = "ro5_scores_v1"
ANSWERED = "answered"
_STAMP = "%Y-%m-%dT%H:%M:%SZ"


def _parse(stamp: str) -> datetime:
    return datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))


@dataclass(frozen=True)
class Detail:
    """One decision's score and how it was formed (the report's row)."""

    scored: W.Scored
    uses: int = 0
    uses_with_r: int = 0
    observed: int = 0
    assessments: tuple[str, ...] = ()
    cost: float | None = None
    cost_baseline: float | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)


def _distribution(trace: Mapping[str, Any]) -> tuple[dict[str, float], dict[str, float], str | None, float | None]:
    mixing = trace.get("mixing") or {}
    mu = {str(k): float(v) for k, v in (mixing.get("mu") or {}).items()}
    llm = (trace.get("policies") or {}).get("llm") or {}
    numeric = (trace.get("policies") or {}).get("numeric") or {}
    support = list(mu)
    raw = {str(k): float(v) for k, v in (llm.get("distribution") or {}).items() if str(k) in mu}
    total = sum(raw.values())
    pi_l = {ref: (raw.get(ref, 0.0) / total if total > 0 else 0.0) for ref in support}
    pi_q = {ref: (1.0 if ref == numeric.get("choice") else 0.0) for ref in support}
    d = {ref: pi_l[ref] - pi_q[ref] for ref in support}
    taken = str(mixing.get("drawn_chosen") or mixing.get("chosen") or "")
    return d, mu, taken, mu.get(taken)


@dataclass(frozen=True)
class WindowSession:
    """One objective session's share of an evaluation window: its local date (its first activity's), the active
    minutes it had accumulated before the window opened (``carried``) and inside the window (``minutes``)."""

    local_date: str
    carried: float
    minutes: float


def _sessions(connection: Any, *, start: str, end: str, gap_minutes: float) -> list[WindowSession]:
    """The window's sessions on the objective's own clock (Codex review F4): the activity the serving price reads
    (``price.activity_spans``: attempts and Reader visits), split into sessions by the serving clock's own
    construction (``price.session_components``, Codex re-review F4: a Reader interval spanning two attempts makes one
    session here as it does there), read from the serving clock's lookback before ``start`` so a session in progress
    at the decision carries the minutes it had then. Activity finished at or before ``start`` is carried, after it
    (through ``end``) is the window's; a session's date is its first activity's."""

    since = (_parse(start) - timedelta(days=P.LOOKBACK_DAYS)).strftime(_STAMP)
    spans = P.activity_spans(connection, since=since, until=end)
    opened = _parse(start)
    out: list[WindowSession] = []
    for members in P.session_components(spans, gap_minutes=gap_minutes):
        carried = sum(spans[i][2] for i in members if spans[i][1] <= opened) / 60.0
        minutes = sum(spans[i][2] for i in members if spans[i][1] > opened) / 60.0
        if minutes > 0:
            first: datetime = min(spans[i][0] for i in members)
            out.append(WindowSession(first.astimezone().date().isoformat(), carried, minutes))
    return out


def window_cost(connection: Any, *, start: str, end: str, gap_minutes: float,
                prices: Mapping[str, tuple[float, float]], own: tuple[float, float]) -> float:
    """``C_i``: the attention cost the objective charges (§8.6) over ``(start, end]``, integrated from each
    session's minutes at the window's start, ``κ0·((m + d)² − m²)/(2m̄)``, at the ``(κ0, m̄)`` in force on the
    session's day (``own``, the decision's, on a day with no trace)."""

    cost = 0.0
    for session in _sessions(connection, start=start, end=end, gap_minutes=gap_minutes):
        kappa0, mbar = prices.get(session.local_date, own)
        total = session.carried + session.minutes
        cost += kappa0 * (total * total - session.carried * session.carried) / (2.0 * mbar)
    return cost


def goal_date(due_at: Any) -> str | None:
    """A goal's date as written (the date of its ``due_at`` in the offset it carries; ``goals/exam_seeding``
    stamps an import on that date), or None."""

    if not due_at:
        return None
    try:
        return _parse(str(due_at)).date().isoformat()
    except ValueError:
        return None


def dated_use_date(trace: Mapping[str, Any], row: Mapping[str, Any], dated: Mapping[str, Any]) -> str:
    """The calendar date a frozen dated use is scored on (Codex review F6): the goal's own date, frozen in the
    trace with its ``due_at`` (the goal's sources, or the use's own ``due_at`` at RO5's tag), never one rebuilt
    from truncated elapsed days; failing both, the decision's moment plus its exact delay."""

    own = goal_date(dated.get("due_at"))
    if own:
        return own
    goals = (trace.get("inputs_sources") or {}).get("goals") or {}
    frozen = goal_date((goals.get(str(dated.get("goal_id"))) or {}).get("due_at"))
    if frozen:
        return frozen
    moment = _parse(str(row["created_at"])) + timedelta(days=float(dated.get("at_days") or 0.0))
    return moment.date().isoformat()


def _day_prices(connection: Any) -> dict[str, tuple[float, float]]:
    """``(κ0, m̄)`` in force each local date: the day's first trace's."""

    out: dict[str, tuple[float, float]] = {}
    for local_date, kappa0, mbar in connection.execute(
            "SELECT local_date, kappa0, remembered_minutes FROM router_objective_traces ORDER BY created_at, id"):
        if local_date not in out and kappa0 is not None:
            out[str(local_date)] = (float(kappa0), max(float(mbar or 1.0), 1e-9))
    return out


def _exam_result(connection: Any, lo: str, on: str) -> float | None:
    """A dated use's ``Y``: the imported results on the goal's date (``goals/exam_seeding``), their mean."""

    rows = [float(row[0]) for row in connection.execute(
        "SELECT correctness FROM practice_attempts WHERE attempt_type = 'exam_evidence' AND learning_object_id = ? "
        "AND substr(created_at, 1, 10) = ? AND correctness IS NOT NULL", (lo, on))]
    return sum(rows) / len(rows) if rows else None


def score_decision(connection: Any, row: Mapping[str, Any], trace: Mapping[str, Any], *,
                   resolved: Mapping[tuple[str, str], C.Resolved], completion_rate: float | None,
                   r_lookup: Callable[[str], dict[str, float]], prices: Mapping[str, tuple[float, float]],
                   gap_minutes: float) -> Detail:
    """``D̂_i`` for one decision whose window has closed, or why it carries none."""

    base = dict(decision_id=str(row["decision_id"]), decided_at=str(row["created_at"]),
                window_closes_at=str(row["window_closes_at"]))
    if row.get("llm_status") != ANSWERED or row.get("numeric_status") != ANSWERED:
        return Detail(scored=W.Scored(**base, value=None, reason=W.FALLBACK))
    coin = trace.get("stop_coin") or {}
    if coin and coin.get("arm") != SC.POLICY:
        return Detail(scored=W.Scored(**base, value=None, reason=SC.FORCED))
    d, mu, taken, mu_taken = _distribution(trace)
    evaluation = trace.get("evaluation") or {}
    window = int(evaluation.get("window_days") or 14)
    start = date.fromisoformat(str(row["local_date"]))
    rate = float(completion_rate or 0.0)
    uses: list[W.Use] = []
    assessments: list[str] = []
    for topic in (evaluation.get("uses") or {}).get("topics") or ():
        lo = str(topic["lo"])
        m0 = topic.get("m0") or []
        for j in range(1, window + 1):
            day = (start + timedelta(days=j)).isoformat()
            r_assign = float(r_lookup(day).get(lo, 0.0))
            found = resolved.get((day, lo))
            observed = found is not None and found.status == "completed" and found.outcome is not None
            if observed:
                assessments.append(found.assessment_key())  # type: ignore[union-attr]
            baseline = m0[j - 1] if j - 1 < len(m0) and m0[j - 1] is not None else 0.0
            uses.append(W.Use(key=f"L:{lo}:{day}", weight=float(topic.get("c") or 0.0), baseline=float(baseline),
                              r=r_assign * rate, observed=observed, outcome=found.outcome if observed else None))
    for dated in (evaluation.get("uses") or {}).get("dated") or ():
        on = dated_use_date(trace, row, dated)
        result = _exam_result(connection, str(dated["lo"]), on)
        if result is None:
            return Detail(scored=W.Scored(**base, value=None, reason=W.NO_RESULT))
        uses.append(W.Use(key=f"G:{dated['goal_id']}:{dated['lo']}", weight=float(dated.get("omega") or 0.0),
                          baseline=float(dated.get("m0") or 0.0), r=1.0, observed=True, outcome=result))
    reason = W.carries_score(uses=uses, failed=[], d_taken=d.get(taken, 0.0), d_all=d)
    counts = dict(uses=len(uses), uses_with_r=sum(1 for use in uses if use.r > 0),
                  observed=sum(1 for use in uses if use.observed), assessments=tuple(assessments))
    if reason is not None:
        return Detail(scored=W.Scored(**base, value=None, reason=reason), **counts)
    if not mu_taken:
        return Detail(scored=W.Scored(**base, value=None, reason="no_logged_probability"), **counts)
    end = (_parse(str(row["created_at"])) + timedelta(days=window)).strftime(_STAMP)
    own = (float(row.get("kappa0") or 0.0), max(float(row.get("remembered_minutes") or 1.0), 1e-9))
    cost = window_cost(connection, start=str(row["created_at"]), end=end, gap_minutes=gap_minutes, prices=prices,
                       own=own)
    c0 = float(evaluation.get("c0") or 0.0)
    value = W.score(d_taken=d.get(taken, 0.0), mu_taken=float(mu_taken), uses=uses, cost=cost, cost_baseline=c0)
    return Detail(scored=W.Scored(**base, value=value), cost=cost, cost_baseline=c0, **counts)


def scores(connection: Any, config: Any, *, at: str) -> list[Detail]:
    """Every decision's score from the traces whose windows closed before ``at`` (no peeking), RO5's checks the
    observations."""

    if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'router_objective_traces'"
                          ).fetchone() is None:
        return []
    through = _parse(at).astimezone().date().isoformat()
    resolved = {(entry.local_date, entry.topic): entry for entry in C.resolve(connection, through=through)}
    rates: dict[str, float | None] = {}

    def completion_at(closes_at: str) -> float | None:
        # The running completion rate as it stood when the window closed: a closed score does not move with later
        # completions or later sessionless days (Codex review, "closed scores never change").
        day = min(_parse(closes_at).astimezone().date().isoformat(), through)
        if day not in rates:
            rates[day] = C.completion(connection, through=day).get("rate")
        return rates[day]

    cache: dict[str, dict[str, float]] = {}

    def r_lookup(day: str) -> dict[str, float]:
        if day not in cache:
            cache[day] = C.r_for(connection, local_date=day)[0] if day <= through else {}
        return cache[day]

    prices = _day_prices(connection)
    gap = float(config.router_objective.session_gap_minutes)
    out: list[Detail] = []
    for row in connection.execute(
            "SELECT decision_id, created_at, window_closes_at, local_date, llm_status, numeric_status, kappa0, "
            "remembered_minutes, trace_json FROM router_objective_traces WHERE decision_kind = 'plan_block' AND "
            "window_closes_at IS NOT NULL AND window_closes_at < ? ORDER BY created_at, id", (at,)):
        record = dict(row)
        trace = json.loads(record.pop("trace_json"))
        out.append(score_decision(connection, record, trace, resolved=resolved,
                                  completion_rate=completion_at(str(record["window_closes_at"])), r_lookup=r_lookup,
                                  prices=prices,
                                  gap_minutes=gap))
    return out


__all__ = ["Detail", "VERSION", "WindowSession", "dated_use_date", "goal_date", "score_decision", "scores",
           "window_cost"]
