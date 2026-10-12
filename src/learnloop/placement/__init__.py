"""Learner field F2: starting new material without ceremony (spec §5.2).

Placement consumes the active learner predictor only through the
``LearnerPredictor`` contract (G10) and writes only its own receipts: never
grading evidence, mastery, facet state, certification, coldness or FSRS state.
It is live at algorithm version ``mvp-0.10`` behind ``placement.enabled``.
"""
