"""Router objective RO1's successor mvp-0.46: one constant, its defaults, its switches, and its upgrade.

The upgrade is the chain's next journalled link: from mvp-0.45 (or mvp-0.9 onwards through the chain), one
transaction with a whole-vault rebuild under the tag, so existing due dates move to
``interval_for_retention(S)`` when it activates. Fakes only; no model call.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import tomllib

import pytest

from learnloop.algorithm_versions import (
    FOLLOWUP_SERVE_ALGORITHM_VERSION,
    INTERVAL_FACTOR_ALGORITHM_VERSION,
    INTERVAL_FACTOR_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.config.schema import LearnLoopConfig
from learnloop.config.template import (
    DEFAULTS_SNAPSHOT_BY_ALGORITHM,
    LEGACY_DEFAULT_CONFIG_TEXT,
    default_config_text,
    defaults_fingerprint_for_version,
)
from learnloop.db.repositories import Repository
from learnloop.interval_factor_upgrade import PREDECESSOR, upgrade_to_interval_factor
from learnloop.params.fitted_params import resolve_fsrs_weights
from learnloop.params.parameter_registry import classify_config_path
from learnloop.router_objective_switches import (
    available_at_reads_on,
    interval_factor_removed,
    self_report_not_validated_on,
)
from learnloop.scheduling.fsrs import interval_for_retention
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version
from tests.test_ro1_interval_factor import _due, _play, _vault

TAG = INTERVAL_FACTOR_ALGORITHM_VERSION
OLD = FOLLOWUP_SERVE_ALGORITHM_VERSION
SWITCHES = ("scheduler.surprise.remove_interval_factor", "router_objective.available_at_reads",
            "router_objective.self_report_not_validated")


def test_the_successor_is_one_constant_after_fg1_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == PREDECESSOR == "mvp-0.45"
    # Router objective RO4 (mvp-0.47), RO5 (mvp-0.48) and RO6 (mvp-0.49) landed after it and keep it.
    assert TAG == "mvp-0.46" == SUCCESSOR_CHAIN[-5] and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.50"
    assert INTERVAL_FACTOR_VERSIONS == frozenset({TAG, "mvp-0.47", "mvp-0.48", "mvp-0.49", "mvp-0.50"})


def test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_keys():
    for version, fingerprint in DEFAULTS_SNAPSHOT_BY_ALGORITHM.items():
        assert fingerprint == defaults_fingerprint_for_version(version), version
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] != DEFAULTS_SNAPSHOT_BY_ALGORITHM[OLD]
    # main's mvp-0.45 value at 90a2f430c9 (FG1c and RO0 landed), frozen here: dropping RO1's keys reproduces it.
    dumped = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(OLD))).model_dump(
        mode="json", exclude_none=False)
    section = dumped["router_objective"]
    assert (section.pop("available_at_reads"), section.pop("self_report_not_validated")) == (True, True)
    # Router objective RO4 (mvp-0.47): its switch and seeds are in every snapshot, inert below its tag.
    from tests.test_ro4_successor import RO4_KEYS
    from tests.test_ro5_successor import RO5_KEYS
    from tests.test_ro6_successor import RO6_KEYS

    for key in (*RO4_KEYS, *RO5_KEYS, *RO6_KEYS):
        section.pop(key)
    assert section == {"receipts": True}  # RO0's switch stays
    assert dumped["scheduler"]["surprise"].pop("remove_interval_factor") is True
    # Router objective RO2 (no successor): its forecaster in the default list and its card budget.
    dumped["adaptive_difficulty"]["outside_forecasters"].remove("llm_history_v1")
    assert dumped["adaptive_difficulty"].pop("history_card_token_budget") == 48_000
    assert dumped["teacher"].pop("episode_log") is True  # teacher TE2-log's switch (no successor, every snapshot)
    assert dumped["adaptive_difficulty"].pop("lesson_opportunities") is True  # teacher TE3a's switch, inert below mvp-0.50
    digest = hashlib.sha256(json.dumps(dumped, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert digest == "ec22e2fc1e80ca9df220fe21ca66c5bb1166aedee8ce48b7eea38793e9ef83f7"


def test_the_factors_constants_stay_in_config_with_their_note():
    surprise = LearnLoopConfig().scheduler.surprise
    assert (surprise.alpha_interval, surprise.f_min, surprise.f_max) == (0.3, 0.5, 1.5)
    # The decision-only template stores none of them; the full template that does carries the note.
    assert "alpha_interval" not in default_config_text(TAG)
    assert "does nothing at\n# mvp-0.46 and later" in LEGACY_DEFAULT_CONFIG_TEXT


@pytest.mark.parametrize("path", SWITCHES)
def test_each_switch_is_classified_and_reads_off_or_below_the_tag(tmp_path, path):
    rule = classify_config_path(path)
    assert rule is not None and rule.kind == "structural" and "mvp-0.46" in rule.rationale
    gates = {"scheduler.surprise.remove_interval_factor": interval_factor_removed,
             "router_objective.available_at_reads": available_at_reads_on,
             "router_objective.self_report_not_validated": self_report_not_validated_on}
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    assert not any(gate(load_vault(paths.root).config) for gate in gates.values())
    set_algorithm_version(paths, TAG)
    assert all(gate(load_vault(paths.root).config) for gate in gates.values())
    section, _, key = path.rpartition(".")
    append_config_toml(paths.root, f"[{section}]\n{key} = false\n")
    config = load_vault(paths.root).config
    assert {name: gate(config) for name, gate in gates.items()} == {name: name != path for name in gates}


def test_the_openers_install_this_links_completion():
    from learnloop.cli import runtime
    from learnloop_sidecar import context

    assert "learnloop.lesson_opportunity_upgrade" in inspect.getsource(runtime._complete_interrupted_activation)
    assert "learnloop.lesson_opportunity_upgrade" in inspect.getsource(context._complete_interrupted_activation)


def test_the_upgrade_moves_existing_due_dates_to_the_unstretched_interval(tmp_path):
    paths, repository = _vault(tmp_path, OLD)
    played = _play(paths, repository)
    before = {item: state for _a, item, _o, state, _s in played}
    result = upgrade_to_interval_factor(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == (OLD, TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    repository = Repository(paths.sqlite_path)
    weights = resolve_fsrs_weights(repository)
    last = {}
    for attempt_id, item, observed, _state, _surprise in played:
        last[item] = (attempt_id, observed)
    for item, (attempt_id, observed) in last.items():
        state = repository.practice_item_state(item)
        assert (state.stability, state.difficulty) == (before[item].stability, before[item].difficulty)
        assert state.due_at == _due(observed, interval_for_retention(state.stability, weights=weights))
        assert state.due_at != before[item].due_at
        assert repository.latest_attempt_surprise(attempt_id)["fsrs_interval_factor"] == 1.0
    assert repository.has_whole_vault_rebuild(algorithm_version=TAG)
    again = upgrade_to_interval_factor(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_the_upgrade_refuses_anything_older_than_the_chain(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.8")
    result = upgrade_to_interval_factor(paths.root)
    assert not result.upgraded and "cannot upgrade from 'mvp-0.8'" in result.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"
