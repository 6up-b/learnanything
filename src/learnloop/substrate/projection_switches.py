"""Switches recorded on a whole-vault rebuild receipt.

The receipt always records whether the FSRS interval omits the surprise factor.
It also records the canonical facet-belief fixes switch at versions that serve it.
"""

from __future__ import annotations

from typing import Any

from learnloop.algorithm_versions import FACET_BELIEF_FIX_VERSIONS
from learnloop.config.scheduler_switches import interval_factor_removed


#: The key a rebuild receipt's ``projection_switches_json`` records the factor's gate under.
INTERVAL_FACTOR_SNAPSHOT_KEY = "scheduler.surprise.remove_interval_factor"

#: The key it records the facet-belief successor's switch under (from mvp-0.59 only).
FACET_BELIEF_FIXES_SNAPSHOT_KEY = "facet_diagnostic.canonical_belief_fixes"


def projection_switches(config: Any) -> dict[str, bool]:
    """What a whole-vault rebuild derived persisted state under (§5.5): whether the factor was removed, and from the
    facet-belief successor (mvp-0.59) whether its fixes were on (the per-LO facet uncertainty and every attempt's
    stored reading of the belief follow a switch change only at the next whole-vault rebuild). Below that tag the
    record is the predecessor's, one key."""

    switches = {INTERVAL_FACTOR_SNAPSHOT_KEY: interval_factor_removed(config)}
    algorithms = getattr(config, "algorithms", None)
    if getattr(algorithms, "algorithm_version", None) in FACET_BELIEF_FIX_VERSIONS:
        # At the tag, ``learner.facet_state_reader.facet_belief_fixes_on`` is the switch itself (read here
        # directly: this module sits below the learner package).
        section = getattr(config, "facet_diagnostic", None)
        switches[FACET_BELIEF_FIXES_SNAPSHOT_KEY] = bool(getattr(section, "canonical_belief_fixes", False))
    return switches
