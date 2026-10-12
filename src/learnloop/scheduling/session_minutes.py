"""Remembered session minutes (daily-loop DL0, ``spec_daily_loop_v1.md`` §6.6).

Start asks for minutes only, and remembers them: the default is the minutes the
last session was begun with, and 25 on a fresh vault (decision D1). The
learner changes them with one tap on a preset chip. Nothing here is served:
``available_minutes`` reaches the scheduler exactly as before (it only sets
``short_session``), and DL1's daily plan takes over the remembered value.

A client that begins without recording a session (the TUI) passes its own last
choice as ``chosen``; the newer of that choice and the last session wins.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from learnloop.clock import parse_utc

#: The one-tap minute chips on Start (§6.6).
MINUTE_PRESETS: tuple[int, ...] = (10, 15, 25, 40, 60)

#: Minutes on a vault with no session that recorded any (decision D1).
FIRST_RUN_MINUTES = 25

MinutesSource = Literal["last_session", "last_choice", "first_run"]


class _SessionMinutesReader(Protocol):
    def latest_session_minutes(self) -> tuple[int, str] | None: ...


@dataclass(frozen=True)
class RememberedMinutes:
    minutes: int
    source: MinutesSource


@dataclass(frozen=True)
class ChosenMinutes:
    """Minutes a client began with without recording a session (the TUI's Begin)."""

    minutes: int
    #: UTC ISO-8601 time of that Begin.
    chosen_at: str


def remembered_session_minutes(
    repository: _SessionMinutesReader,
    *,
    chosen: ChosenMinutes | None = None,
) -> RememberedMinutes:
    """The minutes Start offers by default.

    The newer of ``chosen`` and the last session's minutes (a tie goes to
    ``chosen``), else D1's 25.
    """

    last = repository.latest_session_minutes()
    if chosen is not None and chosen.minutes > 0:
        if last is None or _not_before(chosen.chosen_at, last[1]):
            return RememberedMinutes(minutes=chosen.minutes, source="last_choice")
    if last is None:
        return RememberedMinutes(minutes=FIRST_RUN_MINUTES, source="first_run")
    return RememberedMinutes(minutes=last[0], source="last_session")


def _not_before(chosen_at: str, started_at: str) -> bool:
    chosen = parse_utc(chosen_at)
    started = parse_utc(started_at)
    return chosen is not None and started is not None and chosen >= started


def minute_choices(remembered: int) -> tuple[int, ...]:
    """The chips to show: the presets plus the remembered value when it isn't one.

    A budget remembered from the old chips (30, 45) stays visible and selected
    rather than silently snapping to a preset the learner never chose.
    """

    return tuple(sorted({*MINUTE_PRESETS, remembered}))


__all__ = [
    "FIRST_RUN_MINUTES",
    "MINUTE_PRESETS",
    "ChosenMinutes",
    "RememberedMinutes",
    "minute_choices",
    "remembered_session_minutes",
]
