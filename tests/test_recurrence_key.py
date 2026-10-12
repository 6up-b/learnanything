"""Slice 1 §7.6: the behaviour-neutral recurrence-key seam Slice 2 T1 swaps."""

from __future__ import annotations

import pytest

from learnloop.diagnosis import causal_factor_deferral
from learnloop.recurrence import RECURRENCE_KEY_VERSION, recurrence_key

from tests.diagnosis_split_helpers import build_diagnosis_vault, seed_history


def test_the_seam_is_the_exact_statement_key_in_slice_1():
    assert RECURRENCE_KEY_VERSION == "statement-normalized-v1"
    assert recurrence_key({"statement_normalized": "x y"}) == "x y"
    assert recurrence_key({"statement_normalized": None}) == ""
    assert causal_factor_deferral.recurrence_key is recurrence_key


@pytest.fixture
def seeded(tmp_path):
    paths = build_diagnosis_vault(tmp_path / "vault")
    _vault, repository = seed_history(paths)
    return repository


def test_candidate_projection_groups_through_the_seam(seeded, monkeypatch):
    repository = seeded
    lo = "lo_svd_compute"
    exact = repository._projected_causal_candidates(lo)
    # Behaviour-neutral: the same statements, the same groups.
    assert {row["statement_normalized"] for row in exact}
    # Swapping the seam (what T1 will do) regroups every caller at once.
    monkeypatch.setattr("learnloop.db.repositories.recurrence_key", lambda _row: "one-group")
    merged = repository._projected_causal_candidates(lo)
    assert len(merged) == 1
    assert merged[0]["occurrence_count"] == sum(row["occurrence_count"] for row in exact)
    assert repository.misconception_candidate_by_normalized(lo, "one-group") is not None
    heads = repository.causal_hypotheses_for_learning_object(lo, statement_normalized="one-group")
    assert heads and all(row["learning_object_id"] == lo for row in heads)


def test_factor_signature_counts_through_the_seam(seeded, monkeypatch):
    repository = seeded
    calls: list[str] = []

    def spy(row):
        calls.append(str(row.get("id")))
        return "key"

    monkeypatch.setattr(causal_factor_deferral, "recurrence_key", spy)
    factor = {"hypothesis_refs": [], "candidate_causes": []}
    hypotheses = repository.causal_hypotheses_for_attempt("att_02_svd_fail")
    refs = [{"hypothesis_id": row["id"], "version": row["version"]} for row in hypotheses]
    statements, _lo = causal_factor_deferral._factor_signature(
        repository, {**factor, "hypothesis_refs": refs, "candidate_causes": refs}
    )
    assert refs
    assert statements == {"key"} and calls
