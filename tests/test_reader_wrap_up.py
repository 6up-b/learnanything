"""Reader workbench RW6a: Wrap up (spec_reader_workbench_v1 §9.1, D16, D34;
UX §4.8, S11; gate G50's second half).

* Wrap up is offered once a session has **activity**: an inquiry, a workbench
  session, a formative answer or a kept comparison. Scrolling, highlights and
  cue taps alone don't count.
* After leaving a source with activity, the offer is a pure read for the
  place the learner lands: the last reader session had activity and no
  ``wrap_up_opened`` followed it.
* Wrap up shows resolved, still open and worth reinforcing; it writes nothing
  of its own, and its actions are the RPCs the same chips call elsewhere.
* ``recap.wrap_up_enabled`` is its kill switch. Fakes only.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from learnloop.reader import recap as RC
from tests.helpers import append_config_toml
from tests.recap_fixtures import (
    EXT, T0, ask, at, call, context, cue_tap, interaction_rows, iso, open_visit, problem, resolve, selection,
    table_counts, visit,
)
from tests.test_reader_dialogue import _setup


def _now(minutes):
    return T0 + timedelta(minutes=minutes)


def test_scrolling_highlights_and_cue_taps_alone_are_not_activity(tmp_path):
    vault, repo = _setup(tmp_path)
    open_visit(repo, "v1", 0)
    selection(repo, 1, "v1")
    cue_tap(repo, 2, visit_id="v1")
    wrap = RC.build_wrap_up(vault, repo, extraction_id=EXT, current_visit_id="v1", now=_now(5))
    assert wrap["available"] is False


@pytest.mark.parametrize("act", ["inquiry", "branch", "workbench"])
def test_an_inquiry_or_a_workbench_session_is_activity(tmp_path, act):
    vault, repo = _setup(tmp_path)
    if act == "branch":
        visit(repo, "v0", -300, -290)
        root = ask(vault, repo, "An older question", -295)
    open_visit(repo, "v1", 0)
    if act == "inquiry":
        ask(vault, repo, "Why weighted by p?", 1)
    elif act == "branch":
        ask(vault, repo, "A follow-up today", 1, parent=root["reader_answer_event_id"])
    else:
        problem(repo, 1, steps=1)
    wrap = RC.build_wrap_up(vault, repo, extraction_id=EXT, current_visit_id="v1", now=_now(5))
    assert wrap["available"] is True


def test_the_footer_offer_follows_the_current_session_only(tmp_path):
    vault, repo = _setup(tmp_path)
    visit(repo, "v1", 0, 10)
    ask(vault, repo, "Yesterday's question", 2)
    # A new session the next day, with nothing done yet: nothing to wrap.
    open_visit(repo, "v2", 1440)
    assert RC.build_wrap_up(vault, repo, extraction_id=EXT, current_visit_id="v2", now=_now(1445))["available"] is False
    # The current visit not yet on the envelope reads the same way.
    assert RC.build_wrap_up(vault, repo, extraction_id=EXT, current_visit_id="v9", now=_now(1445))["available"] is False


def test_the_offer_appears_where_the_learner_lands_until_wrap_up_is_opened(tmp_path):
    vault, repo = _setup(tmp_path)
    visit(repo, "v1", 0, 20)
    ask(vault, repo, "Why weighted by p?", 2)
    offer = RC.wrap_up_offer(vault, repo, now=_now(21))
    assert offer is not None and offer["extraction_id"] == EXT
    assert offer["session"]["ended_at"] == iso(20)

    RC.record_recap_event(repo, extraction_id=EXT, event="wrap_up_opened", visit_id=None, clock=at(22))
    assert RC.wrap_up_offer(vault, repo, now=_now(23)) is None


def test_the_offer_reads_the_most_recent_session_only(tmp_path):
    vault, repo = _setup(tmp_path)
    visit(repo, "v1", 0, 20)
    ask(vault, repo, "A question", 2)
    visit(repo, "v2", 300, 310)  # a later session with no activity
    assert RC.wrap_up_offer(vault, repo, now=_now(311)) is None


def test_wrap_up_lists_resolved_still_open_and_worth_reinforcing(tmp_path):
    vault, repo = _setup(tmp_path)
    open_visit(repo, "v1", 0)
    done = ask(vault, repo, "Why weighted by p?", 1)
    resolve(repo, done["reader_answer_event_id"], 3)
    pending = ask(vault, repo, "Density of a sum?", 4)
    problem(repo, 5, steps=2, book=True)
    wrap = RC.build_wrap_up(vault, repo, extraction_id=EXT, current_visit_id="v1", now=_now(20))
    assert wrap["available"] is True
    assert [line["root_exchange_id"] for line in wrap["resolved"]] == [done["reader_answer_event_id"]]
    assert [line["root_exchange_id"] for line in wrap["still_open"]] == [pending["reader_answer_event_id"]]
    assert wrap["resolved"][0]["question_md"].startswith("Why weighted")
    [worked] = [line for line in wrap["worth_reinforcing"] if line["kind"] == "with_help"]
    assert worked["marker"] == "◌" and worked["help_line"] == "help so far: the book"
    # Headings carry no counts; nothing is overdue.
    assert "overdue" not in json.dumps(wrap).lower()


def test_wrap_up_is_a_pure_read_and_its_actions_are_the_chips_rpcs(tmp_path):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    vault, repo = _setup(tmp_path)
    open_visit(repo, "v1", 0)
    done = ask(vault, repo, "Why weighted by p?", 1)
    resolve(repo, done["reader_answer_event_id"], 3)
    ask(vault, repo, "Density of a sum?", 4)
    ctx = context(vault.root)
    before_counts, before_rows = table_counts(repo), interaction_rows(repo)
    wrap = call(ctx, "reader.wrap_up", {"extractionId": EXT, "visitId": "v1"})
    offer = call(ctx, "reader.wrap_up_offer", {})
    assert wrap["available"] is True and "offer" in offer
    assert table_counts(repo) == before_counts and interaction_rows(repo) == before_rows

    actions = {action["rpc"] for line in wrap["resolved"] + wrap["stillOpen"] for action in line["actions"]}
    import learnloop_sidecar.handlers  # noqa: F401
    assert actions and actions <= set(METHOD_REGISTRY)
    assert actions <= {"reader.set_inquiry_status", "reader.invoke_preset"}
    # "keep open" writes nothing: it carries no RPC at all.
    keep = [a for line in wrap["stillOpen"] for a in line["actions"] if a["action"] == "keep_open"]
    assert keep == [] or all(a.get("rpc") is None for a in keep)


def test_opening_wrap_up_writes_only_the_wrap_up_opened_event(tmp_path):
    vault, repo = _setup(tmp_path)
    visit(repo, "v1", 0, 20)
    ask(vault, repo, "Why weighted by p?", 2)
    ctx = context(vault.root)
    before = interaction_rows(repo)
    call(ctx, "reader.recap_event", {"extractionId": EXT, "event": "wrap_up_opened"})
    new = [row for row in interaction_rows(repo) if row not in before]
    assert len(new) == 1 and json.loads(new[0][4])["event"] == "wrap_up_opened"
    assert call(ctx, "reader.wrap_up_offer", {})["offer"] is None


def test_wrap_up_switched_off_refuses_and_writes_nothing(tmp_path):
    from learnloop_sidecar.errors import SidecarError

    vault, repo = _setup(tmp_path)
    visit(repo, "v1", 0, 20)
    ask(vault, repo, "Why weighted by p?", 2)
    append_config_toml(vault.root, """
    [recap]
    wrap_up_enabled = false
    """)
    ctx = context(vault.root)
    before_counts, before_rows = table_counts(repo), interaction_rows(repo)
    for name, params in (
        ("reader.wrap_up", {"extractionId": EXT}),
        ("reader.wrap_up_offer", {}),
        ("reader.recap_event", {"extractionId": EXT, "event": "wrap_up_opened"}),
    ):
        with pytest.raises(SidecarError) as refused:
            call(ctx, name, params)
        assert refused.value.code == "wrap_up_disabled"
    assert table_counts(repo) == before_counts and interaction_rows(repo) == before_rows
    # The card keeps working on its own switch.
    assert call(ctx, "reader.recap", {"extractionId": EXT})["version"] == 1


def test_the_card_off_leaves_wrap_up_on_its_own_switch(tmp_path):
    from learnloop_sidecar.context import config_dto
    from learnloop.vault.loader import load_vault

    vault, repo = _setup(tmp_path)
    visit(repo, "v1", 0, 20)
    ask(vault, repo, "Why weighted by p?", 2)
    append_config_toml(vault.root, """
    [recap]
    enabled = false
    """)
    ctx = context(vault.root)
    assert call(ctx, "reader.wrap_up_offer", {})["offer"]["extractionId"] == EXT
    assert config_dto(load_vault(vault.root))["recap"] == {"enabled": False, "wrapUpEnabled": True}
