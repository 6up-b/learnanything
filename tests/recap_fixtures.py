"""Shared seeding for RW6a's tests ("Last time here", the session summary,
ReaderObservationV1 and Wrap up; spec_reader_workbench_v1 §9.1).

Everything goes through the code the Reader itself uses: visits through
``reader_inquiry.record_activity`` (the RW1a envelope), questions through
``reader_dialogue.ask`` with the stub client, statuses and reconnect answers
through ``reader_inquiry``, problems through ``reader.workbench``. Each write
takes a frozen clock ``minutes`` after ``T0`` so sessions have real gaps.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.reader import reader_dialogue as RD
from learnloop.reader import reader_inquiry as RI
from learnloop.reader import workbench as WB
from tests.helpers import NOW

EXT = "ext1"
T0 = NOW


def at(minutes: float) -> FrozenClock:
    return FrozenClock(T0 + timedelta(minutes=minutes))


def iso(minutes: float) -> str:
    return (T0 + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def open_visit(repo: Repository, visit_id: str, minutes: float, *, extraction_id: str = EXT) -> None:
    RI.record_activity(repo, [{
        "kind": "reader_view_opened",
        "payload": {"visitId": visit_id, "extractionId": extraction_id, "sourceId": "src1", "surface": "text"},
    }], clock=at(minutes))


def close_visit(repo: Repository, visit_id: str, minutes: float, *, extraction_id: str = EXT) -> None:
    RI.record_activity(repo, [{
        "kind": "reader_view_closed",
        "payload": {"visitId": visit_id, "extractionId": extraction_id, "activeSeconds": 60, "idleSeconds": 0},
    }], clock=at(minutes))


def visit(repo: Repository, visit_id: str, start: float, end: float | None, *, extraction_id: str = EXT) -> None:
    open_visit(repo, visit_id, start, extraction_id=extraction_id)
    if end is not None:
        close_visit(repo, visit_id, end, extraction_id=extraction_id)


def ask(vault: Any, repo: Repository, question: str, minutes: float, *, parent: str | None = None,
        span_id: str = "s1", extraction_id: str = EXT) -> dict[str, Any]:
    return RD.ask(vault, repo, RD.StubReaderClient(), extraction_id=extraction_id, span_id=span_id,
                  question_md=question, parent_exchange_id=parent, clock=at(minutes))


def resolve(repo: Repository, exchange_id: str, minutes: float, resolution: str = "resolved") -> None:
    RI.set_inquiry_status(repo, extraction_id=EXT, exchange_id=exchange_id, resolution=resolution,
                          trigger="chip", clock=at(minutes))


def still_unclear(repo: Repository, exchange_id: str, minutes: float) -> dict[str, Any]:
    return RI.answer_reconnect(repo, extraction_id=EXT, exchange_id=exchange_id, answer="still_unclear",
                               via="inline", clock=at(minutes))


def cue_tap(repo: Repository, minutes: float, *, event: str = "cue_opened", visit_id: str | None = None) -> None:
    """A cue impression (client) -- the activity the wrap-up rule ignores."""

    RI.record_activity(repo, [{
        "kind": "reader_action_invoked", "event": "cue_shown",
        "payload": {"visitId": visit_id, "extractionId": EXT, "cueId": "cue_1", "cueKind": "revisit"},
    }], clock=at(minutes))


def selection(repo: Repository, minutes: float, visit_id: str) -> None:
    RI.record_activity(repo, [{
        "kind": "reader_selection", "payload": {"visitId": visit_id, "extractionId": EXT, "spanCount": 1},
    }], clock=at(minutes))


def problem(repo: Repository, minutes: float, *, steps: int = 2, book: bool = True,
            stem: str = "Exercise 5.14: write the CDF of the mixture.") -> dict[str, Any]:
    session, _resumed = WB.open_session(
        repo, origin="reader", entry="work_through", stem_md=stem, extraction_id=EXT, span_ids=["s1"],
        source_visible=book, clock=at(minutes),
    )
    for index in range(steps):
        WB.save_step(repo, session["id"], op="add", client_idempotency_key=f"{session['id']}-{index}",
                     body_md=f"step {index + 1}", clock=at(minutes + 0.5 * (index + 1)))
    return WB.session_row(repo, session["id"])


def table_counts(repo: Repository) -> dict[str, int]:
    with repo.connection() as connection:
        names = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )]
        return {
            name: connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
            for name in names if not name.startswith("source_block_fts")
        }


def interaction_rows(repo: Repository) -> list[tuple]:
    with repo.connection() as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT id, kind, subject_type, subject_id, payload_json, created_at FROM interaction_events ORDER BY id"
        )]


def call(ctx: Any, name: str, params: dict[str, Any]) -> dict[str, Any]:
    import learnloop_sidecar.handlers  # noqa: F401 - register methods
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def context(root: Any) -> Any:
    from learnloop_sidecar.context import SidecarContext

    ctx = SidecarContext()
    ctx.load(root)
    return ctx
