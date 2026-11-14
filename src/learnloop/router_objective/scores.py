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


@dataclass(frozen=True)
class Bounded:
    """RO6's landing ruling R1: a window's return with its missing terms carried as missing. ``value`` is the
    observed terms' bracket (the cost included: costs are always observed); the return lies in
    ``[value + lo, value + hi]``, the sums of the missing terms' bounds (:meth:`Term.bounds`). ``value`` None: no
    return at all (unbounded). ``reason``: the missing terms counted by reason (``dated_missing:n``,
    ``no_check_support:n``). ``excluded`` (landing ruling R7): the undated uses whose topic had no check support as of
    the draw, outside the measurable target and left out of ``value`` and the bounds alike."""

    value: float | None
    reason: str | None = None
    lo: float = 0.0
    hi: float = 0.0
    missing: int = 0
    excluded: int = 0
    #: R10: the missing terms by reason (the ledger's loss kinds and RO6's own)
    by_reason: Mapping[str, int] = field(default_factory=dict)


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


def _sessions(connection: Any, *, start: str, end: str, gap_minutes: float,
              lessons: bool = False) -> list[WindowSession]:
    """The window's sessions on the objective's own clock (Codex review F4): the activity the serving price reads
    (``price.activity_spans``: attempts and Reader visits), split into sessions by the serving clock's own
    construction (``price.session_components``, Codex re-review F4: a Reader interval spanning two attempts makes one
    session here as it does there), read from the serving clock's lookback before ``start`` so a session in progress
    at the decision carries the minutes it had then. Activity finished at or before ``start`` is carried, after it
    (through ``end``) is the window's; a session's date is its first activity's. ``lessons`` (teacher TE3b): the
    lessons' active minutes too, as the serving clock reads them."""

    since = (_parse(start) - timedelta(days=P.LOOKBACK_DAYS)).strftime(_STAMP)
    spans = P.activity_spans(connection, since=since, until=end, lessons=lessons)
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
                prices: Mapping[str, tuple[float, float]], own: tuple[float, float], lessons: bool = False) -> float:
    """``C_i``: the attention cost the objective charges (§8.6) over ``(start, end]``, integrated from each
    session's minutes at the window's start, ``κ0·((m + d)² − m²)/(2m̄)``, at the ``(κ0, m̄)`` in force on the
    session's day (``own``, the decision's, on a day with no trace)."""

    cost = 0.0
    for session in _sessions(connection, start=start, end=end, gap_minutes=gap_minutes, lessons=lessons):
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


def _price_rows(connection: Any) -> list[tuple[Any, Any, Any, Any]]:
    """Every price-source trace, ``(local_date, κ0, m̄, created_at)``, in the order the day's first one is read."""

    return [tuple(row) for row in connection.execute(
        "SELECT local_date, kappa0, remembered_minutes, created_at FROM router_objective_traces "
        "ORDER BY created_at, id")]


def _day_prices(connection: Any, closure: C.Closure | None = None,
                rows: Sequence[tuple[Any, Any, Any, Any]] | None = None) -> dict[str, tuple[float, float]]:
    """``(κ0, m̄)`` in force each local date as of a window's ``closure``: the day's first trace's, every
    price-source trace admitted through :meth:`checks.Closure.admits` on its created time (landing ruling R11: a
    trace written after the window closed never prices it). ``rows``: :func:`_price_rows`, read once for many
    closures. No ``closure``: every trace (a test's read of the whole log)."""

    out: dict[str, tuple[float, float]] = {}
    for local_date, kappa0, mbar, created in (rows if rows is not None else _price_rows(connection)):
        if closure is not None and not closure.admits(created):
            continue
        if local_date not in out and kappa0 is not None:
            out[str(local_date)] = (float(kappa0), max(float(mbar or 1.0), 1e-9))
    return out


def _exam_result(connection: Any, lo: str, on: str, closure: C.Closure | None = None) -> float | None:
    """A dated use's ``Y``: the imported results on the goal's date (``goals/exam_seeding``), their mean, each
    admitted by the window's closure on its occurrence and its received time (landing ruling R1: an import after
    the window closed is not seen, and the use is censored ``no_result``, as one never imported)."""

    rows = [float(row[0]) for row in connection.execute(
        "SELECT correctness, created_at, received_at FROM practice_attempts WHERE attempt_type = 'exam_evidence' "
        "AND learning_object_id = ? AND substr(created_at, 1, 10) = ? AND correctness IS NOT NULL", (lo, on))
        if closure is None or closure.admits(row[1], row[2])]
    return sum(rows) / len(rows) if rows else None


def exam_result_known(connection: Any, config: Any, lo: str, on: str, at: str,
                      closure: C.Closure | None = None) -> float | None:
    """RO6: a dated use's ``Y`` as known at ``at``: the results imported for the goal's date that THE availability
    predicate (``router_objective_switches.attempt_time_sql``) admits by ``at``, their mean. ``closure`` (a closed
    window's, RO6's landing ruling R4): each result is also admitted through :meth:`checks.Closure.admits` on its
    occurrence and received time, as RO5's scores read it, so a closed window's return never moves with a later
    import."""

    from learnloop.router_objective_switches import attempt_time_sql

    known = attempt_time_sql(config)
    rows = [float(row[0]) for row in connection.execute(
        "SELECT correctness, created_at, received_at FROM practice_attempts WHERE attempt_type = 'exam_evidence' "
        f"AND learning_object_id = ? AND substr(created_at, 1, 10) = ? AND correctness IS NOT NULL AND {known} <= ?",
        (lo, on, at)) if closure is None or closure.admits(row[1], row[2])]
    return sum(rows) / len(rows) if rows else None


def score_decision(connection: Any, row: Mapping[str, Any], trace: Mapping[str, Any], *,
                   resolved: Mapping[tuple[str, str], C.Resolved], completion_rate: float | None,
                   r_lookup: Callable[[str], dict[str, float]], prices: Mapping[str, tuple[float, float]],
                   gap_minutes: float, closure: C.Closure | None = None, lessons: bool = False) -> Detail:
    """``D̂_i`` for one decision whose window has closed, or why it carries none. ``resolved``, the completion
    rate and ``r_lookup`` stand as of ``closure`` (:func:`scores` forms them through it), which also admits the
    dated uses' imported results."""

    base = dict(decision_id=str(row["decision_id"]), decided_at=str(row["created_at"]),
                window_closes_at=str(row["window_closes_at"]))
    if row.get("llm_status") != ANSWERED or row.get("numeric_status") != ANSWERED:
        return Detail(scored=W.Scored(**base, value=None, reason=W.FALLBACK))
    coin = trace.get("stop_coin") or {}
    if coin and coin.get("arm") != SC.POLICY:
        return Detail(scored=W.Scored(**base, value=None, reason=SC.FORCED))
    d, mu, taken, mu_taken = _distribution(trace)

    def exam(conn: Any, lo: str, on: str) -> float | None:
        return _exam_result(conn, lo, on, closure)

    found_uses = window_uses(connection, row, trace, resolved=resolved, completion_rate=completion_rate,
                             r_lookup=r_lookup, exam_result=exam)
    if found_uses is None:
        return Detail(scored=W.Scored(**base, value=None, reason=W.NO_RESULT))
    uses, assessments = found_uses
    reason = W.carries_score(uses=uses, failed=[], d_taken=d.get(taken, 0.0), d_all=d)
    counts = dict(uses=len(uses), uses_with_r=sum(1 for use in uses if use.r > 0),
                  observed=sum(1 for use in uses if use.observed), assessments=tuple(assessments))
    if reason is not None:
        return Detail(scored=W.Scored(**base, value=None, reason=reason), **counts)
    if not mu_taken:
        return Detail(scored=W.Scored(**base, value=None, reason="no_logged_probability"), **counts)
    cost, c0 = _window_cost_and_baseline(connection, row, trace, prices=prices, gap_minutes=gap_minutes,
                                         lessons=lessons)
    value = W.score(d_taken=d.get(taken, 0.0), mu_taken=float(mu_taken), uses=uses, cost=cost, cost_baseline=c0)
    return Detail(scored=W.Scored(**base, value=value), cost=cost, cost_baseline=c0, **counts)


#: RO6's landing ruling R10: the classes of a window's terms (:func:`classify_window`)
OBSERVED = "observed"
DESIGN_ZERO = "design_zero"
EXCLUDED_AT_DRAW = "excluded_at_draw"
MISSING = "missing"
#: reasons beside the ledger's own statuses (``checks``: skipped, not answered, displaced, not administered, open,
#: excluded:*)
RO6_NOT_DRAWN = "not_drawn"
RO6_NO_DRAW_DAY = "no_draw_day"
RO6_UNSUPPORTED_AT_DRAW = "unsupported_at_draw"
RO6_COMPLETED = "completed"
RO6_DATED_RESULT = "dated_result"


@dataclass(frozen=True)
class Term:
    """One term of a window's realized return and its class (RO6's landing ruling R10).

    ``observed``: measured (a completed check with its label, a dated use's known result). ``design_zero``: the
    design's own randomization left it unmeasured (a topic the day's check draw did not take, with its logged ``r``):
    inverse weighting covers it. ``excluded_at_draw`` (R7): no check support as of the coin's draw, outside the
    measurable target. ``missing``: its measurement was lost after the draw for a reason that is not the design's
    randomization (a drawn check skipped, unanswered, displaced, not administered, still open, or its grade carrying
    no label; a day with no draw; support lost after the draw; a dated result not known as of the closure)."""

    key: str
    kind: str
    reason: str
    weight: float
    baseline: float
    #: the day's assignment probability (1 for a dated use)
    r: float
    outcome: float | None = None
    dated: bool = False
    #: a missing check term whose topic was drawn that day (its slot exists)
    drawn: bool = False
    assessment: str | None = None

    def bounds(self) -> tuple[float, float]:
        """R1: a missing term's range in the bounded return: performance in ``[0, 1]`` times its weight, less its
        baseline, inverse weighted as the observed term would have been (``1/r`` for a drawn check; a day with no
        draw also admits zero, the topic perhaps not drawn; unweighted where ``r = 0``)."""

        ends = [self.weight * (0.0 - self.baseline), self.weight * (1.0 - self.baseline)]
        if not self.dated and self.r > 0:
            ends = [end / self.r for end in ends]
            if not self.drawn:
                ends.append(0.0)
        return min(ends), max(ends)


def classify_window(connection: Any, row: Mapping[str, Any], trace: Mapping[str, Any], *,
                    resolved: Mapping[tuple[str, str], C.Resolved], r_lookup: Callable[[str], dict[str, float]],
                    exam_result: Callable[[Any, str, str], float | None] | None = None,
                    support: Mapping[str, float] | None = None,
                    drawn: Callable[[str], bool] | None = None) -> list[Term]:
    """RO6's landing ruling R10: THE classification of every term of one decision's window, observed, a design zero,
    excluded at the draw (R7) or missing (:class:`Term`). Every reader of a window's return goes through it: RO5's
    scores and the cross-check through :func:`window_uses`, the stop coin's bounded return through
    :func:`observed_return`.

    Per topic-day ``(L, d)``: with ``support`` (the coin's draw's, R7), a topic with none is excluded. Else the day's
    slot for ``L`` (``resolved``, the ledger as of the closure): completed with a label is observed; any other status
    is missing under that status. With no slot: ``r = 0`` that day is missing (``no_check_support``: support lost
    after the draw); a day with no draw (``drawn(d)`` false: no session that day) is missing (``no_draw_day``);
    otherwise the draw took another topic, a design zero. A dated use: observed with its result known as of the
    closure (``exam_result``), else missing (``dated_missing``)."""

    evaluation = trace.get("evaluation") or {}
    window = int(evaluation.get("window_days") or 14)
    start = date.fromisoformat(str(row["local_date"]))
    terms: list[Term] = []
    for topic in (evaluation.get("uses") or {}).get("topics") or ():
        lo = str(topic["lo"])
        m0 = topic.get("m0") or []
        weight = float(topic.get("c") or 0.0)
        for j in range(1, window + 1):
            day = (start + timedelta(days=j)).isoformat()
            r_assign = float(r_lookup(day).get(lo, 0.0))
            found = resolved.get((day, lo))
            baseline = float(m0[j - 1]) if j - 1 < len(m0) and m0[j - 1] is not None else 0.0
            base = dict(key=f"L:{lo}:{day}", weight=weight, baseline=baseline, r=r_assign)
            if support is not None and float(support.get(lo) or 0.0) <= 0.0:
                terms.append(Term(**base, kind=EXCLUDED_AT_DRAW, reason=RO6_UNSUPPORTED_AT_DRAW))
            elif found is not None and found.status == C.COMPLETED and found.outcome is not None:
                terms.append(Term(**base, kind=OBSERVED, reason=RO6_COMPLETED, outcome=float(found.outcome),
                                  assessment=found.assessment_key()))
            elif found is not None:
                status = found.status if found.status != C.COMPLETED else f"{C.COMPLETED}:no_label"
                terms.append(Term(**base, kind=MISSING, reason=str(status), drawn=True))
            elif r_assign <= 0.0:
                terms.append(Term(**base, kind=MISSING, reason=RO6_NO_CHECK_SUPPORT))
            elif drawn is not None and not drawn(day):
                terms.append(Term(**base, kind=MISSING, reason=RO6_NO_DRAW_DAY))
            else:
                terms.append(Term(**base, kind=DESIGN_ZERO, reason=RO6_NOT_DRAWN))
    read_exam = exam_result if exam_result is not None else _exam_result
    for dated in (evaluation.get("uses") or {}).get("dated") or ():
        on = dated_use_date(trace, row, dated)
        result = read_exam(connection, str(dated["lo"]), on)
        base = dict(key=f"G:{dated['goal_id']}:{dated['lo']}", weight=float(dated.get("omega") or 0.0),
                    baseline=float(dated.get("m0") or 0.0), r=1.0, dated=True)
        if result is None:
            terms.append(Term(**{**base, "key": f"{base['key']}:{on}"}, kind=MISSING, reason=RO6_DATED_MISSING))
        else:
            terms.append(Term(**base, kind=OBSERVED, reason=RO6_DATED_RESULT, outcome=float(result)))
    return terms


def window_uses(connection: Any, row: Mapping[str, Any], trace: Mapping[str, Any], *,
                resolved: Mapping[tuple[str, str], C.Resolved], completion_rate: float | None,
                r_lookup: Callable[[str], dict[str, float]],
                exam_result: Callable[[Any, str, str], float | None] | None = None) -> tuple[list[W.Use], list[str]] | None:
    """RO5's reading of one decision's window (its scores, the cross-check): the frozen uses with what the randomized
    checks observed of them (and the completed assessments' keys), or None when a dated use in the window has no
    imported result (``no_result``). Every term is classified by :func:`classify_window` (R10); here each undated
    use's observation probability is ``r × the pooled completion rate``, RO5's estimator, unchanged.

    ``exam_result(connection, lo, on)``: the dated use's imported result (:func:`score_decision` hands in RO5's
    :func:`_exam_result` through its window's closure; RO6's return reader one that also applies THE availability
    predicate, Codex review of RO6, F5)."""

    rate = float(completion_rate or 0.0)
    uses: list[W.Use] = []
    assessments: list[str] = []
    for term in classify_window(connection, row, trace, resolved=resolved, r_lookup=r_lookup, exam_result=exam_result):
        if term.dated:
            if term.kind != OBSERVED:
                return None
            uses.append(W.Use(key=term.key, weight=term.weight, baseline=term.baseline, r=1.0, observed=True,
                              outcome=term.outcome))
            continue
        observed = term.kind == OBSERVED
        if observed and term.assessment is not None:
            assessments.append(term.assessment)
        uses.append(W.Use(key=term.key, weight=term.weight, baseline=term.baseline, r=term.r * rate,
                          observed=observed, outcome=term.outcome if observed else None))
    return uses, assessments


def _window_cost_and_baseline(connection: Any, row: Mapping[str, Any], trace: Mapping[str, Any], *,
                              prices: Mapping[str, tuple[float, float]], gap_minutes: float,
                              lessons: bool = False) -> tuple[float, float]:
    """``C_i`` over the decision's window and its frozen ``C⁰_i``."""

    evaluation = trace.get("evaluation") or {}
    window = int(evaluation.get("window_days") or 14)
    end = (_parse(str(row["created_at"])) + timedelta(days=window)).strftime(_STAMP)
    own = (float(row.get("kappa0") or 0.0), max(float(row.get("remembered_minutes") or 1.0), 1e-9))
    cost = window_cost(connection, start=str(row["created_at"]), end=end, gap_minutes=gap_minutes, prices=prices,
                       own=own, lessons=lessons)
    return cost, float(evaluation.get("c0") or 0.0)


def observed_return(connection: Any, row: Mapping[str, Any], trace: Mapping[str, Any], *,
                    resolved: Mapping[tuple[str, str], C.Resolved], completion_rate: float | None,
                    r_lookup: Callable[[str], dict[str, float]], prices: Mapping[str, tuple[float, float]],
                    gap_minutes: float,
                    exam_result: Callable[[Any, str, str], float | None] | None = None,
                    complete: bool = False,
                    support: Mapping[str, float] | None = None,
                    drawn: Callable[[str], bool] | None = None,
                    lessons: bool = False) -> tuple[float | None, str | None] | Bounded:
    """RO6 (§10): §8.7's bracket alone for one closed window, ``Σ_u v·(R/r)·(Y − m⁰) − (C − C⁰)``, with no action
    contrast: the observed return a randomized contrast multiplies (the stop coin's, or an importance ratio's).
    ``(None, reason)`` when a dated use has no result or no use has ``r > 0`` (effort alone is no return).
    ``exam_result``: as :func:`window_uses` (:func:`observed_returns` hands in the as-of reader).

    ``complete`` (the stop coin's contrasts; RO6's landing ruling R1, superseding Codex re-review F1's reading): a
    :class:`Bounded` return, every term whose measurement can be missing carried as missing, never as zero. The
    observed terms are the bracket over the uses a check could observe (``r > 0``, the checks' exact assignment
    probabilities) with the dated uses whose result is known as of the window's closure, and the cost (always
    observed). Missing, each bounded by its structural range (performance in ``[0, 1]`` times its known weight, less
    its frozen baseline, :meth:`Term.bounds`): a dated use whose result is not known as of the closure
    (``dated_missing``) and a use no check could observe, ``r = 0`` (``no_check_support``).

    ``support`` (``complete`` only; landing ruling R7): each topic's check support as of the coin's draw
    (:func:`checks.support_at`, or the decision's frozen snapshot). A use whose topic had none is outside the
    measurable target: left out of the return and its bounds (``excluded``), never a missing outcome, since the
    exclusion is fixed before randomization. A use whose topic had support at the draw and none on its day (support
    lost afterwards) stays a bounded missing term. None: no exclusion (an unknown support).

    Landing ruling R10 (``complete``): every term is classified by :func:`classify_window`. The observed terms are
    inverse weighted by the design's own probability alone, ``v·(Y − m⁰)/r`` (a topic the day's draw did not take is
    the design's zero); a check that was drawn but not completed as of the closure (skipped, unanswered, displaced,
    not administered, open, no label), a day with no draw, support lost after the draw and a dated result not known
    are missing terms, each bounded (:meth:`Term.bounds`), never a zero under a pooled completion rate. ``drawn``:
    whether a day had a check draw as of the closure (:class:`AsOf`)."""

    if not complete:
        found_uses = window_uses(connection, row, trace, resolved=resolved, completion_rate=completion_rate,
                                 r_lookup=r_lookup, exam_result=exam_result)
        if found_uses is None:
            return None, W.NO_RESULT
        uses, _assessments = found_uses
        if not any(use.r > 0 for use in uses):
            return None, W.NO_RANDOMIZED_USE
        cost, c0 = _window_cost_and_baseline(connection, row, trace, prices=prices, gap_minutes=gap_minutes,
                                             lessons=lessons)
        return W.score(d_taken=1.0, mu_taken=1.0, uses=uses, cost=cost, cost_baseline=c0), None
    terms = classify_window(connection, row, trace, resolved=resolved, r_lookup=r_lookup, exam_result=exam_result,
                            support=support, drawn=drawn)
    cost, c0 = _window_cost_and_baseline(connection, row, trace, prices=prices, gap_minutes=gap_minutes,
                                         lessons=lessons)
    value = -(cost - c0)
    for term in terms:
        if term.kind == OBSERVED and term.outcome is not None and (term.dated or term.r > 0):
            scale = 1.0 if term.dated else 1.0 / term.r
            value += term.weight * scale * (float(term.outcome) - term.baseline)
    missing = [term for term in terms if term.kind == MISSING]
    counts: dict[str, int] = {}
    for term in missing:
        counts[term.reason] = counts.get(term.reason, 0) + 1
    notes = ";".join(f"{reason}:{count}" for reason, count in sorted(counts.items())) or None
    ranges = [term.bounds() for term in missing]
    return Bounded(value=value, reason=notes, lo=sum(lo for lo, _hi in ranges), hi=sum(hi for _lo, hi in ranges),
                   missing=len(missing), excluded=sum(1 for term in terms if term.kind == EXCLUDED_AT_DRAW),
                   by_reason=dict(sorted(counts.items())))


#: RO6's missing terms of a bounded return (landing ruling R1; :func:`observed_return`'s ``complete``)
RO6_DATED_MISSING = "dated_missing"
RO6_NO_CHECK_SUPPORT = "no_check_support"


@dataclass(frozen=True)
class AsOf:
    """What one closed window's score reads, all as of one :class:`checks.Closure` (landing rulings R1, R11 of RO5;
    R4 of RO6): the resolved checks, the completion rate in its ``r``, each day's assignment probabilities and each
    day's price."""

    closure: C.Closure
    resolved: Mapping[tuple[str, str], C.Resolved]
    rate: float | None
    r_lookup: Callable[[str], dict[str, float]]
    prices: Mapping[str, tuple[float, float]]
    #: R10: whether a day had a check draw as of the closure (None: unknown, every day treated as drawn)
    drawn: Callable[[str], bool] | None = None


def _context(connection: Any, *, at: str | None = None) -> Callable[[str], AsOf]:
    """The as-of reader every closed window's score and return share: ``as_of(closes_at)`` is the window's
    :class:`AsOf`, through the closure at ``closes_at`` (no later than ``at``, the reading moment, when given), over
    one snapshot of the checks' events (:class:`checks.Ledger`) and of the price-source traces, so many closures read
    one log."""

    ledger = C.Ledger(connection)
    price_rows = _price_rows(connection)
    by_closure: dict[str, AsOf] = {}

    def as_of(closes_at: str) -> AsOf:
        cut = min(str(closes_at), str(at)) if at is not None else str(closes_at)
        if cut not in by_closure:
            closure = C.Closure.at(cut)
            resolved = {(entry.local_date, entry.topic): entry for entry in ledger.resolve(closure)}
            rate = ledger.completion(closure).get("rate")
            cache: dict[str, tuple[dict[str, float], str]] = {}

            def read(day: str, closure: C.Closure = closure, cache: dict = cache) -> tuple[dict[str, float], str]:
                if day not in cache:
                    cache[day] = ledger.r_for(day, closure) if day <= closure.local_date else ({}, "none")
                return cache[day]

            def r_lookup(day: str, read: Callable = read) -> dict[str, float]:
                return read(day)[0]

            def drawn(day: str, read: Callable = read) -> bool:
                return read(day)[1] == "drawn"

            by_closure[cut] = AsOf(closure=closure, resolved=resolved, rate=rate, r_lookup=r_lookup,
                                   prices=_day_prices(connection, closure, price_rows), drawn=drawn)
        return by_closure[cut]

    def support_at(decided_at: str) -> dict[str, float]:
        """R7: each topic's check support as of a decision's draw, over the same snapshot."""

        return C.support_at(connection, decided_at, days=ledger.days)[0]

    as_of.support_at = support_at  # type: ignore[attr-defined]
    return as_of


def frozen_support(trace: Mapping[str, Any]) -> Mapping[str, float] | None:
    """R7: the check support a decision froze at its draw (``residual.measurable.support``), or None."""

    residual = trace.get("residual") if isinstance(trace.get("residual"), Mapping) else {}
    measurable = residual.get("measurable") if isinstance(residual.get("measurable"), Mapping) else {}
    support = measurable.get("support")
    return {str(lo): float(r) for lo, r in support.items()} if isinstance(support, Mapping) else None


def observed_returns(connection: Any, config: Any, *, at: str, rows: Sequence[Mapping[str, Any]],
                     complete: bool = False) -> dict[str, Any]:
    """RO6: :func:`observed_return` for each of ``rows`` (a trace's columns with its parsed ``trace``) whose window
    closed before ``at``, keyed by decision id. Each reads as of its own window's closure, as :func:`scores` does
    (RO6's landing ruling R4 on RO5's R1 and R11: the checks, the completion rate, the assignment probabilities and
    the daily prices), and an imported result counts only once THE availability predicate admits it by ``at`` and the
    closure admits it on its occurrence and received time (:func:`exam_result_known`; Codex review of RO6, F5; RO5's
    landing ruling R10: an import that arrives after the window closed is never that window's).
    ``complete``: as :func:`observed_return` (the stop coin's contrasts: each value a :class:`Bounded`; else a
    ``(value, reason)`` pair), with each decision's check support as of its draw (R7): the support it froze
    (:func:`frozen_support`), else :func:`checks.support_at` as of its moment."""

    closed = [row for row in rows if row.get("window_closes_at") and str(row["window_closes_at"]) < at]
    if not closed:
        return {}
    as_of = _context(connection, at=at)
    support_at = getattr(as_of, "support_at", None)
    gap = float(config.router_objective.session_gap_minutes)
    lessons = _lessons_on(config)
    out: dict[str, Any] = {}
    for row in closed:
        found = as_of(str(row["window_closes_at"]))

        def known(conn: Any, lo: str, on: str, closure: C.Closure = found.closure) -> float | None:
            return exam_result_known(conn, config, lo, on, at, closure)

        support = None
        if complete:
            support = frozen_support(row["trace"])
            if support is None and support_at is not None:
                support = support_at(str(row["created_at"]))
        out[str(row["decision_id"])] = observed_return(
            connection, row, row["trace"], resolved=found.resolved, completion_rate=found.rate,
            r_lookup=found.r_lookup, prices=found.prices, gap_minutes=gap, exam_result=known, complete=complete,
            support=support, drawn=found.drawn, lessons=lessons)
    return out


def _lessons_on(config: Any) -> bool:
    """Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): the objective's clock counts lessons' active minutes (its tag and
    switch: ``router_objective_switches.lesson_offers_on``); off, or below the tag, the predecessor's clock."""

    from learnloop.router_objective_switches import lesson_offers_on

    return lesson_offers_on(config)


def scores(connection: Any, config: Any, *, at: str) -> list[Detail]:
    """Every decision's score from the traces whose windows closed before ``at`` (no peeking), RO5's checks the
    observations. Each score reads as of its own window's closure (landing rulings R1, R11, :class:`checks.Closure`):
    the checks it observes, the completion rate in its ``r``, the assignment probabilities, the dated uses' results
    and the daily prices its cost charges,
    every event through the one cutoff, so a closed score never moves with later data (a grade's later hold or
    regrade aside, as the closure names)."""

    if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'router_objective_traces'"
                          ).fetchone() is None:
        return []
    # Landing ruling R11: the daily prices a score charges stand as of its window's closure (built per closure from
    # one read of the price-source traces); the activity they price stays on occurrence time (R10).
    as_of = _context(connection)
    gap = float(config.router_objective.session_gap_minutes)
    lessons = _lessons_on(config)
    out: list[Detail] = []
    for row in connection.execute(
            "SELECT decision_id, created_at, window_closes_at, local_date, llm_status, numeric_status, kappa0, "
            "remembered_minutes, trace_json FROM router_objective_traces WHERE decision_kind = 'plan_block' AND "
            "window_closes_at IS NOT NULL AND window_closes_at < ? ORDER BY created_at, id", (at,)):
        record = dict(row)
        trace = json.loads(record.pop("trace_json"))
        found = as_of(str(record["window_closes_at"]))
        out.append(score_decision(connection, record, trace, resolved=found.resolved, completion_rate=found.rate,
                                  r_lookup=found.r_lookup, prices=found.prices, gap_minutes=gap,
                                  closure=found.closure, lessons=lessons))
    return out


__all__ = ["AsOf", "Bounded", "DESIGN_ZERO", "Detail", "EXCLUDED_AT_DRAW", "MISSING", "OBSERVED", "RO6_DATED_MISSING",
           "RO6_NO_CHECK_SUPPORT", "RO6_NO_DRAW_DAY", "RO6_NOT_DRAWN", "RO6_UNSUPPORTED_AT_DRAW", "Term", "VERSION",
           "WindowSession", "classify_window", "dated_use_date", "exam_result_known", "goal_date", "observed_return",
           "observed_returns", "score_decision", "scores", "window_cost", "window_uses"]
