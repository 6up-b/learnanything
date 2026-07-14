from __future__ import annotations

import io
import json

from learnloop.db.repositories import Repository
from learnloop.services.provenance import get_entity_provenance
from learnloop_sidecar.server import serve

from tests.helpers import create_basic_vault


def _rpc(messages: list[dict]) -> list[dict]:
    stdin = io.StringIO("".join(json.dumps(message) + "\n" for message in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def _seed_links(repository: Repository) -> None:
    repository.insert_entity_source_link(
        entity_type="facet",
        entity_id="facet_det",
        locator="block_span:p12",
        relation="primary",
        source_id="src_axler",
        revision_id="rev_1",
        locator_scheme="block_span_v1",
        span_hash="sha256:aa",
    )
    repository.insert_entity_source_link(
        entity_type="facet",
        entity_id="facet_det",
        locator="t=00:03:10-00:03:40",
        relation="assessment_alignment",
        source_id="src_exam_2021",
        revision_id="rev_exam",
    )


def test_get_entity_provenance_separates_semantic_and_assessment(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    _seed_links(repository)

    view = get_entity_provenance(repository, "facet", "facet_det")

    assert view["has_provenance"]
    assert len(view["semantic_sources"]) == 1
    assert len(view["assessment_alignment_sources"]) == 1
    assert view["semantic_authority"]["relation"] == "primary"
    assert view["semantic_authority"]["source_id"] == "src_axler"
    # Assessment alignment is NOT semantic authority.
    assert view["assessment_alignment_sources"][0]["relation"] == "assessment_alignment"


def test_get_entity_provenance_reports_staleness(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    repository.insert_entity_source_link(
        entity_type="learning_object",
        entity_id="lo_x",
        locator="block_span:p1",
        relation="support",
        revision_id="rev_old",
        status="needs_reanchor",
    )
    view = get_entity_provenance(repository, "learning_object", "lo_x")
    assert len(view["stale_links"]) == 1
    assert view["semantic_authority"] is None  # no current semantic authority


def test_get_entity_provenance_includes_conflicts_and_notation(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    repository.insert_source_conflict(
        entity_type="facet",
        entity_id="facet_det",
        statement="Sources disagree on the sign convention.",
        left_source_id="src_a",
        right_source_id="src_b",
    )
    repository.insert_notation_mapping(
        entity_type="facet",
        entity_id="facet_det",
        canonical_notation="det(A)",
        alternate_notation="|A|",
        context="determinant",
    )
    view = get_entity_provenance(repository, "facet", "facet_det")
    assert len(view["conflicts"]) == 1
    assert view["conflicts"][0]["status"] == "open"
    assert len(view["notation_mappings"]) == 1
    assert view["notation_mappings"][0]["canonical_notation"] == "det(A)"


def test_empty_entity_has_no_provenance(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    view = get_entity_provenance(repository, "facet", "unknown")
    assert view["has_provenance"] is False
    assert view["semantic_sources"] == []


def test_sidecar_get_entity_provenance(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    _seed_links(repository)

    responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "get_entity_provenance",
                "params": {"entityType": "facet", "entityId": "facet_det"},
            },
        ]
    )
    result = responses[1]["result"]
    # versioned() camelCases keys.
    assert len(result["semanticSources"]) == 1
    assert len(result["assessmentAlignmentSources"]) == 1
    assert result["semanticAuthority"]["relation"] == "primary"
