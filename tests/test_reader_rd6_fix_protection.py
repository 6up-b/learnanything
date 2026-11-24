"""A due check's protection (spec §12.6.1, decision D15): while a cold check is due on an LO, nothing the goal
lens's replies carry names or describes it: not in a held LO's own path row (its title, phrase, section titles,
treatment words, alternates, exercise), and not across LOs or goals (a section covering X and Y, with X's check due,
names nothing of X in Y's goal; a reason written for Y that names X, or that depends on X, is withheld). The masking
is one server function over every text-bearing field (``curriculum.goal_lens``, its protection); every model is a fake."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from learnloop.curriculum import commitments as C
from learnloop.curriculum import goal_lens as GL
from learnloop.source_retrieval import deliverable_path as DP
from learnloop.source_retrieval import section_coverage as SC
from learnloop.vault.loader import load_vault
from tests.goal_lens_helpers import build_lens_vault, lens_context, scoped_goal
from tests.reading_path_fixtures import call
from tests.section_coverage_fixtures import CoverageJudgeFake

X = "Eigenvalues"
P = GL.Protection.of(["lo_x"], [X], ["ext_book/ch_x", "ext_book/ch_shared"], ["lo_dep"])


def _strings(value: Any, path: str = "") -> list[tuple[str, str]]:
    """Every string in a reply, with where it is."""

    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, dict):
        return [found for key, child in value.items() for found in _strings(child, f"{path}.{key}" if path else key)]
    if isinstance(value, list):
        return [found for index, child in enumerate(value) for found in _strings(child, f"{path}[{index}]")]
    return []


def _identifier(path: str) -> bool:
    """Ids name nothing to the learner (``lo_eigen``, ``ch_eigen``): kept, so the desks still place what they show."""

    import re

    return re.search(r"(_id|Id|_ids|Ids)(\[\d+\])?$", path) is not None


def _section(section_id: str, title: str, **extra: Any) -> dict[str, Any]:
    return {"extraction_id": "ext_book", "section_id": section_id, "title": title, "book": "Linear Algebra Notes",
            "treatment": "develops", "treatment_words": "develops it", "start_span_id": "s1", **extra}


def _band() -> dict[str, Any]:
    line_x = {"learning_object_id": "lo_x", "title": X, "phrase": "eigenvalues of a matrix", "reason": f"Read {X} here.",
              "section": _section("ch_x", f"Chapter 5 {X}"),
              "alternates": [_section("ch_alt", f"{X} again", difference=f"a slower {X} proof")],
              "exercise": {"label": f"Exercise 5.1 ({X})", "extraction_id": "ext_book", "span_ids": ["s9"]}}
    line_shared = {"learning_object_id": "lo_y", "title": "Determinants", "phrase": "determinants",
                   "reason": "The determinant, from the shared chapter.", "section": _section("ch_shared", "Chapter 4 Both"),
                   "alternates": [], "exercise": {"label": "Exercise 4.2", "extraction_id": "ext_book", "span_ids": ["s8"]}}
    line_names = {"learning_object_id": "lo_z", "title": "Diagonalization", "phrase": "diagonalize",
                  "reason": f"Use {X.lower()} to diagonalize.", "section": _section("ch_z", "Chapter 6 Diagonal"),
                  "alternates": [_section("ch_z2", "Chapter 7", difference=f"needs {X.lower()} first")], "exercise": None}
    line_dep = {"learning_object_id": "lo_dep", "title": "Spectra", "phrase": "spectra", "reason": "Builds on what came before.",
                "section": _section("ch_dep", "Chapter 8 Spectra"), "alternates": [], "exercise": None}
    line_clean = {"learning_object_id": "lo_w", "title": "Rows", "phrase": "rows", "reason": "Row swaps, plainly.",
                  "section": _section("ch_w", "Chapter 2 Rows"), "alternates": [], "exercise": None}
    return {
        "goal": {"title": "eigenvalues for the midterm", "sentence": "eigenvalues for the midterm"},
        "learning_objects": [{"learning_object_id": "lo_x", "title": X, "readiness_line": f"{X}: likely",
                              "primary": _section("ch_x", f"Chapter 5 {X}"), "held": False},
                             {"learning_object_id": "lo_y", "title": "Determinants", "readiness_line": "likely",
                              "primary": _section("ch_shared", "Chapter 4 Both"), "held": False}],
        "next": {"kind": "section", "learning_object_id": "lo_y", "section": _section("ch_shared", "Chapter 4 Both")},
        "path": {"title": "eigenvalues for the midterm", "sentence": "eigenvalues for the midterm",
                 "lines": [line_x, line_shared, line_names, line_dep, line_clean],
                 "uncovered": [{"learning_object_id": "lo_x", "title": X, "phrase": "eigen"}]},
    }


def _lens() -> dict[str, Any]:
    def level(section_id: str, title: str, lo_ids: list[str], **extra: Any) -> dict[str, Any]:
        return {"section_id": section_id, "title": title, "lo_ids": lo_ids, "held": False, "level": "supporting",
                "reason_md": f"It uses {X}.", "coverage_line": f"coverage: develops “{X}”", "learner_line": None,
                "determining_lo_id": lo_ids[0] if lo_ids else None,
                "learning_objects": [{"learning_object_id": lo, "title": X if lo == "lo_x" else "Other"} for lo in lo_ids],
                **extra}
    return {"extraction_id": "ext_book", "levels": [
        level("ch_shared", "Chapter 4 Both", ["lo_y"]),                       # covers X too, though X is not in this goal
        level("ch_named", f"{X} in passing", []),                             # its title names X
        level("ch_reason", "Chapter 6", ["lo_z"], reason_md=f"Use {X.lower()} here.", coverage_line="coverage: applies “Z”"),
        level("ch_dep", "Chapter 8", ["lo_dep"], reason_md="Builds on it.", coverage_line="coverage: develops “Spectra”"),
        level("ch_clean", "Chapter 2", ["lo_w"], reason_md="Row swaps.", coverage_line="coverage: develops “Rows”"),
    ]}


# The table: every text-bearing field of the band, its path and the lens, and what it becomes.
BAND_TABLE = [
    ("learning_objects[0].title", None), ("learning_objects[0].readiness_line", None),
    ("learning_objects[0].primary.title", GL.NEUTRAL_SECTION), ("learning_objects[1].primary.title", GL.NEUTRAL_SECTION),
    ("learning_objects[1].title", "Determinants"), ("next.section.title", GL.NEUTRAL_SECTION),
    ("path.lines[0].title", GL.NEUTRAL_LO), ("path.lines[0].phrase", ""), ("path.lines[0].reason", None),
    ("path.lines[0].section.title", GL.NEUTRAL_SECTION), ("path.lines[0].section.treatment_words", ""),
    ("path.lines[0].alternates[0].title", GL.NEUTRAL_SECTION), ("path.lines[0].alternates[0].difference", ""),
    ("path.lines[0].exercise.label", GL.NEUTRAL_EXERCISE),
    ("path.lines[1].title", "Determinants"), ("path.lines[1].reason", None),
    ("path.lines[1].section.title", GL.NEUTRAL_SECTION), ("path.lines[1].exercise.label", GL.NEUTRAL_EXERCISE),
    ("path.lines[2].reason", None), ("path.lines[2].alternates[0].difference", ""),
    ("path.lines[2].alternates[0].title", "Chapter 7"), ("path.lines[2].section.title", "Chapter 6 Diagonal"),
    ("path.lines[3].reason", None),
    ("path.lines[4].reason", "Row swaps, plainly."), ("path.lines[4].section.title", "Chapter 2 Rows"),
    ("path.uncovered[0].title", GL.NEUTRAL_LO), ("path.uncovered[0].phrase", ""),
]
LENS_TABLE = [
    ("levels[0].title", GL.NEUTRAL_SECTION), ("levels[0].reason_md", GL.HELD_REASON), ("levels[0].coverage_line", None),
    ("levels[0].held", True), ("levels[0].determining_lo_id", None), ("levels[0].learning_objects[0].title", None),
    ("levels[1].title", GL.NEUTRAL_SECTION), ("levels[1].reason_md", GL.HELD_REASON),
    ("levels[2].reason_md", GL.HELD_REASON), ("levels[2].coverage_line", "coverage: applies “Z”"), ("levels[2].held", False),
    ("levels[3].reason_md", GL.HELD_REASON),
    ("levels[4].reason_md", "Row swaps."), ("levels[4].title", "Chapter 2"), ("levels[4].held", False),
]
#: The learner's own words, kept: the goal's sentence (no LO's text).
KEPT = ("goal.title", "goal.sentence", "path.title", "path.sentence")


def _at(reply: Any, path: str) -> Any:
    value = reply
    for part in path.replace("]", "").replace("[", ".").split("."):
        value = value[int(part)] if part.isdigit() else value[part]
    return value


@pytest.mark.parametrize(("path", "expected"), BAND_TABLE)
def test_every_text_bearing_band_field_is_masked(path, expected):
    assert _at(GL.protect_band(_band(), P), path) == expected


@pytest.mark.parametrize(("path", "expected"), LENS_TABLE)
def test_every_text_bearing_lens_field_is_masked(path, expected):
    assert _at(GL.protect_lens(_lens(), P), path) == expected


def test_no_string_left_names_the_held_lo_and_nothing_changes_without_a_due_check():
    band, lens = GL.protect_band(_band(), P), GL.protect_lens(_lens(), P)
    leaks = [(path, text) for path, text in _strings(band) + _strings(lens)
             if X.casefold() in text.casefold() and path not in KEPT and not _identifier(path)]
    assert leaks == []
    # Identifiers stay, so the desks still place and open what they show.
    assert band["path"]["lines"][0]["section"]["section_id"] == "ch_x" and band["learning_objects"][0]["learning_object_id"] == "lo_x"
    assert GL.protect_band(_band(), GL.Protection()) == _band() and GL.protect_lens(_lens(), GL.Protection()) == _lens()


def test_a_title_is_matched_as_whole_words():
    rank = GL.Protection.of(["lo_r"], ["Rank"])
    assert rank.names_held("the rank of A") and rank.names_held("Rank-nullity") and not rank.names_held("ranking the rows")


# -- the replies, end to end ----------------------------------------------------------------------------------------

def _due_check(repository, lo_id):
    """A due check on the LO, begun inline (the replies mask a check's LO only once it is begun)."""

    from tests.inline_hold_helpers import hold_open

    due = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
    commitment_id = C.create_commitment(
        repository, action="test_me_later", intent_text=f"check {lo_id}", depth_preset=DP.READY_DEPTH_PRESET,
        targets=[{"target_kind": "learning_object", "target_ref": lo_id, "role": "required"}],
        client_idempotency_key=f"rd6fix:{lo_id}", due_hint=due, provenance={"via": "deliverable_ready"}).id
    hold_open(repository, commitment_id)
    return commitment_id


def _shared_vault(tmp_path):
    """``ch_eigen`` treats Eigenvalues (develops) and Determinants (applies); ``ch_det`` treats Determinants."""

    paths, repository = build_lens_vault(tmp_path / "vault", cover=())
    vault = load_vault(paths.root)
    SC.judge(vault, repository, "lo_eigen", client=CoverageJudgeFake())
    SC.judge(vault, repository, "lo_det", client=CoverageJudgeFake(treatments={"Chapter 5 Eigenvalues": "applies"}))
    return paths, repository


def _leaks(reply: Any, word: str) -> list[tuple[str, str]]:
    kept = ("goal.title", "goal.sentence", "path.title", "path.sentence", "unmatched")
    return [(path, text) for path, text in _strings(reply) if word in text.casefold() and not _identifier(path)
            and not any(path == k or path.startswith(f"{k}[") for k in kept)]


def test_another_goals_due_check_masks_a_shared_section_and_names_nothing_of_it(tmp_path):
    paths, repository = _shared_vault(tmp_path)
    goal_id = scoped_goal(paths, repository, sentence="determinants")
    _due_check(repository, "lo_eigen")
    ctx = lens_context(paths)
    band = call(ctx, "goal.band", {"goal_id": goal_id})
    lens = call(ctx, "goal.lens", {"goal_id": goal_id, "extraction_id": "ext_book"})
    assert _leaks(band, "eigen") == [] and _leaks(lens, "eigen") == []
    shared = next(level for level in lens["levels"] if level["sectionId"] == "ch_eigen")
    assert shared["held"] and shared["reasonMd"] == GL.HELD_REASON and shared["title"] == GL.NEUTRAL_SECTION
    # The determinants chapter, which treats nothing held, keeps its words.
    det = next(level for level in lens["levels"] if level["sectionId"] == "ch_det")
    assert not det["held"] and det["title"] == "Chapter 3 Determinants"


def test_a_held_los_own_path_row_names_nothing(tmp_path):
    paths, repository = build_lens_vault(tmp_path / "vault")
    goal_id = scoped_goal(paths, repository)
    _due_check(repository, "lo_eigen")
    ctx = lens_context(paths)
    band = call(ctx, "goal.band", {"goal_id": goal_id})
    lens = call(ctx, "goal.lens", {"goal_id": goal_id, "extraction_id": "ext_book"})
    assert _leaks(band, "eigen") == [] and _leaks(lens, "eigen") == []
    line = next(line for line in band["path"]["lines"] if line["learningObjectId"] == "lo_eigen")
    assert (line["title"], line["section"]["title"], line["reason"]) == (GL.NEUTRAL_LO, GL.NEUTRAL_SECTION, None)


def test_a_goals_own_words_keep_everything_but_a_held_topics_name():
    assert P.mask_names("Understand eigenvalues well enough to diagonalize") == (
        f"Understand {GL.HIDDEN_TOPIC} well enough to diagonalize")
    assert P.mask_names("eigenvaluesque words") == "eigenvaluesque words"
    assert GL.Protection().mask_names("Understand eigenvalues") == "Understand eigenvalues"
    rows = GL.protect_unmatched([{"phrase": "eigenvalues by hand", "proposed_title": "Eigenvalues by hand"},
                                 {"phrase": "pivots", "proposed_title": "Pivots"}], P)
    assert rows[0] == {"phrase": f"{GL.HIDDEN_TOPIC} by hand", "proposed_title": f"{GL.HIDDEN_TOPIC} by hand", "held": True}
    assert rows[1] == {"phrase": "pivots", "proposed_title": "Pivots"}


def test_the_band_and_the_chooser_show_the_goal_in_the_learners_words_masked_only_while_its_check_is_due(tmp_path):
    paths, repository = build_lens_vault(tmp_path / "vault")
    sentence = "understand eigenvalues well enough to diagonalize"
    goal_id = scoped_goal(paths, repository, sentence=sentence)
    ctx = lens_context(paths)
    assert call(ctx, "goal.band", {"goal_id": goal_id})["goal"]["sentence"] == sentence
    chosen = next(g for g in call(ctx, "goal.choices", {})["goals"] if g["goalId"] == goal_id)
    assert chosen["label"] == sentence
    _due_check(repository, "lo_eigen")
    masked = f"understand {GL.HIDDEN_TOPIC} well enough to diagonalize"
    band = call(ctx, "goal.band", {"goal_id": goal_id})
    assert band["goal"]["sentence"] == masked and "eigen" not in band["goal"]["title"].casefold()
    assert all("eigen" not in str(row).casefold() for row in band.get("unmatched") or [])
    chosen = next(g for g in call(ctx, "goal.choices", {})["goals"] if g["goalId"] == goal_id)
    assert chosen["label"] == masked
