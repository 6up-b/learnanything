"""Learned relatedness and implication: the proposal and its structure (spec_adaptive_difficulty_v1 §5.10, D19).

**The proposal** (``ad-relatedness-v1``): per subject, a frontier LLM on the
field harness's route ``ai.routing.llm_probability_llm`` (empty: the active
provider; Codex on the subscription is ``estimated_only``) proposes the prior
means of two sparse sets of shared terms:

* **soft loadings**: for each item, at most 3 facets of its subject outside
  its own that answering it implies knowledge of, each ``weak`` (0.25),
  ``moderate`` (0.5) or ``strong`` (1.0), their sum capped at 1;
* **couplings**: for each LO, at most 3 related LOs of its subject, with
  strengths in the same vocabulary. A pair is coupled when either side names
  it, at the mean of the two sides' strengths.

It reads exactly the subject's LO titles and summaries, the facets' titles and
descriptions, the concept graph (``relations.yaml`` edges) and prerequisites,
and the stems of the subject's items (:func:`subject_inputs`). It never reads
learner data of any kind, any held-out or exam unit's text, an item derived
from one, or any reference answer (A8): protected items are left out, and the
job's :class:`~learnloop.adaptive_difficulty.sending.SendGuard` re-checks
every item it quotes before each request and each record. Invalid outputs (an
unknown id, a facet of another subject, a self-loading, more than three per
unit) are dropped; a unit left with no valid proposal has none.

Each proposed loading and coupling appends one ``judgment_ledger`` row (task
``ad_relatedness``, judge ``llm``, the strength as ``score``, the rationale,
the run's ``input_hash``), and the run appends one ``ad_relatedness_runs``
receipt naming the units it covered, in one fenced transaction under the
subject's durable claim. An unchanged input hash is never re-asked. Spend:
``adaptive_difficulty.daily_spend_cap_usd`` (owner kind ``ad_relatedness``).

**As of** (§5.10): the subject view is built under one adopted coupling version
(``ad_coupling_versions``). The proposals in force at adoption apply to the
whole history; a later run reaches only what did not exist yet: the loadings of
a new item revision (frozen in its serve-input receipt) and the couplings of a
facet whose coordinates are created after the run. Changing what already
exists is a new coupling version, adopted through the playbook with a shadow
rebuild (:func:`adopt`).

**Never evidence**: nothing here writes evidence, mastery, FSRS or
certification, and nothing is written to the relations registry (KM §8.1).
"""

from __future__ import annotations

from learnloop.adaptive_difficulty.operation import entry

import hashlib
import json
import logging
from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
from typing import Any, Literal

from learnloop.ai.errors import AIInterrupted, AIInvalidOutput, AIProviderUnavailable
from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import SpendLimitExceeded
from learnloop.ai.transport import render_structured_prompt
from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.stores import ad_serving as serving_store

from learnloop.adaptive_difficulty import model as M
from learnloop.adaptive_difficulty import priors as P

LOG = logging.getLogger(__name__)

TASK = "ad_relatedness"
PROMPT_VERSION = "ad-relatedness-v1"
ROUTE = "llm_probability_llm"
OWNER_KIND = "ad_relatedness"
STRENGTHS = {"weak": 0.25, "moderate": 0.5, "strong": 1.0}
STEM_LIMIT = 400
SUMMARY_LIMIT = 600
_CAPS = dict(max_candidates=0, max_pairs=0, max_retries=1, max_calls=2, max_total_tokens=400_000)


# -- the wire models ------------------------------------------------------------------------

class LoadingV1(WireModel):
    facet_id: str
    strength: Literal["weak", "moderate", "strong"]
    why: str


class ItemLoadingsV1(WireModel):
    item_id: str
    loadings: list[LoadingV1]


class RelatedV1(WireModel):
    learning_object_id: str
    strength: Literal["weak", "moderate", "strong"]
    why: str


class LearningObjectCouplingsV1(WireModel):
    learning_object_id: str
    related: list[RelatedV1]


class RelatednessV1(WireModel):
    """The proposal: per item, its loadings; per LO, its related LOs."""

    items: list[ItemLoadingsV1]
    learning_objects: list[LearningObjectCouplingsV1]


# -- the inputs (exactly what the job reads) -----------------------------------------------------

def _excerpt(text: Any, limit: int) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= limit else value[: limit - 1] + "…"


def lo_subject(vault: Any, lo: Any) -> str:
    subjects = list(getattr(lo, "subjects", None) or [])
    return str(subjects[0]) if subjects else "default"


#: The reserved unit a relatedness run records its subject's protection fingerprint under (fix
#: round 12, F38): never an LO or a revision, so no coupling or loading is read from it.
PROTECTION_UNIT = "protection:subject"
#: The reserved unit a run records its whole prompt context under (fix round 13, F38): every item
#: revision the prompt quoted, with its source identity, whether or not it was a proposed unit.
CONTEXT_UNIT = "protection:context"
#: Every reserved unit's prefix: never an LO or a revision.
RESERVED = "protection:"


def reserved(unit: Any) -> bool:
    return str(unit).startswith(RESERVED)


def context_protected(view: Any, connection: Any, context: Any) -> bool:
    """Whether any revision a run's prompt quoted is protected NOW (fix round 13, F38): its item is
    withheld, its revision is (judged by its own sources), or its recorded source identity lies in
    held-out material. The persisted context is judged, not today's items, so replacing, deleting or
    re-scoping an item cannot hide its old revision's protection. Unreadable: protected."""

    try:
        entries = json.loads(context) if isinstance(context, str) else list(context or [])
    except (TypeError, ValueError):
        return True
    for entry in entries:
        if not isinstance(entry, Mapping):
            return True
        if view.withheld(entry.get("item")) or view.revision_hash_withheld(connection, entry.get("revision")):
            return True
        if view.protection.covers_identity(entry.get("sources") or {"practice_item_id": entry.get("item")}):
            return True
    return False


def run_in_force(view: Any, connection: Any, run: Mapping[str, Any], current: str | None) -> bool:
    """Whether a saved run may be used now (F38's blunt rule, rounds 12-13): it was proposed under
    the subject's current protection (``current``: :func:`protection_fingerprint`), it recorded its
    whole prompt context, and nothing in that context is protected now. A run recorded before runs
    carried both (legacy) is never in force."""

    units = run.get("units")
    if current is None or not isinstance(units, Mapping):
        return False
    if units.get(PROTECTION_UNIT) != current or CONTEXT_UNIT not in units:
        return False
    return not context_protected(view, connection, units[CONTEXT_UNIT])


def subject_lo_ids(vault: Any, subject: str) -> set[str]:
    """The active LOs of a subject (the relatedness prompt's scope)."""

    return {lo.id for lo in vault.learning_objects.values()
            if getattr(lo, "status", "active") == "active" and lo_subject(vault, lo) == subject}


def protection_fingerprint(view: Any, connection: Any, lo_ids: Any) -> str | None:
    """The protected material in a subject's prompt context, as one digest (fix round 12, F38):
    each withheld current item or saved revision of the subject's LOs, by item id, revision hash
    and source identity. A run records it at proposal time; a run whose subject's fingerprint has
    changed since is not used (the blunt rule: protecting, or releasing, material in a subject
    resets its learned coupling until the owner re-proposes and re-adopts). None while the
    held-out predicate is unavailable (then nothing is used)."""

    from learnloop.adaptive_difficulty.feature_audit import item_revision
    from learnloop.adaptive_difficulty.outside import source_identity

    if not view.available:
        return None
    scope = {str(lo_id) for lo_id in lo_ids}
    withheld, _visible = view._withheld_and_visible_revisions(connection)
    entries = sorted({json.dumps({"item": str(item.id), "revision": item_revision(item)[0],
                                  "sources": source_identity(item, str(item.id))}, sort_keys=True)
                      for item in withheld if str(getattr(item, "learning_object_id", "")) in scope})
    return hashlib.sha256(json.dumps(entries).encode()).hexdigest()


def stale_judgments(connection: Any, vault: Any, *, view: Any) -> set[str]:
    """The judgments of every run its subject's protection has changed since (F38): what a frozen
    loading naming any of them may not be used for (the replay, fix round 12)."""

    out: set[str] = set()
    fingerprints: dict[str, str | None] = {}
    for run in view.stored(connection, serving_store.RELATEDNESS_RUNS, serving_store.relatedness_runs):
        subject = str(run["subject_id"])
        if subject not in fingerprints:
            fingerprints[subject] = protection_fingerprint(view, connection, subject_lo_ids(vault, subject))
        if not run_in_force(view, connection, run, fingerprints[subject]):
            out.update(str(judgment) for judgment in run["judgment_ids"] or ())
    return out


def lo_facets(view: Any, lo: Any) -> list[str]:
    """The LO's authored facets, else its visible active items' facets, through the operation's
    material view (A8; Codex verify F17's audit, F19): a facet only withheld items name is never
    quoted to a prompt, never steers generation and never enters the replay's structure."""

    return view.lo_facets(lo)


def subjects(vault: Any) -> list[str]:
    return sorted({lo_subject(vault, lo) for lo in vault.learning_objects.values()
                   if getattr(lo, "status", "active") == "active"})


@entry
def subject_inputs(vault: Any, repository: Any, subject: str, *, protected: Any = None) -> dict[str, Any]:
    """Exactly what the proposal reads for one subject: LO and facet text, the concept graph and
    prerequisites, and the stems of the subject's unprotected items. Never learner data, a
    reference answer, or held-out / exam material (A8)."""

    from learnloop.adaptive_difficulty.feature_audit import item_revision
    from learnloop.adaptive_difficulty.material_view import material_view

    view = material_view(vault, repository, protected)
    los = sorted((lo for lo in vault.learning_objects.values()
                  if getattr(lo, "status", "active") == "active" and lo_subject(vault, lo) == subject),
                 key=lambda lo: lo.id)
    lo_ids = {lo.id for lo in los}
    concepts = {lo.concept for lo in los}
    facets: dict[str, dict[str, Any]] = {}
    lo_rows = []
    for lo in los:
        owned = lo_facets(view, lo)
        for facet_id in owned:
            facet = vault.evidence_facets.get(facet_id)
            facets[facet_id] = {"facet_id": facet_id, "title": _excerpt(getattr(facet, "title", None) or facet_id, 200),
                                "description": _excerpt(getattr(facet, "description", None) or "", 300)}
        lo_rows.append({
            "learning_object_id": lo.id, "title": _excerpt(lo.title, 200), "summary": _excerpt(lo.summary, SUMMARY_LIMIT),
            "concept": lo.concept, "facets": owned,
            "prerequisites": sorted(p for p in (lo.prerequisites or []) if p in lo_ids),
        })
    edges = sorted(
        ({"relation": edge.relation_type, "source": edge.source, "target": edge.target}
         for edge in getattr(vault, "edges", []) or []
         if edge.source in concepts | lo_ids and edge.target in concepts | lo_ids),
        key=lambda e: (e["source"], e["target"], e["relation"]),
    )
    items = []
    revisions: dict[str, str] = {}
    for item in view.items(active=True):
        if item.learning_object_id not in lo_ids:
            continue
        content_hash, _json = item_revision(item)
        revisions[str(item.id)] = content_hash
        items.append({
            "item_id": str(item.id), "learning_object_id": item.learning_object_id,
            "facets": sorted({vault.canonical_facet_id(str(f)) for f in item.evidence_facets}),
            "stem": _excerpt(item.prompt, STEM_LIMIT),
        })
    payload = {"subject": subject, "learning_objects": lo_rows, "facets": [facets[f] for f in sorted(facets)],
               "concept_graph": edges, "items": items}
    # Each unit's own fingerprint (§5.10 "When"): an LO's couplings depend on its text, its facets'
    # text, its prerequisites and the relations touching it; an item revision is its content hash.
    unit_hashes: dict[str, str] = {}
    for row in lo_rows:
        lo = row["learning_object_id"]
        own = {"lo": row, "facets": [facets[f] for f in row["facets"] if f in facets],
               "edges": [e for e in edges if lo in (e["source"], e["target"]) or row["concept"] in
                         (e["source"], e["target"])]}
        unit_hashes[f"lo:{lo}"] = hashlib.sha256(json.dumps(own, sort_keys=True).encode()).hexdigest()
    for item_id, content_hash in revisions.items():
        unit_hashes[f"rev:{content_hash}"] = content_hash
    # The subject's protection fingerprint (F38): recorded on every run, never quoted to the model.
    from contextlib import closing

    from learnloop.db.connection import connect

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        unit_hashes[PROTECTION_UNIT] = str(protection_fingerprint(view, connection, lo_ids))
    # The whole prompt context, persisted on the run (fix round 13, F38): every quoted revision and
    # its source identity, the proposed units and the context alike. Never quoted to the model.
    from learnloop.adaptive_difficulty.outside import source_identity

    quoted = {str(item.id): item for item in view.items(active=True) if item.learning_object_id in lo_ids}
    unit_hashes[CONTEXT_UNIT] = json.dumps(sorted(
        ({"item": item_id, "revision": revisions[item_id], "sources": source_identity(quoted[item_id], item_id)}
         for item_id in revisions if item_id in quoted), key=lambda entry: entry["item"]), sort_keys=True)
    return {"payload": payload, "revisions": revisions,
            "input_hash": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
            "item_ids": [row["item_id"] for row in items], "unit_hashes": unit_hashes}


def _latest_unit_hashes(runs: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    """The fingerprint each unit had at its latest ok run (a run's ``units`` maps unit -> hash)."""

    latest: dict[str, str] = {}
    for run in runs:
        if run.get("status") != "ok":
            continue
        units = run.get("units") or {}
        if isinstance(units, Mapping):
            latest.update({str(unit): str(value) for unit, value in units.items()})
        else:
            latest.update({str(unit): "" for unit in units})
    return latest


def touched_units(inputs: Mapping[str, Any], runs: Sequence[Mapping[str, Any]], *,
                  in_force: Callable[[Mapping[str, Any]], bool] | None = None) -> list[str]:
    """The units whose fingerprint changed (or that are new) since their latest ok run: all of
    them when the subject has none.

    Only runs in force count (F38's blunt rule, rounds 12-13; ``in_force``: :func:`run_in_force`
    bound to the operation's view, else the recorded subject fingerprint alone): a run out of use
    neither answers for a unit nor spares it a new proposal. When protection changed since every
    run, every unit is proposed again."""

    current = inputs["unit_hashes"].get(PROTECTION_UNIT)
    fresh = [run for run in runs
             if isinstance(run.get("units"), Mapping) and run["units"].get(PROTECTION_UNIT) == current
             and (in_force is None or in_force(run))]
    latest = _latest_unit_hashes(fresh)
    return sorted(unit for unit, value in inputs["unit_hashes"].items()
                  if not reserved(unit) and latest.get(unit) != value)


def focus(inputs: Mapping[str, Any], units: Sequence[str]) -> dict[str, Any]:
    """The inputs restricted to proposing for ``units`` only (the whole subject stays as context;
    the input hash covers the focus, so an unchanged request is never re-asked)."""

    chosen = set(units)
    los = [row["learning_object_id"] for row in inputs["payload"]["learning_objects"] if f"lo:{row['learning_object_id']}" in chosen]
    items = [item_id for item_id in inputs["item_ids"] if f"rev:{inputs['revisions'][item_id]}" in chosen]
    payload = {**inputs["payload"], "propose_for": {"learning_objects": los, "items": items}}
    return {**inputs, "payload": payload, "focus_learning_objects": los, "focus_items": items,
            "input_hash": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()}


def prompt(inputs: Mapping[str, Any]) -> str:
    return render_structured_prompt("Propose which topics are related and what answering each item implies",
                                    PROMPT_VERSION, {
        "instructions": (
            "You are given one subject's topics (learning objects), their facets, the concept graph and the "
            "stems of the subject's practice items. For each item, name at most 3 facets of this subject OUTSIDE "
            "the item's own facets that answering the item correctly implies knowledge of (for example a "
            "prerequisite's facets), each weak, moderate or strong; name none when nothing beyond its own facets "
            "is implied. For each learning object, name at most 3 other learning objects of this subject most "
            "related to it, each weak, moderate or strong. Use only the ids given. Give a one-line reason for each. "
            "Propose only for the items and learning objects listed in propose_for; the rest is context."
        ),
        "state": dict(inputs["payload"]),
    })


# -- validation --------------------------------------------------------------------------

@dataclass
class Proposal:
    loadings: dict[str, dict[str, tuple[float, str]]] = field(default_factory=dict)  # item id -> facet -> (Q, why)
    couplings: dict[str, dict[str, tuple[float, str]]] = field(default_factory=dict)  # LO -> M -> (C, why)
    dropped: list[dict[str, Any]] = field(default_factory=list)


def validate(answer: RelatednessV1 | Mapping[str, Any], inputs: Mapping[str, Any]) -> Proposal:
    """Drop what fails validation: unknown ids, another subject's facet, self-loadings or
    self-couplings, more than three per unit; the loadings' sum capped at 1."""

    if isinstance(answer, Mapping):
        answer = RelatednessV1.model_validate(dict(answer))
    payload = inputs["payload"]
    facets = {row["facet_id"] for row in payload["facets"]}
    los = {row["learning_object_id"] for row in payload["learning_objects"]}
    own = {row["item_id"]: set(row["facets"]) for row in payload["items"]}
    proposal = Proposal()
    wanted_items = set(inputs.get("focus_items", own))
    wanted_los = set(inputs.get("focus_learning_objects", los))
    for entry in answer.items:
        if entry.item_id not in own:
            proposal.dropped.append({"unit": entry.item_id, "why": "unknown_item"})
            continue
        if entry.item_id not in wanted_items:
            proposal.dropped.append({"unit": entry.item_id, "why": "not_asked"})
            continue
        kept: dict[str, tuple[float, str]] = {}
        for loading in entry.loadings:
            if loading.facet_id not in facets:
                proposal.dropped.append({"unit": entry.item_id, "facet": loading.facet_id, "why": "unknown_facet"})
            elif loading.facet_id in own[entry.item_id]:
                proposal.dropped.append({"unit": entry.item_id, "facet": loading.facet_id, "why": "self_loading"})
            elif loading.facet_id in kept:
                proposal.dropped.append({"unit": entry.item_id, "facet": loading.facet_id, "why": "duplicate"})
            elif len(kept) >= P.MAX_LOADINGS:
                proposal.dropped.append({"unit": entry.item_id, "facet": loading.facet_id, "why": "over_cap"})
            else:
                kept[loading.facet_id] = (STRENGTHS[loading.strength], _excerpt(loading.why, 300))
        total = sum(q for q, _why in kept.values())
        if total > 1.0:
            kept = {f: (q / total, why) for f, (q, why) in kept.items()}
        if kept:
            proposal.loadings[entry.item_id] = kept
    for entry in answer.learning_objects:
        if entry.learning_object_id not in los:
            proposal.dropped.append({"unit": entry.learning_object_id, "why": "unknown_learning_object"})
            continue
        if entry.learning_object_id not in wanted_los:
            proposal.dropped.append({"unit": entry.learning_object_id, "why": "not_asked"})
            continue
        kept = {}
        for related in entry.related:
            if related.learning_object_id not in los:
                proposal.dropped.append({"unit": entry.learning_object_id, "lo": related.learning_object_id,
                                         "why": "unknown_learning_object"})
            elif related.learning_object_id == entry.learning_object_id:
                proposal.dropped.append({"unit": entry.learning_object_id, "why": "self_coupling"})
            elif related.learning_object_id in kept:
                proposal.dropped.append({"unit": entry.learning_object_id, "lo": related.learning_object_id,
                                         "why": "duplicate"})
            elif len(kept) >= P.MAX_COUPLED:
                proposal.dropped.append({"unit": entry.learning_object_id, "lo": related.learning_object_id,
                                         "why": "over_cap"})
            else:
                kept[related.learning_object_id] = (STRENGTHS[related.strength], _excerpt(related.why, 300))
        if kept:
            proposal.couplings[entry.learning_object_id] = kept
    return proposal


# -- the job --------------------------------------------------------------------------------

@dataclass
class ProposalOutcome:
    subject: str
    status: str
    run_id: str | None = None
    judgments: int = 0
    reason: str | None = None
    input_hash: str | None = None
    dropped: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {"subject": self.subject, "status": self.status, "run_id": self.run_id, "judgments": self.judgments,
                "reason": self.reason, "input_hash": self.input_hash, "dropped": self.dropped}


def protection_identity(inputs: Mapping[str, Any]) -> str:
    """The run's protection, as one digest: the subject's fingerprint and the whole persisted prompt
    context (fix round 13, F45). Part of the run's and the claim's identity, never of the prompt."""

    hashes = inputs.get("unit_hashes") or {}
    return hashlib.sha256(json.dumps([hashes.get(PROTECTION_UNIT), hashes.get(CONTEXT_UNIT)]).encode()).hexdigest()


def run_key(subject: str, input_hash: str, protection: str | None = None) -> str:
    """A run's identity: the subject, the prompt's hash and (fix round 13, F45) its protection
    identity, so a run proposed under other protection never answers for a new request."""

    return f"{subject}:{input_hash}" + (f":{protection}" if protection else "")


def claim_key(subject: str, input_hash: str, protection: str | None = None) -> str:
    return f"ad_relatedness:{subject}:{input_hash}" + (f":{protection}" if protection else "")


def _client(vault: Any, injected: Any | None) -> tuple[Any | None, str | None]:
    from learnloop.adaptive_difficulty import spend as ad_spend
    from learnloop.practice_index.paid import plan_route, resolve_client

    if injected is not None:
        return injected, None
    if ad_spend.models_off():
        return None, "models_off"
    return resolve_client(vault, plan_route(vault, ROUTE))  # type: ignore[arg-type]


def coupling_on(config: Any) -> bool:
    from learnloop.adaptive_difficulty.successor import switch_on

    return switch_on(config, "learned_coupling")


@entry
def propose_subject(vault: Any, repository: Any, subject: str, *, client: Any = None, clock: Clock | None = None,
                    fence: Any = None, live_vault: Callable[[], Any] | None = None,
                    protected: Any = None) -> ProposalOutcome:
    """One subject's proposal, under its durable claim; never with ``learned_coupling`` off."""

    from learnloop.adaptive_difficulty import spend as ad_spend
    from learnloop.adaptive_difficulty.claims import LeaseLost, ReceiptWriteFailed, claimed
    from learnloop.adaptive_difficulty.sending import ProtectedContent, SendGuard, ask_llm, refusal_status
    from learnloop.practice_index.paid import plan_route

    outcome = ProposalOutcome(subject, "disabled")
    if not coupling_on(vault.config):
        return outcome
    from learnloop.adaptive_difficulty.material_view import material_view

    view = material_view(vault, repository, protected)
    if not view.available:
        # Fail closed before any work is prepared (Codex verify F32): with the held-out predicate
        # unavailable nothing about the subject is assembled, claimed or sent.
        outcome.status, outcome.reason = "unavailable", view.reason
        return outcome
    whole = subject_inputs(vault, repository, subject, protected=view)
    if not whole["payload"]["learning_objects"]:
        outcome.status = "empty"
        return outcome
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        runs = view.stored(connection, serving_store.RELATEDNESS_RUNS, serving_store.relatedness_runs,
                           subject_id=subject)
        current = whole["unit_hashes"].get(PROTECTION_UNIT)
        live = {run["id"] for run in runs if run_in_force(view, connection, run, current)}
    # Only what changed is re-proposed (§5.10 "When"); a first run proposes every unit.
    units = touched_units(whole, runs, in_force=lambda run: run["id"] in live)
    if not units:
        outcome.status = "current"
        outcome.input_hash = whole["input_hash"]
        return outcome
    inputs = focus(whole, units)
    outcome.input_hash = inputs["input_hash"]
    protection = protection_identity(inputs)
    key = run_key(subject, inputs["input_hash"], protection)
    # A stale successful run never satisfies the duplicate check (F45): only a run in force does.
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        current = inputs["unit_hashes"].get(PROTECTION_UNIT)
        if any(run["run_key"] == key and run["status"] == "ok" and run_in_force(view, connection, run, current)
               for run in runs):
            outcome.status = "current"
            return outcome
    llm, why = _client(vault, client)
    if llm is None:
        outcome.status, outcome.reason = "unavailable", why
        return outcome
    # Every quoted item is guarded (the whole subject's stems are context in the prompt).
    items = [item for item in (view.item(item_id) for item_id in inputs["item_ids"]) if item is not None]
    try:
        with claimed(repository, claim_key(subject, inputs["input_hash"], protection), fence=fence) as worker:
            if worker is None:
                outcome.status = "busy"
                return outcome
            send = SendGuard(vault, repository, items=items, protected=view.protection, live_vault=live_vault)
            route = plan_route(vault, ROUTE, llm)  # type: ignore[arg-type]
            price = vault.config.adaptive_difficulty.price_per_million
            if route.billing != "subscription" and price is None:
                outcome.status, outcome.reason = "refused_spend", (
                    "a metered llm_probability_llm route needs adaptive_difficulty.price_per_million")
                return outcome
            envelope = ad_spend.ad_envelope(vault, worker.base, clock=clock)
            text = prompt(inputs)
            try:
                worker.require_live()
                answer, calls = ask_llm(send, route, llm, price=price, repository=worker.repository, caps=_CAPS,
                                        owner_kind=OWNER_KIND, owner_id=key, purpose=TASK, prompt=text,
                                        result_model=RelatednessV1, metadata={"owner_id": key}, envelope=envelope)
            except ProtectedContent as exc:
                outcome.status, outcome.reason = refusal_status(exc), str(exc)[:200]
                return outcome
            except ReceiptWriteFailed as exc:
                outcome.status, outcome.reason = "failed", str(exc)[:200]
                return outcome
            except (AIInterrupted, LeaseLost):
                raise
            except SpendLimitExceeded as exc:
                outcome.status, outcome.reason = "refused_spend", str(exc)[:200]
                return outcome
            except (AIProviderUnavailable, AIInvalidOutput, TimeoutError, ValueError) as exc:
                outcome.status, outcome.reason = "failed", type(exc).__name__
                return outcome
            proposal = validate(answer, inputs)
            model = str(calls.last_resolved_model or getattr(llm, "model", None) or route.model or "unknown")
            try:
                generation = send.check("record")
            except ProtectedContent as exc:
                outcome.status, outcome.reason = refusal_status(exc), str(exc)[:200]
                return outcome
            try:
                run_id, written = _record(worker.repository, subject, inputs, proposal, model=model,
                                          created_at=utc_now_iso(clock),
                                          admit=lambda: send.confirm(generation, "record"))
            except ProtectedContent as exc:
                outcome.status, outcome.reason = refusal_status(exc), str(exc)[:200]
                return outcome
            outcome.status, outcome.run_id, outcome.judgments = "ok", run_id, written
            outcome.dropped = len(proposal.dropped)
    except LeaseLost:
        outcome.status = "stale"
    return outcome


def _record(repository: Any, subject: str, inputs: Mapping[str, Any], proposal: Proposal, *, model: str,
            created_at: str, admit: Callable[[], None]) -> tuple[str | None, int]:
    from learnloop.db.stores.judgments import append_judgment

    key = run_key(subject, inputs["input_hash"], protection_identity(inputs))
    units: dict[str, str] = {}
    ids: list[str] = []
    focus_los = set(inputs.get("focus_learning_objects", [r["learning_object_id"] for r in inputs["payload"]["learning_objects"]]))
    focus_items = set(inputs.get("focus_items", inputs["item_ids"]))
    units[PROTECTION_UNIT] = str(inputs["unit_hashes"].get(PROTECTION_UNIT))
    units[CONTEXT_UNIT] = str(inputs["unit_hashes"].get(CONTEXT_UNIT, "[]"))
    with repository.atomic():
        admit()
        connection = repository.connection()
        for row in inputs["payload"]["learning_objects"]:
            lo = row["learning_object_id"]
            if lo not in focus_los:
                continue
            units[f"lo:{lo}"] = inputs["unit_hashes"][f"lo:{lo}"]
            for other, (strength, why) in sorted(proposal.couplings.get(lo, {}).items()):
                ids.append(append_judgment(
                    connection, task=TASK, left_kind="learning_object", left_id=lo, right_kind="learning_object",
                    right_id=other, judge="llm", judge_model=model, prompt_version=PROMPT_VERSION,
                    input_hash=str(inputs["input_hash"]), verdict=f"{strength:g}", score=float(strength),
                    rationale=json.dumps({"run_key": key, "subject": subject, "why": why}, sort_keys=True),
                    created_at=created_at))
        for item_id in inputs["item_ids"]:
            if item_id not in focus_items:
                continue
            content_hash = inputs["revisions"][item_id]
            units[f"rev:{content_hash}"] = content_hash
            for facet, (strength, why) in sorted(proposal.loadings.get(item_id, {}).items()):
                ids.append(append_judgment(
                    connection, task=TASK, left_kind="practice_item_revision", left_id=content_hash,
                    right_kind="facet", right_id=facet, judge="llm", judge_model=model,
                    prompt_version=PROMPT_VERSION, input_hash=str(inputs["input_hash"]),
                    verdict=f"{strength:g}", score=float(strength),
                    rationale=json.dumps({"run_key": key, "subject": subject, "item_id": item_id, "why": why},
                                         sort_keys=True),
                    created_at=created_at))
        from learnloop.adaptive_difficulty.operation import own_write

        with own_write(serving_store.RELATEDNESS_RUNS):
            run_id = serving_store.insert_relatedness_run(connection, {
                "run_key": key, "subject_id": subject, "input_hash": str(inputs["input_hash"]), "units": units,
                "judgment_ids": ids, "status": "ok", "prompt_version": PROMPT_VERSION, "judge_model": model,
                "created_at": created_at,
            })
    return run_id, len(ids)


def _ledger(connection: Any, table: str, reader: Callable[..., Any], **kwargs: Any) -> list[dict[str, Any]]:
    """AD's own run ledgers: through the operation's view inside one, else as stored (the owner's
    ``adopt`` command runs outside any operation and reads no learner data)."""

    from learnloop.adaptive_difficulty.operation import current

    op = current()
    return op.view.stored(connection, table, reader, **kwargs) if op is not None else reader(connection, **kwargs)


class ReinterpretationNeedsShadow(ValueError):
    """A later coupling version reinterprets what exists: shadow-rebuild report first (§5.10, §11.1)."""


def candidate_version(connection: Any, subject: str) -> dict[str, Any] | None:
    """The coupling version adopting would write now: every unit's latest ok run."""

    runs = [run for run in _ledger(connection, serving_store.RELATEDNESS_RUNS, serving_store.relatedness_runs,
                                   subject_id=subject) if run["status"] == "ok"]
    if not runs:
        return None
    latest: dict[str, str] = {}
    for run in runs:
        for unit in run["units"]:
            latest[unit] = run["id"]
    run_ids = sorted(set(latest.values()))
    versions = [row for row in _ledger(connection, serving_store.COUPLING_VERSIONS, serving_store.coupling_versions)
                if row["subject_id"] == subject]
    number = 1 + max((int(row["version"]) for row in versions), default=0)
    digest = hashlib.sha256(json.dumps({"subject": subject, "runs": run_ids}, sort_keys=True).encode()).hexdigest()
    return {"subject_id": subject, "version": number, "coupling_version": f"{subject}:v{number}:{digest[:16]}",
            "run_ids": run_ids, "existing_versions": len(versions)}


def adopt(repository: Any, subject: str, *, adopted_by: str, note: str | None = None,
          clock: Clock | None = None, confirm_reinterpretation: bool = False) -> dict[str, Any] | None:
    """Adopt the proposals now in force for ``subject`` as its next coupling version.

    The first version (at the successor's tag) applies to the whole history by
    one rebuild. A later one reinterprets what exists: it goes through the
    playbook's shadow rebuild first (:func:`shadow_report`), and is refused
    unless ``confirm_reinterpretation`` says the owner read it (§5.10, §11.1)."""

    with repository.atomic():
        connection = repository.connection()
        row = candidate_version(connection, subject)
        if row is None:
            return None
        if row.pop("existing_versions") and not confirm_reinterpretation:
            raise ReinterpretationNeedsShadow(
                f"{subject} already has a coupling version: a new one reinterprets the history; read its shadow "
                "report (learnloop ad relatedness --adopt --shadow) and confirm the reinterpretation")
        row.update({"adopted_by": adopted_by, "note": note, "adopted_at": utc_now_iso(clock)})
        row["id"] = serving_store.insert_coupling_version(connection, row)
    return row


@entry
def shadow_report(vault: Any, repository: Any, subject: str) -> dict[str, Any]:
    """What adopting the candidate version would change, computed in memory (the playbook's shadow
    rebuild for a reinterpretation): the subject view's state hash and every attempt whose
    subject-view trace moves. Writes nothing; zero model calls."""

    from learnloop.adaptive_difficulty import replay as RP

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        candidate = candidate_version(connection, subject)
        settings = RP.ReplaySettings.from_config(vault.config)
        from learnloop.adaptive_difficulty.material_view import material_view

        view = material_view(vault, repository)
        current = RP.run(RP.load_events(connection, vault, repository, settings=settings, view=view), settings)
        if candidate is None:
            return {"subject": subject, "candidate": None, "changed": False}
        events = RP.load_events(connection, vault, repository, settings=settings, view=view)
        events.structure = load_structure(connection, vault, view=view, coupled=settings.coupling,
                                          override={subject: {**candidate, "adopted_at": utc_now_iso()}})
        shadow = RP.run(events, settings)
    before = {row["attempt_id"]: row for row in current.trace if row["view"] == RP.VIEW_SUBJECT}
    after = {row["attempt_id"]: row for row in shadow.trace if row["view"] == RP.VIEW_SUBJECT}
    moved = sorted(attempt for attempt in set(before) | set(after) if before.get(attempt) != after.get(attempt))
    return {"subject": subject, "candidate": candidate.get("coupling_version"),
            "state_hash": [current.subject.bank.state_hash(), shadow.subject.bank.state_hash()],
            "changed": current.subject.bank.state_hash() != shadow.subject.bank.state_hash(),
            "attempts_moved": moved}


# -- the structure the replayer reads ----------------------------------------------------------

def _stamp(value: Any) -> float:
    parsed = parse_utc(str(value)) if value else None
    return parsed.timestamp() / 86400.0 if parsed is not None else float("-inf")


@dataclass
class _UnitProposal:
    at: float  # -inf: in force from the start (the adopted version)
    values: dict[str, float]


class VaultStructure(M.Structure):
    """The relatedness in force, as of the replay's current time (``now``, in days).

    The adopted version's proposals hold from the start; a later run's hold from its
    write time, so they reach only coordinates created after it (§5.10 "As of")."""

    def __init__(self, *, facet_los: Mapping[str, Sequence[str]], lo_facets: Mapping[str, Sequence[str]],
                 couplings: Mapping[str, Sequence[_UnitProposal]] | None = None,
                 loadings: Mapping[str, Sequence[_UnitProposal]] | None = None,
                 versions: Mapping[str, str] | None = None) -> None:
        self.facet_los = {f: tuple(sorted(set(los))) for f, los in facet_los.items()}
        self.lo_facets = {lo: tuple(fs) for lo, fs in lo_facets.items()}
        self._couplings = {lo: sorted(props, key=lambda p: p.at) for lo, props in (couplings or {}).items()}
        self._loadings = {rev: sorted(props, key=lambda p: p.at) for rev, props in (loadings or {}).items()}
        self.versions = dict(versions or {})
        self.now = float("inf")

    @classmethod
    def fixed(cls, *, facet_los: Mapping[str, Sequence[str]], lo_facets: Mapping[str, Sequence[str]],
              couplings: Mapping[str, Mapping[str, float]] | None = None,
              loadings: Mapping[str, Mapping[str, float]] | None = None) -> "VaultStructure":
        """A structure whose proposals hold from the start (a synthetic vault's, ``learnloop.sim``):
        ``couplings`` LO -> {LO: C}, ``loadings`` revision -> {facet: Q}."""

        return cls(facet_los=facet_los, lo_facets=lo_facets,
                   couplings={lo: [_UnitProposal(float("-inf"), dict(values))]
                              for lo, values in (couplings or {}).items()},
                   loadings={rev: [_UnitProposal(float("-inf"), dict(values))]
                             for rev, values in (loadings or {}).items()},
                   versions={"synthetic": "fixed"})

    @staticmethod
    def _in_force(props: Sequence[_UnitProposal], at: float) -> dict[str, float]:
        chosen: dict[str, float] = {}
        for prop in props:
            if prop.at <= at:
                chosen = prop.values
        return chosen

    def named(self, lo: str, at: float | None = None) -> dict[str, float]:
        return self._in_force(self._couplings.get(lo, ()), self.now if at is None else at)

    def coupling(self, lo: str, at: float | None = None) -> dict[str, float]:
        """Symmetrized strengths ``C_{LM}``: the mean of the two sides (0 for a side that names none)."""

        at = self.now if at is None else at
        own = self.named(lo, at)
        partners = set(own)
        for other in self._couplings:
            if other != lo and lo in self.named(other, at):
                partners.add(other)
        out = {}
        for other in sorted(partners):
            value = 0.5 * (own.get(other, 0.0) + self.named(other, at).get(lo, 0.0))
            if value > 0:
                out[other] = value
        # Sparsity (§5.10 safeguard 1): at most 3 coupled LOs per LO, the strongest, ties by id
        # (symmetrizing can give an LO more partners than it named).
        kept = sorted(out.items(), key=lambda kv: (-kv[1], kv[0]))[:P.MAX_COUPLED]
        return dict(sorted(kept))

    def loadings(self, content_hash: str | None, at: float | None = None) -> dict[str, float]:
        if not content_hash:
            return {}
        return dict(self._in_force(self._loadings.get(content_hash, ()), self.now if at is None else at))

    def _partners(self, facet: str) -> dict[str, float]:
        los = self.facet_los.get(facet, ())
        partners: dict[str, float] = {}
        for lo in los:
            for other, strength in self.coupling(lo).items():
                if other in los:
                    continue
                partners[other] = max(partners.get(other, 0.0), strength)
        return partners

    def _regression(self, facet: str, name_for: Callable[[str], str], existing: Callable[[str], bool]) -> M.Regression:
        regressors: list[str] = []
        raw: list[float] = []
        total = 0.0
        for other, strength in sorted(self._partners(facet).items()):
            present = [g for g in self.lo_facets.get(other, ()) if g != facet and existing(name_for(g))]
            if not present:
                continue
            total += strength
            for g in present:
                regressors.append(name_for(g))
                raw.append(strength / len(present))
        return M.Regression(tuple(regressors), tuple(raw), total)

    def facet_regression(self, facet: str, existing: Callable[[str], bool]) -> M.Regression:
        return self._regression(facet, M.facet_name, existing)

    def cell_regression(self, facet: str, capability: str, existing: Callable[[str], bool]) -> M.Regression:
        return self._regression(facet, lambda g: M.cell_name(g, capability), existing)

    def coupled_facets(self, facet: str) -> tuple[str, ...]:
        out: list[str] = []
        for other in sorted(self._partners(facet)):
            out.extend(g for g in self.lo_facets.get(other, ()) if g != facet)
        return tuple(dict.fromkeys(out))


def load_structure(connection: Any, vault: Any, *, view: Any, coupled: bool = True,
                   override: Mapping[str, Mapping[str, Any]] | None = None) -> VaultStructure:
    """The relatedness in force for the replay: the adopted versions' runs from the start,
    later runs from their write time. With ``coupled`` false (``learned_coupling`` off) none.
    ``override`` (the shadow report) replaces a subject's adopted version by a candidate.
    ``view``: the operation's material view, whose facet maps name no facet only withheld items
    name (Codex verify F19), and through which every saved loading is revalidated (F38)."""

    facet_to_los, lo_to_facets = view.facet_maps()
    if not coupled or not serving_store.has_table(connection, serving_store.COUPLING_VERSIONS):
        return VaultStructure(facet_los=facet_to_los, lo_facets=lo_to_facets)
    adopted: dict[str, dict[str, Any]] = {}
    for row in view.stored(connection, serving_store.COUPLING_VERSIONS, serving_store.coupling_versions):
        current = adopted.get(row["subject_id"])
        if current is None or int(row["version"]) > int(current["version"]):
            adopted[row["subject_id"]] = row
    for subject, row in (override or {}).items():
        adopted[subject] = dict(row)
    if not adopted:
        return VaultStructure(facet_los=facet_to_los, lo_facets=lo_to_facets)
    judgments = {str(row["id"]): (row["id"], row["left_kind"], row["left_id"], row["right_kind"], row["right_id"],
                                  row["score"]) for row in view.rows(connection, "judgment_ledger", "task = ?", (TASK,))}
    couplings: dict[str, list[_UnitProposal]] = {}
    loadings: dict[str, list[_UnitProposal]] = {}
    versions: dict[str, str] = {}
    for subject, version in adopted.items():
        versions[subject] = str(version["coupling_version"])
        base_runs = set(version["run_ids"])
        adopted_at = _stamp(version["adopted_at"])
        # The subject's protection now (F38's blunt rule): a run proposed under a different one,
        # or recorded before runs carried one, is not used at all, its couplings and loadings both.
        current = protection_fingerprint(view, connection, subject_lo_ids(vault, subject))
        for run in view.stored(connection, serving_store.RELATEDNESS_RUNS, serving_store.relatedness_runs,
                               subject_id=subject):
            if run["status"] != "ok":
                continue
            if not run_in_force(view, connection, run, current):
                continue
            if run["id"] in base_runs:
                at = float("-inf")
            elif _stamp(run["created_at"]) > adopted_at:
                at = _stamp(run["created_at"])
            else:
                continue  # an older run superseded at adoption
            per_unit: dict[str, dict[str, float]] = {unit: {} for unit in run["units"] if not reserved(unit)}
            for judgment_id in run["judgment_ids"]:
                row = judgments.get(str(judgment_id))
                if row is None:
                    continue
                _id, left_kind, left_id, _right_kind, right_id, score = row
                unit = f"lo:{left_id}" if left_kind == "learning_object" else f"rev:{left_id}"
                per_unit.setdefault(unit, {})[str(right_id)] = float(score or 0.0)
            for unit, values in per_unit.items():
                kind, ident = unit.split(":", 1)
                if kind != "lo":
                    # A saved loading is revalidated now (Codex verify F38, fix round 11): a withheld
                    # revision (its support) has no unit at all, and no loading lands on a facet only
                    # withheld material names. The judgment ledger itself is never changed.
                    if view.revision_hash_withheld(connection, ident):
                        continue
                    values = view.visible_loadings(connection, ident, values)
                target = couplings if kind == "lo" else loadings
                target.setdefault(ident, []).append(_UnitProposal(at, values))
    return VaultStructure(facet_los=facet_to_los, lo_facets=lo_to_facets, couplings=couplings, loadings=loadings,
                          versions=versions)


__all__ = [
    "OWNER_KIND",
    "PROMPT_VERSION",
    "CONTEXT_UNIT",
    "PROTECTION_UNIT",
    "Proposal",
    "ProposalOutcome",
    "ReinterpretationNeedsShadow",
    "ROUTE",
    "RelatednessV1",
    "STRENGTHS",
    "TASK",
    "VaultStructure",
    "adopt",
    "candidate_version",
    "load_structure",
    "lo_facets",
    "lo_subject",
    "prompt",
    "propose_subject",
    "context_protected",
    "protection_fingerprint",
    "protection_identity",
    "run_in_force",
    "stale_judgments",
    "shadow_report",
    "subject_inputs",
    "subjects",
    "focus",
    "touched_units",
    "validate",
]
