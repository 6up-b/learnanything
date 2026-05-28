from __future__ import annotations

from typing import Literal, TypeAlias

AttemptType: TypeAlias = Literal[
    "independent_attempt",
    "hinted_attempt",
    "dont_know",
    "diagnostic_probe",
    "guided_walkthrough",
    "reconstruction_after_walkthrough",
    "skip",
    "self_report",
    "open_text",
]

SUPPORTED_ATTEMPT_TYPES: tuple[AttemptType, ...] = (
    "independent_attempt",
    "hinted_attempt",
    "dont_know",
    "diagnostic_probe",
    "guided_walkthrough",
    "reconstruction_after_walkthrough",
    "skip",
    "self_report",
    "open_text",
)

NON_RECORDING_ATTEMPT_TYPES: frozenset[AttemptType] = frozenset({"guided_walkthrough", "skip"})

DEFAULT_ATTEMPT_TYPE: AttemptType = "independent_attempt"

ATTEMPT_TYPE_FACTORS: dict[AttemptType, float] = {
    "independent_attempt": 1.0,
    "open_text": 1.0,
    "diagnostic_probe": 1.0,
    "hinted_attempt": 1.0,
    "reconstruction_after_walkthrough": 0.5,
    "dont_know": 0.7,
    "self_report": 0.3,
    "guided_walkthrough": 0.0,
    "skip": 0.0,
}

_SUPPORTED = set(SUPPORTED_ATTEMPT_TYPES)


def unsupported_attempt_types(values: list[str] | tuple[str, ...] | None) -> list[str]:
    if not values:
        return []
    return sorted({value for value in values if value not in _SUPPORTED})


def default_attempt_type(allowed: list[str] | tuple[str, ...] | None) -> AttemptType:
    if not allowed:
        return DEFAULT_ATTEMPT_TYPE
    if DEFAULT_ATTEMPT_TYPE in allowed:
        return DEFAULT_ATTEMPT_TYPE
    for attempt_type in allowed:
        if attempt_type in _SUPPORTED and attempt_type not in NON_RECORDING_ATTEMPT_TYPES:
            return attempt_type  # type: ignore[return-value]
    return DEFAULT_ATTEMPT_TYPE
