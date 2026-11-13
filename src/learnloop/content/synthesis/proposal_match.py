"""What a synthesis run's result is when an earlier run already proposed the same rows.

Nothing looks a run up by its manifest: a rebuild re-runs the orchestration, every paid call answers from its
checkpoint, and the gates and the facet plan run under today's code. That re-run normalizes to the same rows as the
run it repeats, and writing them again would put a second copy of a proposal in front of the learner. So, after a
run's rows are normalized and gated and before anything is written, the rows are compared with the proposals earlier
runs of the same source set persisted under the same purpose, and the first equal one decides (``match_proposal``):

* **pending** (an item still waits for review, whatever the others' decisions): that proposal is the run's result.
  Nothing new is written, an apply the caller asked for applies its waiting items, and the epigraph step is skipped
  because nothing new was persisted. An item the learner rejected stays rejected: the proposal is returned as it is,
  and an apply takes only waiting items.
* **settled** (nothing waits and not every item was rejected: applied, or applied in part and rejected in part):
  nothing new is written and the result says there is nothing new.
* **rejected** (every item was rejected): not that proposal again. The run's saved answers are dropped (as a gate
  rejection drops them) and the build pays for fresh ones.

A pending match wins over a settled one, and either over a rejected one.

**Equal** means the same items, compared per ``client_item_id`` on everything the run proposed: ``item_type``,
``operation``, ``target_entity_type``, ``target_entity_id``, ``payload`` (as proposed, not as the learner edited it),
``source_ref_ids``, ``audit`` (the instrument gates' verdicts), ``validation_status``, ``validation_errors`` and the
item's dependencies, named by the ``client_item_id`` of each item it depends on as the batch stores them (an unknown
or self dependency is dropped, as :meth:`Repository.persist_proposal_batch` drops it). Left out, because each run mints
them or the learner's review writes them: the item's ``id``, its batch id, ``created_at``, ``updated_at``,
``decision``, ``decided_at``, ``decided_by``, ``edited_payload``, ``applied_change_batch_id``, ``dependency_status``
and ``dependency_block_reason``. Values are compared as the batch stores them (JSON with sorted keys).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, Literal, Mapping

from learnloop.db.repositories import Repository

MatchKind = Literal["pending", "settled", "rejected"]

_COMPARED_FIELDS: tuple[str, ...] = (
    "item_type",
    "operation",
    "target_entity_type",
    "target_entity_id",
    "payload",
    "source_ref_ids",
    "audit",
    "validation_status",
    "validation_errors",
)

_PREFERENCE: dict[str, int] = {"pending": 0, "settled": 1, "rejected": 2}


@dataclass(frozen=True)
class ProposalMatch:
    proposal_id: str
    kind: MatchKind


def _stored(value: Any) -> Any:
    # The batch writes JSON with sorted keys; a row in hand may hold tuples or
    # unsorted dicts that read back equal only after the same round trip.
    return json.loads(json.dumps(value, sort_keys=True))


def _content(rows: Iterable[Mapping[str, Any]], dependencies: Mapping[str, list[str]]) -> dict[str, Any]:
    return {
        str(row["client_item_id"]): {
            **{name: _stored(row.get(name)) for name in _COMPARED_FIELDS},
            "depends_on": dependencies.get(str(row["client_item_id"]), []),
        }
        for row in rows
    }


def proposed_content(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    """The compared content of a run's rows, before they are persisted."""

    client_ids = {str(row["client_item_id"]) for row in rows}
    dependencies = {
        str(row["client_item_id"]): sorted(
            {str(dep) for dep in row.get("depends_on_client_item_ids") or []
             if str(dep) in client_ids and str(dep) != str(row["client_item_id"])}
        )
        for row in rows
    }
    return _content(rows, dependencies)


def stored_content(repository: Repository, items: list[dict[str, Any]]) -> dict[str, Any]:
    """The compared content of a persisted proposal's items."""

    client_by_id = {str(item["id"]): str(item["client_item_id"]) for item in items}
    dependencies = {
        str(item["client_item_id"]): sorted(
            {client_by_id[dep] for dep in repository.proposal_item_dependencies(item["id"]) if dep in client_by_id}
        )
        for item in items
    }
    return _content(items, dependencies)


def _kind(items: list[dict[str, Any]]) -> MatchKind:
    decisions = {item["decision"] for item in items}
    if "pending" in decisions:
        return "pending"
    return "rejected" if decisions == {"rejected"} else "settled"


def match_proposal(
    repository: Repository, *, source_set_id: str, purpose: str, rows: list[Mapping[str, Any]],
) -> ProposalMatch | None:
    """The earlier proposal of ``source_set_id`` under ``purpose`` whose items equal ``rows`` (module docstring)."""

    if not rows:
        return None
    wanted = proposed_content(rows)
    found: list[tuple[int, int, ProposalMatch]] = []
    seen: set[str] = set()
    # Newest first, so of two equal proposals of one kind the later one decides.
    for order, manifest in enumerate(reversed(repository.completed_synthesis_manifests(source_set_id))):
        proposal_id = manifest.get("proposal_id")
        if not proposal_id or proposal_id in seen:
            continue
        seen.add(proposal_id)
        batch = repository.proposal_batch(proposal_id)
        if batch is None or batch.get("purpose") != purpose:
            continue
        items = repository.proposal_items(proposal_id)
        if not items or stored_content(repository, items) != wanted:
            continue
        kind = _kind(items)
        found.append((_PREFERENCE[kind], order, ProposalMatch(proposal_id=str(proposal_id), kind=kind)))
    return min(found, key=lambda entry: entry[:2])[2] if found else None


class RejectedProposalMatch(Exception):
    """A run's rows equal a proposal the learner wholly rejected: its answers are dropped and it pays again."""

    def __init__(self, proposal_id: str) -> None:
        super().__init__(proposal_id)
        self.proposal_id = proposal_id


__all__ = [
    "MatchKind",
    "ProposalMatch",
    "RejectedProposalMatch",
    "match_proposal",
    "proposed_content",
    "stored_content",
]
