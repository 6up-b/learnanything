"""The E0 report template (spec §11 "E0 report"): aggregates only.

Sections, in order: status and denominators; the baseline handoff; the
corpus; the bank and labels (κ, confusion table, audit counts); paired
delivery results (D0-D3); paired retrieval results (R0-R5, the matched-unit
screen apart from the system arms); blind answers for the finalists; tokens,
latency and bills per arm (the E0 ledger); the failure ledger with original
denominators; the S1-S4 decisions; the adoption statement.

``results`` may be partial (a dry run, a budget stop, a blocked arm): every
missing section renders as "not run" with its reason, so an incomplete run
is reported as incomplete, never as a smaller complete one. Nothing here
carries question text, passage text, vectors or labels: those stay in the
private run directory under ``fixtures-local``.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
from typing import Any

from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.stop_rules import incomplete_rules, summarize_decisions

_PRIVATE_KEYS = frozenset({"question", "text", "passage", "quote", "selection_quote_md", "vectors", "embedding",
                           "labels", "answer", "context", "title"})


def assert_aggregate(value: Any, path: str = "") -> None:
    """Refuse a report payload that carries a private field (fail closed)."""

    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _PRIVATE_KEYS:
                raise ValueError(f"private field {path + '.' + str(key)} in a public E0 report")
            assert_aggregate(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            assert_aggregate(item, f"{path}[{index}]")


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _interval(result: Mapping[str, Any] | None) -> str:
    if not result or result.get("difference") is None:
        return "not scored"
    low, high = result["ci95"]
    flag = " (exploratory)" if result.get("exploratory") else ""
    return (f"{result['difference']:+.3f} [{low:+.3f}, {high:+.3f}], n={result['n']}, "
            f"families={result['clusters']}{flag}")


def render(results: Mapping[str, Any]) -> str:
    """The Markdown report for ``results`` (see the module docstring)."""

    assert_aggregate(results)
    status = results.get("status", "not_run")
    lines = ["# E0 report: contextual source embeddings (hosted, no GPU)", "",
             f"**Status:** {status}. Run `{results.get('run_id', 'n/a')}`, harness {pins.HARNESS_VERSION}.", ""]
    if status != "complete":
        lines += [f"**Incomplete:** {results.get('incomplete_reason', 'no results yet')}. Every table below keeps its "
                  "original denominator; missing work is listed in the failure ledger.", ""]
    planned = results.get("planned") or {}
    lines += ["## Planned work and what was done", "",
              f"- Development seeds {_fmt(planned.get('development_seeds'))}, written "
              f"{_fmt(planned.get('development_written'))}; questions {_fmt(planned.get('questions'))}, labelled "
              f"{_fmt(planned.get('labelled'))}; answers planned {_fmt(planned.get('answers'))}, made "
              f"{_fmt(planned.get('answers_made'))}.",
              f"- Missing: {_fmt(planned.get('missing') or 'none')}.", ""]
    baseline = results.get("baseline") or {}
    lines += ["## Baseline handoff", "",
              f"- Delivery fixes: `{pins.DELIVERY_FIXES['merge_commit']}` ({pins.DELIVERY_FIXES['review']}).",
              f"- Extraction engines: {_fmt(baseline.get('extraction_engines'))}.",
              f"- D0/D1 reproduced: {_fmt(baseline.get('d0_d1_reproduced'))}.",
              f"- Dense coverage: {_fmt(baseline.get('dense_coverage'))}.", ""]
    corpus = results.get("corpus") or []
    lines += ["## Corpus", "", "| Vault | Sources | Units | Windows | Unit tokens | Withheld |", "|---|---|---|---|---|---|"]
    for entry in corpus:
        lines.append(f"| {entry.get('vault')} | {len(entry.get('sources', []))} | {entry.get('units')} | "
                     f"{entry.get('windows')} | {entry.get('unit_tokens')} | "
                     f"{json.dumps(entry.get('policy', {}).get('withheld', {}), sort_keys=True)} |")
    if not corpus:
        lines.append("| not run | | | | | |")
    labels = results.get("label_quality") or {}
    agreement = labels.get("agreement") or {}
    lines += ["", "## Bank and labels", "",
              f"- Questions by slice: {_fmt(results.get('bank', {}).get('by_slice'))}.",
              f"- Cohen's kappa (relevance): {_fmt(agreement.get('kappa'))}; weighted "
              f"{_fmt(agreement.get('weighted_kappa'))}; n={_fmt(agreement.get('n'))}.",
              f"- Confusion ({', '.join(agreement.get('categories', []))}): {_fmt(agreement.get('confusion'))}.",
              f"- Set agreement: {_fmt(labels.get('set_agreement'))}; adjudicated: {_fmt(labels.get('adjudicated'))}; "
              f"model-only: {_fmt(labels.get('model_only'))}; owner-reviewed: {_fmt(labels.get('owner_reviewed', 0))}; "
              f"unresolved: {_fmt(labels.get('unresolved'))}.", ""]
    lines += ["## Delivery (D0-D3, same tutor)", "", "| Comparison | Answer pass, paired difference |", "|---|---|"]
    delivery = dict(results.get("delivery") or {})
    does_not_fit = delivery.pop("does_not_fit", None)
    for name, result in sorted(delivery.items()):
        lines.append(f"| {name} | {_interval(result)} |")
    if not delivery:
        lines.append("| not run | |")
    lines += ["", f"- does_not_fit (answered by the named bounded fallback, reported apart, never paired as "
                  f"whole context): {_fmt(does_not_fit)}."]
    checks = results.get("latency_checks") or {}
    for name, check in sorted(checks.items()):
        lines.append(f"- Latency {name}: p50/p95 {_fmt(check.get('p50'))}/{_fmt(check.get('p95'))} s vs incumbent "
                     f"{_fmt(check.get('incumbent_p50'))}/{_fmt(check.get('incumbent_p95'))} s (paired "
                     f"{_fmt(check.get('paired'))}); deadline {_fmt(check.get('deadline_s'))} s; regression "
                     f"{_fmt(check.get('regression'))}; ok {_fmt(check.get('ok'))}.")
    lines += ["", "## Retrieval (Complete Evidence@10 on common units; primary development slice, where the "
                  "finalists are chosen)", "",
              "| Arm | CE@10 | Support R@10 | Answer R@10 | nDCG@10 | MRR | Unknown share | Scored / total |",
              "|---|---|---|---|---|---|---|---|"]
    for arm, row in sorted((results.get("retrieval") or {}).items()):
        lines.append(f"| {arm} | {_fmt(row.get('ce10'))} | {_fmt(row.get('support10'))} | {_fmt(row.get('answer10'))} | "
                     f"{_fmt(row.get('ndcg10'))} | {_fmt(row.get('mrr'))} | {_fmt(row.get('unknown'))} | "
                     f"{row.get('scored', 0)} / {row.get('total', 0)} |")
    if not results.get("retrieval"):
        lines.append("| not run | | | | | | | |")
    slices = results.get("retrieval_slices") or {}
    names = [name for name in ("primary_development", "development_all", "logged", "direct_lookup", "no_support")
             if name in slices]
    if names:
        lines += ["", "| Arm | " + " | ".join(f"{name} CE@10 (scored/total)" for name in names) + " |",
                  "|---|" + "---|" * len(names)]
        for arm in sorted({arm for name in names for arm in slices[name]}):
            cells = []
            for name in names:
                row = slices[name].get(arm) or {}
                cells.append(f"{_fmt(row.get('ce10'))} ({row.get('scored', 0)}/{row.get('total', 0)})")
            lines.append(f"| {arm} | " + " | ".join(cells) + " |")
    lines += ["", "| Paired comparison | Difference [95% CI] |", "|---|---|"]
    for name, result in sorted((results.get("paired") or {}).items()):
        lines.append(f"| {name} | {_interval(result)} |")
    systems = results.get("system_arms") or {}
    if systems:
        lines += ["", "| System arm | Interface | Ranked / questions | Missing | Pages | Verification | Dense used |",
                  "|---|---|---|---|---|---|---|"]
        for arm, row in sorted(systems.items()):
            lines.append(f"| {arm} | {row.get('interface')} | {row.get('ranked')} / {row.get('questions')} | "
                         f"{_fmt(row.get('missing') or 'none')} | {_fmt(row.get('pages'))} | "
                         f"{_fmt(row.get('verification'))} | {row.get('dense_used')} |")
    lines += ["", "## Blind answers (finalists, D1)", "", "| Arm | Pass all criteria | Correct | Assumptions | "
              "Citations entailed | Abstention |", "|---|---|---|---|---|---|"]
    for arm, row in sorted((results.get("answers") or {}).items()):
        lines.append(f"| {arm} | {_fmt(row.get('pass'))} | {_fmt(row.get('correct'))} | {_fmt(row.get('assumptions'))} "
                     f"| {_fmt(row.get('citations'))} | {_fmt(row.get('abstention'))} |")
    if not results.get("answers"):
        lines.append("| not run | | | | | |")
    ledger = results.get("ledger") or {}
    lines += ["", "## Tokens, latency and bills", "",
              f"- Committed ${_fmt(ledger.get('committed_usd'))} of ${pins.E0_CAP_USD:.0f}; outstanding reservations "
              f"${_fmt(ledger.get('outstanding_reservations_usd'))}; requests {_fmt(ledger.get('requests'))}; "
              f"refusals {_fmt(ledger.get('refusals'))}.",
              "", "| Arm / category | Requests | Committed $ | Input tokens | Output tokens | Latency s |",
              "|---|---|---|---|---|---|"]
    for arm, row in sorted((ledger.get("by_arm") or {}).items()):
        lines.append(f"| {arm} | {row['requests']} | {row['committed_usd']:.4f} | {row['input_tokens']} | "
                     f"{row['output_tokens']} | {row['latency_s']:.1f} |")
    lines += ["", "## Failure ledger (original denominators)", "", "| Item | Kind | Reason | Denominator |",
              "|---|---|---|---|"]
    for row in results.get("failures") or []:
        lines.append(f"| {row.get('item')} | {row.get('kind')} | {row.get('reason')} | {row.get('denominator')} |")
    if not results.get("failures"):
        lines.append("| none recorded | | | |")
    decisions = results.get("decisions") or incomplete_rules()
    lines += ["", "## Stop rules (computed by code; thresholds fixed before results)", ""]
    lines += [f"- {line}" for line in summarize_decisions(decisions)]
    lines += ["", "Passing E0 is not production authorization: a second production space needs independent "
              "confirmation and the owner's explicit D6 amendment (spec §7).", ""]
    return "\n".join(lines)


def failure_rows(blocked: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [{"item": row.get("arm") or row.get("item"), "kind": row.get("kind", "blocked"),
             "reason": row.get("reason"), "denominator": row.get("denominator")} for row in blocked]
