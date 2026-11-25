"""Refusals a remote frontend may show the host verbatim (spec_mcp_frontend_c1 §4).

Only these carry their message to a chat host; any other exception is an
internal failure, reported as one generic line (no internal text leaves).
"""

from __future__ import annotations

from learnloop.db import writer_fence


class RemoteRequestError(Exception):
    """A request LearnLoop refuses, with a learner-readable reason."""

    code = "invalid_request"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code


class NotFound(RemoteRequestError):
    code = "not_found"


class InvalidRequest(RemoteRequestError):
    code = "invalid_request"


#: The writer fence's refusal, for an adapter that may not import the database layer (a ``BaseException``).
FenceRefusal = writer_fence.WriterFenceRefusal


def upgraded_while_open(error: BaseException) -> RemoteRequestError | None:
    """The refusal to show for a write the writer fence refused (``learnloop.db.writer_fence``): the vault was
    upgraded after this request loaded it, nothing was saved, and the next request loads it again. None for any other
    error."""

    if not writer_fence.is_refusal(error):
        return None
    return RemoteRequestError(
        "LearnLoop was upgraded while this request ran, so nothing was saved. Try again.",
        code="vault_upgraded_while_open",
    )


__all__ = ["FenceRefusal", "InvalidRequest", "NotFound", "RemoteRequestError", "upgraded_while_open"]
