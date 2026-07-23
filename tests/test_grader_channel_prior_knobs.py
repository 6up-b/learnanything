"""P4 (measurement-correctness revision): the heuristic grade-channel prior knobs
(reliability floor, certainty-LCB quantile) live in the fitted_parameters store,
seeding respects them, and latest-wins model resolution lets a retuned prior reach
vaults seeded under the old constants."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import grader_calibration as gc
from learnloop.services.fitted_params import (
    CERTAINTY_LCB_QUANTILE_DEFAULT,
    GRADER_CHANNEL_RELIABILITY_FLOOR_DEFAULT,
    GRADER_CHANNEL_SCOPE,
    resolve_grader_channel_prior,
)
from learnloop.services.outcome_schemas import COARSE_RESPONSE_SLUG, ensure_builtin_schemas, resolve_schema_id
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault

CLOCK = FrozenClock(NOW)


def _repo(tmp_path) -> Repository:
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repo = Repository(paths.sqlite_path)
    sync_vault_state(vault, repo, clock=CLOCK)
    ensure_builtin_schemas(repo, clock=CLOCK)
    return repo


def _success_posterior(repo: Repository) -> float:
    schema_id, schema_version = resolve_schema_id(repo, COARSE_RESPONSE_SLUG, clock=CLOCK)
    resolved = gc.resolve_calibration_model(
        repo,
        grader_identity_hash=None,
        outcome_schema_id=schema_id,
        outcome_schema_version=schema_version,
        clock=CLOCK,
    )
    posterior = gc.posterior_over_true_class(
        resolved, observed_class="success", confidence_bucket="high"
    )
    return posterior["success"]


def test_resolver_defaults_and_fitted_override(tmp_path):
    repo = _repo(tmp_path)
    prior = resolve_grader_channel_prior(repo)
    assert prior.reliability_floor == pytest.approx(GRADER_CHANNEL_RELIABILITY_FLOOR_DEFAULT)
    assert prior.lcb_quantile == pytest.approx(CERTAINTY_LCB_QUANTILE_DEFAULT)

    repo.insert_fitted_parameters(
        scope=GRADER_CHANNEL_SCOPE,
        params={"reliability_floor": 0.95, "lcb_quantile": 0.3},
        algorithm_version="mvp-0.8",
        training_rows_count=0,
        clock=CLOCK,
    )
    fitted = resolve_grader_channel_prior(repo)
    assert fitted.reliability_floor == pytest.approx(0.95)
    assert fitted.lcb_quantile == pytest.approx(0.3)


def test_resolver_rejects_malformed_values(tmp_path):
    repo = _repo(tmp_path)
    repo.insert_fitted_parameters(
        scope=GRADER_CHANNEL_SCOPE,
        params={"reliability_floor": 1.7, "lcb_quantile": "wat"},
        algorithm_version="mvp-0.8",
        training_rows_count=0,
        clock=CLOCK,
    )
    prior = resolve_grader_channel_prior(repo)
    assert prior.reliability_floor == pytest.approx(GRADER_CHANNEL_RELIABILITY_FLOOR_DEFAULT)
    assert prior.lcb_quantile == pytest.approx(CERTAINTY_LCB_QUANTILE_DEFAULT)


def test_seeded_prior_respects_reliability_floor(tmp_path):
    """The default floor (0.92) replaces the bare longform 0.80: a high-confidence
    success emission resolves to a posterior near the floor, not 0.8."""

    repo = _repo(tmp_path)
    p_success = _success_posterior(repo)
    assert p_success >= 0.9


def test_retuned_knob_reaches_an_already_seeded_vault(tmp_path):
    """Latest-wins global resolution + unconditional content-addressed re-seed:
    activating a higher fitted floor mints a new prior row and subsequent
    resolution sharpens, without touching pinned interpretations."""

    repo = _repo(tmp_path)
    before = _success_posterior(repo)  # seeds under the default floor

    repo.insert_fitted_parameters(
        scope=GRADER_CHANNEL_SCOPE,
        params={"reliability_floor": 0.98, "lcb_quantile": 0.25},
        algorithm_version="mvp-0.8",
        training_rows_count=0,
        clock=CLOCK,
    )
    after = _success_posterior(repo)
    assert after > before
