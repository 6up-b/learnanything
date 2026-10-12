"""Deterministic block-role hints (spec_source_ingestion_v2 §2.6).

Annotate likely pedagogical roles from headings and block context — external to
any marker processor. These are *hints*, not semantic truth; they shrink
inventory prompts and let role-aware treatment differ (problem sets emphasize
exercises; papers emphasize claims/limitations). "Definition 4.2", "Exercises",
and "Worked Example" are recognizable deterministically.
"""

from __future__ import annotations

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
_LEAD_RE = re.compile(
    r"^\s*(definition|theorem|lemma|proposition|corollary|claim|proof|example|exercise|problem|solution|remark)\b",
    re.IGNORECASE,
)
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
