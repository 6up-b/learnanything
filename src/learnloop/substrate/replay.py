from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from learnloop.clock import Clock, FrozenClock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import AttemptResult, GradeAttribution, replay_existing_attempt
from learnloop.learner import mastery as learner_mastery
from learnloop.vault.models import LoadedVault


@dataclass(frozen=True)
class ReplayResult:
    learning_object_id: str
    replayed_attempts: int
    attempt_ids: list[str]

    def as_dict(self) -> dict[str, object]:
        return {
            "learning_object_id": self.learning_object_id,
            "replayed_attempts": self.replayed_attempts,
            "attempt_ids": self.attempt_ids,
        }


@dataclass(frozen=True)
class RebuildResult:
    algorithm_version: str
    rebuilt_learning_objects: int
    replayed_attempts: int
    learning_object_ids: list[str]
    marker_id: str | None = None

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "algorithm_version": self.algorithm_version,
            "rebuilt_learning_objects": self.rebuilt_learning_objects,
            "replayed_attempts": self.replayed_attempts,
            "learning_object_ids": self.learning_object_ids,
        }
        if self.marker_id is not None:
            payload["marker_id"] = self.marker_id
        return payload


def _restore_debug_audit_events(
    repository: Repository,
    attempt_id: str,
    prior_payload: Mapping[str, Any] | None,
) -> None:
    """Preserve decision-time firewall audit events across deterministic replay.

    The firewall can derive a write-barrier event on the first replay and encode
    the resulting block into the replacement error event.  A second replay then
    quite correctly derives no *new* barrier, but dropping the first audit event
    makes replay non-idempotent.  These events have no external source ledger;
    merge the prior and newly-derived lists by content after the attempt write.
    Diagnosis receipts are preserved separately by the repository writer.
    """

    prior_attribution = (
        prior_payload.get("causal_attribution")
        if isinstance(prior_payload, Mapping)
        else None
    )
    prior_events = (
        prior_attribution.get("firewall_events")
        if isinstance(prior_attribution, Mapping)
        else None
    )
    if not isinstance(prior_events, list) or not prior_events:
        return
    current_payload = repository.attempt_debug_payload(attempt_id)
    if not isinstance(current_payload, dict):
        return
    current_attribution = current_payload.get("causal_attribution")
    if not isinstance(current_attribution, dict):
        current_attribution = {}
        current_payload["causal_attribution"] = current_attribution
    current_events = current_attribution.get("firewall_events")
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for value in [*prior_events, *(current_events if isinstance(current_events, list) else [])]:
        if not isinstance(value, Mapping):
            continue
        event = dict(value)
        identity = json.dumps(event, sort_keys=True, separators=(",", ":"))
        if identity in seen:
            continue
        seen.add(identity)
        merged.append(event)
    current_attribution["firewall_events"] = merged
    with repository.connection() as connection:
        connection.execute(
            "UPDATE attempt_debug_payloads SET payload_json = ? WHERE attempt_id = ?",
            (
                json.dumps(current_payload, sort_keys=True, separators=(",", ":")),
                attempt_id,
            ),
        )
        connection.commit()


class _ClaimStream:
    """Claims replayed at their own ``created_at`` (LP-min (a); AD §5.5).

    The predecessor seeded a replayed LO from the claims in force at rebuild
    time, so a claim written after an attempt seeded that attempt's prior, and
    a re-anchoring claim made after the first attempt was lost (or became the
    seed). Here:

    * the seed is materialized just before the first attempt from the claims
      made by then (``claims_as_of``), exactly the state the attempt path would
      otherwise construct from them;
    * each later claim from a re-anchoring source
      (``mastery.REANCHORING_CLAIM_SOURCES``) re-anchors at its own instant
      through the live function, before any attempt stamped after it. A claim
      stamped at the same instant as an attempt goes first: a rung-variant
      request writes its claim, then its self-report attempt.

    Claims are mutable rows (a re-claim replaces the earlier one), so a
    replaced claim's earlier version is not replayed.
    """

    def __init__(self, vault: LoadedVault, repository: Repository, learning_object_id: str, claims: list[tuple[Any, dict[str, Any]]]):
        self._vault = vault
        self._repository = repository
        self._learning_object_id = learning_object_id
        self._pending = claims
        self._seeded = False

    @classmethod
    def open(cls, vault: LoadedVault, repository: Repository, learning_object_id: str) -> "_ClaimStream | None":
        if not learner_mastery.claim_fixes_live(vault):
            return None
        learning_object = vault.learning_objects.get(learning_object_id)
        if learning_object is None:
            return None
        claims: list[tuple[Any, dict[str, Any]]] = []
        for claim in repository.learner_claims():
            if str(claim.get("source")) not in learner_mastery.REANCHORING_CLAIM_SOURCES:
                continue
            if claim.get("scope_type") != "learning_object" or claim.get("scope_id") != learning_object_id:
                continue
            created = _parse_or_none(claim.get("created_at"))
            if created is None:
                continue  # unordered: it can only act through the seed
            claims.append((created, claim))
        claims.sort(key=lambda pair: (pair[0], str(pair[1].get("id") or "")))
        return cls(vault, repository, learning_object_id, claims)

    def advance_to(self, until_iso: str) -> None:
        """Apply every claim made by ``until_iso``; seed the row on first use."""

        until = parse_utc(until_iso)
        if not self._seeded:
            self._seeded = True
            if self._repository.mastery_state(self._learning_object_id) is None:
                self._repository.upsert_mastery_state(
                    learner_mastery.initial_mastery_state_for_learning_object(
                        self._vault,
                        self._repository,
                        self._learning_object_id,
                        until_iso,
                        claims_as_of=until_iso,
                    )
                )
            # Claims made by the first attempt are in its seed already.
            self._pending = [pair for pair in self._pending if pair[0] > until]
            return
        while self._pending and self._pending[0][0] <= until:
            _created, claim = self._pending.pop(0)
            self._reanchor(claim)

    def finish(self) -> None:
        while self._pending:
            _created, claim = self._pending.pop(0)
            self._reanchor(claim)

    def _reanchor(self, claim: dict[str, Any]) -> None:
        created_at = str(claim["created_at"])
        learner_mastery.reanchor_mastery_from_claim(
            self._vault,
            self._repository,
            self._learning_object_id,
            claimed_level=float(claim["claimed_level"]),
            prior_pseudo_count=float(claim["prior_pseudo_count"]),
            now_iso=created_at,
            claims_as_of=created_at,
        )


def _parse_or_none(value: Any):
    try:
        return parse_utc(str(value)) if value else None
    except ValueError:
        return None


def replay_learning_object(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    error_attribution_overrides: dict[str, list[GradeAttribution]] | None = None,
    grader_identity_overrides: dict[str, tuple[str, str] | None] | None = None,
    project_canonical_state: bool = True,
) -> ReplayResult:
    """Rebuild attempt-derived state for one learning object from persisted grades.

    Replay intentionally does not call Codex or any AI provider. It treats
    `practice_attempts` plus current non-superseded `grading_evidence` as the raw
    log, clears derived state for the learning object, then runs each attempt
    through the same computation path used by live attempts.

    ``grader_identity_overrides`` maps an attempt a regrade just re-graded to
    the calibration identity of its new grade; every other attempt replays
    under the identity its ledgers record.
    """

    attempts = repository.list_attempts_by_learning_object(learning_object_id)
    existing_error_events = {
        attempt["id"]: repository.raw_error_events_for_attempt(attempt["id"])
        for attempt in attempts
    }
    existing_debug_payloads = {
        attempt["id"]: repository.attempt_debug_payload(attempt["id"])
        for attempt in attempts
    }
    repository.reset_learning_object_derived_state(learning_object_id)
    # LP-min (a), the claim-fixes successor: claims enter the attempt stream at
    # their own time. Off, or below the tag: None, and the first attempt seeds
    # from the claims in force now, exactly as the predecessor.
    claim_stream = _ClaimStream.open(vault, repository, learning_object_id)
    replayed: list[AttemptResult] = []
    for attempt in attempts:
        observed_at = parse_utc(attempt.get("created_at"))
        clock = FrozenClock(observed_at) if observed_at is not None else None
        if claim_stream is not None and observed_at is not None:
            claim_stream.advance_to(str(attempt["created_at"]))
        override_attributions = (error_attribution_overrides or {}).get(attempt["id"])
        event_snapshot = existing_error_events.get(attempt["id"], [])
        replayed_result = replay_existing_attempt(
            vault,
            repository,
            attempt,
            clock=clock,
            error_event_ids=None if override_attributions is not None else [event["id"] for event in event_snapshot],
            error_events=event_snapshot,
            error_attributions=override_attributions,
            **(
                {"grader_identity": grader_identity_overrides[attempt["id"]]}
                if grader_identity_overrides and attempt["id"] in grader_identity_overrides
                else {}
            ),
        )
        _restore_debug_audit_events(
            repository,
            str(attempt["id"]),
            existing_debug_payloads.get(attempt["id"]),
        )
        replayed.append(replayed_result)
    if claim_stream is not None:
        # A re-anchoring claim made after the last attempt merges too, as it
        # did live at its own time.
        claim_stream.finish()
    # spec §7: registry links survive replay (persisted misconception_id on the
    # error events is re-threaded through GradeAttribution). Replay never
    # re-normalizes, but it re-derives resolution status deterministically from
    # the replayed attempts so a rebuilt vault matches the live one.
    from learnloop.diagnosis.misconceptions import update_misconception_posteriors_and_resolve

    update_misconception_posteriors_and_resolve(
        vault, repository, learning_object_id=learning_object_id
    )
    # KM2 §7.1: canonical shared belief is vault-level, so it is recomputed as a
    # whole-ledger projection (no-op under mvp-0.6). Idempotent and deterministic,
    # so replaying any subset of LOs reproduces byte-identical canonical state.
    if project_canonical_state:
        from learnloop.substrate.canonical_projection import project_canonical_facet_state

        # project_canonical_facet_state also derives KM5 §4.2 capability-residual
        # activation from the same event history (a no-op unless
        # [capabilities].residual_activation_enabled), so a rebuild reproduces
        # activation deterministically with the feature on or off.  The R2
        # umbrella disables this per-LO refresh and runs the vault-wide projector
        # once after every LO has replayed; direct callers refresh per LO by
        # default.
        project_canonical_facet_state(vault, repository)
    return ReplayResult(
        learning_object_id=learning_object_id,
        replayed_attempts=len(replayed),
        attempt_ids=[result.attempt_id for result in replayed],
    )


def rebuild_derived_state(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_ids: list[str] | None = None,
    clock: Clock | None = None,
    record_receipt: bool = True,
    project_canonical_state: bool = True,
) -> RebuildResult:
    """Replay all requested learning objects that have persisted attempts."""

    requested_ids = learning_object_ids or repository.learning_object_ids_with_attempts()
    rebuilt: list[str] = []
    replayed_attempts = 0
    for learning_object_id in requested_ids:
        if learning_object_id not in vault.learning_objects:
            continue
        result = replay_learning_object(
            vault,
            repository,
            learning_object_id,
            project_canonical_state=project_canonical_state,
        )
        rebuilt.append(learning_object_id)
        replayed_attempts += result.replayed_attempts
    scope = "learning_object" if learning_object_ids else "all"
    # P2 §4.4: the canonical projection's own semantics version is recorded
    # alongside the vault algorithm version, so a projection change that
    # retro-changes derived facet state from unchanged evidence surfaces as one
    # deliberate recalibration boundary rather than silently.
    from learnloop.substrate.canonical_projection import CANONICAL_PROJECTION_VERSION

    # Measurement §5.2: the coverage denominator is a third, independent
    # recalibration boundary — it moves DISPLAYED mastery (through the variance
    # floor) without touching the evidence or the projection. The version is
    # content-addressed on the effective frontier, so an ordinary rebuild that
    # changes no cells re-stamps the same value and emits no entry.
    from learnloop.learner.facet_diagnostics import coverage_denominator_version

    marker_id = None
    if record_receipt:
        marker_id = repository.record_derived_state_rebuild(
            scope=scope,
            learning_object_ids=rebuilt,
            algorithm_version=vault.config.algorithms.algorithm_version,
            rebuilt_learning_objects=len(rebuilt),
            replayed_attempts=replayed_attempts,
            canonical_projection_version=CANONICAL_PROJECTION_VERSION,
            coverage_denominator_version=coverage_denominator_version(vault, repository),
            clock=clock,
        )
    return RebuildResult(
        algorithm_version=vault.config.algorithms.algorithm_version,
        rebuilt_learning_objects=len(rebuilt),
        replayed_attempts=replayed_attempts,
        learning_object_ids=rebuilt,
        marker_id=marker_id,
    )


def record_content_recalibration(
    vault: LoadedVault,
    repository: Repository,
    *,
    affected_learning_object_ids: list[str],
    clock: Clock | None = None,
) -> str | None:
    """Stamp the recalibration boundary AT the content change, not after it.

    Applying ingested content (new LOs, changed blueprints) moves the
    vault-wide contract frontier. Without a marker at the apply, the
    coverage-denominator delta would stay armed until the next unrelated
    rebuild, which would narrate the recalibration at the wrong time and
    attribute it to a rebuild that did not cause it (an LO-scoped rebuild
    would fold the whole vault-wide drift into its own marker).

    Discipline is `integration_backfill`'s: apply → reload → rebuild the
    affected LOs → exactly one marker. The caller passes the RELOADED vault.
    Affected LOs with persisted attempts are genuinely replayed (an append can
    change the blueprint of a practised LO); brand-new LOs have nothing to
    replay, and for them this records a zero-replay marker so the
    content-addressed coverage version is stamped now. Idempotence survives:
    an apply that changes no frontier cells re-stamps the same version and
    `derived_state_rebuild_version_changes` emits nothing.
    """

    affected = sorted(set(affected_learning_object_ids) & set(vault.learning_objects))
    if not affected:
        return None
    with_attempts = set(repository.learning_object_ids_with_attempts())
    replayable = [lo_id for lo_id in affected if lo_id in with_attempts]
    if replayable:
        # One write transaction: the replay clears each LO's derived rows before
        # re-folding them, and a content apply runs inside an ingest job's write
        # fence. Holding the write lock keeps a replacement worker from taking
        # the lease between the clear and the re-fold, and any failure leaves
        # the published projection untouched.
        with repository.atomic():
            return rebuild_derived_state(
                vault, repository, learning_object_ids=replayable, clock=clock
            ).marker_id
    from learnloop.substrate.canonical_projection import CANONICAL_PROJECTION_VERSION
    from learnloop.learner.facet_diagnostics import coverage_denominator_version

    return repository.record_derived_state_rebuild(
        scope="learning_object",
        learning_object_ids=affected,
        algorithm_version=vault.config.algorithms.algorithm_version,
        rebuilt_learning_objects=0,
        replayed_attempts=0,
        canonical_projection_version=CANONICAL_PROJECTION_VERSION,
        coverage_denominator_version=coverage_denominator_version(vault, repository),
        clock=clock,
    )
