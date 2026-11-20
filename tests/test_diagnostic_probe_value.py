"""The successor's pure probe evaluator (G2 step 4, unserved): it prices "ask the probe, then act on its result"
against acting now, over the locked hypotheses, in the router objective's own terms, and returns its value with its
record. Literal inputs only; no vault.

What each test proves is in its docstring. The owner's open decisions are passed as
``diagnostic_payload.DESIGN_RECOMMENDATIONS`` (the design's recommendations), never read from inside the evaluator.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from learnloop.router_objective import diagnostic_payload as DP
from learnloop.router_objective import diagnostic_value as DV
from learnloop.router_objective import rollouts as ROL
from learnloop.router_objective import types as OT
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = DP.DESIGN_RECOMMENDATIONS
DRAWS = 8


def _inputs(*, gap: tuple[float, float] = (0.8, 0.0), gamma: tuple[float, float] = (0.2, 0.0), causes: bool = True,
            kappa0: float = 0.05, session_minutes: float = 5.0) -> OT.Inputs:
    """Two practised topics; ``lo_a`` (the missed one) has a dated use. A literal ``γ_gap`` above ``γ`` makes a
    repair that covers a gap worth more than one that does not (at the seeded priors the two are equal)."""

    split = OT.CauseSplit(gap=gap, slip=(0.0, gamma[1])) if causes else None
    return OT.Inputs(
        topics=(OT.Topic("lo_a", -0.5, 0.3, practiced=True, stability=5.0, elapsed_days=2.0, undated_density=1.0),
                OT.Topic("lo_b", 0.5, 0.3, practiced=True, stability=5.0, elapsed_days=2.0, undated_density=0.2)),
        dated=(OT.DatedUse("g", "lo_a", 10.0, 1.0),),
        session_minutes=session_minutes, price=OT.Price(kappa0=kappa0, remembered=30.0), tail_block_minutes=10.0,
        tail_block_items=2, horizon_days=14.0, fsrs_weights=tuple(FSRS6_DEFAULT_WEIGHTS),
        learning=OT.Learning(gamma=gamma, causes=split))


def _repair(ref: str, minutes: float = 6.0) -> OT.Action:
    return OT.Action(ref=ref, kind=OT.REPAIR, item_los=("lo_a", "lo_a"), minutes=minutes)


HYPOTHESES = (DP.Hypothesis("h1", 0.6, DP.GAP), DP.Hypothesis("h2", 0.3, DP.GAP),
              DP.Hypothesis(DP.OPEN_HYPOTHESIS, 0.1, DP.UNKNOWN))
REPAIRS = (DP.RepairOption("r1", _repair("r1"), frozenset({"h1"})),
           DP.RepairOption("r2", _repair("r2"), frozenset({"h2"})))


def _channel(rows: dict[str, tuple[float, ...]], results: tuple[str, ...] = ("a", "b", "c")) -> DP.Channel:
    return DP.Channel(results=results, rows=tuple(rows.items()), version="test_channel_v1", source="literal")


INFORMATIVE = _channel({"h1": (0.9, 0.05, 0.05), "h2": (0.05, 0.9, 0.05), DP.OPEN_HYPOTHESIS: (1 / 3, 1 / 3, 1 / 3)})
PERFECT = _channel({"h1": (1.0, 0.0, 0.0), "h2": (0.0, 1.0, 0.0), DP.OPEN_HYPOTHESIS: (0.0, 0.0, 1.0)})
FLAT = _channel({h.id: (0.5, 0.5) for h in HYPOTHESES}, results=("right", "wrong"))


def _payload(channel=INFORMATIVE, **overrides) -> DP.DiagnosticProbe:
    fields = dict(topic="lo_a", hypotheses=HYPOTHESES, prior_basis="literal", channel=channel, repairs=REPAIRS)
    fields.update(overrides)
    return DP.DiagnosticProbe(**fields)


def _probe(payload: DP.DiagnosticProbe | None = None, *, ref: str = "probe", minutes: float = 3.0) -> OT.Action:
    return OT.Action(ref=ref, kind=OT.PROBE, item_los=("lo_a",), minutes=minutes,
                     diagnostic=payload if payload is not None else _payload())


def _evaluate(action: OT.Action, inputs: OT.Inputs | None = None, **kwargs) -> DV.ProbeValuation:
    return DV.evaluate_probe(inputs or _inputs(), action, decisions=kwargs.pop("decisions", DECISIONS), draws=DRAWS,
                             seed=kwargs.pop("seed", "g2b"), **kwargs)


def _q(valuation: DV.ProbeValuation, ref: str) -> float:
    return valuation.by_ref()[ref].q


# -- the policy sees the result ---------------------------------------------------------------------------------------


def test_an_informative_channel_changes_the_preferred_repair():
    """With causes that need different repairs and a channel that separates them, the repair chosen after a result
    pointing at the less likely cause differs from the one chosen under the prior, and the probe's information
    (its policy's value minus asking it and then acting on the prior) is positive."""

    out = _evaluate(_probe())
    record = out.record
    choices = {row["result"]: row["choice"] for row in record["results"]}
    assert record["prior_choice"] == "r1"
    assert choices["a"] == "r1" and choices["b"] == "r2"
    assert record["policy_changes_with_result"] is True
    assert record["values"]["information"] > 0.0
    assert record["channel_use"] == "channel"


def test_a_flat_channel_changes_nothing_and_its_probe_is_worth_only_its_burden():
    """Identical rows leave every posterior at the prior: every result chooses the prior's repair, the information
    is exactly zero, and the probe's value is exactly "ask it, then act on the prior", below acting now with that
    repair by the probe's own time (its burden), with no binary-ability credit."""

    out = _evaluate(_probe(_payload(FLAT)))
    record = out.record
    assert {row["choice"] for row in record["results"]} == {record["prior_choice"]}
    for row in record["results"]:
        assert row["posterior"] == pytest.approx(_payload().effective_prior())
    assert record["values"]["information"] == 0.0
    assert record["values"]["probe_policy"] == record["values"]["probe_then_prior_choice"]
    assert _q(out, "probe") < _q(out, f"{DV.ACT_NOW}{record['prior_choice']}")
    assert record["policy_changes_with_result"] is False


def test_acting_now_is_always_valued_beside_the_probe():
    """The open arm (acting without the probe: no repair, or each repair now) is valued in every case: with a
    channel, without one, exposed, and when a hard stop keeps the probe out of the support (then only the open arm
    is valued and the exclusion is recorded)."""

    now = {f"{DV.ACT_NOW}none", f"{DV.ACT_NOW}r1", f"{DV.ACT_NOW}r2"}
    for payload in (_payload(), _payload(FLAT), _payload(DP.MissingChannel("unauthored")), _payload(exposed=True)):
        out = _evaluate(_probe(payload))
        assert now <= set(out.by_ref()) and "probe" in out.by_ref()
        assert out.choice in now | {"probe"}
    stopped = _evaluate(_probe(_payload(hard_stops=("learner_preference",))))
    assert set(stopped.by_ref()) == now
    assert stopped.record["excluded"]["probe"] == ["learner_preference"]
    assert stopped.choice in now


def test_no_clairvoyance():
    """The policy sees the result, never the hypothesis: its value never exceeds "ask the probe, then act knowing the
    true hypothesis" (the bound the record computes); a perfect channel reaches it, a noisy one falls short."""

    for channel in (INFORMATIVE, PERFECT, FLAT, DP.MissingChannel("unauthored")):
        values = _evaluate(_probe(_payload(channel))).record["values"]
        assert values["probe_policy"] <= values["clairvoyant"] + 1e-12
    perfect = _evaluate(_probe(_payload(PERFECT))).record["values"]
    assert perfect["probe_policy"] == pytest.approx(perfect["clairvoyant"], abs=1e-12)
    noisy = _evaluate(_probe(_payload(INFORMATIVE))).record["values"]
    assert noisy["probe_policy"] < noisy["clairvoyant"] - 1e-9


# -- one clock, one tail ----------------------------------------------------------------------------------------------


def _cost(inputs: OT.Inputs, *pieces: tuple[OT.Action, int]) -> float:
    """The κ integral of these segments back to back from the session's minutes, per draw, averaged."""

    model = ROL._Model(inputs, DRAWS, "g2b")
    minutes = sum(model._durations(action, stream) for action, stream in pieces)
    return float(model.cost(np.full(DRAWS, float(inputs.session_minutes)), minutes).mean())


def test_the_probe_duration_is_charged_once():
    """The probe's minutes enter the action's κ integral once: alone (probe, then no repair), before a repair (the
    two back to back) and in the policy's value (every branch carries the probe once)."""

    inputs = _inputs()
    probe = _probe()
    terms = _evaluate(probe, inputs).record["branch_terms"]["probe"]
    assert terms["none"]["none"]["kappa_integral"] == pytest.approx(_cost(inputs, (probe, 0)), rel=1e-12)
    for key, value in terms["r1"].items():
        assert value["kappa_integral"] == pytest.approx(_cost(inputs, (probe, 0), (REPAIRS[0].action, DV.REPAIR_STREAM)),
                                                        rel=1e-12), key
    now = _evaluate(probe, inputs).record["branch_terms"]["act_now"]
    assert now["none"]["none"]["kappa_integral"] == 0.0
    assert now["r1"]["uncovered"]["kappa_integral"] == pytest.approx(
        _cost(inputs, (REPAIRS[0].action, DV.REPAIR_STREAM)), rel=1e-12)


def test_a_probe_anywhere_in_a_sequence_appends_the_rest_and_the_tail_once():
    """In a sequence the probe's result chooses the repair, which comes right after it; the remaining steps follow
    once and the tail once. Probe first or last, each path's κ integral is its segments back to back; a one-step
    sequence is the probe alone."""

    inputs = _inputs()
    review = OT.Action(ref="review_b", kind=OT.REVIEW, item_los=("lo_b",), minutes=4.0)
    probe = _probe()
    one = OT.Action(ref="seq1", kind=OT.SEQUENCE, item_los=("lo_a",), minutes=3.0, steps=(probe,))
    alone = _evaluate(probe, inputs)
    assert _q(_evaluate(one, inputs), "seq1") == pytest.approx(_q(alone, "probe"), abs=1e-12)
    for steps in ((probe, review), (review, probe)):
        sequence = OT.Action(ref="seq", kind=OT.SEQUENCE, item_los=("lo_a", "lo_b"), minutes=7.0, steps=steps)
        record = _evaluate(sequence, inputs).record
        streams = dict((step.ref, stream) for step, stream in ROL._Model(inputs, DRAWS, "g2b")._steps(sequence, 0))
        segments = [(step, streams[step.ref]) for step in steps]
        assert record["branch_terms"]["probe"]["none"]["none"]["kappa_integral"] == pytest.approx(
            _cost(inputs, *segments), rel=1e-12)
        at = [step.ref for step in steps].index("probe") + 1
        with_repair = [*segments[:at], (REPAIRS[1].action, DV.REPAIR_STREAM), *segments[at:]]
        assert record["branch_terms"]["probe"]["r2"][DP.GAP]["kappa_integral"] == pytest.approx(
            _cost(inputs, *with_repair), rel=1e-12)
        assert record["given"]["position"] == f"step {at - 1} of a sequence"
    with pytest.raises(ValueError, match="one diagnostic probe"):
        _evaluate(OT.Action(ref="two", kind=OT.SEQUENCE, item_los=("lo_a",), minutes=6.0,
                            steps=(probe, _probe(ref="probe2"))), inputs)


def test_a_lesson_declined_at_the_same_boundary_prices_its_probe_as_exposed():
    """A lesson offered at the post-miss boundary releases the feedback, so the probe that follows a "Not now" is
    exposed: the offer is ``p·(lesson accepted) + (1 − p)·(the probe, exposed)``, the declined probe earns no
    information however informative its channel, and it is charged its minutes once."""

    inputs = _inputs()
    probe = _probe()
    lesson = OT.Action(ref="lesson", kind=OT.LESSON, item_los=("lo_a",), minutes=8.0, mass=0.5, accept=(2.0, 2.0),
                       declined=probe)
    out = _evaluate(lesson, inputs)
    record = out.record
    assert record["given"]["position"] == "declined branch of an offer"
    assert record["channel_use"] == "exposed" and record["given"]["payload"]["exposed"] is True
    assert record["values"]["information"] == 0.0
    model = ROL._Model(inputs, DRAWS, "g2b")
    accepted, _state, _minutes = model._do(replace(lesson, accept=None, declined=None))
    p = ROL._beta_draw(model.streams.offer_u, 2.0, 2.0)
    declined = np.asarray(record["offer"]["declined_q_draws"])
    np.testing.assert_allclose(out.by_ref()["lesson"].q_draws, p * accepted.q + (1 - p) * declined, rtol=1e-12)
    exposed = _evaluate(_probe(_payload(exposed=True)), inputs, base_stream=1).by_ref()["probe"]
    np.testing.assert_allclose(declined, exposed.q_draws, rtol=1e-12)
    assert record["branch_terms"]["probe"]["none"]["none"]["kappa_integral"] == pytest.approx(
        _cost(inputs, (probe, 1)), rel=1e-12)


# -- no information where none can be had ------------------------------------------------------------------------------


def test_an_exposed_answer_gives_no_information():
    """The same discriminating channel, the answer exposed (after feedback, causes or a reveal): one posterior, the
    prior; zero information; the value of asking and then acting on the prior."""

    out = _evaluate(_probe(_payload(exposed=True)))
    record = out.record
    assert record["channel_use"] == "exposed"
    assert [row["result"] for row in record["results"]] == ["exposed"]
    assert record["values"]["information"] == 0.0
    assert record["values"]["probe_policy"] == record["values"]["probe_then_prior_choice"]


def test_a_missing_channel_is_explicit_and_earns_no_information_credit():
    """An unauthored probe has no channel: the payload says so (it cannot carry a partial one), the record names it,
    and under decision 1's recommendation it earns no information; its burden and repair are still priced."""

    out = _evaluate(_probe(_payload(DP.MissingChannel("unauthored"))))
    record = out.record
    assert record["channel_use"] == "missing:unauthored"
    assert record["given"]["payload"]["channel"] == {"status": "missing", "reason": "unauthored"}
    assert record["values"]["information"] == 0.0
    assert record["decisions"]["1_unauthored_channel"] == {"value": DP.NO_INFORMATION_CREDIT, "status": DP.PENDING}
    with pytest.raises(ValueError, match="one row per locked hypothesis"):
        _payload(_channel({"h1": (0.5, 0.5, 0.0), "h2": (0.0, 0.5, 0.5)}))


def test_hypotheses_are_reweighted_never_removed():
    """A result that rules a hypothesis out leaves it in the posterior at zero; the open hypothesis stays; a routing
    weight reweights (the effective prior moves) and can never be zero."""

    out = _evaluate(_probe(_payload(PERFECT)))
    ids = [h.id for h in HYPOTHESES]
    for row in out.record["results"]:
        assert list(row["posterior"]) == ids
    assert out.record["results"][0]["posterior"]["h2"] == 0.0
    weighted = _payload(routing_weights=DP.weights_from({"h2": 3.0}), routing_version="li4_test_v1")
    prior = weighted.effective_prior()
    assert list(prior) == ids and prior["h2"] == pytest.approx(0.9 / 1.6) and prior[DP.OPEN_HYPOTHESIS] > 0.0
    assert _evaluate(_probe(weighted)).record["given"]["payload"]["routing_version"] == "li4_test_v1"
    with pytest.raises(ValueError, match="never removes"):
        _payload(routing_weights=(("h2", 0.0),))


# -- the owner's decisions are inputs ---------------------------------------------------------------------------------


def test_the_owner_decisions_are_named_inputs_marked_pending():
    """Each open decision is a field of the decisions input, recorded with its value and "pending the owner"; a value
    the code cannot honestly supply is refused, not approximated; decision 3 keeps no intervention as an arm when
    there is no room to wait, and its predecessor's shape (False) removes it."""

    record = _evaluate(_probe()).record["decisions"]
    assert {entry["status"] for entry in record.values()} == {DP.PENDING}
    assert record["2_uncovered_repair_effect"]["value"] == DP.PRACTICE_GAMMA
    for field, value in (("unauthored_channel", "generation_prior"), ("uncovered_repair_effect", "zero")):
        with pytest.raises(ValueError, match="decision"):
            replace(DECISIONS, **{field: value})
    kept = _evaluate(_probe(), wait_feasible=False)
    assert f"{DV.ACT_NOW}none" in kept.by_ref()
    removed = _evaluate(_probe(), wait_feasible=False, decisions=replace(DECISIONS, no_intervention_without_wait=False))
    assert f"{DV.ACT_NOW}none" not in removed.by_ref()
    assert removed.record["excluded"][f"{DV.ACT_NOW}none"] == "decision 3: no room to wait removes no intervention"


def test_at_the_seeded_priors_a_covering_repair_on_a_gap_is_worth_what_practice_is():
    """Decision 2's consequence, stated: ``γ_gap``'s seeded prior is ``γ``'s and an uncovered repair is practice at
    ``γ``, so between two gap causes the probe's information is worth nothing until data move ``γ_gap``; with no
    cause slopes in the inputs at all, every repair is practice."""

    for inputs in (_inputs(gap=(0.2, 0.0)), _inputs(causes=False)):
        values = _evaluate(_probe(_payload(PERFECT)), inputs).record["values"]
        assert values["information"] == pytest.approx(0.0, abs=1e-12)


# -- purity and reach -------------------------------------------------------------------------------------------------


def test_the_evaluator_is_deterministic_and_its_record_names_its_inputs():
    """The same inputs and seed give the same values and record (the cost aside); the record carries what it was
    given, the draws and the seed, and the version of this policy."""

    first, second = _evaluate(_probe()), _evaluate(_probe())
    assert [v.q_draws for v in first.valued] == [v.q_draws for v in second.valued]
    strip = {k: v for k, v in first.record.items() if k != "cost"}
    assert strip == {k: v for k, v in second.record.items() if k != "cost"}
    assert first.record["version"] == DV.POLICY_VERSION
    assert first.record["given"]["draws"] == DRAWS and first.record["given"]["seed"] == "g2b"
    assert first.record["cost"]["rollouts"] > 0


def test_a_probe_without_a_payload_is_the_predecessors_and_a_payload_is_refused_there():
    """No payload: the rollouts value a probe exactly as before (the predecessor's binary probe). A payload reaching
    the predecessor's rollouts is refused rather than priced as a binary probe; only the successor evaluator prices
    it."""

    inputs = _inputs()
    bare = OT.Action(ref="probe", kind=OT.PROBE, item_los=("lo_a",), minutes=3.0, repair=REPAIRS[0].action)
    assert bare.diagnostic is None
    ROL.evaluate(inputs, [bare], draws=DRAWS, seed="g2b")
    with pytest.raises(ValueError, match="diagnostic payload"):
        ROL.evaluate(inputs, [_probe()], draws=DRAWS, seed="g2b")
    with pytest.raises(ValueError, match="only a probe"):
        OT.Action(ref="r", kind=OT.REPAIR, item_los=("lo_a",), diagnostic=_payload())


def test_no_served_module_imports_the_evaluator():
    """Nothing under ``src`` imports the successor evaluator (by name, from its package, or through importlib): it
    runs only in tests and the comparison report until the behaviour step wires it."""

    hits = []
    for path in sorted((ROOT / "src").rglob("*.py")):
        if path.name == "diagnostic_value.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "diagnostic_value" not in text:
            continue
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.ImportFrom) and (
                    (node.module or "").endswith("diagnostic_value")
                    or any(alias.name == "diagnostic_value" for alias in node.names)):
                hits.append(str(path.relative_to(ROOT)))
            elif isinstance(node, ast.Import) and any(a.name.endswith("diagnostic_value") for a in node.names):
                hits.append(str(path.relative_to(ROOT)))
            elif isinstance(node, ast.Call) and getattr(node.func, "attr", getattr(node.func, "id", "")) in {
                    "import_module", "__import__"} and any(
                    isinstance(arg, ast.Constant) and "diagnostic_value" in str(arg.value) for arg in node.args):
                hits.append(str(path.relative_to(ROOT)))
    assert hits == []
