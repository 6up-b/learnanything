from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ruamel.yaml import YAML

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptDraft, AttemptResult, SelfGradeInput, complete_self_graded_attempt
from learnloop.vault.models import LoadedVault

_yaml = YAML(typ="safe")


class ObservationTemplatesNotReady(RuntimeError):
    pass


class ObservationTemplateError(ValueError):
    pass


@dataclass(frozen=True)
class ObservationResult:
    observation_event_id: str
    binding_mode: str
    emitted_attempt_id: str | None
    attempt_result: AttemptResult | None


def parse_template_yaml(template_yaml: str) -> dict[str, Any]:
    data = _yaml.load(template_yaml)
    if not isinstance(data, dict):
        raise ObservationTemplateError("Observation template must be a YAML mapping")
    return data


def validate_template(template: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(template, dict):
        return ["Observation template must be a mapping"]
    fields = template.get("fields")
    if not isinstance(fields, list) or not fields:
        errors.append("Observation template requires a non-empty 'fields' list")
    emits = template.get("emits")
    if emits is not None:
        if not isinstance(emits, dict):
            errors.append("'emits' must be a mapping")
        elif "attempt_type" not in emits:
            errors.append("'emits' requires an attempt_type")
        elif "answer_field" not in emits:
            errors.append("'emits' requires an answer_field")
    return errors


def register_observation_template(
    repository: Repository,
    *,
    domain: str,
    version: str,
    title: str,
    template_yaml: str,
    active: bool = True,
    clock: Clock | None = None,
) -> str:
    template = parse_template_yaml(template_yaml)
    errors = validate_template(template)
    if errors:
        raise ObservationTemplateError("; ".join(errors))
    emits_attempt = template.get("emits") is not None
    return repository.insert_observation_template(
        {
            "domain": domain,
            "version": version,
            "title": title,
            "template_yaml": template_yaml,
            "emits_attempt": emits_attempt,
            "active": active,
        },
        clock=clock,
    )


def record_observation(
    vault: LoadedVault,
    repository: Repository,
    *,
    template_id: str,
    response: dict[str, Any],
    related_learning_object_id: str | None = None,
    related_practice_item_id: str | None = None,
    session_id: str | None = None,
    subject: str | None = None,
    clock: Clock | None = None,
) -> ObservationResult:
    template_row = repository.fetch_observation_template(template_id)
    if template_row is None:
        raise ObservationTemplateError(f"Unknown observation template {template_id}")
    template = parse_template_yaml(template_row["template_yaml"])
    errors = validate_template(template)
    if errors:
        raise ObservationTemplateError("; ".join(errors))

    emits = template.get("emits")
    emitted_attempt_id: str | None = None
    attempt_result: AttemptResult | None = None

    # Ambiguous binding (no resolved Practice Item for an emitting template) lands
    # in 'pending'; LearnLoop never silently guesses the binding.
    if emits is not None and related_practice_item_id is not None:
        binding_mode = "template_fixed"
        attempt_result = _emit_attempt(
            vault,
            repository,
            emits=emits,
            practice_item_id=related_practice_item_id,
            response=response,
            clock=clock,
        )
        emitted_attempt_id = attempt_result.attempt_id
    elif emits is not None:
        binding_mode = "pending"
    else:
        binding_mode = "template_fixed" if related_practice_item_id else "learner_picks"

    observation_event_id = repository.insert_observation_event(
        {
            "template_id": template_id,
            "subject": subject,
            "session_id": session_id,
            "related_learning_object_id": related_learning_object_id,
            "related_practice_item_id": related_practice_item_id,
            "binding_mode": binding_mode,
            "response": response,
            "emitted_attempt_id": emitted_attempt_id,
            "template_version": template_row["version"],
        },
        clock=clock,
    )
    return ObservationResult(
        observation_event_id=observation_event_id,
        binding_mode=binding_mode,
        emitted_attempt_id=emitted_attempt_id,
        attempt_result=attempt_result,
    )


def _emit_attempt(
    vault: LoadedVault,
    repository: Repository,
    *,
    emits: dict[str, Any],
    practice_item_id: str,
    response: dict[str, Any],
    clock: Clock | None,
) -> AttemptResult:
    answer_field = emits["answer_field"]
    answer = str(response.get(answer_field, ""))
    criterion_points = response.get(emits.get("criterion_points_field", "criterion_points"), {})
    confidence = int(response.get(emits.get("confidence_field", "confidence"), 3))
    error_type = response.get(emits.get("error_type_field", "error_type"))
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=practice_item_id,
            learner_answer_md=answer,
            attempt_type=emits["attempt_type"],
        ),
        SelfGradeInput(
            criterion_points={key: float(value) for key, value in dict(criterion_points).items()},
            confidence=confidence,
            error_type=error_type,
        ),
        clock=clock,
    )
