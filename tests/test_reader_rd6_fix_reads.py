"""RD6's fix round: ``goal.band`` and ``goal.lens`` are reads. A goal change a stopped process left half done (its
journal entry) is finished by the next curriculum action, never by a band or lens read: those write no file."""
from __future__ import annotations

from pathlib import Path

from tests.goal_lens_helpers import build_lens_vault, lens_context, scoped_goal
from tests.reading_path_fixtures import call


def _files(root: Path) -> dict[str, tuple[int, int]]:
    """Every file under the vault but its database (whose pages a read may touch), with its size and time."""

    return {str(path.relative_to(root)): (path.stat().st_size, path.stat().st_mtime_ns)
            for path in sorted(root.rglob("*")) if path.is_file() and ".sqlite" not in path.name}


def test_band_and_lens_reads_leave_an_unfinished_goal_change_for_the_next_action(tmp_path):
    paths, repository = build_lens_vault(tmp_path / "vault")
    goal_id = scoped_goal(paths, repository)
    ctx = lens_context(paths)
    journal = paths.root / ".learnloop" / "curriculum-journal"
    journal.mkdir(parents=True, exist_ok=True)
    (journal / "dpj_stopped.json").write_text("{", encoding="utf-8")  # a stopped process's half-written entry
    before = _files(paths.root)
    call(ctx, "goal.band", {"goal_id": goal_id})
    call(ctx, "goal.lens", {"goal_id": goal_id, "extraction_id": "ext_book"})
    assert _files(paths.root) == before
    # The next curriculum action finishes (here: drops) it.
    call(ctx, "curriculum.path", {"goal_id": goal_id})
    assert not (journal / "dpj_stopped.json").exists()


def _check(repository, lo_id: str, *, days: int) -> str:
    from datetime import UTC, datetime, timedelta

    from learnloop.curriculum import commitments as C
    from learnloop.source_retrieval import deliverable_path as DP

    day = (datetime.now(UTC) + timedelta(days=days)).strftime("%Y-%m-%d")
    C.create_commitment(
        repository, action="test_me_later", intent_text=f"check {lo_id}", depth_preset=DP.READY_DEPTH_PRESET,
        targets=[{"target_kind": "learning_object", "target_ref": lo_id, "role": "required"}],
        client_idempotency_key=f"rd6fix-next:{lo_id}", due_hint=day, provenance={"via": "deliverable_ready"})
    return day


def test_the_band_says_when_the_next_check_falls_due_so_it_is_read_again_then(tmp_path):
    paths, repository = build_lens_vault(tmp_path / "vault")
    goal_id = scoped_goal(paths, repository)
    ctx = lens_context(paths)
    assert call(ctx, "goal.band", {"goal_id": goal_id})["nextCheckDue"] is None
    _check(repository, "lo_det", days=-1)  # due already: hidden now, not a time to read again
    day = _check(repository, "lo_eigen", days=2)
    band = call(ctx, "goal.band", {"goal_id": goal_id})
    from datetime import UTC, datetime

    due = datetime.strptime(band["nextCheckDue"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    # Its day (the stamp is that day's start where the learner is, in UTC), never the check already due.
    assert due > datetime.now(UTC) and abs((due.date() - datetime.strptime(day, "%Y-%m-%d").date()).days) <= 1
