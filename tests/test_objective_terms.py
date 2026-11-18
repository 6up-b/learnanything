"""The router's objective with plain values: each term's contribution to a path's value, what the trace reports of
them, and how a candidate's value and the numeric policy's choice read them (``router_objective/objective.py``).

No vault, no rollout: ledgers are built from literals (binary fractions, so every sum is exact) and every expected
number is worked by hand.
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from learnloop.router_objective import objective as OBJ

#: A term's sign in ``q``: rewards add, attention costs subtract; ``unmeasured`` is a share kept apart, not a term.
SIGNS = {"crossed": 1.0, "undated_action": 1.0, "kappa_action": -1.0, "tail_reward": 1.0, "tail_cost": -1.0,
         "terminal_reward": 1.0, "terminal_cost": -1.0, "unmeasured": 0.0}


def _ledger(**fields: list[float]) -> OBJ._Ledger:
    k = len(next(iter(fields.values()))) if fields else 1
    return OBJ._Ledger(**{name: np.array(fields.get(name, [0.0] * k), dtype=np.float64)
                          for name in OBJ._LEDGER_FIELDS})


def _path() -> OBJ._Ledger:
    return _ledger(crossed=[0.5, 0.25], undated_action=[0.25, 0.5], kappa_action=[0.125, 0.0625],
                   tail_reward=[1.0, 2.0], tail_cost=[0.25, 0.5], terminal_reward=[0.75, 0.25],
                   terminal_cost=[0.125, 0.125], unmeasured=[0.0625, 0.1875])


def test_the_ledger_holds_every_term_and_nothing_else():
    assert set(SIGNS) == set(OBJ._LEDGER_FIELDS)


@pytest.mark.parametrize("term", sorted(SIGNS))
def test_each_term_contributes_with_its_sign_and_only_through_q(term):
    alone = _ledger(**{term: [3.0, 0.0]})
    assert alone.q.tolist() == [3.0 * SIGNS[term], 0.0]


def test_a_paths_value_is_its_rewards_minus_its_attention_costs():
    path = _path()
    # draw 0: 0.5 + 0.25 - 0.125 + 1.0 - 0.25 + 0.75 - 0.125; draw 1: 0.25 + 0.5 - 0.0625 + 2.0 - 0.5 + 0.25 - 0.125
    assert path.q.tolist() == [2.0, 2.3125]
    # T_C, the net continuation past the cutoff, and E[V(x')], the tail from the action's end with T_C
    assert path.terminal.tolist() == [0.625, 0.125]
    assert path.after.tolist() == [1.375, 1.625]


def test_the_trace_reports_each_terms_mean_in_a_fixed_order():
    terms = OBJ._terms(_path())
    assert list(terms) == ["crossed_date_reward", "undated_reward", "kappa_integral", "after", "tail_reward",
                           "tail_cost", "terminal"]
    assert terms == {"crossed_date_reward": 0.375, "undated_reward": 0.375, "kappa_integral": 0.09375,
                     "after": 1.5, "tail_reward": 1.5, "tail_cost": 0.375, "terminal": 0.375}
    # The unmeasured share is reported only when the decision kept it apart, and is never added to q.
    kept = OBJ._terms(_path(), SimpleNamespace(unmeasured=frozenset({"lo_a"})))
    assert list(kept)[-1] == "unmeasured_reward" and kept["unmeasured_reward"] == 0.125
    assert "unmeasured_reward" not in OBJ._terms(_path(), SimpleNamespace(unmeasured=None))


def test_a_candidates_value_is_the_mean_of_its_draws_and_v_is_the_reference_rows():
    row = OBJ.Valued(ref="a", kind="review", q_draws=tuple(_path().q.tolist()), terms=OBJ._terms(_path()), extra={},
                     choosable=True)
    assert row.q == 2.15625
    reference = OBJ.Valued(ref="tail_next", kind="review", q_draws=(1.0, 1.5), terms={}, extra={}, choosable=False)
    evaluation = OBJ.Evaluation(valued=(row,), draws=2, cutoff=7.0, seed="s", elapsed_ms=0, complete=True,
                                reference=reference)
    assert evaluation.v == 1.25
    assert OBJ.Evaluation(valued=(row,), draws=2, cutoff=7.0, seed="s", elapsed_ms=0, complete=True).v == 0.0


def test_the_numeric_policy_takes_the_argmax_and_breaks_ties_within_the_paired_precision_by_support_order():
    def row(ref, draws):
        return OBJ.Valued(ref=ref, kind="review", q_draws=draws, terms={}, extra={}, choosable=True)

    # a - b per draw: (0.5, -0.5): mean 0, sample sd 1/sqrt(2), so the paired precision is 0.5
    a, b, c = row("a", (1.5, 0.5)), row("b", (1.0, 1.0)), row("c", (0.0, 0.0))
    assert OBJ.paired_standard_error(a, b) == pytest.approx(0.5, rel=1e-15)
    evaluation = OBJ.Evaluation(valued=(a, b, c), draws=2, cutoff=7.0, seed="s", elapsed_ms=0, complete=True)
    chosen, tie = OBJ.numeric_choice(evaluation, ["b", "a", "c"])
    assert chosen == "b" and tie["tied"] == ["b", "a"] and tie["top_two"] == ["b", "a"]
    assert tie["paired_se_top_two"] == pytest.approx(0.5, rel=1e-15)
    # c is a full point below a, outside their paired precision (0.5 again): never chosen by the tie rule
    assert OBJ.numeric_choice(evaluation, ["c", "a"])[0] == "a"
