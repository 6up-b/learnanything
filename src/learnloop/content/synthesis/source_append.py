"""Append reconciliation: safe increments to an existing study map (ING M7, §10).

After the first study map exists, every added source, newly selected unit, or
adopted source revision routes here. This service REUSES all of M6's synthesis
machinery (manifests, span protocol, §8.7 gates, proposal pipeline) with a
different context builder + prompt:

    context = new/changed inventories + brief + a BOUNDED affected neighborhood
              (append_neighborhood.select_neighborhood) — NEVER the full map.

Output is an ``AppendReconciliation`` mapped to the §10.2 intent/storage vocabulary:

    new_coverage                         -> create existing curriculum types
    span_attach / alternate_explanation  -> provenance_link create
    assessment_alignment                 -> provenance_link create (relation=...)
    notation_mapping                     -> notation_mapping create (review)
    conflict                             -> source_conflict create (review)
    restructure_unlocked                 -> update/deactivate (review; an LO with attempts refuses)

Purity is VERIFIED from item type + payload (the append-vocabulary gate + the
specialized apply handlers), never trusted from the LLM's intent label. Routine
span/assessment attachments that pass §10.3 auto-apply under the vault lock; every
other item stays a pending review proposal.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from learnloop.ai.execution import ModelCheckpoint, generation_limit, model_settings
from learnloop.clock import Clock
from learnloop.content.synthesis.ai_contracts import (
    AppendReconciliation,
    AppendReconciliationContext,
    SourceSetSynthesis,
    append_reconciliation_prompt,
    append_reconciliation_prompt_version,
)
from learnloop.ai.transport import StructuredTransport, execute_structured_operation
from learnloop.db.repositories import Repository
from learnloop.vault.repository import vault_repository
from learnloop.ids import new_ulid
from learnloop.content.synthesis.append_neighborhood import select_neighborhood
from learnloop.content.synthesis.graph_nomination import GraphNominator, plan_ingest_embedding
from learnloop.content.proposals.patches import compute_target_hash
from learnloop.content.facet_identity import authority as facet_meaning
from learnloop.content.synthesis.source_set_synthesis import (
    RunScope,
    StudyMapError,
    SynthesisAnswer,
    SynthesisMode,
    SynthesisOutcome,
    _Normalized,
    _count_items,
    _collect_inputs,
    _normalize,
    _resolve_span_requests,
    _result_tokens,
    _row,
    _span_refs,
    _support_citations,
    _synthesis_pass_key,
    finish_synthesis_run,
    open_synthesis_run,
)
from learnloop.content.synthesis.synthesis_gates import (
    ASSESSMENT_ONLY_ROLES,
    GateItem,
    ProvenanceRef,
)
from learnloop.content.synthesis.synthesis_manifests import content_hash
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths

APPEND_AGENT_PURPOSE = "append_reconciliation"
APPEND_PROPOSAL_PURPOSE = "sourceset_append"


def request_append_reconciliation(
    client: StructuredTransport, context: AppendReconciliationContext
) -> AppendReconciliation:
    """Reconcile one bounded append context through the shared transport."""

    return execute_structured_operation(
        client,
        purpose="append_reconciliation",
        prompt=append_reconciliation_prompt(context),
        result_model=AppendReconciliation,
    )


#: The typed refusal of an append whose request is over ``append_input_ceiling``.
#: Not retryable: the same append refuses the same way until it is narrowed or
#: the ceiling is raised (splitting a large append into passes is K2.4).
APPEND_INPUT_OVER_CEILING = "append_input_over_ceiling"


def append_checkpoint_key(prompt: str, settings: dict[str, Any]) -> str:
    """Model-work checkpoint identity of one append call (the first call or its
    span round): a bootstrap pass's key under the append's purpose. No budget
    in it, so a paid answer is reused under any budget."""

    return _synthesis_pass_key(
        prompt, AppendReconciliation.model_json_schema(), settings, purpose=APPEND_AGENT_PURPOSE,
    )


@dataclass(frozen=True)
class _AppendCall:
    """One append request, checkpointed and bounded as a bootstrap pass is:
    a saved answer is read before anything is paid; otherwise the input is held
    to its ceiling before the call, the call runs under the output budget as
    its generation limit, and the answer is saved before the output check, so
    a retry never pays for it again. ``None`` limits: an unlimited run.
    An answer the gates reject is dropped (:meth:`discard_answers`), so a retry
    pays for a fresh one instead of replaying the rejection."""

    client: Any
    repository: Repository
    settings: dict[str, Any]
    input_ceiling: int | None
    output_budget: int | None
    #: Each answer this run used, fresh or reused: its checkpoint key and the stored form it was served from.
    answers: list[tuple[str, Any]] = field(default_factory=list)

    def __call__(self, context: AppendReconciliationContext) -> AppendReconciliation:
        prompt = append_reconciliation_prompt(context)
        checkpoint = ModelCheckpoint(
            self.repository, append_checkpoint_key(prompt, self.settings), APPEND_AGENT_PURPOSE,
            AppendReconciliation.model_validate,
        )
        # The same estimate as a bootstrap pass: the prompt and schema sent.
        tokens = max(1, (len(prompt) + len(json.dumps(AppendReconciliation.model_json_schema()))) // 4)

        def call() -> AppendReconciliation:
            if self.input_ceiling is not None and tokens > self.input_ceiling:
                raise _over_ceiling(tokens, self.input_ceiling)
            with generation_limit(self.output_budget):
                return request_append_reconciliation(self.client, context)

        result, _reused, stored = checkpoint.answer_stored(
            call, usage=lambda answer: {"input_tokens_estimate": tokens, "output_tokens_estimate": _result_tokens(answer)},
        )
        self.answers.append((checkpoint.key, stored))
        if self.output_budget is not None and _result_tokens(result) > self.output_budget:
            raise StudyMapError("budget_exceeded", "Append reconciliation exceeded its output budget.")
        return result

    def discard_answers(self) -> None:
        """Drop every answer this run used (the first call and its span round).
        A rejected answer is the model's, not the budget's: kept, it would be
        replayed into the same rejection by every retry at zero cost while the
        card offers Retry. An over-budget answer is not dropped: a raised
        budget reuses it. Each is dropped only while it is still the saved
        answer, so a fresh one another run saved since is kept."""

        for key, stored in self.answers:
            self.repository.discard_model_checkpoint(key, result=stored)


def _over_ceiling(tokens: int, ceiling: int) -> StudyMapError:
    message = (
        f"This update's request comes to about {tokens:,} input tokens, over its ceiling of {ceiling:,} "
        "([ingest.budgets] append_input_ceiling), so nothing was sent."
    )
    return StudyMapError(
        APPEND_INPUT_OVER_CEILING, message,
        diagnostics=[{
            "gate": "append_input_ceiling",
            "severity": "hard_fail",
            "entity_refs": [],
            "message": message,
            "suggested_action": (
                "build fewer new sections at once, or raise [ingest.budgets] append_input_ceiling; "
                "splitting a large update into passes is not built yet"
            ),
        }],
    )


def select_new_inventories(
    entries: list[dict[str, Any]],
    revision_ids: Collection[str],
    new_unit_ids: Mapping[str, Sequence[str]] | None,
) -> list[dict[str, Any]]:
    """The inventory entries an append sends as new.

    Every entry of ``revision_ids``, except that a revision named in
    ``new_unit_ids`` sends only its listed units (a merged unit when any
    member is listed). A book is one revision, so without the unit filter
    each keep-ahead append re-sent every chapter built so far.
    """

    chosen: list[dict[str, Any]] = []
    for entry in entries:
        revision_id = entry["revision_id"]
        if revision_id not in revision_ids:
            continue
        units = (new_unit_ids or {}).get(revision_id)
        if units is not None and not ({entry["unit_id"], *entry.get("source_unit_ids", ())} & set(units)):
            continue
        chosen.append(entry)
    return chosen


def _units_by_revision(unit_keys: Collection[str], revision_ids: Collection[str]) -> dict[str, set[str]]:
    """``{revision: units}`` from a manifest's ``"revision:unit"`` keys."""

    units: dict[str, set[str]] = {}
    for revision_id in revision_ids:
        prefix = f"{revision_id}:"
        units[revision_id] = {key[len(prefix):] for key in unit_keys if key.startswith(prefix)}
    return units


def _sent_units(repository: Repository, source_set_id: str, revision_ids: Collection[str]) -> dict[str, set[str]]:
    """The units each kept synthesis of the set sent, per revision.

    A completed run's manifest records them: a bootstrap sent every unit in
    its ``unit_inventory_versions``, an append the units of its scope's
    revisions (only the listed ones of a revision its ``new_unit_ids``
    names). Kept: the run's proposal was not wholly rejected (a proposal
    waiting for review counts, as a keep-ahead build's chapters count once
    it builds them). A merged unit sent under a member's id counts as unsent,
    so at worst it is sent again."""

    sent: dict[str, set[str]] = {revision_id: set() for revision_id in revision_ids}
    for manifest in repository.completed_synthesis_manifests(source_set_id):
        proposal_id = manifest.get("proposal_id")
        decisions = [item["decision"] for item in repository.proposal_items(proposal_id)] if proposal_id else []
        if decisions and all(decision == "rejected" for decision in decisions):
            continue
        keys = list(manifest.get("unit_inventory_versions") or {})
        scope = manifest.get("scope")
        if isinstance(scope, dict) and scope.get("mode") == "append":
            named = set(scope.get("new_revision_ids") or ())
            unit_filter = scope.get("new_unit_ids") or {}
        else:
            named, unit_filter = set(revision_ids), {}
        for revision_id, units in _units_by_revision(keys, named & set(revision_ids)).items():
            listed = unit_filter.get(revision_id)
            sent[revision_id] |= units if listed is None else units & set(listed)
    return sent


def units_not_yet_sent(root: Path, source_set_id: str) -> tuple[list[str], dict[str, list[str]]]:
    """What an append that names no revision sends (the CLI's ``synthesize``):
    the set's units no kept synthesis of it has sent (:func:`_sent_units`),
    as ``(new_revision_ids, new_unit_ids)`` for :func:`append_source`.

    A revision none of whose units was sent is named whole, with no unit
    filter (a wholly new member, as the collection build sends it); a partly
    sent one is narrowed to its unsent units (K3.2's filter); a wholly sent one
    is left out. Both empty: nothing new. Without this every such append
    re-sent the whole set's inventories, the bootstrap's book included.
    Read-only, so a dry run may call it."""

    vault = load_vault(root)
    source_set = next((s for s in vault.source_sets if s.id == source_set_id), None)
    if source_set is None:
        raise StudyMapError("source_set_not_found", f"Source set '{source_set_id}' does not exist.")
    repository = Repository.attach(VaultPaths(vault.root, vault.config).sqlite_path, read_only=True)
    inputs = _collect_inputs(repository, vault, source_set)
    current = _units_by_revision(list(inputs.unit_inventory_versions), inputs.selected_revision_ids)
    sent = _sent_units(repository, source_set_id, inputs.selected_revision_ids)
    revision_ids: list[str] = []
    new_unit_ids: dict[str, list[str]] = {}
    for revision_id in inputs.selected_revision_ids:
        unsent = current[revision_id] - sent[revision_id]
        if not unsent:
            continue
        revision_ids.append(revision_id)
        if sent[revision_id]:
            new_unit_ids[revision_id] = sorted(unsent)
    return revision_ids, new_unit_ids


def append_scope(
    vault: LoadedVault,
    *,
    change_kind: str,
    revision_ids: Collection[str],
    neighborhood: dict[str, Any],
    new_unit_ids: Mapping[str, Sequence[str]] | None = None,
    facet_identity_client: Any = None,
    revision_diff: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """The append manifest's ``scope``: what changed and what the append read around it. A key exists only when its
    input does, so the record of an append without a unit filter or a revision diff keeps its earlier shape."""

    scope: dict[str, Any] = {
        "mode": "append",
        "change_kind": change_kind,
        "new_revision_ids": sorted(revision_ids),
        "neighborhood": neighborhood,
    }
    if new_unit_ids is not None:
        scope["new_unit_ids"] = {revision: sorted(units) for revision, units in sorted(new_unit_ids.items())}
    if revision_diff:
        # Rendered into the append request, so the record names it.
        scope["revision_diff_hash"] = content_hash(dict(revision_diff))
    # Facet identity (handoff §4): the judge's identity in the manifest only
    # while the switch is on.
    if vault.config.facet_identity.enabled:
        from learnloop.content.facet_identity.judge import manifest_identity

        scope["facet_identity"] = manifest_identity(vault.config, client=facet_identity_client)
    return scope


def subject_has_applied_study_map(vault: LoadedVault, subject_id: str) -> bool:
    """The bootstrap-vs-append discriminator (§8/§10).

    A subject already carries a live study map once any learning object is scoped
    to it — the same "a study map exists" existence check the CLI's ``--mode auto``
    uses (``loaded.evidence_facets``), but subject-scoped so a multi-subject vault
    routes each subject independently. When this is true, a newly added source
    reconciles into the existing map through the bounded append vocabulary instead
    of re-creating it with bootstrap.
    """

    return any(subject_id in lo.subjects for lo in vault.learning_objects.values())

_AUTO_APPLY_RELATIONS = frozenset({"support", "alternate", "assessment_alignment"})


@dataclass
class AppendResult:
    source_set_id: str
    subject_id: str
    change_kind: str
    manifest_hash: str
    synthesis_run_id: str | None = None
    proposal_id: str | None = None
    # The proposal is an earlier run's equal one (``proposal_match``); nothing new was written.
    reused: bool = False
    # ... and that proposal had nothing left waiting: the append added nothing.
    nothing_new: bool = False
    auto_applied_item_ids: list[str] = field(default_factory=list)
    review_item_ids: list[str] = field(default_factory=list)
    item_counts: dict[str, int] = field(default_factory=dict)
    gate_diagnostics: list[dict[str, Any]] = field(default_factory=list)
    neighborhood: dict[str, Any] = field(default_factory=dict)
    span_request_count: int = 0
    study_map_diff: dict[str, Any] = field(default_factory=dict)
    merge_review_proposals: list[dict[str, Any]] = field(default_factory=list)
    # Facet identity (handoff §4): None when the switch is off.
    facet_identity: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_set_id": self.source_set_id,
            "subject_id": self.subject_id,
            "change_kind": self.change_kind,
            "manifest_hash": self.manifest_hash,
            "synthesis_run_id": self.synthesis_run_id,
            "proposal_id": self.proposal_id,
            "reused": self.reused,
            "nothing_new": self.nothing_new,
            "auto_applied_item_ids": list(self.auto_applied_item_ids),
            "review_item_ids": list(self.review_item_ids),
            "item_counts": dict(self.item_counts),
            "gate_diagnostics": list(self.gate_diagnostics),
            "neighborhood": dict(self.neighborhood),
            "span_request_count": self.span_request_count,
            "study_map_diff": dict(self.study_map_diff),
            "merge_review_proposals": list(self.merge_review_proposals),
            "facet_identity": self.facet_identity,
        }


# --- orchestration ----------------------------------------------------------


def append_source(
    root: Path,
    source_set_id: str,
    *,
    client: Any,
    new_revision_ids: list[str] | None = None,
    new_unit_ids: Mapping[str, Sequence[str]] | None = None,
    change_kind: str = "source_added",
    revision_diff: dict[str, Any] | None = None,
    brief: dict[str, Any] | None = None,
    auto_apply: bool = True,
    repository: Repository | None = None,
    clock: Clock | None = None,
    budget_overrides: dict[str, int] | None = None,
    unlimited_token_budget: bool = False,
    embedding_client_factory: Callable[[], Any] | None = None,
    facet_identity_client: Any = None,
    apply_gate: Callable[[], bool] | None = None,
) -> AppendResult:
    """Run bounded append reconciliation and (by policy) auto-apply routine items.

    ``new_revision_ids`` and ``new_unit_ids`` pick the new inventories
    (``select_new_inventories``). ``embedding_client_factory`` replaces the
    ``ai.routing.embedding`` client for T5 nominations (tests); it is used
    only when nominations are on. ``facet_identity_client`` replaces the
    facet-identity judge (tests).
    """

    vault = load_vault(root)
    if repository is None:
        # Repository opens a fresh sqlite connection per call; nothing to close.
        repository = vault_repository(VaultPaths(vault.root, vault.config))
    return _append(
        vault, repository, root, source_set_id,
        client=client, new_revision_ids=new_revision_ids, new_unit_ids=new_unit_ids, change_kind=change_kind,
        revision_diff=revision_diff or {}, brief=brief or {}, auto_apply=auto_apply, apply_gate=apply_gate, clock=clock,
        budget_overrides=budget_overrides,
        unlimited_token_budget=unlimited_token_budget,
        embedding_client_factory=embedding_client_factory,
        facet_identity_client=facet_identity_client,
    )


def plan_append_embedding(
    root: Path, source_set_id: str, *, new_revision_ids: list[str] | None = None,
    new_unit_ids: Mapping[str, Sequence[str]] | None = None,
) -> dict[str, Any]:
    """Dry run of one append's Slice 2 T5 embedding spend.

    Reads the new inventories through a read-only connection and stored
    vectors only: no client, manifest, agent run or other data change. The new
    inventory's claim and concept queries are priced exactly (less those
    already stored); the candidates the reconciliation writes are bounded by
    the per-run cap (:func:`plan_ingest_embedding`).
    """

    vault = load_vault(root)
    source_set = next((s for s in vault.source_sets if s.id == source_set_id), None)
    if source_set is None:
        raise StudyMapError("source_set_not_found", f"Source set '{source_set_id}' does not exist.")
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    inputs = _collect_inputs(Repository.attach(sqlite_path, read_only=True), vault, source_set)
    revs = set(new_revision_ids or inputs.selected_revision_ids)
    new_inventories = select_new_inventories(inputs.unit_inventories, revs, new_unit_ids)
    plan = plan_ingest_embedding(vault, sqlite_path, entry="append", new_inventories=new_inventories)
    from learnloop.content.facet_identity.plan import ingest_dry_run

    return {"source_set_id": source_set_id, "new_revision_ids": sorted(revs), **plan,
            "facet_identity": ingest_dry_run(vault)}


def _append(
    vault: LoadedVault,
    repository: Repository,
    root: Path,
    source_set_id: str,
    *,
    client: Any,
    new_revision_ids: list[str] | None,
    change_kind: str,
    revision_diff: dict[str, Any],
    new_unit_ids: Mapping[str, Sequence[str]] | None = None,
    brief: dict[str, Any],
    auto_apply: bool,
    clock: Clock | None,
    budget_overrides: dict[str, int] | None = None,
    unlimited_token_budget: bool = False,
    embedding_client_factory: Callable[[], Any] | None = None,
    facet_identity_client: Any = None,
    apply_gate: Callable[[], bool] | None = None,
) -> AppendResult:
    """The append opens its run with the shared head (:func:`open_synthesis_run`); its scope step selects the new
    inventories and the bounded neighbourhood around them, which the manifest records and the request reads. Its
    call asks the append prompt (with a span round when the model asks for one); everything after the answer is the
    shared tail (:func:`finish_synthesis_run`), under the ``APPEND`` mode, with §10.3's routine items as what it
    applies."""

    def decide_scope(_brief, inputs, budgets, nominator) -> RunScope:
        revs = set(new_revision_ids or inputs.selected_revision_ids)
        new_inventories = select_new_inventories(inputs.unit_inventories, revs, new_unit_ids)
        # Deterministic bounded affected-neighborhood selection (§10.1/§3.2), with
        # Slice 2 T5 embedding nominations unioned in when they are switched on.
        neighborhood = select_neighborhood(
            vault, repository, new_inventories,
            budget_tokens=budgets.append_neighborhood_input_tokens,
            source_ids={entry["source_id"] for entry in new_inventories}, revision_ids=revs,
            nominator=nominator,
        )
        return RunScope(
            append_scope(
                vault, change_kind=change_kind, revision_ids=revs, neighborhood=neighborhood.as_manifest_record(),
                new_unit_ids=new_unit_ids, facet_identity_client=facet_identity_client, revision_diff=revision_diff,
            ),
            revision_ids=sorted(revs),
            context=(new_inventories, neighborhood.as_context()),
        )

    run = open_synthesis_run(
        vault, repository, root, source_set_id, APPEND,
        client=client, brief=brief, decide_scope=decide_scope, clock=clock, budget_overrides=budget_overrides,
        unlimited_token_budget=unlimited_token_budget, embedding_client_factory=embedding_client_factory,
        facet_identity_client=facet_identity_client,
    )
    source_set, budgets = run.source_set, run.budgets
    new_inventories, neighborhood_context = run.context
    call = _AppendCall(
        client, repository,
        # A bootstrap pass's settings: what shapes the answer, with the run's provider and model.
        settings={**model_settings(client), "provider": run.provider, "model": run.model},
        input_ceiling=None if unlimited_token_budget else budgets.append_input_ceiling,
        output_budget=None if unlimited_token_budget else budgets.append_output_tokens,
    )

    def ask() -> SynthesisAnswer:
        reconciliation, span_request_count = _run_reconciliation(
            call, repository, run.inputs, new_inventories, neighborhood_context, source_set,
            source_set.subject_id, change_kind, revision_diff, run.brief, budgets,
            one_facet_per_skill=run.one_facet_per_skill,
        )
        reconciliation, preset_diagnostics = _within_preset(reconciliation, run.brief)
        return SynthesisAnswer(reconciliation, span_request_count, diagnostics=preset_diagnostics)

    outcome = finish_synthesis_run(
        run, APPEND, ask=ask, drop_answers=call.discard_answers,
        apply=lambda outcome: _apply_routine_items(
            root, repository, vault, outcome, auto_apply=auto_apply, apply_gate=apply_gate, clock=clock,
        ),
    )
    return AppendResult(
        source_set_id=source_set.id, subject_id=source_set.subject_id, change_kind=change_kind,
        manifest_hash=run.manifest["manifest_hash"], synthesis_run_id=run.synthesis_run_id,
        proposal_id=outcome.proposal_id, reused=outcome.reused, nothing_new=outcome.nothing_new,
        item_counts=_count_items(outcome.normalized.rows), gate_diagnostics=outcome.gate_diagnostics,
        # The neighbourhood as its manifest records it (match reasons and entity hashes, not its context).
        neighborhood=run.manifest["scope"]["neighborhood"], span_request_count=outcome.answer.span_request_count,
        facet_identity=outcome.facet_identity, **outcome.applied,
    )


def _apply_routine_items(
    root: Path,
    repository: Repository,
    vault: LoadedVault,
    outcome: SynthesisOutcome,
    *,
    auto_apply: bool,
    apply_gate: Callable[[], bool] | None,
    clock: Clock | None,
) -> dict[str, Any]:
    """The append's apply step: which of the proposal's items wait for review, and §10.3's lane, where routine
    span/assessment attachments apply under the vault lock; everything else stays a pending review proposal.
    Returns the fields it adds to the :class:`AppendResult`.

    ``apply_gate`` is read immediately before applying: an automatic build re-reads its kill switches and Undo
    state there."""

    rows, auto_apply_ids = outcome.normalized.rows, outcome.normalized.auto_apply_ids or []
    if outcome.match is None:
        row_by_client = {r["client_item_id"]: r["id"] for r in rows}
        auto_ids = [row_by_client[c] for c in auto_apply_ids if c in row_by_client]
        review_ids = [r["id"] for r in rows if r["id"] not in set(auto_ids)]
    else:
        # The earlier proposal's items: only those still waiting apply or wait.
        waiting = {item["client_item_id"]: item["id"] for item in repository.proposal_items(outcome.proposal_id)
                   if item["decision"] == "pending"}
        auto_ids = [waiting[c] for c in auto_apply_ids if c in waiting]
        review_ids = [item_id for item_id in waiting.values() if item_id not in set(auto_ids)]
    added: dict[str, Any] = {"review_item_ids": review_ids}
    if not (auto_apply and auto_ids and (apply_gate is None or apply_gate())):
        return added

    from learnloop.content.proposals.patches import apply_accepted_items

    snapshot = _snapshot(repository, vault)
    apply_accepted_items(root, outcome.proposal_id, item_ids=auto_ids, clock=clock)
    added["auto_applied_item_ids"] = auto_ids
    vault_after = load_vault(root)
    added["study_map_diff"] = _diff_from_snapshot(repository, vault_after, snapshot, outcome.proposal_id)
    # Post-append near-duplicate facet doctor pass: merge-review only, never
    # auto-merge (§14). Runs after any new_coverage facets have been applied.
    from learnloop.content.synthesis.facet_doctor import near_duplicate_facet_review

    added["merge_review_proposals"] = [
        p.as_dict() for p in near_duplicate_facet_review(vault_after, nominator=GraphNominator.for_review(vault_after))
    ]
    return added

def _run_reconciliation(
    call: _AppendCall, repository, inputs, new_inventories, neighborhood_context, source_set,
    subject_id, change_kind, revision_diff, brief, budgets, *, one_facet_per_skill: bool = False,
):
    context = AppendReconciliationContext(
        source_set_id=source_set.id, subject_id=subject_id, change_kind=change_kind,
        brief=brief, new_inventories=new_inventories, neighborhood=neighborhood_context,
        exam_profile=inputs.exam_profile or {}, revision_diff=revision_diff, resolved_spans=[],
        one_facet_per_skill=one_facet_per_skill,
    )
    result = call(context)
    span_request_count = 0
    requests = [r if isinstance(r, dict) else r.model_dump() for r in getattr(result, "span_requests", []) or []]
    if requests:
        span_request_count = len(requests)
        resolved, _hashes = _resolve_span_requests(
            repository, requests, inputs,
            max_count=budgets.synthesis_span_request_max_count,
            char_cap=budgets.synthesis_span_char_cap,
        )
        context = AppendReconciliationContext(
            source_set_id=source_set.id, subject_id=subject_id, change_kind=change_kind,
            brief=brief, new_inventories=new_inventories, neighborhood=neighborhood_context,
            exam_profile=inputs.exam_profile or {}, revision_diff=revision_diff, resolved_spans=resolved,
            one_facet_per_skill=one_facet_per_skill,
        )
        result = call(context)
    return result, span_request_count


# --- normalization ----------------------------------------------------------


def _normalize_append(reconciliation, inputs, vault, now, *, subject_id,
                      items_off: bool = False, nominator=None, facet_identity_plan=None) -> _Normalized:
    """Map an AppendReconciliation to proposal rows and gate items: the bootstrap normalizer over its new
    coverage, then the append's own item kinds after it, with the client ids §10.3 auto-applies."""

    def d(obj):
        return obj if isinstance(obj, dict) else obj.model_dump()

    # new_coverage reuses the bootstrap normalizer — including its items-off
    # drop guard, which this lane previously bypassed by omission.
    coverage = SourceSetSynthesis(
        concepts=getattr(reconciliation, "concepts", []) or [],
        facets=getattr(reconciliation, "facets", []) or [],
        learning_objects=getattr(reconciliation, "learning_objects", []) or [],
        blueprints=getattr(reconciliation, "blueprints", []) or [],
        practice_items=getattr(reconciliation, "practice_items", []) or [],
    )
    normalized = _normalize(coverage, inputs, vault, now, subject_id=subject_id,
                            items_off=items_off, nominator=nominator,
                            facet_identity_plan=facet_identity_plan)
    rows = list(normalized.rows)
    gate_items = list(normalized.gate_items)
    auto_apply_ids: list[str] = []

    # provenance_link items.
    dropped_diagnostics: list[dict[str, Any]] = []
    for link in getattr(reconciliation, "provenance_links", []) or []:
        obj = d(link)
        client = obj.get("client_item_id") or f"plink_{new_ulid()[:8]}"
        target_type = obj.get("target_entity_type") or "facet"
        target_id = obj.get("target_entity_id") or ""
        problem = _span_problem(obj.get("span") or {}, inputs)
        if problem:
            # A link IS its span: with nothing resolvable to attach, the item
            # is empty. Drop it with a typed review record rather than letting
            # the span/scope/unit gates hard-fail the whole paid run — the same
            # trade the bootstrap normalizer makes for unresolved concepts.
            dropped_diagnostics.append(
                {
                    "gate": "provenance_link_span",
                    "severity": "review",
                    "entity_refs": [client, target_id] if target_id else [client],
                    "message": (
                        f"dropped provenance_link {client!r} for {target_type} "
                        f"{target_id!r}: {problem}"
                    ),
                    "suggested_action": "cite a span id from the new inventories, or rerun the append",
                }
            )
            continue
        relation = obj.get("relation") or _relation_for_intent(obj.get("reconciliation_intent"))
        gate_refs, yaml_refs, span_ids = _span_refs([obj.get("span") or {}], inputs, default_relation=relation)
        ref = yaml_refs[0] if yaml_refs else {}
        # An exam span (its role resolved from the source set) only ever aligns
        # assessment (§4.2).
        if ref.get("role") in ASSESSMENT_ONLY_ROLES:
            relation = "assessment_alignment"
        if relation == "assessment_alignment" and target_type == "facet":
            dropped_diagnostics.append(
                {
                    "gate": "provenance_link_span",
                    "severity": "review",
                    "entity_refs": [client, target_id] if target_id else [client],
                    "message": (
                        f"dropped provenance_link {client!r} for facet {target_id!r}: its span is exam "
                        "material, which aligns assessment and never supports a facet's meaning"
                    ),
                    "suggested_action": "attach exam material to a task blueprint, learning object or practice item",
                }
            )
            continue
        current_hash = compute_target_hash(vault, _hash_type(target_type), target_id)
        payload = {
            "target_entity_type": target_type,
            "target_entity_id": target_id,
            "relation": relation,
            "reconciliation_intent": obj.get("reconciliation_intent") or "span_attach",
            "expected_target_hash": obj.get("expected_target_hash") or current_hash,
            "source_id": ref.get("source_id"),
            "revision_id": ref.get("revision_id"),
            "extraction_id": ref.get("extraction_id"),
            "locator": ref.get("locator"),
            "locator_scheme": ref.get("locator_scheme"),
            "span_hash": ref.get("span_hash"),
            "subject_id": subject_id,
        }
        rows.append(_row("provenance_link", new_ulid(), payload, [], client_id=client, now=now,
                         target_entity_id=target_id, target_entity_type=_target_type(target_type)))
        gate_items.append(
            GateItem(
                client_item_id=client, item_type="provenance_link", operation="create",
                entity_id=None, payload=payload, provenance=gate_refs,
                reconciliation_intent=obj.get("reconciliation_intent"),
            )
        )
        if _auto_applies(payload, gate_refs, vault, current_hash, target_type):
            auto_apply_ids.append(client)

    # notation_mapping items (review-required).
    for mapping in getattr(reconciliation, "notation_mappings", []) or []:
        obj = d(mapping)
        client = obj.get("client_item_id") or f"notation_{new_ulid()[:8]}"
        _gate_refs, yaml_refs, _ = _span_refs([obj.get("span") or {}], inputs, default_relation="support")
        ref = yaml_refs[0] if yaml_refs else {}
        payload = {
            "target_entity_type": obj.get("target_entity_type") or "facet",
            "target_entity_id": obj.get("target_entity_id") or "",
            "canonical_notation": obj.get("canonical_notation") or "",
            "alternate_notation": obj.get("alternate_notation") or "",
            "context": obj.get("context"),
            "source_id": ref.get("source_id"),
            "revision_id": ref.get("revision_id"),
            "locator": ref.get("locator"),
            "subject_id": subject_id,
        }
        rows.append(_row("notation_mapping", new_ulid(), payload, [], client_id=client, now=now))
        gate_items.append(
            GateItem(client_item_id=client, item_type="notation_mapping", operation="create",
                     entity_id=None, payload=payload)
        )

    # source_conflict items (always reviewed).
    conflict_candidates = list(getattr(reconciliation, "conflict_candidates", []) or [])
    for conflict in getattr(reconciliation, "conflicts", []) or []:
        obj = d(conflict)
        client = obj.get("client_item_id") or f"conflict_{new_ulid()[:8]}"
        left = _span_yaml(obj.get("left"), inputs)
        right = _span_yaml(obj.get("right"), inputs)
        payload = {
            "entity_type": obj.get("entity_type") or "facet",
            "entity_id": obj.get("entity_id") or "",
            "statement": obj.get("statement") or "",
            "left": left,
            "right": right,
            "candidate_id": client,
            "subject_id": subject_id,
        }
        rows.append(_row("source_conflict", new_ulid(), payload, [], client_id=client, now=now))
        gate_items.append(
            GateItem(client_item_id=client, item_type="source_conflict", operation="create",
                     entity_id=None, payload=payload)
        )

    # restructure_unlocked items (update/deactivate, review + lock-checked).
    for restructure in getattr(reconciliation, "restructures", []) or []:
        obj = d(restructure)
        client = obj.get("client_item_id") or f"restructure_{new_ulid()[:8]}"
        target_type = obj.get("target_entity_type") or "learning_object"
        target_id = obj.get("target_entity_id") or ""
        operation = obj.get("operation") or "update"
        if target_type == "facet":
            reword = _facet_reword(obj, vault, inputs, operation, target_id)
            refs = [client, target_id] if target_id else [client]
            unresolved = "; ".join(reword.unresolved)
            if reword.payload is None:
                dropped_diagnostics.append(
                    {
                        "gate": reword.gate,
                        "severity": "review",
                        "entity_refs": refs,
                        "message": (
                            f"dropped facet restructure {client!r} of {target_id!r}: {reword.problem}"
                            + (f" (unresolved citations: {unresolved})" if unresolved else "")
                        ),
                        "suggested_action": (
                            "reword a registered facet with an update carrying its new facet_wording and "
                            "the provided spans that support it, or reword it yourself in the Library "
                            "(an owner reword, with an undo); merge facets from the facet inspector"
                        ),
                    }
                )
                continue
            if unresolved:
                dropped_diagnostics.append(
                    {
                        "gate": "facet_restructure",
                        "severity": "review",
                        "entity_refs": refs,
                        "message": (
                            f"facet restructure {client!r} of {target_id!r} kept without the citations "
                            f"that do not resolve: {unresolved}"
                        ),
                        "suggested_action": "check the reword against the spans it still cites",
                    }
                )
            if reword.confirm is not None:
                dropped_diagnostics.append({**reword.confirm, "entity_refs": refs})
            row = _row("facet", target_id, reword.payload, [], client_id=client, now=now,
                       target_entity_id=target_id, target_entity_type="facet")
            row["operation"] = operation
            rows.append(row)
            gate_items.append(
                GateItem(client_item_id=client, item_type="facet", operation=operation,
                         entity_id=target_id, payload=reword.payload, provenance=reword.provenance,
                         reconciliation_intent="restructure_unlocked")
            )
            continue
        payload = dict(obj.get("payload") or {})
        payload["id"] = target_id
        payload["expected_target_hash"] = obj.get("expected_target_hash")
        row = _row(target_type, target_id, payload, [], client_id=client, now=now)
        row["operation"] = operation
        rows.append(row)
        gate_items.append(
            GateItem(client_item_id=client, item_type=target_type, operation=operation,
                     entity_id=target_id, payload=payload, reconciliation_intent="restructure_unlocked")
        )

    # `normalized.edge_diagnostics` carries the bootstrap normalizer's typed review
    # records — concept-edge drops and the D2 facet-mint verdicts. They must ride
    # out to the caller's `gate_diagnostics`: D2's rule is "failure is typed, not
    # silent", and a record dropped here is silent.
    return replace(
        normalized,
        rows=rows,
        gate_items=gate_items,
        conflict_candidates=conflict_candidates,
        non_conflict_dispositions=set(getattr(reconciliation, "non_conflict_dispositions", []) or []),
        edge_diagnostics=[*normalized.edge_diagnostics, *dropped_diagnostics],
        auto_apply_ids=auto_apply_ids,
    )


APPEND = SynthesisMode(
    name="append",
    agent_purpose=APPEND_AGENT_PURPOSE,
    prompt_template="append-reconciliation",
    output_schema="AppendReconciliation",
    prompt_version=append_reconciliation_prompt_version,
    # The neighbourhood's cap is a scaling and safety invariant, recorded even unlimited. ``append_input_ceiling``
    # is a refusal and stays out of the record.
    recorded_budgets=("append_neighborhood_input_tokens", "append_output_tokens"),
    unlimited_recorded_budgets=("append_neighborhood_input_tokens",),
    proposal_purpose=APPEND_PROPOSAL_PURPOSE,
    summary_fallback="append reconciliation for {subject}",
    gate_failure=("append_gate_failed", "Append proposal failed hard quality gates."),
    normalize=_normalize_append,
    append_vocabulary=True,
    facet_action_origin="append",
    keeps_candidate_for_repair=False,
    checks_client_id_collisions=False,
    analyzes_identifiability=False,
    meters_the_model_call=False,
    usage_only_with_a_proposal=True,
    resolves_an_empty_subject=False,
)


def _within_preset(reconciliation: Any, brief: Mapping[str, Any]) -> tuple[Any, list[dict[str, Any]]]:
    """The answer the brief's authoring preset allows, with a review record of what it dropped.

    The narrow-adjunct preset's no-restructure promise is a deterministic boundary, not merely prompt advice:
    every additive candidate is kept and only model-emitted restructure operations are dropped."""

    restructures = list(getattr(reconciliation, "restructures", []) or [])
    if brief.get("authoring_preset") != "narrow_adjunct" or not restructures:
        return reconciliation, []
    if hasattr(reconciliation, "model_copy"):
        reconciliation = reconciliation.model_copy(update={"restructures": []})
    elif isinstance(reconciliation, dict):
        reconciliation = {**reconciliation, "restructures": []}
    return reconciliation, [{
        "gate": "narrow_adjunct",
        "severity": "review",
        "entity_refs": [],
        "message": (
            f"dropped {len(restructures)} model-emitted restructure operation(s): "
            "the enrichment preset permits additive changes only"
        ),
        "suggested_action": "review the additive proposal; use a standard append to restructure",
    }]


@dataclass(frozen=True)
class _FacetReword:
    """A facet restructure, normalized: its proposal payload and the citations the gates judge.

    ``payload`` is ``None`` when it cannot apply, and ``problem`` says why.
    ``unresolved`` names each citation dropped because it does not resolve.
    """

    payload: dict[str, Any] | None
    provenance: list[ProvenanceRef] = field(default_factory=list)
    problem: str | None = None
    unresolved: list[str] = field(default_factory=list)
    #: A ``facet_reword_confirm`` review record when the reword will wait for the owner's confirm.
    confirm: dict[str, Any] | None = None
    #: The review gate a dropped reword is reported under.
    gate: str = "facet_restructure"


def _facet_reword(
    obj: dict[str, Any], vault: LoadedVault, inputs: Any, operation: str, target_id: str,
) -> _FacetReword:
    """Normalize a facet restructure: a reword of a registered facet.

    A facet restructure is a reword (Codex review F2): an ``update`` of a
    registered facet whose new wording arrives in ``facet_wording`` (declared,
    so a strict-schema provider can fill it; the bare ``payload`` dict is read
    too, for a provider that fills it). The meaning fields, the title and the
    worked examples travel (``authority.AUTHORITY_FIELDS``; Codex review of
    the reword confirm, F5), and a blank field keeps the facet's value. The
    apply writes a facet version with an undo when the meaning changes; a
    title or worked-example change only is not a version, but is on the
    facet's history with its undo. ``expected_target_hash`` is stamped from
    the vault the model saw: the neighborhood never shows the model a target
    hash, so its own value can only be a guess, and a guess would refuse
    every accept.

    A reword changes a canonical claim, so it obeys the §4.2 authority matrix
    like a new facet (Codex re-review F6). It cites the provided spans that
    support its new wording (``facet_wording.provenance``):

    * a citation that does not resolve in the source set is dropped, as an
      unresolvable ``provenance_link`` is, rather than hard-failing the run;
    * each citation's role comes from its extraction run, never from the
      model. The gates then judge them: only exam material is an
      ``exam_authority`` hard fail, no semantic-authority role is an
      ``adequate_provenance`` review;
    * a reword with no explanatory support that is not exam-only (left with
      no citation, or citing only notes, problem-set or unknown-role spans)
      is kept, with a ``facet_reword_confirm`` diagnostic: accepting it holds
      it for the owner's one-tap confirm, which shows the wording before and
      after and its sources (owner, 2026-10-13). It used to be dropped
      because exam units never reach the model as text, so an exam-driven
      reword arrives uncited; the confirm shows the owner that it cites
      nothing, and only the owner writes it. A title or worked-example
      change needs no explanatory citation;
    * under the kill switch ``facet_identity.reword_confirm = false`` the
      predecessor rule holds: a reword the chokepoint would refuse is dropped
      here (``facet_restructure``), never kept to fail the accept.

    The citations are added to the facet's ``provenance`` snapshot (the apply
    links them in ``entity_source_links``). An exam citation is recorded as
    ``assessment_alignment``, never as semantic support (§9.3).
    """

    if operation != "update":
        return _FacetReword(None, problem="a facet is retired by a merge, never a deactivate")
    facet = vault.evidence_facets.get(target_id)
    if facet is None:
        return _FacetReword(None, problem="it names no registered facet")
    wording = dict(obj.get("facet_wording") or {})
    loose = dict(obj.get("payload") or {})
    payload: dict[str, Any] = {}
    for name in facet_meaning.AUTHORITY_FIELDS:
        value = wording.get(name)
        if value in (None, "", []):
            value = loose.get(name)
        if value not in (None, "", []):
            payload[name] = value
    current = facet.model_dump(mode="json", exclude_none=False)
    if not facet_meaning.authority_changes(current, {**current, **payload}):
        return _FacetReword(None, problem="it carries no new wording")
    policy = facet_meaning.meaning_policy(vault.config)

    citations = wording.get("provenance") or loose.get("provenance")
    resolved: list[dict[str, Any]] = []
    unresolved: list[str] = []
    exam_unresolved: list[dict[str, Any]] = []
    for span in citations if isinstance(citations, list) else []:
        span = span if isinstance(span, dict) else {}
        problem = _span_problem(span, inputs)
        if problem is None:
            resolved.append(span)
        else:
            label = f"{span.get('extraction_id') or '?'}:{span.get('span_id') or '?'}"
            unresolved.append(f"{label} ({problem})")
            if inputs.resolver is not None and inputs.resolver.exam_material(span):
                # Dropped, it supports nothing, but it is still exam material:
                # the reword is judged with it, so it is never "uncited".
                exam_unresolved.append({key: span.get(key) for key in ("extraction_id", "unit_id", "span_id")})
    gate_refs, yaml_refs, _spans = (_span_refs(resolved, inputs, default_relation="support") if resolved
                                    else ([], [], []))
    if not yaml_refs:
        # Uncited: kept for the owner's confirm at accept (owner, 2026-10-13),
        # never written without it. The facet's provenance is left as it is.
        payload["id"] = target_id
        payload["expected_target_hash"] = compute_target_hash(vault, "facet", target_id)
        support = facet_meaning.contributions(exam_unresolved, label="reword")
        payload["meaning_support"] = facet_meaning.support_entries(support)
        return _checked_reword(target_id, current, payload, [], support, unresolved, inputs, policy)
    snapshot = dict(current.get("provenance") or {})
    source_refs = [dict(ref) for ref in snapshot.get("source_refs") or []]
    seen = {(ref.get("revision_id"), ref.get("locator"), ref.get("relation")) for ref in source_refs}
    for ref in yaml_refs:
        if ref.get("role") in ASSESSMENT_ONLY_ROLES:
            ref["relation"] = "assessment_alignment"
        key = (ref.get("revision_id"), ref.get("locator"), ref.get("relation"))
        if key not in seen:
            seen.add(key)
            source_refs.append(ref)
    payload["provenance"] = {"origin": snapshot.get("origin") or "manual", "source_refs": source_refs}
    payload["id"] = target_id
    payload["expected_target_hash"] = compute_target_hash(vault, "facet", target_id)
    # What the apply judges again, at the facet-meaning chokepoint.
    support = facet_meaning.contributions([*_support_citations(gate_refs), *exam_unresolved], label="reword")
    payload["meaning_support"] = facet_meaning.support_entries(support)
    return _checked_reword(target_id, current, payload, gate_refs, support, unresolved, inputs, policy)


def _checked_reword(
    target_id: str, current: dict[str, Any], payload: dict[str, Any], gate_refs: list[ProvenanceRef],
    support: Any, unresolved: list[str], inputs: Any,
    policy: facet_meaning.MeaningPolicy = facet_meaning.REWORD_CONFIRM,
) -> _FacetReword:
    """A reword, judged in advance by the chokepoint the apply runs again.

    Waiting for the owner's confirm: kept, with a ``facet_reword_confirm``
    review record. Exam-only: when an exam citation the gates see is among
    its refs, the gates hard-fail it; when its only exam material is a
    citation that did not resolve (named under the wrong unit, say), the gates
    cannot see it, so the reword is dropped here (``exam_authority``, review).
    Refused without being confirmable (the kill switch's predecessor rule):
    dropped here (``facet_restructure``), as bootstrap normalization drops a
    refused registered-id candidate.
    """

    check = facet_meaning.check_meaning_write(
        target_id, before=current, after=facet_meaning.overlay(current, payload), registered=True,
        contributions=support, resolver=inputs.resolver, policy=policy,
    )
    if check.code == "exam_authority" and not any(ref.role in ASSESSMENT_ONLY_ROLES for ref in gate_refs):
        return _FacetReword(None, unresolved=unresolved, gate="exam_authority", problem=(
            "it rests on exam material only (cited under a unit that does not hold it, or outside the selected "
            "units): an exam citation only ever aligns assessment (§4.2)"
        ))
    if check.code == "unsupported_reword" and not check.confirmable:
        return _FacetReword(None, unresolved=unresolved, problem=(
            "it cites no span from an explanatory source in the selected units, and "
            "facet_identity.reword_confirm = false refuses it (§4.2)"
        ))
    return _FacetReword(payload, provenance=gate_refs, unresolved=unresolved,
                        confirm=check.diagnostic(entity_refs=[target_id]) if check.confirmable else None)


def _span_problem(span: dict[str, Any], inputs) -> str | None:
    """Why a cited span cannot attach, or None when it can.

    The facet-meaning chokepoint's resolver decides (Codex verification of
    F6): the extraction must be in the source set, the span must resolve, the
    span must lie in the unit it is cited with, and that unit must be one the
    source set selects. A link or reword citation that fails is dropped per
    item rather than failing the run."""

    if inputs.resolver is None:
        return "no source set to resolve it in"
    resolved = inputs.resolver.resolve(dict(span or {}))
    return None if isinstance(resolved, facet_meaning.ResolvedCitation) else resolved.problem


def _relation_for_intent(intent: str | None) -> str:
    return {
        "span_attach": "support",
        "alternate_explanation": "alternate",
        "assessment_alignment": "assessment_alignment",
    }.get(str(intent or ""), "support")


def _hash_type(target_type: str) -> str:
    return "learning_object" if target_type == "task_blueprint" else target_type


def _target_type(target_type: str) -> str:
    valid = {"learning_object", "practice_item", "concept", "concept_edge", "rubric",
             "error_type", "facet", "task_blueprint", "provenance_link", "notation_mapping", "source_conflict"}
    return target_type if target_type in valid else None


def _auto_applies(payload, gate_refs, vault, current_hash, target_type) -> bool:
    """§10.3 auto-apply predicate for a provenance_link.

    span_attach/alternate: target hash still matches, every cited span resolves in
    scope, relation not already present, nothing removed/replaced.
    assessment_alignment: only to task/blueprint metadata or provenance, never to a
    facet semantic contract."""

    relation = payload["relation"]
    if relation not in _AUTO_APPLY_RELATIONS:
        return False
    if not payload.get("locator") or not payload.get("target_entity_id"):
        return False
    if relation == "assessment_alignment":
        return target_type in {"task_blueprint", "learning_object", "practice_item"}
    # expected target hash must still match the live entity (nothing changed).
    expected = payload.get("expected_target_hash")
    if expected is not None and current_hash is not None and expected != current_hash:
        return False
    if current_hash is None:  # target does not exist -> cannot auto-attach
        return False
    # every cited span must have resolved (gate_refs carry validated ids).
    if not gate_refs or any(not r.span_id for r in gate_refs):
        return False
    # Relation-not-already-present + nothing-removed are guaranteed structurally:
    # the entity_source_links insert is INSERT OR IGNORE on the UNIQUE relation key,
    # and the handler only ever inserts a row (never rewrites the target YAML).
    return True


def _span_yaml(span, inputs) -> dict[str, Any]:
    if span is None:
        return {}
    _refs, yaml_refs, _ = _span_refs([span if isinstance(span, dict) else span.model_dump()], inputs, default_relation="support")
    return yaml_refs[0] if yaml_refs else {}


# --- study-map diff snapshot ------------------------------------------------


def _snapshot(repository: Repository, vault: LoadedVault) -> dict[str, Any]:
    return {
        "facets": set(vault.evidence_facets.keys()),
        "links": _link_count(repository),
        "open_conflicts": len(repository.source_conflicts_by_status("open")),
        "stale_links": len(repository.stale_entity_source_links()),
        "notations": len(repository.all_notation_mappings()),
    }


def _link_count(repository: Repository) -> int:
    with repository.connection() as connection:
        return int(connection.execute("SELECT COUNT(*) AS n FROM entity_source_links").fetchone()["n"])


def _diff_from_snapshot(repository, vault_after, before, patch_id) -> dict[str, Any]:
    from learnloop.content.synthesis.study_map_diff import compute_study_map_diff

    return compute_study_map_diff(repository, vault_after, before, patch_id)
