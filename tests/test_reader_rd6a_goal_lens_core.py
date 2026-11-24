"""The goal lens's level rules (Reader workbench v2 §12.3, §18.1 "Goal lens"): one table row per rule,
including unmapped, partial and multi-LO sections, run through the pure core with plain values."""
from __future__ import annotations

import pytest

from learnloop.curriculum import goal_lens as GL
from learnloop.source_retrieval import section_coverage as SC

HERE = "ext_book/sec_here"
ELSEWHERE = "ext_lay/sec_other"

LOS = {
    "lo_a": GL.GoalLo("lo_a", "Eigenvalues", "needed", 0),
    "lo_b": GL.GoalLo("lo_b", "Determinants", "prerequisite", 1),
    "lo_c": GL.GoalLo("lo_c", "Bases", "needed", 2),
    "lo_shown": GL.GoalLo("lo_shown", "Vectors", "needed", 3, demonstrated=True),
    "lo_assumed": GL.GoalLo("lo_assumed", "Scalars", "prerequisite", 4, assumed=True),
    "lo_deep": GL.GoalLo("lo_deep", "Fields", "later", 5),
    "lo_deep_shown": GL.GoalLo("lo_deep_shown", "Groups", "later", 6, demonstrated=True),
    "lo_held": GL.GoalLo("lo_held", "Traces", "needed", 7, held=True),
}


def place(lo, primary=HERE, *, alternates=(), label="core", effective=None, reason="Clear here.", override=None):
    return GL.PathPlace(lo, primary, tuple(alternates), label, effective or label, reason, override)


def cov(*pairs):
    return tuple(GL.Coverage(lo, treatment) for lo, treatment in pairs)


# Each row: (rule, coverage rows at HERE, path places, placed here, unsettled, choice,
#            expected (level, mapping, reason_key, determining, dim, known_level))
ROWS = [
    # -- mapping state first
    ("unmapped: no coverage row names the section", (), {}, (), (), None,
     ("unmapped", "unmapped", "unmapped", None, False, None)),
    ("unmapped never dims, even with topics unsettled", (), {}, (), ("lo_c",), None,
     ("unmapped", "unmapped", "unmapped", None, False, None)),
    ("partial: the path places an LO here that coverage no longer names", cov(("lo_c", "mentions")),
     {"lo_a": place("lo_a")}, ("lo_a",), (), None,
     ("partial", "partial", "partial_unplaced", None, False, "supporting")),
    ("partial: placed here with no coverage row at all", (), {"lo_a": place("lo_a")}, ("lo_a",), (), None,
     ("partial", "partial", "partial_unplaced", None, False, None)),
    ("partial: an unchecked topic could still need a section only about other books' topics",
     cov(("lo_other", "develops")), {}, (), ("lo_c",), None,
     ("partial", "partial", "partial_unsettled", None, False, None)),
    ("partial: an unchecked topic could raise supporting", cov(("lo_a", "mentions")), {}, (), ("lo_c",), None,
     ("partial", "partial", "partial_unsettled", None, False, "supporting")),
    ("an unchecked topic cannot raise core: the section is settled", cov(("lo_a", "develops")),
     {"lo_a": place("lo_a")}, ("lo_a",), ("lo_c",), None,
     ("core", "mapped", "primary", "lo_a", False, None)),
    # -- per-LO rules (one LO each)
    ("core: a needed LO's primary, introduces", cov(("lo_a", "introduces")), {"lo_a": place("lo_a")}, ("lo_a",),
     (), None, ("core", "mapped", "primary", "lo_a", False, None)),
    ("core: a needed LO's primary, develops", cov(("lo_a", "develops")), {"lo_a": place("lo_a")}, ("lo_a",),
     (), None, ("core", "mapped", "primary", "lo_a", False, None)),
    ("core after use this one instead (the primary moved here)", cov(("lo_a", "develops")),
     {"lo_a": place("lo_a", override="use_instead", alternates=((ELSEWHERE, ""),))}, ("lo_a",), (), None,
     ("core", "mapped", "primary", "lo_a", False, None)),
    ("supporting: a prerequisite's primary", cov(("lo_b", "develops")),
     {"lo_b": place("lo_b", label="prerequisite")}, ("lo_b",), (), None,
     ("supporting", "mapped", "prerequisite", "lo_b", False, None)),
    ("supporting: an alternate on the path", cov(("lo_a", "develops")),
     {"lo_a": place("lo_a", ELSEWHERE, alternates=((HERE, "a geometric view"),))}, ("lo_a",), (), None,
     ("supporting", "mapped", "alternate", "lo_a", False, None)),
    ("supporting: another section that develops it, not on the path here", cov(("lo_a", "develops")),
     {"lo_a": place("lo_a", ELSEWHERE)}, (), (), None,
     ("supporting", "mapped", "another_treatment", "lo_a", False, None)),
    ("supporting: applies", cov(("lo_a", "applies")), {"lo_a": place("lo_a", ELSEWHERE)}, (), (), None,
     ("supporting", "mapped", "applies", "lo_a", False, None)),
    ("supporting: mentions", cov(("lo_a", "mentions")), {"lo_a": place("lo_a", ELSEWHERE)}, (), (), None,
     ("supporting", "mapped", "mentions", "lo_a", False, None)),
    ("supporting: the learner's also about, with no judged treatment", cov(("lo_c", "learner")), {}, (), (),
     None, ("supporting", "mapped", "learner_about", "lo_c", False, None)),
    ("supporting: a needed LO with no path line (not judged yet) that develops here", cov(("lo_c", "develops")),
     {}, (), (), None, ("supporting", "mapped", "another_treatment", "lo_c", False, None)),
    ("later: needed only at a deeper depth", cov(("lo_deep", "develops")), {}, (), (), None,
     ("later", "mapped", "deeper_depth", "lo_deep", True, None)),
    ("later stays lit when the learner chose to read it anyway", cov(("lo_deep", "develops")), {}, (), (),
     "read_anyway", ("later", "mapped", "deeper_depth", "lo_deep", False, None)),
    ("already shown: demonstrated", cov(("lo_shown", "develops")), {"lo_shown": place("lo_shown",
                                                                                     label="already_shown")},
     ("lo_shown",), (), None, ("already_shown", "mapped", "demonstrated", "lo_shown", False, None)),
    ("already shown before later: a deeper LO already demonstrated", cov(("lo_deep_shown", "develops")), {}, (),
     (), None, ("already_shown", "mapped", "demonstrated", "lo_deep_shown", False, None)),
    ("already shown: assumed known (an open assumption)", cov(("lo_assumed", "develops")), {}, (), (), None,
     ("already_shown", "mapped", "assumed", "lo_assumed", False, None)),
    ("already shown: the path's assumed label", cov(("lo_a", "develops")),
     {"lo_a": place("lo_a", label="assumed")}, ("lo_a",), (), None,
     ("already_shown", "mapped", "assumed", "lo_a", False, None)),
    ("already shown: I know this, check me later, while the check waits", cov(("lo_a", "develops")),
     {"lo_a": place("lo_a", effective="check_pending", override="check_later")}, ("lo_a",), (), None,
     ("already_shown", "mapped", "check_pending", "lo_a", False, None)),
    # -- skippable
    ("skippable: mapped, every covered LO out of the goal's scope", cov(("lo_other", "develops")), {}, (), (),
     None, ("skippable", "mapped", "out_of_scope", None, True, None)),
    ("skippable: the judge marked it not about the goal's LOs", cov(("lo_a", "not_about")),
     {"lo_a": place("lo_a", ELSEWHERE)}, (), (), None, ("skippable", "mapped", "not_about", None, True, None)),
    ("skippable: the learner skipped its only goal LO", cov(("lo_a", "develops")),
     {"lo_a": place("lo_a", effective="skipped", override="skip")}, ("lo_a",), (), None,
     ("skippable", "mapped", "you_skipped", "lo_a", True, None)),
    ("skippable stays lit when the learner chose to read it anyway", cov(("lo_other", "develops")), {}, (), (),
     "read_anyway", ("skippable", "mapped", "out_of_scope", None, False, None)),
    # -- multi-LO sections: the highest-need level
    ("multi-LO: a demonstrated LO never dims a section another LO needs",
     cov(("lo_shown", "develops"), ("lo_a", "mentions")), {"lo_a": place("lo_a", ELSEWHERE)}, (), (), None,
     ("supporting", "mapped", "mentions", "lo_a", False, None)),
    ("multi-LO: core beats supporting, later and already shown",
     cov(("lo_shown", "develops"), ("lo_deep", "develops"), ("lo_b", "applies"), ("lo_a", "introduces")),
     {"lo_a": place("lo_a")}, ("lo_a",), (), None, ("core", "mapped", "primary", "lo_a", False, None)),
    ("multi-LO: later beats already shown", cov(("lo_shown", "develops"), ("lo_deep", "develops")), {}, (), (),
     None, ("later", "mapped", "deeper_depth", "lo_deep", True, None)),
    ("multi-LO: an out-of-scope LO beside a goal LO never makes it skippable",
     cov(("lo_other", "develops"), ("lo_b", "mentions")), {}, (), (), None,
     ("supporting", "mapped", "mentions", "lo_b", False, None)),
    ("multi-LO: a skipped LO beside a needed one keeps the needed level",
     cov(("lo_a", "develops"), ("lo_c", "mentions")),
     {"lo_a": place("lo_a", effective="skipped", override="skip")}, ("lo_a",), (), None,
     ("supporting", "mapped", "mentions", "lo_c", False, None)),
    ("multi-LO: equal need goes to path order", cov(("lo_c", "mentions"), ("lo_a", "mentions")), {}, (), (),
     None, ("supporting", "mapped", "mentions", "lo_a", False, None)),
]


@pytest.mark.parametrize("rule, coverage, path, placed, unsettled, choice, expected", ROWS,
                         ids=[row[0] for row in ROWS])
def test_every_level_rule(rule, coverage, path, placed, unsettled, choice, expected):
    goal = GL.GoalReads("my midterm", "learn_to_use_it", "learn to use it", LOS, path, frozenset(unsettled))
    section = GL.SectionReads(HERE, "Here", coverage, placed, None, choice)
    level = GL.section_level(section, goal)
    got = (level.level, level.mapping, level.reason_key, level.determining, level.dim, level.known_level)
    assert got == expected, rule
    assert level.level in GL.SECTION_LEVELS and level.mapping in GL.MAPPINGS
    assert level.reason_key in GL.REASON_KEYS
    view = GL.level_view(level, section, goal)
    assert view["judged_per"] == "section" and view["reason_md"]


@pytest.mark.parametrize("protection", ["withheld", "left_out"])
def test_protected_or_left_out_sections_are_never_mapped(protection):
    goal = GL.GoalReads("g", "fluency", "fluency", LOS, {"lo_a": place("lo_a")})
    section = GL.SectionReads(HERE, "Here", cov(("lo_a", "develops")), ("lo_a",), protection)
    level = GL.section_level(section, goal)
    assert (level.level, level.mapping, level.reason_key, level.learning_objects) == (
        "unmapped", "unmapped", protection, ())


def test_a_held_lo_hides_the_purpose_text_of_every_section_it_is_in():
    goal = GL.GoalReads("g", "fluency", "fluency", LOS, {"lo_held": place("lo_held", reason="The trace's home.")})
    section = GL.SectionReads(HERE, "Here", cov(("lo_held", "develops"), ("lo_b", "mentions")), ("lo_held",))
    level = GL.section_level(section, goal)
    view = GL.level_view(level, section, goal)
    assert level.level == "core" and level.held
    assert view["reason_md"] == GL.HELD_REASON and view["coverage_line"] is None
    assert view["determining_lo_id"] is None
    held = next(entry for entry in view["learning_objects"] if entry["learning_object_id"] == "lo_held")
    assert held["title"] is None and "The trace's home." not in str(view)
    assert "Traces" not in str(view)


def test_reason_text_is_the_paths_own_line_on_the_path_and_assembled_off_it():
    goal = GL.GoalReads("g", "get_the_idea", "get the idea", LOS,
                        {"lo_a": place("lo_a", reason="Strang's chapter is the clearest for you."),
                         "lo_b": place("lo_b", ELSEWHERE, label="prerequisite",
                                       alternates=((HERE, "shorter, with pictures"),))})
    primary = GL.SectionReads(HERE, "Here", cov(("lo_a", "develops")), ("lo_a",))
    level = GL.section_level(primary, goal)
    assert GL.reason_text(level, primary, goal) == "Strang's chapter is the clearest for you."
    assert GL.coverage_line(level, primary, goal) == (
        "This section develops “Eigenvalues” · goal topic · main reading")
    alternate = GL.SectionReads(HERE, "Here", cov(("lo_b", "develops")), ("lo_b",))
    assert GL.reason_text(GL.section_level(alternate, goal), alternate, goal) == "shorter, with pictures"
    deep = GL.SectionReads(HERE, "Here", cov(("lo_deep", "applies")))
    assert GL.reason_text(GL.section_level(deep, goal), deep, goal) == (
        "Needed for “Fields” only at a deeper level than get the idea.")


def test_the_learner_line_names_their_choice_or_todays_answer():
    los = {**LOS, "lo_c": GL.GoalLo("lo_c", "Bases", "needed", 2, answered_today=True)}
    goal = GL.GoalReads("g", "fluency", "fluency", los,
                        {"lo_a": place("lo_a", override="use_instead")})
    here = GL.SectionReads(HERE, "Here", cov(("lo_a", "develops")), ("lo_a",))
    assert GL.learner_line(GL.section_level(here, goal), here, goal) == "You chose to read it here."
    answered = GL.SectionReads(HERE, "Here", cov(("lo_c", "develops")))
    assert GL.learner_line(GL.section_level(answered, goal), answered, goal) == (
        "You answered its cold check on your own today.")
    kept = GL.SectionReads(HERE, "Here", cov(("lo_other", "develops")), choice="read_anyway")
    assert GL.learner_line(GL.section_level(kept, goal), kept, goal) == "You chose to read it anyway."


def test_the_cores_vocabulary_is_coverages():
    assert GL.TREATMENTS == SC.TREATMENTS
    assert set(GL.TREATMENT_VERBS) == set(SC.ABOUT)


def test_the_band_counts_within_the_depth_and_hides_held_names():
    los = [
        GL.BandLo("lo_a", "Eigenvalues", "needed", 0, "demonstrated", "Shown on your own."),
        GL.BandLo("lo_b", "Determinants", "prerequisite", 1, "likely", "likely"),
        GL.BandLo("lo_c", "Bases", "needed", 2, "untested", "Not tested.", checks_due=1, held=True),
        GL.BandLo("lo_deep", "Fields", "later", 3, "untested", "Not tested."),
    ]
    assert GL.band_counts(los) == {"learning_objects": 3, "demonstrated": 1, "likely": 1, "untested": 1}
    dots = GL.band_learning_objects(los)
    assert [dot["learning_object_id"] for dot in dots] == ["lo_a", "lo_b", "lo_c", "lo_deep"]
    held = dots[2]
    assert held["title"] is None and held["check"] == "due" and held["readiness_line"] is None
    assert dots[3]["beyond_depth"] and not dots[0]["beyond_depth"]


def test_next_for_the_goal_is_checks_then_the_next_unread_primary_then_read():
    section = {"extraction_id": "ext_book", "section_id": "sec_here"}
    lines = [GL.NextLine("lo_a", "core", section, read=True),
             GL.NextLine("lo_b", "skipped", section, read=False),
             GL.NextLine("lo_c", "prerequisite", {"section_id": "sec_c"}, read=False)]
    assert GL.next_for_goal(2, {"commitment_id": "c1"}, lines) == {
        "kind": "checks", "count": 2, "check": {"commitment_id": "c1"}}
    assert GL.next_for_goal(0, None, lines) == {"kind": "section", "learning_object_id": "lo_c",
                                                "section": {"section_id": "sec_c"}}
    assert GL.next_for_goal(0, None, lines[:2]) == {"kind": "path_read"}
    assert GL.next_for_goal(0, None, []) == {"kind": "none"}
