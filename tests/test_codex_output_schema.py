from __future__ import annotations

import dataclasses
import inspect
import re
import textwrap
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from learnloop.ai.strict_schema import strict_output_schema, map_typed_schema_paths
from learnloop.ai import schemas as codex_schemas
from learnloop.attempts import ai_contracts as attempts_ai_contracts
from learnloop.attempts.ai_contracts import ErrorAttribution
from learnloop.content.authoring import ai_contracts as content_authoring_ai_contracts
from learnloop.content.pipeline import ai_contracts as content_pipeline_ai_contracts
from learnloop.content.proposals import ai_contracts as content_proposals_ai_contracts
from learnloop.content.proposals.ai_contracts import (
    PracticeItemPatchPayload,
    TraceContractPayload,
    TraceRecipePayload,
)
from learnloop.content.synthesis import ai_contracts as content_synthesis_ai_contracts
from learnloop.curriculum import ai_contracts as curriculum_ai_contracts
from learnloop.diagnosis import ai_contracts as diagnosis_ai_contracts
from learnloop.reader import ai_contracts as reader_ai_contracts
from learnloop.tutor import ai_contracts as tutor_ai_contracts
from learnloop.attempts.ai_contracts import GradingProposal
from learnloop.content.proposals.ai_contracts import AuthoringProposal
from learnloop.content.synthesis.ai_contracts import AppendReconciliation


def test_strict_schema_preserves_a_field_named_title():
    schema = strict_output_schema(AuthoringProposal)
    assert "title" in schema["$defs"]["LearningObjectPatchPayload"]["properties"]


def test_append_schema_declares_properties_on_bare_restructure_payload():
    """Regression for the provider's misleading extra-required-key 400.

    A bare ``dict`` has no Pydantic ``properties`` member. Strict Responses
    schemas still require that member, even when it is empty; without it the
    provider rejected the enclosing ``AppendRestructure`` as though its
    required ``payload`` key were not declared.
    """

    schema = strict_output_schema(AppendReconciliation)

    assert schema["$defs"]["AppendRestructure"]["properties"]["payload"] == {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }
    assert not _non_strict_objects(schema)


def test_authoring_payload_rejects_unknown_attempt_type():
    with pytest.raises(ValidationError):
        PracticeItemPatchPayload.model_validate(
            {
                "learning_object_id": "lo_svd",
                "practice_mode": "constructed_response",
                "attempt_types_allowed": ["freeform_answer"],
                "prompt": "Explain SVD.",
                "expected_answer": "U Sigma V transpose.",
            }
        )


def _public_schema_models() -> list[type[BaseModel]]:
    contract_modules = (
        codex_schemas,
        attempts_ai_contracts,
        content_authoring_ai_contracts,
        content_pipeline_ai_contracts,
        content_proposals_ai_contracts,
        content_synthesis_ai_contracts,
        curriculum_ai_contracts,
        diagnosis_ai_contracts,
        reader_ai_contracts,
        tutor_ai_contracts,
    )
    models: set[type[BaseModel]] = set()
    for module in contract_modules:
        models.update(
            obj
            for obj in vars(module).values()
            if inspect.isclass(obj)
            and issubclass(obj, BaseModel)
            and obj.__module__ == module.__name__
            and obj is not codex_schemas.WireModel
        )
    return sorted(
        models,
        key=lambda model: model.__name__,
    )


# Everything strict structured output accepts. Anything outside this set is a
# 400 from the provider before a single token is generated, so the sanitizer
# has to normalize or drop it -- see _strict_json_schema.
_STRICT_SUPPORTED_KEYWORDS = {
    "$defs",
    "$ref",
    "additionalProperties",
    "anyOf",
    "description",
    "enum",
    "items",
    "properties",
    "required",
    "type",
}


@pytest.mark.parametrize("model", _public_schema_models(), ids=lambda model: model.__name__)
def test_every_codex_schema_uses_only_strict_supported_keywords(model):
    """Every public wire schema stays inside the strict structured-output subset.

    Strict structured output rejects any keyword outside this set (for example
    `oneOf`/`discriminator`) at request time, and every object must close
    `additionalProperties` and require all of its properties.
    """

    schema = strict_output_schema(model)

    assert _schema_keys(schema) <= _STRICT_SUPPORTED_KEYWORDS
    assert not _non_strict_objects(schema)


def test_discriminated_target_ref_is_a_flat_nullable_any_of():
    schema = strict_output_schema(GradingProposal)

    target_ref = schema["$defs"]["ErrorAttribution"]["properties"]["target_ref"]
    assert target_ref == {
        "anyOf": [
            {"$ref": "#/$defs/FacetCapabilityTargetRef"},
            {"$ref": "#/$defs/CriterionTargetRef"},
            {"$ref": "#/$defs/ItemStepTargetRef"},
            {"$ref": "#/$defs/AnswerSpanTargetRef"},
            {"$ref": "#/$defs/NoTargetRef"},
            {"type": "null"},
        ]
    }
    # The discriminator survives as the variant's own literal, so Pydantic can
    # still route the response back onto the right member on validation.
    assert schema["$defs"]["NoTargetRef"]["properties"]["kind"] == {
        "enum": ["none"],
        "type": "string",
    }


def test_discriminated_target_ref_still_round_trips_after_sanitizing():
    attribution = ErrorAttribution.model_validate(
        {
            "error_type": "sign_error",
            "evidence": "Dropped the minus sign in step 2.",
            "target_ref": {"kind": "criterion", "criterion_id": "solve"},
        }
    )

    assert attribution.target_ref is not None
    assert attribution.target_ref.kind == "criterion"


# Open-keyed object fields cannot be expressed under strict structured output,
# so they sanitize into objects the provider is forbidden to populate and always
# arrive empty -- silently, with no error from either side. Do not grow this
# set: carry an open-keyed field on the wire as a list of key/value pairs, the
# way EvidenceWeightMap and friends do, so the provider can actually fill it.
#
# Every entry below is an ALREADY-BROKEN field, recorded rather than hidden. The
# `dict[str, X]` arm of the detector was clean; widening it to bare `dict`
# fields (`additionalProperties: true`) exposed these, which are the same F2
# defect -- a field the model is structurally unable to fill, failing closed
# toward "empty" with no error from either side:
#
#   * DepthEdgeInstancePayload -- six of its ten authored fields, i.e. the
#     entire task contract, evidence, freshness and burden of an LLM-authored
#     depth edge. Every instance the provider returns has them empty, so the
#     deterministic gates in ``learnloop.curriculum.depth_edge_authoring`` can
#     only ever see a
#     bare edge_id/milestone/rationale skeleton.
#   * AppendRestructure.payload -- the whole body of a §10.2 restructure item.
#   * PracticeItemPatchPayload.hint_policy, and the `dict` arm of
#     expected_answer (its `str` arm still works, so a structured expected
#     answer is unreachable while a prose one is not).
#
# Fixing them means giving each a declared shape (or an explicit pair-list);
# that touches services outside this change's ownership, so they are pinned
# here to keep the next one from being added silently.
_KNOWN_UNFILLABLE_MAP_FIELDS: set[str] = {
    "AppendRestructure.payload",
    "DepthEdgeInstancePayload.activity_path",
    "DepthEdgeInstancePayload.entry_evidence",
    "DepthEdgeInstancePayload.exit_evidence",
    "DepthEdgeInstancePayload.expected_burden",
    "DepthEdgeInstancePayload.fresh_proof",
    "DepthEdgeInstancePayload.successor_task_contract",
    "PracticeItemPatchPayload.expected_answer",
    "PracticeItemPatchPayload.hint_policy",
}


def _map_field_identity(model: type[BaseModel], path: str) -> str:
    """Collapse a schema path to ``Owner.field``, ignoring where it was reached.

    The same field surfaces under every model that nests it via ``$defs``, and a
    ``dict[str, dict[str, X]]`` surfaces twice within one path.
    """

    _, defs_marker, tail = path.rpartition("/$defs/")
    if not defs_marker:
        tail = f"{model.__name__}{path}"
    name, _, rest = tail.partition("/properties/")
    return f"{name}.{rest.split('/')[0].split('[')[0]}"


def test_weight_maps_travel_as_pairs_and_land_as_maps():
    payload = PracticeItemPatchPayload.model_validate(
        {
            "evidence_facets": ["recall", "numeric"],
            "evidence_weights": [
                {"facet_id": "recall", "weight": 0.6},
                {"facet_id": "numeric", "weight": 0.4},
            ],
            "criterion_facet_weights": [
                {"criterion_id": "solve", "weights": [{"facet_id": "numeric", "weight": 1.0}]}
            ],
        }
    )

    assert payload.evidence_weights == {"recall": 0.6, "numeric": 0.4}
    assert payload.criterion_facet_weights == {"solve": {"numeric": 1.0}}
    # Consumers read the dumped payload, so the map form has to survive the dump.
    assert payload.model_dump(exclude_none=True)["evidence_weights"] == {
        "recall": 0.6,
        "numeric": 0.4,
    }


def test_weight_maps_still_accept_the_legacy_map_form():
    payload = PracticeItemPatchPayload.model_validate(
        {
            "evidence_weights": {"recall": 1.0},
            "criterion_facet_weights": {"solve": {"numeric": 1.0}},
        }
    )

    assert payload.evidence_weights == {"recall": 1.0}
    assert payload.criterion_facet_weights == {"solve": {"numeric": 1.0}}


def test_trace_recipe_dependencies_travel_as_pairs():
    recipe = TraceRecipePayload.model_validate(
        {
            "id": "recipe_1",
            "checkpoints": ["setup", "solve"],
            "dependencies": [{"checkpoint_id": "solve", "depends_on": ["setup"]}],
        }
    )

    assert recipe.dependencies == {"solve": ["setup"]}
    # The contract validator walks dependencies as a map; pairs must reach it
    # already converted or every generated trace contract would fail.
    TraceContractPayload.model_validate({"status": "available", "recipes": [recipe.model_dump()]})


def test_undeclared_wire_field_is_rejected_by_name():
    """An undeclared provider field fails validation and names itself.

    Silently dropping an unknown field (for example ``targets`` on
    ``RubricCriterionPayload``) would discard provider output with no error
    from either side, so the defect would look like a design decision.
    """

    with pytest.raises(ValidationError) as excinfo:
        content_proposals_ai_contracts.RubricCriterionPayload.model_validate(
            {
                "id": "solve",
                "points": 2.0,
                "description": "Solves both branches.",
                "targets_v2": [{"facet": "complex_multiplication"}],
            }
        )

    assert codex_schemas.undeclared_wire_fields(excinfo.value) == ["targets_v2"]
    message = codex_schemas.describe_wire_validation_error(
        content_proposals_ai_contracts.RubricCriterionPayload, excinfo.value
    )
    assert "RubricCriterionPayload" in message
    assert "targets_v2" in message


def test_undeclared_field_inside_a_proposal_item_names_the_payload_model():
    """The union must not bury the diagnosis under six irrelevant failures."""

    with pytest.raises(ValidationError) as excinfo:
        content_proposals_ai_contracts.AuthoringProposalItem.model_validate(
            {
                "client_item_id": "c1",
                "item_type": "practice_item",
                "operation": "create",
                "proposed_entity_id": "pi_1",
                "rationale": "why",
                "review_route": "review_required",
                "payload": {
                    "learning_object_id": "lo_1",
                    "prompt": "Explain SVD.",
                    "difficulty_prior": 0.4,
                },
            }
        )

    message = str(excinfo.value)
    assert "PracticeItemPatchPayload does not declare difficulty_prior" in message


@pytest.mark.parametrize("model", _public_schema_models(), ids=lambda model: model.__name__)
def test_runtime_validation_and_strict_schema_agree_on_what_is_admissible(model):
    """The two halves of one contract, checked against each other.

    ``_strict_json_schema`` stamps ``additionalProperties: false`` onto every
    object it sends the provider; ``WireModel`` forbids extras at validation.
    Before this test the sanitizer *imposed* strictness the model did not
    declare, so the runtime happily accepted-and-discarded a field the wire
    schema forbade. Here every model-backed object must already forbid extras
    on its own, i.e. the sanitizer adds nothing it was not given.
    """

    assert issubclass(model, codex_schemas.WireModel)
    assert model.model_config.get("extra") == "forbid"

    unstrict = [
        path
        for path, node in _object_nodes(model.model_json_schema(), "")
        # `properties` marks a model-backed object; a bare `dict` field has none
        # and is pinned separately by _KNOWN_UNFILLABLE_MAP_FIELDS.
        if "properties" in node and node.get("additionalProperties") is not False
    ]
    assert unstrict == []


def _object_nodes(value: Any, path: str) -> list[tuple[str, dict[str, Any]]]:
    if isinstance(value, list):
        return [
            node for index, item in enumerate(value) for node in _object_nodes(item, f"{path}[{index}]")
        ]
    if not isinstance(value, dict):
        return []
    found: list[tuple[str, dict[str, Any]]] = []
    if value.get("type") == "object" or "properties" in value:
        found.append((path, value))
    for key, child in value.items():
        if key in {"$defs", "properties"} and isinstance(child, dict):
            for name, schema in child.items():
                found.extend(_object_nodes(schema, f"{path}/{key}/{name}"))
            continue
        found.extend(_object_nodes(child, f"{path}/{key}"))
    return found


def test_output_schema_refuses_a_model_outside_the_wire_hierarchy():
    """A non-WireModel would forbid extras on the wire and drop them at runtime."""

    class Loose(BaseModel):
        summary: str = ""

    with pytest.raises(TypeError, match="Loose is not a WireModel"):
        strict_output_schema(Loose)


def test_no_new_open_keyed_map_fields_are_introduced():
    found = {
        _map_field_identity(model, path)
        for model in _public_schema_models()
        for path in map_typed_schema_paths(model)
    }

    assert found == _KNOWN_UNFILLABLE_MAP_FIELDS


def _schema_keys(value: Any) -> set[str]:
    if isinstance(value, list):
        return {key for item in value for key in _schema_keys(item)}
    if not isinstance(value, dict):
        return set()
    keys = set(value)
    for key, child in value.items():
        if key in {"$defs", "properties"} and isinstance(child, dict):
            for schema in child.values():
                keys.update(_schema_keys(schema))
            continue
        keys.update(_schema_keys(child))
    return keys


def _non_strict_objects(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for child in value for item in _non_strict_objects(child)]
    if not isinstance(value, dict):
        return []

    failures: list[dict[str, Any]] = []
    if value.get("type") == "object" or "properties" in value:
        properties = value.get("properties", {})
        if "properties" not in value:
            failures.append(value)
        if value.get("additionalProperties") is not False:
            failures.append(value)
        if set(value.get("required", [])) != set(properties):
            failures.append(value)
    for child in value.values():
        failures.extend(_non_strict_objects(child))
    return failures


def _logged_event(records, event: str) -> dict:
    for record in records:
        if record.getMessage() == event:
            fields = getattr(record, "event_fields", None)
            if isinstance(fields, dict):
                return fields
    raise AssertionError(f"missing log event {event}")


# --- outbound half of the same defect ---------------------------------------
#
# `WireModel` closes the INBOUND direction: a provider field the schema does not
# declare is an error. The prompt/context pair is the same defect one level up
# and in the other direction. Every prompt builder
# ships `asdict(context)` beside prose that names `context.<field>`; the prose
# is a plain string, so a field removed from (or renamed on) the dataclass
# leaves the instruction referring to a key that is no longer in the payload.
# Nothing errors -- the model is simply told to consult something that is not
# there, which is exactly how a dropped `clarification_exchange` desynchronises
# the grading prompt from the grading contract without a single failing call.


def _context_field_references(function) -> set[str]:
    """Every ``context.<name>`` the builder mentions, prose included."""

    source = textwrap.dedent(inspect.getsource(function))
    return set(re.findall(r"context\.([a-z_][a-z0-9_]*)", source))


def _prompt_builders_with_dataclass_contexts() -> list[tuple[str, Any, Any]]:
    from learnloop.attempts.ai_contracts import GradingContext, grading_prompt
    from learnloop.content.authoring.ai_contracts import (
        ConceptAnimationContext,
        ExerciseAuthoringContext,
        concept_animation_prompt,
        exercise_authoring_prompt,
    )
    from learnloop.content.pipeline.ai_contracts import CanonicalIngestContext, canonical_ingest_prompt
    from learnloop.content.proposals.ai_contracts import AuthoringContext, authoring_prompt
    from learnloop.content.synthesis.ai_contracts import (
        AppendReconciliationContext,
        ConceptGraphContext,
        SourceSetSynthesisContext,
        SourceUnitInventoryContext,
        append_reconciliation_prompt,
        concept_graph_structuring_prompt,
        source_set_synthesis_prompt,
        source_unit_inventory_prompt,
    )
    from learnloop.curriculum.ai_contracts import (
        DepthEdgeInstanceContext,
        RungBackfillContext,
        depth_edge_instance_prompt,
        rung_backfill_prompt,
    )
    from learnloop.diagnosis.ai_contracts import (
        MisconceptionMatchContext,
        ProbeDialogueTurnContext,
        ProbeFamilyTrialsContext,
        ProbeInstanceContext,
        misconception_match_prompt,
        probe_dialogue_turn_prompt,
        probe_family_trials_prompt,
        probe_instance_surfaces_prompt,
    )
    from learnloop.reader.ai_contracts import (
        ReaderPresetSynthesisContext,
        ReadingQuickCheckContext,
        reader_preset_synthesis_prompt,
        reading_quick_check_prompt,
    )
    from learnloop.tutor.ai_contracts import (
        PromotionAnalysisContext,
        TeachBackAuthoringContext,
        TeachBackQuestionContext,
        TutorQAContext,
        promotion_analysis_prompt,
        teach_back_authoring_prompt,
        teach_back_question_prompt,
        tutor_qa_prompt,
    )

    return [
        ("append_reconciliation_prompt", append_reconciliation_prompt, AppendReconciliationContext),
        ("authoring_prompt", authoring_prompt, AuthoringContext),
        ("canonical_ingest_prompt", canonical_ingest_prompt, CanonicalIngestContext),
        ("concept_animation_prompt", concept_animation_prompt, ConceptAnimationContext),
        ("concept_graph_structuring_prompt", concept_graph_structuring_prompt, ConceptGraphContext),
        ("depth_edge_instance_prompt", depth_edge_instance_prompt, DepthEdgeInstanceContext),
        ("exercise_authoring_prompt", exercise_authoring_prompt, ExerciseAuthoringContext),
        ("grading_prompt", grading_prompt, GradingContext),
        ("misconception_match_prompt", misconception_match_prompt, MisconceptionMatchContext),
        ("probe_dialogue_turn_prompt", probe_dialogue_turn_prompt, ProbeDialogueTurnContext),
        ("probe_family_trials_prompt", probe_family_trials_prompt, ProbeFamilyTrialsContext),
        ("probe_instance_surfaces_prompt", probe_instance_surfaces_prompt, ProbeInstanceContext),
        ("promotion_analysis_prompt", promotion_analysis_prompt, PromotionAnalysisContext),
        ("reader_preset_synthesis_prompt", reader_preset_synthesis_prompt, ReaderPresetSynthesisContext),
        ("reading_quick_check_prompt", reading_quick_check_prompt, ReadingQuickCheckContext),
        ("rung_backfill_prompt", rung_backfill_prompt, RungBackfillContext),
        ("source_set_synthesis_prompt", source_set_synthesis_prompt, SourceSetSynthesisContext),
        ("source_unit_inventory_prompt", source_unit_inventory_prompt, SourceUnitInventoryContext),
        ("teach_back_authoring_prompt", teach_back_authoring_prompt, TeachBackAuthoringContext),
        ("teach_back_question_prompt", teach_back_question_prompt, TeachBackQuestionContext),
        ("tutor_qa_prompt", tutor_qa_prompt, TutorQAContext),
    ]


@pytest.mark.parametrize(
    "name,function,context_type",
    _prompt_builders_with_dataclass_contexts(),
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_prompt_prose_only_names_context_fields_that_exist(name, function, context_type):
    declared = {f.name for f in dataclasses.fields(context_type)}
    referenced = _context_field_references(function)

    assert referenced <= declared, (
        f"{name} instructs the model to read "
        f"{sorted(referenced - declared)} from {context_type.__name__}, which does not "
        "carry those fields; the prompt and the context have diverged."
    )


