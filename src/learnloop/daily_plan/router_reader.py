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

**The card's "Reader activity" section** (router R2, spec §9.2; Codex review
F1). The card builder (``daily_plan.router_card``) puts :func:`for_card`'s
bounded copy in the card's typed evidence registry
(``evidence_sections.reader_activity``, R2a's hook, as R2c's teach-back
summaries) and ``router.card.render_text`` renders it, so the router models
read it at the next block boundary. With no reader activity on the
candidates' LOs, or with ``digest.enabled`` off, the card is the
predecessor's byte for byte. **Nothing in it is evidence** (W1): no scoring,
scheduling, projection, grading or serving path reads it, and the router
never cites it as evidence.

**As of** (Codex review F5; ruling R2). Every event-timed read is bounded by
``as_of``: digest rows created and ended before it; an inquiry's status from its
``inquiry_status_set`` events before it; a follow-up's disposition and date
from its commitment events and versions before it; a claim's answer from its
facet curve's points before it; a gap's reversal and a probe episode's close
before it; the narrative from its ``judgment_ledger`` verdict before it. Three
inputs are read as they are now, because no history of them is kept: a
rival's facet marginal and a causal factor's pending decision (they stay
listed, with their source rows) and a digest row's summary and valuation,
which are the row's latest version (a later re-plan of the same session
shows through). No production caller reads a historical cutoff; see
:func:`reader_activity_for_card`.

Its reads are bounded by RW6b's digest rows (one per reader session with
activity) whose sessions touched these LOs. Absent (None) with
``digest.enabled`` or ``reader_inquiry.enabled`` off; the narrative also
with ``digest.narrative_enabled`` off (Codex review F4). Exam material (the
one predicate, ``exam_withheld``): an inquiry anchored in a withheld passage
keeps its entry and never its words (fail closed when the predicate cannot
be read).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
import json
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
#: The narrative's ``judgment_ledger`` verdict (``instructional.reader_digest``'s
#: ``LEDGER_TASK`` / ``LEDGER_LEFT``; restated: the plan never imports the service).
NARRATIVE_LEDGER_TASK = "reader_digest_narrative"
NARRATIVE_LEDGER_LEFT = "reader_session_digest"
#: The sections of ``ReaderActivityV1``, in order.
SECTIONS: tuple[str, ...] = (
    "open_inquiries", "assisted_only", "pending_followups", "missed_predictions", "open_hypotheses",
    "formative_records", "kept_comparisons", "candidate_actions", "narrative",
)
#: The card's evidence-registry key (``evidence_sections.reader_activity``).
CARD_SECTION = "reader_activity"
#: keep: a prompt-size bound, not a judgment (router R2c's teach-back
#: ``CARD_LIMIT`` precedent). Each list section of the card's copy keeps this
#: many entries (the newest, or the soonest due) and states how many it left
#: out; ``reader_activity_for_card`` itself returns everything.
CARD_LIST_LIMIT = 6
_LIST_SECTIONS = tuple(name for name in SECTIONS if name != "narrative")
#: Lists ordered oldest first, whose newest entries the card keeps.
_NEWEST_LAST = frozenset({"open_inquiries", "missed_predictions", "open_hypotheses", "formative_records",
                          "kept_comparisons"})
#: A probe episode's statuses while it is open (``probe_episodes``).
_EPISODE_OPEN = frozenset({"pending_items", "in_progress"})


def reader_activity_enabled(vault: Any) -> bool:
    """The section's switches: ``digest.enabled`` (RW6b part 2) and
    ``reader_inquiry.enabled`` (the sessions and inquiries are RW1a's)."""

    config = vault.config
    return bool(getattr(getattr(config, "digest", None), "enabled", True)) and bool(
        getattr(getattr(config, "reader_inquiry", None), "enabled", True))


def narrative_enabled(vault: Any) -> bool:
    """``digest.narrative_enabled`` (under ``digest.enabled``): off, no saved
    narrative reaches the section (Codex review F4). Read from the config
    here: the daily plan never imports the instructional service."""

    digest = getattr(vault.config, "digest", None)
    return bool(getattr(digest, "enabled", True)) and bool(getattr(digest, "narrative_enabled", True))


def _ids(values: Iterable[Any]) -> list[str]:
    return [str(value) for value in values if value not in (None, "")]


def _before(value: Any, cutoff: datetime | None) -> bool:
    when = parse_utc(str(value)) if value else None
    return cutoff is None or (when is not None and when < cutoff)


def _excerpt(text: Any) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= EXCERPT_CHARS else value[: EXCERPT_CHARS - 1].rstrip() + "…"


def _facets_of(vault: Any, lo_ids: Sequence[str]) -> set[str]:
    """The LOs' facets (canonical): their own facet union and the evidence
    facets of their practice items (an item's facets are what a claim or a
    formative record names)."""

    from learnloop.vault.models import learning_object_facet_union

    wanted = set(lo_ids)
    out: set[str] = set()
    for lo_id in wanted:
        lo = vault.learning_objects.get(lo_id)
        if lo is None:
            continue
        for facet in learning_object_facet_union(lo):
            out.add(vault.canonical_facet_id(str(facet)))
    for item in vault.practice_items.values():
        if getattr(item, "learning_object_id", None) in wanted:
            for facet in item.evidence_facets or ():
                out.add(vault.canonical_facet_id(str(facet)))
    return out


def _item_lo(vault: Any, item_id: Any) -> str | None:
    item = vault.practice_items.get(str(item_id or ""))
    return getattr(item, "learning_object_id", None) if item is not None else None


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


def _status_events(repository: Any) -> dict[str, list[dict[str, Any]]]:
    """Each inquiry root's ``inquiry_status_set`` events, oldest first."""

    from learnloop.reader import recap as RC

    out: dict[str, list[dict[str, Any]]] = {}
    for event in RC._action_events(repository, ("inquiry_status_set",)):
        payload = event.get("payload") or {}
        root_id = str(payload.get("root_exchange_id") or "")
        if root_id:
            out.setdefault(root_id, []).append({"at": event.get("created_at"),
                                                "resolution": payload.get("resolution"),
                                                "previous": payload.get("previous_resolution")})
    for events in out.values():
        events.sort(key=lambda e: str(e.get("at") or ""))
    return out


def _resolution_as_of(root: Mapping[str, Any], events: Sequence[Mapping[str, Any]],
                      cutoff: datetime | None) -> str:
    """The inquiry's status as it stood at ``cutoff`` (Codex review F5): the
    last status event before it; before its first event, that event's
    previous status. With no event at all, its current status."""

    current = str(root.get("resolution") or "open")
    if cutoff is None or not events:
        return current
    earlier = [event for event in events if _before(event.get("at"), cutoff)]
    if earlier:
        return str(earlier[-1].get("resolution") or "open")
    return str(events[0].get("previous") or "open")


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
    statuses = _status_events(repository) if roots_by_extraction else {}
    for extraction_id, wanted in sorted(roots_by_extraction.items()):
        trees = _inquiry_tree(RD.ask_history(repository, extraction_id=extraction_id, branches=True), cutoff)
        for root_id in sorted(wanted):
            tree = trees.get(root_id)
            if tree is None:
                continue
            root = tree["root"]
            if (_resolution_as_of(root, statuses.get(root_id) or (), cutoff) != "open"
                    or not root.get("question_event_id")):
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
                   lo_ids: set[str], cutoff: datetime | None) -> list[dict[str, Any]]:
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
                "learning_object_ids": sorted({lo for lo in (_item_lo(vault, line.get("practice_item_id"))
                                                             for line in lines) if lo in lo_ids}),
            }
            previous = claims.get(facet)
            if previous is None or str(entry["at"] or "") > str(previous["at"] or ""):
                claims[facet] = entry
    if not claims:
        return []
    # Answered since: an unassisted success on the facet's Demonstrated curve
    # after the session's start (RW6a's own definition of the claim), from
    # the curve's points before ``as_of`` (Codex review F5).
    try:
        from learnloop.learner.facet_evidence_timeline import facet_evidence_timelines
        from learnloop.reader import recap as RC

        curves = facet_evidence_timelines(vault, repository, sorted(claims))
        for facet, points in curves.items():
            points = [point for point in points if _before(getattr(point, "t", None), cutoff)]
            if facet in claims and RC._effective_success_since(points, str(claims[facet]["since"])):
                claims.pop(facet)
    except Exception:  # noqa: BLE001 - unreadable curves: the claims stand as recorded
        LOG.debug("reader activity: claim curves unreadable", exc_info=True)
    return [claims[facet] for facet in sorted(claims)]


def _due_hint(repository: Any, commitment_id: str, cutoff: datetime | None) -> str | None:
    versions = sorted((v for v in repository.commitment_versions_for(commitment_id)
                       if _before(v.get("created_at"), cutoff)), key=lambda r: int(r["version"]))
    return next((str(v["due_hint"]) for v in reversed(versions) if v.get("due_hint")), None)


def _line_los(line: Mapping[str, Any]) -> set[str]:
    out: set[str] = set()
    for entry in line.get("licensing") or ():
        if isinstance(entry, Mapping):
            out.update(_ids(entry.get("learning_object_ids") or ()))
    return out


def _pending_followups(repository: Any, rows: Sequence[Mapping[str, Any]], lo_ids: set[str],
                       cutoff: datetime | None, as_of: str | None) -> list[dict[str, Any]]:
    from learnloop.curriculum import commitments as C

    out: list[dict[str, Any]] = []
    for row in rows:
        valuation = row.get("valuation") or {}
        for line in valuation.get("chosen") or ():
            commitment_id = line.get("commitment_id")
            los = _line_los(line) & lo_ids
            if not commitment_id or not los:
                continue
            # The disposition and the date as they stood at ``as_of`` (Codex review F5).
            commitment = repository.commitment(str(commitment_id))
            if commitment is None or not _before(commitment.get("created_at"), cutoff):
                continue
            try:
                if C.resolve_disposition(repository, str(commitment_id), before=as_of) != "one_check_pending":
                    continue
            except C.UnknownCommitment:
                continue
            out.append({
                "commitment_id": str(commitment_id), "digest_id": row["id"], "item_id": line.get("ref"),
                "purpose": line.get("purpose"), "novelty": line.get("novelty"),
                "due_hint": _due_hint(repository, str(commitment_id), cutoff) or line.get("due_hint"),
                "learning_object_ids": sorted(los),
                "valuation": {"mode": line.get("mode"), "regime": line.get("regime"),
                              "value_minutes_lcb": line.get("value_minutes_lcb"),
                              "expected_minutes": line.get("expected_minutes"), "probe_eig": line.get("probe_eig"),
                              "point_eig_nats": line.get("point_eig_nats"),
                              "evsi_assignment": line.get("evsi_assignment"),
                              "scale": valuation.get("scale")},
            })
    return sorted(out, key=lambda e: (str(e.get("due_hint") or "9999"), e["commitment_id"]))


def _gap_reversals(repository: Any, gap_ids: Sequence[str], cutoff: datetime | None) -> dict[str, list[str]]:
    """The learner's reversals of these named gaps made before ``cutoff``."""

    if not gap_ids:
        return {}
    out: dict[str, list[str]] = {}
    with repository.connection() as connection:
        if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                              ("learner_text_gap_reversals",)).fetchone() is None:
            return {}
        marks = ", ".join("?" for _ in gap_ids)
        for row in connection.execute(
                f"SELECT gap_id, reversal, created_at FROM learner_text_gap_reversals WHERE gap_id IN ({marks}) "
                "ORDER BY created_at, id", list(gap_ids)):
            if _before(row["created_at"], cutoff):
                out.setdefault(str(row["gap_id"]), []).append(str(row["reversal"]))
    return out


def _episode_open(repository: Any, episode_id: str, cutoff: datetime | None) -> bool:
    """A probe episode open at ``cutoff``: created before it and not closed
    before it (its ``completed_at``, else its last update, is the close)."""

    record = repository.probe_episode(episode_id)
    if record is None:
        return False
    if not _before(getattr(record, "created_at", None), cutoff):
        return False
    if record.status in _EPISODE_OPEN:
        return True
    closed_at = getattr(record, "completed_at", None) or getattr(record, "updated_at", None)
    return cutoff is not None and not _before(closed_at, cutoff)


def _open_hypotheses(repository: Any, rows: Sequence[Mapping[str, Any]], lo_ids: set[str],
                     cutoff: datetime | None) -> list[dict[str, Any]]:
    """Open hypotheses as they stood at ``cutoff`` (Codex review F8): a named
    gap the learner reversed is left out (it is kept, with its reversal, in
    the card's own open problems); a rival explanation lists only its targets
    still open (a probe episode closed by then, or a reversed gap, is
    settled), and goes when none is. Each identity appears once, from the
    latest session that named it, with its source rows."""

    gaps: dict[str, dict[str, Any]] = {}
    rivals: dict[str, dict[str, Any]] = {}
    ordered = sorted(rows, key=lambda r: (str(r.get("ended_at") or ""), str(r.get("id") or "")))
    gap_ids: set[str] = set()
    for row in ordered:
        gap_ids.update(str(gap["gap_id"]) for gap in (row.get("summary") or {}).get("gaps_named") or ()
                       if gap.get("gap_id"))
        for question in (row.get("valuation") or {}).get("questions") or ():
            gap_ids.update(str(ref["id"]) for ref in (question.get("question") or {}).get("target_hypotheses") or ()
                           if ref.get("kind") == "named_gap" and ref.get("id"))
    reversed_gaps = _gap_reversals(repository, sorted(gap_ids), cutoff)
    episodes: dict[str, bool] = {}

    def still_open(ref: Mapping[str, Any]) -> bool:
        kind, ident = ref.get("kind"), str(ref.get("id") or "")
        if kind == "named_gap":
            return ident not in reversed_gaps
        if kind == "episode_label":
            if ident not in episodes:
                episodes[ident] = _episode_open(repository, ident, cutoff)
            return episodes[ident]
        # A facet marginal or a causal factor's pending decision has no kept
        # history: listed with its source row, as recorded.
        return True

    for row in ordered:
        summary = row.get("summary") or {}
        for gap in summary.get("gaps_named") or ():
            gap_id = str(gap.get("gap_id") or "")
            if not gap_id or gap_id in reversed_gaps:
                continue
            gaps.pop(gap_id, None)
            # The gap's own kind (prerequisite, misconception...) is ``gap_kind``:
            # ``kind`` names the hypothesis entry.
            gaps[gap_id] = {"kind": "named_gap", "gap_kind": gap.get("kind"),
                            **{key: gap.get(key) for key in ("gap_id", "target_kind", "target_id", "source_id")},
                            "source": {"table": "learner_text_gaps", "digest_id": row["id"]}}
        for question in (row.get("valuation") or {}).get("questions") or ():
            body = question.get("question") or {}
            if body.get("purpose") != "discriminating" or not body.get("target_hypotheses"):
                continue
            los = set(_ids(body.get("learning_object_ids") or ())) & lo_ids
            if not los:
                continue
            targets = [dict(h) for h in body.get("target_hypotheses") or () if still_open(h)]
            identity = str(question.get("key") or "")
            rivals.pop(identity, None)
            if not targets:
                continue
            rivals[identity] = {"kind": "rival_explanations", "question": question.get("key"),
                                "learning_object_ids": sorted(los), "target_hypotheses": targets,
                                "raised_by": [dict(r) for r in body.get("raised_by") or ()],
                                "outcome": question.get("outcome"),
                                "source": {"table": "reader_session_digests", "digest_id": row["id"]}}
    return [*gaps.values(), *rivals.values()]


def _prediction_los(vault: Any, repository: Any, rows: Sequence[Mapping[str, Any]]) -> dict[str, set[str]]:
    """Each missed figure prediction's LOs, through its figure's passages
    (Codex review F6: a prediction record names no facet or span of its own)."""

    from learnloop.reader.reader_progression import learning_objects_for_span

    # Both lists that carry a missed prediction (re-review F6): the session's
    # missed predictions and its formative records.
    wanted = sorted({event for row in rows for event in _prediction_events(row.get("summary") or {})})
    if not wanted:
        return {}
    with repository.connection() as connection:
        if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'figure_predictions'"
                              ).fetchone() is None:
            return {}
        marks = ", ".join("?" for _ in wanted)
        found = [dict(r) for r in connection.execute(
            "SELECT p.id AS prediction_id, f.extraction_id, f.span_ids_json, f.input_span_ids_json "
            f"FROM figure_predictions p JOIN interactive_figures f ON f.id = p.figure_id WHERE p.id IN ({marks})",
            wanted)]
    out: dict[str, set[str]] = {}
    for row in found:
        spans: list[str] = []
        for column in ("span_ids_json", "input_span_ids_json"):
            try:
                spans = _ids(json.loads(row.get(column) or "[]"))
            except (TypeError, ValueError):
                spans = []
            if spans:
                break
        los: set[str] = set()
        for span_id in spans:
            los.update(str(lo) for lo in learning_objects_for_span(
                vault, repository, extraction_id=str(row["extraction_id"]), span_id=span_id))
        out[str(row["prediction_id"])] = los
    return out


def _prediction_events(summary: Mapping[str, Any]) -> list[str]:
    """The source events of the summary's missed figure predictions (both
    lists that carry one: missed predictions and formative records)."""

    return [str(event) for key in ("predictions_missed", "observations")
            for record in summary.get(key) or ()
            if isinstance(record, Mapping) and record.get("kind") == "prediction_missed"
            for event in record.get("source_event_ids") or ()]


def _predicts_on(summary: Mapping[str, Any], prediction_los: Mapping[str, set[str]], lo_ids: set[str]) -> bool:
    """Whether a missed prediction of the session resolves, through its
    figure's passages, to one of these LOs (final verify F6)."""

    return any(prediction_los.get(event, set()) & lo_ids for event in _prediction_events(summary))


def _records(rows: Sequence[Mapping[str, Any]], scope: set[str], key: str,
             prediction_los: Mapping[str, set[str]] | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        for record in (row.get("summary") or {}).get(key) or ():
            if not isinstance(record, Mapping):
                continue
            in_scope = _record_in_scope(record, scope)
            if not in_scope and record.get("kind") == "prediction_missed" and prediction_los:
                # A prediction's scope is its figure's passages' LOs (F6).
                in_scope = any(prediction_los.get(str(event), set()) & scope
                               for event in record.get("source_event_ids") or ())
            if in_scope:
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


def _narrated_at(repository: Any, digest_ids: Sequence[str]) -> dict[str, str]:
    """When each digest's narrative was kept: its ``judgment_ledger`` verdict
    (the narrative columns carry no time of their own)."""

    if not digest_ids:
        return {}
    marks = ", ".join("?" for _ in digest_ids)
    with repository.connection() as connection:
        rows = connection.execute(
            f"SELECT left_id, MIN(created_at) AS at FROM judgment_ledger WHERE task = ? AND left_kind = ? "
            f"AND verdict = 'kept' AND left_id IN ({marks}) GROUP BY left_id",
            (NARRATIVE_LEDGER_TASK, NARRATIVE_LEDGER_LEFT, *digest_ids)).fetchall()
    return {str(row["left_id"]): str(row["at"]) for row in rows if row["at"]}


def _narrative(repository: Any, rows: Sequence[Mapping[str, Any]], cutoff: datetime | None) -> dict[str, Any] | None:
    kept = [row for row in rows if row.get("narrative_md")]
    if kept and cutoff is not None:
        # Written before ``as_of`` (Codex review F5): its verdict's time.
        times = _narrated_at(repository, [str(row["id"]) for row in kept])
        kept = [row for row in kept if _before(times.get(str(row["id"])), cutoff)]
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
    (a pure read; None when switched off).

    **The ``as_of`` contract** (orchestrator ruling R2 on final verify F5).
    ``as_of`` bounds the event-timed rows: which digest rows exist (created and
    ended before it), inquiry statuses, follow-up dispositions and dates,
    claim answers, gap reversals, probe-episode closes and the narrative's
    verdict. It does not version a digest row's ``summary_json`` and
    ``valuation_json``: those are the row's latest version, so a re-plan
    after ``as_of`` (part 1 rewrites an ``incomplete`` row in place) shows
    through, as do a rival's facet marginal and a causal factor's pending
    decision. No production caller reconstructs a historical card: the card
    gatherer reads at the decision's own time, and the stored card payload
    (``router_decision_payloads``) is the replay record. A caller that needs
    exact historical cards needs digest versions first (open item, router
    R2)."""

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
    rows = [row for row in rows if _before(row.get("ended_at"), cutoff) and _before(row.get("created_at"), cutoff)]
    # A missed prediction names no facet or span of its own, and the summary's
    # touched LOs need not include its figure's (final verify F6): its
    # provenance (figure, then passage, then LO) is resolved before rows are
    # selected, so a session that touched these LOs only through a figure is
    # kept for its prediction.
    prediction_los = _prediction_los(vault, repository, rows)
    rows = [row for row in rows if _touches(row.get("summary") or {}, los, facets)
            or _predicts_on(row.get("summary") or {}, prediction_los, los)]
    scope = los | facets
    pending = _pending_followups(repository, rows, los, cutoff, as_of)
    activity.update({
        "open_inquiries": _open_inquiries(vault, repository, rows, los, cutoff),
        "assisted_only": _assisted_only(vault, repository, rows, facets, los, cutoff),
        "pending_followups": pending,
        "missed_predictions": _records(rows, scope, "predictions_missed", prediction_los),
        "open_hypotheses": _open_hypotheses(repository, rows, los, cutoff),
        "formative_records": _records(rows, scope, "observations", prediction_los),
        "kept_comparisons": _kept_comparisons(vault, repository, lo_ids, as_of),
        "candidate_actions": _candidate_actions(repository, rows, pending, los),
        # Off: no saved narrative in any payload (Codex review F4).
        "narrative": _narrative(repository, rows, cutoff) if narrative_enabled(vault) else None,
    })
    return activity


def for_card(activity: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """The card's copy (``evidence_sections.reader_activity``), or None when
    there is nothing to say (the card is then the predecessor's, byte for
    byte). Bounded for the card's budget: each list keeps
    :data:`CARD_LIST_LIMIT` entries (the newest; for follow-ups and next
    actions, the first in their order) and ``omitted`` counts the rest.
    ``as_of`` is left out: the card has its own decision time."""

    if not activity or not any(activity.get(name) for name in SECTIONS):
        return None
    out: dict[str, Any] = {"activity_version": activity.get("activity_version", ACTIVITY_VERSION),
                           "authority": activity.get("authority", AUTHORITY)}
    omitted: dict[str, int] = {}
    for name in _LIST_SECTIONS:
        entries = list(activity.get(name) or ())
        if not entries:
            continue
        kept = entries[-CARD_LIST_LIMIT:] if name in _NEWEST_LAST else entries[:CARD_LIST_LIMIT]
        if len(entries) > len(kept):
            omitted[name] = len(entries) - len(kept)
        out[name] = kept
    if activity.get("narrative"):
        out["narrative"] = dict(activity["narrative"])
    if omitted:
        out["omitted"] = omitted
    return out


__all__ = ["ACTIVITY_VERSION", "AUTHORITY", "CARD_LIST_LIMIT", "CARD_SECTION", "SECTIONS", "for_card",
           "narrative_enabled", "reader_activity_enabled", "reader_activity_for_card"]
