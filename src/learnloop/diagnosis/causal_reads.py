"""Factor and diagnosis-receipt reads and deterministic EVSI input summaries.

The decision, machine-check queue, discriminating observation and cold verification
use these helpers to read stored factors, repair mappings, burden and provenance.
Shared formula and machine-check constants live alongside those reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from learnloop.db.repositories import Repository

CAUSAL_ORCHESTRATOR_FORMULA_VERSION = "causal_orchestrator_v1"


MACHINE_CHECK_REPAIR_MAPPING = "repair_class_mapping_backfill"


#: The machine owes this factor an INSTRUMENT: its causes need different repairs,
#: and no probe candidate exists that could tell them apart.  Queued by
#: ``sweep_machine_checks`` and drained by
#: ``learnloop.diagnosis.causal_probe_commissioning.commission_probe_instrument``.
MACHINE_CHECK_INSTRUMENT_COMMISSIONING = "causal_probe_instrument_commissioning"


#: Which pending checks may hold a learner probe.  `decide_probe`'s
#: ``defer_machine_checks`` arm means "the machine can still resolve this
#: uncertainty itself, so do not buy learner effort yet" — which is true of a
#: repair-mapping backfill and false of instrument commissioning: commissioning
#: does not resolve the uncertainty, it BUILDS the thing that would.  A factor
#: with no instrument is already reported honestly as
#: ``no_discriminating_instrument``, and folding commissioning into
#: ``defer_machine_checks`` would relabel a missing instrument as a resolvable
#: check and hide the instrument-pool bottleneck behind a softer verb.
PROBE_BLOCKING_MACHINE_CHECK_KINDS = frozenset({MACHINE_CHECK_REPAIR_MAPPING})


#: Kinds `sweep_machine_checks` owns, and therefore may auto-close when their
#: obligation stops being emitted. A kind absent here is somebody else's queue
#: entry and must not be closed by the sweep.
SWEPT_MACHINE_CHECK_KINDS = frozenset(
    {MACHINE_CHECK_REPAIR_MAPPING, MACHINE_CHECK_INSTRUMENT_COMMISSIONING}
)


def open_factors_for_hypothesis(
    repository: Repository, causal_hypothesis_id: str
) -> list[dict[str, Any]]:
    """Open cause factors on this hypothesis' own learning object (§3.9)."""

    hypothesis = repository.causal_hypothesis(causal_hypothesis_id)
    if hypothesis is None:
        return []
    learning_object_id = str(hypothesis["learning_object_id"])
    factors: list[dict[str, Any]] = []
    for factor in repository.open_unresolved_cause_factors(
        learning_object_id=learning_object_id
    ):
        ids = {
            str(value.get("hypothesis_id"))
            for value in factor.get("candidate_causes") or []
            if isinstance(value, Mapping) and value.get("hypothesis_id")
        }
        if causal_hypothesis_id in ids:
            factors.append(factor)
    return factors


def _durable_case_factor(
    repository: Repository, misconception: Any
) -> dict[str, Any] | None:
    """The open cause factor a durable misconception's case rides on, if any.

    The G12 decision receipt must be keyed on the factor the feedback attach
    reads (``unresolved_cause_factors_for_attempt(attempt_id)[0]``), and the
    receipt table's ``factor_id`` is NOT NULL — so with no open factor on the
    case's learning object there is honestly no receipt to write (and nothing
    the attach could surface anyway).  Prefers a factor whose hydrated
    candidate statements match the misconception's statement; falls back to
    the learning object's first open factor, which is the same
    "the case is on this LO" scope every other reader of
    ``open_unresolved_cause_factors`` uses.
    """

    from learnloop.diagnosis.causal_attribution import _normalized

    factors = repository.open_unresolved_cause_factors(
        learning_object_id=str(misconception.learning_object_id)
    )
    if not factors:
        return None
    wanted = _normalized(str(getattr(misconception, "statement", "") or ""))
    for factor in factors:
        for candidate in factor.get("candidate_causes") or []:
            if not isinstance(candidate, Mapping) or candidate.get("open_set"):
                continue
            if _normalized(str(candidate.get("statement") or "")) == wanted:
                return factor
    return factors[0]


def _case_repair_class_id(
    repository: Repository, hypothesis: Mapping[str, Any]
) -> str | None:
    """The repair class a factor-less diagnosis case would cold-verify (G14).

    Resolution order mirrors ``cold_verification_context`` exactly — the
    hypothesis's own mapped ``repair_class_id``, then the diagnosing attempt's
    receipt — because that is the chain the scheduled cold retry will walk
    when it lands; if nothing resolves HERE, nothing will resolve THEN either,
    and the episode would be unmeasurable from birth.
    """

    if hypothesis.get("repair_class_id"):
        return str(hypothesis["repair_class_id"])
    return _receipt_repair_class_id(
        diagnosis_receipt(
            repository, str(hypothesis.get("attempt_id") or "") or None
        )
    )


def _unmapped_case_obligation(hypothesis: Mapping[str, Any]) -> dict[str, Any]:
    """The typed mapping obligation for a factor-less unmapped diagnosis case.

    Same shape as :func:`backfill_obligation` (the queue consumers key on
    ``kind`` / ``hypothesis_ids`` / ``unresolved_reasons``), with
    ``factor_id`` honestly None — there is no factor; that absence is the
    arm's defining feature.
    """

    hypothesis_id = str(hypothesis["id"])
    return {
        "kind": MACHINE_CHECK_REPAIR_MAPPING,
        "state": "unmapped_diagnosis_case",
        "coherence_gate_state": None,
        "factor_id": None,
        "attempt_id": str(hypothesis.get("attempt_id") or "") or None,
        "hypothesis_ids": [hypothesis_id],
        "unresolved_reasons": {
            hypothesis_id: str(
                hypothesis.get("repair_class_unresolved_reason") or "unrecorded"
            )
        },
        "repair_class_ids": [],
        "reason": "diagnosis case has no resolvable repair class",
        "learner_actionable": False,
    }


def diagnosis_receipt(
    repository: Repository, attempt_id: str | None
) -> Mapping[str, Any] | None:
    if not attempt_id:
        return None
    debug = repository.attempt_debug_payload(attempt_id) or {}
    attribution = debug.get("causal_attribution")
    if not isinstance(attribution, Mapping):
        return None
    receipt = attribution.get("diagnosis_receipt")
    return receipt if isinstance(receipt, Mapping) else None


def _receipt_repair_class_id(receipt: Mapping[str, Any] | None) -> str | None:
    """The repair class one diagnosis receipt commits to, if any.

    Prefers the §6 common-repair cover (safe for the whole plausible set), then
    the §6.4 minimal-repair selection. The selection stores its winner NESTED
    (``selected.repair_class.id``) — the previous reader looked for a flat
    ``repair_selection.repair_class_id`` key that has never existed, so this
    fallback silently never fired."""

    if not isinstance(receipt, Mapping):
        return None
    cover = receipt.get("common_repair_cover")
    if isinstance(cover, Mapping) and cover.get("repair_class_id"):
        return str(cover["repair_class_id"])
    selection = receipt.get("repair_selection")
    if not isinstance(selection, Mapping):
        return None
    selected = selection.get("selected")
    if not isinstance(selected, Mapping):
        return None
    repair_class = selected.get("repair_class")
    if isinstance(repair_class, Mapping) and repair_class.get("id"):
        return str(repair_class["id"])
    return None


def _repair_class_by_hypothesis(
    causes: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for cause in causes:
        if not isinstance(cause, Mapping):
            continue
        hypothesis_id = cause.get("hypothesis_id")
        repair_class_id = cause.get("repair_class_id")
        if hypothesis_id and repair_class_id:
            mapping[str(hypothesis_id)] = str(repair_class_id)
    return mapping


def _avoided_overteaching_minutes(
    repository: Repository,
    *,
    attempt_id: str | None,
    repair_class_ids: Sequence[str],
    default_minutes: float,
) -> tuple[float, str]:
    """Expected teaching minutes a discriminating answer would save, + provenance.

    Teaching every plausible branch costs the sum of their expected minutes;
    knowing which one is needed costs the mean.  The difference is the avoided
    over-teaching, which is what §7 prices the probe against — not raw
    information gain.

    ``expected_minutes`` originates in an authored repair suggestion, so a value
    sourced from the diagnosis receipt is ``model_reported`` (standing
    constraint 4).  It never overrules a computed quantity: it is a multiplicand
    of the deterministic separability terms, so a provably inseparable
    instrument stays worthless however large this number is.
    """

    if len(repair_class_ids) < 2:
        return 0.0, "deterministic"
    receipt = diagnosis_receipt(repository, attempt_id)
    by_id: dict[str, Mapping[str, Any]] = {}
    if receipt is not None:
        for entry in receipt.get("repair_classes") or []:
            if isinstance(entry, Mapping) and entry.get("id"):
                by_id[str(entry["id"])] = entry
    minutes: list[float] = []
    from_receipt = False
    from_default = False
    for repair_class_id in repair_class_ids:
        entry = by_id.get(str(repair_class_id))
        raw = entry.get("expected_minutes") if entry is not None else None
        if isinstance(raw, (int, float)) and not isinstance(raw, bool) and raw > 0:
            minutes.append(float(raw))
            from_receipt = True
        else:
            minutes.append(default_minutes)
            from_default = True
    total = sum(minutes)
    if from_receipt and from_default:
        # Part of the sum is authored prose and part is the pinned 8.0 fallback;
        # calling that "model_reported" would launder the default (§4.1).
        provenance = "mixed"
    elif from_receipt:
        provenance = "model_reported"
    else:
        provenance = "heuristic_default" if from_default else "deterministic"
    return max(0.0, total - total / len(minutes)), provenance


def _probe_burden_minutes(
    repository: Repository, practice_item_id: str | None, default_minutes: float
) -> tuple[float, str]:
    """Probe burden from the instrument card's own expected seconds, + provenance."""

    if not practice_item_id:
        return default_minutes, "heuristic_default"
    for link in repository.probe_item_family_links(practice_item_id):
        card = repository.probe_instrument_card(
            link.instrument_card_id, link.instrument_card_version
        )
        if card is None:
            continue
        seconds = (card.card or {}).get("expected_seconds")
        if isinstance(seconds, (int, float)) and not isinstance(seconds, bool):
            if seconds > 0:
                # Reading the card is deterministic; the NUMBER is an authored
                # family-template constant, and the receipt records the source,
                # not the reproducibility (§4.1).
                return float(seconds) / 60.0, "authored_prior"
    return default_minutes, "heuristic_default"


def _recent_diagnostic_burden(
    repository: Repository, learning_object_id: str, window: int
) -> int:
    attempts = repository.list_recent_attempts_by_learning_object(
        learning_object_id, limit=max(1, window)
    )
    return sum(
        1
        for attempt in attempts
        if str(attempt.get("attempt_type") or "") == "diagnostic_probe"
    )


@dataclass(frozen=True)
class DiscriminationInputs:
    """The two EVSI terms plus where each came from (standing constraint 4)."""

    expected_information_gain: float
    probability_information_changes_repair: float
    gain_provenance: str
    action_change_provenance: str
    separable_pairs: int = 0
    inseparable_pairs: int = 0


def _discrimination_inputs(
    candidate: Mapping[str, Any] | None,
    repair_class_by_hypothesis: Mapping[str, str],
) -> DiscriminationInputs:
    """``(expected_information_gain, p(information changes the repair))``.

    Both are COMPUTED, never model-reported (standing constraint 4):

    * the gain is the share of hypothesis pairs the candidate's recorded
      ``blind_bundle_discrimination`` provably separates under the real matcher
      (``rows_are_separable`` over declared feature rows);
    * the action-change probability is the share of those separable pairs whose
      hypotheses land in different repair classes — separating two causes that
      would be repaired identically changes nothing.

    With no instrument, or no parsable pair, the value is the pinned 0.0
    fallback and is tagged ``heuristic_default`` rather than being passed off as
    a computed zero.
    """

    empty = DiscriminationInputs(0.0, 0.0, "heuristic_default", "heuristic_default")
    if candidate is None:
        return empty
    discrimination = candidate.get("discrimination")
    if not isinstance(discrimination, Mapping):
        return empty
    separable = [
        [str(value) for value in pair]
        for pair in discrimination.get("separable_pairs") or []
        if isinstance(pair, (list, tuple)) and len(pair) == 2
    ]
    inseparable = [
        pair
        for pair in discrimination.get("inseparable_pairs") or []
        if isinstance(pair, (list, tuple)) and len(pair) == 2
    ]
    total = len(separable) + len(inseparable)
    if total == 0:
        return empty
    expected_information_gain = len(separable) / total
    if not separable:
        # Provably inseparable: zero discriminating information is a computed
        # fact, and no model-reported teaching cost can overrule it.
        return DiscriminationInputs(
            expected_information_gain,
            0.0,
            "deterministic",
            "deterministic",
            separable_pairs=0,
            inseparable_pairs=len(inseparable),
        )
    action_changing = sum(
        1
        for left, right in separable
        if repair_class_by_hypothesis.get(left)
        and repair_class_by_hypothesis.get(right)
        and repair_class_by_hypothesis[left] != repair_class_by_hypothesis[right]
    )
    return DiscriminationInputs(
        expected_information_gain,
        action_changing / len(separable),
        "deterministic",
        "deterministic",
        separable_pairs=len(separable),
        inseparable_pairs=len(inseparable),
    )


class CausalRepairError(ValueError):
    """The repair case itself is unusable (no such misconception / candidate)."""

