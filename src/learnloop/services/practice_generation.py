from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from learnloop.ai.client import AIProviderClient
from learnloop.db.repositories import Repository
from learnloop.services.mastery import display_mastery
from learnloop.services.proposals import generate_authoring_proposal
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

    def as_dict(self) -> dict[str, Any]:
        return {"patch_id": self.patch_id, "plan": self.plan.as_dict()}


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
) -> PracticeExpansionPlan:
    if target_items_per_lo <= 0:
        raise PracticeExpansionError("target_items_per_lo must be positive")
    if max_new_per_lo <= 0:
        raise PracticeExpansionError("max_new_per_lo must be positive")
    subject_filter = set(subjects or [])
    item_counts = _active_practice_item_counts(vault, repository)
    targets: list[PracticeExpansionTarget] = []
    for learning_object in sorted(vault.learning_objects.values(), key=lambda lo: lo.id):
        if learning_object.status != "active":
            continue
        if subject_filter and not (subject_filter & set(learning_object.subjects)):
            continue
        probe_state = repository.probe_state(learning_object.id)
        if probe_state is None or probe_state.status != "complete":
            continue
        existing_count = item_counts.get(learning_object.id, 0)
        needed = target_items_per_lo - existing_count
        if needed <= 0:
            continue
        mastery = repository.mastery_state(learning_object.id)
        mastery_mean = display_mastery(mastery).mastery_mean if mastery is not None else None
        targets.append(
            PracticeExpansionTarget(
                learning_object_id=learning_object.id,
                title=learning_object.title,
                subjects=list(learning_object.subjects),
                concept=learning_object.concept,
                existing_practice_items=existing_count,
                requested_new_items=min(needed, max_new_per_lo),
                probe_attempts_completed=probe_state.probe_attempts_completed,
                probe_attempts_target=probe_state.probe_attempts_target,
                mastery_mean=mastery_mean,
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
) -> DiagnosticPracticePlan:
    if max_needs <= 0:
        raise PracticeExpansionError("max_needs must be positive")
    targets: list[DiagnosticPracticeTarget] = []
    for need in repository.pending_intervention_needs(learning_object_id):
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
            for state in repository.facet_recall_states(learning_object.id)
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
                mastery_mean=mastery_mean,
                facet_recall_mean_by_facet=facet_means,
                facet_recall_variance_by_facet=facet_variances,
                recommended_difficulty_band=_difficulty_band(facet_means, mastery_mean),
            )
        )
        if len(targets) >= max_needs:
            break
    return DiagnosticPracticePlan(targets=targets)


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
    patch_id = generate_authoring_proposal(
        root,
        codex_client,
        subjects=sorted({subject for target in plan.targets for subject in target.subjects}),
        instructions=_diagnostic_practice_instructions(plan, extra_instructions=extra_instructions),
        codex_revision=codex_revision,
    )
    fulfilled: list[str] = []
    for target in plan.targets:
        if repository.update_intervention_need_status(
            target.need_id,
            status="fulfilled",
            blocked_reason=f"diagnostic_proposal_queued:{patch_id}",
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
    extra_instructions: str | None = None,
    codex_revision: str | None = None,
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
    )
    if not plan.targets:
        raise PracticeExpansionError("No completed probe Learning Objects need more Practice Items.")
    patch_id = generate_authoring_proposal(
        root,
        codex_client,
        subjects=_target_subjects(plan, subjects),
        instructions=_practice_expansion_instructions(plan, extra_instructions=extra_instructions),
        codex_revision=codex_revision,
    )
    return PracticeExpansionResult(patch_id=patch_id, plan=plan)


def _active_practice_item_counts(vault: LoadedVault, repository: Repository) -> dict[str, int]:
    states = repository.practice_item_states()
    counts: dict[str, int] = {}
    for item in vault.practice_items.values():
        state = states.get(item.id)
        if state is not None and not state.active:
            continue
        counts[item.learning_object_id] = counts.get(item.learning_object_id, 0) + 1
    return counts


def _target_subjects(plan: PracticeExpansionPlan, subjects: list[str] | None) -> list[str]:
    if subjects:
        return subjects
    return sorted({subject for target in plan.targets for subject in target.subjects})


def _practice_expansion_instructions(
    plan: PracticeExpansionPlan,
    *,
    extra_instructions: str | None,
) -> str:
    lines = [
        "Generate additional LearnLoop Practice Items after completed probe phases.",
        "Create only practice_item proposal items; do not create new Learning Objects, concepts, or concept edges.",
        "Each new Practice Item must attach to one of the target learning_object_id values below.",
        "Prefer constructed_response items with attempt_types_allowed ['open_text'] unless the Learning Object clearly calls for another existing supported attempt type.",
        "Use review_route='review_required' unless a direct note or canonical source reference in the supplied context supports auto_apply.",
        "Avoid duplicating existing prompts in context; vary facets, difficulty, and expected answer shape.",
        "For each target, create exactly requested_new_items Practice Items.",
        f"Targets: {[target.as_dict() for target in plan.targets]}",
    ]
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
        "Calibrate difficulty to the recommended_difficulty_band; use the lower half for recall_failure or low facet recall, and the upper half when facet recall is already high.",
        "Use evidence_facets exactly equal to target_facets, evidence_weights normalized across target_facets, and repair_targets equal to target_facets.",
        "The grading_rubric must include at least one criterion per target facet and criterion_facet_weights must map each criterion to its facet.",
        "Set retrieval_demand high (0.75-0.95), transfer_distance low-to-moderate (0.05-0.35), scaffold_level no higher than 0.35, and difficulty_source='llm_estimate'.",
        "Use review_route='review_required'; generated diagnostic probes must be reviewed before writing vault content.",
        f"Targets: {[target.as_dict() for target in plan.targets]}",
    ]
    if extra_instructions:
        lines.append(f"Additional instructions: {extra_instructions}")
    return "\n".join(lines)


def _difficulty_band(facet_means: dict[str, float], mastery_mean: float | None) -> tuple[float, float]:
    values = list(facet_means.values())
    ability = sum(values) / len(values) if values else (mastery_mean if mastery_mean is not None else 0.5)
    if ability < 0.45:
        return (0.25, 0.45)
    if ability > 0.65:
        return (0.60, 0.80)
    return (0.45, 0.65)
