"""Deterministic composition of a repaired trace from its stored parts.

A ``repaired_trace`` is auditable *by construction*: ``repaired_answer_md`` is
never trusted as an independent copy, it is recomposed server-side from
``learner_work_prefix + regenerated_work``. That composition is only honest if
the prefix really is the learner's preserved work, which is what this module
derives.

Two failures motivated it, both from one live exhibit (exam attempt on
``pi_what_makes_log_transport_strategy``):

1. The model declared ``learner_work_prefix`` as the learner's ENTIRE answer,
   hedge included ("... but I'm not sure what to do from here"), while its own
   ``preserve_refs`` quote covered only the first clause. The prefix was checked
   for being verbatim but never for agreeing with the model's own preserve
   judgement, so the hedge was certified as preserved work.
2. The insertion anchor was ``missing_required_step`` with null offsets — an
   end-append — and nothing required a separator, so the regenerated solution
   was pasted mid-sentence directly after the hedge.

Everything here is a pure function of stored fields (the learner answer and the
suggestion payload), so rebuild/regrade paths reproduce it exactly. Nothing here
can fail a grade: a disagreement between the model-reported prefix and the
derived one is recorded as telemetry, the same way ``resolve_quote_anchor``
records ``model_reported_char_start`` rather than rejecting the measurement.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


#: Closed vocabulary for where ``learner_work_prefix`` came from. Mirrors
#: ``ANCHOR_BASES``: deterministic server derivation outranks a model report.
PREFIX_BASES = (
    "model_reported",
    "derived_from_preserve_refs",
)

#: Closed vocabulary for how the regenerated suffix was joined to the prefix.
SPLICE_JOINS = (
    "verbatim",
    "paragraph_break_inserted",
)


# Sentence terminators, including any trailing closing quotes/brackets.
_SENTENCE_END = re.compile(r"[.!?]+[\"')\]”’]*")
# Coordinators and subordinators strong enough to end a clause. The boundary is
# the whitespace run *before* the word, so the conjunction starts the repair
# rather than trailing the preserved work.
_CLAUSE_WORDS = (
    "but",
    "however",
    "although",
    "though",
    "yet",
    "so",
    "because",
    "since",
    "while",
    "whereas",
    "unless",
    "and",
    "or",
    "nor",
    "then",
    "therefore",
    "thus",
)
_CONJUNCTION = re.compile(
    r"\s+(?:" + "|".join(_CLAUSE_WORDS) + r")\b", re.IGNORECASE
)
# Intra-sentence punctuation. The boundary is *past* the mark, so a preserved
# clause keeps its own comma rather than handing it to the repair.
_PUNCT_BREAK = re.compile(r"[,;:—–]")
# End of a line's content (before the newline and any trailing spaces).
_LINE_END = re.compile(r"[ \t]*\n")

_PARAGRAPH_BREAK_AT_END = re.compile(r"\n[ \t]*\n[ \t]*\Z")
_PARAGRAPH_BREAK_AT_START = re.compile(r"\A[ \t]*\n[ \t]*\n")
_NEWLINE_AT_END = re.compile(r"\n[ \t]*\Z")
_NEWLINE_AT_START = re.compile(r"\A[ \t]*\n")


@dataclass(frozen=True)
class PreservedPrefix:
    """The server's answer to "how much of this answer is the learner's?"."""

    text: str
    basis: str
    #: End of the declared preserve-span union, before outward snapping.
    declared_end: int
    #: End actually used, after snapping to a clause/sentence boundary.
    snapped_end: int


@dataclass(frozen=True)
class SplicedAnswer:
    repaired_answer_md: str
    #: The suffix as actually composed — ``repaired_answer_md`` is exactly
    #: ``prefix + regenerated_work``, so the stored trace stays self-consistent.
    regenerated_work: str
    join: str


def clause_boundaries(answer: str) -> list[int]:
    """Offsets in ``answer`` that a preserved prefix may legitimately end at.

    A boundary must be followed by whitespace or be the end of the text, which
    is what makes "never cut mid-word" structural rather than a separate pass:
    ``3.5`` and ``1,000`` produce no boundary inside the token because the
    character after the mark is not whitespace.
    """

    n = len(answer)
    candidates: set[int] = {n}
    for match in _SENTENCE_END.finditer(answer):
        candidates.add(match.end())
    for match in _CONJUNCTION.finditer(answer):
        candidates.add(match.start())
    for match in _PUNCT_BREAK.finditer(answer):
        candidates.add(match.end())
    for match in _LINE_END.finditer(answer):
        candidates.add(match.start())
    return sorted(
        offset
        for offset in candidates
        if 0 < offset <= n and (offset == n or answer[offset].isspace())
    )


def snap_prefix_end(answer: str, end: int) -> int:
    """Snap ``end`` OUTWARD to the next clause/sentence boundary.

    Outward only: the derivation may keep a whole clause the model's span
    clipped, but never less than the model asked to preserve. End of text is
    itself a boundary, so an answer with no internal punctuation degrades to
    "keep all of it" rather than to an arbitrary word cut.
    """

    n = len(answer)
    if end >= n:
        return n
    if end <= 0:
        return 0
    for boundary in clause_boundaries(answer):
        if boundary >= end:
            return boundary
    return n


def _resolved_span_end(answer: str, ref: dict[str, Any]) -> int | None:
    """End offset of one ``answer_span`` preserve ref, quote-authoritative."""

    quote = str(ref.get("quote") or "")
    start = ref.get("char_start")
    end = ref.get("char_end")
    if (
        isinstance(start, int)
        and isinstance(end, int)
        and 0 <= start < end <= len(answer)
        and (not quote or answer[start:end] == quote)
    ):
        return end
    if quote:
        # Same authority order the attribution anchors use: the quote places the
        # span, model offsets are only a disambiguation hint. Imported lazily —
        # ``grading`` imports this module at load time.
        from learnloop.attempts.grading import resolve_quote_anchor

        resolution = resolve_quote_anchor(
            answer, quote, hint_start=start if isinstance(start, int) else None
        )
        if resolution.char_end is not None:
            return resolution.char_end
    return None


def preserved_prefix_from_refs(
    answer: str,
    preserve_refs: list[Any] | None,
    *,
    before_offset: int | None = None,
) -> PreservedPrefix | None:
    """Derive the preserved prefix from a suggestion's ``preserve_refs``.

    Returns ``None`` when the suggestion declares no locatable ``answer_span``
    preservation — there is then nothing to derive from and the caller keeps its
    existing verbatim-``learner_work_prefix`` behaviour unchanged.

    The union of declared spans is reduced to its maximum end because the trace
    schema can only express a *prefix*; a span that starts mid-answer still
    implies everything before it survives, since the repair is spliced after the
    preserved region.
    """

    if not answer:
        return None
    limit = (
        max(0, min(len(answer), int(before_offset)))
        if before_offset is not None
        else None
    )
    ends: list[int] = []
    for ref in preserve_refs or []:
        if not isinstance(ref, dict) or ref.get("kind") != "answer_span":
            continue
        resolved = _resolved_span_end(answer, ref)
        # A later preserved citation is still useful evidence, but it cannot
        # move a prefix-only splice past the divergence being repaired.  It
        # belongs in regenerated downstream work instead.
        if resolved is not None and (limit is None or resolved <= limit):
            ends.append(resolved)
    if not ends:
        return None
    declared_end = max(ends)
    snapped_end = snap_prefix_end(answer, declared_end)
    if limit is not None:
        snapped_end = min(snapped_end, limit)
    return PreservedPrefix(
        text=answer[:snapped_end],
        basis="derived_from_preserve_refs",
        declared_end=declared_end,
        snapped_end=snapped_end,
    )


def is_end_append(repaired_trace: dict[str, Any]) -> bool:
    """Whether the repair appends after the learner's work rather than into it.

    Requires an explicit insertion point: a trace that declares none says
    nothing about where the edit lands, and inventing a separator for it would
    rewrite every legacy trace's stored bytes for no evidence.
    """

    insertion = repaired_trace.get("repair_insertion_point")
    if not isinstance(insertion, dict):
        return False
    if "end_append" in insertion:
        return bool(insertion["end_append"])
    if insertion.get("anchor_kind") == "missing_required_step":
        return True
    return insertion.get("char_start") is None and insertion.get("char_end") is None


def _has_paragraph_break(prefix: str, regenerated: str) -> bool:
    if _PARAGRAPH_BREAK_AT_END.search(prefix):
        return True
    if _PARAGRAPH_BREAK_AT_START.match(regenerated):
        return True
    return bool(
        _NEWLINE_AT_END.search(prefix) and _NEWLINE_AT_START.match(regenerated)
    )


def splice_repaired_answer(
    prefix: str, regenerated: str, *, end_append: bool
) -> SplicedAnswer:
    """Compose the repaired answer, guarding the end-append junction.

    An end-append starts a new step; without a blank line it renders as a
    continuation of the learner's last sentence — which is exactly how the
    exhibit ended up with a solution pasted after "I'm not sure what to do from
    here". Only the leading spaces/tabs of the suffix are dropped; the prefix is
    never trimmed, so it stays a verbatim slice of the learner's answer.
    """

    if (
        end_append
        and prefix.strip()
        and regenerated.strip()
        and not _has_paragraph_break(prefix, regenerated)
    ):
        suffix = "\n\n" + regenerated.lstrip(" \t")
        return SplicedAnswer(prefix + suffix, suffix, "paragraph_break_inserted")
    return SplicedAnswer(prefix + regenerated, regenerated, "verbatim")
