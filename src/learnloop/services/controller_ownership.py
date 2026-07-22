"""P4 §14.2 step 3 -- commitment-scoped controller ownership (design §A.2 / §C step 3).

The dual-controller coexistence seam. During the cutover window a commitment (and its
P2 golden-path run) is owned by EXACTLY ONE controller at a time (design §A.2):

- the **staged policy** owns P2 golden-path commitments (a confirmed goal contract +
  depth policy/envelope);
- the **legacy scheduler** owns everything else (loose FSRS maintenance, un-committed
  practice items).

Ownership is a rebuildable projection head keyed by ``commitment_id``; every transition
is append-only with a durable receipt (migration 099). Arbitration is deterministic
(design §A.2 order): a P2 golden-path commitment goes to ``staged``; the default for any
commitment without a recorded head is ``legacy`` (so a fresh vault with no ownership
rows behaves exactly as pre-cutover -- the legacy scheduler owns all work).

Two consumers read this head:
- the **legacy scheduler** excludes staged-owned commitments' practice items from its
  queues (:func:`staged_owned_practice_item_ids`, wired into ``scheduler.build_due_queue``);
- the **staged policy** refuses items it does not own (``staged_policy.decide`` live mode).

Rollback (design §A.5 / §C step-3 gate f) is a SINGLE registered switch
(:func:`rollback_to_legacy`) that atomically returns owned commitments to legacy under
one shared receipt; it applies to the next uncommitted decision only (in-flight
administrations complete under their pinned controller).
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services import commitments as C
from learnloop.services.activities import _json

# Structural policy version of the ownership arbitration (enum, not a decision knob).
OWNERSHIP_POLICY_VERSION = 1

STAGED = "staged"
LEGACY = "legacy"
# The default owner of any commitment with no recorded ownership head (design §A.2 rule
# 2): everything the staged policy has not explicitly claimed stays with legacy.
DEFAULT_OWNER = LEGACY


class NotAP2GoldenPathCommitment(Exception):
    """Refused a staged-ownership assignment for a commitment that is not a P2
    golden-path commitment (design §A.2 rule 1: staged owns only commitments with a
    confirmed goal contract + depth policy + depth envelope)."""


class StagedOwnedAdministrationRefused(Exception):
    """An administration surface (legacy queue, probe episode, held-out exam) refused to
    serve a learning object / practice item that a staged-owned P2 commitment owns
    (design §A.2 rule 3, the dual-authority exclusion). The staged policy is the sole
    controller allowed to administer a staged-owned commitment's work."""


class ExamReservationOwnershipConflict(Exception):
    """A staged-ownership assignment and a held-out exam reservation would cover the same
    practice item(s). Exam reservation and staged ownership are mutually exclusive
    (design §A.2 rule 3): a reserved held-out item must stay uncontaminated by the staged
    controller, and a staged-owned item must not be quarantined into an exam pool."""


# ---------------------------------------------------------------------------
# Arbitration predicate (design §A.2 rule 1).
# ---------------------------------------------------------------------------


def is_p2_golden_path_commitment(repository: Repository, commitment_id: str) -> bool:
    """A P2 golden-path commitment has a confirmed goal contract AND a depth policy AND
    a depth envelope (the three things ``golden_path_confirm`` mints atomically). Only
    such a commitment may be owned by the staged policy."""

    try:
        head = C.resolve_head(repository, commitment_id)
    except Exception:
        return False
    return bool(
        head.goal_id
        and head.depth_policy_version_id
        and head.depth_envelope_version_id
    )


# ---------------------------------------------------------------------------
# Head projection + append-only transition log.
# ---------------------------------------------------------------------------


def ownership_head(repository: Repository, commitment_id: str) -> dict[str, Any] | None:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT * FROM controller_ownership WHERE commitment_id = ?", (commitment_id,)
        ).fetchone()
    return dict(row) if row is not None else None


def rebuild_ownership_head(
    repository: Repository, *, commitment_id: str | None = None
) -> dict[str, Any]:
    """Rebuild the current-owner head projection by folding ``controller_ownership_events``
    (design §A.2: the head is a REBUILDABLE projection of the append-only event log, not a
    source of truth). With ``commitment_id=None`` every commitment that has events is
    rebuilt; otherwise only the named one. Deterministic: the fold replays transitions in
    ``event_ordinal`` order, so the head owner is the last event's ``to_owner`` and the
    ``ownership_version`` is the transition count. Returns the rebuilt heads.

    This makes the "rebuildable projection head" claim in migration 099 / the module
    docstring true and testable: a corrupted or dropped head can be reconstructed exactly
    from the durable events (audit L1/D3)."""

    connection = repository.connection()
    try:
        connection.execute("BEGIN")
        if commitment_id is None:
            rows = connection.execute(
                "SELECT DISTINCT commitment_id FROM controller_ownership_events"
            ).fetchall()
            ids = [r["commitment_id"] for r in rows]
        else:
            ids = [commitment_id]
        rebuilt: list[dict[str, Any]] = []
        for cid in sorted(ids):
            events = connection.execute(
                "SELECT to_owner, receipt_id, policy_version, created_at FROM "
                "controller_ownership_events WHERE commitment_id = ? ORDER BY event_ordinal",
                (cid,),
            ).fetchall()
            if not events:
                continue
            last = events[-1]
            version = len(events)  # ownership_version increments once per transition.
            connection.execute(
                "INSERT INTO controller_ownership(commitment_id, owner, ownership_version, "
                "policy_version, receipt_id, assigned_at) VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(commitment_id) DO UPDATE SET owner = excluded.owner, "
                "ownership_version = excluded.ownership_version, "
                "policy_version = excluded.policy_version, receipt_id = excluded.receipt_id, "
                "assigned_at = excluded.assigned_at",
                (cid, last["to_owner"], version, last["policy_version"],
                 last["receipt_id"], last["created_at"]),
            )
            rebuilt.append(
                {"commitment_id": cid, "owner": last["to_owner"], "ownership_version": version}
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return {"rebuilt": rebuilt, "count": len(rebuilt)}


def resolve_owner(repository: Repository, commitment_id: str) -> str:
    """The current owner of a commitment. Absent head -> ``legacy`` default (§A.2)."""

    head = ownership_head(repository, commitment_id)
    return head["owner"] if head is not None else DEFAULT_OWNER


def is_staged_owned(repository: Repository, commitment_id: str) -> bool:
    return resolve_owner(repository, commitment_id) == STAGED


def ownership_events(repository: Repository, commitment_id: str) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT * FROM controller_ownership_events WHERE commitment_id = ? "
            "ORDER BY event_ordinal",
            (commitment_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def _append_transition(
    connection: Any,
    *,
    commitment_id: str,
    to_owner: str,
    reason: str,
    receipt_id: str,
    detail: Mapping[str, Any] | None,
    now: str,
) -> dict[str, Any] | None:
    """Append one ownership transition + upsert the head, INSIDE an open transaction.
    Idempotent: a transition to the owner the head already holds is a no-op (returns
    None). The caller owns the BEGIN/COMMIT so a batch rollback is one atomic unit."""

    head = connection.execute(
        "SELECT owner, ownership_version FROM controller_ownership WHERE commitment_id = ?",
        (commitment_id,),
    ).fetchone()
    from_owner = head["owner"] if head is not None else None
    if from_owner == to_owner:
        return None  # already owned by the target controller -- append-only, no churn.

    ordinal_row = connection.execute(
        "SELECT COALESCE(MAX(event_ordinal), 0) AS m FROM controller_ownership_events "
        "WHERE commitment_id = ?",
        (commitment_id,),
    ).fetchone()
    ordinal = int(ordinal_row["m"]) + 1
    version = (int(head["ownership_version"]) + 1) if head is not None else 1
    event_id = new_ulid()
    connection.execute(
        "INSERT INTO controller_ownership_events(id, commitment_id, event_ordinal, "
        "from_owner, to_owner, reason, receipt_id, policy_version, detail_json, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            event_id, commitment_id, ordinal, from_owner, to_owner, reason, receipt_id,
            OWNERSHIP_POLICY_VERSION, _json(dict(detail)) if detail is not None else None, now,
        ),
    )
    connection.execute(
        "INSERT INTO controller_ownership(commitment_id, owner, ownership_version, "
        "policy_version, receipt_id, assigned_at) VALUES (?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(commitment_id) DO UPDATE SET owner = excluded.owner, "
        "ownership_version = excluded.ownership_version, policy_version = excluded.policy_version, "
        "receipt_id = excluded.receipt_id, assigned_at = excluded.assigned_at",
        (commitment_id, to_owner, version, OWNERSHIP_POLICY_VERSION, receipt_id, now),
    )
    return {
        "event_id": event_id, "commitment_id": commitment_id, "event_ordinal": ordinal,
        "from_owner": from_owner, "to_owner": to_owner, "ownership_version": version,
        "receipt_id": receipt_id,
    }


def assign(
    repository: Repository,
    *,
    commitment_id: str,
    owner: str,
    reason: str,
    receipt_id: str | None = None,
    detail: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record a durable ownership transition (append-only + head upsert), atomically.
    Idempotent: re-assigning the current owner returns the standing head with
    ``changed=False`` and appends nothing."""

    if owner not in (STAGED, LEGACY):
        raise ValueError(f"unknown controller owner: {owner!r}")
    receipt_id = receipt_id or new_ulid()
    now = utc_now_iso(clock)
    connection = repository.connection()
    try:
        connection.execute("BEGIN")
        transition = _append_transition(
            connection, commitment_id=commitment_id, to_owner=owner, reason=reason,
            receipt_id=receipt_id, detail=detail, now=now,
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return {
        "receipt_id": receipt_id, "commitment_id": commitment_id, "owner": owner,
        "changed": transition is not None, "transition": transition,
    }


def assign_p2_run(
    repository: Repository,
    *,
    commitment_id: str,
    reason: str = "p2_golden_path_run",
    detail: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Assign a P2 golden-path commitment to the staged controller (design §A.2 rule 1).
    Refuses (raises :class:`NotAP2GoldenPathCommitment`) any commitment lacking the
    confirmed goal contract + depth policy + depth envelope."""

    if not is_p2_golden_path_commitment(repository, commitment_id):
        raise NotAP2GoldenPathCommitment(commitment_id)
    # Dual-authority mutual exclusion (design §A.2 rule 3): a commitment whose items are
    # held-out exam-reserved must not become staged-owned -- the staged controller would
    # be able to administer an item the exam has quarantined. Direct legacy_practice_item
    # refs are checked here; the authoritative reserve-side guard lives in the exam-pool
    # selector (which drops every staged-owned item before reservation).
    refs = _commitment_refs(repository, commitment_id)
    if refs:
        reserved = repository.reserved_exam_pool_item_ids()
        if reserved & refs:
            raise ExamReservationOwnershipConflict(commitment_id)
    return assign(
        repository, commitment_id=commitment_id, owner=STAGED, reason=reason,
        detail=detail, clock=clock,
    )


# ---------------------------------------------------------------------------
# Consumers: the coexistence-seam projections.
# ---------------------------------------------------------------------------


def staged_owned_commitment_ids(repository: Repository) -> set[str]:
    """Every commitment whose current head is owned by the staged controller."""

    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT commitment_id FROM controller_ownership WHERE owner = ?", (STAGED,)
        ).fetchall()
    return {r["commitment_id"] for r in rows}


def staged_owned_refs(repository: Repository) -> set[str]:
    """The atomic dual-authority exclusion input shared by every administration surface
    (design §A.2 rule 3): the union of every staged-owned commitment's head targets of
    kind ``learning_object`` / ``legacy_practice_item`` (raw refs, not resolved against a
    vault). An ``learning_object`` ref means the WHOLE learning object is staged-owned; a
    ``legacy_practice_item`` ref means one item is.

    Empty when no commitment is staged-owned -- so every consumer is a no-op on a
    pre-cutover vault. Bounded: one head-projection read, then one head-targets read per
    staged-owned commitment (not per candidate)."""

    owned = staged_owned_commitment_ids(repository)
    if not owned:
        return set()
    refs: set[str] = set()
    for commitment_id in owned:
        try:
            head = C.resolve_head(repository, commitment_id)
        except Exception:
            continue
        for target in head.targets:
            if target.target_kind in ("learning_object", "legacy_practice_item"):
                refs.add(target.target_ref)
    return refs


def _commitment_refs(repository: Repository, commitment_id: str) -> set[str]:
    """The head-target refs (learning_object / legacy_practice_item) of ONE commitment."""

    try:
        head = C.resolve_head(repository, commitment_id)
    except Exception:
        return set()
    return {
        target.target_ref
        for target in head.targets
        if target.target_kind in ("learning_object", "legacy_practice_item")
    }


def is_learning_object_staged_owned(repository: Repository, learning_object_id: str) -> bool:
    """True when the WHOLE learning object is a head target of a staged-owned commitment
    (an ``learning_object``-kind ref). Such an LO must never be administered by a legacy
    surface (design §A.2 rule 3)."""

    return learning_object_id in staged_owned_refs(repository)


def staged_owned_practice_item_ids(vault: Any, repository: Repository) -> set[str]:
    """The legacy-scheduler EXCLUSION set (design §A.2 rule 3, the coexistence seam):
    every practice item that belongs to a staged-owned commitment, resolved down from
    the commitment's head targets (``learning_object`` / ``legacy_practice_item`` kinds).

    Empty when no commitment is staged-owned -- so a pre-cutover vault's legacy queue is
    byte-identical (the exclusion is a no-op). Bounded: one head-projection read, then one
    head-targets read per staged-owned commitment (not per candidate)."""

    refs = staged_owned_refs(repository)
    if not refs:
        return set()
    excluded: set[str] = set()
    for item in getattr(vault, "practice_items", {}).values():
        if item.id in refs or getattr(item, "learning_object_id", None) in refs:
            excluded.add(item.id)
    return excluded


# ---------------------------------------------------------------------------
# Rollback -- the single registered switch (design §A.5 / §C step-3 gate f).
# ---------------------------------------------------------------------------


def rollback_to_legacy(
    repository: Repository,
    *,
    reason: str = "cutover_rollback",
    commitment_ids: Sequence[str] | None = None,
    detail: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Return owned commitments to the legacy controller atomically under ONE shared
    receipt (design §C step-3 gate f). With ``commitment_ids=None`` every staged-owned
    commitment is rolled back; otherwise only the named ones. Applies to the next
    uncommitted decision -- in-flight administrations complete under their pinned
    controller (design §A.5); all ownership-event history is preserved (append-only).

    Returns the shared ``receipt_id`` and the list of transitioned commitments."""

    targets = set(commitment_ids) if commitment_ids is not None else staged_owned_commitment_ids(repository)
    receipt_id = new_ulid()
    now = utc_now_iso(clock)
    transitioned: list[dict[str, Any]] = []
    connection = repository.connection()
    try:
        connection.execute("BEGIN")
        for commitment_id in sorted(targets):
            transition = _append_transition(
                connection, commitment_id=commitment_id, to_owner=LEGACY, reason=reason,
                receipt_id=receipt_id, detail=detail, now=now,
            )
            if transition is not None:
                transitioned.append(transition)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return {"receipt_id": receipt_id, "reason": reason, "transitioned": transitioned,
            "count": len(transitioned)}
