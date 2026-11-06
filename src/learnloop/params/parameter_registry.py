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
    # Local contextual retrieval P1 (spec_local_contextual_retrieval_v1 §9.5,
    # §9.6): the local space's pins and guardrails, the window rule, the
    # fallback client's limits and the fusion core's numerical budgets. No
    # ranking weight or margin is a constant here: those are learned (fusion).
    "local_pins": "src/learnloop/local_embeddings/pins.py",
    "local_fusion": "src/learnloop/local_embeddings/fusion.py",
    "source_windows": "src/learnloop/source_retrieval/windows.py",
    "fallback_space": "src/learnloop/source_retrieval/fallback_space.py",
    "local_index": "src/learnloop/source_retrieval/local_index.py",
    "voyage_contextual": "src/learnloop/ai/providers/voyage_contextual.py",
    "retrieval_feedback": "src/learnloop/source_retrieval/feedback.py",
    # Reader RW5d P1 (spec_reader_show_me_figures_v1 §8.3, §15): the figure
    # switches' leaf module, home of the grounding-passage cap.
    "figure_admission": "src/learnloop/figure_admission.py",
    # Reader RW5d P2 (spec_reader_show_me_figures_v1 §9, §15): the sketch tier's
    # caps, numerical tolerances and sandbox limits, every one a `keep`
    # guardrail (no learner-model weight, margin or threshold).
    "figure_sketch": "src/learnloop/figures/sketch.py",
    "figure_sketch_engine": "src/learnloop/figures/sketch_engine.py",
    "figure_sketch_verify": "src/learnloop/figures/sketch_verify.py",
    # Reader RW5d P2b (spec §9b, §15): the rich tiers' caps (the brief, the
    # rich calls, the declared-function checks), the plan-wait retry interval
    # and the Manim render sandbox's resource caps, every one a `keep`
    # guardrail (no learner-model weight, margin or threshold).
    "figure_rich": "src/learnloop/figures/rich.py",
    "figure_manim": "src/learnloop/figures/manim_figure.py",
    # Reader follow-ups Nov 1b (spec §9b.4, P2b ruling R2): the free-text
    # label rule's one structural bound (a `keep` wording guardrail).
    "figure_labels": "src/learnloop/figures/labels.py",
    # Learner data-relax 2 (owner principle 2026-11-01): what the figure
    # author is told about the learner; prompt-size bounds only, every one a
    # `keep` (no learner-model weight, margin or threshold).
    "figure_learner_state": "src/learnloop/figures/learner_state.py",
    # Reader RW5d P3 (spec §11.2, §11.4): figures as a help kind; a structural
    # ladder level and a read bound, every one a `keep` (no weight or margin).
    "figure_help": "src/learnloop/figures/help.py",
    # Reader RW5d P5 (spec §10b, §15): figures ahead of need. The decision model's
    # seeded, labelled priors (learn: data move them; LP §2 fields in each rationale),
    # the numerical resolution of its posterior, and the service's prompt, output and
    # queue bounds and the power probe's timeout, every one a `keep` guardrail. No
    # weight, margin or threshold decides a prebuild: the posterior EU does.
    "figure_prefetch": "src/learnloop/figures/prefetch.py",
    "figure_prefetch_model": "src/learnloop/figures/prefetch_model.py",
    "figure_power": "src/learnloop/figures/power.py",
    "figure_foreground": "src/learnloop/figures/foreground.py",
    "concept_animation": "src/learnloop/content/authoring/concept_animation.py",
    # FG1 §8: the leakage gate's shingle order now also decides whether a probe stops, and its span cap.
    "practice_leakage": "src/learnloop/content/authoring/practice_leakage.py",
    # Local contextual retrieval P2 (spec §7.1, §9.3, §9.6): the query student's pins and
    # guardrails, the decision core's computation budgets, the data and schedule budgets. No
    # quality margin or ranking weight is a constant: adoption, the screen's choice and whether
    # training continues are expected-utility decisions; the student's fusion weight is learned.
    "student_pins": "src/learnloop/local_embeddings/student_pins.py",
    "student_decision": "src/learnloop/local_embeddings/student_decision.py",
    "student_data": "src/learnloop/source_retrieval/student_data.py",
    "query_student": "src/learnloop/source_retrieval/query_student.py",
    # Teacher TE1 (spec_teacher_v1 §12.1, §12.2, §18.4): the learned lesson-check weight's,
    # the forecast pool's and the tap/hedge recalibration's seeded priors (each labelled with its
    # basis and width), the numerical resolution of their search, and the lesson's budgets and
    # its one contract guardrail. No weight, margin or threshold is a hand-set constant.
    "lesson_weight": "src/learnloop/learner/lesson_weight.py",
    "teacher_brief": "src/learnloop/teacher/brief.py",
    "teacher_service": "src/learnloop/teacher/service.py",
    "teacher_actions": "src/learnloop/teacher/actions.py",
    # Teacher TE1b (spec_teacher_v1 §15.1, §18.4): the acceptance model's and the decline
    # recovery's seeded priors (basis legacy, labelled), the card's presentation bounds.
    "lesson_suggestions": "src/learnloop/router/lesson_suggestions.py",
    # Data capture (docs/reviews/data-capture-a1-a6.md): no decision parameter of its own. The delay is
    # the outcome contract's, the floor the router's, the pitch and dates the teacher's.
    "data_capture_prefilter": "src/learnloop/data_capture/prefilter.py",
    # Router objective RO0 (spec_router_objective_v1 §4): logging, no decision parameter of its own.
    "router_objective_decision_state": "src/learnloop/router_objective/decision_state.py",
    "router_objective_question_state": "src/learnloop/router_objective/question_state.py",
    "followup_run_jobs": "src/learnloop/followup_run/jobs.py",
    "delayed_checks": "src/learnloop/delayed_checks.py",
    # Router objective RO2 (spec_router_objective_v1 §6): the full-history forecaster, its card, its
    # resolver, its audit and its report (receipts and reports only; nothing serving reads them).
    "ad_history_card": "src/learnloop/adaptive_difficulty/history_card.py",
    "ad_history_forecast": "src/learnloop/adaptive_difficulty/history_forecast.py",
    "ad_history_resolve": "src/learnloop/adaptive_difficulty/history_resolve.py",
    "ad_history_audit": "src/learnloop/adaptive_difficulty/history_audit.py",
    "ad_scoring": "src/learnloop/adaptive_difficulty/scoring.py",
    # Router objective RO4 (spec_router_objective_v1 §8): the value estimator, its memory model, the
    # attention price and the weight's posterior. Every number is a labelled seed, a keep bound or numerical.
    "router_objective_memory": "src/learnloop/router_objective/memory.py",
    "router_objective_value": "src/learnloop/router_objective/value.py",
    "router_objective_price": "src/learnloop/router_objective/price.py",
    "router_objective_weight": "src/learnloop/router_objective/weight.py",
    # Router objective RO5 (spec_router_objective_v1 §9): the stop coin and κ0's posterior, the randomized checks,
    # their scores, the goal-date read and the open picks. The arms' rates are config keys (declared prices for
    # information); the modules' numbers are labelled seeds or numerical resolution.
    "router_objective_stop_coin": "src/learnloop/router_objective/stop_coin.py",
    "router_objective_checks": "src/learnloop/router_objective/checks.py",
    "router_objective_scores": "src/learnloop/router_objective/scores.py",
    "router_objective_goal_read": "src/learnloop/router_objective/goal_read.py",
    "router_objective_picks": "src/learnloop/router_objective/picks.py",
    # Router objective RO6 (spec_router_objective_v1 §10): the learned tail (pure fit and weight, its data reads,
    # its serving step and its report). Its priors are config keys; the modules' numbers are numerical resolution.
    "router_objective_learned_tail": "src/learnloop/router_objective/learned_tail.py",
    "router_objective_tail_data": "src/learnloop/router_objective/tail_data.py",
    "router_objective_tail_serve": "src/learnloop/router_objective/tail_serve.py",
    "router_objective_tail_report": "src/learnloop/router_objective/tail_report.py",
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


# The leakage gate (ING M8, and FG1 §8's reserved-question check). Both keep.
_reg_const("practice_leakage:DEFAULT_SHINGLE_N", "constraint", kind="structural", owner="practice_leakage",
           rationale="keep: a protection bound, not a learner-model weight. Six contiguous words is the ingest gate's "
                     "existing order. A false match costs one question on one miss, a miss a leaked exam question, so "
                     "it errs short. Leave-one-out on one real vault: 21 of 84 ordinary items would match at 6, 6 at 8, "
                     "2 at 10, 0 at 12.")
_reg_const("practice_leakage:_SPAN_TEXT_CAP", "constraint", kind="structural", owner="practice_leakage",
           rationale="keep: a context budget for a cited span; the gate reads the inventory, not these snippets.")
_reg_const("practice_leakage:_SEMANTIC_RELATION_PRIORITY", "version", kind="structural", owner="practice_leakage",
           rationale="keep: an ordering of the source-link relations, an identity and not a weight.")

# Local contextual retrieval P1 module constants (all keep: identities, guardrails, budgets).
_reg_const("local_pins:MODEL_DIMENSIONS", "version", kind="structural", owner="local_pins",
           rationale="keep: the pinned model's output width (identity: a change is a new space).")
_reg_const("local_pins:DOWNLOAD_FREE_DISK_GIB", "constraint", kind="structural", owner="local_pins",
           rationale="keep: disk guardrail for the owner-run 33.6 GB download (files plus partial copies).")
_reg_const("local_pins:MIN_HOST_AVAILABLE_GIB", "operational", kind="structural", owner="local_pins",
           rationale="keep: memory floor the 9B worker needs to start (E1 measured; oomd killed the owner's terminal three times).")
_reg_const("local_pins:MIN_FREE_VRAM_GIB", "operational", kind="structural", owner="local_pins",
           rationale="keep: free-VRAM floor the 9B worker needs to start (E1 measured 18.4 GB reserved at peak).")
_reg_const("local_pins:MAX_OTHER_GPU_PROCESS_MIB", "operational", kind="structural", owner="local_pins",
           rationale="keep: the workload rule (owner, 2026-10-23): the owner's desktop GPU use comes first.")
_reg_const("local_pins:MAX_OTHER_GPU_TOTAL_MIB", "operational", kind="structural", owner="local_pins",
           rationale="keep: the workload rule (owner, 2026-10-23): the owner's desktop GPU use comes first.")
_reg_const("local_pins:MAX_GPU_UTILIZATION_PCT", "operational", kind="structural", owner="local_pins",
           rationale="keep: the workload rule (owner, 2026-10-23): no load while the GPU is busy.")
_reg_const("local_pins:HOST_FLOOR_GIB", "operational", kind="structural", owner="local_pins",
           rationale="keep: runtime abort floor protecting the owner's session inside the scope's limit.")
_reg_const("local_pins:DEVICE_PEAK_TARGET_GIB", "operational", kind="structural", owner="local_pins",
           rationale="keep: runtime abort above the 20 GiB device target on the shared GPU.")
_reg_const("local_pins:SAMPLE_INTERVAL_S", "operational", kind="structural", owner="local_pins",
           rationale="keep: the worker sampler's period (operational).")
_reg_const("local_pins:HEARTBEAT_GRACE_S", "version", kind="structural", owner="local_pins",
           rationale="keep: how long a silent worker is still charged to the GPU meter (operational).")
_reg_const("local_pins:KILL_GRACE_S", "operational", kind="structural", owner="local_pins",
           rationale="keep: SIGTERM-to-SIGKILL grace for the worker the caller started (operational).")
_reg_const("local_pins:MAX_DOCUMENT_TOKENS", "version", kind="structural", owner="local_pins",
           rationale="keep: the longest window the worker encodes, by the model's own count; never a truncation.")
_reg_const("local_pins:INDEX_BATCH_SIZE", "version", kind="structural", owner="local_pins",
           rationale="keep: one window per forward pass (padding never enters the index; identity).")
_reg_const("local_pins:QUERY_BATCH_SIZE", "version", kind="structural", owner="local_pins",
           rationale="keep: one query per forward pass (identity).")
_reg_const("local_pins:BATCH_INVARIANCE_MIN_COS", "version", kind="structural", owner="local_pins",
           rationale="keep: smoke check: padding and batch invariance (E1 measured 0.99991); an identity check, not quality.")
_reg_const("local_pins:CONTEXT_SENSITIVITY_MAX_COS", "version", kind="structural", owner="local_pins",
           rationale="keep: smoke check: a chunk in two contexts must differ (the model is contextual); identity.")
_reg_const("local_pins:CANARY_MIN_COS", "version", kind="structural", owner="local_pins",
           rationale="keep: canary identity check (E1 measured invariance at 0.99991): below it the computation changed (epoch drift).")
_reg_const("local_pins:PROFILE_TOKENS", "version", kind="structural", owner="local_pins",
           rationale="keep: P0 profiling sizes (2k/4k/8k), measurement points, not decisions.")
_reg_const("local_pins:PROFILE_REPEATS", "version", kind="structural", owner="local_pins",
           rationale="keep: repeats per profiling size (measurement).")
_reg_const("local_fusion:NEWTON_STEPS", "numerical", kind="structural", owner="local_fusion",
           rationale="keep: the MAP fit's iteration ceiling (numerical, not a model parameter).")
_reg_const("local_fusion:NEWTON_TOLERANCE", "numerical", kind="structural", owner="local_fusion",
           rationale="keep: the MAP fit's convergence tolerance (numerical).")
_reg_const("local_fusion:PROPENSITY_DRAWS", "numerical", kind="structural", owner="local_fusion",
           rationale="keep: Monte Carlo draws behind an explored delivery's propensities (a computation budget).")
_reg_const("local_fusion:RRF_K_GRID", "numerical", kind="structural", owner="local_fusion",
           rationale="keep: octave grid around the seeded rrf_k searched by marginal likelihood (resolution of the search, not a weight).")
_reg_const("source_windows:WINDOW_TOKENS", "version", kind="structural", owner="source_windows",
           rationale="keep: the window rule's identity (w4096-section-policy-v1; E0's corpus rule): a change is a new space.")
_reg_const("source_windows:CHUNK_MARKER_TOKENS", "version", kind="structural", owner="source_windows",
           rationale="keep: tokens counted per chunk marker inside a window (the window rule's identity).")
_reg_const("source_windows:MAX_DOCUMENT_TOKENS", "version", kind="structural", owner="source_windows",
           rationale="keep: the worker's own per-document bound (identity); every window stays under WINDOW_TOKENS.")
_reg_const("source_windows:PART_TOKENS", "version", kind="structural", owner="source_windows",
           rationale="keep: structural, WINDOW_TOKENS minus one chunk marker: the most text one part of a split block holds, so every window holds the bound (Codex review F15).")
_reg_const("local_fusion:MIN_PROPENSITY", "numerical", kind="structural", owner="local_fusion",
           rationale="keep: the smallest propensity an inverse-propensity weight divides by (a numerical floor, not a weight).")
_reg_const("local_fusion:SELECTION_DRAWS", "numerical", kind="structural", owner="local_fusion",
           rationale="keep: Monte Carlo draws behind a query's joint selection probability (a computation budget; standard error under 0.008, Codex re-review F18).")
_reg_const("fallback_space:MAX_RETRIES", "operational", kind="structural", owner="fallback_space",
           rationale="keep: retries a capped fallback backfill reserves room for (the Qwen backfill's); spend stays under max_cost_usd_per_run.")
_reg_const("local_index:PROFILE_POOL_FACTOR", "operational", kind="structural", owner="local_index",
           rationale="keep: the P0 profile pool's estimated size per target (E1 measured 0.68 model tokens per estimated token); the worker fits the true size by its own count, so this only guarantees enough text.")
_reg_const("retrieval_feedback:REFIT_EVERY_HOURS", "operational", kind="structural", owner="retrieval_feedback",
           rationale="keep: spec §9.2's nightly refit cadence (plus one at the host's start, only when receipts arrived); when the posterior is refreshed, never what it says.")
_reg_const("voyage_contextual:MAX_INPUTS_PER_REQUEST", "constraint", kind="structural", owner="voyage_contextual",
           rationale="keep: Voyage's documented inputs per request (provider limit).")
_reg_const("voyage_contextual:MAX_CHUNKS_PER_REQUEST", "constraint", kind="structural", owner="voyage_contextual",
           rationale="keep: Voyage's documented chunks per request (provider limit).")

# Teacher TE1 module constants (spec_teacher_v1 §18.4: every number a seeded prior, a structural
# form or keep). The priors are lp_priors_v1's; the data move them.
_reg_const("lesson_weight:ETA0_PRIOR_MEAN", "prior", owner="lesson_weight",
           rationale="seeded prior, basis legacy: logit of the type's configured 0.5 (config evidence masses); "
                     "the lesson-check mass's centre before any later cold outcome.")
_reg_const("lesson_weight:ETA0_PRIOR_SD", "prior", owner="lesson_weight",
           rationale="seeded prior width, basis legacy: the LP spec's rule for legacy priors (>= 1 logit).")
_reg_const("lesson_weight:BETA_C_PRIOR_SD", "prior", owner="lesson_weight",
           rationale="seeded prior width, basis simulation: the narrowest under which a planted +-0.5-logit "
                     "confidence effect is still recovered; centre 0 (no effect).")
_reg_const("lesson_weight:BETA_P_PRIOR_SD", "prior", owner="lesson_weight",
           rationale="seeded prior width, basis simulation (as beta_c), for the predicted-success effect.")
_reg_const("lesson_weight:TAU_GRID", "prior", owner="lesson_weight",
           rationale="the per-LO offset scale's grid support, basis simulation (the planted-recovery suite tells "
                     "the points apart); its weights start uniform and are learned (AD's ad_hyper mechanism).")
_reg_const("lesson_weight:TAP_PRIOR_MAP", "prior", owner="lesson_weight",
           rationale="today's fixed tap -> probability map {1: .10 ... 5: .90}, the recalibration's legacy-seeded "
                     "centre (goals.exam_calibration's map; a test pins them equal).")
_reg_const("lesson_weight:PRIOR_TERMS", "version", kind="structural", owner="lesson_weight",
           rationale="keep: the state vector's index of each prior term (identity; the report's sensitivity rerun "
                     "shifts these).")
_reg_const("lesson_weight:POOL_GRID_POINTS", "numerical", kind="structural", owner="lesson_weight",
           rationale="keep: the pool weight's grid resolution (numerical resolution, spec §18.4).")
_reg_const("lesson_weight:POOL_PRIOR_ALPHA", "prior", owner="lesson_weight",
           rationale="Beta(1, 4) over the pool weight, basis legacy (owner: the parametric weight starts ahead).")
_reg_const("lesson_weight:POOL_PRIOR_BETA", "prior", owner="lesson_weight",
           rationale="Beta(1, 4) over the pool weight, basis legacy (owner: the parametric weight starts ahead).")
_reg_const("lesson_weight:TAP_INTERCEPT_PRIOR", "prior", owner="lesson_weight",
           rationale="the tap recalibration's intercept N(0, 1), basis legacy (>= 1 logit around today's map).")
_reg_const("lesson_weight:TAP_SLOPE_PRIOR", "prior", owner="lesson_weight",
           rationale="the tap recalibration's slope N(1, 1), basis legacy (centred on today's fixed map).")
_reg_const("lesson_weight:HEDGE_INTERCEPT_PRIOR", "prior", owner="lesson_weight",
           rationale="each hedge value's intercept N(0, 1): centre chance (no information), >= 1 logit wide.")
_reg_const("lesson_weight:_IMPLIED_ETA_BOUND", "numerical", kind="structural", owner="lesson_weight",
           rationale="keep: the pool-implied mass's search interval on the logit scale (numerical resolution: "
                     "sigma(+-12) is within 1e-5 of the link's bounds).")
_reg_const("lesson_weight:_BISECTION_STEPS", "numerical", kind="structural", owner="lesson_weight",
           rationale="keep: bisection steps of that search (numerical resolution).")
_reg_const("teacher_brief:STEM_CHARS", "display", kind="structural", owner="teacher_brief",
           rationale="keep: how much of a long prompt a brief header shows (a size bound; text comes through "
                     "the actions).")
_reg_const("teacher_brief:INTERVAL_Z", "display", kind="structural", owner="teacher_brief",
           rationale="keep: the conventional 95% interval shown with a prediction (display convention).")
_reg_const("teacher_service:MAX_CONTRACT_FAILURES", "constraint", kind="structural", owner="teacher_service",
           rationale="keep: three consecutive refused teacher turns close the lesson (contract guardrail, "
                     "spec §18.4).")
_reg_const("teacher_actions:_HISTORY_TEXT_CHARS", "display", kind="structural", owner="teacher_actions",
           rationale="keep: how much of one past answer or tutor reply read_history returns (a prompt-size bound).")

# Teacher TE1b module constants (spec_teacher_v1 §15.1, §18.4): seeded priors (basis legacy:
# revision 3's defaults, 1.0 logit per effect, the recovery rate on a grid), learned from every
# shown suggestion's response; presentation bounds kept.
_reg_const("followup_run_jobs:LEASE_SECONDS", "numerical", kind="structural", owner="followup_run_jobs",
           rationale="a generation job's lease: one structured model call with its checks; a lapsed lease is reclaimed.")
_reg_const("followup_run_jobs:MAX_GENERATION_ATTEMPTS", "numerical", kind="structural", owner="followup_run_jobs",
           rationale="FG1 spec §8: the structural bound on physical generation per workflow or need on a subscription route.")
_reg_const("followup_run_jobs:RETRY_BACKOFF_SECONDS", "numerical", kind="structural", owner="followup_run_jobs",
           rationale="the pause before the one retry after a transient provider failure; short against the learner's wait.")
_reg_const("followup_run_jobs:NEED_RETRY_DELAY_SECONDS", "numerical", kind="structural", owner="followup_run_jobs",
           rationale="a failed lane's background retry: what just failed would fail again if tried at once.")
_reg_const("data_capture_prefilter:_ROUND_DIGITS", "numerical", kind="structural", owner="data_capture_prefilter",
           rationale="decimal places of a priority or minutes in a prefilter receipt's inputs, so float "
           "noise does not defeat the content-addressed dedupe; receipt size only, never a decision.")
_reg_const("router_objective_decision_state:_ROUND_DIGITS", "numerical", kind="structural",
           owner="router_objective_decision_state",
           rationale="decimal places of a number in a decision's state receipt; receipt size only, never a decision.")
_reg_const("router_objective_question_state:_WORKED_LEVEL", "constraint", kind="structural",
           owner="router_objective_question_state",
           rationale="the help ladder's first worked level (levels 4 and 5 give the solution away, hints.writer): what "
           "the disclosure receipt calls a worked solution. Read by nothing that decides.")
# Router objective RO2 (spec_router_objective_v1 §6): llm_history_v1 writes receipts only (A2, A12); its
# bounds are `keep` (work, prompt and spend bounds, never a judgement), its lags measurement points, its
# calibration prior seeded and labelled (the audit's prior sweep reports its strength).
_reg_const("ad_history_card:ROW_LIMITS", "operational", kind="structural", owner="ad_history_card",
           rationale="keep: each bounded read's row limit before any trimming, so the serve transaction's work is "
           "bounded (spec 6.3); a work bound, never a judgement; the card says which reads reached it.")
_reg_const("ad_history_card:ANCESTRY_ROUNDS", "operational", kind="structural", owner="ad_history_card",
           rationale="keep (Codex re-review F8): the most reads up the inquiry branch links in one serve, sharing "
           "the exchanges row budget, so a long thread's work is bounded; past it the root and status are "
           "unknown and the card says so (inquiry_ancestry). A work bound, never a judgement.")
_reg_const("ad_history_card:ANSWER_TEXT_LIMIT", "operational", kind="structural", owner="ad_history_card",
           rationale="keep: one whole answer's text bound on the card (prompt size), never a judgement.")
_reg_const("ad_history_card:TEXT_LIMIT", "operational", kind="structural", owner="ad_history_card",
           rationale="keep: one help text's, question's or digest's bound on the card (prompt size).")
_reg_const("ad_history_card:GAP_TEXT_LIMIT", "operational", kind="structural", owner="ad_history_card",
           rationale="keep: one named gap's learner text bound on the card (prompt size).")
_reg_const("ad_history_forecast:LAGS", "constraint", kind="structural", owner="ad_history_forecast",
           rationale="keep (spec 6.2): the cold forecast's measurement points in days after the block; nothing "
           "weights them; past the last an outcome is censored beyond_measured_lag.")
_reg_const("ad_history_forecast:RATIONALE_SENTENCES", "display", kind="structural", owner="ad_history_forecast",
           rationale="keep (spec 6.2): at most three sentences of rationale, unvalidated and trace-only.")
_reg_const("ad_history_resolve:MAX_LAG_DAYS", "constraint", kind="structural", owner="ad_history_resolve",
           rationale="structural: the forecaster's last lag (LAGS); past it an outcome is censored "
           "beyond_measured_lag until a longer lag is added (spec 6.2).")
_reg_const("ad_history_audit:PRIOR_SCALES", "numerical", kind="structural", owner="ad_history_audit",
           rationale="keep: the prior-strength sweep's grid (multiples of the seeded prior's sd, report T8): "
           "a sensitivity read, never applied to anything.")
_reg_const("ad_scoring:CLIP", "numerical", kind="structural", owner="ad_scoring",
           rationale="numerical: the log loss's probability clip, so a 0 or 1 forecast scores finitely.")
_reg_const("ad_scoring:FIT_TOLERANCE", "numerical", kind="structural", owner="ad_scoring",
           rationale="numerical: the calibration fit converges when the log posterior's gradient is below it "
           "(Codex review F2); an unconverged fit states no slope.")
_reg_const("ad_scoring:FIT_ITERATIONS", "numerical", kind="structural", owner="ad_scoring",
           rationale="numerical: the damped Newton fit's work bound; past it an unconverged fit is reported as such.")
_reg_const("ad_scoring:FIT_ARMIJO", "numerical", kind="structural", owner="ad_scoring",
           rationale="numerical: the backtracking line search's sufficient-increase share (Armijo's textbook "
           "1e-4), so every step raises the log posterior.")
_reg_const("ad_scoring:SLOPE_PRIOR", "prior", owner="ad_scoring",
           rationale="seeded prior, basis a calibrated forecaster (intercept 0, slope 1 on the log-odds), each "
           "with its sd: a model and prompt version's calibration slope shrinks to the population's posterior "
           "(hierarchical); reports only; the forecast audit's prior sweep reports its strength (spec 6.4).")
_reg_const("delayed_checks:_EXACT_TIE", "numerical", kind="structural", owner="delayed_checks",
           rationale="floating-point resolution of an exact tie between two items' predicted success; "
           "numerical resolution, not a margin: a real difference is never a tie.")
_reg_const("lesson_suggestions:LEGACY_DAILY_SHOW", "prior", owner="lesson_suggestions",
           rationale="seeded prior, basis legacy (revision 3's about-one-suggestion-a-day): the acceptance "
                     "intercept's centre, logit(0.9), so with no data a card shows on about nine days in ten; "
                     "the responses move it.")
_reg_const("lesson_suggestions:LEGACY_DECLINED_SHOW", "prior", owner="lesson_suggestions",
           rationale="seeded prior, basis legacy (revision 3's Not-now mute): a goal just declined starts at about "
                     "one chance in a hundred (the decline depth D's centre, logit(0.9) - logit(0.01)); "
                     "re-acceptance after a decline moves it.")
_reg_const("lesson_suggestions:LEGACY_CADENCE_DAYS", "prior", owner="lesson_suggestions",
           rationale="seeded prior, basis legacy (revision 3's about-one-suggestion-a-day): the gap at which the "
                     "days-since-last-suggestion feature 1/(1+c) - 1/(1+d) is 0, so the seeded centres are the "
                     "one-a-day context's; its learned coefficient (prior N(0, 1)) sets how acceptance moves with "
                     "the gap (codex review F7).")
_reg_const("lesson_suggestions:PRIOR_SD", "prior", owner="lesson_suggestions",
           rationale="seeded prior width, basis legacy: 1.0 logit on every effect (spec §18.4; the LP spec's rule "
                     "for legacy priors), centre 0 (no effect) for every context effect.")
_reg_const("lesson_suggestions:RECOVERY_DAYS_GRID", "prior", owner="lesson_suggestions",
           rationale="the per-learner recovery rate's grid support, basis legacy: centred on revision 3's 7-day mute, "
                     "a factor of two either side at half-octave steps; its weights start uniform and are learned "
                     "(AD's ad_hyper mechanism).")
_reg_const("lesson_suggestions:CARD_MINUTES", "display", kind="structural", owner="lesson_suggestions",
           rationale="keep: the card's 'about 15 min' (spec §19 copy; presentation, not a model of the learner).")
_reg_const("lesson_suggestions:MAX_ALTERNATIVES", "display", kind="structural", owner="lesson_suggestions",
           rationale="keep: up to two alternatives on the suggestion card (spec §18.4: presentation).")
_reg_const("lesson_suggestions:_SECONDS_PER_DAY", "numerical", kind="structural", owner="lesson_suggestions",
           rationale="keep: a unit conversion (seconds in a day).")

# Local contextual retrieval P2 module constants (identities, guardrails, budgets, optimizer settings;
# no quality margin or ranking weight: those are expected-utility decisions and learned fusion weights).
_reg_const("student_pins:STUDENT_DIMENSIONS", "version", kind="structural", owner="student_pins",
           rationale="keep: the student's output width, the teacher space's (identity).")
_reg_const("student_pins:BUDGETS", "version", kind="structural", owner="student_pins",
           rationale='keep: the nested learning-curve budgets 2k/10k/50k (spec §7.1): the data points the curve reads, not a decision.')
_reg_const("student_pins:QUERIES_PER_PASSAGE_MIN", "operational", kind="structural", owner="student_pins",
           rationale='keep: questions asked per passage (spec §7.1, 8-12): a generation request size.')
_reg_const("student_pins:QUERIES_PER_PASSAGE_MAX", "operational", kind="structural", owner="student_pins",
           rationale='keep: questions kept per passage at most (spec §7.1, 8-12).')
_reg_const("student_pins:PASSAGES_PER_CALL", "operational", kind="structural", owner="student_pins",
           rationale='keep: passages per generator call (prompt size, operational).')
_reg_const("student_pins:PASSAGE_TOKENS", "operational", kind="structural", owner="student_pins",
           rationale='keep: estimated tokens of permitted text one passage carries at most (prompt size).')
_reg_const("student_pins:TEACHER_TOP_K", "version", kind="structural", owner="student_pins",
           rationale="keep: the teacher's top-k kept per query for the ranking losses (spec §7.1: top-50).")
_reg_const("student_pins:MAX_QUERY_TOKENS", "version", kind="structural", owner="student_pins",
           rationale="keep: the longest training or serving query in the base's tokens (spec §7.1).")
_reg_const("student_pins:LEAKAGE_MAX_TEACHER_COS", "constraint", kind="structural", owner="student_pins",
           rationale='keep: leakage guard (spec §9.6: protecting the evaluation is a rule, not a trade-off; may only tighten).')
_reg_const("student_pins:LEAKAGE_MAX_5GRAM_OVERLAP", "constraint", kind="structural", owner="student_pins",
           rationale='keep: leakage guard (spec §9.6; may only tighten).')
_reg_const("student_pins:LEAKAGE_NGRAM", "constraint", kind="structural", owner="student_pins",
           rationale='keep: the n of the n-gram leakage guard (spec §7.1: 5-grams).')
_reg_const("student_pins:EPOCHS", "numerical", kind="structural", owner="student_pins",
           rationale='keep: epochs per run (spec §7.1: 3); how a run descends, not what it decides.')
_reg_const("student_pins:FINAL_SEEDS", "version", kind="structural", owner="student_pins",
           rationale='keep: the chosen recipe runs on at least three seeds (spec §7.1).')
_reg_const("student_pins:LEARNING_RATE_FULL", "numerical", kind="structural", owner="student_pins",
           rationale='numerical (optimizer): published BERT-scale fine-tuning rate (Devlin et al. 2019); how a run descends, never a decision.')
_reg_const("student_pins:LEARNING_RATE_HEAD", "numerical", kind="structural", owner="student_pins",
           rationale='numerical (optimizer): the usual Adam rate for a linear map (Kingma and Ba 2015).')
_reg_const("student_pins:WEIGHT_DECAY", "numerical", kind="structural", owner="student_pins",
           rationale="numerical (optimizer): AdamW's customary decoupled decay.")
_reg_const("student_pins:WARMUP_FRACTION", "numerical", kind="structural", owner="student_pins",
           rationale='numerical (optimizer): linear warm-up share of the steps.')
_reg_const("student_pins:GRAD_CLIP_NORM", "numerical", kind="structural", owner="student_pins",
           rationale='numerical (optimizer): gradient-norm clip, a stability bound.')
_reg_const("student_pins:TRAIN_BATCH_SIZE", "numerical", kind="structural", owner="student_pins",
           rationale='numerical (throughput): queries per optimizer step.')
_reg_const("student_pins:AGREEMENT_K", "version", kind="structural", owner="student_pins",
           rationale='keep: the depth of the teacher-agreement diagnostic (spec §9.3: top-10 recall).')
_reg_const("student_pins:LATENCY_PROBES", "operational", kind="structural", owner="student_pins",
           rationale='keep (measurement): queries timed per device for the latency diagnostic.')
_reg_const("student_pins:P2_GPU_HOURS_CAP", "constraint", kind="structural", owner="student_pins",
           rationale="keep: P2's whole GPU budget (spec §7.1, §9.6: <= 6 GPU-hours); a budget, not a quality trade-off.")
_reg_const("student_pins:SERVE_MIN_HOST_AVAILABLE_GIB", "operational", kind="structural", owner="student_pins",
           rationale="keep: the query process's host memory floor (spec §7.2: MemAvailable >= 6 GiB).")
_reg_const("student_pins:SERVE_MIN_FREE_VRAM_GIB", "operational", kind="structural", owner="student_pins",
           rationale='keep: the free VRAM the query process needs to choose the GPU (spec §7.1, Q10: >= 4 GiB).')
_reg_const("student_pins:REPLAY_MAX_QUERIES", "constraint", kind="structural", owner="student_pins",
           rationale="keep: the GPU budget of one nightly teacher replay (2,000 at E1's 18 ms is ~36 s of a loaded model).")
_reg_const("student_pins:REPLAY_EVERY_HOURS", "operational", kind="structural", owner="student_pins",
           rationale='keep: a replay-only 9B batch at most nightly (spec §9.2-§9.3 cadence).')
_reg_const("student_pins:START_TIMES_KEPT", "operational", kind="structural", owner="student_pins",
           rationale='keep: the measured cold starts the start-time distribution keeps (recency window).')
_reg_const("student_pins:STUDENT_CANARY_MIN_COS", "version", kind="structural", owner="student_pins",
           rationale="keep: the student canary identity check (as the 9B's, E1 measured invariance at 0.99991).")
_reg_const("student_pins:SOCKET_TIMEOUT_S", "operational", kind="structural", owner="student_pins",
           rationale="keep: the query process's socket timeout (operational).")
_reg_const("student_pins:YIELD_WAIT_S", "operational", kind="structural", owner="student_pins",
           rationale="keep (operational, Codex review F11): the wait for a GPU-resident query process to exit before an exclusive GPU job's start checks.")
_reg_const("student_decision:DRAWS", "numerical", kind="structural", owner="student_decision",
           rationale='keep (computation budget): posterior draws behind every expected utility (MC s.e. of P(best) < 0.008).')
_reg_const("student_decision:RATE_GRID_POINTS", "numerical", kind="structural", owner="student_decision",
           rationale="keep (numerical): resolution of an exchange-rate posterior's log grid.")
_reg_const("student_decision:RATE_GRID_SPAN_SD", "numerical", kind="structural", owner="student_decision",
           rationale='structural: the log grid spans six prior sds each side (resolution of the search, not a weight).')
_reg_const("student_data:DEV_SHARE_DENOMINATOR", "operational", kind="structural", owner="student_data",
           rationale='keep (measurement split): one passage in ten of the training families is development.')
_reg_const("student_data:MAX_QUESTION_CHARS", "constraint", kind="structural", owner="student_data",
           rationale='keep: the longest generated question accepted (a validation bound).')
_reg_const("student_data:MAX_RETRIES_PER_CALL", "operational", kind="structural", owner="student_data",
           rationale='keep: retries one generator call may use (a failed answer is a new admitted attempt).')
_reg_const("student_data:OUTPUT_TOKENS", "operational", kind="structural", owner="student_data",
           rationale="keep: the generator answer's output budget (prompt size).")
_reg_const("query_student:SHARD_SIZE", "operational", kind="structural", owner="query_student",
           rationale='keep: teacher target rows per int8 shard (an aborted run keeps every finished shard).')
_reg_const("query_student:DEV_MAX", "operational", kind="structural", owner="query_student",
           rationale='keep (measurement): development questions one run is measured on at most.')
_reg_const("query_student:MIN_TEMPERATURE", "numerical", kind="structural", owner="query_student",
           rationale='keep (numerical): the smallest temperature a degenerate development set may yield.')
_reg_const("voyage_contextual:MAX_TOKENS_PER_REQUEST", "constraint", kind="structural", owner="voyage_contextual",
           rationale="keep: Voyage's documented tokens per request (provider limit).")
_reg_const("voyage_contextual:MAX_TOKENS_PER_DOCUMENT", "constraint", kind="structural", owner="voyage_contextual",
           rationale="keep: Voyage's documented tokens per chunk (provider limit).")
_reg_const("voyage_contextual:REQUEST_TIMEOUT_S", "constraint", kind="structural", owner="voyage_contextual",
           rationale="keep: one request's timeout when no retrieval time box applies (operational).")

# Reader RW5d P1 (Codex review F9): the one new module constant (keep).
_reg_const("figure_admission:GROUNDING_PASSAGES", "constraint", kind="structural", owner="figure_admission",
           rationale="keep: prompt size (spec_reader_show_me_figures_v1 §8.3, §15, owner-approved): at most three "
                     "passages ground a figure goal (retrieved, or a tutor answer's cited ones); more dilute the "
                     "author's context. A bound on what is sent, never a weight, margin or threshold.")

# Reader RW5d P3: figures as a help kind (all keep: a structural ladder level and a read bound).
_reg_const("figure_help:FIGURE_LEVEL", "version", kind="structural", owner="figure_help",
           rationale="keep: identity: the hints spec's ladder level 2 a figure's help row is written at (one "
                     "hint-equivalent in the fold, the level of explore_figure, spec §11.2, §11.4).")
_reg_const("figure_help:QUALIFYING_SCAN", "operational", kind="structural", owner="figure_help",
           rationale="keep: read size: the newest shown figures the chooser's precondition scans (a bound on a "
                     "local read, never a weight, margin or threshold).")

# Learner data-relax 2: the figure author's learner state (all keep: prompt and read size).
_reg_const("figure_learner_state:MAX_TOPICS", "constraint", kind="structural", owner="figure_learner_state",
           rationale="keep: prompt size: the passage's topics described to the figure author (an anchor names one "
                     "or two). A bound on what is sent, never a weight, margin or threshold.")
_reg_const("figure_learner_state:MAX_STATEMENTS", "constraint", kind="structural", owner="figure_learner_state",
           rationale="keep: prompt size: open misconception and gap statements sent, newest first.")
_reg_const("figure_learner_state:STATEMENT_CHARS", "constraint", kind="structural", owner="figure_learner_state",
           rationale="keep: prompt size: one statement's characters (library_ask's open-question bound).")
_reg_const("figure_learner_state:RECENT_ANSWERS", "constraint", kind="structural", owner="figure_learner_state",
           rationale="keep: the owner's bound for learner data-relax 2: at most two recent answer excerpts on the "
                     "passage's topics.")
_reg_const("figure_learner_state:ANSWER_CHARS", "constraint", kind="structural", owner="figure_learner_state",
           rationale="keep: prompt size: one answer excerpt's characters.")
_reg_const("figure_learner_state:QUESTION_CHARS", "constraint", kind="structural", owner="figure_learner_state",
           rationale="keep: prompt size: one graded question's characters.")
_reg_const("figure_learner_state:ATTEMPTS_SCANNED", "operational", kind="structural", owner="figure_learner_state",
           rationale="keep: read size: the newest attempts on the topics scanned for two unprotected answers.")

# Reader RW5d P5 (spec §10b.3, §15): the prefetch decision model's priors, each with LP §2's
# treatment (learn), prior_basis and prior_scale in its rationale; outside the learner model (SM8).
_reg_const("figure_prefetch_model:ALPHA_PRIOR_MEAN", "prior", owner="figure_prefetch_model",
           rationale="treatment learn, prior_basis llm_content, prior_scale 1 (with ALPHA_PRIOR_SD): the judge-"
                     "trust slope's centre is the identity map (believe the judge's stated probability until "
                     "opens say otherwise); moved by assumed-density filtering on closed, built decisions.")
_reg_const("figure_prefetch_model:ALPHA_PRIOR_SD", "prior", owner="figure_prefetch_model",
           rationale="treatment learn, prior_basis llm_content: the slope's prior width, 1 (spec §10b.3).")
_reg_const("figure_prefetch_model:KIND_PRIOR_MEAN", "prior", owner="figure_prefetch_model",
           rationale="treatment learn, prior_basis legacy (debt, LP §3.3): beta_kind's shared level centred at 0 "
                     "logits; no population data exist.")
_reg_const("figure_prefetch_model:KIND_PRIOR_SD", "prior", owner="figure_prefetch_model",
           rationale="treatment learn, prior_basis legacy (debt): LP §3.0's widest un-sourced prior, 1.5 logits "
                     "(spec §10b.3).")
_reg_const("figure_prefetch_model:POOLING_GRID", "prior", owner="figure_prefetch_model",
           rationale="structural form: the a-priori grid (uniform) of the pooling scales of beta_kind's "
                     "per-trigger deviations and beta_src's per-source offsets; the scale is a posterior over it "
                     "(AD's ad_hyper_v1 mechanism), so the grid is the search's resolution, not a weight.")
_reg_const("figure_prefetch_model:PAUSE_INTERCEPT_PRIOR_MEAN", "prior", owner="figure_prefetch_model",
           rationale="treatment learn, prior_basis legacy (debt): the plan pause-risk logistic's intercept centre, "
                     "-3 logits (spec §10b.3); learned from plan_usage_pauses and the days' plan loads.")
_reg_const("figure_prefetch_model:PAUSE_INTERCEPT_PRIOR_SD", "prior", owner="figure_prefetch_model",
           rationale="treatment learn, prior_basis legacy (debt): the intercept's width, 2 logits (spec §10b.3).")
_reg_const("figure_prefetch_model:PAUSE_SLOPE_PRIOR_MEAN", "prior", owner="figure_prefetch_model",
           rationale="treatment learn, prior_basis legacy (debt): the slope per standardized unit of the day's plan "
                     "load, 1.5 logits (spec §10b.3).")
_reg_const("figure_prefetch_model:PAUSE_SLOPE_PRIOR_SD", "prior", owner="figure_prefetch_model",
           rationale="treatment learn, prior_basis legacy (debt): the slope's width, 2 logits (spec §10b.3).")
_reg_const("figure_prefetch_model:POSTERIOR_DRAWS", "numerical", kind="structural", owner="figure_prefetch_model",
           rationale="keep (numerical): the Monte Carlo resolution of the logged propensity (spec §15: 64 draws).")
_reg_const("figure_prefetch_model:P_CONTENT_CLIP", "numerical", kind="structural", owner="figure_prefetch_model",
           rationale="keep (numerical): the judge's stated 0 or 1 clipped before its logit so the feature stays "
                     "finite; resolution, not a weight.")
_reg_const("figure_prefetch:PREFETCH_SECTION_CANDIDATES", "constraint", kind="structural", owner="figure_prefetch",
           rationale="keep (spec §15: 3): the section judge's output size, one idea per block.")
_reg_const("figure_prefetch:PREFETCH_CONCURRENT_BUILDS", "operational", kind="structural", owner="figure_prefetch",
           rationale="keep (spec §15: 1): one background build at a time, given the oomd history.")
_reg_const("figure_prefetch:MAX_SECTION_BLOCKS", "constraint", kind="structural", owner="figure_prefetch",
           rationale="keep: the blocks of one section the judge reads (prompt bound).")
_reg_const("figure_prefetch:BLOCK_CHARS", "constraint", kind="structural", owner="figure_prefetch",
           rationale="keep: one block's text as the judge reads it (prompt bound).")
_reg_const("figure_prefetch:GAP_STATEMENT_CHARS", "constraint", kind="structural", owner="figure_prefetch",
           rationale="keep: a gap's statement as the gap judge reads it (prompt bound).")
_reg_const("figure_prefetch:PASSAGE_CHARS", "constraint", kind="structural", owner="figure_prefetch",
           rationale="keep: a gap's passage as the gap judge reads it (prompt bound).")
_reg_const("figure_prefetch:MAX_JUDGE_ATTEMPTS", "constraint", kind="structural", owner="figure_prefetch",
           rationale="keep (plan headroom): judge calls per section or gap; the second is told the first's "
                     "problems (rev 1's author cap carried over).")
_reg_const("figure_foreground:FOREGROUND_WAIT_SECONDS", "operational", kind="structural", owner="figure_foreground",
           rationale="keep (operational): how long background figure work (the prebuild queue, the judge, a "
                     "prebuild's rich job before its next request) waits for foreground work to end before it "
                     "leaves the rest for later; a pause length, never a decision.")
_reg_const("figure_prefetch:MAX_NODE_SPANS", "constraint", kind="structural", owner="figure_prefetch",
           rationale="keep: a lesson node's passages one prebuild anchors (inside the figure anchor's 40-span cap).")
_reg_const("figure_power:PROBE_TIMEOUT_SECONDS", "operational", kind="structural", owner="figure_power",
           rationale="keep (operational): how long a power-profile or pmset read may take before it counts as "
                     "unknown (fail closed: on battery).")
_reg_const("figure_power:PROBE_CACHE_SECONDS", "operational", kind="structural", owner="figure_power",
           rationale="keep (operational): how long one power-profile or pmset probe answers before it is started "
                     "again (follow-ups batch 6 C: a bound on process starts, not a model parameter); a Linux "
                     "power-supply change in sysfs drops it at once, and a failed probe still reads as on battery.")

# Reader RW5d P2: the sketch tier's module constants (all keep: caps, tolerances, sandbox limits, identities).
# Reader RW5d P2b: the rich tiers' module constants (all keep: caps, guardrails, sandbox limits).
_reg_const("figure_rich:RICH_BRIEF_MAX", "constraint", kind="structural", owner="figure_rich",
           rationale="keep: prompt size for the rich call (spec §15: 1,500 characters).")
_reg_const("figure_rich:MAX_RICH_ATTEMPTS", "constraint", kind="structural", owner="figure_rich",
           rationale="keep (money): rev 1's author cap carried to the rich call (spec §15: 2); the pacing repair "
                     "is the second attempt.")
_reg_const("figure_rich:PLAN_WAIT_RETRY_SECONDS", "operational", kind="structural", owner="figure_rich",
           rationale="keep (operational): how often a rich job waiting for the ChatGPT plan is asked again while "
                     "the learner reads (one cheap failed plan request at most per interval; never an offer).")
_reg_const("figure_manim:MAX_FUNCTIONS", "constraint", kind="structural", owner="figure_manim",
           rationale="keep (operational): declared functions per Manim figure (check work, check lines).")
_reg_const("figure_manim:MAX_FUNCTION_ARGS", "constraint", kind="structural", owner="figure_manim",
           rationale="keep (operational): checked arguments per declared function (3 grid values each: at most "
                     "81 points, rev 1's grid).")
_reg_const("figure_manim:MAX_FIGURE_CLAIMS", "constraint", kind="structural", owner="figure_manim",
           rationale="keep (operational): claims per Manim figure.")
_reg_const("figure_manim:MAX_PLOTTED", "constraint", kind="structural", owner="figure_manim",
           rationale="keep (operational): plotted_from entries per Manim figure.")
_reg_const("figure_manim:MAX_TITLE", "constraint", kind="structural", owner="figure_manim",
           rationale="keep (display): a Manim figure's title length.")
_reg_const("figure_manim:MAX_NARRATION", "constraint", kind="structural", owner="figure_manim",
           rationale="keep (display): the narration (the video's transcript) length.")
_reg_const("figure_manim:FUNCTION_CHECK_SECONDS", "operational", kind="structural", owner="figure_manim",
           rationale="keep (machine safety): the declared-function check's sandbox CPU and wall clock.")
_reg_const("figure_manim:FUNCTION_CHECK_MEMORY_MB", "operational", kind="structural", owner="figure_manim",
           rationale="keep (machine safety): the declared-function check's address-space cap in the sandbox.")
_reg_const("figure_labels:MIN_SEGMENT_WORDS", "constraint", kind="structural", owner="figure_labels",
           rationale="keep (wording rule, spec §9b.4): the shortest segment of a code-owned label matched on its "
                     "own. Two words ('not checked') are ordinary prose; three name a label's claim ('not checked "
                     "against the book'). A structural bound on what reads as a label, never a learner-model "
                     "weight, margin or threshold.")
_reg_const("concept_animation:_STDERR_TAIL_CHARS", "operational", kind="structural", owner="concept_animation",
           rationale="keep (operational): how much of a failed render's stderr is kept for the repair round-trip "
                     "and the failure view.")
_reg_const("concept_animation:_PACING_OVER_SLACK_SECONDS", "operational", kind="structural",
           owner="concept_animation",
           rationale="keep (display): seconds over the pacing band's maximum the static pacing lint tolerates "
                     "(a rough estimate catching a 3-second explainer, not a timer).")
_reg_const("concept_animation:RENDER_MEMORY_MAX", "operational", kind="structural", owner="concept_animation",
           rationale="keep (machine safety, RW5d P2b spec §15): a figure render's memory cap (4 GiB; oomd history).")
_reg_const("concept_animation:RENDER_TASKS_MAX", "operational", kind="structural", owner="concept_animation",
           rationale="keep (machine safety, RW5d P2b): a figure render's task cap in its scope (fork bombs).")
# Reader RW5d P2b, Codex review fixes (F2, F3): the declared-function check's work and clock, and the render's
# output and video caps. All keep: machine-safety bounds, never a weight, margin or threshold.
_reg_const("concept_animation:RENDER_MAX_OUTPUT_BYTES", "operational", kind="structural", owner="concept_animation",
           rationale="keep (machine safety, Codex review F3): the most stdout+stderr one render may print; both pipes "
                     "are drained with bounded tails, and a render past it is stopped (its process group) and fails.")
_reg_const("concept_animation:RENDER_MAX_VIDEO_BYTES", "operational", kind="structural", owner="concept_animation",
           rationale="keep (machine safety, Codex review F3): the largest rendered mp4 read into the sidecar; a "
                     "larger file fails as too large, unread.")
_reg_const("concept_animation:_TASKKILL_SECONDS", "operational", kind="structural", owner="concept_animation",
           rationale="keep (operational, Codex re-review F12): how long Windows' taskkill /T may take to end a "
                     "render's process tree before the render itself is killed anyway.")
_reg_const("figure_manim:MAX_CLAIM_WORK", "operational", kind="structural", owner="figure_manim",
           rationale="keep (machine safety, Codex review F2): the claim oracle's metered expression steps over one "
                     "Manim figure's claims (the sketch verifier's cap, reused).")
_reg_const("figure_manim:CHECK_SECONDS", "operational", kind="structural", owner="figure_manim",
           rationale="keep (machine safety, Codex review F2): one Manim figure's whole check (sandboxed run and "
                     "oracle) wall clock, as the sketch verifier's.")
_reg_const("figure_manim:INTERRUPT_SECONDS", "operational", kind="structural", owner="figure_manim",
           rationale="keep (operational, Codex review F2/F6): how often a long oracle phase calls the rich job's "
                     "heartbeat (where a cancel is noticed), at most.")
_reg_const("figure_manim:_TICK_WORK", "operational", kind="structural", owner="figure_manim",
           rationale="keep (operational): metered steps between the oracle's looks at the clock (about a "
                     "millisecond), as the sketch verifier's.")
_reg_const("figure_sketch:SKETCH_MAX_SOURCE_BYTES", "constraint", kind="structural", owner="figure_sketch",
           rationale="keep: bounds a sketch's program to one reviewable idea (spec §15: 32 KiB).")
_reg_const("figure_sketch:SKETCH_MAX_ELEMENTS", "constraint", kind="structural", owner="figure_sketch",
           rationale="keep (display): the renderer's cost, at most 4,000 drawn elements (spec §15).")
_reg_const("figure_sketch:SKETCH_MAX_POINTS", "constraint", kind="structural", owner="figure_sketch",
           rationale="keep (display): every coordinate drawn across a scene's elements; renderer cost.")
_reg_const("figure_sketch:SKETCH_MAX_CELLS", "constraint", kind="structural", owner="figure_sketch",
           rationale="keep (display): one heat map's cells (64 x 64); renderer cost.")
_reg_const("figure_sketch:SKETCH_MAX_SERIES", "constraint", kind="structural", owner="figure_sketch",
           rationale="keep (display): a probe series' length (the values table and claim checks).")
_reg_const("figure_sketch:SKETCH_TIME_SAMPLES", "constraint", kind="structural", owner="figure_sketch",
           rationale='keep (numerical): verification coverage of a clocked sketch, 9 times from 0 to t_max (spec §15).')
_reg_const("figure_sketch:SKETCH_MAX_CLOCK_STEPS", "constraint", kind="structural", owner="figure_sketch",
           rationale='keep (operational): the most clock steps to t_max, so verification stays bounded.')
_reg_const("figure_sketch:SKETCH_PLAY_TICKS", "operational", kind="structural", owner="figure_sketch",
           rationale="keep (display, fix round 4): how many reads play takes from t = 0 to t_max (the desktop's PLAY_TICKS); part of the read schedule every run of a sketch follows.")
_reg_const("figure_sketch:SKETCH_FRAME_MS", "operational", kind="structural", owner="figure_sketch",
           rationale="keep (display): one frame's budget in the desktop (spec §15: 16 ms).")
_reg_const("figure_sketch:SKETCH_WATCHDOG_FRAMES", "operational", kind="structural", owner="figure_sketch",
           rationale='keep (display): frames a Worker call may take before the sketch is paused (spec §15: 30).')
_reg_const("figure_sketch:CLAIM_REL_TOL", "constraint", kind="structural", owner="figure_sketch",
           rationale="keep (numerical): float equality for an equals claim, the golden corpus's 1e-9 relative.")
_reg_const("figure_sketch:ODE_SAFETY", "constraint", kind="structural", owner="figure_sketch",
           rationale="keep (numerical): the margin on the Richardson estimate of RK4's integration error (spec §15: 4).")
_reg_const("figure_sketch:MC_FALSE_ALARM", "constraint", kind="structural", owner="figure_sketch",
           rationale='keep (numerical): how often a correct Monte Carlo sketch may be refused by chance, per check (spec §15: 1e-6); the strictness of a guard, not a learner-model number.')
_reg_const("figure_sketch:MAX_PROBES", "constraint", kind="structural", owner="figure_sketch",
           rationale='keep (display): declared probes per sketch (the values table).')
_reg_const("figure_sketch:MAX_CLAIMS", "constraint", kind="structural", owner="figure_sketch",
           rationale='keep (operational): claims per sketch (verification work, check lines).')
_reg_const("figure_sketch:MAX_BINDINGS", "constraint", kind="structural", owner="figure_sketch",
           rationale='keep (operational): element-probe bindings per sketch.')
_reg_const("figure_sketch:MAX_CHOICES", "constraint", kind="structural", owner="figure_sketch",
           rationale='keep (display): answers a choice prediction offers.')
_reg_const("figure_sketch:MAX_ID", "constraint", kind="structural", owner="figure_sketch",
           rationale='keep (display): the length of an element id.')
_reg_const("figure_sketch_engine:SKETCH_MEMORY_BYTES", "operational", kind="structural", owner="figure_sketch_engine",
           rationale="keep (machine safety): the sealed engine's memory cap, compiled into the engine (spec §15: 64 MiB).")
_reg_const("figure_sketch_engine:SKETCH_FUEL_PER_CALL", "operational", kind="structural", owner="figure_sketch_engine",
           rationale='keep (deterministic work cap): interrupt ticks per entry-point call, identical in verifier and desktop; measured on carson so a call at the cap fits about one frame (spec §15; the review file records the measurement).')
_reg_const("figure_sketch_engine:SKETCH_SERIALIZE_TICKS", "operational", kind="structural", owner="figure_sketch_engine",
           rationale="keep (deterministic work cap): ticks for writing one result as JSON, compiled into the engine; a scene at the point cap fits, and a getter or toJSON left in a result stays bounded.")
_reg_const("figure_sketch_engine:WASM_MEMORY_BYTES", "operational", kind="structural", owner="figure_sketch_engine",
           rationale="keep (machine safety): wasmtime's store memory limit, above the engine's own cap.")
_reg_const("figure_sketch_engine:WASM_FUEL_PER_CALL", "operational", kind="structural", owner="figure_sketch_engine",
           rationale='keep (machine safety): wasmtime fuel per call, a backstop for native work the interpreter cannot interrupt.')
_reg_const("figure_sketch_engine:CALL_SECONDS", "operational", kind="structural", owner="figure_sketch_engine",
           rationale='keep (machine safety): the wall-clock epoch deadline per call, the last backstop.')
_reg_const("figure_sketch_engine:WASM_STACK_BYTES", "operational", kind="structural", owner="figure_sketch_engine",
           rationale="keep (machine safety): wasm stack for the interpreter's recursion (the engine's JS guard fires first).")
_reg_const("figure_sketch_engine:STDERR_KEEP", "operational", kind="structural", owner="figure_sketch_engine",
           rationale="keep: error text kept from the shim's fd_write.")
_reg_const("figure_sketch_engine:_EBADF", "version", kind="structural", owner="figure_sketch_engine",
           rationale='a WASI errno value the deny-all shim answers with (protocol identity, not a parameter).')
_reg_const("figure_sketch_engine:_ENOSYS", "version", kind="structural", owner="figure_sketch_engine",
           rationale='a WASI errno value the deny-all shim answers with (protocol identity, not a parameter).')
_reg_const("figure_sketch:SKETCH_MAX_CLAIM_WORK", "operational", kind="structural", owner="figure_sketch",
           rationale="keep (machine safety, Codex review F2): the most grammar-expression steps checking one sketch's claims may take over every point read, every grammar evaluation metered as it runs (Codex review F2 round 3); bounds the Python oracle as the engine's caps bound the program.")
_reg_const("figure_sketch:SKETCH_MAX_VERIFY_OUTPUT_BYTES", "operational", kind="structural", owner="figure_sketch",
           rationale="keep (machine safety, Codex review F1): the engine output one verification reads over both runs; results are streamed (one held at a time), and this bounds their parsing and checking.")
_reg_const("figure_sketch:SKETCH_VERIFY_SECONDS", "operational", kind="structural", owner="figure_sketch",
           rationale="keep (machine safety, Codex review F2): one verification's wall clock (spec §8.4: a sketch is ready in tens of seconds); engine calls and claim loops stop at it.")
_reg_const("figure_sketch_engine:EPOCH_TICK_SECONDS", "operational", kind="structural", owner="figure_sketch_engine",
           rationale="keep (machine safety, Codex review F7): the tick of the shared epoch clock per-store deadlines are counted in; a deadline is honoured to within one tick.")
_reg_const("figure_sketch_verify:_TICK_WORK", "operational", kind="structural", owner="figure_sketch_verify",
           rationale="keep (operational, Codex re-review F2): how many metered expression steps claim checks do between wall-clock checks (about a millisecond of the oracle); cost of the check, not a model number.")
_reg_const("figure_sketch_verify:VERIFIER_REPORT_VERSION", "version", kind="structural", owner="figure_sketch_verify",
           rationale="the verifier's report version (Codex review F11 round 3), bumped whenever verification semantics change; a stored report from another version is re-verified by code before it is shown (an identity, not a parameter).")
_reg_const("figure_sketch_verify:TESTED_DIGEST_HEX", "version", kind="structural", owner="figure_sketch_verify",
           rationale="the length (hex digits, 128 bits) of a tested read's SHA-256 a report keeps for the desktop to compare (fix round 4); a format, not a parameter.")
_reg_const("figure_sketch_verify:VERIFY_SEED", "version", kind="structural", owner="figure_sketch_verify",
           rationale="the seed verification and a sketch's first drawn sample use (an identity, so the first drawn sample is the verified one).")

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
           rationale="how many candidates' summaries one value-of-information receipt keeps below "
           "mvp-0.44 or with data_capture.serving off (from it, every one; the best keeps its full "
           "forecast); receipt size only, never a decision.")
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
           rationale="§9.3 the true assignment probability below which a randomization variant's "
           "off-policy support is flagged thin; a guardrail that only fires when a design has too "
           "many variants for the floor, and never changes the logged 1/n (data capture A8).",
           bind_site="randomization_layer._uniform_propensity (thin-support flag)")

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


# Router objective RO4 (spec_router_objective_v1 §8.4, §8.6): the memory model's combiner prior is a labelled
# seed the Bayesian logistic fit moves; the rest are numerical resolution or structural units.
_reg_const("router_objective_memory:COMBINER_PRIOR_MEAN", "prior", owner="router_objective_memory",
           rationale="seed (judgment, labelled; RO4 §8.4): the combiner's prior means (a0, aA, aR) = (0, 1, 0.5): AD's "
           "predictive the baseline, FSRS's item memory moving it half its gap; the Laplace fit on realized cold "
           "outcomes moves it.")
_reg_const("router_objective_memory:COMBINER_PRIOR_VARIANCE", "prior", owner="router_objective_memory",
           rationale="seed (judgment, labelled; RO4 §8.4): the combiner's prior variance per coefficient, 0.25.")
_reg_const("router_objective_memory:_R_CLIP", "numerical", kind="structural", owner="router_objective_memory",
           rationale="numerical: retrievability kept inside (0, 1) before its logit (an exact 1 right after a review).")
_reg_const("router_objective_memory:_FIT_ITERATIONS", "numerical", kind="structural", owner="router_objective_memory",
           rationale="numerical resolution of the combiner's damped Newton fit, never a judgement.")
_reg_const("router_objective_memory:_FIT_TOLERANCE", "numerical", kind="structural", owner="router_objective_memory",
           rationale="numerical resolution of the combiner's damped Newton fit, never a judgement.")
_reg_const("router_objective_value:MINUTES_PER_DAY", "numerical", kind="structural", owner="router_objective_value",
           rationale="structural unit: active minutes to days on the rollout's clock.")
_reg_const("router_objective_price:GUARD_MULTIPLE", "constraint", kind="structural", owner="router_objective_price",
           rationale="keep (RO4 §8.6): the runaway guard's default, 3 x the remembered minutes; a numerical safeguard "
           "that forces a stop offer into the support and is reported, never a budget.")
_reg_const("router_objective_price:LOOKBACK_DAYS", "numerical", kind="structural", owner="router_objective_price",
           rationale="structural (RO4 §8.6, named in RO5's Codex review F4): how far back the session clock reads "
                     "activity, the literal RO4's serving clock already used; the realized window cost reads the same.")
# Router objective RO5 (spec_router_objective_v1 §9): a labelled recalibration prior and numerical resolution.
_reg_const("router_objective_stop_coin:_TINY", "numerical", kind="structural", owner="router_objective_stop_coin",
           rationale="numerical: a choice probability kept inside (0, 1) before its log in κ0's likelihood.")
_reg_const("router_objective_stop_coin:_REACH", "numerical", kind="structural", owner="router_objective_stop_coin",
           rationale="numerical resolution (RO5 Codex re-review F8, landing ruling R2): the return slope's prior "
                     "nodes span 40 prior sds; the bounds start there or past the likelihood's peak and widen with "
                     "the tail mass.")
_reg_const("router_objective_stop_coin:_PEAK_SPREADS", "numerical", kind="structural",
           owner="router_objective_stop_coin",
           rationale="numerical resolution (landing ruling R2): the return slope's nodes around the likelihood's peak "
                     "reach 8 of its spreads, wherever it falls.")
_reg_const("router_objective_stop_coin:_SPAN_NODES", "numerical", kind="structural",
           owner="router_objective_stop_coin",
           rationale="numerical resolution (landing ruling R2): the return slope's nodes across the bounds (both peaks "
                     "and the region between).")
_reg_const("router_objective_stop_coin:_WIDENINGS", "numerical", kind="structural",
           owner="router_objective_stop_coin",
           rationale="numerical resolution (landing ruling R2): widenings of the integration's bounds before it is "
                     "reported unconverged (the prior then stands).")
_reg_const("router_objective_stop_coin:_TAIL_TOLERANCE", "numerical", kind="structural",
           owner="router_objective_stop_coin",
           rationale="numerical resolution (landing ruling R2): the mass past the integration's bounds, bounded by the "
                     "prior's kernel, relative to the mass inside.")
_reg_const("router_objective_stop_coin:_PRIOR_NODES", "numerical", kind="structural",
           owner="router_objective_stop_coin",
           rationale="numerical resolution (RO5 Codex re-review F8): the return slope's nodes over the prior's range.")
_reg_const("router_objective_stop_coin:_LOCAL_NODES", "numerical", kind="structural",
           owner="router_objective_stop_coin",
           rationale="numerical resolution (RO5 Codex re-review F8): the return slope's nodes around the ratio "
                     "estimate.")
_reg_const("router_objective_stop_coin:_REFINEMENTS", "numerical", kind="structural",
           owner="router_objective_stop_coin",
           rationale="numerical resolution (RO5 Codex re-review F8): refinements before the integration is reported "
                     "unconverged (the prior then stands).")
_reg_const("router_objective_stop_coin:_TOLERANCE", "numerical", kind="structural", owner="router_objective_stop_coin",
           rationale="numerical resolution (RO5 Codex re-review F8): the integration's convergence tolerance, relative "
                     "to the posterior sd.")
_reg_const("router_objective_stop_coin:_COLLINEAR", "numerical", kind="structural",
           owner="router_objective_stop_coin",
           rationale="numerical resolution (RO5 Codex re-review F9): proportional session contributions (no "
                     "information about the slope) detected to double precision.")
_reg_const("router_objective_goal_read:CALIBRATION_PRIOR_MEAN", "prior", owner="router_objective_goal_read",
           rationale="seed (judgment, labelled; RO5 §9 item 3): the pool forecast's recalibration prior (a, b) = (0, 1), "
           "the forecast taken at its word; the randomized checks' Laplace fit moves it.")
_reg_const("router_objective_goal_read:CALIBRATION_PRIOR_VARIANCE", "prior", owner="router_objective_goal_read",
           rationale="seed (judgment, labelled; RO5 §9 item 3): the recalibration prior's variance per coefficient, 1.")
# Router objective RO6 (spec_router_objective_v1 §10): numerical resolution and a resource bound, no judgement.
_reg_const("router_objective_learned_tail:_FIT_PASSES", "numerical", kind="structural",
           owner="router_objective_learned_tail",
           rationale="numerical: the most refinements of the plug-in noise variance in the fit and in w^'s slope.")
_reg_const("router_objective_learned_tail:_FIT_TOLERANCE", "numerical", kind="structural",
           owner="router_objective_learned_tail",
           rationale="numerical: the relative change at which the noise variance's refinement stops.")
_reg_const("router_objective_learned_tail:_TINY", "numerical", kind="structural",
           owner="router_objective_learned_tail",
           rationale="numerical: a floor under a variance before a division.")
_reg_const("router_objective_tail_data:_CACHE_LIMIT", "constraint", kind="structural",
           owner="router_objective_tail_data",
           rationale="keep (resource bound): the parsed immutable traces kept per process before the cache is cleared; "
           "it changes no number, only how often a trace is parsed again.")
_reg_const("router_objective_tail_data:_SAME_CUTOFF_SECONDS", "numerical", kind="structural",
           owner="router_objective_tail_data",
           rationale="numerical (Codex review F3): two cutoffs this close are one; the trace keeps cutoff_days to six "
           "places (about 0.09 s), so a shared cutoff read back from two traces differs by rounding only.")

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
    # Plan-first transport T1 (owner, 2026-10-21): which transport may serve,
    # never what is measured. agent_harness_opt_in admits the frozen Codex
    # harness (default false: refused for every task, never a fallback);
    # plan_fallback_profile names the OpenRouter profile LearnLoop may OFFER
    # while the ChatGPT plan is unavailable (used only on the learner's choice).
    _ConfigRule(_exact("ai.agent_harness_opt_in", "ai.plan_fallback_profile"), "structural", "operational",
                "transport admission (Codex agent-harness opt-in; the asked-for OpenRouter offer while the "
                "ChatGPT plan is unavailable); selects who answers, never what is measured."),
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
    # Reader workbench RW2b: the workbench's own calls ("Check my work", the
    # bridge to the book) per problem, their metered spend a UTC day and the
    # owner's price for a metered check route (verdicts are help, recorded in
    # help_assists; a shown check reaches the attempt only through hints_used
    # with its existing meaning).
    _ConfigRule(_exact(
        "workbench.max_calls_per_session",
        "workbench.max_daily_cost_usd",
        "workbench.price_per_million",
    ), "structural", "operational",
        "the workbench's own model calls per problem / their metered spend a UTC day / the owner's price "
        "for a metered check route; money bounds, no measurement authority (a check never grades)."),
    # Reader workbench RW2b: the kill switches of "Check my work" and the help
    # ladder and its parts (fix round 1, F11: booleans, so Inventory A's
    # numeric walk never reaches them; classified here so every new key has
    # a rule). Off restores RW2a or drops the part; a shown check or hint
    # reaches the attempt only through hints_used / primed with their
    # existing meaning, so none changes a measurement.
    _ConfigRule(_exact(
        "workbench.help_enabled",
        "workbench.symbolic_checks_enabled",
        "workbench.discriminate_enabled",
        "workbench.error_kind_enabled",
        "workbench.bridge_enabled",
    ), "structural", "operational",
        "kill switches for the workbench's checks and help ladder / the sandboxed symbolic checks / the "
        "discriminating question / the error-kind guess / the bridge to the book; on-off availability of "
        "help, no measurement, scheduling or serving authority."),
    # Reader workbench RW2c (what helps this learner, spec §5.10): the kill
    # switches of the help-outcome lines (a pure read given to the hint writer
    # and chooser as context), the worked example in the learner's route,
    # "Compare with the book's method" (a reveal of an existing kind on the
    # item, with its existing meaning) and the logged draw between passages
    # that all passed the judge. Context, display and learner picks: none
    # changes a measurement.
    _ConfigRule(_exact(
        "workbench.help_outcomes_enabled",
        "workbench.examples_enabled",
        "workbench.compare_methods_enabled",
        "workbench.passage_draw_enabled",
    ), "structural", "operational",
        "kill switches for the help-outcome lines given to the hint writer and chooser / the worked example "
        "in the learner's route / compare methods after a correct Submit / the logged passage draw; context, "
        "display and learner picks, no measurement, scheduling or serving authority."),
    # Reader workbench RW2d (spec §5.11, G41): the kill switch of the successor
    # whose field derivation reads mid-work stuck steps and help before the
    # first step. A boolean (classified so every new key has a rule); the rows
    # it adds carry no outcome and no mass, so there is no weight to learn:
    # they only feed the field's existing fast-track blocking rule. Off
    # restores the predecessor's derivation, serving and plans exactly.
    _ConfigRule(_exact(
        "workbench.field_signals_enabled",
    ), "structural", "operational",
        "kill switch for RW2d's successor: workbench stuck steps and help before the first step as field "
        "signals that keep an LO out of fast-track and teach it first; zero-mass rows that never reach the "
        "record; off, the predecessor's derivation, Phase 6 serving and plans."),
    # FG1c (spec_followup_generate_serve_v1 §7): the learner's marks on possible causes. A boolean
    # (classified so every new key has a rule). Marks are receipts and an attributed opinion, so
    # there is no weight to learn until a later stage measures the sensor.
    _ConfigRule(_exact(
        "followup.hypothesis_marks",
    ), "structural", "operational",
        "kill switch for the learner's marks on possible causes and the hypothesis-list exposure receipts; "
        "they reach the learner state card and the diagnoser's context as attributed opinion and move no "
        "probability; off, no marks UI, no rows, and every reply and context as it was."),
    # Rebuild equivalence (mvp-0.34, docs/reviews/rebuild-equivalence-fix.md):
    # the kill switch of the successor whose replay reads the ledger bounded at
    # the replayed attempt. A boolean (classified so every new key has a rule);
    # it selects which ledger rows replay folds, never a weight. Off restores
    # the predecessor's whole-ledger replay exactly; live writes never read it.
    _ConfigRule(_exact(
        "replay.ledger_bounded",
    ), "structural", "operational",
        "kill switch for the rebuild-equivalence successor: replay reads the recent-attempt windows and the "
        "canonical facet cache bounded at the replayed attempt, as its live write saw them; off, replay reads "
        "the whole ledger as the predecessor did. Never read by a live write."),
    # Mobile PR-4 (mvp-0.37, docs/reviews/mobile-pr3-pr4.md, Codex review
    # F4): the kill switch of the successor whose live attempt writes only its
    # item row's scheduling columns. A boolean (classified so every new key
    # has a rule); which columns a write owns is structural, never a weight.
    # Off restores the predecessor's whole-row upsert exactly; replay never
    # reads it.
    _ConfigRule(_exact(
        "practice.attempt_keeps_content_state",
    ), "structural", "operational",
        "kill switch for mobile PR-4's successor: a live attempt writes only its item row's scheduling columns "
        "(active only closes, content_hash is content sync's), so it never reopens a row a content sync closed; "
        "off, the attempt upserts the whole row as the predecessor did. Never read by replay."),
    # Router objective RO0 (spec_router_objective_v1 §4): the receipts' kill switch. A boolean
    # (classified so every new key has a rule); it decides no plan, only whether a row is written.
    _ConfigRule(_exact(
        "router_objective.receipts",
    ), "structural", "operational",
        "kill switch for RO0's additive receipts and columns: off, nothing is written and nothing else changes. "
        "Nothing serving, scheduling, certification or replay reads what it writes."),
    # Mobile PR-6 (Codex review F6): the kill switch of the phone's device rules.
    # A boolean; which items need a desktop is structural (their contract and
    # their parsed Markdown), never a weight.
    _ConfigRule(_exact(
        "practice.device_eligibility_enabled",
    ), "structural", "operational",
        "kill switch for the phone's device rules (mobile PR-6): off, a phone request is served as the desktop is, "
        "with no queue exclusion, no desktop_only refusal and no refusal to adopt around a draft. Never read by "
        "a desktop request or by replay."),
    # The cold-retry reschedule (mvp-0.38, owner decision 2026-10-25, CA2
    # follow-up Q4; docs/reviews/cold-retry-after-assist.md): the kill switch
    # of the successor that schedules one fresh repair cold retry after help
    # was taken on a due one. A boolean (classified so every new key has a
    # rule); the fresh retry's timing is the lane's existing delay and its
    # bound (one per chain) is structural, so no weight, margin or threshold
    # is added. Off restores the predecessor exactly; replay never reads it.
    _ConfigRule(_exact(
        "practice.reschedule_cold_after_assist",
    ), "structural", "operational",
        "kill switch for the cold-retry reschedule successor: help taken on a due repair cold retry withdraws it "
        "and schedules one fresh cold retry on another independent surface at the lane's existing delay (one per "
        "chain, a structural bound); off, the assisted retry is withdrawn at the next serve as the predecessor "
        "did. Never read by replay."),
    # Follow-ups Nov 2 (mvp-0.42, renumbered from mvp-0.41 at its landing; Codex review F1; docs/reviews/followups-nov2.md):
    # the kill switch of the successor whose keyed help fold counts exactly the
    # rows that attach. A boolean (classified so every new key has a rule); no
    # weight, margin or threshold is added. Off restores the predecessor's fold
    # exactly; replay never reads it.
    _ConfigRule(_exact(
        "hints.fold_follows_attach",
    ), "structural", "operational",
        "kill switch for the help-fold successor mvp-0.42: a keyed submit's fold counts the key's shown server "
        "hints in any practice session and the attempt takes them in its own transaction (a hint shown before the "
        "session rolled over is counted or primes where it attaches); off, the predecessor's session-only fold and "
        "H0's attach after the commit. Never read by replay."),
    # Teacher TE0 (spec_teacher_v1 §15.2): the kill switch of the confidence
    # events in model contexts and on the router card. A boolean (classified
    # so every new key has a rule); the events are context, never a weight,
    # and nothing that scores, schedules, projects or serves reads them. Off
    # restores every reader's predecessor context exactly.
    _ConfigRule(_exact(
        "teacher.confidence_events_enabled",
    ), "structural", "operational",
        "kill switch for TE0's confidence events (the tap and the grader's hedge read with the outcome) in the "
        "router card, the history-aware diagnoser, the hint writer and the tutor; context only, no "
        "measurement, scheduling or serving authority; off, every context is its predecessor's."),
    # Router objective RO1 (mvp-0.46; spec_router_objective_v1 §5.5): the successor's three kill
    # switches. Booleans (classified so every new key has a rule); RO1 adds no weight, margin or
    # threshold, it removes one (the surprise factor's alpha_interval, f_min and f_max stay for older
    # versions and are inert at the tag with the switch on). Off restores mvp-0.45 exactly.
    _ConfigRule(_exact(
        "scheduler.surprise.remove_interval_factor",
    ), "structural", "operational",
        "kill switch for RO1's successor mvp-0.46: the surprise factor is not applied to the FSRS interval "
        "(due_at follows interval_for_retention(S); rating, S, D and surprise unchanged, and the surprise row "
        "records 1.0, what was applied, live and in replay); off, the predecessor's stretched interval. A flip "
        "reaches persisted due dates at the next whole-vault rebuild, whose receipt records it."),
    _ConfigRule(_exact(
        "router_objective.available_at_reads",
    ), "structural", "operational",
        "kill switch for RO1's successor mvp-0.46: the router card's decision-time attempt reads filter by the "
        "availability time coalesce(received_at, created_at); off, by created_at. Outcomes, FSRS and mastery "
        "always read created_at."),
    _ConfigRule(_exact(
        "router_objective.self_report_not_validated",
    ), "structural", "operational",
        "kill switch for RO1's successor mvp-0.46: a learner's misconception pick (a learner_report:* "
        "resolution id) is not counted as validated evidence in the diagnoser's history; the factor's status "
        "and resolution ids are unchanged. Off, every resolution id counts, as the predecessor."),
    # Router objective RO4 (mvp-0.47; spec_router_objective_v1 §8, §12): the successor's kill switches,
    # its seeds and its keep bounds. No weight, margin or threshold is a hand-set constant: every seed is
    # a labelled prior a posterior moves (w through the Gaussian posterior over Δ, β_v through the effect
    # slopes, p_accept through §4 row 7, κ0 re-centred daily) or a stated preference (c, ω, H, B), and
    # the bounds are numerical safeguards (keep).
    _ConfigRule(_exact(
        "router_objective.enabled", "router_objective.sensors_in_value",
    ), "structural", "operational",
        "kill switches for RO4's successor mvp-0.47: enabled serves the objective (soft-budget frame, the two "
        "policies and their learned mix, the trace); off, mvp-0.46's mixture and frame exactly. "
        "sensors_in_value: the LLM's effect-slope correction on the memory rollout's learning effect."),
    _ConfigRule(_exact(
        "router_objective.rollout_theta_draws", "router_objective.rollout_theta_draws_max",
    ), "structural", "numerical",
        "keep (RO4 §8.1, mvp-0.47): the parameter draws shared across candidates (at least the first, more while "
        "the LLM policy is out, up to the second): a precision and work bound, never a judgement; the trace "
        "reports the paired standard error of the top two."),
    _ConfigRule(_exact(
        "router_objective.horizon_days", "router_objective.undated_use_density",
        "router_objective.dated_use_weight", "router_objective.evaluation_window_days",
    ), "decision", "prior",
        "RO4 §3.3, §8.5, §8.7 seeds (mvp-0.47), chosen by judgment and labelled: H (how far undated uses count), "
        "c (the daily density of undated uses, copied into a goal at creation), ω (a dated goal's weight per "
        "topic) and B (the evaluation window). Preferences, not learnable from outcomes; shown in every trace."),
    _ConfigRule(_exact(
        "router_objective.session_gap_minutes", "router_objective.session_guard_minutes",
        "router_objective.llm_card_token_budget",
    ), "structural", "constraint",
        "keep (RO4 §8.6, §8.3, mvp-0.47): the gap that ends a session for the attention price, the runaway guard "
        "(3 x the remembered minutes by default; a numerical safeguard that forces a stop offer into the "
        "support and is reported, never a budget) and the LLM policy's card bound (prompt size)."),
    _ConfigRule(_exact(
        "router_objective.llm_weight_prior", "router_objective.llm_min_share",
        "router_objective.numeric_min_share", "router_objective.delta_prior_sd",
        "router_objective.effect_slope_prior_mean", "router_objective.effect_slope_prior_variance",
        "router_objective.stop_accept_prior_a", "router_objective.stop_accept_prior_b",
    ), "decision", "prior",
        "RO4 §8.3, §8.4, §8.7, §8.1 seeded priors (mvp-0.47), chosen by judgment and not measured: w starts at 0.8 "
        "with declared minimum shares 0.1 each (prices for information), the Gaussian prior sd s0 = 0.01 over "
        "Δ that the scores move, the effect slope β_v ~ N(0.2, 0.04) (AD's alpha:z_v1) learned from "
        "randomized assignments, and p_accept ~ Beta(1, 1) updated from §4 row 7."),
    # Router objective RO5 (mvp-0.48; spec_router_objective_v1 §9, §12): the arms are declared prices for
    # information (an exact logged probability each, the report shows each arm's minutes), the calibration's
    # spreads are labelled seeds a posterior moves, and fitted_models is a kill switch.
    _ConfigRule(_exact(
        "router_objective.stop_coin", "router_objective.check_rate", "router_objective.embedded_checks_per_day",
        "router_objective.pick_open_share",
    ), "decision", "shaping_weight",
        "RO5 §9 items 1, 2, 6 and §12 (mvp-0.48): declared prices for information, not statistical facts: the stop "
        "coin 0.05 each way at a reversible boundary (offer stop / present the next block), one embedded randomized "
        "cold check a day (or a rate per valued topic per day; off schedules none), a 0.1 share of misconception "
        "picks left open. Each assignment is logged with its exact probability in policy_experiment_assignments; "
        "zero (off) serves mvp-0.47 exactly; the router objective report shows the minutes each arm costs."),
    _ConfigRule(_exact(
        "router_objective.kappa_prior_log_sd", "router_objective.return_slope_prior_sd",
        "router_objective.goal_transfer_prior_sd",
    ), "decision", "prior",
        "RO5 §9 items 1 and 3 seeded priors (mvp-0.48), chosen by judgment and labelled: kappa0's prior spread on the "
        "log scale around the seed it is handed from (randomized stop offers move it), the return model's slope "
        "prior centred on no effect (randomized stop offers move it), and the pool-to-goal transfer's wide prior "
        "(imported exam results and sittings move it)."),
    _ConfigRule(_exact("router_objective.fitted_models"), "structural", "operational",
        "kill switch for RO5's successor mvp-0.48 (§9 item 7): the rollouts read AD's fitted learning posterior "
        "and the combiner fed resolved randomized checks; off, RO4's priors."),
    # Router objective RO6 (mvp-0.49; spec_router_objective_v1 §10): a kill switch and two labelled priors that
    # the data move (no promotion step, threshold or minimum sample: owner, Nov 4).
    _ConfigRule(_exact("router_objective.learned_tail"), "structural", "operational",
        "kill switch for RO6's successor mvp-0.49 (§10): the numeric policy values each candidate with the learned "
        "tail's residual, V~ = V_tail + w^ * V_residual; off, mvp-0.48 exactly (nothing fitted, read or traced)."),
    _ConfigRule(_exact(
        "router_objective.residual_prior_sd", "router_objective.residual_weight_prior_sd",
    ), "decision", "prior",
        "RO6 §10 seeded priors (mvp-0.49), chosen by judgment and labelled: the fitted Q evaluation's Gaussian "
        "prior sd on each standardized coefficient (0.01 use-equivalents, about one block's effect, as "
        "delta_prior_sd; its regularization, centred on no residual), and the residual's calibration slope w^'s "
        "prior sd (1.0, centred on zero, so w^ starts at zero); only randomized stop-coin contrasts move w^."),
    # Teacher TE1 (mvp-0.41; spec_teacher_v1 §18): the successor's kill switches
    # and curriculum C4's brief switch. Booleans and an enum (classified so every
    # new key has a rule); the lesson-check mass is learned (§12.1, its seeded
    # priors are the module constants of learner.lesson_weight), so no weight,
    # margin or threshold is added here. Off restores mvp-0.40 exactly.
    _ConfigRule(_exact(
        "teacher.enabled", "teacher.weight.learned", "teacher.weight.source", "teacher.brief.use_deliverable",
    ), "structural", "operational",
        "kill switches for teacher TE1's successor: lessons may open / a lesson check enters mastery at the "
        "learned mass (off: the type's configured 0.5) / the forecast pool on top of it (parametric: the "
        "learned mass alone) / curriculum C4's deliverable and notes in the brief. Operational only: the "
        "learned quantities move with the data, never with these."),
    # Teacher TE2-log (spec_teacher_v1 §11.6, §11.9, §20): item 5's logging. A boolean
    # (classified so every new key has a rule); it decides no lesson, only whether the
    # episode rows, the activity intervals and the node forecasts are written.
    _ConfigRule(_exact(
        "teacher.episode_log",
    ), "structural", "operational",
        "kill switch for TE2-log's additive receipts (lesson_episodes, lesson_activity_intervals, the "
        "lesson_node_held forecast and the receipt's episodes and minutes) and the turn fields that feed them "
        "(note_detour, p_held); off, nothing is written and lessons are TE1's exactly. Nothing serving, "
        "scheduling, certification or replay reads what it writes."),
    # Reader RW5d P4b (spec_reader_show_me_figures_v1 §6.5, §10.4): the teacher's
    # manipulatives. A boolean (classified so every new key has a rule): content and
    # display only, no weight, margin or threshold; off, the teacher's prompt and turn
    # schema are TE1's byte for byte and no lesson figure is built or shown.
    _ConfigRule(_exact(
        "teacher.visuals",
    ), "structural", "operational",
        "kill switch for the teacher's visuals (RW5d P4b): a lesson turn may carry a figure built by the "
        "figure service (grammar and sketch tiers, its own predictions off in the lesson); a figure never "
        "grades and is never evidence; off, the teacher's prompt and turn schema are TE1's exactly."),
    _ConfigRule(_exact(
        "teacher.brief.depth", "teacher.context.sources_tokens", "teacher.delayed.max_wait_days",
        "teacher.metered_price_per_million", "teacher.max_lesson_cost_usd",
    ), "structural", "operational",
        "keep: the brief's prerequisite depth and the sources' token budget (context budgets: cost and "
        "latency, not a model of the learner) / no promised delayed check waits longer (a guardrail so a "
        "promise is never dropped silently, RW6b's max_wait_days) / the owner's price and per-lesson cap "
        "for a metered lesson (spend; unset, no OpenRouter offer and no metered turn)."),
    _ConfigRule(_exact(
        "teacher.delayed.target_retrievability", "teacher.delayed.fallback_retention_days",
        "teacher.delayed.fallback_transfer_days",
    ), "decision", "prior",
        "seeded priors of the delayed checks' dates (spec §13, §18.4): R* = 0.9, basis published (FSRS's "
        "default desired retention; RW6b's valuation replaces it); 3 and 7 days, basis legacy (RW6b's "
        "retention fallback and capture.test_me_later_days), used only while the LO has no FSRS state. "
        "Serving dates, never evidence."),
    # Teacher TE1b (spec_teacher_v1 §15.1, §18.4): the successor's kill switch and
    # the anti-nagging ceiling (keep: never learned, each bind logged). How often a
    # suggestion comes and how long a "Not now" lasts are learned (the module's
    # seeded priors); neither is a config value.
    _ConfigRule(_exact("router.lesson_suggestions.enabled"), "structural", "operational",
        "kill switch for teacher TE1b's successor: Today may draw one lesson suggestion a day with an exact "
        "logged propensity; off (or below the tag) nothing is drawn or written and Today is mvp-0.42's."),
    _ConfigRule(_exact("router.lesson_suggestions.ceiling_per_day"), "structural", "constraint",
        "keep: an anti-nagging guardrail on shown suggestions a day (spec §18.4: never learned; a bind is logged "
        "on the decision as ceiling_bound, and a ceiling that binds often means the acceptance model is wrong)."),
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
    # Reader CA3: comparing from anywhere. The kill switch (a boolean,
    # classified so every new key has a rule), and the ask box's reading of
    # named books (one Decider request per pressed Enter; verdicts go to
    # judgment_ledger, never evidence): its deadline and the route's daily
    # call cap. Latency and spend bounds: the reading only picks which books
    # a display-only comparison reads.
    _ConfigRule(_exact(
        "reader_compare.scope_enabled",
        "reader_compare.scope_timeout_seconds",
        "reader_compare.scope_max_calls_per_day",
    ), "structural", "operational",
        "kill switch for comparing from anywhere (one comparison request for every door, an anchor without "
        "pins, named books that only narrow the scope) / the ask box's reading deadline / the route's daily "
        "Decider call cap; display, latency and spend bounds, no measurement, scheduling or serving authority."),
    # Reader CA4: the table by point. The kill switch (a boolean, classified so
    # every new key has a rule) and the most views a comparison asks for and
    # keeps: a stored-size bound labelled a `keep` guardrail (§12.2), never a
    # learned constant (the views only pick which display rows exist).
    _ConfigRule(_exact(
        "reader_compare.by_point",
        "reader_compare.max_perspectives",
    ), "structural", "display",
        "kill switch for the comparison table by point (source_compare.v2, the grid, chips, the learner's "
        "column, hide row, narrow cards, by book) / keep: the most requested views a comparison asks for and "
        "keeps (a stored-size bound); display and proposals only, no measurement, scheduling or serving "
        "authority."),
    # Reader workbench RW4a: the library answer's organizer (one listwise call
    # per ask; notes are display, verdicts go to judgment_ledger, never
    # evidence): its metered spend a UTC day.
    _ConfigRule(_exact(
        "library_ask.max_daily_cost_usd",
    ), "structural", "operational",
        "the library answer's organizer's metered spend a UTC day; a money bound, no measurement "
        "authority (its notes are display only)."),
    # Reader workbench RW6b part 1 (cold follow-ups, spec §9.3): two keep
    # guardrails. The valuation's own parameters (lambda, the burden, the
    # nat-to-minutes scale) are robust_composition's, read from there, and the
    # retention date is FSRS's (the practiced item's effective due, else the
    # scheduler's own first interval for that attempt's rating), so the
    # spec's followups.fallback_days is not a key at all.
    _ConfigRule(_exact(
        "followups.max_wait_days",
        "followups.max_daily_cost_usd",
    ), "structural", "operational",
        "keep: the anti-nag time cap (no claim waits longer than this for its check on your own; a "
        "ceiling on the date the existing machinery derives, never the date itself) / the metered spend a "
        "UTC day of the relevance and exposure calls made for follow-ups (the owner's spending authority; "
        "subscription calls are estimated_only); no measurement, scheduling or serving authority."),
    _ConfigRule(_exact(
        "followups.enabled",
        "followups.formative_questions_enabled",
        "followups.generate_when_nothing_fits",
    ), "structural", "operational",
        "kill switches for cold follow-ups (followups.enabled is the kill switch of the successor mvp-0.39; "
        "off, or below the tag, the predecessor's plan) / formative records adding questions / background "
        "generation when nothing fits; test_me_later commitments the learner can undo, never evidence."),
    # Reader workbench RW6b part 2 (spec §9.2): the session narrative (one
    # background call per reader session, salience only, never evidence) and
    # the router card's "Reader activity" section (routing only, never
    # evidence). The 120-word bound is the spec's structural bound in code
    # (reader_digest.MAX_WORDS), not a key; the card's per-list bound
    # (router_reader.CARD_LIST_LIMIT) is a prompt-size bound, keep, not a key.
    _ConfigRule(_exact(
        "digest.enabled",
        "digest.narrative_enabled",
    ), "structural", "operational",
        "kill switches for RW6b part 2 as a whole (the narrative and the router card's Reader activity section) / "
        "the narrative alone; display and routing data, never evidence, no measurement, scheduling or serving "
        "authority (no successor)."),
    _ConfigRule(_exact(
        "digest.max_daily_cost_usd",
        "digest.price_per_million",
    ), "structural", "operational",
        "keep: the narrative's metered spend a UTC day (the owner's spending authority; subscription calls are "
        "estimated_only) / the owner's price for a metered narrative route; money bounds, no measurement "
        "authority (a narrative never grades)."),
    # Reader workbench RW1c: the Reader tutor's kill switches (booleans, so
    # Inventory A's numeric walk never reaches them; classified here so every
    # new key has a rule). Retrieval is context and display, the offers are
    # learner picks; off restores today's selection-and-neighbours tutor and
    # no buttons. A Reader question asked inside a workbench session bound to
    # an item is stored on that item and practice session (Codex review F1),
    # so it reaches the attempt only through the existing fields: the
    # submit's question hint-equivalents and tutor_answer / source_review
    # reveals on key overlap of everything it showed.
    _ConfigRule(_exact(
        "reader_tutor.retrieval_enabled",
        "reader_tutor.offers_enabled",
    ), "structural", "operational",
        "kill switches for the Reader tutor's retrieval, answer modes, abstention, another way and that "
        "didn't help / the offer buttons under its answers; context and display, no measurement, scheduling "
        "or serving authority."),
    # Learner-blindness relax (owner direction 2026-11-01: blindness only
    # where it matters, the grader; docs/reviews/learner-blindness-relax.md).
    # Three kill switches (booleans, classified so every new key has a rule)
    # and the diagnoser's prior-analysis arm (a string: a randomized
    # equipoise arm by default, recorded on each diagnosis receipt and read
    # per arm in the m2 report, never a fixed preference). Every one changes
    # a model context only: the tutor, the narrative, the diagnoser and AD's
    # reporting-only forecasters never write an attempt, a claim, mastery or
    # a grade, and the blind grader's inputs are untouched.
    _ConfigRule(_exact(
        "reader_tutor.learner_state_enabled",
        "digest.narrative_quotes_inquiry",
        "adaptive_difficulty.history_answer_excerpts",
        "diagnosis.history_includes_prior_analysis",
    ), "structural", "operational",
        "kill switches for the Reader tutor's learner state (readiness in words, confidence events, recent "
        "exchanges and outcomes through learner_protection) / the narrative's quotes of the learner's own "
        "inquiry questions / the llm_v3 history card's answer excerpts / the diagnoser's prior-analysis arm "
        "(randomized by default, measured per arm); model context only, no measurement, scheduling or serving "
        "authority, never the grader."),
    # Reader workbench RW4b: the kill switches of the textbook-exercise view and
    # of its retired fallback search (booleans, so Inventory A's numeric walk
    # never reaches them; classified here so every new key has a rule, as
    # RW2b's fix round 1 F11 did). The view only displays the sources
    # service's candidates and hands a learner's pick to its existing import
    # and pick paths, so neither changes a measurement.
    _ConfigRule(_exact(
        "library_exercises.enabled",
        "library_exercises.fallback_enabled",
    ), "structural", "operational",
        "kill switches for the Reader's view of textbook-exercise candidates / the learner-initiated fallback "
        "search; on-off availability of display and of the existing import path, no measurement, scheduling "
        "or serving authority."),
    # Reader workbench RW3b: discovered cues. The switches are booleans
    # (classified so every new key has a rule); the holdout rate is the
    # display experiment's logged draw (a withheld cue is only not shown; its
    # seed and propensity are receipts, never evidence); the call cap and the
    # metered daily spend bound the background cue judge.
    _ConfigRule(_exact(
        "cues.discovery_enabled",
        "cues.try_first_enabled",
        "cues.value_order_enabled",
    ), "structural", "operational",
        "kill switches for discovered margin cues / their try-this-step-first offers / their value order; "
        "display only, no measurement, scheduling or serving authority."),
    _ConfigRule(_exact(
        "cues.holdout_rate",
        "cues.max_calls_per_source_open",
        "cues.max_calls_per_source_per_day",
        "cues.max_daily_cost_usd",
    ), "structural", "operational",
        "the share of eligible discovered margin cues withheld at random (seed and propensity logged) / the "
        "cue judge's calls per source open / its calls per source per rolling 24 hours, over every open, counted from "
        "the durable receipts / its metered spend a UTC day; a display experiment and spend bounds, no "
        "measurement authority (cues are display only)."),
    # Reader workbench RW4d: the kill switch of "Keep this comparison" (a
    # boolean, so Inventory A's numeric walk never reaches it; classified here
    # so every new key has a rule). Keep writes source-object proposals (P3
    # §7) and the learner's own take; nothing reads them for grading,
    # scheduling, serving, replay or evidence, and nothing becomes a concept
    # edge, facet merge, prerequisite or LO change.
    _ConfigRule(_exact(
        "reader_compare.keep_enabled",
    ), "structural", "operational",
        "kill switch for keeping a source comparison as source-object proposals (with the learner's take, "
        "the kept-comparison mark and requested perspectives); proposals and display, no measurement, "
        "scheduling or serving authority."),
    # Reader CA1: the problem as printed. The kill switch (a boolean,
    # classified so every new key has a rule): the crop of an imported
    # problem's own blocks, the original page (one hint-equivalent before
    # Submit, in the existing book component of hints_used: no new evidence
    # meaning), the learner's photo and the transcription report (a
    # maintenance notice). Display and a report only.
    _ConfigRule(_exact(
        "practice.as_printed.enabled",
    ), "structural", "operational",
        "kill switch for the problem as printed (a crop of its own blocks), the original page link, the "
        "learner's photo and the transcription report; display and a maintenance notice, no measurement, "
        "scheduling or serving authority (the page's one hint-equivalent is the existing book count)."),
    # Reader workbench RW4e: instructional roles. The switches are booleans
    # (classified so every new key has a rule): the judges' role proposals
    # (source-object proposals, never evidence) and their positive use in
    # retrieval, cue shortlists and library grouping (roles add, never
    # exclude); the batch labeller's per-run spend bound.
    _ConfigRule(_exact(
        "roles.on_demand_enabled",
        "roles.positive_filter_enabled",
    ), "structural", "operational",
        "kill switches for the Reader judges' instructional-role proposals / their positive use in retrieval, "
        "cue shortlists and library grouping; labels on sources, no measurement, scheduling or serving "
        "authority (roles never exclude)."),
    _ConfigRule(_exact(
        "roles.batch_max_cost_usd",
    ), "structural", "operational",
        "the owner-run batch role labeller's metered spend per run, checked before each batch call; a spend "
        "bound, no measurement authority (role labels are source-object proposals)."),
    # Reader workbench RW7a: reading paths in the Guide. The switch is a
    # boolean (classified so every new key has a rule): the Guide's path card
    # and its judge (display only; labels, overrides and the depth are read
    # by no plan, scheduling, projection or serving path); the judge's
    # metered spend a UTC day.
    _ConfigRule(_exact(
        "reading_paths.enabled",
    ), "structural", "operational",
        "kill switch for the Guide's reading path (section labels, reasons, overrides, one exercise per core "
        "section, the suggested next line) and its judge call; display only, no measurement, scheduling or "
        "serving authority (no algorithm successor)."),
    _ConfigRule(_exact(
        "reading_paths.max_daily_cost_usd",
    ), "structural", "operational",
        "the reading-path judge's metered spend a UTC day, checked before the call; a spend bound, no "
        "measurement authority (path labels are display only)."),
    # Reader workbench RW7b (spec §10.2, G47): the kill switch of the
    # successor whose plan's reading block opens the next core or
    # prerequisite section of the reading path. A boolean (classified so
    # every new key has a rule); the rule is structural (the path's own
    # labels and the learner's overrides decide, no weight, margin or
    # threshold to learn). Off restores the predecessor's reading block
    # exactly.
    _ConfigRule(_exact(
        "reading_paths.plan_uses_path",
    ), "structural", "operational",
        "kill switch for RW7b's successor: the plan's reading block opens the next unfinished core or "
        "prerequisite section of the learner's reading path (read it anyway counts as core, skip it and "
        "enrichment are never planned); off, the predecessor's reading order exactly."),
    # Deliverable curriculum C0a: section coverage and reader.correspondents.
    # The switch is a boolean (classified so every new key has a rule); the
    # two dollar caps are spend guardrails (`keep`: unapproved spend is the
    # realistic harm) and the prompt bound is the context window's, as
    # source_service.compare_max_prompt_tokens. None is a model or decision
    # parameter: coverage is display and retrieval context only.
    _ConfigRule(_exact(
        "curriculum.enabled",
    ), "structural", "operational",
        "kill switch for section coverage (the coverage judge, learnloop curriculum cover, the learner's "
        "corrections) and reader.correspondents; display and retrieval context only, no measurement, "
        "scheduling or serving authority (no algorithm successor)."),
    _ConfigRule(_exact(
        "curriculum.max_daily_cost_usd",
        "curriculum.cover_max_cost_usd",
    ), "structural", "operational",
        "keep: the coverage judge's metered spend a UTC day and per owner-run cover batch, checked before "
        "each call; spend bounds with no measurement authority (coverage rows are display only)."),
    _ConfigRule(_exact(
        "curriculum.max_prompt_tokens",
    ), "structural", "operational",
        "keep: one coverage judgment's prompt bound (the context window), shared equally by the candidate "
        "sections' passages; a size bound, never a threshold on any score."),
    # Reader CA5a (ux_reader_compare_ask_v1 §6.2, §13): "find this section in
    # my other books". A boolean (classified so every new key has a rule):
    # the Guide's pressed action over reader.correspondents' unchecked search
    # hits; navigation and display, with no weight, margin or threshold (the
    # hits keep the search's own order and C0a's per-source bound).
    _ConfigRule(_exact(
        "reader.correspondence.enabled",
    ), "structural", "operational",
        "kill switch for Reader CA5a's find this section in my other books (the Guide's pressed action: "
        "unchecked search hits by book, peek, go there, compare, not about this); navigation and display, "
        "no measurement, scheduling or serving authority (no algorithm successor)."),
    # Reader CA5 (ux_reader_compare_ask_v1 §6.2): the learner's off switch on
    # the Guide's "also in your books" line (hide everywhere, hide for these
    # books). A boolean and a list of source ids (classified so every new key
    # has a rule): preferences, with no weight, margin or threshold.
    _ConfigRule(_exact(
        "reader.correspondence.hide_everywhere",
        "reader.correspondence.hidden_sources",
    ), "structural", "operational",
        "the learner's own hide preferences for Reader CA5's also in your books line (everywhere / for these "
        "books); display only, no measurement, scheduling or serving authority (no algorithm successor)."),
    # Deliverable curriculum C0b: the on-extract coverage job's switch (a
    # boolean, classified so every new key has a rule). The scope resolver
    # and the path judge add no number: they share the C0a caps above.
    _ConfigRule(_exact(
        "curriculum.coverage_on_extract",
    ), "structural", "operational",
        "kill switch for the background job a completed extraction queues to judge the already-covered LOs "
        "again (quiet: plan only); display and retrieval context only, no measurement, scheduling or serving "
        "authority (no algorithm successor)."),
    # Deliverable curriculum C2 (spec §10, §12 C2; C2b: the vault's own notes):
    # notes in the learner's voice, linked. One boolean (classified so every
    # new key has a rule) and one `keep` bound: the notes one judgment reads (a
    # prompt bound). None is a model or decision parameter: links are display
    # and learner-voice records, never evidence, and which note discusses what
    # is the model's judgment. (C2's tend adapter keys are gone; a legacy
    # tend table under [notes] is ignored.)
    _ConfigRule(_exact(
        "notes.enabled",
    ), "structural", "operational",
        "kill switch for curriculum C2's notes (the vault notes search, the note link judge, the margin marks, "
        "path lines and Compare's your-take band); display and learner-voice records, no measurement, "
        "scheduling or serving authority (no algorithm successor)."),
    _ConfigRule(_exact(
        "notes.max_candidates",
    ), "structural", "operational",
        "keep: the notes one note link judgment reads (a prompt bound); a size bound, never a threshold on "
        "any score."),
    # Deliverable curriculum C5 (spec §10.2, §12 C5): notes as learner text. One
    # boolean, the learner's opt-in (owner Q9: off by default): a linked note is
    # then a tier-2 learner-text-gaps input, read like any other learner text. No
    # number: which gap a note names is the model's judgment.
    _ConfigRule(_exact(
        "notes.gaps_enabled",
    ), "structural", "operational",
        "the learner's opt-in (default off) for curriculum C5: a linked note (a standing proposal or the "
        "learner's own link, never a hidden one) is read for gaps on the ChatGPT plan only, as tier-2 learner "
        "text that steers hypotheses and suggestions; never mastery, evidence or grading (no algorithm "
        "successor)."),
    # Reader CA6 (ux_reader_compare_ask_v1 §6.4, §13): side by side. A boolean
    # (classified so every new key has a rule): two panes, follow along at
    # section crossings to the first judged correspondent in the API's order;
    # no weight, margin or threshold (the narrow-window breakpoint is the
    # spec's layout bound in the frontend, not a parameter of any decision).
    _ConfigRule(_exact(
        "reader.side_by_side.enabled",
    ), "structural", "operational",
        "kill switch for Reader CA6's side by side (two source panes, follow along at section crossings, "
        "exposure rows for the second pane's text); navigation and display, no measurement, scheduling or "
        "serving authority (no algorithm successor)."),
    # Deliverable curriculum C1 (mvp-0.40; spec §7.6): the kill switch of the
    # successor whose plan reading block follows the nearest deliverable's
    # path. A boolean (classified so every new key has a rule); which section
    # is read is the path judge's order and the existing filters, so no
    # weight, margin or threshold is added. Off restores RW7b's plans exactly;
    # replay never reads it.
    _ConfigRule(_exact(
        "curriculum.plan_uses_path",
    ), "structural", "operational",
        "kill switch for curriculum C1's successor: the plan's reading block opens the next unfinished core or "
        "prerequisite section in the nearest active deliverable's fresh path order, in whichever book (the "
        "front-matter rule, exam filter and DL2's reading_allowed first); off, RW7b's plans byte for byte. "
        "Never read by replay."),
    # Deliverable curriculum C3 (spec §9.2): the kill switch of the scope
    # resolver's past-papers input. A boolean (classified so every new key has
    # a rule); which topics count is the exam predicate's partition (held out
    # or not) and the LOs' own provenance, so no weight, margin or threshold
    # is added. Off restores C0b's resolution byte for byte.
    _ConfigRule(_exact(
        "curriculum.exam_units_in_scope",
    ), "structural", "operational",
        "kill switch for curriculum C3's past-papers scope input: the ids (never the text) of the topics "
        "practice-available exam and problem-set units map to are read by the deliverable scope resolver; "
        "held-out units contribute nothing. Off, C0b's resolution byte for byte. Scoping display and proposals "
        "only, no measurement, scheduling or serving authority (no algorithm successor)."),
    # Reader CA2 (ux_reader_compare_ask_v1 §7, §13): the one Ask panel's
    # presentation switch and the kill switch of its successor's one help
    # rule. Booleans (classified so every new key has a rule); the rules are
    # structural: the tutor model's typed question_type decides what counts
    # (HINT_EQUIVALENT_TYPES, the existing mapping) and taking help converts
    # a cold attempt by construction; no weight, margin or threshold to learn.
    _ConfigRule(_exact(
        "ask.panel_enabled",
    ), "structural", "operational",
        "kill switch for Reader CA2's one Ask panel (docked in practice, inline per step, the help style as "
        "Ask's mode, the attempt's own thread, earlier on this question); off, the overlay and the Reader's "
        "per-source answer mode exactly as before."),
    _ConfigRule(_exact(
        "ask.cold_help_converts",
    ), "structural", "operational",
        "kill switch for Reader CA2's successor: on a check on your own only a substantive question (the "
        "tutor's question_type) counts as help on every path, and help taken on a cold follow-up makes the "
        "attempt practice with help instead of a refused submit; off, the predecessor's rules exactly."),
    # Reader workbench RW5a: explorable figures. The kill switches (booleans,
    # so Inventory A's numeric walk never reaches them; classified so every
    # new key has a rule) and the two routes' metered spend a UTC day and the
    # owner's price. Figures are content and their predictions formative:
    # nothing in scoring, scheduling, projection or serving reads them (W1).
    _ConfigRule(_exact(
        "figures.enabled",
        "figures.predictions_enabled",
        "figures.region_enabled",
        "figures.revisions_enabled",
    ), "structural", "operational",
        "kill switches for explorable figures / their predictions / region selection / \"not right?\" "
        "versions; on-off availability of content and formative records, no measurement, scheduling or "
        "serving authority."),
    # Reader workbench RW5b: the advanced panels (heat maps, vector fields,
    # trajectories, iterated maps) and figures offered by the organizer and
    # the tutor in the calls they already make. Kill switches over content.
    _ConfigRule(_exact(
        "figures.advanced_panels_enabled",
        "figures.offers_enabled",
    ), "structural", "operational",
        "kill switches for RW5b's figure panels / \"make this explorable\" offers on organizer and tutor "
        "citations; on-off availability of content, no measurement, scheduling or serving authority."),
    # Reader RW5d P1: "show me" (the learner's words, with or without a
    # passage; the tutor's optional figure goal). A kill switch over content.
    # Reader RW5d P2: the sketch tier (sealed, verified simulations). A kill
    # switch over content.
    _ConfigRule(_exact(
        "figures.sketch_enabled",
    ), "structural", "operational",
        "kill switch for RW5d's sketch tier (a sealed, verified simulation when the figure grammar can't express "
        "an idea); on-off availability of content, no measurement, scheduling or serving authority."),
    # Reader RW5d P2b: the rich tiers (a narrated Manim figure; JS behind its
    # build flag). A kill switch over content, and the learner's standing
    # opt-in for running AI-written animation code in the sandbox (a
    # permission and its date, not a number).
    _ConfigRule(_exact(
        "figures.rich_tiers_enabled",
        "figures.manim_opt_in",
        "figures.manim_opt_in_at",
    ), "structural", "operational",
        "kill switch for RW5d's rich tiers (a narrated Manim animation built from the author's brief) / the "
        "learner's standing opt-in to render AI-written animation code in the sandbox and its date; on-off "
        "availability of content and a permission, no measurement, scheduling or serving authority."),
    # Reader RW5d P3: figures as a help kind inside attempts. A kill switch over help content.
    _ConfigRule(_exact(
        "figures.help_kind_enabled",
    ), "structural", "operational",
        "kill switch for figures inside an open attempt (show me on practice, feedback and the workbench with "
        "its cost line, the cold take step, the chooser's explore_figure, figure in the help outcomes); a "
        "figure adds one hint-equivalent through the existing fold (hints_used's existing meaning), so this "
        "switch decides which help is offered, never a weight, margin or threshold."),
    # Learner data-relax 2: the figure author's learner state. A kill switch over content.
    _ConfigRule(_exact(
        "figures.author_learner_state",
    ), "structural", "operational",
        "kill switch for sending the figure author the learner's state on the passage's topics (status in words, "
        "open statements, two recent answers, protected work never); on-off availability of context for help "
        "content, no measurement, scheduling or serving authority."),
    # Reader RW5c P1: the kill switch over "matches the book's equation (checked)".
    _ConfigRule(_exact(
        "figures.checked_labels_enabled",
    ), "structural", "operational",
        "kill switch for RW5c's code-only source check and code-owned labels on a checked figure; on-off "
        "availability of a content label, no measurement, scheduling or serving authority (never evidence)."),
    _ConfigRule(_exact(
        "figures.show_me_enabled",
    ), "structural", "operational",
        "kill switch for RW5d's \"show me\" (figure goals in the learner's words, grounding in their books, "
        "the tutor's figure_goal button); on-off availability of content, no measurement, scheduling or "
        "serving authority."),
    # Reader RW5d P5 (spec §10b.4, §15): figures ahead of need. A kill switch and two
    # `keep` caps (guardrails that cut the queue in EU order, never admit a candidate).
    _ConfigRule(_exact(
        "figures.prefetch_enabled",
    ), "structural", "operational",
        "kill switch for figures built ahead of need (background, plan only, mains only, never exam material); "
        "which content exists sooner, no measurement, scheduling or serving authority (a figure never grades)."),
    _ConfigRule(_exact(
        "figures.prefetch.max_daily_builds",
        "figures.prefetch.max_daily_render_minutes",
    ), "structural", "constraint",
        "keep (spec §15, Q24): plan headroom spent on speculation a day / wall-clock minutes of background "
        "Manim renders a day; guardrails that cut the prebuild queue in expected-utility order, never a weight, "
        "margin or threshold."),
    _ConfigRule(_exact(
        "figures.max_daily_cost_usd",
        "figures.price_per_million",
    ), "structural", "operational",
        "the figure author's and verifier's metered spend a UTC day / the owner's price for a metered figure "
        "route; money bounds, no measurement authority (a figure never grades)."),
    # UX Phase 2: the shell's kill switch (a string enum, so Inventory A's
    # numeric walk never reaches it; classified here so every new key has a
    # rule, Codex review of ux-phase2-shell F9). Only the app snapshot reads
    # it; the desktop draws one shell or the other.
    _ConfigRule(_exact(
        "ui.shell",
    ), "structural", "operational",
        "kill switch for the desktop shell (\"simple\": four places, Under the hood, notices, the palette's "
        "> prefix; \"classic\": the ten tabs as before); display only, read by the app snapshot alone, no "
        "measurement, scheduling, serving or replay authority (no algorithm successor)."),
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
    # The owner's price for a metered LLM route of these roles is null by
    # default, so the default-config audit never sees it as a numeric leaf;
    # a configured price is one (Codex review F7).
    # Router objective RO2: the llm_history_v1 card's size bound (keep; UTF-8 bytes, an upper bound on
    # tokens): over it, entries are trimmed oldest first within each rung and the card says so.
    _ConfigRule(_exact("adaptive_difficulty.history_card_token_budget"), "structural", "operational",
        "keep: the full-history forecaster's card size bound in UTF-8 bytes (an upper bound on its tokens); a "
        "prompt and spend bound, never a judgement; receipts only (spec_router_objective_v1 6.3)."),
    _ConfigRule(_exact(
        "adaptive_difficulty.daily_spend_cap_usd",
        "adaptive_difficulty.price_per_million",
    ), "structural", "operational",
        "the outside forecasters' and feature audit's metered spend a UTC day / the owner's price (USD per "
        "million tokens) for a metered LLM route of these roles; a money bound and its rate, no measurement "
        "authority (AD1 logs forecasts and audits, it decides nothing served)."),
    # Adaptive difficulty AD2+AD3 (mvp-0.30): the selection rule's band and
    # overlap intervals, overlap share, near-tie margin and calibrate trigger
    # (D1, D6; pre-registered, docs/reviews/adaptive-difficulty-ad23.md §1.2)
    # decide which existing item a planned new-material slot serves, with
    # exact logged propensities; the readiness line's threshold labels a
    # prediction. Never evidence, mastery, FSRS or certification (A2, A11).
    _ConfigRule(_exact(
        "adaptive_difficulty.practice_band", "adaptive_difficulty.overlap_band",
        "adaptive_difficulty.overlap_share", "adaptive_difficulty.near_tie_margin",
        "adaptive_difficulty.calibrate_below", "adaptive_difficulty.ready_threshold",
    ), "decision", "threshold",
        "AD's practice draw: the 70-80% band (D1), the acceptable-success overlap interval and its share "
        "(D6), the near-tie margin, the band-mode trigger and the 'likely ready' threshold; a serving draw "
        "with exact propensities and a labelled prediction, never evidence or certification (A2, A11)."),
    # Adaptive difficulty AD2+AD3 (owner decision 2026-10-19): which historical
    # attempts AD's replay reads. "current_content" (the default) reads an
    # attempt whose exact item revision was not saved against today's item
    # text; "exclude" leaves it out. AD's own key: field.legacy_fallback (the
    # field harness and its projections) is unchanged. A string leaf, so the
    # numeric walk never sees it: registered through ENUM_DECISION_LEAVES.
    _ConfigRule(_exact(
        "adaptive_difficulty.history_fallback",
    ), "decision", "constraint",
        "which historical attempts enter AD's replay: those without a saved item revision read against "
        "today's item text (current_content, the default) or left out (exclude); membership of AD's serving "
        "state only, never evidence, mastery, FSRS or certification (A2); field.legacy_fallback unchanged."),
    # Teacher TE3a (mvp-0.50 on its branch; spec_teacher_v1 rev 5 §14.2): the AD lesson opportunity's kill
    # switch. Its curve's prior (adaptive_difficulty.priors.LESSON_PRIORS, ad_lesson_priors_v1) is derived, not
    # chosen: centred and spread on RO4's placeholder (AD's gamma prior times the teacher's seeded lesson-check mass
    # 0.5, basis legacy), shaped by AD's existing rule for a new kind's prior; the filter learns it.
    _ConfigRule(_exact("adaptive_difficulty.lesson_opportunities"), "structural", "operational",
        "kill switch for TE3a's AD successor: a closed lesson's landed or taught node raises AD's predicted level "
        "by its subkind's learned dose curve and the objective's lesson interface reads it; off, the predecessor "
        "exactly and RO4's placeholder (prediction only, never evidence: A2, A12)."),
    # Adaptive difficulty AD2+AD3 (D21, outside the successor): the Reader's
    # randomized dose offers' floor per variant and daily friction budget. They
    # decide what the Reader may offer (an extra worked example or question),
    # never evidence; the propensities are logged before anything is shown.
    _ConfigRule(_exact(
        "adaptive_difficulty.dose_floor", "adaptive_difficulty.dose_daily_offers",
    ), "decision", "shaping_weight",
        "the dose arm's per-variant offer probability (D21's floor) and its offers a day (the friction "
        "budget); a randomized offer with exact logged propensities, never evidence (A12)."),
    # Tutor delivery fixes (2026-10-13): the source text one tutor turn reads
    # (a context-size bound) and one automatic source-block backfill's spend.
    _ConfigRule(_exact(
        "tutor_qa.context_token_budget",
        "embedding.source_backfill_max_cost_usd",
    ), "structural", "operational",
        "tutor context token budget / automatic source-block embedding backfill dollar cap; context and "
        "spend bounds, no measurement authority (delivery is context for one answer; vectors rank retrieval "
        "candidates only)."),
    # Local contextual retrieval P1 (spec_local_contextual_retrieval_v1 §9.6):
    # the local index batch wait, the fallback's per-run spend cap and its
    # published price. All keep: an operational default the owner tunes, the
    # owner's spending authority and a measured provider rate; none ranks.
    # Local contextual retrieval P2 (spec §7.1, §9.6): the query process's idle exit (how long the
    # student stays loaded, never ranking) and the generator's per-run money cap on a metered route
    # (the owner's spending authority, Q8). Both keep.
    _ConfigRule(_exact(
        "embedding.local.student_idle_minutes",
        "embedding.local.student_generator_max_cost_usd",
    ), "structural", "operational",
        "keep: the query student's idle exit (operational: how long the 4G query process stays loaded, never "
        "what it ranks) / the synthetic-question generator's dollar cap per run on a metered route (the "
        "owner's spending authority; the plan's quota costs $0); no measurement or serving authority."),
    _ConfigRule(_exact(
        "embedding.local.index_batch_minutes",
        "embedding.fallback.max_cost_usd_per_run",
        "embedding.fallback.price_per_million",
    ), "structural", "operational",
        "keep: the local index batch wait (how soon a new book is indexed, never ranking) / the Voyage fallback "
        "backfill's dollar cap per run (the owner's spending authority) / Voyage's published price per million "
        "tokens, admitted in full; no measurement or serving authority."),
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
    # LP-min (a) (spec_learned_parameters_v1 §3.0b item 1): the one kill switch
    # of the claim-fixes successor. A boolean with no weight behind it: the
    # fixes are structural (a claim applied at its own time, a mean-only warm
    # merge whose variance floor is the state's own variance, a recency-first
    # tie order), so there is no number to learn. Off restores the
    # predecessor's claim seed, re-anchor, merge, ranking and replay exactly.
    _ConfigRule(_exact("mastery.claim_fixes_enabled"), "structural", "operational",
                "kill switch for LP-min (a)'s successor: gap claims re-anchor, claims replay at their own time, "
                "a claim never lowers a variance, ties by recency then pseudo-count, the resolving review's claim "
                "line; off, the predecessor's claim handling."),
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
    # Daily-loop DL2 (intent; the successor mvp-0.29 behind intent.enabled and
    # intent.recall_targets_enabled, Codex re-review F2): the per-intent recall
    # targets (Q8, owner defaults accepted 2026-10-12, checkpoint open) scale
    # an effective due at serving time only; due_at is still written at 0.90
    # and nothing reaches evidence. The "Check once" delay is a timing default.
    _ConfigRule(_prefix("intent.recall_targets."), "decision", "threshold",
                "per-intent recall target (spec_daily_loop_v1 §5.3, Q8): when an item is served, as "
                "effective_due = anchor + (due_at - anchor) x ratio(target); serving only, never "
                "persisted state or evidence; kill switch intent.recall_targets_enabled."),
    _ConfigRule(_exact("capture.test_me_later_days"), "decision", "threshold",
                "how long a \"Check once\" waits before its one cold check when its commitment names no "
                "due_hint (spec_daily_loop_v1 §5.2); a serving date, never evidence."),
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

#: Boolean leaves registered for inventory only: structural, not decisions.
BOOLEAN_STRUCTURAL_LEAVES: tuple[str, ...] = (
    "router_objective.receipts",
)


#: String (enum) config leaves that are DECISIONS: like the booleans above, the
#: numeric walk skips them, so each is enumerated here.
ENUM_DECISION_LEAVES: tuple[str, ...] = (
    "adaptive_difficulty.history_fallback",
)


def _build_config_specs() -> None:
    for path in sorted(config_numeric_leaves().keys()):
        _register_config_path(path)
    for path in BOOLEAN_DECISION_LEAVES:
        if not _register_config_path(path):
            raise RuntimeError(
                f"boolean decision leaf {path} has no classification rule"
            )
    for path in ENUM_DECISION_LEAVES:
        if not _register_config_path(path):
            raise RuntimeError(
                f"enum decision leaf {path} has no classification rule"
            )
    for path in BOOLEAN_STRUCTURAL_LEAVES:
        if not _register_config_path(path):
            raise RuntimeError(
                f"boolean structural leaf {path} has no classification rule"
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
