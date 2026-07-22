"""P2 LEARNING track -- the nine-rung pattern ladder (7 ordinals) + stage transitions
(spec_p2_narrow_golden_path §7.1, §7.2, §12.3; design B.6; migration 084).

The ladder is composed entirely from LANDED P1 substrate -- reviewed
``activity_patterns`` (the admitted pattern registry + its routing metadata via
``activity_patterns.routing_metadata``) and the ``administration_adapters``
(purpose-specific evidence). P2 owns
only the ordering:

- ``select_rung`` picks the NEAREST USEFUL rung from the diagnostic route rather than
  forcing every learner from the bottom (§7.1). A capable learner skips instruction.
  The ladder entry stage is set by the diagnostic track's ``failure_triage`` route,
  which has already advanced the run into the route's ``ladder_entry_stage`` run
  state -- this module consumes that (no parallel routing).
- ``advance_stage`` applies the §7.2 exit contracts. Advancement is driven by
  purpose-appropriate evidence through the P1 adapters: the ``InstructionalAdapter``
  records scaffold use but mints NO unassisted certification and opens NO lapse; the
  ``PracticeAdapter`` requires a cold/unhinted response. Repeated failures on VARIED
  surfaces terminate into ``needs_review`` telemetry, not infinite near-clone practice.

Ladder STATE lives on the run's append-only event stream
(``golden_path_run_events``) -- there is NO parallel ladder state machine (design
B.6). A rung that crosses a run-state boundary is recorded through
``golden_path_run.advance`` (validated adjacency); an intra-state rung is recorded
as a self-loop event carrying the rung in ``selected_activity_json.stage``.
``project_run`` therefore reproduces the ladder position from events alone (§12.6).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from datetime import timedelta

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.services import administration_adapters as AA
from learnloop.services import golden_path_run as GPR
from learnloop.services.activities import _json

LADDER_POLICY_SCHEMA_VERSION = 1  # structural enum; ladder policy spec schema pin.

# decision parameter -- N distinct varied-surface failures on a ladder rung that
# terminate into `needs_review` / P4-expansion telemetry rather than infinite
# near-clone practice (§7.2). Registered heuristic in the P0 registry (design §E).
REPEATED_FAILURE_REVIEW_N = 3

# decision parameter -- the per-stage delayed-check window (days) before delayed
# independent target-like practice is due (§7.2 delay lengths). Registered
# heuristic in the P0 registry (design §E).
STAGE_DELAY_DAYS = 1

# decision parameter -- the scaffold-use fraction at/above which an
# `example_completion` rung is treated as scaffold-heavy (exit records scaffold use;
# never certifies independence, §7.2). Registered heuristic (design §E).
COMPLETION_SCAFFOLD_THRESHOLD = 0.5


class LadderError(Exception):
    """A ladder action references an unknown run / stage."""


@dataclass(frozen=True)
class LadderStage:
    stage_key: str
    ordinal: int
    purpose: str  # 'instructional' | 'practice'
    run_state: str
    pattern_family: str
    mints_certification: bool
    requires_cold: bool
    records_scaffold: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "stage_key": self.stage_key,
            "ordinal": self.ordinal,
            "purpose": self.purpose,
            "run_state": self.run_state,
            "pattern_family": self.pattern_family,
            "mints_certification": self.mints_certification,
            "requires_cold": self.requires_cold,
            "records_scaffold": self.records_scaffold,
        }


# The §7.1 ladder as the authority for ORDERING logic; the identical rows are
# seeded as the reviewable `p2_ladder_stages` DATA table (migration 084). A test
# asserts the two never drift. `mints_certification` is False on EVERY rung.
LADDER_STAGES: tuple[LadderStage, ...] = (
    LadderStage("explanation", 0, "instructional", "instructing", "example_study", False, False, False),
    LadderStage("example_study", 1, "instructional", "instructing", "example_study", False, False, False),
    LadderStage("example_comparison", 1, "instructional", "instructing", "example_comparison", False, False, False),
    LadderStage("example_completion", 2, "instructional", "completing", "example_completion", False, False, True),
    LadderStage("setup_only", 3, "instructional", "instructing", "setup_only", False, False, False),
    LadderStage("move_spotting", 3, "instructional", "instructing", "move_spotting", False, False, False),
    LadderStage("independent_repair", 4, "practice", "practicing", "independent_repair", False, True, False),
    LadderStage("whole_task_integration", 5, "practice", "integrating", "whole_task_integration", False, True, False),
    LadderStage("delayed_independent_practice", 6, "practice", "practicing", "independent_repair", False, True, False),
)
STAGE_BY_KEY: dict[str, LadderStage] = {s.stage_key: s for s in LADDER_STAGES}

# The representative rung at each ordinal (the forward-climb spine; alternates share
# an ordinal but the climb visits the representative next).
_REPRESENTATIVE_BY_ORDINAL: dict[int, LadderStage] = {}
for _s in LADDER_STAGES:
    _REPRESENTATIVE_BY_ORDINAL.setdefault(_s.ordinal, _s)

# §6.2 triage reason -> ladder entry rung (the "nearest useful rung", §7.1). The two
# fault/ambiguous reasons open no instructional rung (they route to needs_review or a
# diagnostic re-open, handled by the triage track).
_REASON_ENTRY_RUNG: dict[str, str] = {
    "memory_lapse": "explanation",
    "unfamiliar_or_missing_knowledge": "explanation",
    "schema_or_conceptual_hole": "example_comparison",
    "false_belief_or_confusion": "explanation",
    "procedure_execution": "example_completion",
    "method_selection": "setup_only",
    "coordination_or_integration": "whole_task_integration",
    "task_interpretation": "example_comparison",
    # surface_or_grading_fault / unknown_or_ambiguous open no rung.
}

# Outcome vocabulary for advance_stage.
_FAIL_OUTCOMES: frozenset[str] = frozenset({"fail", "incorrect", "gave_up"})


def _next_stage(stage: LadderStage) -> LadderStage | None:
    """The next rung on the forward climb (the representative at ordinal+1), or None
    when the ladder is complete (the run is then ready to assess)."""

    return _REPRESENTATIVE_BY_ORDINAL.get(stage.ordinal + 1)


# ---------------------------------------------------------------------------
# Reviewable policy (DATA) readers -- the owner-auditable ladder artifact.
# ---------------------------------------------------------------------------

def active_ladder(repository: Repository, *, policy_slug: str = "ladder_v1") -> dict[str, Any]:
    """The reviewable ladder policy + its ordered stage rows (migration 084 DATA)."""

    policy = repository.active_ladder_policy(policy_slug)
    if policy is None:  # pragma: no cover - seeded at migration time
        raise LadderError(f"no active ladder policy: {policy_slug!r}")
    stages = repository.ladder_stages_for_policy(policy["id"])
    return {"policy": policy, "stages": stages}


# ---------------------------------------------------------------------------
# Rung selection (§7.1) -- nearest useful rung, never always the bottom.
# ---------------------------------------------------------------------------

def select_rung(
    *,
    triage: Mapping[str, Any] | None = None,
    reason: str | None = None,
    demonstrated_capability: bool = False,
) -> LadderStage | None:
    """Pick the nearest useful rung from the diagnostic route (§7.1).

    A capable planted learner (``demonstrated_capability``) skips unnecessary
    instruction straight to ``independent_repair`` (§12.3). Otherwise the triage
    reason maps to its entry rung; the two fault/ambiguous reasons return None (no
    instructional rung -- the triage track handles quarantine / diagnostic re-open).
    """

    if demonstrated_capability:
        return STAGE_BY_KEY["independent_repair"]
    resolved = reason
    if resolved is None and triage is not None:
        resolved = triage.get("reason")
    if resolved is None:
        return None
    key = _REASON_ENTRY_RUNG.get(str(resolved))
    return STAGE_BY_KEY[key] if key is not None else None


# ---------------------------------------------------------------------------
# Purpose-appropriate evidence (§7.2) -- via the P1 administration adapters.
# ---------------------------------------------------------------------------

def stage_evidence_effects(stage_key: str, *, eligible: bool = True, failed: bool = False) -> AA.AdministrationEffects:
    """Resolve the P1 administration adapter for a rung's IMMUTABLE purpose and return
    its evidence effects (§7.2). Instructional rungs mint NO unassisted certification
    and open NO lapse; practice rungs are practice-weighted when eligible -- neither
    mints unassisted certification (that is the assessment purpose's alone)."""

    stage = STAGE_BY_KEY.get(stage_key)
    if stage is None:
        raise LadderError(f"unknown ladder stage: {stage_key!r}")
    adapter = AA.resolve_adapter(stage.purpose)
    return adapter.effects(eligible=eligible, failed=failed)


# ---------------------------------------------------------------------------
# Ladder state on the run event stream (§7.2, §12.6) -- no parallel state.
# ---------------------------------------------------------------------------

def _current_rung_key(events: list[Mapping[str, Any]]) -> str | None:
    import json as _json_mod

    for event in reversed(events):
        raw = event.get("selected_activity_json")
        if not raw:
            continue
        payload = _json_mod.loads(raw)
        if isinstance(payload, Mapping) and payload.get("kind") == "ladder_rung" and payload.get("stage"):
            return str(payload["stage"])
    return None


def _failed_surfaces(events: list[Mapping[str, Any]], *, stage: str | None = None) -> set[str]:
    """Distinct failed surfaces, filtered to ONE rung when ``stage`` is given (§7.2).

    Per-rung counting is the §7.2 semantics: ``REPEATED_FAILURE_REVIEW_N`` distinct
    varied-surface failures ON THE SAME RUNG terminate into ``needs_review``; a single
    fail per rung while climbing does NOT accumulate across rungs into a false review."""

    import json as _json_mod

    out: set[str] = set()
    for event in events:
        raw = event.get("selected_activity_json")
        if not raw:
            continue
        payload = _json_mod.loads(raw)
        if (
            isinstance(payload, Mapping)
            and payload.get("kind") == "ladder_rung"
            and payload.get("outcome") in _FAIL_OUTCOMES
            and payload.get("surface_id")
            and (stage is None or payload.get("stage") == stage)
        ):
            out.add(str(payload["surface_id"]))
    return out


def _record_rung(
    repository: Repository,
    run_id: str,
    stage: LadderStage,
    *,
    reason: str,
    idempotency_key: str,
    outcome: str | None = None,
    surface_id: str | None = None,
    scaffold_use: float | None = None,
    evidence_ids: list[str] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record a rung on the run's event stream (design B.6). When the rung's run
    state differs from the run's current state, record it through the validated
    ``golden_path_run.advance`` (a genuine transition); otherwise append a self-loop
    event carrying the rung -- so ``project_run`` reproduces the ladder from events."""

    state = GPR.project_run(repository, run_id)
    selected = {
        "kind": "ladder_rung",
        "stage": stage.stage_key,
        "purpose": stage.purpose,
        "pattern_family": stage.pattern_family,
        "outcome": outcome,
        "surface_id": surface_id,
        "scaffold_use": scaffold_use,
        "records_scaffold": stage.records_scaffold,
        "mints_certification": stage.mints_certification,
    }
    # §7.2 (L7 wiring) scaffold-heavy completion: an example_completion exit with scaffold
    # use at/above COMPLETION_SCAFFOLD_THRESHOLD is recorded scaffold-heavy -- its success
    # never certifies independence and it always requires later independent work.
    if stage.records_scaffold and scaffold_use is not None:
        selected["scaffold_heavy"] = scaffold_use >= COMPLETION_SCAFFOLD_THRESHOLD
    # §7.2 (L7 wiring) delayed independent practice is due only after the STAGE_DELAY_DAYS
    # window -- the rung carries its computed due_at so the scheduler holds it until then.
    if stage.stage_key == "delayed_independent_practice":
        now_dt = parse_utc(utc_now_iso(clock))
        if now_dt is not None:
            selected["delayed_check_due_at"] = (
                (now_dt + timedelta(days=STAGE_DELAY_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
    if stage.run_state != state.current_state:
        result = GPR.advance(
            repository,
            run_id,
            to_state=stage.run_state,
            reason=reason,
            idempotency_key=idempotency_key,
            evidence_ids=evidence_ids,
            selected_activity=selected,
            clock=clock,
        )
        return {"event_id": result.event_id, "transitioned": not result.already_exists}
    run = repository.golden_path_run(run_id)
    head = repository.fetch_goal_contract_head(run["goal_id"]) if run else None
    gc_head = head["head_version_id"] if head else None
    outcome_row = repository.append_golden_path_run_event(
        run_id=run_id,
        to_state=state.current_state,
        reason=reason,
        idempotency_key=idempotency_key,
        goal_contract_head_version_id=gc_head,
        depth_policy_version_id=run["depth_policy_version_id"] if run else None,
        depth_envelope_version_id=run["depth_envelope_version_id"] if run else None,
        selected_activity_json=_json(selected),
        evidence_ids_json=_json(list(evidence_ids)) if evidence_ids else None,
        clock=clock,
    )
    event = outcome_row["event"]
    return {"event_id": event["id"], "transitioned": not outcome_row.get("already_exists", False)}


@dataclass(frozen=True)
class LadderAdvance:
    run_id: str
    from_stage: str
    to_stage: str | None
    outcome: str
    event_id: str
    needs_review: bool
    ready_to_assess: bool
    repeated_failures: int
    effects: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "from_stage": self.from_stage,
            "to_stage": self.to_stage,
            "outcome": self.outcome,
            "event_id": self.event_id,
            "needs_review": self.needs_review,
            "ready_to_assess": self.ready_to_assess,
            "repeated_failures": self.repeated_failures,
            "effects": self.effects,
        }


def enter_ladder(
    repository: Repository,
    run_id: str,
    *,
    triage: Mapping[str, Any] | None = None,
    reason: str | None = None,
    demonstrated_capability: bool = False,
    idempotency_key: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record the ladder ENTRY rung on the run's event stream (§7.1). The diagnostic
    track has already advanced the run into the route's ``ladder_entry_stage`` run
    state; this pins the fine-grained rung consistent with that state."""

    run = repository.golden_path_run(run_id)
    if run is None:
        raise LadderError(f"unknown golden-path run: {run_id}")
    stage = select_rung(triage=triage, reason=reason, demonstrated_capability=demonstrated_capability)
    if stage is None:
        return {"run_id": run_id, "stage": None, "reason": "no_instructional_rung"}
    key = idempotency_key or f"ladder-enter:{run_id}:{stage.stage_key}"
    recorded = _record_rung(
        repository, run_id, stage, reason=f"ladder_enter:{stage.stage_key}",
        idempotency_key=key, clock=clock,
    )
    return {"run_id": run_id, "stage": stage.stage_key, "event_id": recorded["event_id"]}


def advance_stage(
    repository: Repository,
    run_id: str,
    *,
    from_stage: str,
    outcome: str,
    surface_id: str | None = None,
    scaffold_use: float | None = None,
    eligible: bool = True,
    evidence_ids: list[str] | None = None,
    idempotency_key: str | None = None,
    clock: Clock | None = None,
) -> LadderAdvance:
    """Apply the §7.2 exit contract for a rung.

    On SUCCESS, climb to the next rung (recorded on the run event stream), or -- when
    the ladder is complete -- advance the run to ``ready_to_assess``. On FAILURE, the
    policy may retry another instructional example, but once ``REPEATED_FAILURE_REVIEW_N``
    DISTINCT varied surfaces have failed, the run terminates into ``needs_review``
    telemetry (§7.2) -- never infinite near-clone practice. Evidence is scored through
    the rung's purpose adapter, so an instructional success mints no certification and
    opens no lapse (§12.3).
    """

    stage = STAGE_BY_KEY.get(from_stage)
    if stage is None:
        raise LadderError(f"unknown ladder stage: {from_stage!r}")
    run = repository.golden_path_run(run_id)
    if run is None:
        raise LadderError(f"unknown golden-path run: {run_id}")
    failed = outcome in _FAIL_OUTCOMES
    effects = stage_evidence_effects(from_stage, eligible=eligible, failed=failed).as_dict()
    # §7.2 (L7): surface the scaffold-heavy signal on the completion rung's effects so a
    # caller sees the exit recorded scaffold use and did NOT certify independence.
    if stage.records_scaffold and scaffold_use is not None:
        effects["scaffold_heavy"] = scaffold_use >= COMPLETION_SCAFFOLD_THRESHOLD

    if failed:
        # Record the failure on the event stream, then count DISTINCT varied surfaces.
        key = idempotency_key or f"ladder-fail:{run_id}:{from_stage}:{surface_id or 'na'}"
        recorded = _record_rung(
            repository, run_id, stage, reason=f"ladder_fail:{from_stage}",
            idempotency_key=key, outcome=outcome, surface_id=surface_id,
            scaffold_use=scaffold_use, evidence_ids=evidence_ids, clock=clock,
        )
        distinct = _failed_surfaces(repository.golden_path_run_events_for(run_id), stage=from_stage)
        if len(distinct) >= REPEATED_FAILURE_REVIEW_N:
            state = GPR.project_run(repository, run_id)
            review_event_id = recorded["event_id"]
            if state.current_state != "needs_review":
                advanced = GPR.advance(
                    repository, run_id, to_state="needs_review",
                    reason="repeated_varied_failures", idempotency_key=f"ladder-review:{run_id}",
                    policy_calibration={"repeated_failure_surfaces": sorted(distinct)}, clock=clock,
                )
                review_event_id = advanced.event_id
            return LadderAdvance(
                run_id=run_id, from_stage=from_stage, to_stage=None, outcome=outcome,
                event_id=review_event_id, needs_review=True, ready_to_assess=False,
                repeated_failures=len(distinct), effects=effects,
            )
        return LadderAdvance(
            run_id=run_id, from_stage=from_stage, to_stage=from_stage, outcome=outcome,
            event_id=recorded["event_id"], needs_review=False, ready_to_assess=False,
            repeated_failures=len(distinct), effects=effects,
        )

    # Success: record the rung's EXIT evidence (outcome / surface / scaffold use) on a
    # self-loop event for `from_stage`, so scaffold use is attributed to the completed
    # rung (§7.2), then climb.
    exit_key = f"{idempotency_key}:exit" if idempotency_key else f"ladder-exit:{run_id}:{from_stage}:{surface_id or 'na'}"
    _record_rung(
        repository, run_id, stage, reason=f"ladder_exit:{from_stage}",
        idempotency_key=exit_key, outcome=outcome, surface_id=surface_id,
        scaffold_use=scaffold_use, evidence_ids=evidence_ids, clock=clock,
    )

    nxt = _next_stage(stage)
    if nxt is None:
        state = GPR.project_run(repository, run_id)
        key = f"{idempotency_key}:assess" if idempotency_key else f"ladder-assess:{run_id}"
        if state.current_state == "ready_to_assess":
            head = GPR._existing_event(repository, run_id, key)
            event_id = head["id"] if head else state.head_event_id or ""
        else:
            advanced = GPR.advance(
                repository, run_id, to_state="ready_to_assess",
                reason=f"ladder_complete:{from_stage}", idempotency_key=key,
                evidence_ids=evidence_ids, clock=clock,
            )
            event_id = advanced.event_id
        return LadderAdvance(
            run_id=run_id, from_stage=from_stage, to_stage=None, outcome=outcome,
            event_id=event_id, needs_review=False, ready_to_assess=True,
            repeated_failures=0, effects=effects,
        )

    key = f"{idempotency_key}:entry" if idempotency_key else f"ladder-advance:{run_id}:{from_stage}->{nxt.stage_key}"
    recorded = _record_rung(
        repository, run_id, nxt, reason=f"ladder_advance:{from_stage}->{nxt.stage_key}",
        idempotency_key=key, outcome=outcome, surface_id=surface_id,
        scaffold_use=scaffold_use, evidence_ids=evidence_ids, clock=clock,
    )
    return LadderAdvance(
        run_id=run_id, from_stage=from_stage, to_stage=nxt.stage_key, outcome=outcome,
        event_id=recorded["event_id"], needs_review=False, ready_to_assess=False,
        repeated_failures=0, effects=effects,
    )


def ladder_status(repository: Repository, run_id: str) -> dict[str, Any]:
    """The current ladder rung + climb history projected from the run event stream
    (§12.6 -- reproducible from events alone)."""

    run = repository.golden_path_run(run_id)
    if run is None:
        raise LadderError(f"unknown golden-path run: {run_id}")
    events = repository.golden_path_run_events_for(run_id)
    current = _current_rung_key(events)
    stage = STAGE_BY_KEY.get(current) if current else None
    import json as _json_mod

    history: list[dict[str, Any]] = []
    for event in events:
        raw = event.get("selected_activity_json")
        if not raw:
            continue
        payload = _json_mod.loads(raw)
        if isinstance(payload, Mapping) and payload.get("kind") == "ladder_rung":
            history.append(
                {
                    "seq": event["seq"],
                    "stage": payload.get("stage"),
                    "outcome": payload.get("outcome"),
                    "run_state": event["to_state"],
                }
            )
    return {
        "run_id": run_id,
        "current_state": run["current_state"],
        "current_stage": current,
        "stage": stage.as_dict() if stage else None,
        "history": history,
    }
