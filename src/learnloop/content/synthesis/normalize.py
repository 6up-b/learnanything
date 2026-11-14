"""A synthesis answer into proposal rows: concepts, facets, learning objects, blueprints, practice items and
concept edges, each as a row beside the gate item the synthesis gates read.

The normalizer is deterministic given the model's answer, the vault and the clock. It runs as stages over one
:class:`_NormalizeState`, in an order that is part of its output: ids are minted in call order (``unique`` suffixes
a taken id ``_2``, ``_3`` in the order stages ask for it, and a ULID names every row and every entity the model left
untitled), so a stage that ran earlier or later would rename what it and the stages after it produce.

1. The registry's concepts are indexed, then the answer's concepts are minted, so a later stage can resolve a
   reference to either.
2. Facets are normalized into candidates first and judged afterwards: the mint gate's criterion is relative (a
   candidate is separable from its nearest neighbours), so no candidate can be judged until every candidate in the
   batch has a payload to be compared with. Facet identity's retirements come between the two: a candidate the
   judge merged or absorbed is not minted, and its survivor takes its meaning first, so the gate sees the
   consolidated facet.
3. The mint gate decides each remaining candidate's disposition (mint, alias into a neighbour, or abstain); a
   retired candidate's references then follow its survivor, the survivors' aliases are registered, and the
   identity actions record what changed. Everything after this reads ``facet_client_to_id`` and
   ``facet_dep_client``, which these stages fill.
4. Learning objects, blueprints and practice items resolve their references against those maps, in that order,
   because a blueprint merges onto its learning object and an item reads both.
5. Concept edges come last: the model's explicit relations first, then the floor derived from the learning
   objects' prerequisites and confusables, each validated against this proposal's concepts and the registry.

Whatever the stages drop or change that a reviewer should see (unresolved references, defaulted capabilities,
mint verdicts, cycle-forming edges) becomes a typed diagnostic on the state, never an exception: a weak model's
answer must not fail a paid synthesis. The append lane normalizes its new coverage through :func:`normalize` and
adds its own item kinds after it.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnloop.content.facet_identity import authority as facet_meaning
from learnloop.content.facet_identity.views import UNION_LIST_FIELDS
from learnloop.content.proposals.patches import compute_target_hash
from learnloop.content.synthesis.facet_mint_gate import MintDisposition, judge_facet_mints, mint_diagnostic
from learnloop.content.synthesis.graph_nomination import annotate_mint_report
from learnloop.content.synthesis.synthesis_gates import ATTACH_GROWABLE_FIELDS, GateItem, ProvenanceRef
from learnloop.ids import new_ulid, snake_case
from learnloop.vault.models import LoadedVault
from learnloop.vault.required_method import advisory_statement_flag, method_targets, normalize_required_method


def _slug(prefix: str, text: str, fallback: str) -> str:
    core = snake_case(text)[:48] if text else ""
    return f"{prefix}_{core}" if core else f"{prefix}_{fallback}"


@dataclass
class Normalized:
    rows: list[dict[str, Any]]
    gate_items: list[GateItem]
    conflict_candidates: list[str]
    non_conflict_dispositions: set[str]
    facet_payloads: list[dict[str, Any]]
    criterion_targets: list[dict[str, Any]]
    recipe_components: list[dict[str, Any]]
    facet_ids: list[str]
    # Typed review records of what normalization dropped or changed (concept edges, items, the D2 mint
    # verdicts; an append's links and restructures): they reach the gate diagnostics, or the drop is silent.
    edge_diagnostics: list[dict[str, Any]] = field(default_factory=list)
    # Slice 2 T5 shadow beside the D2 mint verdicts (None when nominations are
    # off): embedding neighbours and the repair-equivalence shadow. Never
    # changes a disposition.
    graph_nomination: dict[str, Any] | None = None
    # Facet identity (handoff §4): one undoable action per judged set the
    # proposal carries; recorded with the proposal.
    facet_identity_actions: list[dict[str, Any]] = field(default_factory=list)
    # The client ids §10.3 lets an append apply without review; None where the mode has no such lane, so its run
    # record names none.
    auto_apply_ids: list[str] | None = None


def _dump(obj: Any) -> dict[str, Any]:
    return obj if isinstance(obj, dict) else obj.model_dump()


@dataclass
class _NormalizeState:
    """What the stages share: the inputs, the id maps, the rows and gate items built so far, and the diagnostics.

    A field is here because more than one stage reads or writes it; a value one stage alone uses stays local to it.
    """

    synth: Any
    inputs: Any  # the source set's `_SynthesisInputs`: `resolver`, `held_out_span_ids` and `span_origin` are read
    vault: LoadedVault
    now: str
    subject_id: str
    items_off: bool = False
    nominator: Any = None
    facet_identity_plan: Any = None

    rows: list[dict[str, Any]] = field(default_factory=list)
    gate_items: list[GateItem] = field(default_factory=list)
    facet_payloads: list[dict[str, Any]] = field(default_factory=list)
    criterion_targets: list[dict[str, Any]] = field(default_factory=list)
    dropped_diagnostics: list[dict[str, Any]] = field(default_factory=list)
    recipe_components: list[dict[str, Any]] = field(default_factory=list)
    # (lo_entity_id, lo_concept_entity_id, prerequisite ids, confusable ids)
    lo_relation_seeds: list[tuple[str, str, list[str], list[str]]] = field(default_factory=list)

    # id assignment maps: client_item_id -> entity id
    concept_ids: dict[str, str] = field(default_factory=dict)
    concept_client_for_id: dict[str, str] = field(default_factory=dict)
    concept_reference_index: dict[str, set[str]] = field(default_factory=dict)
    facet_client_to_id: dict[str, str] = field(default_factory=dict)
    # candidate client key -> the client id of the row that materializes its facet.
    # Distinct from `facet_client_to_id` because the D2 mint gate can resolve a
    # candidate to a facet whose row is a DIFFERENT item (an earlier candidate it
    # aliased into) or to no row at all (an already-registered facet).
    facet_dep_client: dict[str, str] = field(default_factory=dict)
    lo_client_to_id: dict[str, str] = field(default_factory=dict)
    used_ids: set[str] = field(default_factory=set)

    # Facets: the candidates, what facet identity retired, and what the mint gate and the alias passes decided.
    candidate_facets: list[dict[str, Any]] = field(default_factory=list)
    retirements: dict[str, Any] = field(default_factory=dict)
    retired_candidates: dict[str, dict[str, Any]] = field(default_factory=dict)
    pre_union: dict[str, dict[str, Any]] = field(default_factory=dict)
    # Why a consolidation or attach kept a survivor's contract as it was.
    contract_notes: dict[str, list[str]] = field(default_factory=dict)
    graph_nomination: dict[str, Any] | None = None
    # target facet id -> candidate ids that collapsed into it (alias-not-mint).
    alias_additions: dict[str, list[str]] = field(default_factory=dict)
    minted_payload_by_id: dict[str, dict[str, Any]] = field(default_factory=dict)
    minted_client_by_id: dict[str, str] = field(default_factory=dict)
    # Proposal bookkeeping per facet row (``meaning_support``, a target hash),
    # added to the rows' payloads last so the facet dicts the identity actions
    # record stay what facets.yaml will hold.
    row_extras: dict[str, dict[str, Any]] = field(default_factory=dict)
    attach_unions: dict[str, list[tuple[dict[str, Any], Any, facet_meaning.Contribution]]] = field(
        default_factory=dict
    )
    alias_canonical: dict[str, str] = field(default_factory=dict)
    retired_targets: dict[str, tuple[str, str, Any, dict[str, Any]]] = field(default_factory=dict)
    registered_before: dict[str, dict[str, Any]] = field(default_factory=dict)
    facet_identity_actions: list[dict[str, Any]] = field(default_factory=list)

    # Concept edges: the review records, and the graph the validity checks walk.
    edge_diagnostics: list[dict[str, Any]] = field(default_factory=list)
    existing_edges: set[tuple[str, str, str]] = field(default_factory=set)
    edge_signatures: set[tuple[str, str, str]] = field(default_factory=set)
    prereq_adjacency: dict[str, set[str]] = field(default_factory=dict)
    part_of_parent: dict[str, str] = field(default_factory=dict)

    def unique(self, candidate: str) -> str:
        """``candidate``, or its first free ``_2``, ``_3`` ... suffix; the id is taken from then on."""

        base = candidate
        n = 2
        while candidate in self.used_ids:
            candidate = f"{base}_{n}"
            n += 1
        self.used_ids.add(candidate)
        return candidate


def _span_refs(
    refs: list[Any], inputs: Any, *, default_relation: str
) -> tuple[list[ProvenanceRef], list[dict[str, Any]], list[str]]:
    """Build gate ProvenanceRefs + YAML source_refs from synth span refs.

    Each citation resolves through the facet-meaning chokepoint's resolver
    (``facet_identity.authority.CitationResolver``, Codex verification of F6):
    its role is the cited unit's ``role_override`` when there is one, else its
    member's role (never the model's claimed role); the span must lie in the
    unit it is cited with and that unit must be selected; an exam citation's
    relation is ``assessment_alignment``; and the recorded locator is derived
    from the validated ids, never the model's. A citation that does not
    resolve is not recorded and supports nothing (role ``unresolved``): the
    span/scope/unit gates hard-fail one whose span, revision or unit does not
    exist, and ``citation_scope`` reviews one outside the selected scope.
    """

    gate_refs: list[ProvenanceRef] = []
    yaml_refs: list[dict[str, Any]] = []
    span_ids: list[str] = []
    for ref in refs or []:
        ref = ref if isinstance(ref, dict) else ref.model_dump()
        extraction_id = str(ref.get("extraction_id") or "")
        span_id = str(ref.get("span_id") or "")
        unit_id = str(ref.get("unit_id") or "")
        if not extraction_id and not span_id:
            # A blank ref is "no citation", not a citation to span "" of run
            # "". Skipping it lets the adequate-provenance gate judge the item
            # (review) instead of three hard-fails naming an empty string.
            continue
        namespaced = f"{extraction_id}:{span_id}"
        held_out = namespaced in inputs.held_out_span_ids
        resolved = (
            inputs.resolver.resolve(ref, default_relation=default_relation)
            if inputs.resolver is not None
            else facet_meaning.CitationProblem(ref, "no source set to resolve it in")
        )
        if isinstance(resolved, facet_meaning.ResolvedCitation):
            gate_refs.append(resolved.gate_ref(held_out=held_out))
            yaml_refs.append(resolved.yaml_ref())
        else:
            origin = inputs.span_origin.get(extraction_id, {})
            gate_refs.append(
                ProvenanceRef(
                    extraction_id=extraction_id,
                    revision_id=origin.get("revision_id", ref.get("revision_id") or ""),
                    # None is the gate's "no unit cited" spelling; "" would fail
                    # unit_id_validity even when the span itself resolves.
                    unit_id=unit_id or None,
                    span_id=span_id,
                    relation=str(ref.get("relation") or default_relation),
                    role=facet_meaning.UNRESOLVED_ROLE,
                    held_out=held_out,
                    problem=resolved.problem,
                )
            )
        if span_id:
            span_ids.append(namespaced)
    return gate_refs, yaml_refs, span_ids


def _unresolved_citations(gate_refs: list[ProvenanceRef]) -> list[dict[str, Any]]:
    """The citations of a candidate that did not resolve, by their ids (they support nothing)."""

    return [
        {"extraction_id": ref.extraction_id, "unit_id": ref.unit_id or "", "span_id": ref.span_id,
         "relation": ref.relation}
        for ref in gate_refs
        if ref.role == facet_meaning.UNRESOLVED_ROLE and ref.extraction_id and ref.span_id
    ]


def _joined_contribution(candidate: Mapping[str, Any]) -> facet_meaning.Contribution:
    """What a retired candidate offers the survivor its meaning joins (in-run consolidation or attach).

    Its validated citations and the ones that did not resolve (Codex review of
    the reword confirm, F1): an unresolved citation supports nothing, but one
    that names exam material by its span (under the wrong unit, say) must keep
    the candidate's claim, conditions and examples out of the survivor, as a
    resolved exam citation does. Without it the contribution would read as
    "uncited", which a new survivor takes and a registered one takes as a
    worked example.
    """

    return facet_meaning.Contribution(
        str(candidate["fkey"]), (*candidate["support"], *candidate.get("unresolved", ())),
    )


def _support_citations(gate_refs: list[ProvenanceRef]) -> list[dict[str, Any]]:
    """The validated citations of a candidate, as a proposal's ``meaning_support`` carries them."""

    return [
        {"extraction_id": ref.extraction_id, "unit_id": ref.unit_id or "", "span_id": ref.span_id,
         "relation": ref.relation}
        for ref in gate_refs
        if ref.role != facet_meaning.UNRESOLVED_ROLE and ref.extraction_id and ref.span_id
    ]


def _facet_identity_actions(
    retired_targets: Mapping[str, tuple[str, str, Any, dict[str, Any]]],
    *,
    pre_union: Mapping[str, dict[str, Any]],
    minted_payload_by_id: Mapping[str, dict[str, Any]],
    registered_before: Mapping[str, dict[str, Any]],
    rows: Sequence[Mapping[str, Any]],
    vault: LoadedVault,
    aliased: set[str] | None = None,
    contract_notes: Mapping[str, Sequence[str]] | None = None,
) -> list[dict[str, Any]]:
    """One undoable action per survivor the proposal changes (facet identity).

    ``before``/``after`` are the facets.yaml entries the proposal's apply will
    replace and write: the survivor's entry without and with every set that
    joined it, and each retired candidate's entry (absent after). Sets from
    different judged groups on one survivor fold into one action (review F7):
    both took ``before`` from the one pre-union snapshot, so separate undos
    would strip each other's content. A set whose survivor the D2 mint gate
    itself aliased elsewhere is recorded without an undo.
    """

    if not retired_targets:
        return []
    groups: dict[tuple[str, str], list[tuple[str, str, Any, dict[str, Any]]]] = {}
    for fkey, (fid, target, retirement, payload) in sorted(retired_targets.items()):
        groups.setdefault((retirement.scope, target), []).append((fkey, fid, retirement, payload))
    actions: list[dict[str, Any]] = []
    for (scope, target), members in sorted(groups.items()):
        first = members[0][2]
        retired = [(fid, payload) for _fkey, fid, _r, payload in members
                   if fid != target and (aliased is None or fid in aliased)]
        if not retired:
            continue
        retired_ids = [fid for fid, _payload in retired]
        kept = [(fkey, fid, r) for fkey, fid, r, _p in members if fid in set(retired_ids)]
        verbs = {(r.action, r.absorb_as) for _fkey, _fid, r in kept}
        action_name = "absorb" if {verb for verb, _as in verbs} == {"absorb"} else "merge"
        absorb_as = next(iter(verbs))[1] if len(verbs) == 1 else None
        group_ids = sorted({r.group_id for _fkey, _fid, r in kept})
        detail: dict[str, Any] = {
            "group_id": group_ids[0] if len(group_ids) == 1 else group_ids,
            "absorb_as": absorb_as if action_name == "absorb" else None,
            "rationale": " / ".join(dict.fromkeys(r.rationale for _fkey, _fid, r in kept if r.rationale)),
            "retired_clients": [fkey for fkey, *_rest in members],
        }
        if len(verbs) > 1 or len(group_ids) > 1:
            detail["members"] = [
                {"facet_id": fid, "action": r.action, "absorb_as": r.absorb_as, "group_id": r.group_id}
                for _fkey, fid, r in kept
            ]
        notes = list(dict.fromkeys((contract_notes or {}).get(target, [])))
        if notes:
            detail["contract_note"] = "; ".join(notes)
        after_entry: dict[str, Any] | None = None
        before_entry: dict[str, Any] | None = None
        if scope == "in_run":
            after_payload = minted_payload_by_id.get(target)
            survivor_client = str(first.survivor_client or "")
            if after_payload is None or survivor_client not in pre_union:
                detail["undo"] = "unavailable: the survivor was aliased by the mint gate"
            else:
                after_entry = copy.deepcopy(after_payload)
                before_entry = copy.deepcopy(after_payload)
                for field_name in (*UNION_LIST_FIELDS, "provenance"):
                    if field_name in pre_union[survivor_client]:
                        before_entry[field_name] = copy.deepcopy(pre_union[survivor_client][field_name])
                    else:
                        before_entry.pop(field_name, None)
                before_entry["aliases"] = [
                    alias for alias in (after_payload.get("aliases") or []) if alias not in set(retired_ids)
                ]
        else:
            if target in registered_before:
                before_entry = copy.deepcopy(registered_before[target])
            elif target in vault.evidence_facets:
                before_entry = vault.evidence_facets[target].model_dump(mode="json")
            update = next((row["payload"] for row in rows
                           if row.get("item_type") == "facet" and row.get("operation") == "update"
                           and row.get("client_item_id") == f"facet_alias_{target}"), None)
            if before_entry is not None and update is not None:
                after_entry = {**before_entry, **copy.deepcopy(update)}
        actions.append({
            "scope": scope, "action": action_name, "survivor_facet_id": target,
            "retired_facet_ids": retired_ids,
            "before": {"facets": {target: before_entry, **dict(retired)}, "order": {}},
            "after": {"facets": {target: after_entry, **{fid: None for fid in retired_ids}}},
            "merge_rows": [],
            "judgment_ids": sorted({jid for _fkey, _fid, r, _p in members for jid in (r.judgment_ids or [])}),
            "judge": first.judge, "judge_model": first.judge_model, "prompt_version": first.prompt_version,
            "detail": detail,
        })
    return actions


def _keep_sibling_criterion_dependencies(
    item_id: str, criteria: list[dict[str, Any]], dropped_diagnostics: list[dict[str, Any]],
) -> None:
    """Keep each criterion's ``depends_on`` to sibling criterion ids (in place).

    A criterion's ``depends_on`` names the criteria of the SAME practice item
    that must be right before it can be judged (first-error localization,
    knowledge model §5.3). Models often write facet, blueprint, client or
    other items' criterion ids there; those name no criterion, so grading
    treats them as passed and the gating is silently lost, and doctor reports
    ``criterion:unknown_dependency``. A self-reference is a cycle. All of them
    are dropped here, with one review diagnostic per item (the same
    drop-and-flag discipline as edges and capability defaults), rather than
    failing the paid-for synthesis.
    """

    siblings = {str(criterion.get("id") or "") for criterion in criteria} - {""}
    removed: list[str] = []
    for criterion in criteria:
        own = str(criterion.get("id") or "")
        kept: list[str] = []
        for dep in criterion.get("depends_on") or []:
            dep = str(dep)
            if dep in siblings and dep != own:
                if dep not in kept:
                    kept.append(dep)
                continue
            if dep not in kept:
                removed.append(f"{own}: {dep}")
        criterion["depends_on"] = kept
    if not removed:
        return
    unique = list(dict.fromkeys(removed))
    dropped_diagnostics.append(
        {
            "gate": "criterion_dependency",
            "severity": "review",
            "entity_refs": [item_id, *sorted({entry.split(": ", 1)[1] for entry in unique})],
            "message": (
                f"item {item_id} dropped {len(unique)} criterion depends_on "
                f"entr{'y' if len(unique) == 1 else 'ies'} that name no sibling criterion "
                f"({'; '.join(unique)})"
            ),
            "suggested_action": (
                "a criterion's depends_on names only sibling criterion ids of the same item; "
                "re-author the dependency if a step really gates this one"
            ),
        }
    )


def _method_target_view(vault: LoadedVault, rows: list[dict[str, Any]]) -> Any:
    """The registry plus this batch's concepts, facets and learning objects, as
    :func:`learnloop.vault.required_method.method_targets` reads them."""

    from types import SimpleNamespace

    concepts: dict[str, Any] = dict(vault.concepts)
    facets: dict[str, Any] = dict(vault.evidence_facets)
    learning_objects: dict[str, Any] = dict(vault.learning_objects)
    for row in rows:
        payload = row.get("payload") or {}
        entity_id = str(payload.get("id") or row.get("target_entity_id") or "")
        if not entity_id:
            continue
        if row.get("item_type") == "concept":
            concepts[entity_id] = SimpleNamespace(
                type=payload.get("type"), title=payload.get("title") or entity_id,
                aliases=list(payload.get("aliases") or []),
            )
        elif row.get("item_type") == "facet":
            facets[entity_id] = SimpleNamespace(
                kind=payload.get("kind"), title=payload.get("title"), aliases=list(payload.get("aliases") or []),
            )
        elif row.get("item_type") == "learning_object":
            learning_objects[entity_id] = SimpleNamespace(id=entity_id, concept=payload.get("concept_id") or "")
    return SimpleNamespace(
        concepts=concepts, evidence_facets=facets, learning_objects=learning_objects,
        canonical_facet_id=vault.canonical_facet_id,
    )


def _row(item_type: str, entity_id: str, payload: dict[str, Any], depends_on: list[str],
         *, client_id: str, now: str, target_entity_id: str | None = None,
         target_entity_type: str | None = None) -> dict[str, Any]:
    return {
        "id": new_ulid(),
        "client_item_id": client_id,
        "item_type": item_type,
        "operation": "create",
        "target_entity_type": target_entity_type if target_entity_id else None,
        "target_entity_id": target_entity_id,
        "payload": payload,
        "source_ref_ids": [],
        "audit": None,
        "decision": "pending",
        "validation_status": "valid",
        "validation_errors": [],
        "depends_on_client_item_ids": list(depends_on),
        "dependency_status": "pending",
        "created_at": now,
        "updated_at": now,
    }


# --- concepts ---------------------------------------------------------------


def _register_concept_reference(st: _NormalizeState, concept_id: str, *values: str) -> None:
    for value in (concept_id, *values):
        key = snake_case(str(value or ""))
        if key:
            st.concept_reference_index.setdefault(key, set()).add(concept_id)


def _resolve_concept_reference(st: _NormalizeState, reference: str) -> tuple[str | None, str | None]:
    if reference in st.concept_ids:
        return st.concept_ids[reference], reference
    if reference in st.vault.concepts:
        return reference, None
    if reference in st.concept_client_for_id:
        return reference, st.concept_client_for_id[reference]
    matches = st.concept_reference_index.get(snake_case(reference), set())
    if len(matches) != 1:
        return None, None
    concept_id = next(iter(matches))
    return concept_id, st.concept_client_for_id.get(concept_id)


def _resolve_concept_references(
    st: _NormalizeState,
    *,
    learning_object_id: str,
    field_name: str,
    client_references: list[str],
    canonical_references: list[str],
) -> tuple[list[str], list[str]]:
    resolved: list[str] = []
    dependencies: list[str] = []
    unresolved: list[str] = []
    for reference in [*client_references, *canonical_references]:
        concept_id, dependency = _resolve_concept_reference(st, str(reference))
        if concept_id is None:
            unresolved.append(str(reference))
            continue
        if concept_id not in resolved:
            resolved.append(concept_id)
        if dependency is not None and dependency not in dependencies:
            dependencies.append(dependency)
    if unresolved:
        # Drop the unresolved links (a weaker model referencing concepts it
        # never declared) with a review diagnostic rather than failing the
        # whole paid synthesis — mirrors the concept-edge handling below.
        st.dropped_diagnostics.append(
            {
                "gate": "learning_object_concept",
                "severity": "review",
                "entity_refs": [learning_object_id, *unresolved],
                "message": (
                    f"learning object {learning_object_id!r} dropped "
                    f"{len(unresolved)} unresolved {field_name}: {', '.join(unresolved)}"
                ),
                "suggested_action": (
                    f"declare the referenced concept(s) or remove them from {field_name}"
                ),
            }
        )
    return resolved, dependencies


def _mint_concept(
    st: _NormalizeState, *, title: str, description: str, learning_object_id: str, detail: str
) -> tuple[str, str]:
    """Synthesize a concept so a learning object with no resolvable concept
    still lands (degraded fallback, §8.5). Registers it in every concept
    index so later references resolve, emits a review diagnostic, and returns
    ``(concept_id, client_key)`` — the client key is the LO row's dependency
    so the concept is created before it. Same-title mints fold into one
    concept downstream via the consolidation pass."""

    cid = st.unique(_slug("concept", title, new_ulid()[:8]))
    st.concept_ids[cid] = cid
    st.concept_client_for_id[cid] = cid
    _register_concept_reference(st, cid, title)
    payload = {
        "id": cid,
        "title": title or cid,
        "type": "concept",
        "description": description,
        "aliases": [],
    }
    st.rows.append(_row("concept", cid, payload, [], client_id=cid, now=st.now))
    st.gate_items.append(
        GateItem(client_item_id=cid, item_type="concept", entity_id=cid,
                 payload=payload, establishes_semantic=False)
    )
    st.dropped_diagnostics.append(
        {
            "gate": "learning_object_concept",
            "severity": "review",
            "entity_refs": [learning_object_id, cid],
            "message": (
                f"learning object {learning_object_id!r} had {detail}; "
                f"synthesized concept {cid!r} from its title"
            ),
            "suggested_action": "review the synthesized concept or merge it into an existing concept",
        }
    )
    return cid, cid


def _index_registry_concepts(st: _NormalizeState) -> None:
    """The registry's concepts resolve by id, title and alias, before any of the answer's are minted."""

    for existing_id, existing in st.vault.concepts.items():
        _register_concept_reference(st, existing_id, existing.title, *existing.aliases)


def _concepts(st: _NormalizeState) -> None:
    """The answer's concepts, with ``unique`` ids; an untitled one takes a ULID-prefix id."""

    # concepts
    for concept in getattr(st.synth, "concepts", []) or []:
        c = _dump(concept)
        cid = c.get("id") or _slug("concept", c.get("title", ""), new_ulid()[:8])
        cid = st.unique(str(cid))
        ckey = c.get("client_item_id") or cid
        st.concept_ids[ckey] = cid
        st.concept_client_for_id[cid] = ckey
        _register_concept_reference(st, cid, c.get("title") or "", *(c.get("aliases") or []))
        payload = {"id": cid, "title": c.get("title") or cid, "type": c.get("type") or "concept",
                   "description": c.get("description") or "", "aliases": c.get("aliases") or []}
        st.rows.append(_row("concept", cid, payload, [], client_id=ckey, now=st.now))
        st.gate_items.append(GateItem(client_item_id=ckey, item_type="concept",
                                   entity_id=cid, payload=payload, establishes_semantic=False))


# --- facets -----------------------------------------------------------------


def _facet_candidates(st: _NormalizeState) -> None:
    """Every facet as a candidate (payload, citations, support), none judged yet."""

    # facets — normalized first, then judged by the D2 mint gate (Meas D2, plan
    # item 5.4). The two passes are the point: D2's criterion is *relative* ("
    # separable from its nearest existing neighbours"), so no candidate can be
    # judged until every candidate in the batch has a payload to be compared with.
    st.candidate_facets: list[dict[str, Any]] = []
    for facet in getattr(st.synth, "facets", []) or []:
        f = _dump(facet)
        client = f.get("client_item_id") or ""
        fid = f.get("id") or _slug("facet", f.get("claim", ""), new_ulid()[:8])
        fid = st.unique(str(fid))
        fkey = client or fid
        concept_client = f.get("concept_client_id") or ""
        concept_id = st.concept_ids.get(concept_client) or f.get("concept_id") or ""
        gate_refs, yaml_refs, _spans = _span_refs(f.get("provenance", []), st.inputs, default_relation="primary")
        payload = {
            "id": fid,
            "concept_id": concept_id or None,
            "kind": f.get("kind") or "definition",
            "claim": f.get("claim") or "",
            "preconditions": f.get("preconditions") or [],
            "postconditions": f.get("postconditions") or [],
            "applicability": f.get("applicability") or [],
            "positive_examples": f.get("positive_examples") or [],
            "negative_examples": f.get("negative_examples") or [],
            "non_goals": f.get("non_goals") or [],
            "error_signatures": f.get("error_signatures") or [],
            "instructional_repairs": f.get("instructional_repairs") or [],
            "aliases": f.get("aliases") or [],
            # Pre-gate default; the D2 mint gate below decides the final status.
            "status": "reviewed",
            "provenance": {"origin": "sourceset_synthesis", "source_refs": yaml_refs},
        }
        support = _support_citations(gate_refs)
        st.candidate_facets.append(
            {
                "fkey": fkey,
                "fid": fid,
                "payload": payload,
                "deps": [concept_client] if concept_client and concept_client in st.concept_ids else [],
                "gate_refs": gate_refs,
                "support": support,
                # Citations that did not resolve: they support nothing, but a
                # reword of a registered facet, and a consolidation or attach
                # that joins this candidate's meaning to a survivor, is judged
                # with them, so one that names exam material by its span is
                # never "uncited" (and so never held for the owner's confirm,
                # nor joined as an uncited example; owner, 2026-10-13, and the
                # Codex review of the reword confirm, F1).
                "unresolved": _unresolved_citations(gate_refs),
                # What supports the facet's meaning, one entry per source of it:
                # the candidate itself, then each candidate whose meaning a
                # consolidation joined to it. The proposal carries them
                # (``meaning_support``) and the apply judges them again.
                "contributions": [facet_meaning.Contribution(fkey, tuple(support))],
            }
        )


def _facet_retirements(st: _NormalizeState) -> None:
    """Candidates facet identity retired leave the batch; an in-run survivor takes each retiree's meaning first."""

    # Facet identity (handoff §4): candidates the judge merged or absorbed are
    # not minted. In-run survivors take the union of their retirees first, so
    # D2 and the gates see the consolidated facet. A retiree's meaning joins
    # only through the facet-meaning chokepoint (Codex verification of F6): a
    # candidate only exam material supports joins as an alias, never as a
    # condition or an example of its survivor.
    st.retirements = dict(getattr(st.facet_identity_plan, "retirements", None) or {})
    if st.retirements:
        by_client = {str(candidate["fkey"]): candidate for candidate in st.candidate_facets}
        for fkey, retirement in sorted(st.retirements.items()):
            candidate = by_client.get(fkey)
            if candidate is None:
                continue
            if retirement.scope == "in_run":
                survivor = by_client.get(str(retirement.survivor_client or ""))
                if survivor is None or str(retirement.survivor_client) in st.retirements:
                    continue
                st.pre_union.setdefault(str(survivor["fkey"]), copy.deepcopy(survivor["payload"]))
                contribution = _joined_contribution(candidate)
                joined = facet_meaning.join_candidate(
                    survivor["payload"], candidate["payload"], survivor_id=str(survivor["fid"]),
                    action=retirement.action, absorb_as=retirement.absorb_as, contribution=contribution,
                    registered=False, resolver=st.inputs.resolver,
                )
                survivor["payload"] = joined.payload
                if joined.joined:
                    survivor["contributions"].append(contribution)
                else:
                    st.contract_notes.setdefault(str(survivor["fid"]), []).append(
                        f"{candidate['fid']} joined as an alias only: {joined.verdict.message}"
                    )
                    st.dropped_diagnostics.append(joined.verdict.diagnostic(
                        entity_refs=[str(survivor["fid"]), str(candidate["fid"])],
                        suggested_action="the candidate's meaning was not merged; corroborate it with an "
                                         "explanatory span to add it to the facet",
                    ))
            elif str(retirement.survivor_facet or "") not in st.vault.evidence_facets:
                continue
            st.retired_candidates[fkey] = candidate
        st.candidate_facets = [c for c in st.candidate_facets if str(c["fkey"]) not in st.retired_candidates]


def _mint_gate(st: _NormalizeState) -> None:
    """The D2 mint gate's verdict on each remaining candidate: mint a row, alias into a neighbour, or drop a reword."""

    registered_payloads = [
        facet.model_dump(mode="json") for facet in st.vault.evidence_facets.values()
    ]
    mint_report = judge_facet_mints(
        [candidate["payload"] for candidate in st.candidate_facets],
        registered=registered_payloads,
    )
    if st.nominator is not None:
        # T5 shadow: recorded beside the verdicts, never consulted by them.
        try:
            st.graph_nomination = annotate_mint_report(
                st.nominator, mint_report,
                [candidate["payload"] for candidate in st.candidate_facets],
                registered_payloads,
            )
        except Exception as exc:  # noqa: BLE001 - a shadow never fails a paid build
            st.graph_nomination = {"error": type(exc).__name__}
    for candidate, verdict in zip(st.candidate_facets, mint_report.verdicts, strict=True):
        fkey = str(candidate["fkey"])
        fid = str(candidate["fid"])
        payload = candidate["payload"]
        diagnostic = mint_diagnostic(verdict)
        if diagnostic is not None:
            st.dropped_diagnostics.append(diagnostic)
        registered_entry = st.vault.evidence_facets.get(fid) if verdict.disposition is not MintDisposition.ALIAS else None
        if registered_entry is not None:
            # A candidate carrying a registered facet's id rewrites that facet
            # (Codex verification of F6, finding 1). It is a reword, checked as
            # an update against the facet as it was now. With explanatory
            # support for every source of its meaning it applies; without it,
            # and not exam-only, it is kept and waits for the owner's confirm
            # at accept (owner, 2026-10-13); exam-only, it is dropped.
            before = registered_entry.model_dump(mode="json", exclude_none=False)
            own, *joined = candidate["contributions"]
            candidate["contributions"] = [
                facet_meaning.Contribution(own.label, (*own.citations, *candidate["unresolved"])), *joined,
            ]
            check = facet_meaning.check_meaning_write(
                fid, before=before, after=facet_meaning.overlay(before, payload), registered=True,
                contributions=candidate["contributions"], resolver=st.inputs.resolver,
                policy=facet_meaning.meaning_policy(st.vault.config),
            )
            if check.confirmable:
                st.dropped_diagnostics.append(check.diagnostic(entity_refs=[fid, fkey]))
            elif not check.allowed:
                # References resolve to the registered facet, as it is.
                st.facet_client_to_id[fkey] = fid
                st.dropped_diagnostics.append(check.diagnostic(
                    entity_refs=[fid, fkey],
                    suggested_action=(
                        f"kept registered facet {fid} as it is: a candidate carrying its id rewords it only "
                        "with an explanatory span from the selected units (or reword it in the Library)"
                    ),
                ))
                continue
        if verdict.disposition is MintDisposition.ALIAS:
            target = str(verdict.alias_of or "")
            # ALIAS-NOT-MINT: no facet row is emitted; every downstream reference
            # to this candidate (recipe components, criterion targets, LO scope)
            # resolves to the neighbour through `facet_client_to_id`, and the
            # candidate id is appended to the neighbour's `aliases` so the id keeps
            # resolving after the batch is applied (`loader._facet_aliases`).
            st.facet_client_to_id[fkey] = target
            # Dependency rewiring: an item that depended on this candidate's row
            # must now depend on whatever row materializes the TARGET, or on
            # nothing at all when the target is already in the registry. Left
            # pointing at the aliased candidate it would be a dangling requirement
            # (`_gate_dependency_closure`), because no row with that client id
            # exists any more.
            target_client = st.minted_client_by_id.get(target)
            if target_client is not None:
                st.facet_dep_client[fkey] = target_client
            if fid != target:
                st.alias_additions.setdefault(target, []).append(fid)
            continue
        payload["status"] = verdict.minted_status or payload["status"]
        st.facet_client_to_id[fkey] = fid
        st.facet_dep_client[fkey] = fkey
        st.minted_payload_by_id[fid] = payload
        st.minted_client_by_id[fid] = fkey
        st.facet_payloads.append(payload)
        deps = list(candidate["deps"])
        st.row_extras[fkey] = {"meaning_support": facet_meaning.support_entries(candidate["contributions"])}
        if registered_entry is not None:
            row = _row("facet", fid, payload, deps, client_id=fkey, now=st.now,
                       target_entity_id=fid, target_entity_type="facet")
            row["operation"] = "update"
            st.row_extras[fkey]["expected_target_hash"] = compute_target_hash(st.vault, "facet", fid)
            st.rows.append(row)
        else:
            st.rows.append(_row("facet", fid, payload, deps, client_id=fkey, now=st.now))
        st.gate_items.append(
            GateItem(
                client_item_id=fkey,
                item_type="facet",
                operation="update" if registered_entry is not None else "create",
                entity_id=fid,
                payload=payload,
                depends_on=deps,
                provenance=candidate["gate_refs"],
                establishes_semantic=True,
                reconciliation_intent="restructure_unlocked" if registered_entry is not None else None,
            )
        )


def _retired_references(st: _NormalizeState) -> None:
    """A retired candidate's references follow its survivor; its id becomes the survivor's alias where it is free."""

    # Facet identity: a retired candidate's references point at its survivor
    # (as D2's alias does) and its id becomes the survivor's alias.
    st.attach_unions: dict[str, list[tuple[dict[str, Any], Any, facet_meaning.Contribution]]] = {}
    st.alias_canonical: dict[str, str] = {}
    st.retired_targets: dict[str, tuple[str, str, Any, dict[str, Any]]] = {}
    for fkey, candidate in st.retired_candidates.items():
        retirement = st.retirements[fkey]
        fid = str(candidate["fid"])
        if retirement.scope == "in_run":
            target = st.facet_client_to_id.get(str(retirement.survivor_client))
            if not target:
                continue
        else:
            target = str(retirement.survivor_facet)
            st.attach_unions.setdefault(target, []).append(
                (candidate["payload"], retirement, _joined_contribution(candidate)),
            )
        if target in st.vault.evidence_facets:
            # A registered survivor gains the alias through its update row, so
            # whatever references the alias depends on that row.
            st.facet_dep_client[fkey] = f"facet_alias_{target}"
        elif st.facet_dep_client.get(str(retirement.survivor_client or "")) is not None:
            st.facet_dep_client[fkey] = st.facet_dep_client[str(retirement.survivor_client)]
        retired_payload = copy.deepcopy(candidate["payload"])
        retired_payload["id"] = fid
        st.retired_targets[fkey] = (fid, target, retirement, retired_payload)
        if fid == target or fid in st.vault.evidence_facets or fid in st.minted_payload_by_id:
            # The id is taken (or is the survivor): references point at the
            # survivor directly, as the D2 alias does.
            st.facet_client_to_id[fkey] = target
            continue
        # On-disk references keep the candidate's own id, which becomes the
        # survivor's alias (resolved at load): an undo that re-mints the
        # candidate needs no reference rewrite. Analysis sees the survivor.
        st.facet_client_to_id[fkey] = fid
        st.alias_canonical[fid] = target
        st.alias_additions.setdefault(target, []).append(fid)


def _register_aliases(st: _NormalizeState) -> None:
    """Add the collected aliases (and an attach's grown contract) to their targets: in place for a minted facet,
    through an `update` row for a registered one."""

    # Register the aliases. An in-batch target is edited in place (its create row
    # holds this very dict); an already-registered target earns an `update` row.
    for target in sorted(set(st.alias_additions) | set(st.attach_unions)):
        new_aliases = [
            alias
            for alias in sorted(dict.fromkeys(st.alias_additions.get(target, [])))
            # Never shadow a real facet id: `loader._facet_aliases` maps aliases
            # and ids into one namespace, so an alias equal to some facet's id
            # would silently reroute that facet's evidence.
            if alias not in st.minted_payload_by_id and alias not in st.vault.evidence_facets
        ]
        if not new_aliases and target not in st.attach_unions:
            continue
        in_batch = st.minted_payload_by_id.get(target)
        if in_batch is not None:
            in_batch["aliases"] = list(
                dict.fromkeys([*(in_batch.get("aliases") or []), *new_aliases])
            )
            continue
        registered_facet = st.vault.evidence_facets.get(target)
        if registered_facet is None:
            continue
        alias_payload: dict[str, Any] = {
            "id": target,
            "aliases": list(
                dict.fromkeys([*(registered_facet.aliases or []), *new_aliases])
            ),
        }
        if target in st.attach_unions:
            # Facet identity attach: a registered facet's contract only grows.
            # A merge is the alias alone; an absorb also adds the special case's
            # claim as a worked example. Claim, conditions, repairs, signatures
            # and status stay untouched (§10.2 additivity, verified by the gate).
            # A precondition narrows the contract, so it stays an alias only and
            # the action says so. Evidence on the registered facet changes
            # nothing here: facet identity locks were removed (owner,
            # 2026-10-12), and an example only annotates the contract.
            # A worked example is part of the facet's meaning, so it grows
            # only through the facet-meaning chokepoint (Codex verification of
            # F6): the absorbed candidate must cite an explanatory span.
            st.registered_before[target] = registered_facet.model_dump(mode="json")
            unioned = registered_facet.model_dump(mode="json")
            grown_by: list[facet_meaning.Contribution] = []
            for attached_payload, attach_retirement, contribution in st.attach_unions[target]:
                if attach_retirement.action != "absorb":
                    continue
                claim = str(attached_payload.get("claim") or "").strip()
                if attach_retirement.absorb_as == "precondition":
                    st.contract_notes.setdefault(target, []).append(
                        "kept as an alias only: a precondition would change the registered facet's contract"
                    )
                    continue
                if claim and claim not in (unioned.get("positive_examples") or []):
                    grown = {**unioned, "positive_examples": [*(unioned.get("positive_examples") or []), claim]}
                    check = facet_meaning.check_meaning_write(
                        target, before=unioned, after=grown, registered=True, contributions=[contribution],
                        resolver=st.inputs.resolver, policy=facet_meaning.meaning_policy(st.vault.config),
                    )
                    if not check.allowed:
                        st.contract_notes.setdefault(target, []).append(
                            f"{attached_payload.get('id') or contribution.label} kept as an alias only: "
                            f"{check.message}"
                        )
                        st.dropped_diagnostics.append(check.diagnostic(
                            entity_refs=[target, str(attached_payload.get("id") or contribution.label)],
                            suggested_action="the absorbed candidate's claim was not added as an example; "
                                             "corroborate it with an explanatory span to add it",
                        ))
                        continue
                    unioned = grown
                    grown_by.append(contribution)
            for field_name in ATTACH_GROWABLE_FIELDS:
                if unioned.get(field_name) != st.registered_before[target].get(field_name):
                    alias_payload[field_name] = unioned[field_name]
            if grown_by:
                st.row_extras[f"facet_alias_{target}"] = {"meaning_support": facet_meaning.support_entries(grown_by)}
        alias_row = _row(
            "facet",
            target,
            alias_payload,
            [],
            client_id=f"facet_alias_{target}",
            now=st.now,
        )
        alias_row["operation"] = "update"
        st.rows.append(alias_row)
        st.gate_items.append(
            GateItem(
                client_item_id=str(alias_row["client_item_id"]),
                item_type="facet",
                operation="update",
                entity_id=target,
                payload=alias_row["payload"],
                # An alias registration asserts no new semantic claim — it
                # WITHDRAWS one, by declining to mint a facet — and it is additive
                # in the §10.2 sense: it appends a synonym and rewrites no part of
                # the target's semantic contract. So it is neither a semantic
                # establishment (no provenance authority owed) nor destructive (no
                # identity lock to clear).
                establishes_semantic=False,
                destructive=False,
            )
        )


def _identity_actions(st: _NormalizeState) -> None:
    """The undoable facet-identity actions, from the rows the stages above wrote."""

    st.facet_identity_actions = _facet_identity_actions(
        st.retired_targets, pre_union=st.pre_union, minted_payload_by_id=st.minted_payload_by_id,
        registered_before=st.registered_before, rows=st.rows, vault=st.vault, aliased=set(st.alias_canonical),
        contract_notes=st.contract_notes,
    )


# --- learning objects, blueprints, practice items ---------------------------


def _learning_objects(st: _NormalizeState) -> None:
    """Learning objects, each anchored to a concept (minted from its title when the answer's reference is lost)."""

    # learning objects
    for lo in getattr(st.synth, "learning_objects", []) or []:
        obj = _dump(lo)
        client = obj.get("client_item_id") or ""
        oid = obj.get("id") or _slug("lo", obj.get("title", ""), new_ulid()[:8])
        oid = st.unique(str(oid))
        lokey = client or oid
        st.lo_client_to_id[lokey] = oid
        concept_client = str(obj.get("concept_client_id") or "")
        concept_reference = concept_client or str(obj.get("concept_id") or "")
        concept_id, concept_dependency = _resolve_concept_reference(st, concept_reference)
        if concept_id is None:
            # Tolerate a model that authored the learning object but left its
            # concept anchor empty or dangling (common on weaker providers):
            # mint a concept from the LO's title and continue rather than failing
            # the whole build. The reported failure mode was an empty anchor
            # ("(missing)"); a non-empty-but-unresolvable reference is minted the
            # same way, both flagged for review.
            concept_id, concept_dependency = _mint_concept(
                st,
                title=obj.get("title") or "",
                description=obj.get("summary") or "",
                learning_object_id=oid,
                detail=(
                    f"an unresolvable concept reference {concept_reference!r}"
                    if concept_reference
                    else "no concept anchor"
                ),
            )
        prerequisites, prerequisite_dependencies = _resolve_concept_references(
            st,
            learning_object_id=oid,
            field_name="prerequisites",
            client_references=list(obj.get("prerequisite_concept_client_ids") or []),
            canonical_references=list(obj.get("prerequisites") or []),
        )
        confusables, confusable_dependencies = _resolve_concept_references(
            st,
            learning_object_id=oid,
            field_name="confusables",
            client_references=list(obj.get("confusable_concept_client_ids") or []),
            canonical_references=list(obj.get("confusables") or []),
        )
        gate_refs, yaml_refs, _spans = _span_refs(obj.get("provenance", []), st.inputs, default_relation="primary")
        payload = {
            "id": oid,
            "concept_id": concept_id or None,
            "title": obj.get("title") or oid,
            "summary": obj.get("summary") or "",
            "subjects": [st.subject_id],
            "knowledge_type": obj.get("knowledge_type") or "concept",
            "prerequisites": prerequisites,
            "confusables": confusables,
            "provenance": {"origin": "codex_proposal", "source_refs": yaml_refs},
        }
        deps = list(
            dict.fromkeys(
                dependency
                for dependency in [concept_dependency, *prerequisite_dependencies, *confusable_dependencies]
                if dependency
            )
        )
        if concept_id:
            st.lo_relation_seeds.append((oid, concept_id, list(prerequisites), list(confusables)))
        st.rows.append(_row("learning_object", oid, payload, deps, client_id=lokey, now=st.now))
        st.gate_items.append(
            GateItem(
                client_item_id=lokey,
                item_type="learning_object",
                entity_id=oid,
                payload=payload,
                depends_on=deps,
                provenance=gate_refs,
                establishes_semantic=True,
            )
        )


def _blueprints(st: _NormalizeState) -> None:
    """Task blueprints, merged onto their learning object, their recipe components resolved to facet ids."""

    # blueprints (task_blueprint items merged onto their LO)
    for blueprint in getattr(st.synth, "blueprints", []) or []:
        bp = _dump(blueprint)
        client = bp.get("client_item_id") or ""
        bid = bp.get("id") or _slug("bp", "", new_ulid()[:8])
        bid = st.unique(str(bid))
        lo_client = bp.get("learning_object_client_id") or ""
        lo_id = st.lo_client_to_id.get(lo_client) or bp.get("learning_object_id") or ""
        recipes_payload: list[dict[str, Any]] = []
        gate_recipes: list[dict[str, Any]] = []
        facet_deps: list[str] = []
        for recipe in bp.get("recipes", []) or []:
            r = recipe if isinstance(recipe, dict) else recipe.model_dump()
            comps_out: list[dict[str, Any]] = []
            flat_facets: list[str] = []
            for slot in ("all_of", "any_of"):
                for comp in r.get(slot) or []:
                    cm = comp if isinstance(comp, dict) else comp.model_dump()
                    fclient = cm.get("facet_client_id") or ""
                    facet_id = st.facet_client_to_id.get(fclient) or cm.get("facet") or ""
                    # D3's discipline extended to ordinary components: the schema
                    # does not default `capability`, so an unchosen capability is
                    # observable here. An `all_of`/`any_of`
                    # component always observes *something*, so the honest remedy
                    # is default-and-flag rather than drop — but a defaulted
                    # capability is still a contract cell nobody authored, and it
                    # must surface as a review diagnostic, never silently.
                    declared = str(cm.get("capability") or "").strip()
                    capability = declared or "retrieval"
                    if not declared:
                        st.dropped_diagnostics.append(
                            {
                                "gate": "recipe_component_capability",
                                "severity": "review",
                                "entity_refs": [lo_id, facet_id],
                                "message": (
                                    f"recipe {r.get('id') or '<unnamed>'} {slot} component for "
                                    f"{facet_id or '<unresolved facet>'} declared no capability; "
                                    "defaulted to `retrieval`"
                                ),
                                "suggested_action": (
                                    "confirm `retrieval` is the capability this component is "
                                    "actually demonstrated at, or re-author it explicitly"
                                ),
                            }
                        )
                    comps_out.append({"facet": facet_id, "capability": capability, "modality": cm.get("modality") or "hard", "_slot": slot})
                    flat_facets.append(st.alias_canonical.get(facet_id, facet_id))
                    st.recipe_components.append({"facet": st.alias_canonical.get(facet_id, facet_id), "capability": capability})
                    # D2: depend on the row that materializes the facet, which the
                    # mint gate may have redirected to an earlier candidate (alias).
                    fdep = st.facet_dep_client.get(fclient)
                    if fdep is not None and fdep not in facet_deps:
                        facet_deps.append(fdep)
            integration = r.get("integration")
            integ_out = None
            if integration:
                im = integration if isinstance(integration, dict) else integration.model_dump()
                fclient = im.get("facet_client_id") or ""
                facet_id = st.facet_client_to_id.get(fclient) or im.get("facet") or ""
                # KM §7.2: the integration component is OPTIONAL and is authored only
                # when component competence can coexist with a repeatable, observable,
                # separately repairable assembly failure. An undeclared capability is
                # therefore an authoring gap, not a licence to mint `coordination` --
                # the previous `or "coordination"` fallback silently stamped the one
                # capability the default rung trajectory deliberately refuses to author
                # (documentation.md: "the built-in trajectory deliberately stops before
                # ... coordination"), so every LO was born with a certification
                # requirement generation is designed never to satisfy. Drop instead:
                # absence of an integration component is the honest default, and
                # `lo_certification` only demands integration evidence when one exists.
                declared_capability = str(im.get("capability") or "").strip()
                if not declared_capability:
                    st.dropped_diagnostics.append(
                        {
                            "gate": "blueprint_integration",
                            "severity": "review",
                            "entity_refs": [lo_id, facet_id],
                            "message": (
                                f"recipe {r.get('id') or '<unnamed>'} declared an integration "
                                "component with no capability; dropped rather than defaulted"
                            ),
                            "suggested_action": (
                                "re-author with an explicit capability if this recipe has a real "
                                "assembly failure mode, otherwise leave it absent"
                            ),
                        }
                    )
                else:
                    if declared_capability == "coordination":
                        # Legitimate, but it is an obligation: nothing certifies this LO
                        # until a whole-task instrument exists at this rung, and the
                        # default generation trajectory will not author one.
                        st.dropped_diagnostics.append(
                            {
                                "gate": "blueprint_integration",
                                "severity": "review",
                                "entity_refs": [lo_id, facet_id],
                                "message": (
                                    f"recipe {r.get('id') or '<unnamed>'} requires integration at "
                                    "`coordination`: this LO cannot be certified until a whole-task "
                                    "instrument is authored at that rung"
                                ),
                                "suggested_action": (
                                    "confirm a real assembly failure mode exists, or lower the "
                                    "integration capability to one the item pool can observe"
                                ),
                            }
                        )
                    integ_out = {"facet": facet_id, "capability": declared_capability, "modality": "hard"}
                    flat_facets.append(st.alias_canonical.get(facet_id, facet_id))
                    st.recipe_components.append({"facet": st.alias_canonical.get(facet_id, facet_id), "capability": declared_capability})
                    # D2: depend on the row that materializes the facet, which the
                    # mint gate may have redirected to an earlier candidate (alias).
                    fdep = st.facet_dep_client.get(fclient)
                    if fdep is not None and fdep not in facet_deps:
                        facet_deps.append(fdep)
            recipe_row = {
                "id": r.get("id") or f"recipe_{new_ulid()[:8]}",
                "composition": r.get("composition") or "conjunctive",
                "all_of": [{"facet": c["facet"], "capability": c["capability"], "modality": c["modality"]} for c in comps_out if c["_slot"] == "all_of"],
                "any_of": [{"facet": c["facet"], "capability": c["capability"], "modality": c["modality"]} for c in comps_out if c["_slot"] == "any_of"],
            }
            if integ_out:
                recipe_row["integration"] = integ_out
            recipes_payload.append(recipe_row)
            gate_recipes.append({**recipe_row, "facets": flat_facets})
        payload = {"id": bid, "learning_object_id": lo_id, "weight": bp.get("weight", 1.0), "recipes": recipes_payload}
        deps = ([lo_client] if lo_client in st.lo_client_to_id else []) + facet_deps
        st.rows.append(_row("task_blueprint", bid, payload, deps, client_id=client or bid, now=st.now,
                         target_entity_id=lo_id, target_entity_type="learning_object"))
        st.gate_items.append(
            GateItem(
                client_item_id=client or bid,
                item_type="task_blueprint",
                entity_id=bid,
                payload={"blueprints": [{"id": bid, "weight": bp.get("weight", 1.0), "recipes": gate_recipes}]},
                depends_on=deps,
                establishes_semantic=False,
            )
        )


def _practice_items(st: _NormalizeState) -> None:
    """Practice items and their rubric criteria; under items-off the model's items are dropped, not trusted."""

    # practice items (+ rubric criteria). Under items-off ("as_you_read"
    # bootstrap) any model-emitted items are dropped by a deterministic guard —
    # never trust prompt compliance — and counted into the diagnostics.
    emitted_items = list(getattr(st.synth, "practice_items", []) or [])
    if st.items_off and emitted_items:
        st.dropped_diagnostics.append(
            {
                "gate": "items_off",
                "severity": "review",
                "entity_refs": [],
                "message": (
                    f"dropped {len(emitted_items)} model-emitted practice item(s): "
                    "this build authors items as-you-read"
                ),
                "suggested_action": "none — items accrue from reading progress",
            }
        )
        emitted_items = []
    for item in emitted_items:
        pi = _dump(item)
        client = pi.get("client_item_id") or ""
        pid = pi.get("id") or _slug("pi", pi.get("prompt", "")[:24], new_ulid()[:8])
        pid = st.unique(str(pid))
        lo_client = pi.get("learning_object_client_id") or ""
        lo_id = st.lo_client_to_id.get(lo_client) or pi.get("learning_object_id") or ""
        evidence_facets: list[str] = []
        for fc in pi.get("evidence_facet_client_ids") or []:
            evidence_facets.append(st.facet_client_to_id.get(fc, fc))
        for f in pi.get("evidence_facets") or []:
            if f not in evidence_facets:
                evidence_facets.append(f)
        criteria_payload: list[dict[str, Any]] = []
        for criterion in pi.get("criteria", []) or []:
            c = criterion if isinstance(criterion, dict) else criterion.model_dump()
            targets_out: list[dict[str, Any]] = []
            for target in c.get("targets", []) or []:
                t = target if isinstance(target, dict) else target.model_dump()
                fclient = t.get("facet_client_id") or ""
                facet_id = st.facet_client_to_id.get(fclient) or t.get("facet") or ""
                # Same default-and-flag discipline as recipe components: an
                # authored target wins verbatim downstream (A1), so a silently
                # defaulted rung would file evidence into a cell nobody chose.
                declared_target_capability = str(t.get("capability") or "").strip()
                capability = declared_target_capability or "retrieval"
                if not declared_target_capability:
                    st.dropped_diagnostics.append(
                        {
                            "gate": "criterion_target_capability",
                            "severity": "review",
                            "entity_refs": [pid, facet_id],
                            "message": (
                                f"criterion target for {facet_id or '<unresolved facet>'} on "
                                f"item {pid} declared no capability; defaulted to `retrieval`"
                            ),
                            "suggested_action": (
                                "state the capability the criterion actually observes"
                            ),
                        }
                    )
                role = t.get("role") or "primary"
                targets_out.append({"facet": facet_id, "capability": capability, "role": role})
                st.criterion_targets.append(
                    {
                        "criterion_id": c.get("id") or "",
                        "correlation_group": c.get("correlation_group") or "",
                        "facet": st.alias_canonical.get(facet_id, facet_id),
                        "capability": capability,
                        "role": role,
                    }
                )
            criteria_payload.append(
                {
                    "id": c.get("id") or f"crit_{new_ulid()[:6]}",
                    "points": c.get("points", 1.0),
                    "description": c.get("description") or "",
                    "tier": c.get("tier") or "core",
                    "targets": targets_out,
                    "depends_on": [str(dep) for dep in c.get("depends_on") or [] if dep],
                    "recipe_ids": c.get("recipe_ids") or [],
                    "correlation_group": c.get("correlation_group") or None,
                }
            )
        _keep_sibling_criterion_dependencies(pid, criteria_payload, st.dropped_diagnostics)
        gate_refs, yaml_refs, span_ids = _span_refs(pi.get("provenance", []), st.inputs, default_relation="exercise")
        fp = pi.get("evidence_fingerprint") or {}
        fp = fp if isinstance(fp, dict) else fp.model_dump()
        rubric = {"max_points": 4, "criteria": criteria_payload, "fatal_errors": []}
        payload = {
            "id": pid,
            "learning_object_id": lo_id,
            "practice_mode": pi.get("practice_mode") or "retrieval",
            "prompt": pi.get("prompt") or "",
            "expected_answer": pi.get("expected_answer") or "",
            "evidence_facets": evidence_facets,
            "grading_rubric": rubric if criteria_payload else None,
            "retrieval_demand": pi.get("retrieval_demand", 0.5),
            "transfer_distance": pi.get("transfer_distance", 0.0),
            "scaffold_level": pi.get("scaffold_level", 0.0),
            "surface_family": pi.get("surface_family") or "source_form",
            "repair_targets": evidence_facets or None,
            "evidence_fingerprint": {k: v for k, v in fp.items() if v},
            "provenance": {"origin": "codex_proposal", "source_refs": yaml_refs},
        }
        required = pi.get("required_method")
        if isinstance(required, dict) and str(required.get("name") or "").strip():
            # Method-explicit items (owner rule 2026-10-13): kept only on a
            # method target (this batch's concepts and facets plus the
            # registry), linked to it; the prompt is stored as generated and
            # the instruction rendered from the field (round 3; the prompt's
            # phrasing is never read to decide, the advisory heuristic only
            # flags it for review).
            payload["required_method"] = dict(required)
            notes = normalize_required_method(
                payload,
                method_targets(
                    _method_target_view(st.vault, st.rows), learning_object_id=lo_id, facet_ids=evidence_facets,
                ),
            )
            kept = payload.get("required_method")
            flag = advisory_statement_flag(payload.get("prompt"), kept["name"]) if kept else None
            if flag is not None:
                st.dropped_diagnostics.append(
                    {
                        "gate": "required_method",
                        "severity": "review",
                        "entity_refs": [pid],
                        "message": (f"item {pid}: required_method:statement_may_disagree ({flag}; advisory, "
                                    "grading reads the field)"),
                        "suggested_action": (
                            "make the prompt agree with 'Use {method} in your answer.', or drop the requirement"
                        ),
                    }
                )
            if any(note.startswith("required_method:dropped") for note in notes):
                st.dropped_diagnostics.append(
                    {
                        "gate": "required_method",
                        "severity": "review",
                        "entity_refs": [pid],
                        "message": f"item {pid}: {', '.join(notes)}",
                        "suggested_action": (
                            "criteria name facts; a method is required only when the item's target is that method"
                        ),
                    }
                )
        deps = ([lo_client] if lo_client in st.lo_client_to_id else [])
        for fc in pi.get("evidence_facet_client_ids") or []:
            fdep = st.facet_dep_client.get(fc)
            if fdep is not None and fdep not in deps:
                deps.append(fdep)
        extra = list(pi.get("depends_on_client_item_ids") or [])
        for dep in extra:
            if dep not in deps:
                deps.append(dep)
        st.rows.append(_row("practice_item", pid, payload, deps, client_id=client or pid, now=st.now))
        st.gate_items.append(
            GateItem(
                client_item_id=client or pid,
                item_type="practice_item",
                entity_id=pid,
                payload={"criteria": criteria_payload, "grading_rubric": rubric},
                depends_on=deps,
                provenance=gate_refs,
                is_teaching_or_practice=True,
                embedded_span_ids=span_ids,
            )
        )


# --- concept edges ----------------------------------------------------------


def _reaches(adjacency: dict[str, set[str]], start: str, goal: str) -> bool:
    stack, seen = [start], set()
    while stack:
        node = stack.pop()
        if node == goal:
            return True
        if node in seen:
            continue
        seen.add(node)
        stack.extend(adjacency.get(node, ()))
    return False


def _resolve_endpoint(st: _NormalizeState, reference: Any) -> str | None:
    reference = str(reference or "")
    if not reference:
        return None
    if reference in st.concept_ids:
        return st.concept_ids[reference]
    if reference in st.concept_client_for_id or reference in st.vault.concepts:
        return reference
    return None


def _edge_review(st: _NormalizeState, message: str, refs: list[str], action: str) -> None:
    st.edge_diagnostics.append(
        {
            "gate": "concept_graph",
            "severity": "review",
            "message": message,
            "entity_refs": [ref for ref in refs if ref],
            "suggested_action": action,
        }
    )


def _add_concept_edge(
    st: _NormalizeState, source_ref: Any, target_ref: Any, relation_type: str, *, rationale: str, strength: float = 1.0
) -> None:
    source = _resolve_endpoint(st, source_ref)
    target = _resolve_endpoint(st, target_ref)
    if source is None or target is None:
        _edge_review(
            st,
            f"concept relation {source_ref!r} -> {target_ref!r} ({relation_type}) has an unresolvable endpoint",
            [str(source_ref or ""), str(target_ref or "")],
            "create the concept or drop the relation",
        )
        return
    if source == target:
        return
    signature = (source, target, relation_type)
    if signature in st.edge_signatures or signature in st.existing_edges:
        return
    if relation_type == "confusable_with" and (
        (target, source, relation_type) in st.edge_signatures
        or (target, source, relation_type) in st.existing_edges
    ):
        return
    if relation_type == "part_of":
        if source in st.part_of_parent:
            _edge_review(
                st,
                f"concept {source} already has part_of parent {st.part_of_parent[source]}; dropped extra parent {target}",
                [source, target],
                "keep exactly one part_of parent per concept",
            )
            return
        parent_adjacency = {child: {parent} for child, parent in st.part_of_parent.items()}
        if _reaches(parent_adjacency, target, source):
            _edge_review(
                st,
                f"part_of relation {source} -> {target} would close a hierarchy cycle; dropped",
                [source, target],
                "restructure the part_of hierarchy",
            )
            return
    if relation_type == "prerequisite" and _reaches(st.prereq_adjacency, target, source):
        _edge_review(
            st,
            f"prerequisite relation {source} -> {target} would close a cycle; dropped",
            [source, target],
            "resolve the prerequisite direction",
        )
        return
    st.edge_signatures.add(signature)
    if relation_type == "prerequisite":
        st.prereq_adjacency.setdefault(source, set()).add(target)
    elif relation_type == "part_of":
        st.part_of_parent[source] = target
    edge_id = st.unique(f"edge_{relation_type}__{snake_case(source)[:40]}__{snake_case(target)[:40]}")
    payload = {
        "id": edge_id,
        "source_concept_id": source,
        "target_concept_id": target,
        "relation_type": relation_type,
        "strength": strength,
        "rationale": rationale or None,
    }
    deps = [
        client
        for client in (st.concept_client_for_id.get(source), st.concept_client_for_id.get(target))
        if client
    ]
    st.rows.append(_row("concept_edge", edge_id, payload, deps, client_id=edge_id, now=st.now))
    st.gate_items.append(
        GateItem(
            client_item_id=edge_id,
            item_type="concept_edge",
            entity_id=edge_id,
            payload={"source": source, "target": target, "relation_type": relation_type},
            depends_on=deps,
            establishes_semantic=False,
        )
    )


def _concept_edges(st: _NormalizeState) -> None:
    """The model's explicit relations, then the floor derived from the learning objects' prerequisites and confusables."""

    # concept edges — explicit relations (shard-local + graph-structuring pass)
    # first, then the deterministic floor derived from LO prerequisites and
    # confusables. Everything validates against this proposal's concepts plus
    # the registry; invalid or cycle-forming edges drop with review diagnostics
    # rather than failing the paid-for synthesis.
    st.existing_edges = {(edge.source, edge.target, edge.relation_type) for edge in st.vault.edges}
    for edge_source, edge_target, edge_type in st.existing_edges:
        if edge_type == "prerequisite":
            st.prereq_adjacency.setdefault(edge_source, set()).add(edge_target)
        elif edge_type == "part_of":
            st.part_of_parent.setdefault(edge_source, edge_target)


    for relation in getattr(st.synth, "concept_relations", []) or []:
        r = _dump(relation)
        _add_concept_edge(
            st,
            r.get("source"),
            r.get("target"),
            str(r.get("relation_type") or "related"),
            rationale=str(r.get("rationale") or "authored during synthesis"),
            strength=float(r.get("strength", 1.0) or 1.0),
        )
    for lo_id, lo_concept_id, prerequisite_ids, confusable_ids in st.lo_relation_seeds:
        for prerequisite_id in prerequisite_ids:
            _add_concept_edge(
                st,
                prerequisite_id, lo_concept_id, "prerequisite",
                rationale=f"derived from learning object {lo_id} prerequisites",
            )
        for confusable_id in confusable_ids:
            _add_concept_edge(
                st,
                lo_concept_id, confusable_id, "confusable_with",
                rationale=f"derived from learning object {lo_id} confusables",
            )


# --- the result -------------------------------------------------------------


def _finalize(st: _NormalizeState) -> Normalized:
    conflict_candidates = [str(c.get("entity_client_id") or c.get("statement") or "")
                           for c in (_dump(x) for x in getattr(st.synth, "conflicts", []) or [])]
    dispositions = set(getattr(st.synth, "non_conflict_dispositions", []) or [])

    # Proposal bookkeeping rides on the facet rows only (the gate items and the
    # identity actions keep the facet as facets.yaml will hold it).
    for row in st.rows:
        extras = st.row_extras.get(str(row.get("client_item_id") or ""))
        if row.get("item_type") == "facet" and extras:
            row["payload"] = {**row["payload"], **extras}

    return Normalized(
        rows=st.rows,
        gate_items=st.gate_items,
        conflict_candidates=[c for c in conflict_candidates if c],
        non_conflict_dispositions=dispositions,
        facet_payloads=st.facet_payloads,
        criterion_targets=st.criterion_targets,
        recipe_components=st.recipe_components,
        facet_ids=list(dict.fromkeys(st.alias_canonical.get(fid, fid) for fid in st.facet_client_to_id.values())),
        edge_diagnostics=st.edge_diagnostics + st.dropped_diagnostics,
        graph_nomination=st.graph_nomination,
        facet_identity_actions=st.facet_identity_actions,
    )


def normalize(
    synth: Any,
    inputs: Any,
    vault: LoadedVault,
    now: str,
    *,
    subject_id: str,
    items_off: bool = False,
    nominator: Any = None,
    facet_identity_plan: Any = None,
) -> Normalized:
    """The proposal rows, gate items and diagnostics of one synthesis answer; the module docstring gives the order."""

    st = _NormalizeState(
        synth=synth, inputs=inputs, vault=vault, now=now, subject_id=subject_id, items_off=items_off,
        nominator=nominator, facet_identity_plan=facet_identity_plan,
    )
    _index_registry_concepts(st)
    _concepts(st)
    _facet_candidates(st)
    _facet_retirements(st)
    _mint_gate(st)
    _retired_references(st)
    _register_aliases(st)
    _identity_actions(st)
    _learning_objects(st)
    _blueprints(st)
    _practice_items(st)
    _concept_edges(st)
    return _finalize(st)
