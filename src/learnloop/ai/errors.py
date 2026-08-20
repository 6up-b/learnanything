"""Provider-neutral AI error taxonomy with legacy Codex aliases."""


class AIProviderUnavailable(RuntimeError):
    """The selected provider could not produce a usable completion."""


class AIInvalidOutput(AIProviderUnavailable):
    """A provider response failed its declared wire contract after repair."""


class AIInterrupted(AIProviderUnavailable):
    """A LearnLoop-owned provider turn was explicitly interrupted."""


class AITurnTimeout(AIProviderUnavailable, TimeoutError):
    """A provider turn exceeded its wall-clock deadline."""


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
    "CodexInterrupted",
    "CodexTurnTimeout",
    "CodexUnavailable",
]
