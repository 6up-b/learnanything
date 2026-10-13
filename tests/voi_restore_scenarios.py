"""Scenarios whose value-of-information decisions are pinned in
``voi_restore_golden.json``.

The golden file was written by the branch at ``1b094b73`` (before the
multi-family study's switches existed). With every switch at its restore value
(``voi_stopping.robust_gate_with_value = true``, ``lookahead_max_checks = 1``,
``robust_quantile = 0.10``) the successor must reproduce these decisions
exactly; ``tests/test_voi_v2.py`` checks it, one switch at a time and all
three together.

* :func:`pure_decisions`: ``voi_stopping.value_candidates`` over a grid of
  synthetic credible sets (beliefs, check strengths, minutes, routes or none),
  where the robust quantile, the lookahead and the abstention fallback matter.
* :func:`integration_decisions`: the real probe vault (a pinned robust channel,
  129 ensemble members): the Today build's value decisions and the queue, then
  an episode answered step by step with its completions.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

from learnloop.config.schema import LearnLoopConfig
from learnloop.diagnosis import voi_stopping as voi

GOLDEN_PATH = Path(__file__).with_name("voi_restore_golden.json")

_DIGITS = 9

#: Accuracy offsets of a synthetic credible set (member 0 is the mean).
_OFFSETS = (0.0, -0.12, -0.08, -0.05, -0.02, 0.02, 0.05, 0.08, 0.12)


def _round(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, _DIGITS)
    if isinstance(value, dict):
        return {str(key): _round(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_round(item) for item in value]
    return value


def summarize(decision: voi.SiteDecision) -> dict[str, Any]:
    """The decision as a decision: verdicts, reasons, methods and values (no
    receipt-only fields such as the parameter list)."""

    return _round(
        {
            "decision": decision.decision,
            "reason": decision.reason,
            "rank": None
            if decision.rank is None
            else {"verdict": decision.rank["verdict"], "reason": decision.rank["reason"], "best_ref": decision.rank["best_ref"]},
            "at_stake": decision.context.get("decision_at_stake"),
            "candidates": [
                {
                    "ref": value.ref,
                    "decision": value.decision,
                    "reason": value.reason,
                    "method": value.method,
                    "value_uncertain": value.value_uncertain,
                    "eig_nats": value.eig_nats,
                    "eig_robust_nats": value.eig_robust_nats,
                    "value_point_minutes": value.value_point_minutes,
                    "value_robust_minutes": value.value_robust_minutes,
                    "value_ucb_minutes": value.value_ucb_minutes,
                    "cost_minutes": value.cost_minutes,
                }
                for value in decision.candidates
            ],
        }
    )


def summarize_body(body: dict[str, Any]) -> dict[str, Any]:
    """A logged ``SiteDecision.as_dict`` body, reduced as :func:`summarize`."""

    return _round(
        {
            "site": body.get("site"),
            "decision": body.get("decision"),
            "reason": body.get("reason"),
            "recommended_ref": body.get("recommended_ref"),
            "rank": None
            if body.get("rank") is None
            else {key: body["rank"].get(key) for key in ("verdict", "reason", "best_ref")},
            "candidates": [
                {key: candidate.get(key) for key in (
                    "ref", "decision", "reason", "method", "value_uncertain", "eig_nats", "eig_robust_nats",
                    "evsi_point_minutes", "evsi_robust_minutes", "cost_minutes",
                )}
                for candidate in body.get("candidates") or []
            ],
        }
    )


class _Repo:
    """Just enough repository for a VoiContext: no latencies, seeded routes."""

    def __init__(self, routes):
        self._routes = routes

    def failure_triage_routes(self):
        return list(self._routes)

    def connection(self):
        import sqlite3
        from contextlib import closing

        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.execute("CREATE TABLE practice_attempts (practice_item_id TEXT, practice_mode TEXT, latency_seconds REAL)")
        connection.execute("CREATE TABLE interaction_events (kind TEXT, attempt_duration_ms INTEGER)")
        return closing(connection)


ROUTES = [
    {"reason": "unfamiliar_or_missing_knowledge", "first_intervention": "study", "active": 1},
    {"reason": "memory_lapse", "first_intervention": "review", "active": 1},
    {"reason": "false_belief_or_confusion", "first_intervention": "contrast", "active": 1},
]


def context(config: LearnLoopConfig | None = None, routes=ROUTES) -> voi.VoiContext:
    return voi.VoiContext(SimpleNamespace(config=config or LearnLoopConfig()), _Repo(routes))


def _binary_members(labels: tuple[str, ...], positive: str, accuracy: float) -> tuple[dict, ...]:
    """A check that answers "is it ``positive``?" with ``accuracy``, as a credible set."""

    members = []
    for offset in _OFFSETS:
        a = min(max(accuracy + offset, 0.501), 0.995)
        members.append(
            {
                label: ({"yes": a, "no": 1.0 - a} if label == positive else {"yes": 1.0 - a, "no": a})
                for label in labels
            }
        )
    return tuple(members)


def _candidate(ref: str, members: tuple[dict, ...], minutes: float) -> voi.Candidate:
    return voi.Candidate(ref=ref, minutes=voi.MinutesEstimate(float(minutes), "authored_prior"), members=members)


_TWO = ("robust_initial_grasp", "unfamiliar")
_THREE = ("misconception:a", "robust_initial_grasp", "unfamiliar")


def _slates() -> dict[str, Callable[[float], list[voi.Candidate]]]:
    return {
        "strong_weak_flat": lambda m: [
            _candidate("strong", _binary_members(_TWO, "unfamiliar", 0.9), m),
            _candidate("weak", _binary_members(_TWO, "unfamiliar", 0.68), m),
            _candidate("flat", _binary_members(_TWO, "unfamiliar", 0.505), m),
        ],
        "two_weak": lambda m: [
            _candidate("weak_a", _binary_members(_TWO, "unfamiliar", 0.7), m),
            _candidate("weak_b", _binary_members(_TWO, "unfamiliar", 0.72), m),
        ],
        "three_weak": lambda m: [
            _candidate("weak_a", _binary_members(_TWO, "unfamiliar", 0.66), m),
            _candidate("weak_b", _binary_members(_TWO, "unfamiliar", 0.7), m),
            _candidate("weak_c", _binary_members(_TWO, "unfamiliar", 0.74), m),
        ],
    }


def _three_slates() -> dict[str, Callable[[float], list[voi.Candidate]]]:
    return {
        "rival_repairs": lambda m: [
            _candidate("is_misconception", _binary_members(_THREE, "misconception:a", 0.8), m),
            _candidate("is_unfamiliar", _binary_members(_THREE, "unfamiliar", 0.75), m),
            _candidate("is_grasp", _binary_members(_THREE, "robust_initial_grasp", 0.7), m),
        ],
    }


PRIORS_TWO = (0.5, 0.65, 0.8, 0.92)
PRIORS_THREE = ((0.4, 0.3, 0.3), (0.6, 0.25, 0.15), (0.2, 0.2, 0.6))
MINUTES = (0.05, 0.4, 1.0, 2.5, 6.0)


def pure_scenarios() -> list[tuple[str, Callable[[voi.VoiContext], voi.SiteDecision]]]:
    """Every pure scenario as ``(name, decide(ctx))``."""

    out: list[tuple[str, Callable[[voi.VoiContext], voi.SiteDecision]]] = []
    for routed in (True, False):
        for slate_name, slate in _slates().items():
            for p in PRIORS_TWO:
                for minutes in MINUTES:
                    prior = {"unfamiliar": p, "robust_initial_grasp": 1.0 - p}

                    def decide(ctx, slate=slate, minutes=minutes, prior=prior):
                        return voi.value_candidates(
                            ctx, voi.SITE_PROBE_EPISODE, slate(minutes), prior=prior, learning_object_id="lo",
                            former_cap=voi.former_cap(voi.SITE_PROBE_EPISODE, value=4, count=1),
                        )

                    out.append((f"{'routed' if routed else 'unrouted'}/{slate_name}/p{p}/m{minutes}", decide))
        for slate_name, slate in _three_slates().items():
            for weights in PRIORS_THREE:
                for minutes in MINUTES:
                    prior = dict(zip(_THREE, weights))

                    def decide(ctx, slate=slate, minutes=minutes, prior=prior):
                        return voi.value_candidates(
                            ctx, voi.SITE_PROBE_EPISODE, slate(minutes), prior=prior, learning_object_id="lo",
                            former_cap=voi.former_cap(voi.SITE_PROBE_EPISODE, value=4, count=1),
                        )

                    out.append(
                        (f"{'routed' if routed else 'unrouted'}/{slate_name}/{'-'.join(map(str, weights))}/m{minutes}", decide)
                    )
    return out


def pure_decisions(config: LearnLoopConfig | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, decide in pure_scenarios():
        ctx = context(config, ROUTES if name.startswith("routed/") else ())
        out[name] = summarize(decide(ctx))
    return out


def integration_decisions(tmp_path: Path, monkeypatch: Any, toml: str = "") -> dict[str, Any]:
    """The real probe vault: a Today build, then an episode answered step by
    step at two minute costs (pinned per check), with each build's value
    decisions, the queue and each completion."""

    import random

    from tests import test_voi_stopping as T
    from learnloop import ids
    from learnloop.scheduling.scheduler import OfferTrace

    # The pinned channel's credible sets are seeded by ids (the episode's, the
    # calibration schema's and models' ULIDs): seeded ids make the ensembles,
    # and so the decisions, the same on every run. Still monotonic, so id order
    # stays creation order.
    monkeypatch.setattr(ids, "_wall_clock_ms", lambda: 1_760_000_000_000)
    monkeypatch.setattr(ids, "_last_timestamp_ms", -1)
    monkeypatch.setattr(ids, "_last_randomness", 0)
    monkeypatch.setattr(ids.secrets, "randbits", random.Random(7).getrandbits)
    out: dict[str, Any] = {}
    _paths, vault, repository = T._probe_vault(tmp_path / "build", "mvp-0.17", toml=toml)
    trace = OfferTrace()
    queue = T._build(vault, repository, trace=trace)
    out["build"] = {
        "queue": _round(T._fingerprint(queue)),
        "decisions": [summarize_body(dict(body)) for body in trace.voi_decisions],
    }
    for name, minutes, gate_on in (("m0.02", 0.02, False), ("m0.75", 0.75, False), ("gate_m0.02", 0.02, True)):
        with monkeypatch.context() as patch:
            T._minutes(patch, minutes)
            if gate_on:
                vault_m, repository_m = _gate_probe_vault(tmp_path / f"gate_{minutes}", toml)
            else:
                vault_m, repository_m = T._long_probe_vault(tmp_path / f"long_{minutes}", "mvp-0.17", toml)
            steps = []
            for index in range(6):
                episode = repository_m.open_probe_episode(T.LO)
                if episode is None:
                    break
                step_trace = OfferTrace()
                step_queue = T._build(vault_m, repository_m, trace=step_trace)
                answered = T._answer_probe(vault_m, repository_m, score=4 if index % 2 else 0)
                detail = None
                if answered.status == "complete":
                    with repository_m.connection() as connection:
                        raw = connection.execute(
                            "SELECT completion_detail_json FROM probe_episodes WHERE id = ?", (answered.id,)
                        ).fetchone()[0]
                    detail = summarize_body(json.loads(raw)) if raw else None
                steps.append(
                    {
                        "queue_head": [item.practice_item_id for item in step_queue[:3]],
                        "decisions": [summarize_body(dict(body)) for body in step_trace.voi_decisions],
                        "status": answered.status,
                        "completion_reason": answered.completion_reason,
                        "completion_detail": detail,
                    }
                )
                if answered.status != "in_progress":
                    break
            out[f"episode_{name}"] = steps
    return out


#: The long vault without its guard against the episode's other stops: the
#: robust completion gate is live from the breadth minimum (two observations).
_GATE_EPISODE_TOML = "[probe.episode]\naction_equivalence_enabled = false\n[probe.block]\ndefault_block_observations = 1\n"


def _gate_probe_vault(tmp_path: Path, toml: str = ""):
    from tests import test_voi_stopping as T
    from tests.helpers import add_followup_item, admit_probe_instrument_card
    from learnloop.substrate.state_sync import sync_vault_state
    from learnloop.vault.loader import load_vault

    paths, _vault, repository = T._probe_vault(tmp_path, "mvp-0.17", toml=_GATE_EPISODE_TOML + toml)
    for item_id in T._EXTRA_PROBES:
        add_followup_item(paths.root, item_id)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=T.CLOCK)
    admit_probe_instrument_card(
        repository, card_id="card_svd_contrast_more", items=("pi_svd_define_001", "pi_svd_define_002", *T._EXTRA_PROBES)
    )
    return vault, repository


def load_golden() -> dict[str, Any]:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


__all__ = [
    "GOLDEN_PATH",
    "context",
    "integration_decisions",
    "load_golden",
    "pure_decisions",
    "pure_scenarios",
    "summarize",
    "summarize_body",
]
