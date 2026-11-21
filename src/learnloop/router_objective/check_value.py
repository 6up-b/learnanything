"""The successor's value of a lesson's committed delayed checks (spec_teacher_v2 §7.4): a check happens only when the
simulated learner returns, costs its minutes on that session's clock, and is answered only as often as checks like it
are answered cold. Unserved: nothing under ``src`` calls :func:`evaluate`; the activation at ``mvp-0.62`` wires it.

**What differs from the rollouts' own pricing** (:mod:`rollouts`, which still prices every served decision and refuses
the typed checks this path reads). There a committed check (``Action.commitments``, ``(LO, days)``) is a full graded
practice attempt at the first day boundary at or past its date, whether or not the learner returns, with no minutes,
its outcome from one of eight shared columns. Here a lesson's :class:`types.CheckCommitment`:

1. is delivered or not once per path: its propensity drawn from its delivery posterior (the stream
   ``theta:commit_delivery:<group>``, shared by the checks of one fitted group; an endpoint is its point mass, never a
   Beta with a zero shape), then its own Bernoulli (``noise:commit_delivery:<key>``). An undelivered check is no event
   at all: no dose, no information, no minutes;
2. comes due at the action's sampled end plus its delay, as before, and waits for a simulated return on or after
   that (the tail's own return mask); a check due on day 3.01 is answered on the first return from day 4 on;
3. on a return day, the due, delivered, unanswered checks are taken in due order (then key) while they fit the
   session's remaining remembered minutes, the plan's own admission rule for a "Check once" (a check that does not
   fit waits for a later return; nothing is answered for free);
4. each runs on the session's clock from the minutes already used: its attention cost ``κ0·((m+d)² − m²)/(2m̄)``,
   split at ``C`` into the tail's cost and ``T_C``'s, and clipped at ``C + H`` (only in-window minutes are charged, and
   a check that would end past the horizon has no answer effect); a dated use its end crosses is scored on the state
   before it, as a tail block's is; then one mass-1 practice attempt at its end, its outcome from its own stream
   (``noise:commit_outcome:<key>``), a wrong answer learning as any practice does;
5. the day's tail session then starts at the minutes and time the checks left, so checks displace tail practice
   rather than being added after a full session.

Undated uses on a check's day are integrated as the tail integrates every day's (its pieces, on the state after the
day's session): the same as for the tail block the check displaces. A return model's first gap depends on today's
session only, and a check is never answered on the decision's own day, so the return draws are untouched.

Every stream is one ``K``-draw array per name, so another commitment, a reordering, or refining ``K`` to ``2K`` keeps
each stream's prefix. An action with no typed checks takes the rollouts' own tail exactly, draw for draw.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Collection, Sequence
from dataclasses import replace
from typing import Any

import numpy as np

from learnloop.router_objective.objective import Evaluation, _Ledger
from learnloop.router_objective.rollouts import (
    MINUTES_PER_DAY,
    _beta_draw,
    _carries,
    _evaluate,
    _Model,
    _seed_int,
    _State,
)
from learnloop.router_objective.types import Action, CheckCommitment, Inputs

#: This path's rule (a changed rule is a new version).
POLICY_VERSION = "committed_check_rollout_v1"
#: How its streams are named and drawn (a changed layout moves every check's draws).
STREAM_LAYOUT_VERSION = "commitment_streams_v1"
#: The plan's admission tolerance for a "Check once" (``daily_plan.engine._EPS``, minutes): a check fits when its
#: minutes are within it of the session's remaining budget. The plan's own number, kept equal by a test; the
#: objective's package cannot import the plan.
FIT_TOLERANCE_MINUTES = 1e-6
_UNTYPED = "untyped commitments have no delivery or minutes: this path prices typed checks only"


def uniforms(seed: str, name: str, draws: int) -> np.ndarray:
    """The named stream's ``draws`` uniforms (one array per name: a longer one extends a shorter one's prefix)."""

    return np.random.default_rng(_seed_int(seed, name)).random(int(draws))


def propensity(u: np.ndarray, delivery: tuple[float, float]) -> np.ndarray:
    """The delivery posterior's draw at ``u``: the Beta quantile, or the point mass at an endpoint."""

    alpha, beta = (float(value) for value in delivery)
    if alpha == 0.0:
        return np.zeros_like(u)
    if beta == 0.0:
        return np.ones_like(u)
    return _beta_draw(u, alpha, beta)


class _Check:
    """One typed check on one path: its topic, due time, minutes, whether it is delivered, its outcome draws."""

    def __init__(self, model: _Model, check: CheckCommitment, at: np.ndarray) -> None:
        self.check = check
        self.lo = model.index[check.lo]
        self.due = np.asarray(at, dtype=np.float64) + float(check.days)
        self.minutes = float(check.minutes)
        p = propensity(uniforms(model.seed, f"theta:commit_delivery:{check.group}", model.k), check.delivery)
        self.delivered = uniforms(model.seed, f"noise:commit_delivery:{check.key}", model.k) < p
        self.outcome_u = uniforms(model.seed, f"noise:commit_outcome:{check.key}", model.k)
        self.taken = np.zeros(model.k, dtype=bool)
        #: per draw, when it was answered (NaN: not answered); for the record and the tests
        self.answered_at = np.full(model.k, np.nan)


class _CheckModel(_Model):
    """The rollouts' model with typed checks executed on simulated returns (the module docstring's rule)."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        #: the last path's state after its tail and its checks (for :func:`simulate`)
        self.tail_state: _State | None = None
        self.tail_checks: tuple[_Check, ...] = ()

    def _screen(self, action: Action) -> None:
        if _carries(action, lambda part: part.diagnostic is not None):
            raise ValueError("a diagnostic payload is priced by diagnostic_value.evaluate_probe, not the rollouts")
        if _carries(action, lambda part: bool(part.commitments)):
            raise ValueError(_UNTYPED)

    def _tail(self, state: _State, ledger: _Ledger, action: Action, *, at: np.ndarray, spent: np.ndarray,
              dated_done: np.ndarray) -> None:
        if action.commitments:
            raise ValueError(_UNTYPED)
        checks = tuple(sorted((_Check(self, check, at) for check in action.checks if check.lo in self.index),
                              key=lambda item: (float(item.check.days), item.check.key)))
        on_return = self._on_return(state, ledger, checks) if checks else None
        self.run_tail(state, ledger, today_minutes=float(self.inputs.session_minutes) + spent, after=at,
                      dated_done=dated_done, on_return=on_return)
        self.tail_state, self.tail_checks = state, checks

    def _on_return(self, state: _State, ledger: _Ledger, checks: Sequence[_Check]) -> Callable[..., Any]:
        k = self.k

        def on_return(day: int, returning: np.ndarray,
                      before_block: Callable[[np.ndarray, np.ndarray], None]) -> tuple[np.ndarray, np.ndarray]:
            day_start = float(day)
            used = np.zeros(k)
            for item in checks:
                due = returning & item.delivered & ~item.taken & (item.due <= day_start + 1e-9)
                go = due & (used + item.minutes <= self.mbar + FIT_TOLERANCE_MINUTES)
                if not go.any():
                    continue
                start = day_start + used / MINUTES_PER_DAY
                finish = start + item.minutes / MINUTES_PER_DAY
                # Only the minutes inside the window are charged; those before C are the tail's, the rest T_C's.
                inside = np.clip((self.end - start) * MINUTES_PER_DAY, 0.0, item.minutes)
                before_c = np.clip((self.cutoff - start) * MINUTES_PER_DAY, 0.0, inside)
                ledger.tail_cost += np.where(go, self.cost(used, before_c), 0.0)
                ledger.terminal_cost += np.where(go, self.cost(used + before_c, inside - before_c), 0.0)
                answered = go & (finish <= self.end + 1e-12)
                before_block(finish, answered)
                self._practice(state, item.lo, finish, item.outcome_u, answered, 1.0)
                item.answered_at = np.where(answered, finish, item.answered_at)
                item.taken |= go
                used = np.where(go, used + inside, used)
            return used, day_start + used / MINUTES_PER_DAY

        return on_return


def evaluate(inputs: Inputs, actions: Sequence[Action], *, draws: int, seed: str, max_draws: int | None = None,
             keep_going: Callable[[], bool] | None = None, deadline: float | None = None,
             clock: Callable[[], float] = time.monotonic, on_complete: Callable[[Evaluation], None] | None = None,
             cutoff: float | None = None, unmeasured: Collection[str] | None = None, merged_sessions: bool = False,
             consistent_review_draw: bool = False, held_ad_link: bool = False) -> Evaluation:
    """``rollouts.evaluate`` with typed committed checks priced by this module's rule (its arguments, its loop, its
    refinement and its reference row); an action with no typed checks gets exactly the rollouts' value."""

    options = {"merged_sessions": merged_sessions, "consistent_review_draw": consistent_review_draw,
               "held_ad_link": held_ad_link}
    return _evaluate(lambda total: _CheckModel(inputs, total, seed, cutoff=cutoff, unmeasured=unmeasured, **options),
                     actions, draws=draws, seed=seed, max_draws=max_draws, keep_going=keep_going, deadline=deadline,
                     clock=clock, on_complete=on_complete)


def simulate(inputs: Inputs, action: Action, *, draws: int, seed: str, **options: Any
             ) -> tuple[_Ledger, _State, tuple[np.ndarray, ...]]:
    """One action's own path (no offer mixing: an offer's accepted branch is the action without ``accept``): its
    ledger, the state after its tail, and each typed check's answer time per draw (NaN: not answered), in due order."""

    model = _CheckModel(inputs, int(draws), seed, **options)
    action = replace(action, accept=None)
    model._screen(action)
    ledger, _effect, _minutes = model._do(action)
    assert model.tail_state is not None
    return ledger, model.tail_state, tuple(item.answered_at for item in model.tail_checks)


__all__ = ["FIT_TOLERANCE_MINUTES", "POLICY_VERSION", "STREAM_LAYOUT_VERSION", "evaluate", "propensity", "simulate",
           "uniforms"]
