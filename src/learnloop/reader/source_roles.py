"""Instructional roles as source-object proposals (reader workbench RW4e; spec_reader_workbench_v1 §7.9).

Ingest gives each block one deterministic ``role_hint`` (definition, theorem,
worked example, exercise, solution, ...), and that hint stays the authority
for **exclusion** (§7.1, G44): T6's item-bound scopes keep exercise and
solution blocks out of practice and feedback contexts, and nothing here
changes that. Finer roles (counterexample, contrast, intuition, prerequisite,
alternative treatment, application, ...) need judgment, so they accumulate
from judgments the Reader already makes: the library organizer (RW4a) and the
cue judge (RW3b) each propose a passage's roles at no extra call, and the
owner-run batch labeller (``learnloop reader label-roles``) labels a whole
source when the index is wanted now.

Each role on each passage is one ``source_objects`` proposal (P3 §7), written
through :mod:`learnloop.reader.source_objects`'s proposal path:

* ``object_type`` mapped by §3.4 item 14 (:func:`object_type_for`),
  ``authorial_role`` the role, ``authorship = 'ai'``, ``status = 'proposed'``,
  the reading's ``revision_id``;
* ``content_json``: the confidence, the judge, its ledger id, the prompt
  version and the model (``kind = "instructional_role"``);
* one citation: the span, its block's content hash and the revision; the
  passage's text is not copied (``exact_text`` is empty);
* a **second judge** proposing the same role on the same passage (same
  revision, span and block hash) appends a version with its own confidence,
  judge and ledger id, so agreement between judges is visible; the same
  judge again writes nothing.

Exam protection: before anything is written, the one exam predicate
(``exam_material(...).withheld``) is asked about every passage; exam and
held-out passages are never proposed (an unreadable predicate proposes
nothing). Every reader here leaves out the objects RW4d's
``hidden_source_objects`` hides (exam or held out **now**, fail closed), so a
proposal on a withheld passage is never returned by any filter or grouping.

Used positively only, and only while ``roles.positive_filter_enabled`` is on
(:func:`role_proposals`, :func:`role_keys`, :func:`best_roles`): the sources
service's ``roles`` filter and intent lists, RW3b's contrast list and the
library answer's grouping. A proposal never admits a block into an item-bound
scope and never removes one from an exclusion. Proposals are labels on
sources: never a concept edge, a learning-object change, evidence or mastery.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
import json
from typing import Any, Literal

from pydantic import model_validator

from learnloop.ai.schemas import WireModel
from learnloop.clock import Clock
from learnloop.content.sources import exam_material as EM
from learnloop.content.sources.span_aliases import CITATION_MADE_AT_SQL, CitationResolver
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_block_fts import block_content_hashes, existing_spans, extraction_source_ids
from learnloop.reader import source_objects as SO

#: The instructional roles a judge may propose (§7.9), one vocabulary for
#: every judge.
ROLES: tuple[str, ...] = (
    "definition", "theorem", "explanation", "intuition", "worked_example", "exercise", "figure",
    "counterexample", "contrast", "prerequisite", "alternative_treatment", "application",
)
CONFIDENCES: tuple[str, ...] = ("high", "medium", "low")
#: The judges whose roles become proposals.
JUDGE_ORGANIZER = "library_organizer"
JUDGE_CUE = "passage_cue_judge"
JUDGE_LABELLER = "role_labeller"
JUDGES: tuple[str, ...] = (JUDGE_ORGANIZER, JUDGE_CUE, JUDGE_LABELLER)
#: ``content_json.kind`` of an RW4e proposal.
PROPOSAL_KIND = "instructional_role"
#: The ids of RW4e's proposal objects (any version marked ``kind``), for SQL.
PROPOSAL_KIND_SQL = ("SELECT source_object_id FROM source_object_versions "
                     "WHERE json_extract(content_json, '$.kind') = 'instructional_role'")
#: §3.4 item 14: the finer role lives in ``authorial_role``; the type is mapped.
OBJECT_TYPE_FOR_ROLE: dict[str, str] = {
    "worked_example": "worked_example", "exercise": "problem", "definition": "definition", "theorem": "claim",
}
#: What the Reader calls a passage with a proposed role (UX §4.5).
MODEL_LABEL = "model's label"
#: Library answer groups for a proposed role (§7.3; the dialogue's Foundation,
#: Explanation and finer views, Prerequisite, Application).
ROLE_GROUPS: dict[str, str] = {
    "definition": "Foundation", "theorem": "Foundation",
    "explanation": "Explanation", "intuition": "Explanation", "figure": "Explanation",
    "alternative_treatment": "Explanation",
    "counterexample": "Contrast", "contrast": "Contrast",
    "worked_example": "Worked example", "exercise": "Exercise",
    "prerequisite": "Prerequisite", "application": "Application",
}
#: Best first; an unstated confidence ranks below medium and above low.
_CONFIDENCE_RANK = {"high": 0, "medium": 1, None: 2, "low": 3}

Key = tuple[str, str]


class RoleProposal(WireModel):
    role: Literal["definition", "theorem", "explanation", "intuition", "worked_example", "exercise", "figure",
                  "counterexample", "contrast", "prerequisite", "alternative_treatment", "application"]
    confidence: Literal["high", "medium", "low"]


assert set(RoleProposal.model_fields["role"].annotation.__args__) == set(ROLES)  # one vocabulary


def clean_roles(value: Any) -> list[dict[str, str]]:
    """A judge's ``roles`` read tolerantly: each well-formed ``{role,
    confidence}`` from the vocabulary, once, in order; anything else (a
    missing field, a string, an unknown role or confidence) is dropped, so a
    malformed roles field never fails the judge's main output."""

    if not isinstance(value, (list, tuple)):
        return []
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for entry in value:
        if isinstance(entry, Mapping):
            role, confidence = entry.get("role"), entry.get("confidence")
        else:
            role, confidence = getattr(entry, "role", None), getattr(entry, "confidence", None)
        if role in ROLES and confidence in CONFIDENCES and role not in seen:
            seen.add(str(role))
            out.append({"role": str(role), "confidence": str(confidence)})
    return out


def tolerate_roles(data: Any) -> Any:
    """A ``mode="before"`` model validator's body: the judgment's ``roles``
    replaced by :func:`clean_roles` of it (``[]`` when missing). It changes no
    JSON schema, so a judge's request identity stays what it was."""

    if isinstance(data, Mapping):
        data = dict(data)
        data["roles"] = clean_roles(data.get("roles"))
    return data


class TolerantRoles(WireModel):
    """A judgment whose ``roles`` field is read with :func:`tolerate_roles`."""

    @model_validator(mode="before")
    @classmethod
    def _tolerate_roles(cls, data: Any) -> Any:
        return tolerate_roles(data)


# ---------------------------------------------------------------------------
# Switches
# ---------------------------------------------------------------------------

def _settings(vault: Any) -> Any:
    return getattr(getattr(vault, "config", None), "roles", None)


def on_demand_enabled(vault: Any) -> bool:
    """The judges' role proposals are written (``roles.on_demand_enabled``)."""

    return bool(getattr(_settings(vault), "on_demand_enabled", False))


def positive_filter_enabled(vault: Any) -> bool:
    """Proposals are read by filters and groupings (``roles.positive_filter_enabled``)."""

    return bool(getattr(_settings(vault), "positive_filter_enabled", False))


def batch_max_cost_usd(vault: Any) -> float:
    return float(getattr(_settings(vault), "batch_max_cost_usd", 5.0) or 0.0)


def object_type_for(role: str) -> str:
    return OBJECT_TYPE_FOR_ROLE.get(role, "motif_or_passage")


# ---------------------------------------------------------------------------
# Writing proposals
# ---------------------------------------------------------------------------

def _existing(repository: Repository, revision_ids: Iterable[str]) -> dict[tuple[Any, ...], dict[str, Any]]:
    """Role proposals already on these revisions, keyed ``(revision, span,
    block hash, role)``: each head's object id, status and judges."""

    revisions = sorted({str(value) for value in revision_ids if value})
    found: dict[tuple[Any, ...], dict[str, Any]] = {}
    if not revisions:
        return found
    marks = ",".join("?" for _ in revisions)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = connection.execute(
            "SELECT v.source_object_id, v.version_ordinal, v.authorial_role, v.content_json, v.status, "
            "c.revision_id, c.span_id, c.block_content_hash "
            "FROM source_object_versions v JOIN source_object_citations c ON c.source_object_version_id = v.id "
            f"WHERE v.source_object_id IN ({PROPOSAL_KIND_SQL}) AND c.citation_ordinal = 1 "
            f"AND c.revision_id IN ({marks}) "
            "ORDER BY v.source_object_id, v.version_ordinal", tuple(revisions)).fetchall()
    by_object: dict[str, dict[str, Any]] = {}
    for object_id, ordinal, role, content_json, status, revision_id, span_id, block_hash in rows:
        entry = by_object.setdefault(str(object_id), {"object_id": str(object_id), "judges": set(), "ordinal": 0})
        try:
            content = json.loads(content_json or "{}")
        except (TypeError, ValueError):
            content = {}
        if isinstance(content, Mapping) and content.get("judge"):
            entry["judges"].add(str(content["judge"]))
        if int(ordinal) >= entry["ordinal"]:
            entry.update(ordinal=int(ordinal), status=str(status), ident=(
                str(revision_id), str(span_id), block_hash, str(role)))
    for entry in by_object.values():
        found.setdefault(entry["ident"], entry)
    return found


def propose_roles(vault: Any, repository: Repository, claims: Sequence[Mapping[str, Any]], *, judge: str,
                  prompt_version: str, model: str | None = None, clock: Clock | None = None) -> dict[str, Any]:
    """Write each ``{extraction_id, span_id, role, confidence, ledger_id}`` as
    a proposal (one object per passage and role; a second judge's agreement a
    version). Returns the object ids written, the versions appended and what
    was skipped, with why. Never raises for a passage it cannot propose."""

    if judge not in JUDGES:
        raise ValueError(f"unknown role judge {judge!r}")
    wanted: dict[tuple[Key, str], tuple[str, str]] = {}
    skipped: list[dict[str, Any]] = []
    for claim in claims:
        key = (str(claim.get("extraction_id") or ""), str(claim.get("span_id") or ""))
        role, confidence = claim.get("role"), claim.get("confidence")
        if not key[0] or not key[1] or role not in ROLES or confidence not in CONFIDENCES:
            skipped.append({"key": list(key), "role": role, "reason": "malformed"})
            continue
        wanted.setdefault((key, str(role)), (str(confidence), str(claim.get("ledger_id") or "")))
    out: dict[str, Any] = {"written": [], "versions": [], "skipped": skipped}
    if not wanted:
        return out
    keys = sorted({key for key, _role in wanted})
    try:
        withheld = set(EM.exam_material(vault, repository).withheld(keys))
    except Exception:  # noqa: BLE001 - an unreadable predicate proposes nothing (fail closed)
        withheld = set(keys)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        # Which passages exist (no text is read: a proposal copies none).
        present = existing_spans(connection, keys)
        hashes = {key: (block_content_hashes(connection, key[0], [key[1]]) or [None])[0] for key in keys}
        sources = extraction_source_ids(connection, sorted({key[0] for key in keys}))
    runs = {extraction_id: repository.get_extraction_run(extraction_id) for extraction_id in {k[0] for k in keys}}
    revisions = {extraction_id: str((run or {}).get("revision_id") or "") for extraction_id, run in runs.items()}
    existing = _existing(repository, revisions.values())
    for (key, role), (confidence, ledger_id) in wanted.items():
        revision_id, source_id = revisions.get(key[0]) or "", sources.get(key[0])
        if key in withheld:
            out["skipped"].append({"key": list(key), "role": role, "reason": "exam_material"})
            continue
        if key not in present or not revision_id or not source_id:
            out["skipped"].append({"key": list(key), "role": role, "reason": "no such passage"})
            continue
        content = {"kind": PROPOSAL_KIND, "role": role, "confidence": confidence, "judge": judge,
                   "ledger_id": ledger_id or None, "prompt_version": prompt_version, "model": model,
                   "extraction_id": key[0]}
        provenance = {"judge": judge, "ledger_id": ledger_id or None, "prompt_version": prompt_version,
                      "model": model}
        citation = {"revision_id": revision_id, "span_id": key[1], "block_content_hash": hashes.get(key)}
        ident = (revision_id, key[1], hashes.get(key), role)
        found = existing.get(ident)
        if found is not None:
            if judge in found["judges"]:
                out["skipped"].append({"key": list(key), "role": role, "reason": "already proposed by this judge"})
                continue
            if found.get("status") != "proposed":
                out["skipped"].append({"key": list(key), "role": role,
                                       "reason": f"reviewed as {found.get('status')}"})
                continue
            written = SO.append_proposal_version(
                repository, source_object_id=found["object_id"], revision_id=revision_id,
                object_type=object_type_for(role), authorial_role=role, content=content, citations=[citation],
                model_provenance=provenance, clock=clock)
            found["judges"].add(judge)
            out["versions"].append({"source_object_id": found["object_id"], **written})
            continue
        authored = SO.author_source_object(
            repository, source_id=str(source_id), revision_id=revision_id, object_type=object_type_for(role),
            authorial_role=role, content=content, citations=[citation], authorship="ai", status="proposed",
            model_provenance=provenance, clock=clock)
        existing[ident] = {"object_id": authored["source_object_id"], "judges": {judge}, "status": "proposed"}
        out["written"].append(authored["source_object_id"])
    return out


def claims_from_judgments(refs: Mapping[str, Key], judgments: Mapping[str, Any],
                          ledger_ids: Mapping[Key, str]) -> list[dict[str, Any]]:
    """The role claims of a listwise judge's judgments (``ref -> judgment``,
    each with a ``roles`` field), in the pool's order."""

    claims: list[dict[str, Any]] = []
    for ref, key in refs.items():
        judgment = judgments.get(ref)
        if judgment is None:
            continue
        for entry in clean_roles(getattr(judgment, "roles", None)):
            claims.append({"extraction_id": key[0], "span_id": key[1], **entry,
                           "ledger_id": ledger_ids.get(key) or ""})
    return claims


# ---------------------------------------------------------------------------
# Reading proposals (positive use only)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RoleLabel:
    """One visible role proposal on one passage of a current reading."""

    object_id: str
    key: Key
    role: str
    object_type: str
    #: The best confidence any judge gave (None: unstated).
    confidence: str | None
    judges: tuple[str, ...]
    versions: int
    status: str

    @property
    def low(self) -> bool:
        return self.confidence == "low"

    def as_dict(self) -> dict[str, Any]:
        return {"role": self.role, "confidence": self.confidence, "judges": list(self.judges),
                "label": MODEL_LABEL}


def _content(text: Any) -> Mapping[str, Any]:
    try:
        value = json.loads(text or "{}")
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, Mapping) else {}


def role_proposals(vault: Any, repository: Repository, *, extraction_ids: Iterable[str] | None = None,
                   roles: Iterable[str] | None = None) -> list[RoleLabel]:
    """The visible RW4e role proposals (one per object and citation), oldest
    first: head versions ``proposed`` or ``reviewed`` with an ``authorial_role``, on
    the reading each citation resolves to now (the one alias authority),
    without any object ``hidden_source_objects`` hides. Empty while
    ``roles.positive_filter_enabled`` is off."""

    if not positive_filter_enabled(vault):
        return []
    extractions = None if extraction_ids is None else {str(value) for value in extraction_ids if value}
    wanted_roles = None if roles is None else {str(value) for value in roles if value}
    if extractions is not None and not extractions or wanted_roles is not None and not wanted_roles:
        return []
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='source_object_versions'").fetchone() is None:
            return []
        rows = connection.execute(
            "SELECT v.source_object_id, o.source_id, v.version_ordinal, v.revision_id, v.authorial_role, "
            "v.object_type, v.content_json, v.status, c.revision_id, c.span_id, c.block_content_hash, "
            f"{CITATION_MADE_AT_SQL} "
            "FROM source_object_versions v "
            "JOIN source_objects o ON o.id = v.source_object_id "
            "LEFT JOIN source_object_citations c ON c.source_object_version_id = v.id "
            f"WHERE v.source_object_id IN ({PROPOSAL_KIND_SQL}) "
            "ORDER BY o.created_at, o.id, v.version_ordinal, c.citation_ordinal").fetchall()
    objects: dict[str, dict[str, Any]] = {}
    for (object_id, source_id, ordinal, version_revision, role, object_type, content_json, status, revision_id,
         span_id, block_hash, made_at) in rows:
        entry = objects.setdefault(str(object_id), {"source_id": source_id, "versions": {}})
        version = entry["versions"].setdefault(int(ordinal), {
            "role": role, "object_type": object_type, "content_json": content_json,
            "content": _content(content_json), "status": status, "revision_id": version_revision,
            "citations": []})
        if span_id is not None:
            version["citations"].append({"revision_id": revision_id, "span_id": span_id,
                                         "block_content_hash": block_hash, "created_at": made_at})
    resolver = CitationResolver(repository)
    found: list[RoleLabel] = []
    heads: dict[str, dict[str, Any]] = {}
    for object_id, entry in objects.items():
        versions = entry["versions"]
        head = versions[max(versions)]
        role = str(head["role"] or "")
        if not role or head["status"] not in ("proposed", "reviewed"):
            continue
        if wanted_roles is not None and role not in wanted_roles:
            continue
        same = [version for version in versions.values() if version["role"] == role]
        confidences = [version["content"].get("confidence") for version in same]
        confidence = min(confidences, key=lambda value: _CONFIDENCE_RANK.get(value, 2)) if confidences else None
        if confidence not in CONFIDENCES:
            confidence = None
        judges = tuple(dict.fromkeys(str(version["content"]["judge"]) for version in same
                                     if version["content"].get("judge")))
        for citation in head["citations"]:
            key = resolver.current_key(citation)
            if key is None or extractions is not None and key[0] not in extractions:
                continue
            found.append(RoleLabel(object_id=object_id, key=(str(key[0]), str(key[1])), role=role,
                                   object_type=str(head["object_type"]), confidence=confidence, judges=judges,
                                   versions=len(versions), status=str(head["status"])))
            # The head as ``hidden_source_objects`` reads one (object, version, citations).
            heads[object_id] = {"object": {"id": object_id, "source_id": entry["source_id"]},
                                "version": {"revision_id": head["revision_id"], "content_json": head["content_json"]},
                                "citations": head["citations"]}
    if not found:
        return []
    hidden = SO.hidden_source_objects(vault, repository, list(heads.values()))
    return [label for label in found if label.object_id not in hidden]


def role_keys(vault: Any, repository: Repository, extraction_ids: Iterable[str],
              roles: Iterable[str]) -> tuple[set[Key], set[Key]]:
    """Passages a visible proposal gives one of ``roles``: ``(confident,
    low)``, a passage with any confident proposal never in ``low``."""

    strong: set[Key] = set()
    weak: set[Key] = set()
    for label in role_proposals(vault, repository, extraction_ids=extraction_ids, roles=roles):
        (weak if label.low else strong).add(label.key)
    return strong, weak - strong


def best_roles(vault: Any, repository: Repository, keys: Iterable[Key]) -> dict[Key, RoleLabel]:
    """Each passage's best visible proposal: the best confidence (``low`` only
    when nothing better exists), then the most judges, then the vocabulary's
    order."""

    wanted = {(str(key[0]), str(key[1])) for key in keys}
    if not wanted:
        return {}
    best: dict[Key, RoleLabel] = {}
    for label in role_proposals(vault, repository, extraction_ids={key[0] for key in wanted}):
        if label.key not in wanted:
            continue
        rank = (_CONFIDENCE_RANK.get(label.confidence, 2), -len(label.judges), ROLES.index(label.role)
                if label.role in ROLES else len(ROLES))
        current = best.get(label.key)
        if current is None or rank < (_CONFIDENCE_RANK.get(current.confidence, 2), -len(current.judges),
                                      ROLES.index(current.role) if current.role in ROLES else len(ROLES)):
            best[label.key] = label
    return best


__all__ = [
    "CONFIDENCES",
    "JUDGES",
    "JUDGE_CUE",
    "JUDGE_LABELLER",
    "JUDGE_ORGANIZER",
    "MODEL_LABEL",
    "OBJECT_TYPE_FOR_ROLE",
    "PROPOSAL_KIND",
    "PROPOSAL_KIND_SQL",
    "ROLES",
    "ROLE_GROUPS",
    "RoleLabel",
    "RoleProposal",
    "TolerantRoles",
    "batch_max_cost_usd",
    "best_roles",
    "claims_from_judgments",
    "clean_roles",
    "object_type_for",
    "on_demand_enabled",
    "positive_filter_enabled",
    "propose_roles",
    "role_keys",
    "role_proposals",
    "tolerate_roles",
]
