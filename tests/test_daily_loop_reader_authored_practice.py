"""Daily-loop audit 2026-10-11: the reader's "write my own question" went nowhere.

``reader.author_qa`` saved the learner's Q+A as a commitment plus an activity card
version, a store the scheduler never reads, while the reader said "It will return
as personal practice". Writing the question is an explicit adoption into practice
(no confirmation step), so the card must become a real Practice Item that the
scheduler serves:

* filed under the Learning Object whose provenance cites the passage the learner
  was reading, through the learner-authored item path (vault YAML);
* linked to the authoring commitment as a ``legacy_practice_item`` target, which
  makes it a learner-requested item, served even on a never-practised LO;
* honest when no topic can be found: kept as a reference, never claimed as
  practice.
"""

from __future__ import annotations

import io
import json
from datetime import timedelta
from pathlib import Path

import pytest

from learnloop.attempts.attempts import ApplyAttemptInput, AttemptDraft, ResolvedGrade, apply_attempt
from learnloop.clock import FrozenClock
from learnloop.curriculum import commitments as C
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.reader import reader_authoring as AUTH
from learnloop.scheduling.scheduler import build_due_queue
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml
from learnloop_sidecar.server import serve

from tests.helpers import NOW, create_basic_vault
from tests.test_source_inventory import _persist, _register_revision

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


def test_written_question_becomes_practice_the_scheduler_serves(tmp_path):
    paths = _reader_vault(tmp_path)
    repository = Repository(paths.sqlite_path)
    assert not repository.mastery_state(LO_ID).last_evidence_at, "sanity: a never-practised LO"

    result = _author(paths)

    assert result["practice_status"] == "scheduled"
    assert result["learning_object_id"] == LO_ID
    item_id = result["practice_item_id"]
    item = load_vault(paths.root).practice_items[item_id]
    # The learner's exact words, learner provenance, grounded in the passage read.
    assert item.prompt == QUESTION and item.expected_answer == ANSWER
    assert item.provenance.origin == "human"
    assert [ref.locator for ref in item.provenance.source_refs] == ["span:ext1/s2"]
    # The commitment that records the adoption names the card it adopted.
    head = C.resolve_head(repository, result["commitment_id"])
    assert ("legacy_practice_item", item_id) in {(t.target_kind, t.target_ref) for t in head.targets}

    # Served now -- first, as the learner's own request -- although the LO has
    # never been practised and sits on no goal frontier.
    queue = _queue_ids(paths)
    assert queue and queue[0] == item_id


def test_written_question_keeps_returning_after_it_is_answered(tmp_path):
    paths = _reader_vault(tmp_path)
    item_id = _author(paths)["practice_item_id"]
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=CLOCK)
    apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(practice_item_id=item_id, learner_answer_md=ANSWER,
                               attempt_type="independent_attempt"),
            attempt_id=new_ulid(),
            grade=ResolvedGrade(rubric_score=4, criterion_points={"correctness": 4.0}, evidence_rows=[],
                                error_attributions=[], grader_confidence=1.0, confidence=4,
                                manual_review_reason=None),
            grading_source="ai",
        ),
        clock=CLOCK,
    )
    state = repository.practice_item_state(item_id)
    assert state is not None and state.due_at is not None
    # It is ordinary personal practice now: back in the queue once it is due.
    due = FrozenClock(NOW).now() + timedelta(days=400)
    assert item_id in _queue_ids(paths, at=due)


def test_retry_with_the_same_key_adopts_one_card(tmp_path):
    paths = _reader_vault(tmp_path)
    first = _author(paths)
    second = _author(paths)
    assert first["commitment_id"] == second["commitment_id"]
    assert first["practice_item_id"] == second["practice_item_id"]
    learner_cards = [
        item for item in load_vault(paths.root).practice_items.values() if item.prompt == QUESTION
    ]
    assert len(learner_cards) == 1


def test_question_with_no_topic_to_file_under_is_kept_as_a_reference(tmp_path):
    """Nothing on the study map cites this passage: no card is invented and the
    result says so, so the reader does not claim practice that will not happen."""

    paths = _reader_vault(tmp_path, cite_span=False)
    result = _author(paths)
    assert result["practice_status"] == "reference_only"
    assert result["practice_item_id"] is None
    assert not any(item.prompt == QUESTION for item in load_vault(paths.root).practice_items.values())
    # The learner's words are still saved verbatim on the card contract.
    assert result["contract"]["prompt"] == QUESTION


def test_explicit_learning_object_is_honoured(tmp_path):
    paths = _reader_vault(tmp_path, cite_span=False)
    result = _author(paths, learning_object_id=LO_ID)
    assert result["practice_status"] == "scheduled"
    assert result["learning_object_id"] == LO_ID


def _rpc(root: Path, calls: list[tuple[str, dict]]) -> list[dict]:
    messages = [{"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"vaultPath": str(root)}}]
    for index, (method, params) in enumerate(calls, start=1):
        messages.append({"jsonrpc": "2.0", "id": index, "method": method, "params": params})
    stdout = io.StringIO()
    serve(io.StringIO("".join(json.dumps(message) + "\n" for message in messages)), stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def test_sidecar_author_qa_serves_the_card_in_today_queue(tmp_path):
    paths = _reader_vault(tmp_path)
    toml = paths.root / "learnloop.toml"
    text = toml.read_text(encoding="utf-8")
    if "reader_enabled" in text:
        text = text.replace("reader_enabled = false", "reader_enabled = true")
    else:
        text += "\n[tutor_qa]\nreader_enabled = true\n"
    toml.write_text(text, encoding="utf-8")

    out = _rpc(paths.root, [
        ("reader.author_qa", {
            "question": QUESTION, "answer": ANSWER, "sourceId": "src1", "revisionId": "rev1",
            "subjectId": "span:ext1/s2", "clientIdempotencyKey": "qa-rpc",
        }),
        ("get_today_queue", {}),
    ])
    authored = out[1]["result"]
    assert authored["practiceStatus"] == "scheduled"
    assert authored["learningObjectId"] == LO_ID
    served = [item["practiceItemId"] for section in out[2]["result"]["sections"] for item in section["items"]]
    assert authored["practiceItemId"] in served


@pytest.mark.parametrize("status", ["dormant", "resolved"])
def test_question_is_not_filed_under_a_put_away_lo(tmp_path, status):
    paths = _reader_vault(tmp_path)
    lo_path = paths.learning_object_path("linear-algebra", LO_ID)
    lo = read_yaml(lo_path)
    lo["status"] = status
    write_yaml(lo_path, lo)
    result = _author(paths, learning_object_id=LO_ID)
    assert result["practice_status"] == "reference_only"
