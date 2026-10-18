"""P0.5 calibration-status parameter registry (spec_p0_measurement_correctness §6).

Definition-as-code: every production numeric value that meets the §6 decision
test is declared once, in this git-reviewable module, keyed by its stable
parameter path. The registry is machine-readable (`REGISTRY: dict[path, spec]`)
and drives:

  * the audit (§2 of the P0.5 design) -- a pydantic-tree walk of every
    ``LearnLoopConfig`` numeric leaf plus an AST walk of the named module-level
    numeric constants; every item must classify as ``decision`` or
    ``structural`` or the audit fails;
  * the per-vault effective-state projection (migration 069 ``parameter_registry``)
    rebuilt idempotently by :func:`refresh`;
  * frozen per-algorithm-version manifests (:func:`freeze_manifest`) so legacy
    replay reads a byte-stable value/hash set;
  * bind-event logging for dormant constraint parameters (:func:`record_bind`).

Classification method: config leaves are covered by explicit ordered rules
(exact path / prefix) so every *current* leaf resolves to decision or structural
with a rationale, and a *future* unmatched numeric field fails the audit loudly
(no open-ended allowlist -- §6). Module-level constants are declared explicitly.

Interpretation notes (U-022 v2; documented in the spec change log):
  * The single "sensitivity certificate" concept is split into two artifacts.
    COVERAGE (``sensitivity_certificate_id``) is descriptive and required for EVERY
    ``active`` decision parameter regardless of status -- it documents where in the
    swept range decisions flip; finding flip points does NOT invalidate it. An active
    parameter lacking valid coverage is ``active_pending_certificate``: enumerated
    debt (a warning in the ordinary audit, a failure in the release gate), never
    silently red. PROMOTION EVIDENCE (``promotion_evidence_id``) is normative and
    gates status beyond ``heuristic``: a ``decision_stable`` sim artifact promotes to
    ``simulation_validated`` (the refusal on a knife-edge value lives here), and the
    activated real-outcome manifest gates ``live_calibrated``. A missing promotion
    artifact for a claimed status is a failure (``promotion_without_evidence``).
  * ``dormant`` parameters need only bind-event logging, never a coverage
    certificate -- dormancy is the explicit alternative to sweeping.
  * ``dormant`` constraint parameters must declare a symbolic ``bind_site`` (the
    guardrail expression P0.5 threads :func:`record_bind` through). The audit
    fails a dormant constraint that declares no bind site -- "an unmonitored
    guardrail is dead code" (§6).
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal

from pydantic import BaseModel

from learnloop.clock import Clock
from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import Repository
from learnloop.substrate.activities import canonical_hash
from learnloop.vault.models import LoadedVault

Kind = Literal["decision", "structural"]
ParamClass = Literal[
    "shaping_weight", "constraint", "likelihood", "evidence_mass",
    "threshold", "prior", "version", "display", "numerical",
    "operational", "fixture",
]
Status = Literal["heuristic", "simulation_validated", "live_calibrated"]
Lifecycle = Literal["active", "dormant", "deleted"]
SourceOfValue = Literal["config", "module_constant", "model_artifact"]

# The sim suites that can promote a heuristic decision parameter (§4.2/§6.3).
PLANTED_LEARNER_GATE = "sim/diagnostic_validation.py::planted_learner_suite"
PLANTED_MISGRADE_GATE = "sim/grader_confusion.py::planted_misgrade_suite"


@dataclass(frozen=True)
class ParameterSpec:
    path: str
    kind: Kind
    param_class: ParamClass
    owner: str
    rationale: str
    scope: str = "global"
    default_status: Status = "heuristic"
    default_lifecycle: Lifecycle = "active"
    source_of_value: SourceOfValue = "config"
    promotion_gate: str | None = None
    # Symbolic guardrail site required for dormant constraint params (§4/§6).
    bind_site: str | None = None
    # Resolver reads the effective value from a resolution context; defaults to a
    # dotted-config-path lookup for config leaves and a module attribute lookup
    # for module constants.
    resolver: Callable[["ResolutionContext"], Any] | None = None


REGISTRY: dict[str, ParameterSpec] = {}


def register(spec: ParameterSpec) -> ParameterSpec:
    REGISTRY[spec.path] = spec
    return spec


# ---------------------------------------------------------------------------
# Inventory B -- named module-level numeric constants (explicit, non-open-ended).
# ---------------------------------------------------------------------------

MODULE_INVENTORY: dict[str, str] = {
    "substrate_cutover": "src/learnloop/substrate/compat/substrate_cutover.py",
    "probe_families": "src/learnloop/diagnosis/probe_families.py",
    "probe_episodes": "src/learnloop/diagnosis/probe_episodes.py",
    "grader_calibration": "src/learnloop/attempts/grader_calibration.py",
    "calibration_streams": "src/learnloop/attempts/calibration_streams.py",
    "robust_composition": "src/learnloop/diagnosis/robust_composition.py",
    "grade_classifier": "src/learnloop/attempts/grade_classifier.py",
    "grade_resolution": "src/learnloop/attempts/grade_resolution.py",
    "grading": "src/learnloop/attempts/grading.py",
    # P1 step 3 -- within-family progression policy defaults (§5.4).
    "progression_policy": "src/learnloop/scheduling/progression_policy.py",
    # P1 step 5 -- purpose-specific administration adapters (§3.10). The hot-path
    # gate is a bool (excluded from the numeric scan) but is registered structural.
    "administration_adapters": "src/learnloop/substrate/administration_adapters.py",
    # P1 step 6 -- one familiarity namespace + familiarity_projection_v1 (§4.1/§4.2).
    "familiarity": "src/learnloop/learner/familiarity.py",
    # P1 step 7 -- fixed/rotating surface mint/gate + durable pre-mint jobs (§5.2/§5.3).
    "surface_mint": "src/learnloop/substrate/surface_mint.py",
    # P1 step 8 -- within-family angle progression + evidence caps + lapse (§4.3/§5.4/§5.5).
    "progression": "src/learnloop/scheduling/progression.py",
    # P1 step 8 -- one-edge depth-transition service; the U-018 structural gate (§5.7).
    "depth_transition": "src/learnloop/curriculum/depth_transition.py",
    # P2 DIAGNOSTIC track -- pre-authored diagnostic pack baseline cap (§5.2, design §E).
    "diagnostic_pack": "src/learnloop/diagnosis/diagnostic_pack.py",
    # P2 DIAGNOSTIC track -- two-tier triage confidence buckets (§6.1, U-027, design §E).
    "failure_triage": "src/learnloop/diagnosis/failure_triage.py",
    # P2 step B.11 -- minimal bidirectional reader dialogue (U-033, §7.6).
    "reader_dialogue": "src/learnloop/reader/reader_dialogue.py",
    # P2 LEARNING track -- the nine-rung pattern ladder (7 ordinals) + stage contracts (§7.1/§7.2).
    "pattern_ladder": "src/learnloop/curriculum/pattern_ladder.py",
    # P2 PRACTICE track -- the bounded rotating practice pool (§7.3, U-028).
    "surface_pool": "src/learnloop/substrate/surface_pool.py",
    # P2 ASSESSMENT + RESTORATION + MILESTONE track -- cold assessment + boundary
    # diff knobs (§8.2/§8.4, design B.8-B.10/§E).
    "golden_path_assessment": "src/learnloop/curriculum/golden_path_assessment.py",
    # P3 slice 1 -- reader integration (spec_p3 §3.4/§4.4/§8.2, design §E).
    "block_health": "src/learnloop/content/sources/block_health.py",
    "annotations": "src/learnloop/reader/annotations.py",
    "salience_firewall": "src/learnloop/attempts/salience_firewall.py",
    # P3 slice 2 -- demand-paged synthesis request priority/window/token knobs (§6.3).
    "reader_requests": "src/learnloop/reader/reader_requests.py",
    # P4 steps 1-2 -- staged controller: snapshot, constraint engine, staged policy
    # (spec_p4 §3/§4/§5, design §E).
    "controller_snapshot": "src/learnloop/scheduling/controller_snapshot.py",
    "constraint_engine": "src/learnloop/scheduling/constraint_engine.py",
    "staged_policy": "src/learnloop/scheduling/staged_policy.py",
    # P4 step 3 -- robust EVSI + minutes loss table + goal-conditioned targets
    # (spec_p4 §6, U-023, design §E).
    "action_loss": "src/learnloop/scheduling/action_loss.py",
    "evsi": "src/learnloop/scheduling/evsi.py",
    # EVSI calibration Part C -- the measured cost of an unresolved misconception
    # (Eedi population prior + heuristics it is shrunk from; docs/reviews/evsi-calibration.md).
    "unresolved_cost": "src/learnloop/scheduling/unresolved_cost.py",
    # mvp-0.21 -- four count caps lifted onto value of information. Its value
    # rule reads robust_composition's and evsi's heuristic decision parameters;
    # its own constants only shape estimates and receipts.
    "voi_stopping": "src/learnloop/diagnosis/voi_stopping.py",
    "predictive_targets": "src/learnloop/scheduling/predictive_targets.py",
    # P4 step 4 -- dispersion/interleaving constraints + the single randomization
    # layer (spec_p4 §9, U-024, design §E).
    "dispersion": "src/learnloop/scheduling/dispersion.py",
    "interleaving": "src/learnloop/scheduling/interleaving.py",
    "randomization_layer": "src/learnloop/scheduling/randomization_layer.py",
    # P4 §14.2 step 3 -- the dual-controller cutover: commitment-scoped ownership, the
    # live StateSignals adapters, and the coexistence-window gates/rollback switch
    # (spec_p4 §14.2, design §A/§C).
    "controller_ownership": "src/learnloop/scheduling/controller_ownership.py",
    "state_signals": "src/learnloop/scheduling/state_signals.py",
    "controller_cutover": "src/learnloop/scheduling/controller_cutover.py",
    # P4 step 5 (descoped, U-026) -- the heuristic LLM-judged soft-kinship feature +
    # its sim admission gate (spec_p4 §8, design §B step 5). Firewall: computed + logged,
    # consulted by nothing until admitted.
    "kinship_feature": "src/learnloop/scheduling/kinship_feature.py",
    # P4 step 6 (descoped, U-025) -- shadow predictive components (spec_p4 §7, design §B
    # step 6). Zero authority; component-only promotion; time-boxed composed telemetry.
    "shadow_components": "src/learnloop/scheduling/shadow_components.py",
    # P4 §15 step 11 -- the §12 re-entry / short-session block-planner adapters.
    "short_session": "src/learnloop/scheduling/short_session.py",
    "reentry_adapter": "src/learnloop/scheduling/reentry_adapter.py",
    # Meas §3.A2-§3.A5 (implementation plan item 6.4) -- the four instrument
    # classes. Every numeric constant in these four modules is a threshold on a
    # REVERT criterion: the number that decides whether an instrument class is
    # still earning its place. §3 requires those criteria to be measurable rather
    # than judged, which makes the thresholds decision parameters in the strict
    # sense -- they are the judgement, written down.
    "discrimination_profiles": "src/learnloop/diagnosis/discrimination_profiles.py",
    "contrast_pairs": "src/learnloop/diagnosis/contrast_pairs.py",
    "error_hunt": "src/learnloop/diagnosis/error_hunt.py",
    "laddered_stems": "src/learnloop/content/authoring/laddered_stems.py",
    # Meas §3.A1/§3.A8 (implementation plan items 6.1 and 6.3). Same argument as
    # the four above: these constants ARE the judgement about when a channel is
    # still honest, so they are decision parameters rather than magic numbers.
    "conjunctive_items": "src/learnloop/content/authoring/conjunctive_items.py",
    "clarification": "src/learnloop/attempts/clarification.py",
}

# Runtime imports are derived from the same source inventory so a module move
# cannot leave a second, silently stale namespace registry behind.
MODULE_IMPORTS: dict[str, str] = {
    name: ".".join(Path(source_path).with_suffix("").parts[1:])
    for name, source_path in MODULE_INVENTORY.items()
}


def _reg_const(
    path: str,
    param_class: ParamClass,
    *,
    kind: Kind = "decision",
    owner: str,
    rationale: str,
    lifecycle: Lifecycle = "active",
    status: Status = "heuristic",
    bind_site: str | None = None,
    gate: str | None = PLANTED_LEARNER_GATE,
) -> None:
    register(
        ParameterSpec(
            path=path,
            kind=kind,
            param_class=param_class,
            owner=owner,
            rationale=rationale,
            default_status=status,
            default_lifecycle=lifecycle,
            source_of_value="module_constant" if kind == "decision" else "module_constant",
            promotion_gate=gate if kind == "decision" else None,
            bind_site=bind_site,
        )
    )


# probe_families
_reg_const("probe_families:ORDINAL_VOCABULARY", "likelihood", owner="probe_families",
           rationale="instrument-row point conditional constants (P(Z|H,card)).")
_reg_const("probe_families:DEFAULT_CONDITIONAL_PSEUDO_COUNT", "prior", owner="probe_families",
           rationale="Dirichlet pseudo-count prior on instrument conditionals.")
_reg_const("probe_families:SIGNATURE_MATCHER_VERSION", "version", kind="structural",
           owner="probe_families", rationale="matcher version pin; enum, not a decision knob.")
_reg_const("probe_families:GRADER_CHANNEL_RELIABILITY", "likelihood", owner="probe_families",
           lifecycle="dormant", rationale="legacy symmetric point channel; frozen in the "
           "mvp-0.6/0.7 manifests, superseded by the P0.3 robust channel under mvp-0.8.",
           bind_site="probe_families.instrument_conditionals (legacy point path)")
# probe_episodes
_reg_const("probe_episodes:FALLBACK_FAMILY_VERSION", "version", kind="structural",
           owner="probe_episodes", rationale="fallback family version pin; enum.")
# grader_calibration
_reg_const("grader_calibration:PRIOR_CONCENTRATION", "prior", owner="grader_calibration",
           rationale="Dirichlet prior concentration on the calibration channel; the "
           "abstention-budget loop (design §6.3) is its promotion gate.",
           gate=PLANTED_MISGRADE_GATE)
_reg_const("grader_calibration:CONFIDENCE_MASS_SPLIT", "prior", owner="grader_calibration",
           rationale="joint (G, confidence-bucket) seed split for the channel prior.")
_reg_const("grader_calibration:ENSEMBLE_DRAWS", "prior", owner="grader_calibration",
           rationale="robustness-analysis ensemble size; does not discharge U-014.")
_reg_const("grader_calibration:ROBUST_QUANTILE", "threshold", owner="grader_calibration",
           rationale="robust lower-quantile for the calibration ensemble.")
# calibration_streams
_reg_const("calibration_streams:CALIBRATION_BASE_INCLUSION_PROBABILITY", "threshold",
           owner="calibration_streams", rationale="base inclusion probability of the "
           "stratified calibration stream (IPW reweight denominator).")
_reg_const("calibration_streams:OVERSAMPLE_LOW_CONFIDENCE", "threshold",
           owner="calibration_streams", rationale="stratification oversample factor.")
_reg_const("calibration_streams:OVERSAMPLE_HIGH_INFLUENCE", "threshold",
           owner="calibration_streams", rationale="stratification oversample factor.")
_reg_const("calibration_streams:OVERSAMPLE_PARTIAL_BOUNDARY", "threshold",
           owner="calibration_streams", rationale="stratification oversample factor.")
_reg_const("calibration_streams:ERROR_INTAKE_NOMINAL_INCLUSION", "prior",
           owner="calibration_streams", lifecycle="dormant",
           rationale="MNAR error-intake marker; never a calibration denominator (U-020).",
           bind_site="calibration_streams.error_intake (non-denominator marker)")
# robust_composition (P0.3)
_reg_const("robust_composition:ROBUST_DRAW_COUNT", "prior", owner="robust_composition",
           rationale="deterministic robust-ensemble draw count (§4.2).",
           gate=PLANTED_MISGRADE_GATE)
_reg_const("robust_composition:ROBUST_QUANTILE", "threshold", owner="robust_composition",
           rationale="robust lower-quantile (10th pct) of the ensemble (§4.2).",
           gate=PLANTED_MISGRADE_GATE)
_reg_const("robust_composition:INSTRUMENT_PERTURBATION_CONCENTRATION", "prior",
           owner="robust_composition", rationale="Dirichlet concentration perturbing the "
           "hand-authored instrument rows (robustness analysis, not calibration).",
           gate=PLANTED_MISGRADE_GATE)
_reg_const("robust_composition:ENSEMBLE_ACTION_AGREEMENT_THRESHOLD", "threshold",
           owner="robust_composition", rationale="90% ensemble action-agreement gate (§4.2).",
           gate=PLANTED_MISGRADE_GATE)
_reg_const("robust_composition:ABSTENTION_BUDGET_FRACTION", "constraint",
           owner="robust_composition", lifecycle="dormant",
           rationale="abstention budget (U-021): the monitored fraction of episodes the "
           "diagnostician may abstain in; over-budget raises an audit alarm, not UI timidity.",
           bind_site="robust_composition.evaluate_selection (abstention emission)",
           gate=PLANTED_MISGRADE_GATE)
_reg_const("robust_composition:LAMBDA_TIME", "constraint", kind="structural",
           owner="robust_composition",
           rationale="minutes numeraire (U-023); structurally fixed at 1.")
_reg_const("robust_composition:BURDEN_COST", "threshold", owner="robust_composition",
           rationale="minutes-denominated stopping burden in the stop rule (§4.2).",
           lifecycle="dormant",
           bind_site="robust_composition.evaluate_selection (stop rule)")
_reg_const("robust_composition:VALUE_PER_NAT_MINUTES", "threshold", owner="robust_composition",
           rationale="nats->minutes value scale converting robust EIG into an EVSI (§4.2).")
# grade_classifier (P0.2)
_reg_const("grade_classifier:CONFIDENCE_LOW_MAX", "threshold", owner="grade_classifier",
           rationale="grader-confidence bucket boundary consumed by the pinned joint channel.")
_reg_const("grade_classifier:CONFIDENCE_MEDIUM_MAX", "threshold", owner="grade_classifier",
           rationale="grader-confidence bucket boundary consumed by the pinned joint channel.")
_reg_const("grade_classifier:LENGTH_BUCKET_SMALL_MAX", "threshold", owner="grade_classifier",
           rationale="response-length bucket boundary (interpretation covariate).")
_reg_const("grade_classifier:LENGTH_BUCKET_MEDIUM_MAX", "threshold", owner="grade_classifier",
           rationale="response-length bucket boundary (interpretation covariate).")
# grade_resolution (P0.2)
_reg_const("grade_resolution:REVIEW_CONFIDENCE_THRESHOLD", "threshold", owner="grade_resolution",
           rationale="low grader-confidence review trigger (§4.4); heuristic until calibrated.")
_reg_const("grade_resolution:INFLUENCE_CERTAINTY_FLOOR", "threshold", owner="grade_resolution",
           rationale="certainty floor below which a consequential observation is flagged.")
_reg_const("grade_resolution:BOUNDED_TRUST_WEIGHT_DEFAULT", "prior", owner="grade_resolution",
           rationale="bounded trust weight (<1) on learner-clarification anchors (§4.7).")
_reg_const("grade_resolution:ADJUDICATION_GRADER_TIER", "constraint", kind="structural",
           owner="grade_resolution", rationale="fixed provenance tier assigned to final "
           "adjudication records; an authority label, not a tunable decision parameter.")
# progression_policy (P1 step 3, spec_p1_shared_substrate §5.4)
_reg_const("progression_policy:SIBLING_SUCCESS_SHRINKAGE", "shaping_weight",
           owner="progression_policy", rationale="sibling success-propagation shrinkage; "
           "affects only the family-stage prior, never marks a sibling reviewed (§5.4).")
_reg_const("progression_policy:ORTHOGONAL_NEXT_DELAY_DAYS", "threshold",
           owner="progression_policy", rationale="delayed-orthogonal cadence after success; "
           "next growth activity is a delayed orthogonal angle, not a near-clone (§5.4).")
_reg_const("progression_policy:PROGRESSION_POLICY_SCHEMA_VERSION", "version", kind="structural",
           owner="progression_policy", rationale="progression-policy body schema version pin; enum.")

# administration_adapters (P1 step 5, spec_p1_shared_substrate §3.10). Structural
# version gate for the hot-path FSRS cutover; OFF keeps the legacy path byte-identical.
_reg_const("administration_adapters:P1_PURPOSE_ADAPTERS_ENABLED", "version", kind="structural",
           owner="administration_adapters", rationale="U-018-style structural gate for the "
           "purpose-adapter hot-path cutover; OFF = byte-identical legacy FSRS write (step 9 flips it).")

# substrate_cutover (P1 step 9, spec_p1_shared_substrate §7.4). Structural version pins
# for the narrowed dual-write cutover: the purpose-adapter path is the LIVE scheduling
# authority for mvp-0.8 vaults; legacy vaults keep the byte-identical purpose-blind path.
_reg_const("substrate_cutover:P1_SCHEDULER_ALGORITHM_VERSION", "version", kind="structural",
           owner="substrate_cutover", rationale="scheduler-algorithm version stamped on P1 "
           "card-lineage state; distinct from the vault projection version so legacy replay "
           "under the old version stays byte-identical (§7.4).")
_reg_const("substrate_cutover:PURPOSE_ADAPTERS_LIVE_FROM", "version", kind="structural",
           owner="substrate_cutover", rationale="the vault projection version (mvp-0.8) from "
           "which the purpose-adapter scheduling path is the LIVE default; bound to the module "
           "constant substrate_cutover.PURPOSE_ADAPTERS_LIVE_FROM, which purpose_adapters_live "
           "reads; legacy vaults keep the purpose-blind path + characterization pins (owner "
           "decision 2026-07-19).")

# familiarity (P1 step 6, spec_p1_shared_substrate §4.2/§4.3).
# familiarity_projection_v1 is a deterministic monotone heuristic; every coefficient
# / threshold that can change evidence or rotation is a registered decision param.
_reg_const("familiarity:TIGHT_KINSHIP_THRESHOLD", "threshold", owner="familiarity",
           rationale="A.4 single-linkage cluster identity for the evidence cap; warmth >= "
           "threshold co-clusters within a target x capability x angle neighborhood.")
_reg_const("familiarity:WARMTH_ROTATION_THRESHOLD", "threshold", owner="familiarity",
           rationale="§5.3 warmth-triggered rotation need; a rotating surface rotates once warmth "
           "crosses this.")
_reg_const("familiarity:V1_COEFFICIENTS", "shaping_weight", owner="familiarity",
           rationale="§4.2 familiarity_projection_v1 per-feature warmth coefficients (monotone, "
           "non-negative); each is a heuristic decision weight the P4 kernel later supersedes.")

# surface_mint (P1 step 7, spec_p1_shared_substrate §5.2/§5.3). Rotation cadence + spare
# policy are provisional heuristics, not invariants (§10); rotation runs off the hot path.
_reg_const("surface_mint:ROTATION_CADENCE_ADMINISTRATIONS", "threshold", owner="surface_mint",
           rationale="§5.3 provisional rotation cadence (~2-3 administrations); a rotating "
           "surface rotates once warmth OR this exposure cadence is reached.")
_reg_const("surface_mint:SPARE_SURFACE_COUNT", "constraint", owner="surface_mint",
           rationale="§5.3 retain one admitted next surface + at most one spare by default; "
           "never spend minting work on an inactive/retired card.")

# Meas §3.A2-§3.A5 instrument classes (implementation plan item 6.4). These are
# the REVERT-criterion thresholds -- the line at which each instrument class stops
# being worth its place in the pool. They are registered as decision parameters
# rather than treated as constants because §3 is explicit that a rung kept on
# judgement is what the spec forbids: the threshold IS the judgement, and it has
# to be visible, owned and promotable like every other one.
_reg_const("discrimination_profiles:NO_PROFILE_APPLIES_FLOOR", "threshold",
           owner="discrimination_profiles",
           rationale="§3.A5 revert direction 1: below this share of judged failures rejecting "
           "every authored profile, the diagnostician is matching the nearest candidate rather "
           "than reading the trace. A floor on honest disagreement, not a tuned quantity.")
_reg_const("discrimination_profiles:PROFILE_SATURATION_CEILING", "threshold",
           owner="discrimination_profiles",
           rationale="§3.A5 revert direction 2 (standing constraint 2's other tail): above this "
           "share of MATCHED failures on one profile, a candidate set of several is behaving as "
           "one. Denominator is matches, not judged failures -- the literal reading is the same "
           "event as the rejection rate collapsing and could never fire on its own.")
_reg_const("discrimination_profiles:MIN_JUDGED_FOR_VERDICT", "threshold",
           owner="discrimination_profiles",
           rationale="§3.A5: judged failures below which neither tail is claimed. A ratio over "
           "three attempts is not a rate, and reporting one is the confident-wrongness the "
           "scoreboard's availability arms exist to prevent.")
_reg_const("discrimination_profiles:MIN_MATCHES_FOR_SATURATION", "threshold",
           owner="discrimination_profiles",
           rationale="§3.A5: matched failures below which no saturation claim is made. Separate "
           "from MIN_JUDGED_FOR_VERDICT because the concentration statistic has its own, smaller "
           "denominator.")
_reg_const("contrast_pairs:PAIR_BAND_TOLERANCE", "constraint", owner="contrast_pairs",
           rationale="§3.A4 gate 1: how far outside the target difficulty band a pair member may "
           "sit. Deliberately tighter than the rung gate's 0.10 -- that one tolerates a "
           "deliberately-harder transfer item, and §3.A4 says 'not one hard, one easy'.")
_reg_const("contrast_pairs:MAX_WITHIN_PAIR_DIFFICULTY_GAP", "constraint", owner="contrast_pairs",
           rationale="§3.A4 gate 1, within-pair form: the band check alone admits a pair sitting "
           "at opposite edges of a wide band, which is the same failure at a smaller scale.")
_reg_const("contrast_pairs:MIN_COMPLETED_PAIRS", "threshold", owner="contrast_pairs",
           rationale="§3.A4 revert criterion: completed pairs below which an order effect cannot "
           "be distinguished from noise.")
_reg_const("contrast_pairs:ORDER_EFFECT_ALPHA", "threshold", owner="contrast_pairs",
           rationale="§3.A4 revert criterion, significance half: because order is randomized, a "
           "pool driven ENTIRELY by the manipulation produces an order-win rate distributed "
           "around 0.5 -- the metric's null value is its own ceiling. This is how surprising the "
           "deviation must be before the verdict fires, without which the revert criterion is a "
           "coin flip.")
_reg_const("contrast_pairs:ORDER_DOMINANCE_CEILING", "threshold", owner="contrast_pairs",
           rationale="§3.A4 revert direction: above this share of within-pair differences "
           "explained by serving order alone, the pair measures order rather than the "
           "manipulation it was authored for.")
_reg_const("error_hunt:MIN_PAIRED_FACETS", "threshold", owner="error_hunt",
           rationale="§3.A3 revert criterion: facets observed by BOTH an error hunt and a "
           "constructed item, below which the agreement rate says nothing about proofreading.")
_reg_const("error_hunt:AGREEMENT_FLOOR", "threshold", owner="error_hunt",
           rationale="§3.A3 revert direction: agreement at or below chance between error-hunt and "
           "constructed-response outcomes on one facet means the two instruments are measuring "
           "different things -- carefulness, not the facet.")
_reg_const("laddered_stems:MIN_PAIRS_PER_ARM", "threshold", owner="laddered_stems",
           rationale="§3.A2 revert criterion: pairs of each kind (within-column, cross-column) "
           "below which the independence claim cannot be checked. Applied per arm, because a "
           "within-column rate over two pairs cannot license a statement about forty cross-column "
           "ones.")
_reg_const("laddered_stems:MIN_INDEPENDENCE_MARGIN", "threshold", owner="laddered_stems",
           rationale="§3.A2: how much lower cross-column agreement must be than within-column "
           "agreement before the independence claim is treated as holding. Zero would call a "
           "one-point difference a success.")

# Meas §3.A1 conjunctive instruments (implementation plan item 6.1).
_reg_const("conjunctive_items:MIN_CONJUNCTIVE_CELLS", "constraint", owner="conjunctive_items",
           rationale="§3.A1: distinct primary cells at which an item counts as conjunctive. Two "
           "is the smallest number for which 'conjunction' means anything -- a definition, not a "
           "tuned quantity, registered so a later change to it is visible as a decision.")
_reg_const("conjunctive_items:CONJUNCTIVE_STRENGTH_CEILING", "constraint",
           owner="conjunctive_items",
           rationale="§3.A1 shape rule: distinct primary cells at which the selection preference "
           "saturates. Beyond four conjuncts the marginal cell says little about whether an item "
           "is a capstone, and an unbounded term would let shape dominate every other selection "
           "component.")

# Meas §3.A8 clarification channel (implementation plan item 6.3).
_reg_const("clarification:DEFAULT_CLARIFICATION_TTL_HOURS", "constraint", owner="clarification",
           rationale="§3.A8: how long a clarification stays askable. Long enough to survive a day "
           "off, short enough that a grade does not sit provisional forever -- a stale question "
           "about work the learner no longer remembers gets a reconstruction, not a report.")
_reg_const("clarification:CLARIFICATION_RATE_WARN_THRESHOLD", "threshold", owner="clarification",
           rationale="§3.A8 revert criterion, and causal §1 principle 8's standing watch: above "
           "this share of gradeable attempts, the channel is being used for MACHINE-resident "
           "uncertainty misclassified as learner-resident, which must be fixed machine-side. A "
           "tripwire, never a cap -- throttling would hide the signal it exists to surface.")
_reg_const("clarification:CLARIFICATION_RATE_MIN_ATTEMPTS", "threshold", owner="clarification",
           rationale="§3.A8: gradeable attempts below which no rate is claimed. A ratio over a "
           "handful of attempts is not a rate, and reporting one is the confident wrongness the "
           "scoreboard's availability arms exist to prevent.")

# Meas §3.A6 opportunistic trace evidence (implementation plan item 6.2). Lives on
# the grading module because that is where the validator that applies it lives.
_reg_const("grading:MAX_EXERCISED_FACETS_PER_ATTEMPT", "constraint", owner="grading",
           rationale="§3.A6 revert direction, cheap half: an attempt reporting a dozen exercised "
           "facets is describing the syllabus rather than the trace. The standing watch is "
           "`trace_evidence_report`'s concentration statistic; this is the per-attempt bound that "
           "keeps one run from swamping it.")
_reg_const("grading:CLARIFICATION_CONFIDENCE_CEILING", "threshold", owner="grading",
           rationale="§3.A8's licensing bound: grader confidence at or above which no "
           "clarification may be asked, because 'never on a confident grade' is what separates "
           "the channel from an interrogation. Shares the 0.40 hedge threshold every other "
           "surface uses so 'hedged' means one thing in this vault.")
_reg_const("grading:FIREWALL_CLEAN_PASS_FRACTION", "threshold", owner="grading",
           rationale="full-credit criterion fraction required before the salience firewall "
           "protects a facet from simultaneous negative attribution.")
_reg_const("grading:FIREWALL_FRACTION_EPSILON", "constraint", kind="structural",
           owner="grading", rationale="floating-point tolerance for the full-credit firewall "
           "comparison; a numerical identity rather than a decision knob.")

# progression (P1 step 8, spec_p1_shared_substrate §4.3/§5.5).
_reg_const("progression:MAX_EFFECTIVE_MASS_PER_CLUSTER", "constraint", owner="progression",
           rationale="§4.3 family evidence cap: max total effective independent mass per "
           "target x capability x angle neighborhood; variants in one family cannot certify alone. "
           "B8: the geometric diminishing-returns decay (DIMINISHING_MASS_DECAY=0.5) already "
           "bounds a single cluster's mass at sum_k decay^k = 1/(1-0.5) = 2.0, so the 3.0 ceiling "
           "never binds in normal accrual -- it is a SAFETY RAIL against a mis-set decay or an "
           "adversarial accrual, kept (not tuned away) per the inert-knob policy: a constraint "
           "parameter stays registered and monitored even while dormant.")
_reg_const("progression:DIMINISHING_MASS_DECAY", "shaping_weight", owner="progression",
           rationale="§4.3 diminishing-returns decay on additional administrations inside one "
           "tight soft-kinship cluster (zero new independent-group count).")
_reg_const("progression:POST_LAPSE_FOLLOWUP_DAYS", "threshold", owner="progression",
           rationale="§5.5/§10 launch post-lapse follow-up cadence (next day), provisional; the "
           "delayed follow-up prefers a fresh/orthogonal surface.")

# depth_transition (P1 step 8, spec_p1_shared_substrate §5.7/§3.1.1/§10). Structural U-018
# gate: OFF in the live product (a confirmed auto_within_envelope behaves as suggest_next).
_reg_const("depth_transition:LIVE_ACTIVATION_ENABLED", "version", kind="structural",
           owner="depth_transition", rationale="U-018 structural gate for live "
           "auto_within_envelope activation; OFF = suggest_next until the auto-depth package ships.")

# P2 DIAGNOSTIC track (spec_p2_narrow_golden_path §5, §6, U-027/U-028; design §E). The
# baseline visible cap and triage confidence buckets are heuristic decision knobs; the
# spec-schema versions are structural enums.
_reg_const("diagnostic_pack:PACK_SPEC_SCHEMA_VERSION", "version", kind="structural",
           owner="diagnostic_pack", rationale="diagnostic-pack spec schema version pin; enum.")
_reg_const("diagnostic_pack:BASELINE_VISIBLE_CAP", "constraint", owner="diagnostic_pack",
           rationale="§5.2 visible-administration cap band (2-4); a requested cap is clamped "
           "into this band and the episode's robust stopping rules do the rest.")
_reg_const("failure_triage:TRIAGE_ROUTES_SCHEMA_VERSION", "version", kind="structural",
           owner="failure_triage", rationale="failure-triage route-table schema version pin; enum.")
_reg_const("failure_triage:TRIAGE_CONFIDENCE_BUCKET_EDGES", "threshold", owner="failure_triage",
           rationale="U-027 grader-confidence bucket edges (low|mid|high); a tier-one signature "
           "route fires only in the high bucket, else tier two applies.")
_reg_const("failure_triage:TRIAGE_DOMINANCE_SHARE", "threshold", owner="failure_triage",
           rationale="C3 owner-flagged default (PENDING OWNER CONFIRMATION): minimum share of the "
           "supplied provisional reason distribution one signature must own for the "
           "high-confidence error-signature route to stay tier-one; a diffuse distribution "
           "downgrades it to a tier-two decision aid. The spec's three decisive triggers are "
           "unaffected. Cheap to reverse (a bare signature with no supplied distribution still "
           "routes tier-one).")

# P2 step B.11 -- reader routing prior (U-033, §7.6, design A.1). The prior is a
# replay-derived decision AID that only reorders triage candidates inside the
# U-027 channel and is superseded by the first cold observation; reader dialogue
# ships DARK (reader_enabled=False default, §12.3.2), so both knobs are dormant
# (bind-log, no coverage certificate) -- they bind only once the owner enables
# the reader and before supersession.
_reg_const("reader_dialogue:ROUTING_PRIOR_HALFLIFE_DAYS", "threshold", owner="reader_dialogue",
           lifecycle="dormant", rationale="A.1 half-life (days) decaying a formative reading "
           "answer's routing-prior weight before it is structurally superseded by the first "
           "cold observation; the single decay knob.",
           bind_site="reader_dialogue.routing_prior_projection_v1 (decay of reading-answer weight)")
_reg_const("reader_dialogue:ROUTING_PRIOR_MAX_WEIGHT", "constraint", owner="reader_dialogue",
           lifecycle="dormant", rationale="A.1 supersession bound: the max magnitude a reading "
           "answer contributes to tier-two triage, held below any single cold observation's "
           "influence so a cold observation always dominates the prior.",
           bind_site="reader_dialogue.routing_prior_projection_v1 (weight clamp)")
_reg_const("reader_dialogue:READER_REVEAL_OVERLAP_THRESHOLD", "threshold", owner="reader_dialogue",
           lifecycle="dormant", rationale="L3 server-side reveal detection: minimum share of a "
           "reserved surface's statement word-bigrams a reader answer must reproduce to count as "
           "quoting (and burn) that reserve; cheap verbatim overlap, no LLM. Dormant with the "
           "dark reader (reader_enabled=False default).",
           bind_site="reader_dialogue._detect_revealed_reserves (verbatim-overlap reveal gate)")
_reg_const("reader_dialogue:READER_BRANCH_PROMPT_ANCESTORS", "operational", kind="structural",
           owner="reader_dialogue", rationale="Reader workbench RW1a (the ported clarification-"
           "branches contract, cf2cbe77): at most this many of a follow-up's ancestors enter the "
           "tutor prompt, newest first; every parent link stays durable and the manifest records "
           "the omitted count. A prompt-size bound (money and latency), never a learning decision.")
_reg_const("reader_dialogue:READER_QUESTION_DENSITY_TARGET", "operational", kind="structural",
           owner="reader_dialogue", rationale="§13 owner-tuning guideline (~1 owner-placed "
           "reading question per major section); NEVER auto-inserted (no ask_now planner / "
           "density policy in this cut, U-017@v3) -- a review-time guideline, not a live knob.")

# P2 LEARNING track -- pattern ladder + stage-transition contracts (§7.1/§7.2,
# §12.3; design B.6/§E). The ladder-policy schema version is a structural enum; the
# repeated-failure cutoff, per-stage delay, and completion-scaffold threshold are
# heuristic decision knobs (the sim sensitivity band shows the review/delay/exit
# decision only flips inside a plausible range, no knife-edge active value).
_reg_const("pattern_ladder:LADDER_POLICY_SCHEMA_VERSION", "version", kind="structural",
           owner="pattern_ladder", rationale="pattern-ladder policy spec schema version pin; enum.")
_reg_const("pattern_ladder:REPEATED_FAILURE_REVIEW_N", "constraint", owner="pattern_ladder",
           rationale="§7.2 N distinct varied-surface failures on a rung that terminate into "
           "needs_review / P4-expansion telemetry rather than infinite near-clone practice.")
_reg_const("pattern_ladder:STAGE_DELAY_DAYS", "threshold", owner="pattern_ladder",
           rationale="§7.2 per-stage delayed-check window (days) before delayed independent "
           "target-like practice is due.")
_reg_const("pattern_ladder:COMPLETION_SCAFFOLD_THRESHOLD", "threshold", owner="pattern_ladder",
           rationale="§7.2 scaffold-use fraction at/above which an example_completion rung is "
           "scaffold-heavy; its exit records scaffold use and never certifies independence.")

# P2 PRACTICE track -- bounded rotating practice pool (§7.3, U-028, design B.7/§E).
# The pool-spec schema version is a structural enum; the spare-cache bound is a
# heuristic decision knob (current + one cached spare at most).
_reg_const("surface_pool:POOL_SPEC_SCHEMA_VERSION", "version", kind="structural",
           owner="surface_pool", rationale="practice-pool spec schema version pin; enum.")
_reg_const("surface_pool:POOL_SPARE_CACHE", "constraint", owner="surface_pool",
           rationale="§7.3 spare surfaces pre-cached beyond the current one (one current + "
           "one cached spare at most); bounds the rotation cache.")

# P2 ASSESSMENT + RESTORATION + MILESTONE track -- cold assessment + boundary diff
# (§8.2/§8.4; design B.8-B.10/§E). The result-artifact schema version is a structural
# enum. The demonstrated-claim certainty floor is a display/decision-AID threshold: it
# only shapes the boundary-diff CELL LABEL (demonstrated vs developing / calibrated vs
# provisional wording) and NEVER a posterior, evidence mass, eligibility, or the
# certification result -- those are the landed P0 pipeline's (certify_from_administration
# + grade_resolution, already registered). Classified structural (fails the §6 decision
# test: changing it cannot change evidence/posterior/certification).
_reg_const("golden_path_assessment:ASSESSMENT_SNAPSHOT_SCHEMA_VERSION", "version",
           kind="structural", owner="golden_path_assessment",
           rationale="cold-assessment result-artifact schema version pin; enum.")
_reg_const("golden_path_assessment:DEMONSTRATED_CLAIM_CERTAINTY", "display",
           kind="structural", owner="golden_path_assessment",
           rationale="§8.4 boundary-diff label floor: the calibrated-certainty at/above "
           "which a covered cell is labeled `demonstrated`/`calibrated` vs "
           "`developing`/`provisional`. A decision-aid/display threshold only -- it never "
           "touches the P0 posterior, evidence mass, eligibility, or certification result.")

# P3 slice 1 -- reader integration decision parameters (spec_p3 §3.4/§4.4/§8.2, §E).
_reg_const("block_health:EQUATION_LOW_CONFIDENCE_THRESHOLD", "threshold", owner="block_health",
           rationale="§3.4 per-block health: equation blocks whose extractor confidence is "
           "below this cutoff are flagged equation_low_confidence -> region-crop fallback. "
           "Conservative/heuristic; unknown health is never treated as healthy (§16).")
_reg_const("block_health:TEXT_DENSITY_ANOMALY_THRESHOLD", "threshold", owner="block_health",
           rationale="§3.4 text-density anomaly cutoff: a block whose char-per-area density "
           "deviates beyond this ratio is flagged text_density_anomaly (garbled/dropped text).")
_reg_const("block_health:OCR_ANOMALY_THRESHOLD", "threshold", owner="block_health",
           rationale="§3.4 OCR character-anomaly cutoff: fraction of replacement/non-printable "
           "characters above which a block is flagged ocr_character_anomaly.")
_reg_const("annotations:SUBBLOCK_CONFIDENCE_MIN", "threshold", owner="annotations",
           rationale="§4.4 sub-block reanchor auto-accept floor: a changed-text candidate below "
           "this confidence is NEVER auto-accepted -> needs_reanchor (ambiguity is visible, "
           "invariant 1.1.5).")
_reg_const("annotations:MANUAL_REVIEW_BATCH", "constraint", owner="annotations",
           rationale="§A.3.5 review-volume budget: the max needs_reanchor segments a single "
           "re-extraction may surface for manual review at once; excess parks the re-extraction "
           "for review rather than silently orphaning annotations.",
           bind_site="annotations.reanchor_annotations (needs_reanchor surfacing budget)")
_reg_const("annotations:FUZZY_COVERAGE_MIN", "threshold", owner="annotations",
           rationale="minimum token-alignment coverage for accepting a fuzzy quote reanchor.")
_reg_const("annotations:FUZZY_WINDOW_SLACK", "constraint", owner="annotations",
           rationale="maximum extra token span allowed around a fuzzy quote alignment.")
_reg_const("annotations:CONTEXT_SCORE_MIN", "threshold", owner="annotations",
           rationale="minimum neighboring-context similarity for accepting a reanchor.")
_reg_const("annotations:CONTEXT_MARGIN_MIN", "threshold", owner="annotations",
           rationale="minimum score margin separating the best context reanchor candidate.")
_reg_const("salience_firewall:DWELL_SEGMENT_MAX", "constraint", owner="salience_firewall",
           rationale="§8.2 bounded visibility-segment cap: max dwell/visibility segments a client "
           "aggregates per window; bounds salience volume and forbids high-frequency timer ticks.",
           bind_site="salience_firewall.reject_salience (bounded segment aggregation)")
# P3 slice 3 -- salience projector v1 depth-suggestion weights (§8.2, design B step 9).
# Structural, not a decision knob: these weight highlight/question/revisit counts into a
# PROPOSAL-priority / depth-SUGGESTION reorder ONLY. The firewall proves there is no path
# from any of them to mastery/posterior/readiness/certification (invariant 1.1.6), so they
# carry no measurement authority and never enter the sim decision-stability suite.
_reg_const("salience_firewall:_DEPTH_SUGGEST_HIGHLIGHT_WEIGHT", "shaping_weight", kind="structural",
           owner="salience_firewall", rationale="salience-only depth-suggestion weight on highlight "
           "count; reorders proposals/suggests depth, never evidence.")
_reg_const("salience_firewall:_DEPTH_SUGGEST_QUESTION_WEIGHT", "shaping_weight", kind="structural",
           owner="salience_firewall", rationale="salience-only depth-suggestion weight on question "
           "count; reorders proposals/suggests depth, never evidence.")
_reg_const("salience_firewall:_DEPTH_SUGGEST_REVISIT_WEIGHT", "shaping_weight", kind="structural",
           owner="salience_firewall", rationale="salience-only depth-suggestion weight on revisit "
           "count; reorders proposals/suggests depth, never evidence.")

# P3 slice 2 -- demand-paged synthesis request parameters (spec_p3 §6.3, §E).
_reg_const("reader_requests:PRIORITY_BAND", "shaping_weight", owner="reader_requests",
           rationale="§6.3 interactive priority band placing reader background requests above bulk "
           "jobs, bounded so rapid scrolling cannot starve an explicitly running batch.")
_reg_const("reader_requests:MAX_ADJACENT_BLOCKS", "constraint", owner="reader_requests",
           rationale="§6.3 smallest-sufficient-window bound: max adjacent blocks per side pulled "
           "into a demand-paged neighborhood; bounds scope so no unrelated chapter is sent.")
_reg_const("reader_requests:TOKEN_CAP", "constraint", owner="reader_requests",
           rationale="§6.3 per-request token cap (visible): exceeding it keeps the local capture and "
           "offers local/manual handling -- it never silently expands scope or sends the whole source.")

# P4 steps 1-2 -- staged controller (spec_p4 §3/§4/§5, design §E; registered at birth).
# Structural version pins (enums, not decision knobs).
_reg_const("controller_snapshot:SNAPSHOT_SCHEMA_VERSION", "version", kind="structural",
           owner="controller_snapshot", rationale="ControllerSnapshot schema version pin; enum.")
_reg_const("constraint_engine:CONSTRAINT_MANIFEST_VERSION", "version", kind="structural",
           owner="constraint_engine", rationale="feasible-set constraint manifest schema version; enum.")
_reg_const("staged_policy:STAGED_POLICY_VERSION", "version", kind="structural",
           owner="staged_policy", rationale="staged decision policy version pin; enum.")
# Decision parameters (heuristic; each ships a sensitivity certificate when active,
# design §E / standing rule 3).
_reg_const("controller_snapshot:CONSERVATIVE_DURATION_MINUTES", "threshold",
           owner="controller_snapshot", rationale="conservative upper-bound minutes for a candidate "
           "of unknown duration, so the fatigue/budget constraint fails closed (§5).")
_reg_const("staged_policy:ATTENTION_BLOCK_MIN_MINUTES", "threshold", owner="staged_policy",
           rationale="lower bound of the 5-15 min coherent attention block (§4.1).")
_reg_const("staged_policy:ATTENTION_BLOCK_MAX_MINUTES", "threshold", owner="staged_policy",
           rationale="upper bound of the 5-15 min coherent attention block (§4.1).")
_reg_const("staged_policy:DEFAULT_BLOCK_BUDGET_MINUTES", "threshold", owner="staged_policy",
           rationale="default attention-block budget when the session gives no tighter bound (§4.1).")
_reg_const("staged_policy:CONTEXT_SWITCH_COST_MINUTES", "threshold", owner="staged_policy",
           rationale="once-per-block context-switch cost charged at block level, not per item (§4.1).")
_reg_const("staged_policy:NEGATIVE_AFFECT_DOWNGRADE_THRESHOLD", "threshold", owner="staged_policy",
           rationale="repeated-negative-affect count that downgrades auto_within_envelope to "
           "suggest_next before an edge commits (U-011, §4.2).")
# Dormant guardrail (constraint): fires only under budget pressure -> bind-logged, not
# swept (U-022). Threaded through constraint_engine.feasible_set when it excludes.
_reg_const("constraint_engine:FATIGUE_BUDGET_SLACK_MINUTES", "constraint",
           owner="constraint_engine", lifecycle="dormant",
           rationale="minutes of slack the fatigue/budget feasibility constraint tolerates before "
           "excluding an over-budget candidate; a guardrail that only fires under budget pressure.",
           bind_site="constraint_engine.feasible_set (fatigue_budget exclusion)")

# P4 step 3 -- robust EVSI + minutes loss table + goal-conditioned targets (spec_p4 §6,
# U-023, design §E). Structural version pins (enums, not decision knobs).
_reg_const("action_loss:LOSS_TABLE_VERSION", "version", kind="structural",
           owner="action_loss", rationale="minutes decision-loss table body schema version; enum.")
_reg_const("evsi:EVSI_SCHEMA_VERSION", "version", kind="structural", owner="evsi",
           rationale="robust-EVSI persistence body schema version; enum.")
_reg_const("predictive_targets:TARGET_SET_SCHEMA_VERSION", "version", kind="structural",
           owner="predictive_targets", rationale="goal-conditioned target-set body schema version; enum.")
# Decision parameters (heuristic).
_reg_const("action_loss:DEFAULT_INTERVENTION_MINUTES", "threshold", owner="action_loss",
           rationale="§6.2 fail-closed per-intervention minutes used only when NO logged attempt "
           "duration is available to derive an estimate from; the conservative fallback that keeps "
           "the loss table inspectable on an un-instrumented vault. The EVSI-per-minute ranking's "
           "loss magnitudes reuse the already-registered robust_composition LAMBDA_TIME/BURDEN_COST; "
           "this is the only new duration constant.")
# EVSI calibration Part C (behind evsi.measured_loss_enabled, default off).
_reg_const("unresolved_cost:EEDI_EXCESS_REPEAT_RATE", "prior", owner="unresolved_cost",
           rationale="population prior (Eedi NeurIPS 2020, 370 misconception triples): excess repeat-error "
           "rate per later encounter after a misconception-consistent error; school maths, multiple choice. "
           "Shrunk toward the learner's own recurrence history (evsi.unresolved_cost_prior_pseudo_count).")
_reg_const("unresolved_cost:ENCOUNTERS_UNTIL_CAUGHT", "prior", owner="unresolved_cost",
           rationale="heuristic: encounters with an unresolved misconception before it is caught another "
           "way; not in Eedi, not yet measured here. Scales the population prior only.")
_reg_const("unresolved_cost:CENSOR_DAYS", "threshold", owner="unresolved_cost",
           rationale="heuristic: a recurrence class first seen this recently with no repeat yet is "
           "right-censored (excluded from the personal mean, counted).")
_reg_const("unresolved_cost:MIN_TIMED_ATTEMPTS", "threshold", owner="unresolved_cost",
           rationale="heuristic: timed attempts the pooled latency median needs before it replaces the "
           "per-repeat minutes default (wall-clock latency is noisy at small n).")
_reg_const("unresolved_cost:LATENCY_CAP_MINUTES", "threshold", owner="unresolved_cost",
           rationale="heuristic: one attempt's wall-clock latency counts at most this many minutes "
           "(a break is not repeated-error time).")
_reg_const("voi_stopping:DURATION_PSEUDO_OBSERVATIONS", "prior", owner="voi_stopping",
           rationale="mvp-0.21: pseudo-observations behind a duration prior when a candidate's "
           "minutes come from its practice mode's median shrunk toward the authored estimate; DL1's "
           "own constant (daily_plan/estimates.PSEUDO_OBSERVATIONS) repeated because serving never "
           "imports the plan. Sizes the minutes cost the value of information must pay.")
_reg_const("voi_stopping:DEFAULT_LATENCY_CAP_MINUTES", "numerical", kind="structural",
           owner="voi_stopping",
           rationale="winsorizing cap on one latency (minutes) when a vault config has no "
           "plan.latency_cap_minutes; the plan's own default, a numerical clamp.")
_reg_const("voi_stopping:_ROUND_DIGITS", "numerical", kind="structural", owner="voi_stopping",
           rationale="decimal places a value-of-information receipt keeps for probabilities and "
           "nats; display of the logged forecast only.")
_reg_const("voi_stopping:MAX_RECORDED_CANDIDATES", "operational", kind="structural",
           owner="voi_stopping",
           rationale="how many candidates' summaries one value-of-information receipt keeps (the "
           "best keeps its full forecast); receipt size only, never a decision.")
_reg_const("voi_stopping:_VARIANCE_FLOOR", "numerical", kind="structural", owner="voi_stopping",
           rationale="mvp-0.21 greedy conditional valuation: the selection reward's own variance "
           "floor (selection_rewards.probe_information_gain_components, 1e-6) repeated so a check's "
           "information decomposed from its reward body reproduces the reward's probe_eig_total; a "
           "numerical clamp, not a decision knob.")
_reg_const("voi_stopping:_DEFAULT_FACET_VARIANCE", "prior", kind="structural", owner="voi_stopping",
           rationale="mvp-0.21 greedy conditional valuation: the facet-recall variance the selection "
           "reward reads for a facet with no state (0.25, Beta(1,1)'s), repeated so the decomposed "
           "information reproduces the reward's; not a new prior.")
_reg_const("voi_stopping:_RECONSTRUCTION_TOLERANCE", "numerical", kind="structural",
           owner="voi_stopping",
           rationale="mvp-0.21 greedy conditional valuation: relative tolerance for 'the decomposed "
           "terms reproduce the logged probe_eig_total'; a body that does not is valued on its total "
           "alone and labelled conditioning: unavailable. A floating-point check, never a decision.")
_reg_const("voi_stopping:_BRANCH_MERGE_DIGITS", "numerical", kind="structural", owner="voi_stopping",
           rationale="mvp-0.21 conditional hypothesis valuation (Codex re-review F2): two expected "
           "posteriors that agree to 12 decimals are one belief branch; floating-point identity, "
           "not a decision knob.")
_reg_const("voi_stopping:_MAX_BELIEF_BRANCHES", "operational", kind="structural", owner="voi_stopping",
           rationale="mvp-0.21 conditional hypothesis valuation (Codex re-review F2): a bound on the "
           "arithmetic of the expected posterior branches kept per hypothesis variable (4096), never "
           "on how many checks are admitted; past it the branches merge at fewer decimals (keeping "
           "their mean) and the receipt says hypothesis_branches: coarsely_merged.")
_reg_const("voi_stopping:_COARSE_MERGE_DIGITS", "numerical", kind="structural", owner="voi_stopping",
           rationale="mvp-0.21 conditional hypothesis valuation: the coarser decimal places tried, in "
           "order, once _MAX_BELIEF_BRANCHES is passed; arithmetic only, labelled in the receipt.")
_reg_const("evsi:PERTURBATION_DELTA", "threshold", owner="evsi",
           rationale="§6.5 bounded per-row probability perturbation (±0.15) for the robustness stress "
           "test; reuses the standing ±0.15 robustness axis. A winner/action flip under it abstains.",
           gate=PLANTED_MISGRADE_GATE)

# P4 step 4 -- dispersion/interleaving + the single randomization layer (spec_p4 §9,
# U-024, design §E). Structural version pins.
_reg_const("dispersion:DISPERSION_POLICY_VERSION", "version", kind="structural",
           owner="dispersion", rationale="same-facet dispersion policy schema version; enum.")
_reg_const("interleaving:INTERLEAVING_POLICY_VERSION", "version", kind="structural",
           owner="interleaving", rationale="stage-aware interleaving policy schema version; enum.")
_reg_const("randomization_layer:RANDOMIZATION_LAYER_VERSION", "version", kind="structural",
           owner="randomization_layer", rationale="single randomization layer schema version; enum.")
# Decision parameters (heuristic + experiment variants, §9.1/§9.3).
_reg_const("dispersion:DISPERSION_MIN_INTERVENING_ADMINISTRATIONS", "constraint",
           owner="dispersion", rationale="§9.1 minimum intervening administrations required between "
           "two fresh-evidence administrations on the same facet/near-kin; a registered heuristic + "
           "experiment variant that generalizes scheduler._rotate_same_day_frontier_repeats, not a "
           "literal in queue code. Feasible-set shaping, never a rank trade.")
_reg_const("randomization_layer:EPSILON_TIE_MARGIN", "threshold", owner="randomization_layer",
           rationale="§9.3 near-equivalence margin (fraction of the top per-minute value) within which "
           "the single randomization layer micro-randomizes / epsilon-tie-breaks reversible feasible "
           "candidates with a logged propensity; above it selection is deterministic and randomization "
           "is inert.")
# Dormant guardrail: the propensity floor only binds when a design would spread the true
# assignment probability too thin (bind-logged, not swept, U-022).
_reg_const("randomization_layer:PROPENSITY_FLOOR", "constraint", owner="randomization_layer",
           lifecycle="dormant",
           rationale="§9.3 minimum true assignment probability a randomization variant may carry, so "
           "off-policy support does not collapse; a guardrail that only fires when a design has too "
           "many variants for the floor.",
           bind_site="randomization_layer._clamped_uniform_propensity (propensity floor clamp)")

# P4 §14.2 step 3 -- dual-controller cutover switches (design §A/§C). Structural version
# pins + the live-cutover gate; the gate is a bool (excluded from the numeric scan) and is
# registered structural, bind-logged when it flips (U-022).
_reg_const("controller_ownership:OWNERSHIP_POLICY_VERSION", "version", kind="structural",
           owner="controller_ownership", rationale="commitment-scoped ownership arbitration "
           "schema version (design §A.2); enum, not a decision knob.")
_reg_const("controller_cutover:STAGED_POLICY_LIVE_FOR_P2", "version", kind="structural",
           owner="controller_cutover", lifecycle="dormant",
           rationale="§14.2 step-3 cutover gate: staged policy is the LIVE authority for "
           "staged-owned P2 commitments. A U-018-style structural switch; OFF returns every "
           "run to the pre-cutover static policy (global rollback). Bind-logged on flip.",
           bind_site="controller_cutover.staged_next_action (live-authority gate)")

# P4 §15 step 11 -- the §12 re-entry / short-session block-planner adapters. Decision
# parameters (heuristic; each an active pool bound, not a reward weight -- they never order
# anything, the within-block robust-EVSI selector does).
_reg_const("staged_policy:SHORT_SESSION_MAX_MINUTES", "threshold", owner="staged_policy",
           rationale="§12.2 available-minutes threshold below which the SAME block planner "
           "plans a completing short-session block (budget = available minutes, composing the "
           "5-15 min bounds); one completed activity completes the session. Reuses the 5-min "
           "attention-block lower bound.")
_reg_const("reentry_adapter:REENTRY_QUESTION_CAP", "threshold", owner="reentry_adapter",
           rationale="§12.1 small visible cap on re-entry re-check questions; it bounds the "
           "candidate pool only -- the within-block robust-EVSI-per-minute selector orders and "
           "the robust stop rule stops, so the cap never orders anything.")
_reg_const("reentry_adapter:REENTRY_RECOVERABLE_BAND", "threshold", owner="reentry_adapter",
           rationale="§12.1 Ready margin below target within which a previously-demonstrated "
           "cell is reported RECOVERABLE (a light refresher) rather than NEEDS_ATTENTION; "
           "reported as neutral context, never a deficit label.")
# The single positive robust-sampling value an open diagnostic episode confers (§4.2 rung
# 3). Its magnitude never orders anything -- the ladder rung is a boolean >0 gate.
_reg_const("state_signals:OPEN_EPISODE_ROBUST_VALUE", "threshold", owner="state_signals",
           rationale="§4.2 rung-3 positive-value flag: the robust sampling value assigned "
           "when an in-progress open diagnostic episode makes a decision-relevant "
           "uncertainty measurable; a boolean gate, never a rank weight.")

# P4 step 5 (descoped, U-026) -- the soft-kinship feature admission threshold. The sim
# admission gate IS its sensitivity certificate (design §E: "kinship-feature admission
# thresholds -- simulation_validated after the sim gate"). The planted-misgrade / sim
# machinery gates its promotion; until admitted, the feature is consulted by nothing.
_reg_const("kinship_feature:ADMISSION_MIN_DISCOUNT_SHIFT", "threshold", owner="kinship_feature",
           rationale="§8.4 minimum independent-evidence-discount SHIFT the repeat-vs-fresh "
           "planted-learner admission sim must demonstrate the feature moves (in the correct "
           "direction) before the soft-kinship feature may be admitted (simulation_validated). "
           "A firewall gate on a shadow feature -- it orders nothing until admission.",
           gate=PLANTED_MISGRADE_GATE)

# P4 step 6 (descoped, U-025) -- shadow predictive components. Two heuristics: the
# predeclared prequential improvement margin an individual component must beat its
# incumbent by, and the composed-selector telemetry time-box. Neither orders a live
# action; a promoted component feeds staged-policy INPUTS only, and the composed selector
# is never promoted at n=1 (structural guard, §7.4).
_reg_const("shadow_components:COMPONENT_PROMOTION_MARGIN", "threshold", owner="shadow_components",
           rationale="§7.4 predeclared prequential (log-loss) margin a predictive component "
           "must beat its incumbent estimate by before promotion is considered; a component "
           "feeds staged-policy inputs only and never reorders actions.")
_reg_const("shadow_components:COMPOSED_SELECTOR_TELEMETRY_HORIZON_DAYS", "threshold",
           owner="shadow_components",
           rationale="§7 composed-selector telemetry time-box (days): unpromoted composed-"
           "selector telemetry retires after this horizon (secondary product, design §B step 6).")


# ---------------------------------------------------------------------------
# Inventory A -- config-leaf classification rules (ordered; first match wins).
# Each rule maps a matcher to a (kind, param_class, lifecycle, status, rationale)
# partial. A leaf matching no rule is UNCLASSIFIED -> audit failure.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _ConfigRule:
    match: Callable[[str], bool]
    kind: Kind
    param_class: ParamClass
    rationale: str
    lifecycle: Lifecycle = "active"
    status: Status = "heuristic"
    bind_site: str | None = None
    gate: str | None = PLANTED_LEARNER_GATE


def _exact(*paths: str) -> Callable[[str], bool]:
    s = set(paths)
    return lambda p: p in s


def _prefix(*prefixes: str) -> Callable[[str], bool]:
    return lambda p: any(p == pre or p.startswith(pre) for pre in prefixes)


def _suffix(*suffixes: str) -> Callable[[str], bool]:
    return lambda p: any(p.endswith(suf) for suf in suffixes)


# Structural inventories (§9.3) come first so they are never captured by a decision rule.
_CONFIG_RULES: list[_ConfigRule] = [
    # --- structural: versions / schema ---
    _ConfigRule(_exact("schema_version"), "structural", "version",
                "schema version int; enum, not a decision knob."),
    # --- structural: operational / infra (no measurement authority, §9.3) ---
    _ConfigRule(_prefix("ai.", "codex.", "ingest.", "animation."), "structural", "operational",
                "AI/codex/ingest/animation infra knob (timeout/port/token ceiling); no "
                "measurement authority."),
    _ConfigRule(_exact("embedding.dimensions"), "structural", "operational",
                "Vector representation width; embeddings have no measurement authority."),
    # Slice 1 M2: queue/wait/budget knobs of the asynchronous diagnoser. The
    # diagnoser writes level-4 hypotheses only (S2), never evidence; these
    # bound latency and spend.
    _ConfigRule(_exact(
        "diagnosis.next_item_wait_seconds",
        "diagnosis.max_attempts",
        "diagnosis.max_calls_per_day",
        "diagnosis.timeout_seconds",
        "diagnosis.full_history_token_budget",
        "diagnosis.exact_history_token_budget",
    ), "structural", "operational",
        "diagnosis queue wait / retry / daily call cap / turn deadline / context token budget; no "
        "measurement authority (the diagnoser never writes evidence, S2)."),
    # Slice 2 T1: live same-cause judge spend and latency bounds. The judge
    # writes judgment_ledger verdicts, never evidence.
    _ConfigRule(_exact(
        "recurrence.judge_max_pairs_per_attempt",
        "recurrence.judge_timeout_seconds",
    ), "structural", "operational",
        "same-cause judge calls per diagnose job / turn deadline; spend and latency bounds, no "
        "measurement authority (verdicts go to judgment_ledger, never evidence)."),
    # Learner-text gaps: per-text spend and latency bounds of the pipeline's
    # judge, reader, Decider and draft calls (verdicts go to judgment_ledger,
    # never evidence).
    _ConfigRule(_exact(
        "learner_text_gaps.judge_max_pairs",
        "learner_text_gaps.judge_timeout_seconds",
        "learner_text_gaps.max_calls_per_text",
        "learner_text_gaps.max_usd_per_text",
        "learner_text_gaps.max_calls_per_day",
        "learner_text_gaps.metered_price_per_million",
    ), "structural", "operational",
        "learner-text gap judge pairs per text / turn deadline / per-text call and dollar caps / the live "
        "path's daily call cap / owner price for metered routes; spend and latency bounds, no measurement "
        "authority."),
    # Reader workbench RW1a: the reconnect line's passage check (formative
    # questions only; the learner's self-checks go to judgment_ledger, never
    # evidence).
    _ConfigRule(_exact(
        "reader_inquiry.max_checks_per_day",
        "reader_inquiry.max_usd_per_check",
        "reader_inquiry.metered_price_per_million",
    ), "structural", "operational",
        "passage quick checks per UTC day / per-check dollar cap on a metered route / owner price for "
        "metered routes; spend bounds, no measurement authority."),
    # Reader workbench RW2a: how long an untouched open problem waits before
    # the recap calls it "unfinished" (a display limit; nothing is closed).
    _ConfigRule(_exact(
        "workbench.open_session_days",
    ), "structural", "operational",
        "days before an untouched open workbench problem shows as unfinished; a display limit, no "
        "measurement, scheduling or serving authority (nothing is closed automatically)."),
    # Reader workbench RW1b: the intent box's router (one Decider choice per
    # routing; verdicts go to judgment_ledger, never evidence): the typing
    # pause before a speculative routing, the routing's deadline and the
    # route's daily call cap (speculation stops at 80% of it).
    _ConfigRule(_exact(
        "reader_intent.speculate_after_ms",
        "reader_intent.timeout_seconds",
        "reader_intent.max_calls_per_day",
    ), "structural", "operational",
        "the typing pause before a speculative intent routing / its deadline / the route's daily Decider "
        "call cap; latency and spend bounds, no measurement authority (a routing only picks which palette "
        "action runs)."),
    # Reader workbench RW4a: the library answer's organizer (one listwise call
    # per ask; notes are display, verdicts go to judgment_ledger, never
    # evidence): its metered spend a UTC day.
    _ConfigRule(_exact(
        "library_ask.max_daily_cost_usd",
    ), "structural", "operational",
        "the library answer's organizer's metered spend a UTC day; a money bound, no measurement "
        "authority (its notes are display only)."),
    # Adaptive hints H1: the approach-map builds' (and merges') metered spend a
    # UTC day (maps are stored help, read by no grading, scheduling, serving or
    # replay path; validation verdicts go to judgment_ledger, never evidence).
    _ConfigRule(_exact(
        "hints.maps.max_daily_cost_usd",
    ), "structural", "operational",
        "the approach-map builds' and merges' metered spend a UTC day; a money bound, no measurement "
        "authority (maps are help, never evidence)."),
    # Adaptive hints H2a: the hint writer's and chooser's metered spend a UTC
    # day, and the chooser's time box (a shown hint reaches the attempt only
    # through hints_used / primed with their existing meaning; the choice and
    # its propensity go to help_assists and judgment_ledger, never evidence).
    _ConfigRule(_exact(
        "hints.max_daily_cost_usd",
        "hints.chooser_timeout_seconds",
    ), "structural", "operational",
        "the hint writer's and chooser's metered spend a UTC day / the chooser's time box before the "
        "fallback serves; money and latency bounds, no measurement authority (no constant decides which "
        "hint a learner gets, spec H3)."),
    # Adaptive hints H2b: how long a hint is written before the practice
    # screen's panel offers the item's own hint instead (a display cap; the
    # offer cancels the request first, so one hint is recorded either way).
    _ConfigRule(_exact(
        "hints.authored_offer_after_seconds",
    ), "structural", "display",
        "seconds a hint is being written before the panel offers the item's own hint instead; a display "
        "cap, no measurement authority (no constant decides which hint a learner gets, spec H3)."),
    # Adaptive difficulty AD1: the outside forecasters' and the feature
    # audit's metered spend a UTC day (receipts and judgments only: nothing
    # serving, scoring, scheduling, evidence or certification reads them, A2).
    _ConfigRule(_exact(
        "adaptive_difficulty.daily_spend_cap_usd",
    ), "structural", "operational",
        "the outside forecasters' and feature audit's metered spend a UTC day; a money bound, no "
        "measurement authority (AD1 logs forecasts and audits, it decides nothing served)."),
    # Tutor delivery fixes (2026-10-13): the source text one tutor turn reads
    # (a context-size bound) and one automatic source-block backfill's spend.
    _ConfigRule(_exact(
        "tutor_qa.context_token_budget",
        "embedding.source_backfill_max_cost_usd",
    ), "structural", "operational",
        "tutor context token budget / automatic source-block embedding backfill dollar cap; context and "
        "spend bounds, no measurement authority (delivery is context for one answer; vectors rank retrieval "
        "candidates only)."),
    _ConfigRule(_prefix("project."), "structural", "operational",
                "Project-understanding M1 knob (probe delay/count, context window, sweep "
                "throttle); it acts only on the standalone projects/project_store.sqlite, "
                "whose answers are practice only, so it has no vault measurement authority."),
    _ConfigRule(_prefix("families."), "structural", "operational",
                "Explicit-command authoring candidate bounds; judges decide identity, "
                "with no live measurement or scheduling authority."),
    _ConfigRule(_prefix("practice_index."), "structural", "operational",
                "find_practice retrieval/proposal sizes, rank-fusion constant, coverage "
                "threshold and rerank spend; it proposes and never serves, so no "
                "measurement or serving authority."),
    _ConfigRule(_prefix("source_service."), "structural", "operational",
                "Canonical-sources service kill switches, time and prompt-size bounds and "
                "spend caps; tools propose and existing serving paths serve, verdicts go to "
                "judgment_ledger, and value of information (never a count) decides how many "
                "checks, so no measurement or serving authority."),
    _ConfigRule(_prefix("graph_nomination."), "structural", "operational",
                "Slice 2 T5 nomination rank limit and ingest-time embedding caps; "
                "nominations only (the structuring/append model or the owner decides), "
                "with no measurement or scheduling authority."),
    _ConfigRule(_prefix("source_retrieval."), "structural", "operational",
                "Slice 2 T6 retrieval switches, fusion constant, pool sizes and live "
                "rewrite/rerank/query-embedding spend; retrieval is context for the "
                "library search, tutor spans, Quick Add preview and labelled LO "
                "suggestions, with no measurement, scheduling or serving authority."),
    _ConfigRule(_prefix("pf."), "structural", "operational",
                "PF-b generation bounds (candidates, panel solves, sandbox limits, daily "
                "publish cap). Publishing verified items is a content change; difficulty "
                "comes from the solver panel and judges/verifiers decide, so these knobs "
                "carry no measurement authority."),
    _ConfigRule(_prefix("facet_identity."), "structural", "operational",
                "Facet-identity judge bounds (neighbourhood size, shortlist rank, spend "
                "caps, owner price); the judge decides which facets are one skill, a "
                "vault-content change with an undo, with no measurement or scheduling "
                "authority."),
    _ConfigRule(_exact(
        "scheduler.candidate_log_retention_limit",
        "probe.episode.presentation_ttl_minutes",
        "probe.shadow.top_k",
        "probe.block.max_block_size",
        "probe.block.conditional_branch_cap",
        "probe.calibration.default_time_budget_minutes",
        "probe.calibration.max_planned_episodes",
        "tutor_qa.max_questions_practice",
        "tutor_qa.max_questions_feedback",
        "tutor_qa.max_questions_library",
        "tutor_qa.max_questions_reader",
        "teach_back.max_followups",
        "teach_back.session_cap",
        "tutor_promotion.requested_items_per_session",
    ), "structural", "operational",
        "server-side rate limit / telemetry retention / conversation cap; no live authority."),
    _ConfigRule(_prefix("probe.generation.", "probe.dialogue."), "structural", "operational",
                "generation/dialogue turn budgets; no measurement authority."),
    # --- structural: numerical clamps / epsilons / display ---
    _ConfigRule(_exact("mastery.irt.p_clip", "mastery.irt.b_var_min"),
                "structural", "numerical", "numerical clamp/epsilon; mathematical identity."),
    _ConfigRule(_exact("mastery.display_strong_threshold", "mastery.display_developing_threshold"),
                "structural", "display", "display formatting threshold (§6 excluded)."),
    # --- structural: test fixtures ---
    _ConfigRule(_prefix("recall_coverage.severity_examples."), "structural", "fixture",
                "expected-band severity fixtures (test data)."),
    # --- structural: legacy-frozen probe block (pre-redesign replay) ---
    _ConfigRule(_exact(
        "probe.attempts_target_default", "probe.attempts_target_with_strong_claim",
        "probe.claim_skip_threshold", "probe.variance_convergence_threshold",
        "probe.hypothesis_set_max_size",
    ), "structural", "fixture",
        "legacy probe block frozen pre-redesign; replays via the mvp-0.6 manifest, not live."),
    # --- structural: FSRS solver-internal knobs ---
    _ConfigRule(_exact(
        "fitting.fsrs.l2_lambda", "fitting.fsrs.max_iterations",
        "fitting.fsrs.initial_step", "fitting.fsrs.min_relative_improvement",
    ), "structural", "numerical", "FSRS solver-internal knob; not a measurement decision."),
    # --- structural: evidence-mass identity (excluded attempt types carry no mass) ---
    _ConfigRule(_exact("evidence.attempt_types.guided_walkthrough.evidence_mass",
                       "evidence.attempt_types.skip.evidence_mass"),
                "structural", "evidence_mass",
                "identity: excluded attempt types carry no evidence mass (fixed 0)."),

    # ======================= DECISION rules =======================
    # FSRS admission gates (decision, source may be fitted).
    _ConfigRule(_exact("fitting.fsrs.min_reviews", "fitting.fsrs.min_elapsed_days"),
                "decision", "threshold", "FSRS fit admission gate (calibration admission decision)."),
    # Deletion-candidate shaping weights (sim-proven decision-inert, §9.1/§4).
    _ConfigRule(_exact(
        "scheduler.forgetting_risk_weight", "scheduler.goal_frontier_weight",
        "scheduler.recent_error_weight", "scheduler.probe_eig_weight",
        "scheduler.followup.predictive_eig_weight", "probe.calibration.disagreement_weight",
    ), "decision", "shaping_weight",
        "additive priority shaping weight; the sim-sweep found weights decision-inert while "
        "membership/caps do the work -> deletion candidate pending a redundancy proof.",
        lifecycle="active"),
    _ConfigRule(_suffix(".lo_mastery_delta"), "decision", "shaping_weight",
                "legacy additive mastery delta; new code uses local_severity_gain instead "
                "-> deletion candidate.", lifecycle="active"),
    # Dormant-with-monitoring constraint parameters (caps/floors/clamps, bind-log).
    _ConfigRule(_exact(
        "evidence.certification.max_groups_per_attempt",
        "mastery.irt.b_abs_max", "mastery.irt.mu_abs_max", "mastery.irt.max_logit_step",
        "scheduler.followup.tau_repeated_item_failures",
        "scheduler.followup.tau_repeated_facet_failures",
        "scheduler.followup.max_interventions_per_lo_per_session",
        "scheduler.followup.max_diagnostic_target_facets",
        "scheduler.followup.predictive_eig_target_cap",
        "probe.episode.maximum_observations",
        "probe.episode.session_qualifying_observation_cap",
        "probe.episode.predictive_target_cap",
        "probe.episode.onboarding_practice_ceiling_observations",
        "recall_coverage.variance_floor_at_zero_coverage",
        "recall_coverage.variance_floor_at_full_coverage",
        "tutor_promotion.gap_need_ttl_days",
        # Meas §3.A1 guard 2 (implementation plan item 6.1): the largest share of
        # a cell's certification credit that may come from embedded (supporting-
        # role) observations. A cap in the strict sense -- it binds only where
        # conjunctive authoring has actually produced embedded credit, and it is
        # what stops A1's throughput from arriving as positive smearing.
        "evidence.certification.max_embedded_credit_share",
        # Meas §3.A6 (item 6.2): the per-session ceiling on asking the learner for
        # a one-line justification. Standing constraint 10 makes annoyance a
        # first-class regression, so this is the guardrail that stops elicitation
        # creeping, not a tuned throughput knob.
        "trace_evidence.max_elicitations_per_session",
    ), "decision", "constraint",
        "cap/floor/clamp/membership guardrail; inert in the nominal scenario but binds under "
        "distribution shift -> dormant-with-monitoring (bind-event logging).",
        lifecycle="dormant", bind_site="config guardrail expression (min/max/clamp)"),
    # Aug Stage 7 C3/C4. Both change diagnostic decisions and learner/model
    # burden, so neither may hide as an unregistered operational constant.
    # ``sampling_enabled`` is the on/off half of the SAME C3 decision: it is what
    # a revert actually flips, and Inventory A's numeric-leaf walk skips booleans,
    # so leaving it unregistered would have hidden the rung's kill switch from the
    # audit that exists to enumerate rung decisions.
    _ConfigRule(
        _exact(
            "diagnostic_augmentation.sampling_enabled",
            "diagnostic_augmentation.sample_count",
            "diagnostic_augmentation.history_limit",
        ),
        "decision",
        "constraint",
        "C3 independent diagnosis-call switch/count and C4 same-surface history "
        "bound; each rung has a persisted hypothesis and revert criterion.",
    ),
    # Slice 1 M2: what the history-aware diagnoser is shown and how often it
    # runs. Its output is a level-4 hypothesis that enters routing through the
    # existing causal machinery, so these are decisions with a revert path
    # (history_mode = "exact" with history_error_limit = 0 restores a
    # history-free diagnoser, spec §5.5), never evidence weights.
    _ConfigRule(
        _exact(
            "diagnosis.history_error_limit",
            "diagnosis.history_success_limit",
            "diagnosis.sample_count",
            "diagnosis.correct_answer_sample_rate",
            "diagnosis.knn_limit",
            "diagnosis.hybrid_keep",
            "diagnosis.rrf_k",
        ),
        "decision",
        "constraint",
        "Slice 1 diagnoser context bounds, sampling and hybrid fusion; hypothesis-only "
        "(S2), reverted by history_mode/limits (spec §5.5, §12 rollback).",
    ),
    # Learner field F2 (Slice A Phase 6): placement routing. These decide which
    # new LOs are assumed known (never evidence) and when the check is due.
    _ConfigRule(_exact(
        "placement.fast_track_min_correct", "placement.fast_track_q",
        "placement.known_probability", "placement.assumed_first_interval_days",
    ), "decision", "threshold",
        "F2 placement routing threshold (field D6): fast-track admission and the "
        "assumed LO's first-review interval; a priori, versioned, tuned from report 3."),
    _ConfigRule(_exact("placement.quick_check_k", "placement.quick_check_budget_minutes"),
                "structural", "operational",
                "optional learner-initiated quick-check length and time bound (field D4)."),
    # Learner-text gaps (implementation_handoffs §4): the vault-wide shortlist
    # breadth (judges decide, R4), the daily cap on created prerequisites, the
    # created LO's delayed check and mvp-0.16's sooner-check delay. A priori,
    # owner-accepted defaults; read from `learnloop gaps report`.
    _ConfigRule(
        _exact("learner_text_gaps.top_k", "learner_text_gaps.max_creations_per_day"),
        "decision",
        "constraint",
        "learner-text gap shortlist breadth (judges decide every pair, R4) and the daily cap on "
        "prerequisites created from learner text; kill switches learner_text_gaps.enabled and "
        "create_prerequisites_enabled.",
    ),
    _ConfigRule(
        _exact("learner_text_gaps.seed_check_delay_days", "learner_text_gaps.sooner_check_delay_hours"),
        "decision",
        "threshold",
        "learner-text gap check timing: a created prerequisite's one delayed check, and mvp-0.16's "
        "bound on how soon a gap brings a check forward (kill switch sooner_check_enabled).",
    ),
    # Slice 2 T1 (mvp-0.12): which embedding-shortlisted pairs reach the
    # same-cause judge. Recall-oriented blocking only: the judge decides every
    # pair it sees and nothing is merged or rejected by score (R4). Set from
    # B3's recall on confirmed matches; reverted by recurrence.enabled = false.
    _ConfigRule(
        _exact("recurrence.top_k"),
        "decision",
        "constraint",
        "Slice 2 T1 same-cause shortlist breadth; set from B3, judges decide (R4), "
        "kill switch recurrence.enabled.",
    ),
    _ConfigRule(
        _prefix("recurrence.blocking_cutoffs."),
        "decision",
        "threshold",
        "Slice 2 T1 per-model blocking cutoff from B3's recall on confirmed matches; never "
        "hand-set in code, never merges or rejects by score (R4).",
    ),
    # Daily-loop DL1 (mvp-0.14): the finite plan. The split caps and the
    # new-material admission decide what Today serves (never evidence); they
    # are a priori owner defaults (D2, Q11), versioned with daily_plan_v1.
    _ConfigRule(_exact(
        "plan.repair_max_share", "plan.maintain_max_share", "plan.load_ceiling",
        "plan.max_new_items_per_day", "plan.min_new_items_per_day",
        "plan.new_item_reviews_14d", "plan.load_horizon_days",
        "plan.reentry_minutes", "plan.reentry_max_items", "plan.project_probes_max_per_day",
    ), "decision", "constraint",
        "daily-plan split cap, new-material admission or re-entry cap (spec_daily_loop_v1 "
        "§6.2, §6.3, §7); a serving guardrail, never evidence; owner default, versioned."),
    _ConfigRule(_exact(
        "plan.default_minutes", "plan.keep_going_minutes", "plan.latency_cap_minutes",
        "plan.read_words_per_minute", "plan.pre_questions", "plan.minutes_presets",
    ), "structural", "operational",
        "daily-plan budget size, duration-estimate winsorizing or reading pace; sizes the "
        "plan and its labels, no measurement authority."),
    # Router R2a (mvp-0.23): the learner-state card's size budget (D8) and how
    # long its stored text is kept. Neither decides what is served (the staged
    # frame's choice never reads the card in R2a) nor reaches evidence.
    _ConfigRule(_exact("router.card_token_budget", "router.payload_retention_days"), "structural", "operational",
                "router learner-state card budget (D8: older successes, then excerpts, then attempts drop; "
                "typed fields never) and the stored payload's retention; sizes a receipt, no measurement "
                "or serving authority."),
    # Router R2b + R2c (mvp-0.24): the model mixture's weights, support size
    # and floor decide which block is served (never evidence); D1/D3 owner
    # defaults, versioned with the successor; R3's switching rule moves them.
    _ConfigRule(_exact(
        "router.weights.staged", "router.weights.decider", "router.weights.llm", "router.k", "router.epsilon_min",
        "router.similar_include_rate",
    ), "decision", "shaping_weight",
        "router model mixture: component weights (D1), top-k options (D3), the exploration floor and the "
        "similar-decision inclusion rate (a logged coin); a serving draw with exact propensities, never "
        "evidence; R3's switching rule (spec §10.4) moves the weights."),
    _ConfigRule(_exact(
        "router.timeout_seconds", "router.prefetch_timeout_seconds", "router.max_daily_cost_usd", "router.similar_k",
    ), "structural", "operational",
        "router model budgets (time a serving step waits, time the models have from prefetch), the metered "
        "daily guard and the similar-decision shortlist size; a fallback moves weight to the staged rule, "
        "no measurement authority."),
    # mvp-0.21 value-of-information stopping: the multi-family EVSI study's
    # switches (docs/reviews/evsi-multisim.md §6.1, ranks 2 and 3; rank 1 is a
    # boolean). Heuristic until live voi_forecasts calibrate them.
    _ConfigRule(_exact("voi_stopping.robust_quantile"), "decision", "threshold",
                "value-of-information gate's lower credible-set quantile (rank_feasible's robust EVSI, the "
                "robust EIG, the lookahead's batch value); the multi-family study's rank 3 (0.25, "
                "directional in all four simulator families); 0.10 restores "
                "robust_composition.ROBUST_QUANTILE, which the mvp-0.8 paths keep."),
    _ConfigRule(_exact("voi_stopping.lookahead_max_checks"), "decision", "threshold",
                "how many ranked checks the probe-episode value gate values jointly when a decision is at "
                "stake and no single check pays (the study's rank 2; one check per surface group); a "
                "valuation depth, never a count of observations served; 1 turns the lookahead off."),
    # Dormant ships-dark forward-compat params (subsystem disabled).
    _ConfigRule(_exact(
        "mastery.irt.discrimination_min", "mastery.irt.discrimination_max",
        "mastery.irt.b_prior_variance", "mastery.irt.b_learning_rate_scale",
        "mastery.irt.b_max_step",
    ), "decision", "prior",
        "forward-compat IRT/EB parameter; ships dark (fixed / feature-disabled in Phase A).",
        lifecycle="dormant", bind_site="mastery.irt (feature-gated, dark)"),
    _ConfigRule(_prefix("capabilities.residual_"), "decision", "threshold",
                "residual-activation parameter; ships dark (residual_activation_enabled=False).",
                lifecycle="dormant", bind_site="capabilities.residual (feature-gated, dark)"),
    # Evidence-mass decision leaves.
    _ConfigRule(_suffix(".evidence_mass", ".surface_exposure"), "decision", "evidence_mass",
                "attempt-type evidence-mass / surface-exposure anchor (eligibility & mass)."),
    # Re-rung request evidence package (``learnloop.content.authoring.rung_variants``):
    # the self-report
    # grade fractions and claim levels ARE the evidence a request writes.
    _ConfigRule(_exact(
        "rung_variants.easier_score_fraction", "rung_variants.harder_score_fraction",
        "rung_variants.easier_claim_level", "rung_variants.harder_claim_level",
        "rung_variants.self_grade_confidence",
    ), "decision", "evidence_mass",
        "rung-variant request evidence: deterministic self-report grade / claim level."),
    _ConfigRule(_exact("rung_variants.claim_pseudo_count"), "decision", "prior",
                "rung-variant claim prior pseudo-count (posterior weight)."),
    _ConfigRule(_exact("rung_variants.max_pending_per_item"), "structural", "operational",
                "per-item request lock cap; no measurement authority."),
    _ConfigRule(_prefix("evidence.item_coverage"), "decision", "prior",
                "practice-mode coverage prior (surface exposure fraction)."),
    _ConfigRule(_prefix("evidence.blueprints."), "decision", "likelihood",
                "noisy-AND slip/guess recipe likelihood."),
    _ConfigRule(_prefix("probe.irt."), "decision", "likelihood",
                "probe 2PL conditional point constants (P(Z|H))."),
    _ConfigRule(_suffix("_pseudo_count", "_prior_scale", "_prior_variance"), "decision", "prior",
                "Bayesian prior pseudo-count/scale (posterior/interval)."),
    _ConfigRule(_prefix("recall_coverage."), "decision", "evidence_mass",
                "recall-coverage discount/blend/threshold (familiarity & facet evidence)."),
    _ConfigRule(_prefix("error_impacts."), "decision", "threshold",
                "mastery damage magnitude per error type (posterior update)."),
    # Everything else under these decision namespaces -> threshold decision.
    # NOTE: this catch-all is FROZEN to a snapshot below (see _freeze_catchall_rule):
    # it classifies only the leaves it matched at freeze time, so a *future* field
    # added under one of these namespaces stays unclassified and fails the audit
    # loudly rather than being silently swept into "threshold" (F6).
    _ConfigRule(_prefix(
        "scheduler.", "goals.", "hypothesis.", "forecasts.", "mastery.",
        "probe.", "facet_diagnostic.", "misconceptions.", "practice_generation.",
        "exam_seeding.", "tutor_qa.", "tutor_promotion.", "teach_back.",
        "locks.", "capabilities.",
    ), "decision", "threshold",
        "ranking/stopping/routing/claim threshold or gate (measurement authority)."),
]

# The catch-all decision-namespace rule (last rule) must not silently absorb future
# fields (F6). We snapshot the paths it currently owns and rebind it to an explicit
# membership test, so a new numeric leaf under those namespaces is UNCLASSIFIED.
_CATCHALL_RULE = _CONFIG_RULES[-1]


def classify_config_path(path: str) -> _ConfigRule | None:
    for rule in _CONFIG_RULES:
        if rule.match(path):
            return rule
    return None


# ---------------------------------------------------------------------------
# Config numeric-leaf walk (Inventory A).
# ---------------------------------------------------------------------------

def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def config_numeric_leaves(config: LearnLoopConfig | None = None) -> dict[str, Any]:
    """Every numeric leaf of the ``LearnLoopConfig`` pydantic tree, keyed by dotted
    path. Numeric tuples (bands) are single leaves; booleans/strings are skipped."""

    cfg = config or LearnLoopConfig()
    leaves: dict[str, Any] = {}

    def walk_value(value: Any, path: str) -> None:
        if isinstance(value, BaseModel):
            for name in type(value).model_fields:
                walk_value(getattr(value, name), f"{path}.{name}" if path else name)
            return
        if isinstance(value, dict):
            for key, sub in value.items():
                walk_value(sub, f"{path}.{key}")
            return
        if isinstance(value, (list, tuple)):
            if value and all(_is_number(x) for x in value):
                leaves[path] = tuple(value)
                return
            for i, sub in enumerate(value):
                walk_value(sub, f"{path}[{i}]")
            return
        if _is_number(value):
            leaves[path] = value

    walk_value(cfg, "")
    return leaves


# ---------------------------------------------------------------------------
# Module-constant AST walk (Inventory B).
# ---------------------------------------------------------------------------

def _module_path(rel: str) -> Path:
    return Path(__file__).resolve().parents[3] / rel


def _numeric_ast(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant) and _is_number(node.value):
        return True
    if isinstance(node, ast.UnaryOp) and isinstance(node.operand, ast.Constant) and _is_number(node.operand.value):
        return True
    if isinstance(node, ast.Dict):
        return any(isinstance(v, ast.Constant) and _is_number(v.value) for v in node.values)
    if isinstance(node, (ast.Tuple, ast.List)):
        return any(isinstance(v, ast.Constant) and _is_number(v.value) for v in node.elts)
    return False


def module_numeric_constants() -> list[str]:
    """Module-level UPPERCASE numeric constants across the §2.1 module inventory,
    as ``module:CONSTANT`` paths."""

    found: list[str] = []
    for module, rel in MODULE_INVENTORY.items():
        path = _module_path(rel)
        if not path.exists():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            targets: list[str] = []
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name) and tgt.id.isupper() and _numeric_ast(node.value):
                        targets.append(tgt.id)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if node.target.id.isupper() and node.value is not None and _numeric_ast(node.value):
                    targets.append(node.target.id)
            for name in targets:
                found.append(f"{module}:{name}")
    return found


def tagged_decision_constants() -> list[str]:
    """Module constants carrying the ``# decision parameter`` breadcrumb comment,
    as ``module:CONSTANT`` paths (the drift cross-check surface of §2.3)."""

    tagged: list[str] = []
    for module, rel in MODULE_INVENTORY.items():
        path = _module_path(rel)
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if "# decision parameter" not in line:
                continue
            head = line.split("=", 1)[0].strip()
            name = head.split(":", 1)[0].strip()  # strip type annotations
            if name and name.replace("_", "").isalnum() and name.upper() == name:
                tagged.append(f"{module}:{name}")
    return tagged


# ---------------------------------------------------------------------------
# Effective-value resolution.
# ---------------------------------------------------------------------------

@dataclass
class ResolutionContext:
    config: LearnLoopConfig
    default_config: LearnLoopConfig
    repository: Repository | None = None


def _resolve_config_value(path: str, config: LearnLoopConfig) -> Any:
    node: Any = config
    for part in path.split("."):
        if isinstance(node, BaseModel):
            node = getattr(node, part)
        elif isinstance(node, dict):
            node = node[part]
        else:
            node = getattr(node, part)
    if isinstance(node, (list, tuple)):
        return list(node)
    return node


_MODULE_ATTR_CACHE: dict[str, Any] = {}


def _resolve_module_constant(path: str) -> Any:
    import importlib

    module_name, const = path.split(":", 1)
    try:
        full = MODULE_IMPORTS[module_name]
    except KeyError as exc:
        raise KeyError(f"No registered module import for {module_name!r}") from exc
    mod = _MODULE_ATTR_CACHE.get(full)
    if mod is None:
        mod = importlib.import_module(full)
        _MODULE_ATTR_CACHE[full] = mod
    value = getattr(mod, const)
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def resolve_effective(spec: ParameterSpec, ctx: ResolutionContext) -> tuple[Any, str]:
    """Return (effective_value, source). Config leaves compare against the pristine
    default to decide default vs vault_override; module constants are code defaults."""

    if spec.resolver is not None:
        value = spec.resolver(ctx)
        return value, "default"
    if ":" in spec.path:  # module constant
        return _resolve_module_constant(spec.path), "default"
    value = _resolve_config_value(spec.path, ctx.config)
    default_value = _resolve_config_value(spec.path, ctx.default_config)
    source = "vault_override" if value != default_value else "default"
    return value, source


# ---------------------------------------------------------------------------
# Registry build: turn the config rules into concrete ParameterSpecs so the
# whole registry (module constants + config leaves) is one machine-readable dict.
# ---------------------------------------------------------------------------

def _freeze_catchall_rule() -> frozenset[str]:
    """Snapshot the config leaves the broad decision-namespace catch-all currently
    owns, then rebind the rule to match only that explicit set (F6). Everything a
    prior rule already claims is excluded; a future field is left unclassified."""

    from dataclasses import replace as _dc_replace

    owned: set[str] = set()
    for path in config_numeric_leaves().keys():
        for rule in _CONFIG_RULES:
            if rule.match(path):
                if rule is _CATCHALL_RULE:
                    owned.add(path)
                break
    snapshot = frozenset(owned)
    idx = _CONFIG_RULES.index(_CATCHALL_RULE)
    _CONFIG_RULES[idx] = _dc_replace(_CATCHALL_RULE, match=lambda p: p in snapshot)
    return snapshot


CATCHALL_SNAPSHOT: frozenset[str] = _freeze_catchall_rule()


def _register_config_path(path: str) -> bool:
    """Register one config leaf from its classification rule. False if unclassified."""

    if path in REGISTRY:
        return True
    rule = classify_config_path(path)
    if rule is None:
        # Deliberately NOT registered: the audit reports it as unclassified.
        return False
    register(
        ParameterSpec(
            path=path,
            kind=rule.kind,
            param_class=rule.param_class,
            owner="config",
            rationale=rule.rationale,
            default_status=rule.status,
            default_lifecycle=rule.lifecycle,
            source_of_value="config",
            promotion_gate=rule.gate if rule.kind == "decision" else None,
            bind_site=rule.bind_site,
        )
    )
    return True


#: Boolean config leaves that are DECISIONS, not structure. Inventory A walks
#: numeric leaves only (``config_numeric_leaves`` skips bools), so a flag that
#: switches a rung on and off -- the thing a revert flips -- would otherwise never
#: reach the registry at all. Enumerated rather than swept: most config booleans
#: really are structural, and a blanket bool sweep would bury these among them.
BOOLEAN_DECISION_LEAVES: tuple[str, ...] = (
    "diagnostic_augmentation.sampling_enabled",
)


def _build_config_specs() -> None:
    for path in sorted(config_numeric_leaves().keys()):
        _register_config_path(path)
    for path in BOOLEAN_DECISION_LEAVES:
        if not _register_config_path(path):
            raise RuntimeError(
                f"boolean decision leaf {path} has no classification rule"
            )


_build_config_specs()


# ---------------------------------------------------------------------------
# Projection refresh (migration 069 parameter_registry).
# ---------------------------------------------------------------------------

def decision_specs() -> list[ParameterSpec]:
    return [s for s in REGISTRY.values() if s.kind == "decision"]


def refresh(vault: LoadedVault, repository: Repository, *, clock: Clock | None = None) -> int:
    """Rebuild the per-vault ``parameter_registry`` projection from the code
    definition + resolved effective values. Idempotent. Implements the value-change
    demotion rule (§6): if a previously-promoted value changed with no matching
    evidence, demote it to ``heuristic`` and clear its certificate link."""

    ctx = ResolutionContext(config=vault.config, default_config=LearnLoopConfig())
    written = 0
    for spec in decision_specs():
        value, source = resolve_effective(spec, ctx)
        value_hash = canonical_hash(value)
        prior = repository.parameter_registry_entry(spec.path)
        status: Status = spec.default_status
        lifecycle: Lifecycle = spec.default_lifecycle
        cert_id = None
        promotion_evidence_id = None
        evidence_manifest_id = None
        redundancy_proof_id = None
        last_review_at = None
        if prior is not None:
            status = prior["status"]  # preserve promotions across refreshes
            lifecycle = prior["lifecycle"]
            cert_id = prior.get("sensitivity_certificate_id")
            promotion_evidence_id = prior.get("promotion_evidence_id")
            evidence_manifest_id = prior.get("evidence_manifest_id")
            redundancy_proof_id = prior.get("redundancy_proof_id")
            last_review_at = prior.get("last_review_at")
            value_changed = prior["effective_value_hash"] != value_hash
            if value_changed:
                certs = repository.sensitivity_certificates_for_path(spec.path)
                # (a) A value change outside the covered hash invalidates the COVERAGE
                # certificate -- it is pending again until a re-sweep covers the new
                # value (U-022 v2). Clear a stale coverage link.
                coverage_covers = bool(cert_id) and any(
                    c["id"] == cert_id and c["covered_value_hash"] == value_hash for c in certs
                )
                if not coverage_covers:
                    cert_id = None
                # (b) A value change without matching PROMOTION EVIDENCE demotes status
                # to heuristic (§6) and drops the sim/real-outcome/redundancy links it
                # was standing on (F10b), else stale evidence keeps vouching for a value
                # the sim no longer covers.
                if status != "heuristic":
                    promotion_covers = bool(promotion_evidence_id) and any(
                        c["id"] == promotion_evidence_id
                        and c["covered_value_hash"] == value_hash
                        and c["decision_stable"]
                        for c in certs
                    )
                    if not promotion_covers:
                        status = "heuristic"
                        promotion_evidence_id = None
                        evidence_manifest_id = None
                        redundancy_proof_id = None
        repository.upsert_parameter_registry_entry(
            entry={
                "path": spec.path,
                "kind": spec.kind,
                "param_class": spec.param_class,
                "effective_value": value,
                "effective_value_hash": value_hash,
                "source": source,
                "status": status,
                "lifecycle": lifecycle,
                "rationale": spec.rationale,
                "scope": spec.scope,
                "owner": spec.owner,
                "sensitivity_certificate_id": cert_id,
                "evidence_manifest_id": evidence_manifest_id,
                "redundancy_proof_id": redundancy_proof_id,
                "promotion_evidence_id": promotion_evidence_id,
                "last_review_at": last_review_at,
            },
            clock=clock,
        )
        written += 1
    return written


def set_promotion_evidence_id(
    repository: Repository,
    path: str,
    evidence_id: str | None,
    *,
    clock: Clock | None = None,
) -> None:
    """Persist the ``promotion_evidence_id`` column for a registry row.

    Thin wrapper over the shared ``upsert_parameter_registry_entry`` for callers
    (e.g. :func:`sensitivity_certificates.promote`) that only want to touch this
    one field after already writing the rest of the entry."""

    entry = repository.parameter_registry_entry(path)
    if entry is None:
        return
    entry["effective_value"] = json.loads(entry["effective_value_json"])
    entry["promotion_evidence_id"] = evidence_id
    repository.upsert_parameter_registry_entry(entry=entry, clock=clock)


# ---------------------------------------------------------------------------
# Manifest freeze (§1.1c / §7).
# ---------------------------------------------------------------------------

def freeze_manifest(
    vault: LoadedVault,
    repository: Repository,
    *,
    algorithm_version: str,
    clock: Clock | None = None,
) -> str | None:
    """Freeze the immutable per-algorithm-version manifest of all decision
    parameters' effective value-hash/status/lifecycle/source. Idempotent per
    version (a second freeze is a no-op).

    F7 caveat: :func:`resolve_effective` reads the *live* config, so every version's
    manifest is captured from whatever config version is loaded at freeze time. We
    record that provenance explicitly as ``captured_from_config_version`` rather than
    pretend the values were resolved under the labelled ``algorithm_version``.
    Per-version value divergence (e.g. a value that legitimately differs between
    mvp-0.6 and mvp-0.7) is NOT yet represented -- when it is, this field is where
    the resolved-per-version values will diverge."""

    refresh(vault, repository, clock=clock)
    captured_from = vault.config.algorithms.algorithm_version
    params: dict[str, Any] = {}
    for row in repository.parameter_registry_entries():
        if row["kind"] != "decision":
            continue
        params[row["path"]] = {
            "value_hash": row["effective_value_hash"],
            "status": row["status"],
            "lifecycle": row["lifecycle"],
            "source": row["source"],
        }
    entries: dict[str, Any] = {
        "captured_from_config_version": captured_from,
        "per_version_divergence_represented": False,
        "parameters": params,
    }
    manifest_hash = canonical_hash(entries)
    return repository.insert_parameter_registry_manifest(
        algorithm_version=algorithm_version,
        manifest_hash=manifest_hash,
        entries=entries,
        clock=clock,
    )


# ---------------------------------------------------------------------------
# Bind-event logging (§4).
# ---------------------------------------------------------------------------

def record_bind(
    repository: Repository,
    path: str,
    context: dict[str, Any],
    *,
    observation_ref: str | None = None,
    clock: Clock | None = None,
) -> str:
    """Log that a dormant guardrail actually fired (§6). Callers thread this at the
    guardrail's bind site (the cap clamps / the floor lifts / the gate excludes)."""

    return repository.record_parameter_bind_event(
        path=path, bound_context=context, observation_ref=observation_ref, clock=clock
    )


# ---------------------------------------------------------------------------
# The audit (§2 / §9.6 / §9.7 item 5).
# ---------------------------------------------------------------------------

@dataclass
class AuditReport:
    unclassified_config: list[str] = field(default_factory=list)
    unclassified_constants: list[str] = field(default_factory=list)
    decision_without_metadata: list[str] = field(default_factory=list)
    # promotion_without_evidence: status above heuristic with no valid promotion
    # evidence (or, for live_calibrated, no real-outcome manifest) -- always a failure.
    promotion_without_evidence: list[str] = field(default_factory=list)
    # active_pending_certificate: an active decision parameter with no valid COVERAGE
    # certificate (U-022 v2). Enumerated DEBT, not a failure: a WARNING in the ordinary
    # audit, a FAILURE in the strict release gate (see ``release_clean``).
    active_pending_certificate: list[str] = field(default_factory=list)
    dormant_without_bind_monitoring: list[str] = field(default_factory=list)
    comment_registration_drift: list[str] = field(default_factory=list)

    @property
    def failures(self) -> list[str]:
        """The failure categories (name) that are non-empty. ``active_pending_
        certificate`` is deliberately excluded -- it is enumerated debt, not a
        failure, in the ordinary audit."""

        out: list[str] = []
        for name in (
            "unclassified_config",
            "unclassified_constants",
            "decision_without_metadata",
            "promotion_without_evidence",
            "dormant_without_bind_monitoring",
            "comment_registration_drift",
        ):
            if getattr(self, name):
                out.append(name)
        return out

    @property
    def clean(self) -> bool:
        """Ordinary audit cleanliness: no failures. Pending coverage certificates are
        a warning and do NOT flip this (else every fresh audit would be silently red)."""

        return not self.failures

    @property
    def release_clean(self) -> bool:
        """Strict release-gate cleanliness: clean AND zero pending coverage
        certificates. The gate treats outstanding coverage debt as blocking."""

        return self.clean and not self.active_pending_certificate

    def as_dict(self) -> dict[str, Any]:
        return {
            "clean": self.clean,
            "release_clean": self.release_clean,
            "unclassified_config": self.unclassified_config,
            "unclassified_constants": self.unclassified_constants,
            "decision_without_metadata": self.decision_without_metadata,
            "promotion_without_evidence": self.promotion_without_evidence,
            "active_pending_certificate": self.active_pending_certificate,
            "active_pending_certificate_count": len(self.active_pending_certificate),
            "dormant_without_bind_monitoring": self.dormant_without_bind_monitoring,
            "comment_registration_drift": self.comment_registration_drift,
        }


def audit(vault: LoadedVault | None = None, repository: Repository | None = None) -> AuditReport:
    """Run the decision-parameter audit. ``vault``/``repository`` are optional: the
    inventory coverage + comment-drift checks are static (code-only); the
    certificate/bind-monitoring checks read the per-vault projection when given."""

    report = AuditReport()

    # Inventory A: every config numeric leaf must be classified. REGISTRY is built
    # from the DEFAULT config, so a vault that adds dict keys (e.g. a custom
    # attempt-type evidence_mass) has leaves absent from REGISTRY; fall back to the
    # classification rules for those (F10a). A leaf a rule covers passes; one no rule
    # covers -- including a future field the frozen catch-all no longer absorbs (F6)
    # -- is reported unclassified.
    config = vault.config if vault is not None else LearnLoopConfig()
    for path in sorted(config_numeric_leaves(config).keys()):
        if path in REGISTRY:
            continue
        if classify_config_path(path) is None:
            report.unclassified_config.append(path)

    # Inventory B: every named module numeric constant must be registered.
    for path in module_numeric_constants():
        if path not in REGISTRY:
            report.unclassified_constants.append(path)

    # Decision metadata completeness (status/provenance/rationale).
    for spec in decision_specs():
        if not spec.rationale or spec.default_status is None or spec.source_of_value is None:
            report.decision_without_metadata.append(spec.path)

    # Comment <-> registration drift (§2.3): every constant carrying the
    # `# decision parameter` breadcrumb must have a matching registered spec (a
    # reworded/moved comment that orphans its tag surfaces here). A tag that the
    # code spec deliberately reclassifies structural (e.g. LAMBDA_TIME, fixed at
    # 1 -- §9.2) is still registered, so it is not drift; a tag with NO spec is.
    for path in tagged_decision_constants():
        if path not in REGISTRY:
            report.comment_registration_drift.append(path)
    # ...and no registered decision constant may lack a promotion gate (its
    # breadcrumb's machine counterpart -- the sim suite that could promote it).
    for spec in decision_specs():
        if ":" in spec.path and spec.promotion_gate is None:
            report.comment_registration_drift.append(spec.path)

    # Dormant constraint parameters must declare a bind site (static check).
    for spec in REGISTRY.values():
        if spec.kind != "decision":
            continue
        if spec.default_lifecycle == "dormant" and spec.param_class == "constraint":
            monitored = bool(spec.bind_site)
            if not monitored and repository is not None:
                monitored = bool(repository.parameter_bind_events_for_path(spec.path))
            if not monitored:
                report.dormant_without_bind_monitoring.append(spec.path)

    # U-022 v2 two-artifact split (per-vault projection checks):
    #  (a) COVERAGE: EVERY active decision parameter needs a valid coverage
    #      certificate (one covering its current value hash), regardless of status.
    #      Missing -> active_pending_certificate (enumerated debt: warning in the
    #      ordinary audit, failure in the release gate). Finding flip points does NOT
    #      make a coverage certificate invalid.
    #  (b) PROMOTION: a status above heuristic needs valid PROMOTION EVIDENCE (a
    #      decision_stable sim artifact covering the value); live_calibrated
    #      additionally needs the activated real-outcome evidence manifest (§6).
    #      Missing -> promotion_without_evidence (a failure).
    #  Dormant/deleted parameters need no coverage certificate -- dormancy is the
    #  explicit alternative to sweeping (bind-event logging covers them instead).
    if repository is not None:
        for row in repository.parameter_registry_entries():
            if row["kind"] != "decision":
                continue
            if row["lifecycle"] != "active":
                continue
            path = row["path"]
            value_hash = row["effective_value_hash"]
            certs = repository.sensitivity_certificates_for_path(path)

            cert_id = row.get("sensitivity_certificate_id")
            coverage_ok = bool(cert_id) and any(
                c["id"] == cert_id and c["covered_value_hash"] == value_hash for c in certs
            )
            if not coverage_ok:
                report.active_pending_certificate.append(path)

            if row["status"] in ("simulation_validated", "live_calibrated"):
                evidence_id = row.get("promotion_evidence_id")
                evidence_ok = bool(evidence_id) and any(
                    c["id"] == evidence_id
                    and c["covered_value_hash"] == value_hash
                    and c["decision_stable"]
                    for c in certs
                )
                manifest_ok = (
                    row["status"] != "live_calibrated" or bool(row.get("evidence_manifest_id"))
                )
                if not (evidence_ok and manifest_ok):
                    report.promotion_without_evidence.append(path)

    return report
