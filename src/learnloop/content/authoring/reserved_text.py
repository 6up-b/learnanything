"""The questions kept for an exam, in text: one predicate for every reader that must not show or send one.

Teaching guards (``teacher.guards``), the topic resolver's catalog (``source_retrieval.deliverables.catalog_screen``),
a lesson's brief and history reads, and a lesson's display ask :func:`quotes_reserved` over :func:`reserved_book`: the
reserved and held-out questions as ``learner_protection.withheld_items`` and ``practice_leakage.reserved_questions``
read them, matched by the matcher's span rule. An unreadable protection state is reported (``unreadable``) so each
caller fails closed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


def _normalized_words(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", str(text).lower()).split())


#: The matcher's span findings (``practice_leakage.reserved_findings``): a reserved question's contiguous wording
#: (its shingle order, less what ordinary items and readable source text already show) or a whole reserved stem.
#: Its lone-number findings are not a question shown: a lesson's arithmetic ("0.5", "1/2") would trip them. A span
#: shorter than the matcher's own shingle order (a whole short stem such as "Define a basis.", or a short text that
#: is a whole short held-out block) can be a common phrase of the subject ("Later we define a basis carefully."), so
#: it counts when it carries something distinctive (:func:`quotes_reserved`):
#:
#: * a distinctive number by the matcher's own numeric rule, read from this text (Codex review F1: "Factor 9871 into
#:   primes."; an ordinary item showing 9871 doesn't make the whole question ordinary: re-review);
#: * or, a whole stem, a word distinctive in this vault by the vault's own text (landing ruling R1, after F1 reopened
#:   twice on short stems: "Decrypt QEBNRFZH using Caesar cipher.", also inside "Please decrypt QEBNRFZH using Caesar
#:   cipher."): no other item and no readable passage shows it (``practice_leakage.distinctive_words``). Punctuation
#:   and position don't matter. A stem made only of common words ("Define a basis.") stays a phrase.
#:
#: No new threshold: the matcher's span length and numeric rule, and document frequency 1 over the vault's text.
RESERVED_SPAN_KINDS: frozenset[str] = frozenset({"wording", "stem"})


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

    from learnloop.content.authoring.practice_leakage import distinctive_words, inventory_for_texts, reserved_findings

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
    numbers = [f" {_normalized_words(number)} " for number in inventory_for_texts([str(text)]).numerics]
    # A stem finding means the text holds the stem's whole word sequence contiguously (the matcher's own test).
    return any(any(number.strip() and number in f" {finding['value']} " for number in numbers)
               or (finding["kind"] == "stem" and bool(distinctive_words(str(finding["value"]), reserved.questions)))
               for finding in spans)


__all__ = ["RESERVED_SPAN_KINDS", "ReservedBook", "quotes_reserved", "reserved_book"]
