"""Which seed a learning object's mastery starts from (mvp-0.67, the mastery seed a topic started from is recorded and
replayed).

Below the tag nothing is recorded: replay seeds a practised learning object from the claims made before its first
attempt and an attempt-free one from the claims in force at rebuild time, as the predecessor did. At the tag:

* the writer that first persists a learning object's mastery records every claim its seed considered, in the same
  transaction (``captured_at_materialization``): vault sync (:func:`materialize_mastery`), an attempt applied to a
  learning object without a row (:func:`attempt_seed_capture`) and a live re-anchoring claim on one
  (``mastery._reanchor_in_transaction``);
* replay and the attempt-free rebuild seed from the record and then apply only the re-anchoring claims made after it,
  so a claim that does not re-anchor (a changed starting level, a manual claim) reaches no row materialized before it,
  live or rebuilt;
* a learning object without a record is seeded the predecessor's way. The upgrade observes exactly that seeding inside
  :func:`reconstructing_legacy_mastery_seeds` and freezes it (``legacy_reconstructed``).

The seed itself stays pure (``mastery.seed_for_learning_object``): asking for a hypothetical prior records nothing.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from learnloop.algorithm_versions import mastery_seed_on
from learnloop.db.mastery_seed_inputs import BASIS_LEGACY_RECONSTRUCTED, MasterySeedInputs
from learnloop.db.repositories import Repository
from learnloop.learner.mastery import (
    MasterySeed,
    live_seed_inputs,
    recorded_seed_state,
    seed_for_learning_object,
)
from learnloop.vault.models import LoadedVault

# The upgrade's observation pass: learning object id -> the seed the predecessor's rebuild gave it. A context variable
# rather than a parameter because the seed is taken deep inside the whole-vault rebuild the observation runs (the claim
# stream, the attempt path, the attempt-free rows), which has no other reason to carry it.
_RECONSTRUCTING: ContextVar[dict[str, MasterySeedInputs] | None] = ContextVar("mastery_seed_reconstructing", default=None)


@contextmanager
def reconstructing_legacy_mastery_seeds() -> Iterator[dict[str, MasterySeedInputs]]:
    """Collect, while the block runs, the seed the rebuild gives every learning object without a record (the first
    seed of each). Nothing is written: the caller records them."""

    collected: dict[str, MasterySeedInputs] = {}
    token = _RECONSTRUCTING.set(collected)
    try:
        yield collected
    finally:
        _RECONSTRUCTING.reset(token)


def note_rebuilt_seed(learning_object_id: str, seed: MasterySeed) -> bool:
    """Hand a rebuild's seed of an unrecorded learning object to the observation pass; whether one is running."""

    reconstructing = _RECONSTRUCTING.get()
    if reconstructing is None:
        return False
    reconstructing.setdefault(learning_object_id, MasterySeedInputs.of(
        learning_object_id, seed.considered, seed.in_force_ids, seed.selected_claim_id,
        basis=BASIS_LEGACY_RECONSTRUCTED, materialized_at=None,
    ))
    return True


def recorded_seed_for_replay(vault: LoadedVault, repository: Repository, learning_object_id: str) -> MasterySeedInputs | None:
    """The seed recorded for a replayed learning object (None below the tag, or where none was recorded)."""

    if not mastery_seed_on(vault.config):
        return None
    return repository.mastery_seed_inputs(learning_object_id)


def materialize_mastery(vault: LoadedVault, repository: Repository, learning_object_id: str, now_iso: str) -> bool:
    """Vault sync's first persistence of a learning object's mastery at the tag; whether it wrote a row.

    One transaction re-reads the row (another process may have materialized it since the caller's snapshot), seeds,
    writes the row and records the seed, so a death between them leaves neither. A record already standing (its row
    lost: nothing live deletes one outside a rebuild's own transaction) is the seed, not a new reading."""

    with repository.atomic():
        if repository.mastery_state(learning_object_id) is not None:
            return False
        recorded = repository.mastery_seed_inputs(learning_object_id)
        if recorded is not None:
            repository.upsert_mastery_state(recorded_seed_state(vault, recorded, now_iso))
            return True
        seed = seed_for_learning_object(vault, repository, learning_object_id, now_iso)
        repository.upsert_mastery_state(seed.state)
        inputs = live_seed_inputs(vault, learning_object_id, seed, materialized_at=now_iso)
        if inputs is not None:
            repository.record_mastery_seed_inputs(inputs, recorded_at=now_iso)
        return True


def attempt_seed_capture(
    vault: LoadedVault, learning_object_id: str, seed: MasterySeed | None, *, replay: bool, now_iso: str
) -> MasterySeedInputs | None:
    """The seed record an attempt's own write carries: the seed its prior was built from when its learning object had
    no row (a live application at the tag); None otherwise. On replay the seed goes to the observation pass, if one is
    running, and nothing is recorded."""

    if seed is None:
        return None
    if replay:
        note_rebuilt_seed(learning_object_id, seed)
        return None
    return live_seed_inputs(vault, learning_object_id, seed, materialized_at=now_iso)


__all__ = [
    "attempt_seed_capture",
    "materialize_mastery",
    "note_rebuilt_seed",
    "reconstructing_legacy_mastery_seeds",
    "recorded_seed_for_replay",
]
