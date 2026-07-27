"""In-process background grading for durable practice-exam answers.

The answer itself is persisted before a worker starts, so a process exit loses
at most the in-flight model call, never the learner's response.  A later exam
resume or finish can schedule the still-ungraded row again.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

LOG = logging.getLogger(__name__)

ExamGradingKey = tuple[str, str]


class ExamGradingManager:
    """Own daemon grading workers and make scheduling idempotent per exam item."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # A learner can answer faster than a model grades. Bound provider work
        # so one exam cannot fan out an unbounded number of model processes.
        self._worker_slots = threading.BoundedSemaphore(value=2)
        self._active: dict[ExamGradingKey, threading.Thread] = {}
        self._errors: dict[ExamGradingKey, Exception] = {}

    def submit(
        self,
        session_id: str,
        practice_item_id: str,
        work: Callable[[], None],
    ) -> bool:
        """Start ``work`` unless this item already has an active worker."""

        key = (session_id, practice_item_id)
        with self._lock:
            active = self._active.get(key)
            if active is not None and active.is_alive():
                return False
            self._errors.pop(key, None)
            thread = threading.Thread(
                target=self._run,
                args=(key, work),
                name=f"learnloop-exam-grade-{practice_item_id}",
                daemon=True,
            )
            self._active[key] = thread
            thread.start()
        return True

    def _run(self, key: ExamGradingKey, work: Callable[[], None]) -> None:
        try:
            with self._worker_slots:
                work()
        except Exception as exc:  # noqa: BLE001 - retained for finish-time retry
            LOG.exception(
                "background exam grading failed",
                extra={"session_id": key[0], "practice_item_id": key[1]},
            )
            with self._lock:
                self._errors[key] = exc
        finally:
            with self._lock:
                current = self._active.get(key)
                if current is threading.current_thread():
                    self._active.pop(key, None)

    def wait_for_session(self, session_id: str) -> None:
        """Join every worker currently grading an answer in ``session_id``."""

        while True:
            with self._lock:
                threads = [
                    thread
                    for (active_session_id, _), thread in self._active.items()
                    if active_session_id == session_id
                ]
            if not threads:
                return
            for thread in threads:
                thread.join()

    def pop_error(
        self, session_id: str, practice_item_id: str
    ) -> Exception | None:
        with self._lock:
            return self._errors.pop((session_id, practice_item_id), None)

    def shutdown(self) -> None:
        """Give active workers a short grace period; they are daemon threads."""

        with self._lock:
            threads = list(self._active.values())
        for thread in threads:
            thread.join(timeout=2)
