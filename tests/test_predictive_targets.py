"""P4 step 3b -- goal-conditioned predictive targets (spec_p4 §6.6, §16.3).

Covers: construction is invariant to candidate/ID insertion order; the candidate is
excluded from its own target set; coverage gaps are reported against available
capabilities; the target-set hash changes only with the pinned contract support.
"""

from __future__ import annotations

from learnloop.services import predictive_targets as PT

_CONTRACT = {
    "exemplars": [
        {"id": "ex_a", "surface_ref": "s_a", "weight": 0.5},
        {"id": "ex_b", "surface_ref": "s_b", "weight": 0.3},
        {"id": "ex_c", "surface_ref": "s_c", "weight": 0.2},
    ],
    "required_capabilities": ["cap_derive", "cap_apply"],
    "task_types": ["compute", "prove"],
    "eligibility": {"held_out": True, "practice": False},
}


def test_construction_is_invariant_to_insertion_order():
    shuffled = {
        **_CONTRACT,
        "exemplars": list(reversed(_CONTRACT["exemplars"])),
        "required_capabilities": ["cap_apply", "cap_derive"],
        "task_types": ["prove", "compute"],
    }
    a = PT.build_target_set(_CONTRACT, contract_version_id="cv1", support_hash="sup1")
    b = PT.build_target_set(shuffled, contract_version_id="cv1", support_hash="sup1")
    assert a.target_set_hash == b.target_set_hash


def test_candidate_is_excluded_from_its_own_target_set():
    ts = PT.build_target_set(_CONTRACT, candidate_id="ex_b")
    ids = {e.id for e in ts.exemplars}
    assert "ex_b" not in ids
    assert ids == {"ex_a", "ex_c"}
    # Excluding by surface_ref also works.
    ts2 = PT.build_target_set(_CONTRACT, candidate_id="s_a")
    assert "ex_a" not in {e.id for e in ts2.exemplars}


def test_excluding_the_candidate_changes_the_hash():
    full = PT.build_target_set(_CONTRACT)
    without = PT.build_target_set(_CONTRACT, candidate_id="ex_a")
    assert full.target_set_hash != without.target_set_hash


def test_coverage_gaps_reported_against_available_capabilities():
    ts = PT.build_target_set(_CONTRACT, available_capabilities=["cap_derive"])
    assert ts.coverage_gaps == ("cap_apply",)
    ts_full = PT.build_target_set(_CONTRACT, available_capabilities=["cap_derive", "cap_apply"])
    assert ts_full.coverage_gaps == ()


def test_held_out_flag_and_weights_are_preserved():
    ts = PT.build_target_set(_CONTRACT)
    assert ts.held_out is True
    assert ts.weight_of("ex_a") == 0.5
    assert ts.required_capabilities == ("cap_apply", "cap_derive")


def test_hash_tracks_the_pinned_support_not_candidate_order():
    a = PT.build_target_set(_CONTRACT, support_hash="sup1")
    b = PT.build_target_set(_CONTRACT, support_hash="sup2")
    # A different pinned support changes the hash; the enumeration order does not.
    assert a.target_set_hash != b.target_set_hash
