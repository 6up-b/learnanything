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


def _add_item(root, item_id: str, prompt: str, facets: list[str]) -> None:
    upsert_practice_item(
        root,
        {
            "id": item_id,
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
        "enabled": True, "modelId": model, "stems": 6, "embedded": 6,
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


def test_other_models_and_prefixes_are_ignored(vault_paths):
    item_ids = sorted(load_vault(vault_paths.root).practice_items)
    baseline = _map(vault_paths.root)
    _store_vectors(vault_paths, _random_vectors(item_ids), model_id="another/embedder")
    _store_vectors(vault_paths, _random_vectors(item_ids, dims=8, seed=3), task_prefix="retrieval-query")
    assert _map(vault_paths.root) == baseline


def test_kill_switch_restores_facet_graph_neighbors(vault_paths):
    item_ids = sorted(load_vault(vault_paths.root).practice_items)
    baseline = _map(vault_paths.root)
    _store_vectors(vault_paths, _random_vectors(item_ids))
    assert {p["neighborBasis"] for p in _map(vault_paths.root)["points"]} == {"item_text"}

    _set_embedding_config(vault_paths.root, "map_neighbors_enabled = false\n")
    switched_off = _map(vault_paths.root)
    assert switched_off["itemTextNeighbors"] == {
        "enabled": False, "modelId": baseline["itemTextNeighbors"]["modelId"], "stems": 0, "embedded": 0,
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
