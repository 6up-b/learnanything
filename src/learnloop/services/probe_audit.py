"""Probe pilot audit and retirement telemetry (spec_probe_eig_redesign.md §13).

Checkpoint 4: predicted-versus-realized EIG, negative realized information,
time calibration, cross-surface replication, downstream outcomes, regrade
agreement / grading confusion per family and grader version, and a replay
determinism check for the fixture-vault pilot. Checkpoint 5: the shadow-mode
selection-policy comparison report.

All aggregates keep synthetic-gate and real-learner evidence strictly separate
(§9.6) and report wide uncertainty at single-learner sample sizes (§9.7):
every number here is learner-specific pooling, never psychometric calibration.
"""

from __future__ import annotations

from math import log
from typing import Any, Mapping

from learnloop.clock import Clock, parse_utc
from learnloop.db.repositories import ProbeEpisodeRecord, Repository
from learnloop.services.probe_episodes import episode_hypothesis_set, episode_posterior
from learnloop.services.probe_families import CompiledInstrument, classify_outcome
from learnloop.vault.models import LoadedVault


def _entropy(distribution: Mapping[str, float]) -> float:
    return -sum(p * log(p) for p in distribution.values() if p > 0)


def _round(value: float | None, digits: int = 4) -> float | None:
    return None if value is None else round(float(value), digits)


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _observation_rows(repository: Repository) -> list[dict[str, Any]]:
    """Every presentation-backed observation with its episode context."""

    rows: list[dict[str, Any]] = []
    for episode in repository.list_probe_episodes():
        for row in repository.probe_observations_for_episode(episode.id):
            row["episode"] = episode
            rows.append(row)
    return rows


def _family_key(row: Mapping[str, Any]) -> str:
    family = row.get("probe_family_template_id") or "unknown"
    version = row.get("probe_family_template_version")
    return f"{family}@v{version}" if version is not None else str(family)


# --- Predicted vs realized EIG (§13.2, Checkpoint 4.3) ------------------------------


def eig_calibration_report(repository: Repository) -> dict[str, Any]:
    """Expected vs realized information per family version.

    ``realized_information_gain`` is signed; the negative-information rate is
    the share of qualifying observations whose posterior entropy increased —
    a §9.7 retirement telemetry signal that an observation model is
    misspecified. Expected-vs-realized gaps here are audit telemetry, not a
    claim of population calibration.
    """

    per_family: dict[str, dict[str, Any]] = {}
    for row in _observation_rows(repository):
        observation = row["observation"]
        if not observation.eligible_for_completion:
            continue
        expected = row.get("expected_information_gain")
        if expected is None:
            continue
        bucket = per_family.setdefault(
            _family_key(row),
            {"expected": [], "realized": [], "negative": 0},
        )
        realized = float(observation.realized_information_gain)
        bucket["expected"].append(float(expected))
        bucket["realized"].append(realized)
        if realized < 0:
            bucket["negative"] += 1

    families: dict[str, dict[str, Any]] = {}
    all_expected: list[float] = []
    all_realized: list[float] = []
    total_negative = 0
    for key, bucket in sorted(per_family.items()):
        expected = bucket["expected"]
        realized = bucket["realized"]
        all_expected.extend(expected)
        all_realized.extend(realized)
        total_negative += bucket["negative"]
        gaps = [r - e for r, e in zip(realized, expected)]
        families[key] = {
            "observations": len(realized),
            "mean_expected_eig": _round(_mean(expected)),
            "mean_realized_information": _round(_mean(realized)),
            "mean_realized_minus_expected": _round(_mean(gaps)),
            "negative_information_count": bucket["negative"],
            "negative_information_rate": _round(bucket["negative"] / len(realized)),
        }
    total = len(all_realized)
    return {
        "observations": total,
        "mean_expected_eig": _round(_mean(all_expected)),
        "mean_realized_information": _round(_mean(all_realized)),
        "mean_realized_minus_expected": _round(
            _mean([r - e for r, e in zip(all_realized, all_expected)])
        ),
        "negative_information_count": total_negative,
        "negative_information_rate": _round(total_negative / total) if total else None,
        "by_family": families,
    }


# --- Time calibration (§13.2) --------------------------------------------------------


def time_calibration_report(repository: Repository) -> dict[str, Any]:
    """Expected instrument seconds vs observed served→submitted seconds."""

    per_family: dict[str, dict[str, list[float]]] = {}
    for row in _observation_rows(repository):
        served = parse_utc(row.get("served_at"))
        submitted = parse_utc(row.get("submitted_at"))
        if served is None or submitted is None or submitted < served:
            continue
        components = row.get("selection_components") or {}
        snapshot = row.get("instrument_card_snapshot") or {}
        expected = components.get("expected_seconds") or snapshot.get("expected_seconds")
        if expected is None:
            continue
        actual = (submitted - served).total_seconds()
        bucket = per_family.setdefault(_family_key(row), {"expected": [], "actual": []})
        bucket["expected"].append(float(expected))
        bucket["actual"].append(actual)

    families: dict[str, dict[str, Any]] = {}
    all_errors: list[float] = []
    count = 0
    for key, bucket in sorted(per_family.items()):
        errors = [a - e for a, e in zip(bucket["actual"], bucket["expected"])]
        all_errors.extend(errors)
        count += len(errors)
        families[key] = {
            "observations": len(errors),
            "mean_expected_seconds": _round(_mean(bucket["expected"]), 2),
            "mean_actual_seconds": _round(_mean(bucket["actual"]), 2),
            "mean_error_seconds": _round(_mean(errors), 2),
            "mean_absolute_error_seconds": _round(_mean([abs(e) for e in errors]), 2),
        }
    return {
        "observations": count,
        "mean_error_seconds": _round(_mean(all_errors), 2),
        "mean_absolute_error_seconds": _round(_mean([abs(e) for e in all_errors]), 2),
        "by_family": families,
    }


# --- Cross-surface replication (§13.2) ------------------------------------------------


def cross_surface_replication_report(vault: LoadedVault, repository: Repository) -> dict[str, Any]:
    """Whether early diagnoses replicate on later observations from a
    different surface family within the same episode."""

    episodes_with_pairs = 0
    replicated = 0
    details: list[dict[str, Any]] = []
    for episode in repository.list_probe_episodes():
        rows = [
            row
            for row in repository.probe_observations_for_episode(episode.id)
            if row["observation"].eligible_for_completion
        ]
        if len(rows) < 2:
            continue

        def surface(row: Mapping[str, Any]) -> str:
            item = vault.practice_items.get(str(row["practice_item_id"]))
            return (item.surface_family if item is not None else None) or str(row["practice_item_id"])

        first, last = rows[0], rows[-1]
        if surface(first) == surface(last):
            continue
        episodes_with_pairs += 1

        def top(posterior: Mapping[str, float]) -> str | None:
            return max(posterior, key=lambda label: posterior[label]) if posterior else None

        first_top = top(first["observation"].posterior_after)
        last_top = top(last["observation"].posterior_after)
        match = first_top is not None and first_top == last_top
        if match:
            replicated += 1
        details.append(
            {
                "episode_id": episode.id,
                "learning_object_id": episode.learning_object_id,
                "first_top": first_top,
                "last_top": last_top,
                "replicated": match,
            }
        )
    return {
        "episodes_with_cross_surface_pairs": episodes_with_pairs,
        "replicated": replicated,
        "replication_rate": _round(replicated / episodes_with_pairs) if episodes_with_pairs else None,
        "episodes": details,
    }


# --- Downstream outcomes (§13.2, proxy) ------------------------------------------------


def downstream_outcome_report(repository: Repository) -> dict[str, Any]:
    """Post-episode success proxy: attempt success on the LO before vs after
    completion. A retention/transfer *proxy*, not a causal estimate — there is
    no counterfactual at n = 1."""

    episodes: list[dict[str, Any]] = []
    for episode in repository.list_probe_episodes(statuses=("complete",)):
        if episode.completed_at is None:
            continue
        before: list[bool] = []
        after: list[bool] = []
        for attempt in repository.list_attempts_by_learning_object(episode.learning_object_id):
            created_at = attempt.get("created_at")
            if not created_at:
                continue
            if attempt.get("attempt_type") == "diagnostic_probe":
                continue
            succeeded = not (
                attempt.get("attempt_type") == "dont_know"
                or float(attempt.get("correctness") or 0.0) <= 0.40
                or bool(attempt.get("error_type"))
            )
            (after if created_at > episode.completed_at else before).append(succeeded)
        episodes.append(
            {
                "episode_id": episode.id,
                "learning_object_id": episode.learning_object_id,
                "completion_reason": episode.completion_reason,
                "attempts_before": len(before),
                "attempts_after": len(after),
                "success_rate_before": _round(_mean([1.0 if s else 0.0 for s in before])),
                "success_rate_after": _round(_mean([1.0 if s else 0.0 for s in after])),
            }
        )
    measurable = [
        e for e in episodes if e["success_rate_before"] is not None and e["success_rate_after"] is not None
    ]
    return {
        "completed_episodes": len(episodes),
        "episodes_with_before_and_after": len(measurable),
        "mean_success_delta": _round(
            _mean([e["success_rate_after"] - e["success_rate_before"] for e in measurable])
        ),
        "episodes": episodes,
    }


# --- Replay determinism (Checkpoint 4.1) -----------------------------------------------


def replay_determinism_report(vault: LoadedVault, repository: Repository) -> dict[str, Any]:
    """Pilot integrity check: replay is deterministic and stored observation
    rows are internally consistent (entropies match their posterior JSON, the
    realized gain matches the entropy delta)."""

    checked = 0
    failures: list[dict[str, Any]] = []
    for episode in repository.list_probe_episodes():
        hypothesis_set = episode_hypothesis_set(repository, episode)
        if hypothesis_set is None:
            continue
        first = episode_posterior(vault, repository, episode, hypothesis_set=hypothesis_set)
        second = episode_posterior(vault, repository, episode, hypothesis_set=hypothesis_set)
        checked += 1
        if first is not None and second is not None:
            drift = max(
                abs(first.posterior.get(label, 0.0) - second.posterior.get(label, 0.0))
                for label in set(first.posterior) | set(second.posterior)
            ) if (first.posterior or second.posterior) else 0.0
            if drift > 1e-9:
                failures.append({"episode_id": episode.id, "kind": "replay_nondeterministic", "drift": drift})
        for row in repository.probe_observations_for_episode(episode.id):
            observation = row["observation"]
            for kind, stored, recomputed in (
                ("entropy_before", observation.entropy_before, _entropy(observation.posterior_before)),
                ("entropy_after", observation.entropy_after, _entropy(observation.posterior_after)),
                (
                    "realized_information_gain",
                    observation.realized_information_gain,
                    observation.entropy_before - observation.entropy_after,
                ),
            ):
                if abs(float(stored) - float(recomputed)) > 1e-6:
                    failures.append(
                        {
                            "episode_id": episode.id,
                            "attempt_id": observation.attempt_id,
                            "kind": f"{kind}_mismatch",
                            "stored": _round(float(stored), 6),
                            "recomputed": _round(float(recomputed), 6),
                        }
                    )
    return {"episodes_checked": checked, "deterministic": not failures, "failures": failures}


# --- Regrade agreement and grading confusion (§7.6, Checkpoint 4.4) ---------------------


def record_probe_regrade_check(
    repository: Repository,
    *,
    attempt_id: str,
    regrade_rubric_score: int | None,
    regrade_error_types: list[str] | None = None,
    attempt_type: str = "diagnostic_probe",
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Classify a regraded response through the observation's own persisted
    card snapshot and record the (original, regrade) outcome pair.

    Returns the recorded pair, or None when the attempt has no probe
    observation or its presentation snapshot is missing.
    """

    observation = repository.probe_observation_for_attempt(attempt_id)
    if observation is None:
        return None
    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None or not attempt.get("probe_presentation_id"):
        return None
    presentation = repository.probe_presentation(str(attempt["probe_presentation_id"]))
    if presentation is None or presentation.instrument_card_snapshot is None:
        return None
    instrument = CompiledInstrument.from_snapshot(presentation.instrument_card_snapshot)
    original_outcome = str((observation.grader_channel or {}).get("observed_outcome") or "")
    if not original_outcome:
        return None
    regrade_outcome = classify_outcome(
        instrument,
        rubric_score=regrade_rubric_score,
        attempt_type=attempt_type,
        fired_error_types=regrade_error_types or [],
    )
    repository.insert_probe_regrade_check(
        attempt_id=attempt_id,
        probe_family_template_id=instrument.family_template_id or "unknown",
        probe_family_template_version=instrument.family_template_version or 1,
        grader_version=instrument.grader_policy,
        original_outcome=original_outcome,
        regrade_outcome=regrade_outcome,
        clock=clock,
    )
    return {"original_outcome": original_outcome, "regrade_outcome": regrade_outcome}


def run_probe_regrade_checks(
    vault: LoadedVault,
    repository: Repository,
    client: Any,
    *,
    limit: int = 10,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Re-grade a sample of probe observations and record agreement (§7.6).

    Non-destructive: unlike the deferred self-grade regrade path, this NEVER
    supersedes evidence or replays state — it only re-runs the grader on the
    stored response, classifies the outcome through the observation's persisted
    card snapshot, and records the (original, regrade) pair. Attempts that
    already have a check are skipped so a fixed sample budget spreads coverage.
    """

    from learnloop.services.grading import (
        build_grading_context,
        validate_codex_grading_proposal,
    )

    already_checked = {check["attempt_id"] for check in repository.probe_regrade_checks()}
    attempted = 0
    recorded = 0
    failures = 0
    for episode in repository.list_probe_episodes():
        if attempted >= limit:
            break
        for row in repository.probe_observations_for_episode(episode.id):
            if attempted >= limit:
                break
            attempt_id = row["observation"].attempt_id
            if attempt_id in already_checked:
                continue
            attempt = repository.fetch_practice_attempt(attempt_id)
            if attempt is None:
                continue
            item = vault.practice_items.get(str(attempt["practice_item_id"]))
            if item is None:
                continue
            attempted += 1
            try:
                context = build_grading_context(
                    vault,
                    item,
                    attempt_id=attempt_id,
                    learner_answer_md=attempt.get("learner_answer_md") or "",
                )
                proposal = client.run_grading_proposal(context)
                validated = validate_codex_grading_proposal(
                    proposal, attempt_id=attempt_id, item=item, vault=vault
                )
            except Exception:
                failures += 1
                continue
            result = record_probe_regrade_check(
                repository,
                attempt_id=attempt_id,
                regrade_rubric_score=validated.rubric_score,
                regrade_error_types=[
                    attribution.error_type for attribution in validated.error_attributions
                ],
                attempt_type=str(attempt.get("attempt_type") or "diagnostic_probe"),
                clock=clock,
            )
            if result is not None:
                recorded += 1
                already_checked.add(attempt_id)
    return {"attempted": attempted, "recorded": recorded, "failed": failures}


def grading_confusion_report(repository: Repository) -> dict[str, Any]:
    """Regrade agreement and the (original, regrade) confusion matrix per
    family version and grader version (§7.6)."""

    per_scope: dict[str, dict[str, Any]] = {}
    for check in repository.probe_regrade_checks():
        key = (
            f"{check['probe_family_template_id']}@v{check['probe_family_template_version']}"
            f"|{check.get('grader_version') or 'unversioned'}"
        )
        scope = per_scope.setdefault(
            key,
            {
                "family": check["probe_family_template_id"],
                "version": check["probe_family_template_version"],
                "grader_version": check.get("grader_version"),
                "checks": 0,
                "agreements": 0,
                "confusion": {},
            },
        )
        scope["checks"] += 1
        scope["agreements"] += int(check["agreement"])
        row = scope["confusion"].setdefault(check["original_outcome"], {})
        row[check["regrade_outcome"]] = row.get(check["regrade_outcome"], 0) + 1
    for scope in per_scope.values():
        scope["agreement_rate"] = _round(scope["agreements"] / scope["checks"]) if scope["checks"] else None
    return {"scopes": dict(sorted(per_scope.items()))}


# --- Evidence-source separation (§9.6, Checkpoint 4.5) -----------------------------------


def calibration_evidence_report(repository: Repository) -> dict[str, Any]:
    """Family calibration rows grouped by evidence source. Synthetic gate
    statistics and real learner evidence are reported side by side but never
    merged; the pilot fails if any scope mixes them."""

    with repository.connection() as connection:
        rows = connection.execute(
            """
            SELECT probe_family_template_id, probe_family_template_version,
                   COALESCE(grader_version, '') AS grader_version,
                   evidence_source, sample_size, effective_sample_size
            FROM probe_family_calibrations
            ORDER BY probe_family_template_id, probe_family_template_version, evidence_source
            """
        ).fetchall()
    families: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = f"{row['probe_family_template_id']}@v{row['probe_family_template_version']}"
        entry = families.setdefault(key, {"sources": {}})
        entry["sources"][row["evidence_source"]] = {
            "sample_size": row["sample_size"],
            "effective_sample_size": _round(row["effective_sample_size"], 2),
            "grader_version": row["grader_version"] or None,
        }
    return {"families": families}


# --- Shadow-mode policy comparison (§13.3, Checkpoint 5.1) --------------------------------


def shadow_policy_report(repository: Repository) -> dict[str, Any]:
    """Compare the executed selection against logged shadow rankings.

    Log-only (§13.3): a policy is promoted from held-out predictive gains,
    never from this report alone. For each policy the report shows how often
    its top-ranked candidate matched the executed pick, and the realized
    information observed when it agreed vs disagreed.
    """

    policies: dict[str, dict[str, Any]] = {}
    observations = 0
    for row in _observation_rows(repository):
        components = row.get("selection_components") or {}
        shadow = components.get("shadow_rankings")
        if not isinstance(shadow, Mapping):
            continue
        executed_item = str(row["practice_item_id"])
        realized = float(row["observation"].realized_information_gain)
        observations += 1
        for policy, ranking in shadow.items():
            if not isinstance(ranking, list) or not ranking:
                continue
            top = str(ranking[0])
            bucket = policies.setdefault(
                str(policy),
                {"observations": 0, "agreements": 0, "realized_when_agreed": [], "realized_when_differed": []},
            )
            bucket["observations"] += 1
            if top == executed_item:
                bucket["agreements"] += 1
                bucket["realized_when_agreed"].append(realized)
            else:
                bucket["realized_when_differed"].append(realized)
    report: dict[str, Any] = {}
    for policy, bucket in sorted(policies.items()):
        report[policy] = {
            "observations": bucket["observations"],
            "agreement_rate": _round(bucket["agreements"] / bucket["observations"])
            if bucket["observations"]
            else None,
            "mean_realized_when_agreed": _round(_mean(bucket["realized_when_agreed"])),
            "mean_realized_when_differed": _round(_mean(bucket["realized_when_differed"])),
        }
    return {"observations_with_shadow": observations, "policies": report}


def planner_shadow_report(repository: Repository) -> dict[str, Any]:
    """§5.9 routine-planner shadow comparison (§13.3, log-only).

    Over presentations that logged a ``shadow_planner`` component: how often
    the served episode was already the plain-rate top pick, how often the
    disagreement-boosted ordering agreed, and the realized information split
    by whether the boosted planner would have served a different episode.
    """

    observations = 0
    plain_top = 0
    boosted_top = 0
    realized_when_boosted_agreed: list[float] = []
    realized_when_boosted_differed: list[float] = []
    for row in _observation_rows(repository):
        components = row.get("selection_components") or {}
        planner = components.get("shadow_planner")
        if not isinstance(planner, Mapping):
            continue
        observations += 1
        realized = float(row["observation"].realized_information_gain)
        if int(planner.get("episode_rank_plain") or 0) == 1:
            plain_top += 1
        if int(planner.get("episode_rank_boosted") or 0) == 1:
            boosted_top += 1
            realized_when_boosted_agreed.append(realized)
        else:
            realized_when_boosted_differed.append(realized)
    return {
        "observations_with_planner_shadow": observations,
        "plain_top_rate": _round(plain_top / observations) if observations else None,
        "boosted_agreement_rate": _round(boosted_top / observations) if observations else None,
        "mean_realized_when_boosted_agreed": _round(_mean(realized_when_boosted_agreed)),
        "mean_realized_when_boosted_differed": _round(_mean(realized_when_boosted_differed)),
    }


# --- Pilot bundle (Checkpoint 4.1) ---------------------------------------------------------


def pilot_report(vault: LoadedVault, repository: Repository) -> dict[str, Any]:
    """The full fixture-vault pilot audit (Checkpoint 4).

    Bundles EIG calibration, time calibration, cross-surface replication,
    downstream outcomes, regrade agreement, evidence-source separation, shadow
    policy comparison, and the replay determinism check.
    """

    return {
        "version": 1,
        "eig_calibration": eig_calibration_report(repository),
        "time_calibration": time_calibration_report(repository),
        "cross_surface_replication": cross_surface_replication_report(vault, repository),
        "downstream_outcomes": downstream_outcome_report(repository),
        "grading_confusion": grading_confusion_report(repository),
        "calibration_evidence": calibration_evidence_report(repository),
        "shadow_policies": shadow_policy_report(repository),
        "planner_shadow": planner_shadow_report(repository),
        "replay_determinism": replay_determinism_report(vault, repository),
    }
