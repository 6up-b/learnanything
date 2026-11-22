"""Queue and discharge machine-side obligations before causal repair.

A machine check records work owed by the system rather than the learner.
Repair-mapping checks block probes; instrument-commissioning checks track
missing instruments for causes whose repairs diverge. The repair decision
and post-attempt follow-up hooks queue obligations. Per-attempt sweeps close
obsolete checks, reconcile expired cold retries and sweep deferred factors;
authors, verifiers and regrade agents can explicitly discharge checks.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.followup_serve.gates import RIVAL_CAUSES_FACTOR_VERSION
from learnloop.diagnosis.causal_probe_coherence import candidate_has_current_blind_input_contract
from learnloop.diagnosis.probe_targeting import classify_cause_set
from learnloop.diagnosis.causal_reads import (
    CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
    MACHINE_CHECK_INSTRUMENT_COMMISSIONING,
    MACHINE_CHECK_REPAIR_MAPPING,
    PROBE_BLOCKING_MACHINE_CHECK_KINDS,
    SWEPT_MACHINE_CHECK_KINDS,
)
from learnloop.diagnosis.content_ids import content_id
from learnloop.vault.models import LoadedVault
from learnloop.diagnosis.causal_cold_verification import sweep_expired_cold_retries
from learnloop.diagnosis.remediation import end_untaken_episodes


def _machine_check_id(obligation: Mapping[str, Any]) -> str:
    return content_id(
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


def instrument_commissioning_obligation(targeting: Any) -> dict[str, Any]:
    """The typed obligation for a divergent factor with no instrument.

    This is the queue entry the P2 lane never had.  Its causes need different
    repairs, so the branch-specific repair is held; discriminating them needs an
    instrument, and until one is commissioned the orchestrator can only report
    ``no_discriminating_instrument``.  Recording the debt makes it drainable
    instead of a state the system re-derives and forgets on every attempt.
    """

    return {
        "kind": MACHINE_CHECK_INSTRUMENT_COMMISSIONING,
        "state": targeting.state,
        "coherence_gate_state": targeting.coherence_gate_state,
        "factor_id": targeting.factor_id,
        "attempt_id": targeting.attempt_id,
        "hypothesis_ids": [
            str(cause.get("hypothesis_id"))
            for cause in targeting.causes
            if isinstance(cause, Mapping) and cause.get("hypothesis_id")
        ],
        "repair_class_ids": list(targeting.repair_class_ids),
        "reason": targeting.reason,
        # Nothing for the learner to do: an instrument is machine-side work.
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
        if factor.get("algorithm_version") == RIVAL_CAUSES_FACTOR_VERSION:
            # R9: FG1 writes this factor's question from its causes, so it owes no mapping,
            # and a check here would refuse the question for a repair class it doesn't need.
            continue
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
        if targeting.needs_machine_backfill:
            obligation = backfill_obligation(targeting)
            live.add(_machine_check_id(obligation))
            enqueue_backfill_obligation(
                repository,
                obligation,
                learning_object_id=learning_object_id,
                source=source,
                clock=clock,
            )
            continue
        # Stage 2.1: the mapping is complete and the causes still diverge, so what
        # is missing is an INSTRUMENT. Queue that debt rather than re-deriving
        # "no_discriminating_instrument" on every attempt and forgetting it.
        # Commissioning itself is not run here: it locks a hypothesis set and
        # writes prediction bundles per factor, which is not post-attempt work.
        if targeting.probe_worthy and len(targeting.repair_class_ids) > 1:
            if any(
                value.get("status") != "rejected"
                and candidate_has_current_blind_input_contract(value)
                for value in repository.causal_probe_candidates_for_factor(
                    str(factor["id"])
                )
            ):
                continue
            obligation = instrument_commissioning_obligation(targeting)
            live.add(_machine_check_id(obligation))
            enqueue_backfill_obligation(
                repository,
                obligation,
                learning_object_id=learning_object_id,
                source=source,
                clock=clock,
            )
    # Piggyback the §4.3 expiry reconciliation on the one per-attempt hook that
    # holds a vault handle (`_run_causal_orchestrator_hooks` calls this on
    # every attempt).  Guarded independently: a fault here must not block the
    # machine-check sweep it rides on.
    try:
        sweep_expired_cold_retries(vault, repository, clock=clock)
    except Exception:  # pragma: no cover - bookkeeping must not fail an attempt
        logging.getLogger(__name__).warning(
            "expired cold-retry reconciliation failed", exc_info=True
        )
    # The same hook ends a repair episode whose primed attempt was never taken once its item's next ordinary
    # review is due (mvp-0.64); without it such an episode, and its cold item's reservation, never end.
    try:
        end_untaken_episodes(vault, repository, clock=clock)
    except Exception:  # pragma: no cover - bookkeeping must not fail an attempt
        logging.getLogger(__name__).warning(
            "untaken repair episode sweep failed", exc_info=True
        )
    # Bounded factor deferral rides the same per-attempt hook so abandoned
    # cases expire even when no attempt on their own learning object ever
    # re-materializes (the escalation-critical run happens earlier, inside
    # `_normalize_compositional`, before the promotion-block read).
    try:
        from learnloop.diagnosis.causal_factor_deferral import (
            sweep_promotion_blocking_factors,
        )

        sweep_promotion_blocking_factors(repository, clock=clock)
    except Exception:  # pragma: no cover - bookkeeping must not fail an attempt
        logging.getLogger(__name__).warning(
            "promotion-blocking factor sweep failed", exc_info=True
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
        if str(check["kind"]) not in SWEPT_MACHINE_CHECK_KINDS:
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

    Factor-scoped checks plus learning-object-wide checks that name no factor,
    restricted to :data:`PROBE_BLOCKING_MACHINE_CHECK_KINDS` — an instrument
    commissioning obligation is real machine-side debt but it does not make
    ``defer_machine_checks`` the honest answer (see that constant).
    """

    checks = [
        check
        for check in repository.causal_machine_checks(
            status="pending", factor_id=factor_id
        )
        if str(check["kind"]) in PROBE_BLOCKING_MACHINE_CHECK_KINDS
    ]
    seen = {str(check["id"]) for check in checks}
    if learning_object_id is not None:
        for check in repository.causal_machine_checks(
            status="pending", learning_object_id=learning_object_id
        ):
            if check.get("factor_id") or str(check["id"]) in seen:
                continue
            if str(check["kind"]) not in PROBE_BLOCKING_MACHINE_CHECK_KINDS:
                continue
            checks.append(check)
    return checks
