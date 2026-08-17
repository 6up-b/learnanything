"""P2 causal probe coherence.

This module composes the P1 causal-hypothesis/repair receipts with the existing
diagnostic-episode machinery.  Its invariants are deliberately structural:

* ambiguity is action-relevant only when plausible causes map to different
  episode repair classes;
* a probe is purchased only when information can change that action and its
  expected avoided burden exceeds the probe burden;
* prediction bundles are generated from a typed, allowlisted, observation-blind
  input — nothing else is expressible, so there is nothing to blocklist;
* a bundle's predicted features are *declared* key sets matched exactly, never
  a subset match against whatever the grader happened to emit;
* an administered probe is classified against the bundles that were **pinned**
  when the probe was minted, so a later bundle cannot rewrite a replay;
* item variants must declare and survive a shared manipulation diff audit;
* diagnostic, instructional, repair, and verification evidence remain separate;
* a successful cold repair supports the repair effect, not the diagnosis.

Missing machine-side data never buys learner effort (spec principle 8): an
unmapped hypothesis routes to backfill (``insufficient_mapping``), never to a
probe.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
from typing import Any, Callable, Iterable, Mapping, Sequence

from learnloop.clock import Clock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.services.canonical_projection import surface_group_id
from learnloop.services.causal_activity_policy import assess_near_clone
from learnloop.services.causal_attribution import (
    CAUSAL_DECISION_POLICY_VERSION,
    OPEN_SET_CAUSE_ID,
    SUPPORT_BASIS_AUTHORITY,
)
from learnloop.services.fitted_params import CAUSAL_PROBE_POLICY_SCOPE
from learnloop.services.probe_hypotheses import H_OTHER
from learnloop.services.probes import Hypothesis, HypothesisSet
from learnloop.vault.models import LoadedVault, PracticeItem

PROBE_REVIEW_TRANSITIONS = {
    "candidate": {"registered", "rejected"},
    "registered": {"reviewed", "rejected"},
    "reviewed": {"active", "rejected"},
    # An active instrument may be withdrawn when its input contract is found
    # invalid. The event log preserves the prior activation and the reason.
    "active": {"rejected"},
    "rejected": set(),
}

#: Version of the allowlisted input supplied to a blind prediction generator.
#: v1 included observation-conditioned ``postdictive_claims`` and is therefore
#: permanently ineligible for registration or serving.
BLIND_INPUT_CONTRACT_VERSION = "observation_free_hypothesis_target_v2"

#: Typed reasons a declared feature row is unusable.  Recorded rather than
#: silently dropped so a null-on-100%-of-bundles field is visible (standing
#: constraint 2 watches both tails).
FEATURE_ROW_SKIP_REASONS = (
    "empty_feature_row",
    "non_mapping_feature_row",
    "declared_keys_do_not_match_values",
    "non_string_feature_key",
)

#: Typed classification outcomes (§3.5).  ``all_bundles_matched`` means the
#: instrument did not discriminate; ``no_bundle_matched`` is genuine open-set
#: evidence.  Only the latter supports H_OTHER.
CLASSIFICATION_OUTCOMES = (
    "matched_single",
    "matched_multiple",
    "no_bundle_matched",
    "all_bundles_matched",
    "cohort_mismatch",
    "unparsed_features",
)

RUNG_GATE_STATES = ("common_cover", "divergent", "insufficient_mapping")


# --- fitted parameter resolution -------------------------------------------
#
# Every knob below used to be a literal in the decision path.  They are policy
# choices, not truths, so they live in the fitted-parameter store (scope
# ``causal_probe_policy``) with pinned heuristic defaults and a lifecycle stamp
# that rides on the decision receipt.


CAUSAL_PROBE_POLICY_DEFAULTS: dict[str, float] = {
    # build_causal_hypothesis_set: H_OTHER's share of the locked prior.
    "open_set_prior_weight": 0.1,
    "open_set_prior_floor": 0.1,
    # record_delayed_cold_verification: correctness at/above which a fresh
    # cross-surface attempt counts as a repair-effect success.
    "cold_verification_success_correctness": 0.8,
    # decide_probe EVSI knobs.
    "recent_diagnostic_limit": 2.0,
    "minimum_expected_information_gain": 0.0,
    "minimum_action_change_probability": 0.0,
    "probe_value_margin_minutes": 0.0,
}

_CAUSAL_PROBE_POLICY_BOUNDS: dict[str, tuple[float, float]] = {
    "open_set_prior_weight": (0.0, 1.0),
    "open_set_prior_floor": (0.0, 1.0),
    "cold_verification_success_correctness": (0.0, 1.0),
    "recent_diagnostic_limit": (-1.0, 100.0),
    "minimum_expected_information_gain": (0.0, 1.0),
    "minimum_action_change_probability": (0.0, 1.0),
    "probe_value_margin_minutes": (0.0, 600.0),
}


@dataclass(frozen=True)
class CausalProbeParameters:
    """Resolved probe-policy knobs plus their provenance.

    ``lifecycle`` is ``"heuristic_default"`` until `learnloop fit` owns the
    scope; the decision receipt carries the manifest so a replayed decision can
    be attributed to the parameters that produced it.
    """

    values: Mapping[str, float]
    lifecycle: str = "heuristic_default"
    fitted_set_id: str | None = None
    invalid_keys: tuple[str, ...] = ()

    def __getitem__(self, key: str) -> float:
        return float(self.values[key])

    @property
    def recent_diagnostic_limit(self) -> int:
        return int(self.values["recent_diagnostic_limit"])

    def manifest(self) -> dict[str, Any]:
        return {
            "scope": CAUSAL_PROBE_POLICY_SCOPE,
            "lifecycle": self.lifecycle,
            "fitted_set_id": self.fitted_set_id,
            "values": dict(self.values),
            "invalid_keys": list(self.invalid_keys),
        }


def resolve_causal_probe_parameters(
    repository: Repository | None,
) -> CausalProbeParameters:
    """Active fitted probe-policy knobs, else the pinned heuristic defaults.

    A malformed fitted value falls back to its default and is reported in
    ``invalid_keys`` rather than crashing the decision path.
    """

    values = dict(CAUSAL_PROBE_POLICY_DEFAULTS)
    if repository is None:
        return CausalProbeParameters(values=values)
    record = repository.active_fitted_parameters(CAUSAL_PROBE_POLICY_SCOPE)
    if record is None:
        return CausalProbeParameters(values=values)
    params = record.get("params") or {}
    invalid: list[str] = []
    for key, default in CAUSAL_PROBE_POLICY_DEFAULTS.items():
        if key not in params:
            continue
        low, high = _CAUSAL_PROBE_POLICY_BOUNDS[key]
        raw = params[key]
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            invalid.append(key)
            continue
        candidate = float(raw)
        if not math.isfinite(candidate) or not (low <= candidate <= high):
            invalid.append(key)
            continue
        values[key] = candidate
    return CausalProbeParameters(
        values=values,
        lifecycle="fitted",
        fitted_set_id=str(record["id"]),
        invalid_keys=tuple(sorted(invalid)),
    )


def _content_id(prefix: str, value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(encoded).hexdigest()[:26]}"


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _canonical(value: Any) -> str:
    return json.dumps(
        _jsonable(value), sort_keys=True, separators=(",", ":"), default=str
    )


# --- §3.1 the one shared feature-row parser ---------------------------------


@dataclass(frozen=True)
class BundleFeatureRow:
    """One declared prediction row.

    ``keys`` is the row's own DECLARED key set (sorted, non-empty).  Matching is
    exact over exactly those keys: every declared key must be *present* in the
    observation and compare equal.  There are no subset semantics — an empty row
    would match every observation vacuously, which is why it is rejected.
    """

    keys: tuple[str, ...]
    values: dict[str, Any]

    def matches(self, observed_features: Mapping[str, Any]) -> bool:
        for key in self.keys:
            if key not in observed_features:
                return False
            if _canonical(observed_features[key]) != _canonical(
                self.values[key]
            ):
                return False
        return True

    def as_record(self) -> dict[str, Any]:
        return {"keys": list(self.keys), "values": dict(self.values)}


@dataclass(frozen=True)
class BundleFeatureRowReport:
    rows: tuple[BundleFeatureRow, ...] = ()
    skipped: tuple[dict[str, Any], ...] = ()

    @property
    def usable(self) -> bool:
        return bool(self.rows)


def _feature_row_from_mapping(
    source: str, raw: Any
) -> tuple[BundleFeatureRow | None, dict[str, Any] | None]:
    """Build one row, or a typed skip record.  Never silently drops."""

    if not isinstance(raw, Mapping):
        return None, {"source": source, "reason": "non_mapping_feature_row"}
    declared = raw.get("keys")
    payload = raw.get("values")
    if isinstance(declared, (list, tuple)) and isinstance(payload, Mapping):
        keys = tuple(str(value) for value in declared)
        values = {str(key): _jsonable(item) for key, item in payload.items()}
        if set(keys) != set(values):
            return None, {
                "source": source,
                "reason": "declared_keys_do_not_match_values",
            }
    else:
        values = {str(key): _jsonable(item) for key, item in raw.items()}
        keys = tuple(values)
    if any(not key.strip() for key in keys):
        return None, {"source": source, "reason": "non_string_feature_key"}
    if not keys:
        return None, {"source": source, "reason": "empty_feature_row"}
    ordered = tuple(sorted(keys))
    return BundleFeatureRow(keys=ordered, values={k: values[k] for k in ordered}), None


def bundle_feature_row_report(
    predictions: Mapping[str, Any] | None,
) -> BundleFeatureRowReport:
    """Parse every declared feature row plus the typed reasons for the rest.

    Accepted shapes (a bundle may use more than one):

    * ``{"feature_rows": [{"keys": [...], "values": {...}}, ...]}`` — explicit;
    * ``{"predicted_features": {...}}`` — the mapping's own keys are declared;
    * ``{"outcomes": [{"features": {...}}, ...]}``.
    """

    rows: list[BundleFeatureRow] = []
    skipped: list[dict[str, Any]] = []
    if not isinstance(predictions, Mapping):
        return BundleFeatureRowReport(
            skipped=({"source": "predictions", "reason": "non_mapping_feature_row"},)
        )

    def absorb(source: str, raw: Any) -> None:
        row, skip = _feature_row_from_mapping(source, raw)
        if row is not None:
            rows.append(row)
        elif skip is not None:
            skipped.append(skip)

    explicit = predictions.get("feature_rows")
    if isinstance(explicit, (list, tuple)):
        for entry in explicit:
            absorb("feature_rows", entry)
    direct = predictions.get("predicted_features")
    if direct is not None:
        absorb("predicted_features", direct)
    outcomes = predictions.get("outcomes")
    if isinstance(outcomes, (list, tuple)):
        for entry in outcomes:
            if not isinstance(entry, Mapping):
                skipped.append(
                    {"source": "outcomes", "reason": "non_mapping_feature_row"}
                )
                continue
            if "features" not in entry:
                continue
            absorb("outcomes", entry.get("features"))

    deduped: list[BundleFeatureRow] = []
    seen: set[str] = set()
    for row in rows:
        fingerprint = _canonical(row.as_record())
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        deduped.append(row)
    assert all(entry["reason"] in FEATURE_ROW_SKIP_REASONS for entry in skipped)
    return BundleFeatureRowReport(rows=tuple(deduped), skipped=tuple(skipped))


def parse_bundle_feature_rows(
    predictions: Mapping[str, Any],
) -> list[BundleFeatureRow]:
    """The single parser used by generation, discrimination, and classification."""

    return list(bundle_feature_row_report(predictions).rows)


# --- §3.3 real pairwise separability ----------------------------------------


def _rows_conflict(left: BundleFeatureRow, right: BundleFeatureRow) -> bool:
    """True iff the rows disagree on a key they BOTH declare.

    Disjoint key sets never conflict: under partial observability a row that
    simply was not measured is absence of evidence, not a contradiction.
    """

    shared = set(left.keys) & set(right.keys)
    if not shared:
        return False
    return any(
        _canonical(left.values[key]) != _canonical(right.values[key])
        for key in sorted(shared)
    )


def _discriminating_row(
    row: BundleFeatureRow, others: Sequence[BundleFeatureRow]
) -> bool:
    return bool(others) and all(_rows_conflict(row, other) for other in others)


def rows_are_separable(
    left: Sequence[BundleFeatureRow], right: Sequence[BundleFeatureRow]
) -> bool:
    """True iff some observation can match exactly one of the two row sets.

    Requires a row on one side that conflicts with EVERY row on the other on a
    shared declared key.  "Some pair conflicts" is not enough: a hypothesis whose
    other row still matches the same observation is not distinguished by it.
    """

    if not left or not right:
        return False
    return any(_discriminating_row(row, right) for row in left) or any(
        _discriminating_row(row, left) for row in right
    )


# --- §3.8 the EVSI decision -------------------------------------------------


@dataclass(frozen=True)
class ProbeDecision:
    decision: str
    reason: str
    repair_class_ids: tuple[str, ...]
    high_priority_need: bool
    #: What a divergent factor holds is the BRANCH-SPECIFIC repair inside it —
    #: never "unrelated remediation" elsewhere, which is what this field used to
    #: be called and what the learner copy used to say.
    blocks_branch_specific_repair: bool
    expected_avoided_overteaching_minutes: float
    probe_burden_minutes: float
    machine_checks_first: tuple[str, ...] = ()
    parameters: dict[str, Any] = field(default_factory=dict)
    decision_policy_version: str = CAUSAL_DECISION_POLICY_VERSION

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["repair_class_ids"] = list(self.repair_class_ids)
        payload["machine_checks_first"] = list(self.machine_checks_first)
        return payload


def decide_probe(
    *,
    repair_class_ids: Sequence[str | None],
    common_repair_covers: bool,
    expected_information_gain: float,
    probability_information_changes_repair: float,
    probe_burden_minutes: float,
    avoided_overteaching_minutes: float,
    pending_machine_checks: Sequence[str] = (),
    session_budget_minutes: float | None = None,
    learner_preference: str = "allow",
    recent_diagnostic_burden: int = 0,
    repository: Repository | None = None,
    parameters: CausalProbeParameters | None = None,
) -> ProbeDecision:
    """Apply §7's EVSI-flavoured, action-relative probe rule.

    Information gain by itself is never sufficient.  The gain is discounted by
    the probability that it changes the selected repair, then valued only by
    avoided over-teaching.  Every threshold is resolved from the fitted store and
    returned on the decision as a parameter manifest for the receipt.
    """

    resolved = parameters or resolve_causal_probe_parameters(repository)
    classes = tuple(sorted({str(value) for value in repair_class_ids if value}))
    different_repairs = len(classes) > 1
    expected_avoided = (
        max(0.0, avoided_overteaching_minutes)
        * max(0.0, min(1.0, probability_information_changes_repair))
        * max(0.0, min(1.0, expected_information_gain))
    )
    base = {
        "repair_class_ids": classes,
        "high_priority_need": different_repairs and not common_repair_covers,
        "blocks_branch_specific_repair": (
            different_repairs and not common_repair_covers
        ),
        "expected_avoided_overteaching_minutes": expected_avoided,
        "probe_burden_minutes": max(0.0, probe_burden_minutes),
        "machine_checks_first": tuple(
            str(value) for value in pending_machine_checks
        ),
        "parameters": resolved.manifest(),
    }
    if common_repair_covers:
        return ProbeDecision(
            decision="skip_common_repair",
            reason="one low-cost repair covers the plausible cause set",
            **base,
        )
    if not different_repairs:
        return ProbeDecision(
            decision="skip_action_equivalent",
            reason="plausible causes imply the same episode repair class",
            **base,
        )
    if pending_machine_checks:
        return ProbeDecision(
            decision="defer_machine_checks",
            reason="machine-side checks must resolve their uncertainty first",
            **base,
        )
    if learner_preference in {"decline", "teach_now", "no_more_diagnostics"}:
        return ProbeDecision(
            decision="defer_learner_preference",
            reason="learner preference does not permit another probe now",
            **base,
        )
    limit = resolved.recent_diagnostic_limit
    if limit >= 0 and recent_diagnostic_burden >= limit:
        return ProbeDecision(
            decision="defer_recent_burden",
            reason="recent diagnostic burden reached the session limit",
            **base,
        )
    if (
        session_budget_minutes is not None
        and session_budget_minutes < probe_burden_minutes
    ):
        return ProbeDecision(
            decision="defer_session_budget",
            reason="the remaining session budget is smaller than probe burden",
            **base,
        )
    if expected_information_gain <= resolved["minimum_expected_information_gain"]:
        return ProbeDecision(
            decision="skip_no_discrimination",
            reason="the proposed probe has no expected discriminating information",
            **base,
        )
    if (
        probability_information_changes_repair
        <= resolved["minimum_action_change_probability"]
    ):
        return ProbeDecision(
            decision="skip_no_action_change",
            reason="the proposed information cannot change the selected repair",
            **base,
        )
    if expected_avoided <= (
        max(0.0, probe_burden_minutes) + resolved["probe_value_margin_minutes"]
    ):
        return ProbeDecision(
            decision="skip_burden_exceeds_value",
            reason="expected avoided over-teaching does not exceed probe burden",
            **base,
        )
    return ProbeDecision(
        decision="probe_now",
        reason="action-changing information is worth more than its burden",
        **base,
    )


def repair_class_need_for_factor(
    repository: Repository, factor_id: str
) -> dict[str, Any]:
    factor = repository.unresolved_cause_factor(factor_id)
    if factor is None:
        raise ValueError("unresolved-cause factor does not exist")
    candidates = [
        value
        for value in factor.get("candidate_causes") or []
        if isinstance(value, Mapping) and not value.get("open_set")
    ]
    classes = sorted(
        {
            str(value["repair_class_id"])
            for value in candidates
            if value.get("repair_class_id")
        }
    )
    receipt_cover = False
    debug = repository.attempt_debug_payload(str(factor["attempt_id"])) or {}
    attribution = debug.get("causal_attribution")
    receipt = (
        attribution.get("diagnosis_receipt")
        if isinstance(attribution, Mapping)
        else None
    )
    if isinstance(receipt, Mapping):
        cover = receipt.get("common_repair_cover")
        receipt_cover = bool(
            isinstance(cover, Mapping)
            and cover.get("covers_plausible_set")
        )
    divergent = len(classes) > 1 and not receipt_cover
    return {
        "factor_id": factor_id,
        "attempt_id": factor["attempt_id"],
        "repair_class_ids": classes,
        "repair_class_divergence": divergent,
        "high_priority_diagnostic_need": divergent,
        "blocks_branch_specific_repair": divergent,
        "common_repair_covers": receipt_cover,
    }


def rung_divergence_gate(
    repository: Repository,
    hypotheses: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Golden-path cause → repair-rung gate, tri-state (§3.7).

    Explicit repair-class ids take precedence.  A reviewed triage reason may use
    the seeded route's ladder entry as the closed-vocabulary repair class.

    ``insufficient_mapping`` is a *machine-side* backfill signal — an empty
    hypothesis set or any hypothesis whose repair class cannot be resolved.  It
    is never probe-worthy: missing machine data must not buy learner effort.
    """

    rows: list[dict[str, Any]] = []
    classes: set[str] = set()
    unresolved: list[str] = []
    for index, hypothesis in enumerate(hypotheses):
        hypothesis_id = str(
            hypothesis.get("hypothesis_id") or f"candidate:{index}"
        )
        repair_class_id = hypothesis.get("repair_class_id")
        basis = "causal_repair_class"
        if not repair_class_id:
            reason = hypothesis.get("triage_reason")
            route = (
                repository.failure_triage_route_for_reason(str(reason))
                if reason
                else None
            )
            repair_class_id = (
                f"golden_rung:{route['ladder_entry_stage']}"
                if route is not None and route.get("ladder_entry_stage")
                else None
            )
            basis = "golden_path_entry_rung"
        if repair_class_id:
            classes.add(str(repair_class_id))
        else:
            unresolved.append(hypothesis_id)
        rows.append(
            {
                "hypothesis_id": hypothesis_id,
                "repair_class_id": repair_class_id,
                "basis": basis if repair_class_id else "unresolved",
            }
        )

    if not rows:
        state = "insufficient_mapping"
        reason = "no hypotheses were supplied to map onto repair classes"
    elif unresolved:
        state = "insufficient_mapping"
        reason = (
            "at least one hypothesis has no resolvable repair class; backfill "
            "the mapping before considering a learner probe"
        )
    elif len(classes) > 1:
        state = "divergent"
        reason = "plausible causes imply different episode repair classes"
    else:
        state = "common_cover"
        reason = "every plausible cause maps to one episode repair class"
    assert state in RUNG_GATE_STATES

    return {
        "state": state,
        "reason": reason,
        "probe_worthy": state == "divergent",
        "repair_class_divergence": state == "divergent",
        "common_repair_cover": state == "common_cover",
        "requires_repair_mapping_backfill": state == "insufficient_mapping",
        "repair_class_ids": sorted(classes),
        "unresolved_hypothesis_ids": unresolved,
        "mapping": rows,
        "decision_policy_version": CAUSAL_DECISION_POLICY_VERSION,
    }


# NOTE (§6): there is deliberately no `remediation_block_reason` here any more.
# It was the pre-orchestrator hold: a string-returning predicate that scanned
# open factors and spoke of blocking "unrelated remediation". Nothing has called
# it since `causal_orchestrator.causal_repair_status` took over the decision, and
# what is actually held is the BRANCH-SPECIFIC repair inside the divergent factor
# — never unrelated repair elsewhere. A dead function that reads as live policy
# is the illusory-safety failure mode this review kept finding, so it is deleted
# rather than kept "just in case": `causal_repair_status` is the single hold, and
# it composes `repair_class_need_for_factor` (below) directly.


# --- §3.8 the locked hypothesis set -----------------------------------------


@dataclass(frozen=True)
class CausalHypothesisSetPlan:
    """An unlocked set plus the provenance of its prior.

    ``prior_basis`` is stamped onto the locked record so an authored uniform
    fallback is never mistaken for a locked experimental prior.
    """

    learning_object_id: str
    hypotheses: list[Hypothesis]
    prior: dict[str, float]
    prior_basis: str
    hypothesis_versions: dict[str, int]
    parameters: dict[str, Any]

    def as_hypothesis_set(self, set_id: str | None = None) -> HypothesisSet:
        return HypothesisSet(
            learning_object_id=self.learning_object_id,
            hypotheses=self.hypotheses,
            prior=self.prior,
            id=set_id,
        )


def _hypothesis_prior_weight(hypothesis: Mapping[str, Any]) -> float:
    """The grader's normalized verbalized prior for one hypothesis, or 0.0.

    Absent on everything drafted before slice 3, which is what keeps the
    uniform fallback reachable and every existing locked set replayable.
    """

    evidence = hypothesis.get("evidence")
    if not isinstance(evidence, Mapping):
        return 0.0
    try:
        weight = float(evidence.get("prior_weight"))
    except (TypeError, ValueError):
        return 0.0
    return weight if weight > 0.0 else 0.0


def build_causal_hypothesis_set(
    repository: Repository,
    factor_id: str,
    *,
    support_scores: Mapping[str, float | None] | None = None,
) -> CausalHypothesisSetPlan:
    """Build the hypothesis-set plan from P1 ids, always with H_OTHER.

    Two vocabularies meet here and they are NOT the same string.
    ``probe_hypotheses.H_OTHER`` (``"other_or_unknown"``) is the open-set *label*
    inside a probe hypothesis set — that is what the plan below emits. A
    *candidate cause row*'s open-world arm is carried by its ``open_set`` flag
    and, pre-materialization, by :data:`~causal_attribution.OPEN_SET_CAUSE_ID`
    (``"H_OTHER"``). This function used to test the cause row's
    ``hypothesis_id`` against the probe LABEL, which could never match: dead code
    in the shape of a safety net, correct only because the flag check beside it
    did all the work. The id test now compares against the value that is actually
    written, and the flag remains the primary carrier.
    """

    factor = repository.unresolved_cause_factor(factor_id)
    if factor is None or factor.get("status") != "open":
        raise ValueError("an open unresolved-cause factor is required")
    concrete: list[dict[str, Any]] = []
    has_open_set = False
    for value in factor.get("candidate_causes") or []:
        if not isinstance(value, Mapping):
            continue
        if value.get("open_set") or value.get("hypothesis_id") == OPEN_SET_CAUSE_ID:
            has_open_set = True
            continue
        hypothesis_id = value.get("hypothesis_id")
        if not hypothesis_id:
            continue
        hypothesis = repository.causal_hypothesis(str(hypothesis_id))
        if hypothesis is not None:
            concrete.append(hypothesis)
    if not concrete:
        raise ValueError("factor has no concrete P1 causal hypotheses")
    if not has_open_set:
        raise ValueError("factor must preserve the H_OTHER open-set arm")

    parameters = resolve_causal_probe_parameters(repository)
    scores = dict(support_scores or {})
    weights = {
        str(value["id"]): max(0.0, float(scores.get(str(value["id"])) or 0.0))
        for value in concrete
    }
    if sum(weights.values()) > 0:
        prior_basis = "support_weighted"
    else:
        # No support score exists for any arm.  Before falling back to uniform,
        # ask the hypotheses what the grader SAID when it drafted them: slice 3
        # writes a normalized verbalized `prior_weight` into each hypothesis's
        # evidence, and a stated prior beats an invented one.
        #
        # It is still only a prior.  Measured support (`support_weighted`)
        # outranks it whenever it exists, and the basis string says which of the
        # three a reader is looking at so nobody can mistake a verbalized
        # ranking for a locked experimental prior.  Hypotheses drafted before
        # slice 3 carry no weight and land on `uniform_fallback` exactly as
        # they did before.
        verbalized = {
            str(value["id"]): _hypothesis_prior_weight(value) for value in concrete
        }
        if sum(verbalized.values()) > 0:
            prior_basis = "model_verbalized_prior"
            weights = {
                # A stated zero is a real statement ("I don't believe this
                # arm"), but a zero-mass probe arm can never be discriminated
                # against, so floor it rather than silently deleting the
                # hypothesis from its own experiment.
                key: max(value, parameters["open_set_prior_floor"])
                for key, value in verbalized.items()
            }
        else:
            prior_basis = "uniform_fallback"
            weights = {str(value["id"]): 1.0 for value in concrete}
    open_weight = max(
        sum(weights.values()) * parameters["open_set_prior_weight"],
        parameters["open_set_prior_floor"],
    )
    total = sum(weights.values()) + open_weight
    hypotheses = [
        Hypothesis(
            label=str(value["id"]),
            severity_at_entry=float(
                ((value.get("evidence") or {}).get("severity") or 0.0)
                if isinstance(value.get("evidence"), Mapping)
                else 0.0
            ),
        )
        for value in concrete
    ]
    hypotheses.append(Hypothesis(label=H_OTHER))
    prior = {key: value / total for key, value in weights.items()}
    prior[H_OTHER] = open_weight / total
    return CausalHypothesisSetPlan(
        learning_object_id=str(concrete[0]["learning_object_id"]),
        hypotheses=hypotheses,
        prior=prior,
        prior_basis=prior_basis,
        hypothesis_versions={
            str(value["id"]): int(value["version"]) for value in concrete
        },
        parameters=parameters.manifest(),
    )


def lock_causal_hypothesis_set(
    repository: Repository,
    factor_id: str,
    *,
    probe_phase_id: str | None,
    algorithm_version: str,
    support_scores: Mapping[str, float | None] | None = None,
    clock: Clock | None = None,
) -> HypothesisSet:
    plan = build_causal_hypothesis_set(
        repository, factor_id, support_scores=support_scores
    )
    records: list[dict[str, Any]] = []
    for hypothesis in plan.hypotheses:
        record = dict(hypothesis.as_record())
        version = plan.hypothesis_versions.get(hypothesis.label)
        if version is not None:
            # Pin the hypothesis VERSION into the locked set.  Classification
            # replays against the version that was locked, not whatever the
            # hypothesis has since been revised to.
            record["causal_hypothesis_version"] = version
        records.append(record)
    set_id = repository.insert_hypothesis_set(
        learning_object_id=plan.learning_object_id,
        probe_phase_id=probe_phase_id,
        hypotheses=records,
        prior=plan.prior,
        algorithm_version=algorithm_version,
        prior_basis=plan.prior_basis,
        clock=clock,
    )
    return plan.as_hypothesis_set(set_id)


# --- §3.6 the blind generation input ----------------------------------------


_RUBRIC_CRITERION_FIELDS = (
    "id",
    "criterion_id",
    "description",
    "points",
    "max_points",
    "measurement_status",
    "targets",
)


@dataclass(frozen=True)
class BlindGenerationInput:
    """The ONLY thing a blind prediction generator ever sees.

    Constructed field-by-field from typed sources.  Observation data is not
    expressible here, so there is nothing to blocklist — the previous deep
    blocklist scan both over-blocked (any item carrying ``observed_*``
    metadata) and under-blocked (an answer nested under an innocuous key).
    """

    hypothesis_id: str
    hypothesis_version: int
    statement: str
    cause_scope: str
    applicability: dict | None
    target_ref: dict | None
    item_prompt: str
    item_id: str
    rubric_criteria: list
    trace_contract: dict | None
    outcome_schema_version: str

    def as_payload(self) -> dict[str, Any]:
        return {
            "hypothesis": {
                "id": self.hypothesis_id,
                "version": self.hypothesis_version,
                "statement": self.statement,
                "cause_scope": self.cause_scope,
                "applicability": self.applicability,
                "target_ref": self.target_ref,
            },
            "item": {"id": self.item_id, "prompt": self.item_prompt},
            "rubric": {"criteria": self.rubric_criteria},
            "trace_contract": self.trace_contract,
            "outcome_schema_version": self.outcome_schema_version,
        }


def _rubric_criteria(rubric: Any) -> list[dict[str, Any]]:
    payload = _jsonable(rubric)
    if isinstance(payload, Mapping):
        raw = payload.get("criteria")
    elif isinstance(payload, (list, tuple)):
        raw = payload
    else:
        raw = None
    criteria: list[dict[str, Any]] = []
    for entry in raw or []:
        if not isinstance(entry, Mapping):
            continue
        criteria.append(
            {
                key: entry[key]
                for key in _RUBRIC_CRITERION_FIELDS
                if key in entry
            }
        )
    return criteria


def _optional_mapping(value: Any) -> dict | None:
    payload = _jsonable(value)
    return dict(payload) if isinstance(payload, Mapping) else None


def generate_blind_prediction_bundle(
    repository: Repository,
    *,
    hypothesis_id: str,
    item: PracticeItem | Mapping[str, Any],
    rubric: Any,
    trace_contract: Any,
    generator: Callable[[dict[str, Any]], Mapping[str, Any]],
    model_revision: str,
    outcome_schema_version: str,
    generation_agent_run_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Generate and persist a bundle from a typed, allowlisted blind input."""

    hypothesis = repository.causal_hypothesis(hypothesis_id)
    if hypothesis is None:
        raise ValueError("causal hypothesis does not exist")
    item_payload = _jsonable(item)
    if not isinstance(item_payload, Mapping):
        raise ValueError("item must be a practice-item payload")
    item_id = str(item_payload.get("id") or "")
    if not item_id:
        raise ValueError("prediction item requires an id")
    blind_input = BlindGenerationInput(
        hypothesis_id=str(hypothesis["id"]),
        hypothesis_version=int(hypothesis["version"]),
        statement=str(hypothesis["statement"]),
        cause_scope=str(hypothesis["cause_scope"]),
        applicability=_optional_mapping(hypothesis.get("applicability")),
        # Causal §5.1: postdictive claims are observation-conditioned and may
        # never feed probe discrimination. A blind bundle gets the hypothesis's
        # typed target plus the fresh item's authored contract instead.
        target_ref=_optional_mapping(hypothesis.get("target_ref")),
        item_prompt=str(item_payload.get("prompt") or ""),
        item_id=item_id,
        rubric_criteria=_rubric_criteria(rubric),
        trace_contract=_optional_mapping(trace_contract),
        outcome_schema_version=outcome_schema_version,
    )
    safe_input = blind_input.as_payload()
    predictions = _jsonable(dict(generator(safe_input)))
    if not predictions:
        raise ValueError("blind prediction generator returned no predictions")
    report = bundle_feature_row_report(predictions)
    empty = [
        entry
        for entry in report.skipped
        if entry["reason"] == "empty_feature_row"
    ]
    if empty:
        # An empty declared key set matches every observation vacuously.
        raise ValueError(
            "blind prediction bundle declared an empty feature row; every "
            "prediction row must declare at least one key"
        )
    if not report.rows:
        raise ValueError(
            "blind prediction bundle declared no usable feature rows: "
            f"{[entry['reason'] for entry in report.skipped] or 'no rows'}"
        )
    input_hash = _content_id("bpi", safe_input)
    identity = {
        "hypothesis_id": hypothesis_id,
        "hypothesis_version": blind_input.hypothesis_version,
        "practice_item_id": item_id,
        "input_hash": input_hash,
        "predictions": predictions,
        "model_revision": model_revision,
        "outcome_schema_version": outcome_schema_version,
    }
    return repository.insert_causal_blind_prediction_bundle(
        bundle_id=_content_id("bpb", identity),
        hypothesis_id=hypothesis_id,
        hypothesis_version=blind_input.hypothesis_version,
        practice_item_id=item_id,
        input_hash=input_hash,
        predictions=predictions,
        model_revision=model_revision,
        outcome_schema_version=outcome_schema_version,
        blind_input_contract_version=BLIND_INPUT_CONTRACT_VERSION,
        generation_agent_run_id=generation_agent_run_id,
        clock=clock,
    )


# --- §3.2 / §3.3 discrimination ---------------------------------------------


def _cohort_of(bundle: Mapping[str, Any]) -> tuple[str, str]:
    return (
        str(bundle.get("model_revision") or ""),
        str(bundle.get("outcome_schema_version") or ""),
    )


def _cohort_record(cohort: tuple[str, str]) -> dict[str, str]:
    return {
        "model_revision": cohort[0],
        "outcome_schema_version": cohort[1],
    }


def _single_cohort(
    bundles: Iterable[Mapping[str, Any]],
) -> tuple[tuple[str, str] | None, list[dict[str, str]]]:
    cohorts = sorted({_cohort_of(bundle) for bundle in bundles})
    if len(cohorts) == 1:
        return cohorts[0], [_cohort_record(cohorts[0])]
    return None, [_cohort_record(value) for value in cohorts]


def blind_bundle_discrimination(
    repository: Repository,
    *,
    hypothesis_ids: Sequence[str],
    practice_item_id: str,
) -> dict[str, Any]:
    """Assess discrimination using only stamped blind bundles.

    Requires one common ``(model_revision, outcome_schema_version)`` cohort and
    real pairwise separability under the actual matcher — full-payload JSON
    distinctness is not separability (two bundles differing only in prose used
    to pass here and then both match at classification).
    """

    wanted = sorted({str(value) for value in hypothesis_ids})
    bundles = repository.causal_blind_prediction_bundles(
        practice_item_id=practice_item_id,
        hypothesis_ids=wanted,
    )
    latest: dict[str, dict[str, Any]] = {}
    for bundle in bundles:
        if not bundle["generated_without_observation"]:
            continue
        if (
            bundle.get("blind_input_contract_version")
            != BLIND_INPUT_CONTRACT_VERSION
        ):
            continue
        latest[str(bundle["hypothesis_id"])] = bundle
    missing = [value for value in wanted if value not in latest]
    in_play = [latest[value] for value in wanted if value in latest]
    cohort, cohorts = _single_cohort(in_play)
    bundle_ids = [latest[value]["id"] for value in wanted if value in latest]

    base = {
        "basis": "blind_prediction_bundles_only",
        "practice_item_id": practice_item_id,
        "hypothesis_ids": wanted,
        "bundle_ids": bundle_ids,
        "missing_hypothesis_ids": missing,
        "cohort": _cohort_record(cohort) if cohort is not None else None,
        "cohorts": cohorts,
        "decision_policy_version": CAUSAL_DECISION_POLICY_VERSION,
    }
    if cohort is None and in_play:
        return {
            **base,
            "separable_pairs": [],
            "inseparable_pairs": [],
            "feature_row_issues": {},
            "distinguishable": False,
            "reason": "cohort_mismatch",
        }

    rows: dict[str, list[BundleFeatureRow]] = {}
    issues: dict[str, list[str]] = {}
    for hypothesis_id in wanted:
        bundle = latest.get(hypothesis_id)
        if bundle is None:
            continue
        report = bundle_feature_row_report(bundle["predictions"])
        rows[hypothesis_id] = list(report.rows)
        if report.skipped:
            issues[str(bundle["id"])] = [
                entry["reason"] for entry in report.skipped
            ]

    unusable = sorted(key for key, value in rows.items() if not value)
    separable: list[list[str]] = []
    inseparable: list[list[str]] = []
    resolved = sorted(rows)
    for index, left in enumerate(resolved):
        for right in resolved[index + 1 :]:
            pair = [left, right]
            if rows_are_separable(rows[left], rows[right]):
                separable.append(pair)
            else:
                inseparable.append(pair)

    if missing:
        reason = "missing_blind_bundles"
    elif unusable:
        reason = "unparsed_features"
    elif len(wanted) < 2:
        reason = "single_hypothesis"
    elif inseparable:
        reason = "inseparable_hypothesis_pairs"
    else:
        reason = "pairwise_separable"
    distinguishable = reason == "pairwise_separable"
    return {
        **base,
        "separable_pairs": separable,
        "inseparable_pairs": inseparable,
        "unusable_hypothesis_ids": unusable,
        "feature_row_issues": issues,
        "distinguishable": distinguishable,
        "reason": reason,
    }


# --- §3.4 / §3.5 classification ---------------------------------------------


def classify_against_blind_bundles(
    repository: Repository,
    *,
    hypothesis_set_id: str,
    practice_item_id: str,
    blind_bundle_ids: Sequence[str],
    observed_features: Mapping[str, Any],
) -> dict[str, Any]:
    """Classify an administered probe against the bundles PINNED to the probe.

    ``blind_bundle_ids`` is required and comes from
    ``causal_probe_candidates.blind_bundle_ids`` (or the probe presentation).
    A pinned id that does not resolve is an error, never a silent fallback to
    "whatever bundle is newest" — the substrate is append-only precisely so a
    later bundle cannot rewrite an earlier replay.
    """

    locked = repository.fetch_hypothesis_set(hypothesis_set_id)
    if locked is None:
        raise ValueError("locked hypothesis set does not exist")
    entries = [
        value
        for value in locked.get("hypotheses") or []
        if isinstance(value, Mapping) and value.get("label")
    ]
    concrete = [
        str(value["label"]) for value in entries if value["label"] != H_OTHER
    ]
    pinned_versions = {
        str(value["label"]): int(value["causal_hypothesis_version"])
        for value in entries
        if value.get("causal_hypothesis_version") is not None
    }

    pinned = [str(value) for value in blind_bundle_ids]
    if not pinned:
        raise ValueError(
            "classification requires the blind bundle ids pinned to the probe"
        )
    resolved: list[dict[str, Any]] = []
    for bundle_id in pinned:
        bundle = repository.causal_blind_prediction_bundle(bundle_id)
        if bundle is None:
            raise ValueError(
                f"pinned blind prediction bundle {bundle_id!r} does not resolve"
            )
        if not bundle["generated_without_observation"]:
            raise ValueError(
                f"pinned bundle {bundle_id!r} was not generated blind"
            )
        if str(bundle["practice_item_id"]) != practice_item_id:
            raise ValueError(
                f"pinned bundle {bundle_id!r} belongs to a different practice item"
            )
        resolved.append(bundle)

    cohort, cohorts = _single_cohort(resolved)
    base: dict[str, Any] = {
        "basis": "blind_prediction_bundles_only",
        "hypothesis_set_id": hypothesis_set_id,
        "practice_item_id": practice_item_id,
        "blind_bundle_ids": pinned,
        "cohort": _cohort_record(cohort) if cohort is not None else None,
        "cohorts": cohorts,
        "decision_policy_version": CAUSAL_DECISION_POLICY_VERSION,
    }
    if cohort is None:
        return {
            **base,
            "outcome": "cohort_mismatch",
            "classified_as": [],
            "open_set": False,
            "supports_open_set": False,
            "ambiguous": False,
            "details": [],
        }

    by_hypothesis: dict[str, list[dict[str, Any]]] = {}
    for bundle in resolved:
        by_hypothesis.setdefault(str(bundle["hypothesis_id"]), []).append(bundle)
    base["bundles_outside_locked_set"] = sorted(
        str(bundle["id"])
        for bundle in resolved
        if str(bundle["hypothesis_id"]) not in concrete
    )

    details: list[dict[str, Any]] = []
    matches: list[str] = []
    evaluable: list[str] = []
    for hypothesis_id in concrete:
        candidates = by_hypothesis.get(hypothesis_id) or []
        if not candidates:
            details.append(
                {
                    "hypothesis_id": hypothesis_id,
                    "matched": False,
                    "reason": "missing_pinned_bundle",
                }
            )
            continue
        expected_version = pinned_versions.get(hypothesis_id)
        usable = [
            bundle
            for bundle in candidates
            if expected_version is None
            or int(bundle["hypothesis_version"]) == expected_version
        ]
        if not usable:
            details.append(
                {
                    "hypothesis_id": hypothesis_id,
                    "bundle_ids": [str(value["id"]) for value in candidates],
                    "matched": False,
                    "reason": "hypothesis_version_mismatch",
                    "locked_hypothesis_version": expected_version,
                }
            )
            continue
        rows: list[BundleFeatureRow] = []
        skipped: list[str] = []
        for bundle in usable:
            report = bundle_feature_row_report(bundle["predictions"])
            rows.extend(report.rows)
            skipped.extend(entry["reason"] for entry in report.skipped)
        if not rows:
            details.append(
                {
                    "hypothesis_id": hypothesis_id,
                    "bundle_ids": [str(value["id"]) for value in usable],
                    "matched": False,
                    "reason": "no_declared_feature_rows",
                    "skipped_feature_rows": sorted(set(skipped)),
                }
            )
            continue
        evaluable.append(hypothesis_id)
        matched = any(row.matches(observed_features) for row in rows)
        if matched:
            matches.append(hypothesis_id)
        details.append(
            {
                "hypothesis_id": hypothesis_id,
                "bundle_ids": [str(value["id"]) for value in usable],
                "locked_hypothesis_version": expected_version,
                "matched": matched,
                "reason": (
                    "deterministic_feature_match"
                    if matched
                    else "declared_features_not_observed"
                ),
                "skipped_feature_rows": sorted(set(skipped)),
            }
        )

    if not evaluable:
        outcome = "unparsed_features"
    elif not matches:
        outcome = "no_bundle_matched"
    elif len(matches) == len(evaluable) and len(evaluable) > 1:
        # Every bundle matched: the instrument did not discriminate.  This is
        # NOT open-set evidence — H_OTHER is unsupported here.
        outcome = "all_bundles_matched"
    elif len(matches) == 1:
        outcome = "matched_single"
    else:
        outcome = "matched_multiple"

    assert outcome in CLASSIFICATION_OUTCOMES
    supports_open_set = outcome == "no_bundle_matched"
    if supports_open_set:
        classified_as = [H_OTHER]
    else:
        classified_as = list(matches)
    return {
        **base,
        "outcome": outcome,
        "classified_as": classified_as,
        "open_set": supports_open_set,
        "supports_open_set": supports_open_set,
        "ambiguous": outcome in {"matched_multiple", "all_bundles_matched"},
        "evaluable_hypothesis_ids": evaluable,
        "details": details,
    }


def _item_diff(
    source: Mapping[str, Any], candidate: Mapping[str, Any]
) -> dict[str, Any]:
    axes: dict[str, dict[str, Any]] = {}

    def compare(axis: str, before: Any, after: Any) -> None:
        if _jsonable(before) != _jsonable(after):
            axes[axis] = {
                "before": _jsonable(before),
                "after": _jsonable(after),
            }

    compare("surface_wording", source.get("prompt"), candidate.get("prompt"))
    compare(
        "answer_contract",
        source.get("expected_answer"),
        candidate.get("expected_answer"),
    )
    compare(
        "practice_mode",
        source.get("practice_mode"),
        candidate.get("practice_mode"),
    )
    compare("difficulty", source.get("difficulty"), candidate.get("difficulty"))
    compare(
        "surface_family",
        source.get("surface_family"),
        candidate.get("surface_family"),
    )
    compare(
        "rubric",
        source.get("grading_rubric"),
        candidate.get("grading_rubric"),
    )
    compare(
        "trace_contract",
        source.get("trace_contract"),
        candidate.get("trace_contract"),
    )
    compare(
        "measurement_targets",
        {
            "evidence_facets": source.get("evidence_facets"),
            "evidence_weights": source.get("evidence_weights"),
            "criterion_facet_weights": source.get("criterion_facet_weights"),
        },
        {
            "evidence_facets": candidate.get("evidence_facets"),
            "evidence_weights": candidate.get("evidence_weights"),
            "criterion_facet_weights": candidate.get(
                "criterion_facet_weights"
            ),
        },
    )
    source_features = source.get("task_features")
    candidate_features = candidate.get("task_features")
    source_features = (
        source_features if isinstance(source_features, Mapping) else {}
    )
    candidate_features = (
        candidate_features if isinstance(candidate_features, Mapping) else {}
    )
    for axis in sorted(set(source_features) | set(candidate_features)):
        compare(
            str(axis),
            source_features.get(axis),
            candidate_features.get(axis),
        )
    return {"changed_axes": axes}


def audit_manipulation_contract(
    repository: Repository,
    *,
    source_item: PracticeItem | Mapping[str, Any],
    candidate_item: PracticeItem | Mapping[str, Any],
    source_kind: str,
    adversarial_review: Mapping[str, Any] | None,
    generation_agent_run_id: str | None = None,
    reviewer_agent_run_id: str | None = None,
    require_adversarial: bool = True,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Run the shared probe/rung structural diff plus independent review."""

    source = _jsonable(source_item)
    candidate = _jsonable(candidate_item)
    if not isinstance(source, Mapping) or not isinstance(candidate, Mapping):
        raise ValueError("source and candidate must be item payloads")
    contract = candidate.get("variant_contract")
    if not isinstance(contract, Mapping):
        contract = candidate.get("manipulation_contract")
    if not isinstance(contract, Mapping):
        contract = {}
    structural = _item_diff(source, candidate)
    changed = set(structural["changed_axes"])
    intended = {
        str(value.get("axis"))
        for value in contract.get("intended_manipulations") or []
        if isinstance(value, Mapping) and value.get("axis")
    }
    incidental = {
        str(value) for value in contract.get("incidental_changes") or []
    }
    held = {str(value) for value in contract.get("held_constant") or []}
    structural["undeclared_differences"] = sorted(
        changed - intended - incidental
    )
    structural["held_constant_violations"] = sorted(changed & held)
    structural["declared_but_unchanged"] = sorted(
        intended - changed - held
    )
    structural_passed = not (
        structural["undeclared_differences"]
        or structural["held_constant_violations"]
    )

    review = dict(adversarial_review or {})
    independent = bool(reviewer_agent_run_id) and not (
        generation_agent_run_id
        and generation_agent_run_id == reviewer_agent_run_id
    )
    review_passed = bool(
        review
        and independent
        and review.get("contract_consistent") is True
        and review.get("measurement_target_independence") is True
        and not review.get("undeclared_differences")
    )
    if not structural_passed or (review and not review_passed):
        status = "rejected"
    elif require_adversarial and not review:
        status = "pending_adversarial_review"
    elif require_adversarial and not review_passed:
        status = "rejected"
    else:
        status = "passed"
    body = {
        "source_kind": source_kind,
        "source_item_id": str(source.get("id") or ""),
        "candidate_item_id": str(candidate.get("id") or ""),
        "contract": dict(contract),
        "structural_diff": structural,
        "adversarial_review": review or None,
        "status": status,
        "generation_agent_run_id": generation_agent_run_id,
        "reviewer_agent_run_id": reviewer_agent_run_id,
    }
    return repository.insert_probe_manipulation_audit(
        audit_id=_content_id("pma", body),
        source_kind=source_kind,
        source_item_id=body["source_item_id"],
        candidate_item_id=body["candidate_item_id"],
        contract=dict(contract),
        structural_diff=structural,
        adversarial_review=review or None,
        status=status,
        generation_agent_run_id=generation_agent_run_id,
        reviewer_agent_run_id=reviewer_agent_run_id,
        clock=clock,
    )


def validate_independent_measurement_contract(
    measurement_contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Reject parent-weight inheritance and require recompilation or abstention."""

    contract = dict(measurement_contract)
    if contract.get("independently_compiled") is not True:
        raise ValueError("probe measurement targets were not independently compiled")
    if contract.get("inherited_parent_facet_weights"):
        raise ValueError("probe measurement may not inherit parent facet weights")
    criteria = contract.get("criteria")
    status = str(contract.get("measurement_status") or "")
    if not criteria and status not in {
        "item_local",
        "no_canonical_facet",
        "abstained",
    }:
        raise ValueError(
            "probe measurement requires criterion links or a typed abstention"
        )
    return contract


def create_probe_candidate(
    repository: Repository,
    *,
    factor_id: str,
    practice_item_id: str,
    hypothesis_set_id: str,
    manipulation_audit_id: str,
    measurement_contract: Mapping[str, Any],
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Mint a candidate only after blind discrimination and the diff audit."""

    audit = repository.probe_manipulation_audit(manipulation_audit_id)
    if audit is None or audit.get("status") != "passed":
        raise ValueError("probe candidate requires a passed manipulation audit")
    locked = repository.fetch_hypothesis_set(hypothesis_set_id)
    if locked is None:
        raise ValueError("locked hypothesis set does not exist")
    labels = [
        str(value.get("label"))
        for value in locked.get("hypotheses") or []
        if isinstance(value, Mapping)
    ]
    if H_OTHER not in labels:
        raise ValueError("locked hypothesis set must include H_OTHER")
    concrete = [value for value in labels if value != H_OTHER]
    discrimination = blind_bundle_discrimination(
        repository,
        hypothesis_ids=concrete,
        practice_item_id=practice_item_id,
    )
    if not discrimination["distinguishable"]:
        raise ValueError(
            "blind prediction bundles do not discriminate the cause set: "
            f"{discrimination['reason']}"
        )
    contract = validate_independent_measurement_contract(measurement_contract)
    identity = {
        "factor_id": factor_id,
        "practice_item_id": practice_item_id,
        "hypothesis_set_id": hypothesis_set_id,
        "manipulation_audit_id": manipulation_audit_id,
        "measurement_contract": contract,
        "bundle_ids": discrimination["bundle_ids"],
        "blind_input_contract_version": BLIND_INPUT_CONTRACT_VERSION,
    }
    return repository.insert_causal_probe_candidate(
        candidate_id=_content_id("cpc", identity),
        factor_id=factor_id,
        practice_item_id=practice_item_id,
        hypothesis_set_id=hypothesis_set_id,
        manipulation_audit_id=manipulation_audit_id,
        measurement_contract=contract,
        blind_bundle_ids=discrimination["bundle_ids"],
        discrimination=discrimination,
        blind_input_contract_version=BLIND_INPUT_CONTRACT_VERSION,
        clock=clock,
    )


def candidate_has_current_blind_input_contract(
    candidate: Mapping[str, Any],
) -> bool:
    """Whether a candidate was minted from the observation-free v2 input."""

    return (
        str(candidate.get("blind_input_contract_version") or "")
        == BLIND_INPUT_CONTRACT_VERSION
    )


#: Serving preference over the review ladder: an active candidate always
#: outranks any unreviewed one, whatever its informativeness.
CANDIDATE_STATUS_RANK = {
    "active": 0,
    "reviewed": 1,
    "registered": 2,
    "candidate": 3,
    "rejected": 4,
}


def _candidate_separable_pairs(candidate: Mapping[str, Any]) -> int:
    discrimination = candidate.get("discrimination")
    if not isinstance(discrimination, Mapping):
        return 0
    pairs = discrimination.get("separable_pairs") or []
    return len(pairs) if isinstance(pairs, (list, tuple)) else 0


def order_probe_candidates(
    candidates: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    """THE deterministic candidate order, shared by every consumer.

    Both `causal_orchestrator`'s decision path and `accept_probe_offer` used to
    take an unranked head (`active[0]` / `candidates[0]`) from DB row order; a
    future ranking would then have let the ranked winner and the served item
    diverge. Key: review-ladder status, then recorded discrimination strength
    (separable-pair count — computed, never model-reported), then created_at,
    then id. When the EVSI selector earns live authority it REPLACES the
    informativeness term (the head of this order), not the status term: an
    unreviewed instrument never outranks a reviewed one.
    """

    return sorted(
        candidates,
        key=lambda value: (
            CANDIDATE_STATUS_RANK.get(str(value.get("status") or ""), len(CANDIDATE_STATUS_RANK)),
            -_candidate_separable_pairs(value),
            str(value.get("created_at") or ""),
            str(value.get("id") or ""),
        ),
    )


def transition_probe_candidate(
    repository: Repository,
    candidate_id: str,
    *,
    to_status: str,
    reviewer: str | None = None,
    reason: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Enforce candidate → registered → reviewed → active."""

    candidate = repository.causal_probe_candidate(candidate_id)
    if candidate is None:
        raise ValueError("causal probe candidate does not exist")
    current = str(candidate["status"])
    if to_status not in PROBE_REVIEW_TRANSITIONS.get(current, set()):
        raise ValueError(
            f"cannot transition causal probe from {current} to {to_status}"
        )
    if to_status in {"reviewed", "rejected"} and not reviewer:
        raise ValueError("review transition requires a reviewer")
    if (
        to_status in {"registered", "reviewed", "active"}
        and not candidate_has_current_blind_input_contract(candidate)
    ):
        raise ValueError(
            "probe was generated under an obsolete observation-exposed blind "
            "input contract"
        )
    discrimination = candidate.get("discrimination")
    if to_status in {"registered", "reviewed", "active"} and not (
        isinstance(discrimination, Mapping)
        and discrimination.get("distinguishable")
    ):
        raise ValueError("probe has not passed blind discrimination")
    updated = repository.update_causal_probe_candidate(
        candidate_id,
        status=to_status,
        reviewer=reviewer,
        review_reason=reason,
        clock=clock,
    )
    assert updated is not None
    if to_status == "active":
        # Generated probes that already carry an existing family/card binding
        # become ordinary reviewed, pre-authored diagnostic cards.  The P2
        # review ladder therefore composes the established serving path rather
        # than introducing a second hot-path instrument representation.
        links = repository.probe_item_family_links(
            str(updated["practice_item_id"])
        )
        for link in links:
            metadata = dict(link.instance_metadata or {})
            metadata.update(
                {
                    "review_status": "reviewed_active",
                    "causal_probe_candidate_id": candidate_id,
                }
            )
            repository.update_probe_item_family_metadata(
                practice_item_id=str(updated["practice_item_id"]),
                instrument_card_id=link.instrument_card_id,
                instrument_card_version=link.instrument_card_version,
                instance_metadata=metadata,
            )
        if links:
            repository.set_practice_item_active(
                str(updated["practice_item_id"]),
                active=True,
                clock=clock,
            )
    return updated


def classify_causal_activity(
    repository: Repository,
    *,
    attempt_id: str,
    contamination_class: str,
    near_clone: bool = False,
    near_clone_basis: str | None = None,
    source: str = "causal_probe_coherence",
    detail: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Persist the contamination classification for one attempt.

    The eligibility decision itself lives in ``services.causal_activity_policy``
    — the single authority shared with attempt scheduling, canonical projection,
    and the facet evidence timeline.  This function only writes.

    ``near_clone_basis`` is a
    :data:`~causal_activity_policy.NEAR_CLONE_BASES` member. It rides with the
    verdict because near-clone status decides certification eligibility (§7), and
    an eligibility loss whose grounds are not recorded is not auditable.
    """

    from learnloop.services.causal_activity_policy import (
        NEAR_CLONE_BASES,
        policy_for_class,
    )

    if near_clone_basis is not None and near_clone_basis not in NEAR_CLONE_BASES:
        raise ValueError(f"unknown near_clone basis {near_clone_basis!r}")
    policy = policy_for_class(contamination_class, near_clone=near_clone)
    payload = dict(detail or {})
    payload.setdefault("activity_policy_version", policy.policy_version)
    payload.setdefault("counts_as_assisted", policy.counts_as_assisted)
    return repository.record_causal_activity_classification(
        attempt_id=attempt_id,
        contamination_class=policy.contamination_class,
        near_clone=policy.near_clone,
        near_clone_basis=near_clone_basis,
        source=source,
        closes_pre_intervention_segment=policy.closes_pre_intervention_segment,
        eligible_for_fsrs=policy.eligible_for_fsrs,
        eligible_for_certification=policy.eligible_for_certification,
        detail=payload,
        clock=clock,
    )


# Migration 145: the repair lane's typed disposition ledger (spec §4.3).
CAUSAL_COLD_OUTCOME_STORE_VERSION = "causal_cold_outcomes_v1"


class ColdVerificationPrecondition(ValueError):
    """A §6.2 precondition failed, with the §4.3 disposition it maps to.

    Subclasses ``ValueError`` so pre-145 callers that caught the untyped guard
    keep working; new callers read ``reason`` instead of parsing the message.
    """

    def __init__(self, reason: str, message: str, *, detail: Mapping[str, Any] | None = None):
        super().__init__(message)
        self.reason = reason
        self.detail = dict(detail or {})


def record_causal_cold_outcome(
    repository: Repository,
    *,
    outcome: str,
    followup_task_id: str | None = None,
    remediation_episode_id: str | None = None,
    case_kind: str | None = None,
    case_ref: str | None = None,
    source_attempt_id: str | None = None,
    cold_attempt_id: str | None = None,
    repair_class_id: str | None = None,
    hypothesis_ids: Sequence[str] = (),
    cold_verification_id: str | None = None,
    servable_opportunity: bool,
    detail: Mapping[str, Any] | None = None,
    scheduled_not_before: str | None = None,
    scheduled_expires_at: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Write one typed terminal disposition (spec §4.3). Idempotent.

    ``duration_state`` is derived here rather than accepted: with a cold
    attempt it is ``captured``/``missing`` from ``latency_seconds``; with no
    attempt there is nothing to time and it stays NULL.
    """

    duration_state: str | None = None
    if cold_attempt_id:
        attempt = repository.fetch_practice_attempt(cold_attempt_id)
        if attempt is not None:
            duration_state = (
                "captured" if attempt.get("latency_seconds") is not None else "missing"
            )
    identity = {
        "followup_task_id": followup_task_id,
        "remediation_episode_id": remediation_episode_id,
        "source_attempt_id": source_attempt_id,
        "cold_attempt_id": cold_attempt_id,
        "outcome": outcome,
    }
    return repository.insert_causal_cold_outcome(
        outcome_id=_content_id("cco", identity),
        outcome=outcome,
        followup_task_id=followup_task_id,
        remediation_episode_id=remediation_episode_id,
        case_kind=case_kind,
        case_ref=case_ref,
        source_attempt_id=source_attempt_id,
        cold_attempt_id=cold_attempt_id,
        repair_class_id=repair_class_id,
        hypothesis_ids=sorted({str(value) for value in hypothesis_ids}),
        cold_verification_id=cold_verification_id,
        servable_opportunity=servable_opportunity,
        duration_state=duration_state,
        detail=dict(detail or {}),
        store_version=CAUSAL_COLD_OUTCOME_STORE_VERSION,
        scheduled_not_before=scheduled_not_before,
        scheduled_expires_at=scheduled_expires_at,
        clock=clock,
    )


def record_delayed_cold_verification(
    vault: LoadedVault,
    repository: Repository,
    *,
    source_attempt_id: str,
    cold_attempt_id: str,
    repair_class_id: str,
    hypothesis_ids: Sequence[str],
    avoided_affordances: Sequence[str],
    diagnosis_support_update: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record three separate cold-outcome channels.

    Passing the fresh task updates repair-effect support.  Diagnosis support is
    empty unless the caller supplies independent discriminating evidence; it is
    never inferred from repair success.
    """

    source_attempt = repository.fetch_practice_attempt(source_attempt_id)
    cold_attempt = repository.fetch_practice_attempt(cold_attempt_id)
    if source_attempt is None or cold_attempt is None:
        raise ColdVerificationPrecondition(
            "missing_chain", "source and cold attempts must exist"
        )
    source_at = parse_utc(source_attempt.get("created_at"))
    cold_at = parse_utc(cold_attempt.get("created_at"))
    if source_at is None or cold_at is None or cold_at <= source_at:
        # A "delayed" verification that is not later than its source is either a
        # mis-wired caller or a replay ordering bug; it can never be evidence of
        # durable transfer.
        raise ColdVerificationPrecondition(
            "chronology_invalid",
            "cold verification must be chronologically later than its source attempt",
        )
    source_item = vault.practice_items.get(
        str(source_attempt["practice_item_id"])
    )
    cold_item = vault.practice_items.get(str(cold_attempt["practice_item_id"]))
    if source_item is None or cold_item is None:
        raise ColdVerificationPrecondition(
            "missing_chain", "source and cold items must exist in the vault"
        )
    source_surface = surface_group_id(source_item)
    cold_surface = surface_group_id(cold_item)
    if source_surface == cold_surface:
        raise ColdVerificationPrecondition(
            "same_surface",
            "cold verification requires a different surface family",
            detail={"surface_group": source_surface},
        )
    if cold_attempt.get("primed") or int(cold_attempt.get("hints_used") or 0):
        raise ColdVerificationPrecondition(
            "contaminated_or_assisted",
            "cold verification must be fresh and unassisted",
            detail={
                "primed": bool(cold_attempt.get("primed")),
                "hints_used": int(cold_attempt.get("hints_used") or 0),
            },
        )
    avoided = sorted({str(value) for value in avoided_affordances if str(value)})
    if not avoided:
        raise ColdVerificationPrecondition(
            "missing_chain",
            "cold verification must declare the avoided source affordance",
        )
    parameters = resolve_causal_probe_parameters(repository)
    threshold = parameters["cold_verification_success_correctness"]
    correctness = float(cold_attempt.get("correctness") or 0.0)
    success = correctness >= threshold
    capability_update = {
        "attempt_id": cold_attempt_id,
        "correctness": correctness,
        "channel": "fresh_cross_surface",
        "updated_separately": True,
    }
    diagnosis_update = dict(diagnosis_support_update or {})
    diagnosis_delta = float(diagnosis_update.get("delta") or 0.0)
    if diagnosis_delta != 0.0 and (
        # ONE allowlist, shared with the discriminating-observation receipt that
        # produces `blind_probe_match` ids (`causal_attribution
        # .SUPPORT_BASIS_AUTHORITY`).  A second copy here would let the two
        # drift, and a basis this path accepted but no channel could produce is
        # how an authority gets granted without a producer.
        diagnosis_update.get("basis") not in SUPPORT_BASIS_AUTHORITY
        or not diagnosis_update.get("observation_id")
    ):
        raise ValueError(
            "diagnosis support requires independent discriminating evidence; "
            "repair outcome alone is insufficient"
        )
    if not diagnosis_update:
        diagnosis_update = {
            "delta": 0.0,
            "reason": (
                "repair success does not retroactively prove the diagnosis"
            ),
        }
    repair_effect = {
        "repair_class_id": repair_class_id,
        "success": success,
        "success_threshold": threshold,
        "parameters": parameters.manifest(),
        "support_event": "cold_transfer_success"
        if success
        else "cold_transfer_failure",
    }
    identity = {
        "source_attempt_id": source_attempt_id,
        "cold_attempt_id": cold_attempt_id,
        "repair_class_id": repair_class_id,
        "hypothesis_ids": sorted({str(value) for value in hypothesis_ids}),
        "source_surface": source_surface,
        "cold_surface": cold_surface,
        "avoided_affordances": avoided,
    }
    receipt = repository.insert_causal_cold_verification(
        verification_id=_content_id("ccv", identity),
        source_attempt_id=source_attempt_id,
        cold_attempt_id=cold_attempt_id,
        repair_class_id=repair_class_id,
        hypothesis_ids=identity["hypothesis_ids"],
        source_surface_family=source_surface,
        cold_surface_family=cold_surface,
        avoided_affordances=avoided,
        success=success,
        capability_update=capability_update,
        diagnosis_support_update=diagnosis_update,
        repair_effect_support=repair_effect,
        clock=clock,
    )
    # §4.3: the near-clone verdict is an explicit fingerprint comparison with a
    # recorded basis, never a hardcoded flag.  A cold verification has ALREADY
    # proved the two items sit in different surface groups (that is the guard
    # above), so re-deriving it through the shared assessor both reuses A4's
    # vocabulary and keeps the two checks from ever drifting apart.
    near_clone_assessment = assess_near_clone(
        vault,
        practice_item_id=str(cold_attempt["practice_item_id"]),
        source_practice_item_id=str(source_attempt["practice_item_id"]),
    )
    classify_causal_activity(
        repository,
        attempt_id=cold_attempt_id,
        contamination_class="verification",
        near_clone=near_clone_assessment.near_clone,
        near_clone_basis=near_clone_assessment.basis,
        source="cold_verification",
        detail={
            "cold_verification_id": receipt["id"],
            "near_clone_assessment": near_clone_assessment.as_dict(),
        },
        clock=clock,
    )
    # Bounded deferral exits (a)/(b-i): the one seam where the verification row
    # and the repository are both in hand, whatever path recorded it. A success
    # resolves matching open diagnostic factors as repair_confirmed (and
    # withdraws the candidate belief); a failure escalates them toward
    # promotion. Diagnosis support is untouched either way — the guard above
    # that repair outcome alone cannot move it stands.
    from learnloop.services.causal_factor_deferral import (
        apply_cold_verification_to_factors,
    )

    apply_cold_verification_to_factors(repository, receipt=receipt, clock=clock)
    return receipt
