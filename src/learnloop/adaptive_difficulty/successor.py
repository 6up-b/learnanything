"""The AD2+AD3 successor's gate and its six switches (spec_adaptive_difficulty_v1 §11.1).

One successor (``mvp-0.28``), six switches under ``[adaptive_difficulty]``,
each restoring its part of the predecessor exactly, and composing:

* ``selection``: the serve and commission draws, substitution, deferrals;
* ``generation_contract``: the prompt names a feature point, with no band;
* ``promoted_predictor``: live decisions and readiness read the subject view
  (off: each LO's own view, and no AD readiness numbers); off makes
  ``learned_coupling``, ``reading_opportunities`` and ``reading_self_check``
  moot for live decisions (the subject view still computes its receipts);
* ``learned_coupling``: loadings, couplings and their proposal (off: the
  subject view at its uniform-sharing points, no proposal call);
* ``reading_opportunities``: reading transitions (off makes
  ``reading_self_check`` moot);
* ``reading_self_check``: the verdict term (D22).

Below the tag every switch reads off whatever the config says, so an
``mvp-0.27`` vault is served exactly as before. The master switch
``adaptive_difficulty.enabled`` turns everything off.

Outside the successor: ``reading_dose_offers`` (D21), which acts at every
version (it changes what the Reader may offer, not any persisted meaning).
"""

from __future__ import annotations

from typing import Any

from learnloop.algorithm_versions import ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION, ADAPTIVE_DIFFICULTY_VERSIONS

from learnloop.adaptive_difficulty.switches import ad_enabled

SUCCESSOR = ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION
SWITCHES = ("selection", "generation_contract", "promoted_predictor", "learned_coupling", "reading_opportunities",
            "reading_self_check")
DOSE_SWITCH = "reading_dose_offers"


def _section(config: Any) -> Any:
    return getattr(config, "adaptive_difficulty", None)


def successor_active(config: Any) -> bool:
    """At the successor's tag or later, with the master switch on."""

    version = getattr(getattr(config, "algorithms", None), "algorithm_version", None)
    return ad_enabled(config) and version in ADAPTIVE_DIFFICULTY_VERSIONS


def switch_on(config: Any, name: str) -> bool:
    """One of the six switches, read only at the tag (below it: off)."""

    if name not in SWITCHES:
        raise ValueError(f"unknown AD2+AD3 switch {name!r}")
    return successor_active(config) and bool(getattr(_section(config), name, False))


def selection_on(config: Any) -> bool:
    return switch_on(config, "selection")


def generation_contract_on(config: Any) -> bool:
    return switch_on(config, "generation_contract")


def subject_view_live(config: Any) -> bool:
    """Live decisions read the subject view (``promoted_predictor``)."""

    return switch_on(config, "promoted_predictor")


def coupling_on(config: Any) -> bool:
    return switch_on(config, "learned_coupling")


def reading_on(config: Any) -> bool:
    return switch_on(config, "reading_opportunities")


def verdicts_on(config: Any) -> bool:
    return reading_on(config) and switch_on(config, "reading_self_check")


def dose_offers_on(config: Any) -> bool:
    """The Reader's dose arm (outside the successor; every version)."""

    return ad_enabled(config) and bool(getattr(_section(config), DOSE_SWITCH, False))


HISTORY_FALLBACKS = ("exclude", "current_content")


def history_fallback(config: Any) -> str:
    """How AD reads a historical attempt whose exact item revision was not saved
    (``adaptive_difficulty.history_fallback``; owner decision 2026-10-19): ``"current_content"``
    (the default) reads it against today's item text, ``"exclude"`` leaves it out. AD's own
    setting, passed to field's revision resolution for AD's reads only; ``field.legacy_fallback``,
    which the field harness and its projections read, is unchanged."""

    value = str(getattr(_section(config), "history_fallback", "current_content") or "current_content")
    if value not in HISTORY_FALLBACKS:
        raise ValueError("adaptive_difficulty.history_fallback must be exclude or current_content")
    return value


def settings(config: Any) -> dict[str, bool]:
    return {
        "successor": successor_active(config),
        **{name: switch_on(config, name) if name in SWITCHES else False for name in SWITCHES},
        "subject_view_live": subject_view_live(config),
        "reading_dose_offers": dose_offers_on(config),
    }


__all__ = [
    "DOSE_SWITCH",
    "HISTORY_FALLBACKS",
    "SUCCESSOR",
    "SWITCHES",
    "coupling_on",
    "dose_offers_on",
    "generation_contract_on",
    "history_fallback",
    "reading_on",
    "selection_on",
    "settings",
    "subject_view_live",
    "successor_active",
    "switch_on",
    "verdicts_on",
]
