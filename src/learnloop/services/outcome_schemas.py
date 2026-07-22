"""Coarse outcome schemas (spec_p0_measurement_correctness §3.1).

Every card version names an immutable ``(outcome_schema_id, version)``. A schema
holds 3 or 4 mutually exclusive true classes, the same observed-class vocabulary,
and the class->score-fraction map ``EffectiveObservation`` (P0.3) reads. Business
logic lives here; SQL is in ``db/repositories.py`` (§5). Schemas are seeded
idempotently by :func:`ensure_builtin_schemas`, content-addressed on the schema
body so a re-run mints nothing new.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.activities import _canonical_hash, _json

# Builtin schema slugs (§3.1). Version numbers are structural (schema identity),
# not decision parameters.
COARSE_RESPONSE_SLUG = "coarse_response_v1"
COARSE_RESPONSE_UNANSWERED_SLUG = "coarse_response_unanswered_v1"
SIGNATURE_ERROR_SLUG = "signature_error_v1"
CRITERION_4CLASS_SLUG = "criterion_4class_v1"

# The class->score-fraction maps (§3.1). The 0.5 partial fraction and the choice
# that unassessable/signature_error/unanswered contribute no score are decision
# parameters used by EffectiveObservation to weight certification mass.
PARTIAL_SUCCESS_SCORE_FRACTION = 0.5  # decision parameter: heuristic
CRITERION_PARTIAL_SCORE_FRACTION = 0.5  # decision parameter: heuristic
UNASSESSABLE_SCORE_FRACTION = 0.0  # decision parameter: heuristic
SIGNATURE_ERROR_SCORE_FRACTION = 0.0  # decision parameter: heuristic
UNANSWERED_SCORE_FRACTION = 0.0  # decision parameter: heuristic


@dataclass(frozen=True)
class BuiltinSchema:
    slug: str
    kind: str
    version: int
    true_classes: tuple[str, ...]
    observed_classes: tuple[str, ...]
    score_fraction: Mapping[str, float]
    has_signature_error: bool = False
    has_unanswered: bool = False

    def content_payload(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "kind": self.kind,
            "version": self.version,
            "true_classes": list(self.true_classes),
            "observed_classes": list(self.observed_classes),
            "score_fraction": {k: self.score_fraction[k] for k in sorted(self.score_fraction)},
            "has_signature_error": self.has_signature_error,
            "has_unanswered": self.has_unanswered,
        }

    def content_hash(self) -> str:
        return _canonical_hash(self.content_payload())


BUILTIN_SCHEMAS: tuple[BuiltinSchema, ...] = (
    # Default 3-class diagnosis schema.
    BuiltinSchema(
        slug=COARSE_RESPONSE_SLUG,
        kind="response",
        version=1,
        true_classes=("success", "partial_success", "other"),
        observed_classes=("success", "partial_success", "other"),
        score_fraction={
            "success": 1.0,
            "partial_success": PARTIAL_SUCCESS_SCORE_FRACTION,
            "other": 0.0,
        },
    ),
    # Optional +unanswered 4-class variant.
    BuiltinSchema(
        slug=COARSE_RESPONSE_UNANSWERED_SLUG,
        kind="response",
        version=1,
        true_classes=("success", "partial_success", "other", "unanswered"),
        observed_classes=("success", "partial_success", "other", "unanswered"),
        score_fraction={
            "success": 1.0,
            "partial_success": PARTIAL_SUCCESS_SCORE_FRACTION,
            "other": 0.0,
            "unanswered": UNANSWERED_SCORE_FRACTION,
        },
        has_unanswered=True,
    ),
    # Misconception-recognizing variant: partial_success replaced by a
    # card-declared signature_error slot (§3.1).
    BuiltinSchema(
        slug=SIGNATURE_ERROR_SLUG,
        kind="response",
        version=1,
        true_classes=("success", "signature_error", "other"),
        observed_classes=("success", "signature_error", "other"),
        score_fraction={
            "success": 1.0,
            "signature_error": SIGNATURE_ERROR_SCORE_FRACTION,
            "other": 0.0,
        },
        has_signature_error=True,
    ),
    # Certification per-criterion 4-class schema (§3.1).
    BuiltinSchema(
        slug=CRITERION_4CLASS_SLUG,
        kind="criterion",
        version=1,
        true_classes=("full", "partial", "none", "unassessable"),
        observed_classes=("full", "partial", "none", "unassessable"),
        score_fraction={
            "full": 1.0,
            "partial": CRITERION_PARTIAL_SCORE_FRACTION,
            "none": 0.0,
            "unassessable": UNASSESSABLE_SCORE_FRACTION,
        },
    ),
)


def ensure_builtin_schemas(
    repository: Repository, *, clock: Clock | None = None
) -> dict[str, str]:
    """Idempotently seed the builtin outcome schemas (§3.1). Returns slug->version_id."""

    result: dict[str, str] = {}
    for schema in BUILTIN_SCHEMAS:
        schema_id = repository.ensure_outcome_schema(
            slug=schema.slug, kind=schema.kind, clock=clock
        )
        version_id = repository.ensure_outcome_schema_version(
            schema_id=schema_id,
            version=schema.version,
            observed_classes_json=_json(list(schema.observed_classes)),
            true_classes_json=_json(list(schema.true_classes)),
            has_signature_error=schema.has_signature_error,
            has_unanswered=schema.has_unanswered,
            score_fraction_json=_json(
                {k: schema.score_fraction[k] for k in sorted(schema.score_fraction)}
            ),
            content_hash=schema.content_hash(),
            clock=clock,
        )
        result[schema.slug] = version_id
    return result


def resolve_schema_id(repository: Repository, slug: str, *, clock: Clock | None = None) -> tuple[str, int]:
    """Return ``(schema_id, version)`` for a slug, seeding builtins if absent."""

    row = repository.fetch_outcome_schema_version(slug=slug)
    if row is None:
        ensure_builtin_schemas(repository, clock=clock)
        row = repository.fetch_outcome_schema_version(slug=slug)
    if row is None:  # pragma: no cover - defensive
        raise ValueError(f"unknown outcome schema slug: {slug}")
    return row["schema_id"], int(row["version"])
