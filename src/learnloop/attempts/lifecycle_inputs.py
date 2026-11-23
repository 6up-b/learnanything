"""Which required facet set a grade application reads (mvp-0.66, retired items replay at the right point in history).

Below the tag every application reads today's item lifecycle (``required_facets``), as the predecessor did. At the
tag:

* a live application reads the set once and records it with its attempt (``captured_at_application``);
* a replay or a regrade reads the recorded set back. An attempt applied at the tag that has none is an integrity
  failure (:class:`LifecycleInputsMissing`), never a reason to read today's lifecycle;
* an attempt with no row that was not applied at the tag (one applied before the upgrade, or written outside the
  attempt pipeline) is read the predecessor's way, from the lifecycle as it stands at the replay. The upgrade
  observes exactly that reading inside :func:`reconstructing_legacy_lifecycle_inputs` and freezes it
  (``legacy_reconstructed``), so after it later lifecycle changes reach no earlier attempt.
"""

from __future__ import annotations

from collections.abc import Collection, Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from learnloop.algorithm_versions import LIFECYCLE_INPUTS_VERSIONS, lifecycle_inputs_on
from learnloop.db.attempt_lifecycle_inputs import BASIS_CAPTURED, BASIS_LEGACY_RECONSTRUCTED, LifecycleInputs
from learnloop.db.repositories import Repository
from learnloop.learner.facet_diagnostics import required_facets
from learnloop.vault.models import LoadedVault

# The upgrade's observation pass: attempt id -> the predecessor's reading at that attempt. A context variable rather
# than a parameter because the reading is taken deep inside the whole-vault rebuild the observation runs, which has no
# other reason to carry it.
_RECONSTRUCTING: ContextVar[dict[str, LifecycleInputs] | None] = ContextVar("lifecycle_inputs_reconstructing", default=None)


class LifecycleInputsMissing(RuntimeError):
    """An attempt applied at the tag has no recorded lifecycle inputs: its replay cannot be told what it read."""

    def __init__(self, attempt_id: str):
        super().__init__(
            f"attempt {attempt_id} was applied with its lifecycle inputs recorded, and they are missing: replay "
            "refuses to read today's item lifecycle in their place"
        )
        self.attempt_id = attempt_id


@contextmanager
def reconstructing_legacy_lifecycle_inputs() -> Iterator[dict[str, LifecycleInputs]]:
    """Collect, while the block runs, the predecessor's reading for every replayed attempt that has no row (the first
    reading of each attempt; a later pass of the same rebuild reuses it). Nothing is written: the caller records them."""

    collected: dict[str, LifecycleInputs] = {}
    token = _RECONSTRUCTING.set(collected)
    try:
        yield collected
    finally:
        _RECONSTRUCTING.reset(token)


def recorded_for_replay(vault: LoadedVault, repository: Repository, attempt_id: str) -> LifecycleInputs | None:
    """The set recorded for a replayed or regraded attempt (None below the tag, or where none was recorded)."""

    if not lifecycle_inputs_on(vault.config):
        return None
    recorded = repository.attempt_lifecycle_inputs(attempt_id)
    if recorded is None and repository.attempt_applied_at_version(attempt_id) in LIFECYCLE_INPUTS_VERSIONS:
        raise LifecycleInputsMissing(attempt_id)
    return recorded


def application_required_facets(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    learning_object_id: str,
    replay: bool,
    recorded: LifecycleInputs | None,
) -> tuple[Collection[str], bool, LifecycleInputs | None]:
    """The required facets a grade application counts, whether its coverage sums them in canonical (sorted) order,
    and the new capture its attempt records (None on replay, on a regrade and below the tag)."""

    if not lifecycle_inputs_on(vault.config):
        return required_facets(vault, learning_object_id, repository), False, None
    applied, new_capture = application_lifecycle_inputs(
        vault, repository, attempt_id=attempt_id, learning_object_id=learning_object_id, replay=replay,
        recorded=recorded,
    )
    return applied.required_facets, True, applied if new_capture else None


def application_lifecycle_inputs(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    learning_object_id: str,
    replay: bool,
    recorded: LifecycleInputs | None,
) -> tuple[LifecycleInputs, bool]:
    """At the tag: the set this application reads, and whether it is a new capture its attempt must record."""

    if not replay:
        return LifecycleInputs.of(
            learning_object_id, required_facets(vault, learning_object_id, repository), basis=BASIS_CAPTURED
        ), True
    if recorded is not None and recorded.learning_object_id == learning_object_id:
        return recorded, False
    reconstructing = _RECONSTRUCTING.get()
    if recorded is None and reconstructing is not None:
        observed = reconstructing.get(attempt_id)
        if observed is not None and observed.learning_object_id == learning_object_id:
            return observed, False
    reading = LifecycleInputs.of(
        learning_object_id, required_facets(vault, learning_object_id, repository), basis=BASIS_LEGACY_RECONSTRUCTED
    )
    if recorded is None and reconstructing is not None:
        reconstructing.setdefault(attempt_id, reading)
    return reading, False


__all__ = [
    "LifecycleInputsMissing",
    "application_lifecycle_inputs",
    "application_required_facets",
    "reconstructing_legacy_lifecycle_inputs",
    "recorded_for_replay",
]
