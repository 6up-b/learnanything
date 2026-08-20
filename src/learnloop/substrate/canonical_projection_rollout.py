"""Startup ownership for the canonical projection-version boundary.

The canonical facet tables are a deterministic cache, so desktop startup
refreshes them from the immutable observation ledger.  A projection semantics
change can alter that cache without adding learner evidence; that refresh must
therefore leave one ``derived_state_rebuilds`` marker.  Keeping the marker next
to the startup refresh prevents the cache write and its learner-visible
recalibration contract from drifting apart.
"""

from __future__ import annotations

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.learner.assessment_contracts import CANONICAL_STATE_VERSIONS
from learnloop.substrate.canonical_projection import (
    CANONICAL_PROJECTION_VERSION,
    project_canonical_facet_state,
)
from learnloop.vault.models import LoadedVault


def refresh_canonical_projection_on_startup(
    vault: LoadedVault,
    repository: Repository,
    *,
    clock: Clock | None = None,
) -> str | None:
    """Refresh the cache and stamp a changed projection baseline exactly once.

    Fresh vaults receive a zero-replay baseline marker.  It is deliberately not
    a learner-visible recalibration, but it prevents the first later restart
    (after the learner has practised under the current projection) from being
    misreported as a version cutover.  Older vaults with observations and no
    current baseline get one marker with the number of observations actually
    folded; subsequent starts still verify the cache but add no marker.

    The marker is written *after* projection succeeds.  If the process stops in
    between, the next startup repeats the idempotent projection and then stamps
    it; it can never claim a rebuild that did not complete.
    """

    algorithm_version = vault.config.algorithms.algorithm_version
    if algorithm_version not in CANONICAL_STATE_VERSIONS:
        return None

    # Startup is allowed to have multiple native callers (initialization,
    # watcher-driven reload, reconnect).  Serialize the check/project/stamp
    # sequence across processes so two simultaneous initializations cannot
    # narrate the same rollout twice.
    from learnloop.ops.vault_lock import vault_mutation_lock

    with vault_mutation_lock(vault.root, purpose="canonical_projection_startup"):
        baseline = repository.latest_canonical_projection_rebuild()
        current = bool(
            baseline is not None
            and baseline.get("algorithm_version") == algorithm_version
            and baseline.get("canonical_projection_version")
            == CANONICAL_PROJECTION_VERSION
        )

        project_canonical_facet_state(vault, repository, clock=clock)
        if current:
            return None

        learning_object_ids = repository.learning_object_ids_with_attempts()
        replayed_attempts = repository.attempt_count()

        # Coverage is an independent displayed-estimate boundary.  Stamp its
        # current content-addressed value on this full projection marker so the
        # review feed never attributes a later coverage change to this rollout.
        from learnloop.learner.facet_diagnostics import (
            coverage_denominator_version,
        )

        return repository.record_derived_state_rebuild(
            scope="canonical_projection_startup",
            learning_object_ids=learning_object_ids,
            algorithm_version=algorithm_version,
            rebuilt_learning_objects=len(learning_object_ids),
            replayed_attempts=replayed_attempts,
            canonical_projection_version=CANONICAL_PROJECTION_VERSION,
            coverage_denominator_version=coverage_denominator_version(
                vault, repository
            ),
            clock=clock,
        )
