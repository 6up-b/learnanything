"""``learnloop sim probe-validation`` and ``sim probe-pilot`` on a vault as it opens by default.

The planted-type simulation drives the opening diagnostic episode with parametric instruments. A default vault
never opens that episode (placement) and has a model write its probes (FG1), so the simulation cannot run there.
An empty report used to pass (``all()`` over nothing) and both commands printed PASS with exit 0."""

from __future__ import annotations

import json
import tempfile

import pytest
from typer.testing import CliRunner

from learnloop.sim.diagnostic_validation import ValidationReport, run_probe_validation

from tests.helpers import create_basic_vault

NEEDED_OFF = ("placement.enabled", "followup.generate_and_serve")


@pytest.fixture
def default_vault(tmp_path, monkeypatch):
    # The commands make their run directory with mkdtemp: keep it under this test's directory.
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    root = tmp_path / "vault"
    create_basic_vault(root)
    return root


def test_a_report_with_no_results_does_not_pass():
    assert not ValidationReport().passes(label_accuracy_threshold=0.6, action_accuracy_threshold=0.6)


def test_the_simulation_refuses_a_default_vault_and_names_the_switches(default_vault, tmp_path):
    report = run_probe_validation(default_vault, tmp_path / "runs", planted_types=("unfamiliar",), seeds=(11,))
    assert report.results == []
    assert report.refusal is not None
    assert tuple(report.refusal.switches) == NEEDED_OFF
    assert not report.passes(label_accuracy_threshold=0.0, action_accuracy_threshold=0.0)
    payload = report.as_dict()
    assert payload["refusal"]["switches"] == list(NEEDED_OFF)
    assert "simulation" in payload["refusal"]["message"]


@pytest.mark.parametrize("command", ["probe-validation", "probe-pilot"])
def test_the_command_on_a_default_vault_fails_and_says_what_it_could_not_run(default_vault, command):
    from learnloop.cli import app

    args = ["sim", command, "--vault", str(default_vault), "--seeds", "1", "--planted", "unfamiliar"]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 1, result.output
    assert "PASS" not in result.output
    for switch in NEEDED_OFF:
        assert switch in result.output
    assert "the simulation's limit, not the vault's" in result.output

    as_json = CliRunner().invoke(app, [*args, "--json"])
    assert as_json.exit_code == 1, as_json.output
    payload = json.loads(as_json.output)
    gate = payload if command == "probe-validation" else payload["entry_gate"]
    assert gate["passes"] is False
    assert gate["results"] == []
    assert gate["refusal"]["switches"] == list(NEEDED_OFF)


def test_with_the_named_switches_off_the_command_runs(default_vault):
    from learnloop.cli import app

    sets = [part for switch in NEEDED_OFF for part in ("--set", f"{switch}=false")]
    result = CliRunner().invoke(
        app,
        ["sim", "probe-validation", "--vault", str(default_vault), "--seeds", "1", "--planted", "unfamiliar",
         "--json", *sets],
    )
    payload = json.loads(result.output)
    assert payload["refusal"] is None
    assert len(payload["results"]) == 1
    assert result.exit_code == (0 if payload["passes"] else 1), result.output
