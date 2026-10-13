"""Compatibility exports for the shared AI spend adapter.

Tier-1 judgments reuse this accounting outside diagnosis. The implementation
lives below the domain packages to avoid a diagnosis/content dependency cycle.
"""
from learnloop.ai.review_spend import *  # noqa: F403
from learnloop.ai.review_spend import __all__
