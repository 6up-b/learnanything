"""Applied facet-identity actions, the vault-level merge, rewords, and one-tap undo.

An action is one judged set: a survivor facet plus the facets merged or
absorbed into it; or (migration 188) a ``reword``: one facet whose meaning a
proposal apply changed, the row keeping the wording it replaced. Facet
identity locks no longer exist (owner, 2026-10-12): no merge, absorb or
reword is refused or demoted because a facet carries evidence; the action
records which facets did (``detail.evidence``) as provenance. Every reference to a retired facet (recipe components,
criterion targets, evidence facets, goals, database rows) keeps its id on
disk: the retired id becomes an alias of the survivor, and the loader and the
projections resolve aliases (``vault.facet_aliases``, then ``facet_merges``).
So an action changes only ``facets.yaml`` (and, for registered facets, the
``facet_merges`` map), and it records exactly what it replaced:

* the ``facets.yaml`` entries before and after (the survivor's entry, and
  each retired facet's entry, which the action removed, with its position);
* the ``facet_merges`` rows it inserted (vault scope only: a retired facet
  that already existed may carry evidence, and that map is how projections
  re-key it).

Three scopes share the record:

* ``vault``: two registered facets (``learnloop facets dedupe``), applied
  here by :func:`merge_registered_facets`;
* ``in_run``: candidates of one synthesis or append run, merged before the
  proposal existed; the proposal carries the survivor;
* ``attach``: a candidate aliased or absorbed into a registered facet.

A ``reword`` (scope ``vault``, origin ``proposal``) has no retired facets: its
undo restores the facet's previous entry, as a merge's undo restores the
survivor's.

In-run and attach actions are recorded ``proposed`` with their proposal; they
are undoable once the proposal is applied (the vault then shows exactly what
they wrote). An undo refuses when the survivor's entry changed since (a later
action or an edit), naming the later action, rather than overwrite it.

Crash safety (review F4). A vault merge writes its intent first: the action
row (``applying``) and its ``facet_merges`` rows commit in one transaction
before ``facets.yaml`` is replaced (a staged, fsynced temp file and an atomic
rename); the row becomes ``applied`` only after the derived state is
refreshed. An undo records ``undoing`` (with the owner's verdicts) before it
restores the file. :func:`recover_interrupted_actions` finishes either from
whichever side of the file write it stopped on; every merge, undo and
dedupe run calls it under the vault lock, the sidecar calls it when it opens
the vault, and ``doctor --fix-state`` does too. Until an action settles, its
``facet_merges`` rows are left out of the merge map
(``Repository.facet_merge_map``), so facets.yaml is the authority: a facet it
still lists keeps its own evidence, and a written merge already resolves
through the alias (review F12).

What an undo restores. Evidence resolved at projection time (every attempt's
criterion targets, recipes and evidence facets, which keep the retired id on
disk) returns to the restored facet when the affected learning objects are
re-folded. Rows written at grading time while the merge stood (exercised
facets, A5 notes, error events) carry the survivor's id and stay with the
survivor after an undo (review F9); the undo result says so.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.content.facet_identity.views import union_payload
from learnloop.db.repositories import Repository
from learnloop.db.stores import facet_identity as store
from learnloop.ids import new_ulid
from learnloop.substrate.replay import record_content_recalibration
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import EvidenceFacet, EvidenceFacetsFile, LoadedVault, learning_object_facet_union
from learnloop.vault.paths import VaultPaths
from learnloop.vault.facet_fingerprint import semantic_fingerprint
from learnloop.vault.yaml_io import read_yaml, yaml_from_string, yaml_to_string

#: Lifecycle of an action row (migration 183). ``applying`` and ``undoing``
#: are write-ahead intents that :func:`recover_interrupted_actions` completes.
IN_FLIGHT = ("applying", "undoing")
#: What an undo cannot move back (review F9): shown with every undo.
UNDO_LIMITS = (
    "rows written while the merge stood (exercised facets, A5 notes, error events) keep the "
    "survivor's id and stay with it"
)

class FacetIdentityActionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


# --- the ledger ---------------------------------------------------------------


def insert_action(connection: Any, record: Mapping[str, Any]) -> str:
    return store.insert_action(connection, {**dict(record), "id": record.get("id") or new_ulid()},
                               created_at=utc_now_iso())


def action_by_id(repository: Repository, action_id: str) -> dict[str, Any] | None:
    with repository.connection() as connection:
        return store.action_by_id(connection, action_id)


def list_actions(
    repository: Repository, *, run_id: str | None = None, status: str | None = None, limit: int | None = 200,
) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        return store.list_actions(connection, run_id=run_id, status=status, limit=limit)


# --- facets.yaml ----------------------------------------------------------------


def normalized_entry(entry: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """An entry as ``facets.yaml`` stores it, minus the recomputed fingerprint."""

    if entry is None:
        return None
    dumped = EvidenceFacet.model_validate(dict(entry)).model_dump(mode="json", exclude_none=False)
    dumped.pop("semantic_fingerprint", None)
    return dumped


def stored_entry(entry: Mapping[str, Any]) -> dict[str, Any]:
    """The entry to write: validated, with its deterministic fingerprint."""

    validated = EvidenceFacet.model_validate(dict(entry))
    dumped = validated.model_dump(mode="json", exclude_none=False)
    dumped["semantic_fingerprint"] = semantic_fingerprint(validated)
    return dumped


def _facets_document(paths: VaultPaths) -> dict[str, Any]:
    data = read_yaml(paths.facets_path) if paths.facets_path.exists() else {}
    if not isinstance(data, dict):
        raise FacetIdentityActionError("invalid_registry", "facets.yaml must contain a mapping")
    data.setdefault("schema_version", 2)
    facets = data.setdefault("facets", [])
    if not isinstance(facets, list):
        raise FacetIdentityActionError("invalid_registry", "facets.yaml must contain a facets list")
    return data


def _index(facets: Sequence[Any], facet_id: str) -> int | None:
    for index, entry in enumerate(facets):
        if isinstance(entry, Mapping) and str(entry.get("id") or "") == facet_id:
            return index
    return None


def _write_facets(paths: VaultPaths, document: Mapping[str, Any]) -> None:
    """Replace facets.yaml atomically (staged, fsynced temp file and rename)."""

    _write_registry_text(paths, yaml_to_string(dict(document)))


def _write_registry_text(paths: VaultPaths, text: str) -> None:
    """Replace facets.yaml with ``text`` atomically (staged, fsynced temp file and rename)."""

    from learnloop.content.proposals.apply_protocol import materialize_targets

    materialize_targets(paths.root, [{
        "rel_path": str(paths.facets_path.relative_to(paths.root)),
        "post_content": text,
        "post_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }])


def _record_parts(record: Mapping[str, Any]) -> tuple[str, list[str], dict[str, Any], dict[str, Any], dict[str, Any]]:
    survivor = str(record["survivor_facet_id"])
    retired = [str(facet_id) for facet_id in record.get("retired_facet_ids") or []]
    before = dict((record.get("before") or {}).get("facets") or {})
    order = dict((record.get("before") or {}).get("order") or {})
    after = dict((record.get("after") or {}).get("facets") or {})
    return survivor, retired, before, order, after


def file_state(record: Mapping[str, Any], facets: Sequence[Any]) -> str:
    """Which side of an action facets.yaml shows: ``after``, ``before`` or ``neither``."""

    survivor, retired, before, _order, after = _record_parts(record)
    index = _index(facets, survivor)
    current = normalized_entry(facets[index]) if index is not None else None
    present = {facet_id for facet_id in retired if _index(facets, facet_id) is not None}
    if current is not None and current == normalized_entry(after.get(survivor)) and not present:
        return "after"
    survivor_before = before.get(survivor)
    if (
        current is not None
        and (survivor_before is None or current == normalized_entry(survivor_before))
        and present == set(retired)
    ):
        return "before"
    return "neither"


def _applied_document(document: dict[str, Any], record: Mapping[str, Any]) -> dict[str, Any]:
    """``document`` with the action applied (survivor replaced, retirees removed)."""

    survivor, retired, _before, _order, after = _record_parts(record)
    facets = list(document["facets"])
    index = _index(facets, survivor)
    if index is not None and after.get(survivor) is not None:
        facets[index] = stored_entry(after[survivor])
    gone = set(retired)
    document["facets"] = [entry for entry in facets
                          if not (isinstance(entry, Mapping) and str(entry.get("id") or "") in gone)]
    return document


def _restored_document(document: dict[str, Any], record: Mapping[str, Any]) -> dict[str, Any]:
    """``document`` with the action undone (survivor and retirees as before)."""

    survivor, retired, before, order, _after = _record_parts(record)
    facets = list(document["facets"])
    index = _index(facets, survivor)
    if index is not None and before.get(survivor):
        facets[index] = stored_entry(before[survivor])
    for facet_id in sorted(retired, key=lambda key: int(order.get(key, len(facets) + 1))):
        entry = before.get(facet_id)
        if not entry or _index(facets, facet_id) is not None:
            continue
        position = order.get(facet_id)
        restored = stored_entry(entry)
        if isinstance(position, int) and 0 <= position <= len(facets):
            facets.insert(position, restored)
        else:
            survivor_at = _index(facets, survivor)
            facets.insert((survivor_at + 1) if survivor_at is not None else len(facets), restored)
    document["facets"] = facets
    return document


# --- evidence provenance and affected learning objects ------------------------------------


def facet_evidence(repository: Repository, facet_ids: Iterable[str]) -> dict[str, dict[str, Any]]:
    """Which of ``facet_ids`` carry graded evidence, and how much (provenance only).

    A merge re-keys this evidence to the survivor through ``facet_merges`` and
    an undo moves it back; a reword leaves it on the facet's id, graded
    against the wording the action kept. Nothing is refused because of it:
    facet identity locks were removed (owner, 2026-10-12).
    """

    ids = sorted({str(facet_id) for facet_id in facet_ids if facet_id})
    if not ids:
        return {}
    legacy = repository.facet_ids_with_recall_evidence()
    out: dict[str, dict[str, Any]] = {}
    for facet_id in ids:
        surface_groups, mass = repository.facet_independence_evidence(facet_id)
        if surface_groups or mass > 0 or facet_id in legacy:
            out[facet_id] = {"surface_groups": int(surface_groups), "independent_mass": round(float(mass), 6)}
    return out


def graded_shared_criteria(
    vault: LoadedVault, repository: Repository, facet_ids: Iterable[str],
) -> list[dict[str, Any]]:
    """Graded criteria whose frozen contract names two of ``facet_ids`` at one capability.

    The canonical projection replays an attempt from the assessment contract
    it was graded against (not from the item as it loads today) and resolves
    each target through aliases and ``facet_merges``. Merging two facets that
    one such criterion targets at the same capability would leave that
    criterion naming one cell twice: a correct answer's mass split and
    discounted, a wrong one read as two candidate causes and never counted
    (review F1). The loader collapses those duplicates for items as they load
    today; frozen history keeps them, so a merge must not create them.
    """

    members = {str(facet_id) for facet_id in facet_ids}
    if len(members) < 2:
        return []
    with repository.connection() as connection:
        contract_ids = store.graded_contract_version_ids(connection)
    if not contract_ids:
        return []
    contracts = repository.effective_assessment_contract_versions(
        contract_ids, projection_version=vault.config.algorithms.algorithm_version,
    )
    merge_map = repository.facet_merge_map()

    def resolve(facet_id: str) -> str:
        current = vault.canonical_facet_id(facet_id)
        seen: set[str] = set()
        while current in merge_map and current not in seen:
            seen.add(current)
            current = merge_map[current]
        return current

    shared: list[dict[str, Any]] = []
    for source_id, stored in sorted(contracts.items()):
        for criterion in (stored.get("contract") or {}).get("criteria") or []:
            named: dict[str, set[str]] = {}
            for target in criterion.get("targets") or []:
                facet = resolve(str(target.get("facet") or ""))
                if facet in members:
                    named.setdefault(str(target.get("capability") or ""), set()).add(facet)
            for capability, facets in sorted(named.items()):
                if len(facets) > 1:
                    shared.append({
                        "contract_version_id": source_id,
                        "practice_item_id": stored.get("practice_item_id"),
                        "criterion_id": str(criterion.get("id") or ""),
                        "capability": capability,
                        "facets": sorted(facets),
                    })
    return shared


def hold_back_shared(
    survivor: str, retired: Sequence[str], shared: Sequence[Mapping[str, Any]],
) -> tuple[list[str], list[dict[str, Any]]]:
    """Split ``retired`` into the facets that can merge and those a graded criterion holds back.

    Greedy in the judge's order: a retiree is held back when a graded
    criterion names it together with the survivor or a retiree already kept
    (review F1). Returns ``(kept, held_back)``.
    """

    group = {survivor}
    kept: list[str] = []
    held: list[dict[str, Any]] = []
    for facet_id in retired:
        hits = [dict(criterion) for criterion in shared
                if facet_id in criterion["facets"] and (set(criterion["facets"]) - {facet_id}) & group]
        if hits:
            held.append({
                "facet_id": facet_id,
                "with": sorted({other for hit in hits for other in hit["facets"] if other != facet_id} & group),
                "criteria": hits,
            })
            continue
        group.add(facet_id)
        kept.append(facet_id)
    return kept, held


#: Why a held-back facet stays registered (review F1); shown with each one.
HELD_BACK_NOTE = (
    "not merged: a graded criterion targets both facets at one capability, and its frozen contract "
    "would then count one facet twice"
)


def affected_learning_objects(vault: LoadedVault, facet_ids: Iterable[str]) -> list[str]:
    wanted = {vault.canonical_facet_id(facet_id) for facet_id in facet_ids} | set(facet_ids)
    affected: set[str] = set()
    for lo in vault.learning_objects.values():
        if wanted & set(learning_object_facet_union(lo)):
            affected.add(lo.id)
    for item in vault.practice_items.values():
        if wanted & set(item.evidence_facets):
            affected.add(item.learning_object_id)
    return sorted(affected)


def refresh_derived_state(root: Path, repository: Repository, affected: Iterable[str], *, clock: Clock | None = None) -> None:
    """Re-sync and re-fold the affected learning objects (evidence re-keyed)."""

    vault_after = load_vault(root)
    sync_vault_state(vault_after, repository, clock=clock)
    record_content_recalibration(
        vault_after, repository, affected_learning_object_ids=sorted(set(affected)), clock=clock,
    )


# --- vault scope: merge registered facets ---------------------------------------------


def merge_registered_facets(
    root: Path,
    repository: Repository,
    *,
    survivor: str,
    retired: Sequence[str],
    action: str,
    absorb_as: str | None,
    origin: str,
    run_id: str,
    judge: str,
    judge_model: str | None,
    prompt_version: str | None,
    judgment_ids: Sequence[str] = (),
    detail: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Merge or absorb registered facets into ``survivor``, live, with an undo record.

    Returns ``{"status": "applied" | "refused", ...}``. A refusal (an unknown
    or already-aliased facet, or a ``facet_merges`` conflict) writes nothing.
    Evidence never refuses a merge (facet locks were removed, owner
    2026-10-12); the facets that carry it are recorded in ``evidence``. A
    retiree that a graded criterion names together with the survivor (or with
    a retiree already kept) at one capability is held back and listed in
    ``held_back`` (review F1: the frozen contract would count one facet
    twice); when every retiree is held back the merge is refused
    (``shared_graded_criterion``).
    """

    from learnloop.vault_lock import vault_mutation_lock

    retired = [facet_id for facet_id in dict.fromkeys(retired) if facet_id != survivor]
    if not retired:
        return {"status": "refused", "reason": "nothing_to_merge"}
    with vault_mutation_lock(root, purpose="facet_identity_merge"):
        recover_interrupted_actions(root, repository, clock=clock)
        vault = load_vault(root)
        paths = VaultPaths(vault.root, vault.config)
        unknown = [facet_id for facet_id in (survivor, *retired) if facet_id not in vault.evidence_facets]
        if unknown:
            return {"status": "refused", "reason": "unknown_facet", "facet_ids": unknown}
        retired, held_back = hold_back_shared(
            survivor, retired, graded_shared_criteria(vault, repository, (survivor, *retired)),
        )
        if not retired:
            return {"status": "refused", "reason": "shared_graded_criterion", "held_back": held_back,
                    "note": HELD_BACK_NOTE}
        evidence = facet_evidence(repository, (survivor, *retired))
        merge_map = repository.facet_merge_map(include_in_flight=True)
        already = [facet_id for facet_id in retired if facet_id in merge_map]
        if already:
            return {"status": "refused", "reason": "already_merged", "facet_ids": already}
        affected_before = affected_learning_objects(vault, (survivor, *retired))

        document = _facets_document(paths)
        facets = document["facets"]
        before: dict[str, Any] = {}
        order: dict[str, int] = {}
        for facet_id in (survivor, *retired):
            index = _index(facets, facet_id)
            if index is None:
                return {"status": "refused", "reason": "not_in_registry_file", "facet_ids": [facet_id]}
            before[facet_id] = copy.deepcopy(facets[index])
            order[facet_id] = index
        new_survivor = stored_entry(union_payload(
            before[survivor], [before[facet_id] for facet_id in retired],
            action=action, absorb_as=absorb_as, alias_ids=retired,
        ))
        now = utc_now_iso(clock)
        rationale = json.dumps({"origin": "facet_identity", "run_id": run_id, "action": action}, sort_keys=True)
        record = {
            "origin": origin, "scope": "vault", "run_id": run_id, "action": action,
            "survivor_facet_id": survivor, "retired_facet_ids": retired,
            "before": {"facets": before, "order": order},
            "after": {"facets": {survivor: new_survivor, **{facet_id: None for facet_id in retired}}},
            "merge_rows": [[facet_id, survivor] for facet_id in retired],
            "judgment_ids": list(judgment_ids), "judge": judge,
            "judge_model": judge_model, "prompt_version": prompt_version,
            "detail": {**dict(detail or {}), "absorb_as": absorb_as, "evidence": evidence,
                       **({"held_back": held_back} if held_back else {})},
            "status": "applying", "created_at": now,
        }
        # 1. The intent: the action row and its facet_merges rows, one transaction.
        with repository.atomic():
            for facet_id in retired:
                repository.insert_facet_merge(
                    retired_facet_id=facet_id, surviving_facet_id=survivor, rationale=rationale, clock=clock,
                )
            action_id = insert_action(repository.connection(), record)
        record["id"] = action_id
        # 2. facets.yaml, replaced atomically; 3. derived state; 4. applied.
        # A crash anywhere after 1 leaves an ``applying`` row that recovery
        # completes from whichever side of the file write it stopped on.
        try:
            _write_facets(paths, _applied_document(document, record))
        except Exception:
            _abandon(repository, record, reason="facets.yaml could not be written", clock=clock)
            raise
        refresh_derived_state(vault.root, repository, affected_before, clock=clock)
        with repository.atomic():
            store.set_status(repository.connection(), action_id, "applied", applied_at=utc_now_iso(clock))
    return {
        "status": "applied", "action_id": action_id, "action": action, "survivor_facet_id": survivor,
        "retired_facet_ids": retired, "absorb_as": absorb_as,
        "evidence": evidence, "affected_learning_objects": affected_before,
        "held_back": held_back,
    }


def _abandon(repository: Repository, record: Mapping[str, Any], *, reason: str, clock: Clock | None = None) -> None:
    """Withdraw an ``applying`` intent whose file write never happened."""

    with repository.atomic():
        connection = repository.connection()
        store.delete_merge_rows(connection, record.get("merge_rows") or [])
        store.set_status(connection, str(record["id"]), "abandoned", undone_at=utc_now_iso(clock),
                         undo_detail={"abandoned": reason})


def _delete_merge_rows(repository: Repository, rows: Iterable[Sequence[str]]) -> int:
    with repository.atomic():
        return store.delete_merge_rows(repository.connection(), rows)


# --- ingest scopes: record proposed actions --------------------------------------------


def record_proposed_actions(
    repository: Repository, actions: Sequence[Mapping[str, Any]], *, origin: str, run_id: str,
    proposal_id: str | None, clock: Clock | None = None,
) -> list[str]:
    """Persist a run's in-run and attach actions with the proposal that carries them."""

    if not actions:
        return []
    now = utc_now_iso(clock)
    ids: list[str] = []
    with repository.atomic():
        connection = repository.connection()
        for action in actions:
            ids.append(insert_action(connection, {
                **dict(action), "origin": origin, "run_id": run_id, "proposal_id": proposal_id,
                "status": "proposed", "created_at": now,
            }))
    return ids


# --- rewords: a facet version instead of a lock -----------------------------------------

#: The fields that carry a facet's meaning. Changing one of them on an
#: existing facet is a reword: it writes a facet version (``version`` + 1, the
#: old entry kept in a ``reword`` action with an undo) instead of being refused
#: or silently overwritten (handoff §4, "Facet locks no longer block merges").
#: Examples, error signatures, repairs, aliases, provenance and status only
#: grow or annotate the contract and are not versioned.
MEANING_FIELDS = (
    "kind", "claim", "description", "preconditions", "postconditions", "applicability", "non_goals",
)
#: The ``judgment_ledger`` task of the owner's verdict on a reword (its undo).
REWORD_TASK = "facet_reword"
#: What a reword's undo leaves as it was (shown with the undo).
REWORD_UNDO_LIMITS = (
    "attempts graded while the new wording stood keep the assessment contract they were graded "
    "against; the facet's id and its evidence never moved"
)


def meaning_changes(before: Mapping[str, Any] | None, after: Mapping[str, Any] | None) -> list[str]:
    """The :data:`MEANING_FIELDS` that differ between two entries of one facet."""

    if not before or not after:
        return []
    old, new = normalized_entry(before) or {}, normalized_entry(after) or {}
    return [name for name in MEANING_FIELDS if old.get(name) != new.get(name)]


def record_reword(
    repository: Repository,
    *,
    action_id: str,
    facet_id: str,
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    run_id: str,
    proposal_id: str | None,
    proposal_item_id: str | None = None,
    origin: str = "proposal",
    clock: Clock | None = None,
) -> str:
    """Record a facet version: ``facet_id``'s meaning changed from ``before`` to ``after``.

    Called once ``facets.yaml`` shows ``after`` (the proposal apply protocol's
    side effect), so the row is ``applied`` at once and undoable. Idempotent
    on ``action_id``: recovery of an interrupted apply replays side effects.
    """

    with repository.atomic():
        connection = repository.connection()
        if store.action_by_id(connection, action_id) is not None:
            return action_id
        now = utc_now_iso(clock)
        insert_action(connection, {
            "id": action_id, "origin": origin, "scope": "vault", "run_id": run_id,
            "proposal_id": proposal_id, "action": "reword",
            "survivor_facet_id": facet_id, "retired_facet_ids": [],
            "before": {"facets": {facet_id: copy.deepcopy(dict(before))}, "order": {}},
            "after": {"facets": {facet_id: copy.deepcopy(dict(after))}},
            "merge_rows": [], "judgment_ids": [], "judge": "proposal",
            "judge_model": None, "prompt_version": None,
            "detail": {
                "fields": meaning_changes(before, after),
                "evidence": facet_evidence(repository, [facet_id]),
                "proposal_item_id": proposal_item_id,
            },
            "status": "applied", "created_at": now, "applied_at": now,
        })
    return action_id


# --- the owner's own edit of facets.yaml (the desktop Library) ---------------------------

#: ``run_id`` of the reword actions an owner's Library edit records.
LIBRARY_RUN_ID = "library"


def _parse_registry_text(text: str) -> dict[str, Any]:
    """The edited facets.yaml as an editable document, or ``invalid_registry``."""

    try:
        document = yaml_from_string(text)
    except Exception as exc:  # noqa: BLE001 - any parse error refuses the save
        first = (str(exc).strip().splitlines() or [type(exc).__name__])[0]
        raise FacetIdentityActionError("invalid_registry", f"facets.yaml does not parse: {first}") from exc
    if document is None:
        document = {}
    if not isinstance(document, dict) or not isinstance(document.get("facets", []), list):
        raise FacetIdentityActionError("invalid_registry", "facets.yaml must be a mapping with a facets list")
    try:
        EvidenceFacetsFile.model_validate(json.loads(json.dumps(document, default=str)))
    except ValueError as exc:
        lines = str(exc).strip().splitlines() or ["invalid entry"]
        raise FacetIdentityActionError(
            "invalid_registry", "facets.yaml is not a valid facet registry: " + " ".join(lines[:3]),
        ) from exc
    return document


def save_registry_text(root: Path, repository: Repository, text: str, *, clock: Clock | None = None) -> dict[str, Any]:
    """Write the owner's own edit of facets.yaml (the desktop Library) with facet versions.

    The Library is the other supported way to change a registered facet
    (review F1), so it keeps the same guarantee as a proposal apply: an edit
    that changes an existing facet's :data:`MEANING_FIELDS` writes a facet
    version, keeps the replaced entry in a ``reword`` action (origin
    ``registry``, judge ``owner``, ``detail.via = "library"``) and is undoable
    from the facet inspector or ``learnloop facets undo``.

    ``version`` is server-managed (review F5): a reworded facet gets one more
    than it had, and a facet whose meaning did not change keeps its version
    whatever the text says. The text is written as typed unless a version (or
    a reworded facet's stale ``semantic_fingerprint``) had to be corrected;
    the result's ``text`` is what was written.

    Under the vault mutation lock, write-ahead like a merge: the ``applying``
    reword rows commit, then the file is replaced atomically, then the rows
    become ``applied``. If the process stops in between, recovery marks a row
    ``applied`` when facets.yaml shows the edit and withdraws it
    (``abandoned``) when it does not: the save never landed, so nothing is
    written on the owner's behalf. Text that does not parse, or is not a
    valid facet registry, is refused (``invalid_registry``) and nothing is
    written.
    """

    from learnloop.vault_lock import vault_mutation_lock

    with vault_mutation_lock(root, purpose="facet_registry_edit"):
        recover_interrupted_actions(root, repository, clock=clock)
        vault = load_vault(root)
        paths = VaultPaths(vault.root, vault.config)
        document = _parse_registry_text(text)
        try:
            current = _current_entries(paths)
        except Exception:  # noqa: BLE001 - a registry that no longer parses has no entries to keep
            current = {}
        rewords: list[tuple[str, dict[str, Any], dict[str, Any], list[str]]] = []
        corrected = False
        for entry in document.get("facets") or []:
            facet_id = str(entry.get("id") or "")
            old = current.get(facet_id)
            if old is None:
                continue  # a new facet: nothing to keep
            old_version = int((normalized_entry(old) or {}).get("version") or 1)
            fields = meaning_changes(old, entry)
            version = old_version + 1 if fields else old_version
            if (normalized_entry(entry) or {}).get("version") != version:
                entry["version"] = version
                corrected = True
            if not fields:
                continue
            if "semantic_fingerprint" in entry:
                fingerprint = semantic_fingerprint(EvidenceFacet.model_validate(json.loads(json.dumps(entry))))
                if entry["semantic_fingerprint"] != fingerprint:
                    entry["semantic_fingerprint"] = fingerprint
                    corrected = True
            rewords.append((facet_id, copy.deepcopy(old), entry, fields))
        written = yaml_to_string(document) if corrected else text
        records: list[dict[str, Any]] = []
        if rewords:
            evidence = facet_evidence(repository, [facet_id for facet_id, *_rest in rewords])
            now = utc_now_iso(clock)
            with repository.atomic():
                connection = repository.connection()
                for facet_id, old, new, fields in rewords:
                    record = {
                        "origin": "registry", "scope": "vault", "run_id": LIBRARY_RUN_ID, "proposal_id": None,
                        "action": "reword", "survivor_facet_id": facet_id, "retired_facet_ids": [],
                        "before": {"facets": {facet_id: old}, "order": {}},
                        "after": {"facets": {facet_id: json.loads(json.dumps(new, default=str))}},
                        "merge_rows": [], "judgment_ids": [], "judge": "owner",
                        "judge_model": None, "prompt_version": None,
                        "detail": {
                            "via": "library", "fields": fields,
                            "evidence": {facet_id: evidence[facet_id]} if facet_id in evidence else {},
                        },
                        "status": "applying", "created_at": now,
                    }
                    record["id"] = insert_action(connection, record)
                    records.append(record)
        try:
            _write_registry_text(paths, written)
        except Exception:
            for record in records:
                _abandon(repository, record, reason="facets.yaml could not be written", clock=clock)
            raise
        # A reword moves no evidence (the facet keeps its id): sync only.
        refresh_derived_state(vault.root, repository, [], clock=clock)
        if records:
            with repository.atomic():
                for record in records:
                    store.set_status(repository.connection(), str(record["id"]), "applied",
                                     applied_at=utc_now_iso(clock))
    return {"text": written, "reword_action_ids": [str(record["id"]) for record in records]}


def facet_history(repository: Repository, facet_id: str, vault: LoadedVault | None = None) -> list[dict[str, Any]]:
    """Every action whose survivor is ``facet_id`` (rewords and merges), newest first."""

    with repository.connection() as connection:
        rows = store.list_actions(connection, survivor_facet_id=facet_id, limit=None)
    return [describe(row, vault) for row in rows]


def _current_entries(paths: VaultPaths) -> dict[str, Any]:
    document = _facets_document(paths)
    return {str(entry.get("id")): entry for entry in document["facets"] if isinstance(entry, Mapping)}


def effective_status(record: Mapping[str, Any], vault: LoadedVault) -> str:
    """``proposed`` until the vault shows what the action wrote, then ``applied``."""

    if record["status"] != "proposed":
        return str(record["status"])
    paths = VaultPaths(vault.root, vault.config)
    try:
        current = _current_entries(paths)
    except FacetIdentityActionError:
        return "proposed"
    survivor = str(record["survivor_facet_id"])
    after = ((record.get("after") or {}).get("facets") or {}).get(survivor)
    entry = current.get(survivor)
    if entry is None or after is None:
        return "proposed"
    aliases = set(entry.get("aliases") or [])
    retired = set(record.get("retired_facet_ids") or [])
    return "applied" if retired <= aliases and not (retired & set(current)) else "proposed"


def describe(record: Mapping[str, Any], vault: LoadedVault | None = None) -> dict[str, Any]:
    """A compact view for results, the CLI and the desktop app."""

    before = (record.get("before") or {}).get("facets") or {}

    def claim(facet_id: str) -> str:
        entry = before.get(facet_id) or {}
        if not entry and vault is not None and facet_id in vault.evidence_facets:
            entry = vault.evidence_facets[facet_id].model_dump(mode="json")
        return str(entry.get("claim") or entry.get("title") or facet_id)

    detail = record.get("detail") or {}
    status = effective_status(record, vault) if vault is not None else record["status"]
    survivor = str(record["survivor_facet_id"])
    reworded: dict[str, Any] | None = None
    if record["action"] == "reword":
        after = ((record.get("after") or {}).get("facets") or {}).get(survivor) or {}
        old = before.get(survivor) or {}
        reworded = {
            "from": str(old.get("claim") or old.get("description") or ""),
            "to": str(after.get("claim") or after.get("description") or ""),
            "from_version": old.get("version"),
            "to_version": after.get("version"),
            "fields": list(detail.get("fields") or []),
        }
    # Facets that carried graded evidence when the action applied (provenance;
    # nothing is refused because of it). Rows written before facet locks were
    # removed recorded lock reasons instead and show no evidence here.
    evidence = detail.get("evidence") or {}
    return {
        "id": record["id"],
        "origin": record["origin"],
        "scope": record["scope"],
        "run_id": record["run_id"],
        "proposal_id": record.get("proposal_id"),
        "action": record["action"],
        "absorb_as": detail.get("absorb_as"),
        "survivor": {"id": survivor, "claim": claim(survivor)},
        "retired": [{"id": facet_id, "claim": claim(facet_id)} for facet_id in record.get("retired_facet_ids") or []],
        "rationale": detail.get("rationale") or "",
        "evidenced_facets": sorted(evidence),
        # A reword: the wording replaced and the one written (versions too).
        "reworded": reworded,
        # Why an attach left a registered facet's contract as it was.
        "contract_note": detail.get("contract_note"),
        # Retirees of the judged set a graded criterion kept registered (review F1).
        "held_back": [str(held.get("facet_id")) for held in detail.get("held_back") or []],
        # What an undo does not move back (review F9).
        "undo_limits": REWORD_UNDO_LIMITS if record["action"] == "reword" else UNDO_LIMITS,
        "judge": record["judge"],
        "judge_model": record.get("judge_model"),
        "status": status,
        "undoable": status == "applied" and not detail.get("undo"),
        # Why there is no undo, when there is none by construction.
        "note": detail.get("undo"),
        "created_at": record["created_at"],
        "undone_at": record.get("undone_at"),
    }


# --- undo ----------------------------------------------------------------------------------


def _later_actions(repository: Repository, record: Mapping[str, Any]) -> list[str]:
    facets = {record["survivor_facet_id"], *(record.get("retired_facet_ids") or [])}
    later = []
    for other in list_actions(repository, limit=None):
        if (other["id"] == record["id"] or other["status"] in {"undone", "abandoned"}
                or other["created_at"] < record["created_at"]):
            continue
        if facets & {other["survivor_facet_id"], *(other.get("retired_facet_ids") or [])}:
            later.append(other["id"])
    return later


def undo_action(root: Path, repository: Repository, action_id: str, *, clock: Clock | None = None) -> dict[str, Any]:
    """Restore the facets.yaml entries and ``facet_merges`` rows one action replaced.

    Refuses (writing nothing) when the action is unknown, already undone, not
    applied yet, or when the survivor's entry has changed since. Otherwise
    the intent (``undoing``) commits before the file is restored, so an
    interrupted undo is finished by :func:`recover_interrupted_actions`.
    """

    from learnloop.vault_lock import vault_mutation_lock

    with vault_mutation_lock(root, purpose="facet_identity_undo"):
        recovered = recover_interrupted_actions(root, repository, clock=clock)
        finished = next((row for row in recovered if row["id"] == action_id and row["to"] == "undone"), None)
        record = action_by_id(repository, action_id)
        if record is None:
            raise FacetIdentityActionError("unknown_action", f"No facet identity action {action_id!r}.")
        if finished is not None:
            # A retry of an interrupted undo: recovery just finished it.
            undo_detail = record.get("undo_detail") or {}
            return {"status": "undone", "action_id": action_id, "recovered": True,
                    "survivor_facet_id": record["survivor_facet_id"],
                    "restored_facet_ids": list(record.get("retired_facet_ids") or []),
                    "merge_rows_deleted": undo_detail.get("merge_rows_deleted", 0),
                    "not_restored": UNDO_LIMITS}
        if record["status"] == "undone":
            raise FacetIdentityActionError("already_undone", f"Action {action_id} was already undone.")
        if record["status"] == "abandoned":
            raise FacetIdentityActionError("abandoned", f"Action {action_id} never applied; nothing to undo.")
        if (record.get("detail") or {}).get("undo"):
            raise FacetIdentityActionError("no_undo", f"Action {action_id} has no undo: {record['detail']['undo']}.")
        vault = load_vault(root)
        status = effective_status(record, vault)
        if status == "proposed":
            raise FacetIdentityActionError(
                "not_applied",
                f"Action {action_id} is part of proposal {record.get('proposal_id') or '(unknown)'}, which has "
                "not been applied; it takes effect only when that proposal is applied.",
            )
        paths = VaultPaths(vault.root, vault.config)
        document = _facets_document(paths)
        survivor, retired, _before, _order, after = _record_parts(record)
        index = _index(document["facets"], survivor)
        if index is None or normalized_entry(document["facets"][index]) != normalized_entry(after.get(survivor)):
            later = _later_actions(repository, record)
            raise FacetIdentityActionError(
                "changed_since",
                f"Facet {survivor} changed after action {action_id}"
                + (f" (later action(s): {', '.join(later)}; undo those first)." if later else " (edited since)."),
            )
        present = [facet_id for facet_id in retired if _index(document["facets"], facet_id) is not None]
        if present:
            raise FacetIdentityActionError(
                "changed_since", f"Facet(s) {', '.join(present)} exist again; nothing to restore.",
            )
        with repository.atomic():
            _record_undo_intent(repository.connection(), record, clock=clock)
        result = _finish_undo(vault.root, repository, record, document=document, clock=clock)
    return {"status": "undone", "action_id": action_id, **result}


def _record_undo_intent(connection: Any, record: Mapping[str, Any], *, clock: Clock | None = None) -> None:
    """The write-ahead undo intent: the owner's verdicts, and the row becomes ``undoing``."""

    now = utc_now_iso(clock)
    owner_ids = append_owner_verdicts(connection, record, created_at=now)
    store.set_status(connection, str(record["id"]), "undoing",
                     undo_detail={"requested_at": now, "owner_judgment_ids": owner_ids})


def append_owner_verdicts(connection: Any, record: Mapping[str, Any], *, created_at: str) -> list[str]:
    """An undo is the owner's verdict (§0 rule 6): ``different`` for every pair of the set.

    Each judge row that put a pair of this action in one set is superseded by
    an owner row on the same question (``supersedes_id``). The set's facets
    also get owner rows keyed by facet id (the ids they carry in the vault
    after the undo), unless a superseding row already is one, so a later
    dedupe or attach never merges them again (``judge.owner_vetoes``).

    A reword has no pair: its undo is the owner rejecting that wording of the
    facet (review F4). One row, task :data:`REWORD_TASK`, asks "is this the
    facet's wording?" about ``facet:<id>`` and ``facet_wording:<hash of the
    meaning fields written>``, verdict ``rejected``. It commits with the undo
    intent (``undoing``), so a retried or recovered undo never appends it again.
    """

    from learnloop.ai.execution import content_key
    from learnloop.content.facet_identity.judge import TASK
    from learnloop.db.stores.judgments import append_judgment

    survivor, retired, before, _order, after = _record_parts(record)
    action_id = str(record["id"])
    if record.get("action") == "reword":
        old = normalized_entry(before.get(survivor)) or {}
        new = normalized_entry(after.get(survivor)) or {}
        wording = {name: new.get(name) for name in MEANING_FIELDS}
        return [append_judgment(
            connection, task=REWORD_TASK, left_kind="facet", left_id=survivor,
            right_kind="facet_wording", right_id=content_key(wording), judge="owner",
            input_hash=content_key({"owner_undo": action_id, "facet": survivor, "wording": wording}),
            verdict="rejected",
            rationale=json.dumps({
                "origin": "undo", "action_id": action_id, "facet": survivor,
                "from_version": old.get("version"), "to_version": new.get("version"),
                "fields": meaning_changes(old, new),
            }, sort_keys=True),
            created_at=created_at,
        )]
    rationale = json.dumps({"origin": "undo", "action_id": action_id, "facets": [survivor, *retired]},
                           sort_keys=True)
    ids: list[str] = []
    covered: set[frozenset[str]] = set()
    judgment_ids = [str(value) for value in record.get("judgment_ids") or []]
    rows = connection.execute(
        f"SELECT * FROM judgment_ledger WHERE id IN ({','.join('?' for _ in judgment_ids)})", judgment_ids,
    ).fetchall() if judgment_ids else []
    for row in rows:
        if str(row["verdict"]) != "same" or str(row["judge"]) == "owner":
            continue
        ids.append(append_judgment(
            connection, task=TASK, left_kind=str(row["left_kind"]), left_id=str(row["left_id"]),
            right_kind=row["right_kind"], right_id=row["right_id"], judge="owner",
            input_hash=str(row["input_hash"]), verdict="different", rationale=rationale,
            supersedes_id=str(row["id"]), created_at=created_at,
        ))
        if row["left_kind"] == "facet" and row["right_kind"] == "facet":
            covered.add(frozenset((str(row["left_id"]), str(row["right_id"]))))
    members = [survivor, *retired]
    for index, first in enumerate(members):
        for second in members[index + 1:]:
            if frozenset((first, second)) in covered:
                continue
            left, right = sorted((first, second))
            ids.append(append_judgment(
                connection, task=TASK, left_kind="facet", left_id=left, right_kind="facet", right_id=right,
                judge="owner", input_hash=content_key({"owner_undo": action_id, "pair": [left, right]}),
                verdict="different", rationale=rationale, created_at=created_at,
            ))
    return ids


def _finish_undo(
    root: Path, repository: Repository, record: Mapping[str, Any], *, document: dict[str, Any] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Restore the file, drop the merge rows, refresh, mark ``undone`` (idempotent)."""

    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    survivor, retired, _before, _order, _after = _record_parts(record)
    reword = record.get("action") == "reword"
    affected = affected_learning_objects(vault, (survivor, *retired))
    document = document if document is not None else _facets_document(paths)
    if file_state(record, document["facets"]) == "after":
        _write_facets(paths, _restored_document(document, record))
    deleted = _delete_merge_rows(repository, record.get("merge_rows") or [])
    vault_after = load_vault(root)
    affected = sorted(set(affected) | set(affected_learning_objects(vault_after, (survivor, *retired))))
    # A reword moved no evidence (the facet keeps its id): sync only, no re-fold.
    refresh_derived_state(root, repository, [] if reword else affected, clock=clock)
    if reword:
        affected = []
    limits = REWORD_UNDO_LIMITS if reword else UNDO_LIMITS
    current = action_by_id(repository, str(record["id"])) or {}
    detail = {**dict(current.get("undo_detail") or {}), "merge_rows_deleted": deleted,
              "restored_facet_ids": retired, "not_restored": limits}
    with repository.atomic():
        store.set_status(repository.connection(), str(record["id"]), "undone", undone_at=utc_now_iso(clock),
                         undo_detail=detail)
    return {
        "survivor_facet_id": survivor, "restored_facet_ids": retired, "merge_rows_deleted": deleted,
        "affected_learning_objects": affected, "not_restored": limits,
        "owner_judgment_ids": list(detail.get("owner_judgment_ids") or []),
    }


# --- recovery -----------------------------------------------------------------------------


def interrupted_actions(repository: Repository) -> list[dict[str, Any]]:
    """Action rows left ``applying`` or ``undoing`` by an interrupted process (oldest first)."""

    rows: list[dict[str, Any]] = []
    for status in IN_FLIGHT:
        rows.extend(list_actions(repository, status=status, limit=None))
    return sorted(rows, key=lambda row: (str(row["created_at"]), str(row["id"])))


def recover_interrupted_actions(root: Path, repository: Repository, *, clock: Clock | None = None) -> list[dict[str, Any]]:
    """Finish every interrupted merge or undo from the side of the file write it stopped on.

    * ``applying``: facets.yaml already shows the merge -> refresh, ``applied``;
      it still shows the facets before -> write the merge, refresh,
      ``applied``, unless a criterion graded meanwhile names two of its facets
      (review F1); that, or anything else (edited since) -> the intent is
      withdrawn (``abandoned``, its ``facet_merges`` rows removed).
    * ``undoing``: the owner asked for the undo, so it is finished: the file
      restored if it still shows the merge, the rows removed, ``undone``. A
      file that shows neither side is reported and left for the owner.

    The caller holds the vault mutation lock (it is re-entrant). Returns what
    happened to each row.
    """

    from learnloop.vault_lock import vault_mutation_lock

    pending = interrupted_actions(repository)
    if not pending:
        return []
    out: list[dict[str, Any]] = []
    with vault_mutation_lock(root, purpose="facet_identity_recover"):
        for record in interrupted_actions(repository):
            vault = load_vault(root)
            paths = VaultPaths(vault.root, vault.config)
            document = _facets_document(paths)
            state = file_state(record, document["facets"])
            survivor, retired, _before, _order, _after = _record_parts(record)
            reword = record.get("action") == "reword"
            if record["status"] == "applying":
                if state == "neither":
                    _abandon(repository, record, reason="facets.yaml changed before the merge was written",
                             clock=clock)
                    out.append({"id": record["id"], "from": "applying", "to": "abandoned"})
                    continue
                if reword and state == "before":
                    # An owner's Library save that never landed: the owner saw
                    # it fail, so withdraw it rather than write one entry of it.
                    _abandon(repository, record, reason="the registry edit was never written", clock=clock)
                    out.append({"id": record["id"], "from": "applying", "to": "abandoned"})
                    continue
                if state == "before":
                    # A criterion graded while the intent waited may now name
                    # two of its facets (review F1): withdraw rather than merge.
                    _kept, held = hold_back_shared(
                        survivor, retired, graded_shared_criteria(vault, repository, (survivor, *retired)),
                    )
                    if held:
                        _abandon(repository, record, clock=clock,
                                 reason="a criterion graded since the intent names two of its facets")
                        out.append({"id": record["id"], "from": "applying", "to": "abandoned", "held_back": held})
                        continue
                    _write_facets(paths, _applied_document(document, record))
                # A reword moved no evidence (the facet keeps its id): sync only.
                affected = [] if reword else affected_learning_objects(vault, (survivor, *retired))
                refresh_derived_state(root, repository, affected, clock=clock)
                with repository.atomic():
                    store.set_status(repository.connection(), str(record["id"]), "applied",
                                     applied_at=utc_now_iso(clock))
                out.append({"id": record["id"], "from": "applying", "to": "applied", "file": state})
                continue
            if state == "neither":
                out.append({"id": record["id"], "from": "undoing", "to": "undoing", "file": state,
                            "problem": f"facets.yaml shows neither side of action {record['id']}; "
                                       f"restore facet {survivor} by hand, then run doctor --fix-state"})
                continue
            _finish_undo(root, repository, record, document=document, clock=clock)
            out.append({"id": record["id"], "from": "undoing", "to": "undone", "file": state})
    return out


__all__ = [
    "FacetIdentityActionError",
    "HELD_BACK_NOTE",
    "MEANING_FIELDS",
    "REWORD_TASK",
    "REWORD_UNDO_LIMITS",
    "append_owner_verdicts",
    "action_by_id",
    "affected_learning_objects",
    "describe",
    "facet_evidence",
    "facet_history",
    "graded_shared_criteria",
    "hold_back_shared",
    "effective_status",
    "insert_action",
    "list_actions",
    "meaning_changes",
    "merge_registered_facets",
    "normalized_entry",
    "record_proposed_actions",
    "record_reword",
    "save_registry_text",
    "file_state",
    "interrupted_actions",
    "recover_interrupted_actions",
    "refresh_derived_state",
    "stored_entry",
    "undo_action",
]
