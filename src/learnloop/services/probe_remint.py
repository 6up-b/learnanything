"""Learner-initiated remint: keep an administered diagnostic probe as practice.

Sometimes a single-use ``practice_mode: diagnostic_probe`` surface happens to be
a genuinely good exercise. After its one administration the learner may ask to
KEEP it: a NEW ordinary practice item is minted as a mechanical copy of the
probe's content (prompt, expected answer, rubric, facets, trace contract,
difficulty), reassigned to an ordinary practice mode. The probe itself is never
mutated — it stays deactivated with its administration history intact, exactly
as the single-use rules left it.

Governance: this is a DIRECT mint, not a proposals/patches round-trip, on the
same authority the learner-owned authoring slice already uses
(``item_authoring`` — "readers control the prompts they collect" — and the
teach-back transformation ``teach_back.ensure_teach_back_item``). The proposals
convention reviews SYSTEM-proposed *new* content; a remint reclassifies content
the learner has already been served and graded on, adds zero AI authorship, and
is deterministic, so parking it in a review inbox would gate the learner's own
collection behind a review of nothing. The re-runging lane routes through a
request + async job only because it authors NEW content with a model; a
mechanical copy has no generation step to wait on.

Surface identity is the load-bearing invariant: the remint shares the probe's
``canonical_projection.surface_group_id`` group (the ONE independence
primitive), so

* familiarity / repeat-surface discounts see the learner already saw this
  surface (the projection's ``repeat_surface_discount`` binds; no fresh
  independent surface group is minted);
* ``probe_episodes.administered_surface_exclusions`` keeps the whole group
  probe-ineligible forever (the remint can never resurrect the burned
  freshness);
* remediation's independent-surface cold pick treats remint and probe as ONE
  surface, never as an independent verification pair.

Supply interplay: the remint is NOT a diagnostic surface (its mode is
ordinary), so ``diagnostic_surface_supply``'s freshness check — keyed on
``practice_mode == "diagnostic_probe"`` — does not count it. The LO's pending
diagnostic replenishment need stays open; keeping the surface for practice does
not pretend the diagnostic hole was refilled.

Scheduling starts fresh: the remint is a new item id, so its
``practice_item_state`` row is created empty (due_at NULL, no FSRS memory) and
the probe's diagnostic attempt never seeds it; the first ordinary attempt
schedules it normally.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.canonical_projection import surface_group_id
from learnloop.vault.hashes import practice_item_hash
from learnloop.vault.models import LoadedVault, PracticeItem
from learnloop.vault.writer import upsert_practice_item

_LOGGER = logging.getLogger(__name__)

#: Provenance origin stamped on every reminted item (vault/models.Provenance).
REMINT_ORIGIN = "probe_remint"

#: Tag added to every remint; diagnostic-only tags below are stripped.
REMINT_TAG = "probe_remint"

#: Tags that mark the *diagnostic role* of the surface rather than its content.
DIAGNOSTIC_ONLY_TAGS = frozenset({"diagnostic", "diagnostic_probe", "probe", "single_use"})

#: Attempt types that are not by themselves an answering mode: a remint whose
#: kept set contains only these still needs a real ordinary answering type.
_NON_ANSWERING_ATTEMPT_TYPES = frozenset({"dont_know", "skip"})


class ProbeRemintError(ValueError):
    """Invalid remint request, with a stable code for the sidecar boundary."""

    def __init__(self, code: str, message: str, *, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


def remint_practice_mode(item: PracticeItem) -> str:
    """Deterministic ordinary mode from the probe's shape.

    A probe with an ``available`` trace contract demands multi-step written
    work against checkpointed recipes — the constructed/written mode ordinary
    generation uses for exactly that shape (``constructed_response``, the
    dominant mode in the fixture corpora). Anything else is a single written
    answer graded against an expected answer: ``short_answer``. Both modes are
    in ``capability_mapping.MODE_CAPABILITY_DEFAULTS``, and the copied item
    ``capability`` (when authored) still overrides the mode default for
    criterion-target compilation (projection v4).
    """

    trace = item.trace_contract
    if trace is not None and trace.status == "available" and trace.recipes:
        return "constructed_response"
    return "short_answer"


def remint_attempt_types(item: PracticeItem) -> list[str]:
    """The ordinary attempt-type set: the probe's own set minus the diagnostic
    administration type, with a real answering type guaranteed.

    Preserves authored intent: a probe allowing ``open_text`` keeps it (the
    generation convention for constructed items); a probe allowing only
    ``diagnostic_probe``/``dont_know`` gains ``independent_attempt``.
    """

    kept = [value for value in item.attempt_types_allowed if value != "diagnostic_probe"]
    if not any(value not in _NON_ANSWERING_ATTEMPT_TYPES for value in kept):
        kept = ["independent_attempt", *kept]
    return kept


def existing_remint(vault: LoadedVault, source_practice_item_id: str) -> PracticeItem | None:
    """The already-minted remint of this probe, if any (provenance query).

    The vault YAML is the durable lineage record: a remint carries
    ``provenance.origin == "probe_remint"`` plus an ``existing_entity`` source
    ref naming the probe. Enforcing idempotency against the source of truth
    (rather than a derived row) survives ``rebuild-derived-state`` untouched.
    """

    for item in vault.practice_items.values():
        provenance = item.provenance
        if provenance.origin != REMINT_ORIGIN:
            continue
        for ref in provenance.source_refs:
            if ref.ref_type == "existing_entity" and ref.ref_id == source_practice_item_id:
                return item
    return None


def _remint_payload(
    source: PracticeItem,
    *,
    new_id: str,
    attempt_id: str,
    now_iso: str,
) -> dict[str, Any]:
    """Mechanical copy of the probe's content + measurement contract.

    Deliberately NOT copied: ``variant_contract`` (belongs to the re-runging
    lane's authored siblings), ``teach_back_source`` (a different
    transformation's contract), ``laddered_stem`` and the contrast-pair binding
    (``contrast_of``/``differing_component`` — the pair contract stays with the
    probe pair; a third item claiming membership would corrupt the structural
    pair analysis).
    """

    def _dump(model: Any) -> Any:
        return None if model is None else model.model_dump(mode="json", exclude_none=False)

    fingerprint = source.evidence_fingerprint.model_dump(mode="json", exclude_none=False)
    # Shared surface group (kinship discipline, same stamp the re-runging lane
    # uses): whatever field the probe's group resolved through, the remint's
    # ``source_family`` pins the identical group id, so `surface_group_id`
    # agreement holds even for a probe with an empty fingerprint (whose group is
    # the ``item:<id>`` fallback that a new id could never reproduce).
    fingerprint["source_family"] = surface_group_id(source)

    tags = sorted(
        (set(source.tags) - DIAGNOSTIC_ONLY_TAGS) | {REMINT_TAG}
    )

    return {
        "schema_version": source.schema_version,
        "id": new_id,
        "learning_object_id": source.learning_object_id,
        "subjects": list(source.subjects) if source.subjects is not None else None,
        "practice_mode": remint_practice_mode(source),
        "attempt_types_allowed": remint_attempt_types(source),
        "evidence_facets": list(source.evidence_facets),
        "evidence_weights": dict(source.evidence_weights),
        "criterion_facet_weights": {
            criterion: dict(weights)
            for criterion, weights in source.criterion_facet_weights.items()
        },
        "trace_contract": _dump(source.trace_contract),
        "prompt": source.prompt,
        "expected_answer": source.expected_answer,
        "difficulty": source.difficulty,
        "difficulty_source": source.difficulty_source,
        "tags": tags,
        "hints": list(source.hints),
        "hint_policy": _dump(source.hint_policy),
        "retrieval_demand": source.retrieval_demand,
        "transfer_distance": source.transfer_distance,
        "scaffold_level": source.scaffold_level,
        "capability": source.capability,
        "task_features": dict(source.task_features) if source.task_features else None,
        "task_feature_schema": source.task_feature_schema,
        # Familiarity identity: the follow-up/goal-frontier exposure machinery
        # compares `item.surface_family or item.id` against recent attempts, so
        # a probe without an authored family keeps matching through its own id.
        "surface_family": source.surface_family or source.id,
        "evidence_fingerprint": fingerprint,
        "misconception_consistent_answer": source.misconception_consistent_answer,
        "discrimination_profiles": [_dump(profile) for profile in source.discrimination_profiles],
        "error_hunt": _dump(source.error_hunt),
        "repair_targets": list(source.repair_targets),
        "grading_rubric": _dump(source.grading_rubric),
        "status": "active",
        "provenance": {
            "origin": REMINT_ORIGIN,
            "source_refs": [
                {
                    "ref_type": "existing_entity",
                    "ref_id": source.id,
                    "locator": f"administering_attempt:{attempt_id}",
                }
            ],
        },
        "created_at": now_iso,
        "updated_at": now_iso,
    }


def remint_probe_as_practice_item(
    root: Path,
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Mint the ordinary practice-item copy of one administered probe.

    Keyed on the administering attempt (the affordance lives on that attempt's
    feedback), with the server-side guards the door needs anyway: the attempt
    must exist and must be an administration of a ``diagnostic_probe`` item.
    Idempotent per probe: a second request raises ``already_reminted`` with the
    existing item id in ``details`` rather than minting a duplicate.
    """

    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        raise ProbeRemintError("attempt_not_found", f"Unknown attempt {attempt_id!r}.")
    source_id = str(attempt.get("practice_item_id") or "")
    source = vault.practice_items.get(source_id)
    if source is None:
        raise ProbeRemintError(
            "item_not_found",
            f"Practice item {source_id!r} for attempt {attempt_id} is not in the vault.",
        )
    if source.practice_mode != "diagnostic_probe":
        raise ProbeRemintError(
            "not_a_diagnostic_probe",
            f"Attempt {attempt_id} is on {source.id}, which is not a diagnostic probe.",
        )

    existing = existing_remint(vault, source.id)
    if existing is not None:
        raise ProbeRemintError(
            "already_reminted",
            f"{source.id} was already kept as {existing.id}.",
            details={"practice_item_id": existing.id, "status": existing.status},
        )

    now_iso = utc_now_iso(clock)
    new_id = f"pi_remint_{new_ulid().lower()}"
    payload = _remint_payload(source, new_id=new_id, attempt_id=attempt_id, now_iso=now_iso)
    upsert_practice_item(root, payload, clock=clock, loaded_vault=vault)
    minted = PracticeItem.model_validate(payload)
    # Keep the caller's snapshot coherent (idempotency within one snapshot) —
    # the sidecar handler still reloads for derived-state consumers.
    vault.practice_items[new_id] = minted

    # Fresh scheduling state: a brand-new row (no FSRS memory, due_at NULL) so
    # the probe's diagnostic attempt cannot seed the remint; activation matches
    # what the next `state_sync` would derive, just without waiting for it.
    repository.upsert_practice_item_state(
        new_id,
        active=True,
        content_hash=practice_item_hash(minted),
        clock=clock,
    )

    try:
        repository.append_interaction_event(
            kind="probe_reminted",
            origin="learner",
            subject_type="practice_item",
            subject_id=source.id,
            attempt_id=attempt_id,
            payload_json=json.dumps(
                {
                    "created_practice_item_id": new_id,
                    "practice_mode": minted.practice_mode,
                    "surface_group_id": surface_group_id(minted),
                },
                sort_keys=True,
            ),
            occurred_at=now_iso,
            clock=clock,
        )
    except Exception:  # noqa: BLE001 - provenance trail is best-effort
        _LOGGER.warning("failed to record probe_reminted for %s", source.id, exc_info=True)

    try:
        repository.bump_queue_revision(clock=clock)
    except Exception:  # noqa: BLE001 - queue nudging never blocks the mint
        _LOGGER.warning("failed to bump queue revision after remint", exc_info=True)

    return {
        "practice_item_id": new_id,
        "source_practice_item_id": source.id,
        "attempt_id": attempt_id,
        "practice_mode": minted.practice_mode,
        "learning_object_id": source.learning_object_id,
        "created": True,
    }
