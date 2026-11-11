"""What other test files use from ``tests/test_placement_diagnosis_decides.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock, utc_now_iso
from learnloop.placement.state import load_placement_state

from tests.diagnosis_fakes import ReviewFakeClient
from tests.diagnosis_split_helpers import at
from tests.split_live_helpers import drain_jobs, submit


LO = "lo_svd_compute"
WRONG = "A = U Sigma V wrong"
DUE_HOURS = 14 * 24


def _iso(hours: float) -> str:
    return utc_now_iso(FrozenClock(at(hours)))


#: When the tests read placement state: after every answer they record, and
#: within placement.rules.DIAGNOSIS_WAIT_DAYS of every diagnosis they queue.
READ_AT = _iso(DUE_HOURS + 100)


class _Diagnosed(ReviewFakeClient):
    """The fake grader and diagnoser with a chosen validity and causal class.

    ``validity_scope`` lands on every blind-grade error attribution;
    ``causal_class`` on every event the diagnoser writes (the M2 validator
    still forces ``unknown`` off a valid measurement)."""

    def __init__(self, *, validity_scope="valid_measurement", causal_class="learner_state", **kwargs):
        super().__init__(**kwargs)
        self.validity_scope = validity_scope
        self.causal_class = causal_class

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        return result.model_copy(update={
            "error_attributions": [
                row.model_copy(update={"validity_scope": self.validity_scope}) for row in result.error_attributions
            ],
        })

    def _diagnosis(self, request, context):
        result = super()._diagnosis(request, context)
        return result.model_copy(update={
            "event_diagnoses": [
                event.model_copy(update={"causal_class": self.causal_class}) for event in result.event_diagnoses
            ],
        })


def _state(vault, repository, lo=LO, *, now_iso=READ_AT):
    state = load_placement_state(vault, repository, now_iso=now_iso)
    (assumption,) = [a for a in state.assumptions if a.learning_object_id == lo]
    return assumption, state.intent_by_lo[lo]


def _miss(vault, repository, client, *, item="pi_svd_compute_001", hours=DUE_HOURS + 1, drain=True):
    result = submit(vault, repository, client, item_id=item, answer=WRONG, when=at(hours))
    if drain:
        drain_jobs(vault, repository, client, clock=FrozenClock(at(hours)))
    return result
