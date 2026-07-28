"""Bounded deferral for promotion-blocking unresolved-cause factors.

``causal_attribution._open_diagnostic_repair_factor`` opens an
``unresolved_cause_factors`` row (``observation_id`` NULL) for every failed
diagnostic administration with a mapped repair class, and
``misconceptions._normalize_compositional`` defers durable-misconception
promotion while the attempt's factor is open. Deferral stays the default —
an ambiguous failure should route to repair, not mint a durable belief — but
before this module the window was infinite: every failed diagnostic probe
blocked its own promotion and nothing ever closed the factor unless the
learner took the probe or an adjudication landed.

This module makes the window finite. Every exit is evidence-labeled on the
factor row (migration 148: ``resolution_kind`` / ``resolution_detail_json``):

(a) ``repair_confirmed`` — a cold verification SUCCEEDED on the factor's
    repair class. The cause is confirmed-and-fixed: the factor resolves, the
    candidate belief is WITHDRAWN (a retired hypothesis version through the
    append-only ``causal_hypotheses`` disposition machinery), and promotion is
    neither blocked nor triggered — there is nothing left to promote.

(b) ``escalated_unrepaired`` — either a cold verification FAILED on the
    factor's repair class, or the same error signature recurred
    :data:`ESCALATION_RECURRENCE_K` more times after the case's first factor
    opened with NO learner engagement. The factor resolves toward promotion:
    the next materialization of the recurring signature is free to promote a
    durable misconception through the ordinary §10.3 arms.

(c) ``expired_unengaged`` — the factor sat open past
    :data:`FACTOR_DEFERRAL_TTL` with no engagement. Retired; promotion
    unblocked. An abandoned diagnosis must not veto the learner model forever.

Replay-safety: every input is derived from stored, append-only records —
cold-verification rows, ``causal_hypotheses`` versions (rebuilt by replay from
attempts), remediation episodes, attribution reports and primed attempts —
and every timestamp comparison uses the injected attempt-time clock, exactly
like ``causal_orchestrator.sweep_expired_cold_retries``. Re-running the sweep
(or replaying attempts) reproduces identical factor outcomes; closing an
already-closed factor is a no-op.

Scope guard: only ``observation_id IS NULL`` factors are touched. The
observation-keyed factors are owned by the canonical projection's
``_sync_unresolved_cause_factors`` reconciliation, and closing one here could
fight that sync (a 'retired' observation factor would be re-opened on the
next projection pass).
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Mapping

from learnloop.clock import Clock, SystemClock, parse_utc
from learnloop.db.repositories import Repository

#: §10.3 deferral escalation: this many further recurrences of the same error
#: signature after the case's first factor opened — with no learner engagement
#: on the case — resolve the deferral toward promotion. Mirrors the lane's
#: other small evidence thresholds (e.g. ``config.py``'s per-signal
#: ``promotion_threshold = 3``); a module constant rather than vault config
#: because the deferral bound is an algorithm property, not a tuning knob.
ESCALATION_RECURRENCE_K = 3

#: Factors open longer than this with no engagement retire as
#: ``expired_unengaged``. Mirrors the repair lane's 30-day cold-retry expiry
#: (``remediation.record_remediation_attempt``: ``expires = not_before +
#: timedelta(days=30)``) — the same "the learner has moved on" horizon.
FACTOR_DEFERRAL_TTL = timedelta(days=30)

_HYPOTHESIS_STATUSES = ("candidate", "validated", "retired", "demoted")


def _concrete_refs(factor: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The factor's hydrated non-open-set candidate refs."""

    refs: list[dict[str, Any]] = []
    for candidate in factor.get("candidate_causes") or []:
        if not isinstance(candidate, Mapping):
            continue
        if candidate.get("open_set") or candidate.get("hypothesis_id") in (
            None,
            "H_OTHER",
        ):
            continue
        refs.append(dict(candidate))
    return refs


def _open_diagnostic_factors(repository: Repository) -> list[dict[str, Any]]:
    return [
        factor
        for factor in repository.unresolved_cause_factors(status="open")
        if factor.get("observation_id") is None
    ]


def _withdraw_candidate_hypothesis(
    repository: Repository,
    hypothesis_id: str,
    *,
    reason: str,
    evidence_ref: Mapping[str, Any],
    clock: Clock | None,
) -> str | None:
    """Withdraw one candidate belief by appending a retired hypothesis version.

    ``causal_hypotheses`` is the single durable home for candidate beliefs in
    canonical vaults (``_projected_causal_candidates`` is a projection over its
    candidate heads), so the existing disposition machinery is a status
    transition appended to the episode chain. A retired head drops out of the
    candidate projection, which is exactly what "withdrawn, do NOT promote"
    means: ``misconception_candidate_by_normalized`` stops returning the
    belief, so no later attempt can promote it. Idempotent: an already-retired
    head is left alone, and ``append_causal_hypothesis`` collapses an
    identical re-append onto the existing head.

    Durable ``misconception_disposition_events`` withdrawal
    (``surfaced_beliefs.record_belief_withdrawal``) is deliberately NOT used
    here: it is FK-bound to promoted ``misconceptions`` rows, and a factor in
    deferral by definition has none.
    """

    hypothesis = repository.causal_hypothesis(hypothesis_id)
    if hypothesis is None:
        return None
    head = repository.latest_causal_hypothesis_for_episode(
        str(hypothesis["episode_key"])
    )
    if head is None or head.get("status") != "candidate":
        return None
    evidence = dict(head.get("evidence") or {})
    evidence["withdrawal"] = {"reason": reason, **dict(evidence_ref)}
    retired = repository.append_causal_hypothesis(
        episode_key=str(head["episode_key"]),
        attempt_id=str(head["attempt_id"]),
        error_event_id=head.get("error_event_id"),
        learning_object_id=str(head["learning_object_id"]),
        cause_scope=str(head["cause_scope"]),
        statement=str(head["statement"]),
        statement_normalized=str(head["statement_normalized"]),
        mechanism=head.get("mechanism"),
        operation=head.get("operation"),
        target_ref=head.get("target_ref"),
        applicability=head.get("applicability"),
        postdictive_claims=head.get("postdictive_claims") or [],
        evidence=evidence,
        repair_class_id=head.get("repair_class_id"),
        repair_class_basis=head.get("repair_class_basis"),
        repair_class_unresolved_reason=head.get("repair_class_unresolved_reason"),
        status="retired",
        generation_agent_run_id=head.get("generation_agent_run_id"),
        model=head.get("model"),
        clock=clock,
    )
    return str(retired["id"])


def apply_cold_verification_to_factors(
    repository: Repository,
    *,
    receipt: Mapping[str, Any],
    clock: Clock | None = None,
) -> list[dict[str, Any]]:
    """Route one recorded cold verification into open diagnostic factors.

    * success=True → exit (a): resolve as ``repair_confirmed`` and withdraw
      the matched candidate beliefs. Deliberately narrow: this is a
      REPAIR-EFFECT consequence only. It never touches diagnosis support —
      ``record_delayed_cold_verification``'s guard that repair success cannot
      retroactively prove the diagnosis stands untouched — and it never
      promotes.
    * success=False → exit (b-i): resolve as ``escalated_unrepaired`` so the
      recurring signature may promote on its next materialization.

    Idempotent: factors already closed are skipped, and re-recording the same
    (content-addressed) verification finds nothing left open to act on.
    """

    repair_class_id = str(receipt.get("repair_class_id") or "")
    if not repair_class_id:
        return []
    success = bool(receipt.get("success"))
    verification_id = str(receipt.get("id") or "")
    actions: list[dict[str, Any]] = []
    for factor in _open_diagnostic_factors(repository):
        matched = [
            ref
            for ref in _concrete_refs(factor)
            if str(ref.get("repair_class_id") or "") == repair_class_id
        ]
        if not matched:
            continue
        factor_id = str(factor["id"])
        if success:
            closed = repository.close_unresolved_cause_factor(
                factor_id,
                status="resolved",
                resolution_kind="repair_confirmed",
                resolution_detail={
                    "cold_verification_id": verification_id,
                    "repair_class_id": repair_class_id,
                },
                clock=clock,
            )
            withdrawn = [
                retired_id
                for ref in matched
                if (
                    retired_id := _withdraw_candidate_hypothesis(
                        repository,
                        str(ref["hypothesis_id"]),
                        reason="repair_confirmed",
                        evidence_ref={"cold_verification_id": verification_id},
                        clock=clock,
                    )
                )
                is not None
            ]
            if closed or withdrawn:
                actions.append(
                    {
                        "factor_id": factor_id,
                        "resolution_kind": "repair_confirmed",
                        "withdrawn_hypothesis_ids": withdrawn,
                    }
                )
        else:
            closed = repository.close_unresolved_cause_factor(
                factor_id,
                status="resolved",
                resolution_kind="escalated_unrepaired",
                resolution_detail={
                    "trigger": "cold_verification_failure",
                    "cold_verification_id": verification_id,
                    "repair_class_id": repair_class_id,
                },
                clock=clock,
            )
            if closed:
                actions.append(
                    {
                        "factor_id": factor_id,
                        "resolution_kind": "escalated_unrepaired",
                    }
                )
    return actions


def _factor_signature(
    repository: Repository, factor: Mapping[str, Any]
) -> tuple[set[str], str | None]:
    """(normalized statements, learning_object_id) for a factor's concrete refs."""

    statements: set[str] = set()
    learning_object_id: str | None = None
    for ref in _concrete_refs(factor):
        hypothesis = repository.causal_hypothesis(str(ref["hypothesis_id"]))
        if hypothesis is None:
            continue
        statements.add(str(hypothesis["statement_normalized"]))
        learning_object_id = learning_object_id or str(
            hypothesis["learning_object_id"]
        )
    return statements, learning_object_id


def _signature_hypotheses(
    repository: Repository, learning_object_id: str, statements: set[str]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for statement in sorted(statements):
        rows.extend(
            repository.causal_hypotheses_for_learning_object(
                learning_object_id,
                statuses=_HYPOTHESIS_STATUSES,
                latest_only=False,
                statement_normalized=statement,
            )
        )
    return rows


def _case_engaged(
    repository: Repository,
    *,
    learning_object_id: str,
    statements: set[str],
    case_factor_ids: list[str],
    hypothesis_rows: list[dict[str, Any]],
    since: str,
) -> bool:
    """Any learner engagement on the case since its first factor opened.

    Three deliberately cheap, stored signals (each one row-bounded):

    1. A remediation episode (any state) whose case_ref names the case — the
       TEACH_ME_NOW / common-repair / treatment path was entered. Diagnosis-kind
       episodes reference hypothesis ids; candidate-kind reference the projected
       candidate id, which IS a hypothesis id in canonical vaults, so the
       hypothesis-id set covers both. Legacy ``misconception_candidates`` rows
       are covered through ``misconception_candidate_by_normalized``.
    2. A learner response on any of the case's diagnostic surfaces — an
       attribution self-report or a classified probe response
       (TAKE_QUICK_CHECK) on one of the case's factors.
    3. A primed attempt on the learning object — a guided redo or the primed
       half of a repair pair, which exists even when no episode row was bound.
    """

    case_refs = {str(row["id"]) for row in hypothesis_rows}
    for statement in sorted(statements):
        legacy = repository.misconception_candidate_by_normalized(
            learning_object_id, statement
        )
        if legacy is not None:
            case_refs.add(str(legacy["id"]))
    for episode in repository.remediation_episodes_for_case_refs(sorted(case_refs)):
        if str(episode.get("created_at") or "") >= since:
            return True
    for factor_id in case_factor_ids:
        if repository.causal_attribution_reports_for_factor(factor_id):
            return True
        if repository.causal_discriminating_observations(factor_id=factor_id):
            return True
    return repository.primed_attempt_exists_for_learning_object(
        learning_object_id, since=since
    )


def sweep_promotion_blocking_factors(
    repository: Repository,
    *,
    clock: Clock | None = None,
) -> list[dict[str, Any]]:
    """Attempt-time sweep: exits (b-ii) and (c) for open diagnostic factors.

    Runs from the same seams as ``sweep_expired_cold_retries`` (the per-attempt
    orchestrator hook) and from ``_normalize_compositional`` between episode
    materialization and the promotion-block check, so an escalation that fires
    on the Kth recurrence unblocks THAT materialization rather than the one
    after it. The clock is the injected attempt clock — replay reproduces
    identical outcomes because it re-runs with the same attempt timestamps.

    Trigger scoping: "K further recurrences after the factor opened" is
    anchored on the CASE's first factor (the earliest factor sharing any of
    the signature's normalized statements). Every open factor of that
    signature escalates together — each failed diagnostic administration opens
    its own factor, and ``_normalize_compositional`` blocks on the CURRENT
    attempt's factor, so escalating only the oldest would leave the block in
    place forever.
    """

    open_factors = _open_diagnostic_factors(repository)
    if not open_factors:
        return []
    now = (clock or SystemClock()).now()
    all_factors = [
        factor
        for factor in repository.unresolved_cause_factors(status=None)
        if factor.get("observation_id") is None
    ]
    actions: list[dict[str, Any]] = []
    for factor in open_factors:
        factor_id = str(factor["id"])
        statements, learning_object_id = _factor_signature(repository, factor)
        if not statements or learning_object_id is None:
            continue
        hypothesis_rows = _signature_hypotheses(
            repository, learning_object_id, statements
        )
        case_attempt_ids = {str(row["attempt_id"]) for row in hypothesis_rows}
        case_factors = sorted(
            (
                candidate_factor
                for candidate_factor in all_factors
                if str(candidate_factor.get("attempt_id") or "") in case_attempt_ids
            ),
            key=lambda row: (str(row["created_at"]), str(row["id"])),
        )
        first = case_factors[0] if case_factors else factor
        first_opened = str(first["created_at"])
        if _case_engaged(
            repository,
            learning_object_id=learning_object_id,
            statements=statements,
            case_factor_ids=[str(row["id"]) for row in case_factors],
            hypothesis_rows=hypothesis_rows,
            since=first_opened,
        ):
            continue  # engagement keeps the deferral window open
        prior_escalation = next(
            (
                case_factor
                for case_factor in case_factors
                if str(case_factor.get("resolution_kind") or "")
                == "escalated_unrepaired"
                and str(case_factor["id"]) != factor_id
            ),
            None,
        )
        if prior_escalation is not None:
            # Escalation is sticky while the case stays unengaged: the bound
            # already resolved the deferral question for this signature, and
            # each further failed administration opens (and would otherwise
            # re-block on) a fresh factor. Re-deferring would undo the bound —
            # the recurring signature must be free to promote NOW.
            if repository.close_unresolved_cause_factor(
                factor_id,
                status="resolved",
                resolution_kind="escalated_unrepaired",
                resolution_detail={
                    "trigger": "prior_escalation",
                    "escalated_factor_id": str(prior_escalation["id"]),
                },
                clock=clock,
            ):
                actions.append(
                    {
                        "factor_id": factor_id,
                        "resolution_kind": "escalated_unrepaired",
                    }
                )
            continue
        recurrence_attempt_ids = sorted(
            {
                str(row["attempt_id"])
                for row in hypothesis_rows
                if str(row["attempt_id"]) != str(first["attempt_id"])
                and str(row.get("created_at") or "") >= first_opened
            }
        )
        if len(recurrence_attempt_ids) >= ESCALATION_RECURRENCE_K:
            if repository.close_unresolved_cause_factor(
                factor_id,
                status="resolved",
                resolution_kind="escalated_unrepaired",
                resolution_detail={
                    "trigger": "unengaged_recurrences",
                    "recurrence_attempt_ids": recurrence_attempt_ids,
                    "k": ESCALATION_RECURRENCE_K,
                    "first_factor_id": str(first["id"]),
                },
                clock=clock,
            ):
                actions.append(
                    {
                        "factor_id": factor_id,
                        "resolution_kind": "escalated_unrepaired",
                    }
                )
            continue
        opened_at = parse_utc(str(factor["created_at"]))
        if opened_at is not None and now - opened_at >= FACTOR_DEFERRAL_TTL:
            if repository.close_unresolved_cause_factor(
                factor_id,
                status="retired",
                resolution_kind="expired_unengaged",
                resolution_detail={
                    "ttl_days": FACTOR_DEFERRAL_TTL.days,
                    "opened_at": str(factor["created_at"]),
                },
                clock=clock,
            ):
                actions.append(
                    {
                        "factor_id": factor_id,
                        "resolution_kind": "expired_unengaged",
                    }
                )
    return actions
