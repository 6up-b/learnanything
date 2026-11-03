"""Data capture: what later evaluation needs, recorded now (owner, 2026-11-02).

The owner's long-horizon target is delayed cold performance and time to goal, with a dataset
that can test policy offline and optimize online by the goal's end. Data not logged cannot be
recovered, so this stage records it. It builds no planner, valuator or new policy:

* :mod:`~learnloop.data_capture.gates`: its two switches;
* :mod:`~learnloop.data_capture.prefilter`: what was decided before the router saw candidates,
  linked into each committed decision (A1).

This package is a leaf (the stores and the version gates only): every serving package may read
it. The rest lives where its reads do: the shared delayed-completion definition
(:mod:`learnloop.delayed_completion`, A4), the frozen objective and its measurement
(:mod:`learnloop.daily_plan.measurement`, A2), the first-delayed-success proxy
(:mod:`learnloop.diagnosis.first_delayed_success`, A3) and the read-only report
(:mod:`learnloop.ops.capture_report`).
"""
