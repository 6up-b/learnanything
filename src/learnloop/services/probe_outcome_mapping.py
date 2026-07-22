"""Versioned probe-outcome -> coarse-class mapping (spec_p0_measurement_correctness
§3.1 + Change log 2026-07-18 entry (a)).

A probe instrument card is exactly the §3.1 "card designed to recognize a specific
misconception" case, so its native fine outcome vocabulary
(``correct_target_reason``, the card's ``confuses_*`` / ``fire:*`` signature
outcomes, weak/partial bands, ``unanswered``, residual systematic errors) maps to a
card-declared coarse ``outcome_schema`` via this **versioned deterministic mapping**:

    success        <-  correct_target_reason (and the other authored "correct" bands)
    signature_error <- the card's declared confusion-target outcome(s)
    unanswered     <-  unanswered (where the resolved schema carries the class)
    other          <-  residual (weak/partial/systematic-error/unmatched)

The mapping is derived **mechanically** from the compiled instrument (its
``signature_error_types`` keys and outcome alphabet) and versioned by
:data:`PROBE_COARSE_MAPPING_VERSION`. The full mapping table + version is snapshotted
on the administration (via the P0.2 dual-write raw grade event) so replay reproduces
the exact class assignment even if the derivation later changes -- a new derivation
mints a new version and never rewrites a snapshotted one.
"""

from __future__ import annotations

from typing import Mapping

from learnloop.services.outcome_schemas import (
    COARSE_RESPONSE_SLUG,
    COARSE_RESPONSE_UNANSWERED_SLUG,
    SIGNATURE_ERROR_SLUG,
)
from learnloop.services.probe_families import CompiledInstrument

# Bump when the mechanical derivation below changes. Snapshotted per administration
# so older episodes keep replaying under the mapping they were recorded with.
PROBE_COARSE_MAPPING_VERSION = "probe_coarse_v1"

# The authored "correct" and "weak/partial" outcome vocabularies, mirrored from
# ``probe_families.classify_outcome`` so a fine outcome coarsens consistently with
# how it was classified in the first place.
_CORRECT_OUTCOMES: frozenset[str] = frozenset(
    {
        "correct_target_reason",
        "correct_recall",
        "correct_prediction_reason",
        "correct_on_shifted",
        "valid_counterexample",
        "correct_commit_reason",
        "complete_correct_structure",
        "correct_strategy_complete",
        "integrated_correct",
        "correct",
        "high",
    }
)
_PARTIAL_OUTCOMES: frozenset[str] = frozenset(
    {
        "correct_weak_reason",
        "partial_recall",
        "correct_prediction_weak_reason",
        "partial_boundary",
        "correct_commit_weak_reason",
        "valid_prefix_first_invalid",
        "correct_strategy_execution_slip",
        "partial_integration",
        "partial",
        "mid",
    }
)


def coarse_schema_slug(instrument: CompiledInstrument) -> str:
    """The card-declared coarse outcome schema this instrument maps onto (§3.1).

    A card with a declared confusion-target outcome recognizes a specific
    misconception -> the three-class ``signature_error`` schema. Otherwise a card
    that admits an explicit no-answer channel uses the four-class unanswered schema;
    the remaining cards use the plain three-class coarse-response schema.
    """

    if instrument.signature_error_types:
        return SIGNATURE_ERROR_SLUG
    if "unanswered" in instrument.outcome_alphabet:
        return COARSE_RESPONSE_UNANSWERED_SLUG
    return COARSE_RESPONSE_SLUG


def _base_coarse_class(instrument: CompiledInstrument, outcome: str) -> str:
    if outcome == "unanswered":
        return "unanswered"
    if outcome in instrument.signature_error_types:
        return "signature_error"
    if outcome in _CORRECT_OUTCOMES:
        return "success"
    if outcome in _PARTIAL_OUTCOMES:
        return "partial_success"
    return "other"


def coarse_class_for_outcome(
    instrument: CompiledInstrument,
    outcome: str,
    *,
    schema_true_classes: Mapping[str, object] | tuple[str, ...] | frozenset[str] | None = None,
) -> str:
    """Deterministically coarsen one fine probe outcome (§3.1).

    ``other`` is the residual: an outcome the schema cannot represent (e.g.
    ``partial_success`` under the three-class signature schema, or ``unanswered``
    under a schema without that class) never silently becomes success or failure --
    it maps to ``other`` (§3.1 "Unclassifiable output maps to other").
    """

    coarse = _base_coarse_class(instrument, outcome)
    if schema_true_classes is not None and coarse not in schema_true_classes:
        return "other"
    return coarse


def probe_outcome_mapping(instrument: CompiledInstrument) -> dict[str, str]:
    """The full deterministic fine-outcome -> coarse-class table for this card.

    Keyed by every outcome in the instrument alphabet (plus the signature keys),
    so the snapshot is self-contained for replay. Deterministic: identical
    instruments produce byte-identical mappings (sorted, pure function of inputs).
    """

    slug = coarse_schema_slug(instrument)
    from learnloop.services.outcome_schemas import BUILTIN_SCHEMAS

    schema = next(s for s in BUILTIN_SCHEMAS if s.slug == slug)
    true_classes = set(schema.true_classes)
    outcomes = set(instrument.outcome_alphabet) | set(instrument.signature_error_types)
    return {
        outcome: coarse_class_for_outcome(
            instrument, outcome, schema_true_classes=true_classes
        )
        for outcome in sorted(outcomes)
    }


def mapping_snapshot(instrument: CompiledInstrument) -> dict[str, object]:
    """The administration-snapshotted mapping identity (deliverable 1).

    Carries enough to reproduce the coarse class of any observed outcome on replay:
    the mapping version, the resolved coarse schema slug, and the full table.
    """

    return {
        "probe_mapping_version": PROBE_COARSE_MAPPING_VERSION,
        "coarse_schema_slug": coarse_schema_slug(instrument),
        "mapping": probe_outcome_mapping(instrument),
    }


def coarse_instrument_rows(
    instrument: CompiledInstrument,
    slot_map: Mapping[str, str],
    schema_true_classes: tuple[str, ...],
) -> dict[str, dict[str, float]]:
    """Aggregate the fine ``P(fine_outcome | H_slot)`` instrument rows into coarse
    ``P(Z_coarse | H_label)`` rows over the schema's true classes (§4.2 P(Z|H,card)).

    ``slot_map`` translates the episode's concrete hypothesis label to the card's
    abstract slot -- the same frozen map selection and replay share.
    """

    rows: dict[str, dict[str, float]] = {}
    for label, slot in slot_map.items():
        fine_row = instrument.rows.get(slot, {})
        agg = {z: 0.0 for z in schema_true_classes}
        for fine, prob in fine_row.items():
            coarse = coarse_class_for_outcome(
                instrument, fine, schema_true_classes=set(schema_true_classes)
            )
            agg[coarse] = agg.get(coarse, 0.0) + float(prob)
        rows[label] = agg
    return rows
