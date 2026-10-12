"""Item fingerprints (DERIVED), replay invariants and job isolation for PF-b (Slice 2 §5.4, §13)."""
from __future__ import annotations

import pytest

from learnloop.ai.spend import SpendCaps
from learnloop.content.authoring import pf_sandbox
from learnloop.content.authoring.pf_sandbox import sandbox_available
from learnloop.db.stores.pf import item_fingerprints
from learnloop.learner.familiarity import NAMESPACES
from learnloop.ops.pf_generation import GenerationOptions, generate_practice
from learnloop.substrate import item_fingerprints as fp
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from tests.helpers import create_basic_vault
from tests.pf_fakes import clients, seed_pf_vault

needs_bwrap = pytest.mark.skipif(not sandbox_available(), reason="bubblewrap is not installed")
CAPS = SpendCaps(max_candidates=100, max_pairs=2000, max_calls=2000, max_total_tokens=10**9, max_estimated_usd=10**4)


def test_keys_use_the_077_namespaces_and_never_mix_them():
    keys = fp.fingerprint_keys(
        prompt="Solve 2x + 4 = 10 for x.", expected_answer="Final answer: 3\n\nWork.",
        skeletons=[{"model_id": "m", "techniques": ["isolate", "divide"]}],
        generator_hash="g", parameters={"a": 2}, sympy_normal_form="Integer(3)",
    )
    assert {namespace for namespace, _, _ in keys} <= set(NAMESPACES)
    assert {(namespace, component) for namespace, component, _ in keys} == {
        ("surface_hash", "stem"), ("verbatim_target", "answer"), ("verbatim_target", "answer_quantities"),
        ("verbatim_target", "answer_sympy"), ("parameter_template", "generator"),
        ("parameter_template", "parameters"), ("solution_recipe", "skeleton:m"),
    }
    assert fp.EXACT_COMPONENTS == {("surface_hash", "stem"), ("parameter_template", "parameters")}


def test_normalization_is_surface_insensitive_but_parameter_sensitive():
    a = fp.fingerprint_keys(prompt="Solve 2x + 4 = 10 for x.", expected_answer="Final answer: 3.0")
    b = fp.fingerprint_keys(prompt="  SOLVE 2x + 4 = 10  for x.", expected_answer="final answer: 3")
    c = fp.fingerprint_keys(prompt="Solve 3x + 4 = 10 for x.", expected_answer="Final answer: 2")
    assert dict(((n, k), v) for n, k, v in a) == dict(((n, k), v) for n, k, v in b)
    assert ("surface_hash", "stem") not in fp.shared_keys(a, c)
    assert fp.key_quantities("Solve 2x + 04 = 10.50") == ["10.5", "2", "4"]
    assert fp.final_answer_text({"final_answer": 7}) == "7"
    # Skeleton keys match across models on the technique sequence alone.
    left = fp.fingerprint_keys(prompt="p", expected_answer="", skeletons=[{"model_id": "x", "techniques": ["A", "B"]}])
    right = fp.fingerprint_keys(prompt="q", expected_answer="", skeletons=[{"model_id": "y", "techniques": ["a", "b"]}])
    assert ("solution_recipe", "skeleton") in fp.shared_keys(left, right)


def test_a_vault_without_families_has_no_fingerprint_rows(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    from learnloop.db.repositories import Repository

    repository = Repository(paths.sqlite_path)
    before = item_fingerprints_snapshot(repository)
    rebuild_all_derived_state(vault, repository)
    assert item_fingerprints_snapshot(repository) == before == []


def item_fingerprints_snapshot(repository):
    with repository.connection() as connection:
        return item_fingerprints(connection)


@needs_bwrap
def test_rebuild_recomputes_fingerprints_without_any_model_or_generator(tmp_path, monkeypatch):
    _, repository, paths = seed_pf_vault(tmp_path / "vault")
    for path in ("generator", "ensemble"):
        report = generate_practice(load_vault(paths.root), caps=CAPS, price_per_million=1.0, clients=clients(),
                                   options=GenerationOptions(path=path, round=f"r-{path}"))
        assert report["status"] == "complete"
    vault = load_vault(paths.root)
    published = [item for item in vault.practice_items.values() if "pf_generated" in item.tags]
    assert published

    def forbidden(*args, **kwargs):
        raise AssertionError("replay must never execute a generator or call a model")

    monkeypatch.setattr(pf_sandbox, "run_sandboxed_python", forbidden)
    monkeypatch.setattr(pf_sandbox, "_sandbox_bwrap_path", forbidden)
    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task", forbidden)
    monkeypatch.setattr("learnloop.ai.transport.execute_structured_operation", forbidden)
    rebuild_all_derived_state(vault, repository)
    first = item_fingerprints_snapshot(repository)
    rebuild_all_derived_state(load_vault(paths.root), repository)
    assert item_fingerprints_snapshot(repository) == first
    by_item = {}
    for row in first:
        by_item.setdefault(row["practice_item_id"], set()).add((row["namespace"], row["component"]))
    assert set(by_item) == {item.id for item in vault.practice_items.values() if item.family_id}
    generator_items = [item.id for item in published if "pf_path_generator" in item.tags]
    for item_id in generator_items:
        assert ("parameter_template", "parameters") in by_item[item_id]
        assert ("verbatim_target", "answer_sympy") in by_item[item_id]
    assert all(("solution_recipe", component) in by_item[item.id]
               for item in published for component in {c for n, c in by_item[item.id] if n == "solution_recipe"})


@needs_bwrap
def test_generic_rotation_claims_never_take_pf_generation_jobs(tmp_path):
    from learnloop.substrate.surface_mint import claim_next_mint_job, request_candidates

    _, repository, paths = seed_pf_vault(tmp_path / "vault")
    generate_practice(load_vault(paths.root), caps=CAPS, price_per_million=1.0, clients=clients(),
                      options=GenerationOptions(path="ensemble", round="r1", publish=False))
    with repository.connection() as connection:
        pf_jobs = connection.execute(
            "SELECT id, status FROM surface_mint_requests WHERE generator_version LIKE 'pf_%'").fetchall()
        connection.execute("UPDATE surface_mint_requests SET status='pending'")
        connection.commit()
    assert pf_jobs
    assert claim_next_mint_job(repository, worker_id="rotation") is None
    card_version = connection_card_version(repository)
    request_candidates(repository, card_version_id=card_version)
    claimed = claim_next_mint_job(repository, worker_id="rotation")
    assert claimed is not None and not claimed["generator_version"].startswith("pf_")


def connection_card_version(repository):
    with repository.connection() as connection:
        return connection.execute("SELECT id FROM activity_card_versions LIMIT 1").fetchone()[0]
