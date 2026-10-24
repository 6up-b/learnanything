"""The E1 plan: inputs, the GPU-hours and dollar estimates, the plan id.

Two sources, one plan shape:

* ``manifest_inputs(e0_run_dir)``: E0's frozen manifests and whatever
  results exist, read-only, with no vault opened (the dry run while E0's
  relabel is still running: the plan is ``provisional``).
* ``import_inputs(layout, replays)``: an E1 import of a FINISHED E0 run,
  replayed and verified (the plan is ``frozen``; only a frozen plan runs).

The plan id (``e1_<16 hex>``) hashes E1's pins, E0's pins, E0's run and plan
digests, its results digests and the counts: a changed input is a new plan.
Estimates use token ESTIMATES (UTF-8 bytes / 3) and the stated assumptions;
admission still reserves each request's hard maximum at the verified price.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.e1 import pins as e1_pins

#: Prompt overhead of a supplementary pass (the rubric, the rule, the frame).
_FRAME_TOKENS = 600
#: A question's context as a labeller reads it (question, selection window).
_QUESTION_TOKENS = 450
#: Per candidate beyond its own text (section path, label, ref).
_CANDIDATE_OVERHEAD = 30
_SONNET = pins.ROLE_PINS["label_a"]
_OPUS = pins.ROLE_PINS["adjudicator"]
_VOYAGE = pins.EMBEDDING_PINS["voyage_context_4"]


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def manifest_inputs(e0_run_dir: Path) -> dict[str, Any]:
    """Counts from E0's frozen manifests (read-only; no vault, no store)."""

    from learnloop.experiments.contextual_embeddings.e1.replay import e0_run_state

    e0_run_dir = Path(e0_run_dir)
    state = e0_run_state(e0_run_dir)
    frozen = e0_run_dir / "frozen"
    plan = json.loads((frozen / "run_plan.json").read_text(encoding="utf-8"))
    corpus = json.loads((frozen / "corpus.json").read_text(encoding="utf-8"))
    maps = json.loads((frozen / "candidate_maps.json").read_text(encoding="utf-8"))
    arms = {row["arm"]: row for row in plan.get("embedding_arms") or []}
    queries_total = int((arms.get("R1") or {}).get("queries") or 0)
    query_tokens_avg = (int((arms.get("R1") or {}).get("query_tokens") or 0) / queries_total) if queries_total else 100
    bank = plan.get("bank") or {}
    vaults = {}
    inventories = {str(item.get("vault")): item for item in corpus}
    for label in state["labels"]:
        inventory = inventories[label]
        entry = (bank.get("vaults") or {}).get(label) or {}
        units = len(maps.get(label) or [])
        smoke = int((entry.get("smoke") or {}).get("count") or 0)
        development = int(entry.get("development_seeds") or 0)
        logged = int((entry.get("logged") or {}).get("eligible") or 0)
        unit_tokens = int(inventory.get("unit_tokens") or 0)
        queries = smoke + development + logged
        vaults[label] = {
            "units": units, "windows": int(inventory.get("windows") or 0), "unit_tokens": unit_tokens,
            "grouped_tokens": unit_tokens + pins.CHUNK_MARKER_TOKENS * units,
            "singleton_tokens": unit_tokens + pins.CHUNK_MARKER_TOKENS * units,
            "queries": queries, "query_tokens": int(round(queries * query_tokens_avg)),
            "labelled_questions": development + logged,
            "unit_tokens_avg": round(unit_tokens / units, 1) if units else 0.0,
        }
    return {"source": "manifests", "e0": _e0_block(state, plan), "vaults": vaults, "gaps": {}, "verification": {}}


def _e0_block(state: Mapping[str, Any], plan: Mapping[str, Any]) -> dict[str, Any]:
    results = state.get("results") or {}
    return {"run_id": state["run_id"], "plan_sha": _sha(plan), "pins_fingerprint": plan.get("pins_fingerprint"),
            "copies": list(state["labels"]), "complete": bool(state.get("complete")),
            "results_sha": {label: (_sha(results[label]) if label in results else None) for label in state["labels"]},
            "status": {label: (results.get(label) or {}).get("status") for label in state["labels"]},
            "finalists": {label: (results.get(label) or {}).get("finalists") for label in state["labels"]},
            "S1": {label: (((results.get(label) or {}).get("decisions") or {}).get("S1") or {}).get("decision")
                   for label in state["labels"]}}


def import_inputs(layout: Any, replays: Sequence[Any]) -> dict[str, Any]:
    """Counts from a verified import's replays (exact documents and queries)."""

    from learnloop.experiments.contextual_embeddings.e1.local import v2_documents, v2_space
    from learnloop.experiments.contextual_embeddings.e1.replay import question_texts

    manifest = layout.manifest()
    plan = layout.plan()
    state = {"run_id": manifest["e0_run_id"], "labels": manifest["labels"], "complete": True,
             "results": {replayed.label: replayed.e0_results for replayed in replays}}
    vaults, gaps, verification = {}, {}, {}
    for replayed in replays:
        snapshot = replayed.snapshot
        tokens = {}
        for arm in e1_pins.V2_ARMS:
            documents, _ = v2_documents(snapshot, v2_space(snapshot, arm))
            tokens[arm] = sum(pins.token_estimate(chunk.text) + pins.CHUNK_MARKER_TOKENS
                              for document in documents for chunk in document.chunks)
        texts = question_texts(replayed)
        unit_tokens = sum(pins.token_estimate(unit.text) for unit in snapshot.units)
        vaults[replayed.label] = {
            "units": len(snapshot.units), "windows": len(snapshot.windows), "unit_tokens": unit_tokens,
            "grouped_tokens": tokens["V2_grouped"], "singleton_tokens": tokens["V2_singleton"],
            "queries": len(texts), "query_tokens": sum(pins.token_estimate(text) for text in texts.values()),
            "labelled_questions": len(replayed.labels), "novelty": e0_novelty(replayed),
            "unit_tokens_avg": round(unit_tokens / len(snapshot.units), 1) if snapshot.units else 0.0,
        }
        gaps[replayed.label] = dict(replayed.gaps)
        verification[replayed.label] = dict(replayed.verification)
    block = _e0_block(state, plan)
    block["import_manifest_sha"] = _sha(manifest)
    return {"source": "import", "e0": block, "vaults": vaults, "gaps": gaps, "verification": verification}


#: The hosted contextual arms whose novelty proxies a new contextual arm's.
NOVELTY_ARMS = ("R4_grouped", "R5_grouped", "R4_singleton", "R5_singleton")


def e0_novelty(replayed: Any) -> dict[str, Any]:
    """How often one of E0's contextual arms ranked, in its top 10, a unit no
    other replayed arm put in its top 20 (nor the writer's proposals): the
    expected new-candidate rate of one more contextual arm. Conservative: E0's
    system arms are left out, and they only add to the pool."""

    from learnloop.experiments.contextual_embeddings.bank import unit_refs

    by_ref = {ref: unit.unit_id for unit in replayed.snapshot.units for ref in unit_refs(unit)}
    counts: list[int] = []
    for question in replayed.questions:
        labels = replayed.labels.get(question.query_id)
        if labels is None or labels.unresolved:
            continue
        for arm in NOVELTY_ARMS:
            if arm not in replayed.rankings:
                continue
            others = {unit for name, ranked in replayed.rankings.items() if name != arm
                      for unit in ranked.get(question.query_id, [])[: pins.POOL_DEPTH]}
            others |= set(question.proposed_units)
            others |= {by_ref[ref] for evidence in question.evidence_sets for ref in evidence.required if ref in by_ref}
            top = replayed.rankings[arm].get(question.query_id, [])[: e1_pins.SUPPLEMENT_DEPTH]
            counts.append(sum(1 for unit in top if unit not in others))
    with_new = [count for count in counts if count]
    return {"questions": len(counts), "p_any": round(len(with_new) / len(counts), 4) if counts else None,
            "mean_new_given_any": round(sum(with_new) / len(with_new), 3) if with_new else 0.0,
            "arms": [arm for arm in NOVELTY_ARMS if arm in replayed.rankings]}


def gpu_estimate(vaults: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    a = e1_pins.ASSUMPTIONS
    tokens = sum(int(item["grouped_tokens"]) + int(item["singleton_tokens"]) for item in vaults.values())
    queries = sum(int(item["queries"]) for item in vaults.values())
    profile_tokens = sum(e1_pins.PROFILE_TOKENS) * e1_pins.PROFILE_REPEATS
    steps = {"load_s": a.load_s, "smoke_s": a.smoke_s,
             "profile_s": round(profile_tokens / 1000 * a.seconds_per_1k_tokens, 1),
             "documents_s": round(tokens / 1000 * a.seconds_per_1k_tokens, 1),
             "queries_s": round(queries * a.query_s, 1)}
    one = sum(steps.values())
    # Worst case: the process fails at the end and runs once more (both charged).
    return {"steps": steps, "document_tokens": tokens, "queries": queries, "processes_expected": 1,
            "expected_hours": round(one / 3600, 3), "worst_case_hours": round(2 * one / 3600, 3),
            "cap_hours": e1_pins.GPU_HOURS_CAP, "fits": 2 * one / 3600 <= e1_pins.GPU_HOURS_CAP,
            "basis": "upper estimates for a pure-torch linear-attention fallback; the meter stops at the cap"}


def _call_usd(pin: Any, tokens_in: float, tokens_out: float) -> float:
    input_price, output_price = pin.prices_for(tokens_in)
    return (tokens_in * input_price + tokens_out * output_price) / 1_000_000


def money_estimate(vaults: Mapping[str, Mapping[str, Any]], gaps: Mapping[str, Mapping[str, Any]] | None = None
                   ) -> dict[str, Any]:
    """Expected and worst-case dollars: the supplementary labels and audits,
    the two model canaries, and any voyage-context-4 fill."""

    a = e1_pins.ASSUMPTIONS
    slots = len(e1_pins.V2_ARMS) * e1_pins.SUPPLEMENT_DEPTH
    rows, expected, worst = {}, {"labels_audits": 0.0, "embeddings": 0.0}, {"labels_audits": 0.0, "embeddings": 0.0}
    for label, item in vaults.items():
        questions = int(item["labelled_questions"])
        size = float(item["unit_tokens_avg"]) + _CANDIDATE_OVERHEAD
        novelty = item.get("novelty") or {}
        # Expected: E0's measured novelty of a contextual arm (leave that arm
        # out of the pool) for each v2 arm, when the import has it; else the
        # stated prior. Worst: every v2 top-10 slot new, every question audited.
        if novelty.get("questions"):
            p_any = 1.0 - (1.0 - float(novelty["p_any"])) ** len(e1_pins.V2_ARMS)
            share = len(e1_pins.V2_ARMS) * float(novelty["mean_new_given_any"]) / slots
        else:
            p_any, share = 1.0, a.new_candidate_share
        for case, share, adjudicated, reached in (("expected", share, a.adjudicated_share, p_any),
                                                  ("worst", 1.0, 1.0, 1.0)):
            new = max(1, math.ceil(slots * share))
            asked = math.ceil(questions * reached)
            tokens_in = _FRAME_TOKENS + _QUESTION_TOKENS + (a.judged_context_units + new) * size
            pass_out = new * a.label_output_tokens_per_candidate + a.set_output_tokens \
                + a.thinking_tokens[_SONNET.model]
            judge_in = tokens_in + 2 * new * 8
            judge_out = new * a.label_output_tokens_per_candidate + a.set_output_tokens + a.thinking_tokens[_OPUS.model]
            passes = 2 * asked * _call_usd(_SONNET, tokens_in, pass_out)
            audits = math.ceil(asked * adjudicated) * _call_usd(_OPUS, judge_in, judge_out)
            target = expected if case == "expected" else worst
            target["labels_audits"] += passes + audits
            rows.setdefault(label, {})[case] = {"questions": questions, "questions_with_new": asked,
                                                "new_candidates_per_question": new,
                                                "basis": "measured_e0_novelty" if novelty.get("questions")
                                                and case == "expected" else "prior",
                                                "pass_usd": round(passes, 4), "audit_usd": round(audits, 4)}
    canaries = _call_usd(_SONNET, 200, 50) + _call_usd(_OPUS, 200, 50)
    for target in (expected, worst):
        target["labels_audits"] += canaries
    fill_expected = fill_worst = 0.0
    for label, item in vaults.items():
        missing = set(((gaps or {}).get(label) or {}).get("arms_missing") or {})
        tokens = int(item["grouped_tokens"]) + int(item["singleton_tokens"]) + int(item["query_tokens"])
        price = _VOYAGE.price_per_million_upper_bound / 1_000_000
        fill_worst += tokens * price
        if missing & set(e1_pins.FILLABLE_ARMS):
            fill_expected += tokens * price
    expected["embeddings"] += fill_expected
    worst["embeddings"] += fill_worst
    return {"by_vault": rows, "expected": {key: round(value, 4) for key, value in expected.items()},
            "worst_case": {key: round(value, 4) for key, value in worst.items()},
            "expected_usd": round(sum(expected.values()), 4), "worst_case_usd": round(sum(worst.values()), 4),
            "cap_usd": e1_pins.E1_CAP_USD,
            "priority": "primary development questions first, then logged, then the other development strata; "
                        "past the cap the rest stays unknown (pool-relative completeness, reported)",
            "basis": "token estimates (bytes/3) at the verified Anthropic and Voyage prices; admission reserves "
                     "each request's hard maximum (max_tokens) before it is sent"}


def build_plan(inputs: Mapping[str, Any], *, keys: Mapping[str, str], prior: Mapping[str, Any]) -> dict[str, Any]:
    from learnloop.experiments.contextual_embeddings.e1.ledger import budget_check

    vaults = inputs["vaults"]
    e0 = inputs["e0"]
    gpu = gpu_estimate(vaults)
    money = money_estimate(vaults, inputs.get("gaps"))
    verified = inputs["source"] == "import" and all((item or {}).get("ok") for item in
                                                     (inputs.get("verification") or {}).values())
    status = "frozen" if verified and e0["complete"] else "provisional"
    identity = {"e1": e1_pins.e1_pins_fingerprint(), "e0_pins": pins.pins_fingerprint(), "e0_run": e0["run_id"],
                "e0_plan": e0["plan_sha"], "e0_results": e0["results_sha"], "vaults": vaults, "status": status,
                "import": e0.get("import_manifest_sha")}
    plan = {
        "plan_id": e1_pins.E1_PLAN_PREFIX + _sha(identity)[:16], "status": status, "source": inputs["source"],
        "harness": e1_pins.E1_HARNESS_VERSION, "e1_pins_fingerprint": e1_pins.e1_pins_fingerprint(),
        "e0": dict(e0), "vaults": dict(vaults), "replay": {"gaps": inputs.get("gaps") or {},
                                                          "verification": inputs.get("verification") or {}},
        "model": {"repo": e1_pins.MODEL_REPO, "revision": e1_pins.MODEL_REVISION, "license": e1_pins.MODEL_LICENSE,
                  "parameters": e1_pins.MODEL_PARAMETERS, "disk_bytes": e1_pins.MODEL_DISK_BYTES,
                  "dimensions": e1_pins.MODEL_DIMENSIONS, "precision": e1_pins.PRECISION,
                  "deferred_precisions": e1_pins.DEFERRED_PRECISIONS, "remote_code": list(e1_pins.REMOTE_CODE_FILES),
                  "environment": {"python": e1_pins.LOCAL_PYTHON, "requirements": list(e1_pins.LOCAL_REQUIREMENTS)}},
        "arms": {"v2": e1_pins.V2_ARMS, "e0_replayed": list(e1_pins.E0_REPRESENTATION_ARMS)},
        "bounds": {"gpu_hours_cap": e1_pins.GPU_HOURS_CAP, "device_peak_target_gib": e1_pins.DEVICE_PEAK_TARGET_GIB,
                   "scope_memory_max": e1_pins.SCOPE_MEMORY_MAX, "scope_swap_max": e1_pins.SCOPE_SWAP_MAX,
                   "min_host_available_gib": e1_pins.MIN_HOST_AVAILABLE_GIB,
                   "min_free_vram_gib": e1_pins.MIN_FREE_VRAM_GIB, "host_floor_gib": e1_pins.HOST_FLOOR_GIB,
                   "max_other_gpu_process_mib": e1_pins.MAX_OTHER_GPU_PROCESS_MIB,
                   "max_gpu_utilization_pct": e1_pins.MAX_GPU_UTILIZATION_PCT,
                   "profile_tokens": list(e1_pins.PROFILE_TOKENS), "max_document_tokens": e1_pins.MAX_DOCUMENT_TOKENS,
                   "residency": "none: one batch process, unload, exit",
                   "cap_usd": e1_pins.E1_CAP_USD, "allocation_usd": e1_pins.E1_ALLOCATION_USD,
                   "supplement_depth": e1_pins.SUPPLEMENT_DEPTH},
        "decision_rules": {"retain_gain_min": e1_pins.RETAIN_GAIN_MIN,
                           "noninferiority_margin": e1_pins.NONINFERIORITY_MARGIN,
                           "supplement_kappa_min": e1_pins.SUPPLEMENT_KAPPA_MIN,
                           "v2_completion_min": e1_pins.V2_COMPLETION_MIN,
                           "rule": "retain local work only for >= 5 points Complete Evidence@10 over the best frozen "
                                   "finalist with the paired 95% CI excluding 0; a non-inferior result (lower bound "
                                   "above -0.02) is kept only for a cost/latency benefit the owner names; otherwise "
                                   "stop. Hosted v1 is a model baseline, not a numerical reference."},
        "gpu": gpu, "money": money,
        "budget": budget_check(money["expected"], dict(prior)),
        "assumptions": e1_pins.ASSUMPTIONS.as_dict(), "keys": dict(keys),
    }
    plan["budget"]["worst_case_usd"] = money["worst_case_usd"]
    return plan


def render_markdown(plan: Mapping[str, Any]) -> str:
    gpu, money, budget = plan["gpu"], plan["money"], plan["budget"]
    lines = [f"# E1 plan {plan['plan_id']} ({plan['status']})", "",
             f"Source: {plan['source']}; E0 run {plan['e0']['run_id']} (complete: {plan['e0']['complete']}).",
             f"Model: {plan['model']['repo']} @ {plan['model']['revision'][:8]}, {plan['model']['precision']}, "
             f"{plan['model']['disk_bytes'] / 1e9:.1f} GB on disk.", "",
             "| Vault | Units | Windows | Grouped tokens | Singleton tokens | Queries | Labelled questions |",
             "|---|---|---|---|---|---|---|"]
    for label, item in sorted(plan["vaults"].items()):
        lines.append(f"| {label} | {item['units']} | {item['windows']} | {item['grouped_tokens']:,} | "
                     f"{item['singleton_tokens']:,} | {item['queries']} | {item['labelled_questions']} |")
    lines += ["", f"GPU: expected {gpu['expected_hours']:.2f} h, worst case {gpu['worst_case_hours']:.2f} h "
                  f"of {gpu['cap_hours']:.0f} h ({gpu['steps']}).",
              f"Money: expected ${money['expected_usd']:.2f}, worst case ${money['worst_case_usd']:.2f} against "
              f"${budget['remaining_usd']:.2f} left of ${budget['cap_usd']:.2f} (fits: {budget['fits']}).",
              f"Priority past the cap: {money['priority']}.", "",
              f"Keys: {plan['keys']}."]
    return "\n".join(lines) + "\n"
