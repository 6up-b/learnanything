from contextlib import closing
from pathlib import Path
import sqlite3

import numpy as np
import pytest

from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.migrate import apply_migrations
from learnloop.db.repositories import Repository
from learnloop.db.stores.embedding_vectors import (
    EmbeddingVectorStore, IncompleteEmbeddingIndex, get_vector, nearest_among_current, put_vector,
    retrieve,
)
from learnloop.db.stores.judgments import append_judgment
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault


@pytest.fixture
def connection(tmp_path):
    path = tmp_path / "state.sqlite"
    apply_migrations(path)
    with closing(connect(path)) as connection:
        yield connection


def identity(**changes):
    return dict(record_kind="item", record_id="a", field="stem", content_hash="h",
                model_id="fake", task_prefix="similarity") | changes


def test_paid_vector_identity_and_float16(connection, tmp_path):
    values = [0.123456, -0.654321]
    first = put_vector(connection, **identity(), vector=values)
    assert put_vector(connection, **identity(), vector=[1, 2]) == first
    np.testing.assert_array_equal(get_vector(connection, **identity()),
                                  np.asarray(values, dtype="<f2").astype(float))
    assert connection.execute("SELECT length(vector) FROM embedding_vectors").fetchone()[0] == 4
    put_vector(connection, **identity(content_hash="new"), vector=[3, 4])
    put_vector(connection, **identity(model_id="other"), vector=[1, 2, 3])
    assert connection.execute("SELECT count(*) FROM embedding_vectors").fetchone()[0] == 3
    connection.commit()
    store = EmbeddingVectorStore(tmp_path / "state.sqlite")
    assert store.contains(**identity())
    assert not store.contains(**identity(record_id="missing"))


@pytest.mark.parametrize("vector", [[], [[1]], [float("nan")], [float("inf")], [70000]])
def test_invalid_vectors_rejected(connection, vector):
    with pytest.raises(ValueError):
        put_vector(connection, **identity(), vector=vector)


def test_dimensions_fixed_per_model(connection):
    put_vector(connection, **identity(), vector=[1, 2])
    with pytest.raises(sqlite3.IntegrityError, match="dimension"):
        put_vector(connection, **identity(record_id="b"), vector=[1, 2, 3])
    with pytest.raises(sqlite3.IntegrityError, match="dimension"):
        put_vector(connection, **identity(), vector=[1])


def test_exact_centered_retrieval_is_model_and_revision_isolated(connection):
    vectors = np.array([[10, 1], [10, -1], [12, 0]], dtype=float)
    for name, vector in zip("abc", vectors):
        put_vector(connection, **identity(record_id=name), vector=vector)
    put_vector(connection, **identity(model_id="other"), vector=[1, 2, 3])
    put_vector(connection, **identity(content_hash="old"), vector=[100, 100])
    args = dict(record_kind="item", field="stem", model_id="fake", task_prefix="similarity",
                query=[10, 1], expected_records=dict.fromkeys("abc", "h"))
    matches = retrieve(connection, **args)
    centered = vectors - vectors.mean(axis=0)
    query = np.array(args["query"]) - vectors.mean(axis=0)
    expected = centered @ query / (np.linalg.norm(centered, axis=1) * np.linalg.norm(query))
    for match in matches:
        assert match.score == pytest.approx(expected["abc".index(match.record_id)])
    assert matches[0].record_id == "a"
    assert [m.record_id for m in retrieve(connection, **args, candidate_ids={"b"}, limit=1)] == ["b"]
    with pytest.raises(ValueError, match="dimension"):
        retrieve(connection, **(args | {"query": [1, 2, 3]}))
    with pytest.raises(IncompleteEmbeddingIndex):
        retrieve(connection, **(args | {"expected_records": {"a": "new", "b": "h"}}))
    with pytest.raises(IncompleteEmbeddingIndex):
        retrieve(connection, **(args | {"model_id": "other", "query": [1, 2, 3]}))


def test_empty_and_zero_centered_retrieval(connection):
    args = dict(record_kind="item", field="stem", model_id="fake", task_prefix="similarity",
                query=[1, 2])
    assert retrieve(connection, **args, expected_records={}) == []
    put_vector(connection, **identity(), vector=[1, 2])
    assert retrieve(connection, **args, expected_records={"a": "h"})[0].score == 0


def test_mrl_retrieval_truncates_before_centering_and_ranking(connection, tmp_path):
    vectors = np.array([[10, 1, -100], [10, -1, 100], [12, 0, 0]], dtype=float)
    for name, vector in zip("abc", vectors):
        put_vector(connection, **identity(record_id=name), vector=vector)
    args = dict(record_kind="item", field="stem", model_id="fake", task_prefix="similarity",
                query=[10, 1, 100], expected_records=dict.fromkeys("abc", "h"))
    assert retrieve(connection, **args)[0].record_id == "b"
    matches = retrieve(connection, **args, dimensions=2)
    assert matches[0].record_id == "a"
    assert retrieve(connection, **(args | {"query": [10, 1]}), dimensions=2) == matches
    # The view truncates, L2-normalizes, then centers (MRL convention).
    view = vectors[:, :2] / np.linalg.norm(vectors[:, :2], axis=1, keepdims=True)
    unit_query = np.array([10, 1]) / np.linalg.norm([10, 1])
    centered = view - view.mean(axis=0)
    query = unit_query - view.mean(axis=0)
    scores = centered @ query / (np.linalg.norm(centered, axis=1) * np.linalg.norm(query))
    for match in matches:
        assert match.score == pytest.approx(scores["abc".index(match.record_id)])
    assert retrieve(connection, **args, dimensions=3) == retrieve(connection, **args)
    assert retrieve(connection, **args, dimensions=2, candidate_ids={"b"}, limit=1) == [
        next(match for match in matches if match.record_id == "b")
    ]
    with pytest.raises(IncompleteEmbeddingIndex):
        retrieve(connection, **(args | {"expected_records": {"a": "new"}}), dimensions=2)
    connection.commit()
    assert EmbeddingVectorStore(tmp_path / "state.sqlite").retrieve(**args, dimensions=2) == matches
    assert connection.execute("SELECT DISTINCT dims FROM embedding_vectors").fetchall()[0][0] == 3
    np.testing.assert_array_equal(get_vector(connection, **identity()), vectors[0])


def test_mrl_view_ranks_like_vectors_embedded_at_that_width(connection):
    # Unit vectors whose 2-d prefixes have different norms (1.0, 0.6, 0.6).
    full = np.array([[0.6, 0.8, 0.0], [0.6, 0.0, 0.8], [0.0, 0.6, 0.8]])
    native = full[:, :2] / np.linalg.norm(full[:, :2], axis=1, keepdims=True)
    for name, wide, narrow in zip("abc", full, native):
        put_vector(connection, **identity(record_id=name, model_id="wide"), vector=wide)
        put_vector(connection, **identity(record_id=name, model_id="narrow"), vector=narrow)
    args = dict(record_kind="item", field="stem", task_prefix="similarity",
                expected_records=dict.fromkeys("abc", "h"))
    query = np.array([0.0, 0.8, 0.6])
    view = retrieve(connection, **args, model_id="wide", query=query, dimensions=2)
    embedded = retrieve(connection, **args, model_id="narrow",
                        query=query[:2] / np.linalg.norm(query[:2]))
    assert [m.record_id for m in view] == [m.record_id for m in embedded]
    assert [m.score for m in view] == pytest.approx([m.score for m in embedded], abs=1e-3)


@pytest.mark.parametrize("dimensions,query", [
    (0, [1, 2]), (-1, [1, 2]), (True, [1, 2]), (1.5, [1, 2]),
    (3, [1, 2]), (3, [1, 2, 3]),
])
def test_invalid_mrl_dimensions(connection, dimensions, query):
    put_vector(connection, **identity(), vector=[1, 2])
    with pytest.raises(ValueError, match="dimension"):
        retrieve(connection, record_kind="item", field="stem", model_id="fake",
                 task_prefix="similarity", query=query, expected_records={"a": "h"},
                 dimensions=dimensions)


def test_client_agnostic_storage_and_prefix_isolation(connection):
    class FakeEmbeddingClient:
        model_id = "local-test"
        dims = 2
        modalities = frozenset({"text"})
        max_input_tokens = 100

        def embed(self, inputs, task_prefix):
            assert task_prefix == "similarity"
            return [[len(text), 1] for text in inputs]

    client = FakeEmbeddingClient()
    for name, vector in zip("ab", client.embed(["a", "bb"], "similarity")):
        put_vector(connection, **identity(record_id=name, model_id=client.model_id), vector=vector)
    for changes in ({"field": "outline"}, {"task_prefix": "retrieval-document"},
                    {"record_kind": "facet"}):
        put_vector(connection, **(identity(model_id=client.model_id) | changes), vector=[100, 100])
    matches = retrieve(connection, record_kind="item", field="stem", model_id=client.model_id,
                       task_prefix="similarity", query=client.embed(["a"], "similarity")[0],
                       expected_records={"a": "h", "b": "h"})
    assert [match.record_id for match in matches] == ["a", "b"]
    assert [match.score for match in matches] == pytest.approx([1, -1])


def test_nearest_among_current_ranks_like_retrieve_over_the_covered_records(connection):
    # Slice 2 T7: all-pairs neighbours for display, tolerating partial coverage.
    for name, vector in {"a": [10, 1, 0], "b": [10, -1, 0], "c": [12, 0, 1], "d": [9, 0, -1]}.items():
        put_vector(connection, **identity(record_id=name), vector=vector)
    put_vector(connection, **identity(record_id="e", content_hash="old"), vector=[0, 0, 9])
    put_vector(connection, **identity(record_id="a", model_id="other"), vector=[1, 2])
    put_vector(connection, **identity(record_id="b", task_prefix="retrieval-query"), vector=[5, 5, 5])
    args = dict(record_kind="item", field="stem", model_id="fake", task_prefix="similarity")
    # "e" is stale (edited since it was embedded) and "f" was never embedded.
    expected = dict.fromkeys("abcdef", "h")
    neighbours = nearest_among_current(connection, **args, expected_records=expected, limit=2)
    assert set(neighbours) == set("abcd")
    covered = dict.fromkeys("abcd", "h")
    for name, ranked in neighbours.items():
        reference = retrieve(
            connection, **args, query=get_vector(connection, **identity(record_id=name)),
            expected_records=covered, candidate_ids=set(covered) - {name}, limit=2,
        )
        assert [m.record_id for m in ranked] == [m.record_id for m in reference]
        assert [m.score for m in ranked] == pytest.approx([m.score for m in reference])
        assert name not in {m.record_id for m in ranked}
    # A limit above the covered count returns everyone else, never itself.
    wide = nearest_among_current(connection, **args, expected_records=covered, limit=9)
    assert {name: {m.record_id for m in ranked} for name, ranked in wide.items()} == {
        name: set(covered) - {name} for name in covered
    }


def test_nearest_among_current_edges(connection):
    args = dict(record_kind="item", field="stem", model_id="fake", task_prefix="similarity")
    with pytest.raises(ValueError, match="limit"):
        nearest_among_current(connection, **args, expected_records={}, limit=-1)
    assert nearest_among_current(connection, **args, expected_records={}, limit=4) == {}
    put_vector(connection, **identity(record_id="b"), vector=[1, 0])
    # One covered record has nobody to rank.
    assert nearest_among_current(connection, **args, expected_records={"b": "h"}, limit=4) == {"b": []}
    put_vector(connection, **identity(record_id="a"), vector=[1, 0])
    put_vector(connection, **identity(record_id="c"), vector=[1, 0])
    # Identical vectors centre to zero: every score is 0 and ties go to the smaller ID.
    covered = dict.fromkeys("abc", "h")
    neighbours = nearest_among_current(connection, **args, expected_records=covered, limit=4)
    assert {name: [(m.record_id, m.score) for m in ranked] for name, ranked in neighbours.items()} == {
        "a": [("b", 0.0), ("c", 0.0)], "b": [("a", 0.0), ("c", 0.0)], "c": [("a", 0.0), ("b", 0.0)],
    }
    assert nearest_among_current(connection, **args, expected_records=covered, limit=0) == {
        "a": [], "b": [], "c": [],
    }


def _migration_head_fixture() -> Path:
    # Resolved, not hard-coded: CLAUDE.md's head-fixture procedure lists the
    # paths to rename, and this test must not become an unlisted sixth one.
    heads = sorted((Path(__file__).resolve().parents[1] / "fixtures").glob("migration_head_*"))
    assert len(heads) == 1, heads
    return heads[0]


@pytest.mark.durability
def test_replay_preserves_paid_inputs_without_models(tmp_path, monkeypatch):
    from learnloop.ai import client
    from learnloop.ai.providers.openai_embedding import OpenAIEmbeddingProviderClient
    from tests.openai_fakes import install_fake_openai

    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("replay must not construct a model")

    monkeypatch.setattr(client, "make_ai_provider_client", forbidden)
    monkeypatch.setattr(client, "make_ai_provider_client_from_profile", forbidden)
    monkeypatch.setattr(OpenAIEmbeddingProviderClient, "__init__", forbidden)
    monkeypatch.setattr(OpenAIEmbeddingProviderClient, "embed", forbidden)
    sdk = install_fake_openai(monkeypatch)
    root = tmp_path / "vault"
    copy_tree_with_databases(_migration_head_fixture(), root)
    repository = Repository(root / "state.sqlite")
    with repository.connection() as connection:
        put_vector(connection, **identity(), vector=[1, 2])
        append_judgment(connection, task="same_target", left_kind="item", left_id="a",
                        judge="owner", input_hash="h", verdict="same")
        before = {table: [tuple(row) for row in connection.execute(f"SELECT * FROM {table}")]
                  for table in ("embedding_vectors", "judgment_ledger")}
    for _ in range(2):
        rebuild_all_derived_state(load_vault(root), repository)
    with repository.connection() as connection:
        after = {table: [tuple(row) for row in connection.execute(f"SELECT * FROM {table}")]
                 for table in before}
    assert after == before
    assert calls == []
    assert sdk.instances == []
