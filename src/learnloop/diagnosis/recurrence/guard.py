"""The same-answer/different-cause guard (Slice 2 §3.6).

A standing regression suite of planted pairs: two hypotheses whose errors
reach the SAME wrong answer through DIFFERENT causes (negatives), plus a few
paraphrased same-cause pairs (positives, reported for recall only). The
same-cause judge decides every pair under the live prompt version; its
verdicts go to ``judgment_ledger`` (task ``same_cause``, subject kind
``planted_hypothesis``, which never touches a vault's groups).

**Any false merge blocks the switch**: ``learnloop upgrade --to mvp-0.12``
refuses unless every REQUIRED negative pair has a verdict from the CONFIGURED
judge (its model AND reasoning effort, ``model@effort``) under the current
prompt version and input, and none of that
model's standing verdicts on them is ``same``. Verdicts from another model
never count (a route change needs a rerun, which asks the new model: reuse is
per producer), and ``--rerun`` asks the same model again, superseding its
previous verdicts.

The required suite is the built-in one (authored here: deterministic, no
learner data) plus every case registered in ``recurrence_guard_cases``: an M1
review run's planted ``same_answer_different_cause`` cases, registered the
first time ``learnloop recurrence guard --from-run`` runs them, stay required
for every later switch check.

**The diagnoser path** (second review F2). Groups also merge through
validated diagnoser citations, at the judge's authority and without any
judge call, so the judge's verdicts alone are not "zero false merges".
``--from-run`` therefore also records, for each planted case, whether the M1
diagnoser's validated citations linked the planted B answer to its A answer
(a ``diagnoser`` row on the planted pair: ``same`` = a false merge through
the citation path), and adds a judge case on the DIAGNOSER's own statement
for the B answer (when M1's planted-cause judge found it named B), not only
the authored ones. Only diagnoses in the vault's configured history mode under
the current diagnosis prompt count. The switch needs at least one such M1
case checked (S1.0's planted pairs are the standing suite, §3.6) and no false
merge on either path.
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
#: A planted case judged on the M1 diagnoser's own statement for the B answer.
DIAGNOSER_STATEMENT_SUFFIX = ":dx"
#: Rationale ``source`` of a recorded M1 diagnoser link outcome.
DIAGNOSER_LINK_SOURCE = "m1_diagnoser_link"

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


@dataclass(frozen=True)
class DiagnoserLink:
    """Whether one M1 diagnosis of a planted B answer linked its A answer."""

    case_id: str
    run_id: str
    diagnosis_id: str
    arm: str
    mode: str
    model: str
    prompt_version: str
    #: Forbidden attempts (the A answers) among the VALIDATED citations: these
    #: merge groups. Cited-but-unvalidated links never merge; reported only.
    validated_forbidden: tuple[str, ...]
    cited_forbidden: tuple[str, ...]

    @property
    def false_merge(self) -> bool:
        return bool(self.validated_forbidden)


@dataclass
class M1Run:
    run_id: str
    pairs: list[PlantedPair]
    links: list[DiagnoserLink]


def _primary_learner_statement(proposal: Mapping[str, Any]) -> str | None:
    best: tuple[float, int, int] | None = None
    chosen: str | None = None
    for event_position, event in enumerate(proposal.get("event_diagnoses") or []):
        if not isinstance(event, Mapping):
            continue
        for cause_position, cause in enumerate(event.get("candidate_causes") or []):
            if not isinstance(cause, Mapping) or str(cause.get("cause_scope") or "learner_state") != "learner_state":
                continue
            text = str(cause.get("statement") or "").strip()
            key = (-float(cause.get("prior_weight") or 0.0), event_position, cause_position)
            if text and (best is None or key < best):
                best, chosen = key, text
    return chosen


def read_m1_run(run_dir: Path, *, history_mode: str | None = None) -> M1Run:
    """An M1 review run's planted same-answer/different-cause cases (Slice 1 S1.0).

    Per case: the authored A/B pair; the diagnoser-statement pair (authored A
    against the B answer's diagnosis, in ``history_mode`` first, when M1's
    planted-cause judge said it named the target cause); and every completed
    diagnosis of the B answer with whether its citations linked an A answer.
    """

    from learnloop.db.stores.diagnosis_review import review_rows
    from learnloop.diagnosis.offline_review.runner import RUN_FILE, SCRATCH_FILE

    run_id = str(json.loads((Path(run_dir) / RUN_FILE).read_text(encoding="utf-8"))["run_id"])
    pairs: list[PlantedPair] = []
    links: list[DiagnoserLink] = []
    with closing(connect(Path(run_dir) / SCRATCH_FILE, read_only=True)) as scratch:
        targets = {
            str(row["attempt_id"]): str(row["id"])
            for row in review_rows(scratch, "review_targets", where={"run_id": run_id})
            if row.get("kind") == "planted"
        }
        diagnoses: dict[str, list[dict[str, Any]]] = {}
        for row in review_rows(scratch, "review_diagnoses", where={"run_id": run_id}):
            diagnoses.setdefault(str(row["target_id"]), []).append(row)
        receipts = {str(row["diagnosis_id"]): row for row in review_rows(scratch, "review_context_receipts")}
        cause_match: dict[str, str] = {}
        if scratch.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'judgment_ledger'").fetchone():
            for left_id, verdict in scratch.execute(
                "SELECT left_id, verdict FROM judgment_ledger WHERE task = 'planted_cause_match' "
                "AND left_kind = 'review_diagnosis' ORDER BY created_at, rowid"
            ):
                cause_match[str(left_id)] = str(verdict)
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
            case_id = f"m1:{run_id}:{row.get('id')}"
            base = PlantedPair(
                case_id=case_id,
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
            pairs.append(base)
            truth = row.get("truth") or {}
            forbidden = {str(value) for value in truth.get("forbidden_link_attempt_ids") or []} or {
                str(attempt.get("attempt_id")) for attempt in record.get("history") or [] if attempt.get("cause") == "A"
            }
            completed = [
                diagnosis for diagnosis in diagnoses.get(targets.get(str(row.get("target_attempt_id") or ""), ""), [])
                if diagnosis.get("status") == "completed" and diagnosis.get("mode") != "legacy_view"
            ]
            completed.sort(key=lambda diagnosis: (history_mode is not None and diagnosis.get("mode") != history_mode,
                                                   str(diagnosis.get("arm") or ""), str(diagnosis["id"])))
            for diagnosis in completed:
                proposal = diagnosis.get("proposal") or {}
                validated = {
                    str(citation.get("attempt_id"))
                    for citation in (receipts.get(str(diagnosis["id"])) or {}).get("validated_citations") or []
                }
                cited = {
                    str(citation.get("attempt_id"))
                    for claim in proposal.get("pattern_claims") or []
                    if isinstance(claim, Mapping) and claim.get("relation") != "disconfirming"
                    for citation in claim.get("cited") or []
                    if isinstance(citation, Mapping)
                }
                links.append(
                    DiagnoserLink(
                        case_id=case_id, run_id=run_id, diagnosis_id=str(diagnosis["id"]),
                        arm=str(diagnosis.get("arm") or ""), mode=str(diagnosis.get("mode") or ""),
                        model=str(diagnosis.get("model") or "unknown"),
                        prompt_version=str(diagnosis.get("prompt_version") or ""),
                        validated_forbidden=tuple(sorted(validated & forbidden)),
                        cited_forbidden=tuple(sorted(cited & forbidden)),
                    )
                )
            recovered = next(
                (diagnosis for diagnosis in completed if cause_match.get(str(diagnosis["id"])) == "target_cause"),
                None,
            )
            statement = _primary_learner_statement(recovered.get("proposal") or {}) if recovered else None
            if statement and statement != b:
                pairs.append(
                    PlantedPair(
                        case_id=f"{case_id}{DIAGNOSER_STATEMENT_SUFFIX}", expected="different", topic=base.topic,
                        problem=base.problem, shared_answer=base.shared_answer, statement_a=a, statement_b=statement,
                        quote_a=base.quote_a, quote_b=base.quote_b, source=base.source,
                    )
                )
    return M1Run(run_id=run_id, pairs=pairs, links=links)


def suite_from_run(run_dir: Path, *, history_mode: str | None = None) -> list[PlantedPair]:
    """Planted cases of an M1 review run (Slice 1 S1.0), as guard pairs."""

    return read_m1_run(run_dir, history_mode=history_mode).pairs


def is_link_case(pair: PlantedPair) -> bool:
    """An M1 case whose diagnoser citations are checked (not a statement pair)."""

    return pair.source.startswith("m1:") and not pair.case_id.endswith(DIAGNOSER_STATEMENT_SUFFIX)


def record_diagnoser_links(repository: Repository, links: Sequence[DiagnoserLink]) -> int:
    """Append each M1 diagnosis's link outcome as a ``diagnoser`` verdict on the planted pair (idempotent)."""

    from learnloop.ai.execution import content_key
    from learnloop.db.stores.judgments import append_judgment

    written = 0
    with repository.atomic():
        connection = repository.connection()
        for link in links:
            input_hash = content_key({"source": DIAGNOSER_LINK_SOURCE, "run": link.run_id, "diagnosis": link.diagnosis_id})
            if connection.execute(
                "SELECT 1 FROM judgment_ledger WHERE task = ? AND judge = 'diagnoser' AND input_hash = ? LIMIT 1",
                (GUARD_KIND.task, input_hash),
            ).fetchone():
                continue
            append_judgment(
                connection, task=GUARD_KIND.task, left_kind=GUARD_SUBJECT_KIND, left_id=f"{link.case_id}:a",
                right_kind=GUARD_SUBJECT_KIND, right_id=f"{link.case_id}:b", judge="diagnoser",
                judge_model=link.model or "unknown", prompt_version=link.prompt_version or "unknown",
                input_hash=input_hash, verdict="same" if link.false_merge else "different",
                rationale=json.dumps({
                    "source": DIAGNOSER_LINK_SOURCE, "run_id": link.run_id, "diagnosis_id": link.diagnosis_id,
                    "arm": link.arm, "mode": link.mode, "validated_forbidden": list(link.validated_forbidden),
                    "cited_forbidden": list(link.cited_forbidden),
                }, sort_keys=True),
            )
            written += 1
    return written


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


def guard_suite(*, from_run: Path | None = None, repository: Repository | None = None,
                history_mode: str | None = None) -> list[PlantedPair]:
    """The built-in suite, the registered cases, and an M1 run's cases (deduplicated)."""

    suite = list(BUILTIN_SUITE)
    if repository is not None:
        suite.extend(registered_cases(repository))
    if from_run is not None:
        suite.extend(suite_from_run(from_run, history_mode=history_mode))
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


def _diagnoser_link_rows(repository: Repository, *, history_mode: str | None) -> dict[frozenset[str], list[dict[str, Any]]]:
    """Recorded M1 diagnoser link outcomes under the CURRENT diagnosis prompt
    (and, given one, the configured history mode), by planted pair."""

    from learnloop.diagnosis.split.settings import DIAGNOSIS_PROMPT_VERSION

    rows: dict[frozenset[str], list[dict[str, Any]]] = {}
    with repository.connection() as connection:
        for left_id, right_id, verdict, model, rationale in connection.execute(
            "SELECT j.left_id, j.right_id, j.verdict, j.judge_model, j.rationale FROM judgment_ledger j "
            "WHERE j.task = ? AND j.judge = 'diagnoser' AND j.left_kind = ? AND j.right_kind = ? AND j.prompt_version = ? "
            "AND NOT EXISTS (SELECT 1 FROM judgment_ledger later WHERE later.supersedes_id = j.id) "
            "ORDER BY j.created_at, j.id",
            (GUARD_KIND.task, GUARD_SUBJECT_KIND, GUARD_SUBJECT_KIND, DIAGNOSIS_PROMPT_VERSION),
        ):
            try:
                detail = json.loads(rationale or "{}")
            except ValueError:
                detail = {}
            if detail.get("source") != DIAGNOSER_LINK_SOURCE:
                continue
            if history_mode is not None and detail.get("mode") != history_mode:
                continue
            rows.setdefault(frozenset((str(left_id), str(right_id))), []).append(
                {"verdict": str(verdict), "model": model, **detail}
            )
    return rows


def guard_status(
    repository: Repository,
    *,
    suite: Sequence[PlantedPair] | None = None,
    judge_model: str | None = None,
    history_mode: str | None = None,
) -> dict[str, Any]:
    """Each planted pair's standing verdicts under the current prompt and input.

    ``suite`` defaults to the REQUIRED suite (built-in plus registered cases).
    ``passed`` needs every negative judged by ``judge_model`` and none of its
    standing (not superseded) verdicts ``same``, and no M1 diagnoser citation
    linking a planted B answer to its A answer (the citation merge path);
    without ``judge_model`` any model's verdicts count (a report, never the
    switch check). ``switch_ready`` also needs at least one M1 case whose
    diagnoser link was checked under the current diagnosis prompt (in
    ``history_mode``, the vault's, when given). Positives only report recall.
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
    # The citation merge path (second review F2): M1's diagnoser on the planted B answer.
    link_rows = _diagnoser_link_rows(repository, history_mode=history_mode)
    link_cases = [pair for pair in suite if pair.expected == "different" and is_link_case(pair)]
    diagnoser_false_merges: list[str] = []
    checked = 0
    unvalidated_links = 0
    for pair in link_cases:
        rows = link_rows.get(frozenset((f"{pair.case_id}:a", f"{pair.case_id}:b")), [])
        if not rows:
            continue
        checked += 1
        if any(row["verdict"] == "same" for row in rows):
            diagnoser_false_merges.append(pair.case_id)
        unvalidated_links += sum(1 for row in rows if row["verdict"] != "same" and row.get("cited_forbidden"))
    passed = not false_merges and not missing and negatives > 0 and not diagnoser_false_merges
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
        "diagnoser": {
            "history_mode": history_mode,
            "m1_cases": len(link_cases),
            "m1_cases_checked": checked,
            "false_merges": diagnoser_false_merges,
            # Cited the A answer but the citation did not validate: no merge.
            "unvalidated_links": unvalidated_links,
        },
        "diagnoser_false_merges": diagnoser_false_merges,
        "passed": passed,
        "switch_ready": passed and checked > 0,
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
    from learnloop.diagnosis.recurrence.backlog import command_spend
    from learnloop.diagnosis.recurrence.judging import (
        default_judge_client,
        estimate_tokens,
        judge_executor,
        producer_label,
        receipt_sink,
    )
    from learnloop.matching.judge import already_judged, judge_pairs, pair_prompt

    from learnloop.diagnosis.split.live import settings_from_config

    history_mode = settings_from_config(vault).history_mode
    m1 = read_m1_run(from_run, history_mode=history_mode) if from_run is not None else None
    suite = guard_suite(repository=repository)
    if m1 is not None:
        known = {case.case_id for case in suite}
        suite.extend(case for case in m1.pairs if case.case_id not in known)
    pairs = guard_pairs(suite)
    producer = producer_label(judge_client) if judge_client is not None else configured_judge_model(vault)
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
        output_tokens=spend.output_limit(GUARD_KIND.route) * len(todo), candidates=len(todo), pairs=len(todo),
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
    if m1 is not None:
        report["m1_run"] = {
            "run_id": m1.run_id,
            "cases": sum(1 for case in m1.pairs if is_link_case(case)),
            "diagnoser_statement_cases": sum(1 for case in m1.pairs if not is_link_case(case)),
            "diagnoses": len(m1.links),
            "diagnoser_false_merges": sorted({link.case_id for link in m1.links if link.false_merge}),
        }
    if dry_run:
        report["current"] = guard_status(repository, suite=suite, judge_model=producer, history_mode=history_mode)
        return report
    if not admissible:
        report["status"] = "over_budget"
        return report
    # The run's cases are required from now on, judged or not, and its
    # diagnoser link outcomes are recorded (no call: they are M1's).
    report["registered"] = register_suite(repository, suite)
    if m1 is not None:
        report["diagnoser_links_recorded"] = record_diagnoser_links(repository, m1.links)
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
    report["result"] = guard_status(repository, suite=suite, judge_model=report["judge_model"], history_mode=history_mode)
    report["spend"] = spend.summary()
    report["status"] = "complete" if not report["not_judged"] else "incomplete"
    return report


def configured_judge_model(vault: LoadedVault) -> str | None:
    """The PRODUCER the same-cause judge route resolves to, from config alone.

    ``model@effort`` (:func:`~learnloop.diagnosis.recurrence.judging.producer_label`):
    Codex's low and medium tiers share a model, so the reasoning effort is
    part of who judged (second review F10). None when the profile names no
    model.
    """

    from learnloop.ai.routing import provider_for_task
    from learnloop.diagnosis.recurrence.judging import producer_label_for

    selection = provider_for_task(vault.config, "same_cause_judge", allow_env=False)
    profile = vault.config.ai.providers.get(selection.provider_name)
    model = getattr(profile, "model", None) if profile is not None else None
    if not model:
        return None
    return producer_label_for(model=model, effort=getattr(profile, "reasoning_effort", None))


__all__ = [
    "BUILTIN_SUITE",
    "DiagnoserLink",
    "M1Run",
    "GUARD_KIND",
    "GUARD_SUBJECT_KIND",
    "GUARD_SUITE_VERSION",
    "PlantedPair",
    "configured_judge_model",
    "guard_pairs",
    "guard_status",
    "guard_suite",
    "is_link_case",
    "read_m1_run",
    "record_diagnoser_links",
    "register_suite",
    "registered_cases",
    "run_guard",
    "suite_from_run",
    "suite_hash",
]
