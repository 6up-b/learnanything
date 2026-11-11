"""What other test files use from ``tests/test_rw2c_fix_round2.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


class _Spans:
    """T6's ``TutorSpanProvider`` faked: verified picks named by the manifest's
    ``span_keys`` and, optionally, referenced blocks appended after them."""

    def __init__(self, verified, referenced=()):
        self.verified = [dict(span) for span in verified]
        self.referenced = [dict(span, relation="referenced") for span in referenced]
        self.calls = 0

    def __call__(self, vault, repository, *, context, question_md, learning_object_ids, item):
        self.calls += 1
        return self.verified + self.referenced, {
            "basis": "retrieved_verified",
            "span_keys": [f"{span['extraction_id']}/{span['span_id']}" for span in self.verified]}


def _span(span_id, extraction_id="ext", **extra):
    return {"span_id": span_id, "extraction_id": extraction_id, "label": f"Book · §{span_id}", "text": "a step",
            **extra}
