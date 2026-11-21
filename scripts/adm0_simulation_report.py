"""Render aggregate ADM0 results captured by the registered pytest run.

Usage: python scripts/adm0_simulation_report.py results.xml report.md
No simulation is run here. Inputs are an explicit JUnit file and frozen protocol.
"""
from __future__ import annotations

import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HASH = "dbc4373bfce05bab88b0cb6fbc6b011b1963c20201b161dc4b7ab65642605dcd"
SEEDS = "Seeds `adm0-v1:0`–`adm0-v1:7`; 8 synthetic learners/seed/world (64/world)."


def number(value):
    if value is None:
        return "N/A"
    return f"{value:.3e}" if 0 < abs(value) < .0001 else f"{value:.4f}"


def table(lines, title, caption, columns, rows):
    lines.extend([f"## {title}", "", caption, "", "| " + " | ".join(columns) + " |",
                  "| " + " | ".join("---" for _ in columns) + " |"])
    lines.extend("| " + " | ".join(str(v) for v in row) + " |" for row in rows)
    lines.append("")


def introduction(timestamp):
    lines = ["# ADM0 simulation report", "",
        "Preregistration SHA-256: `" + HASH + "`.", "",
        "The protocol was written and hash-frozen on 2026-11-21 **before new simulation code, tests or runs**. "
        "The hash was recorded in this report before implementation. The sandbox cannot commit; the orchestrator "
        "commits the artifacts together. This establishes the session's order, not a separate earlier Git commit.", "",
        f"Completed registered-run JUnit timestamp: `{timestamp}`. Base: `3f42da228a`. "
        "Source: `tests/test_ad_memory_simulation.py::test_registered_experiment` (`arc_close`). "
        "All 384 synthetic trajectories / 18,432 presentations were included. No owner outcomes, owner vaults, "
        "configuration files, network or model calls were used. **No claim of learner benefit, including at n=1.**", "",
        "The simulation calls the real AD `Bank`, `View`, category kernel and FSRS review/recall functions. "
        "The sole production-file edit is a keyword-only residual-variance argument to `Bank.update`; omission "
        "executes the old residual calculation. No production caller supplies it. Nothing served, persisted, "
        "configured, tagged or migrated changes. Existing `ad_synthetic.py`, scenario seeds and fixtures remain untouched.", "",
        "## Findings", "",
        "1. **Decides something:** the joint same-item filter retains the analytically required ability variance floor; "
        "retaining cross-covariance is necessary for this interpretation.",
        "2. **Decides something:** extra warmth coefficients preserve the prior eta mean and add predictive variance "
        "immediately; success probability and band probability consequently change.",
        "3. **Decides something:** stable item and family coordinates, strict pre-serve features and once-per-surface "
        "gamma can be exercised through the existing numerical model without a served-model change.",
        "4. **Cannot be decided by simulation:** none of the registered support/ladder comparisons satisfies all "
        "selection conditions below; no production rho, LO value or warmth ladder is selected.",
        "5. **Cannot be decided by simulation:** per-learner family/item decomposition is weakly identified; repeated "
        "success alone does not identify transferable ability. Recovery and contraction are reported, not inferred from loss.",
        "6. **Cannot be decided by simulation:** prior widths are not established population values. Quarter/four-times "
        "variance and one-SD mean perturbations remain alternatives, even where one has lower synthetic loss.",
        "7. **Cannot be decided by simulation:** the planted effective-stability multiplier does not identify RE8's "
        "latent weights or the LP width support; no RE8 fitter is implemented here.",
        "8. **Decides something:** numerical cold replay, cached-input construction, candidate-grid work and synthetic "
        "Next have measured costs and explicit workloads; no covariance approximation is proposed.",
        "9. **Cannot be decided by simulation:** these numerical timings do not establish production Next latency, "
        "database replay cost, storage growth or owner-data prevalence.",
        "10. **Cannot be decided by simulation:** synthetic prediction/recovery says nothing by itself about learner "
        "benefit or the effects of a changed serving policy.", "",
        "## Design and limits", "",
        SEEDS + " Six worlds and all 48 scheduled events per learner. At synthetic origin 2026-01-01T00:00:00Z, "
        "block b starts at day 36b; offsets are 0, 1/24, 1/4, 1, 3, 7, 30, 31, 32, 33, 34, 35 days. "
        "Strict review-time < serve-time; labels close inclusively at 2026-06-01T00:00:00Z under "
        "`adm0_synthetic_categories_v1`. Every presentation is issued, answered and resolved; missing, unbound, "
        "censored, held, primed and pre-exposed counts are all zero. This experiment does not validate their production eligibility.", "",
        "Each trajectory has 20 items, 12 surface groups, 28 same-item repeats (including four singleton repeats), "
        "eight unseen siblings, four singleton first encounters, four initial anchors and four novel families after drilling. "
        "Assigned/natural-labelled delays each cover 24 events. The latter are scripted, not observational evidence. "
        "Views share truth and outcome uniforms. Subject filtering uses three distinct inherited split points; "
        "coupling/implication duplicates in the 36-point grid are numerically equivalent in this one-cell design "
        "(tested against the full grid). LO filtering has fixed rho candidates 0/.5/1, never a learned rho mixture.", "",
        "True effects are stable while the filter applies the spec's inherited drift. This deliberate mismatch can "
        "make intervals conservative and prevent contraction. No random-walk truth recovery is claimed. Memory uses "
        "past FSRS reviews; the slow-retention world alone reads planted S_eff=S*exp(.5). The truth uses its own "
        "pre-memory eta and each candidate freezes its own mean. The positive-easiness sign convention follows "
        "ADM §4.4; §4.2's contrary -1 wording remains a spec-owner correction.", "",
        "Rho is the initial variance split. Even at rho=0 or 1, an initially zero-variance effect receives "
        "the specified later drift; the endpoints do not impose a permanent zero effect.", "",
        "Scores are binary unassisted-success log loss and Brier; calibration is ten-bin absolute calibration "
        "error (ECE) and signed mean p-y. Coverage is a nominal 95% moment interval for planted latent eta, "
        "including unseen residuals, using **pre-update mixture weights**. It is not coverage of binary labels "
        "and is not an exact mixture quantile. Paired intervals use eight seed-level means with t(7), not attempts "
        "as independent samples. FSRS predicts recall (rating != AGAIN), and mastery predicts rubric correctness; "
        "their target mismatch to AD's category-2 success is retained and disclosed.", "",
        "## Execution ledger", "",
        "Tests were written first and initially failed collection because the new module did not exist. The fast "
        "test's initial per-filter comparison was corrected to compare matching grids. The first arc-close attempt "
        "failed during first-world score aggregation (NumPy boolean negation); labels were cast to floats, with a "
        "regression test. A subsequent complete run was superseded after a stronger novel-only compatibility "
        "test found that candidate drift preceded prediction instead of following View.observe's boundary. "
        "The candidate now predicts first, then applies cell/effect drift, measurement and learning. "
        "The final complete registered rerun supplies all tables; earlier numerical results are discarded. "
        "This necessary correctness rerun departs from the requested single successful execution, not from the "
        "statistical protocol. No seed, world, prior, "
        "selection criterion or frozen-protocol byte changed. JUnit's explicit `--junitxml` destination records "
        "the aggregate payload as `adm0_results`; this replaces the protocol's proposed environment-variable "
        "output mechanism because the supplied wrapper clears the environment. This is an output-only deviation.", ""]
    return lines


def interpretation(payload):
    results = payload["results"]
    balanced = results["balanced"]["subject"]
    reference = balanced["R3-H3"]
    old = balanced["predecessor"]["scores"]["same_item"]["log_loss"]
    new = reference["scores"]["same_item"]["log_loss"]
    entropy = [views["subject"]["R3-H3"]["rho_entropy_fraction"] for views in results.values()]
    sensitivity = [arm["scores"]["all"]["log_loss"] for name, arm in balanced.items() if "_var" in name or "_mean" in name or "effect_scale" in name]
    rec = reference["recovery"]["48"]
    slow = results["slow_retention"]["subject"]["R3-H3"]["recovery"]["48"]["ability"]
    return ["## Reading the numerical results", "",
            SEEDS + f" In the balanced world, subject repeat loss is {old:.4f} for the predecessor and {new:.4f} "
            "for the R3/H3 reference (1,792 repeat outcomes). This descriptive gain does not select rho or warmth. "
            f"R3's seed-mean entropy fractions span {min(entropy):.4f}–{max(entropy):.4f} across worlds, close to uniform. "
            "The rho point that generated a world gets slightly more than uniform mass, but that is weak evidence, "
            "not reliable identification.", "",
            f"After 48 events, the balanced reference's first family/item variances are {rec['family']['variance_ratio']:.3f} "
            f"and {rec['item']['variance_ratio']:.3f} times their original priors (64 estimates each): neither contracts. "
            f"The memory-weight ratios are {rec['memory_item']['variance_ratio']:.3f} and "
            f"{rec['memory_family']['variance_ratio']:.3f}, showing some information about those terms. "
            f"In slow_retention, ability RMSE is {slow['rmse']:.3f} and interval coverage {slow['coverage']:.3f}; "
            "the model can forecast practised answers while misattributing their explanation.", "",
            f"Across the fourteen one-factor prior perturbations, balanced-world overall subject loss ranges "
            f"{min(sensitivity):.4f}–{max(sensitivity):.4f} (3,072 outcomes per arm). These are sensitivity results, "
            "not a search for a replacement prior. The full tables retain each perturbation and every world, "
            "including losses and coverage failures. Added warmth scales have strongly overlapping temporal "
            "signals here; small prediction differences and curve-recovery failures leave ladder selection unresolved.", ""]


def render(payload, timestamp):
    result = payload["results"]
    lines = introduction(timestamp) + interpretation(payload)
    table(lines, "Exact joint same-item variance floor",
          "Deterministic, no random seed; 1 filter per row, 512 alternating category-0/2 observations at fixed time; "
          "no learning transition, memory or warmth. v_s=3, v_e as listed. Floor=3*v_e/(3+v_e).",
          ["v_e", "Floor", "Minimum / final ability variance", "Ability/effect covariance", "Sibling variance", "Novel variance"],
          [[number(r["effect_variance"]), number(r["floor"]), number(r["final_ability_variance"]),
            number(r["ability_effect_covariance"]), number(r["sibling_variance"]), number(r["novel_variance"])] for r in payload["floor"]])
    lines += ["The observed sum can become precise while ability and stable effects remain negatively correlated. "
              "This is exact within the existing Gaussian projection, not an exact non-Gaussian posterior. "
              "The floor is a fixed-time, fixed-feature result; gamma uncertainty and drift in the main run add other uncertainty.", "",
              "A structural contrast (no sampled outcomes): ability=+1 with effect=0 and ability=-1 with effect=+2 "
              "give identical drilled-item eta=1 and success=.98*sigmoid(1). On a novel family at zero mean effect "
              "they give eta=+1 and -1. Same-item likelihoods cannot distinguish the two; novel families expose "
              "a different projection, but **one novel binary answer cannot identify the decomposition**. "
              "These +/-1 and +2 values are an algebraic illustration, not added fitted priors or an unregistered recovery run.", ""]
    table(lines, "Warmth prior predictive check",
          "Deterministic, no random seed; 1 cold LO filter per row, 0 observations, one fresh item/family at each stated exposure gap. "
          "Variance excludes the unchanged unit residual; added variance=sum(.25*exp(-2*hours/h)) over extra scales.",
          ["Ladder", "Hours", "Eta mean (old=new)", "Old variance", "Added variance", "New variance", "Old/new success", "Old/new band"],
          [["H" + str(len(r["ladder"])), r["hours"], number(r["mean"]), number(r["old_variance"]), number(r["added_variance"]),
            number(r["variance"]), f'{number(r["old_success"])} / {number(r["success"])}',
            f'{number(r["old_band"])} / {number(r["band"])}'] for r in payload["warmth"]])
    for view in ("subject", "lo"):
        rows = []
        for world, views in result.items():
            for name, arm in views[view].items():
                score = arm["scores"]["all"]
                rec = arm["recovery"]["48"]
                rows.append([world, name, score["count"], *[number(score[k]) for k in ("log_loss", "brier", "calibration", "bias", "coverage")],
                             number(rec["ability"]["rmse"]), number(rec["ability"]["coverage"])])
        table(lines, f"All candidates and prior sensitivity — {view}",
              SEEDS + " Each row: 3,072 predictions (48 per learner), final ability recovery over 64 learners. "
              "H ladders and R supports follow the frozen register; sensitivity rows change one prior at a time around R3/H3 "
              "(LO: fixed rho=.5/H3). No result chooses a constant.",
              ["World", "Arm", "N", "Loss", "Brier", "ECE", "Bias", "Eta coverage", "Ability RMSE", "Ability coverage"], rows)
    rows = []
    for world, views in result.items():
        for name, arm in views["baselines"].items():
            score = arm["scores"]["all"]
            rows.append([world, name, score["count"], *[number(score[k]) for k in ("log_loss", "brier", "calibration", "bias", "coverage")]])
    table(lines, "Descriptive baselines", SEEDS + " Same baseline predictions in both views. Each world: 3,072 presentations; "
          "FSRS available only on 1,792 repeats (28/learner), not comparable to a full-stream loss without restricting the other arms. "
          "Rate a=.5/1/2 all remain candidates; last-outcome's 0/1 values are clipped only for log loss.",
          ["World", "Baseline", "N", "Loss", "Brier", "ECE", "Bias", "Eta coverage"], rows)
    for view in ("subject", "lo"):
        rows = []
        reference = "R3-H3" if view == "subject" else "rho0.5-H3"
        for world, views in result.items():
            for name in ("predecessor", reference):
                for stratum, score in views[view][name]["scores"].items():
                    if stratum == "all":
                        continue
                    rows.append([world, name, stratum, score["count"], *[number(score[k]) for k in ("log_loss", "brier", "calibration", "bias", "coverage")]])
        table(lines, f"Strata, delay and singleton checks — {view}", SEEDS + " Row N is the prediction count. "
              "Overlapping flags (singleton_all, all_first_surfaces, delay and source) are not additional observations. "
              "First_surface names initial anchors; all_first_surfaces also includes singleton-first and novel-after-drilling.",
              ["World", "Arm", "Stratum", "N", "Loss", "Brier", "ECE", "Bias", "Eta coverage"], rows)
    rows = []
    for world, views in result.items():
        for name, arm in views["baselines"].items():
            for stratum in ("same_item", "unseen_sibling", "singleton_all", "novel_after_drilling", "delay:<=1d", "delay:1..7d", "delay:>7d"):
                score = arm["scores"][stratum]
                rows.append([world, name, stratum, score["count"], *[number(score[k]) for k in ("log_loss", "brier", "calibration", "bias")]])
    table(lines, "Baseline strata", SEEDS + " Same predictions for both views; N=0 means unavailable (never imputed). "
          "Use same_item to compare FSRS against AD on the identical 1,792 outcomes per world.",
          ["World", "Baseline", "Stratum", "N", "Loss", "Brier", "ECE", "Bias"], rows)
    rows = []
    for world, views in result.items():
        for view, reference in (("subject", "R3-H3"), ("lo", "rho0.5-H3")):
            for checkpoint, recovery in views[view][reference]["recovery"].items():
                for name in ("ability", "family", "item", "memory_item", "memory_family"):
                    row = recovery[name]
                    rows.append([world, view, checkpoint, name, *[number(row[k]) for k in ("rmse", "bias", "coverage", "variance_ratio")]])
    table(lines, "Recovery and identifiability", SEEDS + " Each row: 64 posterior estimates, after 12 or 48 events/learner "
          "(768 or 3,072 training observations/world). Reference R3/H3 subject and rho=.5/H3 LO only. "
          "Family/item are the first anchor's stable effects. Variance ratios use the original prior, not a drift-adjusted prior; "
          "ability's denominator is the initial 3 (later gamma uncertainty is retained in its numerator).",
          ["World", "View", "After", "Quantity", "RMSE", "Bias", "95% coverage", "Posterior/prior variance"], rows)
    rows = []
    for world, views in result.items():
        for view in ("subject", "lo"):
            for h in (1, 3, 5):
                arm = views[view][f'{"R3" if view == "subject" else "rho0.5"}-H{h}']
                for name, row in arm["recovery"]["48"].items():
                    if name.startswith("warmth@"):
                        rows.append([world, view, f"H{h}", name, *[number(row[k]) for k in ("rmse", "bias", "coverage", "variance_ratio")]])
    table(lines, "Warmth curve recovery", SEEDS + " Each row: 64 estimates after 48 events/learner (3,072/world). "
          "Pointwise curve recovery is reported instead of asserting that correlated basis coefficients were separately identified.",
          ["World", "View", "Ladder", "Gap", "RMSE", "Bias", "95% coverage", "Variance ratio"], rows)
    rows = []
    for world, views in result.items():
        for name in ("R3-H3", "R5-H3"):
            arm = views["subject"][name]
            rows.append([world, name, ", ".join(number(w) for w in arm["rho_weights"]), number(arm["rho_entropy_fraction"])])
    table(lines, "Rho grid identifiability", SEEDS + " Each row: 64 learners after 48 events (3,072 observations). "
          "Weights are learner/seed averages in support order; entropy fraction is averaged over seed-mean weight vectors. "
          "It therefore measures cohort concentration and can conceal different individual posteriors. LO has no rho grid. "
          "No quarter-point generating world was registered, so R5 resolution cannot be validated.",
          ["World", "Support/ladder", "Posterior masses", "Entropy / uniform entropy"], rows)
    rows = []
    for name, comparison in payload["selection"].items():
        for world, row in comparison["worlds"].items():
            intervals = [" / ".join(number(v) for v in row["intervals"][stratum]) for stratum in ("same_item", "unseen_sibling", "all_first_surfaces")]
            rows.append([name, world, *intervals, number(row["minimum_recovery_coverage"]), row["predictive_recovery_criteria"]])
    table(lines, "Registered selection diagnostics", SEEDS + " Each interval has 8 paired seed means; each seed has 224 repeat, "
          "64 sibling and 96 first-surface outcomes. Cells give mean / lower / upper of candidate-minus-simpler log loss, t(7) 95%. "
          "Negative favours the candidate. Coverage minimum covers ability, memory weights and six warmth-curve points at event 48. "
          "The joint rule is deliberately reported separately from isolated loss improvements.",
          ["Comparison", "World", "Repeat delta / CI", "Sibling delta / CI", "First-surface delta / CI", "Min recovery coverage", "Joint criteria"], rows)
    lines += ["".join(f'- `{name}`: **{c["verdict"]}**; additional diagnostics `{json.dumps(c["diagnostics"], sort_keys=True)}`.\n'
                     for name, c in payload["selection"].items()), "",
              "Failure to select is not equivalence, nor proof that no effect exists. Where a loss interval is wholly "
              "positive it is evidence against that candidate under that world; intervals crossing zero cannot resolve "
              "the predictive ordering. Sparse siblings, correlated memory/effect terms and prior sensitivity prevent "
              "a general per-learner recovery claim. These are observational fits to scripted schedules, not randomized "
              "policy-effect estimates.", ""]
    table(lines, "Cost", "Seeds `adm0-v1:0`–`adm0-v1:7`; balanced world, 1 learner/seed, 48-event cold replays. "
          "Cached-input and synthetic Next costs are per call over 100 calls/seed. Next uses the full 108-filter state, "
          "three repeat/sibling/novel predictions and 16 fixed novel-family demand points; it is not the production router. "
          "No model, DB, UI or disk work is included. Covariance bytes count S and S0 only.",
          ["Workload", "Median ms", "Min ms", "Max ms", "Calls/seed", "Filters", "Coordinates", "Covariance bytes"],
          [[key, *[number(row[k] * 1000) for k in ("median_seconds", "min_seconds", "max_seconds")], row["calls_per_seed"],
            row.get("filters", "108 for Next" if key == "synthetic_next" else "N/A"), row.get("coordinates", "N/A"), row.get("covariance_bytes", "N/A")]
           for key, row in payload["cost"].items()])
    lines += [f'Complete candidate-grid experiment: **{payload["candidate_grid_seconds"]:.3f} s**; '
              f'complete numerical report workload including diagnostics/benchmarks: **{payload["seconds"]:.3f} s**. '
              "Counts: 6 worlds x 8 seeds x 2 views x (23 candidates + predecessor) x 48 events x 8 learners = "
              "884,736 arm-predictions, plus six descriptive baselines on the same 18,432 presentations. "
              "Subject candidate filters per learner are 3, 9 or 15; the full inherited-grid/R3 benchmark has 108. "
              "The timings include Python/NumPy overhead and depend on the execution environment; no latency threshold "
              "was chosen. Full inherited 36-point predecessor cost was not separately timed; the exact collapsed "
              "three-point predecessor was. No approximation is proposed, so approximation error is N/A.", "",
              "## Tests, reproduction and owner questions", "",
              "Landing contracts: `tests/test_ad_memory_simulation.py -m 'not arc_close'`. Full report source: "
              "the same explicit file with `-m arc_close --junitxml=results.xml` (final corrected run at the registered size). "
              "Render with `python scripts/adm0_simulation_report.py results.xml docs/reviews/adm0-simulation-report.md`. "
              "Use the supplied pytest/venv wrappers; no index or commit operations are performed. The final handoff "
              "records the actual regression/gate command results.", "",
              "For the spec owner: correct §4.2's sign wording to match §4.4; keep the rho/warmth/prior ranges "
              "unselected pending stronger identification; confirm that RE8 width recovery belongs to ADM3; decide "
              "whether later experiments should independently vary delays, include quarter-point rho truths and "
              "multiple cells, or randomized novel-family checks. Those require a new preregistration. "
              "Owner-copy counts remain entirely in the owner's lane. No production support or LO value is authorized by this report.", ""]
    return "\n".join(lines)


def main():
    source, destination = map(Path, sys.argv[1:])
    root = Path(__file__).resolve().parents[1]
    actual = hashlib.sha256((root / "docs/reviews/adm0-preregistration.md").read_bytes()).hexdigest()
    if actual != HASH:
        raise ValueError("frozen preregistration changed")
    tree = ET.parse(source)
    payloads = [p.attrib["value"] for p in tree.findall(".//property") if p.attrib.get("name") == "adm0_results"]
    if len(payloads) != 1 or tree.findall(".//failure") or tree.findall(".//error"):
        raise ValueError("expected one successful registered run")
    payload = json.loads(payloads[0])
    if any(c["verdict"] == "favoured in simulation" for c in payload["selection"].values()):
        raise ValueError("report narrative must be reviewed: selection result changed")
    stamp = tree.find(".//testsuite").attrib.get("timestamp", "unavailable")
    destination.write_text(render(payload, stamp), encoding="utf-8")
    print(f"Rendered {len(payload['worlds'])} worlds, {payload['presentations']} presentations; preregistration hash verified")


if __name__ == "__main__":
    main()
