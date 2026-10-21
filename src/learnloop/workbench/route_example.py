"""Reader workbench RW2c: a worked example that takes your route (spec_reader_workbench_v1 §5.10, G40).

"A worked example using CDF-first derivation… the learner should not have to
restart." The retrieval is the sources spec's: ``find_sources(intent=
"worked_example", item=…, learner_work_md=<the learner's steps>)`` under the
workbench's caller context, derived on the server, so its policy is
``assisted_practice`` for the item (no exercise or solution block of the
item, nothing linked to it, no passage reproducing its answer, no exam or
held-out material; a cold administration retrieves nothing). Its listwise
verification judges each candidate ``follows_learner_route``,
``worked_example`` or ``unrelated`` (its §9.2). This module adds only the
Reader's part:

* **the query**: after a hint, the hint's own text (the writer wrote it from
  the learner's route and the questionable step) with the step it is about,
  as the bridge asks; on "Show me a similar example", the step in focus;
* **when**: in the background after a shown level-3-or-higher hint in the
  Reader, or on "Show me a similar example";
* **what is kept**: verified passages only, ``follows_learner_route`` first,
  and, again here, none whose text overlaps the item's key and none that is
  exam material (the shared predicates), so a fake or a future change of the
  service cannot widen what reaches the learner;
* **what the learner sees**, beside the step: "A worked example that takes
  your route: Book A §3.4 · compare it with your step 4" (or "by another
  route" when no passage follows the learner's), the passage one click away
  in the book, and "another passage" when the draw had options.

**Before the sources spec's S3** (no ``worked_example`` intent, or the source
service or retrieval switched off) the example is absent, not approximated:
nothing is searched and "Show me a similar example" is not offered.

**Inside the workbench's limits.** A search is one of the workbench's own
calls: its ``help_assists`` row (``assist_kind = 'example'``) is written
BEFORE the search, in the transaction that checks
``workbench.max_calls_per_session``, and its metered calls are charged to
``workbench.max_daily_cost_usd`` as well as the source service's envelope.
The row is counted by nothing (like the bridge, §5.4: the book being open
already counts, and peeking the passage counts through the book's own rule).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
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
from learnloop.workbench import passage_draw

KIND = "example"
TRIGGERS = ("after_hint", "show_me")
#: The lowest hint level after which the example is looked for (§5.10).
MIN_HINT_LEVEL = 3
#: Passages asked for (the verification's pick bound).
LIMIT = 4
ROUTE_LINE = "A worked example that takes your route: {label}{step}"
OTHER_ROUTE_LINE = "A worked example (by another route): {label}{step}"
NOTHING_LINE = "no worked example in your books fits this step yet"
QUERY_CHARS = 1200
WORK_CHARS = 3000


def s3_available(vault: Any) -> tuple[bool, str | None]:
    """Whether the sources spec's ``worked_example`` intent can run here."""

    try:
        from learnloop.source_retrieval import find_sources as fs
    except ImportError:  # pragma: no cover - the service is on main
        return False, "sources_s3_absent"
    if "worked_example" not in tuple(getattr(fs, "INTENTS", ())):
        return False, "sources_s3_absent"
    if not bool(getattr(vault.config.source_service, "enabled", False)):
        return False, "source_service_disabled"
    if not bool(getattr(vault.config.source_retrieval, "enabled", False)):
        return False, "source_retrieval_disabled"
    return True, None


def examples_enabled(vault: Any) -> bool:
    return bool(getattr(vault.config.workbench, "examples_enabled", False))


def available(vault: Any) -> bool:
    """The switch is on and the sources spec's S3 can serve the intent."""

    return examples_enabled(vault) and s3_available(vault)[0]


def learner_work_md(steps: Sequence[Any]) -> str:
    """The learner's steps as the verification reads them (numbered)."""

    return "\n\n".join(f"Step {step.number}: {step.body_md}" for step in steps if str(step.body_md).strip())


def _label(hit: Mapping[str, Any]) -> str:
    parts = [str(hit.get("source_title") or "your book")]
    if hit.get("section"):
        parts.append(f"§{hit['section']}" if not str(hit["section"]).startswith("§") else str(hit["section"]))
    if hit.get("page") is not None:
        parts.append(f"p. {hit['page']}")
    return " · ".join(parts)[:120]


def _default_find(vault: Any, repository: Repository, query: str, *, caller: Any, learner_work_md: str,
                  owner_id: str) -> Any:
    """The sources spec's search under the caller's derived policy and the
    service's own daily cap (``propose_sources``)."""

    from learnloop.instructional.sources import propose_sources

    return propose_sources(vault, repository, query, caller=caller, intent="worked_example",
                           learner_work_md=learner_work_md, limit=LIMIT, owner_id=owner_id)


def caller_for_session(repository: Repository, workbench_session_id: str, item: Any) -> Any:
    """The workbench session's caller: the item's practice context (assisted
    practice), cold when a cold administration of the item is open."""

    from learnloop.instructional.policy import caller_for

    return caller_for(repository, "code", ref=f"workbench:{workbench_session_id}", item_id=item.id,
                      learning_object_ids=(item.learning_object_id,), context="practice")


def keep(vault: Any, repository: Repository, item: Any, hits: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """The verified passages a learner may be shown, route first (module docstring)."""

    from learnloop.source_retrieval.corpus import exam_withheld
    from learnloop.tutor.tutor_qa import span_leaks_expected

    kept = [dict(hit) for hit in hits if str(hit.get("verdict") or "") in passage_draw.EXAMPLE_VERDICTS
            and str(hit.get("role") or "") not in ("exercise", "solution")
            and not span_leaks_expected(str(hit.get("text") or ""), item.expected_answer)]
    if kept:
        withheld = exam_withheld(vault, repository, [(str(hit["extraction_id"]), str(hit["span_id"]))
                                                     for hit in kept])
        kept = [hit for hit in kept if (str(hit["extraction_id"]), str(hit["span_id"])) not in withheld]
    order = {verdict: index for index, verdict in enumerate(passage_draw.EXAMPLE_VERDICTS)}
    kept.sort(key=lambda hit: order[str(hit["verdict"])])  # stable: the judge's order within a class
    for hit in kept:
        hit["label"] = _label(hit)
    return kept


def _settle(repository: Repository, assist_id: str, fields: dict[str, Any]) -> None:
    with repository.atomic():
        assists_store.settle_bridge(repository.connection(), assist_id, fields, kind=KIND)


def example_for(
    vault: Any,
    repository: Repository,
    *,
    workbench_session_id: str,
    item: Any,
    steps: Sequence[Any],
    trigger: str,
    about_step_id: str | None = None,
    hint_assist_id: str | None = None,
    submission_id: str | None = None,
    find: Callable[..., Any] | None = None,
    envelope: Any | None = None,
    max_calls: int | None = None,
    draw_enabled: bool = False,
    seed: str | None = None,
) -> dict[str, Any]:
    """Look for the example; write the row prepared (``shown = 0``). Returns
    ``{status: ready | none | absent | unavailable, assist_id, line, ...}``."""

    from learnloop.workbench.check import session_calls_on

    if trigger not in TRIGGERS:
        raise ValueError(f"trigger must be one of {', '.join(TRIGGERS)}")
    ok, reason = s3_available(vault)
    if not ok:
        # Absent, not approximated (G40): nothing searched, nothing written.
        return {"status": "absent", "reason": reason}
    numbers = {step.chain_id: step.number for step in steps}
    about = next((step for step in steps if step.chain_id == about_step_id), None)
    hint = None
    if hint_assist_id is not None:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            hint = assists_store.assist(connection, hint_assist_id)
        if hint is None or hint.get("workbench_session_id") != workbench_session_id or not hint.get("shown"):
            return {"status": "unavailable", "reason": "hint_not_shown"}
        about = next((step for step in steps if step.chain_id == hint.get("about_step_id")), about)
    query = "\n\n".join(part for part in (str((hint or {}).get("body_md") or ""),
                                          str(about.body_md) if about is not None else "") if part.strip())
    if not query.strip():
        query = learner_work_md(steps[-1:]) if steps else ""
    if not query.strip():
        return {"status": "none", "line": NOTHING_LINE}
    if envelope is not None and envelope.remaining() <= 0 and _metered(vault):
        return {"status": "unavailable", "reason": "capped"}
    assist_id = "ha_" + new_ulid()
    placement = {"trigger": trigger, "status": "searching",
                 **({"hint_assist_id": hint_assist_id} if hint_assist_id else {})}
    row = {
        "id": assist_id, "surface": "workbench", "assist_kind": KIND, "practice_item_id": item.id,
        "practice_item_hash": practice_item_hash(item), "practice_session_id": None,
        "workbench_session_id": workbench_session_id,
        "submission_id": (hint or {}).get("submission_id") or submission_id,
        "placement_json": json.dumps(placement, sort_keys=True),
        "chooser": "none", "shown": 0, "counted_by": None,
        "about_step_id": about.chain_id if about is not None else None,
        # The work it was searched against, identity only (ids and content
        # hashes, never the text): what its unaided progress is measured from
        # (``hints.report_workbench.workbench_unaided_progress``; review F4).
        "step_snapshot_json": json.dumps([{"chain_id": step.chain_id, "step_id": step.step_id,
                                           "number": step.number, "hash": step.content_hash}
                                          for step in steps], sort_keys=True),
        "requested_at": utc_now_iso(),
    }
    with repository.atomic():
        connection = repository.connection()
        if max_calls is not None and session_calls_on(connection, workbench_session_id) >= int(max_calls):
            return {"status": "unavailable", "reason": "session_capped"}
        # The search's place among the problem's calls, taken before it runs.
        assists_store.insert_assist(connection, row)
    caller = caller_for_session(repository, workbench_session_id, item)
    try:
        with spend_envelopes(envelope):
            hits = (find or _default_find)(vault, repository, query[:QUERY_CHARS], caller=caller,
                                           learner_work_md=learner_work_md(steps)[:WORK_CHARS],
                                           owner_id=f"workbench_example:{assist_id}")
    except SpendLimitExceeded:
        _settle(repository, assist_id, {"placement_json": json.dumps({**placement, "status": "capped"},
                                                                     sort_keys=True)})
        return {"status": "unavailable", "reason": "capped"}
    except Exception as exc:  # noqa: BLE001 - an example never reaches the hint
        _settle(repository, assist_id, {"placement_json": json.dumps(
            {**placement, "status": "failed", "error": type(exc).__name__}, sort_keys=True)})
        return {"status": "unavailable", "reason": type(exc).__name__}
    manifest = dict(getattr(hits, "manifest", {}) or {})
    verification = str((manifest.get("verification") or {}).get("status") or "")
    kept = keep(vault, repository, item, list(getattr(hits, "hits", []) or [])) \
        if verification in ("verified", "cached") else []
    manifest_json = json.dumps({"policy": getattr(hits, "policy", None), "status": getattr(hits, "status", None),
                                **manifest}, sort_keys=True, default=str)
    if not kept:
        _settle(repository, assist_id, {
            "placement_json": json.dumps({**placement, "status": "none", "verification": verification or None},
                                         sort_keys=True),
            "retrieval_manifest_json": manifest_json})
        return {"status": "none", "line": NOTHING_LINE}
    chosen = kept[0]
    drawn = passage_draw.draw(passage_draw.best_class(kept), seed=seed or passage_draw.new_seed()) \
        if draw_enabled else None
    if drawn is not None:
        chosen = next(hit for hit in kept if passage_draw.option_id(hit) == drawn.drawn["option_id"])
    line = example_line(chosen, numbers.get(about.chain_id) if about is not None else None)
    _settle(repository, assist_id, {
        "body_md": line,
        "placement_json": json.dumps({**placement, "status": "found", "span_id": chosen["span_id"],
                                      "extraction_id": chosen["extraction_id"], "label": chosen["label"],
                                      # The book it is in (review F1: another book opens there).
                                      "source_id": chosen.get("source_id"),
                                      "verdict": chosen["verdict"], "role": "worked_example",
                                      "step_number": numbers.get(about.chain_id) if about is not None else None},
                                     sort_keys=True),
        "cited_span_ids_json": json.dumps([str(chosen["span_id"])]),
        "retrieval_manifest_json": manifest_json,
        **(drawn.columns() if drawn is not None else {}),
    })
    result = {"status": "ready", "assist_id": assist_id, "line": line, "span_id": chosen["span_id"],
              "extraction_id": chosen["extraction_id"], "source_id": chosen.get("source_id"),
              "label": chosen["label"], "verdict": chosen["verdict"], "trigger": trigger, "about_step_id": about.chain_id if about is not None else None}
    if drawn is not None:
        result["alternatives"] = len(drawn.options) - 1
    return result


def example_line(passage: Mapping[str, Any], step_number: int | None) -> str:
    step = f" · compare it with your step {step_number}" if step_number else ""
    template = ROUTE_LINE if passage.get("verdict") == "follows_learner_route" else OTHER_ROUTE_LINE
    return template.format(label=str(passage.get("label") or "a passage"), step=step)


def _metered(vault: Any) -> bool:
    from learnloop.practice_index.paid import plan_route

    try:
        return plan_route(vault, "source_rerank", None).billing == "metered"  # type: ignore[arg-type]
    except Exception:  # noqa: BLE001 - unknown: treated as metered (fail closed)
        return True


def example_view(row: Mapping[str, Any]) -> dict[str, Any]:
    """What the workbench shows of a shown example (no passage text: the
    passage opens in the book)."""

    placement = json.loads(row.get("placement_json") or "{}")
    view = {"assist_id": row["id"], "line": row.get("body_md") or "", "span_id": placement.get("span_id"),
            "extraction_id": placement.get("extraction_id"), "source_id": placement.get("source_id"),
            "label": placement.get("label"),
            "verdict": placement.get("verdict"), "trigger": placement.get("trigger"),
            "about_step_id": row.get("about_step_id"), "hint_assist_id": placement.get("hint_assist_id")}
    view.update(passage_draw.alternatives_view(row))
    return view


__all__ = ["KIND", "MIN_HINT_LEVEL", "NOTHING_LINE", "OTHER_ROUTE_LINE", "ROUTE_LINE", "TRIGGERS", "available",
           "caller_for_session", "example_for", "example_line", "example_view", "examples_enabled", "keep",
           "learner_work_md", "s3_available"]
