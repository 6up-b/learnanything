from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.codex.client import CanonicalIngestContext
from learnloop.codex.schemas import AuthoringProposal
from learnloop.db.repositories import Repository
from learnloop.services.proposals import accept_items, persist_authoring_proposal, reject_items
from learnloop.services.source_ingestion import ingest_canonical_source
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault


def test_ingest_local_html_registers_source_and_auto_applies(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    html = _source_file(tmp_path)
    client = _FakeCanonicalClient()

    result = ingest_canonical_source(
        vault_root,
        str(html),
        client,
        subject_id="linear-algebra",
        clock=FrozenClock(NOW),
    )

    assert result.patch_id
    assert result.source_kind == "website_page"
    assert result.auto_applied_count == 2
    assert result.review_required_count == 0
    assert result.invalid_count == 0
    assert len(client.calls) == 1
    context = client.calls[0]
    assert context.source_kind == "website_page"
    assert context.canonical_source["id"] == result.source_note_id
    assert context.chunks[0].locator.endswith("/p1")

    loaded = load_vault(vault_root)
    note = loaded.notes[result.source_note_id]
    assert note.source_type == "canonical_source"
    assert note.model_extra["canonical_source"]["content_hash"] == result.content_hash
    assert "lo_ingested_svd" in loaded.learning_objects
    assert "pi_ingested_svd_001" in loaded.practice_items
    assert loaded.learning_objects["lo_ingested_svd"].provenance.origin == "canonical_extract"
    assert list((vault_root / "canonical-sources" / "raw").glob("*.bin"))

    repository = Repository(vault_root / "state.sqlite")
    batch = repository.proposal_batch_for_agent_run(result.agent_run_id)
    assert batch["purpose"] == "canonical_ingest"
    assert repository.find_record(result.agent_run_id)[1]["status"] == "completed"


def test_ingest_same_canonical_source_is_noop_after_completed_run(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    html = _source_file(tmp_path)
    client = _FakeCanonicalClient()

    first = ingest_canonical_source(
        vault_root,
        str(html),
        client,
        subject_id="linear-algebra",
        clock=FrozenClock(NOW),
    )
    second = ingest_canonical_source(
        vault_root,
        str(html),
        client,
        subject_id="linear-algebra",
        clock=FrozenClock(NOW),
    )

    assert second.reused_existing is True
    assert second.patch_id == first.patch_id
    assert len(client.calls) == 1
    loaded = load_vault(vault_root)
    canonical_notes = [note for note in loaded.notes.values() if note.source_type == "canonical_source"]
    assert len(canonical_notes) == 1


def test_ingest_invalid_returned_locator_blocks_auto_apply(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    html = _source_file(tmp_path)
    client = _FakeCanonicalClient(locator="missing/p99")

    result = ingest_canonical_source(
        vault_root,
        str(html),
        client,
        subject_id="linear-algebra",
        clock=FrozenClock(NOW),
    )

    assert result.auto_applied_count == 0
    assert result.invalid_count == 2
    loaded = load_vault(vault_root)
    assert "lo_ingested_svd" not in loaded.learning_objects

    repository = Repository(vault_root / "state.sqlite")
    items = repository.proposal_items(result.patch_id)
    assert {item["validation_status"] for item in items} == {"invalid"}
    assert all(item["validation_errors"][0].startswith("unresolved_source_ref:") for item in items)


def test_ingest_retries_with_stronger_ai_provider_on_validation_failure(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    html = _source_file(tmp_path)
    first_client = _FakeCanonicalClient(locator="missing/p99", provider_name="deepseek_flash", model="deepseek-v4-flash")
    retry_client = _FakeCanonicalClient(provider_name="deepseek_pro", model="deepseek-v4-pro")

    result = ingest_canonical_source(
        vault_root,
        str(html),
        first_client,
        subject_id="linear-algebra",
        model="deepseek-v4-flash",
        retry_client=retry_client,
        retry_model="deepseek-v4-pro",
        clock=FrozenClock(NOW),
    )

    repository = Repository(vault_root / "state.sqlite")
    with repository.connection() as connection:
        all_runs = connection.execute("SELECT * FROM agent_runs ORDER BY started_at, id").fetchall()
    runs_by_provider = {row["provider"]: row for row in all_runs}

    assert len(first_client.calls) == 1
    assert len(retry_client.calls) == 1
    assert result.invalid_count == 0
    assert result.auto_applied_count == 2
    assert result.agent_run_id == runs_by_provider["deepseek_pro"]["id"]
    assert runs_by_provider["deepseek_flash"]["model"] == "deepseek-v4-flash"
    assert runs_by_provider["deepseek_flash"]["status"] == "failed"
    assert "validation_failed" in runs_by_provider["deepseek_flash"]["error_message"]
    assert runs_by_provider["deepseek_pro"]["provider_type"] == "openai_chat"
    assert runs_by_provider["deepseek_pro"]["model"] == "deepseek-v4-pro"
    assert runs_by_provider["deepseek_pro"]["status"] == "completed"


def test_reingest_changed_source_records_stale_source_events(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    html = _source_file(tmp_path)
    client = _FakeCanonicalClient()
    first = ingest_canonical_source(
        vault_root,
        str(html),
        client,
        subject_id="linear-algebra",
        clock=FrozenClock(NOW),
    )
    html.write_text(
        html.read_text(encoding="utf-8").replace(
            "It supports low rank approximation",
            "It now emphasizes spectral geometry",
        ),
        encoding="utf-8",
    )

    second = ingest_canonical_source(
        vault_root,
        str(html),
        client,
        subject_id="linear-algebra",
        clock=FrozenClock(NOW),
    )

    assert second.reused_existing is False
    assert second.content_hash != first.content_hash
    assert second.source_event_count == 2
    repository = Repository(vault_root / "state.sqlite")
    lo_events = repository.content_events_for_entity("learning_object", "lo_ingested_svd")
    pi_events = repository.content_events_for_entity("practice_item", "pi_ingested_svd_001")
    assert any(event["event_type"] == "source_span_changed" for event in lo_events)
    assert any(event["event_type"] == "source_span_changed" for event in pi_events)
    batch = repository.proposal_batch_for_agent_run(second.agent_run_id)
    assert "Source diff:" in batch["summary"]


def test_regrounded_update_clears_active_source_span_events(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    html = _source_file(tmp_path)
    client = _FakeCanonicalClient()
    ingest_canonical_source(
        vault_root,
        str(html),
        client,
        subject_id="linear-algebra",
        clock=FrozenClock(NOW),
    )
    html.write_text(
        html.read_text(encoding="utf-8").replace(
            "It supports low rank approximation",
            "It now emphasizes spectral geometry",
        ),
        encoding="utf-8",
    )
    second = ingest_canonical_source(
        vault_root,
        str(html),
        client,
        subject_id="linear-algebra",
        clock=FrozenClock(NOW),
    )
    repository = Repository(vault_root / "state.sqlite")
    assert repository.active_source_events_for_entity("learning_object", "lo_ingested_svd")

    note = load_vault(vault_root).notes[second.source_note_id]
    proposal = AuthoringProposal.model_validate(
        {
            "summary": "Refresh LO grounding after source change.",
            "source_refs": [
                {
                    "ref_type": "canonical_source",
                    "ref_id": note.id,
                    "path": note.path,
                    "locator": "html/body/p1",
                }
            ],
            "items": [
                {
                    "client_item_id": "lo_reground",
                    "item_type": "learning_object",
                    "operation": "update",
                    "target": {"entity_type": "learning_object", "entity_id": "lo_ingested_svd"},
                    "source_ref_ids": [note.id],
                    "rationale": "Re-ground the Learning Object against the changed source span.",
                    "review_route": "review_required",
                    "payload": {
                        "summary": "SVD factors a matrix and now links to the refreshed canonical source span.",
                    },
                }
            ],
        }
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    item_id = repository.proposal_items(patch_id)[0]["id"]
    accept_items(vault_root, patch_id, [item_id])

    assert repository.content_events_for_entity("learning_object", "lo_ingested_svd")
    assert repository.active_source_events_for_entity("learning_object", "lo_ingested_svd") == []


def test_reject_auto_applied_ingest_items_deactivates_created_entities(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    html = _source_file(tmp_path)
    result = ingest_canonical_source(
        vault_root,
        str(html),
        _FakeCanonicalClient(),
        subject_id="linear-algebra",
        clock=FrozenClock(NOW),
    )
    repository = Repository(vault_root / "state.sqlite")
    assert repository.practice_item_state("pi_ingested_svd_001").active is True

    count = reject_items(vault_root, result.patch_id)

    assert count == 2
    loaded = load_vault(vault_root)
    assert loaded.learning_objects["lo_ingested_svd"].status == "dormant"
    assert repository.practice_item_state("pi_ingested_svd_001").active is False
    decisions = {item["client_item_id"]: item["decision"] for item in repository.proposal_items(result.patch_id)}
    assert decisions == {"lo_ingested_svd": "rejected", "pi_ingested_svd": "rejected"}
    assert any(
        event["event_type"] == "deactivated" and event["review_status"] == "rejected"
        for event in repository.content_events_for_entity("practice_item", "pi_ingested_svd_001")
    )


class _FakeCanonicalClient:
    def __init__(
        self,
        locator: str | None = None,
        *,
        provider_name: str = "codex",
        model: str | None = None,
    ):
        self.locator = locator
        self.provider_name = provider_name
        self.provider_type = "codex_sdk" if provider_name == "codex" else "openai_chat"
        self.model = model
        self.calls: list[CanonicalIngestContext] = []

    def run_canonical_ingest(self, context: CanonicalIngestContext) -> AuthoringProposal:
        self.calls.append(context)
        locator = self.locator or context.chunks[0].locator
        return AuthoringProposal.model_validate(_proposal_payload(context, locator))

    def run_authoring_proposal(self, context):  # pragma: no cover - unused in these tests
        raise NotImplementedError

    def run_grading_proposal(self, context):  # pragma: no cover - unused in these tests
        raise NotImplementedError


def _source_file(tmp_path):
    text = " ".join(
        [
            "Singular value decomposition factors a matrix into orthogonal matrices and singular values.",
            "It supports low rank approximation, least squares reasoning, and geometric interpretation.",
            "A useful learner should know the definition, identify the factors, and connect singular values to scale.",
        ]
        * 5
    )
    html = tmp_path / "svd.html"
    html.write_text(
        f"""
        <html>
          <head>
            <title>SVD canonical source</title>
            <link rel="canonical" href="https://example.edu/svd" />
          </head>
          <body>
            <h1>Singular Value Decomposition</h1>
            <p>{text}</p>
          </body>
        </html>
        """,
        encoding="utf-8",
    )
    return html


def _proposal_payload(context: CanonicalIngestContext, locator: str) -> dict:
    source_ref_id = context.canonical_source["id"]
    return {
        "summary": "Ingested SVD source.",
        "source_refs": [
            {
                "ref_type": "canonical_source",
                "ref_id": source_ref_id,
                "path": context.canonical_source["path"],
                "locator": locator,
            }
        ],
        "items": [
            {
                "client_item_id": "lo_ingested_svd",
                "item_type": "learning_object",
                "operation": "create",
                "proposed_entity_id": "lo_ingested_svd",
                "source_ref_ids": [source_ref_id],
                "rationale": "Extract the canonical definition.",
                "review_route": "auto_apply",
                "payload": {
                    "title": "Ingested SVD definition",
                    "subjects": [context.target_subject],
                    "concept_id": "singular_value_decomposition",
                    "knowledge_type": "definition",
                    "summary": "SVD factors a matrix into orthogonal matrices and singular values.",
                },
            },
            {
                "client_item_id": "pi_ingested_svd",
                "item_type": "practice_item",
                "operation": "create",
                "proposed_entity_id": "pi_ingested_svd_001",
                "source_ref_ids": [source_ref_id],
                "rationale": "Practice the extracted definition.",
                "review_route": "auto_apply",
                "payload": {
                    "learning_object_id": "lo_ingested_svd",
                    "subjects": None,
                    "practice_mode": "short_answer",
                    "attempt_types_allowed": ["independent_attempt"],
                    "prompt": "What does SVD factorize a matrix into?",
                    "expected_answer": "Orthogonal matrices and singular values.",
                    "evidence_facets": ["recall"],
                    "evidence_weights": {"recall": 1.0},
                    "grading_rubric": {
                        "max_points": 4,
                        "criteria": [{"id": "correctness", "points": 4, "description": "Names the factors."}],
                        "fatal_errors": [],
                    },
                },
            },
        ],
    }
