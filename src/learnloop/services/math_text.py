"""Deterministic Unicode-math <-> LaTeX bridging for quote anchoring.

Selections captured off rendered surfaces (the pdf.js text layer, KaTeX HTML)
carry Unicode math codepoints (``𝑧``, ``𝜆``, ``∈``, ``√``) where the extraction
text stores LaTeX (``$z$``, ``\\lambda``, ``\\in``, ``\\sqrt``). Anchoring a
quote across that divide needs a shared canonical space: both sides reduce to
the same symbol-token stream — structure (``^``, ``_``, braces, style macros)
is dropped, because the rendered glyph text never had it. ``locate_by_canonical``
finds the quote's token stream inside the block's and maps back to codepoint
offsets in the ORIGINAL block text, so the anchored slice keeps its LaTeX.

``unicode_math_to_latex`` is the lossy fallback for text that never anchors
(pypdf-extracted blocks, scanned pages): it upgrades Unicode math runs to
``$``-wrapped LaTeX so a learner edits ``\\lambda`` instead of ``𝜆``. It cannot
recover sub/superscripts that were already flattened upstream — that is why
anchoring into the extraction's own LaTeX is always preferred.

Pure functions, no I/O, no clock.
"""

from __future__ import annotations

import difflib
import re
import unicodedata

# Canonical acceptance: most of the quote's canonical tokens must align inside
# one window of the block, and the window must not balloon far past the quote
# (mirrors the fuzzy tier, but tighter — canonical space should agree well).
CANONICAL_COVERAGE_MIN = 0.75
CANONICAL_WINDOW_SLACK = 8

# Greek letters share one canonical name with their LaTeX commands. LaTeX
# ``\lambda`` maps automatically (unknown commands canonicalize to their own
# name); Unicode needs the explicit table because unicodedata spells it LAMDA.
GREEK: dict[str, str] = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "epsilon",
    "ϵ": "epsilon", "ζ": "zeta", "η": "eta", "θ": "theta", "ϑ": "theta",
    "ι": "iota", "κ": "kappa", "λ": "lambda", "μ": "mu", "ν": "nu",
    "ξ": "xi", "π": "pi", "ϖ": "pi", "ρ": "rho", "ϱ": "rho",
    "σ": "sigma", "ς": "sigma", "τ": "tau", "υ": "upsilon", "φ": "phi",
    "ϕ": "phi", "χ": "chi", "ψ": "psi", "ω": "omega",
    "Γ": "Gamma", "Δ": "Delta", "Θ": "Theta", "Λ": "Lambda", "Ξ": "Xi",
    "Π": "Pi", "Σ": "Sigma", "Υ": "Upsilon", "Φ": "Phi", "Ψ": "Psi",
    "Ω": "Omega",
}

# Unicode symbol -> canonical name (LaTeX command without the backslash where
# one exists). Symbols canonicalizing to a keep-punct character (e.g. the
# minus sign) map to that character instead.
SYMBOLS: dict[str, str] = {
    "…": "dots", "⋯": "dots", "−": "-", "±": "pm", "∓": "mp",
    "×": "times", "÷": "div", "⋅": "cdot", "·": "cdot", "∘": "circ",
    "√": "sqrt", "∞": "infty", "∂": "partial", "∇": "nabla",
    "∈": "in", "∉": "notin", "∋": "ni", "∅": "emptyset",
    "∪": "cup", "∩": "cap", "⊂": "subset", "⊆": "subseteq",
    "⊃": "supset", "⊇": "supseteq", "∖": "setminus",
    "≤": "leq", "⩽": "leq", "≥": "geq", "⩾": "geq", "≠": "neq",
    "≈": "approx", "∼": "sim", "≃": "simeq", "≅": "cong",
    "≡": "equiv", "∝": "propto", "⊥": "perp", "∥": "|", "∠": "angle",
    "∀": "forall", "∃": "exists", "¬": "neg", "∧": "wedge", "∨": "vee",
    "⊕": "oplus", "⊗": "otimes", "⊙": "odot",
    "∑": "sum", "∏": "prod", "∫": "int", "∮": "oint",
    "→": "to", "⟶": "to", "←": "leftarrow", "↦": "mapsto",
    "⇒": "implies", "⇐": "impliedby", "⇔": "iff",
    "⟨": "langle", "⟩": "rangle", "′": "prime", "″": "prime",
    "‖": "|", "∣": "|", "°": "circ",
}

# LaTeX command aliases folding onto one canonical name.
LATEX_ALIASES: dict[str, str] = {
    "le": "leq", "ge": "geq", "ne": "neq",
    "ldots": "dots", "cdots": "dots", "dotsc": "dots", "dotsb": "dots",
    "rightarrow": "to", "longrightarrow": "to",
    "Rightarrow": "implies", "Leftarrow": "impliedby", "Leftrightarrow": "iff",
    "land": "wedge", "lor": "vee", "lnot": "neg",
    "varepsilon": "epsilon", "vartheta": "theta", "varpi": "pi",
    "varrho": "rho", "varsigma": "sigma", "varphi": "phi",
    "varnothing": "emptyset",
    "lvert": "|", "rvert": "|", "vert": "|", "Vert": "|", "mid": "|",
    "parallel": "|", "lVert": "|", "rVert": "|",
}

# Style/layout commands carry no symbol identity — the rendered glyph side has
# no trace of them, so they vanish in canonical space.
STYLE_SKIP = {
    "mathbf", "mathbb", "mathrm", "mathit", "mathcal", "mathsf", "mathfrak",
    "mathscr", "boldsymbol", "bm", "text", "textbf", "textit", "textrm",
    "operatorname", "left", "right", "big", "Big", "bigg", "Bigg",
    "bigl", "bigr", "Bigl", "Bigr", "biggl", "biggr",
    "displaystyle", "textstyle", "scriptstyle", "limits", "nolimits",
    "quad", "qquad", "phantom", "vphantom", "hphantom", "notag", "nonumber",
}

# Punctuation that is meaningful on both surfaces and cheap to compare.
KEEP_PUNCT = set("=+-()[]|,;:.!?/<>*'")

_SUPERSCRIPTS = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
                 "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "ⁿ": "n", "ⁱ": "i"}
_SUBSCRIPTS = {"₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
               "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9"}

# Letterlike math symbols outside the Mathematical Alphanumeric block.
_LETTERLIKE = set("ℂℍℕℙℚℝℤℓℎℯℊℴℬℰℱℋℐℒℳℛ℘ℑℜ")


def _is_math_alphanumeric(ch: str) -> bool:
    return 0x1D400 <= ord(ch) <= 0x1D7FF or ch in _LETTERLIKE


def contains_unicode_math(text: str) -> bool:
    """True when the text carries Unicode math the extraction stores as LaTeX."""

    return any(
        _is_math_alphanumeric(ch)
        or ch in SYMBOLS
        or ch in GREEK
        or ch in _SUPERSCRIPTS
        or ch in _SUBSCRIPTS
        for ch in text
    )


Token = tuple[str, int, int]  # (canonical token, source start, source end)


def _char_tokens(ch: str, start: int, end: int) -> list[Token]:
    """Canonical tokens for one source character (shared by both surfaces).
    Letters and digits stay single-character tokens on purpose: the glyph
    surface has no word structure inside math (``𝑧𝑛`` folds to ``zn`` while the
    LaTeX side reads ``z_n``), so per-character alignment is the common grain."""

    if ch in SYMBOLS:
        return [(SYMBOLS[ch], start, end)]
    if ch in GREEK:
        return [(GREEK[ch], start, end)]
    if ch in _SUPERSCRIPTS:
        return [(_SUPERSCRIPTS[ch], start, end)]
    if ch in _SUBSCRIPTS:
        return [(_SUBSCRIPTS[ch], start, end)]
    # NFKC folds math-alphanumeric styling away (𝑧→z, 𝐂→C, 𝜆→λ); re-classify
    # each folded character so Greek/symbols still canonicalize by name.
    folded = unicodedata.normalize("NFKC", ch)
    tokens: list[Token] = []
    for sub in folded:
        if sub in SYMBOLS:
            tokens.append((SYMBOLS[sub], start, end))
        elif sub in GREEK:
            tokens.append((GREEK[sub], start, end))
        elif sub.isalnum():
            tokens.append((sub, start, end))
        elif sub in KEEP_PUNCT:
            tokens.append((sub, start, end))
        # everything else (whitespace, decorations) carries no anchor signal
    return tokens


def canonical_tokens(text: str) -> list[Token]:
    """Canonical token stream for rendered-surface text (Unicode math + prose)."""

    tokens: list[Token] = []
    for i, ch in enumerate(text):
        tokens.extend(_char_tokens(ch, i, i + 1))
    return tokens


_LATEX_COMMAND = re.compile(r"\\([a-zA-Z]+)|\\.")


def latex_tokens(text: str) -> list[Token]:
    """Canonical token stream for extraction text (LaTeX-bearing markdown)."""

    tokens: list[Token] = []
    i = 0
    length = len(text)
    while i < length:
        ch = text[i]
        if ch == "\\":
            match = _LATEX_COMMAND.match(text, i)
            if match and match.group(1):
                name = match.group(1)
                canon = LATEX_ALIASES.get(name, name)
                if name not in STYLE_SKIP:
                    tokens.append((canon, match.start(), match.end()))
                i = match.end()
                continue
            # Escaped single character (\{ \$ \%): structural, no signal.
            i += 2
            continue
        if ch in "${}^_&~":
            i += 1
            continue
        tokens.extend(_char_tokens(ch, i, i + 1))
        i += 1
    return tokens


def _find_contiguous(haystack: list[str], needle: list[str]) -> list[int]:
    """Start indexes of every contiguous occurrence of needle in haystack."""

    if not needle or len(needle) > len(haystack):
        return []
    hits: list[int] = []
    first = needle[0]
    for i in range(len(haystack) - len(needle) + 1):
        if haystack[i] == first and haystack[i : i + len(needle)] == needle:
            hits.append(i)
    return hits


def _snap_and_balance(text: str, start: int, end: int) -> tuple[int, int]:
    """Snap outward to whitespace, then keep ``$`` delimiters paired so the
    anchored slice renders as the math it points at."""

    while start > 0 and not text[start - 1].isspace():
        start -= 1
    while end < len(text) and not text[end].isspace():
        end += 1
    if text.count("$", start, end) % 2 == 1:
        closing = text.find("$", end)
        if closing != -1:
            end = closing + 1
        else:
            opening = text.rfind("$", 0, start)
            if opening != -1:
                start = opening
    return start, end


def locate_by_canonical(text: str, quote: str) -> tuple[int, int] | None:
    """Locate a rendered-surface quote inside LaTeX-bearing block text by
    aligning both in canonical symbol space; returns codepoint offsets into the
    ORIGINAL block text (so the caller's slice keeps its LaTeX), or None.

    An exact contiguous canonical match must be unique; with none, a difflib
    alignment covering >= ``CANONICAL_COVERAGE_MIN`` of the quote inside a
    non-degenerate window is accepted (tolerates residual OCR noise)."""

    text_tokens = latex_tokens(text)
    quote_tokens = canonical_tokens(quote)
    if not text_tokens or not quote_tokens:
        return None
    text_stream = [token for token, _, _ in text_tokens]
    quote_stream = [token for token, _, _ in quote_tokens]

    hits = _find_contiguous(text_stream, quote_stream)
    if len(hits) == 1:
        at = hits[0]
        start = text_tokens[at][1]
        end = text_tokens[at + len(quote_stream) - 1][2]
        return _snap_and_balance(text, start, end)
    if len(hits) > 1:
        return None  # ambiguous — honesty over a guess (§3.2)

    matcher = difflib.SequenceMatcher(None, text_stream, quote_stream, autojunk=False)
    matching = [b for b in matcher.get_matching_blocks() if b.size > 0]
    if not matching:
        return None
    matched = sum(b.size for b in matching)
    if matched / len(quote_stream) < CANONICAL_COVERAGE_MIN:
        return None
    first, last = matching[0], matching[-1]
    window = (last.a + last.size) - first.a
    if window > 2 * len(quote_stream) + CANONICAL_WINDOW_SLACK:
        return None
    start = text_tokens[first.a][1]
    end = text_tokens[last.a + last.size - 1][2]
    return _snap_and_balance(text, start, end)


# ---- lossy transliteration fallback ----------------------------------------

# A word joins a math run when it contains real math codepoints; pure
# digit/operator words act as connectors between mathy neighbors.
_CONNECTOR = re.compile(r"^[\d=+\-*/()\[\]|.,;:]+$")
_MATH_SEGMENT = re.compile(r"\$[^$]*\$")


def _word_is_mathy(word: str) -> bool:
    return contains_unicode_math(word)


def _transliterate_run(run: str) -> str:
    out: list[str] = []
    for ch in run:
        if ch in SYMBOLS:
            name = SYMBOLS[ch]
            out.append(name if name in KEEP_PUNCT else f"\\{name} ")
        elif ch in GREEK:
            out.append(f"\\{GREEK[ch]} ")
        elif ch in _SUPERSCRIPTS:
            out.append(f"^{{{_SUPERSCRIPTS[ch]}}}")
        elif ch in _SUBSCRIPTS:
            out.append(f"_{{{_SUBSCRIPTS[ch]}}}")
        elif _is_math_alphanumeric(ch):
            folded = unicodedata.normalize("NFKC", ch)
            if folded in GREEK:
                out.append(f"\\{GREEK[folded]} ")
            else:
                out.append(folded)
        else:
            out.append(ch)
    text = "".join(out)
    text = re.sub(r"(\\[a-zA-Z]+) (?=[^a-zA-Z]|$)", r"\1", text)  # keep space only before letters
    return f"${text.strip()}$"


def unicode_math_to_latex(text: str) -> tuple[str, bool]:
    """Upgrade Unicode math runs to ``$``-wrapped LaTeX, leaving existing
    ``$...$`` regions and plain prose untouched. Returns (text, changed).
    Lossy by construction (flattened sub/superscripts stay flattened) — this is
    the fallback for surfaces that could not anchor into extraction LaTeX."""

    if not contains_unicode_math(text):
        return text, False

    def convert_outside_math(segment: str) -> str:
        parts = re.split(r"(\s+)", segment)
        words = [(i, w) for i, w in enumerate(parts) if w and not w.isspace()]
        mathy = {i for i, w in words if _word_is_mathy(w)}
        if not mathy:
            return segment
        # Grow each mathy word rightward over connector words (digits, bare
        # operators) so `𝑧 = (𝑧1` and `𝜆² ≥ 0` stay one $...$ run each.
        in_run = set(mathy)
        for pos, (i, w) in enumerate(words):
            if i in mathy:
                continue
            if _CONNECTOR.match(w) and pos > 0 and words[pos - 1][0] in in_run:
                in_run.add(i)
        out: list[str] = []
        run: list[str] = []
        for i, part in enumerate(parts):
            if i in in_run:
                run.append(part)
            elif part.isspace() and run and any(
                j in in_run for j in range(i + 1, min(i + 2, len(parts)))
            ):
                run.append(part)
            else:
                if run:
                    out.append(_transliterate_run("".join(run)))
                    run = []
                out.append(part)
        if run:
            out.append(_transliterate_run("".join(run)))
        return "".join(out)

    pieces: list[str] = []
    last = 0
    for match in _MATH_SEGMENT.finditer(text):
        pieces.append(convert_outside_math(text[last : match.start()]))
        pieces.append(match.group(0))
        last = match.end()
    pieces.append(convert_outside_math(text[last:]))
    result = "".join(pieces)
    return result, result != text
