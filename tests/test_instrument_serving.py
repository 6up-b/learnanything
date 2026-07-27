"""Servability, after the retirement: the seam stays, the two arms are gone.

Spec: ``spec_measurement_efficiency_v1.md`` §3.A2/§3.A3; implementation plan item
6.4 and the Stage 6 adversarial review, whose fix these tests used to pin.

WHAT CHANGED AND WHY THESE TESTS ARE INVERTED. The predicate refused two
instrument classes outright — every error hunt (§3.A3) and every laddered-stem
part (§3.A2) — because the serving surface carried neither stimulus, and serving
one produced a *silent* failure: the learner asked to repair work they cannot
see, the grader (which does receive the solution) marking every plant missed, and
the projection banking negative facet mass for a repair nobody was shown the
material to make.

That fact is now false. ``handlers/serializers.item_presentation`` emits
``laddered_stem_stimulus`` and ``error_hunt_worked_solution`` blocks, and
``components/ItemPresentation.tsx`` renders them on the practice, exam and
golden-path surfaces. The module docstring named exactly one legitimate way to
remove the filter — "make the fact false: render the stimulus, then delete the
arm here" — so the arms are deleted, and these tests, which existed to make that
deletion visible, now assert the other half of the same claim: both classes are
servable, and the seam every boundary calls is still there for the next class
that ships ahead of its renderer.

The data-level check is NOT retired and is not tested here: whether a particular
item carries non-blank content lives in ``item_presentation`` (see
``tests/test_sidecar_item_presentation.py`` and the blank-content journeys), and
it is a fact about the item, not about the class.
"""

from __future__ import annotations

import pytest

from learnloop.services.instrument_serving import (
    UNSERVABLE_ERROR_CODE,
    UNSERVABLE_REMEDIES,
    UnservableReason,
    unservable_reason,
    unservable_refusal,
)


def _arms() -> set[str]:
    """The declared vocabulary, empty while :data:`UnservableReason` is ``Never``."""

    return set(getattr(UnservableReason, "__args__", ()))


class _Item:
    """The two fields the predicate used to read, and nothing else."""

    def __init__(self, *, error_hunt=None, laddered_stem=None) -> None:
        self.id = "pi_1"
        self.error_hunt = error_hunt
        self.laddered_stem = laddered_stem


def test_an_ordinary_item_is_servable():
    assert unservable_reason(_Item()) is None


def test_an_error_hunt_is_servable_now_that_the_worked_solution_renders():
    """§3.A3's arm, retired. The presentation payload carries the solution and
    the surface frames it, so the class is no longer a reason to refuse."""

    assert unservable_reason(_Item(error_hunt=object())) is None
    assert unservable_refusal(_Item(error_hunt=object())) is None


def test_a_laddered_stem_part_is_servable_now_that_the_stimulus_renders():
    """§3.A2's arm, retired. Every part carries the shared setup it climbs, so a
    part met days after part 1 is answerable on its own."""

    assert unservable_reason(_Item(laddered_stem=object())) is None
    assert unservable_refusal(_Item(laddered_stem=object())) is None


def test_an_item_carrying_both_contracts_is_servable():
    assert unservable_reason(_Item(error_hunt=object(), laddered_stem=object())) is None


def test_the_predicate_currently_declares_no_arms():
    """The retirement receipt, in one assertion.

    A future arm makes this fail, which is the intended prompt: adding a
    renderer-blocked class means adding the arm, its remedy, and a journey in
    ``tests/test_instrument_servability_journeys.py`` — the same three edits the
    Stage 6 review found half-done.
    """

    assert _arms() == set()
    assert UNSERVABLE_REMEDIES == {}


def test_every_arm_states_a_remedy():
    """A refusal without a remedy is a dead end.

    Vacuous today and deliberately kept: it is the guard against the seam
    growing an arm that the doctor warning then renders as a KeyError instead of
    an explanation.
    """

    arms = _arms()
    assert set(UNSERVABLE_REMEDIES) == arms
    for arm in arms:
        assert UNSERVABLE_REMEDIES[arm].strip()


def test_the_seam_survives_the_retirement():
    """Both functions and the wire code stay callable, on every shape of input.

    ~10 boundaries (scheduler, exam pool, probe episodes, remediation,
    follow-ups, the staged constraint set, the cold probe, two sidecar handlers)
    ask this question today. Deleting the predicate with its arms would mean
    re-threading it through all of them the next time a class ships ahead of its
    renderer, which is precisely how the gap was created.
    """

    assert callable(unservable_reason)
    assert callable(unservable_refusal)
    assert UNSERVABLE_ERROR_CODE == "item_not_servable"


def test_the_predicate_ignores_unrelated_attributes():
    """Duck-typed on purpose: the call sites hold a `PracticeItem`, but the
    predicate must stay dependency-free so the scheduler and the exam pool can
    each import it without importing the other."""

    class _Bare:
        id = "pi_bare"

    assert unservable_reason(_Bare()) is None


@pytest.mark.parametrize("field", ["error_hunt", "laddered_stem"])
def test_an_explicitly_absent_contract_is_servable(field: str):
    assert unservable_reason(_Item(**{field: None})) is None
