"""The goal lens (Reader workbench v2 §12.2-§12.5): how critical each section is for one goal, and the
goal band's summary. The functional core: pure functions over reads gathered from the real model
(``source_retrieval.goal_lens_reads`` gathers them; the sidecar adds due checks and pace).

**Display only.** Nothing here is evidence, a plan input or a model call: a level is a deterministic
function of the deliverable's path (``deliverable_path_sections`` as the path shows it today), its
coverage (``section_coverage``'s standing rows), the LOs' certification and the learner's own choices.
No weight or threshold: every rule is an ordering or a set membership the model already defines.

**Per LO** (for each goal LO a section covers; :func:`lo_level`):

* *already shown*: demonstrated (``lo_certification``), assumed known (an open assumption, or the
  path's ``assumed`` label), or "I know this, check me later" while that check waits (the learner's
  own claim, shown as the assumed label is);
* *later*: needed only at a deeper depth than the one chosen (the path's prerequisite closure reaches
  further at a deeper depth);
* *core*: the LO's primary section on the path, with the LO needed and the treatment ``introduces``
  or ``develops``;
* *supporting*: the primary section of a prerequisite, an alternate, another section that introduces
  or develops it, or a section that applies or mentions it;
* taken out (``out``): the learner chose *skip it* on the LO's path line.

**Per section** (:func:`section_level`), mapping first. No coverage row at all is *unmapped*; a
section the path places an LO on whose coverage no longer names it, or one whose level a topic not
yet checked could still raise, is *partial*. Missing mapping never becomes "not needed": a section is
*skippable* only when it is mapped, every topic of the goal is settled, and no goal LO it covers
needs it. Otherwise the section's level is the highest-need level among its LOs (core > supporting
> later > already shown), so one shown LO never dims a section another LO still needs.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

#: Coverage's treatment vocabulary (``section_coverage.TREATMENTS``; a test pins the two equal, since
#: this module may not import ``source_retrieval``: it imports ``curriculum``, so that would cycle).
TREATMENTS: tuple[str, ...] = ("introduces", "develops", "applies", "mentions", "not_about")
PRIMARY_TREATMENTS: tuple[str, ...] = ("introduces", "develops")
TREATMENT_VERBS: dict[str, str] = {"introduces": "introduces", "develops": "develops", "applies": "uses",
                                   "mentions": "mentions"}
#: A learner's *also about…* where no judge row says how the section treats the LO (coverage's standing
#: row then has no treatment).
LEARNER_ABOUT = "learner"
ABOUT: tuple[str, ...] = (*TREATMENTS[:4], LEARNER_ABOUT)

#: The per-LO levels in need order (highest first); ``out`` is an LO the learner took off the path.
NEED_ORDER: tuple[str, ...] = ("core", "supporting", "later", "already_shown")
LO_LEVELS: tuple[str, ...] = (*NEED_ORDER, "out")
#: A section's level: a need level, or skippable, or one of the two mapping states that draw no level.
SECTION_LEVELS: tuple[str, ...] = (*NEED_ORDER, "skippable", "partial", "unmapped")
MAPPINGS: tuple[str, ...] = ("mapped", "partial", "unmapped")
#: The levels a reader dims while dimming is on (§12.3, decision D5). Dimmed is never hidden.
DIMMED: frozenset[str] = frozenset({"skippable", "later"})

#: How a goal LO belongs to the goal: needed by its scope, background at the chosen depth, or
#: background only at a deeper depth.
LO_KINDS: tuple[str, ...] = ("needed", "prerequisite", "later")

#: Why an LO or a section has its level (the frontend's keys; :func:`reason_text` words them).
REASON_KEYS: tuple[str, ...] = (
    "primary", "prerequisite", "alternate", "another_treatment", "applies", "mentions", "learner_about",
    "deeper_depth",
    "demonstrated", "assumed", "check_pending", "you_skipped", "out_of_scope", "not_about", "unmapped",
    "withheld", "left_out", "partial_unsettled", "partial_unplaced",
)


# ---------------------------------------------------------------------------
# The gathered reads
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GoalLo:
    """One LO of the goal: needed, a prerequisite at the chosen depth, or one needed only deeper."""

    learning_object_id: str
    title: str
    kind: str
    #: Its place in path order (lines first, then the goal's other LOs).
    ordinal: int
    demonstrated: bool = False
    assumed: bool = False
    #: A cold check is due on it: its purpose text is hidden until answered (§12.6.1, decision D15).
    held: bool = False
    #: A cold check on it was answered on the learner's own today.
    answered_today: bool = False


@dataclass(frozen=True)
class PathPlace:
    """An LO's line on the path as the learner sees it now (``deliverable_path.effective_lines``)."""

    learning_object_id: str
    primary: str
    #: ``(section ref, the judge's one-line difference)`` per alternate.
    alternates: tuple[tuple[str, str], ...] = ()
    #: core | prerequisite | already_shown | assumed (the honest label).
    label: str = "core"
    #: The label after the learner's choice: also ``skipped`` or ``check_pending``.
    effective: str = "core"
    reason: str = ""
    override: str | None = None

    def alternate(self, ref: str) -> tuple[str, str] | None:
        return next((entry for entry in self.alternates if entry[0] == ref), None)


@dataclass(frozen=True)
class Coverage:
    """One standing coverage row at a section (judge or learner)."""

    learning_object_id: str
    treatment: str


@dataclass(frozen=True)
class SectionReads:
    ref: str
    title: str = ""
    #: Every standing coverage row naming the section, for any LO (in the goal or not).
    coverage: tuple[Coverage, ...] = ()
    #: The goal LOs the path's current judgment places here (primary or alternate).
    placed: tuple[str, ...] = ()
    #: Protected (exam or held-out) or left out of the library: never mapped.
    protection: str | None = None
    #: The learner's choice on this section for this goal (``read_anyway``), if any.
    choice: str | None = None
    #: Goal LOs whose rows here were written against an earlier version of the section and none stands now: what
    #: they say of it is unknown (a changed section never reads as "not about" them).
    stale: tuple[str, ...] = ()


@dataclass(frozen=True)
class GoalReads:
    goal_title: str
    depth: str
    depth_label: str
    los: Mapping[str, GoalLo]
    path: Mapping[str, PathPlace] = field(default_factory=dict)
    #: Goal LOs whose coverage has not been judged for their current statement (and is not known to
    #: have no candidate section): a section such an LO could be about is not settled.
    unsettled: frozenset[str] = frozenset()


# ---------------------------------------------------------------------------
# Levels
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LoLevel:
    learning_object_id: str
    level: str
    reason_key: str
    treatment: str


@dataclass(frozen=True)
class SectionLevel:
    ref: str
    level: str
    mapping: str
    reason_key: str
    #: The LO whose level the section takes (None: unmapped, skippable without one, or partial).
    determining: str | None
    #: The goal LOs the section covers, highest need first, then path order.
    learning_objects: tuple[LoLevel, ...]
    #: Partial only: the highest-need level known so far (None when nothing known needs it).
    known_level: str | None
    held: bool
    dim: bool


def lo_level(lo: GoalLo, place: PathPlace | None, row: Coverage, ref: str) -> LoLevel:
    """One goal LO's level at the section ``ref``, which covers it with ``row``'s treatment."""

    def made(level: str, key: str) -> LoLevel:
        return LoLevel(lo.learning_object_id, level, key, row.treatment)

    if lo.demonstrated:
        return made("already_shown", "demonstrated")
    if lo.assumed or (place is not None and place.label == "assumed"):
        return made("already_shown", "assumed")
    if lo.kind == "later":
        return made("later", "deeper_depth")
    if place is not None and place.effective == "check_pending":
        return made("already_shown", "check_pending")
    if place is not None and place.effective == "skipped":
        return made("out", "you_skipped")
    if place is not None and ref == place.primary:
        if lo.kind == "needed" and row.treatment in PRIMARY_TREATMENTS:
            return made("core", "primary")
        if lo.kind == "prerequisite":
            return made("supporting", "prerequisite")
    if place is not None and place.alternate(ref) is not None:
        return made("supporting", "alternate")
    if row.treatment in PRIMARY_TREATMENTS:
        return made("supporting", "another_treatment")
    if row.treatment == LEARNER_ABOUT:
        return made("supporting", "learner_about")
    return made("supporting", "applies" if row.treatment == "applies" else "mentions")


def _need_rank(level: str) -> int:
    return NEED_ORDER.index(level) if level in NEED_ORDER else len(NEED_ORDER)


def section_level(section: SectionReads, goal: GoalReads) -> SectionLevel:
    """The section's level for the goal (the rules in this module's docstring)."""

    def done(level: str, mapping: str, key: str, *, determining: str | None = None,
             levels: tuple[LoLevel, ...] = (), known: str | None = None) -> SectionLevel:
        held = any(goal.los[entry.learning_object_id].held for entry in levels)
        return SectionLevel(ref=section.ref, level=level, mapping=mapping, reason_key=key, determining=determining,
                            learning_objects=levels, known_level=known, held=held,
                            dim=level in DIMMED and section.choice != "read_anyway")

    if section.protection is not None:
        return done("unmapped", "unmapped", section.protection)
    about = [row for row in section.coverage if row.treatment in ABOUT]
    levels = []
    for row in about:
        lo = goal.los.get(row.learning_object_id)
        if lo is not None:
            levels.append(lo_level(lo, goal.path.get(lo.learning_object_id), row, section.ref))
    ordinal = {lo_id: lo.ordinal for lo_id, lo in goal.los.items()}
    ordered = tuple(sorted(levels, key=lambda entry: (_need_rank(entry.level),
                                                      ordinal.get(entry.learning_object_id, 0),
                                                      entry.learning_object_id)))
    needed = [entry for entry in ordered if entry.level in NEED_ORDER]
    covered = {row.learning_object_id for row in about}
    unplaced = [lo_id for lo_id in section.placed if lo_id not in covered]
    if not section.coverage and not unplaced and not section.stale:
        return done("unmapped", "unmapped", "unmapped")
    best = needed[0] if needed else None
    # A topic not checked yet could still raise any level but core (the highest); a placement coverage
    # no longer names leaves the section's mapping incomplete whatever it shows.
    unsettled = (bool(goal.unsettled) or any(lo_id in goal.los for lo_id in section.stale)) and (
        best is None or best.level != "core")
    if unplaced or unsettled:
        return done("partial", "partial", "partial_unplaced" if unplaced else "partial_unsettled",
                    levels=ordered, known=best.level if best is not None else None)
    if best is not None:
        return done(best.level, "mapped", best.reason_key, determining=best.learning_object_id, levels=ordered)
    taken_out = next((entry for entry in ordered if entry.level == "out"), None)
    if taken_out is not None:
        return done("skippable", "mapped", "you_skipped", determining=taken_out.learning_object_id, levels=ordered)
    goal_not_about = any(row.treatment == "not_about" and row.learning_object_id in goal.los
                         for row in section.coverage)
    key = "out_of_scope" if about or not goal_not_about else "not_about"
    return done("skippable", "mapped", key, levels=ordered)


# ---------------------------------------------------------------------------
# Words (no model: the path's own reason where it has one, else assembled from the labels)
# ---------------------------------------------------------------------------

HELD_REASON = "A cold check is due on a topic here. Why it matters comes back once you've answered it."


def _quoted(title: str) -> str:
    return f"“{title}”"


def reason_text(level: SectionLevel, section: SectionReads, goal: GoalReads) -> str:
    """The why card's "For <goal>: <why>" line (§12.3 point 6): the path's per-section reason for a
    section it places, assembled from the labels otherwise. Hidden while a check is due (D15)."""

    if level.held:
        return HELD_REASON
    key = level.reason_key
    lo = goal.los.get(level.determining or "")
    title = _quoted(lo.title) if lo is not None else ""
    place = goal.path.get(level.determining or "")
    entry = next((e for e in level.learning_objects if e.learning_object_id == level.determining), None)
    if key in ("primary", "prerequisite") and place is not None and place.reason:
        return place.reason
    if key == "alternate" and place is not None:
        found = place.alternate(section.ref)
        if found is not None and found[1]:
            return found[1]
        return f"Another way to {title}; your path reads it elsewhere."
    words = {
        "prerequisite": f"Background for your goal: {title}.",
        "primary": f"Where your path reads {title}.",
        "another_treatment": (f"It {TREATMENT_VERBS.get(entry.treatment if entry else '', 'treats')} {title}, "
                              "a topic of your goal; your path reads it elsewhere."),
        "applies": f"It uses {title}, a topic of your goal.",
        "mentions": f"It mentions {title}, a topic of your goal.",
        "learner_about": f"You said it's also about {title}, a topic of your goal.",
        "deeper_depth": f"Needed for {title} only deeper than {goal.depth_label}.",
        "demonstrated": f"You've shown {title} on your own.",
        "assumed": f"{title} is assumed known (not tested).",
        "check_pending": f"You said you know {title}; a cold check will tell.",
        "you_skipped": f"You chose to skip {title}.",
        "out_of_scope": "Not about any topic of your goal, as far as coverage says.",
        "not_about": "Coverage judged it not about the topics of your goal.",
        "unmapped": "Not mapped for this goal yet.",
        "withheld": "Protected material: LearnLoop doesn't map it.",
        "left_out": "Not in the library LearnLoop maps (protected, or not teaching material).",
        "partial_unsettled": "Not every topic of your goal has been checked against your books yet.",
        "partial_unplaced": "Your path places a topic here that coverage no longer finds here.",
    }
    return words.get(key, "")


def learner_line(level: SectionLevel, section: SectionReads, goal: GoalReads) -> str | None:
    """The learner's own part in the level: their choice here or on the path, or today's answer."""

    if section.choice == "read_anyway":
        return "You chose to read it anyway."
    if level.held:
        return None
    place = goal.path.get(level.determining or "")
    if place is not None and place.override == "use_instead" and place.primary == section.ref:
        return "You chose to read it here."
    if place is not None and place.override == "skip":
        return "You chose to skip it."
    if place is not None and place.override == "check_later":
        return "You asked to be checked on it later."
    if place is not None and place.override == "read_anyway":
        return "You chose to read it anyway."
    if any(goal.los[entry.learning_object_id].answered_today for entry in level.learning_objects):
        return "You answered its cold check on your own today."
    return None


def coverage_line(level: SectionLevel, section: SectionReads, goal: GoalReads) -> str | None:
    """"coverage: introduces “<LO>” · a goal LO · its primary section · core" (§12.3)."""

    if level.held or level.determining is None:
        return None
    entry = next(e for e in level.learning_objects if e.learning_object_id == level.determining)
    lo = goal.los[level.determining]
    role = {"needed": "a goal LO", "prerequisite": "a prerequisite", "later": "needed at a deeper depth"}[lo.kind]
    place = goal.path.get(lo.learning_object_id)
    if place is not None and place.primary == section.ref:
        where = "its primary section"
    elif place is not None and place.alternate(section.ref) is not None:
        where = "another way"
    else:
        where = "not on your path here"
    verb = "is about (your words)" if entry.treatment == LEARNER_ABOUT else TREATMENT_VERBS.get(entry.treatment,
                                                                                                 entry.treatment)
    return f"coverage: {verb} {_quoted(lo.title)} · {role} · {where} · {level.level.replace('_', ' ')}"


def level_view(level: SectionLevel, section: SectionReads, goal: GoalReads) -> dict[str, Any]:
    """One section's level as ``goal.lens`` returns it (the frontend's marks, dimming and why card)."""

    def lo_view(entry: LoLevel) -> dict[str, Any]:
        lo = goal.los[entry.learning_object_id]
        place = goal.path.get(entry.learning_object_id)
        return {"learning_object_id": entry.learning_object_id, "title": None if lo.held else lo.title,
                "kind": lo.kind, "level": entry.level, "reason_key": entry.reason_key, "treatment": entry.treatment,
                "path_label": place.label if place is not None else None,
                "override": place.override if place is not None else None, "held": lo.held,
                "answered_today": lo.answered_today}

    return {
        "level": level.level, "mapping": level.mapping, "reason_key": level.reason_key,
        "reason_md": reason_text(level, section, goal), "known_level": level.known_level,
        "lo_ids": [entry.learning_object_id for entry in level.learning_objects],
        "learning_objects": [lo_view(entry) for entry in level.learning_objects],
        "determining_lo_id": None if level.held else level.determining,
        "learner_line": learner_line(level, section, goal), "coverage_line": coverage_line(level, section, goal),
        "held": level.held, "dim": level.dim, "choice": section.choice,
        # Decision D1: passages inherit their section's level; the card says so.
        "judged_per": "section",
    }


# ---------------------------------------------------------------------------
# The band (§12.2)
# ---------------------------------------------------------------------------

READINESS: tuple[str, ...] = ("demonstrated", "likely", "untested")


@dataclass(frozen=True)
class BandLo:
    learning_object_id: str
    title: str
    kind: str
    ordinal: int
    #: demonstrated (``lo_certification``) | likely (AD's labelled prediction) | untested.
    readiness: str
    readiness_line: str
    primary: Mapping[str, Any] | None = None
    checks_due: int = 0
    answered_today: int = 0
    held: bool = False


def band_learning_objects(los: Sequence[BandLo]) -> list[dict[str, Any]]:
    """One dot per LO in path order. While a check is due on an LO its name is not shown (D15)."""

    out = []
    for lo in sorted(los, key=lambda entry: (entry.ordinal, entry.learning_object_id)):
        check = None
        if lo.checks_due:
            check = "due"
        elif lo.answered_today:
            check = "answered"
        out.append({"learning_object_id": lo.learning_object_id, "title": None if lo.held else lo.title,
                    "kind": lo.kind, "ordinal": lo.ordinal, "readiness": lo.readiness,
                    "readiness_line": None if lo.held else lo.readiness_line,
                    "beyond_depth": lo.kind == "later", "primary": dict(lo.primary) if lo.primary else None,
                    "check": check, "held": lo.held})
    return out


def band_counts(los: Iterable[BandLo]) -> dict[str, int]:
    """"N LEARNING OBJECTS · a LIKELY · b UNTESTED": the LOs within the chosen depth."""

    within = [lo for lo in los if lo.kind != "later"]
    return {"learning_objects": len(within),
            **{state: sum(1 for lo in within if lo.readiness == state) for state in READINESS}}


@dataclass(frozen=True)
class NextLine:
    """One path line as "next for the goal" reads it."""

    learning_object_id: str
    effective: str
    section: Mapping[str, Any]
    read: bool
    held: bool = False


def next_for_goal(checks_due: int, first_check: Mapping[str, Any] | None,
                  lines: Sequence[NextLine]) -> dict[str, Any]:
    """"◇ n cold checks due today", else the next unread primary section, else "the path is read"."""

    if checks_due:
        return {"kind": "checks", "count": checks_due, "check": dict(first_check) if first_check else None}
    for line in lines:
        if line.effective in ("core", "prerequisite") and not line.read:
            return {"kind": "section", "learning_object_id": line.learning_object_id, "section": dict(line.section)}
    if any(line.effective in ("core", "prerequisite") for line in lines):
        return {"kind": "path_read"}
    return {"kind": "none"}


__all__ = [
    "BandLo", "Coverage", "GoalLo", "GoalReads", "LoLevel", "NextLine", "PathPlace", "SectionLevel",
    "SectionReads", "band_counts", "band_learning_objects", "level_view", "lo_level", "next_for_goal",
    "section_level",
]
