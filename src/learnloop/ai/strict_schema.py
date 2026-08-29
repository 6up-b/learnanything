"""Strict JSON-schema conversion shared by structured transports."""

from __future__ import annotations

from typing import Any, Iterator

from pydantic import BaseModel

from learnloop.ai.schemas import WireModel

_UNSUPPORTED_STRICT_SCHEMA_KEYS = {
    "default",
    # Tagged unions (`Field(discriminator=...)`) emit `discriminator` + `oneOf`.
    # Strict structured output permits neither; Pydantic still routes on the
    # `kind` literal when the response is validated, so dropping the hint is
    # free. `oneOf` is renamed rather than dropped -- see _strict_json_schema.
    "discriminator",
    "exclusiveMaximum",
    "exclusiveMinimum",
    "format",
    "maxItems",
    "maxLength",
    "maximum",
    "minItems",
    "minLength",
    "minimum",
    "multipleOf",
    "pattern",
    "title",
    "uniqueItems",
}


def strict_output_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Return a schema accepted by Codex's strict Responses API wrapper.

    The gate is the point. ``_strict_json_schema`` forbids undeclared fields on
    the wire; :class:`~learnloop.ai.schemas.WireModel` forbids them at
    validation. Those are two halves of one contract, and for most of this
    module's life they agreed only by luck — a model outside the ``WireModel``
    hierarchy runs ``extra="ignore"``, so the provider would be barred from
    emitting a field that, had it arrived by any non-strict route, would have
    been discarded in silence (``spec_measurement_efficiency_v1.md`` §2 F2).
    Refusing to build a schema for such a model makes the two halves derive
    from a single declaration instead.
    """

    if not (isinstance(model, type) and issubclass(model, WireModel)):
        raise TypeError(
            f"{model.__name__} is not a WireModel, so its strict output schema would "
            "forbid extra fields that its validator silently drops. Inherit "
            "learnloop.ai.schemas.WireModel."
        )
    return _strict_json_schema(model.model_json_schema())


def _strict_json_schema(value: Any) -> Any:
    if isinstance(value, list):
        return [_strict_json_schema(item) for item in value]
    if not isinstance(value, dict):
        return value

    normalized: dict[str, Any] = {}
    for key, child in value.items():
        if key in {"$defs", "properties"} and isinstance(child, dict):
            normalized[key] = {name: _strict_json_schema(schema) for name, schema in child.items()}
            continue
        if key in _UNSUPPORTED_STRICT_SCHEMA_KEYS:
            continue
        if key == "additionalProperties":
            continue
        if key == "oneOf":
            # Tagged unions are `anyOf` for our purposes: the variants are
            # mutually exclusive on their `kind` literal anyway, so nothing
            # ambiguous can match twice.
            key = "anyOf"
            if "anyOf" in value:  # pragma: no cover - Pydantic never emits both
                raise ValueError("cannot normalize a schema carrying both anyOf and oneOf")
        if key == "const":
            # `const` is outside the strict-output keyword allowlist; a
            # single-member `enum` is inside it and validates identically.
            normalized["enum"] = [child]
            continue
        normalized[key] = _strict_json_schema(child)

    _flatten_nested_any_of(normalized)

    if _is_object_schema(normalized):
        # The Responses API's strict-schema validator requires the complete
        # object triplet even for a bare ``dict`` that has no declared keys.
        # Omitting ``properties`` here made a parent field disappear during
        # provider validation while its name remained in the parent's
        # ``required`` list (for example ``AppendRestructure.payload``), which
        # surfaced as the misleading "Extra required key 'payload'" 400.
        properties = normalized.get("properties")
        if not isinstance(properties, dict):
            properties = {}
            normalized["properties"] = properties
        normalized["required"] = list(properties.keys())
        normalized["additionalProperties"] = False

    return normalized


def _flatten_nested_any_of(schema: dict[str, Any]) -> None:
    """Splice ``anyOf`` members that are themselves a bare ``anyOf`` wrapper.

    An optional tagged union arrives as ``anyOf: [{oneOf: [...]}, {null}]``;
    once the inner ``oneOf`` is renamed that leaves a pointless nesting level.
    """

    members = schema.get("anyOf")
    if not isinstance(members, list):
        return
    flattened: list[Any] = []
    for member in members:
        if isinstance(member, dict) and set(member) == {"anyOf"} and isinstance(member["anyOf"], list):
            flattened.extend(member["anyOf"])
            continue
        flattened.append(member)
    schema["anyOf"] = flattened


def map_typed_schema_paths(model: type[BaseModel]) -> list[str]:
    """Locate open-keyed object fields, which strict output cannot express.

    Strict structured output requires ``additionalProperties: false`` on every
    object and has no open-keyed map form, so sanitizing one yields an object
    the provider is forbidden to populate: the field always arrives empty
    instead of erroring. The fields that already ship this way are pinned by a
    test so a new one cannot be added without noticing the limitation. Modeling
    such a field as a list of key/value objects is the way to make it fillable.

    Two shapes qualify, and only the first was detected originally:

    * ``dict[str, X]`` -> ``additionalProperties: {<schema of X>}``;
    * a bare ``dict`` / ``dict[str, Any]`` -> ``additionalProperties: true``.

    The second is the same defect wearing a different keyword — it sanitizes to
    ``{"type": "object", "properties": {}, "required": [],
    "additionalProperties": false}``, an object with no declared properties and
    no permitted extras, so the only value the provider can legally emit is
    ``{}``. ``WireModel``'s
    ``extra="forbid"`` cannot help here: the ban lives on the *model*, and
    these are untyped ``dict`` fields with no model behind them.
    """

    def walk(node: Any, path: str) -> Iterator[str]:
        if isinstance(node, list):
            for index, item in enumerate(node):
                yield from walk(item, f"{path}[{index}]")
            return
        if not isinstance(node, dict):
            return
        extra = node.get("additionalProperties")
        if "properties" not in node and (extra is True or (isinstance(extra, dict) and extra)):
            yield path
        for key, child in node.items():
            if key in {"$defs", "properties"} and isinstance(child, dict):
                for name, schema in child.items():
                    yield from walk(schema, f"{path}/{key}/{name}")
                continue
            yield from walk(child, f"{path}/{key}")

    return sorted(set(walk(model.model_json_schema(), "")))


def _is_object_schema(schema: dict[str, Any]) -> bool:
    schema_type = schema.get("type")
    if schema_type == "object":
        return True
    if isinstance(schema_type, list) and "object" in schema_type:
        return True
    return "properties" in schema

# Temporary private alias for out-of-tree consumers during the namespace
# transition. LearnLoop itself imports the provider-neutral public spelling.
_codex_output_schema = strict_output_schema

__all__ = [
    "_codex_output_schema",
    "_strict_json_schema",
    "map_typed_schema_paths",
    "strict_output_schema",
]
