"""Reader workbench RW2b: "Compare with the book" under a hint (spec_reader_workbench_v1 §5.2 bridging, G8).

After a hint is shown in the Reader, a background request may add a verified
passage of the learner's own source the hint relies on. It uses T6's
``TutorSpanProvider`` in the ``practice`` context unchanged: the item-bound
scope (no exercise or solution block, nothing linked to the item, answer-
overlap spans withheld) and listwise verification. It never delays the hint
(the hint shows *finding the matching step in the book…* meanwhile). A
``worked_parallel`` hint that already quotes the learner's source gets no
second bridge to the same passage.

The bridge is a ``help_assists`` row (``assist_kind = 'bridge'``) counted by
neither the server nor the client: the book being open already counts as one
hint (§5.4), and peeking the passage with the book hidden shows the book,
which counts it then through the book's own rule. Its passage and the
retrieval manifest are kept on the row (``cited_span_ids_json``,
``retrieval_manifest_json``).
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import closing
import json
from typing import Any

from learnloop.clock import utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import help_assists as assists_store
from learnloop.ids import new_ulid
from learnloop.vault.hashes import practice_item_hash

COMPARE_LINE = "§ compare with the book: {label} ▸"
NOTHING_LINE = "no matching step in your books for this hint"


def bridge_for_hint(
    vault: Any,
    repository: Repository,
    *,
    workbench_session_id: str,
    hint_assist_id: str,
    item: Any,
    provider: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Look for the passage; write the bridge row prepared (``shown = 0``).
    Returns ``{status: ready | none | unavailable, assist_id, line, ...}``."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        hint = assists_store.assist(connection, hint_assist_id)
    if hint is None or hint.get("surface") != "workbench" or not hint.get("shown"):
        return {"status": "unavailable", "reason": "hint_not_shown"}
    about_text = ""
    try:
        for entry in json.loads(hint.get("step_snapshot_json") or "[]"):
            if entry.get("chain_id") == hint.get("about_step_id"):
                about_text = str(entry.get("body_md") or "")
    except (TypeError, ValueError):
        about_text = ""
    question = "\n\n".join(part for part in (str(hint.get("body_md") or ""), about_text) if part.strip())
    if not question.strip():
        return {"status": "none", "line": NOTHING_LINE}
    if provider is None:
        from learnloop.source_retrieval.tutor import TutorSpanProvider

        provider = TutorSpanProvider()
    try:
        spans, manifest = provider(vault, repository, context="practice", question_md=question,
                                   learning_object_ids=[item.learning_object_id], item=item)
    except Exception as exc:  # noqa: BLE001 - a bridge never reaches the hint
        return {"status": "unavailable", "reason": type(exc).__name__}
    already = set()
    try:
        already = {str(span) for span in json.loads(hint.get("cited_span_ids_json") or "[]")}
    except (TypeError, ValueError):
        already = set()
    chosen = next((span for span in spans or () if str(span.get("span_id")) not in already), None)
    if chosen is None:
        return {"status": "none", "line": NOTHING_LINE,
                "basis": (manifest or {}).get("basis") if isinstance(manifest, dict) else None}
    label = str(chosen.get("label") or "a passage")[:120]
    assist_id = "ha_" + new_ulid()
    row = {
        "id": assist_id, "surface": "workbench", "assist_kind": "bridge", "practice_item_id": item.id,
        "practice_item_hash": practice_item_hash(item), "practice_session_id": None,
        "workbench_session_id": workbench_session_id, "submission_id": hint.get("submission_id"),
        "body_md": COMPARE_LINE.format(label=label),
        "placement_json": json.dumps({"hint_assist_id": hint_assist_id, "span_id": chosen.get("span_id"),
                                      "extraction_id": chosen.get("extraction_id"), "label": label}, sort_keys=True),
        "chooser": "none", "shown": 0, "counted_by": None,
        "about_step_id": hint.get("about_step_id"),
        "cited_span_ids_json": json.dumps([str(chosen.get("span_id"))]),
        "retrieval_manifest_json": json.dumps(manifest, sort_keys=True, default=str) if manifest else None,
        "requested_at": utc_now_iso(),
    }
    with repository.atomic():
        assists_store.insert_assist(repository.connection(), row)
    return {"status": "ready", "assist_id": assist_id, "line": row["body_md"], "span_id": chosen.get("span_id"),
            "extraction_id": chosen.get("extraction_id"), "label": label}


__all__ = ["COMPARE_LINE", "NOTHING_LINE", "bridge_for_hint"]
