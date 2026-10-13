"""Facet meaning authority: the one chokepoint (Codex verification of F6 and its re-review, 2026-10-13).

Facet identity locks were removed (owner, 2026-10-12), so nothing about a
facet's history stops its meaning from changing. What must still hold is the
§4.2 authority matrix: exam material never establishes or changes a canonical
claim on its own; it only ever aligns assessment. This module is the one place
that rule is enforced for a facet, whichever path writes it.

* :data:`AUTHORITY_FIELDS` are a facet's meaning: kind, title, claim,
  description, conditions, applicability, non-goals and worked examples. A
  write that changes none of them (aliases, error signatures, repairs,
  provenance, status, version) is not judged here.
* :class:`CitationResolver` resolves a citation from its ids, never from what
  its producer says about it. The extraction must belong to a source-set
  member (as the member revision's latest extraction or, after a
  re-extraction, an earlier one of the same pinned revision); the span must
  resolve in that extraction; a cited unit must hold the span (a split child
  holds only the blocks under its own heading); the span must be held by a
  unit selected in the member's scope; its role is that scope entry's
  ``role_override`` when there is one, else the member's ``default_role`` (the
  least authoritative one when several entries or members select it, in any
  order); an exam citation's relation is ``assessment_alignment``; and its
  locator is derived from the ids.
* :func:`check_meaning_write` judges one facet's change from the resolved
  citations of each contribution to it, with ``role_authority.support_verdict``:

  - a registered facet's meaning changes only when every contribution has an
    explanatory citation (an uncited or exam-only change is refused);
  - a new facet may not carry a contribution only exam material supports (a
    notes or problem-set citation never corroborates one). An uncited new
    facet stays what it was: a proposal the ``adequate_provenance`` gate sends
    to review;
  - a proposal's contributions are its ``meaning_support`` reconciled with the
    refs it records (:func:`write_contributions`): a recorded span no declared
    contribution cites is one more contribution, and malformed bookkeeping is
    refused; recorded citations an undo restores must still resolve.

  A citation that does not resolve supports nothing: it is recorded as
  ``unresolved`` and never becomes a source link (:func:`added_provenance`).
* :func:`join_candidate` is how a merge or absorb of a candidate (in-run
  consolidation, attach) changes its survivor: the candidate's meaning joins
  only when :func:`check_meaning_write` allows it, otherwise it joins as an
  alias. :func:`merged_survivor` is a vault merge's union of registered facets.
* :func:`write_registry_text` is the one writer of ``facets.yaml`` outside the
  proposal compiler (vault merges, undo, recovery, the Library). It compares the
  new text with the file, and each facet whose meaning changes must be covered
  by a basis it verifies itself: :class:`Cited` (judged as above),
  :class:`RegisteredMerge` (the union of registered facets, recomputed here),
  :class:`Restore` (an entry an action recorded) or :class:`OwnerEdit` (the
  owner's own Library save, the explicit manual authority, which must name
  the owner's ``granted`` verdict recorded for it). :func:`check_registry_text`
  decides without writing, so a caller that records an intent first (undo)
  never records one the chokepoint would refuse.
* The proposal compiler (``patches._compile_facet``) calls
  :func:`check_meaning_write` for each facet item through a
  :class:`ProposalAuthority`, and the apply refuses a staged ``facets.yaml``
  whose meaning changes no checked item wrote (:func:`verify_registry_transition`).

Producers (bootstrap and append normalization, consolidation, the reword lane)
call the same functions to drop or flag what would be refused, so a paid run is
not lost at accept; the guarantee does not depend on them.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnloop.content.facet_identity.views import union_payload
from learnloop.content.sources.role_authority import (
    ASSESSMENT_ONLY_ROLES,
    CITATION_RELATIONS,
    EXAM_UNCORROBORATED,
    EXPLANATORY,
    can_authorize_semantic,
    is_semantic_support,
    support_verdict,
)
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.content.synthesis.source_unit_selection import effective_unit_spans
from learnloop.content.synthesis.synthesis_gates import ProvenanceRef
from learnloop.ingest.locators import BLOCK_SPAN_V1, format_block_span, parse_block_span
from learnloop.vault.models import EvidenceFacet
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, yaml_from_string

#: A facet's meaning, for the authority rule. ``MEANING_FIELDS`` (what a
#: version records) is a subset; worked examples and a legacy facet's title
#: are meaning too, though growing them is not a new version.
AUTHORITY_FIELDS = (
    "kind", "title", "claim", "description", "preconditions", "postconditions", "applicability",
    "non_goals", "positive_examples", "negative_examples",
)
#: Proposal bookkeeping a facet payload may carry; never written to facets.yaml.
PROPOSAL_ONLY_KEYS = frozenset({"expected_target_hash", "meaning_support"})
#: The role a citation that does not resolve is given: it supports nothing.
UNRESOLVED_ROLE = "unresolved"

ALLOWED_CODES = frozenset({"unchanged", "explanatory", "new_unsupported", "owner", "registered", "restore"})


class FacetAuthorityError(ValueError):
    """A facet meaning write the chokepoint refused (nothing was written)."""

    def __init__(self, code: str, message: str, *, facet_id: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.facet_id = facet_id


# --- a facet's meaning ----------------------------------------------------------------------


def overlay(before: Mapping[str, Any] | None, values: Mapping[str, Any]) -> dict[str, Any]:
    """The entry a write leaves: ``values`` over ``before`` (what ``upsert_facet`` writes)."""

    merged = {**dict(before or {}), **{key: value for key, value in values.items() if key not in PROPOSAL_ONLY_KEYS}}
    return EvidenceFacet.model_validate(merged).model_dump(mode="json", exclude_none=False)


def authority_meaning(entry: Mapping[str, Any] | None) -> dict[str, Any]:
    """The :data:`AUTHORITY_FIELDS` of an entry, normalized (an absent entry has none)."""

    data = {key: value for key, value in dict(entry or {}).items() if key not in PROPOSAL_ONLY_KEYS}
    data.setdefault("id", "_")
    dumped = EvidenceFacet.model_validate(data).model_dump(mode="json", exclude_none=False)
    return {name: dumped.get(name) for name in AUTHORITY_FIELDS}


def authority_changes(before: Mapping[str, Any] | None, after: Mapping[str, Any] | None) -> list[str]:
    """The :data:`AUTHORITY_FIELDS` that differ (for a new facet: every one it states)."""

    old, new = authority_meaning(before), authority_meaning(after)
    return [name for name in AUTHORITY_FIELDS if old[name] != new[name]]


# --- citations ------------------------------------------------------------------------------


@dataclass(frozen=True)
class ResolvedCitation:
    """A citation the resolver validated: its role and locator come from the ids."""

    extraction_id: str
    span_id: str
    unit_id: str
    source_id: str
    revision_id: str
    role: str
    relation: str
    span_hash: str | None = None

    @property
    def locator(self) -> str:
        return format_block_span(self.extraction_id, self.span_id)

    @property
    def supports(self) -> bool:
        return is_semantic_support(self.role, self.relation)

    def citation(self) -> dict[str, Any]:
        """The ids a proposal's ``meaning_support`` carries (re-resolved at apply)."""

        return {"extraction_id": self.extraction_id, "unit_id": self.unit_id, "span_id": self.span_id,
                "relation": self.relation}

    def yaml_ref(self) -> dict[str, Any]:
        """The provenance ref a facet (or any entity) records for this citation."""

        return {
            "ref_type": "canonical_source",
            "ref_id": self.source_id,
            "source_id": self.source_id,
            "revision_id": self.revision_id,
            "extraction_id": self.extraction_id,
            "locator": self.locator,
            "locator_scheme": BLOCK_SPAN_V1,
            "relation": self.relation,
            "role": self.role,
            "span_hash": self.span_hash,
        }

    def gate_ref(self, *, held_out: bool = False) -> ProvenanceRef:
        return ProvenanceRef(
            extraction_id=self.extraction_id, revision_id=self.revision_id, unit_id=self.unit_id or None,
            span_id=self.span_id, relation=self.relation, role=self.role, held_out=held_out,
        )


@dataclass(frozen=True)
class CitationProblem:
    """A citation that does not resolve, and why. It supports nothing."""

    citation: Mapping[str, Any]
    problem: str

    def label(self) -> str:
        return f"{self.citation.get('extraction_id') or '?'}:{self.citation.get('span_id') or '?'}"


@dataclass(frozen=True)
class _Member:
    #: The member revision's latest extraction ("" when it has none yet). A
    #: citation of any other extraction of the same pinned revision resolves
    #: through the revision (Codex re-review F4).
    extraction_id: str
    source_id: str
    revision_id: str
    default_role: str
    scope: tuple[tuple[str, str | None], ...]
    source_set_id: str = ""


@dataclass
class _Units:
    """One extraction's units: each raw and each effective unit with the spans it holds."""

    raw: dict[str, frozenset[str]]
    effective: dict[str, frozenset[str]]
    spans: set[str]

    def spans_of(self, unit_id: str) -> frozenset[str] | None:
        """The spans ``unit_id`` holds, or None when it is no unit of this extraction.

        A raw unit holds its own spans. An effective unit holds what the
        boundary overrides give it: a merge its members' spans, a split child
        only the blocks under its own heading (Codex re-review F3), never its
        raw parent's.
        """

        if unit_id in self.raw:
            return self.raw[unit_id]
        return self.effective.get(unit_id)


def _authority_rank(role: str) -> int:
    """Lower is less authoritative: exam, then roles that never support a claim, then explanatory."""

    if role in ASSESSMENT_ONLY_ROLES:
        return 0
    return 1 if not can_authorize_semantic(role) else 2


class CitationResolver:
    """Resolves citations against source-set members (their selected units and roles)."""

    def __init__(
        self,
        members: Sequence[_Member],
        *,
        load_ir: Callable[[str], Any],
        load_overrides: Callable[[str], Sequence[Mapping[str, Any]]],
        load_revision: Callable[[str], str | None] | None = None,
    ) -> None:
        self._members = list(members)
        self._load_ir = load_ir
        self._load_overrides = load_overrides
        self._load_revision = load_revision
        self._units: dict[str, _Units | None] = {}
        self._revisions: dict[str, str | None] = {}

    @classmethod
    def for_source_sets(cls, repository: Any, source_sets: Iterable[Any]) -> CitationResolver:
        members: list[_Member] = []
        for source_set in source_sets:
            for member in source_set.members:
                members.append(_Member(
                    extraction_id=resolve_extraction_id(repository, member.revision_id) or "",
                    source_id=member.source_id, revision_id=member.revision_id,
                    default_role=str(member.default_role or ""),
                    scope=tuple((str(entry.unit_id), entry.role_override) for entry in member.scope),
                    source_set_id=str(source_set.id),
                ))

        def overrides(extraction_id: str) -> Sequence[Mapping[str, Any]]:
            return list((repository.get_unit_selection(extraction_id) or {}).get("boundary_overrides") or [])

        def revision(extraction_id: str) -> str | None:
            run = repository.get_extraction_run(extraction_id)
            return str(run["revision_id"]) if run and run.get("revision_id") else None

        return cls(members, load_ir=repository.load_document_ir, load_overrides=overrides, load_revision=revision)

    @classmethod
    def for_source_set(cls, repository: Any, source_set: Any) -> CitationResolver:
        return cls.for_source_sets(repository, [source_set])

    @classmethod
    def for_vault(cls, repository: Any, vault: Any) -> CitationResolver:
        return cls.for_source_sets(repository, vault.source_sets)

    def _index(self, extraction_id: str) -> _Units | None:
        if extraction_id not in self._units:
            ir = self._load_ir(extraction_id)
            if ir is None:
                self._units[extraction_id] = None
            else:
                effective = effective_unit_spans(ir, list(self._load_overrides(extraction_id)))
                self._units[extraction_id] = _Units(
                    raw={unit.unit_id: frozenset(unit.span_ids) for unit in ir.units},
                    effective={unit_id: frozenset(spans) for unit_id, spans in effective.items()},
                    spans={block.span_id for block in ir.blocks},
                )
        return self._units[extraction_id]

    def _members_for(self, extraction_id: str) -> list[_Member]:
        """The members an extraction run belongs to: by its id, else by the revision it extracted.

        A re-extraction of a member's pinned revision makes it the member's
        latest extraction; a citation of the earlier one still belongs to that
        member, with its role and scope (Codex re-review F4), rather than
        becoming a citation that resolves nowhere.
        """

        members = [member for member in self._members if member.extraction_id == extraction_id]
        if members or self._load_revision is None:
            return members
        if extraction_id not in self._revisions:
            self._revisions[extraction_id] = self._load_revision(extraction_id)
        revision_id = self._revisions[extraction_id]
        if not revision_id:
            return []
        return [member for member in self._members if member.revision_id == revision_id]

    def resolve(
        self, citation: Mapping[str, Any], *, default_relation: str = "support",
    ) -> ResolvedCitation | CitationProblem:
        """Validate a citation by its ids; the model's role, source, revision and locator are ignored.

        The span's role is decided by the scope entries that hold it (a split
        child holds only its own blocks): an entry's ``role_override``, else
        the member's role. When several entries or members select the span, the
        least authoritative role wins, whatever order they are listed in.
        """

        citation = dict(citation)
        extraction_id = str(citation.get("extraction_id") or "")
        span_id = str(citation.get("span_id") or "")
        unit_id = str(citation.get("unit_id") or "")
        if not extraction_id or not span_id:
            return CitationProblem(citation, "no span cited")
        members = self._members_for(extraction_id)
        if not members:
            return CitationProblem(citation, f"extraction run {extraction_id} is not in the source set")
        units = self._index(extraction_id)
        if units is None or span_id not in units.spans:
            return CitationProblem(citation, f"span {span_id} does not resolve in extraction run {extraction_id}")
        if unit_id:
            named = units.spans_of(unit_id)
            if named is None:
                return CitationProblem(citation, f"unit {unit_id} is not valid for extraction run {extraction_id}")
            if span_id not in named:
                return CitationProblem(
                    citation, f"span {span_id} is not in unit {unit_id} of extraction run {extraction_id}",
                )
        containing = sorted(unit for unit, spans in units.raw.items() if span_id in spans)
        hits: list[tuple[str, str, _Member]] = []  # (role, unit, member)
        for member in members:
            if not member.scope:  # the whole artifact is in scope, with the member's role
                hits.append((member.default_role, unit_id or (containing[0] if containing else ""), member))
                continue
            for scope_unit, role_override in member.scope:
                held = units.spans_of(scope_unit)
                if held is None or span_id not in held:
                    continue
                hits.append((str(role_override or member.default_role), unit_id or scope_unit, member))
        if not hits:
            return CitationProblem(
                citation, f"span {span_id} is outside the selected units of extraction run {extraction_id}",
            )
        role, unit, member = min(hits, key=lambda hit: (_authority_rank(hit[0]), hit[0], hit[1]))
        relation = str(citation.get("relation") or default_relation)
        if relation not in CITATION_RELATIONS:
            relation = default_relation if default_relation in CITATION_RELATIONS else "support"
        if role in ASSESSMENT_ONLY_ROLES:
            relation = "assessment_alignment"
        span_hash = citation.get("span_hash")
        return ResolvedCitation(
            extraction_id=extraction_id, span_id=span_id, unit_id=unit, source_id=member.source_id,
            revision_id=member.revision_id, role=role, relation=relation,
            span_hash=str(span_hash) if span_hash else None,
        )

    def resolve_ref(self, ref: Mapping[str, Any], *, default_relation: str = "support") -> ResolvedCitation | CitationProblem:
        """Resolve a persisted provenance ref by the span its locator names (its identity)."""

        parsed = parse_block_span(str(ref.get("locator") or ""))
        if parsed is None:
            return CitationProblem(dict(ref), "not a block-span citation")
        extraction_id, span_id = parsed
        return self.resolve(
            {"extraction_id": extraction_id, "span_id": span_id, "relation": ref.get("relation"),
             "span_hash": ref.get("span_hash")},
            default_relation=default_relation,
        )


# --- the rule -------------------------------------------------------------------------------


@dataclass(frozen=True)
class Contribution:
    """The citations one source of a write's meaning offers (a candidate, a reword, an absorbed facet)."""

    label: str
    citations: tuple[Mapping[str, Any], ...] = ()


def contributions(citations: Iterable[Mapping[str, Any]], *, label: str = "write") -> tuple[Contribution, ...]:
    return (Contribution(label, tuple(dict(citation) for citation in citations)),)


def support_entries(contributed: Iterable[Contribution]) -> list[dict[str, Any]]:
    """A proposal payload's ``meaning_support``: each contribution's citations by id."""

    return [{"from": item.label, "citations": [dict(citation) for citation in item.citations]}
            for item in contributed]


def _invalid_support(message: str) -> FacetAuthorityError:
    return FacetAuthorityError("invalid_meaning_support", f"meaning_support {message}")


def _cited_span(citation: Any, where: str) -> dict[str, Any]:
    if not isinstance(citation, Mapping):
        raise _invalid_support(f"{where} is not a citation (a mapping with extraction_id and span_id)")
    if not str(citation.get("extraction_id") or "") or not str(citation.get("span_id") or ""):
        raise _invalid_support(f"{where} names no span (extraction_id and span_id)")
    return dict(citation)


def contributions_from_support(meaning_support: Any) -> tuple[Contribution, ...]:
    """Parse a payload's ``meaning_support`` (a flat citation list is one contribution).

    Bookkeeping that is not a list of contributions (``{"from", "citations":
    [...]}``) or of citations, each naming a span, is refused
    (``invalid_meaning_support``), never read as "no support" (Codex re-review F2).
    """

    if not isinstance(meaning_support, list):
        raise _invalid_support("must be a list of contributions")
    out: list[Contribution] = []
    flat: list[dict[str, Any]] = []
    for index, entry in enumerate(meaning_support, start=1):
        where = f"entry {index}"
        if not isinstance(entry, Mapping):
            raise _invalid_support(f"{where} is not a contribution or a citation")
        if "citations" in entry:
            citations = entry["citations"]
            if not isinstance(citations, list):
                raise _invalid_support(f"{where}'s citations must be a list")
            label = entry.get("from")
            if label is not None and not isinstance(label, str):
                raise _invalid_support(f"{where}'s from must be a label")
            out.append(Contribution(
                str(label or f"contribution {index}"),
                tuple(_cited_span(citation, f"{where}, citation {number}")
                      for number, citation in enumerate(citations, start=1)),
            ))
        else:
            flat.append(_cited_span(entry, where))
    if flat:
        out.append(Contribution("write", tuple(flat)))
    return tuple(out)


def _refs(entry: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    provenance = (entry or {}).get("provenance") or {}
    refs = provenance.get("source_refs") if isinstance(provenance, Mapping) else None
    return [dict(ref) for ref in refs or [] if isinstance(ref, Mapping)]


def _ref_key(ref: Mapping[str, Any]) -> str:
    if ref.get("locator"):
        return f"{ref.get('locator')}|{ref.get('relation') or ''}|{ref.get('revision_id') or ''}"
    return json.dumps(dict(ref), sort_keys=True, default=str)


def _new_refs(before: Mapping[str, Any] | None, after: Mapping[str, Any]) -> list[dict[str, Any]]:
    seen = {_ref_key(ref) for ref in _refs(before)}
    return [ref for ref in _refs(after) if _ref_key(ref) not in seen]


def _span_key(citation: Mapping[str, Any]) -> tuple[str, str]:
    return str(citation.get("extraction_id") or ""), str(citation.get("span_id") or "")


def write_contributions(
    payload: Mapping[str, Any], *, before: Mapping[str, Any] | None, after: Mapping[str, Any],
) -> tuple[Contribution, ...]:
    """What supports a proposal write: its ``meaning_support``, reconciled with the refs it records.

    Without ``meaning_support`` the block-span refs the write adds are its one
    contribution. With it, each declared contribution is judged on its own,
    and a block-span ref the write records that no declared contribution cites
    is one more contribution, judged on its own too (Codex re-review F2): an
    empty or partial declaration never hides the write's own exam citation, nor
    lets a declared explanatory span corroborate a citation it does not name.
    Malformed bookkeeping raises :class:`FacetAuthorityError`.
    """

    recorded: list[dict[str, Any]] = []
    for ref in _new_refs(before, after):
        parsed = parse_block_span(str(ref.get("locator") or ""))
        if parsed is not None:
            recorded.append({"extraction_id": parsed[0], "span_id": parsed[1], "relation": ref.get("relation")})
    if "meaning_support" not in payload:
        return contributions(recorded, label="provenance") if recorded else ()
    declared = contributions_from_support(payload.get("meaning_support"))
    covered = {_span_key(citation) for item in declared for citation in item.citations}
    uncovered = tuple(citation for citation in recorded if _span_key(citation) not in covered)
    return (*declared, *((Contribution("provenance", uncovered),) if uncovered else ()))


@dataclass(frozen=True)
class MeaningVerdict:
    """Whether one facet meaning write is allowed, and why."""

    facet_id: str
    allowed: bool
    code: str
    fields: tuple[str, ...] = ()
    resolved: tuple[ResolvedCitation, ...] = ()
    problems: tuple[str, ...] = ()
    message: str = ""

    def diagnostic(self, *, entity_refs: Sequence[str] | None = None, severity: str = "review",
                   suggested_action: str | None = None) -> dict[str, Any]:
        """A typed review record for a producer that dropped what this verdict refuses."""

        return {
            "gate": "exam_authority" if self.code == "exam_authority" else "facet_restructure",
            "severity": severity,
            "entity_refs": list(entity_refs or [self.facet_id]),
            "message": self.message,
            "suggested_action": suggested_action or (
                "cite an explanatory span (textbook, lecture, paper, reference or alternate explanation) "
                "from the selected units, or reword the facet yourself in the Library (an owner reword, "
                "with an undo)"
            ),
        }


def _verdict(facet_id: str, allowed: bool, code: str, message: str = "", **kwargs: Any) -> MeaningVerdict:
    return MeaningVerdict(facet_id=facet_id, allowed=allowed, code=code, message=message, **kwargs)


def check_meaning_write(
    facet_id: str,
    *,
    before: Mapping[str, Any] | None,
    after: Mapping[str, Any],
    registered: bool,
    contributions: Sequence[Contribution],
    resolver: CitationResolver | None,
    require_resolved: bool = False,
) -> MeaningVerdict:
    """Judge one write of a facet's meaning from validated citations (the §4.2 rule, once).

    ``registered``: the facet is in the registry, so a change needs an
    explanatory citation in every contribution. Otherwise (a new facet, or a
    candidate a consolidation grows) only an exam-uncorroborated contribution
    is refused. Citations resolve through ``resolver``; without one none does.

    ``require_resolved``: the citations were recorded (an undo restoring a
    candidate on its own citations), so one that no longer resolves refuses
    the write (``unresolved_citation``) instead of leaving the contribution
    "uncited" (Codex re-review F4): only a write that cites nothing gets the
    treatment of uncited content.
    """

    fields = tuple(authority_changes(before, after))
    if not fields:
        return _verdict(facet_id, True, "unchanged")
    resolved_all: list[ResolvedCitation] = []
    problems: list[str] = []
    verdicts: list[tuple[str, str]] = []
    for contribution in contributions:
        resolved: list[ResolvedCitation] = []
        for citation in contribution.citations:
            result = (resolver.resolve(citation, default_relation="support") if resolver is not None
                      else CitationProblem(citation, "no source set to resolve it in"))
            if isinstance(result, ResolvedCitation):
                resolved.append(result)
            else:
                problems.append(f"{result.label()}: {result.problem}")
        resolved_all.extend(resolved)
        verdicts.append((contribution.label, support_verdict((item.role, item.relation) for item in resolved)))
    where = ", ".join(fields)
    detail = f" ({'; '.join(problems)})" if problems else ""
    extra = {"fields": fields, "resolved": tuple(resolved_all), "problems": tuple(problems)}
    exam_only = [label for label, verdict in verdicts if verdict == EXAM_UNCORROBORATED]
    if exam_only:
        return _verdict(
            facet_id, False, "exam_authority",
            f"exam material would change facet {facet_id}'s meaning ({where}) with no explanatory span "
            f"beside it ({', '.join(exam_only)}): an exam citation only ever aligns assessment (§4.2){detail}",
            **extra,
        )
    if require_resolved and problems:
        return _verdict(
            facet_id, False, "unresolved_citation",
            f"facet {facet_id}'s recorded citations no longer resolve in the source sets, so their authority "
            f"cannot be judged ({where}){detail}",
            **extra,
        )
    if registered:
        if not verdicts or any(verdict != EXPLANATORY for _label, verdict in verdicts):
            return _verdict(
                facet_id, False, "unsupported_reword",
                f"a change to registered facet {facet_id}'s meaning ({where}) cites no span from an "
                f"explanatory source in the selected units{detail}",
                **extra,
            )
        return _verdict(facet_id, True, "explanatory", **extra)
    explained = bool(verdicts) and all(verdict == EXPLANATORY for _label, verdict in verdicts)
    return _verdict(facet_id, True, "explanatory" if explained else "new_unsupported", **extra)


def written_provenance(
    before: Mapping[str, Any] | None, after: Mapping[str, Any], verdict: MeaningVerdict,
    resolver: CitationResolver | None, *, record_support: bool = True,
) -> dict[str, Any]:
    """The provenance a checked write records: what it displays is what was validated.

    The entry's earlier refs stay as they were. Each ref the write adds is
    rewritten from the span its locator names (role, relation, extraction and
    source from the resolution); one that does not resolve (or names no block
    span, or has no source set to resolve in) is kept, marked ``unresolved``,
    and supports nothing: it never becomes a source link
    (:func:`added_provenance`). With ``record_support`` (a write that states
    its provenance), every citation the verdict resolved is recorded too (an
    exam one as ``assessment_alignment``); a write that leaves provenance alone
    (an alias, a grown example) keeps the facet's as it was.
    """

    provenance = dict((after or {}).get("provenance") or {})
    old_keys = {_ref_key(ref) for ref in _refs(before)}
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ref in _refs(after):
        if _ref_key(ref) not in old_keys and ref.get("locator"):  # a ref with no locator never links
            parsed = parse_block_span(str(ref.get("locator") or ""))
            result = resolver.resolve_ref(ref) if resolver is not None and parsed is not None else None
            if isinstance(result, ResolvedCitation):
                ref = {**ref, **result.yaml_ref()}
            else:
                ref = {**ref, **({"extraction_id": parsed[0]} if parsed is not None else {}),
                       "role": UNRESOLVED_ROLE}
        key = _ref_key(ref)
        if key in seen:
            continue
        seen.add(key)
        out.append(ref)
    for citation in verdict.resolved if record_support else ():
        ref = citation.yaml_ref()
        if _ref_key(ref) not in seen:
            seen.add(_ref_key(ref))
            out.append(ref)
    return {"origin": provenance.get("origin") or "manual", "source_refs": out}


def added_provenance(before: Mapping[str, Any] | None, written: Mapping[str, Any]) -> dict[str, Any]:
    """The refs a write adds that were validated (what its ``entity_source_links`` rows record).

    A ref marked ``unresolved`` is left out (Codex re-review F5): a link row is
    ``current`` provenance, and a ``primary`` one is the entity's displayed
    semantic authority (``content.sources.provenance``), so a citation outside
    the selected units, or one that resolves nowhere, never becomes one.
    """

    return {"provenance": {"source_refs": [
        ref for ref in _new_refs(before, written) if ref.get("role") != UNRESOLVED_ROLE
    ]}}


# --- merges and absorbs ---------------------------------------------------------------------


@dataclass(frozen=True)
class Join:
    """A candidate merged or absorbed into a survivor: whether its meaning joined."""

    payload: dict[str, Any]
    joined: bool
    verdict: MeaningVerdict


def join_candidate(
    survivor: Mapping[str, Any],
    retired: Mapping[str, Any],
    *,
    survivor_id: str,
    action: str,
    absorb_as: str | None,
    contribution: Contribution,
    registered: bool,
    resolver: CitationResolver | None,
) -> Join:
    """Merge or absorb a candidate into ``survivor``, through the authority rule.

    The candidate's meaning (conditions, examples, its claim as an example or a
    precondition) joins only when :func:`check_meaning_write` allows that change
    of the survivor on the candidate's own citations. Otherwise it joins as an
    alias only: the survivor keeps its meaning and its provenance.
    """

    union = union_payload(survivor, [retired], action=action, absorb_as=absorb_as)
    union["id"] = survivor_id
    verdict = check_meaning_write(
        survivor_id, before=survivor, after=union, registered=registered, contributions=[contribution],
        resolver=resolver,
    )
    if verdict.allowed:
        return Join(payload=union, joined=True, verdict=verdict)
    alias_only = union_payload(survivor, [{"aliases": list(retired.get("aliases") or [])}], action="merge")
    alias_only["id"] = survivor_id
    return Join(payload=alias_only, joined=False, verdict=verdict)


def merged_survivor(
    survivor: Mapping[str, Any], retired: Sequence[Mapping[str, Any]], *, action: str, absorb_as: str | None,
    alias_ids: Sequence[str],
) -> dict[str, Any]:
    """A vault merge's survivor: the union of registered facets (their meaning was admitted)."""

    return union_payload(survivor, retired, action=action, absorb_as=absorb_as, alias_ids=alias_ids)


# --- the registry writer ----------------------------------------------------------------------


@dataclass(frozen=True)
class OwnerEdit:
    """The owner's own Library save: explicit manual authority, audited.

    ``judgment_id`` is the owner's ``granted`` verdict in ``judgment_ledger``
    for this facet's new meaning (scope, actor, timestamp, rationale), recorded
    before the write (Codex re-review F6); an owner edit without one is refused.
    """

    judgment_id: str = ""
    via: str = "library"


@dataclass(frozen=True)
class Cited:
    """A change supported by recorded citations, judged by :func:`check_meaning_write`.

    ``require_resolved``: a recorded citation that no longer resolves refuses
    the write rather than counting as no citation (Codex re-review F4).
    """

    contributions: tuple[Contribution, ...] = ()
    require_resolved: bool = True


@dataclass(frozen=True)
class RegisteredMerge:
    """A vault merge of registered facets: the survivor must be their union, recomputed here."""

    survivor: str
    retired: tuple[str, ...]
    action: str
    absorb_as: str | None = None


@dataclass(frozen=True)
class Restore:
    """An undo or recovery: each changed facet must be exactly an entry an action recorded."""

    entries: Mapping[str, Mapping[str, Any] | None] = field(default_factory=dict)


Basis = OwnerEdit | Cited | RegisteredMerge | Restore


def registry_entries(document: Any, *, strict: bool = True) -> dict[str, dict[str, Any]]:
    """``{facet id: entry}`` of a registry document; ``strict`` refuses an id listed twice."""

    facets = document.get("facets") if isinstance(document, Mapping) else None
    out: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []
    for entry in facets or []:
        if not isinstance(entry, Mapping):
            continue
        facet_id = str(entry.get("id") or "")
        if facet_id in out:
            duplicates.append(facet_id)
            continue
        out[facet_id] = dict(entry)
    if strict and duplicates:
        raise FacetAuthorityError(
            "duplicate_facet_ids",
            f"facets.yaml lists {', '.join(sorted(set(duplicates)))} more than once: each facet id is one entry",
        )
    return out


def _file_entries(paths: VaultPaths) -> dict[str, dict[str, Any]]:
    if not paths.facets_path.exists():
        return {}
    try:
        return registry_entries(read_yaml(paths.facets_path), strict=False)
    except Exception:  # noqa: BLE001 - an unreadable registry has no entries to keep
        return {}


def _check_basis(
    facet_id: str,
    before: Mapping[str, Any] | None,
    entry: Mapping[str, Any],
    basis: Basis | None,
    current: Mapping[str, Mapping[str, Any]],
    resolver: CitationResolver | None,
) -> MeaningVerdict:
    fields = tuple(authority_changes(before, entry))
    where = ", ".join(fields)
    if isinstance(basis, OwnerEdit):
        if not basis.judgment_id:
            return _verdict(facet_id, False, "unaudited",
                            f"the owner's edit of facet {facet_id}'s meaning ({where}) has no authority verdict "
                            "recorded for it", fields=fields)
        return _verdict(facet_id, True, "owner", fields=fields)
    if isinstance(basis, Cited):
        if resolver is None:  # fail closed: an exam citation cannot be told apart without one
            return _verdict(facet_id, False, "unauthorized",
                            f"facet {facet_id}'s cited change ({where}) has no source set to resolve its citations",
                            fields=fields)
        return check_meaning_write(facet_id, before=before, after=entry, registered=before is not None,
                                   contributions=basis.contributions, resolver=resolver,
                                   require_resolved=basis.require_resolved)
    if isinstance(basis, RegisteredMerge):
        members = (basis.survivor, *basis.retired)
        if facet_id == basis.survivor and all(member in current for member in members):
            expected = merged_survivor(
                current[basis.survivor], [current[member] for member in basis.retired], action=basis.action,
                absorb_as=basis.absorb_as, alias_ids=basis.retired,
            )
            if authority_meaning(expected) == authority_meaning(entry):
                return _verdict(facet_id, True, "registered", fields=fields)
        return _verdict(facet_id, False, "unauthorized",
                        f"facet {facet_id}'s new meaning ({where}) is not the union of the registered facets "
                        f"{', '.join(members)}", fields=fields)
    if isinstance(basis, Restore):
        recorded = basis.entries.get(facet_id)
        if recorded is not None and authority_meaning(recorded) == authority_meaning(entry):
            return _verdict(facet_id, True, "restore", fields=fields)
        return _verdict(facet_id, False, "unauthorized",
                        f"facet {facet_id}'s meaning ({where}) is not the entry the action recorded", fields=fields)
    return _verdict(facet_id, False, "unauthorized",
                    f"nothing authorizes the change to facet {facet_id}'s meaning ({where})", fields=fields)


def check_registry_text(
    paths: VaultPaths,
    text: str,
    *,
    basis: Mapping[str, Basis],
    resolver: CitationResolver | None = None,
) -> dict[str, MeaningVerdict]:
    """Verify, without writing, that every meaning change ``text`` makes to facets.yaml is authorized.

    Each facet whose :data:`AUTHORITY_FIELDS` differ from the file (a new
    facet included) must have a basis that verifies (see the module
    docstring); otherwise :class:`FacetAuthorityError` is raised. A facet id
    listed twice is refused. Returns the verdict of each changed facet. A
    caller that records an intent before writing (an undo) checks first, so a
    refused write leaves nothing in flight (Codex re-review F1).
    """

    try:
        document = yaml_from_string(text) or {}
    except Exception as exc:  # noqa: BLE001 - an unparseable registry is never written
        raise FacetAuthorityError("invalid_registry", f"facets.yaml does not parse: {exc}") from exc
    entries = registry_entries(document)
    current = _file_entries(paths)
    verdicts: dict[str, MeaningVerdict] = {}
    for facet_id, entry in entries.items():
        before = current.get(facet_id)
        if not authority_changes(before, entry):
            continue
        verdict = _check_basis(facet_id, before, entry, basis.get(facet_id), current, resolver)
        if not verdict.allowed:
            raise FacetAuthorityError(verdict.code, verdict.message, facet_id=facet_id)
        verdicts[facet_id] = verdict
    return verdicts


def write_registry_text(
    paths: VaultPaths,
    text: str,
    *,
    basis: Mapping[str, Basis],
    resolver: CitationResolver | None = None,
) -> None:
    """Replace facets.yaml with ``text`` if every meaning change in it is authorized.

    The caller holds the vault mutation lock. :func:`check_registry_text`
    decides; when it refuses, :class:`FacetAuthorityError` is raised and
    nothing is written. The file is replaced atomically (a staged, fsynced
    temp file and a rename).
    """

    from learnloop.content.proposals.apply_protocol import materialize_targets

    check_registry_text(paths, text, basis=basis, resolver=resolver)
    materialize_targets(paths.root, [{
        "rel_path": str(paths.facets_path.relative_to(paths.root)),
        "post_content": text,
        "post_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }])


# --- the proposal compiler's context ------------------------------------------------------------


class ProposalAuthority:
    """The chokepoint's context for one proposal apply.

    It resolves citations in the proposal's own source set (the one its
    synthesis run was made from), or in every source set of the vault when the
    proposal has none, and it keeps what each facet item was checked to write,
    for :func:`verify_registry_transition`.
    """

    def __init__(self, resolver_factory: Callable[[], CitationResolver | None]) -> None:
        self._factory = resolver_factory
        self._resolver: CitationResolver | None = None
        self._built = False
        self.checked: dict[str, dict[str, Any]] = {}

    @property
    def resolver(self) -> CitationResolver | None:
        if not self._built:
            self._resolver = self._factory()
            self._built = True
        return self._resolver

    def record(self, facet_id: str, entry: Mapping[str, Any]) -> None:
        self.checked[facet_id] = copy.deepcopy(dict(entry))

    @classmethod
    def for_proposal(cls, vault: Any, repository: Any, patch_id: str) -> ProposalAuthority:
        def factory() -> CitationResolver:
            source_set = _proposal_source_set(vault, repository, patch_id)
            if source_set is not None:
                return CitationResolver.for_source_set(repository, source_set)
            return CitationResolver.for_vault(repository, vault)

        return cls(factory)


def _proposal_source_set(vault: Any, repository: Any, patch_id: str) -> Any:
    batch = repository.proposal_batch(patch_id) or {}
    agent_run_id = str(batch.get("agent_run_id") or "")
    run = repository.synthesis_run_for_agent_run(agent_run_id) if agent_run_id else None
    manifest_id = str((run or {}).get("manifest_id") or "")
    manifest = repository.synthesis_manifest(manifest_id) if manifest_id else None
    source_set_id = str((manifest or {}).get("source_set_id") or "")
    return next((source_set for source_set in vault.source_sets if source_set.id == source_set_id), None)


def verify_registry_transition(
    paths: VaultPaths, targets: Sequence[Mapping[str, Any]], *, checked: Mapping[str, Mapping[str, Any]],
) -> None:
    """Refuse a staged facets.yaml whose meaning changes no checked facet item wrote.

    ``targets`` are the staged files of one proposal apply; ``checked`` is what
    the compiler checked each facet item to write (:class:`ProposalAuthority`).
    """

    rel_path = str(paths.facets_path.relative_to(paths.root))
    target = next((item for item in targets if item.get("rel_path") == rel_path), None)
    if target is None:
        return
    current = _file_entries(paths)
    staged = registry_entries(yaml_from_string(str(target.get("post_content") or "")) or {})
    for facet_id, entry in staged.items():
        fields = authority_changes(current.get(facet_id), entry)
        if not fields:
            continue
        recorded = checked.get(facet_id)
        if recorded is None or authority_meaning(recorded) != authority_meaning(entry):
            raise FacetAuthorityError(
                "unauthorized",
                f"the staged registry changes facet {facet_id}'s meaning ({', '.join(fields)}) "
                "that no checked facet write produced",
                facet_id=facet_id,
            )


__all__ = [
    "ALLOWED_CODES",
    "AUTHORITY_FIELDS",
    "Basis",
    "Cited",
    "CitationProblem",
    "CitationResolver",
    "Contribution",
    "FacetAuthorityError",
    "Join",
    "MeaningVerdict",
    "OwnerEdit",
    "PROPOSAL_ONLY_KEYS",
    "ProposalAuthority",
    "RegisteredMerge",
    "ResolvedCitation",
    "Restore",
    "UNRESOLVED_ROLE",
    "added_provenance",
    "authority_changes",
    "authority_meaning",
    "check_meaning_write",
    "check_registry_text",
    "contributions",
    "contributions_from_support",
    "join_candidate",
    "merged_survivor",
    "overlay",
    "registry_entries",
    "support_entries",
    "verify_registry_transition",
    "write_contributions",
    "write_registry_text",
    "written_provenance",
]
