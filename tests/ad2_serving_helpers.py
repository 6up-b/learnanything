"""What other test files use from ``tests/test_ad2_serving.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from typing import Any

from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import LO, set_item


HARD = {"complexity": 3, "transfer": "far", "scaffolding": "none", "span": "multi_step",
        "response": "long_constructed", "tools": ["closed_book"]}


def _generation_prompt(paths) -> tuple[Any, str]:
    from learnloop.content.authoring.practice_generation import (
        _practice_expansion_instructions,
        build_practice_expansion_plan,
    )

    vault = load_vault(paths.root)
    plan = build_practice_expansion_plan(vault, Repository(paths.sqlite_path), learning_object_ids=[LO],
                                         require_completed_probe=False)
    return plan, _practice_expansion_instructions(plan, extra_instructions=None)


def _land(paths, item_id: str, features: dict, at: str, *, capability: str, **extra: Any) -> None:
    """A generated item landing for the commission's cell (a copy of the LO's item at ``features``)."""

    import yaml

    from tests.ad_fakes import stamp_task_features
    from tests.helpers import write_yaml

    payload = yaml.safe_load(paths.practice_item_path("linear-algebra", "pi_g1").read_text(encoding="utf-8"))
    payload.update({"id": item_id, "created_at": at, "updated_at": at, "prompt": f"Question {item_id}."})
    write_yaml(paths.practice_item_path("linear-algebra", item_id), payload)
    stamp_task_features(paths, item_id, features, difficulty_source="llm_estimate", **extra)
    set_item(paths, item_id, capability=capability)
