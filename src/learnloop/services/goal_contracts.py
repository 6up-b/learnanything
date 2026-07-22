"""Terminal-contract versioning + consumer pins (spec_p0_measurement_correctness §3.4).

The confirmed terminal contract is the Layer-5 goal shape: purpose, exemplars,
required facets/capabilities, task regime, administration conditions, held-out/
practice eligibility, acceptable performance/rubric, the named baseline depth
milestone, and (when enabled) the learner-confirmed DepthEnvelope. Before
confirmation it is a mutable ``goals.yaml`` draft that no consumer may pin;
``confirm_goal_contract`` validates >=1 exemplar + a reviewed blueprint and
appends v1. Every post-confirmation material edit APPENDS an immutable successor
whose ``change_class`` the SERVICE computes (never the caller). SQLite is
authoritative for confirmed versions and pins; ``goals.yaml`` keeps the
pre-confirmation draft and a controlled-writer mirror of the head id.

``support_hash`` is computed over the SUPPORT-group subset only, so
``support_change`` / ``authorized_depth_step`` successors carry a *changed*
support hash (old reserves become unrepresentative of the new head) while
``reweight`` / ``evaluation_change`` / ``metadata`` successors leave it unchanged
(old reserves stay representative). Representativeness is a projection-time
comparison against the current head -- never a mutation of an immutable pin.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.activities import _canonical_hash, _json
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml

# Provenance/version pins (design §9) -- versioned, NOT tunable knobs.
CONTRACT_SCHEMA_VERSION = 1
DEPTH_ENVELOPE_SNAPSHOT_SCHEMA_VERSION = 1
CHANGE_CLASS_PARTITION_VERSION = 1


# ---------------------------------------------------------------------------
# Exceptions (§7.3)
# ---------------------------------------------------------------------------

class DraftNotConfirmable(Exception):
    """A pre-confirmation draft fails the confirmation gate (§3.4)."""

    def __init__(self, reason: str):
        super().__init__(f"draft not confirmable: {reason}")
        self.reason = reason


class NotConfirmed(Exception):
    """A successor was requested for a goal that has no confirmed head."""

    def __init__(self, goal_id: str):
        super().__init__(f"goal has no confirmed terminal contract: {goal_id}")
        self.goal_id = goal_id


class UseDepthSuccessor(Exception):
    """A support edit that advances the depth milestone must go through
    ``append_authorized_depth_successor`` (§3.4)."""

    def __init__(self, goal_id: str):
        super().__init__(
            f"edit advances the depth milestone; use append_authorized_depth_successor: {goal_id}"
        )
        self.goal_id = goal_id


class NoTargetPin(Exception):
    """A goal-conditioned terminal claim was requested but the administration has
    no target pin (§7.3 "missing target pin -> no goal-conditioned terminal claim")."""

    def __init__(self, administration_id: str):
        super().__init__(f"administration has no target pin: {administration_id}")
        self.administration_id = administration_id


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ContractVersion:
    id: str
    goal_id: str
    version: int
    predecessor_version_id: str | None
    content_hash: str
    support_hash: str
    change_class: str
    contract: dict[str, Any]
    author: str
    reason: str | None
    envelope_version: str | None = None
    activated_edge_id: str | None = None
    minted: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Draft:
    id: str
    goal_id: str
    rejection_reason: str
    requires: str
    proposed_change_class: str | None
    predecessor_version_id: str | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SupportComparison:
    representative: bool
    pinned_support_hash: str | None
    head_support_hash: str | None
    head_version_id: str | None
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConsumerPin:
    consumer_kind: str
    consumer_id: str
    target_contract_version_id: str
    support_hash: str | None
    representative: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CertificationCitation:
    administration_id: str
    cited_version_id: str
    cited_version: int
    head_version_id: str | None
    representative: bool
    reason: str
    # M3 (§4.5): a citation is only a terminal claim when every observation under
    # the administration is terminal-eligible. A non-terminal observation (e.g.
    # feedback revealed before response) carries its eligibility_reason and never a
    # terminal claim.
    terminal: bool = True
    eligibility_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DriftReport:
    goal_id: str
    drifted: bool
    reason: str
    field_diff: dict[str, Any] = field(default_factory=dict)
    would_be_change_class: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Canonical body (§2.1) + field partition (§2.2)
# ---------------------------------------------------------------------------

def canonicalize_body(body: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a proposed contract body to the canonical Layer-5 shape (§2.1).

    Every extension slot is present so the content hash is stable; ``target_recall``
    is mirrored into ``evaluation.acceptable_performance`` (its canonical home).
    """

    target_recall = body.get("target_recall")
    evaluation = dict(body.get("evaluation") or {})
    acceptable = dict(evaluation.get("acceptable_performance") or {})
    if target_recall is not None:
        # Top-level target_recall is the canonical source of acceptable performance
        # (§2.1); it always wins so a changed target_recall propagates into the
        # evaluation subset (and thus the evaluation_change classification).
        acceptable["target_recall"] = target_recall
    evaluation["acceptable_performance"] = acceptable
    evaluation.setdefault("rubric", body.get("rubric") or {})

    return {
        "schema_version": int(body.get("schema_version", CONTRACT_SCHEMA_VERSION)),
        "kind": body.get("kind", "terminal"),
        "purpose": body.get("purpose"),
        "due_at": body.get("due_at"),
        "burden_bounds": dict(body.get("burden_bounds") or {}),
        "target_recall": target_recall,
        "facet_scope": {
            "concepts": sorted(list((body.get("facet_scope") or {}).get("concepts") or [])),
            "facets": sorted(list((body.get("facet_scope") or {}).get("facets") or [])),
        },
        "exemplars": [
            {
                "id": ex.get("id"),
                "surface_ref": ex.get("surface_ref"),
                "weight": ex.get("weight", 1.0),
                "note": ex.get("note"),
            }
            for ex in (body.get("exemplars") or [])
        ],
        "required_capabilities": sorted(list(body.get("required_capabilities") or []), key=_json),
        "task_types": sorted(list(body.get("task_types") or []), key=_json),
        "regime": dict(body.get("regime") or {}),
        "administration_conditions": dict(body.get("administration_conditions") or {}),
        "eligibility": {
            "held_out": (body.get("eligibility") or {}).get("held_out", True),
            "practice": (body.get("eligibility") or {}).get("practice", True),
        },
        "evaluation": evaluation,
        "exam": dict(body.get("exam") or {}),
        "baseline_milestone": body.get("baseline_milestone"),
        "depth_envelope": body.get("depth_envelope"),
    }


def _exemplar_identities(body: Mapping[str, Any]) -> list[dict[str, Any]]:
    # Membership/identity (order + id + surface_ref), NOT weight.
    return [
        {"id": ex.get("id"), "surface_ref": ex.get("surface_ref"), "note": ex.get("note")}
        for ex in (body.get("exemplars") or [])
    ]


def _exemplar_weights(body: Mapping[str, Any]) -> list[list[Any]]:
    return [[ex.get("id"), ex.get("weight", 1.0)] for ex in (body.get("exemplars") or [])]


def _support_subset(body: Mapping[str, Any]) -> dict[str, Any]:
    """The SUPPORT-group projection whose hash is ``support_hash`` (§2.4).

    Excludes weights, evaluation, and metadata. Includes the support-bearing
    bounds of the depth envelope so an authorized depth step changes it.
    """

    envelope = body.get("depth_envelope") or {}
    return {
        "exemplar_identities": _exemplar_identities(body),
        "facet_scope": body.get("facet_scope"),
        "required_capabilities": body.get("required_capabilities"),
        "task_types": body.get("task_types"),
        "regime": body.get("regime"),
        "administration_conditions": body.get("administration_conditions"),
        "eligibility": body.get("eligibility"),
        "depth_support": (envelope.get("bounds") if isinstance(envelope, Mapping) else None),
    }


def _evaluation_subset(body: Mapping[str, Any]) -> dict[str, Any]:
    evaluation = body.get("evaluation") or {}
    return {
        "acceptable_performance": evaluation.get("acceptable_performance"),
        "rubric": evaluation.get("rubric"),
    }


def support_hash(body: Mapping[str, Any]) -> str:
    return _canonical_hash(_support_subset(body))


def content_hash(body: Mapping[str, Any]) -> str:
    return _canonical_hash(body)


def compute_change_class(prev: Mapping[str, Any], new: Mapping[str, Any]) -> str:
    """Service-computed change class with most-invalidating-wins precedence (§2.2)."""

    if _json(_support_subset(prev)) != _json(_support_subset(new)):
        return "support_change"
    if _json(_evaluation_subset(prev)) != _json(_evaluation_subset(new)):
        return "evaluation_change"
    if _json(_exemplar_weights(prev)) != _json(_exemplar_weights(new)):
        return "reweight"
    return "metadata"


def _support_diff_touches_envelope(
    prev_body: Mapping[str, Any], new_body: Mapping[str, Any], envelope: Mapping[str, Any]
) -> bool:
    """Does the support diff intersect the active envelope's reviewed-edge
    dimensions (M5, §3.4/§2.5)? Such an edit must go through the authorized-depth
    path, not a plain ``support_change`` -- otherwise a plain successor could grow
    envelope-governed terminal support with no edge/evidence receipt."""

    bounds = envelope.get("bounds") or {}
    additions = set(bounds.get("target_additions") or []) | set(
        bounds.get("capability_additions") or []
    )
    prev_support = _support_subset(prev_body)
    new_support = _support_subset(new_body)
    for leaf_key in set(prev_support) | set(new_support):
        pv = prev_support.get(leaf_key)
        nv = new_support.get(leaf_key)
        if _json(pv) == _json(nv):
            continue
        if leaf_key == "facet_scope":
            prev_c = set((pv or {}).get("concepts") or [])
            new_c = set((nv or {}).get("concepts") or [])
            if (new_c - prev_c) & additions:
                return True
            if (prev_c - new_c) and bounds.get("concept_removals"):
                return True
            prev_f = sorted((pv or {}).get("facets") or [])
            new_f = sorted((nv or {}).get("facets") or [])
            if prev_f != new_f and "facets" in bounds:
                return True
        elif leaf_key == "required_capabilities":
            prev_caps = set(pv or [])
            new_caps = set(nv or [])
            if (new_caps - prev_caps) & additions:
                return True
            if (prev_caps - new_caps) and bounds.get("capability_removals"):
                return True
        elif leaf_key == "depth_support":
            continue  # a bounds mutation is caught by the depth path's Check 2/3
        elif leaf_key in bounds:
            return True
    return False


def _envelope_version(body: Mapping[str, Any]) -> str | None:
    envelope = body.get("depth_envelope")
    if isinstance(envelope, Mapping):
        return envelope.get("envelope_version")
    return None


# ---------------------------------------------------------------------------
# Confirmation + successors (§2.5)
# ---------------------------------------------------------------------------

def _row_to_version(row: Mapping[str, Any], *, minted: bool = True) -> ContractVersion:
    return ContractVersion(
        id=row["id"],
        goal_id=row["goal_id"],
        version=row["version"],
        predecessor_version_id=row["predecessor_version_id"],
        content_hash=row["content_hash"],
        support_hash=row["support_hash"],
        change_class=row["change_class"],
        contract=_loads_json(row["contract_json"]),
        author=row["author"],
        reason=row["reason"],
        envelope_version=row.get("envelope_version"),
        activated_edge_id=row.get("activated_edge_id"),
        minted=minted,
    )


def _loads_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    import json

    return json.loads(value)


def confirm_goal_contract(
    repository: Repository,
    *,
    goal_id: str,
    contract_body: Mapping[str, Any],
    author: str = "learner",
    vault: LoadedVault | None = None,
    clock: Clock | None = None,
) -> ContractVersion:
    """Validate the draft (>=1 exemplar + reviewed blueprint) and mint v1 (§3.4).

    On failure raises :class:`DraftNotConfirmable` and records the body as a
    non-pinnable ``goal_contract_drafts`` row. Idempotent: a second confirm of
    byte-identical bytes returns the existing v1.
    """

    body = canonicalize_body(contract_body)
    exemplars = body.get("exemplars") or []
    scope = body.get("facet_scope") or {}
    has_blueprint = bool(scope.get("concepts") or scope.get("facets") or body.get("required_capabilities"))
    has_baseline = bool(body.get("baseline_milestone"))

    if len(exemplars) < 1:
        repository.insert_goal_contract_draft(
            goal_id=goal_id,
            predecessor_version_id=None,
            proposed_contract_json=_json(body),
            proposed_change_class="confirm",
            rejection_reason="pre_confirmation_draft",
            requires="exemplar_and_blueprint",
            author=author,
            clock=clock,
        )
        raise DraftNotConfirmable("no_exemplar")
    if not (has_blueprint and has_baseline):
        repository.insert_goal_contract_draft(
            goal_id=goal_id,
            predecessor_version_id=None,
            proposed_contract_json=_json(body),
            proposed_change_class="confirm",
            rejection_reason="pre_confirmation_draft",
            requires="exemplar_and_blueprint",
            author=author,
            clock=clock,
        )
        raise DraftNotConfirmable("no_reviewed_blueprint")

    result = repository.append_goal_contract_version(
        goal_id=goal_id,
        version=1,
        predecessor_version_id=None,
        contract_json=_json(body),
        content_hash=content_hash(body),
        support_hash=support_hash(body),
        contract_schema_version=int(body.get("schema_version", CONTRACT_SCHEMA_VERSION)),
        change_class="confirm",
        author=author,
        reason=None,
        head_envelope_version=_envelope_version(body),
        clock=clock,
    )
    version = _row_to_version(result["version"], minted=not result["already_exists"])
    if vault is not None:
        _mirror_head_to_yaml(vault, goal_id, version.id, version.content_hash)
    return version


def append_successor(
    repository: Repository,
    *,
    goal_id: str,
    proposed_body: Mapping[str, Any],
    author: str = "learner",
    reason: str | None = None,
    vault: LoadedVault | None = None,
    clock: Clock | None = None,
) -> ContractVersion:
    """Append a successor with a SERVICE-computed change class (§2.2). Prior version
    bytes/hash are untouched. Raises :class:`NotConfirmed` when there is no head and
    :class:`UseDepthSuccessor` when the edit advances the depth milestone."""

    head_row = repository.fetch_goal_contract_head(goal_id)
    if head_row is None:
        raise NotConfirmed(goal_id)
    prev = repository.fetch_goal_contract_version(head_row["head_version_id"])
    assert prev is not None
    prev_body = _loads_json(prev["contract_json"])
    new_body = canonicalize_body(proposed_body)

    # A support edit that either advances the baseline depth milestone OR touches
    # the active envelope's reviewed-edge dimensions MUST go through the
    # authorized-depth path (M5, §3.4/§2.5). Goals with no active envelope keep the
    # plain support_change route.
    new_envelope = new_body.get("depth_envelope")
    envelope_active = isinstance(new_envelope, Mapping) and bool(
        new_envelope.get("reviewed_edges") or new_envelope.get("bounds")
    )
    if envelope_active and (
        prev_body.get("baseline_milestone") != new_body.get("baseline_milestone")
        or _support_diff_touches_envelope(prev_body, new_body, new_envelope)
    ):
        raise UseDepthSuccessor(goal_id)

    change_class = compute_change_class(prev_body, new_body)
    result = repository.append_goal_contract_version(
        goal_id=goal_id,
        version=head_row["head_version"] + 1,
        predecessor_version_id=prev["id"],
        contract_json=_json(new_body),
        content_hash=content_hash(new_body),
        support_hash=support_hash(new_body),
        contract_schema_version=int(new_body.get("schema_version", CONTRACT_SCHEMA_VERSION)),
        change_class=change_class,
        author=author,
        reason=reason,
        head_envelope_version=_envelope_version(new_body),
        clock=clock,
    )
    version = _row_to_version(result["version"], minted=not result["already_exists"])
    if vault is not None and version.minted:
        _mirror_head_to_yaml(vault, goal_id, version.id, version.content_hash)
    return version


def append_authorized_depth_successor(
    repository: Repository,
    *,
    goal_id: str,
    proposed_body: Mapping[str, Any],
    progression_decision: Mapping[str, Any] | None,
    predecessor_version_id: str | None = None,
    author: str = "controller",
    vault: LoadedVault | None = None,
    clock: Clock | None = None,
) -> ContractVersion | Draft:
    """Fail-closed one-edge authorized depth step (§3.4). Commits a version only when
    ALL five checks hold; otherwise writes a non-pinnable draft and returns it."""

    head_row = repository.fetch_goal_contract_head(goal_id)
    if head_row is None:
        raise NotConfirmed(goal_id)
    prev = repository.fetch_goal_contract_version(head_row["head_version_id"])
    assert prev is not None
    prev_body = _loads_json(prev["contract_json"])
    new_body = canonicalize_body(proposed_body)
    progression_decision = dict(progression_decision or {})

    def _reject(rejection_reason: str, requires: str) -> Draft:
        draft_id = repository.insert_goal_contract_draft(
            goal_id=goal_id,
            predecessor_version_id=prev["id"],
            proposed_contract_json=_json(new_body),
            proposed_change_class="authorized_depth_step",
            rejection_reason=rejection_reason,
            requires=requires,
            author=author,
            evidence_receipt_json=_json(progression_decision) if progression_decision else None,
            clock=clock,
        )
        return Draft(
            id=draft_id,
            goal_id=goal_id,
            rejection_reason=rejection_reason,
            requires=requires,
            proposed_change_class="authorized_depth_step",
            predecessor_version_id=prev["id"],
        )

    # Check 1: predecessor is the current head.
    if predecessor_version_id is not None and predecessor_version_id != prev["id"]:
        return _reject("predecessor_not_head", "learner_confirmed_successor")

    # Check 2: the active envelope version is unchanged across the edge.
    if _envelope_version(prev_body) != _envelope_version(new_body):
        return _reject("stale_envelope", "learner_confirmed_envelope")

    envelope = new_body.get("depth_envelope")
    if not isinstance(envelope, Mapping):
        return _reject("outside_envelope", "learner_confirmed_envelope")
    bounds = envelope.get("bounds") or {}
    reviewed_edges = envelope.get("reviewed_edges") or []

    # Check 3: EVERY changed support leaf must be authorized by an envelope bound,
    # not just facet_scope.concepts (H2 fail-open fix, §3.4). Diff the full support
    # subset leaf-wise; concept/capability ADDITIONS are authorized by the additions
    # bounds as before, but any OTHER changed support dimension (administration
    # conditions, regime, task types, eligibility, exemplar identity, concept/
    # capability removals) is authorized only if the envelope bounds explicitly name
    # it -- otherwise the edge is outside the envelope and cannot pin.
    additions = set(bounds.get("target_additions") or []) | set(
        bounds.get("capability_additions") or []
    )

    def _leaf_authorized(leaf_key: str, prev_val: Any, new_val: Any) -> bool:
        if leaf_key == "facet_scope":
            prev_c = set((prev_val or {}).get("concepts") or [])
            new_c = set((new_val or {}).get("concepts") or [])
            if not (new_c - prev_c).issubset(additions):
                return False  # an added concept the envelope never authorized
            if (prev_c - new_c) and not bounds.get("concept_removals"):
                return False  # concept removal the envelope never authorized
            prev_f = sorted((prev_val or {}).get("facets") or [])
            new_f = sorted((new_val or {}).get("facets") or [])
            if prev_f != new_f and "facets" not in bounds:
                return False  # facet-scope change the envelope never authorized
            return True
        if leaf_key == "required_capabilities":
            prev_caps = set(prev_val or [])
            new_caps = set(new_val or [])
            if not (new_caps - prev_caps).issubset(additions):
                return False
            if (prev_caps - new_caps) and not bounds.get("capability_removals"):
                return False
            return True
        if leaf_key == "depth_support":
            # The envelope's own bounds. Check 2 already pinned the envelope version
            # equal, so any change here is a same-version bounds mutation -> reject.
            return False
        # Every other support dimension must be explicitly named in the bounds.
        return leaf_key in bounds

    prev_support = _support_subset(prev_body)
    new_support = _support_subset(new_body)
    for leaf_key in set(prev_support) | set(new_support):
        prev_val = prev_support.get(leaf_key)
        new_val = new_support.get(leaf_key)
        if _json(prev_val) == _json(new_val):
            continue
        if not _leaf_authorized(leaf_key, prev_val, new_val):
            return _reject("outside_envelope", "learner_confirmed_envelope")

    # Check 4: the transition matches exactly one reviewed edge.
    from_milestone = prev_body.get("baseline_milestone")
    to_milestone = new_body.get("baseline_milestone")
    matches = [
        edge
        for edge in reviewed_edges
        if edge.get("from_milestone") == from_milestone
        and edge.get("to_milestone") == to_milestone
    ]
    reviewed_matches = [edge for edge in matches if edge.get("reviewed")]
    if len(reviewed_matches) == 0:
        return _reject("unreviewed_edge", "learner_confirmed_envelope")
    if len(reviewed_matches) >= 2:
        return _reject("multiple_edges", "learner_confirmed_envelope")
    edge = reviewed_matches[0]

    # Check 5: the cited progression decision carries qualifying evidence.
    if not progression_decision.get("qualifies") or not progression_decision.get("evidence_receipt"):
        return _reject("insufficient_evidence", "learner_confirmed_successor")

    result = repository.append_goal_contract_version(
        goal_id=goal_id,
        version=head_row["head_version"] + 1,
        predecessor_version_id=prev["id"],
        contract_json=_json(new_body),
        content_hash=content_hash(new_body),
        support_hash=support_hash(new_body),
        contract_schema_version=int(new_body.get("schema_version", CONTRACT_SCHEMA_VERSION)),
        change_class="authorized_depth_step",
        envelope_version=_envelope_version(new_body),
        predecessor_milestone=from_milestone,
        activated_edge_id=edge.get("edge_id"),
        evidence_receipt_json=_json(progression_decision),
        burden_delta_json=_json(edge.get("burden_delta") or bounds.get("cumulative_burden") or {}),
        author=author,
        reason="authorized_depth_step",
        head_envelope_version=_envelope_version(new_body),
        clock=clock,
    )
    version = _row_to_version(result["version"], minted=not result["already_exists"])
    if vault is not None and version.minted:
        _mirror_head_to_yaml(vault, goal_id, version.id, version.content_hash)
    return version


# ---------------------------------------------------------------------------
# Reads / projections
# ---------------------------------------------------------------------------

def resolve_head(repository: Repository, goal_id: str) -> ContractVersion | None:
    """The current head (O(1) via ``goal_contract_heads``). None when unconfirmed."""

    head_row = repository.fetch_goal_contract_head(goal_id)
    if head_row is None:
        return None
    row = repository.fetch_goal_contract_version(head_row["head_version_id"])
    return _row_to_version(row, minted=False) if row is not None else None


def compare_support(
    repository: Repository, *, goal_id: str, pinned_version_id: str | None
) -> SupportComparison:
    """Projection-time representativeness of a pinned version vs the current head.

    A pure read: it never mutates the pin (invariant 1/8, §3.4). ``representative``
    iff the pinned support hash equals the head support hash.
    """

    head_row = repository.fetch_goal_contract_head(goal_id)
    head_support = head_row["head_support_hash"] if head_row else None
    head_version_id = head_row["head_version_id"] if head_row else None
    if pinned_version_id is None:
        return SupportComparison(False, None, head_support, head_version_id, "no_pin")
    pinned = repository.fetch_goal_contract_version(pinned_version_id)
    pinned_support = pinned["support_hash"] if pinned else None
    if pinned is None:
        return SupportComparison(False, None, head_support, head_version_id, "unknown_version")
    representative = pinned_support == head_support
    return SupportComparison(
        representative=representative,
        pinned_support_hash=pinned_support,
        head_support_hash=head_support,
        head_version_id=head_version_id,
        reason="representative" if representative else "support_changed",
    )


def list_consumer_pins(repository: Repository, goal_id: str) -> list[ConsumerPin]:
    """UNION projection of every consumer pin for the goal (§1.5) with a live
    representativeness flag from :func:`compare_support`."""

    versions = repository.goal_contract_versions_for_goal(goal_id)
    version_ids = [row["id"] for row in versions]
    head_row = repository.fetch_goal_contract_head(goal_id)
    head_support = head_row["head_support_hash"] if head_row else None
    support_by_version = {row["id"]: row["support_hash"] for row in versions}
    pins = repository.consumer_pins_for_versions(version_ids)
    result: list[ConsumerPin] = []
    for pin in pins:
        version_id = pin["target_contract_version_id"]
        support = pin.get("target_support_hash") or support_by_version.get(version_id)
        result.append(
            ConsumerPin(
                consumer_kind=pin["consumer_kind"],
                consumer_id=pin["consumer_id"],
                target_contract_version_id=version_id,
                support_hash=support,
                representative=support == head_support,
            )
        )
    return result


def certify_from_administration(
    repository: Repository,
    *,
    administration_id: str,
    goal_conditioned: bool = True,
) -> CertificationCitation:
    """Cite the exact assessed target version and label its representativeness
    (§3.4, §4.5, §9.4). Raises :class:`NoTargetPin` for a goal-conditioned request
    with no pin (§7.3). Never rewrites the citation to the new head."""

    admin = repository.fetch_administration(administration_id)
    if admin is None:
        raise ValueError(f"unknown administration: {administration_id}")
    pin = admin.get("target_contract_version_id")
    if pin is None:
        if goal_conditioned:
            raise NoTargetPin(administration_id)
        return CertificationCitation(
            administration_id=administration_id,
            cited_version_id="",
            cited_version=0,
            head_version_id=None,
            representative=False,
            reason="not_goal_conditioned",
            terminal=False,
            eligibility_reason="not_goal_conditioned",
        )
    version = repository.fetch_goal_contract_version(pin)
    if version is None:
        raise ValueError(f"unknown target version: {pin}")
    comparison = compare_support(
        repository, goal_id=version["goal_id"], pinned_version_id=pin
    )

    # M3 (§4.5): terminal iff every observation under the administration is
    # terminal-eligible. Any non-terminal observation demotes the citation and
    # surfaces its eligibility_reason -- never a silent terminal claim.
    observations = repository.observations_for_administration(administration_id)
    non_terminal = [
        obs for obs in observations if obs.get("evidence_eligibility") != "terminal"
    ]
    terminal = not non_terminal
    eligibility_reason = None if terminal else (
        non_terminal[0].get("eligibility_reason") or "non_terminal_evidence"
    )
    return CertificationCitation(
        administration_id=administration_id,
        cited_version_id=pin,
        cited_version=version["version"],
        head_version_id=comparison.head_version_id,
        representative=comparison.representative,
        reason=comparison.reason,
        terminal=terminal,
        eligibility_reason=eligibility_reason,
    )


# ---------------------------------------------------------------------------
# goals.yaml mirror + drift (§3)
# ---------------------------------------------------------------------------

_YAML_DRIFT_FIELDS = ("purpose", "due_at", "target_recall", "facet_scope", "exam")


def _yaml_subset_from_goal(goal: Any) -> dict[str, Any]:
    scope = getattr(goal, "facet_scope", None)
    exam = getattr(goal, "exam", None)
    return canonicalize_body(
        {
            "purpose": getattr(goal, "title", None),
            "due_at": getattr(goal, "due_at", None),
            "target_recall": getattr(goal, "target_recall", None),
            "facet_scope": scope.model_dump() if scope is not None else {},
            "exam": exam.model_dump() if exam is not None else {},
        }
    )


def _yaml_subset_from_body(body: Mapping[str, Any]) -> dict[str, Any]:
    return canonicalize_body(
        {
            "purpose": body.get("purpose"),
            "due_at": body.get("due_at"),
            "target_recall": body.get("target_recall"),
            "facet_scope": body.get("facet_scope") or {},
            "exam": body.get("exam") or {},
        }
    )


def detect_contract_drift(
    vault: LoadedVault, repository: Repository, goal_id: str
) -> DriftReport:
    """Detect divergence between a confirmed goal's live YAML draft fields and its
    confirmed head (§3). Never reconciles: consumers keep pinning the confirmed
    head; adoption requires an explicit ``contracts amend`` (append_successor)."""

    head = resolve_head(repository, goal_id)
    if head is None:
        return DriftReport(goal_id=goal_id, drifted=False, reason="unconfirmed")
    goal = next((g for g in vault.goals if g.id == goal_id), None)
    if goal is None:
        return DriftReport(goal_id=goal_id, drifted=False, reason="goal_missing")
    yaml_body = _yaml_subset_from_goal(goal)
    head_body = _yaml_subset_from_body(head.contract)
    diff: dict[str, Any] = {}
    for field_name in _YAML_DRIFT_FIELDS:
        if _json(yaml_body.get(field_name)) != _json(head_body.get(field_name)):
            diff[field_name] = {"yaml": yaml_body.get(field_name), "head": head_body.get(field_name)}
    if not diff:
        return DriftReport(goal_id=goal_id, drifted=False, reason="in_sync")
    # The change_class the diff WOULD mint if adopted as a successor.
    merged = dict(head.contract)
    merged.update({k: yaml_body.get(k) for k in _YAML_DRIFT_FIELDS})
    would_be = compute_change_class(head.contract, canonicalize_body(merged))
    return DriftReport(
        goal_id=goal_id,
        drifted=True,
        reason="yaml_diverged_from_head",
        field_diff=diff,
        would_be_change_class=would_be,
    )


def _mirror_head_to_yaml(
    vault: LoadedVault, goal_id: str, head_version_id: str, head_content_hash: str
) -> None:
    """The single controlled writer of the confirmed-head mirror into goals.yaml
    (§3). Touches ONLY the two mirror fields; never the editable draft fields."""

    paths = VaultPaths(vault.root, vault.config)
    data = read_yaml(paths.goals_path)
    if not isinstance(data, dict):
        return
    for goal in data.get("goals") or []:
        if isinstance(goal, dict) and goal.get("id") == goal_id:
            goal["confirmed_contract_head_id"] = head_version_id
            goal["confirmed_contract_hash"] = head_content_hash
            break
    write_yaml(paths.goals_path, data)
