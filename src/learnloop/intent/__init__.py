"""Daily-loop DL2: the single intent control (``spec_daily_loop_v1.md`` §5).

Commitments carry intent; goals are optional deadlines on top. This package
writes commitments through ``learnloop.curriculum.commitments`` for the control
(``control``), deadlines (``deadline``) and settled checks (``checks``), and
reports on them (``report``). What serving reads lives below it, in
``learnloop.scheduling.intent`` (the scheduler imports that, never this).

Nothing here is evidence: ``due_at`` keeps being written at 0.90, recall
targets scale an effective due at serving time only, and replay never reads
intent. The plan's projected-cost function (``daily_plan.intent_cost``) is
handed to the control, so this package never imports the plan.
"""
