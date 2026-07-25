"""P2 causal repair orchestration (spec_causal_attribution_v1 §6).

ONE orchestration service, deliberately not one RPC per low-level function.  The
P2 primitives (``causal_probe_coherence``, ``probe_targeting``,
``probe_episodes``, ``remediation``) are each individually correct and were each
individually unreachable; this module is the single path that composes them:

    open factor
      -> machine checks (must discharge first; principle 8)
      -> recorded probe decision (EVSI, every decision persisted)
      -> learner offer / defer ("Not now" persists)
      -> factor-aware episode (``enter_episode(causal_factor_id=...)``)
      -> reviewed-ACTIVE candidate with PINNED bundles
      -> classification against exactly those pinned bundles
      -> discriminating-observation receipt (resolves the factor; the ONLY
         channel through which diagnosis support may move)
      -> targeted repair
      -> cold verification (wired through the follow-up task record)

Status mapping (§6).  ``decide_probe`` publishes decision verbs; this module
maps them onto the five learner-visible repair statuses:

| probe decision              | instrument            | repair status                  |
|-----------------------------|-----------------------|--------------------------------|
| ``skip_common_repair``      | n/a                   | ``safe_common_repair_available``|
| ``skip_action_equivalent``  | n/a                   | ``started``                    |
| ``defer_machine_checks``    | n/a                   | ``deferred_machine_checks``    |
| ``probe_now``               | reviewed-active       | ``needs_disambiguation``       |
| ``probe_now``               | unreviewed / absent   | ``blocked_pending_review``     |
| ``probe_now``               | episode conflict‡     | ``blocked_pending_review``     |
| ``defer_learner_preference``| any                   | ``needs_disambiguation``†      |
| ``defer_recent_burden``     | any                   | ``needs_disambiguation``†      |
| ``defer_session_budget``    | any                   | ``needs_disambiguation``†      |
| ``skip_*`` (value/EIG)      | present               | ``started``                    |
| ``skip_*`` (value/EIG)      | absent                | ``blocked_pending_review``     |

† the state is unchanged — the causes still diverge — but the OFFER is
suppressed (``probe_offered = False``, and the "Take the quick check" action is
withdrawn).  That is what "Not now" means: stop asking, not stop being
ambiguous.  The escape hatch is always "Teach me now", which records an explicit
learner authorisation to be taught under ambiguity and returns ``started``.

‡ at most ONE probe episode may be open per Learning Object.  When another
diagnostic episode owns it AND has already recorded observations under its own
locked hypothesis set, the causal probe cannot be served: relocking that episode
would reinterpret its observations under a set that did not exist when they were
made.  The offer is therefore withheld (``probe_offered = False``) rather than
shown and then refused — ``causal_repair_status`` and ``accept_probe_offer``
consult the SAME predicate, :func:`episode_conflict_reason`.  An open episode
that has measured nothing carries nothing to reinterpret and is relocked onto
the cause set instead (``probe_episodes.retarget_episode_to_causal_factor``);
without that, vault state sync's ``initial`` placement episode — which it opens
for every active LO — made the whole journey unreachable in the running app.

A divergent cause set with NO discriminating instrument at all is
``blocked_pending_review``, not ``started``.  Serving one branch of a
genuinely divergent repair is precisely the over-teaching §7 exists to price;
the honest answer is that the branch-specific repair is not yet servable, and
the learner may override it explicitly.

EVSI INPUTS — standing constraint 4 (`spec_diagnostic_augmentation_v1.md` §1:
"deterministic quantities outrank model-reported ones wherever both exist").
``decide_probe`` takes ``expected_information_gain`` and
``probability_information_changes_repair`` as caller-supplied floats, and this
module is the caller.  Neither is ever asked of a model:

* ``expected_information_gain`` is the share of hypothesis pairs the pinned
  instrument PROVABLY separates, read off the candidate's recorded
  ``blind_bundle_discrimination`` — ``rows_are_separable`` under the real
  matcher.  A cause set whose bundles are inseparable has zero discriminating
  information; that is computed, not estimated.
* ``probability_information_changes_repair`` is the share of those separable
  pairs that land in DIFFERENT repair classes, read off the repair-class map of
  the cause set itself.

The one genuinely model-sourced quantity is ``avoided_overteaching_minutes``,
whose per-class ``expected_minutes`` originate in authored repair suggestions.
It is tagged ``model_reported`` on the receipt, and it cannot overrule a
computed quantity: it enters only as a MULTIPLICAND of the two deterministic
factors above, so a provably inseparable instrument stays worthless no matter
how large the claimed teaching cost.  Every EVSI input carries its provenance
(``deterministic`` | ``model_reported`` | ``heuristic_default``) in the decision
receipt — P4 consumes these as training records, and a record that cannot say
where its numbers came from is not a training record.

MACHINE CHECKS — scope statement (§6, §10b).  This module owns the *queue*:
``sweep_machine_checks`` turns ``probe_targeting.repair_mapping_backfills``'
typed obligations (and the ``insufficient_mapping`` state that
``causal_probe_coherence.rung_divergence_gate`` publishes) into pending
``causal_machine_checks`` rows, the orchestrator CONSUMES them as
``decide_probe(pending_machine_checks=...)``, and every sweep auto-closes
checks whose obligation has gone away.  It does NOT own the *writer* of
``causal_hypotheses.repair_class_id``: that table is append-only (migration
118's ``causal_hypotheses_no_update`` trigger) and appending a new version mints
a new id, which would sever the ``unresolved_cause_factors.candidate_causes``
references that point at it.  The mapping must therefore be written where the
hypothesis is minted, in ``causal_attribution``.  This queue is what makes the
gap visible, blocking, and self-closing in the meantime — it is not a
substitute for the mint-time writer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import ProbeEpisodeRecord, Repository
from learnloop.services.causal_attribution import (
    CAUSAL_DECISION_POLICY_VERSION,
    SUPPORT_BASIS_AUTHORITY,
)
from learnloop.services.causal_probe_coherence import (
    ProbeDecision,
    bundle_feature_row_report,
    classify_against_blind_bundles,
    decide_probe,
    repair_class_need_for_factor,
    resolve_causal_probe_parameters,
)
from learnloop.services.probe_targeting import (
    CAUSE_SET_INCOMPLETE_MAPPING,
    MAPPING_BASIS_LEGACY_FACET,
    classify_cause_set,
)
from learnloop.vault.models import LoadedVault

CAUSAL_ORCHESTRATOR_FORMULA_VERSION = "causal_orchestrator_v1"

#: Fitted-parameter scope for the orchestrator's own EVSI inputs.  The
#: ``decide_probe`` thresholds live in ``causal_probe_policy``; the *inputs* fed
#: to it (burdens and expected teaching costs) are a separate policy surface.
CAUSAL_ORCHESTRATOR_POLICY_SCOPE = "causal_orchestrator_policy"

REPAIR_STATUSES = (
    "started",
    "needs_disambiguation",
    "deferred_machine_checks",
    "safe_common_repair_available",
    "blocked_pending_review",
)

LEARNER_PREFERENCES = ("allow", "decline", "teach_now", "no_more_diagnostics")

#: Standing constraint 4: where an EVSI input came from.  ``deterministic`` is a
#: computed fact (blind-bundle separability, a stored learner action, a counted
#: attempt); ``model_reported`` came from authored/model prose; and
#: ``heuristic_default`` is a pinned fallback used because neither existed.
EVSI_PROVENANCE = ("deterministic", "model_reported", "heuristic_default")

MACHINE_CHECK_REPAIR_MAPPING = "repair_class_mapping_backfill"

#: The §7 evidence basis a blind-bundle classification carries.  It is a key of
#: `causal_attribution.SUPPORT_BASIS_AUTHORITY`, which is also what
#: `record_delayed_cold_verification` validates a caller-supplied basis against —
#: so an observation recorded here is citable there by id.
BLIND_PROBE_BASIS = "blind_probe_match"

#: Where an observed feature vector came from.  `unknown` exists on purpose:
#: a sensor that cannot say what it is must fail closed rather than inherit the
#: deterministic grant (standing constraint 2 — every enum keeps its abstention
#: arm).
OBSERVATION_FEATURE_SOURCES = (
    "deterministic",
    "model_extracted",
    "learner_declared",
    "unknown",
)
#: ...and the ONE source that earns `validator_owned` support authority.
VALIDATOR_OWNED_FEATURE_SOURCES = frozenset({"deterministic"})

#: Classification outcomes that carry discriminating information at all.  The
#: other four (`matched_multiple`, `all_bundles_matched`, `cohort_mismatch`,
#: `unparsed_features`) are recorded and resolve nothing.
DISCRIMINATING_OUTCOMES = frozenset({"matched_single", "no_bundle_matched"})

#: Deterministic probe-feature vocabulary (see `deterministic_probe_features`).
DETERMINISTIC_FEATURE_PREFIX = "criterion:"

#: §6 learner copy.  The previous message ("unrelated remediation") was
#: semantically wrong: what is held is the BRANCH-SPECIFIC repair inside the
#: divergent factor, not unrelated repair elsewhere.
NEEDS_DISAMBIGUATION_MESSAGE = (
    "I'm holding this targeted repair because two explanations would need "
    "different help. A quick check can distinguish them."
)
DEFERRED_OFFER_MESSAGE = (
    "I'm holding this targeted repair because two explanations would need "
    "different help. I won't ask again right now."
)
DEFERRED_MACHINE_CHECKS_MESSAGE = (
    "I'm still working out which repair this needs. Nothing for you to do — "
    "I'll finish the machine-side checks first."
)
SAFE_COMMON_REPAIR_MESSAGE = (
    "One repair covers every explanation that fits, so there is nothing to "
    "distinguish first."
)
BLOCKED_PENDING_REVIEW_MESSAGE = (
    "I'm holding this targeted repair because two explanations would need "
    "different help, and the check that would tell them apart isn't ready yet."
)
#: Refusal id shared by `accept_probe_offer` and `causal_repair_status`. The
#: Tauri panel maps it to its own copy (`PROBE_OFFER_COPY`), so it is contract.
EPISODE_CONFLICT_REASON = "another_probe_episode_is_open"
EPISODE_CONFLICT_MESSAGE = (
    "I'm holding this targeted repair because two explanations would need "
    "different help. I can't run the check while another diagnostic is open "
    "on this topic — finish that one first."
)
STARTED_MESSAGE = "Starting the targeted repair."

TAKE_QUICK_CHECK = ("take_quick_check", "Take the quick check")
TEACH_ME_NOW = ("teach_me_now", "Teach me now")
NOT_NOW = ("not_now", "Not now")


# --- fitted parameters -------------------------------------------------------


CAUSAL_ORCHESTRATOR_POLICY_DEFAULTS: dict[str, float] = {
    # Fallback probe burden when the candidate item has no instrument card.
    "probe_burden_minutes_default": 1.5,
    # Fallback teaching cost of one repair class when the diagnosis receipt did
    # not estimate `expected_minutes`.
    "repair_class_expected_minutes_default": 8.0,
    # How many recent attempts on the learning object count toward the recent
    # diagnostic burden `decide_probe` budgets against.
    "recent_diagnostic_window_attempts": 10.0,
}

_ORCHESTRATOR_POLICY_BOUNDS: dict[str, tuple[float, float]] = {
    "probe_burden_minutes_default": (0.0, 600.0),
    "repair_class_expected_minutes_default": (0.0, 600.0),
    "recent_diagnostic_window_attempts": (1.0, 1000.0),
}


@dataclass(frozen=True)
class OrchestratorParameters:
    """Resolved orchestrator knobs plus their provenance."""

    values: Mapping[str, float]
    lifecycle: str = "heuristic_default"
    fitted_set_id: str | None = None
    invalid_keys: tuple[str, ...] = ()

    def __getitem__(self, key: str) -> float:
        return float(self.values[key])

    def manifest(self) -> dict[str, Any]:
        return {
            "scope": CAUSAL_ORCHESTRATOR_POLICY_SCOPE,
            "lifecycle": self.lifecycle,
            "fitted_set_id": self.fitted_set_id,
            "values": dict(self.values),
            "invalid_keys": list(self.invalid_keys),
        }


def resolve_orchestrator_parameters(
    repository: Repository | None,
) -> OrchestratorParameters:
    values = dict(CAUSAL_ORCHESTRATOR_POLICY_DEFAULTS)
    if repository is None:
        return OrchestratorParameters(values=values)
    record = repository.active_fitted_parameters(
        CAUSAL_ORCHESTRATOR_POLICY_SCOPE
    )
    if record is None:
        return OrchestratorParameters(values=values)
    params = record.get("params") or {}
    invalid: list[str] = []
    for key in CAUSAL_ORCHESTRATOR_POLICY_DEFAULTS:
        if key not in params:
            continue
        low, high = _ORCHESTRATOR_POLICY_BOUNDS[key]
        raw = params[key]
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            invalid.append(key)
            continue
        candidate = float(raw)
        if not math.isfinite(candidate) or not (low <= candidate <= high):
            invalid.append(key)
            continue
        values[key] = candidate
    return OrchestratorParameters(
        values=values,
        lifecycle="fitted",
        fitted_set_id=str(record["id"]),
        invalid_keys=tuple(sorted(invalid)),
    )


def _content_id(prefix: str, value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(encoded).hexdigest()[:26]}"


# --- typed result ------------------------------------------------------------


@dataclass(frozen=True)
class RepairAction:
    id: str
    label: str

    def as_dict(self) -> dict[str, str]:
        return {"id": self.id, "label": self.label}


@dataclass(frozen=True)
class RepairStatus:
    """The typed union returned by :func:`causal_repair_status` (§6)."""

    status: str
    reason: str
    message: str
    misconception_id: str
    factor_id: str | None = None
    learning_object_id: str | None = None
    attempt_id: str | None = None
    probe_offered: bool = False
    probe_decision: str | None = None
    probe_decision_reason: str | None = None
    decision_receipt_id: str | None = None
    candidate_id: str | None = None
    blind_bundle_ids: tuple[str, ...] = ()
    hypothesis_set_id: str | None = None
    repair_class_ids: tuple[str, ...] = ()
    common_repair_class_id: str | None = None
    pending_machine_check_ids: tuple[str, ...] = ()
    learner_preference: str = "allow"
    actions: tuple[RepairAction, ...] = ()
    episode: dict[str, Any] | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    #: Standing constraint 4: per-EVSI-input provenance, mirrored from the
    #: decision receipt so a caller can see it without re-reading the ledger.
    evsi_provenance: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        assert self.status in REPAIR_STATUSES, self.status

    @property
    def repair_permitted(self) -> bool:
        """True when the causal state allows the targeted repair to run.

        Distinct from ``episode is not None``: a caller may ask with
        ``start_repair=False`` (a pure status read) and get a permitted repair
        with no episode minted.
        """

        return self.status in {"started", "safe_common_repair_available"}

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "message": self.message,
            "misconception_id": self.misconception_id,
            "factor_id": self.factor_id,
            "learning_object_id": self.learning_object_id,
            "attempt_id": self.attempt_id,
            "probe_offered": self.probe_offered,
            "probe_decision": self.probe_decision,
            "probe_decision_reason": self.probe_decision_reason,
            "decision_receipt_id": self.decision_receipt_id,
            "candidate_id": self.candidate_id,
            "blind_bundle_ids": list(self.blind_bundle_ids),
            "hypothesis_set_id": self.hypothesis_set_id,
            "repair_class_ids": list(self.repair_class_ids),
            "common_repair_class_id": self.common_repair_class_id,
            "pending_machine_check_ids": list(self.pending_machine_check_ids),
            "learner_preference": self.learner_preference,
            "actions": [action.as_dict() for action in self.actions],
            "episode": self.episode,
            "parameters": self.parameters,
            "evsi_provenance": dict(self.evsi_provenance),
            "decision_policy_version": CAUSAL_DECISION_POLICY_VERSION,
            "formula_version": CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
        }


# --- machine-check queue (§6, the `deferred_machine_checks` producer) --------


def _machine_check_id(obligation: Mapping[str, Any]) -> str:
    return _content_id(
        "cmc",
        {
            "kind": obligation.get("kind"),
            "factor_id": obligation.get("factor_id"),
            "attempt_id": obligation.get("attempt_id"),
            "hypothesis_ids": sorted(
                str(value) for value in obligation.get("hypothesis_ids") or []
            ),
        },
    )


def backfill_obligation(targeting: Any) -> dict[str, Any]:
    """The typed backfill obligation for one classified cause set.

    Byte-identical in shape to what ``probe_targeting.repair_mapping_backfills``
    emits, but derivable from a single already-classified factor — the
    learning-object sweep walks the whole observation ledger, which is too
    expensive to run on a per-repair question.
    """

    unmapped = set(targeting.unmapped_hypothesis_ids)
    # Migration 125 gives each gap a typed reason ("author a repair for this
    # episode" and "re-target the authored repair" are different remedies), so
    # carry it: a queue entry that cannot be routed is not a queue.
    unresolved_reasons = {
        str(cause["hypothesis_id"]): str(
            cause.get("repair_class_unresolved_reason") or "unrecorded"
        )
        for cause in targeting.causes
        if isinstance(cause, Mapping)
        and str(cause.get("hypothesis_id") or "") in unmapped
    }
    return {
        "kind": MACHINE_CHECK_REPAIR_MAPPING,
        "state": targeting.state,
        "coherence_gate_state": targeting.coherence_gate_state,
        "factor_id": targeting.factor_id,
        "attempt_id": targeting.attempt_id,
        "hypothesis_ids": list(targeting.unmapped_hypothesis_ids),
        "unresolved_reasons": unresolved_reasons,
        "repair_class_ids": list(targeting.repair_class_ids),
        "reason": targeting.reason,
        "learner_actionable": False,
    }


def enqueue_backfill_obligation(
    repository: Repository,
    obligation: Mapping[str, Any],
    *,
    learning_object_id: str | None,
    source: str = "causal_orchestrator",
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Queue one typed obligation; idempotent on its content hash."""

    return repository.enqueue_causal_machine_check(
        check_id=_machine_check_id(obligation),
        kind=str(obligation.get("kind") or MACHINE_CHECK_REPAIR_MAPPING),
        payload=dict(obligation),
        source=source,
        learning_object_id=learning_object_id,
        factor_id=(
            str(obligation["factor_id"]) if obligation.get("factor_id") else None
        ),
        attempt_id=(
            str(obligation["attempt_id"]) if obligation.get("attempt_id") else None
        ),
        clock=clock,
    )


def sweep_machine_checks(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    source: str = "causal_orchestrator",
    clock: Clock | None = None,
) -> list[dict[str, Any]]:
    """Turn backfill obligations into queued machine checks, idempotently.

    This is the producer the ``deferred_machine_checks`` arm was missing.  It
    also closes the loop: a pending check whose obligation is no longer emitted
    (the mapping was filled at mint time, or the factor closed) is auto-resolved
    on the next sweep, so the arm cannot become a permanent block.

    Cost matters — this runs on the post-attempt path.  It classifies the open
    factors this learning object already indexes rather than calling
    ``probe_targeting.repair_mapping_backfills``, which reaches the same
    obligations by walking the whole canonical observation ledger.  Same typed
    shape, O(open factors) instead of O(all attempts).  ``vault`` is therefore
    unused; it stays in the signature because every other P2 service entrypoint
    takes it and callers already hold one.

    Returns the pending checks for this learning object after the sweep.
    """

    live: set[str] = set()
    memo: dict[str, str | None] = {}
    for factor in repository.open_unresolved_cause_factors(
        learning_object_id=learning_object_id
    ):
        causes = list(factor.get("candidate_causes") or [])
        if not any(
            isinstance(cause, Mapping)
            and (cause.get("open_set") is True or cause.get("hypothesis_id") == "H_OTHER")
            for cause in causes
        ):
            # A P0-era authored set without the explicit open-world arm is not a
            # probe target at all, so it owes no probe-blocking mapping
            # (mirrors `probe_targeting.open_cause_set_states_for_learning_object`).
            continue
        targeting = classify_cause_set(
            causes,
            repository=repository,
            factor_id=str(factor["id"]),
            attempt_id=str(factor.get("attempt_id") or "") or None,
            memo=memo,
        )
        if not targeting.needs_machine_backfill:
            continue
        obligation = backfill_obligation(targeting)
        live.add(_machine_check_id(obligation))
        enqueue_backfill_obligation(
            repository,
            obligation,
            learning_object_id=learning_object_id,
            source=source,
            clock=clock,
        )
    return _close_orphan_checks(repository, learning_object_id, live, clock=clock)


def _close_orphan_checks(
    repository: Repository,
    learning_object_id: str,
    live: set[str],
    *,
    clock: Clock | None = None,
) -> list[dict[str, Any]]:
    for check in repository.causal_machine_checks(
        status="pending", learning_object_id=learning_object_id
    ):
        if str(check["kind"]) != MACHINE_CHECK_REPAIR_MAPPING:
            continue
        if str(check["id"]) in live:
            continue
        repository.close_causal_machine_check(
            str(check["id"]),
            status="resolved",
            resolution={
                "basis": "obligation_no_longer_present",
                "formula_version": CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
            },
            clock=clock,
        )
    return repository.causal_machine_checks(
        status="pending", learning_object_id=learning_object_id
    )


def close_satisfied_backfills(
    repository: Repository, factor_id: str, *, clock: Clock | None = None
) -> int:
    """Close this factor's repair-mapping checks once it owes nothing.

    Called at the point of CONSUMPTION, not only from the learning-object
    sweep: once the mint path fills the missing ``repair_class_id`` the factor
    becomes divergent, and a stale pending check would wedge the offer behind
    ``deferred_machine_checks`` forever.
    """

    closed = 0
    for check in repository.causal_machine_checks(
        status="pending", factor_id=factor_id
    ):
        if str(check["kind"]) != MACHINE_CHECK_REPAIR_MAPPING:
            continue
        repository.close_causal_machine_check(
            str(check["id"]),
            status="resolved",
            resolution={
                "basis": "repair_mapping_resolved",
                "formula_version": CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
            },
            clock=clock,
        )
        closed += 1
    return closed


def resolve_machine_check(
    repository: Repository,
    check_id: str,
    *,
    resolution: Mapping[str, Any],
    status: str = "resolved",
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Explicit discharge for a regrade / verifier / authoring agent."""

    return repository.close_causal_machine_check(
        check_id, status=status, resolution=dict(resolution), clock=clock
    )


def pending_machine_checks_for_factor(
    repository: Repository,
    *,
    factor_id: str,
    learning_object_id: str | None = None,
) -> list[dict[str, Any]]:
    """Checks that must discharge before this factor may buy learner effort.

    Factor-scoped checks plus learning-object-wide checks that name no factor.
    """

    checks = repository.causal_machine_checks(
        status="pending", factor_id=factor_id
    )
    seen = {str(check["id"]) for check in checks}
    if learning_object_id is not None:
        for check in repository.causal_machine_checks(
            status="pending", learning_object_id=learning_object_id
        ):
            if check.get("factor_id") or str(check["id"]) in seen:
                continue
            checks.append(check)
    return checks


# --- learner preference ("Not now" must persist) ----------------------------


def record_learner_preference(
    repository: Repository,
    *,
    preference: str,
    factor_id: str | None = None,
    learning_object_id: str | None = None,
    session_id: str | None = None,
    source: str = "learner_action",
    expires_at: str | None = None,
    detail: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    if preference not in LEARNER_PREFERENCES:
        raise ValueError(f"unknown learner probe preference {preference!r}")
    if factor_id is not None:
        scope, scope_ref = "factor", factor_id
    elif session_id is not None:
        scope, scope_ref = "session", session_id
    elif learning_object_id is not None:
        scope, scope_ref = "learning_object", learning_object_id
    else:
        raise ValueError(
            "a probe preference must be scoped to a factor, session, or "
            "learning object"
        )
    return repository.record_causal_probe_preference(
        scope=scope,
        scope_ref=scope_ref,
        preference=preference,
        source=source,
        session_id=session_id,
        expires_at=expires_at,
        detail=dict(detail) if detail is not None else None,
        clock=clock,
    )


def learner_preference(
    repository: Repository,
    *,
    factor_id: str | None = None,
    learning_object_id: str | None = None,
    session_id: str | None = None,
) -> str:
    record = repository.causal_probe_preference(
        factor_id=factor_id,
        learning_object_id=learning_object_id,
        session_id=session_id,
    )
    if record is None:
        return "allow"
    return str(record["preference"])


# --- factor / receipt plumbing ----------------------------------------------


def open_factors_for_hypothesis(
    repository: Repository, causal_hypothesis_id: str
) -> list[dict[str, Any]]:
    """Open cause factors on this hypothesis' own learning object (§3.9)."""

    hypothesis = repository.causal_hypothesis(causal_hypothesis_id)
    if hypothesis is None:
        return []
    learning_object_id = str(hypothesis["learning_object_id"])
    factors: list[dict[str, Any]] = []
    for factor in repository.open_unresolved_cause_factors(
        learning_object_id=learning_object_id
    ):
        ids = {
            str(value.get("hypothesis_id"))
            for value in factor.get("candidate_causes") or []
            if isinstance(value, Mapping) and value.get("hypothesis_id")
        }
        if causal_hypothesis_id in ids:
            factors.append(factor)
    return factors


def _diagnosis_receipt(
    repository: Repository, attempt_id: str | None
) -> Mapping[str, Any] | None:
    if not attempt_id:
        return None
    debug = repository.attempt_debug_payload(attempt_id) or {}
    attribution = debug.get("causal_attribution")
    if not isinstance(attribution, Mapping):
        return None
    receipt = attribution.get("diagnosis_receipt")
    return receipt if isinstance(receipt, Mapping) else None


def _repair_class_by_hypothesis(
    causes: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for cause in causes:
        if not isinstance(cause, Mapping):
            continue
        hypothesis_id = cause.get("hypothesis_id")
        repair_class_id = cause.get("repair_class_id")
        if hypothesis_id and repair_class_id:
            mapping[str(hypothesis_id)] = str(repair_class_id)
    return mapping


def _avoided_overteaching_minutes(
    repository: Repository,
    *,
    attempt_id: str | None,
    repair_class_ids: Sequence[str],
    default_minutes: float,
) -> tuple[float, str]:
    """Expected teaching minutes a discriminating answer would save, + provenance.

    Teaching every plausible branch costs the sum of their expected minutes;
    knowing which one is needed costs the mean.  The difference is the avoided
    over-teaching, which is what §7 prices the probe against — not raw
    information gain.

    ``expected_minutes`` originates in an authored repair suggestion, so a value
    sourced from the diagnosis receipt is ``model_reported`` (standing
    constraint 4).  It never overrules a computed quantity: it is a multiplicand
    of the deterministic separability terms, so a provably inseparable
    instrument stays worthless however large this number is.
    """

    if len(repair_class_ids) < 2:
        return 0.0, "deterministic"
    receipt = _diagnosis_receipt(repository, attempt_id)
    by_id: dict[str, Mapping[str, Any]] = {}
    if receipt is not None:
        for entry in receipt.get("repair_classes") or []:
            if isinstance(entry, Mapping) and entry.get("id"):
                by_id[str(entry["id"])] = entry
    minutes: list[float] = []
    from_receipt = False
    from_default = False
    for repair_class_id in repair_class_ids:
        entry = by_id.get(str(repair_class_id))
        raw = entry.get("expected_minutes") if entry is not None else None
        if isinstance(raw, (int, float)) and not isinstance(raw, bool) and raw > 0:
            minutes.append(float(raw))
            from_receipt = True
        else:
            minutes.append(default_minutes)
            from_default = True
    total = sum(minutes)
    if from_receipt:
        provenance = "model_reported"
    else:
        provenance = "heuristic_default" if from_default else "deterministic"
    return max(0.0, total - total / len(minutes)), provenance


def _probe_burden_minutes(
    repository: Repository, practice_item_id: str | None, default_minutes: float
) -> tuple[float, str]:
    """Probe burden from the instrument card's own expected seconds, + provenance."""

    if not practice_item_id:
        return default_minutes, "heuristic_default"
    for link in repository.probe_item_family_links(practice_item_id):
        card = repository.probe_instrument_card(
            link.instrument_card_id, link.instrument_card_version
        )
        if card is None:
            continue
        seconds = (card.card or {}).get("expected_seconds")
        if isinstance(seconds, (int, float)) and not isinstance(seconds, bool):
            if seconds > 0:
                return float(seconds) / 60.0, "deterministic"
    return default_minutes, "heuristic_default"


def _recent_diagnostic_burden(
    repository: Repository, learning_object_id: str, window: int
) -> int:
    attempts = repository.list_recent_attempts_by_learning_object(
        learning_object_id, limit=max(1, window)
    )
    return sum(
        1
        for attempt in attempts
        if str(attempt.get("attempt_type") or "") == "diagnostic_probe"
    )


@dataclass(frozen=True)
class DiscriminationInputs:
    """The two EVSI terms plus where each came from (standing constraint 4)."""

    expected_information_gain: float
    probability_information_changes_repair: float
    gain_provenance: str
    action_change_provenance: str
    separable_pairs: int = 0
    inseparable_pairs: int = 0


def _discrimination_inputs(
    candidate: Mapping[str, Any] | None,
    repair_class_by_hypothesis: Mapping[str, str],
) -> DiscriminationInputs:
    """``(expected_information_gain, p(information changes the repair))``.

    Both are COMPUTED, never model-reported (standing constraint 4):

    * the gain is the share of hypothesis pairs the candidate's recorded
      ``blind_bundle_discrimination`` provably separates under the real matcher
      (``rows_are_separable`` over declared feature rows);
    * the action-change probability is the share of those separable pairs whose
      hypotheses land in different repair classes — separating two causes that
      would be repaired identically changes nothing.

    With no instrument, or no parsable pair, the value is the pinned 0.0
    fallback and is tagged ``heuristic_default`` rather than being passed off as
    a computed zero.
    """

    empty = DiscriminationInputs(0.0, 0.0, "heuristic_default", "heuristic_default")
    if candidate is None:
        return empty
    discrimination = candidate.get("discrimination")
    if not isinstance(discrimination, Mapping):
        return empty
    separable = [
        [str(value) for value in pair]
        for pair in discrimination.get("separable_pairs") or []
        if isinstance(pair, (list, tuple)) and len(pair) == 2
    ]
    inseparable = [
        pair
        for pair in discrimination.get("inseparable_pairs") or []
        if isinstance(pair, (list, tuple)) and len(pair) == 2
    ]
    total = len(separable) + len(inseparable)
    if total == 0:
        return empty
    expected_information_gain = len(separable) / total
    if not separable:
        # Provably inseparable: zero discriminating information is a computed
        # fact, and no model-reported teaching cost can overrule it.
        return DiscriminationInputs(
            expected_information_gain,
            0.0,
            "deterministic",
            "deterministic",
            separable_pairs=0,
            inseparable_pairs=len(inseparable),
        )
    action_changing = sum(
        1
        for left, right in separable
        if repair_class_by_hypothesis.get(left)
        and repair_class_by_hypothesis.get(right)
        and repair_class_by_hypothesis[left] != repair_class_by_hypothesis[right]
    )
    return DiscriminationInputs(
        expected_information_gain,
        action_changing / len(separable),
        "deterministic",
        "deterministic",
        separable_pairs=len(separable),
        inseparable_pairs=len(inseparable),
    )


# --- the orchestrator --------------------------------------------------------


class CausalRepairError(ValueError):
    """The repair case itself is unusable (no such misconception / candidate)."""


#: Repair-episode states that have not yet committed to a specific item pair.
#: An episode in one of these is still the SAME repair and is reused; from
#: `treatment` on, the episode owns a primed/cold item pair and a fresh request
#: is a genuinely new repair.
_UNCOMMITTED_REPAIR_STATES = ("diagnosis", "prescribed")


def _open_repair_episode_id(
    repository: Repository, *, case_kind: str, case_ref: str
) -> str | None:
    placeholders = ",".join("?" for _ in _UNCOMMITTED_REPAIR_STATES)
    with repository.connection() as connection:
        row = connection.execute(
            f"""
            SELECT id FROM remediation_episodes
             WHERE case_kind = ? AND case_ref = ?
               AND state IN ({placeholders})
             ORDER BY created_at DESC, id DESC
             LIMIT 1
            """,
            (case_kind, case_ref, *_UNCOMMITTED_REPAIR_STATES),
        ).fetchone()
    return str(row["id"]) if row is not None else None


def _episode_for(
    repository: Repository,
    *,
    case_kind: str,
    case_ref: str,
    clock: Clock | None,
) -> dict[str, Any]:
    """The repair episode for this case — reused, not re-minted.

    ``causal_repair_status`` is called once per learner action ("Teach me now"
    on the feedback screen), and again by ``start_remediation`` when the repair
    surface it hands off to mounts. ``create_remediation_episode`` always
    INSERTs, so that one handoff minted two episodes for one repair: the second
    orphaned the first, and every downstream record (prescription, treatment,
    cold-retry follow-up) hung off whichever id the caller happened to keep.
    This is the only caller of ``create_remediation_episode`` in the tree, so
    de-duplicating here de-duplicates the lane.
    """

    existing = _open_repair_episode_id(
        repository, case_kind=case_kind, case_ref=case_ref
    )
    if existing is not None:
        episode = repository.remediation_episode(existing)
        if episode is not None:
            return episode
    return repository.create_remediation_episode(
        case_kind=case_kind, case_ref=case_ref, clock=clock
    )


def _actions(status: str, *, offered: bool) -> tuple[RepairAction, ...]:
    if status in {"started", "safe_common_repair_available"}:
        return ()
    if status == "deferred_machine_checks":
        return ()
    if offered:
        return (
            RepairAction(*TAKE_QUICK_CHECK),
            RepairAction(*TEACH_ME_NOW),
            RepairAction(*NOT_NOW),
        )
    return (RepairAction(*TEACH_ME_NOW),)


def causal_repair_status(
    vault: LoadedVault | None,
    repository: Repository,
    *,
    misconception_id: str,
    session_id: str | None = None,
    session_budget_minutes: float | None = None,
    start_repair: bool = True,
    clock: Clock | None = None,
) -> RepairStatus:
    """Resolve — and where safe, START — the repair for one cause.

    This is the single P2 entrypoint.  With ``start_repair`` (the default) it is
    not a pure predicate: when the causal state permits a repair it creates the
    remediation episode, because "may I repair this?" and "start repairing this"
    are the same learner action, and splitting them into two RPCs is how the
    previous surface ended up with an unreachable decision path.
    ``RepairStatus.episode`` is populated exactly when a repair was started.

    Pass ``start_repair=False`` for a read (a status panel, a poll): the
    decision and its receipt are still recorded — the negative decisions are the
    P4 training records — but no episode is minted.  Read
    ``RepairStatus.repair_permitted`` rather than ``episode is not None`` then.

    ``vault`` is accepted for interface symmetry with the rest of the P2
    services and is not required: every decision here is derived from the
    factor, its hypotheses, and the diagnosis receipt.  The learning-object-wide
    obligation sweep, which does need the vault, runs on the live attempt path
    (``followups.evaluate_attempt_intervention_followup``).
    """

    misconception = repository.misconception(misconception_id)
    if misconception is not None and misconception.status in {
        "active",
        "resolving",
    }:
        # A durable, already-adjudicated misconception is not a causal
        # ambiguity: there is nothing left to disambiguate.
        episode = (
            _episode_for(
                repository,
                case_kind="misconception",
                case_ref=misconception_id,
                clock=clock,
            )
            if start_repair
            else None
        )
        return RepairStatus(
            status="started",
            reason="durable_misconception",
            message=STARTED_MESSAGE,
            misconception_id=misconception_id,
            episode=episode,
        )

    candidate_case = repository.misconception_candidate_by_id(misconception_id)
    if candidate_case is None or candidate_case.get("status") != "candidate":
        raise CausalRepairError(
            "repair requires an active durable misconception or provisional belief"
        )

    factors = open_factors_for_hypothesis(repository, misconception_id)
    if not factors:
        episode = (
            _episode_for(
                repository,
                case_kind="diagnosis",
                case_ref=misconception_id,
                clock=clock,
            )
            if start_repair
            else None
        )
        return RepairStatus(
            status="started",
            reason="no_open_causal_factor",
            message=STARTED_MESSAGE,
            misconception_id=misconception_id,
            episode=episode,
        )

    factor = factors[0]
    return _status_for_factor(
        repository,
        misconception_id=misconception_id,
        factor=factor,
        session_id=session_id,
        session_budget_minutes=session_budget_minutes,
        start_repair=start_repair,
        clock=clock,
    )


def _status_for_factor(
    repository: Repository,
    *,
    misconception_id: str,
    factor: Mapping[str, Any],
    session_id: str | None,
    session_budget_minutes: float | None,
    start_repair: bool,
    clock: Clock | None,
) -> RepairStatus:
    factor_id = str(factor["id"])
    attempt_id = str(factor.get("attempt_id") or "") or None
    hypothesis = repository.causal_hypothesis(misconception_id)
    learning_object_id = (
        str(hypothesis["learning_object_id"]) if hypothesis is not None else None
    )
    parameters = resolve_orchestrator_parameters(repository)
    probe_parameters = resolve_causal_probe_parameters(repository)

    targeting = classify_cause_set(
        list(factor.get("candidate_causes") or []),
        repository=repository,
        factor_id=factor_id,
        attempt_id=attempt_id,
    )
    repair_class_by_hypothesis = _repair_class_by_hypothesis(targeting.causes)
    hypothesis_ids = sorted(repair_class_by_hypothesis) or sorted(
        str(value.get("hypothesis_id"))
        for value in targeting.causes
        if isinstance(value, Mapping) and value.get("hypothesis_id")
    )

    def finish(
        *,
        status: str,
        reason: str,
        message: str,
        decision: str,
        decision_reason: str,
        inputs: Mapping[str, Any],
        offered: bool = False,
        candidate: Mapping[str, Any] | None = None,
        machine_check_ids: Sequence[str] = (),
        common_repair_class_id: str | None = None,
        preference: str = "allow",
        start_episode: bool = False,
    ) -> RepairStatus:
        receipt = repository.insert_causal_probe_decision_receipt(
            factor_id=factor_id,
            decision=decision,
            reason=decision_reason,
            repair_status=status,
            decision_policy_version=CAUSAL_DECISION_POLICY_VERSION,
            formula_version=CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
            inputs=dict(inputs),
            parameters={
                "orchestrator": parameters.manifest(),
                "probe_policy": probe_parameters.manifest(),
            },
            hypothesis_ids=hypothesis_ids,
            repair_class_ids=list(targeting.repair_class_ids),
            blind_bundle_ids=list(candidate.get("blind_bundle_ids") or [])
            if candidate is not None
            else [],
            machine_check_ids=list(machine_check_ids),
            learning_object_id=learning_object_id,
            attempt_id=attempt_id,
            misconception_id=misconception_id,
            candidate_id=str(candidate["id"]) if candidate is not None else None,
            clock=clock,
        )
        episode = (
            _episode_for(
                repository,
                case_kind="diagnosis",
                case_ref=misconception_id,
                clock=clock,
            )
            if start_episode and start_repair
            else None
        )
        return RepairStatus(
            status=status,
            reason=reason,
            message=message,
            misconception_id=misconception_id,
            factor_id=factor_id,
            learning_object_id=learning_object_id,
            attempt_id=attempt_id,
            probe_offered=offered,
            probe_decision=decision,
            probe_decision_reason=decision_reason,
            decision_receipt_id=str(receipt["id"]),
            candidate_id=str(candidate["id"]) if candidate is not None else None,
            blind_bundle_ids=tuple(
                str(value) for value in (candidate or {}).get("blind_bundle_ids") or []
            ),
            hypothesis_set_id=(
                str(candidate["hypothesis_set_id"]) if candidate is not None else None
            ),
            repair_class_ids=targeting.repair_class_ids,
            common_repair_class_id=common_repair_class_id,
            pending_machine_check_ids=tuple(str(v) for v in machine_check_ids),
            learner_preference=preference,
            actions=_actions(status, offered=offered),
            episode=episode,
            parameters={
                "orchestrator": parameters.manifest(),
                "probe_policy": probe_parameters.manifest(),
            },
            evsi_provenance=dict(inputs.get("evsi_provenance") or {}),
        )

    base_inputs: dict[str, Any] = {
        "cause_set_state": targeting.state,
        "cause_set_basis": targeting.basis,
        "coherence_gate_state": targeting.coherence_gate_state,
        "repair_class_ids": list(targeting.repair_class_ids),
        "unmapped_hypothesis_ids": list(targeting.unmapped_hypothesis_ids),
    }

    # A pre-P1 legacy cause set has no repair-class vocabulary at all.  Facet
    # divergence is the vocabulary under indictment (§0 root cause 8) and must
    # never block or buy a P2 probe; record the decision and let the repair run.
    if targeting.basis == MAPPING_BASIS_LEGACY_FACET:
        return finish(
            status="started",
            reason="legacy_pre_p1_cause_set",
            message=STARTED_MESSAGE,
            decision="skip_action_equivalent",
            decision_reason=(
                "pre-P1 cause set has no repair-class mapping; facet divergence "
                "is not an action-relative divergence"
            ),
            inputs=base_inputs,
            start_episode=True,
        )

    # §6/principle 8: missing machine-side data is bought with machine effort.
    # This is the producer: the typed obligation `probe_targeting` publishes
    # becomes a queued check the orchestrator itself then consumes.
    if targeting.state == CAUSE_SET_INCOMPLETE_MAPPING:
        enqueue_backfill_obligation(
            repository,
            backfill_obligation(targeting),
            learning_object_id=learning_object_id,
            source="causal_repair_status",
            clock=clock,
        )
        pending = pending_machine_checks_for_factor(
            repository,
            factor_id=factor_id,
            learning_object_id=learning_object_id,
        )
        check_ids = [str(check["id"]) for check in pending]
        return finish(
            status="deferred_machine_checks",
            reason="incomplete_repair_mapping",
            message=DEFERRED_MACHINE_CHECKS_MESSAGE,
            decision="defer_machine_checks",
            decision_reason=targeting.reason
            or "at least one hypothesis has no resolvable repair class",
            inputs={**base_inputs, "pending_machine_checks": check_ids},
            machine_check_ids=check_ids,
        )

    # The factor's own mapping is complete, so any repair-mapping check it still
    # carries has been discharged (typically by the mint path filling
    # `repair_class_id`). Close it here rather than waiting for a sweep.
    close_satisfied_backfills(repository, factor_id, clock=clock)

    need = repair_class_need_for_factor(repository, factor_id)
    common_repair_covers = bool(need["common_repair_covers"]) or not targeting.probe_worthy
    receipt = _diagnosis_receipt(repository, attempt_id)
    common_repair_class_id = None
    if isinstance(receipt, Mapping):
        cover = receipt.get("common_repair_cover")
        if isinstance(cover, Mapping) and cover.get("covers_plausible_set"):
            common_repair_class_id = (
                str(cover["repair_class_id"])
                if cover.get("repair_class_id")
                else None
            )
    if common_repair_class_id is None and len(targeting.repair_class_ids) == 1:
        common_repair_class_id = targeting.repair_class_ids[0]

    pending_checks = (
        pending_machine_checks_for_factor(
            repository,
            factor_id=factor_id,
            learning_object_id=learning_object_id,
        )
        if targeting.probe_worthy
        else []
    )
    pending_check_ids = [str(check["id"]) for check in pending_checks]

    # §6: never offer an action that would fail. `accept_probe_offer` refuses
    # while another diagnostic episode owns the learning object and has already
    # measured something under its own locked set; the learner must see that
    # state, not a "Take the quick check" button that answers with a refusal.
    episode_conflict = _probe_episode_conflict(
        repository, factor_id=factor_id, learning_object_id=learning_object_id
    )

    candidates = repository.causal_probe_candidates_for_factor(factor_id)
    active = [value for value in candidates if value.get("status") == "active"]
    # Only a reviewed-ACTIVE candidate is servable; an unreviewed one still
    # tells us how much information the instrument WOULD carry, which is what
    # the decision receipt should record.
    chosen = active[0] if active else (candidates[0] if candidates else None)
    instrument_available = bool(active)

    discrimination = _discrimination_inputs(chosen, repair_class_by_hypothesis)
    expected_information_gain = discrimination.expected_information_gain
    action_change = discrimination.probability_information_changes_repair
    probe_burden, burden_provenance = _probe_burden_minutes(
        repository,
        str(chosen["practice_item_id"]) if chosen is not None else None,
        parameters["probe_burden_minutes_default"],
    )
    avoided, avoided_provenance = _avoided_overteaching_minutes(
        repository,
        attempt_id=attempt_id,
        repair_class_ids=targeting.repair_class_ids,
        default_minutes=parameters["repair_class_expected_minutes_default"],
    )
    preference = learner_preference(
        repository,
        factor_id=factor_id,
        learning_object_id=learning_object_id,
        session_id=session_id,
    )
    recent_burden = (
        _recent_diagnostic_burden(
            repository,
            learning_object_id,
            int(parameters["recent_diagnostic_window_attempts"]),
        )
        if learning_object_id
        else 0
    )

    decision: ProbeDecision = decide_probe(
        repair_class_ids=list(targeting.repair_class_ids),
        common_repair_covers=common_repair_covers,
        expected_information_gain=expected_information_gain,
        probability_information_changes_repair=action_change,
        probe_burden_minutes=probe_burden,
        avoided_overteaching_minutes=avoided,
        pending_machine_checks=pending_check_ids,
        session_budget_minutes=session_budget_minutes,
        learner_preference=preference,
        recent_diagnostic_burden=recent_burden,
        repository=repository,
        parameters=probe_parameters,
    )

    # Standing constraint 4: say where every EVSI number came from. P4 reads
    # these receipts as training records and must be able to tell a computed
    # separability from an authored minute estimate from a pinned fallback.
    evsi_provenance = {
        "expected_information_gain": discrimination.gain_provenance,
        "probability_information_changes_repair": (
            discrimination.action_change_provenance
        ),
        "probe_burden_minutes": burden_provenance,
        "avoided_overteaching_minutes": avoided_provenance,
        "common_repair_covers": "deterministic",
        "learner_preference": "deterministic",
        "recent_diagnostic_burden": "deterministic",
        "session_budget_minutes": (
            "deterministic" if session_budget_minutes is not None else "heuristic_default"
        ),
    }
    assert all(value in EVSI_PROVENANCE for value in evsi_provenance.values())
    inputs = {
        **base_inputs,
        "common_repair_covers": common_repair_covers,
        "expected_information_gain": expected_information_gain,
        "probability_information_changes_repair": action_change,
        "separable_pairs": discrimination.separable_pairs,
        "inseparable_pairs": discrimination.inseparable_pairs,
        "probe_burden_minutes": probe_burden,
        "avoided_overteaching_minutes": avoided,
        "expected_avoided_overteaching_minutes": (
            decision.expected_avoided_overteaching_minutes
        ),
        "pending_machine_checks": pending_check_ids,
        "session_budget_minutes": session_budget_minutes,
        "learner_preference": preference,
        "recent_diagnostic_burden": recent_burden,
        "candidate_statuses": sorted(
            str(value.get("status")) for value in candidates
        ),
        "instrument_available": instrument_available,
        "probe_episode_conflict": episode_conflict,
        "evsi_provenance": evsi_provenance,
    }

    verb = decision.decision
    if verb == "skip_common_repair":
        return finish(
            status="safe_common_repair_available",
            reason="common_repair_cover",
            message=SAFE_COMMON_REPAIR_MESSAGE,
            decision=verb,
            decision_reason=decision.reason,
            inputs=inputs,
            candidate=chosen if instrument_available else None,
            common_repair_class_id=common_repair_class_id,
            preference=preference,
            start_episode=True,
        )
    if verb == "skip_action_equivalent":
        return finish(
            status="started",
            reason="action_equivalent_causes",
            message=STARTED_MESSAGE,
            decision=verb,
            decision_reason=decision.reason,
            inputs=inputs,
            preference=preference,
            start_episode=True,
        )
    if verb == "defer_machine_checks":
        return finish(
            status="deferred_machine_checks",
            reason="pending_machine_checks",
            message=DEFERRED_MACHINE_CHECKS_MESSAGE,
            decision=verb,
            decision_reason=decision.reason,
            inputs=inputs,
            machine_check_ids=pending_check_ids,
            preference=preference,
        )
    if verb == "probe_now":
        if not instrument_available:
            return finish(
                status="blocked_pending_review",
                reason=(
                    "unreviewed_probe_candidate"
                    if candidates
                    else "no_discriminating_instrument"
                ),
                message=BLOCKED_PENDING_REVIEW_MESSAGE,
                decision=verb,
                decision_reason=decision.reason,
                inputs=inputs,
                candidate=chosen,
                preference=preference,
            )
        if episode_conflict is not None:
            return finish(
                status="blocked_pending_review",
                reason=episode_conflict,
                message=EPISODE_CONFLICT_MESSAGE,
                decision=verb,
                decision_reason=decision.reason,
                inputs=inputs,
                offered=False,
                candidate=chosen,
                preference=preference,
            )
        return finish(
            status="needs_disambiguation",
            reason="divergent_repair_classes",
            message=NEEDS_DISAMBIGUATION_MESSAGE,
            decision=verb,
            decision_reason=decision.reason,
            inputs=inputs,
            offered=True,
            candidate=chosen,
            preference=preference,
        )
    if verb in {
        "defer_learner_preference",
        "defer_recent_burden",
        "defer_session_budget",
    }:
        if preference == "teach_now":
            return finish(
                status="started",
                reason="learner_requested_teaching_without_probe",
                message=STARTED_MESSAGE,
                decision=verb,
                decision_reason=decision.reason,
                inputs=inputs,
                candidate=chosen if instrument_available else None,
                preference=preference,
                start_episode=True,
            )
        # The causes still diverge; only the OFFER is withdrawn.
        return finish(
            status="needs_disambiguation",
            reason=verb,
            message=DEFERRED_OFFER_MESSAGE,
            decision=verb,
            decision_reason=decision.reason,
            inputs=inputs,
            offered=False,
            candidate=chosen if instrument_available else None,
            preference=preference,
        )
    # skip_no_discrimination / skip_no_action_change / skip_burden_exceeds_value
    if not instrument_available:
        return finish(
            status="blocked_pending_review",
            reason=(
                "unreviewed_probe_candidate"
                if candidates
                else "no_discriminating_instrument"
            ),
            message=BLOCKED_PENDING_REVIEW_MESSAGE,
            decision=verb,
            decision_reason=decision.reason,
            inputs=inputs,
            candidate=chosen,
            preference=preference,
        )
    return finish(
        status="started",
        reason="probe_not_worth_its_burden",
        message=STARTED_MESSAGE,
        decision=verb,
        decision_reason=decision.reason,
        inputs=inputs,
        candidate=chosen,
        preference=preference,
        start_episode=True,
    )


# --- learner actions ---------------------------------------------------------


@dataclass(frozen=True)
class ProbeOffer:
    """Result of accepting the quick check."""

    accepted: bool
    reason: str
    factor_id: str
    episode_id: str | None = None
    presentation_id: str | None = None
    practice_item_id: str | None = None
    candidate_id: str | None = None
    hypothesis_set_id: str | None = None
    blind_bundle_ids: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "reason": self.reason,
            "factor_id": self.factor_id,
            "episode_id": self.episode_id,
            "presentation_id": self.presentation_id,
            "practice_item_id": self.practice_item_id,
            "candidate_id": self.candidate_id,
            "hypothesis_set_id": self.hypothesis_set_id,
            "blind_bundle_ids": list(self.blind_bundle_ids),
        }


def _causal_origin(factor_id: str) -> str:
    return f"causal_factor:{factor_id}"


def episode_conflict_reason(
    repository: Repository, episode: ProbeEpisodeRecord | None
) -> str | None:
    """Why an already-open probe episode cannot host this causal probe.

    Returns ``None`` when the episode can be relocked onto the cause set (see
    ``probe_episodes.retarget_episode_to_causal_factor``), and the typed refusal
    reason when it cannot — which is exactly when it has already interpreted
    observations under its own locked hypothesis set.

    ONE predicate, consulted by both ``causal_repair_status`` (so the offer is
    withheld rather than shown and then refused) and ``accept_probe_offer`` (so
    a stale offer still cannot force the relock).
    """

    from learnloop.services.probe_episodes import episode_has_observations

    if episode is None:
        return None
    if episode.status not in ("pending_items", "in_progress"):
        return None
    if episode_has_observations(repository, episode.id):
        return EPISODE_CONFLICT_REASON
    return None


def _probe_episode_conflict(
    repository: Repository, *, factor_id: str, learning_object_id: str | None
) -> str | None:
    """The conflict that would make ``accept_probe_offer`` refuse, if any."""

    if not learning_object_id:
        return None
    existing = repository.open_probe_episode(learning_object_id)
    if existing is None or str(existing.origin or "") == _causal_origin(factor_id):
        return None
    return episode_conflict_reason(repository, existing)


def accept_probe_offer(
    vault: LoadedVault,
    repository: Repository,
    *,
    factor_id: str,
    decision_receipt_id: str | None = None,
    session_id: str | None = None,
    clock: Clock | None = None,
    ai_client: object | None = None,
) -> ProbeOffer:
    """"Take the quick check": enter a factor-aware episode and pin the probe.

    This is the ONLY caller of ``enter_episode(causal_factor_id=...)`` — the
    parameter existed with zero callers anywhere, which is why the locked causal
    hypothesis set never reached a served instrument.

    The candidate id and its blind bundle ids are pinned into the presentation's
    ``selection_components`` (free-form JSON, so no schema change) under a
    dedicated ``causal_probe`` key.  Classification later replays against
    exactly those bundles, never a fresh query.
    """

    factor = repository.unresolved_cause_factor(factor_id)
    if factor is None or factor.get("status") != "open":
        return ProbeOffer(
            accepted=False, reason="factor_not_open", factor_id=factor_id
        )
    candidates = repository.causal_probe_candidates_for_factor(
        factor_id, statuses=("active",)
    )
    if not candidates:
        return ProbeOffer(
            accepted=False,
            reason="no_reviewed_active_candidate",
            factor_id=factor_id,
        )
    candidate = candidates[0]
    practice_item_id = str(candidate["practice_item_id"])
    item = vault.practice_items.get(practice_item_id)
    if item is None:
        return ProbeOffer(
            accepted=False,
            reason="probe_item_missing_from_vault",
            factor_id=factor_id,
            candidate_id=str(candidate["id"]),
        )
    learning_object_id = item.learning_object_id

    from learnloop.services.probe_episodes import (
        commit_presentation,
        eligible_instruments,
        enter_episode,
        retarget_episode_to_causal_factor,
    )

    origin = _causal_origin(factor_id)
    existing = repository.open_probe_episode(learning_object_id)
    if existing is not None and str(existing.origin or "") != origin:
        if episode_conflict_reason(repository, existing) is not None:
            # The open episode has already interpreted observations under its
            # own locked set.  Locking a second, causal hypothesis set over it
            # would reinterpret them.
            return ProbeOffer(
                accepted=False,
                reason=EPISODE_CONFLICT_REASON,
                factor_id=factor_id,
                episode_id=existing.id,
                candidate_id=str(candidate["id"]),
            )
        # An open episode that has measured NOTHING (the `initial` placement
        # episode vault state sync opens for every active LO is exactly this)
        # is relocked onto the cause set instead.  At most one episode may be
        # open per LO, so refusing here unconditionally made the whole journey
        # unreachable in the running app.
        episode = retarget_episode_to_causal_factor(
            vault, repository, existing, factor_id, origin=origin, clock=clock
        )
    else:
        episode = enter_episode(
            vault,
            repository,
            learning_object_id,
            # `probe_episodes.trigger` is a closed CHECK vocabulary; a cause-set
            # probe IS a belief-diagnosis trigger.  The causal provenance rides
            # on `origin`, which is free-form and is what `accept_probe_offer`
            # matches on when deciding whether an already-open episode is ours.
            trigger="misconception",
            origin=origin,
            causal_factor_id=factor_id,
            clock=clock,
            ai_client=ai_client,
        )
    if episode.status != "in_progress":
        return ProbeOffer(
            accepted=False,
            reason=f"episode_{episode.status}",
            factor_id=factor_id,
            episode_id=episode.id,
            candidate_id=str(candidate["id"]),
        )
    eligible = [
        entry
        for entry in eligible_instruments(vault, repository, episode)
        if entry.item.id == practice_item_id
    ]
    if not eligible:
        return ProbeOffer(
            accepted=False,
            reason="probe_item_not_eligible",
            factor_id=factor_id,
            episode_id=episode.id,
            candidate_id=str(candidate["id"]),
        )
    bundle_ids = tuple(str(value) for value in candidate.get("blind_bundle_ids") or [])
    # Accepting twice (a re-tapped button, a remounted panel) must not commit a
    # second presentation: the newest would win at serving time and the older
    # pin would be stranded.  An already-pinned, unconsumed probe for this same
    # candidate IS this offer.
    committed = repository.active_probe_presentation(
        episode.id, practice_item_id=practice_item_id
    )
    if committed is not None:
        already = pinned_causal_probe(repository, committed.id) or {}
        if str(already.get("causal_probe_candidate_id") or "") == str(candidate["id"]):
            return ProbeOffer(
                accepted=True,
                reason="probe_already_pinned",
                factor_id=factor_id,
                episode_id=episode.id,
                presentation_id=committed.id,
                practice_item_id=practice_item_id,
                candidate_id=str(candidate["id"]),
                hypothesis_set_id=str(candidate["hypothesis_set_id"]),
                blind_bundle_ids=tuple(
                    str(value) for value in already.get("blind_bundle_ids") or []
                ),
            )
    presentation = commit_presentation(
        vault,
        repository,
        episode,
        eligible[0],
        extra_selection_components={
            # Nested under one key: the near-clone basis reads top-level
            # `source_practice_item_id`, and adding sibling keys there would
            # change an unrelated eligibility decision.
            "causal_probe": {
                "causal_factor_id": factor_id,
                "causal_probe_candidate_id": str(candidate["id"]),
                "hypothesis_set_id": str(candidate["hypothesis_set_id"]),
                "blind_bundle_ids": list(bundle_ids),
                "decision_receipt_id": decision_receipt_id,
                "decision_policy_version": CAUSAL_DECISION_POLICY_VERSION,
                "formula_version": CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
                "session_id": session_id,
            }
        },
        clock=clock,
    )
    return ProbeOffer(
        accepted=True,
        reason="probe_pinned",
        factor_id=factor_id,
        episode_id=episode.id,
        presentation_id=presentation.id,
        practice_item_id=practice_item_id,
        candidate_id=str(candidate["id"]),
        hypothesis_set_id=str(candidate["hypothesis_set_id"]),
        blind_bundle_ids=bundle_ids,
    )


def defer_probe_offer(
    repository: Repository,
    *,
    factor_id: str,
    learning_object_id: str | None = None,
    session_id: str | None = None,
    preference: str = "decline",
    clock: Clock | None = None,
) -> dict[str, Any]:
    """"Not now": persist the decline so the next attempt does not re-offer."""

    return record_learner_preference(
        repository,
        preference=preference,
        factor_id=factor_id,
        learning_object_id=learning_object_id,
        session_id=session_id,
        source="probe_offer_declined",
        detail={"factor_id": factor_id},
        clock=clock,
    )


def request_teaching_now(
    vault: LoadedVault,
    repository: Repository,
    *,
    misconception_id: str,
    factor_id: str,
    session_id: str | None = None,
    clock: Clock | None = None,
) -> RepairStatus:
    """"Teach me now": an explicit learner authorisation to skip the check."""

    record_learner_preference(
        repository,
        preference="teach_now",
        factor_id=factor_id,
        session_id=session_id,
        source="teach_me_now",
        detail={"misconception_id": misconception_id},
        clock=clock,
    )
    return causal_repair_status(
        vault,
        repository,
        misconception_id=misconception_id,
        session_id=session_id,
        clock=clock,
    )


# --- classification against the PINNED bundles -------------------------------


def pinned_causal_probe(
    repository: Repository, presentation_id: str
) -> dict[str, Any] | None:
    presentation = repository.probe_presentation(presentation_id)
    if presentation is None:
        return None
    components = presentation.selection_components or {}
    pinned = components.get("causal_probe")
    return dict(pinned) if isinstance(pinned, Mapping) else None


def classify_probe_response(
    repository: Repository,
    *,
    presentation_id: str,
    observed_features: Mapping[str, Any],
) -> dict[str, Any]:
    """Classify an administered causal probe against its PINNED bundles.

    The bundle ids come from the presentation, which froze them when the probe
    was minted.  A fresh ``causal_blind_prediction_bundles`` query would let a
    later bundle rewrite an earlier replay, which is exactly what the append-only
    substrate exists to prevent (§3.4).

    This function is a pure read: it classifies and returns, so a caller may
    preview a verdict without committing to it.  Acting on the verdict — closing
    the factor, recording support — is :func:`record_probe_classification`, which
    writes the §7 discriminating-observation receipt.  Diagnosis support moves
    only through that receipt, never as a side effect of repair success, and its
    id is what a later ``record_delayed_cold_verification`` cites as
    ``diagnosis_support_update={"basis": "blind_probe_match", ...}``.
    """

    pinned = pinned_causal_probe(repository, presentation_id)
    if pinned is None:
        raise CausalRepairError(
            "presentation carries no pinned causal probe candidate"
        )
    presentation = repository.probe_presentation(presentation_id)
    assert presentation is not None
    result = classify_against_blind_bundles(
        repository,
        hypothesis_set_id=str(pinned["hypothesis_set_id"]),
        practice_item_id=str(presentation.practice_item_id),
        blind_bundle_ids=[str(value) for value in pinned.get("blind_bundle_ids") or []],
        observed_features=observed_features,
    )
    return {
        **result,
        "presentation_id": presentation_id,
        "causal_factor_id": pinned.get("causal_factor_id"),
        "causal_probe_candidate_id": pinned.get("causal_probe_candidate_id"),
        "formula_version": CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
    }


# --- the classification -> resolution edge (§6, §7) --------------------------


@dataclass(frozen=True)
class DiscriminatingObservation:
    """One classification, judged: what it may close and what it may not."""

    classification: dict[str, Any]
    receipt: dict[str, Any] | None
    admitted: bool
    admission_reason: str
    resolved_factor: bool
    support_authority: str | None
    support_scores: dict[str, float]

    @property
    def outcome(self) -> str:
        return str(self.classification.get("outcome") or "")

    @property
    def observation_id(self) -> str | None:
        return str(self.receipt["id"]) if self.receipt is not None else None

    def as_dict(self) -> dict[str, Any]:
        return {
            **self.classification,
            "admitted": self.admitted,
            "admission_reason": self.admission_reason,
            "resolved_factor": self.resolved_factor,
            "support_authority": self.support_authority,
            "support_scores": dict(self.support_scores),
            "observation_id": self.observation_id,
            "basis": BLIND_PROBE_BASIS,
        }


def _measured_hypotheses(
    repository: Repository,
    classification: Mapping[str, Any],
    observed_features: Mapping[str, Any],
) -> tuple[set[str], set[str]]:
    """Which of the locked set's concrete hypotheses the observation MEASURED.

    The matcher is exact over a bundle row's declared key set, so a hypothesis
    whose declared key was never observed and one whose declared key was
    observed-and-different both report ``matched: False``.  Only the second is
    evidence.  A hypothesis counts as measured when at least one of its declared
    rows had every key present in ``observed_features`` — a row is a
    conjunction, and several rows for one hypothesis are alternatives.

    Every concrete hypothesis of the locked set is considered, not just the
    evaluable ones: a rival with no pinned bundle, a version mismatch, or no
    parsable feature row was not tested either, and letting those fall outside
    the coverage question would resolve a factor on an instrument that never
    put the rival at risk.

    Returns ``(measured, unmeasured)``.
    """

    measured: set[str] = set()
    unmeasured: set[str] = set()
    evaluable = {
        str(value) for value in classification.get("evaluable_hypothesis_ids") or []
    }
    for detail in classification.get("details") or []:
        if not isinstance(detail, Mapping):
            continue
        hypothesis_id = str(detail.get("hypothesis_id") or "")
        if not hypothesis_id:
            continue
        if hypothesis_id not in evaluable:
            # No pinned bundle, a locked-version mismatch, or no parsable
            # feature row: whatever the observation contained, this arm was not
            # put at risk by it.
            unmeasured.add(hypothesis_id)
            continue
        covered = False
        for bundle_id in detail.get("bundle_ids") or []:
            bundle = repository.causal_blind_prediction_bundle(str(bundle_id))
            if bundle is None:
                continue
            report = bundle_feature_row_report(bundle["predictions"])
            for row in report.rows:
                if all(key in observed_features for key in row.keys):
                    covered = True
                    break
            if covered:
                break
        (measured if covered else unmeasured).add(hypothesis_id)
    return measured, unmeasured


def _observation_support_scores(
    classification: Mapping[str, Any], measured: set[str]
) -> dict[str, float]:
    """Support mass a discriminating observation licenses, and nothing more.

    ``matched_single`` puts all of it on the one hypothesis whose pre-registered
    prediction was borne out; every other MEASURED hypothesis is scored 0.0
    because its prediction was tested and failed.  An unmeasured hypothesis gets
    no entry at all — the resulting gap is what makes
    ``normalize_causal_support`` report ``incomplete`` and refuse promotion,
    which is the honest outcome for an instrument that did not test everything.
    """

    outcome = str(classification.get("outcome") or "")
    if outcome not in DISCRIMINATING_OUTCOMES:
        return {}
    matched = {
        str(value)
        for value in classification.get("classified_as") or []
        if not classification.get("supports_open_set")
    }
    return {
        hypothesis_id: (1.0 if hypothesis_id in matched else 0.0)
        for hypothesis_id in sorted(measured)
    }


def record_probe_classification(
    repository: Repository,
    *,
    presentation_id: str,
    observed_features: Mapping[str, Any],
    feature_source: str,
    probe_attempt_id: str | None = None,
    clock: Clock | None = None,
) -> DiscriminatingObservation:
    """Classify an administered probe AND act on the verdict (§6, §7).

    This is the edge the P2 lane was missing.  A probe could be offered,
    accepted, served with pinned bundles, answered and classified — and then
    nothing consumed the verdict: no factor closed, no diagnosis support moved.

    What it will and will not close:

    * ``matched_single`` over features that actually MEASURED every evaluable
      hypothesis resolves the factor and records support.  Exactly one
      pre-registered blind prediction was borne out and the rivals' were tested
      and failed; that is a discriminating observation.
    * ``no_bundle_matched`` over the same coverage is genuine open-set evidence
      for ``H_OTHER`` (§3.5) and is recorded as such — but it resolves NOTHING.
      An open-world arm names no cause, so there is no branch-specific repair to
      unblock.
    * ``matched_multiple`` and ``all_bundles_matched`` mean the instrument did
      not discriminate; ``cohort_mismatch`` and ``unparsed_features`` mean it
      could not be read.  All four are recorded and resolve nothing.  Agent A3
      split these outcomes apart precisely so "the instrument failed" stops
      being indistinguishable from "the answer fits none of our causes".
    * Any outcome whose declared features were not observed is inadmissible,
      whatever it says.  See :func:`_measured_hypotheses`.

    SUPPORT AUTHORITY — the deliberate split (argued, not assumed):

    Resolving the factor and granting routing authority are different powers and
    are gated differently.

    * The FACTOR closes on any admitted ``matched_single``.  The epistemic guard
      there is pre-registration: the prediction was committed before the response
      existed, is content-addressed and append-only, was cohort-pinned, and
      passed the register -> review -> activate ladder plus a manipulation-contract
      audit.  Requiring a deterministic sensor as well would make the lane
      unreachable for every short-answer probe, which is most of them.
    * ``validator_owned`` SUPPORT — which is what unlocks the §2.1
      ``causal_authority`` promotion arm in `failure_triage` — is granted only
      when the observed features came from a deterministic sensor
      (``feature_source == "deterministic"``).  The match is deterministic; the
      *sensor* need not be, and a model reading "did the answer transpose?" out
      of prose is a model-reported quantity however deterministic the comparison
      downstream is.  Standing constraint 4 (deterministic quantities outrank
      model-reported ones) is a per-input rule, so the provenance is recorded
      per input rather than inferred from the pipeline's last step.
    * A model-extracted observation still reaches triage as support and may
      therefore VETO a tier-one route.  §2.1 lets causal support downgrade
      freely and restricts only promotion; a conservative downgrade on real
      discriminating evidence is exactly the asymmetry it asks for.

    Diagnosis support moves ONLY through this receipt.  It is never a side
    effect of repair success, and it is deliberately not written back onto the
    diagnosis receipt: that lives in ``attempt_debug_payloads``, which replay
    rebuilds, so support written there would be silently discarded.
    """

    if feature_source not in OBSERVATION_FEATURE_SOURCES:
        raise ValueError(f"unknown observed-feature source {feature_source!r}")
    classification = classify_probe_response(
        repository,
        presentation_id=presentation_id,
        observed_features=observed_features,
    )
    factor_id = classification.get("causal_factor_id")
    if not factor_id:
        raise CausalRepairError(
            "pinned causal probe names no causal factor to observe"
        )
    factor_id = str(factor_id)
    factor = repository.unresolved_cause_factor(factor_id)
    attempt_id = str((factor or {}).get("attempt_id") or "") or None

    outcome = str(classification.get("outcome") or "")
    measured, unmeasured = _measured_hypotheses(
        repository, classification, observed_features
    )
    declared_keys_observed = not unmeasured and bool(measured)

    if outcome not in DISCRIMINATING_OUTCOMES:
        admitted, admission_reason = False, f"non_discriminating_outcome:{outcome}"
    elif not declared_keys_observed:
        # The verdict is an artefact of what was not measured, not of what was.
        admitted, admission_reason = False, "declared_features_not_observed"
    else:
        admitted, admission_reason = True, f"{outcome}_over_measured_features"

    support_scores = (
        _observation_support_scores(classification, measured) if admitted else {}
    )
    support_authority = (
        SUPPORT_BASIS_AUTHORITY[BLIND_PROBE_BASIS]
        if admitted and feature_source in VALIDATOR_OWNED_FEATURE_SOURCES
        else None
    )

    identity = {
        "presentation_id": presentation_id,
        "blind_bundle_ids": sorted(
            str(value) for value in classification.get("blind_bundle_ids") or []
        ),
        "observed_features": dict(observed_features),
        "feature_source": feature_source,
        "outcome": outcome,
    }
    observation_id = _content_id("cdo", identity)

    # Resolve BEFORE recording so the receipt can state truthfully whether it
    # was the observation that closed the factor.  A factor already closed by
    # another channel is not re-closed and the receipt says so.
    resolved = False
    if admitted and outcome == "matched_single":
        resolved = repository.resolve_unresolved_cause_factor(
            factor_id,
            resolution_observation_ids=[observation_id],
            clock=clock,
        )
    receipt = repository.insert_causal_discriminating_observation(
        observation_id=observation_id,
        factor_id=factor_id,
        attempt_id=attempt_id,
        probe_attempt_id=probe_attempt_id,
        presentation_id=presentation_id,
        hypothesis_set_id=str(classification.get("hypothesis_set_id") or ""),
        candidate_id=(
            str(classification["causal_probe_candidate_id"])
            if classification.get("causal_probe_candidate_id")
            else None
        ),
        blind_bundle_ids=identity["blind_bundle_ids"],
        outcome=outcome,
        classified_as=[
            str(value) for value in classification.get("classified_as") or []
        ],
        supports_open_set=bool(classification.get("supports_open_set")) and admitted,
        feature_source=feature_source,
        observed_features=dict(observed_features),
        declared_keys_observed=declared_keys_observed,
        admitted=admitted,
        admission_reason=admission_reason,
        support_authority=support_authority,
        support_scores=support_scores,
        resolved_factor=resolved,
        detail={
            "basis": BLIND_PROBE_BASIS,
            "measured_hypothesis_ids": sorted(measured),
            "unmeasured_hypothesis_ids": sorted(unmeasured),
            "classification_details": classification.get("details") or [],
            "cohort": classification.get("cohort"),
        },
        decision_policy_version=CAUSAL_DECISION_POLICY_VERSION,
        formula_version=CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
        clock=clock,
    )
    return DiscriminatingObservation(
        classification=classification,
        receipt=receipt,
        admitted=admitted,
        admission_reason=admission_reason,
        resolved_factor=resolved,
        support_authority=support_authority,
        support_scores=support_scores,
    )


def deterministic_probe_features(
    vault: LoadedVault, repository: Repository, attempt_id: str
) -> dict[str, Any]:
    """The graded probe attempt's own criterion outcomes, as a feature vector.

    ``{"criterion:<id>:passed": bool, "criterion:<id>:full_credit": bool}``.

    This is the one probe sensor that runs no model: the values come from
    recorded grading evidence against the item's authored rubric.  A blind
    bundle whose predictions are declared in this vocabulary can therefore be
    classified automatically, with ``feature_source="deterministic"`` and the
    ``validator_owned`` grant it earns.  A bundle that declares anything else
    needs a sensor that can read it, and :func:`auto_classify_pinned_probe`
    declines rather than guessing.

    It is deliberately NOT a global feature registry (§3.1): bundles still
    declare their own key sets, and this vocabulary is simply the subset a
    deterministic sensor can supply.
    """

    attempt = repository.fetch_practice_attempt(attempt_id) or {}
    item = vault.practice_items.get(str(attempt.get("practice_item_id") or ""))
    rubric = vault.rubric_for_item(item) if item is not None else None
    if item is None or rubric is None:
        return {}
    evidence = {
        row.criterion_id: row for row in repository.fetch_grading_evidence(attempt_id)
    }
    features: dict[str, Any] = {}
    for criterion in rubric.criteria:
        awarded = float(
            evidence[criterion.id].points_awarded
            if criterion.id in evidence
            else 0.0
        )
        possible = float(criterion.points)
        fraction = max(0.0, min(1.0, awarded / possible)) if possible > 0 else 0.0
        features[f"{DETERMINISTIC_FEATURE_PREFIX}{criterion.id}:passed"] = (
            fraction >= 0.40
        )
        features[f"{DETERMINISTIC_FEATURE_PREFIX}{criterion.id}:full_credit"] = (
            fraction >= 1.0 - 1e-9
        )
    return features


def auto_classify_pinned_probe(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    clock: Clock | None = None,
) -> DiscriminatingObservation | None:
    """Close the loop automatically when a probe answer can be read by machine.

    Runs on the live post-attempt path.  Returns ``None`` — recording nothing —
    unless the attempt consumed a presentation carrying a pinned causal probe
    AND every declared feature key of the pinned bundles is in the deterministic
    vocabulary :func:`deterministic_probe_features` supplies.

    That gate is not squeamishness.  The matcher is exact over declared keys, so
    handing it a feature vector that simply lacks those keys yields
    ``no_bundle_matched`` — which §3.5 defines as open-set evidence for
    ``H_OTHER``.  Auto-classifying against an incapable sensor would therefore
    manufacture evidence that the learner's cause is outside the hypothesis set,
    from a probe that was never actually read.  Declining is the only honest
    default; a bundle authored in the deterministic vocabulary needs no learner
    or app involvement at all.
    """

    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        return None
    presentation_id = attempt.get("probe_presentation_id")
    if not presentation_id:
        return None
    pinned = pinned_causal_probe(repository, str(presentation_id))
    if not pinned or not pinned.get("blind_bundle_ids"):
        return None
    if repository.causal_discriminating_observations(
        presentation_id=str(presentation_id)
    ):
        # Already observed. Re-classifying the same probe from a second hook
        # would append a duplicate verdict under a new attempt id.
        return None
    features = deterministic_probe_features(vault, repository, attempt_id)
    if not features:
        return None
    declared: set[str] = set()
    for bundle_id in pinned["blind_bundle_ids"]:
        bundle = repository.causal_blind_prediction_bundle(str(bundle_id))
        if bundle is None:
            return None
        for row in bundle_feature_row_report(bundle["predictions"]).rows:
            declared.update(row.keys)
    if not declared or not declared <= set(features):
        return None
    return record_probe_classification(
        repository,
        presentation_id=str(presentation_id),
        observed_features=features,
        feature_source="deterministic",
        probe_attempt_id=attempt_id,
        clock=clock,
    )


# --- §6.2 cold verification context -----------------------------------------


def cold_verification_context(
    vault: LoadedVault | None,
    repository: Repository,
    *,
    episode: Mapping[str, Any],
    source_attempt: Mapping[str, Any],
) -> dict[str, Any]:
    """Everything ``record_delayed_cold_verification`` will need, resolved NOW.

    §6.2: carry the source attempt, causal factor, hypothesis set, repair class
    and avoided affordances THROUGH the follow-up task record.  Resolving them
    days later, from a consumed task and a bare item id, is the "future caller
    reconstructs it" assumption that leaves the cold channel unwired.

    ``vault`` is optional because this runs inside ``apply_attempt``'s
    remediation hook, which has no vault handle; without it the source surface
    family is simply not named among the avoided affordances.
    """

    from learnloop.services.canonical_projection import surface_group_id

    case_ref = str(episode.get("case_ref") or "")
    hypothesis = (
        repository.causal_hypothesis(case_ref)
        if episode.get("case_kind") == "diagnosis"
        else None
    )
    factor_id: str | None = None
    hypothesis_set_id: str | None = None
    repair_class_id: str | None = None
    hypothesis_ids: list[str] = []
    if hypothesis is not None:
        hypothesis_ids = [str(hypothesis["id"])]
        repair_class_id = (
            str(hypothesis["repair_class_id"])
            if hypothesis.get("repair_class_id")
            else None
        )
        factors = open_factors_for_hypothesis(repository, case_ref)
        if factors:
            factor_id = str(factors[0]["id"])
            hypothesis_ids = sorted(
                {
                    str(value.get("hypothesis_id"))
                    for value in factors[0].get("candidate_causes") or []
                    if isinstance(value, Mapping) and value.get("hypothesis_id")
                }
                | set(hypothesis_ids)
            )
            candidates = repository.causal_probe_candidates_for_factor(factor_id)
            if candidates:
                hypothesis_set_id = str(candidates[0]["hypothesis_set_id"])
    if repair_class_id is None:
        receipt = _diagnosis_receipt(
            repository, str(source_attempt.get("id") or "") or None
        )
        if isinstance(receipt, Mapping):
            cover = receipt.get("common_repair_cover")
            if isinstance(cover, Mapping) and cover.get("repair_class_id"):
                repair_class_id = str(cover["repair_class_id"])
            else:
                selection = receipt.get("repair_selection")
                if isinstance(selection, Mapping) and selection.get(
                    "repair_class_id"
                ):
                    repair_class_id = str(selection["repair_class_id"])

    # The affordances the primed source attempt had and the cold retry avoids.
    avoided: list[str] = ["primed_repair_context"]
    if int(source_attempt.get("hints_used") or 0) > 0:
        avoided.append("hints")
    primed_item = (
        vault.practice_items.get(str(source_attempt.get("practice_item_id") or ""))
        if vault is not None
        else None
    )
    if primed_item is not None:
        avoided.append(f"surface_family:{surface_group_id(primed_item)}")
    if episode.get("passages_shown"):
        avoided.append("remediation_passages")

    return {
        "kind": "causal_cold_verification",
        "formula_version": CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
        "source_attempt_id": str(source_attempt.get("id") or ""),
        "causal_factor_id": factor_id,
        "hypothesis_set_id": hypothesis_set_id,
        "hypothesis_ids": hypothesis_ids,
        "repair_class_id": repair_class_id,
        "avoided_affordances": sorted(set(avoided)),
    }


def record_cold_verification_from_task(
    vault: LoadedVault,
    repository: Repository,
    *,
    task: Mapping[str, Any],
    cold_attempt_id: str,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Fire the delayed cold verification when a scheduled retry completes.

    Returns the receipt, or None with no side effect when the carried context is
    incomplete or the pair does not satisfy the §6.2 preconditions (same surface
    family, assisted retry, non-monotone chronology).  This runs inside
    ``apply_attempt``, so it must never raise on the hot path.
    """

    from learnloop.services.causal_probe_coherence import (
        record_delayed_cold_verification,
    )

    context = task.get("context")
    if not isinstance(context, Mapping):
        return None
    if context.get("kind") != "causal_cold_verification":
        return None
    repair_class_id = context.get("repair_class_id")
    source_attempt_id = context.get("source_attempt_id")
    if not repair_class_id or not source_attempt_id:
        # No repair class means there is no repair-effect claim to make.  Stay
        # silent rather than inventing one.
        return None
    try:
        return record_delayed_cold_verification(
            vault,
            repository,
            source_attempt_id=str(source_attempt_id),
            cold_attempt_id=cold_attempt_id,
            repair_class_id=str(repair_class_id),
            hypothesis_ids=[
                str(value) for value in context.get("hypothesis_ids") or []
            ],
            avoided_affordances=[
                str(value) for value in context.get("avoided_affordances") or []
            ],
            clock=clock,
        )
    except ValueError:
        # A precondition failed (same surface family, assisted cold attempt,
        # chronology).  The verification simply does not apply; the attempt
        # itself is unaffected.
        return None


__all__ = [
    "BLIND_PROBE_BASIS",
    "CAUSAL_ORCHESTRATOR_FORMULA_VERSION",
    "CAUSAL_ORCHESTRATOR_POLICY_DEFAULTS",
    "CAUSAL_ORCHESTRATOR_POLICY_SCOPE",
    "CausalRepairError",
    "DETERMINISTIC_FEATURE_PREFIX",
    "DISCRIMINATING_OUTCOMES",
    "EVSI_PROVENANCE",
    "OBSERVATION_FEATURE_SOURCES",
    "VALIDATOR_OWNED_FEATURE_SOURCES",
    "DiscriminatingObservation",
    "DiscriminationInputs",
    "EPISODE_CONFLICT_MESSAGE",
    "EPISODE_CONFLICT_REASON",
    "LEARNER_PREFERENCES",
    "MACHINE_CHECK_REPAIR_MAPPING",
    "NEEDS_DISAMBIGUATION_MESSAGE",
    "ProbeOffer",
    "REPAIR_STATUSES",
    "RepairAction",
    "RepairStatus",
    "accept_probe_offer",
    "auto_classify_pinned_probe",
    "backfill_obligation",
    "causal_repair_status",
    "classify_probe_response",
    "close_satisfied_backfills",
    "deterministic_probe_features",
    "enqueue_backfill_obligation",
    "episode_conflict_reason",
    "cold_verification_context",
    "defer_probe_offer",
    "learner_preference",
    "record_probe_classification",
    "open_factors_for_hypothesis",
    "pending_machine_checks_for_factor",
    "pinned_causal_probe",
    "record_cold_verification_from_task",
    "record_learner_preference",
    "request_teaching_now",
    "resolve_machine_check",
    "resolve_orchestrator_parameters",
    "sweep_machine_checks",
]
