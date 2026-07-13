"""Family-version and instance lifecycle transitions (§9.7, Checkpoint 4.7).

    draft -> provisional -> trusted | revised version | retired

Promotion to ``trusted`` and retirement are gated on REAL-LEARNER evidence
only: synthetic admission statistics establish structural validity (§9.6) but
never trust. Every transition persists a lifecycle event with the metric
evidence that justified it. Retiring a version never changes the meaning of
historical observations — replay keeps resolving the persisted version (§9.1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.probe_audit import eig_calibration_report, grading_confusion_report
from learnloop.services.probe_families import ProbeFamilyTemplate
from learnloop.vault.models import LoadedVault

# from -> allowed targets. `retired` is terminal; a revision is a NEW draft
# version, never a resurrection of the retired one.
ALLOWED_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "draft": ("provisional", "retired"),
    "provisional": ("trusted", "retired"),
    "trusted": ("provisional", "retired"),
    "retired": (),
}


class LifecycleTransitionError(ValueError):
    pass


@dataclass(frozen=True)
class FamilyLifecycleMetrics:
    real_sample_size: int
    real_effective_sample_size: float
    eligible_observations: int
    negative_information_rate: float | None
    mean_realized_minus_expected: float | None
    regrade_checks: int
    regrade_agreement: float | None


@dataclass(frozen=True)
class FamilyLifecycleAssessment:
    family_id: str
    version: int
    status: str
    metrics: FamilyLifecycleMetrics
    recommendation: str  # promote_to_trusted | retire | retain | insufficient_evidence | retired
    reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "family_id": self.family_id,
            "version": self.version,
            "status": self.status,
            "recommendation": self.recommendation,
            "reasons": self.reasons,
            "metrics": {
                "real_sample_size": self.metrics.real_sample_size,
                "real_effective_sample_size": round(self.metrics.real_effective_sample_size, 2),
                "eligible_observations": self.metrics.eligible_observations,
                "negative_information_rate": self.metrics.negative_information_rate,
                "mean_realized_minus_expected": self.metrics.mean_realized_minus_expected,
                "regrade_checks": self.metrics.regrade_checks,
                "regrade_agreement": self.metrics.regrade_agreement,
            },
        }


def family_lifecycle_metrics(
    repository: Repository, family_id: str, version: int
) -> FamilyLifecycleMetrics:
    """Real-learner evidence for one family version (synthetic rows excluded)."""

    real_sample = 0
    real_effective = 0.0
    for row in repository.probe_family_calibrations_for_family(family_id, version):
        if row["evidence_source"] != "real_learner":
            continue
        real_sample += int(row["sample_size"])
        real_effective += float(row["effective_sample_size"] or 0.0)

    key = f"{family_id}@v{version}"
    eig_bucket = eig_calibration_report(repository)["by_family"].get(key, {})
    regrade_checks = 0
    regrade_agreements = 0
    for scope in grading_confusion_report(repository)["scopes"].values():
        if scope["family"] == family_id and scope["version"] == version:
            regrade_checks += scope["checks"]
            regrade_agreements += scope["agreements"]
    return FamilyLifecycleMetrics(
        real_sample_size=real_sample,
        real_effective_sample_size=real_effective,
        eligible_observations=int(eig_bucket.get("observations") or 0),
        negative_information_rate=eig_bucket.get("negative_information_rate"),
        mean_realized_minus_expected=eig_bucket.get("mean_realized_minus_expected"),
        regrade_checks=regrade_checks,
        regrade_agreement=(regrade_agreements / regrade_checks) if regrade_checks else None,
    )


def evaluate_family_lifecycle(
    vault: LoadedVault, repository: Repository, family_id: str, version: int
) -> FamilyLifecycleAssessment:
    """Recommend a transition for one family version against the §9.7 gates.

    A recommendation is advice for the CLI/reviewer; nothing transitions
    automatically. Retirement telemetry (negative realized information,
    grading disagreement) dominates promotion criteria.
    """

    record = repository.probe_family_template(family_id, version)
    if record is None:
        raise LifecycleTransitionError(f"unknown family version {family_id} v{version}")
    metrics = family_lifecycle_metrics(repository, family_id, version)
    config = vault.config.probe.lifecycle
    reasons: list[str] = []

    if record.status == "retired":
        return FamilyLifecycleAssessment(family_id, version, record.status, metrics, "retired")

    negative_rate = metrics.negative_information_rate
    if (
        metrics.eligible_observations >= config.retire_minimum_sample
        and negative_rate is not None
        and negative_rate >= config.retire_negative_information_rate
    ):
        reasons.append(
            f"negative realized information rate {negative_rate:.2f} >= "
            f"{config.retire_negative_information_rate} over {metrics.eligible_observations} observations"
        )
    if (
        metrics.regrade_checks >= max(config.trust_minimum_regrade_checks, 1)
        and metrics.regrade_agreement is not None
        and metrics.regrade_agreement < config.retire_regrade_agreement_floor
    ):
        reasons.append(
            f"regrade agreement {metrics.regrade_agreement:.2f} < "
            f"{config.retire_regrade_agreement_floor} over {metrics.regrade_checks} checks"
        )
    if reasons:
        return FamilyLifecycleAssessment(family_id, version, record.status, metrics, "retire", reasons)

    if record.status == "provisional":
        unmet: list[str] = []
        if metrics.real_sample_size < config.trust_minimum_real_sample:
            unmet.append(
                f"real-learner sample {metrics.real_sample_size} < {config.trust_minimum_real_sample}"
            )
        if metrics.regrade_checks < config.trust_minimum_regrade_checks:
            unmet.append(
                f"regrade checks {metrics.regrade_checks} < {config.trust_minimum_regrade_checks}"
            )
        elif (
            metrics.regrade_agreement is not None
            and metrics.regrade_agreement < config.trust_minimum_regrade_agreement
        ):
            unmet.append(
                f"regrade agreement {metrics.regrade_agreement:.2f} < "
                f"{config.trust_minimum_regrade_agreement}"
            )
        if metrics.eligible_observations == 0:
            unmet.append("no eligible observations")
        elif (
            negative_rate is not None
            and negative_rate > config.trust_maximum_negative_information_rate
        ):
            unmet.append(
                f"negative information rate {negative_rate:.2f} > "
                f"{config.trust_maximum_negative_information_rate}"
            )
        if not unmet:
            return FamilyLifecycleAssessment(
                family_id, version, record.status, metrics, "promote_to_trusted",
                ["all trust gates met on real-learner evidence"],
            )
        return FamilyLifecycleAssessment(
            family_id, version, record.status, metrics, "insufficient_evidence", unmet
        )

    return FamilyLifecycleAssessment(family_id, version, record.status, metrics, "retain")


def apply_family_lifecycle_transition(
    repository: Repository,
    *,
    family_id: str,
    version: int,
    to_status: str,
    reason: dict[str, Any] | None = None,
    clock: Clock | None = None,
) -> None:
    """Apply one explicit transition and persist its lifecycle event."""

    record = repository.probe_family_template(family_id, version)
    if record is None:
        raise LifecycleTransitionError(f"unknown family version {family_id} v{version}")
    if to_status == record.status:
        raise LifecycleTransitionError(f"{family_id} v{version} is already {to_status}")
    allowed = ALLOWED_TRANSITIONS.get(record.status, ())
    if to_status not in allowed:
        raise LifecycleTransitionError(
            f"cannot transition {family_id} v{version} from {record.status} to {to_status}; "
            f"allowed: {list(allowed) or 'none (terminal)'}"
        )
    repository.update_probe_family_template_status(family_id, version, status=to_status, clock=clock)
    repository.insert_probe_family_lifecycle_event(
        probe_family_template_id=family_id,
        probe_family_template_version=version,
        from_status=record.status,
        to_status=to_status,
        reason=reason,
        clock=clock,
    )


def revise_family_version(
    repository: Repository,
    family_id: str,
    *,
    clock: Clock | None = None,
) -> int:
    """Create the next version as a draft copy of the latest template (§9.7).

    Revision is how a compiled row gets structurally fixed: the ordinal words
    change on the NEW version while the old version keeps replaying history
    unchanged. Returns the new version number.
    """

    latest = repository.latest_probe_family_template(
        family_id, statuses=("draft", "provisional", "trusted", "retired")
    )
    if latest is None:
        raise LifecycleTransitionError(f"unknown family {family_id}")
    template = ProbeFamilyTemplate.from_dict(latest.template)
    new_version = latest.version + 1
    revised = ProbeFamilyTemplate.from_dict({**template.as_dict(), "version": new_version})
    repository.upsert_probe_family_template(
        family_id=family_id,
        version=new_version,
        status="draft",
        template=revised.as_dict(),
        schema_hash=revised.schema_hash(),
        clock=clock,
    )
    repository.insert_probe_family_lifecycle_event(
        probe_family_template_id=family_id,
        probe_family_template_version=new_version,
        from_status=latest.status,
        to_status="draft",
        reason={"revised_from_version": latest.version},
        clock=clock,
    )
    return new_version


def retire_probe_instance(
    repository: Repository,
    practice_item_id: str,
    *,
    reason: str | None = None,
    clock: Clock | None = None,
) -> bool:
    """Retire one generated instance: deactivate the item and mark every
    family link's review status. Historical observations are untouched."""

    links = repository.probe_item_family_links(practice_item_id)
    if not links:
        return False
    for link in links:
        metadata = dict(link.instance_metadata or {})
        metadata["review_status"] = "retired"
        if reason:
            metadata["retired_reason"] = reason
        repository.update_probe_item_family_metadata(
            practice_item_id=practice_item_id,
            instrument_card_id=link.instrument_card_id,
            instrument_card_version=link.instrument_card_version,
            instance_metadata=metadata,
        )
    repository.set_practice_item_active(practice_item_id, active=False, clock=clock)
    return True


def family_lifecycle_overview(
    vault: LoadedVault, repository: Repository
) -> list[FamilyLifecycleAssessment]:
    """Assessment for every stored family version, for the CLI report."""

    return [
        evaluate_family_lifecycle(vault, repository, record.id, record.version)
        for record in repository.all_probe_family_templates()
    ]
