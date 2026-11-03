"""Data capture: what later evaluation needs, recorded now (owner, 2026-11-02).

The owner's long-horizon target is delayed cold performance and time to goal,
with a dataset that can test policy offline and optimize online by the goal's
end. Data not logged cannot be recovered, so this package records it. It builds
no planner, valuator or new policy:

* :mod:`~learnloop.data_capture.prefilter`: what was decided before the router saw
  candidates, linked into each committed decision (A1);
* :mod:`~learnloop.data_capture.objectives`: the objective a decision's arms are
  evaluated on, frozen before the draw, and its measurement's states (A2);
* :mod:`~learnloop.data_capture.first_delayed_success`: the first-delayed-success
  proxy: calendar time and recorded minutes, with coverage (A3);
* :mod:`~learnloop.data_capture.report`: the read-only report of it all.

The shared delayed-completion definition (A4) is the leaf module
:mod:`learnloop.delayed_completion`.
"""
