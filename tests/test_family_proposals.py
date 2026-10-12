from __future__ import annotations

import hashlib
import json
import threading

import pytest
from typer.testing import CliRunner

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.execution import report_call_usage
from learnloop.ai.routing import provider_for_task
from learnloop.ai.spend import SpendCaps
from learnloop.cli import app
from learnloop.db.repositories import Repository
from learnloop.ops.family_proposals import FamilyVerdict, propose_families
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item
from tests.helpers import create_basic_vault


class Judge:
    provider_name = "fake"
    model = "fake-judge"

    def __init__(self, verdict="different", *, after_call=None, fail_at=None):
        self.verdict = verdict
        self.after_call = after_call
        self.fail_at = fail_at
        self.calls = []

    def supports(self, capability):
        return capability in {"structured_completion", "bounded_structured_completion"}

    def complete(self, request):
        self.calls.append(request)
        assert request.output_budget_tokens == 1024
        report_call_usage({"input_tokens": 10, "output_tokens": 20, "resolved_model": "fake-resolved"})
        if self.after_call:
            self.after_call()
        if self.fail_at == len(self.calls):
            raise AIProviderUnavailable("PRIVATE provider detail")
        verdict = self.verdict(request) if callable(self.verdict) else self.verdict
        return FamilyVerdict(
            verdict=verdict, variant_relation="same_target" if verdict == "same" else None,
            rationale="A shared full target" if verdict == "same" else "Not the same",
            idea_statement="SVD definition" if verdict == "same" else "",
            retrieval_target="State the complete matrix factorization" if verdict == "same" else "",
        )


@pytest.fixture
def vault(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    loaded = load_vault(paths.root)
    original = next(iter(loaded.practice_items.values()))
    for suffix in ("b", "c"):
        item = original.model_copy(update={"id": suffix, "prompt": f"{original.prompt} {suffix}"})
        upsert_practice_item(paths.root, item)
    return load_vault(paths.root), Repository(paths.sqlite_path), paths


def run(vault, client, **kwargs):
    loaded, _, _ = vault
    return propose_families(
        loaded, client=client, caps=kwargs.pop("caps", SpendCaps(max_total_tokens=1_000_000)),
        price_per_million=kwargs.pop("price_per_million", 1.0), **kwargs,
    )


def test_dry_run_no_calls_or_writes(vault):
    _, repository, paths = vault
    judge = Judge("same")
    before = hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()
    report = run(vault, judge, dry_run=True)
    assert report["status"] == "dry_run"
    assert report["estimate"]["calls"] == 6
    assert report["estimate"]["pairs"] == 3
    assert report["estimate"]["estimated_usd"] > 0
    assert not judge.calls
    assert before == hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()
    assert not (paths.root / ".learnloop" / "families-propose.lock").exists()


@pytest.mark.parametrize("caps", [
    SpendCaps(max_candidates=2), SpendCaps(max_pairs=2), SpendCaps(max_calls=5),
    SpendCaps(max_total_tokens=1), SpendCaps(max_estimated_usd=0),
])
def test_caps_admit_before_any_calls(vault, caps):
    judge = Judge()
    assert run(vault, judge, caps=caps)["status"] == "over_budget"
    assert not judge.calls


def test_unknown_price_fails_closed_even_with_high_cap(vault):
    judge = Judge()
    report = run(vault, judge, price_per_million=None,
                 caps=SpendCaps(max_total_tokens=1_000_000, max_estimated_usd=1e9))
    assert report["status"] == "over_budget"
    assert report["estimate"]["estimated_usd"] is None
    assert not judge.calls


def test_every_pair_gets_two_different_prompts_and_reject_ledger(vault):
    _, repository, _ = vault
    judge = Judge()
    report = run(vault, judge)
    assert report["status"] == "complete"
    assert len(judge.calls) == 6
    assert not report["accepted"]
    assert report["results_by_model"] == {"fake-resolved": {"different": 6}}
    with repository.connection() as connection:
        judgments = connection.execute("SELECT * FROM judgment_ledger WHERE task='same_target'").fetchall()
        rejects = connection.execute("SELECT * FROM judgment_ledger WHERE verdict='reject'").fetchall()
        receipts = connection.execute("SELECT * FROM model_call_receipts WHERE purpose='pf_family_judge'").fetchall()
    assert len(judgments) == 6 and len(rejects) == 3
    assert len({row["prompt_version"] for row in judgments}) == 2
    assert all(row["judge_model"] == "fake-resolved" and row["input_hash"] for row in judgments)
    assert len(receipts) == 6
    assert all(row["resolved_model"] == "fake-resolved" for row in receipts)
    assert all(json.loads(row["budget_json"])["max_pairs"] == 100 for row in receipts)
    assert all(json.loads(row["budget_json"])["family_judge"]["prompt_version"] for row in receipts)
    rerun = run(vault, judge)
    assert rerun["cached_passes"] == 6 and rerun["charged"]["calls"] == 0
    assert len(judge.calls) == 6


def test_two_agreeing_passes_apply_and_one_step_undo(vault):
    loaded, repository, paths = vault
    report = run(vault, Judge("same"))
    assert report["status"] == "complete"
    assert len(report["accepted"]) == 1
    decision = report["accepted"][0]
    grouped = load_vault(paths.root)
    assert len({item.family_id for item in grouped.practice_items.values()}) == 1
    assert next(iter(grouped.practice_items.values())).family_id == decision["family_id"]
    result = CliRunner().invoke(app, ["families", "undo", decision["family_id"], "--vault", str(paths.root), "--json"])
    assert result.exit_code == 0, result.output
    ungrouped = load_vault(paths.root)
    assert all(item.family_id is None for item in ungrouped.practice_items.values())
    # Undo is sticky: persisted same judgments must not immediately reapply it.
    rerun = run((ungrouped, repository, paths), Judge("same"))
    assert not rerun["accepted"] and rerun["charged"]["calls"] == 0
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM judgment_ledger WHERE verdict='accept'").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM judgment_ledger WHERE verdict='undo'").fetchone()[0] == 1


def test_disagreement_does_not_apply(vault):
    report = run(vault, Judge(lambda request:
        "different" if "counterexample-v1" in request.prompt else "same"))
    assert not report["accepted"]
    assert all(getattr(item, "family_id", None) is None for item in vault[0].practice_items.values())


def test_no_chaining_rejects_entire_ambiguous_component(vault):
    def verdict(request):
        context = json.loads(request.prompt.split("\n\n")[-1])["context"]
        ids = {context["left"]["item"]["id"], context["right"]["item"]["id"]}
        return "different" if ids == {"b", "c"} else "same"
    report = run(vault, Judge(verdict))
    assert not report["accepted"] and report["rejected_components"] == 1


def test_cancel_after_paid_pass_is_saved_and_resumes(vault):
    stop = threading.Event()
    judge = Judge(after_call=stop.set)
    report = run(vault, judge, cancelled=stop.is_set)
    assert report["status"] == "cancelled"
    assert report["completed_passes"] == 1 and len(judge.calls) == 1
    second = Judge()
    report = run(vault, second)
    assert report["status"] == "complete" and len(second.calls) == 5


def test_each_retry_spends_and_never_echoes_provider_error(vault):
    judge = Judge(fail_at=1)
    caps = SpendCaps(max_total_tokens=1_000_000, max_retries=0)
    report = run(vault, judge, caps=caps)
    assert report["status"] == "provider_failed" and len(judge.calls) == 1
    assert "PRIVATE" not in json.dumps(report)
    judge = Judge(fail_at=1)
    report = run(vault, judge)
    assert report["status"] == "complete"
    assert report["charged"]["calls"] == 7 and report["charged"]["retries"] == 1


def test_inputs_or_model_changes_do_not_reuse_paid_verdict(vault):
    assert run(vault, Judge())["charged"]["calls"] == 6
    loaded, _, _ = vault
    loaded.practice_items["b"].prompt += " Changed target."
    upsert_practice_item(loaded.root, loaded.practice_items["b"])
    report = run(vault, Judge())
    assert report["cached_passes"] == 2 and report["charged"]["calls"] == 4
    judge = Judge()
    judge.model = "new-model"
    assert run(vault, judge)["charged"]["calls"] == 6


def test_unset_pf_routes_fall_back_to_active(vault, monkeypatch):
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    config = vault[0].config
    config.ai.active_provider = "chosen"
    for task in ("pf_family_judge", "pf_generator", "pf_isomorph_judge",
                 "pf_closed_book", "pf_reference_verifier", "pf_solver_panel"):
        assert provider_for_task(config, task).provider_name == "chosen"


def test_large_lo_embeddings_block_only_and_judge_different_never_groups(vault):
    from learnloop.db.stores.embedding_vectors import put_vector
    from learnloop.vault.embedding_recipes import embedding_records

    loaded, repository, _ = vault
    loaded.config.families.max_exhaustive_items = 2
    loaded.config.families.blocking_top_k = 2
    # Identical vectors/surfaces still cannot establish shared identity.
    with repository.connection() as connection:
        for record in embedding_records(loaded, ("item/stem",)):
            put_vector(
                connection, record_kind="item", record_id=record.record_id,
                field="stem", content_hash=record.content_hash,
                model_id=loaded.config.embedding.model, task_prefix="retrieval-document",
                vector=[1, 2, 3],
            )
    report = run(vault, Judge("different"))
    assert report["blocked_los"] == 1 and report["pairs"] == 3
    assert report["accepted"] == []
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM activity_family_membership_events").fetchone()[0] == 0


def test_large_lo_missing_index_fails_before_judge(vault):
    vault[0].config.families.max_exhaustive_items = 2
    judge = Judge()
    with pytest.raises(ValueError, match="embedding backfill"):
        run(vault, judge)
    assert not judge.calls


def test_cli_dry_run_reports_cost_without_client_or_data_changes(vault, monkeypatch):
    _, _, paths = vault
    def forbidden(*args, **kwargs):
        pytest.fail("dry-run must not construct a client")
    monkeypatch.setattr("learnloop.ops.family_proposals.ready_client_for_task", forbidden)
    before = paths.sqlite_path.read_bytes()
    result = CliRunner().invoke(app, [
        "families", "propose", "--vault", str(paths.root), "--dry-run",
        "--price-per-million", "1", "--json",
    ])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["estimate"]["calls"] == 6 and report["status"] == "dry_run"
    assert paths.sqlite_path.read_bytes() == before


def test_isomorph_is_preserved_in_authored_members(vault):
    class IsomorphJudge(Judge):
        def complete(self, request):
            return super().complete(request).model_copy(update={"variant_relation": "isomorph"})
    report = run(vault, IsomorphJudge("same"))
    assert len(report["accepted"]) == 1
    loaded = load_vault(vault[2].root)
    assert sorted(item.variant_relation for item in loaded.practice_items.values()) == [
        "isomorph", "isomorph", "same_target",
    ]


def test_default_codex_route_is_rejected_before_client_or_spend(vault, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("unbounded transport must be rejected before startup")
    monkeypatch.setattr("learnloop.ops.family_proposals.ready_client_for_task", forbidden)
    report = propose_families(vault[0], caps=SpendCaps(max_total_tokens=1_000_000),
                             price_per_million=1)
    assert report["status"] == "unavailable"
    assert report["charged"]["calls"] == 0
    assert "pf_family_judge" in report["reason"]


def test_explicit_revision_invalidates_alias_cache_but_reports_resolved_model(vault):
    first = run(vault, Judge())
    assert first["results_by_model"] == {"fake-resolved": {"different": 6}}
    class ChangedAlias(Judge):
        def complete(self, request):
            value = super().complete(request)
            report_call_usage({"resolved_model": "fake-new-resolved"})
            return value
    # Resume is intentionally the same saved experiment, not a claim that the
    # alias still serves the old model. A new experiment needs a new revision.
    cached = run(vault, ChangedAlias())
    assert cached["charged"]["calls"] == 0
    assert cached["results_by_model"] == first["results_by_model"]
    fresh = run(vault, ChangedAlias(), judge_revision="2")
    assert fresh["charged"]["calls"] == 6
    assert fresh["results_by_model"] == {"fake-new-resolved": {"different": 6}}


def test_reject_identity_excludes_unrelated_pairs(vault):
    _, repository, paths = vault
    run(vault, Judge())
    with repository.connection() as connection:
        before = {row["id"] for row in connection.execute(
            "SELECT id FROM judgment_ledger WHERE verdict='reject'"
        )}
    loaded = load_vault(paths.root)
    item = loaded.practice_items["b"].model_copy(update={"id": "new"})
    upsert_practice_item(paths.root, item)
    run((load_vault(paths.root), repository, paths), Judge())
    with repository.connection() as connection:
        after = {row["id"] for row in connection.execute(
            "SELECT id FROM judgment_ledger WHERE verdict='reject'"
        )}
    assert before <= after and len(after - before) == 3


def test_route_availability_never_changes_preview_model(vault, monkeypatch):
    from types import SimpleNamespace
    from learnloop.config.schema import OpenAICompatibleProviderConfig

    loaded, _, _ = vault
    loaded.config.ai.routing.pf_family_judge = "primary"
    loaded.config.ai.providers["primary"] = OpenAICompatibleProviderConfig(model="pinned")
    loaded.config.ai.fallback_provider = "fallback"
    seen = []
    def resolve(root, config, task, *, explicit):
        seen.append(explicit)
        return SimpleNamespace(ready=False, runtime=SimpleNamespace(message="Primary unavailable"))
    monkeypatch.setattr("learnloop.ops.family_proposals.ready_client_for_task", resolve)
    options = {"caps": SpendCaps(max_total_tokens=1_000_000), "price_per_million": 1}
    preview = propose_families(loaded, dry_run=True, **options)
    actual = propose_families(loaded, **options)
    assert preview["provider"] == actual["provider"] == "primary"
    assert preview["model_id"] == actual["model_id"] == "pinned"
    assert preview["estimate"] == actual["estimate"]
    assert actual["status"] == "unavailable" and actual["charged"]["calls"] == 0
    assert seen == ["primary"]
