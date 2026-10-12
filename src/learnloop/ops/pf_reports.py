"""PF-b pilot and scaling-check reports (Slice 2 §5.6), run through `learnloop eval`.

Both read persisted pipeline state (``pf_candidates``), verdicts
(``judgment_ledger``), receipts (``model_call_receipts``) and usage signals
(attempts, retirements and affect taps on published items). The only paid step
is the optional blind pairwise LLM judge (``--judge``; route
``pf_selection_judge``), two passes with swapped order and their agreement
reported; every rating appends to ``judgment_ledger`` (task ``pilot_rating``).

* **Pilot / generation-path comparison:** per arm (single-shot, generator
  programs, ensemble) survival per filter, the panel-disagreement rate per
  family, cost per published item, usage signals per item source, and the
  blind comparison of up to 15 survivors against 15 single-shot items. It
  recommends a default path only when the data separate the arms.
* **Scaling check:** the same round run at the configured cheap and frontier
  tiers (``learnloop pf generate --tier``). Per tier: filter survival,
  verified-reference pass rate, judge agreement with verifiers and with undo /
  contest signals, cost, and a blind pairwise rating of up to 10 survivors per
  tier. Per component it says whether quality rises with the model.

Reports are aggregate-only and split by model id. Thin data never blocks a
report; counts, Wilson intervals and exclusions are stated instead.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Mapping
from dataclasses import asdict
import json
import math
from pathlib import Path
from typing import Any

from learnloop.ai.errors import AIInterrupted, AIProviderUnavailable
from learnloop.ai.execution import content_key
from learnloop.ai.spend import SpendCaps, SpendEstimate, SpendLimitExceeded
from learnloop.content.authoring import pf_contracts as C
from learnloop.db.repositories import Repository
from learnloop.db.stores import pf as store
from learnloop.ids import new_ulid
from learnloop.ops.embedding_compare import judge_prediction
from learnloop.ops.pf_calls import (
    PFCaller, PFUnavailable, estimate_tokens, planned_role_clients, resolve_role_clients,
)
from learnloop.ops.pf_generation import FILTER_ORDER
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths

REPORT_VERSION = "pf-reports-v3"
PILOT_PAIRS = 15
SCALING_PAIRS = 10
# Agreed (two-pass) blind comparisons each arm needs, on families both arms
# share, before the pilot recommends a default path.
MIN_AGREED_PAIRS = 5
ARMS = ("single_shot", "generator", "ensemble", "source_anchored")


def wilson(successes: int, total: int, z: float = 1.96) -> list[float] | None:
    if total == 0:
        return None
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [round(max(0.0, centre - margin), 4), round(min(1.0, centre + margin), 4)]


def _rate(successes: int, total: int) -> dict[str, Any]:
    return {"successes": successes, "n": total,
            "rate": round(successes / total, 4) if total else None, "wilson95": wilson(successes, total)}


def _rows(repository: Repository, round_id: str) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        return store.candidates(connection, where="round=?", params=(round_id,))


def _verdicts(repository: Repository, rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Ledgered verdicts per candidate: the authority for every report metric (§5.8)."""
    with repository.connection() as connection:
        return store.candidate_verdicts(connection, [row["id"] for row in rows])


def _survival(rows: list[dict[str, Any]], verdicts: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
    funnel = {}
    for name in FILTER_ORDER:
        evaluated = rejected = 0
        for row in rows:
            verdict = verdicts[row["id"]]["filters"].get(name)
            if verdict is not None:
                evaluated += 1
                rejected += int(verdict == "fail")
        funnel[name] = {"evaluated": evaluated, "rejected": rejected,
                        "survival": round(1 - rejected / evaluated, 4) if evaluated else None}
    return funnel


def _panel_disagreement(rows: list[dict[str, Any]], verdicts: Mapping[str, dict[str, Any]],
                        minimum: int) -> dict[str, Any]:
    per_family: dict[str, list[bool]] = defaultdict(list)
    for row in rows:
        panel = store.verdict_panel(verdicts[row["id"]])
        if panel is not None:
            per_family[row["family_id"]].append(panel[0] < minimum)
    return {family: _rate(sum(values), len(values)) for family, values in sorted(per_family.items())}


def _receipts_cost(repository: Repository, run_ids: set[str]) -> dict[str, Any]:
    if not run_ids:
        return {"calls": 0, "tokens": 0, "metered_usd": 0.0, "estimated_only_usd": None}
    marks = ",".join("?" for _ in run_ids)
    with repository.connection() as connection:
        # Usage lands on the innermost receipt (a transport's child call when it has
        # one), so sum every receipt; only roots count as calls.
        rows = connection.execute(
            f"SELECT input_tokens, output_tokens, cost, usage_json, parent_call_id FROM model_call_receipts "
            f"WHERE owner_kind='pf_generation' AND owner_id IN ({marks})",
            tuple(sorted(run_ids)),
        ).fetchall()
    calls = sum(1 for row in rows if row["parent_call_id"] is None)
    tokens = sum((row["input_tokens"] or 0) + (row["output_tokens"] or 0) for row in rows)
    metered = sum(row["cost"] or 0.0 for row in rows if "estimated_only" not in (row["usage_json"] or ""))
    estimated = [json.loads(row["usage_json"]).get("estimated_usd") for row in rows
                 if row["usage_json"] and "estimated_only" in row["usage_json"]]
    return {"calls": calls, "tokens": tokens, "metered_usd": round(metered, 6),
            "estimated_only_usd": (round(sum(value for value in estimated if value is not None), 6)
                                   if estimated and all(value is not None for value in estimated) else None),
            "estimated_only_calls": len(estimated)}


def usage_signals(repository: Repository, vault: LoadedVault, item_ids: list[str]) -> dict[str, Any]:
    """Attempts, retirements and affect taps on published items (aggregate)."""
    if not item_ids:
        return {"items": 0}
    marks = ",".join("?" for _ in item_ids)
    with repository.connection() as connection:
        attempts = connection.execute(
            f"SELECT COUNT(*) FROM practice_attempts WHERE practice_item_id IN ({marks})", tuple(item_ids),
        ).fetchone()[0]
        taps = connection.execute(
            f"SELECT e.affect_tap_kind, COUNT(*) FROM interaction_events e "
            f"JOIN activity_surfaces s ON s.id = e.surface_id "
            f"WHERE e.kind='affect_tap' AND s.legacy_practice_item_id IN ({marks}) GROUP BY 1",
            tuple(item_ids),
        ).fetchall()
    retired = Counter(
        (vault.practice_items[item_id].status_reason or "unspecified")
        for item_id in item_ids
        if item_id in vault.practice_items and vault.practice_items[item_id].status == "retired"
    )
    return {"items": len(item_ids), "attempts": attempts,
            "retired_by_reason": dict(sorted(retired.items())),
            "affect_taps": {row[0]: row[1] for row in taps}}


class _Judge:
    """The paid blind pairwise judge; two passes with the order swapped."""

    def __init__(self, vault: LoadedVault, repository: Repository, *, caps: SpendCaps,
                 price_per_million: float | None, cancelled: Callable[[], bool] | None,
                 clients: Mapping[str, Any] | None) -> None:
        self.caller = PFCaller(vault, repository, caps=caps, price_per_million=price_per_million,
                               run_id=new_ulid(), owner_kind="pf_reports", cancelled=cancelled)
        self.entry = resolve_role_clients(vault, "pairwise", injected=(clients or {}).get("pairwise"))[0]

    def admit(self, estimate: SpendEstimate) -> None:
        """Admit the whole comparison before any request (unknown metered prices fail closed)."""
        _admit(self.caller, self.entry, estimate)


    def compare(self, left: dict[str, Any], right: dict[str, Any], *, task_label: str) -> dict[str, Any]:
        def side(row: dict[str, Any]) -> dict[str, Any]:
            payload = json.loads(row["payload_json"])
            return {"problem": payload["stem"], "reference": payload["final_answer"],
                    "worked_solution": payload["solution"]}

        verdicts = []
        for order in ((left, right), (right, left)):
            call = self.caller.call(self.entry, prompt=C.pairwise_prompt(a=side(order[0]), b=side(order[1])),
                                    prompt_version=C.PAIRWISE_PROMPT, result_model=C.PairwiseVerdict,
                                    output_tokens=800)

            def mapped(value: str) -> str:
                return "tie" if value == "tie" else ("left" if (value == "A") == (order[0] is left) else "right")

            result = {key: mapped(getattr(call.result, key)) for key in ("preferred", "depth", "accuracy")}
            self.caller.ledger(task="pilot_rating", left_kind="pf_candidate", left_id=left["id"],
                               right_kind="pf_candidate", right_id=right["id"], judge="llm",
                               judge_model=call.model, prompt_version=C.PAIRWISE_PROMPT,
                               input_hash=call.input_hash, verdict=result["preferred"],
                               rationale={"comparison": task_label, "depth": result["depth"],
                                          "accuracy": result["accuracy"],
                                          "order": "left_first" if order[0] is left else "right_first"})
            verdicts.append((call.model, result))
        return {"model": verdicts[0][0], "passes": [verdict for _, verdict in verdicts],
                "family_id": left["family_id"]}


def _admit(caller: PFCaller, entry: Any, estimate: SpendEstimate) -> None:
    """Whole-plan admission for one route's billing class (Codex: estimated only, not capped)."""
    caller.check_shared(estimate)
    budget = caller.subscription if entry.subscription else caller.metered
    budget.check(SpendEstimate(total_tokens=estimate.total_tokens, estimated_usd=estimate.estimated_usd))


def _judge_estimate(vault: LoadedVault, repository: Repository, pairs: int, *, caps: SpendCaps,
                    price_per_million: float | None, clients: Mapping[str, Any] | None,
                    cancelled: Callable[[], bool] | None) -> tuple[SpendEstimate, dict[str, Any], Any]:
    """The blind judge's planned calls, tokens and dollars, admitted without building a client."""
    injected = (clients or {}).get("pairwise")
    entry = (resolve_role_clients(vault, "pairwise", injected=injected) if injected is not None
             else planned_role_clients(vault, "pairwise"))[0]
    caller = PFCaller(vault, repository, caps=caps, price_per_million=price_per_million,
                      run_id=new_ulid(), owner_kind="pf_reports", cancelled=cancelled)
    estimate = _judge_plan(pairs, price_per_million, subscription=entry.subscription)
    rendered = {**asdict(estimate), "billing": "subscription" if entry.subscription else "metered",
                "cost_basis": "estimated_only" if entry.subscription else "metered_caps",
                "provider": entry.provider, "model": entry.model}
    return estimate, rendered, (caller, entry)


def frozen_inputs_key(row: Mapping[str, Any]) -> tuple[str, str | None, str | None]:
    """(family, judged parent contract, family revision): rows comparable as identical inputs."""
    try:
        judged = json.loads(row.get("judged_inputs_json") or "{}")
    except ValueError:
        judged = {}
    return (row["family_id"], judged.get("parent_input_hash"), judged.get("family_revision"))


def _pair_rows(left: list[dict[str, Any]], right: list[dict[str, Any]], limit: int,
               key: Callable[[Mapping[str, Any]], Any] = frozen_inputs_key) -> list[tuple[dict, dict]]:
    """Pairs within the same family and frozen inputs only, spread across families.

    A comparison between different families (or a parent edited between the
    arms) would measure topic mix, not the arms.
    """
    groups: dict[Any, tuple[list[dict], list[dict]]] = defaultdict(lambda: ([], []))
    for side, rows in ((0, left), (1, right)):
        for row in rows:
            groups[key(row)][side].append(row)
    queues = []
    for group in sorted(groups, key=lambda value: json.dumps(value, default=str)):
        lefts, rights = (sorted(rows, key=lambda row: content_key(["pair", row["id"]])) for rows in groups[group])
        queues.append(list(zip(lefts, rights)))
    pairs: list[tuple[dict, dict]] = []
    while len(pairs) < limit and any(queues):
        for queue in queues:
            if queue and len(pairs) < limit:
                pairs.append(queue.pop(0))
    return pairs


def _summarize_pairs(results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        return {"pairs": 0, "families": [], "decisions": []}
    summary: dict[str, Any] = {"pairs": len(results), "by_judge_model": dict(Counter(r["model"] for r in results)),
                               "families": sorted({r["family_id"] for r in results})}
    for key in ("preferred", "depth", "accuracy"):
        agree = [r for r in results if r["passes"][0][key] == r["passes"][1][key]]
        left_wins = sum(1 for r in agree if r["passes"][0][key] == "left")
        right_wins = sum(1 for r in agree if r["passes"][0][key] == "right")
        summary[key] = {"two_pass_agreement": _rate(len(agree), len(results)),
                        "left_wins_when_agreed": left_wins, "right_wins_when_agreed": right_wins,
                        "ties_when_agreed": len(agree) - left_wins - right_wins}
    # Per-pair outcome on the overall preference (ids only): the recommendation
    # counts agreed comparisons on families both arms share.
    summary["decisions"] = [{"family_id": r["family_id"],
                             "agreed": r["passes"][0]["preferred"] == r["passes"][1]["preferred"],
                             "winner": r["passes"][0]["preferred"]} for r in results]
    return summary


def _judge_plan(pairs: int, price_per_million: float | None, *, subscription: bool = False) -> SpendEstimate:
    """Two passes per pair; dollars from the owner price (None when metered and unknown)."""
    side = {"problem": "x" * 1200, "reference": "x" * 300, "worked_solution": "x" * 2400}
    tokens = 2 * pairs * estimate_tokens(C.pairwise_prompt(a=side, b=side), C.PairwiseVerdict, 800)
    if price_per_million is not None:
        usd: float | None = round(tokens * price_per_million / 1_000_000, 8)
    else:
        usd = None if (pairs and not subscription) else 0.0 if not pairs else None
    return SpendEstimate(calls=2 * pairs, total_tokens=tokens, estimated_usd=usd)


def _write(output_dir: Path, name: str, report: dict[str, Any], markdown: str) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    identity = content_key({key: report.get(key) for key in ("round", "kind", "arms", "tiers")})[:16]
    files = [f"{name}-{identity}.json", f"{name}-{identity}.md"]
    (output_dir / files[0]).write_text(json.dumps(report, sort_keys=True, indent=2, default=str), encoding="utf-8")
    (output_dir / files[1]).write_text(markdown, encoding="utf-8")
    return files


def _repository(vault: LoadedVault, writable: bool) -> Repository:
    path = VaultPaths(vault.root, vault.config).sqlite_path
    return Repository(path) if writable else Repository.attach(path, read_only=True)


def _arm_summary(repository: Repository, vault: LoadedVault, rows: list[dict[str, Any]],
                 verdicts: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
    minimum = vault.config.pf.min_agreeing_solves
    published = [row["published_item_id"] for row in rows if row["status"] == "published"]
    cost = _receipts_cost(repository, {row["run_id"] for row in rows})
    per_item = (cost["tokens"] / len(published)) if published else None
    return {
        "candidates": len(rows),
        "by_status": dict(Counter(row["status"] for row in rows)),
        "verified": _rate(sum(1 for row in rows
                              if store.verdict_verified(verdicts[row["id"]], row["generation_path"])), len(rows)),
        "survival_by_filter": _survival(rows, verdicts),
        "survived_all_filters": _rate(sum(1 for row in rows if store.verdict_survived(verdicts[row["id"]])),
                                      len(rows)),
        "panel_disagreement_by_family": _panel_disagreement(rows, verdicts, minimum),
        "verdict_source": "judgment_ledger",
        "by_proposer_model": {model: dict(Counter(row["status"] for row in rows if row["proposer_model"] == model))
                              for model in sorted({row["proposer_model"] or "unknown" for row in rows})},
        "cost": cost,
        "cost_per_published_item": {"tokens": round(per_item, 1) if per_item is not None else None,
                                    "metered_usd": round(cost["metered_usd"] / len(published), 6) if published else None,
                                    "published": len(published)},
        "usage_signals": usage_signals(repository, vault, published),
    }


def pilot_report(vault: LoadedVault, *, round_id: str, output_dir: Path, judge: bool = False,
                 dry_run: bool = False, caps: SpendCaps | None = None, price_per_million: float | None = None,
                 cancelled: Callable[[], bool] | None = None, clients: Mapping[str, Any] | None = None) -> dict[str, Any]:
    caps = caps or SpendCaps()
    repository = _repository(vault, writable=judge and not dry_run)
    rows = [row for row in _rows(repository, round_id) if row["tier"] is None]
    verdicts = _verdicts(repository, rows)
    by_arm = {arm: [row for row in rows if row["generation_path"] == arm] for arm in ARMS}
    report: dict[str, Any] = {"status": "dry_run" if dry_run else "complete", "kind": "pf_pilot",
                              "version": REPORT_VERSION, "round": round_id,
                              "arms": {arm: _arm_summary(repository, vault, arm_rows, verdicts)
                                       for arm, arm_rows in by_arm.items() if arm_rows}}
    single = by_arm["single_shot"]
    comparisons = {arm: _pair_rows([row for row in by_arm[arm] if store.verdict_survived(verdicts[row["id"]])],
                                   single, PILOT_PAIRS)
                   for arm in ("generator", "ensemble") if by_arm[arm] and single}
    report["blind_comparison_plan"] = {arm: len(pairs) for arm, pairs in comparisons.items()}
    refused = False  # the judge plan failed admission: no request, no report file
    if judge:
        try:
            estimate, report["judge_estimate"], (planner, entry) = _judge_estimate(
                vault, repository, sum(len(pairs) for pairs in comparisons.values()), caps=caps,
                price_per_million=price_per_million, clients=clients, cancelled=cancelled)
            _admit(planner, entry, estimate)
        except SpendLimitExceeded as exc:
            report.update(status="over_budget", reason=str(exc))
            refused = True
        except PFUnavailable as exc:
            report.update(status="unavailable", reason=str(exc))
            refused = True
        if not dry_run and not refused:
            try:
                runner = _Judge(vault, repository, caps=caps, price_per_million=price_per_million,
                                cancelled=cancelled, clients=clients)
                runner.admit(estimate)
                report["blind_comparison"] = {
                    arm: {"left": arm, "right": "single_shot",
                          **_summarize_pairs([runner.compare(a, b, task_label=f"{arm}_vs_single_shot")
                                              for a, b in pairs])}
                    for arm, pairs in comparisons.items()}
                report["judge_usage"] = runner.caller.report()
            except (AIInterrupted, KeyboardInterrupt):
                report["status"] = "cancelled"
            except SpendLimitExceeded as exc:
                report.update(status="over_budget", reason=str(exc))
            except (AIProviderUnavailable, PFUnavailable) as exc:
                report.update(status="provider_failed", error_type=type(exc).__name__)
    report["recommendation"] = _recommend(report)
    if not dry_run and not refused:
        report["report_files"] = _write(output_dir, "pf-pilot", report, _pilot_markdown(report))
    return report


def _recommend(report: dict[str, Any]) -> dict[str, Any]:
    """A default path only from usable, agreed blind comparisons on shared families (§5.6).

    Each arm is compared with single-shot items of the same family and frozen
    inputs. Only pairs whose two passes agree count, only on families both
    arms were compared on, and each arm needs ``MIN_AGREED_PAIRS`` of them.
    Programs become the default only when their preference rate over
    single-shot clearly exceeds the ensemble's (Wilson intervals separate);
    otherwise ensemble matches or beats them and is the default (§5.6).
    """
    arms = report.get("arms", {})
    comparison = report.get("blind_comparison") or {}
    if not {"generator", "ensemble"} <= set(arms):
        return {"default_path": None, "reason": "insufficient evidence: both quantitative arms must run"}
    if not comparison:
        return {"default_path": None, "reason": "insufficient evidence: run with --judge for the blind comparison"}
    decisions = {arm: [d for d in (comparison.get(arm) or {}).get("decisions") or [] if d.get("agreed")]
                 for arm in ("generator", "ensemble")}
    common = {d["family_id"] for d in decisions["generator"]} & {d["family_id"] for d in decisions["ensemble"]}
    tallies = {}
    for arm, rows in decisions.items():
        usable = [d for d in rows if d["family_id"] in common]
        tallies[arm] = _rate(sum(1 for d in usable if d["winner"] == "left"), len(usable))
    evidence = {"agreed_pairs_on_shared_families": {arm: tally["n"] for arm, tally in tallies.items()},
                "shared_families": sorted(common), "minimum_agreed_pairs": MIN_AGREED_PAIRS,
                "preferred_over_single_shot": tallies}
    if any(tally["n"] < MIN_AGREED_PAIRS for tally in tallies.values()):
        return {"default_path": None, "reason": "insufficient evidence: too few agreed blind comparisons "
                "on families both arms share", **evidence}
    generator, ensemble = tallies["generator"]["wilson95"], tallies["ensemble"]["wilson95"]
    if generator[0] > ensemble[1]:
        return {"default_path": "generator", "reason": "programs clearly beat ensemble on the blind comparison",
                **evidence}
    return {"default_path": "ensemble",
            "reason": "ensemble matches or beats programs; keep programs for procedural drill", **evidence}


def _pilot_markdown(report: dict[str, Any]) -> str:
    lines = [f"# PF pilot — round {report['round']}", "",
             "| Arm | Candidates | Verified | Survived all filters | Published | Tokens / published |",
             "|---|---|---|---|---|---|"]
    for arm, summary in report.get("arms", {}).items():
        lines.append(f"| {arm} | {summary['candidates']} | {summary['verified']['rate']} | "
                     f"{summary['survived_all_filters']['rate']} | {summary['cost_per_published_item']['published']} | "
                     f"{summary['cost_per_published_item']['tokens']} |")
    for arm, comparison in (report.get("blind_comparison") or {}).items():
        if comparison.get("pairs"):
            preferred = comparison["preferred"]
            lines.append(f"\nBlind comparison {arm} vs single-shot: {comparison['pairs']} pairs; two-pass agreement "
                         f"{preferred['two_pass_agreement']['rate']}; {arm} preferred {preferred['left_wins_when_agreed']}, "
                         f"single-shot {preferred['right_wins_when_agreed']}.")
    lines.append(f"\nRecommendation: {report.get('recommendation')}")
    lines.append("\nAggregates only; verdicts are in judgment_ledger (task pilot_rating).")
    return "\n".join(lines) + "\n"


def scaling_report(vault: LoadedVault, *, round_id: str, output_dir: Path, judge: bool = False,
                   dry_run: bool = False, caps: SpendCaps | None = None, price_per_million: float | None = None,
                   cancelled: Callable[[], bool] | None = None, clients: Mapping[str, Any] | None = None) -> dict[str, Any]:
    caps = caps or SpendCaps()
    repository = _repository(vault, writable=judge and not dry_run)
    rows = _rows(repository, round_id)
    verdicts = _verdicts(repository, rows)
    tiers = {tier: [row for row in rows if row["tier"] == tier] for tier in ("cheap", "frontier")}
    report: dict[str, Any] = {"status": "dry_run" if dry_run else "complete", "kind": "pf_scaling",
                              "version": REPORT_VERSION, "round": round_id,
                              "routes": {"cheap": list(vault.config.pf.scaling.cheap),
                                         "frontier": list(vault.config.pf.scaling.frontier)},
                              "tiers": {}}
    for tier, tier_rows in tiers.items():
        summary = _arm_summary(repository, vault, tier_rows, verdicts)
        summary["judge_agreement"] = _judge_agreement(repository, vault, tier_rows)
        summary["by_path"] = {path: _rate(sum(1 for row in tier_rows if row["generation_path"] == path
                                              and store.verdict_verified(verdicts[row["id"]], path)),
                                          sum(1 for row in tier_rows if row["generation_path"] == path))
                              for path in sorted({row["generation_path"] for row in tier_rows})}
        report["tiers"][tier] = summary
    survivors = {tier: [row for row in tier_rows if store.verdict_survived(verdicts[row["id"]])
                        and store.verdict_verified(verdicts[row["id"]], row["generation_path"])]
                 for tier, tier_rows in tiers.items()}
    # Identical inputs: the same family, frozen parent/family inputs and path.
    pairs = _pair_rows(survivors["frontier"], survivors["cheap"], SCALING_PAIRS,
                       key=lambda row: (*frozen_inputs_key(row), row["generation_path"]))
    report["blind_comparison_plan"] = {"pairs": len(pairs)}
    refused = False  # the judge plan failed admission: no request, no report file
    if judge:
        try:
            estimate, report["judge_estimate"], (planner, entry) = _judge_estimate(
                vault, repository, len(pairs), caps=caps, price_per_million=price_per_million,
                clients=clients, cancelled=cancelled)
            _admit(planner, entry, estimate)
        except SpendLimitExceeded as exc:
            report.update(status="over_budget", reason=str(exc))
            refused = True
        except PFUnavailable as exc:
            report.update(status="unavailable", reason=str(exc))
            refused = True
        if not dry_run and not refused:
            try:
                runner = _Judge(vault, repository, caps=caps, price_per_million=price_per_million,
                                cancelled=cancelled, clients=clients)
                runner.admit(estimate)
                report["blind_comparison"] = {"left": "frontier", "right": "cheap", **_summarize_pairs(
                    [runner.compare(a, b, task_label="frontier_vs_cheap") for a, b in pairs])}
                report["judge_usage"] = runner.caller.report()
            except (AIInterrupted, KeyboardInterrupt):
                report["status"] = "cancelled"
            except SpendLimitExceeded as exc:
                report.update(status="over_budget", reason=str(exc))
            except (AIProviderUnavailable, PFUnavailable) as exc:
                report.update(status="provider_failed", error_type=type(exc).__name__)
    report["judge_accuracy_on_labelled_pairs"] = {"freshness": _labelled_judge_accuracy(repository)}
    report["components"] = _components(report)
    if not dry_run and not refused:
        report["report_files"] = _write(output_dir, "pf-scaling", report, _scaling_markdown(report))
    return report


def _judge_agreement(repository: Repository, vault: LoadedVault, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Judge behaviour on this tier's own candidates, and usage signals (Slice 2 §5.6).

    Both judge rates here are **descriptive only**, never judge accuracy or
    quality, and never rank a tier:

    * the share of program draws the structure judge calls ``isomorph``: the
      program verifies invariance, but every label is positive, so a judge that
      always says ``isomorph`` scores 1.0;
    * the share of fingerprint-suspect pairs the freshness judge accepts as
      ``same_surface`` / ``isomorph``: suspicion (a shared answer or technique
      sequence) is not verified equivalence, so a higher rate is not better.

    Judge accuracy comes from independently labelled pairs judged at both
    tiers (:func:`_labelled_judge_accuracy`). Undo / contest: the share of
    published items later retired or tapped ``misgraded`` / ``ambiguous``.
    """
    ids = [row["id"] for row in rows]
    if not ids:
        return {}
    marks = ",".join("?" for _ in ids)
    with repository.connection() as connection:
        verdicts = connection.execute(
            f"SELECT left_id, judge, prompt_version, verdict, rationale FROM judgment_ledger "
            f"WHERE task='isomorph' AND left_kind='pf_candidate' AND left_id IN ({marks})", tuple(ids),
        ).fetchall()
    path_of = {row["id"]: row["generation_path"] for row in rows}
    structure = [v for v in verdicts if v["prompt_version"] == C.STRUCTURE_PROMPT and path_of.get(v["left_id"]) == "generator"]
    suspects = [v for v in verdicts if v["prompt_version"] == C.FRESHNESS_PROMPT
                and json.loads(v["rationale"] or "{}").get("suspect_keys")]
    published = [row["published_item_id"] for row in rows if row["status"] == "published"]
    signals = usage_signals(repository, vault, published)
    contested = sum(signals.get("retired_by_reason", {}).values()) + sum(
        count for kind, count in signals.get("affect_taps", {}).items() if kind in {"misgraded", "ambiguous"})
    return {
        "descriptive": {
            "note": "descriptive only: not judge accuracy or quality; never compared across tiers",
            "structure_isomorph_rate_on_program_draws": _rate(
                sum(1 for v in structure if v["verdict"] == "isomorph"), len(structure)),
            "freshness_suspect_acceptance": _rate(
                sum(1 for v in suspects if v["verdict"] in {"same_surface", "isomorph"}), len(suspects)),
        },
        "undo_or_contest_on_published": _rate(min(contested, len(published)), len(published)),
    }


def _labelled_judge_accuracy(repository: Repository) -> dict[str, Any]:
    """Each tier's freshness judge against B2's independent labels, on identical pairs.

    Reads the B2 judge view's ledgered verdicts (``learnloop embeddings compare
    --suite b2 --view judge --tier cheap|frontier``). A verdict counts only
    through its ``case_identity`` (benchmark revision, case id, both pair
    inputs and the label), and only identities both tiers judged are scored,
    so the tiers face the same pairs and the same labels; verdicts without an
    identity are excluded. A missing verdict is an abstention: it is never a
    correct answer, it counts against accuracy and recall, and coverage is
    reported per tier.
    """
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT left_id, verdict, rationale FROM judgment_ledger WHERE task='isomorph' "
            "AND left_kind='b2_case' AND prompt_version=? ORDER BY rowid", (C.FRESHNESS_PROMPT,),
        ).fetchall()
    latest: dict[str, dict[str, tuple[bool | None, bool]]] = {"cheap": {}, "frontier": {}}
    without_identity = 0
    for row in rows:
        rationale = json.loads(row["rationale"] or "{}")
        tier, label, identity = rationale.get("tier"), rationale.get("label"), rationale.get("case_identity")
        if tier in latest and label in {"positive", "negative"}:
            if not identity:
                without_identity += 1
                continue
            latest[tier][identity] = (judge_prediction(row["verdict"]), label == "positive")
    shared = sorted(identity for identity in set(latest["cheap"]) & set(latest["frontier"])
                    if latest["cheap"][identity][1] == latest["frontier"][identity][1])
    result: dict[str, Any] = {"source": "b2 judge view (independent labels)", "pairs_judged_at_both_tiers": len(shared),
                              "matched_by": "case_identity (benchmark revision, case id, both pair inputs, label)",
                              "excluded_without_identity": without_identity}
    for tier, judged in latest.items():
        outcomes = [judged[identity] for identity in shared]
        answered = [(predicted, label) for predicted, label in outcomes if predicted is not None]
        correct = sum(1 for predicted, label in answered if predicted == label)
        positives = [predicted for predicted, label in outcomes if label]
        answered_negatives = [predicted for predicted, label in answered if not label]
        result[tier] = {"accuracy": _rate(correct, len(outcomes)),
                        "coverage": _rate(len(answered), len(outcomes)),
                        "abstained": len(outcomes) - len(answered),
                        "recall_on_positives": _rate(sum(1 for predicted in positives if predicted is True),
                                                     len(positives)),
                        "false_positive_rate": _rate(sum(answered_negatives), len(answered_negatives))}
    return result


def _tier_verdict(cheap: dict[str, Any], frontier: dict[str, Any]) -> str:
    if not cheap.get("n") or not frontier.get("n") or min(cheap["n"], frontier["n"]) < 10:
        return "insufficient_data"
    if frontier["wilson95"][0] > cheap["wilson95"][1]:
        return "rises_with_tier"
    if frontier["wilson95"][1] < cheap["wilson95"][0]:
        return "falls_with_tier"
    return "no_clear_difference"


def _components(report: dict[str, Any]) -> dict[str, Any]:
    tiers = report["tiers"]
    labelled = (report.get("judge_accuracy_on_labelled_pairs") or {}).get("freshness") or {}
    if not tiers.get("cheap", {}).get("candidates") or not tiers.get("frontier", {}).get("candidates"):
        return {"status": "insufficient_data", "reason": "run the same round at both tiers",
                "freshness_judge": _tier_verdict((labelled.get("cheap") or {}).get("accuracy") or {},
                                                 (labelled.get("frontier") or {}).get("accuracy") or {})}

    labelled = (report.get("judge_accuracy_on_labelled_pairs") or {}).get("freshness") or {}
    result = {
        "generators_verified_pass_rate": _tier_verdict(tiers["cheap"]["verified"], tiers["frontier"]["verified"]),
        "generators_survival": _tier_verdict(tiers["cheap"]["survived_all_filters"],
                                             tiers["frontier"]["survived_all_filters"]),
        # No independently labelled pairs for the structure judge exist at both
        # tiers; its isomorph rate on program draws is descriptive only.
        "structure_judge": "insufficient_data",
        "freshness_judge": _tier_verdict((labelled.get("cheap") or {}).get("accuracy") or {},
                                         (labelled.get("frontier") or {}).get("accuracy") or {}),
    }
    comparison = report.get("blind_comparison") or {}
    if comparison.get("pairs"):
        preferred = comparison["preferred"]
        result["blind_pairwise"] = ("frontier_preferred" if preferred["left_wins_when_agreed"] > preferred["right_wins_when_agreed"]
                                    else "cheap_preferred" if preferred["right_wins_when_agreed"] > preferred["left_wins_when_agreed"]
                                    else "no_preference")
    result["note"] = ("A component whose quality does not rise with the tier is where hand-built structure may beat "
                      "more compute; verifiers (panel, sandboxed sympy) are held fixed across tiers. Judge components "
                      "are scored only against independent labels on pairs both tiers judged (B2 judge view with "
                      "--tier); suspect acceptance and positive-only agreement are descriptive.")
    return result


def _scaling_markdown(report: dict[str, Any]) -> str:
    lines = [f"# PF scaling check — round {report['round']}", "",
             "| Tier | Candidates | Verified | Survived all filters | Tokens |", "|---|---|---|---|---|"]
    for tier, summary in report["tiers"].items():
        lines.append(f"| {tier} | {summary['candidates']} | {summary['verified']['rate']} | "
                     f"{summary['survived_all_filters']['rate']} | {summary['cost']['tokens']} |")
    lines.append(f"\nComponents: {json.dumps(report.get('components'), sort_keys=True)}")
    lines.append("\nAggregates only; ratings are in judgment_ledger (task pilot_rating).")
    return "\n".join(lines) + "\n"


__all__ = ["pilot_report", "scaling_report", "usage_signals", "wilson"]
