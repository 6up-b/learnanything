"""P2 causal repair decisions (spec_causal_attribution_v1 §6).

Map an open factor to a learner-visible repair status, recording the probe
decision and machine-check obligations. The surrounding causal repair lane
connects this decision to learner actions and observations:

    open factor
      -> machine checks (must discharge first; principle 8)
      -> recorded probe decision (EVSI, every decision persisted)
      -> learner offer / defer ("Not now" persists)
      -> factor-aware episode (``enter_episode(causal_factor_id=...)``)
      -> reviewed-ACTIVE candidate with PINNED bundles
      -> classification against exactly those pinned bundles
      -> discriminating-observation receipt (resolves the factor)
      -> targeted repair
      -> cold verification (wired through the follow-up task record)

The discriminating observation and the learner's self-report each resolve a
factor; the episode posterior moves independently as observations arrive.
This module holds the repair decision and parameters. Learner offers and actions
live in ``probe_offer``; discriminating observations live in ``causal_discrimination``.
Factor and receipt reads live in ``causal_reads``; learner preferences and episode
conflicts live in ``probe_hard_stops``.

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

MACHINE CHECKS — scope statement (§6, §10b).  ``machine_checks`` owns the *queue*:
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

from dataclasses import dataclass, field, replace
import math
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.causal_attribution import CAUSAL_DECISION_POLICY_VERSION
from learnloop.diagnosis.causal_probe_coherence import (
    ProbeDecision,
    candidate_has_current_blind_input_contract,
    decide_probe,
    order_probe_candidates,
    repair_class_need_for_factor,
    resolve_causal_probe_parameters,
)
from learnloop.diagnosis.probe_targeting import (
    CAUSE_SET_INCOMPLETE_MAPPING,
    MAPPING_BASIS_LEGACY_FACET,
    classify_cause_set,
)
from learnloop.diagnosis.causal_reads import (
    CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
    CausalRepairError,
    _avoided_overteaching_minutes,
    _case_repair_class_id,
    _discrimination_inputs,
    _durable_case_factor,
    _probe_burden_minutes,
    _recent_diagnostic_burden,
    _repair_class_by_hypothesis,
    _unmapped_case_obligation,
    diagnosis_receipt,
    open_factors_for_hypothesis,
)
from learnloop.diagnosis.probe_hard_stops import (
    EPISODE_CONFLICT_MESSAGE,
    learner_preference,
    probe_episode_conflict,
)
from learnloop.diagnosis.machine_checks import (
    backfill_obligation,
    enqueue_backfill_obligation,
    close_satisfied_backfills,
    pending_machine_checks_for_factor,
)
from learnloop.vault.models import LoadedVault


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


#: Standing constraint 4: where an EVSI input came from.  ``deterministic`` is a
#: computed fact (blind-bundle separability, a stored learner action, a counted
#: attempt); ``model_reported`` came from authored/model prose;
#: ``authored_prior`` is a human/template-authored constant read verbatim
#: (decision-value spec §4.1: deterministically REPRODUCIBLE is not an
#: epistemic source — a card's ``expected_seconds=45`` is still authored);
#: ``mixed`` means part of one aggregate came from authored/model prose and part
#: from a pinned default; ``heuristic_default`` is a pinned fallback alone.
EVSI_PROVENANCE = (
    "deterministic",
    "model_reported",
    "authored_prior",
    "mixed",
    "heuristic_default",
)

#: The loss regime of the CURRENT live decision rule. The P2 proxy prices a
#: probe against avoided over-teaching minutes; it consumes no L(h,a) table at
#: all, and the receipt must say so rather than imply a learned loss model.
LOSS_TABLE_REGIME_P2_PROXY = "p2_pairwise_proxy_no_loss_table"


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
    #: How much of the answer this repair episode has already handed over
    #: (migration 154's reveal ledger, summed over rows stamped with the
    #: episode), against `remediation.EPISODE_REVEAL_BUDGET`. ``None`` when the
    #: status carries no episode — a status read with ``start_repair=False``
    #: has nothing to have spent yet. Reported, never enforced: no repair is
    #: refused on budget, and a surface that shows it is showing what the
    #: repair has cost the measurement at the end of it.
    reveal_spend: float | None = None
    reveal_budget: float | None = None

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
            "reveal_spend": self.reveal_spend,
            "reveal_budget": self.reveal_budget,
            "decision_policy_version": CAUSAL_DECISION_POLICY_VERSION,
            "formula_version": CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
        }


def _with_reveal_spend(repository: Repository, status: RepairStatus) -> RepairStatus:
    """Stamp the episode's reveal spend and the budget it is measured against.

    One place, applied to every status that carries an episode: the spend is a
    property of the episode, and re-deriving it per construction site is how
    two surfaces end up disagreeing about how much a repair has told the
    learner. A status with no episode reports neither — there is no episode to
    have spent anything.
    """

    if status.episode is None:
        return status
    from learnloop.diagnosis.remediation import (
        EPISODE_REVEAL_BUDGET,
        episode_reveal_spend,
    )

    return replace(
        status,
        reveal_spend=episode_reveal_spend(repository, str(status.episode.get("id") or "")),
        reveal_budget=EPISODE_REVEAL_BUDGET,
    )


# --- the orchestrator --------------------------------------------------------


#: Repair-episode states that have not yet committed to a specific item pair.
#: An episode in one of these is still the SAME repair and is reused; from
#: `treatment` on, the episode owns a primed/cold item pair and a fresh request
#: is a genuinely new repair.
_UNCOMMITTED_REPAIR_STATES = ("diagnosis", "prescribed")


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

    # Atomic get-or-create (StrictMode double-mount hardening): the read and
    # the insert happen inside one repository write transaction, so two racing
    # "start this repair" calls resolve to one episode instead of a duplicate
    # pair whose orphan strands every downstream record.
    return repository.get_or_create_open_remediation_episode(
        case_kind=case_kind,
        case_ref=case_ref,
        states=_UNCOMMITTED_REPAIR_STATES,
        clock=clock,
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
        # ambiguity: there is nothing left to disambiguate.  The decision is
        # still a decision (G12): without a receipt the feedback surface's
        # commonRepair attach (which READS `causal_probe_decision_receipts`,
        # never calls this function) could not show the misconception path at
        # all.  The receipt is keyed on the case's factor when one exists —
        # exactly the row `_attach_common_repair` looks under — and is written
        # for BOTH the read-only consultation (start_repair=False, which mints
        # no episode) and the overlay start (which mints exactly one through
        # the get-or-create below).
        factor = _durable_case_factor(repository, misconception)
        receipt: dict[str, Any] | None = None
        if factor is not None:
            receipt = repository.insert_causal_probe_decision_receipt(
                factor_id=str(factor["id"]),
                decision="start_durable_repair",
                reason="durable_misconception",
                repair_status="started",
                decision_policy_version=CAUSAL_DECISION_POLICY_VERSION,
                formula_version=CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
                inputs={
                    "case_kind": "misconception",
                    "misconception_status": str(misconception.status),
                    "start_repair": bool(start_repair),
                },
                parameters={},
                hypothesis_ids=[],
                learning_object_id=str(misconception.learning_object_id),
                attempt_id=str(factor.get("attempt_id") or "") or None,
                misconception_id=misconception_id,
                clock=clock,
            )
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
        return _with_reveal_spend(
            repository,
            RepairStatus(
                status="started",
                reason="durable_misconception",
                message=STARTED_MESSAGE,
                misconception_id=misconception_id,
                factor_id=str(factor["id"]) if factor is not None else None,
                learning_object_id=str(misconception.learning_object_id),
                decision_receipt_id=(
                    str(receipt["id"]) if receipt is not None else None
                ),
                probe_decision="start_durable_repair" if receipt is not None else None,
                episode=episode,
            ),
        )

    candidate_case = repository.misconception_candidate_by_id(misconception_id)
    if candidate_case is None or candidate_case.get("status") != "candidate":
        raise CausalRepairError(
            "repair requires an active durable misconception or provisional belief"
        )

    factors = open_factors_for_hypothesis(repository, misconception_id)
    if not factors:
        # G14: with no factor there is no cause-set classification, so this
        # arm used to start a measurable diagnosis-kind episode with NO
        # repair-mapping check — a clean primed redo then scheduled a 30-day
        # cold retry whose context carried `repair_class_id=None`, and the
        # measurement could only ever land as `missing_chain`.  Mirror the
        # CAUSE_SET_INCOMPLETE_MAPPING arm instead: publish the typed mapping
        # obligation and defer; the machine buys the missing mapping, not the
        # learner's time.  A legacy candidate with no causal hypothesis at all
        # (pre-P1 vault) keeps the started path — it has no repair-class
        # vocabulary to check, exactly like MAPPING_BASIS_LEGACY_FACET.
        hypothesis = repository.causal_hypothesis(misconception_id)
        if hypothesis is not None and _case_repair_class_id(
            repository, hypothesis
        ) is None:
            check = enqueue_backfill_obligation(
                repository,
                _unmapped_case_obligation(hypothesis),
                learning_object_id=str(hypothesis["learning_object_id"]),
                source="causal_repair_status",
                clock=clock,
            )
            return RepairStatus(
                status="deferred_machine_checks",
                reason="incomplete_repair_mapping",
                message=DEFERRED_MACHINE_CHECKS_MESSAGE,
                misconception_id=misconception_id,
                learning_object_id=str(hypothesis["learning_object_id"]),
                attempt_id=str(hypothesis.get("attempt_id") or "") or None,
                probe_decision="defer_machine_checks",
                probe_decision_reason=(
                    "diagnosis case has no resolvable repair class; a cold "
                    "retry would be unmeasurable (missing_chain)"
                ),
                pending_machine_check_ids=(str(check["id"]),),
            )
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
        return _with_reveal_spend(
            repository,
            RepairStatus(
                status="started",
                reason="no_open_causal_factor",
                message=STARTED_MESSAGE,
                misconception_id=misconception_id,
                episode=episode,
            ),
        )

    factor = factors[0]
    return _status_for_factor(
        repository,
        misconception_id=misconception_id,
        factor=factor,
        session_id=session_id,
        session_budget_minutes=session_budget_minutes,
        start_repair=start_repair,
        vault=vault,
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
    vault: LoadedVault | None = None,
) -> RepairStatus:
    """Map a factor to repair status after machine checks and probe valuation.

    Record the decision, then offer a ready instrument or withhold branch repair.
    """
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
        return _with_reveal_spend(
            repository,
            RepairStatus(
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
                    str(value)
                    for value in (candidate or {}).get("blind_bundle_ids") or []
                ),
                hypothesis_set_id=(
                    str(candidate["hypothesis_set_id"])
                    if candidate is not None
                    else None
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
            ),
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
    receipt = diagnosis_receipt(repository, attempt_id)
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
    episode_conflict = probe_episode_conflict(
        repository, factor_id=factor_id, learning_object_id=learning_object_id
    )

    candidates = order_probe_candidates(
        [
            value
            for value in repository.causal_probe_candidates_for_factor(factor_id)
            if candidate_has_current_blind_input_contract(value)
        ]
    )
    active = [value for value in candidates if value.get("status") == "active"]
    # Only a reviewed-ACTIVE candidate is servable; an unreviewed one still
    # tells us how much information the instrument WOULD carry, which is what
    # the decision receipt should record. The head is THE shared deterministic
    # order (`order_probe_candidates`), the same one `accept_probe_offer`
    # serves from, so the receipt's chosen candidate and the served instrument
    # cannot diverge.
    chosen = active[0] if active else (candidates[0] if candidates else None)
    instrument_available = bool(active)

    discrimination = _discrimination_inputs(chosen, repair_class_by_hypothesis)
    expected_information_gain = discrimination.expected_information_gain
    action_change = discrimination.probability_information_changes_repair

    # Decision-value spec §4.1/§10.1: the receipt states how the prior was
    # formed, whether the likelihood coverage is complete (H_OTHER and any
    # bundle-less hypothesis included), and which loss regime priced the
    # decision — P4 consumes these receipts as training records and must be
    # able to refuse fabricated inputs without re-deriving them.
    prior_basis: str | None = None
    if chosen is not None and chosen.get("hypothesis_set_id"):
        locked_set = repository.fetch_hypothesis_set(str(chosen["hypothesis_set_id"]))
        if locked_set is not None:
            prior_basis = (
                str(locked_set.get("prior_basis")) if locked_set.get("prior_basis") else None
            )
    likelihood_completeness: dict[str, Any]
    if chosen is None:
        likelihood_completeness = {"complete": False, "reason": "no_instrument"}
    else:
        chosen_discrimination = (
            chosen.get("discrimination")
            if isinstance(chosen.get("discrimination"), Mapping)
            else {}
        )
        missing_ids = [
            str(value)
            for value in (chosen_discrimination.get("missing_hypothesis_ids") or [])
        ]
        unusable_ids = [
            str(value)
            for value in (chosen_discrimination.get("unusable_hypothesis_ids") or [])
        ]
        likelihood_completeness = {
            "complete": not missing_ids and not unusable_ids,
            "missing_hypothesis_ids": missing_ids,
            "unusable_hypothesis_ids": unusable_ids,
        }
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
        "prior_basis": prior_basis,
        "likelihood_completeness": likelihood_completeness,
        "loss_table_regime": LOSS_TABLE_REGIME_P2_PROXY,
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




__all__ = [
    "CAUSAL_ORCHESTRATOR_POLICY_DEFAULTS",
    "CAUSAL_ORCHESTRATOR_POLICY_SCOPE",
    "EVSI_PROVENANCE",
    "NEEDS_DISAMBIGUATION_MESSAGE",
    "REPAIR_STATUSES",
    "RepairAction",
    "RepairStatus",
    "causal_repair_status",
    "resolve_orchestrator_parameters",
]
