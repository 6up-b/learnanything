"""E0's named system arms on separate service copies (spec §5.4: R0, R1, R1').

The frozen corpus copy is never written. System arms run on *service copies*
made from it through the backup API: production search writes its own
receipts there, and the Qwen arms need Qwen enabled and backfilled, which
changes only that copy's ``learnloop.toml`` and database.

**Policy before encoding (Codex review F1).** Before any production path
runs on a service copy, the copy is REDACTED: the text of every block the
experiment's policy withholds (exam and held-out material, solutions, the
assessment lane; section headers included) is blanked in the copy's own
``source_document_blocks`` (the FTS index follows by its triggers). A blank
block is not embeddable, gives no section-path title and matches no keyword,
so the production backfill, search, rewrite and verification can never read
protected text, and dense coverage is still complete over what remains. The
backfill client is wrapped in ``ProtectedTextGuard`` as a second line: a
batch containing any protected passage is refused before it is sent.

**The specified production interfaces (Codex review F12).**

* ``R0``: today's effective path, ``find_sources`` on the copy as
  configured (policy ``reading``, the question's intent, library scope, the
  intent-specific candidate lists, the mandatory verification of a
  non-explain intent and the ``compare`` delegation), two pages of ten.
* ``R1_service_rrf``: the same ``find_sources`` path on the Qwen copy (R1').
* ``R1_service_pool``: the first-page ``dense_plus_bm25`` variant (R1'),
  ``search_spans`` with that pool.
* ``R1_pool_verify``: the production ``pool_verify`` control (R1): the
  tutor's own ``tutor_pool`` with ``dense_plus_bm25`` and the production
  ``verify_spans`` verification; its ranking is the picks, then the rest of
  the pool (as the T6 report scores it).

Per question each arm records its pages, cross-page duplicates, the
verification status, the pool mode and whether dense ranking was used. A
question whose required verification did not run, or (for a Qwen arm) whose
search fell back from dense ranking, has NO ranking for that arm: it counts
against the arm's completion (S1) instead of being scored as if covered.

Every paid step is admitted by the E0 ledger: embedding requests through
``LedgerEnvelope`` under the production ``spend_envelopes``, any LLM request
(rewrite, verification, comparison) through ``SystemRequestGate``, billed by
the resolved client.

**Resume (Codex review F11).** ``prepare_service_copies`` keeps a state file
per service directory: a copy whose preparation completed for the same
frozen copy, policy and harness is reopened; an incomplete or incompatible
one is moved aside and prepared again; the backfill itself is idempotent
(missing vectors only).
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
import json
import os
from pathlib import Path
import time
from typing import Any

from learnloop.ai.execution import gate_model_requests
from learnloop.ai.spend import is_subscription_transport, spend_envelopes
from learnloop.db.copies import copy_tree_with_databases

from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.bank import BankQuestion
from learnloop.experiments.contextual_embeddings.budget import E0BudgetExceeded, E0Ledger, LedgerEnvelope, Request
from learnloop.experiments.contextual_embeddings.corpus import CorpusSnapshot, PolicySnapshot, _inside_local_root
from learnloop.experiments.contextual_embeddings.retrieval import units_from_blocks

#: Every system arm: (service copy, interface).
SYSTEM_ARMS = {
    "R0": ("R0", "find_sources"),
    "R1_service_rrf": ("R1_service", "find_sources"),
    "R1_service_pool": ("R1_service", "dense_plus_bm25_first_page"),
    "R1_pool_verify": ("R1_service", "pool_verify"),
}
#: Arms whose comparisons need dense ranking (a keyword fallback is no result).
DENSE_ARMS = frozenset({"R1_service_rrf", "R1_service_pool", "R1_pool_verify"})
SERVICE_STATE = "e0_service_state.json"
#: A protected passage is probed by this many leading normalized characters.
GUARD_PROBE_CHARS = 48


class ProtectedTextRefused(E0BudgetExceeded):
    """A request would have carried protected text; nothing was sent."""


def make_service_copy(frozen_root: Path, destination: Path) -> Path:
    """A backup-API copy of a frozen copy, for the system arms."""

    if not _inside_local_root(destination):
        raise ValueError("a service copy must be under fixtures-local")
    copy_tree_with_databases(Path(frozen_root), Path(destination))
    return Path(destination)


#: The orchestrator's switches that enable embeddings on a copy (the copies predate Phase 1).
ENABLE_EMBEDDINGS = {
    "routing": {"embedding": "openrouter_embedding"},
    "profile": {"type": "openai_embedding", "base_url": "https://openrouter.ai/api/v1",
                "api_key_env": "OPENROUTER_API_KEY"},
    "embedding": {"enabled": True, "backfill_enabled": True},
}


def enable_embeddings_on_copy(root: Path) -> None:
    """Set ``ai.routing.embedding``, the ``[ai.providers.openrouter_embedding]``
    profile and ``[embedding] enabled/backfill_enabled`` in a service copy's
    ``learnloop.toml`` (never a tracked vault: the path must be under
    fixtures-local). Refuses a copy whose embedding switches are already on."""

    import tomlkit

    root = Path(root)
    if not _inside_local_root(root):
        raise ValueError("embeddings are enabled only on copies under fixtures-local")
    toml = root / "learnloop.toml"
    document = tomlkit.parse(toml.read_text(encoding="utf-8"))
    embedding = document.get("embedding")
    if embedding is not None and embedding.get("enabled"):
        raise ValueError("embeddings are already enabled on this copy")
    ai = document.setdefault("ai", tomlkit.table())
    ai.setdefault("routing", tomlkit.table())["embedding"] = ENABLE_EMBEDDINGS["routing"]["embedding"]
    providers = ai.setdefault("providers", tomlkit.table())
    profile = tomlkit.table()
    for key, value in ENABLE_EMBEDDINGS["profile"].items():
        profile[key] = value
    providers["openrouter_embedding"] = profile
    table = document.setdefault("embedding", tomlkit.table())
    for key, value in ENABLE_EMBEDDINGS["embedding"].items():
        table[key] = value
    toml.write_text(tomlkit.dumps(document), encoding="utf-8")


# -- policy before encoding -------------------------------------------------------------


def redact_service_copy(handle: Any, policy: PolicySnapshot) -> dict[str, int]:
    """Blank every withheld block's text in a SERVICE copy's database (never
    the frozen copy: the path must be under fixtures-local). Returns counts."""

    from learnloop.db.connection import connect

    if not _inside_local_root(Path(handle.sqlite_path)):
        raise ValueError("only a service copy under fixtures-local is redacted")
    blanked = 0
    with closing(connect(Path(handle.sqlite_path))) as connection:
        rows = connection.execute(
            "SELECT extraction_id, span_id FROM source_document_blocks WHERE text IS NOT NULL AND text != ''"
        ).fetchall()
        withheld = [(str(row[0]), str(row[1])) for row in rows if policy.verdict(str(row[0]), str(row[1]))]
        for extraction_id, span_id in withheld:
            connection.execute("UPDATE source_document_blocks SET text = '' WHERE extraction_id = ? AND span_id = ?",
                               (extraction_id, span_id))
        blanked = len(withheld)
        connection.commit()
    return {"blanked_blocks": blanked}


def _normalize(text: str) -> str:
    return " ".join(str(text or "").split()).lower()


class ProtectedTextGuard:
    """An embedding client wrapper that refuses any batch carrying protected text."""

    def __init__(self, client: Any, probes: Sequence[str]) -> None:
        self._client = client
        self._probes = [probe for probe in probes if probe]
        self.refused = 0

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)

    def embed(self, inputs: list[Any], task_prefix: str) -> Any:
        for value in inputs:
            text = _normalize(value if isinstance(value, str) else getattr(value, "text", "") or "")
            if any(probe in text for probe in self._probes):
                self.refused += 1
                raise ProtectedTextRefused("an embedding request carried protected text; nothing was sent")
        return self._client.embed(inputs, task_prefix)


def protected_probes(snapshot: CorpusSnapshot) -> list[str]:
    """Leading normalized characters of every withheld block long enough to probe."""

    probes = []
    for extraction_id, blocks in snapshot.blocks.items():
        for block in blocks:
            if snapshot.policy.verdict(extraction_id, block.span_id):
                text = _normalize(block.text)
                if len(text) >= 16:
                    probes.append(text[:GUARD_PROBE_CHARS])
    return probes


def guarded_factory(factory: Callable[[], Any], snapshot: CorpusSnapshot) -> Callable[[], Any]:
    probes = protected_probes(snapshot)
    return lambda: ProtectedTextGuard(factory(), probes)


# -- the LLM gate for production paths ----------------------------------------------------


class SystemRequestGate:
    """Admits every physical LLM request a production path makes on a service
    copy (rewrite, verification, comparison) through the E0 ledger, billed by
    the RESOLVED client: a subscription transport at $0; a metered one at
    ``source_retrieval.llm_price_per_million`` and its output bound (unset
    price or unbounded output: refused before sending)."""

    def __init__(self, ledger: E0Ledger, config: Any, *, arm: str) -> None:
        self.ledger = ledger
        self.price = config.source_retrieval.llm_price_per_million
        self.arm = arm

    def admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> Any:
        from learnloop.experiments.contextual_embeddings.callers import estimate_input_tokens

        if getattr(client, "provider_type", None) == "openai_embedding" or purpose == "embedding":
            # An embedding request: admitted by the ledger through the production
            # SpendBudget and the LedgerEnvelope (spend_envelopes), not twice here.
            return None
        subscription = is_subscription_transport(client=client)
        tokens_in = estimate_input_tokens(prompt)
        if not subscription:
            if self.price is None:
                raise E0BudgetExceeded(f"{self.arm}: a metered production route without "
                                       "source_retrieval.llm_price_per_million is refused")
            if budget is None:
                raise E0BudgetExceeded(f"{self.arm}: a metered request without an output bound is refused")
        output = int(budget or 0)
        usd = 0.0 if subscription else (tokens_in + output) * float(self.price) / 1_000_000
        reservation = self.ledger.reserve(Request(
            category="answers_verification", provider=str(getattr(client, "provider_name", "copy_route")),
            route=str(getattr(client, "model", "") or ""), purpose=f"system:{purpose}", arm=self.arm,
            billing="subscription" if subscription else "metered", estimated_usd=usd,
            estimated_tokens=tokens_in + output))
        return (reservation, subscription, time.monotonic())

    def settle(self, admission: Any, usage: Mapping[str, Any]) -> None:
        if admission is None:
            return
        reservation, subscription, started = admission
        cost = usage.get("cost")
        tokens = [usage.get("input_tokens"), usage.get("output_tokens")]
        actual = None
        if isinstance(cost, (int, float)) and not isinstance(cost, bool) and cost >= 0:
            actual = float(cost)
        elif not subscription and self.price is not None and any(isinstance(value, int) for value in tokens):
            actual = sum(int(value or 0) for value in tokens) * float(self.price) / 1_000_000
        self.ledger.settle(reservation, actual_usd=actual,
                           usage={"input_tokens": tokens[0], "output_tokens": tokens[1], "cost": cost},
                           latency_s=round(time.monotonic() - started, 4))


# -- ranking ------------------------------------------------------------------------------


def _keys(hits: Sequence[Any]) -> list[tuple[str, str]]:
    found = []
    for hit in hits:
        if isinstance(hit, Mapping):
            found.append((str(hit["extraction_id"]), str(hit["span_id"])))
        else:
            found.append((str(hit.extraction_id), str(hit.span_id)))
    return found


def _bump(counter: dict[str, int], key: str, amount: int = 1) -> None:
    counter[key] = counter.get(key, 0) + amount


def rank_system(handle: Any, snapshot: CorpusSnapshot, questions: Sequence[BankQuestion], *, arm: str,
                ledger: E0Ledger, query_text: Mapping[str, str],
                clients: Mapping[str, Any] | None = None) -> tuple[dict[str, list[str]], dict[str, Any]]:
    """``{query_id: unit ids}`` for one system arm, and its report (pages,
    duplicates, verification, pool modes, dense use, dropped hits, missing)."""

    from learnloop.source_retrieval.corpus import library_scope
    from learnloop.source_retrieval.find_sources import INTENTS, find_sources
    from learnloop.source_retrieval.search import search_spans
    from learnloop.source_retrieval.tutor import tutor_pool
    from learnloop.source_retrieval.verify import verify_spans

    clients = dict(clients or {})
    interface = SYSTEM_ARMS[arm][1]
    envelope = LedgerEnvelope(ledger, category="embeddings", provider="openrouter",
                              route=pins.EMBEDDING_PINS["qwen3_8b"].model, arm=arm)
    gate = SystemRequestGate(ledger, handle.vault.config, arm=arm)
    scope = library_scope(handle.repository)
    ranked: dict[str, list[str]] = {}
    report: dict[str, Any] = {"arm": arm, "interface": interface, "questions": len(questions), "ranked": 0,
                              "missing": {}, "withheld": 0, "unmapped": 0, "pages": {}, "page_duplicates": 0,
                              "verification": {}, "pool_modes": {}, "dense_used": 0, "latency_s": []}
    with spend_envelopes(envelope), gate_model_requests(gate):
        for question in questions:
            text = query_text[question.query_id]
            owner = f"e0:{arm}:{question.query_id}"
            started = time.monotonic()
            missing: str | None = None
            lists: list[str] | None = []
            if interface == "find_sources":
                intent = question.intent if question.intent in INTENTS else "explain"
                kwargs = dict(policy="reading", intent=intent, scope="library", limit=pins.TOP_K, owner_id=owner,
                              embedder=clients.get("embedder"), rewrite_client=clients.get("rewrite_client"),
                              rerank_client=clients.get("rerank_client"),
                              compare_client=clients.get("compare_client"))
                first = find_sources(handle.vault, handle.repository, text, **kwargs)
                pages = [first]
                if first.cursor and intent != "compare" and len(first.hits) < pins.POOL_DEPTH:
                    pages.append(find_sources(handle.vault, handle.repository, text, cursor=first.cursor, **kwargs))
                keys: list[tuple[str, str]] = []
                for page in pages:
                    for key in _keys(page.hits):
                        if key in keys:
                            report["page_duplicates"] += 1
                        else:
                            keys.append(key)
                _bump(report["pages"], str(len(pages)))
                if intent == "compare":
                    # Delegated to compare_sources (its own searches, verification
                    # and status); its dense use is not on this manifest.
                    verification = f"compare:{first.status}"
                    lists = None
                else:
                    verification = str((first.manifest.get("verification") or {}).get("status"))
                    search = first.manifest.get("search") or {}
                    lists = list(search.get("lists") or [])
                    _bump(report["pool_modes"], str((search.get("pool") or {}).get("mode")))
                _bump(report["verification"], verification)
                if intent not in ("explain", "compare") and verification not in ("verified", "cached"):
                    # The production path must verify this intent: unverified is no ranking.
                    missing = f"verification_{verification}"
            elif interface == "dense_plus_bm25_first_page":
                result = search_spans(handle.vault, handle.repository, text, scope, deep=True, limit=pins.POOL_DEPTH,
                                      pool="dense_plus_bm25", owner_id=owner, embedder=clients.get("embedder"),
                                      rewrite_client=clients.get("rewrite_client"))
                keys = _keys(result.hits)
                lists = list(result.lists)
                mode = str((result.pool or {}).get("mode"))
                _bump(report["pool_modes"], mode)
                if mode != "dense_plus_bm25":
                    missing = f"pool_fallback_{mode}"
            else:  # pool_verify
                pool = tutor_pool(handle.vault, handle.repository, context="library", question_md=text,
                                  learning_object_ids=(), item=None, embedder=clients.get("embedder"),
                                  rewrite_client=clients.get("rewrite_client"), owner_id=owner,
                                  pool="dense_plus_bm25", scope=scope)
                lists = list(pool.search.lists)
                mode = str((pool.search.pool or {}).get("mode"))
                _bump(report["pool_modes"], mode)
                outcome = verify_spans(handle.vault, handle.repository, question=text, pool=list(pool.pool),
                                       pick_at_most=handle.vault.config.source_retrieval.tutor_spans,
                                       client=clients.get("rerank_client"), owner_id=owner)
                _bump(report["verification"], outcome.status)
                picks = _keys(outcome.picks)
                keys = picks + [key for key in _keys(pool.pool) if key not in picks]
                if not outcome.ran:
                    missing = f"verification_{outcome.status}"
            dense = lists is not None and "meaning" in lists
            report["dense_used"] += int(dense)
            if missing is None and arm in DENSE_ARMS and lists is not None and not dense:
                missing = "dense_not_used"
            report["latency_s"].append(round(time.monotonic() - started, 4))
            if missing is not None:
                _bump(report["missing"], missing)
                continue
            units, counts = units_from_blocks(snapshot, keys)
            ranked[question.query_id] = units[: pins.POOL_DEPTH]
            report["ranked"] += 1
            report["withheld"] += counts["withheld"]
            report["unmapped"] += counts["unmapped"]
    from learnloop.experiments.contextual_embeddings.metrics import latency_summary

    report["latency_s"] = latency_summary(report["latency_s"])
    return ranked, report


# -- the service copies -------------------------------------------------------------------


def backfill_service_copy(handle: Any, ledger: E0Ledger, *, client_factory: Any = None) -> list[dict[str, Any]]:
    """The production source backfill on a REDACTED service copy, under the E0 ledger."""

    from learnloop.source_retrieval.source_vectors import backfill_source_vectors

    envelope = LedgerEnvelope(ledger, category="embeddings", provider="openrouter",
                              route=pins.EMBEDDING_PINS["qwen3_8b"].model, arm="R1_service_backfill")
    reports = []
    with spend_envelopes(envelope):
        for extraction_id in _current(handle):
            reports.append(backfill_source_vectors(handle.vault, extraction_id, client_factory=client_factory))
    return reports


def _current(handle: Any) -> list[str]:
    from learnloop.source_retrieval.corpus import current_extractions

    return sorted(current_extractions(handle.repository))


def dense_coverage_complete(handle: Any) -> dict[str, Any]:
    """Whether every embeddable (permitted) block of every current extraction
    of the service copy has a vector: the condition for a fully covered arm."""

    from learnloop.source_retrieval.source_vectors import source_coverage

    coverage = source_coverage(handle.vault, handle.repository)
    incomplete = [source for source in coverage["sources"] if source["status"] not in ("complete", "empty")]
    return {"effective": coverage["effective"], "complete": not incomplete, "incomplete_sources": len(incomplete),
            "sources": len(coverage["sources"])}


def open_service(root: Path) -> Any:
    """A service copy opened writable through the vault's own repository
    (production search writes its receipts there; never the frozen copy)."""

    from learnloop.experiments.contextual_embeddings.corpus import CopyHandle
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths
    from learnloop.vault.repository import vault_repository

    root = Path(root)
    if not _inside_local_root(root):
        raise ValueError("a service copy must be under fixtures-local")
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    return CopyHandle(root, vault, vault_repository(paths), Path(paths.sqlite_path))


def _write_state(path: Path, state: Mapping[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(dict(state), sort_keys=True, indent=1), encoding="utf-8")
    os.replace(temporary, path)


def _read_state(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _identity(frozen_root: Path, snapshot: CorpusSnapshot) -> dict[str, Any]:
    from learnloop.experiments.contextual_embeddings.runner import tree_digest

    return {"frozen_tree": tree_digest(Path(frozen_root)), "policy": snapshot.policy.fingerprint,
            "harness": pins.HARNESS_VERSION}


def _prepare_one(frozen_root: Path, root: Path, name: str, snapshot: CorpusSnapshot, identity: Mapping[str, Any],
                 state: dict[str, Any], state_path: Path, *, enable: bool) -> tuple[Any, str]:
    """One service copy, reopened when its completed preparation matches."""

    entry = state.get(name) or {}
    if root.exists() and entry.get("status") == "ready" and entry.get("identity") == dict(identity):
        return open_service(root), "reopened"
    if root.exists():
        # Incomplete or for another frozen copy/policy: set aside, never reused.
        aside = root.with_name(f".{root.name}.stale-{int(time.time())}-{os.getpid()}")
        root.rename(aside)
    state[name] = {"status": "copying", "identity": dict(identity)}
    _write_state(state_path, state)
    make_service_copy(frozen_root, root)
    if enable:
        enable_embeddings_on_copy(root)
    handle = open_service(root)
    redaction = redact_service_copy(handle, snapshot.policy)
    state[name] = {"status": "ready", "identity": dict(identity), "redaction": redaction}
    _write_state(state_path, state)
    return handle, "prepared"


def prepare_service_copies(frozen_root: Path, service_root: Path, ledger: E0Ledger, *, snapshot: CorpusSnapshot,
                           client_factory: Callable[[], Any] | None = None,
                           factory_for_config: Callable[[Any], Callable[[], Any]] | None = None,
                           ) -> tuple[dict[str, Any], dict[str, Any]]:
    """``{"R0": handle, "R1_service": handle}`` and the preparation report
    (per copy: prepared or reopened, the redaction, the backfill reports and
    the dense coverage). Resumable; see the module docstring."""

    service_root = Path(service_root)
    if not _inside_local_root(service_root):
        raise ValueError("service copies must be under fixtures-local")
    service_root.mkdir(parents=True, exist_ok=True)
    state_path = service_root / SERVICE_STATE
    state = _read_state(state_path)
    identity = _identity(frozen_root, snapshot)
    r0, r0_how = _prepare_one(frozen_root, service_root / "r0", "r0", snapshot, identity, state, state_path,
                              enable=False)
    qwen, qwen_how = _prepare_one(frozen_root, service_root / "qwen", "qwen", snapshot, identity, state, state_path,
                                  enable=True)
    if client_factory is None:
        if factory_for_config is None:
            from learnloop.experiments.contextual_embeddings.live import qwen_factory as factory_for_config
        client_factory = factory_for_config(qwen.vault.config)
    backfill = backfill_service_copy(qwen, ledger, client_factory=guarded_factory(client_factory, snapshot))
    coverage = dense_coverage_complete(qwen)
    report = {"r0": {"how": r0_how, "redaction": state["r0"].get("redaction")},
              "qwen": {"how": qwen_how, "redaction": state["qwen"].get("redaction"), "coverage": coverage,
                       "backfill": [{key: item.get(key) for key in ("status", "records", "embedded", "reason")}
                                    for item in backfill]}}
    return {"R0": r0, "R1_service": qwen}, report
