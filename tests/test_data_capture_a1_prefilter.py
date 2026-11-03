"""Data capture A1: the prefilter receipt, linked into each committed decision.

What was decided before the router saw candidates: considered ids, exclusions and reasons, likelihood and
config versions, actual inputs, code revision. Deterministic admission is probability 0 or 1, the router's
own probability stays conditional on it. The plan's pool has no OfferTrace today, scheduler gates are lost
when no session exists yet, the block receipt holds only project probes' valuations, and VOI receipts keep
six candidate summaries: each reproduced here. Parts are stored once by hash; nothing here changes serving.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from learnloop.algorithm_versions import DATA_CAPTURE_ALGORITHM_VERSION, LESSON_SUGGESTIONS_ALGORITHM_VERSION
from learnloop.daily_plan.engine import PlanEnv, advance, build_plan
from learnloop.data_capture import prefilter as PF
from learnloop.db.stores import data_capture as store
from learnloop.diagnosis import voi_stopping as voi
from learnloop.vault.loader import load_vault

from tests.daily_plan_fakes import MovableClock
from tests.router_mixture_helpers import mixture_env, rows, run
from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime
from tests.test_daily_plan_build import _seed_wide, _wide_vault

TAG = DATA_CAPTURE_ALGORITHM_VERSION
OLD = LESSON_SUGGESTIONS_ALGORITHM_VERSION
OFF = "[data_capture]\nreceipts = false\n"


def _real_env(tmp_path, *, session_id=None, version=TAG, toml=None):
    """A plan env that builds through the real scheduler (no injected list)."""

    from tests.helpers import append_config_toml

    paths = _wide_vault(tmp_path, version=version)
    if toml:
        append_config_toml(paths.root, toml)
    vault = load_vault(paths.root)
    from learnloop.db.repositories import Repository

    repository = Repository(paths.sqlite_path)
    env = PlanEnv(vault=vault, repository=repository, clock=MovableClock(), session_id=session_id)
    _seed_wide(repository)
    return env


def _receipts(env):
    with env.repository.connection() as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM prefilter_receipts ORDER BY created_at, id")]


def _read(env, decision_id):
    with env.repository.connection() as connection:
        return PF.read(connection, decision_id)


def test_a_plan_built_with_no_session_links_the_schedulers_gates_into_its_decision(tmp_path):
    """Reproduced first: no session, so no slate; the build's gates reached no record at all."""

    env = _real_env(tmp_path, session_id=None)
    record = build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    assert record.blocks
    with env.repository.connection() as connection:
        decisions = [dict(row) for row in connection.execute(
            "SELECT id, decision_kind, session_id FROM router_decisions WHERE decision_kind = 'plan_block'")]
    assert decisions and decisions[0]["session_id"] is None
    receipt = _read(env, decisions[0]["id"])
    assert receipt is not None and receipt["surface"] == PF.SURFACE_PLAN_POOL
    assert receipt["session_present"] == 0 and receipt["scheduler_trace"] == 1
    assert "exclusions" in receipt["gates"]
    assert isinstance(receipt["inputs"]["considered"], list) and receipt["inputs"]["considered"]
    assert receipt["considered_count"] >= receipt["admitted_count"] > 0
    assert receipt["code_revision"] and receipt["algorithm_version"] == TAG
    assert receipt["versions"]["receipt"] == PF.RECEIPT_VERSION
    assert receipt["versions"]["voi_forecast"] == voi.FORECAST_VERSION


def test_admission_is_probability_one_or_zero_and_the_routers_stays_conditional(tmp_path):
    env = _real_env(tmp_path, session_id="s1")
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    with env.repository.connection() as connection:
        decision = dict(connection.execute(
            "SELECT id, candidates_json, propensity FROM router_decisions WHERE decision_kind = 'plan_block'").fetchone())
    receipt = _read(env, decision["id"])
    admission = receipt["classification"]["admission"]
    assert admission["deterministic"] is True and admission["router_probability"] == "conditional_on_admission"
    admitted = admission["probability_1"]
    assert admitted
    assert PF.admission_probability(receipt, admitted[0]) == 1.0
    assert PF.admission_probability(receipt, "pi_never_considered") is None
    refused = [item for ids in admission["probability_0"].values() for item in ids]
    if refused:
        assert PF.admission_probability(receipt, refused[0]) == 0.0
    # Every item of every candidate of the decision was admitted first.
    items = {item for entry in json.loads(decision["candidates_json"]) for item in entry.get("item_ids") or ()}
    assert items <= set(admitted)


def test_a_trace_refusal_names_every_reason_and_id(tmp_path):
    trace = SimpleNamespace(
        exclusions={"zero_priority": ["pi_a", "pi_b"], "retired": ["pi_c"]}, probe_block_reason="cap",
        cold_deferrals=(), pinned_item_id=None, placement_active=False, voi_decisions=({"site": "probe_episode"},),
        teach_back_exclusion_reason="x", considered=(), exploration={"seed": "s", "rate": 0.0}, base_propensity={},
        session_context={}, config_snapshot={"algorithm_version": TAG}, limit=None, session_id=None,
    )
    material = PF.today_offer_material(trace, offered=["pi_x"], versions={})
    gates = json.loads(material.parts["gates"])
    assert gates["exclusions"] == {"retired": ["pi_c"], "zero_priority": ["pi_a", "pi_b"]}
    assert gates["probe_block_reason"] == "cap"
    assert json.loads(material.parts["upstream"])["voi_decisions"] == [{"site": "probe_episode"}]


def _site_decision(candidates, *, record_all):
    values = tuple(
        voi.CandidateValue(ref=f"pi_{index}", decision="stop", reason="r", method="eig", value_uncertain=False,
                           eig_nats=0.1, eig_robust_nats=0.1, member_eig_nats=0.1, value_point_minutes=0.1,
                           value_robust_minutes=0.1, value_ucb_minutes=None, cost_minutes=1.0,
                           minutes=voi.MinutesEstimate(1.0, "plan_estimate"), forecast={}, detail={})
        for index in range(candidates)
    )
    return voi.SiteDecision(site="probe_episode", learning_object_id="lo", decision="stop", reason="r", candidates=values,
                            former_cap={}, rank=None, context={}, parameters=[], record_all_candidates=record_all)


def test_a_voi_receipt_no_longer_truncates_candidates_to_six():
    """Reproduced first: nine candidates, six summaries (candidate_count says nine)."""

    assert len(_site_decision(9, record_all=False).as_dict()["candidates"]) == voi.MAX_RECORDED_CANDIDATES
    whole = _site_decision(9, record_all=True).as_dict()
    assert len(whole["candidates"]) == whole["candidate_count"] == 9


def test_the_voi_flag_follows_the_successors_switch(tmp_path):
    tagged = _real_env(tmp_path / "tag")
    below = _real_env(tmp_path / "old", version=OLD)
    off = _real_env(tmp_path / "off", toml="[data_capture]\nserving = false\n")
    from learnloop.data_capture.gates import serving_on

    assert serving_on(tagged.vault.config) and not serving_on(below.vault.config) and not serving_on(off.vault.config)


def test_an_unchanged_part_is_referenced_not_copied(tmp_path):
    env = _real_env(tmp_path, session_id="s1")
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    env.clock.advance(1)
    run(env)
    receipts = _receipts(env)
    assert len(receipts) >= 2
    assert len({row["config_payload_hash"] for row in receipts}) == 1, "the configuration is stored once"
    with env.repository.connection() as connection:
        parts = {row[0]: row[1] for row in connection.execute("SELECT content_hash, part FROM prefilter_payloads")}
        distinct = {row[n] for row in receipts for n in ("gates_hash", "classification_hash", "upstream_hash", "inputs_hash",
                                                          "config_payload_hash")}
        stored, raw = connection.execute("SELECT SUM(stored_bytes), SUM(raw_bytes) FROM prefilter_payloads").fetchone()
    assert set(parts) == distinct, "every stored part is referenced, and each once"
    assert len(parts) < 5 * len(receipts)
    assert 0 < stored < raw


def test_every_mixture_and_interrupt_decision_has_its_receipt(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=FakeLLM()), version=TAG)
    run(env)
    # ``mixture_env`` injects its list, so its receipts name the missing trace rather than inventing one.
    for row in rows(env):
        receipt = _read(env, row["id"])
        assert receipt is not None and receipt["scheduler_trace"] == 0
        assert receipt["classification"]["pool"]


def test_receipts_act_at_every_version_and_change_nothing_served(tmp_path):
    """Below the tag the receipts are written and the plan is what it was."""

    with_receipts = _real_env(tmp_path / "on", version=OLD)
    without = _real_env(tmp_path / "off", version=OLD, toml=OFF)
    first = build_plan(with_receipts, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    second = build_plan(without, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    assert [(b.lane, tuple(i.practice_item_id for i in b.items)) for b in first.blocks] == [
        (b.lane, tuple(i.practice_item_id for i in b.items)) for b in second.blocks]
    assert _receipts(with_receipts) and not _receipts(without)
    with with_receipts.repository.connection() as a, without.repository.connection() as b:
        chosen_a = [dict(row)["chosen_ref"] for row in a.execute("SELECT chosen_ref FROM router_decisions ORDER BY created_at")]
        chosen_b = [dict(row)["chosen_ref"] for row in b.execute("SELECT chosen_ref FROM router_decisions ORDER BY created_at")]
    assert chosen_a == chosen_b


def test_a_refused_receipt_never_blocks_the_block(tmp_path, monkeypatch):
    env = _real_env(tmp_path, session_id="s1")

    def refuse(*_args, **_kwargs):
        raise RuntimeError("the disk is full")

    monkeypatch.setattr(store, "insert_prefilter_receipt", refuse)
    record = build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    assert record.blocks and not _receipts(env)


def test_the_code_revision_is_named_and_can_be_pinned(monkeypatch):
    PF.code_revision.cache_clear()
    monkeypatch.setenv(PF.CODE_REVISION_ENV, "release-1")
    assert PF.code_revision() == "release-1"
    PF.code_revision.cache_clear()
    monkeypatch.delenv(PF.CODE_REVISION_ENV)
    assert PF.code_revision().split(":")[0] in {"git", "package", "unknown"}
    PF.code_revision.cache_clear()


def test_a_decision_row_receipt_says_it_has_no_scheduler_trace():
    row = {"candidates_json": json.dumps([{"ref": "a", "feasible": True}, {"ref": "b", "feasible": False}]),
           "exclusions_json": json.dumps({"named": {"new_goal_only": ["lo_x"]}}), "snapshot_hash": "h", "session_id": None}
    material = PF.decision_row_material(row, versions={})
    assert material.scheduler_trace is False and material.surface == PF.SURFACE_DECISION_ROW
    assert material.admitted == 1 and material.refused == 1


def test_receipts_are_keyed_by_the_decision_once(tmp_path):
    env = _real_env(tmp_path, session_id="s1")
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    advance(env, serve=True)
    with env.repository.connection() as connection:
        ids = [row["decision_id"] for row in connection.execute("SELECT decision_id FROM prefilter_receipts")]
    assert len(ids) == len(set(ids))


def test_a_followups_interrupt_decision_has_the_builds_receipt(tmp_path):
    from tests.router_model_fakes import first_option, seed_with_first_uniform
    from tests.test_router_g4_restraint import DECIDER_ONLY, PAST_THE_FLOOR, _followup_env

    runtime = fake_runtime(decider=FakeDecider(choice=first_option, p_yes=0.0),
                           seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env = _followup_env(tmp_path, runtime, version=TAG, toml=DECIDER_ONLY)
    advance(env, serve=True)
    (row,) = rows(env, "plan_interrupt")
    receipt = _read(env, row["id"])
    assert receipt is not None and receipt["decision_kind"] == "plan_interrupt"
    assert receipt["surface"] == PF.SURFACE_PLAN_POOL


def test_todays_offer_links_its_builds_receipt_with_every_gate(tmp_path):
    import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    from tests.helpers import create_basic_vault, seed_due_item

    paths = create_basic_vault(tmp_path / "vault")
    seed_due_item(paths)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    session = METHOD_REGISTRY["start_session"].handler(
        ctx, METHOD_REGISTRY["start_session"].params_model.model_validate({"availableMinutes": 25}))
    spec = METHOD_REGISTRY["get_today_queue"]
    spec.handler(ctx, spec.params_model.model_validate({"sessionId": session["sessionId"]}))
    _vault, repository = ctx.require_vault()
    with repository.connection() as connection:
        offers = [dict(row) for row in connection.execute(
            "SELECT id, decision_kind FROM router_decisions WHERE decision_kind = 'today_offer'")]
        assert offers
        receipt = PF.read(connection, offers[-1]["id"])
    assert receipt is not None and receipt["surface"] == PF.SURFACE_TODAY_OFFER and receipt["session_present"] == 1
    assert receipt["scheduler_trace"] == 1 and "exclusions" in receipt["gates"]
    assert "probability_1" in receipt["classification"]["admission"]
    assert receipt["algorithm_version"] == _vault.config.algorithms.algorithm_version
