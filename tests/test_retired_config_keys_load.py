"""Config keys removed because nothing read them (refactor step C3) stay harmless in an old learnloop.toml.

A vault whose TOML still sets every one of them loads, and its effective config is the effective config of the same
TOML without them: the nested keys are dropped, and the retired top-level ``[locks]`` table stays an unread extra, as
any unknown top-level table does. Nothing else moves. Doctor still names the two it warned about.
"""

from __future__ import annotations

from learnloop.ops.doctor import run_doctor
from learnloop.vault.loader import load_vault
from tests.helpers import append_config_toml, create_basic_vault

#: The fragment a pre-C3 vault may carry: every removed key, each next to keys that are still read, so the test
#: also shows the surviving neighbours load as written.
OLD_FRAGMENT = """
[locks]
facet_lock_mass = 3.5
facet_surface_groups = 4

[facet_identity]
merge_locked_facets = false
shortlist_top_k = 3

[mastery.irt]
discrimination_min = 0.4
discrimination_max = 2.5
discrimination_default = 1.0

[plan]
pre_questions = 7
read_words_per_minute = 150

[recall_coverage.severity_examples.arithmetic_slip]
correctness = 0.75
expected_correctness = 0.70
target_error_type = "arithmetic_slip"
expected_error_type = "arithmetic_slip"
expected_severity_band = [0.25, 0.35]

[error_impacts.recall_failure]
families = { recall = -0.25 }
lo_mastery_delta = -0.05
local_severity_gain = 0.9
"""

#: The same fragment with the removed keys taken out (and the emptied `[locks]` table).
CURRENT_FRAGMENT = """
[facet_identity]
shortlist_top_k = 3

[mastery.irt]
discrimination_default = 1.0

[plan]
read_words_per_minute = 150

[recall_coverage.severity_examples.arithmetic_slip]
correctness = 0.75
expected_correctness = 0.70
expected_error_type = "arithmetic_slip"
expected_severity_band = [0.25, 0.35]

[error_impacts.recall_failure]
families = { recall = -0.25 }
local_severity_gain = 0.9
"""

REMOVED = (
    "facet_lock_mass", "facet_surface_groups", "merge_locked_facets", "discrimination_min", "discrimination_max",
    "pre_questions", "target_error_type", "lo_mastery_delta",
)


def _leaf_names(value, names=None):
    names = set() if names is None else names
    if isinstance(value, dict):
        for key, child in value.items():
            names.add(str(key))
            _leaf_names(child, names)
    elif isinstance(value, list):
        for child in value:
            _leaf_names(child, names)
    return names


def test_an_old_config_setting_every_removed_key_loads_as_if_it_did_not(tmp_path):
    old = create_basic_vault(tmp_path / "old")
    append_config_toml(old.root, OLD_FRAGMENT)
    current = create_basic_vault(tmp_path / "current")
    append_config_toml(current.root, CURRENT_FRAGMENT)

    old_config = load_vault(old.root).config
    current_config = load_vault(current.root).config

    dumped = old_config.model_dump(mode="json")
    # The top level keeps an unknown table as an extra nothing reads (``extra="allow"``), as it keeps any other;
    # every removed key below the top level is dropped.
    assert dumped.pop("locks") == {"facet_lock_mass": 3.5, "facet_surface_groups": 4}
    assert dumped == current_config.model_dump(mode="json")
    assert not set(REMOVED) & _leaf_names(dumped)
    # The neighbours were read as written.
    assert old_config.facet_identity.shortlist_top_k == 3
    assert old_config.plan.read_words_per_minute == 150
    assert old_config.error_impacts["recall_failure"].local_severity_gain == 0.9


def test_doctor_still_names_the_retired_lock_settings(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    append_config_toml(paths.root, OLD_FRAGMENT)
    report = run_doctor(paths.root)
    retired = {issue.details.get("setting") for issue in report.issues if issue.code == "config:retired_setting"}
    assert {"locks", "facet_identity.merge_locked_facets"} <= retired
