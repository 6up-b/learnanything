"""What the router's numeric policy optimizes (spec_router_objective_v1 §3): the terms of one path, their sum, and
how a candidate's value is reported.

**The objective in plain words.** At a decision, each candidate action is valued as the cold performance it buys at
the learner's valued uses of what they study, minus the attention it costs, up to one cutoff ``C`` shared by every
candidate (the horizon, or the latest goal date if further) and, once, a horizon past it. Rewards are valued uses:
a goal's dated use of a topic scored at its date, and each topic's undated uses at a constant daily density. The
cost is the attention price, which rises with the session's active minutes. Every amount is in use-equivalents.
Per parameter draw, a candidate's value is its path's ``q`` (:attr:`_Ledger.q`)::

    q = crossed + undated_action − kappa_action + tail_reward − tail_cost + terminal_reward − terminal_cost

**The terms** (the fields of :class:`_Ledger`, each a use-equivalent per draw; :mod:`rollouts` accrues them):

- ``crossed`` rewards each dated use that falls during the action: its weight ``ω`` times the chance of performing
  it at its date, on the state before the action's effect. From the goals' dated uses (``Inputs.dated``) and the
  memory forecast (``memory.perform`` over AD's ability and FSRS's retrievability). ``_Model._segment``.
- ``undated_action`` rewards undated uses during the action before ``C``: each topic's daily density ``c_L`` times
  its chance of performing, times the days the action takes. From ``Topic.undated_density`` (the goals' contract)
  and the memory forecast. ``_Model._segment``.
- ``kappa_action`` charges the attention price over the action's active minutes before ``C``:
  ``κ0·((m + d)² − m²)/(2m̄)`` from session minute ``m`` for ``d`` minutes. From ``Inputs.price`` (``κ0``, the
  day's price; ``m̄``, the plan's remembered minutes) and ``Inputs.session_minutes``. ``_Model._segment`` through
  ``_Model.cost``.
- ``tail_reward`` rewards the valued uses, dated and undated, from the action's end to ``C`` under the tail (the
  continuation the rollouts simulate). Same inputs as the two rewards above. ``_Model.run_tail``,
  ``_Model._score_dated``.
- ``tail_cost`` charges the attention price of the tail's sessions that start before ``C``. ``_Model._session``.
- ``terminal_reward`` and ``terminal_cost`` (``T_C``, the net continuation, valued once) reward the undated uses
  and charge the attention price from ``C`` to ``C + H``, the action's own minutes past ``C`` included.
  ``_Model._segment``, ``_Model.run_tail``, ``_Model._session``.
- ``unmeasured`` is not a term of ``q``: the share of the undated rewards above from the topics the decision was
  told no randomized check can measure, kept apart on the same paths for the learned tail.

**What is reported.** :func:`_terms` gives each term's mean over the draws (what the trace records per candidate);
:class:`Valued` holds a candidate's draws of ``q`` and its ``Q̄`` (their mean); :class:`Evaluation` holds every
candidate's and the reference row's (``V``, the tail's next action's ``Q̄``); :func:`numeric_choice` is ``π_Q``,
the argmax of ``Q̄`` with ties within :func:`paired_standard_error` broken by support order.

**Order.** This module imports nothing of LearnLoop. :mod:`rollouts` imports it: it accumulates every path into a
``_Ledger``, compares branches inside one candidate's simulation by ``q``, and builds each :class:`Valued` row from
the definitions here (``rollouts.evaluate``), so this module cannot import the rollouts.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math
from typing import Any

import numpy as np

OBJECTIVE_VERSION = "router_objective_v1"
TERMINAL_VERSION = "net_continuation_v1"


_LEDGER_FIELDS = ("crossed", "undated_action", "kappa_action", "tail_reward", "tail_cost", "terminal_reward",
                  "terminal_cost", "unmeasured")


@dataclass
class _Ledger:
    """Per draw: the terms of one path (§8.8's per-candidate terms)."""

    crossed: np.ndarray        # dated uses crossed during the action
    undated_action: np.ndarray  # undated uses during the action
    kappa_action: np.ndarray    # the action's κ integral (a cost, positive)
    tail_reward: np.ndarray     # valued uses from the action's end to C
    tail_cost: np.ndarray       # the tail's attention cost to C
    terminal_reward: np.ndarray  # valued uses past C (T_C's reward)
    terminal_cost: np.ndarray    # attention cost past C (T_C's cost)
    #: RO6's landing ruling R7: the part of the undated uses' reward (inside ``undated_action``, ``tail_reward`` and
    #: ``terminal_reward``) from the topics the model was told are unmeasured, on the same paths; not added to ``q``
    #: again (zero unless :class:`_Model` has ``unmeasured``)
    unmeasured: np.ndarray

    @classmethod
    def zeros(cls, k: int) -> "_Ledger":
        return cls(*(np.zeros(k) for _ in _LEDGER_FIELDS))

    def copy(self) -> "_Ledger":
        return _Ledger(*(np.array(getattr(self, name), copy=True) for name in _LEDGER_FIELDS))

    @property
    def q(self) -> np.ndarray:
        return (self.crossed + self.undated_action - self.kappa_action + self.tail_reward - self.tail_cost
                + self.terminal_reward - self.terminal_cost)

    @property
    def terminal(self) -> np.ndarray:
        return self.terminal_reward - self.terminal_cost

    @property
    def after(self) -> np.ndarray:
        """``E[V(x′)]``: the tail from the action's end, ``T_C`` included."""

        return self.tail_reward - self.tail_cost + self.terminal

    @staticmethod
    def mix(p: np.ndarray, a: "_Ledger", b: "_Ledger") -> "_Ledger":
        return _Ledger(*(p * getattr(a, n) + (1 - p) * getattr(b, n) for n in _LEDGER_FIELDS))

    @staticmethod
    def select(mask: np.ndarray, a: "_Ledger", b: "_Ledger") -> "_Ledger":
        return _Ledger(*(np.where(mask, getattr(a, n), getattr(b, n)) for n in _LEDGER_FIELDS))


@dataclass(frozen=True)
class Valued:
    """One candidate's value (§8.8's terms)."""

    ref: str
    kind: str
    q_draws: tuple[float, ...]
    terms: Mapping[str, float]
    extra: Mapping[str, Any]
    choosable: bool

    @property
    def q(self) -> float:
        return float(np.mean(self.q_draws)) if self.q_draws else 0.0


@dataclass(frozen=True)
class Evaluation:
    valued: tuple[Valued, ...]
    draws: int
    cutoff: float
    seed: str
    elapsed_ms: int
    complete: bool
    reference: Valued | None = None

    def by_ref(self) -> dict[str, Valued]:
        return {v.ref: v for v in self.valued}

    @property
    def v(self) -> float:
        """``V = Σ_a π_tail(a)·Q(a)``: the tail's next action is deterministic, so ``V`` is its row's ``Q``."""

        return self.reference.q if self.reference is not None else 0.0


def _terms(ledger: _Ledger, model: Any = None) -> dict[str, float]:
    terms = {
        "crossed_date_reward": float(ledger.crossed.mean()),
        "undated_reward": float(ledger.undated_action.mean()),
        "kappa_integral": float(ledger.kappa_action.mean()),
        "after": float(ledger.after.mean()),
        "tail_reward": float(ledger.tail_reward.mean()),
        "tail_cost": float(ledger.tail_cost.mean()),
        "terminal": float(ledger.terminal.mean()),
    }
    if model is not None and model.unmeasured is not None:
        # RO6's landing ruling R7: the unmeasured topics' share of q (the measurable part is q minus it).
        terms["unmeasured_reward"] = float(ledger.unmeasured.mean())
    return terms


def paired_standard_error(a: Valued, b: Valued) -> float:
    """The standard error of ``Q̄(a) − Q̄(b)`` over the shared draws (common random numbers)."""

    x = np.asarray(a.q_draws) - np.asarray(b.q_draws)
    if x.size < 2:
        return 0.0
    return float(np.std(x, ddof=1) / math.sqrt(x.size))


def numeric_choice(evaluation: Evaluation, support: Sequence[str]) -> tuple[str, dict[str, Any]]:
    """``π_Q`` (§8.3): plain argmax of ``Q̄``; candidates within the paired precision of the maximum are broken
    by support order (staged's pick first). Returns the choice and the record of the tie rule."""

    rows = evaluation.by_ref()
    ranked = [ref for ref in support if ref in rows]
    if not ranked:
        raise ValueError("no valued candidate in the support")
    best = max(ranked, key=lambda ref: rows[ref].q)
    tied = [ref for ref in ranked
            if ref == best or rows[best].q - rows[ref].q <= paired_standard_error(rows[best], rows[ref]) + 1e-15]
    chosen = next(ref for ref in ranked if ref in tied)
    order = sorted(ranked, key=lambda ref: -rows[ref].q)
    top_two = order[:2]
    precision = paired_standard_error(rows[top_two[0]], rows[top_two[1]]) if len(top_two) == 2 else 0.0
    return chosen, {"argmax": best, "tied": tied, "chosen": chosen, "top_two": top_two,
                    "paired_se_top_two": precision, "rule": "argmax_qbar_ties_within_paired_se_by_support_order"}


__all__ = ["OBJECTIVE_VERSION", "TERMINAL_VERSION", "Evaluation", "Valued", "numeric_choice", "paired_standard_error"]
