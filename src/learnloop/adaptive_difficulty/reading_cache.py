"""Router speed stage 2, item 1: AD's section → LO map held within ONE objective job (no successor).

AD's reading map (:class:`~learnloop.adaptive_difficulty.reading.VaultReadingMap`) maps a completed section, a viewed
span or a question's anchors to the LOs whose provenance cites them (``section_map.learning_objects_for_section_in_ir``
through ``MaterialView.document_ir``). The map was built afresh at every call of the combiner's join (RO2's opportunity
resolve, twice a job), of the sweep and of the rollouts' reading action, and each section's mapping re-read the
reading's run, revision and source and walked every LO's references over the section's blocks: the landing's profile
measured it at 11 ms a call, 3,794 calls in a week on the owner's linear_algebra copy.

**Landing ruling R1** (structural): the held map lives only within one objective job's ``decision_reads`` scope
(:func:`job_scope`, which ``objective_inputs.decision_reads`` opens), as a **snapshot as of that job's first read**, and
is discarded when the job ends. Nothing is held across jobs, or across walks of different jobs, so a vault or database
edit is always seen by the next decision; outside a job the map is main's (its per-map memo alone). Within the job:

* a reading's IR is loaded once, at the job's first read of it (through ``MaterialView.document_ir``, the reading
  chokepoint), and every section and span mapping the job computes is computed over that IR, so held hits and
  misses give the snapshot's mapping alike (an IR rewritten mid-job is read by the next job);
* each section's LOs (per vault object), each reading's span → section map and the view's section → spans map are
  held, keyed by the database, the operation's **protection epoch** (``MaterialView.epoch``), the vault object (held
  weakly) and the reading;
* every memo return (these held values and the map's and the view's own memos) is preceded by the withheld rule,
  asked of the caller's view fresh at that call; a different epoch within the job (a protection change: an exam
  reservation, a held-out span, a withheld reading) drops everything the job held for that database.

A vault edit landing in the middle of one ~1 s job is read as of the job's snapshot, which the ruling accepts (the
decision is as of its inputs). A mapping that failed (no IR, an unreadable extraction, a guard refusal) is not held.
Behind ``[router_objective] held_reading_map`` (:func:`held_on`; Codex review F2): off, nothing here is read. Pure
in-process memory, bounded by the job's own readings; nothing is written.
"""

from __future__ import annotations

from collections.abc import Hashable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
import threading
from typing import Any
import weakref


def held_on(config: Any) -> bool:
    """``[router_objective] held_reading_map`` at the follow-up batch's tag with the objective serving (router speed
    stage 2's Codex review F2): the map's values are the same either way, but held they cost less, so the objective
    job's input builds finish sooner and a deadline-bound refinement completes more draws; it is versioned as RO6's
    generator payload and the prefetch key version it. Off (or below the tag): main e9ceaf8d44's map, which reads
    nothing of this module."""

    from learnloop.router_objective_switches import followup_on

    return config is not None and followup_on(config, "held_reading_map")


class JobHold:
    """One objective job's held reading map (:func:`job_scope`): values per database, each under the protection epoch
    it was computed at. The job's threads share it (the job copies its context), hence the lock; values are immutable
    (tuples, read-only mappings, the IR the chokepoint handed out, which the mapping only reads)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._values: dict[Hashable, tuple[Any, Any]] = {}
        self._epochs: dict[str, str] = {}

    def at_epoch(self, database: str, epoch: str) -> None:
        """Landing ruling R1: a protection change within the job (another epoch for this database than the one the
        job holds values at) drops everything the job held for the database."""

        with self._lock:
            if self._epochs.get(database) == epoch:
                return
            if database in self._epochs:
                for key in [key for key in self._values if key[0] == database]:
                    del self._values[key]
            self._epochs[database] = epoch

    def get(self, key: Hashable, vault: Any) -> Any:
        with self._lock:
            entry = self._values.get(key)
        if entry is None:
            return None
        owner, value = entry
        raw_vault = _owner(vault)
        if (owner is None) != (raw_vault is None) or (owner is not None and owner() is not raw_vault):
            return None  # another vault object at a reused address: never this one's
        return value

    def put(self, key: Hashable, vault: Any, value: Any) -> None:
        raw_vault = _owner(vault)
        try:
            owner = None if raw_vault is None else weakref.ref(raw_vault)
        except TypeError:  # an object that cannot be referenced weakly is never held
            return
        with self._lock:
            if self._epochs.get(key[0]) == key[1]:  # dropped by a protection change meanwhile: not held
                self._values[key] = (owner, value)

    def discard(self) -> None:
        with self._lock:
            self._values.clear()
            self._epochs.clear()


#: The objective job's hold (:func:`job_scope`); None outside one, where nothing is held across maps.
_JOB: ContextVar[JobHold | None] = ContextVar("learnloop_ad_reading_job_hold", default=None)


@contextmanager
def job_scope() -> Iterator[None]:
    """One objective job's hold (landing ruling R1), opened by ``objective_inputs.decision_reads``: what AD's reading
    map holds inside lives until the scope ends and is discarded then. A scope inside another is the outer one."""

    if _JOB.get() is not None:
        yield
        return
    hold = JobHold()
    token = _JOB.set(hold)
    try:
        yield
    finally:
        _JOB.reset(token)
        hold.discard()


def _owner(vault: Any) -> Any:
    return None if vault is None else getattr(vault, "_ad_raw_vault", vault)


class HeldReads:
    """What one view may read of the job's hold: keys carry the database, the view's epoch and, for a vault-derived
    value, the raw vault object (with whether the map reads the operation's projection of it)."""

    def __init__(self, hold: JobHold, database: str, epoch: str) -> None:
        self._hold = hold
        self._database = database
        self._epoch = epoch

    def _key(self, vault: Any, parts: tuple[Any, ...]) -> tuple[Any, ...]:
        owner = _owner(vault)
        return (self._database, self._epoch, None if owner is None else id(owner),
                vault is not None and hasattr(vault, "_ad_raw_vault"), *parts)

    def get(self, vault: Any, *parts: Any) -> Any:
        """The value the job holds for ``parts`` (and this vault object; None: a value no vault is read for)."""

        return self._hold.get(self._key(vault, parts), vault)

    def put(self, vault: Any, value: Any, *parts: Any) -> None:
        self._hold.put(self._key(vault, parts), vault, value)

    def document_ir(self, view: Any, repository: Any, extraction_id: str) -> Any:
        """The reading's IR as of the job's first read of it (``view.document_ir``, the chokepoint), the withheld rule
        asked of ``view`` fresh before a held IR is returned; None (never held) for a withheld or unreadable one."""

        if not getattr(view, "available", False) or view.reading_withheld(extraction_id):
            return None
        found = self.get(None, "ir", str(extraction_id))
        if found is None:
            found = view.document_ir(repository, extraction_id)
            if found is not None:
                self.put(None, found, "ir", str(extraction_id))
        return found


def job_hold(view: Any, repository: Any) -> HeldReads | None:
    """The objective job's hold as ``view`` reads it, or None: outside a job, while the view is unavailable or has no
    epoch, or with no database to key by. The view's epoch is checked against the job's for the database at every
    call (a different one drops what the job held: landing ruling R1)."""

    hold = _JOB.get()
    if hold is None or not getattr(view, "available", False):
        return None
    epoch = view.epoch
    raw_repository = getattr(repository, "_ad_raw_repository", repository)
    path = getattr(raw_repository, "sqlite_path", None)
    if epoch is None or path is None:
        return None
    database = str(Path(path).resolve())
    hold.at_epoch(database, str(epoch))
    return HeldReads(hold, database, str(epoch))


__all__ = ["HeldReads", "JobHold", "held_on", "job_hold", "job_scope"]
