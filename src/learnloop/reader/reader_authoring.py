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

Adoption into practice (daily-loop audit 2026-10-11): writing the question IS the
learner adopting it into practice, so the same call also files it as a
learner-authored Practice Item -- the store the scheduler actually reads --
under the Learning Object whose provenance cites the passage being read, and
links that item to the commitment as a ``legacy_practice_item`` target (which
the scheduler reads as a learner-requested item). When no active Learning
Object fits, nothing is invented: the result says ``reference_only`` so the
reader never promises practice that will not happen. Such a reference is adopted
later, with no learner step, once an active Learning Object cites its passage
(:func:`adopt_reference_questions`, run on every sidecar vault load).

Fluid maintenance (§9.3) dispatches to P1 lineage classification: already-administered
versions stay immutable; split/merge never blindly transfers scheduling/certification;
a cosmetic edit retains card state ONLY through the P1 classifier. An AI sibling never
impersonates learner/source authorship.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.content.authoring.item_authoring import author_item, retire_item
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.db.repositories import Repository
from learnloop.ingest.locators import BLOCK_SPAN_V1, format_block_span, parse_block_span
from learnloop.reader.reader_progression import learning_objects_for_span
from learnloop.vault.lifecycle import learning_object_servable
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault
from learnloop.substrate import card_lineage as CL
from learnloop.curriculum import commitments as C
from learnloop.substrate.activities import canonical_hash, canonical_json

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
    root: Path | None = None,
    learning_object_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Persist a learner-authored Q+A card + pinned surface under an explicit
    commitment, in ONE confirmation (§9.1).

    The Q+A is written to the durable card contract and the commitment BEFORE any
    coach/model work runs -- the caller may lint afterwards without risking the
    learner's content. Idempotent on ``client_idempotency_key`` via the commitment.

    With the vault ``root`` the card is also adopted into practice (see the module
    docstring): ``practice_status`` is ``scheduled`` with the new
    ``practice_item_id``, or ``reference_only`` when no active Learning Object fits
    (an explicit ``learning_object_id`` wins over the passage's provenance)."""

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
        card_id=card_id, version=1, card_contract_hash=canonical_hash(contract),
        contract_json=canonical_json(contract), schema_version=AUTHORING_SCHEMA_VERSION, clock=clock,
    )
    lineage_id = CL.start_lineage(
        repository, genesis_card_version_id=card_version_id, family_id=family_id,
        card_id=card_id, clock=clock,
    )

    # 3. Adopt into practice: the scheduler serves Practice Items, not card versions.
    practice = (
        _adopt_into_practice(
            root, repository, commitment_id=commitment.id, question=question, answer=answer,
            subject_id=subject_id, source_id=source_id, learning_object_id=learning_object_id,
            clock=clock,
        )
        if root is not None
        else {"practice_item_id": None, "learning_object_id": None, "practice_status": "reference_only"}
    )

    return {
        **practice,
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


def _span_anchor(repository: Repository, subject_id: str | None) -> tuple[str, str] | None:
    """``span:<extraction>/<span>`` (the reader's subject for a passage) -> ids."""

    parsed = parse_block_span(subject_id or "")
    if parsed is None:
        return None
    extraction_id, span_id = parsed
    return resolve_extraction_id(repository, extraction_id) or extraction_id, span_id


def _practice_learning_object(
    vault: LoadedVault, repository: Repository, *, learning_object_id: str | None,
    anchor: tuple[str, str] | None,
) -> str | None:
    """The active Learning Object a written question is filed under: the learner's
    explicit choice, else the first (sorted) active LO whose provenance cites the
    passage's section -- the same span->LO resolution tutor promotions use."""

    if learning_object_id is not None:
        return learning_object_id if learning_object_servable(vault, learning_object_id) else None
    if anchor is None:
        return None
    extraction_id, span_id = anchor
    candidates = learning_objects_for_span(vault, repository, extraction_id=extraction_id, span_id=span_id)
    return candidates[0] if candidates else None


# Versioned provenance of cards the sweep adopts (vs. "reader_author_qa", the
# write-time adoption), so they can be told apart and audited later.
REFERENCE_ADOPTION_MECHANISM = "reader_reference_adoption_v1"


def reader_practice_item_id(commitment_id: str) -> str:
    """The stable practice-item id of a reader question's card (its commitment's)."""

    digest = hashlib.sha256(f"reader_authored_qa:{commitment_id}".encode("utf-8")).hexdigest()
    return f"pi_learner_{digest[:26]}"


def _adopt_into_practice(
    root: Path,
    repository: Repository,
    *,
    commitment_id: str,
    question: str,
    answer: str,
    subject_id: str | None,
    source_id: str | None,
    learning_object_id: str | None,
    clock: Clock | None,
    mechanism: str = "reader_author_qa",
) -> dict[str, Any]:
    vault = load_vault(root)
    # Idempotent retry: this commitment already adopted a card with these words.
    for target in C.resolve_head(repository, commitment_id).targets:
        if target.target_kind != "legacy_practice_item":
            continue
        existing = vault.practice_items.get(target.target_ref)
        if existing is not None and existing.prompt == question.strip() and existing.expected_answer == answer.strip():
            return {
                "practice_item_id": existing.id,
                "learning_object_id": existing.learning_object_id,
                "practice_status": "scheduled",
            }

    anchor = _span_anchor(repository, subject_id)
    lo_id = _practice_learning_object(vault, repository, learning_object_id=learning_object_id, anchor=anchor)
    if lo_id is None:
        return {"practice_item_id": None, "learning_object_id": None, "practice_status": "reference_only"}

    if source_id is None and anchor is not None:
        run = repository.get_extraction_run(anchor[0]) or {}
        source_id = (repository.get_source_revision(str(run.get("revision_id") or "")) or {}).get("source_id")
    # Crash-safe idempotency bound to THIS commitment: its card has an id derived
    # from the commitment, so a card written before the link below landed is
    # reused, while an identical question's card or an independently written
    # matching card is never captured (review F2).
    item_id = reader_practice_item_id(commitment_id)
    existing = vault.practice_items.get(item_id)
    if existing is not None:
        C.add_target(
            repository, commitment_id=commitment_id,
            target={"target_kind": "legacy_practice_item", "target_ref": existing.id, "role": "required"},
            change_reason="adopted_into_practice", clock=clock,
        )
        return {
            "practice_item_id": existing.id, "learning_object_id": existing.learning_object_id,
            "practice_status": "scheduled" if existing.status == "active" else "reference_only",
        }

    source_refs = (
        [{
            "ref_type": "canonical_source",
            "ref_id": source_id or anchor[0],
            "locator": format_block_span(anchor[0], anchor[1]),
            "locator_scheme": BLOCK_SPAN_V1,
        }]
        if anchor is not None
        else None
    )
    payload = author_item(
        root, repository, learning_object_id=lo_id, prompt=question, expected_answer=answer,
        source_refs=source_refs,
        event_detail={"mechanism": mechanism, "commitment_id": commitment_id},
        item_id=item_id, clock=clock,
    )
    # The commitment records which card it adopted; a learner-held commitment's
    # legacy_practice_item target is what the scheduler reads as "requested".
    C.add_target(
        repository, commitment_id=commitment_id,
        target={"target_kind": "legacy_practice_item", "target_ref": payload["id"], "role": "required"},
        change_reason="adopted_into_practice", clock=clock,
    )
    return {"practice_item_id": payload["id"], "learning_object_id": lo_id, "practice_status": "scheduled"}


def adopt_reference_questions(
    vault: LoadedVault, repository: Repository, *, clock: Clock | None = None
) -> list[dict[str, Any]]:
    """Adopt reference-only reader questions whose passage an active LO now cites.

    A question written over a passage no active Learning Object cited was kept as
    a reference (no ``legacy_practice_item`` target on its ``reader_authored_qa``
    commitment). When a study-map apply adds or links an LO that cites the
    passage, the question becomes practice exactly as if the LO had existed when
    it was written -- the learner takes no step. Idempotent: an adopted
    commitment carries its card as a target and is never swept again; a retired
    commitment is never adopted. Returns one row per newly adopted question.

    Behind the kill switch ``tutor_qa.adopt_reference_questions`` (default on):
    off, nothing is adopted and cards adopted earlier are kept. Each adopted
    card's provenance event names ``REFERENCE_ADOPTION_MECHANISM``."""

    if not vault.config.tutor_qa.adopt_reference_questions:
        return []
    with repository.connection() as connection:
        rows = connection.execute(
            """
            SELECT commitment.id AS id
            FROM commitments commitment
            WHERE commitment.created_action = 'help_me_remember'
              AND EXISTS (
                SELECT 1 FROM commitment_versions version
                WHERE version.commitment_id = commitment.id AND version.reason = 'reader_authored_qa'
              )
              AND NOT EXISTS (
                SELECT 1 FROM commitment_versions version
                JOIN commitment_target_versions target ON target.commitment_version_id = version.id
                WHERE version.commitment_id = commitment.id AND target.target_kind = 'legacy_practice_item'
              )
              AND NOT EXISTS (
                SELECT 1 FROM commitment_events event
                WHERE event.commitment_id = commitment.id AND event.kind = 'retired'
              )
            ORDER BY commitment.created_at, commitment.id
            """
        ).fetchall()
    adopted: list[dict[str, Any]] = []
    for row in rows:
        head = C.resolve_head(repository, row["id"])
        subject_id = next(
            (t.target_ref for t in head.targets if t.target_kind == "source_locator"), None
        )
        anchor = _span_anchor(repository, subject_id)
        if anchor is None or not head.interpretation_text:
            continue
        if _practice_learning_object(vault, repository, learning_object_id=None, anchor=anchor) is None:
            continue
        practice = _adopt_into_practice(
            vault.root, repository, commitment_id=row["id"], question=head.intent_text,
            answer=head.interpretation_text, subject_id=subject_id, source_id=None,
            learning_object_id=None, clock=clock, mechanism=REFERENCE_ADOPTION_MECHANISM,
        )
        if practice["practice_item_id"] is not None:
            adopted.append({"commitment_id": row["id"], **practice})
    return adopted


def _retire_adopted_items(
    root: Path, repository: Repository, *, commitment_id: str, clock: Clock | None
) -> list[str]:
    """Retire the practice items a reader question (``reader_authored_qa``
    commitment) was adopted into. Other commitments' targets are left alone."""

    with repository.connection() as connection:
        is_reader_question = connection.execute(
            "SELECT 1 FROM commitment_versions WHERE commitment_id = ? AND reason = 'reader_authored_qa' LIMIT 1",
            (commitment_id,),
        ).fetchone()
    if is_reader_question is None:
        return []
    vault = load_vault(root)
    retired: list[str] = []
    for target in C.resolve_head(repository, commitment_id).targets:
        item = vault.practice_items.get(target.target_ref) if target.target_kind == "legacy_practice_item" else None
        if item is None or item.status != "active":
            continue
        if _requested_by_another_commitment(repository, item.id, commitment_id=commitment_id):
            # Still another active commitment's practice: it is not this
            # question's alone to retire (review F2).
            continue
        retire_item(
            root, repository, practice_item_id=item.id, reason="no_longer_relevant",
            note="the reader question was retired", clock=clock,
        )
        retired.append(item.id)
    return retired


def _requested_by_another_commitment(
    repository: Repository, practice_item_id: str, *, commitment_id: str
) -> bool:
    """True when a different, unretired commitment's head still targets the item."""

    with repository.connection() as connection:
        others = [
            row["commitment_id"]
            for row in connection.execute(
                """
                SELECT DISTINCT version.commitment_id AS commitment_id
                FROM commitment_versions version
                JOIN commitment_target_versions target ON target.commitment_version_id = version.id
                WHERE target.target_kind = 'legacy_practice_item' AND target.target_ref = ?
                  AND version.commitment_id != ?
                  AND NOT EXISTS (
                    SELECT 1 FROM commitment_events event
                    WHERE event.commitment_id = version.commitment_id AND event.kind = 'retired'
                  )
                """,
                (practice_item_id, commitment_id),
            )
        ]
    return any(
        ("legacy_practice_item", practice_item_id)
        in {(t.target_kind, t.target_ref) for t in C.resolve_head(repository, other).targets}
        for other in others
    )


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
        card_id=card_id, version=next_version, card_contract_hash=canonical_hash(contract),
        contract_json=canonical_json(contract), schema_version=AUTHORING_SCHEMA_VERSION, clock=clock,
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

    from learnloop.substrate.activities import log_interaction_event
    from learnloop.attempts.salience_firewall import salience_payload

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
    root: Path | None = None,
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
        # A reader question adopted into practice takes its card with it (with the
        # vault ``root``), through the learner retire path: off the queue, serving
        # doors closed, surface work obsolete, history kept.
        retired = (
            _retire_adopted_items(root, repository, commitment_id=commitment_id, clock=clock)
            if root is not None
            else []
        )
        return {
            "action": "retire", "disposition": disposition, "evidence_preserved": True,
            "retired_practice_item_ids": retired,
        }

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
