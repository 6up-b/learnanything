"""Hardening round 3 of the Codex tool lockdown: every turn is tool-free by construction.

The verify of ``bc90f31ae..3c16fa0d1`` (orchestrator job 20261021-130509-fPY40I)
found three Highs and a Low:

* inherited execution-policy ``allow`` rules bypass the sandbox of the one
  route that kept a shell (the snapshot diagnosis);
* native skill discovery and ``$name`` expansion can pull files (a skill
  directory linked into the vault) into a turn;
* a hidden code-mode continuation is not admitted before its request (the
  early stop reacts to usage, after the fact);
* the AST sweep misses aliased or variable-argument process launches.

Binding rulings: the catalog LearnLoop pins is the bundled one with every tool
removed (code mode off), read back through ``debug models`` and ``debug
prompt-input`` (incremental form, which renders the model-visible tools); the
snapshot diagnosis is inlined, so no route has a shell; every skill is
disabled and the rendered context must list none; every process-launch site is
on an approved list. Fakes and the installed CLI's non-model commands only.
"""

from __future__ import annotations

import ast
import json
from collections import Counter
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from learnloop.ai.errors import CodexUnavailable
from learnloop.ai.providers.codex import SdkCodexClient
from learnloop.ai.transport import StructuredRequest
from learnloop.config import CodexConfig
from learnloop.diagnosis.offline_review.judge import LinkJudgment

from tests.codex_cli_fakes import bundled_catalog, fake_codex_calls, write_fake_codex
from tests.project_support import install_fake_codex_sdk

ROOT = Path(__file__).resolve().parents[1]
CODEX = shutil.which("codex")
needs_codex = pytest.mark.skipif(CODEX is None, reason="the Codex CLI is not installed")
ANSWER = '{"links": []}'
MODEL = "gpt-5.6-sol"


def _lockdown():
    from learnloop.ai.providers import codex_lockdown

    return codex_lockdown


def _client(tmp_path: Path, **config: Any) -> SdkCodexClient:
    vault_root = tmp_path / "vault"
    vault_root.mkdir(exist_ok=True)
    return SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex"), model=MODEL, **config), vault_root)


def _launched(log: Path) -> list[list[str]]:
    return [call["overrides"] for call in fake_codex_calls(log) if call["command"][:1] == ["app-server"]]


def _turn(client: SdkCodexClient, workspace: Path | None = None, purpose: str = "tutor_qa"):
    return client.complete(StructuredRequest(purpose=purpose, prompt="p", result_model=LinkJudgment,
                                             workspace=workspace))


# -- 1. the catalog LearnLoop pins has no tool -------------------------------------------


def test_the_pinned_catalog_removes_every_tool_from_every_entry():
    lockdown = _lockdown()
    bundled = bundled_catalog(MODEL, "gpt-6-luna", experimental_supported_tools=["clock", "send_user_message_async"])
    stripped = json.loads(lockdown.tool_free_catalog(json.dumps(bundled)))
    for entry in stripped["models"]:
        assert entry["tool_mode"] == "direct" and entry["shell_type"] == "disabled"
        assert entry["apply_patch_tool_type"] is None and entry["experimental_supported_tools"] == []
        assert entry["supports_search_tool"] is False and entry["multi_agent_version"] == "disabled"
        assert entry["base_instructions"] == bundled["models"][0]["base_instructions"]  # instructions kept
    assert lockdown.tool_free_violations(stripped, MODEL) == []
    assert lockdown.tool_free_violations(bundled, MODEL)  # the bundled catalog is not tool-free
    with pytest.raises(lockdown.CodexLockdownUnavailable):
        lockdown.tool_free_catalog('{"not": "a catalog"}')


def test_every_turn_is_pinned_to_the_tool_free_catalog(tmp_path, monkeypatch):
    """Round 3 (H3 at the source): the app server serves the bundled catalog
    minus its tools, so no tool (code mode's exec/wait included) is offered and
    no continuation can follow a tool call."""

    program, log = write_fake_codex(tmp_path / "bin")
    captured = install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    _turn(_client(tmp_path, sdk_codex_bin=str(program)))
    (launched,) = _launched(log)
    pinned = json.loads(Path(_lockdown().catalog_pin_path(launched)).read_text(encoding="utf-8"))
    assert _lockdown().tool_free_violations(pinned, MODEL) == []
    assert json.loads(captured["spawned"]["stdout"])["experimental_tools"][MODEL] == []


@pytest.mark.parametrize(
    "spec, reason",
    [
        ({"forced_catalog": bundled_catalog(MODEL)}, "not the catalog the launch check pinned"),  # tools again
        ({"forced_tools": ["test_sync_tool"]}, "would offer tools: functions.test_sync_tool"),
        ({"catalog": bundled_catalog(MODEL, use_responses_lite=False)}, "could not be read back"),
    ],
    ids=["catalog-with-tools", "a-tool-from-elsewhere", "no-read-back"],
)
def test_a_turn_that_would_offer_any_tool_is_refused_before_launch(tmp_path, monkeypatch, spec, reason):
    program, log = write_fake_codex(tmp_path / "bin", **spec)
    captured = install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    with pytest.raises(_lockdown().CodexLockdownUnavailable, match=re.escape(reason)):
        _turn(_client(tmp_path, sdk_codex_bin=str(program)))
    assert _launched(log) == [] and "app_config" not in captured


# -- the installed binary: what the turn would really offer --------------------------------

_SKILL_CANARY = "LLCANARY-ROUND3-SKILL-BODY"


def _real_layout(tmp_path: Path, monkeypatch) -> dict[str, Path]:
    """Throwaway ``HOME``/``CODEX_HOME`` holding what the verify named: an
    execution-policy rule allowing ``python3``, and a skill directory linked
    to a file outside (the "vault")."""

    home = tmp_path / "home"
    codex_home = tmp_path / "codex-home"
    outside = tmp_path / "vault-skill"
    for path in (home / ".agents" / "skills", codex_home / "rules", outside):
        path.mkdir(parents=True)
    (codex_home / "config.toml").write_text("", encoding="utf-8")
    (codex_home / "rules" / "default.rules").write_text(
        'prefix_rule(pattern=["python3"], decision="allow")\n', encoding="utf-8")
    (outside / "SKILL.md").write_text(
        f"---\nname: canary-skill\ndescription: A synthetic linked skill.\n---\n{_SKILL_CANARY}\n", encoding="utf-8")
    (home / ".agents" / "skills" / "canary-skill").symlink_to(outside, target_is_directory=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    return {"home": home, "codex_home": codex_home, "outside": outside}


def _prompt_input(layout: dict[str, Path], overrides: list[str], cwd: Path, prompt: str = "") -> list[dict[str, Any]]:
    args = [CODEX]
    for override in [*overrides, "features.incremental_tools=true", f"model={json.dumps(MODEL)}"]:
        args += ["-c", override]
    environ = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(layout["home"]),
               "CODEX_HOME": str(layout["codex_home"])}
    done = subprocess.run([*args, "debug", "prompt-input", *([prompt] if prompt else [])], cwd=cwd, env=environ,
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


def _offered_tools(items: list[dict[str, Any]]) -> list[str]:
    """Parsed here, not by the code under test: every tool an ``additional_tools`` item declares."""

    def names(tools):
        for tool in tools or ():
            if tool.get("tools"):
                yield from (f"{tool.get('name')}.{name}" for name in names(tool["tools"]))
            else:
                yield str(tool.get("name"))

    return [name for item in items if item.get("type") == "additional_tools" for name in names(item.get("tools"))]


def _texts(items: list[dict[str, Any]]) -> str:
    return "\n".join(content.get("text", "") for item in items for content in item.get("content") or ())


def _real_turn_overrides(tmp_path: Path, monkeypatch, layout, *, workspace: Path | None) -> tuple[list[str], Path]:
    """The overrides a real launch check gives a turn (the probes run the installed CLI)."""

    captured = install_fake_codex_sdk(monkeypatch, final_response=ANSWER)
    _turn(_client(tmp_path, sdk_codex_bin=CODEX), workspace, purpose="diagnosis" if workspace else "tutor_qa")
    root = Path(captured["app_config"]["cwd"])
    root.mkdir(exist_ok=True)  # the turn's scratch directory, removed after the turn
    return list(captured["app_config"]["config_overrides"]), root


@needs_codex
@pytest.mark.parametrize("route", ["text", "snapshot-diagnosis"])
def test_the_installed_codex_offers_the_turn_no_tool_at_all(tmp_path, monkeypatch, route):
    """High 1 and 3 on 0.163.0: neither a text turn nor the snapshot diagnosis
    is offered any tool (no code mode exec/wait, no shell), so an inherited
    ``allow`` rule has no command to apply to and no tool call can start a
    continuation. Read back from the model-visible input Codex builds."""

    layout = _real_layout(tmp_path, monkeypatch)
    workspace = None
    if route == "snapshot-diagnosis":
        workspace = tmp_path / "export"
        workspace.mkdir()
        (workspace / "INDEX.md").write_text("# history\n", encoding="utf-8")
    overrides, root = _real_turn_overrides(tmp_path, monkeypatch, layout, workspace=workspace)
    items = _prompt_input(layout, overrides, root)
    assert _offered_tools(items) == [], "the turn would be offered tools"
    first = next(item for item in items if item.get("type") == "message")
    assert first["role"] == "developer" and first["content"][0]["text"].startswith("You are Codex")  # incremental form
    # The control: the same read-back of the catalog as bundled offers code mode.
    pin = _lockdown().catalog_pin_path(overrides)
    bundled = subprocess.run([CODEX, "debug", "models", "--bundled"], capture_output=True, text=True, timeout=60,
                             env={"PATH": os.environ.get("PATH", ""), "HOME": str(layout["home"]),
                                  "CODEX_HOME": str(layout["codex_home"])}, cwd=tmp_path)
    control_pin = tmp_path / "bundled.json"
    control_pin.write_text(bundled.stdout, encoding="utf-8")
    control = [override.replace(json.dumps(pin), json.dumps(str(control_pin))) for override in overrides]
    assert {"functions.exec", "functions.wait"} <= set(_offered_tools(_prompt_input(layout, control, root)))


@needs_codex
def test_the_installed_codex_lists_and_expands_no_skill(tmp_path, monkeypatch):
    """High 2 through Codex's prompt-building path: a user skill linked to a
    file outside, and the bundled system skills, are listed for a default
    launch; the turn's overrides leave the context with no skill at all, and
    neither a ``$name`` mention nor a link to the SKILL.md brings it in."""

    layout = _real_layout(tmp_path, monkeypatch)
    overrides, root = _real_turn_overrides(tmp_path, monkeypatch, layout, workspace=None)
    mention = f"Use $canary-skill and [$canary-skill]({layout['outside'] / 'SKILL.md'}) now."
    items = _prompt_input(layout, overrides, root, mention)
    text = _texts(items)
    assert "<skills_instructions>" not in text and "canary-skill:" not in text
    assert _SKILL_CANARY not in json.dumps(items)
    # The control: without the turn's skill overrides the linked skill is listed.
    plain = [override for override in overrides if not override.startswith("skills.")]
    listed = _texts(_prompt_input(layout, plain, root, mention))
    assert "canary-skill: A synthetic linked skill." in listed


def test_a_skill_that_stays_listed_refuses_the_turn(tmp_path, monkeypatch):
    lockdown = _lockdown()
    skill = str(tmp_path / "skills" / "linked" / "SKILL.md")
    program, log = write_fake_codex(tmp_path / "bin", skills=[["linked", skill]])
    captured = install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    _turn(_client(tmp_path, sdk_codex_bin=str(program)))
    (launched,) = _launched(log)
    assert "skills.bundled.enabled=false" in launched
    assert any(override.startswith("skills.config=") and '"linked"' in override and json.dumps(skill) in override
               for override in launched)
    # A skill the disable cannot reach (a rule this CLI ignores) refuses.
    monkeypatch.setattr(lockdown, "skill_disable_overrides", lambda skills: ["skills.bundled.enabled=false"])
    from learnloop.ai.providers import codex as codex_module

    monkeypatch.setattr(codex_module, "skill_disable_overrides", lockdown.skill_disable_overrides)
    lockdown.clear_check_cache()
    with pytest.raises(lockdown.CodexLockdownUnavailable, match="still lists skills"):
        _turn(_client(tmp_path, sdk_codex_bin=str(program)))
    assert len(_launched(log)) == 1 and captured


def test_the_skills_parser_reads_the_rendered_catalog():
    lockdown = _lockdown()
    block = ("<skills_instructions>\n## Skills\n### Skill roots\n- `r0` = `/h/.agents/skills`\n"
             "- `r1` = `/c/skills/.system`\n### Available skills\n"
             "- imagegen: Generate images. (file: r1/imagegen/SKILL.md)\n"
             "- canary-skill: A synthetic linked skill. (file: r0/canary-skill/SKILL.md)\n</skills_instructions>")
    stdout = json.dumps([{"type": "message", "role": "developer", "content": [{"type": "input_text", "text": block}]}])
    assert lockdown.rendered_skills(stdout) == [("imagegen", "/c/skills/.system/imagegen/SKILL.md"),
                                                ("canary-skill", "/h/.agents/skills/canary-skill/SKILL.md")]
    garbled = stdout.replace("(file: r0/canary-skill/SKILL.md)", "(somewhere)")
    assert lockdown.rendered_skills(garbled) is None
    assert lockdown.rendered_skills("[]") == []


# -- 2. the snapshot diagnosis is inlined: no route keeps a shell ----------------------------


@pytest.fixture()
def seeded(tmp_path):
    from tests.diagnosis_split_helpers import build_diagnosis_vault, seed_history

    paths = build_diagnosis_vault(tmp_path / "vault")
    vault, repository = seed_history(paths)
    return paths, vault, repository


def _current(vault, store):
    from tests.test_diagnosis_history_modes import _current as current

    return current(vault, store)


def test_a_snapshot_diagnosis_on_codex_is_inlined_and_gives_the_same_structured_output(seeded, tmp_path, monkeypatch):
    """The representative snapshot fits the inline budget, the turn runs
    tool-free in a scratch directory, and the diagnosis output equals the one a
    workspace-reading client produces from the same export (a fake: no model)."""

    from learnloop.ai.chatgpt_plan.workspace import INSTRUCTIONS_INLINE
    from learnloop.attempts.grading import resolved_rubric
    from learnloop.diagnosis.split.diagnoser import run_diagnosis
    from learnloop.diagnosis.split.history import VaultHistoryStore
    from learnloop.diagnosis.split.settings import DiagnosisSettings

    from tests.codex_cli_fakes import stub_isolation_probe
    from tests.diagnosis_fakes import ReviewFakeClient

    _paths, vault, repository = seeded
    store = VaultHistoryStore(vault, repository)
    item, current = _current(vault, store)
    rubric = resolved_rubric(vault, item)
    reference_client = ReviewFakeClient(workspace=True)
    reference = run_diagnosis(reference_client, vault=vault, item=item, rubric=rubric, store=store,
                              current=current, settings=DiagnosisSettings(), mode="snapshot")
    assert reference.status == "completed"

    # The Codex fake answers as the workspace-reading fake would, from the
    # export rebuilt out of the inlined blocks alone.
    seen: dict[str, Any] = {}
    rebuilt = tmp_path / "rebuilt"

    def answer(prompt: str) -> str:
        head, _sep, inline = prompt.partition(f"\n\n{INSTRUCTIONS_INLINE}\n\n")
        files = dict(re.findall(r'<workspace_file path="([^"]+)">\n(.*?)\n</workspace_file>', inline, re.S))
        seen.update(prompt=prompt, files=files)
        for relative, text in files.items():
            (rebuilt / relative).parent.mkdir(parents=True, exist_ok=True)
            (rebuilt / relative).write_text(text, encoding="utf-8")
        fake = ReviewFakeClient(workspace=True)
        from learnloop.diagnosis.split.contract import proposal_model_for

        request = StructuredRequest(purpose="diagnosis", prompt=head, result_model=proposal_model_for("snapshot"),
                                    workspace=rebuilt)
        return fake.complete(request).model_dump_json()

    captured = install_fake_codex_sdk(monkeypatch, respond=answer)
    client = _client(tmp_path, sdk_codex_bin="/usr/bin/codex-for-test")
    stub_isolation_probe(monkeypatch, client)
    outcome = run_diagnosis(client, vault=vault, item=item, rubric=rubric, store=store, current=current,
                            settings=DiagnosisSettings(), mode="snapshot")

    assert outcome.status == reference.status == "completed"
    assert outcome.proposal == reference.proposal
    assert outcome.unknown_id_count == reference.unknown_id_count == 0
    # Every export file was inlined, within the budget, and recorded as read.
    assert sorted(seen["files"]) == reference_client.workspace_files[-1]
    assert len(seen["prompt"]) < SdkCodexClient.INLINE_WORKSPACE_MAX_CHARS
    assert outcome.receipt["snapshot"]["served"]["entry_count"] == len(seen["files"])
    assert outcome.receipt["snapshot"]["opened"] == sorted(seen["files"]) or \
        set(outcome.receipt["snapshot"]["opened"]) == set(seen["files"])
    # Tool-free, in a scratch directory: never the export, never a shell.
    root = Path(captured["app_config"]["cwd"])
    assert root.name.startswith("learnloop-isolated-turn-")
    assert "features.shell_tool=false" in captured["app_config"]["config_overrides"]


def test_an_export_over_the_inline_budget_refuses_before_launch(tmp_path, monkeypatch):
    from tests.codex_cli_fakes import stub_isolation_probe

    captured = install_fake_codex_sdk(monkeypatch, final_response=ANSWER)
    client = _client(tmp_path, sdk_codex_bin="/usr/bin/codex-for-test")
    stub_isolation_probe(monkeypatch, client)
    monkeypatch.setattr(SdkCodexClient, "INLINE_WORKSPACE_MAX_CHARS", 100)
    workspace = tmp_path / "export"
    workspace.mkdir()
    (workspace / "INDEX.md").write_text("x" * 500, encoding="utf-8")
    with pytest.raises(CodexUnavailable, match="cannot be inlined"):
        _turn(client, workspace, purpose="diagnosis")
    assert "app_config" not in captured


# -- 4. every process-launch site is on an approved list ---------------------------------

_LAUNCH = {
    "subprocess": {"Popen", "run", "call", "check_call", "check_output", "getoutput", "getstatusoutput"},
    "os": {"system", "popen", "execv", "execve", "execvp", "execvpe", "execl", "execle", "execlp", "execlpe",
           "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe",
           "posix_spawn", "posix_spawnp", "startfile", "forkpty", "fork"},
    "asyncio": {"create_subprocess_exec", "create_subprocess_shell"},
    "pty": {"spawn", "fork"},
}
_ANY_RECEIVER = {"subprocess_exec", "subprocess_shell"}


class _LaunchSweep(ast.NodeVisitor):
    """Every reference (not only calls) to a process-launching function, through
    any import alias or ``getattr``, with its enclosing scope; whatever the
    arguments are (a list in a variable, a bare name), the site is listed."""

    def __init__(self, relative: str):
        self.relative = relative
        self.stack: list[str] = []
        self.modules: dict[str, str] = {}
        self.names: dict[str, str] = {}
        #: One entry per reference (frozen round, verify uuB5X5 Low 5): a second
        #: launch inside an approved scope is a second entry, not the same one.
        self.sites: list[tuple[str, str, str]] = []

    def _owner(self) -> str:
        return ".".join(self.stack) or "<module>"

    def _scope(self, node):
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    visit_FunctionDef = visit_AsyncFunctionDef = visit_ClassDef = _scope

    def visit_Import(self, node):
        for alias in node.names:
            top = alias.name.split(".")[0]
            if top in _LAUNCH:
                self.modules[alias.asname or top] = top
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = (node.module or "").split(".")[0]
        if module in _LAUNCH and node.level == 0:
            for alias in node.names:
                if alias.name == "*" or alias.name in _LAUNCH[module]:
                    self.names[alias.asname or alias.name] = f"{module}.{alias.name}"
                    self.sites.append((self.relative, self._owner(), f"import {module}.{alias.name}"))
        self.generic_visit(node)

    def visit_Assign(self, node):
        # An indirect alias (``run = subprocess.run``; ``launch = run``): the
        # names bound to a launch reference count as launch references too.
        target = self._launch_target(node.value)
        self.generic_visit(node)
        if target is not None:
            for name in node.targets:
                if isinstance(name, ast.Name):
                    self.names[name.id] = target

    def _launch_target(self, value) -> str | None:
        if isinstance(value, ast.Name) and value.id in self.names:
            return self.names[value.id]
        if isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name) and value.value.id in self.modules:
            module = self.modules[value.value.id]
            if value.attr in _LAUNCH[module]:
                return f"{module}.{value.attr}"
        return None

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and node.id in self.names:
            self.sites.append((self.relative, self._owner(), self.names[node.id]))

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id in self.modules:
            module = self.modules[node.value.id]
            if node.attr in _LAUNCH[module]:
                self.sites.append((self.relative, self._owner(), f"{module}.{node.attr}"))
        if node.attr in _ANY_RECEIVER:
            self.sites.append((self.relative, self._owner(), f"*.{node.attr}"))
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == "getattr" and node.args:
            base = node.args[0]
            if isinstance(base, ast.Name) and base.id in self.modules:
                self.sites.append((self.relative, self._owner(), f"getattr({self.modules[base.id]})"))
        self.generic_visit(node)


def _launch_sites(text: str, relative: str = "snippet.py") -> list[tuple[str, str, str]]:
    sweep = _LaunchSweep(relative)
    sweep.visit(ast.parse(text))
    return sweep.sites


#: Every process-launch reference in the Python LearnLoop ships or runs
#: (``src``, ``scripts``, ``integrations``), each reviewed (security stage
#: codex-tool-lockdown, round 3). A new one fails until it is reviewed and added.
APPROVED_LAUNCH_SITES = {
    ("scripts/benchmark_chatgpt_plan_latency.py", "_install_fake_codex_sdk.FakeCodex.__enter__", "subprocess.Popen"),
    ("scripts/benchmark_chatgpt_plan_latency.py", "_install_fake_codex_sdk.FakeCodex.__init__", "subprocess.Popen"),
    ("scripts/benchmark_chatgpt_plan_latency.py", "main", "subprocess.run"),
    # Storage S0's owner-run landing: read-only `git ls-files` / `git ls-tree HEAD` /
    # `git rev-parse --verify HEAD` / `git cat-file blob` in the owner's checkout
    # (fixed argv, no shell), no model call.
    ("scripts/s0_landing.py", "_git", "subprocess.run"),
    ("src/learnloop/ai/chatgpt_plan/store.py", "_fsync_directory", "getattr(os)"),
    ("src/learnloop/ai/providers/codex.py", "SdkCodexClient.__init__", "subprocess.Popen"),  # annotation
    # The launch check's probes: the resolved Codex CLI, never a model call.
    ("src/learnloop/ai/providers/codex.py", "SdkCodexClient._codex_probe", "subprocess.Popen"),
    ("src/learnloop/ai/providers/codex.py", "_read_checkout_revision", "subprocess.run"),  # git rev-parse
    ("src/learnloop/ai/providers/codex.py", "_stop_probe", "subprocess.Popen"),  # annotation
    # The legacy HTTP transport's startup command: refused before it (round 2, H3).
    ("src/learnloop/ai/providers/codex.py", "default_startup", "getattr(subprocess)"),
    ("src/learnloop/ai/providers/codex.py", "default_startup", "subprocess.Popen"),  # x2: annotation + call
    ("src/learnloop/cli/ai_compare.py", "tracked_database_reason", "subprocess.run"),
    ("src/learnloop/content/authoring/concept_animation.py", "manim_runtime", "subprocess.run"),
    ("src/learnloop/content/authoring/concept_animation.py", "provision_animation_venv", "subprocess.run"),
    ("src/learnloop/content/authoring/concept_animation.py", "render_scene", "subprocess.run"),
    ("src/learnloop/content/authoring/pf_sandbox.py", "check_generator_answers", "subprocess.run"),
    # E1's harness (experiments, owner-run): the metered worker under its scope,
    # nvidia-smi probes, the env's version listing. Fixed argv lists, no shell.
    ("src/learnloop/experiments/contextual_embeddings/e1/gpu_meter.py", "supervise", "subprocess.Popen"),
    ("src/learnloop/experiments/contextual_embeddings/e1/run.py", "environment_versions", "subprocess.run"),
    ("src/learnloop/experiments/contextual_embeddings/e1/worker.py", "run_nvidia_smi", "subprocess.run"),
    # Local contextual retrieval P1a (moved from E1): the launcher's
    # systemd-run scope under the meter (an argv list built by launcher.py),
    # nvidia-smi probes, and the owner-run setup's uv venv / uv pip install /
    # pinned download / epoch probe in the separate env (argv lists, no shell).
    ("src/learnloop/local_embeddings/gpu_meter.py", "supervise", "subprocess.Popen"),
    ("src/learnloop/local_embeddings/setup.py", "run_setup", "subprocess.run"),
    ("src/learnloop/local_embeddings/worker.py", "run_nvidia_smi", "subprocess.run"),
    # Local retrieval P2 (reviewed): the base download through the separate environment's own
    # interpreter (an argv list, no shell, nothing that can start Codex), and the query student's
    # process in its own capped systemd scope (an argv list, no shell, start_new_session).
    ("src/learnloop/source_retrieval/query_student.py", "setup_bases", "subprocess.run"),
    ("src/learnloop/source_retrieval/student_encoder.py", "_spawn", "subprocess.Popen"),
    ("src/learnloop/content/authoring/pf_sandbox.py", "run_equivalence_checks", "subprocess.run"),
    ("src/learnloop/content/authoring/pf_sandbox.py", "run_generator_tests", "subprocess.run"),
    ("src/learnloop/content/authoring/pf_sandbox.py", "run_sandboxed_python", "subprocess.run"),
    ("src/learnloop/ingest/extractors/glm_text_layer.py", "pdfium_worker", "getattr(subprocess)"),
    ("src/learnloop/ingest/extractors/glm_text_layer.py", "pdfium_worker", "subprocess.run"),
    ("src/learnloop/ingest/extractors/marker_worker.py", "_exited", "subprocess.Popen"),
    ("src/learnloop/ingest/extractors/marker_worker.py", "_own_process_group", "getattr(subprocess)"),
    ("src/learnloop/ingest/extractors/marker_worker.py", "_send", "subprocess.Popen"),
    ("src/learnloop/ingest/extractors/marker_worker.py", "_stop", "subprocess.Popen"),
    ("src/learnloop/ingest/extractors/marker_worker.py", "_wait", "subprocess.Popen"),
    ("src/learnloop/ingest/extractors/marker_worker.py", "run_marker", "subprocess.Popen"),
    ("src/learnloop/ops/pf_verify.py", "VerifierEnv", "subprocess.run"),
    ("src/learnloop/projects/git.py", "run_git", "subprocess.run"),
    ("src/learnloop_mobile/doctor.py", "_command", "subprocess.run"),
    ("src/learnloop_sidecar/handlers/cli.py", "run_cli_command", "subprocess.run"),
}


#: How many references each approved site holds (1 unless named here). The list
#: counts references, not scopes (frozen round, verify uuB5X5 Low 5): a second
#: launch added inside an approved function changes its count and fails.
APPROVED_LAUNCH_COUNTS: dict[tuple[str, str, str], int] = {
    ("src/learnloop/ai/providers/codex.py", "default_startup", "subprocess.Popen"): 2,
}


def _approved() -> Counter:
    return Counter({site: APPROVED_LAUNCH_COUNTS.get(site, 1) for site in APPROVED_LAUNCH_SITES})


def _unapproved(found: Counter, approved: Counter) -> tuple[list[Any], list[Any]]:
    """(references beyond the approved count, approved references that are gone)."""

    return sorted((found - approved).items()), sorted((approved - found).items())


def test_a_second_launch_inside_an_approved_scope_is_not_approved():
    approved = Counter({("snippet.py", "run_git", "subprocess.run"): 1})
    one = Counter(_launch_sites("import subprocess\ndef run_git(args):\n    return subprocess.run(args)\n"))
    assert _unapproved(one, approved) == ([], [])
    two = Counter(_launch_sites(
        "import subprocess\n"
        "def run_git(args):\n"
        "    command = ['codex', 'app-server']\n"
        "    subprocess.run(command)\n"
        "    return subprocess.run(args)\n"
    ))
    assert _unapproved(two, approved) == ([(("snippet.py", "run_git", "subprocess.run"), 1)], [])


def test_an_indirect_alias_of_a_launch_function_is_a_launch_reference():
    sites = Counter(_launch_sites(
        "import subprocess\n"
        "run = subprocess.run\n"
        "def f(cmd):\n"
        "    launch = run\n"
        "    launch(cmd)\n"
        "    other = launch\n"
        "    return other(cmd)\n"
    ))
    assert sites == Counter({("snippet.py", "<module>", "subprocess.run"): 1,
                             ("snippet.py", "f", "subprocess.run"): 4})


def test_the_launch_sweep_sees_aliases_variables_and_references():
    """The verify's three missed shapes, plus a reference passed as a value and getattr."""

    sites = set(_launch_sites(
        "from subprocess import Popen as launch\n"
        "launch(['codex', 'app-server'])\n"
        "import subprocess as sp\n"
        "def f():\n"
        "    sp.Popen(['codex', 'app-server'])\n"
        "def g(subprocess=None):\n"
        "    import subprocess\n"
        "    command = ['codex', 'app-server']\n"
        "    subprocess.Popen(command)\n"
        "def h(run=sp.run):\n"
        "    return getattr(sp, 'Popen')\n"
        "async def k(loop):\n"
        "    await loop.subprocess_exec(object, 'codex')\n"
    ))
    assert sites == {
        ("snippet.py", "<module>", "import subprocess.Popen"),
        ("snippet.py", "<module>", "subprocess.Popen"),
        ("snippet.py", "f", "subprocess.Popen"),
        ("snippet.py", "g", "subprocess.Popen"),
        ("snippet.py", "h", "subprocess.run"),  # a default value: listed with its function
        ("snippet.py", "h", "getattr(subprocess)"),
        ("snippet.py", "k", "*.subprocess_exec"),
    }


def test_every_process_launch_site_is_approved():
    """Low 4: every process-launch reference in ``src``, ``scripts`` and
    ``integrations`` is on :data:`APPROVED_LAUNCH_SITES`; the Rust shell
    starts exactly one process (the sidecar)."""

    found: Counter = Counter()
    for directory in ("src", "scripts", "integrations"):
        for path in sorted((ROOT / directory).rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            found.update(_launch_sites(path.read_text(encoding="utf-8"), str(path.relative_to(ROOT))))
    extra, gone = _unapproved(found, _approved())
    assert extra == [], "an unreviewed process-launch reference (a new one, or another inside an approved scope)"
    assert gone == [], "an approved reference is gone: lower its count or remove it from the list"
    rust = sorted(
        (str(path.relative_to(ROOT)), line.strip())
        for path in (ROOT / "apps" / "learnloop-tauri" / "src-tauri" / "src").rglob("*.rs")
        for line in path.read_text(encoding="utf-8").splitlines() if "Command::new" in line
    )
    assert rust == [("apps/learnloop-tauri/src-tauri/src/sidecar.rs", "let mut command = Command::new(&spec.program);")]
