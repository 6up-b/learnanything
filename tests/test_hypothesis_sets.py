from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.probes import build_hypothesis_set
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, create_basic_vault


def _insert_error(repository: Repository, error_type: str, severity: float) -> None:
    repository.insert_error_event(
        {
            "id": f"err_{error_type}",
            "learning_object_id": "lo_svd_definition",
            "error_type": error_type,
            "severity": severity,
            "is_misconception": True,
            "status": "active",
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )


def test_hypothesis_set_always_has_mastered_and_unfamiliar(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)

    hypothesis_set = build_hypothesis_set(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    labels = [h.label for h in hypothesis_set.hypotheses]
    assert labels == ["mastered", "unfamiliar"]
    assert hypothesis_set.prior["mastered"] == pytest.approx(0.5)
    assert hypothesis_set.prior["unfamiliar"] == pytest.approx(0.5)
    assert sum(hypothesis_set.prior.values()) == pytest.approx(1.0)


def test_hypothesis_set_adds_active_misconception(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    _insert_error(repository, "conceptual_slip", 0.7)

    hypothesis_set = build_hypothesis_set(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    labels = [h.label for h in hypothesis_set.hypotheses]
    assert "misconception:conceptual_slip" in labels
    assert sum(hypothesis_set.prior.values()) == pytest.approx(1.0)


def test_hypothesis_set_caps_and_drops_lowest_severity(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    # max_size = 5 -> keep mastered + unfamiliar + the 3 most severe misconceptions.
    _insert_error(repository, "err_high", 0.9)
    _insert_error(repository, "err_mid", 0.8)
    _insert_error(repository, "err_low", 0.7)
    _insert_error(repository, "err_drop", 0.6)

    hypothesis_set = build_hypothesis_set(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    assert len(hypothesis_set.hypotheses) == 5
    error_types = {h.error_type for h in hypothesis_set.hypotheses if h.error_type}
    assert error_types == {"err_high", "err_mid", "err_low"}
    assert "err_drop" not in error_types
    assert sum(hypothesis_set.prior.values()) == pytest.approx(1.0)
