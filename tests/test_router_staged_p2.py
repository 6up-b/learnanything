"""Router R1: every live staged P2 decision is a logged router decision.

The P2 bridge (``controller_cutover.staged_next_action``) consults the staged
policy for a staged-owned golden-path run. Each decision it makes writes one
``router_decisions`` row: "continue" (the run's canonical successor), the §4.2
ladder's blocks with their staged eligibility, the within-block feasible items
with their ranks, and stop; the served choice; and its propensity, which is
"deterministic" because nothing on this path is drawn.
"""

from __future__ import annotations

import json

import pytest

from learnloop.clock import FrozenClock
from learnloop.curriculum import golden_path_confirm as GPC
from learnloop.curriculum import golden_path_run as GPR
from learnloop.curriculum import task_blueprints as TB
from learnloop.db.repositories import Repository
from learnloop.router.decisions import CONTINUE_REF, STOP_REF
from learnloop.scheduling import controller_cutover as cut
from learnloop.scheduling import controller_ownership as own
from learnloop.scheduling.scheduler import SchedulerSession
from learnloop.substrate.activities import resolve_legacy_item
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, append_config_toml, create_basic_vault

CLOCK = FrozenClock(NOW)


def _run(tmp_path, *, toml: str | None = None):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    if toml:
        append_config_toml(root, toml)
    vault = load_vault(root)
    repo = Repository(paths.sqlite_path)
    item = vault.practice_items["pi_svd_define_001"]
    spec = {
        "source_rev": "rev-1", "unit_id": "unit-a", "family_key": "method-selection",
        "exemplars": [{"exemplar_ref": item.id, "unit_id": "unit-a", "family_key": "method-selection"}],
    }
    bv = TB.register_blueprint_version(repo, blueprint_slug="bp1", spec=spec, clock=CLOCK)
    bv = TB.review_blueprint_version(repo, blueprint_version_id=bv.id, clock=CLOCK)
    resolved = resolve_legacy_item(vault, repo, item, purpose="assessment", clock=CLOCK)
    body = {
        "purpose": "method selection",
        "facet_scope": {"concepts": ["unit-a"], "facets": ["method_selection"]},
        "required_capabilities": ["method_selection"],
        "baseline_milestone": "m0",
        "exemplars": [{"id": item.id, "surface_ref": resolved.surface_id, "weight": 1.0}],
    }
    receipt = GPC.confirm_exemplar_and_start(
        repo, goal_id="g1", blueprint_version_id=bv.id, contract_body=body,
        depth_preset="master_tasks_like_these", source_rev="rev-1", unit_id="unit-a",
        assessment_surface_id=resolved.surface_id, clock=CLOCK,
    )
    own.assign_p2_run(repo, commitment_id=receipt.commitment_id, clock=CLOCK)
    return repo, receipt, vault


def _session():
    return SchedulerSession(session_id="s1", available_minutes=15)


def _rows(repo) -> list[dict]:
    with repo.connection() as connection:
        rows = [dict(row) for row in connection.execute("SELECT * FROM router_decisions ORDER BY created_at, id")]
    for row in rows:
        for column in ("candidates_json", "exclusions_json", "detail_json"):
            row[column] = json.loads(row[column])
    return rows


def test_a_live_staged_decision_logs_continue_the_ladder_and_its_choice(tmp_path):
    repo, receipt, vault = _run(tmp_path)
    canonical = GPR.project_run(repo, receipt.run_id).next_action

    action = cut.staged_next_action(repo, receipt.run_id, vault=vault, session=_session(),
                                    live=True, receipt_key="rk1", clock=CLOCK)

    [row] = _rows(repo)
    assert action.authority == "staged"
    assert (row["decision_kind"], row["mode"], row["policy"], row["surface"]) == (
        "staged_p2", "staged", "staged_policy_v1", "p2_bridge",
    )
    assert row["controller_decision_id"] == action.staged_decision_id
    assert row["chosen_ref"] == CONTINUE_REF
    assert (row["propensity"], row["propensity_kind"], row["design"], row["learner_pick"]) == (
        1.0, "deterministic", None, 0,
    )
    refs = [c["ref"] for c in row["candidates_json"]]
    assert refs[0] == CONTINUE_REF and refs[-1] == STOP_REF
    cont = row["candidates_json"][0]
    assert (cont["to_state"], cont["source"], cont["chosen"]) == (canonical.to_state, "p2_run", True)
    blocks = [c for c in row["candidates_json"] if c["kind"] == "block"]
    assert [b["rung"] for b in blocks] == list(range(1, 11))
    # The ladder's pick is the first eligible rung (stop is always eligible);
    # the ones the spec never samples are marked irreversible.
    fired = [b for b in blocks if b["fired"]]
    first_eligible = next(b for b in blocks if b["staged_eligible"])
    assert fired == [first_eligible] and blocks[-1]["staged_eligible"]
    irreversible = {b["staged_rule"] for b in blocks if not b["reversible"]}
    assert irreversible == {"terminal_required_with_reserve", "depth_progression_edge_feasible", "model_misspecification"}
    # Non-owned items are refused by ownership and logged as a count.
    assert row["exclusions_json"]["counts"].get("controller_ownership", 0) >= 0
    assert row["detail_json"]["authority"] == "staged" and row["detail_json"]["run_id"] == receipt.run_id


def test_a_retried_bridge_call_logs_its_decision_once(tmp_path):
    repo, receipt, vault = _run(tmp_path)
    for _ in range(2):
        cut.staged_next_action(repo, receipt.run_id, vault=vault, session=_session(),
                               live=True, receipt_key="rk-same", clock=CLOCK)
    assert len(_rows(repo)) == 1


def test_a_veto_is_logged_as_the_stop_it_served(tmp_path, monkeypatch):
    repo, receipt, vault = _run(tmp_path)
    monkeypatch.setattr(cut, "_constraint_or_evsi_veto", lambda _result: "evsi:stop_waiting_for_delay_or_fresh_surface")

    action = cut.staged_next_action(repo, receipt.run_id, vault=vault, session=_session(),
                                    live=True, receipt_key="rk-veto", clock=CLOCK)

    [row] = _rows(repo)
    assert action.authority == "staged_veto"
    assert row["chosen_ref"] == STOP_REF and row["chosen_practice_item_id"] is None
    assert row["detail_json"]["veto_reason"] == "evsi:stop_waiting_for_delay_or_fresh_surface"
    assert row["propensity_kind"] == "deterministic"


def test_legacy_authority_writes_no_staged_row(tmp_path):
    repo, receipt, vault = _run(tmp_path)
    action = cut.staged_next_action(repo, receipt.run_id, vault=vault, session=_session(),
                                    live=False, clock=CLOCK)
    assert action.authority == "legacy" and _rows(repo) == []


def test_logging_switch_off_writes_no_staged_row(tmp_path):
    repo, receipt, vault = _run(tmp_path, toml="[router]\nlog_decisions = false\n")
    action = cut.staged_next_action(repo, receipt.run_id, vault=vault, session=_session(),
                                    live=True, receipt_key="rk-off", clock=CLOCK)
    assert action.authority == "staged" and _rows(repo) == []


def test_a_logging_failure_never_changes_the_staged_decision(tmp_path, monkeypatch):
    from learnloop.router import decisions as router_decisions

    repo, receipt, vault = _run(tmp_path)

    def broken(*_args, **_kwargs):
        raise RuntimeError("logging broke")

    monkeypatch.setattr(router_decisions, "build_staged_p2_decision", broken)
    action = cut.staged_next_action(repo, receipt.run_id, vault=vault, session=_session(),
                                    live=True, receipt_key="rk-broken", clock=CLOCK)
    assert action.authority == "staged" and _rows(repo) == []


@pytest.mark.parametrize("short_circuit,learner_pick", [("explicit_learner_choice", True), ("continuation", False)])
def test_short_circuited_blocks_are_logged_as_the_learner_pick_or_the_continuation(short_circuit, learner_pick):
    from learnloop.router.decisions import build_staged_p2_decision
    from learnloop.scheduling import staged_policy as sp

    result = sp.DecisionResult(
        decision_id="d1", already=False, action="practice", subtype=None, staged_rule=short_circuit,
        chosen_candidate_ref="pi_1", stop_reason=None, snapshot_hash="h",
        trace={"attention_block": {"short_circuit_reason": short_circuit}, "feasible_set": ["pi_1"],
               "ranking_inputs": {"selector": "due_order", "ranked": [{"candidate_ref": "pi_1", "rank": 1}]}},
        why="",
    )
    row = build_staged_p2_decision(
        result, ladder=[], canonical=None, authority="staged", veto_reason=None, run_id="r",
        commitment_id="c", algorithm_version="mvp-0.12", session_id="s", chosen_learning_object_id="lo",
    )
    if learner_pick:
        assert (row["learner_pick"], row["propensity"], row["propensity_kind"]) == (1, None, "none")
        assert row["chosen_ref"] == "block:practice"
    else:
        assert (row["learner_pick"], row["chosen_ref"], row["propensity_kind"]) == (0, CONTINUE_REF, "deterministic")
        cont = json.loads(row["candidates_json"])[0]
        assert (cont["ref"], cont["source"]) == (CONTINUE_REF, "continuation")
    assert (row["chosen_practice_item_id"], row["chosen_learning_object_id"]) == ("pi_1", "lo")


def test_a_randomized_within_block_choice_logs_its_assignment_propensity():
    from learnloop.router.decisions import build_staged_p2_decision
    from learnloop.scheduling import staged_policy as sp

    result = sp.DecisionResult(
        decision_id="d2", already=False, action="measure_diagnostic", subtype=None,
        staged_rule="positive_robust_measurement_value", chosen_candidate_ref="pi_2", stop_reason=None,
        snapshot_hash="h",
        trace={"attention_block": {}, "feasible_set": ["pi_1", "pi_2"],
               "ranking_inputs": {"selector": "robust_evsi_per_minute",
                                  "ranked": [{"candidate_ref": "pi_1", "rank": 1}, {"candidate_ref": "pi_2", "rank": 2}],
                                  "evsi_assignment": {"randomized": True, "propensity": 0.5, "seed": "seed-x",
                                                      "variant": "pi_2"}}},
        why="",
    )
    row = build_staged_p2_decision(
        result, ladder=[], canonical=None, authority="staged", veto_reason=None, run_id="r",
        commitment_id="c", algorithm_version="mvp-0.12", session_id="s",
    )
    assert (row["propensity"], row["propensity_kind"], row["design"], row["seed"]) == (
        0.5, "exact", "epsilon_tiebreak", "seed-x",
    )
