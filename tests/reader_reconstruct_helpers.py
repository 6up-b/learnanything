"""What other test files use from ``tests/test_reader_reconstruct.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.reader import reader_quick_check as RQC
from learnloop.reader.ai_contracts import ReadingActiveCheck

from tests.helpers import NOW
from tests.reader_active_reading_helpers import ActiveClient


CLOCK = FrozenClock(NOW)
LO = "lo_svd_definition"


def _reconstruct(repo):
    client = ActiveClient(ReadingActiveCheck(question_md="Derive the SVD's form without looking at the book.",
                                             span_ids=["s1"]))
    return RQC.author_selection_question(repo, client, extraction_id="ext1", anchor_span_ids=["s1", "s2"],
                                         style="reconstruct", clock=CLOCK, owner="job_r")
