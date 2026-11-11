"""What other test files use from ``tests/test_discriminating_search.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from dataclasses import dataclass

from learnloop.instructional.discriminating import make_valuer


@dataclass
class _Estimate:
    minutes: float

    def as_dict(self):
        return {"minutes": self.minutes, "prior_source": "test"}


def estimator(item_id, mode, expected):
    return _Estimate(12.0 if mode == "proof" else 2.0)


def _valuer(llm):
    return make_valuer(estimator=estimator, screen_client=llm, judge_client=llm)
