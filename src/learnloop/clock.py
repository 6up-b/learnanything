from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        """Return an aware UTC datetime."""


@dataclass(frozen=True)
class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


@dataclass(frozen=True)
class FrozenClock:
    instant: datetime

    def now(self) -> datetime:
        if self.instant.tzinfo is None:
            return self.instant.replace(tzinfo=UTC)
        return self.instant.astimezone(UTC)


def utc_now_iso(clock: Clock | None = None) -> str:
    current = (clock or SystemClock()).now()
    return current.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
