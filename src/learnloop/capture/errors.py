"""Stable domain errors shared by the HTTP, CLI and desktop adapters."""


class CaptureError(ValueError):
    def __init__(self, code: str, status: int, message: str):
        super().__init__(message)
        self.code = code
        self.status = status
        self.message = message
        self.retryable = status in (429, 503)
