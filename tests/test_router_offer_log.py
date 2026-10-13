"""Router R1: every Today offer is a logged decision (spec_action_router_v1 §9, §11).

Each published offer writes one ``router_decisions`` row in the offer receipt's
transaction: the full candidate set with planner values, the head Today shows
first as the chosen candidate, and its exact propensity (or an explicit
``deterministic``). Continue and stop are candidates; learner picks are rows of
their own with no propensity.
"""

from __future__ import annotations

from datetime import UTC, datetime
import json

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.placement.decisions import record_self_report
from learnloop.router import decisions as router_decisions
from learnloop.router.decisions import (
    CONTINUE_REF,
    STOP_REF,
    OfferHeadMismatch,
    build_today_offer_decision,
)
from learnloop.scheduling import scheduler as scheduler_module
from learnloop.scheduling.scheduler import (
    ExplorationOutcome,
    OfferTrace,
    ScheduledItem,
    SchedulerSession,
    _apply_goal_quota,
    _fill_offer_trace,
    build_due_queue,
)
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import (
    NOW,
    add_followup_item,
    append_config_toml,
    create_basic_vault,
    create_placement_vault,
    seed_due_item,
)

SECOND_ITEM = "pi_svd_define_002"


def _call(ctx, name: str, params: dict):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _context(root):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    context = SidecarContext()
    context.load(root)
    context.grading_provider_override = "manual"
    return context


def _decisions(repository, kind: str | None = None) -> list[dict]:
    with repository.connection() as connection:
        rows = [dict(row) for row in connection.execute("SELECT * FROM router_decisions ORDER BY created_at, id")]
    for row in rows:
        for column in ("candidates_json", "exclusions_json", "detail_json"):
            row[column] = json.loads(row[column])
    return [row for row in rows if kind is None or row["decision_kind"] == kind]


def _served(queue) -> list[str]:
    return [item["practiceItemId"] for section in queue["sections"] for item in section["items"]]


def _two_due_items(tmp_path, *, toml: str | None = None):
    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    add_followup_item(paths.root, SECOND_ITEM)
    repository.upsert_practice_item_state(
        SECOND_ITEM, difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z", active=True,
    )
    if toml:
        append_config_toml(paths.root, toml)
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=20, notes_md_path=None)
    return paths, repository, _context(paths.root), session_id


# ── the offer row ────────────────────────────────────────────────────────────


def test_today_offer_logs_candidates_the_served_head_and_its_exact_propensity(tmp_path):
    paths, repository, ctx, session_id = _two_due_items(tmp_path)

    queue = _call(ctx, "get_today_queue", {"sessionId": session_id})

    [row] = _decisions(repository)
    served = _served(queue)
    assert row["decision_kind"] == "today_offer" and row["mode"] == "legacy_queue"
    assert row["policy"] == "composed_offer_v2" and row["surface"] == "desktop_queue"
    assert row["chosen_ref"] == served[0] == row["chosen_practice_item_id"]
    items = {c["ref"]: c for c in row["candidates_json"] if c["kind"] == "item"}
    assert set(items) == set(served)
    assert [items[ref]["offered_rank"] for ref in served] == [1, 2]
    assert all(c["feasible"] and c["planner"]["selection_reward"] is not None for c in items.values())
    # The two items are near-ties: the exploration's support splits 0.9 / 0.1.
    assert row["propensity"] == pytest.approx(items[served[0]]["propensity"])
    assert row["propensity_kind"] == "exact" and 0 < row["propensity"] < 1
    assert row["design"] == "scheduler_seeded_exploration" and row["seed"]
    stop = next(c for c in row["candidates_json"] if c["ref"] == STOP_REF)
    assert stop["propensity"] == 0.0
    assert sum(c["propensity"] for c in row["candidates_json"]) == pytest.approx(1.0)
    # The decision commits with the published offer and links to its slate.
    slate = repository.latest_scheduler_slate_by_session(session_id)
    assert row["scheduler_slate_id"] == slate["id"] == row["receipt_key"].split(":", 1)[1]
    candidate_ids = {c["id"] for c in repository.scheduler_slate_candidates(slate["id"]) if c["practice_item_id"] == served[0]}
    assert row["chosen_scheduler_candidate_id"] in candidate_ids
    with repository.connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM scheduler_offer_receipts WHERE slate_id=?", (slate["id"],)
        ).fetchone()[0] == 1


def test_each_published_offer_is_its_own_decision_and_rows_are_append_only(tmp_path):
    import sqlite3

    paths, repository, ctx, session_id = _two_due_items(tmp_path)
    _call(ctx, "get_today_queue", {"sessionId": session_id})
    _call(ctx, "get_today_queue", {"sessionId": session_id})
    rows = _decisions(repository)
    assert len(rows) == 2 and len({row["scheduler_slate_id"] for row in rows}) == 2
    with repository.connection() as connection:
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("UPDATE router_decisions SET chosen_ref = 'x'")
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("DELETE FROM router_decisions")


def test_offer_without_a_session_is_not_a_logged_decision(tmp_path):
    paths, repository, ctx, _session_id = _two_due_items(tmp_path)
    _call(ctx, "get_today_queue", {})
    assert _decisions(repository) == []


def test_logging_switch_off_writes_nothing_and_serves_the_same(tmp_path):
    # Two vaults have two session ids, hence two exploration draws: switch the
    # draw off so the served order is comparable.
    greedy = "[scheduler]\nselection_exploration_rate = 0.0\n"
    on_paths, on_repo, on_ctx, on_session = _two_due_items(tmp_path / "on", toml=greedy)
    off_paths, off_repo, off_ctx, off_session = _two_due_items(
        tmp_path / "off", toml=greedy + "[router]\nlog_decisions = false\n"
    )
    on = _call(on_ctx, "get_today_queue", {"sessionId": on_session})
    off = _call(off_ctx, "get_today_queue", {"sessionId": off_session})
    assert _decisions(off_repo) == [] and len(_decisions(on_repo)) == 1
    assert [i["practiceItemId"] for i in on["sections"][0]["items"]] == [
        i["practiceItemId"] for i in off["sections"][0]["items"]
    ]


def test_a_logging_failure_never_fails_the_offer(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import queue as queue_handler

    paths, repository, ctx, session_id = _two_due_items(tmp_path)

    def broken(*_args, **_kwargs):
        raise RuntimeError("logging broke")

    monkeypatch.setattr(queue_handler, "build_today_offer_decision", broken)
    queue = _call(ctx, "get_today_queue", {"sessionId": session_id})
    assert len(_served(queue)) == 2
    assert _decisions(repository) == []
    slate = repository.latest_scheduler_slate_by_session(session_id)
    with repository.connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM scheduler_offer_receipts WHERE slate_id=?", (slate["id"],)
        ).fetchone()[0] == 1


def test_an_empty_offer_logs_a_deterministic_stop(tmp_path):
    # The basic vault's only item is retired, so Today has nothing to offer.
    paths = create_basic_vault(tmp_path / "vault")
    item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    item_path.write_text(item_path.read_text().replace("practice_mode:", "status: retired\npractice_mode:", 1))
    repository = Repository(paths.sqlite_path)
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=20, notes_md_path=None)
    ctx = _context(paths.root)

    queue = _call(ctx, "get_today_queue", {"sessionId": session_id})

    assert _served(queue) == []
    [row] = _decisions(repository)
    assert row["chosen_ref"] == STOP_REF and row["chosen_practice_item_id"] is None
    assert (row["propensity"], row["propensity_kind"], row["design"]) == (1.0, "deterministic", None)
    assert row["exclusions_json"]["counts"] == {"retired": 1}


def test_skip_requeue_is_logged_with_the_skipped_item_removed(tmp_path):
    paths, repository, ctx, session_id = _two_due_items(tmp_path)
    first = _served(_call(ctx, "get_today_queue", {"sessionId": session_id}))

    requeued = _call(ctx, "skip_practice_item", {"sessionId": session_id, "practiceItemId": first[0]})

    row = _decisions(repository)[-1]
    assert row["surface"] == "skip_requeue"
    assert row["exclusions_json"]["named"]["skipped_by_learner"] == [first[0]]
    assert row["chosen_ref"] == _served(requeued)[0] != first[0]
    # The skipped item is still a considered candidate; it just cannot head.
    skipped = next(c for c in row["candidates_json"] if c["ref"] == first[0])
    assert skipped["propensity"] == 0.0 and "offered_rank" not in skipped
    assert row["propensity_kind"] == "deterministic"


# ── learner picks and continue ───────────────────────────────────────────────


def _draft(ctx, session_id, item_id, candidate_id, submission_id="sub-1", answer="half an answer"):
    return _call(
        ctx,
        "save_practice_draft",
        {
            "sessionId": session_id,
            "practiceItemId": item_id,
            "answerMd": answer,
            "hintsUsed": 0,
            "submissionId": submission_id,
            "schedulerCandidateId": candidate_id,
        },
    )


def test_a_learner_pick_of_another_candidate_is_logged_without_propensity(tmp_path):
    paths, repository, ctx, session_id = _two_due_items(tmp_path)
    queue = _call(ctx, "get_today_queue", {"sessionId": session_id})
    items = [item for section in queue["sections"] for item in section["items"]]
    head, other = items[0], items[1]
    [offer] = _decisions(repository)

    _draft(ctx, session_id, other["practiceItemId"], other["schedulerCandidateId"])
    _draft(ctx, session_id, other["practiceItemId"], other["schedulerCandidateId"], answer="more")

    [pick] = _decisions(repository, "learner_pick")
    assert pick["parent_decision_id"] == offer["id"]
    assert (pick["chosen_ref"], pick["chosen_scheduler_candidate_id"]) == (
        other["practiceItemId"], other["schedulerCandidateId"],
    )
    assert (pick["propensity"], pick["propensity_kind"], pick["learner_pick"]) == (None, "none", 1)
    assert pick["policy"] == "learner" and pick["detail_json"]["overrode_ref"] == head["practiceItemId"]
    offered = next(c for c in offer["candidates_json"] if c["ref"] == other["practiceItemId"])
    assert pick["detail_json"]["offer_probability_of_pick"] == pytest.approx(offered["propensity"])


def test_taking_the_offers_head_is_not_a_learner_pick(tmp_path):
    paths, repository, ctx, session_id = _two_due_items(tmp_path)
    queue = _call(ctx, "get_today_queue", {"sessionId": session_id})
    head = queue["sections"][0]["items"][0]
    _draft(ctx, session_id, head["practiceItemId"], head["schedulerCandidateId"])
    assert _decisions(repository, "learner_pick") == []


def test_a_draft_in_progress_is_logged_as_the_continue_candidate(tmp_path):
    paths, repository, ctx, session_id = _two_due_items(tmp_path)
    queue = _call(ctx, "get_today_queue", {"sessionId": session_id})
    other = [item for section in queue["sections"] for item in section["items"]][1]
    _draft(ctx, session_id, other["practiceItemId"], other["schedulerCandidateId"])

    _call(ctx, "get_today_queue", {"sessionId": session_id})

    offer = _decisions(repository, "today_offer")[-1]
    [cont] = [c for c in offer["candidates_json"] if c["ref"] == CONTINUE_REF]
    assert cont["source"] == "draft" and cont["practice_item_id"] == other["practiceItemId"]
    # The legacy queue never resumes a draft itself: the draft's item heads (or
    # not) as an ordinary item, and "continue" is never served (counted once).
    item = next(c for c in offer["candidates_json"] if c["ref"] == other["practiceItemId"])
    assert cont["propensity"] == 0.0 and "served_as" not in item
    assert sum(c["propensity"] for c in offer["candidates_json"]) == pytest.approx(1.0)
    assert offer["chosen_ref"] != CONTINUE_REF
    assert offer["detail_json"]["in_progress"]["source"] == "draft"


# ── placement candidates, components and exclusions ─────────────────────────


def test_placement_components_and_exclusions_are_in_the_candidate_set(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.11")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=FrozenClock(NOW))
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=20, notes_md_path=None)
    ctx = _context(paths.root)

    _call(ctx, "get_today_queue", {"sessionId": session_id})

    [row] = _decisions(repository)
    items = {c["ref"]: c for c in row["candidates_json"] if c["kind"] == "item"}
    # The sidecar serves at the wall clock, months past the assumption's
    # 14-day first review: one check item is admitted, the rest withheld.
    [check] = [ref for ref, c in items.items() if c["planner"]["signals"].get("assumed_check")]
    named = row["exclusions_json"]["named"]
    assert set(named["placement_assumed_withheld"]) | {check} == {"pi_diag_easy", "pi_diag_mid", "pi_diag_hard"}
    new_material = [c for c in items.values() if c["planner"]["signals"].get("new_material")]
    assert {c["learning_object_id"] for c in new_material} == {"lo_eigen_basics", "lo_spectral"}
    # lo_spectral sits one prerequisite layer below lo_eigen_basics.
    assert {c["planner"]["signals"].get("placement_layer") for c in new_material if c["learning_object_id"] == "lo_spectral"} == {1.0}
    assert row["detail_json"]["placement_active"] is True


# ── exactness: the logged propensity is the distribution actually sampled ────


def _wide_window_vault(tmp_path):
    """Goal items beside never-practised new material, with every candidate a
    near-tie, so exploring a non-goal item lets the goal quota pull a goal item
    back to the front."""

    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.11")
    repository = seed_due_item(paths)
    add_followup_item(paths.root, SECOND_ITEM)
    repository.upsert_practice_item_state(
        SECOND_ITEM, difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z", active=True,
    )
    append_config_toml(
        paths.root, "[scheduler]\nselection_exploration_rate = 0.5\nselection_exploration_reward_window = 5.0\n"
    )
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository


def test_every_counterfactual_outcome_reproduces_the_build_that_draw_would_make(tmp_path, monkeypatch):
    vault, repository = _wide_window_vault(tmp_path)
    clock = FrozenClock(NOW)
    session = SchedulerSession(session_id="s-exact")
    trace = OfferTrace()
    live = build_due_queue(vault, repository, clock=clock, session=session, persist_explanations=False, offer_trace=trace)

    assert len(trace.outcomes) > 2
    assert sum(outcome.probability for outcome in trace.outcomes) == pytest.approx(1.0)
    realized = trace.outcomes[trace.realized]
    assert [i.practice_item_id for i in realized.composed] == [i.practice_item_id for i in live]

    alternatives = trace.exploration["alternative_item_ids"]
    for outcome in trace.outcomes:
        if outcome.explored_item_id is None:
            forced = (1.0, 0.0)  # roll >= rate: the greedy order
        else:
            index = alternatives.index(outcome.explored_item_id)
            forced = (0.0, (index + 0.5) / len(alternatives))
        monkeypatch.setattr(scheduler_module, "_exploration_draws", lambda *_a, _f=forced, **_k: _f)
        rebuilt = build_due_queue(vault, repository, clock=clock, session=session, persist_explanations=False)
        assert [i.practice_item_id for i in rebuilt] == [i.practice_item_id for i in outcome.composed]

    # Composition after the draw is inside the propensity: exploring a
    # non-goal item does not put it first, because the goal quota pulls a goal
    # item back to the front.
    goal_items = {"pi_svd_define_001", SECOND_ITEM}
    displaced = [
        outcome for outcome in trace.outcomes
        if outcome.explored_item_id not in (None, *goal_items)
    ]
    assert displaced and all(outcome.composed[0].practice_item_id in goal_items for outcome in displaced)
    distribution = router_decisions.head_distribution(trace.outcomes, lambda composed: composed[0].practice_item_id)
    assert set(distribution) <= goal_items
    assert sum(distribution.values()) == pytest.approx(1.0)


def _scheduled(item_id: str, reward: float, *, goal: bool = False) -> ScheduledItem:
    components = {"selection_reward": reward}
    if goal:
        components["goal_frontier"] = 0.5
    return ScheduledItem(
        practice_item_id=item_id, learning_object_id="lo", priority=reward, components=components,
        readiness_factor=None, selected_mode="short_answer", plain_english=[],
        reward_debug={"intent": "practice"},
    )


def _config(rate: float, window: float):
    from learnloop.config.schema import LearnLoopConfig

    config = LearnLoopConfig()
    config.scheduler.selection_exploration_rate = rate
    config.scheduler.selection_exploration_reward_window = window
    return config


def test_a_draw_composition_always_undoes_is_logged_as_deterministic():
    # Best is a goal item; its only near-tie is not. Exploring the near-tie
    # moves it first, and the goal quota (floor 0.5) pulls the goal item back:
    # both outcomes serve the goal item, so the choice was never drawn.
    queue = [_scheduled("goal", 1.0, goal=True), _scheduled("plain", 0.95)]
    trace = OfferTrace()
    _fill_offer_trace(
        trace, config=_config(0.2, 1.0), session=SchedulerSession(session_id="s"),
        now=datetime(2026, 5, 19, 12, tzinfo=UTC), limit=None, greedy_queue=queue, considered=queue,
        compose=lambda composed, record: _apply_goal_quota(composed, 0.5),
        base_propensity={"goal": 0.8, "plain": 0.2}, pinned_item_id=None, probe_block_reason=None,
        cold_deferrals=[], slate_id="slate", candidate_ids={"goal": "c1", "plain": "c2"}, placement_active=False,
    )
    assert [o.explored_item_id for o in trace.outcomes] == [None, "plain"]
    row = build_today_offer_decision(
        trace, offered=queue, head_of=lambda composed: composed[0].practice_item_id,
        section_of=lambda _item: "due", served_head="goal", surface="desktop_queue", policy="composed_offer_v2",
    )
    assert (row["chosen_ref"], row["propensity"], row["propensity_kind"], row["design"]) == (
        "goal", 1.0, "deterministic", None,
    )
    plain = next(c for c in json.loads(row["candidates_json"]) if c["ref"] == "plain")
    # The pre-composition draw gave it 0.2; the served offer never leads with it.
    assert (plain["exploration_propensity"], plain["propensity"]) == (0.2, 0.0)
    assert json.loads(row["detail_json"])["exploration"]["alternative_item_ids"] == ["plain"]


def test_a_committed_presentation_is_logged_as_the_continue_choice():
    pinned = _scheduled("probe", 0.4)
    other = _scheduled("other", 0.5)
    trace = OfferTrace(
        algorithm_version="mvp-0.11", session_id="s", now_iso="2026-05-19T12:00:00Z", slate_id="slate",
        candidate_ids={"probe": "c1", "other": "c2"}, greedy_item_ids=("other", "probe"),
        considered=(pinned, other), base_propensity={"other": 0.9, "probe": 0.1},
        exploration={"seed": "x"}, pinned_item_id="probe",
        outcomes=(
            ExplorationOutcome(None, 0.9, (pinned, other)),
            ExplorationOutcome("probe", 0.1, (pinned, other)),
        ),
    )
    row = build_today_offer_decision(
        trace, offered=[pinned, other], head_of=lambda composed: composed[0].practice_item_id,
        section_of=lambda _item: "due", served_head="probe", surface="desktop_queue", policy="composed_offer_v2",
    )
    assert (row["chosen_ref"], row["chosen_practice_item_id"], row["propensity_kind"]) == (
        CONTINUE_REF, "probe", "deterministic",
    )
    candidates = {c["ref"]: c for c in json.loads(row["candidates_json"])}
    assert (candidates[CONTINUE_REF]["source"], candidates[CONTINUE_REF]["propensity"]) == ("probe_presentation", 1.0)
    assert candidates["probe"]["propensity"] == 0.0 and candidates["probe"]["served_as"] == CONTINUE_REF
    assert sum(c["propensity"] for c in candidates.values()) == pytest.approx(1.0)


def test_a_recomposition_that_disagrees_with_the_served_head_is_refused():
    item = _scheduled("a", 1.0)
    trace = OfferTrace(
        slate_id="slate", considered=(item,), outcomes=(ExplorationOutcome(None, 1.0, (item,)),),
    )
    with pytest.raises(OfferHeadMismatch):
        build_today_offer_decision(
            trace, offered=[item], head_of=lambda composed: composed[0].practice_item_id,
            section_of=lambda _item: "due", served_head="b", surface="desktop_queue", policy="composed_offer_v2",
        )


# ── Codex review fixes (router R1 review) ────────────────────────────────────


def _row_for_insert(row: dict, **changes) -> dict:
    stored = {**row, **changes}
    for column in ("candidates_json", "exclusions_json", "detail_json"):
        if not isinstance(stored[column], str):
            stored[column] = json.dumps(stored[column])
    return stored


def test_a_row_the_ledger_constraints_refuse_raises_instead_of_vanishing(tmp_path):
    """F1: CHECK and NOT NULL violations raise; only a repeated receipt key is a no-op."""

    import sqlite3

    from learnloop.db.stores.router import insert_router_decision

    paths, repository, ctx, session_id = _two_due_items(tmp_path)
    _call(ctx, "get_today_queue", {"sessionId": session_id})
    [row] = _decisions(repository)
    with repository.atomic(), repository.connection() as connection:
        with pytest.raises(sqlite3.IntegrityError):
            insert_router_decision(
                connection,
                _row_for_insert(row, id="bad-p", receipt_key="today_offer:bad-p", propensity=1.0, propensity_kind="exact"),
            )
        with pytest.raises(sqlite3.IntegrityError):
            insert_router_decision(
                connection, _row_for_insert(row, id="bad-null", receipt_key="today_offer:bad-null", snapshot_hash=None)
            )
        # The same receipt key again is the idempotent duplicate it always was.
        assert insert_router_decision(connection, _row_for_insert(row, id="dup")) is False
    assert [r["id"] for r in _decisions(repository)] == [row["id"]]


def test_an_offer_row_the_ledger_refuses_is_warned_and_the_offer_still_publishes(tmp_path, monkeypatch, caplog):
    """F1: the offer call site catches the refusal, warns, and keeps the receipt."""

    import logging

    from learnloop_sidecar.handlers import queue as queue_handler

    paths, repository, ctx, session_id = _two_due_items(tmp_path)
    original = queue_handler.build_today_offer_decision

    def malformed(*args, **kwargs):
        return {**original(*args, **kwargs), "propensity": 1.0, "propensity_kind": "exact"}

    monkeypatch.setattr(queue_handler, "build_today_offer_decision", malformed)
    with caplog.at_level(logging.WARNING):
        queue = _call(ctx, "get_today_queue", {"sessionId": session_id})

    assert len(_served(queue)) == 2 and _decisions(repository) == []
    slate = repository.latest_scheduler_slate_by_session(session_id)
    with repository.connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM scheduler_offer_receipts WHERE slate_id=?", (slate["id"],)
        ).fetchone()[0] == 1
    assert any("router R1" in record.getMessage() and "refused" in record.getMessage() for record in caplog.records)


def test_an_unregistered_design_is_refused():
    """F5: the design column names a registered assignment mechanism only."""

    from learnloop.db.stores.router import ROUTER_DESIGNS, insert_router_decision

    assert {"scheduler_seeded_exploration", "epsilon_tiebreak"} <= set(ROUTER_DESIGNS)
    with pytest.raises(ValueError, match="design"):
        insert_router_decision(None, {"design": "made_up_draw"})  # refused before any SQL


def test_today_offers_name_the_schedulers_own_exploration_as_their_design(tmp_path):
    """F5: the Today draw is not randomization_layer's epsilon_tiebreak."""

    paths, repository, ctx, session_id = _two_due_items(tmp_path)
    _call(ctx, "get_today_queue", {"sessionId": session_id})
    [row] = _decisions(repository)
    assert row["propensity_kind"] == "exact"
    assert row["design"] == "scheduler_seeded_exploration"
    assert row["detail_json"]["exploration"]["mechanism"] == "scheduler_seeded_exploration"


def test_a_learner_pick_that_cannot_be_logged_never_fails_the_bind(tmp_path, monkeypatch, caplog):
    """F7: a logging failure inside the bind rolls back alone; the draft saves."""

    import logging
    import sqlite3

    from learnloop.db.stores import collection

    paths, repository, ctx, session_id = _two_due_items(tmp_path)
    queue = _call(ctx, "get_today_queue", {"sessionId": session_id})
    other = [item for section in queue["sections"] for item in section["items"]][1]

    slate = repository.latest_scheduler_slate_by_session(session_id)

    def drifted(connection, **_kwargs):
        # A partial write, then the kind of error a renumbered schema raises.
        connection.execute("UPDATE scheduler_slates SET returned_count = returned_count + 100 WHERE id=?", (slate["id"],))
        raise sqlite3.OperationalError("no such column: drifted")

    monkeypatch.setattr(collection, "record_learner_pick", drifted)
    with caplog.at_level(logging.WARNING):
        result = _draft(ctx, session_id, other["practiceItemId"], other["schedulerCandidateId"])

    assert result == {"ok": True}
    with repository.connection() as connection:
        intent = connection.execute(
            "SELECT scheduler_candidate_id FROM submission_intents WHERE submission_id='sub-1'"
        ).fetchone()
        returned = connection.execute("SELECT returned_count FROM scheduler_slates WHERE id=?", (slate["id"],)).fetchone()
    assert intent["scheduler_candidate_id"] == other["schedulerCandidateId"]
    assert returned[0] == slate["returned_count"]  # the partial write rolled back alone
    assert _decisions(repository, "learner_pick") == []
    assert any("learner pick" in record.getMessage() for record in caplog.records)


def test_a_teach_back_reopened_from_a_refreshed_list_is_one_pick(tmp_path):
    """F7: a conversation's later offer is validated, not picked again."""

    from types import SimpleNamespace

    from learnloop_sidecar.handlers.teach_back import _conversation_offer

    paths, repository, ctx, session_id = _two_due_items(tmp_path)
    first = [i for s in _call(ctx, "get_today_queue", {"sessionId": session_id})["sections"] for i in s["items"]]
    second = [i for s in _call(ctx, "get_today_queue", {"sessionId": session_id})["sections"] for i in s["items"]]
    assert first[0]["practiceItemId"] == second[0]["practiceItemId"]
    item_id = first[1]["practiceItemId"]
    assert second[1]["practiceItemId"] == item_id
    assert first[1]["schedulerCandidateId"] != second[1]["schedulerCandidateId"]

    def params(candidate_id):
        return SimpleNamespace(session_id=session_id, practice_item_id=item_id, scheduler_candidate_id=candidate_id)

    bound = _conversation_offer(repository, params(first[1]["schedulerCandidateId"]), None)
    assert bound == first[1]["schedulerCandidateId"]
    assert _conversation_offer(repository, params(second[1]["schedulerCandidateId"]), bound) == bound

    [pick] = _decisions(repository, "learner_pick")
    assert pick["chosen_scheduler_candidate_id"] == bound


def test_while_the_plan_serves_the_full_list_logs_no_system_choice_and_every_bind_is_a_pick(tmp_path, monkeypatch):
    """F3: under DL1's plan the list is a learner-choice surface, not a served head."""

    from learnloop_sidecar.handlers import queue as queue_handler

    paths, repository, ctx, session_id = _two_due_items(tmp_path)
    monkeypatch.setattr(queue_handler, "today_head_served", lambda _vault: False)
    queue = _call(ctx, "get_today_queue", {"sessionId": session_id})

    [row] = _decisions(repository)
    assert (row["decision_kind"], row["surface"]) == ("today_offer", "full_list")
    assert (row["chosen_ref"], row["chosen_practice_item_id"], row["chosen_scheduler_candidate_id"]) == (None, None, None)
    assert (row["propensity"], row["propensity_kind"], row["design"], row["seed"]) == (None, "not_served", None, None)
    assert {c["ref"] for c in row["candidates_json"] if c["kind"] == "item"} == set(_served(queue))
    assert row["detail_json"]["head_served"] is False

    # Opening the list's first item is the learner's choice too.
    head = queue["sections"][0]["items"][0]
    _draft(ctx, session_id, head["practiceItemId"], head["schedulerCandidateId"])
    [pick] = _decisions(repository, "learner_pick")
    assert pick["parent_decision_id"] == row["id"]
    assert (pick["chosen_ref"], pick["propensity_kind"], pick["learner_pick"]) == (head["practiceItemId"], "none", 1)
    assert pick["detail_json"]["overrode_ref"] is None


def test_the_full_list_seam_follows_dl1s_plan_once_it_lands(monkeypatch):
    """F3 tripwire: after the DL1 merge the seam must read ``plan_active``."""

    from types import SimpleNamespace

    from learnloop_sidecar.handlers import queue as queue_handler

    assert queue_handler.today_head_served(SimpleNamespace(config=None)) is True
    engine = pytest.importorskip("learnloop.daily_plan.engine")
    monkeypatch.setattr(engine, "plan_active", lambda _vault: True)
    monkeypatch.setattr(queue_handler, "plan_active", lambda _vault: True, raising=False)
    assert queue_handler.today_head_served(SimpleNamespace(config=None)) is False


def test_the_head_rule_and_the_served_list_read_one_state_snapshot(tmp_path, monkeypatch):
    """F6: a due date moved between the DTO read and the head rule's own read
    used to refuse the row (OfferHeadMismatch); one shared read logs it."""

    from learnloop_sidecar.handlers import queue as queue_handler

    paths, repository, ctx, session_id = _two_due_items(tmp_path, toml="[scheduler]\nselection_exploration_rate = 0.0\n")
    original = queue_handler.scheduled_item_dtos

    def then_the_worker_reschedules(vault, repo, items, **kwargs):
        dtos = original(vault, repo, items, **kwargs)
        with repo.connection() as connection:
            connection.execute(
                "UPDATE practice_item_state SET due_at='2099-01-01T00:00:00Z' WHERE practice_item_id=?",
                (items[0].practice_item_id,),
            )
            connection.commit()
        return dtos

    monkeypatch.setattr(queue_handler, "scheduled_item_dtos", then_the_worker_reschedules)
    queue = _call(ctx, "get_today_queue", {"sessionId": session_id})

    [row] = _decisions(repository)
    assert row["chosen_ref"] == _served(queue)[0]


def test_teach_back_readiness_is_probed_once_per_offer(tmp_path, monkeypatch):
    """F6: the served list's filter and the head rule share one readiness probe."""

    from learnloop.vault.writer import upsert_practice_item
    from learnloop_sidecar.handlers import queue as queue_handler
    from learnloop_sidecar.handlers import teach_back as teach_back_handler

    paths, repository, _ctx, session_id = _two_due_items(tmp_path)
    upsert_practice_item(paths.root, _TEACH_BACK_ITEM, clock=FrozenClock(NOW))
    ctx = _context(paths.root)
    calls = []

    def unready(_vault, **_kwargs):
        calls.append(1)
        return False

    monkeypatch.setattr(teach_back_handler, "teach_back_offerable", unready)
    monkeypatch.setattr(queue_handler, "teach_back_offerable", unready, raising=False)
    queue = _call(ctx, "get_today_queue", {"sessionId": session_id})

    assert "pi_svd_teach_back" not in _served(queue)
    [row] = _decisions(repository)
    assert row["exclusions_json"]["named"]["teach_back_provider_unready"] == ["pi_svd_teach_back"]
    assert len(calls) == 1


_TEACH_BACK_ITEM = {
    "id": "pi_svd_teach_back",
    "learning_object_id": "lo_svd_definition",
    "subjects": None,
    "practice_mode": "teach_back",
    "attempt_types_allowed": ["teach_back"],
    "evidence_facets": ["recall"],
    "evidence_weights": {"recall": 1.0},
    "criterion_facet_weights": {"core_definition": {"recall": 1.0}},
    "prompt": "Teach the singular value decomposition to a curious student.",
    "expected_answer": "U, Sigma and V transpose.",
    "grading_rubric": {
        "max_points": 1,
        "criteria": [{"id": "core_definition", "points": 1.0, "tier": "core", "description": "States U, Sigma, V."}],
        "fatal_errors": [],
    },
    "created_at": "2026-05-19T12:00:00Z",
    "updated_at": "2026-05-19T12:00:00Z",
}


def test_candidate_propensities_are_one_distribution_with_continue_counted_once():
    """F9: the pinned item's mass is on "continue" only; everything sums to 1."""

    pinned = _scheduled("probe", 0.4)
    other = _scheduled("other", 0.5)
    trace = OfferTrace(
        algorithm_version="mvp-0.15", session_id="s", now_iso="2026-05-19T12:00:00Z", slate_id="slate",
        candidate_ids={"probe": "c1", "other": "c2"}, greedy_item_ids=("other", "probe"),
        considered=(pinned, other), base_propensity={"other": 0.9, "probe": 0.1},
        exploration={"seed": "x"}, pinned_item_id="probe",
        outcomes=(
            ExplorationOutcome(None, 0.7, (pinned, other)),
            ExplorationOutcome("other", 0.3, (other, pinned)),
        ),
    )
    row = build_today_offer_decision(
        trace, offered=[pinned, other], head_of=lambda composed: composed[0].practice_item_id,
        section_of=lambda _item: "due", served_head="probe", surface="desktop_queue", policy="composed_offer_v2",
    )
    candidates = {c["ref"]: c for c in json.loads(row["candidates_json"])}
    assert row["chosen_ref"] == CONTINUE_REF and row["propensity"] == pytest.approx(0.7)
    assert candidates[CONTINUE_REF]["propensity"] == pytest.approx(0.7)
    assert candidates["probe"]["propensity"] == 0.0 and candidates["probe"]["served_as"] == CONTINUE_REF
    assert candidates["other"]["propensity"] == pytest.approx(0.3)
    assert sum(c["propensity"] for c in candidates.values()) == pytest.approx(1.0)


def test_the_snapshot_hash_covers_the_decision_inputs_not_the_build_time():
    """F9: same inputs at another instant hash alike; another session context differs."""

    item = _scheduled("a", 1.0)

    def row(now_iso: str, minutes: int, rate: float = 0.1):
        trace = OfferTrace(
            algorithm_version="mvp-0.15", session_id="s", now_iso=now_iso, slate_id="slate",
            candidate_ids={"a": "c1"}, considered=(item,), outcomes=(ExplorationOutcome(None, 1.0, (item,)),),
            session_context={"available_minutes": minutes, "energy": None, "short_session": False,
                             "readiness_factor": None},
            config_snapshot={"scheduler": {"selection_exploration_rate": rate}},
        )
        return build_today_offer_decision(
            trace, offered=[item], head_of=lambda composed: composed[0].practice_item_id,
            section_of=lambda _item: "due", served_head="a", surface="desktop_queue", policy="composed_offer_v2",
            inputs={"teach_back_ready": None},
        )

    base = row("2026-05-19T12:00:00Z", 20)["snapshot_hash"]
    assert row("2026-05-19T12:00:07Z", 20)["snapshot_hash"] == base
    assert row("2026-05-19T12:00:00Z", 45)["snapshot_hash"] != base
    assert row("2026-05-19T12:00:00Z", 20, rate=0.2)["snapshot_hash"] != base
