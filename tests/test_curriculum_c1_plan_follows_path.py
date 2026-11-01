"""Curriculum C1: the plan follows the deliverable (spec_deliverable_curriculum_v1 §7.6, §8.1; G-C4).

Scratch exploration (replaced below).
"""
from __future__ import annotations

import json

from learnloop.algorithm_versions import DELIVERABLE_PLAN_ALGORITHM_VERSION
from learnloop.daily_plan import engine as E
from learnloop.source_retrieval import deliverable_path as DP
from learnloop.source_retrieval import deliverables as DL
from learnloop.vault.loader import load_vault
from tests.deliverable_fixtures import DeliverableFake, build_deliverable_vault, cover_all
from tests.helpers import append_config_toml, set_algorithm_version
from tests.reading_path_fixtures import FixedClock, call, context

TAG = DELIVERABLE_PLAN_ALGORITHM_VERSION


def test_explore(tmp_path, monkeypatch):
    FixedClock(monkeypatch)
    paths, repository = build_deliverable_vault(tmp_path / "v", prerequisite=True)
    set_algorithm_version(paths, TAG)
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO synthesis_manifests(id, manifest_hash, extraction_ids_json, brief_json, created_at) "
            "VALUES ('man_c1', 'hash_c1', ?, ?, '2026-10-01T09:00:00Z')",
            (json.dumps(["ext_book"]), json.dumps({"practice_items": "as_you_read"})))
        connection.execute(
            "INSERT INTO synthesis_runs(id, manifest_id, mode, status, created_at, completed_at) "
            "VALUES ('run_c1', 'man_c1', 'bootstrap', 'completed', '2026-10-01T09:00:00Z', '2026-10-01T09:05:00Z')")
        connection.commit()
    cover_all(paths, repository, "lo_eigen", "lo_det")
    vault = load_vault(paths.root)
    print("plan active", E.plan_active(vault), E.reading_path_plan_active(vault), E.deliverable_plan_active(vault))
    goal_id = DL.create_deliverable(vault, repository, "eigenvalues for my midterm")["goal_id"]
    DL.resolve(load_vault(paths.root), repository, goal_id, client=DeliverableFake())
    DL.add_input(load_vault(paths.root), repository, goal_id, "depth", text="learn_to_use_it")
    vault = load_vault(paths.root)
    r = DP.judge(vault, repository, goal_id, client=DeliverableFake(primaries={"Eigenvalues": "5.2 The characteristic equation"}))
    print(r)
    p = DP.deliverable_plan_path(load_vault(paths.root), repository, DL.goal_of(load_vault(paths.root), goal_id))
    print(p.status, [ (s.learning_object_id, s.extraction_id, s.section_id, s.label) for s in p.lines])
    plan = call(context(paths.root), "get_daily_plan", {})
    with repository.connection() as connection:
        split = json.loads(connection.execute("SELECT split_json FROM daily_plans").fetchone()[0])
    print(json.dumps(split.get("reading"), indent=1), json.dumps(split.get("reading_path"), indent=1))
    assert False
