"""Quantile-based (data-relative) follow-up thresholds."""

from __future__ import annotations

import json

import pytest

from learnloop.config import SchedulerFollowupConfig
from learnloop.db.repositories import Repository
from learnloop.numeric import empirical_quantile
from learnloop.diagnosis.signal_quantiles import resolve_followup_thresholds

from tests.helpers import create_basic_vault


def _repository(tmp_path) -> Repository:
    paths = create_basic_vault(tmp_path / "vault")
    return Repository(paths.sqlite_path)


def _seed_surprise_rows(repository: Repository, values, *, direction="negative", severity=None, start=0):
    """Insert minimal attempt + surprise rows directly (FKs are enforced)."""

    with repository.connection() as connection:
        for offset, value in enumerate(values):
            index = start + offset
            attempt_id = f"a_{index:05d}"
            created = f"2026-01-01T{index // 3600:02d}:{(index // 60) % 60:02d}:{index % 60:02d}Z"
            connection.execute(
                """
                INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, created_at)
                VALUES (?, 'pi_svd_define_001', 'lo_svd_definition', 'short_answer', 'independent_attempt', ?)
                """,
                (attempt_id, created),
            )
            gate = json.dumps({"max_error_severity": severity}) if severity is not None else None
            connection.execute(
                """
                INSERT INTO attempt_surprise(attempt_id, observed_joint_bucket_json, bayesian_surprise,
                                             surprise_direction, gate_diagnostics_json, algorithm_version, created_at)
                VALUES (?, '{}', ?, ?, ?, 'test', ?)
                """,
                (attempt_id, value, direction, gate, created),
            )
        connection.commit()


def test_absolute_fallback_below_min_samples(tmp_path):
    repository = _repository(tmp_path)
    config = SchedulerFollowupConfig()
    _seed_surprise_rows(repository, [0.1] * 10)

    resolved = resolve_followup_thresholds(repository, config)
    tau = resolved["tau_followup_nats"]
    assert tau.source == "absolute_fallback"
    assert tau.value == config.tau_followup_nats
    assert tau.sample_size == 10


def test_quantile_resolution_with_enough_samples(tmp_path):
    repository = _repository(tmp_path)
    config = SchedulerFollowupConfig(quantile_min_samples=30)
    values = [i / 100 for i in range(1, 41)]  # 0.01 .. 0.40
    _seed_surprise_rows(repository, values)

    resolved = resolve_followup_thresholds(repository, config)
    tau = resolved["tau_followup_nats"]
    assert tau.source == "quantile"
    assert tau.sample_size == 40
    assert tau.value == pytest.approx(empirical_quantile(values, config.tau_followup_quantile))
    assert tau.absolute_fallback == config.tau_followup_nats


def test_positive_direction_rows_do_not_count(tmp_path):
    repository = _repository(tmp_path)
    config = SchedulerFollowupConfig(quantile_min_samples=30)
    _seed_surprise_rows(repository, [0.5] * 40, direction="positive")

    resolved = resolve_followup_thresholds(repository, config)
    assert resolved["tau_followup_nats"].source == "absolute_fallback"
    assert resolved["tau_followup_nats"].sample_size == 0


def test_current_attempt_excluded(tmp_path):
    repository = _repository(tmp_path)
    config = SchedulerFollowupConfig(quantile_min_samples=30)
    # 30 rows at 0.10 plus one enormous outlier: excluding the outlier (the
    # attempt under evaluation) leaves exactly the min-sample count.
    _seed_surprise_rows(repository, [0.10] * 30)
    _seed_surprise_rows(repository, [9.9], start=30)

    with_outlier = resolve_followup_thresholds(repository, config)
    excluded = resolve_followup_thresholds(repository, config, exclude_attempt_id="a_00030")
    assert with_outlier["tau_followup_nats"].sample_size == 31
    assert excluded["tau_followup_nats"].sample_size == 30
    assert excluded["tau_followup_nats"].value == pytest.approx(0.10)


def test_window_limits_history(tmp_path):
    repository = _repository(tmp_path)
    config = SchedulerFollowupConfig(quantile_min_samples=10, quantile_window=20)
    # Old rows huge, recent rows small; window must only see the recent 20.
    _seed_surprise_rows(repository, [5.0] * 30)
    _seed_surprise_rows(repository, [0.1] * 20, start=30)

    resolved = resolve_followup_thresholds(repository, config)
    tau = resolved["tau_followup_nats"]
    assert tau.sample_size == 20
    assert tau.value == pytest.approx(0.1)


def test_severity_quantile_reads_gate_diagnostics(tmp_path):
    repository = _repository(tmp_path)
    config = SchedulerFollowupConfig(quantile_min_samples=30)
    severities = [i / 50 for i in range(1, 41)]
    for index, severity in enumerate(severities):
        _seed_surprise_rows(repository, [0.1], severity=severity, start=index)

    resolved = resolve_followup_thresholds(repository, config)
    tau = resolved["tau_severe_error"]
    assert tau.source == "quantile"
    assert tau.value == pytest.approx(empirical_quantile(severities, config.tau_severe_error_quantile))


def test_absolute_mode_disables_quantiles(tmp_path):
    repository = _repository(tmp_path)
    config = SchedulerFollowupConfig(threshold_mode="absolute")
    _seed_surprise_rows(repository, [0.5] * 50)

    resolved = resolve_followup_thresholds(repository, config)
    assert resolved["tau_followup_nats"].source == "absolute"
    assert resolved["tau_followup_nats"].value == config.tau_followup_nats
    # Static thresholds are always absolute.
    assert resolved["gamma_min"].source == "absolute"
    assert resolved["tau_unfamiliar_intervention"].source == "absolute"
