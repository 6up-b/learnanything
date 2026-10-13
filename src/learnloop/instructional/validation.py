"""Post-import validation of an authored exercise against its request (spec §8.1).

The implementation lives in ``learnloop.content.authoring.draft_validation``
so the interactive import job can validate a learner's pick against its
proposal (Codex re-review F7).
"""
from __future__ import annotations

from learnloop.content.authoring.draft_validation import draft_validator

__all__ = ["draft_validator"]
