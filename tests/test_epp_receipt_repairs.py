"""EPp-c: future logging changes only; synthetic vaults, frozen time, no model calls."""

from dataclasses import replace
import json
from types import SimpleNamespace

import pytest

from learnloop.daily_plan import ad_slot, slot_facts
from learnloop.daily_plan import slot_facts_schema as SF
from learnloop.db.repositories import Repository
from learnloop.router import mixture
from learnloop.router_objective import assignments as A
from learnloop.router_objective import checks as C
from learnloop.vault.loader import load_vault

from tests.ad23_contract_helpers import _deterministic, _reset_ids
from tests.epp_receipt_repairs_helpers import legacy_place
from tests.epp_snapshot_helpers import journey, table_rows, tables
from tests.ro5_checks_helpers import CHECKS_ONLY, TAG, _env
from tests.router_mixture_helpers import join_carried_valuations, mixture_env, run
from tests.router_model_fakes import fake_runtime


def facts(**changes):
    return SF.SlotFacts(kind="slot", now="2026-10-12T09:00:00Z", plan_id="plan1",
                        members=(), refusals={}, cold_items=(), reserved_items=(),
                        exclusions={name: () for name in SF.EXCLUSION_NAMES}, **changes)


@pytest.mark.parametrize("propensity", [None, 0.0, 0.37, 1.0])
def test_nullable_slot_facts_round_trip(propensity):
    original = facts(router_propensity=propensity)
    assert original.version == "slot_facts_v2"
    assert SF.decode(SF.encode(original), visible=()) == original
    assert facts().router_propensity is None


@pytest.mark.parametrize("propensity", [0.0, 0.37, 1.0])
def test_old_numeric_slot_facts_keep_their_value_and_wire(propensity):
    wire = SF.encode(facts(router_propensity=propensity, version="slot_facts_v1"))
    decoded = SF.decode(wire, visible=())
    assert decoded.router_propensity == propensity
    assert SF.encode(decoded) == wire


def test_null_is_only_in_the_versioned_nullable_contract():
    with pytest.raises(SF.SlotFactsError):
        SF.decode(SF.encode(facts(router_propensity=None, version="slot_facts_v1")), visible=())


@pytest.mark.parametrize("old_propensity", [1.0, 0.37])
def test_unknown_propensity_changes_only_logging_through_ad_slot(tmp_path, monkeypatch, old_propensity):
    real_facts, real_decide = slot_facts.for_slot, ad_slot.decide
    wires = []

    def decide(vault, repository, wire, **kwargs):
        wires.append(json.loads(wire))
        return real_decide(vault, repository, wire, **kwargs)

    def copy(root, old):
        def no_router(env, record, block, *args, **kwargs):
            result = real_facts(env, record, replace(block, chosen=None, decision_ref=None), *args, **kwargs)
            if old:
                return replace(result, router_propensity=old_propensity, version="slot_facts_v1")
            assert result.router_propensity is None
            return result

        with monkeypatch.context() as patch:
            patch.setattr(slot_facts, "for_slot", no_router)
            patch.setattr(ad_slot, "decide", decide)
            return journey(root, patch)

    # Process-level first-use setup consumes one extra id, independently of the repair.
    journey(tmp_path / "warmup", monkeypatch)
    old = copy(tmp_path / "old", True)
    new = copy(tmp_path / "new", False)
    assert old["served"] == new["served"]
    assert any(w["version"] == "slot_facts_v1" for w in wires)
    assert any(w["version"] == "slot_facts_v2" and w["router_propensity"] is None for w in wires)
    for table in tables(old["paths"].sqlite_path):
        left, right = (table_rows(copy_["paths"].sqlite_path, table) for copy_ in (old, new))
        if table == "ad_selections":
            assert left and len(left) == len(right)
            for before, after in zip(left, right, strict=True):
                if before["block_id"] is None:  # commission draws have no router slot
                    assert before == after
                    continue
                assert before.pop("router_propensity") == old_propensity
                assert after.pop("router_propensity") is None
                pair = before.pop("pair_propensity")
                assert pair == pytest.approx(old_propensity * before["propensity"])
                assert after.pop("pair_propensity") is None
        assert left == right, (table, [(key, a[key], b[key]) for a, b in zip(left, right, strict=False)
                                      for key in a if a[key] != b[key]])


def test_redraw_is_reconstructed_from_placement_alone_and_uses_one_uniform(tmp_path, monkeypatch):
    env = _env(tmp_path)
    C.draw_day(env.vault, env.repository, local_date=env.today(), now_iso=env.now_iso(),
               topics={"L": 1.0}, eligible_items=lambda *_: {"L": ["original"]})
    with env.repository.connection() as connection:
        before = A.rows(connection, A.CHECK)
    calls = []
    real_uniform = mixture.uniform

    def uniform(seed, label):
        calls.append((seed, label))
        return real_uniform(seed, label)

    monkeypatch.setattr(mixture, "uniform", uniform)
    pool = [SimpleNamespace(practice_item_id=item, lane=None) for item in ("a", "b", "c")]
    [placement] = C.place(env.vault, env.repository, local_date=env.today(), session_id=None,
                          pool=pool, planned=(), chooser_items=[pool[0]], lane=None,
                          eligible_items=lambda *_: {"L": ["c", "outside_pool", "b", "a"]})
    assert len(calls) == 1
    record = json.loads(json.dumps(placement.detail))
    redraw = record["redraw"]
    assert redraw["candidate_ids"] == ["c", "b", "a"]
    assert redraw["u"] == real_uniform(*calls[0])
    assert redraw["conditional_propensity"] == 1 / len(redraw["candidate_ids"])
    chosen = redraw["candidate_ids"][min(int(redraw["u"] * len(redraw["candidate_ids"])),
                                         len(redraw["candidate_ids"]) - 1)]
    assert chosen == redraw["replacement_item_id"] == placement.item.practice_item_id
    assert redraw["original_item_id"] == placement.slot["item_id"] == "original"
    assert placement.slot["item_propensity"] == 1.0
    assert record["replaced"] == "a"  # the displaced chooser slot is a separate identity
    with env.repository.connection() as connection:
        assert A.rows(connection, A.CHECK) == before


def test_redraw_frozen_journey_keeps_served_items_ids_and_every_seed(tmp_path, monkeypatch):
    real_place = C.place
    join_carried_valuations(monkeypatch)

    def copy(root, placement):
        with monkeypatch.context() as patch:
            _deterministic(patch)
            _reset_ids(patch)
            patch.setattr(C, "place", placement)
            runtime = fake_runtime()
            runtime.clock = lambda: 1.0
            env = mixture_env(root, runtime, version=TAG, toml=CHECKS_ONLY)
            # A historical assignment whose item is absent now. Actual eligibility and
            # the engine's pool provide the replacement at the administration boundary.
            C.draw_day(env.vault, env.repository, local_date=env.today(), now_iso=env.now_iso(),
                       topics={"lo_eigen_basics": 1.0},
                       eligible_items=lambda *_: {"lo_eigen_basics": ["original"]})
            run(env, steps=8)
            return env.repository.sqlite_path

    copy(tmp_path / "warmup", real_place)
    old = copy(tmp_path / "old", legacy_place)
    new = copy(tmp_path / "new", real_place)
    redrawn = []
    for table in tables(old):
        left, right = table_rows(old, table), table_rows(new, table)
        if table == "attention_block_events":
            for row in right:
                detail = json.loads(row["detail_json"])
                check = detail.get("ro5_check", {})
                if "redraw" in check:
                    redrawn.append(check.pop("redraw"))
                    row["detail_json"] = json.dumps(detail, sort_keys=True)
            for row in left + right:
                row["detail_json"] = json.loads(row["detail_json"])
        assert left == right, (table, [(key, a[key], b[key]) for a, b in zip(left, right, strict=False)
                                      for key in a if a[key] != b[key]])
    assert redrawn and all(r["original_item_id"] == "original" for r in redrawn)
    assert table_rows(new, "plan_presentations")
    assert table_rows(new, "router_objective_traces")


def test_epp1_stop_condition_scorer_raises_on_unreadable_time(tmp_path, monkeypatch):
    """Do not repair the clamp until the reader contract has been reviewed (user stop condition)."""
    from learnloop.adaptive_difficulty import scoring

    result = journey(tmp_path, monkeypatch)
    repository = Repository(result["paths"].sqlite_path)
    vault = load_vault(result["paths"].root)
    with repository.atomic(), repository.connection() as connection:
        readable = scoring.score_rows(connection, vault, repository)
        assert any(row["status"] == "scored" for row in readable)
        # Append a synthetic historical receipt; no old row or trigger is modified.
        row = dict(connection.execute("SELECT * FROM forecast_receipts WHERE "
                                      "plan_presentation_id IS NOT NULL LIMIT 1").fetchone())
        row.update(id="unreadable_receipt", receipt_key="unreadable_receipt", inputs_as_of="!not a time")
        connection.execute(f"INSERT INTO forecast_receipts ({','.join(row)}) "
                           f"VALUES ({','.join('?' for _ in row)})", tuple(row.values()))
        with pytest.raises(ValueError, match="Invalid isoformat string"):
            scoring.score_rows(connection, vault, repository)
