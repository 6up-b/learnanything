"""E0 retrieval arms R0-R5 (spec §5.4) over the common candidate units.

**Representation screen** (R1-R5): exact search, ordinary cosine on the
L2-normalized scoring copies, the same units, scope and query text for every
arm, no rewrite, ties broken by unit id (stable). Each arm's index holds one
document space only; a query from another encoder is refused
(``adapters.assert_compatible``).

**System arms** (R0, R1_service): the production search on the copy as it
is, with its native scoring, rewrite default, pool and policy. Its block hits
map to the unit holding each block (first occurrence), withheld blocks
dropped and counted; its top 10 is reported apart from the matched-unit
top 10 (spec §4.1: not directly interchangeable).

Recipes (what each arm encodes for a unit):

* ``production_recipe``: "Section: <path>" and the unit's text (recipe v1).
* ``plain``: the unit's text only (hosted arms; context is the model's job).
* ``deterministic_header`` (R2): source alias, section path, the preceding
  numbered environment's label and up to 400 characters of the preceding
  permitted unit of the same section and policy segment.
* ``llm_context`` (R3): a 50-100-token context written once per window from
  permitted text only, never from a benchmark query; generated headers aid
  indexing only, a delivered citation is always the canonical text.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Any

import numpy as np
from pydantic import Field

from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import render_structured_prompt

from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.adapters import (
    Chunk,
    Document,
    SpaceVectors,
    assert_compatible,
)
from learnloop.experiments.contextual_embeddings.corpus import CandidateUnit, CorpusSnapshot, Window, alias

PRECEDING_CHARS = 400
CONTEXT_PROMPT_VERSION = pins.ROLE_PINS["context"].prompt_version
CONTEXT_INSTRUCTIONS = (
    "For each passage, write 50 to 100 words that situate it in the source excerpt shown: what the section "
    "is about, which definition, theorem or example it belongs to, and what it depends on. Use only the "
    "excerpt. Do not answer questions, do not add facts, do not quote solutions. Return one context per ref."
)


def _sha(*parts: Any) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()


# -- recipes --------------------------------------------------------------------------


def preceding_text(snapshot: CorpusSnapshot, unit: CandidateUnit) -> tuple[str | None, str]:
    """The preceding numbered label and up to ``PRECEDING_CHARS`` of the
    preceding unit, within the same extraction, section and policy segment."""

    units = [candidate for candidate in snapshot.units if candidate.extraction_id == unit.extraction_id]
    position = next(index for index, candidate in enumerate(units) if candidate.unit_id == unit.unit_id)
    label = None
    previous_text = ""
    for index in range(position - 1, -1, -1):
        candidate = units[index]
        if candidate.segment != unit.segment or candidate.section != unit.section:
            break
        if not previous_text:
            previous_text = candidate.text[-PRECEDING_CHARS:]
        if candidate.label:
            label = candidate.label
            break
    return label, previous_text


def recipe_text(snapshot: CorpusSnapshot, unit: CandidateUnit, recipe: str,
                headers: Mapping[str, str] | None = None) -> str:
    body = " ".join(unit.text.split())
    path = " > ".join(unit.section)
    if recipe == "plain":
        return unit.text
    if recipe == "production_recipe":
        return f"Section: {path}\n{body}" if path else body
    if recipe == "deterministic_header":
        label, before = preceding_text(snapshot, unit)
        lines = [f"Source: {alias('src', unit.source_id)}"]
        if path:
            lines.append(f"Section: {path}")
        if label:
            lines.append(f"Within: {label}")
        if before:
            lines.append("Preceding: " + " ".join(before.split()))
        return "\n".join(lines + [body])
    if recipe == "llm_context":
        header = (headers or {}).get(unit.unit_id)
        if not header:
            raise KeyError(f"no generated context for {unit.unit_id}")
        return f"{header}\n{body}"
    raise ValueError(f"unknown recipe {recipe!r}")


def document_vector_key(space_id: str, snapshot: CorpusSnapshot, units: Sequence[CandidateUnit],
                        texts: Sequence[str]) -> str:
    """The spec's ``document_vector_key`` (§4.3): the space, the extraction
    revision, every context span and offset, the targets, the policy, and the
    exact texts (which carry any generated-context dependency)."""

    return "dv_" + _sha(space_id, sorted({snapshot.infos[unit.extraction_id].fingerprint for unit in units}),
                        [[(member.span_id, member.start, member.end) for member in unit.members] for unit in units],
                        [unit.unit_id for unit in units], snapshot.policy.fingerprint, list(texts))[:32]


def documents_for(snapshot: CorpusSnapshot, encoding: str, recipe: str, space_id: str,
                  headers: Mapping[str, str] | None = None) -> tuple[list[Document], dict[str, str]]:
    """The documents an arm encodes, and ``{chunk_id: unit_id}``."""

    chunk_unit: dict[str, str] = {}
    documents: list[Document] = []
    if encoding == "grouped":
        for window in snapshot.windows:
            units = [snapshot.unit(unit_id) for unit_id in window.unit_ids]
            texts = [recipe_text(snapshot, unit, recipe, headers) for unit in units]
            chunks = tuple(Chunk(f"{window.window_id}:{unit.unit_id}", text) for unit, text in zip(units, texts,
                                                                                                    strict=True))
            for chunk, unit in zip(chunks, units, strict=True):
                chunk_unit[chunk.chunk_id] = unit.unit_id
            documents.append(Document(window.window_id, chunks, document_vector_key(space_id, snapshot, units, texts)))
        return documents, chunk_unit
    for unit in snapshot.units:
        text = recipe_text(snapshot, unit, recipe, headers)
        chunk = Chunk(unit.unit_id, text)
        chunk_unit[chunk.chunk_id] = unit.unit_id
        documents.append(Document(unit.unit_id, (chunk,), document_vector_key(space_id, snapshot, [unit], [text])))
    return documents, chunk_unit


def query_vector_key(encoder_id: str, query_text: str) -> str:
    """The spec's ``query_vector_key``: the encoder and the complete effective query."""

    return "qv_" + _sha(encoder_id, query_text)[:32]


# -- exact search ---------------------------------------------------------------------


def exact_search(index: SpaceVectors, query: Sequence[float], *, query_encoder: str,
                 top_k: int = pins.POOL_DEPTH, allowed: set[str] | None = None) -> list[tuple[str, float]]:
    """Ordinary cosine over normalized vectors, best first, ties by id."""

    assert_compatible(index, query_encoder)
    vector = np.asarray(query, dtype=np.float32)
    norm = float(np.linalg.norm(vector))
    if not norm or not math.isfinite(norm):
        raise ValueError("query vector has an invalid norm")
    scores = index.matrix @ (vector / norm)
    ranked = sorted(((index.ids[position], round(float(score), 7)) for position, score in enumerate(scores)
                     if allowed is None or index.ids[position] in allowed),
                    key=lambda item: (-item[1], item[0]))
    return ranked[:top_k]


_WORD = re.compile(r"[a-z0-9]+")


def _terms(text: str) -> list[str]:
    return _WORD.findall(text.lower())


@dataclass
class BM25:
    """Okapi BM25 (k1 1.2, b 0.75) over unit texts; ties by id."""

    ids: list[str]
    documents: list[list[str]]
    k1: float = 1.2
    b: float = 0.75

    @classmethod
    def build(cls, texts: Mapping[str, str]) -> BM25:
        ids = sorted(texts)
        return cls(ids, [_terms(texts[key]) for key in ids])

    def search(self, query: str, top_k: int = pins.POOL_DEPTH) -> list[tuple[str, float]]:
        terms = _terms(query)
        if not terms or not self.documents:
            return []
        count = len(self.documents)
        average = sum(len(document) for document in self.documents) / count or 1.0
        frequencies: dict[str, int] = {}
        for document in self.documents:
            for term in set(document):
                frequencies[term] = frequencies.get(term, 0) + 1
        scored: list[tuple[str, float]] = []
        for key, document in zip(self.ids, self.documents, strict=True):
            score = 0.0
            for term in terms:
                tf = document.count(term)
                if not tf:
                    continue
                df = frequencies.get(term, 0)
                idf = math.log(1 + (count - df + 0.5) / (df + 0.5))
                score += idf * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * len(document) / average))
            if score > 0:
                scored.append((key, round(score, 7)))
        scored.sort(key=lambda item: (-item[1], item[0]))
        return scored[:top_k]


# -- R3 context generation (a paid role: implemented, tested with fakes) -------------


class GeneratedContext(WireModel):
    ref: str = Field(min_length=1)
    context: str = Field(min_length=1)


class GeneratedContexts(WireModel):
    contexts: list[GeneratedContext]


def context_prompt(snapshot: CorpusSnapshot, window: Window) -> tuple[str, dict[str, str]]:
    """One prompt per window: its permitted units as the excerpt, one ref per unit."""

    refs = {f"p{index}": unit_id for index, unit_id in enumerate(window.unit_ids, start=1)}
    excerpt = [{"ref": ref, "passage": snapshot.unit(unit_id).text} for ref, unit_id in refs.items()]
    prompt = render_structured_prompt("E0 chunk context", CONTEXT_PROMPT_VERSION,
                                      {"instructions": CONTEXT_INSTRUCTIONS, "context": {"excerpt": excerpt}})
    return prompt, refs


def generate_contexts(snapshot: CorpusSnapshot, caller: Any) -> tuple[dict[str, str], dict[str, int]]:
    """``{unit_id: context}`` for every unit, one call per window; a missing or
    out-of-range context is counted (``stats``) and the unit is reported
    without an R3 vector rather than silently given another recipe."""

    headers: dict[str, str] = {}
    stats = {"windows": 0, "missing": 0, "short": 0, "long": 0}
    for window in snapshot.windows:
        prompt, refs = context_prompt(snapshot, window)
        result = caller.call("context", prompt=prompt, result_model=GeneratedContexts, arm="R3")
        stats["windows"] += 1
        for item in result.contexts:
            unit_id = refs.get(item.ref)
            if unit_id is None or unit_id in headers:
                continue
            words = len(item.context.split())
            if words < 30:
                stats["short"] += 1
            elif words > 160:
                stats["long"] += 1
            headers[unit_id] = " ".join(item.context.split())
        stats["missing"] += sum(1 for unit_id in refs.values() if unit_id not in headers)
    return headers, stats


# -- system arms ----------------------------------------------------------------------


def units_from_blocks(snapshot: CorpusSnapshot, hits: Sequence[tuple[str, str]]) -> tuple[list[str], dict[str, int]]:
    """Production block hits mapped to the units that hold them (first
    occurrence), withheld or unmapped blocks dropped and counted."""

    unit_of: dict[tuple[str, str], str] = {}
    for unit in snapshot.units:
        for key in unit.keys:
            unit_of.setdefault(key, unit.unit_id)
    ranked: list[str] = []
    dropped = {"withheld": 0, "unmapped": 0}
    for key in hits:
        if not snapshot.policy.permitted(*key):
            dropped["withheld"] += 1
            continue
        unit_id = unit_of.get((str(key[0]), str(key[1])))
        if unit_id is None:
            dropped["unmapped"] += 1
            continue
        if unit_id not in ranked:
            ranked.append(unit_id)
    return ranked, dropped
