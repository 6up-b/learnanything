"""Static example candidates. Only a sandboxed execution receipt can promote a slice."""
from __future__ import annotations

import ast
from hashlib import sha256
from importlib import metadata
import re
from textwrap import dedent, indent

from learnloop.notebook_authoring.marimo_adapter import inspect_cells


def _tools(cell, aliases, imports):
    result = set()
    for node in ast.walk(ast.parse(cell['code'])):
        if not isinstance(node, (ast.Attribute, ast.Name)):
            continue
        parts = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if not isinstance(node, ast.Name) or node.id not in aliases:
            continue
        qualified = '.'.join([aliases[node.id], *reversed(parts)])
        result.update(imports.get(qualified, ()))
    return result


def index_demo(source, origin, version, cards, *, graph=None):
    if graph is None:
        graph = inspect_cells(source)
    if graph['findings']:
        return []
    cells = graph['cells']
    imports = {}
    for name, card in cards.items():
        if 'import_path' in card:
            imports.setdefault(card['import_path'], set()).add(name)
    aliases = {}
    for cell in cells:
        for node in ast.walk(ast.parse(cell['code'])):
            if isinstance(node, ast.Import):
                for a in node.names:
                    root = a.name.partition('.')[0]
                    aliases[a.asname or root] = a.name if a.asname else root
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                aliases.update({a.asname or a.name: f'{node.module}.{a.name}' for a in node.names})

    direct = {c['id']: _tools(c, aliases, imports) for c in cells}
    slices = []
    for cell in cells:
        parents = set()
        pending = list(cell['depends_on'])
        while pending:
            parent = pending.pop()
            if parent not in parents:
                parents.add(parent)
                pending.extend(cells[int(parent)]['depends_on'])
        indexes = sorted(parents | {cell['id']}, key=int)
        used = sorted(set().union(*(direct[i] for i in indexes)))
        if not used or all(tool == 'mo.md' for tool in used):
            continue
        code = cell['code']
        purpose = f"{', '.join(used)} in {origin.rsplit('/', 1)[-1]} ({cell['name']})"
        ancestors = [{k: cells[int(i)][k] for k in ('id', 'name', 'code', 'options', 'depends_on')} for i in indexes]
        slices.append(dict(id=f"{origin}@{version}#{cell['id']}", demo=origin, version=version,
                           demo_sha256=sha256(source.encode()).hexdigest(), tools=used, purpose=purpose,
                           cell=cell['id'], code=code, ancestors=ancestors, focus_lines=len(code.splitlines()),
                           lines=sum(len(c['code'].splitlines()) for c in ancestors), execution='pending',
                           render='pending'))
    return slices


def installed_demos(pins, cards):
    for package, version in sorted(pins.items()):
        dist = metadata.distribution(package)
        for rel in sorted(dist.files or ()):
            parts = rel.parts
            if (str(rel).endswith('.py') and rel.name != '__init__.py'
                    and parts[:-1] in ((package, 'demos'), (package, '_tutorials'), ('demos',))):
                yield str(rel), version, dist.locate_file(rel).read_text(encoding='utf-8')

    # Some wheels omit the demo directory but ship examples in the API docs.
    # Keep each fence independent so unrelated examples never supply each other's inputs.
    for name, card in sorted(cards.items()):
        export = card.get('import_path', '')
        if not export.startswith('wigglystuff.') and 'api_source' not in card:
            continue
        for index, block in enumerate(re.findall(r'^\s*```python[ \t]*\n(.*?)^\s*```',
                                                card['doc'], re.MULTILINE | re.DOTALL)):
            block = dedent(block)
            try:
                ast.parse(block)
            except SyntaxError:
                continue
            module, _, symbol = export.rpartition('.')
            imports = f'import marimo as mo\nfrom {module} import {symbol}\n'
            source = (f'import marimo\n\n__generated_with = "{pins["marimo"]}"\napp = marimo.App()\n\n'
                      + '@app.cell\ndef example():\n'
                      + indent(imports + block.rstrip(), '    ') + '\n    return\n\n'
                      + 'if __name__ == "__main__":\n    app.run()\n')
            yield f"{card['source']}/{name}/example-{index}", card['version'], source


def search_examples(examples, query, *, widget=None, k: int, line_budget: int):
    """Lexical search of static candidates within the caller's context budget."""
    if k < 0 or line_budget < 0:
        raise ValueError('Specify nonnegative budgets.')
    terms = set(re.findall(r'\w+', query.casefold()))
    matches = []
    for row in examples:
        if widget and widget not in row['tools']:
            continue
        words = set(re.findall(r'\w+', (row['purpose'] + ' ' + row['code']).casefold()))
        score = len(terms & words)
        if score or not terms:
            matches.append((-score, row['id'], row))
    result = []
    for _, _, row in sorted(matches):
        if len(result) == k:
            break
        if row['focus_lines'] <= line_budget:
            result.append({key: row[key] for key in ('id', 'tools', 'purpose', 'lines', 'focus_lines', 'code', 'execution')})
            line_budget -= row['focus_lines']
    return result
