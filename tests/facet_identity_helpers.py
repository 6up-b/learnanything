"""What other test files use from ``tests/test_facet_identity.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.content.facet_identity.views import judge_view
from learnloop.db.repositories import Repository
from learnloop.vault.loader import add_subject, init_vault, load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import write_yaml

from tests.facet_identity_fakes import FakeFacetJudge, clusters_from_pairs, regression_data


_CLOCK = FrozenClock(datetime(2026, 10, 12, 12, 0, 0, tzinfo=UTC))
_NOW = "2026-10-12T12:00:00Z"


def _regression_vault(root: Path) -> tuple[Path, Repository, dict]:
    """A fresh vault holding the study's 39 facets, their concepts and graph."""

    data = regression_data()
    init_vault(root, clock=_CLOCK)
    add_subject(root, "vector-spaces", "Vector Spaces", clock=_CLOCK)
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    write_yaml(paths.concepts_path, {"schema_version": 1, "concepts": {
        concept["id"]: {"title": concept["title"], "type": concept["type"], "aliases": [], "description": None,
                        "tags": [], "created_at": _NOW, "updated_at": _NOW}
        for concept in data["concepts"]
    }})
    write_yaml(paths.relations_path, {"schema_version": 1, "edges": [
        {"id": f"edge_{index}", "relation_type": edge["relation_type"], "source": edge["source"],
         "target": edge["target"], "strength": 1.0, "rationale": None, "created_at": _NOW, "updated_at": _NOW}
        for index, edge in enumerate(data["edges"])
    ]})
    write_yaml(paths.facets_path, {"schema_version": 2, "facets": [
        {**facet, "aliases": [], "status": "reviewed", "version": 1,
         "provenance": {"origin": "sourceset_synthesis", "source_refs": []}}
        for facet in data["facets"]
    ]})
    loaded = load_vault(root)
    assert loaded.issues == []
    return root, Repository(VaultPaths(loaded.root, loaded.config).sqlite_path), data


def _study_judge(data: dict, **kwargs) -> FakeFacetJudge:
    """A fake judge that merges exactly the study's merge-worthy clusters."""

    claim_of = {facet["id"]: judge_view(facet)["claim"] for facet in data["facets"]}
    clusters = [[claim_of[facet_id] for facet_id in cluster] for cluster in clusters_from_pairs(data["must_merge"])]
    return FakeFacetJudge(clusters=clusters, **kwargs)
