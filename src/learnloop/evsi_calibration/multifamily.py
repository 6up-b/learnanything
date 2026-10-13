"""The multi-family study behind ``learnloop evsi multisim`` (stage ``evsi-multisim``).

Owner decision 2026-10-13: *multiple sim families for EVSI calibration*.
RankCert (arXiv 2609.26069): a policy or parameter conclusion drawn under one
simulator family is a statement about that family; certify it only when it
holds under every structurally different family that fits the data.

For every family (:mod:`.families`; ``lca``, ``cdm``, ``nrm``, ``lta``, plus
the ``lta_reveal`` stress variant) and under common seeds:

1. **main** (fitted strength, repair 3): every policy with the family's own
   calibrated system, today's ``hand_set`` vocabulary, and every other fitted
   family's calibrated system (RankCert's rotation of which family is truth).
2. **regimes**: instrument strength (fitted, 0.7, 0.9) x repair minutes
   (3, 10, 30), the family's own calibrated system.
3. **rotation** at (0.9, 10) and (0.9, 30): the other families' systems.
4. **sensitivity** at (0.9, 10): the single-family study's sweeps.
5. **Part C**: the measured loss against minutes-only, at the fitted strength
   and 0.9.
6. **pseudo count**: a stream of episodes in which the system starts from the
   hand-set vocabulary and folds every check into posterior-weighted counts
   (as ``probe_families.record_real_observation_counts`` does), at several
   ``DEFAULT_CONDITIONAL_PSEUDO_COUNT`` values.

Then :func:`analyze` scores every claim of the single-family study family by
family (agreement, effect, CI; ``supported`` only when every family's CI
agrees) and, per regime, which policy wins in each family, the co-winners,
the regret of acting on another family's winner and the rank agreement
(Kendall's tau) between families; and each policy's worst-case regret over
every family x regime cell (the robust choice when the families disagree
about the winner). The ranked change proposal built on it is in
``docs/reviews/evsi-multisim.md``.
"""

from __future__ import annotations

import math
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from learnloop.config.schema import ProbeEpisodeConfig
from learnloop.diagnosis import robust_composition as rc
from learnloop.diagnosis.probe_families import (
    CONTRAST_CONFUSABLE_DEFAULT_ROWS,
    DEFAULT_CONDITIONAL_PSEUDO_COUNT,
    ORDINAL_VOCABULARY,
)
from learnloop.evsi_calibration import metrics as M
from learnloop.evsi_calibration import policies as P
from learnloop.evsi_calibration.eedi import OPTIONS, EediBank, EediQuestion
from learnloop.evsi_calibration.experiments import (
    DEFAULT_SWEEP_POLICIES,
    SWEEP_POLICIES,
    SWEEPS,
    hand_set_implied,
)
from learnloop.evsi_calibration.families import (
    FAMILY_NAMES,
    STRESS_FAMILIES,
    FamilyModel,
    build_families,
    implied_quantities,
)
from learnloop.evsi_calibration.family_fit import FamilyFits
from learnloop.evsi_calibration.multisim import (
    MULTISIM_VERSION,
    SYSTEM_FAMILY,
    SYSTEM_HAND_SET,
    FamilyLearner,
    MultiSimRun,
    MultiSimSettings,
    World,
    _Models,
    _seed,
    draw_family_learners,
    run_family_simulation,
    true_loss,
    with_policy,
)
from learnloop.evsi_calibration.simulate import loss_table_for
from learnloop.evsi_calibration.world import (
    HYP_KNOWS,
    HYP_OTHER,
    MIS_PREFIX,
    build_scenarios,
    route_for,
)

#: v2: rotation claims per regime, S4, the A ablations, ``no difference``, and
#: C6c's log loss bootstrapped per arm.
#: v3 (Codex review): only families that pass the adequacy gate vote, and a
#: claim missing a voting family's cell is ``insufficient evidence`` (F2); a
#: value certifies only through a CI (C1a's from the subjects); A4 (the
#: package's serving rule) and S4 on the top-value variant (F1); episodes that
#: ran out of questions are counted (F4).
MULTIFAMILY_VERSION = "evsi_multifamily_v3"

#: Paired comparisons recorded in every cell: (left, right) -> mean(right - left).
PAIRS: tuple[tuple[str, str], ...] = (
    ("incumbent", "evsi"),
    ("evsi_lcb_only", "evsi"),
    ("evsi_lcb_only", "evsi_lookahead"),
    ("evsi", "evsi_lookahead"),
    ("caps_only", "incumbent"),
    ("incumbent", "evsi_lookahead"),
    ("caps_only", "evsi_lookahead"),
    ("incumbent", "evsi_lcb_only"),
    ("eig_no_gate", "eig"),
    ("incumbent", "max_entropy"),
    ("incumbent", "random"),
    ("evsi_lookahead", "eig_no_gate"),
    ("eig_no_gate", "evsi_lcb_only"),
    ("incumbent", "voi_successor"),
    ("voi_successor", "voi_proposed"),
    ("incumbent", "voi_proposed"),
    ("caps_only", "voi_proposed"),
    ("evsi_lookahead", "voi_proposed"),
    ("voi_proposed", "voi_p_with_gate"),
    ("voi_proposed", "voi_p_with_fallback"),
    ("voi_p_one_step", "voi_proposed"),
    ("voi_proposed", "voi_p_top_value"),
    ("evsi_lookahead", "voi_p_top_value"),
    ("voi_successor", "voi_p_with_fallback"),
    ("incumbent", "voi_p_with_fallback"),
)


@dataclass(frozen=True)
class MultiFamilySettings:
    learners: int = 400
    sensitivity_learners: int = 300
    seed: int = 20261012
    workers: int = 8
    families: tuple[str, ...] = FAMILY_NAMES
    stress_families: tuple[str, ...] = STRESS_FAMILIES
    strengths: tuple[float | None, ...] = (None, 0.7, 0.9)
    repairs: tuple[float, ...] = (3.0, 10.0, 30.0)
    rotation_regimes: tuple[tuple[float | None, float], ...] = ((0.9, 10.0), (0.9, 30.0))
    sensitivity_strength: float = 0.9
    sensitivity_repair: float = 10.0
    sweeps: tuple[str, ...] | None = None
    unresolved_encounters: tuple[float, ...] = (3.0, 6.0, 12.0, 24.0)
    minutes_per_repeat_error: float = 2.0
    pseudo_counts: tuple[float, ...] = (0.5, 2.0, 8.0, 32.0)
    pseudo_count_regimes: tuple[tuple[float | None, float], ...] = ((None, 3.0), (0.9, 10.0))
    pseudo_count_block: int = 50
    draw_count: int = 32
    bootstrap: int = 400

    def as_dict(self) -> dict[str, Any]:
        return {k: (list(v) if isinstance(v, tuple) else v) for k, v in self.__dict__.items()}


def _label(strength: float | None) -> str:
    return "fitted" if strength is None else str(strength)


def _compact_episodes(run: MultiSimRun) -> dict[str, Any]:
    """Per policy, per learner (in learner order): total minutes, checks, right action."""

    order = [spec.index for spec in run.learners]
    position = {index: i for i, index in enumerate(order)}
    out: dict[str, Any] = {"learners": order, "policies": {}}
    by_policy: dict[str, list[Any]] = {}
    for episode in run.episodes:
        by_policy.setdefault(episode.policy, []).append(episode)
    for policy, episodes in sorted(by_policy.items()):
        total = [0.0] * len(order)
        checks = [0] * len(order)
        correct = [0] * len(order)
        for e in episodes:
            i = position[e.learner]
            total[i] = round(float(e.total_minutes), 4)
            checks[i] = int(e.checks)
            correct[i] = int(bool(e.correct_action))
        out["policies"][policy] = {"total": total, "checks": checks, "correct": correct}
    return out


def _paired(compact: Mapping[str, Any], left: str, right: str, *, seed: int, draws: int) -> dict[str, Any] | None:
    policies = compact["policies"]
    if left not in policies or right not in policies:
        return None
    a = np.asarray(policies[left]["total"], dtype=float)
    b = np.asarray(policies[right]["total"], dtype=float)
    diffs = b - a
    if diffs.size == 0:
        return None
    rng = np.random.default_rng(seed)
    picks = rng.integers(0, diffs.size, size=(draws, diffs.size))
    boots = diffs[picks].mean(axis=1)
    return {
        "n": int(diffs.size),
        "mean_difference": round(float(diffs.mean()), 4),
        "ci95": [round(float(np.quantile(boots, 0.025)), 4), round(float(np.quantile(boots, 0.975)), 4)],
    }


def _policy_table(run: MultiSimRun, *, seed: int, draws: int) -> dict[str, Any]:
    summary = M.summarize(run.checks, run.episodes, seed=seed, draws=draws)
    out: dict[str, Any] = {}
    for policy, blocks in summary.items():
        e = blocks["episodes"]
        episodes = [x for x in run.episodes if x.policy == policy]
        out[policy] = {
            "mean_checks": e.get("mean_checks"),
            "max_checks": max((x.checks for x in episodes), default=0),
            #: Episodes that ended because the subject's questions ran out (the
            #: bank, not the policy's rule, stopped them), and any a count bound
            #: stopped (none since review F4).
            "ran_out_of_questions": sum(1 for x in episodes if x.stop_reason == "no_question_left"),
            "count_bound_stops": sum(1 for x in episodes if x.stop_reason == "safety_bound"),
            "mean_total_minutes": e.get("mean_total_minutes"),
            "total_minutes_ci95": e.get("total_minutes_ci95"),
            "correct_action_rate": e.get("correct_action_rate"),
            "misconception_identified_rate": e.get("misconception_identified_rate"),
            "mean_wasted_minutes": e.get("mean_wasted_minutes"),
            "stop_reasons": dict(list((e.get("stop_reasons") or {}).items())[:4]),
            "outcome_calibration": {k: blocks["outcome_calibration"].get(k) for k in ("log_loss", "ece", "checks")},
            "information": {k: blocks["information"].get(k) for k in (
                "mean_predicted_eig", "mean_entropy_drop", "mean_truth_log_gain", "truth_log_gain_ci95")},
            "action_change": {k: blocks["action_change"].get(k) for k in ("mean_predicted", "realized_rate")},
            "value_of_checks": {k: blocks["value_of_checks"].get(k) for k in (
                "checks", "mean_predicted_evsi_point", "mean_realized_value", "realized_value_ci95",
                "model_minutes_per_nat", "minutes_per_nat", "minutes_per_nat_ci95", "member_quantile_minus_realized")},
        }
    return out


def _cell(run: MultiSimRun, *, seed: int, draws: int) -> dict[str, Any]:
    compact = _compact_episodes(run)
    pairs = {}
    for left, right in PAIRS:
        result = _paired(compact, left, right, seed=seed, draws=draws)
        if result is not None:
            pairs[f"{right}-{left}"] = result
    return {"policies": _policy_table(run, seed=seed, draws=draws), "paired": pairs, "episodes": compact}


# -- the pseudo-count stream ------------------------------------------------------------------------------


_SLOT_OF = {"knows": "robust_initial_grasp", "confuses": "confuses_with_neighbor", "other": "other_or_unknown"}
ROLES = ("correct", "signature", "other_error")


def _vocabulary_role_row(slot: str) -> dict[str, float]:
    words = CONTRAST_CONFUSABLE_DEFAULT_ROWS[slot]
    weight = {outcome: ORDINAL_VOCABULARY[word] for outcome, word in words.items()}
    row = {
        "correct": weight["correct_target_reason"] + weight["correct_weak_reason"],
        "signature": weight["confusable_signature"],
        "other_error": weight["other_systematic_error"],
    }
    total = sum(row.values())
    return {k: v / total for k, v in row.items()}


def _slot_and_signature(hypothesis: str, question: EediQuestion) -> tuple[str, tuple[str, ...]]:
    """The contrast card's slot for a hypothesis on a question, and its signature
    options (exactly :func:`.world.hand_set_row`'s mapping)."""

    if hypothesis == HYP_KNOWS:
        slot, signature = "knows", tuple(sorted(question.misconception_by_option))
    elif hypothesis.startswith(MIS_PREFIX) and question.options_for(hypothesis[len(MIS_PREFIX):]):
        slot, signature = "confuses", question.options_for(hypothesis[len(MIS_PREFIX):])
    else:
        slot, signature = "other", tuple(sorted(question.misconception_by_option))
    return _SLOT_OF[slot], (signature or question.distractors)


def _role_of(option: str, question: EediQuestion, signature: Sequence[str]) -> str:
    if option == question.correct:
        return "correct"
    return "signature" if option in signature else "other_error"


def counted_row(hypothesis: str, question: EediQuestion, counts: Mapping[str, Mapping[str, float]],
                pseudo_count: float) -> dict[str, float]:
    """The card's compiled row ``(pseudo * vocabulary + counts) / (pseudo + n)``
    (``validate_and_compile_card``), mapped onto the four options."""

    slot, signature = _slot_and_signature(hypothesis, question)
    base = _vocabulary_role_row(slot)
    observed = counts.get(slot, {})
    n = sum(observed.values())
    role_row = {r: (pseudo_count * base[r] + observed.get(r, 0.0)) / (pseudo_count + n) for r in ROLES}
    distractors = question.distractors
    rest = [d for d in distractors if d not in signature] or list(distractors)
    row = {o: 0.0 for o in OPTIONS}
    row[question.correct] += role_row["correct"]
    for option in signature:
        row[option] += role_row["signature"] / len(signature)
    for option in rest:
        row[option] += role_row["other_error"] / len(rest)
    total = sum(row.values())
    return {o: v / total for o, v in row.items()}


def run_count_stream(
    world: World,
    learners: Sequence[FamilyLearner],
    *,
    mode: str,
    pseudo_count: float,
    repair_minutes: float,
    seed: int,
    max_checks: int = 4,
) -> list[dict[str, float]]:
    """One stream of episodes in learner order with a capped EIG chooser.

    ``mode``: ``counts`` (vocabulary + posterior-weighted counts, learning as it
    goes), ``hand_set`` (the vocabulary, frozen) or ``family`` (the family's
    calibrated rows: the target the counts should reach)."""

    models = _Models(world)
    ps = P.PolicySettings(repair_minutes=repair_minutes)
    counts: dict[str, dict[str, float]] = {}
    records: list[dict[str, float]] = []
    config = ProbeEpisodeConfig()
    for spec in learners:
        scenario = world.scenarios[spec.scenario_index]
        truth = models.get(world.truth, spec.scenario_index)
        prior = truth.system_prior()

        def rows_for(question: EediQuestion) -> dict[str, dict[str, float]]:
            if mode == "family":
                return truth.system_rows(question)
            if mode == "hand_set":
                return {h: counted_row(h, question, {}, 1.0) for h in scenario.hypotheses}
            return {h: counted_row(h, question, counts, pseudo_count) for h in scenario.hypotheses}

        belief = dict(prior)
        for question_id, option in spec.history:
            belief = rc.observed_update(rows_for(scenario.question(question_id)), belief, option)
        loss_table = loss_table_for(scenario, ps, unresolved=0.0)
        answered = {q for q, _ in spec.history}
        remaining = [q.question_id for q in scenario.questions if q.question_id not in answered]
        state_truth = spec.state
        log_losses: list[float] = []
        gains: list[float] = []
        n = 0
        while remaining and n < max_checks:
            ordered = sorted(belief.values(), reverse=True)
            top, second = ordered[0], (ordered[1] if len(ordered) > 1 else 0.0)
            stable = top >= config.posterior_stop_threshold and (top <= 0 or second / top <= config.ambiguity_threshold)
            if stable and n >= config.minimum_independent_observations:
                break
            rows_by_q = {q: rows_for(scenario.question(q)) for q in remaining}
            best = max(sorted(remaining), key=lambda q: rc.expected_information_gain(rows_by_q[q], belief))
            question = scenario.question(best)
            rows = rows_by_q[best]
            predicted = P.mixture(rows, belief)
            needs_now = truth.needs(state_truth)
            answer_rng = np.random.default_rng(_seed(seed, "answer", spec.index, best))
            realized = truth.answer(state_truth, question, answer_rng)
            if truth.learns:
                uniform = float(np.random.default_rng(_seed(seed, "learn", spec.index, "episode", n)).random())
                state_truth = truth.transition(state_truth, uniform)
            log_losses.append(-math.log(max(predicted.get(realized, 0.0), 1e-12)))
            posterior = rc.observed_update(rows, belief, realized)
            before = max(sum(belief.get(h, 0.0) for h in needs_now), 1e-12)
            after = max(sum(posterior.get(h, 0.0) for h in needs_now), 1e-12)
            gains.append(math.log(after) - math.log(before))
            if mode == "counts":
                for h, weight in posterior.items():
                    slot, signature = _slot_and_signature(h, question)
                    role = _role_of(realized, question, signature)
                    row = counts.setdefault(slot, {})
                    row[role] = row.get(role, 0.0) + float(weight)
            belief = posterior
            remaining = [q for q in remaining if q != best]
            n += 1
        action = loss_table.argmin_action(belief)
        needs_final = truth.needs(state_truth)
        records.append({
            "checks": n,
            "log_loss_sum": float(sum(log_losses)),
            "truth_gain_sum": float(sum(gains)),
            "correct": float(action in {route_for(h) for h in needs_final}),
            "total_minutes": n * ps.check_minutes + true_loss(needs_final, action, repair_minutes=repair_minutes,
                                                             unresolved=0.0),
        })
    return records


def _stream_summary(records: Sequence[Mapping[str, float]], block: int) -> dict[str, Any]:
    blocks = []
    for start in range(0, len(records), block):
        part = records[start:start + block]
        checks = sum(r["checks"] for r in part)
        blocks.append({
            "episodes": [start + 1, start + len(part)],
            "log_loss": round(sum(r["log_loss_sum"] for r in part) / checks, 4) if checks else None,
            "truth_gain_per_check": round(sum(r["truth_gain_sum"] for r in part) / checks, 4) if checks else None,
            "right_action": round(float(np.mean([r["correct"] for r in part])), 4),
            "total_minutes": round(float(np.mean([r["total_minutes"] for r in part])), 4),
        })
    checks = sum(r["checks"] for r in records)
    return {
        "blocks": blocks,
        "log_loss": round(sum(r["log_loss_sum"] for r in records) / checks, 4) if checks else None,
        "truth_gain_per_check": round(sum(r["truth_gain_sum"] for r in records) / checks, 4) if checks else None,
        "right_action": round(float(np.mean([r["correct"] for r in records])), 4) if records else None,
        "total_minutes": round(float(np.mean([r["total_minutes"] for r in records])), 4) if records else None,
        "per_episode_total": [round(r["total_minutes"], 4) for r in records],
        "per_episode_log_loss": [round(r["log_loss_sum"], 4) for r in records],
        "per_episode_checks": [int(r["checks"]) for r in records],
    }


def _stream_job(payload: tuple[World, Sequence[FamilyLearner], str, float, float, int, int]) -> dict[str, Any]:
    world, learners, mode, pseudo, repair, seed, block = payload
    records = run_count_stream(world, learners, mode=mode, pseudo_count=pseudo, repair_minutes=repair, seed=seed)
    return _stream_summary(records, block)


# -- the study ------------------------------------------------------------------------------------------------


def study_base(settings: MultiFamilySettings) -> MultiSimSettings:
    """Every cell's starting settings. No count bound on any episode (review F4):
    the bank is finite, so an episode ends by its rule or when its subject's
    questions run out, and a bound would censor exactly the episodes whose
    cost a value rule is judged on."""

    return MultiSimSettings(learners=settings.learners, seed=settings.seed, workers=settings.workers,
                            policy=P.PolicySettings(draw_count=settings.draw_count, safety_bound=None))


def run_multifamily(
    bank: EediBank,
    fits: FamilyFits,
    settings: MultiFamilySettings,
    *,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    say = progress or (lambda message: None)
    started = time.time()
    families = build_families(bank, fits)
    scenarios = tuple(build_scenarios(bank, fits.lca))
    if not scenarios:
        raise ValueError("no simulation scenario: the 2024 bank and the fits share no usable subject")
    names = tuple(n for n in settings.families if n in families)
    stress = tuple(n for n in settings.stress_families if n in families)
    base = study_base(settings)
    strength_cache: dict[tuple[str, float | None], FamilyModel] = {}

    def family_at(name: str, strength: float | None) -> FamilyModel:
        key = (name, strength)
        if key not in strength_cache:
            strength_cache[key] = families[name].with_strength(strength)
        return strength_cache[key]

    def world_at(name: str, strength: float | None) -> World:
        return World(family_at(name, strength), scenarios,
                     systems={other: family_at(other, strength) for other in names})

    learners_cache: dict[tuple[str, float | None], list[FamilyLearner]] = {}

    def learners_at(name: str, strength: float | None) -> list[FamilyLearner]:
        key = (name, strength)
        if key not in learners_cache:
            learners_cache[key] = draw_family_learners(world_at(name, strength), base)
        return learners_cache[key]

    report: dict[str, Any] = {
        "version": MULTIFAMILY_VERSION,
        "simulation_version": MULTISIM_VERSION,
        "settings": settings.as_dict(),
        "policy_defaults": base.policy.as_dict(),
        "fits": {
            "version": fits.version,
            "source": fits.source,
            "validation": fits.validation,
            "lca_pooled": {k: v.as_dict() for k, v in fits.lca.pooled.items()},
            "lca_persistence": {k: v.as_dict() for k, v in fits.lca.persistence.items()},
            "lta_transitions": np.round(fits.lta.transitions, 6).tolist(),
            "lta_transition_counts": np.round(fits.lta.transition_counts, 1).tolist(),
            "cdm_subjects": len(fits.cdm),
            "nrm_triples": len(fits.nrm),
        },
        "bank": {"scenarios": len(scenarios), "questions": len(bank.questions)},
        "hand_set_implied": hand_set_implied(bank, scenarios),
        "families": {},
    }
    seed, draws = settings.seed, settings.bootstrap
    with ProcessPoolExecutor(max_workers=settings.workers) as pool:

        def simulate(name: str, strength: float | None, run_settings: MultiSimSettings,
                     learners: Sequence[FamilyLearner] | None = None) -> MultiSimRun:
            return run_family_simulation(world_at(name, strength), run_settings,
                                         learners=learners if learners is not None else learners_at(name, strength),
                                         pool=pool)

        for name in names + stress:
            fitted = name in names
            say(f"{name}: implied quantities")
            block: dict[str, Any] = {
                "fitted": fitted,
                "implied": {_label(c): implied_quantities(family_at(name, c), scenarios) for c in settings.strengths},
            }
            block["flagged_learners"] = {_label(c): len(learners_at(name, c)) for c in settings.strengths}
            block["starting_belief"] = {
                _label(c): _starting_belief(world_at(name, c), learners_at(name, c)) for c in settings.strengths
            }
            # 1. main
            say(f"{name}: main comparison")
            main: dict[str, Any] = {}
            systems = [SYSTEM_FAMILY, SYSTEM_HAND_SET] + ([o for o in names if o != name] if fitted else [])
            for system in systems:
                main[system] = _cell(simulate(name, None, replace(base, system=system)), seed=seed, draws=draws)
            block["main"] = main
            # 2. regimes
            say(f"{name}: regimes")
            regimes = []
            for strength in settings.strengths:
                for repair in settings.repairs:
                    if strength is None and repair == 3.0:
                        cell = main[SYSTEM_FAMILY]
                    else:
                        cell = _cell(simulate(name, strength, with_policy(base, repair_minutes=repair)),
                                     seed=seed, draws=draws)
                    regimes.append({"consistency": _label(strength), "repair_minutes": repair, **cell})
            block["regimes"] = regimes
            if not fitted:
                report["families"][name] = block
                continue
            # 3. rotation
            say(f"{name}: rotation")
            rotation = []
            for strength, repair in settings.rotation_regimes:
                for system in [o for o in names if o != name]:
                    run = simulate(name, strength, replace(with_policy(base, repair_minutes=repair), system=system))
                    rotation.append({"consistency": _label(strength), "repair_minutes": repair, "system": system,
                                     **_cell(run, seed=seed, draws=draws)})
            block["rotation"] = rotation
            # 4. sensitivity
            say(f"{name}: sensitivity")
            block["sensitivity"] = _sensitivity(name, settings, base, simulate, learners_at)
            # 5. Part C
            say(f"{name}: part C")
            block["part_c"] = _part_c(name, fits, settings, base, simulate, learners_at)
            report["families"][name] = block
        # 6. pseudo count streams
        say("pseudo count streams")
        jobs, keys = [], []
        for name in names:
            for strength, repair in settings.pseudo_count_regimes:
                world = world_at(name, strength)
                learners = learners_at(name, strength)
                arms = [("hand_set", 0.0), ("family", 0.0)] + [("counts", pc) for pc in settings.pseudo_counts]
                for mode, pc in arms:
                    jobs.append((world, learners, mode, pc, repair, seed, settings.pseudo_count_block))
                    keys.append((name, _label(strength), repair, mode, pc))
        results = list(pool.map(_stream_job, jobs))
    streams: dict[str, Any] = {}
    for (name, strength, repair, mode, pc), result in zip(keys, results):
        arm = mode if mode != "counts" else f"pseudo_{pc:g}"
        streams.setdefault(name, {}).setdefault(f"{strength}/{repair:g}", {})[arm] = result
    report["pseudo_count"] = {
        "current": DEFAULT_CONDITIONAL_PSEUDO_COUNT,
        "chooser": "capped hypothesis EIG (caps_only), mean rows",
        "streams": streams,
    }
    report["elapsed_seconds"] = round(time.time() - started, 1)
    report["analysis"] = analyze(report)
    return report


def _starting_belief(world: World, learners: Sequence[FamilyLearner]) -> dict[str, Any]:
    models = _Models(world)
    by_class: dict[str, list[float]] = {}
    for spec in learners:
        scenario = world.scenarios[spec.scenario_index]
        model = models.get(world.truth, spec.scenario_index)
        belief = model.system_prior()
        for question_id, option in spec.history:
            belief = rc.observed_update(model.system_rows(scenario.question(question_id)), belief, option)
        needs = spec.needs
        cls = "knows" if needs == (HYP_KNOWS,) else ("other" if needs == (HYP_OTHER,) else
                                                      ("holds_two" if len(needs) > 1 else "holds"))
        by_class.setdefault(cls, []).append(sum(belief.get(h, 0.0) for h in needs))
    return {c: {"n": len(v), "mean_probability_on_truth": round(float(np.mean(v)), 4)} for c, v in sorted(by_class.items())}


def _sensitivity(name: str, settings: MultiFamilySettings, base: MultiSimSettings, simulate, learners_at) -> dict[str, Any]:
    strength, repair = settings.sensitivity_strength, settings.sensitivity_repair
    sens_base = with_policy(replace(base, learners=settings.sensitivity_learners), repair_minutes=repair)
    learners = learners_at(name, strength)[: settings.sensitivity_learners]
    out: dict[str, Any] = {"regime": {"consistency": strength, "repair_minutes": repair}, "parameters": {}}
    for sweep, (field_name, current, grid) in SWEEPS.items():
        if settings.sweeps is not None and sweep not in settings.sweeps:
            continue
        policies = SWEEP_POLICIES.get(sweep, DEFAULT_SWEEP_POLICIES)
        runs: dict[float, MultiSimRun] = {}
        for value in sorted(set(grid) | {current}):
            arm = replace(with_policy(sens_base, **{field_name: value}), policies=policies,
                          truth_repair_minutes=repair, truth_check_minutes=sens_base.policy.check_minutes)
            if field_name == "draw_count":
                arm = replace(arm, policy=replace(arm.policy, draw_count=int(value)))
            runs[value] = simulate(name, strength, arm, learners)
        rows = []
        for value, run in sorted(runs.items()):
            row: dict[str, Any] = {"value": value, "current": value == current, "policies": {}}
            for policy in policies:
                episodes = [e for e in run.episodes if e.policy == policy]
                base_episodes = [e for e in runs[current].episodes if e.policy == policy]
                summary = M.episode_summary(episodes, np.random.default_rng(settings.seed), settings.bootstrap)
                row["policies"][policy] = {
                    "mean_total_minutes": summary["mean_total_minutes"],
                    "mean_checks": summary["mean_checks"],
                    "correct_action_rate": summary["correct_action_rate"],
                    "difference_vs_current": M.paired_difference(base_episodes, episodes, seed=settings.seed,
                                                                 draws=settings.bootstrap),
                }
            rows.append(row)
        out["parameters"][sweep] = {"field": field_name, "current": current, "rows": rows}
    return out


def _part_c(name: str, fits: FamilyFits, settings: MultiFamilySettings, base: MultiSimSettings, simulate,
            learners_at) -> dict[str, Any]:
    excess = fits.lca.persistence.get("excess_repeat_rate")
    rate = float(excess.median) if excess is not None and math.isfinite(excess.median) else 0.151
    out: dict[str, Any] = {"excess_repeat_rate": rate, "minutes_per_repeat_error": settings.minutes_per_repeat_error,
                           "rows": []}
    for strength in (None, settings.sensitivity_strength):
        for encounters in settings.unresolved_encounters:
            true_u = rate * encounters * settings.minutes_per_repeat_error
            arms = {}
            for label, system_u in (("minutes_only", 0.0), ("measured_unresolved", true_u)):
                arm = with_policy(
                    replace(base, truth_unresolved_minutes=true_u,
                            policies=("evsi_lcb_only", "evsi_lookahead", "incumbent")),
                    unresolved_minutes=system_u,
                )
                arms[label] = simulate(name, strength, arm)
            for policy in ("evsi_lcb_only", "evsi_lookahead"):
                left = [e for e in arms["minutes_only"].episodes if e.policy == policy]
                right = [e for e in arms["measured_unresolved"].episodes if e.policy == policy]
                out["rows"].append({
                    "consistency": _label(strength),
                    "encounters": encounters,
                    "true_unresolved_minutes": round(true_u, 4),
                    "policy": policy,
                    "minutes_only_total": round(float(np.mean([e.total_minutes for e in left])), 4),
                    "measured_total": round(float(np.mean([e.total_minutes for e in right])), 4),
                    "minutes_only_checks": round(float(np.mean([e.checks for e in left])), 4),
                    "measured_checks": round(float(np.mean([e.checks for e in right])), 4),
                    "difference": M.paired_difference(left, right, seed=settings.seed, draws=settings.bootstrap),
                })
    return out


# -- analysis: claims across families (RankCert) -------------------------------------------------------------

#: RankCert's uncertainty set needs at least two structurally different
#: families that pass the adequacy gate; with fewer, nothing is certified.
MIN_VOTING_FAMILIES = 2
INSUFFICIENT = "insufficient evidence"


def _has_ci(value: Mapping[str, Any]) -> bool:
    ci = value.get("ci95")
    return isinstance(ci, (list, tuple)) and len(ci) == 2 and all(isinstance(x, (int, float)) for x in ci)


def _ci_only(values: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """A value certifies only through its 95% CI: one without a CI can hold
    (its point estimate agrees) but is never certified."""

    return [{**v, "certified": bool(v.get("certified")) and _has_ci(v)} for v in values]


def _voting_families(report: Mapping[str, Any], fitted: Sequence[str]) -> tuple[list[str], list[dict[str, str]]]:
    """The families that vote, and the exclusions with their reason. A family
    votes when it is in the report, was fitted, and passed the adequacy gate
    on held-out students (RankCert: predictive adequacy is a prerequisite of
    the uncertainty set). The study's required families come from its
    settings; one absent from the report is an exclusion too."""

    validation = ((report.get("fits") or {}).get("validation") or {}).get("families") or {}
    required = list((report.get("settings") or {}).get("families") or [])
    voting: list[str] = []
    excluded: list[dict[str, str]] = []
    for name in required:
        if name not in report.get("families", {}):
            excluded.append({"family": name, "reason": "required by the study but absent from the report"})
    for name in fitted:
        block = validation.get(name)
        if block is None:
            excluded.append({"family": name, "reason": "no held-out validation (adequacy unknown)"})
        elif block.get("adequate") is not True:
            excluded.append({"family": name, "reason": "failed the adequacy gate on held-out students"})
        else:
            voting.append(name)
    return voting, excluded


def _verdict(values: Sequence[Mapping[str, Any]]) -> str:
    """``supported`` when every family's CI agrees with the claim, ``directional``
    when every family's point estimate agrees, ``family-dependent`` otherwise;
    ``no difference`` when the two arms took identical episodes everywhere
    (a zero effect with a zero-width CI in every family). A value without a CI
    is never certified (:func:`_ci_only`)."""

    if not values:
        return "not tested"
    values = _ci_only(values)
    if all(v.get("value") == 0 and list(v.get("ci95") or [None, None]) == [0, 0] for v in values):
        return "no difference"
    if all(v.get("certified") for v in values):
        return "supported"
    if all(v.get("holds") for v in values):
        return "directional"
    if not any(v.get("holds") for v in values):
        return "contradicted"
    return "family-dependent"


def _regime(block: Mapping[str, Any], consistency: str, repair: float) -> Mapping[str, Any] | None:
    for cell in block.get("regimes", []):
        if cell["consistency"] == consistency and float(cell["repair_minutes"]) == float(repair):
            return cell
    return None


def _signed(pair: Mapping[str, Any], sign: int, **extra: Any) -> dict[str, Any]:
    mean, (lo, hi) = pair["mean_difference"], pair["ci95"]
    return {
        **extra,
        "value": mean,
        "ci95": [lo, hi],
        "holds": (mean > 0) if sign > 0 else (mean < 0),
        "certified": (lo > 0) if sign > 0 else (hi < 0),
    }


def _pair_claim(report: Mapping[str, Any], families: Sequence[str], consistency: str, repair: float, key: str,
                sign: int, *, seed: int = 0, draws: int = 400) -> list[dict[str, Any]]:
    """``key`` = ``right-left``: the paired difference right - left should have
    sign ``sign`` (+1: right costs more minutes), computed from the stored
    per-learner episodes of each family's own-system cell."""

    right, left = key.split("-", 1)
    out = []
    for name in families:
        cell = _regime(report["families"][name], consistency, repair)
        if cell is None:
            continue
        pair = _paired(cell["episodes"], left, right, seed=seed, draws=draws)
        if pair is not None:
            out.append(_signed(pair, sign, family=name, regime=f"{consistency}/{repair:g}"))
    return out


def _rotation_claim(report: Mapping[str, Any], families: Sequence[str], key: str, sign: int, *, seed: int,
                    draws: int) -> list[dict[str, Any]]:
    """The same paired difference when the system is calibrated to another family
    (every truth x system pair, every rotation regime, and the main comparison)."""

    right, left = key.split("-", 1)
    out = []
    for name in families:
        block = report["families"][name]
        main = block.get("main", {})
        # In the study's family order, not the stored dict's (a stored report's keys come back sorted).
        cells = [(f"fitted/3 system={system}", main[system]) for system in families
                 if system in main and system != name]
        cells += [(f"{c['consistency']}/{float(c['repair_minutes']):g} system={c['system']}", c)
                  for c in block.get("rotation", []) if c.get("system") in families and c.get("system") != name]
        for where, cell in cells:
            pair = _paired(cell["episodes"], left, right, seed=seed, draws=draws)
            if pair is not None:
                out.append(_signed(pair, sign, family=name, regime=where))
    return out


def _kendall_tau(left: Mapping[str, float], right: Mapping[str, float]) -> float | None:
    """Kendall's tau-b between two families' mean minutes over their common policies."""

    keys = sorted(set(left) & set(right))
    concordant = discordant = ties_left = ties_right = 0
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            x = float(np.sign(left[a] - left[b]))
            y = float(np.sign(right[a] - right[b]))
            if x == 0 and y == 0:
                continue
            if x == 0:
                ties_left += 1
            elif y == 0:
                ties_right += 1
            elif x == y:
                concordant += 1
            else:
                discordant += 1
    denominator = math.sqrt((concordant + discordant + ties_left) * (concordant + discordant + ties_right))
    return None if denominator == 0 else (concordant - discordant) / denominator


def _winners(report: Mapping[str, Any], families: Sequence[str], *, seed: int, draws: int) -> list[dict[str, Any]]:
    """Per regime: each family's winner, co-winners (not distinguishable from the
    best), top-1 agreement and the regret of acting on another family's winner."""

    rows = []
    # Every regime any voting family ran, in the order they were run (a family
    # missing one is reported, never silently left out of the row).
    regimes: list[tuple[str, float]] = []
    for name in families:
        for cell0 in report["families"][name].get("regimes", []):
            regime = (cell0["consistency"], float(cell0["repair_minutes"]))
            if regime not in regimes:
                regimes.append(regime)
    for consistency, repair in regimes:
        per_family = {}
        for name in families:
            cell = _regime(report["families"][name], consistency, repair)
            if cell is None:
                continue
            policies = cell["episodes"]["policies"]
            means = {p: float(np.mean(v["total"])) for p, v in policies.items()}
            best = min(means, key=lambda p: (means[p], p))
            co = []
            for p in sorted(means):
                if p == best:
                    co.append(p)
                    continue
                pair = _paired(cell["episodes"], best, p, seed=seed, draws=draws)
                if pair is not None and pair["ci95"][0] <= 0.0:
                    co.append(p)
            ranked = sorted(means, key=lambda p: (means[p], p))
            runner = ranked[1] if len(ranked) > 1 else None
            margin = _paired(cell["episodes"], best, runner, seed=seed, draws=draws) if runner else None
            per_family[name] = {"winner": best, "mean": round(means[best], 4), "co_winners": co,
                                "runner_up": runner, "margin_over_runner_up": margin,
                                "means": {p: round(v, 4) for p, v in sorted(means.items())}}
        missing = [name for name in families if name not in per_family]
        winners = [v["winner"] for v in per_family.values()]
        top = max((winners.count(w) for w in winners), default=0)
        # Ties are listed, and the first in name order is the reported mode, so
        # the analysis does not depend on set iteration order.
        modal_tied = sorted({w for w in winners if winners.count(w) == top})
        modal = modal_tied[0] if modal_tied else None
        common = set.intersection(*(set(v["co_winners"]) for v in per_family.values())) if per_family else set()
        regret = {}
        for truth_name, truth in per_family.items():
            regret[truth_name] = {
                source: round(truth["means"][per_family[source]["winner"]] - truth["mean"], 4)
                for source in per_family
            }
        taus = [
            _kendall_tau(per_family[a]["means"], per_family[b]["means"])
            for i, a in enumerate(sorted(per_family))
            for b in sorted(per_family)[i + 1:]
        ]
        taus = [t for t in taus if t is not None]
        rows.append({
            "regime": f"{consistency}/{repair:g}",
            #: Every voting family has this regime; else the row is not evidence.
            "complete": not missing,
            "missing": missing,
            "per_family": per_family,
            "modal_winner": modal,
            "modal_tied": modal_tied,
            "top1_agreement": f"{winners.count(modal)}/{len(winners)}" if modal else "0/0",
            "ranking_kendall_tau": {
                "mean": round(float(np.mean(taus)), 4) if taus else None,
                "min": round(float(np.min(taus)), 4) if taus else None,
                "pairs": len(taus),
            },
            "common_co_winners": sorted(common),
            "regret_of_other_family_winner": regret,
            "max_regret": max((v for r in regret.values() for v in r.values()), default=0.0),
        })
    return rows


#: A policy within this many minutes per episode of a cell's best counts as best there.
NEAR_BEST_MINUTES = 0.10


def _policy_regret(report: Mapping[str, Any], families: Sequence[str], stress: Sequence[str],
                   expected_regimes: Sequence[str] | None = None) -> list[dict[str, Any]]:
    """RankCert's robust choice: each policy's regret (its mean minutes minus the
    best policy's) in every family x regime cell, worst case first. A policy
    that is never far from the best whichever family is true is the one to
    ship when the families disagree about the winner. A policy missing from
    any voting family x expected regime cell is ``complete: false`` and ranks
    after every complete one (its worst case is unknown)."""

    regrets: dict[str, dict[str, list[tuple[float, str]]]] = {}
    for name in list(families) + list(stress):
        for cell in report["families"][name].get("regimes", []):
            means = {p: float(np.mean(v["total"])) for p, v in cell["episodes"]["policies"].items()}
            if not means:
                continue
            best = min(means.values())
            where = f"{cell['consistency']}/{float(cell['repair_minutes']):g}"
            for policy, mean in means.items():
                regrets.setdefault(policy, {}).setdefault(name, []).append((mean - best, where))
    rows = []
    for policy, by_family in regrets.items():
        fitted = [(value, f"{name} {where}") for name in families for value, where in by_family.get(name, [])]
        if not fitted:
            continue
        worst = max(fitted)
        stressed = [(value, f"{name} {where}") for name in stress for value, where in by_family.get(name, [])]
        covered = {(name, where) for name in families for _value, where in by_family.get(name, [])}
        regimes = expected_regimes if expected_regimes is not None else sorted({w for _n, w in covered})
        missing_cells = [f"{name} {where}" for name in families for where in regimes if (name, where) not in covered]
        rows.append({
            "policy": policy,
            "complete": not missing_cells,
            "missing_cells": missing_cells,
            "max_regret": round(worst[0], 4),
            "max_regret_cell": worst[1],
            "mean_regret": round(float(np.mean([v for v, _ in fitted])), 4),
            "cells_near_best": f"{sum(1 for v, _ in fitted if v <= NEAR_BEST_MINUTES)}/{len(fitted)}",
            "max_regret_by_family": {name: round(max(v for v, _ in by_family[name]), 4)
                                     for name in families if by_family.get(name)},
            "stress_max_regret": round(max(stressed)[0], 4) if stressed else None,
            "stress_max_regret_cell": max(stressed)[1] if stressed else None,
        })
    rows.sort(key=lambda row: (not row["complete"], row["max_regret"], row["mean_regret"], row["policy"]))
    return rows


def _per_check_log_loss(arm: Mapping[str, Any], picks: np.ndarray) -> np.ndarray:
    """A stream arm's log loss per check under each bootstrap resample of its
    episodes: a ratio of sums over the arm's OWN checks (two arms stop after
    different numbers of checks, so one arm's count never divides the other's
    loss). ``picks`` (draws x episodes) is shared by the arms being compared."""

    loss = np.asarray(arm["per_episode_log_loss"], dtype=float)[picks].sum(axis=1)
    checks = np.asarray(arm["per_episode_checks"], dtype=float)[picks].sum(axis=1)
    return loss / np.maximum(checks, 1.0)


def analyze(report: Mapping[str, Any], *, seed: int | None = None, draws: int | None = None) -> dict[str, Any]:
    settings = report["settings"]
    seed = settings["seed"] if seed is None else seed
    draws = settings["bootstrap"] if draws is None else draws
    # The study's own family order (a stored report's keys come back sorted).
    order = list(settings.get("families") or []) + list(settings.get("stress_families") or [])
    names = [n for n in order if n in report["families"]] + sorted(n for n in report["families"] if n not in order)
    fitted = [n for n in names if report["families"][n].get("fitted")]
    stress = [n for n in names if not report["families"][n].get("fitted")]
    # Review F2: only families that pass the adequacy gate vote; a claim must
    # cover every voting family (and cell), else it is insufficient evidence.
    families, excluded = _voting_families(report, fitted)
    enough = len(families) >= MIN_VOTING_FAMILIES
    claims: list[dict[str, Any]] = []

    def finish(claim_id: str, statement: str, values: list[dict[str, Any]], *, expected: Sequence[Any],
               key: Callable[[Mapping[str, Any]], Any], stress_values=None, note: str = "") -> None:
        values = _ci_only(values)
        present = {key(v) for v in values}
        missing = [k for k in expected if k not in present]
        verdict = _verdict(values)
        if not enough or (values and missing):
            # Fewer voting families than RankCert needs, or a voting family
            # without the claim's cell ("not tested": no family ran it).
            verdict = INSUFFICIENT
        claims.append({
            "id": claim_id,
            "statement": statement,
            "verdict": verdict,
            "families_holding": f"{sum(1 for v in values if v['holds'])}/{len(values)}",
            "families_certified": f"{sum(1 for v in values if v['certified'])}/{len(values)}",
            "missing": [k if isinstance(k, str) else " ".join(str(x) for x in k) for k in missing],
            "values": values,
            "stress": _ci_only(stress_values or []),
            "note": note,
        })

    def add(claim_id: str, statement: str, values: list[dict[str, Any]], *, stress_values=None, note: str = "") -> None:
        finish(claim_id, statement, values, expected=families, key=lambda v: v["family"],
               stress_values=stress_values, note=note)

    # C1: the vocabulary is overconfident relative to every family's consistency.
    hand = report["hand_set_implied"]["consistency"]["contrast_card_dominant_normalized"]
    values = []
    for name in families:
        implied = (report["families"][name].get("implied") or {}).get("fitted") or {}
        c = implied.get("consistency")
        if c is None:
            continue
        ci = implied.get("consistency_ci95")
        values.append({"family": name, "value": c, "ci95": ci, "holds": c < hand,
                       "certified": _has_ci({"ci95": ci}) and ci[1] < hand})
    add("C1a", f"the hand-set card implies consistency {hand}; every family's fitted consistency is lower",
        values, note="certified when the 95% CI of the family's bank-mean consistency (subjects resampled) is below "
                     "the card's; a report without that CI holds at most directionally")

    # C1b: hand-set checks realize no information about the truth; calibrated ones do.
    for policy in ("incumbent", "caps_only"):
        values, calibrated = [], []
        for name in families + stress:
            main = report["families"][name].get("main") or {}
            info = (((main.get(SYSTEM_HAND_SET) or {}).get("policies") or {}).get(policy) or {}).get("information")
            if info is None:
                continue
            gain, ci = info.get("mean_truth_log_gain"), info.get("truth_log_gain_ci95") or [None, None]
            entry = {"family": name, "value": gain, "ci95": ci,
                     "holds": gain is not None and gain <= 0.0,
                     "certified": ci[1] is not None and ci[1] < 0.0}
            (values if name in families else calibrated).append(entry)
        add(f"C1b:{policy}", f"under the hand-set vocabulary, {policy}'s checks realize no information "
            "about the truth (mean log gain <= 0; certified when the CI is below 0)", values, stress_values=calibrated)
    values = []
    for name in families:
        main = report["families"][name].get("main") or {}
        info = (((main.get(SYSTEM_FAMILY) or {}).get("policies") or {}).get("incumbent") or {}).get("information")
        if info is None:
            continue
        gain, ci = info.get("mean_truth_log_gain"), info.get("truth_log_gain_ci95") or [None, None]
        values.append({"family": name, "value": gain, "ci95": ci, "holds": gain is not None and gain > 0,
                       "certified": ci[0] is not None and ci[0] > 0})
    add("C1c", "under the family's calibrated model, incumbent's checks realize positive information about the truth",
        values)

    def pair(group: Sequence[str], consistency: str, repair: float, key: str, sign: int) -> list[dict[str, Any]]:
        return _pair_claim(report, group, consistency, repair, key, sign, seed=seed, draws=draws)

    def paired_claim(claim_id: str, statement: str, consistency: str, repair: float, key: str, sign: int) -> None:
        add(claim_id, statement, pair(families, consistency, repair, key, sign),
            stress_values=pair(stress, consistency, repair, key, sign))

    # C7: at the fitted strength, value rules beat the incumbent (one check is rarely worth a minute).
    for repair in (3.0, 10.0, 30.0):
        paired_claim(f"C7:{repair:g}", f"fitted strength, repair {repair:g}: evsi as built costs fewer minutes "
                     "than the incumbent", "fitted", repair, "evsi-incumbent", -1)
    # C2: strong checks, high stakes: EVSI as built under-probes.
    paired_claim("C2a", "0.9/30: evsi as built costs more minutes than the incumbent (it under-probes)",
                 "0.9", 30.0, "evsi-incumbent", +1)
    for consistency, repair in (("0.9", 30.0), ("0.9", 10.0), ("0.7", 30.0)):
        regime = f"{consistency}/{repair:g}"
        paired_claim(f"C2b:{regime}", f"{regime}: the flip abstention costs minutes (evsi - evsi_lcb_only > 0)",
                     consistency, repair, "evsi-evsi_lcb_only", +1)
        paired_claim(f"C2c:{regime}", f"{regime}: the 2-3 check lookahead saves minutes over the one-step rule "
                     "without abstention (evsi_lookahead - evsi_lcb_only < 0)",
                     consistency, repair, "evsi_lookahead-evsi_lcb_only", -1)
        paired_claim(f"C2d:{regime}", f"{regime}: the lookahead beats the incumbent",
                     consistency, repair, "evsi_lookahead-incumbent", -1)
        paired_claim(f"C2e:{regime}", f"{regime}: the lookahead beats caps_only (the same caps without the gate)",
                     consistency, repair, "evsi_lookahead-caps_only", -1)
    for consistency, repair in (("0.9", 30.0), ("0.9", 10.0), ("0.7", 30.0)):
        regime = f"{consistency}/{repair:g}"
        paired_claim(f"C3:{regime}", f"{regime}: today's robust completion gate costs minutes "
                     "(incumbent - caps_only > 0)", consistency, repair, "incumbent-caps_only", +1)
    paired_claim("C3w:fitted/3", "fitted/3: where checks are weak the robust completion gate saves minutes "
                 "(incumbent - caps_only < 0)", "fitted", 3.0, "incumbent-caps_only", -1)
    paired_claim("C8:0.9/30", "0.9/30: the EIG path's agreement gate costs minutes (eig - eig_no_gate > 0)",
                 "0.9", 30.0, "eig-eig_no_gate", +1)
    paired_claim("C8w:fitted/3", "fitted/3: the agreement gate saves minutes because the nat-scaled rule "
                 "over-measures (eig - eig_no_gate < 0)", "fitted", 3.0, "eig-eig_no_gate", -1)

    # S: the successor as built, and the proposed package, against today's incumbent.
    for consistency, repair in (("fitted", 3.0), ("fitted", 30.0), ("0.7", 30.0), ("0.9", 10.0), ("0.9", 30.0)):
        regime = f"{consistency}/{repair:g}"
        paired_claim(f"S1:{regime}", f"{regime}: the successor as built (voi_successor) costs no more minutes than "
                     "the incumbent (voi_successor - incumbent < 0)", consistency, repair,
                     "voi_successor-incumbent", -1)
        paired_claim(f"S2:{regime}", f"{regime}: the proposed package (voi_proposed) costs fewer minutes than the "
                     "successor as built (voi_proposed - voi_successor < 0)", consistency, repair,
                     "voi_proposed-voi_successor", -1)
        paired_claim(f"S3:{regime}", f"{regime}: the proposed package costs fewer minutes than the incumbent",
                     consistency, repair, "voi_proposed-incumbent", -1)
        # S4 isolates the stability stops: voi_p_top_value and evsi_lookahead
        # differ only by them (both serve rank_feasible's top-ranked check).
        paired_claim(f"S4:{regime}", f"{regime}: keeping the stability stops (decision stable, action "
                     "equivalent) on top of the lookahead saves minutes (voi_p_top_value - evsi_lookahead < 0)",
                     consistency, repair, "voi_p_top_value-evsi_lookahead", -1)
        # Leave-one-out: each piece of the successor as built, put back into the package.
        paired_claim(f"A1:{regime}", f"{regime}: inside the package, today's robust completion gate costs minutes "
                     "(voi_p_with_gate - voi_proposed > 0)", consistency, repair, "voi_p_with_gate-voi_proposed", +1)
        paired_claim(f"A2:{regime}", f"{regime}: inside the package, handing a flip abstention to the nat-scaled "
                     "EIG costs minutes (voi_p_with_fallback - voi_proposed > 0)", consistency, repair,
                     "voi_p_with_fallback-voi_proposed", +1)
        paired_claim(f"A3:{regime}", f"{regime}: inside the package, the 2-3 check lookahead saves minutes "
                     "(voi_proposed - voi_p_one_step < 0)", consistency, repair, "voi_proposed-voi_p_one_step", -1)
        # The successor with only the gate dropped and the lookahead added (its
        # flip-abstention handling and serving kept): what A2 leaves standing.
        paired_claim(f"S5:{regime}", f"{regime}: the successor with the robust completion gate dropped and the "
                     "lookahead added, its abstention handling kept (voi_p_with_fallback), costs fewer minutes "
                     "than the successor as built (voi_p_with_fallback - voi_successor < 0)", consistency, repair,
                     "voi_p_with_fallback-voi_successor", -1)
        paired_claim(f"S6:{regime}", f"{regime}: voi_p_with_fallback costs fewer minutes than the incumbent",
                     consistency, repair, "voi_p_with_fallback-incumbent", -1)
        # Review F1: the serving rule, ablated on its own.
        paired_claim(f"A4:{regime}", f"{regime}: inside the package, serving rank_feasible's top-ranked paying "
                     "check instead of the successor's choice (the highest-EIG check when it pays) saves minutes "
                     "(voi_p_top_value - voi_proposed < 0)", consistency, repair, "voi_p_top_value-voi_proposed", -1)

    # C4b: loss-derived EVSI (no nat scale) against the nat-scaled EIG rule, both without abstention.
    for consistency, repair in (("fitted", 3.0), ("fitted", 30.0), ("0.9", 10.0), ("0.9", 30.0)):
        regime = f"{consistency}/{repair:g}"
        paired_claim(f"C4b:{regime}", f"{regime}: loss-derived EVSI costs fewer minutes than the EIG rule with "
                     "VALUE_PER_NAT_MINUTES = 60 (evsi_lcb_only - eig_no_gate < 0)",
                     consistency, repair, "evsi_lcb_only-eig_no_gate", -1)

    # Rotation: the policy conclusions when the system is calibrated to the wrong
    # family, one claim per regime (a claim about strong checks is not expected
    # to hold where checks are weak, so the regimes are never pooled).
    for key, sign, statement in (
        ("evsi_lookahead-incumbent", -1, "the lookahead beats the incumbent"),
        ("evsi-evsi_lcb_only", +1, "the flip abstention costs minutes"),
        ("incumbent-caps_only", +1, "the robust completion gate costs minutes"),
        ("evsi-incumbent", +1, "evsi as built costs more than the incumbent"),
        ("voi_proposed-voi_successor", -1, "the proposed package beats the successor as built"),
        ("voi_p_with_fallback-voi_successor", -1, "the gate dropped and the lookahead added beat the successor as built"),
    ):
        by_regime: dict[str, list[dict[str, Any]]] = {}
        for value in _rotation_claim(report, families, key, sign, seed=seed, draws=draws):
            regime, _, system = value["regime"].partition(" system=")
            by_regime.setdefault(regime, []).append({**value, "regime": regime, "system": system})
        rotation_cells = [(truth, system) for truth in families for system in families if system != truth]
        for regime, values in by_regime.items():
            finish(f"R:{key}@{regime}",
                   f"{regime}, system calibrated to another family: {statement} ({key}, sign {sign:+d})",
                   values, expected=rotation_cells, key=lambda v: (v["family"], v["system"]),
                   note="counts are cells: every truth family x every other family's calibrated system")

    # C4: VALUE_PER_NAT_MINUTES = 60 is far too high (measured minutes per nat, calibrated model).
    values = []
    for name in families:
        measured = []
        if not report["families"][name].get("regimes"):
            continue
        for cell in report["families"][name]["regimes"]:
            for policy in ("incumbent", "caps_only"):
                v = cell["policies"].get(policy, {}).get("value_of_checks", {})
                if v.get("minutes_per_nat") is not None:
                    measured.append((v["minutes_per_nat"], v.get("minutes_per_nat_ci95"), cell["consistency"],
                                     cell["repair_minutes"], policy))
        top = max(measured, key=lambda m: m[0]) if measured else None
        values.append({
            "family": name,
            "value": top[0] if top else None,
            "ci95": top[1] if top else None,
            "where": f"{top[2]}/{top[3]:g} ({top[4]})" if top else None,
            "ratio_60_over_max": round(60.0 / top[0], 2) if top and top[0] > 0 else None,
            "holds": bool(top and top[0] < 60.0),
            "certified": bool(top and top[1] and top[1][1] is not None and top[1][1] < 60.0 / 4.0),
        })
    add("C4", "VALUE_PER_NAT_MINUTES = 60 is above every measured minutes-per-nat (certified: 60 is >= 4x the "
        "largest measured value's upper CI)", values)

    # C5: Part C pays off once the unresolved cost is large; costs nothing measurable below.
    values = []
    for name in families:
        if not (report["families"][name].get("part_c") or {}).get("rows"):
            continue
        rows = [r for r in report["families"][name]["part_c"]["rows"] if r["consistency"] == str(0.9)]
        pays = sorted({r["true_unresolved_minutes"] for r in rows if r["difference"].get("ci95")
                       and r["difference"]["ci95"][1] < 0})
        hurts = [r for r in rows if r["difference"].get("ci95") and r["difference"]["ci95"][0] > 0]
        largest = max((r for r in rows if r["policy"] == "evsi_lookahead"), key=lambda r: r["true_unresolved_minutes"],
                      default=None)
        values.append({
            "family": name,
            "value": pays[0] if pays else None,
            "ci95": largest["difference"].get("ci95") if largest else None,
            "never_hurts": not hurts,
            "holds": bool(pays) and not hurts,
            "certified": bool(pays) and not hurts and pays[0] <= 3.7,
        })
    add("C5", "0.9: charging the measured unresolved cost saves minutes once it is about 3.6 minutes or more, and "
        "never costs minutes (value: the smallest U with a CI below 0)", values)

    # C6: robustness knobs.
    values = []
    for name in families:
        q10 = []
        if not report["families"][name].get("regimes"):
            continue
        for cell in report["families"][name]["regimes"]:
            v = cell["policies"].get("caps_only", {}).get("value_of_checks", {})
            bias = v.get("member_quantile_minus_realized") or {}
            realized = v.get("mean_realized_value")
            if realized is not None and realized > 0.05 and "q10" in bias:
                q10.append((bias["q10"], bias.get("q25"), bias.get("q50"), cell["consistency"], cell["repair_minutes"]))
        under = [b for b in q10 if b[0] < 0]
        closer = [b for b in q10 if b[1] is not None and abs(b[1]) < abs(b[0])]
        values.append({"family": name, "value": f"{len(under)}/{len(q10)} under; q25 closer {len(closer)}/{len(q10)}",
                       "ci95": None, "holds": bool(q10) and len(under) == len(q10),
                       "certified": bool(q10) and len(under) == len(q10) and len(closer) == len(q10),
                       "cells": [{"regime": f"{b[3]}/{b[4]:g}", "q10": b[0], "q25": b[1], "q50": b[2]} for b in q10]})
    add("C6a", "ROBUST_QUANTILE 0.10 under-predicts the realized value of checks wherever checks have value, and "
        "the 25th percentile is closer (caps_only's checks)", values)
    for sweep, field_name, recommended, policy in (
        ("robust_composition.ROBUST_QUANTILE", "robust_quantile", 0.25, "evsi_lookahead"),
        ("evsi.PERTURBATION_DELTA", "perturbation_delta", 0.10, "evsi"),
        ("robust_composition.BURDEN_COST", "burden_cost", 0.5, "evsi_lookahead"),
        ("action_loss.DEFAULT_INTERVENTION_MINUTES (repair minutes)", "repair_minutes", 10.0, "evsi_lookahead"),
        ("robust_composition.VALUE_PER_NAT_MINUTES", "value_per_nat_minutes", 10.0, "eig_no_gate"),
        ("robust_composition.INSTRUMENT_PERTURBATION_CONCENTRATION", "instrument_concentration", 4.0, "evsi_lookahead"),
    ):
        values = []
        for name in families:
            parameter = report["families"][name].get("sensitivity", {}).get("parameters", {}).get(sweep)
            if not parameter:
                continue
            row = next((r for r in parameter["rows"] if float(r["value"]) == float(recommended)), None)
            if row is None or policy not in row["policies"]:
                continue
            diff = row["policies"][policy]["difference_vs_current"]
            mean, ci = diff.get("mean_difference"), diff.get("ci95") or [None, None]
            best = min(parameter["rows"], key=lambda r: r["policies"].get(policy, {}).get("mean_total_minutes", 1e9))
            values.append({"family": name, "value": mean, "ci95": ci,
                           "best_in_sweep": best["value"],
                           "holds": mean is not None and mean <= 0.0,
                           "certified": ci[1] is not None and ci[1] < 0.0,
                           "harmful": ci[0] is not None and ci[0] > 0.0})
        add(f"C6:{field_name}={recommended:g}", f"{sweep} = {recommended:g} (vs current) does not cost minutes for "
            f"{policy} at 0.9/10 (certified when it saves minutes with a CI below 0)", values)

    # C6c: pseudo count 8 -> 2.
    values = []
    regime_order = [f"{_label(s)}/{float(r):g}" for s, r in settings.get("pseudo_count_regimes") or []]
    for name in families:
        streams = report.get("pseudo_count", {}).get("streams", {}).get(name, {})
        ordered = [r for r in regime_order if r in streams] + sorted(r for r in streams if r not in regime_order)
        for regime in ordered:
            arms = streams[regime]
            two, eight = arms.get("pseudo_2"), arms.get("pseudo_8")
            if not two or not eight:
                continue
            diff = np.asarray(two["per_episode_total"]) - np.asarray(eight["per_episode_total"])
            rng = np.random.default_rng(seed)
            picks = rng.integers(0, diff.size, size=(draws, diff.size))
            boots = diff[picks].mean(axis=1)
            boots_ll = _per_check_log_loss(two, picks) - _per_check_log_loss(eight, picks)
            values.append({
                "family": name, "regime": regime,
                "value": round(float(diff.mean()), 4),
                "ci95": [round(float(np.quantile(boots, 0.025)), 4), round(float(np.quantile(boots, 0.975)), 4)],
                "log_loss_2": two["log_loss"], "log_loss_8": eight["log_loss"],
                "log_loss_difference_ci95": [round(float(np.quantile(boots_ll, 0.025)), 4),
                                             round(float(np.quantile(boots_ll, 0.975)), 4)],
                "holds": two["log_loss"] is not None and eight["log_loss"] is not None
                and two["log_loss"] <= eight["log_loss"],
                "certified": float(np.quantile(boots_ll, 0.975)) < 0.0,
            })
    finish("C6c", "DEFAULT_CONDITIONAL_PSEUDO_COUNT 2 forecasts answers better than 8 over a stream that starts "
           "from the hand-set vocabulary (value: minutes per episode, 2 - 8; certified on log loss)", values,
           expected=[(name, regime) for name in families for regime in regime_order],
           key=lambda v: (v["family"], v["regime"]))

    winners = _winners(report, families, seed=seed, draws=draws) if families else []
    expected_regimes = [f"{_label(c)}/{float(r):g}" for c in settings.get("strengths") or []
                        for r in settings.get("repairs") or []] or None
    return {"families": families, "stress_families": stress, "excluded_families": excluded,
            "minimum_voting_families": MIN_VOTING_FAMILIES, "enough_families": enough,
            "claims": claims, "winners": winners,
            "policy_regret": _policy_regret(report, families, stress, expected_regimes) if families else []}


__all__ = ["MultiFamilySettings", "analyze", "counted_row", "run_count_stream", "run_multifamily"]
