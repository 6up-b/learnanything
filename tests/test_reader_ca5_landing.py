"""Reader CA5 landing onto main: its interactions with CA5a and curriculum C0a/C0b.

(i) CA5's one line and CA5a's footer action never both show for one section:
    the quiet read is ``judged`` (CA5's line) or not (CA5a's action), never
    both. A CA5 *not about this* naming LOs and CA5a's dismiss of the same hit
    (every LO of the open section) stay consistent through undo: the newest
    correction per LO and the newest pair verdict decide, so the judged line,
    the quiet status and CA5a's search hit always agree. (The frontend side,
    the action appearing once the last line is corrected away and hiding again
    on undo, is pinned in alsoInBooksReader.test.tsx.)
(ii) ``curriculum.enabled`` off and ``reader.correspondence.enabled`` off each
    restore today's Reader: no ``correspondence`` key in the prompt contract,
    the palette unchanged, and every CA5 RPC refused or reporting off.
(iii) The hide preferences survive a vault reload (a new sidecar on the same
    vault reads them) and a second sidecar's write (neither loses the other's).

Every model is a fake; nothing leaves the machine.
"""
from __future__ import annotations

import copy
from typing import Any

import pytest

from learnloop_sidecar.errors import SidecarError
from tests.practice_index_fakes import _learning_object
from tests.reading_path_fixtures import call, context
from tests.section_coverage_fixtures import (
    BOOK_EIGEN,
    BOOK_EIGEN_SPAN,
    CoverageJudgeFake,
    build_coverage_vault,
    cite,
    judge_section,
)
from tests.source_service_fakes import set_config

FIND = {"extraction_id": "ext_book", "section_id": BOOK_EIGEN}
QUIET = {**FIND, "search_fallback": False}
PRESSED = {**FIND, "search_fallback": True}


def _ctx(paths, **attrs):
    return context(paths.root, coverage_inline=True, **attrs)


def _second_lo(paths) -> None:
    from learnloop.vault.yaml_io import write_yaml

    lo = _learning_object("lo_charpoly", "Eigenvalue polynomial")
    lo["summary"] = "The eigenvalues of A are the roots of det(A - tI), its characteristic polynomial."
    write_yaml(paths.learning_object_path("linear-algebra", "lo_charpoly"), lo)
    cite(paths, "lo_charpoly", "src_book", "ext_book", BOOK_EIGEN_SPAN)


def _judged(tmp_path, *, two: bool = False):
    paths, repository = build_coverage_vault(tmp_path / "vault")
    if two:
        _second_lo(paths)
    judge = CoverageJudgeFake(treatments={"5.1 Eigenvectors and eigenvalues": "introduces",
                                          "5.2 The characteristic equation": "develops"}, notation="uses row vectors")
    ctx = _ctx(paths, coverage_judge_client=judge)
    judge_section(ctx, FIND)
    return paths, repository, ctx, judge


def _lines(view) -> set[tuple[str, str]]:
    return {(group["learningObjectId"], section["sectionId"])
            for group in view["learningObjects"] for source in group["sources"] for section in source["sections"]}


def _hits(view) -> set[str]:
    search = view.get("search") or {}
    return {section["sectionId"] for source in search.get("sources", []) for section in source["sections"]}


def _dismiss(ctx, target: str, operation_id: str, *, los=None, undo_of=None) -> dict[str, Any]:
    params = {**FIND, "target_extraction_id": "ext_lay", "target_section_id": target, "operation_id": operation_id}
    if los is not None:
        params["learning_object_ids"] = los
    if undo_of is not None:
        params["undo_of"] = undo_of
    return call(ctx, "reader.correspondent_dismiss", params)["operation"]


def _shows(view) -> tuple[bool, bool]:
    """(CA5's line, CA5a's footer action) as the Reader decides them from one quiet read."""

    line = view["status"] == "judged" and bool(_lines(view))
    action = view["status"] not in ("judged", "withheld")
    return line, action


# -- (i) one line or one action; the two dismissals agree through undo ------------------------------


def test_i_a_section_shows_the_line_or_the_action_never_both_and_correcting_every_line_away_swaps_them(tmp_path):
    _paths, _repository, ctx, judge = _judged(tmp_path)
    calls = judge.calls
    view = call(ctx, "reader.correspondents", QUIET)
    assert _shows(view) == (True, False)
    lines = sorted(_lines(view))
    operations = {}
    for index, (lo, target) in enumerate(lines):
        operations[target] = _dismiss(ctx, target, f"op_line_{index:04d}", los=[lo])["operationId"]
    view = call(ctx, "reader.correspondents", QUIET)
    # Every judged line corrected away: no line, CA5a's action is due.
    assert not _lines(view) and _shows(view) == (False, True), view["status"]
    # CA5a's pressed search never offers a hit the learner already said is not about this.
    pressed = call(ctx, "reader.correspondents", PRESSED)
    assert not (_hits(pressed) & set(operations)), _hits(pressed)
    # Undo one: the line is back and the action hides again.
    target = lines[0][1]
    _dismiss(ctx, target, "op_line_undo_0", undo_of=operations[target])
    view = call(ctx, "reader.correspondents", QUIET)
    assert (lines[0][0], target) in _lines(view) and _shows(view) == (True, False)
    assert judge.calls == calls, "no model call"


def test_i_ca5_named_los_then_ca5a_dismiss_of_the_same_hit_agree_through_either_undo(tmp_path):
    _paths, _repository, ctx, _judge = _judged(tmp_path, two=True)
    target = "lay_char"
    assert {("lo_eigen", target), ("lo_charpoly", target)} <= _lines(call(ctx, "reader.correspondents", QUIET))
    # CA5: not about this, under lo_eigen only.
    ca5 = _dismiss(ctx, target, "op_ca5_line_01", los=["lo_eigen"])
    assert ca5["learningObjectIds"] == ["lo_eigen"]
    lines = _lines(call(ctx, "reader.correspondents", QUIET))
    assert ("lo_eigen", target) not in lines and ("lo_charpoly", target) in lines
    # CA5a's dismiss of the same hit names no LOs: every LO of the open section.
    ca5a = _dismiss(ctx, target, "op_ca5a_hit_01")
    assert sorted(ca5a["learningObjectIds"]) == ["lo_charpoly", "lo_eigen"]
    view = call(ctx, "reader.correspondents", QUIET)
    assert not {line for line in _lines(view) if line[1] == target}
    assert target not in _hits(call(ctx, "reader.correspondents", PRESSED))
    # Undoing CA5a's operation restores every LO it wrote, the earlier CA5 one
    # included (the newest correction per LO decides): the hit is back for both.
    _dismiss(ctx, target, "op_ca5a_undo_1", undo_of=ca5a["operationId"])
    lines = _lines(call(ctx, "reader.correspondents", QUIET))
    assert {("lo_eigen", target), ("lo_charpoly", target)} <= lines
    # The earlier CA5 operation's undo is then a no-op on the rows (already
    # restored) and leaves the same state; it is still accepted (the Reader
    # keeps its undo), and a replay returns the same record.
    first = _dismiss(ctx, target, "op_ca5_undo_01", undo_of=ca5["operationId"])
    again = _dismiss(ctx, target, "op_ca5_undo_01", undo_of=ca5["operationId"])
    assert first["operationId"] == again["operationId"] and again["choice"] == "none"
    assert _lines(call(ctx, "reader.correspondents", QUIET)) == lines


def test_i_undoing_the_earlier_ca5_correction_after_ca5a_follows_the_newest_verdict(tmp_path):
    _paths, _repository, ctx, _judge = _judged(tmp_path, two=True)
    target = "lay_char"
    ca5 = _dismiss(ctx, target, "op_ca5_line_02", los=["lo_eigen"])
    ca5a = _dismiss(ctx, target, "op_ca5a_hit_02")
    # Undo the earlier CA5 operation: lo_eigen's newest correction becomes none
    # (the learner's latest word on it), lo_charpoly keeps CA5a's not_about.
    _dismiss(ctx, target, "op_ca5_undo_02", undo_of=ca5["operationId"])
    lines = {line for line in _lines(call(ctx, "reader.correspondents", QUIET)) if line[1] == target}
    assert lines == {("lo_eigen", target)}
    # CA5a's undo restores what it still holds (lo_charpoly) and leaves lo_eigen as it is.
    _dismiss(ctx, target, "op_ca5a_undo_2", undo_of=ca5a["operationId"])
    lines = {line for line in _lines(call(ctx, "reader.correspondents", QUIET)) if line[1] == target}
    assert lines == {("lo_eigen", target), ("lo_charpoly", target)}


def test_i_a_ca5a_dismissal_before_the_judge_ran_keeps_the_hit_off_the_judged_line_until_undone(tmp_path):
    paths, _repository = build_coverage_vault(tmp_path / "vault")
    judge = CoverageJudgeFake(treatments={"5.1 Eigenvectors and eigenvalues": "introduces",
                                          "5.2 The characteristic equation": "develops"}, notation=None)
    ctx = _ctx(paths, coverage_judge_client=judge)
    pressed = call(ctx, "reader.correspondents", PRESSED)
    assert pressed["status"] == "unchecked" and _hits(pressed), pressed["status"]
    target = sorted(_hits(pressed))[0]
    operation = _dismiss(ctx, target, "op_ca5a_first_1")
    assert target not in _hits(call(ctx, "reader.correspondents", PRESSED))
    # The judge runs afterwards: the learner's not_about outranks it, so CA5's line never lists the hit.
    judge_section(ctx, FIND)
    view = call(ctx, "reader.correspondents", QUIET)
    assert view["status"] in ("judged", "none")
    assert target not in {line[1] for line in _lines(view)}
    # Undo (CA5a's operation, from either list): the judge's verdict shows again.
    _dismiss(ctx, target, "op_ca5a_first_u", undo_of=operation["operationId"])
    view = call(ctx, "reader.correspondents", QUIET)
    assert target in {line[1] for line in _lines(view)} and _shows(view) == (True, False)


# -- (ii) either switch off restores today's Reader --------------------------------------------------


def _palette_ids(contract) -> list[str]:
    return [action["id"] for group in contract["intent"]["palette"] for action in group["actions"]]


def _contract(tmp_path, name: str, **switches: bool) -> tuple[dict[str, Any], Any]:
    paths, _repository = build_coverage_vault(tmp_path / name)
    if not switches.get("curriculum", True):
        set_config(paths, "curriculum", enabled=False)
    if not switches.get("correspondence", True):
        set_config(paths, "reader.correspondence", enabled=False)
    ctx = _ctx(paths)
    return call(ctx, "reader.prompt_contract", {}), ctx


def test_ii_curriculum_off_and_correspondence_off_each_restore_todays_reader(tmp_path):
    on, _ctx_on = _contract(tmp_path, "on")
    assert on["correspondence"] == {"enabled": True, "findSection": True, "alsoInBooks": True,
                                    "hiddenEverywhere": False, "hiddenSources": []}
    today = copy.deepcopy(on)
    today.pop("correspondence")
    for name, switches in {"curriculum_off": {"curriculum": False},
                           "correspondence_off": {"correspondence": False}}.items():
        contract, ctx = _contract(tmp_path, name, **switches)
        assert "correspondence" not in contract, name
        assert _palette_ids(contract) == _palette_ids(on), name
        if name == "correspondence_off":
            # Nothing but the key moves.
            assert contract == today, name
        else:
            assert contract["intent"]["palette"] == on["intent"]["palette"], name
        # The preferences say off and refuse a change; nothing is read.
        shown = dict(call(ctx, "reader.correspondence_preferences", {}))
        shown.pop("version", None)
        assert shown == {"enabled": False, "hideEverywhere": False, "hiddenSources": []}, name
        with pytest.raises(SidecarError):
            call(ctx, "reader.set_correspondence_preferences", {"hide_everywhere": True})
        with pytest.raises(SidecarError):
            call(ctx, "reader.correspondent_peek", {"extraction_id": "ext_lay", "section_id": "lay_eigen"})


# -- (iii) hide preferences survive a reload and a second sidecar's write ---------------------------


def _prefs(ctx, **params) -> dict[str, Any]:
    out = dict(call(ctx, "reader.set_correspondence_preferences", params))
    out.pop("version", None)
    return out


def _hidden(ctx) -> tuple[bool, list[str]]:
    contract = call(ctx, "reader.prompt_contract", {})["correspondence"]
    return contract["hiddenEverywhere"], sorted(contract["hiddenSources"])


def test_iii_hide_preferences_survive_a_vault_reload_and_a_second_sidecars_write(tmp_path):
    paths, _repository = build_coverage_vault(tmp_path / "vault")
    first, second = _ctx(paths), _ctx(paths)
    _prefs(first, source_id="src_book", hide_source=True)
    # A reload of the same sidecar, and a new one on the vault, read it.
    first.reload(maintenance=False)
    assert _hidden(first) == (False, ["src_book"])
    assert _hidden(_ctx(paths)) == (False, ["src_book"])
    # The second sidecar (loaded before that write) writes its own change: both survive.
    _prefs(second, source_id="src_lay", hide_source=True)
    _prefs(second, hide_everywhere=True)
    assert _hidden(second) == (True, ["src_book", "src_lay"])
    first.reload(maintenance=False)
    assert _hidden(first) == (True, ["src_book", "src_lay"])
    # Settings in the first brings one back; a fresh sidecar sees exactly that.
    _prefs(first, hide_everywhere=False)
    out = _prefs(first, source_id="src_book", hide_source=False)
    assert [entry["sourceId"] for entry in out["hiddenSources"]] == ["src_lay"]
    third = _ctx(paths)
    assert _hidden(third) == (False, ["src_lay"])
    shown = dict(call(third, "reader.correspondence_preferences", {}))
    assert [entry["sourceId"] for entry in shown["hiddenSources"]] == ["src_lay"]
    # The keys stay in the vault's config across the reloads.
    import tomllib

    section = tomllib.loads((paths.root / "learnloop.toml").read_text(encoding="utf-8"))["reader"]["correspondence"]
    assert section["hidden_sources"] == ["src_lay"] and section["hide_everywhere"] is False
