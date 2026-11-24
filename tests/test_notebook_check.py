"""Structure inspection is offline, read-only and never acceptance."""
from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import tomllib

import pytest
from typer.testing import CliRunner

from tests.notebook_authoring_helpers import external_report_directory, notebook

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def external():
    with external_report_directory() as path:
        yield path


def invoke(path, out, *extra):
    from learnloop.cli import app
    return CliRunner().invoke(app, ['notebook', 'check', str(path), '--scope', 'structure',
                                  '--out', str(out), *extra], terminal_width=200)


def check(external, source):
    pytest.importorskip('marimo')
    path = external / 'notebooks/input.py'
    path.parent.mkdir()
    path.write_text(source)
    before = path.read_bytes()
    result = invoke(path, external / 'report')
    assert result.exit_code in (0, 1), result.output
    assert path.read_bytes() == before
    return result, json.loads((external / 'report/structure.json').read_text())


def test_base_cli_help_without_notebook_imports():
    code = '''
import importlib.abc, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname.split('.')[0] in {'marimo', 'wigglystuff'}:
            raise ModuleNotFoundError(fullname)
sys.meta_path.insert(0, Block())
from learnloop.cli import app
from typer.testing import CliRunner
for args in (['--help'], ['notebook', '--help'], ['doctor', '--help']):
    result = CliRunner().invoke(app, args, terminal_width=200)
    assert result.exit_code == 0, result.output
    if args == ['--help']:
        assert 'notebook' in result.output
assert not any(n.startswith(('marimo', 'learnloop.notebook_authoring')) for n in sys.modules)
'''
    result = subprocess.run([sys.executable, '-B', '-c', code], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('failure', ['missing', 'wrong-version', 'unimportable'])
def test_dependency_error_is_actionable(tmp_path, monkeypatch, failure):
    original = importlib.metadata.version
    def version(name):
        if name == 'marimo':
            if failure == 'missing':
                raise importlib.metadata.PackageNotFoundError(name)
            if failure == 'wrong-version':
                return '0.0.0'
        return original(name)
    monkeypatch.setattr(importlib.metadata, 'version', version)
    if failure == 'unimportable':
        monkeypatch.setitem(sys.modules, 'marimo', None)
        for key in list(sys.modules):
            if key.startswith('marimo.'):
                monkeypatch.delitem(sys.modules, key)
    path = tmp_path / 'input.py'
    path.write_text(notebook(('one', 'x = 1')))
    result = invoke(path, tmp_path / 'report')
    assert result.exit_code == 2
    assert 'uv sync --extra notebook' in result.output
    project = tomllib.loads((ROOT / 'pyproject.toml').read_text())
    pin, = (dep for dep in project['project']['optional-dependencies']['notebook'] if dep.startswith('marimo=='))
    assert pin in result.output
    assert not (tmp_path / 'report').exists()


def test_cells_names_definitions_references_and_function_cells(external):
    source = notebook(('source', 'x = 1'), ('consumer', 'y = x + 2'))
    source = source.replace('if __name__', '@app.function\ndef double(value):\n    return value * x\n\nif __name__')
    result, report = check(external, source)
    assert result.exit_code == 0, result.output
    assert [(c['name'], c['defines'], c['reads']) for c in report['cells']] == [
        ('source', ['x'], []), ('consumer', ['y'], ['x']), ('double', ['double'], ['x'])]
    assert report['cells'][1]['depends_on'] == ['0']
    assert report['findings'] == []


@pytest.mark.parametrize(('cells', 'kind', 'ids'), [
    ([('broken', 'x =')], 'unparsable_cell', ['0']),
    ([('first', 'x = 1'), ('second', 'x = 2')], 'duplicate_definition', ['0', '1']),
    ([('first', 'x = y + 1'), ('second', 'y = x + 1')], 'cycle', ['0', '1']),
])
def test_structural_failures_identify_cells(external, cells, kind, ids):
    result, report = check(external, notebook(*cells))
    assert result.exit_code == 1, result.output
    assert report['structure_status'] == 'failed'
    assert any(f['kind'] == kind and f['cells'] == ids for f in report['findings'])
    assert len(report['cells']) == len(cells)


def test_side_effects_never_execute_and_source_is_unchanged(external):
    marker = external / 'executed'
    trap = f'__import__("pathlib").Path({str(marker)!r}).write_text("executed")'
    source = notebook(('trap', trap), ('dependency', 'import nonexistent_notebook_dependency'))
    source = source.replace('app = marimo.App()', 'app = marimo.App()\n' + trap)
    result, report = check(external, source)
    assert not marker.exists()
    assert report['review_status'] == 'incomplete'
    assert result.exit_code == 1
    assert set(external.iterdir()) == {external / 'notebooks', external / 'report'}


def test_structure_pass_explicitly_is_not_acceptance(external):
    result, report = check(external, notebook(('one', 'x = 1')))
    assert result.exit_code == 0
    assert report['scope'] == 'structure'
    assert report['review_status'] == 'incomplete'
    assert report['accepted'] is False
    assert report['execution_performed'] is False
    assert report['review_layers_performed'] == []
    summary = (external / 'report/structure.txt').read_text()
    assert 'Structure only' in summary and 'no execution' in summary
    assert 'no review layers' in summary and 'not acceptance' in summary


@pytest.mark.parametrize('mode', ['traversal', 'symlink', 'parent-symlink', 'file-symlink', 'hardlink', 'existing', 'checkout'])
def test_output_refusals(tmp_path, mode, request):
    pytest.importorskip('marimo')
    # Link and collision cases reach the descriptor checks only outside a checkout.
    external = tmp_path if mode in ('traversal', 'checkout') else request.getfixturevalue('external')
    path = external / 'input.py'
    path.write_text(notebook(('one', 'x = 1')))
    out = external / 'report'
    if mode == 'traversal':
        out = external / 'report' / '..' / 'escaped'
    elif mode in ('symlink', 'parent-symlink'):
        target = external / 'target'
        target.mkdir()
        out.symlink_to(target, target_is_directory=True)
        if mode == 'parent-symlink':
            out = out / 'child'
    elif mode in ('file-symlink', 'hardlink', 'existing'):
        out.mkdir()
        dest = out / 'structure.json'
        if mode == 'file-symlink':
            dest.symlink_to(path)
        elif mode == 'hardlink':
            dest.hardlink_to(path)
        else:
            dest.write_text('keep')
    elif mode == 'checkout':
        out = ROOT / 'notebook-output-must-not-exist'
    before = path.read_bytes()
    result = invoke(path, out)
    assert result.exit_code == 2, result.output
    assert "Output refused" in result.output
    assert path.read_bytes() == before
    assert not (external / 'escaped').exists()
    assert not (ROOT / 'notebook-output-must-not-exist').exists()
    assert not list(external.rglob('structure.txt'))


def test_out_is_required(tmp_path):
    from learnloop.cli import app
    result = CliRunner().invoke(app, ['notebook', 'check', str(tmp_path / 'input.py'), '--scope', 'structure'])
    assert result.exit_code == 2
    assert '--out' in result.output


def test_check_never_discovers_vault_or_config(external, monkeypatch):
    from learnloop.cli import receipts
    def forbidden(*args, **kwargs):
        pytest.fail('implicit discovery')
    monkeypatch.setattr(receipts, 'find_vault_root', forbidden)
    # The receipt observer must stay idle even when invoked through the root CLI.
    monkeypatch.setattr(receipts.CommandReceipts, '_store', forbidden)
    result, _ = check(external, notebook(('one', 'x = 1')))
    assert result.exit_code == 0


@pytest.mark.parametrize('source', ['', 'x = 1\n', 'import marimo\napp = (\n'])
def test_invalid_notebooks_still_get_failed_reports(external, source):
    result, report = check(external, source)
    assert result.exit_code == 1
    assert report['structure_status'] == 'failed'
    assert report['findings']


def test_compilation_does_not_create_marimo_scratch(monkeypatch):
    pytest.importorskip('marimo')
    from marimo._ast import compiler
    def forbidden(*args, **kwargs):
        pytest.fail('compiler tried to create implicit scratch')
    monkeypatch.setattr(compiler, 'get_tmpdir', forbidden)
    from learnloop.notebook_authoring.marimo_adapter import _parse_structure
    assert _parse_structure(notebook(('one', 'x = 1')))['findings'] == []


def test_malformed_cell_decorator_is_an_artifact_finding():
    pytest.importorskip('marimo')
    from learnloop.notebook_authoring.marimo_adapter import inspect_structure
    source = notebook(('quantity', 'x = 3')).replace('def quantity():', 'class Quantity:')
    report = inspect_structure(source)
    assert [finding['kind'] for finding in report['findings']] == ['invalid_notebook']


def test_fresh_parser_import_writes_nothing_outside_output(external):
    pytest.importorskip('marimo')
    import os
    path = external / 'input.py'
    path.write_text(notebook(('one', 'x = 1')))
    env = {**os.environ, 'XDG_CACHE_HOME': str(external / 'unrequested-cache'),
           'PYTHONDONTWRITEBYTECODE': '1'}
    result = subprocess.run([sys.executable, '-B', '-m', 'learnloop', 'notebook', 'check', str(path),
                             '--scope', 'structure', '--out', str(external / 'report')],
                            cwd=ROOT, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert not (external / 'unrequested-cache').exists()


@pytest.mark.parametrize('source', [
    notebook(('quantity', 'x = 3')) + '\nimport key\n',
    notebook(('quantity', 'x = 3')).replace('@app.cell', '@app.cell(name=b"quantity")'),
])
def test_unrepresented_source_fails_as_a_format_finding(source):
    pytest.importorskip('marimo')
    from learnloop.notebook_authoring.marimo_adapter import inspect_structure
    report = inspect_structure(source)
    assert any(f['kind'] == 'notebook_format' for f in report['findings'])
