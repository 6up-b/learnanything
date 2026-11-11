"""What other test files use from ``tests/test_ro5_stop_coin.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


ARMS_OFF = ("[router_objective]\nstop_coin = 0.0\ncheck_rate = \"off\"\npick_open_share = 0.0\n"
            "fitted_models = false\n")
