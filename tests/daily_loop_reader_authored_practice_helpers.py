"""What other test files use from ``tests/test_daily_loop_reader_authored_practice.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.reader import reader_authoring as AUTH
from learnloop.scheduling.scheduler import build_due_queue
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW, create_basic_vault
from tests.source_inventory_helpers import _persist, _register_revision


LO_ID = "lo_svd_definition"
CLOCK = FrozenClock(NOW)
QUESTION = "Why are the columns of U orthonormal?"
ANSWER = "Because U holds the eigenvectors of the symmetric matrix A A^T."


def _reader_vault(tmp_path, *, cite_span: bool = True, goal_active: bool = False) -> VaultPaths:
    """A basic vault with one extraction (``ext1``: spans s0-s2, section u1) whose
    span ``s1`` the LO's provenance cites. The goal is paused by default so the
    LO is cold (never practised, off every goal frontier) -- the common case of
    reading new material."""

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    _register_revision(repository, source_id="src1", revision_id="rev1")
    blocks = [
        DocumentBlock.build(span_id="s0", block_type="Section", text="Singular value decomposition",
                            ordinal=0, page=1, section_path=["SVD"]),
        DocumentBlock.build(span_id="s1", block_type="Text",
                            text="The singular value decomposition writes A as U Sigma V transpose.",
                            ordinal=1, page=1, section_path=["SVD"]),
        DocumentBlock.build(span_id="s2", block_type="Text", text="The columns of U and V are orthonormal.",
                            ordinal=2, page=1, section_path=["SVD"]),
    ]
    ir = DocumentIR(
        extractor="marker", extractor_version="1",
        units=[DocumentUnit(unit_id="u1", label="SVD", ordinal=0, semantic_hash="sha256:svd",
                            page_start=1, page_end=1, span_ids=["s0", "s1", "s2"])],
        blocks=blocks, assets=[], health=ExtractionHealth(),
    )
    _persist(repository, ir, revision_id="rev1", extraction_id="ext1")

    lo_path = paths.learning_object_path("linear-algebra", LO_ID)
    lo = read_yaml(lo_path)
    lo["provenance"]["source_refs"] = (
        [{"ref_type": "canonical_source", "ref_id": "src1", "locator": "span:ext1/s1",
          "source_id": "src1", "extraction_id": "ext1"}]
        if cite_span
        else []
    )
    write_yaml(lo_path, lo)
    goals = read_yaml(paths.goals_path)
    goals["goals"][0]["status"] = "active" if goal_active else "paused"
    write_yaml(paths.goals_path, goals)
    sync_vault_state(load_vault(paths.root), repository, clock=CLOCK)
    return paths


def _author(paths: VaultPaths, *, key: str = "qa1", span: str = "s2", **overrides):
    params = dict(
        question=QUESTION, answer=ANSWER, source_id="src1", revision_id="rev1",
        subject_id=f"span:ext1/{span}", client_idempotency_key=key, clock=CLOCK,
    )
    params.update(overrides)
    return AUTH.author_qa(Repository(paths.sqlite_path), root=paths.root, **params)


def _queue_ids(paths: VaultPaths, *, at=NOW) -> list[str]:
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(at))
    return [entry.practice_item_id for entry in build_due_queue(vault, repository, clock=FrozenClock(at))]
