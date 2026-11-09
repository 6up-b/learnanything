"""What the test lane's fixed outcome-schema ids leave real, and what the random ids they replace can do.

A vault mints its builtin schemas' ids at random, and each id reaches the certainty bound's seed through the calibration
model's hash. The lane fixes only the minted id, so a test's masses repeat. Here production's own method runs with its
random id, and the bound is checked across seeds: its limits hold for every vault, not for one chosen hash.
"""

from __future__ import annotations

import sqlite3

import pytest

from learnloop.attempts import grader_calibration as gc
from learnloop.attempts.effective_observation import _certainty, effective_observation_from_posterior
from learnloop.attempts.outcome_schemas import COARSE_RESPONSE_SLUG, resolve_schema_id
from learnloop.db.repositories import Repository
from learnloop.diagnosis import robust_composition as rc
from tests import conftest as lane


def _rows(repository):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute("SELECT id, slug, kind FROM outcome_schemas ORDER BY slug")]


def test_production_mints_a_new_random_ulid_for_each_vault_and_keeps_it(tmp_path):
    first, second = Repository(tmp_path / "a.sqlite"), Repository(tmp_path / "b.sqlite")
    minted = lane._production_ensure_outcome_schema(first, slug="coarse", kind="response")
    other = lane._production_ensure_outcome_schema(second, slug="coarse", kind="response")
    assert minted != other and len(minted) == len(other) == 26
    assert not minted.startswith("01SCHEMA")
    assert _rows(first) == [(minted, "coarse", "response")]
    assert lane._production_ensure_outcome_schema(first, slug="coarse", kind="response") == minted  # idempotent


def test_the_lane_fixes_only_the_id_and_production_still_inserts_the_row(tmp_path, monkeypatch):
    from learnloop.db import repositories

    first, second = Repository(tmp_path / "a.sqlite"), Repository(tmp_path / "b.sqlite")
    minted: list[str] = []
    lane_new_ulid = repositories.new_ulid

    def counted():
        minted.append(lane_new_ulid())
        return minted[-1]

    with monkeypatch.context() as patch:
        patch.setattr(repositories, "new_ulid", counted)
        fixed = first.ensure_outcome_schema(slug="coarse", kind="response")
        # Production's insert branch ran and minted this id: nothing inserted the row before it.
        assert minted == [fixed]
        assert first.ensure_outcome_schema(slug="coarse", kind="response") == fixed
        assert minted == [fixed]  # and its select branch mints nothing
    assert second.ensure_outcome_schema(slug="coarse", kind="response") == fixed
    assert first.ensure_outcome_schema(slug="other", kind="response") != fixed
    assert first.ensure_outcome_schema(slug="coarse", kind="response") == fixed
    assert _rows(second) == [(fixed, "coarse", "response")]
    # The insert is production's: its CHECK constraint still refuses a bad kind, and nothing was pre-inserted.
    with pytest.raises(sqlite3.IntegrityError):
        first.ensure_outcome_schema(slug="bad", kind="neither")
    assert [row[1] for row in _rows(first)] == ["coarse", "other"]
    # Only inside that method: every other id is still random.
    assert repositories.new_ulid() != repositories.new_ulid()
    assert not repositories.new_ulid().startswith("01SCHEMA")


def test_the_bound_stays_inside_its_limits_on_every_seed_and_mass_with_it(tmp_path):
    """The certainty bound never exceeds the posterior mean's certainty, and never goes below 0. So on any vault an
    answer's mass is at most its type's, and it stays positive while the bound does. A seed's only freedom is how far
    below certainty the bound falls: that is why a test may not pin one vault's exact mass with a random id."""

    repository = Repository(tmp_path / "state.sqlite")
    schema_id, version = resolve_schema_id(repository, COARSE_RESPONSE_SLUG)
    resolved = gc.resolve_calibration_model(repository, grader_identity_hash="x", outcome_schema_id=schema_id,
                                            outcome_schema_version=version, domain=None, length_bucket=None)
    emission = "other|unknown"
    posterior = gc.posterior_over_true_class(resolved, observed_class="other", confidence_bucket="unknown")
    point = _certainty(posterior)
    assert 0.0 < point < 1.0
    bounds = [rc.certainty_lcb(joint_alpha=resolved.joint_alpha, observed_emission=emission,
                               calibration_model_hash=f"seed-{seed}", decision_context_hash="context")
              for seed in range(1500)]
    assert all(0.0 < bound <= point + 1e-12 for bound in bounds)
    # Most vaults sit on the mean's certainty and some fall below it: both happen, which is what made this a flake.
    at_point = sum(bound >= point - 1e-9 for bound in bounds)
    assert at_point > 0.9 * len(bounds) and at_point < len(bounds)
    masses = [effective_observation_from_posterior(observation_id=None, posterior=posterior, certainty_lcb=bound,
                                                   attempt_type_mass=0.7, assistance_discount=1.0,
                                                   familiarity_discount=1.0, score_fraction={}).effective_mass
              for bound in bounds]
    assert all(0.0 < mass <= 0.7 + 1e-12 for mass in masses)
    assert max(masses) == pytest.approx(0.7) and min(masses) < 0.7


def test_each_bound_is_repeatable_for_its_own_seed(tmp_path):
    repository = Repository(tmp_path / "state.sqlite")
    schema_id, version = resolve_schema_id(repository, COARSE_RESPONSE_SLUG)
    resolved = gc.resolve_calibration_model(repository, grader_identity_hash="x", outcome_schema_id=schema_id,
                                            outcome_schema_version=version, domain=None, length_bucket=None)
    draw = lambda seed: rc.certainty_lcb(joint_alpha=resolved.joint_alpha, observed_emission="other|high",  # noqa: E731
                                         calibration_model_hash=seed, decision_context_hash="context")
    assert draw("seed-a") == draw("seed-a")
    assert len({draw(f"seed-{index}") for index in range(20)}) > 1
