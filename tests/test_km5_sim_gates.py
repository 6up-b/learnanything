"""KM5 sim shadow gates.

A planted capability-divergent student (strong retrieval, weak method_selection
on one shared facet):

* residual activation (config-enabled) improves the capability-sliced belief MAE
  vs the pooled shared parent, WITHOUT inflating that parent — checked at >= 8
  trials per surface (the Beta lower-bound gotcha: fewer trials leave the belief
  too diffuse to separate the slices reliably);
* the shadow intent planner logs the right session intents (a
  ``practice_integration`` candidate is classified as such alongside live
  behavior), while the live queue composition is unchanged.
"""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.scheduling.scheduler import SchedulerSession, build_due_queue
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault, set_algorithm_version, write_facets
from tests.test_capability_residual import _build_vault, FACET, _RETRIEVAL_ITEMS, _SELECT_ITEMS
from tests.test_km2_write_path import _attempt, _item, _rubric

# The sim discrimination convention: >= 8 trials clears the 25th-percentile Beta
# bounds a perfect discriminator otherwise fails at N=5 (0.79 < 0.80 gate).
SIM_TRIALS = 8


def test_residual_activation_improves_capability_mae_without_parent_inflation(tmp_path):
    paths = _build_vault(tmp_path / "vault", enable=True)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    clock = FrozenClock(NOW)
    for _ in range(SIM_TRIALS):
        for item_id in _RETRIEVAL_ITEMS:
            _attempt(vault, repository, item_id, {"correctness": 4}, clock)
        for item_id in _SELECT_ITEMS:
            _attempt(vault, repository, item_id, {"correctness": 0}, clock)

    rows = {r["capability"]: r for r in repository.capability_residual_states()}
    assert {"retrieval", "method_selection"} <= set(rows)
    truth = {"retrieval": 1.0, "method_selection": 0.0}
    parent_mean = rows["retrieval"]["parent_mean"]

    residual_mae = sum(abs(rows[c]["residual_mean"] - truth[c]) for c in truth) / len(truth)
    parent_mae = sum(abs(parent_mean - truth[c]) for c in truth) / len(truth)
    assert residual_mae < parent_mae
    # No capability inflation of the shared parent: it stays between the slices.
    assert rows["method_selection"]["residual_mean"] < parent_mean < rows["retrieval"]["residual_mean"]


def _integration_item(item_id):
    return {
        "schema_version": 1,
        "id": item_id,
        "learning_object_id": "lo_svd_definition",
        "subjects": None,
        "practice_mode": "constructed_response",
        "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
        "evidence_facets": [FACET],
        "evidence_weights": {FACET: 1.0},
        "prompt": "Assemble the full derivation.",
        "expected_answer": "A full derivation.",
        "difficulty": 0.6,
        "grading_rubric": _rubric(
            "assembles",
            [{"facet": FACET, "capability": "coordination", "role": "primary"}],
            correlation_group="integration_grp",
        ),
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


def test_shadow_intent_logs_practice_integration_at_the_right_moment(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})
    write_facets(paths, [{"id": FACET, "kind": "procedure_contract", "claim": "Assemble."}])
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_integration_001"),
        _integration_item("pi_integration_001"),
    )
    set_algorithm_version(paths, "mvp-0.7")

    loaded = load_vault(paths.root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    sync_vault_state(loaded, repository, clock=FrozenClock(NOW))
    queue = build_due_queue(
        loaded, repository, clock=FrozenClock(NOW), session=SchedulerSession(session_id="s_intent")
    )
    assert any(i.practice_item_id == "pi_integration_001" for i in queue)

    slate = repository.latest_scheduler_slate_by_session("s_intent")
    plan = (slate["session_context"] or {}).get("shadow_intent")
    assert plan is not None
    # The constructed-response candidate is classified as practice_integration.
    assert "practice_integration" in plan["intent_counts"]
