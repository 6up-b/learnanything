from __future__ import annotations

import subprocess
import types
from pathlib import Path

from learnloop.content.authoring.ai_contracts import CONCEPT_ANIMATION_SCENE_SCAFFOLD
from learnloop.content.authoring.concept_animation import (
    RenderResult,
    estimate_scene_duration,
    lint_scene_pacing,
    manim_runtime,
    render_scene,
    validate_scene_code,
)

VALID_SCENE = """\
from manim import Scene, Circle, Create
import numpy as np
import math


class ExplainSVD(Scene):
    def construct(self):
        circle = Circle(radius=math.sqrt(2))
        self.play(Create(circle))
        self.wait(1)
"""


def test_valid_scene_passes_and_names_class():
    scene_class, violations = validate_scene_code(VALID_SCENE)
    assert scene_class == "ExplainSVD"
    assert violations == []


def test_validator_rejects_malicious_samples():
    samples = {
        "import os": "import os\nfrom manim import Scene\nclass S(Scene):\n    pass\n",
        "from subprocess": "from subprocess import run\nfrom manim import Scene\nclass S(Scene):\n    pass\n",
        "relative import": "from . import secrets\nfrom manim import Scene\nclass S(Scene):\n    pass\n",
        "open": "from manim import Scene\nclass S(Scene):\n    def construct(self):\n        open('x')\n",
        "eval": "from manim import Scene\nclass S(Scene):\n    def construct(self):\n        eval('1')\n",
        "exec": "from manim import Scene\nclass S(Scene):\n    def construct(self):\n        exec('1')\n",
        "__import__": "from manim import Scene\nclass S(Scene):\n    def construct(self):\n        __import__('os')\n",
        "getattr": "from manim import Scene\nclass S(Scene):\n    def construct(self):\n        getattr(self, 'play')\n",
        "dunder escape": "from manim import Scene\nclass S(Scene):\n    def construct(self):\n        ().__class__.__subclasses__()\n",
        "globals": "from manim import Scene\nclass S(Scene):\n    def construct(self):\n        globals()\n",
        "alias smuggle": "import os as np\nfrom manim import Scene\nclass S(Scene):\n    pass\n",
    }
    for label, code in samples.items():
        _, violations = validate_scene_code(code)
        assert violations, f"expected violations for: {label}"


def test_validator_requires_scene_subclass_and_reports_syntax_errors():
    _, violations = validate_scene_code("import manim\nx = 1\n")
    assert any("Scene subclass" in violation for violation in violations)
    scene_class, violations = validate_scene_code("def broken(:\n")
    assert scene_class is None
    assert violations and "syntax error" in violations[0]


def _fake_run_success(command, cwd=None, env=None, capture_output=None, timeout=None):
    media = Path(cwd) / "media" / "videos" / "scene" / "480p15"
    media.mkdir(parents=True)
    (media / "ExplainSVD.mp4").write_bytes(b"fake-mp4-bytes")
    # Manim also leaves one fragment per self.play() beside the combined file;
    # it sorts AFTER the class-named file, so a naive sorted(glob)[-1] picks it.
    partial = media / "partial_movie_files" / "ExplainSVD"
    partial.mkdir(parents=True)
    (partial / "uncached_00000.mp4").write_bytes(b"partial-fragment")
    return types.SimpleNamespace(returncode=0, stdout=b"", stderr=b"rendered fine")


def test_render_scene_ignores_partial_movie_files_when_only_partials_exist():
    def partial_only_run(command, cwd=None, env=None, capture_output=None, timeout=None):
        partial = Path(cwd) / "media" / "videos" / "scene" / "480p15" / "partial_movie_files" / "ExplainSVD"
        partial.mkdir(parents=True)
        (partial / "uncached_00000.mp4").write_bytes(b"partial-fragment")
        return types.SimpleNamespace(returncode=0, stdout=b"", stderr=b"")

    result = render_scene(VALID_SCENE, "ExplainSVD", sandbox=False, run=partial_only_run)

    assert result.ok is False
    assert result.video_bytes is None
    assert "partial movie files" in result.stderr_tail


def test_render_scene_prefers_scene_class_named_file():
    def two_outputs_run(command, cwd=None, env=None, capture_output=None, timeout=None):
        media = Path(cwd) / "media" / "videos" / "scene" / "480p15"
        media.mkdir(parents=True)
        (media / "ExplainSVD.mp4").write_bytes(b"named")
        (media / "Zzz.mp4").write_bytes(b"other")
        return types.SimpleNamespace(returncode=0, stdout=b"", stderr=b"")

    result = render_scene(VALID_SCENE, "ExplainSVD", sandbox=False, run=two_outputs_run)

    assert result.ok is True
    assert result.video_bytes == b"named"


def test_render_scene_success_reads_mp4_and_cleans_temp(tmp_path):
    captured = {}

    def spy_run(command, cwd=None, env=None, capture_output=None, timeout=None):
        captured["command"] = command
        captured["cwd"] = cwd
        captured["env"] = env
        return _fake_run_success(command, cwd=cwd)

    result = render_scene(
        VALID_SCENE, "ExplainSVD", quality="ql", timeout_seconds=60, sandbox=False, run=spy_run
    )

    assert result.ok is True
    assert result.video_bytes == b"fake-mp4-bytes"
    assert "-ql" in captured["command"] and "ExplainSVD" in captured["command"]
    # Constrained env: nothing vault-shaped leaks into the subprocess.
    assert not any(key.upper().startswith("LEARNLOOP") for key in captured["env"])
    # Temp workdir is cleaned up.
    assert not Path(captured["cwd"]).exists()


def test_render_scene_failure_captures_stderr_tail():
    def failing_run(command, cwd=None, env=None, capture_output=None, timeout=None):
        return types.SimpleNamespace(returncode=1, stdout=b"", stderr=b"Tex not found: latex missing")

    result = render_scene(VALID_SCENE, "ExplainSVD", sandbox=False, run=failing_run)

    assert result.ok is False
    assert result.video_bytes is None
    assert "latex missing" in result.stderr_tail
    assert result.returncode == 1


def test_render_scene_timeout_is_typed():
    def timeout_run(command, cwd=None, env=None, capture_output=None, timeout=None):
        raise subprocess.TimeoutExpired(cmd=command, timeout=timeout)

    result = render_scene(VALID_SCENE, "ExplainSVD", timeout_seconds=5, sandbox=False, run=timeout_run)

    assert result.ok is False
    assert "timed out after 5s" in result.stderr_tail


def test_manim_runtime_probe_found_and_missing():
    def found_run(command, capture_output=None, timeout=None):
        assert command[-1] == "--version"
        return types.SimpleNamespace(returncode=0, stdout=b"Manim Community v0.18.1", stderr=b"")

    probe = manim_runtime(run=found_run)
    assert probe["available"] is True
    assert "0.18.1" in probe["version"]

    def missing_run(command, capture_output=None, timeout=None):
        raise FileNotFoundError(command[0])

    probe = manim_runtime(run=missing_run)
    assert probe["available"] is False
    assert "not found" in probe["reason"]


def test_render_result_is_plain_dataclass():
    result = RenderResult(ok=False, video_bytes=None, stderr_tail="x", returncode=2)
    assert result.stderr_tail == "x"


def _spy_run_factory(captured):
    def spy_run(command, cwd=None, env=None, capture_output=None, timeout=None):
        captured["command"] = command
        captured["cwd"] = cwd
        captured["env"] = env
        return _fake_run_success(command, cwd=cwd)

    return spy_run


def test_render_scene_sandboxes_with_bwrap(monkeypatch):
    import learnloop.content.authoring.concept_animation as ca

    monkeypatch.setattr(ca.sys, "platform", "linux")
    monkeypatch.setattr(ca.shutil, "which", lambda name: "/usr/bin/bwrap")
    captured = {}

    result = render_scene(VALID_SCENE, "ExplainSVD", run=_spy_run_factory(captured))

    assert result.ok is True
    command = captured["command"]
    assert command[0] == "/usr/bin/bwrap"
    assert "--unshare-all" in command  # includes the network namespace
    assert "--" in command
    inner = command[command.index("--") + 1 :]
    assert "render" in inner and "ExplainSVD" in inner
    # The scratch dir is the only writable mount and doubles as HOME.
    assert command[command.index("--bind") + 1] == captured["cwd"]
    assert captured["env"]["HOME"] == captured["cwd"]


def test_render_scene_requires_bwrap_on_linux(monkeypatch):
    import learnloop.content.authoring.concept_animation as ca

    monkeypatch.setattr(ca.sys, "platform", "linux")
    monkeypatch.setattr(ca.shutil, "which", lambda name: None)

    def never_run(command, **kwargs):
        raise AssertionError("render must not run without the sandbox on linux")

    result = render_scene(VALID_SCENE, "ExplainSVD", run=never_run)

    assert result.ok is False
    assert "bubblewrap" in result.stderr_tail


def test_render_scene_off_linux_runs_direct_without_bwrap(monkeypatch):
    import learnloop.content.authoring.concept_animation as ca

    monkeypatch.setattr(ca.sys, "platform", "darwin")
    captured = {}

    result = render_scene(VALID_SCENE, "ExplainSVD", run=_spy_run_factory(captured))

    assert result.ok is True
    assert captured["command"][0] != "/usr/bin/bwrap"
    assert "render" in captured["command"]


def _scaffold_with_beats(count: int) -> str:
    beats = "".join(
        f'        self.beat("Beat {index}", Circle(), run_time=2, hold=3)\n' for index in range(count)
    )
    code = CONCEPT_ANIMATION_SCENE_SCAFFOLD.replace(
        '        # self.beat("Heading of at most eight words", visual, run_time=2, hold=3)\n', beats
    ).replace(
        '        # self.recap(["first takeaway", "second takeaway", "third takeaway"])\n',
        '        self.recap(["a", "b", "c"])\n',
    )
    assert code != CONCEPT_ANIMATION_SCENE_SCAFFOLD
    return code


def test_scaffold_passes_validator():
    scene_class, violations = validate_scene_code(CONCEPT_ANIMATION_SCENE_SCAFFOLD)
    assert scene_class == "ConceptExplainer"
    assert violations == []


def test_scaffold_with_four_beats_estimates_within_the_band():
    code = _scaffold_with_beats(4)
    estimate = estimate_scene_duration(code)
    # title card (5 s) + 4 beats (about 6.2 s each) + recap (about 5 s):
    # the static estimate counts the recap loop once, so it lands just under.
    assert estimate is not None and 28 <= estimate <= 45
    assert lint_scene_pacing(code, min_seconds=25, max_seconds=60) == []


def test_short_and_overlong_scenes_are_flagged_by_pacing_lint():
    short = lint_scene_pacing(VALID_SCENE, min_seconds=30, max_seconds=60)
    assert len(short) == 1 and "below the 30s minimum" in short[0]
    long_scene = VALID_SCENE + "        self.wait(500)\n"
    over = lint_scene_pacing(long_scene, min_seconds=30, max_seconds=60)
    assert len(over) == 1 and "exceeds the 60s maximum" in over[0]
    assert lint_scene_pacing(VALID_SCENE, min_seconds=0, max_seconds=0) == []
    assert lint_scene_pacing("def broken(:", min_seconds=30, max_seconds=60) == []


def test_estimate_follows_loops_defaults_and_helpers():
    code = """\
from manim import Scene, Circle, Create


class Looping(Scene):
    def construct(self):
        for i in range(3):
            self.wait(2)
        for j in range(1, 3):
            self.play(Create(Circle()), run_time=1.5)
        self.step(hold=4)
        self.step()
        self.play(Create(Circle()))

    def step(self, *, hold=2.0):
        self.play(Create(Circle()), run_time=0.5)
        self.wait(hold)
"""
    # 3*2 + 2*1.5 + (0.5+4) + (0.5+2) + 1 = 17
    assert estimate_scene_duration(code) == 17.0
    assert estimate_scene_duration("import manim\nx = 1\n") is None
