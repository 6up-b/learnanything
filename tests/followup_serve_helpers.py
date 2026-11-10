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

from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.diagnosis_fakes import ReviewFakeClient
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


# -- the live shape: a blind vault, a real diagnosis job, an item with task features ----------------


class BlindRivalClient(ReviewFakeClient):
    """Grader and diagnoser, as the real ones answer: a nontrivial error, causes aimed at the failed
    criterion, a repair aimed at it too, so the factor opens through ``_open_repair_factor`` and the
    second materialization runs. An answer on a generated probe fits the rival ``fact_1`` names."""

    divergent = False
    #: Words a test wants in the first cause's statement.
    quoting = ""
    #: What this diagnosis leaves unmapped: "", "no_target", "no_repair", "other_criterion", or "trivial".
    shape = ""
    #: How many distinct causes it names.
    causes = 2

    def _grade_parts(self, context):
        parts = super()._grade_parts(context)
        if any(criterion["id"] == "fact_0" for criterion in parts["criteria"]):
            parts["evidence"] = [
                {"criterion_id": criterion["id"], "evidence": "graded",
                 "points_awarded": 0.0 if criterion["id"] == "fact_0" else float(criterion["points"])}
                for criterion in parts["criteria"]
            ]
        return parts

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        return result.model_copy(update={"error_attributions": [
            attribution.model_copy(update={"error_type": "local_slip" if self.shape == "trivial" else "conceptual_schema_error"})
            for attribution in result.error_attributions
        ]})

    def _diagnosis(self, request, context):
        data = super()._diagnosis(request, context).model_dump()
        criteria = {
            attribution["index"]: (attribution.get("first_divergence") or {}).get("criterion_id")
            for attribution in context["current_attempt"]["blind_grade"]["error_attributions"]
        }
        for event in data["event_diagnoses"]:
            target = {"kind": "criterion", "criterion_id": criteria.get(event["event_index"])}
            event["candidate_causes"] = [
                {"statement": statement, "cause_scope": "learner_state", "prior_weight": weight, "target_ref": target,
                 "mechanism": mechanism, "discriminating_predictions": [f"if so, {statement}"]}
                for statement, weight, mechanism in (
                    (f"The order of the steps is wrong.{self.quoting}", 3.0, "incomplete_procedure_schema"),
                    ("The two conditions are confused.", 2.0, "representation_instability"),
                )
            ]
        for repair in data["repair_suggestions"]:
            repair["target_criterion_ids"] = [value for value in criteria.values() if value]
        for event in data["event_diagnoses"]:
            event["candidate_causes"] = event["candidate_causes"][:self.causes]
            if self.shape == "no_target":
                for cause in event["candidate_causes"]:
                    cause["target_ref"] = None
        if self.shape == "no_repair":
            data["repair_suggestions"] = []
        if self.shape == "other_criterion":
            names = [criterion["criterion_id"] for criterion in context["current_attempt"]["blind_grade"]["criteria"]]
            other = [name for name in names if name not in criteria.values()][:1]
            for repair in data["repair_suggestions"]:
                repair["target_criterion_ids"] = other
        if self.divergent:
            # Two causes needing different repairs, what the predecessor's quick check is for.
            names = [criterion["criterion_id"] for criterion in context["current_attempt"]["blind_grade"]["criteria"]][:2]
            for event in data["event_diagnoses"]:
                for cause, name in zip(event["candidate_causes"], names, strict=True):
                    cause["target_ref"] = {"kind": "criterion", "criterion_id": name}
            first = data["repair_suggestions"][0]
            data["repair_suggestions"] = [
                {**first, "target_criterion_ids": [name], "operator": f"elicit_{name}"} for name in names
            ]
        return request.result_model.model_validate(data)


#: What real items carry: the audit diffs each of these as its own axis (96 of 99 on one owner's vault).
TASK_FEATURES = {"complexity": 2, "transfer": "near", "representation": ["symbolic", "verbal"],
                 "response": "structured_steps", "scaffolding": "cue", "span": "multi_step"}
LIVE_ITEM = "pi_svd_compute_001"


def live_shape_vault(tmp_path, *, version: str = TAG, config: str = "", task_features: bool = True):
    """(paths, vault, repository): a blind vault, its missed item with task features."""

    from tests.split_live_helpers import split_vault

    paths, vault, repository = split_vault(tmp_path, version=version, config=config)
    if task_features:
        path = vault.practice_items[LIVE_ITEM].source_path if hasattr(vault.practice_items[LIVE_ITEM], "source_path") else None
        path = path or _item_path(paths, LIVE_ITEM)
        payload = read_yaml(path)
        payload["task_features"] = dict(TASK_FEATURES)
        write_yaml(path, payload)
        vault = load_vault(paths.root)
        sync_vault_state(vault, repository, clock=CLOCK)
    return paths, vault, repository


def _item_path(paths: Any, item_id: str) -> Any:
    return next(path for path in paths.root.rglob("*.yaml") if path.stem == item_id or item_id in path.read_text(encoding="utf-8"))


def live_miss(vault: Any, repository: Repository, client: Any, *, item_id: str = LIVE_ITEM, session_id: str | None = None,
              clock: Any = CLOCK, answer: str = "A = U Sigma V wrong"):
    """The miss through the real door, with its diagnosis job drained: the workflow's job is queued."""

    from tests.split_live_helpers import drain_jobs, submit

    result = submit(vault, repository, client, item_id=item_id, answer=answer, session_id=session_id, pipeline=False,
                    when=clock.now())
    outcome = run_post_attempt_pipeline(vault, repository, result=result, session_id=session_id,
                                        followup_surface=SERVING_SURFACE, clock=clock)
    drain_jobs(vault, repository, client, clock=clock)
    return result, outcome
