"""Curriculum C1: the plan follows the deliverable (spec_deliverable_curriculum_v1 §7.6, §8.1; G-C4).

* **What changes.** At C1's tag, with ``curriculum.plan_uses_path`` and
  ``curriculum.enabled`` on (and RW7b's gate), the plan's reading block opens
  the next unfinished **core** or **prerequisite** section in the nearest
  active deliverable's path order, **in whichever book it is**. The
  predecessor's front-matter rule, the exam filter and DL2's
  ``reading_allowed`` still run first on each candidate.
* **Which deliverable.** The nearest active goal (the existing nearest-goal
  rule) among goals with a fresh deliverable path.
* **Receipts.** ``reading_path_plan_v2``: v1's keys, ``predecessor`` is RW7b's
  choice, ``chosen_by = "deliverable"``, ``deliverable`` (goal id, path state
  key, the rows read) and ``rw7b`` (what RW7b alone stored).
* **Stale path.** Not followed (no model call from the plan): RW7b's choice
  stands and the receipt says ``stale``. Once a day, before the plan is built,
  the sidecar re-judges it quietly (plan only); a plan built meanwhile takes
  the refreshed step while its reading has no reading history (C1's invariant,
  fix round 2: the plan's reading is what a fresh build would choose now).
* **G-C4.** Off (either switch) every plan build is RW7b's byte for byte;
  turning it off after the build puts RW7b's reading back while it has no
  reading history (the fresh choice), recorded in the receipt's ``moves``.
* **Persisted meaning.** A successor (mvp-0.40 after mvp-0.39, ONE constant; built as mvp-0.39):
  no migration, a journalled activation, a shadow rebuild with zero deltas.

Every model is a fake (``DeliverableFake``, ``PathJudgeFake``, C0a's coverage
fake); nothing leaves the machine.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

import pytest
from typer.testing import CliRunner

from learnloop.algorithm_versions import (
    DELIVERABLE_PLAN_VERSIONS,
    READER_FOLLOWUPS_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.daily_plan import engine as E
from learnloop.db.repositories import Repository
from learnloop.ops.vault_upgrade import rewrite_algorithm_version
from learnloop.source_retrieval import deliverable_path as DP
from learnloop.source_retrieval import deliverables as DL
from learnloop.vault.loader import load_vault
from tests.deliverable_fixtures import DeliverableFake, PlanDeliverableFake
from tests.helpers import append_config_toml, create_placement_vault, set_algorithm_version
from tests.reading_path_fixtures import call, context
from tests.plan_follows_path_helpers import HEAD, _fixture_copy, _plan_state
from tests.curriculum_c1_plan_follows_path_helpers import (
    C1_OFF,
    CURRICULUM_OFF,
    GUIDE_OFF,
    PRIMARIES,
    RW7B_OFF,
    TAG,
    _activated,
    _at,
    _c1,
    _complete,
    _deliverable,
    _journal,
    _judge,
    _split,
    _step,
    _version,
)
from tests.curriculum_c1_plan_follows_path_helpers import (  # noqa: F401 - fixtures, used by parameter name
    _cli_process,
)

PREDECESSOR = READER_FOLLOWUPS_ALGORITHM_VERSION


@dataclass
class _Exam:
    extractions: frozenset = frozenset()
    spans: frozenset = frozenset()


def _spans(repository, extraction_id, section_id) -> list[str]:
    from learnloop.reader.reader_guidance import extraction_sections

    sections, _blocks, _map = extraction_sections(repository.load_document_ir(extraction_id))
    return [str(span) for span in next(s for s in sections if str(s["id"]) == section_id)["span_ids"]]


# -- the successor's vocabulary and switch ------------------------------------------------------------


def test_the_successor_is_one_constant_after_rw6bs_followups():
    from learnloop.deliverable_plan_upgrade import PREDECESSOR as UPGRADE_PREDECESSOR

    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1:SUCCESSOR_CHAIN.index(TAG) + 1] == (PREDECESSOR, TAG) == ("mvp-0.39", "mvp-0.40")
    # Teacher TE1's mvp-0.41, follow-ups Nov 2's mvp-0.42 and teacher TE1b's mvp-0.43 follow it (and keep it).
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) + 1:] == ("mvp-0.41", "mvp-0.42", "mvp-0.43", "mvp-0.44", "mvp-0.45", "mvp-0.46", "mvp-0.47", "mvp-0.48", "mvp-0.49", "mvp-0.50", "mvp-0.51", "mvp-0.52", "mvp-0.53", "mvp-0.54", "mvp-0.55", "mvp-0.56", "mvp-0.57", "mvp-0.58")
    assert UPGRADE_PREDECESSOR == PREDECESSOR
    assert DELIVERABLE_PLAN_VERSIONS == frozenset({TAG, "mvp-0.41", "mvp-0.42", "mvp-0.43", "mvp-0.44", "mvp-0.45", "mvp-0.46", "mvp-0.47", "mvp-0.48", "mvp-0.49", "mvp-0.50", "mvp-0.51", "mvp-0.52", "mvp-0.53", "mvp-0.54", "mvp-0.55", "mvp-0.56", "mvp-0.57", "mvp-0.58"})


def test_the_switch_is_on_by_default_classified_and_needs_the_curriculum_and_rw7b(tmp_path):
    from learnloop.config.schema import CurriculumConfig
    from learnloop.params.parameter_registry import classify_config_path

    assert CurriculumConfig().plan_uses_path is True
    rule = classify_config_path("curriculum.plan_uses_path")
    assert rule is not None and rule.kind == "structural" and "kill switch" in rule.rationale
    paths = create_placement_vault(tmp_path / "v", version=TAG)
    assert E.deliverable_plan_active(load_vault(paths.root))
    set_algorithm_version(paths, PREDECESSOR)
    assert not E.deliverable_plan_active(load_vault(paths.root))
    for index, fragment in enumerate((C1_OFF, CURRICULUM_OFF, RW7B_OFF, GUIDE_OFF, "[plan]\nenabled = false\n")):
        other = create_placement_vault(tmp_path / f"off{index}", version=TAG)
        append_config_toml(other.root, fragment)
        assert not E.deliverable_plan_active(load_vault(other.root)), fragment


# -- what changes (fail-first: RW7b opens the notes' "Chapter 5 Eigenvalues") -------------------------


def test_the_reading_block_opens_the_paths_first_unfinished_section_and_the_receipt_names_rw7bs(
        tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    plan = call(context(c1.paths.root), "get_daily_plan", {})
    split = _split(c1.repository)
    assert _at(split["reading"]) == ("ext_book", "ch_det") and split["reading"]["path_label"] == "prerequisite"
    receipt = split["reading_path"]
    assert receipt["version"] == E.READING_PATH_RECEIPT_VERSION_V2 == "reading_path_plan_v2"
    # v1's keys, with RW7b's choice as the predecessor (RW7b had no path here: the order's).
    assert {"predecessor", "chosen_by", "label", "same_as_predecessor", "paths"} <= set(receipt)
    assert _at(receipt["predecessor"]) == ("ext_book", "ch_eigen") and receipt["rw7b"] is None
    assert (receipt["chosen_by"], receipt["label"], receipt["same_as_predecessor"]) == (
        "deliverable", "prerequisite", False)
    deliverable = receipt["deliverable"]
    assert deliverable["goal_id"] == c1.goal_id and deliverable["status"] == "path" and deliverable["fresh"]
    assert deliverable["judgment"]["state_key"] == deliverable["input_state_key"]
    with c1.repository.connection() as connection:
        judged = {row[0] for row in connection.execute(
            "SELECT id FROM deliverable_path_sections WHERE goal_id = ? AND label != 'alternate'", (c1.goal_id,))}
    assert {row["judgment_row_id"] for row in deliverable["rows"]} == judged
    assert [(row["learning_object_id"], row["label"]) for row in deliverable["rows"]] == [
        ("lo_det", "prerequisite"), ("lo_eigen", "core")]
    assert deliverable["step"]["learning_object_id"] == "lo_det"
    projected = [row for row in plan["plan"]["projected"] if row.get("readingTitle")]
    assert projected and projected[0]["readingTitle"] == "Chapter 3 Determinants"


def test_the_plan_picks_across_books_in_the_paths_order(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    reading, receipt = _step(c1)
    assert _at(reading) == ("ext_book", "ch_det")
    _complete(c1.repository, "ext_book", "ch_det")
    # A book the learner started is learner context (C0b's key): the path is stale until judged again.
    reading, receipt = _step(c1)
    assert receipt["deliverable"]["status"] == "stale" and receipt["chosen_by"] == "order"
    _judge(c1)
    reading, receipt = _step(c1)
    # The next line is in Lay, a book the predecessor's order never reads (not as-you-read).
    assert _at(reading) == ("ext_lay", "lay_char") and reading.path_label == "core"
    assert receipt["chosen_by"] == "deliverable" and _at(receipt["predecessor"]) == ("ext_book", "ch_orth")
    _complete(c1.repository, "ext_lay", "lay_char")
    _judge(c1)
    # Nothing left on the path: RW7b's choice stands (here the order's), and the receipt says so.
    reading, receipt = _step(c1)
    assert _at(reading) == ("ext_book", "ch_orth") and receipt["deliverable"]["status"] == "path"
    assert receipt["chosen_by"] == "order" and receipt["same_as_predecessor"] and receipt["deliverable"]["step"] is None


def test_the_nearest_deliverable_with_a_fresh_path_is_followed(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    # A nearer deliverable with no depth is passed over; one with a fresh path is followed.
    near = _deliverable(c1.paths, c1.repository, "determinants for the quiz", due_at="2026-11-20", depth=None)
    reading, receipt = _step(c1)
    assert receipt["deliverable"]["goal_id"] == c1.goal_id
    assert [(entry["goal_id"], entry["status"]) for entry in receipt["deliverable"]["consulted"]] == [
        (near, "no_depth"), (c1.goal_id, "path")]
    DL.add_input(c1.vault, c1.repository, near, "depth", text="get_the_idea")
    DP.judge(c1.vault, c1.repository, near, client=DeliverableFake(primaries=PRIMARIES))
    reading, receipt = _step(c1)
    assert receipt["deliverable"]["goal_id"] == near and receipt["chosen_by"] == "deliverable"


# -- the predecessor's filters still run first ---------------------------------------------------------


def test_the_exam_filter_runs_first_on_each_candidate(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    _complete(c1.repository, "ext_book", "ch_det")
    _judge(c1)
    held = frozenset(("ext_lay", span) for span in _spans(c1.repository, "ext_lay", "lay_char"))
    reading, receipt = _step(c1, exam=_Exam(spans=held))
    assert _at(reading) == ("ext_book", "ch_orth") and receipt["chosen_by"] == "order"
    assert receipt["deliverable"]["status"] == "path" and receipt["deliverable"]["step"] is None
    reading, _receipt = _step(c1, exam=_Exam(extractions=frozenset({"ext_lay"})))
    assert _at(reading) == ("ext_book", "ch_orth")
    reading, _receipt = _step(c1)
    assert _at(reading) == ("ext_lay", "lay_char")  # without the filter, the path's line


def test_dl2s_reading_allowed_runs_first_on_each_candidate(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    asked: list[str] = []

    def allowed(extraction_id: str) -> bool:
        asked.append(extraction_id)
        return extraction_id != "ext_book"

    reading, receipt = _step(c1, allowed=allowed)
    # The notes are out of reading: the path's next line, in Lay, is the step.
    assert _at(reading) == ("ext_lay", "lay_char") and receipt["chosen_by"] == "deliverable"
    assert asked[:2] == ["ext_book", "ext_lay"]


def test_the_build_applies_dl2s_intent_to_each_book_on_the_path(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    ctx = context(c1.paths.root)
    applied = call(ctx, "set_intent", {"scopeKind": "source", "scopeId": "src_book", "choice": "pause"})
    assert applied["available"], applied
    call(context(c1.paths.root), "get_daily_plan", {})
    split = _split(c1.repository)
    # The notes are paused (no new reading there): the path's next line, in Lay, is the step.
    assert _at(split["reading"]) == ("ext_lay", "lay_char") and split["reading_path"]["chosen_by"] == "deliverable"
    assert split["reading_path"]["predecessor"] is None  # RW7b (the as-you-read notes only) offers none


def test_the_front_matter_rule_runs_first_on_each_candidate(tmp_path, monkeypatch):
    from learnloop.daily_plan import reading as R

    c1 = _c1(tmp_path, monkeypatch)
    monkeypatch.setattr(R, "is_front_matter_label", lambda label: label == "Chapter 3 Determinants")
    reading, _receipt = _step(c1)
    assert _at(reading) == ("ext_lay", "lay_char")
    # DL1's order (U4's rule off) does not apply it.
    reading, _receipt = _step(c1, from_furthest=False)
    assert _at(reading) == ("ext_book", "ch_det")


def test_a_section_withheld_since_the_judgment_is_never_the_step(tmp_path, monkeypatch):
    from tests.section_coverage_fixtures import hold_out

    c1 = _c1(tmp_path, monkeypatch)
    _complete(c1.repository, "ext_book", "ch_det")
    hold_out(c1.repository, "lay_char")
    reading, receipt = _step(c1)
    assert _at(reading) != ("ext_lay", "lay_char")
    assert receipt["deliverable"]["status"] in ("stale", "path")
    if receipt["deliverable"]["status"] == "path":
        assert all(row["section_id"] != "lay_char" for row in receipt["deliverable"]["rows"])


def test_a_withheld_path_plans_nothing(tmp_path, monkeypatch):
    from learnloop.source_retrieval import section_coverage as SC

    c1 = _c1(tmp_path, monkeypatch)

    def withheld(*_args, **_kwargs):
        raise SC.CoverageError("withheld", "protection unreadable")

    monkeypatch.setattr(DP, "path_inputs", withheld)
    reading, receipt = _step(c1)
    assert reading is None and receipt["chosen_by"] is None and receipt["deliverable"]["status"] == "withheld"


def test_a_path_that_cannot_be_read_leaves_rw7bs_choice_and_says_so(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)

    def boom(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(DP, "effective_lines", boom)
    reading, receipt = _step(c1)
    assert _at(reading) == ("ext_book", "ch_eigen") and receipt["chosen_by"] == "order"
    assert receipt["deliverable"]["status"] == "unreadable" and receipt["deliverable"]["error"] == "RuntimeError"


# -- a stale path, and the daily quiet re-judgment ------------------------------------------------------


def test_a_stale_path_is_not_followed_and_the_receipt_says_stale(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    judged_key = DP.deliverable_plan_path(c1.vault, c1.repository, DL.goal_of(c1.vault, c1.goal_id)).state_key
    c1.clock.advance(days=1)  # a day passes: the days left (in the path's key) move
    calls = []
    monkeypatch.setattr(DP, "judge", lambda *a, **k: calls.append(a))
    call(context(c1.paths.root, deliverable_inline=True), "get_daily_plan", {})
    split = _split(c1.repository)
    assert _at(split["reading"]) == ("ext_book", "ch_eigen") and "path_label" not in split["reading"]
    receipt = split["reading_path"]
    assert receipt["chosen_by"] == "order" and receipt["deliverable"]["status"] == "stale"
    assert receipt["deliverable"]["latest_judged_state_key"] == judged_key
    assert receipt["deliverable"]["input_state_key"] != judged_key
    # The plan itself called no model; only the daily refresh asked (and was stubbed here).
    assert len(calls) == 1


def test_the_daily_refresh_rejudges_quietly_before_the_plan_is_built_once_a_day(tmp_path, monkeypatch):
    from learnloop.ai import plan_fallback

    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    c1.clock.advance(days=1)
    quiet: list[bool] = []

    class QuietFake(PlanDeliverableFake):
        def complete(self, request):
            quiet.append(plan_fallback.offers_suppressed())
            return super().complete(request)

    fake = QuietFake(primaries=PRIMARIES)
    ctx = context(c1.paths.root, deliverable_path_client=fake, deliverable_inline=True)
    call(ctx, "get_daily_plan", {})
    assert fake.calls == 1 and quiet == [True]
    split = _split(c1.repository)
    assert _at(split["reading"]) == ("ext_book", "ch_det") and split["reading_path"]["chosen_by"] == "deliverable"
    call(ctx, "get_daily_plan", {})
    call(ctx, "next_plan_item", {})
    assert fake.calls == 1  # once a day
    from learnloop_sidecar.handlers.deliverables import _work

    assert _work(ctx).refresh["status"] == "ready" and _work(ctx).refresh["goal_id"] == c1.goal_id
    c1.clock.advance(days=1)
    call(ctx, "get_daily_plan", {})
    assert fake.calls == 2  # the next day, once more


def test_with_the_plan_down_the_plan_falls_back_to_rw7b_says_stale_and_nothing_asks(tmp_path, monkeypatch):
    from learnloop.ai import plan_fallback
    from learnloop_sidecar.handlers.deliverables import _work

    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    c1.clock.advance(days=1)
    fake = PlanDeliverableFake(primaries=PRIMARIES, fail=RuntimeError("plan down"))
    relayed = []
    monkeypatch.setattr(plan_fallback, "relay_hint", lambda hint: relayed.append(hint))
    ctx = context(c1.paths.root, deliverable_path_client=fake, deliverable_inline=True)
    call(ctx, "get_daily_plan", {})
    split = _split(c1.repository)
    assert _at(split["reading"]) == ("ext_book", "ch_eigen")
    assert split["reading_path"]["deliverable"]["status"] == "stale" and relayed == []
    assert _work(ctx).refresh["status"] in ("unavailable", "failed")


def test_the_refresh_job_is_quiet_and_only_judges_a_stale_path(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    fake = PlanDeliverableFake(primaries=PRIMARIES)
    assert DP.refresh_for_plan(c1.vault, c1.repository, client=fake)["status"] == "fresh" and fake.calls == 0
    c1.clock.advance(days=1)
    assert DP.refresh_for_plan(c1.vault, c1.repository, client=fake)["status"] == "ready" and fake.calls == 1
    append_config_toml(c1.paths.root, C1_OFF)
    c1.clock.advance(days=1)
    assert DP.refresh_for_plan(c1.vault, c1.repository, client=fake)["status"] == "switched_off"
    assert fake.calls == 1


def test_a_plan_built_on_a_stale_path_takes_the_refreshed_step_while_unstarted(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    c1.clock.advance(days=1)
    ctx = context(c1.paths.root)
    call(ctx, "get_daily_plan", {})
    assert _at(_split(c1.repository)["reading"]) == ("ext_book", "ch_eigen")
    c1.clock.advance(minutes=5)
    _judge(c1)  # the daily job (or a Guide open) judged it after the build
    call(ctx, "get_daily_plan", {})
    split = _split(c1.repository)
    assert _at(split["reading"]) == ("ext_book", "ch_det") and split["reading"]["path_label"] == "prerequisite"
    receipt = split["reading_path"]
    assert receipt["chosen_by"] == "deliverable" and receipt["deliverable"]["status"] == "path"
    [move] = receipt["moves"]
    assert move["reason"] == "deliverable_path_moved" and receipt["move_count"] == 1
    assert _at(move["from"]) == ("ext_book", "ch_eigen") and _at(move["to"]) == ("ext_book", "ch_det")
    # Nothing changed since: reading the plan again writes nothing.
    call(ctx, "get_daily_plan", {})
    assert _split(c1.repository) == split
    # The switch still reaches it afterwards: RW7b's reading comes back (no reading history).
    append_config_toml(c1.paths.root, C1_OFF)
    call(context(c1.paths.root), "get_daily_plan", {})
    after = _split(c1.repository)
    assert _at(after["reading"]) == ("ext_book", "ch_eigen")
    assert after["reading_path"]["moves"][-1]["reason"] == "deliverable_path_off"
    assert after["reading_path"]["moves"][0] == move and after["reading_path"]["move_count"] == 2


# -- G-C4: off is RW7b's plans byte for byte -----------------------------------------------------------


_BOOK_PATH = {"ch_eigen": "core", "ch_det": "enrichment", "ch_orth": "core"}


@pytest.mark.parametrize("variant", ["switch_off", "curriculum_off"])
def test_gc4_off_every_plan_build_is_rw7bs(tmp_path, monkeypatch, variant):
    base = _c1(tmp_path, monkeypatch, "base", version=PREDECESSOR, book_path=_BOOK_PATH)
    off = _c1(tmp_path, monkeypatch, "off", version=TAG, book_path=_BOOK_PATH,
              config=C1_OFF if variant == "switch_off" else CURRICULUM_OFF)
    baseline = _plan_state(base.paths)
    stored = json.dumps(baseline["stored"]["daily_plans"])
    assert "reading_path_plan_v1" in stored and "reading_path_plan_v2" not in stored
    assert _plan_state(off.paths) == baseline
    # The same vault with the successor on is not (the test can see the change).
    on = _c1(tmp_path, monkeypatch, "on", version=TAG, book_path=_BOOK_PATH)
    assert _plan_state(on.paths) != baseline


def test_the_receipts_predecessor_is_rw7bs_choice_with_its_own_receipt_kept(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, book_path=_BOOK_PATH)
    call(context(c1.paths.root), "get_daily_plan", {})
    receipt = _split(c1.repository)["reading_path"]
    rw7b = receipt["rw7b"]
    assert rw7b["version"] == E.READING_PATH_RECEIPT_VERSION and rw7b["chosen_by"] == "path"
    # RW7b's choice (its path: Chapter 5 is core) is the predecessor; the order's is RW7b's own.
    assert _at(receipt["predecessor"]) == ("ext_book", "ch_eigen") == _at(rw7b["predecessor"])
    assert receipt["paths"] == rw7b["paths"]
    assert _at(_split(c1.repository)["reading"]) == ("ext_book", "ch_det")


def test_with_no_deliverable_in_play_the_plan_is_rw7bs_byte_for_byte(tmp_path, monkeypatch):
    base = _c1(tmp_path, monkeypatch, "base", version=PREDECESSOR, judge=False, book_path=_BOOK_PATH)
    on = _c1(tmp_path, monkeypatch, "on", version=TAG, judge=False, book_path=_BOOK_PATH)
    assert _plan_state(on.paths) == _plan_state(base.paths)


def test_switching_both_paths_off_after_the_build_puts_the_orders_reading_back(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, book_path={"ch_eigen": "enrichment"})
    call(context(c1.paths.root), "get_daily_plan", {})
    built = _split(c1.repository)
    assert _at(built["reading"]) == ("ext_book", "ch_det") and built["reading"]["path_label"] == "prerequisite"
    # RW7b's own path skips Chapter 5 (enrichment) and opens Determinants too, as core.
    assert _at(built["reading_path"]["predecessor"]) == ("ext_book", "ch_det")
    assert built["reading_path"]["predecessor"]["path_label"] == "core" and built["reading_path"]["same_as_predecessor"]
    append_config_toml(c1.paths.root, C1_OFF + RW7B_OFF.replace("[reading_paths]\n", "\n[reading_paths]\n"))
    call(context(c1.paths.root), "get_daily_plan", {})
    after = _split(c1.repository)
    # Both paths off: the order's choice (what a build now gives), recorded in one move.
    assert _at(after["reading"]) == ("ext_book", "ch_eigen") and "path_label" not in after["reading"]
    [move] = after["reading_path"]["moves"]
    assert move["reason"] == "reading_path_off"
    assert move["switch"] == {"plan_uses_path": False, "enabled": True,
                              "curriculum": {"plan_uses_path": False, "enabled": True}}
    assert after["reading_path"]["deliverable"] is None and after["reading_path"]["rw7b"] is None
    call(context(c1.paths.root), "get_daily_plan", {})
    assert _split(c1.repository) == after


def test_switching_c1_off_on_the_same_section_restores_rw7bs_label(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, book_path={"ch_eigen": "enrichment"})
    call(context(c1.paths.root), "get_daily_plan", {})
    append_config_toml(c1.paths.root, C1_OFF)
    call(context(c1.paths.root), "get_daily_plan", {})
    after = _split(c1.repository)
    # RW7b's plan exactly: the same section, under RW7b's own label.
    assert after["reading"] == after["reading_path"]["predecessor"] and after["reading"]["path_label"] == "core"
    assert after["reading_path"]["moves"][-1]["reason"] == "deliverable_path_off"


def test_switching_c1_off_with_rw7b_on_puts_rw7bs_choice_back(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    call(context(c1.paths.root), "get_daily_plan", {})
    assert _at(_split(c1.repository)["reading"]) == ("ext_book", "ch_det")
    append_config_toml(c1.paths.root, C1_OFF)
    call(context(c1.paths.root), "get_daily_plan", {})
    after = _split(c1.repository)
    assert _at(after["reading"]) == ("ext_book", "ch_eigen") and "path_label" not in after["reading"]
    move = after["reading_path"]["moves"][-1]
    assert move["reason"] == "deliverable_path_off"
    assert move["switch"]["curriculum"] == {"plan_uses_path": False, "enabled": True}


def test_gc4_on_the_head_fixture_copy_on_and_off_are_rw7bs(tmp_path, monkeypatch):
    from datetime import UTC, datetime

    import learnloop.clock as clock_module

    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: datetime(2026, 10, 31, 9, 30, tzinfo=UTC))
    baseline = _plan_state(_fixture_copy(tmp_path, HEAD, "base", version=PREDECESSOR))
    for name, toml in (("off", C1_OFF), ("curriculum_off", CURRICULUM_OFF), ("on", None)):
        assert _plan_state(_fixture_copy(tmp_path, HEAD, name, version=TAG, toml=toml)) == baseline, name


# -- persisted meaning: a serving change, no projection deltas ------------------------------------------


def test_a_shadow_rebuild_is_zero_and_never_reads_a_deliverable_path(tmp_path, monkeypatch):
    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    c1 = _c1(tmp_path, monkeypatch)
    call(context(c1.paths.root), "get_daily_plan", {})
    reads = []
    real = DP.deliverable_plan_path
    monkeypatch.setattr(DP, "deliverable_plan_path", lambda *a, **k: reads.append(a) or real(*a, **k))
    result = shadow_rebuild(c1.vault)
    assert result.live_database_unchanged
    assert result.learner_state_diff["summary"] == {"mastery": 0, "facet": 0, "schedule": 0}
    assert reads == []


# -- the upgrade -----------------------------------------------------------------------------------------


@pytest.mark.parametrize("start", ["mvp-0.9", "mvp-0.32", "mvp-0.37", "mvp-0.38", "mvp-0.39"])
def test_upgrade_to_mvp040_works_from_supported_versions(tmp_path, _cli_process, start):
    from learnloop.cli import app

    paths = create_placement_vault(tmp_path / "v", version=start)
    result = CliRunner().invoke(app, ["upgrade", "--to", TAG, "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"{start} -> {TAG}" in result.output
    assert _version(paths) == TAG and _activated(paths) and not _journal(paths).exists()
    if start != PREDECESSOR:
        assert _activated(paths, PREDECESSOR)


def test_a_bare_upgrade_targets_mvp040_and_refuses_twice(tmp_path, _cli_process):
    from learnloop.cli import app
    from learnloop.deliverable_plan_upgrade import upgrade_to_deliverable_plan

    paths = create_placement_vault(tmp_path / "v", version=PREDECESSOR)
    # Follow-ups Nov 2 (mvp-0.42, after TE1's mvp-0.41) is the bare upgrade's target now; C1's own link is --to mvp-0.40.
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root), "--to", TAG])
    assert result.exit_code == 0, result.output
    assert f"{PREDECESSOR} -> {TAG}" in result.output and _version(paths) == TAG
    again = upgrade_to_deliverable_plan(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_the_upgrade_refuses_a_version_before_the_chain(tmp_path):
    from learnloop.deliverable_plan_upgrade import upgrade_to_deliverable_plan

    paths = create_placement_vault(tmp_path / "old", version="mvp-0.9")
    rewrite_algorithm_version(paths.root / "learnloop.toml", "mvp-0.9", "mvp-0.8", durable=True)
    result = upgrade_to_deliverable_plan(paths.root)
    assert not result.upgraded and _version(paths) == "mvp-0.8"
    assert "cannot upgrade from 'mvp-0.8'" in result.problems[0]


def _interrupted(tmp_path, name, predecessor=PREDECESSOR, target=TAG):
    paths = create_placement_vault(tmp_path / name, version=predecessor)
    _journal(paths).write_text(json.dumps({"predecessor": predecessor, "target": target}), encoding="utf-8")
    rewrite_algorithm_version(paths.root / "learnloop.toml", predecessor, target, durable=True)
    assert not _activated(paths, target)
    return paths


def test_the_next_cli_command_completes_an_interrupted_mvp040_activation(tmp_path, _cli_process):
    from learnloop.cli import app
    from learnloop.deliverable_plan_upgrade import upgrade_to_deliverable_plan

    paths = _interrupted(tmp_path, "interrupted")
    result = CliRunner().invoke(app, ["backfill-originals", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert not _journal(paths).exists() and _activated(paths) and _version(paths) == TAG
    again = upgrade_to_deliverable_plan(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_the_upgrade_completes_its_own_journal(tmp_path):
    from learnloop.deliverable_plan_upgrade import upgrade_to_deliverable_plan

    paths = _interrupted(tmp_path, "interrupted")
    result = upgrade_to_deliverable_plan(paths.root)
    assert result.upgraded and result.notes == [f"completed the interrupted activation of {TAG}"]
    assert not _journal(paths).exists() and _activated(paths)


def test_a_failure_after_the_rename_leaves_the_predecessor_and_no_journal(tmp_path, monkeypatch):
    import learnloop.deliverable_plan_upgrade as upgrade

    paths = create_placement_vault(tmp_path / "failing", version=PREDECESSOR)
    real = upgrade._publish_algorithm_version

    def publish_then_fail(config_path, from_version, to_version, *, renamed=None):
        real(config_path, from_version, to_version, renamed=renamed)
        if to_version == TAG:
            raise OSError("the directory fsync failed")

    monkeypatch.setattr(upgrade, "_publish_algorithm_version", publish_then_fail)
    with pytest.raises(OSError):
        upgrade.upgrade_to_deliverable_plan(paths.root)
    assert _version(paths) == PREDECESSOR and not _journal(paths).exists() and not _activated(paths)


def test_an_interrupted_mvp039_activation_then_upgrade_to_mvp040_completes_it(tmp_path, _cli_process):
    from learnloop.cli import app

    paths = _interrupted(tmp_path, "interrupted039", "mvp-0.38", PREDECESSOR)
    result = CliRunner().invoke(app, ["upgrade", "--to", TAG, "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"{PREDECESSOR} -> {TAG}" in result.output
    assert _version(paths) == TAG and not _journal(paths).exists()
    assert _activated(paths, PREDECESSOR) and _activated(paths)


def test_without_a_completion_an_attach_refuses_and_the_upgrade_still_completes_the_mvp039_journal(
        tmp_path, monkeypatch):
    from learnloop import activation_journal
    from learnloop.deliverable_plan_upgrade import complete_interrupted_activation, upgrade_to_deliverable_plan

    paths = _interrupted(tmp_path, "refused039", "mvp-0.38", PREDECESSOR)
    monkeypatch.setattr(activation_journal, "_COMPLETER", None)
    with pytest.raises(activation_journal.InterruptedActivation, match=f"learnloop upgrade --to {PREDECESSOR}"):
        Repository(paths.sqlite_path)
    assert complete_interrupted_activation(paths.root) == PREDECESSOR
    assert not _journal(paths).exists() and complete_interrupted_activation(paths.root) is None
    result = upgrade_to_deliverable_plan(paths.root)
    assert result.upgraded and result.from_version == PREDECESSOR and _version(paths) == TAG
    assert not _journal(paths).exists() and _activated(paths, PREDECESSOR) and _activated(paths)
