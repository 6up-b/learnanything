"""The rich (video) job, golden (refactor K10.4, strategy ``docs/reviews/k10-figures-strategy-2026-11-14.md`` section
4.2).

Each case builds a quick figure whose answer asks for a Manim video, then runs the queued rich job with the fake rich
author, renderer and function runner the rich job tests use (``tests/figure_rich_job_helpers.py``). It records what
the job sent the rich author, what it asked the renderer and the function runner, every row it wrote, changed or
removed in the figure tables (``figure_build_golden_helpers.TABLES``), and the Reader's list after it. Cases: a video
that lands; a claim that fails on the first attempt; a render that fails and is repaired; a video from a cropped
region; a video from a show-me press whose saved context has only its home; and each code ``rich.RichJobStopped``
ends a job with.

Recorded with ``FIGURE_BUILD_WRITE_GOLDEN=1`` into ``tests/fixtures/figure_rich_job_golden.json``; never rewritten by
a structure step. No model, Manim or bubblewrap runs.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

import pytest

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.spend import SpendLimitExceeded
from learnloop.figures import rich as RICH
from tests import rich_fixtures as RF
from tests.figure_build_golden_helpers import (
    check_golden,
    fixed_sandbox,
    normalized,
    recorded_twice,
    table_rows,
    written,
)
from tests.figure_fixtures import flagship
from tests.figure_rich_job_helpers import WHY, _Rig


GOLDEN = Path(__file__).parent / "fixtures" / "figure_rich_job_golden.json"
WRITE = os.environ.get("FIGURE_BUILD_WRITE_GOLDEN") == "1"
#: Fifteen cases, each run twice in a vault of its own: about 20 s serial.
pytestmark = pytest.mark.slow

ORDER = ("rich_prompts", "renders", "functions", "written", "job", "list")
QUICK = [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))]


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class RichCase:
    """A quick figure built and its rich job queued; :meth:`run` drains the queue and records what the job did."""

    def __init__(self, tmp_path: Path, monkeypatch: Any, rich_answers: list[Any] | None = None, *,
                 request: Any = None, find: Any = None, images: bool = False, **rig: Any) -> None:
        self.rig = _Rig(tmp_path, monkeypatch, list(QUICK), rich_answers, **rig)
        self.rig.author.images = images  # a region's crop goes only to a route that reads images
        self.rig.build(request, find=find)
        self.before = table_rows(self.rig.paths.sqlite_path)

    def run(self) -> dict[str, Any]:
        rig = self.rig
        rig.ingest.drain()
        author = rig.rich_author
        listed = rig.listed()  # first: a list read may write too
        found = {
            "rich_prompts": list(author.prompts) if author is not None else [],
            # The render's wrapper names this machine's prlimit: the scene, its class and the settings are recorded.
            "renders": [{"scene_class": call["scene_class"], "scene_sha256": _sha(call["scene_code"]),
                         "settings": sorted(key for key in call if key not in ("scene_code", "scene_class")),
                         "quality": call.get("quality")} for call in rig.renders.calls],
            "functions": [_sha(source) for source in rig.functions.sources],
            "written": written(self.before, table_rows(rig.paths.sqlite_path)),
            "job": {key: rig.job().get(key) for key in ("status", "error", "phase", "attempt_count")},
            "list": listed,
        }
        return normalized(found, ORDER)


def case_video_lands(tmp_path, monkeypatch):
    return RichCase(tmp_path, monkeypatch).run()


def case_claim_fails_on_the_first_attempt(tmp_path, monkeypatch):
    wrong = RF.scene_output(declared={**RF.DECLARED, "claims": [
        {"kind": "equals", "function": "x", "expr": "exp(a*t)*sin(b*t)"}]})
    return RichCase(tmp_path, monkeypatch, [wrong, RF.scene_output()]).run()


def case_render_fails_and_is_repaired(tmp_path, monkeypatch):
    return RichCase(tmp_path, monkeypatch, renders=RF.Renders([RF.failed_render()])).run()


def case_video_from_a_cropped_region(tmp_path, monkeypatch):
    """The job's saved context names a region (a box over the figure block p4) and its crop, not a selection: the
    job's held-out check reads the region's block."""

    import base64
    import json

    import learnloop.reader.span_view as SV
    from learnloop.figures import request as FQ
    from tests.figure_fixtures import EXTRACTION

    def crop(path, page, bbox):
        data = ("CROP:" + json.dumps([round(float(value), 2) for value in bbox])).encode()
        return "data:image/png;base64," + base64.b64encode(data).decode("ascii"), [612.0, 792.0]

    monkeypatch.setattr(SV, "_original_pdf_for", lambda repo, extraction_id: "book.pdf")
    monkeypatch.setattr(SV, "_original_pdf_path", lambda repo, revision, uri: "book.pdf")
    monkeypatch.setattr(SV, "_local_pdf_block_crop", crop)
    request = FQ.FigureRequest(extraction_id=EXTRACTION, span_ids=[],
                               region={"span_id": "p4", "bbox": [150.0, 120.0, 260.0, 220.0]})
    return RichCase(tmp_path, monkeypatch, request=request, images=True).run()


def case_video_from_a_show_me_press_with_only_a_home(tmp_path, monkeypatch):
    """A show-me press with no passage whose retrieval found nothing: the job's saved context has no span and no
    retrieved key, only the reading position (its home), which the job's held-out check reads."""

    from learnloop.figures import request as FQ
    from tests.figure_fixtures import EXTRACTION
    from tests.figures_help_helpers import FindFake

    request = FQ.FigureRequest(extraction_id=EXTRACTION, span_ids=[], origin="show_me",
                               goal_text="show how the mass left of zero moves as p changes", goal_author="learner",
                               reading_at={"extraction_id": EXTRACTION, "span_id": "p2"})
    return RichCase(tmp_path, monkeypatch, request=request, find=FindFake()).run()


def case_stopped_figures_changed(tmp_path, monkeypatch):
    """The switch goes off while the rich author answers: the job's next gate check stops it."""

    case = RichCase(tmp_path, monkeypatch)

    class SwitchedOff(RF.RichAuthorFake):
        def complete(self, request: Any) -> Any:
            RF.configure(case.rig.paths, rich_tiers_enabled=False)
            return super().complete(request)

    case.rig.rich_author = SwitchedOff()
    return case.run()


def case_stopped_rich_disabled(tmp_path, monkeypatch):
    case = RichCase(tmp_path, monkeypatch)
    RF.configure(case.rig.paths, manim_opt_in="declined")
    return case.run()


def case_stopped_manim_unavailable(tmp_path, monkeypatch):
    case = RichCase(tmp_path, monkeypatch)
    monkeypatch.setattr(RICH, "manim_runtime_state",
                        lambda vault, probe=True: {"ready": False, "reason": "no_manim", "version": None})
    return case.run()


def case_stopped_exam_material(tmp_path, monkeypatch):
    from tests.figures_codex_review_helpers import _hold_out

    case = RichCase(tmp_path, monkeypatch)
    _hold_out(monkeypatch, "p2")  # a neighbour the author was sent
    return case.run()


def case_stopped_waiting_for_plan(tmp_path, monkeypatch):
    return RichCase(tmp_path, monkeypatch, [AIProviderUnavailable("usage limit reached")]).run()


def case_stopped_capped(tmp_path, monkeypatch):
    return RichCase(tmp_path, monkeypatch, [SpendLimitExceeded("the day's figure envelope")]).run()


def case_stopped_unpriced(tmp_path, monkeypatch):
    case = RichCase(tmp_path, monkeypatch)
    case.rig.rich_author = RF.RichAuthorFake(provider_type="openrouter")  # metered, and no price set
    return case.run()


def case_stopped_unrouted(tmp_path, monkeypatch):
    from learnloop.ops.settings_store import apply_config_updates

    case = RichCase(tmp_path, monkeypatch)
    case.rig.rich_author = None  # no injected client: the route as configured, which names no provider
    apply_config_updates(case.rig.paths.root / "learnloop.toml", {("ai", "routing", "figure_rich_author"): "manual"})
    monkeypatch.setattr(RICH.R, "models_off", lambda: False)
    return case.run()


def case_stopped_not_isolated(tmp_path, monkeypatch):
    class Leaky(RF.RichAuthorFake):
        def supports(self, capability: str) -> bool:
            from learnloop.ai.transport import ISOLATED_TURN

            return capability != ISOLATED_TURN and super().supports(capability)

    case = RichCase(tmp_path, monkeypatch)
    case.rig.rich_author = Leaky()
    return case.run()


def case_stopped_models_off(tmp_path, monkeypatch):
    case = RichCase(tmp_path, monkeypatch)
    case.rig.rich_author = None  # no injected client, and the tests' environment turns the models off
    return case.run()


CASES = {name[len("case_"):]: function for name, function in sorted(globals().items()) if name.startswith("case_")}


@pytest.mark.parametrize("case", sorted(CASES))
def test_the_rich_job_is_as_recorded(case, tmp_path):
    runs = iter(("first", "second"))

    def run(monkeypatch):
        root = tmp_path / next(runs)
        root.mkdir()
        fixed_sandbox(monkeypatch)
        return CASES[case](root, monkeypatch)

    check_golden(GOLDEN, case, recorded_twice(run), write=WRITE)


def test_every_stop_code_has_a_case():
    import inspect

    codes = set(inspect.getdoc(RICH.RichJobStopped).split("``")[1::2]) - {"code", "retryable"}
    assert {f"stopped_{code}" for code in codes} <= set(CASES), sorted(codes)
