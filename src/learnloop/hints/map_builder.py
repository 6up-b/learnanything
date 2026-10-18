"""Adaptive hints H1: building, merging and reading approach maps (spec §4.3, §4.3.1, §7.2-7.3).

**One structured call per map** on route ``approach_map`` (unset: the active
provider; any chat profile, Codex included), through ``PaidCalls``: receipts
under owner kind ``approach_map``, the validated answer checkpointed before it
is written (a rerun never pays twice), Codex and the ChatGPT plan
``estimated_only``. A metered call is admitted only inside the shared daily
envelope ``hints.maps.max_daily_cost_usd`` (reserved atomically in the vault's
spend ledger, every process; RW4a's ``SharedDailyEnvelope``) at
``hints.price_per_million`` (unset: refused before sending). Because admission
follows the RESOLVED route's billing, ``LEARNLOOP_AI_PROVIDER`` can move the
route but never past the cap.

**Validation in code** (:func:`learnloop.hints.maps.validate_map`): a failing
map is re-asked once with its reasons, then not stored. Every validation is
appended to ``judgment_ledger`` (task ``approach_map_valid``, judge
``verifier``): ``valid``, ``invalid_reasked`` or ``invalid_not_stored``, with
the reasons, so the report counts failures by reason.

**Triggers** (§4.3.1):

* :func:`schedule_build_on_serve` (``hints.maps.build_on_serve``): a daemon
  thread in a fresh context, started after the serve's response is built; one
  build per item in flight, de-duplicated across concurrent serves; it never
  raises into, waits on or changes the serve. A revision whose build was not
  stored is not retried on serve (the owner's CLI retries it, from its
  checkpoints).
* :func:`build_map_inline`: H2's synchronous entry when a hint finds no map
  (waits for a build in flight, then builds; built and tested, wired to no RPC).
* :func:`merge_learner_routes`: lazy; the learner's correct answers newer than
  the map either gain a matching route's attempt id or open a route with
  origin ``learner:<attempt ids>``; a new version row.
* :func:`backfill`: ``learnloop hints maps build``; ``dry_run`` opens nothing
  writable, retrieves nothing, calls nothing and prints the estimate.

**Revision keys.** A map is current for an item when it was built for the
item's ``practice_item_hash`` and ``structure_hash`` (the trace contract, PF
skeletons, authored hints and the resolved rubric); ``seeds_hash`` (every
seed, the learner's attempts and source passages included) keys the row, so a
revised item or changed seeds is a new row with ``supersedes_id``, never an
update.

**One builder per item across processes** (Codex review F3). The in-process
lock serializes a process's threads; a durable claim on the shared
``judgment_work_claims`` machinery (key ``approach_map_build:<item id>``, a
lease renewed by a heartbeat while the build or merge runs, released when it
ends, expiring if its process dies) keeps a sidecar, a CLI backfill and a
second sidecar from paying for the same item at once. The commit is fenced:
it lands only while this worker's lease holds, a build only when no map of
the revision was stored meanwhile, and a merge only onto the base map it
read (a stale merge is not stored: its attempts stay unmined and the next
merge takes them).

**Liveness** (fix round 2, M3). The lease is checked for expiry as well as
owner and epoch, a lapsed lease is never renewed, and the heartbeat signals a
lost lease to the builder. Before every paid request (the re-ask and a
provider retry included) and every ``judgment_ledger`` write the builder
checks it still holds a live lease; once it does not, it stops and answers
``stale`` without paying for anything more. The final transaction re-checks
owner, epoch and expiry inside BEGIN IMMEDIATE.

**Lifecycle** (fix round 2, M4). Builds on serve belong to a
:class:`BackgroundBuilds` registry the sidecar owns, bound to the loaded vault
with a generation token. A vault switch, ``shutdown`` and EOF stop admitting
builds, cancel the ones running and join them for a bounded few seconds.
Provider calls cannot be interrupted, so their results are fenced instead:
every late write of a build (receipts, checkpoints, judgments, the map row,
the claim's renewal and release) goes through the generation token and the
lease, so a worker of vault A never writes after the switch. The daily spend
ledger's settlement is the one deliberate exception: money already spent is
always settled against the cap.

``hints.maps.enabled = false`` builds nothing and :func:`current_map` reads
nothing. Maps are help, never evidence, and never reach the grader.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import closing, contextmanager
import contextvars
from dataclasses import asdict, dataclass, field
import json
import logging
import os
from pathlib import Path
import sqlite3
import threading
import time
from typing import Any

from pydantic import BaseModel

from learnloop.ai.errors import AIInterrupted, AIInvalidOutput, AIProviderUnavailable
from learnloop.ai.execution import content_key
from learnloop.ai.spend import SpendBudget, SpendCaps, SpendLimitExceeded, spend_envelopes
from learnloop.ai.transport import render_structured_prompt
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import approach_maps as store
from learnloop.db.stores.judgment_claims import CLAIMED, claim_work, holds_claim, release_claim, renew_claim
from learnloop.db.stores.model_calls import delete_checkpoint, finish_receipt, insert_checkpoint
from learnloop.db.stores.judgments import append_judgment
from learnloop.hints.map_seeds import (
    MAX_ATTEMPTS,
    MAX_SPANS,
    SPAN_CHARS,
    MapSeeds,
    SeedAttempt,
    SeedSpan,
    assemble_seeds,
    item_revision,
    qualifying_attempts,
)
from learnloop.hints.map_seeds import item_side
from learnloop.hints.maps import (
    ApproachMapV1,
    LearnerRouteMergeV1,
    MapContext,
    Validation,
    apply_merge,
    route_counts,
    validate_map,
)
from learnloop.ids import new_ulid
from learnloop.practice_index.paid import PaidCalls, PaidRoute, estimated_call_tokens, plan_route, resolve_client
from learnloop.source_retrieval.service_spend import SharedDailyEnvelope, daily_accounting, midnight
from learnloop.vault.models import LoadedVault, PracticeItem

LOG = logging.getLogger(__name__)

PROMPT_VERSION = "approach_map.v1"
MERGE_PROMPT_VERSION = "approach_map_merge.v1"
ROUTE_TASK = "approach_map"
PURPOSE = "approach_map"
MERGE_PURPOSE = "approach_map_merge"
#: The receipts' owner kind, and the kind the daily cap counts.
OWNER_KIND = "approach_map"
ENVELOPE = "hints.maps.max_daily_cost_usd"
LEDGER_TASK = "approach_map_valid"
#: ``LEARNLOOP_APPROACH_MAP_BUILDS=off``: a serve never starts a build that
#: would resolve a real client (the test suite sets it, as it sets
#: ``LEARNLOOP_ROUTER_MODELS=off``; a sidecar run on a vault copy may too).
BUILDS_ENV = "LEARNLOOP_APPROACH_MAP_BUILDS"
TRIGGERS = ("serve", "inline", "cli", "merge")
#: One build's paid-call bounds: the first ask, the re-ask, and a truncation
#: or provider retry of each (runaway-loop bounds, not money: money is the
#: daily envelope).
_CAPS = dict(max_candidates=0, max_pairs=0, max_retries=2, max_calls=4, max_total_tokens=400_000)


@dataclass
class MapOutcome:
    """What one build or merge did. ``status``: built | merged | current |
    up_to_date | not_stored | failed_before | disabled | not_found | no_map |
    busy | stale | capped | unpriced | unavailable | failed | planned."""

    status: str
    practice_item_id: str
    map_id: str | None = None
    version: int | None = None
    trigger: str | None = None
    reasons: list[str] = field(default_factory=list)
    reason: str | None = None
    rounds: int = 0
    model: str | None = None
    billing: str | None = None
    verified_goal: bool | None = None
    routes: dict[str, int] = field(default_factory=dict)
    usage: dict[str, Any] = field(default_factory=dict)
    estimate: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value not in (None, [], {})}


def maps_enabled(config: Any) -> bool:
    return bool(config.hints.maps.enabled)


# ---------------------------------------------------------------------------
# Spend
# ---------------------------------------------------------------------------

def maps_envelope(vault: LoadedVault, repository: Repository, *, clock: Clock | None = None) -> SharedDailyEnvelope:
    """``hints.maps.max_daily_cost_usd`` as a durable, atomic daily cap in the
    vault's spend ledger (``source_service_spend``) under its own envelope:
    each metered map request reserves its estimate in one BEGIN IMMEDIATE
    transaction checking today's total plus the estimate against the cap.
    Today's total is the map receipts (owner kind ``approach_map``) priced at
    ``hints.price_per_million`` plus the reservations in flight; subscription
    receipts are ``estimated_only`` and count nothing."""

    return SharedDailyEnvelope(
        vault, repository, day=midnight(clock), cap=float(vault.config.hints.maps.max_daily_cost_usd),
        clock=clock, name=ENVELOPE, owner_kinds=(OWNER_KIND,),
        price_per_million=vault.config.hints.price_per_million)


def maps_spend_today(vault: LoadedVault, connection: sqlite3.Connection, *, clock: Clock | None = None) -> dict[str, Any]:
    """Today's map spend as the cap counts it, with the cap and what remains."""

    accounting = daily_accounting(connection, vault, midnight(clock), envelope=ENVELOPE, now=utc_now_iso(clock),
                                  owner_kinds=(OWNER_KIND,), price_per_million=vault.config.hints.price_per_million)
    cap = float(vault.config.hints.maps.max_daily_cost_usd)
    return {
        "envelope": ENVELOPE, "day": accounting["day"], "cap_usd": cap, "metered_usd": float(accounting["usd"]),
        "remaining_usd": max(0.0, cap - float(accounting["usd"])), "requests": accounting["requests"],
        "estimated_only": dict(accounting["estimated_only"]), "price_per_million": vault.config.hints.price_per_million,
        "basis": ("metered dollars from the map receipts and reservations; Codex and the ChatGPT plan are "
                  "estimated_only and never counted against the cap"),
    }


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------

def _active_item(vault: LoadedVault, item_id: str) -> PracticeItem | None:
    item = vault.practice_items.get(item_id)
    return item if item is not None and item.status == "active" else None


def current_map(vault: LoadedVault, repository: Repository, practice_item_id: str) -> dict[str, Any] | None:
    """The item's map for its current revision, or None. The one reader the
    hint writer (H2) and the workbench (RW2b) call: None with
    ``hints.maps.enabled`` off (nothing reads maps)."""

    if not maps_enabled(vault.config):
        return None
    item = vault.practice_items.get(practice_item_id)
    if item is None:
        return None
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        item_hash, structure = item_revision(vault, connection, item)
        return store.current_map(connection, item.id, practice_item_hash=item_hash, structure_hash=structure)


def _revision_key(item_hash: str, structure: str) -> str:
    return f"{item_hash}:{structure}"


def _failed_before(connection: sqlite3.Connection, item_id: str, right_kind: str, right_id: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM judgment_ledger WHERE task = ? AND left_kind = 'practice_item' AND left_id = ? "
        "AND right_kind = ? AND right_id = ? AND verdict = 'invalid_not_stored' LIMIT 1",
        (LEDGER_TASK, item_id, right_kind, right_id),
    ).fetchone() is not None


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_INSTRUCTIONS = (
    "Build an approach map for one practice question: a small graph of the subgoals a solver passes "
    "through, with every genuinely distinct route from the givens to the goal. It is never shown whole and "
    "never graded against; later hints name one node at a time. Nodes: one or more with role 'given' (what "
    "the question states), 'step' nodes (intermediate subgoals: what is established there) and exactly one "
    "'goal' node (what the question asks for); a handful of nodes per route. label: a short structural "
    "subgoal label with no values and no expression from any later state (e.g. 'Find the CDF on the "
    "support'). state: what is true at the node (LaTeX allowed). recognizers: what in a learner's work shows "
    "the node is reached. checkpoint_id: the id of the trace-contract checkpoint or skeleton checkpoint the "
    "node matches, else ''. leak: true when the state contains or gives away the expected answer. value: on a "
    "given or step node, the bare expression its state establishes (e.g. 'x^2'), else ''. conclusion: on the "
    "goal node, the final answer as a bare expression with no prose, no variable name, no '=' and no units "
    "(e.g. '1/4', not 'P = 1/4' or '4 m'), or '' for a proof; '' on every other node. unit: the unit of the "
    "value or conclusion (e.g. 'm'), else ''. Edges: "
    "from_node, to_node, technique (a short name), principle, and facet_ids taken only from allowed_facet_ids "
    "(or none). Routes: id, name, path (node ids from a given to the goal, each consecutive pair an edge), "
    "origin and learner_attempt_ids. origin is 'reference' for the reference solution's route (always "
    "present); 'trace_contract:<recipe id>' for a recipe whose route differs; 'skeleton' for the solution "
    "skeleton's route; 'source:<worked example refs>' for a worked example whose route differs; "
    "'learner:<solution refs>' for a route of the learner's own solutions the others lack; 'model' for "
    "another distinct route a capable student would take. Record only genuinely distinct routes and share "
    "nodes between them. learner_attempt_ids: the learner solution refs that took the route. goal_node_id: "
    "the goal node. goal_answer: the final value or expression the goal establishes, exactly as the reference "
    "solution states it, or '' for a proof (the goal node's conclusion is that answer as a bare expression). "
    "A family_template, when given, is the map of an isomorphic "
    "sibling question: keep its structure and write this question's own states, values and leak marks."
)

_MERGE_INSTRUCTIONS = (
    "An approach map of a practice question is given with the learner's new correct solutions. For each "
    "solution, either name the existing route it follows (matches: attempt_ref and route_id), or, when no "
    "existing route matches it, add a new route (new_routes: id, name, attempt_refs, the nodes new to the map "
    "with fresh ids, the edges it needs, and its path from a given to the goal, reusing existing nodes where "
    "the solution passes through them). Place every solution exactly once. Follow the map's own rules: "
    "structural labels with no values, states, recognizers, checkpoint_id or '', leak marks, value (the bare "
    "expression a new node's state establishes, else ''), conclusion '' and unit, facet_ids only from "
    "allowed_facet_ids."
)


def _clip(text: str, limit: int) -> str:
    value = str(text or "")
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _expected_text(expected: Any) -> str:
    return expected if isinstance(expected, str) else json.dumps(expected, sort_keys=True, ensure_ascii=False)


def build_prompt(seeds: MapSeeds, *, feedback: Mapping[str, Any] | None = None) -> str:
    item = seeds.item
    context: dict[str, Any] = {
        "question": item.prompt,
        "reference_solution": _expected_text(item.expected_answer),
        "rubric": seeds.rubric,
        "authored_hints": seeds.authored_hints,
        "allowed_facet_ids": seeds.facet_ids,
        "learning_object": seeds.learning_object_title or item.learning_object_id,
    }
    if item.required_method is not None:
        context["required_method"] = item.required_method.model_dump(mode="json")
    if seeds.trace_contract is not None:
        context["trace_contract"] = seeds.trace_contract
    if seeds.skeletons:
        context["solution_skeletons"] = [
            {key: skeleton.get(key) for key in ("techniques", "operations", "checkpoints", "skeleton_text")}
            for skeleton in seeds.skeletons]
    if seeds.spans:
        context["worked_examples"] = [{"ref": span.ref, "source": span.source_title, "text": span.text}
                                      for span in seeds.spans]
    if seeds.attempts:
        context["learner_solutions"] = [{"ref": attempt.ref, "answer": attempt.answer_md} for attempt in seeds.attempts]
    if seeds.template is not None:
        context["family_template"] = seeds.template.get("map")
    if feedback:
        context["previous_answer_problems"] = dict(feedback)
    return render_structured_prompt("Approach map", PROMPT_VERSION,
                                    {"instructions": _INSTRUCTIONS, "context": context})


def merge_prompt(item: PracticeItem, current: Mapping[str, Any], attempts: Sequence[SeedAttempt],
                 facet_ids: Sequence[str], *, feedback: Mapping[str, Any] | None = None) -> str:
    context: dict[str, Any] = {
        "question": item.prompt,
        "approach_map": current,
        "new_learner_solutions": [{"ref": attempt.ref, "answer": attempt.answer_md} for attempt in attempts],
        "allowed_facet_ids": list(facet_ids),
    }
    if feedback:
        context["previous_answer_problems"] = dict(feedback)
    return render_structured_prompt("Approach map learner routes", MERGE_PROMPT_VERSION,
                                    {"instructions": _MERGE_INSTRUCTIONS, "context": context})


def map_context(vault: LoadedVault, seeds: MapSeeds) -> MapContext:
    return MapContext(
        expected_answer=seeds.item.expected_answer, facet_ids=frozenset(seeds.facet_ids),
        canonical_facet=vault.canonical_facet_id, checkpoint_ids=seeds.checkpoint_ids,
        recipe_ids=seeds.recipe_ids, span_refs=seeds.span_refs(), attempt_refs=seeds.attempt_refs(),
        public_text=seeds.item.prompt)


# ---------------------------------------------------------------------------
# Paid calls
# ---------------------------------------------------------------------------

def _route_client(vault: LoadedVault, route: PaidRoute) -> tuple[Any | None, str | None]:
    """The route's pinned client (patched by tests; never a silent fallback)."""

    return resolve_client(vault, route)


class _Unpriced(Exception):
    pass


@dataclass
class _Caller:
    vault: LoadedVault
    repository: Repository
    item: PracticeItem
    trigger: str
    client: Any | None
    clock: Clock | None
    deadline: float | None
    #: The build's claim: its liveness fences every paid request and every
    #: receipt and checkpoint write (fix round 2, M3/M4).
    claim: "_Claim | None" = None
    route: PaidRoute = field(init=False)
    calls: PaidCalls | None = field(init=False, default=None)
    resolved: Any | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        self.route = plan_route(self.vault, ROUTE_TASK, self.client)  # type: ignore[arg-type]

    def open(self) -> str | None:
        """Resolve the client and the budget; a reason when no call can be made."""

        if self.client is not None:
            self.resolved = self.client
        else:
            self.resolved, problem = _route_client(self.vault, self.route)
            if self.resolved is None:
                return problem or "no client"
        subscription = self.route.billing == "subscription"
        price = self.vault.config.hints.price_per_million
        if not subscription and price is None:
            raise _Unpriced("a metered approach_map route needs hints.price_per_million")
        if not subscription and maps_envelope(self.vault, self.repository, clock=self.clock).remaining() <= 0:
            # A spent day refuses before anything is retrieved or asked.
            raise SpendLimitExceeded(f"{ENVELOPE}: today's metered map budget is spent")
        budget = SpendBudget(SpendCaps(max_estimated_usd=None, **_CAPS), subscription=subscription)
        claim = self.claim
        writes: Any = self.repository if claim is None else _FencedRepository(self.repository, claim)

        def admit(_estimate: Any) -> None:
            # Before every physical request, its retries included.
            if claim is not None:
                _require_live(self.repository, claim)

        self.calls = PaidCalls(route=self.route, budget=budget, price_per_million=price, repository=writes,
                               owner_kind=OWNER_KIND, owner_id=self.item.id, admit=admit)
        return None

    def ask(self, *, purpose: str, prompt: str, result_model: type[BaseModel], metadata: Mapping[str, Any]) -> Any:
        assert self.calls is not None
        envelope = maps_envelope(self.vault, self.repository, clock=self.clock)
        with spend_envelopes(envelope):
            return self.calls.call(self.resolved, purpose=purpose, prompt=prompt, result_model=result_model,
                                   output_tokens=self.route.output_tokens, metadata=metadata,
                                   deadline=self.deadline)

    @property
    def model(self) -> str | None:
        if self.calls is not None and self.calls.last_resolved_model:
            return self.calls.last_resolved_model
        return getattr(self.resolved, "model", None) or self.route.model

    def usage(self) -> dict[str, Any]:
        return {} if self.calls is None else self.calls.report()


def _ledger(repository: Repository, *, item_id: str, right_kind: str, right_id: str, prompt: str, verdict: str,
            validation: Validation | None, extra_reasons: Sequence[str] = (), round_: int, trigger: str,
            clock: Clock | None, prompt_version: str = PROMPT_VERSION, claim: "_Claim | None" = None) -> None:
    reasons = list(dict.fromkeys([*extra_reasons, *(validation.reasons if validation else [])]))
    rationale = {"round": round_, "trigger": trigger, "reasons": reasons,
                 "details": (validation.details if validation else [])[:20],
                 "verified_goal": validation.verified_goal if validation else None}
    # Fenced like the map row (fix rounds 2 and 3): no verdict lands once the
    # lease or the vault is lost; the check runs inside the transaction.
    with _fenced_txn(repository, claim) as connection:
        append_judgment(connection, task=LEDGER_TASK, left_kind="practice_item", left_id=item_id,
                        right_kind=right_kind, right_id=right_id, judge="verifier",
                        input_hash=content_key(prompt), verdict=verdict, prompt_version=prompt_version,
                        rationale=json.dumps(rationale, sort_keys=True, default=str),
                        created_at=utc_now_iso(clock))


@dataclass(frozen=True)
class _Stored:
    """What :func:`_store` did: ``stored`` (a new row), ``current`` (a build
    found its revision's map stored by another builder first) or ``stale``
    (the claim was lost, or a merge's base is no longer the newest row)."""

    status: str
    map_id: str | None = None
    version: int | None = None


def _store(repository: Repository, *, item: PracticeItem, item_hash: str, structure: str, seeds_hash: str,
           seeds_record: Mapping[str, Any], validated: ApproachMapV1, validation: Validation, trigger: str,
           model: str | None, prompt_version: str, prompt: str, clock: Clock | None,
           claim: "_Claim | None", base_map_id: str | None = None, vault: LoadedVault | None = None) -> _Stored:
    """Insert the new version, fenced in the same BEGIN IMMEDIATE transaction
    (Codex review F3): only while ``claim`` is this worker's lease, unexpired
    (owner, epoch and expiry; fix round 2, M3) and its vault still loaded
    (M4); a build (``base_map_id`` None) only when no map of its revision
    exists yet (another process's seeds may differ, so the UNIQUE seeds key
    alone would let both land); a merge only when ``base_map_id`` is still
    the newest row of ITS revision and that revision is still the item's
    active one (M5: a revert to an earlier revision can merge again), so a
    slower merge never supersedes a newer map with stale content. A merge
    supersedes its base."""

    map_id = "am_" + new_ulid()
    merge = base_map_id is not None
    try:
        with _fenced_txn(repository, claim) as connection:
            version, supersedes = store.next_version(connection, item.id)
            if merge:
                newest = store.current_map(connection, item.id, practice_item_hash=item_hash,
                                           structure_hash=structure)
                if newest is None or newest["id"] != base_map_id:
                    return _Stored("stale")
                if vault is not None and tuple(item_revision(vault, connection, item)) != (item_hash, structure):
                    return _Stored("stale")
                supersedes = base_map_id
            if not merge:
                existing = store.current_map(connection, item.id, practice_item_hash=item_hash,
                                             structure_hash=structure)
                if existing is not None:
                    return _Stored("current", existing["id"], existing["version"])
            store.insert_map(connection, {
                "id": map_id, "practice_item_id": item.id, "practice_item_hash": item_hash,
                "family_id": item.family_id, "version": version,
                "map_json": validated.model_dump_json(),
                "seeds_json": json.dumps(dict(seeds_record), sort_keys=True, default=str),
                "seeds_hash": seeds_hash, "structure_hash": structure,
                "validation_json": json.dumps(validation.as_dict(), sort_keys=True, default=str),
                "verified_goal": int(validation.verified_goal), "trigger": trigger, "model": model,
                "prompt_version": prompt_version, "input_hash": content_key(prompt),
                "created_at": utc_now_iso(clock), "supersedes_id": supersedes,
            })
    except _LeaseLost:
        return _Stored("stale")
    except sqlite3.IntegrityError:
        return _Stored("stale" if merge else "current")
    return _Stored("stored", map_id, version)


# ---------------------------------------------------------------------------
# Builds
# ---------------------------------------------------------------------------

_LOCKS: dict[tuple[str, str], threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()


def _item_lock(sqlite_path: Any, item_id: str) -> threading.Lock:
    key = (str(Path(sqlite_path)), item_id)
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(key, threading.Lock())


# -- the durable claim (Codex review F3) ------------------------------------------------

#: This process's token, in the owner of every map claim it takes.
PROCESS_TOKEN = "proc_" + new_ulid()
CLAIM_TASK = "approach_map_build"
#: Process-liveness bounds, not judgments: a live builder renews its lease
#: every heartbeat; a dead one's lease lapses and the next builder takes it.
CLAIM_LEASE_SECONDS = 120
CLAIM_HEARTBEAT_SECONDS = 30
_CLAIM_POLL_SECONDS = 0.1


@dataclass(frozen=True)
class _Claim:
    key: str
    owner: str
    epoch: int
    #: Set by the heartbeat when the lease is lost (fix round 2, M3).
    lost: threading.Event = field(default_factory=threading.Event, compare=False, repr=False)
    #: The background build's ticket (M4); None for inline, CLI and merge work.
    fence: "BuildFence | None" = field(default=None, compare=False, repr=False)


class _LeaseLost(Exception):
    """The build's lease or vault is gone: stop without paying or writing more."""


def _holds(connection: sqlite3.Connection, claim: _Claim) -> bool:
    """Owner, epoch and expiry (fix round 2, M3), and the heartbeat's own signal."""

    if claim.lost.is_set() or (claim.fence is not None and not claim.fence.live()):
        return False
    return holds_claim(connection, claim_key=claim.key, owner=claim.owner, epoch=claim.epoch, now=_lease_now())


def _alive(repository: Repository, claim: _Claim) -> bool:
    if claim.lost.is_set() or (claim.fence is not None and not claim.fence.live()):
        return False
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return _holds(connection, claim)


def _require_live(repository: Repository, claim: _Claim) -> None:
    if not _alive(repository, claim):
        raise _LeaseLost("the build's lease or vault was lost; nothing more is paid for")


@contextmanager
def _fenced_txn(repository: Repository, claim: _Claim | None, *, fence: "BuildFence | None" = None,
                lease: bool = True) -> Iterator[sqlite3.Connection]:
    """One fenced write transaction (fix rounds 3 and 4). BEGIN IMMEDIATE is
    acquired first. Inside it the lease (owner, epoch, expiry) is re-checked,
    then the registry's small generation lock is taken just long enough to
    check the generation and register this writer as committing; the commit
    follows outside that lock, and the writer deregisters after it.

    The linearisation point is the registration: a writer that registered
    before a close's generation bump is a pre-close write to its own vault
    (it may finish committing after close returns); a writer that checks
    after the bump rolls back (``_LeaseLost``), however long busy_timeout
    kept it waiting. Nothing here ever makes close wait past its bound
    (U2). ``lease=False``: the generation only (taking a new claim, renewing)."""

    fence = fence if fence is not None else (claim.fence if claim is not None else None)
    registered = False
    try:
        with repository.atomic():
            connection = repository.connection()
            # The lease cannot change under this write lock (BEGIN IMMEDIATE),
            # so checking it before the generation is the same linearisation.
            if claim is not None and lease and not _holds(connection, claim):
                raise _LeaseLost("the build's lease was lost before this write committed")
            if fence is not None:
                if not fence.enter_commit():
                    raise _LeaseLost("the build's vault was closed before this write committed")
                registered = True
            yield connection
    finally:
        if registered:
            fence.leave_commit()


class _FencedRepository:
    """The repository a build's paid calls write through: receipts and
    checkpoints are written in a :func:`_fenced_txn`, so they commit only
    while the build's lease and vault hold (fix rounds 2 and 3). A start
    that is fenced out raises (the request is never sent); a fenced finish
    or checkpoint is dropped and logged with the call's id and usage. The
    spend ledger still settles the money (the envelope writes it, not here)."""

    def __init__(self, repository: Repository, claim: _Claim) -> None:
        self._repository = repository
        self._claim = claim

    def __getattr__(self, name: str) -> Any:
        return getattr(self._repository, name)

    def _dropped(self, what: str, detail: Mapping[str, Any]) -> None:
        LOG.warning("approach map %s not written: the build's lease or vault was lost (%s)", what,
                    json.dumps(dict(detail), sort_keys=True, default=str))

    def record_model_event(self, action: str, event: dict[str, Any], *, owner_kind: str, owner_id: str) -> None:
        detail = {"id": event.get("id"), **{key: event.get(key) for key in
                                            ("input_tokens", "output_tokens", "cost", "resolved_model")}}
        if action == "start":
            # On the transaction's pinned connection; fenced out, it raises and nothing is sent.
            with _fenced_txn(self._repository, self._claim):
                self._repository.record_model_event(action, event, owner_kind=owner_kind, owner_id=owner_id)
            return
        try:
            with _fenced_txn(self._repository, self._claim) as connection:
                if action == "finish":
                    finish_receipt(connection, event, owner_kind=owner_kind, owner_id=owner_id)
                else:
                    raise ValueError(f"Unknown model receipt action: {action}")
        except _LeaseLost:
            self._dropped(f"receipt ({action})", detail)

    def save_model_checkpoint(self, cache_key: str, *, purpose: str, result: dict[str, Any],
                              usage: dict[str, Any] | None = None) -> None:
        try:
            with _fenced_txn(self._repository, self._claim) as connection:
                insert_checkpoint(connection, cache_key, purpose=purpose, result=result, usage=usage)
        except _LeaseLost:
            self._dropped("checkpoint", {"key": cache_key})

    def discard_model_checkpoint(self, cache_key: str) -> None:
        try:
            with _fenced_txn(self._repository, self._claim) as connection:
                delete_checkpoint(connection, cache_key)
        except _LeaseLost:
            self._dropped("checkpoint discard", {"key": cache_key})


def _lease_now() -> str:
    """Wall-clock time for leases: process liveness, never the vault's clock."""

    return utc_now_iso()


def claim_key(practice_item_id: str) -> str:
    return f"{CLAIM_TASK}:{practice_item_id}"


def _try_claim(repository: Repository, item_id: str, fence: "BuildFence | None" = None) -> _Claim | None:
    owner = f"{PROCESS_TOKEN}:{new_ulid()}"
    try:
        with _fenced_txn(repository, None, fence=fence, lease=False) as connection:
            status, epoch = claim_work(
                connection, claim_key=claim_key(item_id), task=CLAIM_TASK, producer=OWNER_KIND,
                prompt_version=None, input_hash="", owner=owner, now=_lease_now(), lease_seconds=CLAIM_LEASE_SECONDS)
    except _LeaseLost:
        return None
    if status == CLAIMED and epoch is not None:
        return _Claim(claim_key(item_id), owner, int(epoch), fence=fence)
    return None


def _claim(repository: Repository, item_id: str, until: float | None,
           fence: "BuildFence | None" = None) -> _Claim | None:
    """Claim the item's builds across processes, waiting until ``until``
    (``time.monotonic()``; None: until claimed; a dead holder's lease lapses
    within ``CLAIM_LEASE_SECONDS``). None: another process holds it."""

    while True:
        if fence is not None and not fence.live():
            return None
        claim = _try_claim(repository, item_id, fence)
        if claim is not None:
            return claim
        if until is not None and time.monotonic() >= until:
            return None
        time.sleep(_CLAIM_POLL_SECONDS if until is None else max(0.0, min(_CLAIM_POLL_SECONDS,
                                                                            until - time.monotonic())))


def _release(repository: Repository, claim: _Claim) -> None:
    try:
        # Lease-checked like every late write (fix round 4, U3): a lost or
        # expired lease is never mutated to released, and a closed vault's
        # claim lapses on its own.
        with _fenced_txn(repository, claim) as connection:
            release_claim(connection, claim_key=claim.key, owner=claim.owner, epoch=claim.epoch, now=_lease_now())
    except _LeaseLost:
        return
    except Exception:  # noqa: BLE001 - an unreleased claim simply expires
        LOG.warning("approach map claim release failed", exc_info=True)


@contextmanager
def _claimed(repository: Repository, item_id: str, until: float | None, *,
             fence: "BuildFence | None" = None) -> Iterator[_Claim | None]:
    """Hold the item's durable claim for the block, renewing its lease while
    the block runs; yields None (and holds nothing) when another process has
    it. The heartbeat sets ``claim.lost`` once the lease cannot be renewed
    (taken over, expired or its vault switched away; fix round 2, M3)."""

    claim = _claim(repository, item_id, until, fence)
    if claim is None:
        yield None
        return
    stop = threading.Event()

    def beat() -> None:
        while not stop.wait(CLAIM_HEARTBEAT_SECONDS):
            try:
                with _fenced_txn(repository, claim, lease=False) as connection:
                    held = not claim.lost.is_set() and renew_claim(
                        connection, claim_key=claim.key, owner=claim.owner, epoch=claim.epoch,
                        now=_lease_now(), lease_seconds=CLAIM_LEASE_SECONDS)
            except _LeaseLost:
                held = False
            except Exception:  # noqa: BLE001 - the next beat retries; a lapsed lease fails the liveness check
                continue
            if not held:
                claim.lost.set()
                return

    thread = threading.Thread(target=beat, name=f"learnloop-approach-map-claim-{item_id}", daemon=True)
    thread.start()
    try:
        yield claim
    finally:
        stop.set()
        thread.join(5)
        _release(repository, claim)


def _two_rounds(caller: _Caller, *, purpose: str, first_prompt: str, reprompt: Callable[[Mapping[str, Any]], str],
                result_model: type[BaseModel], check: Callable[[Any], tuple[Validation, list[str]]],
                ledger: Callable[..., None], metadata: Mapping[str, Any]) -> tuple[Validation | None, str, int, list[str]]:
    """Ask, validate, re-ask once with the reasons, validate; never a third
    time. No ask once the build's lease or vault is lost (fix round 2, M3)."""

    prompt = first_prompt
    reasons: list[str] = []
    for round_ in (1, 2):
        if caller.claim is not None:
            _require_live(caller.repository, caller.claim)
        answer = caller.ask(purpose=purpose, prompt=prompt, result_model=result_model,
                            metadata={**metadata, "round": round_})
        validation, extra = check(answer)
        reasons = list(dict.fromkeys([*extra, *validation.reasons]))
        if not reasons:
            ledger(prompt=prompt, verdict="valid", validation=validation, extra_reasons=(), round_=round_)
            return validation, prompt, round_, []
        final = round_ == 2
        ledger(prompt=prompt, verdict="invalid_not_stored" if final else "invalid_reasked", validation=validation,
               extra_reasons=extra, round_=round_)
        if final:
            return None, prompt, round_, reasons
        previous = answer.model_dump(mode="json") if isinstance(answer, BaseModel) else answer
        prompt = reprompt({"reasons": reasons, "details": (validation.details or [])[:20], "previous_answer": previous})
    return None, prompt, 2, reasons  # pragma: no cover - the loop always returns


def _paid(outcome: MapOutcome, caller: _Caller, body: Callable[[], MapOutcome]) -> MapOutcome:
    """Run ``body`` with the paid-call failures mapped to an outcome."""

    outcome.billing = caller.route.billing
    try:
        try:
            problem = caller.open()
        except _Unpriced as exc:
            outcome.status, outcome.reason = "unpriced", str(exc)
            return outcome
        if problem is not None:
            outcome.status, outcome.reason = "unavailable", problem
            return outcome
        return body()
    except _LeaseLost as exc:
        outcome.status, outcome.reason = "stale", f"{exc}; nothing more was paid for or stored"
    except SpendLimitExceeded as exc:
        outcome.status, outcome.reason = "capped", str(exc)
    except AIInterrupted:
        raise
    except (AIProviderUnavailable, AIInvalidOutput) as exc:
        outcome.status, outcome.reason = "failed", f"{type(exc).__name__}: {exc}"[:300]
    finally:
        outcome.usage = caller.usage()
        outcome.model = outcome.model or caller.model
    return outcome


def build_map(vault: LoadedVault, repository: Repository, practice_item_id: str, *, trigger: str,
              client: Any | None = None, clock: Clock | None = None, deadline: float | None = None,
              wait_seconds: float | None = 0.0, find: Callable[..., Any] | None = None,
              fence: "BuildFence | None" = None) -> MapOutcome:
    """Build and store the item's map unless its current revision has one.

    ``wait_seconds``: how long to wait for a build of the same item already in
    flight in this process (0: do not wait, answer ``busy``; None: wait).
    ``fence``: a background build's ticket (its registry's vault generation)."""

    if trigger not in TRIGGERS or trigger == "merge":
        raise ValueError(f"trigger must be one of serve, inline, cli; got {trigger!r}")
    outcome = MapOutcome(status="disabled", practice_item_id=practice_item_id, trigger=trigger)
    if not maps_enabled(vault.config):
        return outcome
    item = _active_item(vault, practice_item_id)
    if item is None:
        outcome.status = "not_found"
        return outcome
    until = None if wait_seconds is None else time.monotonic() + max(0.0, wait_seconds)
    lock = _item_lock(repository.sqlite_path, item.id)
    acquired = lock.acquire(timeout=wait_seconds) if wait_seconds else lock.acquire(blocking=wait_seconds is None)
    if not acquired:
        outcome.status = "busy"
        return outcome
    try:
        if _settled_build(vault, repository, item, outcome):
            return outcome
        # Another process may be building the item: claim it durably first,
        # then read again (it may have stored the map while this one waited).
        if fence is not None and not fence.live():
            outcome.status, outcome.reason = "stale", "the vault was closed before the build started"
            return outcome
        with _claimed(repository, item.id, until, fence=fence) as claim:
            if claim is None:
                if fence is not None and not fence.live():
                    outcome.status, outcome.reason = "stale", "the vault was closed before the build started"
                    return outcome
                outcome.status = "busy"
                outcome.reason = "another process is building or merging this item's map"
                return outcome
            if _settled_build(vault, repository, item, outcome):
                return outcome
            return _build_claimed(vault, repository, item, outcome, claim, client=client, clock=clock,
                                  deadline=deadline, find=find)
    finally:
        lock.release()


def _settled_build(vault: LoadedVault, repository: Repository, item: PracticeItem, outcome: MapOutcome) -> bool:
    """True (``outcome`` set) when no build is due: the revision has a map,
    or a serve meets a revision whose build was not stored."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        item_hash, structure = item_revision(vault, connection, item)
        existing = store.current_map(connection, item.id, practice_item_hash=item_hash, structure_hash=structure)
        failed = outcome.trigger == "serve" and _failed_before(connection, item.id, "approach_map_revision",
                                                               _revision_key(item_hash, structure))
    if existing is not None:
        outcome.status, outcome.map_id, outcome.version = "current", existing["id"], existing["version"]
        outcome.reason = None
        return True
    if failed:
        outcome.status = "failed_before"
        outcome.reason = "this revision's build was not stored; `learnloop hints maps build` retries it"
        return True
    return False


def _build_claimed(vault: LoadedVault, repository: Repository, item: PracticeItem, outcome: MapOutcome,
                   claim: _Claim, *, client: Any | None, clock: Clock | None, deadline: float | None,
                   find: Callable[..., Any] | None) -> MapOutcome:
    trigger = str(outcome.trigger)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        item_hash, structure = item_revision(vault, connection, item)
    caller = _Caller(vault, repository, item, trigger, client, clock, deadline, claim)
    right_id = _revision_key(item_hash, structure)
    metadata = {"practice_item_id": item.id, "trigger": trigger, "prompt_version": PROMPT_VERSION}

    def ledger(**kwargs: Any) -> None:
        _ledger(repository, item_id=item.id, right_kind="approach_map_revision", right_id=right_id,
                trigger=trigger, clock=clock, claim=claim, **kwargs)

    def body() -> MapOutcome:
        # Seeds are assembled only once a call can be made (no retrieval for
        # an unpriced, unavailable or capped route) and the lease still holds.
        _require_live(repository, claim)
        seeds = assemble_seeds(vault, repository, item, find=find)
        context = map_context(vault, seeds)
        validation, prompt, rounds, reasons = _two_rounds(
            caller, purpose=PURPOSE, first_prompt=build_prompt(seeds),
            reprompt=lambda feedback: build_prompt(seeds, feedback=feedback), result_model=ApproachMapV1,
            check=lambda answer: (validate_map(answer, context), []), ledger=ledger, metadata=metadata)
        outcome.rounds = rounds
        if validation is None or validation.normalized is None:
            outcome.status, outcome.reasons = "not_stored", reasons
            return outcome
        stored = _store(repository, item=item, item_hash=item_hash, structure=structure,
                        seeds_hash=seeds.seeds_hash, seeds_record=seeds.record(), validated=validation.normalized,
                        validation=validation, trigger=trigger, model=caller.model, prompt_version=PROMPT_VERSION,
                        prompt=prompt, clock=clock, claim=claim)
        if stored.status == "current":
            outcome.status, outcome.map_id, outcome.version = "current", stored.map_id, stored.version
            return outcome
        if stored.status == "stale":
            outcome.status = "stale"
            outcome.reason = "this build's lease or vault was lost before it stored; nothing was stored"
            return outcome
        outcome.status, outcome.map_id, outcome.version = "built", stored.map_id, stored.version
        outcome.verified_goal = validation.verified_goal
        outcome.routes = _route_kinds(validation.normalized)
        return outcome

    return _paid(outcome, caller, body)


def _route_kinds(value: ApproachMapV1) -> dict[str, int]:
    return route_counts(value.model_dump(mode="json"))


def build_map_inline(vault: LoadedVault, repository: Repository, practice_item_id: str, *,
                     client: Any | None = None, clock: Clock | None = None,
                     deadline: float | None = None, find: Callable[..., Any] | None = None) -> MapOutcome:
    """H2's entry when a hint finds no map (§4.3.1, row 2): build it now, in
    the same request, and store it. A build of the item already in flight (a
    serve's) is waited for until ``deadline`` (``time.monotonic()``), then
    read; nothing is built twice."""

    wait = None if deadline is None else max(0.001, deadline - time.monotonic())
    return build_map(vault, repository, practice_item_id, trigger="inline", client=client, clock=clock,
                     deadline=deadline, wait_seconds=wait, find=find)


# ---------------------------------------------------------------------------
# Build on serve
# ---------------------------------------------------------------------------

_INFLIGHT: set[tuple[str, str]] = set()
_INFLIGHT_GUARD = threading.Lock()
_THREADS: list[threading.Thread] = []
#: How long a vault switch, ``shutdown`` or EOF waits for running builds
#: (process liveness, not a judgment): a provider call cannot be interrupted,
#: so a build still waiting on one is left to finish fenced, never waited for.
DRAIN_SECONDS = 3.0


class BuildFence:
    """One background build's ticket: the registry's vault generation when it
    was admitted. It is live while that generation is the registry's own and
    the registry is open (fix round 2, M4)."""

    def __init__(self, registry: "BackgroundBuilds", generation: str) -> None:
        self._registry = registry
        self.generation = generation

    def live(self) -> bool:
        return self._registry._live(self.generation)

    def enter_commit(self) -> bool:
        """Under the registry's generation lock: still this generation? Then
        count this writer as committing (fix round 4, U2)."""

        return self._registry._enter_commit(self.generation)

    def leave_commit(self) -> None:
        self._registry._leave_commit()


class BackgroundBuilds:
    """The lifecycle of build-on-serve workers, owned by the sidecar (fix
    round 2, M4): a registry keyed to the loaded vault with a generation
    token. :meth:`bind` keys it to a vault (a different vault closes the
    previous one first); :meth:`close` stops admitting builds, cancels the
    running ones and joins them for at most ``drain_seconds``. A cancelled
    build's late writes are fenced by its generation (and its lease): a write
    that registered as committing before the switch's generation bump is a
    pre-close write to its own vault, and no write that checks after the bump
    lands. Close waits for registered commits only until its deadline (U2).
    An unbound
    registry (the module default: tests and callers without a sidecar)
    admits builds of any vault."""

    def __init__(self, *, drain_seconds: float = DRAIN_SECONDS) -> None:
        self.drain_seconds = drain_seconds
        self._lock = threading.Lock()
        #: The small lock the generation lives under (fix round 4, U2):
        #: held only to check or bump it, never across a commit.
        self._generation_lock = threading.Lock()
        self._commits_done = threading.Condition(self._generation_lock)
        self._committing = 0
        self._path: str | None = None
        self._generation = "gen_" + new_ulid()
        self._open = True
        self._threads: list[threading.Thread] = []

    @property
    def generation(self) -> str:
        return self._generation

    def _live(self, generation: str) -> bool:
        return self._open and generation == self._generation

    def _enter_commit(self, generation: str) -> bool:
        with self._generation_lock:
            if not (self._open and generation == self._generation):
                return False
            self._committing += 1
            return True

    def _leave_commit(self) -> None:
        with self._generation_lock:
            self._committing -= 1
            if self._committing <= 0:
                self._commits_done.notify_all()

    @property
    def committing(self) -> int:
        with self._generation_lock:
            return self._committing

    def bind(self, sqlite_path: Any) -> None:
        """Key the registry to the loaded vault; a different vault (or a closed
        registry) closes the previous generation (draining it only if no
        close has drained it yet) and opens a new one."""

        key = str(Path(sqlite_path))
        with self._lock:
            if self._open and self._path == key:
                return
        self.close()
        with self._lock, self._generation_lock:
            self._path, self._generation, self._open = key, "gen_" + new_ulid(), True

    def admit(self, sqlite_path: Any) -> BuildFence | None:
        with self._lock:
            if not self._open or (self._path is not None and self._path != str(Path(sqlite_path))):
                return None
            return BuildFence(self, self._generation)

    def launch(self, sqlite_path: Any, work: Callable[[BuildFence], Callable[[], None]], *,
               name: str) -> threading.Thread | None:
        """Admit, register and start one build atomically with :meth:`close`
        (fix round 3, R4): under the registry lock the build is refused once
        closed, and registered before it starts, so a close either refuses it
        or joins it. None when refused."""

        with self._lock:
            if not self._open or (self._path is not None and self._path != str(Path(sqlite_path))):
                return None
            fence = BuildFence(self, self._generation)
            thread = threading.Thread(target=contextvars.Context().run, args=(work(fence),), daemon=True, name=name)
            self._threads[:] = [existing for existing in self._threads if existing.is_alive()] + [thread]
            try:
                thread.start()
            except BaseException:
                self._threads.remove(thread)
                raise
            return thread

    def track(self, thread: threading.Thread) -> None:
        with self._lock:
            self._threads[:] = [existing for existing in self._threads if existing.is_alive()] + [thread]

    def close(self, timeout: float | None = None) -> bool:
        """Stop admitting, cancel, and join for at most ``timeout`` seconds
        (default ``drain_seconds``; never hangs). True when every build ended.

        A generation is drained once (fix round 3, R4): closing an already
        closed registry joins nothing more, so a vault switch (close, then
        bind) and shutdown (the handler, then the server's ``finally``) each
        spend one deadline."""

        bound = self.drain_seconds if timeout is None else max(0.0, timeout)
        end = time.monotonic() + bound
        with self._lock:
            already = not self._open
            self._open = False
            threads = list(self._threads)
        if already:
            with self._lock:
                self._threads[:] = [thread for thread in self._threads if thread.is_alive()]
                return not self._threads
        # The bump is the linearisation point (fix round 4, U2): no writer can
        # pass its check after it. Writers registered before it may still be
        # committing (a reader can hold a rollback-journal commit for up to
        # busy_timeout): they are waited for only until the deadline, never past it.
        with self._generation_lock:
            self._generation = "gen_" + new_ulid()
            drained = self._commits_done.wait_for(lambda: self._committing <= 0,
                                                  timeout=max(0.0, end - time.monotonic()))
            pending = self._committing
        if not drained:
            LOG.warning("approach map builds: %d pre-close commit(s) still finishing after the %.2fs close "
                        "bound; they write only to their own vault", pending, bound)
        for thread in threads:
            if thread is not threading.current_thread():
                thread.join(max(0.0, end - time.monotonic()))
        with self._lock:
            self._threads[:] = [thread for thread in self._threads if thread.is_alive()]
            return drained and not self._threads

    @property
    def running(self) -> int:
        with self._lock:
            return sum(thread.is_alive() for thread in self._threads)


_DEFAULT_BUILDS = BackgroundBuilds()


def schedule_build_on_serve(vault: LoadedVault, sqlite_path: Any, practice_item_id: str, *,
                            client: Any | None = None, clock: Clock | None = None,
                            find: Callable[..., Any] | None = None,
                            builds: BackgroundBuilds | None = None) -> threading.Thread | None:
    """Start a background build for a served item (``hints.maps.build_on_serve``).

    Called after the serve's response is built; returns at once and never
    raises. The thread runs in a fresh context (no envelope or observer of the
    serving request leaks into it), on its own connection; one build per item
    is in flight per process, so concurrent serves start one build. ``builds``
    is the sidecar's registry (fix round 2, M4): a build is admitted only for
    its loaded vault and only while it is open."""

    key: tuple[str, str] | None = None
    try:
        maps = vault.config.hints.maps
        if not (maps.enabled and maps.build_on_serve):
            return None
        if client is None and os.environ.get(BUILDS_ENV, "").strip().lower() == "off":
            return None
        if _active_item(vault, practice_item_id) is None:
            return None
        registry = builds if builds is not None else _DEFAULT_BUILDS
        candidate = (str(Path(sqlite_path)), practice_item_id)
        with _INFLIGHT_GUARD:
            if candidate in _INFLIGHT:
                return None
            _INFLIGHT.add(candidate)
            key = candidate

        def work(fence: BuildFence) -> Callable[[], None]:
            def run() -> None:
                try:
                    if not fence.live():
                        return
                    repository = Repository.attach(Path(sqlite_path))
                    outcome = build_map(vault, repository, practice_item_id, trigger="serve", client=client,
                                        clock=clock, find=find, fence=fence)
                    LOG.info("approach map on serve: %s", json.dumps(outcome.as_dict(), sort_keys=True, default=str))
                except Exception:  # noqa: BLE001 - a background build never reaches the serve
                    LOG.warning("approach map build on serve failed", exc_info=True)
                finally:
                    with _INFLIGHT_GUARD:
                        _INFLIGHT.discard(candidate)

            return run

        thread = registry.launch(sqlite_path, work, name=f"learnloop-approach-map-{practice_item_id}")
        if thread is None:
            return None  # refused: the registry is closed or bound to another vault (finally clears the mark)
        key = None  # the started thread owns the in-flight mark now
        with _INFLIGHT_GUARD:
            _THREADS[:] = [existing for existing in _THREADS if existing.is_alive()] + [thread]
        return thread
    except Exception:  # noqa: BLE001 - scheduling never fails a serve
        LOG.warning("approach map scheduling failed", exc_info=True)
        return None
    finally:
        # Any failure before the thread started leaves no in-flight mark (fix round 2, L1).
        if key is not None:
            with _INFLIGHT_GUARD:
                _INFLIGHT.discard(key)


def schedule_merge_after_hint(vault: LoadedVault, sqlite_path: Any, practice_item_id: str, *,
                              client: Any | None = None, clock: Clock | None = None,
                              builds: BackgroundBuilds | None = None) -> threading.Thread | None:
    """Start the lazy learner-route merge after a hint is shown (§4.3.1 row 3;
    H2a review F9): background, never on the request path, so it may use the
    map route's Codex. Called after delivery; returns at once and never raises.

    Its switches are the background map work's: ``hints.maps.enabled`` (the
    kill switch) and ``hints.maps.build_on_serve`` (map work in the background
    of the practice screen), and ``LEARNLOOP_APPROACH_MAP_BUILDS=off`` without
    an injected client. It runs :func:`merge_learner_routes` with H1's item
    lock, durable claim, lease, spend envelope and fence, admitted only by the
    sidecar's registry for its loaded vault; one map job per item is in flight
    per process (a build or a merge). Nothing new to merge, or no map, asks
    no model."""

    key: tuple[str, str] | None = None
    try:
        maps = vault.config.hints.maps
        if not (maps.enabled and maps.build_on_serve):
            return None
        if client is None and os.environ.get(BUILDS_ENV, "").strip().lower() == "off":
            return None
        if _active_item(vault, practice_item_id) is None:
            return None
        registry = builds if builds is not None else _DEFAULT_BUILDS
        candidate = (str(Path(sqlite_path)), practice_item_id)
        with _INFLIGHT_GUARD:
            if candidate in _INFLIGHT:
                return None
            _INFLIGHT.add(candidate)
            key = candidate

        def work(fence: BuildFence) -> Callable[[], None]:
            def run() -> None:
                try:
                    if not fence.live():
                        return
                    repository = Repository.attach(Path(sqlite_path))
                    outcome = merge_learner_routes(vault, repository, practice_item_id, client=client, clock=clock,
                                                   fence=fence)
                    LOG.info("approach map merge after a hint: %s",
                             json.dumps(outcome.as_dict(), sort_keys=True, default=str))
                except Exception:  # noqa: BLE001 - a background merge never reaches the hint
                    LOG.warning("approach map merge after a hint failed", exc_info=True)
                finally:
                    with _INFLIGHT_GUARD:
                        _INFLIGHT.discard(candidate)

            return run

        thread = registry.launch(sqlite_path, work, name=f"learnloop-approach-map-merge-{practice_item_id}")
        if thread is None:
            return None
        key = None
        with _INFLIGHT_GUARD:
            _THREADS[:] = [existing for existing in _THREADS if existing.is_alive()] + [thread]
        return thread
    except Exception:  # noqa: BLE001 - scheduling never fails a delivery
        LOG.warning("approach map merge scheduling failed", exc_info=True)
        return None
    finally:
        if key is not None:
            with _INFLIGHT_GUARD:
                _INFLIGHT.discard(key)


def wait_for_background_builds(timeout: float = 30.0) -> bool:
    """Join the background builds started so far, of every registry (tests;
    the sidecar's shutdown path closes its own registry, :meth:`BackgroundBuilds.close`)."""

    end = time.monotonic() + timeout
    with _INFLIGHT_GUARD:
        threads = list(_THREADS)
    for thread in threads:
        thread.join(max(0.0, end - time.monotonic()))
    return not any(thread.is_alive() for thread in threads)


# ---------------------------------------------------------------------------
# The learner-route merge
# ---------------------------------------------------------------------------

def _known_attempts(current: Mapping[str, Any]) -> set[str]:
    """The attempts the map has mined: those a route records (Codex review
    F4). A seeded attempt no route took is not mined, so a later merge places it."""

    known: set[str] = set()
    for route in (current.get("map") or {}).get("routes") or ():
        known.update(str(value) for value in route.get("learner_attempt_ids") or ())
    return known


def new_learner_attempts(vault: LoadedVault, repository: Repository, practice_item_id: str) -> list[SeedAttempt]:
    """The learner's correct answers in the item's family the current map has
    not seen (§4.3.1 row 3: "the map predates the learner's latest correct
    answers"), newest first, at most ``MAX_ATTEMPTS``."""

    current = current_map(vault, repository, practice_item_id)
    item = _active_item(vault, practice_item_id)
    if current is None or item is None:
        return []
    known = _known_attempts(current)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        found = qualifying_attempts(vault, connection, item, limit=10_000)
    fresh = [attempt for attempt in found if attempt.attempt_id not in known][:MAX_ATTEMPTS]
    return [SeedAttempt(ref=f"n{index}", attempt_id=attempt.attempt_id, practice_item_id=attempt.practice_item_id,
                        basis=attempt.basis, answer_md=attempt.answer_md, created_at=attempt.created_at)
            for index, attempt in enumerate(fresh, start=1)]


def merge_learner_routes(vault: LoadedVault, repository: Repository, practice_item_id: str, *,
                         client: Any | None = None, clock: Clock | None = None,
                         deadline: float | None = None, fence: "BuildFence | None" = None) -> MapOutcome:
    """Merge the learner's new correct routes into the item's map (lazy: H2
    calls it after a hint is shown on an item whose map predates them,
    :func:`schedule_merge_after_hint`). ``fence``: a background merge's
    ticket (its registry's vault generation), as a background build's."""

    outcome = MapOutcome(status="disabled", practice_item_id=practice_item_id, trigger="merge")
    if not maps_enabled(vault.config):
        return outcome
    item = _active_item(vault, practice_item_id)
    if item is None:
        outcome.status = "not_found"
        return outcome
    lock = _item_lock(repository.sqlite_path, item.id)
    acquired = lock.acquire(timeout=max(0.001, deadline - time.monotonic())) if deadline is not None else lock.acquire()
    if not acquired:
        outcome.status = "busy"
        return outcome
    try:
        if _settled_merge(vault, repository, item, outcome) is None:
            return outcome
        if fence is not None and not fence.live():
            outcome.status, outcome.reason = "stale", "the vault was closed before the merge started"
            return outcome
        with _claimed(repository, item.id, deadline, fence=fence) as claim:
            if claim is None:
                outcome.status = "busy"
                outcome.reason = "another process is building or merging this item's map"
                return outcome
            return _merge_claimed(vault, repository, item, outcome, claim, client=client, clock=clock,
                                  deadline=deadline)
    finally:
        lock.release()


def _settled_merge(vault: LoadedVault, repository: Repository, item: PracticeItem,
                   outcome: MapOutcome) -> tuple[dict[str, Any], list[SeedAttempt]] | None:
    """``(current map, new attempts)`` when a merge is due, else None with
    ``outcome`` set (no map, or nothing new)."""

    current = current_map(vault, repository, item.id)
    if current is None:
        outcome.status = "no_map"
        return None
    fresh = new_learner_attempts(vault, repository, item.id)
    if not fresh:
        outcome.status, outcome.map_id, outcome.version = "up_to_date", current["id"], current["version"]
        return None
    return current, fresh


def _merge_claimed(vault: LoadedVault, repository: Repository, item: PracticeItem, outcome: MapOutcome,
                   claim: _Claim, *, client: Any | None, clock: Clock | None, deadline: float | None) -> MapOutcome:
    # Read again under the claim: another process may have merged meanwhile.
    due = _settled_merge(vault, repository, item, outcome)
    if due is None:
        return outcome
    current, fresh = due
    right_id = f"{current['id']}:{content_key([attempt.attempt_id for attempt in fresh])[:16]}"
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if _failed_before(connection, item.id, "approach_map_merge", right_id):
            outcome.status = "failed_before"
            outcome.reason = "this merge was not stored before; it is retried when the learner's answers change"
            return outcome
    base = ApproachMapV1.model_validate(current["map"])
    seeds_record = dict(current["seeds"])
    facet_ids = sorted({vault.canonical_facet_id(str(facet)) for facet in item.evidence_facets})
    known_spans = [f"{entry.get('extraction_id')}:{entry.get('span_id')}" for entry in seeds_record.get("spans") or ()]
    known_attempts = sorted(_known_attempts(current))
    refs = {attempt.ref: attempt.attempt_id for attempt in fresh}
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        side = item_side(vault, connection, item)
    context = MapContext(
        expected_answer=item.expected_answer, facet_ids=frozenset(facet_ids), canonical_facet=vault.canonical_facet_id,
        checkpoint_ids=side.checkpoint_ids, recipe_ids=side.recipe_ids,
        span_refs={key: key for key in known_spans},
        attempt_refs={**{attempt_id: attempt_id for attempt_id in known_attempts}, **refs}, public_text=item.prompt)
    caller = _Caller(vault, repository, item, "merge", client, clock, deadline, claim)
    current_payload = current["map"]
    metadata = {"practice_item_id": item.id, "trigger": "merge", "prompt_version": MERGE_PROMPT_VERSION,
                "base_map_id": current["id"]}

    def ledger(**kwargs: Any) -> None:
        _ledger(repository, item_id=item.id, right_kind="approach_map_merge", right_id=right_id, trigger="merge",
                clock=clock, prompt_version=MERGE_PROMPT_VERSION, claim=claim, **kwargs)

    def check(answer: LearnerRouteMergeV1) -> tuple[Validation, list[str]]:
        merged, merge_reasons, merge_details = apply_merge(base, answer, attempt_refs=refs)
        validation = validate_map(merged, context)
        validation.details = [*merge_details, *validation.details]
        if merge_reasons:
            validation.normalized = None
        return validation, merge_reasons

    def body() -> MapOutcome:
        validation, prompt, rounds, reasons = _two_rounds(
            caller, purpose=MERGE_PURPOSE,
            first_prompt=merge_prompt(item, current_payload, fresh, facet_ids),
            reprompt=lambda feedback: merge_prompt(item, current_payload, fresh, facet_ids, feedback=feedback),
            result_model=LearnerRouteMergeV1, check=check, ledger=ledger, metadata=metadata)
        outcome.rounds = rounds
        if validation is None or validation.normalized is None:
            outcome.status, outcome.reasons = "not_stored", reasons
            return outcome
        fresh_ids = {attempt.attempt_id for attempt in fresh}
        seeds_record["attempts"] = [*(entry for entry in seeds_record.get("attempts") or ()
                                      if str(entry.get("id")) not in fresh_ids),
                                    *({"id": attempt.attempt_id, "practice_item_id": attempt.practice_item_id,
                                       "basis": attempt.basis} for attempt in fresh)]
        seeds_record["merged_from"] = current["id"]
        seeds_hash = content_key({"base": current["seeds_hash"],
                                  "attempts": [[attempt.attempt_id, content_key(attempt.answer_md)]
                                               for attempt in fresh]})
        stored = _store(repository, item=item, item_hash=current["practice_item_hash"],
                        structure=current["structure_hash"], seeds_hash=seeds_hash, seeds_record=seeds_record,
                        validated=validation.normalized, validation=validation, trigger="merge", model=caller.model,
                        prompt_version=MERGE_PROMPT_VERSION, prompt=prompt, clock=clock, claim=claim,
                        base_map_id=str(current["id"]), vault=vault)
        if stored.status != "stored":
            # A newer map landed (or the claim was lost): this merge's base is
            # stale. Nothing is stored; the attempts the newer map lacks stay
            # unmined, so the next merge places them on it.
            outcome.status = "stale"
            outcome.reason = "the map changed while this merge ran; nothing was stored"
            return outcome
        outcome.status, outcome.map_id, outcome.version = "merged", stored.map_id, stored.version
        outcome.verified_goal = validation.verified_goal
        outcome.routes = _route_kinds(validation.normalized)
        return outcome

    return _paid(outcome, caller, body)


# ---------------------------------------------------------------------------
# The owner's backfill
# ---------------------------------------------------------------------------

def select_items(vault: LoadedVault, *, item_id: str | None = None, family_id: str | None = None,
                 learning_object_id: str | None = None) -> list[PracticeItem]:
    """The active items one ``hints maps build`` selector names (all, without one)."""

    if sum(value is not None for value in (item_id, family_id, learning_object_id)) > 1:
        raise ValueError("give at most one of --item, --family and --lo")
    items = [item for _, item in sorted(vault.practice_items.items()) if item.status == "active"]
    if item_id is not None:
        items = [item for item in items if item.id == item_id]
        if not items:
            raise ValueError(f"no active practice item {item_id!r}")
    elif family_id is not None:
        items = [item for item in items if item.family_id == family_id]
        if not items:
            raise ValueError(f"no active practice item in family {family_id!r}")
    elif learning_object_id is not None:
        items = [item for item in items if item.learning_object_id == learning_object_id]
        if not items:
            raise ValueError(f"no active practice item for learning object {learning_object_id!r}")
    return items


def _planned_seeds(seeds: MapSeeds) -> MapSeeds:
    """The dry run's seeds: the worked examples counted at their cap."""

    seeds.spans = [SeedSpan(ref=f"s{index}", extraction_id="planned", span_id=f"s{index}", role="worked_example",
                            source_title="(a worked example, counted at its cap)", text="x" * SPAN_CHARS)
                   for index in range(1, MAX_SPANS + 1)]
    return seeds


def plan_item(vault: LoadedVault, repository: Repository, item: PracticeItem, *,
              client: Any | None = None) -> MapOutcome:
    """A dry run for one item: is a map due, and what would the call cost?
    Reads only; no retrieval, no call, no write."""

    outcome = MapOutcome(status="planned", practice_item_id=item.id, trigger="cli")
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        item_hash, structure = item_revision(vault, connection, item)
        existing = store.current_map(connection, item.id, practice_item_hash=item_hash, structure_hash=structure)
    if existing is not None:
        outcome.status, outcome.map_id, outcome.version = "current", existing["id"], existing["version"]
        return outcome
    seeds = _planned_seeds(assemble_seeds(vault, repository, item, retrieve=False))
    route = plan_route(vault, ROUTE_TASK, client)  # type: ignore[arg-type]
    prompt = build_prompt(seeds)
    one = estimated_call_tokens(prompt, ApproachMapV1, route.output_tokens)
    price = vault.config.hints.price_per_million
    budget = SpendBudget(SpendCaps(max_estimated_usd=None, **_CAPS), subscription=route.billing == "subscription")
    calls = PaidCalls(route=route, budget=budget, price_per_million=price, repository=None,
                      owner_kind=OWNER_KIND, owner_id=item.id)
    plan = calls.plan([one])
    plan["worst_case_with_reask"] = calls.plan([one, one])
    plan["seeds"] = {"trace_contract": seeds.trace_contract is not None, "skeletons": len(seeds.skeletons),
                     "authored_hints": len(seeds.authored_hints), "learner_solutions": len(seeds.attempts),
                     "worked_examples": f"up to {MAX_SPANS}, counted at their cap",
                     "family_template": seeds.template is not None}
    outcome.billing = route.billing
    outcome.model = route.model
    outcome.estimate = plan
    if route.billing == "metered" and price is None:
        outcome.reason = "a metered route needs hints.price_per_million; this item would be skipped"
    return outcome


def backfill(vault: LoadedVault, repository: Repository, items: Iterable[PracticeItem], *, dry_run: bool,
             limit: int | None = None, client: Any | None = None, clock: Clock | None = None,
             find: Callable[..., Any] | None = None) -> dict[str, Any]:
    """``learnloop hints maps build``: build the items without a current map.

    A dry run prints the estimate and writes nothing. A real run stops at the
    first capped item (a capped day builds nothing more) and says so."""

    selected = list(items)
    result: dict[str, Any] = {
        "dry_run": dry_run, "enabled": maps_enabled(vault.config), "selected": len(selected),
        "route": None, "items": [], "counts": {},
    }
    if not maps_enabled(vault.config):
        result["status"] = "disabled"
        result["message"] = "hints.maps.enabled is off: nothing is built and nothing reads maps."
        return result
    route = plan_route(vault, ROUTE_TASK, client)  # type: ignore[arg-type]
    result["route"] = {"task": ROUTE_TASK, "provider": route.provider, "model": route.model, "billing": route.billing,
                       "cost_basis": "estimated_only" if route.billing == "subscription" else "metered_estimate"}
    counts: dict[str, int] = {}
    outcomes: list[dict[str, Any]] = []
    attempted = 0
    capped = False
    for item in selected:
        if dry_run:
            outcome = plan_item(vault, repository, item, client=client)
        else:
            if capped:
                outcome = MapOutcome(status="capped", practice_item_id=item.id, trigger="cli",
                                     reason=f"skipped: {ENVELOPE} was reached earlier in this run")
            elif limit is not None and attempted >= limit:
                outcome = MapOutcome(status="skipped", practice_item_id=item.id, trigger="cli",
                                     reason=f"--limit {limit} reached")
            else:
                outcome = build_map(vault, repository, item.id, trigger="cli", client=client, clock=clock,
                                    wait_seconds=None, find=find)
                if outcome.status not in ("current",):
                    attempted += 1
                capped = capped or outcome.status == "capped"
        counts[outcome.status] = counts.get(outcome.status, 0) + 1
        outcomes.append(outcome.as_dict())
    result["items"] = outcomes
    result["counts"] = counts
    if dry_run:
        due = [entry for entry in outcomes if entry["status"] == "planned"]
        usd = [((entry.get("estimate") or {}).get("estimated_usd")) for entry in due]
        result["estimate"] = {
            "builds_due": len(due), "already_current": counts.get("current", 0),
            "calls": len(due), "worst_case_calls_with_reask": 2 * len(due),
            "estimated_usd": None if any(value is None for value in usd) else round(sum(usd), 6),
            "cost_basis": result["route"]["cost_basis"],
            "daily_cap_usd": float(vault.config.hints.maps.max_daily_cost_usd),
        }
        result["status"] = "planned"
        result["message"] = "Dry run: nothing was retrieved, called or written."
    else:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            result["spend_today"] = maps_spend_today(vault, connection, clock=clock)
        result["status"] = "capped" if capped else "ok"
        if capped:
            result["message"] = (f"The day's map budget ({ENVELOPE} = ${float(vault.config.hints.maps.max_daily_cost_usd):.2f}) "
                                 "is spent: the remaining builds were skipped. Run again tomorrow or raise the cap.")
    return result


__all__ = [
    "BUILDS_ENV",
    "DRAIN_SECONDS",
    "ENVELOPE",
    "LEDGER_TASK",
    "MERGE_PROMPT_VERSION",
    "OWNER_KIND",
    "PROMPT_VERSION",
    "ROUTE_TASK",
    "BackgroundBuilds",
    "BuildFence",
    "MapOutcome",
    "backfill",
    "build_map",
    "build_map_inline",
    "build_prompt",
    "claim_key",
    "current_map",
    "map_context",
    "maps_enabled",
    "maps_envelope",
    "maps_spend_today",
    "merge_learner_routes",
    "merge_prompt",
    "new_learner_attempts",
    "plan_item",
    "schedule_build_on_serve",
    "schedule_merge_after_hint",
    "select_items",
    "wait_for_background_builds",
]
