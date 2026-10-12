"""Slice 2 T4: contamination detectors as shadow flags (spec §7).

The lexical floor in ``practice_leakage``, ``tutor_qa`` and ``reader_dialogue``
keeps every live decision. This package widens what is checked, offline and on
the owner's command: stored embeddings shortlist by rank, a symbolic check
covers math answers, and an LLM judge (or the verifier, or the owner) decides.
Flags propose reserve burns, reveal debits and item reviews; nothing here
executes them, calls an embedding provider, or changes what is served.
"""
from learnloop.ops.contamination.recipes import CONTAMINATION_RECIPES
from learnloop.ops.contamination.report import REPORT_VERSION, contamination_report

__all__ = ["CONTAMINATION_RECIPES", "REPORT_VERSION", "contamination_report"]
