"""P4 step 1 -- the ControllerSnapshot (spec §3.1, design B step 1).

One immutable, content-hashed snapshot per decision, assembled from BULK/BOUNDED
reads. Every staged-policy decision consumes exactly one snapshot; its hash is logged
on the decision trace so the whole choice replays from events (§16.10). The §9.7-style
operability bar is hard: the builder issues a FIXED, small number of full-table reads
and never one query per candidate (enforced by the bounded-query acceptance test).

The snapshot carries the §3.1 material the constraint engine + staged policy read:
learner-state projections, commitments + heads + depth policy/envelope + milestones,
the goal-contract heads, the global exposure/freshness index (the ONE ledger, §3.6),
assessment reserves, familiarity projections available BEFORE selection, the session
budget, and the registered parameter/projection versions. It contains NO cold-answer
material (leakage test).

Affect / failure-triage signals are DEFERRED for P4 (U-011, audit F5): the
``affect_by_commitment`` field exists in the contract as a forward-compatible slot but is
NOT loaded and is NOT part of the snapshot hash body. Until the affect event stream is
wired in (a later unit), the field is always empty and no decision depends on it -- so no
current test may assert affect content on the snapshot. Wiring it in later means loading
the events here AND adding them to the hashed ``body`` in the same change, so the decision
still replays from its hash.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services import commitments as C
from learnloop.services import controller_store as store
from learnloop.services import parameter_registry as pr
from learnloop.services.activities import _canonical_hash
from learnloop.vault.models import LoadedVault

SNAPSHOT_SCHEMA_VERSION = 1

# A conservative upper-bound minutes estimate used for a candidate whose duration is
# unknown, so the fatigue/budget constraint fails closed (§5: "unknown duration may
# fit only when its conservative upper bound fits the budget"). Heuristic.
CONSERVATIVE_DURATION_MINUTES = 3.0

# Administration purposes (P1 §3.10 vocabulary) a practice mode maps to.
_PURPOSE_DIAGNOSTIC = "diagnostic"
_PURPOSE_INSTRUCTIONAL = "instructional"
_PURPOSE_PRACTICE = "practice"
_PURPOSE_ASSESSMENT = "assessment"

_DIAGNOSTIC_MODES = frozenset({"teach_back", "diagnostic_microprobe", "probe"})


def _purpose_for_mode(practice_mode: str | None) -> str:
    if practice_mode is None:
        return _PURPOSE_PRACTICE
    if practice_mode in _DIAGNOSTIC_MODES or "probe" in practice_mode or "diagnostic" in practice_mode:
        return _PURPOSE_DIAGNOSTIC
    return _PURPOSE_PRACTICE


@dataclass(frozen=True)
class Candidate:
    """One selection candidate. All fields are pre-loaded (no DB read per candidate)."""

    candidate_ref: str
    learning_object_id: str | None = None
    active: bool = True
    quarantined: bool = False
    purpose: str = _PURPOSE_PRACTICE
    facet_id: str | None = None
    surface_id: str | None = None
    surface_hash: str | None = None
    fingerprint: str | None = None
    expected_minutes: float | None = None
    practice_mode: str | None = None
    due_at: str | None = None
    # P4 step 4 -- dispersion/interleaving material (§9.1/§9.2). All default-absent so
    # a candidate that carries none is never dispersed/interleaved (fail-open shaping).
    capability_id: str | None = None
    card_lineage_id: str | None = None
    hard_group_id: str | None = None
    soft_kinship_group: str | None = None
    neighborhood_id: str | None = None
    is_lapse_retry: bool = False
    in_frozen_target: bool = True

    def hashable(self) -> dict[str, Any]:
        return {
            "candidate_ref": self.candidate_ref,
            "learning_object_id": self.learning_object_id,
            "active": self.active,
            "quarantined": self.quarantined,
            "purpose": self.purpose,
            "facet_id": self.facet_id,
            "surface_id": self.surface_id,
            "surface_hash": self.surface_hash,
            "fingerprint": self.fingerprint,
            "expected_minutes": self.expected_minutes,
            "practice_mode": self.practice_mode,
            "due_at": self.due_at,
            "capability_id": self.capability_id,
            "card_lineage_id": self.card_lineage_id,
            "hard_group_id": self.hard_group_id,
            "soft_kinship_group": self.soft_kinship_group,
            "neighborhood_id": self.neighborhood_id,
            "is_lapse_retry": self.is_lapse_retry,
            "in_frozen_target": self.in_frozen_target,
        }


@dataclass(frozen=True)
class CommitmentSummary:
    commitment_id: str
    created_action: str
    disposition: str
    depth_policy: str | None
    depth_policy_version_id: str | None
    depth_envelope_version_id: str | None
    goal_id: str | None
    reached_milestones: tuple[str, ...]
    reviewed_edges: tuple[dict[str, Any], ...]

    def hashable(self) -> dict[str, Any]:
        return {
            "commitment_id": self.commitment_id,
            "created_action": self.created_action,
            "disposition": self.disposition,
            "depth_policy": self.depth_policy,
            "depth_policy_version_id": self.depth_policy_version_id,
            "depth_envelope_version_id": self.depth_envelope_version_id,
            "goal_id": self.goal_id,
            "reached_milestones": list(self.reached_milestones),
            "reviewed_edges": [dict(sorted(e.items())) for e in self.reviewed_edges],
        }


@dataclass(frozen=True)
class ControllerSnapshot:
    snapshot_hash: str
    session_id: str | None
    available_minutes: float | None
    energy: str | None
    remaining_minutes: float | None
    conservative_duration_minutes: float | None
    candidates: tuple[Candidate, ...]
    exposure_by_hash: Mapping[str, tuple[dict[str, Any], ...]]
    exposure_by_fingerprint: Mapping[str, tuple[dict[str, Any], ...]]
    reserved_assessment_surface_ids: frozenset[str]
    commitments: tuple[CommitmentSummary, ...]
    affect_by_commitment: Mapping[str, dict[str, Any]]
    param_manifest_hash: str
    projection_versions: Mapping[str, Any]
    # P4 step 4 -- the immediately preceding fresh-evidence administration, for
    # same-facet dispersion (§9.1). None when no fresh evidence has been served in the
    # session, so dispersion is inert.
    last_fresh_evidence: Mapping[str, Any] | None = None

    def commitment(self, commitment_id: str) -> CommitmentSummary | None:
        for c in self.commitments:
            if c.commitment_id == commitment_id:
                return c
        return None


def _controller_param_manifest_hash() -> str:
    """Deterministic hash over the registered controller decision/structural params
    (owner in the controller modules). No DB: the registry is a module-level dict."""

    owners = {"constraint_engine", "staged_policy", "controller_snapshot"}
    entries = {
        spec.path: {
            "kind": spec.kind, "param_class": spec.param_class,
            "status": spec.default_status, "lifecycle": spec.default_lifecycle,
        }
        for spec in pr.REGISTRY.values()
        if spec.owner in owners
    }
    return _canonical_hash(dict(sorted(entries.items())))


def _commitment_summary(repository: Repository, commitment_id: str) -> CommitmentSummary | None:
    try:
        head = C.resolve_head(repository, commitment_id)
    except Exception:
        return None
    disposition = C.resolve_disposition(repository, commitment_id)
    policy = None
    if head.depth_policy_version_id:
        row = repository.depth_policy_version(head.depth_policy_version_id)
        policy = row["policy"] if row is not None else None
    reviewed_edges: list[dict[str, Any]] = []
    if head.depth_envelope_version_id:
        env = repository.depth_envelope_version(head.depth_envelope_version_id)
        if env is not None:
            import json as _json_mod

            reviewed_edges = _json_mod.loads(env["reviewed_edges_json"] or "[]")
    reached: list[str] = []
    for event in repository.commitment_events_for(commitment_id):
        if event["kind"] == "depth_milestone_reached":
            import json as _json_mod

            detail = _json_mod.loads(event.get("detail_json") or "{}")
            milestone = detail.get("milestone") or detail.get("milestone_slug")
            if milestone:
                reached.append(milestone)
    return CommitmentSummary(
        commitment_id=commitment_id,
        created_action="",  # filled from the header row in build_snapshot
        disposition=disposition,
        depth_policy=policy,
        depth_policy_version_id=head.depth_policy_version_id,
        depth_envelope_version_id=head.depth_envelope_version_id,
        goal_id=head.goal_id,
        reached_milestones=tuple(reached),
        reviewed_edges=tuple(reviewed_edges),
    )


def _candidates_from_vault(
    vault: LoadedVault, states: Mapping[str, Any]
) -> list[Candidate]:
    candidates: list[Candidate] = []
    for item in vault.practice_items.values():
        state = states.get(item.id)
        active = True if state is None else bool(getattr(state, "active", True))
        facets = list(getattr(item, "evidence_facets", []) or [])
        candidates.append(
            Candidate(
                candidate_ref=item.id,
                learning_object_id=item.learning_object_id,
                active=active,
                quarantined=False,
                purpose=_purpose_for_mode(getattr(item, "practice_mode", None)),
                facet_id=facets[0] if facets else None,
                surface_id=None,
                surface_hash=None,
                fingerprint=None,
                expected_minutes=None,
                practice_mode=getattr(item, "practice_mode", None),
                due_at=getattr(state, "due_at", None) if state is not None else None,
            )
        )
    candidates.sort(key=lambda c: c.candidate_ref)
    return candidates


def build_snapshot(
    vault: LoadedVault,
    repository: Repository,
    session: Any | None = None,
    *,
    candidates: Sequence[Candidate] | None = None,
    clock: Clock | None = None,
) -> ControllerSnapshot:
    """Assemble one immutable, content-hashed ControllerSnapshot from bounded bulk
    reads (§3.1). ``session`` is the existing ``SchedulerSession`` (extended here, not
    forked). Pass explicit ``candidates`` to snapshot a specific candidate universe;
    otherwise the vault's practice items are the universe.

    Query budget (independent of candidate count): 1 practice-item-state read, 1
    exposure-ledger read, 1 commitment-header read, 1 assessment-reserve read, plus a
    fixed per-commitment head/event read (bounded by the commitment count, not the
    candidate count)."""

    states = repository.practice_item_states()  # 1 bulk read
    if candidates is None:
        cand_list = _candidates_from_vault(vault, states)
    else:
        cand_list = sorted(candidates, key=lambda c: c.candidate_ref)

    exposure_events = store.bulk_exposure_events(repository)  # 1 bulk read
    by_hash: dict[str, list[dict[str, Any]]] = {}
    by_fp: dict[str, list[dict[str, Any]]] = {}
    for ev in exposure_events:
        by_hash.setdefault(ev["surface_hash"], []).append(ev)
        fp = ev.get("fingerprint")
        if fp:
            by_fp.setdefault(fp, []).append(ev)

    # The immediately preceding fresh-evidence administration, for same-facet
    # dispersion (§9.1). The ledger carries surface hash/fingerprint (near-kin), not
    # facet/capability; finer dispersion material is plantable on the snapshot.
    last_fresh_evidence: dict[str, Any] | None = None
    for ev in reversed(exposure_events):
        if ev.get("consumes_unseen"):
            last_fresh_evidence = {
                "surface_hash": ev.get("surface_hash"),
                "fingerprint": ev.get("fingerprint"),
                "purpose": ev.get("purpose"),
                "intervening_administrations": 0,
            }
            break

    reserved = {row["id"] for row in repository.reserved_assessment_surfaces()}  # 1 read

    commitment_rows = store.bulk_commitment_rows(repository)  # 1 bulk read
    commitments: list[CommitmentSummary] = []
    # Affect/failure-triage signals are DEFERRED for P4 (U-011, audit F5): left empty,
    # never loaded, and NOT part of the snapshot hash body below. See the module docstring.
    affect_by_commitment: dict[str, dict[str, Any]] = {}
    for row in commitment_rows:
        summary = _commitment_summary(repository, row["id"])
        if summary is None:
            continue
        # created_action comes from the header row (avoids a placeholder).
        summary = CommitmentSummary(
            commitment_id=summary.commitment_id,
            created_action=row["created_action"],
            disposition=summary.disposition,
            depth_policy=summary.depth_policy,
            depth_policy_version_id=summary.depth_policy_version_id,
            depth_envelope_version_id=summary.depth_envelope_version_id,
            goal_id=summary.goal_id,
            reached_milestones=summary.reached_milestones,
            reviewed_edges=summary.reviewed_edges,
        )
        commitments.append(summary)

    session_id = getattr(session, "session_id", None) if session is not None else None
    available_minutes = getattr(session, "available_minutes", None) if session is not None else None
    energy = getattr(session, "energy", None) if session is not None else None
    remaining_minutes = float(available_minutes) if available_minutes is not None else None

    param_manifest_hash = _controller_param_manifest_hash()
    from learnloop.services import constraint_engine as ce

    projection_versions = {
        "snapshot_schema_version": SNAPSHOT_SCHEMA_VERSION,
        "constraint_manifest_hash": ce.manifest()["manifest_hash"],
        "constraint_manifest_version": ce.CONSTRAINT_MANIFEST_VERSION,
    }

    body = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "session": {
            "session_id": session_id,
            "available_minutes": available_minutes,
            "energy": energy,
        },
        "remaining_minutes": remaining_minutes,
        "conservative_duration_minutes": CONSERVATIVE_DURATION_MINUTES,
        "candidates": [c.hashable() for c in cand_list],
        "exposure_hashes": sorted(by_hash.keys()),
        "exposure_fingerprints": sorted(by_fp.keys()),
        "reserved_assessment_surface_ids": sorted(reserved),
        "commitments": [c.hashable() for c in commitments],
        "last_fresh_evidence": dict(sorted(last_fresh_evidence.items())) if last_fresh_evidence else None,
        "param_manifest_hash": param_manifest_hash,
        "projection_versions": dict(sorted(projection_versions.items())),
    }
    snapshot_hash = _canonical_hash(body)

    return ControllerSnapshot(
        snapshot_hash=snapshot_hash,
        session_id=session_id,
        available_minutes=available_minutes,
        energy=energy,
        remaining_minutes=remaining_minutes,
        conservative_duration_minutes=CONSERVATIVE_DURATION_MINUTES,
        candidates=tuple(cand_list),
        exposure_by_hash={k: tuple(v) for k, v in by_hash.items()},
        exposure_by_fingerprint={k: tuple(v) for k, v in by_fp.items()},
        reserved_assessment_surface_ids=frozenset(reserved),
        commitments=tuple(commitments),
        affect_by_commitment=affect_by_commitment,
        param_manifest_hash=param_manifest_hash,
        projection_versions=projection_versions,
        last_fresh_evidence=last_fresh_evidence,
    )


def persist_snapshot(
    repository: Repository, snapshot: ControllerSnapshot, *, clock: Clock | None = None
) -> str:
    """Persist (dedupe on content hash). Returns the snapshot row id."""

    body = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "candidates": [c.hashable() for c in snapshot.candidates],
        "commitments": [c.hashable() for c in snapshot.commitments],
        "exposure_hashes": sorted(snapshot.exposure_by_hash.keys()),
        "reserved_assessment_surface_ids": sorted(snapshot.reserved_assessment_surface_ids),
    }
    return store.upsert_snapshot(
        repository,
        snapshot_hash=snapshot.snapshot_hash,
        session_id=snapshot.session_id,
        body=body,
        param_manifest_hash=snapshot.param_manifest_hash,
        projection_versions=snapshot.projection_versions,
        clock=clock,
    )
