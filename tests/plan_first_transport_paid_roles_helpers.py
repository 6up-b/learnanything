"""What other test files use from ``tests/test_plan_first_transport_paid_roles.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, get_args

import pytest
import tomlkit

from learnloop.ai import plan_fallback
from learnloop.ai.routing import AITask, DECIDER_TASKS, provider_for_task

from tests.helpers import create_basic_vault


TASKS: tuple[str, ...] = get_args(AITask)
#: Tasks pinned by construction (provider_for_task returns an explicit selection).
PINNED_BY_CONSTRUCTION = frozenset({"embedding", "field_question_classifier"}) | DECIDER_TASKS
#: The tasks main added after T1's base (55063be64) ride these existing tasks:
#: RW2c's comparison lines on CheckRoute (workbench_check), its example
#: search on the source-retrieval roles, RW5a's figures on figure_author.
MAIN_FEATURE_TASKS = ("workbench_check", "source_query_rewrite", "source_rerank", "figure_author")


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    for name in ("LEARNLOOP_AI_PROVIDER", "LEARNLOOP_AI_FALLBACK", "OPENROUTER_API_KEY", "OPENAI_API_KEY",
                 "DEEPSEEK_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    plan_fallback.revoke_all()
    yield
    plan_fallback.revoke_all()


#: The action each test's resolutions run as (redesign D: a grant names the action that asked).
LEARNER = "test.learner_request"


@pytest.fixture(autouse=True)
def learner_request():
    """Each test resolves routes as one request of action ``LEARNER`` does (the
    sidecar's dispatch opens ``plan_fallback.request`` per RPC): a grant counts
    only in a request of the granted action, or in a unit it created
    (tests/test_plan_first_transport_offer_grants.py pins the property)."""

    with plan_fallback.request(None, LEARNER):
        yield


def _priced_vault(tmp_path: Path) -> Path:
    """A vault with every feature price set, so no task's offer is blocked (review F2)."""

    root = tmp_path / "vault"
    create_basic_vault(root)
    path = root / "learnloop.toml"
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    for dotted in sorted(set(plan_fallback.METERED_PRICE_SETTINGS.values())):
        table: Any = document
        *parents, leaf = dotted.split(".")
        for part in parents:
            if part not in table:
                table[part] = tomlkit.table()
            table = table[part]
        table[leaf] = 1.0
    path.write_text(tomlkit.dumps(document), encoding="utf-8")
    return root


def _routed_tasks(config) -> list[str]:
    tasks = [task for task in TASKS if not provider_for_task(config, task).explicit]  # type: ignore[arg-type]
    assert set(TASKS) - set(tasks) == PINNED_BY_CONSTRUCTION
    assert set(MAIN_FEATURE_TASKS) <= set(tasks)
    return tasks
