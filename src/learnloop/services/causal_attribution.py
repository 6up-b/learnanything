"""Causal-attribution records, structural repair, and learner reports.

P0 established honest attribution axes and the learner-report channel.  P1
materializes those immutable observations into versioned causal hypotheses and
an attempt-scoped diagnosis receipt without granting a single model response
durable-belief or negative-facet authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Literal
from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.capability_mapping import (
    CriterionOutcome,
    localize_criterion_outcomes,
)
from learnloop.vault.models import LoadedVault

SELF_REPORT_REASONS = frozenset(
    {
        "slipped",
        "believed_candidate",
        "item_unclear",
        "notation_confused",
        "other_valid_approach",
        "diagnosis_wrong",
    }
)

_NORMALIZE_RE = re.compile(r"\W+")

PERMITTED_USES = frozenset(
    {
        "learner_feedback",
        "routing",
        "probe_selection",
        "durable_belief",
        "facet_negative_evidence",
    }
)
SINGLE_ATTEMPT_USES = (
    "learner_feedback",
    "routing",
    "probe_selection",
)
REPAIR_POLICY_VERSION = "structural_lexicographic_v1"
VERIFICATION_STATUSES = frozenset(
    {
        "verified",
        "contradicted",
        "unsupported",
        "parse_failed",
        "assumption_missing",
    }
)


def _content_id(prefix: str, value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(encoded).hexdigest()[:26]}"


@dataclass(frozen=True)
class VerificationResult:
    """Typed deterministic-verifier output; no boolean authority laundering."""

    status: Literal[
        "verified",
        "contradicted",
        "unsupported",
        "parse_failed",
        "assumption_missing",
    ]
    parsed_form: Any = None
    assumptions: tuple[str, ...] = ()
    discrimination_features: dict[str, Any] = field(default_factory=dict)
    detail: str | None = None

    def __post_init__(self) -> None:
        if self.status not in VERIFICATION_STATUSES:
            raise ValueError(f"unknown verification status {self.status!r}")
        if not self.discrimination_features:
            object.__setattr__(
                self,
                "discrimination_features",
                {"unparsed": self.status in {"unsupported", "parse_failed"}},
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "parsed_form": self.parsed_form,
            "assumptions": list(self.assumptions),
            "discrimination_features": dict(self.discrimination_features),
            "detail": self.detail,
        }


@dataclass(frozen=True)
class RepairValidationResult:
    """Validator-owned structural and deterministic-verification outcome."""

    status: Literal["valid", "invalid", "incomplete"]
    reasons: tuple[str, ...]
    structural_checks: dict[str, bool]
    verification: VerificationResult

    def as_dict(self) -> dict[str, Any]:
        body = {
            "status": self.status,
            "reasons": list(self.reasons),
            "structural_checks": dict(self.structural_checks),
            "verification": self.verification.as_dict(),
        }
        return {
            "id": _content_id("rv", body),
            "authority": "learnloop_validator",
            **body,
        }


class SympyVerifierAdapter:
    """Small P1 CAS adapter for equality checks.

    Import is deliberately lazy: environments without the optional/transitive
    SymPy install receive ``unsupported`` rather than a fabricated verdict.
    """

    def verify(
        self,
        observed_expression: str,
        expected_expression: str,
        *,
        assumptions: tuple[str, ...] = (),
        required_assumptions: tuple[str, ...] = (),
    ) -> VerificationResult:
        missing = sorted(set(required_assumptions) - set(assumptions))
        if missing:
            return VerificationResult(
                "assumption_missing",
                assumptions=assumptions,
                detail="missing assumptions: " + ", ".join(missing),
            )
        try:
            import sympy
        except ImportError:
            return VerificationResult(
                "unsupported",
                assumptions=assumptions,
                detail="sympy is unavailable",
            )
        try:
            observed = sympy.sympify(observed_expression)
            expected = sympy.sympify(expected_expression)
        except (TypeError, ValueError, SyntaxError, sympy.SympifyError) as exc:
            return VerificationResult(
                "parse_failed",
                assumptions=assumptions,
                detail=str(exc),
            )
        difference = sympy.simplify(observed - expected)
        parsed = {
            "observed": str(observed),
            "expected": str(expected),
            "difference": str(difference),
        }
        return VerificationResult(
            "verified" if difference == 0 else "contradicted",
            parsed_form=parsed,
            assumptions=assumptions,
            discrimination_features={"unparsed": False},
        )


class TestExecutionVerifierAdapter:
    """Typed adapter over an already-sandboxed test-execution result."""

    def verify(
        self,
        *,
        returncode: int | None,
        tests_collected: int,
        parsed_form: Any = None,
        assumptions: tuple[str, ...] = (),
    ) -> VerificationResult:
        if returncode is None:
            return VerificationResult(
                "unsupported",
                parsed_form=parsed_form,
                assumptions=assumptions,
                detail="test execution was unavailable",
            )
        if tests_collected <= 0:
            return VerificationResult(
                "assumption_missing",
                parsed_form=parsed_form,
                assumptions=assumptions,
                detail="no tests were collected",
            )
        return VerificationResult(
            "verified" if returncode == 0 else "contradicted",
            parsed_form=parsed_form,
            assumptions=assumptions,
            discrimination_features={
                "unparsed": parsed_form is None,
                "tests_collected": tests_collected,
            },
        )


def validate_repair_candidate(
    suggestion: dict[str, Any],
    *,
    expected_answer: str | dict[str, Any] | None = None,
) -> RepairValidationResult:
    """Validate a repair without trusting any verdict supplied in its payload."""

    repair_class = _repair_class(suggestion)
    trace_value = suggestion.get("repaired_trace")
    trace = trace_value if isinstance(trace_value, dict) else None
    structural_checks = {
        "operator_declared": bool(str(suggestion.get("operator") or "").strip()),
        "target_declared": bool(repair_class["target_refs"]),
        "trace_present": trace is not None,
        "minimal_edit_declared": bool(
            trace is not None
            and str(trace.get("minimal_edit") or "").strip()
        ),
        "repaired_answer_declared": bool(
            trace is not None
            and str(trace.get("repaired_answer_md") or "").strip()
        ),
        "latent_changes_accounted": bool(
            trace is not None and "changed_latent_claims" in trace
        ),
        "checkpoint_changes_accounted": bool(
            trace is not None and "changed_checkpoint_ids" in trace
        ),
    }
    reasons = [
        f"incomplete_{name}"
        for name, passed in structural_checks.items()
        if not passed
    ]
    verification_request = suggestion.get("verification_request")
    verification_request = (
        verification_request
        if isinstance(verification_request, dict)
        else None
    )
    verification = VerificationResult(
        "unsupported",
        detail="no deterministic verification was requested",
    )
    if verification_request is not None and trace is not None:
        kind = str(verification_request.get("kind") or "")
        repaired_answer = str(trace.get("repaired_answer_md") or "")
        assumptions = tuple(
            str(value)
            for value in verification_request.get("assumptions") or []
        )
        required_assumptions = tuple(
            str(value)
            for value in verification_request.get("required_assumptions")
            or []
        )
        if not isinstance(expected_answer, str):
            verification = VerificationResult(
                "unsupported",
                assumptions=assumptions,
                detail="the authored expected answer is not a verifiable string",
            )
        elif kind == "symbolic_equality":
            verification = SympyVerifierAdapter().verify(
                repaired_answer,
                expected_answer,
                assumptions=assumptions,
                required_assumptions=required_assumptions,
            )
        elif kind == "exact_match":
            verification = VerificationResult(
                (
                    "verified"
                    if repaired_answer.strip() == expected_answer.strip()
                    else "contradicted"
                ),
                parsed_form={
                    "observed": repaired_answer.strip(),
                    "expected": expected_answer.strip(),
                },
                assumptions=assumptions,
                discrimination_features={"unparsed": False},
            )
        else:
            verification = VerificationResult(
                "unsupported",
                assumptions=assumptions,
                detail="unknown deterministic verifier request",
            )
    if verification.status == "contradicted":
        reasons.append("deterministic_verifier_contradiction")
    if reasons:
        status: Literal["valid", "invalid", "incomplete"] = (
            "invalid"
            if verification.status == "contradicted"
            else "incomplete"
        )
    else:
        status = "valid"
    return RepairValidationResult(
        status=status,
        reasons=tuple(reasons),
        structural_checks=structural_checks,
        verification=verification,
    )


def _ref_key(ref: Any) -> str:
    if not isinstance(ref, dict):
        return ""
    if ref.get("kind") == "facet_capability":
        return f"facet_capability:{ref.get('facet_id')}"
    if ref.get("kind") == "criterion":
        return f"criterion:{ref.get('criterion_id')}"
    if ref.get("kind") == "item_step":
        return (
            f"item_step:{ref.get('recipe_id') or '*'}:"
            f"{ref.get('checkpoint_id')}"
        )
    return json.dumps(ref, sort_keys=True, separators=(",", ":"), default=str)


def _trace_edit_cost(before: str, after: str) -> int:
    cost = 0
    for tag, start_a, end_a, start_b, end_b in SequenceMatcher(
        None, before, after
    ).get_opcodes():
        if tag != "equal":
            cost += max(end_a - start_a, end_b - start_b)
    return cost


def _repair_class(
    suggestion: dict[str, Any],
    *,
    episode_id: str | None = None,
    repair_policy_version: str = REPAIR_POLICY_VERSION,
) -> dict[str, Any]:
    target_refs = [
        dict(value)
        for value in suggestion.get("target_refs") or []
        if isinstance(value, dict)
    ]
    if not target_refs:
        target_refs.extend(
            {
                "kind": "facet_capability",
                "facet_id": str(facet),
                "capability": "shared",
            }
            for facet in suggestion.get("target_evidence_families") or []
        )
        target_refs.extend(
            {"kind": "criterion", "criterion_id": str(criterion)}
            for criterion in suggestion.get("target_criterion_ids") or []
        )
    preserve_refs = [
        dict(value)
        for value in suggestion.get("preserve_refs") or []
        if isinstance(value, dict)
    ]
    definition = {
        "equivalence_scope": "episode_repair_equivalence",
        "episode_id": episode_id or "ad_hoc",
        "repair_policy_version": repair_policy_version,
        "operator": str(
            suggestion.get("operator")
            or suggestion.get("practice_mode")
            or "targeted_repair"
        ),
        "target_refs": target_refs,
        "preserve_refs": preserve_refs,
        "expected_minutes": suggestion.get("expected_minutes"),
        "answer_reveal_budget": float(
            suggestion.get("answer_reveal_budget") or 0.0
        ),
    }
    return {"id": _content_id("rc", definition), **definition}


def select_minimal_repair(
    repairs: list[dict[str, Any]],
    *,
    protected_refs: list[dict[str, Any]] | None = None,
    episode_id: str | None = None,
    repair_policy_version: str = REPAIR_POLICY_VERSION,
    expected_answer: str | dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Select the least-backtracking safe repair by §6.4's lexicographic rule."""

    protected = {_ref_key(value) for value in protected_refs or []}
    ranked: list[tuple[tuple[Any, ...], dict[str, Any], list[str]]] = []
    for suggestion in repairs:
        validation = validate_repair_candidate(
            suggestion, expected_answer=expected_answer
        )
        validated_suggestion = {
            key: value
            for key, value in suggestion.items()
            if key
            not in {
                "evidence_contradiction",
                "invalid_rule",
                "verification_status",
                "repair_validation",
            }
        }
        validated_suggestion["repair_validation"] = validation.as_dict()
        repair_class = _repair_class(
            validated_suggestion,
            episode_id=episode_id,
            repair_policy_version=repair_policy_version,
        )
        target_keys = {
            _ref_key(value) for value in repair_class["target_refs"]
        }
        reasons: list[str] = []
        contradiction = (
            validation.verification.status == "contradicted"
        )
        invalid_rule = validation.status in {"invalid", "incomplete"}
        protected_violation = bool(protected & target_keys)
        if contradiction:
            reasons.append("evidence_contradiction")
        if invalid_rule:
            reasons.extend(validation.reasons or ("invalid_rule",))
        if protected_violation:
            reasons.append("demonstrated_capability_not_preserved")
        trace = validated_suggestion.get("repaired_trace")
        trace = trace if isinstance(trace, dict) else {}
        before = str(trace.get("learner_work_prefix") or "")
        after = str(trace.get("repaired_answer_md") or "")
        latent_cost = len(
            {
                str(value)
                for value in trace.get("changed_latent_claims") or []
                if str(value)
            }
        )
        checkpoint_cost = len(
            {
                str(value)
                for value in trace.get("changed_checkpoint_ids") or []
                if str(value)
            }
        )
        minutes = validated_suggestion.get("expected_minutes")
        burden = float(minutes) if isinstance(minutes, (int, float)) else float("inf")
        rank = (
            int(contradiction),
            int(invalid_rule),
            int(protected_violation),
            latent_cost,
            checkpoint_cost,
            burden,
            repair_class["id"],
        )
        minimality = {
            "preserved_spans": [before] if before else [],
            "preserved_criteria": [
                value.get("criterion_id")
                for value in repair_class["preserve_refs"]
                if value.get("kind") == "criterion"
            ],
            "changed_latent_claims": list(
                dict.fromkeys(trace.get("changed_latent_claims") or [])
            ),
            "changed_trace_steps": list(
                dict.fromkeys(trace.get("changed_checkpoint_ids") or [])
            ),
            "trace_edit_cost": (
                _trace_edit_cost(before, after) if before or after else None
            ),
            "latent_change_cost": latent_cost,
            "checkpoint_change_cost": checkpoint_cost,
            "estimated_minutes": minutes,
            "text_diff": {
                "before": before,
                "after": after,
            }
            if before or after
            else None,
        }
        ranked.append(
            (
                rank,
                {
                    "repair_class": repair_class,
                    "suggestion": validated_suggestion,
                    "minimality": minimality,
                },
                reasons,
            )
        )
    ranked.sort(key=lambda value: value[0])
    safe = [entry for entry in ranked if not entry[2]]
    selected = safe[0][1] if safe else None
    return {
        "selected": selected,
        "rejected": [
            {
                "repair_class_id": entry[1]["repair_class"]["id"],
                "reasons": entry[2] or ["higher_lexicographic_cost"],
            }
            for entry in ranked
            if selected is None
            or entry[1]["repair_class"]["id"]
            != selected["repair_class"]["id"]
        ],
        "ranking": [
            entry[1]["repair_class"]["id"]
            for entry in ranked
        ],
    }


def _normalized(value: str) -> str:
    return _NORMALIZE_RE.sub(" ", value.casefold()).strip()


def mint_causal_mechanism_taxonomy(
    repository: Repository,
    *,
    min_cluster_size: int = 2,
    activate: bool = False,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Build an immutable mechanism-taxonomy snapshot as an explicit batch.

    The first implementation is intentionally interpretable: exact normalized
    operation groups are the clusters, statements are retained as medoids/examples,
    and singleton operations explicitly abstain.  Assignments live on this
    snapshot; hypothesis episode history is not rewritten.
    """

    if min_cluster_size < 2:
        raise ValueError("mechanism clusters require at least two observations")
    hypotheses = repository.causal_hypotheses_with_operations()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for hypothesis in hypotheses:
        operation = str(hypothesis.get("operation") or "")
        if operation:
            grouped.setdefault(operation, []).append(hypothesis)
    clusters: list[dict[str, Any]] = []
    abstained: list[dict[str, Any]] = []
    assignments: list[dict[str, str]] = []
    for operation, members in sorted(grouped.items()):
        if len(members) < min_cluster_size:
            abstained.append({"operation": operation, "support": len(members)})
            continue
        mechanism_id = f"operation:{operation}"
        statements = list(
            dict.fromkeys(str(member["statement"]) for member in members)
        )
        clusters.append(
            {
                "id": mechanism_id,
                "algorithm": "exact_operation_v1",
                "operation": operation,
                "support": len(members),
                "statements": statements,
            }
        )
        for member in members:
            assignments.append(
                {
                    "hypothesis_id": str(member["id"]),
                    "mechanism_id": mechanism_id,
                }
            )
    source_heads = [
        {
            "id": str(value["id"]),
            "episode_key": str(value["episode_key"]),
            "version": int(value["version"]),
            "operation": str(value["operation"]),
            "statement_normalized": str(value["statement_normalized"]),
        }
        for value in hypotheses
    ]
    source_head_hash = _content_id("ch", source_heads)
    taxonomy = {
        "schema_version": 1,
        "algorithm": "exact_operation_v1",
        "min_cluster_size": min_cluster_size,
        "source_head_hash": source_head_hash,
        "clusters": clusters,
        "abstained": abstained,
    }
    status = "active" if activate else "draft"
    taxonomy_version_id = _content_id(
        "ctv",
        {
            "taxonomy": taxonomy,
            "assignments": assignments,
            "status": status,
        },
    )
    return repository.insert_causal_mechanism_taxonomy_version(
        taxonomy_version_id=taxonomy_version_id,
        algorithm="exact_operation_v1",
        min_cluster_size=min_cluster_size,
        source_head_hash=source_head_hash,
        status=status,
        taxonomy=taxonomy,
        assignments=assignments,
        clock=clock,
    )


def _criterion_receipt(
    vault: LoadedVault,
    repository: Repository,
    attempt_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    attempt = repository.fetch_practice_attempt(attempt_id) or {}
    item = vault.practice_items.get(str(attempt.get("practice_item_id") or ""))
    rubric = vault.rubric_for_item(item) if item is not None else None
    if item is None or rubric is None:
        return [], []
    evidence = {
        row.criterion_id: row for row in repository.fetch_grading_evidence(attempt_id)
    }
    raw: list[CriterionOutcome] = []
    rows: list[dict[str, Any]] = []
    for criterion in rubric.criteria:
        awarded = float(
            evidence[criterion.id].points_awarded
            if criterion.id in evidence
            else 0.0
        )
        fraction = (
            max(0.0, min(1.0, awarded / float(criterion.points)))
            if criterion.points > 0
            else 0.0
        )
        raw.append(
            CriterionOutcome(
                criterion_id=criterion.id,
                passed=fraction >= 0.40,
                depends_on=tuple(criterion.depends_on),
            )
        )
        rows.append(
            {
                "criterion_id": criterion.id,
                "criterion_label": criterion.description,
                "points_awarded": awarded,
                "points_possible": float(criterion.points),
                "raw_fraction": fraction,
                "passed": fraction >= 0.40,
                "full_credit": fraction >= 1.0 - 1e-9,
                "assessable": True,
            }
        )
    localized = {
        value.criterion_id: value for value in localize_criterion_outcomes(raw)
    }
    for row in rows:
        row["assessable"] = localized[row["criterion_id"]].assessable

    protected: list[dict[str, Any]] = [
        {"kind": "criterion", "criterion_id": row["criterion_id"]}
        for row in rows
        if row["assessable"] and row["full_credit"]
    ]
    full_credit_criteria = {
        row["criterion_id"]
        for row in rows
        if row["assessable"] and row["full_credit"]
    }
    failed_criteria = {
        row["criterion_id"]
        for row in rows
        if row["assessable"] and not row["full_credit"]
    }
    weights = item.criterion_facet_weights or {}
    passed_facets = {
        vault.canonical_facet_id(str(facet))
        for criterion_id, facets in weights.items()
        if criterion_id in full_credit_criteria
        for facet in facets
    }
    failed_facets = {
        vault.canonical_facet_id(str(facet))
        for criterion_id, facets in weights.items()
        if criterion_id in failed_criteria
        for facet in facets
    }
    protected.extend(
        {
            "kind": "facet_capability",
            "facet_id": facet,
            "capability": item.capability or "shared",
        }
        for facet in sorted(passed_facets - failed_facets)
    )
    return rows, protected


def _repair_definitions(
    repair_suggestions: list[dict[str, Any]],
    protected_refs: list[dict[str, Any]],
    *,
    episode_id: str,
    expected_answer: str | dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for raw in repair_suggestions:
        suggestion = dict(raw)
        preserve = [
            dict(value)
            for value in suggestion.get("preserve_refs") or []
            if isinstance(value, dict)
        ]
        seen = {_ref_key(value) for value in preserve}
        for ref in protected_refs:
            if _ref_key(ref) not in seen:
                preserve.append(dict(ref))
                seen.add(_ref_key(ref))
        suggestion["preserve_refs"] = preserve
        normalized.append(suggestion)
    selection = select_minimal_repair(
        normalized,
        protected_refs=protected_refs,
        episode_id=episode_id,
        expected_answer=expected_answer,
    )
    classes = [
        _repair_class(value, episode_id=episode_id)
        for value in normalized
    ]
    deduped = {
        repair_class["id"]: repair_class for repair_class in classes
    }
    return list(deduped.values()), selection


def _repair_for_target(
    repair_classes: list[dict[str, Any]],
    target_ref: dict[str, Any] | None,
) -> str | None:
    if not repair_classes:
        return None
    target_key = _ref_key(target_ref)
    matches = [
        value
        for value in repair_classes
        if target_key
        and target_key in {_ref_key(ref) for ref in value["target_refs"]}
    ]
    if len(matches) == 1:
        return str(matches[0]["id"])
    return None


def _candidate_key(
    candidate: dict[str, Any],
    *,
    target_ref: dict[str, Any] | None,
    status: str,
) -> str:
    """Stable identity for a candidate independent of presentation order."""

    if status == "open_set":
        return "open_set"
    return _content_id(
        "ck",
        {
            "statement_normalized": _normalized(
                str(candidate.get("statement") or "")
            ),
            "cause_scope": str(candidate.get("cause_scope") or "unknown"),
            "target_ref": target_ref,
        },
    )


def _hypothesis_specs(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    repair_classes: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    attempt = repository.fetch_practice_attempt(attempt_id) or {}
    learning_object_id = str(attempt.get("learning_object_id") or "")
    item_id = str(attempt.get("practice_item_id") or "")
    diagnostic_probe = str(attempt.get("attempt_type") or "") == "diagnostic_probe"
    item = vault.practice_items.get(item_id)
    surface_family = None
    if item is not None:
        from learnloop.services.canonical_projection import surface_group_id

        surface_family = surface_group_id(item)
    specs: list[dict[str, Any]] = []
    event_specs_by_signature: dict[str, list[dict[str, Any]]] = {}
    for event in repository.error_events_for_attempt(attempt_id):
        plan = event.get("repair_plan")
        plan = plan if isinstance(plan, dict) else {}
        raw_candidates = [
            dict(value)
            for value in plan.get("candidate_causes") or []
            if isinstance(value, dict)
        ]
        if not raw_candidates and event.get("misconception_statement"):
            raw_candidates = [
                {
                    "statement": event["misconception_statement"],
                    "cause_scope": plan.get("cause_scope") or "learner_state",
                    "target_ref": plan.get("target_ref"),
                }
            ]
        for candidate in raw_candidates:
            statement = str(candidate.get("statement") or "").strip()
            if not statement:
                continue
            target_ref = candidate.get("target_ref")
            target_ref = dict(target_ref) if isinstance(target_ref, dict) else None
            status = (
                "open_set"
                if candidate.get("hypothesis_id") == "H_OTHER"
                or candidate.get("open_set") is True
                else "candidate"
            )
            candidate_key = _candidate_key(
                candidate, target_ref=target_ref, status=status
            )
            spec = {
                "episode_key": (
                    f"{attempt_id}:event:{event['id']}:{candidate_key}"
                ),
                "attempt_id": attempt_id,
                "error_event_id": str(event["id"]),
                "learning_object_id": learning_object_id,
                "cause_scope": str(
                    candidate.get("cause_scope")
                    or plan.get("cause_scope")
                    or "unknown"
                ),
                "statement": statement,
                "statement_normalized": _normalized(statement),
                "operation": plan.get("operation"),
                "target_ref": target_ref,
                "applicability": {
                    "practice_item_id": item_id,
                    "surface_family": surface_family,
                    "criterion_ids": list(
                        plan.get("target_criterion_ids") or []
                    ),
                },
                "postdictive_claims": list(
                    plan.get("postdictive_claims") or []
                ),
                "evidence": {
                    "source_error_event_id": str(event["id"]),
                    "error_type": event.get("error_type"),
                    "severity": event.get("severity"),
                    "observed_evidence": plan.get("evidence"),
                    "resolution_status": plan.get("resolution_status"),
                    "first_divergence": plan.get("first_divergence"),
                    "model_reported_localization_confidence": plan.get(
                        "model_reported_localization_confidence"
                    ),
                    "model_reported_causal_confidence": plan.get(
                        "model_reported_causal_confidence"
                    ),
                    "observed_signature": event.get(
                        "misconception_consistent_answer"
                    ),
                    "preregistered_signature": (
                        None
                        if diagnostic_probe
                        else event.get("misconception_consistent_answer")
                    ),
                    "facet_contrast": plan.get("facet_contrast"),
                },
                "repair_class_id": _repair_for_target(
                    repair_classes, target_ref
                ),
                "status": status,
            }
            specs.append(spec)
            signature = json.dumps(
                {
                    "statement": spec["statement_normalized"],
                    "target_ref": target_ref,
                    "status": status,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            event_specs_by_signature.setdefault(signature, []).append(spec)

    factor_specs: dict[str, list[dict[str, Any]]] = {}
    for factor in repository.unresolved_cause_factors_for_attempt(
        attempt_id, status="open"
    ):
        refs: list[dict[str, Any]] = []
        for candidate in factor.get("candidate_causes") or []:
            if not isinstance(candidate, dict):
                continue
            statement = str(candidate.get("statement") or "").strip()
            if not statement:
                continue
            target_ref = candidate.get("target_ref")
            target_ref = (
                dict(target_ref) if isinstance(target_ref, dict) else None
            )
            status = (
                "open_set"
                if candidate.get("hypothesis_id") == "H_OTHER"
                or candidate.get("open_set") is True
                else "candidate"
            )
            candidate_key = _candidate_key(
                candidate, target_ref=target_ref, status=status
            )
            signature = json.dumps(
                {
                    "statement": _normalized(statement),
                    "target_ref": target_ref,
                    "status": status,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            matching = event_specs_by_signature.get(signature) or []
            if matching:
                refs.append(matching[0])
                continue
            spec = {
                "episode_key": (
                    f"{attempt_id}:factor:{factor['id']}:{candidate_key}"
                ),
                "attempt_id": attempt_id,
                "error_event_id": None,
                "learning_object_id": learning_object_id,
                "cause_scope": str(candidate.get("cause_scope") or "unknown"),
                "statement": statement,
                "statement_normalized": _normalized(statement),
                "operation": candidate.get("operation"),
                "target_ref": target_ref,
                "applicability": {
                    "practice_item_id": item_id,
                    "surface_family": surface_family,
                    "observation_id": factor.get("observation_id"),
                },
                "postdictive_claims": [],
                "evidence": {
                    "unresolved_cause_factor_id": factor["id"],
                    "observation_id": factor.get("observation_id"),
                },
                "repair_class_id": _repair_for_target(
                    repair_classes, target_ref
                ),
                "status": status,
            }
            specs.append(spec)
            refs.append(spec)
        factor_specs[str(factor["id"])] = refs
    return specs, factor_specs


def _anchors(
    hypotheses: list[dict[str, Any]],
    selection: dict[str, Any],
) -> dict[str, Any]:
    raw_divergences = [
        (hypothesis.get("evidence") or {}).get("first_divergence")
        for hypothesis in hypotheses
        if isinstance(hypothesis.get("evidence"), dict)
        and (hypothesis.get("evidence") or {}).get("first_divergence")
    ]
    divergences: list[dict[str, Any]] = []
    seen_divergences: set[str] = set()
    for value in raw_divergences:
        if not isinstance(value, dict):
            continue
        key = json.dumps(
            value, sort_keys=True, separators=(",", ":"), default=str
        )
        if key not in seen_divergences:
            divergences.append(value)
            seen_divergences.add(key)
    observable_candidates = [
        value
        for value in divergences
        if value.get("anchor_kind") != "missing_required_step"
    ]
    positioned = [
        value
        for value in observable_candidates
        if isinstance(value.get("char_start"), int)
    ]
    if positioned:
        earliest_start = min(int(value["char_start"]) for value in positioned)
        earliest = [
            value
            for value in positioned
            if int(value["char_start"]) == earliest_start
        ]
        observable = earliest[0] if len(earliest) == 1 else None
    elif len(observable_candidates) == 1:
        observable = observable_candidates[0]
    else:
        observable = None
    selected = selection.get("selected")
    suggestion = selected.get("suggestion") if isinstance(selected, dict) else {}
    trace = (
        suggestion.get("repaired_trace")
        if isinstance(suggestion, dict)
        else None
    )
    insertion = (
        trace.get("repair_insertion_point")
        if isinstance(trace, dict)
        else None
    )
    return {
        "first_observable_divergence": observable,
        # A missing step is an observed omission, not evidence of the
        # learner's earliest faulty commitment.  Keep this unavailable until a
        # separately anchored commitment is present.
        "earliest_supported_faulty_commitment": None,
        "repair_insertion_point": insertion,
        "observable_divergence_candidates": observable_candidates,
        "anchor_disagreement": (
            len(observable_candidates) > 1 and observable is None
        ),
    }


def _repair_cover_matrix(
    hypotheses: list[dict[str, Any]],
    selection: dict[str, Any],
) -> tuple[list[dict[str, Any]], bool, str | None]:
    selected = selection.get("selected")
    selected = selected if isinstance(selected, dict) else None
    repair_class = (
        selected.get("repair_class")
        if selected is not None
        and isinstance(selected.get("repair_class"), dict)
        else None
    )
    repair_class_id = (
        str(repair_class["id"]) if repair_class is not None else None
    )
    target_keys = {
        _ref_key(value)
        for value in (
            repair_class.get("target_refs") if repair_class is not None else []
        )
        if _ref_key(value)
    }
    matrix: list[dict[str, Any]] = []
    for hypothesis in hypotheses:
        target_key = _ref_key(hypothesis.get("target_ref"))
        covered = bool(
            repair_class_id
            and target_key
            and target_key in target_keys
        )
        matrix.append(
            {
                "hypothesis_id": hypothesis["id"],
                "repair_class_id": repair_class_id,
                "target_ref": hypothesis.get("target_ref"),
                "covered": covered,
                "basis": (
                    "exact_target_match"
                    if covered
                    else (
                        "hypothesis_target_unresolved"
                        if not target_key
                        else "repair_target_mismatch"
                    )
                ),
            }
        )
    return matrix, bool(matrix and all(row["covered"] for row in matrix)), repair_class_id


def _trace_backtracking_depth(
    vault: LoadedVault,
    attempt: dict[str, Any],
    changed_steps: list[str],
) -> int | None:
    if not changed_steps:
        return None
    item = vault.practice_items.get(
        str(attempt.get("practice_item_id") or "")
    )
    trace = item.trace_contract if item is not None else None
    if trace is None or trace.status != "available":
        return None
    wanted = set(changed_steps)
    depths: list[int] = []
    for recipe in trace.recipes:
        if not wanted <= set(recipe.checkpoints):
            continue
        memo: dict[str, int] = {}

        def depth(checkpoint: str, visiting: set[str]) -> int:
            if checkpoint in memo:
                return memo[checkpoint]
            if checkpoint in visiting:
                return 0
            dependencies = recipe.dependencies.get(checkpoint, [])
            value = (
                0
                if not dependencies
                else 1
                + max(
                    depth(value, visiting | {checkpoint})
                    for value in dependencies
                )
            )
            memo[checkpoint] = value
            return value

        all_depths = [depth(value, set()) for value in recipe.checkpoints]
        changed_depths = [depth(value, set()) for value in wanted]
        depths.append(max(all_depths, default=0) - min(changed_depths))
    return min(depths) if depths else None


def materialize_causal_episode(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    repair_suggestions: list[dict[str, Any]] | None = None,
    generation_agent_run_id: str | None = None,
    model: str | None = None,
    mechanism_taxonomy_version_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Materialize all P1 causal records and return the immutable receipt."""

    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        raise ValueError("attempt does not exist")
    if model is None and generation_agent_run_id:
        agent_record = repository.find_record(generation_agent_run_id)
        if agent_record is not None and agent_record[0] == "agent_run":
            model = (
                agent_record[1].get("model")
                or agent_record[1].get("actual_model")
            )
    criterion_outcomes, protected_refs = _criterion_receipt(
        vault, repository, attempt_id
    )
    repair_classes, selection = _repair_definitions(
        list(repair_suggestions or []),
        protected_refs,
        episode_id=attempt_id,
        expected_answer=(
            vault.practice_items[str(attempt["practice_item_id"])]
            .expected_answer
        ),
    )
    specs, factor_specs = _hypothesis_specs(
        vault,
        repository,
        attempt_id=attempt_id,
        repair_classes=repair_classes,
    )
    by_episode: dict[str, dict[str, Any]] = {}
    for spec in specs:
        hypothesis = repository.append_causal_hypothesis(
            **spec,
            generation_agent_run_id=generation_agent_run_id,
            model=model,
            clock=clock,
        )
        by_episode[str(spec["episode_key"])] = hypothesis
    hypotheses = repository.causal_hypotheses_for_attempt(attempt_id)
    by_episode = {
        str(hypothesis["episode_key"]): hypothesis
        for hypothesis in hypotheses
    }
    for factor_id, factor_spec_rows in factor_specs.items():
        refs: list[dict[str, Any]] = []
        for spec in factor_spec_rows:
            hypothesis = by_episode.get(str(spec["episode_key"]))
            if hypothesis is None:
                continue
            refs.append(
                {
                    "hypothesis_id": hypothesis["id"],
                    "version": hypothesis["version"],
                    **(
                        {"open_set": True}
                        if hypothesis["status"] == "open_set"
                        else {}
                    ),
                }
            )
        repository.set_unresolved_cause_hypothesis_refs(
            factor_id, refs, clock=clock
        )

    concrete = [
        value for value in hypotheses if value["status"] != "open_set"
    ]
    model_reported_support_proposals = {
        str(value["id"]): (
            (value.get("evidence") or {}).get(
                "model_reported_causal_confidence"
            )
            if isinstance(value.get("evidence"), dict)
            else None
        )
        for value in concrete
    }
    # A single attempt does not produce validator-owned causal support or an
    # ordinal posterior. Preserve model proposals as provenance, not rank.
    support_scores = {
        str(value["id"]): None for value in concrete
    }
    mapped_repair_ids = {
        str(value["repair_class_id"])
        for value in concrete
        if value.get("repair_class_id")
    }
    cover_matrix, common_cover, common_repair_class_id = (
        _repair_cover_matrix(concrete, selection)
    )
    valid_targets = [
        value["target_ref"]
        for value in hypotheses
        if isinstance(value.get("target_ref"), dict)
        and value["target_ref"].get("kind") != "none"
    ]
    resolution_axes = [
        {
            "hypothesis_id": value["id"],
            "version": value["version"],
            "cause_scope": value["cause_scope"],
            "resolution_status": (
                (value.get("evidence") or {}).get("resolution_status")
                if isinstance(value.get("evidence"), dict)
                else None
            ),
            "target_ref": value.get("target_ref"),
        }
        for value in hypotheses
    ]
    divergence_anchors = _anchors(hypotheses, selection)
    selected_repair = selection.get("selected")
    if isinstance(selected_repair, dict):
        minimality = selected_repair.get("minimality")
        if isinstance(minimality, dict):
            minimality["divergence_anchors"] = divergence_anchors
            minimality["backtracking_depth"] = _trace_backtracking_depth(
                vault,
                attempt,
                list(minimality.get("changed_trace_steps") or []),
            )
            suggestion = selected_repair.get("suggestion")
            trace = (
                suggestion.get("repaired_trace")
                if isinstance(suggestion, dict)
                and isinstance(suggestion.get("repaired_trace"), dict)
                else None
            )
            if trace is not None:
                before = str(attempt.get("learner_answer_md") or "")
                after = str(trace.get("repaired_answer_md") or "")
                minimality["trace_edit_cost"] = _trace_edit_cost(
                    before, after
                )
                minimality["text_diff"] = {
                    "before": before,
                    "after": after,
                }
    created_at = str(attempt.get("created_at") or "")
    prior_debug = repository.attempt_debug_payload(attempt_id) or {}
    prior_attribution = prior_debug.get("causal_attribution")
    prior_receipt = (
        prior_attribution.get("diagnosis_receipt")
        if isinstance(prior_attribution, dict)
        else None
    )
    if mechanism_taxonomy_version_id is None and isinstance(
        prior_receipt, dict
    ):
        pinned = prior_receipt.get("mechanism_taxonomy_version_id")
        if pinned:
            mechanism_taxonomy_version_id = str(pinned)
    if mechanism_taxonomy_version_id is None:
        active_taxonomy = (
            repository.latest_active_causal_mechanism_taxonomy()
        )
        if active_taxonomy is not None:
            mechanism_taxonomy_version_id = str(active_taxonomy["id"])
    taxonomy_ref = None
    if mechanism_taxonomy_version_id is not None:
        taxonomy_ref = repository.causal_mechanism_taxonomy_version(
            mechanism_taxonomy_version_id
        )
        if taxonomy_ref is None:
            raise ValueError("mechanism taxonomy version does not exist")
        if taxonomy_ref["status"] != "active":
            raise ValueError(
                "diagnosis receipts may reference only active mechanism taxonomies"
            )
    receipt_body = {
        "schema_version": 1,
        "attempt_id": attempt_id,
        "criterion_outcomes": criterion_outcomes,
        "divergence_anchors": divergence_anchors,
        "attribution_axes": resolution_axes,
        "valid_targets": valid_targets,
        "hypotheses": [
            {
                "id": value["id"],
                "version": value["version"],
                "status": value["status"],
                "repair_class_id": value.get("repair_class_id"),
            }
            for value in hypotheses
        ],
        "support_scores": support_scores,
        "model_reported_support_proposals": (
            model_reported_support_proposals
        ),
        "support_authority": "unavailable_single_attempt",
        "plausible_set": [value["id"] for value in concrete],
        "ordinal_ranking": [],
        "repair_classes": repair_classes,
        "repair_class_ranking": selection["ranking"],
        "repair_selection": selection,
        "common_repair_cover": {
            "covers_plausible_set": common_cover,
            "repair_class_id": (
                common_repair_class_id if common_cover else None
            ),
            "matrix": cover_matrix,
        },
        "probe_decision": {
            "decision": "skip_common_repair"
            if common_cover
            else (
                "consider_probe"
                if len(mapped_repair_ids) > 1
                else "no_action_changing_probe"
            ),
            "reason": (
                "one safe repair covers every plausible cause"
                if common_cover
                else (
                    "plausible causes map to different repair classes"
                    if len(mapped_repair_ids) > 1
                    else "no explicitly validated common repair cover"
                )
            ),
        },
        "permitted_uses": list(SINGLE_ATTEMPT_USES),
        "mechanism_taxonomy_version_id": (
            taxonomy_ref["id"] if taxonomy_ref is not None else None
        ),
        "mechanism_taxonomy_hash": (
            taxonomy_ref["source_head_hash"]
            if taxonomy_ref is not None
            else None
        ),
        "created_at": created_at,
    }
    receipt = {
        "id": _content_id("dr", receipt_body),
        **receipt_body,
    }
    if repository.attempt_debug_payload(attempt_id) is not None:
        repository.append_attempt_diagnosis_receipt(attempt_id, receipt)
    return receipt


def causal_episode_for_attempt(
    repository: Repository, attempt_id: str
) -> dict[str, Any] | None:
    debug = repository.attempt_debug_payload(attempt_id) or {}
    attribution = debug.get("causal_attribution")
    receipt = (
        attribution.get("diagnosis_receipt")
        if isinstance(attribution, dict)
        else None
    )
    hypotheses: list[dict[str, Any]] = []
    if isinstance(receipt, dict):
        taxonomy_version_id = receipt.get(
            "mechanism_taxonomy_version_id"
        )
        for ref in receipt.get("hypotheses") or []:
            if not isinstance(ref, dict) or not ref.get("id"):
                continue
            hypothesis = repository.causal_hypothesis(str(ref["id"]))
            if hypothesis is not None:
                if taxonomy_version_id:
                    mechanism = repository.causal_mechanism_assignment(
                        str(taxonomy_version_id), str(hypothesis["id"])
                    )
                    if mechanism is not None:
                        hypothesis = {**hypothesis, "mechanism": mechanism}
                hypotheses.append(hypothesis)
    if not hypotheses:
        hypotheses = repository.causal_hypotheses_for_attempt(attempt_id)
    if not hypotheses and not isinstance(receipt, dict):
        return None
    return {
        "attempt_id": attempt_id,
        "receipt": receipt,
        "hypotheses": hypotheses,
    }


def claim_checked_feedback(
    vault: LoadedVault,
    repository: Repository,
    attempt_id: str,
) -> dict[str, Any] | None:
    """Build the typed P1 overlay, failing closed on unpermitted claims."""

    episode = causal_episode_for_attempt(repository, attempt_id)
    if episode is None or not isinstance(episode.get("receipt"), dict):
        return None
    receipt = dict(episode["receipt"])
    permitted = {
        str(value) for value in receipt.get("permitted_uses") or []
    }
    unknown = permitted - PERMITTED_USES
    if unknown:
        raise ValueError(
            "diagnosis receipt contains unknown permitted uses: "
            + ", ".join(sorted(unknown))
        )
    may_render = "learner_feedback" in permitted
    if not may_render:
        return None
    hypotheses_by_id = {
        str(value["id"]): value for value in episode.get("hypotheses") or []
    }
    uncertain_hypotheses = []
    if may_render:
        for ref in receipt.get("hypotheses") or []:
            if not isinstance(ref, dict) or ref.get("status") == "open_set":
                continue
            hypothesis = hypotheses_by_id.get(str(ref.get("id") or ""))
            if hypothesis is None:
                continue
            uncertain_hypotheses.append(
                {
                    "hypothesis_id": hypothesis["id"],
                    "label": "Possible explanation — not yet confirmed",
                    "statement": hypothesis["statement"],
                    "cause_scope": hypothesis["cause_scope"],
                    "support_score": (
                        receipt.get("support_scores") or {}
                    ).get(str(hypothesis["id"])),
                }
            )
    criterion_outcomes = receipt.get("criterion_outcomes") or []
    demonstrated = [
        {
            "criterion_id": value.get("criterion_id"),
            "criterion_label": value.get("criterion_label"),
            "points_awarded": value.get("points_awarded"),
            "points_possible": value.get("points_possible"),
        }
        for value in criterion_outcomes
        if isinstance(value, dict)
        and value.get("assessable")
        and value.get("full_credit")
    ]
    selection = receipt.get("repair_selection")
    selection = selection if isinstance(selection, dict) else {}
    selected = selection.get("selected")
    selected = selected if isinstance(selected, dict) else None
    suggestion = (
        selected.get("suggestion")
        if selected is not None
        and isinstance(selected.get("suggestion"), dict)
        else None
    )
    repair_class = (
        selected.get("repair_class")
        if selected is not None
        and isinstance(selected.get("repair_class"), dict)
        else None
    )
    validation = (
        suggestion.get("repair_validation")
        if suggestion is not None
        and isinstance(suggestion.get("repair_validation"), dict)
        else {}
    )
    verification = (
        validation.get("verification")
        if isinstance(validation.get("verification"), dict)
        else {}
    )
    verification_status = verification.get("status")
    verified_correction = None
    if may_render and verification_status == "verified" and suggestion is not None:
        request = suggestion.get("verification_request")
        request = request if isinstance(request, dict) else {}
        verification_kind = str(request.get("kind") or "")
        verified_correction = {
            "label": "Checked repair",
            "rationale": suggestion.get("rationale"),
            "verification_status": "verified",
            "verification_scope": (
                "The repaired answer is symbolically equivalent to the authored answer."
                if verification_kind == "symbolic_equality"
                else "The repaired answer exactly matches the authored answer."
            ),
        }
    unverified: list[dict[str, Any]] = [
        {
            "kind": "causal_hypothesis",
            "hypothesis_id": value["hypothesis_id"],
            "statement": value["statement"],
        }
        for value in uncertain_hypotheses
    ]
    metadata = repository.fetch_attempt_feedback_metadata(attempt_id) or {}
    if may_render and metadata.get("feedback_md") and verified_correction is None:
        unverified.append(
            {
                "kind": "grader_feedback",
                "statement": metadata["feedback_md"],
            }
        )
    debug = repository.attempt_debug_payload(attempt_id) or {}
    attribution = debug.get("causal_attribution")
    firewall_events = (
        attribution.get("firewall_events")
        if isinstance(attribution, dict)
        else []
    )
    protected_by_target: dict[str, dict[str, Any]] = {}
    for value in firewall_events or []:
        if not isinstance(value, dict) or not str(
            value.get("kind") or ""
        ).startswith("passed_"):
            continue
        target = str(value.get("target") or "demonstrated_target")
        protected_by_target[target] = {
            "target": value.get("target"),
            "reason": "You demonstrated this part, so it is not treated as a weakness or included in the repair.",
        }
    for criterion in demonstrated:
        target = f"criterion:{criterion['criterion_id']}"
        protected_by_target.setdefault(
            target,
            {
                "target": target,
                "reason": "You earned full credit here, so the suggested repair leaves it intact.",
            },
        )
    if repair_class is not None:
        for ref in repair_class.get("preserve_refs") or []:
            if not isinstance(ref, dict):
                continue
            target = _ref_key(ref)
            protected_by_target.setdefault(
                target,
                {
                    "target": target,
                    "reason": "The suggested repair leaves this demonstrated work intact.",
                },
            )
    protected = list(protected_by_target.values())
    repaired_trace = (
        suggestion.get("repaired_trace")
        if suggestion is not None
        and isinstance(suggestion.get("repaired_trace"), dict)
        else None
    )
    # P2 adds the contamination class. Until it is present, an answer-revealing
    # trace is retained in the receipt but never displayed.
    contamination_status = receipt.get("contamination_status")
    trace_display = None
    trace_withheld_reason = None
    if repaired_trace is not None:
        if contamination_status in {"repair_activity", "verification"}:
            trace_display = repaired_trace
        else:
            trace_withheld_reason = "contamination_status_not_authorized"
    open_contest_factors = repository.unresolved_cause_factors_for_attempt(
        attempt_id, status="open"
    )
    contest_factor = next(
        (
            factor
            for factor in open_contest_factors
            if factor.get("self_report") is None
        ),
        None,
    )
    contest_already_recorded = any(
        factor.get("self_report") is not None
        for status in ("open", "resolved", "retired")
        for factor in repository.unresolved_cause_factors_for_attempt(
            attempt_id, status=status
        )
    )
    return {
        "receipt_id": receipt["id"],
        "verified_correction": verified_correction,
        "causal_hypotheses": uncertain_hypotheses,
        "unverified": unverified,
        "proposed_next_action": (
            {
                "label": "Proposed next action",
                "operator": repair_class.get("operator")
                if repair_class is not None
                else None,
                "rationale": suggestion.get("rationale")
                if suggestion is not None
                else None,
                "repair_class_id": repair_class.get("id")
                if repair_class is not None
                else None,
            }
            if may_render and selected is not None
            else None
        ),
        "demonstrated_criteria": demonstrated,
        "first_divergence": (
            receipt.get("divergence_anchors") or {}
        ).get("first_observable_divergence"),
        "protected_targets": protected,
        "contest_action": {
            "available": bool(
                uncertain_hypotheses and not contest_already_recorded
            ),
            "factor_id": (
                str(contest_factor["id"])
                if contest_factor is not None
                else None
            ),
            "reasons": [
                "slipped",
                "notation_confused",
                "diagnosis_wrong",
                "item_unclear",
                "other_valid_approach",
            ],
        },
        "repaired_trace": trace_display,
        "repaired_trace_withheld_reason": trace_withheld_reason,
        "permitted_uses": sorted(permitted),
    }


def record_causal_diagnosis_contest(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    response: str,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record a typed P1 contest even when P0 opened no ambiguity factor.

    P0 factors are created only for an action-changing ambiguous cause set. P1
    still promises every uncertain learner-facing diagnosis a contest action.
    On explicit learner action, create the thinnest factor possible—hypothesis
    refs plus the open-set arm—then reuse the immutable P0 report channel.
    """

    if response == "believed_candidate":
        raise ValueError(
            "belief confirmation requires choosing a presented candidate"
        )
    if response not in SELF_REPORT_REASONS:
        raise ValueError(f"unknown causal diagnosis contest reason {response!r}")
    if any(
        factor.get("self_report") is not None
        for status in ("open", "resolved", "retired")
        for factor in repository.unresolved_cause_factors_for_attempt(
            attempt_id, status=status
        )
    ):
        raise ValueError("attempt already has a learner causal report")
    factor = next(
        (
            value
            for value in repository.unresolved_cause_factors_for_attempt(
                attempt_id, status="open"
            )
            if value.get("self_report") is None
        ),
        None,
    )
    if factor is None:
        episode = causal_episode_for_attempt(repository, attempt_id)
        if episode is None or not isinstance(episode.get("receipt"), dict):
            raise ValueError("attempt has no contestable diagnosis receipt")
        refs = [
            {
                "hypothesis_id": hypothesis["id"],
                "version": hypothesis["version"],
            }
            for hypothesis in episode.get("hypotheses") or []
            if hypothesis.get("status") != "open_set"
        ]
        if not refs:
            raise ValueError("attempt has no contestable causal hypothesis")
        refs.append({"hypothesis_id": "H_OTHER", "open_set": True})
        factor_id = repository.insert_unresolved_cause_factor(
            attempt_id=attempt_id,
            candidate_causes=refs,
            algorithm_version="causal_attribution_p1",
            observation_id=(
                "diagnosis_receipt:"
                + str(episode["receipt"].get("id") or attempt_id)
            ),
            clock=clock,
        )
    else:
        factor_id = str(factor["id"])
    return record_unresolved_cause_self_report(
        vault,
        repository,
        factor_id=factor_id,
        response=response,
        clock=clock,
    )


def _trace_consistent(
    vault: LoadedVault,
    repository: Repository,
    attempt_id: str,
) -> bool:
    """Hard-veto deterministic postdictive claims contradicted by full credit."""

    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        return False
    item = vault.practice_items.get(str(attempt.get("practice_item_id") or ""))
    if item is None:
        return False
    rubric = vault.rubric_for_item(item)
    if rubric is None:
        return False
    maxima = {criterion.id: float(criterion.points) for criterion in rubric.criteria}
    awarded = {
        row.criterion_id: float(row.points_awarded)
        for row in repository.fetch_grading_evidence(attempt_id)
    }
    for event in repository.error_events_for_attempt(attempt_id):
        plan = event.get("repair_plan")
        if not isinstance(plan, dict):
            continue
        for claim in plan.get("postdictive_claims") or []:
            if not isinstance(claim, dict):
                continue
            criterion_id = str(claim.get("criterion_id") or "")
            maximum = maxima.get(criterion_id)
            if maximum is None or criterion_id not in awarded:
                continue
            if awarded[criterion_id] >= maximum - 1e-9:
                return False
    return True


def record_unresolved_cause_self_report(
    vault: LoadedVault,
    repository: Repository,
    *,
    factor_id: str,
    response: str,
    candidate_index: int | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record the one-tap report; confirmation may open a provisional belief."""

    if response not in SELF_REPORT_REASONS:
        raise ValueError(f"unknown unresolved-cause self-report reason {response!r}")
    factor = repository.unresolved_cause_factor(factor_id)
    if factor is None or factor.get("status") != "open":
        raise ValueError("unresolved-cause factor is not open")
    presented_factor = next(
        (
            row
            for row in repository.unresolved_cause_factors_for_attempt(
                str(factor["attempt_id"])
            )
            if row["id"] == factor_id
        ),
        None,
    )
    if presented_factor is not None and presented_factor.get("self_report") is not None:
        raise ValueError("unresolved-cause factor already has a learner report")
    candidates = list(factor.get("candidate_causes") or [])
    selected: dict[str, Any] | None = None
    if response == "believed_candidate":
        if candidate_index is None or not 0 <= candidate_index < len(candidates):
            raise ValueError("believed_candidate requires a valid candidate_index")
        raw = candidates[candidate_index]
        if not isinstance(raw, dict) or raw.get("hypothesis_id") == "H_OTHER":
            raise ValueError("believed_candidate must select a concrete hypothesis")
        selected = raw

    report_id = new_ulid()
    observation_id = f"learner_report:{report_id}"
    attempt_id = str(factor["attempt_id"])
    repository.insert_causal_attribution_report(
        report_id=report_id,
        factor_id=factor_id,
        attempt_id=attempt_id,
        response=response,
        candidate_index=candidate_index,
        payload={"observation_id": observation_id},
        clock=clock,
    )

    provisional_belief_id: str | None = None
    resolved = False
    if selected is not None and _trace_consistent(vault, repository, attempt_id):
        attempt = repository.fetch_practice_attempt(attempt_id) or {}
        learning_object_id = str(attempt.get("learning_object_id") or "")
        learning_object = vault.learning_objects.get(learning_object_id)
        statement = str(selected.get("statement") or "").strip()
        if statement and learning_object is not None:
            item = vault.practice_items.get(
                str(attempt.get("practice_item_id") or "")
            )
            error_events = repository.error_events_for_attempt(attempt_id)
            surface_families: list[str] = []
            if item is not None:
                from learnloop.services.canonical_projection import surface_group_id

                surface_families = [surface_group_id(item)]
            selected_hypothesis = repository.causal_hypothesis(
                str(selected.get("hypothesis_id") or "")
            )
            if selected_hypothesis is not None:
                evidence = dict(selected_hypothesis.get("evidence") or {})
                evidence["learner_confirmation"] = {
                    "report_id": report_id,
                    "observation_id": observation_id,
                    "response": response,
                }
                confirmed = repository.append_causal_hypothesis(
                    episode_key=str(selected_hypothesis["episode_key"]),
                    attempt_id=str(selected_hypothesis["attempt_id"]),
                    error_event_id=selected_hypothesis.get("error_event_id"),
                    learning_object_id=str(
                        selected_hypothesis["learning_object_id"]
                    ),
                    # Choosing "I believed this" is direct learner confirmation
                    # of learner-state scope; the separate "slipped" response
                    # covers transient execution.
                    cause_scope="learner_state",
                    statement=str(selected_hypothesis["statement"]),
                    statement_normalized=str(
                        selected_hypothesis["statement_normalized"]
                    ),
                    mechanism=selected_hypothesis.get("mechanism"),
                    operation=selected_hypothesis.get("operation"),
                    target_ref=selected_hypothesis.get("target_ref"),
                    applicability=selected_hypothesis.get("applicability"),
                    postdictive_claims=selected_hypothesis.get(
                        "postdictive_claims"
                    )
                    or [],
                    evidence=evidence,
                    repair_class_id=selected_hypothesis.get("repair_class_id"),
                    status="candidate",
                    generation_agent_run_id=selected_hypothesis.get(
                        "generation_agent_run_id"
                    ),
                    model=selected_hypothesis.get("model"),
                    clock=clock,
                )
                provisional_belief_id = str(confirmed["id"])
            else:
                # Compatibility for a P0 factor created before hypothesis
                # materialization. New P1 factors store ids only.
                existing = repository.misconception_candidate_by_normalized(
                    learning_object_id, _normalized(statement)
                )
                if existing is None:
                    target_ref = selected.get("target_ref")
                    target_ref = (
                        target_ref if isinstance(target_ref, dict) else {}
                    )
                    facet = (
                        target_ref.get("facet_id")
                        if target_ref.get("kind") == "facet_capability"
                        else selected.get("facet")
                    )
                    provisional_belief_id = (
                        repository.insert_misconception_candidate(
                            learning_object_id=learning_object_id,
                            statement=statement,
                            statement_normalized=_normalized(statement),
                            concept_id=learning_object.concept,
                            target_facet=str(facet) if facet else None,
                            facet_ids=[str(facet)] if facet else [],
                            source_error_event_ids=[
                                str(event["id"]) for event in error_events
                            ],
                            surface_families=surface_families,
                            item_ids=[
                                str(attempt.get("practice_item_id") or "")
                            ],
                            occurrence_count=1,
                            severity=max(
                                (
                                    float(event.get("severity") or 0.0)
                                    for event in error_events
                                ),
                                default=0.7,
                            ),
                            clock=clock,
                        )
                    )
                else:
                    provisional_belief_id = str(existing["id"])
            resolved = repository.resolve_unresolved_cause_factor(
                factor_id,
                resolution_observation_ids=[observation_id],
                clock=clock,
            )
            feedback = repository.fetch_attempt_feedback_metadata(attempt_id) or {}
            materialize_causal_episode(
                vault,
                repository,
                attempt_id=attempt_id,
                repair_suggestions=list(
                    feedback.get("repair_suggestions") or []
                ),
                generation_agent_run_id=feedback.get("agent_run_id"),
                clock=clock,
            )
    return {
        "factor_id": factor_id,
        "response": response,
        "resolved": resolved,
        "provisional_belief_id": provisional_belief_id,
        "observation_id": observation_id,
    }
