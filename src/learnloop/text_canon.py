"""One definition of how text is canonicalised before it is matched or sent
(RW1c fix round 11).

Two readers must agree, so they share these functions rather than copies:

* :func:`collapse_whitespace` is the search's and the query rewrite's own
  normalisation (``practice_index.query_vectors.normalize_query`` is this
  function): every whitespace run, newlines, tabs and no-break spaces
  included, becomes one space, and the ends are trimmed.
* :func:`canonical` is what the bound Reader's answer guard scores and what
  its delivery plan sends for every model-written text
  (``tutor.reader_modes.plan_bound_delivery``): Unicode NFKC, then the
  invisible format characters (zero-width spaces and joiners, the byte-order
  mark, soft hyphens: category ``Cf``) removed, then
  :func:`collapse_whitespace`, repeated to a fixed point (fix round 12). It
  is idempotent, and every later whitespace collapse leaves it unchanged, so
  no downstream transform of the sent text can raise what the guard scored;
  the guard scores exactly the delivered text, never a transform of it.

This module imports nothing from LearnLoop: the practice index, the
retrieval package and the tutor package all read it.
"""
from __future__ import annotations

import unicodedata


def collapse_whitespace(text: str | None) -> str:
    """Whitespace runs as one space, the ends trimmed."""

    return " ".join((text or "").split())


#: More passes than any input needs: each pass after the first can only
#: compose what removing a format character exposed (fix round 12).
_MAX_PASSES = 16


def _pass(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = "".join(char for char in value if unicodedata.category(char) != "Cf")
    return collapse_whitespace(value)


def canonical(text: str | None) -> str:
    """NFKC, no invisible format characters, whitespace collapsed: a true
    fixed point, ``canonical(canonical(x)) == canonical(x)``.

    One pass is not enough (RW1c fix round 12): removing a format character
    can expose a new composition ("A", a zero-width space, a combining ring:
    the pass leaves "A" + ring, the next composes "Å"). The pass is repeated
    until nothing changes."""

    value = _pass(str(text or ""))
    for _ in range(_MAX_PASSES):
        again = _pass(value)
        if again == value:
            return value
        value = again
    raise ValueError("text did not reach a canonical form")  # never seen; fail loudly, not silently


__all__ = ["canonical", "collapse_whitespace"]
