"""P1 step 5 -- purpose-specific administration adapters (spec_p1_shared_substrate
§3.10, standing rule 4, invariants 8/9).

Standing rule 4: **there is no universal "incorrect answer" pipeline.** The
administration's immutable family PURPOSE (never ``attempt_type`` or UI route)
selects the adapter, and each adapter defines its own scheduling / evidence /
familiarity / lifecycle semantics per the §3.10 matrix:

| purpose       | scheduling                         | evidence                              | familiarity   | lifecycle                    |
|---------------|------------------------------------|---------------------------------------|---------------|------------------------------|
| diagnostic    | no practice schedule update        | only frozen-episode / declared facet  | full exposure | consumed forever             |
| instructional | progression-path/exposure; no lapse| no unassisted certification           | full exposure | reusable per policy          |
| practice      | card-level review when eligible    | context/familiarity/reliability weight| full exposure | reusable; rotate lazily      |
| assessment    | no practice FSRS                   | terminal distribution/certification   | full exposure | P0 assessment burn rules     |

FSRS remains **predictive scheduling only**; only the practice adapter, and only
on an eligible observation, applies it.

**The attempt hot path.** ``attempts.apply_attempt`` applies its FSRS review
through the practice adapter's eligibility (:func:`hot_path_applies_practice_review`):
an eligible practice observation is reviewed as before, an ineligible one leaves
the card's scheduling state as it was (§3.8).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.substrate import card_lineage as _lineage
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS

PURPOSES: tuple[str, ...] = ("diagnostic", "instructional", "practice", "assessment")

class PurposeMismatch(Exception):
    """An administration was routed to the wrong adapter (§7.5 purpose mismatch)."""


class OpportunisticDiagnosisRejected(Exception):
    """Invariant 8: only an administration committed to a diagnostic episode and its
    frozen hypothesis set may update that episode. A cold practice/other response
    can never update an open probe episode opportunistically."""


@dataclass(frozen=True)
class AdministrationEffects:
    """The three intentionally-different projections + lifecycle for one purpose
    (§1, §3.10). Two projections may disagree by design."""

    purpose: str
    updates_practice_schedule: bool
    applies_fsrs_review: bool
    evidence_class: str
    mints_unassisted_certification: bool
    records_full_exposure: bool
    opens_lapse_on_failure: bool
    lifecycle_after_render: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "purpose": self.purpose,
            "updates_practice_schedule": self.updates_practice_schedule,
            "applies_fsrs_review": self.applies_fsrs_review,
            "evidence_class": self.evidence_class,
            "mints_unassisted_certification": self.mints_unassisted_certification,
            "records_full_exposure": self.records_full_exposure,
            "opens_lapse_on_failure": self.opens_lapse_on_failure,
            "lifecycle_after_render": self.lifecycle_after_render,
        }


class Adapter:
    purpose: str = ""

    def effects(self, *, eligible: bool, failed: bool) -> AdministrationEffects:  # pragma: no cover
        raise NotImplementedError

    def apply_scheduling(
        self,
        repository: Repository,
        *,
        card_lineage_id: str,
        scheduler_algorithm_version: str,
        review_event: Mapping[str, Any] | None,
        eligible: bool,
        prior_reviews: Sequence[Mapping[str, Any]] = (),
        model_label: str = "fsrs",
        weights: tuple[float, ...] = FSRS6_DEFAULT_WEIGHTS,
        clock: Clock | None = None,
    ) -> dict[str, Any] | None:
        """Default: no scheduling projection. The practice adapter overrides."""

        return None


class DiagnosticAdapter(Adapter):
    purpose = "diagnostic"

    def effects(self, *, eligible: bool, failed: bool) -> AdministrationEffects:
        return AdministrationEffects(
            purpose="diagnostic",
            updates_practice_schedule=False,
            applies_fsrs_review=False,
            evidence_class="frozen_episode_only",
            mints_unassisted_certification=False,
            records_full_exposure=True,
            opens_lapse_on_failure=False,
            lifecycle_after_render="consumed_forever_for_diagnosis",
        )

    def update_episode(self, *, committed_episode_id: str | None) -> str:
        """Invariant 8 / §9.4: an episode update requires a committed diagnostic
        presentation. No opportunistic diagnosis."""

        if not committed_episode_id:
            raise OpportunisticDiagnosisRejected(
                "diagnostic evidence requires a committed episode presentation"
            )
        return committed_episode_id


class InstructionalAdapter(Adapter):
    purpose = "instructional"

    def effects(self, *, eligible: bool, failed: bool) -> AdministrationEffects:
        # Progression-path / exposure only; never a practice lapse; instruction is
        # not proof -> no unassisted certification (invariant 9).
        return AdministrationEffects(
            purpose="instructional",
            updates_practice_schedule=False,
            applies_fsrs_review=False,
            evidence_class="no_unassisted_certification",
            mints_unassisted_certification=False,
            records_full_exposure=True,
            opens_lapse_on_failure=False,
            lifecycle_after_render="reusable_per_policy",
        )


class PracticeAdapter(Adapter):
    purpose = "practice"

    def effects(self, *, eligible: bool, failed: bool) -> AdministrationEffects:
        return AdministrationEffects(
            purpose="practice",
            updates_practice_schedule=eligible,
            applies_fsrs_review=eligible,
            evidence_class="practice_weighted" if eligible else "ineligible",
            mints_unassisted_certification=False,
            records_full_exposure=True,
            opens_lapse_on_failure=bool(eligible and failed),
            lifecycle_after_render="reusable_rotate_lazily",
        )

    def apply_scheduling(
        self,
        repository: Repository,
        *,
        card_lineage_id: str,
        scheduler_algorithm_version: str,
        review_event: Mapping[str, Any] | None,
        eligible: bool,
        prior_reviews: Sequence[Mapping[str, Any]] = (),
        model_label: str = "fsrs",
        weights: tuple[float, ...] = FSRS6_DEFAULT_WEIGHTS,
        clock: Clock | None = None,
    ) -> dict[str, Any] | None:
        """Card-level review, ONLY when the observation is eligible (§3.8, §3.10).
        Quarantined / out-of-band observations leave card state unchanged."""

        if not eligible or review_event is None:
            return None
        reviews = [*prior_reviews, dict(review_event)]
        return _lineage.rebuild_card_state(
            repository,
            card_lineage_id=card_lineage_id,
            scheduler_algorithm_version=scheduler_algorithm_version,
            review_events=reviews,
            model_label=model_label,
            weights=weights,
            clock=clock,
        )


class AssessmentAdapter(Adapter):
    purpose = "assessment"

    def effects(self, *, eligible: bool, failed: bool) -> AdministrationEffects:
        return AdministrationEffects(
            purpose="assessment",
            updates_practice_schedule=False,
            applies_fsrs_review=False,
            evidence_class="terminal_certification_only",
            mints_unassisted_certification=True,
            records_full_exposure=True,
            opens_lapse_on_failure=False,
            lifecycle_after_render="p0_assessment_burn",
        )


_ADAPTERS: dict[str, Adapter] = {
    "diagnostic": DiagnosticAdapter(),
    "instructional": InstructionalAdapter(),
    "practice": PracticeAdapter(),
    "assessment": AssessmentAdapter(),
}


def resolve_adapter(purpose: str) -> Adapter:
    """Select the adapter by immutable family purpose (never attempt_type/route)."""

    adapter = _ADAPTERS.get(purpose)
    if adapter is None:
        raise PurposeMismatch(f"no administration adapter for purpose: {purpose!r}")
    return adapter


def resolve_adapter_for_administration(
    repository: Repository, administration_id: str
) -> Adapter:
    row = repository.activity_administration(administration_id)
    if row is None:
        raise PurposeMismatch(f"no administration: {administration_id!r}")
    return resolve_adapter(row["purpose"])


@dataclass(frozen=True)
class ProjectionResult:
    effects: AdministrationEffects
    card_state: dict[str, Any] | None
    deferred: bool
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "effects": self.effects.as_dict(),
            "card_state": self.card_state,
            "deferred": self.deferred,
            "error": self.error,
        }


def project_administration(
    repository: Repository,
    *,
    administration_id: str,
    eligible: bool,
    failed: bool,
    card_lineage_id: str | None = None,
    scheduler_algorithm_version: str | None = None,
    review_event: Mapping[str, Any] | None = None,
    prior_reviews: Sequence[Mapping[str, Any]] = (),
    model_label: str = "fsrs",
    clock: Clock | None = None,
) -> ProjectionResult:
    """Resolve the purpose adapter and project scheduling in one fail-safe unit.

    Fail-safe (§7.5 partial projection failure): an adapter/projection error keeps
    the raw events and returns ``deferred=True`` (a deterministic rebuild can be
    re-run) -- it NEVER raises into the attempt writer. Familiarity/exposure is the
    caller's concern (always full exposure); this focuses on the scheduling delta,
    which is the one that must not half-update card state.
    """

    try:
        adapter = resolve_adapter_for_administration(repository, administration_id)
        effects = adapter.effects(eligible=eligible, failed=failed)
        card_state = None
        if effects.applies_fsrs_review and card_lineage_id and scheduler_algorithm_version:
            card_state = adapter.apply_scheduling(
                repository,
                card_lineage_id=card_lineage_id,
                scheduler_algorithm_version=scheduler_algorithm_version,
                review_event=review_event,
                eligible=eligible,
                prior_reviews=prior_reviews,
                model_label=model_label,
                clock=clock,
            )
        return ProjectionResult(effects=effects, card_state=card_state, deferred=False)
    except OpportunisticDiagnosisRejected:
        raise
    except Exception as exc:  # noqa: BLE001 -- fail-safe: keep raw events, enqueue rebuild
        row = repository.activity_administration(administration_id)
        purpose = row["purpose"] if row is not None else "practice"
        try:
            effects = resolve_adapter(purpose).effects(eligible=eligible, failed=failed)
        except Exception:  # noqa: BLE001
            effects = PracticeAdapter().effects(eligible=eligible, failed=failed)
        return ProjectionResult(effects=effects, card_state=None, deferred=True, error=str(exc))


# ---------------------------------------------------------------------------
# Hot-path seam (attempts.apply_attempt).
# ---------------------------------------------------------------------------

def hot_path_applies_practice_review(*, attempt_type: str, eligible: bool = True) -> bool:
    """Whether the attempt hot path applies its FSRS practice review: the practice
    adapter's eligibility semantics. ``apply_attempt`` is reached only by ordinary
    practice attempts (diagnostic-probe/exam are excluded upstream); for an
    eligible one the review applies, while an ineligible (quarantined /
    out-of-band) observation leaves card state unchanged (§3.8)."""

    return PracticeAdapter().effects(eligible=eligible, failed=False).applies_fsrs_review
