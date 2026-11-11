from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.probes import (
    Hypothesis,
    build_hypothesis_set,
    conditional_distribution,
)
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, create_basic_vault


def _insert_error(
    repository: Repository,
    error_type: str = "conceptual_slip",
    severity: float = 0.7,
    *,
    is_misconception: bool = True,
) -> None:
    repository.insert_error_event(
        {
            "id": f"err_{error_type}",
            "learning_object_id": "lo_svd_definition",
            "error_type": error_type,
            "severity": severity,
            "is_misconception": is_misconception,
            "status": "active",
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )


def test_conditional_distribution_is_normalized_for_every_hypothesis():
    known = ["conceptual_slip"]
    for hypothesis in [
        Hypothesis(label="mastered"),
        Hypothesis(label="unfamiliar"),
        Hypothesis(label="misconception:conceptual_slip", error_type="conceptual_slip"),
    ]:
        distribution = conditional_distribution(
            hypothesis,
            fatal_error_ids={"conceptual_slip"},
            known_error_types=known,
        )
        assert sum(distribution.values()) == pytest.approx(1.0)


def test_probe_hypothesis_set_ignores_transient_errors(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    _insert_error(repository, error_type="transient_slip", is_misconception=False)
    loaded = load_vault(vault_root)

    hypothesis_set = build_hypothesis_set(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    assert [hypothesis.label for hypothesis in hypothesis_set.hypotheses] == ["mastered", "unfamiliar"]
