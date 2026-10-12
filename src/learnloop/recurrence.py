"""The recurrence-key seam (Slice 1 §7.6), dependency-neutral.

Every site that asks "is this the same hypothesis as that one?" groups by
``recurrence_key(hypothesis)``. In Slice 1 it is exactly the exact-statement
key the sites used before (``statement_normalized``), so routing them through
it changes no behaviour. Slice 2 T1 swaps this body for a recurrence-group id
(validated citations + adjudicated would-merge pairs) and every grouping site
follows: candidate projection, holding-pen lookups, factor signatures, the K=3
recurrence count, durable promotion and error-hunt minting.

It lives below the domains (like ``algorithm_versions``) because the
repository's candidate projection is one of its callers.
"""

from __future__ import annotations

from typing import Any, Mapping

#: Identity of the grouping rule; T1 bumps it with its successor.
RECURRENCE_KEY_VERSION = "statement-normalized-v1"


def recurrence_key(hypothesis: Mapping[str, Any]) -> str:
    """The group a hypothesis (or projected candidate) recurs under."""

    value = hypothesis.get("statement_normalized")
    return "" if value is None else str(value)


__all__ = ["RECURRENCE_KEY_VERSION", "recurrence_key"]
