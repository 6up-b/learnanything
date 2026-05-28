from __future__ import annotations

import logging
import os
import sys
import warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Reserved LogRecord attribute that carries structured event fields. Handlers
# emit it as a nested ``data`` object so debug events stay machine-parseable.
EVENT_FIELDS_ATTR = "event_fields"

LOG = logging.getLogger("learnloop.sidecar")

_TRUTHY = {"1", "true", "yes", "on", "debug"}


class JsonLineFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        import json

        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "level": record.levelname.lower(),
            "event": record.getMessage(),
        }
        fields = getattr(record, EVENT_FIELDS_ATTR, None)
        if isinstance(fields, dict) and fields:
            payload["data"] = fields
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def debug_enabled() -> bool:
    """True when the sidecar should emit verbose state-update events.

    Enabled by ``LEARNLOOP_SIDECAR_DEBUG`` (truthy) or by setting
    ``LEARNLOOP_SIDECAR_LOG_LEVEL=DEBUG``.
    """

    if os.environ.get("LEARNLOOP_SIDECAR_DEBUG", "").strip().lower() in _TRUTHY:
        return True
    return os.environ.get("LEARNLOOP_SIDECAR_LOG_LEVEL", "").strip().upper() == "DEBUG"


def _resolve_level() -> int:
    if debug_enabled():
        return logging.DEBUG
    name = os.environ.get("LEARNLOOP_SIDECAR_LOG_LEVEL", "INFO").strip().upper()
    return getattr(logging, name, logging.INFO)


def configure_logging() -> None:
    formatter = JsonLineFormatter()
    handlers: list[logging.Handler] = []

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    handlers.append(stderr_handler)

    # Tauri can swallow sidecar stderr, so allow tee-ing the JSONL stream to a
    # file for after-the-fact inspection of state updates.
    file_path = os.environ.get("LEARNLOOP_SIDECAR_DEBUG_LOG", "").strip()
    if file_path:
        try:
            path = Path(file_path).expanduser()
            path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(path, encoding="utf-8")
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        except OSError as exc:  # pragma: no cover - defensive, never fatal
            LOG.warning("debug log file unavailable: %s", exc)

    level = _resolve_level()
    root = logging.getLogger()
    root.handlers[:] = handlers
    root.setLevel(level)
    warnings.showwarning = _show_warning


def log_event(event: str, *, level: int = logging.DEBUG, **fields: Any) -> None:
    """Emit a structured sidecar event.

    ``event`` is the short message; ``fields`` are serialized under ``data``.
    Defaults to DEBUG so it is silent unless debug logging is enabled.
    """

    if not LOG.isEnabledFor(level):
        return
    LOG.log(level, event, extra={EVENT_FIELDS_ATTR: {k: v for k, v in fields.items() if v is not None}})


def _show_warning(message, category, filename, lineno, file=None, line=None) -> None:
    logging.getLogger("warnings").warning(
        "%s:%s:%s:%s",
        filename,
        lineno,
        category.__name__,
        message,
    )
