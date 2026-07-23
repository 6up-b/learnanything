from __future__ import annotations

from learnloop.codex.schemas import AuthoringProposal
from learnloop.db.repositories import Repository
from learnloop.services.practice_generation import (
    build_practice_expansion_plan,
    generate_post_probe_practice_proposal,
)
from learnloop.services.reader_progression import source_refs_for_section
from learnloop.vault.loader import load_vault
from learnloop.vault.models import SourceRef
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml
from learnloop_sidecar.ingest_jobs import DurableIngestJobs

from tests.helpers import create_basic_vault
from tests.test_reader_guidance import _setup


def test_reader_source_refs_preserve_bounded_span_context(tmp_path):
    vault, repository = _setup(tmp_path)
    learning_object = vault.learning_objects["lo_svd_definition"]
    learning_object.provenance.source_refs = [
        SourceRef(
            ref_type="canonical_source",
            ref_id="src1",
            locator="span:ext1/s1",
            source_id="src1",
            extraction_id="ext1",
        )
    ]
    raw_path = VaultPaths(vault.root, vault.config).canonical_source_raw_path("sha256:abc")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(b"source bytes")

    refs = source_refs_for_section(
        vault,
        repository,
        extraction_id="ext1",
        section_id="u1",
        learning_object_ids=["lo_svd_definition"],
    )

    assert len(refs) == 1
    ref = refs[0]
    assert ref["ref_id"] == "reader_citation:ext1:lo_svd_definition:s0-s2"
    assert ref["source_id"] == "src1"
    assert ref["revision_id"] == "rev1"
    assert ref["extraction_id"] == "ext1"
    assert ref["span_ids"] == ["s0", "s1", "s2"]
    assert ref["learning_object_ids"] == ["lo_svd_definition"]
    assert "orthonormal" in ref["quote"]
    assert ref["path"] == "canonical-sources/raw/sha256-abc"


def test_practice_plan_uses_blueprint_facets_before_first_item(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    lo_path = paths.learning_object_path("linear-algebra", "lo_svd_definition")
    payload = read_yaml(lo_path)
    payload["blueprints"] = [
        {
            "id": "bp_svd",
            "recipes": [
                {
                    "id": "recipe_svd",
                    "all_of": [
                        {
                            "facet": "facet_svd_structure",
                            "capability": "schema_interpretation",
                        }
                    ],
                }
            ],
        }
    ]
    write_yaml(lo_path, payload)
    paths.practice_item_path("linear-algebra", "pi_svd_define_001").unlink()
    vault = load_vault(paths.root)

    plan = build_practice_expansion_plan(
        vault,
        Repository(paths.sqlite_path),
        learning_object_ids=["lo_svd_definition"],
        require_completed_probe=False,
        target_items_per_lo=3,
    )

    assert plan.targets[0].existing_practice_items == 0
    assert plan.targets[0].existing_evidence_facets == ["facet_svd_structure"]


class _CaptureClient:
    model = "fake"
    provider_type = "fake"

    def __init__(self) -> None:
        self.context = None

    def run_authoring_proposal(self, context):
        self.context = context
        return AuthoringProposal(summary="No items needed from this fake.")


def test_post_probe_generation_passes_and_persists_reader_source_refs(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    raw_path = paths.canonical_source_raw_path("sha256:reader")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(b"reader source")
    source_ref = {
        "ref_type": "canonical_source",
        "ref_id": "reader_citation:ext1:lo_svd_definition:s1-s2",
        "path": "canonical-sources/raw/sha256-reader",
        "locator": "span:ext1/s1",
        "quote": "SVD source context",
        "source_id": "src1",
        "revision_id": "rev1",
        "extraction_id": "ext1",
        "span_ids": ["s1", "s2"],
        "section_id": "u1",
        "learning_object_ids": ["lo_svd_definition"],
    }
    client = _CaptureClient()

    result = generate_post_probe_practice_proposal(
        paths.root,
        client,
        learning_object_ids=["lo_svd_definition"],
        require_completed_probe=False,
        source_refs=[source_ref],
    )

    assert client.context.source_refs == [source_ref]
    persisted = Repository(paths.sqlite_path).proposal_batch(result.patch_id)
    assert persisted["source_refs"][0]["ref_id"] == source_ref["ref_id"]
    assert persisted["source_refs"][0]["span_ids"] == ["s1", "s2"]


def test_practice_expansion_queue_preserves_reader_source_refs(tmp_path):
    repository = Repository(tmp_path / "state.sqlite")
    jobs = DurableIngestJobs()
    jobs.bind(repository, tmp_path, background=False)
    source_ref = {
        "ref_type": "canonical_source",
        "ref_id": "reader_citation:ext1:lo_svd_definition:s1-s2",
        "source_id": "src1",
        "revision_id": "rev1",
        "extraction_id": "ext1",
        "span_ids": ["s1", "s2"],
        "learning_object_ids": ["lo_svd_definition"],
    }

    batch_id = jobs.enqueue_practice_expansion(
        learning_object_ids=["lo_svd_definition"],
        source_refs=[source_ref],
    )

    queued = repository.ingest_jobs_for_batch(batch_id)
    assert len(queued) == 1
    assert queued[0]["payload"]["source_refs"] == [source_ref]
