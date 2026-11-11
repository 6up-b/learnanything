"""What other test files use from ``tests/test_ad23_inversion.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


HARD = {"complexity": 3, "transfer": "far", "scaffolding": "none", "span": "multi_step",
        "response": "long_constructed", "tools": ["closed_book"]}
ITEMS = ("pi_h", "pi_e1", "pi_e2")
ROUTERS = {"staged": "[router]\nmode = \"staged\"\n", "off": "[router]\nenabled = false\n"}
