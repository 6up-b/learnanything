"""The repair lane's reads about a possible probe, as one value (``probe_facts.ProbeProposalReads``).

``causal_orchestrator.gather_probe_reads`` makes the reads the repair status always made, in the same order, and
writes nothing; the verdict reads its values unchanged. The value keeps a missing instrument, or a candidate whose
record has no pair to read, apart from the numeric zeros the verdict is given for them.
"""

from __future__ import annotations

import pytest

from learnloop.db.table_roles import TABLE_ROLES
from learnloop.diagnosis import causal_orchestrator as causal
from learnloop.diagnosis.causal_probe_coherence import resolve_causal_probe_parameters
from learnloop.diagnosis.causal_reads import _repair_class_by_hypothesis
from learnloop.diagnosis.probe_facts import (
    CHANNEL_NO_INSTRUMENT,
    CHANNEL_NO_SEPARABILITY_RECORD,
    CHANNEL_SEPARABILITY_COMPUTED,
    ProbeProposalReads,
    channel_status,
    probe_facts,
    probe_verdict,
)
from learnloop.diagnosis.probe_targeting import classify_cause_set

from tests.probe_router_authority_helpers import CLOCK, count, divergent_factor


def _reads(**overrides) -> ProbeProposalReads:
    values = dict(
        repair_class_ids=("repair:method", "repair:recall"), common_repair_covers=False, common_repair_class_id=None,
        pending_machine_check_ids=(), episode_conflict=None, candidates=(), chosen=None, instrument_available=False,
        channel_status=CHANNEL_NO_INSTRUMENT, expected_information_gain=0.0,
        probability_information_changes_repair=0.0, gain_provenance="heuristic_default",
        action_change_provenance="heuristic_default", separable_pairs=0, inseparable_pairs=0, prior_basis=None,
        likelihood_completeness={"complete": False, "reason": "no_instrument"}, probe_burden_minutes=1.5,
        burden_provenance="heuristic_default", avoided_overteaching_minutes=8.0,
        avoided_provenance="heuristic_default", learner_preference="allow", recent_diagnostic_burden=0)
    return ProbeProposalReads(**{**values, **overrides})


def test_the_reads_give_the_facts_the_verdict_computes_from_the_same_values():
    reads = _reads(expected_information_gain=1.0, probability_information_changes_repair=0.5,
                   pending_machine_check_ids=("cmc_1",), learner_preference="decline", recent_diagnostic_burden=3)
    for budget in (None, 1.0, 2.0):
        assert reads.facts(session_budget_minutes=budget) == probe_facts(
            repair_class_ids=["repair:method", "repair:recall"], common_repair_covers=False,
            expected_information_gain=1.0, probability_information_changes_repair=0.5, probe_burden_minutes=1.5,
            avoided_overteaching_minutes=8.0, pending_machine_checks=["cmc_1"], session_budget_minutes=budget,
            learner_preference="decline", recent_diagnostic_burden=3)


def test_a_missing_channel_is_a_status_and_not_the_zero_it_is_priced_at():
    assert channel_status(instrument=False, separability_computed=False) == CHANNEL_NO_INSTRUMENT
    assert channel_status(instrument=True, separability_computed=False) == CHANNEL_NO_SEPARABILITY_RECORD
    assert channel_status(instrument=True, separability_computed=True) == CHANNEL_SEPARABILITY_COMPUTED
    # Both missing states reach the verdict as the same numeric zero; only the status tells them apart.
    missing = _reads()
    unreadable = _reads(chosen={"id": "c1"}, channel_status=CHANNEL_NO_SEPARABILITY_RECORD)
    assert missing.facts() == unreadable.facts()
    assert missing.channel_status != unreadable.channel_status


def _gather(case):
    factor = case.repository.unresolved_cause_factor(case.factor)
    attempt_id = str(factor.get("attempt_id") or "") or None
    targeting = classify_cause_set(list(factor.get("candidate_causes") or []), repository=case.repository,
                                   factor_id=case.factor, attempt_id=attempt_id)
    return causal.gather_probe_reads(
        case.repository, factor_id=case.factor, attempt_id=attempt_id, learning_object_id="lo_svd_definition",
        session_id=None, targeting=targeting, repair_class_by_hypothesis=_repair_class_by_hypothesis(targeting.causes),
        parameters=causal.resolve_orchestrator_parameters(case.repository))


def _rows(repository):
    return {table: count(repository, table) for table in sorted(TABLE_ROLES)}


@pytest.mark.parametrize("instrument", [True, False])
def test_gathering_writes_nothing_and_the_verdict_on_its_facts_is_the_statuss(tmp_path, instrument):
    case = divergent_factor(tmp_path, instrument=instrument)
    before = _rows(case.repository)
    reads = _gather(case)
    assert _rows(case.repository) == before
    status = causal.causal_repair_status(case.vault, case.repository, misconception_id=case.first,
                                         start_repair=False, clock=CLOCK)
    verdict, _reason = probe_verdict(reads.facts(), resolve_causal_probe_parameters(case.repository))
    assert verdict == status.probe_decision
    if instrument:
        assert reads.channel_status == CHANNEL_SEPARABILITY_COMPUTED and reads.instrument_available
        assert str(reads.chosen["id"]) == status.candidate_id and reads.expected_information_gain > 0.0
        assert reads.gain_provenance == "deterministic"
    else:
        assert reads.channel_status == CHANNEL_NO_INSTRUMENT and reads.chosen is None
        assert reads.expected_information_gain == 0.0 and reads.gain_provenance == "heuristic_default"
