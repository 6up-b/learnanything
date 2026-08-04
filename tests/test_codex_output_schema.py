from __future__ import annotations

import dataclasses
import inspect
import json
import re
import textwrap
import logging
import sys
import threading
import time
from enum import Enum
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from learnloop.codex.client import (
    AuthoringContext,
    CodexUnavailable,
    CodexTurnTimeout,
    ReaderPresetSynthesisContext,
    SdkCodexClient,
    TeachBackAuthoringContext,
    _codex_output_schema,
    _resolved_sdk_codex_bin,
    map_typed_schema_paths,
)
from learnloop.codex import schemas as codex_schemas
from learnloop.codex.schemas import (
    AuthoringProposal,
    ErrorAttribution,
    GradingProposal,
    PracticeItemPatchPayload,
    ReaderPresetSynthesis,
    TeachBackAuthoring,
    TraceContractPayload,
    TraceRecipePayload,
)
from learnloop.config import CodexConfig


def test_codex_authoring_schema_is_strict_response_format_compatible():
    schema = _codex_output_schema(AuthoringProposal)

    assert schema["additionalProperties"] is False
    assert "default" not in _schema_keys(schema)
    assert "title" not in _schema_keys(schema)
    assert "minimum" not in _schema_keys(schema)
    assert "maximum" not in _schema_keys(schema)
    assert "title" in schema["$defs"]["LearningObjectPatchPayload"]["properties"]
    assert not _non_strict_objects(schema)


def test_codex_grading_schema_is_strict_response_format_compatible():
    schema = _codex_output_schema(GradingProposal)

    assert schema["additionalProperties"] is False
    assert "default" not in _schema_keys(schema)
    assert not _non_strict_objects(schema)


def test_codex_teach_back_authoring_schema_is_strict_response_format_compatible():
    schema = _codex_output_schema(TeachBackAuthoring)

    assert schema["additionalProperties"] is False
    assert "default" not in _schema_keys(schema)
    assert not _non_strict_objects(schema)


def test_append_schema_declares_properties_on_bare_restructure_payload():
    """Regression for the provider's misleading extra-required-key 400.

    A bare ``dict`` has no Pydantic ``properties`` member. Strict Responses
    schemas still require that member, even when it is empty; without it the
    provider rejected the enclosing ``AppendRestructure`` as though its
    required ``payload`` key were not declared.
    """

    schema = _codex_output_schema(codex_schemas.AppendReconciliation)

    assert schema["$defs"]["AppendRestructure"]["properties"]["payload"] == {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }
    assert not _non_strict_objects(schema)


def test_sdk_teach_back_authoring_passes_source_and_quest_to_prompt(tmp_path):
    client = SdkCodexClient(
        CodexConfig(checkout_path=str(tmp_path / "codex")),
        tmp_path,
    )
    captured: dict[str, Any] = {}

    def fake_run_structured(prompt: str, output_schema: dict[str, Any], *, purpose: str) -> str:
        captured.update(prompt=prompt, output_schema=output_schema, purpose=purpose)
        return json.dumps(
            {
                "prompt_md": "Teach how to find both square roots of i.",
                "expected_answer_md": "Explain the Cartesian method.",
                "core_criteria": [
                    {
                        "description": "Explains the Cartesian method.",
                        "source_criterion_ids": ["solve"],
                        "measurement_status": "item_local",
                        "facet_ids": [],
                    }
                ],
                "transfer_criterion": {
                    "description": "Uses the reasoning in signal processing.",
                    "source_criterion_ids": ["solve"],
                    "measurement_status": "supporting",
                    "facet_ids": ["complex_multiplication"],
                },
                "transfer_scenario": "Interpret a phase rotation in signal processing.",
                "quest_connection": "connected",
                "trace_contract": None,
            }
        )

    client._run_structured = fake_run_structured  # type: ignore[method-assign]
    context = TeachBackAuthoringContext(
        source_practice_item_id="pi_roots",
        source_prompt="Find two distinct square roots of i.",
        source_expected_answer="±(1+i)/sqrt(2)",
        source_criteria=[{"id": "solve", "description": "Solves both sign branches."}],
        allowed_facets=[{"id": "complex_multiplication"}],
        learning_object_title="Compute with Complex Numbers",
        quest_sentence="I want to learn complex numbers for signal processing.",
    )

    result = client.run_teach_back_authoring(context)

    assert result.quest_connection == "connected"
    assert captured["purpose"] == "teach_back_authoring"
    payload = json.loads(captured["prompt"].rsplit("\n\n", 1)[1])
    assert payload["context"]["source_prompt"] == context.source_prompt
    assert payload["context"]["quest_sentence"] == context.quest_sentence
    assert "quest may shape ONLY this transfer criterion" in payload["task"]
    assert not _non_strict_objects(captured["output_schema"])


def test_sdk_authoring_path_passes_strict_schema_to_codex(tmp_path):
    checkout = tmp_path / "codex"
    client = SdkCodexClient(CodexConfig(checkout_path=str(checkout)), tmp_path)
    captured: dict[str, Any] = {}

    def fake_run_structured(prompt: str, output_schema: dict[str, Any], *, purpose: str) -> str:
        captured["prompt"] = prompt
        captured["output_schema"] = output_schema
        captured["purpose"] = purpose
        return '{"summary": "ok"}'

    client._run_structured = fake_run_structured  # type: ignore[method-assign]

    proposal = client.run_authoring_proposal(AuthoringContext(vault_root=str(tmp_path), source_ids=[]))

    assert proposal.summary == "ok"
    assert captured["purpose"] == "authoring"
    assert "retrieval_demand" in captured["prompt"]
    assert "repair_targets" in captured["prompt"]
    assert not _non_strict_objects(captured["output_schema"])


def test_sdk_reader_preset_repairs_invalid_unicode_json_once(tmp_path):
    client = SdkCodexClient(
        CodexConfig(checkout_path=str(tmp_path / "codex")),
        tmp_path,
    )
    calls: list[dict[str, Any]] = []
    malformed = (
        '{"content_md":"'
        + ("x" * 990)
        + '\\ud800","span_ids":["s1"]}'
    )
    responses = iter(
        [
            malformed,
            '{"content_md":"Use coordinatewise distributivity.","span_ids":["s1"]}',
        ]
    )

    def fake_run_structured(prompt: str, output_schema: dict[str, Any], *, purpose: str) -> str:
        calls.append({"prompt": prompt, "output_schema": output_schema, "purpose": purpose})
        return next(responses)

    client._run_structured = fake_run_structured  # type: ignore[method-assign]
    selected = r"Show that $(a+b)x = ax + bx$ for all $a,b \in F$ and all $x \in F^n$"

    result = client.run_reader_preset_synthesis(
        ReaderPresetSynthesisContext(
            preset="worked_example",
            selected_text=selected,
            selection_edited=True,
            blocks=[{"span_id": "s1", "text": selected}],
        )
    )

    assert result == ReaderPresetSynthesis(
        content_md="Use coordinatewise distributivity.", span_ids=["s1"]
    )
    assert [call["purpose"] for call in calls] == [
        "reader_preset_synthesis",
        "reader_preset_synthesis_json_repair",
    ]
    payload = json.loads(calls[0]["prompt"].rsplit("\n\n", 1)[1])
    assert payload["context"]["selected_text"] == selected
    assert "escape backslashes" in calls[1]["prompt"]


def test_sdk_reader_preset_regenerates_when_app_server_rejects_hex_escape(tmp_path):
    client = SdkCodexClient(
        CodexConfig(checkout_path=str(tmp_path / "codex")),
        tmp_path,
    )
    calls: list[dict[str, Any]] = []
    responses: list[str | BaseException] = [
        CodexUnavailable("unexpected end of hex escape at line 1 column 1024"),
        '{"content_md":"Apply distributivity coordinatewise.","span_ids":["s1"]}',
    ]

    def fake_run_structured(prompt: str, output_schema: dict[str, Any], *, purpose: str) -> str:
        calls.append({"prompt": prompt, "output_schema": output_schema, "purpose": purpose})
        response = responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response

    client._run_structured = fake_run_structured  # type: ignore[method-assign]
    selected = r"Show that $(a+b)x = ax + bx$ for all $a,b \in F$ and all $x \in F^n$"

    result = client.run_reader_preset_synthesis(
        ReaderPresetSynthesisContext(
            preset="worked_example",
            selected_text=selected,
            selection_edited=True,
            blocks=[{"span_id": "s1", "text": selected}],
        )
    )

    assert result.content_md == "Apply distributivity coordinatewise."
    assert [call["purpose"] for call in calls] == [
        "reader_preset_synthesis",
        "reader_preset_synthesis_json_regenerate",
    ]
    assert r"emit `\\in`" in calls[1]["prompt"]


def test_sdk_runtime_prefers_bundle_and_falls_back_for_source_checkout(
    monkeypatch,
):
    bundled = ModuleType("codex_cli_bin")
    bundled.bundled_codex_path = lambda: "/pinned/codex"  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "codex_cli_bin", bundled)
    assert _resolved_sdk_codex_bin("") is None

    bundled.bundled_codex_path = lambda: (_ for _ in ()).throw(  # type: ignore[attr-defined]
        FileNotFoundError("package metadata absent")
    )
    monkeypatch.setattr("learnloop.codex.client.shutil.which", lambda _name: "/usr/bin/codex")
    assert _resolved_sdk_codex_bin("") == "/usr/bin/codex"
    assert _resolved_sdk_codex_bin("/configured/codex") == "/configured/codex"


def test_sdk_codex_client_logs_full_prompt_and_response(tmp_path, monkeypatch, caplog):
    captured: dict[str, Any] = {}

    class FakeCodex:
        def __init__(self, config):
            captured["app_config"] = config

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def close(self):
            return None

        def thread_start(self, **kwargs):
            captured["thread_start"] = kwargs
            return FakeThread()

    class FakeThread:
        def turn(self, prompt: str, **kwargs):
            captured["run"] = {"prompt": prompt, **kwargs}
            return FakeTurn()

    class FakeTurn:
        def run(self):
            return SimpleNamespace(final_response='{"summary": "ok"}')

        def interrupt(self):
            return None

    class SdkAppConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class ReasoningEffort(Enum):
        low = "low"
        medium = "medium"

    class ReasoningSummary:
        @classmethod
        def model_validate(cls, value):
            return value

    openai_codex = ModuleType("openai_codex")
    openai_codex.Codex = FakeCodex
    openai_codex.CodexConfig = SdkAppConfig
    openai_codex_types = ModuleType("openai_codex.types")
    openai_codex_types.Personality = SimpleNamespace(pragmatic="pragmatic")
    openai_codex_types.ReasoningEffort = ReasoningEffort
    openai_codex_types.ReasoningSummary = ReasoningSummary
    monkeypatch.setitem(sys.modules, "openai_codex", openai_codex)
    monkeypatch.setitem(sys.modules, "openai_codex.types", openai_codex_types)
    caplog.set_level(logging.DEBUG, logger="learnloop.codex.client")

    client = SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex")), tmp_path)
    response = client._run_structured("full prompt body", {"type": "object"}, purpose="grading")

    assert response == '{"summary": "ok"}'
    assert captured["run"]["prompt"] == "full prompt body"
    prompt_log = _logged_event(caplog.records, "codex.prompt")
    response_log = _logged_event(caplog.records, "codex.response")
    assert prompt_log["purpose"] == "grading"
    assert prompt_log["prompt"] == "full prompt body"
    assert prompt_log["output_schema"] == {"type": "object"}
    assert response_log["response"] == '{"summary": "ok"}'


def test_sdk_codex_turn_timeout_interrupts_and_returns(tmp_path, monkeypatch):
    interrupted = threading.Event()

    class FakeCodex:
        def __init__(self, config):
            self.config = config

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.close()

        def close(self):
            interrupted.set()

        def thread_start(self, **_kwargs):
            return FakeThread()

    class FakeThread:
        def turn(self, _prompt: str, **_kwargs):
            return FakeTurn()

    class FakeTurn:
        def run(self):
            interrupted.wait(timeout=2)
            raise RuntimeError("turn stopped")

        def interrupt(self):
            # Simulate an app-server that never answers turn/interrupt. The
            # client's force-close fallback must still release turn.run().
            threading.Event().wait(timeout=2)

    class SdkAppConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class ReasoningEffort(Enum):
        low = "low"

    class ReasoningSummary:
        @classmethod
        def model_validate(cls, value):
            return value

    openai_codex = ModuleType("openai_codex")
    openai_codex.Codex = FakeCodex
    openai_codex.CodexConfig = SdkAppConfig
    openai_codex_types = ModuleType("openai_codex.types")
    openai_codex_types.Personality = SimpleNamespace(pragmatic="pragmatic")
    openai_codex_types.ReasoningEffort = ReasoningEffort
    openai_codex_types.ReasoningSummary = ReasoningSummary
    monkeypatch.setitem(sys.modules, "openai_codex", openai_codex)
    monkeypatch.setitem(sys.modules, "openai_codex.types", openai_codex_types)

    client = SdkCodexClient(
        CodexConfig(checkout_path=str(tmp_path / "codex"), timeout_seconds=0.05),
        tmp_path,
    )
    started = time.monotonic()

    with pytest.raises(CodexTurnTimeout, match="0.05-second deadline"):
        client._run_structured("prompt", {"type": "object"}, purpose="authoring")

    assert interrupted.is_set()
    assert time.monotonic() - started < 1


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
    return sorted(
        (
            obj
            for obj in vars(codex_schemas).values()
            if inspect.isclass(obj)
            and issubclass(obj, BaseModel)
            and obj.__module__ == codex_schemas.__name__
            # WireModel is the empty base, not a payload anyone sends.
            and obj is not codex_schemas.WireModel
        ),
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
    """Guard every schema, not the three that happened to get hand-written tests.

    A discriminated union shipped `oneOf`/`discriminator` into GradingProposal
    and broke every grading call at request time; the per-model tests below all
    passed because none of them looked for composition keywords.
    """

    schema = _codex_output_schema(model)

    assert _schema_keys(schema) <= _STRICT_SUPPORTED_KEYWORDS
    assert not _non_strict_objects(schema)


def test_discriminated_target_ref_is_a_flat_nullable_any_of():
    schema = _codex_output_schema(GradingProposal)

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
#     deterministic gates in services/depth_edge_authoring can only ever see a
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
    """The regression that would have caught F2 at authoring time.

    ``RubricCriterionPayload`` had no ``targets`` field; a provider that emitted
    one had it deleted at validation with no error from either side, and the
    resulting "an item can only ever fill one column" defect read as a design
    decision for 43 attempts. An undeclared field must now name itself.
    """

    with pytest.raises(ValidationError) as excinfo:
        codex_schemas.RubricCriterionPayload.model_validate(
            {
                "id": "solve",
                "points": 2.0,
                "description": "Solves both branches.",
                "targets_v2": [{"facet": "complex_multiplication"}],
            }
        )

    assert codex_schemas.undeclared_wire_fields(excinfo.value) == ["targets_v2"]
    message = codex_schemas.describe_wire_validation_error(
        codex_schemas.RubricCriterionPayload, excinfo.value
    )
    assert "RubricCriterionPayload" in message
    assert "targets_v2" in message


def test_undeclared_field_inside_a_proposal_item_names_the_payload_model():
    """The union must not bury the diagnosis under six irrelevant failures."""

    with pytest.raises(ValidationError) as excinfo:
        codex_schemas.AuthoringProposalItem.model_validate(
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
        _codex_output_schema(Loose)


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
# declare is now an error instead of a silent drop. The prompt/context pair is
# the same defect one level up and in the other direction. Every prompt builder
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
    import learnloop.codex.client as client_module

    builders = []
    for name, function in vars(client_module).items():
        if not (name.startswith("_") and name.endswith("_prompt") and inspect.isfunction(function)):
            continue
        annotation = inspect.signature(function).parameters.get("context")
        if annotation is None:
            continue
        resolved = getattr(client_module, str(annotation.annotation).split(".")[-1], None)
        if resolved is None or not dataclasses.is_dataclass(resolved):
            continue
        builders.append((name, function, resolved))
    return sorted(builders)


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


def test_http_adapter_strips_the_usage_envelope_but_not_a_bad_field():
    """The one legitimate superset on this boundary, and only that one.

    The adapter contract allows a flat response body *and* an opportunistic
    top-level `usage` object, so on the flat shape `usage` is envelope, not
    proposal. Before `extra="forbid"` it was simply deleted here in silence.
    Any other unknown key is a genuine divergence and must say so.
    """

    from learnloop.codex.client import HttpCodexClient

    client = HttpCodexClient(CodexConfig())

    flat = client._validated(
        codex_schemas.MisconceptionMatch,
        {"decision": "new", "misconception_id": None, "usage": {"prompt_tokens": 12}},
        purpose="misconception_match",
    )
    assert flat.decision == "new"

    nested = client._validated(
        codex_schemas.MisconceptionMatch,
        {"proposal": {"decision": "same", "misconception_id": "mc_1"}, "usage": {}},
        purpose="misconception_match",
    )
    assert nested.misconception_id == "mc_1"

    with pytest.raises(CodexUnavailable) as excinfo:
        client._validated(
            codex_schemas.MisconceptionMatch,
            {"decision": "new", "confidence": 0.9},
            purpose="misconception_match",
        )
    assert "MisconceptionMatch does not declare confidence" in str(excinfo.value)
