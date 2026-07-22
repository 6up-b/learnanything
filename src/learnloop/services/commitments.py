"""P1 step 1 -- durable learner commitments (spec_p1_shared_substrate §3.1, §3.2).

A ``Commitment`` records *why* this learner wants attention spent. It is not a
goal, card, reading mark, or scheduler bucket (§3.1). Stable ``commitments`` +
immutable ``commitment_versions`` + membership ``commitment_target_versions``,
with an append-only ``commitment_events`` ledger and the commitment-level depth
objects (policy / envelope) that P0's goal_contracts envelope validation plugs
into.

Owner decisions adopted (spec change log 2026-07-19, pending owner confirmation):
  * A.2 -- depth policy/envelope are immutable content-addressed version objects;
  * A.3 -- a depth-policy or depth-envelope change forces a commitment
    ``version_appended`` in the SAME transaction as the typed
    ``depth_policy_changed`` / ``depth_envelope_changed`` event, because the
    immutable version stores the active policy/envelope ids and a version hash;
    ``depth_milestone_reached`` / ``depth_transition_committed`` do NOT bump the
    version (achievement facts over the existing envelope), and disposition
    changes do NOT bump the version (disposition is a projection over events).

Invariant 4 (§1.1): only the four commit-class actions create a commitment;
passive surfaces (highlight/read/ask/shown-proposal) cannot reach this service.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.activities import _canonical_hash, _json

# The four commit-class actions (invariant 4, §1.1 / §3.1). Any other action is a
# passive surface and MUST NOT create a commitment.
COMMIT_ACTIONS: frozenset[str] = frozenset(
    {"help_me_remember", "test_me_later", "select_exemplar", "create_quest"}
)

DEPTH_PRESETS: frozenset[str] = frozenset(
    {"keep_in_touch", "remember_key_ideas", "work_fluently", "master_tasks_like_these"}
)

TARGET_KINDS: frozenset[str] = frozenset(
    {
        "p0_target_exemplar",
        "canonical_facet",
        "learning_object",
        "source_locator",
        "legacy_practice_item",
    }
)

DISPOSITIONS: frozenset[str] = frozenset(
    {"active", "paused", "reference_only", "one_check_pending", "satisfied", "stopped"}
)

# §10 launch defaults: a quick ``test_me_later`` capture is a single delayed cold
# check -> ``hold_at_target``; every other capture defaults to ``suggest_next``.
# End-of-chapter ongoing commitments recommend ``auto_within_envelope``, but that
# is an owner-tooling recommendation layered on top, not an action default here.
_ACTION_DEFAULT_POLICY: dict[str, str] = {
    "test_me_later": "hold_at_target",
    "help_me_remember": "suggest_next",
    "select_exemplar": "suggest_next",
    "create_quest": "suggest_next",
}

DEPTH_ENVELOPE_SCHEMA_VERSION = 1
DEPTH_POLICY_SCHEMA_VERSION = 1


class PassiveActionCannotCommit(Exception):
    """A non-commit-class action tried to create a commitment (invariant 4, §9.1)."""

    def __init__(self, action: str):
        super().__init__(
            f"passive action {action!r} cannot create a commitment; "
            f"only {sorted(COMMIT_ACTIONS)} may"
        )
        self.action = action


class InvalidTarget(Exception):
    """A commitment target used an unknown target kind or role."""


class UnknownCommitment(Exception):
    def __init__(self, commitment_id: str):
        super().__init__(f"unknown commitment: {commitment_id}")
        self.commitment_id = commitment_id


class EnvelopeWideningRejected(Exception):
    """A shrink/change tried to WIDEN the depth envelope (§10.2, F4).

    Envelope bounds may only contract (dimension-wise subset). Widening the
    authorized region requires the explicit confirmed-successor path
    (goal_contracts / learner-confirmed envelope successor), which passes
    ``allow_widen=True``. ``dimension`` names the offending bounds key."""

    def __init__(self, dimension: str):
        super().__init__(
            f"envelope change widens authorization on dimension {dimension!r}; "
            "widening is only allowed via a confirmed envelope successor"
        )
        self.dimension = dimension


def _bounds_value_is_subset(new_val: Any, old_val: Any) -> bool:
    """Is ``new_val`` provably contained in ``old_val`` for one bounds dimension?

    An absent dimension is the empty (most-restrictive) region, so callers pass
    ``old_val=None`` when the current envelope does not constrain a dimension the
    new bounds introduces -- adding any non-empty region there is a widening.
    """

    # New empties (None / [] / {} / False / 0) are subsets of anything.
    if new_val is None or new_val == [] or new_val == {} or new_val is False:
        return True
    if old_val is None:
        # Current envelope is empty on this dimension; a non-empty new value widens.
        return not new_val

    if isinstance(new_val, bool) or isinstance(old_val, bool):
        # Booleans only tighten: a new True requires the old to already be True.
        return (not bool(new_val)) or bool(old_val)
    if isinstance(new_val, (list, tuple, set)) and isinstance(old_val, (list, tuple, set)):
        return set(new_val) <= set(old_val)
    if isinstance(new_val, Mapping) and isinstance(old_val, Mapping):
        if {"min", "max"} & set(new_val) or {"min", "max"} & set(old_val):
            # A numeric [min, max] range: narrower-or-equal on both ends.
            new_lo = new_val.get("min", float("-inf"))
            new_hi = new_val.get("max", float("inf"))
            old_lo = old_val.get("min", float("-inf"))
            old_hi = old_val.get("max", float("inf"))
            return new_lo >= old_lo and new_hi <= old_hi
        # Nested bounds: every new sub-dimension must be a subset.
        return all(
            _bounds_value_is_subset(v, old_val.get(k)) for k, v in new_val.items()
        )
    if isinstance(new_val, (int, float)) and isinstance(old_val, (int, float)):
        # A scalar cap contracts only by staying no larger.
        return new_val <= old_val
    # Type mismatch or unrecognised shape: cannot prove containment -> reject.
    return new_val == old_val


def envelope_widening_dimension(
    new_bounds: Mapping[str, Any], current_bounds: Mapping[str, Any]
) -> str | None:
    """Return the first bounds dimension on which ``new_bounds`` widens
    ``current_bounds``, or ``None`` if ``new_bounds`` is a subset (a shrink)."""

    for dimension, new_val in new_bounds.items():
        if not _bounds_value_is_subset(new_val, current_bounds.get(dimension)):
            return dimension
    return None


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CommitmentTarget:
    target_kind: str
    target_ref: str
    role: str
    salience: float | None = None
    provenance: dict[str, Any] | None = None

    def normalized(self) -> dict[str, Any]:
        # Identity for the target-set hash: kind + ref + role (salience/provenance
        # are learner annotations, not membership identity).
        return {"target_kind": self.target_kind, "target_ref": self.target_ref, "role": self.role}


@dataclass(frozen=True)
class CommitmentVersion:
    id: str
    commitment_id: str
    version: int
    predecessor_version_id: str | None
    intent_text: str
    interpretation_text: str | None
    goal_id: str | None
    depth_preset: str
    depth_policy_version_id: str | None
    depth_envelope_version_id: str | None
    target_set_hash: str
    version_hash: str
    author: str
    change_reason: str | None
    targets: tuple[CommitmentTarget, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Commitment:
    id: str
    learner_id: str
    created_action: str
    head: CommitmentVersion
    disposition: str
    created: bool = True
    merge_candidate: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Normalization + hashing
# ---------------------------------------------------------------------------

def _coerce_targets(targets: Sequence[Mapping[str, Any] | CommitmentTarget]) -> list[CommitmentTarget]:
    out: list[CommitmentTarget] = []
    for raw in targets:
        if isinstance(raw, CommitmentTarget):
            target = raw
        else:
            kind = raw.get("target_kind")
            ref = raw.get("target_ref")
            role = raw.get("role", "required")
            if kind not in TARGET_KINDS:
                raise InvalidTarget(f"unknown target kind: {kind!r}")
            if role not in ("required", "optional"):
                raise InvalidTarget(f"unknown target role: {role!r}")
            if not ref:
                raise InvalidTarget("target_ref is required")
            target = CommitmentTarget(
                target_kind=kind,
                target_ref=str(ref),
                role=role,
                salience=raw.get("salience"),
                provenance=dict(raw.get("provenance")) if raw.get("provenance") else None,
            )
        if target.target_kind not in TARGET_KINDS:
            raise InvalidTarget(f"unknown target kind: {target.target_kind!r}")
        out.append(target)
    return out


def target_set_hash(targets: Sequence[CommitmentTarget]) -> str:
    """Order-independent identity of the target set (§3.1 idempotency key)."""

    return _canonical_hash(sorted((t.normalized() for t in targets), key=_json))


def _version_hash(
    fields: Mapping[str, Any],
    targets: Sequence[CommitmentTarget],
    *,
    predecessor_version_id: str | None,
    version: int,
) -> str:
    """Chain-aware content hash: identity of this version's content plus its position
    in the append-only chain. Position is included so a legitimate later version that
    restores a prior content shape (e.g. add-then-remove a target) is still a
    distinct, unique version rather than a UNIQUE(commitment_id, version_hash)
    collision with the earlier one."""

    payload = {
        **{k: v for k, v in fields.items() if k != "version_hash"},
        "targets": sorted((t.normalized() for t in targets), key=_json),
        "predecessor_version_id": predecessor_version_id,
        "version": version,
    }
    return _canonical_hash(payload)


def _default_depth_body(action: str, preset: str) -> dict[str, Any]:
    policy = _ACTION_DEFAULT_POLICY.get(action, "suggest_next")
    return {
        "schema_version": DEPTH_POLICY_SCHEMA_VERSION,
        "policy": policy,
        "derived_from_action": action,
        "derived_from_preset": preset,
    }


def _default_envelope_body(preset: str) -> dict[str, Any]:
    # The four coarse presets expand into an editable proposed envelope (§3.1.1,
    # §3.4). At creation the reviewed-edge DAG is empty; the immutable envelope --
    # not the preset label -- is authoritative.
    return {
        "schema_version": DEPTH_ENVELOPE_SCHEMA_VERSION,
        "preset": preset,
        "bounds": {},
        "reviewed_edges": [],
    }


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def create_commitment(
    repository: Repository,
    *,
    action: str,
    intent_text: str,
    targets: Sequence[Mapping[str, Any] | CommitmentTarget],
    depth_preset: str,
    interpretation_text: str | None = None,
    client_idempotency_key: str | None = None,
    goal_id: str | None = None,
    author: str = "learner",
    learner_id: str = "local",
    attention_bounds: Mapping[str, Any] | None = None,
    due_hint: str | None = None,
    hiatus_hint: str | None = None,
    reason: str | None = None,
    provenance: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> Commitment:
    """Create a durable commitment from an explicit commit-class action (§3.1).

    Enforces invariant 4 (only the four commit actions reach here). Idempotent on
    ``learner + normalized target set + action + client idempotency key``. Without a
    client key, a matching commitment is returned as a *merge candidate* (never a
    silent merge of differently worded intent, §3.1)."""

    if action not in COMMIT_ACTIONS:
        raise PassiveActionCannotCommit(action)
    if depth_preset not in DEPTH_PRESETS:
        raise InvalidTarget(f"unknown depth preset: {depth_preset!r}")
    coerced = _coerce_targets(targets)
    ts_hash = target_set_hash(coerced)

    # Idempotency / merge-candidate resolution (§3.1).
    if client_idempotency_key is not None:
        existing = repository.find_commitment_by_idempotency(
            learner_id=learner_id,
            created_action=action,
            target_set_hash=ts_hash,
            idempotency_key=client_idempotency_key,
        )
        if existing is not None:
            return _load_commitment(repository, existing["id"], created=False)
    else:
        candidate = repository.find_commitment_candidate(
            learner_id=learner_id, created_action=action, target_set_hash=ts_hash
        )
        if candidate is not None:
            return _load_commitment(
                repository, candidate["id"], created=False, merge_candidate=True
            )

    policy_body = _default_depth_body(action, depth_preset)
    policy_id = repository.ensure_depth_policy_version(
        policy=policy_body["policy"],
        body_json=_json(policy_body),
        content_hash=_canonical_hash(policy_body),
        clock=clock,
    )
    envelope_body = _default_envelope_body(depth_preset)
    envelope_id = repository.ensure_depth_envelope_version(
        envelope_version=f"env-{DEPTH_ENVELOPE_SCHEMA_VERSION}",
        bounds_json=_json(envelope_body["bounds"]),
        reviewed_edges_json=_json(envelope_body["reviewed_edges"]),
        content_hash=_canonical_hash(envelope_body),
        clock=clock,
    )

    version_fields = {
        "intent_text": intent_text,
        "interpretation_text": interpretation_text,
        "goal_id": goal_id,
        "depth_preset": depth_preset,
        "depth_policy_version_id": policy_id,
        "depth_envelope_version_id": envelope_id,
        "attention_bounds_json": _json(dict(attention_bounds)) if attention_bounds else None,
        "due_hint": due_hint,
        "hiatus_hint": hiatus_hint,
        "reason": reason,
        "provenance_json": _json(dict(provenance)) if provenance else None,
        "target_set_hash": ts_hash,
    }
    version_fields["version_hash"] = _version_hash(
        version_fields, coerced, predecessor_version_id=None, version=1
    )

    commitment_id, created = repository.create_commitment(
        learner_id=learner_id,
        created_action=action,
        idempotency_key=client_idempotency_key,
        version_fields=version_fields,
        targets=[_target_row(t) for t in coerced],
        author=author,
        change_reason=None,
        clock=clock,
    )
    # B6: on an idempotency-key race the DB backstop returns the winner (created=False).
    return _load_commitment(repository, commitment_id, created=created)


def _target_row(t: CommitmentTarget) -> dict[str, Any]:
    return {
        "target_kind": t.target_kind,
        "target_ref": t.target_ref,
        "role": t.role,
        "salience": t.salience,
        "provenance_json": _json(t.provenance) if t.provenance else None,
    }


# ---------------------------------------------------------------------------
# Version append + targets (§3.2)
# ---------------------------------------------------------------------------

def append_commitment_version(
    repository: Repository,
    *,
    commitment_id: str,
    targets: Sequence[Mapping[str, Any] | CommitmentTarget] | None = None,
    intent_text: str | None = None,
    interpretation_text: str | None = None,
    goal_id: str | None = None,
    depth_preset: str | None = None,
    change_reason: str,
    author: str = "learner",
    extra_events: Sequence[Mapping[str, Any]] = (),
    clock: Clock | None = None,
) -> CommitmentVersion:
    """Append an immutable successor version. Prior version bytes/hash are untouched
    (invariant 5). Recomputes target_set_hash/version_hash and fires the
    ``version_appended`` event plus any typed events supplied by the caller."""

    head = _require_head(repository, commitment_id)
    new_targets = (
        _coerce_targets(targets) if targets is not None else list(head.targets)
    )
    ts_hash = target_set_hash(new_targets)
    version_fields = {
        "intent_text": intent_text if intent_text is not None else head.intent_text,
        "interpretation_text": interpretation_text
        if interpretation_text is not None
        else head.interpretation_text,
        "goal_id": goal_id if goal_id is not None else head.goal_id,
        "depth_preset": depth_preset if depth_preset is not None else head.depth_preset,
        "depth_policy_version_id": head.depth_policy_version_id,
        "depth_envelope_version_id": head.depth_envelope_version_id,
        "attention_bounds_json": None,
        "due_hint": None,
        "hiatus_hint": None,
        "reason": None,
        "provenance_json": None,
        "target_set_hash": ts_hash,
    }
    version_fields["version_hash"] = _version_hash(
        version_fields, new_targets, predecessor_version_id=head.id, version=head.version + 1
    )

    events = [{"kind": "version_appended", "detail": {"change_reason": change_reason}}]
    events.extend(dict(e) for e in extra_events)
    repository.append_commitment_version(
        commitment_id=commitment_id,
        predecessor_version_id=head.id,
        version=head.version + 1,
        version_fields=version_fields,
        targets=[_target_row(t) for t in new_targets],
        author=author,
        change_reason=change_reason,
        events=events,
        clock=clock,
    )
    return _load_commitment(repository, commitment_id, created=False).head


def add_target(
    repository: Repository,
    *,
    commitment_id: str,
    target: Mapping[str, Any] | CommitmentTarget,
    change_reason: str = "target_added",
    author: str = "learner",
    clock: Clock | None = None,
) -> CommitmentVersion:
    head = _require_head(repository, commitment_id)
    new = list(head.targets) + _coerce_targets([target])
    added = _coerce_targets([target])[0]
    return append_commitment_version(
        repository,
        commitment_id=commitment_id,
        targets=new,
        change_reason=change_reason,
        author=author,
        extra_events=[{"kind": "target_added", "detail": added.normalized()}],
        clock=clock,
    )


def remove_target(
    repository: Repository,
    *,
    commitment_id: str,
    target_ref: str,
    change_reason: str = "target_removed",
    author: str = "learner",
    clock: Clock | None = None,
) -> CommitmentVersion:
    """Remove a target: appends a commitment successor and stops future generation
    for it. It never deletes observations already mapped to it (§3.2) -- observations
    live on the P0 activity ledger, untouched by this append-only version bump."""

    head = _require_head(repository, commitment_id)
    remaining = [t for t in head.targets if t.target_ref != target_ref]
    if len(remaining) == len(head.targets):
        raise InvalidTarget(f"target not present: {target_ref!r}")
    return append_commitment_version(
        repository,
        commitment_id=commitment_id,
        targets=remaining,
        change_reason=change_reason,
        author=author,
        extra_events=[{"kind": "target_removed", "detail": {"target_ref": target_ref}}],
        clock=clock,
    )


# ---------------------------------------------------------------------------
# Depth changes (A.3): version bump + typed event in one transaction
# ---------------------------------------------------------------------------

def change_depth_policy(
    repository: Repository,
    *,
    commitment_id: str,
    policy: str,
    body: Mapping[str, Any] | None = None,
    change_reason: str = "depth_policy_changed",
    author: str = "learner",
    clock: Clock | None = None,
) -> CommitmentVersion:
    if policy not in ("hold_at_target", "suggest_next", "auto_within_envelope"):
        raise InvalidTarget(f"unknown depth policy: {policy!r}")
    head = _require_head(repository, commitment_id)
    policy_body = dict(body or {})
    policy_body.setdefault("schema_version", DEPTH_POLICY_SCHEMA_VERSION)
    policy_body["policy"] = policy
    policy_id = repository.ensure_depth_policy_version(
        policy=policy,
        body_json=_json(policy_body),
        content_hash=_canonical_hash(policy_body),
        clock=clock,
    )
    # B8: a no-op change (the resolved policy version equals the head's active one)
    # short-circuits -- no version bump, no typed event (A.3 only fires on a real
    # change to the active policy id).
    if policy_id == head.depth_policy_version_id:
        return head
    return _append_depth_version(
        repository,
        head=head,
        depth_policy_version_id=policy_id,
        depth_envelope_version_id=head.depth_envelope_version_id,
        event_kind="depth_policy_changed",
        detail={"from": head.depth_policy_version_id, "to": policy_id, "policy": policy},
        change_reason=change_reason,
        author=author,
        clock=clock,
    )


def change_depth_envelope(
    repository: Repository,
    *,
    commitment_id: str,
    bounds: Mapping[str, Any],
    reviewed_edges: Sequence[Mapping[str, Any]] = (),
    change_reason: str = "depth_envelope_changed",
    author: str = "learner",
    allow_widen: bool = False,
    clock: Clock | None = None,
) -> CommitmentVersion:
    head = _require_head(repository, commitment_id)
    # F4: an envelope change may only CONTRACT the authorized region unless it
    # arrives via the confirmed-successor path (allow_widen=True). A "shrink"
    # that adds authorization on any dimension is rejected, naming the dimension.
    if not allow_widen:
        current = _current_envelope_bounds(repository, head.depth_envelope_version_id)
        widened = envelope_widening_dimension(dict(bounds), current)
        if widened is not None:
            raise EnvelopeWideningRejected(widened)
    envelope_body = {
        "schema_version": DEPTH_ENVELOPE_SCHEMA_VERSION,
        "bounds": dict(bounds),
        "reviewed_edges": [dict(e) for e in reviewed_edges],
    }
    envelope_id = repository.ensure_depth_envelope_version(
        envelope_version=f"env-{DEPTH_ENVELOPE_SCHEMA_VERSION}",
        bounds_json=_json(envelope_body["bounds"]),
        reviewed_edges_json=_json(envelope_body["reviewed_edges"]),
        content_hash=_canonical_hash(envelope_body),
        clock=clock,
    )
    # B8: a no-op envelope change (resolved id == head's active envelope) short-circuits.
    if envelope_id == head.depth_envelope_version_id:
        return head
    return _append_depth_version(
        repository,
        head=head,
        depth_policy_version_id=head.depth_policy_version_id,
        depth_envelope_version_id=envelope_id,
        event_kind="depth_envelope_changed",
        detail={"from": head.depth_envelope_version_id, "to": envelope_id},
        change_reason=change_reason,
        author=author,
        clock=clock,
    )


def _append_depth_version(
    repository: Repository,
    *,
    head: CommitmentVersion,
    depth_policy_version_id: str | None,
    depth_envelope_version_id: str | None,
    event_kind: str,
    detail: Mapping[str, Any],
    change_reason: str,
    author: str,
    clock: Clock | None,
) -> CommitmentVersion:
    ts_hash = target_set_hash(head.targets)
    version_fields = {
        "intent_text": head.intent_text,
        "interpretation_text": head.interpretation_text,
        "goal_id": head.goal_id,
        "depth_preset": head.depth_preset,
        "depth_policy_version_id": depth_policy_version_id,
        "depth_envelope_version_id": depth_envelope_version_id,
        "attention_bounds_json": None,
        "due_hint": None,
        "hiatus_hint": None,
        "reason": None,
        "provenance_json": None,
        "target_set_hash": ts_hash,
    }
    version_fields["version_hash"] = _version_hash(
        version_fields, head.targets, predecessor_version_id=head.id, version=head.version + 1
    )
    repository.append_commitment_version(
        commitment_id=head.commitment_id,
        predecessor_version_id=head.id,
        version=head.version + 1,
        version_fields=version_fields,
        targets=[_target_row(t) for t in head.targets],
        author=author,
        change_reason=change_reason,
        events=[
            {"kind": "version_appended", "detail": {"change_reason": change_reason}},
            {"kind": event_kind, "detail": dict(detail)},
        ],
        clock=clock,
    )
    return _load_commitment(repository, head.commitment_id, created=False).head


# ---------------------------------------------------------------------------
# Disposition + milestone events (no version bump)
# ---------------------------------------------------------------------------

def change_disposition(
    repository: Repository,
    *,
    commitment_id: str,
    disposition: str,
    clock: Clock | None = None,
) -> str:
    """Append a ``disposition_changed`` event only; disposition is a projection over
    events (§3.1), so no version bump. Returns the resolved disposition."""

    if disposition not in DISPOSITIONS:
        raise InvalidTarget(f"unknown disposition: {disposition!r}")
    _require_head(repository, commitment_id)
    repository.append_commitment_event(
        commitment_id=commitment_id,
        commitment_version_id=None,
        kind="disposition_changed",
        detail_json=_json({"disposition": disposition}),
        clock=clock,
    )
    return resolve_disposition(repository, commitment_id)


def pause(repository: Repository, *, commitment_id: str, clock: Clock | None = None) -> str:
    _require_head(repository, commitment_id)
    repository.append_commitment_event(
        commitment_id=commitment_id, commitment_version_id=None, kind="paused",
        detail_json=None, clock=clock,
    )
    return resolve_disposition(repository, commitment_id)


def resume(repository: Repository, *, commitment_id: str, clock: Clock | None = None) -> str:
    _require_head(repository, commitment_id)
    repository.append_commitment_event(
        commitment_id=commitment_id, commitment_version_id=None, kind="resumed",
        detail_json=None, clock=clock,
    )
    return resolve_disposition(repository, commitment_id)


def retire(repository: Repository, *, commitment_id: str, clock: Clock | None = None) -> str:
    _require_head(repository, commitment_id)
    repository.append_commitment_event(
        commitment_id=commitment_id, commitment_version_id=None, kind="retired",
        detail_json=None, clock=clock,
    )
    return resolve_disposition(repository, commitment_id)


def satisfy_single_check(
    repository: Repository, *, commitment_id: str, administration_id: str | None = None,
    clock: Clock | None = None,
) -> str:
    """One eligible delayed cold administration satisfies a ``test_me_later``
    commitment (§3.1): ``one_check_pending`` -> ``satisfied``, never an open-ended
    review obligation. A no-op for a commitment not currently pending its check."""

    disposition = resolve_disposition(repository, commitment_id)
    if disposition != "one_check_pending":
        return disposition
    repository.append_commitment_event(
        commitment_id=commitment_id,
        commitment_version_id=None,
        kind="disposition_changed",
        detail_json=_json({"disposition": "satisfied", "administration_id": administration_id}),
        clock=clock,
    )
    return resolve_disposition(repository, commitment_id)


def record_milestone_reached(
    repository: Repository,
    *,
    commitment_id: str,
    milestone_slug: str,
    detail: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> None:
    """Append ``depth_milestone_reached``: an achievement fact over the existing
    authored envelope. No version bump (A.3) and it never clears a prior success or
    the ``satisfied`` disposition (§3.1.1 achievement monotonicity)."""

    _require_head(repository, commitment_id)
    payload = {"milestone_slug": milestone_slug}
    if detail:
        payload.update(dict(detail))
    repository.append_commitment_event(
        commitment_id=commitment_id,
        commitment_version_id=None,
        kind="depth_milestone_reached",
        detail_json=_json(payload),
        clock=clock,
    )


def record_depth_transition_committed(
    repository: Repository,
    *,
    commitment_id: str,
    detail: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> str:
    """Append ``depth_transition_committed``: an activation fact over the existing
    authored envelope (A.3). Like ``depth_milestone_reached`` it changes neither the
    active policy id nor the active envelope id, so it appends only the event -- no
    version bump. Emitted by the one-edge depth-transition service (§5.7)."""

    _require_head(repository, commitment_id)
    return repository.append_commitment_event(
        commitment_id=commitment_id,
        commitment_version_id=None,
        kind="depth_transition_committed",
        detail_json=_json(dict(detail)) if detail else None,
        clock=clock,
    )


def attach_family(
    repository: Repository, *, commitment_id: str, family_id: str, clock: Clock | None = None
) -> None:
    _require_head(repository, commitment_id)
    repository.append_commitment_event(
        commitment_id=commitment_id, commitment_version_id=None, kind="family_attached",
        detail_json=_json({"family_id": family_id}), clock=clock,
    )


def detach_family(
    repository: Repository, *, commitment_id: str, family_id: str, clock: Clock | None = None
) -> None:
    _require_head(repository, commitment_id)
    repository.append_commitment_event(
        commitment_id=commitment_id, commitment_version_id=None, kind="family_detached",
        detail_json=_json({"family_id": family_id}), clock=clock,
    )


# ---------------------------------------------------------------------------
# Projections
# ---------------------------------------------------------------------------

def resolve_disposition(repository: Repository, commitment_id: str) -> str:
    """Fold ``commitment_events`` to one disposition (§3.1). ``test_me_later`` starts
    ``one_check_pending``; other actions start ``active``. Family/card retirement is
    recorded separately and never changes commitment disposition implicitly."""

    commitment = repository.commitment(commitment_id)
    if commitment is None:
        raise UnknownCommitment(commitment_id)
    disposition = (
        "one_check_pending" if commitment["created_action"] == "test_me_later" else "active"
    )
    for event in repository.commitment_events_for(commitment_id):
        kind = event["kind"]
        if kind == "disposition_changed":
            detail = _loads(event["detail_json"])
            new = detail.get("disposition")
            if new in DISPOSITIONS:
                disposition = new
        elif kind == "paused":
            disposition = "paused"
        elif kind == "resumed":
            disposition = "active"
        elif kind == "retired":
            disposition = "stopped"
    return disposition


def resolve_head(repository: Repository, commitment_id: str) -> CommitmentVersion:
    return _require_head(repository, commitment_id)


def load_commitment(repository: Repository, commitment_id: str) -> Commitment:
    return _load_commitment(repository, commitment_id, created=False)


# ---------------------------------------------------------------------------
# Internal loaders
# ---------------------------------------------------------------------------

def _loads(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    import json

    return json.loads(value)


def _current_envelope_bounds(
    repository: Repository, envelope_version_id: str | None
) -> dict[str, Any]:
    """Bounds of the head's active depth envelope (empty when unset)."""
    if not envelope_version_id:
        return {}
    row = repository.depth_envelope_version(envelope_version_id)
    if row is None:
        return {}
    return _loads(row.get("bounds_json"))


def _version_from_row(row: Mapping[str, Any], targets: Sequence[Mapping[str, Any]]) -> CommitmentVersion:
    return CommitmentVersion(
        id=row["id"],
        commitment_id=row["commitment_id"],
        version=row["version"],
        predecessor_version_id=row["predecessor_version_id"],
        intent_text=row["intent_text"],
        interpretation_text=row["interpretation_text"],
        goal_id=row["goal_id"],
        depth_preset=row["depth_preset"],
        depth_policy_version_id=row["depth_policy_version_id"],
        depth_envelope_version_id=row["depth_envelope_version_id"],
        target_set_hash=row["target_set_hash"],
        version_hash=row["version_hash"],
        author=row["author"],
        change_reason=row["change_reason"],
        targets=tuple(
            CommitmentTarget(
                target_kind=t["target_kind"],
                target_ref=t["target_ref"],
                role=t["role"],
                salience=t["salience"],
                provenance=_loads(t["provenance_json"]) or None,
            )
            for t in targets
        ),
    )


def _require_head(repository: Repository, commitment_id: str) -> CommitmentVersion:
    head_row = repository.commitment_head(commitment_id)
    if head_row is None:
        raise UnknownCommitment(commitment_id)
    targets = repository.commitment_targets_for_version(head_row["id"])
    return _version_from_row(head_row, targets)


def _load_commitment(
    repository: Repository, commitment_id: str, *, created: bool, merge_candidate: bool = False
) -> Commitment:
    commitment = repository.commitment(commitment_id)
    if commitment is None:
        raise UnknownCommitment(commitment_id)
    head = _require_head(repository, commitment_id)
    return Commitment(
        id=commitment["id"],
        learner_id=commitment["learner_id"],
        created_action=commitment["created_action"],
        head=head,
        disposition=resolve_disposition(repository, commitment_id),
        created=created,
        merge_candidate=merge_candidate,
    )
