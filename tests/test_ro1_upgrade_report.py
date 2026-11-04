"""Router objective RO1 §5.5: the upgrade's report, from the playbook's shadow rebuild on a copy.

A synthetic mvp-0.45 vault with a few weeks of mixed reviews; ``shadow_rebuild`` with the candidate at
mvp-0.46 reports the item due-date shifts (the old factor's range: each new interval is the old one
divided by its factor, so the ratio lies in [1/f_max, 1/f_min]), and ``schedule_effects`` the queue due
at an instant and admission's projected review load, before and after. The live database is unchanged.
Fakes only; no model call. The same builder produces the numbers recorded in docs/reviews/router-ro1.md.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from functools import partial

import pytest

from learnloop.algorithm_versions import FOLLOWUP_SERVE_ALGORITHM_VERSION, INTERVAL_FACTOR_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock, parse_utc
from learnloop.config.schema import LearnLoopConfig
from learnloop.daily_plan.admission import ReviewItem, projected_review_load
from learnloop.daily_plan.engine import PlanEnv, _estimator, _review_items, intent_view
from learnloop.daily_plan.schedule_effects import ServingSchedule, schedule_effects, serving_schedule
from learnloop.db.repositories import Repository
from learnloop.substrate.shadow_rebuild import ShadowRebuildError, _learner_state_snapshot, shadow_rebuild
from learnloop.vault.loader import load_vault

from tests.daily_plan_fakes import MovableClock, iso, record_attempt, seed_due
from tests.helpers import NOW, PLACEMENT_LOS, create_placement_vault
from tests.intent_fakes import NOW as INTENT_NOW
from tests.intent_fakes import OURS, make_intent_vault

TAG = INTERVAL_FACTOR_ALGORITHM_VERSION
PREDECESSOR = FOLLOWUP_SERVE_ALGORITHM_VERSION
ITEMS = sorted(item for _concept, _prereqs, items in PLACEMENT_LOS.values() for item in items)
#: Score pattern per round (points out of 4), cycling over the items: hits, partials and misses.
POINTS = (4, 3, 1, 4, 0, 2, 4, 4)
ROUNDS = 5
DAYS_BETWEEN = 6


def build_history(root):
    """A mvp-0.45 vault where every placement item was reviewed ``ROUNDS`` times, ``DAYS_BETWEEN`` days apart."""

    paths = create_placement_vault(root, version=PREDECESSOR)
    repository = Repository(paths.sqlite_path)
    for round_index in range(ROUNDS):
        for index, item_id in enumerate(ITEMS):
            observed = NOW + timedelta(days=round_index * DAYS_BETWEEN, minutes=index)
            complete_self_graded_attempt(
                load_vault(paths.root), repository,
                AttemptDraft(practice_item_id=item_id, learner_answer_md="An answer."),
                SelfGradeInput(criterion_points={"correctness": POINTS[(index + round_index) % len(POINTS)]},
                               confidence=4),
                clock=FrozenClock(observed),
            )
    return paths


#: The day after the last round: when the upgrade would run.
AS_OF = NOW + timedelta(days=(ROUNDS - 1) * DAYS_BETWEEN + 1)


def _effects(result, *, as_of, horizon_days: int) -> dict:
    return schedule_effects(result.schedule_before, result.schedule_after, as_of=as_of, horizon_days=horizon_days,
                            serving_before=result.observed_before, serving_after=result.observed_after)


def upgrade_report(paths) -> dict:
    vault = load_vault(paths.root)
    result = shadow_rebuild(vault, assignments=(f"algorithms.algorithm_version={TAG}",),
                            observe=partial(serving_schedule, as_of=AS_OF))
    effects = _effects(result, as_of=AS_OF, horizon_days=int(vault.config.plan.load_horizon_days))
    return {"shadow": result.as_dict(), "effects": effects, "live_unchanged": result.live_database_unchanged}


def _unstamped(row):
    return None if row is None else {k: v for k, v in row.items() if k != "algorithm_version"}


def only_the_version_stamp_moved(diff, families, same) -> bool:
    """Every change is the version stamp, or one a same-version rebuild shows too (``same``: the
    vault's own replay-against-live difference, which the tag does not cause)."""

    for family in families:
        known = {json.dumps(c["key"], sort_keys=True): (c["change"], _unstamped(c["after"]))
                 for c in same[family]["changes"]}
        for change in diff[family]["changes"]:
            if change["change"] == "changed" and _unstamped(change["before"]) == _unstamped(change["after"]):
                continue
            if known.get(json.dumps(change["key"], sort_keys=True)) == (change["change"], _unstamped(change["after"])):
                continue
            return False
    return True


def test_the_shadow_rebuild_reports_the_upgrades_schedule_effects(tmp_path):
    paths = build_history(tmp_path / "vault")
    report = upgrade_report(paths)
    assert report["live_unchanged"]
    assert report["shadow"]["candidate_algorithm_version"] == TAG
    diff = report["shadow"]["learner_state_diff"]
    # Mastery and facet rows move only by the version stamp they carry; the schedule moves for real.
    same = shadow_rebuild(load_vault(paths.root)).learner_state_diff
    assert same["summary"]["schedule"] == 0
    assert only_the_version_stamp_moved(diff, ("mastery", "facet"), same)
    assert diff["summary"]["schedule"] > 0
    items = report["effects"]["practice_item_state"]
    assert items["rows"] == len(ITEMS) and items["due_dates_moved"] > 0
    surprise = LearnLoopConfig().scheduler.surprise
    ratio = items["interval_ratio"]
    assert 1 / surprise.f_max - 1e-3 <= ratio["min"] <= ratio["max"] <= 1 / surprise.f_min + 1e-3
    assert items["earlier"] + items["later"] == items["due_dates_moved"]
    assert set(items["queue_due"]) == {"before", "after", "newly_due", "no_longer_due"}
    assert items["queue_due"]["after"] - items["queue_due"]["before"] == (
        items["queue_due"]["newly_due"] - items["queue_due"]["no_longer_due"])
    assert set(items["review_load_per_day"]) == {"before", "after"}
    # Activity cards: none in this vault (the schedule is the items').
    assert report["effects"]["activity_card_state"]["rows"] == 0
    json.dumps(report["effects"])


def test_with_the_factor_kept_the_shadow_reports_no_schedule_change(tmp_path):
    paths = build_history(tmp_path / "vault")
    vault = load_vault(paths.root)
    result = shadow_rebuild(vault, assignments=(f"algorithms.algorithm_version={TAG}",
                                                "scheduler.surprise.remove_interval_factor=false"),
                            observe=partial(serving_schedule, as_of=AS_OF))
    same = shadow_rebuild(vault).learner_state_diff
    assert only_the_version_stamp_moved(result.learner_state_diff, ("mastery", "facet", "schedule"), same)
    effects = _effects(result, as_of=AS_OF, horizon_days=14)
    assert effects["practice_item_state"]["due_dates_moved"] == 0
    load = effects["practice_item_state"]["review_load_per_day"]
    assert load["before"] == load["after"]
    assert effects["practice_item_state"]["queue_due"]["newly_due"] == 0


# --- codex review F2: the interval runs from the review that set the due date -----------------------

MAY = datetime(2026, 5, 1, 9, 0, tzinfo=UTC)


def _row(due: datetime, last: datetime) -> dict:
    return {"projection": "practice_item_state", "practice_item_id": "pi_x", "due_at": iso(due),
            "last_attempt_at": iso(last), "stability": 5.0, "active": 1}


def test_a_primed_retry_after_the_review_is_not_the_intervals_anchor():
    """F2's case: a review on May 1 set May 11; a primed retry on May 10 moved ``last_attempt_at`` only;
    RO1 moves the due date to May 16. The interval went from 10 to 15 days: 1.5, not 6/1."""

    key = ("practice_item_state", "pi_x")
    before = {key: _row(MAY + timedelta(days=10), MAY + timedelta(days=9))}
    after = {key: _row(MAY + timedelta(days=15), MAY + timedelta(days=9))}
    anchors = {"pi_x": iso(MAY)}
    serving = lambda due: ServingSchedule(  # noqa: E731
        population={"pi_x": ReviewItem("pi_x", iso(due), iso(MAY), 1.0)}, anchors=anchors)
    as_of = MAY + timedelta(days=9, hours=12)
    effects = schedule_effects(before, after, as_of=as_of, horizon_days=14,
                               serving_before=serving(MAY + timedelta(days=10)),
                               serving_after=serving(MAY + timedelta(days=15)))
    items = effects["practice_item_state"]
    assert items["interval_ratio"] == {"min": 1.5, "median": 1.5, "max": 1.5}
    # The load is admission's from serving's own anchor: ceil(14/10) = 2 reviews, then ceil(14/15) = 1.
    assert items["review_load_per_day"] == {"before": round(2 / 14, 4), "after": round(1 / 14, 4)}


def test_serving_reads_the_anchor_past_a_primed_retry_and_a_held_grade(tmp_path, monkeypatch):
    import learnloop.held_grades as held_grades

    iv = make_intent_vault(tmp_path / "vault")
    reviewed = INTENT_NOW - timedelta(days=10)
    # A primed retry on pi_c1 two days ago (its state's last_attempt_at moves, the schedule does not).
    retry = record_attempt(iv.repository, "pi_c1", "lo_c", INTENT_NOW - timedelta(days=2))
    with iv.repository.connection() as connection:
        connection.execute("UPDATE practice_attempts SET primed = 1 WHERE id = ?", (retry,))
        connection.commit()
    seed_due(iv.repository, "pi_c1", due=INTENT_NOW - timedelta(days=1), last=INTENT_NOW - timedelta(days=2))
    # An eligible review on pi_c2 three days ago whose grade is held for review: it wrote no schedule.
    held = record_attempt(iv.repository, "pi_c2", "lo_c", INTENT_NOW - timedelta(days=3))
    seed_due(iv.repository, "pi_c2", due=INTENT_NOW - timedelta(days=1), last=INTENT_NOW - timedelta(days=3))
    real = held_grades.held_for_review_attempts
    monkeypatch.setattr(held_grades, "held_for_review_attempts",
                        lambda connection, ids=None: frozenset(real(connection, ids)) | {held})
    # A commitment, so serving's intent view is live and admission reads the anchor.
    iv.choose("learning_object", "lo_a", "learn", INTENT_NOW - timedelta(days=1))
    view = serving_schedule(iv.vault, iv.repository, as_of=INTENT_NOW)
    assert view.anchors["pi_c1"] == iso(reviewed) and view.anchors["pi_c2"] == iso(reviewed)
    assert view.population["pi_c1"].last_review_at == iso(reviewed)
    assert view.population["pi_c2"].last_review_at == iso(reviewed)


# --- codex review F3: the queue and the load are serving's own --------------------------------------

def _plans_own(iv, at):
    env = PlanEnv(vault=iv.vault, repository=iv.repository, clock=MovableClock(at))
    return {item.practice_item_id: (item.due_at, item.last_review_at)
            for item in _review_items(env, _estimator(env), intent_view(env))}


def test_the_report_counts_the_queue_and_load_admission_counts(tmp_path):
    """Inactive, paused, waiting-check and non-default-retention items, as serving reads them."""

    iv = make_intent_vault(tmp_path / "vault")
    at = INTENT_NOW + timedelta(minutes=5)
    before_view = serving_schedule(iv.vault, iv.repository, as_of=at)
    before = _learner_state_snapshot(iv.repository)["schedule"]
    assert set(before_view.population) == OURS
    iv.choose("learning_object", "lo_a", "pause", INTENT_NOW)              # excluded
    iv.choose("practice_item", "pi_b1", "check_once", INTENT_NOW)          # a check not yet due: withheld
    iv.choose("learning_object", "lo_c", "light_touch", INTENT_NOW)        # recall target 0.80: due later
    iv.repository.upsert_practice_item_state("pi_c2", difficulty=5.0, stability=5.0,
                                             due_at=iso(INTENT_NOW - timedelta(days=1)),
                                             last_attempt_at=iso(INTENT_NOW - timedelta(days=10)), active=False)
    after_view = serving_schedule(iv.vault, iv.repository, as_of=at)
    after = _learner_state_snapshot(iv.repository)["schedule"]
    # The report's population is the plan's own, item for item: due dates and anchors.
    assert {k: (v.due_at, v.last_review_at) for k, v in after_view.population.items()} == _plans_own(iv, at)
    assert set(after_view.population) == {"pi_c1"}
    stored = after[("practice_item_state", "pi_c1")]["due_at"]
    assert parse_utc(after_view.population["pi_c1"].due_at) > parse_utc(stored)
    effects = schedule_effects(before, after, as_of=at, horizon_days=14,
                               serving_before=before_view, serving_after=after_view)
    items = effects["practice_item_state"]
    # Every stored due date is still past, so a stored-date count would say five before and five after.
    assert all(parse_utc(row["due_at"]) <= at for key, row in after.items() if key[1] in OURS)
    expected_after = sum(1 for item in after_view.population.values() if parse_utc(item.due_at) <= at)
    assert items["queue_due"]["before"] == len(OURS)
    assert items["queue_due"]["after"] == expected_after < len(OURS)
    assert items["queue_due"]["no_longer_due"] == len(OURS) - expected_after
    assert items["review_load_per_day"]["after"] == round(projected_review_load(
        [ReviewItem(k, due, last, 1.0) for k, (due, last) in _plans_own(iv, at).items()],
        now=at, horizon_days=14), 4)
    assert "queue_due" not in effects["activity_card_state"]


def test_the_observer_reads_the_live_database_read_only_with_commitments(tmp_path):
    iv = make_intent_vault(tmp_path / "vault")
    iv.choose("practice_item", "pi_b1", "check_once", INTENT_NOW - timedelta(days=9))   # due: the check gate runs
    iv.choose("learning_object", "lo_c", "keep", INTENT_NOW - timedelta(days=9))
    at = INTENT_NOW + timedelta(minutes=5)
    result = shadow_rebuild(load_vault(iv.root), observe=partial(serving_schedule, as_of=at))
    assert result.live_database_unchanged
    assert isinstance(result.observed_before, ServingSchedule) and isinstance(result.observed_after, ServingSchedule)
    assert {k: (v.due_at, v.last_review_at) for k, v in result.observed_before.population.items()} == (
        _plans_own(iv, at))


def test_an_observer_failure_is_a_shadow_failure(tmp_path):
    paths = build_history(tmp_path / "vault")

    def broken(_vault, _repository):
        raise RuntimeError("no read")

    with pytest.raises(ShadowRebuildError, match="observer failed on the live database"):
        shadow_rebuild(load_vault(paths.root), observe=broken)
