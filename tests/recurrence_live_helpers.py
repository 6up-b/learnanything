"""What other test files use from ``tests/test_recurrence_live.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.vault.loader import load_vault

from tests.split_live_helpers import enable_embeddings, split_vault


V_SAME = "Believes V and V transpose are the same matrix."
V_REWORDED = "Thinks the last SVD factor never needs transposing."
V_THIRD = "Writes V where the transpose of V belongs."
STATEMENTS = {"first": V_SAME, "second": V_REWORDED, "third": V_THIRD}


def _vault(tmp_path, *, version="mvp-0.12", config: str = ""):
    paths, _vault, repository = split_vault(tmp_path, version=version, seed=False, config=config)
    enable_embeddings(paths.root)
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text(encoding="utf-8").replace("dimensions = 4096", "dimensions = 16"), encoding="utf-8")
    return paths, load_vault(paths.root), repository


def _heads(repository, attempt_id):
    return [row for row in repository.causal_hypotheses_for_attempt(attempt_id)
            if row["status"] != "open_set" and row["cause_scope"] == "learner_state"]
