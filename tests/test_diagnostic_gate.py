"""§6 sim discrimination gate (spec_misconception_diagnostics.md)."""

from __future__ import annotations

from tests.structured_ai import StructuredClientFake

from learnloop.ai.errors import CodexUnavailable
from learnloop.diagnosis.ai_contracts import DiagnosticTrialResult, DiagnosticTrials
from learnloop.db.repositories import MisconceptionRecord, Repository
from learnloop.diagnosis.diagnostic_gate import (
    BACKFILL_SKIPPED_EXISTING,
    BACKFILL_SKIPPED_UNREGISTERED,
    backfill_discrimination_rows,
    run_discrimination_gate,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, create_basic_vault
from learnloop.clock import FrozenClock


def _record(mc_id="mc_reverse_q", signature="Q^T x is the coordinate vector"):
    return MisconceptionRecord(
        id=mc_id,
        learning_object_id="lo_svd_definition",
        concept_id=None,
        statement="believes Q maps standard vectors to eigenbasis coefficients",
        signature=signature,
        facet_ids=["recall"],
        severity=0.8,
        status="active",
        source_error_event_ids=[],
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
        resolved_at=None,
    )


def _discriminating_item(mc_id="mc_reverse_q"):
    return {
        "id": "pi_diag_reverse",
        "expected_answer": "Qx is the coordinate vector",
        "misconception_consistent_answer": "Q^T x is the coordinate vector",
        "surface_family": "computation",
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "c1", "points": 4, "description": "correct"}],
            "fatal_errors": [{"id": "fe_reversed", "misconception_id": mc_id, "max_grade": 1}],
        },
    }


def test_discriminating_item_accepted_and_row_written(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    record = _record()

    # 8 trials clears the 25th-percentile bounds for a perfect discriminator
    # (the default 5 leaves the lower bound at 0.79, just under the 0.8 spec gate).
    trials = 8
    result = run_discrimination_gate(
        vault, repository, item=_discriminating_item(), misconception=record, trials=trials
    )

    assert result.accepted is True
    # Planted student fires every trial; clean student never fires.
    assert result.sens_alpha == 1.0 + trials
    assert result.sens_beta == 1.0
    assert result.spec_alpha == 1.0 + trials
    assert result.spec_beta == 1.0
    row = repository.discrimination_row("pi_diag_reverse", "mc_reverse_q")
    assert row is not None
    assert row.source == "sim"
    assert row.n_planted_trials == trials


def test_paraphrase_rejected_low_sensitivity(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    record = _record()
    # The motivating paraphrase: the planted student answers it correctly, so
    # the misconception-consistent answer equals the expected answer.
    item = _discriminating_item()
    item["misconception_consistent_answer"] = item["expected_answer"]

    result = run_discrimination_gate(vault, repository, item=item, misconception=record)

    assert result.accepted is False
    trials = vault.config.misconceptions.sim_gate_trials
    # sens lower bound is Beta(1, N+1): the planted student never fires.
    assert result.sens_alpha == 1.0
    assert result.sens_beta == 1.0 + trials
    assert "sensitivity_lb_below_threshold" in result.reasons


def test_gate_writes_no_attempt_or_error_event_rows(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    run_discrimination_gate(vault, repository, item=_discriminating_item(), misconception=_record())

    assert repository.list_attempts_by_learning_object("lo_svd_definition") == []
    assert repository.active_error_events() == []


# -- Feature 1: discrimination backfill -----------------------------------------


def _keyed_item_payload(item_id: str, mc_id: str) -> dict:
    return {
        "id": item_id,
        "learning_object_id": "lo_svd_definition",
        "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt"],
        "evidence_facets": ["recall"],
        "evidence_weights": {"recall": 1.0},
        "prompt": "Which of Qx / Q^T x is the coordinate vector?",
        "expected_answer": "Qx is the coordinate vector",
        "misconception_consistent_answer": "Q^T x is the coordinate vector",
        "surface_family": "computation",
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "c1", "points": 4, "description": "correct"}],
            "fatal_errors": [
                {
                    "id": "fe_reversed",
                    "description": "States Q^T (not Q) yields the coordinate vector.",
                    "misconception_id": mc_id,
                    "max_grade": 1,
                }
            ],
        },
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


def _seed_backfill_vault(tmp_path, *, register: bool = True, mc_id: str = "mc_reverse_q"):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    if register:
        repository.insert_misconception(
            id=mc_id,
            learning_object_id="lo_svd_definition",
            statement="believes Q maps standard vectors to eigenbasis coefficients",
            signature="Q^T x is the coordinate vector",
            facet_ids=["recall"],
            severity=0.8,
            clock=FrozenClock(NOW),
        )
    upsert_practice_item(
        paths.root, _keyed_item_payload("pi_keyed_reverse", mc_id), clock=FrozenClock(NOW)
    )
    return paths, repository


def test_backfill_creates_row_for_keyed_pair(tmp_path):
    paths, repository = _seed_backfill_vault(tmp_path)
    vault = load_vault(paths.root)

    results = backfill_discrimination_rows(vault, repository)

    ran = [r for r in results if not r.reasons or r.reasons[0] not in {
        BACKFILL_SKIPPED_EXISTING, BACKFILL_SKIPPED_UNREGISTERED}]
    assert len(ran) == 1
    assert ran[0].practice_item_id == "pi_keyed_reverse"
    row = repository.discrimination_row("pi_keyed_reverse", "mc_reverse_q")
    assert row is not None
    assert row.source == "sim"


def test_backfill_skips_existing_row_without_force(tmp_path):
    paths, repository = _seed_backfill_vault(tmp_path)
    vault = load_vault(paths.root)
    backfill_discrimination_rows(vault, repository)
    before = repository.discrimination_row("pi_keyed_reverse", "mc_reverse_q")

    results = backfill_discrimination_rows(vault, repository)

    assert [r for r in results if BACKFILL_SKIPPED_EXISTING in r.reasons]
    # Untouched: same posterior counts.
    after = repository.discrimination_row("pi_keyed_reverse", "mc_reverse_q")
    assert after.n_planted_trials == before.n_planted_trials
    assert after.sensitivity_alpha == before.sensitivity_alpha


def test_backfill_force_reruns(tmp_path):
    paths, repository = _seed_backfill_vault(tmp_path)
    vault = load_vault(paths.root)
    backfill_discrimination_rows(vault, repository)

    results = backfill_discrimination_rows(vault, repository, force=True)

    ran = [r for r in results if r.practice_item_id == "pi_keyed_reverse" and not (
        set(r.reasons) & {BACKFILL_SKIPPED_EXISTING, BACKFILL_SKIPPED_UNREGISTERED})]
    assert len(ran) == 1


def test_backfill_skips_unregistered_misconception(tmp_path):
    paths, repository = _seed_backfill_vault(tmp_path, register=False, mc_id="mc_ghost")
    vault = load_vault(paths.root)

    results = backfill_discrimination_rows(vault, repository)

    skipped = [r for r in results if BACKFILL_SKIPPED_UNREGISTERED in r.reasons]
    assert any(r.misconception_id == "mc_ghost" for r in skipped)
    # No row written for the unregistered pair.
    assert repository.discrimination_row("pi_keyed_reverse", "mc_ghost") is None


# -- Feature 2: codex answers-under-belief (LLM trials) -------------------------


class _StubTrialsClient(StructuredClientFake):
    def __init__(self, *, planted_fires: int, clean_fires: int, n: int, raises: bool = False):
        self._planted_fires = planted_fires
        self._clean_fires = clean_fires
        self._n = n
        self._raises = raises
        self.calls = 0

    def run_diagnostic_trials(self, context) -> DiagnosticTrials:
        self.calls += 1
        if self._raises:
            raise CodexUnavailable("provider down")
        planted = [
            DiagnosticTrialResult(answer=f"p{i}", fires=i < self._planted_fires)
            for i in range(self._n)
        ]
        clean = [
            DiagnosticTrialResult(answer=f"c{i}", fires=i < self._clean_fires)
            for i in range(self._n)
        ]
        return DiagnosticTrials(planted=planted, clean=clean)


def test_llm_trials_combine_into_beta_counts(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    vault.config.misconceptions.sim_gate_llm_trials = 4
    repository = Repository(paths.sqlite_path)
    client = _StubTrialsClient(planted_fires=4, clean_fires=0, n=4)

    result = run_discrimination_gate(
        vault,
        repository,
        item=_discriminating_item(),
        misconception=_record(),
        grading_client=client,
        trials=8,
    )

    assert client.calls == 1
    assert result.llm_trials_ran is True
    assert "llm_trials_ran" in result.reasons
    # deterministic 8 planted fires + 4 LLM planted fires; 12 clean no-fires.
    assert result.n_planted_trials == 12
    assert result.n_clean_trials == 12
    assert result.sens_alpha == 1.0 + 12
    assert result.sens_beta == 1.0
    assert result.spec_alpha == 1.0 + 12
    assert result.spec_beta == 1.0
    assert result.accepted is True
    row = repository.discrimination_row("pi_diag_reverse", "mc_reverse_q")
    assert row.n_planted_trials == 12
    assert row.source == "sim"


def test_llm_not_called_when_deterministic_rejects(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    vault.config.misconceptions.sim_gate_llm_trials = 4
    repository = Repository(paths.sqlite_path)
    item = _discriminating_item()
    item["misconception_consistent_answer"] = item["expected_answer"]  # paraphrase
    client = _StubTrialsClient(planted_fires=4, clean_fires=0, n=4)

    result = run_discrimination_gate(
        vault, repository, item=item, misconception=_record(), grading_client=client
    )

    assert client.calls == 0
    assert result.llm_trials_ran is False
    assert result.accepted is False


def test_llm_not_called_when_disabled(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    # sim_gate_llm_trials defaults to 0.
    assert vault.config.misconceptions.sim_gate_llm_trials == 0
    repository = Repository(paths.sqlite_path)
    client = _StubTrialsClient(planted_fires=4, clean_fires=0, n=4)

    result = run_discrimination_gate(
        vault,
        repository,
        item=_discriminating_item(),
        misconception=_record(),
        grading_client=client,
        trials=8,
    )

    assert client.calls == 0
    assert result.llm_trials_ran is False
    assert result.n_planted_trials == 8


def test_llm_unavailable_falls_back_to_deterministic(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    vault.config.misconceptions.sim_gate_llm_trials = 4
    repository = Repository(paths.sqlite_path)
    client = _StubTrialsClient(planted_fires=0, clean_fires=0, n=4, raises=True)

    result = run_discrimination_gate(
        vault,
        repository,
        item=_discriminating_item(),
        misconception=_record(),
        grading_client=client,
        trials=8,
    )

    assert client.calls == 1
    assert result.llm_trials_ran is False
    assert "llm_trials_unavailable" in result.reasons
    # Deterministic-only result stands: 8 trials, accepted.
    assert result.n_planted_trials == 8
    assert result.accepted is True
