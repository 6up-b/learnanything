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

**Inside the workbench's limits** (fix round 1, F9). A search is one of the
workbench's own calls: its row is written BEFORE the search runs, in the
transaction that checks ``workbench.max_calls_per_session``, so every search
counts against the problem's calls whether it finds a passage or not (a
search that found nothing keeps its row, never shown, with what happened in
``placement_json.status``). Its metered calls are charged to
``workbench.max_daily_cost_usd`` as well as to the source service's own
envelope (the envelopes stack); with the day's budget used and a metered
verification route the search is refused before anything is paid.
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import closing
import json
from typing import Any

from learnloop.ai.spend import SpendLimitExceeded, spend_envelopes
from learnloop.clock import utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import help_assists as assists_store
from learnloop.ids import new_ulid
from learnloop.vault.hashes import practice_item_hash

COMPARE_LINE = "§ compare with the book: {label} ▸"
NOTHING_LINE = "no matching step in your books for this hint"


def _metered_verification(vault: Any) -> bool:
    """Whether the bridge's paid step (T6's listwise verification) bills by
    the token: only then can the workbench's daily budget refuse it."""

    from learnloop.practice_index.paid import plan_route

    try:
        return plan_route(vault, "source_rerank", None).billing == "metered"  # type: ignore[arg-type]
    except Exception:  # noqa: BLE001 - unknown: treated as metered (fail closed)
        return True


def _settle(repository: Repository, assist_id: str, fields: dict[str, Any]) -> None:
    with repository.atomic():
        assists_store.settle_bridge(repository.connection(), assist_id, fields)


def bridge_for_hint(
    vault: Any,
    repository: Repository,
    *,
    workbench_session_id: str,
    hint_assist_id: str,
    item: Any,
    provider: Callable[..., Any] | None = None,
    envelope: Any | None = None,
    max_calls: int | None = None,
    draw_enabled: bool = False,
    seed: str | None = None,
) -> dict[str, Any]:
    """Look for the passage; write the bridge row prepared (``shown = 0``).
    Returns ``{status: ready | none | unavailable, assist_id, line, ...}``.
    ``envelope``: the workbench's daily envelope (the caller's); ``max_calls``:
    ``workbench.max_calls_per_session`` (module docstring). ``draw_enabled``
    (RW2c, ``workbench.passage_draw_enabled``): with two or more verified
    passages, the one shown is drawn and the draw logged on the row
    (:mod:`learnloop.workbench.passage_draw`); ``seed`` fixes the draw."""

    from learnloop.workbench.check import session_calls_on

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
    if envelope is not None and _metered_verification(vault) and envelope.remaining() <= 0:
        return {"status": "unavailable", "reason": "capped"}
    assist_id = "ha_" + new_ulid()
    placement = {"hint_assist_id": hint_assist_id, "status": "searching"}
    row = {
        "id": assist_id, "surface": "workbench", "assist_kind": "bridge", "practice_item_id": item.id,
        "practice_item_hash": practice_item_hash(item), "practice_session_id": None,
        "workbench_session_id": workbench_session_id, "submission_id": hint.get("submission_id"),
        "placement_json": json.dumps(placement, sort_keys=True),
        "chooser": "none", "shown": 0, "counted_by": None,
        "about_step_id": hint.get("about_step_id"),
        "requested_at": utc_now_iso(),
    }
    with repository.atomic():
        connection = repository.connection()
        if max_calls is not None and session_calls_on(connection, workbench_session_id) >= int(max_calls):
            return {"status": "unavailable", "reason": "session_capped"}
        # The search's place among the problem's calls, taken before it runs.
        assists_store.insert_assist(connection, row)
    if provider is None:
        from learnloop.source_retrieval.tutor import TutorSpanProvider

        provider = TutorSpanProvider()
    try:
        with spend_envelopes(envelope):
            spans, manifest = provider(vault, repository, context="practice", question_md=question,
                                       learning_object_ids=[item.learning_object_id], item=item)
    except SpendLimitExceeded:
        _settle(repository, assist_id, {"placement_json": json.dumps({**placement, "status": "capped"},
                                                                     sort_keys=True)})
        return {"status": "unavailable", "reason": "capped"}
    except Exception as exc:  # noqa: BLE001 - a bridge never reaches the hint
        _settle(repository, assist_id, {"placement_json": json.dumps(
            {**placement, "status": "failed", "error": type(exc).__name__}, sort_keys=True)})
        return {"status": "unavailable", "reason": type(exc).__name__}
    already = set()
    try:
        already = {str(span) for span in json.loads(hint.get("cited_span_ids_json") or "[]")}
    except (TypeError, ValueError):
        already = set()
    eligible = [span for span in spans or () if str(span.get("span_id")) not in already]
    chosen = eligible[0] if eligible else None
    drawn = None
    if draw_enabled and chosen is not None and isinstance(manifest, dict) \
            and manifest.get("basis") == "retrieved_verified":
        # RW2c (§5.10): every returned span passed T6's listwise judge, so a
        # draw between them withholds nothing.
        from learnloop.workbench import passage_draw

        drawn = passage_draw.draw(eligible, seed=seed or passage_draw.new_seed())
        if drawn is not None:
            chosen = next(span for span in eligible if passage_draw.option_id(span) == drawn.drawn["option_id"])
    manifest_json = json.dumps(manifest, sort_keys=True, default=str) if manifest else None
    if chosen is None:
        _settle(repository, assist_id, {"placement_json": json.dumps({**placement, "status": "none"}, sort_keys=True),
                                        "retrieval_manifest_json": manifest_json})
        return {"status": "none", "line": NOTHING_LINE,
                "basis": (manifest or {}).get("basis") if isinstance(manifest, dict) else None}
    label = str(chosen.get("label") or "a passage")[:120]
    line = COMPARE_LINE.format(label=label)
    _settle(repository, assist_id, {
        "body_md": line,
        "placement_json": json.dumps({"hint_assist_id": hint_assist_id, "span_id": chosen.get("span_id"),
                                      "extraction_id": chosen.get("extraction_id"), "label": label,
                                      "status": "found"}, sort_keys=True),
        "cited_span_ids_json": json.dumps([str(chosen.get("span_id"))]),
        "retrieval_manifest_json": manifest_json,
        **(drawn.columns() if drawn is not None else {}),
    })
    result = {"status": "ready", "assist_id": assist_id, "line": line, "span_id": chosen.get("span_id"),
              "extraction_id": chosen.get("extraction_id"), "label": label}
    if drawn is not None:
        result["alternatives"] = len(drawn.options) - 1
    return result


__all__ = ["COMPARE_LINE", "NOTHING_LINE", "bridge_for_hint"]
