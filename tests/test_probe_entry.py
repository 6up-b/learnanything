from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.probes import enter_probe
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault


def test_enter_probe_creates_in_progress_state_and_locked_hypothesis_set(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)

    hypothesis_set = enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    state = repository.probe_state("lo_svd_definition")
    assert state is not None
    assert state.status == "in_progress"
    assert state.hypothesis_set_id == hypothesis_set.id
    assert state.probe_attempts_target == 3
    assert state.entered_at is not None

    record = repository.fetch_hypothesis_set(hypothesis_set.id)
    assert record is not None
    labels = {entry["label"] for entry in record["hypotheses"]}
    assert {"mastered", "unfamiliar"} <= labels
    assert sum(record["prior"].values()) == pytest.approx(1.0)


def test_enter_probe_reduces_target_with_strong_claim(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)

    enter_probe(loaded, repository, "lo_svd_definition", claimed_level=0.9, clock=FrozenClock(NOW))

    state = repository.probe_state("lo_svd_definition")
    assert state.probe_attempts_target == 1


def test_enter_probe_is_deterministic(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)

    first = enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    second = enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    assert [h.label for h in first.hypotheses] == [h.label for h in second.hypotheses]
    assert first.prior == second.prior
