"""The switches of follow-up generate and serve (FG1). A leaf: no store, no domain.

``generate_and_serve_on`` is the successor's gate (``FOLLOWUP_SERVE_VERSIONS``, the
kill switch ``followup.generate_and_serve``): off, or below the tag, behaviour is
mvp-0.44's and the stored ``probe.generation.auto_generate_on_entry`` applies.
"""

from __future__ import annotations

from typing import Any

from learnloop.algorithm_versions import FOLLOWUP_SERVE_VERSIONS

#: The one surface with the pending and skip UI (spec §3.1, §10): the desktop.
#: The phone and the TUI stay on the predecessor's behaviour.
SERVING_SURFACE = "desktop"
#: The phone's request-origin surface name, used for its hand-off line (§10).
PHONE_SURFACE = "phone"
#: R9: a factor FG1's lane opened for its question. It owes no repair mapping, so the machine
#: check sweep leaves it out, and it closes when its question won't be asked.
RIVAL_CAUSES_FACTOR_VERSION = "followup_rival_causes_v1"


def generate_and_serve_on(config: Any) -> bool:
    section = getattr(config, "followup", None)
    algorithms = getattr(config, "algorithms", None)
    return (
        bool(getattr(section, "generate_and_serve", False))
        and getattr(algorithms, "algorithm_version", None) in FOLLOWUP_SERVE_VERSIONS
    )


def effective_auto_generate_on_entry(config: Any) -> bool:
    """§4.3: true while FG1 is on, whatever the file says. The stored value stays
    untouched for rollback, and off it is what applies."""

    if generate_and_serve_on(config):
        return True
    probe = getattr(config, "probe", None)
    generation = getattr(probe, "generation", None)
    return bool(getattr(generation, "auto_generate_on_entry", False))
