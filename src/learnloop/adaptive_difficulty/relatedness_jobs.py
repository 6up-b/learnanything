"""The relatedness proposal's re-proposals in the background (spec_adaptive_difficulty_v1 §5.10 "When").

After the owner's one-time backfill per subject (``learnloop ad relatedness``,
dry-run first, then ``--adopt``), a subject is re-proposed whenever its content
changes: an LO or facet added, retitled or redescribed, a relation or
prerequisite edited, a new item revision. The sidecar's reload (and the file
watcher's refresh) schedules it here, off the request path, on the vault's
build registry, one subject per job and at most :data:`SUBJECTS_PER_TRIGGER`
subjects a trigger (the bounded-queue pattern of AD1's preparation). An
unchanged input hash is never re-asked. A re-proposal reaches only what does
not exist yet (§5.10 "As of"); adopting it for what exists is a new coupling
version through the playbook. Nothing runs below the tag, with
``learned_coupling`` off, for a subject with no adopted version, or with
``LEARNLOOP_AD_MODELS=off`` and no injected client.
"""

from __future__ import annotations

from learnloop.adaptive_difficulty.operation import entry

import logging
from collections.abc import Callable
from contextlib import closing
from pathlib import Path
from typing import Any

from learnloop.db.connection import connect
from learnloop.db.stores import ad_serving as store

from learnloop.adaptive_difficulty import relatedness as R
from learnloop.adaptive_difficulty import spend as ad_spend
from learnloop.adaptive_difficulty.successor import coupling_on

LOG = logging.getLogger(__name__)

SUBJECTS_PER_TRIGGER = 2


@entry
def stale_subjects(vault: Any, repository: Any) -> list[str]:
    """Subjects with an adopted coupling version and a unit (an LO or an item revision) whose
    fingerprint changed, or that is new, since its latest run."""

    from learnloop.adaptive_difficulty.material_view import material_view

    # Exactly as ``propose_subject`` reads the runs (Codex verify F45, fix round 14): only a run in
    # force answers for a unit, so a run whose recorded context is protected now schedules its units
    # again. With the held-out predicate unavailable nothing is stale (nothing may be proposed).
    view = material_view(vault, repository)
    if not view.available:
        return []
    stale = []
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        adopted = {row["subject_id"] for row in store.coupling_versions(connection)}
        runs = store.relatedness_runs(connection)
        for subject in R.subjects(vault):
            if subject not in adopted:
                continue
            inputs = R.subject_inputs(vault, repository, subject, protected=view)
            current = inputs["unit_hashes"].get(R.PROTECTION_UNIT)
            own = [run for run in runs if run["subject_id"] == subject]
            live = {run["id"] for run in own if R.run_in_force(view, connection, run, current)}
            if R.touched_units(inputs, own, in_force=lambda run, live=live: run["id"] in live):
                stale.append(subject)
    return stale


def schedule_reproposals(vault: Any, sqlite_path: Any, *, client: Any = None, builds: Any = None,
                         live_vault: Callable[[], Any] | None = None) -> list[Any]:
    """Re-propose the stale subjects in the background; returns the threads started. Never raises."""

    try:
        if not coupling_on(vault.config):
            return []
        if ad_spend.models_off() and client is None:
            return []
        from learnloop.adaptive_difficulty.background import _launch
        from learnloop.db.repositories import Repository

        repository = Repository.attach(Path(sqlite_path))
        threads = []
        for subject in stale_subjects(vault, repository)[:SUBJECTS_PER_TRIGGER]:
            def job(fence: Any, subject: str = subject) -> None:
                worker_repository = Repository.attach(Path(sqlite_path))
                outcome = R.propose_subject(vault, worker_repository, subject, client=client, fence=fence,
                                            live_vault=live_vault)
                LOG.info("AD relatedness re-proposal for %s: %s", subject, outcome.status)

            thread = _launch(sqlite_path, f"relatedness:{subject}", job, builds=builds,
                             name=f"learnloop-ad-relatedness-{subject}")
            if thread is not None:
                threads.append(thread)
        return threads
    except Exception:  # noqa: BLE001 - a re-proposal never blocks a reload
        LOG.warning("AD relatedness re-proposals not scheduled", exc_info=True)
        return []


__all__ = ["SUBJECTS_PER_TRIGGER", "schedule_reproposals", "stale_subjects"]
