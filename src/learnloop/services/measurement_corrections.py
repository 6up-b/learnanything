"""Append-only authoring corrections for attempted assessment contracts (§5.7).

An attempted PracticeItem is an immutable historical surface. Correcting its
measurement contract mints a sibling PracticeItem and contract snapshot, then
records immutable edges from every source contract version to the corrected
version. A named projection may follow those edges only when the correction
explicitly authorizes historical reinterpretation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.assessment_contracts import (
    compile_assessment_contract,
    snapshot_for_presentation,
)
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import PracticeItem
from learnloop.vault.writer import upsert_practice_item


class MeasurementCorrectionError(ValueError):
    """The requested change cannot be represented as an honest correction."""


@dataclass(frozen=True)
class MeasurementCorrectionResult:
    correction_set_id: str
    correction_ids: list[str]
    source_practice_item_id: str
    corrected_practice_item_id: str
    source_contract_version_ids: list[str]
    corrected_contract_version_id: str
    consuming_projection_version: str
    historical_evidence_policy: str
    projection_rebuild_id: str | None


def _criterion_signature(contract: Mapping[str, Any]) -> dict[str, float]:
    return {
        str(criterion["id"]): float(criterion.get("max_points") or 0.0)
        for criterion in contract.get("criteria") or []
    }


def _assert_reinterpretable(
    source_contract: Mapping[str, Any],
    corrected_contract: Mapping[str, Any],
) -> None:
    """Ensure the correction changes measurement, not the historical task.

    Projection-time reinterpretation may repair criterion target links,
    measurement statuses, trace metadata, or correlation metadata. It may not
    pretend the learner saw a different prompt/answer contract or was graded
    against different criterion identifiers/maxima.
    """

    immutable_checks = (
        (
            "learning_object_id",
            source_contract.get("learning_object_id"),
            corrected_contract.get("learning_object_id"),
        ),
        (
            "prompt",
            source_contract.get("prompt"),
            corrected_contract.get("prompt"),
        ),
        (
            "expected_answer",
            source_contract.get("expected_answer"),
            corrected_contract.get("expected_answer"),
        ),
        (
            "item_content_hash",
            source_contract.get("item_content_hash"),
            corrected_contract.get("item_content_hash"),
        ),
        (
            "criterion maxima",
            _criterion_signature(source_contract),
            _criterion_signature(corrected_contract),
        ),
        (
            "rubric_total",
            float(source_contract.get("rubric_total") or 0.0),
            float(corrected_contract.get("rubric_total") or 0.0),
        ),
    )
    changed = [name for name, before, after in immutable_checks if before != after]
    if changed:
        raise MeasurementCorrectionError(
            "historical reinterpretation cannot change " + ", ".join(changed)
        )


def create_measurement_correction(
    root: Path,
    repository: Repository,
    *,
    source_practice_item_id: str,
    corrected_fields: Mapping[str, Any],
    reason: str,
    consuming_projection_version: str,
    reinterpret_historical_evidence: bool = False,
    corrected_practice_item_id: str | None = None,
    clock: Clock | None = None,
) -> MeasurementCorrectionResult:
    """Mint a corrected item/version and append projection-versioned receipts.

    `corrected_fields` is a partial PracticeItem payload. The source item is
    never edited. Unattempted items intentionally do not enter this workflow:
    they can be re-audited directly through the normal authoring writer.
    """

    reason = reason.strip()
    projection_version = consuming_projection_version.strip()
    if not reason:
        raise MeasurementCorrectionError("a correction reason is required")
    if not projection_version:
        raise MeasurementCorrectionError("a consuming projection version is required")

    vault = load_vault(root)
    source = vault.practice_items.get(source_practice_item_id)
    if source is None:
        raise MeasurementCorrectionError(
            f"unknown source PracticeItem {source_practice_item_id!r}"
        )
    if source_practice_item_id not in repository.attempted_practice_item_ids():
        raise MeasurementCorrectionError(
            "unattempted items must be re-audited directly; no historical "
            "measurement correction is needed"
        )
    if source_practice_item_id in repository.superseded_measurement_item_ids():
        raise MeasurementCorrectionError(
            "source PracticeItem already has an accepted measurement correction"
        )

    corrected_id = (
        corrected_practice_item_id.strip()
        if corrected_practice_item_id is not None
        else f"pi_correction_{new_ulid().lower()}"
    )
    if not corrected_id or corrected_id == source_practice_item_id:
        raise MeasurementCorrectionError("the corrected PracticeItem must have a new id")
    if corrected_id in vault.practice_items:
        raise MeasurementCorrectionError(
            f"corrected PracticeItem {corrected_id!r} already exists"
        )
    if "id" in corrected_fields and str(corrected_fields["id"]) != corrected_id:
        raise MeasurementCorrectionError(
            "corrected_fields.id must match corrected_practice_item_id"
        )
    if (
        "learning_object_id" in corrected_fields
        and str(corrected_fields["learning_object_id"]) != source.learning_object_id
    ):
        raise MeasurementCorrectionError(
            "a measurement correction cannot move an item to another learning object"
        )

    now = utc_now_iso(clock)
    payload = source.model_dump(mode="json", exclude_none=False)
    payload.update(dict(corrected_fields))
    payload.update(
        {
            "id": corrected_id,
            "learning_object_id": source.learning_object_id,
            "status": "active",
            "status_reason": None,
            "created_at": now,
            "updated_at": now,
        }
    )
    tags = [str(tag) for tag in payload.get("tags") or []]
    correction_tag = f"measurement-correction:{source_practice_item_id}"
    if correction_tag not in tags:
        tags.append(correction_tag)
    payload["tags"] = tags
    corrected = PracticeItem.model_validate(payload)
    corrected_contract = compile_assessment_contract(vault, corrected)

    source_versions = repository.assessment_contract_versions_for_practice_item(
        source_practice_item_id
    )
    if not source_versions:
        source_version_id = snapshot_for_presentation(
            repository, vault, source, clock=clock
        )
        stored = repository.fetch_assessment_contract_version(source_version_id)
        source_versions = [stored] if stored is not None else []
    if not source_versions:
        raise MeasurementCorrectionError("could not snapshot the source contract")

    policy = (
        "reinterpret_measurement"
        if reinterpret_historical_evidence
        else "preserve_original"
    )
    if reinterpret_historical_evidence:
        for source_version in source_versions:
            _assert_reinterpretable(source_version["contract"], corrected_contract)

    # The new file is the only vault mutation. The attempted source file stays
    # byte-for-byte untouched, including its misleading authored maps.
    upsert_practice_item(root, corrected, clock=clock)
    corrected_vault = load_vault(root)
    corrected_item = corrected_vault.practice_items[corrected_id]
    corrected_version_id = snapshot_for_presentation(
        repository, corrected_vault, corrected_item, clock=clock
    )

    correction_set_id = new_ulid()
    source_version_ids = [str(version["id"]) for version in source_versions]
    correction_ids = repository.append_measurement_contract_corrections(
        correction_set_id=correction_set_id,
        source_practice_item_id=source_practice_item_id,
        source_contract_version_ids=source_version_ids,
        corrected_practice_item_id=corrected_id,
        corrected_contract_version_id=corrected_version_id,
        consuming_projection_version=projection_version,
        historical_evidence_policy=policy,
        reason=reason,
        correction={
            "corrected_fields": sorted(str(key) for key in corrected_fields),
            "source_item_preserved": True,
        },
        clock=clock,
    )
    # The source remains in the vault for replay/audit but becomes unschedulable;
    # the corrected sibling is activated in the same reconciliation pass.
    sync_vault_state(corrected_vault, repository, clock=clock)
    projection_rebuild_id: str | None = None
    if (
        reinterpret_historical_evidence
        and corrected_vault.config.algorithms.algorithm_version == projection_version
    ):
        from learnloop.services.canonical_projection import (
            project_canonical_facet_state,
        )

        project_canonical_facet_state(corrected_vault, repository, clock=clock)
        learning_object_ids = repository.learning_object_ids_with_attempts()
        projection_rebuild_id = repository.record_derived_state_rebuild(
            scope=f"measurement_correction:{correction_set_id}",
            learning_object_ids=learning_object_ids,
            algorithm_version=projection_version,
            rebuilt_learning_objects=len(learning_object_ids),
            replayed_attempts=len(repository.list_all_attempts()),
            clock=clock,
        )

    return MeasurementCorrectionResult(
        correction_set_id=correction_set_id,
        correction_ids=correction_ids,
        source_practice_item_id=source_practice_item_id,
        corrected_practice_item_id=corrected_id,
        source_contract_version_ids=source_version_ids,
        corrected_contract_version_id=corrected_version_id,
        consuming_projection_version=projection_version,
        historical_evidence_policy=policy,
        projection_rebuild_id=projection_rebuild_id,
    )
