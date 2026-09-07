"""Start-screen epigraphs (vault_epigraphs.py): validation, persistence, and
the never-raises contract around the one extra model call a synthesis makes."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from learnloop.ai.usage import TokenUsage
from learnloop.clock import FrozenClock
from learnloop.content.synthesis import vault_epigraphs as VE
from learnloop.content.synthesis.ai_contracts import (
    VAULT_EPIGRAPHS_PROMPT_VERSION,
    VaultEpigraph,
    VaultEpigraphBatch,
    VaultEpigraphContext,
)
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import add_subject, init_vault, load_vault
from tests.structured_ai import StructuredClientFake

_CLOCK = FrozenClock(datetime(2026, 9, 3, 12, 0, 0, tzinfo=UTC))

GOOD = VaultEpigraphBatch(
    epigraphs=[
        VaultEpigraph(kind="quote", lines=["Symmetry is a promise the transpose keeps."]),
        VaultEpigraph(kind="haiku", lines=["A equals A T", "the spectral theorem waits", "eigenvectors align"]),
        VaultEpigraph(kind="quote", lines=["Escape will make me diagonal."]),
    ]
)


class FakeClient(StructuredClientFake):
    provider_name = "fake"
    model = "fake-model"

    def __init__(self, batch: VaultEpigraphBatch | None = None, *, raise_with: Exception | None = None):
        self.calls: list[VaultEpigraphContext] = []
        self.batch = batch or GOOD
        self.raise_with = raise_with
        self.drained = 0

    def run_vault_epigraphs(self, context):
        self.calls.append(context)
        if self.raise_with is not None:
            raise self.raise_with
        return self.batch

    def consume_usage(self) -> TokenUsage:
        self.drained += 1
        return TokenUsage(input_tokens=10, output_tokens=5)


def _setup(tmp_path: Path):
    root = tmp_path / "vault"
    init_vault(root, clock=_CLOCK)
    add_subject(root, "linear-algebra", "Linear Algebra", clock=_CLOCK)
    return load_vault(root), Repository(root / "state.sqlite")


def _digest():
    return VE.ContentDigest(
        summary="bootstrap map for symmetric matrices",
        concepts=["Symmetric matrix"],
        claims=["A real square matrix is symmetric when A^T = A."],
        learning_objects=["Diagonalize a symmetric matrix"],
    )


def _generate(repo, vault, client, **overrides):
    kwargs = dict(subject_id="linear-algebra", source_set_id="set_la", synthesis_run_id="run_1",
                  mode="bootstrap", digest=_digest(), brief={"depth": "intro", "secret": {"x": 1}},
                  clock=_CLOCK)
    kwargs.update(overrides)
    return VE.generate_vault_epigraphs(repo, vault, client, **kwargs)


def test_prompt_round_trips_through_the_structured_fake():
    client = FakeClient()
    context = VaultEpigraphContext(subject_id="s", source_set_id="set", mode="append",
                                   concepts=["SVD"], recent_epigraphs=["old line"])

    batch = VE.request_vault_epigraphs(client, context)

    assert batch == GOOD
    seen = client.calls[0]
    assert (seen.subject_id, seen.mode, seen.concepts, seen.recent_epigraphs) == ("s", "append", ["SVD"], ["old line"])


def test_generate_persists_three_rows_with_stamps(tmp_path):
    vault, repo = _setup(tmp_path)
    client = FakeClient()

    rows = _generate(repo, vault, client)

    assert len(rows) == 3
    stored = repo.recent_vault_epigraphs(subject_id="linear-algebra")
    assert [row["id"] for row in stored] == [row["id"] for row in rows]
    assert {row["kind"] for row in stored} == {"quote", "haiku"}
    haiku = next(row for row in stored if row["kind"] == "haiku")
    assert haiku["text"] == "A equals A T\nthe spectral theorem waits\neigenvectors align"
    first = stored[0]
    assert first["prompt_version"] == VAULT_EPIGRAPHS_PROMPT_VERSION
    assert first["provider"] == "fake"
    assert first["model"] == "fake-model"
    assert first["mode"] == "bootstrap"
    assert first["source_set_id"] == "set_la"
    assert first["synthesis_run_id"] == "run_1"
    assert first["created_at"].startswith("2026-09-03T12:00:00")
    context = client.calls[0]
    assert context.subject_title == "Linear Algebra"
    assert context.brief == {"depth": "intro"}  # non-scalar / unknown keys filtered
    assert context.claims == _digest().claims


def test_generate_drops_invalid_items_and_in_batch_duplicates(tmp_path):
    vault, repo = _setup(tmp_path)
    batch = VaultEpigraphBatch(
        epigraphs=[
            VaultEpigraph(kind="quote", lines=[" ".join(["word"] * 20)]),
            VaultEpigraph(kind="haiku", lines=["only two", "lines here"]),
            VaultEpigraph(kind="quote", lines=["", "   "]),
            VaultEpigraph(kind="quote", lines=["Rank is destiny — Albert Einstein"]),
            VaultEpigraph(kind="quote", lines=["- a bullet point"]),
            VaultEpigraph(kind="quote", lines=["see https://example.com"]),
            VaultEpigraph(kind="quote", lines=["“Escape will make me diagonal.”"]),
            VaultEpigraph(kind="quote", lines=["escape will make me diagonal"]),
        ]
    )

    rows = _generate(repo, vault, FakeClient(batch))

    assert [row["text"] for row in rows] == ["Escape will make me diagonal."]


def test_unknown_kind_is_rejected_by_the_normalizer():
    assert VE.normalize_epigraph({"kind": "limerick", "lines": ["a"]}) is None
    assert VE.normalize_epigraph({"kind": "haiku", "lines": ["a", "b", "c"]}) == ("haiku", ["a", "b", "c"])
    # An em dash inside a line is fine; only a capitalised attribution tail is not.
    assert VE.normalize_epigraph({"kind": "quote", "lines": ["Eigenvalues — the matrix's true voice"]}) is not None


def test_generate_dedupes_against_recent_rows(tmp_path):
    vault, repo = _setup(tmp_path)
    repo.insert_vault_epigraphs(
        subject_id="linear-algebra", source_set_id="set_la", synthesis_run_id="run_0", mode="bootstrap",
        epigraphs=[{"kind": "quote", "text": "SYMMETRY   is a promise the transpose keeps"}],
        prompt_version="v", provider=None, model=None, clock=_CLOCK,
    )
    client = FakeClient()

    rows = _generate(repo, vault, client, synthesis_run_id="run_1")

    assert len(rows) == 2
    assert all("promise" not in row["text"] for row in rows)
    assert client.calls[0].recent_epigraphs == ["SYMMETRY   is a promise the transpose keeps"]


@pytest.mark.parametrize(
    "client",
    [
        FakeClient(raise_with=RuntimeError("provider down")),
        StructuredClientFake(),  # no run_vault_epigraphs handler at all
        object(),  # supports() missing -> AIProviderUnavailable
        None,
    ],
    ids=["raises", "bare-fake", "unsupported", "none"],
)
def test_generate_never_raises(tmp_path, client):
    vault, repo = _setup(tmp_path)

    assert _generate(repo, vault, client) == []
    assert repo.recent_vault_epigraphs(subject_id="linear-algebra") == []


def test_generate_survives_a_repository_failure(tmp_path, monkeypatch):
    vault, repo = _setup(tmp_path)

    def boom(**_kwargs):
        raise sqlite3.OperationalError("disk full")

    monkeypatch.setattr(repo, "insert_vault_epigraphs", boom)
    assert _generate(repo, vault, FakeClient()) == []


def test_generate_drains_client_usage_even_when_the_call_fails(tmp_path):
    vault, repo = _setup(tmp_path)
    ok = FakeClient()
    bad = FakeClient(raise_with=RuntimeError("down"))

    _generate(repo, vault, ok)
    _generate(repo, vault, bad)

    assert ok.drained == 1
    assert bad.drained == 1


def test_digest_caps_dedupes_and_truncates():
    rows = [{"item_type": "concept", "payload": {"title": f"Concept {i}"}} for i in range(100)]
    rows += [{"item_type": "concept", "payload": {"title": "concept 0"}}]
    rows += [{"item_type": "facet", "payload": {"claim": "x" * 500}}]
    rows += [{"item_type": "learning_object", "payload": {"title": "  spaced   title  "}}]
    rows += [{"item_type": "practice_item", "payload": {"title": "ignored"}}]

    digest = VE.digest_from_proposal_rows(rows, summary="s" * 1000)

    assert len(digest.concepts) == VE.MAX_DIGEST_CONCEPTS
    assert digest.concepts[0] == "Concept 0"
    assert len(digest.claims[0]) == VE.MAX_DIGEST_ITEM_CHARS
    assert digest.learning_objects == ["spaced title"]
    assert len(digest.summary) == VE.MAX_SUMMARY_CHARS


def test_digest_for_append_uses_inventories_and_neighborhood():
    rows = [{"item_type": "provenance_link", "payload": {"target_entity_id": "facet_x"}}]
    inventories = [{"inventory": {
        "outline_summary": "symmetric matrices, again",
        "claims": [{"statement": "A real square matrix with A^T = A is called symmetric."}],
        "concept_mentions": [{"name": "symmetric matrix"}],
    }}]
    neighborhood = {
        "concepts": [{"id": "c1", "title": "Spectral theorem"}],
        "facets": [{"id": "f1", "claim": "The spectral theorem applies to real symmetric matrices."}],
        "learning_objects": [{"id": "lo1", "title": "Diagonalize a symmetric matrix"}],
    }

    digest = VE.digest_for_append(rows, inventories, neighborhood)

    assert digest.summary == "symmetric matrices, again"
    assert digest.concepts == ["symmetric matrix", "Spectral theorem"]
    assert len(digest.claims) == 2
    assert digest.learning_objects == ["Diagonalize a symmetric matrix"]


def test_recent_vault_epigraphs_filters_by_subject_and_limits(tmp_path):
    _vault, repo = _setup(tmp_path)
    for subject in ("linear-algebra", "other"):
        repo.insert_vault_epigraphs(
            subject_id=subject, source_set_id=None, synthesis_run_id=None, mode="append",
            epigraphs=[{"kind": "quote", "text": f"{subject} {i}"} for i in range(4)],
            prompt_version="v", provider=None, model=None, clock=_CLOCK,
        )

    assert len(repo.recent_vault_epigraphs()) == 8
    mine = repo.recent_vault_epigraphs(subject_id="linear-algebra", limit=2)
    assert [row["text"] for row in mine] == ["linear-algebra 3", "linear-algebra 2"]


def test_vault_epigraphs_rows_are_immutable(tmp_path):
    _vault, repo = _setup(tmp_path)
    (epigraph_id,) = repo.insert_vault_epigraphs(
        subject_id="linear-algebra", source_set_id=None, synthesis_run_id=None, mode="bootstrap",
        epigraphs=[{"kind": "quote", "text": "fixed"}], prompt_version="v", provider=None, model=None,
        clock=_CLOCK,
    )

    with connect(repo.sqlite_path) as connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute("UPDATE vault_epigraphs SET text = 'edited' WHERE id = ?", (epigraph_id,))
