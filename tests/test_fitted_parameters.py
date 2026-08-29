"""Fitted-parameter store (migration 016): activation invariant, decoding,
rollback, and the hard-validated FSRS weights resolution fallback."""

from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.params.fitted_params import FSRS_WEIGHTS_SCOPE, resolve_fsrs_weights
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS

from tests.helpers import create_basic_vault


def _repository(tmp_path) -> Repository:
    paths = create_basic_vault(tmp_path / "vault")
    return Repository(paths.sqlite_path)


def test_insert_and_activate_replaces_prior_active_set(tmp_path):
    repository = _repository(tmp_path)
    first = repository.insert_fitted_parameters(
        scope="demo_scope",
        params={"weights": [1.0]},
        algorithm_version="mvp-0.3",
        training_rows_count=10,
    )
    second = repository.insert_fitted_parameters(
        scope="demo_scope",
        params={"weights": [2.0]},
        algorithm_version="mvp-0.3",
        training_rows_count=20,
        metrics={"log_loss": 0.5},
    )

    active = repository.active_fitted_parameters("demo_scope")
    assert active is not None
    assert active["id"] == second
    assert active["params"] == {"weights": [2.0]}
    assert active["metrics"] == {"log_loss": 0.5}
    assert active["active"] is True

    rows = repository.list_fitted_parameters("demo_scope")
    assert [row["id"] for row in rows] == [second, first]
    deactivated = [row for row in rows if row["id"] == first][0]
    assert deactivated["active"] is False
    assert deactivated["deactivated_at"] is not None


def test_activation_is_scoped(tmp_path):
    repository = _repository(tmp_path)
    a = repository.insert_fitted_parameters(
        scope="scope_a", params={}, algorithm_version="v", training_rows_count=1
    )
    b = repository.insert_fitted_parameters(
        scope="scope_b", params={}, algorithm_version="v", training_rows_count=1
    )
    assert repository.active_fitted_parameters("scope_a")["id"] == a
    assert repository.active_fitted_parameters("scope_b")["id"] == b


def test_insert_without_activate_keeps_prior_active(tmp_path):
    repository = _repository(tmp_path)
    first = repository.insert_fitted_parameters(
        scope="demo_scope", params={}, algorithm_version="v", training_rows_count=1
    )
    repository.insert_fitted_parameters(
        scope="demo_scope", params={}, algorithm_version="v", training_rows_count=2, activate=False
    )
    assert repository.active_fitted_parameters("demo_scope")["id"] == first


def test_deactivate_rolls_back_to_defaults(tmp_path):
    repository = _repository(tmp_path)
    repository.insert_fitted_parameters(
        scope="demo_scope", params={}, algorithm_version="v", training_rows_count=1
    )
    assert repository.deactivate_fitted_parameters("demo_scope") == 1
    assert repository.active_fitted_parameters("demo_scope") is None
    # History is kept.
    assert len(repository.list_fitted_parameters("demo_scope")) == 1


def test_resolve_fsrs_weights_defaults_when_absent(tmp_path):
    repository = _repository(tmp_path)
    assert resolve_fsrs_weights(repository) is FSRS6_DEFAULT_WEIGHTS


def test_resolve_fsrs_weights_uses_valid_fitted_set(tmp_path):
    repository = _repository(tmp_path)
    fitted = [w * 1.1 for w in FSRS6_DEFAULT_WEIGHTS]
    repository.insert_fitted_parameters(
        scope=FSRS_WEIGHTS_SCOPE,
        params={"weights": fitted},
        algorithm_version="v",
        training_rows_count=100,
    )
    assert resolve_fsrs_weights(repository) == tuple(fitted)


def test_resolve_fsrs_weights_falls_back_on_malformed_payload(tmp_path):
    repository = _repository(tmp_path)
    for params in (
        {},  # missing weights
        {"weights": [1.0, 2.0]},  # wrong length
        {"weights": [*FSRS6_DEFAULT_WEIGHTS[:-1], "nan-string"]},  # non-numeric
        {"weights": [*FSRS6_DEFAULT_WEIGHTS[:-1], float("nan")]},  # non-finite
        {"weights": [*FSRS6_DEFAULT_WEIGHTS[:-1], True]},  # bool masquerading as number
    ):
        repository.insert_fitted_parameters(
            scope=FSRS_WEIGHTS_SCOPE,
            params=params,
            algorithm_version="v",
            training_rows_count=1,
        )
        assert resolve_fsrs_weights(repository) is FSRS6_DEFAULT_WEIGHTS
