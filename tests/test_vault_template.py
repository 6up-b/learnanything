from learnloop.db.repositories import Repository
from tests import helpers


def test_template_copies_have_independent_database_files_and_configuration(tmp_path):
    first = helpers.create_basic_vault(tmp_path / "first")
    second = helpers.create_basic_vault(tmp_path / "second")
    before = second.sqlite_path.read_bytes()
    with Repository(first.sqlite_path).connection() as connection:
        connection.execute("CREATE TABLE isolation_sentinel (value TEXT)")
        connection.commit()
    first.config.algorithms.algorithm_version = "mutated-test"
    assert second.sqlite_path.read_bytes() == before
    assert second.config.algorithms.algorithm_version != "mutated-test"
    assert helpers._BASIC_VAULT_TEMPLATE.config.algorithms.algorithm_version != "mutated-test"
    assert first.sqlite_path.stat().st_ino != second.sqlite_path.stat().st_ino


def test_explicit_fresh_construction_still_runs_initializer(tmp_path, monkeypatch):
    calls = []
    original = helpers.init_vault
    def initialize(*args, **kwargs):
        calls.append(args[0])
        return original(*args, **kwargs)
    monkeypatch.setattr(helpers, "init_vault", initialize)
    helpers.create_basic_vault(tmp_path / "fresh", fresh=True)
    assert calls == [tmp_path / "fresh"]
