"""Slice 2 T4's report: shadow contamination flags with audited samples (§13).

``contamination_report`` scans persisted history, decides what it can, and
reports flag rates, agreement with the lexical floor, proposals and samples.

* **Shadow only.** It never blocks an item, debits ``reveal_events``, burns a
  reservation, writes an exposure or changes what is served. Proposals are
  listed for the owner and are never executed (``proposals_executed`` is 0).
* **No embedding call.** It reads stored vectors only; missing vectors degrade
  to the lexical floor and the symbolic check, and the report says where.
* **Who decides** (R1, R4): the owner, then the symbolic verifier (a math match
  linked to the item: the text works the item's own expression to its answer),
  then the LLM judge's first pass. No score decides anything.
* **Noise floor** (R6): a bounded, deterministic sample of pairs per detector
  is judged a second time under identical settings; the report gives the
  disagreement between the two passes beside the owner's audited verdicts, so
  a detector change can be told apart from judge variability.
* **Paid work** is the judge alone, under ``SpendCaps``; ``--dry-run`` plans it
  (repeats included) with no client, lock or data change. Verdicts append to
  ``judgment_ledger``.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import statistics
from typing import Any

from learnloop.ai.errors import AIInterrupted, AIProviderUnavailable
from learnloop.ai.execution import content_key
from learnloop.ai.routing import provider_for_task, ready_client_for_task
from learnloop.ai.spend import (
    ESTIMATED_ONLY, SpendBudget, SpendCaps, SpendLimitExceeded, is_subscription_transport,
)
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION
from learnloop.db.repositories import Repository
from learnloop.db.stores.judgments import append_judgment
from learnloop.ids import new_ulid
from learnloop.ops.contamination.detectors import (
    DETECTORS, POSITIVE_VERDICT, SCANNERS, Candidate, DetectorScan, StoredVectors,
)
from learnloop.ops.contamination.judge import (
    METERED_JUDGE_TYPES, PRIMARY_PASS, PROMPT_VERSIONS, REPEAT_PASS, JudgeRequest, build_requests,
    estimate, judge_settings, owner_rows, rows_by_id, run_judgments,
)
from learnloop.ops.contamination.recipes import CONTAMINATION_RECIPES
from learnloop.ops.contamination.symbolic import SYMBOLIC_VERSION
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths


REPORT_VERSION = "slice-2-t4-contamination-report-v1"
EXCERPT_CHARS = 240
SAMPLE_CATEGORIES = ("shadow_only", "floor_and_shadow", "floor_only", "unsure")


@dataclass(frozen=True)
class Decision:
    verdict: str  # positive (leak/reveal) | clean | unsure | undecided
    judge: str | None = None
    judgment_id: str | None = None
    model: str | None = None
    rationale: str | None = None

    @property
    def positive(self) -> bool:
        return self.verdict in POSITIVE_VERDICT.values()


def verifier_judgment_id(candidate: Candidate) -> str:
    """Content-addressed: the same texts and checker never append twice."""

    assert candidate.symbolic is not None
    return "ctv_" + content_key({
        "version": SYMBOLIC_VERSION, "question": candidate.question,
        "subject": candidate.subject_text, "expected": candidate.symbolic.expected,
    })


def _repeats(requests: list[JudgeRequest]) -> int:
    return sum(request.pass_index != PRIMARY_PASS for request in requests)


@contextmanager
def _report_lock(root: Path) -> Iterator[None]:
    import fcntl

    path = root / ".learnloop" / "contamination-report.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another contamination report is running for this vault") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _excerpt(text: str) -> str:
    flat = " ".join((text or "").split())
    return flat if len(flat) <= EXCERPT_CHARS else flat[: EXCERPT_CHARS - 1] + "…"


def _rationale(row: dict[str, Any]) -> str | None:
    try:
        parsed = json.loads(row.get("rationale") or "")
    except ValueError:
        return row.get("rationale") or None
    if isinstance(parsed, dict):
        result = parsed.get("result")
        if isinstance(result, dict):
            return result.get("rationale")
        return parsed.get("reason") or parsed.get("matched")
    return None


def _decide(
    candidate: Candidate, request: JudgeRequest | None, rows: dict[str, dict[str, Any]],
    owners: dict[tuple[str, str, str, str, str], dict[str, Any]],
) -> Decision:
    def decision(row: dict[str, Any]) -> Decision:
        return Decision(row["verdict"], row["judge"], row["id"], row.get("judge_model"), _rationale(row))

    owner = owners.get(candidate.question)
    if owner is not None:
        return decision(owner)
    if candidate.symbolic is not None and candidate.symbolic.decides:
        row = rows.get(verifier_judgment_id(candidate))
        if row is not None:
            return decision(row)
    if request is not None and request.judgment_id in rows:
        return decision(rows[request.judgment_id])
    return Decision("undecided")


def _stats(values: Sequence[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0}
    return {"n": len(values), "min": round(min(values), 6),
            "median": round(statistics.median(values), 6), "max": round(max(values), 6)}


def _proposal(candidate: Candidate, decision: Decision) -> dict[str, Any] | None:
    common = {"decided_by": decision.judge, "judgment_id": decision.judgment_id}
    if candidate.detector == "exam_leakage":
        return {"action": "review_item", "practice_item_id": candidate.left_id,
                "source_span": candidate.right_id, "live_gate_would_block": candidate.floor, **common}
    if candidate.detector == "tutor_answer_leak":
        next_attempt = candidate.extra.get("next_attempt") or {}
        if candidate.floor or next_attempt.get("primed"):
            # The live floor already flagged and debited this answer, or the
            # next attempt was recorded as primed anyway: nothing to correct.
            return None
        return {"action": "reveal_debit", "question_event_id": candidate.left_id,
                "practice_item_id": candidate.right_id,
                "live_reveal_amount": candidate.extra.get("live_reveal_amount"),
                "next_attempt": candidate.extra.get("next_attempt"), **common}
    status = candidate.extra.get("reservation_status")
    if status == "reserved":
        if not candidate.extra.get("burn_eligible"):
            return None  # already burned by an exposure, or no longer held unseen
        return {"action": "burn_reserve", "surface_id": candidate.right_id,
                "question_event_id": candidate.left_id, "asked_at": candidate.extra.get("asked_at"),
                "reserved_at": candidate.extra.get("reserved_at"), **common}
    if status == "rendered":
        # Taken after the reveal: nothing to burn, but its cold evidence may be
        # contaminated, so the administration goes for review.
        return {"action": "review_assessment", "surface_id": candidate.right_id,
                "question_event_id": candidate.left_id, "administration_id": candidate.extra.get("administration_id"),
                "reservation_status": status, "asked_at": candidate.extra.get("asked_at"),
                "reserved_at": candidate.extra.get("reserved_at"),
                "rendered_at": candidate.extra.get("closed_at"), **common}
    return None  # cancelled or released unseen: no reserve and no assessment


def _agreement(pairs: list[tuple[str, str]]) -> dict[str, Any]:
    compared = len(pairs)
    agree = sum(left == right for left, right in pairs)
    return {"compared": compared, "agree": agree, "disagree": compared - agree}


def _noise_floor(
    scan: DetectorScan, requests: dict[tuple[str, str, str, str, str], JudgeRequest],
    repeats: dict[tuple[str, str, str, str, str], JudgeRequest], rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Run-to-run disagreement of the judge on its repeated pairs (R6)."""

    pairs = []
    sampled = [candidate for candidate in scan.candidates if candidate.question in repeats]
    for candidate in sampled:
        first, second = requests.get(candidate.question), repeats[candidate.question]
        if first is not None and first.judgment_id in rows and second.judgment_id in rows:
            pairs.append((rows[first.judgment_id]["verdict"], rows[second.judgment_id]["verdict"]))
    block = {"repeat_pairs": len(sampled), **_agreement(pairs)}
    block["disagreement_rate"] = round(block["disagree"] / block["compared"], 6) if block["compared"] else None
    return block


def _owner_audit(
    scan: DetectorScan, requests: dict[tuple[str, str, str, str, str], JudgeRequest],
    rows: dict[str, dict[str, Any]], owners: dict[tuple[str, str, str, str, str], dict[str, Any]],
) -> dict[str, Any]:
    """The independently audited baseline: each automatic judge against the owner."""

    audited, llm, verifier = 0, [], []
    for candidate in scan.candidates:
        owner = owners.get(candidate.question)
        if owner is None:
            continue
        audited += 1
        request = requests.get(candidate.question)
        if request is not None and request.judgment_id in rows:
            llm.append((rows[request.judgment_id]["verdict"], owner["verdict"]))
        if candidate.symbolic is not None and candidate.symbolic.decides:
            row = rows.get(verifier_judgment_id(candidate))
            if row is not None:
                verifier.append((row["verdict"], owner["verdict"]))
    return {"audited_pairs": audited, "llm": _agreement(llm), "verifier": _agreement(verifier)}


def _summarize(
    scan: DetectorScan, decisions: dict[tuple[str, str, str, str, str], Decision],
    requests: dict[tuple[str, str, str, str, str], JudgeRequest],
    repeats: dict[tuple[str, str, str, str, str], JudgeRequest],
    rows: dict[str, dict[str, Any]], owners: dict[tuple[str, str, str, str, str], dict[str, Any]],
    sample_size: int,
) -> dict[str, Any]:
    reasons = Counter(reason for candidate in scan.candidates for reason in candidate.reasons)
    decided = Counter()
    by_judge = Counter()
    agreement = Counter()
    by_model: dict[str, Counter] = defaultdict(Counter)
    scores: dict[str, list[float]] = defaultdict(list)
    proposals, flagged_subjects = [], set()
    categories: dict[str, list[tuple[str, Candidate, Decision]]] = defaultdict(list)
    judged = 0
    for candidate in scan.candidates:
        decision = decisions[candidate.question]
        request = requests.get(candidate.question)
        if request is not None and request.judgment_id in rows:
            judged += 1
            row = rows[request.judgment_id]
            by_model[row["judge_model"]][row["verdict"]] += 1
        label = "flag" if decision.positive else decision.verdict
        decided[label] += 1
        if decision.judge:
            by_judge[decision.judge] += 1
        if decision.positive:
            flagged_subjects.add(candidate.left_id)
            proposal = _proposal(candidate, decision)
            if proposal is not None:
                proposals.append(proposal)
        if candidate.embedding_score is not None and decision.verdict in {"clean", *POSITIVE_VERDICT.values()}:
            scores["flag" if decision.positive else "clean"].append(candidate.embedding_score)
        if candidate.floor and decision.positive:
            category = "floor_and_shadow"
        elif candidate.floor and decision.verdict == "clean":
            category = "floor_only"
        elif decision.positive:
            category = "shadow_only"
        elif decision.verdict == "unsure":
            category = "unsure"
        else:
            category = "floor_undecided" if candidate.floor else None
        if category is not None:
            agreement[category] += 1
            if category in SAMPLE_CATEGORIES:
                categories[category].append((content_key(candidate.question), candidate, decision))
    samples = {}
    for category in SAMPLE_CATEGORIES:
        chosen = sorted(categories.get(category, []), key=lambda entry: entry[0])[:sample_size]
        samples[category] = [{
            "question": dict(zip(("task", "left_kind", "left_id", "right_kind", "right_id"), candidate.question)),
            "signals": candidate.signals(),
            "decision": asdict(decision),
            "subject_excerpt": _excerpt(candidate.subject_text),
            "target_excerpt": _excerpt(candidate.target_text),
        } for _, candidate, decision in chosen]
    return {
        "status": scan.status,
        "subjects": scan.subjects,
        "targets": scan.targets,
        "embedding": scan.embedding,
        "lexical_floor": {
            "flagged_subjects": scan.floor_subjects,
            "flagged_pairs": sum(candidate.floor for candidate in scan.candidates),
        },
        "symbolic": scan.symbolic,
        "shortlist": {
            "pairs": len(scan.candidates),
            "by_reason": {reason: reasons.get(reason, 0) for reason in ("bound", "lexical", "symbolic", "embedding")},
            "embedding_only": sum(candidate.reasons - {"bound"} == {"embedding"} for candidate in scan.candidates),
        },
        "judge": {
            "requested": sum(candidate.question in requests for candidate in scan.candidates),
            "judged": judged,
            "verdicts_by_model": {model: dict(counts) for model, counts in sorted(by_model.items())},
        },
        "decided": {
            "flags": decided.get("flag", 0), "clean": decided.get("clean", 0),
            "unsure": decided.get("unsure", 0), "undecided": decided.get("undecided", 0),
            "by_judge": dict(sorted(by_judge.items())),
        },
        "flagged_subjects": len(flagged_subjects),
        # Nothing was measured without targets or subjects: no rate, not zero.
        "flag_rate": (
            round(len(flagged_subjects) / scan.subjects, 6)
            if scan.status == "scanned" and scan.subjects else None
        ),
        "agreement": {key: agreement.get(key, 0) for key in (
            "floor_and_shadow", "floor_only", "shadow_only", "floor_undecided", "unsure",
        )},
        "noise_floor": _noise_floor(scan, requests, repeats, rows),
        "owner_audit": _owner_audit(scan, requests, rows, owners),
        "embedding_scores": {"flag": _stats(scores["flag"]), "clean": _stats(scores["clean"])},
        "proposals": proposals,
        "samples": samples,
        **({"flags_by_reservation_status": dict(sorted(Counter(
            candidate.extra.get("reservation_status") for candidate in scan.candidates
            if decisions[candidate.question].positive
        ).items()))} if scan.detector == "reader_reveal" else {}),
    }


def _write_verifier_verdicts(repository: Repository, candidates: list[Candidate], rows: dict[str, dict[str, Any]]) -> int:
    written = 0
    for candidate in candidates:
        if candidate.symbolic is None or not candidate.symbolic.decides:
            continue
        judgment_id = verifier_judgment_id(candidate)
        if judgment_id in rows:
            continue
        with repository.connection() as connection:
            if connection.execute("SELECT 1 FROM judgment_ledger WHERE id=?", (judgment_id,)).fetchone():
                continue
            append_judgment(
                connection, id=judgment_id, task=candidate.task,
                left_kind=candidate.left_kind, left_id=candidate.left_id,
                right_kind=candidate.right_kind, right_id=candidate.right_id,
                judge="verifier", prompt_version=SYMBOLIC_VERSION,
                input_hash=judgment_id[4:], verdict=POSITIVE_VERDICT[candidate.task],
                rationale=json.dumps({
                    "detector": candidate.detector,
                    "matched": candidate.symbolic.matched, "expected": candidate.symbolic.expected,
                    "method": candidate.symbolic.method,
                }, sort_keys=True),
            )
        written += 1
    return written


def contamination_report(
    loaded: LoadedVault,
    *,
    caps: SpendCaps,
    dry_run: bool = False,
    judge: bool = True,
    detectors: Sequence[str] = DETECTORS,
    top_k: int = 3,
    sample_size: int = 5,
    repeat_sample: int = 5,
    price_per_million: float | None = None,
    judge_revision: str = "1",
    cancelled: Callable[[], bool] | None = None,
    client: Any | None = None,
) -> dict[str, Any]:
    """Scan, decide what can be decided, and report; see the module docstring."""

    unknown = sorted(set(detectors) - set(DETECTORS))
    if unknown or not detectors:
        raise ValueError(f"Unknown or empty detectors: {', '.join(unknown) or 'none selected'}")
    if type(top_k) is not int or not 1 <= top_k <= 50:
        raise ValueError("top_k must be an integer between 1 and 50")
    if type(sample_size) is not int or not 0 <= sample_size <= 100:
        raise ValueError("sample_size must be an integer between 0 and 100")
    if type(repeat_sample) is not int or not 0 <= repeat_sample <= 50:
        raise ValueError("repeat_sample must be an integer between 0 and 50")
    if price_per_million is not None and (not math.isfinite(price_per_million) or price_per_million <= 0):
        raise ValueError("price_per_million must be finite and positive")
    if not judge_revision.strip():
        raise ValueError("judge_revision must be nonempty")
    sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
    if not sqlite_path.exists():
        raise ValueError("The vault has no database; initialize it first")

    # Read-only scan: no migration, no write, no provider.
    reader = Repository.attach(sqlite_path, read_only=True)
    vectors = StoredVectors(loaded, sqlite_path)
    try:
        scans = {name: SCANNERS[name](loaded, reader, vectors, top_k=top_k) for name in DETECTORS if name in detectors}
    finally:
        vectors.close()
    candidates = [candidate for scan in scans.values() for candidate in scan.candidates]
    # The noise-floor sample: per detector, the first pairs in a stable hash
    # order, so a resumed or repeated report re-judges the same pairs.
    repeat_questions = [
        question for scan in scans.values()
        for _, question in sorted((content_key(c.question), c.question) for c in scan.candidates)[:repeat_sample]
    ]

    selection = provider_for_task(loaded.config, "contamination_judge")
    provider = getattr(client, "provider_name", None) or selection.provider_name
    settings = judge_settings(loaded, provider, getattr(client, "model", None), judge_revision)
    route_profile = loaded.config.ai.providers.get(provider)
    subscription = (
        is_subscription_transport(client=client) if client is not None
        else is_subscription_transport(profile=route_profile)
    )

    def plan() -> tuple[list[JudgeRequest], dict[str, dict[str, Any]], list[JudgeRequest]]:
        requests = build_requests(candidates, settings, repeats=repeat_questions) if judge else []
        verifier_ids = [verifier_judgment_id(c) for c in candidates if c.symbolic is not None and c.symbolic.decides]
        rows = rows_by_id(sqlite_path, [r.judgment_id for r in requests] + verifier_ids)
        return requests, rows, [r for r in requests if r.judgment_id not in rows]

    requests, rows, pending = plan()
    budget = SpendBudget(caps, cancelled=cancelled, subscription=subscription)
    report: dict[str, Any] = {
        "status": "dry_run" if dry_run else "pending", "dry_run": dry_run,
        "report": REPORT_VERSION, "shadow": True, "proposals_executed": 0,
        "detectors_run": [name for name in DETECTORS if name in detectors],
        "top_k": top_k, "sample_size": sample_size, "repeat_sample": repeat_sample,
        "manifest": {
            "algorithm_version": loaded.config.algorithms.algorithm_version,
            "config_hash": content_key(loaded.config.model_dump(mode="json")),
            "prompt_versions": dict(PROMPT_VERSIONS),
            "symbolic_version": SYMBOLIC_VERSION,
            "recipe_versions": {name: recipe.version for name, recipe in sorted(CONTAMINATION_RECIPES.items())},
            "embedding_model": loaded.config.embedding.model,
            "embedding_enabled": loaded.config.embedding.enabled,
            "judge_revision": judge_revision,
            "shortlist_rule": "rank_top_k_with_boundary_ties_no_cosine_cutoff",
            "tutor_pair_rule": "every bound pair judged; rank recorded for evaluation only",
            "reader_scope_rule": "reservations live at, or closed after, each answer; burn only live eligible reserves",
            "noise_floor_rule": "repeat_sample pairs per detector judged a second time under identical settings",
            "tutor_floor_rule": "leak_suspected or live reveal debit >= AUTO_PRIME_REVEAL_THRESHOLD",
            "decision_authority": ["owner", "verifier", "llm"],
        },
        "judge": {
            "enabled": judge, "provider": provider, "model_id": settings["model"],
            "billing": "subscription" if subscription else "metered",
            "cost_basis": ESTIMATED_ONLY if subscription else "metered_caps",
            "physical_request_bound": not subscription,
            "caps": caps.as_dict(), "caps_in_force": budget.declared(),
            "requests": len(requests), "repeat_requests": _repeats(requests),
            "cached": len(requests) - len(pending),
            "pending": len(pending), "completed": 0,
            "estimate": asdict(estimate(pending, price_per_million)),
            "charged": asdict(budget.used),
            "price_per_million": price_per_million,
            "price_source": "owner_override" if price_per_million is not None else "unknown",
        },
        "verifier": {"decisions": sum(1 for c in candidates if c.symbolic is not None and c.symbolic.decides),
                     "written": 0},
    }

    def finish(status: str | None = None, **extra: Any) -> dict[str, Any]:
        if status is not None:
            report["status"] = status
        report.update(extra)
        current_rows = rows_by_id(
            sqlite_path,
            [r.judgment_id for r in requests]
            + [verifier_judgment_id(c) for c in candidates if c.symbolic is not None and c.symbolic.decides],
        )
        owners = owner_rows(sqlite_path)
        by_question = {r.candidate.question: r for r in requests if r.pass_index == PRIMARY_PASS}
        repeats = {r.candidate.question: r for r in requests if r.pass_index == REPEAT_PASS}
        decisions = {c.question: _decide(c, by_question.get(c.question), current_rows, owners) for c in candidates}
        report["judge"]["charged"] = asdict(budget.used)
        report["judge"]["remaining"] = sum(1 for r in requests if r.judgment_id not in current_rows)
        report["detectors"] = {
            name: _summarize(scan, decisions, by_question, repeats, current_rows, owners, sample_size)
            for name, scan in scans.items()
        }
        return report

    try:
        budget.check(estimate(pending, price_per_million))
    except AIInterrupted:
        return finish("cancelled")
    except SpendLimitExceeded as exc:
        return finish("over_budget", reason=str(exc))
    if dry_run:
        report["judge"]["bounded_transport"] = (
            client.supports(BOUNDED_STRUCTURED_COMPLETION) if client is not None
            else route_profile is not None and route_profile.type in METERED_JUDGE_TYPES
        )
        return finish()

    with _report_lock(loaded.root):
        writer = Repository(sqlite_path)  # applies migrations: the ledger must exist
        requests, rows, pending = plan()
        report["verifier"]["written"] = _write_verifier_verdicts(writer, candidates, rows)
        if not pending:
            return finish("complete")
        if client is None:
            profile = route_profile
            if profile is None or not (profile.type in METERED_JUDGE_TYPES or is_subscription_transport(profile=profile)):
                return finish(
                    "unavailable",
                    reason="The contamination judge needs an openai_chat/openrouter profile (bounded "
                           "physical requests) or a Codex profile (subscription, estimated cost). "
                           "Set ai.routing.contamination_judge to one, or pass --no-judge.",
                )
            # Pin the planned route: a fallback must not silently change the
            # dry-run model, checkpoint ids or estimate.
            resolved = ready_client_for_task(loaded.root, loaded.config, "contamination_judge", explicit=provider)
            if not resolved.ready:
                return finish("unavailable", reason=resolved.runtime.message)
            client = resolved.client
            # The resolved client names the model the checkpoint ids include.
            settings = judge_settings(loaded, provider, getattr(client, "model", None), judge_revision)
            requests, rows, pending = plan()
            report["judge"].update(
                model_id=settings["model"], requests=len(requests), repeat_requests=_repeats(requests),
                cached=len(requests) - len(pending), pending=len(pending),
                estimate=asdict(estimate(pending, price_per_million)),
            )
            if not pending:
                return finish("complete")
        if not subscription and not client.supports(BOUNDED_STRUCTURED_COMPLETION):
            return finish("unavailable", reason="Judge transport cannot bound physical requests")
        if not settings["model"]:
            return finish("unavailable", reason="The contamination judge must resolve to an explicit model ID")
        run_id = new_ulid()
        report["run_id"] = run_id
        try:
            budget.check(estimate(pending, price_per_million))

            def saved(_request: JudgeRequest) -> None:
                report["judge"]["completed"] += 1

            run_judgments(
                writer, pending, client=client, budget=budget, settings=settings,
                subscription=subscription, price_per_million=price_per_million,
                run_id=run_id, on_saved=saved,
            )
            return finish("complete")
        except (AIInterrupted, KeyboardInterrupt):
            return finish("cancelled")
        except SpendLimitExceeded as exc:
            return finish("over_budget", reason=str(exc))
        except AIProviderUnavailable as exc:
            # Never echo provider errors: they can contain request text.
            return finish("provider_failed", error_type=type(exc).__name__)
