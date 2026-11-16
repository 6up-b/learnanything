"""What a test vault "at an older tag" needs to be served as that tag was: each successor's kill switches, by tag.

Below the floor (mvp-0.58) no vault opens, and refactor D4-D6 removed the tag halves of the successors' gates, so the
code no longer reads a vault's tag to choose between a successor and its predecessor: a vault a test puts at an older
tag would be served every successor. Each switch's off-branch is its predecessor's code, so the suite reaches an older
tag's behaviour through the switches instead.

What it writes, and when. ``tests/helpers.set_algorithm_version`` (``create_placement_vault``, ``mixture_env`` and
every other helper that puts a vault at a tag goes through it) calls :func:`serve_as_at` after rewriting the tag:

* At a tag ``v``, every key of :data:`SWITCHES_BY_TAG` whose successor tag comes after ``v`` (``switches_after``) is
  written into ``learnloop.toml`` with the value listed (each one's predecessor), creating its table if needed. At
  ``mvp-0.57`` or later (the floor, the head) nothing is written: a vault at a tag that can still open is untouched.
* Moving the same vault to a later tag removes the keys this module wrote that the later tag no longer needs, and only
  those; back at the head the config is the one the test had before.
* A tag this code does not know (``mvp-0.60``, ``mvp-1.0``, ``not-a-tag``) writes nothing.

How a test opts out. A key the test's config already sets is never written or removed: set the switch yourself
(before ``set_algorithm_version``, or after it with ``append_config_toml``, which merges into a table only this module
wrote and hands the keys it names to the test) to keep a successor on at an older tag. A key whose value no longer
matches what was written here is the test's from then on.

Only the successors whose gates refactor D6 part 2 removed are listed; part 1's tests name their switch where they use
it. D7 removes these switches: a test that still reaches a predecessor through one of them loses its predecessor then
(its entry here goes with the switch), and moves to the head or goes with it.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from learnloop.algorithm_versions import (
    ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION,
    DATA_CAPTURE_ALGORITHM_VERSION,
    FAILURE_SHARE_ALGORITHM_VERSION,
    FOLLOWUP_SERVE_ALGORITHM_VERSION,
    INTERVAL_FACTOR_ALGORITHM_VERSION,
    LESSON_OFFERS_ALGORITHM_VERSION,
    LESSON_OPPORTUNITY_ALGORITHM_VERSION,
    LESSON_SUGGESTIONS_ALGORITHM_VERSION,
    ROUTER_CALIBRATION_ALGORITHM_VERSION,
    ROUTER_FOLLOWUPS_ALGORITHM_VERSION,
    ROUTER_LEARNED_TAIL_ALGORITHM_VERSION,
    SLIP_GAP_ALGORITHM_VERSION,
    ROUTER_OBJECTIVE_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    TEACHER_ALGORITHM_VERSION,
)
from learnloop.router_objective_switches import FOLLOWUP_SWITCHES

#: Successor tag -> the config values that serve its predecessor (dotted key -> value).
SWITCHES_BY_TAG: dict[str, dict[str, Any]] = {
    ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION: {"adaptive_difficulty.enabled": False},
    TEACHER_ALGORITHM_VERSION: {"teacher.enabled": False},
    LESSON_SUGGESTIONS_ALGORITHM_VERSION: {"router.lesson_suggestions.enabled": False},
    DATA_CAPTURE_ALGORITHM_VERSION: {"data_capture.serving": False},
    FOLLOWUP_SERVE_ALGORITHM_VERSION: {"followup.generate_and_serve": False},
    INTERVAL_FACTOR_ALGORITHM_VERSION: {
        "scheduler.surprise.remove_interval_factor": False,
        "router_objective.available_at_reads": False,
        "router_objective.self_report_not_validated": False,
    },
    ROUTER_OBJECTIVE_ALGORITHM_VERSION: {"router_objective.enabled": False},
    # RO5's arms at their declared zero, and RO4's priors for its follow-ups.
    ROUTER_CALIBRATION_ALGORITHM_VERSION: {
        "router_objective.stop_coin": 0.0,
        "router_objective.check_rate": "off",
        "router_objective.pick_open_share": 0.0,
        "router_objective.fitted_models": False,
    },
    ROUTER_LEARNED_TAIL_ALGORITHM_VERSION: {"router_objective.learned_tail": False},
    ROUTER_FOLLOWUPS_ALGORITHM_VERSION: {f"router_objective.{key}": False for key in FOLLOWUP_SWITCHES},
    LESSON_OPPORTUNITY_ALGORITHM_VERSION: {"adaptive_difficulty.lesson_opportunities": False},
    LESSON_OFFERS_ALGORITHM_VERSION: {"router.lesson_suggestions.in_objective": False},
    # Instruct hand-off's batch (one tag).
    FAILURE_SHARE_ALGORITHM_VERSION: {
        "router_objective.failure_share_to_other_policy": False,
        "router_objective.lessons_compete_with_followups": False,
        "router_objective.preferences_inform_router": False,
        "router_objective.learner_preferences": False,
        "router_objective.workbench_is_open_item": False,
        "router_objective.lesson_sources_follow_diagnosis": False,
        "router_objective.lesson_candidate_after_cold_miss": False,
    },
    SLIP_GAP_ALGORITHM_VERSION: {
        "router_objective.miss_cause_sensor": False,
        "router_objective.miss_cause_in_value": False,
    },
}


def switches_after(version: str) -> dict[str, Any]:
    """Every listed successor switch of a tag after ``version``, as its predecessor's value."""

    index = SUCCESSOR_CHAIN.index(version) if version in SUCCESSOR_CHAIN else -1
    out: dict[str, Any] = {}
    for tag, switches in SWITCHES_BY_TAG.items():
        if SUCCESSOR_CHAIN.index(tag) > index:
            out.update(switches)
    return out


_MISSING = object()

#: Per vault root, the keys :func:`serve_as_at` wrote and the value it wrote.
_WRITTEN: dict[Path, dict[str, Any]] = {}


def _value(config: dict[str, Any], dotted: str) -> Any:
    node: Any = config
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return _MISSING
        node = node[part]
    return node


def serve_as_at(root: Path, version: str) -> None:
    """Make ``root``'s ``learnloop.toml`` serve ``version`` for the listed successors: every switch of a later tag
    off, unless the test set it; every switch this module set for an earlier, lower tag that ``version`` reaches,
    removed again."""

    import tomlkit

    from learnloop.version_floor import is_below_floor

    if version not in SUCCESSOR_CHAIN and not is_below_floor(version):
        return
    path = Path(root) / "learnloop.toml"
    key_root = Path(root).resolve()
    text = path.read_text(encoding="utf-8")
    current = tomllib.loads(text)
    written = _WRITTEN.setdefault(key_root, {})
    # A key whose value is no longer what was written here is the test's now.
    for key in [key for key, value in written.items() if _value(current, key) != value]:
        del written[key]
    desired = switches_after(version)
    document = tomlkit.parse(text)
    changed = False
    for key in [key for key in written if key not in desired]:
        parts = key.split(".")
        node: Any = document
        for part in parts[:-1]:
            node = node[part]
        del node[parts[-1]]
        del written[key]
        changed = True
    for key, value in desired.items():
        if key in written or _value(current, key) is not _MISSING:
            continue
        parts = key.split(".")
        node = document
        for part in parts[:-1]:
            if part not in node:
                node[part] = tomlkit.table()
            node = node[part]
        node[parts[-1]] = value
        written[key] = value
        changed = True
    if changed:
        path.write_text(tomlkit.dumps(document), encoding="utf-8")


def owns_table(root: Path, table: str) -> bool:
    """Whether every key of ``[table]`` in ``root``'s config was written by :func:`serve_as_at` (so a fragment that
    names the table is merged into it, not refused as a duplicate)."""

    config = tomllib.loads((Path(root) / "learnloop.toml").read_text(encoding="utf-8"))
    node = _value(config, table)
    written = _WRITTEN.get(Path(root).resolve(), {})
    if not isinstance(node, dict):
        return False
    leaves = [f"{table}.{key}" for key, value in node.items() if not isinstance(value, dict)]
    return all(leaf in written for leaf in leaves)


def forget(root: Path, keys: list[str]) -> None:
    """``keys`` are the test's now (a fragment it appended set them)."""

    written = _WRITTEN.get(Path(root).resolve(), {})
    for key in keys:
        written.pop(key, None)
