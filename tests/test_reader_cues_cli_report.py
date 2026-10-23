"""Reader workbench RW3b: the owner-run discovery command and the cue report (spec §6.4, §15).

``learnloop reader cues discover --dry-run`` lists the targets and their
shortlists (keyword matches only), calls nothing and writes nothing; a real
run with no model reachable (the suite's ``LEARNLOOP_CUE_JUDGE_MODELS=off``)
writes nothing and says why. ``learnloop reader report`` gains the discovered
cues' funnel only once impressions exist: reasons, kinds, responses, the
share of new-application marks, and the holdout's estimate (shown vs held
out, next attempt on the cue's LO, weighted by 1/propensity), which leaves
density, spacing and restored-line suppressions out. Fakes only.
"""

from __future__ import annotations

import hashlib
import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.reader.reader_report import _holdout_estimate, build_reader_report
from tests.passage_cue_fakes import build_cue_vault


def _digest(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_the_dry_run_lists_targets_and_shortlists_and_writes_nothing(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    repository.connection().close()
    before = _digest(paths.sqlite_path)
    result = CliRunner().invoke(app, ["reader", "cues", "discover", "--vault", str(paths.root), "--source",
                                      "src_text", "--dry-run", "--json"])
    assert result.exit_code == 0, result.output
    out = json.loads(result.output)
    assert out["dry_run"] is True and out["calls"] == 0
    assert out["targets"] and all(entry["status"] == "dry_run" for entry in out["targets"])
    assert out["targets"][0]["manifest"]["candidates"] >= 1
    assert _digest(paths.sqlite_path) == before


def test_a_real_run_with_no_model_reachable_writes_no_link(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    result = CliRunner().invoke(app, ["reader", "cues", "discover", "--vault", str(paths.root), "--source",
                                      "src_text", "--json"])
    assert result.exit_code == 0, result.output
    out = json.loads(result.output)
    assert out["calls"] == 0 and {entry["status"] for entry in out["targets"]} == {"unavailable"}
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM passage_links").fetchone()[0] == 0


def test_an_unknown_source_is_refused(tmp_path):
    paths, _repository, _spans = build_cue_vault(tmp_path / "v")
    result = CliRunner().invoke(app, ["reader", "cues", "discover", "--vault", str(paths.root), "--source", "nope",
                                      "--dry-run"])
    assert result.exit_code == 1 and json.loads(result.output)["status"] == "invalid"


def _impression(connection, impression_id: str, *, link_id: str | None, shown: int, reason: str | None,
                propensity: float | None, kind: str = "distinction", response: str = "none",
                created_at: str = "2026-10-10T10:00:00Z", lo: str = "lo_matrices") -> None:
    connection.execute(
        "INSERT INTO reader_cue_impressions (id, cue_id, link_id, extraction_id, span_id, learning_object_id, kind, "
        "visit_id, shown, suppressed_reason, propensity, seed, p_open, p_open_source, density, response, created_at, "
        "responded_at) VALUES (?, ?, ?, 'ext_text', 't3', ?, ?, 'v', ?, ?, ?, NULL, 1.0, 'x', 'normal', ?, ?, ?)",
        (impression_id, f"c_{impression_id}", link_id, lo, kind, shown, reason, propensity, response, created_at,
         None if response == "none" else created_at))


def test_the_report_counts_discovered_impressions_only_once_there_are_some(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    assert "discovered" not in build_reader_report(paths.sqlite_path)["cues"]
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO judgment_ledger (id, created_at, task, left_kind, left_id, right_kind, right_id, judge, "
            "judge_model, prompt_version, input_hash, verdict, score, rationale) VALUES ('pcj', "
            "'2026-10-01T00:00:00Z', 'passage_cue', 'cue_target', 'x', 'reader_span', 'ext_text/t3', 'llm', 'm', "
            "'v', 'h', 'clarifies_distinction', 1.0, '{}')")
        connection.execute(
            "INSERT INTO passage_links (id, extraction_id, span_id, target_kind, target_id, relation, quote, "
            "pick_rank, ledger_id, state_key, model, prompt_version, created_at) VALUES ('plink', 'ext_text', 't3', "
            "'misconception', 'm', 'clarifies_distinction', 'q', 1, 'pcj', 'k', 'm', 'v', '2026-10-01T00:00:00Z')")
        _impression(connection, "i1", link_id="plink", shown=1, reason=None, propensity=0.9, response="opened")
        _impression(connection, "i2", link_id="plink", shown=0, reason="holdout", propensity=0.1)
        _impression(connection, "i3", link_id=None, shown=1, reason=None, propensity=None, kind="revisit")
        _impression(connection, "i4", link_id="plink", shown=0, reason="density", propensity=0.9)
        _impression(connection, "i5", link_id=None, shown=1, reason=None, propensity=None, kind="application",
                    response="fewer")
        connection.commit()
    block = build_reader_report(paths.sqlite_path)["cues"]["discovered"]
    assert block["impressions"] == 5 and block["shown"] == 3
    assert block["not_shown"] == {"holdout": 1, "density": 1}
    assert block["new_application_share"] == {"count": 1, "of": 3, "share": 0.3333}
    assert block["responses"]["opened"]["count"] == 1 and block["responses"]["fewer"]["count"] == 1
    assert block["holdout"]["shown"]["n"] == 0  # no attempt after them yet: counts only


def test_the_holdout_estimate_weights_by_propensity_and_leaves_other_suppressions_out():
    rows = [
        {"shown": True, "propensity": 0.9, "outcome": 1.0}, {"shown": True, "propensity": 0.9, "outcome": 0.0},
        {"shown": True, "propensity": 0.5, "outcome": 1.0},
        {"shown": False, "propensity": 0.1, "outcome": 0.0}, {"shown": False, "propensity": 0.5, "outcome": 1.0},
    ]
    estimate = _holdout_estimate(rows)
    shown = (1 / 0.9 + 1 / 0.5) / (2 / 0.9 + 1 / 0.5)
    held = (1 / 0.5) / (1 / 0.1 + 1 / 0.5)
    assert estimate["shown"] == {"n": 3, "links": 3, "pending": 0, "mean": round(shown, 4)}
    assert estimate["held_out"] == {"n": 2, "links": 2, "pending": 0, "mean": round(held, 4)}
    assert estimate["effect"] == round(round(shown, 4) - round(held, 4), 4)
    low, high = estimate["interval_95"]
    assert low < estimate["effect"] < high
    assert _holdout_estimate(rows[:3])["effect"] is None  # one arm empty: counts only
