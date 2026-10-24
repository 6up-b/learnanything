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
4. The route canaries run, then the service copies are prepared (redacted,
   resumable; no Qwen copy when its canary failed) and the copy's
   ``paid.run_paid`` runs with the ONE ledger of the plan's authorization
   (``budget.authorized_ledger``, fix round 4), never one under ``run_dir``.

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
from learnloop.experiments.contextual_embeddings.bank import logged_questions
from learnloop.experiments.contextual_embeddings.budget import E0Ledger
from learnloop.experiments.contextual_embeddings.callers import Checkpoints, LiveRoleCaller, canary_models
from learnloop.experiments.contextual_embeddings.corpus import build_snapshot, open_copy
from learnloop.experiments.contextual_embeddings.paid import run_paid
from learnloop.experiments.contextual_embeddings.records import ExperimentRecords
from learnloop.experiments.contextual_embeddings.report import assert_aggregate, render
from learnloop.experiments.contextual_embeddings.runner import freeze, plan_identity
from learnloop.experiments.contextual_embeddings.stop_rules import incomplete_rules


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
    #: The HTTP transport of the Messages API roles (None: ``adapters.UrllibTransport``).
    anthropic_transport: Any = None


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
    # Keys come only from the shell or --env-file (re-plan 2026-10-22): no settings file is loaded.
    handles = [open_copy(Path(copy), load_environment=False) for copy in copies]
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


def _failure_outcome(plan: Mapping[str, Any], handle: Any, ledger: E0Ledger, exc: BaseException,
                     preparation: Mapping[str, Any] | None) -> dict[str, Any]:
    """The aggregate failure report of a copy whose run stopped on an
    unexpected failure (fix round 4, Medium 12): its classification only
    (never the exception's text), the ledger, and every planned item as
    missing."""

    from learnloop.experiments.contextual_embeddings.boundary import classify, safe_message

    return {"status": "incomplete", "run_id": plan["run_id"],
            "incomplete_reason": f"stopped on a failure ({classify(exc)}): {safe_message(exc)}",
            "failures": [{"item": "run", "kind": f"failure_{classify(exc)}", "reason": safe_message(exc),
                          "denominator": None}],
            "planned": {"missing": {"run_stopped": 1}}, "ledger": ledger.report(),
            "service_preparation": dict(preparation or {}), "decisions": incomplete_rules()}


def _write_outcome(vault_dir: Path, outcome: Mapping[str, Any]) -> None:
    assert_aggregate(outcome)
    vault_dir.mkdir(parents=True, exist_ok=True)
    (vault_dir / "results.json").write_text(json.dumps(outcome, sort_keys=True, indent=1, default=str),
                                            encoding="utf-8")
    (vault_dir / "report.md").write_text(render(outcome), encoding="utf-8")


def reused_store(run_dir: Path, plan: Mapping[str, Any], snapshots: Sequence[Any], reuse_run: str) -> Path:
    """The earlier run directory whose stores a plan reuses (relabel round).

    Every store there is content-keyed (role checkpoints by pin, identity,
    output bound, prompt and schema; vectors by document space and content;
    service copies by frozen tree, policy and harness; latency by query
    encoder and question), so a changed request misses and only an identical
    one is reused. Refused unless the earlier run froze the SAME corpus:
    its frozen splits and candidate maps must equal this plan's."""

    store = Path(run_dir) / reuse_run
    frozen = store / "frozen"
    if not (frozen / "run_plan.json").is_file() or not (frozen / "candidate_maps.json").is_file():
        raise PlanMismatch("the reused run has no frozen plan under the run directory; nothing was spent")
    earlier = json.loads((frozen / "run_plan.json").read_text(encoding="utf-8"))
    if earlier.get("splits") != plan.get("splits"):
        raise PlanMismatch("the reused run froze other splits; nothing was spent")
    maps = {snapshot.vault_label: [{"unit": unit.unit_id, "extraction": unit.extraction_id,
                                    "members": [[m.span_id, m.start, m.end] for m in unit.members]}
                                   for unit in snapshot.units] for snapshot in snapshots}
    if json.loads((frozen / "candidate_maps.json").read_text(encoding="utf-8")) != json.loads(
            json.dumps(maps, sort_keys=True, default=str)):
        raise PlanMismatch("the reused run froze other candidate maps; nothing was spent")
    return store


def run_live(copies: Sequence[Path], *, plan: Mapping[str, Any], run_dir: Path,
             key_envs: Mapping[str, str], reader_latency_budget_s: float | None = None,
             factories: LiveFactories | None = None,
             bind_receipts: Callable[[Any], None] | None = None,
             new_authorization: str | None = None, reuse_run: str | None = None) -> dict[str, Any]:
    """The paid run (see the module docstring).

    One budget per authorization (fix round 4, High 3): the ledger is the
    plan's canonical ``<fixtures-local>/contextual-embeddings/ledger/<plan_id>.ledger``,
    whatever ``run_dir`` says; a new plan while another plan's ledger exists
    needs ``new_authorization``. Provider log records are sanitized for the
    whole run (High 8). Each copy's route canaries run BEFORE its service
    backfill (Medium 9). Any failure still writes that copy's aggregate
    failure report (Medium 12); a halted ledger (an overage) stops every
    later copy at once (High 2).

    ``reuse_run`` (relabel round, 2026-10-23): the earlier run whose
    content-keyed stores this plan reads and extends (:func:`reused_store`);
    this plan's frozen manifests and results go to its own directory, and
    the earlier run's results stay as they were. Its ledger is carried and
    sealed by the new authorization (``budget.authorized_ledger``)."""

    from learnloop.experiments.contextual_embeddings.boundary import (
        quiet_provider_logs,
        require_codex_lockdown,
        require_no_codex_roles,
    )
    from learnloop.experiments.contextual_embeddings.budget import authorized_ledger

    from learnloop.experiments.contextual_embeddings.corpus import _inside_local_root

    # Private run state stays under fixtures-local (pre-paid verify L7): refused before anything.
    if not _inside_local_root(Path(run_dir)):
        raise ValueError("the run directory must be under a fixtures-local directory")
    # No Codex turn of a paid run outside the locked-down transport (55063be64).
    require_codex_lockdown()
    # And none of its roles is a Codex route at all (re-plan 2026-10-22).
    require_no_codex_roles()
    from learnloop.experiments.contextual_embeddings.paid import PaidState, run_contracts
    from learnloop.experiments.contextual_embeddings.adapters import Receipts, VectorStore

    factories = factories or default_factories()
    root = Path(run_dir)
    run_dir = root / str(plan["run_id"])
    handles, snapshots, strata = rebuild_frozen(copies, plan)
    store_dir = reused_store(root, plan, snapshots, reuse_run) if reuse_run else run_dir
    ledger = authorized_ledger(copies, str(plan["run_id"]), new_authorization=new_authorization)
    ledger.start_clock(pins.MAX_WALL_S)
    freeze(run_dir / "frozen", plan, snapshots)
    results: dict[str, Any] = {"run_id": plan["run_id"], "vaults": {}, "status": "complete"}
    provider_keys = {"perplexity": key_envs.get("perplexity"), "voyage": key_envs.get("voyage"),
                     "openrouter": key_envs.get("openrouter"), "anthropic": key_envs.get("anthropic")}
    with quiet_provider_logs():
        for handle, snapshot in zip(handles, snapshots, strict=True):
            from learnloop.experiments.contextual_embeddings.system_arms import prepare_service_copies

            # The stores (content-keyed) and this plan's outcome may live apart (reuse).
            vault_dir = store_dir / handle.label
            out_dir = run_dir / handle.label
            halted = ledger.halted()
            if halted:
                results["vaults"][handle.label] = {"status": "not_run", "reason": "the ledger is halted"}
                results["status"] = "incomplete"
                continue
            preparation: dict[str, Any] | None = None
            try:
                records = ExperimentRecords(vault_dir / "records")
                if bind_receipts is not None:
                    bind_receipts(records.repository)
                with records.receipts(f"e0:{plan['run_id']}:{handle.label}"):
                    caller = LiveRoleCaller(handle.root, handle.vault.config, ledger,
                                            checkpoints=Checkpoints(vault_dir / "llm"),
                                            client_factory=factories.role_clients, records=records,
                                            key_envs=provider_keys, environ=factories.environ,
                                            anthropic_transport=factories.anthropic_transport)
                    # Each pinned model id is checked before any bulk work (re-plan 2026-10-22).
                    model_canaries = canary_models(caller)
                    logged, _counts = logged_questions(handle, snapshot)
                    qwen_factory_for_copy = factories.qwen(handle.vault.config)
                    canaries = PaidState()
                    run_contracts(snapshot, canaries, ledger=ledger, transport=factories.transport,
                                  receipts=Receipts(vault_dir / "receipts.jsonl"),
                                  store=VectorStore(vault_dir / "vectors"),
                                  qwen_client_factory=qwen_factory_for_copy, key_envs=provider_keys,
                                  environ=factories.environ)
                    qwen_ok = (canaries.contracts.get("R1") or {}).get("status") != "failed"
                    system_handles, preparation = prepare_service_copies(
                        handle.root, vault_dir / "service", ledger, snapshot=snapshot,
                        client_factory=factories.backfill, factory_for_config=factories.qwen,
                        backfill=qwen_ok)
                    outcome = run_paid(snapshot, ledger=ledger, caller=caller, run_dir=vault_dir,
                                       transport=factories.transport, qwen_client_factory=qwen_factory_for_copy,
                                       logged=logged, strata=strata[handle.label], key_envs=provider_keys,
                                       environ=factories.environ, system_handles=system_handles,
                                       system_preparation=preparation, system_clients=factories.system_clients,
                                       latency_budget_s=reader_latency_budget_s, contracts=canaries.contracts)
                outcome["service_preparation"] = preparation
                outcome["model_canaries"] = model_canaries
                outcome["records"] = {"judgments": len(records.judgments()), "receipts": records.receipt_count()}
                outcome["run_id"] = plan["run_id"]
                outcome["corpus"] = [snapshot.inventory()]
            except Exception as exc:  # noqa: BLE001 - the aggregate failure report is always written
                outcome = _failure_outcome(plan, handle, ledger, exc, preparation)
            if outcome.get("status") != "complete":
                results["status"] = "incomplete"
            if reuse_run:
                outcome["reused_run"] = reuse_run
            _write_outcome(out_dir, outcome)
            results["vaults"][handle.label] = outcome
    results["ledger"] = ledger.report()
    return results
