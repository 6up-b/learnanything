"""P4 step 2 -- the transparent staged decision policy (spec §4, design B step 2).

Two levels (§4.1/§4.4): first choose one coherent 5-15 minute ATTENTION BLOCK, then
one activity inside it. The global staged rule (§4.2) is an explicit if/elif ladder
producing exactly ONE canonical action; there is no weighted sum. Every decision emits
a full inspectable trace (§3.3): the snapshot hash, the staged rule that fired, the
feasible set + exclusions, the ranking inputs, the chosen action, the constraint
manifest + version, and the decision-parameter hash. The learner-facing "why" is the
staged reason, never the largest opaque score term.

Discipline enforced here:
- ONE edge per decision. ``practice(depth_progression)`` records the predecessor
  milestone as reached, then calls ``depth_transition.commit_one_edge`` at most once;
  under the deferred U-018 gate it returns a ``suggest_next`` proposal (activates
  nothing).
- AFFECT checks (U-011) are evaluated BEFORE any depth edge is considered/committed.
- Constraints define feasibility; NO score trades a hard constraint (§4.4, invariant 1).
- The legacy scheduler weighted sum (``scheduler._priority`` /
  ``selection_rewards.score_selection_reward``) is recorded as a LOGGED COMPARATOR on
  the trace, never authority for the staged choice (design §B4).
- Shadow scorers/kernels have ZERO authority (invariant 3): their output is persisted
  and joined to the snapshot hash, and is never consulted to order/select/stop.

For all of P4 steps 1-2 the policy runs in ``shadow`` mode: it logs a next-action
recommendation beside the live scheduler and drives P2 golden-path runs' next-action
recommendations, but composes no live Today work. Making it live for P2 runs is the
§14.2 cutover (a later step).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Callable, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services import action_loss as AL
from learnloop.services import constraint_engine as ce
from learnloop.services import controller_actions as A
from learnloop.services import controller_snapshot as cs
from learnloop.services import controller_store as store
from learnloop.services import depth_transition as DT
from learnloop.services import evsi as EV
from learnloop.services import randomization_layer as RL
from learnloop.vault.models import LoadedVault

STAGED_POLICY_VERSION = 1

# Attention-block bounds (§4.1) and the once-per-block context-switch cost (§4.1).
# Heuristic decision parameters (design §E).
ATTENTION_BLOCK_MIN_MINUTES = 5
ATTENTION_BLOCK_MAX_MINUTES = 15
DEFAULT_BLOCK_BUDGET_MINUTES = 10
CONTEXT_SWITCH_COST_MINUTES = 1.0

# Repeated-negative-affect count that downgrades ``auto_within_envelope`` to
# ``suggest_next`` before an edge commits (U-011). Heuristic.
NEGATIVE_AFFECT_DOWNGRADE_THRESHOLD = 2

# Short-session adapter (§12.2). When the session's available minutes fall BELOW the
# 5-minute lower bound, the SAME block planner runs but the block is planned to COMPLETE
# within the available minutes: one activity is the whole block, never a dangling
# multi-activity block. The block budget is then the available minutes -- a documented
# exception that COMPOSES the registered attention-block bounds (it never exceeds the max
# and only drops below the min for an explicitly short session). Heuristic.
SHORT_SESSION_MAX_MINUTES = ATTENTION_BLOCK_MIN_MINUTES

# The admitted short P1 patterns a short session PREFERS among the feasible set (§12.2):
# whichever fits the conservative duration bound the constraint engine already enforced.
# Structural vocabulary (P1 pattern ids), not a tunable reward term.
SHORT_SESSION_PREFERRED_PATTERNS: tuple[str, ...] = (
    "setup_only", "example_completion", "example_comparison",
)

# Purpose sets each canonical action is compatible with (feasible-set gate, §5).
_ACTION_PURPOSES: dict[str, tuple[str, ...]] = {
    A.MEASURE_DIAGNOSTIC: ("diagnostic",),
    A.INSTRUCT: ("instructional", "practice"),
    A.PRACTICE: ("practice",),
    A.ASSESS_TERMINAL: ("assessment",),
    A.MAINTAIN: ("practice",),
    A.EXPAND_MODEL: (),
    A.STOP: (),
}


@dataclass(frozen=True)
class AttentionBlock:
    """One coherent 5-15 minute block (§4.1)."""

    action: str
    subtype: str | None
    commitment_id: str | None
    budget_minutes: float
    compatible_purposes: tuple[str, ...]
    neighborhood: dict[str, Any] = field(default_factory=dict)
    exit_rules: tuple[str, ...] = ()
    short_circuit_reason: str | None = None
    # P4 step 4 -- the stage this block is at, for stage-aware interleaving (§9.2).
    # None (unstaged) leaves interleaving inert.
    stage: str | None = None

    def content_hash(self) -> str:
        from learnloop.services.activities import _canonical_hash

        return _canonical_hash({
            "action": self.action, "subtype": self.subtype,
            "commitment_id": self.commitment_id, "budget_minutes": self.budget_minutes,
            "compatible_purposes": list(self.compatible_purposes),
            "neighborhood": dict(sorted(self.neighborhood.items())),
            "exit_rules": list(self.exit_rules),
            "short_circuit_reason": self.short_circuit_reason,
            "stage": self.stage,
        })


@dataclass(frozen=True)
class StagedIntent:
    """The one canonical action the §4.2 ladder produced, and which rung fired."""

    action: str
    subtype: str | None
    staged_rule: str
    commitment_id: str | None = None
    stop_reason: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class StateSignals:
    """Decision-relevant state signals feeding the §4.2 ladder. Supplied by the caller
    (the golden-path run / triage) or planted in tests. Absent signals fail safe: the
    ladder falls through to ``stop`` rather than inventing certainty (§14.4)."""

    pending_triage_route: dict[str, Any] | None = None
    model_misspecified: bool = False
    decision_relevant_robust_value: float = 0.0
    target_acquired: bool = True
    capability_fragile: bool = False
    integration_failing: bool = False
    terminal_required_unshown: bool = False
    terminal_reserve_valid: bool = False
    milestone_reached: str | None = None
    milestone_evidence_receipt: dict[str, Any] | None = None
    retention_near_limit: bool = False
    goal_satisfied: bool = False


def is_short_session(snapshot: cs.ControllerSnapshot) -> bool:
    """A short session (§12.2): available minutes are known and below the 5-min lower
    bound of the coherent attention block. The block then plans to complete within them."""

    remaining = snapshot.remaining_minutes
    return remaining is not None and remaining < float(SHORT_SESSION_MAX_MINUTES)


def _block_budget(snapshot: cs.ControllerSnapshot) -> float:
    remaining = snapshot.remaining_minutes
    if remaining is not None and remaining < float(ATTENTION_BLOCK_MIN_MINUTES):
        # Short session (§12.2): the block COMPLETES within the available minutes; the one
        # completing activity is the whole block. The budget is the available minutes -- a
        # documented exception BELOW the lower bound, never clamped UP to 5 (which would
        # plan a block the session cannot finish).
        return max(0.0, float(remaining))
    budget = float(DEFAULT_BLOCK_BUDGET_MINUTES)
    if remaining is not None:
        budget = min(budget, max(float(ATTENTION_BLOCK_MIN_MINUTES), remaining))
    return max(float(ATTENTION_BLOCK_MIN_MINUTES), min(float(ATTENTION_BLOCK_MAX_MINUTES), budget))


def _as_short_block(block: AttentionBlock, snapshot: cs.ControllerSnapshot) -> AttentionBlock:
    """Mark a block as a short-session completing block (§12.2): one completed activity
    ends the session, so its single exit rule is ``session_complete_on_one_activity`` and
    its neighborhood records the short-session budget. The 5-15 min bounds still frame it
    (the budget composes them); it just drops below the lower bound for this session."""

    return replace(
        block,
        exit_rules=("session_complete_on_one_activity",),
        neighborhood={
            **block.neighborhood,
            "short_session": True,
            "available_minutes": snapshot.remaining_minutes,
            "block_bounds_minutes": [ATTENTION_BLOCK_MIN_MINUTES, ATTENTION_BLOCK_MAX_MINUTES],
        },
    )


def _pick_commitment(snapshot: cs.ControllerSnapshot, *, want_auto: bool = False) -> cs.CommitmentSummary | None:
    for c in snapshot.commitments:
        if c.disposition not in ("active", "one_check_pending"):
            continue
        if want_auto and c.depth_policy != "auto_within_envelope":
            continue
        return c
    return None


def _feasible_reviewed_edge(commitment: cs.CommitmentSummary, milestone: str) -> dict[str, Any] | None:
    """A reviewed edge originating at the reached milestone, wholly inside the
    envelope (§5 depth constraints, structural). Missing/stale -> None (excludes)."""

    for edge in commitment.reviewed_edges:
        if not edge.get("reviewed"):
            continue
        if edge.get("outside_envelope"):
            continue
        frm = edge.get("from_milestone") or edge.get("predecessor_milestone")
        if frm == milestone and edge.get("edge_id"):
            return edge
    return None


def evaluate_staged_rule(
    snapshot: cs.ControllerSnapshot, signals: StateSignals
) -> StagedIntent:
    """The §4.2 global staged rule as an explicit if/elif ladder. Produces exactly one
    canonical action and records which rung fired."""

    commitment = _pick_commitment(snapshot)
    cid = commitment.commitment_id if commitment is not None else None

    # 1. a valid failure triage already determines the next repair.
    route = signals.pending_triage_route
    if route:
        stage = route.get("first_intervention") or route.get("ladder_entry_stage")
        if stage in ("instruct", "explain", "compare"):
            return StagedIntent(A.INSTRUCT, None, "triage_determined_instruct", cid, detail={"route": route})
        return StagedIntent(
            A.PRACTICE, A.COMPLETION_OR_REPAIR, "triage_determined_repair", cid,
            detail={"route": route},
        )

    # 2. model misspecification prevents an action-safe conclusion.
    if signals.model_misspecified:
        return StagedIntent(A.EXPAND_MODEL, None, "model_misspecification", cid)

    # 3. decision-relevant uncertainty has positive robust sampling value.
    if signals.decision_relevant_robust_value > 0.0:
        return StagedIntent(A.MEASURE_DIAGNOSTIC, None, "positive_robust_measurement_value", cid)

    # 4. target knowledge is not acquired.
    if not signals.target_acquired:
        return StagedIntent(A.INSTRUCT, None, "target_not_acquired", cid)

    # 5. capability is scaffold-dependent or fragile.
    if signals.capability_fragile:
        return StagedIntent(A.PRACTICE, A.COMPLETION_OR_REPAIR, "capability_fragile", cid)

    # 6. components present but whole-task integration fails.
    if signals.integration_failing:
        return StagedIntent(A.PRACTICE, A.INTEGRATION, "integration_failing", cid)

    # 7. terminal performance required, not shown, and a valid reserve exists.
    if signals.terminal_required_unshown and signals.terminal_reserve_valid:
        return StagedIntent(A.ASSESS_TERMINAL, None, "terminal_required_with_reserve", cid)

    # 8. milestone reached, policy auto_within_envelope, one reviewed next edge feasible.
    if signals.milestone_reached and commitment is not None:
        auto = _pick_commitment(snapshot, want_auto=True)
        if auto is not None:
            edge = _feasible_reviewed_edge(auto, signals.milestone_reached)
            if edge is not None:
                return StagedIntent(
                    A.PRACTICE, A.DEPTH_PROGRESSION, "depth_progression_edge_feasible",
                    auto.commitment_id,
                    detail={"edge_id": edge["edge_id"], "milestone": signals.milestone_reached},
                )

    # 9. retention approaching its contract limit.
    if signals.retention_near_limit:
        return StagedIntent(A.MAINTAIN, None, "retention_near_limit", cid)

    # else: stop or propose a depth-envelope successor.
    if signals.goal_satisfied:
        return StagedIntent(
            A.STOP, A.STOP_GOAL_SATISFIED, "goal_satisfied", cid,
            stop_reason=A.STOP_GOAL_SATISFIED,
        )
    return StagedIntent(
        A.STOP, A.STOP_NO_POSITIVE_ROBUST_VALUE, "no_positive_value_stop", cid,
        stop_reason=A.STOP_NO_POSITIVE_ROBUST_VALUE,
    )


def choose_block(
    snapshot: cs.ControllerSnapshot,
    signals: StateSignals,
    *,
    continuation: Mapping[str, Any] | None = None,
    explicit_choice: Mapping[str, Any] | None = None,
    served_administration: Mapping[str, Any] | None = None,
) -> tuple[AttentionBlock, StagedIntent]:
    """Level one (§4.1). Continuation / explicit learner choice / served administration
    short-circuit FIRST and are logged as such; otherwise the global staged rule
    chooses the coherent neighborhood. Context-switch cost is charged here, once."""

    budget = _block_budget(snapshot)

    if served_administration is not None:
        action = served_administration.get("action", A.PRACTICE)
        block = AttentionBlock(
            action=action, subtype=served_administration.get("subtype"),
            commitment_id=served_administration.get("commitment_id"),
            budget_minutes=budget, compatible_purposes=_ACTION_PURPOSES.get(action, ()),
            neighborhood={"source": "served_administration"},
            exit_rules=("administration_complete",),
            short_circuit_reason="served_administration",
        )
        intent = StagedIntent(action, block.subtype, "served_administration_wins", block.commitment_id)
        return block, intent

    if explicit_choice is not None:
        action = explicit_choice.get("action", A.PRACTICE)
        block = AttentionBlock(
            action=action, subtype=explicit_choice.get("subtype"),
            commitment_id=explicit_choice.get("commitment_id"),
            budget_minutes=budget, compatible_purposes=_ACTION_PURPOSES.get(action, ()),
            neighborhood={"source": "explicit_learner_choice"},
            exit_rules=("learner_exit", "budget_exhausted"),
            short_circuit_reason="explicit_learner_choice",
        )
        intent = StagedIntent(action, block.subtype, "explicit_learner_choice", block.commitment_id)
        return block, intent

    if continuation is not None:
        action = continuation.get("action", A.PRACTICE)
        block = AttentionBlock(
            action=action, subtype=continuation.get("subtype"),
            commitment_id=continuation.get("commitment_id"),
            budget_minutes=budget, compatible_purposes=_ACTION_PURPOSES.get(action, ()),
            neighborhood={"source": "continuation"},
            exit_rules=("budget_exhausted",), short_circuit_reason="continuation",
        )
        intent = StagedIntent(action, block.subtype, "continuation", block.commitment_id)
        return block, intent

    intent = evaluate_staged_rule(snapshot, signals)
    block = AttentionBlock(
        action=intent.action, subtype=intent.subtype, commitment_id=intent.commitment_id,
        budget_minutes=budget, compatible_purposes=_ACTION_PURPOSES.get(intent.action, ()),
        neighborhood={"source": "staged_rule", "staged_rule": intent.staged_rule},
        exit_rules=("budget_exhausted", "fatigue", "state_change", "learner_action"),
    )
    if is_short_session(snapshot):
        block = _as_short_block(block, snapshot)
    return block, intent


@dataclass
class DiagnosticSelector:
    """P4 step 3 within-block ranking context (§6.4). Supplies the minutes-denominated
    loss table + per-candidate credible-set ``P(E|H)`` matrices so a
    ``measure_diagnostic`` block ranks feasible questions by robust EVSI per minute --
    strictly WITHIN the feasible set the constraint engine already gated. Absent, the
    block falls back to the transparent due-order selector."""

    loss_table: AL.LossTable
    # candidate_ref -> (members, prior, expected_minutes, burden_minutes)
    candidates: Mapping[str, dict[str, Any]]
    experiment_id: str | None = None
    seed: str | None = None
    randomize: bool = False


def _select_within_block(
    block: AttentionBlock,
    report: ce.FeasibilityReport,
    snapshot: cs.ControllerSnapshot | None = None,
) -> tuple[cs.Candidate | None, str, list[tuple[cs.Candidate, int]]]:
    """Level two (§4.4): apply the block-specific TRANSPARENT selector over the
    feasible set. No score trades a constraint (the feasible set is already gated).
    Returns (chosen, selector_name, ranked). This is the due-order / stage-order
    fallback; a ``measure_diagnostic`` block with a :class:`DiagnosticSelector` uses the
    robust-EVSI-per-minute selector (:func:`_select_diagnostic`) instead.

    In a short session (§12.2) the selector PREFERS the admitted short P1 patterns whose
    conservative duration already fit the budget (the constraint engine's fatigue gate
    guarantees every feasible candidate fits), then falls back to due order. The chosen
    single activity IS the whole block -- one completed activity completes the session."""

    if not report.feasible:
        return None, "empty_feasible_set", []

    def due_key(c: cs.Candidate) -> tuple[Any, str]:
        return (c.due_at or "9999", c.candidate_ref)

    if snapshot is not None and is_short_session(snapshot):
        selector = "short_session_preferred_pattern"

        def short_key(c: cs.Candidate) -> tuple[int, Any, str]:
            preferred = 0 if c.practice_mode in SHORT_SESSION_PREFERRED_PATTERNS else 1
            return (preferred, c.due_at or "9999", c.candidate_ref)

        ranked_candidates = sorted(report.feasible, key=short_key)
    else:
        selector = "due_order"
        ranked_candidates = sorted(report.feasible, key=due_key)
    ranked = [(c, i + 1) for i, c in enumerate(ranked_candidates)]
    return ranked_candidates[0], selector, ranked


def _tiebreak_seed(snapshot_hash: str, experiment_id: str, refs: Sequence[str]) -> str:
    """The decision-specific ε tie-break seed (audit M2/F4): derived from the snapshot
    hash + experiment id + the tied candidate refs so two DIFFERENT decisions draw
    differently while the SAME decision replays to the same draw. Never a static constant
    (which would apply one fixed draw to every decision, a hidden deterministic bias)."""

    return "|".join(["evsi_tiebreak", snapshot_hash, experiment_id, *sorted(refs)])


def _select_diagnostic(
    report: ce.FeasibilityReport,
    diagnostic: DiagnosticSelector,
    *,
    repository: Repository | None,
    clock: Clock | None,
    snapshot_hash: str | None = None,
    decision_id: str | None = None,
) -> tuple[cs.Candidate | None, str, list[tuple[cs.Candidate, int]], EV.RankResult, dict[str, Any] | None]:
    """Robust-EVSI-per-minute selection over the feasible set (§6.4). Ranks ONLY the
    feasible candidates that carry diagnostic material; the constraint engine already
    defined feasibility, so a high EVSI can never resurrect an excluded candidate. When
    the top feasible candidates are near-equivalent, the single randomization layer
    (§9.3) breaks the tie with a logged propensity. Returns
    (chosen, selector, ranked, rank_result, assignment)."""

    by_ref = {c.candidate_ref: c for c in report.feasible}
    diag_candidates: list[EV.DiagnosticCandidate] = []
    for ref, c in by_ref.items():
        material = diagnostic.candidates.get(ref)
        if material is None:
            continue
        diag_candidates.append(
            EV.DiagnosticCandidate(
                ref=ref,
                members=tuple(material["members"]),
                prior=material["prior"],
                expected_minutes=float(material["expected_minutes"]),
                burden_minutes=float(material.get("burden_minutes", 0.0)),
            )
        )
    result = EV.rank_feasible(diag_candidates, diagnostic.loss_table)
    ranked_for_trace = [
        (by_ref[r.ref], r.ordinal) for r in result.ranked if r.ref in by_ref
    ]

    if result.verdict != "measure" or result.best_ref is None:
        # EVSI says stop or abstain -- no administration this decision (handled upstream
        # as a typed stop). Not a "no feasible activity": the feasible set is non-empty.
        return None, "robust_evsi_per_minute", ranked_for_trace, result, None

    chosen_ref = result.best_ref
    assignment_detail: dict[str, Any] | None = None
    if diagnostic.randomize and len(result.ranked) >= 2:
        refs = [r.ref for r in result.ranked]
        values = [r.rank_value for r in result.ranked]
        experiment_id = diagnostic.experiment_id or "within_block_evsi"
        # Refuse a static fallback seed (audit M2/F4): a decision-specific seed requires a
        # snapshot hash. An explicit seed on the selector is honored (a caller pinning a
        # replay); otherwise the seed is derived so it varies across decisions.
        if diagnostic.seed is not None:
            seed = diagnostic.seed
        elif snapshot_hash is not None:
            seed = _tiebreak_seed(snapshot_hash, experiment_id, refs)
        else:
            raise ValueError(
                "epsilon tie-break requires a decision-specific seed (snapshot_hash); "
                "refusing a static fallback seed"
            )
        assignment = RL.epsilon_tiebreak(
            repository, experiment_id=experiment_id,
            refs=refs, values=values, seed=seed, decision_id=decision_id, clock=clock,
        )
        if assignment.variant:
            chosen_ref = assignment.variant
        assignment_detail = assignment.as_dict()

    chosen = by_ref.get(chosen_ref)
    return chosen, "robust_evsi_per_minute", ranked_for_trace, result, assignment_detail


OWNERSHIP_REFUSAL_KEY = "controller_ownership"


def _apply_ownership(
    report: ce.FeasibilityReport, owned_item_refs: set[str]
) -> tuple[ce.FeasibilityReport, list[str]]:
    """Refuse every feasible candidate the staged controller does not own (§14.2 step 3).
    Returns a narrowed report + the refused refs. The refusal is a typed exclusion, so a
    non-owned item can never be selected and never trades against a score (invariant 1)."""

    refused: list[str] = []
    new_feasible: list[cs.Candidate] = []
    new_excluded = list(report.excluded)
    per_candidate = dict(report.per_candidate)
    for candidate in report.feasible:
        if candidate.candidate_ref in owned_item_refs:
            new_feasible.append(candidate)
            continue
        reason = ce.ExclusionReason(
            OWNERSHIP_REFUSAL_KEY, 1, "not_owned_by_staged_controller",
            {"candidate_ref": candidate.candidate_ref}, kind="exclude",
        )
        prior = per_candidate.get(candidate.candidate_ref)
        prior_exclusions = tuple(prior.exclusions) if prior is not None else ()
        feas = ce.Feasibility(candidate.candidate_ref, prior_exclusions + (reason,))
        per_candidate[candidate.candidate_ref] = feas
        new_excluded.append((candidate, feas))
        refused.append(candidate.candidate_ref)
    narrowed = ce.FeasibilityReport(
        feasible=new_feasible, excluded=new_excluded, per_candidate=per_candidate,
        manifest_hash=report.manifest_hash,
    )
    return narrowed, refused


def _affect_downgrade(snapshot: cs.ControllerSnapshot, commitment_id: str | None) -> dict[str, Any]:
    """U-011 affect check, evaluated BEFORE any depth edge is considered. Repeated
    negative affect on a commitment's families downgrades ``auto_within_envelope`` to
    ``suggest_next`` pending re-confirmation. The dead-man switch is calibrated (P0
    U-010 signal is live), and it never activates an edge on its own."""

    signal = snapshot.affect_by_commitment.get(commitment_id or "", {})
    negative = int(signal.get("negative_affect_count", 0))
    downgraded = negative >= NEGATIVE_AFFECT_DOWNGRADE_THRESHOLD
    return {
        "evaluated": True,
        "negative_affect_count": negative,
        "threshold": NEGATIVE_AFFECT_DOWNGRADE_THRESHOLD,
        "downgraded_auto_to_suggest_next": downgraded,
    }


def _comparator(
    vault: LoadedVault, repository: Repository, session: Any | None,
    feasible_refs: set[str],
) -> dict[str, Any] | None:
    """Run the LEGACY scheduler weighted sum in shadow and record its outputs for
    comparison only (design §B4). Never authority for the staged choice."""

    try:
        from learnloop.services.scheduler import build_due_queue

        slate = build_due_queue(vault, repository, session=session, persist_explanations=False)
    except Exception as exc:  # legacy comparator is advisory; its failure is inert
        return {"available": False, "error": type(exc).__name__}
    scores = {
        item.practice_item_id: {
            "priority": item.priority,
            "components": dict(getattr(item, "components", {}) or {}),
        }
        for item in slate
    }
    legacy_top = slate[0].practice_item_id if slate else None
    return {
        "available": True,
        "policy": "selection_reward_v1",
        "legacy_top": legacy_top,
        "scores": scores,
    }


def _run_shadow_scorers(
    scorers: Sequence[Callable[[cs.ControllerSnapshot, cs.Candidate | None], Any]] | None,
    snapshot: cs.ControllerSnapshot,
    chosen: cs.Candidate | None,
) -> list[dict[str, Any]]:
    """Evaluate injected shadow scorers with ZERO authority (invariant 3). A scorer
    that raises is recorded UNUSABLE; its output never reaches the decision."""

    out: list[dict[str, Any]] = []
    for i, scorer in enumerate(scorers or ()):
        try:
            value = scorer(snapshot, chosen)
            out.append({"scorer_kind": f"shadow_scorer_{i}", "prediction": {"value": value},
                        "usable": True})
        except Exception as exc:
            out.append({"scorer_kind": f"shadow_scorer_{i}",
                        "prediction": {"error": type(exc).__name__}, "usable": False})
    return out


@dataclass
class DecisionResult:
    decision_id: str
    already: bool
    action: str
    subtype: str | None
    staged_rule: str
    chosen_candidate_ref: str | None
    stop_reason: str | None
    snapshot_hash: str
    trace: dict[str, Any]
    feasibility: ce.FeasibilityReport | None = None
    block: AttentionBlock | None = None
    why: str = ""


def decide(
    vault: LoadedVault,
    repository: Repository,
    session: Any | None = None,
    *,
    signals: StateSignals | None = None,
    candidates: Sequence[cs.Candidate] | None = None,
    continuation: Mapping[str, Any] | None = None,
    explicit_choice: Mapping[str, Any] | None = None,
    served_administration: Mapping[str, Any] | None = None,
    receipt_key: str | None = None,
    shadow_scorers: Sequence[Callable[[cs.ControllerSnapshot, cs.Candidate | None], Any]] | None = None,
    record_comparator: bool = True,
    diagnostic: DiagnosticSelector | None = None,
    mode: str = "shadow",
    owned_item_refs: set[str] | None = None,
    clock: Clock | None = None,
) -> DecisionResult:
    """Run one staged decision end to end and persist its full trace (shadow mode).

    Order of operations (the trace's ``steps`` mirrors this exactly): snapshot ->
    block -> feasible set -> within-block selection -> AFFECT check -> at most one depth
    edge -> comparator (logged) -> persist. Idempotent on ``receipt_key``: a retry
    after commit returns the standing decision and the same candidate (§14.4)."""

    signals = signals or StateSignals()
    steps: list[dict[str, Any]] = []

    if receipt_key is not None:
        standing = store.decision_by_receipt_key(repository, receipt_key)
        if standing is not None:
            import json as _json_mod

            trace = _json_mod.loads(standing["trace_json"])
            return DecisionResult(
                decision_id=standing["id"], already=True, action=standing["action"],
                subtype=standing["subtype"], staged_rule=standing["staged_rule"],
                chosen_candidate_ref=standing["chosen_candidate_ref"],
                stop_reason=standing["stop_reason"], snapshot_hash=standing["snapshot_hash"],
                trace=trace, why=trace.get("why", ""),
            )

    snapshot = cs.build_snapshot(vault, repository, session, candidates=candidates, clock=clock)
    snapshot_id = cs.persist_snapshot(repository, snapshot, clock=clock)
    steps.append({"step": "snapshot", "snapshot_hash": snapshot.snapshot_hash})

    block, intent = choose_block(
        snapshot, signals, continuation=continuation, explicit_choice=explicit_choice,
        served_administration=served_administration,
    )
    steps.append({"step": "attention_block", "action": block.action, "subtype": block.subtype,
                  "short_circuit_reason": block.short_circuit_reason,
                  "budget_minutes": block.budget_minutes,
                  "context_switch_cost_minutes": CONTEXT_SWITCH_COST_MINUTES})

    # Level two: constraint engine defines the feasible set; scores rank only within.
    report = ce.feasible_set(
        list(snapshot.candidates), snapshot, block, repository=repository, clock=clock,
    )
    # P4 §14.2 step 3: in LIVE mode the staged policy owns exactly the commitment it was
    # handed; it REFUSES any item it does not own (design §A.2). A non-owned candidate is
    # moved out of the feasible set with a typed refusal -- never selected, never a rank
    # trade. In shadow mode ownership is inert (the whole universe is advisory).
    ownership_refusals: list[str] = []
    if mode == "live" and owned_item_refs is not None:
        report, ownership_refusals = _apply_ownership(report, owned_item_refs)
    steps.append({
        "step": "feasible_set", "manifest_hash": report.manifest_hash,
        "mode": mode, "ownership_refusals": ownership_refusals,
        "feasible": [c.candidate_ref for c in report.feasible],
        "excluded": [
            {"candidate_ref": c.candidate_ref, "exclusions": [e.as_dict() for e in feas.exclusions]}
            for c, feas in report.excluded
        ],
    })

    chosen: cs.Candidate | None = None
    selector = "none"
    ranked: list[tuple[cs.Candidate, int]] = []
    stop_reason = intent.stop_reason
    action = intent.action
    subtype = intent.subtype

    evsi_result: EV.RankResult | None = None
    evsi_assignment: dict[str, Any] | None = None
    if action == A.STOP:
        selector = "stop"
    elif action == A.EXPAND_MODEL:
        selector = "expand_model_off_hot_path"
    elif action == A.PRACTICE and subtype == A.DEPTH_PROGRESSION:
        selector = "depth_edge"  # no card candidate: the activity is the edge
        # Short session (§12.2/§16.9): a reviewed edge may be activated ONLY when the
        # transition fits safely. A depth edge carries no card duration, so it is bounded
        # by the conservative duration estimate; if that does not fit the available
        # minutes the session stops honestly rather than dangling an unfinishable edge.
        if is_short_session(snapshot):
            conservative = snapshot.conservative_duration_minutes or 0.0
            if conservative > (snapshot.remaining_minutes or 0.0):
                action, subtype = A.STOP, A.STOP_NO_FEASIBLE_ACTIVITY
                stop_reason = A.STOP_NO_FEASIBLE_ACTIVITY
                intent = StagedIntent(
                    action, subtype, "short_session_transition_cannot_fit",
                    intent.commitment_id, stop_reason=stop_reason,
                )
                selector = "stop"
    elif action == A.MEASURE_DIAGNOSTIC and diagnostic is not None:
        # Robust-EVSI-per-minute selection WITHIN the feasible set (§6.4).
        chosen, selector, ranked, evsi_result, evsi_assignment = _select_diagnostic(
            report, diagnostic, repository=repository, clock=clock,
            snapshot_hash=snapshot.snapshot_hash,
        )
        if chosen is None:
            # EVSI stop/abstain is a typed stop, distinct from no-feasible-activity.
            if evsi_result is not None and evsi_result.verdict == "abstain":
                action, subtype = A.STOP, A.STOP_WAITING_FOR_DELAY_OR_FRESH_SURFACE
                stop_reason = A.STOP_WAITING_FOR_DELAY_OR_FRESH_SURFACE
                intent = StagedIntent(action, subtype, "evsi_abstained", intent.commitment_id,
                                      stop_reason=stop_reason)
            elif evsi_result is not None and not report.feasible:
                action, subtype = A.STOP, A.STOP_NO_FEASIBLE_ACTIVITY
                stop_reason = A.STOP_NO_FEASIBLE_ACTIVITY
                intent = StagedIntent(action, subtype, "no_feasible_activity",
                                      intent.commitment_id, stop_reason=stop_reason)
            else:
                action, subtype = A.STOP, A.STOP_NO_POSITIVE_ROBUST_VALUE
                stop_reason = A.STOP_NO_POSITIVE_ROBUST_VALUE
                intent = StagedIntent(action, subtype, "no_positive_robust_value",
                                      intent.commitment_id, stop_reason=stop_reason)
    else:
        chosen, selector, ranked = _select_within_block(block, report, snapshot)
        if chosen is None:
            # No feasible activity -> typed stop, never a lowest-score bypass (§14.4).
            action, subtype = A.STOP, A.STOP_NO_FEASIBLE_ACTIVITY
            stop_reason = A.STOP_NO_FEASIBLE_ACTIVITY
            intent = StagedIntent(action, subtype, "no_feasible_activity", intent.commitment_id,
                                  stop_reason=stop_reason)
    steps.append({"step": "within_block_selection", "selector": selector,
                  "chosen_candidate_ref": chosen.candidate_ref if chosen else None,
                  "evsi": evsi_result.as_dict() if evsi_result is not None else None,
                  "evsi_assignment": evsi_assignment,
                  "ranked": [{"candidate_ref": c.candidate_ref, "rank": r} for c, r in ranked]})

    # AFFECT check BEFORE any depth edge (U-011, §4.2).
    affect = _affect_downgrade(snapshot, intent.commitment_id)
    steps.append({"step": "affect_check", **affect})

    depth_edge_result: dict[str, Any] | None = None
    if action == A.PRACTICE and subtype == A.DEPTH_PROGRESSION:
        commitment = snapshot.commitment(intent.commitment_id or "")
        edge_id = intent.detail.get("edge_id")
        milestone = intent.detail.get("milestone")
        if affect["downgraded_auto_to_suggest_next"]:
            depth_edge_result = {
                "committed": False, "kind": "suggest_next",
                "reason": "affect_downgraded_auto_to_suggest_next",
            }
        elif commitment is not None and edge_id and milestone:
            receipt = signals.milestone_evidence_receipt or {"qualifies": True, "evidence_receipt": {}}
            # Record the predecessor milestone reached, then request ONE edge (U-018
            # gate OFF -> returns a suggest_next proposal, activates nothing).
            outcome = DT.commit_one_edge(
                repository, commitment_id=commitment.commitment_id, milestone=milestone,
                selected_edge_id=edge_id, evidence_receipt=receipt, clock=clock,
            )
            depth_edge_result = {
                "committed": bool(getattr(outcome, "committed", False)),
                "kind": getattr(outcome, "kind", None) if not getattr(outcome, "committed", False) else "committed",
                "reason": getattr(outcome, "reason", None),
                "selected_edge_id": edge_id, "milestone": milestone,
            }
        else:
            depth_edge_result = {"committed": False, "kind": "refused",
                                 "reason": "edge_not_feasible"}
        steps.append({"step": "depth_edge", **depth_edge_result})

    comparator = None
    if record_comparator:
        feasible_refs = {c.candidate_ref for c in report.feasible}
        comparator = _comparator(vault, repository, session, feasible_refs)
        steps.append({"step": "comparator_logged",
                      "legacy_top": comparator.get("legacy_top") if comparator else None,
                      "authority": "none"})

    # Assemble candidate rows (feasible + excluded), with logged comparator scores.
    comparator_scores = (comparator or {}).get("scores", {}) if comparator else {}
    ranks = {c.candidate_ref: r for c, r in ranked}
    candidate_rows: list[dict[str, Any]] = []
    for cand in snapshot.candidates:
        feas = report.per_candidate.get(cand.candidate_ref)
        is_feasible = feas.eligible if feas is not None else False
        comp = comparator_scores.get(cand.candidate_ref)
        candidate_rows.append({
            "candidate_ref": cand.candidate_ref,
            "learning_object_id": cand.learning_object_id,
            "feasible": is_feasible,
            "exclusion_reasons": [e.as_dict() for e in feas.exclusions] if feas else [],
            "within_mode_metrics": {"selector": selector, "due_at": cand.due_at},
            "comparator_score": comp.get("priority") if isinstance(comp, dict) else None,
            "selected": bool(chosen is not None and cand.candidate_ref == chosen.candidate_ref),
            "rank_ordinal": ranks.get(cand.candidate_ref),
        })

    why = _why_copy(intent, block, chosen)
    decision_params_hash = snapshot.param_manifest_hash
    trace = {
        "snapshot_hash": snapshot.snapshot_hash,
        "policy_version": STAGED_POLICY_VERSION,
        "mode": mode,
        "ownership_refusals": ownership_refusals,
        "staged_rule": intent.staged_rule,
        "action": action,
        "subtype": subtype,
        "commitment_id": intent.commitment_id,
        "attention_block": {
            "action": block.action, "subtype": block.subtype,
            "budget_minutes": block.budget_minutes,
            "short_circuit_reason": block.short_circuit_reason,
            "compatible_purposes": list(block.compatible_purposes),
        },
        "constraint_manifest_hash": report.manifest_hash,
        "constraint_manifest_version": ce.CONSTRAINT_MANIFEST_VERSION,
        "decision_params_hash": decision_params_hash,
        "param_manifest_hash": snapshot.param_manifest_hash,
        "feasible_set": [c.candidate_ref for c in report.feasible],
        "exclusions": {
            c.candidate_ref: [e.as_dict() for e in feas.exclusions]
            for c, feas in report.excluded
        },
        "ranking_inputs": {"selector": selector,
                           "evsi": evsi_result.as_dict() if evsi_result is not None else None,
                           "evsi_assignment": evsi_assignment,
                           "ranked": [{"candidate_ref": c.candidate_ref, "rank": r} for c, r in ranked]},
        "chosen_action": {"action": action, "subtype": subtype,
                          "candidate_ref": chosen.candidate_ref if chosen else None},
        "affect_check": affect,
        "depth_edge": depth_edge_result,
        "stop_alternatives": list(A.STOP_REASONS),
        "stop_reason": stop_reason,
        "comparator": comparator,
        "model_versions": {"staged_policy": STAGED_POLICY_VERSION,
                           "constraint_manifest": ce.CONSTRAINT_MANIFEST_VERSION,
                           "snapshot_schema": cs.SNAPSHOT_SCHEMA_VERSION},
        "remaining_budget_minutes": snapshot.remaining_minutes,
        "why": why,
        "steps": steps,
    }

    # Persist the attention block + one open event, then the decision + candidates.
    block_id = store.create_attention_block(
        repository, session_id=snapshot.session_id, commitment_id=block.commitment_id,
        action=block.action, subtype=block.subtype, budget_minutes=block.budget_minutes,
        neighborhood=block.neighborhood, exit_rules=list(block.exit_rules),
        short_circuit_reason=block.short_circuit_reason, content_hash=block.content_hash(),
        clock=clock,
    )
    store.append_block_event(repository, block_id=block_id, kind="block_opened",
                             detail={"staged_rule": intent.staged_rule}, clock=clock)

    written = store.persist_decision(
        repository, receipt_key=receipt_key, snapshot_id=snapshot_id,
        snapshot_hash=snapshot.snapshot_hash, session_id=snapshot.session_id, mode=mode,
        commitment_id=intent.commitment_id, staged_rule=intent.staged_rule, action=action,
        subtype=subtype, attention_block_id=block_id,
        chosen_candidate_ref=chosen.candidate_ref if chosen else None, stop_reason=stop_reason,
        constraint_manifest_hash=report.manifest_hash, decision_params_hash=decision_params_hash,
        policy_version=str(STAGED_POLICY_VERSION), comparator=comparator, trace=trace,
        candidates=candidate_rows, clock=clock,
    )
    decision_id = written["decision_id"]

    # Shadow predictions: persisted, joined to the snapshot hash, ZERO authority.
    for pred in _run_shadow_scorers(shadow_scorers, snapshot, chosen):
        store.persist_shadow_prediction(
            repository, decision_id=decision_id, snapshot_hash=snapshot.snapshot_hash,
            scorer_kind=pred["scorer_kind"], model_version="shadow_v0",
            prediction=pred["prediction"], usable=pred["usable"], clock=clock,
        )

    return DecisionResult(
        decision_id=decision_id, already=written["already"], action=action, subtype=subtype,
        staged_rule=intent.staged_rule,
        chosen_candidate_ref=chosen.candidate_ref if chosen else None, stop_reason=stop_reason,
        snapshot_hash=snapshot.snapshot_hash, trace=trace, feasibility=report, block=block,
        why=why,
    )


def _why_copy(intent: StagedIntent, block: AttentionBlock, chosen: cs.Candidate | None) -> str:
    """Learner-facing 'why' comes from the staged reason + commitment, never the
    largest opaque score term (§3.3)."""

    if intent.action == A.STOP:
        return f"Stopping: {intent.stop_reason or intent.staged_rule}."
    target = f" on {chosen.candidate_ref}" if chosen is not None else ""
    sub = f" ({intent.subtype})" if intent.subtype else ""
    return f"{intent.action}{sub}{target} because {intent.staged_rule}."
