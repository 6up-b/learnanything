"""E1 consumes E0 by path: import (copies), replay (no call) and verification.

**Import.** ``import_e0`` copies, once E0's run has finished (every copy has
its ``results.json``), what E1 reads into E1's own ``fixtures-local``: the
run's frozen manifests and results, each copy's content-keyed stores (LLM
checkpoints, vectors; E0's ``--reuse-run`` puts them in the reused run's
directory, which the results name), E0's frozen vault copies, and the label
pools read from E0's experiment records. Databases go through the backup
API (``learnloop.db.copies``) and are put in rollback-journal mode. The
manifest records every part's tree digest; E1 never reads or writes E0's
worktree afterwards.

**Replay.** Per copy, the E0 pipeline runs again with replay doubles: the
corpus is rebuilt under E0's frozen plan (pins, reserve share, strata, splits
and the run id must hold), the bank, the R3 contexts and the label passes come from E0's
checkpoints (``ReplayRoleCaller``: a missing result raises ``ReplayMiss``,
a recorded failure raises the same classified failure E0 saw), and every
representation arm ranks from E0's stored vectors (a zero-cap ledger
refuses any request before it is sent, so a missing vector is a reported
gap, never a call). The label pools come from E0's recorded verdicts; a
wrong pool changes the prompt, misses the checkpoint and is caught.

**Verification.** The replayed labels and rankings are scored with E0's own
code and must reproduce E0's published ``retrieval_slices`` for every
representation arm (and its κ): otherwise E1 refuses to score.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any

from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.bank import (
    LABEL_VERSION,
    BankQuestion,
    QuestionLabels,
    accept_agreed,
    adjudicate,
    audit_plan,
    evidence_sets_from_labels,
    freeze_context,
    label_question,
    logged_questions,
    plan_seeds,
    smoke_bank,
    write_questions,
)
from learnloop.experiments.contextual_embeddings.budget import E0Ledger, E0ProviderFailure, E0Stop
from learnloop.experiments.contextual_embeddings.callers import Checkpoints, LiveRoleCaller, checkpoint_key
from learnloop.experiments.contextual_embeddings.corpus import CopyHandle, CorpusSnapshot, _inside_local_root
from learnloop.experiments.contextual_embeddings.e1 import pins as e1_pins

IMPORT_MANIFEST = "import_manifest.json"
#: Lock, claim and temporary files are never imported.
_SKIPPED_SUFFIXES = (".lock", ".claim", ".tmp")
#: Metrics compared with E0's published slices (all of ``arm_summary``'s keys).
VERIFIED_SLICES = ("primary_development", "development_all", "logged")
VERIFIED_TOLERANCE = 1e-9


class ReplayMiss(RuntimeError):
    """A result E0 never recorded: replay cannot stand in for a call."""


class ImportRefused(ValueError):
    """E0's run is not finished, or its outputs are not where they should be."""


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def _ignore(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name.endswith(_SKIPPED_SUFFIXES) or name.startswith(".")
            and not name.endswith(".failed.json")}


# -- import ----------------------------------------------------------------------------
@dataclass(frozen=True)
class ImportLayout:
    """Where an import keeps each part (all under E1's fixtures-local)."""

    root: Path

    @property
    def manifest_path(self) -> Path:
        return self.root / IMPORT_MANIFEST

    def manifest(self) -> dict[str, Any]:
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    @property
    def frozen(self) -> Path:
        return self.root / "frozen"

    def plan(self) -> dict[str, Any]:
        return json.loads((self.frozen / "run_plan.json").read_text(encoding="utf-8"))

    def vault(self, label: str) -> Path:
        return self.root / "vaults" / label

    def store(self, label: str) -> Path:
        return self.root / "stores" / label

    def results(self, label: str) -> dict[str, Any]:
        return json.loads((self.root / "results" / f"{label}.json").read_text(encoding="utf-8"))

    def pools(self, label: str) -> dict[str, list[str]]:
        return json.loads((self.root / "label_pools" / f"{label}.json").read_text(encoding="utf-8"))

    @property
    def labels(self) -> list[str]:
        return list(self.manifest()["labels"])


def e0_run_state(e0_run_dir: Path) -> dict[str, Any]:
    """What an E0 run directory holds, read-only: its frozen plan, each copy's
    results (or their absence) and where its stores live."""

    e0_run_dir = Path(e0_run_dir)
    frozen = e0_run_dir / "frozen"
    if not (frozen / "run_plan.json").is_file() or not (frozen / "splits.json").is_file():
        raise ImportRefused("the E0 run directory has no frozen plan")
    labels = sorted(json.loads((frozen / "splits.json").read_text(encoding="utf-8")))
    results: dict[str, Any] = {}
    stores: dict[str, str] = {}
    for label in labels:
        path = e0_run_dir / label / "results.json"
        if path.is_file():
            value = json.loads(path.read_text(encoding="utf-8"))
            results[label] = value
            reused = value.get("reused_run")
            stores[label] = str((e0_run_dir.parent / reused / label) if reused else (e0_run_dir / label))
    return {"run_id": e0_run_dir.name, "labels": labels, "results": results, "stores": stores,
            "complete": len(results) == len(labels)}


def import_e0(e0_run_dir: Path, vaults_dir: Path, destination: Path) -> dict[str, Any]:
    """Copy a FINISHED E0 run's outputs into E1's fixtures-local (see the module docstring)."""

    from learnloop.db.copies import copy_tree_with_databases
    from learnloop.experiments.contextual_embeddings.corpus import to_rollback_journal
    from learnloop.experiments.contextual_embeddings.runner import tree_digest

    destination = Path(destination)
    if not _inside_local_root(destination):
        raise ImportRefused("an E1 import must be made under a fixtures-local directory")
    if destination.exists():
        raise ImportRefused("the import directory already exists; an import is made once")
    state = e0_run_state(e0_run_dir)
    if not state["complete"]:
        missing = sorted(set(state["labels"]) - set(state["results"]))
        raise ImportRefused("E0's run has not finished: no results for " + ", ".join(missing))
    layout = ImportLayout(destination)
    copy_tree_with_databases(Path(e0_run_dir) / "frozen", layout.frozen, ignore=_ignore)
    digests: dict[str, Any] = {"frozen": tree_digest(layout.frozen), "copies": {}}
    for label in state["labels"]:
        source_vault = Path(vaults_dir) / label
        if not (source_vault / "learnloop.toml").is_file():
            raise ImportRefused(f"E0's frozen vault copy {label} is not under the vaults directory")
        for database in copy_tree_with_databases(source_vault, layout.vault(label), ignore=_ignore):
            to_rollback_journal(database)
        store = Path(state["stores"][label])
        for part in ("llm", "vectors"):
            if (store / part).is_dir():
                copy_tree_with_databases(store / part, layout.store(label) / part, ignore=_ignore)
        (layout.root / "results").mkdir(parents=True, exist_ok=True)
        (layout.root / "results" / f"{label}.json").write_text(
            json.dumps(state["results"][label], sort_keys=True, indent=1), encoding="utf-8")
        pools = label_pools_from_records(store / "records", layout.root / "work" / label / "records")
        (layout.root / "label_pools").mkdir(parents=True, exist_ok=True)
        (layout.root / "label_pools" / f"{label}.json").write_text(json.dumps(pools, sort_keys=True, indent=1),
                                                                     encoding="utf-8")
        digests["copies"][label] = {
            "vault": tree_digest(layout.vault(label)), "store": tree_digest(layout.store(label)),
            "results": _sha(state["results"][label]), "pools": _sha(pools)}
    manifest = {"version": 1, "e0_run_id": state["run_id"], "labels": state["labels"],
                "e0_stores": {label: Path(path).parent.name for label, path in state["stores"].items()},
                "e0_plan_sha": _sha(layout.plan()), "digests": digests,
                "label_version": LABEL_VERSION}
    layout.manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=1), encoding="utf-8")
    return manifest


def label_pools_from_records(records: Path, work: Path) -> dict[str, list[str]]:
    """``{query_id: [unit ids]}``: every unit a label pass of THIS rubric
    version judged, from a backup copy of E0's experiment records."""

    from learnloop.db.copies import copy_tree_with_databases
    from learnloop.experiments.contextual_embeddings.records import ExperimentRecords

    if not (Path(records) / "learnloop.toml").is_file():
        return {}
    copy_tree_with_databases(Path(records), Path(work), ignore=_ignore)
    pools: dict[str, set[str]] = {}
    for row in ExperimentRecords(Path(work)).judgments("e0_label"):
        if row.get("prompt_version") == LABEL_VERSION and row.get("right_id"):
            pools.setdefault(str(row["left_id"]), set()).add(str(row["right_id"]))
    return {query_id: sorted(units) for query_id, units in sorted(pools.items())}


def verify_import(layout: ImportLayout) -> list[str]:
    """Each imported part still hashes to its manifest digest."""

    from learnloop.experiments.contextual_embeddings.runner import tree_digest

    manifest = layout.manifest()
    problems = []
    if tree_digest(layout.frozen) != manifest["digests"]["frozen"]:
        problems.append("frozen manifests changed since the import")
    for label, expected in manifest["digests"]["copies"].items():
        if tree_digest(layout.vault(label)) != expected["vault"]:
            problems.append(f"{label}: vault copy changed since the import")
        if tree_digest(layout.store(label)) != expected["store"]:
            problems.append(f"{label}: stores changed since the import")
        if _sha(layout.results(label)) != expected["results"] or _sha(layout.pools(label)) != expected["pools"]:
            problems.append(f"{label}: results or label pools changed since the import")
    return problems


# -- replay doubles --------------------------------------------------------------------------
class ReplayRoleCaller(LiveRoleCaller):
    """E0's role calls answered from E0's checkpoints only (never sent)."""

    def __init__(self, handle: CopyHandle, checkpoints: Checkpoints, scratch: Path) -> None:
        super().__init__(handle.root, handle.vault.config, zero_ledger(scratch), checkpoints=checkpoints,
                         key_envs={"anthropic": pins.ANTHROPIC_KEY_ENV}, environ={})
        self.replayed = 0
        self.misses: list[str] = []

    def call(self, role: str, *, prompt: str, result_model: Any, arm: str | None = None) -> Any:
        pin = self.role_pins[role]
        _client, identity = self._client(pin)
        key = checkpoint_key(pin, prompt, result_model, identity=identity, output_bound=self.output_bound(pin))
        saved = self.checkpoints.get(key)
        if saved is not None:
            self.replayed += 1
            return result_model.model_validate(saved["result"])
        known = self.checkpoints.failure(key)
        if known:
            raise E0ProviderFailure(str(known.get("classification") or "unknown"), reason=known.get("reason"),
                                    status_code=known.get("status_code"), details=known.get("details") or {})
        self.misses.append(role)
        raise ReplayMiss(f"no E0 checkpoint for a {role} request")


class QwenReplayClient:
    """The production OpenRouter embedding client's IDENTITY (the Qwen
    adapter's space ids hash it), without a key and without ``embed``."""

    provider_type = "openai_embedding"

    def __init__(self, config: Any) -> None:
        from learnloop.ai.providers.openai_embedding import DEFAULT_BASE_URL, DEFAULT_MODEL
        from learnloop.config.schema import DEFAULT_EMBEDDING_PROVIDER

        name = config.ai.routing.embedding or DEFAULT_EMBEDDING_PROVIDER
        self.profile = config.ai.providers[name]
        self.default_base_url = DEFAULT_BASE_URL
        self.model_id = self.profile.model or DEFAULT_MODEL
        self.model = self.model_id
        self.dims = getattr(self.profile, "dimensions", 4096)

    def embed(self, *_args: Any, **_kwargs: Any) -> Any:
        raise ReplayMiss("a Qwen vector E0 never stored")


class RefusingTransport:
    def post(self, *_args: Any, **_kwargs: Any) -> Any:
        raise ReplayMiss("a hosted vector E0 never stored")


def zero_ledger(scratch: Path) -> E0Ledger:
    """A ledger that admits nothing: any request is refused before it is sent."""

    return E0Ledger(Path(scratch) / "replay-ledger", cap_usd=0.0,
                    allocation={key: 0.0 for key in pins.ALLOCATION_USD}, max_requests=0, max_subscription_requests=0)


# -- the replay ----------------------------------------------------------------------------
@dataclass
class Replayed:
    label: str
    handle: CopyHandle
    snapshot: CorpusSnapshot
    smoke: list[BankQuestion]
    questions: list[BankQuestion]
    headers: dict[str, str]
    rankings: dict[str, dict[str, list[str]]]
    labels: dict[str, QuestionLabels]
    e0_results: dict[str, Any]
    gaps: dict[str, Any] = field(default_factory=dict)
    verification: dict[str, Any] = field(default_factory=dict)

    @property
    def all_questions(self) -> list[BankQuestion]:
        return [*self.smoke, *self.questions]


def replay_labels(snapshot: CorpusSnapshot, questions: Sequence[BankQuestion], pools: Mapping[str, Sequence[str]],
                  caller: Any, gaps: dict[str, Any]) -> dict[str, QuestionLabels]:
    """E0's ``paid.label_all`` with E0's own pools, from checkpoints: a stop
    or a question failure ends or skips exactly as it did in E0."""

    from learnloop.experiments.contextual_embeddings.paid import QUESTION_FAILURES

    labelled: dict[str, QuestionLabels] = {}
    stopped = False
    for question in questions:
        pool = pools.get(question.query_id)
        if pool is None:
            gaps["labels_unlabelled_in_e0"] = gaps.get("labels_unlabelled_in_e0", 0) + 1
            continue
        try:
            labelled[question.query_id] = label_question(question, list(pool), snapshot, caller)
        except E0ProviderFailure as exc:
            if exc.classification not in QUESTION_FAILURES:
                stopped = True
                break
            gaps["labels_failed_in_e0"] = gaps.get("labels_failed_in_e0", 0) + 1
        except (E0Stop, ReplayMiss):
            gaps["labels_missing"] = gaps.get("labels_missing", 0) + 1
    plan = audit_plan(list(labelled.values()))
    by_id = {question.query_id: question for question in questions}
    for query_id, labels in labelled.items():
        question = by_id[query_id]
        if query_id in plan:
            labels.audit_reason = plan[query_id]
            if not stopped:
                try:
                    adjudicate(question, labels, snapshot, caller)
                except E0ProviderFailure as exc:
                    if exc.classification not in QUESTION_FAILURES:
                        stopped = True
                except (E0Stop, ReplayMiss):
                    gaps["audits_missing"] = gaps.get("audits_missing", 0) + 1
            if not labels.adjudicated:
                if plan[query_id] == "seeded_sample":
                    accept_agreed(labels)
                else:
                    labels.unresolved = True
        else:
            accept_agreed(labels)
        question.evidence_sets = evidence_sets_from_labels(labels, snapshot)
        question.label_provenance = "adjudicated" if labels.adjudicated else "model_only"
    return labelled


def representation_rankings(snapshot: CorpusSnapshot, questions: Sequence[BankQuestion], headers: Mapping[str, str],
                            *, store: Any, config: Any, scratch: Path, gaps: dict[str, Any],
                            arms: Sequence[str] = e1_pins.E0_REPRESENTATION_ARMS,
                            adapters: dict[str, Any] | None = None) -> dict[str, dict[str, list[str]]]:
    """Every E0 representation arm ranked from E0's stored vectors only."""

    from learnloop.experiments.contextual_embeddings.adapters import AdapterError, Receipts
    from learnloop.experiments.contextual_embeddings.paid import make_adapter, rank_arm

    ledger = zero_ledger(scratch)
    rankings: dict[str, dict[str, list[str]]] = {}
    for arm in arms:
        if arm == "R3" and not headers:
            gaps.setdefault("arms_missing", {})[arm] = "no R3 contexts"
            continue
        try:
            adapter = make_adapter(arm, snapshot, ledger=ledger, transport=RefusingTransport(), receipts=Receipts(None),
                                   store=store, qwen_client_factory=lambda: QwenReplayClient(config))
            rankings[arm] = rank_arm(arm, snapshot, list(questions), adapter,
                                     headers=headers if arm == "R3" else None)
            if adapters is not None:
                adapters[arm] = adapter
        except (E0Stop, ReplayMiss, AdapterError) as exc:
            # A vector E0 never stored: the arm is a gap (a fill needs the paid stage).
            gaps.setdefault("arms_missing", {})[arm] = type(exc).__name__
    return rankings


def replay_copy(layout: ImportLayout, label: str, *, scratch: Path, store: Any = None) -> Replayed:
    """One copy's E0 run, replayed (see the module docstring)."""

    from learnloop.experiments.contextual_embeddings.adapters import VectorStore
    from learnloop.experiments.contextual_embeddings.retrieval import generate_contexts

    handle, snapshot, strata = rebuild_copy(layout, label)
    checkpoints = Checkpoints(layout.store(label) / "llm")
    caller = ReplayRoleCaller(handle, checkpoints, scratch)
    gaps: dict[str, Any] = {}
    smoke, _ = smoke_bank(snapshot)
    seeds, _ = plan_seeds(snapshot, strata=strata)
    development, writer = write_questions(snapshot, seeds, caller)
    if writer.get("stopped"):
        gaps["writer_stopped"] = True
    logged, _ = logged_questions(handle, snapshot)
    questions = [*development, *logged]
    for question in [*smoke, *questions]:
        freeze_context(question, snapshot)
    try:
        headers, _stats = generate_contexts(snapshot, caller)
    except (E0Stop, ReplayMiss):
        headers = {}
    store = store if store is not None else VectorStore(layout.store(label) / "vectors")
    rankings = representation_rankings(snapshot, [*smoke, *questions], headers, store=store,
                                       config=handle.vault.config, scratch=scratch, gaps=gaps)
    labels = replay_labels(snapshot, questions, layout.pools(label), caller, gaps)
    if caller.misses:
        gaps["checkpoint_misses"] = len(caller.misses)
    return Replayed(label, handle, snapshot, smoke, questions, headers, rankings, labels, layout.results(label), gaps)


def rebuild_copy(layout: ImportLayout, label: str) -> tuple[CopyHandle, CorpusSnapshot, dict[str, int]]:
    """One imported copy rebuilt under E0's frozen plan: E0's pins, its
    reserve share and strata, and its family splits must all hold (the
    run-wide run id is checked over every copy by :func:`run_identity`)."""

    from learnloop.experiments.contextual_embeddings.corpus import build_snapshot, open_copy
    from learnloop.experiments.contextual_embeddings.live import PlanMismatch

    plan = layout.plan()
    if plan.get("pins_fingerprint") != pins.pins_fingerprint():
        raise PlanMismatch("E0's pins changed since its plan was frozen: this checkout cannot replay it")
    handle = open_copy(layout.vault(label), load_environment=False)
    snapshot = build_snapshot(handle, reserve_share=float(plan["reserve_share"]))
    strata = dict((((plan.get("bank") or {}).get("vaults") or {}).get(label) or {}).get("development_strata") or {})
    if not strata:
        raise PlanMismatch(f"E0's plan has no frozen strata for {label}")
    if dict(sorted(snapshot.family_status.items())) != (plan.get("splits") or {}).get(label):
        raise PlanMismatch(f"{label} does not rebuild to E0's frozen family splits")
    return handle, snapshot, strata


def run_identity(layout: ImportLayout) -> str:
    """E0's run id rebuilt over every imported copy (must equal E0's plan)."""

    from learnloop.experiments.contextual_embeddings.corpus import build_snapshot, open_copy
    from learnloop.experiments.contextual_embeddings.runner import plan_identity

    plan = layout.plan()
    handles = [open_copy(layout.vault(label), load_environment=False) for label in layout.labels]
    snapshots = [build_snapshot(handle, reserve_share=float(plan["reserve_share"])) for handle in handles]
    strata = {handle.label: dict(((plan.get("bank") or {}).get("vaults") or {}).get(handle.label, {})
                                 .get("development_strata") or {}) for handle in handles}
    return str(plan_identity(handles, snapshots, strata)["run_id"])


def verify_replay(replayed: Replayed) -> dict[str, Any]:
    """The replay must reproduce E0's published slices for every
    representation arm it ranked, and E0's label κ."""

    from learnloop.experiments.contextual_embeddings.evaluate import agreement, question_rows
    from learnloop.experiments.contextual_embeddings.paid import slice_summaries

    rows = question_rows(replayed.snapshot, replayed.questions, replayed.rankings, replayed.labels)
    slices = slice_summaries(rows, sorted(replayed.rankings))
    published = replayed.e0_results.get("retrieval_slices") or {}
    mismatches = []
    compared = 0
    for name in VERIFIED_SLICES:
        for arm, mine in slices.get(name, {}).items():
            theirs = (published.get(name) or {}).get(arm)
            if theirs is None:
                mismatches.append(f"{name}/{arm}: not in E0's results")
                continue
            for metric, value in mine.items():
                other = theirs.get(metric)
                compared += 1
                if (value is None) != (other is None) or (value is not None and abs(float(value) - float(other))
                                                          > VERIFIED_TOLERANCE):
                    mismatches.append(f"{name}/{arm}/{metric}")
    kappa = agreement(list(replayed.labels.values()))["agreement"]["kappa"]
    published_kappa = ((replayed.e0_results.get("label_quality") or {}).get("agreement") or {}).get("kappa")
    if (kappa is None) != (published_kappa is None) or (kappa is not None and abs(kappa - published_kappa) > 1e-9):
        mismatches.append("label_quality/kappa")
    result = {"ok": not mismatches and compared > 0, "compared": compared, "mismatches": mismatches[:50],
              "arms": sorted(replayed.rankings), "gaps": dict(replayed.gaps)}
    replayed.verification = result
    return result


def question_texts(replayed: Replayed) -> dict[str, str]:
    from learnloop.experiments.contextual_embeddings.paid import effective_query

    return {question.query_id: effective_query(question, replayed.snapshot) for question in replayed.all_questions}
