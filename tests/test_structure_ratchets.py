"""Structure numbers that only go down: the largest import cycle, first-level names, long functions, history comments.

``scripts/refactor_measures.py`` counts them from the tracked source (the test reads files and imports nothing from
``learnloop``); ``tests/goldens/structure.toml`` holds the numbers the tree is held to, with the members behind them so
a failure can name what is new. A number above the golden fails; one below passes, because the golden is lowered when an
arc closes, not on every commit, so branches that each shrink a number do not conflict on the file.

Two ways out of a failure: fix the code, or raise the golden in the same commit with the reason in the commit message:

    uv run python tests/test_structure_ratchets.py --write
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tomllib
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = Path(__file__).parent / "goldens" / "structure.toml"
REGENERATE = "uv run python tests/test_structure_ratchets.py --write"
HEADER = (
    "# What the structure ratchets hold the tree to (tests/test_structure_ratchets.py), from scripts/refactor_measures.py.\n"
    "# [ratchet] is the gate: a number above it fails. [members] and [stage_comments_by_file] only let a failure name\n"
    "# what is new. Generated; do not edit by hand. Lower it at an arc close; raise it only in the commit that must,\n"
    "# with the reason in the message: " + REGENERATE + "\n"
)


def _measures():
    spec = importlib.util.spec_from_file_location("refactor_measures", ROOT / "scripts" / "refactor_measures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def current() -> dict[str, Any]:
    """The ratcheted numbers and the members behind them, as the golden stores them."""

    swept = _measures().structure_sweep()
    names = swept["first_level_names"]
    return {
        "ratchet": {
            "largest_import_component": swept["import_component"]["modules"],
            "modules_in_an_import_cycle": swept["modules_in_a_cycle"],
            "first_level_packages": names["packages"],
            "first_level_root_modules": names["root_modules"],
            "first_level_root_modules_not_upgrade": names["root_modules_not_upgrade"],
            "functions_over_200_lines": len(swept["functions_over_200_lines"]),
            "comment_lines_naming_a_stage_artifact": swept["stage_comments"]["naming_a_stage_artifact"],
            "test_files_named_for_a_stage": swept["stage_test_files"]["count"],
        },
        "members": {
            "import_component": swept["import_component"]["members"],
            "root_modules": names["root_module_names"],
            "functions_over_200_lines": swept["functions_over_200_lines"],
            "stage_test_files": swept["stage_test_files"]["names"],
        },
        "stage_comments_by_file": swept["stage_comments"]["by_file"],
    }


def _toml(payload: dict[str, Any]) -> str:
    out = [HEADER]
    for table, body in payload.items():
        out.append(f"\n[{table}]")
        for key, value in body.items():
            if isinstance(value, list):
                out.append(f"{key} = [" + "".join(f"\n    {json.dumps(item)}," for item in value) + "\n]")
            else:
                out.append(f"{json.dumps(key) if table == 'stage_comments_by_file' else key} = {value}")
    return "\n".join(out) + "\n"


# Ratchet key -> what to say, which members hold its offenders (None: say the count only), and how to name them.
EXPLAIN = {
    "largest_import_component": ("the largest import cycle (modules in the biggest strongly connected component of the "
                                 "import graph, function-local imports included, TYPE_CHECKING left out)",
                                 "import_component", "joined the component"),
    "modules_in_an_import_cycle": ("modules in any import cycle", None, ""),
    "first_level_packages": ("first-level packages in src/learnloop", None, ""),
    "first_level_root_modules": ("root modules in src/learnloop", "root_modules", "new root modules"),
    "first_level_root_modules_not_upgrade": ("root modules in src/learnloop not named *_upgrade.py", "root_modules",
                                             "new root modules"),
    "functions_over_200_lines": ("functions over 200 lines", "functions_over_200_lines", "new long functions"),
    "comment_lines_naming_a_stage_artifact": ("comment lines naming a stage artifact (a ruling, Codex, a round, a "
                                              "landing, an F- or R-number)", None, ""),
    "test_files_named_for_a_stage": ("test files named for a stage or a fix round", "stage_test_files",
                                     "new stage-named test files"),
}


def _new(key: str, now: dict[str, Any], golden: dict[str, Any]) -> list[str]:
    members = EXPLAIN[key][1]
    if members:
        before, after = Counter(golden.get("members", {}).get(members, [])), Counter(now["members"][members])
        return sorted((after - before).elements())
    if key == "comment_lines_naming_a_stage_artifact":
        before, after = golden.get("stage_comments_by_file", {}), now["stage_comments_by_file"]
        return sorted(f"{path} (+{n - before.get(path, 0)})" for path, n in after.items() if n > before.get(path, 0))
    return []


def failures(now: dict[str, Any], golden: dict[str, Any]) -> list[str]:
    messages = []
    for key, value in now["ratchet"].items():
        held = golden["ratchet"].get(key)
        if held is None:
            messages.append(f"structure ratchet '{key}' has no line in [ratchet] of tests/goldens/structure.toml, so "
                            f"nothing holds it (now {value}); restore the line ({REGENERATE}).")
            continue
        if value <= held:
            continue
        what, _members, verb = EXPLAIN[key]
        new = _new(key, now, golden)
        listing = f"\n  {verb}:\n    " + "\n    ".join(new[:40]) + ("\n    ..." if len(new) > 40 else "") if new else ""
        messages.append(
            f"structure ratchet '{key}' rose: {what} is {value}, the golden holds {held} (+{value - held}).{listing}"
        )
    if messages:
        messages.append(
            "Two ways out: fix the code so the number does not rise, or raise tests/goldens/structure.toml in the same "
            f"commit with the reason in the commit message ({REGENERATE})."
        )
    return messages


def test_no_structure_number_rose_above_the_golden() -> None:
    golden = tomllib.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    problems = failures(current(), golden)
    assert not problems, "\n" + "\n".join(problems)


def test_the_failure_message_names_what_is_new() -> None:
    golden = {"ratchet": {"largest_import_component": 2, "functions_over_200_lines": 0, "first_level_root_modules": 1},
              "members": {"import_component": ["a", "b"], "functions_over_200_lines": [], "root_modules": ["x"]},
              "stage_comments_by_file": {}}
    now = {"ratchet": {"largest_import_component": 3, "functions_over_200_lines": 1, "first_level_root_modules": 1},
           "members": {"import_component": ["a", "b", "c"], "functions_over_200_lines": ["src/m.py big"],
                       "root_modules": ["x"]},
           "stage_comments_by_file": {}}
    text = "\n".join(failures(now, golden))
    assert "'largest_import_component' rose" in text and "is 3, the golden holds 2" in text
    assert "joined the component:\n    c" in text and "src/m.py big" in text
    assert "first_level_root_modules" not in text and "--write" in text


def test_a_ratchet_key_missing_from_the_golden_fails() -> None:
    golden = {"ratchet": {}, "members": {}, "stage_comments_by_file": {}}
    now = {"ratchet": {"functions_over_200_lines": 0}, "members": {"functions_over_200_lines": []},
           "stage_comments_by_file": {}}
    text = "\n".join(failures(now, golden))
    assert "'functions_over_200_lines' has no line" in text


def write() -> None:
    GOLDEN_PATH.parent.mkdir(exist_ok=True)
    GOLDEN_PATH.write_text(_toml(current()), encoding="utf-8")
    print(f"wrote {GOLDEN_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    if sys.argv[1:] == ["--write"]:
        write()
    else:
        raise SystemExit(__doc__)
