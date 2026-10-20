"""Daily-loop DL2 fix round 5 (orchestrator rulings on the verify of
``1a8128254``, Codex job 20261020-124824-K2sjh2): the fail-first tests.

F16 (High, a round-4 regression): a due "Check once" was forced into the
plan's first block past the staged frame, so an item holding a live
assessment reservation (``activity_surface_reservations``) was planned as a
check. Ruling: checks are exempt from value and count composition only, never
from a mandatory constraint. A reserved candidate is never a check's item: an
LO check takes an eligible sibling (its own selection rule: the top-ranked
servable candidate); a check left with none is recorded in
``checks_unplanned`` as ``assessment_reservation``. Every other staged-frame
refusal is evaluated before an item is forced; a refused check stays in the
pool, so the frame refuses it and names the refusal on the ``plan_block`` row.

F17 (Medium): moving a deadline kept the linked goal's ``target_recall`` from
the depth the deadline was added at.

The behaviour tests ran against ``1a8128254`` and failed for the reasons the
findings give; the controls passed (counts in
``docs/reviews/daily-loop-dl2-codex-review.md``). Fakes only; the staged
policy runs with ``router.mode = "staged"`` (no model is ever asked).
"""

from __future__ import annotations

import json
import random
from datetime import timedelta

import pytest

from learnloop.algorithm_versions import INTENT_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.daily_plan.engine import DEFAULT_POLICY, PlanEnv, build_plan
from learnloop.daily_plan.policy import policy_for
from learnloop.db.repositories import MasteryState, Repository
from learnloop.intent.control import Scope, apply_choice
from learnloop.intent.deadline import set_deadline
from learnloop.substrate.activities import reserve_surface, resolve_legacy_item
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from tests.daily_plan_fakes import MovableClock, iso, record_attempt, seed_due
from tests.helpers import append_config_toml, create_daily_plan_vault
from tests.intent_fakes import NOW, make_intent_vault
from tests.test_intent_fix_round4 import _as_teach_back, _never_worth_its_minutes

STAGED = '[router]\nmode = "staged"\n'
DUE_DAY = NOW + timedelta(days=8)


def _reserve(vault, repository, item_id):
    resolved = resolve_legacy_item(vault, repository, vault.practice_items[item_id], purpose="assessment")
    reserve_surface(repository, surface_id=resolved.surface_id, purpose="assessment")


def _staged_vault(tmp_path):
    iv = make_intent_vault(tmp_path / "vault")
    append_config_toml(iv.root, STAGED)
    iv.reload()
    return iv


def _env(iv, at, *, staged=True):
    clock = MovableClock(at)
    policy = policy_for(iv.vault, iv.repository, clock=clock) if staged else DEFAULT_POLICY
    if staged:
        assert policy is not DEFAULT_POLICY
    return PlanEnv(vault=iv.vault, repository=iv.repository, clock=clock, policy=policy)


def _plan(iv, at, *, budget=15.0, staged=True):
    return build_plan(_env(iv, at, staged=staged), kind="normal", budget=budget, remembered=int(budget),
                      minutes_source="chip")


def _planned(record):
    return {item.practice_item_id for item in record.items()}


def _plan_block_rows(repository):
    with repository.connection() as connection:
        rows = [dict(row) for row in connection.execute(
            "SELECT * FROM router_decisions WHERE decision_kind = 'plan_block' ORDER BY created_at, id"
        )]
    for row in rows:
        row["exclusions_json"] = json.loads(row["exclusions_json"])
    return rows


# -- F16: the verify's reproduction, through the staged policy ---------------------------------


@pytest.mark.parametrize("staged", [True, False], ids=["staged", "dl1_pair"])
def test_f16_a_reserved_item_check_is_never_planned_and_the_miss_is_recorded(tmp_path, staged):
    iv = _staged_vault(tmp_path)
    commitment = iv.choose("practice_item", "pi_c2", "check_once", NOW).commitment_id
    _reserve(iv.vault, iv.repository, "pi_c2")
    record = _plan(iv, DUE_DAY, staged=staged)
    assert "pi_c2" not in _planned(record)
    assert [row for row in record.split.get("checks") or [] if row["practice_item_id"] == "pi_c2"] == []
    (miss,) = [row for row in record.split["checks_unplanned"] if row["commitment_id"] == commitment]
    assert miss["reason"] == "assessment_reservation"
    assert miss["reserved_item_ids"] == ["pi_c2"]


@pytest.mark.parametrize("reserved,sibling", [("pi_a1", "pi_a2"), ("pi_a2", "pi_a1")])
def test_f16_an_lo_check_takes_an_eligible_sibling_of_a_reserved_candidate(tmp_path, reserved, sibling):
    iv = _staged_vault(tmp_path)
    iv.choose("learning_object", "lo_a", "check_once", NOW)
    _reserve(iv.vault, iv.repository, reserved)
    record = _plan(iv, DUE_DAY)
    planned = _planned(record)
    assert reserved not in planned
    (row,) = record.split["checks"]
    assert row["practice_item_id"] == sibling and sibling in planned
    assert record.split["checks_unplanned"] == []


def test_f16_the_frame_refuses_a_reserved_check_before_it_is_forced(tmp_path, monkeypatch):
    """The second gate alone (the reservation read of check selection
    disabled): the staged frame's mandatory constraints are evaluated before
    the item enters the first block, the refusal is named on the ``plan_block``
    row, and the miss is recorded with the constraint's key."""

    from learnloop.scheduling.intent import serving

    iv = _staged_vault(tmp_path)
    commitment = iv.choose("practice_item", "pi_c2", "check_once", NOW).commitment_id
    _reserve(iv.vault, iv.repository, "pi_c2")
    monkeypatch.setattr(serving, "reserved_assessment_items", lambda repository: frozenset(), raising=False)
    record = _plan(iv, DUE_DAY)
    assert "pi_c2" not in _planned(record)
    (miss,) = [row for row in record.split["checks_unplanned"] if row["commitment_id"] == commitment]
    assert miss["reason"] == "assessment_reservation"
    assert miss["refusal"][0]["reason"] == "reserved_assessment_surface"
    named = {}
    for row in _plan_block_rows(iv.repository):
        for key, items in (row["exclusions_json"].get("named") or {}).items():
            named.setdefault(key, set()).update(items)
    assert "pi_c2" in named.get("assessment_reservation", set())


def test_f16_an_unreserved_check_is_still_planned_under_the_staged_policy(tmp_path):
    """Control: the staged path still plans a due check first."""

    iv = _staged_vault(tmp_path)
    iv.choose("practice_item", "pi_c2", "check_once", NOW)
    record = _plan(iv, DUE_DAY)
    assert "pi_c2" in _planned(record)
    assert [row["practice_item_id"] for row in record.split["checks"]] == ["pi_c2"]


@pytest.mark.parametrize("staged", [True, False], ids=["staged", "dl1_pair"])
def test_f16_a_reservation_taken_after_planning_displaces_the_planned_check(tmp_path, staged):
    """Reconciliation reads the reservation too: a check planned before its
    item was reserved is displaced at the next step, not served."""

    from learnloop.daily_plan.engine import advance

    iv = _staged_vault(tmp_path)
    iv.choose("practice_item", "pi_c2", "check_once", NOW)
    env = _env(iv, DUE_DAY, staged=staged)
    record = build_plan(env, kind="normal", budget=15.0, remembered=15, minutes_source="chip")
    assert "pi_c2" in _planned(record)
    _reserve(iv.vault, iv.repository, "pi_c2")
    env.clock.advance(2)
    record, _step = advance(env, serve=False)
    item = next(item for item in record.items() if item.practice_item_id == "pi_c2")
    assert item.displaced_reason == "intent_check_reserved"


# -- F16 contract: the round-4 property test with random reservations ------------------------------

BUILDS = 6
ALLOWED_MISSES = {"plan_minutes_exhausted", "assessment_reservation"}


def _random_vault(root, rng: random.Random):
    target = [(f"pi_t{index}", float(rng.choice([1.0, 2.0, 3.0, 6.0]))) for index in range(rng.randint(1, 3))]
    los = {"lo_t": target}
    for lo_index in range(rng.randint(1, 3)):
        los[f"lo_f{lo_index}"] = [
            (f"pi_f{lo_index}_{index}", float(rng.choice([1.0, 2.0, 4.0]))) for index in range(rng.randint(1, 3))
        ]
    paths = create_daily_plan_vault(root, learning_objects=los, version=INTENT_ALGORITHM_VERSION)
    append_config_toml(paths.root, STAGED)
    for item_id, _ in target:
        if rng.random() < 0.3:
            _as_teach_back(paths.root, item_id)
    vault = load_vault(paths.root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    reviewed = NOW - timedelta(days=10)
    for lo_id, items in los.items():
        for item_id, _minutes in items:
            record_attempt(repository, item_id, lo_id, reviewed)
            seed_due(repository, item_id, due=NOW - timedelta(days=rng.randint(0, 5)), last=reviewed)
        repository.upsert_mastery_state(
            MasteryState(
                learning_object_id=lo_id, logit_mean=0.0, logit_variance=1.0, evidence_count=1,
                last_evidence_at=iso(reviewed), algorithm_version=vault.config.algorithms.algorithm_version,
                updated_at=iso(reviewed),
            )
        )
    scope = (Scope("practice_item", rng.choice(target)[0]) if rng.random() < 0.5
             else Scope("learning_object", "lo_t"))
    commitment = apply_choice(vault, repository, scope, "check_once", clock=FrozenClock(NOW)).commitment_id
    all_items = [item_id for items in los.values() for item_id, _ in items]
    reserved = {item_id for item_id in all_items if rng.random() < 0.35}
    if scope.kind == "practice_item" and rng.random() < 0.5:
        reserved.add(scope.id)  # the check's only candidate
    for item_id in sorted(reserved):
        _reserve(vault, repository, item_id)
    return vault, repository, commitment, {item_id for item_id, _ in target}, reserved


@pytest.mark.parametrize("seed", range(16))
def test_f16_contract_no_reserved_item_is_ever_planned_and_every_miss_is_named(tmp_path, seed, monkeypatch):
    """R2's contract with random reservations, through the staged policy: no
    build ever plans a reserved item; the commitment's item is planned within
    ``BUILDS`` builds, or every build that missed it recorded minutes
    exhausted or the reservation."""

    rng = random.Random(seed)
    vault, repository, commitment, targets, reserved = _random_vault(tmp_path / "vault", rng)
    _never_worth_its_minutes(monkeypatch)
    misses = []
    served = False
    for build in range(BUILDS):
        at = DUE_DAY + timedelta(days=build, hours=1)
        clock = MovableClock(at)
        env = PlanEnv(vault=vault, repository=repository, clock=clock, policy=policy_for(vault, repository, clock=clock))
        budget = float(rng.choice([1, 2, 4, 8, 15, 30]))
        record = build_plan(env, kind="normal", budget=budget, remembered=int(budget), minutes_source="chip")
        planned = _planned(record)
        assert not planned & reserved, (seed, build, sorted(planned & reserved))
        if planned & targets and not served:
            served = True
        if not served:
            misses.append((build, list(record.split.get("checks_unplanned") or [])))
    if served:
        return
    for build, unplanned in misses:
        reasons = {row["reason"] for row in unplanned if row.get("commitment_id") == commitment}
        assert reasons and reasons <= ALLOWED_MISSES, (seed, build, unplanned)


# -- F17: moving a deadline after a depth change ---------------------------------------------------


def test_f17_moving_a_deadline_after_a_depth_change_updates_the_goal_target(tmp_path):
    iv = make_intent_vault(tmp_path / "vault")
    scope = Scope("learning_object", "lo_a")
    targets = iv.vault.config.intent.recall_targets
    iv.choose("learning_object", "lo_a", "keep", NOW)
    first = set_deadline(iv.vault, iv.repository, scope, "2026-12-01", clock=FrozenClock(NOW))
    iv.reload()
    (goal,) = [goal for goal in iv.vault.goals if goal.id == first["goal_id"]]
    assert goal.target_recall == pytest.approx(targets["remember_key_ideas"])
    iv.choose("learning_object", "lo_a", "master", NOW + timedelta(minutes=1))
    moved = set_deadline(iv.vault, iv.repository, scope, "2026-12-15", clock=FrozenClock(NOW + timedelta(minutes=2)))
    iv.reload()
    assert moved["goal_id"] == first["goal_id"] and moved["created"] is False
    (goal,) = [goal for goal in iv.vault.goals if goal.id == first["goal_id"]]
    assert goal.due_at == "2026-12-15T23:59:59Z"
    assert goal.target_recall == pytest.approx(targets["master_tasks_like_these"]) == pytest.approx(0.92)


def test_f17_moving_a_deadline_at_the_same_depth_keeps_its_target(tmp_path):
    """Control."""

    iv = make_intent_vault(tmp_path / "vault")
    scope = Scope("learning_object", "lo_a")
    iv.choose("learning_object", "lo_a", "keep", NOW)
    first = set_deadline(iv.vault, iv.repository, scope, "2026-12-01", clock=FrozenClock(NOW))
    iv.reload()
    set_deadline(iv.vault, iv.repository, scope, "2026-12-15", clock=FrozenClock(NOW + timedelta(minutes=1)))
    iv.reload()
    (goal,) = [goal for goal in iv.vault.goals if goal.id == first["goal_id"]]
    assert goal.target_recall == pytest.approx(iv.vault.config.intent.recall_targets["remember_key_ideas"])
