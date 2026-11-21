"""The pinned static marimo interfaces, isolated from the command and filesystem."""
from __future__ import annotations

from importlib import metadata, util
import json
import os
import subprocess
import sys
from typing import Any


class NotebookDependencyError(ValueError):
    """The optional parser cannot safely be used with this installation."""


def _parser_pin() -> str:
    # Distribution requirements are generated from pyproject.toml, including in
    # wheels: a second source-code version constant would silently drift.
    for requirement in metadata.requires('learnloop') or ():
        dependency = requirement.split(';', 1)[0].strip()
        if dependency.startswith('marimo=='):
            return dependency.removeprefix('marimo==')
    raise NotebookDependencyError('Reinstall LearnLoop with its notebook extra; its marimo pin is missing.')


def _parse_structure(source: str) -> dict[str, Any]:
    """Parse and compile metadata only; never construct or run a notebook App."""
    from marimo._ast.cell import SourcePosition
    from marimo._ast.compiler import compile_cell
    from marimo._ast.parse import MarimoFileError, parse_notebook
    from marimo._runtime.dataflow import DirectedGraph
    from marimo._schemas.serialization import UnparsableCell

    pin = _parser_pin()
    cells: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    result = {'parser_version': pin, 'cells': cells, 'findings': findings}
    try:
        notebook = parse_notebook(source)
    except (MarimoFileError, SyntaxError, ValueError) as exc:
        findings.append({'kind': 'invalid_notebook', 'cells': [], 'message': str(exc)})
        return result
    if notebook is None or not notebook.valid:
        findings.append({'kind': 'invalid_notebook', 'cells': [], 'message': 'No valid marimo notebook found.'})
        return result

    graph = DirectedGraph()
    for index, cell in enumerate(notebook.cells):
        cell_id = str(index)
        row = {'id': cell_id, 'name': cell.options.get('name', cell.name), 'line': cell.lineno,
               'defines': [], 'reads': [], 'depends_on': [], 'parse_status': 'parsed'}
        cells.append(row)
        if isinstance(cell, UnparsableCell):
            row['parse_status'] = 'unparsable'
            findings.append({'kind': 'unparsable_cell', 'cells': [cell_id], 'line': cell.lineno,
                             'message': 'Marimo could not parse this cell.'})
            continue
        try:
            # Without a position marimo allocates an implicit scratch directory.
            # compile_cell builds code objects; nothing evaluates those objects.
            compiled = compile_cell(cell.code, cell_id=cell_id,
                                    source_position=SourcePosition(filename='<notebook>', lineno=cell.lineno,
                                                                   col_offset=cell.col_offset))
        except (SyntaxError, ValueError) as exc:
            row['parse_status'] = 'unparsable'
            findings.append({'kind': 'unparsable_cell', 'cells': [cell_id], 'line': cell.lineno,
                             'message': str(exc)})
            continue
        row['defines'] = sorted(compiled.defs)
        row['reads'] = sorted(compiled.refs)
        graph.register_cell(cell_id, compiled)

    for violation in notebook.violations:
        related = [str(i) for i, c in enumerate(notebook.cells)
                   if c.lineno <= violation.lineno <= c.end_lineno]
        findings.append({'kind': 'notebook_format', 'cells': related, 'line': violation.lineno,
                         'message': violation.description})
    for name, owners in sorted(graph.definitions.items()):
        if len(owners) > 1:
            findings.append({'kind': 'duplicate_definition', 'cells': sorted(owners, key=int),
                             'name': name, 'message': f'{name} is defined in multiple cells.'})
    cycles = {tuple(sorted({cid for edge in cycle for cid in edge}, key=int)) for cycle in graph.cycles}
    for cycle in sorted(cycles):
        findings.append({'kind': 'cycle', 'cells': list(cycle), 'message': 'Cyclic cell dependencies.'})
    for row in cells:
        if row['parse_status'] == 'parsed':
            row['depends_on'] = sorted(graph.parents[row['id']], key=int)
    return result


def inspect_structure(source: str) -> dict[str, Any]:
    """Inspect in a clean process so upstream import logging cannot write to home."""
    pin = _parser_pin()
    message = f'Install the pinned marimo=={pin} with `uv sync --extra notebook` to check notebooks.'
    try:
        if metadata.version('marimo') != pin or util.find_spec('marimo') is None:
            raise NotebookDependencyError(message)
    except (ImportError, metadata.PackageNotFoundError) as exc:
        raise NotebookDependencyError(message) from exc
    result = subprocess.run(
        [sys.executable, '-I', '-B', '-m', 'learnloop.notebook_authoring.marimo_adapter'],
        input=source, text=True, capture_output=True, cwd=sys.prefix,
        env={'XDG_CACHE_HOME': os.devnull, 'XDG_CONFIG_HOME': os.devnull, 'XDG_STATE_HOME': os.devnull},
    )
    if result.returncode:
        raise NotebookDependencyError(message)
    return json.loads(result.stdout)


def _deny_side_effects(event: str, args: tuple) -> None:
    # Marimo initializes a file logger during import. A fresh process lets us
    # deny writes before that import without changing the caller's audit policy.
    if event == 'open':
        flags = args[2]
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            raise PermissionError('Static notebook inspection cannot write files')
    elif event in {'os.mkdir', 'os.remove', 'os.rename', 'os.rmdir', 'os.link', 'os.symlink',
                   'os.chmod', 'os.chown', 'os.truncate', 'os.utime', 'os.system', 'subprocess.Popen'} \
            or event.startswith('socket.'):
        raise PermissionError('Static notebook inspection cannot cause external effects')


if __name__ == '__main__':
    sys.addaudithook(_deny_side_effects)
    print(json.dumps(_parse_structure(sys.stdin.read())))
