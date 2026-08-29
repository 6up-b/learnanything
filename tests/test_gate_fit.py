"""Gate fitter: label assembly semantics and pure-Python logistic recovery."""

from __future__ import annotations

import json

import pytest

from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import Repository
from learnloop.diagnosis.gate_fit import (
    GateExample,
    GateFitError,
    assemble_gate_training_set,
    fit_gate_weights,
)
from learnloop.diagnosis.gate_score import GATE_FEATURES, GATE_FEATURE_VERSION

from tests.helpers import create_basic_vault


def _repository(tmp_path) -> Repository:
    paths = create_basic_vault(tmp_path / "vault")
    return Repository(paths.sqlite_path)


def _seed_gate_row(repository, attempt_id, gate, *, rating=None, created="2026-01-01T00:00:00Z"):
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, created_at)
            VALUES (?, 'pi_svd_define_001', 'lo_svd_definition', 'short_answer', 'independent_attempt', ?)
            """,
            (attempt_id, created),
        )
        connection.execute(
            """
            INSERT INTO attempt_surprise(attempt_id, observed_joint_bucket_json, gate_diagnostics_json,
                                         algorithm_version, created_at)
            VALUES (?, '{}', ?, 'test', ?)
            """,
            (attempt_id, json.dumps(gate), created),
        )
        connection.commit()
    if rating is not None:
        repository.upsert_followup_rating(
            attempt_id=f"{attempt_id}_followup_rated",
            gate_attempt_id=attempt_id,
            useful=rating,
        )


def _cascade_gate(**overrides):
    gate = {
        "outcome": "queued",
        "decisive_reason": "negative_surprise",
        "decisive_signal": {"name": "bayesian_surprise", "value": 0.2, "threshold": 0.05},
        "natural_trigger_reasons": ["negative_surprise"],
        "would_suppress": [],
        "would_auto_fire": True,
        "manual_override": False,
        "bayesian_surprise": 0.2,
        "surprise_direction": "negative",
        "tau_followup_nats": 0.05,
        "grader_confidence": 0.9,
        "max_error_severity": 0.0,
        "target_facets": [],
        "feature_version": GATE_FEATURE_VERSION,
    }
    gate.update(overrides)
    return gate


def test_label_assembly(tmp_path):
    repository = _repository(tmp_path)
    # The rated-followup FK targets need attempt rows too.
    with repository.connection() as connection:
        for suffix in ("a_manual_followup_rated", "a_useful_followup_rated", "a_useless_followup_rated"):
            connection.execute(
                """
                INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, created_at)
                VALUES (?, 'pi_svd_define_002', 'lo_svd_definition', 'short_answer', 'independent_attempt', '2026-01-02T00:00:00Z')
                """,
                (suffix,),
            )
        connection.commit()

    # Manual override where the gate was silent -> positive.
    _seed_gate_row(
        repository,
        "a_manual",
        _cascade_gate(manual_override=True, would_auto_fire=False, natural_trigger_reasons=[]),
        created="2026-01-01T00:00:01Z",
    )
    # Auto-fired, rated useful -> positive; rated not useful -> negative.
    _seed_gate_row(repository, "a_useful", _cascade_gate(), rating=True, created="2026-01-01T00:00:02Z")
    _seed_gate_row(repository, "a_useless", _cascade_gate(), rating=False, created="2026-01-01T00:00:03Z")
    # Silent row -> weak negative.
    _seed_gate_row(
        repository,
        "a_silent",
        _cascade_gate(
            outcome="not_triggered",
            decisive_reason="no_trigger",
            natural_trigger_reasons=[],
            would_auto_fire=False,
            bayesian_surprise=0.01,
        ),
        created="2026-01-01T00:00:04Z",
    )
    # Budget-suppressed row -> excluded entirely.
    _seed_gate_row(
        repository,
        "a_no_time",
        _cascade_gate(outcome="suppressed", decisive_reason="no_time"),
        created="2026-01-01T00:00:05Z",
    )
    # Manual override that would ALSO have auto-fired -> no label.
    _seed_gate_row(
        repository,
        "a_manual_agree",
        _cascade_gate(manual_override=True, would_auto_fire=True),
        created="2026-01-01T00:00:06Z",
    )

    examples = assemble_gate_training_set(repository, LearnLoopConfig())
    by_source = {example.label_source: example for example in examples}
    assert len(examples) == 4
    assert by_source["manual_override"].label == 1
    assert by_source["rating_useful"].label == 1
    assert by_source["rating_not_useful"].label == 0
    assert by_source["silent_gate"].label == 0
    assert by_source["silent_gate"].weight == pytest.approx(0.25)
    assert all(set(example.features) == set(GATE_FEATURES) for example in examples)


def test_label_assembly_excludes_old_feature_semantics(tmp_path):
    repository = _repository(tmp_path)
    old_gate = _cascade_gate(feature_version=GATE_FEATURE_VERSION - 1)
    _seed_gate_row(repository, "old_window_counts", old_gate)

    assert assemble_gate_training_set(repository, LearnLoopConfig()) == []


def _example(features, label, source="rating_useful", weight=1.0, attempt_id="a"):
    full = {name: 0.0 for name in GATE_FEATURES}
    full.update(features)
    return GateExample(attempt_id, full, label, source, weight)


def test_fitter_recovers_separating_weights():
    # Positives always have negative_surprise=1, negatives 0 — the fitter must
    # find a strongly positive weight on that feature and separate perfectly.
    examples = [
        _example({"negative_surprise": 1.0, "error_event_written": 1.0}, 1, attempt_id=f"p{i}")
        for i in range(20)
    ] + [
        _example({"error_event_written": 1.0}, 0, attempt_id=f"n{i}")
        for i in range(20)
    ]
    result = fit_gate_weights(examples, l2=0.01, epochs=800, learning_rate=1.0)
    assert result.weights["negative_surprise"] > 0.5
    assert result.auc == pytest.approx(1.0)
    assert result.accuracy > 0.9


def test_l2_shrinks_weights():
    examples = [
        _example({"negative_surprise": 1.0}, 1, attempt_id=f"p{i}") for i in range(10)
    ] + [_example({}, 0, attempt_id=f"n{i}") for i in range(10)]
    loose = fit_gate_weights(examples, l2=0.001, epochs=500)
    tight = fit_gate_weights(examples, l2=10.0, epochs=500)
    assert abs(tight.weights["negative_surprise"]) < abs(loose.weights["negative_surprise"])


def test_fitter_requires_both_classes():
    examples = [_example({"negative_surprise": 1.0}, 1)]
    with pytest.raises(GateFitError):
        fit_gate_weights(examples)
    with pytest.raises(GateFitError):
        fit_gate_weights([])


def test_auc_handles_ties():
    examples = [
        _example({"negative_surprise": 0.5}, 1, attempt_id="p0"),
        _example({"negative_surprise": 0.5}, 0, attempt_id="n0"),
    ]
    result = fit_gate_weights(examples, epochs=10)
    assert result.auc == pytest.approx(0.5)
