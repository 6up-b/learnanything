"""RW1b's five intentions (spec_reader_workbench_v1 §4.2's table; UX §4.1; gates G3, G51).

* The palette is grouped by intention (understand, apply, consolidate,
  transfer, orient) plus Mark, which has none; a group with nothing in it is
  absent (orient, until RW4a and RW7a land).
* Grouping changes no action's effect: every one of today's nine presets,
  highlight and exercise import is in the catalogue with the same preset (the
  same ``reader.invoke_preset`` call), and nothing in today's Notes palette is
  missing from it (U13: everything one key away).
* Actions of phases that have not landed are absent, not disabled.
* The learner's own notes offer only the anchor-free actions; a transcript
  takes the same box and active reading as a book.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.reader import reader_capture as RC
from learnloop.reader import reader_intent as RI
from learnloop.reader import reader_quick_check as RQC
from learnloop.vault.loader import load_vault
from tests.helpers import NOW
from tests.reader_fixtures import notes_source, transcript_source
from tests.test_reader_active_reading import ActiveClient
from tests.test_reader_guidance import _setup
from tests.test_reader_intent import FakeDecider, _prefer

ROOT = Path(__file__).resolve().parents[1]
NOTES_RAIL = ROOT / "apps" / "learnloop-tauri" / "src" / "screens" / "reader" / "NotesRail.tsx"
EVERYTHING = RI.Availability(active_reading=True, workbench=True, sources=True)
#: Actions §4.2 names for phases that have not landed (RW4b, RW4d, RW7a, DL3). RW4a's
#: "what do I need first?", "where else is this explained?" and "where is this used?" landed;
#: RW5a's "make this explorable" landed behind figures.enabled (tests/test_figures_rpc.py).
NOT_LANDED = {"compare_sources", "practice_this_question", "find_exercise", "what_matters",
              "practice_new_setting"}
RW4A_ACTIONS = {"what_do_i_need_first", "where_else_explained", "where_is_this_used"}


def test_the_palette_is_grouped_by_intention_with_mark_last():
    groups = RI.palette(EVERYTHING)
    assert [g["group"] for g in groups] == ["understand", "apply", "consolidate", "transfer", "mark"]
    assert all(g["intention"] == g["group"] for g in groups[:-1]) and groups[-1]["intention"] is None
    assert {a["intention"] for a in groups[-1]["actions"]} == {None}
    labels = {a["label"] for g in groups for a in g["actions"]}
    assert {"let me try the next step", "why does this step work?", "what does this assume?",
            "another way to see this", "reconstruct this later", "work through this"} <= labels


def test_grouping_changes_no_presets_effect():
    by_preset = {a.effect["preset"]: a for a in RI.ACTIONS if a.effect["kind"] == "preset"}
    assert set(by_preset) == set(RC.PRESETS)  # all nine, each its own preset
    for preset, action in by_preset.items():
        assert action.id == preset
    kinds = {a.effect["kind"] for a in RI.ACTIONS}
    assert kinds == {"ask", "preset", "highlight", "import_exercise", "work_through", "active_reading", "another_way",
                     "library_ask", "figure"}
    assert {a.effect["style"] for a in RI.ACTIONS if a.effect["kind"] == "active_reading"} == set(RQC.SELECTION_STYLES)


def test_nothing_in_todays_notes_palette_is_missing():
    presets = set(re.findall(r'preset:\s*"([a-z_]+)"', NOTES_RAIL.read_text(encoding="utf-8")))
    assert presets and presets <= {a.effect.get("preset") for a in RI.ACTIONS}


def test_actions_of_phases_not_landed_are_absent():
    assert not NOT_LANDED & {a.id for a in RI.ACTIONS}
    assert not [g for g in RI.palette(EVERYTHING) if g["group"] == "orient"]


def test_rw4a_adds_orient_and_transfer_library_asks_only_with_its_switch():
    with_library = RI.palette(RI.Availability(active_reading=True, workbench=True, sources=True, library=True))
    groups = {g["group"]: {a["id"] for a in g["actions"]} for g in with_library}
    assert groups["orient"] == {"what_do_i_need_first"}
    assert {"where_else_explained", "where_is_this_used"} <= groups["transfer"]
    assert [g["group"] for g in with_library] == ["understand", "apply", "consolidate", "transfer", "orient", "mark"]
    assert all(RI.ACTIONS_BY_ID[action].effect == {"kind": "library_ask", "entry": action} for action in RW4A_ACTIONS)
    assert not RW4A_ACTIONS & {a.id for a in RI.available_actions(RI.Availability(active_reading=True, sources=True))}
    # The learner's own notes keep only the anchor-free actions.
    notes = RI.Availability(active_reading=True, sources=True, library=True, notes=True)
    assert not RW4A_ACTIONS & {a.id for a in RI.available_actions(notes)}


def test_switches_remove_their_actions():
    ids = {a.id for a in RI.available_actions(RI.Availability())}
    assert not ids & {"next_step", "why_step", "assumptions", "reconstruct", "another_way", "work_through"}
    assert "another_way" not in {a.id for a in RI.available_actions(RI.Availability(active_reading=True))}
    protected = {a.id for a in RI.available_actions(RI.Availability(active_reading=True, model=False))}
    assert protected == {"highlight", "note", "mark_confusing", "not_worth_remembering"}


def test_the_notes_pane_offers_only_the_anchor_free_actions():
    notes = {a.id for a in RI.available_actions(RI.Availability(active_reading=True, workbench=True, sources=True,
                                                                notes=True))}
    assert notes == set(RI.ANCHOR_FREE_ACTIONS)


@pytest.mark.parametrize("source", ["transcript", "notes"])
def test_the_box_routes_on_every_source_kind(tmp_path, source):
    vault, repo = _setup(tmp_path)
    fixture = transcript_source(repo) if source == "transcript" else notes_source(repo)
    vault = load_vault(vault.root)
    decider = FakeDecider(choice=_prefer("test_me_later"))
    routing = RI.route(vault.root, vault.config, repo, text="quiz me on this later", quote="the density",
                       extraction_id=fixture["extraction_id"], span_ids=[fixture["span_id"]],
                       available=RI.Availability.from_config(vault.config, notes=source == "notes"),
                       client_factory=lambda: decider, clock=FrozenClock(NOW))
    assert routing.action == "test_me_later"
    options = set(decider.calls[0]["questions"][RI.QUESTION_NAME].options)
    if source == "notes":
        assert options == set(RI.ANCHOR_FREE_ACTIONS)
    else:
        assert "next_step" in options


def test_active_reading_works_on_a_transcript(tmp_path):
    vault, repo = _setup(tmp_path)
    fixture = transcript_source(repo)
    folded = RQC.folded_span_ids(repo, extraction_id=fixture["extraction_id"], anchor_span_ids=["s1"])
    assert folded  # the cues after the selected one fold
    row = RQC.author_selection_question(
        repo, ActiveClient(), extraction_id=fixture["extraction_id"], anchor_span_ids=["s1"], style="next_step",
        clock=FrozenClock(NOW), owner="job_t",
    )
    assert row["answer_basis"] == "source" and row["expected_answer_md"]


def test_the_readers_test_fixture_is_the_sidecars_palette():
    """The frontend's RW1b tests use a copy of the contract; it must not drift."""

    import json

    from learnloop.config.schema import LearnLoopConfig
    from learnloop_sidecar.dto import to_camel

    fixture = ROOT / "apps" / "learnloop-tauri" / "src" / "fixtures" / "readerIntentContract.ts"
    text = fixture.read_text(encoding="utf-8")
    body = text[text.index("= {") + 2:text.rindex("};") + 1]
    config = LearnLoopConfig()
    expected = to_camel({
        "palette": RI.palette(RI.Availability.from_config(config)),
        "notes_palette": RI.palette(RI.Availability.from_config(config, notes=True)),
        "speculative": True, "speculate_after_ms": 600, "timeout_seconds": 4.0,
    })
    assert json.loads(body) == expected
