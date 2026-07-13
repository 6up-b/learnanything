"""Checkpoint-3 sim validation: planted latent hypothesis types end to end.

Extends the sim harness with planted students whose latent state IS one of the
episode hypothesis templates — ``surface_only``, ``confuses_with:<neighbor>``,
``schema_without_transfer``, ``unfamiliar``, ``robust_initial_grasp`` — and
drives the REAL episode policy against them: entry through state sync,
parameterized instance generation (§10), predictive-EIG selection (§7.4),
committed presentations, the live attempt pipeline, contamination rules, and
the §11 completion policy. Instrument gates alone cannot validate the policy;
this measures whether the *episode* recovers the planted state within its
observation budget and selects the matching instructional action
(spec_probe_eig_redesign.md Checkpoint 3.9 / Checkpoint 4 entry gate).

The planted responder is behavioral, not sampled from the card conditionals:
each planted type reacts to what an instrument actually elicits (a shifted
surface breaks a surface-bound learner; a counterexample request breaks a
schema-without-transfer learner), so a policy that probes the wrong capability
fails the validation even though every family passed its own gate.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.services.grading import resolved_rubric
from learnloop.services.probe_episodes import (
    commit_presentation,
    eligible_instruments,
    episode_posterior,
    serve_presentation,
)
from learnloop.services.probe_families import (
    DEFAULT_INSTRUCTIONAL_ACTIONS,
    CompiledInstrument,
    builtin_family_templates,
)
from learnloop.services.probe_hypotheses import CONFUSES_PREFIX
from learnloop.services.probe_instance_generation import generate_instances_for_episode
from learnloop.services.state_sync import sync_vault_state
from learnloop.sim.runner import apply_config_overrides, prepare_run_vault
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

VALIDATION_START = datetime(2026, 2, 2, 9, 0, 0, tzinfo=UTC)

PLANTED_TYPES = (
    "robust_initial_grasp",
    "unfamiliar",
    "surface_only",
    "schema_without_transfer",
    "confuses_with",
)

_CORRECT_OUTCOMES = frozenset(
    {
        "correct_target_reason",
        "correct_recall",
        "correct_prediction_reason",
        "correct_on_shifted",
        "valid_counterexample",
        "correct_commit_reason",
        "correct",
        "high",
    }
)
_WEAK_OUTCOMES = frozenset(
    {
        "correct_weak_reason",
        "partial_recall",
        "correct_prediction_weak_reason",
        "partial_boundary",
        "correct_commit_weak_reason",
        "partial",
        "mid",
    }
)


@dataclass(frozen=True)
class PlantedResponse:
    attempt_type: str  # diagnostic_probe | dont_know
    score: int
    fired_error_types: tuple[str, ...] = ()


def _effective_slot(planted: str, instrument: CompiledInstrument) -> str:
    slots = set(instrument.rows)
    if planted in slots:
        return planted
    alias = instrument.slot_aliases.get(planted)
    if alias is not None and alias in slots:
        return alias
    if planted == "confuses_with" or planted.startswith(CONFUSES_PREFIX):
        if "confuses_with_neighbor" in slots:
            return "confuses_with_neighbor"
        neighbor_alias = instrument.slot_aliases.get("confuses_with_neighbor")
        if neighbor_alias is not None and neighbor_alias in slots:
            return neighbor_alias
    if "other_or_unknown" in slots:
        return "other_or_unknown"
    return sorted(slots)[0]


def planted_response(
    planted: str,
    instrument: CompiledInstrument,
    rng: random.Random,
) -> PlantedResponse:
    """Behavioral response of one planted student to one instrument.

    The student behaves according to what the instrument's measurement pattern
    elicits from its latent state (via the family's slot semantics, including
    the declared cannot-separate aliases): a shifted surface breaks a
    surface-bound learner, a contrast fires the confusable signature, a
    non-eliciting instrument sees capable performance. Responses are noisy
    around the modal class, and are emitted as (attempt type, score, fired
    error types) — the real signature matcher, grader channel, and posterior
    replay then interpret them, so this validates the episode policy without
    feeding it its own conditionals.
    """

    slot = _effective_slot(planted, instrument)
    row = instrument.rows.get(slot, {})
    modal_outcome = max(
        (outcome for outcome in row if outcome != "hedge"),
        key=lambda outcome: row[outcome],
        default="",
    )

    def draw(distribution: list[tuple[float, str]]) -> str:
        roll = rng.random()
        cumulative = 0.0
        for probability, outcome in distribution:
            cumulative += probability
            if roll < cumulative:
                return outcome
        return distribution[-1][1]

    if modal_outcome in _CORRECT_OUTCOMES:
        choice = draw([(0.90, "correct"), (0.08, "weak"), (0.02, "low")])
    elif modal_outcome in _WEAK_OUTCOMES:
        choice = draw([(0.65, "weak"), (0.20, "correct"), (0.15, "low")])
    elif modal_outcome == "unanswered":
        choice = draw([(0.75, "dont_know"), (0.15, "low"), (0.10, "weak")])
    elif modal_outcome in instrument.signature_error_types:
        choice = draw([(0.80, "signature"), (0.12, "weak"), (0.08, "correct")])
    else:
        choice = draw([(0.70, "low"), (0.20, "weak"), (0.10, "correct")])

    if choice == "dont_know":
        return PlantedResponse(attempt_type="dont_know", score=0)
    if choice == "correct":
        return PlantedResponse(attempt_type="diagnostic_probe", score=4)
    if choice == "weak":
        return PlantedResponse(attempt_type="diagnostic_probe", score=2)
    if choice == "signature":
        fired = instrument.signature_error_types.get(modal_outcome, (modal_outcome,))
        return PlantedResponse(
            attempt_type="diagnostic_probe", score=1, fired_error_types=tuple(fired)
        )
    return PlantedResponse(attempt_type="diagnostic_probe", score=1)


@dataclass(frozen=True)
class EpisodeValidationResult:
    planted: str
    seed: int
    learning_object_id: str
    episode_id: str
    completed: bool
    completion_reason: str | None
    observations_used: int
    diagnosed_label: str | None
    diagnosed_probability: float
    label_matched: bool
    expected_action: str | None
    diagnosed_action: str | None
    action_matched: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "planted": self.planted,
            "seed": self.seed,
            "learning_object_id": self.learning_object_id,
            "episode_id": "<id>",
            "completed": self.completed,
            "completion_reason": self.completion_reason,
            "observations_used": self.observations_used,
            "diagnosed_label": self.diagnosed_label,
            "diagnosed_probability": round(self.diagnosed_probability, 4),
            "label_matched": self.label_matched,
            "expected_action": self.expected_action,
            "diagnosed_action": self.diagnosed_action,
            "action_matched": self.action_matched,
        }


@dataclass
class ValidationReport:
    results: list[EpisodeValidationResult] = field(default_factory=list)

    def by_planted(self) -> dict[str, dict[str, Any]]:
        grouped: dict[str, list[EpisodeValidationResult]] = {}
        for result in self.results:
            grouped.setdefault(result.planted, []).append(result)
        summary: dict[str, dict[str, Any]] = {}
        for planted, entries in sorted(grouped.items()):
            runs = len(entries)
            summary[planted] = {
                "runs": runs,
                "completed": sum(1 for entry in entries if entry.completed),
                "label_accuracy": sum(1 for entry in entries if entry.label_matched) / runs,
                "action_accuracy": sum(1 for entry in entries if entry.action_matched) / runs,
                "mean_observations": sum(entry.observations_used for entry in entries) / runs,
            }
        return summary

    def as_dict(self) -> dict[str, Any]:
        results = [result.as_dict() for result in self.results]
        by_planted = self.by_planted()
        total = len(self.results) or 1
        return {
            "version": 1,
            "overall_label_accuracy": sum(1 for r in self.results if r.label_matched) / total,
            "overall_action_accuracy": sum(1 for r in self.results if r.action_matched) / total,
            "by_planted": by_planted,
            "results": results,
        }

    def passes(self, *, label_accuracy_threshold: float, action_accuracy_threshold: float) -> bool:
        """Checkpoint 4 entry gate: every planted type classified at or above
        threshold within the budget, with matching instructional actions."""

        summary = self.by_planted()
        return all(
            entry["label_accuracy"] >= label_accuracy_threshold
            and entry["action_accuracy"] >= action_accuracy_threshold
            for entry in summary.values()
        )


def _expected_label(planted: str, diagnosed: str | None) -> bool:
    if diagnosed is None:
        return False
    if planted == "confuses_with":
        return diagnosed.startswith(CONFUSES_PREFIX)
    return diagnosed == planted


def _action_for_label(label: str | None) -> str | None:
    if label is None:
        return None
    if label.startswith(CONFUSES_PREFIX):
        return DEFAULT_INSTRUCTIONAL_ACTIONS["confuses_with_neighbor"]
    if label.startswith("misconception:"):
        return DEFAULT_INSTRUCTIONAL_ACTIONS["holds_misconception"]
    return DEFAULT_INSTRUCTIONAL_ACTIONS.get(label)


def run_probe_validation(
    source_vault: Path,
    workdir: Path,
    *,
    planted_types: tuple[str, ...] = PLANTED_TYPES,
    seeds: tuple[int, ...] = (11, 12, 13),
    learning_object_id: str | None = None,
    claim_level: float = 0.7,
    config_overrides: Mapping[str, Any] | None = None,
) -> ValidationReport:
    """Run the planted-type episode validation against copies of one vault.

    Each (planted, seed) pair gets a fresh vault copy with reset derived state,
    a covering learner claim (so surface/transfer hypotheses are instantiable
    at cold start, §6.2), trusted builtin families, and generated instrument
    instances; the run then drives the real selection → presentation → attempt
    → observation → completion loop.
    """

    report = ValidationReport()
    for planted in planted_types:
        for seed in seeds:
            run_root = workdir / f"run_{planted.replace(':', '_')}_{seed}"
            prepare_run_vault(source_vault, run_root, reset_state=True)
            result = _run_one_episode(
                run_root,
                planted=planted,
                seed=seed,
                learning_object_id=learning_object_id,
                claim_level=claim_level,
                config_overrides=config_overrides,
            )
            if result is not None:
                report.results.append(result)
    return report


def _run_one_episode(
    vault_root: Path,
    *,
    planted: str,
    seed: int,
    learning_object_id: str | None,
    claim_level: float,
    config_overrides: Mapping[str, Any] | None,
) -> EpisodeValidationResult | None:
    vault = load_vault(vault_root)
    overrides = dict(config_overrides or {})
    # The full template set must be instantiable for the classification to be
    # meaningful; keep every plausible candidate in the locked set.
    overrides.setdefault("probe.hypothesis_set_max_size", 7)
    vault.config = apply_config_overrides(vault.config, overrides)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    clock = FrozenClock(VALIDATION_START)
    rng = random.Random(seed)

    # Cold-start context (§6.2): a covering claim makes surface-only and
    # schema-without-transfer hypotheses plausible before any evidence.
    repository.insert_learner_claim(
        {
            "id": f"claim_validation_{seed}",
            "claim_type": "self_rating",
            "scope_type": "global",
            "scope_id": None,
            "evidence_family": None,
            "claimed_level": claim_level,
            "prior_pseudo_count": 4.0,
            "source": "manual_cli",
        },
        clock=clock,
    )
    # Trusted families: generated instances auto-admit provisionally (§10) so
    # the episode can actually serve instruments.
    for template in builtin_family_templates():
        repository.upsert_probe_family_template(
            family_id=template.id,
            version=template.version,
            status="trusted",
            template=template.as_dict(),
            schema_hash=template.schema_hash(),
            clock=clock,
        )
    sync_vault_state(vault, repository, clock=clock)

    target_lo = learning_object_id
    if target_lo is None:
        open_episodes = repository.open_probe_episodes()
        if not open_episodes:
            return None
        target_lo = sorted(open_episodes)[0]
    episode = repository.open_probe_episode(target_lo)
    if episode is None:
        return None
    if episode.status == "pending_items":
        generate_instances_for_episode(repository, vault, episode.id, clock=clock, seed=seed)
        vault = load_vault(vault_root)
        vault.config = apply_config_overrides(vault.config, overrides)
        episode = repository.probe_episode(episode.id)
        if episode is None:
            return None

    steps = 0
    max_steps = episode.maximum_observations + 2
    now = VALIDATION_START
    while steps < max_steps:
        episode = repository.probe_episode(episode.id)
        if episode is None or episode.status != "in_progress":
            break
        entries = eligible_instruments(vault, repository, episode)
        if not entries:
            break
        top = entries[0]
        step_clock = FrozenClock(now)
        # candidates= logs §13.3 shadow-policy rankings so the pilot audit has
        # policy-comparison data.
        presentation = commit_presentation(
            vault, repository, episode, top, candidates=entries, clock=step_clock
        )
        serve_presentation(repository, presentation.id, clock=step_clock)
        response = planted_response(planted, top.instrument, rng)
        _submit_response(vault, repository, top.item.id, presentation.id, response, clock=step_clock)
        steps += 1
        now = now + timedelta(seconds=90)

    final = repository.probe_episode(episode.id)
    posterior = episode_posterior(vault, repository, final) if final is not None else None
    diagnosed_label, diagnosed_probability = (posterior.top if posterior is not None else (None, 0.0))
    observations = posterior.qualifying_observations if posterior is not None else 0
    expected_action = _action_for_label(
        planted if planted != "confuses_with" else f"{CONFUSES_PREFIX}x"
    )
    diagnosed_action = _action_for_label(diagnosed_label)
    completed = final is not None and final.status == "complete"
    return EpisodeValidationResult(
        planted=planted,
        seed=seed,
        learning_object_id=target_lo,
        episode_id=final.id if final is not None else "",
        completed=completed,
        completion_reason=final.completion_reason if final is not None else None,
        observations_used=observations,
        diagnosed_label=diagnosed_label or None,
        diagnosed_probability=diagnosed_probability,
        label_matched=_expected_label(planted, diagnosed_label),
        expected_action=expected_action,
        diagnosed_action=diagnosed_action,
        action_matched=expected_action is not None and expected_action == diagnosed_action,
    )


def _submit_response(
    vault,
    repository: Repository,
    practice_item_id: str,
    presentation_id: str,
    response: PlantedResponse,
    *,
    clock: FrozenClock,
) -> None:
    item = vault.practice_items[practice_item_id]
    rubric = resolved_rubric(vault, item)
    fraction = {4: 1.0, 3: 0.75, 2: 0.5, 1: 0.25, 0: 0.0}[max(0, min(response.score, 4))]
    criterion_points = {
        criterion.id: round(float(criterion.points) * fraction, 2) for criterion in rubric.criteria
    }
    attributions = [
        GradeAttribution(
            error_type=error_type,
            severity=0.8,
            is_misconception=True,
            evidence="Systematic signature produced by the planted latent state.",
        )
        for error_type in response.fired_error_types
    ]
    grade = ResolvedGrade(
        rubric_score=response.score,
        criterion_points=criterion_points,
        evidence_rows=[],
        error_attributions=attributions,
        grader_confidence=0.95,
        confidence=4,
        manual_review_reason=None,
    )
    apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=practice_item_id,
                learner_answer_md=f"[planted response score={response.score}]",
                attempt_type=response.attempt_type,
                hints_used=0,
                probe_presentation_id=presentation_id,
            ),
            attempt_id=new_ulid(),
            grade=grade,
            grading_source="ai",
        ),
        clock=clock,
    )
