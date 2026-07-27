from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from math import log
from pathlib import Path
from typing import Any, Mapping

from learnloop.codex.prompts import PRACTICE_GENERATION_PROMPT_VERSION

from learnloop.ai.client import AIProviderClient
from learnloop.clock import Clock, SystemClock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.services.activity_patterns import LEGACY_UNMAPPED, map_capability
from learnloop.services.contract_commissioning import commission_plan
from learnloop.services.depth_rungs import (
    TASK_FEATURE_SCHEMA_SLUG,
    RungTarget,
    capability_rung,
    select_rung,
    validate_item_against_rung,
)
from learnloop.services.followups import (
    current_same_facet_failure_streak,
    current_same_item_failure_streak,
)
from learnloop.services.facet_state_reader import facet_recall_states_for_lo
from learnloop.services.mastery import covering_learner_claim, display_mastery
from learnloop.services.authoring_gates import (
    SELECTED_RESPONSE_PATTERNS as _SELECTED_RESPONSE_PATTERNS,
    SelectedResponseGate as _SelectedResponseGate,
    build_instrument_gates,
    chain_gates as _chain_gates,
)
from learnloop.services.proposals import generate_authoring_proposal
from learnloop.services.teach_back import TEACH_BACK_PRACTICE_MODE
from learnloop.services.state_sync import sync_vault_state
from learnloop.services.synthesis_gates import GateDiagnostic
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths


@dataclass(frozen=True)
class PracticeExpansionTarget:
    learning_object_id: str
    title: str
    subjects: list[str]
    concept: str
    existing_practice_items: int
    requested_new_items: int
    probe_attempts_completed: int
    probe_attempts_target: int
    mastery_mean: float | None
    recommended_difficulty_band: tuple[float, float]
    existing_evidence_facets: list[str] = field(default_factory=list)
    # Depth-rung target (services/depth_rungs): the waypoint in capability ×
    # task-feature space new items must be authored AT. Difficulty (above) is
    # calibrated WITHIN this rung, never by changing the rung.
    rung: RungTarget | None = None
    # The LO's assessment blueprint, decomposed into the distinct components an
    # item can probe (facet × capability × role). Without this the authoring
    # model sees only a flat facet list and permutes ONE surface across the whole
    # batch; readiness is a conjunction over these components, so a batch that
    # misses most of them cannot move the projection however well it is answered.
    blueprint_components: list[dict[str, Any]] = field(default_factory=list)
    # Surface families already used for this LO — the batch must not repeat them.
    existing_surface_families: list[str] = field(default_factory=list)
    # Stage 5.1 (Meas §5.8.2): the unreachable contract cells this LO owes
    # instruments for, in `commissioning_queue()` order, each carrying the
    # capability the CONTRACT names and the waypoint that authors AT it. Non-empty
    # => `rung` above is the first of these, not the mastery-band waypoint: Step 0
    # measured that 72% of attempts landed at a capability the contract never
    # asked for, purely because the rung was chosen independently of the contract.
    commissioned_cells: list[dict[str, Any]] = field(default_factory=list)
    # Every capability this LO's contract names (reachable cells included) — the
    # admission set `_RungGate` holds generated items to. Empty for a legacy LO
    # with no blueprint, which keeps today's single-rung behaviour exactly.
    contract_capabilities: list[str] = field(default_factory=list)
    # Cells generation may NOT author, with their typed reason (§5.8.3: a
    # `coordination` integration is owed a reviewed depth envelope / A1 capstone,
    # not a quietly-lowered rung). Reported, never silently dropped.
    deferred_cells: list[dict[str, Any]] = field(default_factory=list)
    # Meas §3.A4 (plan item 6.4): the facet pairs no instrument in this vault can
    # separate, as authoring REQUESTS. §3.A4 is explicit that contrast pairs are
    # "commissioned, not merely permitted" -- so the findings have to reach the
    # authoring model as targets, exactly as `commissioned_cells` does, rather
    # than sitting in a report a human might one day read.
    contrast_pair_requests: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "learning_object_id": self.learning_object_id,
            "title": self.title,
            "subjects": self.subjects,
            "concept": self.concept,
            "existing_practice_items": self.existing_practice_items,
            "requested_new_items": self.requested_new_items,
            "probe_attempts_completed": self.probe_attempts_completed,
            "probe_attempts_target": self.probe_attempts_target,
            "mastery_mean": self.mastery_mean,
            "recommended_difficulty_band": list(self.recommended_difficulty_band),
            "existing_evidence_facets": self.existing_evidence_facets,
            "blueprint_components": self.blueprint_components,
            "existing_surface_families": self.existing_surface_families,
        }
        if self.commissioned_cells:
            payload["commissioned_cells"] = self.commissioned_cells
        if self.contract_capabilities:
            payload["contract_capabilities"] = self.contract_capabilities
        if self.contrast_pair_requests:
            payload["contrast_pair_requests"] = self.contrast_pair_requests
        if self.rung is not None:
            from learnloop.services.depth_rungs import rung_float_proxies

            payload["waypoint_slug"] = self.rung.waypoint_slug
            payload["capability"] = self.rung.capability
            payload["target_task_features"] = dict(self.rung.task_features)
            payload["rung_source"] = self.rung.source
            payload["float_proxy_bands"] = {
                proxy: list(band) for proxy, band in rung_float_proxies(self.rung).items()
            }
        return payload


@dataclass(frozen=True)
class PracticeExpansionPlan:
    targets: list[PracticeExpansionTarget]

    @property
    def requested_new_items(self) -> int:
        return sum(target.requested_new_items for target in self.targets)

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "targets": [target.as_dict() for target in self.targets],
            "requested_new_items": self.requested_new_items,
        }
        # Deferred contract cells ride on the PLAN, not on the prompt payload:
        # they are an authoring obligation nobody may discharge yet (§5.8.3), so
        # naming them to the model would only invite a wrong-rung item, while
        # dropping them entirely is how 18 uncertifiable objectives went unseen.
        deferred = [
            {"learning_object_id": target.learning_object_id, **cell}
            for target in self.targets
            for cell in target.deferred_cells
        ]
        if deferred:
            payload["deferred_contract_cells"] = deferred
        return payload


@dataclass(frozen=True)
class PracticeExpansionResult:
    patch_id: str
    plan: PracticeExpansionPlan
    # --mode-mix compliance of the persisted proposal. Violations are hard
    # (requested teach_back count not honored for a targeted LO); warnings are
    # soft mismatches on other practice modes.
    mode_mix_violations: list[str] = field(default_factory=list)
    mode_mix_warnings: list[str] = field(default_factory=list)
    # Rung-gate outcomes: hard_fail diagnostics per generated item (those rows
    # were forced to review, never auto-applied); warnings are review-severity.
    rung_violations: list[str] = field(default_factory=list)
    rung_warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "plan": self.plan.as_dict(),
            "mode_mix_violations": list(self.mode_mix_violations),
            "mode_mix_warnings": list(self.mode_mix_warnings),
            "rung_violations": list(self.rung_violations),
            "rung_warnings": list(self.rung_warnings),
        }


class PracticeExpansionError(ValueError):
    pass


@dataclass(frozen=True)
class DiagnosticPracticeTarget:
    need_id: str
    learning_object_id: str
    title: str
    subjects: list[str]
    concept: str
    desired_intent: str
    trigger_reason: str
    target_facets: list[str]
    source_practice_item_id: str | None
    source_prompt: str | None
    source_expected_answer: str | dict | None
    candidate_requirements: dict[str, Any]
    diagnostic_focus: dict[str, Any] | None
    repair_rationales: list[dict[str, Any]]
    mastery_mean: float | None
    facet_recall_mean_by_facet: dict[str, float]
    facet_recall_variance_by_facet: dict[str, float]
    recommended_difficulty_band: tuple[float, float]

    def as_dict(self) -> dict[str, Any]:
        return {
            "need_id": self.need_id,
            "learning_object_id": self.learning_object_id,
            "title": self.title,
            "subjects": self.subjects,
            "concept": self.concept,
            "desired_intent": self.desired_intent,
            "trigger_reason": self.trigger_reason,
            "target_facets": self.target_facets,
            "source_practice_item_id": self.source_practice_item_id,
            "source_prompt": self.source_prompt,
            "source_expected_answer": self.source_expected_answer,
            "candidate_requirements": self.candidate_requirements,
            "diagnostic_focus": self.diagnostic_focus,
            "repair_rationales": self.repair_rationales,
            "mastery_mean": self.mastery_mean,
            "facet_recall_mean_by_facet": self.facet_recall_mean_by_facet,
            "facet_recall_variance_by_facet": self.facet_recall_variance_by_facet,
            "recommended_difficulty_band": list(self.recommended_difficulty_band),
        }


@dataclass(frozen=True)
class DiagnosticPracticePlan:
    targets: list[DiagnosticPracticeTarget]

    @property
    def requested_new_items(self) -> int:
        return len(self.targets)

    def as_dict(self) -> dict[str, Any]:
        return {
            "targets": [target.as_dict() for target in self.targets],
            "requested_new_items": self.requested_new_items,
        }


@dataclass(frozen=True)
class DiagnosticPracticeResult:
    patch_id: str
    plan: DiagnosticPracticePlan
    fulfilled_need_ids: list[str]
    # Stage 5.3 (Meas §3.0): the planted-persona gate's roll-up for this batch.
    # Blocked rows are persisted `validation_status="invalid"` (acceptance refuses
    # them); flagged rows lost auto-apply and carry a review note. Reported here so
    # the CLI can name the decisive reason instead of the caller re-deriving it.
    persona_gate: dict[str, Any] = field(default_factory=dict)
    persona_gate_violations: list[str] = field(default_factory=list)
    persona_gate_warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "patch_id": self.patch_id,
            "plan": self.plan.as_dict(),
            "fulfilled_need_ids": self.fulfilled_need_ids,
        }
        if self.persona_gate:
            payload["persona_gate"] = dict(self.persona_gate)
        if self.persona_gate_violations:
            payload["persona_gate_violations"] = list(self.persona_gate_violations)
        if self.persona_gate_warnings:
            payload["persona_gate_warnings"] = list(self.persona_gate_warnings)
        return payload


def build_practice_expansion_plan(
    vault: LoadedVault,
    repository: Repository,
    *,
    subjects: list[str] | None = None,
    target_items_per_lo: int = 5,
    max_new_per_lo: int = 3,
    max_los: int | None = None,
    focus_concepts: list[str] | None = None,
    learning_object_ids: list[str] | None = None,
    mode_mix: dict[str, int] | None = None,
    require_completed_probe: bool = True,
    exclude_item_ids: set[str] | None = None,
) -> PracticeExpansionPlan:
    if target_items_per_lo <= 0:
        raise PracticeExpansionError("target_items_per_lo must be positive")
    if max_new_per_lo <= 0:
        raise PracticeExpansionError("max_new_per_lo must be positive")
    _validate_mode_mix(mode_mix)
    named_lo_ids = list(dict.fromkeys(learning_object_ids or []))
    # Stage 5.1: 3.1's reachability report, resolved into rung-correct authoring
    # targets. One static pass over vault content (no attempts, no provider), and
    # it is what makes the contract — rather than the learner's mastery band — the
    # authority on the capability new items are authored at.
    commissions = commission_plan(vault, repository)
    _validate_named_learning_objects(
        vault,
        repository,
        named_lo_ids,
        require_completed_probe=require_completed_probe,
        contract_backed={
            lo_id for lo_id in named_lo_ids if commissions.for_learning_object(lo_id)
        },
    )
    subject_filter = set(subjects or [])
    concept_filter = set(focus_concepts or [])
    item_counts = _active_practice_item_counts(vault, repository, exclude_item_ids=exclude_item_ids)
    facet_unions = _active_evidence_facet_unions(vault, repository)
    surface_families = _active_surface_families(vault, repository)
    # Meas §3.A4: the identifiability findings a contrast pair can close, keyed by
    # the facets they name. One static pass, no provider, and it reuses the SAME
    # `analyze_identifiability` the doctor runs -- a request here and a finding
    # there can never disagree about what is non-identifiable.
    pair_requests_by_facet = _contrast_pair_requests_by_facet(vault, repository)
    irt = vault.config.mastery.irt
    mode_mix_items = sum(mode_mix.values()) if mode_mix else None
    targets: list[PracticeExpansionTarget] = []
    for learning_object in sorted(vault.learning_objects.values(), key=lambda lo: lo.id):
        if named_lo_ids and learning_object.id not in named_lo_ids:
            continue
        if learning_object.status != "active":
            continue
        if subject_filter and not (subject_filter & set(learning_object.subjects)):
            continue
        if concept_filter and learning_object.concept not in concept_filter:
            continue
        # Stage 5.1 corollary: the completed-probe gate follows probe *evidence*,
        # but a commissionable contract cell is an authoring obligation that
        # exists regardless of probes — the rung below comes from the contract,
        # not the mastery band, so the gate would only starve the contract it
        # exists to protect. (Measured: with the gate unconditional,
        # fixtures/linear_algebra yields 0 targets while 18 LOs hold
        # commissionable cells, because lo_probe_state has no rows.) LOs with
        # nothing commissionable keep the gate byte-for-byte.
        commissioned = commissions.for_learning_object(learning_object.id)
        probe_state = repository.probe_state(learning_object.id)
        if (
            require_completed_probe
            and not commissioned
            and (probe_state is None or probe_state.status != "complete")
        ):
            continue
        existing_count = item_counts.get(learning_object.id, 0)
        needed = target_items_per_lo - existing_count
        named = learning_object.id in named_lo_ids
        if needed <= 0 and not named:
            continue
        if mode_mix_items is not None:
            # --mode-mix is a hard per-LO constraint; it overrides the deficit sizing.
            requested = mode_mix_items
        elif needed > 0:
            requested = min(needed, max_new_per_lo)
        else:
            # Named LO past its deficit target: still request at least one item.
            requested = 1
        mastery = repository.mastery_state(learning_object.id)
        mastery_mean = display_mastery(mastery).mastery_mean if mastery is not None else None
        # With no mastery state at all, the learner claim (if any) sets both the
        # rung entry point and the ability the difficulty band inverts around. A
        # claim-seeded mastery state already carries the claim in mastery_mean.
        claimed_level: float | None = None
        if mastery is None:
            claim = covering_learner_claim(vault, repository, learning_object.id)
            claimed_level = float(claim["claimed_level"]) if claim is not None else None
        # Rung-correct generation (Stage 5.1 / Meas §5.8.2): when this LO's own
        # blueprint names cells no authored item can observe, the CONTRACT sets the
        # waypoint — the head of the commissioning queue for this LO, honouring
        # 3.1's `_queue_sort_key` rather than a second priority invented here.
        # Otherwise nothing changes: `select_rung`'s mastery-band / probe-hypothesis
        # / milestone path stands exactly as before, which is why a legacy vault
        # with no authored blueprints is byte-for-byte unaffected.
        deferred = commissions.deferred_for_learning_object(learning_object.id)
        if commissioned:
            rung = commissioned[0].rung
        else:
            rung = select_rung(
                vault,
                repository,
                learning_object_id=learning_object.id,
                mastery_mean=mastery_mean,
                evidence_count=(mastery.evidence_count if mastery is not None else 0),
                claimed_level=claimed_level,
            )
        ability = mastery_mean if mastery_mean is not None else claimed_level
        targets.append(
            PracticeExpansionTarget(
                learning_object_id=learning_object.id,
                title=learning_object.title,
                subjects=list(learning_object.subjects),
                concept=learning_object.concept,
                existing_practice_items=existing_count,
                requested_new_items=requested,
                probe_attempts_completed=(probe_state.probe_attempts_completed if probe_state else 0),
                probe_attempts_target=(probe_state.probe_attempts_target if probe_state else 0),
                mastery_mean=mastery_mean,
                recommended_difficulty_band=_success_band_difficulty(
                    _ability_logit(ability),
                    vault.config.practice_generation.practice_success_band,
                    discrimination=irt.discrimination_default,
                    difficulty_scale=irt.difficulty_prior_scale,
                    difficulty_floor=vault.config.practice_generation.difficulty_floor,
                    min_band_width=vault.config.practice_generation.min_band_width,
                ),
                existing_evidence_facets=facet_unions.get(learning_object.id, []),
                rung=rung,
                blueprint_components=_blueprint_components(learning_object),
                existing_surface_families=surface_families.get(learning_object.id, []),
                commissioned_cells=[cell.as_dict() for cell in commissioned],
                contract_capabilities=list(commissions.capabilities_for(learning_object.id)),
                deferred_cells=[cell.as_dict() for cell in deferred],
                contrast_pair_requests=_contrast_pair_requests_for(
                    pair_requests_by_facet, learning_object
                ),
            )
        )
    # Target order follows the commissioning queue: an LO whose best unreachable
    # cell sits earlier in `commissioning_queue()` is commissioned first, and LOs
    # with nothing commissionable sort last by id. This is the "prioritized queue"
    # half of item 5.1 — without it `max_los` would truncate alphabetically and
    # could drop every cell the queue put at the front.
    queue_rank = commissions.learning_object_rank()
    unranked = len(queue_rank) + 1
    targets.sort(
        key=lambda target: (
            queue_rank.get(target.learning_object_id, unranked),
            target.learning_object_id,
        )
    )
    if max_los is not None:
        targets = targets[:max_los]
    return PracticeExpansionPlan(targets=targets)


def build_diagnostic_practice_plan(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_id: str | None = None,
    max_needs: int = 3,
    clock: Clock | None = None,
) -> DiagnosticPracticePlan:
    if max_needs <= 0:
        raise PracticeExpansionError("max_needs must be positive")
    irt = vault.config.mastery.irt
    now = (clock or SystemClock()).now().astimezone(UTC)
    targets: list[DiagnosticPracticeTarget] = []
    for need in repository.pending_intervention_needs(learning_object_id):
        if _stale_repeat_failure_need(vault, repository, need) or _stale_tutor_gap_need(
            vault, repository, need, now=now
        ):
            continue
        learning_object = vault.learning_objects.get(need["learning_object_id"])
        if learning_object is None or learning_object.status != "active":
            continue
        target_facets = [vault.canonical_facet_id(facet) for facet in need.get("target_facets", [])]
        if not target_facets:
            continue
        source_item = vault.practice_items.get(need.get("practice_item_id") or "")
        mastery = repository.mastery_state(learning_object.id)
        mastery_mean = display_mastery(mastery).mastery_mean if mastery is not None else None
        facet_states = {
            state.facet_id: state
            for state in facet_recall_states_for_lo(vault, repository, learning_object.id)
            if state.practice_item_id is None
        }
        facet_means = {
            facet: float(facet_states[facet].recall_mean)
            for facet in target_facets
            if facet in facet_states
        }
        facet_variances = {
            facet: float(facet_states[facet].recall_variance)
            for facet in target_facets
            if facet in facet_states
        }
        diagnostic_focus = need.get("diagnostic_focus") if isinstance(need.get("diagnostic_focus"), dict) else None
        repair_rationales = _repair_rationales_from_focus(diagnostic_focus) or _repair_rationales(
            repository, need.get("attempt_id")
        )
        targets.append(
            DiagnosticPracticeTarget(
                need_id=need["id"],
                learning_object_id=learning_object.id,
                title=learning_object.title,
                subjects=list(learning_object.subjects),
                concept=learning_object.concept,
                desired_intent=need["desired_intent"],
                trigger_reason=need["trigger_reason"],
                target_facets=target_facets,
                source_practice_item_id=source_item.id if source_item is not None else need.get("practice_item_id"),
                source_prompt=source_item.prompt if source_item is not None else None,
                source_expected_answer=source_item.expected_answer if source_item is not None else None,
                candidate_requirements=dict(need.get("candidate_requirements") or {}),
                diagnostic_focus=diagnostic_focus,
                repair_rationales=repair_rationales,
                mastery_mean=mastery_mean,
                facet_recall_mean_by_facet=facet_means,
                facet_recall_variance_by_facet=facet_variances,
                # No floor here: the probe band is deliberately narrow and
                # centred on the learner's boundary, where outcome variance
                # (and so diagnostic information) is already maximal. Raising it
                # would blunt the very thing a probe is for. The one guarded
                # case is a band that clamped to zero width — the degenerate
                # [0.0, 0.0] collapse that pinned authored difficulty to 0.0
                # pre-101474c — which _guard_degenerate_band widens away from
                # the clamp edge without re-centring.
                recommended_difficulty_band=_guard_degenerate_band(
                    _success_band_difficulty(
                        _ability_logit(_ability_estimate(facet_means, mastery_mean)),
                        vault.config.practice_generation.probe_success_band,
                        discrimination=irt.discrimination_default,
                        difficulty_scale=irt.difficulty_prior_scale,
                    ),
                    min_band_width=vault.config.practice_generation.min_band_width,
                ),
            )
        )
        if len(targets) >= max_needs:
            break
    return DiagnosticPracticePlan(targets=targets)


def _stale_repeat_failure_need(
    vault: LoadedVault,
    repository: Repository,
    need: dict[str, Any],
) -> bool:
    """Lazily retire repeat-failure needs whose streak has since resolved.

    Staleness is deliberately trigger-aware: residual uncertainty may still be
    useful evidence for a future diagnostic, but it must not keep alive a need
    whose recorded reason was a repeated failure that is no longer repeating.
    Other trigger families retain their existing lifecycle.
    """

    reason = need.get("trigger_reason")
    config = vault.config.scheduler.followup
    streak: int
    threshold: int
    if reason == "repeated_same_item_failure":
        practice_item_id = need.get("practice_item_id")
        streak = (
            current_same_item_failure_streak(repository, str(practice_item_id))
            if practice_item_id
            else 0
        )
        threshold = config.tau_repeated_item_failures
    elif reason == "repeated_same_facet_failure":
        facets = [vault.canonical_facet_id(str(facet)) for facet in need.get("target_facets", [])]
        streak = current_same_facet_failure_streak(
            vault,
            repository,
            str(need["learning_object_id"]),
            facets,
        )
        threshold = config.tau_repeated_facet_failures
    else:
        return False

    if streak >= threshold:
        return False
    repository.update_intervention_need_status(
        str(need["id"]),
        status="stale",
        blocked_reason=f"resolved_failure_streak:{streak}/{threshold}",
    )
    return True


def _stale_tutor_gap_need(
    vault: LoadedVault,
    repository: Repository,
    need: dict[str, Any],
    *,
    now: datetime,
) -> bool:
    """Lazily retire tutor_gap_declaration needs (spec §3 G3).

    A gap need goes stale when every target facet has landed >=1 *successful*
    attempt after the need was created (mirrors question-signal resolution
    semantics: not dont_know, correctness > 0.40, no error_type), or once it is
    older than ``tutor_promotion.gap_need_ttl_days``. Other trigger families keep
    their existing lifecycle.
    """

    if need.get("trigger_reason") != "tutor_gap_declaration":
        return False
    created_at = need.get("created_at")
    target_facets = {vault.canonical_facet_id(str(facet)) for facet in need.get("target_facets", [])}

    # TTL path: an unmeasured gap that no longer reflects the learner's state.
    ttl_days = vault.config.tutor_promotion.gap_need_ttl_days
    created = parse_utc(created_at) if created_at else None
    if created is not None and now - created > timedelta(days=ttl_days):
        repository.update_intervention_need_status(
            str(need["id"]),
            status="stale",
            blocked_reason=f"tutor_gap_ttl:{ttl_days}d",
        )
        return True

    # Facet-success path: every target facet has been measured successfully since.
    if target_facets:
        resolved: set[str] = set()
        for attempt in repository.list_recent_attempts_by_learning_object(
            str(need["learning_object_id"]), limit=200
        ):
            attempted_at = attempt.get("created_at")
            if not attempted_at or (created_at and attempted_at <= created_at):
                continue
            if _attempt_failed(attempt):
                continue
            for facet in attempt.get("evidence_facets", []):
                resolved.add(vault.canonical_facet_id(str(facet)))
        if target_facets <= resolved:
            repository.update_intervention_need_status(
                str(need["id"]),
                status="stale",
                blocked_reason="tutor_gap_facets_resolved",
            )
            return True
    return False


def _attempt_failed(attempt: dict[str, Any]) -> bool:
    """Failure predicate mirroring ``question_signal._attempt_failed`` (§3 G3).

    Kept in sync deliberately so tutor_gap staleness resolves on exactly the same
    "successful attempt" definition the question-signal channel uses.
    """

    return (
        attempt.get("attempt_type") == "dont_know"
        or float(attempt.get("correctness") or 0.0) <= 0.40
        or bool(attempt.get("error_type"))
    )


def generate_diagnostic_practice_proposal(
    root: Path,
    codex_client: AIProviderClient,
    *,
    learning_object_id: str | None = None,
    max_needs: int = 3,
    extra_instructions: str | None = None,
    codex_revision: str | None = None,
) -> DiagnosticPracticeResult:
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    sync_vault_state(vault, repository)
    plan = build_diagnostic_practice_plan(
        vault,
        repository,
        learning_object_id=learning_object_id,
        max_needs=max_needs,
    )
    if not plan.targets:
        raise PracticeExpansionError("No pending intervention needs require diagnostic Practice Items.")
    source_refs = _diagnostic_source_refs(plan)
    # Stage 5.3 (Meas §3.0): the planted-persona gate on the LIVE diagnostic route.
    # It rides the same `row_transform` seam `_RungGate`/`_SelectedResponseGate`
    # use, so it runs after validation/repair and before persist + auto-apply. The
    # gate is passed the provider as its grading client: `PersonaGate` escalates to
    # `grade_diagnostic_fire` only when the provider exposes it, and falls back to
    # the deterministic in-memory rule otherwise (a provider outage must not block
    # authoring). Nothing about the tier is decided here — see `classify_instrument`.
    # Meas §3.A4 (plan item 6.4): the pair gate is chained after the persona gate
    # on every route, and separate from it — the persona gate asks whether the
    # belief-holder fails exactly one member (a question about beliefs); the pair
    # gate asks whether the two payloads are a pair at all. The diagnostic route
    # has no per-LO difficulty band, so the band clause abstains and says so in
    # the audit rather than inventing a band to check against. The composition
    # itself lives in `authoring_gates.build_instrument_gates` so the ingest
    # lanes run the identical chain.
    gates = build_instrument_gates(vault, repository, grading_client=codex_client)
    persona_gate = gates.persona_gate
    pair_gate = gates.pair_gate
    patch_id = generate_authoring_proposal(
        root,
        codex_client,
        subjects=sorted({subject for target in plan.targets for subject in target.subjects}),
        source_refs=source_refs,
        instructions=_diagnostic_practice_instructions(plan, extra_instructions=extra_instructions),
        codex_revision=codex_revision,
        merge_context_source_refs=True,
        row_transform=gates,
    )
    fulfilled: list[str] = []
    persisted_items = repository.proposal_items(patch_id)
    diagnostic_item_ids_by_need = _diagnostic_item_ids_by_need(plan, persisted_items)
    # Rows the persona gate hard-blocked, resolved from client id to persisted id.
    blocked_client_ids = {outcome.client_item_id for outcome in persona_gate.blocked}
    blocked_item_ids = {
        str(item["id"])
        for item in persisted_items
        if str(item.get("client_item_id") or "") in blocked_client_ids
    }
    authored_items = [
        item
        for item in persisted_items
        if item.get("item_type") == "practice_item" and item.get("operation") == "create"
    ]
    # `_diagnostic_item_ids_by_need` is a heuristic attribution (source refs, then a
    # single-unmatched-pair fallback). When it cannot attribute an item to a need
    # but EVERY authored item in the batch was blocked, nothing shippable exists for
    # that need either way, so reopening it is exact rather than conservative.
    nothing_shippable = bool(authored_items) and len(blocked_item_ids) == len(authored_items)
    for target in plan.targets:
        item_id = diagnostic_item_ids_by_need.get(target.need_id)
        if (item_id is not None and item_id in blocked_item_ids) or (
            item_id is None and nothing_shippable
        ):
            # §3.0 hard tier: a diagnostic that cannot discriminate must not
            # consume the need that asked for it, or the learner silently loses the
            # measurement. Same reopen convention as `proposals._reopen_need_after_
            # gate_failure`. The row is left `pending` + `invalid` rather than
            # auto-rejected: acceptance already refuses an invalid row, and leaving
            # `decision` untouched keeps it a record of a HUMAN's judgement (which
            # is what `persona_gate.gate_precision` reports descriptively).
            rejected_reason = f"diagnostic_proposal_rejected:{patch_id}"
            if item_id is not None:
                rejected_reason = f"{rejected_reason}:{item_id}"
            repository.update_intervention_need_status(
                target.need_id,
                status="pending",
                blocked_reason=rejected_reason,
            )
            continue
        blocked_reason = f"diagnostic_proposal_queued:{patch_id}"
        if item_id:
            blocked_reason = f"{blocked_reason}:{item_id}"
        if repository.update_intervention_need_status(
            target.need_id,
            status="fulfilled",
            blocked_reason=blocked_reason,
        ):
            fulfilled.append(target.need_id)
    return DiagnosticPracticeResult(
        patch_id=patch_id,
        plan=plan,
        fulfilled_need_ids=fulfilled,
        persona_gate=persona_gate.summary(),
        persona_gate_violations=persona_gate.violations + pair_gate.violations,
        persona_gate_warnings=persona_gate.warnings,
    )


def generate_post_probe_practice_proposal(
    root: Path,
    codex_client: AIProviderClient,
    *,
    subjects: list[str] | None = None,
    target_items_per_lo: int = 5,
    max_new_per_lo: int = 3,
    max_los: int | None = None,
    focus_concepts: list[str] | None = None,
    focus_facets: list[str] | None = None,
    extra_instructions: str | None = None,
    codex_revision: str | None = None,
    learning_object_ids: list[str] | None = None,
    mode_mix: dict[str, int] | None = None,
    require_completed_probe: bool = True,
    source_refs: list[dict[str, Any]] | None = None,
) -> PracticeExpansionResult:
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    sync_vault_state(vault, repository)
    plan = build_practice_expansion_plan(
        vault,
        repository,
        subjects=subjects,
        target_items_per_lo=target_items_per_lo,
        max_new_per_lo=max_new_per_lo,
        max_los=max_los,
        focus_concepts=focus_concepts,
        learning_object_ids=learning_object_ids,
        mode_mix=mode_mix,
        require_completed_probe=require_completed_probe,
    )
    if not plan.targets:
        raise PracticeExpansionError("No completed probe Learning Objects need more Practice Items.")
    rung_gate = _RungGate(repository, plan)
    # Meas §3.0, advisory tier for plain practice (plan §7.3): chained onto the
    # plain-practice route too, so that a row which is *structurally* a diagnostic
    # instrument is hard-gated even when produced here. The tier is never a
    # property of the route. Meas §3.A4: the pair gate holds both members to the
    # SAME target band the rung gate already uses (`_success_band_difficulty`'s
    # inversion), so "the target difficulty band" means one thing in this vault.
    gates = build_instrument_gates(
        vault,
        repository,
        grading_client=codex_client,
        rung_gate=rung_gate,
        difficulty_band_by_lo={
            target.learning_object_id: target.recommended_difficulty_band
            for target in plan.targets
        },
    )
    surface_gate = gates.surface_gate
    persona_gate = gates.persona_gate
    pair_gate = gates.pair_gate
    patch_id = generate_authoring_proposal(
        root,
        codex_client,
        subjects=_target_subjects(plan, subjects),
        instructions=_practice_expansion_instructions(
            plan,
            extra_instructions=extra_instructions,
            focus_facets=focus_facets,
            mode_mix=mode_mix,
        ),
        focus_concepts=focus_concepts,
        focus_facets=focus_facets,
        source_refs=source_refs,
        codex_revision=codex_revision,
        merge_context_source_refs=bool(source_refs),
        row_transform=gates,
    )
    violations: list[str] = []
    warnings: list[str] = []
    if mode_mix:
        violations, warnings = _mode_mix_compliance(plan, mode_mix, repository.proposal_items(patch_id))
    return PracticeExpansionResult(
        patch_id=patch_id,
        plan=plan,
        mode_mix_violations=violations,
        mode_mix_warnings=warnings,
        rung_violations=(
            rung_gate.violations
            + surface_gate.violations
            + persona_gate.violations
            # Meas §3.A4: a refused pair is a hard authoring failure like any
            # other gate's, and it surfaces on the same list so a caller that
            # already reports violations does not need to learn a new field.
            + pair_gate.violations
        ),
        rung_warnings=rung_gate.warnings + persona_gate.warnings,
    )


def build_goal_practice_plan(
    vault: LoadedVault,
    repository: Repository,
    goal,
    *,
    target_items_per_lo: int = 5,
    max_new_per_lo: int = 3,
) -> tuple[PracticeExpansionPlan, list[str]]:
    """Expansion plan covering a goal's scope, sized by *practicable* supply.

    Goal population differs from post-probe expansion in two deliberate ways:
    the completed-probe gate is waived (the goal itself is the learner's
    declared intent to practice these LOs), and items reserved for a held-out
    exam pool do not count as existing supply (they are quarantined from the
    scheduler, so they cannot cover the goal's facets). Returns the plan plus
    the goal's currently at-risk facet ids for generation focus.
    """

    from learnloop.services.goal_projection import goal_report, resolve_goal_scope

    scope = resolve_goal_scope(vault, goal, repository)
    if not scope:
        raise PracticeExpansionError(f"Goal {goal.id} has no active learning objects in scope.")
    reserved = repository.reserved_exam_pool_item_ids()
    plan = build_practice_expansion_plan(
        vault,
        repository,
        target_items_per_lo=target_items_per_lo,
        max_new_per_lo=max_new_per_lo,
        learning_object_ids=sorted(scope),
        require_completed_probe=False,
        exclude_item_ids=reserved,
    )
    report = goal_report(vault, repository, goal)
    at_risk_facets = sorted({facet.facet_id for facet in report.facets if not facet.on_track})
    return plan, at_risk_facets


def generate_goal_practice_proposal(
    root: Path,
    codex_client: AIProviderClient,
    *,
    goal_id: str,
    target_items_per_lo: int = 5,
    max_new_per_lo: int = 3,
    extra_instructions: str | None = None,
    codex_revision: str | None = None,
) -> PracticeExpansionResult:
    """Generate Practice Items that populate an active goal's scope.

    See ``build_goal_practice_plan`` for how goal population differs from the
    post-probe expansion path. The goal's at-risk facets become the generation
    focus so new items retire the facets that block the goal first.
    """

    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    sync_vault_state(vault, repository)
    goal = next((candidate for candidate in vault.goals if candidate.id == goal_id), None)
    if goal is None:
        raise PracticeExpansionError(f"Unknown goal id: {goal_id}")
    if goal.status != "active":
        raise PracticeExpansionError(f"Goal {goal_id} is not active (status={goal.status}).")
    plan, at_risk_facets = build_goal_practice_plan(
        vault,
        repository,
        goal,
        target_items_per_lo=target_items_per_lo,
        max_new_per_lo=max_new_per_lo,
    )
    if not plan.targets:
        raise PracticeExpansionError(
            f"Goal {goal_id}'s learning objects already have enough practicable items."
        )
    goal_preamble = (
        f"These items populate practice for the learner's goal '{goal.title}' ({goal.id}), "
        f"target recall {goal.target_recall:.2f}"
        + (f" by {goal.due_at}" if goal.due_at else "")
        + "."
    )
    merged_instructions = (
        f"{goal_preamble} {extra_instructions}" if extra_instructions else goal_preamble
    )
    rung_gate = _RungGate(repository, plan)
    # Meas §3.0 (see `generate_post_probe_practice_proposal` for the tier note);
    # Meas §3.A4 band note ditto. One shared composition: `authoring_gates`.
    gates = build_instrument_gates(
        vault,
        repository,
        grading_client=codex_client,
        rung_gate=rung_gate,
        difficulty_band_by_lo={
            target.learning_object_id: target.recommended_difficulty_band
            for target in plan.targets
        },
    )
    surface_gate = gates.surface_gate
    persona_gate = gates.persona_gate
    pair_gate = gates.pair_gate
    patch_id = generate_authoring_proposal(
        root,
        codex_client,
        subjects=_target_subjects(plan, None),
        instructions=_practice_expansion_instructions(
            plan,
            extra_instructions=merged_instructions,
            focus_facets=at_risk_facets or None,
        ),
        focus_concepts=list(goal.facet_scope.concepts) or None,
        focus_facets=at_risk_facets or None,
        codex_revision=codex_revision,
        row_transform=gates,
    )
    return PracticeExpansionResult(
        patch_id=patch_id,
        plan=plan,
        rung_violations=(
            rung_gate.violations
            + surface_gate.violations
            + persona_gate.violations
            # Meas §3.A4: a refused pair is a hard authoring failure like any
            # other gate's, and it surfaces on the same list so a caller that
            # already reports violations does not need to learn a new field.
            + pair_gate.violations
        ),
        rung_warnings=rung_gate.warnings + persona_gate.warnings,
    )


@dataclass(frozen=True)
class LeakageBlock:
    """One generated practice item blocked by the held-out leakage gate (§8.5)."""

    client_item_id: str | None
    learning_object_id: str | None
    findings: list[dict[str, str]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "client_item_id": self.client_item_id,
            "learning_object_id": self.learning_object_id,
            "findings": self.findings,
        }


@dataclass(frozen=True)
class CrossSourcePracticeResult:
    patch_id: str
    plan: PracticeExpansionPlan
    # Multi-source grounding actually placed in the generation context, per LO.
    context_span_count: int
    leakage_blocked: list[LeakageBlock] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "plan": self.plan.as_dict(),
            "context_span_count": self.context_span_count,
            "leakage_blocked": [block.as_dict() for block in self.leakage_blocked],
        }


def _blueprint_shaping(vault: LoadedVault, learning_object) -> list[dict[str, Any]]:
    """Task-family / capability distribution from the LO's assessment blueprints.

    Shapes generation toward the exam's declared task families (§8.5). Weights are
    normalized across the LO's blueprints; capabilities come from recipe components."""

    families: list[dict[str, Any]] = []
    total = sum(max(bp.weight, 0.0) for bp in (learning_object.blueprints or []))
    for blueprint in learning_object.blueprints or []:
        capabilities = sorted(
            {
                comp.capability
                for recipe in blueprint.recipes or []
                for comp in [*(recipe.all_of or []), *(recipe.any_of or [])]
            }
        )
        families.append(
            {
                "task_family": blueprint.id,
                "weight": round(blueprint.weight, 4),
                "normalized_weight": round(blueprint.weight / total, 4) if total > 0 else 0.0,
                "capabilities": capabilities,
            }
        )
    return families


def _cross_source_instructions(
    plan: PracticeExpansionPlan,
    context_by_lo: dict[str, list[dict[str, Any]]],
    shaping_by_lo: dict[str, list[dict[str, Any]]],
    *,
    extra_instructions: str | None,
    focus_facets: list[str] | None,
) -> str:
    lines = [
        "Generate additional LearnLoop Practice Items grounded in MULTIPLE cited sources.",
        "Create only practice_item proposal items; do not create Learning Objects, concepts, or edges.",
        "Each new Practice Item must attach to one of the target learning_object_id values below.",
        "CROSS_SOURCE_CONTEXT gives bounded grounding spans per learning object: the "
        "semantic_authority span defines the concept; alternate/support spans offer "
        "variety in wording and representation. Ground items in this material; prefer the "
        "semantic-authority span for the canonical claim and draw surface variety from the alternates.",
        "BLUEPRINT_SHAPING gives the assessment task-family distribution per learning object. "
        "Distribute generated items across task families roughly in proportion to normalized_weight, "
        "and exercise the listed capabilities.",
        "HARD leakage rule (enforced by a deterministic code gate, not trust): NEVER reproduce "
        "held-out exam wording, numbers, diagrams, or answer-structure fingerprints. Generate a fresh "
        "surface. An item that echoes held-out material is blocked and cannot be applied.",
        "Reuse existing facet ids from each target's existing_evidence_facets; mint a new facet id only "
        "when no existing facet covers the item.",
        "Calibrate difficulty to each target's recommended_difficulty_band (~70-85% expected success). "
        "For each target, create exactly requested_new_items Practice Items.",
        "Depth waypoint: each target names a depth waypoint (waypoint_slug, capability, target_task_features). "
        "Author every item AT that waypoint: set `capability` to the target capability exactly and every "
        "task_features dimension to the target value (a deterministic gate rejects overshoot). Keep "
        "retrieval_demand/transfer_distance/scaffold_level inside float_proxy_bands. Difficulty varies WITHIN "
        "the waypoint - never change the waypoint to change difficulty.",
        _CONSTRUCTED_RESPONSE_RULE,
        _BLUEPRINT_SPREAD_RULE,
        _CONJUNCTIVE_ITEM_RULE,
        # Only A5 on this route. The cross-source path is already carrying a
        # multi-source grounding contract and a hard leakage screen, and A2/A3/A4
        # each add a second authoring contract on top of that; A5 adds a field to
        # items the route was authoring anyway, and it is the producer Stage 7's
        # planted-ground-truth harness consumes, so it is the one worth the
        # tokens here.
        _DISCRIMINATION_PROFILE_RULE,
    ]
    # Same rung-correct rule as the post-probe path: BLUEPRINT_SHAPING already
    # named the contract's capabilities as a *distribution*, which the model was
    # free to read as advice; commissioned_cells names them as the requirement.
    if any(target.commissioned_cells for target in plan.targets):
        lines.append(_CONTRACT_CELL_RULE)
    lines += [
        f"Targets: {[target.as_dict() for target in plan.targets]}",
        f"CROSS_SOURCE_CONTEXT: {json.dumps(context_by_lo, sort_keys=True, separators=(",", ":"))}",
        f"BLUEPRINT_SHAPING: {json.dumps(shaping_by_lo, sort_keys=True, separators=(",", ":"))}",
    ]
    if focus_facets:
        lines.append(
            "Focus facets: prioritize items whose evidence_facets target these facet ids: "
            f"{sorted(focus_facets)}."
        )
    if extra_instructions:
        lines.append(f"Additional instructions: {extra_instructions}")
    return "\n".join(lines)


def generate_cross_source_practice_proposal(
    root: Path,
    codex_client: AIProviderClient,
    *,
    subjects: list[str] | None = None,
    target_items_per_lo: int = 5,
    max_new_per_lo: int = 3,
    max_los: int | None = None,
    focus_concepts: list[str] | None = None,
    focus_facets: list[str] | None = None,
    learning_object_ids: list[str] | None = None,
    max_spans_per_item: int = 4,
    extra_instructions: str | None = None,
    codex_revision: str | None = None,
) -> CrossSourcePracticeResult:
    """Assessment-blueprint-driven, multi-source practice generation with HARD
    leakage controls (spec §8.5, ING M8).

    Draws bounded ``entity_source_links`` grounding spans (semantic authority first,
    alternates for variety) per target LO, shaped by the LO's assessment blueprints,
    and runs a deterministic held-out leakage gate over every generated surface: any
    item that reproduces held-out exam wording/numbers is blocked (never auto-applied
    and marked invalid). Per-item context is capped at ``max_spans_per_item`` so it
    does not grow with source count (KM §12.9)."""

    from learnloop.services.practice_leakage import (
        build_cross_source_spans,
        build_held_out_inventory,
        screen_practice_payload,
    )

    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    sync_vault_state(vault, repository)
    plan = build_practice_expansion_plan(
        vault,
        repository,
        subjects=subjects,
        target_items_per_lo=target_items_per_lo,
        max_new_per_lo=max_new_per_lo,
        max_los=max_los,
        focus_concepts=focus_concepts,
        learning_object_ids=learning_object_ids,
    )
    if not plan.targets:
        raise PracticeExpansionError("No completed probe Learning Objects need more Practice Items.")

    context_by_lo: dict[str, list[dict[str, Any]]] = {}
    shaping_by_lo: dict[str, list[dict[str, Any]]] = {}
    span_count = 0
    for target in plan.targets:
        lo = vault.learning_objects.get(target.learning_object_id)
        if lo is None:
            continue
        spans = build_cross_source_spans(
            vault, repository, target.learning_object_id, max_spans_per_item=max_spans_per_item
        )
        context_by_lo[target.learning_object_id] = [span.as_dict() for span in spans]
        shaping_by_lo[target.learning_object_id] = _blueprint_shaping(vault, lo)
        span_count += len(spans)

    held_out = build_held_out_inventory(vault, repository, subject_ids=subjects)
    lo_by_client: dict[str, str] = {}
    blocked: list[LeakageBlock] = []

    def _leakage_gate(rows: list[dict[str, Any]]) -> None:
        for row in rows:
            if row.get("item_type") != "practice_item":
                continue
            payload = row.get("payload")
            if not isinstance(payload, dict):
                continue
            findings = screen_practice_payload(payload, held_out)
            if not findings:
                continue
            # A gate, not a prompt hope: block the item hard. It never auto-applies
            # and is marked invalid so review cannot silently accept leaked content.
            row["_auto_apply"] = False
            row["validation_status"] = "invalid"
            existing = row.get("validation_errors") or []
            row["validation_errors"] = ["held_out_leakage"] + list(existing)
            blocked.append(
                LeakageBlock(
                    client_item_id=row.get("client_item_id"),
                    learning_object_id=payload.get("learning_object_id"),
                    findings=findings,
                )
            )

    rung_gate = _RungGate(repository, plan)
    # Meas §3.0 / §3.A4 notes as on the other routes; the cross-source route
    # additionally runs its leakage gate FIRST, as a `leading` hook on the one
    # shared composition.
    gates = build_instrument_gates(
        vault,
        repository,
        grading_client=codex_client,
        rung_gate=rung_gate,
        difficulty_band_by_lo={
            target.learning_object_id: target.recommended_difficulty_band
            for target in plan.targets
        },
        leading=(_leakage_gate,),
    )
    patch_id = generate_authoring_proposal(
        root,
        codex_client,
        subjects=_target_subjects(plan, subjects),
        instructions=_cross_source_instructions(
            plan,
            context_by_lo,
            shaping_by_lo,
            extra_instructions=extra_instructions,
            focus_facets=focus_facets,
        ),
        focus_concepts=focus_concepts,
        focus_facets=focus_facets,
        codex_revision=codex_revision,
        prompt_version=PRACTICE_GENERATION_PROMPT_VERSION,
        row_transform=gates,
    )
    return CrossSourcePracticeResult(
        patch_id=patch_id,
        plan=plan,
        context_span_count=span_count,
        leakage_blocked=blocked,
    )


def _validate_mode_mix(mode_mix: dict[str, int] | None) -> None:
    if not mode_mix:
        return
    for mode, count in mode_mix.items():
        if not isinstance(mode, str) or not mode.strip():
            raise PracticeExpansionError("mode_mix practice modes must be non-empty strings")
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise PracticeExpansionError(f"mode_mix count for '{mode}' must be an integer >= 1")


def _validate_named_learning_objects(
    vault: LoadedVault,
    repository: Repository,
    learning_object_ids: list[str],
    *,
    require_completed_probe: bool = True,
    contract_backed: set[str] | None = None,
) -> None:
    """Named --los targets must exist, be active, and have a completed probe.

    Naming an LO bypasses only the item-count deficit gate; the completed-probe
    gate stays (evidence-not-mastery: generation targets follow probe evidence)
    unless the caller explicitly waives it (goal population, where the goal
    itself is the learner's declared intent to practice these LOs) or the LO is
    in ``contract_backed`` — its blueprint names commissionable contract cells,
    so the contract, not probe evidence, is the authority on what gets authored
    (Stage 5.1) and the plan loop would waive the same LO anyway.
    """

    contract_backed = contract_backed or set()
    for lo_id in learning_object_ids:
        learning_object = vault.learning_objects.get(lo_id)
        if learning_object is None:
            raise PracticeExpansionError(f"Unknown learning object id: {lo_id}")
        if learning_object.status != "active":
            raise PracticeExpansionError(f"Learning object {lo_id} is not active (status={learning_object.status}).")
        if not require_completed_probe or lo_id in contract_backed:
            continue
        probe_state = repository.probe_state(lo_id)
        if probe_state is None or probe_state.status != "complete":
            raise PracticeExpansionError(
                f"Learning object {lo_id} has no completed probe phase; finish its probes before generating practice."
            )


#: Surfaces that mean "pick one of these" rather than "produce an answer".
# `_SELECTED_RESPONSE_PATTERNS` / `_SelectedResponseGate` / `_chain_gates` now
# live in `authoring_gates` (imported above under their historical names) so
# the ingest lanes consume the SAME instrument-gate implementations instead of
# a private subset that could drift.


def _contrast_pair_requests_by_facet(
    vault: LoadedVault, repository: Repository
) -> dict[str, list[dict[str, Any]]]:
    """Canonical facet id -> the A4 authoring requests that name it (Meas §3.A4).

    Indexed by facet rather than by learning object because an identifiability
    finding is a statement about a FACET PAIR — it has no learning object, and
    inventing one would attach the request to whichever LO happened to be
    alphabetically first. The routing to targets happens in
    :func:`_contrast_pair_requests_for`, off the LO's own facet union, so a
    finding reaches every LO that could honestly discharge it.

    Fail-soft: identifiability runs over the whole registry and a malformed
    neighborhood should degrade authoring to "no pair requests", never abort a
    generation the learner is waiting on.
    """

    from learnloop.services.contrast_pairs import commission_contrast_pairs

    try:
        plan = commission_contrast_pairs(vault, repository)
    except Exception:  # pragma: no cover - defensive
        import logging

        logging.getLogger(__name__).warning(
            "contrast-pair commissioning failed; authoring proceeds without it",
            exc_info=True,
        )
        return {}
    by_facet: dict[str, list[dict[str, Any]]] = {}
    for request in plan.commissioned:
        payload = request.as_dict()
        for facet in request.facet_ids:
            by_facet.setdefault(vault.canonical_facet_id(str(facet)), []).append(payload)
    return by_facet


def _contrast_pair_requests_for(
    by_facet: Mapping[str, list[dict[str, Any]]], learning_object: Any
) -> list[dict[str, Any]]:
    """The requests this LO can discharge: those naming a facet its blueprints use.

    Deduplicated by ``target_key`` and ordered by the commissioning queue rank,
    so an LO that could close two findings is told to close the higher-priority
    one first — the same "consume a prioritized queue rather than invent a second
    one" discipline ``commission_plan`` follows.
    """

    from learnloop.vault.models import learning_object_facet_union

    if not by_facet:
        return []
    seen: dict[str, dict[str, Any]] = {}
    for facet in learning_object_facet_union(learning_object):
        for request in by_facet.get(str(facet), ()):  # type: ignore[arg-type]
            seen.setdefault(str(request["target_key"]), request)
    return sorted(seen.values(), key=lambda request: int(request["queue_rank"]))


class _RungGate:
    """Deterministic rung admission over persisted proposal rows (row_transform
    seam): a generated item that overshoots or contradicts its target waypoint is
    forced off the auto-apply route; the diagnostics surface on the result.
    Fail-closed: an exception here aborts persistence, never silently admits.

    Stage 5.1 changes *which* waypoint an item is held to, not how strictly. For a
    contract-bearing LO the admission set is the set of capabilities that LO's own
    blueprint names, and each item is validated against the trajectory waypoint of
    the capability it declares — so an item authored at the contract's capability is
    admitted where it used to hard-fail against the mastery-band waypoint, and an
    item at a capability the contract never names hard-fails where it used to pass.
    That inversion *is* item 5.1: §5.4 files credit per ``(facet, capability)``
    cell, so an off-contract rung produces evidence that can never close the cell.
    An LO with no contract cells keeps the previous single-rung behaviour exactly.
    """

    def __init__(self, repository: Repository, plan: PracticeExpansionPlan):
        from learnloop.services.activity_patterns import ensure_capability_alias_registry

        ensure_capability_alias_registry(repository)
        self._repository = repository
        self._rung_by_lo: dict[str, RungTarget] = {
            target.learning_object_id: target.rung
            for target in plan.targets
            if target.rung is not None
        }
        # LO -> {capability the contract names: the waypoint authoring AT it}. The
        # value is ``None`` for ``coordination``: the contract legitimately asks for
        # it (§5.8.3) but the default trajectory has no waypoint there, so the item
        # is admitted with a review diagnostic rather than validated against a
        # waypoint that does not exist or silently re-aimed one rung down.
        self._contract_rungs_by_lo: dict[str, dict[str, RungTarget | None]] = {
            target.learning_object_id: {
                capability: capability_rung(repository, capability)
                for capability in target.contract_capabilities
            }
            for target in plan.targets
            if target.contract_capabilities
        }
        self._band_by_lo: dict[str, tuple[float, float]] = {
            target.learning_object_id: target.recommended_difficulty_band
            for target in plan.targets
        }
        self.violations: list[str] = []
        self.warnings: list[str] = []

    def __call__(self, rows: list[dict[str, Any]]) -> None:
        for row in rows:
            if row.get("item_type") != "practice_item" or row.get("operation") != "create":
                continue
            payload = row.get("payload")
            if not isinstance(payload, dict):
                continue
            learning_object_id = str(payload.get("learning_object_id") or "")
            ref = str(row.get("client_item_id") or payload.get("id") or "item")
            self._check_difficulty_band(row, payload, learning_object_id, ref)
            rung, diagnostics = self._resolve_rung(payload, learning_object_id, ref)
            if rung is not None:
                diagnostics = diagnostics + validate_item_against_rung(
                    self._repository, payload=payload, rung=rung
                )
            hard = [d for d in diagnostics if d.severity == "hard_fail"]
            soft = [d for d in diagnostics if d.severity != "hard_fail"]
            self.violations.extend(f"{ref}: {d.message}" for d in hard)
            self.warnings.extend(f"{ref}: {d.message}" for d in soft)
            if hard:
                row["_auto_apply"] = False
                row["validation_status"] = "warning" if row.get("validation_status") == "valid" else row.get("validation_status")
                errors = list(row.get("validation_errors") or [])
                errors.extend(f"rung_target: {d.message}" for d in hard)
                row["validation_errors"] = errors
            if isinstance(payload.get("task_features"), dict):
                payload["task_feature_schema"] = TASK_FEATURE_SCHEMA_SLUG

    def _resolve_rung(
        self,
        payload: dict[str, Any],
        learning_object_id: str,
        ref: str,
    ) -> tuple[RungTarget | None, list[GateDiagnostic]]:
        """The waypoint this item is admitted against, plus resolution diagnostics.

        Three arms, closed over the possibilities:

        * **no contract** — legacy LO (no blueprint components, e.g. every LO in
          ``fixtures/arxiv``): the plan's single mastery-band rung, unchanged;
        * **on-contract capability** — the trajectory waypoint at *that*
          capability, so the contract decides the rung; ``coordination`` resolves
          to no waypoint and earns a review diagnostic naming the obligation;
        * **off-contract capability** — hard fail. This is the 72% lever: an item
          one rung below the requirement files evidence into a cell the contract
          did not ask for, and no amount of practice on it can close the cell.
        """

        contract = self._contract_rungs_by_lo.get(learning_object_id)
        if not contract:
            return self._rung_by_lo.get(learning_object_id), []

        def diag(severity: str, message: str, action: str) -> GateDiagnostic:
            return GateDiagnostic(
                gate="contract_capability",
                severity=severity,  # type: ignore[arg-type]
                entity_refs=(ref,),
                message=message,
                suggested_action=action,
            )

        declared = payload.get("capability")
        if not declared:
            # Missing metadata is not an off-contract claim; fall through to the
            # plan rung so `validate_item_against_rung` raises its existing
            # "missing capability/task_features" review diagnostic once.
            return self._rung_by_lo.get(learning_object_id), []
        mapped = map_capability(self._repository, str(declared))
        if mapped == LEGACY_UNMAPPED:
            return self._rung_by_lo.get(learning_object_id), []
        if mapped not in contract:
            return None, [
                diag(
                    "hard_fail",
                    f"capability {mapped!r} is not one this learning object's contract "
                    f"names ({', '.join(sorted(contract))}); evidence is filed per "
                    "(facet, capability) cell, so it cannot close any required cell",
                    "author at one of the contract's capabilities (see commissioned_cells)",
                )
            ]
        rung = contract[mapped]
        if rung is None:
            diagnostics = [
                diag(
                    "review",
                    f"contract capability {mapped!r} has no default-trajectory waypoint; "
                    "a whole-task instrument needs a reviewed depth envelope",
                    "review the item as a whole-task capstone, or lower the blueprint component",
                )
            ]
            # No waypoint means no task-feature bounds to check, but the one
            # structural rule about `coordination` still holds and would otherwise
            # go unchecked here (it normally lives in `validate_item_against_rung`):
            # a coordination observation IS a whole-task observation.
            features = payload.get("task_features")
            if isinstance(features, Mapping) and features.get("span") != "whole_task":
                diagnostics.append(
                    diag(
                        "hard_fail",
                        f"{mapped} requires span=whole_task, not {features.get('span')!r}",
                        "use a whole-task span or a different capability",
                    )
                )
            return None, diagnostics
        return rung, []

    #: How far outside its band an item's difficulty may sit before the batch is
    #: held for review. One deliberately-harder transfer item per target is
    #: allowed by the instructions, so this only catches systematic drift.
    _DIFFICULTY_BAND_TOLERANCE = 0.10

    def _check_difficulty_band(
        self,
        row: dict[str, Any],
        payload: dict[str, Any],
        learning_object_id: str,
        ref: str,
    ) -> None:
        """Flag items authored well outside their recommended difficulty band.

        Nothing used to check this, and the model reliably pinned every item to
        ``difficulty: 0.0`` against bands like (0.15, 0.33). A floored difficulty
        is not cosmetic: it sets the IRT ``b`` the mastery EKF predicts against,
        so success is expected in advance and the observation carries almost no
        information — and it collapses the exam pool's difficulty stratification,
        which files every item in the same stratum.
        """

        band = self._band_by_lo.get(learning_object_id)
        declared = payload.get("difficulty")
        if band is None or declared is None:
            return
        try:
            value = float(declared)
        except (TypeError, ValueError):
            return
        low, high = min(band), max(band)
        if low - self._DIFFICULTY_BAND_TOLERANCE <= value <= high + self._DIFFICULTY_BAND_TOLERANCE:
            return
        message = (
            f"difficulty {value:g} is outside the recommended band "
            f"[{low:g}, {high:g}] (tolerance {self._DIFFICULTY_BAND_TOLERANCE:g})"
        )
        self.warnings.append(f"{ref}: {message}")
        row["_auto_apply"] = False
        errors = list(row.get("validation_errors") or [])
        errors.append(f"difficulty_band: {message}")
        row["validation_errors"] = errors


def _mode_mix_compliance(
    plan: PracticeExpansionPlan,
    mode_mix: dict[str, int],
    proposal_items: list[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    """Check the persisted proposal against the requested per-LO mode counts.

    The teach_back count is a hard requirement (violations); other modes only
    soft-warn on mismatch, since the reviewer can still accept a useful batch.
    """

    counts: dict[tuple[str, str], int] = {}
    for item in proposal_items:
        if item.get("item_type") != "practice_item" or item.get("operation") != "create":
            continue
        payload = item.get("edited_payload") if item.get("edited_payload") is not None else item.get("payload")
        if not isinstance(payload, dict):
            continue
        lo_id = payload.get("learning_object_id")
        mode = payload.get("practice_mode")
        if not lo_id or not mode:
            continue
        counts[(str(lo_id), str(mode))] = counts.get((str(lo_id), str(mode)), 0) + 1
    violations: list[str] = []
    warnings: list[str] = []
    for target in plan.targets:
        for mode, requested in sorted(mode_mix.items()):
            actual = counts.get((target.learning_object_id, mode), 0)
            if actual == requested:
                continue
            message = (
                f"{target.learning_object_id}: requested {requested} '{mode}' item(s), proposal has {actual}"
            )
            if mode == TEACH_BACK_PRACTICE_MODE:
                violations.append(message)
            else:
                warnings.append(message)
    return violations, warnings


def _active_practice_item_counts(
    vault: LoadedVault,
    repository: Repository,
    *,
    exclude_item_ids: set[str] | None = None,
) -> dict[str, int]:
    states = repository.practice_item_states()
    excluded = exclude_item_ids or set()
    counts: dict[str, int] = {}
    for item in vault.practice_items.values():
        if item.id in excluded:
            continue
        state = states.get(item.id)
        if state is not None and not state.active:
            continue
        counts[item.learning_object_id] = counts.get(item.learning_object_id, 0) + 1
    return counts


def _blueprint_components(learning_object) -> list[dict[str, Any]]:
    """The distinct (facet, capability, role) requirements of an LO's blueprints.

    Readiness is a conjunction over these components (``blueprint_projection``),
    so an item batch that probes only one of them cannot raise the LO's projected
    readiness however well the learner answers. Handing the decomposition to the
    authoring model lets one batch spread across the requirement set instead of
    permuting a single surface.
    """

    components: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    def add(blueprint, component, role: str) -> None:
        key = (str(component.facet), str(component.capability), role)
        if key in seen:
            return
        seen.add(key)
        components.append(
            {
                "task_family": blueprint.id,
                "blueprint_weight": round(blueprint.weight, 4),
                "facet": component.facet,
                "capability": component.capability,
                "modality": component.modality,
                "role": role,
            }
        )

    for blueprint in learning_object.blueprints or []:
        for recipe in blueprint.recipes or []:
            for component in recipe.all_of or []:
                add(blueprint, component, "required")
            for component in recipe.any_of or []:
                add(blueprint, component, "alternative")
            if recipe.integration is not None:
                add(blueprint, recipe.integration, "integration")
    return components


def _active_surface_families(
    vault: LoadedVault, repository: Repository
) -> dict[str, list[str]]:
    """Surface families already in use per LO, so a batch cannot re-run them."""

    states = repository.practice_item_states()
    families: dict[str, set[str]] = {}
    for item in vault.practice_items.values():
        state = states.get(item.id)
        if state is not None and not state.active:
            continue
        if item.surface_family:
            families.setdefault(item.learning_object_id, set()).add(str(item.surface_family))
    return {lo_id: sorted(values) for lo_id, values in families.items()}


def _active_evidence_facet_unions(vault: LoadedVault, repository: Repository) -> dict[str, list[str]]:
    """Canonical facet vocabulary available to each Learning Object.

    Blueprints remain authoritative even before the first Practice Item exists;
    active item facets supplement them for legacy/ad-hoc vaults.  Reader-first
    bootstrapping otherwise hands an empty vocabulary to the authoring target at
    precisely the moment it must create the first items.
    """
    from learnloop.vault.models import learning_object_facet_union

    states = repository.practice_item_states()
    unions: dict[str, set[str]] = {
        learning_object.id: {
            vault.canonical_facet_id(str(facet))
            for facet in learning_object_facet_union(learning_object)
        }
        for learning_object in vault.learning_objects.values()
    }
    for item in vault.practice_items.values():
        state = states.get(item.id)
        if state is not None and not state.active:
            continue
        unions.setdefault(item.learning_object_id, set()).update(
            vault.canonical_facet_id(facet) for facet in item.evidence_facets
        )
    return {learning_object_id: sorted(facets) for learning_object_id, facets in unions.items()}


def _target_subjects(plan: PracticeExpansionPlan, subjects: list[str] | None) -> list[str]:
    if subjects:
        return subjects
    return sorted({subject for target in plan.targets for subject in target.subjects})


#: Hard ban on selected-response surfaces. Enforced downstream by
#: ``_SelectedResponseGate``; stated here so the model does not author them at all.
_CONSTRUCTED_RESPONSE_RULE = (
    "NEVER author a selected-response item. The learner must PRODUCE the answer, never pick it. "
    "Forbidden surfaces: lettered or numbered option lists (\"A. ... B. ... C. ...\"), "
    "\"reply with the letter\", \"select the correct option\", \"which of the following\", and "
    "true/false questions. This holds at EVERY depth waypoint including the easiest: a low-demand "
    "item is made easy by narrowing scope and adding a cue, NOT by supplying candidate answers. "
    "Multiple choice measures option elimination rather than the capability the Learning Object "
    "names, and it is near-worthless as evidence - an easy recognition item's success is already "
    "predicted, so answering it correctly moves the learner model by almost nothing. "
    "To make an item easier: ask for one specific step, name the object to work with, or give a "
    "worked analogue first - then ask the learner to state, compute, derive, or explain."
)

#: Blueprint coverage. Readiness is a conjunction over blueprint components, so a
#: batch that probes one component cannot move the projection (see
#: ``_blueprint_components``).
_BLUEPRINT_SPREAD_RULE = (
    "COVER THE BLUEPRINT, do not permute one surface. Each target lists blueprint_components: the "
    "distinct (facet, capability, role) requirements its assessment blueprint is built from. The "
    "Learning Object's readiness is a CONJUNCTION over those components, so a batch that probes "
    "only one of them cannot demonstrate the Learning Object however well the learner answers. "
    "Spread the target's requested_new_items across as many DISTINCT blueprint_components as the "
    "count allows - prefer a new component over a second item on one already covered, weighting by "
    "blueprint_weight - and set each item's evidence_facets to the component(s) it actually probes. "
    "Within a batch no two items may share a surface_family, reuse a surface_family listed in the "
    "target's existing_surface_families, or differ only in wording, numbers, or which option is "
    "correct. Vary the representation (symbolic / verbal / worked / counterexample / applied) and "
    "the answer's shape. Each item must state in its rationale which blueprint component it probes."
)

#: Conjunctive instruments (Meas §3.A1, plan item 6.1). §2 F2/F3 measured the two
#: reasons cells-per-question sits near 1: a generated criterion could not author
#: ``targets`` at all, and the spread rule pushed one blueprint component per item
#: by policy. The schema half is fixed (``CriterionTargetPayload``); this is the
#: authoring half.
#:
#: The measurement spec asks for the spread rule to be *inverted*. The plan
#: deliberately does not adopt that: a pool holding only capstones starves
#: diagnosis, because a conjunctive failure localizes only when the learner got
#: far enough to diverge somewhere specific, and a weak learner fails at step 1 of
#: every capstone. So authoring produces BOTH shapes and selection picks between
#: them from the posterior (``services/conjunctive_items.conjunctive_fit``).
_CONJUNCTIVE_ITEM_RULE = (
    "AUTHOR CAPSTONES ALONGSIDE THE DECOMPOSED ITEMS. Where a target's "
    "blueprint_components (or commissioned_cells) can be honestly required by ONE task - a task a "
    "learner cannot complete without genuinely using all of them - author that task as well, in "
    "ADDITION to the decomposed items, not instead of them. Both shapes are wanted: the capstone "
    "measures several cells in one question when the learner succeeds, the decomposed items say "
    "WHICH cell broke when they do not, and the scheduler chooses between them from the learner's "
    "current posterior. At most one capstone per target. "
    "A capstone declares what it measures through per-criterion `targets`, a list of "
    "{facet, capability, role}: `role='primary'` is the step that criterion OWNS - the thing it "
    "is grading - and `role='supporting'` is a facet that step CONSUMES to get there. Give every "
    "criterion of a capstone exactly one primary target, and set `depends_on` to the criterion ids "
    "whose results that step builds on, so a divergence at step 2 is not scored as failure at "
    "steps 3 and 4. "
    "`role` here is NOT the blueprint component role (required / alternative / integration); they "
    "are different vocabularies and a criterion target never uses the blueprint words. "
    "Only claim a supporting target when the work the learner must WRITE DOWN exercises that facet. "
    "A supporting target whose facet does not appear in the learner's trace earns nothing and is "
    "recorded as an unexercised claim, so listing facets speculatively makes the item look worse, "
    "not better. Never author supporting targets on an item with a single criterion: with nothing "
    "to consume, they are the item's own facets restated at a discount."
)

#: Meas §3.A5 discrimination profiles (plan item 6.4). Today an item can author
#: ONE link from a fatal error to a belief; the *shape* of the wrong answer — where
#: the diagnostic information actually lives — is discarded. Authoring it is the
#: change; it is then reused three times (the §3.0 gate's oracle, a grading prior,
#: A4's commissioning input) rather than re-derived.
_DISCRIMINATION_PROFILE_RULE = (
    "WRITE DOWN WHAT A WRONG ANSWER LOOKS LIKE, not only that one is wrong. For an item "
    "that can plausibly go wrong in a NAMED way, author `discrimination_profiles`: per "
    "candidate hypothesis, `hypothesis` (the belief in learner-model terms - what the "
    "learner thinks is TRUE, e.g. \"believes Q maps standard vectors to eigenbasis "
    "coefficients\", never \"used Q instead of Q^T\") and `observable_signature` (what a "
    "holder of that belief would actually WRITE on this item). "
    "The signature must be categorically different from expected_answer: if a "
    "belief-holder would produce the right answer anyway, the item is blind to that "
    "belief and a deterministic gate rejects it. "
    "Link `misconception_id` when the belief is already in the registry and `facet_id` "
    "when it contradicts a specific facet's claim - a linked profile can be corroborated "
    "elsewhere in the vault, an unlinked one cannot. "
    "Two or three profiles is plenty. Do NOT enumerate every way to be wrong: a profile "
    "set that covers everything gives the diagnostician nothing to reject, and rejecting "
    "them all is a first-class outcome the system watches for."
)

#: Meas §3.A2 laddered stems. The instrument that fills a ROW of the capability
#: grid rather than a cell, by amortizing the one cost that dominates assessment:
#: loading the problem into the learner's head.
_LADDERED_STEM_RULE = (
    "AMORTIZE ONE STIMULUS ACROSS THE CAPABILITY LADDER. Where a target's "
    "blueprint_components span two or more capabilities on the SAME facet, author a "
    "laddered stem: several items over ONE stimulus, each asking for that facet at a "
    "different capability - state it (retrieval), say which result applies "
    "(method_selection), execute it (procedure_execution), handle the case where "
    "coordinating the steps is the difficulty (coordination). "
    "Every part sets `laddered_stem` with the SAME `stem_id`, its own `part_index`, the "
    "shared `part_count`, and the stimulus text in `stimulus_md`; set "
    "`evidence_fingerprint.shared_stimulus_id` to the same stem_id. Each part declares "
    "its OWN `capability` - that is the whole point, and credit is filed per (facet, "
    "capability) cell. "
    "Parts at the same capability on one stimulus count as roughly ONE observation, so "
    "never author two parts in the same column; parts at different capabilities count "
    "separately. A 'stem' whose parts all sit at one capability is a set of near-clones."
)

#: Meas §3.A3 error hunts. Cheap per cell, and dangerous if authored casually:
#: an error any careful reader catches measures carefulness.
_ERROR_HUNT_RULE = (
    "ERROR HUNTS ARE REPAIR TASKS, NOT PROOFREADING. To author one, set `error_hunt` "
    "with a fully worked `worked_solution_md` and, in `planted_errors`, each error you "
    "planted: `step_ref` (which step holds it), `error_signature` (the text you planted, "
    "VERBATIM), `required_repair` (what a correct fix must produce), and `source`. "
    "`source` must be `misconception_registry` (with `misconception_id`) or "
    "`facet_error_signature` (with `facet_id`), and the signature must be the registry "
    "text itself - never an error you invented, which is an untyped instrument. "
    "The planted error must be INVISIBLE to a holder of that belief: it has to be what "
    "they would have written, so that only a learner who holds the facet can see it. A "
    "gate rejects a plant a belief-holder would catch. "
    "Ask the learner to CORRECT the solution, never merely to flag what is wrong. "
    "NEVER state how many errors there are, and NEVER hint that there is at least one. "
    "Author some error hunts with an EMPTY planted_errors list over genuinely correct "
    "work: a learner who 'finds' an error in a correct solution has told you what they "
    "believe, and the rotation is what stops 'there is always an error' from working."
)

#: Meas §3.A4 contrast pairs. The one instrument that removes the learner's
#: general ability as a nuisance parameter instead of averaging over it.
_CONTRAST_PAIR_RULE = (
    "A CONTRAST PAIR IS TWO PROMPTS DIFFERING IN EXACTLY ONE REQUIREMENT. Author both "
    "members together, and set on BOTH: `contrast_of` (the other member's id) and "
    "`differing_component` ({facet, capability, structural_change}) - the single "
    "requirement they differ on. "
    "The manipulation must change the STRUCTURE of the correct answer - whether a "
    "precondition holds, whether a theorem applies, what shape the answer takes - never "
    "only its numbers. Different numbers is a clone and is rejected. "
    "Both members must sit INDEPENDENTLY in the target's recommended_difficulty_band, "
    "and close to each other within it. Not 'one hard, one easy': a trivial member "
    "measures nothing and wastes the contrast. "
    "Give the two members DIFFERENT surface_family values where you honestly can, so the "
    "manipulation is not salient when they are served near each other. "
    "Give at least one member a `discrimination_profiles` entry describing the learner the pair "
    "is meant to catch - the one who succeeds on one member and fails the other. The authoring "
    "gate has to plant that learner to check the pair discriminates at all, and a pair it cannot "
    "plant is rejected. "
    "A target that lists contrast_pair_requests is telling you which facet pairs NO existing "
    "instrument in this vault can separate, in priority order. Author a pair for the first "
    "request the target's facets can honestly discharge; each request's `request` field says "
    "exactly what the pair has to separate."
)

#: Rung-correct authoring (Stage 5.1, Meas §5.8.2). Step 0 measured that 100% of
#: attempts hit a facet the contract requires and only 28% hit a required
#: ``(facet, capability)`` cell — every attempt on-topic, nearly three quarters of
#: the practice discarded by the capability axis alone. The prompt now hands the
#: model the cells themselves rather than one learner-derived waypoint, and
#: ``_RungGate`` enforces the admission set deterministically.
_CONTRACT_CELL_RULE = (
    "AUTHOR AT THE CAPABILITY THE CONTRACT NAMES. A target that lists commissioned_cells is "
    "telling you exactly which (facet, capability) obligations its own assessment blueprint "
    "declares that NO existing item can observe, already ordered by priority. Author the target's "
    "requested_new_items against commissioned_cells IN THAT ORDER - the first item for the first "
    "cell, the second for the second, and so on; only if there are more items than cells may you "
    "give a cell a second item. For each item: set `capability` to that cell's capability EXACTLY, "
    "set every dimension of `task_features` to that cell's target_task_features, include that "
    "cell's facet in evidence_facets with the dominant evidence weight, and name the cell's "
    "recipe_refs in the item's rationale. An item whose capability is not listed in the target's "
    "contract_capabilities is REJECTED by a deterministic gate: evidence credit is filed per "
    "(facet, capability) cell, so an item one rung below the requirement produces evidence that "
    "can NEVER close it, however well the learner answers. Difficulty still varies WITHIN the "
    "cell's capability - never trade the capability for an easier item."
)

_TEACH_BACK_GENERATION_GUIDANCE = (
    "teach_back item format: the learner teaches the concept to an AI that plays a curious naive student; "
    "the learner writes an opening explanation and then answers the student's follow-up questions. "
    "Write the item prompt as a teaching brief addressed to the learner, e.g. "
    "\"Explain the singular value decomposition to a student who has never seen it.\" "
    "Every teach_back item MUST set practice_mode='teach_back', attempt_types_allowed=['teach_back'], "
    "and carry its OWN grading_rubric (never rely on a default rubric). "
    "The rubric is two-tiered via the criterion `tier` field: include exactly one tier='core' criterion "
    "per facet in the item's evidence_facets (each core criterion probes that one facet), plus 2-3 "
    "tier='transfer' criteria that stress-test edge cases, what-if scenarios, or transfer to new situations "
    "(each transfer criterion also mapped to the facet(s) it stresses). "
    "criterion_facet_weights MUST carry one entry per rubric criterion (core and transfer) naming its facet(s), "
    "evidence_facets/evidence_weights must be set, and criterion points must sum to max_points (4 or less)."
)


def _ladder_capabilities(target: "PracticeExpansionTarget") -> int:
    """How many distinct capabilities this target's contract spans (Meas §3.A2).

    A laddered stem fills a ROW of the capability grid, so a target whose
    components all sit at one capability has no row to fill and is not told about
    the instrument.
    """

    capabilities = {
        str(component.get("capability") or "")
        for component in target.blueprint_components
        if component.get("capability")
    }
    capabilities.update(
        str(cell.get("capability") or "")
        for cell in target.commissioned_cells
        if cell.get("capability")
    )
    return len(capabilities)


def _practice_expansion_instructions(
    plan: PracticeExpansionPlan,
    *,
    extra_instructions: str | None,
    focus_facets: list[str] | None = None,
    mode_mix: dict[str, int] | None = None,
) -> str:
    lines = [
        "Generate additional LearnLoop Practice Items after completed probe phases.",
        "Create only practice_item proposal items; do not create new Learning Objects, concepts, or concept edges.",
        "Each new Practice Item must attach to one of the target learning_object_id values below.",
        "Prefer constructed_response items with attempt_types_allowed ['open_text'] unless the Learning Object clearly calls for another existing supported attempt type.",
        "Use review_route='review_required' unless a direct note or canonical source reference in the supplied context supports auto_apply.",
        "Avoid duplicating existing prompts in context; vary prompt surface and expected answer shape.",
        "Facet vocabulary: each target lists existing_evidence_facets, the facet ids already established for that Learning Object. When an item probes knowledge one of those facets names, reuse that exact facet id in evidence_facets/evidence_weights/criterion_facet_weights. Mint a new facet id only when the item probes knowledge no existing facet covers; never restate an existing facet under a new name.",
        "Calibrate each item's difficulty to its target's recommended_difficulty_band (~70-85% expected success - effortful but usually successful, the desirable-difficulty band), and set difficulty and difficulty_source='llm_estimate' accordingly. At most one item per target may be a harder transfer item above the band, and only when corrective feedback makes the challenge productive.",
        "Depth waypoint: each target names a depth waypoint (waypoint_slug, capability, target_task_features). Author every item AT that waypoint: set the item's `capability` to the target capability exactly, and set every dimension in `task_features` to the target's value (a deterministic gate rejects items that overshoot the waypoint). Keep retrieval_demand/transfer_distance/scaffold_level inside the target's float_proxy_bands.",
        "Difficulty varies WITHIN the waypoint - use surface, content, and specificity to hit the difficulty band. NEVER change the waypoint (capability, response form, transfer, span, scaffolding) to change difficulty.",
        _CONSTRUCTED_RESPONSE_RULE,
        _BLUEPRINT_SPREAD_RULE,
        _CONJUNCTIVE_ITEM_RULE,
        # Meas §3.A3/§3.A5 (plan item 6.4). Unconditional: both are things ANY
        # item can be, and an item that could plausibly go wrong in a named way
        # is not a property of the target payload.
        _ERROR_HUNT_RULE,
        _DISCRIMINATION_PROFILE_RULE,
        "For each target, create exactly requested_new_items Practice Items.",
    ]
    # A2 and A4 are stated only when a target can actually discharge them, on the
    # same reasoning `_CONTRACT_CELL_RULE` uses below: a rule naming fields no
    # target carries is noise the model has to read past on every call, and both
    # of these have a precondition that is visible in the plan.
    #
    # A2's precondition is a capability LADDER to climb — a target whose
    # blueprint components sit at one capability has no row to fill.
    if any(_ladder_capabilities(target) >= 2 for target in plan.targets):
        lines.append(_LADDERED_STEM_RULE)
    # A4 is "commissioned, not merely permitted" (§3.A4), so the rule appears when
    # identifiability has actually asked for a pair.
    if any(target.contrast_pair_requests for target in plan.targets):
        lines.append(_CONTRAST_PAIR_RULE)
    # Stated only when there is a contract to honour: on a legacy vault with no
    # authored blueprints the rule would name fields no target carries.
    if any(target.commissioned_cells for target in plan.targets):
        lines.append(_CONTRACT_CELL_RULE)
    lines.append(f"Targets: {[target.as_dict() for target in plan.targets]}")
    if mode_mix:
        mix = ", ".join(f"{count} item(s) with practice_mode='{mode}'" for mode, count in sorted(mode_mix.items()))
        lines.append(
            "Hard practice-mode mix constraint: for EACH target learning_object_id above, "
            f"produce exactly {mix}. Do not substitute other practice modes for these counts."
        )
        if TEACH_BACK_PRACTICE_MODE in mode_mix:
            lines.append(_TEACH_BACK_GENERATION_GUIDANCE)
    if focus_facets:
        lines.append(
            "Focus facets: prioritize items whose evidence_facets target these facet ids, "
            f"and weight them accordingly in evidence_weights: {sorted(focus_facets)}."
        )
    if extra_instructions:
        lines.append(f"Additional instructions: {extra_instructions}")
    return "\n".join(lines)


def _diagnostic_practice_instructions(
    plan: DiagnosticPracticePlan,
    *,
    extra_instructions: str | None,
) -> str:
    lines = [
        "Generate diagnostic LearnLoop Practice Items for unresolved intervention_needs.",
        "Create only practice_item proposal items; do not create Learning Objects, concepts, concept edges, rubrics, or error types.",
        "Create exactly one new Practice Item per target need_id.",
        "Each item must use the target learning_object_id, honor candidate_requirements, and must not duplicate the source_prompt.",
        "Use practice_mode='diagnostic_probe' and attempt_types_allowed ['diagnostic_probe', 'open_text', 'dont_know'].",
        "The item should test the target_facets directly, not reteach the full original item.",
        "Each target's diagnostic_focus is the frozen reason those target_facets were selected; use its primary_target_facet and repair_rationales to frame the probe. Treat rationale text as intent/framing only - the target_facets remain authoritative and evidence_facets must still equal target_facets.",
        "When diagnostic_focus.tutor_question_context is present, those are the learner's own questions asked while working - direct evidence of what they were confused about. Aim the probe at the mechanism/equation/interpretation the questions expose rather than merely re-asking the missed rubric criterion, while still keeping evidence_facets equal to target_facets.",
        "When diagnostic_focus.target_facet_marginals is present, it is the belief state per target facet (facet_solid vs facet_absent vs misconception:*). Design the probe so a learner holding each hypothesis would produce visibly different answers - the item should discriminate between those hypotheses, not just detect generic failure.",
        "Set difficulty within the recommended_difficulty_band: it lies on the learner's boundary (~50% expected success) so the probe is maximally diagnostic. Do not soften the probe toward an easy item, even on recall_failure - a boundary item that the learner can only sometimes answer is what discriminates the target facets.",
        "Use evidence_facets exactly equal to target_facets, evidence_weights normalized across target_facets, and repair_targets equal to target_facets.",
        "The grading_rubric must include at least one criterion per target facet and criterion_facet_weights must carry one entry per criterion naming its facet.",
        "Set retrieval_demand high (0.75-0.95), transfer_distance low-to-moderate (0.05-0.35), scaffold_level no higher than 0.35, and difficulty_source='llm_estimate'.",
        "Use only the supplied context.source_refs for source refs. Each item.source_ref_ids should include its target need_id and, when relevant, the target learning_object_id or source_practice_item_id. Do not invent source refs.",
        "Use review_route='review_required'; generated diagnostic probes must be reviewed before writing vault content.",
        f"Targets: {[target.as_dict() for target in plan.targets]}",
    ]
    if extra_instructions:
        lines.append(f"Additional instructions: {extra_instructions}")
    return "\n".join(lines)


def _diagnostic_item_ids_by_need(
    plan: DiagnosticPracticePlan,
    proposal_items: list[dict[str, Any]],
) -> dict[str, str]:
    target_need_ids = {target.need_id for target in plan.targets}
    item_ids_by_need: dict[str, str] = {}
    used_item_ids: set[str] = set()
    for item in proposal_items:
        if not _is_diagnostic_practice_item_row(item):
            continue
        source_ref_ids = {str(ref_id) for ref_id in item.get("source_ref_ids") or []}
        for need_id in sorted(source_ref_ids & target_need_ids):
            item_ids_by_need.setdefault(need_id, item["id"])
            used_item_ids.add(item["id"])

    unmatched_need_ids = [need_id for need_id in target_need_ids if need_id not in item_ids_by_need]
    unmatched_items = [
        item
        for item in proposal_items
        if _is_diagnostic_practice_item_row(item) and item["id"] not in used_item_ids
    ]
    if len(unmatched_need_ids) == 1 and len(unmatched_items) == 1:
        item_ids_by_need[unmatched_need_ids[0]] = unmatched_items[0]["id"]
    return item_ids_by_need


def _is_diagnostic_practice_item_row(item: dict[str, Any]) -> bool:
    if item.get("item_type") != "practice_item" or item.get("operation") != "create":
        return False
    payload = item.get("edited_payload") if item.get("edited_payload") is not None else item.get("payload")
    if not isinstance(payload, dict):
        return False
    if payload.get("practice_mode") == "diagnostic_probe":
        return True
    attempt_types = payload.get("attempt_types_allowed")
    return isinstance(attempt_types, list) and "diagnostic_probe" in attempt_types


def _repair_rationales_from_focus(diagnostic_focus: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not diagnostic_focus:
        return []
    raw_rationales = diagnostic_focus.get("repair_rationales")
    if not isinstance(raw_rationales, list):
        return []
    rationales: list[dict[str, Any]] = []
    for suggestion in raw_rationales:
        if not isinstance(suggestion, dict):
            continue
        rationale = str(suggestion.get("rationale") or "").strip()
        if not rationale:
            continue
        entry: dict[str, Any] = {"rationale": rationale}
        practice_mode = suggestion.get("practice_mode")
        if practice_mode:
            entry["practice_mode"] = str(practice_mode)
        targets = suggestion.get("target_evidence_families")
        if isinstance(targets, list):
            entry["target_evidence_families"] = [str(facet) for facet in targets]
        rationales.append(entry)
    return rationales


def _repair_rationales(repository: Repository, attempt_id: str | None) -> list[dict[str, Any]]:
    """Pull the grader's repair-suggestion rationales for the source attempt.

    These are the same free-text remediations surfaced to the learner as the
    diagnostic need. The target facet alone is a lossy handle for that intent,
    so we pass every rationale through as steering context and let the authoring
    model choose which to honor; the target_facets remain authoritative.
    """

    if not attempt_id:
        return []
    feedback = repository.fetch_attempt_feedback_metadata(attempt_id)
    if feedback is None:
        return []
    rationales: list[dict[str, Any]] = []
    for suggestion in feedback.get("repair_suggestions", []):
        if not isinstance(suggestion, dict):
            continue
        rationale = str(suggestion.get("rationale") or "").strip()
        if not rationale:
            continue
        entry: dict[str, Any] = {"rationale": rationale}
        practice_mode = suggestion.get("practice_mode")
        if practice_mode:
            entry["practice_mode"] = str(practice_mode)
        targets = suggestion.get("target_evidence_families")
        if isinstance(targets, list):
            entry["target_evidence_families"] = [str(facet) for facet in targets]
        rationales.append(entry)
    return rationales


def _diagnostic_source_refs(plan: DiagnosticPracticePlan) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(ref_type: str, ref_id: str | None) -> None:
        if not ref_id:
            return
        key = (ref_type, ref_id)
        if key in seen:
            return
        seen.add(key)
        refs.append({"ref_type": ref_type, "ref_id": ref_id})

    for target in plan.targets:
        add("manual_context", target.need_id)
        add("existing_entity", target.learning_object_id)
        add("existing_entity", target.source_practice_item_id)
    return refs


def _ability_estimate(facet_means: dict[str, float], mastery_mean: float | None) -> float:
    """Best available ability estimate (probability scale) for difficulty targeting.

    Prefers the mean of the target facets' recall means — the latent the probe is
    about — and falls back to scalar LO mastery, then to an uninformative 0.5.
    """

    values = list(facet_means.values())
    if values:
        return sum(values) / len(values)
    return mastery_mean if mastery_mean is not None else 0.5


def _ability_logit(ability: float | None) -> float:
    return _logit(ability if ability is not None else 0.5)


def _logit(probability: float) -> float:
    p = min(max(probability, 1e-6), 1.0 - 1e-6)
    return log(p / (1.0 - p))


def _difficulty_for_success(
    ability_logit: float,
    target_success: float,
    *,
    discrimination: float,
    difficulty_scale: float,
) -> float:
    """Authored difficulty in [0,1] whose IRT ``b`` yields ``target_success`` at ``ability_logit``.

    Inverts the mastery channel's 2PL link (``services/mastery.py``):
    ``p = sigmoid(a·(theta − b))`` with ``b = scale·(2·difficulty − 1)``, so a
    higher target success maps to an easier (lower-difficulty) item.
    """

    b = ability_logit - _logit(target_success) / max(discrimination, 1e-6)
    difficulty = b / (2.0 * difficulty_scale) + 0.5
    return round(min(max(difficulty, 0.0), 1.0), 2)


def _success_band_difficulty(
    ability_logit: float,
    success_band: tuple[float, float],
    *,
    discrimination: float,
    difficulty_scale: float,
    difficulty_floor: float = 0.0,
    min_band_width: float = 0.0,
) -> tuple[float, float]:
    """``(easier, harder)`` authored-difficulty band spanning a target success interval.

    The *higher* success bound yields the *lower* (easier) difficulty edge, so the
    band is returned low-to-high in difficulty.

    ``difficulty_floor`` / ``min_band_width`` keep the band from collapsing onto
    0.0 at a low ability estimate. Without them the band degenerates to
    ``[0.0, 0.0]`` — "author the easiest item expressible" — whose outcome the
    model already predicts, so it yields no information and cannot correct the
    pessimistic estimate that produced it.
    """

    success_low, success_high = min(success_band), max(success_band)
    low = _difficulty_for_success(
        ability_logit, success_high, discrimination=discrimination, difficulty_scale=difficulty_scale
    )
    high = _difficulty_for_success(
        ability_logit, success_low, discrimination=discrimination, difficulty_scale=difficulty_scale
    )
    low = max(low, difficulty_floor)
    high = max(high, low + min_band_width)
    return (round(min(low, 1.0), 2), round(min(high, 1.0), 2))


def _guard_degenerate_band(
    band: tuple[float, float], *, min_band_width: float
) -> tuple[float, float]:
    """Restore width to a band that clamped to ``[x, x]``; never re-centre it.

    The probe band deliberately carries no ``difficulty_floor`` — it sits on the
    learner's boundary, where outcome variance (and so diagnostic information)
    is already maximal, and raising it would blunt the probe. The one shape
    that must not survive is zero width at a clamp edge: ``[0.0, 0.0]`` under a
    pessimistic ability estimate (or ``[1.0, 1.0]`` under an optimistic one)
    names an item whose outcome the model already predicts, so it yields no
    information and can never correct the estimate that produced it. Width is
    restored away from the clamp edge only; the boundary-centred edge stays
    where the estimate put it.
    """

    low, high = band
    if high - low > 1e-9 or min_band_width <= 0.0:
        return band
    if high + min_band_width <= 1.0:
        return (low, round(high + min_band_width, 2))
    return (round(max(0.0, low - min_band_width), 2), high)
