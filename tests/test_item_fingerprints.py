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
        ("parameter_template", "parameters"), ("solution_recipe", "skeleton:m@unversioned"),
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


def test_skeletons_from_one_model_at_two_prompt_versions_rebuild_without_a_key_collision(tmp_path):
    """Codex review F4: a prompt upgrade (or a published item later used as a parent,
    re-skeletonised by the same model) leaves two skeletons per item and model."""
    from learnloop.db.stores.pf import insert_skeleton
    from learnloop.vault.hashes import skeleton_content_hash

    vault, repository, _ = seed_pf_vault(tmp_path / "vault")
    item = vault.practice_items["pi_linear_001"]
    content_hash = skeleton_content_hash(item.prompt, item.expected_answer)
    with repository.connection() as connection:
        for version, techniques in (("pf-ensemble-propose-v1", ["isolate", "divide"]),
                                    ("pf-skeleton-v1", ["subtract", "divide", "check"])):
            insert_skeleton(connection, skeleton_id=f"sk_{version}", content_hash=content_hash,
                            subject_kind="practice_item", subject_id=item.id, model_id="same-model",
                            prompt_version=version, techniques=techniques, operations=[],
                            checkpoints=["c"], skeleton_text="t", created_at="2026-10-12T00:00:00Z")
    rebuild_all_derived_state(vault, repository)
    rows = [row for row in item_fingerprints_snapshot(repository)
            if row["practice_item_id"] == item.id and row["namespace"] == "solution_recipe"]
    assert len(rows) == 2 and len({row["component"] for row in rows}) == 2
    assert {row["fingerprint_version"] for row in rows} == {fp.FINGERPRINT_VERSION}
    # Matching still works across versions and models on the technique sequence.
    keys = fp.item_fingerprint_keys(item, skeletons=[{"model_id": "other", "prompt_version": "v9",
                                                      "techniques": ["Subtract", "divide", "check"]}])
    stored = [(row["namespace"], row["component"], row["value_hash"]) for row in rows]
    assert ("solution_recipe", "skeleton") in fp.shared_keys(keys, stored)


@needs_bwrap
def test_a_published_item_later_used_as_the_parent_rebuilds(tmp_path):
    """F4 end to end: the proposer and the skeleton writer are the same model."""
    from learnloop.vault.writer import upsert_practice_item
    from tests.pf_fakes import PFFake

    _, repository, paths = seed_pf_vault(tmp_path / "vault")
    same = PFFake("fake-a")
    fakes = clients(skeleton=same, proposer=[same, PFFake("fake-b")])
    first = generate_practice(load_vault(paths.root), caps=CAPS, price_per_million=1.0, clients=fakes,
                              options=GenerationOptions(path="ensemble", round="r1"))
    assert first["published_item_ids"]
    parent = load_vault(paths.root).practice_items["pi_linear_001"].model_dump(mode="json")
    parent["status"] = "retired"
    upsert_practice_item(paths.root, parent)  # a published item becomes the family's parent
    second = generate_practice(load_vault(paths.root), caps=CAPS, price_per_million=1.0, clients=fakes,
                               options=GenerationOptions(path="ensemble", round="r2"))
    assert second["families"][0]["parent_item_id"] in first["published_item_ids"]
    rebuild_all_derived_state(load_vault(paths.root), repository)
    new_parent = second["families"][0]["parent_item_id"]
    components = [row["component"] for row in item_fingerprints_snapshot(repository)
                  if row["practice_item_id"] == new_parent and row["namespace"] == "solution_recipe"]
    assert len(components) == len(set(components)) >= 2
