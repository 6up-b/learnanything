"""Router R2a: ``LearnerStateCardV1``, the learner as one router decision sees it.

spec_action_router_v1 §4 and plan_router_r2_v1 §3.6. The card is rebuilt from
the ledger at each block boundary, built and stored (R2a sends it nowhere;
R2b's models will read it), and never edited by a model. This module is the
pure builder: typed fields plus text sections, the token budget, and a hash.
The caller (``daily_plan.router_card``) gathers the inputs with bounded reads
and applies the leakage rules before anything reaches here:

* no reference solution, answer key, rubric or source text;
* nothing about a candidate item beyond its topic, minutes and kind (no stem
  of an item the learner has not attempted);
* no exam material and nothing from a surface reserved for an assessment;
* a grade held for review is "held for review", never a score;
* an answer whose key is not verified says so.

**Budget** (``router.card_token_budget``, D8): when the rendered card is over
budget, older successes leave the recent-work section first, then older answer
excerpts and stems, then older attempts; typed fields never drop (TE0's
7-day confidence events go before all of these, oldest first).
**Hash**: the SHA-256 of the canonical JSON of the typed card and its text, on
the decision row (``card_hash``) and with the stored payload.

**Confidence** (teacher TE0, spec_teacher_v1 §15.2; ``learner_state_card_v2``):
each recent attempt line carries its confidence event in words (the tap and
the grader's hedge read with the outcome, "marked 5/5 sure; wrong"), the
7-day window lists the candidate topics' events, and the card states the
limit when the taps so far do not span the scale ("your taps so far are all
4-5"). Never raw scalars and never threshold counts: the reading models
decide what counts as confident. The caller renders the events
(``learnloop.confidence_events``); with no confidence data a v2 card's text
and typed fields are a v1 card's, byte for byte, and only the version
label differs. With the kill switch ``teacher.confidence_events_enabled``
off (``CardInputs.confidence_enabled``) the card is a v1 card, label too.
The 7-day section is bounded by the caller (per topic) and is the first
thing the token budget trims, oldest events first (each shown attempt's
line keeps its own event); what was left out is stated
(``confidence_omitted``, review F3).

A leaf module (the router package): no imports beyond the standard library.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Any

CARD_VERSION = "learner_state_card_v2"
#: The predecessor (before TE0): the same card without confidence events.
PREDECESSOR_CARD_VERSION = "learner_state_card_v1"
#: router.card_token_budget's default (D8).
DEFAULT_TOKEN_BUDGET = 16_000
EXCERPT_LIMIT = 400
STEM_LIMIT = 200
STATEMENT_LIMIT = 300

#: The typed sections, in order. ``evidence_sections`` is the registry hook
#: (§15.1 teach-back summaries, §15.5 the surface-gap signal): a later stage
#: adds a typed section there without changing this card's version scheme.
TYPED_SECTIONS: tuple[str, ...] = (
    "decision", "session", "intent", "candidates", "learning_objects", "interaction_7d",
    "confidence_7d", "open_hypotheses", "unknowns", "self_reports", "evidence_sections",
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def estimate_tokens(value: Any) -> int:
    """UTF-8 bytes / 4, rounded up (the Slice 1 estimator the V3 renderer uses)."""

    text = value if isinstance(value, str) else canonical_json(value)
    return math.ceil(len(text.encode("utf-8")) / 4)


def excerpt(text: Any, limit: int) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


@dataclass(frozen=True)
class CardInputs:
    """Everything the card renders, gathered and filtered by the caller."""

    decision: Mapping[str, Any]
    session: Mapping[str, Any]
    intent: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    candidates: Sequence[Mapping[str, Any]] = ()
    learning_objects: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    interaction_7d: Mapping[str, Any] = field(default_factory=dict)
    open_hypotheses: Sequence[Mapping[str, Any]] = ()
    unknowns: Sequence[str] = ()
    self_reports: Sequence[Mapping[str, Any]] = ()
    #: newest first; each: attempt_id, at, learning_object_id, topic, kind,
    #: result (correct | partial | incorrect | held_for_review | not_graded),
    #: hints_used, key_status, stem (the pinned revision's question, or None),
    #: stem_note (why a shown attempt has no question), answer (or None) and,
    #: when the attempt has a tap or a hedge read, confidence (its event in words)
    recent_work: Sequence[Mapping[str, Any]] = ()
    evidence_sections: Mapping[str, Any] = field(default_factory=dict)
    #: TE0: per candidate topic id, its confidence events in the 7-day window,
    #: newest first: each {"attempt_id", "at", "event"}. Empty: no section.
    confidence_7d: Mapping[str, Sequence[Mapping[str, Any]]] = field(default_factory=dict)
    #: TE0: the stated limit when the taps so far do not span the scale.
    confidence_limit: str | None = None
    #: TE0: events the caller left out of ``confidence_7d`` by its per-topic bound.
    confidence_omitted: int = 0
    #: TE0's kill switch (``teacher.confidence_events_enabled``): off, the
    #: card is the predecessor's (``PREDECESSOR_CARD_VERSION``).
    confidence_enabled: bool = True


@dataclass(frozen=True)
class LearnerStateCard:
    card_version: str
    json: Mapping[str, Any]
    text: str
    card_hash: str
    tokens: int
    truncation: Mapping[str, Any]

    def payload(self) -> dict[str, Any]:
        """What the decision stores (``router_decision_payloads``, kind card)."""

        return {"card_version": self.card_version, "card_hash": self.card_hash, "json": dict(self.json),
                "text": self.text, "tokens": self.tokens, "truncation": dict(self.truncation)}


def _successful(entry: Mapping[str, Any]) -> bool:
    return entry.get("result") == "correct"


def _work_line(entry: Mapping[str, Any]) -> str:
    parts = [str(entry.get("at") or "")[:10], str(entry.get("topic") or entry.get("learning_object_id") or "")]
    if entry.get("kind"):
        parts.append(str(entry["kind"]).replace("_", " "))
    result = str(entry.get("result") or "not_graded")
    parts.append("held for review (no score yet)" if result == "held_for_review" else result.replace("_", " "))
    hints = int(entry.get("hints_used") or 0)
    parts.append("no hints" if hints == 0 else f"{hints} hint{'s' if hints != 1 else ''}")
    if entry.get("confidence"):
        parts.append(str(entry["confidence"]))
    if entry.get("key_status") == "unverified":
        parts.append("answer key not verified")
    if entry.get("withheld"):
        parts.append(f"question and answer withheld ({entry['withheld']})")
    elif entry.get("stem_note"):
        parts.append(str(entry["stem_note"]))
    line = "- " + " · ".join(part for part in parts if part)
    if entry.get("stem"):
        line += f"\n  question: {entry['stem']}"
    if entry.get("answer"):
        line += f"\n  answer: {entry['answer']}"
    return line


def _lo_line(lo_id: str, row: Mapping[str, Any]) -> str:
    bits = [f"- {row.get('title') or lo_id}: {str(row.get('status') or 'unknown').replace('_', ' ')}"]
    predictor = row.get("predictor") or {}
    if predictor.get("p_success") is not None:
        low, high = predictor.get("low"), predictor.get("high")
        interval = f" ({low:.2f}-{high:.2f})" if low is not None and high is not None else ""
        bits.append(f"predicted success {predictor['p_success']:.2f}{interval}")
    if row.get("recall_now") is not None:
        bits.append(f"recall now {float(row['recall_now']):.2f}")
    evidence = row.get("evidence") or {}
    if evidence:
        bits.append(
            f"{evidence.get('graded', 0)} graded ({evidence.get('correct', 0)} correct, {evidence.get('partial', 0)} "
            f"partial, {evidence.get('incorrect', 0)} incorrect, {evidence.get('held', 0)} held), "
            f"{evidence.get('assisted', 0)} assisted (hints or a primed redo)"
        )
    if row.get("last_attempt_at"):
        bits.append(f"last {str(row['last_attempt_at'])[:10]}")
    ad = row.get("adaptive_difficulty")
    if ad:
        # Adaptive difficulty AD2+AD3 (spec §10.1): readiness numbers, predictions.
        if ad.get("untested"):
            bits.append(f"AD prediction: {float(ad.get('p_band_next') or 0):.2f} chance the next level lands in the "
                        "practice band; untested")
        else:
            bits.append(f"AD prediction: {float(ad.get('p_band_next') or 0):.2f} chance the next level lands in the "
                        f"practice band; {float(ad.get('p_bar_at_top') or 0):.2f} predicted at the top level")
    return "; ".join(bits)


def render_text(card: Mapping[str, Any]) -> str:
    """The card's text sections (deterministic from the typed card)."""

    session = card.get("session") or {}
    lines = ["# Session"]
    lines.append(
        f"Plan {session.get('plan_kind')}: {session.get('minutes_left')} of {session.get('minutes_budget')} min left; "
        f"items left {session.get('items_left') if session.get('items_left') is not None else 'no cap'}."
    )
    lines.append(
        f"Days since last activity: {session.get('days_since_last_activity')}; streak {session.get('streak_days')} days"
        + ("; re-entry after a break." if session.get("reentry") else ".")
    )
    lines.append("# Candidates")
    for candidate in card.get("candidates") or ():
        topics = ", ".join(candidate.get("topics") or ()) or candidate.get("section") or "-"
        flags = "reversible" if candidate.get("reversible", True) else "irreversible (only the rule may pick it)"
        lines.append(
            f"- [{candidate.get('ref')}] {candidate.get('kind')} · {candidate.get('est_minutes')} min · "
            f"{candidate.get('item_count', 0)} items · {topics} · {flags} · reason {candidate.get('reason_code')}"
        )
    lines.append("# Topics")
    for lo_id, row in sorted((card.get("learning_objects") or {}).items()):
        lines.append(_lo_line(lo_id, row))
    signals = card.get("interaction_7d") or {}
    lines.append("# Last 7 days")
    lines.append(", ".join(f"{key} {value}" for key, value in sorted(signals.items())) or "nothing recorded")
    confidence = card.get("confidence_7d") or {}
    omitted = int(card.get("confidence_omitted") or 0)
    if confidence or card.get("confidence_limit") or omitted:
        # TE0 (spec_teacher_v1 §15.2): each tap or hedge read with its
        # outcome, never a count; absent with no confidence data.
        lines.append("# Confidence, last 7 days (taps and the grader's hedge reads, newest first)")
        titles = {lo_id: (row or {}).get("title") for lo_id, row in (card.get("learning_objects") or {}).items()}
        for lo_id, events in sorted(confidence.items(), key=lambda pair: str(titles.get(pair[0]) or pair[0])):
            shown = "; ".join(f"{str(event.get('at') or '')[:10]} {event.get('event')}" for event in events)
            lines.append(f"- {titles.get(lo_id) or lo_id}: {shown}")
        if not confidence and not omitted:
            lines.append("none on these topics")
        if omitted:
            lines.append(f"({omitted} older confidence event{'s' if omitted != 1 else ''} left out)")
        if card.get("confidence_limit"):
            lines.append(f"({card['confidence_limit']})")
    lines.append("# Open problems")
    hypotheses = card.get("open_hypotheses") or ()
    if not hypotheses:
        lines.append("none recorded")
    for entry in hypotheses:
        statement = entry.get("statement") or (
            f"statement withheld ({entry['withheld']})" if entry.get("withheld") else ""
        )
        lines.append(
            f"- {entry.get('topic') or entry.get('learning_object_id')}: {entry.get('kind')} "
            f"({entry.get('status')}, since {str(entry.get('since') or '')[:10]}): {statement}".rstrip()
        )
    lines.append("# Unknowns")
    unknowns = card.get("unknowns") or ()
    lines.extend(f"- {unknown}" for unknown in unknowns)
    if not unknowns:
        lines.append("none")
    lines.append("# Self-reports")
    reports = card.get("self_reports") or ()
    if not reports:
        lines.append("none recorded")
    for report in reports:
        lines.append(f"- {str(report.get('at') or '')[:10]} {report.get('topic') or ''}: {report.get('report')}".rstrip())
    teach_backs = (card.get("evidence_sections") or {}).get("teach_back_summaries") or ()
    if teach_backs:
        # Router R2c (spec §15.1): typed evidence from graded teach-back dialogues.
        lines.append("# Teach-back summaries (newest first)")
        for entry in teach_backs:
            lines.append(f"- {str(entry.get('at') or '')[:10]} {entry.get('topic') or ''} (attempt {entry.get('attempt_id')})")
            for label, key in (("explained correctly", "explained_correctly"), ("missing or wrong", "missing_or_wrong"),
                               ("in their words", "learner_words")):
                points = [str(point) for point in entry.get(key) or ()]
                if points:
                    lines.append(f"  {label}: " + "; ".join(points))
    lines.append("# Recent graded work (newest first)")
    work = card.get("recent_work") or ()
    if not work:
        lines.append("none")
    lines.extend(_work_line(entry) for entry in work)
    truncation = card.get("truncation") or {}
    if any(truncation.get(key) for key in ("dropped_successes", "dropped_excerpts", "dropped_attempts")):
        lines.append(
            f"(over the card budget: {truncation.get('dropped_successes', 0)} older successes, "
            f"{truncation.get('dropped_excerpts', 0)} older excerpts and {truncation.get('dropped_attempts', 0)} "
            "older attempts left out)"
        )
    return "\n".join(lines) + "\n"


#: The card's version when it carries adaptive difficulty's fields (spec §10.1:
#: the card's version moves with them; without them the card is unchanged).
AD_CARD_VERSION = CARD_VERSION + "+ad23"


def _card_version(inputs: CardInputs) -> str:
    base = CARD_VERSION if inputs.confidence_enabled else PREDECESSOR_CARD_VERSION
    return base + "+ad23" if any(
        "adaptive_difficulty" in row for row in (inputs.learning_objects or {}).values()) else base


def _assemble(inputs: CardInputs, work: list[dict[str, Any]], truncation: Mapping[str, Any],
              confidence: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
              confidence_dropped: int = 0) -> dict[str, Any]:
    card = {
        "card_version": _card_version(inputs),
        "decision": dict(inputs.decision),
        "session": dict(inputs.session),
        "intent": {key: dict(value) for key, value in sorted(inputs.intent.items())},
        "candidates": [dict(entry) for entry in inputs.candidates],
        "learning_objects": {key: dict(value) for key, value in sorted(inputs.learning_objects.items())},
        "interaction_7d": dict(inputs.interaction_7d),
        "open_hypotheses": [dict(entry) for entry in inputs.open_hypotheses],
        "unknowns": list(inputs.unknowns),
        "self_reports": [dict(entry) for entry in inputs.self_reports],
        "recent_work": work,
        "evidence_sections": dict(inputs.evidence_sections),
        "truncation": dict(truncation),
    }
    # TE0: present only with confidence data, so a card without any is the
    # predecessor's card in every typed field (only the version differs).
    events = inputs.confidence_7d if confidence is None else confidence
    events = {lo: rows for lo, rows in events.items() if rows}
    if events:
        card["confidence_7d"] = {lo: [dict(event) for event in rows] for lo, rows in sorted(events.items())}
    if inputs.confidence_limit:
        card["confidence_limit"] = inputs.confidence_limit
    omitted = int(inputs.confidence_omitted or 0) + int(confidence_dropped)
    if omitted:
        card["confidence_omitted"] = omitted
    return card


def _drop_oldest_event(confidence: dict[str, list[dict[str, Any]]]) -> bool:
    """Remove the oldest 7-day confidence event of any topic (each list is
    newest first); False when none is left."""

    tails = [(str(rows[-1].get("at") or ""), str(rows[-1].get("attempt_id") or ""), lo)
             for lo, rows in confidence.items() if rows]
    if not tails:
        return False
    confidence[min(tails)[2]].pop()
    return True


def build_card(inputs: CardInputs, *, token_budget: int = DEFAULT_TOKEN_BUDGET) -> LearnerStateCard:
    """The card for one decision, within ``token_budget`` (deterministic)."""

    work = [
        {
            **dict(entry),
            "stem": excerpt(entry["stem"], STEM_LIMIT) if entry.get("stem") else None,
            "answer": excerpt(entry["answer"], EXCERPT_LIMIT) if entry.get("answer") else None,
        }
        for entry in inputs.recent_work
    ]
    dropped = {"dropped_successes": 0, "dropped_excerpts": 0, "dropped_attempts": 0}
    confidence = {lo: [dict(event) for event in rows] for lo, rows in inputs.confidence_7d.items()}
    confidence_dropped = 0

    def size() -> int:
        card = _assemble(inputs, work, dropped, confidence, confidence_dropped)
        return estimate_tokens(card) + estimate_tokens(render_text(card))

    # TE0 (review F3): the 7-day confidence events first, oldest first; each
    # shown attempt's line keeps its own event, and the omission is stated.
    while size() > token_budget and _drop_oldest_event(confidence):
        confidence_dropped += 1
        dropped["dropped_confidence_events"] = confidence_dropped

    # Older successes first (the oldest entries are at the end, newest first).
    while size() > token_budget:
        index = next((i for i in range(len(work) - 1, -1, -1) if _successful(work[i])), None)
        if index is None:
            break
        work.pop(index)
        dropped["dropped_successes"] += 1
    # Then older excerpts (stems and answers).
    while size() > token_budget:
        index = next((i for i in range(len(work) - 1, -1, -1) if work[i].get("stem") or work[i].get("answer")), None)
        if index is None:
            break
        work[index] = {**work[index], "stem": None, "answer": None}
        dropped["dropped_excerpts"] += 1
    # Then older attempts. Typed fields never drop.
    while size() > token_budget and work:
        work.pop()
        dropped["dropped_attempts"] += 1
    card = _assemble(inputs, work, dropped, confidence, confidence_dropped)
    text = render_text(card)
    digest = hashlib.sha256(canonical_json({"json": card, "text": text}).encode("utf-8")).hexdigest()
    return LearnerStateCard(
        card_version=_card_version(inputs),
        json=card,
        text=text,
        card_hash=digest,
        tokens=estimate_tokens(card) + estimate_tokens(text),
        truncation=dropped,
    )


__all__ = [
    "AD_CARD_VERSION",
    "CARD_VERSION",
    "PREDECESSOR_CARD_VERSION",
    "CardInputs",
    "DEFAULT_TOKEN_BUDGET",
    "LearnerStateCard",
    "TYPED_SECTIONS",
    "build_card",
    "canonical_json",
    "estimate_tokens",
    "excerpt",
    "render_text",
]
