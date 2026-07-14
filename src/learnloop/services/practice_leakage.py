"""ING M8 — cross-source practice generation leakage controls (spec §8.5, §14).

Two deterministic instruments here are CODE, not prompt instructions:

* ``build_held_out_inventory`` — the normalized word-shingle + numeric-literal
  fingerprint of every held-out exam span text vault-wide (§4.2 use modes).
  Held-out questions/answers/numbers must never surface in generated practice.
* ``screen_practice_payload`` / ``check_leakage`` — a deterministic gate that
  flags any generated surface reproducing a held-out contiguous word-shingle or a
  distinctive numeric literal. A gate, not a prompt hope: the generation flow
  blocks (never auto-applies) any item the gate flags.

Plus the cross-source practice CONTEXT builder (``build_cross_source_spans``):
bounded ``entity_source_links`` spans for a learning object's facets, semantic
authority first and alternates for variety, capped PER ITEM so the per-item
context never grows with source count (knowledge-model §12.9).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.services.source_outline import resolve_extraction_id
from learnloop.vault.models import LoadedVault

# Default contiguous word-shingle order for the wording-overlap gate. Six words
# is long enough that innocuous shared phrasing ("the derivative of the") does not
# trip it, but any reproduced held-out sentence fragment does.
DEFAULT_SHINGLE_N = 6

# Semantic-authority relation priority (§9.1). ``exercise`` / ``assessment_alignment``
# are assessment lanes and are NEVER placed in a teaching/generation context.
_SEMANTIC_RELATION_PRIORITY = {"primary": 0, "support": 1, "alternate": 2}

# A cited span's text is truncated in the generation context; the gate uses the
# held-out inventory, not these snippets, to catch leakage.
_SPAN_TEXT_CAP = 600


@dataclass(frozen=True)
class HeldOutInventory:
    """Deterministic fingerprint of held-out exam text (§8.5)."""

    shingles: frozenset[str] = frozenset()
    numerics: frozenset[str] = frozenset()
    shingle_n: int = DEFAULT_SHINGLE_N
    span_count: int = 0

    @property
    def empty(self) -> bool:
        return not self.shingles and not self.numerics


@dataclass(frozen=True)
class CrossSourceSpan:
    extraction_id: str
    span_id: str
    relation: str
    semantic_authority: bool
    source_id: str | None
    label: str
    text: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "extraction_id": self.extraction_id,
            "span_id": self.span_id,
            "relation": self.relation,
            "semantic_authority": self.semantic_authority,
            "source_id": self.source_id,
            "label": self.label,
            "text": self.text,
        }


# --- normalization ----------------------------------------------------------


def _normalize_tokens(text: str) -> list[str]:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).split()


def _shingles(tokens: list[str], n: int) -> set[str]:
    if n <= 0 or len(tokens) < n:
        # Short texts contribute their whole normalized form so a reproduced
        # short held-out phrase is still caught.
        return {" ".join(tokens)} if tokens else set()
    return {" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def _numeric_literals(text: str) -> set[str]:
    """Distinctive numeric literals: multi-digit integers, decimals, fractions,
    or percentages. Ubiquitous small integers (< 3 significant chars, no decimal)
    are excluded so the numeric gate does not false-positive on ``2`` or ``10``."""

    out: set[str] = set()
    for token in re.findall(r"\d[\d.,/%]*", text):
        stripped = token.rstrip(".,")
        digits = re.sub(r"[^0-9]", "", stripped)
        if not digits:
            continue
        distinctive = len(digits) >= 3 or any(ch in stripped for ch in "./%")
        if distinctive:
            out.add(stripped)
    return out


# --- held-out inventory -----------------------------------------------------


def _held_out_span_texts(
    vault: LoadedVault, repository: Repository, *, subject_ids: set[str] | None
) -> list[str]:
    """Resolve the text of every held-out exam span vault-wide (§4.2 use modes).

    Mirrors ``source_set_synthesis._collect_inputs`` held-out logic: an exam-role
    unit contributes its held-out assessment-signal spans, and a whole
    ``held_out_evaluation`` unit contributes all its spans.
    """

    texts: list[str] = []
    for source_set in vault.source_sets:
        if subject_ids is not None and source_set.subject_id not in subject_ids:
            continue
        for member in source_set.members:
            role_overrides = {s.unit_id: s.role_override for s in member.scope if s.role_override}
            is_exam_member = member.default_role == "exam" or "exam" in role_overrides.values()
            if not is_exam_member:
                continue
            extraction_id = resolve_extraction_id(repository, member.revision_id)
            if extraction_id is None:
                continue
            ir = repository.load_document_ir(extraction_id)
            if ir is None:
                continue
            selection = repository.get_unit_selection(extraction_id) or {}
            exam_use_modes = selection.get("exam_use_modes", {}) or {}
            unit_span_ids = {u.unit_id: set(u.span_ids) for u in ir.units}
            scope_units = [s.unit_id for s in member.scope] or [u.unit_id for u in ir.units]
            inventories = {
                row["unit_id"]: row["inventory"]
                for row in repository.unit_inventories_for_revision(member.revision_id)
                if row.get("inventory")
            }
            for unit_id in scope_units:
                effective_role = role_overrides.get(unit_id, member.default_role)
                if effective_role != "exam":
                    continue
                whole_unit = exam_use_modes.get(unit_id) == "held_out_evaluation"
                span_ids: set[str] = set()
                if whole_unit:
                    span_ids |= unit_span_ids.get(unit_id, set())
                inventory = inventories.get(unit_id)
                if inventory:
                    for signal in inventory.get("assessment_signals", []) or []:
                        if whole_unit or signal.get("held_out"):
                            span_ids |= {str(s) for s in signal.get("span_ids", []) or []}
                for span_id in span_ids:
                    block = ir.block_by_span(span_id)
                    if block is not None and block.text:
                        texts.append(block.text)
    return texts


def build_held_out_inventory(
    vault: LoadedVault,
    repository: Repository,
    *,
    subject_ids: list[str] | None = None,
    shingle_n: int = DEFAULT_SHINGLE_N,
) -> HeldOutInventory:
    """Fingerprint every held-out exam span text vault-wide (§8.5)."""

    subjects = set(subject_ids) if subject_ids else None
    texts = _held_out_span_texts(vault, repository, subject_ids=subjects)
    shingles: set[str] = set()
    numerics: set[str] = set()
    for text in texts:
        shingles |= _shingles(_normalize_tokens(text), shingle_n)
        numerics |= _numeric_literals(text)
    return HeldOutInventory(
        shingles=frozenset(shingles),
        numerics=frozenset(numerics),
        shingle_n=shingle_n,
        span_count=len(texts),
    )


# --- the gate ---------------------------------------------------------------


def check_leakage(text: str, inventory: HeldOutInventory) -> list[dict[str, str]]:
    """Deterministic overlap findings between ``text`` and held-out material.

    A finding is a reproduced held-out word-shingle or a distinctive numeric
    literal. Returns [] when nothing overlaps (or the inventory is empty)."""

    if inventory.empty or not text:
        return []
    findings: list[dict[str, str]] = []
    tokens = _normalize_tokens(text)
    for shingle in sorted(_shingles(tokens, inventory.shingle_n) & inventory.shingles):
        findings.append({"kind": "wording", "value": shingle})
    for numeric in sorted(_numeric_literals(text) & inventory.numerics):
        findings.append({"kind": "numeric", "value": numeric})
    return findings


def _payload_surfaces(payload: dict[str, Any]) -> str:
    """Concatenate the learner-visible surfaces of a practice-item payload.

    Prompt + expected answer + rubric criterion descriptions — the surfaces the
    §8.5 rule protects (wording, numbers, answer structure)."""

    parts: list[str] = []
    prompt = payload.get("prompt")
    if isinstance(prompt, str):
        parts.append(prompt)
    expected = payload.get("expected_answer")
    if isinstance(expected, str):
        parts.append(expected)
    elif isinstance(expected, dict):
        parts.append(" ".join(str(v) for v in expected.values() if isinstance(v, (str, int, float))))
    rubric = payload.get("grading_rubric") or {}
    for criterion in (rubric.get("criteria") or []) if isinstance(rubric, dict) else []:
        if isinstance(criterion, dict):
            for key in ("description", "expected_evidence"):
                value = criterion.get(key)
                if isinstance(value, str):
                    parts.append(value)
    return "\n".join(parts)


def screen_practice_payload(payload: dict[str, Any], inventory: HeldOutInventory) -> list[dict[str, str]]:
    """Leakage findings for one generated practice-item payload (§14)."""

    return check_leakage(_payload_surfaces(payload), inventory)


# --- cross-source context ---------------------------------------------------


def _lo_facet_ids(vault: LoadedVault, learning_object) -> list[str]:
    """Canonical facet ids a learning object teaches: blueprint recipe components
    plus its practice items' evidence facets."""

    facets: set[str] = set()
    for blueprint in learning_object.blueprints or []:
        for recipe in blueprint.recipes or []:
            for comp in [*(recipe.all_of or []), *(recipe.any_of or [])]:
                facets.add(vault.canonical_facet_id(comp.facet))
            if recipe.integration is not None:
                facets.add(vault.canonical_facet_id(recipe.integration.facet))
    for item in vault.practice_items.values():
        if item.learning_object_id == learning_object.id:
            facets.update(vault.canonical_facet_id(f) for f in item.evidence_facets)
    return sorted(facets)


def _span_text(repository: Repository, extraction_id: str, span_id: str) -> str | None:
    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        return None
    block = ir.block_by_span(span_id)
    if block is None or not block.text:
        return None
    text = block.text.strip()
    return text[:_SPAN_TEXT_CAP]


def _span_id_from_locator(locator: str | None) -> str | None:
    if not locator:
        return None
    from learnloop.ingest.locators import parse_block_span

    parsed = parse_block_span(locator)
    if parsed is not None:
        return parsed[1]
    # Permanent compatibility with the malformed early-v2 `span:<span>` form.
    return locator[len("span:"):] if locator.startswith("span:") else locator


def build_cross_source_spans(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    max_spans_per_item: int = 4,
) -> list[CrossSourceSpan]:
    """Bounded multi-source grounding spans for one learning object (§8.5).

    Draws semantic-authority ``entity_source_links`` spans (primary first, then
    support, then alternate for variety) across the LO's facets and the LO entity
    itself. Assessment/exercise (held-out-adjacent) relations are excluded — this
    is a TEACHING context. Capped at ``max_spans_per_item`` so the per-item
    context does not grow with source count (KM §12.9)."""

    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        return []

    candidates: list[tuple[int, str, dict[str, Any]]] = []
    seen: set[tuple[str, str]] = set()

    def _consider(links: list[dict[str, Any]]) -> None:
        for link in links:
            relation = link.get("relation")
            if relation not in _SEMANTIC_RELATION_PRIORITY:
                continue
            if link.get("status") not in (None, "current"):
                continue
            extraction_id = link.get("extraction_id")
            span_id = _span_id_from_locator(link.get("locator"))
            if not extraction_id or not span_id:
                continue
            key = (str(extraction_id), str(span_id))
            if key in seen:
                continue
            seen.add(key)
            candidates.append((_SEMANTIC_RELATION_PRIORITY[relation], relation, link))

    for facet_id in _lo_facet_ids(vault, learning_object):
        _consider(repository.entity_source_links("facet", facet_id))
    _consider(repository.entity_source_links("learning_object", learning_object_id))

    candidates.sort(key=lambda entry: (entry[0], str(entry[2].get("source_id") or ""), entry[2].get("id") or ""))

    spans: list[CrossSourceSpan] = []
    for _priority, relation, link in candidates:
        if len(spans) >= max_spans_per_item:
            break
        extraction_id = str(link["extraction_id"])
        span_id = str(_span_id_from_locator(link.get("locator")))
        text = _span_text(repository, extraction_id, span_id)
        if text is None:
            continue
        source_id = link.get("source_id")
        spans.append(
            CrossSourceSpan(
                extraction_id=extraction_id,
                span_id=span_id,
                relation=relation,
                semantic_authority=(relation == "primary"),
                source_id=source_id,
                label=f"{relation}:{source_id}" if source_id else relation,
                text=text,
            )
        )
    return spans
