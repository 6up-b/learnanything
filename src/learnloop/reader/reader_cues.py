"""Reader workbench RW3a: margin cues from the Guide (spec_reader_workbench_v1 §6).

The Guide already computes, per section, the passages cited by items whose
Learning Object carries an active error (``reader_guidance._passages_by_section``
with ``learner_signal = 'recent_misunderstanding'``), and it reads the
misconception statement through the diagnoser's overlay. RW3a shows those
same passages as quiet margin marks in the text:

* **The margin and the rail agree.** A cue is one of the plan's own passages
  (same span, same Learning Object, the same overlaid error), in the rail's
  order; a section shows at most the learner's density budget of them.
* **Wording is fixed** (G16): a note that says what connects, never what the
  learner lacks, and a "because" line that says where the link came from
  ("from the Guide's citations"). The Guide's "Revisit this to resolve: …"
  stays in the rail.
* **Never on held-out or exam material**: a section with held-out material
  (``reader_guidance.held_out_sections``) and any span the exam predicate
  covers (``content.sources.exam_material``) carry no cue.
* **Display only** (G13): computing cues reads; a tap writes one
  salience-only ``reader_action_invoked`` event and one ``learner_card``
  verdict on the ``passage_cue`` task (``same`` for open and check me,
  ``different`` for not relevant, ``undone`` for its undo). Nothing reaches
  evidence, mastery, projections, FSRS or the plan. "Not relevant" withholds
  that cue (passage and target) until the learner undoes it; a new error on
  the Learning Object is a new target and a new cue.
* The learner's preferences (density, cues off for a book) live in vault
  config (``[cues]``) so they hold across devices; the Reader adds the
  per-screen restraint rules (one mark per screenful, never on the restored
  passage, never while skimming, never animated).

No table: cues are computed from the Guide plan; taps are events and ledger
rows (spec §6.3).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence

from learnloop.attempts.salience_firewall import salience_payload
from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.content.sources.exam_material import exam_material
from learnloop.db.repositories import Repository
from learnloop.db.stores.answered_contracts import answered_contracts
from learnloop.db.stores.judgments import append_judgment
from learnloop.reader.reader_guidance import held_out_sections
from learnloop.substrate.activities import log_interaction_event
from learnloop.vault.required_method import answered_question, fit_presented_prompt

CUES_VERSION = "rw3a-guide-cues-v1"
#: The judgment_ledger task every cue verdict lands on (spec §6.2, §11).
CUE_TASK = "passage_cue"
CUE_LEFT_KIND = "reader_span"
CUE_RIGHT_KIND = "error_event"
#: RW3a's one cue kind: the Guide's passage on something the learner worked on
#: (``◌┆``). RW3b adds "new application" and "try this step first".
CUE_KIND_REVISIT = "revisit"

DENSITIES: tuple[str, ...] = ("off", "fewer", "normal", "more")
#: Marks per section at each density: a display limit the learner owns (D10).
DENSITY_BUDGET: Mapping[str, int] = {"off": 0, "fewer": 1, "normal": 2, "more": 4}

#: A tap on a cue -> its payload event and its learner_card verdict.
CUE_TAP_ACTIONS: Mapping[str, tuple[str, str]] = {
    "opened": ("cue_opened", "same"),
    "check_me": ("cue_check_me", "same"),
    "not_relevant": ("cue_not_relevant", "different"),
    "not_relevant_undone": ("cue_not_relevant_undone", "undone"),
}
#: Preference changes, written by the sidecar with the config write.
CUE_PREFERENCE_EVENTS: tuple[str, ...] = ("cue_density_changed", "cue_source_off", "cue_source_on")
#: Every ``event`` value RW3a's server writes on ``reader_action_invoked``.
SERVER_CUE_EVENTS: tuple[str, ...] = tuple(event for event, _verdict in CUE_TAP_ACTIONS.values()) + CUE_PREFERENCE_EVENTS
#: Where a preference change was made (the funnel's denominators).
PREFERENCE_VIA: tuple[str, ...] = ("footer", "fewer", "popover", "settings", "undo")

# -- fixed templates (G16) ----------------------------------------------------------------
#: What connects. Never what the learner lacks, never a trait, never "error".
NOTE_TEMPLATE = "Connects to something you worked on: {topic}."
#: Why it is there and how the link was found (spec §6.1).
BECAUSE_TEMPLATE = "Because: your answer on {day} · from the Guide's citations"
BECAUSE_UNDATED = "Because: an answer you gave · from the Guide's citations"
#: The screen reader's full sentence for the mark (UX §7.2).
LABEL_TEMPLATE = "Note on this paragraph: {note} {because}"
CUE_TEMPLATES: tuple[str, ...] = (NOTE_TEMPLATE, BECAUSE_TEMPLATE, BECAUSE_UNDATED, LABEL_TEMPLATE)

MAX_PROMPT_CHARS = 220
#: The learner's answer "Open" shows, clipped for the popover (line breaks kept).
MAX_ANSWER_CHARS = 600
MAX_NOT_RELEVANT_CHARS = 1000


class CueError(ValueError):
    """A refused cue request (nothing was written)."""


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def cues_enabled(vault: Any) -> bool:
    """RW3a's kill switch (``cues.enabled``, default on)."""

    section = getattr(vault.config, "cues", None)
    return bool(getattr(section, "enabled", True))


def cue_density(vault: Any) -> str:
    section = getattr(vault.config, "cues", None)
    density = str(getattr(section, "density", "normal") or "normal")
    return density if density in DENSITY_BUDGET else "normal"


def density_budget(density: str) -> int:
    if density not in DENSITY_BUDGET:
        raise CueError(f"unknown cue density {density!r}")
    return DENSITY_BUDGET[density]


def step_down(density: str) -> str:
    """"Fewer marks like this": one notch down (more -> normal -> fewer -> off)."""

    index = DENSITIES.index(density) if density in DENSITIES else DENSITIES.index("normal")
    return DENSITIES[max(0, index - 1)]


def off_sources(vault: Any) -> list[str]:
    section = getattr(vault.config, "cues", None)
    return [str(source) for source in (getattr(section, "off_sources", None) or [])]


def one_per_viewport(vault: Any) -> bool:
    section = getattr(vault.config, "cues", None)
    return bool(getattr(section, "one_per_viewport", True))


# ---------------------------------------------------------------------------
# The cues of one guide plan
# ---------------------------------------------------------------------------

def _digest(parts: Sequence[Any]) -> str:
    return hashlib.sha256(json.dumps(list(parts), sort_keys=True, default=str).encode("utf-8")).hexdigest()


def cue_id_for(extraction_id: str, span_id: str, learning_object_id: str, target_id: str) -> str:
    return "cue_" + _digest([extraction_id, span_id, learning_object_id, target_id])[:24]


def _day(created_at: str | None) -> str | None:
    """"2 Oct" for a timestamp (UTC), or None when it does not parse."""

    try:
        when = parse_utc(created_at)
    except (TypeError, ValueError):
        return None
    if when is None:
        return None
    return f"{when.day} {when.strftime('%b')}"


def render_note(topic: str) -> str:
    return NOTE_TEMPLATE.format(topic=topic.strip().rstrip(".") or "this passage")


def render_because(day: str | None) -> str:
    return BECAUSE_TEMPLATE.format(day=day) if day else BECAUSE_UNDATED


def _clip(text: str | None, limit: int) -> str | None:
    if not text:
        return None
    flat = " ".join(str(text).split())
    return flat if len(flat) <= limit else flat[: limit - 1].rstrip() + "…"


def _clip_question(statement: str | None, method: Any) -> str | None:
    """The answered question for the popover: the statement clipped as before,
    and a required method's instruction after it, whole."""

    if not statement and method is None:
        return None
    if not str(statement or "").strip() and method is None:
        return None
    return fit_presented_prompt(statement or "", method, MAX_PROMPT_CHARS,
                                lambda text, limit: _clip(text, limit) or "")


def _clip_answer(text: str | None, limit: int = MAX_ANSWER_CHARS) -> str | None:
    """The learner's own words, verbatim but for surrounding blank space and a
    clip at ``limit`` (line breaks kept: an answer's shape is part of it)."""

    if not text or not str(text).strip():
        return None
    words = str(text).strip()
    return words if len(words) <= limit else words[: limit - 1].rstrip() + "…"


def _strongest_error(repository: Repository, learning_object_id: str) -> Any | None:
    """The error the Guide's reason names: the same choice ``_learner_signal``
    makes over the diagnoser's overlay (highest severity, then newest)."""

    errors = repository.active_errors_by_learning_object_overlaid(learning_object_id)
    if not errors:
        return None
    return max(errors, key=lambda error: (error.severity, error.created_at))


def _earlier_work(vault: Any, repository: Repository, error: Any, pending: set[str]) -> dict[str, Any]:
    """What "Open" shows (spec §6.1, "the cited attempt, its diagnosis"): when
    the learner answered, on which question, the answer itself in their own
    words, and LearnLoop's model's reading of that answer once it has one.

    The question is the one the answer was given (method-explicit items,
    ``answered_question``): for a method-explicit answer its graded
    contract's statement and frozen required method, the instruction kept
    whole when the popover's clip shortens the statement; otherwise the item
    as it is now, exactly as before."""

    attempt = repository.fetch_practice_attempt(error.attempt_id) if error.attempt_id else None
    item_id = str((attempt or {}).get("practice_item_id") or "") or None
    item = vault.practice_items.get(item_id) if item_id else None
    answered_at = str((attempt or {}).get("created_at") or error.created_at or "") or None
    contract = None
    if attempt is not None:
        with repository.connection() as connection:
            contract = answered_contracts(connection, [str(error.attempt_id)]).get(str(error.attempt_id))
    statement, method = answered_question(item, contract)
    return {
        "attempt_id": error.attempt_id,
        "practice_item_id": item_id,
        "prompt": _clip_question(statement, method),
        "answer": _clip_answer((attempt or {}).get("learner_answer_md")),
        "answered_at": answered_at,
        "answered_on": _day(answered_at),
        "statement": (error.misconception_statement or None),
        "statement_pending": bool(error.attempt_id and error.attempt_id in pending),
    }


def _current_verdicts(repository: Repository, extraction_id: str) -> dict[tuple[str, str], str]:
    """The learner's current verdict per (span, target) on this extraction's cues."""

    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT id, left_id, right_id, verdict, supersedes_id FROM judgment_ledger "
            "WHERE task = ? AND left_kind = ? AND judge = 'learner_card' AND left_id LIKE ?",
            (CUE_TASK, CUE_LEFT_KIND, f"{extraction_id}/%"),
        ).fetchall()
    superseded = {row[4] for row in rows if row[4]}
    current: dict[tuple[str, str], str] = {}
    for row in rows:
        if row[0] in superseded:
            continue
        current[(str(row[1]), str(row[2] or ""))] = str(row[3])
    return current


def cue_candidates(vault: Any, repository: Repository, *, extraction_id: str,
                   plan: Mapping[str, Any]) -> tuple[list[dict[str, Any]], int]:
    """Every cue the plan's sections would carry, in the rail's order per
    section, before the learner's choices (density, not relevant, cues off).
    Returns the candidates and how many passages held-out or exam material
    kept from being one. Held-out material never yields a cue."""

    sections = list(plan.get("sections") or [])
    raw: list[tuple[int, dict[str, Any], dict[str, Any]]] = []
    for ordinal, section in enumerate(sections):
        for passage in section.get("suggested_passages") or []:
            # A passage cited on an earlier reading whose words changed at its
            # place (re-read safety) is shown flagged in the rail; the margin
            # marks only words that are the ones cited.
            if (passage.get("learner_signal") == "recent_misunderstanding"
                    and passage.get("anchor", "current") == "current"):
                raw.append((ordinal, section, passage))
    if not raw:
        return [], 0
    held_sections = held_out_sections(vault, repository, extraction_id, sections)
    material = exam_material(vault, repository)
    pending = set(repository.pending_live_diagnoses_for_active_errors(
        {str(passage["learning_object_id"]) for _ordinal, _section, passage in raw}
    ))
    candidates: list[dict[str, Any]] = []
    held = 0
    rank_in_section: dict[str, int] = {}
    errors: dict[str, Any] = {}
    for ordinal, section, passage in raw:
        span_id = str(passage["span_id"])
        section_id = str(section["id"])
        if section_id in held_sections or material.covers(extraction_id, span_id):
            held += 1
            continue
        learning_object_id = str(passage["learning_object_id"])
        if learning_object_id not in errors:
            errors[learning_object_id] = _strongest_error(repository, learning_object_id)
        error = errors[learning_object_id]
        if error is None:
            continue
        topic = str(passage.get("learning_object_title") or "this idea")
        earlier = _earlier_work(vault, repository, error, pending)
        note = render_note(topic)
        because = render_because(earlier["answered_on"])
        section_rank = rank_in_section.get(section_id, 0)
        rank_in_section[section_id] = section_rank + 1
        span_ids = list(section.get("span_ids") or [])
        candidates.append({
            "cue_id": cue_id_for(extraction_id, span_id, learning_object_id, error.id),
            "kind": CUE_KIND_REVISIT,
            "span_id": span_id,
            "section_id": section_id,
            "section_ordinal": ordinal,
            "position": span_ids.index(span_id) if span_id in span_ids else 0,
            "learning_object_id": learning_object_id,
            "learning_object_title": topic,
            "target_id": error.id,
            "section_rank": section_rank,
            "note": note,
            "because": because,
            "label": LABEL_TEMPLATE.format(note=note, because=because),
            "earlier": earlier,
        })
    return candidates, held


def guide_cues(vault: Any, repository: Repository, *, extraction_id: str,
               plan: Mapping[str, Any]) -> dict[str, Any]:
    """The plan's margin cues within the learner's choices (spec §6.1-6.2).

    Per section, the rail's ``recent_misunderstanding`` passages in the rail's
    order, minus held-out material and cues the learner called not relevant,
    up to the density budget. Ranked for the Reader's spacing rule: each
    section's first cue before any section's second, then in reading order.
    Reads only."""

    density = cue_density(vault)
    budget = DENSITY_BUDGET[density]
    source_id = str(plan.get("source_id") or "")
    source_off = bool(source_id) and source_id in off_sources(vault)
    candidates, held = cue_candidates(vault, repository, extraction_id=extraction_id, plan=plan)
    verdicts = _current_verdicts(repository, extraction_id) if candidates else {}
    withheld = {"held_out": held, "not_relevant": 0, "density": 0, "source_off": 0}
    kept: list[dict[str, Any]] = []
    shown_in_section: dict[str, int] = {}
    for cue in candidates:
        if verdicts.get((f"{extraction_id}/{cue['span_id']}", cue["target_id"])) == "different":
            withheld["not_relevant"] += 1
            continue
        if source_off:
            withheld["source_off"] += 1
            continue
        count = shown_in_section.get(cue["section_id"], 0)
        if count >= budget:
            withheld["density"] += 1
            continue
        shown_in_section[cue["section_id"]] = count + 1
        kept.append({**cue, "section_rank": count})
    kept.sort(key=lambda cue: (cue["section_rank"], cue["section_ordinal"], cue["position"]))
    marks = []
    for rank, cue in enumerate(kept):
        public = {key: value for key, value in cue.items() if key not in ("section_ordinal", "position")}
        marks.append({**public, "rank": rank})
    return {
        "version": CUES_VERSION,
        "density": density,
        "budget_per_section": budget,
        "one_per_viewport": one_per_viewport(vault),
        "source_off": source_off,
        "marks": marks,
        "withheld": withheld,
    }


def find_cue(vault: Any, repository: Repository, *, extraction_id: str, cue_id: str,
             plan: Mapping[str, Any]) -> dict[str, Any]:
    """A cue of this plan by id, whatever the learner's choices (a "not
    relevant" can be undone, a cue from a book switched off still answers);
    held-out material is never a cue. Refused when it is not one."""

    candidates, _held = cue_candidates(vault, repository, extraction_id=extraction_id, plan=plan)
    for cue in candidates:
        if cue["cue_id"] == cue_id:
            return cue
    raise CueError(f"no margin cue {cue_id!r} on this source")


# ---------------------------------------------------------------------------
# Taps (events and learner_card verdicts)
# ---------------------------------------------------------------------------

def record_cue_tap(repository: Repository, *, extraction_id: str, cue: Mapping[str, Any], action: str,
                   text: str | None = None, clock: Clock | None = None) -> dict[str, Any]:
    """Record a tap on a cue: one salience-only event and, when it changes the
    learner's verdict, one ``learner_card`` row on ``passage_cue`` (the
    question is (span, target)); a repeated verdict appends nothing and an
    undo with nothing to undo appends nothing. "Not relevant, because…" text
    stays judge feedback (the verdict's rationale): it is never learner text
    for gaps and never reaches the event. Validated before any write."""

    if action not in CUE_TAP_ACTIONS:
        raise CueError(f"unknown cue action {action!r}")
    event, verdict = CUE_TAP_ACTIONS[action]
    reason = " ".join((text or "").split())[:MAX_NOT_RELEVANT_CHARS] if action == "not_relevant" else ""
    left_id = f"{extraction_id}/{cue['span_id']}"
    right_id = str(cue["target_id"])
    now = utc_now_iso(clock)
    with repository.atomic():
        connection = repository.connection()
        rows = connection.execute(
            "SELECT id, verdict, supersedes_id FROM judgment_ledger WHERE task = ? AND left_kind = ? "
            "AND left_id = ? AND right_kind = ? AND right_id = ? AND judge = 'learner_card'",
            (CUE_TASK, CUE_LEFT_KIND, left_id, CUE_RIGHT_KIND, right_id),
        ).fetchall()
        superseded = {row[2] for row in rows if row[2]}
        current = next((row for row in rows if row[0] not in superseded), None)
        current_verdict = str(current[1]) if current is not None else None
        ledger_id: str | None = None
        changes = verdict != current_verdict and not (verdict == "undone" and current_verdict != "different")
        if changes:
            rationale = {
                "opened": "the learner opened the cue's earlier work",
                "check_me": "the learner asked to be checked on the cue's idea, on their own",
                "not_relevant": "the learner marked the cue not relevant",
                "not_relevant_undone": "the learner undid 'not relevant'",
            }[action]
            if reason:
                rationale = f"{rationale}, because: {reason}"
            ledger_id = append_judgment(
                connection,
                id="cue_v_" + _digest([left_id, right_id, verdict, current[0] if current else None])[:32],
                task=CUE_TASK,
                left_kind=CUE_LEFT_KIND,
                left_id=left_id,
                right_kind=CUE_RIGHT_KIND,
                right_id=right_id,
                judge="learner_card",
                input_hash=_digest([cue.get("cue_id"), cue.get("learning_object_id"), cue.get("note")]),
                verdict=verdict,
                prompt_version=CUES_VERSION,
                rationale=rationale,
                supersedes_id=current[0] if current is not None else None,
                created_at=now,
            )
        event_id = log_interaction_event(
            repository,
            kind="reader_action_invoked",
            origin="learner",
            subject_type="reader_cue",
            subject_id=str(cue["cue_id"]),
            payload=salience_payload({
                "event": event,
                "extraction_id": extraction_id,
                "span_id": cue["span_id"],
                "section_id": cue.get("section_id"),
                "learning_object_id": cue.get("learning_object_id"),
                "target_id": right_id,
                "cue_id": cue["cue_id"],
                "cue_kind": cue.get("kind", CUE_KIND_REVISIT),
                "has_text": bool(reason),
                "verdict": verdict if changes else None,
            }),
            clock=clock,
        )
    return {
        "cue_id": cue["cue_id"],
        "action": action,
        "event_id": event_id,
        "verdict": verdict if changes else current_verdict,
        "ledger_id": ledger_id,
    }


def preference_changes(vault: Any, *, density: str | None = None, source_id: str | None = None,
                       source_off: bool | None = None, via: str = "footer"
                       ) -> tuple[dict[tuple[str, ...], Any], list[dict[str, Any]]]:
    """The ``[cues]`` config updates a preference change makes, and the events
    it logs. Validated before anything is written; no change, no update."""

    if via not in PREFERENCE_VIA:
        raise CueError(f"unknown preference origin {via!r}")
    updates: dict[tuple[str, ...], Any] = {}
    events: list[dict[str, Any]] = []
    if density is not None:
        density_budget(density)
        before = cue_density(vault)
        if density != before:
            updates[("cues", "density")] = density
            events.append({"event": "cue_density_changed", "from": before, "to": density, "via": via})
    if source_off is not None:
        if not source_id:
            raise CueError("switching cues off for a book names the book")
        current = off_sources(vault)
        if source_off and source_id not in current:
            updates[("cues", "off_sources")] = [*current, source_id]
            events.append({"event": "cue_source_off", "source_id": source_id, "via": via})
        elif not source_off and source_id in current:
            updates[("cues", "off_sources")] = [entry for entry in current if entry != source_id]
            events.append({"event": "cue_source_on", "source_id": source_id, "via": via})
    return updates, events


def log_preference_events(repository: Repository, events: Iterable[Mapping[str, Any]], *,
                          extraction_id: str | None = None, clock: Clock | None = None) -> list[str]:
    """Record preference changes (salience only; no learner text)."""

    ids: list[str] = []
    for entry in events:
        payload = {key: value for key, value in entry.items()}
        if extraction_id:
            payload["extraction_id"] = extraction_id
        ids.append(log_interaction_event(
            repository,
            kind="reader_action_invoked",
            origin="learner",
            subject_type="reader_cues",
            subject_id=extraction_id or "cues",
            payload=salience_payload(payload),
            clock=clock,
        ))
    return ids


def preferences(vault: Any, *, source_id: str | None = None) -> dict[str, Any]:
    """The learner's cue preferences, as the Reader and Settings show them."""

    density = cue_density(vault)
    return {
        "enabled": cues_enabled(vault),
        "density": density,
        "budget_per_section": DENSITY_BUDGET[density],
        "one_per_viewport": one_per_viewport(vault),
        "source_off": bool(source_id) and source_id in off_sources(vault),
        "off_source_count": len(off_sources(vault)),
    }


def check_me_request(vault: Any, cue: Mapping[str, Any]) -> dict[str, Any]:
    """What "Check me" asks ``find_practice`` for (spec §6.1): one short item
    on the cue's Learning Object, as an ordinary attempt on your own. The
    question the learner answered is left out (its answer was shown in
    feedback), and so are families whose answer was revealed lately."""

    earlier = cue.get("earlier") or {}
    exclude = [str(earlier["practice_item_id"])] if earlier.get("practice_item_id") else []
    return {
        "query": str(cue.get("learning_object_title") or cue.get("learning_object_id")),
        "constraints": {
            "learning_object_ids": [str(cue["learning_object_id"])],
            "exclude_item_ids": exclude,
            "exclude_revealed_families": True,
            "kinds": "items",
            "rerank": False,
            "limit": 3,
        },
    }


__all__ = [
    "BECAUSE_TEMPLATE",
    "BECAUSE_UNDATED",
    "CUES_VERSION",
    "CUE_KIND_REVISIT",
    "CUE_PREFERENCE_EVENTS",
    "CUE_TAP_ACTIONS",
    "CUE_TASK",
    "CUE_TEMPLATES",
    "CueError",
    "DENSITIES",
    "DENSITY_BUDGET",
    "LABEL_TEMPLATE",
    "MAX_ANSWER_CHARS",
    "NOTE_TEMPLATE",
    "PREFERENCE_VIA",
    "SERVER_CUE_EVENTS",
    "check_me_request",
    "cue_candidates",
    "cue_density",
    "cue_id_for",
    "cues_enabled",
    "density_budget",
    "find_cue",
    "guide_cues",
    "log_preference_events",
    "preference_changes",
    "preferences",
    "record_cue_tap",
    "render_because",
    "render_note",
    "step_down",
]
