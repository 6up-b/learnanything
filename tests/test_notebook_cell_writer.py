import os

import pytest

from learnloop.notebook_authoring.cell_writer import edit_cell, write_cells
from learnloop.notebook_authoring.marimo_adapter import generate, inspect_structure

pytest.importorskip('marimo')


def test_round_trip_and_edit(tmp_path):
    cells = [('measure', 'length = 3'), ('twice', 'def twice(value):\n    return value * 2'),
             ('scale', 'result = twice(length)'), ('preview', 'result')]
    path = write_cells(tmp_path, cells)
    assert path.read_text() == generate(cells)
    assert '@app.function' in path.read_text()
    graph = inspect_structure(path.read_text())
    assert [c['name'] for c in graph['cells']] == [n for n, _ in cells]
    assert graph['cells'][2]['depends_on'] == ['0', '1']
    edit_cell(tmp_path, 'measure', 'length = 5')
    assert path.read_text() == generate([('measure', 'length = 5'), *cells[1:]])
    before = path.read_bytes()
    with pytest.raises(ValueError, match='Unknown cell'):
        edit_cell(tmp_path, 'other', 'x = 3')
    with pytest.raises(ValueError):
        edit_cell(tmp_path, 'scale', 'broken =')
    assert path.read_bytes() == before


def test_promotion_retains_given_name_and_never_executes(tmp_path):
    marker = tmp_path / 'executed'
    code = f'from pathlib import Path\nPath({str(marker)!r}).touch()'
    path = write_cells(tmp_path, [('transformation', 'def double(n):\n    return n * 2'), ('trap', code)])
    assert [c['name'] for c in inspect_structure(path.read_text())['cells']] == ['transformation', 'trap']
    assert not marker.exists()


@pytest.mark.parametrize('cells', [
    [], [('repeat', 'x=1'), ('repeat', 'y=2')], [('x(): pass', 'x=1')], [('_', 'x=1')],
    [('first', 'x=y'), ('other', 'y=x')], [('first', 'x=1'), ('other', 'x=2')],
    [('invalid', 'x=')], [('empty_cell', '')],
])
def test_reject_before_creating_artifact(tmp_path, cells):
    with pytest.raises(ValueError):
        write_cells(tmp_path, cells)
    assert list(tmp_path.iterdir()) == []


def test_job_paths(tmp_path):
    real = tmp_path / 'real'
    real.mkdir()
    alias = tmp_path / 'alias'
    alias.symlink_to(real)
    for path in (alias, real / '..'):
        with pytest.raises((OSError, ValueError)):
            write_cells(path, [('quantity', 'quantity = 3')])
    target = real / 'keep'
    target.write_text('original')
    path = real / 'activity.py'
    path.symlink_to(target)
    for edit in (lambda: write_cells(real, [('some', 'x=1')]), lambda: edit_cell(real, 'some', 'x=1')):
        with pytest.raises(OSError):
            edit()
    path.unlink()
    path.hardlink_to(target)
    with pytest.raises(ValueError, match='links'):
        edit_cell(real, 'some', 'x=1')
    assert target.read_text() == 'original'


@pytest.mark.skipif(os.environ.get('LEARNLOOP_TEST_NO_SOCKETS') == '1',
                    reason='marimo check --strict requires an asyncio socketpair')
def test_generated_file_passes_pinned_marimo_check(tmp_path):
    import subprocess
    import sys
    path = write_cells(tmp_path, [('origin', 'start = 3'), ('shift', 'start + 1')])
    before = path.read_bytes()
    result = subprocess.run(
        [sys.executable, '-I', '-B', '-m', 'marimo', 'check', '--strict', path.name],
        cwd=tmp_path, env={'HOME': str(tmp_path), 'TMPDIR': str(tmp_path), 'PATH': os.defpath},
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert path.read_bytes() == before
