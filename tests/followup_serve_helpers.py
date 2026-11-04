"""FG1's fixtures: a synthetic vault with a miss whose diagnosis leaves two rival causes."""

from __future__ import annotations

from typing import Any

from learnloop.algorithm_versions import FOLLOWUP_SERVE_ALGORITHM_VERSION
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.db.repositories import Repository
from learnloop.followup_serve.gates import SERVING_SURFACE
from learnloop.followup_serve.jobs import process_next_job
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, set_algorithm_version
from tests.test_causal_p2_acceptance import CLOCK, _acceptance_vault, _divergent_failure

TAG = FOLLOWUP_SERVE_ALGORITHM_VERSION
OFF = "\n[followup]\ngenerate_and_serve = false\n"


def rival_causes_vault(tmp_path, *, version: str = TAG, config: str = ""):
    """(vault, repository, paths) at ``version``: a joint vault, whose hypotheses normalization writes."""

    _vault, _repository, paths = _acceptance_vault(tmp_path)
    set_algorithm_version(paths, version)
    if config:
        append_config_toml(paths.root, config)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=CLOCK)
    return vault, repository, paths


def miss_with_rivals(vault: Any, repository: Repository, *, attempt_id: str = "att_causal_e2e",
                     surface: str | None = SERVING_SURFACE, session_id: str | None = None):
    """The miss, through the real pipeline."""

    result = _divergent_failure(vault, repository, attempt_id=attempt_id)
    outcome = run_post_attempt_pipeline(
        vault, repository, result=result, session_id=session_id, followup_surface=surface, clock=CLOCK,
    )
    return result, outcome


def run_jobs(vault: Any, repository: Repository, *, clients: Any = None, clock: Any = CLOCK, limit: int = 20) -> list[Any]:
    outcomes = []
    while len(outcomes) < limit:
        outcome = process_next_job(vault, repository, owner="test", clients=clients, clock=clock)
        if outcome is None:
            break
        outcomes.append(outcome)
    return outcomes
