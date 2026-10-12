"""Slice 2 T5 report: nomination recall on doctor-found duplicates (spec §13)."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from learnloop.ai.spend import SpendCaps
from learnloop.cli import app
from learnloop.db.repositories import Repository
from learnloop.db.stores.judgments import append_judgment
from learnloop.ops.graph_nomination_report import REPORT_RECIPES, nomination_report
from learnloop.vault.loader import load_vault
from learnloop.vault.models import Concept, EvidenceFacet

from tests.embedding_fakes import BagOfWordsEmbedder, ExplodingFactory
from tests.helpers import create_basic_vault

NOW = "2026-10-12T00:00:00+00:00"
CAPS = SpendCaps(max_candidates=1000, max_total_tokens=10**7)


@pytest.fixture
def vault(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    loaded = load_vault(paths.root)
    config = loaded.config
    config.embedding.enabled = True
    config.embedding.backfill_enabled = True
    config.embedding.dimensions = 64
    config.graph_nomination.top_k = 2
    claim = "A real symmetric matrix is orthogonally diagonalizable by the spectral theorem"
    loaded.evidence_facets.update({
        "facet_spectral": EvidenceFacet(
            id="facet_spectral", claim=claim,
            instructional_repairs=["check symmetry before invoking the spectral theorem"],
            error_signatures=["applies the theorem to a non-symmetric matrix"],
        ),
        # A lexical near-duplicate the doctor finds (Jaccard >= 0.85).
        "facet_spectral_restated": EvidenceFacet(
            id="facet_spectral_restated", claim=claim + " too",
            instructional_repairs=["before invoking the spectral theorem check symmetry"],
            error_signatures=["applies the theorem to a non-symmetric matrix"],
        ),
        "facet_elimination": EvidenceFacet(
            id="facet_elimination", claim="Gaussian elimination reaches row echelon form",
            instructional_repairs=["practise one pivot at a time"],
        ),
        "facet_trace": EvidenceFacet(
            id="facet_trace", claim="The trace equals the sum of the eigenvalues",
        ),
    })
    loaded.concepts.clear()
    for concept_id, title, description, aliases in (
        ("concept_symmetric", "Symmetric matrix", "A square matrix equal to its own transpose.", []),
        # A doctor strong-alias pair: it shares the surface "symmetric matrix".
        ("concept_symmetric_matrices", "Symmetric matrices",
         "Square matrices equal to their transposes.", ["symmetric matrix"]),
        ("concept_elimination", "Gaussian elimination", "Row reduction to echelon form.", []),
    ):
        loaded.concepts[concept_id] = Concept(
            title=title, description=description, aliases=aliases, created_at=NOW, updated_at=NOW,
        )
    return loaded, paths


def test_dry_run_plans_the_backfill_without_calls_or_changes(vault):
    loaded, paths = vault
    before = paths.sqlite_path.read_bytes()
    factory = ExplodingFactory()
    report = nomination_report(loaded, caps=CAPS, dry_run=True, client_factory=factory)
    assert report["status"] == "dry_run" and factory.calls == 0
    assert paths.sqlite_path.read_bytes() == before
    assert report["backfill"]["recipes"] == sorted(REPORT_RECIPES)
    assert report["backfill"]["pending"] == 4 + 3 + 3  # facets, concepts, distinct repairs
    assert report["ground_truth"]["facet"]["doctor_near_duplicate"] == 1
    assert report["ground_truth"]["concept"] == {"doctor_strong_alias": 1}
    assert "facets" not in report  # nothing is computed in a dry run


@pytest.mark.durability
def test_report_measures_recall_cutoffs_noise_and_the_repair_shadow(vault):
    loaded, paths = vault
    embedder = BagOfWordsEmbedder()
    report = nomination_report(loaded, caps=CAPS, client_factory=lambda: embedder)
    assert report["status"] == "complete", report
    facets = report["facets"]
    assert facets["index_status"] == "complete"
    assert facets["recall"]["doctor_near_duplicate"]["recall@1"] == 1.0
    assert facets["recall"]["all"]["n"] >= 1
    assert set(facets["cosine_at_recall"]) == {"90%", "95%", "100%"}
    assert facets["noise_floor"]["n"] == 6  # 4 facets -> 6 pairs
    assert facets["missed_at_top_k"] == []
    assert "Unjudged" in facets["embedding_only_mutual_nearest"]["note"]
    assert report["concepts"]["index_status"] == "complete"
    assert report["concepts"]["recall"]["doctor_strong_alias"]["recall@1"] == 1.0
    shadow = report["repair_shadow"]
    assert shadow["d2_pairs_with_repairs"] >= 1
    assert shadow["text_says_distinct_repair"] >= 1
    assert shadow["min_best_cosine_of_text_distinct"]["max"] > 0.99
    calls = len(embedder.calls)
    rerun = nomination_report(loaded, caps=CAPS, client_factory=lambda: embedder)
    assert rerun["backfill"]["pending"] == 0 and len(embedder.calls) == calls
    assert rerun["facets"]["recall"] == facets["recall"]


def test_stored_only_reports_without_paying(vault):
    loaded, _paths = vault
    factory = ExplodingFactory()
    report = nomination_report(loaded, caps=CAPS, stored_only=True, client_factory=factory)
    assert factory.calls == 0
    assert report["status"] == "complete"
    assert report["facets"]["index_status"] == "index_incomplete"
    assert "run the backfill" in report["facets"]["note"]


def test_ledger_same_verdicts_join_the_ground_truth(vault):
    loaded, paths = vault
    with Repository(paths.sqlite_path).connection() as connection:
        append_judgment(
            connection, task="same_concept", left_kind="concept", left_id="concept_symmetric",
            right_kind="concept", right_id="concept_elimination", judge="owner",
            input_hash="h", verdict="same",
        )
        append_judgment(
            connection, task="same_concept", left_kind="concept_candidate", left_id="abc",
            right_kind="concept", right_id="concept_symmetric", judge="llm",
            judge_model="m", prompt_version="p", input_hash="h2", verdict="same",
        )
    report = nomination_report(loaded, caps=CAPS, stored_only=True)
    assert report["ground_truth"]["concept"]["ledger_same"] == 1
    assert {(row["judge"], row["count"]) for row in report["ledger"]} == {("owner", 1), ("llm", 1)}


def test_cli_dry_run_and_flag_conflict(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    before = paths.sqlite_path.read_bytes()
    result = CliRunner().invoke(app, [
        "embeddings", "nomination-report", "--vault", str(paths.root), "--dry-run", "--json",
    ])
    assert result.exit_code == 0, result.output
    report = json.loads(result.stdout)
    assert report["status"] == "dry_run" and report["backfill"]["status"] == "dry_run"
    assert paths.sqlite_path.read_bytes() == before
    conflict = CliRunner().invoke(app, [
        "embeddings", "nomination-report", "--vault", str(paths.root), "--dry-run", "--stored-only",
    ])
    assert conflict.exit_code == 1
    assert json.loads(conflict.stdout)["status"] == "invalid"
