"""Daily-loop DL1: the finite daily plan (``docs/specs/spec_daily_loop_v1.md`` §6, §7).

Today serves N remembered minutes, split by the system across repair,
maintain, new and push, chosen block by block through the §6.8 source/chooser
interface, done when done, with "keep going". It is live at algorithm version
``mvp-0.14`` (``daily_plan_v1``) and later (``DAILY_PLAN_VERSIONS``), behind
``plan.enabled``. It changes
what is served, never what is evidence: estimates, splits and plan rows never
write evidence, mastery, certification, coldness or FSRS state, and replay
never reads them.

This package is a leaf consumer: nothing in the domain below imports it.
"""
