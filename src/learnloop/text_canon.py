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
  :func:`collapse_whitespace`. It is idempotent, and every later whitespace
  collapse leaves it unchanged, so no downstream transform of the sent text
  can raise what the guard scored.

This module imports nothing from LearnLoop: the practice index, the
retrieval package and the tutor package all read it.
"""
from __future__ import annotations

import unicodedata


def collapse_whitespace(text: str | None) -> str:
    """Whitespace runs as one space, the ends trimmed."""

    return " ".join((text or "").split())


def canonical(text: str | None) -> str:
    """NFKC, no invisible format characters, whitespace collapsed (idempotent)."""

    value = unicodedata.normalize("NFKC", str(text or ""))
    value = "".join(char for char in value if unicodedata.category(char) != "Cf")
    return collapse_whitespace(value)


__all__ = ["canonical", "collapse_whitespace"]
