"""B2 blinded persona-vs-real realism matcher.

The matcher sees only observable answer text.  It receives neither grades nor
diagnoses, fits its text-shape baseline out of fold, and persists only aggregate
scores plus a content hash.  A separable corpus does not license synthetic
diagnostic scores; an insufficient corpus is an abstention, never a pass.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository


PERSONA_REALISM_MATCHER_VERSION = "persona_realism_blind_stylometry_v1"
DEFAULT_SEPARATION_THRESHOLD = 0.70
MIN_TRACES_PER_ARM = 4

_WORD_RE = re.compile(r"[A-Za-z0-9_]+(?:['’-][A-Za-z0-9_]+)?")
_SENTENCE_RE = re.compile(r"[.!?]+")
_MATH_RE = re.compile(r"[=+\-*/^√∑∫]|\\[a-zA-Z]+")
_HEDGE_RE = re.compile(
    r"\b(?:maybe|perhaps|probably|i think|i guess|not sure|might|could)\b",
    re.IGNORECASE,
)
_FIRST_PERSON_RE = re.compile(r"\b(?:i|i'm|i've|me|my)\b", re.IGNORECASE)
_MARKDOWN_RE = re.compile(r"(?:^|\s)(?:[-*] |\d+[.)] |#{1,6} |```)", re.MULTILINE)

FEATURE_NAMES: tuple[str, ...] = (
    "log_words",
    "mean_word_length",
    "lexical_diversity",
    "sentence_density",
    "punctuation_density",
    "digit_density",
    "math_density",
    "line_density",
    "first_person_density",
    "hedge_density",
    "markdown_density",
    "uppercase_density",
)


@dataclass(frozen=True)
class PersonaRealismReport:
    run_id: str | None
    verdict: str
    balanced_accuracy: float | None
    separation_threshold: float
    persona_count: int
    real_count: int
    matcher_correct: int
    matcher_total: int
    generator_family: str | None
    note: str

    @property
    def licensed(self) -> bool:
        return self.verdict == "indistinguishable"

    def as_dict(self) -> dict[str, Any]:
        return {
            "matcher_version": PERSONA_REALISM_MATCHER_VERSION,
            "run_id": self.run_id,
            "verdict": self.verdict,
            "licensed": self.licensed,
            "balanced_accuracy": self.balanced_accuracy,
            "separation_threshold": self.separation_threshold,
            "persona_count": self.persona_count,
            "real_count": self.real_count,
            "matcher_correct": self.matcher_correct,
            "matcher_total": self.matcher_total,
            "generator_family": self.generator_family,
            "note": self.note,
        }


def text_features(text: str) -> tuple[float, ...]:
    """Bounded, content-agnostic text-shape features used by the blind matcher."""

    body = str(text or "")
    words = _WORD_RE.findall(body)
    word_count = max(len(words), 1)
    chars = max(len(body), 1)
    alpha = [char for char in body if char.isalpha()]
    return (
        math.log1p(len(words)),
        sum(len(word) for word in words) / word_count,
        len({word.casefold() for word in words}) / word_count,
        len(_SENTENCE_RE.findall(body)) / word_count,
        sum(not char.isalnum() and not char.isspace() for char in body) / chars,
        sum(char.isdigit() for char in body) / chars,
        len(_MATH_RE.findall(body)) / word_count,
        max(body.count("\n") + 1, 1) / word_count,
        len(_FIRST_PERSON_RE.findall(body)) / word_count,
        len(_HEDGE_RE.findall(body)) / word_count,
        len(_MARKDOWN_RE.findall(body)) / word_count,
        sum(char.isupper() for char in alpha) / max(len(alpha), 1),
    )


def _distance(left: Sequence[float], right: Sequence[float]) -> float:
    return sum((a - b) ** 2 for a, b in zip(left, right))


def _centroid(rows: Sequence[Sequence[float]]) -> tuple[float, ...]:
    return tuple(sum(row[index] for row in rows) / len(rows) for index in range(len(rows[0])))


def _standardize(
    train: Sequence[Sequence[float]],
    row: Sequence[float],
) -> tuple[float, ...]:
    means = _centroid(train)
    scales: list[float] = []
    for index, mean in enumerate(means):
        variance = sum((value[index] - mean) ** 2 for value in train) / max(len(train) - 1, 1)
        scales.append(math.sqrt(variance) or 1.0)
    return tuple((value - means[index]) / scales[index] for index, value in enumerate(row))


def _blind_leave_pair_out(
    persona_rows: Sequence[Sequence[float]],
    real_rows: Sequence[Sequence[float]],
) -> tuple[float, int, int]:
    """Paired folds prevent the held-out arm itself becoming a classifier cue."""

    folds = min(len(persona_rows), len(real_rows))
    arm_correct = {0: 0, 1: 0}
    arm_total = {0: 0, 1: 0}
    for held_index in range(folds):
        train_persona = [
            tuple(row)
            for index, row in enumerate(persona_rows[:folds])
            if index != held_index
        ]
        train_real = [
            tuple(row)
            for index, row in enumerate(real_rows[:folds])
            if index != held_index
        ]
        train = train_real + train_persona
        train_labels = [0] * len(train_real) + [1] * len(train_persona)
        standardized_train = [_standardize(train, row) for row in train]
        centroids = {
            arm: _centroid(
                [
                    row
                    for row, row_label in zip(standardized_train, train_labels)
                    if row_label == arm
                ]
            )
            for arm in (0, 1)
        }
        held_pair = (
            (tuple(real_rows[held_index]), 0),
            (tuple(persona_rows[held_index]), 1),
        )
        for held, label in held_pair:
            standardized_held = _standardize(train, held)
            predicted = min(
                (0, 1),
                key=lambda arm: (
                    _distance(standardized_held, centroids[arm]),
                    arm,
                ),
            )
            arm_total[label] += 1
            arm_correct[label] += int(predicted == label)
    balanced = sum(arm_correct[arm] / arm_total[arm] for arm in (0, 1)) / 2
    # A matcher is allowed to invert its output labels.  Accuracy substantially
    # below chance is therefore just as separable as accuracy above chance.
    separability = max(balanced, 1.0 - balanced)
    return separability, sum(arm_correct.values()), sum(arm_total.values())


def trace_corpus_hash(traces: Iterable[str]) -> str:
    """Order-independent content identity for one matcher arm."""

    payload = sorted(
        hashlib.sha256(text.encode("utf-8")).hexdigest() for text in traces
    )
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _corpus_hash(persona: Iterable[str], real: Iterable[str]) -> str:
    payload = {
        "persona": trace_corpus_hash(persona),
        "real": trace_corpus_hash(real),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def match_persona_realism(
    repository: Repository,
    persona_traces: Sequence[str],
    *,
    real_traces: Sequence[str] | None = None,
    persona_source: str = "authored_signature",
    generator_provider: str | None = None,
    generator_model: str | None = None,
    generator_family: str | None = None,
    separation_threshold: float = DEFAULT_SEPARATION_THRESHOLD,
    persist: bool = True,
    clock: Clock | None = None,
) -> PersonaRealismReport:
    """Run B2 and optionally append its aggregate result.

    ``real_traces=None`` reads the vault corpus.  Explicit traces are useful for
    a held-out evaluation or a deterministic test; neither path ever persists
    the trace text.
    """

    if not 0.5 <= separation_threshold <= 1.0:
        raise ValueError("separation_threshold must be in [0.5, 1.0]")
    persona = [str(trace).strip() for trace in persona_traces if str(trace).strip()]
    if real_traces is None:
        real = [
            str(row.get("learner_answer_md") or "").strip()
            for row in repository.real_attempt_trace_rows()
            if str(row.get("learner_answer_md") or "").strip()
        ]
    else:
        real = [str(trace).strip() for trace in real_traces if str(trace).strip()]

    score: float | None
    correct = 0
    total = 0
    if len(persona) < MIN_TRACES_PER_ARM or len(real) < MIN_TRACES_PER_ARM:
        verdict = "insufficient_data"
        score = None
        note = (
            f"need at least {MIN_TRACES_PER_ARM} traces per arm; "
            f"have {len(persona)} persona and {len(real)} real"
        )
    else:
        score, correct, total = _blind_leave_pair_out(
            [text_features(trace) for trace in persona],
            [text_features(trace) for trace in real],
        )
        verdict = (
            "separable" if score >= separation_threshold else "indistinguishable"
        )
        note = (
            f"blind matcher separability {score:.3f} "
            f"{'>=' if verdict == 'separable' else '<'} "
            f"{separation_threshold:.3f}"
        )

    run_id = None
    if persist:
        run_id = repository.insert_persona_realism_run(
            {
                "matcher_version": PERSONA_REALISM_MATCHER_VERSION,
                "corpus_hash": _corpus_hash(persona, real),
                "persona_corpus_hash": trace_corpus_hash(persona),
                "real_corpus_hash": trace_corpus_hash(real),
                "persona_source": persona_source,
                "generator_provider": generator_provider,
                "generator_model": generator_model,
                "generator_family": generator_family,
                "persona_count": len(persona),
                "real_count": len(real),
                "folds": total,
                "matcher_correct": correct,
                "matcher_total": total,
                "balanced_accuracy": score,
                "separation_threshold": separation_threshold,
                "verdict": verdict,
                "feature_manifest": {
                    "features": list(FEATURE_NAMES),
                    "classifier": "standardized_nearest_centroid_leave_pair_out",
                    "labels_visible_to_matcher": True,
                    "outcome_metadata_visible": False,
                    "trace_text_persisted": False,
                },
            },
            clock=clock,
        )
    return PersonaRealismReport(
        run_id=run_id,
        verdict=verdict,
        balanced_accuracy=score,
        separation_threshold=separation_threshold,
        persona_count=len(persona),
        real_count=len(real),
        matcher_correct=correct,
        matcher_total=total,
        generator_family=generator_family,
        note=note,
    )


def latest_realism_license(
    repository: Repository,
    *,
    generator_family: str | None = None,
    persona_source: str | None = None,
    persona_corpus_hash: str | None = None,
) -> dict[str, Any] | None:
    """Latest matching B2 run; callers must inspect ``verdict``."""

    return repository.latest_persona_realism_run(
        generator_family=generator_family,
        persona_source=persona_source,
        persona_corpus_hash=persona_corpus_hash,
    )
