"""Display-only practice-information value (scheduler explanation).

The number is the Fisher information of one ordinary graded attempt about the
LO mastery latent under the 2PL link — a²·p·(1−p) at the learner's current
mastery logit, scaled by the default attempt type's evidence mass. It must
NEVER influence selection: `_priority` reads exactly its four weighted keys.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from learnloop.db.repositories import Repository
from learnloop.services.golden_path_fixture import build_golden_path_fixture
from learnloop.services.mastery import initial_mastery_state
from learnloop.services.scheduler import _practice_information, _priority
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths


@pytest.fixture()
def golden_vault():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "gp"
        build_golden_path_fixture(root)
        vault = load_vault(root)
        repository = Repository(VaultPaths(root, vault.config).sqlite_path)
        sync_vault_state(vault, repository)
        yield vault, repository


def _mastery_at(logit_mean: float):
    state = initial_mastery_state("lo_x", "test", "2026-07-21T00:00:00Z")
    return type(state)(**{**state.__dict__, "logit_mean": logit_mean})


def test_boundary_item_maximizes_information(golden_vault):
    vault, _repository = golden_vault
    item = next(iter(vault.practice_items.values()))
    lo = vault.learning_object_for_item(item)

    # Golden-path items carry difficulty 0.6; sweep θ and confirm the maximum
    # sits where p crosses 0.5 (θ == b), not at the extremes.
    values = {theta: _practice_information(item, lo, _mastery_at(theta), vault.config) for theta in (-4.0, -2.0, 0.0, 0.5, 2.0, 4.0)}
    boundary_theta = max(values, key=values.get)
    assert values[boundary_theta] > values[-4.0]
    assert values[boundary_theta] > values[4.0]
    # Far-above-level (θ=4) is near-zero information.
    assert values[4.0] < 0.05
    # a=1.0, mass(independent_attempt)=1.0 → the theoretical max is p(1−p)=0.25.
    assert max(values.values()) <= 0.25 + 1e-9


def test_claim_seeded_theta_shifts_information(golden_vault):
    vault, _repository = golden_vault
    item = next(iter(vault.practice_items.values()))
    lo = vault.learning_object_for_item(item)
    # difficulty 0.6 → b = 2.5·(0.6−0.5)·2 = 0.5. A learner claiming near the
    # boundary (θ≈b) gets more information from this item than a strong one.
    near_boundary = _practice_information(item, lo, _mastery_at(0.5), vault.config)
    strong = _practice_information(item, lo, _mastery_at(3.0), vault.config)
    assert near_boundary > strong
    # Missing mastery state falls back to θ=0 without crashing.
    assert _practice_information(item, lo, None, vault.config) > 0


def test_practice_information_never_reaches_priority(golden_vault):
    vault, _repository = golden_vault
    components = {
        "forgetting_risk": 0.7,
        "goal_frontier": 0.2,
        "recent_error": 0.1,
        "probe_eig": 0.3,
    }
    base = _priority(components, vault.config)
    with_display = _priority({**components, "practice_information": 5.0}, vault.config)
    assert with_display == base
