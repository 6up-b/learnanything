"""Reader workbench RW6a: "Last time here", the typed session summary and Wrap up
(spec_reader_workbench_v1 §9.1; UX §4.8, S10, S11; gates G25, G31, G50).

Everything here is a **pure read** over the ledgers the Reader already writes
(``question_events``, ``reader_section_progress``, ``reader_authored_questions``,
``workbench_sessions``, ``practice_attempts``, commitments and the reader
envelope); nothing new is stored. The only writes are three salience-only
events on the existing ``reader_action_invoked`` kind (payload ``event``):
``recap_shown`` (the card was on screen), ``recap_dismissed`` (hide it for this
source until the next session) and ``wrap_up_opened`` (ends the offer at the
destination). No model is called and no evidence is read for anything but
display.

* :func:`session_summary` -- the typed per-session summary of §9.1
  (``ReaderSessionSummaryV1``): deterministic from the ledgers, so computed
  twice it is identical (G25). It carries ids, kinds and verdicts, never the
  learner's words (the summary is the class of data the router card is).
* :func:`build_recap` -- the returning card for a source: continue at, Still
  open, Unfinished, Worth a second look, Since last time. Headings carry no
  counts and nothing is overdue (UX U12); evidence status uses the well's
  markers, never a percentage (W2).
* :func:`build_wrap_up` / :func:`wrap_up_offer` -- the three short lists and
  the one-line offer where the learner lands after leaving a source with
  activity (S11). Wrap up's actions are the RPCs the same chips call
  elsewhere; it writes nothing of its own.

W1 tier 1 and 2: salience and routing only. An import-linter contract keeps
everything that writes evidence from importing this module (G50).
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from typing import Any

from learnloop.attempts.salience_firewall import salience_payload
from learnloop.clock import Clock, parse_utc
from learnloop.goals.certification import is_demonstrated_credit
from learnloop.goals.goal_certification import lo_certification
from learnloop.learner.facet_evidence_timeline import facet_evidence_timelines, vault_timeline_snapshot
from learnloop.reader import reader_dialogue as RD
from learnloop.reader import reader_observations as RO
from learnloop.reader import reader_sessions as RS
from learnloop.reader import workbench as WB
from learnloop.reader.reader_guidance import extraction_sections
from learnloop.reader.reader_progression import learning_objects_by_section, learning_objects_for_span
from learnloop.substrate.activities import log_interaction_event
from learnloop.vault.models import learning_object_facet_union

RECAP_VERSION = "rw6a-recap-v1"
SUMMARY_VERSION = "reader-session-summary-v1"
WRAP_UP_VERSION = "rw6a-wrap-up-v1"

#: Payload ``event`` values on ``reader_action_invoked`` (no new kind, §3.4 item 4).
CARD_EVENTS: tuple[str, ...] = ("recap_shown", "recap_dismissed")
WRAP_UP_EVENTS: tuple[str, ...] = ("wrap_up_opened",)
RECAP_EVENTS: tuple[str, ...] = CARD_EVENTS + WRAP_UP_EVENTS

#: RW3a's tap events the summary lists (cues opened or marked not relevant).
CUE_OPEN_EVENTS: tuple[str, ...] = ("cue_opened", "cue_check_me")
CUE_NOT_RELEVANT_EVENT = "cue_not_relevant"
CUE_NOT_RELEVANT_UNDONE = "cue_not_relevant_undone"

EXCERPT_CHARS = 140
TITLE_CHARS = 80
#: Before every ledger time: the start of a window that reads all history.
_EPOCH = "1970-01-01T00:00:00Z"

#: The markers of the well (UX §3.4), the only evidence words the card uses.
MARK_WITH_HELP = "◌"
MARK_DEMONSTRATED = "●"


class RecapError(ValueError):
    """A refused recap request (nothing was written)."""


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def recap_enabled(vault: Any) -> bool:
    """RW6a's card switch (``recap.enabled``, default on)."""

    return bool(getattr(getattr(vault.config, "recap", None), "enabled", True))


def wrap_up_enabled(vault: Any) -> bool:
    """Wrap up's switch (``recap.wrap_up_enabled``, default on)."""

    return bool(getattr(getattr(vault.config, "recap", None), "wrap_up_enabled", True))


# ---------------------------------------------------------------------------
# Small pure helpers
# ---------------------------------------------------------------------------

def excerpt(text: str | None, limit: int = EXCERPT_CHARS) -> str:
    flat = " ".join(str(text or "").split())
    return flat if len(flat) <= limit else flat[: limit - 1].rstrip() + "…"


def _payload(raw: Any) -> dict[str, Any]:
    if isinstance(raw, Mapping):
        return dict(raw)
    try:
        decoded = json.loads(raw or "{}")
    except (TypeError, ValueError):
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _json_list(raw: Any) -> list[Any]:
    try:
        value = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError):
        return []
    return list(value) if isinstance(value, list) else []


def _later(left: str | None, right: str | None) -> bool:
    a, b = _when(left), _when(right)
    return a is not None and b is not None and a > b


def _when(value: str | None) -> datetime | None:
    try:
        return parse_utc(value) if value else None
    except ValueError:
        return None


def help_line(*, book_counted: bool, carried: int) -> str:
    """"help so far: the book" -- what a problem has used, in plain words."""

    parts = (["the book"] if book_counted else []) + (
        [f"{carried} hint{'s' if carried != 1 else ''} on the answer box"] if carried else []
    )
    return "help so far: " + (", ".join(parts) if parts else "none")


def window(session: RS.ReaderSession | None, *, until: str | None = None) -> RS.ReaderSession:
    """A session-shaped window over all history up to ``until`` (or the session's end)."""

    end = until or (session.ended_at if session else _EPOCH)
    return RS.ReaderSession(session.extraction_id if session else "", ("history",), _EPOCH, end)


# ---------------------------------------------------------------------------
# Ledger reads (one source)
# ---------------------------------------------------------------------------

def _inquiry_roots(history: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    """Each exchange's root exchange id (walks the durable parent links)."""

    by_id = {str(e["event_id"]): e for e in history}
    roots: dict[str, str] = {}
    for exchange_id in by_id:
        current, seen = exchange_id, {exchange_id}
        while True:
            parent = by_id[current].get("parent_exchange_id")
            if not parent or parent not in by_id or parent in seen:
                break
            seen.add(parent)
            current = str(parent)
        roots[exchange_id] = current
    return roots


def _action_events(repository: Any, events: Iterable[str]) -> list[dict[str, Any]]:
    wanted = set(events)
    return [
        event for event in repository.reader_interaction_events(kind="reader_action_invoked")
        if (event.get("payload") or {}).get("event") in wanted
    ]


def _workbench_rows(repository: Any, extraction_id: str) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    with repository.connection() as connection:
        sessions = [dict(row) for row in connection.execute(
            "SELECT * FROM workbench_sessions WHERE extraction_id = ? ORDER BY created_at, id", (extraction_id,)
        )]
        ids = [row["id"] for row in sessions]
        steps: dict[str, list[str]] = {}
        if ids:
            marks = ", ".join("?" for _ in ids)
            for row in connection.execute(
                f"SELECT session_id, created_at FROM workbench_steps WHERE session_id IN ({marks}) "
                "ORDER BY created_at, id",
                ids,
            ):
                steps.setdefault(str(row["session_id"]), []).append(str(row["created_at"]))
    return sessions, steps


def _attempts(repository: Any, attempt_ids: Sequence[str]) -> dict[str, dict[str, Any]]:
    wanted = sorted({str(a) for a in attempt_ids if a})
    if not wanted:
        return {}
    marks = ", ".join("?" for _ in wanted)
    with repository.connection() as connection:
        return {str(row["id"]): dict(row) for row in connection.execute(
            f"SELECT * FROM practice_attempts WHERE id IN ({marks})", wanted
        )}


def _canonical_facets(vault: Any, raw: Any) -> list[str]:
    facets: list[str] = []
    for facet in _json_list(raw):
        canonical = vault.canonical_facet_id(str(facet))
        if canonical not in facets:
            facets.append(canonical)
    return facets


def _sections(repository: Any, extraction_id: str) -> dict[str, str]:
    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        return {}
    rows, _blocks, _span_to_section = extraction_sections(ir)
    return {str(row["id"]): str(row["label"]) for row in rows}


def _section_progress(repository: Any, extraction_id: str) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT section_id, revealed_at, completed_at, updated_at FROM reader_section_progress "
            "WHERE extraction_id = ? ORDER BY section_id", (extraction_id,)
        )]


# ---------------------------------------------------------------------------
# The typed per-session summary (§9.1; G25)
# ---------------------------------------------------------------------------

def session_summary(
    vault: Any, repository: Any, *, extraction_id: str, session: RS.ReaderSession, now: datetime,
) -> dict[str, Any]:
    """``ReaderSessionSummaryV1`` for one reader session (a pure read).

    Ids, kinds, statuses and verdicts copied from their rows; no learner text.
    ``now`` only decides which open problems are past
    ``workbench.open_session_days`` (shown as unfinished, never closed)."""

    history = RD.ask_history(repository, extraction_id=extraction_id, branches=True)
    roots = _inquiry_roots(history)
    by_id = {str(e["event_id"]): e for e in history}
    in_session = sorted(
        (e for e in history if session.contains(e.get("created_at"))),
        key=lambda e: (str(e.get("created_at") or ""), str(e["event_id"])),
    )

    def inquiry(root_id: str) -> dict[str, Any]:
        root = by_id[root_id]
        return {
            "root_exchange_id": root_id,
            "question_event_id": root.get("question_event_id"),
            "span_ids": list(root.get("selection_span_ids") or []) or [root["span_id"]],
            "resolution": root.get("resolution") or "open",
            "opened_at": root.get("created_at"),
        }

    opened = [str(e["event_id"]) for e in in_session if roots[str(e["event_id"])] == str(e["event_id"])]
    touched = _touched_roots(in_session, roots)
    resolved_ids = _status_roots(repository, extraction_id, session, by_id, resolution="resolved")
    resolved = [inquiry(r) for r in resolved_ids if (by_id[r].get("resolution") or "open") == "resolved"]
    still_open = [inquiry(r) for r in touched if (by_id[r].get("resolution") or "open") == "open"]

    # Workbench sessions the session worked on (a step written, or a
    # lifecycle event in the window).
    wb_sessions, wb_steps = _workbench_rows(repository, extraction_id)
    wb_events = {
        str(e.get("subject_id"))
        for e in repository.reader_interaction_events(kind="reader_action_invoked", subject_type=WB.SUBJECT_TYPE)
        if session.contains(e.get("created_at"))
    }
    worked = [
        row for row in wb_sessions
        if row["id"] in wb_events or any(session.contains(at) for at in wb_steps.get(row["id"], []))
        or session.contains(row["created_at"])
    ]
    attempts = _attempts(repository, [row["attempt_id"] for row in worked if row.get("attempt_id")])
    workbench = []
    for row in worked:
        attempt = attempts.get(str(row.get("attempt_id") or ""))
        workbench.append({
            "session_id": row["id"],
            "practice_item_id": row["practice_item_id"],
            "status": row["status"],
            # The ladder's levels arrive with RW2b; RW2a records the book and
            # the answer box's carried hints.
            "highest_help_level": None,
            "book_counted": WB.book_counted(row),
            "hints": WB.session_hints(row),
            "attempt_id": row.get("attempt_id"),
            "grade": (
                {"rubric_score": attempt.get("rubric_score"), "correctness": attempt.get("correctness")}
                if attempt else None
            ),
        })

    # Cues (RW3a): opened, and marked not relevant (undo taken into account).
    cue_events = [
        e for e in _action_events(repository, (*CUE_OPEN_EVENTS, CUE_NOT_RELEVANT_EVENT, CUE_NOT_RELEVANT_UNDONE))
        if e["payload"].get("extraction_id") == extraction_id and session.contains(e.get("created_at"))
    ]
    cues_opened = sorted({str(e["payload"].get("cue_id")) for e in cue_events
                          if e["payload"]["event"] in CUE_OPEN_EVENTS})
    not_relevant: dict[str, bool] = {}
    for event in cue_events:
        if event["payload"]["event"] == CUE_NOT_RELEVANT_EVENT:
            not_relevant[str(event["payload"].get("cue_id"))] = True
        elif event["payload"]["event"] == CUE_NOT_RELEVANT_UNDONE:
            not_relevant[str(event["payload"].get("cue_id"))] = False

    observations = RO.observations_for_session(
        vault, repository, extraction_id=extraction_id, session=session, exchanges=history,
    )
    formative = RO.formative_answers(repository, extraction_id=extraction_id, session=session)

    # Gaps named from the session's questions (learner-text gaps).
    question_ids = [str(e["question_event_id"]) for e in in_session if e.get("question_event_id")]
    named = RO.named_gaps(repository, question_ids)
    gaps = [gap for q in question_ids for gap in named.get(q, [])]

    # Facets touched: the problems' items, and the LOs of the inquiries' anchors.
    learning_objects: list[str] = []
    for root_id in touched:
        for span_id in inquiry(root_id)["span_ids"]:
            for lo_id in learning_objects_for_span(vault, repository, extraction_id=extraction_id, span_id=span_id):
                if lo_id not in learning_objects:
                    learning_objects.append(lo_id)
    facets: list[str] = []
    for row in worked:
        item = vault.practice_items.get(str(row.get("practice_item_id") or ""))
        for facet in (item.evidence_facets if item is not None else []):
            canonical = vault.canonical_facet_id(str(facet))
            if canonical not in facets:
                facets.append(canonical)
    for lo_id in learning_objects:
        lo = vault.learning_objects.get(lo_id)
        for facet in (learning_object_facet_union(lo) if lo is not None else []):
            canonical = vault.canonical_facet_id(str(facet))
            if canonical not in facets:
                facets.append(canonical)

    activity_sources = (
        (["inquiry"] if in_session else []) + (["workbench"] if worked else [])
        + (["formative_answer"] if formative else [])
    )
    return {
        "summary_version": SUMMARY_VERSION,
        "extraction_id": extraction_id,
        "session": session.as_dict(),
        "sections_read": _sections_read(repository, extraction_id, session),
        "inquiries": {
            "opened": [inquiry(r) for r in opened],
            "resolved": resolved,
            "still_open": still_open,
        },
        # Every Ask exchange of the session, roots and branches (activity).
        "inquiry_exchanges": [str(e["event_id"]) for e in in_session],
        "workbench": workbench,
        "cues": {"opened": cues_opened, "not_relevant": sorted(c for c, on in not_relevant.items() if on)},
        "predictions_missed": [r.as_dict() for r in observations if r.kind == "prediction_missed"],
        "gaps_named": gaps,
        "learning_objects_touched": sorted(learning_objects),
        "facets_touched": sorted(facets),
        "claims_needing_independent_check": _claims(vault, repository, session, worked, attempts),
        "observations": [r.as_dict() for r in observations],
        # D34: an inquiry, a workbench session, a formative answer or a kept
        # comparison (RW4d, absent). Scrolling, highlights and cue taps don't.
        "activity_sources": activity_sources,
        "activity": bool(activity_sources),
    }


def _touched_roots(in_session: Sequence[Mapping[str, Any]], roots: Mapping[str, str]) -> list[str]:
    """The inquiries (roots) an exchange of the session belongs to, first seen first."""

    touched: list[str] = []
    for exchange in in_session:
        root_id = roots[str(exchange["event_id"])]
        if root_id not in touched:
            touched.append(root_id)
    return touched


def _status_roots(
    repository: Any, extraction_id: str, window: RS.ReaderSession, by_id: Mapping[str, Any],
    *, resolution: str | None = None,
) -> list[str]:
    """Roots whose status was set in ``window`` (to ``resolution`` when given)."""

    found: list[str] = []
    for event in _action_events(repository, ("inquiry_status_set",)):
        payload = event["payload"]
        if payload.get("extraction_id") != extraction_id or not window.contains(event.get("created_at")):
            continue
        root_id = str(payload.get("root_exchange_id") or "")
        if root_id in by_id and (resolution is None or payload.get("resolution") == resolution) and root_id not in found:
            found.append(root_id)
    return found


def _sections_read(repository: Any, extraction_id: str, session: RS.ReaderSession) -> list[dict[str, Any]]:
    out = []
    for row in _section_progress(repository, extraction_id):
        stamps = [row.get("revealed_at"), row.get("completed_at"), row.get("updated_at")]
        if any(session.contains(stamp) for stamp in stamps if stamp):
            out.append({"section_id": row["section_id"], "completed": session.contains(row.get("completed_at"))})
    return out


def _claims(
    vault: Any, repository: Any, session: RS.ReaderSession, worked: Sequence[Mapping[str, Any]],
    attempts: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Facets the session's work was assisted on, with no unassisted success since.

    Assisted (§9.1): a source-visible attempt (the book counted) or one with
    help. RW2b adds help level 3 or more through ``help_assists``. "Since"
    starts with the session, so an own success in it answers the claim too.
    The success is read from the facet's Demonstrated curve (certification
    credit earned unassisted), the evidence system's own definition."""

    assisted: dict[str, dict[str, Any]] = {}
    for row in worked:
        attempt = attempts.get(str(row.get("attempt_id") or ""))
        if attempt is None or not session.contains(attempt.get("created_at")):
            continue
        book = WB.book_counted(row)
        if not book and int(attempt.get("hints_used") or 0) <= 0:
            continue
        for facet in _canonical_facets(vault, attempt.get("evidence_facets_json")):
            claim = assisted.setdefault(facet, {"facet_id": facet, "basis": "source_visible" if book else "help",
                                                "attempt_ids": []})
            if attempt["id"] not in claim["attempt_ids"]:
                claim["attempt_ids"].append(attempt["id"])
            if book:
                claim["basis"] = "source_visible"
    if not assisted:
        return []
    # An unassisted success is what the evidence system itself counts as one:
    # an attempt on the facet's Demonstrated curve whose *effective* grading
    # (its latest epoch: a regrade replaces the attempt's credit) still banks
    # credit, without help or priming, made at or after the session's start.
    # A success regraded to nothing answers nothing (review F3), and neither
    # does embedded credit the embedded-share cap banks as nothing (round 2 F3).
    # Whether it still banks is read on the current state: against the cell's
    # final totals, so a later correction elsewhere in the cell (the direct
    # credit an embedded share leaned on, regraded away) takes it back too
    # (round 3 F2).
    curves = facet_evidence_timelines(vault, repository, sorted(assisted))
    answered = {facet for facet, points in curves.items() if _effective_success_since(points, session.started_at)}
    return [
        {**claim, "attempt_ids": sorted(claim["attempt_ids"])}
        for facet, claim in sorted(assisted.items()) if facet not in answered
    ]


def _effective_success_since(points: Sequence[Any], since: str) -> bool:
    """Some attempt made at or after ``since`` whose latest point still banks
    unassisted, unprimed credit (the attempt's effective grading, after the
    embedded-share cap: what it adds to certification credit now, against
    the cells' final totals)."""

    latest: dict[str, Any] = {}
    first_seen: dict[str, str] = {}
    for point in points:
        latest[point.attempt_id] = point
        first_seen.setdefault(point.attempt_id, point.t)
    return any(
        float(point.attempt_banked_credit) > 1e-9 and not point.assisted and not point.primed
        and not _later(since, first_seen[attempt_id])
        for attempt_id, point in latest.items()
    )


# ---------------------------------------------------------------------------
# Since last time (UX S10): what became demonstrated since the session ended
# ---------------------------------------------------------------------------

def _capabilities_at(points: Sequence[Any], moment: str) -> set[str]:
    """The capabilities a facet had demonstrated credit at, as of ``moment``
    (its curve's last point at or before it; every cell as the ledger banks it)."""

    credit: Sequence[tuple[str, float]] = ()
    for point in points:
        if _later(point.t, moment):
            break
        credit = point.capability_credit
    return {capability for capability, value in credit if is_demonstrated_credit(value)}


def demonstrated_since(
    vault: Any, repository: Any, learning_object_ids: Sequence[str], *, after: str,
) -> list[dict[str, Any]]:
    """The LOs demonstrated now that became so after ``after`` (a pure read).

    An LO counts when ``lo_certification(...).demonstrated`` holds now and the
    same predicate -- every recipe obligation at its capability, one
    alternative per ``any_of`` group, the integration cell -- did not hold at
    ``after``. "As of a moment" replays the grading ledger as it stood then
    (gradings, regrades and corrections written by that moment, novelty and
    discounts included) and reads each facet's capability credit from that
    Demonstrated curve, so a regrade counts when it landed and never rewrites
    what an earlier attempt banked before it (round 2 F1). It is dated by the
    certifying attempt: the point after ``after`` at which the LO last went
    from not demonstrated to demonstrated. Newest first; ties by id (review F1)."""

    los = [vault.learning_objects[lo] for lo in sorted(set(learning_object_ids)) if lo in vault.learning_objects]
    now_demonstrated = [lo for lo in los if lo_certification(vault, repository, lo).demonstrated]
    if not now_demonstrated:
        return []
    facets_by_lo = {
        lo.id: sorted({vault.canonical_facet_id(str(f)) for f in learning_object_facet_union(lo)})
        for lo in now_demonstrated
    }
    facets = sorted({f for fs in facets_by_lo.values() for f in fs})
    snapshot = vault_timeline_snapshot(vault, repository)
    curves = facet_evidence_timelines(vault, repository, facets, snapshot=snapshot)
    curves_then: dict[str, dict[str, list[Any]]] = {}

    def certified(lo: Any, moment: str) -> bool:
        if moment not in curves_then:
            curves_then[moment] = facet_evidence_timelines(vault, repository, facets, snapshot=snapshot,
                                                           as_of=moment)
        then = curves_then[moment]

        def as_of(facet_id: str) -> set[str]:
            return _capabilities_at(then.get(vault.canonical_facet_id(facet_id)) or [], moment)

        return lo_certification(vault, repository, lo, demonstrated=as_of).demonstrated

    rows = []
    for lo in now_demonstrated:
        if certified(lo, after):
            continue
        points = [p for facet in facets_by_lo[lo.id] for p in curves.get(facet) or [] if _later(p.t, after)]
        moments = sorted({p.t for p in points}, key=lambda t: (_when(t), t))
        was, dated = False, None
        for moment in moments:
            now = certified(lo, moment)
            if now and not was:
                dated = moment
            was = now
        if dated is None or not was:
            # The curve and the ledger disagree: claim nothing.
            continue
        at_moment = sorted((p for p in points if p.t == dated), key=lambda p: (float(p.delta) <= 1e-9, p.attempt_id))
        rows.append({
            "learning_object_id": lo.id,
            "title": lo.title,
            "demonstrated_on": dated,
            "attempt_id": at_moment[0].attempt_id if at_moment else None,
        })
    return sorted(rows, key=lambda row: (row["demonstrated_on"], row["learning_object_id"]), reverse=True)


def source_learning_objects(vault: Any, repository: Any, extraction_id: str) -> list[str]:
    """The Learning Objects this source teaches (provenance-linked to a section)."""

    found: set[str] = set()
    for lo_ids in learning_objects_by_section(vault, repository, extraction_id=extraction_id).values():
        found.update(lo_ids)
    return sorted(found)


def since_last_time(vault: Any, repository: Any, *, extraction_id: str, after: str) -> list[dict[str, Any]]:
    """:func:`demonstrated_since` over the real ledger for this source's LOs."""

    return demonstrated_since(vault, repository, source_learning_objects(vault, repository, extraction_id), after=after)


def retired_checks(repository: Any, *, extraction_id: str, after: str) -> list[dict[str, Any]]:
    """Checks retired since as no longer needed (RW6b's re-valuation writes
    them: a ``retired`` commitment event whose detail names the reason
    ``no_longer_needed`` and this source). Nothing on ``main`` writes one yet."""

    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT commitment_id, detail_json, created_at FROM commitment_events "
            "WHERE kind = 'retired' AND created_at > ? ORDER BY created_at, id",
            (after,),
        ).fetchall()
    out = []
    for row in rows:
        detail = _payload(row["detail_json"])
        if detail.get("reason") == "no_longer_needed" and detail.get("extraction_id") == extraction_id:
            out.append({"commitment_id": row["commitment_id"], "retired_at": row["created_at"],
                        "solved_attempt_id": detail.get("solved_attempt_id")})
    return out


# ---------------------------------------------------------------------------
# The card (§9.1, UX §4.8, W12)
# ---------------------------------------------------------------------------

def _dismissed(repository: Any, extraction_id: str, since: str) -> bool:
    return any(
        e["payload"].get("extraction_id") == extraction_id and not _later(since, e.get("created_at"))
        for e in _action_events(repository, ("recap_dismissed",))
    )


def _continue_at(repository: Any, extraction_id: str, session: RS.ReaderSession) -> dict[str, Any] | None:
    labels = _sections(repository, extraction_id)
    touched = [
        row for row in _section_progress(repository, extraction_id)
        if any(session.contains(stamp) for stamp in (row.get("updated_at"), row.get("revealed_at")) if stamp)
    ]
    if not touched:
        return None
    last = max(touched, key=lambda row: (str(row.get("updated_at") or ""), str(row["section_id"])))
    return {"section_id": last["section_id"], "label": labels.get(str(last["section_id"]))}


def build_recap(
    vault: Any, repository: Any, *, extraction_id: str, current_visit_id: str | None, now: datetime,
) -> dict[str, Any]:
    """The returning card for a source, or ``{"recap": None}`` (a pure read).

    ``recap`` is None on a first visit, within the first session, and when
    the learner dismissed it during the current session (``dismissed``)."""

    sessions = RS.sessions_for_source(repository, extraction_id)
    previous, current = RS.split_sessions(sessions, current_visit_id=current_visit_id, now=now,
                                          extraction_id=extraction_id)
    if _dismissed(repository, extraction_id, current.started_at):
        return {"recap": None, "dismissed": True}
    if previous is None:
        return {"recap": None, "dismissed": False}

    history = RD.ask_history(repository, extraction_id=extraction_id, branches=True)
    roots = _inquiry_roots(history)
    by_id = {str(e["event_id"]): e for e in history}
    open_roots = [
        e for e in history
        if roots[str(e["event_id"])] == str(e["event_id"]) and e.get("question_event_id")
        and (e.get("resolution") or "open") == "open"
    ]

    # Worth a second look: last time's formative records, and every earlier
    # "still unclear" whose inquiry is still open (one line per inquiry).
    records = RO.observations_for_session(vault, repository, extraction_id=extraction_id,
                                          session=window(previous), exchanges=history)
    second_look: list[dict[str, Any]] = []
    seen_roots: set[str] = set()
    open_ids = {str(e["event_id"]) for e in open_roots}
    for record in sorted(records, key=lambda r: r.observed_at, reverse=True):
        if record.kind == "still_unclear":
            root_id = record.root_exchange_id or ""
            if root_id not in open_ids or root_id in seen_roots:
                continue
            seen_roots.add(root_id)
            root = by_id[root_id]
            second_look.append({
                "kind": record.kind, "root_exchange_id": root_id, "span_id": root["span_id"],
                "question_md": excerpt(root.get("question_md")), "observed_at": record.observed_at,
                "source_event_ids": list(record.source_event_ids),
            })
        elif previous.contains(record.observed_at):
            second_look.append({
                "kind": record.kind, "root_exchange_id": None,
                "span_id": record.span_ids[0] if record.span_ids else None,
                "question_md": None, "observed_at": record.observed_at,
                "source_event_ids": list(record.source_event_ids), "observed": dict(record.observed),
            })

    still_open = [
        {
            "root_exchange_id": str(e["event_id"]),
            "question_event_id": e.get("question_event_id"),
            "question_md": excerpt(e.get("question_md")),
            "span_id": e["span_id"],
            "anchor_span_ids": list(e.get("selection_span_ids") or []) or [e["span_id"]],
            "opened_at": e.get("created_at"),
        }
        for e in open_roots if str(e["event_id"]) not in seen_roots
    ]

    # Open problems and abandoned ones (§5.4: their steps stay learner work
    # and appear here); an abandoned one says so and offers reopen (review F8).
    unfinished = []
    for summary in WB.sessions_for_source(repository, extraction_id, now=now, open_days=WB.open_session_days(vault)):
        if summary["status"] not in ("open", "abandoned"):
            continue
        row = WB.session_row(repository, summary["session_id"])
        carried = WB.carried_hints(row)
        unfinished.append({
            "session_id": summary["session_id"],
            "status": summary["status"],
            "title": excerpt(str(summary["stem_md"] or "").splitlines()[0] if summary["stem_md"] else "", TITLE_CHARS),
            "step_count": summary["step_count"],
            "help": {"book_counted": bool(summary["book_counted"]), "hints": carried},
            "help_line": help_line(book_counted=bool(summary["book_counted"]), carried=carried),
            "unfinished": bool(summary["unfinished"]),
            "span_ids": list(summary["span_ids"]),
            "updated_at": summary["updated_at"],
        })
    unfinished.sort(key=lambda line: (str(line["updated_at"]), line["session_id"]), reverse=True)

    card = {
        "recap_version": RECAP_VERSION,
        "extraction_id": extraction_id,
        "session": previous.as_dict(),
        "continue_at": _continue_at(repository, extraction_id, previous),
        "still_open": still_open,
        "unfinished": unfinished,
        "worth_a_second_look": second_look,
        "since_last_time": {
            "demonstrated": since_last_time(vault, repository, extraction_id=extraction_id, after=previous.ended_at),
            "checks_retired": retired_checks(repository, extraction_id=extraction_id, after=previous.ended_at),
        },
    }
    return {"recap": card, "dismissed": False}


# ---------------------------------------------------------------------------
# Wrap up (§9.1, UX §4.8, S11)
# ---------------------------------------------------------------------------

def _status_action(action: str, extraction_id: str, root_id: str, resolution: str, trigger: str) -> dict[str, Any]:
    return {"action": action, "rpc": "reader.set_inquiry_status",
            "params": {"extraction_id": extraction_id, "exchange_id": root_id, "resolution": resolution,
                       "trigger": trigger}}


def build_wrap_up(
    vault: Any, repository: Any, *, extraction_id: str, current_visit_id: str | None, now: datetime,
) -> dict[str, Any]:
    """The session's three lists: resolved, still open, worth reinforcing.

    With ``current_visit_id`` (the Reader) the session is the current one,
    running to ``now``; without it (the destination) the source's latest.
    ``available`` is the activity rule (D34)."""

    sessions = RS.sessions_for_source(repository, extraction_id)
    if current_visit_id:
        _previous, session = RS.split_sessions(sessions, current_visit_id=current_visit_id, now=now,
                                               extraction_id=extraction_id)
    elif sessions:
        session = sessions[-1]
    else:
        return {"wrap_up_version": WRAP_UP_VERSION, "available": False, "extraction_id": extraction_id,
                "session": None, "resolved": [], "still_open": [], "worth_reinforcing": []}
    summary = session_summary(vault, repository, extraction_id=extraction_id, session=session, now=now)
    rows_history = RD.ask_history(repository, extraction_id=extraction_id, branches=True)
    history = {str(e["event_id"]): e for e in rows_history}

    def words(root_id: str) -> str:
        return excerpt((history.get(root_id) or {}).get("question_md"))

    # The session's inquiries are the ones it touched, plus any whose status
    # was set from the session's start to now -- so a resolve (or its undo)
    # from Wrap up, in the Reader or where the learner landed, moves a line
    # between the lists instead of dropping it (review F4). The lists follow
    # each inquiry's current status.
    roots = _inquiry_roots(rows_history)
    in_session = sorted(
        (e for e in rows_history if session.contains(e.get("created_at"))),
        key=lambda e: (str(e.get("created_at") or ""), str(e["event_id"])),
    )
    through_now = RS.ReaderSession(session.extraction_id, session.visit_ids, session.started_at,
                                   max(session.ended_at, RS.iso_seconds(now), key=lambda t: (_when(t), t)))
    members = _touched_roots(in_session, roots)
    for root_id in _status_roots(repository, extraction_id, through_now, history):
        if root_id not in members:
            members.append(root_id)

    def spans(root_id: str) -> list[str]:
        root = history[root_id]
        return list(root.get("selection_span_ids") or []) or [root["span_id"]]

    def status(root_id: str) -> str:
        return history[root_id].get("resolution") or "open"

    resolved = [
        {"root_exchange_id": root_id, "question_md": words(root_id),
         "actions": [_status_action("undo", extraction_id, root_id, "open", "undo")]}
        for root_id in members if status(root_id) == "resolved"
    ]
    still_open = [
        {"root_exchange_id": line["root_exchange_id"], "question_md": words(line["root_exchange_id"]),
         "span_ids": line["span_ids"],
         "actions": [
             _status_action("resolve", extraction_id, line["root_exchange_id"], "resolved", "chip"),
             # The RW1a chip: the test_me_later preset on the root's anchor
             # (needs the open reading, so the Reader offers it).
             {"action": "revisit_once", "rpc": "reader.invoke_preset",
              "params": {"preset": "test_me_later", "span_ids": line["span_ids"]}, "where": "reader"},
             # Keep open is the status it already has: nothing is written.
             {"action": "keep_open"},
         ]}
        for line in ({"root_exchange_id": r, "span_ids": spans(r)} for r in members if status(r) == "open")
    ]
    worth: list[dict[str, Any]] = []
    rows = {row["id"]: row for row in _workbench_rows(repository, extraction_id)[0]}
    for line in summary["workbench"]:
        if not (line["book_counted"] or line["hints"]):
            continue
        row = rows.get(line["session_id"]) or {}
        worth.append({
            "kind": "with_help", "marker": MARK_WITH_HELP, "session_id": line["session_id"],
            "title": excerpt(str(row.get("stem_md") or "").splitlines()[0] if row.get("stem_md") else "", TITLE_CHARS),
            "status": line["status"],
            "help_line": help_line(book_counted=line["book_counted"], carried=WB.carried_hints(row) if row else 0),
        })
    for claim in summary["claims_needing_independent_check"]:
        worth.append({"kind": "claim", "marker": MARK_WITH_HELP, "facet_id": claim["facet_id"],
                      "basis": claim["basis"], "attempt_ids": claim["attempt_ids"]})
    for record in summary["observations"]:
        if record["kind"] != "still_unclear":
            worth.append({"kind": record["kind"], "marker": MARK_WITH_HELP,
                          "span_ids": record["span_ids"], "observed": record["observed"]})
    return {
        "wrap_up_version": WRAP_UP_VERSION,
        "available": summary["activity"],
        "extraction_id": extraction_id,
        "session": summary["session"],
        "resolved": resolved,
        "still_open": still_open,
        "worth_reinforcing": worth,
    }


def _source_id(repository: Any, extraction_id: str) -> str | None:
    run = repository.get_extraction_run(extraction_id)
    if run is None:
        return None
    revision = repository.get_source_revision(run["revision_id"])
    return str((revision or {}).get("source_id") or "") or None


def wrap_up_offer(vault: Any, repository: Any, *, now: datetime) -> dict[str, Any] | None:
    """The offer where the learner lands (S11): the most recent reader session
    had activity and no ``wrap_up_opened`` followed its start. A pure read."""

    sessions = RS.all_sessions(repository)
    if not sessions:
        return None
    last = max(sessions, key=lambda s: (s.ended_at, s.started_at, s.session_id))
    opened = any(
        e["payload"].get("extraction_id") == last.extraction_id and not _later(last.started_at, e.get("created_at"))
        for e in _action_events(repository, WRAP_UP_EVENTS)
    )
    if opened:
        return None
    summary = session_summary(vault, repository, extraction_id=last.extraction_id, session=last, now=now)
    if not summary["activity"]:
        return None
    return {"extraction_id": last.extraction_id, "source_id": _source_id(repository, last.extraction_id),
            "session": last.as_dict()}


# ---------------------------------------------------------------------------
# The three events (G31: the only writes)
# ---------------------------------------------------------------------------

def record_recap_event(
    repository: Any, *, extraction_id: str, event: str, visit_id: str | None, clock: Clock | None = None,
) -> str:
    """One salience-only ``reader_action_invoked`` with payload ``event``."""

    if event not in RECAP_EVENTS:
        raise RecapError(f"unknown recap event {event!r}")
    if not extraction_id:
        raise RecapError("a recap event names its source")
    return log_interaction_event(
        repository,
        kind="reader_action_invoked",
        origin="learner",
        subject_type="reader_extraction",
        subject_id=extraction_id,
        payload=salience_payload({"event": event, "extraction_id": extraction_id, "visit_id": visit_id}),
        clock=clock,
    )


__all__ = [
    "CARD_EVENTS",
    "RECAP_EVENTS",
    "RECAP_VERSION",
    "RecapError",
    "SUMMARY_VERSION",
    "WRAP_UP_EVENTS",
    "build_recap",
    "build_wrap_up",
    "demonstrated_since",
    "help_line",
    "recap_enabled",
    "record_recap_event",
    "retired_checks",
    "session_summary",
    "since_last_time",
    "source_learning_objects",
    "wrap_up_enabled",
    "wrap_up_offer",
]
