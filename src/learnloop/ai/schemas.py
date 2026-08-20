from __future__ import annotations

from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    model_validator,
)


# --- the wire contract's runtime half ---------------------------------------
#
# ``ai.strict_schema.strict_output_schema`` stamps ``additionalProperties: false``
# onto every object in the schema handed to the provider. That is one half of a
# contract; ``WireModel`` is the other. Before it existed every model here ran
# pydantic's default ``extra="ignore"``, so the two halves disagreed in the one
# direction that is invisible: the provider was *forbidden* to emit an
# undeclared field on the strict path, and if it emitted one anyway (chat/JSON
# mode, a non-strict profile, a hand-written fixture, a stored payload from a
# newer revision) validation **dropped it without a word**.
#
# ``spec_measurement_efficiency_v1.md`` §2 F2 is the measured cost of that
# silence: ``RubricCriterionPayload`` had no ``targets`` field, models that
# emitted one had it deleted at validation, and the resulting "an item can only
# ever fill one column" defect read as a design decision for 43 attempts.
# Implementation-plan item 6.1 added the field; this class removes the class of
# defect, by making an undeclared field an error at the boundary that saw it.
#
# Every feature-owned wire model inherits it. There is deliberately no opt-out: a
# model that legitimately carries open content declares a ``dict`` FIELD (whose
# contents are unconstrained), never an open model. See
# ``ai.strict_schema.map_typed_schema_paths`` for why even that is not free.


class WireModel(BaseModel):
    """Base for every payload that crosses the provider boundary.

    ``extra="forbid"`` mirrors the ``additionalProperties: false`` that
    ``strict_output_schema`` sends to the provider, so a field the schema does
    not declare is rejected by name instead of being silently discarded.

    Distinct on purpose from :class:`~learnloop.vault.models.VaultModel`, which
    is ``extra="allow"``: a vault row is *our own* persisted state, read back by
    a possibly-older binary, and dropping a field a newer writer added would
    lose the learner's data. A wire payload is the opposite situation — it is
    untrusted input arriving against a schema we just published, so an
    unrecognized key means the contract and the sender have diverged and the
    only safe report is a loud one.
    """

    model_config = ConfigDict(extra="forbid")


#: Pydantic's error ``type`` for a field rejected by ``extra="forbid"``.
EXTRA_FORBIDDEN_ERROR_TYPE = "extra_forbidden"


class UndeclaredWireFieldError(ValueError):
    """A payload carried a field the wire contract does not declare.

    Raised at the boundary that parsed the payload, naming the model and every
    offending path, because "which field" is the entire actionable content of
    the failure — for the human reading the log, and for the bounded repair
    turn that is asked to drop it.
    """

    def __init__(self, model: type[BaseModel], fields: list[str]) -> None:
        self.model_name = model.__name__
        self.fields = list(fields)
        super().__init__(
            f"{self.model_name} does not declare "
            + ", ".join(self.fields)
            + "; the wire contract forbids undeclared fields "
            "(add the field to its feature-owned AI contract or stop emitting it)."
        )


def undeclared_wire_fields(exc: ValidationError) -> list[str]:
    """Dotted paths of every ``extra="forbid"`` rejection inside ``exc``.

    Returns ``[]`` for an ordinary validation failure, so a caller can tell an
    undeclared field (a contract divergence someone must resolve) apart from a
    malformed value (which the repair turn can usually fix on its own).
    """

    paths: list[str] = []
    for error in exc.errors():
        if error.get("type") != EXTRA_FORBIDDEN_ERROR_TYPE:
            continue
        location = ".".join(str(part) for part in error.get("loc", ()))
        if location and location not in paths:
            paths.append(location)
    return paths


def describe_wire_validation_error(model: type[BaseModel], exc: BaseException) -> str:
    """One actionable line for a failed wire parse, naming model and fields."""

    if isinstance(exc, ValidationError):
        undeclared = undeclared_wire_fields(exc)
        if undeclared:
            return str(UndeclaredWireFieldError(model, undeclared))
    return f"{model.__name__} validation failed: {exc}"

class FacetCapabilityTargetRef(WireModel):
    kind: Literal["facet_capability"]
    facet_id: str
    capability: str | None = None


class CriterionTargetRef(WireModel):
    kind: Literal["criterion"]
    criterion_id: str


class ItemStepTargetRef(WireModel):
    kind: Literal["item_step"]
    checkpoint_id: str
    recipe_id: str | None = None


class AnswerSpanTargetRef(WireModel):
    kind: Literal["answer_span"]
    quote: str
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_offsets(self) -> "AnswerSpanTargetRef":
        if (self.char_start is None) != (self.char_end is None):
            raise ValueError("answer-span offsets must be supplied together")
        if (
            self.char_start is not None
            and self.char_end is not None
            and self.char_end < self.char_start
        ):
            raise ValueError("answer-span char_end must be >= char_start")
        return self


class NoTargetRef(WireModel):
    kind: Literal["none"]


AttributionTargetRef = (
    FacetCapabilityTargetRef
    | CriterionTargetRef
    | ItemStepTargetRef
    | AnswerSpanTargetRef
    | NoTargetRef
)

class CandidateCause(WireModel):
    """One free-text candidate explanation of an observed failure.

    ``statement`` is deliberately unconstrained. There is no vocabulary to fit,
    no required stratum, and no validator that can reject a candidate for what
    it *says* — this codebase has been burned repeatedly by content constraints
    on model output (regex recall-coercion, facet lexical anchoring), and causal
    §5.1 is prose-first / taxonomy-after for exactly that reason.

    Diversity is asked for, never enforced. The grading prompt requests the SET
    of candidates in one generation with verbalized relative weights
    (``prior_weight``) and states the norm that two candidates whose
    ``discriminating_predictions`` do not differ are the same candidate and
    should be merged. Fewer than the suggested count is correct output when the
    trace genuinely underdetermines less.

    ``prior_weight`` is a PRIOR, never a measurement. It is normalized
    server-side across the event's candidates and must never be treated as a
    calibrated probability — the same standing rule as
    ``raw_grade_events.model_confidence``, which is never multiplied into
    anything.

    ``mechanism`` is optional and advisory: the post-hoc projection onto
    ``MECHANISM_TAXONOMY`` prefers it when it maps, and falls back to an
    open-set annotation otherwise. It gates nothing.
    """

    statement: str
    cause_scope: Literal[
        "learner_state",
        "transient_execution",
        "interaction_context",
        "item_contract",
        "grader_interpretation",
        "unknown",
    ]
    target_ref: AttributionTargetRef | None = Field(default=None, discriminator="kind")
    #: Verbalized relative plausibility within this event's candidate set. Any
    #: non-negative scale is accepted (the server normalizes); absent means "no
    #: opinion", which normalizes to the set's uniform share.
    prior_weight: float | None = Field(default=None, ge=0.0)
    #: Free-text falsifiable expectations of the form "if this cause is true,
    #: we'd observe X on Y". These are what make two candidates *different*;
    #: the prompt asks for them, nothing validates their content.
    discriminating_predictions: list[str] = Field(default_factory=list)
    #: The model's own optional mechanism label. Advisory input to the post-hoc
    #: projection; an unrecognised value is ignored, never an error.
    mechanism: str | None = None

    @model_validator(mode="after")
    def validate_statement(self) -> "CandidateCause":
        if not self.statement.strip():
            raise ValueError("candidate cause statement cannot be empty")
        return self
