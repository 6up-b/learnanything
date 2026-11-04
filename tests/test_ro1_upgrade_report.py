"""Router objective RO1 §5.5: the upgrade's report, from the playbook's shadow rebuild on a copy.

A synthetic mvp-0.45 vault with a few weeks of mixed reviews; ``shadow_rebuild`` with the candidate at
mvp-0.46 reports the item due-date shifts (the old factor's range: each new interval is the old one
divided by its factor, so the ratio lies in [1/f_max, 1/f_min]), and ``schedule_effects`` the queue due
at an instant and admission's projected review load, before and after. The live database is unchanged.
Fakes only; no model call. The same builder produces the numbers recorded in docs/reviews/router-ro1.md.
"""

from __future__ import annotations

import json
from datetime import timedelta

from learnloop.algorithm_versions import FOLLOWUP_SERVE_ALGORITHM_VERSION, INTERVAL_FACTOR_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.config.schema import LearnLoopConfig
from learnloop.daily_plan.schedule_effects import schedule_effects
from learnloop.db.repositories import Repository
from learnloop.substrate.shadow_rebuild import shadow_rebuild
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, PLACEMENT_LOS, create_placement_vault

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


def upgrade_report(paths) -> dict:
    vault = load_vault(paths.root)
    result = shadow_rebuild(vault, assignments=(f"algorithms.algorithm_version={TAG}",))
    effects = schedule_effects(result.schedule_before, result.schedule_after, as_of=AS_OF,
                               horizon_days=int(vault.config.plan.load_horizon_days))
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
                                                "scheduler.surprise.remove_interval_factor=false"))
    same = shadow_rebuild(vault).learner_state_diff
    assert only_the_version_stamp_moved(result.learner_state_diff, ("mastery", "facet", "schedule"), same)
    effects = schedule_effects(result.schedule_before, result.schedule_after, as_of=AS_OF, horizon_days=14)
    assert effects["practice_item_state"]["due_dates_moved"] == 0
    load = effects["practice_item_state"]["review_load_per_day"]
    assert load["before"] == load["after"]
