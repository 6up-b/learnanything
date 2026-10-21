"""E0 execution: the dry run (this stage) and the paid run's frozen steps.

**The dry run** (``learnloop experiments e0 run --dry-run``) makes zero
network calls and writes nothing to the copies:

* a socket-level guard is installed for its whole duration
  (``socket.socket.connect``/``connect_ex``, ``socket.create_connection``
  and ``socket.getaddrinfo`` raise ``NetworkForbidden`` and are counted);
* every copy's tree is digested (paths, sizes, contents) before and after,
  and a difference fails the run;
* the vault is loaded without the settings file or dotenv, the database
  attached read-only and never migrated.

It reports the frozen plan: arms, units, question counts, token estimates per
provider and route, the estimate per arm and in total against the $25 cap,
the baseline handoff (delivery-fixes commit and policy, extraction engines,
the redacted effective-config allowlist, dense coverage) and which keys are
present (names only).

**The paid run** is a separate, orchestrator-authorized step: ``freeze``
writes the private frozen manifests (environment, corpus, splits, plan,
prompt hashes) into the run directory; the contract canaries come first;
every request is admitted by the E0 ledger; a refusal or an endpoint failure
stops the affected work and the report is marked incomplete with its
original denominators.
"""
from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import socket
import threading
from typing import Any

from learnloop.experiments.contextual_embeddings import credentials, pins
from learnloop.experiments.contextual_embeddings.bank import logged_bank, plan_seeds, smoke_bank, writer_prompt
from learnloop.experiments.contextual_embeddings.corpus import CopyHandle, CorpusSnapshot, alias, build_snapshot, open_copy
from learnloop.experiments.contextual_embeddings.plan import (
    ASSUMPTIONS,
    EMBEDDING_ARMS,
    embedding_arm_estimate,
    llm_estimates,
    query_token_sizes,
    run_id,
    summarize,
    system_arm_estimates,
)


class NetworkForbidden(RuntimeError):
    """A network call was attempted where none is allowed."""


class _Guard:
    def __init__(self) -> None:
        self.attempts = 0
        self.lock = threading.Lock()

    def refuse(self, *_args: Any, **_kwargs: Any) -> Any:
        with self.lock:
            self.attempts += 1
        raise NetworkForbidden("network access is forbidden in an E0 dry run")


@contextmanager
def network_guard() -> Iterator[_Guard]:
    """Refuse every outbound connection and name lookup in this process."""

    guard = _Guard()
    saved = (socket.socket.connect, socket.socket.connect_ex, socket.create_connection, socket.getaddrinfo)
    socket.socket.connect = guard.refuse  # type: ignore[method-assign]
    socket.socket.connect_ex = guard.refuse  # type: ignore[method-assign]
    socket.create_connection = guard.refuse  # type: ignore[assignment]
    socket.getaddrinfo = guard.refuse  # type: ignore[assignment]
    try:
        yield guard
    finally:
        (socket.socket.connect, socket.socket.connect_ex, socket.create_connection,
         socket.getaddrinfo) = saved  # type: ignore[method-assign,assignment]


def tree_digest(root: Path) -> str:
    """Paths, sizes and content hashes of every file under ``root``."""

    digest = hashlib.sha256()
    for path in sorted(Path(root).rglob("*")):
        if path.is_file():
            digest.update(str(path.relative_to(root)).encode())
            digest.update(str(path.stat().st_size).encode())
            with open(path, "rb") as handle:
                for block in iter(lambda: handle.read(1 << 20), b""):
                    digest.update(block)
    return digest.hexdigest()


def _route(config: Any, task: str) -> dict[str, Any]:
    from learnloop.ai.routing import provider_for_task

    try:
        name = provider_for_task(config, task, allow_env=False).provider_name
    except Exception as exc:  # an unconfigured route is reported, not raised
        return {"provider": None, "error": type(exc).__name__}
    profile = config.ai.providers.get(name)
    return {"provider": name, "type": getattr(profile, "type", None), "model": getattr(profile, "model", None)}


def config_allowlist(config: Any) -> dict[str, Any]:
    """The redacted effective-config allowlist (spec §5.1.2): embedding
    switches, model, route, dimensions, rewrite, pool, policy and caps. Never
    a raw config or environment dump; prices only as set/unset."""

    embedding = config.embedding
    retrieval = config.source_retrieval
    tutor = config.tutor_qa

    def set_or_unset(value: Any) -> str:
        return "unset" if value is None else "set"

    return {
        "embedding.enabled": embedding.enabled,
        "embedding.backfill_enabled": embedding.backfill_enabled,
        "embedding.model": embedding.model,
        "embedding.dimensions": embedding.dimensions,
        "embedding.backfill_sources_on_extract": embedding.backfill_sources_on_extract,
        "embedding.source_backfill_max_cost_usd": embedding.source_backfill_max_cost_usd,
        "source_retrieval.enabled": retrieval.enabled,
        "source_retrieval.dense": retrieval.dense,
        "source_retrieval.query_rewrite": retrieval.query_rewrite,
        "source_retrieval.tutor_query_rewrite": retrieval.tutor_query_rewrite,
        "source_retrieval.tutor_rerank": retrieval.tutor_rerank,
        "source_retrieval.pool": retrieval.pool,
        "source_retrieval.pool_keyword_extras": retrieval.pool_keyword_extras,
        "source_retrieval.tutor_candidate_pool": retrieval.tutor_candidate_pool,
        "source_retrieval.tutor_spans": retrieval.tutor_spans,
        "source_retrieval.passage_token_budget": retrieval.passage_token_budget,
        "source_retrieval.complete_passages": retrieval.complete_passages,
        "source_retrieval.rewrite_max_cost_usd": retrieval.rewrite_max_cost_usd,
        "source_retrieval.rerank_max_cost_usd": retrieval.rerank_max_cost_usd,
        "source_retrieval.llm_price_per_million": set_or_unset(retrieval.llm_price_per_million),
        "source_retrieval.query_embedding_price_per_million": set_or_unset(retrieval.query_embedding_price_per_million),
        "tutor_qa.context_token_budget": tutor.context_token_budget,
        "tutor_qa.resolve_references": tutor.resolve_references,
        "tutor_qa.expanded_delivery": tutor.expanded_delivery,
        "source_service.max_daily_cost_usd": getattr(getattr(config, "source_service", None), "max_daily_cost_usd",
                                                     None),
        "routes": {task: _route(config, task) for task in ("embedding", "source_query_rewrite", "source_rerank",
                                                           "tutor_qa")},
        "LEARNLOOP_AI_PROVIDER": credentials.availability(["LEARNLOOP_AI_PROVIDER"])["LEARNLOOP_AI_PROVIDER"],
    }


def dense_coverage(handle: CopyHandle) -> dict[str, Any]:
    """Aggregate dense coverage (``source_vectors.source_coverage``), ids aliased."""

    from learnloop.source_retrieval.source_vectors import source_coverage

    try:
        coverage = source_coverage(handle.vault, handle.repository)
    except Exception as exc:  # an older database without the vector store reads as uncovered
        return {"error": type(exc).__name__}
    return {"model_id": coverage["model_id"], "effective": coverage["effective"], "reason": coverage["reason"],
            "switches": coverage["switches"], "auto_backfill": coverage["auto_backfill"], "totals": coverage["totals"],
            "sources": [{"source": alias("src", source["source_id"]), "blocks": source["blocks"],
                         "covered": source["covered"], "status": source["status"]} for source in coverage["sources"]]}


def split_strata(snapshots: Sequence[CorpusSnapshot], strata: Mapping[str, int] | None = None) -> dict[str, dict[str, int]]:
    """Divide the development strata across vaults by permitted units
    (largest remainder; deterministic)."""

    strata = dict(strata or pins.DEV_STRATA)
    weights = {snapshot.vault_label: len(snapshot.units) for snapshot in snapshots}
    total = sum(weights.values()) or 1
    result: dict[str, dict[str, int]] = {label: {} for label in weights}
    for stratum, count in strata.items():
        shares = {label: count * weight / total for label, weight in weights.items()}
        floors = {label: int(share) for label, share in shares.items()}
        left = count - sum(floors.values())
        for label in sorted(shares, key=lambda label: (-(shares[label] - floors[label]), label))[:left]:
            floors[label] += 1
        for label, value in floors.items():
            result[label][stratum] = value
    return result


def plan_identity(handles: Sequence[CopyHandle], snapshots: Sequence[CorpusSnapshot],
                  strata: Mapping[str, Mapping[str, int]]) -> dict[str, Any]:
    """What a frozen plan is: the run id (pins, policy, units, the bank's
    smoke, logged and seed ids) and the family splits. The paid run rebuilds
    this and refuses any difference (Codex review F5)."""

    bank_ids: list[str] = []
    for handle, snapshot in zip(handles, snapshots, strict=True):
        smoke, _stats = smoke_bank(snapshot)
        logged, _counts = logged_bank(snapshot, handle.repository.question_events(answer_status="answered"))
        seeds, _shortfall = plan_seeds(snapshot, strata=strata[handle.label])
        bank_ids.extend(question.query_id for question in smoke + logged)
        bank_ids.extend(seed.seed_id for seed in seeds)
    return {"run_id": run_id(snapshots, bank_ids),
            "splits": {snapshot.vault_label: dict(sorted(snapshot.family_status.items())) for snapshot in snapshots}}


def migration_head(handle: CopyHandle) -> int | None:
    from contextlib import closing

    from learnloop.db.connection import connect

    with closing(connect(handle.sqlite_path, read_only=True)) as connection:
        row = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
                                 ).fetchone()
        if row is None:
            return None
        value = connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()
    return None if value is None or value[0] is None else int(value[0])


def dry_run(copies: Sequence[Path], *, key_envs: Mapping[str, str] | None = None, env_file: Path | None = None,
            reserve_share: float = 0.0, environ: Mapping[str, str] | None = None) -> dict[str, Any]:
    """The frozen plan and its estimate, with no network and no writes."""

    key_envs = dict(pins.DEFAULT_KEY_ENVS | dict(key_envs or {}))
    roots = [Path(copy) for copy in copies]
    before = {str(root): tree_digest(root) for root in roots}
    with network_guard() as guard:
        if env_file is not None:
            keys = credentials.load_env_file(env_file, key_envs.values())
        else:
            keys = credentials.availability(key_envs.values(), environ=environ)
        snapshots: list[CorpusSnapshot] = []
        handles: list[CopyHandle] = []
        baseline: dict[str, Any] = {"delivery_fixes": pins.DELIVERY_FIXES, "vaults": {}}
        bank_ids: list[str] = []
        bank_summary: dict[str, Any] = {"vaults": {}}
        allowlists: dict[str, Any] = {}
        logged_counts: dict[str, int] = {}
        for root in roots:
            handle = open_copy(root)
            snapshot = build_snapshot(handle, reserve_share=reserve_share)
            handles.append(handle)
            snapshots.append(snapshot)
            allowlists[handle.label] = config_allowlist(handle.vault.config)
            baseline["vaults"][handle.label] = {
                "migration_head": migration_head(handle),
                "extraction_engines": sorted({f"{info.extractor}/{info.extractor_version}"
                                              for info in snapshot.infos.values()}),
                "config_allowlist": allowlists[handle.label],
                "dense_coverage": dense_coverage(handle),
            }
        strata = split_strata(snapshots)
        seeds: dict[str, Any] = {}
        questions: dict[str, dict[str, int]] = {}
        all_bank = []
        for handle, snapshot in zip(handles, snapshots, strict=True):
            smoke, smoke_stats = smoke_bank(snapshot)
            events = handle.repository.question_events(answer_status="answered")
            logged, logged_stats = logged_bank(snapshot, events)
            vault_seeds, shortfall = plan_seeds(snapshot, strata=strata[handle.label])
            seeds[handle.label] = vault_seeds
            development = len(vault_seeds)
            known = (sum(1 for seed in vault_seeds if seed.selection_unit is not None)
                     + sum(1 for question in logged if question.selection is not None))
            questions[handle.label] = {"development": development, "logged": len(logged), "known_location": known}
            logged_counts[handle.label] = len(logged)
            bank_ids.extend(question.query_id for question in smoke + logged)
            bank_ids.extend(seed.seed_id for seed in vault_seeds)
            all_bank.extend(smoke + logged)
            bank_summary["vaults"][handle.label] = {
                "smoke": smoke_stats, "logged": logged_stats, "development_seeds": development,
                "development_strata": strata[handle.label], "development_shortfall": shortfall,
                "known_location_questions": known,
                "logged_by_context": _count(question.stratum for question in logged),
            }
        development_total = sum(item["development"] for item in questions.values())
        bank_summary["totals"] = {
            "smoke": sum(len(smoke_bank(snapshot)[0]) for snapshot in snapshots),
            "development": development_total, "development_target": list(pins.DEV_QUESTIONS),
            "development_within_target": pins.DEV_QUESTIONS[0] <= development_total <= pins.DEV_QUESTIONS[1],
            "logged": sum(logged_counts.values()),
        }
        query_sizes = query_token_sizes(all_bank, development_total)
        arms = [embedding_arm_estimate(arm, snapshots, query_sizes) for arm in EMBEDDING_ARMS]
        query_counts = {label: questions[label]["development"] + questions[label]["logged"]
                        + len(smoke_bank(snapshot)[0]) for label, snapshot in
                        zip((handle.label for handle in handles), snapshots, strict=True)}
        systems = system_arm_estimates(snapshots, allowlists, query_counts)
        roles = llm_estimates(snapshots, seeds, questions)
        totals = summarize(arms, systems, roles)
        prompts = {"writer": _prompt_hash(snapshots, seeds), "versions": {
            role: pin.prompt_version for role, pin in sorted(pins.ROLE_PINS.items())}}
        plan = {
            "status": "dry_run", "run_id": run_id(snapshots, bank_ids), "harness": pins.HARNESS_VERSION,
            # The frozen split the paid run must execute exactly (Codex review F5).
            "reserve_share": float(reserve_share),
            "splits": {snapshot.vault_label: dict(sorted(snapshot.family_status.items())) for snapshot in snapshots},
            "pins_fingerprint": pins.pins_fingerprint(), "seed": pins.SEED,
            "baseline": baseline,
            "corpus": [snapshot.inventory() for snapshot in snapshots],
            "bank": bank_summary,
            "delivery_arms": {arm: spec.description for arm, spec in pins.DELIVERY_ARMS.items()},
            "retrieval_arms": {arm: spec.description for arm, spec in pins.RETRIEVAL_ARMS.items()},
            "embedding_arms": arms, "system_arms": systems, "llm_roles": roles, "totals": totals,
            "by_provider": _by_provider(arms, systems, roles),
            "assumptions": ASSUMPTIONS, "prompts": prompts,
            "limits": {"cap_usd": pins.E0_CAP_USD, "allocation_usd": pins.ALLOCATION_USD,
                       "max_metered_requests": pins.MAX_PAID_REQUESTS, "subscription_requests": "unbounded (owner)",
                       "request_timeout_s": pins.REQUEST_TIMEOUT_S, "max_wall_s_enforced": True,
                       "latency_regression_tolerance": pins.LATENCY_REGRESSION_TOLERANCE,
                       "output_bound": "the ai.output_tokens policy per role profile (reserved as sent)",
                       "token_bound": "UTF-8 bytes + 8 for limits and admission; bytes/3 for estimates",
                       "max_wall_s": pins.MAX_WALL_S, "transient_retries": pins.TRANSIENT_RETRIES,
                       "auth_or_contract_retries": 0, "window_tokens": pins.WINDOW_TOKENS,
                       "d1_evidence_tokens": pins.D1_EVIDENCE_TOKENS, "pool_depth": pins.POOL_DEPTH,
                       "top_k": pins.TOP_K, "bootstrap_resamples": pins.BOOTSTRAP_RESAMPLES},
            "keys": keys,
            "pins": {"embeddings": {name: {"model": pin.model, "provider": pin.provider, "method": pin.method,
                                           "dimensions": pin.dimensions, "output_format": pin.output_format,
                                           "contract_verified": pin.contract_verified,
                                           "price_verified": pin.price_verified,
                                           "price_per_million_upper_bound": pin.price_per_million_upper_bound}
                                    for name, pin in sorted(pins.EMBEDDING_PINS.items())},
                     "roles": {name: {"model": pin.model, "transport": pin.transport, "billing": pin.billing,
                                      "provider_profile": pin.provider_profile, "category": pin.category,
                                      "prompt_version": pin.prompt_version}
                               for name, pin in sorted(pins.ROLE_PINS.items())}},
        }
        network_attempts = guard.attempts
    after = {str(root): tree_digest(root) for root in roots}
    changed = sorted(alias("copy", root) for root in before if before[root] != after[root])
    if changed:
        raise RuntimeError(f"the dry run changed {len(changed)} copies")
    plan["checks"] = {"network_calls": network_attempts, "copies_changed": 0,
                      "copy_tree_digests_equal": True, "settings_file_read": False, "database_mode": "read_only"}
    return plan


def _count(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return dict(sorted(counts.items()))


def _prompt_hash(snapshots: Sequence[CorpusSnapshot], seeds: Mapping[str, Sequence[Any]]) -> str:
    digest = hashlib.sha256()
    for snapshot in snapshots:
        vault_seeds = list(seeds.get(snapshot.vault_label, []))
        for start in range(0, len(vault_seeds), ASSUMPTIONS["writer_batch"]):
            prompt, _refs, _units = writer_prompt(snapshot, vault_seeds[start:start + ASSUMPTIONS["writer_batch"]])
            digest.update(prompt.encode())
    return digest.hexdigest()


def _by_provider(arms: Sequence[Mapping[str, Any]], systems: Sequence[Mapping[str, Any]],
                 roles: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    found: dict[str, dict[str, Any]] = {}
    for row in arms:
        entry = found.setdefault(f"{row['provider']}:{row['model']}", {"tokens": 0, "requests": 0, "estimated_usd": 0.0})
        entry["tokens"] += int(row["tokens"])
        entry["requests"] += int(row["requests"])
        entry["estimated_usd"] = round(entry["estimated_usd"] + float(row["estimated_usd"]), 6)
    for row in systems:
        entry = found.setdefault("openrouter:qwen/qwen3-embedding-8b (system arms)",
                                 {"tokens": 0, "requests": 0, "estimated_usd": 0.0})
        entry["tokens"] += int(row.get("backfill_tokens") or 0)
        entry["estimated_usd"] = round(entry["estimated_usd"] + float(row["estimated_usd"]), 6)
    for row in roles:
        entry = found.setdefault(f"{row['transport']}:{row['model']}",
                                 {"tokens": 0, "requests": 0, "estimated_usd": 0.0, "billing": row["billing"]})
        entry["tokens"] += int(row["input_tokens"]) + int(row["output_tokens"])
        entry["requests"] += int(row["calls"])
        entry["estimated_usd"] = round(entry["estimated_usd"] + float(row["estimated_usd"]), 6)
    return dict(sorted(found.items()))


def render_markdown(plan: Mapping[str, Any]) -> str:
    """The dry-run aggregate as Markdown (no private text)."""

    totals = plan["totals"]
    lines = [f"# E0 dry run `{plan['run_id']}`", "",
             f"Harness {plan['harness']}; pins `{plan['pins_fingerprint'][:12]}`; seed {plan['seed']}.", "",
             f"**Estimate:** ${totals['estimated_usd']:.2f} expected, ${totals['worst_case_usd']:.2f} worst case "
             f"(every request retried twice) against the ${totals['cap_usd']:.0f} cap: "
             f"{'fits' if totals['fits_cap'] else 'DOES NOT FIT'}; allocations "
             f"{'fit' if totals['fits_allocations'] else 'overflow: ' + ', '.join(totals['overflowing_categories'])}.",
             "", "| Category | Expected $ | Worst case $ | Allocation $ | Fits |", "|---|---|---|---|---|"]
    for name, category in totals["categories"].items():
        lines.append(f"| {name} | {category['estimated_usd']:.4f} | {category['worst_case_usd']:.4f} | "
                     f"{category['allocation_usd']:.2f} | {'yes' if category['fits'] else 'no'} |")
    lines += ["", "| Embedding arm | Model | Documents | Chunks | Requests | Tokens | Expected $ |",
              "|---|---|---|---|---|---|---|"]
    for row in plan["embedding_arms"]:
        lines.append(f"| {row['arm']} | {row['model']} | {row['documents']} | {row['chunks']} | {row['requests']} | "
                     f"{row['tokens']:,} | {row['estimated_usd']:.4f} |")
    lines += ["", "| LLM role | Model | Billing | Calls | Input tokens | Output tokens | Expected $ |",
              "|---|---|---|---|---|---|---|"]
    for row in plan["llm_roles"]:
        lines.append(f"| {row['role']} | {row['model']} | {row['billing']} | {row['calls']} | "
                     f"{row['input_tokens']:,} | {row['output_tokens']:,} | {row['estimated_usd']:.4f} |")
    lines += ["", "Keys: " + ", ".join(f"{name} {state}" for name, state in sorted(plan["keys"].items())),
              f"Checks: {json.dumps(plan.get('checks', {}), sort_keys=True)}"]
    return "\n".join(lines) + "\n"


def freeze(run_dir: Path, plan: Mapping[str, Any], snapshots: Sequence[CorpusSnapshot]) -> dict[str, str]:
    """The paid run's private frozen manifests (spec §6), written before any
    call; returns their hashes. Private: under fixtures-local only."""

    from learnloop.experiments.contextual_embeddings.corpus import _inside_local_root

    if not _inside_local_root(run_dir):
        raise ValueError("a run directory must be under fixtures-local")
    run_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "environment.json": {"pins_fingerprint": plan["pins_fingerprint"], "harness": plan["harness"],
                             "keys": plan["keys"], "python_hash_seed": os.environ.get("PYTHONHASHSEED")},
        "corpus.json": [snapshot.inventory() for snapshot in snapshots],
        "splits.json": {snapshot.vault_label: snapshot.family_status for snapshot in snapshots},
        "run_plan.json": dict(plan),
        "candidate_maps.json": {snapshot.vault_label: [{"unit": unit.unit_id, "extraction": unit.extraction_id,
                                                        "members": [[m.span_id, m.start, m.end] for m in unit.members]}
                                                       for unit in snapshot.units] for snapshot in snapshots},
    }
    hashes = {}
    for name, value in files.items():
        text = json.dumps(value, sort_keys=True, indent=1, default=str)
        (run_dir / name).write_text(text, encoding="utf-8")
        hashes[name] = hashlib.sha256(text.encode()).hexdigest()
    return hashes


def require_paid_authorization(*, authorized: bool, dry_run_ok: bool) -> None:
    """A paid run needs the orchestrator's explicit flag and a passing dry run."""

    if not authorized:
        raise PermissionError("a paid E0 run needs --i-am-authorized-to-spend (orchestrator step after review)")
    if not dry_run_ok:
        raise PermissionError("run --dry-run first; its plan must fit the cap")


__all__: Sequence[str] = ("NetworkForbidden", "config_allowlist", "dry_run", "freeze", "network_guard",
                          "render_markdown", "require_paid_authorization", "split_strata", "tree_digest")
