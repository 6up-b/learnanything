"""Waiting on the terminal app's background work in a test.

A TUI test must wait for the work it reads, not for a number of pauses: the feedback screen grades
in a worker (``FeedbackScreen.auto_submit_ai`` on ``asyncio.to_thread``), so how many event-loop
pauses grading takes depends on the machine's load (refactor bug ledger D-13: a fixed ten pauses
failed in loaded gate runs).
"""

from __future__ import annotations

import asyncio

#: A generous ceiling for a fake grading round trip; a test that hits it fails with its own message
#: instead of hanging the run.
GRADING_SECONDS = 60.0


async def wait_for_feedback_result(pilot, feedback, *, seconds: float = GRADING_SECONDS):
    """Wait until ``feedback`` has a result or its workers have all finished, then let the screen
    settle. Returns ``feedback.result`` (``None`` when grading finished without one)."""

    loop = asyncio.get_running_loop()
    deadline = loop.time() + seconds
    while feedback.result is None:
        mine = [worker for worker in feedback.app.workers if worker.node is feedback]
        if mine and all(worker.is_finished for worker in mine):
            break
        if loop.time() > deadline:
            raise AssertionError(f"the feedback screen's grading did not finish within {seconds:.0f} s")
        pending = [worker for worker in mine if not worker.is_finished]
        if pending:
            # The grading worker exists: wait on it (its errors surface below as no result).
            await asyncio.wait({asyncio.ensure_future(_finished(worker)) for worker in pending},
                               timeout=max(0.0, deadline - loop.time()))
        else:
            # Not started yet (the screen's on_mount starts it): let the app process its messages.
            await pilot.pause()
    await pilot.pause()
    return feedback.result


async def _finished(worker) -> None:
    try:
        await worker.wait()
    except Exception:  # noqa: BLE001 - a failed or cancelled grading shows as no result
        pass
