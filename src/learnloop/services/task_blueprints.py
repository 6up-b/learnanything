"""P2 step 1 -- reviewed, immutable TaskBlueprint versions
(spec_p2_narrow_golden_path §3.1, §3.2, §12.1; migration 081).

A TaskBlueprintVersion is the human-reviewed contract for ONE chapter/unit and ONE
target family (invariant 1). This module mirrors the P1 activity-pattern
register->review->activate triad exactly (activity_patterns.py:341/376/382): a draft
is registered content-addressed, an owner reviews it, and only a reviewed version may
be activated by the atomic confirmation. Every step is an append-only review event
(U-034 artifacts-not-API-calls). No LLM runs on any hot path -- blueprint drafting is a
reviewable artifact produced offline (a deterministic stub in tests).

This is NOT a measurement engine: it stores a reviewed contract, it never mints a
posterior, FSRS write, or certification.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.activities import _canonical_hash, _json

BLUEPRINT_SPEC_SCHEMA_VERSION = 1

# The closed P1 capability vocabulary (schemas.SynthRecipeComponent.capability).
CAPABILITY_VOCAB: frozenset[str] = frozenset(
    {"retrieval", "schema_interpretation", "procedure_execution", "method_selection", "coordination"}
)


class InvalidBlueprint(Exception):
    """A blueprint spec violates the one-chapter/one-family invariant or references a
    capability outside the closed P1 vocabulary (§1.2 invariant 1, §12.1)."""


@dataclass(frozen=True)
class ExemplarCandidate:
    """A source object / inventory exercise proposed as a target exemplar (§3.1)."""

    exemplar_ref: str
    unit_id: str
    statement: str
    family_key: str
    practice_eligible: bool
    assessment_eligible: bool
    extraction_health: str = "ok"
    detail: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BlueprintVersion:
    """A registered/reviewed/active immutable blueprint version."""

    id: str
    blueprint_id: str
    version: int
    status: str
    content_hash: str
    canonical_hash: str
    spec: dict[str, Any]
    exemplars: tuple[dict[str, Any], ...] = ()
    minted: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# One-unit / one-family validation (§1.2 invariant 1)
# ---------------------------------------------------------------------------

def validate_single_unit(spec: Mapping[str, Any]) -> None:
    """Reject a mixed-unit or multi-family blueprint before it can validate (§12.1)."""

    source_rev = spec.get("source_rev")
    unit_id = spec.get("unit_id")
    family_key = spec.get("family_key")
    if not source_rev or not unit_id or not family_key:
        raise InvalidBlueprint("blueprint must pin one source_rev, unit_id, and family_key")

    exemplars = spec.get("exemplars") or []
    if not exemplars:
        raise InvalidBlueprint("blueprint must name at least one exemplar")
    for ex in exemplars:
        if ex.get("unit_id", unit_id) != unit_id:
            raise InvalidBlueprint(
                f"exemplar {ex.get('exemplar_ref')!r} is outside unit {unit_id!r} (mixed-unit)"
            )
        fam = ex.get("family_key", family_key)
        if fam != family_key:
            raise InvalidBlueprint(
                f"exemplar {ex.get('exemplar_ref')!r} is family {fam!r}, not {family_key!r} (multi-family)"
            )

    # Every declared solution-recipe capability must be in the closed P1 vocabulary.
    for recipe in spec.get("solution_recipes") or []:
        for slot in ("all_of", "any_of"):
            for comp in recipe.get(slot) or []:
                cap = comp.get("capability")
                if cap is not None and cap not in CAPABILITY_VOCAB:
                    raise InvalidBlueprint(f"capability {cap!r} outside closed P1 vocabulary")
        integ = recipe.get("integration")
        if integ is not None:
            cap = integ.get("capability")
            if cap is not None and cap not in CAPABILITY_VOCAB:
                raise InvalidBlueprint(f"integration capability {cap!r} outside vocabulary")


def _canonicalize_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    body = dict(spec)
    body.setdefault("schema_version", BLUEPRINT_SPEC_SCHEMA_VERSION)
    return body


def _exemplar_rows(spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ex in spec.get("exemplars") or []:
        held_out = bool(ex.get("held_out"))
        rows.append(
            {
                "exemplar_ref": ex["exemplar_ref"],
                "weight": float(ex.get("weight", 1.0)),
                # invariant 4 / §12.1: a selected exemplar is a familiar anchor with
                # ZERO held-out weight -- it can never be labeled held out.
                "exposure_status": "unseen_sibling" if held_out else "familiar_anchor",
                "held_out_weight": float(ex.get("held_out_weight", 0.0)) if held_out else 0.0,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Discover -> register -> review -> activate
# ---------------------------------------------------------------------------

def discover_exemplar_candidates(
    candidates: Sequence[Mapping[str, Any]],
    *,
    unit_id: str,
    family_key: str,
) -> list[ExemplarCandidate]:
    """Project reviewed inventory exercise rows into exemplar candidates within one
    unit (§3.1). Composition-only: the caller supplies inventory rows (from
    ``source_unit_inventory``); this filters/normalizes -- it invents no extractor."""

    out: list[ExemplarCandidate] = []
    for row in candidates:
        if row.get("unit_id", unit_id) != unit_id:
            continue
        out.append(
            ExemplarCandidate(
                exemplar_ref=row["exemplar_ref"],
                unit_id=unit_id,
                statement=row.get("statement", ""),
                family_key=row.get("family_key", family_key),
                practice_eligible=bool(row.get("practice_eligible", True)),
                assessment_eligible=bool(row.get("assessment_eligible", True)),
                extraction_health=row.get("extraction_health", "ok"),
                detail=dict(row.get("detail") or {}),
            )
        )
    return out


def register_blueprint_version(
    repository: Repository,
    *,
    blueprint_slug: str,
    spec: Mapping[str, Any],
    authoring_version: str = "stub-1",
    model_version: str | None = None,
    provenance_version: str = "owner-review-1",
    author: str = "owner",
    clock: Clock | None = None,
) -> BlueprintVersion:
    """Register an immutable content-addressed draft blueprint version (§3.2). Fails
    closed on a mixed-unit/multi-family spec. Idempotent on content hash."""

    validate_single_unit(spec)
    body = _canonicalize_spec(spec)
    content_hash = _canonical_hash(body)
    canonical_hash = content_hash
    blueprint_id = repository.ensure_task_blueprint(
        blueprint_slug=blueprint_slug,
        source_rev=body["source_rev"],
        unit_id=body["unit_id"],
        family_key=body["family_key"],
        clock=clock,
    )
    result = repository.register_task_blueprint_version(
        blueprint_id=blueprint_id,
        spec_json=_json(body),
        content_hash=content_hash,
        canonical_hash=canonical_hash,
        authoring_version=authoring_version,
        model_version=model_version,
        provenance_version=provenance_version,
        exemplars=_exemplar_rows(body),
        detail_json=_json({"exemplar_count": len(body.get("exemplars") or [])}),
        author=author,
        clock=clock,
    )
    return _load_version(repository, result["version"]["id"], minted=not result["already_exists"])


def review_blueprint_version(
    repository: Repository,
    *,
    blueprint_version_id: str,
    checks: Mapping[str, Any] | None = None,
    author: str = "owner",
    clock: Clock | None = None,
) -> BlueprintVersion:
    """Owner marks the version reviewed (§3.2 seven checks captured as the artifact)."""

    repository.transition_task_blueprint_version(
        blueprint_version_id=blueprint_version_id,
        status="reviewed",
        event_kind="reviewed",
        detail_json=_json(dict(checks)) if checks else None,
        author=author,
        clock=clock,
    )
    return _load_version(repository, blueprint_version_id)


def activate_blueprint_version(
    repository: Repository,
    *,
    blueprint_version_id: str,
    author: str = "owner",
    clock: Clock | None = None,
) -> BlueprintVersion:
    """Activate a reviewed version. (The atomic confirmation activates it too, inside
    its transaction; this is the standalone owner affordance.)"""

    version = repository.task_blueprint_version(blueprint_version_id)
    if version is None or version["status"] not in ("reviewed", "active"):
        raise InvalidBlueprint(
            f"cannot activate blueprint version in status "
            f"{version['status'] if version else None!r}"
        )
    if version["status"] == "reviewed":
        repository.transition_task_blueprint_version(
            blueprint_version_id=blueprint_version_id,
            status="active",
            event_kind="activated",
            author=author,
            clock=clock,
        )
    return _load_version(repository, blueprint_version_id)


def place_reading_question(
    repository: Repository,
    *,
    blueprint_version_id: str,
    placement: Mapping[str, Any],
    author: str = "owner",
    clock: Clock | None = None,
) -> str:
    """Record an owner-placed reading question at a section boundary as a blueprint
    review artifact (§7.6, U-033). Placement is a reviewed, static part of the
    blueprint -- there is no ask_now planner or density policy in this cut."""

    return repository.append_task_blueprint_review_event(
        blueprint_version_id=blueprint_version_id,
        kind="reading_question_placed",
        detail_json=_json(dict(placement)),
        author=author,
        clock=clock,
    )


def _load_version(repository: Repository, version_id: str, *, minted: bool = True) -> BlueprintVersion:
    row = repository.task_blueprint_version(version_id)
    if row is None:
        raise InvalidBlueprint(f"unknown blueprint version: {version_id}")
    import json as _json_mod

    exemplars = tuple(repository.target_exemplars_for(version_id))
    return BlueprintVersion(
        id=row["id"],
        blueprint_id=row["blueprint_id"],
        version=row["version"],
        status=row["status"],
        content_hash=row["content_hash"],
        canonical_hash=row["canonical_hash"],
        spec=_json_mod.loads(row["spec_json"]),
        exemplars=exemplars,
        minted=minted,
    )
