"""S5 (§11.3): `learnloop sources outcomes`."""
from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.instructional.interventions import ASSOCIATIONS_LABEL, outcomes_report, record_need_served
from tests.source_service_fakes import build_service_vault, loaded, set_config


def test_the_report_groups_and_labels_associations(tmp_path):
    paths, repository = build_service_vault(tmp_path / "vault")
    vault = loaded(paths)
    record_need_served(vault, repository, {"id": "n1", "target_facets": ["facet_eigen"],
                                           "learning_object_id": "lo_matrices"}, practice_item_id="pi_eigen_1")
    report = outcomes_report(vault, repository)
    assert report["label"] == ASSOCIATIONS_LABEL and report["interventions"] == 1
    assert report["by"]["kind"]["source_exercise"]["n"] == 1
    assert report["overall"]["R_cold"]["states"] == {"right_censored_pending": 1}
    assert report["certification_gate"]["unverified_attempts"] == 0
    assert "not yet calibrated" in report["valuation"]["scale"]
    result = CliRunner().invoke(app, ["sources", "outcomes", "--json", "--vault", str(paths.root)])
    assert result.exit_code == 0 and json.loads(result.stdout)["interventions"] == 1


def test_the_report_says_when_recording_is_off(tmp_path):
    paths, repository = build_service_vault(tmp_path / "vault")
    set_config(paths, "source_service", interventions=False)
    report = outcomes_report(loaded(paths), repository)
    assert report["recording"].startswith("off") and report["interventions"] == 0
