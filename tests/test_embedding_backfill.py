from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.execution import model_call, report_call_usage
from learnloop.ai.spend import SpendCaps
from learnloop.cli import app
from learnloop.db.repositories import Repository
from learnloop.ops.embedding_backfill import _backfill_lock, backfill_embeddings, estimated_tokens
from learnloop.vault.embedding_recipes import EMBEDDING_RECIPES, embedding_records, select_recipes
from learnloop.vault.loader import load_vault
from learnloop.vault.models import EvidenceFacet
from tests.helpers import create_basic_vault
from tests.openai_fakes import install_fake_openai

# Phase 5b's practice-index recipes: one per dossier field, sorted by name.
DOSSIER_RECIPES = [f"facet/dossier_{field}" for field in ("contrast", "errors", "moves", "scope")]
# The default vault-content registry, in selection (name) order: Phase 1's
# facet/item recipes, Phase 5b's dossier fields, Slice 2 T5's concept
# definitions and instructional repairs, and Phase 5a's item/skeleton (persisted
# PF-b skeletons; none exist in these vaults). Consumer registries (T4) and
# database-backed kinds (Slice 1 M2) never join it.
DEFAULT_RECIPES = sorted([
    "facet/definition", "item/stem", *DOSSIER_RECIPES, "concept/definition", "facet_repair/text",
    "item/skeleton", "learning_object/statement",
])


class FakeEmbeddingClient:
    model_id = model = "qwen/qwen3-embedding-8b"
    dims = 3
    modalities = frozenset({"text"})
    max_input_tokens = 32_768
    provider_name = "fake"

    def __init__(self, *, fail_at=None, after_call=None, cost=None):
        self.calls = []
        self.fail_at = fail_at
        self.after_call = after_call
        self.cost = cost

    def embed(self, inputs, task_prefix):
        with model_call(self, purpose="embedding", prompt=inputs):
            self.calls.append((list(inputs), task_prefix))
            report_call_usage({"input_tokens": len(inputs), "output_tokens": 0, "cost": self.cost})
            if self.after_call:
                self.after_call()
            if self.fail_at == len(self.calls):
                raise AIProviderUnavailable("Do not echo PRIVATE request text")
            return [[1.0, 2.0, 3.0] for _ in inputs]


@pytest.fixture
def vault(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    loaded = load_vault(paths.root)
    loaded.config.embedding.enabled = True
    loaded.config.embedding.backfill_enabled = True
    loaded.config.embedding.dimensions = 3
    loaded.evidence_facets["definition"] = EvidenceFacet(
        id="definition", title="SVD", claim="A canonical factorization claim.",
    )
    # The counts below are about one facet and one item record; Slice 2 T5's
    # concept/definition recipe is covered in test_graph_nomination.py and the
    # learner-text gaps' learning_object/statement recipe in
    # test_learner_text_gaps.py.
    loaded.concepts.clear()
    for learning_object in loaded.learning_objects.values():
        learning_object.status = "dormant"
    return loaded, Repository(paths.sqlite_path)


def run(loaded, client, **kwargs):
    return backfill_embeddings(
        loaded, caps=kwargs.pop("caps", SpendCaps()),
        client_factory=lambda: client, **kwargs,
    )


def test_recipes_declare_canonical_text_and_hash_only_their_inputs(vault):
    loaded, _ = vault
    assert set(EMBEDDING_RECIPES) == set(DEFAULT_RECIPES)
    records = embedding_records(loaded)
    # Dossier-field recipes read persisted dossiers; none exist in this vault.
    assert {(r.record_kind, r.field) for r in records} == {("facet", "definition"), ("item", "stem")}
    assert all(EMBEDDING_RECIPES[f"{r.record_kind}/{r.field}"].text_recipe for r in records)
    item = next(iter(loaded.practice_items.values()))
    before = next(r for r in records if r.record_kind == "item")
    item.expected_answer = "SECRET ANSWER"
    item.hints.append("SECRET HINT")
    assert before == next(r for r in embedding_records(loaded) if r.record_kind == "item")
    item.prompt += " New canonical words."
    after = next(r for r in embedding_records(loaded) if r.record_kind == "item")
    assert before.content_hash != after.content_hash
    item.status = "retired"
    assert all(r.record_kind != "item" for r in embedding_records(loaded))
    with pytest.raises(ValueError, match="Unknown"):
        embedding_records(loaded, ("attempt",))


def test_recipes_are_selected_by_kind_or_by_kind_and_field():
    # Slice 2 R3 adds fields per kind (item/skeleton, facet/dossier_*); a bare
    # kind selects all of its fields, kind/field exactly one.
    assert [r.name for r in select_recipes()] == DEFAULT_RECIPES
    assert [r.name for r in select_recipes(["item"])] == ["item/skeleton", "item/stem"]
    assert [r.name for r in select_recipes(["facet/definition", "facet"])] == [
        "facet/definition", *DOSSIER_RECIPES,
    ]
    assert [r.name for r in select_recipes(["facet/definition"])] == ["facet/definition"]
    for selectors in (["item/outline"], ["facet/stem"], ["attempt"]):
        with pytest.raises(ValueError, match="Unknown embedding recipes"):
            select_recipes(selectors)
    with pytest.raises(ValueError, match="at least one"):
        select_recipes([])


@pytest.mark.durability
def test_backfill_is_batched_and_idempotent_with_receipts(vault):
    loaded, repository = vault
    client = FakeEmbeddingClient()
    first = run(loaded, client)
    second = run(loaded, client)
    assert first["status"] == second["status"] == "complete"
    assert first["embedded"] == 2
    assert second["embedded"] == 0
    assert second["cached"] == 2
    assert len(client.calls) == 1
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM embedding_vectors").fetchone()[0] == 2
        row = connection.execute(
            "SELECT purpose,status,input_tokens,budget_json FROM model_call_receipts WHERE owner_kind='embedding_backfill'"
        ).fetchone()
        assert tuple(row[:3]) == ("embedding", "completed", 2)
        budget = json.loads(row[3])
        manifest = budget.pop("embedding")
        assert budget == SpendCaps().as_dict()
        assert manifest["recipe_versions"] == {name: 1 for name in DEFAULT_RECIPES}
        assert manifest["prompt_version"] == "embedding-v1"
        assert connection.execute(
            "SELECT owner_id FROM model_call_receipts WHERE owner_kind='embedding_backfill'"
        ).fetchone()[0] == first["run_id"]
    assert "canonical factorization" not in json.dumps(first)


def test_changed_content_adds_vector_without_removing_old_revision(vault):
    loaded, repository = vault
    client = FakeEmbeddingClient()
    run(loaded, client)
    next(iter(loaded.practice_items.values())).prompt += " Revised."
    report = run(loaded, client)
    assert report["embedded"] == 1
    assert len(client.calls) == 2
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM embedding_vectors").fetchone()[0] == 3


def test_dry_run_does_not_construct_client_or_change_database(vault):
    loaded, repository = vault
    before = repository.sqlite_path.read_bytes()
    report = backfill_embeddings(
        loaded, caps=SpendCaps(), dry_run=True,
        client_factory=lambda: pytest.fail("constructed client during dry run"),
    )
    assert report["status"] == "dry_run"
    assert report["estimate"]["calls"] == 1
    assert report["estimate"]["total_tokens"] > 0
    assert report["estimate"]["estimated_usd"] > 0
    assert repository.sqlite_path.read_bytes() == before
    assert not (loaded.root / ".learnloop" / "embedding-backfill.lock").exists()


@pytest.mark.parametrize("switch", ["enabled", "backfill_enabled"])
def test_switches_disable_all_paid_work(vault, switch):
    loaded, _ = vault
    setattr(loaded.config.embedding, switch, False)
    client = FakeEmbeddingClient()
    assert run(loaded, client)["status"] == "disabled"
    assert client.calls == []


@pytest.mark.parametrize("caps", [
    SpendCaps(max_candidates=1), SpendCaps(max_calls=0),
    SpendCaps(max_total_tokens=1), SpendCaps(max_estimated_usd=0),
])
def test_caps_refuse_before_client_construction(vault, caps):
    loaded, _ = vault
    report = backfill_embeddings(
        loaded, caps=caps, client_factory=lambda: pytest.fail("constructed over-budget client"),
    )
    assert report["status"] == "over_budget"


def test_unknown_price_fails_closed_but_finite_owner_estimate_allows_it(vault):
    loaded, _ = vault
    loaded.config.embedding.model = "unknown/model"
    client = FakeEmbeddingClient()
    client.model_id = client.model = "unknown/model"
    assert run(loaded, client)["status"] == "over_budget"
    assert not client.calls
    assert run(loaded, client, price_per_million=0.1)["status"] == "complete"
    assert len(client.calls) == 1


@pytest.mark.parametrize("price", [0, -1, float("inf"), float("nan"), True])
def test_invalid_price_override_cannot_authorize_paid_work(vault, price):
    loaded, _ = vault
    client = FakeEmbeddingClient()
    with pytest.raises(ValueError, match="finite and positive"):
        run(loaded, client, price_per_million=price)
    assert not client.calls


@pytest.mark.durability
def test_cancel_after_paid_batch_saves_it_and_resume_skips_it(vault):
    loaded, _ = vault
    cancelled = False

    def stop():
        nonlocal cancelled
        cancelled = True

    client = FakeEmbeddingClient(after_call=stop)
    report = run(loaded, client, batch_size=1, cancelled=lambda: cancelled)
    assert report["status"] == "cancelled"
    assert report["embedded"] == report["remaining"] == 1
    resumed = run(loaded, client, batch_size=1)
    assert resumed["status"] == "complete"
    assert resumed["embedded"] == resumed["cached"] == 1
    assert len(client.calls) == 2


def test_failed_batch_keeps_successful_checkpoint_and_redacts_report(vault):
    loaded, _ = vault
    client = FakeEmbeddingClient(fail_at=2)
    report = run(loaded, client, batch_size=1, caps=SpendCaps(max_retries=0))
    assert report["status"] == "provider_failed"
    assert report["embedded"] == 1
    assert report["charged"]["calls"] == 2
    assert "PRIVATE" not in json.dumps(report)
    assert run(loaded, client)["embedded"] == 1


def test_retry_is_charged_and_keeps_candidates_unique(vault):
    loaded, repository = vault
    client = FakeEmbeddingClient(fail_at=1)
    report = run(loaded, client, caps=SpendCaps(max_retries=1))
    assert report["status"] == "complete"
    assert report["charged"]["calls"] == 2
    assert report["charged"]["retries"] == 1
    assert report["charged"]["candidates"] == 2
    with repository.connection() as connection:
        assert [r[0] for r in connection.execute(
            "SELECT status FROM model_call_receipts ORDER BY started_at,id"
        )] == ["failed", "completed"]


def test_retry_is_admitted_against_remaining_call_cap(vault):
    loaded, _ = vault
    client = FakeEmbeddingClient(fail_at=1)
    report = run(loaded, client, caps=SpendCaps(max_calls=1))
    assert report["status"] == "over_budget"
    assert len(client.calls) == 1


def test_real_embedding_transport_retry_is_bounded_and_receipted(vault, monkeypatch):
    loaded, repository = vault
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    reply = SimpleNamespace(
        data=[SimpleNamespace(index=i, embedding=[1, 2, 3]) for i in range(2)],
        usage=SimpleNamespace(prompt_tokens=5, total_tokens=5),
    )
    module = install_fake_openai(
        monkeypatch, embeddings=[RuntimeError("PRIVATE upstream failure"), reply],
    )
    report = backfill_embeddings(loaded, caps=SpendCaps(max_retries=1))
    assert report["status"] == "complete"
    assert report["embedded"] == 2
    assert report["charged"]["calls"] == 2
    assert len(module.instances) == 1
    assert module.instances[0].kwargs["max_retries"] == 0
    assert len(module.instances[0].embedding_requests) == 2
    with repository.connection() as connection:
        receipts = connection.execute(
            "SELECT status,budget_json FROM model_call_receipts ORDER BY started_at,id"
        ).fetchall()
    assert [r[0] for r in receipts] == ["failed", "completed"]
    assert all(json.loads(r[1])["max_retries"] == 1 for r in receipts)


def test_reported_overrun_stops_next_batch_without_losing_paid_result(vault):
    loaded, _ = vault
    client = FakeEmbeddingClient(cost=2.0)
    report = run(loaded, client, batch_size=1)
    assert report["status"] == "over_budget"
    assert report["embedded"] == 1
    assert len(client.calls) == 1
    assert report["charged"]["estimated_usd"] == 2.0


def test_dimension_change_refused_before_paid_call(vault):
    loaded, _ = vault
    client = FakeEmbeddingClient()
    run(loaded, client)
    loaded.config.embedding.dimensions = 2
    with pytest.raises(ValueError, match="different dimensions"):
        run(loaded, client)
    assert len(client.calls) == 1


def test_oversized_text_is_not_silently_truncated(vault):
    loaded, _ = vault
    client = FakeEmbeddingClient()
    client.max_input_tokens = 1
    with pytest.raises(ValueError, match="input limit"):
        run(loaded, client)
    assert not client.calls
    assert estimated_tokens("数") > len("数")


def test_concurrent_backfill_refused(vault):
    loaded, _ = vault
    client = FakeEmbeddingClient()
    with _backfill_lock(loaded.root):
        with pytest.raises(ValueError, match="Another embedding"):
            run(loaded, client)
    assert not client.calls


def test_already_cancelled_never_constructs_client(vault):
    loaded, _ = vault
    report = backfill_embeddings(
        loaded, caps=SpendCaps(), cancelled=lambda: True,
        client_factory=lambda: pytest.fail("cancelled run constructed client"),
    )
    assert report["status"] == "cancelled"


def test_cli_dry_run_on_disabled_vault_needs_no_provider(tmp_path, monkeypatch):
    paths = create_basic_vault(tmp_path / "vault")
    monkeypatch.setattr(
        "learnloop.ops.embedding_backfill.ready_client_for_task",
        lambda *a, **kw: pytest.fail("dry-run resolved provider"),
    )
    before = paths.sqlite_path.read_bytes()
    result = CliRunner().invoke(app, [
        "embeddings", "backfill", "--vault", str(paths.root), "--dry-run", "--json",
    ])
    assert result.exit_code == 0, result.output
    report = json.loads(result.stdout)
    assert report["status"] == "dry_run"
    assert not report["embedding_enabled"]
    assert not report["backfill_enabled"]
    assert report["recipes"] == DEFAULT_RECIPES
    assert paths.sqlite_path.read_bytes() == before
    narrowed = CliRunner().invoke(app, [
        "embeddings", "backfill", "--vault", str(paths.root), "--dry-run", "--json",
        "--record-kind", "item/stem",
    ])
    assert narrowed.exit_code == 0, narrowed.output
    assert json.loads(narrowed.stdout)["recipes"] == ["item/stem"]
    assert json.loads(narrowed.stdout)["manifest"]["recipe_versions"] == {"item/stem": 1}


def test_cli_requires_explicit_vault():
    result = CliRunner().invoke(app, ["embeddings", "backfill", "--dry-run"])
    assert result.exit_code == 2


def test_cli_registration_does_not_load_the_vector_store():
    # numpy-backed storage is imported only when the backfill command runs.
    import subprocess
    import sys

    code = (
        "import sys, learnloop.cli; "
        "assert 'learnloop.db.stores.embedding_vectors' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


@pytest.mark.parametrize("reply", [
    SimpleNamespace(usage=SimpleNamespace(prompt_tokens=5, total_tokens=5)),  # no data
    SimpleNamespace(data=[SimpleNamespace(index=0, embedding=[1, 2, 3])],
                    usage=SimpleNamespace(prompt_tokens=5, total_tokens=5)),  # one vector for two inputs
    SimpleNamespace(data=[SimpleNamespace(index=i, embedding=[1, 2]) for i in range(2)],
                    usage=SimpleNamespace(prompt_tokens=5, total_tokens=5)),  # too narrow
])
def test_invalid_paid_response_keeps_the_report_and_is_not_retried(vault, monkeypatch, reply):
    loaded, repository = vault
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    module = install_fake_openai(monkeypatch, embeddings=[reply, reply, reply])
    report = backfill_embeddings(loaded, caps=SpendCaps(max_retries=2))
    assert report["status"] == "provider_failed"
    assert report["error_type"] == "ValueError"
    assert report["run_id"]
    assert report["embedded"] == 0 and report["remaining"] == 2
    assert report["charged"]["calls"] == 1
    assert report["charged"]["total_tokens"] >= 5
    assert len(module.instances[0].embedding_requests) == 1
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM embedding_vectors").fetchone()[0] == 0
        assert [tuple(row) for row in connection.execute(
            "SELECT status, input_tokens FROM model_call_receipts WHERE owner_id=?", (report["run_id"],)
        )] == [("failed", 5)]


def test_provider_failure_reports_sdk_class_without_its_message(vault, monkeypatch):
    loaded, _ = vault
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")

    class AuthenticationError(Exception):
        pass

    install_fake_openai(monkeypatch, embeddings=[AuthenticationError("PRIVATE sk-or-v1-secret")])
    report = backfill_embeddings(loaded, caps=SpendCaps(max_retries=0))
    assert report["status"] == "provider_failed"
    assert report["provider_error"] == "AuthenticationError"
    assert "PRIVATE" not in json.dumps(report) and "sk-or" not in json.dumps(report)


def test_unknown_price_reason_names_the_remedy(vault):
    loaded, _ = vault
    loaded.config.embedding.model = "unknown/model"
    report = backfill_embeddings(loaded, caps=SpendCaps(), dry_run=True)
    assert report["status"] == "over_budget"
    assert "--price-per-million" in report["reason"] and "unknown/model" in report["reason"]


def test_content_reuse_covers_explicit_extra_and_registry_records(vault):
    """Slice 2 T5's content-addressed reuse, composed at its merge with T8's
    explicit records, Slice 1 M2's database-backed extra records and T4's
    consumer registry: a vector paid under one record id serves the identical
    input under another, whichever way the record reached the backfill."""

    from learnloop.db.stores.embedding_vectors import get_vector, put_vector
    from learnloop.diagnosis.split.embeddings import misconception_record
    from learnloop.ops.embedding_backfill import TASK_PREFIX
    from learnloop.vault.embedding_recipes import EmbeddingRecipe

    loaded, repository = vault
    client = FakeEmbeddingClient()
    stem = EMBEDDING_RECIPES["item/stem"]
    shared = "A stem an earlier graded attempt showed."
    consumer = EmbeddingRecipe(
        "probe", "text", 1, "Test-only consumer recipe.", lambda _loaded: iter([("probe_new", shared)]),
    )
    paid = [
        stem.record("item_paid", shared),
        consumer.record("probe_paid", shared),
        misconception_record("durable:paid", "Believes det(A+B) = det A + det B"),
    ]
    with repository.connection() as connection:
        for record in paid:
            put_vector(connection, record_kind=record.record_kind, record_id=record.record_id,
                       field=record.field, content_hash=record.content_hash,
                       model_id=client.model_id, task_prefix=TASK_PREFIX, vector=[0.5, 0.25, 1.0])
    new = [
        stem.record("item_seen", shared),
        consumer.record("probe_new", shared),
        misconception_record("candidate:new", "Believes det(A+B) = det A + det B"),
    ]
    reports = [
        run(loaded, client, recipes=("item/stem",), records=[new[0]]),
        run(loaded, client, registry={"probe/text": consumer}),
        run(loaded, client, recipes=(), extra_records=[new[2]], extra_recipes=["misconception/statement"]),
    ]
    assert reports[0]["records_source"] == "explicit"
    for report in reports:
        assert report["status"] == "complete", report
        assert (report["reused_by_content"], report["embedded"]) == (1, 0)
    assert client.calls == []
    with repository.connection() as connection:
        for record in new:
            assert get_vector(connection, record_kind=record.record_kind, record_id=record.record_id,
                              field=record.field, content_hash=record.content_hash,
                              model_id=client.model_id, task_prefix=TASK_PREFIX) is not None
