"""Offline PF-a report assembly, JSON and markdown."""
from __future__ import annotations

import json
from pathlib import Path

from learnloop.evaluation.harness import digest, replay
from learnloop.evaluation.predictors import FamilyMemory, IdeaHier
from learnloop.substrate.family_memory_rows import load_rows
from learnloop.params.fitted_params import fitted_fsrs_provenance, resolve_fsrs_weights
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS


def evaluate(vault, repository, *, legacy_fallback: str = "exclude") -> dict:
    rows, source = load_rows(vault, repository, legacy_fallback=legacy_fallback)
    weight_sets = {"current_fit": resolve_fsrs_weights(repository),
                   "defaults": FSRS6_DEFAULT_WEIGHTS}
    arms = [FamilyMemory(key, weights, weight_label=label, distance_discount=discount)
            for label, weights in weight_sets.items()
            for key in ("item", "family", "lo") for discount in (False, True)]
    cfg = vault.config.mastery
    arms.append(IdeaHier(base_observation_variance=cfg.base_observation_variance,
                         sigma2_drift=cfg.sigma2_drift, p_max=cfg.p_max))
    return replay(rows, arms, manifest={
        "algorithm": vault.config.algorithms.algorithm_version,
        "config_hash": digest(vault.config.model_dump(mode="json")),
        "weights": {key: {"values": list(weights), "hash": digest(weights)}
                    for key, weights in weight_sets.items()},
        "current_fit_id": fitted_fsrs_provenance(repository),
        "current_fit_is_defaults": fitted_fsrs_provenance(repository) is None,
        "source": source,
    })


def write_report(report: dict, output: Path) -> tuple[Path, Path]:
    output.mkdir(parents=True, exist_ok=True)
    # Content-addressed reports are reproducible and do not overwrite a
    # different run merely because it was launched on the same calendar day.
    stem = "pf-a-" + digest(report)[:16]
    json_path, md_path = output / (stem + ".json"), output / (stem + ".md")
    json_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    lines = ["# PF-a offline replay", "", "**Research only; not an activation decision.**", "",
             "| Arm | N | Log loss | Brier |", "|---|---:|---:|---:|"]
    for arm, splits in report["arms"].items():
        overall = splits["overall"]
        lines.append(f"| {arm} | {overall['count']} | {overall['log_loss']} | {overall['brier']} |")
    lines += ["", "## Counts", "", "```json", json.dumps(report["counts"], sort_keys=True, indent=2),
              "```", "", "## Limitations", ""]
    lines += ["- " + value for value in report["limitations"]]
    lines += ["", "Full splits, uncertainty intervals, reliability bins and version manifest are in the companion JSON.", ""]
    md_path.write_text("\n".join(lines))
    return json_path, md_path
