"""T6's suites on the shared compare harness (Slice 2 §4): the consumer's seam.

``learnloop embeddings compare`` is the composition root: it calls
``register_suites(SUITES, role_tasks=ROLE_TASKS)`` before ``run_compare``, which
adds the ``source_retrieval`` report and benchmark ``b4``, and maps their LLM
roles to T6's routes. Idempotent; Phase 5a's suites and roles are untouched.
"""
from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

from learnloop.source_retrieval.b4 import B4Suite
from learnloop.source_retrieval.bench import T6_ROLE_TASKS
from learnloop.source_retrieval.evaluation import SourceRetrievalSuite


def register_suites(suites: MutableMapping[str, Any], *, role_tasks: MutableMapping[str, str]) -> None:
    for suite in (SourceRetrievalSuite(), B4Suite()):
        existing = suites.get(suite.name)
        if existing is not None and type(existing) is not type(suite):
            raise ValueError(f"suite {suite.name!r} is already registered by another consumer")
        suites.setdefault(suite.name, suite)
    for role, task in T6_ROLE_TASKS.items():
        if role_tasks.get(role, task) != task:
            raise ValueError(f"role {role!r} is already mapped to {role_tasks[role]!r}")
        role_tasks[role] = task


__all__ = ["register_suites"]
