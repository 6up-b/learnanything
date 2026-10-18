"""Adaptive hints H1: what an approach map is built from (spec §4.3 items 1-3).

1. **The item:** its reference solution (``expected_answer``), rubric, authored
   hints, the trace contract's checkpoint recipes (alternative recipes are
   alternative routes) and PF's solution skeletons (``item_skeletons``, keyed
   by the item text's ``skeleton_content_hash``).
2. **The learner's own textbook's worked examples** for the item's LO, through
   T6's ``find_sources_for_caller`` under the item-bound practice caller (so
   the derived policy is ``assisted_practice``: T6's item-bound exclusions of
   exercise and solution roles and of the item's own source, exam
   withholding, and the answer-overlap filter), ``roles=("worked_example",)``
   from ingest's block roles, ranked only (no verification call) and with no
   query rewrite: retrieval is consumed as it is, never re-implemented.
3. **The learner's own successful solutions** to the item and its family
   siblings: graded fully correct, or a PF-c valid alternative (placement's
   ``pfc_unverified_attempt_ids``: the final answer verified on a route the
   grader could not), never a grade held for review.

A seed an item does not have is simply absent. Two revision keys
(:mod:`learnloop.hints.map_builder`): ``structure_hash`` covers the item-side
seeds ``practice_item_hash`` does not (trace contract, skeletons, authored
hints) and is cheap enough for a serve to check; ``seeds_hash`` covers every
seed. Reads only.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
import hashlib
import json
from typing import Any

from learnloop.ai.execution import content_key
from learnloop.db.connection import connect
from learnloop.db.stores import approach_maps as map_store
from learnloop.db.stores.pf import skeletons_for_hashes
from learnloop.held_grades import held_for_review_attempts
from learnloop.placement.state import pfc_unverified_attempt_ids
from learnloop.vault.hashes import practice_item_hash, skeleton_content_hash
from learnloop.vault.models import LoadedVault, PracticeItem

#: Prompt size caps (money and context, not judgments): how many worked
#: examples and own solutions a build reads, and how much of each.
MAX_SPANS = 4
SPAN_CHARS = 1500
MAX_ATTEMPTS = 6
ATTEMPT_CHARS = 2000
#: Attempt types whose answer is not the learner's own route.
_NOT_OWN_ROUTE = frozenset({"dont_know", "skip", "self_report", "guided_walkthrough", "teach_back",
                            "exam_evidence"})


@dataclass(frozen=True)
class SeedSpan:
    ref: str
    extraction_id: str
    span_id: str
    role: str | None
    source_title: str | None
    text: str

    @property
    def key(self) -> str:
        return f"{self.extraction_id}:{self.span_id}"


@dataclass(frozen=True)
class SeedAttempt:
    ref: str
    attempt_id: str
    practice_item_id: str
    basis: str  # "correct" | "pfc_valid"
    answer_md: str
    created_at: str


@dataclass
class MapSeeds:
    item: PracticeItem
    item_hash: str
    rubric: list[dict[str, Any]]
    authored_hints: list[str]
    trace_contract: dict[str, Any] | None
    skeletons: list[dict[str, Any]]
    spans: list[SeedSpan] = field(default_factory=list)
    attempts: list[SeedAttempt] = field(default_factory=list)
    retrieval: dict[str, Any] = field(default_factory=dict)
    template: dict[str, Any] | None = None
    facet_ids: list[str] = field(default_factory=list)
    learning_object_title: str | None = None

    @property
    def structure_hash(self) -> str:
        return structure_hash(self.item, self.skeletons)

    @property
    def checkpoint_ids(self) -> frozenset[str]:
        found: set[str] = set()
        for recipe in (self.trace_contract or {}).get("recipes") or ():
            found.update(str(value) for value in recipe.get("checkpoints") or ())
        for skeleton in self.skeletons:
            for checkpoint in skeleton.get("checkpoints") or ():
                found.add(_checkpoint_id(checkpoint))
        return frozenset(value for value in found if value)

    @property
    def recipe_ids(self) -> frozenset[str]:
        return frozenset(str(recipe.get("id")) for recipe in (self.trace_contract or {}).get("recipes") or ())

    def span_refs(self) -> dict[str, str]:
        return {span.ref: span.key for span in self.spans}

    def attempt_refs(self) -> dict[str, str]:
        return {attempt.ref: attempt.attempt_id for attempt in self.attempts}

    @property
    def seeds_hash(self) -> str:
        return content_key({
            "item_hash": self.item_hash, "structure_hash": self.structure_hash,
            "spans": [[span.key, _sha(span.text)] for span in self.spans],
            "attempts": [[attempt.attempt_id, _sha(attempt.answer_md)] for attempt in self.attempts],
            "template": (self.template or {}).get("id"),
        })

    def record(self) -> dict[str, Any]:
        """``seeds_json``: which seeds the map was built from (ids, never texts)."""

        return {
            "practice_item_id": self.item.id,
            "practice_item_hash": self.item_hash,
            "trace_contract": None if self.trace_contract is None else {
                "status": self.trace_contract.get("status"),
                "recipes": [str(recipe.get("id")) for recipe in self.trace_contract.get("recipes") or ()],
            },
            "skeletons": [{"id": skeleton.get("id"), "model_id": skeleton.get("model_id"),
                           "prompt_version": skeleton.get("prompt_version")} for skeleton in self.skeletons],
            "authored_hints": len(self.authored_hints),
            "spans": [{"extraction_id": span.extraction_id, "span_id": span.span_id, "role": span.role}
                      for span in self.spans],
            "attempts": [{"id": attempt.attempt_id, "practice_item_id": attempt.practice_item_id,
                          "basis": attempt.basis} for attempt in self.attempts],
            "retrieval": dict(self.retrieval),
            "family_template": None if self.template is None else {
                "map_id": self.template.get("id"), "practice_item_id": self.template.get("practice_item_id")},
        }


def _sha(text: str) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()


def _checkpoint_id(checkpoint: Any) -> str:
    if isinstance(checkpoint, Mapping):
        return str(checkpoint.get("id") or checkpoint.get("checkpoint_id") or "")
    return str(checkpoint or "")


def item_skeletons(connection: Any, item: PracticeItem) -> list[dict[str, Any]]:
    """PF's persisted solution skeletons of the item's current text (paid output, read only)."""

    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'item_skeletons'").fetchone()
    if exists is None:
        return []
    found = skeletons_for_hashes(connection, [skeleton_content_hash(item.prompt, item.expected_answer)])
    return [{key: record.get(key) for key in ("id", "model_id", "prompt_version", "techniques", "operations",
                                              "checkpoints", "skeleton_text")}
            for records in found.values() for record in records]


def structure_hash(item: PracticeItem, skeletons: Sequence[Mapping[str, Any]]) -> str:
    """The item-side seeds ``practice_item_hash`` does not cover: the trace
    contract and the PF skeletons (and the authored hints, which it does)."""

    return content_key({
        "trace_contract": item.trace_contract.model_dump(mode="json") if item.trace_contract is not None else None,
        "skeletons": [[skeleton.get("id"), _sha(json.dumps(skeleton, sort_keys=True, default=str))]
                      for skeleton in skeletons],
        "hints": list(item.hints),
    })


def item_revision(vault: LoadedVault, connection: Any, item: PracticeItem) -> tuple[str, str]:
    """``(practice_item_hash, structure_hash)``: the cheap revision key a serve checks."""

    return practice_item_hash(item), structure_hash(item, item_skeletons(connection, item))


def family_items(vault: LoadedVault, item: PracticeItem) -> list[PracticeItem]:
    if item.family_id is None:
        return [item]
    return [other for _, other in sorted(vault.practice_items.items()) if other.family_id == item.family_id]


def qualifying_attempts(vault: LoadedVault, connection: Any, item: PracticeItem, *,
                        limit: int = MAX_ATTEMPTS) -> list[SeedAttempt]:
    """The learner's own correct solutions to the item and its family siblings,
    newest first: graded fully correct, or a PF-c valid alternative; never a
    grade held for review, never a non-answer (G-H9)."""

    item_ids = [other.id for other in family_items(vault, item)]
    rows = connection.execute(
        f"SELECT id, practice_item_id, learner_answer_md, correctness, attempt_type, created_at "
        f"FROM practice_attempts WHERE practice_item_id IN ({', '.join('?' for _ in item_ids)}) "
        "AND learner_answer_md IS NOT NULL AND TRIM(learner_answer_md) != '' ORDER BY created_at DESC, id DESC",
        item_ids,
    ).fetchall()
    rows = [row for row in rows if row[4] not in _NOT_OWN_ROUTE]
    if not rows:
        return []
    ids = [str(row[0]) for row in rows]
    pfc_valid = pfc_unverified_attempt_ids(connection)
    held = held_for_review_attempts(connection, ids)
    found: list[SeedAttempt] = []
    for row in rows:
        attempt_id = str(row[0])
        if attempt_id in held:
            continue
        correct = row[3] is not None and float(row[3]) >= 1.0 - 1e-9
        basis = "correct" if correct else ("pfc_valid" if attempt_id in pfc_valid else None)
        if basis is None:
            continue
        found.append(SeedAttempt(ref=f"a{len(found) + 1}", attempt_id=attempt_id, practice_item_id=str(row[1]),
                                 basis=basis, answer_md=str(row[2])[:ATTEMPT_CHARS], created_at=str(row[5])))
        if len(found) >= limit:
            break
    return found


def source_worked_examples(vault: LoadedVault, repository: Any, item: PracticeItem, *,
                           find: Callable[..., Any] | None = None) -> tuple[list[SeedSpan], dict[str, Any]]:
    """The learner's own books' worked examples for the item's LO (T6, consumed)."""

    from learnloop.source_retrieval.find_sources import find_sources_for_caller
    from learnloop.source_retrieval.policy import CallerContext

    lo = vault.learning_objects.get(item.learning_object_id)
    query = " ".join(part for part in ((lo.title if lo is not None else ""), item.prompt) if part)[:1000]
    caller = CallerContext(kind="code", context="practice", item_id=item.id,
                           learning_object_ids=(item.learning_object_id,))
    try:
        hits = (find or find_sources_for_caller)(
            vault, repository, query, caller=caller, intent="explain", roles=("worked_example",),
            verify=False, rewrite=False, limit=MAX_SPANS, owner_id=f"approach_map:{item.id}")
    except Exception as exc:  # noqa: BLE001 - a missing seed is absent, never a failed build
        return [], {"status": "failed", "reason": f"{type(exc).__name__}: {exc}"[:300]}
    spans = [SeedSpan(ref=f"s{index}", extraction_id=str(hit["extraction_id"]), span_id=str(hit["span_id"]),
                      role=hit.get("role"), source_title=hit.get("source_title"),
                      text=str(hit.get("text") or "")[:SPAN_CHARS])
             for index, hit in enumerate(hits.hits[:MAX_SPANS], start=1)]
    manifest = hits.manifest or {}
    return spans, {"status": hits.status, "policy": hits.policy, "intent": "explain",
                   "roles": ["worked_example"], "query_hash": manifest.get("query_hash"),
                   "returned": len(spans)}


def item_side(vault: LoadedVault, connection: Any, item: PracticeItem) -> MapSeeds:
    """Seeds from the item alone (no retrieval, no attempts)."""

    rubric = vault.rubric_for_item(item)
    lo = vault.learning_objects.get(item.learning_object_id)
    return MapSeeds(
        item=item, item_hash=practice_item_hash(item),
        rubric=[{"id": criterion.id, "description": criterion.description, "points": criterion.points}
                for criterion in (rubric.criteria if rubric is not None else [])],
        authored_hints=list(item.hints),
        trace_contract=(item.trace_contract.model_dump(mode="json")
                        if item.trace_contract is not None and item.trace_contract.recipes else None),
        skeletons=item_skeletons(connection, item),
        facet_ids=sorted({vault.canonical_facet_id(str(facet)) for facet in item.evidence_facets}),
        learning_object_title=lo.title if lo is not None else None,
    )


def assemble_seeds(vault: LoadedVault, repository: Any, item: PracticeItem, *, retrieve: bool = True,
                   find: Callable[..., Any] | None = None) -> MapSeeds:
    """Every seed of the item. ``retrieve=False`` (a dry run) reads no source:
    its estimate counts the worked examples at their cap."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        seeds = item_side(vault, connection, item)
        seeds.attempts = qualifying_attempts(vault, connection, item)
        if item.family_id is not None:
            template = map_store.family_template(connection, item.family_id, exclude_item_id=item.id)
            if template is not None:
                seeds.template = {"id": template["id"], "practice_item_id": template["practice_item_id"],
                                  "map": template["map"]}
    if retrieve:
        seeds.spans, seeds.retrieval = source_worked_examples(vault, repository, item, find=find)
    else:
        seeds.retrieval = {"status": "not_run", "reason": "dry run: sources counted at their cap"}
    return seeds


__all__ = [
    "ATTEMPT_CHARS",
    "MAX_ATTEMPTS",
    "MAX_SPANS",
    "SPAN_CHARS",
    "MapSeeds",
    "SeedAttempt",
    "SeedSpan",
    "assemble_seeds",
    "family_items",
    "item_revision",
    "item_side",
    "item_skeletons",
    "qualifying_attempts",
    "source_worked_examples",
    "structure_hash",
]
