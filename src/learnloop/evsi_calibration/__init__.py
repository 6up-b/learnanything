"""EVSI/EIG calibration (owner question 2026-10-12): measure instead of assume.

Value of information is about to become the only limit on probes and
follow-ups, so the numbers it runs on must be measured where they can be and
labelled honestly where they cannot. This package holds the two read-only
halves of that work:

* **Part A, offline** (:mod:`.eedi`, :mod:`.response_fit`, :mod:`.world`,
  :mod:`.policies`, :mod:`.simulate`): simulated learners whose misconceptions
  come from Eedi's distractor -> misconception labels (2024 Kaggle release)
  answer Eedi questions under a response model fitted to Eedi's real answer
  patterns (NeurIPS 2020 release). The real EIG and EVSI selectors
  (:func:`learnloop.diagnosis.robust_composition.evaluate_selection`,
  :func:`learnloop.scheduling.evsi.rank_feasible`) choose the checks; the
  harness scores their forecasts against what the simulated learner did.
  ``learnloop evsi simulate``.
* **Part B, live** (:mod:`.live_report`): the calibration report over the
  ``voi_forecasts`` receipts that every live value-of-information decision
  writes (:mod:`learnloop.scheduling.voi_forecasts`), joined to realized
  outcomes and to later truth. ``learnloop evsi calibration``.

Nothing here serves, schedules or writes vault state. Only the CLI imports it.
"""
