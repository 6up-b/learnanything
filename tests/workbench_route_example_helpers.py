"""What other test files use from ``tests/test_workbench_route_example.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from types import SimpleNamespace

from learnloop.source_retrieval.policy import derive_policy


ROUTE = {"span_id": "w2", "extraction_id": "ext", "source_title": "Book A", "section": "3.4", "page": 41,
         "text": "Example 3.4: take the CDF first, then read the boundary.", "role": "worked_example",
         "verdict": "follows_learner_route"}
OTHER = {"span_id": "w1", "extraction_id": "ext", "source_title": "Book A", "section": "3.2", "page": 39,
         "text": "Example 3.2: integrate the density directly.", "role": "worked_example",
         "verdict": "worked_example"}


class FindFake:
    """``find_sources(intent="worked_example")``, faked at the Reader's seam."""

    def __init__(self, hits, status="verified"):
        self.hits = hits
        self.status = status
        self.calls = []

    def __call__(self, vault, repository, query, *, caller, learner_work_md, owner_id):
        self.calls.append({"query": query, "caller": caller, "learner_work_md": learner_work_md,
                           "owner_id": owner_id})
        policy, _reason = derive_policy(caller)
        return SimpleNamespace(hits=[dict(hit) for hit in self.hits], policy=policy, status="ok",
                               manifest={"verification": {"status": self.status}, "policy": policy})
