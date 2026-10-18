"""Adaptive difficulty (``docs/specs/spec_adaptive_difficulty_v1.md``).

AD1, measure and log (§14; ``docs/reviews/adaptive-difficulty-ad1.md``): no
algorithm successor and nothing served changes. At every plan serve, in the
serve's own transaction, it records the reading opportunities written since
the last sweep (§5.11), the frozen serve inputs of a never-attempted item
(§7.5) and the in-process forecasts of unassisted success (§8.1-8.2); in the
background it runs the outside forecasters and the feature audit (§7.2), and
the practice screen sends the optional rating tap and the first-hint progress
marker with the attempt (§11.2, §12).

Nothing here writes evidence, mastery, facet recall, FSRS or certification
(A2, A12): an import-linter contract keeps the package away from the evidence
writers, and every write goes to AD's own receipts, ``forecast_receipts``,
``judgment_ledger`` or ``practice_item_snapshots``. Replay never reads or
writes any of it and never calls a model (A1).
"""
