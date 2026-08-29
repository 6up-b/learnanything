"""Deleting an imported source (spec_source_ingestion_v2 §4.1).

Deletion is the one operation that has to reason about the whole source graph at
once, so these cover the three policies in
``Repository.delete_source_artifact`` — cascade derived rows, detach learner-owned
records, leave append-only history — plus the vault-side cleanup and the refusal
that keeps a running worker from writing into a half-deleted source.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ingest.hashing import extraction_request_hash, extraction_result_hash
from learnloop.ingest.ir import (
    IR_SCHEMA_VERSION,
    DocumentBlock,
    DocumentIR,
    DocumentUnit,
    ExtractionHealth,
)
from learnloop.content.sources.source_deletion import (
    SourceDeletionError,
    delete_source,
    plan_source_deletion,
)
from learnloop.vault.loader import add_subject, init_vault, load_vault
from learnloop.vault.paths import canonical_source_raw_path
from learnloop.vault.writer import upsert_source_set

_CLOCK = FrozenClock(datetime(2026, 7, 26, 12, 0, 0, tzinfo=UTC))


def _ir(unit_id: str, text: str) -> DocumentIR:
    block = DocumentBlock.build(
        span_id=f"{unit_id}_s1",
        block_type="Text",
        text=text,
        role_hint="ordinary_prose",
        page=1,
        section_path=("root",),
        ordinal=0,
    )
    return DocumentIR(
        extractor="text",
        extractor_version="1",
        units=[
            DocumentUnit(
                unit_id=unit_id,
                label=unit_id,
                ordinal=0,
                semantic_hash=f"sha256:{unit_id}",
                page_start=1,
                page_end=1,
                span_ids=[block.span_id],
            )
        ],
        blocks=[block],
        assets=[],
        health=ExtractionHealth(),
    )


def _seed_source(
    repo: Repository,
    *,
    source_id: str,
    revision_id: str,
    extraction_id: str,
    asset_hash: str = "sha256:aaa",
    uri: str | None = None,
) -> str:
    now = _CLOCK.now().isoformat()
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, display_title, created_at, updated_at)"
            " VALUES (?,?,?,?,?,?)",
            (source_id, "pdf", uri or f"file:///{source_id}.pdf", f"Title {source_id}", now, now),
        )
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, created_at) VALUES (?,?,?,?)",
            (revision_id, source_id, asset_hash, now),
        )
        connection.commit()
    ir = _ir(f"u_{source_id}", "A vector space is closed under addition.")
    request_hash = extraction_request_hash(
        revision_id=revision_id,
        extractor=ir.extractor,
        extractor_version=ir.extractor_version,
        ir_schema_version=IR_SCHEMA_VERSION,
    )
    repo.insert_extraction_run(
        id=extraction_id,
        revision_id=revision_id,
        extractor=ir.extractor,
        extractor_version=ir.extractor_version,
        extraction_request_hash=request_hash,
        ir_schema_version=IR_SCHEMA_VERSION,
        status="running",
        clock=_CLOCK,
    )
    repo.persist_document_ir(extraction_id, ir)
    repo.complete_extraction_run(
        extraction_id, extraction_result_hash=extraction_result_hash(request_hash, ir), clock=_CLOCK
    )
    return extraction_id


def _vault(tmp_path: Path) -> tuple[Path, Repository]:
    root = tmp_path / "vault"
    init_vault(root, clock=_CLOCK)
    add_subject(root, "linear-algebra", "Linear Algebra", clock=_CLOCK)
    return root, Repository(root / "state.sqlite")


def test_delete_removes_every_derived_row_and_leaves_other_sources_intact(tmp_path: Path) -> None:
    root, repo = _vault(tmp_path)
    _seed_source(repo, source_id="src_a", revision_id="rev_a", extraction_id="ext_a")
    _seed_source(repo, source_id="src_b", revision_id="rev_b", extraction_id="ext_b", asset_hash="sha256:bbb")
    repo.insert_entity_source_link(
        entity_type="learning_object", entity_id="lo_1", locator="p1", relation="primary",
        source_id="src_a", revision_id="rev_a", extraction_id="ext_a", clock=_CLOCK,
    )
    repo.create_annotation(source_id="src_a", clock=_CLOCK)

    result = delete_source(load_vault(root), repo, "src_a", vault_root=root)

    assert repo.get_source_artifact("src_a") is None
    assert repo.source_revisions_for("src_a") == []
    assert repo.load_document_ir("ext_a") is None
    assert repo.entity_source_links_for_sources(["src_a"]) == []
    assert repo.annotations_for_source("src_a") == []
    assert result.deleted_rows["source_artifacts"] == 1
    assert result.deleted_rows["source_document_blocks"] == 1

    # The untouched source keeps its whole chain.
    assert repo.get_source_artifact("src_b") is not None
    assert repo.load_document_ir("ext_b") is not None


def test_delete_detaches_learner_records_instead_of_destroying_them(tmp_path: Path) -> None:
    """A commitment arc outlives the source that motivated it — the binding is
    nulled, the arc is not deleted."""

    root, repo = _vault(tmp_path)
    _seed_source(repo, source_id="src_a", revision_id="rev_a", extraction_id="ext_a")
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO commitments(id, created_action, created_at) VALUES (?,?,?)",
            ("cmt_1", "help_me_remember", _CLOCK.now().isoformat()),
        )
        connection.commit()
    arc_id = repo.create_commitment_arc(commitment_id="cmt_1", source_id="src_a", clock=_CLOCK)

    delete_source(load_vault(root), repo, "src_a", vault_root=root)

    with repo.connection() as connection:
        row = connection.execute(
            "SELECT id, source_id FROM commitment_arcs WHERE id = ?", (arc_id,)
        ).fetchone()
    assert row is not None, "the arc must survive its source"
    assert row["source_id"] is None


def test_delete_drops_the_source_from_its_collections(tmp_path: Path) -> None:
    root, repo = _vault(tmp_path)
    _seed_source(repo, source_id="src_a", revision_id="rev_a", extraction_id="ext_a")
    _seed_source(repo, source_id="src_b", revision_id="rev_b", extraction_id="ext_b", asset_hash="sha256:bbb")
    upsert_source_set(
        root,
        {
            "id": "set_x",
            "subject_id": "linear-algebra",
            "title": "Collection",
            "members": [
                {"source_id": "src_a", "revision_id": "rev_a", "default_role": "primary_textbook",
                 "scope": [{"unit_id": "u_src_a"}], "priority": 1},
                {"source_id": "src_b", "revision_id": "rev_b", "default_role": "reference",
                 "scope": [{"unit_id": "u_src_b"}], "priority": 2},
            ],
        },
        clock=_CLOCK,
    )

    plan = plan_source_deletion(load_vault(root), repo, "src_a")
    assert [impact.source_set_id for impact in plan.collections] == ["set_x"]
    assert plan.collections[0].leaves_empty is False

    result = delete_source(load_vault(root), repo, "src_a", vault_root=root)

    assert result.collections_updated == ["set_x"]
    members = next(s for s in load_vault(root).source_sets if s.id == "set_x").members
    assert [member.source_id for member in members] == ["src_b"]


def test_delete_keeps_stored_bytes_another_source_still_shares(tmp_path: Path) -> None:
    """The original store is content-addressed, so two artifacts importing the
    same file share one file on disk."""

    root, repo = _vault(tmp_path)
    shared = "sha256:shared"
    _seed_source(repo, source_id="src_a", revision_id="rev_a", extraction_id="ext_a", asset_hash=shared)
    _seed_source(repo, source_id="src_b", revision_id="rev_b", extraction_id="ext_b", asset_hash=shared)
    stored = canonical_source_raw_path(root, shared)
    stored.parent.mkdir(parents=True, exist_ok=True)
    stored.write_bytes(b"%PDF-1.7 shared")

    plan = plan_source_deletion(load_vault(root), repo, "src_a")
    assert plan.removes_stored_original is False

    result = delete_source(load_vault(root), repo, "src_a", vault_root=root)

    assert result.removed_original is False
    assert stored.is_file(), "the surviving source still needs these bytes"

    # Once the last holder goes, so do the bytes.
    second = delete_source(load_vault(root), repo, "src_b", vault_root=root)
    assert second.removed_original is True
    assert not stored.exists()


def test_delete_is_refused_while_an_ingest_job_is_active(tmp_path: Path) -> None:
    root, repo = _vault(tmp_path)
    _seed_source(repo, source_id="src_a", revision_id="rev_a", extraction_id="ext_a")
    repo.insert_ingest_batch(id="batch_1", workflow_type="import", clock=_CLOCK)
    repo.insert_ingest_job(
        id="job_1", batch_id="batch_1", ordinal=0, job_type="inventory",
        payload={"extraction_id": "ext_a"}, clock=_CLOCK,
    )

    plan = plan_source_deletion(load_vault(root), repo, "src_a")
    assert plan.deletable is False
    assert "job_1" in plan.blockers[0]

    with pytest.raises(SourceDeletionError) as excinfo:
        delete_source(load_vault(root), repo, "src_a", vault_root=root)
    assert excinfo.value.code == "source_delete_blocked"
    # Nothing was removed by the refused attempt.
    assert repo.get_source_artifact("src_a") is not None
    assert repo.load_document_ir("ext_a") is not None


def test_plan_reports_study_map_citations_without_deleting(tmp_path: Path) -> None:
    root, repo = _vault(tmp_path)
    _seed_source(repo, source_id="src_a", revision_id="rev_a", extraction_id="ext_a")
    for entity_id in ("lo_1", "lo_2"):
        repo.insert_entity_source_link(
            entity_type="learning_object", entity_id=entity_id, locator="p1", relation="primary",
            source_id="src_a", revision_id="rev_a", extraction_id="ext_a", clock=_CLOCK,
        )

    plan = plan_source_deletion(load_vault(root), repo, "src_a")

    assert plan.citation_count == 2
    assert {entity["entity_id"] for entity in plan.cited_entities} == {"lo_1", "lo_2"}
    assert plan.unit_count == 1 and plan.block_count == 1
    assert plan.title == "Title src_a"
    assert plan.deletable is True
    # A preview never mutates.
    assert repo.get_source_artifact("src_a") is not None
    assert len(repo.entity_source_links_for_sources(["src_a"])) == 2


def test_plan_rejects_an_unknown_source(tmp_path: Path) -> None:
    root, repo = _vault(tmp_path)
    with pytest.raises(SourceDeletionError) as excinfo:
        plan_source_deletion(load_vault(root), repo, "src_missing")
    assert excinfo.value.code == "source_not_found"


# --------------------------------------------------------------------------
# Sidecar contract — the Source library's delete affordance
# --------------------------------------------------------------------------


def _sidecar(vault_root: Path, *messages) -> list[dict]:
    import io
    import json

    from learnloop_sidecar.server import serve

    payload = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}}
    ]
    payload.extend(
        {"jsonrpc": "2.0", "id": index + 2, "method": name, "params": params}
        for index, (name, params) in enumerate(messages)
    )
    stdin = io.StringIO("".join(json.dumps(message) + "\n" for message in payload))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()][1:]


def test_delete_source_over_the_sidecar_removes_it_from_the_library(tmp_path: Path) -> None:
    root, repo = _vault(tmp_path)
    _seed_source(repo, source_id="src_a", revision_id="rev_a", extraction_id="ext_a")
    _seed_source(repo, source_id="src_b", revision_id="rev_b", extraction_id="ext_b", asset_hash="sha256:bbb")

    responses = _sidecar(
        root,
        ("preview_source_deletion", {"sourceId": "src_a"}),
        ("delete_source", {"sourceId": "src_a"}),
        ("get_source_library", {}),
    )

    plan = responses[0]["result"]["plan"]
    assert plan["deletable"] is True
    assert plan["unitCount"] == 1
    deleted = responses[1]["result"]["deleted"]
    assert deleted["sourceId"] == "src_a"
    assert deleted["deletedRows"]["sourceArtifacts"] == 1
    assert [card["sourceId"] for card in responses[2]["result"]["sources"]] == ["src_b"]


def test_delete_source_over_the_sidecar_reports_a_missing_source(tmp_path: Path) -> None:
    root, _repo = _vault(tmp_path)
    responses = _sidecar(root, ("delete_source", {"sourceId": "src_missing"}))
    assert responses[0]["error"]["data"]["code"] == "source_not_found"
