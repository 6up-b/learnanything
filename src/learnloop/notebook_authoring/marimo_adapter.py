"""The pinned static marimo interfaces, isolated from the command and filesystem."""
from __future__ import annotations

import ast
import contextlib
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


def _parse_structure(source: str, *, include_code: bool = False) -> dict[str, Any]:
    """Parse and compile metadata only; never construct or run a notebook App."""
    from marimo._ast.cell import SourcePosition
    from marimo._ast.compiler import compile_cell
    from marimo._ast.parse import MarimoFileError, is_run_guard, parse_notebook
    from marimo._runtime.dataflow import DirectedGraph
    from marimo._schemas.serialization import UnparsableCell

    pin = _parser_pin()
    cells: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    result = {'parser_version': pin, 'cells': cells, 'findings': findings}
    try:
        notebook = parse_notebook(source)
    # The pinned parser also asserts on incompatible decorator/node pairs.
    # Without this branch an ordinary malformed artifact looks like a missing extra.
    except (MarimoFileError, SyntaxError, ValueError, AssertionError) as exc:
        findings.append({'kind': 'invalid_notebook', 'cells': [], 'message': str(exc)})
        return result
    if notebook is None or not notebook.valid:
        findings.append({'kind': 'invalid_notebook', 'cells': [], 'message': 'No valid marimo notebook found.'})
        return result

    # The loader stops consuming statements at the run guard. Executable
    # trailing code would otherwise disappear from the review of the artifact.
    try:
        statements = ast.parse(source).body
    except SyntaxError:
        statements = []  # The loader's fallback reports the broken cells.
    for index, statement in enumerate(statements[:-1]):
        if isinstance(statement, ast.If) and is_run_guard(statement):
            findings.append({'kind': 'notebook_format', 'cells': [], 'line': statements[index + 1].lineno,
                             'message': 'Unexpected statements after the notebook run guard.'})
            break

    graph = DirectedGraph()
    for index, cell in enumerate(notebook.cells):
        cell_id = str(index)
        row = {'id': cell_id, 'name': cell.options.get('name', cell.name), 'line': cell.lineno,
               'defines': [], 'reads': [], 'depends_on': [], 'parse_status': 'parsed'}
        options = cell.options
        try:
            json.dumps(options, allow_nan=False)
            if not isinstance(row['name'], str):
                raise ValueError('non-text cell name')
        except (ValueError, TypeError):
            findings.append({'kind': 'notebook_format', 'cells': [cell_id], 'line': cell.lineno,
                             'message': 'Cell options require JSON-compatible values and a text name.'})
            row['name'] = cell.name if isinstance(cell.name, str) else ""
            options = {}
        if include_code:
            row.update(code=cell.code, options=options)
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
    return _worker('structure', source)


def inspect_cells(source: str) -> dict[str, Any]:
    """Return cell bodies alongside the graph for static authoring tools."""
    return _worker('cells', source)


def inspect_demos(sources: list[str]) -> list[dict]:
    return _worker('demos', json.dumps(sources))


def generate(cells: list[tuple[str, str]], *, held=()) -> str:
    return _worker('generate', json.dumps({'cells': cells, 'held': sorted(held)}))


def _worker(operation: str, payload: str) -> Any:
    pin = _parser_pin()
    message = f'Install the pinned marimo=={pin} with `uv sync --extra notebook` to check notebooks.'
    try:
        if metadata.version('marimo') != pin or util.find_spec('marimo') is None:
            raise NotebookDependencyError(message)
    except (ImportError, metadata.PackageNotFoundError) as exc:
        raise NotebookDependencyError(message) from exc
    result = subprocess.run(
        [sys.executable, '-I', '-B', '-m', 'learnloop.notebook_authoring.marimo_adapter', operation],
        input=payload, text=True, capture_output=True, cwd=sys.prefix,
        env={'XDG_CACHE_HOME': os.devnull, 'XDG_CONFIG_HOME': os.devnull, 'XDG_STATE_HOME': os.devnull},
    )
    if result.returncode:
        raise NotebookDependencyError(message)
    response = json.loads(result.stdout)
    if 'error' in response:
        raise ValueError(response['error'])
    return response['result']


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


def _generate(cells: list[tuple[str, str]], held: list[str]) -> str:
    import keyword
    import tempfile

    from marimo._ast.cell import CellConfig
    from marimo._ast.codegen import generate_filecontents
    from marimo._ast.parse import parse_notebook
    from marimo._lint.context import LintContext, RuleContext
    from marimo._lint.rules import DEFAULT_RULE_CODES

    if not all(isinstance(pair, list) and len(pair) == 2 and all(isinstance(x, str) for x in pair)
               for pair in cells):
        raise ValueError('Cells must be (name, code) string pairs.')
    names = [name for name, _ in cells]
    if set(held) - set(names):
        raise ValueError('Only named cells in this revision can be held.')
    if not names or len(set(names)) != len(names):
        raise ValueError('Supply nonempty cells with unique names.')
    for name in names:
        if (not name.isidentifier() or keyword.iskeyword(name) or not name.strip('_')
                or name in {'app', 'marimo', '__name__', '__generated_with'}):
            raise ValueError(f'Invalid cell name: {name!r}')

    # Codegen needs a filename for compile(), but never opens that filename.
    # Without an explicit tempdir, tempfile probes the filesystem with a write.
    tempfile.tempdir = os.devnull
    codes = [code for _, code in cells]

    def serialize():
        return generate_filecontents(codes.copy(), names.copy(), [CellConfig(disabled=n in held) for n in names])

    source = serialize()
    notebook = parse_notebook(source, filepath='activity.py')
    if notebook and len(notebook.cells) == len(names):
        # Marimo promotes pure definitions to module scope under the function's
        # own name. A trailing comment keeps a differently named cell wrapped.
        for index, (expected, cell) in enumerate(zip(names, notebook.cells, strict=True)):
            if cell.name != expected:
                codes[index] += f'\n# Cell: {expected}'
        if codes != [code for _, code in cells]:
            source = serialize()
            notebook = parse_notebook(source, filepath='activity.py')
    if notebook is None or [cell.name for cell in notebook.cells] != names:
        raise ValueError('Marimo could not round-trip the supplied cell names and order.')
    if {c.name for c in notebook.cells if c.options.get('disabled')} != set(held):
        raise ValueError('Marimo could not preserve the held cells.')
    findings = _parse_structure(source)['findings']
    if findings:
        raise ValueError('; '.join(f['message'] for f in findings))

    async def check():
        context = LintContext(notebook, source)
        for rule_type in DEFAULT_RULE_CODES.values():
            rule = rule_type()
            await rule.check(RuleContext(context, rule))
        return await context.get_diagnostics()

    # These pinned marimo check rules only await in-memory diagnostics. Running
    # them serially avoids asyncio's socketpair and propagates rule failures.
    with contextlib.closing(check()) as checks:
        try:
            checks.send(None)
        except StopIteration as done:
            diagnostics = done.value
        else:
            raise NotebookDependencyError('The pinned marimo check rules now require asynchronous I/O.')
    if diagnostics:
        raise ValueError('; '.join(f'{d.code}: {d.message}' for d in diagnostics))
    return source


if __name__ == '__main__':
    sys.addaudithook(_deny_side_effects)
    operation = sys.argv[1] if len(sys.argv) > 1 else 'structure'
    payload = sys.stdin.read()
    try:
        if operation == 'generate':
            result = _generate(**json.loads(payload))
        elif operation == 'demos':
            result = [_parse_structure(source, include_code=True) for source in json.loads(payload)]
        else:
            result = _parse_structure(payload, include_code=operation == 'cells')
        print(json.dumps({'result': result}))
    except (ValueError, SyntaxError) as exc:
        print(json.dumps({'error': str(exc)}))
