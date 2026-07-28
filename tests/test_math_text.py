"""Unicode-math ↔ LaTeX bridging: canonical anchoring + transliteration fallback.

The motivating pair (a real pdf.js text-layer capture vs. marker's extraction
text): the rendered surface carries Mathematical Alphanumeric codepoints and
symbol characters; the block text carries $-delimited LaTeX. The canonical
tier must anchor the former onto the latter and hand back the LaTeX slice.
"""

from learnloop.services.annotations import _locate_quote
from learnloop.services.math_text import (
    canonical_tokens,
    contains_unicode_math,
    latex_tokens,
    locate_by_canonical,
    unicode_math_to_latex,
)

BLOCK_INLINE = (
    "Complex numbers were defined earlier so that every polynomial has a root; "
    "for $z = (z_1, \\dots , z_n) \\in \\mathbf{C}^n$ the coordinates are complex."
)
QUOTE_INLINE = "𝑧 = (𝑧1, … , 𝑧𝑛) ∈ 𝐂𝑛"

BLOCK_ABS = (
    "For $\\lambda = a + bi$, the absolute value of $\\lambda$, denoted by "
    "$|\\lambda|$, is defined by $|\\lambda| = \\sqrt{a^2+b^2}$; it is a norm."
)
QUOTE_ABS = "the absolute value of 𝜆, denoted by |𝜆|, is defined by |𝜆| = √𝑎2 + 𝑏2;"


def test_canonical_streams_agree_across_surfaces():
    glyphs = [token for token, _, _ in canonical_tokens(QUOTE_INLINE)]
    latex = [token for token, _, _ in latex_tokens("$z = (z_1, \\dots , z_n) \\in \\mathbf{C}^n$")]
    assert glyphs == latex


def test_locate_by_canonical_returns_latex_slice():
    located = locate_by_canonical(BLOCK_INLINE, QUOTE_INLINE)
    assert located is not None
    start, end = located
    slice_ = BLOCK_INLINE[start:end]
    assert "$z = (z_1, \\dots , z_n) \\in \\mathbf{C}^n$" in slice_
    assert slice_.count("$") % 2 == 0  # delimiters stay paired


def test_locate_quote_anchors_unicode_math_onto_latex():
    located = _locate_quote(BLOCK_ABS, QUOTE_ABS)
    assert located is not None
    start, end = located
    slice_ = BLOCK_ABS[start:end]
    assert "\\sqrt{a^2+b^2}" in slice_
    assert "the absolute value of $\\lambda$" in slice_
    assert "𝜆" not in slice_


def test_locate_quote_exact_match_unaffected():
    text = "plain prose block with no math at all"
    assert _locate_quote(text, "prose block") == (6, 17)


def test_ambiguous_canonical_match_refuses():
    text = "first $x_1$ here and later $x_1$ again"
    assert locate_by_canonical(text, "𝑥1") is None


def test_contains_unicode_math():
    assert contains_unicode_math(QUOTE_INLINE)
    assert contains_unicode_math("the eigenvalue 𝜆 grows")
    assert not contains_unicode_math("plain prose, even with $x_1$ latex")


def test_transliteration_upgrades_runs_and_reports_change():
    result, changed = unicode_math_to_latex(QUOTE_INLINE)
    assert changed
    assert "\\in" in result
    assert "\\dots" in result
    assert result.startswith("$") and result.endswith("$")
    assert not contains_unicode_math(result)


def test_transliteration_leaves_prose_and_existing_latex_alone():
    text = "the absolute value is $|\\lambda|$ as defined before"
    result, changed = unicode_math_to_latex(text)
    assert not changed
    assert result == text


def test_transliteration_mixed_prose():
    result, changed = unicode_math_to_latex("the eigenvalue 𝜆 satisfies 𝜆² ≥ 0 always")
    assert changed
    assert "\\lambda" in result
    assert "^{2}" in result
    assert "\\geq" in result
    assert result.endswith("always")
    assert not contains_unicode_math(result)
