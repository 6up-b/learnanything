"""What other test files use from ``tests/test_ux_phase1_auto_build.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.content.pipeline.jobs import DurableIngestJobs

from tests.ux_phase1_support import CLOCK, repository


def _jobs(root, services):
    repo = repository(root)
    jobs = DurableIngestJobs()
    jobs.bind(repo, root, background=False, clock=CLOCK, services=services)
    return repo, jobs
