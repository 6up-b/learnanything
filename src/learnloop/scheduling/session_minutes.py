"""Remembered session minutes (daily-loop DL0, ``spec_daily_loop_v1.md`` §6.6).

Start asks for minutes only, and remembers them: the default is the minutes the
last session was begun with, and 25 on a fresh vault (decision D1). The
learner changes them with one tap on a preset chip. Nothing here is served:
``available_minutes`` reaches the scheduler exactly as before (it only sets
``short_session``), and DL1's daily plan takes over the remembered value.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

#: The one-tap minute chips on Start (§6.6).
MINUTE_PRESETS: tuple[int, ...] = (10, 15, 25, 40, 60)

#: Minutes on a vault with no session that recorded any (decision D1).
FIRST_RUN_MINUTES = 25

MinutesSource = Literal["last_session", "first_run"]


class _SessionMinutesReader(Protocol):
    def latest_session_available_minutes(self) -> int | None: ...


@dataclass(frozen=True)
class RememberedMinutes:
    minutes: int
    source: MinutesSource


def remembered_session_minutes(repository: _SessionMinutesReader) -> RememberedMinutes:
    """The minutes Start offers by default: the last session's, else D1's 25."""

    last = repository.latest_session_available_minutes()
    if last is None:
        return RememberedMinutes(minutes=FIRST_RUN_MINUTES, source="first_run")
    return RememberedMinutes(minutes=last, source="last_session")


def minute_choices(remembered: int) -> tuple[int, ...]:
    """The chips to show: the presets plus the remembered value when it isn't one.

    A budget remembered from the old chips (30, 45) stays visible and selected
    rather than silently snapping to a preset the learner never chose.
    """

    return tuple(sorted({*MINUTE_PRESETS, remembered}))


__all__ = [
    "FIRST_RUN_MINUTES",
    "MINUTE_PRESETS",
    "RememberedMinutes",
    "minute_choices",
    "remembered_session_minutes",
]
