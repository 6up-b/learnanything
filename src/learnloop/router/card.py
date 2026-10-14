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
excerpts and stems, then older attempts; typed fields never drop.
**Hash**: the SHA-256 of the canonical JSON of the typed card and its text, on
the decision row (``card_hash``) and with the stored payload.

A leaf module (the router package): no imports beyond the standard library.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Any

CARD_VERSION = "learner_state_card_v1"
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
    "open_hypotheses", "unknowns", "self_reports", "evidence_sections",
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
    #: hints_used, key_status, stem (or None), answer (or None)
    recent_work: Sequence[Mapping[str, Any]] = ()
    evidence_sections: Mapping[str, Any] = field(default_factory=dict)


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
    if entry.get("key_status") == "unverified":
        parts.append("answer key not verified")
    if entry.get("withheld"):
        parts.append(f"question and answer withheld ({entry['withheld']})")
    line = "- " + " · ".join(part for part in parts if part)
    if entry.get("stem"):
        line += f"\n  question: {entry['stem']}"
    if entry.get("answer"):
        line += f"\n  answer: {entry['answer']}"
    return line


def _lo_line(lo_id: str, row: Mapping[str, Any]) -> str:
    bits = [f"- {row.get('title') or lo_id}: {row.get('status') or 'unknown'}"]
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
            f"{evidence.get('assisted', 0)} with hints"
        )
    if row.get("last_attempt_at"):
        bits.append(f"last {str(row['last_attempt_at'])[:10]}")
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
    lines.append("# Open problems")
    hypotheses = card.get("open_hypotheses") or ()
    if not hypotheses:
        lines.append("none recorded")
    for entry in hypotheses:
        lines.append(
            f"- {entry.get('topic') or entry.get('learning_object_id')}: {entry.get('kind')} "
            f"({entry.get('status')}, since {str(entry.get('since') or '')[:10]}): {entry.get('statement') or ''}".rstrip()
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


def _assemble(inputs: CardInputs, work: list[dict[str, Any]], truncation: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "card_version": CARD_VERSION,
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

    def size() -> int:
        card = _assemble(inputs, work, dropped)
        return estimate_tokens(card) + estimate_tokens(render_text(card))

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
    card = _assemble(inputs, work, dropped)
    text = render_text(card)
    digest = hashlib.sha256(canonical_json({"json": card, "text": text}).encode("utf-8")).hexdigest()
    return LearnerStateCard(
        card_version=CARD_VERSION,
        json=card,
        text=text,
        card_hash=digest,
        tokens=estimate_tokens(card) + estimate_tokens(text),
        truncation=dropped,
    )


__all__ = [
    "CARD_VERSION",
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
