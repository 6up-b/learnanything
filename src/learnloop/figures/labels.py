"""Reader RW5d: the figures' code-owned label words, and the free-text label rule (spec §9b.4).

**The labels** (SM2, §6.6, §6.8, §9.5): a figure's badge and its check lines
are code-owned. They are written only from closed values (the verification,
the tier, the grounding, the keys of the checks code ran), in these words,
and never in a model's words. The desktop's frames (``FIGURE_FRAME``,
``SKETCH_FRAME`` and ``RICH_FRAME``) carry the same strings, and a test keeps
the two sides equal.

**The free-text label rule** (§9b.4, P2b ruling R2): model-written free text
on any tier must not read like one of these labels. That covers what a figure
shows (``demonstrates``), its assumptions, a Manim figure's title and
narration, and the author's tier reason (``why_this_tier``, or V2's
``why_not_spec``). :func:`label_like` matches the label vocabulary
structurally, from the constants below and not from a hand list of phrases:

* a code-owned label, or a three-word-or-longer segment of one that states a
  check (*not checked against the book*), along with its positive form
  (*checked against the book*);
* a check word (:data:`CHECK_LABEL_WORDS`: the check lines' *checked* and
  RW5c's stored *verified*) in a badge form: in brackets (*(checked)*), as
  its own ``·`` segment or a whole text (*Verified*), as a lead
  (*Checked: ...*), or naming LearnLoop (*verified by LearnLoop*,
  *LearnLoop checked*);
* a check-mark glyph (:data:`CHECK_GLYPHS`), which is badge vocabulary;
* N-a's source-verification claim (*matches the book*, *agrees with your
  textbook*, *verified against the book*: :data:`SOURCE_CLAIM_VERBS`,
  :data:`SOURCE_NOUNS`), with no check word or glyph needed (Codex review F1,
  Nov 1b);
* a badge form at the start of any line of its own, read at the text's
  original line breaks without its Markdown lead or emphasis (a line reading
  *- **Checked:** ...*), since the desktop keeps a narration's line breaks
  (Codex review F2);
* a label phrase or a source-verification claim in the text as its Markdown
  renders: emphasis, code spans and link targets dropped, and its lines joined
  without their leads (*matches **the book***, *matches [the book](...)*, a
  claim broken over a line break; the orchestrator's scoped verify, F1
  remainder).

Ordinary prose is not matched: *check that the area is 1*, *we verified the
identity by expanding*, *the box is checked*. Matching ignores case and
Unicode compatibility forms (NFKC).

On a hit, the author's repair call gets code's own words
(:func:`label_problems`). A figure that still violates after that call is
handled by its tier's existing path. A spec or sketch is shown without the
text (:func:`strip_json`). A Manim figure is refused
(:func:`learnloop.figures.manim_figure.parse_figure`), as any other invalid
answer is.

A stored figure is presented under the same rule (Codex review F3,
:func:`learnloop.figures.service.worded_row`): listed or reused, it is shown
without its label-like text, a Manim title left out and each label-like
transcript line replaced in code's words (:func:`strip_lines`). The stored
row is never rewritten.

Nothing here calls a model or touches the vault.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Iterable
from typing import Any

from learnloop.db.stores.figures import VERIFIED_RW5C

#: The word a code-owned check line states.
CHECKED = "checked"
#: The check lines' lead (the desktop's ``FIGURE_FRAME.checksLead`` and ``SKETCH_FRAME.checksLead``).
CHECKS_LEAD = f"{CHECKED} by LearnLoop:"

# The grammar figure's badges (RW5a; RW5d P1's abstention).
#: What a grammar figure's badge says (spec §8.3): never "matches the book" (RW5c's).
ILLUSTRATIVE_LABEL = "AI-built illustration of an interpretation · not checked against the book"
#: What a figure built with nothing from the learner's books says (RW1c's abstention).
NOT_FROM_BOOKS_LABEL = "AI-built illustration · not from your books"
#: The sketch's code-owned badges (spec §6.6, §9.5): never "checked against the book".
SKETCH_LABEL = "AI-written simulation · sandboxed · not checked against the book"
SKETCH_UNCHECKED_LABEL = "AI-written simulation · nothing in it checked"
SKETCH_NOT_FROM_BOOKS_LABEL = "AI-written simulation · sandboxed · not from your books"
#: The Manim figure's code-owned badges (spec §6.8): never "checked against the book".
MANIM_LABEL = "AI-made video · not checked against the book"
MANIM_UNCHECKED_LABEL = "AI-made video · not checked"
MANIM_NOT_FROM_BOOKS_LABEL = "AI-made video · not from your books"
#: The line every Manim figure's checks end with (spec §6.8).
MANIM_NOT_COVERED = "the video itself is not checked frame by frame"

#: Every code-owned badge and check-line string a model's text must not reproduce.
CODE_OWNED_LABELS = (ILLUSTRATIVE_LABEL, NOT_FROM_BOOKS_LABEL, SKETCH_LABEL, SKETCH_UNCHECKED_LABEL,
                     SKETCH_NOT_FROM_BOOKS_LABEL, MANIM_LABEL, MANIM_UNCHECKED_LABEL, MANIM_NOT_FROM_BOOKS_LABEL,
                     MANIM_NOT_COVERED, CHECKS_LEAD)
#: The words a check label states: the check lines' word, and RW5c's stored
#: verification (``verified``, the "matches the book (checked)" status).
CHECK_LABEL_WORDS = (CHECKED, VERIFIED_RW5C)
#: keep (wording rule): the check-mark glyphs a badge can wear. Any of them in
#: model text reads as a badge: a figure's own words never need one.
CHECK_GLYPHS = "✓✔☑✅\U0001f5f8"
#: keep (wording rule): the shortest label segment matched on its own. Two
#: words (*not checked*) are ordinary prose. Three name a label's claim.
MIN_SEGMENT_WORDS = 3
#: keep (wording rule, N-a; Codex review F1, Nov 1b): the source-verification
#: claim no RW5d tier makes (§9b.4: *never "matches the book"*), matched on its
#: own, with no check word or glyph: one of these verbs, then *the* or *your*,
#: then one of :data:`SOURCE_NOUNS`. Equality with the book's equation is
#: RW5c's question and label; until RW5c draws it, nothing may claim it.
SOURCE_CLAIM_VERBS = ("match", "matches", "matched", "matching", "agree with", "agrees with", "agreed with")
#: keep (wording rule, N-a): what a source-verification claim names.
SOURCE_NOUNS = ("book", "books", "textbook", "textbooks")
#: What replaces a tier reason that still reads like a check label after the
#: repair call (it is a receipt's rationale, in code's words).
REASON_WITHHELD = "(the author's reason read like a LearnLoop check label and was left out)"
#: What replaces a stored figure's label-like line when it is presented
#: (Codex review F3, Nov 1b): the stored text is kept, the view says so.
LINE_WITHHELD = "(a line that read like a LearnLoop check label was left out)"
#: What replaces stored text that reads like a label across its lines.
TEXT_WITHHELD = "(this text read like a LearnLoop check label and was left out)"

_SEPARATORS = re.compile(r"\s*[·•∙⋅]\s*")
_SPACES = re.compile(r"\s+")


def fold(text: Any) -> str:
    """Text as the rule reads it: NFKC, case-folded, separators as `` · ``, single spaces."""

    folded = unicodedata.normalize("NFKC", str(text or "")).casefold()
    return _SPACES.sub(" ", _SEPARATORS.sub(" · ", folded)).strip()


def _label_phrases() -> tuple[str, ...]:
    phrases: set[str] = set()
    for label in CODE_OWNED_LABELS:
        folded = fold(label)
        phrases.add(folded.rstrip(" :"))
        for segment in folded.split(" · "):
            segment = segment.strip(" :")
            words = segment.split()
            if len(words) < MIN_SEGMENT_WORDS or not set(words) & set(CHECK_LABEL_WORDS):
                continue
            phrases.add(segment)
            if words[0] == "not" and len(words) - 1 >= MIN_SEGMENT_WORDS:
                phrases.add(" ".join(words[1:]))
    return tuple(sorted(phrases, key=lambda phrase: (-len(phrase), phrase)))


#: The label phrases, longest first (derived from :data:`CODE_OWNED_LABELS`).
LABEL_PHRASES = _label_phrases()
_PHRASE = re.compile("|".join(rf"(?<!\w){re.escape(phrase)}(?!\w)" for phrase in LABEL_PHRASES))
_WORD = "(?:" + "|".join(re.escape(word) for word in CHECK_LABEL_WORDS) + ")"
_LEARNLOOP = re.escape(fold("LearnLoop"))
_BADGE = re.compile(
    rf"[\(\[\{{]\s*{_WORD}\s*[\)\]\}}]"                                  # (checked), [verified]
    rf"|(?<!\w){_WORD}\s+by\s+{_LEARNLOOP}(?!\w)"                       # verified by LearnLoop
    rf"|(?<!\w){_LEARNLOOP}\s+(?:has\s+|have\s+)?{_WORD}(?!\w)"         # LearnLoop checked
    rf"|(?:^|·)\s*{_WORD}\s*(?:·|:|[.!]?$)"                    # · checked ·, Verified, Checked: ...
    rf"|[{re.escape(CHECK_GLYPHS)}]"                                     # a check-mark glyph
)
_NOUN = "(?:" + "|".join(re.escape(noun) for noun in sorted(SOURCE_NOUNS, key=len, reverse=True)) + ")"
_SOURCE_CLAIM = re.compile(
    "(?<!\\w)(?:" + "|".join(re.escape(verb).replace("\\ ", r"\s+")
                             for verb in sorted(SOURCE_CLAIM_VERBS, key=len, reverse=True)) + ")"
    rf"\s+(?:the|your)\s+{_NOUN}(?!\w)"                                   # matches the book
    rf"|(?<!\w){_WORD}\s+against\s+(?:the|your)\s+{_NOUN}(?!\w)"          # verified against your books
)
#: A line's Markdown lead (quote, heading, list or number marker) and emphasis
#: (Codex review F2, Nov 1b: the desktop keeps a narration's line breaks).
_LINE_LEAD = re.compile(r"^[\s>#*+\-]*(?:\d+[.)]\s*)?")
_EMPHASIS = re.compile(r"[*_`~]+")
#: A Markdown link or image, inline or by reference: the learner reads its text
#: (orchestrator's scoped verify, F1 remainder). The text may span a line break.
_LINK = re.compile(r"!?\[([^\]]*)\]\s*(?:\([^)]*\)|\[[^\]]*\])")


def _lines(text: Any) -> list[str]:
    """Each line of ``text`` as the rule reads it, split at its original line
    breaks before spaces collapse, without its Markdown lead, emphasis, code
    spans and link targets."""

    found = []
    for line in _EMPHASIS.sub("", _LINK.sub(r"\1", str(text or ""))).splitlines():
        folded = _LINE_LEAD.sub("", fold(line))
        if folded:
            found.append(folded)
    return found


def label_like(text: Any) -> str | None:
    """The label-like phrase ``text`` contains (folded), or None."""

    folded = fold(text)
    if not folded:
        return None
    found = _PHRASE.search(folded) or _BADGE.search(folded) or _SOURCE_CLAIM.search(folded)
    if found is None:
        lines = _lines(text)
        # The text as the learner reads it once its Markdown renders (F1
        # remainder): *matches **the book***, a link's text, or a claim broken
        # over lines (each line's lead dropped) still states the claim.
        plain = " ".join(lines)
        # A label form at the start of a line of its own (Codex review F2):
        # "Checked: ..." after a line break shows as a separate label line.
        found = (_PHRASE.search(plain) or _SOURCE_CLAIM.search(plain)
                 or next((match for line in lines if (match := _BADGE.search(line))), None))
    return found.group(0).strip() if found else None


def label_problems(fields: Iterable[tuple[str, Any]]) -> list[str]:
    """Code's words for every field whose text reads like a check label (the repair call's problems)."""

    problems = []
    for where, text in fields:
        phrase = label_like(text)
        if phrase is not None:
            problems.append(f"{where} reads like one of LearnLoop's check labels ({phrase!r}). Only LearnLoop "
                            "writes check labels, and only for checks its code ran: say it in your own words, "
                            "without check marks or words like \"checked\" or \"verified\" used as a label")
    return problems


def strip_lines(text: Any) -> str:
    """Stored ``text`` as it is presented (Codex review F3, Nov 1b): each
    label-like line replaced by :data:`LINE_WITHHELD`, so the cut is never
    silent; :data:`TEXT_WITHHELD` when it still reads like a label across its
    lines. Unchanged when nothing reads like a label."""

    raw = str(text or "")
    if label_like(raw) is None:
        return raw
    kept = "\n".join(LINE_WITHHELD if label_like(line) is not None else line for line in raw.splitlines())
    return kept if label_like(kept) is None else TEXT_WITHHELD


def _assumption_text(item: Any) -> Any:
    return item.get("text") if isinstance(item, dict) else item


def _object(raw: Any) -> dict[str, Any] | None:
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError):
        return None
    return dict(data) if isinstance(data, dict) else None


def json_fields(name: str, raw: Any) -> list[tuple[str, Any]]:
    """The free text of a figure answer's JSON (a spec, a sketch or a rich
    brief: they share these keys): what it shows and its assumptions."""

    data = _object(raw)
    if data is None:
        return []
    fields: list[tuple[str, Any]] = [(f"{name}.demonstrates", data.get("demonstrates"))]
    assumptions = data.get("assumptions")
    if isinstance(assumptions, list):
        fields += [(f"{name}.assumptions[{index}]", _assumption_text(item)) for index, item in enumerate(assumptions)]
    return fields


def strip_json(raw: Any) -> Any:
    """``raw`` without its label-like free text: what it shows is emptied
    and a label-like assumption is dropped. Unchanged (the same object) when
    nothing reads like a label, or when it is not a JSON object."""

    data = _object(raw)
    if data is None:
        return raw
    changed = False
    if label_like(data.get("demonstrates")) is not None:
        data["demonstrates"] = ""
        changed = True
    assumptions = data.get("assumptions")
    if isinstance(assumptions, list):
        kept = [item for item in assumptions if label_like(_assumption_text(item)) is None]
        if len(kept) != len(assumptions):
            data["assumptions"] = kept
            changed = True
    if not changed:
        return raw
    return json.dumps(data, ensure_ascii=False) if isinstance(raw, str) else data


__all__ = [
    "CHECKED",
    "CHECKS_LEAD",
    "CHECK_GLYPHS",
    "CHECK_LABEL_WORDS",
    "CODE_OWNED_LABELS",
    "ILLUSTRATIVE_LABEL",
    "LABEL_PHRASES",
    "LINE_WITHHELD",
    "MANIM_LABEL",
    "MANIM_NOT_COVERED",
    "MANIM_NOT_FROM_BOOKS_LABEL",
    "MANIM_UNCHECKED_LABEL",
    "MIN_SEGMENT_WORDS",
    "NOT_FROM_BOOKS_LABEL",
    "REASON_WITHHELD",
    "SKETCH_LABEL",
    "SKETCH_NOT_FROM_BOOKS_LABEL",
    "SKETCH_UNCHECKED_LABEL",
    "SOURCE_CLAIM_VERBS",
    "SOURCE_NOUNS",
    "TEXT_WITHHELD",
    "fold",
    "json_fields",
    "label_like",
    "label_problems",
    "strip_json",
    "strip_lines",
]
