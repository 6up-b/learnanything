"""Config fields arc C retired, kept only for the identities that hashed them.

Arc C (``docs/specs/refactor_strategy_v3.md`` §2.1, §2.5) removed config fields nothing read, under the rule that a
deletion changes nothing at a fixed input. A few places hash a config section into an identity that is compared
later: the synthesis manifest, whose hash is the completed-run cache key (``content.synthesis``), and the
predictors' version hashes (forecast version labels, the valuation state hash that keys a VOI receipt, the eval
harness's arm hashes). Removing a field changed such a hash at a fixed input: a completed run was no longer reused,
so a paid generation started again, and an unchanged predictor read as a new version (Codex review of arc C,
finding 1; ``docs/reviews/arcC-review-fixes.md``). Those sites dump through :func:`identity_dump`, which puts every
retired field back with the value the code before arc C would have dumped: what the model's input set (each model
here remembers it when validated) or the recorded default.

The models do not get the fields back: nothing reads them, an old config's value changes no behaviour, and only an
identity dump shows them. Never list a field here that something should read. A stored payload or a provenance-only
hash (a report's ``config_hash``, a plan row, a receipt) dumps the live model and does not come here.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache
from typing import Any, TypeVar

from pydantic import BaseModel, PrivateAttr, TypeAdapter, ValidationError, model_validator


@dataclass(frozen=True)
class RetiredField:
    """A removed field: the model class it lived on, its path there (two names for a leaf of a removed section),
    its type and default there, and the arc C step that removed it."""

    model: str
    path: tuple[str, ...]
    annotation: Any
    default: Any
    removed_by: str


#: Every retired field an identity dump still carries, with its type and default at ``88607cb3fe`` (arc C's base).
RETIRED_FIELDS: tuple[RetiredField, ...] = (
    RetiredField("FacetIdentityConfig", ("merge_locked_facets",), bool, True, "C3"),
    RetiredField("PlanConfig", ("pre_questions",), int, 3, "C3"),
    RetiredField("MasteryIRTConfig", ("discrimination_min",), float, 0.2, "C3"),
    RetiredField("MasteryIRTConfig", ("discrimination_max",), float, 3.0, "C3"),
    # The built-in ``arithmetic_slip`` example set it at construction (``remembering``).
    RetiredField("SeverityExampleConfig", ("target_error_type",), str | None, None, "C3"),
    # The built-in ``recall_failure`` and ``scaffold_failure`` impacts set -0.05 at construction.
    RetiredField("ErrorImpact", ("lo_mastery_delta",), float, 0.0, "C3"),
    # ``LocksConfig``, the whole ``[locks]`` section.
    RetiredField("LearnLoopConfig", ("locks", "facet_lock_mass"), float, 2.0, "C3"),
    RetiredField("LearnLoopConfig", ("locks", "facet_surface_groups"), int, 2, "C3"),
    RetiredField("AIConfig", ("agent_harness_opt_in",), bool, False, "C4"),
)

_BY_MODEL: dict[str, tuple[RetiredField, ...]] = {}
for _field in RETIRED_FIELDS:
    _BY_MODEL[_field.model] = (*_BY_MODEL.get(_field.model, ()), _field)

_MISSING = object()
_Model = TypeVar("_Model", bound="KeepsRetiredFields")


@cache
def _adapter(annotation: Any) -> TypeAdapter[Any]:
    return TypeAdapter(annotation)


def _coerce(field: RetiredField, raw: Any) -> Any:
    """``raw`` as the removed field read it (lax pydantic validation of its old type), JSON-safe."""

    try:
        return _adapter(field.annotation).validate_python(raw)
    except ValidationError:
        # The old model refused this value, so no identity was ever recorded with it.
        return field.default


def _given(data: Any, path: tuple[str, ...]) -> Any:
    for key in path:
        if not isinstance(data, Mapping) or key not in data:
            return _MISSING
        data = data[key]
    return data


class KeepsRetiredFields(BaseModel):
    """A config model some of whose fields arc C retired (:data:`RETIRED_FIELDS`).

    Validation remembers what the input gave each retired field, or its default, for :func:`identity_dump` only:
    nothing else reads it and no other dump shows it. An instance validated again keeps its own values.
    """

    _retired_values: dict[tuple[str, ...], Any] = PrivateAttr(default_factory=dict)

    @model_validator(mode="wrap")
    @classmethod
    def _remember_retired_values(cls, data: Any, handler: Any) -> Any:
        model = handler(data)
        if isinstance(model, KeepsRetiredFields) and model is not data:
            model._retired_values = {
                field.path: field.default if (raw := _given(data, field.path)) is _MISSING else _coerce(field, raw)
                for field in _BY_MODEL.get(type(model).__name__, ())
            }
        return model


def remembering(model: _Model, **values: Any) -> _Model:
    """``model``, remembering ``values`` for its retired fields as if its input had set them: a built-in default
    that set one at construction before arc C (the ``recall_failure`` impact's ``lo_mastery_delta``)."""

    fields = {field.path: field for field in _BY_MODEL.get(type(model).__name__, ())}
    for name, value in values.items():
        field = fields[(name,)]
        model._retired_values[field.path] = _coerce(field, value)
    return model


def identity_dump(model: BaseModel) -> dict[str, Any]:
    """``model.model_dump(mode="json")`` with every retired field under it put back, for a hash that is compared.

    At a fixed input it is the dump the code before arc C wrote: removing a field must not orphan a cache entry or
    an identity (every caller hashes sorted JSON, so where a field goes back in the dict does not matter).
    """

    dump = model.model_dump(mode="json")
    _put_back(model, dump)
    return dump


def identity_view(model: BaseModel, fields: tuple[str, ...]) -> dict[str, Any]:
    """The named ``fields`` of :func:`identity_dump`: an explicit identity view of a flat config section.

    A field added to the model later stays out of the identity until a view names it on purpose. A named field
    that is removed must go into :data:`RETIRED_FIELDS` (``identity_dump`` puts it back); until then this raises,
    so the removal cannot move a compared hash silently. Listing every field a section had when its identity was
    first recorded keeps the bytes: the view equals the whole dump at that point (``tests/test_identity_pins.py``).
    """

    dump = identity_dump(model)
    missing = [name for name in fields if name not in dump]
    if missing:
        raise KeyError(f"{type(model).__name__} no longer has {missing}, which an identity hashes: add them to "
                       "config.retired.RETIRED_FIELDS (keep the bytes) or drop them from the view on purpose")
    return {name: dump[name] for name in fields}


def _put_back(model: BaseModel, dump: dict[str, Any]) -> None:
    for name in type(model).model_fields:
        if name in dump:
            _descend(getattr(model, name), dump[name])
    fields = _BY_MODEL.get(type(model).__name__, ())
    remembered = model._retired_values if isinstance(model, KeepsRetiredFields) else {}
    # A removed section is rebuilt whole: the code before arc C dumped exactly its fields (an old table's
    # unknown keys, kept now as an unread extra, were dropped then).
    for section in {field.path[0] for field in fields if len(field.path) > 1}:
        dump[section] = {}
    for field in fields:
        node = dump
        for key in field.path[:-1]:
            node = node[key]
        node[field.path[-1]] = remembered.get(field.path, field.default)


def _descend(value: Any, node: Any) -> None:
    if isinstance(value, BaseModel) and isinstance(node, dict):
        _put_back(value, node)
    elif isinstance(value, Mapping) and isinstance(node, dict):
        for key, child in value.items():
            if key in node:
                _descend(child, node[key])
    elif isinstance(value, list | tuple) and isinstance(node, list):
        for child, child_node in zip(value, node, strict=False):
            _descend(child, child_node)


__all__ = ["RETIRED_FIELDS", "KeepsRetiredFields", "RetiredField", "identity_dump", "identity_view", "remembering"]
