"""What other test files use from ``tests/test_notes_as_learner_text.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.diagnosis.text_gaps import jobs as J
from learnloop.diagnosis.text_gaps.pipeline import PipelineClients

from tests.helpers import NOW
from tests.reading_path_fixtures import call
from tests.notes_linked_helpers import _deliverable, _lines
from tests.text_gap_fakes import GapLLMFake


CLOCK = FrozenClock(NOW)
GAPS_ON = "[notes]\ngaps_enabled = true\n"


class PlanGapFake(GapLLMFake):
    """The gap reader and judge on the ChatGPT plan."""

    provider_name = "fake_plan_gap"
    provider_type = "chatgpt_plan"
    model = "fake/plan-gap"


def _linked(tmp_path: Path, monkeypatch=None, *, gaps: bool = True, config: str = ""):
    """C2's deliverable vault with the path's two vault notes linked (the typed Reader note
    carries ``SENTINEL``; the other is a capture), and the opt-in on (or off)."""

    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path, config=(GAPS_ON if gaps else "") + config)
    ctx.post_attempt_worker.autostart = False  # jobs are run by hand here
    lines = _lines(call(ctx, "notes.path", {"goal_id": goal_id}))
    assert {line["noteKey"] for line in lines} == {corpus["typed"], corpus["captured"]}
    _CORPUS[str(repository.sqlite_path)] = corpus
    return paths, repository, ctx, goal_id, corpus, lines


#: The corpus of each linked vault (by database), so :func:`_snapshots` can name its notes.
_CORPUS: dict[str, dict[str, str]] = {}
TYPED, CAPTURED = "typed", "captured"


def _snapshots(repository) -> dict[str, str]:
    """``{"typed" | "captured": the newest snapshot id}``."""

    corpus = _CORPUS[str(repository.sqlite_path)]
    names = {corpus[TYPED]: TYPED, corpus[CAPTURED]: CAPTURED}
    with repository.connection() as connection:
        return {names[str(row[1])]: str(row[0]) for row in connection.execute(
            "SELECT id, note_key FROM learner_notes ORDER BY created_at, rowid") if str(row[1]) in names}


def _typed_line(lines):
    return next(line for line in lines if "Av = lv" in line["note"]["text"])


def _gaps(repository) -> list[dict]:
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM learner_text_gaps WHERE source_kind = 'learner_note' ORDER BY created_at, id")]


def _clients(llm, *, decider=None) -> PipelineClients:
    return PipelineClients(judge=lambda: llm, reader=lambda: llm, decider=(lambda: decider) if decider else None,
                           drafter=lambda: llm, tutor=None, embedder=None)


def _run(paths, repository, clients, *, source: tuple[str, str] | None = None):
    return J.process_next_gap_job(paths.root, repository, owner="t", clients=clients, clock=CLOCK, source=source)
