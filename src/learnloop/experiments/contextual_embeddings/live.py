"""The paid E0 run's live wiring (never executed in the harness stage).

``run_live`` is what ``learnloop experiments e0 run`` (without ``--dry-run``,
with ``--i-am-authorized-to-spend``) calls after a fresh dry run that fits:

1. **The frozen plan is executed exactly (Codex review F5).** The copies are
   rebuilt with the plan's own ``reserve_share`` and per-vault strata, and
   the rebuilt identity (pins fingerprint, run id over policy, units and
   bank ids, and the family splits) must equal the plan's, or nothing is
   spent (``PlanMismatch``).
2. The run's wall-time bound starts (``pins.MAX_WALL_S``, Codex review F14).
3. Per copy, an **experiment-owned repository** (``records.ExperimentRecords``,
   a fresh vault under the private run directory) receives every model-call
   receipt and every verdict (Codex review F4, F10), bound explicitly, so
   nothing depends on the working directory; the CLI's own receipt binding is
   pointed at it as well (``bind_receipts``).
4. The service copies are prepared (redacted, resumable) and the copy's
   ``paid.run_paid`` runs with one shared E0 ledger.

Everything paid is admitted by the ledger before it is sent. The real
clients come from ``default_factories`` (tests substitute fakes there).
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.bank import logged_bank
from learnloop.experiments.contextual_embeddings.budget import E0Ledger
from learnloop.experiments.contextual_embeddings.callers import Checkpoints, LiveRoleCaller
from learnloop.experiments.contextual_embeddings.corpus import build_snapshot, open_copy
from learnloop.experiments.contextual_embeddings.paid import run_paid
from learnloop.experiments.contextual_embeddings.records import ExperimentRecords
from learnloop.experiments.contextual_embeddings.report import assert_aggregate, render
from learnloop.experiments.contextual_embeddings.runner import freeze, plan_identity


class PlanMismatch(ValueError):
    """The copies no longer rebuild to the frozen plan; nothing was spent."""


def qwen_factory(config: Any) -> Callable[[], Any]:
    """The production OpenRouter embedding client for the copy's embedding route."""

    def build() -> Any:
        from learnloop.ai.providers.openai_embedding import OpenAIEmbeddingProviderClient
        from learnloop.config.schema import DEFAULT_EMBEDDING_PROVIDER

        name = config.ai.routing.embedding or DEFAULT_EMBEDDING_PROVIDER
        return OpenAIEmbeddingProviderClient(name, config.ai.providers[name])

    return build


@dataclass
class LiveFactories:
    """Where the paid run's clients come from (real by default)."""

    transport: Any
    qwen: Callable[[Any], Callable[[], Any]] = qwen_factory
    #: ``profile name -> client`` for the LLM roles; None: the vault's client stack.
    role_clients: Callable[[str], Any] | None = None
    #: Clients injected into the system arms' production paths (None: their own).
    system_clients: Mapping[str, Any] | None = None
    #: The backfill client factory for the Qwen service copy (None: ``qwen``).
    backfill: Callable[[], Any] | None = None
    environ: Mapping[str, str] | None = None


def default_factories() -> LiveFactories:
    from learnloop.experiments.contextual_embeddings.adapters import UrllibTransport

    return LiveFactories(transport=UrllibTransport())


def rebuild_frozen(copies: Sequence[Path], plan: Mapping[str, Any]) -> tuple[list[Any], list[Any], dict[str, Any]]:
    """The copies' handles and snapshots rebuilt under the plan's own split
    and strata, refused unless their identity is the plan's."""

    if "reserve_share" not in plan or "splits" not in plan:
        raise PlanMismatch("the plan predates the frozen split; run --dry-run again")
    if plan.get("pins_fingerprint") != pins.pins_fingerprint():
        raise PlanMismatch("the pins changed since the plan was made; run --dry-run again")
    handles = [open_copy(Path(copy), load_environment=True) for copy in copies]
    snapshots = [build_snapshot(handle, reserve_share=float(plan["reserve_share"])) for handle in handles]
    vaults = (plan.get("bank") or {}).get("vaults") or {}
    strata = {handle.label: dict((vaults.get(handle.label) or {}).get("development_strata") or {})
              for handle in handles}
    if any(not value for value in strata.values()):
        raise PlanMismatch("the plan has no frozen strata for every copy")
    identity = plan_identity(handles, snapshots, strata)
    problems = [name for name in ("run_id", "splits") if identity[name] != plan.get(name)]
    if problems:
        raise PlanMismatch("the copies do not rebuild to the frozen plan (" + ", ".join(problems)
                           + " differ); nothing was spent")
    return handles, snapshots, strata


def run_live(copies: Sequence[Path], *, plan: Mapping[str, Any], run_dir: Path,
             key_envs: Mapping[str, str], reader_latency_budget_s: float | None = None,
             factories: LiveFactories | None = None,
             bind_receipts: Callable[[Any], None] | None = None) -> dict[str, Any]:
    factories = factories or default_factories()
    run_dir = Path(run_dir) / str(plan["run_id"])
    handles, snapshots, strata = rebuild_frozen(copies, plan)
    ledger = E0Ledger(run_dir.parent / "ledger")
    ledger.start_clock(pins.MAX_WALL_S)
    freeze(run_dir / "frozen", plan, snapshots)
    results: dict[str, Any] = {"run_id": plan["run_id"], "vaults": {}}
    provider_keys = {"perplexity": key_envs.get("perplexity"), "voyage": key_envs.get("voyage"),
                     "openrouter": key_envs.get("openrouter")}
    for handle, snapshot in zip(handles, snapshots, strict=True):
        from learnloop.experiments.contextual_embeddings.system_arms import prepare_service_copies

        vault_dir = run_dir / handle.label
        records = ExperimentRecords(vault_dir / "records")
        if bind_receipts is not None:
            bind_receipts(records.repository)
        with records.receipts(f"e0:{plan['run_id']}:{handle.label}"):
            caller = LiveRoleCaller(handle.root, handle.vault.config, ledger,
                                    checkpoints=Checkpoints(vault_dir / "llm"),
                                    client_factory=factories.role_clients, records=records)
            logged, _counts = logged_bank(snapshot, handle.repository.question_events(answer_status="answered"))
            system_handles, preparation = prepare_service_copies(
                handle.root, vault_dir / "service", ledger, snapshot=snapshot, client_factory=factories.backfill,
                factory_for_config=factories.qwen)
            outcome = run_paid(snapshot, ledger=ledger, caller=caller, run_dir=vault_dir,
                               transport=factories.transport,
                               qwen_client_factory=factories.qwen(handle.vault.config),
                               logged=logged, strata=strata[handle.label], key_envs=provider_keys,
                               environ=factories.environ, system_handles=system_handles,
                               system_preparation=preparation, system_clients=factories.system_clients,
                               latency_budget_s=reader_latency_budget_s)
        outcome["service_preparation"] = preparation
        outcome["records"] = {"judgments": len(records.judgments()), "receipts": records.receipt_count()}
        outcome["run_id"] = plan["run_id"]
        outcome["corpus"] = [snapshot.inventory()]
        assert_aggregate(outcome)
        results["vaults"][handle.label] = outcome
        (vault_dir / "results.json").write_text(json.dumps(outcome, sort_keys=True, indent=1, default=str),
                                                encoding="utf-8")
        (vault_dir / "report.md").write_text(render(outcome), encoding="utf-8")
    results["ledger"] = ledger.report()
    return results
