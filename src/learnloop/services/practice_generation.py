from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from math import log
from pathlib import Path
from typing import Any

from learnloop.ai.client import AIProviderClient
from learnloop.clock import Clock, SystemClock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.services.followups import (
    current_same_facet_failure_streak,
    current_same_item_failure_streak,
)
from learnloop.services.facet_state_reader import facet_recall_states_for_lo
from learnloop.services.mastery import display_mastery
from learnloop.services.proposals import generate_authoring_proposal
from learnloop.services.teach_back import TEACH_BACK_PRACTICE_MODE
from learnloop.services.state_sync import sync_vault_state
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

    def as_dict(self) -> dict[str, Any]:
        return {
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
        }


@dataclass(frozen=True)
class PracticeExpansionPlan:
    targets: list[PracticeExpansionTarget]

    @property
    def requested_new_items(self) -> int:
        return sum(target.requested_new_items for target in self.targets)

    def as_dict(self) -> dict[str, Any]:
        return {
            "targets": [target.as_dict() for target in self.targets],
            "requested_new_items": self.requested_new_items,
        }


@dataclass(frozen=True)
class PracticeExpansionResult:
    patch_id: str
    plan: PracticeExpansionPlan
    # --mode-mix compliance of the persisted proposal. Violations are hard
    # (requested teach_back count not honored for a targeted LO); warnings are
    # soft mismatches on other practice modes.
    mode_mix_violations: list[str] = field(default_factory=list)
    mode_mix_warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "plan": self.plan.as_dict(),
            "mode_mix_violations": list(self.mode_mix_violations),
            "mode_mix_warnings": list(self.mode_mix_warnings),
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

    def as_dict(self) -> dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "plan": self.plan.as_dict(),
            "fulfilled_need_ids": self.fulfilled_need_ids,
        }


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
    _validate_named_learning_objects(
        vault, repository, named_lo_ids, require_completed_probe=require_completed_probe
    )
    subject_filter = set(subjects or [])
    concept_filter = set(focus_concepts or [])
    item_counts = _active_practice_item_counts(vault, repository, exclude_item_ids=exclude_item_ids)
    facet_unions = _active_evidence_facet_unions(vault, repository)
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
        probe_state = repository.probe_state(learning_object.id)
        if require_completed_probe and (probe_state is None or probe_state.status != "complete"):
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
                    _ability_logit(mastery_mean),
                    vault.config.practice_generation.practice_success_band,
                    discrimination=irt.discrimination_default,
                    difficulty_scale=irt.difficulty_prior_scale,
                ),
                existing_evidence_facets=facet_unions.get(learning_object.id, []),
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
                recommended_difficulty_band=_success_band_difficulty(
                    _ability_logit(_ability_estimate(facet_means, mastery_mean)),
                    vault.config.practice_generation.probe_success_band,
                    discrimination=irt.discrimination_default,
                    difficulty_scale=irt.difficulty_prior_scale,
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
    patch_id = generate_authoring_proposal(
        root,
        codex_client,
        subjects=sorted({subject for target in plan.targets for subject in target.subjects}),
        source_refs=source_refs,
        instructions=_diagnostic_practice_instructions(plan, extra_instructions=extra_instructions),
        codex_revision=codex_revision,
        merge_context_source_refs=True,
    )
    fulfilled: list[str] = []
    diagnostic_item_ids_by_need = _diagnostic_item_ids_by_need(plan, repository.proposal_items(patch_id))
    for target in plan.targets:
        blocked_reason = f"diagnostic_proposal_queued:{patch_id}"
        item_id = diagnostic_item_ids_by_need.get(target.need_id)
        if item_id:
            blocked_reason = f"{blocked_reason}:{item_id}"
        if repository.update_intervention_need_status(
            target.need_id,
            status="fulfilled",
            blocked_reason=blocked_reason,
        ):
            fulfilled.append(target.need_id)
    return DiagnosticPracticeResult(patch_id=patch_id, plan=plan, fulfilled_need_ids=fulfilled)


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
    )
    if not plan.targets:
        raise PracticeExpansionError("No completed probe Learning Objects need more Practice Items.")
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
        codex_revision=codex_revision,
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
    )
    return PracticeExpansionResult(patch_id=patch_id, plan=plan)


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
) -> None:
    """Named --los targets must exist, be active, and have a completed probe.

    Naming an LO bypasses only the item-count deficit gate; the completed-probe
    gate stays (evidence-not-mastery: generation targets follow probe evidence)
    unless the caller explicitly waives it (goal population, where the goal
    itself is the learner's declared intent to practice these LOs).
    """

    for lo_id in learning_object_ids:
        learning_object = vault.learning_objects.get(lo_id)
        if learning_object is None:
            raise PracticeExpansionError(f"Unknown learning object id: {lo_id}")
        if learning_object.status != "active":
            raise PracticeExpansionError(f"Learning object {lo_id} is not active (status={learning_object.status}).")
        if not require_completed_probe:
            continue
        probe_state = repository.probe_state(lo_id)
        if probe_state is None or probe_state.status != "complete":
            raise PracticeExpansionError(
                f"Learning object {lo_id} has no completed probe phase; finish its probes before generating practice."
            )


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


def _active_evidence_facet_unions(vault: LoadedVault, repository: Repository) -> dict[str, list[str]]:
    """Union of evidence facet ids across each Learning Object's active items."""
    states = repository.practice_item_states()
    unions: dict[str, set[str]] = {}
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
    "criterion_facet_weights MUST map every rubric criterion (core and transfer) to its facet(s), "
    "evidence_facets/evidence_weights must be set, and criterion points must sum to max_points (4 or less)."
)


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
        "For each target, create exactly requested_new_items Practice Items.",
        f"Targets: {[target.as_dict() for target in plan.targets]}",
    ]
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
        "The grading_rubric must include at least one criterion per target facet and criterion_facet_weights must map each criterion to its facet.",
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
) -> tuple[float, float]:
    """``(easier, harder)`` authored-difficulty band spanning a target success interval.

    The *higher* success bound yields the *lower* (easier) difficulty edge, so the
    band is returned low-to-high in difficulty.
    """

    success_low, success_high = min(success_band), max(success_band)
    low = _difficulty_for_success(
        ability_logit, success_high, discrimination=discrimination, difficulty_scale=difficulty_scale
    )
    high = _difficulty_for_success(
        ability_logit, success_low, discrimination=discrimination, difficulty_scale=difficulty_scale
    )
    return (low, high)
