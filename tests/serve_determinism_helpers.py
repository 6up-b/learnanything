"""One served day at the head, run in a process of its own, for ``tests/test_serve_tie_breaks.py``.

Run as ``python -m tests.serve_determinism_helpers ROOT OUT [--reverse-unordered-selects]``: it builds the router
mixture's wide vault under ROOT, serves and answers the day (the staged pick inside the objective, the decisions'
measurements with their delayed-check picks), and writes to OUT every staged pick, every served step and every
measurement pick's chosen item. Seeded draws are pinned as in the parent test (``tests/pinned_draws.py``, by the
parent's node id), so what is left to differ between two runs is anything run-specific that decides: the process's
hash seed (set by the parent), a fresh id or an instant used as a tie-break, or row order from a query with no
``ORDER BY`` (``--reverse-unordered-selects`` turns on SQLite's pragma of that name on every connection).
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

QUIET = "[router_objective]\nstop_coin = 0.0\n"


def _reverse_unordered_selects() -> None:
    real = sqlite3.connect

    def connect(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        connection = real(*args, **kwargs)
        connection.execute("PRAGMA reverse_unordered_selects = ON")
        return connection

    sqlite3.connect = connect  # type: ignore[assignment]


def served_day(root: Path) -> dict[str, Any]:
    import pytest

    from learnloop import delayed_checks
    from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
    from learnloop.daily_plan.staged_frame import StagedChooser
    from tests import pinned_draws
    from tests import router_mixture_helpers as RMH
    from tests.ih4_preferences_inform_router_helpers import _pin
    from tests.router_model_fakes import fake_runtime

    pinned_draws.pin_this_process("served-day")
    patch = pytest.MonkeyPatch()
    picks: list[str] = []
    steps: list[Any] = []
    real_choose, real_advance = StagedChooser.choose, RMH.advance

    def choose(self: Any, state: Any, feasible: Any) -> Any:
        choice = real_choose(self, state, feasible)
        picks.append(choice.candidate_id)
        return choice

    def advance(env: Any, **kwargs: Any) -> Any:
        record, step = real_advance(env, **kwargs)
        steps.append(None if step is None else [step.get("kind"), step.get("practice_item_id")])
        return record, step

    measured: list[Any] = []
    real_pick = delayed_checks.pick_with_receipt

    def pick(*args: Any, **kwargs: Any) -> Any:
        item, receipt = real_pick(*args, **kwargs)
        measured.append([receipt.get("tied"), receipt.get("chosen")])
        return item, receipt

    patch.setattr(delayed_checks, "pick_with_receipt", pick)
    patch.setattr(StagedChooser, "choose", choose)
    patch.setattr(RMH, "advance", advance)
    RMH.join_carried_valuations(patch)
    seed = _pin(patch)
    env = RMH.mixture_env(root, fake_runtime(seed=seed), version=LATEST_ALGORITHM_VERSION, toml=QUIET,
                          session_id="s1")
    RMH.run(env)
    patch.undo()
    return {"picks": picks, "steps": steps, "measured": measured}


def main(argv: list[str]) -> int:
    root, out = Path(argv[0]), Path(argv[1])
    if "--reverse-unordered-selects" in argv[2:]:
        _reverse_unordered_selects()
    out.write_text(json.dumps(served_day(root), sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
