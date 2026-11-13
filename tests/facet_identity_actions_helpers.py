"""What other test files use from ``tests/test_facet_identity_actions.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.content.facet_identity.actions import merge_registered_facets
from learnloop.db.repositories import Repository
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW, write_facets
from tests.km2_write_path_helpers import SELECT, SHARED, _attempt, _item, _rubric, build_shared_facet_vault


DUP = "facet_svd_factorization_restated"
_CLOCK = FrozenClock(datetime(2026, 10, 12, 12, 0, 0, tzinfo=UTC))


def _vault_with_duplicate(tmp_path):
    paths = build_shared_facet_vault(tmp_path / "vault")
    write_facets(paths, [
        {"id": SHARED, "kind": "definition", "claim": "SVD factorizes into U, Sigma, V^T.",
         "positive_examples": ["A = U Sigma V^T for a 2x2 matrix"]},
        {"id": SELECT, "kind": "applicability_condition", "claim": "When SVD applies."},
        {"id": "recall", "kind": "definition", "claim": "SVD recall."},
        {"id": DUP, "kind": "definition", "claim": "Every matrix A can be written A = U Sigma V^T.",
         "preconditions": ["A is a real matrix"]},
    ])
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_restated_001"),
        _item(
            "pi_svd_restated_001", "lo_svd_application", evidence_facets=[DUP],
            rubric=_rubric("states_factorization", [{"facet": DUP, "capability": "retrieval", "role": "primary"}],
                           correlation_group="svd_restated"),
            fingerprint={"source_family": "chapter9-restated"},
        ),
    )
    lo_path = paths.learning_object_path("linear-algebra", "lo_svd_application")
    lo = read_yaml(lo_path)
    lo["blueprints"] = [{"id": "bp_apply", "weight": 1.0, "recipes": [{
        "id": "recipe_apply", "composition": "conjunctive",
        "all_of": [{"facet": DUP, "capability": "retrieval", "modality": "hard"}], "any_of": [],
        "integration": None,
    }]}]
    write_yaml(lo_path, lo)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return paths, load_vault(paths.root), repository


def _belief(repository: Repository) -> list[tuple]:
    return sorted(
        (state.facet_id, state.capability_key, state.practice_item_id or "", round(state.recall_alpha, 9),
         round(state.recall_beta, 9), round(state.independent_evidence_mass, 9))
        for state in repository.canonical_facet_recall_states()
    )


def _merge(paths, repository, **kwargs):
    """Merge DUP into SHARED. These fixtures' facets have probe episodes from the
    first sync, which used to lock them; facet locks were removed (owner,
    2026-10-12), so nothing about their history refuses a merge."""

    return merge_registered_facets(
        paths.root, repository, survivor=SHARED, retired=[DUP], action=kwargs.pop("action", "merge"),
        absorb_as=kwargs.pop("absorb_as", None), origin="dedupe", run_id="run1", judge="llm",
        judge_model="fake-judge-1", prompt_version="v1", clock=_CLOCK, **kwargs,
    )


def _lock_shared(vault, repository):
    # Two distinct surface groups: what used to lock SHARED (knowledge model §3.4).
    _attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, FrozenClock(NOW))
    _attempt(vault, repository, "pi_svd_apply_001", {"uses_factorization": 4}, FrozenClock(NOW))
