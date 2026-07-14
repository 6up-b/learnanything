"""Deterministic semantic fingerprint for content facets (knowledge-model §3.2).

The fingerprint is a hash of a facet's *normalized semantic contract* — kind,
claim, conditions, examples, non-goals, error signatures, and instructional
repairs. It proposes cross-vault reuse/equivalence when importing or comparing
vaults; it NEVER asserts equivalence (that requires a reviewed import mapping,
§3.4). Naming/lifecycle fields (id, aliases, status, version, provenance,
concept_id, tags, title, description) are excluded so a rename or wording
refinement of surrounding metadata never changes identity.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

# Fields, in canonical order, that constitute the semantic contract.
_CONTRACT_SCALAR_FIELDS = ("kind", "claim")
_CONTRACT_LIST_FIELDS = (
    "preconditions",
    "postconditions",
    "applicability",
    "positive_examples",
    "negative_examples",
    "non_goals",
    "error_signatures",
    "instructional_repairs",
)

_WHITESPACE = re.compile(r"\s+")

FINGERPRINT_PREFIX = "sf_"


def _normalize_text(value: Any) -> str:
    """Lowercase, strip, and collapse internal whitespace."""

    if value is None:
        return ""
    return _WHITESPACE.sub(" ", str(value).strip().lower())


def _normalize_list(values: Any) -> list[str]:
    """Normalize each entry, drop empties, and sort so order is not identity."""

    if values is None:
        return []
    if isinstance(values, (str, bytes)):
        items: Sequence[Any] = [values]
    elif isinstance(values, Sequence):
        items = values
    else:
        items = [values]
    normalized = [_normalize_text(item) for item in items]
    return sorted(text for text in normalized if text)


def normalized_contract(facet: Any) -> dict[str, Any]:
    """Extract and normalize the semantic contract from a facet-like object.

    Accepts a mapping or any object exposing the contract attributes (e.g. the
    ``EvidenceFacet`` pydantic model), so it works both at load time and on raw
    YAML/proposal payloads before a model is built.
    """

    def _get(name: str) -> Any:
        if isinstance(facet, Mapping):
            return facet.get(name)
        return getattr(facet, name, None)

    contract: dict[str, Any] = {}
    for field in _CONTRACT_SCALAR_FIELDS:
        contract[field] = _normalize_text(_get(field))
    for field in _CONTRACT_LIST_FIELDS:
        contract[field] = _normalize_list(_get(field))
    return contract


def semantic_fingerprint(facet: Any) -> str:
    """Deterministic ``sf_...`` fingerprint of a facet's normalized contract."""

    contract = normalized_contract(facet)
    canonical = json.dumps(contract, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"{FINGERPRINT_PREFIX}{digest[:16]}"
