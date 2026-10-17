"""Grading epochs: one definition of which grade of an attempt is current.

A grading epoch is one grading of one attempt: the ``grading_evidence`` rows a
single writer (a first grade, a regrade, an adjudication) wrote together. Its
key is its ``grading_revision`` when the rows carry one (``revision:N``), else
the write stamp its rows share (``legacy:<created_at>``), as every reader of
the ledger has grouped them.

**The sequence.** From the regrade-contract successor (``mvp-0.26``) every
writer of a new epoch stamps the attempt's next revision
(:func:`next_grading_revision`): 0 for a first grade, else one more than the
greatest revision any row of the attempt carries, superseded rows included.
The number is read and written inside the grading's own transaction, so two
epochs of one attempt never share it. A regrade or an adjudication at the
successor also supersedes every live row of the attempt, so its epoch is the
attempt's only live one.

**The current epoch** (:func:`current_epoch`) is chosen among the live rows,
never by a content first-seen stamp:

* one live epoch (every epoch written at the successor): that epoch;
* several (only rows written before the successor, whose ordinary regrades
  superseded the self-grade tier alone): an epoch without a revision over one
  with a revision, because every writer that stamped a revision either came
  first (the first grade, revision 0) or superseded every live row (an
  adjudication), so a revision-less epoch still live beside it is a later
  regrade; among several revision-less epochs, the latest by its last row's
  ``(created_at, id)`` (ids are unique, so it cannot tie); among revisioned
  ones, the greatest revision.

**Its contract** (:func:`epoch_contract_version_id`) is the one assessment
contract version every row of the epoch cites; an epoch whose rows cite none,
several, or not all the same, has no contract on record.

This module is a leaf: pure functions over rows that are either
``GradingEvidenceRecord`` objects or mappings with the same field names.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

def _field(row: Any, name: str) -> Any:
    if isinstance(row, Mapping):
        return row.get(name)
    return getattr(row, name, None)


def epoch_key(row: Any) -> str:
    """``revision:N`` for a row carrying a grading revision, else ``legacy:<created_at>``."""

    revision = _field(row, "grading_revision")
    if revision is not None:
        return f"revision:{int(revision)}"
    return f"legacy:{_field(row, 'created_at')}"


@dataclass(frozen=True)
class GradingEpoch:
    """The rows of one grading epoch, in the order they were given."""

    key: str
    rows: tuple[Any, ...]

    @property
    def revision(self) -> int | None:
        revisions = {_field(row, "grading_revision") for row in self.rows}
        revisions.discard(None)
        return int(max(revisions)) if revisions else None

    @property
    def live(self) -> bool:
        """Does any of its rows still stand (not superseded)?"""

        return any(_field(row, "superseded_at") is None for row in self.rows)

    @property
    def last_written(self) -> tuple[str, str]:
        """``(created_at, id)`` of its last-written row."""

        return max((str(_field(row, "created_at") or ""), str(_field(row, "id") or "")) for row in self.rows)

    @property
    def contract_version_id(self) -> str | None:
        return epoch_contract_version_id(self.rows)

    @property
    def criterion_ids(self) -> tuple[str, ...]:
        return tuple(sorted({str(_field(row, "criterion_id")) for row in self.rows}))

    @property
    def agent_run_ids(self) -> tuple[str, ...]:
        return tuple(sorted({str(value) for row in self.rows if (value := _field(row, "agent_run_id"))}))


def epoch_contract_version_id(rows: Iterable[Any]) -> str | None:
    """The one contract version every row cites, else None (none on record)."""

    versions = {_field(row, "assessment_contract_version_id") for row in rows}
    if len(versions) != 1:
        return None
    (version,) = versions
    return str(version) if version else None


def group_epochs(rows: Iterable[Any]) -> list[GradingEpoch]:
    """The epochs of ``rows``, in the order their keys first appear."""

    grouped: dict[str, list[Any]] = {}
    for row in rows:
        grouped.setdefault(epoch_key(row), []).append(row)
    return [GradingEpoch(key, tuple(members)) for key, members in grouped.items()]


def _current_among(epochs: Sequence[GradingEpoch]) -> GradingEpoch | None:
    if not epochs:
        return None
    if len(epochs) == 1:
        return epochs[0]
    legacy = [epoch for epoch in epochs if epoch.revision is None]
    if legacy:
        return max(legacy, key=lambda epoch: epoch.last_written)
    return max(epochs, key=lambda epoch: (epoch.revision, epoch.last_written))


def current_epoch(rows: Iterable[Any]) -> GradingEpoch | None:
    """The attempt's current grading epoch: chosen among its live rows (see
    the module doc). ``rows`` may include superseded rows; they are ignored.
    None when no row stands."""

    live = [row for row in rows if _field(row, "superseded_at") is None]
    return _current_among(group_epochs(live))


def ordered_epochs(rows: Iterable[Any]) -> list[GradingEpoch]:
    """Every epoch of ``rows`` (superseded ones included) in written order,
    the current epoch last.

    Earlier epochs are ordered by their last row's write stamp, then their
    revision, then that row's id: an epoch written at the successor in its
    predecessor's second still sorts after it by its revision, and ids are
    unique, so the order never ties. The current epoch (:func:`current_epoch`)
    is placed last whatever its stamp."""

    rows = list(rows)
    epochs = group_epochs(rows)
    current = current_epoch(rows)
    earlier = sorted(
        (epoch for epoch in epochs if current is None or epoch.key != current.key),
        key=lambda epoch: (
            epoch.last_written[0],
            -1 if epoch.revision is None else epoch.revision,
            epoch.last_written[1],
        ),
    )
    return [*earlier, *([current] if current is not None else [])]


def next_grading_revision(rows: Iterable[Any]) -> int:
    """The grading revision the attempt's next epoch takes: 0 for its first
    grade (no rows at all), else one more than the greatest revision any of
    its rows carries (superseded included), and never below 1."""

    rows = list(rows)
    if not rows:
        return 0
    revisions = [int(value) for row in rows if (value := _field(row, "grading_revision")) is not None]
    return max([0, *revisions]) + 1


def only_grade(rows: Iterable[Any]) -> bool:
    """Is ``rows`` (every row of the attempt, superseded included) one write:
    the attempt's first grade and nothing after it?

    One epoch key is not enough (review F3). Revision-less rows share the key
    ``legacy:<created_at>``, so a regrade written in its original's second
    falls under the original's key. Two signs say there was a second write:

    * a superseded row: a grade's rows are only ever superseded by a later
      write (a regrade, an adjudication, a clarification's resolution);
    * two grading runs: one write carries at most one ``agent_run_id`` (a
      joint grade's self-graded tier carries none beside its model tier's).
    """

    rows = list(rows)
    if len(group_epochs(rows)) != 1:
        return False
    if any(_field(row, "superseded_at") is not None for row in rows):
        return False
    runs = {str(value) for row in rows if (value := _field(row, "agent_run_id"))}
    return len(runs) <= 1


__all__ = [
    "GradingEpoch",
    "current_epoch",
    "epoch_contract_version_id",
    "epoch_key",
    "group_epochs",
    "next_grading_revision",
    "only_grade",
    "ordered_epochs",
]
