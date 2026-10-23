"""Deterministic block-role hints (spec_source_ingestion_v2 §2.6).

Annotate likely pedagogical roles from headings and block context — external to
any marker processor. These are *hints*, not semantic truth; they shrink
inventory prompts and let role-aware treatment differ (problem sets emphasize
exercises; papers emphasize claims/limitations). "Definition 4.2", "Exercises",
and "Worked Example" are recognizable deterministically.
"""

from __future__ import annotations

from collections.abc import Iterable

from dataclasses import dataclass
import re

ROLES = (
    "definition",
    "theorem",
    "proof",
    "worked_example",
    "exercise",
    "solution",
    "summary",
    "reference",
    "equation",
    "figure",
    "table",
    "ordinary_prose",
)

# Native block types that pin a role regardless of surrounding text.
_BLOCK_TYPE_ROLES = {
    "equation": "equation",
    "equationnumber": "equation",
    "math": "equation",
    "inlinemath": "equation",
    "figure": "figure",
    "picture": "figure",
    "figuregroup": "figure",
    "image": "figure",
    "table": "table",
    "tablegroup": "table",
}

# Heading/lead-text cues, checked in priority order (first match wins). Each entry
# is (compiled regex, role). "Worked Example" must beat "Example"; "Solution"
# must beat generic prose; "Exercises"/"Problems" map to exercise.
_CUES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bworked[\s\-]+examples?\b", re.IGNORECASE), "worked_example"),
    (re.compile(r"\bdefinitions?\b", re.IGNORECASE), "definition"),
    (re.compile(r"\b(?:theorems?|lemmas?|propositions?|corollar(?:y|ies)|claims?)\b", re.IGNORECASE), "theorem"),
    (re.compile(r"\bproof\b", re.IGNORECASE), "proof"),
    (re.compile(r"\bsolutions?\b", re.IGNORECASE), "solution"),
    (re.compile(r"\b(?:exercises?|problems?|problem\s+set)\b", re.IGNORECASE), "exercise"),
    (re.compile(r"\bexamples?\b", re.IGNORECASE), "worked_example"),
    (re.compile(r"\b(?:summary|summaries|key\s+takeaways?|recap)\b", re.IGNORECASE), "summary"),
    (re.compile(r"\b(?:references?|bibliography|works\s+cited|further\s+reading)\b", re.IGNORECASE), "reference"),
)

# Numbered-environment lead patterns like "Definition 4.2." or "Theorem 1 —".
# "Worked Example" must be recognized before the bare "Example" alternative.
_WORKED_LEAD_RE = re.compile(r"^\s*worked[\s\-]+examples?\b", re.IGNORECASE)
_ENVIRONMENT_WORDS = (
    "definition|theorem|lemma|proposition|corollary|claim|proof|example|exercise|problem|solution|remark"
)
_LEAD_RE = re.compile(rf"^\s*({_ENVIRONMENT_WORDS})\b", re.IGNORECASE)
_LEAD_ROLE = {
    "definition": "definition",
    "theorem": "theorem",
    "lemma": "theorem",
    "proposition": "theorem",
    "corollary": "theorem",
    "claim": "theorem",
    "proof": "proof",
    "example": "worked_example",
    "exercise": "exercise",
    "problem": "exercise",
    "solution": "solution",
}


# Words a heading may consist of when it names a whole exercise, solution or
# example unit ("Exercises", "Solutions to Selected Problems", "Problem Set 4",
# "Exercises for Section 5.3"), as opposed to a teaching section whose title
# merely contains such a word ("Solutions of linear systems", "The eigenvalue
# problem", "Least-squares problems"). Numbers and roman numerals are ignored.
_UNIT_WORDS = {
    "solution": "solution", "solutions": "solution", "answer": "solution", "answers": "solution",
    "hint": "solution", "hints": "solution",
    "exercise": "exercise", "exercises": "exercise", "problem": "exercise", "problems": "exercise",
    "homework": "exercise", "assignment": "exercise", "assignments": "exercise",
    "example": "worked_example", "examples": "worked_example", "worked": "worked_example",
}
_UNIT_FILLER = frozenset("""
a an the and to for of on in with set sets selected odd even numbered chapter chapters section sections
part parts review practice additional further more supplementary extra end unit lesson week
""".split())
_ROMAN_RE = re.compile(r"^[ivxlc]+$")
_UNIT_ROLE_ORDER = ("solution", "exercise", "worked_example")


def lead_role(text: str) -> str | None:
    """The role a block's own lead text names ("Solution:", "Example 5.2"), or None."""

    if _WORKED_LEAD_RE.match(text or ""):
        return "worked_example"
    lead = _LEAD_RE.match(text or "")
    if lead:
        return _LEAD_ROLE.get(lead.group(1).lower())
    return None


def unit_heading_role(heading: str | None) -> str | None:
    """The role of a heading that names a whole exercise, solution or example
    unit, or None for any other heading (a teaching section's title that only
    contains such a word)."""

    words = re.findall(r"[a-z]+", (heading or "").lower().replace("-", " "))
    words = [word for word in words if not _ROMAN_RE.match(word)]
    roles = {_UNIT_WORDS[word] for word in words if word in _UNIT_WORDS}
    if not roles or any(word not in _UNIT_WORDS and word not in _UNIT_FILLER for word in words):
        return None
    return next(role for role in _UNIT_ROLE_ORDER if role in roles)


def classify_block_role(
    block_type: str,
    section_path: list[str] | None,
    text: str,
) -> str:
    """Return the most likely pedagogical role for a block (§2.6)."""

    native = _BLOCK_TYPE_ROLES.get((block_type or "").replace(" ", "").lower())
    if native is not None:
        return native

    role = lead_role(text)
    if role is not None:
        return role

    # Nearest (deepest) heading in the section path dominates.
    heading = ""
    if section_path:
        for candidate in reversed(section_path):
            if candidate and candidate.lower() != "root":
                heading = candidate
                break
    haystack = heading.replace("-", " ")
    for pattern, role in _CUES:
        if pattern.search(haystack):
            return role

    return "ordinary_prose"


def positional_structure(blocks: Iterable[tuple[str, str]]) -> list[tuple[list[str], str]]:
    """Each block's ``(section_path, role_hint)`` derived from the given blocks alone, by
    POSITION: the section path is the nearest preceding ``SectionHeader``'s text (whitespace
    normalized), and the role is :func:`classify_block_role` over that path, as ingest classifies.

    ``blocks`` is ``(block_type, text)`` in reading order. Nothing else is read: no stored path, no
    extractor heading stack, no outline. The adaptive-difficulty projection derives both with it
    from the VISIBLE blocks of a reading, so a withheld header is nobody's heading, exactly as when
    it was never extracted (the AD23 redesign round 7)."""

    out: list[tuple[list[str], str]] = []
    heading: str | None = None
    for block_type, text in blocks:
        path = [] if heading is None else [heading]
        out.append((path, classify_block_role(block_type, path, text)))
        if (block_type or "").replace(" ", "") == "SectionHeader":
            heading = " ".join(str(text or "").split()) or None
    return out


# --- numbered environments and references to them -------------------------
#
# Tutor delivery fixes (2026-10-13): "by Theorem 3.2", "as in Example 1.4.13"
# or "Equation (3.4)" in a passage the tutor reads is resolved to the numbered
# block of the same extraction. The vocabulary is the lead words above, less
# the two that are not numbered environments of their own (a proof or a
# solution belongs to the statement it follows), plus equations.

NUMBERED_KINDS = frozenset({
    "definition", "theorem", "lemma", "proposition", "corollary", "claim",
    "example", "exercise", "problem", "remark", "equation",
})
_NUMBER = r"\d+(?:\.\d+)*"
# Markdown or marker furniture a label may sit behind: heading hashes, bold or
# italic marks, a quote bar, a starred-section marker.
_LABEL_PREFIX = r"^[\s#>*_★☆]*(?:\$\\bigstar\$\s*)?[*_]*"
# The number ends the label: then a name in parentheses, punctuation, a new
# sentence or the end ("Theorem 1.4.8 tells us ..." is a sentence about it).
_LABEL_END = r"(?=[*_]*(?:\s*[(.:;,\u2014\u2013-]|\s*$|\s+[A-Z$\\]))"
_NUMBERED_LEAD_RE = re.compile(
    _LABEL_PREFIX + rf"(?P<kind>(?i:{_ENVIRONMENT_WORDS}))\.?[*_]*\s+[*_]*(?P<number>(?>{_NUMBER})){_LABEL_END}"
)
# A number-first label ("1.20 definition: vector space", "★ 1.4.11 (Labeling
# objects)."): a dotted number leading the block, then optionally its kind.
_NUMBER_FIRST_RE = re.compile(
    # The number stands alone ("6.041SC Probabilistic ..." is a course code).
    _LABEL_PREFIX + rf"(?P<number>\d+(?:\.\d+)+)(?![0-9A-Za-z])\.?[*_]*"
    rf"(?:\s+(?P<kind>{_ENVIRONMENT_WORDS}|notation)\b)?",
    re.IGNORECASE,
)
_EQUATION_TAG_RE = re.compile(rf"\\tag\*?\{{\s*(?P<number>{_NUMBER})\s*\}}")
_EQUATION_END_RE = re.compile(rf"\(\s*(?P<number>{_NUMBER})\s*\)\s*(?:\$\$|\\\]|\$)?\s*$")
_EQUATION_BLOCK_TYPES = frozenset({"equation", "equationnumber", "math"})
# A table-of-contents line names a label without being it. Only strong
# evidence counts (Codex review F6): a TableOfContents block, leader dots
# ("Theorem 3.2 .......... 45"), or a page number in its own column (after a
# tab, a run of spaces or a table cell). A statement that merely ends in a
# number ("Theorem 3.2. The derivative of a constant is 0", Axler's "1.31 a
# number times the vector 0") is a label.
_TOC_LEADER_RE = re.compile(r"(?:\.\s*){4,}|…{2,}")
_TOC_COLUMN_RE = re.compile(r"(?:\t| {3,}|\|)\s*\d+\s*\|?\s*$")
_TOC_BLOCK_TYPES = frozenset({"tableofcontents"})

_REF_KINDS = {
    "definition": "definition", "definitions": "definition", "def.": "definition", "defs.": "definition",
    "theorem": "theorem", "theorems": "theorem", "thm.": "theorem", "thms.": "theorem",
    "lemma": "lemma", "lemmas": "lemma", "lemmata": "lemma", "lem.": "lemma",
    "proposition": "proposition", "propositions": "proposition", "prop.": "proposition",
    "props.": "proposition",
    "corollary": "corollary", "corollaries": "corollary", "cor.": "corollary",
    "claim": "claim", "claims": "claim",
    "example": "example", "examples": "example",
    "exercise": "exercise", "exercises": "exercise",
    "problem": "problem", "problems": "problem",
    "remark": "remark", "remarks": "remark",
    "equation": "equation", "equations": "equation", "eq.": "equation", "eqs.": "equation",
}
# Named references are capitalized ("Theorem 3.2"), so prose ("for example 2
# apples") never reads as one; an equation is often lower case ("equation (3.4)").
_REF_KIND_RE = (
    r"(?P<kind>Definitions?|Defs?\.|Theorems?|Thms?\.|Lemmata|Lemmas?|Lem\.|Propositions?|Props?\.|"
    r"Corollar(?:y|ies)|Cor\.|Claims?|Examples?|Exercises?|Problems?|Remarks?|[Ee]quations?|[Ee]qs?\.)"
)
_REF_ONE = rf"\(?{_NUMBER}\)?"
_REF_SEPARATOR = r"\s*(?:,\s*(?:and\s+|or\s+)?|and\s+|or\s+|&\s*|[–-]\s*)"
_REFERENCE_RE = re.compile(
    rf"(?<![\w.]){_REF_KIND_RE}\s*~?\s*(?P<numbers>{_REF_ONE}(?:{_REF_SEPARATOR}{_REF_ONE})*)"
)
# A bare number after a cue word ("by 1.32", "see 1.13"): books that number
# every result (number-first labels) refer to them this way. Resolved only
# against a number-first label of the same extraction.
_BARE_REFERENCE_RE = re.compile(r"\b(?i:by|see|in|from|using)\s+(?P<numbers>\d+\.\d+(?:\.\d+)*)(?![\d.]*\d)")
_NUMBER_IN_RE = re.compile(_NUMBER)


@dataclass(frozen=True)
class NumberedLabel:
    """A block's own number: ``kind`` (normalized; None for a bare number-first
    label such as "1.3 properties of complex arithmetic"), ``number``, and
    whether the number leads the block (``number_first``: the books that refer
    to results by bare number, "by 1.32")."""

    kind: str | None
    number: str
    number_first: bool = False

    @property
    def text(self) -> str:
        return f"{self.kind.capitalize()} {self.number}" if self.kind else self.number


@dataclass(frozen=True)
class NumberedReference:
    """One numbered environment a passage refers to, as written (``text``)."""

    kind: str | None
    number: str
    text: str
    start: int


def numbered_label(text: str, block_type: str = "") -> NumberedLabel | None:
    """The numbered environment a block opens ("Theorem 3.2 (Name). ...",
    "1.20 definition: vector space", an equation tagged "(3.4)"), or None.

    Proof and solution leads, and table-of-contents lines, are not labels."""

    value = text or ""
    if not value.strip() or (block_type or "").replace(" ", "").lower() in _TOC_BLOCK_TYPES:
        return None
    head = value.strip().splitlines()[0]
    if len(head) < 120 and (_TOC_LEADER_RE.search(head) or _TOC_COLUMN_RE.search(head)):
        return None
    lead = _NUMBERED_LEAD_RE.match(value)
    if lead:
        kind = lead.group("kind").lower()
        if kind in NUMBERED_KINDS:
            return NumberedLabel(kind, lead.group("number"))
        return None
    first = _NUMBER_FIRST_RE.match(value)
    if first:
        kind = (first.group("kind") or "").lower() or None
        if kind in {"proof", "solution"}:
            return None
        return NumberedLabel(kind if kind in NUMBERED_KINDS else None, first.group("number"), True)
    tag = _EQUATION_TAG_RE.search(value)
    if tag:
        return NumberedLabel("equation", tag.group("number"))
    if (block_type or "").replace(" ", "").lower() in _EQUATION_BLOCK_TYPES or value.lstrip().startswith(("$$", "\\[")):
        end = _EQUATION_END_RE.search(value)
        if end:
            return NumberedLabel("equation", end.group("number"))
    return None


def numbered_references(text: str) -> list[NumberedReference]:
    """The numbered environments ``text`` refers to, in order of appearance.

    "Theorems 1.4.7 and 1.4.8" names two; "Equation (3.4)" one equation; "by
    1.32" a bare number (``kind`` None). A block's own label is not a
    reference to it (the caller skips it)."""

    value = text or ""
    found: list[NumberedReference] = []
    seen: set[tuple[str | None, str]] = set()
    taken: list[tuple[int, int]] = []
    for match in _REFERENCE_RE.finditer(value):
        kind = _REF_KINDS.get(match.group("kind").lower())
        if kind is None:
            continue
        taken.append(match.span())
        for number in _NUMBER_IN_RE.finditer(match.group("numbers")):
            key = (kind, number.group(0))
            if key in seen:
                continue
            seen.add(key)
            label = "Equation" if kind == "equation" else kind.capitalize()
            found.append(NumberedReference(kind, number.group(0), f"{label} {number.group(0)}",
                                           match.start()))
    for match in _BARE_REFERENCE_RE.finditer(value):
        if any(start <= match.start() < end for start, end in taken):
            continue
        number = match.group("numbers")
        if (None, number) in seen:
            continue
        seen.add((None, number))
        found.append(NumberedReference(None, number, number, match.start("numbers")))
    return sorted(found, key=lambda reference: reference.start)
