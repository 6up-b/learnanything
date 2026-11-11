"""What other test files use from ``tests/test_intent_fix_round4.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.scheduling import scheduler
from learnloop.vault.yaml_io import read_yaml, write_yaml


def _as_teach_back(root, item_id):
    path = next(root.rglob(f"{item_id}.yaml"))
    payload = read_yaml(path)
    payload["practice_mode"] = "teach_back"
    payload["attempt_types_allowed"] = ["teach_back"]
    write_yaml(path, payload)


def _never_worth_its_minutes(monkeypatch):
    """Every teach-back's value of information below its minutes (the
    verify's 12.95 value-minutes against 15 cost-minutes, on every build)."""

    monkeypatch.setattr(scheduler, "_teach_back_value_admission", lambda *args, **kwargs: (frozenset(), []))
