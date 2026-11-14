from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.config import LearnLoopConfig
from learnloop.learner.recall_calibration import (
    SEVERITY_EXAMPLES,
    assert_recall_calibration_bands,
    format_recall_calibration_table,
    run_recall_calibration_harness,
)
from tests.helpers import allow_below_floor


def test_recall_calibration_examples_are_config_backed():
    config = LearnLoopConfig()

    assert config.recall_coverage.severity_examples == SEVERITY_EXAMPLES
    assert list(config.recall_coverage.severity_examples) == [
        "first_dont_know",
        "second_same_item_dont_know",
        "second_same_facet_dont_know",
        "hinted_dont_know",
        "arithmetic_slip",
        "ambiguous_item",
    ]
    assert config.recall_coverage.severity_examples["arithmetic_slip"].expected_error_type == "arithmetic_slip"


@pytest.mark.xfail(
    strict=True,
    reason="ledger D-24: the harness calibrates the mvp-0.6 error vocabulary and severity bands its config "
    "examples name; that legacy model is gone, so it now runs the head's (mechanism names, mechanism severities)",
)
def test_recall_calibration_harness_is_deterministic_and_in_band(tmp_path):
    # The harness builds its scenario vaults at mvp-0.6, below the floor (ledger D-24).
    allow_below_floor(tmp_path)
    first = run_recall_calibration_harness(tmp_path / "first")
    second = run_recall_calibration_harness(tmp_path / "second")

    assert [row.as_dict() for row in first] == [row.as_dict() for row in second]
    assert [row.scenario for row in first] == list(SEVERITY_EXAMPLES)
    assert_recall_calibration_bands(first)
    table = format_recall_calibration_table(first)
    assert table.splitlines()[0].startswith("scenario | error_type | event_severity")
    assert "second_same_item_dont_know | recall_failure | 1.0000" in table
    assert "second_same_facet_dont_know | recall_failure" in table
    assert "ambiguous_item | recall_failure" in table
    assert "0.700->0.760" in table


@pytest.mark.xfail(
    strict=True,
    reason="ledger D-24: the harness calibrates the mvp-0.6 error vocabulary and severity bands its config "
    "examples name; that legacy model is gone, so it now runs the head's (mechanism names, mechanism severities)",
)
def test_recall_calibration_cli_json_and_assert_mode(tmp_path):
    allow_below_floor(tmp_path)  # the harness's scratch vaults are at mvp-0.6 (ledger D-24)
    result = CliRunner().invoke(app, ["recall-calibration", "--json", "--assert"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["version"] == 1
    assert [row["scenario"] for row in payload["rows"]] == list(SEVERITY_EXAMPLES)
    assert all(row["severity_in_band"] for row in payload["rows"])
