"""Data capture on the phone's real offer path (mobile M2a: a queue with no plan, ``phone_queue``, its head served).

A phone build must never carry a measurement check it can't show, and a measurement's check it holds back stays due for
the desktop rather than lost. The offer's prefilter receipt says what the phone was offered and why the rest wasn't. Fakes
only; no network.
"""

from __future__ import annotations


import pytest

from learnloop.curriculum import commitments as C
from learnloop.daily_plan import measurement as M
from learnloop.data_capture import prefilter
from learnloop.db.connection import connect
from learnloop.db.stores import data_capture as store

from tests.test_device_eligibility import IMAGE, ORIGIN, PLAIN, _call, _ids, _world

pytestmark = pytest.mark.durability
TAG = "mvp-0.44"


def _at_tag(ctx):
    vault, _repository = ctx.require_vault()
    vault.config.algorithms.algorithm_version = TAG
    vault.config.data_capture.serving = True
    return vault


def _measurement_on(ctx, repository, item_id, *, decision_id="d_measure"):
    """A due check once a decision arranged, on ``item_id``: as ``measurement._new_check`` writes it."""

    vault = _at_tag(ctx)
    item = vault.practice_items[item_id]
    commitment = C.create_commitment(
        repository, action="test_me_later", intent_text="one question on your own, later, to see what stuck",
        targets=[{"target_kind": "legacy_practice_item", "target_ref": item_id, "role": "required"}],
        depth_preset=M.CHECK_DEPTH_PRESET, client_idempotency_key=f"measurement:{decision_id}", due_hint="2026-05-01",
        reason="decision_measurement",
        provenance={"via": M.VIA, "decision_id": decision_id, "learning_object_id": item.learning_object_id, "pick": {}},
    )
    connection = connect(repository.sqlite_path)
    try:
        connection.execute("PRAGMA foreign_keys = OFF")  # the decision's own row is not what these read
        store.insert_objective(connection, {
            "decision_id": decision_id, "decision_kind": "plan_block", "objective_version": M.OBJECTIVE_VERSION,
            "learning_object_id": item.learning_object_id, "source": M.SOURCE_STAGED, "scope_json": "[]", "arm": M.ARM_READING,
            "support_json": "[]", "measurement": M.ARRANGED, "commitment_id": commitment.id, "practice_item_id": item_id,
            "pick_json": "{}", "experiment_id": None, "created_at": "2026-04-01T00:00:00Z",
        })
        connection.commit()
    finally:
        connection.close()
    return commitment.id


def _states(repository, decision_id="d_measure"):
    with repository.connection() as connection:
        return [(row["state"], row["reason"]) for row in store.measurement_events(connection).get(decision_id, ())]


def _offer_receipts(repository):
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT d.id, d.surface, r.surface AS receipt_surface FROM router_decisions d "
            "LEFT JOIN prefilter_receipts r ON r.decision_id = d.id WHERE d.decision_kind = 'today_offer' ORDER BY d.rowid"
        ).fetchall()
        return [dict(row) for row in rows]


def test_a_phone_build_never_carries_a_measurement_check_it_cannot_show(tmp_path):
    _paths, repository, ctx = _world(tmp_path)
    _measurement_on(ctx, repository, IMAGE)
    with ctx.acting_as(ORIGIN):
        session = _call(ctx, "start_session", {"availableMinutes": 60})
        queue = _call(ctx, "get_today_queue", {"sessionId": session["sessionId"]})
    assert IMAGE not in _ids(queue)
    assert queue["deviceDeferredCount"] >= 1, "the phone says it waits"
    # The check stands: due for the desktop, not answered and not lost.
    states = _states(repository)
    assert states and all(state == "due" for state, _reason in states)


def test_the_check_the_phone_held_back_is_still_the_desktops(tmp_path):
    _paths, repository, ctx = _world(tmp_path)
    _measurement_on(ctx, repository, IMAGE)
    with ctx.acting_as(ORIGIN):
        phone = _call(ctx, "start_session", {"availableMinutes": 60})
        _call(ctx, "get_today_queue", {"sessionId": phone["sessionId"]})
        _call(ctx, "end_session", {"sessionId": phone["sessionId"]})
    desktop = _call(ctx, "start_session", {"availableMinutes": 60})
    assert IMAGE in _ids(_call(ctx, "get_today_queue", {"sessionId": desktop["sessionId"]}))


def test_the_phone_offers_a_check_it_can_show(tmp_path):
    _paths, repository, ctx = _world(tmp_path)
    _measurement_on(ctx, repository, PLAIN)
    with ctx.acting_as(ORIGIN):
        session = _call(ctx, "start_session", {"availableMinutes": 60})
        assert PLAIN in _ids(_call(ctx, "get_today_queue", {"sessionId": session["sessionId"]}))


def test_a_phone_offers_receipt_is_linked_and_names_what_it_held_back(tmp_path):
    _paths, repository, ctx = _world(tmp_path)
    _measurement_on(ctx, repository, IMAGE)
    with ctx.acting_as(ORIGIN):
        session = _call(ctx, "start_session", {"availableMinutes": 60})
        _call(ctx, "get_today_queue", {"sessionId": session["sessionId"]})
    (row,) = _offer_receipts(repository)[-1:]
    assert row["receipt_surface"] == prefilter.SURFACE_TODAY_OFFER, "a phone offer has its receipt, linked"
    assert row["surface"] != "full_list", "a phone has no plan: its head is served"
    with repository.connection() as connection:
        receipt = prefilter.read(connection, row["id"])
        slate_surface = connection.execute(
            "SELECT entry_surface FROM scheduler_offer_receipts ORDER BY rowid DESC LIMIT 1").fetchone()[0]
    assert slate_surface == "phone_queue"
    # A check's candidates ask the device's gate inside the check's own decision, so this reads the check's reason.
    assert IMAGE in receipt["gates"]["exclusions"]["intent_check_held"]
    assert prefilter.admission_probability(receipt, IMAGE) == 0.0, "held back: it could not have been offered here"
    assert prefilter.admission_probability(receipt, PLAIN) == 1.0


def test_the_phone_arranges_nothing_of_its_own_and_has_no_measurement_slot(tmp_path):
    """A phone has no plan (M2a): no decision of its offers freezes an objective, and no slot comes off a maintain lane."""

    _paths, repository, ctx = _world(tmp_path)
    _at_tag(ctx)
    with ctx.acting_as(ORIGIN):
        session = _call(ctx, "start_session", {"availableMinutes": 60})
        _call(ctx, "get_today_queue", {"sessionId": session["sessionId"]})
    assert _offer_receipts(repository)
    assert not _objectives_on(repository)
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM daily_plans").fetchone()[0] == 0


def test_a_check_the_phone_showed_reads_due_until_it_is_answered(tmp_path):
    """``offered`` is a plan presentation's, and a phone has none: its list is no presentation. Known and reported."""

    _paths, repository, ctx = _world(tmp_path)
    _measurement_on(ctx, repository, PLAIN)
    with ctx.acting_as(ORIGIN):
        session = _call(ctx, "start_session", {"availableMinutes": 60})
        _call(ctx, "get_today_queue", {"sessionId": session["sessionId"]})
        _call(ctx, "get_today_queue", {"sessionId": session["sessionId"]})
    assert {state for state, _reason in _states(repository)} == {"due"}


def test_answered_on_the_phone_a_check_measures_its_objective(tmp_path):
    _paths, repository, ctx = _world(tmp_path)
    vault = _at_tag(ctx)
    _measurement_on(ctx, repository, PLAIN)
    lo = vault.practice_items[PLAIN].learning_object_id
    with ctx.acting_as(ORIGIN):
        session = _call(ctx, "start_session", {"availableMinutes": 60})
        _call(ctx, "get_today_queue", {"sessionId": session["sessionId"]})
    connection = connect(repository.sqlite_path)
    try:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, hints_used,"
            " correctness, manual_review, created_at, session_id, primed, evidence_origin, entry_surface)"
            " VALUES ('att_phone', ?, ?, 'short_answer', 'independent_attempt', 0, 1.0, 0, ?, ?, 0, 'human', 'phone_practice')",
            (PLAIN, lo, "2026-11-03T12:00:00Z", session["sessionId"]))
        connection.commit()
    finally:
        connection.close()
    with ctx.acting_as(ORIGIN):
        _call(ctx, "get_today_queue", {"sessionId": session["sessionId"]})
    assert "answered" in {state for state, _reason in _states(repository)}
    assert _objectives_on(repository)["d_measure"]["commitment_id"]


def _objectives_on(repository):
    with repository.connection() as connection:
        return store.objectives(connection)
