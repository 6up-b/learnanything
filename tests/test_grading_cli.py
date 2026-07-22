"""P0.5 adjudication queue CLI (spec §5, §9.7 items 2/5).

`learnloop grading reviews` (pending, influence-ordered) / `grading adjudicate` /
`grading receipt`. Thin adapters over the landed P0.2 services; no CLI command
edits a projection table directly.
"""

from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.services.grade_resolution import quarantine_observation
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault, set_algorithm_version

CLOCK = FrozenClock(NOW)
ITEM = "pi_svd_define_001"
runner = CliRunner()


def _p0_vault(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.8")
    vault = load_vault(paths.root)
    repo = Repository(paths.sqlite_path)
    sync_vault_state(vault, repo, clock=CLOCK)
    return paths, vault, repo


def _attempt(vault, repo):
    return complete_self_graded_attempt(
        vault,
        repo,
        AttemptDraft(
            practice_item_id=ITEM,
            learner_answer_md="SVD factorizes a matrix as U Sigma V transpose.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, fatal_errors=[], confidence=4),
        clock=CLOCK,
    )


def test_reviews_lists_quarantined_then_adjudicate_clears_and_receipt(tmp_path):
    paths, vault, repo = _p0_vault(tmp_path)
    result = _attempt(vault, repo)
    observation = repo.observation_by_attempt(result.attempt_id)

    # A learner contest quarantines the observation (zero current authority).
    quarantine_observation(
        repo, observation_id=observation["id"], surface_id=None,
        reason="learner_contested", clock=CLOCK,
    )

    # `grading reviews` surfaces the quarantined interpretation.
    reviews = runner.invoke(app, ["grading", "reviews", "--vault", str(paths.root), "--json"])
    assert reviews.exit_code == 0, reviews.output
    payload = json.loads(reviews.output)
    assert payload["reviews"], "expected a pending review"
    head_id = payload["reviews"][0]["id"]
    assert payload["reviews"][0]["quarantine_state"] == "quarantined"

    # Adjudicate it append-only via the CLI.
    adj = runner.invoke(
        app,
        [
            "grading", "adjudicate", head_id,
            "--resolved-class", "other",
            "--source", "human_owner",
            "--rationale", "owner review",
            "--vault", str(paths.root),
            "--json",
        ],
    )
    assert adj.exit_code == 0, adj.output
    adj_payload = json.loads(adj.output)
    assert adj_payload["adjudication"]["interpretation_id"]

    # The queue is now empty (the new head is active, not quarantined/flagged).
    reviews_after = runner.invoke(app, ["grading", "reviews", "--vault", str(paths.root), "--json"])
    assert json.loads(reviews_after.output)["reviews"] == []

    # Resolve the decision-parameter registry projection so the receipt can trace it.
    from learnloop.services import parameter_registry as pr

    pr.refresh(vault, repo, clock=CLOCK)

    # `grading receipt` traces response -> raw grade -> interpretation history.
    receipt = runner.invoke(app, ["grading", "receipt", result.attempt_id, "--vault", str(paths.root)])
    assert receipt.exit_code == 0, receipt.output
    rec = json.loads(receipt.output)
    assert rec["attempt_id"] == result.attempt_id
    assert rec["raw_grade_events"]
    assert rec["active_interpretation"] is not None
    # Append-only: the history retains more than one interpretation (original +
    # quarantine + adjudication).
    assert len(rec["interpretation_history"]) >= 3

    # F8: the receipt carries the decision lineage -- the administration pin, the
    # calibration model id+hash from the active interpretation, and the resolved
    # registry rows.
    assert "decision_params_hash" in rec
    assert rec["administration_id"] == observation["administration_id"]
    assert rec["calibration"]["calibration_model_id"] == rec["active_interpretation"]["calibration_model_id"]
    assert rec["calibration"]["calibration_model_hash"] == rec["active_interpretation"]["calibration_model_hash"]
    assert rec["calibration"]["calibration_model_hash"]
    assert rec["registry_entries"]  # resolved decision-parameter registry projection


def test_retire_surface_from_cli_preserves_evidence_and_logs_reason(tmp_path):
    """§9.7 item 6 (Journey 12 at CLI): a bad prompt is retired from the CLI with a
    taxonomy reason, its evidence visibly survives, and the reason lands in
    ``interaction_events``."""

    from learnloop.db.connection import connect
    from learnloop.services.canonical_projection import project_canonical_facet_state

    paths, vault, repo = _p0_vault(tmp_path)
    result = _attempt(vault, repo)
    project_canonical_facet_state(vault, repo)
    observation = repo.observation_by_attempt(result.attempt_id)
    surface_id = observation["surface_id"]

    evidence_before = repo.facet_capability_evidence_all()
    assert evidence_before  # evidence exists to survive the retirement

    out = runner.invoke(
        app,
        [
            "surfaces", "retire", surface_id,
            "--reason", "too_easy",
            "--provenance", "owner_tooling",
            "--vault", str(paths.root),
        ],
    )
    assert out.exit_code == 0, out.output
    assert json.loads(out.output)["retirement_record_id"]

    # Evidence survives untouched (retirement deletes nothing, §3.7).
    assert repo.facet_capability_evidence_all() == evidence_before

    # The taxonomy reason landed in interaction_events.
    with connect(repo.sqlite_path) as connection:
        rows = connection.execute(
            "SELECT kind, payload_json FROM interaction_events WHERE kind = 'retirement_reason'"
        ).fetchall()
    assert rows
    assert any("too_easy" in (r["payload_json"] or "") for r in rows)

    # And the retirement record + surface lifecycle event are inspectable.
    assert repo.retirement_records_for_surface(surface_id)


def test_registry_certify_links_coverage_without_promoting(tmp_path):
    # U-022 v2: `registry certify` runs the real seeded sweep, produces + links a
    # COVERAGE certificate, and does NOT change status (coverage is descriptive).
    # `registry promote` is the separate normative gate. Kept tiny (2 grid points,
    # 3 sim days) so it stays fast.
    paths, _vault, _repo = _p0_vault(tmp_path)
    path = "scheduler.short_session_minutes"
    out = runner.invoke(
        app,
        [
            "registry", "certify", path,
            "--low", "10", "--high", "40", "--steps", "2",
            "--days", "3", "--items-per-day", "3", "--seed", "42",
            "--vault", str(paths.root), "--json",
        ],
    )
    assert out.exit_code == 0, out.output
    payload = json.loads(out.output)
    assert payload["path"] == path
    assert payload["certificate_id"]
    assert payload["covered_value"] == 20
    # Coverage links regardless of the sweep's stability verdict (flip points do not
    # invalidate coverage, U-022 v2), and never changes status.
    assert payload["coverage_linked"] is True
    assert payload["status"] == "heuristic"  # coverage never promotes

    # The coverage link is durable and clears rule (a) for this parameter.
    show = runner.invoke(
        app, ["registry", "show", path, "--vault", str(paths.root), "--json"]
    )
    shown = json.loads(show.output)
    assert shown["status"] == "heuristic"
    assert shown["sensitivity_certificate_id"] == payload["certificate_id"]


def test_registry_promote_advances_status_via_promotion_evidence(tmp_path):
    # U-022 v2: `registry promote` consumes sim promotion evidence and advances a
    # stable-in-range decision to simulation_validated (the normative gate).
    paths, _vault, _repo = _p0_vault(tmp_path)
    path = "scheduler.short_session_minutes"
    out = runner.invoke(
        app,
        [
            "registry", "promote", path,
            "--low", "10", "--high", "40", "--steps", "2",
            "--days", "3", "--items-per-day", "3", "--seed", "42",
            "--vault", str(paths.root), "--json",
        ],
    )
    assert out.exit_code == 0, out.output
    payload = json.loads(out.output)
    # The normative gate: a stable-in-range sweep promotes; a flip refuses. Assert the
    # gate is consistent with the sweep verdict (robust to the real sweep's outcome).
    if payload["decision_stable"]:
        assert payload["promoted"] is True
        assert payload["status"] == "simulation_validated"
    else:
        assert payload["promoted"] is False
        assert payload["refusal_reason"] == "decision_unstable_in_plausible_range"
        assert payload["status"] == "heuristic"

    show = runner.invoke(
        app, ["registry", "show", path, "--vault", str(paths.root), "--json"]
    )
    assert json.loads(show.output)["status"] == payload["status"]


def test_registry_certify_refuses_module_constants(tmp_path):
    paths, _vault, _repo = _p0_vault(tmp_path)
    out = runner.invoke(
        app,
        [
            "registry", "certify", "grader_calibration:PRIOR_CONCENTRATION",
            "--low", "0.1", "--high", "2.0", "--vault", str(paths.root),
        ],
    )
    assert out.exit_code == 1
    assert "module constants are code-fixed" in out.output


def test_registry_audit_cli_is_clean_and_show_traces(tmp_path):
    paths, _vault, _repo = _p0_vault(tmp_path)
    audit = runner.invoke(app, ["registry", "audit", "--vault", str(paths.root), "--json"])
    assert audit.exit_code == 0, audit.output
    report = json.loads(audit.output)
    # U-022 v2: pending coverage is enumerated debt (warning), not a failure -- the
    # ordinary audit stays clean and exits 0 while listing the debt.
    assert report["clean"] is True
    assert report["active_pending_certificate_count"] > 0
    assert report["release_clean"] is False


def test_registry_release_check_cli_blocks_on_pending_coverage(tmp_path):
    # U-022 v2: the strict release gate treats a nonzero pending-coverage count as a
    # failure (exit 1) with the list attached, even though `registry audit` passes.
    paths, _vault, _repo = _p0_vault(tmp_path)
    audit = runner.invoke(app, ["registry", "audit", "--vault", str(paths.root)])
    assert audit.exit_code == 0

    gate = runner.invoke(app, ["registry", "release-check", "--vault", str(paths.root), "--json"])
    assert gate.exit_code == 1, gate.output
    report = json.loads(gate.output)
    assert report["release_clean"] is False
    assert report["active_pending_certificate"]  # the debt list is attached

    show = runner.invoke(
        app,
        ["registry", "show", "grader_calibration:PRIOR_CONCENTRATION", "--vault", str(paths.root), "--json"],
    )
    assert show.exit_code == 0, show.output
    entry = json.loads(show.output)
    assert entry["path"] == "grader_calibration:PRIOR_CONCENTRATION"
    assert entry["status"] == "heuristic"
    assert entry["kind"] == "decision"
