"""Seed the canonical facet belief a head (canonical-state) vault reads.

From ``mvp-0.7`` (KM2b) a facet's recall belief is the vault-wide canonical
cache (``facet_recall_state``, keyed on facet, capability and item scope), and
every per-LO reader folds it through ``learner.facet_state_reader``. Tests of a
reader (goal projection, measurement labels, the scheduler's facet boundary...)
used to seed the legacy per-LO table directly; on a head vault that table is
never read and the KM2b guard refuses the write.

:func:`seed_canonical_facet_recall` is the head's counterpart. It writes one
cell through the projection's own writer (``Repository.replace_canonical_facet_state``),
keeping every other cell and every capability row as stored, so it is exactly
what ``project_canonical_facet_state`` would leave for an observation history
with that alpha, beta and mass. Like the legacy seed it stands in for, it is a
derived cache: anything that re-projects (an attempt, a vault open through the
app, a rebuild) rewrites it from the observation ledger, so a test seeds after
such a step, never before it.
"""

from __future__ import annotations

from dataclasses import asdict

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.db.repositories import Repository

from tests.helpers import NOW_ISO

#: The basic vault's one item (`short_answer` on facet `recall`) compiles to
#: this capability, so its observations land in this canonical cell.
BASIC_ITEM_CAPABILITY = "schema_interpretation"


def seed_canonical_facet_recall(
    repository: Repository,
    *,
    facet_id: str,
    mean: float,
    mass: float = 2.0,
    capability: str = BASIC_ITEM_CAPABILITY,
    practice_item_id: str | None = None,
    pseudo_count: float = 10.0,
    raw_mass: float | None = None,
    last_observed_at: str = "2026-05-16T12:00:00Z",
    last_error_at: str | None = None,
    consecutive_failures: int = 0,
    algorithm_version: str = LATEST_ALGORITHM_VERSION,
) -> None:
    """Make one canonical recall cell hold ``mean`` with ``mass`` independent evidence.

    ``alpha = mean * pseudo_count`` and ``beta = (1 - mean) * pseudo_count``, as
    the legacy seeds wrote them; a facet observed at one capability folds to
    exactly this cell (``facet_state_reader._fold`` is the identity there).
    """

    alpha = mean * pseudo_count
    beta = (1.0 - mean) * pseudo_count
    total = alpha + beta
    cell = {
        "facet_id": facet_id,
        "capability_key": capability,
        "practice_item_id": practice_item_id,
        "recall_alpha": alpha,
        "recall_beta": beta,
        "recall_mean": alpha / total,
        "recall_variance": alpha * beta / (total**2 * (total + 1.0)),
        "independent_evidence_mass": mass,
        "raw_coverage_mass": mass if raw_mass is None else raw_mass,
        "last_observed_at": last_observed_at,
        "last_error_at": last_error_at,
        "consecutive_failures": consecutive_failures,
        "created_at": NOW_ISO,
    }
    key = (facet_id, capability, practice_item_id)
    kept = [
        {
            "facet_id": row.facet_id,
            "capability_key": row.capability_key,
            "practice_item_id": row.practice_item_id,
            "recall_alpha": row.recall_alpha,
            "recall_beta": row.recall_beta,
            "recall_mean": row.recall_mean,
            "recall_variance": row.recall_variance,
            "independent_evidence_mass": row.independent_evidence_mass,
            "raw_coverage_mass": row.raw_coverage_mass,
            "last_observed_at": row.last_observed_at,
            "last_error_at": row.last_error_at,
            "consecutive_failures": row.consecutive_failures,
            "created_at": row.created_at,
        }
        for row in repository.canonical_facet_recall_states()
        if (row.facet_id, row.capability_key, row.practice_item_id) != key
    ]
    capability_rows = []
    for row in repository.facet_capability_evidence_all():
        data = asdict(row)
        capability_rows.append(data)
    repository.replace_canonical_facet_state(
        recall_rows=[*kept, cell],
        capability_rows=capability_rows,
        algorithm_version=algorithm_version,
    )
