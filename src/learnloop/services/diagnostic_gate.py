"""Sim discrimination gate for generated diagnostics.

Implements spec_misconception_diagnostics.md §6: before a ``diagnostic_authoring``
proposal is queued, simulate a planted student (who answers with the belief's
misconception-consistent answer) and a clean student (who answers correctly),
grade each in memory, and turn the fire-counts into Beta posteriors over the
item's sensitivity / specificity against the belief. The posteriors are written
to ``item_misconception_discrimination`` (source ``sim``) and gate acceptance.

CRITICAL: the gate never writes attempts, error_events, or mastery — it grades
in memory only, so running it cannot pollute the learner's state. The only
persistence side effect is the discrimination row.

Deterministic grader semantics (the default, provider-free path): the keyed
fatal error fires iff the submitted answer equals the misconception-consistent
answer AND that answer differs categorically from the expected answer (compared
under case/whitespace/punctuation normalization). This is exactly the §5.2.2
"categorical contrast" property; its limits are documented on
``_keyed_fatal_fires`` below. The motivating paraphrase — whose planted student
answers correctly because ``misconception_consistent_answer == expected_answer``
— therefore never fires, so its sensitivity lower bound collapses to
``Beta(1, N+1)`` and it is rejected (the regression case for the whole spec).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import (
    ItemMisconceptionDiscrimination,
    MisconceptionRecord,
    Repository,
)
from learnloop.numeric import beta_quantile
from learnloop.vault.models import LoadedVault, PracticeItem, discriminates

_LOGGER = logging.getLogger(__name__)

_PUNCT_RE = re.compile(r"[^\w\s]")
_WS_RE = re.compile(r"\s+")


def _normalize(text: str | None) -> str:
    if not text:
        return ""
    lowered = _PUNCT_RE.sub(" ", str(text).lower())
    return _WS_RE.sub(" ", lowered).strip()


#: Public alias. §3.0's shared authoring gate (``services/persona_gate``) and the
#: D2 mint gate (``services/facet_mint_gate``) decide "categorically distinct"
#: with THIS normalizer, not a second one, so the three uses of the one harness
#: (Meas §3.0/D2: "one mechanism, three uses") cannot drift apart on what counts
#: as the same answer.
normalize_answer = _normalize


@dataclass(frozen=True)
class GateResult:
    """Beta posteriors + acceptance verdict from a discrimination gate run (§6)."""

    practice_item_id: str
    misconception_id: str
    sens_alpha: float
    sens_beta: float
    spec_alpha: float
    spec_beta: float
    n_planted_trials: int
    n_clean_trials: int
    accepted: bool
    reasons: list[str] = field(default_factory=list)
    # Whether the opt-in codex answers-under-belief pass contributed trials to
    # these posteriors (spec §6, sim_gate_llm_trials). False on the pure
    # deterministic path and when the LLM call was skipped or fell back.
    llm_trials_ran: bool = False

    def sensitivity_lb(self, q: float = 0.25) -> float:
        return beta_quantile(q, self.sens_alpha, self.sens_beta)

    def specificity_lb(self, q: float = 0.25) -> float:
        return beta_quantile(q, self.spec_alpha, self.spec_beta)

    def as_dict(self) -> dict[str, Any]:
        return {
            "practice_item_id": self.practice_item_id,
            "misconception_id": self.misconception_id,
            "sensitivity_lb": self.sensitivity_lb(),
            "specificity_lb": self.specificity_lb(),
            "n_planted_trials": self.n_planted_trials,
            "n_clean_trials": self.n_clean_trials,
            "accepted": self.accepted,
            "llm_trials_ran": self.llm_trials_ran,
            "reasons": list(self.reasons),
        }


def _payload_field(item: PracticeItem | dict[str, Any], key: str) -> Any:
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)


def _item_id(item: PracticeItem | dict[str, Any]) -> str | None:
    value = _payload_field(item, "id")
    return str(value) if value else None


def _expected_answer_text(item: PracticeItem | dict[str, Any]) -> str:
    expected = _payload_field(item, "expected_answer")
    if isinstance(expected, dict):
        # Structured answers: fall back to a stable serialization.
        return " ".join(str(v) for v in expected.values())
    return str(expected or "")


def _keyed_fatal_error_ids(item: PracticeItem | dict[str, Any], misconception_id: str) -> list[str]:
    """Fatal-error ids on the item's rubric keyed to ``misconception_id`` (§5.2.3)."""

    rubric = _payload_field(item, "grading_rubric")
    fatal_errors: list[Any]
    if isinstance(rubric, dict):
        fatal_errors = rubric.get("fatal_errors") or []
    elif rubric is not None:
        fatal_errors = list(getattr(rubric, "fatal_errors", []) or [])
    else:
        fatal_errors = []
    keyed: list[str] = []
    for fatal_error in fatal_errors:
        if isinstance(fatal_error, dict):
            mc_id = fatal_error.get("misconception_id")
            fe_id = fatal_error.get("id")
        else:
            mc_id = getattr(fatal_error, "misconception_id", None)
            fe_id = getattr(fatal_error, "id", None)
        if mc_id == misconception_id and fe_id:
            keyed.append(str(fe_id))
    return keyed


def _keyed_fatal_descriptions(
    item: PracticeItem | dict[str, Any], misconception_id: str
) -> list[dict[str, str]]:
    """``{id, description}`` for each fatal error keyed to ``misconception_id``."""

    rubric = _payload_field(item, "grading_rubric")
    if isinstance(rubric, dict):
        fatal_errors = rubric.get("fatal_errors") or []
    elif rubric is not None:
        fatal_errors = list(getattr(rubric, "fatal_errors", []) or [])
    else:
        fatal_errors = []
    out: list[dict[str, str]] = []
    for fatal_error in fatal_errors:
        if isinstance(fatal_error, dict):
            mc_id = fatal_error.get("misconception_id")
            fe_id = fatal_error.get("id")
            desc = fatal_error.get("description")
        else:
            mc_id = getattr(fatal_error, "misconception_id", None)
            fe_id = getattr(fatal_error, "id", None)
            desc = getattr(fatal_error, "description", None)
        if mc_id == misconception_id and fe_id:
            out.append({"id": str(fe_id), "description": str(desc or "")})
    return out


def _diagnostic_trials_context(
    item: PracticeItem | dict[str, Any],
    misconception: MisconceptionRecord,
    *,
    expected: str,
    misconception_consistent: str | None,
    n_trials: int,
) -> dict[str, Any]:
    """Token-frugal context for the codex answers-under-belief call (spec §6)."""

    return {
        "n_trials": int(n_trials),
        "max_answer_words": 40,
        "item_prompt": str(_payload_field(item, "prompt") or ""),
        "expected_answer": expected,
        "misconception_statement": misconception.statement,
        "misconception_consistent_answer": str(misconception_consistent or ""),
        "keyed_fatal_errors": _keyed_fatal_descriptions(item, misconception.id),
    }


def _keyed_fatal_fires(
    answer: str,
    *,
    expected: str,
    misconception_consistent: str | None,
    has_keyed_fatal: bool,
) -> bool:
    """Whether the keyed fatal error fires on ``answer`` (deterministic grader).

    Fires iff the answer matches the misconception-consistent answer AND that
    answer is categorically distinct from the expected answer. Limits: it is a
    string-equality proxy for what an LLM grader attributes semantically, so it
    cannot catch a belief-consistent answer phrased differently from the recorded
    signature, and it treats any exact match to the expected answer as clean. It
    is deliberately conservative — it under-fires rather than false-fires — which
    is the safe direction for a specificity-strict gate.
    """

    if not has_keyed_fatal or not misconception_consistent:
        return False
    normalized_answer = _normalize(answer)
    normalized_mc = _normalize(misconception_consistent)
    if not normalized_mc:
        return False
    return normalized_answer == normalized_mc and normalized_mc != _normalize(expected)


def run_discrimination_gate(
    vault: LoadedVault,
    repository: Repository,
    *,
    item: PracticeItem | dict[str, Any],
    misconception: MisconceptionRecord,
    grading_client: Any = None,
    trials: int | None = None,
    clock: Clock | None = None,
) -> GateResult:
    """Estimate + persist an item's discrimination against ``misconception`` (§6).

    Simulates ``trials`` planted and ``trials`` clean answers, grades each in
    memory through :func:`_keyed_fatal_fires`, writes the Beta posteriors to
    ``item_misconception_discrimination`` (uniform Beta(1,1) prior + observed
    counts, source ``sim``), and accepts iff both lower bounds clear the config
    thresholds. ``grading_client`` is an optional hook to answer/grade under the
    belief with an LLM; the deterministic default is the canned answer, which is
    what the acceptance test relies on. No attempt/error_event rows are written.
    """

    config = vault.config.misconceptions
    n_trials = trials if trials is not None else config.sim_gate_trials
    item_id = _item_id(item)
    if item_id is None:
        raise ValueError("run_discrimination_gate requires an item with an id")

    expected = _expected_answer_text(item)
    # The planted student answers with the item's recorded belief-consistent
    # answer, falling back to the registry signature (spec §6).
    misconception_consistent = _payload_field(item, "misconception_consistent_answer") or misconception.signature
    keyed_fatal_ids = _keyed_fatal_error_ids(item, misconception.id)
    has_keyed_fatal = bool(keyed_fatal_ids)

    def _fire(answer: str) -> bool:
        if grading_client is not None:
            grade_fires = getattr(grading_client, "grade_diagnostic_fire", None)
            if callable(grade_fires):
                return bool(
                    grade_fires(
                        item=item,
                        misconception=misconception,
                        answer=answer,
                        expected=expected,
                        keyed_fatal_error_ids=keyed_fatal_ids,
                    )
                )
        return _keyed_fatal_fires(
            answer,
            expected=expected,
            misconception_consistent=misconception_consistent,
            has_keyed_fatal=has_keyed_fatal,
        )

    planted_fires = sum(1 for _ in range(n_trials) if _fire(str(misconception_consistent or "")))
    clean_fires = sum(1 for _ in range(n_trials) if _fire(expected))
    n_planted = n_trials
    n_clean = n_trials

    def _blocking(sens_a: float, sens_b: float, spec_a: float, spec_b: float) -> list[str]:
        blocking: list[str] = []
        if not has_keyed_fatal:
            blocking.append("no_keyed_fatal_error")
        if beta_quantile(0.25, sens_a, sens_b) < config.sim_gate_min_sensitivity_lb:
            blocking.append("sensitivity_lb_below_threshold")
        if beta_quantile(0.25, spec_a, spec_b) < config.sim_gate_min_specificity_lb:
            blocking.append("specificity_lb_below_threshold")
        return blocking

    def _posteriors(pf: int, cf: int, np_: int, nc: int) -> tuple[float, float, float, float]:
        # Sensitivity = P(fire | belief); specificity = P(no fire | clean).
        return (1.0 + pf, 1.0 + (np_ - pf), 1.0 + (nc - cf), 1.0 + cf)

    sens_alpha, sens_beta, spec_alpha, spec_beta = _posteriors(
        planted_fires, clean_fires, n_planted, n_clean
    )
    det_accepted = not _blocking(sens_alpha, sens_beta, spec_alpha, spec_beta)

    # spec §6: opt-in codex answers-under-belief pass. Short-circuit — only escalate
    # to the (token-costly) LLM call when the deterministic pass already accepted
    # and a provider that exposes run_diagnostic_trials is wired through. The
    # deterministic trials are real trials of the canned answers, so LLM fires are
    # ADDED to the Beta counts rather than replacing them.
    llm_trials = int(getattr(config, "sim_gate_llm_trials", 0) or 0)
    run_trials = getattr(grading_client, "run_diagnostic_trials", None) if grading_client else None
    notes: list[str] = []
    llm_trials_ran = False
    if llm_trials > 0 and callable(run_trials) and det_accepted:
        try:
            llm_result = run_trials(_diagnostic_trials_context(
                item,
                misconception,
                expected=expected,
                misconception_consistent=misconception_consistent,
                n_trials=llm_trials,
            ))
            planted_fires += sum(1 for t in llm_result.planted if getattr(t, "fires", False))
            clean_fires += sum(1 for t in llm_result.clean if getattr(t, "fires", False))
            n_planted += len(llm_result.planted)
            n_clean += len(llm_result.clean)
            sens_alpha, sens_beta, spec_alpha, spec_beta = _posteriors(
                planted_fires, clean_fires, n_planted, n_clean
            )
            llm_trials_ran = True
            notes.append("llm_trials_ran")
        except Exception as exc:  # provider outage must not block generation (spec §6)
            _LOGGER.warning(
                "run_diagnostic_trials failed for item %s / misconception %s: %s",
                item_id,
                misconception.id,
                exc,
            )
            notes.append("llm_trials_unavailable")

    row = ItemMisconceptionDiscrimination(
        practice_item_id=item_id,
        misconception_id=misconception.id,
        sensitivity_alpha=sens_alpha,
        sensitivity_beta=sens_beta,
        specificity_alpha=spec_alpha,
        specificity_beta=spec_beta,
        n_planted_trials=n_planted,
        n_clean_trials=n_clean,
        source="sim",
        updated_at=None,
    )
    repository.upsert_item_misconception_discrimination(row, clock=clock)

    blocking = _blocking(sens_alpha, sens_beta, spec_alpha, spec_beta)
    accepted = not blocking
    return GateResult(
        practice_item_id=item_id,
        misconception_id=misconception.id,
        sens_alpha=sens_alpha,
        sens_beta=sens_beta,
        spec_alpha=spec_alpha,
        spec_beta=spec_beta,
        n_planted_trials=n_planted,
        n_clean_trials=n_clean,
        accepted=accepted,
        reasons=blocking + notes,
        llm_trials_ran=llm_trials_ran,
    )


# Reason tags used by :func:`backfill_discrimination_rows` to classify a pair
# that was NOT (re)run: an already-present row respected by default, or a keyed
# misconception with no registry record. The CLI reads them for its summary.
BACKFILL_SKIPPED_EXISTING = "skipped_existing_row"
BACKFILL_SKIPPED_UNREGISTERED = "skipped_unregistered_misconception"


def _existing_row_gate_result(
    config: Any, row: ItemMisconceptionDiscrimination
) -> GateResult:
    """A read-only GateResult mirroring an existing discrimination row's verdict."""

    sens_lb = beta_quantile(0.25, row.sensitivity_alpha, row.sensitivity_beta)
    spec_lb = beta_quantile(0.25, row.specificity_alpha, row.specificity_beta)
    accepted = (
        sens_lb >= config.sim_gate_min_sensitivity_lb
        and spec_lb >= config.sim_gate_min_specificity_lb
    )
    return GateResult(
        practice_item_id=row.practice_item_id,
        misconception_id=row.misconception_id,
        sens_alpha=row.sensitivity_alpha,
        sens_beta=row.sensitivity_beta,
        spec_alpha=row.specificity_alpha,
        spec_beta=row.specificity_beta,
        n_planted_trials=row.n_planted_trials,
        n_clean_trials=row.n_clean_trials,
        accepted=accepted,
        reasons=[BACKFILL_SKIPPED_EXISTING],
    )


def backfill_discrimination_rows(
    vault: LoadedVault,
    repository: Repository,
    *,
    force: bool = False,
    clock: Clock | None = None,
) -> list[GateResult]:
    """Seed measured discrimination rows for every keyed (item, misconception) pair.

    Iterates the loaded vault's practice items, resolves each item's rubric, and
    uses :func:`discriminates` to find ``misconception_id`` links on the item's
    fatal errors. For each pair whose misconception is registered and that has no
    ``item_misconception_discrimination`` row yet, runs the deterministic sim gate
    (no ``grading_client``) — which persists the Beta posteriors — so downstream
    consumers stop falling back to the uncalibrated bridge default.

    Existing rows are respected by default (never clobbered — in particular
    ``source='sim'`` / observed rows survive); ``force=True`` re-runs every pair.
    Pairs whose misconception is not in the registry are skipped without error.

    The returned list carries one :class:`GateResult` per discovered pair, tagged
    via ``reasons`` so callers can classify them: a freshly measured row (ran
    pairs), :data:`BACKFILL_SKIPPED_EXISTING` (respected existing row), or
    :data:`BACKFILL_SKIPPED_UNREGISTERED` (no registry record).
    """

    config = vault.config.misconceptions
    results: list[GateResult] = []
    for item_id in sorted(vault.practice_items):
        item = vault.practice_items[item_id]
        rubric = vault.rubric_for_item(item)
        mapping = discriminates(item, rubric)
        for mc_id in sorted(mapping):
            record = repository.misconception(mc_id)
            if record is None:
                _LOGGER.info(
                    "backfill skip: misconception %s (item %s) is not registered",
                    mc_id,
                    item_id,
                )
                results.append(
                    GateResult(
                        practice_item_id=item_id,
                        misconception_id=mc_id,
                        sens_alpha=1.0,
                        sens_beta=1.0,
                        spec_alpha=1.0,
                        spec_beta=1.0,
                        n_planted_trials=0,
                        n_clean_trials=0,
                        accepted=False,
                        reasons=[BACKFILL_SKIPPED_UNREGISTERED],
                    )
                )
                continue
            if not force:
                existing = repository.discrimination_row(item_id, mc_id)
                if existing is not None:
                    results.append(_existing_row_gate_result(config, existing))
                    continue
            # Pass the resolved rubric onto the payload so the gate sees the same
            # keyed fatal errors discriminates() found (items may inherit a
            # default rubric that is not on item.grading_rubric).
            payload = item.model_dump()
            payload["grading_rubric"] = rubric.model_dump() if rubric is not None else None
            results.append(
                run_discrimination_gate(
                    vault,
                    repository,
                    item=payload,
                    misconception=record,
                    clock=clock,
                )
            )
    return results
