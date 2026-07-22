"""P3 slice 3, step 8 -- learner Q+A authoring, formulation coach, and in-review
maintenance (spec_p3_reader_integration §9, design B step 8).

The Q+A flow (§9.1): from an optional annotation/span the learner writes the
question AND the answer. This content PERSISTS BEFORE any AI assistance. One
confirmation creates a learner-authored P1 card + pinned surface under an explicit
commitment, composing the LANDED P1 substrate (commitments + activity card versions
+ card lineage) -- never a parallel authoring path. The learner's exact surface
(verbatim question/answer) is preserved on the card contract.

The formulation coach (§9.2) is a NON-BLOCKING scale (novice/middle/expert). Its
lint NEVER prevents acceptance; it records the learner's accept/edit/dismiss for
future corpus analysis, not a live learned policy. It runs AFTER the Q+A is durable.

Fluid maintenance (§9.3) dispatches to P1 lineage classification: already-administered
versions stay immutable; split/merge never blindly transfers scheduling/certification;
a cosmetic edit retains card state ONLY through the P1 classifier. An AI sibling never
impersonates learner/source authorship.
"""

from __future__ import annotations

from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services import card_lineage as CL
from learnloop.services import commitments as C
from learnloop.services.activities import _canonical_hash, _json

AUTHORING_SCHEMA_VERSION = 1
COACH_LEVELS = ("novice", "middle", "expert")


class AuthoringError(ValueError):
    """Domain error for the reader-authoring service."""


def _learner_card_contract(
    *, question: str, answer: str, target_ref: str | None, authorship: str,
    source_id: str | None, revision_id: str | None, annotation_id: str | None,
) -> dict[str, Any]:
    """The card contract preserving the learner's EXACT surface (§9.1). The verbatim
    question/answer are stored on the contract; authorship provenance is explicit."""

    return {
        "schema_version": AUTHORING_SCHEMA_VERSION,
        "prompt": question,
        "expected_answer": answer,
        "authorship": authorship,
        "provenance": {
            "origin": authorship,
            "source_id": source_id,
            "revision_id": revision_id,
            "annotation_id": annotation_id,
        },
        "target": target_ref,
        "capability": "retrieval",
        "pinned": True,
    }


def author_qa(
    repository: Repository,
    *,
    question: str,
    answer: str,
    source_id: str | None = None,
    revision_id: str | None = None,
    annotation_id: str | None = None,
    subject_id: str | None = None,
    depth_preset: str = "remember_key_ideas",
    client_idempotency_key: str | None = None,
    family_title: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Persist a learner-authored Q+A card + pinned surface under an explicit
    commitment, in ONE confirmation (§9.1).

    The Q+A is written to the durable card contract and the commitment BEFORE any
    coach/model work runs -- the caller may lint afterwards without risking the
    learner's content. Idempotent on ``client_idempotency_key`` via the commitment."""

    if not question.strip() or not answer.strip():
        raise AuthoringError("both a question and an answer are required (§9.1)")

    target_ref = subject_id or annotation_id or source_id or "learner_authored"
    # 1. Durable commitment (explicit commit-class action). Idempotent on the key.
    commitment = C.create_commitment(
        repository,
        action="help_me_remember",
        intent_text=question,
        interpretation_text=answer,
        targets=[{"target_kind": "source_locator", "target_ref": target_ref, "role": "required"}],
        depth_preset=depth_preset,
        client_idempotency_key=client_idempotency_key,
        reason="reader_authored_qa",
        provenance={"authorship": "learner", "annotation_id": annotation_id},
        clock=clock,
    )

    # 2. Learner-authored P1 card version + genesis lineage (verbatim surface, §9.1).
    contract = _learner_card_contract(
        question=question, answer=answer, target_ref=target_ref, authorship="learner",
        source_id=source_id, revision_id=revision_id, annotation_id=annotation_id,
    )
    family_id = repository.ensure_activity_family(
        purpose="practice", legacy_kind=None, title=family_title or "learner_authored", clock=clock
    )
    card_id = repository.ensure_activity_card(family_id=family_id, clock=clock)
    card_version_id = repository.ensure_activity_card_version(
        card_id=card_id, version=1, card_contract_hash=_canonical_hash(contract),
        contract_json=_json(contract), schema_version=AUTHORING_SCHEMA_VERSION, clock=clock,
    )
    lineage_id = CL.start_lineage(
        repository, genesis_card_version_id=card_version_id, family_id=family_id,
        card_id=card_id, clock=clock,
    )

    return {
        "commitment_id": commitment.id,
        "family_id": family_id,
        "card_id": card_id,
        "card_version_id": card_version_id,
        "lineage_id": lineage_id,
        "authorship": "learner",
        "pinned": True,
        "authored_before_ai": True,
        "contract": contract,
    }


def mint_ai_sibling(
    repository: Repository,
    *,
    family_id: str,
    predecessor_card_version_id: str,
    question: str,
    answer: str,
    scheduler_algorithm_version: str = "fsrs6",
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Mint a NON-learner-authored sibling for transfer (§9.1 last line). It carries
    ``authorship='ai'`` and NEVER impersonates learner/source authorship; it forks a
    NEW lineage + fresh scheduling state (no FSRS/certification inheritance, §3.7)."""

    contract = _learner_card_contract(
        question=question, answer=answer, target_ref=None, authorship="ai",
        source_id=None, revision_id=None, annotation_id=None,
    )
    # One card per family (P0.1); a sibling is a new VERSION on that card, forked into
    # its own lineage with fresh scheduling state.
    card_id = repository.ensure_activity_card(family_id=family_id, clock=clock)
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT COALESCE(MAX(version), 0) AS m FROM activity_card_versions WHERE card_id = ?",
            (card_id,),
        ).fetchone()
    next_version = int(row["m"]) + 1
    forked_version = repository.ensure_activity_card_version(
        card_id=card_id, version=next_version, card_contract_hash=_canonical_hash(contract),
        contract_json=_json(contract), schema_version=AUTHORING_SCHEMA_VERSION, clock=clock,
    )
    fork = CL.fork_card(
        repository,
        predecessor_card_version_id=predecessor_card_version_id,
        forked_card_version_id=forked_version,
        scheduler_algorithm_version=scheduler_algorithm_version,
        family_id=family_id, card_id=card_id,
        rationale={"reason": "ai_transfer_sibling"}, clock=clock,
    )
    return {"card_version_id": forked_version, "authorship": "ai", **fork}


# ---------------------------------------------------------------------------
# Formulation coach (§9.2) -- non-blocking, deterministic (no live AI)
# ---------------------------------------------------------------------------

def coach_lint(
    *, question: str, answer: str, level: str = "expert"
) -> dict[str, Any]:
    """Non-blocking formulation lint (§9.2). Deterministic (test stub): returns
    suggestions but NEVER blocks acceptance. Novice = scaffolding questions; middle =
    a starter template; expert = post-hoc lint for ambiguity/duplicate/granularity/
    missing context/rubric mismatch."""

    if level not in COACH_LEVELS:
        raise AuthoringError(f"unknown coach level: {level!r}")
    suggestions: list[dict[str, str]] = []
    if level == "novice":
        suggestions = [
            {"kind": "atomic_target", "prompt": "What single idea does this test?"},
            {"kind": "discrimination", "prompt": "What common wrong answer should it rule out?"},
            {"kind": "retention", "prompt": "How long do you want to remember this?"},
        ]
    elif level == "middle":
        suggestions = [
            {"kind": "starter_template", "prompt": "Define ___; contrast with ___; when does ___ apply?"},
        ]
    else:  # expert post-hoc lint
        q = question.strip()
        a = answer.strip()
        if len(q.split()) < 3:
            suggestions.append({"kind": "ambiguity", "prompt": "The question may be too terse to be unambiguous."})
        if len(a.split()) > 60:
            suggestions.append({"kind": "granularity", "prompt": "The answer is long; consider splitting into sub-cards."})
        if "?" not in q:
            suggestions.append({"kind": "missing_context", "prompt": "Consider phrasing the prompt as a question."})
    return {
        "level": level,
        "suggestions": suggestions,
        "blocking": False,  # §9.2: lint never prevents acceptance.
    }


def record_coach_response(
    repository: Repository,
    *,
    commitment_id: str | None,
    level: str,
    response: str,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record the learner's accept/edit/dismiss of a coach suggestion for corpus
    analysis (§9.2) -- NOT a live learned policy. Stored as a salience-only interaction
    event so it can never enter evidence."""

    from learnloop.services.activities import log_interaction_event
    from learnloop.services.salience_firewall import salience_payload

    if response not in ("accept", "edit", "dismiss"):
        raise AuthoringError(f"unknown coach response: {response!r}")
    event_id = log_interaction_event(
        repository,
        kind="reader_action_invoked",
        origin="learner",
        subject_type="reader_authoring",
        subject_id=commitment_id,
        payload=salience_payload({"action": "coach_response", "level": level, "response": response}),
        clock=clock,
    )
    return {"event_id": event_id, "response": response, "corpus_only": True}


# ---------------------------------------------------------------------------
# Fluid maintenance (§9.3) -- dispatch to P1 lineage / commitment machinery
# ---------------------------------------------------------------------------

MAINTENANCE_ACTIONS = ("edit", "split", "merge", "spawn", "retire", "change_depth")


def maintain(
    repository: Repository,
    *,
    action: str,
    lineage_id: str | None = None,
    from_card_version_id: str | None = None,
    to_card_version_id: str | None = None,
    prev_contract: Mapping[str, Any] | None = None,
    new_contract: Mapping[str, Any] | None = None,
    into_lineage_id: str | None = None,
    merged_card_version_id: str | None = None,
    split_card_version_id: str | None = None,
    forked_card_version_id: str | None = None,
    commitment_id: str | None = None,
    policy: str | None = None,
    bounds: Mapping[str, Any] | None = None,
    reviewed_edges: Any = (),
    scheduler_algorithm_version: str = "fsrs6",
    clock: Clock | None = None,
) -> dict[str, Any]:
    """In-review maintenance verbs (§9.3), each routed through the LANDED P1 lineage
    classifier / commitment machinery. Already-administered versions stay immutable;
    a cosmetic edit retains card state only when the classifier proves it
    surface-preserving; a material edit/split/merge/spawn forks NEW lineage with no
    blind stability/certification transfer."""

    if action not in MAINTENANCE_ACTIONS:
        raise AuthoringError(f"unknown maintenance action: {action!r}")

    if action == "edit":
        if prev_contract is None or new_contract is None:
            raise AuthoringError("edit requires prev_contract and new_contract")
        classification = CL.classify_edit(dict(prev_contract), dict(new_contract))
        if classification.verdict == "surface_preserving":
            edge_id = None
            if lineage_id and from_card_version_id and to_card_version_id:
                edge_id = CL.append_minor_successor(
                    repository, lineage_id=lineage_id, from_card_version_id=from_card_version_id,
                    to_card_version_id=to_card_version_id, rationale={"reason": "cosmetic_edit"}, clock=clock,
                )
            return {"action": "edit", "verdict": classification.verdict, "retains_state": True,
                    "edge_id": edge_id}
        # Material / review -> fork with fresh scheduling state (no inheritance).
        fork = None
        if classification.verdict == "fork_required" and from_card_version_id and to_card_version_id:
            fork = CL.fork_card(
                repository, predecessor_card_version_id=from_card_version_id,
                forked_card_version_id=to_card_version_id,
                scheduler_algorithm_version=scheduler_algorithm_version,
                predecessor_lineage_id=lineage_id, rationale={"reason": "material_edit"}, clock=clock,
            )
        return {"action": "edit", "verdict": classification.verdict, "retains_state": False,
                "fork": fork, "changed_unknown": list(classification.changed_unknown)}

    if action == "split":
        if from_card_version_id is None or split_card_version_id is None:
            raise AuthoringError("split requires from_card_version_id and split_card_version_id")
        new_lineage = CL.split_lineage(
            repository, from_card_version_id=from_card_version_id,
            split_card_version_id=split_card_version_id, rationale={"reason": "learner_split"}, clock=clock,
        )
        return {"action": "split", "new_lineage_id": new_lineage, "retains_state": False}

    if action == "merge":
        if into_lineage_id is None or from_card_version_id is None or merged_card_version_id is None:
            raise AuthoringError("merge requires into_lineage_id, from_card_version_id, merged_card_version_id")
        edge = CL.merge_lineage(
            repository, into_lineage_id=into_lineage_id, from_card_version_id=from_card_version_id,
            merged_card_version_id=merged_card_version_id, rationale={"reason": "learner_merge"}, clock=clock,
        )
        return {"action": "merge", "merge_edge_id": edge, "retains_state": False}

    if action == "spawn":
        if from_card_version_id is None or forked_card_version_id is None:
            raise AuthoringError("spawn requires from_card_version_id and forked_card_version_id")
        fork = CL.fork_card(
            repository, predecessor_card_version_id=from_card_version_id,
            forked_card_version_id=forked_card_version_id,
            scheduler_algorithm_version=scheduler_algorithm_version,
            predecessor_lineage_id=lineage_id, rationale={"reason": "learner_spawn_sibling"}, clock=clock,
        )
        return {"action": "spawn", "retains_state": False, **fork}

    if action == "retire":
        if commitment_id is None:
            raise AuthoringError("retire requires commitment_id")
        # Retirement preserves commitment/evidence + provenance (§9.3): a disposition
        # event only, never a delete.
        disposition = C.retire(repository, commitment_id=commitment_id, clock=clock)
        return {"action": "retire", "disposition": disposition, "evidence_preserved": True}

    # change_depth
    if commitment_id is None:
        raise AuthoringError("change_depth requires commitment_id")
    changed: dict[str, Any] = {"action": "change_depth"}
    if policy is not None:
        C.change_depth_policy(repository, commitment_id=commitment_id, policy=policy, clock=clock)
        changed["policy"] = policy
    if bounds is not None:
        # Reader-side maintenance is salience-only: it may contract the envelope
        # but never widen it (allow_widen defaults False -> EnvelopeWideningRejected).
        C.change_depth_envelope(
            repository, commitment_id=commitment_id, bounds=bounds, reviewed_edges=reviewed_edges, clock=clock
        )
        changed["envelope_changed"] = True
    return changed
