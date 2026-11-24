"""The probe router's learner lane: what the router reads about one factor's quick check, as plain values.

At the probe router's tag the repair status is a read of facts (``causal_orchestrator._routed``). When a reviewed,
executable instrument exists and no hard stop keeps it out, the status carries a :class:`Proposal`; the router
(``daily_plan.learner_probe``) prices it with the existing instrument's channel (:func:`diagnostic_payload`) and decides
once per factor. Nothing here judges whether the probe is worth asking: it reads the locked hypothesis set, the
instrument's composed ``P(outcome | hypothesis)`` through the same slot mapping the episode's own valuation reads
(``probe_families.instrument_conditionals``, ``voi_stopping.label_conditionals``), each hypothesis's cause class and
the repair each needs. A hypothesis whose row the instrument cannot give makes the channel missing, never a row filled
in here.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Any

from learnloop.diagnosis.probe_facts import ProbeProposalReads
from learnloop.router_objective import diagnostic_payload as DP
from learnloop.router_objective import types as OT
from learnloop.router_objective.miss_cause import CLASSES

#: The channel's record: where its rows came from.
CHANNEL_SOURCE = "instrument_conditionals"
#: The probe action's ref in the router's valuation.
PROBE_ACTION_REF = "probe"


@dataclass(frozen=True)
class Proposal:
    """One factor's possible quick check as the status read it (``causal_orchestrator._routed``)."""

    factor_id: str
    misconception_id: str
    learning_object_id: str | None
    attempt_id: str | None
    session_id: str | None
    repair_class_by_hypothesis: Mapping[str, str]
    hypothesis_ids: tuple[str, ...]
    #: The orchestrator's per-repair-class minutes (``repair_class_expected_minutes_default``), each repair's duration.
    repair_minutes: float
    reads: ProbeProposalReads
    #: The candidate the offer would serve (the shared serving order's head).
    chosen: Mapping[str, Any] = field(default_factory=dict)

    @property
    def practice_item_id(self) -> str | None:
        value = self.chosen.get("practice_item_id")
        return str(value) if value else None

    def facts(self) -> dict[str, Any]:
        """The repair lane's facts, as plain values: for the record and the card, never priced."""

        return {key: (list(value) if isinstance(value, tuple) else value)
                for key, value in asdict(self.reads.facts()).items()}


def _cause_class(repository: Any, hypothesis_id: str) -> str:
    row = repository.causal_hypothesis(hypothesis_id)
    scope = str((row or {}).get("cause_scope") or "")
    return scope if scope in CLASSES else DP.UNKNOWN


def _channel(vault: Any, repository: Any, item: Any, hypothesis_set: Any, labels: list[str]) -> DP.Channel | DP.MissingChannel:
    from learnloop.diagnosis.probe_episodes import resolve_instrument
    from learnloop.diagnosis.probe_families import instrument_conditionals
    from learnloop.diagnosis.voi_stopping import label_conditionals

    resolved = resolve_instrument(vault, repository, item, hypothesis_set)
    if resolved is None:
        return DP.MissingChannel("no_instrument_binding")
    instrument, slot_map = resolved
    rows = label_conditionals(instrument_conditionals(instrument), slot_map, labels)
    if any(label not in rows for label in labels):
        return DP.MissingChannel("hypothesis_without_row")
    results = tuple(dict.fromkeys(str(outcome) for label in labels for outcome in rows[label]))
    table = []
    for label in labels:
        row = {str(outcome): float(p) for outcome, p in rows[label].items()}
        total = sum(row.values())
        if total <= 0.0:
            return DP.MissingChannel("row_without_mass")
        # The composed rows are distributions up to float rounding; dividing by the sum keeps them so exactly.
        table.append((label, tuple(row.get(result, 0.0) / total for result in results)))
    version = ":".join(str(part) for part in (instrument.card_id, instrument.card_version,
                                              instrument.family_template_id, instrument.family_template_version,
                                              instrument.compiled_likelihood_hash()))
    return DP.Channel(results=results, rows=tuple(table), version=version,
                      source=f"{CHANNEL_SOURCE}:{instrument.provenance}")


def diagnostic_payload(vault: Any, repository: Any, proposal: Proposal) -> DP.DiagnosticProbe | str:
    """The probe's diagnostic payload, or why none can be built (a string): the locked set's hypotheses at its prior,
    each with its cause class; the instrument's channel or its typed absence; one repair option per repair class,
    covering the hypotheses mapped to it. The repairs' and the probe's durations are set by the router, which reads
    the vault's duration spread."""

    from learnloop.diagnosis.probes import HypothesisSet

    chosen = proposal.chosen
    lo = proposal.learning_object_id
    if not lo or not chosen.get("hypothesis_set_id") or not proposal.practice_item_id:
        return "no_locked_set_or_item"
    record = repository.fetch_hypothesis_set(str(chosen["hypothesis_set_id"]))
    if record is None:
        return "locked_set_missing"
    hypothesis_set = HypothesisSet.from_record(record)
    item = vault.practice_items.get(proposal.practice_item_id)
    if item is None:
        return "probe_item_missing_from_vault"
    labels = [str(h.label) for h in hypothesis_set.hypotheses]
    prior = {str(key): float(value) for key, value in hypothesis_set.prior.items()}
    hypotheses = tuple(DP.Hypothesis(label, max(prior.get(label, 0.0), 0.0), _cause_class(repository, label))
                       for label in labels)
    if sum(h.prior for h in hypotheses) <= 0.0:
        return "locked_prior_without_mass"
    classes = sorted({str(value) for value in proposal.repair_class_by_hypothesis.values() if value})
    repairs = []
    for repair_class in classes:
        covers = frozenset(h for h, value in proposal.repair_class_by_hypothesis.items()
                           if value == repair_class and h in labels)
        if not covers:
            continue
        action = OT.Action(ref=repair_class, kind=OT.REPAIR, item_los=(lo,), minutes=float(proposal.repair_minutes))
        repairs.append(DP.RepairOption(repair_class, action, covers, source="cause_set_repair_class"))
    return DP.DiagnosticProbe(
        topic=lo,
        hypotheses=hypotheses,
        prior_basis=proposal.reads.prior_basis or "locked_set_prior",
        channel=_channel(vault, repository, item, hypothesis_set, labels),
        repairs=tuple(repairs),
        source=(("attempt", str(proposal.attempt_id or "")), ("factor", proposal.factor_id),
                ("candidate", str(chosen.get("id") or "")), ("item", proposal.practice_item_id),
                ("origin", "learner_lane")),
        facts=tuple(sorted(proposal.facts().items())),
    )


__all__ = ["CHANNEL_SOURCE", "PROBE_ACTION_REF", "Proposal", "diagnostic_payload"]
