"""Extract author-facing API facts from the Python sources shipped in pinned wheels."""
from __future__ import annotations

import ast
from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
from importlib import import_module, metadata
from importlib.util import resolve_name
import inspect
from pathlib import Path

from learnloop.notebook_authoring.dependencies import notebook_pins
from learnloop.notebook_authoring.tool_notes import RECIPES, TOOL_NOTES


@lru_cache(maxsize=None)
def _module(module: str):
    dist = metadata.distribution(module.split('.')[0])
    base = module.replace('.', '/')
    for rel in (base + '.py', base + '/__init__.py'):
        path = Path(dist.locate_file(rel))
        if path.is_file():
            source = path.read_bytes()
            return rel, sha256(source).hexdigest(), ast.parse(source)
    raise ValueError(f'Missing installed source for {module}')


def _imports(module: str) -> dict[str, tuple[str, str]]:
    rel, _, tree = _module(module)
    package = module if rel.endswith('/__init__.py') else module.rpartition('.')[0]
    imports = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            name = resolve_name('.' * node.level + (node.module or ''), package)
            imports.update({a.asname or a.name: (name, a.name) for a in node.names})
    return imports


def _exports(module: str) -> list[str]:
    for node in _module(module)[2].body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '__all__' for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f'Cannot inventory {module}.__all__')


def _definition(module, name):
    rel, digest, tree = _module(module)
    for node in reversed(tree.body):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return rel, digest, node
    raise ValueError(f'Cannot extract {module}.{name}; declare an exclusion or extend extraction.')


def _traits(module, cls):
    traits = {}
    imports = _imports(module)
    for base in cls.bases:
        if isinstance(base, ast.Name) and base.id in imports:
            parent, name = imports[base.id]
            if parent.startswith('wigglystuff.'):
                traits.update(_traits(parent, _definition(parent, name)[2]))
    for field in cls.body:
        if not isinstance(field, (ast.Assign, ast.AnnAssign)) or not isinstance(field.value, ast.Call):
            continue
        call = field.value
        if (isinstance(call.func, ast.Attribute) and call.func.attr == 'tag'
                and any(k.arg == 'sync' and isinstance(k.value, ast.Constant) and k.value.value is True
                        for k in call.keywords)):
            targets = field.targets if isinstance(field, ast.Assign) else [field.target]
            traits.update({t.id: ast.unparse(call.func.value) for t in targets if isinstance(t, ast.Name)})
    return traits


def _card(public, module, name):
    path, digest, definition = _definition(module, name)
    signature = definition
    traits = {}
    if isinstance(definition, ast.ClassDef):
        signature = next((d for d in definition.body if isinstance(d, ast.FunctionDef) and d.name == '__init__'), None)
        traits = _traits(module, definition)
    if signature is None:
        # A widget can inherit its entire constructor from an installed base.
        arguments = str(inspect.signature(getattr(import_module(module), name)))
    else:
        args = deepcopy(signature.args)
        if isinstance(definition, ast.ClassDef):
            (args.posonlyargs or args.args).pop(0)
        arguments = '(' + ast.unparse(args) + ')'
    doc = ast.get_docstring(definition) or (ast.get_docstring(signature) if signature else '') or ''
    methods = {}
    if isinstance(definition, ast.ClassDef):
        for method in definition.body:
            if isinstance(method, ast.FunctionDef) and not method.name.startswith('_'):
                methods[method.name] = {'signature': ast.unparse(method.args), 'doc': ast.get_docstring(method) or ''}
    return dict(name=public, source=path, line=definition.lineno, source_sha256=digest,
                version=metadata.version(module.split('.')[0]),
                signature=arguments, doc=doc, synced_traits=traits, methods=methods, **TOOL_NOTES.get(public, {}))


def build_cards() -> dict:
    pins = notebook_pins()
    cards, exclusions = {}, {}
    for module, prefix, names in (
        ('wigglystuff', '', _exports('wigglystuff')),
        ('marimo._plugins.ui', 'mo.ui.', _exports('marimo._plugins.ui')),
        ('marimo', 'mo.', [n[3:] for n in TOOL_NOTES if n.startswith('mo.') and n.count('.') == 1]),
    ):
        imports = _imports(module)
        for name in sorted(names):
            public = prefix + name
            note = TOOL_NOTES.get(public, {})
            if 'exclude' in note:
                exclusions[public] = note['exclude']
                continue
            cards[public] = _card(public, *imports[name])
            cards[public]['import_path'] = ('marimo.' + public[3:] if public.startswith('mo.')
                                            else 'wigglystuff.' + public)
    for name, entry in TOOL_NOTES.items():
        if 'api_source' in entry:
            module, symbol = entry['api_source']
            if module.split('.')[0] not in pins:
                raise ValueError(f'{name} needs an exact notebook dependency.')
            cards[name] = _card(name, module, symbol)
            cards[name]['import_path'] = f'{module}.{symbol}'
    unknown = TOOL_NOTES.keys() - cards.keys() - exclusions.keys()
    if unknown:
        raise ValueError(f'Stale tool entries: {sorted(unknown)}')
    env = {d.metadata['Name']: d.version for d in metadata.distributions() if d.metadata['Name']}
    cards['environment'] = {'name': 'environment', 'doc': 'Installed distributions in this authoring environment.',
                            'packages': dict(sorted(env.items()))}
    for name, description in RECIPES.items():
        cards['recipe.' + name] = {'name': 'recipe.' + name, 'doc': description, 'source': 'LearnLoop design'}
    widgets = metadata.distribution('wigglystuff')
    for path in sorted(widgets.files or ()):
        if path.parts[-3:-1] != ('docs', 'reference') or path.suffix != '.md' or '..' in path.parts:
            continue
        stem = path.stem.replace('-', '').replace('_', '').casefold()
        for card in cards.values():
            if card.get('source', '').startswith('wigglystuff/') and stem in {
                card['name'].casefold(), Path(card['source']).stem.replace('_', '').casefold()
            }:
                card.setdefault('reference', {})[str(path)] = widgets.locate_file(path).read_text(encoding='utf-8')
    dist = metadata.distribution('marimo')
    for path in sorted(dist.files or ()):
        if 'marimo-pair' in path.parts and path.suffix == '.md':
            name = 'marimo.rules.' + path.stem
            cards[name] = {'name': name, 'doc': dist.locate_file(path).read_text(encoding='utf-8'), 'source': str(path)}
    return {'pins': pins, 'cards': cards, 'exclusions': exclusions}
