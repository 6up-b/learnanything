"""Slice 1 §5.2 / §5.6 / §9.4: the four history modes and the read-only workspace."""

from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from learnloop.ai.errors import AIProviderUnavailable, CodexUnavailable
from learnloop.ai.providers.codex import SdkCodexClient
from learnloop.ai.transport import READ_ONLY_WORKSPACE, StructuredRequest, execute_structured_operation
from learnloop.attempts.grading import resolved_rubric
from learnloop.config import CodexConfig
from learnloop.diagnosis.split.context import (
    assemble_diagnosis_context,
    cacheable_prefix,
    current_attempt_from,
)
from learnloop.diagnosis.split.diagnoser import SKIPPED_NO_WORKSPACE, run_diagnosis
from learnloop.diagnosis.split.history import VaultHistoryStore
from learnloop.diagnosis.split.retrieval import EmbeddingHistoryRetriever
from learnloop.diagnosis.split.settings import DiagnosisSettings
from learnloop.diagnosis.split.snapshot import export_snapshot, snapshot_workspace
from learnloop.diagnosis.offline_review.judge import DiagnosisJudgment
from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import FakeEmbeddingClient, ReviewFakeClient
from tests.diagnosis_split_helpers import blind_record, build_diagnosis_vault, seed_history

PROSE = ("Feedback.", "The final factor is not transposed.", "transpose_confusion")


@pytest.fixture()
def seeded(tmp_path):
    paths = build_diagnosis_vault(tmp_path / "vault")
    vault, repository = seed_history(paths)
    return paths, vault, repository


def _current(vault, store, attempt_id="att_06_svd_fail"):
    attempt = store.attempt(attempt_id)
    item = vault.practice_items[attempt.practice_item_id]
    record = blind_record(
        score=2, max_points=4, criteria={"setup": 2, "result": 0},
        attributions=[{"error_type": "conceptual_slip", "evidence": "Blind evidence here.",
                       "first_divergence": {"anchor_kind": "span", "criterion_id": "result", "quote": attempt.learner_answer_md.split()[-1]},
                       "target_evidence_families": ["recall"], "resolution_status": "unresolved", "validity_scope": "valid_measurement"}],
        local_analysis="Blind local reading of this answer.",
    )
    return item, current_attempt_from(vault, item, attempt_id=attempt_id, completed_at=attempt.completed_at,
                                      learner_answer_md=attempt.learner_answer_md, blind_grade=record)


# -- full ---------------------------------------------------------------------------


def test_full_includes_every_neighbour_attempt_chronologically(seeded):
    _paths, vault, repository = seeded
    store = VaultHistoryStore(vault, repository)
    _item, current = _current(vault, store)
    assembled = assemble_diagnosis_context(vault, store, current, DiagnosisSettings(), mode="full")
    history = assembled.blocks["history"]
    ids = [row["attempt_id"] for row in history]
    # No facet-overlap filter: the transpose failure (facet "transpose") is in.
    assert ids == ["att_01_transpose_fail", "att_02_svd_fail", "att_03_svd_pass", "att_05_eigen_fail"]
    assert [row["date"] for row in history] == sorted(row["date"] for row in history)
    by_id = {row["attempt_id"]: row for row in history}
    assert by_id["att_02_svd_fail"]["learner_answer_md"] == "A = U Sigma V"
    assert "learner_answer_md" not in by_id["att_03_svd_pass"]
    assert by_id["att_01_transpose_fail"]["relation"] == "prerequisite"
    assert by_id["att_05_eigen_fail"]["relation"] == "confusable"


def test_full_budget_truncates_oldest_attempts_before_any_hypothesis(seeded):
    _paths, vault, repository = seeded
    store = VaultHistoryStore(vault, repository)
    _item, current = _current(vault, store)
    roomy = assemble_diagnosis_context(vault, store, current, DiagnosisSettings(), mode="full")
    hypotheses = len(roomy.blocks["prior_hypotheses"])
    assert hypotheses
    one_less = assemble_diagnosis_context(vault, store, current, DiagnosisSettings(), mode="full", token_budget=roomy.tokens - 5)
    assert [row["attempt_id"] for row in one_less.blocks["history"]][0] == "att_02_svd_fail"
    assert len(one_less.blocks["prior_hypotheses"]) == hypotheses
    assert one_less.blocks["disclosures"]["dropped"]["attempts"] == 1
    starved = assemble_diagnosis_context(vault, store, current, DiagnosisSettings(), mode="full", token_budget=1)
    assert starved.blocks["history"] == []
    assert starved.blocks["disclosures"]["dropped"]["attempts"] == 4
    assert starved.blocks["disclosures"]["truncated"] is True


def test_full_stable_prefix_is_shared_by_consecutive_diagnoses_on_one_lo(seeded):
    _paths, vault, repository = seeded
    store = VaultHistoryStore(vault, repository)
    _item, sixth = _current(vault, store, "att_06_svd_fail")
    _item, seventh = _current(vault, store, "att_07_svd_future")
    first = assemble_diagnosis_context(vault, store, sixth, DiagnosisSettings(), mode="full")
    second = assemble_diagnosis_context(vault, store, seventh, DiagnosisSettings(), mode="full")
    prefix = cacheable_prefix(first.blocks)
    assert len(prefix) > 500
    assert second.rendered().startswith(prefix)
    assert first.rendered().startswith(prefix)


# -- snapshot -------------------------------------------------------------------------


def test_snapshot_export_is_as_of_and_stripped(seeded, tmp_path):
    _paths, vault, repository = seeded
    store = VaultHistoryStore(vault, repository)
    _item, current = _current(vault, store)
    manifest = export_snapshot(vault, store, current.ref(), tmp_path / "snap")
    files = set(manifest.files)
    attempt_files = [name for name in files if name.startswith("attempts/")]
    assert len(attempt_files) == 5  # the whole vault before att_06, any LO
    assert not any("att_06" in name or "att_07" in name for name in files)
    assert {"INDEX.md", "graph/learning_objects.md"} <= files
    text = "".join((tmp_path / "snap" / name).read_text(encoding="utf-8") for name in files)
    for leaked in PROSE:
        assert leaked not in text
    assert "att_02_svd_fail" in manifest.known.attempt_ids
    assert "att_06_svd_fail" not in manifest.known.attempt_ids
    again = export_snapshot(vault, store, current.ref(), tmp_path / "snap2")
    assert again.manifest_hash == manifest.manifest_hash


def test_snapshot_workspace_is_deleted_on_success_and_on_failure(seeded):
    _paths, vault, repository = seeded
    store = VaultHistoryStore(vault, repository)
    item, current = _current(vault, store)
    rubric = resolved_rubric(vault, item)
    client = ReviewFakeClient(workspace=True)
    outcome = run_diagnosis(client, vault=vault, item=item, rubric=rubric, store=store, current=current,
                            settings=DiagnosisSettings(), mode="snapshot")
    assert outcome.status == "completed"
    workspace = client.workspaces[-1]
    assert not workspace.exists()
    assert "INDEX.md" in client.workspace_files[-1]
    assert outcome.receipt["snapshot"]["file_count"] == len(client.workspace_files[-1])
    assert outcome.receipt["snapshot"]["opened"] == ["cat INDEX.md"]
    # The agent cited an attempt it found only in the files: known via the snapshot.
    assert outcome.unknown_id_count == 0
    failing = ReviewFakeClient(workspace=True, fail_purposes=("diagnosis",))
    outcome = run_diagnosis(failing, vault=vault, item=item, rubric=rubric, store=store, current=current,
                            settings=DiagnosisSettings(), mode="snapshot")
    assert outcome.status == "failed"
    assert outcome.error == "AIProviderUnavailable"
    assert failing.workspaces and not failing.workspaces[-1].exists()
    with pytest.raises(RuntimeError):
        with snapshot_workspace(vault, store, current.ref()) as manifest:
            root = manifest.root
            raise RuntimeError("boom")
    assert not root.exists()


def test_snapshot_is_unavailable_without_the_capability(seeded):
    _paths, vault, repository = seeded
    store = VaultHistoryStore(vault, repository)
    item, current = _current(vault, store)
    client = ReviewFakeClient(workspace=False)
    outcome = run_diagnosis(client, vault=vault, item=item, rubric=resolved_rubric(vault, item), store=store,
                            current=current, settings=DiagnosisSettings(), mode="snapshot")
    assert outcome.status == "skipped" and outcome.error == SKIPPED_NO_WORKSPACE
    assert client.calls == []
    with pytest.raises(AIProviderUnavailable):
        execute_structured_operation(client, purpose="diagnosis", prompt="{}", result_model=DiagnosisJudgment, workspace=Path("/tmp"))


def test_codex_workspace_replaces_the_vault_root(tmp_path, monkeypatch):
    """The snapshot workspace REPLACES the vault root (§5.6); the read boundary
    itself is tested against the installed Codex in test_diagnosis_isolation."""

    from learnloop.diagnosis.offline_review.judge import LinkJudgment
    from tests.test_diagnosis_isolation import _fake_sdk

    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    workspace = tmp_path / "snapshot"
    workspace.mkdir()
    captured: dict[str, Any] = {}
    _fake_sdk(monkeypatch, captured)

    def turn_items(*_args, **_kwargs):
        return SimpleNamespace(final_response='{"links": []}', items=[{"command": ["rg", "transpose", "attempts/"]}])

    client = SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex"), sdk_codex_bin="/usr/bin/codex-for-test"), vault_root)
    monkeypatch.setattr(client, "_configured_mcp_server_ids", lambda _cwd: ())
    assert client.supports(READ_ONLY_WORKSPACE)
    import openai_codex

    original = openai_codex.Codex.thread_start

    def thread_start(self, **kwargs):
        thread = original(self, **kwargs)
        thread.turn = lambda prompt, **turn_kwargs: (captured.__setitem__("turn", turn_kwargs), SimpleNamespace(run=turn_items, interrupt=lambda: None))[1]
        return thread

    monkeypatch.setattr(openai_codex.Codex, "thread_start", thread_start)
    result = client.complete(StructuredRequest(purpose="diagnosis", prompt="p", result_model=LinkJudgment, workspace=workspace))
    assert result == LinkJudgment(links=[])
    for cwd in (captured["app_config"]["cwd"], captured["thread_start"]["cwd"], captured["turn"]["cwd"]):
        assert cwd == str(workspace.resolve())
        assert str(vault_root.resolve()) not in cwd
    assert "sandbox" not in captured["thread_start"]
    assert client.workspace_activity() == ["rg transpose attempts/"]


# -- all modes ------------------------------------------------------------------------


@pytest.mark.parametrize("mode", ["exact", "full", "snapshot", "hybrid"])
def test_every_mode_keeps_s3_and_validates_evidence_ids(seeded, mode):
    paths, vault, repository = seeded
    store = VaultHistoryStore(vault, repository)
    item, current = _current(vault, store)
    client = ReviewFakeClient(invent_id=True)
    retriever = EmbeddingHistoryRetriever(client=FakeEmbeddingClient(), sqlite_path=paths.sqlite_path) if mode == "hybrid" else None
    outcome = run_diagnosis(client, vault=vault, item=item, rubric=resolved_rubric(vault, item), store=store, current=current,
                            settings=DiagnosisSettings(), mode=mode, retriever=retriever)
    assert outcome.status == "completed"
    prompt = client.prompts[-1]
    for leaked in PROSE:
        assert leaked not in prompt
    assert outcome.unknown_id_count == 1
    assert outcome.validation_report["unknown_ids"]["attempts"] == ["att_does_not_exist"]
    assert "att_does_not_exist" not in outcome.proposal["evidence_attempt_ids"]
    assert outcome.receipt["history_mode"] == mode
    assert outcome.context_hash


# -- hybrid -----------------------------------------------------------------------------


def test_hybrid_fuses_exact_and_knn_and_records_provenance(seeded):
    paths, vault, repository = seeded
    store = VaultHistoryStore(vault, repository)
    _item, current = _current(vault, store)
    embedder = FakeEmbeddingClient()
    retriever = EmbeddingHistoryRetriever(client=embedder, sqlite_path=paths.sqlite_path)
    prepared = retriever.prepare(store.all_attempts())
    assert prepared == 6  # every non-pass attempt, embedded once
    assert retriever.prepare(store.all_attempts()) == 0  # content-hash idempotent: never re-embedded
    settings = DiagnosisSettings(history_error_limit=1)
    assembled = assemble_diagnosis_context(vault, store, current, settings, mode="hybrid", retriever=retriever)
    receipt = assembled.receipt
    assert receipt["method"] == "hybrid"
    assert receipt["embedding_model_id"] == "qwen/qwen3-embedding-8b"
    sources = {row["attempt_id"]: row["source"] for row in receipt["retrieval"]}
    assert set(sources) == {"att_05_eigen_fail", "att_02_svd_fail"}
    assert len([row for row in receipt["retrieval"] if row["kept"]]) == 1
    assert set(receipt["knn_only_attempt_ids"]) <= set(sources)


def test_hybrid_degrades_to_exact_when_embeddings_fail(seeded):
    paths, vault, repository = seeded
    store = VaultHistoryStore(vault, repository)
    _item, current = _current(vault, store)
    retriever = EmbeddingHistoryRetriever(client=FakeEmbeddingClient(fail=True), sqlite_path=paths.sqlite_path)
    assembled = assemble_diagnosis_context(vault, store, current, DiagnosisSettings(), mode="hybrid", retriever=retriever)
    assert assembled.receipt["method"] == "exact_fallback"
    assert assembled.receipt["retrieval_error"] == "AIProviderUnavailable"
    exact = assemble_diagnosis_context(vault, store, current, DiagnosisSettings(), mode="exact")
    assert assembled.blocks["failure_history"] == exact.blocks["failure_history"]
    unconfigured = assemble_diagnosis_context(vault, store, current, DiagnosisSettings(), mode="hybrid", retriever=None)
    assert unconfigured.receipt["method"] == "exact_fallback"


def test_repairs_before_filters_owners_and_cold_outcomes_by_the_cutoff(tmp_path):
    """F5: a repair class shown as of attempt N carries no owner or outcome from after N."""

    import sqlite3
    from contextlib import closing

    paths = build_diagnosis_vault(tmp_path / "vault")
    _vault, repository = seed_history(paths)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection, connection:
        owners = dict(connection.execute(
            "SELECT attempt_id, id FROM causal_hypotheses WHERE attempt_id IN ('att_02_svd_fail', 'att_07_svd_future')"
        ).fetchall())
        # A test-only shortcut on a throwaway vault: give two existing
        # hypotheses one repair class (the live path appends successors).
        connection.execute("DROP TRIGGER causal_hypotheses_no_update")
        connection.execute(
            "UPDATE causal_hypotheses SET repair_class_id = 'rc_transpose' "
            "WHERE attempt_id IN ('att_02_svd_fail', 'att_07_svd_future')"
        )
        for cold_attempt, success, when in (("att_03_svd_pass", 1, "2026-05-01T11:00:00Z"), ("att_07_svd_future", 1, "2026-05-01T19:00:00Z")):
            connection.execute(
                "INSERT INTO causal_cold_verifications (id, source_attempt_id, cold_attempt_id, repair_class_id, hypothesis_ids_json, "
                "source_surface_family, cold_surface_family, avoided_affordances_json, success, capability_update_json, "
                "diagnosis_support_update_json, repair_effect_support_json, created_at) "
                "VALUES (?, 'att_02_svd_fail', ?, 'rc_transpose', '[]', 'svd_compute', 'svd_compute_b', '[]', ?, '{}', '{}', '{}', ?)",
                (f"ccv_{cold_attempt}", cold_attempt, success, when),
            )
    vault = load_vault(paths.root)
    store = VaultHistoryStore(vault, repository)
    cutoff = store.ref("att_06_svd_fail")
    (record,) = store.repairs_before(cutoff, None)
    assert record.hypothesis_ids == (owners["att_02_svd_fail"],)
    assert (record.cold_successes, record.cold_failures) == (1, 0)
    # After both observations, everything is visible.
    (late,) = store.repairs_before(store.ref("att_07_svd_future"), None)
    assert late.hypothesis_ids == (owners["att_02_svd_fail"],)
    assert (late.cold_successes, late.cold_failures) == (1, 0)


def test_as_of_history_needs_each_record_written_before_the_cutoff(tmp_path):
    """F5 (re-review): a record written after the cutoff is invisible at it,
    whatever earlier attempt it references: a cold observation, a repair
    owner, a new hypothesis episode or a later version of an earlier one."""

    import sqlite3
    from contextlib import closing

    from tests.diagnosis_split_helpers import at

    def iso(hours: float) -> str:
        return at(hours).isoformat().replace("+00:00", "Z")

    paths = build_diagnosis_vault(tmp_path / "vault")
    _vault, repository = seed_history(paths)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection, connection:
        connection.row_factory = sqlite3.Row
        first = dict(connection.execute(
            "SELECT * FROM causal_hypotheses WHERE attempt_id = 'att_02_svd_fail' ORDER BY version LIMIT 1"
        ).fetchone())
        connection.execute("DROP TRIGGER causal_hypotheses_no_update")
        # The att_02 hypothesis (written at hour 1) owns the repair class.
        connection.execute("UPDATE causal_hypotheses SET repair_class_id = 'rc_transpose' WHERE id = ?", (first["id"],))
        columns = list(first)

        def insert(**changes):
            row = {**first, "repair_class_id": "rc_transpose", **changes}
            connection.execute(
                f"INSERT INTO causal_hypotheses ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
                [row[name] for name in columns],
            )

        # Written at hour 7 (after att_06 at hour 5), about att_02 (hour 1):
        # a second version of the same episode, and a brand-new episode.
        insert(id="ch_v2_late", version=first["version"] + 1, supersedes_id=first["id"], status="validated", created_at=iso(7))
        insert(id="ch_new_late", episode_key="episode_written_late", version=1, supersedes_id=None, created_at=iso(7))
        # A cold verification on att_03 (hour 2), recorded at hour 7.
        connection.execute(
            "INSERT INTO causal_cold_verifications (id, source_attempt_id, cold_attempt_id, repair_class_id, hypothesis_ids_json, "
            "source_surface_family, cold_surface_family, avoided_affordances_json, success, capability_update_json, "
            "diagnosis_support_update_json, repair_effect_support_json, created_at) "
            "VALUES ('ccv_late', 'att_02_svd_fail', 'att_03_svd_pass', 'rc_transpose', '[]', 'svd_compute', 'svd_compute_b', "
            "'[]', 1, '{}', '{}', '{}', ?)",
            (iso(7),),
        )
    vault = load_vault(paths.root)
    store = VaultHistoryStore(vault, repository)
    cutoff = store.ref("att_06_svd_fail")
    (record,) = store.repairs_before(cutoff, None)
    assert record.hypothesis_ids == (first["id"],)
    assert (record.cold_successes, record.cold_failures) == (0, 0)
    visible = {row.id: row for row in store.hypotheses_before(cutoff, list(vault.learning_objects))}
    assert "ch_new_late" not in visible and "ch_v2_late" not in visible
    assert visible[first["id"]].status == first["status"]
    # Once the cutoff passes hour 7, the later records are all visible.
    later = store.ref("att_07_svd_future")
    (late,) = store.repairs_before(later, None)
    assert set(late.hypothesis_ids) == {"ch_v2_late", "ch_new_late"}
    assert (late.cold_successes, late.cold_failures) == (1, 0)
    visible_late = {row.id for row in store.hypotheses_before(later, list(vault.learning_objects))}
    assert {"ch_v2_late", "ch_new_late"} <= visible_late and first["id"] not in visible_late
