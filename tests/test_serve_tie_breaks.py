"""Once the difficulty label is retired an LO's items predict alike, so ties are the ordinary case on the serve path.
Every tie must break the same way on every run: on a total order of persisted identifiers, or by a seeded draw whose
seed names a persisted decision and is recorded with what it drew. A delayed check's pick among tied items is such a
draw (seeded on the decision it measures, its tied set, seed, draw and propensity on the receipt)."""

from __future__ import annotations

import itertools
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from learnloop import delayed_checks as D
from learnloop.algorithm_versions import LABEL_RETIRED_ALGORITHM_VERSION
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.difficulty_replay_helpers import build_vault

ROOT = Path(__file__).resolve().parents[1]


def test_a_delayed_picks_tie_is_one_answer_in_any_candidate_order_and_replays_from_its_receipt(tmp_path):
    paths = build_vault(tmp_path / "vault", version=LABEL_RETIRED_ALGORITHM_VERSION)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    items = sorted((item for item_id, item in vault.practice_items.items() if item_id.startswith("pi_eig_")),
                   key=lambda item: item.id)
    assert len(items) >= 3
    outcomes = {}
    for order in itertools.permutations(items):
        item, receipt = D.pick_with_receipt(vault, repository, list(order), seed_key="decision:one")
        outcomes[tuple(entry.id for entry in order)] = (item.id, json.dumps(receipt, sort_keys=True))
    assert len(set(outcomes.values())) == 1
    item_id, receipt = next(iter(outcomes.values()))
    receipt = json.loads(receipt)
    # Every item ties without a label; the receipt replays the draw.
    assert receipt["tied"] == sorted(receipt["tied"]) and receipt["n"] == len(items)
    assert receipt["seed"] == D.seed_for("decision:one") and receipt["propensity"] == pytest.approx(1 / len(items))
    assert receipt["tied"][min(int(receipt["draw"] * receipt["n"]), receipt["n"] - 1)] == item_id == receipt["chosen"]


@pytest.mark.slow
def test_the_served_day_is_one_answer_under_two_hash_seeds_and_reversed_row_order(tmp_path):
    """The staged pick inside the objective, every served step and every measurement's pick, over one day at the head,
    in three processes: hash seeds 0 and 1, and hash seed 0 with SQLite returning unordered rows in reverse."""

    runs = {}
    for name, seed, extra in (("seed0", "0", []), ("seed1", "1", []),
                              ("reversed", "0", ["--reverse-unordered-selects"])):
        out = tmp_path / f"{name}.json"
        env = {**os.environ, "PYTHONHASHSEED": seed}
        done = subprocess.run([sys.executable, "-m", "tests.serve_determinism_helpers", str(tmp_path / name), str(out),
                               *extra], cwd=ROOT, env=env, capture_output=True, text=True, timeout=600)
        assert done.returncode == 0, done.stderr[-4000:]
        runs[name] = json.loads(out.read_text(encoding="utf-8"))
    assert runs["seed0"]["picks"] and runs["seed0"]["steps"]
    assert any(len(tied) > 1 for tied, _chosen in runs["seed0"]["measured"]), "the day met no tie"
    assert runs["seed0"] == runs["seed1"] == runs["reversed"]
