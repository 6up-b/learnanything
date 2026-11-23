"""What the goal lens may say while a cold check is due (spec §12.6.1, decision D15): the one place the replies of
``goal.band`` and ``goal.lens`` (and the band's path) are masked, so no client can forget it.

While any check is due on an LO **X**, in every goal, nothing these replies carry may name or describe X: not its
title or phrase, not the titles of the sections that treat it (a book's heading "Eigenvalues" names it), not a reason
or difference that explains it, not an exercise picked for it. The protection is computed from every due LO,
independently of the goal shown (:class:`Protection`): a section that covers X and another goal's Y is protected for
Y's goal too, and a reason written for Y is withheld when Y depends on X (its prerequisites, or what its section takes
as known) or when it names X.

Masking replaces text with neutral words (:data:`NEUTRAL_LO`, :data:`NEUTRAL_SECTION`, :data:`NEUTRAL_EXERCISE`) and
keeps every identifier, number and flag, so the desks still place, count and open what they show. Pure: the reads
that build a :class:`Protection` are in ``source_retrieval.goal_lens_reads``.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from learnloop.curriculum.goal_lens import HELD_REASON

#: An LO's name while its check is due (the band's own words for such a dot).
NEUTRAL_LO = "a topic with a cold check due"
#: A section's title while it treats an LO whose check is due.
NEUTRAL_SECTION = "a section held until its cold check"
#: An exercise picked from such a section.
NEUTRAL_EXERCISE = "an exercise held until its cold check"


@dataclass(frozen=True)
class Protection:
    #: Every LO with a due check, in any goal.
    held: frozenset[str] = frozenset()
    #: Their titles, folded, for the text check (a reason may name X in words).
    titles: tuple[str, ...] = ()
    #: ``extraction/section`` refs of the sections that treat a held LO (standing coverage about it, a path
    #: placement of it in any goal, a check's host).
    sections: frozenset[str] = frozenset()
    #: LOs whose explanations depend on a held LO (its prerequisites, or what a section read for it takes as known).
    depends: frozenset[str] = frozenset()

    @classmethod
    def of(cls, held: Iterable[str], titles: Iterable[str], sections: Iterable[str] = (),
           depends: Iterable[str] = ()) -> Protection:
        folded = tuple(sorted({title.casefold() for title in titles if title and title.strip()}))
        return cls(frozenset(held), folded, frozenset(sections), frozenset(depends))

    @property
    def active(self) -> bool:
        return bool(self.held)

    def names_held(self, text: Any) -> bool:
        """Whether words name a held LO: its title as whole words, in any case (so "Rank" is not "ranking")."""

        if not isinstance(text, str) or not text:
            return False
        folded = text.casefold()
        return any(re.search(rf"(?<!\w){re.escape(title)}(?!\w)", folded) for title in self.titles)

    def protects(self, extraction_id: Any, section_id: Any) -> bool:
        return f"{extraction_id}/{section_id}" in self.sections

    def lo_masked(self, lo_id: Any) -> bool:
        return lo_id in self.held


def _neutral(section: Mapping[str, Any]) -> dict[str, Any]:
    """A section reference with nothing of what it treats: neutral title, no treatment, no difference."""

    out = {**section, "title": NEUTRAL_SECTION, "held": True}
    for key, blank in (("treatment_words", ""), ("treatment", None), ("difference", "")):
        if key in out:
            out[key] = blank
    return out


def _section(section: Mapping[str, Any] | None, protection: Protection) -> dict[str, Any] | None:
    """A section reference (a path line's, an alternate, a band dot's primary, ``next``): neutral words when it
    treats a held LO or its title names one."""

    if section is None:
        return None
    out = dict(section)
    if protection.protects(out.get("extraction_id"), out.get("section_id")) or protection.names_held(out.get("title")):
        return _neutral(out)
    if protection.names_held(out.get("difference")):
        out["difference"] = ""
    return out


def protect_path(view: Mapping[str, Any] | None, protection: Protection) -> dict[str, Any] | None:
    """The band's path view: a held LO's line names nothing; any line's section, alternates, exercise and reason are
    masked by what they treat, depend on or say."""

    if view is None:
        return None
    out = dict(view)
    if not protection.active:
        return out
    lines = []
    for line in view.get("lines") or ():
        row = dict(line)
        lo_id = row.get("learning_object_id")
        held = protection.lo_masked(lo_id)
        row["section"] = _section(row.get("section"), protection)
        row["alternates"] = [_section(alternate, protection) for alternate in row.get("alternates") or ()]
        exercise = row.get("exercise")
        if exercise is not None and (held or (row["section"] or {}).get("held") or protection.names_held(exercise.get("label"))):
            row["exercise"] = {**exercise, "label": NEUTRAL_EXERCISE}
        if held:
            row["title"], row["phrase"], row["held"] = NEUTRAL_LO, "", True
            if row["section"] is not None:
                row["section"] = _neutral(row["section"])
            row["alternates"] = [_neutral(alternate) for alternate in row["alternates"]]
        if (held or lo_id in protection.depends or (row["section"] or {}).get("held")
                or protection.names_held(row.get("reason"))):
            row["reason"] = None
        lines.append(row)
    out["lines"] = lines
    out["uncovered"] = [{**entry, "title": NEUTRAL_LO, "phrase": ""} if protection.lo_masked(entry.get("learning_object_id"))
                        else dict(entry) for entry in view.get("uncovered") or ()]
    return out


def protect_band(reply: Mapping[str, Any], protection: Protection) -> dict[str, Any]:
    """``goal.band``: its dots, its next step and its path."""

    out = dict(reply)
    if not protection.active:
        return out
    dots = []
    for dot in reply.get("learning_objects") or ():
        row = dict(dot)
        if protection.lo_masked(row.get("learning_object_id")):
            row["title"], row["readiness_line"], row["held"] = None, None, True
            if row.get("primary") is not None:
                row["primary"] = _neutral(row["primary"])
        else:
            row["primary"] = _section(row.get("primary"), protection)
        dots.append(row)
    out["learning_objects"] = dots
    following = reply.get("next")
    if isinstance(following, Mapping) and following.get("kind") == "section":
        section = _section(following.get("section"), protection)
        if protection.lo_masked(following.get("learning_object_id")) and section is not None:
            section = _neutral(section)
        out["next"] = {**following, "section": section}
    out["path"] = protect_path(reply.get("path"), protection)
    return out


def protect_lens(reply: Mapping[str, Any], protection: Protection) -> dict[str, Any]:
    """``goal.lens``: a section treating a held LO (in any goal) is held: its title, reason, coverage line and every
    LO's name withheld; any other section's words are withheld where they name a held LO."""

    out = dict(reply)
    if not protection.active:
        return out
    extraction_id = reply.get("extraction_id")
    levels = []
    for level in reply.get("levels") or ():
        row = dict(level)
        held = (bool(row.get("held")) or protection.protects(extraction_id, row.get("section_id"))
                or any(protection.lo_masked(lo_id) for lo_id in row.get("lo_ids") or ())
                or protection.names_held(row.get("title")))
        if held:
            row["held"] = True
            row["title"] = NEUTRAL_SECTION
            row["reason_md"] = HELD_REASON
            row["coverage_line"] = None
            row["determining_lo_id"] = None
            if row.get("learner_line") != "You chose to read it anyway.":
                row["learner_line"] = None
            row["learning_objects"] = [{**entry, "title": None, "held": True} for entry in row.get("learning_objects") or ()]
        else:
            if protection.names_held(row.get("reason_md")) or row.get("determining_lo_id") in protection.depends:
                row["reason_md"] = HELD_REASON
            if protection.names_held(row.get("coverage_line")):
                row["coverage_line"] = None
            if protection.names_held(row.get("learner_line")):
                row["learner_line"] = None
            row["learning_objects"] = [{**entry, "title": None, "held": True} if protection.lo_masked(entry.get("learning_object_id"))
                                       else dict(entry) for entry in row.get("learning_objects") or ()]
        levels.append(row)
    out["levels"] = levels
    return out


__all__ = ["NEUTRAL_EXERCISE", "NEUTRAL_LO", "NEUTRAL_SECTION", "Protection", "protect_band", "protect_lens",
           "protect_path"]
