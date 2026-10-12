"""Facet dossiers: grounded, capped, idempotent paid outputs; never rebuilt."""
from __future__ import annotations

import json

import pytest

from learnloop.ai.spend import SpendCaps
from learnloop.db.repositories import Repository
from learnloop.practice_index.dossiers import build_plans, dossier_status, generate_dossiers
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.embedding_recipes import EMBEDDING_RECIPES, embedding_records
from learnloop.vault.loader import load_vault
from learnloop.vault.repository import open_vault_repository
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.helpers import write_facets
from tests.practice_index_fakes import (
    FakePracticeLLM,
    build_practice_vault,
    enable_practice_index,
    facet_definitions,
)

CAPS = SpendCaps(max_candidates=100, max_calls=100, max_retries=2,
                 max_total_tokens=1_000_000, max_estimated_usd=1.0)


@pytest.fixture
def practice(tmp_path):
    paths = build_practice_vault(tmp_path / "vault")
    enable_practice_index(paths, embeddings=False)
    open_vault_repository(paths.root, paths.sqlite_path)
    return paths


def _rows(paths):
    with Repository(paths.sqlite_path).connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM facet_dossiers ORDER BY facet_id, created_at")]


def test_grounding_excludes_answers_diagnostic_surfaces_and_exam_reserves(practice):
    paths = practice
    item_path = paths.practice_item_path("linear-algebra", "pi_eigen_2")
    write_yaml(item_path, {**read_yaml(item_path), "practice_mode": "diagnostic_probe"})
    repository = Repository(paths.sqlite_path)
    repository.insert_exam_pool_items([{
        "id": "epi_1", "goal_id": "goal_linear_algebra_ml", "practice_item_id": "pi_eigen_3",
        "reserved_at": "2026-10-12T00:00:00Z",
    }])
    vault = load_vault(paths.root)
    plans = {plan.facet_id: plan for plan in build_plans(vault, repository)}
    assert set(plans) == {f["id"] for f in facet_definitions()}
    eigen = plans["facet_eigen"]
    prompts = [entry["prompt"] for entry in eigen.grounding["items"]]
    assert prompts == [vault.practice_items["pi_eigen_1"].prompt]
    assert eigen.grounding["rubric_criteria"] == ["Correct work for pi_eigen_1."]
    for plan in plans.values():
        assert "ANSWER-" not in plan.prompt
        assert vault.practice_items["pi_eigen_2"].prompt not in plan.prompt
        assert vault.practice_items["pi_eigen_3"].prompt not in plan.prompt
    # Neighbours: shared learning objects first, then the shared concept.
    assert [n["title"] for n in plans["facet_independence"].grounding["neighbors"]][0] == "Span"


def test_dry_run_estimates_without_a_client_or_writes(practice):
    paths = practice
    before = paths.sqlite_path.read_bytes()
    report = generate_dossiers(load_vault(paths.root), caps=CAPS, dry_run=True)
    assert report["status"] == "dry_run"
    assert report["pending"] == 6
    assert report["estimate"]["calls"] == 6
    assert report["estimate"]["billing"] == "subscription"  # the template routes Codex
    assert report["estimate"]["cost_basis"] == "estimated_only"
    assert report["estimate"]["estimated_tokens"] > 0
    assert report["estimate"]["marginal_usd"] == 0.0
    assert paths.sqlite_path.read_bytes() == before


def test_generation_is_capped_idempotent_and_receipted(practice):
    paths = practice
    llm = FakePracticeLLM()
    vault = load_vault(paths.root)
    first = generate_dossiers(vault, caps=CAPS, client=llm)
    assert first["status"] == "complete", first
    assert first["generated"] == 6
    assert first["usage"]["estimated_only_tokens"] > 0
    assert first["charged"]["total_tokens"] == 0  # subscription: no token or dollar charge
    assert first["charged"]["calls"] == 6
    second = generate_dossiers(vault, caps=CAPS, client=llm)
    assert second["status"] == "complete" and second["pending"] == 0
    assert len(llm.calls) == 6
    rows = _rows(paths)
    assert len(rows) == 6
    eigen = next(row for row in rows if row["facet_id"] == "facet_eigen")
    assert eigen["scope"].startswith("Covers:\n- Eigenvalues and eigenvectors")
    assert "Excludes:\n- proof theory" in eigen["scope"]
    assert eigen["moves"].startswith("1. ")
    assert eigen["contrast"].startswith("- Versus ")
    assert eigen["billing"] == "subscription"
    with Repository(paths.sqlite_path).connection() as connection:
        receipts = connection.execute(
            "SELECT budget_json FROM model_call_receipts WHERE owner_kind='practice_dossiers' "
            "AND parent_call_id IS NULL").fetchall()
    assert len(receipts) == 6
    declared = json.loads(receipts[0][0])
    assert declared["practice_index"]["billing"] == "subscription"
    assert declared["practice_index"]["cost_basis"] == "estimated_only"
    assert declared["practice_index"]["prompt_version"] == "facet_dossier.v1"
    assert declared["max_calls"] == CAPS.max_calls
    assert "ANSWER-" not in json.dumps(first)


def test_call_caps_still_bind_a_subscription_route(practice):
    paths = practice
    llm = FakePracticeLLM()
    capped = SpendCaps(max_candidates=100, max_calls=2, max_retries=0,
                       max_total_tokens=0, max_estimated_usd=0.0)
    report = generate_dossiers(load_vault(paths.root), caps=capped, client=llm)
    assert report["status"] == "over_budget"
    assert llm.calls == []


def test_regenerated_only_when_the_facet_or_its_sources_change(practice):
    paths = practice
    llm = FakePracticeLLM()
    generate_dossiers(load_vault(paths.root), caps=CAPS, client=llm)
    # An answer edit is not a dossier source.
    item_path = paths.practice_item_path("linear-algebra", "pi_span_1")
    write_yaml(item_path, {**read_yaml(item_path), "expected_answer": "changed"})
    # (Dossiers are keyed by model, so planning names the same fake model.)
    assert generate_dossiers(load_vault(paths.root), caps=CAPS, dry_run=True, client=llm)["pending"] == 0
    # A facet edit regenerates that facet and the facets that contrast with it.
    facets = facet_definitions()
    next(f for f in facets if f["id"] == "facet_span")["claim"] = "Describe every linear combination."
    write_facets(paths, facets)
    vault = load_vault(paths.root)
    status = dossier_status(vault, Repository(paths.sqlite_path))
    assert status["counts"] == {"current": 4, "stale": 1, "missing": 1}
    report = generate_dossiers(vault, caps=CAPS, client=llm)
    assert report["generated"] == 2
    assert [payload["context"]["facet"]["id"] for _, payload in llm.calls[-2:]] == [
        "facet_independence", "facet_span",
    ]
    # A new item testing a facet changes that facet's sources only.
    new_item = {**read_yaml(paths.practice_item_path("linear-algebra", "pi_orthogonal_1")),
                "id": "pi_orthogonal_4", "prompt": "Find a vector orthogonal to (1,1).",
                "created_at": "2026-12-01T00:00:00Z"}
    write_yaml(paths.practice_item_path("linear-algebra", "pi_orthogonal_4"), new_item)
    calls = len(llm.calls)
    report = generate_dossiers(load_vault(paths.root), caps=CAPS, dry_run=True, client=llm)
    assert report["pending"] == 1
    assert len(llm.calls) == calls  # a dry run never calls the client


def test_switch_off_and_unknown_metered_price_fail_closed(tmp_path):
    paths = build_practice_vault(tmp_path / "vault")
    open_vault_repository(paths.root, paths.sqlite_path)
    llm = FakePracticeLLM()
    vault = load_vault(paths.root)
    assert generate_dossiers(vault, caps=CAPS, client=llm)["status"] == "disabled"
    enable_practice_index(paths, embeddings=False)
    vault = load_vault(paths.root)
    metered = FakePracticeLLM(provider_type="openrouter")
    report = generate_dossiers(vault, caps=CAPS, client=metered)
    assert report["status"] == "over_budget"
    assert "--price-per-million" in report["reason"]
    priced = generate_dossiers(vault, caps=CAPS, client=metered, price_per_million=2.0)
    assert priced["status"] == "complete"
    assert priced["charged"]["total_tokens"] > 0  # metered: tokens and dollars are charged
    assert priced["charged"]["estimated_usd"] > 0
    assert llm.calls == []


def test_an_unusable_answer_is_retried_then_reported_per_facet(practice):
    paths = practice

    class Empty(FakePracticeLLM):
        def _practice_dossier(self, context):
            draft = super()._practice_dossier(context)
            if context["facet"]["id"] == "facet_span":
                return draft.model_copy(update={"moves": []})
            return draft

    llm = Empty()
    report = generate_dossiers(load_vault(paths.root), caps=CAPS, client=llm)
    assert report["status"] == "partial"
    assert report["failed"] == [{"facet_id": "facet_span", "error_type": "AIInvalidOutput"}]
    assert report["generated"] == 5
    assert report["charged"]["retries"] == 2


def test_dossier_fields_are_embedding_recipes(practice):
    paths = practice
    vault = load_vault(paths.root)
    assert not [r for r in embedding_records(vault, ("facet",)) if r.field.startswith("dossier_")]
    generate_dossiers(vault, caps=CAPS, client=FakePracticeLLM())
    records = embedding_records(load_vault(paths.root), ("facet/dossier_scope", "facet/dossier_moves"))
    assert {(r.field, r.record_id) for r in records} == {
        (field, f["id"]) for field in ("dossier_scope", "dossier_moves") for f in facet_definitions()
    }
    assert EMBEDDING_RECIPES["facet/dossier_contrast"].version == 1


@pytest.mark.durability
def test_rebuild_preserves_dossiers_and_calls_no_model(practice, monkeypatch):
    from learnloop.ai import client

    paths = practice
    generate_dossiers(load_vault(paths.root), caps=CAPS, client=FakePracticeLLM())
    before = _rows(paths)

    def forbidden(*args, **kwargs):
        raise AssertionError("replay must not construct a model")

    monkeypatch.setattr(client, "make_ai_provider_client", forbidden)
    monkeypatch.setattr(client, "make_ai_provider_client_from_profile", forbidden)
    for _ in range(2):
        rebuild_all_derived_state(load_vault(paths.root), Repository(paths.sqlite_path))
    assert _rows(paths) == before


def test_a_paid_answer_survives_a_failed_write_and_is_not_paid_again(practice, monkeypatch):
    """F8: the response is checkpointed before insert_dossier; a rerun recovers it."""
    import sqlite3

    from learnloop.practice_index import dossiers as dossiers_module

    paths = practice
    llm = FakePracticeLLM()
    real_insert = dossiers_module.insert_dossier

    def failing_insert(connection, **values):
        if values["facet_id"] == "facet_span":
            raise sqlite3.OperationalError("disk I/O error")
        return real_insert(connection, **values)

    monkeypatch.setattr(dossiers_module, "insert_dossier", failing_insert)
    with pytest.raises(sqlite3.OperationalError):
        generate_dossiers(load_vault(paths.root), caps=CAPS, client=llm)
    paid = [payload["context"]["facet"]["id"] for _, payload in llm.calls]
    assert "facet_span" in paid and "facet_span" not in {row["facet_id"] for row in _rows(paths)}
    monkeypatch.setattr(dossiers_module, "insert_dossier", real_insert)
    planned = generate_dossiers(load_vault(paths.root), caps=CAPS, dry_run=True, client=llm)
    assert planned["recoverable"] == 1
    assert planned["estimate"]["calls"] == planned["pending"] - 1
    report = generate_dossiers(load_vault(paths.root), caps=CAPS, client=llm)
    assert report["status"] == "complete", report
    assert report["usage"]["recovered"] == 1
    assert [payload["context"]["facet"]["id"] for _, payload in llm.calls].count("facet_span") == 1
    assert len(_rows(paths)) == 6


class _ItemAware(FakePracticeLLM):
    """Dossier text that depends on the grounding items, so revisions differ."""

    def _practice_dossier(self, context):
        draft = super()._practice_dossier(context)
        first = context["items"][0]["prompt"] if context.get("items") else "none"
        return draft.model_copy(update={"covers": [*draft.covers, f"grounded on {first}"]})


def test_reverting_sources_selects_the_matching_earlier_dossier(practice):
    """F4: selection uses the current source hash, so a revert reuses revision A."""
    from learnloop.practice_index.retrieval import load_snapshot

    paths = practice
    llm = _ItemAware()
    item_path = paths.practice_item_path("linear-algebra", "pi_orthogonal_1")
    original = read_yaml(item_path)
    generate_dossiers(load_vault(paths.root), caps=CAPS, client=llm)
    vault = load_vault(paths.root)
    plan_a = {plan.facet_id: plan for plan in build_plans(vault, Repository(paths.sqlite_path))}
    write_yaml(item_path, {**original, "prompt": "Find the angle between two orthogonal vectors."})
    report = generate_dossiers(load_vault(paths.root), caps=CAPS, client=llm)
    assert report["generated"] == 1  # sources B
    write_yaml(item_path, original)  # back to sources A: already paid for
    vault = load_vault(paths.root)
    assert generate_dossiers(vault, caps=CAPS, client=llm, dry_run=True)["pending"] == 0
    repository = Repository(paths.sqlite_path)
    status = dossier_status(vault, repository)
    assert status["counts"] == {"current": 6, "stale": 0, "missing": 0}
    selected = load_snapshot(vault, repository).dossiers["facet_orthogonal"]
    assert selected.source_hash == plan_a["facet_orthogonal"].source_hash
    assert "grounded on Are (1,2) and (2,-1) orthogonal" in selected.scope
    # The embedding recipe offers revision A's text, so the backfill can embed it.
    scopes = {record.text for record in embedding_records(vault, ("facet/dossier_scope",))
              if record.record_id == "facet_orthogonal"}
    assert selected.scope in scopes
    # After the backfill, retrieval finds revision A's vectors for every field.
    from learnloop.ops.embedding_backfill import backfill_embeddings
    from tests.practice_index_fakes import HashingEmbedder

    vault.config.embedding.enabled = vault.config.embedding.backfill_enabled = True
    vault.config.embedding.dimensions = 64
    embedder = HashingEmbedder()
    backfilled = backfill_embeddings(vault, caps=SpendCaps(max_candidates=1000, max_calls=100,
                                                           max_total_tokens=10_000_000),
                                     client_factory=lambda: embedder)
    assert backfilled["status"] == "complete", backfilled
    snapshot = load_snapshot(vault, repository, embedder=embedder)
    assert snapshot.dossier_vectors_complete and snapshot.dossier_available
    assert snapshot.dossiers["facet_orthogonal"].id == selected.id


def test_select_dossier_prefers_current_sources_then_the_intended_model():
    from learnloop.db.stores.practice_index import DossierRow
    from learnloop.practice_index.dossiers import DOSSIER_PROMPT_VERSION, select_dossier

    def row(name, source, model, version=DOSSIER_PROMPT_VERSION):
        return DossierRow(name, "facet", "fh", source, model, version, "s", "m", "e", "c", name)

    a_m1, b_m1, a_m2 = row("1", "A", "m1"), row("2", "B", "m1"), row("3", "A", "m2")
    rows = [a_m1, b_m1, a_m2]
    assert select_dossier(rows, source_hash="A", model_id="m1") == (a_m1, "current")
    assert select_dossier(rows, source_hash="A", model_id="m2") == (a_m2, "current")
    assert select_dossier(rows, source_hash="A", model_id="other") == (a_m2, "current")
    assert select_dossier(rows, source_hash="B", model_id="m2") == (b_m1, "current")
    assert select_dossier(rows, source_hash="C", model_id="m1") == (a_m2, "stale")
    old_prompt = [row("4", "A", "m1", version="facet_dossier.v0")]
    assert select_dossier(old_prompt, source_hash="A", model_id="m1")[1] == "stale"
