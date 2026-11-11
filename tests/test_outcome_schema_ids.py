"""What the test lane's fixed outcome-schema and calibration-model ids leave real, and what the random ids they replace can do.

A vault mints its builtin schemas' ids and its calibration models' ids at random, and each reaches the certainty bound's
seed through the resolved calibration model's hash. The lane fixes only those minted ids, so a test's masses repeat. Here
production's own methods run with their random ids, and the bound is checked across seeds: its limits hold for every
vault, not for one chosen hash.
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


def _models(repository):
    with repository.connection() as connection:
        ordered = [row[0] for row in connection.execute("SELECT id FROM grader_calibration_models ORDER BY created_at, id")]
        inserted = [row[0] for row in connection.execute("SELECT id FROM grader_calibration_models ORDER BY rowid")]
        alphas = {row[0] for row in connection.execute("SELECT id FROM grader_calibration_alphas")}
    return ordered, inserted, alphas


def _resolved(repository, clock):
    schema_id, version = resolve_schema_id(repository, COARSE_RESPONSE_SLUG)
    return gc.resolve_calibration_model(repository, grader_identity_hash=None, outcome_schema_id=schema_id,
                                        outcome_schema_version=version, domain=None, length_bucket=None, clock=clock)


def test_production_mints_a_new_random_calibration_model_id_for_each_vault_and_keeps_it(tmp_path):
    first, second = Repository(tmp_path / "a.sqlite"), Repository(tmp_path / "b.sqlite")
    model = {"semver": "0.1.0", "content_hash": "the-same-content", "scope_level": "global", "backoff_chain_json": "[]",
             "status": "heuristic"}
    alphas = {"success": {"success|high": 1.0}}
    minted = lane._production_insert_calibration_model(first, model=model, alphas=alphas)
    other = lane._production_insert_calibration_model(second, model=model, alphas=alphas)
    assert minted != other and len(minted) == len(other) == 26
    assert not minted.startswith("01GCM") and not other.startswith("01GCM")
    assert lane._production_insert_calibration_model(first, model=model, alphas=alphas) == minted  # content-addressed


def test_the_lane_fixes_only_the_model_ids_so_two_vaults_draw_the_same_bound(tmp_path):
    """Fail-first: with only the schema ids fixed, two vaults seeded alike resolved different model hashes (the global
    prior's id is in it), so their certainty bounds differed about 1 run in 60 (the AD3 reading flake)."""

    from tests.daily_plan_fakes import MovableClock

    clock = MovableClock()  # frozen: every created_at ties, so the order rests on the ids alone
    first, second = Repository(tmp_path / "a.sqlite"), Repository(tmp_path / "b.sqlite")
    one, two = _resolved(first, clock), _resolved(second, clock)
    assert one.model_id == two.model_id and one.model_id.startswith("01GCM")
    assert one.model_hash == two.model_hash
    (ordered, inserted, alphas), (ordered_b, _inserted_b, alphas_b) = _models(first), _models(second)
    assert ordered == ordered_b and len(ordered) > 1
    # Creation order, as production's monotonic ULIDs give it: a re-seeded prior still wins as the latest.
    assert ordered == inserted
    # Only the model's own id: its alpha rows mint theirs at random, and nothing collides.
    assert alphas and not alphas & alphas_b and not any(value.startswith("01GCM") for value in alphas)
    assert _resolved(first, clock).model_hash == one.model_hash and _models(first)[1] == inserted  # nothing re-minted
    from learnloop.db import repositories

    assert repositories.new_ulid() != repositories.new_ulid()
    assert not repositories.new_ulid().startswith("01GCM")
