"""``passage.promoted`` (spec §9.1, §0 item 7): up to four rows at the top of the split menu, from what LearnLoop knows
about the object the menu was opened on, each with its glyph, its label, its reason and an action.

**Candidates.** The cheap rows come from the union read of the object's passages with no model: the learner's own
exchanges with the tutor there and the reasoning the tutor adjusted, the gaps read from their words, their pad lines
linked there, the questions they carry from there, their margin notes, a figure made for the passage, and another
passage the cue judge tied to the same problem. The judged rows (another book's section on the same topic, a passage
that says this in other words) come from correspondents and search through a job (:func:`judged_rows`), checked or
labelled "found by search, not checked". A due check is never a row: nothing about it may show (§12.6.1).

**Order** (:func:`rank`; an orchestrator default the owner may override, recorded in ``docs/reviews/reader-rd5a.md``):
the rows that carry an act of the learner's on this object first, most recent act first; then the rest by their own
judge's rank, checked before unchecked; one row of each kind before a second of any kind; ties by row id; a row the
learner dismissed or marked "not this" on this object is left out. At most four: an attention limit (split-menu
research), never a score cut. No weights.

A row's id is stable for its object, kind and target, so a label given to a row ("opened", "dismiss", "not this",
``proposal_labels`` with ``proposal_kind = 'promoted_row'``) finds it the next time the menu opens on that object.
Display, never evidence; read only.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field, replace
from typing import Any

#: The attention limit of the split menu's promoted rows (spec §9.1: "the limit of four is an attention limit").
CAP = 4
OBJECT_KINDS = ("passage", "cue", "highlight", "note", "window", "pad_line")
DISMISSING = ("dismiss", "not_this")


@dataclass(frozen=True)
class Row:
    row_id: str
    kind: str
    glyph: str
    label: str
    reason: str
    #: What running the row does: ``{verb, ...}`` (open a content reference, open a thread in the companion, open a
    #: pad at a block, show a carried question, open a figure, open What this knows).
    action: Mapping[str, Any]
    #: When the learner's own act behind the row happened (None: no act of theirs, a judge's finding).
    learner_at: str | None = None
    #: Checked by a judge (passage links, judged coverage, a verified search hit); None for the learner's own rows.
    checked: bool | None = None
    #: The row's rank within its own finder (lower first); 0 for the learner's own rows.
    judge_rank: int = 0
    basis: str = "union"  # union | judged
    extra: Mapping[str, Any] = field(default_factory=dict)

    def wire(self) -> dict[str, Any]:
        out = asdict(self)
        out["action"] = dict(self.action)
        out["extra"] = dict(self.extra)
        return out


def object_key(object_kind: str, *, extraction_id: str | None = None, span_id: str | None = None,
               annotation_id: str | None = None, block_id: str | None = None, window_id: str | None = None) -> str:
    """The object a menu was opened on, as one string (what a row's id and its labels are keyed by)."""

    parts = {"passage": [extraction_id, span_id], "cue": [extraction_id, span_id],
             "highlight": [annotation_id or "", extraction_id, span_id], "note": [annotation_id or "", extraction_id,
                                                                                    span_id],
             "window": [window_id or "", extraction_id, span_id], "pad_line": [block_id]}[object_kind]
    return ":".join([object_kind, *[str(part or "") for part in parts]])


def row_id(key: str, kind: str, target: Any) -> str:
    digest = hashlib.sha256(json.dumps([key, kind, target], sort_keys=True).encode()).hexdigest()
    return f"pr_{digest[:24]}"


def _date(stamp: Any) -> str:
    return str(stamp or "")[:10]


def cheap_rows(key: str, places: Sequence[tuple[str, str, Mapping[str, Any]]],
               elsewhere: Sequence[Any] = ()) -> list[Row]:
    """The rows the union read of the object's passages gives (``places``: each passage's reading, span and union
    entry), and another passage the cue judge tied to the same problem (``elsewhere``: passage-link findings)."""

    rows: dict[str, Row] = {}

    def add(kind: str, glyph: str, label: str, reason: str, action: Mapping[str, Any], target: Any, **more: Any) -> None:
        rid = row_id(key, kind, target)
        if rid not in rows:
            rows[rid] = Row(rid, kind, glyph, label, reason, action, **more)
        elif (more.get("learner_at") or "") > (rows[rid].learner_at or ""):
            # The same row reached from another of the object's passages ranks by the learner's latest act on it.
            rows[rid] = replace(rows[rid], learner_at=more["learner_at"])

    for _extraction_id, _span_id, entry in places:
        for exchange in entry.get("exchanges") or ():
            add("question", "?", "open your question in the companion",
                f"you asked the tutor about this on {_date(exchange.get('created_at'))}",
                {"verb": "open", "ref": {"kind": "thread", "root_exchange_id": exchange["question_event_id"]}},
                exchange["question_event_id"], learner_at=str(exchange.get("created_at") or ""))
        stamps = {exchange["question_event_id"]: str(exchange.get("created_at") or "")
                  for exchange in entry.get("exchanges") or ()}
        for adjusted in entry.get("adjustments") or ():
            add("adjustment", "◇", "the tutor adjusted your reasoning here",
                "the tutor corrected how you read this passage",
                {"verb": "open", "ref": {"kind": "thread", "root_exchange_id": adjusted["question_event_id"]}},
                adjusted["gap_id"], learner_at=stamps.get(adjusted["question_event_id"]) or None)
        for gap in entry.get("gaps") or ():
            if gap.get("kind") not in ("misconception", "prerequisite") or gap.get("quality") == "unanchored":
                continue
            label = ("connects to a distinction you worked on" if gap["kind"] == "misconception"
                     else "connects to something you were missing")
            add("gap", "◇", label, f"LearnLoop read your words about this on {_date(gap.get('created_at'))}",
                {"verb": "knows", "gap_id": gap["gap_id"]}, gap["gap_id"], learner_at=str(gap.get("created_at") or ""))
        for block in entry.get("pad_blocks") or ():
            add("your_words", "›", "see your words in your pad", "you linked this passage to a pad line",
                {"verb": "open", "ref": {"kind": "pad", "pad_id": block["pad_id"]},
                 "target": {"block_id": block["block_id"]}},
                block["block_id"], learner_at=str(block.get("created_at") or "") or None)
        for question in entry.get("carried") or ():
            add("carried", "◌", f"you carried: {question['text']}", f"since {_date(question.get('since'))}",
                {"verb": "carried", "carried_id": question["carried_id"]}, question["carried_id"],
                learner_at=str(question.get("since") or ""))
        for annotation in entry.get("annotations") or ():
            if not str(annotation.get("learner_text") or "").strip():
                continue
            add("note", "›", "your margin note", str(annotation["learner_text"])[:80],
                {"verb": "annotation", "annotation_id": annotation["annotation_id"]}, annotation["annotation_id"],
                learner_at=str(annotation.get("created_at") or "") or None)
        for figure in entry.get("figures") or ():
            add("figure", "◇", "a figure made for this passage", "help, not a check",
                {"verb": "figure", "figure_id": figure["figure_id"]}, figure["figure_id"], checked=False,
                judge_rank=0)
    for finding in elsewhere:
        add("next_step", "§", "takes it to the next step", finding.reason,
            {"verb": "open", "ref": finding.target()["content"], "target": finding.target()["target"]},
            [finding.extraction_id, finding.span_id], checked=finding.checked, judge_rank=finding.rank,
            extra={"quote": finding.quote, "judgment_ref": finding.judgment_ref})
    return list(rows.values())


def finding_rows(key: str, findings: Iterable[Any]) -> list[Row]:
    """The judged rows: correspondents and search findings."""

    out: dict[str, Row] = {}
    for finding in findings:
        kind = "correspondent" if finding.found_by == "correspondent" else "elsewhere"
        label = (f"{finding.source_title or 'another source'} treats this too" if kind == "correspondent"
                 else f"{finding.source_title or 'another source'} says this in other words")
        rid = row_id(key, kind, [finding.extraction_id, finding.span_id])
        out.setdefault(rid, Row(rid, kind, "▸" if kind == "correspondent" else "§", label, finding.reason,
                                {"verb": "open", "ref": finding.target()["content"],
                                 "target": finding.target()["target"]},
                                checked=finding.checked, judge_rank=finding.rank, basis="judged"))
    return list(out.values())


def rank(rows: Iterable[Row], *, dismissed: Iterable[str] = (), cap: int = CAP) -> list[Row]:
    """Option A (an orchestrator default the owner may override): the learner's history most recent first; then the
    rest by their own judge's rank, checked before unchecked; one of each kind before a second; ties by row id;
    dismissed or "not this" rows left out; at most ``cap``."""

    gone = set(dismissed)
    standing = [row for row in rows if row.row_id not in gone]
    # Most recent act first; a tie on the time keeps the smaller id first (the sort is stable).
    acted = sorted((row for row in standing if row.learner_at), key=lambda row: row.row_id)
    acted.sort(key=lambda row: row.learner_at or "", reverse=True)
    others = sorted((row for row in standing if not row.learner_at),
                    key=lambda row: (0 if row.checked else 1, row.judge_rank, row.row_id))
    ordered = acted + others
    first, rest, kinds = [], [], set()
    for row in ordered:
        (rest if row.kind in kinds else first).append(row)
        kinds.add(row.kind)
    return (first + rest)[:cap]


def dismissed_rows(labels: Iterable[Mapping[str, Any]]) -> set[str]:
    return {str(label["proposal_id"]) for label in labels if label.get("label") in DISMISSING}


__all__ = ["CAP", "DISMISSING", "OBJECT_KINDS", "Row", "cheap_rows", "dismissed_rows", "finding_rows", "object_key",
           "rank", "row_id"]
