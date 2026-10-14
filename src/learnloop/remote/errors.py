"""Refusals a remote frontend may show the host verbatim (spec_mcp_frontend_c1 §4).

Only these carry their message to a chat host; any other exception is an
internal failure, reported as one generic line (no internal text leaves).
"""

from __future__ import annotations


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


__all__ = ["InvalidRequest", "NotFound", "RemoteRequestError"]
