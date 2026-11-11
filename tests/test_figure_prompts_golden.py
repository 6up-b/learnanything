"""The figure author's and the prefetch judge's prompts, byte for byte (refactor B4's proof).

B4 adds decision records beside the figure author's attempts and the prefetch pass; a record must never
change what a model is sent. The golden (``tests/fixtures/figure_prompts_golden.json``) was written from
main ``536963aa30``, before any B4 code, with ``FIGURE_PROMPTS_WRITE_GOLDEN=1``: a pressed build whose first
answer is refused (so the second prompt carries the first's problems), one that fails verification twice,
and a plan-triggered prefetch pass (the section judge's prompt and the prebuild's author prompt). Fakes only.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from learnloop.figures import prefetch as PF
from tests.figure_fixtures import AuthorFake, build, build_figure_vault, context, flagship, half_density
from tests.figures_prefetch_helpers import JudgeFake, env_for, make_vault, mains, plan_record  # noqa: F401 - mains: autouse

GOLDEN = Path(__file__).parent / "fixtures" / "figure_prompts_golden.json"
WRITE = os.environ.get("FIGURE_PROMPTS_WRITE_GOLDEN") == "1"


def _pressed(root: Path, answers: list) -> list[str]:
    paths, _repository = build_figure_vault(root)
    author = AuthorFake(answers)
    build(context(paths.root, author=author))
    return author.prompts


def _recorded(tmp_path: Path, monkeypatch) -> dict[str, list[str]]:
    recorded = {
        "pressed_refused_then_accepted": _pressed(tmp_path / "a", ["{not json", flagship()]),
        "pressed_failed_twice": _pressed(tmp_path / "b", [half_density(), half_density()]),
    }
    _paths, repository, vault = make_vault(tmp_path / "c")
    plan_record(monkeypatch)
    judge, author = JudgeFake(), AuthorFake()
    PF.run_trigger(env_for(vault, repository, judge=judge, author=author), PF.Trigger("plan", "dp_1"))
    recorded["prefetch_judge"] = judge.prompts
    recorded["prefetch_author"] = author.prompts
    return recorded


def test_figure_prompts_are_main_s_byte_for_byte(tmp_path, monkeypatch):
    recorded = _recorded(tmp_path, monkeypatch)
    assert all(recorded.values()), {name: len(prompts) for name, prompts in recorded.items()}
    if WRITE:
        GOLDEN.write_text(json.dumps(recorded, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    assert recorded == json.loads(GOLDEN.read_text(encoding="utf-8"))
