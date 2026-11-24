"""What the probe router's tests and the tests it moves to its predecessor share (a test file never imports another,
``tests/test_test_layout.py``)."""

from __future__ import annotations

from learnloop.algorithm_versions import PROBE_ROUTER_ALGORITHM_VERSION, SUCCESSOR_CHAIN

#: The tag just below the probe router's, computed from the chain so a renumber needs no edit here. Tests whose subject
#: is the automatic lane as it asked its probe (the decision, the written question, its admission, serving and
#: receipts) build there: from the probe router's tag a probe the router cannot value is asked only by the probe coin,
#: which ``tests/test_probe_router.py`` covers.
BEFORE_PROBE_ROUTER = SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(PROBE_ROUTER_ALGORITHM_VERSION) - 1]
