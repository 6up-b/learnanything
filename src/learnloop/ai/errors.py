"""Provider-neutral AI error taxonomy with legacy Codex aliases."""


class AIProviderUnavailable(RuntimeError):
    """The selected provider could not produce a usable completion."""


class AIInvalidOutput(AIProviderUnavailable):
    """A provider response failed its declared wire contract after repair."""


class AIInterrupted(AIProviderUnavailable):
    """A LearnLoop-owned provider turn was explicitly interrupted."""


class AITurnTimeout(AIProviderUnavailable, TimeoutError):
    """A provider turn exceeded its wall-clock deadline."""


class VideoGenerationFailed(AIProviderUnavailable):
    """A video-generation job ended in a terminal non-success state."""

    def __init__(
        self,
        message: str,
        *,
        status: str = "failed",
        job_id: str | None = None,
        shot_index: int | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.job_id = job_id
        self.shot_index = shot_index


class VideoGenerationTimeout(AITurnTimeout):
    """A storyboard did not finish within its wall-clock budget."""


# Compatibility names.  Aliases (rather than subclasses) preserve exception
# identity and make every existing ``except CodexUnavailable`` catch the new
# provider-neutral subclasses.
CodexUnavailable = AIProviderUnavailable
CodexInterrupted = AIInterrupted
CodexTurnTimeout = AITurnTimeout

__all__ = [
    "AIInterrupted",
    "AIInvalidOutput",
    "AIProviderUnavailable",
    "AITurnTimeout",
    "VideoGenerationFailed",
    "VideoGenerationTimeout",
    "CodexInterrupted",
    "CodexTurnTimeout",
    "CodexUnavailable",
]
