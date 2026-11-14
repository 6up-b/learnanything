"""``tests/successor_switches.py``: what putting a test vault at a tag writes into its config, and what it never does."""

from __future__ import annotations

import tomllib

from learnloop.algorithm_versions import (
    FAILURE_SHARE_ALGORITHM_VERSION,
    LATEST_ALGORITHM_VERSION,
    OLDEST_SUPPORTED,
    SLIP_GAP_ALGORITHM_VERSION,
)
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version
from tests.successor_switches import SWITCHES_BY_TAG, switches_after


def _toml(paths) -> dict:
    return tomllib.loads((paths.root / "learnloop.toml").read_text(encoding="utf-8"))


def _at(config: dict, dotted: str):
    node = config
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _set_keys(config: dict) -> set[str]:
    every = {key for switches in SWITCHES_BY_TAG.values() for key in switches}
    return {key for key in every if _at(config, key) is not None}


def test_a_vault_at_a_tag_that_opens_is_untouched(tmp_path):
    for version in (OLDEST_SUPPORTED, LATEST_ALGORITHM_VERSION):
        paths = create_basic_vault(tmp_path / version)
        before = (paths.root / "learnloop.toml").read_text(encoding="utf-8")
        set_algorithm_version(paths, version)
        after = (paths.root / "learnloop.toml").read_text(encoding="utf-8")
        assert after == before.replace(f'algorithm_version = "{LATEST_ALGORITHM_VERSION}"',
                                       f'algorithm_version = "{version}"')


def test_an_older_tag_gets_exactly_the_documented_switches(tmp_path):
    every = {key: value for switches in SWITCHES_BY_TAG.values() for key, value in switches.items()}
    for version, expected in (("mvp-0.14", every),
                              (FAILURE_SHARE_ALGORITHM_VERSION, SWITCHES_BY_TAG[SLIP_GAP_ALGORITHM_VERSION])):
        paths = create_basic_vault(tmp_path / version)
        assert not _set_keys(_toml(paths))
        set_algorithm_version(paths, version)
        assert switches_after(version) == expected
        config = _toml(paths)
        assert {key: _at(config, key) for key in _set_keys(config)} == expected
        load_vault(paths.root)  # still a valid config


def test_back_at_the_head_the_switches_are_reversed(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    original = load_vault(paths.root).config.model_dump()
    set_algorithm_version(paths, "mvp-0.14")
    set_algorithm_version(paths, SLIP_GAP_ALGORITHM_VERSION)
    assert not _set_keys(_toml(paths))  # nothing after mvp-0.57 is listed: every earlier key was removed
    set_algorithm_version(paths, LATEST_ALGORITHM_VERSION)
    assert not _set_keys(_toml(paths))
    assert load_vault(paths.root).config.model_dump() == original


def test_a_tests_own_switch_is_never_overwritten(tmp_path):
    # Set before the tag moves: kept at the older tag and after the move back.
    paths = create_basic_vault(tmp_path / "before")
    append_config_toml(paths.root, "[teacher]\nenabled = true\n")
    set_algorithm_version(paths, "mvp-0.14")
    assert _at(_toml(paths), "teacher.enabled") is True
    set_algorithm_version(paths, LATEST_ALGORITHM_VERSION)
    assert _at(_toml(paths), "teacher.enabled") is True
    # Set after: the fragment merges into the table the helper wrote, and the key is the test's from then on.
    other = create_basic_vault(tmp_path / "after")
    set_algorithm_version(other, "mvp-0.14")
    append_config_toml(other.root, "[router_objective]\nfailure_share_to_other_policy = true\n")
    assert _at(_toml(other), "router_objective.failure_share_to_other_policy") is True
    assert _at(_toml(other), "router_objective.enabled") is False
    set_algorithm_version(other, LATEST_ALGORITHM_VERSION)
    assert _at(_toml(other), "router_objective.failure_share_to_other_policy") is True
    assert _at(_toml(other), "router_objective.enabled") is None
    # A fragment naming a table the test itself wrote still refuses the duplicate.
    third = create_basic_vault(tmp_path / "third")
    append_config_toml(third.root, "[intent]\nenabled = true\n")
    set_algorithm_version(third, "mvp-0.14")
    try:
        append_config_toml(third.root, "[intent]\nenabled = false\n")
    except AssertionError as error:
        assert "already has [intent]" in str(error)
    else:
        raise AssertionError("a duplicate table the test wrote was merged")


def test_a_tag_this_code_does_not_know_writes_nothing(tmp_path):
    newer = f"mvp-0.{int(LATEST_ALGORITHM_VERSION.split('.')[1]) + 1}"
    for version in (newer, "mvp-1.0", "not-a-tag"):
        paths = create_basic_vault(tmp_path / version)
        set_algorithm_version(paths, version)
        assert not _set_keys(_toml(paths))
