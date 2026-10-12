"""The generic shortlist + judge + ledger step (Slice 2 R4, parameterized by kind)."""

from __future__ import annotations

from contextlib import closing

import numpy as np
import pytest

from learnloop.ai.spend import SpendLimitExceeded
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.embedding_vectors import put_vector
from learnloop.matching import MatchKind, SameOrDifferent, Subject, judge_pairs, shortlist_pairs
from learnloop.matching.judge import pair_input_hash, pair_prompt

from tests.helpers import create_basic_vault

#: A kind that knows nothing about misconceptions: two learning objectives.
KIND = MatchKind(
    name="same objective", task="same_objective_test", subject_kind="objective", record_kind="objective",
    field="statement", task_prefix="similarity", route="authoring", purpose="same_objective_test",
    prompt_version="test-v1", question="Do these name the same objective?", guidance="Wording may differ.",
)
MODEL = "test/embedder"


def _subject(identifier, text, created="2026-01-01"):
    return Subject(kind="objective", id=identifier, text=text, content_hash=f"h-{identifier}", created_at=created,
                   scope={"group": "g"}, view={"statement": text})


@pytest.fixture
def repository(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    return Repository(paths.sqlite_path)


def _store(repository, subjects_and_vectors):
    with closing(connect(repository.sqlite_path)) as connection, connection:
        for subject, vector in subjects_and_vectors:
            put_vector(connection, record_kind=KIND.record_kind, record_id=subject.id, field=KIND.field,
                       content_hash=subject.content_hash, model_id=MODEL, task_prefix=KIND.task_prefix,
                       vector=np.asarray(vector, dtype=float))


def test_shortlist_takes_top_k_skips_settled_and_applies_only_a_given_cutoff(repository):
    query = _subject("q", "query", created="2026-02-01")
    near, mid, far, settled, missing = (_subject(name, name) for name in ("near", "mid", "far", "settled", "missing"))
    _store(repository, [
        (query, [1.0, 0.0, 0.0, 0.1]), (near, [0.9, 0.1, 0.0, 0.0]), (mid, [0.5, 0.5, 0.0, 0.0]),
        (far, [-1.0, 0.0, 0.2, 0.0]), (settled, [1.0, 0.0, 0.0, 0.0]),
    ])
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        result = shortlist_pairs(
            connection, KIND, queries=[query], pool=[near, mid, far, settled, missing], model_id=MODEL, top_k=2,
            cutoff=None, compatible=lambda q, c: True, settled=lambda q, c: c.id == "settled",
        )
        assert [pair.right.id for pair in result.pairs] == ["near", "mid"]
        assert [pair.rank for pair in result.pairs] == [1, 2]
        assert result.skipped_settled == 1 and result.pool_with_vector == 4
        assert result.summary()["cutoff_basis"] == "top_k_only"
        cut = shortlist_pairs(
            connection, KIND, queries=[query], pool=[near, mid, far], model_id=MODEL, top_k=3,
            cutoff=0.9, compatible=lambda q, c: True,
        )
        # Below the cutoff a pair never reaches the judge; nothing is decided.
        assert [pair.right.id for pair in cut.pairs] == ["near"] and cut.below_cutoff == 2
        none = shortlist_pairs(connection, KIND, queries=[missing], pool=[near], model_id=MODEL, top_k=3, cutoff=None,
                               compatible=lambda q, c: True)
        assert none.pairs == [] and none.queries_without_vector == 1


class _Judge:
    provider_type = "fake"
    provider_name = "fake"
    model = "fake"

    def __init__(self, verdicts):
        self.verdicts = list(verdicts)

    def __call__(self, prompt, model, purpose):
        assert purpose == KIND.purpose and KIND.prompt_version in prompt
        verdict = self.verdicts.pop(0)
        if isinstance(verdict, BaseException):
            raise verdict
        return SameOrDifferent(verdict=verdict, rationale="because"), "fake-judge"


def _pairs(*names):
    from learnloop.matching import CandidatePair

    base = _subject("base", "base")
    return [CandidatePair(left=_subject(name, name, created="2026-02-01"), right=base, score=0.5, rank=1, model_id=MODEL)
            for name in names]


def test_every_verdict_goes_to_the_ledger_once(repository):
    judge = _Judge(["same", "different"])
    results = judge_pairs(repository, KIND, _pairs("a", "b"), execute=judge)
    assert [row.verdict for row in results] == ["same", "different"]
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT task, left_kind, judge, judge_model, prompt_version, verdict, score FROM judgment_ledger ORDER BY created_at"
        ).fetchall()
    assert [tuple(row) for row in rows] == [
        ("same_objective_test", "objective", "llm", "fake-judge", "test-v1", "same", None),
        ("same_objective_test", "objective", "llm", "fake-judge", "test-v1", "different", None),
    ]
    again = judge_pairs(repository, KIND, _pairs("a", "b"), execute=_Judge([]))
    assert [row.status for row in again] == ["already_judged", "already_judged"]


def test_a_spend_refusal_stops_the_batch_and_a_failure_skips_one_pair(repository):
    results = judge_pairs(
        repository, KIND, _pairs("a", "b", "c", "d"),
        execute=_Judge([RuntimeError("boom"), "same", SpendLimitExceeded("calls"), "same"]),
    )
    assert [row.status for row in results] == ["failed", "judged", "not_run", "not_run"]


def test_presentation_order_and_input_hash_ignore_rank_and_side():
    a, b = _subject("a", "first text"), _subject("b", "second text")
    assert pair_prompt(KIND, a, b) == pair_prompt(KIND, b, a)
    assert pair_input_hash(KIND, a, b) == pair_input_hash(KIND, b, a)
    changed = Subject(kind="objective", id="a", text="other", content_hash="h-other", view={"statement": "other"})
    assert pair_input_hash(KIND, changed, b) != pair_input_hash(KIND, a, b)
