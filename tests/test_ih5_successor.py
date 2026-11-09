"""Instruct hand-off IH5's successor (mvp-0.55, after phone V3's mvp-0.54): one constant, its defaults, its gate, its
upgrade, and the mix's failure rule (docs/specs/spec_instruct_handoff_v1.md §7a).

A failed policy's share of the router objective's mix goes to the OTHER policy, no longer to staged. The upgrade is the
chain's next journalled link (a projection activation; nothing recorded changes, no migration).
``[router_objective] failure_share_to_other_policy = false`` serves mvp-0.54's mix exactly. Fakes only; no model call.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import random
import tomllib

import pytest

from learnloop.algorithm_versions import (
    FAILURE_SHARE_ALGORITHM_VERSION,
    FAILURE_SHARE_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    PHONE_PROBES_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.config.schema import LearnLoopConfig, RouterObjectiveConfig
from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, default_config_text, defaults_fingerprint_for_version
from learnloop.daily_plan.objective_chooser import _failure_rule_field, objective_settings
from learnloop.failure_share_upgrade import PREDECESSOR, upgrade_to_failure_share
from learnloop.params.parameter_registry import classify_config_path
from learnloop.router import mixture as mx
from learnloop.router_objective import mix
from learnloop.router_objective_switches import failure_share_tag, failure_share_to_other_policy_on
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

TAG = FAILURE_SHARE_ALGORITHM_VERSION
OLD = PHONE_PROBES_ALGORITHM_VERSION
#: IH5's key and IH2's, on the same unreleased tag (spec_instruct_handoff_v1 §5, §7a).
IH5_KEYS = {"failure_share_to_other_policy": True, "lessons_compete_with_followups": True, "learner_preferences": True}


def drop_ih5_keys(dumped: dict) -> dict:
    """An earlier successor's frozen defaults digest: IH5's key (in every snapshot, inert below mvp-0.55) dropped."""

    for key, value in IH5_KEYS.items():
        assert dumped["router_objective"].pop(key) is value
    return dumped


# -- the successor -------------------------------------------------------------------------------------------


def test_the_successor_is_one_constant_after_phone_v3_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == PREDECESSOR == "mvp-0.54"
    assert TAG == "mvp-0.55" == SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION
    assert FAILURE_SHARE_VERSIONS == frozenset({TAG})


def test_the_switch_defaults_on_and_is_classified():
    assert RouterObjectiveConfig().failure_share_to_other_policy is True
    rule = classify_config_path("router_objective.failure_share_to_other_policy")
    assert rule is not None and "kill switch" in rule.rationale and "IH5" in rule.rationale


def test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_key():
    for version, fingerprint in DEFAULTS_SNAPSHOT_BY_ALGORITHM.items():
        assert fingerprint == defaults_fingerprint_for_version(version), version
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] != DEFAULTS_SNAPSHOT_BY_ALGORITHM[OLD]
    # mvp-0.54's value on the branch at IH5's base (19a812ae46), frozen here: dropping IH5's key reproduces it (and router
    # speed stage 2's switches, in every snapshot, which landed after that base).
    from tests.test_rofu_successor import drop_rospeed2_keys

    dumped = drop_rospeed2_keys(drop_ih5_keys(LearnLoopConfig.model_validate(tomllib.loads(default_config_text(OLD))).model_dump(
        mode="json", exclude_none=False)))
    canonical = json.dumps(dumped, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical).hexdigest() == MVP054_BASE_DIGEST
    # The tag's own defaults differ from the predecessor's by the version label alone (the key is in both).
    at_tag = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(TAG))).model_dump(
        mode="json", exclude_none=False)
    before = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(OLD))).model_dump(
        mode="json", exclude_none=False)
    assert at_tag["algorithms"].pop("algorithm_version") == TAG and before["algorithms"].pop("algorithm_version") == OLD
    assert at_tag == before


#: mvp-0.54's recorded defaults snapshot on instruct/handoff 19a812ae46 (the effective config dumped, sorted, compact).
MVP054_BASE_DIGEST = "9b301cbbd426103bc0740712938de05738b347d02057e6be61e92dea2b2d0ff8"


def test_the_gate_reads_off_below_the_tag_switched_off_and_with_the_objective_off(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    assert not failure_share_tag(load_vault(paths.root).config)
    assert not failure_share_to_other_policy_on(load_vault(paths.root).config)
    set_algorithm_version(paths, TAG)
    assert failure_share_to_other_policy_on(load_vault(paths.root).config)
    for n, toml in enumerate(("[router_objective]\nfailure_share_to_other_policy = false\n",
                              "[router_objective]\nenabled = false\n")):
        other = create_basic_vault(tmp_path / f"off{n}")
        set_algorithm_version(other, TAG)
        append_config_toml(other.root, toml)
        assert failure_share_tag(load_vault(other.root).config)
        assert not failure_share_to_other_policy_on(load_vault(other.root).config), toml


def test_the_prefetch_key_names_the_switch_at_the_tag_and_keeps_its_bytes_below(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    below = objective_settings(load_vault(paths.root).config)
    assert "failure_share_to_other_policy" not in below
    set_algorithm_version(paths, TAG)
    on = objective_settings(load_vault(paths.root).config)
    assert on["failure_share_to_other_policy"] is True
    off = create_basic_vault(tmp_path / "off")
    set_algorithm_version(off, TAG)
    append_config_toml(off.root, "[router_objective]\nfailure_share_to_other_policy = false\n")
    flipped = objective_settings(load_vault(off.root).config)
    assert flipped["failure_share_to_other_policy"] is False and flipped != on
    assert {k: v for k, v in on.items() if k not in IH5_KEYS} == below


def test_the_openers_install_this_links_completion():
    from learnloop import failure_share_upgrade
    from learnloop.cli import runtime
    from learnloop_sidecar import context

    assert "learnloop.failure_share_upgrade" in inspect.getsource(runtime._complete_interrupted_activation)
    assert "learnloop.failure_share_upgrade" in inspect.getsource(context._complete_interrupted_activation)
    # It hands an earlier link's journal to phone V3's completion, which hands it on in turn.
    assert "learnloop.phone_probes_upgrade import complete_interrupted_activation" in inspect.getsource(
        failure_share_upgrade)


def test_the_upgrade_publishes_the_tag_and_completes_once(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    result = upgrade_to_failure_share(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == (OLD, TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    again = upgrade_to_failure_share(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_the_upgrade_chains_from_an_older_link(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.47")
    result = upgrade_to_failure_share(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == ("mvp-0.47", TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG


def test_the_upgrade_refuses_anything_older_than_the_chain(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.8")
    result = upgrade_to_failure_share(paths.root)
    assert not result.upgraded and "cannot upgrade from 'mvp-0.8'" in result.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"


def test_the_cli_upgrade_reaches_the_tag_by_default_and_by_name(tmp_path):
    from typer.testing import CliRunner

    from learnloop.cli.app import app

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"{OLD} -> {LATEST_ALGORITHM_VERSION}" in result.output
    named = create_basic_vault(tmp_path / "named")
    set_algorithm_version(named, OLD)
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(named.root), "--to", TAG])
    assert result.exit_code == 0, result.output
    assert load_vault(named.root).config.algorithms.algorithm_version == TAG


# -- the mix's failure rule (spec §7a) -----------------------------------------------------------------------

SUPPORT = ["lesson_offer", "block_a", "block_b", "block_c"]
EPSILON = 0.02
W = 0.7
LLM_DIST = {"lesson_offer": 0.1, "block_a": 0.5, "block_b": 0.3, "block_c": 0.1}
STAGED_REF = "block_b"
NUMERIC_REF = "lesson_offer"


def _record(failed, *, rule=None, w=W):
    record = {"support": SUPPORT, "staged_ref": STAGED_REF, "epsilon": EPSILON, "w": w, "failed": list(failed),
              "llm_distribution": LLM_DIST, "numeric_choice": NUMERIC_REF}
    if rule is not None:
        record["failure_rule"] = rule
    return record


def _weights(failed, *, to_other):
    return mix.effective_weights(W, failed, to_other_policy=to_other)


@pytest.mark.parametrize("failed, today, after", [
    ([], {"staged": 0.0, "llm": W, "numeric": 1 - W}, {"staged": 0.0, "llm": W, "numeric": 1 - W}),
    (["llm"], {"staged": W, "llm": 0.0, "numeric": 1 - W}, {"staged": 0.0, "llm": 0.0, "numeric": 1.0}),
    (["numeric"], {"staged": 1 - W, "llm": W, "numeric": 0.0}, {"staged": 0.0, "llm": 1.0, "numeric": 0.0}),
    (["llm", "numeric"], {"staged": 1.0, "llm": 0.0, "numeric": 0.0}, {"staged": 1.0, "llm": 0.0, "numeric": 0.0}),
])
def test_each_row_of_the_table_produces_its_weights(failed, today, after):
    assert _weights(failed, to_other=False) == pytest.approx(today)
    assert _weights(failed, to_other=True) == pytest.approx(after)
    # The default is the predecessor's rule.
    assert mix.effective_weights(W, failed) == _weights(failed, to_other=False)


@pytest.mark.parametrize("failed", [[], ["llm"], ["numeric"], ["llm", "numeric"]])
def test_the_floor_is_kept_and_propensities_are_exact_in_every_row(failed):
    for rule in (mix.STAGED_RULE, mix.OTHER_POLICY_RULE):
        record = _record(failed, rule=rule)
        pi = mix.recompute(record)
        assert sum(pi.values()) == pytest.approx(1.0)
        assert min(pi.values()) >= EPSILON - 1e-12
        # The drawn candidate's logged propensity is its mu, and the draw's marginal is mu.
        failed_set = set(failed)
        parts = mix.components(SUPPORT, STAGED_REF, llm=None if "llm" in failed_set else LLM_DIST,
                               numeric_ref=None if "numeric" in failed_set else NUMERIC_REF)
        weights = mix.effective_weights(W, failed, to_other_policy=rule == mix.OTHER_POLICY_RULE)
        for n in range(40):
            drawn = mix.draw(SUPPORT, parts, weights, EPSILON, f"seed-{rule}-{failed}-{n}")
            assert drawn.propensity == pytest.approx(pi[drawn.chosen]) and drawn.pi == pytest.approx(pi)


def test_with_the_llm_down_numeric_takes_the_whole_mix_and_staged_is_only_the_last_resort():
    pi = mix.recompute(_record(["llm"], rule=mix.OTHER_POLICY_RULE))
    k = len(SUPPORT)
    assert pi[NUMERIC_REF] == pytest.approx((1 - k * EPSILON) + EPSILON)
    assert all(pi[ref] == pytest.approx(EPSILON) for ref in SUPPORT if ref != NUMERIC_REF)
    pi = mix.recompute(_record(["numeric"], rule=mix.OTHER_POLICY_RULE))
    for ref in SUPPORT:
        assert pi[ref] == pytest.approx((1 - k * EPSILON) * LLM_DIST[ref] + EPSILON)
    both = mix.recompute(_record(["llm", "numeric"], rule=mix.OTHER_POLICY_RULE))
    assert both == pytest.approx(mix.recompute(_record(["llm", "numeric"])))
    assert both[STAGED_REF] == pytest.approx((1 - k * EPSILON) + EPSILON)


def test_a_lesson_offer_in_the_support_can_be_drawn_when_the_llm_has_no_answer():
    # Staged never picks a lesson (its ref is a block); numeric's argmax is the offer.
    parts = mix.components(SUPPORT, STAGED_REF, llm=None, numeric_ref=NUMERIC_REF)
    old = mix.mu(SUPPORT, parts, _weights(["llm"], to_other=False), EPSILON)
    new = mix.mu(SUPPORT, parts, _weights(["llm"], to_other=True), EPSILON)
    assert new["lesson_offer"] > old["lesson_offer"]
    assert old["lesson_offer"] == pytest.approx((1 - len(SUPPORT) * EPSILON) * (1 - W) + EPSILON)
    weights = _weights(["llm"], to_other=True)
    drawn = [mix.draw(SUPPORT, parts, weights, EPSILON, f"offer-{n}") for n in range(200)]
    offers = [d for d in drawn if d.chosen == "lesson_offer"]
    assert len(offers) > 150 and all(d.component in (mix.NUMERIC, mx.UNIFORM) for d in offers)
    assert {d.component for d in drawn} <= {mix.NUMERIC, mx.UNIFORM}  # staged is never drawn with numeric up


def test_switch_off_or_below_the_tag_the_mix_is_the_predecessors_exactly(tmp_path):
    # The chooser asks the gate; its answer picks the rule, and a False gate adds nothing to the record.
    assert _failure_rule_field(False) == {}
    assert _failure_rule_field(True) == {"failure_rule": mix.OTHER_POLICY_RULE}
    for failed in ([], ["llm"], ["numeric"], ["llm", "numeric"]):
        assert mix.recompute(_record(failed)) == mix.recompute(_record(failed, rule=mix.STAGED_RULE))
        assert mix.effective_weights(W, failed, to_other_policy=False) == mix.effective_weights(W, failed)
    # predecessor mix, written out: an LLM failure gives staged w, a numeric failure staged 1 - w.
    assert mix.effective_weights(W, ["llm"]) == {"staged": W, "llm": 0.0, "numeric": pytest.approx(1 - W)}
    assert mix.effective_weights(W, ["numeric"]) == {"staged": pytest.approx(1 - W), "llm": W, "numeric": 0.0}
    paths = create_basic_vault(tmp_path / "vault")
    for version in (OLD,):
        set_algorithm_version(paths, version)
        assert not failure_share_to_other_policy_on(load_vault(paths.root).config)


def test_a_logged_decision_replays_to_its_logged_mu_under_its_own_rule():
    rng = random.Random(5)
    for n in range(60):
        failed = rng.choice([[], ["llm"], ["numeric"], ["llm", "numeric"]])
        rule = rng.choice([None, mix.STAGED_RULE, mix.OTHER_POLICY_RULE])
        to_other = rule == mix.OTHER_POLICY_RULE
        w = rng.uniform(0.05, 0.95)
        record = _record(failed, rule=rule, w=w)
        parts = mix.components(SUPPORT, STAGED_REF, llm=None if "llm" in failed else LLM_DIST,
                               numeric_ref=None if "numeric" in failed else NUMERIC_REF)
        drawn = mix.draw(SUPPORT, parts, mix.effective_weights(w, failed, to_other_policy=to_other), EPSILON,
                         mix.seed_for("boundary", f"decision-{n}"))
        # What the chooser logs: its pi, and (only under the new rule) the rule's name.
        assert mix.recompute(record) == pytest.approx(dict(drawn.pi))
    with pytest.raises(mix.ObjectiveMixError):
        mix.recompute(_record(["llm"], rule="staged_or_so"))


def test_replay_under_both_rules_on_a_synthetic_history_reports_how_often_the_served_choice_changes():
    """The spec's replay: the same seeds drawn under both rules. Only a decision with exactly one policy failed can
    differ, and it can only change when the other policy's pick is not the one the old mix served."""

    rng = random.Random(11)
    changed = {"none": 0, "llm": 0, "numeric": 0, "both": 0}
    seen = {"none": 0, "llm": 0, "numeric": 0, "both": 0}
    for n in range(800):
        failed = rng.choices([[], ["llm"], ["numeric"], ["llm", "numeric"]], weights=[40, 40, 10, 10])[0]
        label = mix.fallback_label(failed) or "none"
        w = rng.uniform(0.2, 0.8)
        raw = [rng.random() + 0.05 for _ in SUPPORT]
        dist = {ref: value / sum(raw) for ref, value in zip(SUPPORT, raw)}
        record = {"support": SUPPORT, "staged_ref": rng.choice(SUPPORT[1:]), "epsilon": EPSILON, "w": w,
                  "failed": failed, "llm_distribution": dist, "numeric_choice": rng.choice(SUPPORT)}
        parts = mix.components(SUPPORT, record["staged_ref"], llm=None if "llm" in failed else dist,
                               numeric_ref=None if "numeric" in failed else record["numeric_choice"])
        seed = mix.seed_for("synthetic", f"d{n}")
        served = {}
        for to_other in (False, True):
            weights = mix.effective_weights(w, failed, to_other_policy=to_other)
            served[to_other] = mix.draw(SUPPORT, parts, weights, EPSILON, seed).chosen
            rule = {"failure_rule": mix.OTHER_POLICY_RULE} if to_other else {}
            assert sum(mix.recompute({**record, **rule}).values()) == pytest.approx(1.0)
        seen[label] += 1
        changed[label] += served[False] != served[True]
    assert changed["none"] == 0 and changed["both"] == 0
    assert seen["llm"] > 0 and changed["llm"] > 0 and changed["numeric"] >= 0
    assert all(changed[key] <= seen[key] for key in seen)
