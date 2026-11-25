"""Deterministic, idempotent backfill of the activity lineage substrate (§7.1).

Runs as a SERVICE function, never inside the migration (migration 065 creates
only empty tables). Re-runnable on a copy of any fixture vault (§9.6 line 1): the
ensure_* writers are content-addressed and synthetic administrations/exposures
key on ``activity_observations.attempt_id`` and existing rows, so a second run
inserts nothing new. Historical rows are timestamped at their RECORDED time
(attempt.created_at), never now(), so byte stability holds across re-runs.

Substrate slice of §7.1 (steps 1-4):

1. Each PracticeItem -> a default legacy ``practice`` family/card/surface. Items
   used for a probe or exam additionally get a purpose-specific diagnostic or
   assessment adapter card+surface with the EXACT identical ``surface_hash``.
2. Every ``assessment_contract_versions`` row -> a semantic card + exact surface,
   mapped back via ``activity_card_versions.legacy_contract_version_id``.
3. Probe instrument-card snapshots -> ``diagnostic``-purpose family/card versions.
4. Each historical attempt -> a synthetic administration + exposure + observation
   at its recorded time; surfaces reconstructed from a missing item are marked
   ``legacy_surface_unverifiable`` (replay preserved, no new pristine credit).

Historical means recorded before the substrate existed (review round 3, FR3-6): before the vault's first
administration written live (:func:`substrate_began_at`, a stored fact). A rebuild derives, so it never writes
evidence the live write should have recorded: a later answer with no observation (a grade whose grade-channel write
failed) is left as it is and reported (:func:`answers_without_grade_record`); ``learnloop doctor`` names it and only
its explicit repair (``doctor --fix-state``) records it. A later probe presentation keeps the rows its live write
made, and none are added.

Steps 5-7 (raw-grade/interpretation conversion, exam-pool reservation
conversion, calibration seeding + registry) belong to the grading/calibration
packages and are out of P0.1 scope; the substrate columns they need already exist.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from datetime import datetime

from learnloop.clock import Clock, FrozenClock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.substrate.activities import (
    _CONSUMING_PURPOSES,
    _PURPOSE_TO_LEGACY_KIND,
    canonical_json,
    administration_snapshot_hash,
    resolve_legacy_item,
)
from learnloop.learner.assessment_contracts import compile_assessment_contract
from learnloop.vault.models import LoadedVault, PracticeItem


@dataclass
class BackfillReport:
    practice_items: int = 0
    diagnostic_adapters: int = 0
    assessment_adapters: int = 0
    contract_versions_split: int = 0
    probe_cards_mapped: int = 0
    presentations_replayed: int = 0
    presentations_skipped_existing: int = 0
    attempts_replayed: int = 0
    attempts_skipped_existing: int = 0
    #: Rows recorded after the substrate existed that have no backfilled counterpart, left as they are: the
    #: presentations their live write already accounts for, and answers missing their observation (reported).
    presentations_after_substrate: int = 0
    attempts_after_substrate_without_observation: int = 0
    surfaces_unverifiable: int = 0
    families: set[str] = field(default_factory=set)
    surfaces: set[str] = field(default_factory=set)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["families"] = sorted(self.families)
        payload["surfaces"] = sorted(self.surfaces)
        payload["family_count"] = len(self.families)
        payload["surface_count"] = len(self.surfaces)
        return payload


def _purpose_for_attempt_type(attempt_type: str) -> str:
    if attempt_type == "diagnostic_probe":
        return "diagnostic"
    if "exam" in attempt_type:
        return "assessment"
    return "practice"


def substrate_began_at(repository: Repository) -> datetime | None:
    """The instant the activity substrate existed from: the vault's first administration written live (the
    backfill's own are marked ``legacy_backfilled``), in the clock the vault's own rows are dated by. None when the
    vault never wrote one."""

    return parse_utc(repository.first_live_administration_at())


def predates_substrate(recorded_at: str | None, began: datetime | None) -> bool:
    """Whether a row recorded at ``recorded_at`` is history from before the substrate (see :func:`substrate_began_at`).

    A vault that never wrote an administration live has no history to backfill: what it holds was recorded by code
    that writes the substrate wherever it writes at all (a probe presentation, a presentationless probe answer), and
    every supported vault older than the substrate had its earlier answers backfilled by the whole-vault rebuilds of
    its upgrades. Should one not have been, its answers are reported as missing their grade record and the repair
    records them: visible, never invented by a rebuild."""

    if began is None:
        return False
    instant = parse_utc(recorded_at)
    return instant is not None and instant < began


def answers_without_grade_record(vault: LoadedVault, repository: Repository) -> list[dict[str, Any]]:
    """Answers recorded after the substrate existed whose grade record (the one ``apply_attempt``'s grade channel
    writes) is incomplete: no observation, or an observation with no raw grade (the write failed after it minted the
    identity). A rebuild never writes these (it derives; FR3-6); ``learnloop doctor`` reports them and
    ``doctor --fix-state`` records them, through that same channel.

    Answers that channel never records are left out: a diagnostic probe (its own paths record a grade when a
    presentation or a lesson asked the question; a presentationless probe records none by design) and an exam answer
    graded once (the sitting records it; an import records none). An exam answer regraded is the channel's from the
    evidence reading fixes (K5-11, the rule of ``attempts.replay_reading.replaced_exam_purpose``)."""

    from learnloop.algorithm_versions import evidence_reading_fixes_on
    from learnloop.grading_epochs import graded_more_than_once

    regraded_exams_recorded = evidence_reading_fixes_on(vault.config)
    began = substrate_began_at(repository)
    missing: list[dict[str, Any]] = []
    for row in repository.answer_grade_records():
        if row["attempt_type"] == "diagnostic_probe" or predates_substrate(row["created_at"], began):
            continue
        if "exam" in str(row["attempt_type"]) and not (regraded_exams_recorded and graded_more_than_once(
                repository.fetch_grading_evidence(row["id"], include_superseded=True))):
            continue
        if row["observation_id"] is None:
            missing.append({"attempt_id": row["id"], "learning_object_id": row["learning_object_id"],
                            "missing": "observation"})
        elif not row["graded"]:
            missing.append({"attempt_id": row["id"], "learning_object_id": row["learning_object_id"],
                            "missing": "grade"})
    return missing


def _clock_at(iso: str | None) -> Clock:
    instant = parse_utc(iso)
    if instant is None:  # pragma: no cover - defensive; attempts always carry a time
        raise ValueError("historical row is missing a timestamp")
    return FrozenClock(instant)


def backfill_activity_substrate(
    vault: LoadedVault,
    repository: Repository,
    *,
    clock: Clock | None = None,
) -> BackfillReport:
    """Backfill migration-065 tables from the vault + legacy SQL (§7.1 steps 1-4)."""

    report = BackfillReport()
    items: dict[str, PracticeItem] = dict(vault.practice_items)
    attempts = repository.list_all_attempts()
    # Read before this run writes anything (its own rows are marked backfilled and never move it).
    began = substrate_began_at(repository)

    # Which items were used for a probe / exam (adapter minting, step 1 tail).
    diagnostic_items: set[str] = set()
    assessment_items: set[str] = set()
    for attempt in attempts:
        purpose = _purpose_for_attempt_type(attempt["attempt_type"])
        if purpose == "diagnostic":
            diagnostic_items.add(attempt["practice_item_id"])
        elif purpose == "assessment":
            assessment_items.add(attempt["practice_item_id"])

    # --- Step 1: default practice family/card/surface for every item. ---------
    for item_id in sorted(items):
        item = items[item_id]
        resolved = resolve_legacy_item(
            vault, repository, item, purpose="practice", clock=clock
        )
        report.practice_items += 1
        report.families.add(resolved.family_id)
        report.surfaces.add(resolved.surface_id)
        # Step 1 tail: purpose-specific adapters (identical surface_hash).
        if item_id in diagnostic_items:
            adapter = resolve_legacy_item(
                vault, repository, item, purpose="diagnostic", clock=clock
            )
            report.diagnostic_adapters += 1
            report.families.add(adapter.family_id)
            report.surfaces.add(adapter.surface_id)
        if item_id in assessment_items:
            adapter = resolve_legacy_item(
                vault, repository, item, purpose="assessment", clock=clock
            )
            report.assessment_adapters += 1
            report.families.add(adapter.family_id)
            report.surfaces.add(adapter.surface_id)

    # --- Step 2: split assessment_contract_versions -> card + surface. --------
    for row in repository.list_all_assessment_contract_versions():
        item = items.get(row["practice_item_id"])
        if item is None:
            continue  # source item gone; nothing to split deterministically
        from learnloop.substrate.activities import (
            card_contract_hash,
            card_semantic_payload,
            fingerprint_of,
            surface_hash,
            surface_payload,
        )

        contract = compile_assessment_contract(vault, item)
        legacy_kind = _PURPOSE_TO_LEGACY_KIND["practice"]
        family_id = repository.ensure_activity_family(
            purpose="practice", legacy_kind=legacy_kind, title=item.id, clock=clock
        )
        card_id = repository.ensure_activity_card(family_id=family_id, clock=clock)
        card_version_id = repository.ensure_activity_card_version(
            card_id=card_id,
            version=1,
            card_contract_hash=card_contract_hash(contract, purpose="practice"),
            contract_json=canonical_json(card_semantic_payload(contract, purpose="practice")),
            schema_version=int(getattr(item, "schema_version", 1) or 1),
            legacy_contract_version_id=row["id"],
            clock=clock,
        )
        repository.ensure_activity_surface(
            card_version_id=card_version_id,
            surface_hash=surface_hash(contract),
            fingerprint=fingerprint_of(contract),
            surface_json=canonical_json(surface_payload(contract)),
            legacy_practice_item_id=item.id,
            clock=clock,
        )
        report.contract_versions_split += 1

    # --- Step 3: probe instrument cards -> diagnostic family/card versions. ----
    for card in repository.list_all_probe_instrument_cards():
        legacy_id = f"{card['id']}@{card['version']}"
        family_id = repository.ensure_activity_family(
            purpose="diagnostic",
            legacy_kind="probe",
            title=legacy_id,
            clock=_clock_at(card.get("created_at")),
        )
        repository.ensure_activity_family_version(
            family_id=family_id,
            version=1,
            family_spec_json=canonical_json(
                {
                    "probe_instrument_card_id": card["id"],
                    "version": card["version"],
                    "learning_object_id": card.get("learning_object_id"),
                    "compiled_likelihood_hash": card.get("compiled_likelihood_hash"),
                }
            ),
            clock=_clock_at(card.get("created_at")),
        )
        card_id = repository.ensure_activity_card(
            family_id=family_id, clock=_clock_at(card.get("created_at"))
        )
        repository.ensure_activity_card_version(
            card_id=card_id,
            version=1,
            card_contract_hash=str(card.get("compiled_likelihood_hash") or legacy_id)[:32],
            contract_json=card.get("card_json") or "{}",
            schema_version=1,
            legacy_contract_version_id=legacy_id,
            clock=_clock_at(card.get("created_at")),
        )
        report.probe_cards_mapped += 1
        report.families.add(family_id)

    # --- Step 3b: probe presentations -> synthetic diagnostic administration +
    # exposure events (§7.1 step 3, "presentations become administrations and
    # exposure events without changing their historical ids"). Idempotent: keyed on
    # the presentation id stored in the administration snapshot; reuses the
    # per-attempt pattern above. A presentation whose source item is gone is skipped
    # (the attempt-level step 4 still reconstructs an unverifiable surface for it).
    for presentation in repository.list_all_probe_presentations():
        if repository.administration_by_legacy_presentation(presentation["id"]) is not None:
            report.presentations_skipped_existing += 1
            continue
        item = items.get(presentation["practice_item_id"])
        if item is None:
            continue
        created_at = presentation.get("served_at") or presentation["created_at"]
        if not predates_substrate(created_at, began):
            report.presentations_after_substrate += 1
            continue
        pres_clock = _clock_at(created_at)
        resolved = resolve_legacy_item(
            vault, repository, item, purpose="diagnostic", clock=pres_clock
        )
        snapshot_payload = {
            "card_version_id": resolved.card_version_id,
            "surface_id": resolved.surface_id,
            "surface_hash": resolved.surface_hash,
            "purpose": "diagnostic",
            "legacy_presentation_id": presentation["id"],
            "probe_episode_id": presentation.get("probe_episode_id"),
        }
        administration_id = repository.insert_legacy_administration(
            surface_id=resolved.surface_id,
            card_version_id=resolved.card_version_id,
            family_id=resolved.family_id,
            purpose="diagnostic",
            snapshot_hash=administration_snapshot_hash(snapshot_payload),
            snapshot_json=canonical_json(snapshot_payload),
            eligibility_json=canonical_json({"legacy_backfilled": True, "from_presentation": True}),
            created_at=created_at,
        )
        existing = repository.exposures_for_surface(resolved.surface_id)
        if not any(event["kind"] == "rendered" for event in existing):
            repository.append_exposure_event_at(
                surface_id=resolved.surface_id,
                administration_id=administration_id,
                surface_hash=resolved.surface_hash,
                fingerprint=resolved.fingerprint,
                kind="rendered",
                purpose="diagnostic",
                consumes_unseen="diagnostic" in _CONSUMING_PURPOSES,
                created_at=created_at,
            )
        report.presentations_replayed += 1
        report.families.add(resolved.family_id)
        report.surfaces.add(resolved.surface_id)

    # --- Step 4: attempts -> synthetic administration + exposure + observation.
    for attempt in attempts:
        if repository.observation_by_attempt(attempt["id"]) is not None:
            report.attempts_skipped_existing += 1
            continue
        if not predates_substrate(attempt.get("created_at"), began):
            # Its live write should have recorded the observation; a rebuild does not invent it (FR3-6).
            report.attempts_after_substrate_without_observation += 1
            continue
        purpose = _purpose_for_attempt_type(attempt["attempt_type"])
        item = items.get(attempt["practice_item_id"])
        attempt_clock = _clock_at(attempt.get("created_at"))
        created_at = attempt["created_at"]

        if item is not None:
            resolved = resolve_legacy_item(
                vault, repository, item, purpose=purpose, clock=attempt_clock
            )
            surface_id = resolved.surface_id
            card_version_id = resolved.card_version_id
            family_id = resolved.family_id
            sh = resolved.surface_hash
            fp = resolved.fingerprint
        else:
            # Item is gone: exact historical surface content is unrecoverable.
            # Preserve replay via a deterministic placeholder surface, marked
            # legacy_surface_unverifiable (grants no new pristine terminal credit).
            legacy_id = attempt["practice_item_id"]
            family_id = repository.ensure_activity_family(
                purpose=purpose,
                legacy_kind="synthetic",
                title=f"unverifiable::{legacy_id}",
                clock=attempt_clock,
            )
            card_id = repository.ensure_activity_card(family_id=family_id, clock=attempt_clock)
            placeholder_contract = {"legacy_practice_item_id": legacy_id, "unverifiable": True}
            from learnloop.substrate.activities import canonical_hash

            card_version_id = repository.ensure_activity_card_version(
                card_id=card_id,
                version=1,
                card_contract_hash=canonical_hash(placeholder_contract),
                contract_json=canonical_json(placeholder_contract),
                schema_version=1,
                legacy_contract_version_id=None,
                clock=attempt_clock,
            )
            sh = canonical_hash({"unverifiable_surface": legacy_id})
            fp = None
            surface_id = repository.ensure_activity_surface(
                card_version_id=card_version_id,
                surface_hash=sh,
                fingerprint=None,
                surface_json=canonical_json(placeholder_contract),
                legacy_practice_item_id=legacy_id,
                legacy_surface_unverifiable=True,
                clock=attempt_clock,
            )
            repository.mark_surface_unverifiable(surface_id)
            report.surfaces_unverifiable += 1

        report.families.add(family_id)
        report.surfaces.add(surface_id)

        snapshot_payload = {
            "card_version_id": card_version_id,
            "surface_id": surface_id,
            "surface_hash": sh,
            "purpose": purpose,
            "legacy_attempt_id": attempt["id"],
        }
        administration_id = repository.insert_legacy_administration(
            surface_id=surface_id,
            card_version_id=card_version_id,
            family_id=family_id,
            purpose=purpose,
            snapshot_hash=administration_snapshot_hash(snapshot_payload),
            snapshot_json=canonical_json(snapshot_payload),
            eligibility_json=canonical_json({"legacy_backfilled": True}),
            created_at=created_at,
        )

        consumes_unseen = purpose in _CONSUMING_PURPOSES
        existing = repository.exposures_for_surface(surface_id)
        has_rendered = any(event["kind"] == "rendered" for event in existing)
        if not has_rendered:
            repository.append_exposure_event_at(
                surface_id=surface_id,
                administration_id=administration_id,
                surface_hash=sh,
                fingerprint=fp,
                kind="rendered",
                purpose=purpose,
                consumes_unseen=consumes_unseen,
                created_at=created_at,
            )
        repository.append_exposure_event_at(
            surface_id=surface_id,
            administration_id=administration_id,
            surface_hash=sh,
            fingerprint=fp,
            kind="submitted",
            purpose=purpose,
            consumes_unseen=False,
            created_at=created_at,
            detail_json=canonical_json({"attempt_type": attempt["attempt_type"]}),
        )
        repository.insert_activity_observation(
            administration_id=administration_id,
            surface_id=surface_id,
            attempt_id=attempt["id"],
            response_ref=attempt["id"],
            clock=attempt_clock,
        )

        # §3.8: attempt-duration interaction event where the attempt path records one.
        latency = attempt.get("latency_seconds")
        if latency is not None:
            repository.append_interaction_event(
                kind="attempt_duration",
                origin="system",
                subject_type="administration",
                subject_id=administration_id,
                administration_id=administration_id,
                surface_id=surface_id,
                attempt_id=attempt["id"],
                attempt_duration_ms=int(float(latency) * 1000),
                payload_json=canonical_json({"source": "legacy_attempt", "unit": "seconds"}),
                clock=attempt_clock,
            )

        report.attempts_replayed += 1

    return report
