"""PF-b: generate many, verify, filter, select, publish (Slice 2 §5.3-§5.4).

One durable job per (family, path, relation, round, tier) reuses the 078 mint
pipeline (``surface_mint_requests``: idempotent key, fenced lease, lifecycle,
retained failures), keyed on the family parent's practice card version. Paid
outputs are checkpointed per call (``ops.pf_calls``), candidates and their
filter results live in ``pf_candidates``, skeletons in ``item_skeletons`` and
every verdict in ``judgment_ledger``. A rebuild re-runs none of it and replay
never executes a generator: published items are stored instances.

Paths:

* ``generator``: the LLM writes one program per family; it runs in the
  bubblewrap sandbox, where unit tests assert the checkpoint sequence is
  invariant across draws and every final answer verifies by its own sympy or
  exact ``check`` (with negative controls). Draws are CAS-verified isomorphs.
* ``ensemble``: at least two distinct proposer models propose; the solver
  panel solves each stem without seeing the proposer's answer, and the
  reference is verified only when at least two panel solves agree, confirmed
  for numeric/symbolic answers by an LLM-written sympy check run in the
  sandbox. A declared isomorph must pass the structure check. The selection
  judge ranks verified survivors only.
* ``source_anchored``: papers, textbooks, repos. Answer first from a cited
  span of the LO's teaching sources; the reference is verified only when the
  quoted span appears verbatim in that source (and a "method does not apply"
  item carries its counterexample) and the reference verifier, reading only
  that span, confirms it states the answer and supports the explanation.
  Why-items without such a span are relabelled ``inferred`` and never
  published (provenance filter); items whose target is source-specific are
  rejected when a closed-book model answers them correctly (closed-book
  filter). No figure items exist yet (figure-only is not applicable).
  Executable what-if perturbations are not built, so a what-if whose
  consequence is executable stays unverified.
* ``single_shot``: the pilot baseline arm. One call, measured by the same
  verification and filters, never published.

Filters, cheapest first: authoring gates (the shared instrument chain),
held-out leakage, exact-key duplicates, verification, solver-panel outliers,
the structure check and the freshness judge. Difficulty is the solver panel's
per-variant offset (``difficulty_source = "solver_panel"``) from the parent's
panel rate, or, when no panel solve matched the parent's reference, from the
mean rate of the verified siblings; LLM self-labels are never requested.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Mapping
from contextlib import contextmanager
import copy
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
import math
from pathlib import Path
from typing import Any, Iterator

from learnloop.ai.errors import AIInterrupted, AIProviderUnavailable
from learnloop.ai.execution import content_key
from learnloop.ai.output_budget import output_budget
from learnloop.ai.spend import SpendCaps, SpendEstimate, SpendLimitExceeded
from learnloop.clock import Clock, utc_now_iso
from learnloop.content.authoring import pf_contracts as C
from learnloop.content.authoring.authoring_gates import build_instrument_gates
from learnloop.content.authoring.pf_sandbox import (
    GENERATOR_PROTOCOL, SandboxLimits, SandboxUnavailable, check_generator_answers,
    equivalence_confirmations, require_sandbox, run_equivalence_checks, run_generator_tests,
    sandbox_available,
)
from learnloop.content.sources.exam_material import exam_material, source_ref_protected
from learnloop.content.authoring.practice_leakage import (
    build_cross_source_spans, build_held_out_inventory, screen_practice_payload,
)
from learnloop.content.proposals.method_statement_judge import (
    LazyStatementJudge,
    planned_tokens,
    recorded_verdict,
    resolve_statement_judge,
)
from learnloop.db.repositories import Repository
from learnloop.db.stores import pf as store
from learnloop.ids import new_ulid
from learnloop.ops import pf_verify
from learnloop.ops.pf_calls import (
    ROLE_TASKS,
    PFCaller, PFUnavailable, RoleClient, distinct_models, estimate_tokens, planned_role_clients,
    resolve_role_clients,
)
from learnloop.ops.pf_publish import (
    TRACE_RELATIONS,
    judge_variant_stem,
    judged_inputs,
    publish_selected,
    remaining_publish_slots,
    stale_inputs,
)
from learnloop.ops.pf_selection import DIVERSITY_BASIS, mmr_order, similarity, vendi_contributions, vendi_score
from learnloop.substrate.activities import resolve_legacy_item
from learnloop.substrate.families import apply_family, family_operation_lock, sync_authored_families
from learnloop.substrate.item_fingerprints import (
    EXACT_COMPONENTS, FINGERPRINT_VERSION, final_answer_text, fingerprint_keys, item_fingerprint_keys,
    published_candidate_payloads, render_expected_answer, shared_keys, skeleton_content_hash,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.models import ActivityFamily, FamilyReference, LoadedVault, PracticeItem
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_activity_family

_LOGGER = logging.getLogger(__name__)

PATHS = ("generator", "ensemble", "source_anchored", "single_shot")
RELATIONS = ("same_target", "isomorph", "near", "far")
GENERATOR_VERSIONS = {"generator": "pf_generator_v1", "ensemble": "pf_ensemble_v1",
                      "source_anchored": "pf_source_anchored_v1", "single_shot": "pf_single_shot_v1"}
# v2 (Codex review): span-support verification, a final isomorph needs a
# passing checkpoint-preservation check, and every filter verdict is ledgered.
GATE_POLICY_VERSION = "pf_gate_v2"
# Deterministic MMR selection (generator and source-anchored families).
MMR_SELECTION_POLICY = "pf-mmr-select-v1"
FILTER_ORDER = (
    "authoring_gates", "held_out_leakage", "exact_duplicate", "execution_cas",
    "solve_first_agreement", "quote_verified_span", "provenance", "closed_book",
    "solver_panel_outlier", "structure_check", "freshness",
)
NOT_APPLICABLE_FILTERS = ("closed_book", "figure_only", "provenance")
# Every role's output budget is its route's under the shared policy
# (learnloop.ai.output_budget via PFCaller; the per-role caps of 800 to 8,000
# tokens are retired, owner 2026-10-12).
MIN_QUOTE_WORDS = 4
#: The agreement report PF keeps on a candidate (``panel``), unchanged by the
#: extraction to ``ops.pf_verify``.
PF_AGREEMENT_KEYS = ("agree", "total", "answer_kind", "usable", "sympy_checked", "normal_form",
                     "degenerate_check", "verifier_model")
PLAN_ROLES = ("skeleton", "program", "single_shot", "source", "proposer", "panel", "equivalence",
              "span_support", "closed_book", "structure", "freshness", "selection")
LEASE_SECONDS = 3600
DIFFICULTY_BOUNDS = (0.02, 0.98)


class PFRefused(ValueError):
    """A configuration the spec forbids (e.g. fewer than two distinct proposers)."""


@dataclass(frozen=True)
class GenerationOptions:
    path: str = "auto"
    relation: str = "isomorph"
    count: int | None = None
    select: int | None = None
    round: str | None = None
    tier: str | None = None
    publish: bool = True
    family_ids: tuple[str, ...] = ()
    learning_object_id: str | None = None
    seed_items: tuple[str, ...] = ()


@dataclass
class Candidate:
    id: str
    path: str
    payload: dict[str, Any]
    proposer_model: str | None
    prompt_version: str
    declared_relation: str
    status: str = "generated"
    verification: str = "unverified"
    verification_check: str | None = None
    final_relation: str | None = None
    rejection_filter: str | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    difficulty: float | None = None
    panel: dict[str, Any] = field(default_factory=dict)
    selection: dict[str, Any] = field(default_factory=dict)
    cost: dict[str, Any] = field(default_factory=dict)

    @property
    def alive(self) -> bool:
        return self.status in {"generated", "survivor", "baseline"} and self.rejection_filter is None

    @property
    def expected_answer(self) -> str:
        return render_expected_answer(self.payload["final_answer"], self.payload["solution"])

    @property
    def content_hash(self) -> str:
        return skeleton_content_hash(self.payload["stem"], self.expected_answer)


def _candidate_from_row(row: dict[str, Any]) -> Candidate:
    """A persisted candidate as the run holds it (review F20: a resumed job)."""

    def loads(raw: Any) -> dict[str, Any]:
        return json.loads(raw) if raw else {}

    return Candidate(
        id=row["id"], path=row["generation_path"], payload=json.loads(row["payload_json"]),
        proposer_model=row["proposer_model"], prompt_version=row["prompt_version"],
        declared_relation=row["declared_relation"], status=row["status"], verification=row["verification"],
        verification_check=row["verification_check"], final_relation=row["final_relation"],
        rejection_filter=row["rejection_filter"], filters=loads(row["filters_json"]),
        difficulty=row["difficulty"], panel=loads(row["panel_json"]), selection=loads(row["selection_json"]),
        cost=loads(row["cost_json"]),
    )


#: The completion marker a finished selection writes into every survivor's
#: ``selection_json``, in ONE transaction with the survivors' statuses (round
#: 3, F22): ``selected_order`` is the exact order chosen (the judge's, else
#: MMR's), and ``selection_complete`` says the whole selection was persisted.
SELECTION_ORDER_KEY = "selected_order"
SELECTION_COMPLETE_KEY = "selection_complete"


def selection_state(rows: list[Mapping[str, Any]]) -> dict[str, Any] | None:
    """How far a mint request's selection got, from its persisted candidates.

    * ``{"stage": "judgment", "order": [...]}``: the completion marker exists,
      so the selection finished; a rerun resumes at the judgment and
      publication step with exactly that order;
    * ``{"stage": "selection"}``: some candidate carries a selection but none
      the marker (persisted candidate by candidate before round 3, and
      interrupted): the selection never finished, so a rerun finishes it
      first (review F22), never taking the rows written so far for it;
    * None: selection never started (a rerun runs the pipeline, from
      checkpoints).
    """

    started = False
    for row in rows:
        raw = row.get("selection_json")
        if not raw:
            continue
        started = True
        try:
            selection = json.loads(raw)
        except (TypeError, ValueError):
            continue
        if isinstance(selection, dict) and selection.get(SELECTION_COMPLETE_KEY):
            return {"stage": "judgment", "order": [str(cid) for cid in selection.get(SELECTION_ORDER_KEY) or ()]}
    return {"stage": "selection"} if started else None


def _sha(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _logit(probability: float) -> float:
    return math.log(probability / (1.0 - probability))


def panel_difficulty(parent_difficulty: float | None, parent_rate: tuple[int, int],
                     variant_rate: tuple[int, int], scale: float) -> float:
    """Per-variant offset from the parent on the 2PL difficulty scale.

    With the panel's ability fixed, ``logit(s_parent) - logit(s_variant)`` is the
    difference in IRT ``b``; ``b = scale * (2d - 1)`` maps it to item difficulty.
    Solve rates are smoothed (k + 0.5) / (n + 1).
    """
    def smoothed(rate: tuple[int, int]) -> float:
        agree, total = rate
        return (agree + 0.5) / (total + 1.0)

    base = 0.5 if parent_difficulty is None else parent_difficulty
    offset = (_logit(smoothed(parent_rate)) - _logit(smoothed(variant_rate))) / (2.0 * scale)
    low, high = DIFFICULTY_BOUNDS
    return round(min(high, max(low, base + offset)), 4)


def _item_context(item: PracticeItem, vault: LoadedVault | None = None) -> dict[str, Any]:
    """Item-side material only; the resolved rubric (item or practice-mode default)."""
    resolved = vault.rubric_for_item(item) if vault is not None else item.grading_rubric
    rubric = resolved.model_dump(mode="json") if resolved is not None else None
    context = {"id": item.id, "prompt": item.prompt, "expected_answer": item.expected_answer,
               "practice_mode": item.practice_mode, "rubric": rubric,
               "trace_contract": item.trace_contract.model_dump(mode="json") if item.trace_contract else None}
    if item.required_method is not None:
        # Method-explicit items: shown only when set, so every other parent's
        # context (and its checkpoint keys) is unchanged.
        context["required_method"] = item.required_method.model_dump(mode="json")
    return context


def _family_context(family: ActivityFamily) -> dict[str, Any]:
    return {"id": family.id, "idea_statement": family.idea_statement,
            "retrieval_target": family.retrieval_target}


@contextmanager
def _run_lock(root: Path) -> Iterator[None]:
    import fcntl

    path = root / ".learnloop" / "pf-generate.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another PF generation or publication run is active") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


pf_run_lock = _run_lock


def family_targets(vault: LoadedVault, options: GenerationOptions) -> list[tuple[ActivityFamily, PracticeItem]]:
    """Families with an active member, each with its parent (anchor) item."""
    members: dict[str, list[PracticeItem]] = defaultdict(list)
    for item in vault.practice_items.values():
        if item.family_id and item.status != "retired":
            members[item.family_id].append(item)
    wanted = set(options.family_ids)
    unknown = wanted - set(vault.activity_families)
    if unknown:
        raise ValueError(f"Unknown activity families: {', '.join(sorted(unknown))}")
    result = []
    for family_id, family in sorted(vault.activity_families.items()):
        if wanted and family_id not in wanted:
            continue
        if options.learning_object_id and family.learning_object_id != options.learning_object_id:
            continue
        items = sorted(members.get(family_id, ()), key=lambda item: item.id)
        if not items:
            continue
        anchors = [item for item in items if item.variant_relation == "same_target"]
        parent = (anchors or items)[0]
        result.append((family, parent))
    return result


def _resolve_path(vault: LoadedVault, family: ActivityFamily, requested: str) -> str:
    if requested != "auto":
        return requested
    if family.source_kind in {"generator", "ensemble", "source_anchored"}:
        return family.source_kind
    return vault.config.pf.default_path


class _Context:
    def __init__(self, vault: LoadedVault, repository: Repository, caller: PFCaller,
                 options: GenerationOptions, round_id: str, tier_routes: list[str] | None,
                 clients: Mapping[str, Any] | None, clock: Clock | None) -> None:
        self.vault = vault
        self.repository = repository
        self.caller = caller
        self.options = options
        self.round = round_id
        self.tier_routes = tier_routes
        self.injected = dict(clients or {})
        self.clock = clock
        self.limits = SandboxLimits.from_config(vault.config.pf)
        self._roles: dict[str, list[RoleClient]] = {}
        self._inventory = None
        self._method_judge: Any = None

    def method_judge(self) -> Any:
        """The one-time required-method publication judge (redesign 2026-10-14),
        resolved on first use: ``clients["required_method_judge"]`` when
        injected, else the Decider via its route, else the LLM judge (a metered
        one at this run's owner price). Its requests are admitted under this
        run's caps (its metered or subscription budget), as the plan counts
        them."""

        if self._method_judge is None:
            injected = self.injected.get("required_method_judge")
            caller = self.caller
            # The run's owner price, as an upper bound when it is an input/output pair.
            price = caller.price if caller.price is not None else (
                max(caller.input_price, caller.output_price or 0.0) if caller.input_price is not None else None)
            self._method_judge = LazyStatementJudge(lambda: resolve_statement_judge(
                self.vault, clients=injected, price_per_million=price,
                budget_for=lambda billing: caller.subscription if billing == "subscription" else caller.metered))
        return self._method_judge

    def role(self, name: str) -> list[RoleClient]:
        if name not in self._roles:
            injected = self.injected.get(name)
            self._roles[name] = resolve_role_clients(
                self.vault, name, injected=injected, tier_routes=self.tier_routes,
            )
        return self._roles[name]

    def inventory(self):
        if self._inventory is None:
            self._inventory = build_held_out_inventory(self.vault, self.repository)
        return self._inventory

    def reload(self) -> None:
        self.vault = load_vault(self.vault.root)
        self.caller.vault = self.vault


class RequiredMethodJudgmentIncomplete(RuntimeError):
    """A selected variant has no required-method verdict yet (review F17):
    the family's job stays retryable instead of completing."""


class _FamilyRun:
    def __init__(self, ctx: _Context, family: ActivityFamily, parent: PracticeItem, path: str,
                 planned_resume: Mapping[str, Any] | None = None) -> None:
        self.ctx = ctx
        #: The resumable state the plan admitted this job under (round 3), or None.
        self.planned_resume = planned_resume
        self.family = family
        self.parent = parent
        self.path = path
        pf = ctx.vault.config.pf
        self.count = ctx.options.count or pf.candidates_per_family
        self.slots = ctx.options.select or pf.select_per_family
        self.relation = "isomorph" if path == "generator" else ctx.options.relation
        self.candidates: list[Candidate] = []
        self.request: dict[str, Any] | None = None
        self.parent_skeleton: dict[str, Any] | None = None
        self.parent_rate: tuple[int, int] | None = None
        self.program: dict[str, Any] | None = None
        self.notes: list[str] = []
        # The parent/family revisions and effective rubric every judge of this
        # run sees; stored per candidate and revalidated at publication.
        self.judged_inputs = judged_inputs(ctx.vault, parent, family)
        self.report: dict[str, Any] = {"family_id": family.id, "path": path,
                                       "parent_item_id": parent.id, "declared_relation": self.relation}

    # -- the 078 job ------------------------------------------------------------
    def _enqueue_and_claim(self) -> bool:
        repository = self.ctx.repository
        resolved = resolve_legacy_item(self.ctx.vault, repository, self.parent, purpose="practice",
                                       clock=self.ctx.clock)
        angle = _job_angle(self.family.id, self.path, self.relation, self.ctx.round, self.ctx.options.tier,
                           self.count)
        request_id = repository.enqueue_surface_mint_request(
            card_version_id=resolved.card_version_id, anchor_surface_id=resolved.surface_id,
            requested_angle_json=json.dumps(angle, sort_keys=True, separators=(",", ":")),
            generator_version=GENERATOR_VERSIONS[self.path], gate_policy_version=GATE_POLICY_VERSION,
            clock=self.ctx.clock,
        )
        now = utc_now_iso(self.ctx.clock)
        expires = (datetime.fromisoformat(now.replace("Z", "+00:00"))
                   + timedelta(seconds=LEASE_SECONDS)).strftime("%Y-%m-%dT%H:%M:%SZ")
        claimed = repository.claim_surface_mint_request(
            request_id, worker_id=self.ctx.caller.run_id, now_iso=now, lease_expires_at=expires,
        )
        self.report["mint_request_id"] = request_id
        # Stable per job (family, path, relation, round, tier, count): a resumed
        # job sends identical requests (checkpoint hits); a new round does not.
        self.generation_seed = content_key(["pf_generation_seed", GENERATOR_VERSIONS[self.path],
                                            json.dumps(angle, sort_keys=True)])[:16]
        if claimed is None:
            current = repository.surface_mint_request(request_id) or {}
            self.report["status"] = "already_" + str(current.get("status") or "claimed")
            return False
        self.request = claimed
        return True

    def _resolve_request(self, status: str, reason: str | None = None) -> None:
        if self.request is None:
            return
        summary = {key: self.report.get(key) for key in (
            "candidates", "by_status", "rejected_by_filter", "selected", "published_item_ids")}
        self.ctx.repository.resolve_surface_mint_request(
            request_id=self.request["id"], status=status, failure_reason=reason,
            gate_results_json=json.dumps(summary, sort_keys=True, default=str),
            expected_lease_epoch=self.request["lease_epoch"], require_active=True, clock=self.ctx.clock,
        )

    def release(self) -> None:
        if self.request is not None:
            self.ctx.repository.release_surface_mint_request(
                self.request["id"], expected_lease_epoch=self.request["lease_epoch"], clock=self.ctx.clock,
            )

    # -- persistence -------------------------------------------------------------
    def _write(self, connection: Any, candidate: Candidate, now: str) -> None:
        stored = store.candidate(connection, candidate.id)
        if stored is not None and stored["status"] == "published":
            return
        store.update_candidate(
            connection, candidate.id, status=candidate.status, verification=candidate.verification,
            verification_check=candidate.verification_check, final_relation=candidate.final_relation,
            rejection_filter=candidate.rejection_filter,
            filters_json=json.dumps(candidate.filters, sort_keys=True),
            payload_json=json.dumps(candidate.payload, sort_keys=True),
            difficulty=candidate.difficulty,
            difficulty_source="solver_panel" if candidate.difficulty is not None else None,
            panel_json=json.dumps(candidate.panel, sort_keys=True) if candidate.panel else None,
            selection_json=json.dumps(candidate.selection, sort_keys=True) if candidate.selection else None,
            cost_json=json.dumps(candidate.cost, sort_keys=True),
            updated_at=now,
        )

    def _persist_all(self, candidates: list[Candidate]) -> None:
        """Persist ``candidates`` in ONE transaction: all of them or none (review F22)."""
        now = utc_now_iso(self.ctx.clock)
        with self.ctx.repository.connection() as connection:
            for candidate in candidates:
                self._write(connection, candidate, now)

    def _persist(self, candidate: Candidate, *, insert: bool = False) -> None:
        now = utc_now_iso(self.ctx.clock)
        with self.ctx.repository.connection() as connection:
            if insert:
                store.insert_candidate(connection, {
                    "id": candidate.id, "run_id": self.ctx.caller.run_id,
                    "mint_request_id": self.request["id"] if self.request else None,
                    "round": self.ctx.round, "tier": self.ctx.options.tier,
                    "family_id": self.family.id, "parent_item_id": self.parent.id,
                    "learning_object_id": self.parent.learning_object_id,
                    "generation_path": candidate.path, "declared_relation": candidate.declared_relation,
                    "proposer_model": candidate.proposer_model, "prompt_version": candidate.prompt_version,
                    "payload_json": json.dumps(candidate.payload, sort_keys=True),
                    "content_hash": candidate.content_hash, "status": candidate.status,
                    "judged_inputs_json": json.dumps(self.judged_inputs, sort_keys=True),
                    "created_at": now, "updated_at": now,
                })
            self._write(connection, candidate, now)

    def _record_filter(self, candidate: Candidate, filter_name: str, verdict: str, detail: Any) -> None:
        """The authoritative filter verdict (§5.8): ledgered, idempotent, superseding.

        ``pf_candidates.filters_json`` mirrors it as pipeline state only; every
        report reads filter verdicts from ``judgment_ledger`` (task ``pf_filter``).
        """
        self.ctx.caller.ledger(
            task="pf_filter", left_kind="pf_candidate", left_id=candidate.id,
            right_kind="pf_filter", right_id=filter_name, judge="verifier",
            prompt_version=GATE_POLICY_VERSION,
            input_hash=content_key([candidate.content_hash, filter_name, verdict, detail]),
            verdict=verdict, supersede=True,
            rationale={"filter": filter_name, "path": candidate.path, "detail": detail},
        )

    def _reject(self, candidate: Candidate, filter_name: str, detail: Any = None) -> None:
        candidate.filters[filter_name] = {"passed": False, **({"detail": detail} if detail is not None else {})}
        self._record_filter(candidate, filter_name, "fail", detail)
        if candidate.path == "single_shot":
            # The baseline arm is measured, never published; record where it fell.
            candidate.rejection_filter = candidate.rejection_filter or filter_name
        else:
            candidate.status = "rejected"
            candidate.rejection_filter = filter_name
        self._persist(candidate)

    def _pass(self, candidate: Candidate, filter_name: str, detail: Any = None) -> None:
        candidate.filters[filter_name] = {"passed": True, **({"detail": detail} if detail is not None else {})}
        self._record_filter(candidate, filter_name, "not_applicable" if detail == "not_applicable" else "pass",
                            detail)

    def _call(self, entry: RoleClient, *, attribute: list[Candidate] | None = None, **kwargs: Any):
        """One paid call; its usage is shared equally across ``attribute`` (cost_json)."""
        call = self.ctx.caller.call(entry, **kwargs)
        for candidate in attribute or ():
            self._attribute(candidate, call, 1.0 / len(attribute))
        return call

    def _attribute(self, candidate: Candidate, call: Any, share: float) -> None:
        usage = call.usage or {}
        tokens = (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0)
        tokens = tokens or usage.get("estimated_total_tokens") or 0
        cost = candidate.cost
        cost["calls"] = round(cost.get("calls", 0.0) + share, 4)
        cost["tokens"] = round(cost.get("tokens", 0.0) + share * tokens, 1)
        if call.cached:
            cost["cached_calls"] = round(cost.get("cached_calls", 0.0) + share, 4)
        if usage.get("billing") == "subscription":
            cost["estimated_only_tokens"] = round(cost.get("estimated_only_tokens", 0.0) + share * tokens, 1)
        else:
            price = self.ctx.caller.price
            usd = usage.get("cost")
            if usd is None and price is not None:
                usd = tokens * price / 1_000_000
            if usd is not None:
                cost["metered_usd"] = round(cost.get("metered_usd", 0.0) + share * usd, 8)

    def _skeleton(self, *, subject_kind: str, subject_id: str, prompt: str, expected_answer: Any,
                  techniques: list[str], checkpoints: list[str], operations: list[str],
                  model: str, prompt_version: str, summary: str) -> dict[str, Any]:
        content_hash = skeleton_content_hash(prompt, expected_answer)
        record = {"model_id": model, "techniques": techniques, "checkpoints": checkpoints,
                  "operations": operations, "content_hash": content_hash}
        text = "Techniques: " + "; ".join(techniques) + "\nCheckpoints: " + "; ".join(checkpoints)
        if summary:
            text += "\nSummary: " + summary
        with self.ctx.repository.connection() as connection:
            store.insert_skeleton(
                connection, skeleton_id="sk_" + content_key([content_hash, model, prompt_version])[:32],
                content_hash=content_hash, subject_kind=subject_kind, subject_id=subject_id,
                model_id=model, prompt_version=prompt_version, techniques=techniques,
                operations=operations, checkpoints=checkpoints, skeleton_text=text,
                created_at=utc_now_iso(self.ctx.clock),
            )
        return record

    def _resume_after_selection(self) -> str | None:
        """Where a rerun of this job resumes, from its persisted candidates.

        ``"judgment"`` (review F20): the selection's completion marker exists
        (:func:`selection_state`), so the job was left retryable after
        selection (a required-method judgment could not be made, F17; a spend
        refusal or a cancellation stopped it there; publication failed). Its
        candidates, filters, panel and selection are persisted: the rerun
        loads them and takes the selected order exactly as it was chosen,
        then asks only the missing verdicts (each verdict already ledgered is
        reused) and publishes. The variants it published meanwhile would
        change the freshness and selection requests, so re-running the
        pipeline would miss their checkpoints and pay again.

        ``"selection"`` (review F22): a selection was started but its marker
        never written (the rows of a selection persisted candidate by
        candidate, interrupted). Nothing was published from it, so the
        survivors are loaded back as survivors and the selection is finished
        first (its judge's request is the one already checkpointed), never
        judged from the partial rows.

        None: selection never started; the pipeline runs (from checkpoints).
        """
        if self.request is None or self.path == "single_shot":
            return None
        with self.ctx.repository.connection() as connection:
            rows = store.candidates(connection, where="mint_request_id=?", params=(self.request["id"],))
        state = selection_state(rows)
        if state is None:
            return None
        self.candidates = [_candidate_from_row(row) for row in rows]
        if state["stage"] == "judgment":
            known = {candidate.id for candidate in self.candidates}
            self.selected_order = [cid for cid in state["order"] if cid in known]
            self.report["resumed"] = "required_method_judgment"
            return "judgment"
        for candidate in self.candidates:
            if candidate.status in ("selected", "not_selected"):
                candidate.status = "survivor"
            candidate.selection = {}
        self.report["resumed"] = "selection"
        return "selection"

    def _judge_and_publish(self) -> None:
        try:
            self._judge_required_method()
        except RequiredMethodJudgmentIncomplete:
            # Review F17: the variants judged so far publish now; the job
            # stays retryable for the rest (below), and a rerun resumes here
            # (F20) without any pipeline work.
            if self.ctx.options.publish:
                self._publish()
            raise
        if self.ctx.options.publish:
            self._publish()

    # -- stages -------------------------------------------------------------------
    def execute(self) -> dict[str, Any]:
        if not self._enqueue_and_claim():
            return self.report
        try:
            stage = self._resume_after_selection()
            if stage == "judgment":
                self._judge_and_publish()
            elif stage == "selection":
                self._select()
                self._judge_and_publish()
            elif self.planned_resume is not None:
                # The plan admitted only this job's unfinished work, and the
                # job has none to resume now: nothing unplanned is paid for.
                self.release()
                self.report.update(status="resume_unavailable",
                                   reason="the job planned as a resume has no persisted selection; rerun to plan it")
                return self.report
            else:
                self._run_pipeline()
            self._summarize()
            selected = self.report.get("selected", 0) + len(self.report.get("published_item_ids", []))
            self._resolve_request("admitted" if selected else "rejected")
            self.report["status"] = "complete"
        except RequiredMethodJudgmentIncomplete as exc:
            # Review F17: paid, verified variants are never stranded by a
            # judgment that could not be made (a timeout, a failure, no judge
            # ready): the mint request is left ``failed``, which a rerun of
            # the round reclaims, resuming at the judgment (F20) and asking
            # only the missing verdicts.
            self._summarize()
            self._resolve_request("failed", reason="required_method_unjudged")
            self.report.update(status="judgment_incomplete", reason=str(exc))
        except (AIInterrupted, KeyboardInterrupt):
            self._summarize()
            self.release()
            raise
        except SpendLimitExceeded:
            self._summarize()
            self.release()
            raise
        except (AIProviderUnavailable, PFUnavailable, SandboxUnavailable) as exc:
            self._summarize()
            self._resolve_request("failed", reason=type(exc).__name__)
            self.report.update(status="failed", error_type=type(exc).__name__, reason=str(exc)[:300])
        except Exception as exc:
            # Never leave the job leased: a failed job is retained for audit and
            # a rerun of the round reclaims it (paid work stays checkpointed).
            self._resolve_request("failed", reason=type(exc).__name__)
            raise
        return self.report

    def _run_pipeline(self) -> None:
        self.parent_skeleton = self._parent_skeleton()
        if self.path == "generator":
            self._generate_programs()
        elif self.path == "source_anchored":
            self._generate_source_anchored()
        else:
            self._generate_proposals()
        self._free_filters()
        if self.path == "generator":
            self._panel_generator()
        elif self.path == "source_anchored":
            self._verify_source_anchored()
        else:
            self._verify_ensemble()
        self._finalize_difficulty()
        self._structure()
        self._freshness()
        for candidate in self.candidates:
            if candidate.alive:
                for name in NOT_APPLICABLE_FILTERS:
                    if name not in candidate.filters:
                        self._pass(candidate, name, "not_applicable")
                if candidate.path != "single_shot":
                    candidate.status = "survivor"
                self._persist(candidate)
        if self.path != "single_shot":
            self._select()
            self._judge_and_publish()

    def _parent_skeleton(self) -> dict[str, Any]:
        entry = self.ctx.role("skeleton")[0]
        call = self.ctx.caller.call(
            entry, prompt=C.skeleton_prompt(prompt=self.parent.prompt, expected_answer=self.parent.expected_answer),
            prompt_version=C.SKELETON_PROMPT, result_model=C.SkeletonResult,
        )
        result = call.result
        return self._skeleton(
            subject_kind="practice_item", subject_id=self.parent.id, prompt=self.parent.prompt,
            expected_answer=self.parent.expected_answer, techniques=result.techniques,
            checkpoints=result.checkpoints, operations=result.operations, model=call.model,
            prompt_version=C.SKELETON_PROMPT, summary=result.summary,
        )

    # generator path
    def _program_ok(self, code: str, declared: list[str], seeds: list[int]) -> tuple[bool, str, list[dict[str, Any]]]:
        result = run_generator_tests(code, seeds=seeds, limits=self.ctx.limits)
        if not result.ok:
            return False, f"sandbox: {result.error}; {result.stderr_tail[-300:]}", []
        output = result.output or {}
        if output.get("import_error"):
            return False, ("the program field is not importable Python source defining generate and "
                           f"check: {output['import_error']}"), []
        draws = output.get("draws") or []
        problems = []
        for entry in draws:
            if entry.get("error"):
                problems.append(f"seed {entry.get('seed')}: {entry['error']}")
            elif not entry.get("self_check"):
                problems.append(f"seed {entry['seed']}: check(draw, draw['final_answer']) returned False "
                                f"for final_answer {entry['draw'].get('final_answer')!r:.80}")
            elif not entry.get("negative_controls_rejected"):
                problems.append(f"seed {entry['seed']}: check accepts a wrong answer")
            elif entry["draw"]["checkpoints"] != declared:
                problems.append(f"seed {entry['seed']}: checkpoints {entry['draw']['checkpoints']!r:.160} "
                                f"differ from the declared {declared!r:.160}")
        if not problems and len({entry["draw"]["stem"] for entry in draws}) < min(2, len(draws)):
            problems.append("every seed produced the same stem: draw the parameters from "
                            "random.Random(seed) instead of hard-coding them")
        return not problems, "; ".join(problems)[:1500], draws

    def _program(self) -> dict[str, Any] | None:
        """The family's tested generator program.

        An ordinary run reuses (or writes and stores) the family's authored
        program. A scaling-check run (``--tier``) is a measurement: each tier's
        writer writes its own program from the same frozen inputs (parent,
        family, parent skeleton), it is never read from or stored into the
        family, and it is persisted per tier, model/settings, prompt version
        and input revision through the writer call's checkpoint.
        """
        test_seeds = list(range(self.ctx.vault.config.pf.generator_test_draws))
        tiered = self.ctx.options.tier is not None
        inputs = {"parent": _item_context(self.parent, self.ctx.vault), "family": _family_context(self.family),
                  "skeleton": self.parent_skeleton or {}}
        inputs_revision = content_key(inputs)
        existing = {} if tiered else (self.family.generator or {})
        if (existing.get("protocol") == GENERATOR_PROTOCOL and existing.get("program")
                and existing.get("hash") == _sha(existing["program"])):
            ok, failure, _ = self._program_ok(existing["program"], list(existing.get("checkpoints") or []), test_seeds)
            self.ctx.caller.ledger(
                task="generator_tests", left_kind="activity_family", left_id=self.family.id,
                judge="verifier", prompt_version=GENERATOR_PROTOCOL, input_hash=existing["hash"],
                verdict="pass" if ok else "fail", rationale={"failure": failure, "seeds": test_seeds},
            )
            if ok:
                return dict(existing)
            self.notes.append("stored generator program failed its tests; writing a new one")
        entry = self.ctx.role("program")[0]
        failure: str | None = None
        attempts = 0
        while True:
            call = self.ctx.caller.call(
                entry, prompt=C.generator_program_prompt(
                    parent=inputs["parent"], family=inputs["family"],
                    skeleton=inputs["skeleton"], relation="isomorph", previous_failure=failure,
                    attempt=attempts),
                prompt_version=C.GENERATOR_PROGRAM_PROMPT, result_model=C.GeneratorProgramResult,
            )
            code = call.result.program
            ok, failure_text, _ = self._program_ok(code, list(call.result.checkpoints), test_seeds)
            self.ctx.caller.ledger(
                task="generator_tests", left_kind="activity_family", left_id=self.family.id,
                judge="verifier", prompt_version=GENERATOR_PROTOCOL, input_hash=_sha(code),
                verdict="pass" if ok else "fail",
                rationale={"failure": failure_text, "seeds": test_seeds, "model": call.model,
                           "tier": self.ctx.options.tier, "inputs_revision": inputs_revision},
            )
            if ok:
                program = {
                    "protocol": GENERATOR_PROTOCOL, "program": code, "hash": _sha(code),
                    "checkpoints": list(call.result.checkpoints), "model": call.model,
                    "prompt_version": C.GENERATOR_PROGRAM_PROMPT, "tested_seeds": test_seeds,
                }
                if tiered:
                    self.report["tier_program"] = {
                        "tier": self.ctx.options.tier, "model": call.model, "hash": program["hash"],
                        "prompt_version": C.GENERATOR_PROGRAM_PROMPT, "inputs_revision": inputs_revision,
                        "writer_input_hash": call.input_hash, "cached": call.cached,
                    }
                else:
                    self._store_program(program)
                return program
            failure = failure_text
            attempts += 1
            if attempts > self.ctx.caller.caps.max_retries:
                self.report["program_failure"] = failure_text[:500]
                return None

    def _store_program(self, program: dict[str, Any]) -> None:
        """Persist the tested program as the family's authored generator content."""
        with family_operation_lock(self.ctx.vault.root):
            current = load_vault(self.ctx.vault.root).activity_families[self.family.id]
            updated = current.model_copy(update={
                "generator": program, "source_kind": "generator",
                "reference": FamilyReference(verification="verified", check="generator_cas_unit_tests"),
                "updated_at": utc_now_iso(self.ctx.clock),
            })
            upsert_activity_family(self.ctx.vault.root, updated)
        self.ctx.reload()
        sync_authored_families(self.ctx.vault, self.ctx.repository, clock=self.ctx.clock)
        self.family = self.ctx.vault.activity_families[self.family.id]

    def _generate_programs(self) -> None:
        program = self._program()
        if program is None:
            self.report["status_detail"] = "generator_tests_failed"
            return
        self.program = program
        base = int(content_key([self.request["id"], program["hash"]])[:8], 16)
        seeds = [base + index for index in range(self.count)]
        result = run_generator_tests(program["program"], seeds=seeds, limits=self.ctx.limits)
        draws = (result.output or {}).get("draws") or [] if result.ok else []
        for index, seed in enumerate(seeds):
            entry = next((draw for draw in draws if draw.get("seed") == seed), {"seed": seed, "error": result.error})
            draw = entry.get("draw") or {}
            payload = {
                "stem": draw.get("stem") or "", "solution": draw.get("solution") or "",
                "final_answer": draw.get("final_answer") or "", "answer_kind": "symbolic",
                "parameters": draw.get("parameters"), "checkpoints": draw.get("checkpoints") or [],
                "techniques": list((self.parent_skeleton or {}).get("techniques") or []),
                "generator_hash": program["hash"], "seed": seed,
                "sympy_normal_form": entry.get("normal_form"),
                "change_note": "parameter draw", "preserved_note": "program-invariant checkpoints",
            }
            candidate = Candidate(
                id="pfc_" + content_key([self.request["id"], "generator", program["hash"], seed])[:32],
                path="generator", payload=payload, proposer_model=program.get("model"),
                prompt_version=C.GENERATOR_PROGRAM_PROMPT, declared_relation="isomorph",
            )
            self.candidates.append(candidate)
            self._persist(candidate, insert=True)
            verified = (not entry.get("error") and entry.get("self_check")
                        and entry.get("negative_controls_rejected")
                        and draw.get("checkpoints") == program["checkpoints"] and payload["stem"])
            self.ctx.caller.ledger(
                task="reference_verified", left_kind="pf_candidate", left_id=candidate.id,
                judge="verifier", prompt_version=GENERATOR_PROTOCOL, input_hash=candidate.content_hash,
                verdict="pass" if verified else "fail",
                rationale={"check": "execution_cas", "error": entry.get("error"),
                           "self_check": entry.get("self_check"),
                           "negative_controls_rejected": entry.get("negative_controls_rejected")},
            )
            if not verified:
                self._reject(candidate, "execution_cas", entry.get("error") or "check failed")
                continue
            candidate.verification = "verified"
            candidate.verification_check = "execution_cas"
            self._pass(candidate, "execution_cas")
            self._skeleton(
                subject_kind="pf_candidate", subject_id=candidate.id, prompt=payload["stem"],
                expected_answer=candidate.expected_answer, techniques=payload["techniques"] or ["generator"],
                checkpoints=payload["checkpoints"], operations=[], model=program.get("model") or "generator",
                prompt_version=C.GENERATOR_PROGRAM_PROMPT, summary="generator program draw",
            )
            self._persist(candidate)

    # ensemble and single-shot paths
    def _generate_proposals(self) -> None:
        single = self.path == "single_shot"
        entries = self.ctx.role("single_shot") if single else self.ctx.role("proposer")
        if not single and len(distinct_models(entries)) < 2:
            raise PFRefused("pf_proposers must resolve to at least two distinct model slugs")
        share = max(1, math.ceil(self.count / len(entries)))
        for slot, entry in enumerate(entries):
            count = min(share, self.count - share * slot) if not single else self.count
            if count <= 0:
                continue
            call = self.ctx.caller.call(
                entry, prompt=C.proposer_prompt(
                    parent=_item_context(self.parent, self.ctx.vault), family=_family_context(self.family),
                    skeleton=self.parent_skeleton or {}, relation=self.relation, count=count,
                    generation_seed=self.generation_seed, single_shot=single),
                prompt_version=C.SINGLE_SHOT_PROMPT if single else C.PROPOSER_PROMPT,
                result_model=C.ProposalBatch, candidates=count,
            )
            for index, proposed in enumerate(call.result.candidates[:count]):
                payload = proposed.model_dump(mode="json")
                candidate = Candidate(
                    id="pfc_" + content_key([self.request["id"], self.path, entry.provider, call.input_hash, index])[:32],
                    path=self.path, payload=payload, proposer_model=call.model,
                    prompt_version=call.prompt_version, declared_relation=self.relation,
                    status="baseline" if single else "generated",
                )
                self.candidates.append(candidate)
                self._attribute(candidate, call, 1.0 / max(1, min(count, len(call.result.candidates))))
                self._persist(candidate, insert=True)
                self._skeleton(
                    subject_kind="pf_candidate", subject_id=candidate.id, prompt=payload["stem"],
                    expected_answer=candidate.expected_answer, techniques=payload["techniques"],
                    checkpoints=payload["checkpoints"], operations=[], model=call.model,
                    prompt_version=call.prompt_version, summary=payload.get("change_note") or "",
                )

    # source-anchored path
    def _passages(self) -> list[dict[str, Any]]:
        """Teaching spans for the LO (assessment-adjacent sources excluded), plus quotes on the parent."""
        passages: list[dict[str, Any]] = []
        # The one exam predicate: exam and held-out material never grounds a
        # generated variant, neither as a linked span nor as the parent's quote.
        exam = exam_material(self.ctx.vault, self.ctx.repository)
        for span in build_cross_source_spans(self.ctx.vault, self.ctx.repository,
                                             self.parent.learning_object_id, max_spans_per_item=6, exam=exam):
            passages.append({"text": span.text, "label": span.label, "extraction_id": span.extraction_id,
                             "span_id": span.span_id, "source_id": span.source_id})
        for ref in self.parent.provenance.source_refs:
            if not (ref.quote and ref.quote.strip()):
                continue
            # Located through the shared parser (a locator, plain or namespaced
            # span ids); a quote it cannot place in a partly protected
            # extraction or source is dropped (Codex review F4).
            if source_ref_protected(exam, ref, self.ctx.repository):
                continue
            passages.append({"text": ref.quote.strip(), "label": ref.ref_type, "ref_id": ref.ref_id,
                             "extraction_id": ref.extraction_id, "span_id": (ref.span_ids or [None])[0]})
        return [{**passage, "ref": f"s{index}"} for index, passage in enumerate(passages)]

    def _generate_source_anchored(self) -> None:
        passages = self._passages()
        self.passages = {passage["ref"]: passage for passage in passages}
        if not passages:
            self.notes.append("no teaching source spans for this LO")
            self.report["status_detail"] = "no_source_spans"
            return
        entry = self.ctx.role("source")[0]
        call = self.ctx.caller.call(
            entry, prompt=C.source_anchored_prompt(
                passages=[{"ref": passage["ref"], "text": passage["text"]} for passage in passages],
                parent=_item_context(self.parent, self.ctx.vault), family=_family_context(self.family), count=self.count,
                generation_seed=self.generation_seed),
            prompt_version=C.SOURCE_ANCHORED_PROMPT, result_model=C.SourceAnchoredBatch,
            candidates=self.count,
        )
        for index, proposed in enumerate(call.result.candidates[:self.count]):
            payload = proposed.model_dump(mode="json")
            passage = self.passages.get(proposed.cited_ref) or {}
            solution = proposed.solution.strip() + f'\n\nSource: "{proposed.cited_quote.strip()}"'
            if proposed.counterexample:
                solution += f"\n\nCounterexample: {proposed.counterexample.strip()}"
            payload.update(final_answer=proposed.answer, solution=solution, answer_kind="text",
                           techniques=[proposed.item_kind], checkpoints=["cite the source span", "answer"],
                           cited_span={key: passage.get(key) for key in ("label", "extraction_id", "span_id",
                                                                          "source_id", "ref_id")})
            candidate = Candidate(
                id="pfc_" + content_key([self.request["id"], "source", call.input_hash, index])[:32],
                path="source_anchored", payload=payload, proposer_model=call.model,
                prompt_version=C.SOURCE_ANCHORED_PROMPT, declared_relation=self.relation,
            )
            self.candidates.append(candidate)
            self._attribute(candidate, call, 1.0 / max(1, min(self.count, len(call.result.candidates))))
            self._persist(candidate, insert=True)

    @staticmethod
    def _quote_in(quote: str, text: str) -> bool:
        def normalized(value: str) -> str:
            return " ".join(value.casefold().split())

        return len(quote.split()) >= MIN_QUOTE_WORDS and normalized(quote) in normalized(text)

    def _span_support(self, candidate: Candidate) -> dict[str, Any]:
        """The reference verifier's independent check that the cited span supports the key."""
        payload = candidate.payload
        support = pf_verify.span_support(
            self._verifier(), subject_kind="pf_candidate", subject_id=candidate.id,
            question=payload["stem"], cited_quote=payload["cited_quote"],
            reference_answer=payload["answer"], explanation=payload["solution"],
            item_kind=payload["item_kind"], on_call=self._attributor([candidate]),
        )
        support.pop("span_answer", None)
        return support

    def _verify_source_anchored(self) -> None:
        """Quote-verified span (exact key) that supports the answer, provenance, then closed-book.

        A reference is verified only when the quoted span appears verbatim in
        its passage (and a "method does not apply" item carries its
        counterexample) AND the reference verifier, reading only that span,
        confirms that it states the answer and supports the explanation. A
        verbatim but unrelated or contradicting quote never verifies a key.
        """
        passages = getattr(self, "passages", {})
        for candidate in [c for c in self.candidates if c.alive]:
            payload = candidate.payload
            passage = passages.get(payload["cited_ref"])
            quoted = passage is not None and self._quote_in(payload["cited_quote"], passage["text"])
            complete = payload["item_kind"] != "method_does_not_apply" or bool((payload.get("counterexample") or "").strip())
            span_ok = quoted and complete
            self.ctx.caller.ledger(
                task="reference_verified", left_kind="pf_candidate", left_id=candidate.id,
                judge="exact_key", prompt_version="pf-quote-span-v1", input_hash=candidate.content_hash,
                verdict="pass" if span_ok else "fail",
                rationale={"check": "quote_verified_span", "quote_found": quoted,
                           "counterexample_required": payload["item_kind"] == "method_does_not_apply",
                           "item_kind": payload["item_kind"]},
            )
            support = self._span_support(candidate) if span_ok else None
            verified = span_ok and bool(support and support["supported"])
            if not verified:
                detail = {"quote_found": quoted, "complete": complete}
                if support is not None:
                    detail.update({key: support[key] for key in (
                        "answer_supported", "rationale_supported", "execution_check_required")})
                if payload["item_kind"] == "why":
                    # Rationale the cited span does not state is a plausible
                    # interpretation, never the key.
                    payload["provenance_label"] = "inferred"
                    self.ctx.caller.ledger(
                        task="provenance", left_kind="pf_candidate", left_id=candidate.id,
                        judge="verifier", prompt_version="pf-quote-span-v1",
                        input_hash=candidate.content_hash, verdict="inferred",
                        rationale={"reason": "no verified span" if not quoted else "cited span does not state it"},
                    )
                    self._reject(candidate, "provenance", {"relabelled": "inferred_unverified", **detail})
                else:
                    self._reject(candidate, "quote_verified_span", detail)
                continue
            candidate.verification = "verified"
            candidate.verification_check = "quote_verified_span+support"
            self._pass(candidate, "quote_verified_span", {"support_model": support["model"]})
            self._pass(candidate, "provenance", "cited")
            if not payload.get("source_specific"):
                self._pass(candidate, "closed_book", "not_source_specific")
                self._persist(candidate)
                continue
            closed = self.ctx.role("closed_book")[0]
            call = self._call(
                closed, attribute=[candidate], prompt=C.closed_book_prompt(stem=payload["stem"]),
                prompt_version=C.CLOSED_BOOK_PROMPT, result_model=C.PanelSolve,
            )
            solve = {"model": call.model, "index": 0, "input_hash": call.input_hash,
                     "final_answer": call.result.final_answer, "answer_kind": call.result.answer_kind}
            outcome = self._agreement("pf_candidate", candidate.id, candidate.content_hash,
                                      payload["stem"], payload["answer"], [solve], attribute=[candidate])
            answerable = outcome["agree"] >= 1
            self.ctx.caller.ledger(
                task="closed_book", left_kind="pf_candidate", left_id=candidate.id, judge="llm",
                judge_model=call.model, prompt_version=C.CLOSED_BOOK_PROMPT, input_hash=call.input_hash,
                verdict="answerable" if answerable else "not_answerable",
                rationale={"verifier_model": outcome["verifier_model"]},
            )
            if answerable:
                self._reject(candidate, "closed_book", {"closed_book_model": call.model})
                continue
            self._pass(candidate, "closed_book", {"closed_book_model": call.model})
            self._persist(candidate)

    # free filters
    def _free_filters(self) -> None:
        alive = [candidate for candidate in self.candidates if candidate.alive]
        if not alive:
            return
        rows = []
        for candidate in alive:
            payload = {
                "id": candidate.id, "learning_object_id": self.parent.learning_object_id,
                "practice_mode": self.parent.practice_mode, "prompt": candidate.payload["stem"],
                "expected_answer": candidate.expected_answer,
                "evidence_facets": list(self.parent.evidence_facets),
                "grading_rubric": (self.parent.grading_rubric.model_dump(mode="json")
                                   if self.parent.grading_rubric is not None else None),
            }
            rows.append({"item_type": "practice_item", "operation": "create", "client_item_id": candidate.id,
                         "payload": copy.deepcopy(payload), "validation_status": "valid",
                         "validation_errors": [], "_auto_apply": True, "_original": payload})
        gates = build_instrument_gates(self.ctx.vault, self.ctx.repository)
        gates(rows)
        hard = {entry["entity_refs"][0] for entry in gates.diagnostics() if entry["severity"] == "hard_fail"}
        inventory = self.ctx.inventory()
        for candidate, row in zip(alive, rows):
            if row.get("validation_status") == "invalid" or candidate.id in hard:
                self._reject(candidate, "authoring_gates", row.get("validation_errors") or ["hard_fail"])
                continue
            self._pass(candidate, "authoring_gates")
            findings = screen_practice_payload(row["_original"], inventory)
            if findings:
                self._reject(candidate, "held_out_leakage", [finding["kind"] for finding in findings])
                continue
            self._pass(candidate, "held_out_leakage")
        # Exact keys decide duplicates (identity), against the LO and the batch.
        lo_keys = self._lo_keys()
        seen: dict[tuple[str, str, str], str] = {}
        for candidate in self.candidates:
            if not candidate.alive:
                continue
            keys = self._candidate_keys(candidate)
            exact = [key for key in keys if (key[0], key[1]) in EXACT_COMPONENTS]
            duplicate_of = None
            for item_id, item_keys in lo_keys.items():
                if set(exact) & set(item_keys):
                    duplicate_of = ("practice_item", item_id)
                    break
            if duplicate_of is None:
                for key in exact:
                    if key in seen:
                        duplicate_of = ("pf_candidate", seen[key])
                        break
            if duplicate_of is not None:
                self.ctx.caller.ledger(
                    task="isomorph", left_kind="pf_candidate", left_id=candidate.id,
                    right_kind=duplicate_of[0], right_id=duplicate_of[1], judge="exact_key",
                    prompt_version=FINGERPRINT_VERSION, input_hash=candidate.content_hash,
                    verdict="same_surface", rationale={"keys": [list(key[:2]) for key in exact]},
                )
                self._reject(candidate, "exact_duplicate", {"of": duplicate_of[1]})
                continue
            for key in exact:
                seen.setdefault(key, candidate.id)
            self._pass(candidate, "exact_duplicate")
            self._persist(candidate)

    def _lo_items(self) -> list[PracticeItem]:
        return [item for _, item in sorted(self.ctx.vault.practice_items.items())
                if item.learning_object_id == self.parent.learning_object_id]

    def _lo_keys(self) -> dict[str, list[tuple[str, str, str]]]:
        items = self._lo_items()
        hashes = {item.id: skeleton_content_hash(item.prompt, item.expected_answer) for item in items}
        with self.ctx.repository.connection() as connection:
            skeletons = store.skeletons_for_hashes(connection, hashes.values())
            payloads = published_candidate_payloads(connection)
        return {item.id: item_fingerprint_keys(item, skeletons=skeletons.get(hashes[item.id], ()),
                                               payload=payloads.get(item.id))
                for item in items}

    def _candidate_keys(self, candidate: Candidate) -> list[tuple[str, str, str]]:
        payload = candidate.payload
        skeletons = [{"model_id": candidate.proposer_model or "generator",
                      "prompt_version": candidate.prompt_version,
                      "techniques": payload.get("techniques") or []}]
        return fingerprint_keys(
            prompt=payload["stem"], expected_answer=candidate.expected_answer, skeletons=skeletons,
            generator_hash=payload.get("generator_hash"), parameters=payload.get("parameters"),
            sympy_normal_form=payload.get("sympy_normal_form"),
        )

    # verification (ops.pf_verify: shared with the canonical-sources key ladder)
    def _verifier(self) -> pf_verify.VerifierEnv:
        return pf_verify.VerifierEnv(caller=self.ctx.caller, role=self.ctx.role, limits=self.ctx.limits)

    def _attributor(self, attribute: list[Candidate] | None):
        """Share each call's usage equally across ``attribute`` (cost_json), as ``_call`` does."""
        if not attribute:
            return None

        def on_call(call: Any) -> None:
            for candidate in attribute:
                self._attribute(candidate, call, 1.0 / len(attribute))

        return on_call

    def _panel_solves(self, stem: str, *, solves_per_model: int,
                      attribute: list[Candidate] | None = None) -> list[dict[str, Any]]:
        return pf_verify.panel_solves(self._verifier(), stem, solves_per_model=solves_per_model,
                                      on_call=self._attributor(attribute))

    def _agreement(self, subject_kind: str, subject_id: str, input_hash: str, stem: str,
                   reference: str, solves: list[dict[str, Any]],
                   attribute: list[Candidate] | None = None) -> dict[str, Any]:
        """LLM agreement per solve, confirmed by the sandboxed sympy check where numeric/symbolic.

        PF decides on the combined ``agree`` exactly as before the extraction,
        and keeps the report it always kept (the separated model and symbolic
        results are the source-import ladder's)."""
        outcome = pf_verify.agreement(self._verifier(), subject_kind, subject_id, input_hash, stem,
                                      reference, solves, on_call=self._attributor(attribute))
        return {key: outcome[key] for key in PF_AGREEMENT_KEYS} | {
            "per_solve": [{"model": row["model"], "agree": row["agree"]} for row in outcome["per_solve"]]}

    def _parent_rate(self) -> tuple[int, int]:
        if self.parent_rate is None:
            k = self.ctx.vault.config.pf.panel_solves_per_model
            solves = self._panel_solves(self.parent.prompt, solves_per_model=k)
            outcome = self._agreement(
                "practice_item", self.parent.id, content_key(_item_context(self.parent, self.ctx.vault)),
                self.parent.prompt, final_answer_text(self.parent.expected_answer), solves,
            )
            self.parent_rate = (outcome["agree"], outcome["total"])
            self.report["parent_panel"] = {"agree": outcome["agree"], "total": outcome["total"]}
        return self.parent_rate

    def _set_difficulty(self, candidate: Candidate, agree: int, total: int) -> None:
        """Record the variant's panel rate; ``_finalize_difficulty`` sets the offset."""
        candidate.panel["variant_rate"] = [agree, total]
        self._parent_rate()

    def _finalize_difficulty(self) -> None:
        """Per-variant offsets from the parent's panel rate, or from the batch.

        When no panel solve matched the parent's reference (usually a prose
        reference, not a hard parent), the parent rate is uninformative; the
        reference is then the mean logit solve rate of the verified siblings.
        """
        rated = [c for c in self.candidates if c.alive and "variant_rate" in c.panel]
        if not rated:
            return
        scale = self.ctx.vault.config.mastery.irt.difficulty_prior_scale
        parent_rate = self._parent_rate()

        def logit(rate: list[int] | tuple[int, int]) -> float:
            return _logit((rate[0] + 0.5) / (rate[1] + 1.0))

        batch_reference = sum(logit(c.panel["variant_rate"]) for c in rated) / len(rated)
        for candidate in rated:
            rate = tuple(candidate.panel["variant_rate"])
            if parent_rate[0] > 0:
                basis = "parent_panel"
                candidate.difficulty = panel_difficulty(self.parent.difficulty, parent_rate, rate, scale)
            else:
                basis = "batch_mean"
                base = 0.5 if self.parent.difficulty is None else self.parent.difficulty
                low, high = DIFFICULTY_BOUNDS
                candidate.difficulty = round(min(high, max(low, base + (batch_reference - logit(rate)) / (2.0 * scale))), 4)
            candidate.panel["difficulty_basis"] = basis
            candidate.panel["parent_rate"] = list(parent_rate)
            self._persist(candidate)

    def _verify_ensemble(self) -> None:
        pf = self.ctx.vault.config.pf
        for candidate in [c for c in self.candidates if c.alive]:
            solves = self._panel_solves(candidate.payload["stem"], solves_per_model=pf.panel_solves_per_model,
                                        attribute=[candidate])
            outcome = self._agreement("pf_candidate", candidate.id, candidate.content_hash,
                                      candidate.payload["stem"], candidate.payload["final_answer"], solves,
                                      attribute=[candidate])
            if outcome["normal_form"]:
                candidate.payload["sympy_normal_form"] = outcome["normal_form"]
            candidate.panel = outcome
            verified = outcome["agree"] >= pf.min_agreeing_solves
            self.ctx.caller.ledger(
                task="reference_verified", left_kind="pf_candidate", left_id=candidate.id,
                judge="verifier", prompt_version=C.EQUIVALENCE_PROMPT, input_hash=candidate.content_hash,
                verdict="pass" if verified else "fail",
                score=outcome["agree"] / outcome["total"] if outcome["total"] else 0.0,
                rationale={"check": "panel_agreement" + ("+sympy" if outcome["sympy_checked"] else ""),
                           "agree": outcome["agree"], "total": outcome["total"],
                           "min_agreeing_solves": pf.min_agreeing_solves},
            )
            if not verified:
                self._reject(candidate, "solve_first_agreement",
                             {"agree": outcome["agree"], "total": outcome["total"]})
                continue
            candidate.verification = "verified"
            candidate.verification_check = "panel_agreement" + ("+sympy" if outcome["sympy_checked"] else "")
            self._pass(candidate, "solve_first_agreement", {"agree": outcome["agree"], "total": outcome["total"]})
            self._set_difficulty(candidate, outcome["agree"], outcome["total"])
            self._pass(candidate, "solver_panel_outlier")
            self._persist(candidate)

    def _panel_generator(self) -> None:
        """Generator draws are CAS-verified; the panel sets difficulty and finds outliers."""
        alive = [candidate for candidate in self.candidates if candidate.alive]
        if not alive or self.program is None:
            return
        k = self.ctx.vault.config.pf.panel_solves_per_model
        solves_by_candidate = {candidate.id: self._panel_solves(candidate.payload["stem"], solves_per_model=k,
                                                                attribute=[candidate])
                               for candidate in alive}
        pairs = [{"draw": {key: candidate.payload.get(key) for key in (
                    "parameters", "stem", "solution", "final_answer", "checkpoints")},
                  "answer": solve["final_answer"]}
                 for candidate in alive for solve in solves_by_candidate[candidate.id]]
        sandbox = check_generator_answers(self.program["program"], pairs, limits=self.ctx.limits)
        checks = list((sandbox.output or {}).get("checks") or []) if sandbox.ok else [None] * len(pairs)
        position = 0
        for candidate in alive:
            solves = solves_by_candidate[candidate.id]
            results = checks[position:position + len(solves)]
            position += len(solves)
            agree = sum(1 for value in results if value is True)
            for solve, value in zip(solves, results):
                self.ctx.caller.ledger(
                    task="answer_equivalence", left_kind="pf_candidate", left_id=candidate.id,
                    judge="verifier", prompt_version=GENERATOR_PROTOCOL,
                    input_hash=content_key([candidate.content_hash, solve["input_hash"]]),
                    verdict={True: "agree", False: "disagree", None: "error"}[value],
                    rationale={"solve_model": solve["model"], "solve_index": solve["index"],
                               "program_hash": self.program["hash"]},
                )
            candidate.panel = {"agree": agree, "total": len(solves), "check": "generator_program",
                               "per_solve": [{"model": s["model"], "agree": v is True}
                                             for s, v in zip(solves, results)]}
            if agree == 0:
                # Outlier: no panel solve reaches the CAS-verified answer, so the
                # draw is likely ill-posed or far off the family's difficulty.
                self._reject(candidate, "solver_panel_outlier", {"agree": 0, "total": len(solves)})
                continue
            self._pass(candidate, "solver_panel_outlier", {"agree": agree, "total": len(solves)})
            self._set_difficulty(candidate, agree, len(solves))
            self._persist(candidate)

    # structure check
    def _structure(self) -> None:
        alive = [candidate for candidate in self.candidates if candidate.alive]
        if not alive:
            return
        # Programs guarantee invariance across draws; one representative check
        # confirms the program's structure and rubric applicability.
        targets = alive[:1] if self.path == "generator" else alive
        entry = self.ctx.role("structure")[0]
        verdicts: dict[str, Any] = {}
        parent_context = {**_item_context(self.parent, self.ctx.vault), "skeleton": self.parent_skeleton}
        for candidate in targets:
            call = self._call(
                entry, attribute=[candidate], prompt=C.structure_prompt(
                    parent=parent_context,
                    candidate={"stem": candidate.payload["stem"], "solution": candidate.payload["solution"],
                               "final_answer": candidate.payload["final_answer"],
                               "techniques": candidate.payload.get("techniques"),
                               "checkpoints": candidate.payload.get("checkpoints")},
                    declared_relation=candidate.declared_relation),
                prompt_version=C.STRUCTURE_PROMPT, result_model=C.StructureVerdict,
            )
            verdicts[candidate.id] = (call, call.result)
            self.ctx.caller.ledger(
                task="isomorph", left_kind="pf_candidate", left_id=candidate.id,
                right_kind="practice_item", right_id=self.parent.id, judge="llm",
                judge_model=call.model, prompt_version=C.STRUCTURE_PROMPT, input_hash=call.input_hash,
                verdict=call.result.relation,
                rationale={"declared": candidate.declared_relation,
                           "checkpoint_sequence_preserved": call.result.checkpoint_sequence_preserved,
                           "rubric_applies_verbatim": call.result.rubric_applies_verbatim,
                           "rationale": call.result.rationale},
            )
        for candidate in alive:
            call, verdict = verdicts.get(candidate.id) or verdicts[targets[0].id]
            detail = {"judged_relation": verdict.relation, "model": call.model,
                      "checkpoint_sequence_preserved": verdict.checkpoint_sequence_preserved,
                      "rubric_applies_verbatim": verdict.rubric_applies_verbatim}
            if verdict.relation == "reject" or not verdict.rubric_applies_verbatim:
                self._reject(candidate, "structure_check", detail)
                continue
            judged = verdict.relation
            if judged in TRACE_RELATIONS and not verdict.checkpoint_sequence_preserved:
                # The checkpoint sequence differs, so the candidate is at most
                # near, whatever relation the judge named (§5.3 step 3).
                judged = "near"
                detail["checkpoints_differ"] = True
            if candidate.declared_relation == "isomorph" and judged != "isomorph":
                # A declared isomorph without a passing structure check is
                # never published as an isomorph: relabel near, or reject.
                if judged in {"near", "far"} and self.path != "generator":
                    candidate.final_relation = judged
                    detail["relabelled"] = judged
                else:
                    self._reject(candidate, "structure_check", detail)
                    continue
            else:
                candidate.final_relation = (
                    candidate.declared_relation if candidate.declared_relation in {"near", "far"}
                    and judged in {"near", "far"} else judged)
            self._pass(candidate, "structure_check", detail)
            self._persist(candidate)

    @staticmethod
    def _structure_confirms(candidate: Candidate) -> bool:
        """A passing checkpoint-preservation check: the only way to a final isomorph."""
        detail = (candidate.filters.get("structure_check") or {}).get("detail") or {}
        return bool(candidate.filters.get("structure_check", {}).get("passed")
                    and detail.get("judged_relation") in TRACE_RELATIONS
                    and detail.get("checkpoint_sequence_preserved") is True)

    # freshness
    def _freshness(self) -> None:
        alive = [candidate for candidate in self.candidates if candidate.alive]
        if not alive:
            return
        items = self._lo_items()
        lo_keys = self._lo_keys()
        exhaustive = len(items) <= self.ctx.vault.config.families.max_exhaustive_items
        top_k = self.ctx.vault.config.pf.freshness_top_k
        entry = self.ctx.role("freshness")[0]
        administered = self._administered({item.id for item in items})
        for candidate in alive:
            keys = self._candidate_keys(candidate)
            suspects = {item_id for item_id, item_keys in lo_keys.items() if shared_keys(keys, item_keys)}
            if exhaustive:
                chosen = [item.id for item in items]
                basis = "exhaustive_lo"
            else:
                # Large LO: suspects by exact symbolic keys always reach the judge;
                # lexical top-k blocks the rest until B2 sets embedding cutoffs.
                ranked = sorted(items, key=lambda item: (-similarity(candidate.payload["stem"], item.prompt), item.id))
                chosen = sorted(suspects | {self.parent.id} | {item.id for item in ranked[:top_k]})
                basis = "suspects_plus_lexical_top_k"
            refs = {f"item_{index}": item_id for index, item_id in enumerate(chosen)}
            comparisons = [{"ref": ref, "prompt": self.ctx.vault.practice_items[item_id].prompt,
                            "is_parent": item_id == self.parent.id}
                           for ref, item_id in refs.items()]
            call = self._call(
                entry, attribute=[candidate], prompt=C.freshness_prompt(
                    candidate={"stem": candidate.payload["stem"],
                               "final_answer": candidate.payload["final_answer"],
                               "relation": candidate.final_relation or candidate.declared_relation},
                    comparisons=comparisons),
                prompt_version=C.FRESHNESS_PROMPT, result_model=C.FreshnessVerdict,
                pairs=len(comparisons),
            )
            verdicts = {comparison.ref: comparison.verdict for comparison in call.result.comparisons
                        if comparison.ref in refs}
            same_surface = []
            for ref, item_id in refs.items():
                verdict = verdicts.get(ref, "missing")
                self.ctx.caller.ledger(
                    task="isomorph", left_kind="pf_candidate", left_id=candidate.id,
                    right_kind="practice_item", right_id=item_id, judge="llm", judge_model=call.model,
                    prompt_version=C.FRESHNESS_PROMPT, input_hash=call.input_hash, verdict=verdict,
                    rationale={"suspect_keys": item_id in suspects, "administered": item_id in administered,
                               "basis": basis},
                )
                if verdict == "same_surface":
                    same_surface.append(item_id)
            missing = [ref for ref in refs if ref not in verdicts]
            relation = candidate.final_relation or candidate.declared_relation
            detail = {"compared": len(refs), "basis": basis, "suspects": len(suspects),
                      "same_surface": same_surface, "missing_verdicts": len(missing), "model": call.model}
            if missing:
                # Silence is not freshness: an unjudged pair blocks.
                self._reject(candidate, "freshness", detail)
                continue
            if same_surface and relation in {"same_target", "isomorph"}:
                self._reject(candidate, "freshness", detail)
                continue
            parent_ref = next((ref for ref, item_id in refs.items() if item_id == self.parent.id), None)
            if relation in {"near", "far"} and parent_ref and verdicts.get(parent_ref) == "isomorph":
                # The freshness judge alone never makes an isomorph: the mandatory
                # structure check must have confirmed the checkpoint sequence.
                if self._structure_confirms(candidate):
                    candidate.final_relation = "isomorph"
                    detail["relabelled"] = "isomorph"
                else:
                    detail["isomorph_relabel_refused"] = "no passing checkpoint-preservation check"
            if (candidate.final_relation or candidate.declared_relation) in TRACE_RELATIONS \
                    and not self._structure_confirms(candidate):
                raise AssertionError("a final isomorph/same_target needs a passing structure check")
            self._pass(candidate, "freshness", detail)
            self._persist(candidate)

    def _administered(self, item_ids: set[str]) -> set[str]:
        if not item_ids:
            return set()
        placeholders = ",".join("?" for _ in item_ids)
        with self.ctx.repository.connection() as connection:
            rows = connection.execute(
                f"SELECT DISTINCT practice_item_id FROM practice_attempts WHERE practice_item_id IN ({placeholders})",
                tuple(sorted(item_ids)),
            ).fetchall()
        return {row[0] for row in rows}

    # selection
    def _select(self) -> None:
        survivors = [candidate for candidate in self.candidates if candidate.status == "survivor"]
        if not survivors:
            return
        history = [item.prompt for item in self._lo_items()]
        order = mmr_order(
            [(c.id, (c.panel.get("agree", 1) / c.panel["total"]) if c.panel.get("total") else 1.0,
              c.payload["stem"]) for c in survivors], history,
        )
        stems = [candidate.payload["stem"] for candidate in survivors]
        contributions = dict(zip([c.id for c in survivors], vendi_contributions(stems)))
        set_vendi = vendi_score(stems)
        by_id = {candidate.id: candidate for candidate in survivors}
        for rank, entry in enumerate(order):
            by_id[entry["ref"]].selection = {
                **entry, "mmr_rank": rank, "vendi_contribution": contributions[entry["ref"]],
                "set_vendi": round(set_vendi, 6), "diversity_basis": DIVERSITY_BASIS,
            }
        if self.path == "ensemble":
            # The judge is offered verified survivors only; it never decides correctness.
            offered = [by_id[entry["ref"]] for entry in order]
            if any(candidate.verification != "verified" for candidate in offered):
                raise AssertionError("selection judge offered an unverified candidate")
            refs = {f"c{index}": candidate.id for index, candidate in enumerate(offered)}
            survivors_context = [{
                "ref": ref, "stem": by_id[cid].payload["stem"],
                "relation": by_id[cid].final_relation, "difficulty": by_id[cid].difficulty,
                "verification": by_id[cid].verification_check,
                "mmr_score": by_id[cid].selection["mmr_score"],
                "vendi_contribution": by_id[cid].selection["vendi_contribution"],
            } for ref, cid in refs.items()]
            entry = self.ctx.role("selection")[0]
            call = self._call(
                entry, attribute=offered, prompt=C.selection_prompt(family=_family_context(self.family),
                                                 survivors=survivors_context, slots=self.slots),
                prompt_version=C.SELECTION_PROMPT, result_model=C.SelectionVerdict,
            )
            chosen = [refs[ref] for ref in dict.fromkeys(call.result.selected) if ref in refs][:self.slots]
            ranking = [refs[ref] for ref in dict.fromkeys(call.result.ranking) if ref in refs]
            for ref, cid in refs.items():
                rank = ranking.index(cid) if cid in ranking else None
                self.ctx.caller.ledger(
                    task="selection", left_kind="pf_candidate", left_id=cid, judge="llm",
                    judge_model=call.model, prompt_version=C.SELECTION_PROMPT, input_hash=call.input_hash,
                    verdict="selected" if cid in chosen else "not_selected",
                    score=float(rank) if rank is not None else None,
                    rationale={"slots": self.slots, "offered": len(refs)},
                )
                by_id[cid].selection["judge_rank"] = rank
                by_id[cid].selection["judge_model"] = call.model
        else:
            chosen = [entry["ref"] for entry in order[:self.slots]]
            # Deterministic selection is a verdict too (§5.8): ledgered with its policy and input.
            selection_input = content_key([MMR_SELECTION_POLICY, DIVERSITY_BASIS, self.slots,
                                           [[entry["ref"], entry.get("mmr_score")] for entry in order]])
            for rank, entry in enumerate(order):
                self.ctx.caller.ledger(
                    task="selection", left_kind="pf_candidate", left_id=entry["ref"], judge="verifier",
                    prompt_version=MMR_SELECTION_POLICY, input_hash=selection_input,
                    verdict="selected" if entry["ref"] in chosen else "not_selected", score=float(rank),
                    rationale={"slots": self.slots, "offered": len(order), "basis": DIVERSITY_BASIS},
                )
        self.selected_order = chosen
        # Review F22: the complete selected order and its completion marker
        # are persisted with every survivor's status in ONE transaction, so a
        # rerun never mistakes a partly persisted selection for a finished one.
        for candidate in survivors:
            candidate.status = "selected" if candidate.id in chosen else "not_selected"
            candidate.selection = {**candidate.selection, SELECTION_ORDER_KEY: list(chosen),
                                   SELECTION_COMPLETE_KEY: True}
        self._persist_all(survivors)

    def _judge_required_method(self) -> None:
        """The one-time publication judgment of each selected variant of a parent
        with a required method (redesign 2026-10-14; review F10): does its stem
        prohibit or contradict the method? Recorded once in ``judgment_ledger``
        whether or not the candidate is published today, so publication (now
        or from the backlog, which makes no model call) reads the verdict and
        refuses a contradicting stem before anything is appended.

        Review F17: a spend refusal or a cancellation propagates (the run
        releases the job, resumable); any other failure, or no judge ready,
        raises :class:`RequiredMethodJudgmentIncomplete` once every selected
        variant has been tried, so the job stays retryable until each has a
        verdict."""
        order = getattr(self, "selected_order", [])
        method = getattr(self.parent, "required_method", None)
        if method is None or not order:
            return
        tally: Counter = Counter()
        failures: Counter = Counter()
        for candidate_id in order:
            with self.ctx.repository.connection() as connection:
                row = store.candidate(connection, candidate_id)
            if row is None:
                continue
            try:
                verdict = judge_variant_stem(self.ctx.vault, self.ctx.repository, row, self.ctx.method_judge(),
                                             owner=(self.ctx.caller.owner_kind, self.ctx.caller.run_id),
                                             clock=self.ctx.clock, strict=True)
            except (AIInterrupted, SpendLimitExceeded):
                raise
            except Exception as exc:  # noqa: BLE001 - no verdict yet; the job stays retryable
                _LOGGER.warning("the required-method publication judgment failed for %s", candidate_id,
                                exc_info=True)
                failures[type(exc).__name__] += 1
                verdict = None
            tally[verdict or "unjudged"] += 1
        self.report["required_method_judgments"] = dict(sorted(tally.items()))
        if failures:
            self.report["required_method_judgment_failures"] = dict(sorted(failures.items()))
        if tally.get("unjudged"):
            reason = (f"{tally['unjudged']} selected variant(s) have no required-method verdict ("
                      + (", ".join(f"{name} x{count}" for name, count in sorted(failures.items())) if failures
                         else "no judge is ready")
                      + "); rerun this round to judge them")
            raise RequiredMethodJudgmentIncomplete(reason)

    def _publish(self) -> None:
        order = getattr(self, "selected_order", [])
        if not order:
            return
        vault, outcome = publish_selected(self.ctx.vault, self.ctx.repository, order, clock=self.ctx.clock)
        self.ctx.vault = vault
        self.ctx.caller.vault = vault
        self.report.update(published_item_ids=outcome["published_item_ids"],
                           capped=outcome["capped_candidates"], stale=outcome["stale_candidates"],
                           refused=outcome["refused_candidates"], unjudged=outcome["unjudged_candidates"])
        for candidate in self.candidates:
            if candidate.id in order:
                with self.ctx.repository.connection() as connection:
                    stored = store.candidate(connection, candidate.id)
                candidate.status = stored["status"] if stored else candidate.status

    def _summarize(self) -> None:
        statuses = Counter(candidate.status for candidate in self.candidates)
        rejected = Counter(candidate.rejection_filter for candidate in self.candidates if candidate.rejection_filter)
        survival = {}
        remaining = len(self.candidates)
        for name in FILTER_ORDER:
            failed = rejected.get(name, 0)
            evaluated = sum(1 for candidate in self.candidates if name in candidate.filters)
            survival[name] = {"evaluated": evaluated, "rejected": failed}
            remaining -= failed
        attempted = [c for c in self.candidates if c.panel.get("total")]
        disagree = sum(1 for c in attempted if c.panel.get("agree", 0) < self.ctx.vault.config.pf.min_agreeing_solves)
        self.report.update(
            candidates=len(self.candidates), by_status=dict(statuses), rejected_by_filter=dict(rejected),
            survival_by_filter=survival, survivors_after_filters=remaining,
            verified=sum(1 for c in self.candidates if c.verification == "verified"),
            selected=statuses.get("selected", 0),
            panel_disagreement_rate=(disagree / len(attempted)) if attempted else None,
            proposer_models=sorted({c.proposer_model for c in self.candidates if c.proposer_model}),
            notes=self.notes,
        )


# -- planning and the command entry -------------------------------------------------

def _job_angle(family_id: str, path: str, relation: str, round_id: str, tier: str | None,
               count: int) -> dict[str, Any]:
    """A family job's requested angle: its mint request's identity (with the
    parent's card version) and its generation seed."""
    return {"family_id": family_id, "path": path, "relation": relation, "round": round_id, "tier": tier,
            "count": count}


def _resumable_job(vault: LoadedVault, repository: Repository, family: ActivityFamily, parent: PracticeItem,
                   path: str, options: GenerationOptions, round_id: str, now_iso: str) -> dict[str, Any] | None:
    """A job of this round whose selection already started, read-only (round 3, F17/F20/F22).

    Detected BEFORE any route is resolved or any budget planned, so a rerun
    is planned and admitted as its unfinished work only: the claimable
    (``pending`` or ``failed``, or ``running`` under an expired lease) mint
    request of the same angle whose candidates were judged against the
    parent and family as they are now (:func:`~learnloop.ops.pf_publish.
    stale_inputs`), with a selection (:func:`selection_state`). Returns its
    request id, stage and selected order, or None (the job runs the
    pipeline, as planned by :func:`_plan_family`).
    """
    if path == "single_shot" or family.id.startswith("(seed:") or not repository.sqlite_path.exists():
        return None
    count = options.count or vault.config.pf.candidates_per_family
    relation = "isomorph" if path == "generator" else options.relation
    angle = json.dumps(_job_angle(family.id, path, relation, round_id, options.tier, count),
                       sort_keys=True, separators=(",", ":"))
    with repository.connection() as connection:
        tables = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('pf_candidates', 'surface_mint_requests')")}
        if tables != {"pf_candidates", "surface_mint_requests"}:
            return None
        requests = [row[0] for row in connection.execute(
            "SELECT id FROM surface_mint_requests WHERE requested_angle_json = ? AND generator_version = ? "
            "AND gate_policy_version = ? AND (status IN ('pending', 'failed') OR (status = 'running' "
            "AND (lease_expires_at IS NULL OR lease_expires_at < ?))) ORDER BY created_at DESC, id DESC",
            (angle, GENERATOR_VERSIONS[path], GATE_POLICY_VERSION, now_iso))]
        for request_id in requests:
            rows = store.candidates(connection, where="mint_request_id=? AND parent_item_id=?",
                                    params=(request_id, parent.id))
            if not rows or any(stale_inputs(vault, row) for row in rows):
                continue
            state = selection_state(rows)
            if state is None:
                continue
            method = getattr(parent, "required_method", None)

            def unjudged(row: Mapping[str, Any], stem: str) -> bool:
                return method is not None and recorded_verdict(
                    connection, question="variant", subject_kind="pf_candidate", subject_id=str(row["id"]),
                    statement=stem, method=method.name) is None

            # Review F7 (method-explicit-3): the persisted inputs of the
            # unfinished work, so the plan estimates THEM, never the parent's
            # stem in their place: the stems still to be judged and, for a
            # selection to finish, the survivors the selection judge is shown.
            missing_stems: list[str] = []
            if state["stage"] == "judgment" and method is not None:
                by_id = {row["id"]: row for row in rows}
                for candidate_id in state["order"]:
                    row = by_id.get(candidate_id)
                    if row is None or row["status"] != "selected":
                        continue  # published or refused meanwhile: no judgment left to ask
                    stem = str(json.loads(row["payload_json"]).get("stem") or "")
                    if unjudged(row, stem):
                        missing_stems.append(stem)
            survivors = []
            for row in rows:
                if row["status"] not in ("survivor", "selected", "not_selected"):
                    continue
                stem = str(json.loads(row["payload_json"]).get("stem") or "")
                survivors.append({"stem": stem, "relation": row["final_relation"], "difficulty": row["difficulty"],
                                  "verification": row["verification_check"], "unjudged": unjudged(row, stem)})
            return {**state, "mint_request_id": request_id, "survivors": len(survivors),
                    "survivor_inputs": survivors, "missing_judgments": len(missing_stems),
                    "missing_stems": missing_stems}
    return None


def _plan_resume(vault: LoadedVault, family: ActivityFamily, parent: PracticeItem, path: str,
                 options: GenerationOptions, roles: Mapping[str, list[RoleClient]],
                 resume: Mapping[str, Any]) -> dict[str, Any]:
    """The plan of a resumable job: only its unfinished work (round 3, F17/F20/F22).

    At the judgment stage that is each selected variant's missing
    required-method judgment (a judgment already ledgered is reused) and the
    publication (no model call). A selection persisted without its marker is
    finished first: the selection judge's request on the ensemble path, then
    up to one judgment per slot. Nothing upstream (skeleton, generation,
    filters, panel, freshness) runs again.
    """
    pf = vault.config.pf
    slots = options.select or pf.select_per_family
    plan: dict[str, Any] = {
        "family_id": family.id, "parent_item_id": parent.id, "path": path, "candidates": 0, "freshness_pairs": 0,
        "roles": {},
        "resume": {"stage": resume["stage"], "mint_request_id": resume["mint_request_id"],
                   "selected": len(resume.get("order") or ()), "missing_judgments": resume["missing_judgments"]},
    }
    method = getattr(parent, "required_method", None)
    # Review F7 (method-explicit-3): each estimate reads the persisted input
    # it stands for (the stem still to be judged, the survivors the
    # selection judge is shown), never the parent's stem in its place, so a
    # long variant cannot pass admission and then exceed the token cap.
    per_stem = ([planned_tokens("variant", stem, method.name) for stem in resume.get("missing_stems") or ()]
                if method is not None else [])
    if resume["stage"] == "selection":
        survivors = list(resume.get("survivor_inputs") or ())
        # Up to one judgment per slot, of the survivors not judged yet: the
        # largest ESTIMATES (re-review F9; an estimate grows with the stem's
        # UTF-8 bytes, not its characters), an upper bound whichever the
        # selection chooses.
        per_stem = sorted((planned_tokens("variant", entry["stem"], method.name)
                           for entry in survivors if entry.get("unjudged")),
                          reverse=True)[:slots] if method is not None else []
        if path == "ensemble":
            entries = roles["selection"]
            context = [{
                "ref": f"c{index}", "stem": entry["stem"], "relation": entry.get("relation"),
                "difficulty": entry.get("difficulty"), "verification": entry.get("verification"),
                # The selection's own scores, as wide as the run writes them.
                "mmr_score": 0.123456, "vendi_contribution": 0.123456,
            } for index, entry in enumerate(survivors)] or [{"ref": "c0", "stem": parent.prompt}]
            prompt = C.selection_prompt(family=_family_context(family), survivors=context, slots=slots)
            tokens = estimate_tokens(prompt, C.SelectionVerdict, output_budget(
                vault.config, ROLE_TASKS["selection"], provider=entries[0].provider if entries else None))
            plan["roles"]["selection"] = {
                "calls": 1, "tokens": tokens, "providers": [entry.provider for entry in entries],
                "models": [entry.model for entry in entries],
                "subscription": [entry.subscription for entry in entries], "per_call_tokens": tokens,
                "per_entry": 1,
            }
    if per_stem:
        plan["required_method_judgment"] = {
            "calls": len(per_stem), "tokens": sum(per_stem), "per_call_tokens": max(per_stem),
            "judge": "the Decider via ai.routing.rubric_phrasing_judge, else the LLM judge on it",
            "billing": "metered (upper bound)",
        }
    return plan


def _tier_routes(vault: LoadedVault, tier: str | None) -> list[str] | None:
    if tier is None:
        return None
    routes = list(getattr(vault.config.pf.scaling, tier, []) or [])
    if not routes:
        raise ValueError(f"pf.scaling.{tier} names no routes; configure the tier's profiles first")
    return routes


def _plan_family(vault: LoadedVault, family: ActivityFamily, parent: PracticeItem, path: str,
                 options: GenerationOptions, roles: Mapping[str, list[RoleClient]],
                 repository: Repository | None) -> dict[str, Any]:
    pf = vault.config.pf
    n = options.count or pf.candidates_per_family
    k = pf.panel_solves_per_model
    panel = len(roles["panel"])
    lo_items = sum(1 for item in vault.practice_items.values() if item.learning_object_id == parent.learning_object_id)
    compare = lo_items if lo_items <= vault.config.families.max_exhaustive_items else min(lo_items, pf.freshness_top_k + 2)
    context = _item_context(parent, vault)
    stem_proxy = parent.prompt
    prompts = {
        "skeleton": C.skeleton_prompt(prompt=parent.prompt, expected_answer=parent.expected_answer),
        "program": C.generator_program_prompt(parent=context, family=_family_context(family), skeleton={},
                                              relation="isomorph", previous_failure=None),
        "proposer": C.proposer_prompt(parent=context, family=_family_context(family), skeleton={},
                                      relation=options.relation, count=n, generation_seed="0" * 16),
        "panel": C.panel_solve_prompt(stem=stem_proxy, solve_index=0),
        "equivalence": C.equivalence_prompt(stem=stem_proxy, reference=final_answer_text(parent.expected_answer),
                                            answers=["x"] * (panel * k)),
        "structure": C.structure_prompt(parent={**context, "skeleton": {}}, candidate={"stem": stem_proxy},
                                        declared_relation=options.relation),
        "freshness": C.freshness_prompt(candidate={"stem": stem_proxy},
                                        comparisons=[{"ref": "item_0", "prompt": stem_proxy}] * max(1, compare)),
        "selection": C.selection_prompt(family=_family_context(family),
                                        survivors=[{"ref": "c0", "stem": stem_proxy}] * n, slots=pf.select_per_family),
        "source": C.source_anchored_prompt(passages=[{"ref": "s0", "text": stem_proxy * 4}] * 6,
                                           parent=context, family=_family_context(family), count=n,
                                           generation_seed="0" * 16),
        "closed_book": C.closed_book_prompt(stem=stem_proxy),
        "span_support": C.span_support_prompt(question=stem_proxy, cited_span=stem_proxy * 4,
                                              reference_answer=stem_proxy, explanation=stem_proxy * 2,
                                              item_kind="what"),
    }
    models = {"skeleton": C.SkeletonResult, "program": C.GeneratorProgramResult, "proposer": C.ProposalBatch,
              "panel": C.PanelSolve, "equivalence": C.EquivalenceResult, "structure": C.StructureVerdict,
              "freshness": C.FreshnessVerdict, "selection": C.SelectionVerdict,
              "source": C.SourceAnchoredBatch, "closed_book": C.PanelSolve,
              "span_support": C.SpanSupportVerdict}
    calls = {"skeleton": 1, "panel": (n + 1) * panel * k, "structure": 1 if path == "generator" else n,
             "freshness": n}
    if path == "generator":
        calls["program"] = 1
        calls["equivalence"] = 1
    elif path == "source_anchored":
        calls.pop("panel")
        calls.update(source=1, span_support=n, closed_book=n, equivalence=n)
    else:
        role = "single_shot" if path == "single_shot" else "proposer"
        calls[role] = 1 if path == "single_shot" else len(roles["proposer"])
        calls["equivalence"] = n + 1
        if path == "ensemble":
            calls["selection"] = 1
    plan: dict[str, Any] = {"family_id": family.id, "parent_item_id": parent.id, "path": path,
                            "candidates": n, "freshness_pairs": n * max(1, compare), "roles": {}}
    for role, count in calls.items():
        prompt_role = "proposer" if role == "single_shot" else role
        entries = roles[role]
        tokens = estimate_tokens(prompts[prompt_role], models[prompt_role], output_budget(
            vault.config, ROLE_TASKS[role], provider=entries[0].provider if entries else None))
        per_entry = count if role in {"panel", "proposer"} else count
        plan["roles"][role] = {
            "calls": count, "tokens": tokens * count,
            "providers": [entry.provider for entry in entries],
            "models": [entry.model for entry in entries],
            "subscription": [entry.subscription for entry in entries],
            "per_call_tokens": tokens, "per_entry": per_entry,
        }
    method = getattr(parent, "required_method", None)
    if method is not None and path != "single_shot":
        # The one-time publication judgment of each selected variant
        # (redesign 2026-10-14): the Decider via ai.routing.rubric_phrasing_judge,
        # else the LLM judge; an upper bound, counted as metered.
        slots = options.select or pf.select_per_family
        per_call = planned_tokens("variant", stem_proxy, method.name)
        plan["required_method_judgment"] = {
            "calls": slots, "tokens": per_call * slots, "per_call_tokens": per_call,
            "judge": "the Decider via ai.routing.rubric_phrasing_judge, else the LLM judge on it",
            "billing": "metered (upper bound)",
        }
    return plan


def _plan_estimates(plans: list[dict[str, Any]], caller: PFCaller,
                    roles: Mapping[str, list[RoleClient]]) -> tuple[SpendEstimate, SpendEstimate]:
    totals = {True: {"calls": 0, "tokens": 0}, False: {"calls": 0, "tokens": 0}}
    candidates = pairs = 0
    for plan in plans:
        candidates += plan["candidates"]
        pairs += plan["freshness_pairs"]
        for role, info in plan["roles"].items():
            entries = roles[role]
            if role == "panel":
                # Calls split evenly across panel members.
                share = info["calls"] // max(1, len(entries))
                for entry in entries:
                    totals[entry.subscription]["calls"] += share
                    totals[entry.subscription]["tokens"] += share * info["per_call_tokens"]
            elif role == "proposer":
                for entry in entries:
                    totals[entry.subscription]["calls"] += 1
                    totals[entry.subscription]["tokens"] += info["per_call_tokens"]
            else:
                entry = entries[0]
                totals[entry.subscription]["calls"] += info["calls"]
                totals[entry.subscription]["tokens"] += info["tokens"]
        judgment = plan.get("required_method_judgment")
        if judgment:
            totals[False]["calls"] += judgment["calls"]
            totals[False]["tokens"] += judgment["tokens"]
    metered = caller.estimate(totals[False]["tokens"], subscription=False, calls=totals[False]["calls"])
    subscription = caller.estimate(totals[True]["tokens"], subscription=True, calls=totals[True]["calls"])
    metered = SpendEstimate(candidates=candidates, pairs=pairs, calls=metered.calls,
                            total_tokens=metered.total_tokens, estimated_usd=metered.estimated_usd)
    return metered, subscription


def _seed_families(vault: LoadedVault, repository: Repository, seed_items: tuple[str, ...],
                   clock: Clock | None) -> LoadedVault:
    """Owner-requested single-item families (an authored record; P12)."""
    for item_id in seed_items:
        item = vault.practice_items.get(item_id)
        if item is None:
            raise ValueError(f"Unknown seed item {item_id}")
        if item.family_id:
            continue
        lo = vault.learning_objects[item.learning_object_id]
        identity = content_key(["pf_seed", item_id])
        family = ActivityFamily(
            id="af_pf_seed_" + identity[:24], learning_object_id=item.learning_object_id,
            idea_statement=f"{lo.title}: the idea practised by {item_id}",
            retrieval_target="The complete solution of the seed item, from setup to final answer.",
            source_kind="authored", created_at=utc_now_iso(clock), updated_at=utc_now_iso(clock),
            provenance={"origin": "human", "source_refs": [
                {"ref_type": "existing_entity", "ref_id": item_id, "locator": "pf_generate --seed-item"}]},
        )
        apply_family(vault, repository, family, {item_id: "same_target"}, proposal_id="pfseed_" + identity,
                     judge="owner", rationale="Owner seeded a practice family for PF generation.", clock=clock)
        vault = load_vault(vault.root)
    return vault


def generate_practice(
    vault: LoadedVault, *, caps: SpendCaps, options: GenerationOptions = GenerationOptions(),
    dry_run: bool = False, price_per_million: float | None = None,
    cancelled: Callable[[], bool] | None = None, clients: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Plan (and unless ``dry_run``, run) PF-b generation; aggregate-only report."""
    if price_per_million is not None and (not math.isfinite(price_per_million) or price_per_million <= 0):
        raise ValueError("price_per_million must be finite and positive")
    if options.path not in (*PATHS, "auto"):
        raise ValueError(f"Unknown path {options.path!r}")
    if options.relation not in RELATIONS:
        raise ValueError(f"Unknown relation {options.relation!r}")
    if options.tier not in (None, "cheap", "frontier"):
        raise ValueError("tier must be cheap or frontier")
    round_id = options.round or datetime.now(timezone.utc).date().isoformat()
    tier_routes = _tier_routes(vault, options.tier)
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    # A dry run never migrates or writes: attach read-only to what exists.
    repository = (Repository.attach(sqlite_path, read_only=True) if dry_run else Repository(sqlite_path))
    run_id = new_ulid()
    caller = PFCaller(vault, repository, caps=caps, price_per_million=price_per_million,
                      run_id=run_id, cancelled=cancelled)
    report: dict[str, Any] = {
        "status": "dry_run" if dry_run else "pending", "dry_run": dry_run, "run_id": run_id,
        "round": round_id, "tier": options.tier, "generation_enabled": vault.config.pf.generation_enabled,
        "sandbox_available": sandbox_available(), "caps": caps.as_dict(),
        "price_per_million": price_per_million,
        "price_source": "owner_override" if price_per_million is not None else "unknown",
        "publish": options.publish, "max_published_per_day": vault.config.pf.max_published_per_day,
        "families": [], "manifest": {
            "algorithm_version": vault.config.algorithms.algorithm_version,
            "config_hash": content_key(vault.config.model_dump(mode="json")),
            "prompt_versions": sorted({C.SKELETON_PROMPT, C.GENERATOR_PROGRAM_PROMPT, C.PROPOSER_PROMPT,
                                       C.SINGLE_SHOT_PROMPT, C.PANEL_SOLVE_PROMPT, C.EQUIVALENCE_PROMPT,
                                       C.STRUCTURE_PROMPT, C.FRESHNESS_PROMPT, C.SELECTION_PROMPT,
                                       C.SOURCE_ANCHORED_PROMPT, C.CLOSED_BOOK_PROMPT,
                                       C.SPAN_SUPPORT_PROMPT}),
            "gate_policy_version": GATE_POLICY_VERSION, "diversity_basis": DIVERSITY_BASIS,
            "panel_solves_per_model": vault.config.pf.panel_solves_per_model,
            "min_agreeing_solves": vault.config.pf.min_agreeing_solves,
        },
    }
    if not dry_run and not vault.config.pf.generation_enabled:
        report.update(status="disabled", reason="pf.generation_enabled is off (the PF-b kill switch)")
        return report
    if not report["sandbox_available"]:
        report.update(status="sandbox_unavailable",
                      reason="PF generation requires bubblewrap and fails closed without it")
        return report
    # Plan seeded families with placeholders: nothing is written until the
    # routes resolve and the whole plan is admitted under the caps.
    unknown_seeds = [item_id for item_id in options.seed_items if item_id not in vault.practice_items]
    if unknown_seeds:
        raise ValueError(f"Unknown seed items: {', '.join(unknown_seeds)}")
    report["seed_items"] = list(options.seed_items)
    targets = family_targets(vault, options)
    for item_id in options.seed_items:
        item = vault.practice_items[item_id]
        if not item.family_id:
            placeholder = ActivityFamily(
                id=f"(seed:{item.id})", learning_object_id=item.learning_object_id,
                idea_statement="seed", retrieval_target="seed", created_at="", updated_at="")
            targets.append((placeholder, item))
    paths = {family.id: _resolve_path(vault, family, options.path) for family, _ in targets}
    # Round 3 (F17/F20/F22): a job of this round left retryable after its
    # selection started is found BEFORE any route is resolved or budget
    # planned, and planned as its unfinished work only (a missing judgment
    # alone fits max_calls = 1); only the other jobs need the pipeline's routes.
    now_iso = utc_now_iso(clock)
    resumable = {
        family.id: state for family, parent in targets
        if (state := _resumable_job(vault, repository, family, parent, paths[family.id], options, round_id,
                                    now_iso)) is not None
    }
    if resumable:
        report["resumable"] = {family_id: {key: state[key] for key in ("stage", "mint_request_id",
                                                                       "missing_judgments")}
                               for family_id, state in resumable.items()}
    fresh_paths = {family_id: path for family_id, path in paths.items() if family_id not in resumable}
    used_roles = {"skeleton", "panel", "structure", "freshness"} if fresh_paths else set()
    if "generator" in fresh_paths.values():
        used_roles |= {"program", "equivalence"}
    if "ensemble" in fresh_paths.values():
        used_roles |= {"proposer", "equivalence", "selection"}
    if "single_shot" in fresh_paths.values():
        used_roles |= {"single_shot", "equivalence"}
    if "source_anchored" in fresh_paths.values():
        used_roles |= {"source", "span_support", "closed_book", "equivalence"}
    if any(state["stage"] == "selection" and paths[family_id] == "ensemble"
           for family_id, state in resumable.items()):
        used_roles.add("selection")
    try:
        if dry_run:
            roles = {role: (resolve_role_clients(vault, role, injected=clients[role])
                            if clients and role in clients
                            else planned_role_clients(vault, role, tier_routes=tier_routes))
                     for role in PLAN_ROLES}
        else:
            roles = {}
            for role in PLAN_ROLES:
                if role in used_roles:
                    roles[role] = resolve_role_clients(vault, role, injected=(clients or {}).get(role),
                                                       tier_routes=tier_routes)
                else:
                    roles[role] = planned_role_clients(vault, role, tier_routes=tier_routes)
    except PFUnavailable as exc:
        report.update(status="unavailable", reason=str(exc))
        return report
    report["routes"] = {role: [{"provider": entry.provider, "model": entry.model,
                                "billing": "subscription" if entry.subscription else "metered"}
                               for entry in entries] for role, entries in roles.items() if role in used_roles}
    if "ensemble" in fresh_paths.values() and len(distinct_models(roles["proposer"])) < 2:
        report.update(status="refused",
                      reason="pf_proposers must name profiles with at least two distinct model slugs")
        return report
    plans = [_plan_resume(vault, family, parent, paths[family.id], options, roles, resumable[family.id])
             if family.id in resumable
             else _plan_family(vault, family, parent, paths[family.id], options, roles, repository)
             for family, parent in targets]
    metered, subscription = _plan_estimates(plans, caller, roles)
    report["plan"] = plans
    report["estimate"] = {"metered": asdict(metered), "subscription": asdict(subscription),
                          "cost_basis": {"metered": "metered_caps", "subscription": "estimated_only"}}
    report["publish_slots_today"] = _publish_slots(vault, repository, clock)
    try:
        caller.check_plan(metered, subscription)
    except SpendLimitExceeded as exc:
        report.update(status="over_budget", reason=str(exc))
        return report
    if dry_run:
        return report
    try:
        require_sandbox()
    except SandboxUnavailable as exc:
        report.update(status="sandbox_unavailable", reason=str(exc))
        return report
    if options.seed_items:
        vault = _seed_families(vault, repository, options.seed_items, clock)
        seeded = tuple(vault.practice_items[item_id].family_id for item_id in options.seed_items)
        if options.family_ids:
            options = replace(options, family_ids=tuple(dict.fromkeys(options.family_ids + seeded)))
        targets = family_targets(vault, options)
        paths = {family.id: paths.get(family.id) or _resolve_path(vault, family, options.path)
                 for family, _parent in targets}
    ctx = _Context(vault, repository, caller, options, round_id, tier_routes, clients, clock)
    ctx._roles.update({role: entries for role, entries in roles.items() if role in used_roles})
    with _run_lock(vault.root):
        try:
            for family, parent in targets:
                run = _FamilyRun(ctx, ctx.vault.activity_families.get(family.id, family),
                                 ctx.vault.practice_items[parent.id], paths[family.id],
                                 planned_resume=resumable.get(family.id))
                try:
                    report["families"].append(run.execute())
                except PFRefused as exc:
                    run._resolve_request("failed", reason="refused")
                    report["families"].append({**run.report, "status": "refused", "reason": str(exc)})
            report["status"] = "complete"
        except (AIInterrupted, KeyboardInterrupt):
            report["status"] = "cancelled"
        except SpendLimitExceeded as exc:
            report.update(status="over_budget", reason=str(exc))
        finally:
            report["usage"] = caller.report()
            report["results_by_model"] = _results_by_model(repository, caller.run_id)
            report["published_item_ids"] = [item for family in report["families"]
                                             for item in family.get("published_item_ids", [])]
    return report


def _publish_slots(vault: LoadedVault, repository: Repository, clock: Clock | None) -> int:
    if not repository.sqlite_path.exists():
        return vault.config.pf.max_published_per_day
    with repository.connection() as connection:
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='pf_candidates'"
        ).fetchone()
    if not exists:
        return vault.config.pf.max_published_per_day
    return remaining_publish_slots(vault, repository, clock)


def _results_by_model(repository: Repository, run_id: str) -> dict[str, Any]:
    """Every PF report splits by model id (Slice 2 §13)."""
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT p.generation_path, p.proposer_model, p.status, COUNT(*) AS n FROM pf_candidates p "
            "WHERE p.run_id=? GROUP BY 1,2,3", (run_id,),
        ).fetchall()
    result: dict[str, dict[str, Any]] = defaultdict(lambda: defaultdict(dict))
    for row in rows:
        result[row["proposer_model"] or "unknown"][row["generation_path"]][row["status"]] = row["n"]
    return {model: {path: dict(statuses) for path, statuses in paths.items()} for model, paths in result.items()}


def publish_backlog(vault: LoadedVault, *, clock: Clock | None = None) -> dict[str, Any]:
    """Publish selected-but-capped candidates under today's cap; no model calls.

    A variant of a parent with a required method is published only with the
    one-time judgment its run recorded at selection (a contradicting stem is
    refused; one with no verdict stays selected, ``unjudged_candidates``)."""
    if not vault.config.pf.generation_enabled:
        return {"status": "disabled", "reason": "pf.generation_enabled is off"}
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    with repository.connection() as connection:
        rows = store.candidates(connection, where="status='selected' AND verification='verified'")
    order = [row["id"] for row in sorted(rows, key=lambda row: (row["created_at"], row["id"]))]
    with _run_lock(vault.root):
        _, outcome = publish_selected(vault, repository, order, clock=clock)
    return {"status": "complete", "pending_selected": len(order), **outcome}


def pf_status(vault: LoadedVault, *, clock: Clock | None = None) -> dict[str, Any]:
    repository = Repository.attach(VaultPaths(vault.root, vault.config).sqlite_path, read_only=True)
    with repository.connection() as connection:
        if not connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='pf_candidates'"
        ).fetchone():
            return {"generation_enabled": vault.config.pf.generation_enabled,
                    "publish_slots_today": vault.config.pf.max_published_per_day,
                    "max_published_per_day": vault.config.pf.max_published_per_day,
                    "candidates": {}, "schema": "pf tables not yet migrated"}
        rows = connection.execute(
            "SELECT generation_path, status, verification, COUNT(*) AS n FROM pf_candidates GROUP BY 1,2,3"
        ).fetchall()
    counts: dict[str, dict[str, int]] = defaultdict(dict)
    for row in rows:
        counts[row["generation_path"]][f"{row['status']}:{row['verification']}"] = row["n"]
    return {"generation_enabled": vault.config.pf.generation_enabled,
            "publish_slots_today": remaining_publish_slots(vault, repository, clock),
            "max_published_per_day": vault.config.pf.max_published_per_day,
            "candidates": {path: dict(values) for path, values in counts.items()}}


__all__ = [
    "FILTER_ORDER", "GATE_POLICY_VERSION", "GENERATOR_VERSIONS", "GenerationOptions",
    "MMR_SELECTION_POLICY", "PATHS",
    "PFRefused", "RequiredMethodJudgmentIncomplete", "family_targets", "generate_practice", "panel_difficulty",
    "pf_run_lock", "pf_status", "publish_backlog",
]
