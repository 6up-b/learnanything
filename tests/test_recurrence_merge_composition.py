"""Slice 2 T1 composed with what main gained before it merged (fakes only).

* PF-c (unverified = unassessed at the split versions): an answer whose only
  shortfall is an unverified criterion queues no diagnosis, so it adds no
  hypothesis, joins no recurrence group and never counts toward the K=3
  escalation.
* Codex unavailable (the same-cause judge route defaults to the diagnosis
  route): the judge is skipped or its calls fail, the diagnosis still
  completes, nothing merges, claims are released and the pairs wait for the
  backlog. Nothing raises.
* Router R0's judgment_ledger: T1 writes only judges inside R0's CHECK; a
  ``decider`` same_cause verdict joins no group; R0's ledger-identity recovery
  (``llm_probability``) never reads T1's rows.
"""

from __future__ import annotations

from types import SimpleNamespace

from learnloop.clock import FrozenClock
from learnloop.diagnosis.recurrence.backlog import run_backlog
from learnloop.diagnosis.split.jobs import diagnosis_status
from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import FakeEmbeddingClient
from tests.recurrence_fakes import JudgeFake, StatementFake, shares_word
from tests.split_live_helpers import at, drain_jobs, enable_embeddings, split_vault, submit
from tests.test_recurrence_commands import CAPS

V_SAME = "Believes V and V transpose are the same matrix."
V_REWORDED = "Thinks the last SVD factor never needs transposing."
V_THIRD = "Writes V where the transpose of V belongs."
STATEMENTS = {"first": V_SAME, "second": V_REWORDED, "third": V_THIRD}
#: The reference's final answer by another route: PF-c's check verifies it.
VERIFYING_ANSWER = "A different route.\nFinal answer: U Sigma V^T"


def _vault(tmp_path, *, config: str = ""):
    paths, _vault, repository = split_vault(tmp_path, version="mvp-0.12", seed=False, config=config)
    enable_embeddings(paths.root)
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text(encoding="utf-8").replace("dimensions = 4096", "dimensions = 16"), encoding="utf-8")
    return paths, load_vault(paths.root), repository


class _UnverifiedOnVerifyingAnswers(StatementFake):
    """StatementFake, except a verifying answer gets ``result`` half its points
    with no error named: the PF-c gate records ``result`` unverified, and the
    assessed criterion (``setup``) passes, so nothing assessed fell short."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        if "Final answer: U Sigma V^T" not in str(context["learner_answer_md"]):
            return result
        evidence = [
            row.model_copy(update={"points_awarded": 1.0}) if row.criterion_id == "result" else row
            for row in result.criterion_evidence
        ]
        return result.model_copy(update={
            "criterion_evidence": evidence,
            "rubric_score": int(sum(row.points_awarded for row in evidence)),
            "error_attributions": [],
        })


def _answer(vault, repository, client, embedder, item_id, answer, offset, **drain_kwargs):
    result = submit(vault, repository, client, item_id=item_id, answer=answer, when=at(10 + 2 * offset))
    drain_jobs(vault, repository, client, embedding=embedder, clock=FrozenClock(at(11 + 2 * offset)), **drain_kwargs)
    return result


def _escalation(repository, attempt_id):
    diagnosis = repository.current_live_diagnosis(attempt_id)
    return repository.recurrence_escalation(diagnosis["id"]) if diagnosis is not None else None


def test_an_unassessed_only_answer_is_never_a_recurrence(tmp_path):
    _paths, vault, repository = _vault(tmp_path)
    client = _UnverifiedOnVerifyingAnswers(STATEMENTS, decide=shares_word("transpos"))
    embedder = FakeEmbeddingClient()
    kwargs = {"judge_factory": lambda: client}
    first = _answer(vault, repository, client, embedder, "pi_svd_compute_001", "A = U Sigma V first", 0, **kwargs)
    unassessed = _answer(vault, repository, client, embedder, "pi_svd_compute_001", VERIFYING_ANSWER, 1, **kwargs)
    second = _answer(vault, repository, client, embedder, "pi_svd_compute_002", "B = U Sigma V second", 2, **kwargs)

    # PF-c: the unverified criterion is out of the grade and queues no diagnosis.
    record = repository.latest_blind_grade_record(unassessed.attempt_id)["record"]
    assert record["grading_support"]["unverified_criterion_ids"] == ["result"]
    assert record["grading_support"]["assessed_shortfall"] is False
    assert diagnosis_status(repository, unassessed.attempt_id)["status"] == "not_needed"
    assert repository.current_live_diagnosis(unassessed.attempt_id) is None
    assert repository.causal_hypotheses_for_attempt(unassessed.attempt_id) == []
    # Two diagnosed failures in one group so far: no escalation yet (it would
    # fire here if the unassessed answer counted as a third).
    assert _escalation(repository, second.attempt_id) is None

    third = _answer(vault, repository, client, embedder, "pi_svd_compute_001", "A = U Sigma V third", 3, **kwargs)
    escalation = _escalation(repository, third.attempt_id)
    assert escalation is not None and escalation["recurrence_count"] == 3
    assert escalation["earlier_attempt_ids"] == [second.attempt_id, first.attempt_id]
    assert unassessed.attempt_id not in escalation["earlier_attempt_ids"]


def _three_failures(tmp_path, client, **drain_kwargs):
    _paths, vault, repository = _vault(tmp_path)
    embedder = FakeEmbeddingClient()
    results = [
        _answer(vault, repository, client, embedder, item_id, answer, offset, **drain_kwargs)
        for offset, (item_id, answer) in enumerate((
            ("pi_svd_compute_001", "A = U Sigma V first"),
            ("pi_svd_compute_002", "B = U Sigma V second"),
            ("pi_svd_compute_001", "A = U Sigma V third"),
        ))
    ]
    return vault, repository, embedder, results


def _backlog_waits(vault, repository, embedder):
    plan = run_backlog(vault, repository, caps=CAPS, dry_run=True, judge_client=JudgeFake(), embedding_client=embedder)
    assert plan["status"] == "dry_run"
    return plan["plan"]["pairs_to_judge"]


def _assert_nothing_merged_and_diagnoses_complete(repository, results):
    for result in results:
        diagnosis = repository.current_live_diagnosis(result.attempt_id)
        assert diagnosis is not None and diagnosis["status"] == "completed"
        assert diagnosis_status(repository, result.attempt_id)["status"] == "done"
    with repository.connection() as connection:
        verdicts = connection.execute("SELECT COUNT(*) FROM judgment_ledger WHERE task = 'same_cause'").fetchone()[0]
        leased = connection.execute("SELECT COUNT(*) FROM judgment_work_claims WHERE state = 'leased'").fetchone()[0]
    assert verdicts == 0 and leased == 0
    assert repository.recurrence_group_map() == {}


def test_a_codex_route_that_is_not_ready_skips_the_judge_and_leaves_the_backlog(tmp_path, monkeypatch):
    """The production judge factory: the same-cause route (unset, so the
    diagnosis route: Codex) resolves not ready. The diagnosis client is the
    fake (as when the diagnoser is routed elsewhere)."""

    from learnloop.ai import routing

    real = routing.ready_client_for_task

    def codex_exhausted(vault_root, config, task, **kwargs):
        if task == "same_cause_judge":
            return SimpleNamespace(ready=False, client=None, runtime=SimpleNamespace(message="Codex usage exhausted"))
        return real(vault_root, config, task, **kwargs)

    monkeypatch.setattr(routing, "ready_client_for_task", codex_exhausted)
    client = StatementFake(STATEMENTS, decide=shares_word("transpos"))
    vault, repository, embedder, results = _three_failures(tmp_path, client)
    assert client.judged == []
    _assert_nothing_merged_and_diagnoses_complete(repository, results)
    assert _backlog_waits(vault, repository, embedder) >= 2
    # The backlog command degrades the same way: no call, no crash.
    report = run_backlog(vault, repository, caps=CAPS, embedding_client=embedder)
    assert report["status"] == "provider_failed" and "not ready" in report["reason"]


def test_failing_codex_judge_calls_release_their_claims_and_leave_the_backlog(tmp_path):
    """Codex resolves but every judge call fails (quota exhausted mid-run):
    each pair is ``failed``, its claim released, no verdict lands, and the
    diagnosis completes."""

    client = StatementFake(STATEMENTS, decide=shares_word("transpos"), fail_purposes=("same_cause_judgment",))
    vault, repository, embedder, results = _three_failures(tmp_path, client, judge_factory=lambda: client)
    assert "same_cause_judgment" not in client.calls or client.judged == []
    _assert_nothing_merged_and_diagnoses_complete(repository, results)
    with repository.connection() as connection:
        released = connection.execute("SELECT COUNT(*) FROM judgment_work_claims WHERE state = 'released'").fetchone()[0]
    assert released >= 1
    assert _backlog_waits(vault, repository, embedder) >= 2
    # Once Codex is back, the backlog judges them and the groups merge.
    report = run_backlog(vault, repository, caps=CAPS, judge_client=JudgeFake(shares_word("transpos")),
                         embedding_client=embedder)
    assert report["status"] == "complete" and report["groups"]["group_count"] == 1


def test_t1_ledger_rows_fit_r0s_check_and_r0s_recovery_never_reads_them(tmp_path):
    from learnloop.field.probability_prep import committed_judgments

    _paths, vault, repository = _vault(tmp_path)
    client = StatementFake(STATEMENTS, decide=shares_word("transpos"))
    embedder = FakeEmbeddingClient()
    for offset, (item_id, answer) in enumerate((("pi_svd_compute_001", "A = U Sigma V first"),
                                                ("pi_svd_compute_002", "B = U Sigma V second"))):
        _answer(vault, repository, client, embedder, item_id, answer, offset, judge_factory=lambda: client)
    with repository.connection() as connection:
        judges = {row[0] for row in connection.execute("SELECT judge FROM judgment_ledger WHERE task = 'same_cause'")}
        check = connection.execute("SELECT sql FROM sqlite_master WHERE name = 'judgment_ledger'").fetchone()[0]
        claims = {row[0] for row in connection.execute("SELECT task FROM judgment_work_claims")}
        # R0's ledger-identity recovery reads only its own task and subject
        # kind: T1's verdicts are never recovered as probability answers.
        assert committed_judgments(connection) == {}
    assert judges == {"llm"} and claims == {"same_cause"}
    assert "'decider'" in check
    assert repository.recurrence_group_map(), "the judge's same verdict merged the pair"


def test_a_decider_same_cause_verdict_is_logged_but_joins_no_group(tmp_path):
    """R0 admits ``decider`` to judgment_ledger; T1's authority order does not
    place it, so it never joins a group (T1 review, second round F6)."""

    from learnloop.db.stores.judgments import append_judgment
    from learnloop.substrate.recurrence_groups import refresh_recurrence_groups

    _paths, vault, repository = _vault(tmp_path, config="[recurrence]\njudge_enabled = false")
    client = StatementFake(STATEMENTS)
    embedder = FakeEmbeddingClient()
    results = [
        _answer(vault, repository, client, embedder, item_id, answer, offset)
        for offset, (item_id, answer) in enumerate((("pi_svd_compute_001", "A = U Sigma V first"),
                                                    ("pi_svd_compute_002", "B = U Sigma V second")))
    ]
    left, right = (
        next(row for row in repository.causal_hypotheses_for_attempt(result.attempt_id)
             if row["cause_scope"] == "learner_state" and row["status"] != "open_set")["episode_key"]
        for result in results
    )
    assert repository.recurrence_group_map() == {}

    def verdict(judge: str) -> None:
        with repository.atomic():
            append_judgment(
                repository.connection(), task="same_cause", left_kind="hypothesis", left_id=left,
                right_kind="hypothesis", right_id=right, judge=judge, judge_model="decider-model",
                prompt_version="test", input_hash=f"{left}|{right}|{judge}", verdict="same", rationale="test",
            )

    verdict("decider")
    refresh_recurrence_groups(vault, repository)
    assert repository.recurrence_group_map() == {}
    # The same verdict at the judge's tier does merge them (the check is live).
    verdict("llm")
    refresh_recurrence_groups(vault, repository)
    assert repository.recurrence_group_map()
