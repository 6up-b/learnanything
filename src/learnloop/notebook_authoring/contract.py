"""Static activity declarations. Values in a key never enter the public report."""
from __future__ import annotations

import ast
from collections import Counter
import math

from learnloop.notebook_authoring.marimo_adapter import inspect_cells


MASKS = {'forward', 'inverse', 'delta', 'structural', 'error', 'step', 'assumption'}
RESPONSES = {'scalar', 'distribution', 'set', 'mask', 'ordering', 'expression', 'text', 'code', 'curve', 'approach'}


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _reference(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Constant) and _text(node.value):
        return node.value
    raise ValueError('Expected a name or literal identifier.')


def _literal(node):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError) as exc:
        raise ValueError('Expected a literal declaration.') from exc


def _metadata(value, cells, definitions):
    if not isinstance(value, dict):
        raise ValueError('Declare a literal contract dictionary.')
    target = value.get('target')
    if not isinstance(target, dict) or not all(_text(target.get(k)) for k in ('facet', 'cold_item_family')):
        raise ValueError('target requires facet and cold_item_family.')
    if value.get('fidelity') not in ('illustrative', 'reconstructed'):
        raise ValueError('Declare fidelity as illustrative or reconstructed.')
    anchors = value.get('source_anchors')
    if not isinstance(anchors, list) or not anchors or not all(map(_text, anchors)):
        raise ValueError('Declare the source anchors.')
    intents = value.get('intents')
    if not isinstance(intents, dict) or set(intents) != cells or not all(map(_text, intents.values())):
        raise ValueError('intents must address each named cell exactly once.')
    assumptions = value.get('assumptions')
    if not isinstance(assumptions, list) or any(
        not isinstance(a, dict) or not _text(a.get('statement')) or not _text(a.get('handle'))
        or a['handle'] not in definitions for a in assumptions
    ):
        raise ValueError('Each assumption needs a statement and a defined code handle.')
    units = value.get('reveal_units', {})
    if not isinstance(units, dict) or not all(_text(k) and _text(v) for k, v in units.items()):
        raise ValueError('reveal_units maps named outputs to their kinds.')
    return {
        'target': {k: target[k] for k in ('facet', 'cold_item_family')},
        'fidelity': value['fidelity'], 'source_anchors': anchors, 'intents': intents,
        'assumptions': [{k: a[k] for k in ('statement', 'handle')} for a in assumptions],
        'reveal_units': units,
    }


def _arguments(call, fields, *, positional=()):
    values = dict(zip(positional, call.args, strict=False))
    if len(call.args) > len(positional):
        raise ValueError('Unexpected positional SDK argument.')
    for kw in call.keywords:
        if kw.arg is None or kw.arg in values:
            raise ValueError('Use explicit, unique SDK arguments.')
        values[kw.arg] = kw.value
    if set(fields) != values.keys():
        raise ValueError(f'Expected SDK arguments {", ".join(fields)}.')
    return values


def _commit(call, binding):
    if not binding or binding.startswith('_'):
        raise ValueError('Assign the commit to its own public name.')
    fields = ('widget_or_input', 'prompt', 'response', 'facets')
    args = _arguments(call, fields, positional=fields[:1])
    if isinstance(args['widget_or_input'], ast.Constant) and args['widget_or_input'].value is None:
        raise ValueError('Specify the commit input.')
    prompt, response, facets = (_literal(args[k]) for k in fields[1:])
    if not _text(prompt) or not isinstance(facets, (list, tuple)) or not facets or not all(map(_text, facets)):
        raise ValueError('Commit requires a prompt and named facets.')
    kind = response.get('kind') if isinstance(response, dict) else response
    if not _text(kind) or kind not in RESPONSES:
        raise ValueError('Unknown commit response kind.')
    if kind == 'scalar':
        precision = response.get('precision') if isinstance(response, dict) else None
        if (not isinstance(response, dict) or not _text(response.get('unit')) or type(precision) not in (int, float)
                or precision < 0 or (type(precision) is float and not math.isfinite(precision))):
            raise ValueError('A scalar response requires a unit and finite, nonnegative precision.')
    return {'id': binding, 'response': kind, 'facets': list(facets)}


def _sdk_call(method, call, binding, cell, declarations):
    if method == 'commit':
        declarations['commits'].append(dict(cell=cell, **_commit(call, binding)))
    elif method == 'draw':
        _arguments(call, ())
    elif method == 'reveal':
        args = _arguments(call, ('after', 'show'))
        declarations['reveals'].append(dict(cell=cell, after=_reference(args['after']), show=_reference(args['show'])))
    elif method == 'explain':
        args = _arguments(call, ('after',))
        declarations['explains'].append(dict(cell=cell, after=_reference(args['after'])))
    elif method == 'mask':
        args = _arguments(call, ('cell', 'kind'), positional=('cell', 'kind'))
        kind = _literal(args['kind'])
        if not _text(kind) or kind not in MASKS:
            raise ValueError('Unknown mask kind.')
        declarations['masks'].append(dict(cell=cell, target=_reference(args['cell']), kind=kind))
    elif method == 'hint_unit':
        kinds = [*call.args[:1], *(kw.value for kw in call.keywords if kw.arg == 'kind')]
        if len(kinds) != 1 or any(kw.arg is None for kw in call.keywords):
            raise ValueError('A hint unit requires its kind.')
        kind = _literal(kinds[0])
        if not _text(kind):
            raise ValueError('Declare the hint unit kind.')
        declarations['hints'].append(dict(cell=cell, id=binding, kind=kind))
    else:
        raise ValueError(f'Unknown declarative SDK method: {method}.')


def _key_interface(source, masks):
    tree = ast.parse(source)
    for name, params in (('generate', ['seed']), ('check', ['draw', 'answer'])):
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
        if len(functions) != 1:
            raise ValueError(f'key.py must define {name} once.')
        args = functions[0].args
        if ([a.arg for a in args.posonlyargs + args.args] != params or args.vararg or args.kwarg
                or args.kwonlyargs or args.defaults):
            raise ValueError(f'Incorrect key signature for {name}.')
    fields = {n.targets[0].id: n.value for n in tree.body if isinstance(n, ast.Assign)
              and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)}
    mutants = fields.get('mutants')
    if isinstance(mutants, ast.Dict):
        labels = [_reference(k) for k in mutants.keys]
    elif isinstance(mutants, (ast.List, ast.Tuple)):
        labels = [_reference(k) for k in mutants.elts]
    else:
        raise ValueError('key.py must declare its named mutants (an empty collection is valid).')
    if len(set(labels)) != len(labels):
        raise ValueError('Mutant names must be unique.')
    if masks:
        values = fields.get('mask_values')
        if not isinstance(values, ast.Dict) or not masks <= {_reference(k) for k in values.keys}:
            raise ValueError('key.py must cover each declared mask in mask_values.')
    return labels


def _key_access(node):
    if isinstance(node, ast.Import):
        return any('key' in a.name.split('.') for a in node.names)
    if isinstance(node, ast.ImportFrom):
        return 'key' in (node.module or '').split('.') or any(a.name == 'key' for a in node.names)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.rsplit('/', 1)[-1] == 'key.py'
    if isinstance(node, ast.Call) and node.args:
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, 'attr', '')
        arg = node.args[0]
        return (name in {'__import__', 'import_module'} and isinstance(arg, ast.Constant)
                and isinstance(arg.value, str) and 'key' in arg.value.split('.'))
    return False


def _reveal_flow(cells, declarations, declared_units, fail):
    """A visible descendant of held data can leak it even through an intermediate cell."""
    protected_names = set(declared_units) | {r['show'] for r in declarations['reveals']}
    protected = {c['id'] for c in cells if c['name'] in protected_names
                 or protected_names.intersection(c['defines'])}
    handles = {c['id'] for c in declarations['commits']}
    for cell in cells:
        if cell['parse_status'] != 'parsed':
            continue
        tree = ast.parse(cell['code'])
        # Referring to a gate in after= declares the edge. Other reads of that
        # gate can expose the submitted answer and belong behind the gate.
        after = {kw.value for call in ast.walk(tree) if isinstance(call, ast.Call)
                 and isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name)
                 and call.func.value.id == 'll' and call.func.attr in {'reveal', 'explain'}
                 for kw in call.keywords if kw.arg == 'after'}
        if any(isinstance(node, ast.Name) and node.id in handles and isinstance(node.ctx, ast.Load)
               and node not in after for node in ast.walk(tree)):
            protected.add(cell['id'])
    def descendants(seeds):
        result = set(seeds)
        while True:
            downstream = {c['id'] for c in cells if result.intersection(c['depends_on'])}
            if downstream <= result:
                return result
            result.update(downstream)

    held = {c['id'] for c in cells if c['options'].get('disabled') is True}
    visible = descendants(protected) - descendants(held)
    for cell in cells:
        if cell['id'] in visible:
            fail('precommit_reveal', cell['name'], 'Hold the reveal output and each cell that reads it.')


def inspect_contract(source: str, key: str | None) -> dict:
    graph = inspect_cells(source)
    cells = graph['cells']
    names = [c['name'] if isinstance(c['name'], str) else '' for c in cells]
    definitions = {d for c in cells for d in c['defines']}
    findings = graph['findings']
    declarations = {k: [] for k in ('commits', 'reveals', 'explains', 'hints', 'masks')}
    mutants = []
    metadata = []
    public_metadata = {}

    def fail(kind, name, message):
        findings.append(dict(kind=kind, cells=[name] if name else [], message=message))

    for name, count in Counter(names).items():
        if not isinstance(name, str) or not name.strip('_') or count != 1:
            fail('cell_name', name, 'A stable, unique cell name is required.')
    for cell in cells:
        if cell['parse_status'] != 'parsed':
            continue
        name = cell['name']
        tree = ast.parse(cell['code'])
        bindings = {}
        direct = set()
        for statement in tree.body:
            value = getattr(statement, 'value', None)
            if isinstance(statement, (ast.Expr, ast.Assign, ast.AnnAssign)):
                direct.add(value)
            targets = statement.targets if isinstance(statement, ast.Assign) else [getattr(statement, 'target', None)]
            if len(targets) == 1 and isinstance(targets[0], ast.Name):
                binding = targets[0].id
                bindings[value] = binding
                if binding == 'contract':
                    try:
                        metadata.append(_literal(value))
                    except ValueError as exc:
                        fail('contract_metadata', name, str(exc))
        sdk_calls = {n.func for n in ast.walk(tree) if isinstance(n, ast.Call)}
        sdk_objects = {n.value for n in sdk_calls if isinstance(n, ast.Attribute)}
        for node in ast.walk(tree):
            if _key_access(node):
                fail('client_key_access', name, 'A client cell refers to the sidecar key.')
            if isinstance(node, ast.Name) and node.id == 'll' and isinstance(node.ctx, ast.Load) and node not in sdk_objects:
                fail('indirect_sdk', name, 'Use direct SDK calls so the declared contract is inspectable.')
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            func = node.func
            if not isinstance(func.value, ast.Name) or func.value.id != 'll':
                continue
            if func.attr == 'chart_theme':
                continue
            try:
                if node not in direct:
                    raise ValueError('SDK declarations must be unconditional cell statements.')
                _sdk_call(func.attr, node, bindings.get(node), name, declarations)
            except ValueError as exc:
                fail('sdk_' + func.attr, name, str(exc))
    try:
        if len(metadata) != 1:
            raise ValueError('Declare contract once.')
        public_metadata = _metadata(metadata[0], set(names), definitions)
    except ValueError as exc:
        fail('contract_metadata', None, str(exc))
    commits = {row['id'] for row in declarations['commits']}
    if len(commits) != len(declarations['commits']):
        fail('duplicate_commit', None, 'Each commit requires a distinct name.')
    for row in declarations['reveals'] + declarations['explains']:
        if row['after'] not in commits:
            fail('unknown_commit', row['cell'], 'after must refer to a declared commit.')
    declared_units = public_metadata.get('reveal_units', {})
    known_outputs = definitions | set(names)
    for output in sorted(declared_units.keys() - known_outputs):
        fail('unknown_reveal', None, f'No output or cell named {output!r} for the declared reveal unit.')
    unit_kinds = dict(declared_units)
    unit_kinds.update({r['id']: r['kind'] for r in declarations['hints'] if r['id']})
    for row in declarations['reveals']:
        if row['show'] not in known_outputs:
            fail('unknown_reveal', row['cell'], 'show must identify a declared output or cell.')
        if row['show'] not in unit_kinds:
            fail('reveal_kind', row['cell'], 'Declare the kind of the reveal unit.')
        else:
            row['kind'] = unit_kinds[row['show']]
    if all(isinstance(c['name'], str) for c in cells):
        _reveal_flow(cells, declarations, declared_units, fail)
    masks = {row['target'] for row in declarations['masks']}
    if masks - set(names):
        fail('unknown_mask_cell', None, 'Mask target must be a named cell.')
    if key is None:
        if commits or masks:
            fail('missing_key', None, 'A commit or mask requires a sidecar key.')
    else:
        try:
            mutants = _key_interface(key, masks)
        except SyntaxError:
            # Parser messages can quote the answer-bearing source line.
            fail('key_interface', None, 'key.py has invalid Python syntax.')
        except ValueError as exc:
            fail('key_interface', None, str(exc))

    return dict(cells=[{k: v for k, v in c.items() if k not in {'code', 'options'}} for c in cells],
                findings=findings, contract=public_metadata, declarations=declarations, mutants=mutants,
                parser_version=graph['parser_version'])
