"""Synthetic-student simulation harness for the LearnLoop belief pipeline.

Generates attempts from parameterized synthetic students *through the real
pipeline* (``serve_due_queue`` -> ``apply_attempt`` -> follow-up gate) so the
team can test identifiability of planted misconceptions, measure
belief-vs-truth accuracy, and discover which config parameters actually change
scheduling decisions before spending scarce real-learner data on them.
"""

from learnloop.sim.profiles import BUILTIN_PROFILES, load_profile
from learnloop.sim.runner import SimReport, run_simulation
from learnloop.sim.sweep import run_sweep

__all__ = [
    "BUILTIN_PROFILES",
    "load_profile",
    "SimReport",
    "run_simulation",
    "run_sweep",
]
