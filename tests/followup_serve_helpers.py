"""FG1's fixtures: a synthetic vault with a miss whose diagnosis leaves two rival causes."""

from __future__ import annotations

from typing import Any

from learnloop.algorithm_versions import FOLLOWUP_SERVE_ALGORITHM_VERSION
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.db.repositories import Repository
from learnloop.followup_serve.gates import SERVING_SURFACE
from learnloop.followup_run.jobs import process_next_job
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


def generated_item(vault_root, repository: Repository, item_id: str, *, workflow_id: str | None = None,
                   source: str = "workflow") -> Any:
    """A real item in the vault with the single-use identity."""

    from learnloop.followup_serve import identity
    from tests.test_causal_p2_acceptance import _extra_item

    _extra_item(vault_root, item_id, source_family=f"family-{item_id}", prompt=f"Fresh question {item_id}")
    identity.register(repository, practice_item_id=item_id, revision=f"rev-{item_id}", source=source,
                      workflow_id=workflow_id, clock=CLOCK)
    vault = load_vault(vault_root)
    sync_vault_state(vault, repository, clock=CLOCK)
    return vault


class AuthorFake:
    """The frontier author, faked: counts its physical calls and keeps what it read."""

    model = "fake-frontier"

    def __init__(self, *, prompt: str | None = None, same_predictions: bool = False, error: Exception | None = None):
        self.calls = 0
        self.contexts: list[Any] = []
        self.prompt = prompt
        self.same_predictions = same_predictions
        self.error = error

    def run_followup_probe_authoring(self, context: Any) -> Any:
        from learnloop.diagnosis.ai_contracts import (
            FollowupProbeAuthored,
            FollowupProbeCriterion,
            FollowupProbeManipulation,
            FollowupProbePrediction,
        )

        self.calls += 1
        self.contexts.append(context)
        if self.error is not None:
            raise self.error
        refs = [row["hypothesis_ref"] for row in context.hypotheses]
        criteria = [f"fact_{index}" for index in range(len(refs))]
        return FollowupProbeAuthored(
            prompt_md=self.prompt or f"On {context.learning_object_title}: which factor makes the product valid, and why? (#{self.calls})",
            expected_answer_md="U Sigma V^T, because the factors must be orthogonal.",
            surface_suffix=f"tell_apart_{self.calls}",
            criteria=[FollowupProbeCriterion(id=name, description=f"States {name}.", points=2) for name in criteria],
            predictions=[
                FollowupProbePrediction(hypothesis_ref=ref, fails_criteria=[criteria[0] if self.same_predictions else criteria[index]])
                for index, ref in enumerate(refs)
            ],
            intended_manipulations=[
                FollowupProbeManipulation(axis=axis, rationale="A new question aimed at the causes.")
                for axis in ("surface_wording", "answer_contract", "rubric")
            ],
        )


def author_clients(fake: Any) -> Any:
    from types import SimpleNamespace

    from tests.structured_ai import StructuredClientFake

    class _Client(StructuredClientFake):
        model = "fake-frontier"

        def run_followup_probe_authoring(self, context):
            return fake.run_followup_probe_authoring(context)

    return SimpleNamespace(author=_Client())
