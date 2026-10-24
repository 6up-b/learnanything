"""The E1 report (aggregates only; refuses private fields like E0's)."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from learnloop.experiments.contextual_embeddings.report import assert_aggregate


def _f(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}" if isinstance(value, float) else str(value)


def _pair(result: Mapping[str, Any] | None) -> str:
    if not result or result.get("difference") is None:
        return "not scored"
    low, high = result["ci95"]
    return (f"{result['difference']:+.3f} [{low:+.3f}, {high:+.3f}], n={result['n']}, families={result['clusters']}"
            + (" (exploratory)" if result.get("exploratory") else ""))


def render(results: Mapping[str, Any]) -> str:
    assert_aggregate(results)
    decision = results.get("decision") or {}
    lines = [f"# E1 report {results.get('plan_id')} ({results.get('status')})", "",
             f"E0 run: {results.get('e0_run_id')}. Decision: **{decision.get('e1')}**"
             + (f" ({'; '.join(decision.get('reasons') or [])})" if decision.get("reasons") else "") + ".",
             f"Production adoption: {decision.get('production_adoption')}.", ""]
    local = results.get("local") or {}
    lines += ["## Local run", "", f"Processes: {local.get('processes')} ({local.get('statuses')}); "
              f"wall {local.get('wall_s')} s; GPU meter {results.get('gpu_meter')}.",
              f"Load: {local.get('load')}.", f"Smoke: {local.get('smoke')}.", f"Profile: {local.get('profile')}.",
              f"Peaks: {local.get('peaks')}; device {local.get('device_peak')}; unload {local.get('unload')}.",
              f"Documents {local.get('documents')}; queries {local.get('queries')}.", ""]
    lines += ["## Comparisons (primary development slice, paired, family-clustered)", ""]
    for name, value in (results.get("comparisons") or {}).items():
        lines.append(f"- {name}: {_pair(value)}")
    lines += ["", f"v2 arm selected on the same slice: {results.get('v2_selected_on_primary_development')}.", ""]
    for label, item in sorted((results.get("copies") or {}).items()):
        lines += [f"## {label}", "", f"Finalists: {item.get('finalists')}; best frozen: {item.get('best_frozen')}; "
                  f"replay reproduced E0: {item.get('replay_ok')}; E0 S1: {item.get('e0_s1')}.", "",
                  "| Arm | CE@10 | Support@10 | Answer@10 | nDCG@10 | MRR | Unknown | Scored |", "|---|---|---|---|---|---|---|---|"]
        for arm, row in sorted((item.get("retrieval") or {}).items()):
            lines.append(f"| {arm} | {_f(row.get('ce10'))} | {_f(row.get('support10'))} | {_f(row.get('answer10'))} | "
                         f"{_f(row.get('ndcg10'))} | {_f(row.get('mrr'))} | {_f(row.get('unknown'))} | "
                         f"{row.get('scored')}/{row.get('total')} |")
        lines += ["", f"Supplementary labels: {item.get('supplement')}; merged: {item.get('merged')}.", ""]
    lines += [f"Spend: {results.get('spend')}.", ""]
    return "\n".join(lines)
