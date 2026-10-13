"""`learnloop grading hardcases`: wrong rejection and wrong acceptance per judge route.

The ITS sweep's P2 (owner decision 2026-10-13): a small, fixed set of hard
grading cases in the owner's subjects (``fixtures/grading_hardcases/``):

* ``valid_alternative`` - a valid proof or derivation by a route other than
  the reference's. A judge that marks any criterion down **wrongly rejects**;
* ``correct_flawed`` - the right final answer reached by invalid reasoning;
* ``wrong_looks_right`` - a fluent proof that is wrong.

For the last two a judge that gives full credit on every labelled failing
criterion **wrongly accepts**. Each route is scored in three roles, all with
the production prompts:

* ``grader`` - the learner-blind grader (the mvp-2.1 reference-policy prompt,
  as live grading sends it) on its raw output;
* ``checker`` - the mvp-0.15 independent route check alone;
* ``item_kind`` - the once-per-item proof-like reading (every case here is a
  proof, derivation, justification or explanation).

From those outputs, with no further calls, it also scores the production
**gate** for every ordered (grader route, checker route) pair: PF-c's gate,
then :func:`learnloop.attempts.proof_check.apply_proof_route_gate`. A gated
criterion ends assessed, unverified (unassessed) or flagged; a flagged or
marked-down failing criterion counts as caught, an unverified one as
unassessed (neither credit nor a catch).

Spend: one :class:`~learnloop.ops.pf_calls.PFCaller` per run: every request
is admitted against the caps before it is sent (metered routes need an owner
price; Codex and ChatGPT-plan routes are subscription, cost estimated from
tokens), recorded as a receipt in the vault copy, and checkpointed, so a rerun
never pays twice. ``--dry-run`` builds no client and sends nothing. Cases are
written for this harness, not learner data, so the report lists per-case
outcomes.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
from math import sqrt
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from learnloop.ai.spend import SpendCaps, SpendEstimate, is_subscription_transport
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN
from learnloop.attempts.blind_grading import (
    BlindGradingContext,
    blind_context_from_grading_context,
    blind_grading_prompt,
    blind_prompt_version,
)
from learnloop.attempts.grading import build_grading_context
from learnloop.attempts.grading_support import (
    apply_valid_alternative_gate,
    blind_result_model,
    reference_policy,
)
from learnloop.attempts.proof_check import (
    ITEM_KIND_PROMPT_VERSION,
    ROUTE_CHECK_PROMPT_VERSION,
    ItemKindReading,
    ProofRouteCheck,
    apply_proof_route_gate,
    item_kind_prompt,
    route_check_prompt,
)
from learnloop.db.repositories import Repository
from learnloop.diagnosis.diagnostic_augmentation import diagnostic_verifier_observations
from learnloop.ids import new_ulid
from learnloop.ops.pf_calls import (
    METERED_TYPES, PFCaller, PFUnavailable, RoleClient, estimate_tokens, pricing_basis, validate_pricing,
)
from learnloop.vault.models import LoadedVault, PracticeItem, Rubric
from learnloop.vault.paths import VaultPaths

HARNESS_VERSION = "grading-hardcases-v1"
CATEGORIES = ("valid_alternative", "correct_flawed", "wrong_looks_right")
ROLES = ("grader", "checker", "item_kind")
#: Output budgets per role (each request reserves its full budget).
OUTPUT_TOKENS = {"grader": 6000, "checker": 3000, "item_kind": 600}
#: Where the tracked gold set lives (the repository's fixtures directory).
DEFAULT_CASES = Path(__file__).resolve().parents[3] / "fixtures" / "grading_hardcases" / "cases_v1.json"
EEDI_MAP_NOTE = (
    "Eedi and Vanderbilt's Kaggle set 'MAP - Charting Student Math Misunderstandings' (2025) "
    "labels each student explanation of a multiple-choice answer True/False x Correct/"
    "Misconception/Neither. Its True_Misconception rows (a correct choice explained with a "
    "named misconception, about 2% of rows) are real correct-but-flawed traces and could fill "
    "the correct_flawed cell. Limits: short school-maths explanations of a chosen option, not "
    "proofs; competition data under Kaggle's competition rules (check the licence before "
    "committing any row); the label match to that set is inferred from the ITS sweep (§3.1), "
    "not verified here. Not used by this gold set."
)


@dataclass(frozen=True)
class HardCase:
    id: str
    subject: str
    category: str
    item: PracticeItem
    rubric: Rubric
    answer: str
    failing: tuple[str, ...]


def load_cases(path: Path | None = None) -> tuple[str, list[HardCase]]:
    """The gold set, validated: labels name real criteria, valid cases none."""

    source = Path(path) if path is not None else DEFAULT_CASES
    payload = json.loads(source.read_text(encoding="utf-8"))
    cases: list[HardCase] = []
    seen: set[str] = set()
    for raw in payload["cases"]:
        case_id = str(raw["id"])
        if case_id in seen:
            raise ValueError(f"duplicate hard case id {case_id!r}")
        seen.add(case_id)
        category = str(raw["category"])
        if category not in CATEGORIES:
            raise ValueError(f"{case_id}: unknown category {category!r}")
        item_raw = raw["item"]
        rubric = Rubric.model_validate({"criteria": item_raw["criteria"]})
        item = PracticeItem.model_validate({
            "id": f"hardcase_{case_id.replace('-', '_')}",
            "learning_object_id": f"hardcase_{raw.get('subject', 'misc')}",
            "practice_mode": item_raw.get("practice_mode", "constructed_response"),
            "prompt": item_raw["prompt"],
            "expected_answer": item_raw["expected_answer"],
            "grading_rubric": rubric.model_dump(mode="json"),
            "created_at": "2026-10-13T00:00:00Z",
            "updated_at": "2026-10-13T00:00:00Z",
        })
        failing = tuple(str(value) for value in raw["label"]["failing_criteria"])
        criterion_ids = {criterion.id for criterion in rubric.criteria}
        if set(failing) - criterion_ids:
            raise ValueError(f"{case_id}: failing criteria {sorted(set(failing) - criterion_ids)} not in its rubric")
        if (category == "valid_alternative") != (not failing):
            raise ValueError(f"{case_id}: a valid alternative fails no criterion; every other case fails one")
        cases.append(HardCase(case_id, str(raw.get("subject", "")), category, item, rubric,
                              str(raw["answer"]), failing))
    return str(payload.get("version", source.stem)), cases


def case_context(vault: LoadedVault, case: HardCase) -> BlindGradingContext:
    """The blind grading context as the live door builds it
    (``attempts._blind_grading_plan``): C2 verifier observations and PF-c's
    reference policy (live grading drops it only when
    ``diagnosis.grading_support`` is off)."""

    joint = build_grading_context(
        vault, case.item, attempt_id=f"hardcase:{case.id}", learner_answer_md=case.answer, rubric=case.rubric,
    )
    return blind_context_from_grading_context(
        joint,
        verifier_observations=diagnostic_verifier_observations(case.answer, joint.expected_answer),
        reference_policy=reference_policy(case.item, case.answer),
    )


def _requests(vault: LoadedVault, case: HardCase) -> dict[str, tuple[str, str, Any]]:
    context = case_context(vault, case)
    return {
        "grader": (blind_grading_prompt(context), blind_prompt_version(context), blind_result_model(context)),
        "checker": (route_check_prompt(case.item, case.rubric, case.answer), ROUTE_CHECK_PROMPT_VERSION,
                    ProofRouteCheck),
        "item_kind": (item_kind_prompt(case.item, case.rubric), ITEM_KIND_PROMPT_VERSION, ItemKindReading),
    }


# -- routes and clients --------------------------------------------------------------------


def _planned_entry(vault: LoadedVault, route: str, role: str) -> RoleClient:
    profile = vault.config.ai.providers.get(route)
    if profile is None:
        raise ValueError(f"--route {route!r} is not a configured [ai.providers.*] profile")
    return RoleClient(
        role=f"hardcase_{role}", provider=route, model=profile.model, profile_type=profile.type,
        subscription=is_subscription_transport(profile=profile),
        settings={"provider": route, "model": profile.model, "profile": profile.model_dump(mode="json")},
    )


def _resolved_entry(vault: LoadedVault, route: str, role: str, injected: Any | None) -> RoleClient:
    from learnloop.ai.routing import ready_client_for_task

    if injected is not None:
        return RoleClient(
            role=f"hardcase_{role}", provider=getattr(injected, "provider_name", None) or route,
            model=getattr(injected, "model", None), profile_type=getattr(injected, "provider_type", None),
            subscription=is_subscription_transport(client=injected), client=injected,
            settings={"provider": route, "model": getattr(injected, "model", None), "injected": True},
        )
    entry = _planned_entry(vault, route, role)
    if not (entry.profile_type in METERED_TYPES or entry.subscription):
        raise PFUnavailable(
            f"--route {route!r} must be an openai_chat/openrouter profile (bounded requests) or a "
            f"subscription profile (Codex, ChatGPT plan); it is {entry.profile_type!r}"
        )
    resolved = ready_client_for_task(vault.root, vault.config, "proof_check", explicit=route)
    if not resolved.ready:
        raise PFUnavailable(f"--route {route!r} is unavailable: {resolved.runtime.message}")
    client = resolved.client
    if not entry.subscription and not client.supports(BOUNDED_STRUCTURED_COMPLETION):
        raise PFUnavailable(f"--route {route!r} cannot bound its physical requests")
    if not client.supports(ISOLATED_TURN):
        raise PFUnavailable(f"--route {route!r} cannot run an isolated, tool-free turn")
    entry.client = client
    entry.model = getattr(client, "model", None) or entry.model
    entry.settings["model"] = entry.model
    return entry


# -- scoring --------------------------------------------------------------------------------


def _wilson(count: int, n: int) -> list[float] | None:
    if not n:
        return None
    p, z = count / n, 1.959963984540054
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [max(0.0, center - half), min(1.0, center + half)]


def _rate(count: int, n: int) -> dict[str, Any]:
    return {"count": count, "n": n, "rate": count / n if n else None, "wilson95": _wilson(count, n)}


def _criterion_states(case: HardCase, points: Mapping[str, float], *, unverified: Sequence[str] = (),
                      flagged: Sequence[str] = ()) -> dict[str, str]:
    """``full`` | ``short`` | ``unassessed`` | ``flagged`` per rubric criterion."""

    states = {}
    for criterion in case.rubric.criteria:
        if criterion.id in flagged:
            states[criterion.id] = "flagged"
        elif criterion.id in unverified:
            states[criterion.id] = "unassessed"
        elif float(points.get(criterion.id, 0.0)) + 1e-9 >= float(criterion.points):
            states[criterion.id] = "full"
        else:
            states[criterion.id] = "short"
    return states


def judge_outcome(case: HardCase, states: Mapping[str, str]) -> str:
    """What one judge did with one case.

    Valid alternatives: ``wrong_rejection`` (a criterion marked down or
    flagged), ``unassessed`` (none marked down, some unassessed) or ``correct``.
    The others: ``wrong_acceptance`` (every labelled failing criterion at full
    credit, unflagged), ``unassessed`` (none caught, some unassessed) or
    ``caught``.
    """

    if case.category == "valid_alternative":
        if any(state in {"short", "flagged"} for state in states.values()):
            return "wrong_rejection"
        return "unassessed" if any(state == "unassessed" for state in states.values()) else "correct"
    failing = [states.get(cid, "short") for cid in case.failing]
    if any(state in {"short", "flagged"} for state in failing):
        return "caught"
    return "unassessed" if any(state == "unassessed" for state in failing) else "wrong_acceptance"


def _checker_states(case: HardCase, check: ProofRouteCheck) -> dict[str, str]:
    verdicts = {row.criterion_id: row.verdict for row in check.criteria}
    states = {}
    for criterion in case.rubric.criteria:
        verdict = verdicts.get(criterion.id, "cannot_tell")
        states[criterion.id] = {"established": "full", "not_established": "short"}.get(verdict, "unassessed")
    return states


def _summary(cases: Sequence[HardCase], outcomes: Mapping[str, str | None]) -> dict[str, Any]:
    valid = [c for c in cases if c.category == "valid_alternative" and outcomes.get(c.id) is not None]
    bad = [c for c in cases if c.category != "valid_alternative" and outcomes.get(c.id) is not None]
    by_category: dict[str, dict[str, int]] = defaultdict(Counter)
    for case in cases:
        by_category[case.category][outcomes.get(case.id) or "failed"] += 1
    return {
        "wrong_rejection": _rate(sum(outcomes[c.id] == "wrong_rejection" for c in valid), len(valid)),
        "wrong_acceptance": _rate(sum(outcomes[c.id] == "wrong_acceptance" for c in bad), len(bad)),
        "unassessed": sum(outcomes.get(c.id) == "unassessed" for c in cases),
        "failed_cases": sum(outcomes.get(c.id) is None for c in cases),
        "by_category": {key: dict(sorted(value.items())) for key, value in sorted(by_category.items())},
    }


def gate_states(case: HardCase, grader_raw: Any, declared_unverified: Sequence[str],
                check: ProofRouteCheck, checker_model: str | None) -> dict[str, str]:
    """The production pipeline on one case: PF-c's gate, then the route check's."""

    policy = reference_policy(case.item, case.answer)
    pfc = apply_valid_alternative_gate(
        grader_raw, rubric=case.rubric, learner_answer_md=case.answer, policy=policy,
        declared_unverified=declared_unverified,
    )
    gate = apply_proof_route_gate(
        pfc.proposal, rubric=case.rubric, learner_answer_md=case.answer, check=check,
        unverified_before=pfc.unverified_criterion_ids,
        grader_review_recommended=bool(grader_raw.manual_review_recommended),
        checker_model=checker_model,
    )
    points = {row.criterion_id: float(row.points_awarded) for row in gate.proposal.criterion_evidence}
    return _criterion_states(case, points, unverified=gate.unverified, flagged=gate.flagged)


# -- the run --------------------------------------------------------------------------------


def run_hardcases(
    vault: LoadedVault,
    *,
    routes: Sequence[str],
    caps: SpendCaps,
    cases_path: Path | None = None,
    dry_run: bool = False,
    price_per_million: float | None = None,
    input_price_per_million: float | None = None,
    output_price_per_million: float | None = None,
    clients: Mapping[str, Any] | None = None,
    cancelled: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Plan (dry run) or run the gold set on each route; aggregate report."""

    validate_pricing(price_per_million, input_price_per_million, output_price_per_million)
    routes = list(dict.fromkeys(routes))
    if not routes:
        raise ValueError("name at least one --route")
    version, cases = load_cases(cases_path)
    requests = {case.id: _requests(vault, case) for case in cases}
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    repository = Repository.attach(sqlite_path, read_only=True) if dry_run else Repository(sqlite_path)
    caller = PFCaller(
        vault, repository, caps=caps, price_per_million=price_per_million, run_id=new_ulid(),
        owner_kind="grading_hardcases", cancelled=cancelled,
        input_price_per_million=input_price_per_million, output_price_per_million=output_price_per_million,
    )
    injected = dict(clients or {})
    planned = {route: _planned_entry(vault, route, "grader") if route not in injected
               else _resolved_entry(vault, route, "grader", injected[route]) for route in routes}
    plan: dict[str, Any] = {}
    totals = {False: [0, 0, 0], True: [0, 0, 0]}  # subscription -> [calls, tokens, output tokens]
    for route in routes:
        roles = {}
        for role in ROLES:
            tokens = sum(
                estimate_tokens(requests[case.id][role][0], requests[case.id][role][2], OUTPUT_TOKENS[role])
                for case in cases
            )
            roles[role] = {"calls": len(cases), "tokens": tokens, "output_tokens": OUTPUT_TOKENS[role] * len(cases)}
            bucket = totals[planned[route].subscription]
            bucket[0] += len(cases)
            bucket[1] += tokens
            bucket[2] += OUTPUT_TOKENS[role] * len(cases)
        plan[route] = {"model": planned[route].model, "billing": (
            "subscription (estimated only)" if planned[route].subscription else "metered"), "roles": roles}
    metered = caller.estimate(totals[False][1], subscription=False, calls=totals[False][0],
                              output_tokens=totals[False][2])
    subscription = caller.estimate(totals[True][1], subscription=True, calls=totals[True][0],
                                   output_tokens=totals[True][2])
    report: dict[str, Any] = {
        "status": "dry_run" if dry_run else "pending",
        "harness": HARNESS_VERSION, "cases_version": version, "cases": len(cases),
        "categories": dict(Counter(case.category for case in cases)),
        "routes": routes, "plan": plan,
        "estimate": {"metered": {"calls": metered.calls, "tokens": metered.total_tokens,
                                 "usd_upper_bound": metered.estimated_usd},
                     "subscription": {"calls": subscription.calls, "tokens": subscription.total_tokens,
                                      "usd_estimated_only": subscription.estimated_usd}},
        "caps": caps.as_dict(),
        "pricing": pricing_basis(price_per_million, input_price_per_million, output_price_per_million),
        "prompt_versions": {"checker": ROUTE_CHECK_PROMPT_VERSION, "item_kind": ITEM_KIND_PROMPT_VERSION},
        "eedi_map_note": EEDI_MAP_NOTE,
    }
    if totals[False][0] and metered.estimated_usd is None:
        report["status"] = "refused"
        report["reason"] = ("a metered route needs a price: pass --input-price-per-million and "
                            "--output-price-per-million (or --price-per-million, an upper bound)")
        return report
    try:
        caller.check_plan(metered, subscription)
    except Exception as exc:  # SpendLimitExceeded and friends: refuse before any request
        report["status"] = "refused"
        report["reason"] = f"{type(exc).__name__}: {exc}"
        return report
    if dry_run:
        return report

    outputs: dict[str, dict[str, dict[str, Any]]] = {route: {role: {} for role in ROLES} for route in routes}
    errors: dict[str, dict[str, int]] = {route: Counter() for route in routes}
    models: dict[str, str | None] = {}
    for route in routes:
        entries = {role: _resolved_entry(vault, route, role, injected.get(route)) for role in ROLES}
        for case in cases:
            for role in ROLES:
                prompt, prompt_version, model = requests[case.id][role]
                try:
                    call = caller.call(entries[role], prompt=prompt, prompt_version=prompt_version,
                                       result_model=model, output_tokens=OUTPUT_TOKENS[role],
                                       retry_invalid_output=False)
                except (PFUnavailable,) as exc:
                    raise
                except Exception as exc:  # one failed case is counted, never a crashed run
                    if type(exc).__name__ in {"SpendLimitExceeded", "AIInterrupted"}:
                        raise
                    errors[route][f"{role}:{type(exc).__name__}"] += 1
                    continue
                outputs[route][role][case.id] = call.result
                models[route] = call.model
    report["status"] = "complete"
    report["models"] = models
    report["errors"] = {route: dict(sorted(counts.items())) for route, counts in errors.items()}
    by_route: dict[str, Any] = {}
    per_case: dict[str, dict[str, Any]] = {case.id: {"category": case.category} for case in cases}
    for route in routes:
        grader_outcomes: dict[str, str | None] = {}
        checker_outcomes: dict[str, str | None] = {}
        for case in cases:
            raw = outputs[route]["grader"].get(case.id)
            if raw is not None:
                proposal = raw.as_blind_proposal() if hasattr(raw, "as_blind_proposal") else raw
                points = {row.criterion_id: float(row.points_awarded) for row in proposal.criterion_evidence}
                grader_outcomes[case.id] = judge_outcome(case, _criterion_states(case, points))
            else:
                grader_outcomes[case.id] = None
            check = outputs[route]["checker"].get(case.id)
            checker_outcomes[case.id] = judge_outcome(case, _checker_states(case, check)) if check else None
            per_case[case.id][f"{route}:grader"] = grader_outcomes[case.id]
            per_case[case.id][f"{route}:checker"] = checker_outcomes[case.id]
        kinds = [reading for reading in outputs[route]["item_kind"].values()]
        by_route[route] = {
            "model": models.get(route),
            "grader": _summary(cases, grader_outcomes),
            "checker": _summary(cases, checker_outcomes),
            "item_kind": {"read": len(kinds), "proof_like": sum(reading.proof_like for reading in kinds),
                          "kinds": dict(Counter(reading.response_kind for reading in kinds))},
        }
    gates: dict[str, Any] = {}
    for grader_route in routes:
        for checker_route in routes:
            outcomes: dict[str, str | None] = {}
            for case in cases:
                raw = outputs[grader_route]["grader"].get(case.id)
                check = outputs[checker_route]["checker"].get(case.id)
                if raw is None or check is None:
                    outcomes[case.id] = None
                    continue
                proposal = raw.as_blind_proposal() if hasattr(raw, "as_blind_proposal") else raw
                declared = list(getattr(raw, "unverified_criterion_ids", []) or [])
                states = gate_states(case, proposal, declared, check, models.get(checker_route))
                outcomes[case.id] = judge_outcome(case, states)
                per_case[case.id][f"gate:{grader_route}+{checker_route}"] = outcomes[case.id]
            gates[f"grader={grader_route} checker={checker_route}"] = {
                "grader_route": grader_route, "checker_route": checker_route,
                "independent": models.get(grader_route) != models.get(checker_route),
                **_summary(cases, outcomes),
            }
    report.update(
        by_route=by_route, gate=gates, per_case=per_case,
        spend={"billed": caller.billed(), "charged": caller.charged(), "declared": caller.declared(),
               "calls_by_role": dict(caller.calls_by_role), "cached_by_role": dict(caller.cached_by_role)},
    )
    return report


def write_report(report: Mapping[str, Any], output_dir: Path) -> dict[str, str]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path, markdown_path = directory / "grading-hardcases.json", directory / "grading-hardcases.md"
    json_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Grading hard cases", "",
        f"Gold set `{report.get('cases_version')}`: {report.get('cases')} cases "
        f"({json.dumps(report.get('categories'), sort_keys=True)}). Status: {report.get('status')}.", "",
    ]
    billed = ((report.get("spend") or {}).get("billed") or {})
    if billed:
        lines += [f"Billed: metered {billed.get('metered', {}).get('usd')} USD over "
                  f"{billed.get('metered', {}).get('requests')} requests; subscription requests "
                  f"{billed.get('subscription', {}).get('requests')} (estimated only).", ""]
    lines += ["| Judge | Route | Model | Wrong rejection (valid) | Wrong acceptance (flawed + wrong) | "
              "Unassessed | Failed |", "|---|---|---|---|---|---|---|"]

    def cell(rate: Mapping[str, Any]) -> str:
        if not rate.get("n"):
            return "n/a"
        interval = rate.get("wilson95") or [None, None]
        return f"{rate['count']}/{rate['n']} = {rate['rate']:.2f} [{interval[0]:.2f}, {interval[1]:.2f}]"

    for route, values in (report.get("by_route") or {}).items():
        for role in ("grader", "checker"):
            summary = values[role]
            lines.append(f"| {role} | {route} | {values.get('model')} | {cell(summary['wrong_rejection'])} | "
                         f"{cell(summary['wrong_acceptance'])} | {summary['unassessed']} | {summary['failed_cases']} |")
    for label, summary in (report.get("gate") or {}).items():
        lines.append(f"| gate | {label} | independent={summary['independent']} | "
                     f"{cell(summary['wrong_rejection'])} | {cell(summary['wrong_acceptance'])} | "
                     f"{summary['unassessed']} | {summary['failed_cases']} |")
    lines += ["", "Eedi MAP: " + str(report.get("eedi_map_note")), ""]
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(markdown_path)}


__all__ = [
    "CATEGORIES",
    "DEFAULT_CASES",
    "EEDI_MAP_NOTE",
    "HARNESS_VERSION",
    "HardCase",
    "case_context",
    "gate_states",
    "judge_outcome",
    "load_cases",
    "run_hardcases",
    "write_report",
]
