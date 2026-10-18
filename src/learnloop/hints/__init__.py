"""Adaptive hints (spec_adaptive_hints_v1).

H0 holds only the telemetry (:mod:`learnloop.hints.telemetry`) and its
descriptive report (:mod:`learnloop.hints.report`). Hints are help, never
evidence (standing constraint H1): this package imports no evidence writer
(import-linter contract ``hints-never-write-evidence``, G-H13).
"""
