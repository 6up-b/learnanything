"""Diagnosis history modes and defaults (Slice 1 §5.2, §12).

M1 takes these as command options; M2's ``[diagnosis]`` config section maps
onto :class:`DiagnosisSettings` unchanged, so the defaults live in one place.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

HistoryMode = Literal["exact", "full", "snapshot", "hybrid"]
HISTORY_MODES: tuple[str, ...] = ("exact", "full", "snapshot", "hybrid")

#: Prompt identity of the diagnoser (receipts and judgment rows carry it).
DIAGNOSIS_PROMPT_VERSION = "diagnosis-v1-split"
#: Identity of the context assembly rules; part of every context hash.
DIAGNOSIS_CONTEXT_VERSION = "diagnosis-context-v1"
#: Proposal schema identity.
DIAGNOSIS_OUTPUT_SCHEMA_VERSION = "diagnosis_proposal_v1"


@dataclass(frozen=True)
class DiagnosisSettings:
    """§12 ``[diagnosis]`` defaults. ``history_mode`` defaults to ``full`` (O16)."""

    history_mode: HistoryMode = "full"
    full_history_token_budget: int = 100_000
    history_error_limit: int = 6
    history_success_limit: int = 4
    #: Fixed budget for ``exact``/``hybrid`` (and snapshot's inline part).
    exact_history_token_budget: int = 12_000
    sample_count: int = 1
    correct_answer_sample_rate: float = 0.0
    #: Hybrid: kNN shortlist size and the fused top-N kept per block.
    knn_limit: int = 8
    hybrid_keep: int = 6
    rrf_k: int = 60

    def __post_init__(self) -> None:
        if self.history_mode not in HISTORY_MODES:
            raise ValueError(f"unknown diagnosis history mode {self.history_mode!r}")
        for name in (
            "full_history_token_budget",
            "history_error_limit",
            "history_success_limit",
            "exact_history_token_budget",
            "knn_limit",
            "hybrid_keep",
            "rrf_k",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        if self.sample_count < 1:
            raise ValueError("sample_count must be at least 1")
        if not 0.0 <= self.correct_answer_sample_rate <= 1.0:
            raise ValueError("correct_answer_sample_rate must be in [0, 1]")

    def with_mode(self, mode: HistoryMode) -> "DiagnosisSettings":
        return replace(self, history_mode=mode)


__all__ = [
    "DIAGNOSIS_CONTEXT_VERSION",
    "DIAGNOSIS_OUTPUT_SCHEMA_VERSION",
    "DIAGNOSIS_PROMPT_VERSION",
    "HISTORY_MODES",
    "DiagnosisSettings",
    "HistoryMode",
]
