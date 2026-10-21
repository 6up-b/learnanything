"""The paid E0 run's live wiring (never executed in the harness stage).

``run_live`` is what ``learnloop experiments e0 run`` (without ``--dry-run``,
with ``--i-am-authorized-to-spend``) calls after a fresh dry run that fits:
it opens each copy with the app's own environment loading (the settings file
the owner keeps the keys in, never read by this code), builds the real
clients (the production OpenRouter embedding client for Qwen, HTTPS for the
hosted adapters, the existing AI client stack for the LLM roles), shares ONE
E0 ledger across every copy, freezes the manifests, runs ``paid.run_paid``
per copy and writes the aggregate results and report into the private run
directory. Everything paid is admitted by the ledger before it is sent.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
from pathlib import Path
from typing import Any

from learnloop.experiments.contextual_embeddings.adapters import UrllibTransport
from learnloop.experiments.contextual_embeddings.bank import logged_bank
from learnloop.experiments.contextual_embeddings.budget import E0Ledger
from learnloop.experiments.contextual_embeddings.callers import Checkpoints, LiveRoleCaller
from learnloop.experiments.contextual_embeddings.corpus import build_snapshot, open_copy
from learnloop.experiments.contextual_embeddings.paid import run_paid
from learnloop.experiments.contextual_embeddings.report import assert_aggregate, render
from learnloop.experiments.contextual_embeddings.runner import freeze, split_strata


def _qwen_factory(config: Any):
    def build() -> Any:
        from learnloop.ai.providers.openai_embedding import OpenAIEmbeddingProviderClient
        from learnloop.config.schema import DEFAULT_EMBEDDING_PROVIDER

        name = config.ai.routing.embedding or DEFAULT_EMBEDDING_PROVIDER
        return OpenAIEmbeddingProviderClient(name, config.ai.providers[name])

    return build


def run_live(copies: Sequence[Path], *, plan: Mapping[str, Any], run_dir: Path,
             key_envs: Mapping[str, str], reader_latency_budget_s: float | None = None) -> dict[str, Any]:
    run_dir = Path(run_dir) / str(plan["run_id"])
    ledger = E0Ledger(run_dir.parent / "ledger")
    handles = [open_copy(Path(copy), load_environment=True) for copy in copies]
    snapshots = [build_snapshot(handle) for handle in handles]
    freeze(run_dir / "frozen", plan, snapshots)
    strata = split_strata(snapshots)
    results: dict[str, Any] = {"run_id": plan["run_id"], "vaults": {}}
    transport = UrllibTransport()
    for handle, snapshot in zip(handles, snapshots, strict=True):
        vault_dir = run_dir / handle.label
        caller = LiveRoleCaller(handle.root, handle.vault.config, ledger, checkpoints=Checkpoints(vault_dir / "llm"))
        logged, _counts = logged_bank(snapshot, handle.repository.question_events(answer_status="answered"))
        provider_keys = {"perplexity": key_envs.get("perplexity"), "voyage": key_envs.get("voyage"),
                         "openrouter": key_envs.get("openrouter")}
        from learnloop.experiments.contextual_embeddings.system_arms import prepare_service_copies

        system_handles, backfill = prepare_service_copies(handle.root, vault_dir / "service", ledger)
        outcome = run_paid(snapshot, ledger=ledger, caller=caller, run_dir=vault_dir, transport=transport,
                           qwen_client_factory=_qwen_factory(handle.vault.config), logged=logged,
                           strata=strata[handle.label], key_envs=provider_keys, system_handles=system_handles,
                           latency_budget_s=reader_latency_budget_s)
        outcome["service_backfill"] = [{key: report.get(key) for key in ("status", "records", "embedded")}
                                       for report in backfill]
        outcome["run_id"] = plan["run_id"]
        outcome["corpus"] = [snapshot.inventory()]
        assert_aggregate(outcome)
        results["vaults"][handle.label] = outcome
        (vault_dir / "results.json").write_text(json.dumps(outcome, sort_keys=True, indent=1, default=str),
                                                encoding="utf-8")
        (vault_dir / "report.md").write_text(render(outcome), encoding="utf-8")
    results["ledger"] = ledger.report()
    return results
