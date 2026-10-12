"""The same-answer/different-cause guard (Slice 2 §3.6).

A standing regression suite of planted pairs: two hypotheses whose errors
reach the SAME wrong answer through DIFFERENT causes (negatives), plus a few
paraphrased same-cause pairs (positives, reported for recall only). The
same-cause judge decides every pair under the live prompt version; its
verdicts go to ``judgment_ledger`` (task ``same_cause``, subject kind
``planted_hypothesis``, which never touches a vault's groups).

**Any false merge blocks the switch**: ``learnloop upgrade --to mvp-0.11``
refuses unless every REQUIRED negative pair has a verdict from the CONFIGURED
judge model under the current prompt version and input, and none of that
model's standing verdicts on them is ``same``. Verdicts from another model
never count (a route change needs a rerun, which asks the new model: reuse is
per producer), and ``--rerun`` asks the same model again, superseding its
previous verdicts.

The required suite is the built-in one (authored here: deterministic, no
learner data) plus every case registered in ``recurrence_guard_cases``: an M1
review run's planted ``same_answer_different_cause`` cases, registered the
first time ``learnloop recurrence guard --from-run`` runs them, stay required
for every later switch check.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.diagnosis.recurrence.kind import SAME_CAUSE
from learnloop.matching.judge import pair_input_hash
from learnloop.matching.kinds import MatchKind, Subject
from learnloop.matching.shortlist import CandidatePair
from learnloop.vault.models import LoadedVault

GUARD_SUBJECT_KIND = "planted_hypothesis"
GUARD_SUITE_VERSION = "same-answer-different-cause-v1"

#: The guard judges with exactly the live kind, prompt and route; only the
#: ledger subject kind differs so planted rows can never join vault groups.
GUARD_KIND = MatchKind(
    name=SAME_CAUSE.name,
    task=SAME_CAUSE.task,
    subject_kind=GUARD_SUBJECT_KIND,
    record_kind=SAME_CAUSE.record_kind,
    field=SAME_CAUSE.field,
    task_prefix=SAME_CAUSE.task_prefix,
    route=SAME_CAUSE.route,
    purpose=SAME_CAUSE.purpose,
    prompt_version=SAME_CAUSE.prompt_version,
    question=SAME_CAUSE.question,
    guidance=SAME_CAUSE.guidance,
    render=SAME_CAUSE.render,
    recipe=SAME_CAUSE.recipe,
)


@dataclass(frozen=True)
class PlantedPair:
    case_id: str
    expected: str  # different (same answer, different cause) | same (paraphrase)
    topic: str
    problem: str
    shared_answer: str | None
    statement_a: str
    statement_b: str
    quote_a: str | None = None
    quote_b: str | None = None
    source: str = "builtin"


def _case(expected: str, topic: str, problem: str, answer: str | None, a: str, b: str,
          quote_a: str | None = None, quote_b: str | None = None) -> PlantedPair:
    digest = hashlib.sha256(json.dumps([expected, topic, problem, a, b], sort_keys=True).encode()).hexdigest()[:16]
    return PlantedPair(f"builtin:{digest}", expected, topic, problem, answer, a, b, quote_a, quote_b)


#: Authored cases. Each negative's two causes reach the shared wrong answer.
BUILTIN_SUITE: tuple[PlantedPair, ...] = (
    _case("different", "Linear equations", "Solve 3x - 5 = 10.", "x = 15",
          "Believes that once the constant is moved across, the coefficient of x can be ignored, so 3x = 15 gives x = 15.",
          "Moves -5 across without changing its sign and then multiplies by the coefficient instead of dividing: 3x = 5 so x = 15.",
          "3x = 15 so x = 15", "3x = 5, x = 5 * 3 = 15"),
    _case("different", "Area of a circle", "Find the area of a circle with diameter 6.", "6π",
          "Uses the circumference formula π·d when asked for the area.",
          "Halves the diameter correctly to r = 3 but believes r² means 2r, so the area is π·2·3.",
          "A = π d = 6π", "r = 3, r² = 6, A = 6π"),
    _case("different", "Expanding brackets", "Expand (x + 3)².", "x² + 9",
          "Believes the square of a sum is the sum of the squares (the exponent distributes over addition).",
          "Multiplies (x + 3)(x + 3) out term by term, then cancels the two cross terms 3x and 3x as if a term and its reverse sum to zero.",
          "(x+3)² = x² + 3²", "x² + 3x + 3x + 9 = x² + 9"),
    _case("different", "2x2 determinants", "Find det [[2, 1], [4, 3]].", "10",
          "Believes the determinant of a 2x2 matrix is ad + bc instead of ad - bc.",
          "Believes the determinant of a matrix is the sum of all of its entries.",
          "2·3 + 1·4 = 10", "2 + 1 + 4 + 3 = 10"),
    _case("different", "Definite integrals", "Evaluate the integral of 2x from 0 to 3.", "18",
          "Believes the antiderivative of 2x is 2x² (multiplies by x instead of raising the power and dividing).",
          "Believes a definite integral is the area of a rectangle whose height is the integrand's largest value on the interval.",
          "∫2x dx = 2x², 2·9 = 18", "height 6, width 3, area 18"),
    _case("different", "Probability with coins", "Two fair coins are tossed. Find P(at least one head).", "1/2",
          "Confuses 'at least one head' with 'exactly one head'.",
          "Believes the second coin must match the first, so only one toss matters.",
          "exactly one head: HT or TH, 2/4 = 1/2", "both coins land the same way, so P = 1/2"),
    _case("different", "Slope", "Find the slope through (1, 2) and (3, 8).", "1/3",
          "Believes slope is run over rise (change in x divided by change in y).",
          "Computes rise over run correctly as 3 and then takes the reciprocal, believing a slope must be less than 1.",
          "(3 - 1)/(8 - 2) = 1/3", "6/2 = 3, so the slope is 1/3"),
    _case("different", "Mean", "Find the mean of 2, 4 and 9.", "4",
          "Confuses the mean with the median (the middle value).",
          "Makes an addition slip, adding 2 + 4 + 9 to 12, and then divides correctly by 3.",
          "middle value is 4", "2 + 4 + 9 = 12, 12/3 = 4"),
    _case("different", "Transpose of a product", "Simplify (AB)ᵀ.", "AᵀBᵀ",
          "Believes the transpose of a product is the product of the transposes in the same order.",
          "Knows the order reverses to BᵀAᵀ but believes matrix multiplication commutes, so rewrites it as AᵀBᵀ.",
          "(AB)ᵀ = AᵀBᵀ", "BᵀAᵀ = AᵀBᵀ since order does not matter"),
    _case("different", "Area units", "Convert 3 m² to cm².", "300 cm²",
          "Uses the linear conversion factor (×100) for an area unit instead of squaring it.",
          "Believes 1 m = 10 cm and then correctly squares the factor to ×100.",
          "3 × 100 = 300", "1 m = 10 cm so 1 m² = 100 cm², 300"),
    _case("same", "Adding fractions", "Find 1/2 + 1/3.", "2/5",
          "Believes fractions are added by adding the numerators and adding the denominators.",
          "Adds the tops and adds the bottoms when combining two fractions."),
    _case("same", "Area of a circle", "Find the area of a circle with diameter 10.", "100π",
          "Uses the diameter in place of the radius in A = πr².",
          "Plugs the circle's full width into the area formula where half of it belongs."),
    _case("same", "Chain rule", "Differentiate sin(3x).", "cos(3x)",
          "Forgets the chain rule's inner derivative when differentiating a composite function.",
          "Differentiates the outside function and leaves out the factor coming from the inside function."),
    _case("same", "Squaring a sum", "Expand (a + b)².", "a² + b²",
          "Believes the square of a sum equals the sum of the squares.",
          "Writes (a + b)² as a² + b², dropping the 2ab term."),
    _case("same", "Union of events", "P(A) = 0.5, P(B) = 0.4, P(A and B) = 0.2. Find P(A or B).", "0.9",
          "Believes P(A or B) = P(A) + P(B) even when the events overlap.",
          "Adds the two probabilities without subtracting the probability that both happen."),
)


def suite_from_run(run_dir: Path) -> list[PlantedPair]:
    """Planted cases of an M1 review run (Slice 1 S1.0), as guard pairs."""

    from learnloop.db.stores.diagnosis_review import review_rows
    from learnloop.diagnosis.offline_review.runner import RUN_FILE, SCRATCH_FILE

    run_id = str(json.loads((Path(run_dir) / RUN_FILE).read_text(encoding="utf-8"))["run_id"])
    pairs: list[PlantedPair] = []
    with closing(connect(Path(run_dir) / SCRATCH_FILE, read_only=True)) as scratch:
        for row in review_rows(scratch, "review_planted_cases", where={"run_id": run_id}):
            record = row.get("history") or {}
            if str(row.get("shape") or record.get("shape") or "") != "same_answer_different_cause":
                continue
            causes = record.get("causes") or {}
            a, b = str(causes.get("A") or "").strip(), str(causes.get("B") or "").strip()
            if not (a and b):
                continue
            target = record.get("target") or {}
            earlier = next(
                (attempt for attempt in record.get("history") or [] if attempt.get("cause") == "A"),
                {},
            )
            pairs.append(
                PlantedPair(
                    case_id=f"m1:{run_id}:{row.get('id')}",
                    expected="different",
                    topic=str(record.get("learning_object_id") or ""),
                    problem=str(target.get("practice_item_id") or ""),
                    shared_answer=target.get("final_answer"),
                    statement_a=a,
                    statement_b=b,
                    quote_a=earlier.get("first_divergence_quote"),
                    quote_b=target.get("first_divergence_quote"),
                    source=f"m1:{run_id}",
                )
            )
    return pairs


def _subject(pair: PlantedPair, side: str) -> Subject:
    statement = pair.statement_a if side == "a" else pair.statement_b
    quote = pair.quote_a if side == "a" else pair.quote_b
    digest = hashlib.sha256(statement.encode("utf-8")).hexdigest()
    return Subject(
        kind=GUARD_SUBJECT_KIND,
        id=f"{pair.case_id}:{side}",
        text=statement,
        content_hash=digest,
        view={
            "statement": statement,
            "learning_object": pair.topic,
            "first_divergence_quote": quote,
        },
    )


def guard_pairs(suite: Sequence[PlantedPair]) -> list[CandidatePair]:
    return [
        CandidatePair(left=_subject(pair, "a"), right=_subject(pair, "b"), score=0.0, rank=0, model_id="guard", basis="planted")
        for pair in suite
    ]


def registered_cases(repository: Repository) -> list[PlantedPair]:
    """The planted cases registered as required (beyond the built-in suite)."""

    return [
        PlantedPair(
            case_id=str(row["case_id"]), expected=str(row["expected"]), topic=str(row.get("topic") or ""),
            problem=str(row.get("problem") or ""), shared_answer=row.get("shared_answer"),
            statement_a=str(row["statement_a"]), statement_b=str(row["statement_b"]),
            quote_a=row.get("quote_a"), quote_b=row.get("quote_b"), source=str(row["source"]),
        )
        for row in repository.recurrence_guard_cases()
    ]


def register_suite(repository: Repository, cases: Sequence[PlantedPair]) -> int:
    """Make cases required for the switch (idempotent by case id)."""

    from learnloop.db.stores.recurrence import register_guard_cases

    extra = [case for case in cases if case.source != "builtin"]
    if not extra:
        return 0
    with repository.atomic():
        return register_guard_cases(
            repository.connection(),
            [{**case.__dict__, "suite_version": GUARD_SUITE_VERSION} for case in extra],
        )


def guard_suite(*, from_run: Path | None = None, repository: Repository | None = None) -> list[PlantedPair]:
    """The built-in suite, the registered cases, and an M1 run's cases (deduplicated)."""

    suite = list(BUILTIN_SUITE)
    if repository is not None:
        suite.extend(registered_cases(repository))
    if from_run is not None:
        suite.extend(suite_from_run(from_run))
    seen: set[str] = set()
    unique = []
    for case in suite:
        if case.case_id not in seen:
            seen.add(case.case_id)
            unique.append(case)
    return unique


def suite_hash(suite: Sequence[PlantedPair]) -> str:
    return hashlib.sha256(
        json.dumps([[pair.case_id, pair.expected, pair.statement_a, pair.statement_b] for pair in suite]).encode()
    ).hexdigest()[:16]


def guard_status(
    repository: Repository,
    *,
    suite: Sequence[PlantedPair] | None = None,
    judge_model: str | None = None,
) -> dict[str, Any]:
    """Each planted pair's standing verdicts under the current prompt and input.

    ``suite`` defaults to the REQUIRED suite (built-in plus registered cases).
    ``passed`` needs every negative judged by ``judge_model`` and none of its
    standing (not superseded) verdicts ``same``; without ``judge_model`` any
    model's verdicts count (a report, never the switch check). Positives only
    report recall.
    """

    suite = list(suite if suite is not None else guard_suite(repository=repository))
    verdicts: dict[frozenset[str], list[dict[str, Any]]] = {}
    with repository.connection() as connection:
        for row in connection.execute(
            "SELECT j.left_id, j.right_id, j.verdict, j.judge_model, j.input_hash FROM judgment_ledger j "
            "WHERE j.task = ? AND j.judge = 'llm' AND j.prompt_version = ? AND j.left_kind = ? AND j.right_kind = ? "
            "AND NOT EXISTS (SELECT 1 FROM judgment_ledger later WHERE later.supersedes_id = j.id) "
            "ORDER BY j.created_at, j.id",
            (GUARD_KIND.task, GUARD_KIND.prompt_version, GUARD_SUBJECT_KIND, GUARD_SUBJECT_KIND),
        ):
            if judge_model is not None and str(row[3]) != judge_model:
                continue
            verdicts.setdefault(frozenset((str(row[0]), str(row[1]))), []).append(
                {"verdict": str(row[2]), "judge_model": row[3], "input_hash": row[4]}
            )
    false_merges: list[str] = []
    missing: list[str] = []
    recall_hits = 0
    positives = 0
    models: set[str] = set()
    for pair, candidate in zip(suite, guard_pairs(suite), strict=True):
        expected_hash = pair_input_hash(GUARD_KIND, candidate.left, candidate.right)
        # Verdicts on different text (the suite changed since) do not count.
        found = [
            row for row in verdicts.get(frozenset((candidate.left.id, candidate.right.id)), [])
            if row["input_hash"] == expected_hash
        ]
        models.update(str(row["judge_model"]) for row in found if row.get("judge_model"))
        if pair.expected == "different":
            if not found:
                missing.append(pair.case_id)
            elif any(row["verdict"] == "same" for row in found):
                false_merges.append(pair.case_id)
        else:
            positives += 1
            if found and found[-1]["verdict"] == "same":
                recall_hits += 1
    negatives = sum(1 for pair in suite if pair.expected == "different")
    return {
        "suite_version": GUARD_SUITE_VERSION,
        "suite_hash": suite_hash(suite),
        "cases": len(suite),
        "registered_cases": sum(1 for pair in suite if pair.source != "builtin"),
        "prompt_version": GUARD_KIND.prompt_version,
        "judge_model": judge_model,
        "judge_models_seen": sorted(models),
        "negatives": negatives,
        "negatives_judged": negatives - len(missing),
        "false_merges": false_merges,
        "missing": missing,
        "positives": positives,
        "positives_merged": recall_hits,
        "passed": not false_merges and not missing and negatives > 0,
    }


def run_guard(
    vault: LoadedVault,
    repository: Repository,
    *,
    caps: Any,
    price_per_million: float | None = None,
    from_run: Path | None = None,
    dry_run: bool = False,
    rerun: bool = False,
    cancelled: Any = None,
    judge_client: Any = None,
) -> dict[str, Any]:
    """Judge every required planted pair the configured judge has not judged.

    ``from_run`` adds an M1 run's cases and (unless ``dry_run``) registers
    them as required. ``rerun`` asks the judge again on every pair and its
    verdicts supersede that model's earlier ones.
    """

    from learnloop.ai.execution import record_model_calls
    from learnloop.ai.spend import SpendLimitExceeded
    from learnloop.diagnosis.recurrence.backlog import JUDGE_OUTPUT_TOKENS, command_spend
    from learnloop.diagnosis.recurrence.judging import (
        default_judge_client,
        estimate_tokens,
        judge_executor,
        model_label,
        receipt_sink,
    )
    from learnloop.matching.judge import already_judged, judge_pairs, pair_prompt

    suite = guard_suite(from_run=from_run, repository=repository)
    pairs = guard_pairs(suite)
    producer = model_label(judge_client) if judge_client is not None else configured_judge_model(vault)
    spend = command_spend(vault, caps, price_per_million=price_per_million, cancelled=cancelled, embedding=False)
    with repository.connection() as connection:
        todo = [
            pair for pair in pairs
            if rerun or not already_judged(connection, GUARD_KIND, pair.left, pair.right,
                                           input_hash=pair_input_hash(GUARD_KIND, pair.left, pair.right),
                                           producer=producer)
        ]
    prompt_tokens = sum(estimate_tokens(pair_prompt(GUARD_KIND, pair.left, pair.right)) for pair in todo)
    estimate = spend.estimate(
        GUARD_KIND.route, calls=len(todo), input_tokens=prompt_tokens,
        output_tokens=JUDGE_OUTPUT_TOKENS * len(todo), candidates=len(todo), pairs=len(todo),
    )
    admissible, refusal = True, None
    try:
        spend.check(estimate)
    except SpendLimitExceeded as exc:
        admissible, refusal = False, str(exc)
    report: dict[str, Any] = {
        "status": "dry_run" if dry_run else "pending",
        "suite_version": GUARD_SUITE_VERSION,
        "suite_hash": suite_hash(suite),
        "cases": len(suite),
        "negatives": sum(1 for pair in suite if pair.expected == "different"),
        "judge_model": producer,
        "rerun": rerun,
        "pairs_to_judge": len(todo),
        "estimate": {"calls": estimate.calls, "metered_tokens": estimate.total_tokens, "metered_usd": estimate.estimated_usd},
        "routes": {route: info.as_dict() for route, info in spend.routes.items()},
        "caps": caps.as_dict(),
        "admissible": admissible,
        "refusal": refusal,
    }
    if dry_run:
        report["current"] = guard_status(repository, suite=suite, judge_model=producer)
        return report
    if not admissible:
        report["status"] = "over_budget"
        return report
    # The run's cases are required from now on, judged or not.
    report["registered"] = register_suite(repository, suite)
    results = []
    if todo:
        client = judge_client if judge_client is not None else default_judge_client(vault)
        if client is None:
            report.update(status="provider_failed", reason="the same-cause judge route is not ready")
            return report
        owner_id = repository.sqlite_path.parent.name
        spend.collector.sink = receipt_sink(repository, owner_kind="recurrence_guard", owner_id=owner_id)
        with record_model_calls(repository, owner_kind="recurrence_guard", owner_id=owner_id):
            executor = judge_executor(spend, client)
            report["judge_model"] = executor.producer
            results = judge_pairs(repository, GUARD_KIND, todo, execute=executor, rerun=rerun)
    report["judged"] = sum(1 for row in results if row.status == "judged")
    report["not_judged"] = [
        row.as_dict() for row in results if row.status in ("failed", "not_run", "claimed_elsewhere", "fenced")
    ]
    report["result"] = guard_status(repository, suite=suite, judge_model=report["judge_model"])
    report["spend"] = spend.summary()
    report["status"] = "complete" if not report["not_judged"] else "incomplete"
    return report


def configured_judge_model(vault: LoadedVault) -> str | None:
    """The model the same-cause judge route resolves to, from config alone."""

    from learnloop.ai.routing import provider_for_task

    selection = provider_for_task(vault.config, "same_cause_judge", allow_env=False)
    profile = vault.config.ai.providers.get(selection.provider_name)
    model = getattr(profile, "model", None) if profile is not None else None
    return str(model) if model else None


__all__ = [
    "BUILTIN_SUITE",
    "GUARD_KIND",
    "GUARD_SUBJECT_KIND",
    "GUARD_SUITE_VERSION",
    "PlantedPair",
    "configured_judge_model",
    "guard_pairs",
    "guard_status",
    "guard_suite",
    "register_suite",
    "registered_cases",
    "run_guard",
    "suite_from_run",
    "suite_hash",
]
