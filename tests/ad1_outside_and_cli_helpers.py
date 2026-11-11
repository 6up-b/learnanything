"""What other test files use from ``tests/test_ad1_outside_and_cli.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from tests.ad_fakes import ForecastLLM


class MeteredLLM(ForecastLLM):
    provider_name = "fake_metered"
    provider_type = "openrouter"
