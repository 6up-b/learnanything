"""What the facet-identity judge sees, and what a merge or absorb writes.

A facet's judge view is its semantic contract, compacted: kind, claim, the
concept it belongs to, and a few conditions and examples. Ids and provenance
never reach the judge (they would anchor it on wording that says nothing about
the skill).

``union_payload`` is the one definition of what ``merge`` and ``absorb`` do to
the surviving facet, shared by the in-run consolidation, the attach decision
and the vault-level dedupe:

* ``merge``: the retired facets state the same testable skill. The survivor
  keeps its own claim, kind and concept; their conditions, examples,
  non-goals, error signatures, repairs, tags and source references are
  unioned in (order kept, survivor first, exact repeats dropped).
* ``absorb``: each retired facet is a special case or worked instance of the
  survivor. Its claim becomes a positive example (``absorb_as="example"``) or a
  precondition (``"precondition"``) of the survivor, and its lists are
  unioned as for a merge.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import copy
import re
from typing import Any

#: The facet payload lists a merge or absorb unions into the survivor.
UNION_LIST_FIELDS = (
    "preconditions",
    "postconditions",
    "applicability",
    "positive_examples",
    "negative_examples",
    "non_goals",
    "error_signatures",
    "instructional_repairs",
    "tags",
)
ABSORB_AS = ("example", "precondition")
_TEXT_LIMIT = 320
_SPACE = re.compile(r"\s+")


def _text(value: Any, limit: int = _TEXT_LIMIT) -> str:
    text = _SPACE.sub(" ", str(value or "")).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _texts(values: Any, count: int) -> list[str]:
    out: list[str] = []
    for value in values or []:
        text = _text(value)
        if text and text not in out:
            out.append(text)
        if len(out) >= count:
            break
    return out


def judge_view(payload: Mapping[str, Any], *, concept_title: str | None = None) -> dict[str, Any]:
    """The compact, id-free contract one facet shows the judge."""

    view: dict[str, Any] = {
        "kind": str(payload.get("kind") or "definition"),
        "claim": _text(payload.get("claim") or payload.get("title") or payload.get("description") or ""),
    }
    if concept_title:
        view["concept"] = _text(concept_title, 120)
    for key, field, count in (
        ("preconditions", "preconditions", 4),
        ("applicability", "applicability", 2),
        ("examples", "positive_examples", 2),
        ("non_examples", "negative_examples", 1),
        ("non_goals", "non_goals", 2),
    ):
        values = _texts(payload.get(field), count)
        if values:
            view[key] = values
    return view


def _norm(value: Any) -> str:
    return _SPACE.sub(" ", str(value or "")).strip().casefold()


def _union_strings(base: Sequence[Any], additions: Iterable[Any]) -> list[Any]:
    out = list(base or [])
    seen = {_norm(value) for value in out}
    for value in additions:
        key = _norm(value)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def _ref_key(ref: Any) -> str:
    if isinstance(ref, Mapping):
        return "|".join(
            str(ref.get(key) or "")
            for key in ("ref_type", "ref_id", "extraction_id", "locator", "relation", "revision_id")
        )
    return str(ref)


def _union_refs(base: Sequence[Any], additions: Iterable[Any]) -> list[Any]:
    out = [copy.deepcopy(ref) for ref in base or []]
    seen = {_ref_key(ref) for ref in out}
    for ref in additions:
        key = _ref_key(ref)
        if key in seen:
            continue
        seen.add(key)
        out.append(copy.deepcopy(ref))
    return out


def union_payload(
    survivor: Mapping[str, Any],
    retired: Sequence[Mapping[str, Any]],
    *,
    action: str,
    absorb_as: str | None = None,
    alias_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """The survivor's payload after ``merge``/``absorb`` of ``retired`` into it.

    ``alias_ids`` are added to the survivor's ``aliases`` (the retired facet
    ids, so every reference to them keeps resolving); a retired facet's own
    aliases come along too. The input mappings are not modified.
    """

    if action not in ("merge", "absorb"):
        raise ValueError(f"unknown facet identity action {action!r}")
    if action == "absorb" and absorb_as not in ABSORB_AS:
        absorb_as = "example"
    merged = copy.deepcopy(dict(survivor))
    survivor_id = str(merged.get("id") or "")
    for field in UNION_LIST_FIELDS:
        additions: list[Any] = []
        for payload in retired:
            if action == "absorb" and field == (
                "positive_examples" if absorb_as == "example" else "preconditions"
            ):
                claim = str(payload.get("claim") or "").strip()
                if claim:
                    additions.append(claim)
            additions.extend(payload.get(field) or [])
        if additions or field in merged:
            merged[field] = _union_strings(merged.get(field) or [], additions)
    aliases = [*(merged.get("aliases") or [])]
    for alias in [*alias_ids, *(alias for payload in retired for alias in (payload.get("aliases") or []))]:
        if alias and alias != survivor_id and _norm(alias) not in {_norm(a) for a in aliases}:
            aliases.append(alias)
    merged["aliases"] = aliases
    provenance = merged.get("provenance")
    retired_refs = [
        ref
        for payload in retired
        for ref in ((payload.get("provenance") or {}).get("source_refs") or [] if isinstance(payload.get("provenance"), Mapping) else [])
    ]
    if isinstance(provenance, Mapping):
        provenance = dict(provenance)
        provenance["source_refs"] = _union_refs(provenance.get("source_refs") or [], retired_refs)
        merged["provenance"] = provenance
    elif retired_refs:
        merged["provenance"] = {"origin": "sourceset_synthesis", "source_refs": _union_refs([], retired_refs)}
    return merged


def comparable_entry(entry: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """A facets.yaml entry with the fields a write recomputes removed.

    Used to decide whether an entry is still exactly what an action wrote
    (undo refuses to overwrite a later edit).
    """

    if entry is None:
        return None
    out = copy.deepcopy(dict(entry))
    out.pop("semantic_fingerprint", None)
    return out


__all__ = [
    "ABSORB_AS",
    "UNION_LIST_FIELDS",
    "comparable_entry",
    "judge_view",
    "union_payload",
]
