"""Reader workbench RW6b part 2: reader activity for the router's learner-state
card (spec_reader_workbench_v1 §9.2; router spec §4).

:func:`reader_activity_for_card` is a **pure read** (like
``named_gaps_for_card``): for the candidates' learning objects it returns
``ReaderActivityV1``, typed, with no prose of LearnLoop's own and no source
text:

* **open inquiries** (the root question's excerpt, the learner's own words;
  its age in days; its depth, the longest chain of follow-ups under it);
* **assisted-only work** (a claim needing an independent check: the facet,
  the highest help used, the date), dropped once an unassisted success on the
  facet's Demonstrated curve answers it;
* **pending reader follow-ups** (purpose, date, the valuation receipt's
  numbers with its scale label);
* **missed predictions** and **the sessions' formative records**
  (``ReaderObservationV1``, typed);
* **open hypotheses** (gaps named from the sessions' questions, the rival
  explanations a follow-up question was asked against, with their source
  rows);
* **kept comparisons** on these LOs (RW4d's ``kept_comparisons_for_card``);
* **candidate actions**, a typed list with where each came from (a pending
  follow-up with its valuation; continue reading where the session stopped;
  near-transfer practice ``find_practice`` proposed when nothing cleared the
  stop), never a choice;
* **the latest narrative**, labelled model-written, with its cited ids.

**Data for the router, not a decision input today.** The card builder
(``daily_plan.router_card``) puts it on ``LearnerStateCard.reader_activity``,
outside the typed card, its text, its hash and its token count, so the stored
cards, every router model's input and every decision are unchanged (router
R2's rendering of it as a "Reader activity" section is a later step: moving
it into the hashed card changes what the router models read, which needs its
own successor). **Nothing in it is evidence** (W1): no scoring, scheduling,
projection, grading or serving path reads it.

Its reads are bounded by RW6b's digest rows (one per reader session with
activity) whose sessions touched these LOs; it reads strictly before
``as_of``. Absent (None) with ``digest.enabled`` or ``reader_inquiry.enabled``
off. Exam material (the one predicate, ``exam_withheld``): an inquiry
anchored in a withheld passage keeps its entry and never its words (fail
closed when the predicate cannot be read).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
import logging
from typing import Any

from learnloop.clock import parse_utc
from learnloop.db.stores import reader_digests as RDG

LOG = logging.getLogger(__name__)

ACTIVITY_VERSION = "reader_activity_v1"
#: W1: routing only; nothing here is evidence.
AUTHORITY = "routing_only"
#: The root question's excerpt (the recap's own excerpt length).
EXCERPT_CHARS = 140
#: The sections of ``ReaderActivityV1``, in order.
SECTIONS: tuple[str, ...] = (
    "open_inquiries", "assisted_only", "pending_followups", "missed_predictions", "open_hypotheses",
    "formative_records", "kept_comparisons", "candidate_actions", "narrative",
)


def reader_activity_enabled(vault: Any) -> bool:
    """The section's switches: ``digest.enabled`` (RW6b part 2) and
    ``reader_inquiry.enabled`` (the sessions and inquiries are RW1a's)."""

    config = vault.config
    return bool(getattr(getattr(config, "digest", None), "enabled", True)) and bool(
        getattr(getattr(config, "reader_inquiry", None), "enabled", True))


def _ids(values: Iterable[Any]) -> list[str]:
    return [str(value) for value in values if value not in (None, "")]


def _before(value: Any, cutoff: datetime | None) -> bool:
    when = parse_utc(str(value)) if value else None
    return cutoff is None or (when is not None and when < cutoff)


def _excerpt(text: Any) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= EXCERPT_CHARS else value[: EXCERPT_CHARS - 1].rstrip() + "…"


def _facets_of(vault: Any, lo_ids: Sequence[str]) -> set[str]:
    from learnloop.vault.models import learning_object_facet_union

    out: set[str] = set()
    for lo_id in lo_ids:
        lo = vault.learning_objects.get(lo_id)
        if lo is None:
            continue
        for facet in learning_object_facet_union(lo):
            out.add(vault.canonical_facet_id(str(facet)))
    return out


def _touches(summary: Mapping[str, Any], lo_ids: set[str], facets: set[str]) -> bool:
    return bool(set(_ids(summary.get("learning_objects_touched") or ())) & lo_ids
                or set(_ids(summary.get("facets_touched") or ())) & facets)


def _record_in_scope(record: Mapping[str, Any], scope: set[str]) -> bool:
    return bool(set(_ids(record.get("facet_candidates") or ())) & scope)


def _days(start: Any, cutoff: datetime | None) -> int | None:
    when = parse_utc(str(start)) if start else None
    if when is None or cutoff is None:
        return None
    return max(0, (cutoff - when).days)


# -- sections ---------------------------------------------------------------------------------


def _inquiry_tree(history: Sequence[Mapping[str, Any]], cutoff: datetime | None) -> dict[str, dict[str, Any]]:
    """Per root exchange: the root's event, its exchange count and depth
    (exchanges strictly before ``cutoff``)."""

    by_id = {str(e["event_id"]): e for e in history if _before(e.get("created_at"), cutoff)}
    trees: dict[str, dict[str, Any]] = {}
    for exchange_id in by_id:
        current, chain = exchange_id, [exchange_id]
        while True:
            parent = by_id[current].get("parent_exchange_id")
            if not parent or str(parent) not in by_id or str(parent) in chain:
                break
            current = str(parent)
            chain.append(current)
        tree = trees.setdefault(current, {"root": by_id[current], "exchanges": 0, "depth": 0})
        tree["exchanges"] += 1
        tree["depth"] = max(tree["depth"], len(chain) - 1)
    return trees


def _open_inquiries(vault: Any, repository: Any, rows: Sequence[Mapping[str, Any]], lo_ids: set[str],
                    cutoff: datetime | None) -> list[dict[str, Any]]:
    from learnloop.reader import reader_dialogue as RD
    from learnloop.reader.reader_progression import learning_objects_for_span

    roots_by_extraction: dict[str, set[str]] = {}
    for row in rows:
        inquiries = (row.get("summary") or {}).get("inquiries") or {}
        for key in ("opened", "still_open"):
            for line in inquiries.get(key) or ():
                if line.get("root_exchange_id"):
                    roots_by_extraction.setdefault(str(row["extraction_id"]), set()).add(str(line["root_exchange_id"]))
    out: list[dict[str, Any]] = []
    for extraction_id, wanted in sorted(roots_by_extraction.items()):
        trees = _inquiry_tree(RD.ask_history(repository, extraction_id=extraction_id, branches=True), cutoff)
        for root_id in sorted(wanted):
            tree = trees.get(root_id)
            if tree is None:
                continue
            root = tree["root"]
            if (root.get("resolution") or "open") != "open" or not root.get("question_event_id"):
                continue
            spans = _ids(root.get("selection_span_ids") or ()) or _ids((root.get("span_id"),))
            los: list[str] = []
            for span_id in spans:
                for lo_id in learning_objects_for_span(vault, repository, extraction_id=extraction_id, span_id=span_id):
                    if lo_id in lo_ids and lo_id not in los:
                        los.append(lo_id)
            if not los:
                continue
            out.append({"extraction_id": extraction_id, "root_exchange_id": root_id,
                        "question_event_id": root.get("question_event_id"),
                        "question_excerpt": _excerpt(root.get("question_md")),
                        "opened_at": root.get("created_at"), "age_days": _days(root.get("created_at"), cutoff),
                        "depth": tree["depth"], "exchanges": tree["exchanges"], "learning_object_ids": sorted(los),
                        "anchor_span_ids": spans})
    if not out:
        return out
    from learnloop.content.sources import exam_material as EM

    keys = sorted({(entry["extraction_id"], span) for entry in out for span in entry["anchor_span_ids"]})
    try:
        withheld: Any = EM.exam_withheld(vault, repository, keys)
    except Exception:  # noqa: BLE001 - an unreadable predicate shows no words (fail closed)
        withheld = None
    for entry in out:
        if withheld is None or any((entry["extraction_id"], span) in withheld for span in entry["anchor_span_ids"]):
            entry["question_excerpt"] = None
            entry["withheld"] = "exam_material"
    return sorted(out, key=lambda e: (str(e.get("opened_at") or ""), e["root_exchange_id"]))


def _assisted_only(vault: Any, repository: Any, rows: Sequence[Mapping[str, Any]], facets: set[str],
                   lo_ids: set[str]) -> list[dict[str, Any]]:
    claims: dict[str, dict[str, Any]] = {}
    for row in rows:
        summary = row.get("summary") or {}
        work = {str(line.get("attempt_id")): line for line in summary.get("workbench") or () if line.get("attempt_id")}
        for claim in summary.get("claims_needing_independent_check") or ():
            facet = str(claim.get("facet_id") or "")
            if facet not in facets:
                continue
            lines = [work[a] for a in _ids(claim.get("attempt_ids") or ()) if a in work]
            levels = [int(line["highest_help_level"]) for line in lines if line.get("highest_help_level") is not None]
            entry = {
                "facet_id": facet, "basis": claim.get("basis"), "attempt_ids": _ids(claim.get("attempt_ids") or ()),
                "highest_help_level": max(levels) if levels else None,
                "hints": max((int(line.get("hints") or 0) for line in lines), default=0),
                "book_counted": any(bool(line.get("book_counted")) for line in lines),
                "at": row.get("ended_at"), "since": row.get("started_at"), "digest_id": row["id"],
                "learning_object_ids": sorted(lo for lo in lo_ids if facet in _facets_of(vault, [lo])),
            }
            previous = claims.get(facet)
            if previous is None or str(entry["at"] or "") > str(previous["at"] or ""):
                claims[facet] = entry
    if not claims:
        return []
    # Answered since: an unassisted success on the facet's Demonstrated curve
    # after the session's start (RW6a's own definition of the claim).
    try:
        from learnloop.learner.facet_evidence_timeline import facet_evidence_timelines
        from learnloop.reader import recap as RC

        curves = facet_evidence_timelines(vault, repository, sorted(claims))
        for facet, points in curves.items():
            if facet in claims and RC._effective_success_since(points, str(claims[facet]["since"])):
                claims.pop(facet)
    except Exception:  # noqa: BLE001 - unreadable curves: the claims stand as recorded
        LOG.debug("reader activity: claim curves unreadable", exc_info=True)
    return [claims[facet] for facet in sorted(claims)]


def _due_hint(repository: Any, commitment_id: str) -> str | None:
    versions = sorted(repository.commitment_versions_for(commitment_id), key=lambda r: int(r["version"]))
    return next((str(v["due_hint"]) for v in reversed(versions) if v.get("due_hint")), None)


def _line_los(line: Mapping[str, Any]) -> set[str]:
    out: set[str] = set()
    for entry in line.get("licensing") or ():
        if isinstance(entry, Mapping):
            out.update(_ids(entry.get("learning_object_ids") or ()))
    return out


def _pending_followups(repository: Any, rows: Sequence[Mapping[str, Any]], lo_ids: set[str],
                       cutoff: datetime | None) -> list[dict[str, Any]]:
    from learnloop.curriculum import commitments as C

    out: list[dict[str, Any]] = []
    for row in rows:
        valuation = row.get("valuation") or {}
        for line in valuation.get("chosen") or ():
            commitment_id = line.get("commitment_id")
            los = _line_los(line) & lo_ids
            if not commitment_id or not los:
                continue
            try:
                if C.resolve_disposition(repository, str(commitment_id)) != "one_check_pending":
                    continue
            except C.UnknownCommitment:
                continue
            out.append({
                "commitment_id": str(commitment_id), "digest_id": row["id"], "item_id": line.get("ref"),
                "purpose": line.get("purpose"), "novelty": line.get("novelty"),
                "due_hint": _due_hint(repository, str(commitment_id)) or line.get("due_hint"),
                "learning_object_ids": sorted(los),
                "valuation": {"mode": line.get("mode"), "regime": line.get("regime"),
                              "value_minutes_lcb": line.get("value_minutes_lcb"),
                              "expected_minutes": line.get("expected_minutes"), "probe_eig": line.get("probe_eig"),
                              "point_eig_nats": line.get("point_eig_nats"),
                              "evsi_assignment": line.get("evsi_assignment"),
                              "scale": valuation.get("scale")},
            })
    return sorted(out, key=lambda e: (str(e.get("due_hint") or "9999"), e["commitment_id"]))


def _open_hypotheses(rows: Sequence[Mapping[str, Any]], lo_ids: set[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        summary = row.get("summary") or {}
        for gap in summary.get("gaps_named") or ():
            out.append({"kind": "named_gap", **{key: gap.get(key) for key in
                                                ("gap_id", "kind", "target_kind", "target_id", "source_id")},
                        "source": {"table": "learner_text_gaps", "digest_id": row["id"]}})
        for question in (row.get("valuation") or {}).get("questions") or ():
            body = question.get("question") or {}
            if body.get("purpose") != "discriminating" or not body.get("target_hypotheses"):
                continue
            los = set(_ids(body.get("learning_object_ids") or ())) & lo_ids
            if not los:
                continue
            out.append({"kind": "rival_explanations", "question": question.get("key"),
                        "learning_object_ids": sorted(los),
                        "target_hypotheses": [dict(h) for h in body.get("target_hypotheses") or ()],
                        "raised_by": [dict(r) for r in body.get("raised_by") or ()],
                        "outcome": question.get("outcome"),
                        "source": {"table": "reader_session_digests", "digest_id": row["id"]}})
    return out


def _records(rows: Sequence[Mapping[str, Any]], scope: set[str], key: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        for record in (row.get("summary") or {}).get(key) or ():
            if isinstance(record, Mapping) and _record_in_scope(record, scope):
                out.append({**dict(record), "digest_id": row["id"]})
    return out


def _kept_comparisons(vault: Any, repository: Any, lo_ids: Sequence[str], as_of: str | None) -> list[dict[str, Any]]:
    try:
        from learnloop.source_retrieval.kept_comparisons import kept_comparisons_for_card

        return list(kept_comparisons_for_card(vault, repository, learning_object_ids=list(lo_ids), as_of=as_of))
    except Exception:  # noqa: BLE001 - unreadable keeps: none on the card
        LOG.debug("reader activity: kept comparisons unreadable", exc_info=True)
        return []


def _candidate_actions(repository: Any, rows: Sequence[Mapping[str, Any]], pending: Sequence[Mapping[str, Any]],
                       lo_ids: set[str]) -> list[dict[str, Any]]:
    from learnloop.reader import reader_sessions as RS
    from learnloop.reader import recap as RC

    actions: list[dict[str, Any]] = [
        {"kind": "pending_followup", "from": "reader_followup", "commitment_id": entry["commitment_id"],
         "item_id": entry["item_id"], "purpose": entry["purpose"], "due_hint": entry["due_hint"],
         "valuation": entry["valuation"]}
        for entry in pending
    ]
    latest: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        current = latest.get(str(row["extraction_id"]))
        if current is None or str(row.get("ended_at") or "") > str(current.get("ended_at") or ""):
            latest[str(row["extraction_id"])] = row
    for extraction_id, row in sorted(latest.items()):
        session = RS.ReaderSession(extraction_id, tuple(_ids(row.get("visit_ids") or ())) or (str(row["session_key"]),),
                                   str(row["started_at"]), str(row["ended_at"]))
        try:
            at = RC._continue_at(repository, extraction_id, session)
        except Exception:  # noqa: BLE001 - an unreadable outline offers nothing
            at = None
        if at:
            actions.append({"kind": "continue_reading", "from": "reader_section_progress",
                            "extraction_id": extraction_id, "section_id": at.get("section_id"),
                            "label": at.get("label"), "digest_id": row["id"]})
    for row in rows:
        for question in (row.get("valuation") or {}).get("questions") or ():
            body = question.get("question") or {}
            los = set(_ids(body.get("learning_object_ids") or ())) & lo_ids
            if not los or not question.get("proposal_id") or question.get("outcome") != "no_check":
                continue
            actions.append({"kind": "near_transfer_practice", "from": "find_practice",
                            "proposal_id": question.get("proposal_id"), "question": question.get("key"),
                            "intent": body.get("intent"), "learning_object_ids": sorted(los),
                            "digest_id": row["id"]})
    return actions


def _narrative(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    kept = [row for row in rows if row.get("narrative_md")]
    if not kept:
        return None
    row = max(kept, key=lambda r: (str(r.get("ended_at") or ""), str(r.get("id") or "")))
    return {"text": row.get("narrative_md"), "cited_event_ids": list(row.get("cited_event_ids") or []),
            "label": RDG.NARRATIVE_LABEL, "authority": RDG.NARRATIVE_AUTHORITY, "model": row.get("model"),
            "prompt_version": row.get("prompt_version"), "digest_id": row.get("id"),
            "extraction_id": row.get("extraction_id"), "ended_at": row.get("ended_at")}


# -- the read ----------------------------------------------------------------------------------


def reader_activity_for_card(vault: Any, repository: Any, learning_object_ids: Sequence[str],
                             as_of: str | None) -> dict[str, Any] | None:
    """``ReaderActivityV1`` for these LOs, read strictly before ``as_of``
    (a pure read; None when switched off)."""

    if not reader_activity_enabled(vault):
        return None
    lo_ids = sorted({str(lo) for lo in learning_object_ids if lo})
    los = set(lo_ids)
    facets = _facets_of(vault, lo_ids)
    cutoff = parse_utc(as_of) if as_of else None
    activity: dict[str, Any] = {"activity_version": ACTIVITY_VERSION, "authority": AUTHORITY, "as_of": as_of,
                                "learning_object_ids": lo_ids}
    with repository.connection() as connection:
        if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                              (RDG.TABLE,)).fetchone() is None:
            rows: list[dict[str, Any]] = []
        else:
            rows = RDG.digests(connection)
    rows = [row for row in rows if _before(row.get("ended_at"), cutoff) and _before(row.get("created_at"), cutoff)
            and _touches(row.get("summary") or {}, los, facets)]
    scope = los | facets
    pending = _pending_followups(repository, rows, los, cutoff)
    activity.update({
        "open_inquiries": _open_inquiries(vault, repository, rows, los, cutoff),
        "assisted_only": _assisted_only(vault, repository, rows, facets, los),
        "pending_followups": pending,
        "missed_predictions": _records(rows, scope, "predictions_missed"),
        "open_hypotheses": _open_hypotheses(rows, los),
        "formative_records": _records(rows, scope, "observations"),
        "kept_comparisons": _kept_comparisons(vault, repository, lo_ids, as_of),
        "candidate_actions": _candidate_actions(repository, rows, pending, los),
        "narrative": _narrative(rows),
    })
    return activity


__all__ = ["ACTIVITY_VERSION", "AUTHORITY", "SECTIONS", "reader_activity_enabled", "reader_activity_for_card"]
