"""PF-c before/after report (Slice 2 §5.5, §5.7: an E1-style report after S1.3).

Two blind graders on identical inputs:

* **before** - the mvp-2.0 blind prompt (no reference policy);
* **after** - mvp-2.1 with PF-c (reference policy, valid-alternative path,
  solve-first, the deterministic unverified-criterion gate).

Two measures:

* **Valid-alternative false rejection.** A frontier route writes a correct
  derivation that differs from the reference; only derivations the
  deterministic checker VERIFIES (final answer equal to the reference, every
  relation checked) count. Each is graded by both arms; a rejection is a score
  below full marks. "Negative evidence" additionally excludes criteria the
  after arm recorded unverified.
* **Error on real adjudicated answers.** The owner's answers whose stored
  diagnosis the owner adjudicated with an anchor: does each arm's first
  divergence land on the adjudicated quote?

Paid work goes through one :class:`ReviewSpend` (caps before requests,
``--dry-run`` estimate, Codex billed ``estimated_only``). The vault is only
read, except that every verdict appends to ``judgment_ledger`` (standard rule
6); answers and statements never appear in the report.
"""

from __future__ import annotations

import json
import random
from collections import Counter
from typing import Any, Callable, Mapping, Sequence

from learnloop.ai.execution import content_key
from learnloop.ai.spend import SpendCaps
from learnloop.attempts.answer_check import parse_answer, reference_final_answer
from learnloop.attempts.blind_grading import (
    BLIND_GRADING_PROMPT_VERSION,
    blind_grading_context,
    blind_grading_prompt,
    validate_blind_grading_proposal,
)
from learnloop.attempts.grading import GradingValidationError, resolved_rubric
from learnloop.attempts.grading_support import (
    REFERENCE_POLICY_PROMPT_VERSION,
    reference_policy,
    request_blind_grading_run,
)
from learnloop.db.repositories import Repository
from learnloop.diagnosis.offline_review.probes import (
    is_reference_bearing,
    request_valid_alternative,
    valid_alternative_prompt,
    verify_alternative,
)
from learnloop.diagnosis.offline_review.report import wilson
from learnloop.diagnosis.offline_review.spend import ReviewSpend
from learnloop.ids import new_ulid
from learnloop.vault.models import LoadedVault

PFC_REPORT_VERSION = "pf-c-report-v1"
ARMS = ("before", "after")
ARM_PROMPTS = {"before": BLIND_GRADING_PROMPT_VERSION, "after": REFERENCE_POLICY_PROMPT_VERSION}
DEFAULT_CAPS = SpendCaps(
    max_candidates=200,
    max_pairs=0,
    max_retries=4,
    max_calls=400,
    max_total_tokens=2_000_000,
    max_estimated_usd=5.0,
)


def _tokens(text: str) -> int:
    return (len(text.encode("utf-8")) + 3) // 4


def checkable_reference(item: Any) -> bool:
    """A bare parseable answer, or a worked solution with a numeric conclusion."""

    expected = item.expected_answer
    if not isinstance(expected, str) or not expected.strip():
        return False
    return reference_final_answer(expected) is not None or parse_answer(expected) is not None


def plan_pfc(
    vault: LoadedVault,
    repository: Repository,
    *,
    max_items: int = 40,
    max_real: int = 40,
    seed: int = 0,
) -> dict[str, Any]:
    """Seeded, LO-stratified reference-bearing items + owner-adjudicated answers."""

    rng = random.Random(seed)
    # Items whose reference has a checkable final answer come first: only
    # those can yield a deterministically verified alternative (a proof-style
    # reference never verifies), so the spend goes where E1 can count.
    tiers: tuple[dict[str, list[str]], dict[str, list[str]]] = ({}, {})
    for item_id, item in sorted(vault.practice_items.items()):
        if item.status == "retired" or not is_reference_bearing(item):
            continue
        tier = tiers[0] if checkable_reference(item) else tiers[1]
        tier.setdefault(item.learning_object_id, []).append(item_id)
    items: list[str] = []
    for by_lo in tiers:
        for ids in by_lo.values():
            rng.shuffle(ids)
        los = sorted(by_lo)
        while len(items) < max_items and any(by_lo.values()):
            for lo in los:
                if by_lo[lo] and len(items) < max_items:
                    items.append(by_lo[lo].pop())
    real: list[str] = []
    for row in repository.list_diagnosis_adjudications(active_only=True):
        if len(real) >= max_real:
            break
        if str(row.get("adjudicator_source") or "") != "human_owner":
            continue
        anchor = row.get("adjudicated_anchor") or {}
        if not isinstance(anchor, Mapping) or not str(anchor.get("quote") or "").strip():
            continue
        attempt = repository.fetch_practice_attempt(str(row["attempt_id"]))
        if attempt is None or str(attempt.get("practice_item_id")) not in vault.practice_items:
            continue
        real.append(str(row["attempt_id"]))
    return {"items": items, "real_attempts": list(dict.fromkeys(real)), "seed": seed}


def estimate_pfc(vault: LoadedVault, repository: Repository, plan: Mapping[str, Any], spend: ReviewSpend) -> dict[str, Any]:
    generator_in = sum(
        _tokens(valid_alternative_prompt(vault, vault.practice_items[item_id])) for item_id in plan["items"]
    )
    grading_in = 0
    for item_id in plan["items"]:
        item = vault.practice_items[item_id]
        context = blind_grading_context(vault, item, attempt_id="probe", learner_answer_md=item.prompt)
        grading_in += 2 * _tokens(blind_grading_prompt(context)) + 400
    for attempt_id in plan["real_attempts"]:
        attempt = repository.fetch_practice_attempt(attempt_id) or {}
        item = vault.practice_items[str(attempt["practice_item_id"])]
        context = blind_grading_context(
            vault, item, attempt_id=attempt_id, learner_answer_md=str(attempt.get("learner_answer_md") or "")
        )
        grading_in += 2 * _tokens(blind_grading_prompt(context)) + 400
    generator_calls = len(plan["items"])
    grading_calls = 2 * (len(plan["items"]) + len(plan["real_attempts"]))
    generator = spend.estimate(
        "diagnosis_generator",
        calls=generator_calls,
        input_tokens=generator_in,
        output_tokens=generator_calls * spend.output_limit("diagnosis_generator"),
        candidates=generator_calls,
    )
    grading = spend.estimate(
        "grading",
        calls=grading_calls,
        input_tokens=grading_in,
        output_tokens=grading_calls * spend.output_limit("grading"),
    )
    total_usd = (
        None
        if generator.estimated_usd is None or grading.estimated_usd is None
        else round(generator.estimated_usd + grading.estimated_usd, 6)
    )
    return {
        "items": len(plan["items"]),
        "real_attempts": len(plan["real_attempts"]),
        "calls": {"diagnosis_generator": generator_calls, "grading": grading_calls},
        "metered_tokens": generator.total_tokens + grading.total_tokens,
        "estimated_usd": total_usd,
        "routes": {route: info.as_dict() for route, info in sorted(spend.routes.items())},
    }


def _grade(
    vault: LoadedVault,
    client: Any,
    spend: ReviewSpend,
    *,
    item_id: str,
    attempt_id: str,
    answer: str,
    arm: str,
) -> dict[str, Any]:
    item = vault.practice_items[item_id]
    rubric = resolved_rubric(vault, item)
    from learnloop.diagnosis.diagnostic_augmentation import diagnostic_verifier_observations

    context = blind_grading_context(
        vault,
        item,
        attempt_id=attempt_id,
        learner_answer_md=answer,
        verifier_observations=diagnostic_verifier_observations(answer, str(item.expected_answer)),
    )
    if arm == "after":
        from dataclasses import replace

        context = replace(context, reference_policy=reference_policy(item, answer))
    with spend.request("grading", f"pfc_{arm}", input_tokens=_tokens(blind_grading_prompt(context))):
        run = request_blind_grading_run(client, context, rubric=rubric)
    try:
        validated = validate_blind_grading_proposal(
            run.proposal, attempt_id=attempt_id, item=item, vault=vault, learner_answer_md=answer, rubric=rubric
        )
    except GradingValidationError as exc:
        return {"status": "invalid", "error": type(exc).__name__}
    maxima = {criterion.id: float(criterion.points) for criterion in rubric.criteria}
    failed = [
        row.criterion_id
        for row in validated.grade.criterion_evidence
        if float(row.points_awarded) + 1e-9 < maxima.get(row.criterion_id, 0.0)
    ]
    unverified = list((run.grading_support or {}).get("unverified_criterion_ids") or [])
    quotes = {
        " ".join(str((row.get("first_divergence") or {}).get("quote") or "").split()).casefold()
        for row in validated.as_record().get("error_attributions") or []
    }
    return {
        "status": "graded",
        "score": float(validated.grade.rubric_score),
        "max_points": float(rubric.max_points),
        "failed_criteria": failed,
        "unverified_criteria": unverified,
        "negative_criteria": [cid for cid in failed if cid not in unverified],
        "quotes": sorted(quote for quote in quotes if quote),
        "prompt_version": run.prompt_version,
    }


def run_pfc(
    vault: LoadedVault,
    repository: Repository,
    *,
    plan: Mapping[str, Any],
    generator_client: Any,
    grading_client: Any,
    caps: SpendCaps = DEFAULT_CAPS,
    price_per_million: float | None = None,
    cancelled: Callable[[], bool] | None = None,
    record_judgments: bool = True,
) -> dict[str, Any]:
    spend = ReviewSpend(caps, cancelled=cancelled, price_per_million=price_per_million, config=vault.config)
    spend.register("diagnosis_generator", generator_client)
    spend.register("grading", grading_client)
    statuses: Counter = Counter()
    alt_rows: list[dict[str, Any]] = []
    real_rows: list[dict[str, Any]] = []
    judgments: list[dict[str, Any]] = []
    with spend.collector.observing():
        for item_id in plan["items"]:
            item = vault.practice_items[item_id]
            prompt = valid_alternative_prompt(vault, item)
            try:
                with spend.request("diagnosis_generator", "pfc_valid_alternative", input_tokens=_tokens(prompt)):
                    draft = request_valid_alternative(generator_client, prompt)
            except Exception as exc:  # noqa: BLE001 - one item never stops the report
                if exc.__class__.__name__ in {"SpendLimitExceeded", "SpendCancelled"}:
                    raise
                statuses["generator_failed"] += 1
                continue
            verdict = verify_alternative(item, draft)
            judgments.append(
                {
                    "task": "reference_verified",
                    "left_kind": "practice_item",
                    "left_id": item_id,
                    "judge": "verifier",
                    "input_hash": content_key({"pfc": "valid_alternative", "item": item_id, "derivation": draft.derivation_md}),
                    "verdict": "pass" if verdict.get("status") == "verified" else "fail",
                    "rationale": f"valid alternative: {verdict.get('status')} ({verdict.get('reason') or verdict.get('method')})",
                }
            )
            if verdict.get("status") != "verified":
                statuses["alternative_unverified"] += 1
                continue
            statuses["alternative_verified"] += 1
            row = {"item_id": item_id}
            for arm in ARMS:
                try:
                    row[arm] = _grade(
                        vault, grading_client, spend,
                        item_id=item_id, attempt_id=f"pfc_{new_ulid()}", answer=draft.derivation_md, arm=arm,
                    )
                except Exception as exc:  # noqa: BLE001
                    if exc.__class__.__name__ in {"SpendLimitExceeded", "SpendCancelled"}:
                        raise
                    row[arm] = {"status": "failed", "error": type(exc).__name__}
                graded = row[arm]
                if graded.get("status") == "graded":
                    judgments.append(
                        {
                            "task": "valid_alternative_grade",
                            "left_kind": "practice_item",
                            "left_id": item_id,
                            "judge": "llm",
                            "judge_model": str(getattr(grading_client, "model", None) or "unknown"),
                            "prompt_version": graded["prompt_version"],
                            "input_hash": content_key({"pfc": arm, "item": item_id, "derivation": draft.derivation_md}),
                            "verdict": "fail" if graded["score"] + 1e-9 < graded["max_points"] else "pass",
                            "score": graded["score"] / max(graded["max_points"], 1.0),
                            "rationale": f"pf-c {arm}: verified valid alternative graded",
                        }
                    )
            alt_rows.append(row)
        for attempt_id in plan["real_attempts"]:
            attempt = repository.fetch_practice_attempt(attempt_id) or {}
            adjudications = repository.list_diagnosis_adjudications(active_only=True, attempt_ids=[attempt_id])
            anchor = next(
                (
                    row.get("adjudicated_anchor")
                    for row in adjudications
                    if str(row.get("adjudicator_source") or "") == "human_owner" and row.get("adjudicated_anchor")
                ),
                None,
            )
            wanted = " ".join(str((anchor or {}).get("quote") or "").split()).casefold()
            row = {"attempt_id": attempt_id}
            for arm in ARMS:
                try:
                    graded = _grade(
                        vault, grading_client, spend,
                        item_id=str(attempt["practice_item_id"]), attempt_id=attempt_id,
                        answer=str(attempt.get("learner_answer_md") or ""), arm=arm,
                    )
                except Exception as exc:  # noqa: BLE001
                    if exc.__class__.__name__ in {"SpendLimitExceeded", "SpendCancelled"}:
                        raise
                    graded = {"status": "failed", "error": type(exc).__name__}
                graded["anchor_hit"] = bool(wanted) and any(wanted in quote or quote in wanted for quote in graded.get("quotes") or [])
                row[arm] = graded
            real_rows.append(row)
    if record_judgments and judgments:
        from learnloop.db.stores.judgments import append_judgment

        with repository.atomic():
            connection = repository.connection()
            for judgment in judgments:
                append_judgment(connection, **judgment)
    return summarize_pfc(alt_rows, real_rows, statuses=statuses, spend=spend.summary(), plan=plan, vault=vault)


def summarize_pfc(
    alt_rows: Sequence[Mapping[str, Any]],
    real_rows: Sequence[Mapping[str, Any]],
    *,
    statuses: Mapping[str, int],
    spend: Mapping[str, Any],
    plan: Mapping[str, Any],
    vault: LoadedVault,
) -> dict[str, Any]:
    arms: dict[str, Any] = {}
    for arm in ARMS:
        graded = [row[arm] for row in alt_rows if (row.get(arm) or {}).get("status") == "graded"]
        real = [row[arm] for row in real_rows if (row.get(arm) or {}).get("status") == "graded"]
        arms[arm] = {
            "prompt_version": ARM_PROMPTS[arm],
            "valid_alternative_false_rejection": wilson(
                sum(1 for row in graded if row["score"] + 1e-9 < row["max_points"]), len(graded)
            ),
            "valid_alternative_negative_evidence": wilson(
                sum(1 for row in graded if row["negative_criteria"]), len(graded)
            ),
            "unverified_recorded": sum(1 for row in graded if row["unverified_criteria"]),
            "real_anchor_accuracy": wilson(sum(1 for row in real if row["anchor_hit"]), len(real)),
            "graded_alternatives": len(graded),
            "graded_real": len(real),
        }
    paired = [
        row for row in alt_rows
        if all((row.get(arm) or {}).get("status") == "graded" for arm in ARMS)
    ]
    flips = Counter(
        (
            "rejected" if row["before"]["score"] + 1e-9 < row["before"]["max_points"] else "accepted",
            "rejected" if row["after"]["score"] + 1e-9 < row["after"]["max_points"] else "accepted",
        )
        for row in paired
    )
    return {
        "report_version": PFC_REPORT_VERSION,
        "manifest": {
            "algorithm_version": vault.config.algorithms.algorithm_version,
            "seed": plan.get("seed"),
            "items_planned": len(plan.get("items") or []),
            "real_attempts_planned": len(plan.get("real_attempts") or []),
            "grading_support": bool(getattr(getattr(vault.config, "diagnosis", None), "grading_support", True)),
        },
        "statuses": dict(statuses),
        "arms": arms,
        "paired_transitions": {f"{left}->{right}": count for (left, right), count in sorted(flips.items())},
        "spend": dict(spend),
        "noise_floor": "single run; rerun with another --seed for the run-to-run spread (O10: no thresholds)",
    }


def render_pfc_markdown(report: Mapping[str, Any]) -> str:
    def fmt(rate: Mapping[str, Any]) -> str:
        if rate.get("rate") is None:
            return "n/a (n=0)"
        return f"{rate['rate']:.2f} [{rate['low']:.2f}, {rate['high']:.2f}] (n={rate['n']})"

    lines = [
        "# PF-c grading support: before vs after",
        "",
        f"{report['report_version']}; aggregates only. Before = {ARM_PROMPTS['before']}, after = {ARM_PROMPTS['after']}.",
        "",
        f"- statuses {json.dumps(report['statuses'], sort_keys=True)}",
    ]
    for arm in ARMS:
        values = report["arms"][arm]
        lines += [
            f"- **{arm}**: valid-alternative false rejection {fmt(values['valid_alternative_false_rejection'])}; "
            f"negative evidence {fmt(values['valid_alternative_negative_evidence'])}; "
            f"real adjudicated anchor accuracy {fmt(values['real_anchor_accuracy'])}",
        ]
    lines += [
        f"- paired transitions {json.dumps(report['paired_transitions'], sort_keys=True)}",
        f"- spend {json.dumps(report['spend'].get('charged'), sort_keys=True)}",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "ARMS",
    "DEFAULT_CAPS",
    "PFC_REPORT_VERSION",
    "estimate_pfc",
    "plan_pfc",
    "render_pfc_markdown",
    "run_pfc",
    "summarize_pfc",
]
