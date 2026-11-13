"""Curriculum C1 landing onto main (docs/reviews/curriculum-c1-plan-follows-path.md, "Landing onto main"):
its interactions with Reader RW6b part 1 (mvp-0.39), the successor C1 is renumbered after.

(i) RW6b's automatic follow-ups sit in DL2's maintain lane next to C1's reading block: a follow-up
    the plan serves is a planned check while the reading block is C1's step; the follow-up never
    changes C1's choice or receipt (nor ``followups.enabled``), and C1's switch never changes the
    checks. A follow-up RW6b's own gate holds (no digest: fail closed) is recorded unplanned, the
    reading unchanged.
(ii) The activation chain mvp-0.38 -> mvp-0.39 -> mvp-0.40: a bare upgrade from mvp-0.38 activates
    both links; an interrupted mvp-0.40 activation (journal mvp-0.39 -> mvp-0.40) is completed by
    the next CLI command and by ``upgrade``, and refused by an opener without the completion; an
    interrupted mvp-0.39 activation is handed down the chain by C1's completion.

Every model is a fake; nothing leaves the machine.
"""
from __future__ import annotations



from learnloop.algorithm_versions import (
    COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION,
    DELIVERABLE_PLAN_ALGORITHM_VERSION,
    READER_FOLLOWUPS_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.curriculum import commitments as C
from learnloop.instructional import reader_followups as RF
from tests.helpers import append_config_toml
from tests.reading_path_fixtures import call, context
from tests.curriculum_c1_plan_follows_path_helpers import C1_OFF, _at, _c1, _split

C1 = DELIVERABLE_PLAN_ALGORITHM_VERSION
RW6B = READER_FOLLOWUPS_ALGORITHM_VERSION
COLD = COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION
ITEM = "pi_eigen_1"


def test_the_chain_is_rw6b_then_c1():
    assert SUCCESSOR_CHAIN[-22:-19] == (COLD, RW6B, C1) == ("mvp-0.38", "mvp-0.39", "mvp-0.40")


# -- (i) RW6b's follow-ups beside C1's reading block ---------------------------------------------------------


def _followup(c1) -> str:
    """A due ``reader_followup`` Check once on an item of the vault (as RW6b schedules it)."""

    return C.create_commitment(
        c1.repository, action="test_me_later", intent_text="check on your own later", depth_preset="keep_in_touch",
        targets=[{"target_kind": "legacy_practice_item", "target_ref": ITEM}], client_idempotency_key="landing:followup",
        author="learnloop", reason=RF.VIA, due_hint=c1.clock.moment.date().isoformat(),
        provenance={"via": RF.VIA, "purpose": "retention"}).id


def _plan(c1) -> dict:
    call(context(c1.paths.root), "get_daily_plan", {})
    return _split(c1.repository)


def _reset(c1) -> None:
    with c1.repository.connection() as connection:
        connection.execute("DELETE FROM attention_block_events")
        connection.execute("DELETE FROM attention_blocks")
        connection.execute("DELETE FROM daily_plans")
        connection.commit()


def test_i_a_served_follow_up_is_a_planned_check_next_to_c1s_reading(tmp_path, monkeypatch):
    import learnloop.scheduling.intent.followup_gate as G

    c1 = _c1(tmp_path, monkeypatch)
    without = _plan(c1)
    _reset(c1)
    followup = _followup(c1)
    # RW6b's serve-time gate passes it (as for a licensed follow-up with no exposure since valuation).
    monkeypatch.setattr(G, "followup_gate", lambda *a, **k: None)
    split = _plan(c1)
    assert any(row["commitment_id"] == followup for row in split["checks"])
    assert _at(split["reading"]) == ("ext_book", "ch_det") and split["reading_path"]["chosen_by"] == "deliverable"
    # The reading and its receipt are the plan's without the follow-up, apart from the build's stamps.
    assert split["reading"] == without["reading"]
    assert {k: v for k, v in split["reading_path"].items()} == without["reading_path"]
    # C1's switch moves the reading, never the checks.
    _reset(c1)
    append_config_toml(c1.paths.root, C1_OFF)
    off = _plan(c1)
    assert off["checks"] == split["checks"] and _at(off["reading"]) == ("ext_book", "ch_eigen")


def test_i_a_follow_up_rw6bs_gate_holds_leaves_c1s_reading_and_followups_off_changes_nothing_of_it(
        tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    followup = _followup(c1)
    split = _plan(c1)
    assert [row["commitment_id"] for row in split["checks_unplanned"]] == [followup]  # held: no digest
    assert _at(split["reading"]) == ("ext_book", "ch_det") and split["reading_path"]["chosen_by"] == "deliverable"
    _reset(c1)
    append_config_toml(c1.paths.root, "[followups]\nenabled = false\n")
    off = _plan(c1)
    assert off["reading"] == split["reading"] and off["reading_path"] == split["reading_path"]


# -- (ii) the activation chain -----------------------------------------------------------------------------
