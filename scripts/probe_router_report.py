"""The report the owner reads before G2's behaviour step: for each recorded post-miss probe decision, the
predecessor's answer beside the successor evaluator's, with what could be computed and what could not
(``docs/reviews/refactor-g2-design.md`` §5; G2 step 5). Read-only, and it prints aggregates only: counts, rates and
timings, never an id or a learner's text.

**Two sources.**

- ``--vault DIR_OR_DATABASE`` (repeatable): a backup-API copy of a vault (never a live one). Every recorded decision
  opportunity: the automatic lane's post-miss Next (one ``followup_gate`` decision record per workflow, retries
  counted apart), the learner lane's causal gate (one ``causal_probe_decision_receipts`` row per status read or repair
  request: a remounted panel is a second verdict), and the practice lane's general follow-up value decisions
  (``followup_value_decisions``). The database is opened read-only (``mode=ro``, ``immutable=1`` on a WAL database
  with no ``-wal``: ``vault_report``'s rule); nothing is written. Only the decision's own row is read, and a row of
  another table only when stamped at or before the decision.
- ``--synthetic``: controlled journeys with complete snapshots (the frozen inputs, the payload, the predecessor's
  facts), each valued by the predecessor's gate, the predecessor's rollouts (the probe kind's binary-ability value)
  and the successor evaluator, with the evaluator's cost.

**Coverage classes** (per input the successor's payload needs, and per answer): ``exact`` (stored with the decision,
or fixed by how the decision is made: an automatic-lane probe is decided before it is written, so its channel is
missing by construction), ``as_of`` (read from a row stamped at or before the decision), ``missing`` (not stored, or
stored only after the decision; never filled in), ``synthetic`` (a controlled snapshot). The successor's numeric
choice needs the frozen objective inputs, which no vault stores today, so on a vault it is ``not computable`` and
only what recorded facts fix is reported (a hard stop, or no information credit). Zero differences out of zero
computable cases are reported as zero computable, not as agreement.

The owner's open decisions are the design's recommendations (``diagnostic_payload.DESIGN_RECOMMENDATIONS``), each
pending; the report says so.

    uv run python scripts/probe_router_report.py --synthetic [--json]
    uv run python scripts/probe_router_report.py --vault ~/learnloop-copies/arxiv_v2 [--json]   # copies only
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
import importlib.util
import json
import sqlite3
import statistics
import sys
import time
from pathlib import Path
from typing import Any

try:
    from learnloop.router_objective import diagnostic_payload as DP
except ModuleNotFoundError:  # run with a bare interpreter from a checkout: the package is under src/
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from learnloop.router_objective import diagnostic_payload as DP
from learnloop.diagnosis.causal_probe_coherence import CAUSAL_PROBE_POLICY_DEFAULTS
from learnloop.diagnosis.probe_facts import probe_facts, probe_verdict
from learnloop.router_objective import diagnostic_value as DV
from learnloop.router_objective import rollouts as ROL
from learnloop.router_objective import types as OT
from learnloop.router_objective.objective import numeric_choice
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS

DECISIONS = DP.DESIGN_RECOMMENDATIONS
AUTOMATIC, LEARNER, PRACTICE = "automatic", "learner", "practice"
EXACT, AS_OF, MISSING, SYNTHETIC, NOT_COMPUTABLE = "exact", "as_of", "missing", "synthetic", "not_computable"

#: The causal gate's verdicts that are hard stops in the successor too (design §2a): the learner's refusal, machine
#: checks, an explicit session budget, an unexecutable contract.
LEARNER_HARD_STOPS = {"defer_machine_checks": "machine_checks", "defer_learner_preference": "learner_preference",
                      "defer_session_budget": "session_budget"}
#: Which predecessor authority answered, for a verdict the successor removes (design §2c).
REMOVED_AUTHORITY = {
    "probe_now": "the gate's offer (the router decides instead)",
    "defer_recent_burden": "recent diagnostic limit (no admission rule after G2)",
    "skip_no_discrimination": "minimum information threshold",
    "skip_no_action_change": "minimum action-change threshold",
    "skip_burden_exceeds_value": "avoided-teaching proxy against burden",
}
SETTLED_BY_CLASSES = {"skip_common_repair", "skip_action_equivalent"}


def _vault_report():
    spec = importlib.util.spec_from_file_location("vault_report", Path(__file__).resolve().parent / "vault_report.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _loads(raw: Any, default: Any) -> Any:
    if raw is None or raw == "":
        return default
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return default


def _database(path: Path) -> Path:
    if path.is_dir():
        toml = path / "learnloop.toml"
        if toml.is_file():
            import tomllib

            data = tomllib.loads(toml.read_text(encoding="utf-8"))
            storage = data.get("storage") if isinstance(data.get("storage"), Mapping) else {}
            name = Path(str(storage.get("sqlite_path") or "state.sqlite"))
            return name if name.is_absolute() else path / name
        return path / "state.sqlite"
    return path


def open_read_only(path: Path) -> sqlite3.Connection:
    """The vault's database, read-only, leaving nothing beside it (``vault_report``'s URI rule)."""

    database = _database(path)
    uri = _vault_report()._read_only_uri(database)
    if uri is None:
        raise RuntimeError("a -wal without its -shm: not read (open the copy in the app once, then rerun)")
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _has(connection: sqlite3.Connection, table: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                              (table,)).fetchone() is not None


def _at_or_before(stamp: Any, decision_at: Any) -> bool:
    """Whether a row stamped ``stamp`` existed at a decision stamped ``decision_at``. Stamps are UTC ISO strings;
    one stamped in the decision's own second counts as available (the store keeps no finer order across tables)."""

    from datetime import datetime

    def parse(value: Any) -> datetime | None:
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None

    a, b = parse(stamp), parse(decision_at)
    return a is not None and b is not None and a <= b


# -- the vault's opportunities ----------------------------------------------------------------------------------------


def _automatic(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """The automatic lane: one opportunity per workflow's first gate record; a retry is counted, not re-judged.

    The successor's inputs, from the record alone: the hard stop (a refusal), whether the repair classes settle the
    question (the logged value check), and the channel, missing by construction because the probe is written after
    this decision. The locked set is written at authoring, after the decision, so it is ``missing`` and not read."""

    if not _has(connection, "decision_records"):
        return []
    out: list[dict[str, Any]] = []
    retries: Counter[str] = Counter()
    firsts: list[tuple[str, sqlite3.Row, dict[str, Any]]] = []
    for row in connection.execute(
            "SELECT status, chosen_ref, decided_by, rule, facts_json FROM decision_records "
            "WHERE kind = 'followup_gate' ORDER BY created_at, rowid"):
        facts = _loads(row["facts_json"], {})
        workflow = str(facts.get("workflow_id") or "")
        if facts.get("retry"):
            retries[workflow] += 1
        else:
            firsts.append((workflow, row, facts))
    for workflow, row, facts in firsts:
        refused = row["status"] == "refused"
        chosen = str(row["chosen_ref"] or "")
        if refused:
            answer = "refused"
        elif chosen == "insert_now":
            answer = "ask_now"
        elif chosen == "continue_current":
            answer = "wait"
        elif chosen == "no_intervention":
            answer = "none"
        elif chosen.startswith(OT.LESSON_OFFER_PREFIX):
            answer = "lesson"
        else:
            answer = "other"
        decided_by = str(row["decided_by"] or "")
        rule = str(row["rule"] or "")
        check = facts.get("value_check")
        if refused:
            information, authority = "excluded_hard_stop", "hard stop (stays)"
        elif check in SETTLED_BY_CLASSES:
            information, authority = "none_one_repair", _automatic_authority(decided_by, rule)
        else:
            information, authority = "none_missing_channel", _automatic_authority(decided_by, rule)
        out.append({
            "lane": AUTOMATIC, "predecessor": answer, "predecessor_asks": answer == "ask_now",
            "predecessor_rule": decided_by if decided_by in {"no_plan", "no_room_to_wait"} else (
                "drawn" if rule.startswith("drawn_") or decided_by == "mixture" else (
                    "refused" if refused else decided_by or "unknown")),
            "authority": authority, "information": information,
            "inputs": {"hard_stops": EXACT, "repair_classes": EXACT if check or facts.get("value_check_absent")
                       else MISSING, "channel": EXACT, "locked_set": MISSING, "exposure": EXACT,
                       "wait_feasible": EXACT if "wait_feasible" in facts else MISSING, "frozen_inputs": MISSING},
            "wait_feasible": facts.get("wait_feasible"),
            "successor_numeric": NOT_COMPUTABLE,
            "retries": retries[workflow],
        })
    return out


def _automatic_authority(decided_by: str, rule: str) -> str:
    if decided_by == "no_plan":
        return "no plan: asked now with no draw (the router decides after G2)"
    if decided_by == "no_room_to_wait":
        return "no room to wait forces the probe (owner decision 3)"
    if rule.startswith("drawn_") or decided_by == "mixture":
        return "the router's draw (stays; its numeric component gains the payload)"
    return f"other: {decided_by or rule or 'unknown'}"


def _learner(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """The learner lane: every causal gate receipt (each status read and repair request writes one).

    The receipt holds its inputs as the verdict read them (``exact``); the locked set's prior is read from its
    hypothesis set only when that row is stamped at or before the receipt (``as_of``); the repair per hypothesis is not
    kept (only the distinct classes), and the instrument's ``P(result | h)`` is not stored (blind-bundle separation is
    not a likelihood), so both are ``missing``."""

    if not _has(connection, "causal_probe_decision_receipts"):
        return []
    out: list[dict[str, Any]] = []
    factors: Counter[str] = Counter()
    rows = connection.execute(
        "SELECT factor_id, decision, inputs_json, hypothesis_ids_json, candidate_id, created_at "
        "FROM causal_probe_decision_receipts ORDER BY created_at, rowid").fetchall()
    for row in rows:
        factors[str(row["factor_id"])] += 1
        inputs = _loads(row["inputs_json"], {})
        decision = str(row["decision"])
        instrument = bool(inputs.get("instrument_available"))
        if decision in LEARNER_HARD_STOPS or inputs.get("probe_episode_conflict"):
            information, authority = "excluded_hard_stop", "hard stop (stays)"
        elif decision == "skip_no_discrimination" and not instrument:
            information, authority = "excluded_hard_stop", "no executable instrument (stays as a hard stop)"
        elif decision in SETTLED_BY_CLASSES:
            information, authority = "none_one_repair", _gate_authority(decision)
        else:
            information, authority = "not_computable_channel", _gate_authority(decision)
        prior = _prior_as_of(connection, row["candidate_id"], row["created_at"])
        out.append({
            "lane": LEARNER, "predecessor": decision, "predecessor_asks": decision == "probe_now",
            "predecessor_rule": decision, "authority": authority, "information": information,
            "inputs": {"hard_stops": EXACT, "repair_classes": EXACT, "channel": MISSING, "locked_set": EXACT,
                       "prior": prior, "repair_per_hypothesis": MISSING, "exposure": MISSING,
                       "frozen_inputs": MISSING},
            "hypotheses": len(_loads(row["hypothesis_ids_json"], [])),
            "successor_numeric": NOT_COMPUTABLE,
            "factor": str(row["factor_id"]),
        })
    for entry in out:
        # The factor's receipt count replaces its id, which no output carries.
        entry["factor_receipts"] = factors[entry.pop("factor")]
    return out


def _prior_as_of(connection: sqlite3.Connection, candidate_id: Any, decision_at: Any) -> str:
    if not candidate_id or not _has(connection, "causal_probe_candidates") or not _has(connection, "hypothesis_sets"):
        return MISSING
    row = connection.execute(
        "SELECT h.created_at FROM causal_probe_candidates c JOIN hypothesis_sets h ON h.id = c.hypothesis_set_id "
        "WHERE c.id = ?", (candidate_id,)).fetchone()
    if row is None:
        return MISSING
    return AS_OF if _at_or_before(row["created_at"], decision_at) else MISSING


def _practice(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """The practice lane's general follow-up value decisions: no locked rivals, so no probe candidate is gathered for
    them before the behaviour step; counted with their outcome only."""

    if not _has(connection, "followup_value_decisions"):
        return []
    return [{"lane": PRACTICE, "predecessor": str(row["decision_outcome"]),
             "predecessor_asks": str(row["decision_outcome"]) == "queued_diagnostic",
             "predecessor_rule": "manual_override" if row["manual_override"] else str(row["verdict"] or "none"),
             "authority": "general follow-up value (probe-intent suppression moves at the behaviour step)",
             "information": "not_computable_no_payload", "inputs": {"frozen_inputs": MISSING},
             "successor_numeric": NOT_COMPUTABLE}
            for row in connection.execute("SELECT decision_outcome, verdict, manual_override "
                                          "FROM followup_value_decisions ORDER BY created_at, rowid")]


def vault_opportunities(path: Path) -> list[dict[str, Any]]:
    connection = open_read_only(path)
    try:
        return [*_automatic(connection), *_learner(connection), *_practice(connection)]
    finally:
        connection.close()


# -- the synthetic journeys -------------------------------------------------------------------------------------------


def _inputs(*, gap_mean: float | None = None) -> OT.Inputs:
    """Seven topics, as many as the recorded journeys G1 timed: the missed one (``lo_0``) and six others, two dated
    uses. ``gap_mean`` None: ``γ_gap``'s seeded prior (``γ``'s), the state of every vault today; a number: an
    illustrative learned ``γ_gap``, labelled as such wherever it is reported."""

    gamma = (0.2, 0.01)
    topics = tuple(OT.Topic(f"lo_{i}", -0.6 + 0.25 * i, 0.3, practiced=i % 3 != 2, stability=3.0 + i,
                            elapsed_days=1.0 + i % 4, undated_density=1.0 if i == 0 else 0.3 + 0.1 * (i % 3))
                   for i in range(7))
    split = OT.CauseSplit(gap=(gamma[0] if gap_mean is None else gap_mean, gamma[1]), slip=(0.0, gamma[1]))
    return OT.Inputs(topics=topics, dated=(OT.DatedUse("g1", "lo_0", 9.0, 1.0), OT.DatedUse("g1", "lo_3", 9.0, 0.5)),
                     session_minutes=5.0, price=OT.Price(kappa0=0.05, remembered=30.0), tail_block_minutes=10.0,
                     tail_block_items=2, horizon_days=14.0, fsrs_weights=tuple(FSRS6_DEFAULT_WEIGHTS),
                     learning=OT.Learning(gamma=gamma, causes=split))


@dataclass(frozen=True)
class Case:
    """One controlled journey: the lane and the predecessor's path, the payload's shape and the inputs' variant."""

    name: str
    lane: str
    hypotheses: int = 3
    channel: str = "informative"
    repairs: str = "different"
    exposed: bool = False
    hard_stop: str | None = None
    wait_feasible: bool = True
    path: str = "plan"
    slip: bool = False
    gap_mean: float | None = None
    recent: int = 0
    offer: bool = False


def synthetic_cases() -> tuple[Case, ...]:
    """Every case the behaviour step's journeys must cover that the evaluator can see (design §4), on both lanes."""

    cases: list[Case] = []
    for channel in ("missing", "flat", "informative", "perfect"):
        for repairs in ("different", "common"):
            for h in (2, 3, 6):
                cases.append(Case(f"{channel}/{repairs}/H{h}", AUTOMATIC if channel == "missing" else LEARNER,
                                  hypotheses=h, channel=channel, repairs=repairs))
    for channel in ("informative", "perfect"):
        for h in (3, 6):
            cases.append(Case(f"{channel}/different/H{h}/learned_gap", LEARNER, hypotheses=h, channel=channel,
                              gap_mean=0.6))
    cases += [
        Case("missing/different/H4", AUTOMATIC, hypotheses=4, channel="missing"),
        Case("informative/different/H4", LEARNER, hypotheses=4),
        Case("informative/gap_and_slip/H3", LEARNER, slip=True),
        Case("informative/gap_and_slip/H3/learned_gap", LEARNER, slip=True, gap_mean=0.6),
        Case("informative/exposed/H3", LEARNER, exposed=True),
        Case("perfect/exposed/H3/learned_gap", LEARNER, channel="perfect", exposed=True, gap_mean=0.6),
        Case("not_now/H3", LEARNER, hard_stop="learner_preference"),
        Case("machine_check/H3", AUTOMATIC, channel="missing", hard_stop="machine_checks"),
        Case("foreign_episode/H3", LEARNER, hard_stop="episode_conflict"),
        Case("no_plan/missing/H3", AUTOMATIC, channel="missing", path="no_plan"),
        Case("no_room/missing/H3", AUTOMATIC, channel="missing", wait_feasible=False, path="no_room"),
        Case("recent_burden/perfect/H3/learned_gap", LEARNER, channel="perfect", recent=2, gap_mean=0.6),
        Case("lesson_declined/perfect/H3/learned_gap", AUTOMATIC, channel="perfect", offer=True, gap_mean=0.6),
    ]
    return tuple(cases)


def _payload(case: Case) -> DP.DiagnosticProbe:
    named = case.hypotheses - 1
    classes = [DP.SLIP if case.slip and i == 1 else DP.GAP for i in range(named)]
    hypotheses = tuple(DP.Hypothesis(f"h{i}", 0.9 / named, classes[i]) for i in range(named)) + (
        DP.Hypothesis(DP.OPEN_HYPOTHESIS, 0.1, DP.UNKNOWN),)
    ids = [h.id for h in hypotheses]
    repair = OT.Action(ref="repair", kind=OT.REPAIR, item_los=("lo_0", "lo_0"), minutes=6.0, minutes_log_sd=0.3)
    if case.repairs == "common":
        repairs = (DP.RepairOption("r_common", replace(repair, ref="r_common"), frozenset(ids[:named]), "synthetic"),)
    else:
        repairs = tuple(DP.RepairOption(f"r{i}", replace(repair, ref=f"r{i}"), frozenset({f"h{i}"}), "synthetic")
                        for i in range(named))
    results = tuple(f"points_to_{h}" for h in ids)
    channel: DP.Channel | DP.MissingChannel
    if case.channel == "missing":
        channel = DP.MissingChannel("unauthored")
    elif case.channel == "flat":
        channel = DP.Channel(results, tuple((h, tuple(1.0 / len(ids) for _ in ids)) for h in ids), "synthetic", "flat")
    else:
        hit = 1.0 if case.channel == "perfect" else 0.7
        rows = tuple((h, tuple(hit if i == j else (1.0 - hit) / (len(ids) - 1) for j in range(len(ids))))
                     for i, h in enumerate(ids))
        channel = DP.Channel(results, rows, "synthetic", case.channel)
    stops = {"learner_preference": ("learner_preference",), "machine_checks": ("machine_checks",),
             "episode_conflict": ("episode_conflict",)}.get(case.hard_stop or "", ())
    return DP.DiagnosticProbe(topic="lo_0", hypotheses=hypotheses, prior_basis="synthetic", channel=channel,
                              repairs=repairs, exposed=case.exposed, hard_stops=stops)


class _Thresholds:
    """The causal gate's thresholds at their pinned defaults (no fitted scope exists: G1 §2)."""

    recent_diagnostic_limit = int(CAUSAL_PROBE_POLICY_DEFAULTS["recent_diagnostic_limit"])

    def __getitem__(self, key: str) -> float:
        return float(CAUSAL_PROBE_POLICY_DEFAULTS[key])


def _gate(case: Case, payload: DP.DiagnosticProbe) -> str:
    """The predecessor's causal gate on the case's facts: the repair classes, the separability share (the share of
    hypothesis pairs whose rows differ, as blind bundles would separate them), the change share, the orchestrator's
    default 8 minutes per repair class and the probe's burden."""

    named = [h for h in payload.hypotheses if h.id != DP.OPEN_HYPOTHESIS]
    classes = [next((o.ref for o in payload.repairs if h.id in o.covers), None) for h in named]
    pairs = [(a, b) for i, a in enumerate(named) for b in named[i + 1:]]
    separable = [(a, b) for a, b in pairs if isinstance(payload.channel, DP.Channel)
                 and payload.channel.row(a.id) != payload.channel.row(b.id)]
    changes = [(a, b) for a, b in separable if classes[named.index(a)] != classes[named.index(b)]]
    facts = probe_facts(
        repair_class_ids=classes, common_repair_covers=case.repairs == "common",
        expected_information_gain=len(separable) / len(pairs) if pairs else 0.0,
        probability_information_changes_repair=len(changes) / len(separable) if separable else 0.0,
        probe_burden_minutes=3.0, avoided_overteaching_minutes=8.0,
        pending_machine_checks=("check",) if case.hard_stop == "machine_checks" else (),
        learner_preference="decline" if case.hard_stop == "learner_preference" else "allow",
        recent_diagnostic_burden=case.recent)
    verb, _reason = probe_verdict(facts, _Thresholds())
    if case.hard_stop == "episode_conflict" and verb == "probe_now":
        return "blocked_episode_conflict"
    return verb


def _gate_authority(gate: str) -> str:
    if gate in LEARNER_HARD_STOPS or gate == "blocked_episode_conflict":
        return "hard stop (stays)"
    if gate in SETTLED_BY_CLASSES:
        return "repair classes settle it (the successor agrees: no information)"
    return REMOVED_AUTHORITY.get(gate, f"other: {gate}")


def _automatic_answer(case: Case) -> str:
    if case.hard_stop:
        return "refused"
    return {"no_plan": "ask_now (no plan)", "no_room": "ask_now (no room to wait)"}.get(case.path, "router draw")


def _predecessor_numeric(inputs: OT.Inputs, payload: DP.DiagnosticProbe, draws: int, seed: str
                         ) -> tuple[bool, float]:
    """The predecessor's rollouts on the same candidates: the probe kind (one binary-ability result, the first repair
    as its repair branch) against no repair and each repair now; whether ``π_Q`` picks the probe, and the probe's
    own valuation time (ms, warm)."""

    first = payload.repairs[0].action
    probe = OT.Action(ref="probe", kind=OT.PROBE, item_los=("lo_0",), minutes=3.0, minutes_log_sd=0.3, repair=first)
    now = [OT.Action(ref=f"now:{o.ref}", kind=OT.REPAIR, item_los=o.action.item_los, minutes=o.action.minutes,
                     minutes_log_sd=o.action.minutes_log_sd) for o in payload.repairs]
    none = OT.Action(ref="now:none", kind=OT.READING, item_los=(), minutes=0.0)
    evaluation = ROL.evaluate(inputs, [none, *now, probe], draws=draws, seed=seed)
    choice, _rule = numeric_choice(evaluation, [none.ref, *(a.ref for a in now), probe.ref])
    model = ROL._Model(inputs, draws, seed)
    model.value(probe)
    started = time.perf_counter()
    model.value(probe)
    return choice == probe.ref, (time.perf_counter() - started) * 1000.0


def synthetic_opportunities(*, draws: int = 8, cases: Sequence[Case] | None = None) -> list[dict[str, Any]]:
    out = []
    for case in cases if cases is not None else synthetic_cases():
        inputs = _inputs(gap_mean=case.gap_mean)
        payload = _payload(case)
        probe = OT.Action(ref="probe", kind=OT.PROBE, item_los=("lo_0",), minutes=3.0, minutes_log_sd=0.3,
                          diagnostic=payload)
        action = (OT.Action(ref="lesson", kind=OT.LESSON, item_los=("lo_0",), minutes=8.0, mass=0.5,
                            accept=(2.0, 2.0), declined=probe) if case.offer else probe)
        seed = f"g2b-report:{case.name}"
        DV.evaluate_probe(inputs, action, decisions=DECISIONS, draws=draws, seed=seed,
                          wait_feasible=case.wait_feasible)  # warm
        valuation = DV.evaluate_probe(inputs, action, decisions=DECISIONS, draws=draws, seed=seed,
                                      wait_feasible=case.wait_feasible)
        record = valuation.record
        values = record["values"]
        gate = _gate(case, payload)
        numeric_asks, predecessor_ms = _predecessor_numeric(inputs, payload, draws, seed)
        # An offer's row is the lesson; the probe after its "Not now" is not asked now.
        successor_asks = valuation.choice == action.ref and not case.offer
        if "probe" in record["excluded"]:
            information = "excluded_hard_stop"
        elif record["channel_use"] != "channel":
            information = "none_" + record["channel_use"].split(":")[0]
        else:
            information = "positive" if values["information"] > 0.0 else "zero"
        out.append({
            "lane": case.lane, "case": case.name, "illustrative": case.gap_mean is not None,
            "predecessor": gate if case.lane == LEARNER else _automatic_answer(case),
            "predecessor_gate": gate, "predecessor_gate_asks": gate == "probe_now",
            # The automatic lane on a plan is a draw: its final answer is unknown here (its numeric component's is
            # the column beside it).
            "predecessor_asks": (gate == "probe_now") if case.lane == LEARNER else (
                None if not case.hard_stop and case.path == "plan" else (not case.hard_stop)),
            "predecessor_numeric_asks": numeric_asks,
            "successor_asks": successor_asks, "successor_choice": _kind(valuation.choice, action.ref, case.offer),
            "information": information, "information_value": values.get("information"),
            "policy_changes_with_result": record.get("policy_changes_with_result"),
            "authority": _gate_authority(gate) if case.lane == LEARNER else (
                "hard stop (stays)" if case.hard_stop else _automatic_authority(
                    {"no_plan": "no_plan", "no_room": "no_room_to_wait"}.get(case.path, ""), "drawn_numeric")),
            "inputs": {name: SYNTHETIC for name in ("hard_stops", "channel", "locked_set", "repair_per_hypothesis",
                                                    "exposure", "frozen_inputs")},
            "successor_numeric": SYNTHETIC,
            "cost": {**record["cost"], "predecessor_probe_ms": predecessor_ms},
        })
    return out


def _kind(choice: str | None, candidate: str, offer: bool) -> str:
    if choice is None:
        return "none"
    if choice == candidate:
        return "lesson_offer" if offer else "probe"
    return "act_now_" + ("none" if choice == f"{DV.ACT_NOW}{DV.NONE}" else "repair")


# -- aggregates -------------------------------------------------------------------------------------------------------


def _quantiles(values: Iterable[float]) -> dict[str, float] | None:
    data = sorted(values)
    if not data:
        return None
    p95 = data[min(len(data) - 1, int(round(0.95 * (len(data) - 1))))]
    return {"n": len(data), "median": round(statistics.median(data), 1), "p95": round(p95, 1),
            "max": round(data[-1], 1)}


def aggregate(opportunities: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Counts, rates and timings by lane: never an id or a text."""

    lanes: dict[str, Any] = {}
    for lane in (AUTOMATIC, LEARNER, PRACTICE):
        rows = [o for o in opportunities if o["lane"] == lane]
        if not rows:
            continue
        coverage: dict[str, Counter[str]] = defaultdict(Counter)
        for row in rows:
            for name, status in row["inputs"].items():
                coverage[name][status] += 1
        computable = [r for r in rows if r["successor_numeric"] != NOT_COMPUTABLE]
        entry: dict[str, Any] = {
            "opportunities": len(rows),
            "predecessor": dict(Counter(r["predecessor"] for r in rows)),
            "predecessor_asks": sum(1 for r in rows if r["predecessor_asks"]),
            "predecessor_by_draw": sum(1 for r in rows if r["predecessor_asks"] is None),
            "authority": dict(Counter(r["authority"] for r in rows)),
            "successor_information": dict(Counter(r["information"] for r in rows)),
            "coverage": {name: dict(counts) for name, counts in sorted(coverage.items())},
            "successor_numeric_computable": len(computable),
        }
        if lane == AUTOMATIC and "retries" in rows[0]:
            entry["retries"] = sum(r["retries"] for r in rows)
        if lane == LEARNER and "factor_receipts" in rows[0]:
            # How many receipts each factor has (a status read per panel mount writes one): {receipts: factors}.
            per = Counter(r["factor_receipts"] for r in rows)
            entry["receipts_per_factor"] = {n: count // n for n, count in sorted(per.items())}
        if computable:
            entry["successor_asks"] = sum(1 for r in computable if r["successor_asks"])
            entry["successor_choice"] = dict(Counter(r["successor_choice"] for r in computable))
            gate_rows = [r for r in computable if "predecessor_gate_asks" in r]
            entry["disagree_gate"] = sum(1 for r in gate_rows if r["predecessor_gate_asks"] != r["successor_asks"])
            entry["predecessor_numeric_asks"] = sum(1 for r in computable if r.get("predecessor_numeric_asks"))
            entry["disagree_predecessor_numeric"] = sum(
                1 for r in computable if r.get("predecessor_numeric_asks") != r["successor_asks"])
            # The predecessor's final answer is known where a rule (not a draw) gave it.
            ruled = [r for r in computable if r["predecessor_asks"] is not None]
            entry["predecessor_final_known"] = len(ruled)
            entry["disagree_final"] = sum(1 for r in ruled if r["predecessor_asks"] != r["successor_asks"])
            entry["differ_by"] = dict(Counter(
                f"{'asks' if r['predecessor_asks'] else 'no'}->{'asks' if r['successor_asks'] else 'no'}: "
                f"{r['authority']}" for r in ruled if r["predecessor_asks"] != r["successor_asks"]))
            entry["illustrative_cases"] = sum(1 for r in computable if r.get("illustrative"))
            costs = [r["cost"] for r in computable if "cost" in r]
            entry["cost_ms"] = _quantiles(c["ms"] for c in costs)
            entry["cost_ms_probe_paths"] = _quantiles(c["ms_probe"] for c in costs if c["ms_probe"])
            entry["predecessor_probe_ms"] = _quantiles(c["predecessor_probe_ms"] for c in costs)
            by_shape: dict[str, list[float]] = defaultdict(list)
            for c in costs:
                by_shape[f"H{c['hypotheses']} R{c['results']} A{c['repairs']} paths{c['effect_paths']}"].append(c["ms"])
            entry["cost_ms_by_shape"] = {shape: _quantiles(v) for shape, v in sorted(by_shape.items())}
        lanes[lane] = entry
    return {"decisions": DECISIONS.record(), "policy_version": DV.POLICY_VERSION, "lanes": lanes,
            "coupled_draws": "not computed: the successor has no mixture before the behaviour step"}


CASE_COLUMNS = ("case", "lane", "predecessor_gate", "predecessor", "predecessor_numeric_asks", "information",
                "information_value", "successor_choice", "ms", "ms_probe", "predecessor_probe_ms")


def case_table(opportunities: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """One row per synthetic journey (design labels, no vault data): what each side answered and what it cost."""

    rows = []
    for o in opportunities:
        value = o.get("information_value")
        rows.append({"case": o["case"], "lane": o["lane"], "predecessor_gate": o["predecessor_gate"],
                     "predecessor": o["predecessor"], "predecessor_numeric_asks": o["predecessor_numeric_asks"],
                     "information": o["information"],
                     "information_value": None if value is None else round(float(value), 4),
                     "successor_choice": o["successor_choice"], "ms": round(o["cost"]["ms"], 1),
                     "ms_probe": round(o["cost"]["ms_probe"], 1),
                     "predecessor_probe_ms": round(o["cost"]["predecessor_probe_ms"], 1)})
    return rows


def render_cases(rows: Sequence[Mapping[str, Any]]) -> str:
    lines = ["| " + " | ".join(CASE_COLUMNS) + " |", "|" + "---|" * len(CASE_COLUMNS)]
    lines += ["| " + " | ".join(str(row[c]) for c in CASE_COLUMNS) + " |" for row in rows]
    return "\n".join(lines)


def render(report: Mapping[str, Any], *, title: str) -> str:
    lines = [f"== {title}", f"successor policy {report['policy_version']}; owner decisions (each pending the owner):"]
    for name, entry in report["decisions"].items():
        lines.append(f"  {name}: {entry['value']}")
    for lane, entry in report["lanes"].items():
        lines.append(f"-- {lane} lane: {entry['opportunities']} opportunities")
        for key, value in entry.items():
            if key == "opportunities":
                continue
            if isinstance(value, Mapping):
                lines.append(f"   {key}:")
                for name, count in value.items():
                    lines.append(f"     {name}: {count}")
            else:
                lines.append(f"   {key}: {value}")
    lines.append(f"coupled draws: {report['coupled_draws']}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault", action="append", default=[], type=Path,
                        help="a vault directory or database: a backup copy, never a live vault")
    parser.add_argument("--synthetic", action="store_true", help="the controlled synthetic journeys")
    parser.add_argument("--draws", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.vault and not args.synthetic:
        parser.error("name --vault or --synthetic")
    reports: dict[str, Any] = {}
    for index, path in enumerate(args.vault, start=1):
        # The vault's position on the command line, never its path: a path can carry a name.
        reports[f"vault {index}"] = aggregate(vault_opportunities(path))
    cases: list[dict[str, Any]] = []
    if args.synthetic:
        synthetic = synthetic_opportunities(draws=args.draws)
        reports["synthetic"] = aggregate(synthetic)
        cases = case_table(synthetic)
    if args.json:
        print(json.dumps({**reports, **({"synthetic_cases": cases} if cases else {})}, indent=1, sort_keys=True))
    else:
        print("\n\n".join(render(report, title=title) for title, report in reports.items()))
        if cases:
            print("\n== synthetic journeys, one row each\n" + render_cases(cases))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
