"""Adaptive hints (spec_adaptive_hints_v1).

H0: the telemetry (:mod:`learnloop.hints.telemetry`) and its descriptive
report (:mod:`learnloop.hints.report`). H1: approach maps
(:mod:`learnloop.hints.maps`, :mod:`learnloop.hints.map_seeds`,
:mod:`learnloop.hints.map_builder`, :mod:`learnloop.hints.map_report`). H2a:
the hint service (:mod:`learnloop.hints.service`, ``request_hint``) with its
kinds and labels (:mod:`learnloop.hints.kinds`), state
(:mod:`learnloop.hints.state`), options (:mod:`learnloop.hints.options`),
chooser (:mod:`learnloop.hints.chooser`), writer
(:mod:`learnloop.hints.writer`), contracts (:mod:`learnloop.hints.contracts`)
and discriminating questions (:mod:`learnloop.hints.discriminating`).

Hints are help, never evidence (standing constraint H1): this package imports
no evidence writer (import-linter contract ``hints-never-write-evidence``,
G-H13); a shown hint reaches the attempt only through the sidecar's submit
fold (``hints_used``, ``primed``) and its delivery's reveal, with their
existing meaning (§5).
"""
