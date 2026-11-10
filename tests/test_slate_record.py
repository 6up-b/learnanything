"""Refactor B6 (ADR-017): the slate's decision record, and the two meanings of ``decision_receipt_id``.

What each group pins:

* one ``slate`` record per persisting queue build: the head and the rule that put it first, the ranked candidates
  after it with their reward and propensity, and every candidate the build kept off the slate, counted by rule with
  up to ten ids each, including the composition's and the cold lane's; a placement check's unusable candidates
  by rule (the map's S15); ids, numbers and codes only;
* reads write none: a build with ``persist_explanations=False`` (``why``, the knowledge map, the facet chart, the
  staged comparator, the simulator) leaves no record;
* a record never changes what is served: with the write failing the queue is the same, and a warning names the
  trace;
* ``why``: ``slate:<id>`` reads the record; ``item:<id>`` says which slates named the item and, off today's slate,
  the rule keeping it off (fail-first: before B6 an excluded item had no answer, ``why item:<id>`` exited
  ``not_found``).
"""

from __future__ import annotations

import json
import logging
from datetime import timedelta
from types import SimpleNamespace

from typer.testing import CliRunner

from learnloop import provenance
from learnloop.clock import FrozenClock
from learnloop.content.authoring.item_authoring import retire_item
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.scheduling import slate_record
from learnloop.scheduling.scheduler import SchedulerSession, build_due_queue, explain_practice_item
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from tests.helpers import NOW, create_placement_vault


def _at(minutes: float) -> FrozenClock:
    return FrozenClock(NOW + timedelta(minutes=minutes))


def _setup(tmp_path, name: str = "vault"):
    paths = create_placement_vault(tmp_path / name)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return paths, vault, repository


def _retire(paths, repository, item_id: str):
    retire_item(paths.root, repository, practice_item_id=item_id, reason="ambiguous", clock=_at(1))
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(1))
    return vault


def _records(paths) -> list[provenance.DecisionRecord]:
    """Every slate record, oldest first."""

    with connect(paths.sqlite_path, read_only=True) as connection:
        ids = [row[0] for row in connection.execute(
            "SELECT id FROM decision_records WHERE kind = 'slate' ORDER BY created_at, id")]
        return [next(record for record in provenance.read(connection, record_id) if record.id == record_id)
                for record_id in ids]


def _all_records(paths) -> list[tuple]:
    with connect(paths.sqlite_path, read_only=True) as connection:
        return [tuple(row) for row in connection.execute("SELECT id, kind FROM decision_records")]


def _slate_id(paths, session_id: str) -> str:
    with connect(paths.sqlite_path, read_only=True) as connection:
        return connection.execute(
            "SELECT id FROM scheduler_slates WHERE session_id = ? ORDER BY created_at DESC, id DESC LIMIT 1",
            (session_id,),
        ).fetchone()[0]


# -- the record ----------------------------------------------------------------------------------------------


def test_a_persisting_build_writes_one_slate_record_with_its_exclusions(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    vault = _retire(paths, repository, "pi_eig_hard")
    with provenance.trace_scope("TRACE_SLATE"):
        queue = build_due_queue(vault, repository, clock=_at(5), session=SchedulerSession(session_id="s1"), limit=2)
    assert queue, "sanity: new material is served"
    slate_id = _slate_id(paths, "s1")
    with connect(paths.sqlite_path, read_only=True) as connection:
        (record,) = provenance.read(connection, f"slate:{slate_id}")
    assert (record.kind, record.status, record.trace_id) == ("slate", "chosen", "TRACE_SLATE")
    assert (record.detail_table, record.detail_id, record.subject_kind) == ("scheduler_slates", slate_id, "slate")
    assert record.chosen_ref == queue[0].practice_item_id
    assert record.decided_by == "composed_offer_v2" and record.rule in {"greedy_order", "composition_order"}
    assert record.versions["algorithm_version"] == vault.config.algorithms.algorithm_version
    facts = record.facts
    assert facts["served_n"] == 2 and facts["limit"] == 2 and facts["session_id"] == "s1"
    # Every candidate after the head, in the composed order: the returned ones ranked below, the rest past the limit.
    assert [a["lost_by"] for a in record.alternatives] == (
        ["ranked_below"] + ["beyond_limit"] * (facts["considered_n"] - 2))
    assert all(isinstance(a["score"], float) and isinstance(a["p"], float) for a in record.alternatives)
    assert facts["exclusions"]["retired"] == {"n": 1, "ids": ["pi_eig_hard"]}
    assert facts["excluded_n"] == sum(entry["n"] for entry in facts["exclusions"].values())
    assert provenance.check_no_prose(record) == []
    text = json.dumps(record.as_dict())
    for item in vault.practice_items.values():
        assert item.prompt not in text


def test_reads_write_no_slate_record(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    session = SchedulerSession(session_id="s_read")
    assert build_due_queue(vault, repository, clock=_at(5), session=session, persist_explanations=False)
    build_due_queue(vault, repository, clock=_at(5), persist_explanations=False)
    explain_practice_item(vault, repository, "pi_eig_easy")
    assert _all_records(paths) == []
    # The same build persisting writes exactly one.
    build_due_queue(vault, repository, clock=_at(5), session=session)
    assert [kind for _id, kind in _all_records(paths)] == ["slate"]


def test_a_record_that_cannot_be_written_changes_nothing_served(tmp_path, monkeypatch, caplog):
    import learnloop.db.stores.provenance as store

    served = []
    for name, broken in (("kept", False), ("broken", True)):
        paths, vault, repository = _setup(tmp_path, name)
        vault = _retire(paths, repository, "pi_eig_hard")
        if broken:
            def refused(*_args, **_kwargs):
                raise RuntimeError("the record store is down")

            monkeypatch.setattr(store, "write_decision", refused)
        with provenance.trace_scope(f"TRACE_{name.upper()}"), caplog.at_level(logging.WARNING):
            queue = build_due_queue(vault, repository, clock=_at(5), session=SchedulerSession(session_id="s1"))
        served.append([(s.practice_item_id, s.priority, s.selected_mode, s.components) for s in queue])
        assert [kind for _id, kind in _all_records(paths)] == ([] if broken else ["slate"])
    assert served[0] == served[1]
    assert "decision record 'slate' not written (trace TRACE_BROKEN): RuntimeError" in caplog.text


def test_a_placement_check_records_why_its_lo_items_were_not_candidates(tmp_path):
    """S15: the first-review check is chosen among an LO's items; the ones it could not be chosen from are named."""

    from learnloop.placement.decisions import record_self_report

    paths, vault, repository = _setup(tmp_path)
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1))
    repository.create_followup_task(
        kind="cold_retry", case_kind="diagnosis", case_ref="case-1",
        not_before="2026-07-01T00:00:00Z", selected_item_id="pi_diag_mid", clock=_at(2),
    )
    queue = build_due_queue(vault, repository, clock=_at(14 * 24 * 60 + 5), session=SchedulerSession(session_id="s2"))
    assert [s.practice_item_id for s in queue if s.components.get("assumed_check")] != ["pi_diag_mid"]
    (record,) = _records(paths)
    assert record.facts["placement_check_exclusions"]["out_of_timing"] == {"n": 1, "ids": ["pi_diag_mid"]}
    # Off the slate itself by the assumed LO's withholding; why it was not the check is the placement fact above.
    assert slate_record.item_outcome(record, "pi_diag_mid") == "placement_assumed_withheld"


def test_exclusions_are_counted_by_rule_with_ten_ids_each():
    summary = slate_record.by_rule({
        "retired": [f"pi_{index:02d}" for index in range(25)] + ["pi_00"],
        "zero_priority": [],
        "lifecycle_put_away": ["an item id with spaces", "pi_ok"],
    })
    assert summary["retired"] == {"n": 25, "ids": [f"pi_{index:02d}" for index in range(10)]}
    assert "zero_priority" not in summary
    # A free-form vault id a record cannot carry is counted, never named, so it never drops the record.
    assert summary["lifecycle_put_away"] == {"n": 2, "ids": ["pi_ok"], "unnamed": 1}


def test_the_composition_and_the_cold_lane_are_exclusions_too():
    merged = slate_record.merged_exclusions(
        {"retired": ["pi_r"]}, greedy_ids=["pi_a", "pi_tb", "pi_b"], considered_ids=["pi_a", "pi_b", "pi_f"],
        teach_back_rule=slate_record.TEACH_BACK_VALUE, cold_deferrals=[{"practice_item_id": "pi_cold"}],
    )
    assert merged == {"retired": ["pi_r"], "teach_back_value_below_minutes_cost": ["pi_tb"],
                      "cold_followup_deferred": ["pi_cold"]}


def test_the_rule_that_put_the_head_first():
    def item(item_id, **components):
        return SimpleNamespace(practice_item_id=item_id, components=components, priority=0.5)

    rule = slate_record.head_rule
    assert rule(None, pinned_item_id=None, check_item_ids=(), greedy_head_id=None) == "empty_slate"
    assert rule(item("a"), pinned_item_id="a", check_item_ids=(), greedy_head_id="b") == "presentation_pin"
    assert rule(item("a", intervention_followup=1.0), pinned_item_id=None, check_item_ids=(),
                greedy_head_id="b") == "pending_followup"
    assert rule(item("a"), pinned_item_id=None, check_item_ids=("a",), greedy_head_id="b") == "check_once"
    assert rule(item("a", exploration_selected=1.0), pinned_item_id=None, check_item_ids=(),
                greedy_head_id="b") == "seeded_exploration"
    assert rule(item("a"), pinned_item_id=None, check_item_ids=(), greedy_head_id="a") == "greedy_order"
    assert rule(item("a"), pinned_item_id=None, check_item_ids=(), greedy_head_id="b") == "composition_order"
    record = slate_record.slate_record(
        served=[item("odd id")], considered=[item("odd id"), item("pi_b")], greedy=[item("odd id")],
        exclusions={}, placement_check_exclusions={}, propensity={}, limit=None, slate_id=None, session_id=None,
        pinned_item_id=None, check_item_ids=(), probe_block_reason=None, algorithm_version="mvp-0.57",
        selection_policy="composed_offer_v2",
    )
    assert record.chosen_ref is None and record.facts["chosen_unnamed"] is True
    assert provenance.check_no_prose(record) == []


def test_a_recorded_slate_keeps_ten_alternatives_and_counts_the_rest():
    """Storage: the slate row holds every candidate, so the record keeps the nearest ten (50 without a slate row)."""

    def item(index):
        return SimpleNamespace(practice_item_id=f"pi_{index:02d}", components={"selection_reward": 1.0 / (index + 1)},
                               priority=0.5)

    considered = [item(index) for index in range(30)]
    common = dict(considered=considered, greedy=considered, exclusions={}, placement_check_exclusions={},
                  propensity={}, session_id="s1", pinned_item_id=None, check_item_ids=(), probe_block_reason=None,
                  algorithm_version="mvp-0.57", selection_policy="composed_offer_v2")
    with_row = slate_record.slate_record(served=considered[:5], limit=5, slate_id="SLATE1", **common)
    assert [a["ref"] for a in with_row.alternatives] == [f"pi_{index:02d}" for index in range(1, 11)]
    assert with_row.facts["alternatives_overflow"] == {"beyond_limit": 19}
    without_row = slate_record.slate_record(served=considered[:5], limit=5, slate_id=None, **common)
    assert len(without_row.alternatives) == 29 and "alternatives_overflow" not in without_row.facts


# -- why -----------------------------------------------------------------------------------------------------


def test_why_names_the_rule_that_kept_an_item_off_the_slate(tmp_path):
    """Fail-first: before B6 ``why item:<id>`` for an excluded item exited ``not_found``: nothing said why."""

    from learnloop.cli import app

    paths, vault, repository = _setup(tmp_path)
    vault = _retire(paths, repository, "pi_eig_hard")
    build_due_queue(vault, repository, clock=_at(5), session=SchedulerSession(session_id="s1"))
    slate_id = _slate_id(paths, "s1")
    runner = CliRunner()
    result = runner.invoke(app, ["why", "item:pi_eig_hard", "--json", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["excluded_now"] == "retired"
    assert [(s["slate_id"], s["outcome"]) for s in payload["slates"]] == [(slate_id, "retired")]
    served = runner.invoke(app, ["why", "slate:" + slate_id, "--json", "--vault", str(paths.root)])
    records = json.loads(served.output)["records"]
    assert [r["kind"] for r in records] == ["slate"] and records[0]["detail_id"] == slate_id
    head = records[0]["chosen_ref"]
    on_slate = json.loads(runner.invoke(app, ["why", f"item:{head}", "--json", "--vault", str(paths.root)]).output)
    assert on_slate["source"] == "current" and "excluded_now" not in on_slate
    assert on_slate["slates"][0]["outcome"] == "chosen"
