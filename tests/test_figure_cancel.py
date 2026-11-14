"""Cancelling a pressed figure build stops it (ledger K10-1).

``reader.figure_job_cancel`` marks the job; the build's ``FiguresGate`` asks
that mark before every physical model request and before the row is
stored, so a cancelled build sends nothing more and stores nothing. A paid
answer it already had is checkpointed under the request identity, so the
next press of the same input recovers it with no call.

The build runs on its own thread here, as in the app, and the fake author
blocks inside its first request until the test has cancelled. The fake
enters ``model_call`` as a real provider does, so each physical request is
admitted by the build's gate.
"""

from __future__ import annotations

import threading

from learnloop.ai.execution import model_call
from tests.figure_fixtures import (
    EXTRACTION,
    AuthorFake,
    build_figure_vault,
    call,
    context,
    flagship,
    half_density,
    rows,
)

PRESS = {"extractionId": EXTRACTION, "spanIds": ["p3"]}


class _ProviderAuthor(AuthorFake):
    """The author fake, each request admitted like a real provider's."""

    def complete(self, request):
        with model_call(self, purpose=request.purpose, prompt=request.prompt):
            return super().complete(request)


def _blocking_first_answer(entered: threading.Event, release: threading.Event):
    """The first answer fails verification (the build would retry), and is
    returned only once the test releases it."""

    def answer(_context):
        entered.set()
        assert release.wait(30), "the test never released the first answer"
        return half_density()

    return answer


def _press_and_cancel_mid_request(ctx, author: AuthorFake) -> str:
    entered, release = threading.Event(), threading.Event()
    author.answers.insert(0, _blocking_first_answer(entered, release))
    job = call(ctx, "reader.figure_request", PRESS)
    assert job["state"] == "pending"
    assert entered.wait(30), "the build never asked the author"
    cancelled = call(ctx, "reader.figure_job_cancel", {"jobId": job["jobId"]})
    assert cancelled["state"] == "cancelled"
    release.set()
    kept = ctx.figure_jobs.get(job["jobId"])
    assert kept is not None and kept.done.wait(60), "the cancelled build did not end"
    return job["jobId"]


def _threaded_context(root, author):
    ctx = context(root, author=author)
    ctx.library_ask_inline = False  # the build runs as a job on its own thread, as in the app
    return ctx


def test_cancel_before_the_second_attempt_sends_nothing_more_and_stores_nothing(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    author = _ProviderAuthor([half_density()])
    ctx = _threaded_context(paths.root, author)

    job_id = _press_and_cancel_mid_request(ctx, author)

    assert author.calls == 1  # the repair attempt was never sent
    assert rows(repository, "interactive_figures") == []
    assert call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"] == []
    assert call(ctx, "reader.figure_job", {"jobId": job_id})["state"] == "cancelled"
    # The refusal is the gate's, recorded as a hold (the build stopped at its admission).
    with repository.connection() as connection:
        rules = [row[0] for row in connection.execute(
            "SELECT rule FROM decision_records WHERE kind = 'figure_admission'")]
    assert rules == ["held"]


def test_a_cancelled_press_is_recovered_free_by_the_next_press(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    author = _ProviderAuthor([flagship(kind="illustrative")])
    ctx = _threaded_context(paths.root, author)

    _press_and_cancel_mid_request(ctx, author)
    assert author.calls == 1

    again = call(ctx, "reader.figure_request", PRESS)
    kept = ctx.figure_jobs.get(again["jobId"])
    assert kept is not None and kept.done.wait(60)
    done = call(ctx, "reader.figure_job", {"jobId": again["jobId"]})
    assert done["state"] == "done", done
    # The cancelled press's paid first answer came back from its checkpoint;
    # only the repair attempt was asked.
    assert author.calls == 2
    assert author.contexts[1].get("problems_with_the_last_attempt")
    assert done["result"]["figure"]["verification"] == "illustrative"
    assert len(rows(repository, "interactive_figures")) == 1
