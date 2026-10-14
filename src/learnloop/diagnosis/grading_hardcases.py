"""`learnloop grading hardcases`: wrong rejection and wrong acceptance per judge route.

The ITS sweep's P2 (owner decision 2026-10-13): a small, fixed set of hard
grading cases in the owner's subjects (``fixtures/grading_hardcases/``), in
P2's four cells:

1. ``valid_alternative_checkable`` - a valid alternative route whose final
   answer the deterministic check verifies (E1's probe);
2. ``valid_alternative_proof`` - a valid proof or derivation by a route other
   than the reference's, with no verifiable final answer. A judge that marks
   any criterion of cells 1-2 down **wrongly rejects**;
3. ``correct_flawed`` - the right final answer reached by invalid reasoning;
4. ``wrong_looks_right`` - a fluent proof that is wrong. A judge that gives
   full credit on every labelled failing criterion of cells 3-4 **wrongly
   accepts**.

Harness v4 (method-explicit items, owner rule 2026-10-13) adds a fifth cell:

5. ``required_method_bypassed`` - an item whose statement requires a method
   (``item.required_method``: its name and the criteria that grade use of
   it) answered correctly by ANOTHER valid method. A correct judge fails the
   method criteria (labelled ``failing_criteria``) and gives every other
   criterion full credit on the facts. Full credit on a method criterion is a
   **wrong acceptance** (the requirement was not enforced); a mark-down of any
   other criterion is a **wrong rejection** (a valid route marked down). Each
   such case is paired with the same mathematics WITHOUT a required method, a
   cell 1-2 valid alternative that any valid method passes.

A case's cell follows from its category and the deterministic final-answer
check. Each case names its provenance: ``synthetic_hand_checked`` (written
for the harness and checked by hand) or ``real_trace`` (a learner's own text,
with its source). P2 requires real traces in cells 3-4, so a set without them
is labelled **synthetic smoke coverage** in every report (review F8).

Each route is scored as the **grader alone** (route-check-in-grader, owner
decision 2026-10-13: mvp-0.17's separate item reading and re-derivation call
were folded into the grader's prompt, and this harness measures what remains
so a harder gold set can show whether a second model is ever worth adding
back):

* ``grader`` - the learner-blind grader with the production prompt (mvp-2.1's
  reference policy plus the own-route rules at their latest version,
  ``own-route-v2``, with the item's required method) on its raw output, under
  each requested **arm** (R2's crossed factors, review F8): the reference
  shown or withheld (``solve_first``, C2), crossed with the final-answer check
  shown to the grader or withheld from it (the deterministic rules still apply
  it; C3). The production arm is ``reference_shown+check_shown``;
  ``--ablations`` runs all four;
* ``gate`` - the same grade along the production decision path (review F6):
  PF-c's gate, then the own-route rule with the deterministic final-answer
  status and the grader's own divergent-route reading (a mark-down on a
  divergent route that quotes nothing is unassessed, except a required
  method's criterion, whose evidence is the route).

``--repeats N`` runs every call N times as separately identified fresh
repetitions (each its own checkpoint, so a rerun resumes rather than reusing
another repetition); the report's ``noise_floor`` is how often a judge's
outcome on a case changes between repetitions (E1's repeat-run floor). The
headline rates are repetition 0's.

Every grader verdict is appended to ``judgment_ledger`` (task
``grading_hardcase_grader``, left = the case keyed by its content),
idempotently: a cached or resumed call ensures its judgment exists without
duplicating it (review F7).

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
from dataclasses import dataclass, replace
import hashlib
import json
from math import sqrt
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from learnloop.ai.output_budget import output_budget
from learnloop.ai.spend import SpendCaps, is_subscription_transport
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN
from learnloop.attempts.answer_check import final_answer_check
from learnloop.attempts.blind_grading import (
    BlindGradingContext,
    blind_context_from_grading_context,
    blind_grading_prompt,
    blind_prompt_version,
)
from learnloop.attempts.grading import build_grading_context
from learnloop.attempts.grading_support import (
    METHOD_ROUTE_RULES_VERSION,
    apply_route_rule,
    apply_valid_alternative_gate,
    blind_result_model,
    policy_method_criteria,
    reference_policy,
)
from learnloop.db.repositories import Repository
from learnloop.diagnosis.diagnostic_augmentation import diagnostic_verifier_observations
from learnloop.ids import new_ulid
from learnloop.ops.pf_calls import (
    METERED_TYPES, CallResult, PFCaller, PFUnavailable, RoleClient, estimate_tokens, pricing_basis,
    validate_pricing,
)
from learnloop.vault.models import LoadedVault, PracticeItem, Rubric
from learnloop.vault.paths import VaultPaths

#: v3 (route-check-in-grader): the grader alone, with the own-route rules; the
#: checker and item-kind roles and the (grader, checker) pairs are gone.
#: v4 (method-explicit items): the production rules are ``own-route-v2`` with
#: the item's required method, and the ``required_method_bypassed`` cell.
HARNESS_VERSION = "grading-hardcases-v4"
#: The own-route rules the production path runs (the latest successor's).
PRODUCTION_ROUTE_RULES = METHOD_ROUTE_RULES_VERSION
CATEGORIES = ("valid_alternative", "correct_flawed", "wrong_looks_right", "required_method_bypassed")
#: P2's four cells, in order, then the method-explicit cell.
CELLS = (
    "valid_alternative_checkable", "valid_alternative_proof", "correct_flawed", "wrong_looks_right",
    "required_method_bypassed",
)
VALID_CELLS = frozenset(CELLS[:2])
#: Cells whose labelled criteria a correct judge marks down (wrong acceptance).
FAILING_CELLS = frozenset(CELLS[2:4])
METHOD_CELL = "required_method_bypassed"
PROVENANCES = ("synthetic_hand_checked", "real_trace")
#: P2: "cells 3 and 4 come from real traces".
REAL_TRACE_CELLS = ("correct_flawed", "wrong_looks_right")
ROLES = ("grader",)
#: R2's crossed grader arms: the reference shown or solve-first (C2), the
#: final-answer check shown to the grader or withheld from it (C3).
REFERENCE_ARMS = ("reference_shown", "solve_first")
CHECK_ARMS = ("check_shown", "check_withheld")
PRODUCTION_ARM = "reference_shown+check_shown"
ALL_ARMS = tuple(f"{reference}+{check}" for reference in REFERENCE_ARMS for check in CHECK_ARMS)
#: What a withheld check reads as in the grader's reference policy.
WITHHELD_CHECK = {"status": "withheld_from_grader", "method": None}
#: The production route the grader's output budget follows. Every request asks
#: for (and reserves) that route's budget under the shared output-budget
#: policy (``learnloop.ai.output_budget``: ``ai.route_output_tokens.<route>``,
#: else the profile's ``max_tokens``, else ``ai.output_tokens``), as the live
#: door's grader does. A truncated answer is never accepted: it is logged and
#: retried once at double the budget (admitted as a retry).
HARDCASE_ROUTES = {"grader": "grading"}
#: ``judgment_ledger`` task per role, and the left kind of a case.
LEDGER_TASKS = {role: f"grading_hardcase_{role}" for role in ROLES}
CASE_KIND = "grading_hardcase"
#: Where the tracked gold set lives (the repository's fixtures directory).
DEFAULT_CASES = Path(__file__).resolve().parents[3] / "fixtures" / "grading_hardcases" / "cases_v3.json"
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
    #: The deterministic ``final_answer_check`` status of the answer.
    final_answer_status: str = "undecidable"
    cell: str = ""
    provenance: str = "synthetic_hand_checked"
    source: str | None = None

    @property
    def content_key(self) -> str:
        """The case keyed by its content (item, rubric, answer, label)."""

        payload = {
            "prompt": self.item.prompt, "expected_answer": self.item.expected_answer,
            "rubric": self.rubric.model_dump(mode="json"), "answer": self.answer,
            "failing": list(self.failing), "category": self.category,
        }
        if self.item.required_method is not None:
            # Only a case that has one names it, so every earlier case keeps its key;
            # what the grader is shown only (who decided the statement requires it
            # is not grading content, so the v3 keys are unchanged).
            payload["required_method"] = self.item.required_method.model_dump(
                mode="json", exclude={"statement", "decided_by", "judgment_id"})
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        return f"{self.id}@{digest[:16]}"


def _cell(category: str, final_status: str) -> str:
    if category == "valid_alternative":
        return CELLS[0] if final_status == "matches_reference" else CELLS[1]
    return category


def method_criteria(case: "HardCase") -> tuple[str, ...]:
    """The criteria a case's required method grades on use of the method."""

    method = case.item.required_method
    return tuple(method.criterion_ids) if method is not None else ()


def load_cases(path: Path | None = None) -> tuple[str, list[HardCase]]:
    """The gold set, validated: labels name real criteria, valid cases none.

    A ``required_method_bypassed`` case carries ``item.required_method``,
    which passes doctor's validation of the field (the canonical sentence, or
    a recorded decision on a hand-written statement); its labelled criteria
    are exactly the method's criteria, and its answer's final answer matches
    the reference (another
    VALID method). Any other case may carry a required method only as a valid
    alternative that uses it.
    """

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
        provenance = str(raw.get("provenance", "synthetic_hand_checked"))
        if provenance not in PROVENANCES:
            raise ValueError(f"{case_id}: unknown provenance {provenance!r}")
        if provenance == "real_trace" and not str(raw.get("source") or "").strip():
            raise ValueError(f"{case_id}: a real trace names its source")
        item_raw = raw["item"]
        rubric = Rubric.model_validate({"criteria": item_raw["criteria"]})
        item = PracticeItem.model_validate({
            "id": f"hardcase_{case_id.replace('-', '_')}",
            "learning_object_id": f"hardcase_{raw.get('subject', 'misc')}",
            "practice_mode": item_raw.get("practice_mode", "constructed_response"),
            "prompt": item_raw["prompt"],
            "expected_answer": item_raw["expected_answer"],
            "grading_rubric": rubric.model_dump(mode="json"),
            **({"required_method": item_raw["required_method"]} if item_raw.get("required_method") else {}),
            "created_at": "2026-10-13T00:00:00Z",
            "updated_at": "2026-10-13T00:00:00Z",
        })
        failing = tuple(str(value) for value in raw["label"]["failing_criteria"])
        criterion_ids = {criterion.id for criterion in rubric.criteria}
        if set(failing) - criterion_ids:
            raise ValueError(f"{case_id}: failing criteria {sorted(set(failing) - criterion_ids)} not in its rubric")
        if (category == "valid_alternative") != (not failing):
            raise ValueError(f"{case_id}: a valid alternative fails no criterion; every other case fails one")
        method = item.required_method
        if method is not None:
            from learnloop.vault.required_method import required_method_problems

            # Doctor's structural validation of the field (redesign
            # 2026-10-14): an ``instruction`` statement carries the canonical
            # sentence verbatim, a hand-written ``source`` statement records
            # who decided it requires the method. No phrasing is read.
            errors = [problem for problem in required_method_problems(item, rubric)
                      if problem.severity == "error" and problem.code != "required_method:unknown_criterion"]
            if errors:
                raise ValueError(f"{case_id}: {errors[0].code}: {errors[0].message}")
            if set(method.criterion_ids) - criterion_ids:
                raise ValueError(f"{case_id}: required method criteria not in its rubric")
        if category == "required_method_bypassed":
            if method is None or not method.criterion_ids:
                raise ValueError(f"{case_id}: a required_method_bypassed case names its required method's criteria")
            if set(failing) != set(method.criterion_ids):
                raise ValueError(f"{case_id}: a required_method_bypassed case fails exactly its method criteria")
        answer = str(raw["answer"])
        status = str(final_answer_check(answer, item.expected_answer).get("status"))
        if category in ("valid_alternative", "required_method_bypassed") and status == "differs_from_reference":
            raise ValueError(f"{case_id}: a valid route's final answer differs from the reference")
        cases.append(HardCase(
            case_id, str(raw.get("subject", "")), category, item, rubric, answer, failing,
            final_answer_status=status, cell=_cell(category, status), provenance=provenance,
            source=str(raw["source"]) if raw.get("source") else None,
        ))
    return str(payload.get("version", source.stem)), cases


def gold_set_coverage(cases: Sequence[HardCase]) -> dict[str, Any]:
    """Cases and real traces per cell, and what the set can and cannot show."""

    by_cell = {cell: sum(case.cell == cell for case in cases) for cell in CELLS}
    real = {cell: sum(case.cell == cell and case.provenance == "real_trace" for case in cases) for cell in CELLS}
    limitations = []
    for cell in CELLS:
        if not by_cell[cell]:
            limitations.append(f"cell {cell} has no case")
    missing_real = [cell for cell in REAL_TRACE_CELLS if not real[cell]]
    if missing_real:
        limitations.append(
            f"no real traces in {', '.join(missing_real)}: P2 requires cells 3-4 from real traces "
            "(the Bitter Lesson rule 'validate the grader only on real traces'), so these rates are "
            "synthetic smoke coverage, not P2/R2 estimates"
        )
    return {
        "kind": "synthetic smoke coverage" if not any(real.values()) else (
            "mixed" if missing_real else "real traces in cells 3-4"),
        "cases_by_cell": by_cell,
        "real_traces_by_cell": real,
        "limitations": limitations,
    }


def case_context(vault: LoadedVault, case: HardCase, arm: str = PRODUCTION_ARM) -> BlindGradingContext:
    """The blind grading context as the live door builds it at the latest
    successor (``attempts._blind_grading_plan``): C2 verifier observations and
    PF-c's reference policy with the own-route rules (``own-route-v2``, with
    the item's required method; live grading drops the policy only when
    ``diagnosis.grading_support`` is off, the rules when
    ``proof_check.enabled`` is, and their required-method part when
    ``required_method.enabled`` is), varied by ``arm``:

    * ``solve_first`` - the reference solution is withheld (the policy says
      ``absent``, so the grader writes its own expected answer first);
    * ``check_withheld`` - the final-answer check, and the C2 verifier
      observations that compare the answer with the reference, are withheld
      from the grader. The deterministic gate still applies the check.
    """

    reference, check = _split_arm(arm)
    joint = build_grading_context(
        vault, case.item, attempt_id=f"hardcase:{case.id}", learner_answer_md=case.answer, rubric=case.rubric,
    )
    policy = _production_policy(case)
    observations = diagnostic_verifier_observations(case.answer, joint.expected_answer)
    if reference == "solve_first":
        policy = {**policy, "reference_status": "absent"}
    if check == "check_withheld":
        policy = {**policy, "final_answer_check": dict(WITHHELD_CHECK)}
        observations = []
    context = blind_context_from_grading_context(
        joint, verifier_observations=observations, reference_policy=policy,
    )
    if reference == "solve_first":
        context = replace(context, expected_answer="", error_hunt_solution=None)
    return context


def _production_policy(case: HardCase) -> dict[str, Any]:
    """PF-c's policy with the production own-route rules and the item's required method."""

    return reference_policy(
        case.item, case.answer, route_rules=PRODUCTION_ROUTE_RULES,
        rubric_criterion_ids=[criterion.id for criterion in case.rubric.criteria],
    )


def _split_arm(arm: str) -> tuple[str, str]:
    reference, _, check = arm.partition("+")
    if reference not in REFERENCE_ARMS or check not in CHECK_ARMS:
        raise ValueError(f"unknown grader arm {arm!r}; arms are {', '.join(ALL_ARMS)}")
    return reference, check


def _grader_request(vault: LoadedVault, case: HardCase, arm: str) -> tuple[str, str, Any]:
    context = case_context(vault, case, arm)
    version = blind_prompt_version(context)
    if arm != PRODUCTION_ARM:
        version = f"{version}+arm:{arm}"
    return blind_grading_prompt(context), version, blind_result_model(context)


def _requests(vault: LoadedVault, case: HardCase, arms: Sequence[str]) -> dict[tuple[str, str], tuple[str, str, Any]]:
    """(role, arm) -> (prompt, prompt version, result model)."""

    return {("grader", arm): _grader_request(vault, case, arm) for arm in arms}


def role_output_tokens(vault: LoadedVault, route: str) -> dict[str, int]:
    """The grader's output budget on ``route`` (a profile name): the policy
    budget of the production grading route (:data:`HARDCASE_ROUTES`), held to
    that profile's ``max_tokens``."""

    return {role: output_budget(vault.config, task, provider=route) for role, task in HARDCASE_ROUTES.items()}


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
    resolved = ready_client_for_task(vault.root, vault.config, "grading", explicit=route)
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


def _repetition_entry(entry: RoleClient, repetition: int) -> RoleClient:
    """Repetition 0 is the plain call (earlier checkpoints stay valid); a later
    repetition is a separately identified fresh call with its own checkpoint."""

    if repetition == 0:
        return entry
    return replace(entry, settings={**entry.settings, "repetition": repetition})


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


def _criterion_states(case: HardCase, points: Mapping[str, float], *, unverified: Sequence[str] = ()) -> dict[str, str]:
    """``full`` | ``short`` | ``unassessed`` per rubric criterion."""

    states = {}
    for criterion in case.rubric.criteria:
        if criterion.id in unverified:
            states[criterion.id] = "unassessed"
        elif float(points.get(criterion.id, 0.0)) + 1e-9 >= float(criterion.points):
            states[criterion.id] = "full"
        else:
            states[criterion.id] = "short"
    return states


def judge_outcome(case: HardCase, states: Mapping[str, str]) -> str:
    """What one judge did with one case.

    Valid alternatives: ``wrong_rejection`` (a criterion marked down),
    ``unassessed`` (none marked down, some unassessed) or ``correct``. The
    others: ``wrong_acceptance`` (every labelled failing criterion at full
    credit), ``unassessed`` (none caught, some unassessed) or ``caught``.

    A required method bypassed: ``wrong_acceptance`` (a method criterion at
    full credit: the requirement was not enforced), else ``wrong_rejection``
    (a criterion other than the method's marked down: a valid route's fact
    rejected), else ``caught`` only when every method criterion failed AND
    every fact criterion has full credit, else ``unassessed`` (a method or a
    fact criterion unassessed: a fact left unassessed was not credited, so
    the case is no success; review F8).
    """

    if case.category == "required_method_bypassed":
        method = set(case.failing)
        facts = [criterion.id for criterion in case.rubric.criteria if criterion.id not in method]
        if any(states.get(cid, "short") == "full" for cid in method):
            return "wrong_acceptance"
        if any(states.get(cid, "short") == "short" for cid in facts):
            return "wrong_rejection"
        if all(states.get(cid, "short") == "short" for cid in method) and all(
                states.get(cid) == "full" for cid in facts):
            return "caught"
        return "unassessed"
    if case.category == "valid_alternative":
        if any(state == "short" for state in states.values()):
            return "wrong_rejection"
        return "unassessed" if any(state == "unassessed" for state in states.values()) else "correct"
    failing = [states.get(cid, "short") for cid in case.failing]
    if any(state == "short" for state in failing):
        return "caught"
    return "unassessed" if any(state == "unassessed" for state in failing) else "wrong_acceptance"


def _summary(cases: Sequence[HardCase], outcomes: Mapping[str, str | None]) -> dict[str, Any]:
    """The headline rates (cells 1-2 and 3-4, as before) and the method cell's own.

    The required-method cell is reported apart (``required_method``): its
    wrong acceptance is an unenforced requirement and its wrong rejection a
    valid route's fact marked down, so it never moves the P2 rates.
    """

    valid = [c for c in cases if c.cell in VALID_CELLS and outcomes.get(c.id) is not None]
    bad = [c for c in cases if c.cell in FAILING_CELLS and outcomes.get(c.id) is not None]
    method = [c for c in cases if c.cell == METHOD_CELL and outcomes.get(c.id) is not None]
    by_cell: dict[str, dict[str, int]] = defaultdict(Counter)
    for case in cases:
        by_cell[case.cell][outcomes.get(case.id) or "failed"] += 1
    return {
        "wrong_rejection": _rate(sum(outcomes[c.id] == "wrong_rejection" for c in valid), len(valid)),
        "wrong_acceptance": _rate(sum(outcomes[c.id] == "wrong_acceptance" for c in bad), len(bad)),
        "required_method": {
            "enforced": _rate(sum(outcomes[c.id] == "caught" for c in method), len(method)),
            "not_enforced": _rate(sum(outcomes[c.id] == "wrong_acceptance" for c in method), len(method)),
            "fact_rejected": _rate(sum(outcomes[c.id] == "wrong_rejection" for c in method), len(method)),
        },
        "unassessed": sum(outcomes.get(c.id) == "unassessed" for c in cases),
        "failed_cases": sum(outcomes.get(c.id) is None for c in cases),
        "by_cell": {cell: dict(sorted(by_cell[cell].items())) for cell in CELLS if cell in by_cell},
    }


def _noise_floor(cases: Sequence[HardCase], by_repetition: Sequence[Mapping[str, str | None]]) -> dict[str, Any]:
    """How often a judge's outcome on a case changes between fresh repetitions."""

    if len(by_repetition) < 2:
        return {"repetitions": len(by_repetition), "changed": None,
                "note": "one repetition: no noise floor (run with --repeats 2 or more)"}
    changed = compared = 0
    for case in cases:
        seen = [outcomes.get(case.id) for outcomes in by_repetition]
        seen = [value for value in seen if value is not None]
        if len(seen) < 2:
            continue
        compared += 1
        changed += len(set(seen)) > 1
    return {"repetitions": len(by_repetition), "changed": _rate(changed, compared)}


def gate_states(
    case: HardCase,
    grader_raw: Any,
    declared_unverified: Sequence[str],
    *,
    divergent_route: bool = False,
) -> tuple[dict[str, str], str]:
    """The production decision path on one case, and what the rule did.

    PF-c's gate (with the real deterministic check, whatever the grader was
    shown), then the own-route rule
    (``attempts.grading_support.apply_route_rule``) with the grader's own
    divergent-route reading, as ``request_blind_grading_run`` applies them
    (review F6), the item's required-method criteria exempt from both on a
    divergent route. The status is ``held`` (nothing assessed, nothing
    validated), ``unlocated`` (a mark-down left unassessed) or ``unchanged``.
    """

    policy = _production_policy(case)
    method_ids = policy_method_criteria(policy)
    pfc = apply_valid_alternative_gate(
        grader_raw, rubric=case.rubric, learner_answer_md=case.answer, policy=policy,
        declared_unverified=declared_unverified,
        method_criterion_ids=method_ids if divergent_route else (),
    )
    rule = apply_route_rule(
        pfc.proposal, rubric=case.rubric, learner_answer_md=case.answer,
        final_answer_status=case.final_answer_status, divergent_route=divergent_route,
        unverified_before=pfc.unverified_criterion_ids, declared_unverified=declared_unverified,
        method_criterion_ids=method_ids,
    )
    points = {row.criterion_id: float(row.points_awarded) for row in rule.proposal.criterion_evidence}
    status = "held" if rule.held_for_review else ("unlocated" if rule.applied else "unchanged")
    return _criterion_states(case, points, unverified=rule.unverified), status


# -- the ledger ---------------------------------------------------------------------------


def _verdict(role: str, case: HardCase, call: CallResult, outcome: str | None) -> tuple[str, float | None]:
    result = call.result
    proposal = result.as_blind_proposal() if hasattr(result, "as_blind_proposal") else result
    points = {row.criterion_id: float(row.points_awarded) for row in proposal.criterion_evidence}
    route = getattr(result, "route_check", None)
    body = {
        "outcome": outcome, "criterion_points": points, "fatal_errors": list(proposal.fatal_errors),
        "unverified_criterion_ids": list(getattr(result, "unverified_criterion_ids", []) or []),
        "divergent_route": bool(getattr(route, "divergent_route", False)),
    }
    maximum = float(sum(float(c.points) for c in case.rubric.criteria)) or 1.0
    return json.dumps(body, sort_keys=True), min(1.0, sum(points.values()) / maximum)


def _record_judgment(caller: PFCaller, role: str, case: HardCase, call: CallResult, outcome: str | None,
                     *, arm: str, repetition: int) -> str:
    """Append one judge's verdict on one case, once (review F7)."""

    verdict, score = _verdict(role, case, call, outcome)
    return caller.ledger(
        task=LEDGER_TASKS[role], left_kind=CASE_KIND, left_id=case.content_key, judge="llm",
        judge_model=call.model, prompt_version=call.prompt_version, input_hash=call.input_hash,
        verdict=verdict, score=score,
        rationale={"harness": HARNESS_VERSION, "cell": case.cell, "provenance": case.provenance,
                   "arm": arm, "repetition": repetition, "cached": call.cached},
    )


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
    arms: Sequence[str] = (PRODUCTION_ARM,),
    repeats: int = 1,
) -> dict[str, Any]:
    """Plan (dry run) or run the gold set on each route; aggregate report."""

    validate_pricing(price_per_million, input_price_per_million, output_price_per_million)
    routes = list(dict.fromkeys(routes))
    if not routes:
        raise ValueError("name at least one --route")
    arms = list(dict.fromkeys(arms))
    if not arms:
        raise ValueError("name at least one grader arm")
    for arm in arms:
        _split_arm(arm)
    if repeats < 1:
        raise ValueError("--repeats must be at least 1")
    version, cases = load_cases(cases_path)
    requests = {case.id: _requests(vault, case, arms) for case in cases}
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
    keys = [("grader", arm) for arm in arms]
    plan: dict[str, Any] = {}
    totals = {False: [0, 0, 0], True: [0, 0, 0]}  # subscription -> [calls, tokens, output tokens]
    for route in routes:
        roles: dict[str, Any] = {}
        budgets = role_output_tokens(vault, route)
        for role, arm in keys:
            label = f"{role}:{arm}"
            calls = len(cases) * repeats
            tokens = repeats * sum(
                estimate_tokens(requests[case.id][(role, arm)][0], requests[case.id][(role, arm)][2],
                                budgets[role])
                for case in cases
            )
            roles[label] = {"calls": calls, "tokens": tokens, "output_tokens": budgets[role] * calls,
                            "output_route": HARDCASE_ROUTES[role]}
            bucket = totals[planned[route].subscription]
            bucket[0] += calls
            bucket[1] += tokens
            bucket[2] += budgets[role] * calls
        plan[route] = {"model": planned[route].model, "billing": (
            "subscription (estimated only)" if planned[route].subscription else "metered"), "roles": roles}
    metered = caller.estimate(totals[False][1], subscription=False, calls=totals[False][0],
                              output_tokens=totals[False][2])
    subscription = caller.estimate(totals[True][1], subscription=True, calls=totals[True][0],
                                   output_tokens=totals[True][2])
    coverage = gold_set_coverage(cases)
    limitations = list(coverage["limitations"])
    if repeats < 2:
        limitations.append("one repetition: no repeat-run noise floor (run with --repeats 2 or more)")
    missing_arms = [arm for arm in ALL_ARMS if arm not in arms]
    if missing_arms:
        limitations.append(
            f"grader arms not run: {', '.join(missing_arms)} (C2/C3 need --ablations)"
        )
    report: dict[str, Any] = {
        "status": "dry_run" if dry_run else "pending",
        "harness": HARNESS_VERSION, "cases_version": version, "cases": len(cases),
        "categories": dict(Counter(case.category for case in cases)),
        "cells": coverage["cases_by_cell"], "gold_set": coverage, "limitations": limitations,
        "arms": arms, "production_arm": PRODUCTION_ARM, "repeats": repeats,
        "routes": routes, "plan": plan,
        "estimate": {"metered": {"calls": metered.calls, "tokens": metered.total_tokens,
                                 "usd_upper_bound": metered.estimated_usd},
                     "subscription": {"calls": subscription.calls, "tokens": subscription.total_tokens,
                                      "usd_estimated_only": subscription.estimated_usd}},
        "caps": caps.as_dict(),
        "pricing": pricing_basis(price_per_million, input_price_per_million, output_price_per_million),
        "prompt_versions": {
            "grader": blind_prompt_version(case_context(vault, cases[0])) if cases else None,
        },
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

    # outputs[route][(role, arm)][repetition][case id] -> CallResult
    outputs: dict[str, dict[tuple[str, str], list[dict[str, CallResult]]]] = {
        route: {key: [{} for _ in range(repeats)] for key in keys} for route in routes
    }
    errors: dict[str, dict[str, int]] = {route: Counter() for route in routes}
    models: dict[str, str | None] = {}
    for route in routes:
        entries = {role: _resolved_entry(vault, route, role, injected.get(route)) for role in ROLES}
        budgets = role_output_tokens(vault, route)
        for repetition in range(repeats):
            for case in cases:
                for role, arm in keys:
                    prompt, prompt_version, model = requests[case.id][(role, arm)]
                    try:
                        # An invalid output is one failed case (never retried),
                        # but a truncation is retried once at double the
                        # budget under the shared policy.
                        call = caller.call(_repetition_entry(entries[role], repetition), prompt=prompt,
                                           prompt_version=prompt_version, result_model=model,
                                           output_tokens=budgets[role], retry_invalid_output=False,
                                           retry_truncation=True)
                    except PFUnavailable:
                        raise
                    except Exception as exc:  # one failed case is counted, never a crashed run
                        if type(exc).__name__ in {"SpendLimitExceeded", "AIInterrupted", "SpendCancelled"}:
                            raise
                        errors[route][f"{role}:{arm}:{type(exc).__name__}"] += 1
                        continue
                    outputs[route][(role, arm)][repetition][case.id] = call
                    models[route] = call.model
    report["status"] = "complete"
    report["models"] = models
    report["errors"] = {route: dict(sorted(counts.items())) for route, counts in errors.items()}
    per_case: dict[str, dict[str, Any]] = {
        case.id: {"category": case.category, "cell": case.cell, "provenance": case.provenance,
                  "final_answer_status": case.final_answer_status}
        for case in cases
    }
    judgments = 0

    def suffix(arm: str, repetition: int) -> str:
        text = "" if arm == PRODUCTION_ARM else f"[{arm}]"
        return text + ("" if repetition == 0 else f"#{repetition}")

    def grader_outcome(case: HardCase, call: CallResult | None) -> str | None:
        if call is None:
            return None
        raw = call.result
        proposal = raw.as_blind_proposal() if hasattr(raw, "as_blind_proposal") else raw
        points = {row.criterion_id: float(row.points_awarded) for row in proposal.criterion_evidence}
        return judge_outcome(case, _criterion_states(case, points))

    by_route: dict[str, Any] = {}
    for route in routes:
        route_report: dict[str, Any] = {"model": models.get(route)}
        for role, arm in keys:
            by_repetition: list[dict[str, str | None]] = []
            for repetition in range(repeats):
                calls = outputs[route][(role, arm)][repetition]
                outcomes: dict[str, str | None] = {}
                for case in cases:
                    call = calls.get(case.id)
                    outcomes[case.id] = grader_outcome(case, call)
                    if call is not None:
                        _record_judgment(caller, role, case, call, outcomes[case.id], arm=arm,
                                         repetition=repetition)
                        judgments += 1
                    per_case[case.id][f"{route}:{role}{suffix(arm, repetition)}"] = outcomes[case.id]
                by_repetition.append(outcomes)
            label = role if arm == PRODUCTION_ARM else f"{role}[{arm}]"
            route_report[label] = {**_summary(cases, by_repetition[0]),
                                   "noise_floor": _noise_floor(cases, by_repetition)}
        by_route[route] = route_report

    gates: dict[str, Any] = {}
    for grader_route in routes:
        for arm in arms:
            by_repetition = []
            rule: Counter = Counter()
            for repetition in range(repeats):
                graders = outputs[grader_route][("grader", arm)][repetition]
                outcomes: dict[str, str | None] = {}
                for case in cases:
                    call = graders.get(case.id)
                    if call is None:
                        outcomes[case.id] = None
                        continue
                    raw = call.result
                    proposal = raw.as_blind_proposal() if hasattr(raw, "as_blind_proposal") else raw
                    declared = list(getattr(raw, "unverified_criterion_ids", []) or [])
                    route_check = getattr(raw, "route_check", None)
                    states, status = gate_states(
                        case, proposal, declared,
                        divergent_route=bool(getattr(route_check, "divergent_route", False)),
                    )
                    if repetition == 0:
                        rule[status] += 1
                    outcomes[case.id] = judge_outcome(case, states)
                    per_case[case.id][f"gate:{grader_route}{suffix(arm, repetition)}"] = outcomes[case.id]
                by_repetition.append(outcomes)
            label = f"grader={grader_route}"
            if arm != PRODUCTION_ARM:
                label += f" arm={arm}"
            gates[label] = {
                "grader_route": grader_route, "arm": arm,
                "rule": dict(sorted(rule.items())),
                **_summary(cases, by_repetition[0]),
                "noise_floor": _noise_floor(cases, by_repetition),
            }
    report.update(
        by_route=by_route, gate=gates, per_case=per_case,
        judgments={"task_prefix": "grading_hardcase_", "ensured": judgments},
        spend={"billed": caller.billed(), "charged": caller.charged(), "declared": caller.declared(),
               "calls_by_role": dict(caller.calls_by_role), "cached_by_role": dict(caller.cached_by_role)},
    )
    return report


def write_report(report: Mapping[str, Any], output_dir: Path) -> dict[str, str]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path, markdown_path = directory / "grading-hardcases.json", directory / "grading-hardcases.md"
    json_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    gold = report.get("gold_set") or {}
    lines = [
        "# Grading hard cases", "",
        f"Gold set `{report.get('cases_version')}`: {report.get('cases')} cases, "
        f"**{gold.get('kind', 'unlabelled')}**. Status: {report.get('status')}.", "",
        "| Cell | Cases | Real traces |", "|---|---:|---:|",
    ]
    for cell in CELLS:
        lines.append(f"| {cell} | {(gold.get('cases_by_cell') or {}).get(cell, 0)} | "
                     f"{(gold.get('real_traces_by_cell') or {}).get(cell, 0)} |")
    lines += ["", f"Grader arms: {', '.join(report.get('arms') or [])}. Repetitions: {report.get('repeats')}.", ""]
    for limitation in report.get("limitations") or []:
        lines.append(f"- Limitation: {limitation}")
    lines.append("")
    billed = ((report.get("spend") or {}).get("billed") or {})
    if billed:
        lines += [f"Billed: metered {billed.get('metered', {}).get('usd')} USD over "
                  f"{billed.get('metered', {}).get('requests')} requests; subscription requests "
                  f"{billed.get('subscription', {}).get('requests')} (estimated only).", ""]
    lines += ["| Judge | Route | Model | Wrong rejection (cells 1-2) | Wrong acceptance (cells 3-4) | "
              "Required method enforced (cell 5) | Unassessed | Failed | Changed across repeats |",
              "|---|---|---|---|---|---|---|---|---|"]

    def cell(rate: Mapping[str, Any] | None) -> str:
        if not rate or not rate.get("n"):
            return "n/a"
        interval = rate.get("wilson95") or [None, None]
        return f"{rate['count']}/{rate['n']} = {rate['rate']:.2f} [{interval[0]:.2f}, {interval[1]:.2f}]"

    for route, values in (report.get("by_route") or {}).items():
        for role, summary in values.items():
            if role == "model":
                continue
            noise = (summary.get("noise_floor") or {}).get("changed")
            method = (summary.get("required_method") or {}).get("enforced")
            lines.append(f"| {role} | {route} | {values.get('model')} | {cell(summary['wrong_rejection'])} | "
                         f"{cell(summary['wrong_acceptance'])} | {cell(method)} | {summary['unassessed']} | "
                         f"{summary['failed_cases']} | {cell(noise)} |")
    for label, summary in (report.get("gate") or {}).items():
        noise = (summary.get("noise_floor") or {}).get("changed")
        method = (summary.get("required_method") or {}).get("enforced")
        lines.append(f"| gate | {label} | rule={summary.get('rule')} | "
                     f"{cell(summary['wrong_rejection'])} | {cell(summary['wrong_acceptance'])} | "
                     f"{cell(method)} | {summary['unassessed']} | {summary['failed_cases']} | {cell(noise)} |")
    lines += ["", "Eedi MAP: " + str(report.get("eedi_map_note")), ""]
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(markdown_path)}


__all__ = [
    "ALL_ARMS",
    "CATEGORIES",
    "CELLS",
    "DEFAULT_CASES",
    "EEDI_MAP_NOTE",
    "HARNESS_VERSION",
    "HardCase",
    "LEDGER_TASKS",
    "METHOD_CELL",
    "PRODUCTION_ARM",
    "PRODUCTION_ROUTE_RULES",
    "PROVENANCES",
    "case_context",
    "gate_states",
    "gold_set_coverage",
    "judge_outcome",
    "load_cases",
    "method_criteria",
    "run_hardcases",
    "write_report",
]
