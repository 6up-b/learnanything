"""Derived per-attempt-type evidence factors (Fable's-take item 3).

One config-owned primitive (``EvidenceConfig``) replaces the three former
module tables (``ATTEMPT_TYPE_FACTORS``, ``ATTEMPT_TYPE_COVERAGE_FACTORS``,
``PRACTICE_MODE_COVERAGE_DEFAULTS``). Reliability and coverage factors are
derived here so they can no longer drift apart for the same attempt mode.
"""

from __future__ import annotations

from learnloop.config import EvidenceConfig

# Fallback for call sites without a vault config in scope (tests, legacy
# helpers). Matches the canonical defaults in ``learnloop.config.schema``.
DEFAULT_EVIDENCE = EvidenceConfig()


def attempt_evidence_mass(attempt_type: str, config: EvidenceConfig | None = None) -> float:
    """Weight of this attempt type on ability-belief updates (mastery EKF)."""

    entry = (config or DEFAULT_EVIDENCE).attempt_types.get(attempt_type)
    if entry is None:
        return 1.0
    return entry.evidence_mass


def attempt_surface_exposure(attempt_type: str, config: EvidenceConfig | None = None) -> float:
    """Fraction of the item's facet surface this attempt type certifies as probed."""

    entry = (config or DEFAULT_EVIDENCE).attempt_types.get(attempt_type)
    if entry is None:
        return 1.0
    if entry.surface_exposure is not None:
        return entry.surface_exposure
    return entry.evidence_mass


def practice_mode_item_coverage(practice_mode: str, config: EvidenceConfig | None = None) -> float:
    """Item-side coverage prior when an item has no evidence weights or rubric."""

    resolved = config or DEFAULT_EVIDENCE
    return resolved.item_coverage_by_practice_mode.get(practice_mode, resolved.item_coverage_default)
