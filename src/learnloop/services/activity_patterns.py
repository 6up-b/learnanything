"""P1 step 2 -- capability aliases, TaskFeatures, and the ActivityPattern registry
(spec_p1_shared_substrate §3.3, §3.4, §3.5).

Three closed contracts land here:

  * the **closed five-capability vocabulary** and its versioned ``capability_aliases``
    registry -- legacy values map to a canonical capability; an unknown value fails
    NEW authoring and remains visible as ``legacy_unmapped`` in replay only (§3.3);
  * the immutable **TaskFeature schema** (§3.4);
  * the curated **ActivityPattern registry** (§3.5) -- a reviewed instructional
    protocol, NOT an LLM prompt. Each version declares its allowed purposes,
    cognitive operation, induced U-035 ``learning_process`` (closed, ROUTING-ONLY),
    capabilities, target kinds, completion/response contract, mint gates, etc.

U-035 routing-only enforcement (§3.5): ``learning_process`` is surfaced in the
"why this activity?" routing DTO (:func:`routing_metadata`) but is categorically
excluded from any evidence/projection input path. :func:`evidence_semantics` -- the
only projection-facing DTO this module exposes -- never carries it, and a test
scans the codebase to assert no evidence/projection module reads the column.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.activities import _canonical_hash, _json

# The closed five-capability vocabulary (§3.3). Every criterion target, blueprint
# component, card contract, observation contribution, and boundary cell uses one.
CAPABILITIES: frozenset[str] = frozenset(
    {"retrieval", "schema_interpretation", "procedure_execution", "method_selection", "coordination"}
)

# The closed cognitive-operation vocabulary (§3.5).
OPERATIONS: frozenset[str] = frozenset(
    {"retrieve", "discriminate", "generate", "compare", "explain", "set_up", "apply", "reflect", "create"}
)

# The closed U-035 induced-learning-process vocabulary (§3.5). ROUTING-ONLY.
LEARNING_PROCESSES: frozenset[str] = frozenset(
    {
        "prior_knowledge_activation",
        "comprehension_monitoring",
        "self_explanation",
        "schema_induction",
        "procedure_compilation",
        "memory_fluency",
        "method_selection",
        "coordination",
        "transfer",
        "reflection",
    }
)

PURPOSES: frozenset[str] = frozenset({"diagnostic", "instructional", "practice", "assessment"})

CALIBRATION_STATUSES: frozenset[str] = frozenset(
    {"heuristic", "simulation_validated", "live_calibrated"}
)

LEGACY_UNMAPPED = "legacy_unmapped"

# Structural version pins (owner decision A / §D). Not tunable knobs.
CAPABILITY_ALIAS_REGISTRY_VERSION = 1
TASK_FEATURE_SCHEMA_VERSION = 1

# The launch TaskFeature schema (§3.4).
_TASK_FEATURE_DIMENSIONS: dict[str, Any] = {
    "complexity": {"kind": "ordinal", "range": [0, 4]},
    "transfer": {"kind": "enum", "values": ["same_context", "near", "far", "novel_combination"]},
    "representation": {
        "kind": "set",
        "values": ["symbolic", "verbal", "diagram", "code", "physical"],
    },
    "response": {
        "kind": "enum",
        "values": ["recognize", "short_constructed", "long_constructed", "structured_steps", "performance"],
    },
    "scaffolding": {"kind": "ordered_enum", "values": ["none", "cue", "partial", "worked"]},
    "time": {"kind": "interval", "unit": "seconds"},
    "tools": {
        "kind": "set",
        "values": ["closed_book", "open_book", "calculator", "code", "references", "collaboration"],
    },
    "span": {"kind": "enum", "values": ["atomic", "single_step", "multi_step", "whole_task"]},
}

# Legacy capability aliases seeded at registry v1 (§3.3). Identity for the five
# canonical values; a handful of pre-P1 synonyms map into the closed vocabulary.
_LEGACY_ALIASES: dict[str, str | None] = {
    **{c: c for c in CAPABILITIES},
    "recall": "retrieval",
    "recognition": "retrieval",
    "interpretation": "schema_interpretation",
    "schema": "schema_interpretation",
    "procedure": "procedure_execution",
    "execution": "procedure_execution",
    "strategy": "method_selection",
    "selection": "method_selection",
    "integration": "coordination",
    "whole_task": "coordination",
}


class InvalidPattern(Exception):
    """A pattern version declared a value outside a closed vocabulary (§3.5, §9.1)."""


class InvalidCoordinationUse(Exception):
    """``coordination`` used outside a blueprint integration component / whole-task
    criterion that cites one (§3.3, §9.1)."""


class UnknownPatternVersion(Exception):
    def __init__(self, pattern_version_id: str):
        super().__init__(f"unknown pattern version: {pattern_version_id}")
        self.pattern_version_id = pattern_version_id


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ActivityPatternVersion:
    id: str
    pattern_id: str
    pattern_slug: str
    version: int
    allowed_purposes: tuple[str, ...]
    operation: str
    learning_process: str  # U-035, routing-only -- NEVER an evidence input.
    allowed_target_kinds: tuple[str, ...]
    allowed_capabilities: tuple[str, ...]
    completion_semantics: dict[str, Any]
    response_contract: dict[str, Any]
    evidence_semantics_by_context: dict[str, Any]
    task_feature_bounds: dict[str, Any]
    variation_axes: dict[str, Any]
    rubric_shape: dict[str, Any]
    mint_gates: dict[str, Any]
    calibration_status: str
    status: str
    content_hash: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Capability alias registry (§3.3)
# ---------------------------------------------------------------------------

def ensure_capability_alias_registry(
    repository: Repository,
    *,
    registry_version: int = CAPABILITY_ALIAS_REGISTRY_VERSION,
    aliases: Mapping[str, str | None] | None = None,
    clock: Clock | None = None,
) -> None:
    """Seed the versioned capability-alias registry (idempotent)."""

    for legacy_value, canonical in (aliases or _LEGACY_ALIASES).items():
        if canonical is not None and canonical not in CAPABILITIES:
            raise InvalidPattern(f"alias maps to unknown capability: {canonical!r}")
        repository.upsert_capability_alias(
            registry_version=registry_version,
            legacy_value=legacy_value,
            canonical=canonical,
            clock=clock,
        )


def map_capability(
    repository: Repository,
    legacy_value: str,
    *,
    registry_version: int = CAPABILITY_ALIAS_REGISTRY_VERSION,
) -> str:
    """Map a legacy capability value to the closed vocabulary (§3.3). A canonical
    value maps to itself; an unknown value returns ``legacy_unmapped`` (it fails NEW
    authoring but stays visible in historical replay)."""

    if legacy_value in CAPABILITIES:
        return legacy_value
    row = repository.capability_alias(registry_version=registry_version, legacy_value=legacy_value)
    if row is None or row["canonical"] is None:
        return LEGACY_UNMAPPED
    return row["canonical"]


def normalize_capabilities(
    repository: Repository,
    values: Iterable[str],
    *,
    registry_version: int = CAPABILITY_ALIAS_REGISTRY_VERSION,
) -> list[str]:
    """Normalize a legacy capability list through the alias registry (§3.3). Used to
    fold ``source_set_synthesis`` recipe-component capabilities into the closed set."""

    return [map_capability(repository, v, registry_version=registry_version) for v in values]


# ---------------------------------------------------------------------------
# TaskFeature schema (§3.4)
# ---------------------------------------------------------------------------

def ensure_builtin_task_feature_schema(
    repository: Repository,
    *,
    schema_slug: str = "p1_launch",
    version: int = TASK_FEATURE_SCHEMA_VERSION,
    clock: Clock | None = None,
) -> str:
    body = {"schema_slug": schema_slug, "version": version, "dimensions": _TASK_FEATURE_DIMENSIONS}
    return repository.ensure_task_feature_schema_version(
        schema_slug=schema_slug,
        version=version,
        dimensions_json=_json(_TASK_FEATURE_DIMENSIONS),
        content_hash=_canonical_hash(body),
        clock=clock,
    )


def validate_task_features(
    repository: Repository, schema_version_id: str, features: Mapping[str, Any]
) -> tuple[bool, list[str]]:
    """Validate a TaskFeature vector against a schema version (§3.4)."""

    schema_row = repository.task_feature_schema_version(schema_version_id)
    if schema_row is None:
        return False, ["unknown task-feature schema version"]
    import json

    dimensions = json.loads(schema_row["dimensions_json"])
    errors: list[str] = []
    for name, value in features.items():
        spec = dimensions.get(name)
        if spec is None:
            errors.append(f"unknown dimension: {name}")
            continue
        kind = spec.get("kind")
        if kind == "ordinal":
            low, high = spec["range"]
            if not isinstance(value, int) or not (low <= value <= high):
                errors.append(f"{name}: {value!r} outside {low}..{high}")
        elif kind in ("enum", "ordered_enum"):
            if value not in spec["values"]:
                errors.append(f"{name}: {value!r} not in {spec['values']}")
        elif kind == "set":
            allowed = set(spec["values"])
            bad = [v for v in (value or []) if v not in allowed]
            if bad:
                errors.append(f"{name}: {bad} not in {spec['values']}")
    return (not errors), errors


# ---------------------------------------------------------------------------
# Pattern registry (§3.5)
# ---------------------------------------------------------------------------

def _validate_pattern_fields(fields: Mapping[str, Any]) -> None:
    purposes = list(fields.get("allowed_purposes") or [])
    if not purposes or any(p not in PURPOSES for p in purposes):
        raise InvalidPattern(f"invalid allowed_purposes: {purposes!r}")
    if fields.get("operation") not in OPERATIONS:
        raise InvalidPattern(f"invalid operation: {fields.get('operation')!r}")
    if fields.get("learning_process") not in LEARNING_PROCESSES:
        raise InvalidPattern(f"invalid learning_process: {fields.get('learning_process')!r}")
    capabilities = list(fields.get("allowed_capabilities") or [])
    bad = [c for c in capabilities if c not in CAPABILITIES]
    if bad:
        # Invalid/unknown capabilities fail new authoring (§9.1).
        raise InvalidPattern(f"invalid capabilities: {bad!r}")
    if "coordination" in capabilities and not fields.get("integration_component"):
        # coordination is valid only for a blueprint integration component or a
        # whole-task criterion that cites one (§3.3, §9.1).
        raise InvalidCoordinationUse(
            "coordination requires an integration_component / whole-task criterion"
        )
    if fields.get("calibration_status") not in CALIBRATION_STATUSES:
        raise InvalidPattern(f"invalid calibration_status: {fields.get('calibration_status')!r}")


def _pattern_content_hash(pattern_slug: str, fields: Mapping[str, Any]) -> str:
    # B8: the content hash deliberately EXCLUDES the version integer so that
    # UNIQUE(pattern_id, content_hash) is a real dedup backstop -- two version integers
    # carrying identical content collide at the storage layer instead of both landing.
    body = {
        "pattern_slug": pattern_slug,
        "allowed_purposes": sorted(fields.get("allowed_purposes") or []),
        "operation": fields.get("operation"),
        "learning_process": fields.get("learning_process"),
        "allowed_target_kinds": sorted(fields.get("allowed_target_kinds") or []),
        "allowed_capabilities": sorted(fields.get("allowed_capabilities") or []),
        "completion_semantics": fields.get("completion_semantics") or {},
        "response_contract": fields.get("response_contract") or {},
        "progression_role": fields.get("progression_role"),
        "prerequisite_evidence": fields.get("prerequisite_evidence") or {},
        "feedback_strategy": fields.get("feedback_strategy") or {},
        "assistance_strategy": fields.get("assistance_strategy") or {},
        "evidence_semantics_by_context": fields.get("evidence_semantics_by_context") or {},
        "task_feature_bounds": fields.get("task_feature_bounds") or {},
        "variation_axes": fields.get("variation_axes") or {},
        "rubric_shape": fields.get("rubric_shape") or {},
        "mint_gates": fields.get("mint_gates") or {},
        "burden_model": fields.get("burden_model") or {},
        "calibration_status": fields.get("calibration_status"),
        "generator_version": fields.get("generator_version"),
    }
    return _canonical_hash(body)


def _fields_to_columns(fields: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "allowed_purposes_json": _json(sorted(fields.get("allowed_purposes") or [])),
        "operation": fields["operation"],
        "learning_process": fields["learning_process"],
        "allowed_target_kinds_json": _json(sorted(fields.get("allowed_target_kinds") or [])),
        "allowed_capabilities_json": _json(sorted(fields.get("allowed_capabilities") or [])),
        "completion_semantics_json": _json(fields.get("completion_semantics") or {}),
        "response_contract_json": _json(fields.get("response_contract") or {}),
        "progression_role": fields.get("progression_role"),
        "prerequisite_evidence_json": _json(fields.get("prerequisite_evidence") or {}),
        "feedback_strategy_json": _json(fields.get("feedback_strategy") or {}),
        "assistance_strategy_json": _json(fields.get("assistance_strategy") or {}),
        "evidence_semantics_by_context_json": _json(fields.get("evidence_semantics_by_context") or {}),
        "task_feature_bounds_json": _json(fields.get("task_feature_bounds") or {}),
        "variation_axes_json": _json(fields.get("variation_axes") or {}),
        "rubric_shape_json": _json(fields.get("rubric_shape") or {}),
        "mint_gates_json": _json(fields.get("mint_gates") or {}),
        "burden_model_json": _json(fields.get("burden_model") or {}),
        "calibration_status": fields["calibration_status"],
        "generator_version": fields.get("generator_version"),
    }


def register_pattern_version(
    repository: Repository,
    *,
    pattern_slug: str,
    fields: Mapping[str, Any],
    status: str = "draft",
    clock: Clock | None = None,
) -> ActivityPatternVersion:
    """Register an immutable, content-addressed pattern version (§3.5). Fails closed
    on any value outside a closed vocabulary and on illegitimate coordination use."""

    _validate_pattern_fields(fields)
    if status not in ("draft", "reviewed", "active", "retired"):
        raise InvalidPattern(f"invalid status: {status!r}")
    pattern_id = repository.ensure_activity_pattern(pattern_slug=pattern_slug, clock=clock)
    existing = repository.activity_pattern_versions()
    versions_for = [v for v in existing if v["pattern_id"] == pattern_id]
    next_version = max((v["version"] for v in versions_for), default=0) + 1
    content_hash = _pattern_content_hash(pattern_slug, fields)
    # Reuse an identical prior version (content-addressed idempotency): the version
    # integer is not part of the hash, so identical content matches regardless of it.
    for prior in versions_for:
        if prior["content_hash"] == content_hash:
            return _load_version(repository, prior["id"])
    result = repository.ensure_activity_pattern_version(
        pattern_id=pattern_id,
        version=next_version,
        content_hash=content_hash,
        fields=_fields_to_columns(fields),
        status=status,
        clock=clock,
    )
    return _row_to_version(dict(result["row"]), pattern_slug)


def review_pattern_version(repository: Repository, *, pattern_version_id: str) -> None:
    repository.set_activity_pattern_version_status(
        pattern_version_id=pattern_version_id, status="reviewed"
    )


def activate_pattern_version(repository: Repository, *, pattern_version_id: str) -> None:
    repository.set_activity_pattern_version_status(
        pattern_version_id=pattern_version_id, status="active"
    )


def list_compatible_patterns(
    repository: Repository,
    *,
    purpose: str,
    target_kind: str | None = None,
    capabilities: Sequence[str] = (),
    status: str = "active",
) -> list[ActivityPatternVersion]:
    """List reviewed/active patterns compatible with a (purpose, target kind,
    capability set). A pattern out-of-bounds for the request is excluded (§3.5)."""

    out: list[ActivityPatternVersion] = []
    for row in repository.activity_pattern_versions(status=status):
        version = _load_version(repository, row["id"])
        if purpose not in version.allowed_purposes:
            continue
        if target_kind is not None and version.allowed_target_kinds and target_kind not in version.allowed_target_kinds:
            continue
        if capabilities and not set(capabilities).issubset(set(version.allowed_capabilities)):
            continue
        out.append(version)
    return out


def candidate_within_bounds(
    version: ActivityPatternVersion,
    *,
    purpose: str | None = None,
    operation: str | None = None,
    capability: str | None = None,
    target_kind: str | None = None,
) -> bool:
    """Fail closed (§3.5): a candidate that invents an operation, capability, target
    kind, or purpose outside the pattern's declared bounds is rejected. An LLM may
    fill declared slots; it may not invent a new operation/evidence rule."""

    if purpose is not None and purpose not in version.allowed_purposes:
        return False
    if operation is not None and operation != version.operation:
        return False
    if capability is not None and capability not in version.allowed_capabilities:
        return False
    if (
        target_kind is not None
        and version.allowed_target_kinds
        and target_kind not in version.allowed_target_kinds
    ):
        return False
    return True


# ---------------------------------------------------------------------------
# DTOs: routing (includes learning_process) vs evidence (never)
# ---------------------------------------------------------------------------

def routing_metadata(version: ActivityPatternVersion) -> dict[str, Any]:
    """The "why this activity?" routing DTO (§3.5). Carries ``learning_process`` --
    controller-side routing metadata stating why this experience is served now."""

    return {
        "pattern_slug": version.pattern_slug,
        "operation": version.operation,
        "learning_process": version.learning_process,
        "progression_role": None,
    }


# The set of evidence/projection-facing keys. ``learning_process`` is DELIBERATELY
# absent (U-035, §3.5): it must never be readable from any evidence/projection input.
_EVIDENCE_INPUT_KEYS: tuple[str, ...] = (
    "pattern_slug",
    "allowed_capabilities",
    "evidence_semantics_by_context",
    "response_contract",
    "completion_semantics",
)


def evidence_semantics(version: ActivityPatternVersion) -> dict[str, Any]:
    """The ONLY projection-facing DTO this module exposes. It never carries
    ``learning_process`` (U-035 routing-only rule, §3.5)."""

    payload = {
        "pattern_slug": version.pattern_slug,
        "allowed_capabilities": list(version.allowed_capabilities),
        "evidence_semantics_by_context": version.evidence_semantics_by_context,
        "response_contract": version.response_contract,
        "completion_semantics": version.completion_semantics,
    }
    assert "learning_process" not in payload  # U-035 guard (§3.5)
    return payload


# ---------------------------------------------------------------------------
# Builtin launch patterns (§3.5)
# ---------------------------------------------------------------------------

def _launch_pattern_defs() -> dict[str, dict[str, Any]]:
    """The reviewed launch patterns (§3.5). Minimal but well-formed declarations;
    the owner reviews/expands them, but they satisfy the closed vocabularies."""

    def base(**over: Any) -> dict[str, Any]:
        d = {
            "allowed_purposes": ["practice"],
            "operation": "retrieve",
            "learning_process": "memory_fluency",
            "allowed_target_kinds": [],
            "allowed_capabilities": ["retrieval"],
            "completion_semantics": {"kind": "single_response"},
            "response_contract": {"form": "short_constructed"},
            "evidence_semantics_by_context": {"cold": "eligible"},
            "task_feature_bounds": {},
            "variation_axes": {},
            "rubric_shape": {"kind": "binary"},
            "mint_gates": {"gates": ["contract_equivalence", "solvability"]},
            "calibration_status": "heuristic",
        }
        d.update(over)
        return d

    return {
        "minimal_retrieval": base(),
        "near_confusable_comparison": base(
            operation="discriminate", learning_process="schema_induction",
            allowed_capabilities=["schema_interpretation"], response_contract={"form": "recognize"},
        ),
        "setup_only": base(
            operation="set_up", learning_process="method_selection",
            allowed_capabilities=["method_selection"], allowed_purposes=["instructional"],
        ),
        "example_study": base(
            operation="explain", learning_process="self_explanation",
            allowed_purposes=["instructional"], allowed_capabilities=["schema_interpretation"],
            response_contract={"form": "long_constructed"},
        ),
        "example_comparison": base(
            operation="compare", learning_process="schema_induction",
            allowed_purposes=["instructional"], allowed_capabilities=["schema_interpretation"],
        ),
        "example_completion": base(
            operation="apply", learning_process="procedure_compilation",
            allowed_purposes=["instructional"], allowed_capabilities=["procedure_execution"],
            response_contract={"form": "structured_steps"},
        ),
        "independent_repair": base(
            operation="apply", learning_process="procedure_compilation",
            allowed_capabilities=["procedure_execution"], response_contract={"form": "structured_steps"},
        ),
        "move_spotting": base(
            operation="discriminate", learning_process="method_selection",
            allowed_capabilities=["method_selection"], response_contract={"form": "recognize"},
        ),
        "whole_task_integration": base(
            operation="create", learning_process="coordination",
            allowed_capabilities=["coordination"], integration_component=True,
            response_contract={"form": "performance"}, task_feature_bounds={"span": ["whole_task"]},
        ),
        "cold_target_assessment": base(
            operation="apply", learning_process="transfer", allowed_purposes=["assessment"],
            allowed_capabilities=["procedure_execution"],
            evidence_semantics_by_context={"cold": "terminal_only"},
        ),
    }


def ensure_builtin_patterns(
    repository: Repository, *, clock: Clock | None = None
) -> dict[str, ActivityPatternVersion]:
    """Seed the reviewed launch patterns (§3.5), idempotent + content-addressed
    (mirrors the P0.2 ``ensure_builtin_schemas`` precedent). Patterns are activated
    so the family construction rule can resolve them."""

    ensure_capability_alias_registry(repository, clock=clock)
    ensure_builtin_task_feature_schema(repository, clock=clock)
    out: dict[str, ActivityPatternVersion] = {}
    for slug, fields in _launch_pattern_defs().items():
        version = register_pattern_version(
            repository, pattern_slug=slug, fields=fields, status="active", clock=clock
        )
        out[slug] = version
    return out


# ---------------------------------------------------------------------------
# Adapter: admitted probe templates -> diagnostic-only patterns (§3.5, §7.3)
# ---------------------------------------------------------------------------

def adapt_probe_template_to_pattern(
    repository: Repository,
    *,
    template_slug: str,
    likelihood_identity: str,
    status: str = "active",
    clock: Clock | None = None,
) -> ActivityPatternVersion:
    """Mirror an admitted probe-family template into a ``diagnostic``-purpose pattern
    without touching the probe rows; the compiled likelihood identity + status remain
    intact on the diagnostic instrument side (§3.5, §7.3)."""

    fields = {
        "allowed_purposes": ["diagnostic"],
        "operation": "discriminate",
        "learning_process": "comprehension_monitoring",
        "allowed_target_kinds": [],
        "allowed_capabilities": ["schema_interpretation"],
        "completion_semantics": {"kind": "probe_response"},
        "response_contract": {"form": "recognize"},
        "evidence_semantics_by_context": {"diagnostic": "frozen_episode_only"},
        "task_feature_bounds": {},
        "variation_axes": {},
        "rubric_shape": {"kind": "ordinal"},
        "mint_gates": {"gates": ["identifiability", "likelihood"]},
        "calibration_status": "heuristic",
        "generator_version": f"probe_adapter:{likelihood_identity}",
    }
    return register_pattern_version(
        repository, pattern_slug=f"probe_diagnostic_{template_slug}", fields=fields,
        status=status, clock=clock,
    )


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def _row_to_version(row: Mapping[str, Any], pattern_slug: str) -> ActivityPatternVersion:
    import json

    def j(key: str) -> Any:
        value = row.get(key)
        return json.loads(value) if value else None

    return ActivityPatternVersion(
        id=row["id"],
        pattern_id=row["pattern_id"],
        pattern_slug=pattern_slug,
        version=row["version"],
        allowed_purposes=tuple(j("allowed_purposes_json") or ()),
        operation=row["operation"],
        learning_process=row["learning_process"],
        allowed_target_kinds=tuple(j("allowed_target_kinds_json") or ()),
        allowed_capabilities=tuple(j("allowed_capabilities_json") or ()),
        completion_semantics=j("completion_semantics_json") or {},
        response_contract=j("response_contract_json") or {},
        evidence_semantics_by_context=j("evidence_semantics_by_context_json") or {},
        task_feature_bounds=j("task_feature_bounds_json") or {},
        variation_axes=j("variation_axes_json") or {},
        rubric_shape=j("rubric_shape_json") or {},
        mint_gates=j("mint_gates_json") or {},
        calibration_status=row["calibration_status"],
        status=row["status"],
        content_hash=row["content_hash"],
    )


def _pattern_slug_for(repository: Repository, pattern_id: str) -> str:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT pattern_slug FROM activity_patterns WHERE id = ?", (pattern_id,)
        ).fetchone()
    return row["pattern_slug"] if row is not None else ""


def _load_version(repository: Repository, pattern_version_id: str) -> ActivityPatternVersion:
    row = repository.activity_pattern_version(pattern_version_id)
    if row is None:
        raise UnknownPatternVersion(pattern_version_id)
    return _row_to_version(row, _pattern_slug_for(repository, row["pattern_id"]))


def load_pattern_version(repository: Repository, pattern_version_id: str) -> ActivityPatternVersion:
    return _load_version(repository, pattern_version_id)
