"""Daily-loop DL2: intent at serving time (``spec_daily_loop_v1.md`` §5.3).

What the scheduler and the plan read: the vocabulary (``model``), the
most-recent-choice resolution (``resolution``), per-intent recall targets and
the anchor rule (``recall_targets``), and the per-build view (``serving``).
Read-only over the commitment tables; the control that writes commitments is
``learnloop.intent`` (above scheduling). Nothing here is evidence.
"""
