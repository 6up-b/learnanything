"""Daily-loop DL2 Codex review (job 20261020-000102-fgOsoH): the fail-first tests.

Each test names its finding. Every one failed on ``bbb0b05d3`` (the reviewed
commit) and passes after the fix; F2 (the successor) was rejected, and its
test pins the predecessor with commitments populated (intent off). Fakes
only; no model is ever called.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.curriculum import commitments as C
from learnloop.daily_plan.admission import projected_review_load
from learnloop.daily_plan.chooser import LaneQuotaChooser
from learnloop.daily_plan.engine import PlanEnv, _estimator, _review_items, advance, build_plan
from learnloop.daily_plan.headline import today_headline
from learnloop.daily_plan.intent_cost import load_cost_context, projected_cost
from learnloop.daily_plan.lanes import LegacyLanesSource, PoolItem, reentry_order
from learnloop.daily_plan.types import PlanState
from learnloop.db.repositories import Repository
from learnloop.intent import deadline as deadline_module
from learnloop.intent.checks import COLD_BANNER, PRACTICE_BANNER, served_check, settle_answered_checks
from learnloop.intent.control import Scope
from learnloop.intent.deadline import goal_id_for, set_deadline
from learnloop.scheduling.intent.model import TIER_PUSH, TIER_UNCOMMITTED
from learnloop.scheduling.intent.recall_targets import effective_due, load_anchors
from learnloop.scheduling.scheduler import build_due_queue
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.daily_plan_fakes import MovableClock, iso, record_attempt, seed_due
from tests.helpers import append_config_toml, create_daily_plan_vault
from tests.intent_fakes import ITEM_LO, NOW, OURS, make_intent_vault


@pytest.fixture
def iv(tmp_path):
    return make_intent_vault(tmp_path / "vault")


def _env(iv, at, *, session_id=None) -> PlanEnv:
    return PlanEnv(vault=iv.vault, repository=iv.repository, clock=MovableClock(at), session_id=session_id)


def _reveal(repository, item_id, at, *, routine=False):
    repository.insert_reveal_event(
        {
            "practice_item_id": item_id,
            "learning_object_id": ITEM_LO.get(item_id),
            "source_kind": "answer_display" if routine else "tutor_answer",
            "basis": f"feedback_full_answer:{item_id}" if routine else None,
            "amount": 1.0,
            "created_at": iso(at),
        }
    )


def _primed_attempt(iv, item_id, at) -> str:
    attempt_id = iv.answer(item_id, at)
    with iv.repository.connection() as connection:
        connection.execute("UPDATE practice_attempts SET primed = 1 WHERE id = ?", (attempt_id,))
        connection.commit()
    return attempt_id


# -- F1: follow-ups and plans already built honour intent -------------------------------------------


def test_f1_a_pending_follow_up_never_resurrects_a_paused_item(iv):
    iv.repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref="mc_f1",
        context={"kind": "causal_cold_verification", "source_attempt_id": "att_src"},
        not_before=iso(NOW - timedelta(hours=1)), selected_item_id="pi_a1",
        expires_at=iso(NOW + timedelta(days=5)), clock=FrozenClock(NOW - timedelta(hours=2)),
    )
    assert iv.queue(NOW)[0] == "pi_a1", "sanity: the follow-up leads the queue"
    iv.choose("practice_item", "pi_a1", "pause", NOW + timedelta(minutes=1))
    assert "pi_a1" not in iv.queue(NOW + timedelta(minutes=2))
    # Nothing was written: resuming brings the follow-up back first.
    iv.choose("practice_item", "pi_a1", "learn", NOW + timedelta(minutes=3))
    assert iv.queue(NOW + timedelta(minutes=4))[0] == "pi_a1"


def test_f1_a_follow_up_never_serves_an_item_a_check_once_still_holds(iv):
    iv.repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref="mc_f1b",
        context={"kind": "causal_cold_verification", "source_attempt_id": "att_src"},
        not_before=iso(NOW - timedelta(hours=1)), selected_item_id="pi_b1",
        expires_at=iso(NOW + timedelta(days=5)), clock=FrozenClock(NOW - timedelta(hours=2)),
    )
    iv.choose("practice_item", "pi_b1", "check_once", NOW)
    assert "pi_b1" not in iv.queue(NOW + timedelta(days=1))


def test_f1_pausing_after_the_plan_was_built_keeps_its_items_unserved(iv):
    at = NOW + timedelta(minutes=1)
    env = _env(iv, at, session_id="s_f1")
    record = build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    planned = {item.practice_item_id for item in record.items()}
    assert {"pi_a1", "pi_a2"} <= planned, "sanity: lo_a is in the plan"
    iv.choose("learning_object", "lo_a", "pause", at + timedelta(seconds=30))
    served = []
    for _ in range(20):
        record, step = advance(env, serve=True)
        if step["kind"] != "item":
            break
        served.append(step["practice_item_id"])
        env.clock.advance(2)
        record_attempt(iv.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now())
        env.clock.advance(1)
    assert not {"pi_a1", "pi_a2"} & set(served)
    displaced = {item.practice_item_id: item.displaced_reason for item in record.items() if item.displaced_at}
    assert displaced.get("pi_a1") == "intent_paused" and displaced.get("pi_a2") == "intent_paused"


def test_f1_a_check_once_chosen_after_the_plan_holds_its_planned_item(iv):
    at = NOW + timedelta(minutes=1)
    env = _env(iv, at, session_id="s_f1c")
    record = build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    assert "pi_a1" in {item.practice_item_id for item in record.items()}
    iv.choose("practice_item", "pi_a1", "check_once", at + timedelta(seconds=30))
    record, _step = advance(env, serve=False)
    item = next(item for item in record.items() if item.practice_item_id == "pi_a1")
    assert item.displaced_reason == "intent_check_waiting"


# -- F3: "Check once" through the one eligibility decision -------------------------------------------


def test_f3_a_check_whose_answer_the_tutor_revealed_is_not_served_as_a_check_on_your_own(iv):
    iv.choose("practice_item", "pi_b1", "check_once", NOW)
    due_day = NOW + timedelta(days=8)
    _reveal(iv.repository, "pi_b1", due_day - timedelta(hours=2))
    view = served_check(iv.vault, iv.repository, "pi_b1", now=due_day)
    assert view["cold"] is False and view["banner"] == PRACTICE_BANNER
    assert view["banner"] != COLD_BANNER and "help_header" not in view
    # Help availability is preserved: the item is still served (as practice).
    assert "pi_b1" in iv.queue(due_day)
    # The primed attempt is practice: it answers nothing, and the check comes
    # back its delay after it.
    attempt_at = due_day + timedelta(minutes=5)
    _primed_attempt(iv, "pi_b1", attempt_at)
    assert settle_answered_checks(iv.vault, iv.repository, clock=FrozenClock(attempt_at + timedelta(minutes=1))) == []
    (check,) = iv.serving(attempt_at + timedelta(minutes=1)).checks.values()
    assert check.answered_by is None and check.due is False and check.date_source == "after_practice"
    assert check.date == attempt_at.replace(microsecond=0) + timedelta(days=7)
    later = attempt_at + timedelta(days=7, minutes=1)
    assert served_check(iv.vault, iv.repository, "pi_b1", now=later)["cold"] is True


def test_f3_a_hinted_attempt_does_not_use_up_the_check(iv):
    commitment = iv.choose("practice_item", "pi_b1", "check_once", NOW).commitment_id
    due_day = NOW + timedelta(days=8)
    attempt_id = iv.answer("pi_b1", due_day)
    with iv.repository.connection() as connection:
        connection.execute("UPDATE practice_attempts SET hints_used = 1 WHERE id = ?", (attempt_id,))
        connection.commit()
    assert settle_answered_checks(iv.vault, iv.repository, clock=FrozenClock(due_day + timedelta(minutes=1))) == []
    assert C.resolve_disposition(iv.repository, commitment) == "one_check_pending"


def test_f3_an_lo_check_prefers_a_candidate_that_can_be_taken_cold(iv):
    iv.choose("learning_object", "lo_a", "check_once", NOW)
    due_day = NOW + timedelta(days=8)
    baseline = [item for item in iv.queue(due_day) if item in ("pi_a1", "pi_a2")]
    assert len(baseline) == 1, "sanity: one item per check"
    exposed = baseline[0]
    other = ({"pi_a1", "pi_a2"} - {exposed}).pop()
    # Two days back: past the one-day hold a reveal puts on its whole LO, so
    # the sibling is cold while the revealed item stays exposed (only an
    # attempt absorbs a tutor answer).
    _reveal(iv.repository, exposed, due_day - timedelta(days=2))
    assert [item for item in iv.queue(due_day) if item in ("pi_a1", "pi_a2")] == [other]
    assert served_check(iv.vault, iv.repository, other, now=due_day)["cold"] is True
    assert iv.serving(due_day).withhold_reason(exposed) == "intent_check_held"


def test_f3_a_routine_display_makes_the_check_wait_until_it_is_cold_again(iv):
    iv.choose("practice_item", "pi_b1", "check_once", NOW)
    due_day = NOW + timedelta(days=8)
    _reveal(iv.repository, "pi_b1", due_day - timedelta(hours=1), routine=True)
    assert "pi_b1" not in iv.queue(due_day)
    assert iv.serving(due_day).withhold_reason("pi_b1") == "intent_check_held"
    lapsed = due_day + timedelta(days=1, hours=1)
    assert "pi_b1" in iv.queue(lapsed)
    assert served_check(iv.vault, iv.repository, "pi_b1", now=lapsed)["cold"] is True


def test_f3_an_exposure_after_planning_is_read_at_the_serve(iv):
    iv.choose("practice_item", "pi_b1", "check_once", NOW)
    due_day = NOW + timedelta(days=8)
    env = _env(iv, due_day, session_id="s_f3")
    record = build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    assert any(item.practice_item_id == "pi_b1" and item.check_kind == "check_once" for item in record.items())
    assert served_check(iv.vault, iv.repository, "pi_b1", now=due_day)["cold"] is True
    _reveal(iv.repository, "pi_b1", due_day + timedelta(minutes=1))
    view = served_check(iv.vault, iv.repository, "pi_b1", now=due_day + timedelta(minutes=2))
    assert view["cold"] is False and view["banner"] == PRACTICE_BANNER


def test_f3_an_lo_check_planned_item_exposed_after_planning_is_displaced(iv):
    iv.choose("learning_object", "lo_a", "check_once", NOW)
    due_day = NOW + timedelta(days=8)
    env = _env(iv, due_day, session_id="s_f3b")
    record = build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    (planned,) = [item.practice_item_id for item in record.items() if item.check_kind == "check_once"]
    _reveal(iv.repository, planned, due_day + timedelta(minutes=1))
    env.clock.advance(2)
    record, _step = advance(env, serve=False)
    item = next(item for item in record.items() if item.practice_item_id == planned)
    assert item.displaced_reason == "intent_check_held"


# -- F4: a held grade is not the anchor --------------------------------------------------------------


def test_f4_a_held_grade_never_becomes_the_anchor_through_the_real_attempt_path(tmp_path):
    from tests.split_live_helpers import split_vault
    from tests.test_held_grade_evidence import ITEM, VERSION, _graded_apply, _held_apply

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    reviewed = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
    _graded_apply(vault, repository, ITEM, {"setup": 2.0, "result": 2.0}, attempt_id="att_review", when=reviewed)
    due_before = repository.practice_item_state(ITEM).due_at
    _held_apply(vault, repository, ITEM, {"setup": 0.0, "result": 0.0},
                attempt_id="att_held", when=reviewed + timedelta(days=4))
    # The attempt path kept FSRS state exactly as it was for the held grade...
    assert repository.practice_item_state(ITEM).due_at == due_before
    with repository.connection() as connection:
        anchors = load_anchors(connection)
    # ...so the anchor stays the review that set due_at.
    assert anchors[ITEM][1] == "att_review"
    from learnloop.params.fitted_params import resolve_fsrs_weights

    weights = tuple(resolve_fsrs_weights(repository))
    light = effective_due(due_at=due_before, anchor_at=anchors[ITEM][0], target=0.80, weights=weights).due
    wrong = effective_due(due_at=due_before, anchor_at=iso(reviewed + timedelta(days=4)), target=0.80, weights=weights).due
    assert light != wrong and light > wrong


# -- F5: a primed retry moves neither the cost preview nor admission -------------------------------------


def _f5_vault(tmp_path, name, *, primed_retry: bool):
    iv = make_intent_vault(tmp_path / name)
    review = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
    with iv.repository.connection() as connection:
        connection.execute("DELETE FROM practice_attempts WHERE practice_item_id = 'pi_b1'")
        connection.commit()
    iv.answer("pi_b1", review)
    last = review
    if primed_retry:
        last = datetime(2026, 10, 10, 9, 0, tzinfo=UTC)
        _primed_attempt(iv, "pi_b1", last)
    seed_due(iv.repository, "pi_b1", due=datetime(2026, 10, 11, 9, 0, tzinfo=UTC), last=last)
    iv.choose("learning_object", "lo_b", "keep", NOW)
    return iv


def test_f5_a_primed_retry_changes_neither_the_cost_preview_nor_the_review_load(tmp_path):
    plain = _f5_vault(tmp_path, "plain", primed_retry=False)
    retried = _f5_vault(tmp_path, "retried", primed_retry=True)
    at = datetime(2026, 10, 10, 12, 0, tzinfo=UTC)
    costs, loads, lasts = [], [], []
    for iv in (plain, retried):
        serving = iv.serving(at)
        context = load_cost_context(iv.vault, iv.repository, clock=FrozenClock(at))
        costs.append(projected_cost(iv.vault, context, "learn", {"pi_b1": serving.intent("pi_b1")}))
        env = _env(iv, at)
        items = [item for item in _review_items(env, _estimator(env), serving) if item.practice_item_id == "pi_b1"]
        lasts.append(items[0].last_review_at)
        loads.append(projected_review_load(items, now=at, horizon_days=int(iv.vault.config.plan.load_horizon_days)))
    assert costs[0] == costs[1]
    assert loads[0] == loads[1]
    assert lasts == ["2026-10-01T09:00:00Z", "2026-10-01T09:00:00Z"]


# -- F6: re-entry's intent order survives the chooser ---------------------------------------------------


def test_f6_the_chooser_takes_the_master_block_first_in_re_entry():
    def pool_item(item_id, lo_id, rank):
        return PoolItem(practice_item_id=item_id, learning_object_id=lo_id, rank=rank, priority=1.0,
                        lane="maintain", reason="past its review date", est_minutes=6.0, never_attempted=False,
                        due=True)

    pool = [pool_item("pi_plain", "lo_plain", 0), pool_item("pi_master", "lo_master", 10)]
    ordered = reentry_order(pool, {"pi_master": TIER_PUSH, "pi_plain": TIER_UNCOMMITTED})
    assert [item.practice_item_id for item in ordered] == ["pi_master", "pi_plain"]
    source = LegacyLanesSource(pool=ordered, lanes_allowed=("maintain", "repair"))
    state = PlanState(plan_id="p", kind="reentry", minutes_budget=15.0, minutes_left=15.0,
                      lane_minutes_left={"maintain": 15.0}, days_since_last_activity=9, streak_days=0,
                      current_block_id=None, lane_minutes_allotted={"maintain": 15.0})
    candidates = source.candidates(state)
    choice = LaneQuotaChooser().choose(state, candidates)
    chosen = next(candidate for candidate in candidates if candidate.candidate_id == choice.candidate_id)
    assert chosen.item_ids[0] == "pi_master"
    # Without intent (tiers None) the order is DL1's exactly: no plan_rank.
    assert all(item.plan_rank is None for item in reentry_order(pool))


# -- F7: reading by the source's intent -----------------------------------------------------------------


def _reading_intent_vault(tmp_path, monkeypatch):
    from tests.test_daily_plan_reading import _seed_as_you_read

    import learnloop.reader.recap as recap

    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_r": [("pi_r1", 2.0)]})
    extraction = _seed_as_you_read(paths)
    monkeypatch.setattr(
        recap, "source_learning_objects",
        lambda vault, repository, extraction_id: ["lo_r"] if extraction_id == extraction else [],
    )
    vault = load_vault(paths.root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    return vault, repository, extraction


@pytest.mark.parametrize("choice,reads", [
    ("learn", True), ("master", True), ("pause", False), ("reference", False), ("let_go", False),
    ("keep", False), ("light_touch", False),
])
def test_f7_a_source_reads_only_under_learn_or_master(tmp_path, monkeypatch, choice, reads):
    from learnloop.intent.control import apply_choice

    vault, repository, extraction = _reading_intent_vault(tmp_path, monkeypatch)
    at = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
    apply_choice(vault, repository, Scope("source", extraction), choice, clock=FrozenClock(at))
    env = PlanEnv(vault=vault, repository=repository, clock=MovableClock(at + timedelta(minutes=1)))
    record = build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    assert (record.split.get("reading") is not None) is reads


def test_f7_a_pause_after_the_plan_drops_its_pending_reading(tmp_path, monkeypatch):
    from learnloop.intent.control import apply_choice

    vault, repository, extraction = _reading_intent_vault(tmp_path, monkeypatch)
    at = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
    # Some commitment makes intent active; the source itself stays uncommitted.
    apply_choice(vault, repository, Scope("learning_object", "lo_eigen_basics"), "keep", clock=FrozenClock(at))
    env = PlanEnv(vault=vault, repository=repository, clock=MovableClock(at + timedelta(minutes=1)), session_id="s_f7")
    record = build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    assert record.split.get("reading") is not None, "sanity: the source reads"
    apply_choice(vault, repository, Scope("source", extraction), "pause", clock=FrozenClock(at + timedelta(minutes=2)))
    env.clock.advance(3)
    steps = []
    for _ in range(30):
        record, step = advance(env, serve=False)
        steps.append(step["kind"])
        if step["kind"] != "item":
            break
        env.clock.advance(2)
        record_attempt(repository, step["practice_item_id"], step["learning_object_id"], env.clock.now())
        env.clock.advance(1)
    assert "reading" not in steps
    assert not [block for block in record.blocks if block.is_reading and block.outcome != "displaced"]


# -- F8, F9: deadlines ------------------------------------------------------------------------------


def _disjoint_facets(iv):
    """lo_a and lo_b share their concept, but not their facets."""

    paths = VaultPaths(iv.vault.root, iv.vault.config)
    for item_id, facet in (("pi_a1", "svd_a_fact"), ("pi_a2", "svd_a_fact"), ("pi_b1", "svd_b_fact")):
        path = paths.practice_item_path("linear-algebra", item_id)
        data = read_yaml(path)
        data["evidence_facets"] = [facet]
        data["evidence_weights"] = {facet: 1.0}
        write_yaml(path, data)
    iv.reload()


def test_f8_a_deadline_covers_its_own_los_not_others_on_the_same_concept(iv):
    from learnloop.goals.goal_projection import resolve_goal_scope

    _disjoint_facets(iv)
    assert iv.vault.learning_objects["lo_a"].concept == iv.vault.learning_objects["lo_b"].concept
    iv.choose("learning_object", "lo_a", "learn", NOW)
    result = set_deadline(iv.vault, iv.repository, Scope("learning_object", "lo_a"), "2026-12-01", clock=FrozenClock(NOW))
    iv.reload()
    goal = next(goal for goal in iv.vault.goals if goal.id == result["goal_id"])
    scope = resolve_goal_scope(iv.vault, goal, iv.repository)
    assert "lo_a" in scope
    assert "lo_b" not in scope  # same concept, disjoint facets: outside the goal


def _goals(iv):
    data = read_yaml(VaultPaths(iv.vault.root, iv.vault.config).goals_path)
    return [goal for goal in data.get("goals") or [] if str(goal.get("id", "")).startswith("goal_intent_")]


def test_f9_a_crash_between_publishing_and_linking_is_recovered_without_an_orphan(iv, monkeypatch):
    commitment = iv.choose("learning_object", "lo_a", "learn", NOW).commitment_id
    original = deadline_module.C.append_commitment_version
    calls = {"n": 0}

    def crash_once(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("process died after goals.yaml was published")
        return original(*args, **kwargs)

    monkeypatch.setattr(deadline_module.C, "append_commitment_version", crash_once)
    with pytest.raises(RuntimeError):
        set_deadline(iv.vault, iv.repository, Scope("learning_object", "lo_a"), "2026-12-01", clock=FrozenClock(NOW))
    iv.reload()
    assert [goal["id"] for goal in _goals(iv)] == [goal_id_for(commitment)]
    retried = set_deadline(iv.vault, iv.repository, Scope("learning_object", "lo_a"), "2026-12-01", clock=FrozenClock(NOW))
    iv.reload()
    assert retried["goal_id"] == goal_id_for(commitment)
    assert [goal["id"] for goal in _goals(iv)] == [goal_id_for(commitment)]
    assert C.resolve_head(iv.repository, commitment).goal_id == goal_id_for(commitment)
    moved = set_deadline(iv.vault, iv.repository, Scope("learning_object", "lo_a"), "2026-12-20", clock=FrozenClock(NOW))
    iv.reload()
    active = [goal for goal in _goals(iv) if goal["status"] == "active"]
    assert moved["goal_id"] == goal_id_for(commitment) and [goal["due_at"] for goal in active] == ["2026-12-20T23:59:59Z"]


def test_f9_concurrent_writers_publish_one_goal_and_one_link(iv):
    commitment = iv.choose("learning_object", "lo_a", "learn", NOW).commitment_id
    barrier = threading.Barrier(2)
    errors: list[BaseException] = []

    def write(due):
        try:
            vault = load_vault(iv.root)
            repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
            barrier.wait()
            set_deadline(vault, repository, Scope("learning_object", "lo_a"), due, clock=FrozenClock(NOW))
        except BaseException as error:  # noqa: BLE001 - reported below
            errors.append(error)

    threads = [threading.Thread(target=write, args=(due,)) for due in ("2026-12-01", "2026-12-02")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    iv.reload()
    assert [goal["id"] for goal in _goals(iv)] == [goal_id_for(commitment)]
    links = [row for row in iv.repository.commitment_versions_for(commitment) if row.get("goal_id")]
    assert len(links) == 1


# -- F10: the headline counts what the plan can serve -----------------------------------------------------


def test_f10_the_headline_leaves_out_excluded_los_and_items(iv):
    at = NOW + timedelta(minutes=1)
    before = today_headline(iv.vault, iv.repository, now=at)
    assert {"lo_a", "lo_c"} <= set(before["learning_object_classes"])
    iv.choose("learning_object", "lo_a", "pause", NOW)
    iv.choose("practice_item", "pi_c1", "let_go", NOW)
    after = today_headline(iv.vault, iv.repository, now=at)
    assert "lo_a" not in after["learning_object_classes"]
    assert "lo_c" in after["learning_object_classes"]  # pi_c2 is still served
    assert sum(after["counts"].values()) == sum(before["counts"].values()) - 1
    assert after["expected_recall_items"] == before["expected_recall_items"] - 3  # pi_a1, pi_a2, pi_c1
    append_config_toml(iv.root, "[intent]\nenabled = false\n")
    iv.reload()
    off = today_headline(iv.vault, iv.repository, now=at)
    assert off["counts"] == before["counts"] and off["expected_recall_items"] == before["expected_recall_items"]


# -- F2 (rejected): the predecessor with commitments populated ------------------------------------------------


def test_f2_with_intent_off_commitments_change_nothing_in_the_ranked_list_or_the_plan(tmp_path):
    bare = make_intent_vault(tmp_path / "bare")
    chosen = make_intent_vault(tmp_path / "chosen")
    chosen.choose("learning_object", "lo_a", "pause", NOW)
    chosen.choose("learning_object", "lo_b", "check_once", NOW)
    chosen.choose("learning_object", "lo_c", "light_touch", NOW)
    for iv in (bare, chosen):
        append_config_toml(iv.root, "[intent]\nenabled = false\n")
        iv.reload()
    at = NOW + timedelta(days=8)

    def ranked(iv):
        return [
            (entry.practice_item_id, round(entry.priority, 12), tuple(sorted(entry.components.items())))
            for entry in build_due_queue(iv.vault, iv.repository, clock=FrozenClock(at), persist_explanations=False)
            if entry.practice_item_id in OURS
        ]

    assert ranked(bare) == ranked(chosen)
    plans = []
    for iv in (bare, chosen):
        record = build_plan(_env(iv, at), kind="normal", budget=25.0, remembered=25, minutes_source="chip")
        blocks = [[(item.practice_item_id, item.lane, item.check_kind) for item in block.items] for block in record.blocks]
        plans.append((record.split.get("pool"), record.admission, blocks))
    assert plans[0] == plans[1]
    with chosen.repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM commitments").fetchone()[0] == 3
