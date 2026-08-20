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
    "exam_evidence",
    "teach_back",
    "exam_attempt",
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
    # Imported per-question outcome from a past exam (exam seeding). Recorded
    # through the deterministic attempt path with a backdated clock; heavily
    # discounted because one exam is one correlated evidence event.
    "exam_evidence",
    # Teach-back conversation graded as one attempt: the learner explains, an
    # AI naive student asks follow-ups, and the whole transcript is graded
    # against the asked rubric criteria only (recording type).
    "teach_back",
    # Held-out practice-exam answer on a fresh, never-practiced item. Recorded
    # through the deterministic attempt path at exam-finish time. Full evidence
    # mass: a proctored fresh-item answer is the highest-quality evidence in the
    # system (unlike the discounted `exam_evidence` import type).
    "exam_attempt",
)

NON_RECORDING_ATTEMPT_TYPES: frozenset[AttemptType] = frozenset({"guided_walkthrough", "skip"})

DEFAULT_ATTEMPT_TYPE: AttemptType = "independent_attempt"

# Per-attempt-type evidence weights now live in config (EvidenceConfig) and are
# derived via learnloop.attempts.evidence — see Fable's-take item 3.

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
