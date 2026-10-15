"""How often the four former count caps bound, and what value of information does instead.

Run on a backup-API copy of a vault (``learnloop.db.copies.copy_tree_with_databases``)
under ``fixtures-local/``; the script refuses any other path. It upgrades the
copy to the value-of-information successor if it is below it (through the
chain), then reports, per site:

* **history**: how often the former cap bound in the copy's recorded sessions
  (qualifying probe observations per session past
  ``probe.episode.session_qualifying_observation_cap``; follow-ups suppressed
  ``session_cap_reached``; teach-back attempts per session past
  ``teach_back.session_cap``), and, for each follow-up the cap suppressed, what
  value decides on the copy's current state (``later``: value would queue it;
  ``agree``: value stops too);
* **now**: one Today build in a fresh session at the successor (each site's
  value decisions and how they compare with the cap: ``earlier`` value stops
  where the cap would not, ``later`` value continues past it), and the build's
  wall time with the four sites on and off.

No model call, no network, no write outside the copy.

    uv run python scripts/voi_cap_report.py --vault fixtures-local/voi-copies/linear_algebra [--json]
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any


def _refuse_unless_copy(root: Path) -> None:
    resolved = root.resolve()
    if "fixtures-local" not in resolved.parts:
        sys.exit(f"refusing {resolved}: run this on a backup-API copy under fixtures-local/")


def _upgrade(root: Path) -> list[str]:
    from learnloop.algorithm_versions import (
        P0_ALGORITHM_VERSION,
        REVEAL_LEDGER_ALGORITHM_VERSION,
        VOI_STOPPING_ALGORITHM_VERSION,
    )
    from learnloop.ops.vault_upgrade import upgrade_to_mvp09
    from learnloop.vault.loader import load_vault
    from learnloop.voi_stopping_upgrade import upgrade_to_mvp021

    steps: list[str] = []
    version = load_vault(root).config.algorithms.algorithm_version
    if version == P0_ALGORITHM_VERSION:
        result = upgrade_to_mvp09(root)
        if not result.upgraded:
            sys.exit(f"mvp-0.9 step refused: {result.problems}")
        steps.append(f"{result.from_version} -> {result.to_version}")
        version = REVEAL_LEDGER_ALGORITHM_VERSION
    if version != VOI_STOPPING_ALGORITHM_VERSION:
        result = upgrade_to_mvp021(root)
        if not result.upgraded:
            sys.exit(f"upgrade refused: {result.problems}")
        steps.append(f"{result.from_version} -> {result.to_version}")
        steps.extend(f"note: {note}" for note in result.notes)
    return steps


def _history(vault: Any, repository: Any) -> dict[str, Any]:
    config = vault.config
    from learnloop.held_grades import held_for_review_attempts

    with repository.connection() as connection:
        connection.row_factory = sqlite3.Row
        observed = connection.execute(
            "SELECT a.session_id AS session_id, o.attempt_id AS attempt_id FROM probe_observations o "
            "JOIN practice_attempts a ON a.id = o.attempt_id "
            "WHERE o.eligible_for_completion = 1 AND a.session_id IS NOT NULL"
        ).fetchall()
        # held-grade-evidence: an observation whose grade is held for review
        # qualifies nothing while it is held (THE predicate, as the session
        # cap itself counts: Repository.qualifying_probe_observation_count_for_session).
        held = held_for_review_attempts(connection, [row["attempt_id"] for row in observed]) if observed else frozenset()
        counts: dict[str, int] = {}
        for row in observed:
            if row["attempt_id"] not in held:
                counts[str(row["session_id"])] = counts.get(str(row["session_id"]), 0) + 1
        per_session = [{"session_id": session, "n": n} for session, n in sorted(counts.items())]
        teach_back = connection.execute(
            "SELECT session_id, COUNT(*) AS n FROM practice_attempts "
            "WHERE practice_mode = 'teach_back' AND session_id IS NOT NULL GROUP BY session_id"
        ).fetchall()
        surprise = connection.execute(
            "SELECT s.attempt_id, s.triggered_actions_json, s.suppressed_actions_json, s.gate_diagnostics_json, "
            "a.learning_object_id, a.practice_item_id, a.session_id "
            "FROM attempt_surprise s JOIN practice_attempts a ON a.id = s.attempt_id"
        ).fetchall()
    probe_cap = int(config.probe.episode.session_qualifying_observation_cap)
    tb_cap = int(config.teach_back.session_cap)
    queued = sum(1 for row in surprise if "intervention_followup:queued:" in (row["triggered_actions_json"] or ""))
    capped = [row for row in surprise if "session_cap_reached" in (row["suppressed_actions_json"] or "")]
    return {
        "probe_episode": {
            "sessions_with_qualifying_observations": len(per_session),
            "qualifying_observations": sum(int(row["n"]) for row in per_session),
            "sessions_where_the_cap_bound": sum(1 for row in per_session if probe_cap > 0 and int(row["n"]) >= probe_cap),
        },
        "followup_intervention": {
            "followups_queued": queued,
            "suppressed_by_the_cap": len(capped),
            "capped": [dict(row) for row in capped],
        },
        "teach_back": {
            "sessions_with_teach_back_attempts": len(teach_back),
            "sessions_past_the_cap": sum(1 for row in teach_back if int(row["n"]) > tb_cap),
        },
        "project_probe": {
            "note": "no scheduled-check provider registers project probes on this base: the cap never applies",
        },
    }


def _revalue_capped_followups(vault: Any, repository: Any, capped: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """What value decides, on the copy's current state, for each further
    follow-up the former cap suppressed (the state has moved on since)."""

    from learnloop.diagnosis import followups as F
    from learnloop.diagnosis.voi_stopping import STOP

    out: list[dict[str, Any]] = []
    config = vault.config.scheduler.followup
    for row in capped:
        gate = json.loads(row["gate_diagnostics_json"] or "{}")
        reasons = list(gate.get("triggered_reasons") or gate.get("natural_trigger_reasons") or [])
        lo_id, item_id = str(row["learning_object_id"]), str(row["practice_item_id"])
        if lo_id not in vault.learning_objects:
            out.append({"attempt_id": row["attempt_id"], "result": "learning_object_gone"})
            continue
        intent = F._choose_intent(
            reasons, probe_phase_active=False, lo_independent_evidence_mass=float(config.cold_start_min_lo_evidence),
            cold_start_min_lo_evidence=float(config.cold_start_min_lo_evidence),
        )
        targets = F._canonical_target_facets(vault, F._attempt_target_facets(repository, item_id))
        selection = F._choose_intervention_item(
            vault, repository, attempt_id=str(row["attempt_id"]), learning_object_id=lo_id,
            exclude_practice_item_id=item_id, target_facets=targets, failed_facets=targets, intent=intent,
            max_error_severity=float(gate.get("max_error_severity") or 0.0),
        )
        if selection.candidate is None:
            out.append({"attempt_id": row["attempt_id"], "result": "no_candidate", "cap_comparison": "agree"})
            continue
        decision = F._intervention_value(
            vault, repository, selection=selection, learning_object_id=lo_id,
            session_interventions_for_lo=int(config.max_interventions_per_lo_per_session),
            session_id=row["session_id"], clock=None,
        )
        best = decision.chosen or decision.best
        out.append(
            {
                "attempt_id": row["attempt_id"],
                "learning_object_id": lo_id,
                "candidate": best.ref if best else None,
                "decision": decision.decision,
                "reason": decision.reason,
                "method": best.method if best else None,
                "value_robust_minutes": round(best.value_robust_minutes, 4) if best else None,
                "cost_minutes": round(best.cost_minutes, 4) if best else None,
                "decision_at_stake": decision.context.get("decision_at_stake"),
                "cap_comparison": "agree" if decision.decision == STOP else "later",
            }
        )
    return out


def _today(root: Path) -> dict[str, Any]:
    from learnloop.clock import SystemClock
    from learnloop.vault.repository import open_vault_repository
    from learnloop.scheduling.scheduler import OfferTrace, SchedulerSession, build_due_queue
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths

    def build(enabled: bool) -> tuple[OfferTrace, float, int]:
        vault = load_vault(root)
        vault.config.voi_stopping.enabled = enabled
        repository = open_vault_repository(vault.root, VaultPaths(vault.root, vault.config).sqlite_path)
        trace = OfferTrace()
        started = time.perf_counter()
        queue = build_due_queue(
            vault, repository, clock=SystemClock(), session=SchedulerSession(session_id="voi-report", available_minutes=30),
            persist_explanations=False, offer_trace=trace,
        )
        return trace, time.perf_counter() - started, len(queue)

    # Interleaved and repeated: the first build warms caches, so each side
    # reports its fastest of three.
    runs = {False: [], True: []}
    for _ in range(3):
        for enabled in (False, True):
            runs[enabled].append(build(enabled))
    off_trace, _, off_len = runs[False][-1]
    on_trace, _, on_len = runs[True][-1]
    off_seconds = min(run[1] for run in runs[False])
    on_seconds = min(run[1] for run in runs[True])
    by_site: dict[str, Counter] = {}
    for decision in on_trace.voi_decisions:
        counter = by_site.setdefault(decision["site"], Counter())
        counter[decision["decision"]] += 1
        counter[f"cap_{decision['cap_comparison']}"] += 1
        counter[f"method_{(decision.get('best') or {}).get('method')}"] += 1
    return {
        "queue_length": {"voi_off": off_len, "voi_on": on_len},
        "build_seconds": {"voi_off": round(off_seconds, 3), "voi_on": round(on_seconds, 3)},
        "decisions_by_site": {site: dict(counter) for site, counter in sorted(by_site.items())},
        "decisions": [
            {key: decision.get(key) for key in ("site", "learning_object_id", "decision", "reason", "cap_comparison", "former_cap")}
            | {
                # A per-candidate receipt (a teach-back) reports its own
                # valuation (``subject``); a site decision its best.
                "ref": (decision.get("subject") or decision.get("best") or {}).get("ref"),
                "value_robust_minutes": (decision.get("subject") or decision.get("best") or {}).get("evsi_robust_minutes"),
                "cost_minutes": (decision.get("subject") or decision.get("best") or {}).get("cost_minutes"),
                "method": (decision.get("subject") or decision.get("best") or {}).get("method"),
                "conditioning": ((decision.get("subject") or {}).get("detail") or {}).get("conditioning"),
                "subject_learning_object_id": ((decision.get("subject") or {}).get("detail") or {}).get(
                    "learning_object_id"
                ),
            }
            for decision in on_trace.voi_decisions
        ],
        "open_episodes_in_progress": None,
    }


def _simulate_probe_episodes(
    vault: Any, repository: Any, learners: int, seed: int = 20261013, *, robust: bool = False
) -> dict[str, Any]:
    """SYNTHETIC: how many observations value asks for in one episode.

    One episode over the cold-start labels a contrast card models (the
    production ``contrast_confusable`` card with its default rows, the
    grader channel composed in, the card's 45-second median), the copy's own
    triage routes and duration evidence, a fresh instrument every step. A
    simulated learner's true hypothesis is drawn from the prior and each
    answer from that hypothesis's row; the posterior updates by Bayes. Value
    stops when the next observation no longer pays for its minutes. The
    episode's own completion rules (``decision_stable``: top posterior at
    ``posterior_stop_threshold`` and runner-up ratio at ``ambiguity_threshold``;
    ``probe.episode.maximum_observations``) are reported beside it.

    ``robust``: value each step over the episode's credible set, the
    composition ensemble on the copy's resolved calibration channel (member 0
    plus 128 draws, as a pinned episode is valued), instead of the point
    conditionals. Answers are then drawn from the ensemble's mean member.
    """

    import random

    from learnloop.diagnosis import voi_stopping as voi
    from learnloop.diagnosis.probe_families import (
        CONTRAST_CONFUSABLE_DEFAULT_ROWS,
        CONTRAST_CONFUSABLE_V1,
        InstrumentCard,
        instrument_conditionals,
        map_episode_labels_to_slots,
        validate_and_compile_card,
    )

    card = InstrumentCard(
        id="synthetic_contrast", version=1, family_template_id=CONTRAST_CONFUSABLE_V1.id,
        family_template_version=CONTRAST_CONFUSABLE_V1.version, learning_object_id="lo_synthetic",
        target_decision="choose_schema_vs_confusable_repair",
        bindings={"target_facet": "recall", "confusable_concept": "neighbour"},
        hypotheses=CONTRAST_CONFUSABLE_V1.hypothesis_slots,
        conditional_observations=CONTRAST_CONFUSABLE_DEFAULT_ROWS,
        target_facets=("recall",), signature_error_types={"confusable_signature": ["conceptual_slip"]},
    )
    instrument = validate_and_compile_card(card, CONTRAST_CONFUSABLE_V1)
    prior = {
        "robust_initial_grasp": 0.30, "confuses_with:neighbour": 0.20, "surface_only": 0.20,
        "unfamiliar": 0.20, "other_or_unknown": 0.10,
    }
    slot_map = map_episode_labels_to_slots(instrument, list(prior), bindings=card.bindings) or {}
    member = voi.label_conditionals(instrument_conditionals(instrument), slot_map, prior)
    channel = None
    if robust:
        from learnloop.diagnosis.probe_robust import instrument_ensemble, resolve_episode_channel

        channel = resolve_episode_channel(repository, learning_object_id="lo_synthetic")
    minutes = voi.MinutesEstimate(float(instrument.expected_seconds) / 60.0, "authored_prior")
    episode = vault.config.probe.episode
    context = voi.VoiContext(vault, repository)
    rng = random.Random(seed)
    value_stops: Counter = Counter()
    stable_at: Counter = Counter()
    methods: Counter = Counter()
    for _ in range(learners):
        truth = rng.choices(list(prior), weights=list(prior.values()))[0]
        belief = dict(prior)
        stable = None
        for step in range(13):
            ordered = sorted(belief.values(), reverse=True)
            if stable is None and ordered[0] >= episode.posterior_stop_threshold and (
                ordered[0] <= 0 or ordered[1] / ordered[0] <= episode.ambiguity_threshold
            ):
                stable = step
            members: tuple = (member,)
            if channel is not None:
                ensemble, _dch = instrument_ensemble(channel, instrument, slot_map, belief, episode_id="synthetic")
                members = tuple(ensemble.members)
                if step == 0:
                    member = members[0]
            decision = voi.value_candidates(
                context, voi.SITE_PROBE_EPISODE, [voi.Candidate(ref="next", minutes=minutes, members=members)],
                prior=belief, learning_object_id="lo_synthetic",
                former_cap=voi.former_cap(voi.SITE_PROBE_EPISODE, value=4, count=step),
            )
            methods[decision.best.method] += 1
            if decision.decision == voi.STOP or step == 12:
                value_stops[step] += 1
                break
            outcomes = list(member[truth])
            outcome = rng.choices(outcomes, weights=[member[truth][o] for o in outcomes])[0]
            raw = {label: belief[label] * member[label].get(outcome, 0.0) for label in belief}
            total = sum(raw.values()) or 1.0
            belief = {label: value / total for label, value in raw.items()}
        stable_at[stable if stable is not None else "never"] += 1
    cap = 4
    stops = [step for step, n in value_stops.items() for _ in range(n)]
    return {
        "synthetic": True,
        "learners": learners,
        "credible_set": "pinned_channel_ensemble" if robust else "point",
        "card": "contrast_confusable v1 default rows, grader channel composed",
        "prior": prior,
        "minutes_per_observation": round(minutes.minutes, 4),
        "observations_value_asks_for": dict(sorted(value_stops.items())),
        "value_stops_earlier_than_4": sum(1 for step in stops if step < cap),
        "value_stops_at_4": sum(1 for step in stops if step == cap),
        "value_continues_past_4": sum(1 for step in stops if step > cap),
        "decision_stable_after": {str(key): value for key, value in sorted(stable_at.items(), key=lambda pair: str(pair[0]))},
        "methods": dict(methods),
        "maximum_observations_per_episode": int(episode.maximum_observations),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--simulate", type=int, default=0, help="synthetic probe-episode learners (0: none)")
    args = parser.parse_args(argv)
    root = args.vault
    _refuse_unless_copy(root)

    from learnloop.vault.repository import open_vault_repository
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths

    steps = _upgrade(root)
    vault = load_vault(root)
    repository = open_vault_repository(vault.root, VaultPaths(vault.root, vault.config).sqlite_path)
    history = _history(vault, repository)
    revalued = _revalue_capped_followups(vault, repository, history["followup_intervention"].pop("capped"))
    history["followup_intervention"]["value_on_the_capped_ones"] = revalued
    today = _today(root)
    with repository.connection() as connection:
        today["open_episodes_in_progress"] = connection.execute(
            "SELECT COUNT(*) FROM probe_episodes WHERE status = 'in_progress'"
        ).fetchone()[0]
    if args.simulate:
        today["synthetic_probe_simulation"] = _simulate_probe_episodes(vault, repository, args.simulate)
        today["synthetic_probe_simulation_robust"] = _simulate_probe_episodes(
            vault, repository, max(args.simulate // 10, 50), robust=True
        )
    report = {
        "vault": str(root),
        "algorithm_version": vault.config.algorithms.algorithm_version,
        "upgrade": steps,
        "history": history,
        "today": today,
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
