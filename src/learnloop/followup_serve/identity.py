"""The one durable single-use identity of a generated probe (spec §4.2).

A generated probe is served once and never again, and it never becomes a practice
item. One identity and retirement rule governs every door: not a naming convention, and
not the generic ``codex_proposal`` origin.

* **Reserved** for its workflow until served: a selected id or a precommitted
  presentation is not exclusive across devices, so the claim is what decides.
* **Burned at first serve** by an atomic claim keyed to the item's revision, the surface
  and the presentation. The claim blocks any new administration and keeps that
  presentation's one valid submission; the presentation itself stays open, since ending
  it would make the submission fail. Generation, queue listing, plan prefetch and
  presentation commit never burn. A response lost after the server burned counts as
  burned: a server cannot prove pixels were displayed, so this errs toward never repeating.
* **Retired while unused** if its hypotheses close first, or the learner takes
  *Continue without it*.
* **Kept for history**: the item stays in the vault so attempts and replays resolve.

The ledger is append-only and read by replay and state sync; it persists after a rollback.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import hashlib
import json
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores import followup_serve as store

#: Why a door refuses a generated probe. Serving-exclusion code and sidecar error alike.
GENERATED_PROBE_CLOSED = "generated_probe_closed"
GENERATED_PROBE_RESERVED = "generated_probe_reserved"

SERVED = "served"
RETIRED = "retired"


def item_revision(payload: Mapping[str, Any]) -> str:
    """The content revision a claim is keyed to: the question as authored."""

    canonical = json.dumps(
        {key: payload.get(key) for key in ("prompt", "expected_answer", "grading_rubric")},
        sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _present(connection: Any) -> bool:
    return store.present(connection, "generated_probe_items")


def register(
    repository: Repository,
    *,
    practice_item_id: str,
    revision: str,
    source: str,
    workflow_id: str | None = None,
    probe_episode_id: str | None = None,
    clock: Clock | None = None,
) -> bool:
    """Give an item the identity, once, in the transaction that writes it."""

    with repository.atomic(), repository.connection() as connection:
        return store.insert_generated_probe(
            connection, practice_item_id=practice_item_id, item_revision=revision, source=source,
            workflow_id=workflow_id, probe_episode_id=probe_episode_id, at=utc_now_iso(clock),
        )


def is_generated_probe(repository: Repository, practice_item_id: str) -> bool:
    if not practice_item_id:
        return False
    with repository.connection() as connection:
        return _present(connection) and store.generated_probe(connection, practice_item_id) is not None


def generated_probe_ids(repository: Repository) -> frozenset[str]:
    with repository.connection() as connection:
        return store.generated_probe_ids(connection) if _present(connection) else frozenset()


def closed_probe_ids(repository: Repository) -> frozenset[str]:
    """Every generated probe with a burn or a retirement."""

    with repository.connection() as connection:
        return store.closed_generated_probe_ids(connection) if _present(connection) else frozenset()


@dataclass(frozen=True)
class Claim:
    """A first-serve claim's verdict."""

    granted: bool
    #: This serve opened the one administration (False: a re-open of it).
    first: bool
    reason: str | None = None
    burn: Mapping[str, Any] | None = None


def claim_serve(
    repository: Repository,
    practice_item_id: str,
    *,
    surface: str,
    presentation_id: str | None,
    workflow_id: str | None = None,
    reason: str = "first_serve",
    clock: Clock | None = None,
) -> Claim:
    """The atomic first-serve burn; an item with no identity needs no claim.

    A re-open by the same surface and presentation is the same administration (a
    remount, a restored session), still with its one valid submission. Anything else
    after a burn or a retirement is refused.
    """

    with repository.atomic(), repository.connection() as connection:
        if not _present(connection):
            return Claim(True, False)
        identity = store.generated_probe(connection, practice_item_id)
        if identity is None:
            return Claim(True, False)
        burns = store.burns_for_item(connection, practice_item_id)
        if RETIRED in burns and SERVED not in burns:
            return Claim(False, False, GENERATED_PROBE_CLOSED, burns[RETIRED])
        if SERVED in burns:
            burn = burns[SERVED]
            same = burn.get("surface") == surface and burn.get("presentation_id") == presentation_id
            if same and RETIRED not in burns:
                return Claim(True, False, None, burn)
            return Claim(False, False, GENERATED_PROBE_CLOSED, burn)
        store.insert_burn(
            connection, practice_item_id=practice_item_id, kind=SERVED, item_revision=str(identity["item_revision"]),
            reason=reason, surface=surface, presentation_id=presentation_id,
            workflow_id=workflow_id or identity.get("workflow_id"), at=utc_now_iso(clock),
        )
        return Claim(True, True, None, store.burns_for_item(connection, practice_item_id)[SERVED])


def retire(
    repository: Repository,
    practice_item_id: str,
    *,
    reason: str,
    workflow_id: str | None = None,
    clock: Clock | None = None,
) -> bool:
    """Close a generated probe for any further administration, and keep it for history.

    A served one keeps its open presentation's one submission until that presentation
    ends; the state row goes inactive so no door lists it.
    """

    with repository.atomic(), repository.connection() as connection:
        if not _present(connection):
            return False
        identity = store.generated_probe(connection, practice_item_id)
        if identity is None:
            return False
        inserted = store.insert_burn(
            connection, practice_item_id=practice_item_id, kind=RETIRED, item_revision=str(identity["item_revision"]),
            reason=reason, workflow_id=workflow_id or identity.get("workflow_id"), at=utc_now_iso(clock),
        )
    repository.set_practice_item_active(practice_item_id, active=False, clock=clock)
    return inserted


def door_refusal(repository: Repository, practice_item_id: str, *, workflow_id: str | None = None) -> str | None:
    """Why a door may not open this generated probe now, or None. Reads only, never burns.

    ``workflow_id`` is the door's own claim to it: a probe stays reserved for its
    workflow until it is served.
    """

    with repository.connection() as connection:
        if not _present(connection):
            return None
        identity = store.generated_probe(connection, practice_item_id)
        if identity is None:
            return None
        burns = store.burns_for_item(connection, practice_item_id)
    if burns:
        return GENERATED_PROBE_CLOSED
    owner = identity.get("workflow_id")
    if owner is not None and workflow_id != owner:
        return GENERATED_PROBE_RESERVED
    return None


def exclude_ids(repository: Repository, item_ids: Iterable[str]) -> set[str]:
    """The ones in ``item_ids`` that carry the identity."""

    known = generated_probe_ids(repository)
    return {str(value) for value in item_ids if str(value) in known}


def replay_inactive_ids(repository: Repository) -> frozenset[str]:
    """Rebuild replay: an item the ledger closed stays closed, attempt or no attempt."""

    return closed_probe_ids(repository)


__all__ = [
    "Claim", "GENERATED_PROBE_CLOSED", "GENERATED_PROBE_RESERVED", "RETIRED", "SERVED", "claim_serve",
    "closed_probe_ids", "door_refusal", "exclude_ids", "generated_probe_ids", "is_generated_probe", "item_revision",
    "register", "replay_inactive_ids", "retire",
]
