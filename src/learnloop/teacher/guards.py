"""The output guards (spec_teacher_v1 §9.3): every learner-facing field passes three (the message and its
choices, a prediction, a check, plan statements and a close's recap: ``service._displayed``).

1. **Keys**: ``learner_context.leaks_key`` against the answer keys of every item on
   the lesson's LOs (today's YAML and every recorded snapshot: the KeyBook), except
   this lesson's own check items once their check has closed (their solution is
   the feedback). An unreadable KeyBook withholds every message (fail closed).
2. **The open check's solution**: while a check is open, a message that gives its
   committed solution away is withheld (the tutor's span filter). A reply to the
   learner's own question during an open check is help, not withheld: its overlap
   decides whether the check is withdrawn (§12, :func:`solution_overlap`).
3. **Citations**: every ``[S3]`` must name a passage delivered to the teacher, and
   a quote placed just before a citation must be in that passage.

On a hit the message is withheld and the model re-prompted with the reason (a
correctable error); it never reaches the learner.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from learnloop.teacher.brief import SourceBook

CITATION = re.compile(r"\[(S\d+)\]")
#: A quoted span followed by its citation: "...quoted text..." [S3].
QUOTE_CITATION = re.compile(r"[\"“]([^\"”]{1,800})[\"”]\s*\[(S\d+)\]")


@dataclass(frozen=True)
class GuardVerdict:
    ok: bool
    reason: str | None = None
    detail: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "reason": self.reason, "detail": self.detail}


def _normalize(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", str(text).lower()).split())


def _identity(value: Any) -> str:
    import json

    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def key_sets(vault: Any, repository: Any, learning_object_ids: Iterable[str],
             exempt_items: Iterable[str]) -> tuple[list[Any], list[Any], bool]:
    """``(lesson keys, vault keys, unreadable)`` from one read of the KeyBook: every recorded answer key on these LOs
    except the exempt items' (the displayed text's guard), and every answer key the vault records on any item, on
    any LO (the identifier guard's, :func:`identifier_guard`)."""

    from learnloop.learner_context import key_book

    unknowns: list[str] = []
    with repository.connection() as connection:
        book = key_book(connection, vault, unknowns)
    exempt = {str(item) for item in exempt_items}
    exempt_ids = {_identity(key) for item in exempt for key in book.item(item)}
    keys = [key for key in book.los(list(learning_object_ids)) if _identity(key) not in exempt_ids]
    every = list({_identity(key): key for item_keys in book.by_item.values() for key in item_keys}.values())
    return keys, every, book.unreadable


def lesson_keys(vault: Any, repository: Any, learning_object_ids: Iterable[str],
                exempt_items: Iterable[str]) -> tuple[list[Any], bool]:
    """``(keys, unreadable)``: every recorded answer key on these LOs except the exempt items'."""

    keys, _every, unreadable = key_sets(vault, repository, learning_object_ids, exempt_items)
    return keys, unreadable


def identifier_guard(text: str, vault_keys: Sequence[Any], unreadable: bool) -> GuardVerdict:
    """A model-supplied field a log row or a receipt copies (a plan node's id or ``lo_id``, a note's node and
    hypothesis, a forecast's node and its LO) against every answer key the vault records (TE2-log landing, ruling
    R1): an exam-reserved or held-out item's on any LO, a topic the lesson's brief never named and one a plan adds
    in the same turn included, with no exemption. An unreadable KeyBook refuses (fail closed)."""

    from learnloop.learner_context import leaks_key

    if unreadable:
        return GuardVerdict(False, "keys_unreadable", "past answer keys could not be read, so nothing is recorded")
    if text and leaks_key(text, vault_keys):
        return GuardVerdict(False, "answer_key", "this reproduces the answer to one of LearnLoop's questions; use a "
                                                 "plain id such as n1, and never an answer")
    return GuardVerdict(True)


def key_guard(message: str, keys: Sequence[Any], unreadable: bool) -> GuardVerdict:
    from learnloop.learner_context import leaks_key

    if unreadable:
        return GuardVerdict(False, "keys_unreadable", "past answer keys could not be read, so nothing is shown")
    if message and leaks_key(message, keys):
        return GuardVerdict(False, "answer_key", "the message reproduces the answer to one of LearnLoop's questions "
                                                 "on these topics; teach the idea without giving that answer")
    return GuardVerdict(True)


def solution_overlap(text: str, solution: str) -> float:
    """How much of a committed solution ``text`` exposes (0..1; the tutor's span measure)."""

    from learnloop.tutor.tutor_qa import span_answer_overlap

    if not text or not solution:
        return 0.0
    return float(span_answer_overlap(text, solution))


def open_check_guard(message: str, open_check: Mapping[str, Any] | None) -> GuardVerdict:
    from learnloop.tutor.tutor_qa import span_leaks_expected

    if not open_check or not message:
        return GuardVerdict(True)
    if span_leaks_expected(message, str(open_check.get("committed_solution") or "")):
        return GuardVerdict(False, "open_check_solution",
                            "the message gives away the open check's solution before the learner answered")
    return GuardVerdict(True)


def citation_guard(message: str, book: SourceBook) -> GuardVerdict:
    cited = CITATION.findall(message or "")
    unknown = sorted({alias for alias in cited if not book.available(alias)})
    if unknown:
        return GuardVerdict(False, "unknown_citation",
                            f"these passages were never delivered to you: {', '.join(unknown)}; cite only the "
                            "aliases you were given")
    for quote, alias in QUOTE_CITATION.findall(message or ""):
        if _normalize(quote) and _normalize(quote) not in _normalize(book.passages[alias]["text"]):
            return GuardVerdict(False, "quote_mismatch",
                                f"the quote before [{alias}] is not in that passage; quote it exactly or paraphrase "
                                "without quotation marks")
    return GuardVerdict(True)


def check_all(message: str, *, keys: Sequence[Any], unreadable: bool, book: SourceBook,
              open_check: Mapping[str, Any] | None, help_reply: bool) -> GuardVerdict:
    """The three guards in order (the open check's is skipped for a reply to the learner's own question)."""

    for verdict in (key_guard(message, keys, unreadable),
                    GuardVerdict(True) if help_reply else open_check_guard(message, open_check),
                    citation_guard(message, book)):
        if not verdict.ok:
            return verdict
    return GuardVerdict(True)


def cited_aliases(message: str) -> list[str]:
    return list(dict.fromkeys(CITATION.findall(message or "")))


__all__ = [
    "CITATION",
    "GuardVerdict",
    "check_all",
    "citation_guard",
    "cited_aliases",
    "identifier_guard",
    "key_guard",
    "key_sets",
    "lesson_keys",
    "open_check_guard",
    "solution_overlap",
]
