"""Teacher TE3a: a closed lesson's nodes as AD's learning opportunities (spec_teacher_v1 rev 5 §14.2).

**What it reads.** ``lesson_receipts`` (``LessonReceiptV1``, written once at the lesson's close), through AD's
guard: the table is a READING table of ``protected_tables`` since TE3a, read only by the material view's rules,
which withhold a receipt whose lesson (``lessons``' rule: the readings its goal names) or whose own record names a
reading the withheld material touches (Option B, §14.3: a lesson grounded in such a reading is absent, as the
reading is). Nothing else of the lesson is read: no turn, no payload, no check row, no minutes, no text.

**What it lists.** One :class:`~learnloop.reading_sources.ListedEvent` per receipt node with an LO of the vault
whose final status is ``landed`` or ``taught`` (the subkind; ``held``, ``uncertain`` or any other status is no
opportunity), with:

* ``source_table`` ``lesson_receipts`` and ``source_id`` ``<lesson id>/<node id>`` (one opportunity per node);
* the receipt's write time as the source time: when the lesson's outcome became known, so a decision before the
  close never sees it (the availability rule RO1 applies to attempts; the receipt is written at the close);
* the LO's facets named directly, so each takes dose one (§14.2: "the dose is one per node"): one landed dose then
  moves the LO's predicted ``η`` by one step of the curve whatever the LO's facet count, which is what the prior is
  centred on (``priors.LESSON_PRIORS``).

Every receipt not yet recorded is listed, however long ago it was written (as tutor exchanges are, Codex review
F4): lessons are few, and a lesson closed while the switch was off is recorded by the first sweep after it is on.
No model call, no write (the sweep writes), no magnitude.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from learnloop.reading_sources import ListedEvent, ReadingMap, source_stamp

from learnloop.adaptive_difficulty import priors as P

SOURCE_TABLE = "lesson_receipts"


def node_source_id(lesson_id: str, node_id: str) -> str:
    return f"{lesson_id}/{node_id}"


def _nodes(receipt: Any) -> list[Mapping[str, Any]]:
    if isinstance(receipt, str):
        try:
            receipt = json.loads(receipt)
        except ValueError:
            return []
    if not isinstance(receipt, Mapping):
        return []
    nodes = receipt.get("nodes")
    if not isinstance(nodes, list):
        nodes = receipt.get("nodes_summary")
    return [node for node in nodes or [] if isinstance(node, Mapping)]


def lesson_events(connection: Any, reading_map: ReadingMap, upper: str, *, view: Any, vault: Any) -> list[ListedEvent]:
    """Every closed lesson's opportunities written no later than ``upper``, as ``view`` sees them (none while the
    view is unavailable: fail closed)."""

    if view is None or not getattr(view, "available", False):
        return []
    los = getattr(vault, "learning_objects", {}) or {}
    events: list[ListedEvent] = []
    for row in view.rows(connection, SOURCE_TABLE, order="created_at, lesson_id"):
        stamp = source_stamp(row.get("created_at"))
        if stamp is None or stamp > upper:
            continue
        lesson_id = str(row["lesson_id"])
        seen: set[str] = set()
        for node in _nodes(row.get("receipt_json")):
            status, lo, node_id = node.get("status"), node.get("lo_id"), node.get("id")
            if status not in P.LESSON_SUBKINDS or not lo or not node_id or str(lo) not in los:
                continue
            if str(node_id) in seen:
                continue  # a node id once per lesson
            seen.add(str(node_id))
            facets = tuple(reading_map.facets_for_lo(str(lo)))
            if not facets:
                continue  # an LO with no visible facet bears on nothing AD models
            identity = node_source_id(lesson_id, str(node_id))
            events.append(ListedEvent(P.LESSON_KIND, str(status), SOURCE_TABLE, identity, stamp, (str(lo),),
                                      named_facets=facets, identity=identity))
    return events


__all__ = ["SOURCE_TABLE", "lesson_events", "node_source_id"]
