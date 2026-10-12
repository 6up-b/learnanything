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

    def __init__(self, verdicts, *, producer: str = "fake-judge", during=None):
        self.verdicts = list(verdicts)
        self.producer = producer
        self.calls = 0
        #: Called inside the model call (another worker interleaving there).
        self.during = during

    def __call__(self, prompt, model, purpose):
        assert purpose == KIND.purpose and KIND.prompt_version in prompt
        self.calls += 1
        if self.during is not None:
            self.during()
        verdict = self.verdicts.pop(0)
        if isinstance(verdict, BaseException):
            raise verdict
        return SameOrDifferent(verdict=verdict, rationale="because"), self.producer


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


def _ledger(repository):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT judge_model, verdict, supersedes_id IS NOT NULL FROM judgment_ledger ORDER BY rowid"
        )]


def test_reuse_is_per_producer_and_a_rerun_supersedes_the_same_producer(repository):
    """Review F4: a route change asks the new model; --rerun asks the same model again."""

    pairs = _pairs("a")
    first = judge_pairs(repository, KIND, pairs, execute=_Judge(["same"], producer="model-a"))
    assert [row.status for row in first] == ["judged"]
    # Same producer again: reused, no call.
    again = _Judge([], producer="model-a")
    assert [row.status for row in judge_pairs(repository, KIND, pairs, execute=again)] == ["already_judged"]
    assert again.calls == 0
    # The route now resolves to another model: it is asked (not "already judged").
    other = _Judge(["different"], producer="model-b")
    assert [row.status for row in judge_pairs(repository, KIND, pairs, execute=other)] == ["judged"]
    assert other.calls == 1
    # An explicit rerun asks model A again; its verdict supersedes A's earlier one.
    rerun = _Judge(["different"], producer="model-a")
    result = judge_pairs(repository, KIND, pairs, execute=rerun, rerun=True)
    assert [row.status for row in result] == ["judged"] and result[0].supersedes_id is not None
    assert _ledger(repository) == [
        ("model-a", "same", False), ("model-b", "different", False), ("model-a", "different", True),
    ]


def test_a_judge_without_a_producer_is_refused(repository):
    class Anonymous:
        def __call__(self, prompt, model, purpose):  # pragma: no cover - never called
            raise AssertionError("called")

    with pytest.raises(ValueError, match="producer"):
        judge_pairs(repository, KIND, _pairs("a"), execute=Anonymous())


def test_a_concurrent_worker_skips_a_claimed_pair_and_never_pays_twice(repository):
    """Review F5: the second worker checks the pair while the first is calling."""

    second = _Judge(["same"], producer="fake-judge")
    seen = {}

    def interleave():
        # The first worker's claim is committed before its call: the second
        # worker sees it held and makes no call.
        seen["second"] = judge_pairs(repository, KIND, _pairs("a"), execute=second)

    first = _Judge(["different"], producer="fake-judge", during=interleave)
    result = judge_pairs(repository, KIND, _pairs("a"), execute=first)
    assert [row.status for row in seen["second"]] == ["claimed_elsewhere"] and second.calls == 0
    assert [row.status for row in result] == ["judged"]
    assert _ledger(repository) == [("fake-judge", "different", False)]
    # Afterwards the question is answered for this producer.
    late = _Judge([], producer="fake-judge")
    assert [row.status for row in judge_pairs(repository, KIND, _pairs("a"), execute=late)] == ["already_judged"]


def test_an_expired_lease_is_reclaimed_and_the_late_verdict_is_fenced_out(repository):
    """Review F5: a worker whose lease expired cannot land a second, conflicting verdict."""

    clock = {"now": "2026-10-01T00:00:00+00:00"}

    def now():
        return clock["now"]

    takeover = _Judge(["same"], producer="fake-judge")
    seen = {}

    def expire_and_take_over():
        clock["now"] = "2026-10-01T01:00:00+00:00"  # past the 60 s lease
        seen["takeover"] = judge_pairs(repository, KIND, _pairs("a"), execute=takeover, lease_seconds=60, now=now)

    slow = _Judge(["different"], producer="fake-judge", during=expire_and_take_over)
    result = judge_pairs(repository, KIND, _pairs("a"), execute=slow, lease_seconds=60, now=now)
    assert [row.status for row in seen["takeover"]] == ["judged"] and takeover.calls == 1
    assert [row.status for row in result] == ["fenced"] and result[0].judgment_id is None
    assert _ledger(repository) == [("fake-judge", "same", False)], "exactly one verdict, the live lease holder's"


def test_a_failed_call_releases_its_claim(repository):
    judge_pairs(repository, KIND, _pairs("a"), execute=_Judge([RuntimeError("boom")]))
    retry = _Judge(["same"])
    assert [row.status for row in judge_pairs(repository, KIND, _pairs("a"), execute=retry)] == ["judged"]


def test_a_partially_backfilled_replacement_model_never_ranks(repository):
    """Review F8 (Slice 1 §9.6): until the new model covers what the old one
    covers, the old index ranks and the replacement's partial index is unused."""

    from learnloop.matching.shortlist import active_model

    subjects = [_subject(name, name, created=f"2026-01-0{index + 1}") for index, name in enumerate(("x", "y", "z"))]
    with closing(connect(repository.sqlite_path)) as connection, connection:
        for index, subject in enumerate(subjects):
            put_vector(connection, record_kind=KIND.record_kind, record_id=subject.id, field=KIND.field,
                       content_hash=subject.content_hash, model_id="old/model", task_prefix=KIND.task_prefix,
                       vector=np.asarray([1.0, float(index), 0.0, 0.5]))
        for index, subject in enumerate(subjects[:2]):  # the replacement's backfill is incomplete
            put_vector(connection, record_kind=KIND.record_kind, record_id=subject.id, field=KIND.field,
                       content_hash=subject.content_hash, model_id=MODEL, task_prefix=KIND.task_prefix,
                       vector=np.asarray([0.0, 1.0, float(index), 0.0]))
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        pending = active_model(connection, KIND, subjects, configured=MODEL)
        assert pending.status == "replacement_pending" and pending.ranking == "old/model"
        assert pending.summary()["current_vectors_by_model"] == {"old/model": 3, MODEL: 2}
    with closing(connect(repository.sqlite_path)) as connection, connection:
        put_vector(connection, record_kind=KIND.record_kind, record_id="z", field=KIND.field,
                   content_hash="h-z", model_id=MODEL, task_prefix=KIND.task_prefix,
                   vector=np.asarray([0.0, 1.0, 2.0, 0.0]))
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        complete = active_model(connection, KIND, subjects, configured=MODEL)
        assert complete.status == "active" and complete.ranking == MODEL


def test_a_cutoff_applies_only_to_the_vectors_it_was_measured_on():
    """Review F7: a cutoff names model, width, recipe and prefix; others are refused."""

    from types import SimpleNamespace

    from learnloop.matching.shortlist import compatible_cutoff

    kind = MatchKind(**{**KIND.__dict__, "recipe": "objective/statement@v1"})
    entry = SimpleNamespace(cutoff=0.4, dims=4096, recipe="objective/statement@v1", task_prefix="similarity")
    assert compatible_cutoff(entry, kind, model_id=MODEL, dims=4096) == (0.4, "benchmark", None)
    value, basis, refusal = compatible_cutoff(entry, kind, model_id=MODEL, dims=1024)
    assert value is None and basis == "refused_incompatible" and "1024" in refusal
    other_recipe = SimpleNamespace(cutoff=0.4, dims=4096, recipe="objective/statement@v2", task_prefix="similarity")
    assert compatible_cutoff(other_recipe, kind, model_id=MODEL, dims=4096)[1] == "refused_incompatible"
    assert compatible_cutoff(None, kind, model_id=MODEL, dims=4096) == (None, "top_k_only", None)


# -- second review F6: what a later kind (learner-text gaps) needs from the step ----------

#: An ASYMMETRIC kind: a learner's stated prerequisite (an ephemeral query,
#: embedded once with the query prompt) against stored learning objectives.
GAPS = MatchKind(
    name="named prerequisite", task="same_prerequisite_test", subject_kind="learning_object",
    record_kind="learning_object", field="statement", task_prefix="retrieval-document",
    route="authoring", purpose="same_prerequisite_test", prompt_version="test-v1",
    question="Does the stated prerequisite name this learning objective?", guidance="Wording may differ.",
    query_record_kind="learner_text", query_field="named_gap", query_task_prefix="retrieval-query",
)


def test_an_asymmetric_kind_shortlists_an_ephemeral_query_against_a_pool_of_another_record_kind(repository):
    from learnloop.matching.kinds import EmbeddingIdentity

    assert GAPS.pool_identity() == EmbeddingIdentity("learning_object", "statement", "retrieval-document", "")
    assert GAPS.query_identity().task_prefix == "retrieval-query" and not GAPS.symmetric
    assert KIND.query_identity() == KIND.pool_identity() and KIND.symmetric
    los = [Subject(kind="learning_object", id=name, text=name, content_hash=f"h-{name}") for name in ("lo_a", "lo_b", "lo_c")]
    with closing(connect(repository.sqlite_path)) as connection, connection:
        for subject, vector in zip(los, ([1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.6, 0.6, 0.0]), strict=True):
            put_vector(connection, record_kind="learning_object", record_id=subject.id, field="statement",
                       content_hash=subject.content_hash, model_id=MODEL, task_prefix="retrieval-document",
                       vector=np.asarray(vector, dtype=float))
    query = Subject(kind="learner_text", id="question-1", text="I never learned what an eigenvector is",
                    content_hash="h-q")
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        result = shortlist_pairs(
            connection, GAPS, queries=[query], pool=los, model_id=MODEL, top_k=2, cutoff=None,
            compatible=lambda q, c: True, query_vectors={"question-1": np.asarray([0.9, 0.1, 0.0])},
        )
    assert [pair.right.id for pair in result.pairs] == ["lo_a", "lo_c"]
    assert result.queries_without_vector == 0 and result.pool_with_vector == 3


class _Verifier(_Judge):
    judge = "verifier"


def test_the_judge_label_is_the_executors_and_reuse_is_per_label(repository):
    """The ledger's ``judge`` is a parameter of the executor (a later stage
    logs a second judge, e.g. the Decider, beside the LLM), and a verdict
    from one judge label is not "already judged" for another."""

    judge_pairs(repository, KIND, _pairs("a"), execute=_Judge(["same"]))
    results = judge_pairs(repository, KIND, _pairs("a"), execute=_Verifier(["different"]))
    assert [row.status for row in results] == ["judged"]
    with repository.connection() as connection:
        rows = connection.execute("SELECT judge, verdict FROM judgment_ledger ORDER BY rowid").fetchall()
    assert [tuple(row) for row in rows] == [("llm", "same"), ("verifier", "different")]
    again = judge_pairs(repository, KIND, _pairs("a"), execute=_Verifier([]))
    assert [row.status for row in again] == ["already_judged"]
