"""Learner-owned practice-item authoring: create, edit, retire, split.

Andy Matuschak's reader-control principle ("the mnemonic medium should give
readers control over the prompts they collect"): the learner can always write
their own card, reword one that is off-target, split one that "wants to be two
questions", or retire one they are done with -- immediately, in place, without a
review gate. The proposals/patches machinery reviews SYSTEM-proposed changes;
a learner acting on their own collection is the authority, so these writes go
straight to the vault YAML (the source of truth) and are recorded as
interaction events for provenance.

Retirement keeps every attempt/evidence row (nothing is deleted): the item's
``status`` flips to ``retired``, state_sync deactivates its scheduler state, and
the substrate surface (if one was ever minted) gets a lifecycle ``retire`` event
so the P1 ledger agrees with the vault.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault, PracticeItem
from learnloop.vault.writer import upsert_practice_item

_LOGGER = logging.getLogger(__name__)

EDITABLE_FIELDS = ("prompt", "expected_answer", "hints")


class ItemAuthoringError(ValueError):
    """Invalid learner authoring operation."""


# The §3.7 typed retirement taxonomy (retirement_records.reason CHECK, migration
# 065) -- also exactly the learner vocabulary from the Matuschak talk-aloud notes
# ("too easy", "I knew the prompt, not the concept", ...).
RETIREMENT_REASONS = (
    "too_easy",
    "ambiguous",
    "missing_context",
    "duplicate_surface",
    "wrong_granularity",
    "no_longer_relevant",
    "bad_underlying_explanation",
    "superseded_by_better_activity",
    "should_be_reference_not_memorized",
    "dont_care_enough_to_retain",
    "knew_prompt_not_concept",
)


def _require_item(vault: LoadedVault, practice_item_id: str) -> PracticeItem:
    item = vault.practice_items.get(practice_item_id)
    if item is None:
        raise ItemAuthoringError(f"unknown practice item {practice_item_id!r}")
    return item


def _record(
    repository: Repository,
    *,
    kind: str,
    practice_item_id: str,
    detail: Mapping[str, Any],
    clock: Clock | None,
) -> None:
    """Provenance trail; failure never blocks the learner's edit."""

    try:
        repository.append_interaction_event(
            kind=kind,
            origin="learner",
            subject_type="practice_item",
            subject_id=practice_item_id,
            payload_json=json.dumps(detail, sort_keys=True),
            clock=clock,
        )
    except Exception:  # noqa: BLE001 - provenance trail is best-effort
        _LOGGER.warning("failed to record %s for %s", kind, practice_item_id, exc_info=True)


def author_item(
    root: Path,
    repository: Repository,
    *,
    learning_object_id: str,
    prompt: str,
    expected_answer: str,
    practice_mode: str = "short_answer",
    hints: Sequence[str] | None = None,
    evidence_facets: Sequence[str] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Create a learner-authored card under an existing Learning Object."""

    vault = load_vault(root)
    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        raise ItemAuthoringError(f"unknown learning object {learning_object_id!r}")
    if not prompt.strip():
        raise ItemAuthoringError("prompt must not be empty")
    if not expected_answer.strip():
        raise ItemAuthoringError("expected answer must not be empty")
    now = utc_now_iso(clock)
    item_id = f"pi_learner_{new_ulid().lower()}"
    payload: dict[str, Any] = {
        "id": item_id,
        "learning_object_id": learning_object_id,
        "practice_mode": practice_mode,
        "attempt_types_allowed": ["independent_attempt"],
        "evidence_facets": list(evidence_facets or []),
        "prompt": prompt.strip(),
        "expected_answer": expected_answer.strip(),
        "hints": list(hints or []),
        # A card must always be gradable: give learner-authored cards a plain
        # correctness rubric so grading/assessment never depends on a vault-level
        # default existing for this practice mode.
        "grading_rubric": {
            "max_points": 4,
            "criteria": [
                {"id": "correctness", "points": 4, "description": "Answer matches the expected answer in substance."}
            ],
        },
        "provenance": {"origin": "human"},
        "created_at": now,
        "updated_at": now,
    }
    upsert_practice_item(root, payload, clock=clock)
    _record(
        repository,
        kind="learner_item_authored",
        practice_item_id=item_id,
        detail={"learning_object_id": learning_object_id},
        clock=clock,
    )
    return payload


def edit_item(
    root: Path,
    repository: Repository,
    *,
    practice_item_id: str,
    prompt: str | None = None,
    expected_answer: str | None = None,
    hints: Sequence[str] | None = None,
    reason: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Reword a card in place. Only prompt / expected answer / hints are
    learner-editable; measurement plumbing (facets, weights, rubric) is not."""

    vault = load_vault(root)
    item = _require_item(vault, practice_item_id)
    changes: dict[str, Any] = {}
    if prompt is not None and prompt.strip() and prompt.strip() != item.prompt:
        changes["prompt"] = prompt.strip()
    if (
        expected_answer is not None
        and expected_answer.strip()
        and isinstance(item.expected_answer, str)
        and expected_answer.strip() != item.expected_answer
    ):
        changes["expected_answer"] = expected_answer.strip()
    if hints is not None and list(hints) != list(item.hints):
        changes["hints"] = list(hints)
    if not changes:
        raise ItemAuthoringError("no changes to apply")
    # The writer validates the full payload up front, so start from the item's dump.
    payload = item.model_dump(mode="json", exclude_none=False)
    payload.update(changes)
    payload["updated_at"] = utc_now_iso(clock)
    upsert_practice_item(root, payload, clock=clock)
    _record(
        repository,
        kind="learner_item_edited",
        practice_item_id=practice_item_id,
        detail={"fields": sorted(changes), "reason": reason},
        clock=clock,
    )
    return {"id": practice_item_id, "changed": sorted(changes)}


def retire_item(
    root: Path,
    repository: Repository,
    *,
    practice_item_id: str,
    reason: str,
    note: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Retire a card: never served again, all history kept. ``reason`` is one of
    the typed ``RETIREMENT_REASONS``; ``note`` is optional free text."""

    if reason not in RETIREMENT_REASONS:
        raise ItemAuthoringError(
            f"unknown retirement reason {reason!r}; one of: {', '.join(RETIREMENT_REASONS)}"
        )
    vault = load_vault(root)
    item = _require_item(vault, practice_item_id)
    if item.status == "retired":
        return {"id": practice_item_id, "status": "retired"}
    status_reason = reason if not (note or "").strip() else f"{reason}: {note.strip()}"  # type: ignore[union-attr]
    payload = item.model_dump(mode="json", exclude_none=False)
    payload.update(
        status="retired", status_reason=status_reason, updated_at=utc_now_iso(clock)
    )
    upsert_practice_item(root, payload, clock=clock)
    _record(
        repository,
        kind="learner_item_retired",
        practice_item_id=practice_item_id,
        detail={"reason": reason, "note": (note or "").strip() or None},
        clock=clock,
    )
    _mirror_surface_retirement(vault, repository, item, reason=reason, clock=clock)
    return {"id": practice_item_id, "status": "retired"}


def split_item(
    root: Path,
    repository: Repository,
    *,
    practice_item_id: str,
    parts: Sequence[Mapping[str, str]],
    reason: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """"This feels like it actually wants to be two questions": retire the
    original and author one card per part, provenance-linked to it."""

    if len(parts) < 2:
        raise ItemAuthoringError("a split needs at least two parts")
    vault = load_vault(root)
    original = _require_item(vault, practice_item_id)
    if original.status != "active":
        raise ItemAuthoringError(f"cannot split non-active item {practice_item_id!r}")
    for i, part in enumerate(parts):
        if not str(part.get("prompt", "")).strip() or not str(part.get("expected_answer", "")).strip():
            raise ItemAuthoringError(f"split part {i + 1} needs a prompt and an expected answer")

    created: list[str] = []
    for part in parts:
        row = author_item(
            root,
            repository,
            learning_object_id=original.learning_object_id,
            prompt=str(part["prompt"]),
            expected_answer=str(part["expected_answer"]),
            practice_mode=original.practice_mode,
            evidence_facets=list(original.evidence_facets),
            clock=clock,
        )
        created.append(row["id"])
    retire_item(
        root,
        repository,
        practice_item_id=practice_item_id,
        reason="wrong_granularity",
        note=reason or f"split into {', '.join(created)}",
        clock=clock,
    )
    _record(
        repository,
        kind="learner_item_split",
        practice_item_id=practice_item_id,
        detail={"created": created, "reason": reason},
        clock=clock,
    )
    return {"id": practice_item_id, "created": created}


def _mirror_surface_retirement(
    vault: LoadedVault,
    repository: Repository,
    item: PracticeItem,
    *,
    reason: str,
    clock: Clock | None,
) -> None:
    """Keep the P1 substrate ledger in agreement: if this item ever minted a
    surface, append its lifecycle ``retire``. Fail-safe -- the vault status flip
    above is the authority and already stops all serving paths."""

    try:
        from learnloop.services.activities import resolve_legacy_item, retire_with_reason

        resolved = resolve_legacy_item(vault, repository, item, purpose="practice", clock=clock)
        retire_with_reason(
            repository,
            scope="surface",
            reason=reason,
            provenance="learner_action",
            surface_id=resolved.surface_id,
            clock=clock,
        )
    except Exception:  # noqa: BLE001 - substrate mirror only; vault status already flipped
        _LOGGER.warning("surface retirement mirror failed for %s", item.id, exc_info=True)
