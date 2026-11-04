"""FG1 on the shape real vaults have, which the joint fixture didn't: a blind vault with a live
diagnosis job, whose factor opens through ``_open_repair_factor`` and whose items carry task features.
Each test here failed on a real copy of the owner's vault before it failed here.
"""

from __future__ import annotations

from learnloop.diagnosis.causal_attribution import OPEN_SET_CAUSE_ID
from learnloop.db.stores import followup_serve as store
from learnloop.followup_serve import workflow as wf

from tests.followup_serve_helpers import (
    LIVE_ITEM,
    OFF,
    TAG,
    TASK_FEATURES,
    AuthorFake,
    BlindRivalClient,
    author_clients,
    live_miss,
    live_shape_vault,
    run_jobs,
)


def _reasons(repository, workflow_id):
    with repository.connection() as connection:
        return [event["reason"] for event in store.workflow_events(connection, workflow_id)]


def _stored_refs(repository, factor_id):
    import json

    with repository.connection() as connection:
        return json.loads(connection.execute(
            "SELECT candidate_causes_json FROM unresolved_cause_factors WHERE id = ?", (factor_id,)).fetchone()[0])


def _has_arm(refs):
    return any(ref.get("open_set") or ref.get("hypothesis_id") == OPEN_SET_CAUSE_ID for ref in refs)


def test_h_other_a_live_diagnosis_leaves_a_factor_without_its_arm_and_the_lane_restores_it(tmp_path):
    paths, vault, repository = live_shape_vault(tmp_path, task_features=False)
    _result, outcome = live_miss(vault, repository, BlindRivalClient())
    fake = AuthorFake()
    run_jobs(vault, repository, clients=author_clients(fake))
    row = wf.get(repository, outcome.workflow_id)
    assert row["lane"] == wf.LANE_PROBE and row["factor_id"]
    assert "factor_not_probeable" not in _reasons(repository, outcome.workflow_id)
    assert fake.calls == 1
    assert row["state"] == wf.READY
    assert _has_arm(_stored_refs(repository, row["factor_id"]))


def _live_factor(tmp_path, version):
    paths, vault, repository = live_shape_vault(tmp_path, version=version, task_features=False)
    client = BlindRivalClient()
    client.divergent = True
    result, _outcome = live_miss(vault, repository, client)
    factors = repository.unresolved_cause_factors_for_attempt(result.attempt_id)
    assert factors
    return vault, repository, str(factors[0]["id"])


def test_h_other_below_the_tag_the_quick_checks_commissioning_still_fails_as_it_did(tmp_path):
    """The predecessor's path has the same defect, and below mvp-0.45 it stays exactly as it was."""

    from learnloop.diagnosis.causal_probe_commissioning import commission_probe_instrument

    vault, repository, factor_id = _live_factor(tmp_path, "mvp-0.44")
    assert not _has_arm(_stored_refs(repository, factor_id))
    assert commission_probe_instrument(vault, repository, factor_id=factor_id)["outcome"] == "factor_not_probeable"


def test_h_other_at_the_tag_the_quick_checks_commissioning_gets_past_the_arm(tmp_path):
    from learnloop.diagnosis.causal_probe_commissioning import commission_probe_instrument

    vault, repository, factor_id = _live_factor(tmp_path, TAG)
    assert _has_arm(_stored_refs(repository, factor_id))
    assert commission_probe_instrument(vault, repository, factor_id=factor_id)["outcome"] != "factor_not_probeable"


def test_h_other_with_the_switch_off_it_stays_as_mvp_0_44(tmp_path):
    vault, repository, factor_id = _live_factor_off(tmp_path)
    assert not _has_arm(_stored_refs(repository, factor_id))


def _live_factor_off(tmp_path):
    paths, vault, repository = live_shape_vault(tmp_path, config=OFF, task_features=False)
    result, _outcome = live_miss(vault, repository, BlindRivalClient())
    factors = repository.unresolved_cause_factors_for_attempt(result.attempt_id)
    return vault, repository, str(factors[0]["id"])


def test_h_other_a_factor_that_lost_its_arm_before_the_tag_gets_it_back_on_the_lane(tmp_path):
    vault, repository, factor_id = _live_factor(tmp_path, TAG)
    row = repository.unresolved_cause_factor(factor_id)
    concrete = [ref for ref in _stored_refs(repository, factor_id) if not ref.get("open_set")]
    repository.set_unresolved_cause_hypothesis_refs(factor_id, concrete)  # an older copy's row
    assert not _has_arm(_stored_refs(repository, factor_id)) and row["status"] == "open"
    fake = AuthorFake()
    run_jobs(vault, repository, clients=author_clients(fake))
    assert fake.calls == 1
    assert _has_arm(_stored_refs(repository, factor_id))


def test_audit_an_item_with_task_features_passes_the_audit_and_reaches_ready(tmp_path):
    paths, vault, repository = live_shape_vault(tmp_path)
    assert vault.practice_items[LIVE_ITEM].task_features == TASK_FEATURES
    _result, outcome = live_miss(vault, repository, BlindRivalClient())
    fake = AuthorFake()
    run_jobs(vault, repository, clients=author_clients(fake))
    row = wf.get(repository, outcome.workflow_id)
    assert "manipulation_audit_rejected" not in _reasons(repository, outcome.workflow_id)
    assert fake.calls == 1 and row["state"] == wf.READY


def test_audit_task_features_are_declared_as_the_systems_and_nothing_undeclared_slips_through(tmp_path):
    import json

    from learnloop.followup_run.authoring import AUTHOR_AXES

    paths, vault, repository = live_shape_vault(tmp_path)
    live_miss(vault, repository, BlindRivalClient())
    run_jobs(vault, repository, clients=author_clients(AuthorFake()))
    with repository.connection() as connection:
        contract, diff, status = connection.execute(
            "SELECT contract_json, structural_diff_json, status FROM probe_manipulation_audits ORDER BY rowid DESC"
        ).fetchone()
    contract, diff = json.loads(contract), json.loads(diff)
    assert status == "passed" and diff["undeclared_differences"] == []
    # Only what this item has: a feature it doesn't carry isn't declared to have changed.
    assert set(TASK_FEATURES) <= set(contract["incidental_changes"])
    assert not set(TASK_FEATURES) & AUTHOR_AXES
    assert "unrelated_feature" not in contract["incidental_changes"]


def test_audit_an_item_with_no_task_features_declares_none(tmp_path):
    import json

    paths, vault, repository = live_shape_vault(tmp_path, task_features=False)
    live_miss(vault, repository, BlindRivalClient())
    run_jobs(vault, repository, clients=author_clients(AuthorFake()))
    with repository.connection() as connection:
        contract = json.loads(connection.execute(
            "SELECT contract_json FROM probe_manipulation_audits ORDER BY rowid DESC").fetchone()[0])
    assert not set(TASK_FEATURES) & set(contract["incidental_changes"])
