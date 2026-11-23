"""Whether a pad block of the learner's carries someone else's words (spec §10.9, §10.11).

A learner's text block that pastes a source or tutor text is detected by overlap with the pad's own quote blocks
and with the passages the block is linked to. One predicate serves both exits: emission marks such a block "quoted
by the learner" (read, never taken as the learner's belief), and submission refuses it ("this includes quoted
text · submit only your own words").

The overlap is a whole sentence of a quote, word for word (case, punctuation and spacing aside), inside the block.
A sentence shorter than :data:`MIN_SENTENCE_CHARS` normalized characters is too short to tell copying from writing
the same few words (a symbol, "yes", a number the passage also states) and never counts. Pure: no database.
"""
from __future__ import annotations

import re
from collections.abc import Iterable

#: The shortest sentence, in normalized characters, whose verbatim presence counts as copying: the same floor the
#: tutor's answer-leak measure uses for a verbatim hit (``tutor.tutor_qa.answer_leak_overlap``).
MIN_SENTENCE_CHARS = 12
_SENTENCE_END = re.compile(r"(?<=[.!?;:])\s+|\n+")
_WORD = re.compile(r"[^\W_]+", re.UNICODE)


def _normalized(text: str) -> str:
    return " ".join(_WORD.findall(str(text or "").casefold()))


def quote_sentences(quote: str) -> list[str]:
    """A quote's sentences, normalized, each long enough to count."""

    sentences = (_normalized(part) for part in _SENTENCE_END.split(str(quote or "")))
    return [sentence for sentence in sentences if len(sentence) >= MIN_SENTENCE_CHARS]


def includes_quote(block_text: str, quotes: Iterable[str]) -> bool:
    """Whether ``block_text`` contains, word for word, a whole sentence of any of ``quotes``."""

    block = f" {_normalized(block_text)} "
    if not block.strip():
        return False
    return any(f" {sentence} " in block for quote in quotes for sentence in quote_sentences(quote))


__all__ = ["MIN_SENTENCE_CHARS", "includes_quote", "quote_sentences"]
