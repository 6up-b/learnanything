"""Reader workbench RW2c: switched off, byte-identical to the base (spec_reader_workbench_v1 §5.10; stage note 4).

With ``workbench.help_outcomes_enabled``, ``.examples_enabled``,
``.compare_methods_enabled`` and ``.passage_draw_enabled`` all off, one help
sequence (``tests/rw2c_base_sequence.py``) gives the hint writer exactly the
prompts, the chooser exactly the states, and the workbench exactly the
payloads, rows and config DTO that the base code (``7e7bdff1b``) gives. With
them on, the same sequence differs where RW2c acts (so the pin is not
vacuous). Every new key is classified in the parameter registry. Fakes only.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from tests.hint_fakes import ChooserFake, WriterFake, prefer
from tests.rw2c_base_sequence import SWITCHES, BridgeFake
from tests.workbench_help_fakes import call, help_rows, open_problem, run_job, sidecar, wb_answer

ROOT = Path(__file__).resolve().parents[1]
BASE = "7e7bdff1b"


def _run_sequence(code_root: Path, vault_dir: Path) -> dict:
    script = code_root / "tests" / "rw2c_base_sequence.py"
    if not script.exists():
        shutil.copy(ROOT / "tests" / "rw2c_base_sequence.py", script)
    env = {**os.environ, "PYTHONPATH": str(code_root / "src")}
    done = subprocess.run([sys.executable, "-m", "tests.rw2c_base_sequence", str(vault_dir)], cwd=code_root,
                          env=env, capture_output=True, text=True, timeout=600)
    assert done.returncode == 0, done.stderr[-3000:]
    return json.loads(done.stdout.strip().splitlines()[-1])


def test_with_all_four_switches_off_the_sequence_equals_the_base_codes(tmp_path):
    if shutil.which("git") is None or subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", BASE],
                                                     capture_output=True).returncode != 0:
        pytest.skip(f"git or commit {BASE} is not available")
    base = tmp_path / "base"
    base.mkdir()
    archive = subprocess.run(["git", "-C", str(ROOT), "archive", BASE, "src", "tests", "migrations"],
                             capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(base)], input=archive, check=True)
    at_base = _run_sequence(base, tmp_path / "vault-base")
    import learnloop

    at_tip = _run_sequence(Path(learnloop.__file__).resolve().parents[2], tmp_path / "vault-tip")
    # The pin covers what RW2c could change: the writer's prompts, the
    # chooser's states, the payloads (hints, bridges, the restored state).
    assert len(at_base["writer_contexts"]) == 2 and len(at_base["chooser_states"]) >= 2
    assert at_base["payloads"]["bridge_1"]["result"]["status"] == "ready"
    for key in ("writer_contexts", "writer_prompts", "check_prompts", "chooser_states", "payloads", "rows",
                "config_workbench"):
        assert at_tip[key] == at_base[key], key


def test_switched_on_the_same_sequence_carries_rw2c(tmp_path):
    """The pin is not vacuous: on, the second hint's writer and chooser get
    the help-outcome lines, the bridge logs its draw and the hint result
    names its example job."""

    writer = WriterFake([wb_answer] * 8)
    chooser = ChooserFake(prefer("next_step@L3", 0.6))
    paths, ctx, _session = sidecar(tmp_path, writer=writer, chooser=chooser)
    ctx.workbench_bridge_provider = BridgeFake()
    ctx.passage_draw_seed = "seed-pin"
    wb, _chains = open_problem(ctx, origin="reader", entry="work_through")
    run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    first = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    assert "exampleJobId" in first
    call(ctx, "workbench.help_job", {"jobId": first["bridgeJobId"]})
    # Before any help on the facet only the check's guess is history: where the work goes off.
    assert [line["line"] for line in writer.contexts[0]["workbench"]["help_outcomes"]] == ["label", "goes_off"]
    run_job(ctx, call(ctx, "workbench.suggest_help", {"sessionId": wb}))
    run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    lines = writer.contexts[-1]["workbench"]["help_outcomes"]
    assert lines[0]["line"] == "label" and any(line["line"] == "help_outcome" for line in lines)
    assert "help_outcomes" in json.dumps(chooser.calls[-1]["state"], default=str)
    [bridge, *_rest] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "bridge"]
    assert bridge["seed"] == "seed-pin" and bridge["propensity"] is not None
    from learnloop_sidecar.context import config_dto

    help_dto = config_dto(ctx.require_vault()[0])["workbench"]["help"]
    assert (help_dto["examples"], help_dto["compareMethods"], help_dto["passageDraw"]) == (True, True, True)


def test_each_switch_off_drops_only_its_own_part(tmp_path):
    from learnloop_sidecar.context import config_dto

    for name, dto_key in (("examples_enabled", "examples"), ("compare_methods_enabled", "compareMethods"),
                          ("passage_draw_enabled", "passageDraw")):
        _paths, ctx, _session = sidecar(tmp_path / name, f"[workbench]\n{name} = false\n")
        help_dto = config_dto(ctx.require_vault()[0])["workbench"]["help"]
        assert dto_key not in help_dto
        assert {"examples", "compareMethods", "passageDraw"} - {dto_key} <= set(help_dto)


def test_every_new_key_is_classified_in_the_parameter_registry():
    from learnloop.params.parameter_registry import classify_config_path

    for name in SWITCHES:
        rule = classify_config_path(f"workbench.{name}")
        assert rule is not None, name
        assert (rule.kind, rule.param_class) == ("structural", "operational"), name
        assert "help-outcome lines" in rule.rationale, name
