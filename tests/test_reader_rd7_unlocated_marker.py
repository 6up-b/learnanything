"""The unlocated due-check marker (the owner's decision on RD7-56, spec §12.6.1): before "check now" no read the desks
make names or places what a due check is about. ``checks.due_for`` answers one opaque handle per due check and nothing
else; ``check.begin_inline`` resolves the handle (stable across reads, spent by a begin, a guessed or stale one refused
plainly); no passage carries a due check; and the replies mask a check's LO only once it is begun (masking from the due
date would point at it by elimination). The grader is a fake; no model is called."""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.curriculum import commitments as C
from learnloop.db.repositories import Repository
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from tests.approach_map_fakes import ITEM, LO
from tests.hint_fakes import hint_vault
from tests.workbench_help_fakes import call

READING = "ext_host_reading"
HOST_SPAN = "span_host_7"


@pytest.fixture(autouse=True)
def grader(monkeypatch):
    import learnloop_sidecar.handlers.practice as practice
    from tests.split_live_helpers import ReadyRuntime
    from tests.stuck_prompt_helpers import StuckFake

    monkeypatch.setattr(practice, "ready_grading_provider", lambda vault, override=None: ("fake", ReadyRuntime(), StuckFake()))


def _vault(tmp_path):
    """A due check on the CDF item whose LO has a primary passage (its host)."""

    paths = hint_vault(tmp_path)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO entity_source_links (id, entity_type, entity_id, locator, relation, created_at) "
            "VALUES ('esl_host', 'learning_object', ?, ?, 'primary', '2026-05-19T09:00:00Z')",
            (LO, f"span:{READING}/{HOST_SPAN}"))
        connection.commit()
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.post_attempt_worker.autostart = False
    repository = Repository.attach(paths.sqlite_path)
    yesterday = (datetime.now(UTC) - timedelta(days=1)).date().isoformat()
    commitment = C.create_commitment(
        repository, action="test_me_later", intent_text="check the CDF later",
        provenance={"via": "reader", "annotation_id": "ann_secret"},
        targets=[{"target_kind": "legacy_practice_item", "target_ref": ITEM, "role": "required"}],
        depth_preset="keep_in_touch", client_idempotency_key="rd7-unlocated", due_hint=yesterday).id
    return paths, ctx, repository, commitment


def _forbidden(ctx, commitment: str) -> list[str]:
    """Everything that would name or place the check: its commitment, LO (id and title), item, host reading and
    passage, and its provenance."""

    vault = ctx.require_vault()[0]
    return [commitment, LO, str(vault.learning_objects[LO].title), ITEM, READING, HOST_SPAN, "ann_secret", "reader"]


def test_due_for_answers_a_handle_and_nothing_of_the_check(tmp_path):
    from learnloop.intent.inline_checks import due_checks

    paths, ctx, repository, commitment = _vault(tmp_path)
    # The fixture's check has a host the server knows (the reply must not carry it).
    [row] = due_checks(ctx.require_vault()[0], repository)
    assert row["host"]["extraction_id"] == READING and row["host"]["span_id"] == HOST_SPAN
    reply = call(ctx, "checks.due_for", {})
    [check] = reply["checks"]
    assert set(check) == {"handle", "beingAnswered"}
    text = json.dumps(reply)
    assert [word for word in _forbidden(ctx, commitment) if word in text] == []
    # The handle is the same on every read (the desks' marker is stable) until a begin spends it.
    assert call(ctx, "checks.due_for", {})["checks"] == reply["checks"]


def test_due_for_takes_no_filter_that_could_ask_where_the_check_is(tmp_path):
    _paths, ctx, _repository, _commitment = _vault(tmp_path)
    with pytest.raises(Exception):
        call(ctx, "checks.due_for", {"extractionId": READING})


def test_begin_resolves_the_handle_and_a_spent_stale_or_guessed_one_is_refused(tmp_path):
    paths, ctx, repository, commitment = _vault(tmp_path)
    [check] = call(ctx, "checks.due_for", {})["checks"]
    card = call(ctx, "check.begin_inline", {"requestId": "r1", "handle": check["handle"], "visible": {}})
    assert card["commitmentId"] == commitment
    # Once begun the card says where it sits (the host is named only now).
    assert card["host"]["extractionId"] == READING and card["host"]["spanId"] == HOST_SPAN
    # A lost reply's retry, or another click with the handle it spent: the open administration, not a second one.
    again = call(ctx, "check.begin_inline", {"requestId": "r2", "handle": check["handle"], "visible": {}})
    assert (again["administrationToken"], again["replayed"]) == (card["administrationToken"], True)
    call(ctx, "check.abandon_inline", {"administrationToken": card["administrationToken"]})
    # Spent: the check is due again under a new handle, and the old one is refused plainly.
    [fresh] = call(ctx, "checks.due_for", {})["checks"]
    assert fresh["handle"] != check["handle"]
    for stale in (check["handle"], "chk_" + "0" * 32, commitment):
        with pytest.raises(SidecarError) as refused:
            call(ctx, "check.begin_inline", {"requestId": f"r_{stale[-4:]}", "handle": stale, "visible": {}})
        assert refused.value.code == "check_unknown"
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM check_administrations").fetchone() == (1,)
    assert call(ctx, "check.begin_inline", {"requestId": "r3", "handle": fresh["handle"], "visible": {}})["commitmentId"] == commitment


def test_a_handle_dies_with_the_sidecar_and_a_new_read_recovers(tmp_path):
    import learnloop.intent.inline_checks as IC

    _paths, ctx, _repository, commitment = _vault(tmp_path)
    [check] = call(ctx, "checks.due_for", {})["checks"]
    IC.new_handle_key()  # what a sidecar restart does
    with pytest.raises(SidecarError) as dead:
        call(ctx, "check.begin_inline", {"requestId": "r1", "handle": check["handle"], "visible": {}})
    assert dead.value.code == "check_unknown"
    [fresh] = call(ctx, "checks.due_for", {})["checks"]
    assert call(ctx, "check.begin_inline", {"requestId": "r2", "handle": fresh["handle"], "visible": {}})["commitmentId"] == commitment


def test_no_passage_says_a_check_is_due_before_it(tmp_path):
    from learnloop.passage_union.union import union_range

    from tests.desk_helpers import seed_reading

    _paths, ctx, repository, _commitment = _vault(tmp_path)
    seed_reading(repository, source_id="src_host", revision_id="rev_host", extraction_id=READING, spans=["s0", HOST_SPAN])
    reply = union_range(ctx.require_vault()[0], repository, extraction_id=READING, from_span_id="s0",
                        to_span_id=HOST_SPAN)
    assert {entry["span_id"] for entry in reply["spans"]} >= {HOST_SPAN}
    assert "checks_due" not in json.dumps(reply)


def test_the_replies_mask_a_check_only_once_it_is_begun(tmp_path):
    from learnloop_sidecar.handlers.goal_lens import protection_now

    _paths, ctx, repository, commitment = _vault(tmp_path)
    vault = ctx.require_vault()[0]
    # Due, not begun: nothing is masked (a masked dot, section or chapter would point at the LO by elimination).
    protection, _next = protection_now(vault, repository)
    assert not protection.active
    [check] = call(ctx, "checks.due_for", {})["checks"]
    token = call(ctx, "check.begin_inline", {"requestId": "r1", "handle": check["handle"], "visible": {}})["administrationToken"]
    protection, _next = protection_now(vault, repository)
    assert protection.held == frozenset({LO})
    call(ctx, "check.abandon_inline", {"administrationToken": token})
    assert not protection_now(vault, repository)[0].active
