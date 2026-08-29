"""KM5 §4.2 lazy capability-residual activation (DEFAULT OFF).

A planted capability-divergent learner (strong retrieval, weak method_selection
on ONE shared facet) drives real attempts. With the feature enabled the
projection activates a learner-specific residual per diverging (facet,
capability): the capability-sliced residual belief tracks the planted truth
better than the pooled shared parent, without inflating that parent. Activation
is derived in the projection fold, so a rebuild reproduces it byte-identically.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.substrate.replay import rebuild_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault, set_algorithm_version, write_facets
from tests.test_km2_write_path import _attempt, _item, _rubric

FACET = "facet_svd_factorization"

# Two surface groups per capability so the persistent-disagreement trigger has
# >= 2 independent groups; retrieval is answered correctly, selection wrongly.
_RETRIEVAL_ITEMS = ("pi_ret_a", "pi_ret_b")
_SELECT_ITEMS = ("pi_sel_a", "pi_sel_b")


def _enable_residual(paths, **overrides) -> None:
    keys = "\n".join(
        [
            "residual_activation_enabled = true",
            f"residual_divergence_threshold = {overrides.get('divergence', 0.1)}",
            f"residual_min_independent_mass = {overrides.get('min_mass', 0.4)}",
            f"residual_min_independent_groups = {overrides.get('min_groups', 2)}",
            f"residual_shrinkage_pseudo_count = {overrides.get('shrinkage', 4.0)}",
        ]
    )
    toml_path = paths.root / "learnloop.toml"
    text = toml_path.read_text(encoding="utf-8")
    updated = text.replace("[capabilities]\n", f"[capabilities]\n{keys}\n", 1)
    if updated == text:
        updated = text + f"\n[capabilities]\n{keys}\n"
    toml_path.write_text(updated, encoding="utf-8")


def _build_vault(root: Path, *, enable: bool):
    paths = create_basic_vault(root)
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})
    write_facets(paths, [{"id": FACET, "kind": "definition", "claim": "SVD factorization."}])
    # Four items on the same facet: two at retrieval, two at method_selection,
    # each with its own source-example family (an independent surface group).
    specs = [
        ("pi_ret_a", "retrieval", "ret-a"),
        ("pi_ret_b", "retrieval", "ret-b"),
        ("pi_sel_a", "method_selection", "sel-a"),
        ("pi_sel_b", "method_selection", "sel-b"),
    ]
    for item_id, capability, family in specs:
        write_yaml(
            paths.practice_item_path("linear-algebra", item_id),
            _item(
                item_id,
                "lo_svd_definition",
                evidence_facets=[FACET],
                rubric=_rubric(
                    "correctness",
                    [{"facet": FACET, "capability": capability, "role": "primary"}],
                    correlation_group=f"grp_{family}",
                ),
                fingerprint={"source_family": family},
            ),
        )
    set_algorithm_version(paths, "mvp-0.7")
    if enable:
        _enable_residual(paths)
    return paths


def _drive(paths):
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    clock = FrozenClock(NOW)
    # Strong retrieval (full marks), weak selection (zero marks); repeat to build
    # mass on each independent surface group.
    for _ in range(3):
        for item_id in _RETRIEVAL_ITEMS:
            _attempt(vault, repository, item_id, {"correctness": 4}, clock)
        for item_id in _SELECT_ITEMS:
            _attempt(vault, repository, item_id, {"correctness": 0}, clock)
    return vault, repository


def _by_capability(repository) -> dict[str, dict]:
    return {row["capability"]: row for row in repository.capability_residual_states()}


def test_residual_activation_default_off_writes_nothing(tmp_path):
    paths = _build_vault(tmp_path / "vault", enable=False)
    _, repository = _drive(paths)
    assert repository.capability_residual_states() == []


def test_residual_activation_tracks_capability_truth_without_inflating_parent(tmp_path):
    paths = _build_vault(tmp_path / "vault", enable=True)
    _, repository = _drive(paths)
    rows = _by_capability(repository)
    assert "retrieval" in rows and "method_selection" in rows
    assert all(row["active"] for row in rows.values())

    truth = {"retrieval": 1.0, "method_selection": 0.0}
    parent_mean = rows["retrieval"]["parent_mean"]
    # The pooled parent is shared, so both cells report the same parent belief.
    assert parent_mean == pytest.approx(rows["method_selection"]["parent_mean"])

    residual_mae = sum(abs(rows[c]["residual_mean"] - truth[c]) for c in truth) / len(truth)
    parent_mae = sum(abs(parent_mean - truth[c]) for c in truth) / len(truth)
    assert residual_mae < parent_mae

    # The shared parent is not inflated toward the strong capability: it sits
    # between the two capability-sliced residual beliefs.
    assert rows["method_selection"]["residual_mean"] < parent_mean < rows["retrieval"]["residual_mean"]


def test_residual_activation_replay_deterministic(tmp_path):
    paths = _build_vault(tmp_path / "vault", enable=True)
    vault, repository = _drive(paths)

    def snapshot():
        return {
            (r["facet_id"], r["capability"]): (
                r["active"],
                r["activation_reason"],
                round(r["residual_mean"], 9),
                round(r["parent_mean"], 9),
                round(r["divergence"], 9),
                r["independent_groups"],
            )
            for r in repository.capability_residual_states()
        }

    live = snapshot()
    assert live  # activation actually happened
    rebuild_derived_state(vault, repository, clock=FrozenClock(NOW))
    once = snapshot()
    rebuild_derived_state(vault, repository, clock=FrozenClock(NOW))
    twice = snapshot()
    assert live == once == twice
