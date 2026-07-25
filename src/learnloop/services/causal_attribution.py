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
from typing import Any, Sequence

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
# v2 (spec_diagnostic_augmentation_v1 §2 A1): the lexicographic order now leads
# with the DETERMINISTIC keys (backtracking depth, validated checkpoint cost,
# trace edit cost) and demotes the model's self-reports (latent-claim count,
# `expected_minutes`) to tie-breakers.  v1 said "structural" while ranking on
# three numbers the model reported about itself; the name now means what it
# says.  Bumping this string also re-mints every `repair_class_id`, which is
# correct: a repair class is defined relative to the policy that selected it.
REPAIR_POLICY_VERSION = "structural_lexicographic_v2"

#: Which regime actually ordered a selection (standing constraint 4).
#: ``structural`` — an available trace contract made the deterministic keys
#: computable.  ``model_reported`` — no usable decomposition existed (the item
#: declares ``no_reliable_decomposition``, or no contract reached the selector),
#: so the deterministic keys tie for every candidate and the model's own counts
#: decide.  P4 trains on these receipts and must be able to tell the two apart;
#: a silent degradation to self-reports is exactly what A1 exists to end.
REPAIR_SELECTION_BASES = ("structural", "model_reported")

#: Latent-claim counts are model self-reports.  ``spec_causal_attribution_v1``
#: §5.1 rejects per-criterion outcome distributions as "fabricated precision at
#: real token cost"; a raw ``len()`` of a model-supplied list is the same
#: fabrication at finer grain.  Within a set of candidates that are already tied
#: on every deterministic key, a latent count within this many claims of the
#: best is treated as tied too, and the ordering falls through to burden.
LATENT_COST_RESOLUTION_FLOOR = 1

# Every P2 decision surface (diagnosis receipt, probe coherence, orchestrator)
# stamps this one constant so a stored decision can be replayed against the
# policy that produced it.
CAUSAL_DECISION_POLICY_VERSION = "causal_p2_v1"

#: The open-world arm's placeholder id on a *candidate cause row* (§5.1: a
#: candidate cause set is never closed).  Written by
#: ``canonical_projection._open_candidate_causes`` and by the receipt-derived
#: factor below; read by ``failure_triage``, ``probe_targeting``, and
#: ``causal_probe_coherence``.
#:
#: This is a DIFFERENT namespace from ``probe_hypotheses.H_OTHER``
#: (``"other_or_unknown"``), which is the open-set *label* inside a probe
#: hypothesis set.  Comparing a cause row's ``hypothesis_id`` against that label
#: can never match — the two vocabularies never meet — so every such guard was
#: dead code wearing the shape of a safety net.  One named constant per
#: namespace, and the ``open_set`` flag stays the primary carrier of the arm.
OPEN_SET_CAUSE_ID = "H_OTHER"

# --- repair-class mapping provenance (§5.3) ---------------------------------
#
# `repair_class_id` is the ONLY vocabulary allowed to declare that two plausible
# causes need different help (facets are the vocabulary under indictment, §0
# root cause 8).  A hypothesis that fails to map is therefore not "not
# divergent" — it is a machine-side backfill obligation, and the reason it
# failed determines what the backfill has to do.  Recording that reason is the
# difference between a routable gap and a silent null.

REPAIR_MAPPING_BASIS_TARGET_REF = "authored_target_ref"
REPAIR_MAPPING_BASIS_CRITERION_REF = "authored_criterion_ref"
#: Several authored classes covered the hypothesis's target and the minimal-repair
#: SELECTION picked one of them. The selection is a machine-side disambiguation
#: under the structural ordering (A1), so the mapping is resolved rather than
#: ambiguous: that class is the repair this episode will actually serve.
REPAIR_MAPPING_BASIS_SELECTED_REPAIR = "selected_repair"
REPAIR_MAPPING_BASIS_OPEN_SET = "open_set"
REPAIR_MAPPING_BASIS_UNRESOLVED = "unresolved"

REPAIR_MAPPING_BASES = (
    REPAIR_MAPPING_BASIS_TARGET_REF,
    REPAIR_MAPPING_BASIS_CRITERION_REF,
    REPAIR_MAPPING_BASIS_SELECTED_REPAIR,
    REPAIR_MAPPING_BASIS_OPEN_SET,
    REPAIR_MAPPING_BASIS_UNRESOLVED,
)

#: Why one concrete hypothesis carries no repair class.  Each value names a
#: distinct machine-side remedy, so an orchestrator can route the backfill
#: instead of reporting an undifferentiated "unmapped".
REPAIR_MAPPING_UNRESOLVED_REASONS = (
    # The diagnosis produced no repair suggestion at all (every self-graded
    # attempt, and any grader that declined to propose a repair).  Remedy:
    # author repairs for this episode.  There is nothing to map TO, so this is
    # emphatically not "the mapping was computed and dropped".
    "no_repair_authored",
    # Repairs exist, but none of them targets anything this hypothesis declares.
    # Remedy: re-target the repair, or localize the hypothesis.
    "no_matching_repair_target",
    # Two or more distinct repair classes cover the same declared target AND the
    # minimal-repair selection picked none of them (they were all rejected), so
    # the machine cannot say WHICH repair addresses this cause.  Remedy:
    # disambiguate the authored repairs — never buy it with a learner probe.
    "ambiguous_repair_target",
    # The hypothesis declares no usable target at all (no `target_ref`, or
    # `kind: none`, and no criterion ids).  Remedy: localize the hypothesis.
    "unlocalized_hypothesis",
)

DIAGNOSIS_RECEIPT_SCHEMA_VERSION = 3

# Who owns the causal-support numbers on a receipt.  A single model response
# over a single attempt owns nothing, which is why the default is explicitly
# "unavailable" rather than a fabricated score.  Only the approved authorities
# may PROMOTE a route; an unapproved authority may still veto (§2).
SUPPORT_AUTHORITIES = (
    "unavailable_single_attempt",
    "validator_owned",
    "learner_confirmed",
    "adjudicated",
    "fingerprint_distinct_recurrence",
)
APPROVED_SUPPORT_AUTHORITIES = frozenset(SUPPORT_AUTHORITIES) - {
    "unavailable_single_attempt"
}
DEFAULT_SUPPORT_AUTHORITY = "unavailable_single_attempt"

# The independent-evidence channels that may move DIAGNOSIS support (§7).  A
# repair outcome is deliberately absent: "the repair worked" is evidence about
# the repair, never retroactive proof of the diagnosis that chose it.
#
# Each basis maps to exactly ONE support authority, and the map is the single
# place that grant is expressed.  `record_delayed_cold_verification` validates
# a caller-supplied basis against the keys; the discriminating-observation
# receipt derives its authority from the value.  Keeping them one table is what
# stops a channel from quietly acquiring an authority its evidence cannot bear.
SUPPORT_BASIS_AUTHORITY: dict[str, str] = {
    # A pinned, pre-registered blind prediction matched by a deterministic
    # exact-key comparison.  The prediction was committed before the response
    # existed, is content-addressed and append-only, and was reviewed through
    # the register -> review -> activate ladder; the match itself runs no model.
    # See `causal_orchestrator.record_probe_classification` for the sensor
    # condition this grant is contingent on.
    "blind_probe_match": "validator_owned",
    "learner_confirmation": "learner_confirmed",
    "adjudication": "adjudicated",
    "fingerprint_distinct_recurrence": "fingerprint_distinct_recurrence",
}
DIAGNOSIS_SUPPORT_BASES = tuple(SUPPORT_BASIS_AUTHORITY)
assert set(SUPPORT_BASIS_AUTHORITY.values()) <= set(SUPPORT_AUTHORITIES)

# §5.6 scopes the trace-consistency veto per hypothesis.  "Nobody made a
# falsifiable claim" is absence of evidence and must never read as
# corroboration, so it gets its own state rather than collapsing into True.
TRACE_CONSISTENCY_STATES = (
    "contradicted",
    "consistent_with_claims",
    "no_deterministic_claims",
    "unknown",
)

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


def _declared_checkpoint_ids(trace: dict[str, Any] | None) -> list[str]:
    if not isinstance(trace, dict):
        return []
    return list(
        dict.fromkeys(
            str(value)
            for value in trace.get("changed_checkpoint_ids") or []
            if str(value or "").strip()
        )
    )


def _checkpoint_claims_verifiable(
    trace_contract: Any,
    changed_checkpoint_ids: Sequence[str],
) -> bool | None:
    """Are the claimed checkpoint ids real steps of some authored recipe?

    ``None`` means the question could not be asked — no trace contract reached
    this validator. That is a *different* fact from "the claim is false", and
    keeping them apart is the point of A1: previously a hallucinated id made
    every recipe fail the subset test in :func:`_backtracking_depth`, the
    depth silently became ``None``, and the one deterministic ordering term
    degraded invisibly into "unavailable".

    Claiming checkpoints on an item that declares ``no_reliable_decomposition``
    is unverifiable by construction: the item states it has no reliable step
    structure, so no id can be checked against one. Claiming NONE is always fine.
    """

    if trace_contract is None:
        return None
    if not changed_checkpoint_ids:
        return True
    wanted = set(changed_checkpoint_ids)
    if getattr(trace_contract, "status", None) != "available":
        return False
    return any(
        wanted <= set(recipe.checkpoints)
        for recipe in getattr(trace_contract, "recipes", None) or []
    )


def _backtracking_depth(
    trace_contract: Any,
    changed_steps: Sequence[str],
) -> int | None:
    """How far back through an authored recipe a repair reaches.

    ``max(recipe depth) - min(depth of a changed checkpoint)``: 0 means the
    repair touches only the final step, higher means it invalidates more
    downstream work. Minimised over the recipes that contain every claimed
    checkpoint. ``None`` when no recipe can answer -- either nothing was claimed,
    or the contract offers no usable decomposition.
    """

    if not changed_steps:
        return None
    if getattr(trace_contract, "status", None) != "available":
        return None
    wanted = set(changed_steps)
    depths: list[int] = []
    for recipe in getattr(trace_contract, "recipes", None) or []:
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


def validate_repair_candidate(
    suggestion: dict[str, Any],
    *,
    expected_answer: str | dict[str, Any] | None = None,
    trace_contract: Any = None,
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
    checkpoints_verifiable = _checkpoint_claims_verifiable(
        trace_contract, _declared_checkpoint_ids(trace)
    )
    if checkpoints_verifiable is not None:
        structural_checks["checkpoint_claims_verified"] = checkpoints_verifiable
    if checkpoints_verifiable is False:
        # A claim contradicted by the authored trace contract, not a missing
        # one: the candidate asserted structure the item does not have.
        reasons.append("unverifiable_checkpoint_claim")
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
            or checkpoints_verifiable is False
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
    trace_contract: Any = None,
    learner_answer_md: str | None = None,
) -> dict[str, Any]:
    """Select the least-backtracking safe repair by §6.4's lexicographic rule.

    Ordering keys, lowest-first, deterministic block before self-reported block
    (spec_diagnostic_augmentation_v1 §2 A1, standing constraint 4):

    1. ``evidence_contradiction`` -- a deterministic verifier refuted it;
    2. ``invalid_rule`` -- the candidate failed validation (including an
       ``unverifiable_checkpoint_claim``);
    3. ``protected_violation`` -- it would undo demonstrated capability;
    4. **backtracking depth** -- how far back through the authored recipe the
       repair reaches, computed against the item's trace contract;
    5. **validated checkpoint cost** -- how many real recipe steps it changes;
    6. **trace edit cost** -- the character-level diff between the learner's
       work and the repaired answer;
    7. latent-claim count -- MODEL-REPORTED, and only to a resolution of
       :data:`LATENT_COST_RESOLUTION_FLOOR`;
    8. ``expected_minutes`` -- MODEL-REPORTED;
    9. the repair-class id, for a deterministic final tie-break.

    Keys 4-6 are computed by this process; 7-8 are numbers the model reports
    about its own proposal. Before v2, keys 7 and 8 sat at positions 4 and 6 and
    the two computed quantities were written to the receipt and used for
    nothing. A model-reported count may break a tie among deterministically
    indistinguishable candidates; it may never overrule a computed one.

    ``trace_contract`` is the item's authored decomposition. Without one (or
    with ``no_reliable_decomposition``) keys 4-5 are unavailable for every
    candidate, they tie, and the self-reports legitimately decide -- which is
    why the result and every candidate's ``minimality`` carry
    ``selection_basis``. See :data:`REPAIR_SELECTION_BASES`.
    """

    protected = {_ref_key(value) for value in protected_refs or []}
    structural = getattr(trace_contract, "status", None) == "available"
    selection_basis = "structural" if structural else "model_reported"
    ranked: list[tuple[tuple[Any, ...], int, dict[str, Any], list[str]]] = []
    for suggestion in repairs:
        validation = validate_repair_candidate(
            suggestion,
            expected_answer=expected_answer,
            trace_contract=trace_contract,
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
        # The edit cost is measured against the learner's ACTUAL work whenever
        # the caller can supply it, so the ranked quantity is the same one the
        # receipt reports rather than a diff against the model's own copy of the
        # prefix.
        before = str(
            learner_answer_md
            if learner_answer_md is not None
            else trace.get("learner_work_prefix") or ""
        )
        after = str(trace.get("repaired_answer_md") or "")
        changed_checkpoints = _declared_checkpoint_ids(trace)
        latent_cost = len(
            {
                str(value)
                for value in trace.get("changed_latent_claims") or []
                if str(value)
            }
        )
        checkpoint_cost = len(changed_checkpoints)
        # Depth is defined only against an available decomposition. A candidate
        # that claims no checkpoint on an item that HAS a recipe backtracks
        # through none of it, which is depth 0; without a recipe the question is
        # unanswerable and every candidate ties at the sentinel.
        if not structural:
            depth = None
        elif not changed_checkpoints:
            depth = 0
        else:
            depth = _backtracking_depth(trace_contract, changed_checkpoints)
        edit_cost = _trace_edit_cost(before, after) if before or after else None
        minutes = validated_suggestion.get("expected_minutes")
        burden = float(minutes) if isinstance(minutes, (int, float)) else float("inf")
        # An unavailable deterministic key must never win by being absent.
        deterministic_rank = (
            int(contradiction),
            int(invalid_rule),
            int(protected_violation),
            float(depth) if depth is not None else float("inf"),
            checkpoint_cost,
            float(edit_cost) if edit_cost is not None else float("inf"),
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
            "changed_trace_steps": list(changed_checkpoints),
            "trace_edit_cost": edit_cost,
            "backtracking_depth": depth,
            "latent_change_cost": latent_cost,
            "checkpoint_change_cost": checkpoint_cost,
            "estimated_minutes": minutes,
            # Which regime ordered this selection; see REPAIR_SELECTION_BASES.
            "selection_basis": selection_basis,
            "text_diff": {
                "before": before,
                "after": after,
            }
            if before or after
            else None,
        }
        ranked.append(
            (
                deterministic_rank,
                latent_cost,
                {
                    "repair_class": repair_class,
                    "suggestion": validated_suggestion,
                    "minimality": minimality,
                },
                reasons,
            )
        )

    # Apply the latent resolution floor WITHIN each deterministically-tied
    # group: a self-reported count that differs from the group's best by no more
    # than the floor is not a real difference and must not decide.
    best_latent: dict[tuple[Any, ...], int] = {}
    for deterministic_rank, latent_cost, _entry, _reasons in ranked:
        current = best_latent.get(deterministic_rank)
        if current is None or latent_cost < current:
            best_latent[deterministic_rank] = latent_cost

    def _sort_key(
        value: tuple[tuple[Any, ...], int, dict[str, Any], list[str]]
    ) -> tuple[Any, ...]:
        deterministic_rank, latent_cost, entry, _reasons = value
        floor = best_latent[deterministic_rank] + LATENT_COST_RESOLUTION_FLOOR
        latent_key = 0 if latent_cost <= floor else latent_cost
        minutes = entry["minimality"]["estimated_minutes"]
        burden = (
            float(minutes) if isinstance(minutes, (int, float)) else float("inf")
        )
        return (*deterministic_rank, latent_key, burden, entry["repair_class"]["id"])

    ranked.sort(key=_sort_key)
    safe = [entry for entry in ranked if not entry[3]]
    selected = safe[0][2] if safe else None
    return {
        "selected": selected,
        "selection_basis": selection_basis,
        "rejected": [
            {
                "repair_class_id": entry[2]["repair_class"]["id"],
                "reasons": entry[3] or ["higher_lexicographic_cost"],
            }
            for entry in ranked
            if selected is None
            or entry[2]["repair_class"]["id"]
            != selected["repair_class"]["id"]
        ],
        "ranking": [entry[2]["repair_class"]["id"] for entry in ranked],
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
    trace_contract: Any = None,
    learner_answer_md: str | None = None,
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
        trace_contract=trace_contract,
        learner_answer_md=learner_answer_md,
    )
    classes = [
        _repair_class(value, episode_id=episode_id)
        for value in normalized
    ]
    deduped = {
        repair_class["id"]: repair_class for repair_class in classes
    }
    return list(deduped.values()), selection


def _classes_covering(
    repair_classes: list[dict[str, Any]], keys: set[str]
) -> list[dict[str, Any]]:
    if not keys:
        return []
    return [
        value
        for value in repair_classes
        if keys & {_ref_key(ref) for ref in value["target_refs"]}
    ]


def _resolve_repair_mapping(
    repair_classes: list[dict[str, Any]],
    *,
    target_ref: dict[str, Any] | None,
    criterion_ids: Sequence[Any] = (),
    open_set: bool = False,
    selected_repair_class_id: str | None = None,
) -> tuple[str | None, str, str | None]:
    """Map one hypothesis onto an authored repair class.

    Returns ``(repair_class_id, basis, unresolved_reason)``.

    Both matching channels compare the hypothesis's OWN authored declarations
    against the repair suggestion's OWN authored targets.  Nothing here derives a
    repair class from a facet: two causes sitting on different facets are not
    thereby "different repairs", which is precisely the inference §5.3 removes.

    The criterion channel exists because the grading contract lets a repair
    declare its target as ``target_criterion_ids`` while the candidate cause
    declares a ``facet_capability`` / span ``target_ref`` (see the grading
    prompt: "target only failed criterion ids and/or genuinely implicated
    evidence facets", with typed ``target_refs`` optional).  Matching only on
    ``target_ref`` therefore produced a spurious null whenever the grader used
    the two sub-vocabularies it was told it could use.

    When several authored classes cover the same declared target,
    ``selected_repair_class_id`` — the winner of the structural minimal-repair
    ordering (A1) — resolves the tie, because that is the repair this episode
    will actually serve. Only when the selector picked none of them (they were
    all rejected) is the mapping genuinely ambiguous.
    """

    if open_set:
        # The open-world arm names no cause, so it can name no repair.  It is
        # never counted as an unmapped hypothesis.
        return None, REPAIR_MAPPING_BASIS_OPEN_SET, None
    target_key = _ref_key(target_ref)
    if isinstance(target_ref, dict) and target_ref.get("kind") == "none":
        target_key = ""
    criterion_keys = {
        f"criterion:{value}" for value in criterion_ids if str(value or "").strip()
    }
    if not target_key and not criterion_keys:
        return None, REPAIR_MAPPING_BASIS_UNRESOLVED, "unlocalized_hypothesis"
    if not repair_classes:
        return None, REPAIR_MAPPING_BASIS_UNRESOLVED, "no_repair_authored"
    for keys, basis in (
        ({target_key} if target_key else set(), REPAIR_MAPPING_BASIS_TARGET_REF),
        (criterion_keys, REPAIR_MAPPING_BASIS_CRITERION_REF),
    ):
        matches = {
            str(value["id"]): value
            for value in _classes_covering(repair_classes, keys)
        }
        if len(matches) == 1:
            return next(iter(matches)), basis, None
        if len(matches) > 1:
            if selected_repair_class_id in matches:
                return (
                    str(selected_repair_class_id),
                    REPAIR_MAPPING_BASIS_SELECTED_REPAIR,
                    None,
                )
            return None, REPAIR_MAPPING_BASIS_UNRESOLVED, "ambiguous_repair_target"
    return None, REPAIR_MAPPING_BASIS_UNRESOLVED, "no_matching_repair_target"


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


def _event_candidate_causes(event: dict[str, Any]) -> list[dict[str, Any]]:
    """The raw candidate causes an error event proposes, in authored order."""

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
    return raw_candidates


def _candidate_status(candidate: dict[str, Any]) -> str:
    return (
        "open_set"
        if candidate.get("hypothesis_id") == OPEN_SET_CAUSE_ID
        or candidate.get("open_set") is True
        else "candidate"
    )


def _selected_repair_class_id(selection: dict[str, Any] | None) -> str | None:
    selected = (selection or {}).get("selected")
    if not isinstance(selected, dict):
        return None
    repair_class = selected.get("repair_class")
    if not isinstance(repair_class, dict) or not repair_class.get("id"):
        return None
    return str(repair_class["id"])


def _repair_mapping_fields(
    repair_classes: list[dict[str, Any]],
    *,
    target_ref: dict[str, Any] | None,
    criterion_ids: Sequence[Any] = (),
    status: str,
    selected_repair_class_id: str | None = None,
) -> dict[str, Any]:
    """The three persisted repair-mapping columns for one hypothesis spec."""

    repair_class_id, basis, reason = _resolve_repair_mapping(
        repair_classes,
        target_ref=target_ref,
        criterion_ids=criterion_ids,
        open_set=status == "open_set",
        selected_repair_class_id=selected_repair_class_id,
    )
    return {
        "repair_class_id": repair_class_id,
        "repair_class_basis": basis,
        "repair_class_unresolved_reason": reason,
    }


def _hypothesis_specs(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    repair_classes: list[dict[str, Any]],
    selected_repair_class_id: str | None = None,
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
        for candidate in _event_candidate_causes(event):
            statement = str(candidate.get("statement") or "").strip()
            if not statement:
                continue
            target_ref = candidate.get("target_ref")
            target_ref = dict(target_ref) if isinstance(target_ref, dict) else None
            status = _candidate_status(candidate)
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
                **_repair_mapping_fields(
                    repair_classes,
                    target_ref=target_ref,
                    criterion_ids=plan.get("target_criterion_ids") or [],
                    status=status,
                    selected_repair_class_id=selected_repair_class_id,
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
            status = _candidate_status(candidate)
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
                **_repair_mapping_fields(
                    repair_classes,
                    target_ref=target_ref,
                    criterion_ids=candidate.get("target_criterion_ids") or [],
                    status=status,
                    selected_repair_class_id=selected_repair_class_id,
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


def _probe_need(
    *,
    divergent: bool,
    repair_class_ids: list[str],
    common_repair_cover: bool,
    incomplete_repair_mapping: bool,
) -> dict[str, Any]:
    """State what a probe would have to resolve — never whether to run one.

    The receipt owns evidence, not policy.  ``probe_now`` / ``defer_*`` /
    ``skip_*`` belong to ``causal_probe_coherence.ProbeDecision``, which reads
    these facts alongside EVSI inputs the receipt cannot see.
    """

    if common_repair_cover:
        reason = "one safe repair covers every plausible cause"
    elif incomplete_repair_mapping:
        reason = (
            "at least one plausible cause has no mapped repair class; "
            "machine-side backfill is required before a learner probe"
        )
    elif divergent:
        reason = "plausible causes map to different repair classes"
    else:
        reason = "no explicitly validated common repair cover"
    return {
        "divergent": bool(divergent),
        "repair_class_ids": sorted(str(value) for value in repair_class_ids),
        "common_repair_cover": bool(common_repair_cover),
        "incomplete_repair_mapping": bool(incomplete_repair_mapping),
        "reason": reason,
    }


def receipt_probe_need(receipt: dict[str, Any] | None) -> dict[str, Any] | None:
    """Read `probe_need` from a receipt of any schema version.

    Schema 2 receipts only carry the old `probe_decision` verbs; translate them
    rather than making every reader branch on `schema_version`.
    """

    if not isinstance(receipt, dict):
        return None
    need = receipt.get("probe_need")
    if isinstance(need, dict):
        return dict(need)
    legacy = receipt.get("probe_decision")
    if not isinstance(legacy, dict):
        return None
    decision = str(legacy.get("decision") or "")
    return _probe_need(
        divergent=decision == "consider_probe",
        repair_class_ids=[],
        common_repair_cover=decision == "skip_common_repair",
        # Schema 2 never recorded it, and claiming completeness would be a
        # fabrication.
        incomplete_repair_mapping=False,
    ) | {"reason": str(legacy.get("reason") or ""), "legacy_schema": True}


def receipt_trace_consistency(
    receipt: dict[str, Any] | None,
    *,
    hypothesis_ids: list[str] | None = None,
) -> dict[str, str]:
    """Read the per-hypothesis trace-consistency map from any schema version.

    A schema 2 receipt carries only the receipt-level bool, which cannot be
    attributed to a hypothesis after the fact; every hypothesis reads `unknown`
    rather than inheriting a verdict it may not have earned.
    """

    if not isinstance(receipt, dict):
        return {}
    states = receipt.get("trace_consistency")
    if isinstance(states, dict):
        return {
            str(key): (
                str(value)
                if str(value) in TRACE_CONSISTENCY_STATES
                else "unknown"
            )
            for key, value in states.items()
        }
    ids = hypothesis_ids
    if ids is None:
        ids = [
            str(ref["id"])
            for ref in receipt.get("hypotheses") or []
            if isinstance(ref, dict) and ref.get("id")
        ]
    return {value: "unknown" for value in ids}


def _attempt_trace_contract(
    vault: LoadedVault, attempt: dict[str, Any]
) -> Any:
    """The authored decomposition of the item an attempt was made on.

    Handed to :func:`select_minimal_repair` so backtracking depth and checkpoint
    claims are computed while candidates are being RANKED. There is deliberately
    no post-selection recompute: the depth used to be derived here, after the
    winner was already chosen, which is how a deterministic quantity ended up
    decorating a receipt while self-reports did the ordering (A1).
    """

    item = vault.practice_items.get(
        str(attempt.get("practice_item_id") or "")
    )
    return item.trace_contract if item is not None else None


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
        # A1: the item's authored decomposition is what makes backtracking depth
        # and checkpoint claims verifiable at RANKING time. Without it the
        # selector silently falls back to the model's self-reported counts.
        trace_contract=_attempt_trace_contract(vault, attempt),
        learner_answer_md=str(attempt.get("learner_answer_md") or ""),
    )
    specs, factor_specs = _hypothesis_specs(
        vault,
        repository,
        attempt_id=attempt_id,
        repair_classes=repair_classes,
        selected_repair_class_id=_selected_repair_class_id(selection),
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
            # `backtracking_depth`, `trace_edit_cost`, and `text_diff` used to be
            # recomputed here, AFTER selection, from the same inputs the ranker
            # now uses -- which is precisely how two deterministic quantities
            # ended up decorating a receipt while self-reports did the ordering
            # (A1). They are set once, at rank time, against the attempt's real
            # `learner_answer_md`. Only the anchors are a post-selection fact.
            minimality["divergence_anchors"] = divergence_anchors
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
    activity = repository.causal_activity_classification(attempt_id)
    contamination_class = (
        str(activity["contamination_class"])
        if activity is not None
        else (
            "repair_activity"
            if attempt.get("primed")
            else (
                (
                    "instructional_diagnostic"
                    if int(attempt.get("hints_used") or 0) > 0
                    else "pure_diagnostic"
                )
                if attempt.get("attempt_type") == "diagnostic_probe"
                else None
            )
        )
    )
    trace_consistency, trace_consistency_detail = _trace_consistency_states(
        vault, repository, attempt_id, hypotheses
    )
    unmapped_concrete = [
        str(value["id"])
        for value in concrete
        if not value.get("repair_class_id")
    ]
    # WHY each concrete hypothesis failed to map, not just THAT it did.  Each
    # reason names a different machine-side remedy (author a repair / re-target
    # it / disambiguate two rivals / localize the hypothesis), so the backfill
    # this routes to is actionable instead of an undifferentiated "unmapped".
    repair_mapping_gaps = {
        str(value["id"]): str(
            value.get("repair_class_unresolved_reason")
            or "no_matching_repair_target"
        )
        for value in concrete
        if not value.get("repair_class_id")
    }
    probe_need = _probe_need(
        divergent=len(mapped_repair_ids) > 1,
        repair_class_ids=sorted(mapped_repair_ids),
        common_repair_cover=common_cover,
        incomplete_repair_mapping=bool(unmapped_concrete),
    )
    receipt_body = {
        "schema_version": DIAGNOSIS_RECEIPT_SCHEMA_VERSION,
        "decision_policy_version": CAUSAL_DECISION_POLICY_VERSION,
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
                "repair_class_basis": value.get("repair_class_basis"),
                "repair_class_unresolved_reason": value.get(
                    "repair_class_unresolved_reason"
                ),
            }
            for value in hypotheses
        ],
        "support_scores": support_scores,
        "model_reported_support_proposals": (
            model_reported_support_proposals
        ),
        # A single attempt earns no approved authority.  The honest value is the
        # one that keeps `failure_triage` from PROMOTING on it (§2); it may still
        # veto.
        "support_authority": DEFAULT_SUPPORT_AUTHORITY,
        "trace_consistency": trace_consistency,
        "trace_consistency_detail": trace_consistency_detail,
        # DEPRECATED: receipt-level alias retained for the P1 claim-check
        # overlay.  Read `trace_consistency` instead — this bool cannot say
        # WHICH hypothesis was contradicted.
        "trace_consistent": not any(
            value == "contradicted" for value in trace_consistency.values()
        ),
        "plausible_set": [value["id"] for value in concrete],
        "ordinal_ranking": [],
        "repair_classes": repair_classes,
        "repair_class_ranking": selection["ranking"],
        "repair_selection": selection,
        # Which regime ordered the repair ranking (A1 / standing constraint 4).
        # P4 trains on these receipts and must not read a model-reported
        # ordering as a structural one.
        "repair_selection_basis": selection.get("selection_basis"),
        "repair_policy_version": REPAIR_POLICY_VERSION,
        "common_repair_cover": {
            "covers_plausible_set": common_cover,
            "repair_class_id": (
                common_repair_class_id if common_cover else None
            ),
            "matrix": cover_matrix,
        },
        "probe_need": probe_need,
        # DEPRECATED: the receipt states a NEED, never a decision.  The verbs
        # live on `causal_probe_coherence.ProbeDecision`; this alias exists so
        # readers of the old key keep working for one release.
        "probe_decision": {**probe_need, "decision": "see probe_need"},
        "unmapped_hypothesis_ids": unmapped_concrete,
        # hypothesis_id -> REPAIR_MAPPING_UNRESOLVED_REASONS member.  The typed
        # backfill obligation §5.3/principle 8 owes the machine side; never a
        # reason to ask the learner to discriminate.
        "repair_mapping_gaps": repair_mapping_gaps,
        "contamination_class": contamination_class,
        # Kept as a display-policy alias for the P1 overlay, whose fail-closed
        # gate landed before the P2 class record existed.
        "contamination_status": contamination_class,
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
    hypothesis_ids = [str(value["id"]) for value in hypotheses]
    return {
        "attempt_id": attempt_id,
        "receipt": receipt,
        "hypotheses": hypotheses,
        # Normalized P2 reads, so the CLI and the Tauri overlay never branch on
        # the receipt's schema version themselves.
        "trace_consistency": receipt_trace_consistency(
            receipt if isinstance(receipt, dict) else None,
            hypothesis_ids=hypothesis_ids,
        ),
        "probe_need": receipt_probe_need(
            receipt if isinstance(receipt, dict) else None
        ),
        "decision_policy_version": (
            receipt.get("decision_policy_version")
            if isinstance(receipt, dict)
            else None
        ),
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
    trace_consistency = episode.get("trace_consistency") or {}
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
                    "support_authority": receipt.get("support_authority"),
                    "trace_consistency": trace_consistency.get(
                        str(hypothesis["id"]), "unknown"
                    ),
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
        "trace_consistency": dict(trace_consistency),
        "probe_need": episode.get("probe_need"),
        "decision_policy_version": episode.get("decision_policy_version"),
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
        refs.append({"hypothesis_id": OPEN_SET_CAUSE_ID, "open_set": True})
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


def _claim_hypothesis_id(
    claim: dict[str, Any],
    *,
    labels: dict[str, str],
    by_index: list[str | None],
    known_ids: set[str],
) -> str | None:
    """Resolve an explicit hypothesis reference carried by a claim, if any."""

    for key in ("hypothesis_id", "candidate_id", "cause_id"):
        raw = claim.get(key)
        if raw is None:
            continue
        value = str(raw)
        if value in known_ids:
            return value
        if value in labels:
            return labels[value]
    index = claim.get("candidate_index")
    if isinstance(index, int) and 0 <= index < len(by_index):
        return by_index[index]
    statement = str(claim.get("statement") or "").strip()
    if statement:
        return labels.get(_normalized(statement))
    return None


def _postdictive_claim_attribution(
    repository: Repository,
    attempt_id: str,
    hypotheses: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    """Attribute each deterministic claim to at most ONE hypothesis.

    Postdictive claims live on ``error_events[].repair_plan``, one level above
    the candidate causes, and P1 copies the whole plan-level list onto every
    candidate of that event.  Crediting a claim to every candidate would let one
    hypothesis's falsifiable commitment corroborate its rivals, so a claim is
    attributed only when it names a candidate explicitly or when the event
    proposed exactly one concrete cause.  Anything else is returned unattributed
    rather than smeared.
    """

    by_episode = {
        str(hypothesis["episode_key"]): hypothesis for hypothesis in hypotheses
    }
    known_ids = {str(hypothesis["id"]) for hypothesis in hypotheses}
    attributed: dict[str, list[dict[str, Any]]] = {
        hypothesis_id: [] for hypothesis_id in known_ids
    }
    unattributed: list[dict[str, Any]] = []
    for event in repository.error_events_for_attempt(attempt_id):
        plan = event.get("repair_plan")
        plan = plan if isinstance(plan, dict) else {}
        claims = [
            dict(value)
            for value in plan.get("postdictive_claims") or []
            if isinstance(value, dict)
        ]
        if not claims:
            continue
        event_id = str(event["id"])
        labels: dict[str, str] = {}
        by_index: list[str | None] = []
        concrete: list[str] = []
        for candidate in _event_candidate_causes(event):
            statement = str(candidate.get("statement") or "").strip()
            if not statement:
                by_index.append(None)
                continue
            target_ref = candidate.get("target_ref")
            target_ref = (
                dict(target_ref) if isinstance(target_ref, dict) else None
            )
            status = _candidate_status(candidate)
            candidate_key = _candidate_key(
                candidate, target_ref=target_ref, status=status
            )
            hypothesis = by_episode.get(
                f"{attempt_id}:event:{event_id}:{candidate_key}"
            )
            hypothesis_id = (
                str(hypothesis["id"]) if hypothesis is not None else None
            )
            by_index.append(hypothesis_id)
            if hypothesis is None or hypothesis_id is None:
                continue
            if str(hypothesis.get("status")) != "open_set":
                concrete.append(hypothesis_id)
            for label in (
                candidate.get("hypothesis_id"),
                candidate.get("id"),
                candidate.get("candidate_id"),
            ):
                if label:
                    labels.setdefault(str(label), hypothesis_id)
            labels.setdefault(_normalized(statement), hypothesis_id)
        for claim in claims:
            hypothesis_id = _claim_hypothesis_id(
                claim, labels=labels, by_index=by_index, known_ids=known_ids
            )
            if hypothesis_id is None and len(concrete) == 1:
                hypothesis_id = concrete[0]
            if hypothesis_id is None:
                unattributed.append(
                    {
                        "error_event_id": event_id,
                        "claim": claim,
                        "reason": (
                            "ambiguous_between_candidates"
                            if len(concrete) > 1
                            else "no_materialized_hypothesis"
                        ),
                    }
                )
                continue
            attributed.setdefault(hypothesis_id, []).append(claim)
    return attributed, unattributed


def _trace_consistency_states(
    vault: LoadedVault,
    repository: Repository,
    attempt_id: str,
    hypotheses: list[dict[str, Any]] | None = None,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Per-hypothesis trace-consistency states plus their audit detail (§5.6).

    The veto is scoped to the hypothesis that made the falsifiable claim.  A
    hypothesis that committed to nothing is ``no_deterministic_claims`` — absence
    of evidence, never corroboration — and an unverifiable claim is ``unknown``,
    which is distinct from ``contradicted``.
    """

    if hypotheses is None:
        hypotheses = repository.causal_hypotheses_for_attempt(attempt_id)
    hypothesis_ids = [str(hypothesis["id"]) for hypothesis in hypotheses]
    attempt = repository.fetch_practice_attempt(attempt_id)
    item = (
        vault.practice_items.get(str(attempt.get("practice_item_id") or ""))
        if attempt is not None
        else None
    )
    rubric = vault.rubric_for_item(item) if item is not None else None
    attributed, unattributed = _postdictive_claim_attribution(
        repository, attempt_id, hypotheses
    )
    detail: dict[str, Any] = {
        "policy_version": CAUSAL_DECISION_POLICY_VERSION,
        "rubric_available": rubric is not None,
        "unattributed_postdictive_claims": unattributed,
        "by_hypothesis": {},
    }
    if rubric is None:
        states = {value: "unknown" for value in hypothesis_ids}
        detail["by_hypothesis"] = {
            value: {
                "state": "unknown",
                "reason": (
                    "attempt_unavailable" if attempt is None else "rubric_unavailable"
                ),
                "claims_attributed": len(attributed.get(value) or []),
                "claims_checked": 0,
                "contradicted_criterion_ids": [],
            }
            for value in hypothesis_ids
        }
        return states, detail
    maxima = {
        criterion.id: float(criterion.points) for criterion in rubric.criteria
    }
    awarded = {
        row.criterion_id: float(row.points_awarded)
        for row in repository.fetch_grading_evidence(attempt_id)
    }
    states: dict[str, str] = {}
    for hypothesis_id in hypothesis_ids:
        claims = attributed.get(hypothesis_id) or []
        deterministic = [
            claim for claim in claims if str(claim.get("criterion_id") or "")
        ]
        contradicted: list[str] = []
        checked = 0
        unverifiable = 0
        for claim in deterministic:
            criterion_id = str(claim["criterion_id"])
            maximum = maxima.get(criterion_id)
            if (
                maximum is None
                or maximum <= 0
                or criterion_id not in awarded
            ):
                unverifiable += 1
                continue
            checked += 1
            if awarded[criterion_id] >= maximum - 1e-9:
                contradicted.append(criterion_id)
        if contradicted:
            state = "contradicted"
            reason = "full_credit_criterion_contradicts_claim"
        elif checked:
            state = "consistent_with_claims"
            reason = "every_attributed_claim_held"
        elif deterministic:
            state = "unknown"
            reason = "claim_criteria_were_not_assessed"
        else:
            state = "no_deterministic_claims"
            reason = "hypothesis_made_no_falsifiable_claim"
        states[hypothesis_id] = state
        detail["by_hypothesis"][hypothesis_id] = {
            "state": state,
            "reason": reason,
            "claims_attributed": len(claims),
            "claims_checked": checked,
            "claims_unverifiable": unverifiable,
            "contradicted_criterion_ids": sorted(set(contradicted)),
        }
    return states, detail


def _trace_consistent(
    vault: LoadedVault,
    repository: Repository,
    attempt_id: str,
    *,
    hypothesis_id: str | None = None,
) -> bool:
    """DEPRECATED receipt-level veto; prefer ``_trace_consistency_states``.

    Retained fail-closed for the learner-confirmation path, which must not open
    a provisional belief on an attempt whose rubric could not be read at all.
    """

    states, detail = _trace_consistency_states(vault, repository, attempt_id)
    if not detail["rubric_available"]:
        return False
    if hypothesis_id:
        state = states.get(str(hypothesis_id))
        if state is not None:
            return state != "contradicted"
    return not any(value == "contradicted" for value in states.values())


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
        if not isinstance(raw, dict) or (
            raw.get("open_set") is True
            or raw.get("hypothesis_id") == OPEN_SET_CAUSE_ID
        ):
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
    #: Set when the confirmed belief is a `causal_hypotheses` chain, so the
    #: returned id can be re-resolved to the live head after re-materialization.
    confirmed_episode_key: str | None = None
    resolved = False
    if selected is not None and _trace_consistent(
        vault,
        repository,
        attempt_id,
        # The veto is scoped to the hypothesis the learner confirmed; a rival
        # hypothesis's contradicted claim says nothing about this one (§5.6).
        hypothesis_id=str(selected.get("hypothesis_id") or "") or None,
    ):
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
                confirmed_episode_key = str(selected_hypothesis["episode_key"])
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
            if confirmed_episode_key is not None:
                # `causal_hypotheses` is append-only, and the re-materialization
                # above may append a further version of the very row we just
                # confirmed.  Returning the id we wrote would hand the caller a
                # SUPERSEDED version, which `misconception_candidate_by_id` no
                # longer resolves (the compatibility projection groups heads
                # only) -- so the repair surface 404'd on the belief the learner
                # had just confirmed.  Return the live head.
                head = repository.latest_causal_hypothesis_for_episode(
                    confirmed_episode_key
                )
                if head is not None:
                    provisional_belief_id = str(head["id"])
    return {
        "factor_id": factor_id,
        "response": response,
        "resolved": resolved,
        "provisional_belief_id": provisional_belief_id,
        "observation_id": observation_id,
    }
