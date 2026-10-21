"""RW5a's kill switch restores the Reader of before RW5a byte for byte (spec §8.6, W3, U13).

With ``figures.enabled`` off, the Reader's prompt contract (its intent box's
palettes included) is exactly what the base tree (``e14b4e4ff``) produced:
no ``figures`` key and no "make this explorable". The golden file was
recorded on that tree, before any RW5a code existed (an export of it, with
``RW5A_WRITE_GOLDEN=1``); every figure RPC then refuses and no route is
called (tests/test_figures_rpc.py).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from tests.library_ask_fixtures import build_library_vault, call, context, set_config

GOLDEN = Path(__file__).parent / "fixtures" / "figures_switch_off.json"
WRITE = os.environ.get("RW5A_WRITE_GOLDEN") == "1"


def _record(tmp_path: Path, *, enabled: bool | None) -> dict:
    paths, _repository, _spans = build_library_vault(tmp_path / "vault")
    if enabled is not None:
        set_config(paths, "figures", enabled=enabled)
    ctx = context(paths.root)
    return {"contract": call(ctx, "reader.prompt_contract", {})}


def test_figures_off_is_the_base_reader_contract_byte_for_byte(tmp_path):
    recorded = _record(tmp_path, enabled=None if WRITE else False)
    if WRITE:
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(recorded, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        pytest.skip("golden written")
    assert recorded == json.loads(GOLDEN.read_text(encoding="utf-8"))


def test_figures_on_adds_only_its_key_and_its_action(tmp_path):
    if WRITE:
        pytest.skip("the golden is written by the switch-off case")
    recorded = _record(tmp_path, enabled=True)["contract"]
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))["contract"]
    assert recorded.pop("figures") == {"predictions": True, "region": True, "revisions": True}
    added = []
    for group in recorded["intent"]["palette"]:
        kept = [action for action in group["actions"] if action["effect"] != {"kind": "figure"}]
        added += [action["id"] for action in group["actions"] if action["effect"] == {"kind": "figure"}]
        group["actions"] = kept
    assert added == ["make_explorable"]
    assert recorded == golden


# ---------------------------------------------------------------------------
# Fix round 3: the Reader report with figures off is the base report
# ---------------------------------------------------------------------------

REPORT_GOLDEN = Path(__file__).parent / "fixtures" / "figures_switch_off_report.json"


def _seed_figure_rows(repository) -> None:
    """One shown figure and one missed prediction with its explanation (the
    rows the figures block counts), written straight to migration 216's tables."""

    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO interactive_figures (id, extraction_id, origin, spec_json, spec_version, kind, verification, "
            "prompt_version, input_hash, created_at) VALUES ('fig_off', 'ext1', 'selection', '{}', 'ifs-v1', "
            "'illustrative', 'illustrative', 'figure_author.v1', 'hash_off', ?)", ("2026-01-01T00:10:00Z",))
        connection.execute(
            "INSERT INTO figure_predictions (id, figure_id, extraction_id, prediction_index, learner_answer, "
            "observed_json, matched, explanation_text, created_at) VALUES ('fpr_off', 'fig_off', 'ext1', 0, 'rises', "
            "'{}', 0, 'p sets it', ?)", ("2026-01-01T00:11:00Z",))
        connection.commit()


def _report(tmp_path: Path, *, figures: bool | None) -> dict:
    from datetime import timedelta

    from learnloop.reader.reader_report import build_reader_report
    from tests.helpers import NOW
    from tests.test_reader_report import _seed

    _vault, repo, _old = _seed(tmp_path)
    if figures is None:  # the base tree: no figure tables, no switch
        return build_reader_report(repo.sqlite_path, now=NOW + timedelta(minutes=60))
    _seed_figure_rows(repo)
    return build_reader_report(repo.sqlite_path, now=NOW + timedelta(minutes=60), figures_enabled=figures)


def test_figures_off_is_the_base_reader_report(tmp_path):
    """Recorded on an export of e14b4e4ff (RW5A_WRITE_GOLDEN=1, -o pythonpath=<export>/src); here the
    vault also has a figure and a prediction, which the switched-off report never reads."""

    recorded = _report(tmp_path, figures=None if WRITE else False)
    if WRITE:
        REPORT_GOLDEN.write_text(json.dumps(recorded, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                                 encoding="utf-8")
        pytest.skip("report golden written")
    assert json.loads(json.dumps(recorded)) == json.loads(REPORT_GOLDEN.read_text(encoding="utf-8"))


def test_figures_on_adds_only_the_figures_block_to_the_report(tmp_path):
    if WRITE:
        pytest.skip("the golden is written by the switch-off case")
    recorded = json.loads(json.dumps(_report(tmp_path, figures=True)))
    assert recorded.pop("figures") == {"built": {"illustrative": 1}, "unsupported_by_kind": {}, "revisions": 0,
                                       "regions": 0, "predictions": 1, "predictions_missed": 1, "what_changed": 1}
    assert recorded == json.loads(REPORT_GOLDEN.read_text(encoding="utf-8"))


def test_the_report_cli_follows_the_switch(tmp_path):
    from typer.testing import CliRunner

    from learnloop.cli import app
    from tests.test_reader_report import _seed

    if WRITE:
        pytest.skip("the golden is written by the switch-off case")
    vault, repo, _old = _seed(tmp_path)
    _seed_figure_rows(repo)
    set_config(_Paths(vault.root), "figures", enabled=False)
    seen = {}
    for enabled in (False, True):
        if enabled:
            _flip(vault.root)
        result = CliRunner().invoke(app, ["reader", "report", "--vault", str(vault.root), "--json"])
        assert result.exit_code == 0, result.output
        seen[enabled] = "figures" in json.loads(result.output)
    assert seen == {False: False, True: True}


class _Paths:
    def __init__(self, root: Path) -> None:
        self.root = root


def _flip(root: Path) -> None:
    config = root / "learnloop.toml"
    config.write_text(config.read_text(encoding="utf-8").replace("[figures]\nenabled = false",
                                                                 "[figures]\nenabled = true"), encoding="utf-8")
