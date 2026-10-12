"""Temporary git repos and fake model routes for the project-understanding tests.

Every repo here is created by the test inside ``tmp_path``; nothing reads the
owner's repos, git config or vaults. ``isolated_git`` points git's global
config at an empty temp file so a developer's signing, hooksPath or template
settings cannot change what the tests see.
"""

from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from learnloop.clock import FrozenClock
from learnloop.projects import ai_runtime
from learnloop.projects.ai_contracts import (
    ClosedBookAnswer,
    ClosedBookAnswers,
    ProbeCandidate,
    ProbeCandidates,
    ProbeCitation,
    ProbeGrade,
    ProbeGrades,
)
from learnloop.projects.ai_runtime import ROLE_TASK, ProjectRoute
from tests.structured_ai import RecordingStructuredClientFake

CLAUDE_TRAILER = "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
BASE_TIME = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)

MODEL_PY = """import torch


class GestureModel:
    def __init__(self, scale):
        self.scale = scale

    def forward(self, x):
        return x * self.scale
"""

MODEL_PY_RELU = """import torch


class GestureModel:
    def __init__(self, scale):
        self.scale = scale

    def forward(self, x):
        # Clamp negatives so the GRU never sees a sign flip.
        y = x * self.scale
        y = y + 1
        return torch.relu(y)
"""


@pytest.fixture
def isolated_git(tmp_path_factory, monkeypatch):
    home = tmp_path_factory.mktemp("git-home")
    config = home / "gitconfig"
    config.write_text(
        "[user]\n\tname = Test\n\temail = test@example.invalid\n"
        "[commit]\n\tgpgsign = false\n[init]\n\tdefaultBranch = main\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("HOME", str(home))
    # pytest's temp root lives inside this repository's checkout: never let
    # git discover that repository from a test directory.
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path_factory.getbasetemp()))
    return config


class TempRepo:
    """A throwaway git repository driven through the git CLI."""

    def __init__(self, path: Path) -> None:
        self.path = path
        path.mkdir(parents=True, exist_ok=True)
        self.git("init", "-q", "-b", "main")

    def git(self, *args: str, env: dict[str, str] | None = None) -> str:
        completed = subprocess.run(
            ["git", "-C", str(self.path), *args],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, **(env or {})},
        )
        return completed.stdout

    def write(self, relative: str, text: str) -> Path:
        target = self.path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def commit(self, message: str, *, trailer: str | None = CLAUDE_TRAILER, when: datetime | None = None, add_all: bool = True) -> str:
        if add_all:
            self.git("add", "-A")
        body = message if trailer is None else f"{message}\n\n{trailer}"
        env = None
        if when is not None:
            stamp = when.strftime("%Y-%m-%dT%H:%M:%S+00:00")
            env = {"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp}
        self.git("commit", "-q", "--allow-empty", "-m", body, env=env)
        return self.git("rev-parse", "HEAD").strip()


def make_model_repo(root: Path, *, agent_commit: bool = True, when: datetime | None = None) -> TempRepo:
    repo = TempRepo(root)
    repo.write("model.py", MODEL_PY)
    repo.commit("Initial model", trailer=None, when=when)
    repo.write("model.py", MODEL_PY_RELU)
    repo.commit(
        "Clamp the forward pass with relu\n\nUse relu so negative activations never reach the GRU.",
        trailer=CLAUDE_TRAILER if agent_commit else None,
        when=when,
    )
    return repo


def clock_at(days: float = 0.0) -> FrozenClock:
    return FrozenClock(BASE_TIME + timedelta(days=days))


def _numbered(excerpt_text: str) -> list[tuple[int, str]]:
    rows = []
    for line in excerpt_text.splitlines():
        number, _, code = line.partition("| ")
        rows.append((int(number.rstrip("|")), code))
    return rows


class ProjectFake(RecordingStructuredClientFake):
    """Deterministic stand-ins for the authoring, closed-book and grading models.

    Authoring returns six candidates, one per behaviour the filters must
    handle: two valid, one quote mismatch, a cited ``why``, an uncited
    ``why``, and one generic question the closed-book model answers.
    """

    def __init__(self, *, fail_closed_book: bool = False, fail_grading: bool = False, all_generic: bool = False) -> None:
        super().__init__()
        self.fail_closed_book = fail_closed_book
        self.fail_grading = fail_grading
        self.all_generic = all_generic
        self.calls: dict[str, int] = {}

    def _count(self, name: str) -> None:
        self.calls[name] = self.calls.get(name, 0) + 1

    def run_project_probe_authoring(self, context: Any) -> ProbeCandidates:
        self._count("authoring")
        entry = next(file for file in context.files if file["excerpts"])
        rows = _numbered(entry["excerpts"][0]["text"])
        usable = [(number, code) for number, code in rows if code.strip() and "[REDACTED" not in code]
        number, code = usable[-1]
        cite = ProbeCitation(source="file", path=entry["path"], line_start=number, line_end=number, quote=code.strip())
        first_line = next((line for line in context.commit_message.splitlines() if line.strip()), "")
        generic = "GENERIC" if self.all_generic else ""
        return ProbeCandidates(
            candidates=[
                ProbeCandidate(kind="what_does", reference_answer="It scales x, adds one and applies relu.",
                               citations=[cite], question=f"Q-what {generic}: what does forward return now?"),
                ProbeCandidate(kind="where_change", reference_answer="In forward, replace the relu call.",
                               citations=[cite], question=f"Q-where {generic}: where would you allow negative outputs?"),
                ProbeCandidate(kind="predict", reference_answer="It returns 0 for x=-5.",
                               citations=[cite.model_copy(update={"quote": "this text is not in the code"})],
                               question="Q-bad-quote: what does forward return for x=-5?"),
                ProbeCandidate(kind="why", reference_answer="So negative activations never reach the GRU.",
                               citations=[ProbeCitation(source="commit_message", quote=first_line, rationale=True)],
                               question=f"Q-why-cited {generic}: why does forward use relu?"),
                ProbeCandidate(kind="why", reference_answer="Probably for stability.",
                               citations=[cite], question="Q-why-uncited: why add one before relu?"),
                ProbeCandidate(kind="what_does", reference_answer="GENERIC",
                               citations=[cite], question="Q-generic: what is relu in general?"),
            ]
        )

    def run_project_closed_book_check(self, context: Any) -> ClosedBookAnswers:
        self._count("closed_book")
        if self.fail_closed_book:
            raise RuntimeError("closed-book transport failed")
        return ClosedBookAnswers(
            answers=[
                ClosedBookAnswer(id=q["id"], answer="GENERIC" if "generic" in q["question"].lower() else "no idea")
                for q in context.questions
            ]
        )

    def run_project_probe_grading(self, context: Any) -> ProbeGrades:
        self._count("grading")
        if self.fail_grading:
            raise RuntimeError("grading transport failed")
        grades = []
        for item in context.items:
            answer = item["answer"].lower()
            if "generic" in answer:
                grades.append(ProbeGrade(id=item["id"], verdict="correct", score=1.0, feedback=""))
            elif "relu" in answer:
                grades.append(ProbeGrade(id=item["id"], verdict="correct", score=0.9, feedback=""))
            elif "scale" in answer:
                grades.append(ProbeGrade(id=item["id"], verdict="partially_correct", score=0.5, feedback="Missed the relu."))
            else:
                grades.append(ProbeGrade(id=item["id"], verdict="incorrect", score=0.0, feedback="Missed the point."))
        return ProbeGrades(grades=grades)


def fake_resolver(fake: Any, *, subscription: bool = True, ready: bool = True):
    def resolver(workdir: Path, config: Any, role: str) -> ProjectRoute:
        return ProjectRoute(
            role=role,
            task=ROLE_TASK[role],
            provider_name="fake",
            provider_type="codex_sdk" if subscription else "openrouter",
            model="fake-model",
            subscription=subscription,
            ready=ready,
            message=None if ready else "fake provider not ready",
            client=fake,
        )

    return resolver


@pytest.fixture
def project_fake(monkeypatch):
    fake = ProjectFake()
    monkeypatch.setattr(ai_runtime, "_route_resolver", fake_resolver(fake))
    return fake


def install_fake_codex_sdk(monkeypatch, *, final_response: str = '{"grades": []}') -> dict[str, Any]:
    """A stand-in ``openai_codex`` SDK that records what a turn is started with.

    The real SDK spawns the Codex app-server; this one only captures the
    ``CodexConfig`` kwargs (``codex_bin``, ``launch_args_override``, ``cwd``)
    and the ``thread_start``/``turn`` kwargs (``cwd``, ``effort``, ...).
    """

    import sys
    from enum import Enum
    from types import ModuleType, SimpleNamespace

    captured: dict[str, Any] = {"turns": []}

    class FakeCodex:
        def __init__(self, config):
            captured["app_config"] = config.kwargs

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def close(self):
            return None

        def thread_start(self, **kwargs):
            captured["thread_start"] = kwargs
            return FakeThread()

    class FakeThread:
        def turn(self, prompt: str, **kwargs):
            captured["turns"].append({"prompt": prompt, **kwargs})
            return FakeTurn()

    class FakeTurn:
        def run(self):
            return SimpleNamespace(final_response=final_response)

        def interrupt(self):
            return None

    class SdkAppConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class ReasoningEffort(Enum):
        minimal = "minimal"
        low = "low"
        medium = "medium"
        high = "high"
        xhigh = "xhigh"

    class ReasoningSummary:
        @classmethod
        def model_validate(cls, value):
            return value

    module = ModuleType("openai_codex")
    module.Codex = FakeCodex
    module.CodexConfig = SdkAppConfig
    types_module = ModuleType("openai_codex.types")
    types_module.Personality = SimpleNamespace(pragmatic="pragmatic")
    types_module.ReasoningEffort = ReasoningEffort
    types_module.ReasoningSummary = ReasoningSummary
    monkeypatch.setitem(sys.modules, "openai_codex", module)
    monkeypatch.setitem(sys.modules, "openai_codex.types", types_module)
    return captured
