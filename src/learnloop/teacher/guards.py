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
4. **Reserved questions** (teacher exam-question guard, found at TE2's landing smoke): the
   keys guard covers answers, not the questions themselves. Every guarded field is also
   compared with the questions LearnLoop keeps for an exam or holds out
   (:func:`reserved_book`: the one authority ``learner_protection.withheld_items`` read through
   ``practice_leakage.reserved_questions``, the matcher FG1's probes and TE2's typed goals use)
   by that matcher's span rule (:func:`reserved_guard`). An unreadable protection state withholds
   every field (fail closed).

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


#: The matcher's span findings (``practice_leakage.reserved_findings``): a reserved question's contiguous wording
#: (its shingle order, less what ordinary items and readable source text already show) or a whole reserved stem.
#: Its lone-number findings are not a question shown: a lesson's arithmetic ("0.5", "1/2") would trip them. A span
#: shorter than the matcher's own shingle order (a whole short stem such as "Define a basis.", or a short text that
#: is a whole short held-out block) can be a common phrase inside a teaching sentence ("Later we define a basis
#: carefully."), so it counts when it is the question (:func:`quotes_reserved`):
#:
#: * it carries a distinctive number by the matcher's own numeric rule, read from this text (Codex review F1:
#:   "Factor 9871 into primes."; an ordinary item showing 9871 doesn't make the whole question ordinary: re-review);
#: * or, a whole stem, the text poses it (Codex re-review F1: "Decrypt QEBNRFZH using Caesar cipher."): it stands
#:   as its own sentence or clause (:data:`CLAUSE_MARKS` or the text's edge on both sides), or the text asks it
#:   (a question mark right after it).
#:
#: No new threshold: the matcher's span length and numeric rule, and punctuation.
RESERVED_SPAN_KINDS: frozenset[str] = frozenset({"wording", "stem"})
#: Where a shown sentence or clause starts or ends: structural punctuation, a line break, a quotation mark or a
#: bracket (an apostrophe is a word's, so it isn't one).
CLAUSE_MARKS: frozenset[str] = frozenset(".,;:!?\n\"“”«»()[]{}")
_TOKEN = re.compile(r"[a-z0-9]+")  # the matcher's words (``practice_leakage._normalize_tokens``), with positions


@dataclass(frozen=True)
class ReservedBook:
    """The questions still reserved for an exam or held out, read once per turn (``questions``:
    ``practice_leakage.ReservedQuestions``). ``unreadable``: the protection state could not be read."""

    questions: Any = None
    unreadable: bool = False


def reserved_book(vault: Any, repository: Any) -> ReservedBook:
    """The reserved and held-out questions as the rest of LearnLoop reads them: ``withheld_items`` (exam pools,
    held-out units and the items made from them, live assessment reservations), then ``reserved_questions`` (their
    stems, keys and rubrics, and every held-out span). Unavailable or failing: unreadable (fail closed)."""

    from learnloop.content.authoring.practice_leakage import reserved_questions
    from learnloop.learner_protection import withheld_items

    try:
        withheld = withheld_items(vault, repository)
        if not withheld.available:
            return ReservedBook(unreadable=True)
        return ReservedBook(questions=reserved_questions(vault, repository, withheld))
    except Exception:  # noqa: BLE001 - an unreadable predicate fails closed
        return ReservedBook(unreadable=True)


def quotes_reserved(text: str, reserved: ReservedBook) -> bool:
    """Whether ``text`` reproduces a reserved or held-out question by the matcher's span rule. Unreadable: True."""

    from learnloop.content.authoring.practice_leakage import inventory_for_texts, reserved_findings

    if reserved.unreadable:
        return True
    if not text or reserved.questions is None:
        return False
    order = int(reserved.questions.inventory.shingle_n)
    spans = [finding for finding in reserved_findings(str(text), reserved.questions)
             if finding["kind"] in RESERVED_SPAN_KINDS]
    if any(len(str(finding["value"]).split()) >= order for finding in spans):
        return True  # at the matcher's span
    if not spans:
        return False
    # The distinctive numbers this text shows, by the matcher's numeric rule, as its normalized words ("16.0" ->
    # "16 0"); read from the text itself, so an ordinary item showing the number doesn't drop it (re-review F1).
    numbers = [f" {_normalize(number)} " for number in inventory_for_texts([str(text)]).numerics]
    return any(any(number.strip() and number in f" {finding['value']} " for number in numbers)
               or (finding["kind"] == "stem" and _posed(str(text), str(finding["value"])))
               for finding in spans)


def _posed(text: str, stem: str) -> bool:
    """Whether ``text`` poses this whole stem (its normalized words): somewhere it stands as its own sentence or clause
    (a :data:`CLAUSE_MARKS` character or the text's edge before and after it), or a question mark follows it. Inside
    a sentence ("Later we define a basis carefully.") it is a phrase, not the question."""

    lowered = text.lower()
    runs = [(match.start(), match.end(), match.group()) for match in _TOKEN.finditer(lowered)]
    words, target = [run[2] for run in runs], stem.split()
    size = len(target)
    for start in range(len(words) - size + 1):
        if not size or words[start:start + size] != target:
            continue
        end = start + size
        before = lowered[runs[start - 1][1] if start else 0:runs[start][0]]
        after = lowered[runs[end - 1][1]:runs[end][0] if end < len(runs) else len(lowered)]
        opens = start == 0 or any(char in CLAUSE_MARKS for char in before)
        closes = end == len(runs) or any(char in CLAUSE_MARKS for char in after)
        if (opens and closes) or "?" in after:
            return True
    return False


def reserved_guard(text: str, reserved: ReservedBook) -> GuardVerdict:
    """A field that would show a question kept for an exam or held out. The detail names no words (it enters the
    transcript the teacher reads next, so it never carries the question)."""

    if reserved.unreadable:
        return GuardVerdict(False, "protection_unreadable",
                            "the questions kept for an exam could not be read, so nothing is shown")
    if text and quotes_reserved(text, reserved):
        return GuardVerdict(False, "reserved_question",
                            "this reproduces a question LearnLoop keeps for an exam or holds out; teach the idea in "
                            "your own words and never quote or restate that question")
    return GuardVerdict(True)


def shown_feedback(feedback: str | None, reserved: ReservedBook) -> str | None:
    """A grader's feedback as the lesson shows it: None when it reproduces a reserved or held-out question, or when
    those could not be read (the result itself stands)."""

    if not feedback:
        return feedback
    return None if quotes_reserved(feedback, reserved) else feedback


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
              open_check: Mapping[str, Any] | None, help_reply: bool, reserved: ReservedBook,
              vault_keys: Sequence[Any] | None = None) -> GuardVerdict:
    """The guards in order, the first refusal named: keys; for a logged field (``vault_keys`` given) the identifier
    guard; reserved questions; the open check's (skipped for a reply to the learner's own question); citations."""

    checks = (
        lambda: key_guard(message, keys, unreadable),
        lambda: GuardVerdict(True) if vault_keys is None else identifier_guard(message, vault_keys, unreadable),
        lambda: reserved_guard(message, reserved),
        lambda: GuardVerdict(True) if help_reply else open_check_guard(message, open_check),
        lambda: citation_guard(message, book),
    )
    for check in checks:
        verdict = check()
        if not verdict.ok:
            return verdict
    return GuardVerdict(True)


def cited_aliases(message: str) -> list[str]:
    return list(dict.fromkeys(CITATION.findall(message or "")))


__all__ = [
    "CITATION",
    "CLAUSE_MARKS",
    "GuardVerdict",
    "RESERVED_SPAN_KINDS",
    "ReservedBook",
    "check_all",
    "citation_guard",
    "cited_aliases",
    "identifier_guard",
    "key_guard",
    "key_sets",
    "lesson_keys",
    "open_check_guard",
    "quotes_reserved",
    "reserved_book",
    "reserved_guard",
    "shown_feedback",
    "solution_overlap",
]
