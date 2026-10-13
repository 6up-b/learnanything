"""``learnloop decider agreement`` (owner decision 2026-10-13): real pairs only, never a model call.

Per ``judgment_ledger`` task: the pairs where both the Decider and an LLM
judged the same input, their agreement and confusion, the Decider's fallbacks,
and its calibration where owner or verifier labels exist (null, never zero,
without them).
"""

from __future__ import annotations

import json

import pytest

from learnloop.db.repositories import Repository


def test_agreement_reports_real_pairs_fallbacks_and_labels(tmp_path):
    from learnloop.ai.agreement import agreement_report, ledger_rows
    from learnloop.db.stores.judgments import append_judgment

    repo = Repository(tmp_path / "state.sqlite")
    with repo.atomic():
        c = repo.connection()

        def row(judge, verdict, digest="same", left="a", right="b", **kw):
            model = None if judge == "owner" else "fake"
            return append_judgment(c, task="same_cause", left_kind="attempt", left_id=left, right_kind="attempt",
                                   right_id=right, judge=judge, judge_model=model,
                                   prompt_version=None if judge == "owner" else "v1", input_hash=digest,
                                   verdict=verdict, **kw)

        d = row("decider", "same", rationale=json.dumps({"probabilities": {"same": 0.8, "different": 0.2}}))
        row("llm", "different")
        row("owner", "same", rationale=json.dumps({"label_for": d}))
        row("llm", "same", "different_input")  # no Decider on this input: no pair
        row("decider", "unavailable", "fallback")
        row("llm", "same", "fallback")
        # A T1 / text-gap executor's rendered distribution, labelled by the owner on the same question.
        row("decider", "different", "text", left="c", right="d",
            rationale="Decider (qs) gives no rationale; probabilities: same 0.300, different 0.700")
        row("llm", "different", "text", left="d", right="c")  # either orientation is the same pair
        row("owner", "different", "owner_input", left="c", right="d")
        report = agreement_report(ledger_rows(c))
    task = report["tasks"]["same_cause"]
    assert (task["pairs"], task["agreements"]) == (2, 1)
    assert task["agreement"] == 0.5
    assert task["confusion"] == {"same": {"different": 1}, "different": {"different": 1}}
    assert task["fallbacks"] == 1 and task["decider_failures"] == {"unavailable": 1}
    assert task["labels"] == 2
    assert task["brier_score"] == pytest.approx((0.08 + 0.18) / 2)
    assert task["calibration_bins"]["0.8"]["accuracy"] == 1.0
    assert task["calibration_bins"]["0.7"]["accuracy"] == 1.0
    assert report["shadow_calls"] == 0


def test_agreement_without_labels_or_pairs_is_null_not_zero():
    from learnloop.ai.agreement import agreement_report

    rows = [{"id": "1", "created_at": "1", "task": "t", "left_kind": "x", "left_id": "a", "right_kind": None,
             "right_id": None, "judge": "decider", "verdict": "yes", "input_hash": "h", "rationale": "{}",
             "supersedes_id": None}]
    task = agreement_report(rows)["tasks"]["t"]
    assert task["agreement"] is None and task["brier_score"] is None and task["labels"] == 0


def test_agreement_cli_is_read_only_and_reads_review_runs(tmp_path, monkeypatch):
    import hashlib

    from typer.testing import CliRunner

    from learnloop import decider_judgments as tier1
    from learnloop.cli import app
    from learnloop.db.stores.judgments import append_judgment
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    run = tmp_path / "review_run"
    run.mkdir()
    scratch = Repository(run / "scratch.sqlite")
    with scratch.atomic():
        for judge, verdict in (("decider", "same"), ("llm", "same")):
            append_judgment(scratch.connection(), task="diagnosis_link_judgment", left_kind="attempt", left_id="a",
                            right_kind="attempt", right_id="b", judge=judge, judge_model="m", prompt_version="v",
                            input_hash="h", verdict=verdict)
    monkeypatch.setattr(tier1, "client_for", lambda *a: pytest.fail("report must never resolve a provider"))
    before = hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()
    result = CliRunner().invoke(app, ["decider", "agreement", "--vault", str(paths.root), "--review-run", str(run),
                                      "--json"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["shadow_calls"] == 0
    assert report["tasks"]["diagnosis_link_judgment"]["agreement"] == 1.0
    assert hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest() == before


def test_span_support_labels_never_leak_to_another_rewords_check(tmp_path):
    """Review F3: a span-support row's endpoints name the facet, not the wording it judged.

    The owner's confirm of check A on facet F labels A only; check B on F (a
    different wording, never acted on) has no label, so it is not scored
    against A's. The same holds for a misconception match (one learning object,
    many statements). A task whose endpoints do name the judged content (a
    same-cause pair) still binds a label by the same question.
    """

    from learnloop.ai.agreement import agreement_report, ledger_rows
    from learnloop.db.stores.judgments import append_judgment

    repo = Repository(tmp_path / "state.sqlite")
    with repo.atomic():
        c = repo.connection()
        for task, left_kind in (("facet_span_support", "facet"), ("misconception_match", "learning_object")):
            a = append_judgment(c, task=task, left_kind=left_kind, left_id="F", judge="decider", judge_model="d",
                                prompt_version="v", input_hash="wording-a", verdict="does not support",
                                rationale=json.dumps({"probabilities": {"supports": 0.2, "does not support": 0.8}}))
            append_judgment(c, task=task, left_kind=left_kind, left_id="F", judge="owner", input_hash="wording-a",
                            verdict="supports", rationale=json.dumps({"label_for": a}))
            append_judgment(c, task=task, left_kind=left_kind, left_id="F", judge="decider", judge_model="d",
                            prompt_version="v", input_hash="wording-b", verdict="supports",
                            rationale=json.dumps({"probabilities": {"supports": 0.9, "does not support": 0.1}}))
        report = agreement_report(ledger_rows(c))
    for task in ("facet_span_support", "misconception_match"):
        entry = report["tasks"][task]
        assert entry["labels"] == 1, task
        assert entry["calibration_bins"] == {"0.8": {"count": 1, "correct": 0, "mean_confidence": 0.8,
                                                     "accuracy": 0.0}}


def test_agreement_counts_each_ledger_row_once_across_a_review_runs_vault_copy(tmp_path):
    """Review F4: a review run's scratch is a backup copy of the vault database, so it repeats every vault row."""

    from typer.testing import CliRunner

    from learnloop.cli import app
    from learnloop.db.copies import backup_database
    from learnloop.db.stores.judgments import append_judgment
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    vault_repo = Repository(paths.sqlite_path)
    with vault_repo.atomic():
        for judge, verdict in (("decider", "unavailable"), ("llm", "yes")):
            append_judgment(vault_repo.connection(), task="learner_gap_needed", left_kind="learning_object",
                            left_id="lo", right_kind="practice_item", right_id="pi", judge=judge, judge_model="m",
                            prompt_version="v", input_hash="needed", verdict=verdict)
    reports = []
    for runs in (0, 1, 2):
        args = ["decider", "agreement", "--vault", str(paths.root), "--json"]
        for index in range(runs):
            run = tmp_path / f"run{runs}-{index}"
            run.mkdir()
            backup_database(paths.sqlite_path, run / "scratch.sqlite")
            args += ["--review-run", str(run)]
        result = CliRunner().invoke(app, args)
        assert result.exit_code == 0, result.output
        reports.append(json.loads(result.output)["tasks"]["learner_gap_needed"])
    for task in reports:
        assert task["fallbacks"] == 1 and task["decider_failures"] == {"unavailable": 1}
