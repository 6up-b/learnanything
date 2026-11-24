"""The probe router's learner lane: what the router reads about one factor's quick check, as plain values.

At the probe router's tag the repair status is a read of facts (``causal_orchestrator._routed``). When a reviewed,
executable instrument exists and no hard stop keeps it out, the status carries a :class:`Proposal`; the router
(``daily_plan.learner_probe``) builds the probe's payload from it with the existing instrument's channel
(``learner_probe.diagnostic_payload``), prices it and decides once per factor. Plain values only: this module reads
nothing, so the status that carries it imports nothing of the router's.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Any

from learnloop.diagnosis.probe_facts import ProbeProposalReads

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


__all__ = ["CHANNEL_SOURCE", "PROBE_ACTION_REF", "Proposal"]
