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
  item carries its counterexample). Why-items without a verified span are
  relabelled ``inferred`` and never published (provenance filter); items whose
  target is source-specific are rejected when a closed-book model answers them
  correctly (closed-book filter). No figure items exist yet (figure-only is not
  applicable) and executable what-if perturbations are not built.
* ``single_shot``: the pilot baseline arm. One call, measured by the same
  verification and filters, never published.

Filters, cheapest first: authoring gates (the shared instrument chain),
held-out leakage, exact-key duplicates, verification, solver-panel outliers,
the structure check and the freshness judge. Difficulty is the solver panel's
per-variant offset from the parent (``difficulty_source = "solver_panel"``);
LLM self-labels are never requested.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Mapping
from contextlib import contextmanager
import copy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterator

from learnloop.ai.errors import AIInterrupted, AIProviderUnavailable
from learnloop.ai.execution import content_key
from learnloop.ai.spend import SpendCaps, SpendEstimate, SpendLimitExceeded
from learnloop.clock import Clock, utc_now_iso
from learnloop.content.authoring import pf_contracts as C
from learnloop.content.authoring.authoring_gates import build_instrument_gates
from learnloop.content.authoring.pf_sandbox import (
    GENERATOR_PROTOCOL, SandboxLimits, SandboxUnavailable, check_generator_answers,
    require_sandbox, run_equivalence_checks, run_generator_tests, sandbox_available,
)
from learnloop.content.authoring.practice_leakage import (
    build_cross_source_spans, build_held_out_inventory, screen_practice_payload,
)
from learnloop.db.repositories import Repository
from learnloop.db.stores import pf as store
from learnloop.ids import new_ulid
from learnloop.ops.pf_calls import (
    PFCaller, PFUnavailable, RoleClient, distinct_models, estimate_tokens, planned_role_clients,
    resolve_role_clients,
)
from learnloop.ops.pf_publish import publish_selected, remaining_publish_slots
from learnloop.ops.pf_selection import DIVERSITY_BASIS, mmr_order, similarity, vendi_contributions, vendi_score
from learnloop.substrate.activities import resolve_legacy_item
from learnloop.substrate.families import apply_family, family_operation_lock, sync_authored_families
from learnloop.substrate.item_fingerprints import (
    EXACT_COMPONENTS, final_answer_text, fingerprint_keys, item_fingerprint_keys,
    published_candidate_payloads, render_expected_answer, shared_keys, skeleton_content_hash,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.models import ActivityFamily, FamilyReference, LoadedVault, PracticeItem
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_activity_family

PATHS = ("generator", "ensemble", "source_anchored", "single_shot")
RELATIONS = ("same_target", "isomorph", "near", "far")
GENERATOR_VERSIONS = {"generator": "pf_generator_v1", "ensemble": "pf_ensemble_v1",
                      "source_anchored": "pf_source_anchored_v1", "single_shot": "pf_single_shot_v1"}
GATE_POLICY_VERSION = "pf_gate_v1"
FILTER_ORDER = (
    "authoring_gates", "held_out_leakage", "exact_duplicate", "execution_cas",
    "solve_first_agreement", "quote_verified_span", "provenance", "closed_book",
    "solver_panel_outlier", "structure_check", "freshness",
)
NOT_APPLICABLE_FILTERS = ("closed_book", "figure_only", "provenance")
OUTPUT_TOKENS = {
    "skeleton": 1200, "program": 6000, "proposer": 8000, "single_shot": 8000, "panel": 1500,
    "equivalence": 2500, "structure": 800, "freshness": 2500, "selection": 1500,
    "source": 8000, "closed_book": 1500,
}
MIN_QUOTE_WORDS = 4
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

    @property
    def alive(self) -> bool:
        return self.status in {"generated", "survivor", "baseline"} and self.rejection_filter is None

    @property
    def expected_answer(self) -> str:
        return render_expected_answer(self.payload["final_answer"], self.payload["solution"])

    @property
    def content_hash(self) -> str:
        return skeleton_content_hash(self.payload["stem"], self.expected_answer)


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
    return {"id": item.id, "prompt": item.prompt, "expected_answer": item.expected_answer,
            "practice_mode": item.practice_mode, "rubric": rubric,
            "trace_contract": item.trace_contract.model_dump(mode="json") if item.trace_contract else None}


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


class _FamilyRun:
    def __init__(self, ctx: _Context, family: ActivityFamily, parent: PracticeItem, path: str) -> None:
        self.ctx = ctx
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
        self.report: dict[str, Any] = {"family_id": family.id, "path": path,
                                       "parent_item_id": parent.id, "declared_relation": self.relation}

    # -- the 078 job ------------------------------------------------------------
    def _enqueue_and_claim(self) -> bool:
        repository = self.ctx.repository
        resolved = resolve_legacy_item(self.ctx.vault, repository, self.parent, purpose="practice",
                                       clock=self.ctx.clock)
        angle = {"family_id": self.family.id, "path": self.path, "relation": self.relation,
                 "round": self.ctx.round, "tier": self.ctx.options.tier, "count": self.count}
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
                    "created_at": now, "updated_at": now,
                })
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
                updated_at=now,
            )

    def _reject(self, candidate: Candidate, filter_name: str, detail: Any = None) -> None:
        candidate.filters[filter_name] = {"passed": False, **({"detail": detail} if detail is not None else {})}
        if candidate.path == "single_shot":
            # The baseline arm is measured, never published; record where it fell.
            candidate.rejection_filter = candidate.rejection_filter or filter_name
        else:
            candidate.status = "rejected"
            candidate.rejection_filter = filter_name
        self._persist(candidate)

    def _pass(self, candidate: Candidate, filter_name: str, detail: Any = None) -> None:
        candidate.filters[filter_name] = {"passed": True, **({"detail": detail} if detail is not None else {})}

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

    # -- stages -------------------------------------------------------------------
    def execute(self) -> dict[str, Any]:
        if not self._enqueue_and_claim():
            return self.report
        try:
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
            self._structure()
            self._freshness()
            for candidate in self.candidates:
                if candidate.alive:
                    for name in NOT_APPLICABLE_FILTERS:
                        candidate.filters.setdefault(name, {"passed": True, "detail": "not_applicable"})
                    if candidate.path != "single_shot":
                        candidate.status = "survivor"
                    self._persist(candidate)
            if self.path != "single_shot":
                self._select()
                if self.ctx.options.publish:
                    self._publish()
            self._summarize()
            selected = self.report.get("selected", 0) + len(self.report.get("published_item_ids", []))
            self._resolve_request("admitted" if selected else "rejected")
            self.report["status"] = "complete"
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
        return self.report

    def _parent_skeleton(self) -> dict[str, Any]:
        entry = self.ctx.role("skeleton")[0]
        call = self.ctx.caller.call(
            entry, prompt=C.skeleton_prompt(prompt=self.parent.prompt, expected_answer=self.parent.expected_answer),
            prompt_version=C.SKELETON_PROMPT, result_model=C.SkeletonResult,
            output_tokens=OUTPUT_TOKENS["skeleton"],
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
            return False, f"import: {output['import_error']}", []
        draws = output.get("draws") or []
        problems = []
        for entry in draws:
            if entry.get("error"):
                problems.append(f"seed {entry.get('seed')}: {entry['error']}")
            elif not entry.get("self_check"):
                problems.append(f"seed {entry['seed']}: check rejects its own final answer")
            elif not entry.get("negative_controls_rejected"):
                problems.append(f"seed {entry['seed']}: check accepts a wrong answer")
            elif entry["draw"]["checkpoints"] != declared:
                problems.append(f"seed {entry['seed']}: checkpoint sequence differs from declared")
        if not problems and len({entry["draw"]["stem"] for entry in draws}) < min(2, len(draws)):
            problems.append("draws do not vary the surface")
        return not problems, "; ".join(problems)[:1500], draws

    def _program(self) -> dict[str, Any] | None:
        test_seeds = list(range(self.ctx.vault.config.pf.generator_test_draws))
        existing = self.family.generator or {}
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
                    parent=_item_context(self.parent, self.ctx.vault), family=_family_context(self.family),
                    skeleton=self.parent_skeleton or {}, relation="isomorph", previous_failure=failure,
                    attempt=attempts),
                prompt_version=C.GENERATOR_PROGRAM_PROMPT, result_model=C.GeneratorProgramResult,
                output_tokens=OUTPUT_TOKENS["program"],
            )
            code = call.result.program
            ok, failure_text, _ = self._program_ok(code, list(call.result.checkpoints), test_seeds)
            self.ctx.caller.ledger(
                task="generator_tests", left_kind="activity_family", left_id=self.family.id,
                judge="verifier", prompt_version=GENERATOR_PROTOCOL, input_hash=_sha(code),
                verdict="pass" if ok else "fail",
                rationale={"failure": failure_text, "seeds": test_seeds, "model": call.model},
            )
            if ok:
                program = {
                    "protocol": GENERATOR_PROTOCOL, "program": code, "hash": _sha(code),
                    "checkpoints": list(call.result.checkpoints), "model": call.model,
                    "prompt_version": C.GENERATOR_PROGRAM_PROMPT, "tested_seeds": test_seeds,
                }
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
                    single_shot=single),
                prompt_version=C.SINGLE_SHOT_PROMPT if single else C.PROPOSER_PROMPT,
                result_model=C.ProposalBatch, output_tokens=OUTPUT_TOKENS["proposer"], candidates=count,
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
        for span in build_cross_source_spans(self.ctx.vault, self.ctx.repository,
                                             self.parent.learning_object_id, max_spans_per_item=6):
            passages.append({"text": span.text, "label": span.label, "extraction_id": span.extraction_id,
                             "span_id": span.span_id, "source_id": span.source_id})
        for ref in self.parent.provenance.source_refs:
            if ref.quote and ref.quote.strip():
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
                parent=_item_context(self.parent, self.ctx.vault), family=_family_context(self.family), count=self.count),
            prompt_version=C.SOURCE_ANCHORED_PROMPT, result_model=C.SourceAnchoredBatch,
            output_tokens=OUTPUT_TOKENS["source"], candidates=self.count,
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
            self._persist(candidate, insert=True)

    @staticmethod
    def _quote_in(quote: str, text: str) -> bool:
        def normalized(value: str) -> str:
            return " ".join(value.casefold().split())

        return len(quote.split()) >= MIN_QUOTE_WORDS and normalized(quote) in normalized(text)

    def _verify_source_anchored(self) -> None:
        """Quote-verified span (exact key), provenance relabel, then the closed-book filter."""
        passages = getattr(self, "passages", {})
        for candidate in [c for c in self.candidates if c.alive]:
            payload = candidate.payload
            passage = passages.get(payload["cited_ref"])
            quoted = passage is not None and self._quote_in(payload["cited_quote"], passage["text"])
            complete = payload["item_kind"] != "method_does_not_apply" or bool((payload.get("counterexample") or "").strip())
            verified = quoted and complete
            self.ctx.caller.ledger(
                task="reference_verified", left_kind="pf_candidate", left_id=candidate.id,
                judge="exact_key", prompt_version="pf-quote-span-v1", input_hash=candidate.content_hash,
                verdict="pass" if verified else "fail",
                rationale={"check": "quote_verified_span", "quote_found": quoted,
                           "counterexample_required": payload["item_kind"] == "method_does_not_apply",
                           "item_kind": payload["item_kind"]},
            )
            if not verified:
                if payload["item_kind"] == "why" and not quoted:
                    # Uncited rationale is a plausible interpretation, never the key.
                    payload["provenance_label"] = "inferred"
                    self.ctx.caller.ledger(
                        task="provenance", left_kind="pf_candidate", left_id=candidate.id,
                        judge="verifier", prompt_version="pf-quote-span-v1",
                        input_hash=candidate.content_hash, verdict="inferred",
                        rationale={"reason": "no verified span"},
                    )
                    self._reject(candidate, "provenance", "relabelled_inferred_unverified")
                else:
                    self._reject(candidate, "quote_verified_span", {"quote_found": quoted, "complete": complete})
                continue
            candidate.verification = "verified"
            candidate.verification_check = "quote_verified_span"
            self._pass(candidate, "quote_verified_span")
            self._pass(candidate, "provenance", "cited")
            if not payload.get("source_specific"):
                self._pass(candidate, "closed_book", "not_source_specific")
                self._persist(candidate)
                continue
            closed = self.ctx.role("closed_book")[0]
            call = self.ctx.caller.call(
                closed, prompt=C.closed_book_prompt(stem=payload["stem"]), prompt_version=C.CLOSED_BOOK_PROMPT,
                result_model=C.PanelSolve, output_tokens=OUTPUT_TOKENS["closed_book"],
            )
            solve = {"model": call.model, "index": 0, "input_hash": call.input_hash,
                     "final_answer": call.result.final_answer, "answer_kind": call.result.answer_kind}
            outcome = self._agreement("pf_candidate", candidate.id, candidate.content_hash,
                                      payload["stem"], payload["answer"], [solve])
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
                    prompt_version="pf-fingerprint-v1", input_hash=candidate.content_hash,
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
                      "techniques": payload.get("techniques") or []}]
        return fingerprint_keys(
            prompt=payload["stem"], expected_answer=candidate.expected_answer, skeletons=skeletons,
            generator_hash=payload.get("generator_hash"), parameters=payload.get("parameters"),
            sympy_normal_form=payload.get("sympy_normal_form"),
        )

    # verification
    def _panel_solves(self, stem: str, *, solves_per_model: int) -> list[dict[str, Any]]:
        solves = []
        for entry in self.ctx.role("panel"):
            for index in range(solves_per_model):
                call = self.ctx.caller.call(
                    entry, prompt=C.panel_solve_prompt(stem=stem, solve_index=index),
                    prompt_version=C.PANEL_SOLVE_PROMPT, result_model=C.PanelSolve,
                    output_tokens=OUTPUT_TOKENS["panel"],
                )
                solves.append({"model": call.model, "index": index, "input_hash": call.input_hash,
                               "final_answer": call.result.final_answer,
                               "answer_kind": call.result.answer_kind})
        return solves

    def _equivalence(self, stem: str, reference: str, solves: list[dict[str, Any]]) -> tuple[Any, Any]:
        entry = self.ctx.role("equivalence")[0]
        call = self.ctx.caller.call(
            entry, prompt=C.equivalence_prompt(stem=stem, reference=reference,
                                               answers=[solve["final_answer"] for solve in solves]),
            prompt_version=C.EQUIVALENCE_PROMPT, result_model=C.EquivalenceResult,
            output_tokens=OUTPUT_TOKENS["equivalence"],
        )
        return call, call.result

    def _agreement(self, subject_kind: str, subject_id: str, input_hash: str, stem: str,
                   reference: str, solves: list[dict[str, Any]]) -> dict[str, Any]:
        """LLM agreement per solve, confirmed by the sandboxed sympy check where numeric/symbolic."""
        call, result = self._equivalence(stem, reference, solves)
        usable = len(result.agreements) == len(solves)
        symbolic = result.answer_kind in {"numeric", "symbolic"}
        confirmations: list[bool | None] = [None] * len(solves)
        normal_form = None
        if usable and symbolic and result.sympy_check:
            sandbox = run_equivalence_checks(
                {"check": result.sympy_check},
                [{"program": "check", "reference": reference, "answer": solve["final_answer"]} for solve in solves],
                normal_forms={"reference": reference}, limits=self.ctx.limits,
            )
            if sandbox.ok:
                confirmations = list((sandbox.output or {}).get("checks") or confirmations)
                normal_form = ((sandbox.output or {}).get("normal_forms") or {}).get("reference")
        agrees = []
        for index, solve in enumerate(solves):
            llm = bool(usable and result.agreements[index])
            confirmed = (not symbolic) or confirmations[index] is True
            agrees.append(llm and confirmed)
            self.ctx.caller.ledger(
                task="answer_equivalence", left_kind=subject_kind, left_id=subject_id,
                judge="llm", judge_model=call.model, prompt_version=C.EQUIVALENCE_PROMPT,
                input_hash=content_key([input_hash, solve["input_hash"], call.input_hash]),
                verdict=("agree" if llm else "disagree") if usable else "unusable",
                rationale={"solve_model": solve["model"], "solve_index": solve["index"],
                           "answer_kind": result.answer_kind},
            )
            if symbolic:
                self.ctx.caller.ledger(
                    task="answer_equivalence", left_kind=subject_kind, left_id=subject_id,
                    judge="verifier", prompt_version="pf-equivalence-v1",
                    input_hash=content_key([input_hash, solve["input_hash"], call.input_hash, "sympy"]),
                    verdict={True: "agree", False: "disagree", None: "error"}[confirmations[index]],
                    rationale={"solve_model": solve["model"], "solve_index": solve["index"],
                               "program_hash": _sha(result.sympy_check or "")},
                )
        return {"agree": sum(agrees), "total": len(solves), "answer_kind": result.answer_kind,
                "usable": usable, "sympy_checked": symbolic, "normal_form": normal_form,
                "verifier_model": call.model, "per_solve": [
                    {"model": solve["model"], "agree": agree} for solve, agree in zip(solves, agrees)]}

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
        candidate.difficulty = panel_difficulty(
            self.parent.difficulty, self._parent_rate(), (agree, total),
            self.ctx.vault.config.mastery.irt.difficulty_prior_scale,
        )

    def _verify_ensemble(self) -> None:
        pf = self.ctx.vault.config.pf
        for candidate in [c for c in self.candidates if c.alive]:
            solves = self._panel_solves(candidate.payload["stem"], solves_per_model=pf.panel_solves_per_model)
            outcome = self._agreement("pf_candidate", candidate.id, candidate.content_hash,
                                      candidate.payload["stem"], candidate.payload["final_answer"], solves)
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
        solves_by_candidate = {candidate.id: self._panel_solves(candidate.payload["stem"], solves_per_model=k)
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
            call = self.ctx.caller.call(
                entry, prompt=C.structure_prompt(
                    parent=parent_context,
                    candidate={"stem": candidate.payload["stem"], "solution": candidate.payload["solution"],
                               "final_answer": candidate.payload["final_answer"],
                               "techniques": candidate.payload.get("techniques"),
                               "checkpoints": candidate.payload.get("checkpoints")},
                    declared_relation=candidate.declared_relation),
                prompt_version=C.STRUCTURE_PROMPT, result_model=C.StructureVerdict,
                output_tokens=OUTPUT_TOKENS["structure"],
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
                      "rubric_applies_verbatim": verdict.rubric_applies_verbatim}
            if verdict.relation == "reject" or not verdict.rubric_applies_verbatim:
                self._reject(candidate, "structure_check", detail)
                continue
            if candidate.declared_relation == "isomorph" and (
                    verdict.relation != "isomorph" or not verdict.checkpoint_sequence_preserved):
                # A declared isomorph without a passing structure check is
                # never published as an isomorph: relabel near, or reject.
                if verdict.relation in {"near", "far"} and self.path != "generator":
                    candidate.final_relation = verdict.relation
                    detail["relabelled"] = verdict.relation
                else:
                    self._reject(candidate, "structure_check", detail)
                    continue
            else:
                candidate.final_relation = (
                    candidate.declared_relation if candidate.declared_relation in {"near", "far"}
                    and verdict.relation in {"near", "far"} else verdict.relation)
            self._pass(candidate, "structure_check", detail)
            self._persist(candidate)

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
            call = self.ctx.caller.call(
                entry, prompt=C.freshness_prompt(
                    candidate={"stem": candidate.payload["stem"],
                               "final_answer": candidate.payload["final_answer"],
                               "relation": candidate.final_relation or candidate.declared_relation},
                    comparisons=comparisons),
                prompt_version=C.FRESHNESS_PROMPT, result_model=C.FreshnessVerdict,
                output_tokens=OUTPUT_TOKENS["freshness"], pairs=len(comparisons),
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
                candidate.final_relation = "isomorph"
                detail["relabelled"] = "isomorph"
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
            call = self.ctx.caller.call(
                entry, prompt=C.selection_prompt(family=_family_context(self.family),
                                                 survivors=survivors_context, slots=self.slots),
                prompt_version=C.SELECTION_PROMPT, result_model=C.SelectionVerdict,
                output_tokens=OUTPUT_TOKENS["selection"],
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
        self.selected_order = chosen
        for candidate in survivors:
            candidate.status = "selected" if candidate.id in chosen else "not_selected"
            self._persist(candidate)

    def _publish(self) -> None:
        order = getattr(self, "selected_order", [])
        if not order:
            return
        vault, outcome = publish_selected(self.ctx.vault, self.ctx.repository, order, clock=self.ctx.clock)
        self.ctx.vault = vault
        self.ctx.caller.vault = vault
        self.report.update(published_item_ids=outcome["published_item_ids"],
                           capped=outcome["capped_candidates"])
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
                                      relation=options.relation, count=n),
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
                                           parent=context, family=_family_context(family), count=n),
        "closed_book": C.closed_book_prompt(stem=stem_proxy),
    }
    models = {"skeleton": C.SkeletonResult, "program": C.GeneratorProgramResult, "proposer": C.ProposalBatch,
              "panel": C.PanelSolve, "equivalence": C.EquivalenceResult, "structure": C.StructureVerdict,
              "freshness": C.FreshnessVerdict, "selection": C.SelectionVerdict,
              "source": C.SourceAnchoredBatch, "closed_book": C.PanelSolve}
    calls = {"skeleton": 1, "panel": (n + 1) * panel * k, "structure": 1 if path == "generator" else n,
             "freshness": n}
    if path == "generator":
        calls["program"] = 1
        calls["equivalence"] = 1
    elif path == "source_anchored":
        calls.pop("panel")
        calls.update(source=1, closed_book=n, equivalence=n)
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
        tokens = estimate_tokens(prompts[prompt_role], models[prompt_role], OUTPUT_TOKENS[role])
        entries = roles[role]
        per_entry = count if role in {"panel", "proposer"} else count
        plan["roles"][role] = {
            "calls": count, "tokens": tokens * count,
            "providers": [entry.provider for entry in entries],
            "models": [entry.model for entry in entries],
            "subscription": [entry.subscription for entry in entries],
            "per_call_tokens": tokens, "per_entry": per_entry,
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
                                       C.SOURCE_ANCHORED_PROMPT, C.CLOSED_BOOK_PROMPT}),
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
    if options.seed_items and dry_run:
        report["seed_items_planned"] = list(options.seed_items)
    elif options.seed_items:
        vault = _seed_families(vault, repository, options.seed_items, clock)
    targets = family_targets(vault, options)
    if options.seed_items and dry_run:
        seeded = [vault.practice_items[item_id] for item_id in options.seed_items if item_id in vault.practice_items]
        for item in seeded:
            if not item.family_id:
                placeholder = ActivityFamily(
                    id=f"(seed:{item.id})", learning_object_id=item.learning_object_id,
                    idea_statement="seed", retrieval_target="seed", created_at="", updated_at="")
                targets.append((placeholder, item))
    paths = {family.id: _resolve_path(vault, family, options.path) for family, _ in targets}
    used_roles = {"skeleton", "panel", "structure", "freshness"}
    if "generator" in paths.values():
        used_roles |= {"program", "equivalence"}
    if "ensemble" in paths.values():
        used_roles |= {"proposer", "equivalence", "selection"}
    if "single_shot" in paths.values():
        used_roles |= {"single_shot", "equivalence"}
    if "source_anchored" in paths.values():
        used_roles |= {"source", "closed_book", "equivalence"}
    try:
        if dry_run:
            roles = {role: (resolve_role_clients(vault, role, injected=clients[role])
                            if clients and role in clients
                            else planned_role_clients(vault, role, tier_routes=tier_routes))
                     for role in ("skeleton", "program", "single_shot", "source", "proposer", "panel",
                                  "equivalence", "closed_book", "structure", "freshness", "selection")}
        else:
            roles = {}
            for role in ("skeleton", "program", "single_shot", "source", "proposer", "panel", "equivalence",
                         "closed_book", "structure", "freshness", "selection"):
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
    if "ensemble" in paths.values() and len(distinct_models(roles["proposer"])) < 2:
        report.update(status="refused",
                      reason="pf_proposers must name profiles with at least two distinct model slugs")
        return report
    plans = [_plan_family(vault, family, parent, paths[family.id], options, roles, repository)
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
    ctx = _Context(vault, repository, caller, options, round_id, tier_routes, clients, clock)
    ctx._roles.update({role: entries for role, entries in roles.items() if role in used_roles})
    with _run_lock(vault.root):
        try:
            for family, parent in targets:
                run = _FamilyRun(ctx, ctx.vault.activity_families.get(family.id, family),
                                 ctx.vault.practice_items[parent.id], paths[family.id])
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
    """Publish selected-but-capped candidates under today's cap; no model calls."""
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
    "FILTER_ORDER", "GATE_POLICY_VERSION", "GENERATOR_VERSIONS", "GenerationOptions", "PATHS",
    "PFRefused", "family_targets", "generate_practice", "panel_difficulty", "pf_run_lock",
    "pf_status", "publish_backlog",
]
