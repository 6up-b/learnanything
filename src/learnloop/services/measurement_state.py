"""Measurement-provenance labels — measured / inferred / claimed / unknown.

Spec: ``spec_measurement_efficiency_v1.md`` §B2 (three-state labels) and §E2
(learner claims as priors only); implementation plan item 3.2.

§B2's complaint: ``facet_state_label`` (``facet_diagnostics.py``) decides
``unexamined`` on a raw evidence-mass threshold alone, so a facet the system can
already predict confidently reads as untouched — and the pooled prediction
(``selection_rewards.predicted_facet_recall``) then renders right next to
directly measured recall with nothing distinguishing the two. An inference
displayed as if it were a measurement is the defect. This module is the ONE
place that decides which of the four labels a displayed number is licensed to
carry; render sites read the label, they never re-derive it.

**This is a labelling vocabulary and nothing else.** No threshold, no
certification decision and no stored belief reads it — §B2's "revert if" is
precisely *inferred states treated as measured anywhere downstream*, so the
label travels outward to the UI and stops there. The existing
``unexamined | uncertain | known_gap | solid`` diagnostic bucket is a different
axis (*what* we believe, and the axis certification reads); this axis is *how we
came to believe it*. Both ride the same rows on surfaces that render a
prediction, and neither is computed from the other.

Licensing, from §B2/§E2 — enforced only in :func:`classify_measurement_state`:

* ``measured`` — direct evidence above the facet mass threshold. Reserved for
  evidence actually observed; nothing derived may claim it.
* ``inferred`` — no direct evidence above the threshold, but the system holds an
  *informative* pooled/dominance-derived prediction: something exists to pool
  from, either sub-threshold direct facet mass or LO-level mastery evidence.
  ``predicted_facet_recall`` returns its 0.5 ignorance default when neither
  exists, and labelling ignorance as inference is exactly the confident
  wrongness this vocabulary exists to prevent.
* ``claimed`` — §E2: a learner claim covers the cell and nothing has been
  observed or pooled. "Claimed, unverified" genuinely is a distinct state from
  unknown; it seeds a prior only, never certifies and never writes mastery.
* ``unknown`` — absence. No evidence, nothing to pool from, no claim.

Precedence is ``measured > inferred > claimed > unknown``: a claim is a prior,
so it can never outrank a number derived from evidence, and a pooled prediction
never outranks direct evidence over the gate.

The *interval* §B2 asks inferred values to be rendered with remains the existing
compact ``mean ±√variance`` readout on Practice/Today/Feedback (standing display
preference); item 3.2 adds the label, not a new interval rendering.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Final, Literal

MeasurementState = Literal["measured", "inferred", "claimed", "unknown"]

MEASURED: Final[MeasurementState] = "measured"
INFERRED: Final[MeasurementState] = "inferred"
CLAIMED: Final[MeasurementState] = "claimed"
UNKNOWN: Final[MeasurementState] = "unknown"

# The closed vocabulary, in precedence order (strongest provenance first).
MEASUREMENT_STATES: Final[tuple[MeasurementState, ...]] = (MEASURED, INFERRED, CLAIMED, UNKNOWN)


def require_measurement_state(value: str) -> MeasurementState:
    """Gate for the closed vocabulary: an unrecognised label is a bug, not data.

    ``unknown`` is a *member* of the vocabulary — the explicit abstention arm
    ("we looked and there is nothing"), which is why absence never needs a label
    outside the four. Anything else raises, so a typo, a stale persisted string
    or a future fifth state can never be silently passed through to a render
    site that would then display it as though it were measured.
    """

    if value not in MEASUREMENT_STATES:
        raise ValueError(
            f"unknown measurement state {value!r}; expected one of {MEASUREMENT_STATES}"
        )
    return value  # type: ignore[return-value]


def classify_measurement_state(
    *,
    evidence_mass: float | None,
    min_evidence_mass: float,
    mastery_evidence_count: int = 0,
    claim_present: bool | Callable[[], bool] = False,
) -> MeasurementState:
    """Which of the four labels a displayed facet-level number is licensed to carry.

    Arguments are the ingredients ``selection_rewards.predicted_facet_recall``
    already takes, so the label and the number it qualifies are derived from the
    same inputs and cannot disagree:

    * ``evidence_mass`` — the facet's aggregate independent evidence mass.
    * ``min_evidence_mass`` — ``recall_coverage.min_facet_evidence_mass``. The
      comparison is strict (``>``), matching the ``solid`` arm of
      ``facet_state_label``, so ``measured`` and ``solid`` agree on the mass gate
      by construction without either one reading the other.
    * ``mastery_evidence_count`` — the LO EKF's evidence count. Zero means the
      mastery row (claim-seeded or absent) carries no information to pool, which
      is why it cannot license ``inferred``.
    * ``claim_present`` — §E2 coverage: does a learner claim cover this cell.
      Accepts a thunk so a caller can defer a per-LO ``covering_learner_claim``
      query to the only branch that needs it; the precedence stays here.

    Nothing here reads or writes belief state, and no caller may branch a
    threshold or a certification on the result.
    """

    mass = max(float(evidence_mass or 0.0), 0.0)
    if mass > min_evidence_mass:
        # Direct evidence over the gate: the only arm that may say "measured".
        return MEASURED
    if mass > 0.0 or int(mastery_evidence_count) > 0:
        # Something informative to pool from — sub-threshold direct mass, or an
        # evidenced LO mastery backbone. The prediction is real inference.
        return INFERRED
    if claim_present() if callable(claim_present) else bool(claim_present):
        # §E2: claimed, unverified. A prior, distinct from absence.
        return CLAIMED
    return UNKNOWN
