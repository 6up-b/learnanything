"""Local-first capture + outbox crash safety (spec §5.3, §13.3, §15.2).

The §15.2 crash test: kill the process after local commit but before drain (and
mid-drain), reopen the durable SQLite from disk, and assert nothing is lost and
nothing is duplicated (idempotent drain). Attempt submission / reading stays usable
with the drain worker down.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import textwrap
from pathlib import Path

from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.services import reader_capture as RC
from tests.test_source_inventory import _persist, _register_revision


def _ingest(repo: Repository) -> None:
    _register_revision(repo, source_id="src1", revision_id="rev1")
    blocks = [
        DocumentBlock.build(span_id="s1", block_type="Text", text="Symmetric matrices have real eigenvalues.", ordinal=1, page=0, bbox=[10, 50, 300, 90], section_path=["Ch1"]),
    ]
    ir = DocumentIR(
        extractor="marker", extractor_version="1",
        units=[DocumentUnit(unit_id="u1", label="x", ordinal=0, semantic_hash="sha256:s", span_ids=["s1"])],
        blocks=blocks, assets=[], health=ExtractionHealth(),
    )
    _persist(repo, ir, revision_id="rev1", extraction_id="ext1")


def _capture(repo: Repository, key: str) -> dict:
    return RC.capture(
        repo, source_id="src1", revision_id="rev1", extraction_id="ext1",
        action="interpretation", client_idempotency_key=key,
        raw_selection={"nodes": [{"span_id": "s1", "quote": "Symmetric"}]}, learner_text="note",
    )


def test_capture_is_one_atomic_transaction(tmp_path: Path) -> None:
    repo = Repository(tmp_path / "state.sqlite")
    _ingest(repo)
    receipt = _capture(repo, "k1")
    assert receipt["receipt"] == "acknowledged"
    assert receipt["anchor_status"] == "exact"
    # annotation + interaction event + outbox row all landed.
    assert repo.annotation_head(receipt["annotation_id"]) is not None
    assert len(repo.pending_capture_outbox()) == 1
    assert len(repo.reader_interaction_events(kind="reader_capture_acknowledged")) == 1


def test_retry_same_key_no_duplicates(tmp_path: Path) -> None:
    repo = Repository(tmp_path / "state.sqlite")
    _ingest(repo)
    first = _capture(repo, "dupe")
    second = _capture(repo, "dupe")
    assert second["deduplicated"] is True
    assert second["annotation_id"] == first["annotation_id"]
    # exactly one annotation version, one event, one outbox row.
    with repo.connection() as c:
        assert c.execute("SELECT COUNT(*) FROM source_annotation_versions").fetchone()[0] == 1
        assert c.execute("SELECT COUNT(*) FROM interaction_events WHERE kind='reader_capture_acknowledged'").fetchone()[0] == 1
        assert c.execute("SELECT COUNT(*) FROM reader_capture_outbox").fetchone()[0] == 1


def test_capture_rolls_back_atomically_on_failure(tmp_path: Path) -> None:
    repo = Repository(tmp_path / "state.sqlite")
    _ingest(repo)
    # An invalid interaction-event kind violates the CHECK inside the single txn ->
    # the WHOLE capture rolls back: no annotation, no event, no outbox, no ack.
    try:
        repo.capture_local_transaction(
            source_id="src1", client_idempotency_key="bad",
            annotation={"annotation_type": "highlight", "learner_text": "x"},
            anchor={"source_id": "src1", "revision_id": "rev1", "extraction_id": "ext1", "status": "exact",
                    "segments": [{"span_id": "s1", "block_content_hash": "sha256:x", "codepoint_start": 0,
                                  "codepoint_end": 1, "exact_quote": "S", "selection_text_hash": "h"}]},
            interaction_event={"kind": "NOT_A_VALID_KIND", "origin": "learner"},
            outbox={"capture_kind": "annotation"},
        )
        raised = False
    except Exception:
        raised = True
    assert raised
    with repo.connection() as c:
        assert c.execute("SELECT COUNT(*) FROM source_annotations").fetchone()[0] == 0
        assert c.execute("SELECT COUNT(*) FROM reader_capture_outbox").fetchone()[0] == 0
        assert c.execute("SELECT COUNT(*) FROM interaction_events WHERE kind='NOT_A_VALID_KIND'").fetchone()[0] == 0


def test_drain_is_idempotent(tmp_path: Path) -> None:
    repo = Repository(tmp_path / "state.sqlite")
    _ingest(repo)
    receipt = _capture(repo, "k1")
    r1 = RC.drain_outbox(repo)
    assert r1["drained"] == [receipt["outbox_id"]]
    # re-draining after everything is done does nothing (no dup work).
    r2 = RC.drain_outbox(repo)
    assert r2["drained"] == []
    row = repo.get_capture_outbox(receipt["outbox_id"])
    assert row["state"] == "done"
    assert row["target_ref"] == receipt["annotation_id"]


def test_commit_preset_captures_commitment_and_enqueues_one_synth_request(tmp_path: Path) -> None:
    # §5.3 + §15.2: a commit preset creates a commitment AND a durable annotation in
    # one safe capture; the outbox drain enqueues exactly one demand-paged synthesis
    # request, and re-draining never double-enqueues (idempotent on the request key).
    repo = Repository(tmp_path / "state.sqlite")
    _ingest(repo)
    receipt = RC.invoke_preset(
        repo, preset="help_me_remember", source_id="src1", revision_id="rev1",
        extraction_id="ext1", client_idempotency_key="c1",
        raw_selection={"nodes": [{"span_id": "s1", "quote": "Symmetric"}]},
        learner_text="keep this", subject_id="s1",
    )
    assert receipt["commitment_id"]
    assert repo.annotation_head(receipt["annotation_id"]) is not None
    RC.drain_outbox(repo)
    assert len(repo.reader_requests_for_source("src1")) == 1
    # The annotation + commitment are already safe; re-draining is a no-op and the
    # convert seam (which enqueues on the canonical request key) never duplicates.
    RC.drain_outbox(repo)
    assert len(repo.reader_requests_for_source("src1")) == 1


def test_ask_and_mark_presets_never_create_commitments(tmp_path: Path) -> None:
    repo = Repository(tmp_path / "state.sqlite")
    _ingest(repo)
    for i, preset in enumerate(("ask", "mark_confusing", "not_worth_remembering")):
        r = RC.invoke_preset(
            repo, preset=preset, source_id="src1", revision_id="rev1", extraction_id="ext1",
            client_idempotency_key=f"k{i}", raw_selection={"nodes": [{"span_id": "s1", "quote": "Symmetric"}]},
            subject_id="s1",
        )
        assert r["commitment_id"] is None


_CHILD_TEMPLATE = textwrap.dedent(
    """
    import os, signal, sys
    from pathlib import Path
    sys.path.insert(0, {repo_src!r})
    from learnloop.db.repositories import Repository
    from learnloop.services import reader_capture as RC
    repo = Repository(Path({db!r}))
    stage = {stage!r}
    if stage == "after_capture":
        RC.capture(repo, source_id="src1", revision_id="rev1", extraction_id="ext1",
                   action="interpretation", client_idempotency_key="crash1",
                   raw_selection={{"nodes": [{{"span_id": "s1", "quote": "Symmetric"}}]}}, learner_text="note")
        os.kill(os.getpid(), signal.SIGKILL)
    elif stage == "mid_drain":
        RC.capture(repo, source_id="src1", revision_id="rev1", extraction_id="ext1",
                   action="interpretation", client_idempotency_key="crash1",
                   raw_selection={{"nodes": [{{"span_id": "s1", "quote": "Symmetric"}}]}}, learner_text="note")
        def boom(repository, row):
            os.kill(os.getpid(), signal.SIGKILL)
        RC.drain_outbox(repo, convert=boom)
    """
)


def _run_child(tmp_path: Path, db: Path, stage: str) -> int:
    repo_src = str(Path(__file__).resolve().parents[1] / "src")
    script = tmp_path / f"child_{stage}.py"
    script.write_text(_CHILD_TEMPLATE.format(repo_src=repo_src, db=str(db), stage=stage))
    proc = subprocess.run([sys.executable, str(script)], capture_output=True)
    return proc.returncode


# F3: the help_me_remember commit-preset path is a longer transaction than a bare
# capture -- it creates a commitment + arc BEFORE the capture, then the drain
# enqueues synthesis. SIGKILL at each seam and assert an idempotent resume leaves
# exactly one of {commitment, arc, capture/annotation, synthesis request}.
_PRESET_CHILD_TEMPLATE = textwrap.dedent(
    """
    import os, signal, sys
    from pathlib import Path
    sys.path.insert(0, {repo_src!r})
    from learnloop.db.repositories import Repository
    from learnloop.services import reader_capture as RC
    repo = Repository(Path({db!r}))
    stage = {stage!r}
    SEL = {{"nodes": [{{"span_id": "s1", "quote": "Symmetric"}}]}}
    KW = dict(preset="help_me_remember", source_id="src1", revision_id="rev1",
              extraction_id="ext1", client_idempotency_key="preset1",
              raw_selection=SEL, learner_text="keep this", subject_id="s1")
    if stage == "before_capture":
        # (a) crash AFTER commitment + arc creation but BEFORE the capture commit.
        def boom_capture(*a, **k):
            os.kill(os.getpid(), signal.SIGKILL)
        RC.capture = boom_capture
        RC.invoke_preset(repo, **KW)
    elif stage == "before_synth":
        # (b) crash AFTER the outbox drain claims the row but BEFORE synth enqueue.
        RC.invoke_preset(repo, **KW)
        def boom(repository, row):
            os.kill(os.getpid(), signal.SIGKILL)
        RC.drain_outbox(repo, convert=boom)
    """
)


def _run_preset_child(tmp_path: Path, db: Path, stage: str) -> int:
    repo_src = str(Path(__file__).resolve().parents[1] / "src")
    script = tmp_path / f"preset_child_{stage}.py"
    script.write_text(_PRESET_CHILD_TEMPLATE.format(repo_src=repo_src, db=str(db), stage=stage))
    proc = subprocess.run([sys.executable, str(script)], capture_output=True)
    return proc.returncode


def _preset_counts(repo: Repository) -> dict[str, int]:
    with repo.connection() as c:
        return {
            "commitments": c.execute("SELECT COUNT(*) FROM commitments").fetchone()[0],
            "arcs": c.execute("SELECT COUNT(*) FROM commitment_arcs").fetchone()[0],
            "annotations": c.execute("SELECT COUNT(*) FROM source_annotation_versions").fetchone()[0],
            "outbox": c.execute("SELECT COUNT(*) FROM reader_capture_outbox").fetchone()[0],
        }


def _invoke_preset(repo: Repository) -> dict:
    return RC.invoke_preset(
        repo, preset="help_me_remember", source_id="src1", revision_id="rev1",
        extraction_id="ext1", client_idempotency_key="preset1",
        raw_selection={"nodes": [{"span_id": "s1", "quote": "Symmetric"}]},
        learner_text="keep this", subject_id="s1",
    )


def test_preset_crash_between_arc_and_capture_resumes_exactly_once(tmp_path: Path) -> None:
    # F3 (a): SIGKILL between commitment/arc creation and the capture commit. The
    # commitment + arc are durable; the annotation/outbox are not yet. An idempotent
    # resume reuses both and completes the capture -- exactly one of each.
    db = tmp_path / "state.sqlite"
    _ingest(Repository(db))
    rc = _run_preset_child(tmp_path, db, "before_capture")
    assert rc == -signal.SIGKILL

    repo = Repository(db)
    before = _preset_counts(repo)
    assert before["commitments"] == 1 and before["arcs"] == 1  # committed before crash
    assert before["annotations"] == 0 and before["outbox"] == 0  # capture never ran

    receipt = _invoke_preset(repo)  # resume with the same client key
    assert receipt["commitment_id"] is not None
    after = _preset_counts(repo)
    assert after == {"commitments": 1, "arcs": 1, "annotations": 1, "outbox": 1}

    RC.drain_outbox(repo)
    assert len(repo.reader_requests_for_source("src1")) == 1
    # A second resume + drain never duplicates anything.
    _invoke_preset(repo)
    RC.drain_outbox(repo)
    assert _preset_counts(repo) == {"commitments": 1, "arcs": 1, "annotations": 1, "outbox": 1}
    assert len(repo.reader_requests_for_source("src1")) == 1


def test_preset_crash_between_drain_and_synth_enqueues_once(tmp_path: Path) -> None:
    # F3 (b): SIGKILL between the outbox drain claiming the row and the synthesis
    # enqueue. Commitment/arc/annotation are all durable; the stale draining row is
    # reclaimed on resume and synthesis is enqueued exactly once.
    db = tmp_path / "state.sqlite"
    _ingest(Repository(db))
    rc = _run_preset_child(tmp_path, db, "before_synth")
    assert rc == -signal.SIGKILL

    repo = Repository(db)
    counts = _preset_counts(repo)
    assert counts == {"commitments": 1, "arcs": 1, "annotations": 1, "outbox": 1}
    assert len(repo.reader_requests_for_source("src1")) == 0  # synth never enqueued
    assert len(repo.recoverable_capture_outbox()) == 1  # row left mid-drain

    RC.drain_outbox(repo)  # reclaims the stale row and enqueues synthesis once
    assert len(repo.reader_requests_for_source("src1")) == 1
    RC.drain_outbox(repo)  # idempotent re-drain
    assert len(repo.reader_requests_for_source("src1")) == 1
    assert _preset_counts(repo) == {"commitments": 1, "arcs": 1, "annotations": 1, "outbox": 1}


def test_crash_after_capture_before_drain_survives_and_resumes_once(tmp_path: Path) -> None:
    db = tmp_path / "state.sqlite"
    Repository(db)
    _ingest(Repository(db))
    rc = _run_child(tmp_path, db, "after_capture")
    assert rc == -signal.SIGKILL  # process was killed, not a clean exit

    # Reopen the durable DB from disk (simulates the app restart).
    repo = Repository(db)
    assert len(repo.annotations_for_source("src1")) == 1  # annotation is safe
    pending = repo.pending_capture_outbox()
    assert len(pending) == 1  # outbox row survived as pending

    result = RC.drain_outbox(repo)
    assert len(result["drained"]) == 1
    assert repo.pending_capture_outbox() == []

    # Retrying the same client key after restart never duplicates.
    dup = _capture(repo, "crash1")
    assert dup["deduplicated"] is True
    with repo.connection() as c:
        assert c.execute("SELECT COUNT(*) FROM reader_capture_outbox").fetchone()[0] == 1
        assert c.execute("SELECT COUNT(*) FROM source_annotation_versions").fetchone()[0] == 1


def test_crash_mid_drain_recovers_without_duplication(tmp_path: Path) -> None:
    db = tmp_path / "state.sqlite"
    _ingest(Repository(db))
    rc = _run_child(tmp_path, db, "mid_drain")
    assert rc == -signal.SIGKILL

    repo = Repository(db)
    # The row is left mid-flight (draining) but recoverable -- nothing is lost.
    assert len(repo.recoverable_capture_outbox()) == 1
    result = RC.drain_outbox(repo)  # reclaims the stale draining row
    assert len(result["drained"]) == 1
    assert repo.recoverable_capture_outbox() == []
    with repo.connection() as c:
        assert c.execute("SELECT COUNT(*) FROM reader_capture_outbox WHERE state='done'").fetchone()[0] == 1
        assert c.execute("SELECT COUNT(*) FROM source_annotation_versions").fetchone()[0] == 1
