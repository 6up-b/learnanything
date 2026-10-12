from dataclasses import replace
import sqlite3

import pytest

from learnloop.config import LearnLoopConfig
from learnloop.field.priors import load_frozen_priors
from learnloop.field.types import AttemptRow, ItemFeatures


def test_claim_priors_use_only_preexisting_historical_scopes():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute(
        "CREATE TABLE learner_claims(id, scope_type, scope_id, claimed_level, prior_pseudo_count, created_at)"
    )
    connection.executemany("INSERT INTO learner_claims VALUES (?,?,?,?,?,?)", [
        ("early", "subject", "math", .75, 1., "2025-01-01T00:00:00Z"),
        ("local", "learning_object", "lo", .25, 1., "2025-01-02T00:00:00Z"),
        ("future", "subject", "math", .99, 10., "2027-01-01T00:00:00Z"),
        ("concept", "concept", "c", .99, 10., "2025-01-01T00:00:00Z"),
    ])
    rows = [AttemptRow("a", ItemFeatures("i", "lo", "2026-01-01T00:00:00Z", subject_id="math"), 1., 1.)]
    general, priors, report = load_frozen_priors(connection, rows, LearnLoopConfig())
    assert general["math"] == pytest.approx(1.0986122886681098)
    assert priors["lo"][0] == pytest.approx(-1.0986122886681098)
    assert report["eligible_before_replay"] == 2
    assert report["excluded_later_or_unordered"] == 1
    assert report["excluded_missing_concept_mapping"] == 1
    assert load_frozen_priors(connection, [replace(rows[0], outcome=0)], LearnLoopConfig()) == (general, priors, report)
    connection.close()


def test_empty_log_does_not_backdate_current_claims():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute(
        "CREATE TABLE learner_claims(id, scope_type, scope_id, claimed_level, prior_pseudo_count, created_at)"
    )
    connection.execute(
        "INSERT INTO learner_claims VALUES ('x','global',NULL,.9,1.,'2025-01-01T00:00:00Z')"
    )
    general, priors, report = load_frozen_priors(connection, (), LearnLoopConfig())
    assert general == priors == {}
    assert report["excluded_later_or_unordered"] == 1
    connection.close()
