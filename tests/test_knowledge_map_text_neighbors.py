"""Slice 2 T7: knowledge-map neighbours from stored item-text vectors.

Display only. The spokes may come from item-text similarity, but the map's
geometry, its facet field and all learner state stay exactly as they were, and
rendering never calls a model.
"""
from __future__ import annotations

from contextlib import closing
import copy

import numpy as np
import pytest

from learnloop.ai.execution import observe_model_calls
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.stores.embedding_vectors import get_vector, put_vector, retrieve
from learnloop.ops.embedding_backfill import TASK_PREFIX
from learnloop.vault.embedding_recipes import embedding_records
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.handlers.item_text_neighbors import ranking_model
from learnloop_sidecar.handlers.knowledge_map import (
    _item_map_geometry,
    _vault_edge_tuples,
    get_knowledge_map,
)
from tests.helpers import NOW, NOW_ISO, create_basic_vault


EXTRA_ITEMS = {
    "pi_t7_compute": ("Compute the SVD of a 2x2 diagonal matrix.", ["procedure"]),
    "pi_t7_orthogonal": ("Why are U and V orthogonal in the SVD?", ["recall", "interpretation"]),
    "pi_t7_rank": ("Use the SVD to read off the rank of a matrix.", ["interpretation"]),
    "pi_t7_singular": ("What are singular values?", ["recall"]),
    "pi_t7_truncate": ("Explain truncated SVD for low-rank approximation.", ["interpretation", "procedure"]),
}


def _add_item(root, item_id: str, prompt: str, facets: list[str], *, status: str = "active") -> None:
    upsert_practice_item(
        root,
        {
            "id": item_id,
            "status": status,
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": facets,
            "evidence_weights": {facet: 1.0 for facet in facets},
            "prompt": prompt,
            "expected_answer": "A worked answer.",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
                "fatal_errors": [],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=FrozenClock(NOW),
    )


@pytest.fixture
def vault_paths(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    for item_id, (prompt, facets) in EXTRA_ITEMS.items():
        _add_item(paths.root, item_id, prompt, facets)
    return paths


def _stem_hashes(root) -> dict[str, str]:
    return {record.record_id: record.content_hash for record in embedding_records(load_vault(root), ["item/stem"])}


def _store_vectors(paths, vectors: dict[str, np.ndarray], *, model_id: str | None = None,
                   task_prefix: str = TASK_PREFIX, hashes: dict[str, str] | None = None) -> None:
    model = model_id or load_vault(paths.root).config.embedding.model
    hashes = hashes or _stem_hashes(paths.root)
    with closing(connect(paths.sqlite_path)) as connection, connection:
        for item_id, vector in vectors.items():
            put_vector(
                connection, record_kind="item", record_id=item_id, field="stem",
                content_hash=hashes[item_id], model_id=model, task_prefix=task_prefix,
                vector=vector,
            )


def _random_vectors(item_ids, *, dims: int = 8, seed: int = 7) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    return {item_id: rng.normal(size=dims) for item_id in sorted(item_ids)}


def _map(root) -> dict:
    context = SidecarContext()
    context.load(root, maintenance=False)
    return get_knowledge_map(context, None)


def _without_neighbors(snapshot: dict) -> dict:
    stripped = copy.deepcopy(snapshot)
    stripped.pop("itemTextNeighbors")
    for point in stripped["points"]:
        point.pop("neighbors")
        point.pop("neighborBasis")
    return stripped


def _set_embedding_config(root, extra: str) -> None:
    config_path = root / "learnloop.toml"
    text = config_path.read_text(encoding="utf-8")
    anchor = "dimensions = 4096\n"
    assert text.count(anchor) == 1
    config_path.write_text(text.replace(anchor, anchor + extra), encoding="utf-8")


def _set_embedding_model(root, model_id: str) -> None:
    config_path = root / "learnloop.toml"
    text = config_path.read_text(encoding="utf-8")
    anchor = f'model = "{load_vault(root).config.embedding.model}"\n'
    assert text.count(anchor) == 1
    config_path.write_text(text.replace(anchor, f'model = "{model_id}"\n'), encoding="utf-8")


def _store_ranking(paths, model_id: str, item_id: str, *, limit: int = 4) -> list[tuple[str, float]]:
    """``retrieve()``'s top ``limit`` for one item over every current stem of ``model_id``."""
    hashes = _stem_hashes(paths.root)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        query = get_vector(
            connection, record_kind="item", record_id=item_id, field="stem",
            content_hash=hashes[item_id], model_id=model_id, task_prefix=TASK_PREFIX,
        )
        matches = retrieve(
            connection, record_kind="item", field="stem", model_id=model_id,
            task_prefix=TASK_PREFIX, query=query, expected_records=hashes,
            candidate_ids=set(hashes) - {item_id}, limit=limit,
        )
    return [(match.record_id, match.score) for match in matches]


def test_item_text_ranks_like_the_store_and_leaves_the_map_geometry_alone(vault_paths):
    baseline = _map(vault_paths.root)
    item_ids = sorted(load_vault(vault_paths.root).practice_items)
    assert len(item_ids) == 6
    assert {point["neighborBasis"] for point in baseline["points"]} == {"facet_graph"}

    vectors = _random_vectors(item_ids)
    _store_vectors(vault_paths, vectors)
    snapshot = _map(vault_paths.root)

    # Never-blend: coordinates, stress, counts, the facet field (well depth,
    # demonstrated beads, Ready) and every per-item belief field are identical.
    assert _without_neighbors(snapshot) == _without_neighbors(baseline)

    loaded = load_vault(vault_paths.root)
    model = loaded.config.embedding.model
    assert snapshot["itemTextNeighbors"] == {
        "enabled": True, "modelId": model, "stems": 6, "embedded": 6, "pendingModel": None,
    }
    items, _concepts, distances, _coords, _stress = _item_map_geometry(loaded, _vault_edge_tuples(loaded))
    index_of = {item.id: index for index, item in enumerate(items)}
    hashes = _stem_hashes(vault_paths.root)
    changed = 0
    with closing(connect(vault_paths.sqlite_path, read_only=True)) as connection:
        for point, before in zip(snapshot["points"], baseline["points"], strict=True):
            assert point["neighborBasis"] == "item_text"
            query = get_vector(
                connection, record_kind="item", record_id=point["id"], field="stem",
                content_hash=hashes[point["id"]], model_id=model, task_prefix=TASK_PREFIX,
            )
            expected = retrieve(
                connection, record_kind="item", field="stem", model_id=model,
                task_prefix=TASK_PREFIX, query=query, expected_records=hashes,
                candidate_ids=set(hashes) - {point["id"]}, limit=4,
            )
            assert [n["id"] for n in point["neighbors"]] == [m.record_id for m in expected]
            for neighbor, match in zip(point["neighbors"], expected, strict=True):
                assert set(neighbor) == {"id", "distance", "similarity"}
                assert neighbor["similarity"] == pytest.approx(match.score)
                # `distance` keeps its meaning: the blended facet/graph distance.
                assert neighbor["distance"] == distances[index_of[point["id"]]][index_of[neighbor["id"]]]
            changed += [n["id"] for n in point["neighbors"]] != [n["id"] for n in before["neighbors"]]
    assert changed, "the fixture must make item text pick different spokes"

    # Same stored state, same bytes.
    assert _map(vault_paths.root) == snapshot


def test_missing_and_stale_stems_degrade_per_item(vault_paths):
    item_ids = sorted(load_vault(vault_paths.root).practice_items)
    baseline = {point["id"]: point for point in _map(vault_paths.root)["points"]}
    _store_vectors(vault_paths, _random_vectors(item_ids))

    # Editing a stem makes its stored vector stale; it must drop out as a
    # source and as a candidate, while the five current items still fill four
    # spokes each from item text.
    prompt, facets = EXTRA_ITEMS["pi_t7_rank"]
    _add_item(vault_paths.root, "pi_t7_rank", prompt + " Justify it.", facets)
    snapshot = _map(vault_paths.root)
    assert snapshot["itemTextNeighbors"]["embedded"] == 5
    by_id = {point["id"]: point for point in snapshot["points"]}
    assert by_id["pi_t7_rank"]["neighborBasis"] == "facet_graph"
    assert by_id["pi_t7_rank"]["neighbors"] == baseline["pi_t7_rank"]["neighbors"]
    for item_id, point in by_id.items():
        if item_id == "pi_t7_rank":
            continue
        assert point["neighborBasis"] == "item_text"
        assert len(point["neighbors"]) == 4
        assert "pi_t7_rank" not in {n["id"] for n in point["neighbors"]}

    # With four embedded items no list could fill four spokes from item text,
    # so every item keeps its facet/graph neighbours rather than a short list.
    _add_item(vault_paths.root, "pi_t7_singular", "What are singular values, exactly?", ["recall"])
    snapshot = _map(vault_paths.root)
    assert snapshot["itemTextNeighbors"]["embedded"] == 4
    assert {point["neighborBasis"] for point in snapshot["points"]} == {"facet_graph"}
    # Prompts are not part of the blended distance, so these are today's lists.
    assert {point["id"]: point["neighbors"] for point in snapshot["points"]} == {
        item_id: point["neighbors"] for item_id, point in baseline.items()
    }


def test_other_task_prefixes_are_ignored(vault_paths):
    item_ids = sorted(load_vault(vault_paths.root).practice_items)
    baseline = _map(vault_paths.root)
    _store_vectors(vault_paths, _random_vectors(item_ids, dims=8, seed=3), task_prefix="retrieval-query")
    assert _map(vault_paths.root) == baseline


def test_a_previous_model_ranks_alone_and_is_named(vault_paths):
    # Vectors of a model other than `embedding.model` (the vault's previous
    # model) keep ranking until the configured model's re-embed catches up
    # (Slice 2 §4). They rank alone: the configured model's two stored stems
    # never mix in, and the summary names both models.
    item_ids = sorted(load_vault(vault_paths.root).practice_items)
    configured = load_vault(vault_paths.root).config.embedding.model
    _store_vectors(vault_paths, _random_vectors(item_ids), model_id="another/embedder")
    _store_vectors(vault_paths, _random_vectors(item_ids[:2], seed=5), model_id=configured)
    snapshot = _map(vault_paths.root)
    assert snapshot["itemTextNeighbors"] == {
        "enabled": True, "modelId": "another/embedder", "stems": 6, "embedded": 6,
        "pendingModel": {"modelId": configured, "embedded": 2},
    }
    for point in snapshot["points"]:
        expected = _store_ranking(vault_paths, "another/embedder", point["id"])
        assert [(n["id"], n["similarity"]) for n in point["neighbors"]] == [
            (item_id, pytest.approx(score)) for item_id, score in expected
        ]


@pytest.mark.parametrize(
    ("coverage", "expected"),
    [
        ({}, None),
        ({"cfg": "a"}, "cfg"),
        ({"old": "ab"}, "old"),
        ({"cfg": "ab", "old": "ab"}, "cfg"),  # caught up: the configured model takes over
        ({"cfg": "abc", "old": "a"}, "cfg"),
        ({"cfg": "bc", "old": "ab"}, "old"),  # as many stems, but not everything "old" covers
        ({"cfg": "a", "older": "ab", "old": "ab"}, "old"),  # ties go to the smaller model ID
        ({"cfg": "a", "old": "abc", "older": "ab"}, "old"),  # otherwise the best-covered one
    ],
)
def test_ranking_model_moves_only_after_a_full_re_embed(coverage, expected):
    assert ranking_model("cfg", {model: frozenset(ids) for model, ids in coverage.items()}) == expected


def test_kill_switch_restores_facet_graph_neighbors(vault_paths):
    item_ids = sorted(load_vault(vault_paths.root).practice_items)
    baseline = _map(vault_paths.root)
    _store_vectors(vault_paths, _random_vectors(item_ids))
    assert {p["neighborBasis"] for p in _map(vault_paths.root)["points"]} == {"item_text"}

    _set_embedding_config(vault_paths.root, "map_neighbors_enabled = false\n")
    switched_off = _map(vault_paths.root)
    assert switched_off["itemTextNeighbors"] == {
        "enabled": False, "modelId": baseline["itemTextNeighbors"]["modelId"], "stems": 0, "embedded": 0,
        "pendingModel": None,
    }
    switched_off["itemTextNeighbors"] = baseline["itemTextNeighbors"]
    assert switched_off == baseline


def test_render_never_calls_a_model_or_writes(vault_paths, monkeypatch):
    item_ids = sorted(load_vault(vault_paths.root).practice_items)
    _store_vectors(vault_paths, _random_vectors(item_ids))
    # Embeddings fully enabled: the map must still not build a client.
    config_path = vault_paths.root / "learnloop.toml"
    text = config_path.read_text(encoding="utf-8")
    assert text.count("[embedding]\nenabled = false\n") == 1
    config_path.write_text(
        text.replace("[embedding]\nenabled = false\n", "[embedding]\nenabled = true\n"), encoding="utf-8"
    )
    context = SidecarContext()
    context.load(vault_paths.root, maintenance=False)
    assert context.vault.config.embedding.enabled

    def refuse(*_args, **_kwargs):
        raise AssertionError("the knowledge map must not build a model client")

    from learnloop.ai import client, routing
    from learnloop.ai.providers.openai_embedding import OpenAIEmbeddingProviderClient

    for module, name in (
        (routing, "ready_client_for_task"),
        (routing, "client_for_provider"),
        (client, "make_ai_provider_client"),
        (client, "make_ai_provider_client_from_profile"),
    ):
        monkeypatch.setattr(module, name, refuse)
    monkeypatch.setattr(OpenAIEmbeddingProviderClient, "__init__", refuse)
    events: list[tuple[str, dict]] = []
    with closing(connect(vault_paths.sqlite_path, read_only=True)) as connection:
        before = list(connection.iterdump())
    with observe_model_calls(lambda action, event: events.append((action, event))):
        snapshot = get_knowledge_map(context, None)
    with closing(connect(vault_paths.sqlite_path, read_only=True)) as connection:
        after = list(connection.iterdump())
    assert {p["neighborBasis"] for p in snapshot["points"]} == {"item_text"}
    assert events == []
    assert after == before


REPLACEMENT_MODEL = "other/replacement-embedder"


def test_interrupted_replacement_backfill_keeps_the_activated_model(vault_paths):
    """Slice 2 §4: retrieval moves to a new `embedding.model` only after its full re-embed."""
    item_ids = sorted(load_vault(vault_paths.root).practice_items)
    model_a = load_vault(vault_paths.root).config.embedding.model
    _store_vectors(vault_paths, _random_vectors(item_ids), model_id=model_a)
    on_a = _map(vault_paths.root)
    assert {point["neighborBasis"] for point in on_a["points"]} == {"item_text"}

    # The owner switches `embedding.model` to B. Nothing is re-embedded yet,
    # then the backfill stops after five of the six stems.
    _set_embedding_model(vault_paths.root, REPLACEMENT_MODEL)
    vectors_b = _random_vectors(item_ids, seed=11)
    for embedded_b in (0, 5):
        _store_vectors(
            vault_paths, {item_id: vectors_b[item_id] for item_id in item_ids[:embedded_b]},
            model_id=REPLACEMENT_MODEL,
        )
        interrupted = _map(vault_paths.root)
        # The spokes stay exactly A's: B ranks nothing until it covers every stem A does.
        assert interrupted["points"] == on_a["points"], embedded_b
        assert interrupted["itemTextNeighbors"] == {
            "enabled": True, "modelId": model_a, "stems": 6, "embedded": 6,
            "pendingModel": {"modelId": REPLACEMENT_MODEL, "embedded": embedded_b},
        }

    # The resumed backfill embeds the last stem: the map moves to B, ranked by B alone.
    _store_vectors(vault_paths, {item_ids[5]: vectors_b[item_ids[5]]}, model_id=REPLACEMENT_MODEL)
    on_b = _map(vault_paths.root)
    assert on_b["itemTextNeighbors"] == {
        "enabled": True, "modelId": REPLACEMENT_MODEL, "stems": 6, "embedded": 6, "pendingModel": None,
    }
    for point in on_b["points"]:
        assert point["neighborBasis"] == "item_text"
        expected = _store_ranking(vault_paths, REPLACEMENT_MODEL, point["id"])
        assert [n["id"] for n in point["neighbors"]] == [item_id for item_id, _score in expected]
        assert [n["similarity"] for n in point["neighbors"]] == pytest.approx([s for _id, s in expected])
    assert [p["neighbors"] for p in on_b["points"]] != [p["neighbors"] for p in on_a["points"]]

    # Once B is active, an edited stem is stale for A and B alike: B stays
    # active and only the edited item falls back to facet/graph neighbours.
    prompt, facets = EXTRA_ITEMS["pi_t7_rank"]
    _add_item(vault_paths.root, "pi_t7_rank", prompt + " Justify it.", facets)
    edited = _map(vault_paths.root)
    assert edited["itemTextNeighbors"] == {
        "enabled": True, "modelId": REPLACEMENT_MODEL, "stems": 6, "embedded": 5, "pendingModel": None,
    }
    assert {p["id"] for p in edited["points"] if p["neighborBasis"] == "facet_graph"} == {"pi_t7_rank"}


@pytest.mark.parametrize("retire_others", [False, True])
def test_coverage_counts_an_embedded_singleton(tmp_path, retire_others):
    if retire_others:
        # Every other map item retired: one eligible stem remains.
        paths = create_basic_vault(tmp_path / "vault")
        for item_id, (prompt, facets) in EXTRA_ITEMS.items():
            _add_item(paths.root, item_id, prompt, facets)
        item_ids = sorted(load_vault(paths.root).practice_items)
        _store_vectors(paths, _random_vectors(item_ids))
        for item_id, (prompt, facets) in EXTRA_ITEMS.items():
            _add_item(paths.root, item_id, prompt, facets, status="retired")
    else:
        paths = create_basic_vault(tmp_path / "vault")
        item_ids = sorted(load_vault(paths.root).practice_items)
        assert len(item_ids) == 1
        _store_vectors(paths, _random_vectors(item_ids))
    (stem_id,) = _stem_hashes(paths.root)
    snapshot = _map(paths.root)
    # The stored vector is counted although one stem has nobody to rank against.
    assert snapshot["itemTextNeighbors"] == {
        "enabled": True, "modelId": load_vault(paths.root).config.embedding.model,
        "stems": 1, "embedded": 1, "pendingModel": None,
    }
    assert {point["id"]: point["neighborBasis"] for point in snapshot["points"]}[stem_id] == "facet_graph"
