"""AD's failure log lines (the final round, owner decision 2026-10-24, Q3).

A failure inside AD, or at its boundary with the view and the predicate, can carry what the failing
code read (held-out text in a JSON error, a row in a traceback's frame). At the default level a line
names only the failure's type; the traceback is written only at DEBUG."""

from __future__ import annotations

import logging
import sys
from typing import Any


def warn_failure(logger: logging.Logger, message: str, *args: Any) -> None:
    """Log the exception being handled: its type at WARNING, the traceback at DEBUG."""

    exc = sys.exc_info()[1]
    name = type(exc).__name__ if exc is not None else "unknown"
    logger.warning(message + " (%s)", *args, name)
    logger.debug(message, *args, exc_info=True)


__all__ = ["warn_failure"]
