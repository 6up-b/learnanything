"""E0 keys (spec D13): process environment only; --env-file never echoes values."""
from __future__ import annotations

import logging

import pytest

from learnloop.experiments.contextual_embeddings import credentials as K

from tests.e0_fakes import verified_prices  # noqa: F401 - the fixture below

#: Every metered pin priced as verified (E0 admission refuses unverified prices; fix round 4).
pytestmark = pytest.mark.usefixtures("verified_prices")


SECRET = "pplx-secret-value-should-never-print-1234"


def test_env_file_loads_only_named_variables_and_never_overrides_the_shell(tmp_path):
    env_file = tmp_path / "keys.env"
    env_file.write_text(f"# comment\nexport PERPLEXITY_API_KEY='{SECRET}'\nVOYAGE_API_KEY=voy-shell-loses\n"
                        "OTHER_SECRET=never-loaded\nnot a line\n", encoding="utf-8")
    environ = {"VOYAGE_API_KEY": "voy-from-shell"}
    result = K.load_env_file(env_file, ["PERPLEXITY_API_KEY", "VOYAGE_API_KEY", "MISSING_KEY"], environ=environ)
    assert result == {"PERPLEXITY_API_KEY": "present", "VOYAGE_API_KEY": "present", "MISSING_KEY": "absent"}
    assert environ["PERPLEXITY_API_KEY"] == SECRET
    assert environ["VOYAGE_API_KEY"] == "voy-from-shell"
    assert "OTHER_SECRET" not in environ


def test_env_file_loading_never_echoes_values(tmp_path, capsys, caplog):
    env_file = tmp_path / "keys.env"
    env_file.write_text(f"PERPLEXITY_API_KEY={SECRET}\n", encoding="utf-8")
    caplog.set_level(logging.DEBUG)
    result = K.load_env_file(env_file, ["PERPLEXITY_API_KEY"], environ={})
    captured = capsys.readouterr()
    assert SECRET not in captured.out + captured.err + caplog.text + repr(result)


def test_an_unreadable_env_file_does_not_quote_it(tmp_path):
    with pytest.raises(K.EnvFileError) as error:
        K.load_env_file(tmp_path / "missing.env", ["PERPLEXITY_API_KEY"], environ={})
    assert "FileNotFoundError" in str(error.value)
    with pytest.raises(K.EnvFileError):
        K.load_env_file(tmp_path / "missing.env", ["bad name"], environ={})


def test_availability_reports_names_only():
    assert K.availability(["A", "B"], environ={"A": "x", "B": ""}) == {"A": "present", "B": "absent"}
    assert K.read_key("A", environ={"A": "x"}) == "x"
    assert K.read_key("B", environ={}) is None
