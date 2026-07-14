"""Three-way learner-error intake: repair, diagnose, or read first."""

from __future__ import annotations

from typing import Literal

from learnloop.db.repositories import MisconceptionRecord


IntakeRoute = Literal["repair", "diagnose", "read_first"]


def classify_intake(
    *,
    misconception: MisconceptionRecord | None = None,
    facet_state_label: str | None = None,
    has_source_exposure: bool = False,
    unresolved_cause: bool = False,
    repeated_failure_despite_coverage: bool = False,
    mechanism_is_misconception: bool = False,
) -> IntakeRoute:
    """Route without ever promoting a one-off mechanism event into a case."""

    if misconception is not None and misconception.status in {"active", "resolving"}:
        return "repair"
    if facet_state_label == "unexamined" and not has_source_exposure:
        return "read_first"
    if unresolved_cause or repeated_failure_despite_coverage:
        return "diagnose"
    # A lone misconception-shaped mechanism is evidence toward promotion, not
    # a durable statement-pair repair case. The safe next step is diagnosis.
    if mechanism_is_misconception:
        return "diagnose"
    return "diagnose"
