"""Router objective RO1 §5.4: a learner's misconception pick is not validated evidence at mvp-0.46.

``record_unresolved_cause_self_report`` resolves the factor with ``resolution_observation_ids =
[learner_report:<id>]``. Below the tag (or with ``[router_objective] self_report_not_validated`` off) the
diagnoser's history counts that id as ``validated_evidence_count``; at the tag it does not. The factor's
status and its resolution ids are unchanged, and the diagnoser still sees the factor (the learner's
attributed opinion). A probe's discriminating observation (``cdo:*``) still counts. Fakes only.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.algorithm_versions import FOLLOWUP_SERVE_ALGORITHM_VERSION, INTERVAL_FACTOR_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.causal_attribution import record_unresolved_cause_self_report
from learnloop.diagnosis.split.history import AttemptRef, VaultHistoryStore
from learnloop.router_objective_switches import validated_resolution_ids
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.helpers import NOW, append_config_toml, set_algorithm_version
from tests.test_km2_write_path import build_mvp07_vault

TAG = INTERVAL_FACTOR_ALGORITHM_VERSION
PREDECESSOR = FOLLOWUP_SERVE_ALGORITHM_VERSION
OFF = "[router_objective]\nself_report_not_validated = false\n"


@pytest.fixture(scope="module")
def picked(tmp_path_factory):
    """A miss with an unresolved factor, resolved by the learner's pick (written at mvp-0.7)."""

    root = tmp_path_factory.mktemp("picked") / "vault"
    paths = build_mvp07_vault(root)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    result = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id="pi_svd_ambiguous_001", learner_answer_md="An answer."),
        SelfGradeInput(criterion_points={"whole_item": 0}, fatal_errors=[], confidence=4),
        clock=clock,
    )
    factor = repository.unresolved_cause_factors_for_attempt(result.attempt_id)[0]
    report = record_unresolved_cause_self_report(
        vault, repository, factor_id=factor["id"], response="believed_candidate", candidate_index=0, clock=clock)
    assert report["resolved"] is True
    return paths, factor["id"], result.attempt_id


def _factor_record(paths, factor_id: str, version: str, toml: str | None, tmp_path):
    from learnloop.db.copies import copy_tree_with_databases

    root = tmp_path / version.replace(".", "_")
    copy_tree_with_databases(paths.root, root)
    copied = VaultPaths(root, paths.config)
    set_algorithm_version(copied, version)
    if toml:
        append_config_toml(root, toml)
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")
    store = VaultHistoryStore(vault, repository)
    later = AttemptRef("~", (NOW + timedelta(days=1)).isoformat().replace("+00:00", "Z"))
    records = [record for record in store.hypotheses_before(later, list(vault.learning_objects))
               if record.id == factor_id]
    assert len(records) == 1
    return records[0], repository.unresolved_cause_factor(factor_id)


@pytest.mark.parametrize("version, toml, counted", [
    (TAG, None, 0), (TAG, OFF, 1), (PREDECESSOR, None, 1)], ids=["tag", "off", "below"])
def test_a_pick_counts_as_validated_evidence_only_below_the_tag_or_switched_off(
        picked, tmp_path, version, toml, counted):
    paths, factor_id, _attempt_id = picked
    record, factor = _factor_record(paths, factor_id, version, toml, tmp_path)
    assert record.kind == "unresolved_factor"
    assert record.validated_evidence_count == counted
    # The factor itself is unchanged: still resolved, by the learner's report.
    assert record.status == "resolved" == factor["status"]
    [observation] = factor["resolution_observation_ids"]
    assert observation.startswith("learner_report:")


def test_a_probes_observation_still_counts_and_only_reports_are_dropped(tmp_path):
    from types import SimpleNamespace

    def config(version, flag=True):
        return SimpleNamespace(algorithms=SimpleNamespace(algorithm_version=version),
                               router_objective=SimpleNamespace(self_report_not_validated=flag))

    ids = ["learner_report:01J", "cdo:abc", "learner_report:01K"]
    assert validated_resolution_ids(ids, config(TAG)) == ["cdo:abc"]
    assert validated_resolution_ids(ids, config(TAG, False)) == ids
    assert validated_resolution_ids(ids, config(PREDECESSOR)) == ids
    assert validated_resolution_ids(None, config(TAG)) == []
