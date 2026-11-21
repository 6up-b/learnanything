"""Whether a progress report finishes its section, and why (mvp-0.63, ``docs/reviews/algorithm-mvp-0.63.md``).

The one rule the progress report (``reader.mark_section_progress``) applies, on the desktop and the phone host alike:

* from mvp-0.63 a section is finished by the learner's word ("I've read this section") or by an acknowledged end
  observation (its last readable passage shown during the learner's own reading, kept by
  ``seen_passages.check_report``); closing a quick check and choosing what to do with its idea finish nothing;
* below the tag every completion the Reader sends finishes it, a quick check's close included, and an end finishes
  nothing, exactly as at mvp-0.62; no cause or tag is stored for it.

A completion is a reading and workflow event (the section's questions, a plan's reading block, the section's reading
exposure), never evidence that the learner understood the section.
"""

from __future__ import annotations

from dataclasses import dataclass

from learnloop.algorithm_versions import section_end_on

#: The section's last readable passage was shown during the learner's own reading.
REACHED_END = "reached_end"
#: The learner said they had read it ("I've read this section").
LEARNER_SAID = "learner_said"

#: What a Reader's ``completed`` can come from; only the learner's word finishes a section from mvp-0.63.
LEARNER = "learner"


@dataclass(frozen=True)
class SectionFinish:
    completed: bool
    #: ``REACHED_END`` or ``LEARNER_SAID`` from mvp-0.63; None below it and when nothing finishes.
    cause: str | None
    #: The vault's tag the completion is written under, from mvp-0.63; None below it.
    version: str | None
    #: Whether the tag's rule applied (the report is read at mvp-0.63 or later).
    versioned: bool


def section_finish(config: object, completed: bool, completed_by: str | None, end_span_id: str | None) -> SectionFinish:
    """``completed`` and ``completed_by`` as the report sent them; ``end_span_id`` the end the report's check kept
    (None when it named none, or none that counts)."""

    if not section_end_on(config):
        return SectionFinish(completed=bool(completed), cause=None, version=None, versioned=False)
    said = bool(completed) and (completed_by is None or completed_by == LEARNER)
    reached = end_span_id is not None
    if not (said or reached):
        return SectionFinish(completed=False, cause=None, version=None, versioned=True)
    version = getattr(getattr(config, "algorithms", None), "algorithm_version", None)
    return SectionFinish(completed=True, cause=LEARNER_SAID if said else REACHED_END, version=version, versioned=True)
