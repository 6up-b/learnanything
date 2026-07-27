"""Servability: an authored instrument the surface cannot render is not served.

Spec: ``spec_measurement_efficiency_v1.md`` §3.A2/§3.A3; implementation plan item
6.4 and the Stage 6 adversarial review.

The defect these pin is not a crash. An error hunt's whole stimulus is its worked
solution and a laddered stem's is its shared setup; neither reaches the practice
DTO yet, while the authoring prompts actively commission both. Serving one
produces a *silent* failure: the learner is asked to repair work they cannot see,
the grader (which does receive the solution) marks every plant missed, and the
projection banks negative facet mass for a repair the learner was never shown the
material to make. A harmful write manufactured by the serving path.

Two halves, and the second is the one the review added: the refusal must be
VISIBLE. A queue filter nobody can see is indistinguishable from a bug — the item
exists, passes every gate, and simply never appears, while the instrument audit
reports zero attempts forever without saying why.
"""

from __future__ import annotations

import pytest

from learnloop.services.instrument_serving import (
    UNSERVABLE_REMEDIES,
    UnservableReason,
    unservable_reason,
)


class _Item:
    """The two fields the predicate reads, and nothing else."""

    def __init__(self, *, error_hunt=None, laddered_stem=None) -> None:
        self.id = "pi_1"
        self.error_hunt = error_hunt
        self.laddered_stem = laddered_stem


def test_an_ordinary_item_is_servable():
    assert unservable_reason(_Item()) is None


def test_an_error_hunt_is_refused_with_its_own_reason():
    reason = unservable_reason(_Item(error_hunt=object()))
    assert reason == "error_hunt_solution_not_rendered"
    assert "worked_solution_md" in UNSERVABLE_REMEDIES[reason]


def test_a_laddered_stem_part_is_refused_with_its_own_reason():
    reason = unservable_reason(_Item(laddered_stem=object()))
    assert reason == "laddered_stem_stimulus_not_rendered"
    assert "stimulus_md" in UNSERVABLE_REMEDIES[reason]


def test_an_item_carrying_both_contracts_is_refused_once():
    """Reporting one reason is enough to keep it out; both would be redundant."""

    assert unservable_reason(_Item(error_hunt=object(), laddered_stem=object())) == (
        "error_hunt_solution_not_rendered"
    )


def test_every_arm_states_a_remedy():
    """A refusal without a remedy is a dead end.

    This is the guard against the filter quietly growing a third arm that the
    doctor warning then renders as a KeyError instead of an explanation.
    """

    arms = set(UnservableReason.__args__)  # type: ignore[attr-defined]
    assert set(UNSERVABLE_REMEDIES) == arms
    for arm in arms:
        assert UNSERVABLE_REMEDIES[arm].strip()


def test_the_predicate_ignores_unrelated_attributes():
    """Duck-typed on purpose: both call sites hold a `PracticeItem`, but the
    predicate must stay dependency-free so the scheduler and the exam pool can
    each import it without importing the other."""

    class _Bare:
        id = "pi_bare"

    assert unservable_reason(_Bare()) is None


@pytest.mark.parametrize("field", ["error_hunt", "laddered_stem"])
def test_an_explicitly_absent_contract_is_servable(field: str):
    """`None` means "this item is not that instrument", not "unknown"."""

    assert unservable_reason(_Item(**{field: None})) is None
