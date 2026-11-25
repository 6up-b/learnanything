"""The probe router's two lanes on one factor, shared by ``tests/test_probe_router_decision_integrity.py`` and
``tests/test_probe_router_episode_owner.py``: the learner lane's case at the head, and the automatic lane's committed
decision on the factor."""

from __future__ import annotations

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.vault.loader import load_vault

from tests.probe_router_authority_helpers import divergent_factor

HEAD = LATEST_ALGORITHM_VERSION


def learner_case(tmp_path, monkeypatch, *, u: float = 0.05):
    from learnloop.router_objective import probe_coin as PC

    from tests.helpers import append_config_toml
    from tests.probe_router_authority_helpers import sidecar

    case = divergent_factor(tmp_path, version=HEAD)
    append_config_toml(case.root, "\n[router_objective]\nstop_coin = 0.2\n")
    case.vault = load_vault(case.root)
    monkeypatch.setattr(PC, "draw_uniform", lambda _seed: u)
    case.ctx = sidecar(case.root)
    return case


def automatic_decision_on(case, chosen_ref: str) -> str:
    """The automatic lane (FG1) decided this factor's probe after its miss: a probe-lane workflow on the factor that
    names its committed decision."""

    from learnloop.db.stores import followup_serve as store
    from learnloop.router.plan_log import log_followup_decision

    from tests.causal_orchestrator_helpers import LO_ID, NOW_ISO

    with case.repository.atomic(), case.repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "hints_used, correctness, latency_seconds, manual_review, created_at, session_id, primed, evidence_origin)"
            " VALUES ('att_orchestrator', 'pi_svd_define_001', ?, 'short_answer', 'independent_attempt', 0, 0.0, 60, "
            "0, ?, NULL, 0, 'human')", (LO_ID, NOW_ISO))
        store.insert_workflow(connection, {"id": "wf_automatic", "source_attempt_id": "att_orchestrator",
                                           "revision_key": "r1", "learning_object_id": LO_ID, "session_id": None,
                                           "surface": "desktop", "origin": "practice", "lane": "probe",
                                           "feedback_held": 0, "created_at": NOW_ISO})
        decision_id = log_followup_decision(connection, {
            "workflow": {"id": "wf_automatic", "learning_object_id": LO_ID, "source_attempt_id": "att_orchestrator",
                         "factor_id": case.factor},
            "chosen_ref": chosen_ref, "propensity": 0.8, "router_record": {}, "config": case.vault.config,
            "decided_at": NOW_ISO})
        store.update_workflow(connection, "wf_automatic", at=NOW_ISO, factor_id=case.factor, decision_id=decision_id,
                              chosen_ref=chosen_ref)
    return str(decision_id)
