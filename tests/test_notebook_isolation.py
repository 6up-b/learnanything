"""Only the explicit CLI adapter can reach the owner-side authoring package."""
from pathlib import Path
import tomllib

from tests.notebook_authoring_helpers import import_targets, module_name

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
HARNESS = SRC / 'learnloop/notebook_authoring'
ENTRY = SRC / 'learnloop/cli/notebook.py'
PREFIX = 'learnloop.notebook_authoring'


def test_no_serving_imports_including_namespace_local_relative_and_dynamic():
    assert HARNESS.is_dir()
    offenders = []
    for path in SRC.rglob('*.py'):
        if path == ENTRY or HARNESS in path.parents:
            continue
        targets = import_targets(path.read_text(), module_name(path, SRC), package=path.name == '__init__.py')
        if any(t == PREFIX or t.startswith(PREFIX + '.') for t in targets):
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders


def test_boundary_scanner_handles_import_forms():
    assert HARNESS.is_dir()
    for source in ('import learnloop.notebook_authoring.check',
                   'def f():\n    from learnloop import notebook_authoring',
                   'from .notebook_authoring import check',
                   'import importlib as i; i.import_module("learnloop.notebook_authoring.check")',
                   '__import__("learnloop.notebook_authoring")'):
        assert any(t == PREFIX or t.startswith(PREFIX + '.')
                   for t in import_targets(source, 'learnloop.new_module'))


def test_harness_has_no_learnloop_dependencies_outside_itself():
    assert HARNESS.is_dir()
    for path in HARNESS.rglob('*.py'):
        for target in import_targets(path.read_text(), module_name(path, SRC), package=path.name == '__init__.py'):
            if target.startswith('learnloop.'):
                assert target == PREFIX or target.startswith(PREFIX + '.'), (path, target)


def test_contract_covers_every_source_except_the_one_cli_adapter():
    config = tomllib.loads((ROOT / 'pyproject.toml').read_text())
    contract = next((c for c in config['tool']['importlinter']['contracts']
                     if c['id'] == 'notebook-authoring-stays-outside-production'), None)
    assert contract is not None
    assert contract['forbidden_modules'] == [PREFIX]
    assert contract['allow_indirect_imports'] is False
    expected = set()
    for path in (SRC / 'learnloop').iterdir():
        if path.name in ('__init__.py', '__main__.py', 'cli', 'notebook_authoring', '__pycache__'):
            continue
        if path.suffix == '.py' or (path.is_dir() and (path / '__init__.py').exists()):
            expected.add('learnloop.' + (path.stem if path.suffix == '.py' else path.name))
    expected.update(module_name(p, SRC) for p in (SRC / 'learnloop/cli').glob('*.py')
                    if p.name not in ('__init__.py', 'notebook.py'))
    assert expected <= set(contract['source_modules'])
    assert {'learnloop_sidecar', 'learnloop_mobile', 'learnloop_mcp'} <= set(contract['source_modules'])
