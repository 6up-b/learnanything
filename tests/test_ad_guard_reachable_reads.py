"""Every table AD's reachable code can read is classified (the reachable-reads audit, 2026-10-27).

The owner's probability vault failed ``upgrade --to mvp-0.35`` because field's serving attribution,
run inside the AD material view's rules, read ``scheduler_offer_receipts``, a table the AD guard's
registry had not classified, on a branch (an attempt bound to a non-forced slate candidate) that no
test vault took. Two checks close the class:

* **static, over the code that runs**: every ``learnloop`` function called while an AD operation
  is open, over AD's whole pipeline (the contract harness: every entry point) and over a vault that
  takes every branch of field's serving attribution, names (on any branch) only tables the registry
  classifies (:mod:`tests.ad_reachable_reads`). Its negative control: the pipeline alone, whose
  vault never takes the learner-pick branch, still names ``scheduler_offer_receipts`` through
  ``field.outcomes._serving``, so the scan would have caught this table before the owner's vault did;
* **dynamic, every branch**: over that vault, the AD replayer (``rebuild-derived-state``), the
  serve's snapshot, the prequential arms and ``ad report`` run with zero guard denials, and the
  view's attempt rows carry field's own serving labels (each one of the branches).

Fakes only: no network, no model call.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing

import pytest

from learnloop.adaptive_difficulty import operation as O
from learnloop.adaptive_difficulty import protected_tables as T
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import ad23_vault, answer, env_for
from tests.ad_reachable_reads import Reached, schema_tables
from tests.test_ad_guard_offer_receipts import AT, seed_learner_pick

ITEMS = ("pi_e1", "pi_e2", "pi_e3")
#: Every serving label field's attribution gives (``field.outcomes._serving``).
LABELS = {"learner_pick", "forced_followup", "system_probe", "daily_plan", "unknown"}


@pytest.fixture
def observed(monkeypatch):
    seen: list[O.Operation] = []
    monkeypatch.setattr(O, "OBSERVERS", [seen.append])
    return seen


def _probe(paths, attempt_id: str, item_id: str) -> None:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO probe_episodes(id, learning_object_id, status, trigger, algorithm_version, created_at, "
            "updated_at) VALUES ('episode', (SELECT learning_object_id FROM practice_attempts WHERE id = ?), "
            "'complete', 'initial', 'test', ?, ?)", (attempt_id, AT, AT))
        connection.execute(
            "INSERT INTO probe_presentations(id, probe_episode_id, practice_item_id, state_segment_id, status, "
            "created_at, updated_at) VALUES ('presentation', 'episode', ?, 'segment', 'submitted', ?, ?)",
            (item_id, AT, AT))
        connection.execute(
            "UPDATE practice_attempts SET probe_presentation_id = 'presentation', "
            "collection_version = 'learnloop-events-v1' WHERE id = ?", (attempt_id,))
        connection.commit()


def every_branch_vault(tmp_path):
    """An AD vault whose attempts take every branch of field's serving attribution: a pick from a
    published offer, a slate candidate with no published offer, a forced follow-up, a system probe,
    a plan serve, and a legacy (unversioned) attempt. Returns the paths and attempt -> branch."""

    from learnloop.daily_plan.engine import advance, build_plan

    paths = ad23_vault(tmp_path, items=ITEMS, config="[router]\nenabled = false\n")
    env, clock = env_for(paths, items=ITEMS)
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    _record, step = advance(env, serve=True)
    assert step["kind"] == "item"
    clock.advance(2)
    branches = {answer(paths, step["practice_item_id"], presentation_id=step["presentation_id"], clock=clock):
                "plan"}
    for tag, item, kwargs in (("a", "pi_e1", {}), ("b", "pi_e2", {"offered": False}),
                              ("c", "pi_e3", {"components": {"intervention_followup": 1}})):
        clock.advance(2)
        attempt = answer(paths, item, correct=tag != "b", clock=clock)
        seed_learner_pick(paths, attempt, item, tag=tag, **kwargs)
        branches[attempt] = {"a": "pick", "b": "unpublished", "c": "forced"}[tag]
    clock.advance(2)
    probed = answer(paths, "pi_e2", clock=clock)
    _probe(paths, probed, "pi_e2")
    branches[probed] = "probe"
    clock.advance(2)
    legacy = answer(paths, "pi_e3", correct=False, clock=clock)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE practice_attempts SET collection_version = 'legacy-unversioned' WHERE id = ?",
                           (legacy,))
        connection.commit()
    branches[legacy] = "legacy"
    return paths, branches


def _run_every_reader(paths) -> None:
    """Every AD reader of field's rows over ``paths``: the replayer through the whole rebuild, the
    serve's snapshot, the prequential arms and the report."""

    from learnloop.adaptive_difficulty import replay as RP
    from learnloop.adaptive_difficulty.report import build
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    rebuild_all_derived_state(load_vault(paths.root), Repository(paths.sqlite_path))
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    RP.clear_cache()
    RP.snapshot(vault, repository)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        build(vault, repository, connection, sensitivity=False)


def test_every_serving_branch_runs_with_zero_denials_and_fields_labels(tmp_path, observed):
    from learnloop.adaptive_difficulty.material_view import material_view
    from learnloop.field.outcomes import load_attempt_rows

    paths, branches = every_branch_vault(tmp_path)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        outside = {row.attempt_id: row.serving_origin for row in load_attempt_rows(connection, vault)}
    assert set(outside) == set(branches)
    labels = {branches[attempt]: label for attempt, label in outside.items()}
    assert labels["pick"] == "learner_pick" and labels["forced"] == "forced_followup"
    assert labels["probe"] == "system_probe" and labels["plan"] == "daily_plan" and labels["legacy"] == "unknown"
    assert set(outside.values()) == LABELS
    with O.ad_operation(vault, repository, read_only=True) as op:
        inside = {row.attempt_id: row.serving_origin
                  for row in material_view(op.vault, op.repository).field_rows(repository.connection())}
    assert inside == outside
    _run_every_reader(paths)
    assert [denial for op in observed for denial in op.guard.denials] == []
    assert O.denial_count(paths.sqlite_path) == 0
    entries = {op.guard.entry for op in observed}
    assert any("replay.load_events" in entry for entry in entries), sorted(entries)
    assert any("report.build" in entry for entry in entries), sorted(entries)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        traced = {str(row[0]) for row in connection.execute("SELECT DISTINCT attempt_id FROM ad_attempt_trace")}
    assert traced, "the replayer wrote AD's trace"


def _unclassified(named: dict[str, set[str]]) -> dict[str, list[str]]:
    return {table: sorted(where) for table, where in sorted(named.items()) if table not in T.ROLES}


#: The functions that run inside an operation OUTSIDE the rules and whose own SQL names a table
#: that is neither neutral nor AD's own, each reviewed (the reachable-reads audit, 2026-10-27): a
#: raw read there would be refused and poison the operation, so each must never take that branch
#: inside one. A function added here names why.
UNRULED_REVIEWED: dict[str, str] = {
    "learnloop.db.repositories:Repository.mastery_states":
        "the named carve-out (CARVE_OUTS: AD1's mastery_ekf comparator, learnloop.adaptive_difficulty.forecasters)",
    "learnloop.db.repositories:Repository.item_parameter_states":
        "the named carve-out (CARVE_OUTS: AD1's mastery_ekf comparator, learnloop.adaptive_difficulty.forecasters)",
    "learnloop.daily_plan.estimates:load_duration_evidence":
        "the incumbent's branch: AD passes its material view's attempt rows, so the raw SELECT never runs in AD",
    "learnloop.daily_plan.estimates:_feedback_dwell":
        "the incumbent's branch: AD passes its material view's block events, so the raw SELECT never runs in AD",
}


def _unruled_unreviewed(reached: Reached, tables: set[str]) -> dict[str, list[str]]:
    named = reached.named_tables(tables, unruled=True)
    out = {}
    for table, where in sorted(named.items()):
        role = T.ROLES.get(table)
        if role == T.NEUTRAL or table in T.AD_WRITABLE:
            continue  # metadata readable raw; AD's own tables (their writes judged by the write rules)
        rest = sorted(function for function in where if function not in UNRULED_REVIEWED)
        if rest:
            out[table] = rest
    return out


def test_every_table_the_code_running_inside_an_operation_names_is_classified(tmp_path, monkeypatch):
    """Static over the code that runs (see the module docstring). Failed before this fix on
    ``scheduler_offer_receipts`` (``field.outcomes._serving``) and ``grader_calibration_alphas``
    (``Repository.calibration_alphas_by_model_ids``: a legacy grade interpretation's pooled alphas,
    read by field's effective observations inside the rules), and, outside the rules, on
    ``raw_grade_events`` (``Repository.raw_grade_events_by_ids``: the replay resolved the grades'
    measurement masses outside the view)."""

    from tests import test_ad23_contract as C

    protected, _absent = C.make_copies(tmp_path / "pipeline", coupled=False)
    C._hold_out(monkeypatch)
    C._deterministic(monkeypatch)
    C._carve_outs(monkeypatch)
    tables = schema_tables(protected.sqlite_path)
    pipeline = Reached()
    with pipeline.recording():
        C._run_at_common_root(protected, monkeypatch)
    named = pipeline.named_tables(tables)
    assert len(pipeline.functions) > 100 and "practice_attempts" in named, "the profiler saw AD's code run"
    # The negative control: this vault takes no learner-pick branch, yet the scan names the table.
    assert "learnloop.field.outcomes:_serving" in named.get("scheduler_offer_receipts", set())
    assert "learnloop.db.repositories:Repository.calibration_alphas_by_model_ids" in named.get(
        "grader_calibration_alphas", set())
    assert _unclassified(named) == {}
    assert _unruled_unreviewed(pipeline, tables) == {}

    branches_paths, _branches = every_branch_vault(tmp_path / "branches")
    every = Reached()
    with every.recording():
        _run_every_reader(branches_paths)
    branch_tables = schema_tables(branches_paths.sqlite_path)
    assert _unclassified(every.named_tables(branch_tables)) == {}
    assert _unruled_unreviewed(every, branch_tables) == {}
    reviewed = {function for table in branch_tables | tables
                for function in pipeline.named_tables(tables, unruled=True).get(table, set())
                | every.named_tables(branch_tables, unruled=True).get(table, set())}
    assert set(UNRULED_REVIEWED) <= reviewed, "a reviewed function no longer runs there: drop it"


def test_the_scan_reports_a_table_the_registry_drops(tmp_path, monkeypatch):
    """The check's own negative control: with ``scheduler_offer_receipts`` taken out of the
    registry the scan reports it, by the function that names it."""

    paths, _branches = every_branch_vault(tmp_path)
    reached = Reached()
    with reached.recording():
        _run_every_reader(paths)
    named = reached.named_tables(schema_tables(paths.sqlite_path))
    monkeypatch.setattr(T, "ROLES", {table: role for table, role in T.ROLES.items()
                                     if table != "scheduler_offer_receipts"})
    assert "learnloop.field.outcomes:_serving" in _unclassified(named)["scheduler_offer_receipts"]


def test_the_scan_reads_sql_and_composed_table_names():
    """The static scan's own rules: a table after FROM or JOIN, a constant that is a table's name
    (a composed statement's table), a module-level string a function names; never a module's body."""

    import types

    from tests import ad_reachable_reads as A

    source = (
        "TABLE = 'gamma'\n"
        "def f(c):\n"
        "    c.execute('SELECT x FROM alpha a JOIN beta b ON a.id = b.id')\n"
        "    for t in ('delta',):\n"
        "        c.execute(f'SELECT * FROM {t}')\n"
        "    return TABLE, (lambda: c.execute('select 1 from epsilon'))\n"
        "def never(c):\n"
        "    c.execute('SELECT 1 FROM zeta')\n"
    )
    module = types.ModuleType("scan_probe")
    code = compile(source, str(A.SRC / "scan_probe.py"), "exec")
    exec(code, module.__dict__)  # noqa: S102 - the scan's own fixture
    reached = A.Reached()
    reached.functions[module.f.__code__] = module.__dict__
    reached.functions[code] = module.__dict__  # the module body: defines ``never``, which never ran
    named = reached.named_tables({"alpha", "beta", "gamma", "delta", "epsilon", "zeta"})
    assert set(named) == {"alpha", "beta", "gamma", "delta", "epsilon"}
    assert json.dumps(sorted(named["alpha"])) == '["scan_probe:f"]'


def test_a_legacy_grade_interpretation_reads_its_pooled_alphas_with_zero_denials(tmp_path, observed):
    """The scan's second finding, taken: an interpretation recorded before the shared certainty LCB
    was persisted (``shared_certainty_lcb`` NULL) has its calibration model's pooled alphas read by
    field's effective observations, inside the rules (``grader_calibration_alphas``). Failed
    before: the unclassified table poisoned the replay."""

    from learnloop.adaptive_difficulty import replay as RP

    paths, _branches = every_branch_vault(tmp_path)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        model = connection.execute(
            "SELECT model_id FROM grader_calibration_alphas ORDER BY model_id LIMIT 1").fetchone()
        assert model is not None, "the vault's heuristic grader models carry alphas"
        changed = connection.execute(
            "UPDATE grade_interpretations SET shared_certainty_lcb = NULL, calibration_model_id = ?, "
            "reference_prior_ids_json = ?", (model[0], json.dumps([model[0]]))).rowcount
        connection.commit()
    assert changed > 0, "the vault's graded attempts carry interpretations"
    RP.snapshot(load_vault(paths.root), Repository(paths.sqlite_path))
    assert [denial for op in observed for denial in op.guard.denials] == []
