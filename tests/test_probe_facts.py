"""The probe's facts and hard stops from plain values, with no vault, and the verdict over them."""

from __future__ import annotations

import pytest

from learnloop.diagnosis.causal_probe_coherence import resolve_causal_probe_parameters
from learnloop.diagnosis.probe_facts import (
    HARD_STOP_LEARNER_PREFERENCE,
    HARD_STOP_MACHINE_CHECKS,
    HARD_STOP_SESSION_BUDGET,
    probe_facts,
    probe_verdict,
    settled_by_repair_classes,
)


def facts(**overrides):
    values = dict(
        repair_class_ids=["r:b", None, "r:a", "r:a", ""],
        common_repair_covers=False,
        expected_information_gain=0.5,
        probability_information_changes_repair=0.8,
        probe_burden_minutes=1.5,
        avoided_overteaching_minutes=10.0,
    )
    values.update(overrides)
    return probe_facts(**values)


def test_each_fact_on_a_case_worked_by_hand():
    out = facts()
    assert out.repair_class_ids == ("r:a", "r:b")
    assert out.different_repairs is True and out.common_repair_covers is False
    assert out.action_relevant is True
    assert out.expected_information_gain == 0.5 and out.probability_information_changes_repair == 0.8
    # 10 minutes avoided x 0.8 chance the answer changes the repair x 0.5 of the pairs separated.
    assert out.expected_avoided_overteaching_minutes == pytest.approx(4.0)
    assert out.probe_burden_minutes == 1.5
    assert out.recent_diagnostic_burden == 0 and out.machine_checks_first == ()
    assert out.hard_stops == ()


def test_the_value_terms_are_clipped_and_floored():
    assert facts(probability_information_changes_repair=1.4, expected_information_gain=2.0,
                 avoided_overteaching_minutes=6.0).expected_avoided_overteaching_minutes == 6.0
    assert facts(expected_information_gain=-0.2).expected_avoided_overteaching_minutes == 0.0
    assert facts(avoided_overteaching_minutes=-3.0).expected_avoided_overteaching_minutes == 0.0
    assert facts(probe_burden_minutes=-2.0).probe_burden_minutes == 0.0
    # The gain and the change probability are kept as given; only their product is clipped.
    assert facts(expected_information_gain=1.4).expected_information_gain == 1.4


def test_one_class_or_a_common_cover_is_not_action_relevant():
    one = facts(repair_class_ids=["r:a", "r:a", None])
    assert one.repair_class_ids == ("r:a",) and not one.different_repairs and not one.action_relevant
    covered = facts(common_repair_covers=True)
    assert covered.different_repairs and not covered.action_relevant


def test_pending_machine_checks_are_a_hard_stop():
    out = facts(pending_machine_checks=["mc2", "mc1"])
    assert out.machine_checks_pending and out.machine_checks_first == ("mc2", "mc1")
    assert out.hard_stops == (HARD_STOP_MACHINE_CHECKS,)


@pytest.mark.parametrize("preference", ["decline", "teach_now", "no_more_diagnostics"])
def test_a_refusing_preference_is_a_hard_stop(preference):
    assert facts(learner_preference=preference).hard_stops == (HARD_STOP_LEARNER_PREFERENCE,)


@pytest.mark.parametrize("preference", ["allow", "something_new"])
def test_other_preferences_are_not(preference):
    assert not facts(learner_preference=preference).learner_preference_refuses


def test_a_session_budget_below_the_burden_as_given_is_a_hard_stop():
    assert facts(session_budget_minutes=1.0).hard_stops == (HARD_STOP_SESSION_BUDGET,)
    assert not facts(session_budget_minutes=1.5).session_budget_short
    assert not facts(session_budget_minutes=None).session_budget_short
    # The budget is compared with the burden before the floor: a negative burden fits any budget at or above it.
    assert not facts(session_budget_minutes=-1.0, probe_burden_minutes=-2.0).session_budget_short
    assert facts(session_budget_minutes=-3.0, probe_burden_minutes=-2.0).session_budget_short


def test_every_hard_stop_is_named_in_the_rules_order():
    out = facts(pending_machine_checks=["mc"], learner_preference="decline", session_budget_minutes=0.5)
    assert out.hard_stops == (HARD_STOP_MACHINE_CHECKS, HARD_STOP_LEARNER_PREFERENCE, HARD_STOP_SESSION_BUDGET)


def test_the_repair_classes_alone_settle_two_cases():
    assert settled_by_repair_classes(common_repair_covers=True, different_repairs=True)[0] == "skip_common_repair"
    assert settled_by_repair_classes(common_repair_covers=False, different_repairs=False)[0] == \
        "skip_action_equivalent"
    assert settled_by_repair_classes(common_repair_covers=False, different_repairs=True) is None


def test_the_verdict_reads_the_facts_in_the_ladders_order():
    defaults = resolve_causal_probe_parameters(None)
    assert probe_verdict(facts(), defaults)[0] == "probe_now"
    assert probe_verdict(facts(common_repair_covers=True, pending_machine_checks=["mc"]), defaults)[0] == \
        "skip_common_repair"
    assert probe_verdict(facts(pending_machine_checks=["mc"], learner_preference="decline"), defaults)[0] == \
        "defer_machine_checks"
    assert probe_verdict(facts(recent_diagnostic_burden=2, session_budget_minutes=0.1), defaults)[0] == \
        "defer_recent_burden"
    assert probe_verdict(facts(session_budget_minutes=0.1, expected_information_gain=0.0), defaults)[0] == \
        "defer_session_budget"
    assert probe_verdict(facts(expected_information_gain=0.0), defaults)[0] == "skip_no_discrimination"
    assert probe_verdict(facts(probability_information_changes_repair=0.0), defaults)[0] == "skip_no_action_change"
    # 4.0 expected minutes avoided against a 4.0-minute burden: not more than its burden.
    assert probe_verdict(facts(probe_burden_minutes=4.0), defaults)[0] == "skip_burden_exceeds_value"


def test_a_threshold_is_read_only_when_the_ladder_reaches_it():
    class Unread:
        @property
        def recent_diagnostic_limit(self):
            raise AssertionError("read before its arm")

        def __getitem__(self, key):
            raise AssertionError(f"{key} read before its arm")

    assert probe_verdict(facts(learner_preference="teach_now"), Unread())[0] == "defer_learner_preference"
