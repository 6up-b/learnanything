"""Adaptive hints H2a: discriminating questions, chosen by expected information gain (spec §4.2, G-H16).

**Rivals.** The open explanations of the learner's trouble on the item, on
every surface: the open hypotheses and the durable misconceptions on the
item's LO as the diagnoser's overlay shows them (never the raw error events,
which miss the diagnoser's statements on split vaults, Reader §3.4 item 1);
the rival causes of the item's latest diagnosed attempt
(``unresolved_cause_factors.candidate_causes_json``); and the beliefs named
from this attempt's learner text (``learner_text_gaps`` of kind
misconception on the item since its last attempt). Deduplicated by
statement; a prompt-size bound keeps the first :data:`MAX_RIVALS`.

**Selection.** The writer proposes a few candidate questions, each with the
answer it predicts under each rival. Each candidate is compiled as an
instrument (one conditional row per rival: all its mass on the answer that
rival predicts, over the distinct predicted answers) and ranked with the
existing ``instrument_expected_information_gain`` under the rivals' weights.
H2a has no posterior over these rivals (an open probe episode's hypotheses
are a different set, and a facet's ``hypothesis_marginal`` is not tied to
them), so the weights are **uniform, and labelled so**. The learner's answer
is compared with the predictions by code, so no grader channel applies
(reliability 1). A candidate whose rivals all predict the same answer has
zero EIG by construction and is dropped; nothing is hand-weighted and no
model call is added.

**Never evidence.** The learner's answer is a ``help_assists`` row
(``discriminate_answer``); it moves no posterior and writes no probe
observation (the EIG function is a pure read: an ``ignore_imports`` line of
``hints-never-write-evidence``).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import closing
from dataclasses import asdict, dataclass
import hashlib
import json
import re
from typing import Any

from learnloop.db.connection import connect

#: A prompt-size bound on the rivals one hint reads (not a judgment).
MAX_RIVALS = 6
#: The weights' basis, recorded on every discriminating row (§4.2).
WEIGHTS_BASIS = "uniform"
#: The compiled candidate's grader policy and provenance (for the record).
GRADER_POLICY = "hint_discriminating_v1"
PROVENANCE = "hint_candidate"
#: An EIG at or below this is zero (float noise from equal predictions).
EIG_EPSILON = 1e-12
#: Cause scopes that explain the learner's trouble (not the item or grader).
_LEARNER_SCOPES = frozenset({"learner_state", "transient_execution", "unknown"})


@dataclass(frozen=True)
class Rival:
    """One open explanation, as typed records for the writer (statement and
    status, no prose; §4.6)."""

    id: str
    statement: str
    source: str
    source_id: str
    status: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalize(text: str) -> str:
    return " ".join(str(text or "").lower().split())


def rival_id(statement: str) -> str:
    return "rv_" + hashlib.sha256(_normalize(statement).encode("utf-8")).hexdigest()[:10]


def _since_last_attempt(repository: Any, practice_item_id: str) -> tuple[str | None, str | None]:
    rows = repository.list_recent_attempts_by_practice_item(practice_item_id, limit=1)
    if not rows:
        return None, None
    return str(rows[0].get("created_at") or "") or None, str(rows[0].get("id") or "") or None


def open_rivals(repository: Any, item: Any) -> list[Rival]:
    """The item's open rival explanations (local reads only)."""

    found: list[Rival] = []
    seen: set[str] = set()

    def add(statement: Any, source: str, source_id: Any, status: str) -> None:
        text = " ".join(str(statement or "").split())
        key = _normalize(text)
        if not key or key in seen or len(found) >= MAX_RIVALS:
            return
        seen.add(key)
        found.append(Rival(rival_id(text), text, source, str(source_id or ""), status))

    lo = item.learning_object_id
    for hypothesis in repository.causal_hypotheses_for_learning_object(lo, statuses=("candidate",)):
        if str(hypothesis.get("cause_scope") or "unknown") in _LEARNER_SCOPES:
            add(hypothesis.get("statement"), "hypothesis", hypothesis.get("id"), "candidate")
    for event in repository.active_errors_by_learning_object_overlaid(lo):
        if event.is_misconception and event.misconception_statement:
            add(event.misconception_statement, "misconception", event.misconception_id or event.id, "active")
    since, last_attempt = _since_last_attempt(repository, item.id)
    if last_attempt:
        for factor in repository.unresolved_cause_factors_for_attempt(last_attempt):
            for cause in factor.get("candidate_causes") or ():
                if isinstance(cause, Mapping):
                    add(cause.get("statement"), "cause_factor", factor.get("id"), "open")
    for gap in _named_gaps(repository, item.id, since):
        add(gap[1], "named_gap", gap[0], "named")
    return found


def _named_gaps(repository: Any, practice_item_id: str, since: str | None) -> list[tuple[str, str]]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if connection.execute("SELECT 1 FROM sqlite_master WHERE name = 'learner_text_gaps'").fetchone() is None:
            return []
        rows = connection.execute(
            "SELECT id, named_json, created_at FROM learner_text_gaps WHERE practice_item_id = ? "
            "AND kind = 'misconception' ORDER BY created_at, id", (practice_item_id,)).fetchall()
    out: list[tuple[str, str]] = []
    for gap_id, named_json, created_at in rows:
        if since is not None and str(created_at or "") <= since:
            continue
        try:
            named = json.loads(named_json or "{}")
        except (TypeError, ValueError):
            named = {}
        statement = str((named or {}).get("belief_statement") or "").strip() if isinstance(named, Mapping) else ""
        if statement:
            out.append((str(gap_id), statement))
    return out


# ---------------------------------------------------------------------------
# Candidates and their ranking
# ---------------------------------------------------------------------------

def normalize_answer(text: str) -> str:
    """A predicted or given answer as a comparable string (math delimiters,
    case and spacing ignored): two rivals predicting ``$0$`` and ``0`` agree."""

    from learnloop.hints.maps import norm

    return re.sub(r"\s+", " ", norm(str(text or "")).lower()).strip(" .")


@dataclass(frozen=True)
class RankedCandidate:
    index: int
    question_md: str
    predictions: dict[str, str]
    eig_nats: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def compile_candidate(predictions: Mapping[str, str]) -> Any:
    """One candidate as an instrument: per rival, all its mass on the answer
    that rival predicts, over the distinct predicted answers."""

    from learnloop.diagnosis.probe_families import CompiledInstrument

    normalized = {rival: normalize_answer(answer) for rival, answer in predictions.items()}
    alphabet = tuple(sorted(set(normalized.values())))
    rows = {rival: {outcome: (1.0 if outcome == answer else 0.0) for outcome in alphabet}
            for rival, answer in normalized.items()}
    return CompiledInstrument(outcome_alphabet=alphabet, rows=rows, pseudo_count=0.0,
                              grader_policy=GRADER_POLICY, provenance=PROVENANCE)


def rank_candidates(candidates: Sequence[Mapping[str, Any]], rivals: Sequence[Rival]) -> list[RankedCandidate]:
    """Every candidate naming at least two of the request's rivals, scored by
    ``instrument_expected_information_gain`` under uniform weights, best
    first (ties keep the writer's order). Zero-EIG candidates are kept in the
    list with their score; :func:`best_candidate` drops them."""

    from learnloop.diagnosis.probe_families import instrument_expected_information_gain

    known = {rival.id for rival in rivals}
    ranked: list[RankedCandidate] = []
    for index, candidate in enumerate(candidates):
        predictions = {str(entry.get("rival_id")): str(entry.get("answer") or "")
                       for entry in candidate.get("predictions") or () if str(entry.get("rival_id")) in known}
        if len(predictions) < 2:
            continue
        instrument = compile_candidate(predictions)
        weights = {rival: 1.0 / len(predictions) for rival in predictions}
        eig = instrument_expected_information_gain(weights, instrument, {rival: rival for rival in predictions},
                                                   grader_reliability=1.0)
        ranked.append(RankedCandidate(index, str(candidate.get("question_md") or ""), predictions, float(eig)))
    ranked.sort(key=lambda entry: (-entry.eig_nats, entry.index))
    return ranked


def best_candidate(ranked: Sequence[RankedCandidate]) -> RankedCandidate | None:
    """The best candidate with positive EIG, or None (§4.2: no positive EIG,
    no discriminating question is shown)."""

    for entry in ranked:
        if entry.eig_nats > EIG_EPSILON:
            return entry
    return None


def states_a_rival(question_md: str, rivals: Sequence[Rival]) -> str | None:
    """A rival the question states outright (its statement, or most of its
    content words), which the kind's contract forbids (§4.2: "never states
    either rival"); the rival's id, or None."""

    question = _normalize(question_md)
    for rival in rivals:
        statement = _normalize(rival.statement)
        if len(statement) >= 12 and statement in question:
            return rival.id
        words = {word for word in re.findall(r"[a-z0-9]+", statement) if len(word) > 3}
        if len(words) >= 4:
            present = {word for word in re.findall(r"[a-z0-9]+", question) if len(word) > 3}
            if len(words & present) / len(words) >= 0.8:
                return rival.id
    return None


__all__ = [
    "EIG_EPSILON",
    "MAX_RIVALS",
    "RankedCandidate",
    "Rival",
    "WEIGHTS_BASIS",
    "best_candidate",
    "compile_candidate",
    "normalize_answer",
    "open_rivals",
    "rank_candidates",
    "rival_id",
    "states_a_rival",
]
