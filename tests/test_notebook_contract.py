"""Each static rule has an activity or revision that breaks it."""
from __future__ import annotations

from copy import deepcopy
import json

import pytest
from typer.testing import CliRunner

from learnloop.notebook_authoring.contract import inspect_contract
from learnloop.notebook_authoring.manifest import check_manifest, static_manifest
from tests.notebook_authoring_helpers import external_report_directory, notebook

pytest.importorskip('marimo')

KEY = ('def generate(seed):\n    return seed\n\ndef check(draw, answer):\n'
       '    return answer == "private-answer-sentinel"\n\nmutants = {"reversed": None}\n')
BASE = [
    ('control', 'switch = True'),
    ('prediction', "guess = ll.commit(switch, prompt='Which direction?', response='approach', facets=['direction'])"),
    ('comparison', 'difference = switch'),
    ('release', "ll.reveal(after=guess, show='comparison')"),
    ('reflection', 'll.explain(after=guess)'),
]


def activity(cells=BASE, *, updates=None, held=('comparison',), metadata=True):
    names = [n for n, _ in cells] + ['description']
    declaration = dict(target=dict(facet='direction', cold_item_family='ordering'),
                       fidelity='illustrative', source_anchors=['synthetic/source'],
                       reveal_units={'comparison': 'contrast'} if 'comparison' in names else {},
                       assumptions=[dict(statement='The switch is enabled.', handle='switch')],
                       intents={n: f'Explain {n}.' for n in names})
    declaration.update(updates or {})
    extra = [('description', f'contract = {declaration!r}')] if metadata else []
    source = notebook(*cells, *extra)
    for name in held:
        source = source.replace(f'@app.cell\ndef {name}(', f'@app.cell(disabled=True)\ndef {name}(')
    return source


def kinds(source, key=KEY):
    return {f['kind'] for f in inspect_contract(source, key)['findings']}


def test_static_contract_and_manifest_obligations():
    source = activity()
    report = inspect_contract(source, KEY)
    assert not report['findings']
    assert 'private-answer-sentinel' not in json.dumps(report)
    assert report['declarations']['commits'] == [
        dict(cell='prediction', id='guess', facets=['direction'], response='approach')]
    manifest = static_manifest(report, source.encode(), KEY.encode())
    assert set(manifest['states']) == {'locked', 'guess/correct', 'guess/junk', 'guess/free-text', 'guess/mutant/reversed'}
    assert {(r['cell'], r['state'], r['layer']) for r in manifest['coverage']} == {
        (c['name'], s, layer) for c in report['cells'] for s in manifest['states']
        for layer in ('layout', 'visual', 'teaching')}
    assert all(row['rounds'] == [] for row in manifest['coverage'])
    assert not check_manifest(manifest, json.dumps(manifest).encode())
    assert manifest['accepted'] is False


def test_help_only_and_rubric_contracts():
    assert not kinds(activity(cells=[BASE[0]]), None)
    assert not kinds(activity(), KEY.replace('{"reversed": None}', '[]'))
    source = activity(cells=[*BASE, ('masking', "ll.mask('comparison', 'structural')"),
                             ('hint', "tip = ll.hint_unit('witness', text='Try the switch.')"),
                             ('drawing', 'public_draw = ll.draw()')])
    assert not kinds(source, KEY + "mask_values = {'comparison': None}\n")


@pytest.mark.parametrize('updates', [
    {'target': {'facet': 'direction'}}, {'assumptions': [{'statement': 'Assume.', 'handle': 'unbound'}]},
    {'source_anchors': []}, {'intents': {'control': 'Observe.'}}, {'fidelity': 'exact'},
])
def test_invalid_metadata(updates):
    assert 'contract_metadata' in kinds(activity(updates=updates))


@pytest.mark.parametrize(('source', 'expected'), [
    (activity(metadata=False), 'contract_metadata'),
    (activity(cells=[*BASE, ('control', 'other = 2')]), 'cell_name'),
    (activity(cells=[*BASE, ('_', 'other = 2')]), 'cell_name'),
    (activity(cells=[('dynamic', 'contract = load_metadata()')], metadata=False), 'contract_metadata'),
    (activity().replace("response='approach'", "response='speed'"), 'sdk_commit'),
    (activity().replace("response='approach'", "response={'kind':'scalar','unit':'m'}"), 'sdk_commit'),
    (activity().replace("facets=['direction']", 'facets=[]'), 'sdk_commit'),
    (activity().replace("prompt='Which direction?'", 'prompt=build_prompt()'), 'sdk_commit'),
    (activity().replace('guess = ll.commit', 'if switch: guess = ll.commit'), 'sdk_commit'),
    (activity().replace('guess = ll.commit', 'll.commit'), 'sdk_commit'),
    (activity().replace('after=guess', 'after=unbound'), 'unknown_commit'),
    (activity().replace("show='comparison'", "show='absent'"), 'unknown_reveal'),
    (activity(updates={'reveal_units': {}}), 'reveal_kind'),
    (activity(held=()), 'precommit_reveal'),
    (activity(cells=[*BASE, ('leak', 'visible = difference')], held=()), 'precommit_reveal'),
    (activity().replace("facets=['direction'])", "facets=['direction'])\n    visible = guess.value"), 'precommit_reveal'),
    (activity(cells=[c for c in BASE if c[0] != 'release'], held=()), 'precommit_reveal'),
    (activity(updates={'reveal_units': {'absent': 'contrast'}}), 'unknown_reveal'),
    (activity(cells=[*BASE, ('read_key', 'import key as sidecar')]), 'client_key_access'),
    (activity(cells=[*BASE, ('read_key', "open('key.py')")]), 'client_key_access'),
    (activity(cells=[*BASE, ('other', "ll.mask('missing', 'inverse')")]), 'unknown_mask_cell'),
    (activity(cells=[*BASE, ('other', "ll.mask('comparison', 'typo')")]), 'sdk_mask'),
    (activity(cells=[*BASE, ('other', 'll.draw(switch)')]), 'sdk_draw'),
    (activity(cells=[*BASE, ('other', 'll.hint_unit()')]), 'sdk_hint_unit'),
    (activity(cells=[*BASE, ('other', 'll.explain()')]), 'sdk_explain'),
    (activity(cells=[*BASE, ('other', 'll.unknown()')]), 'sdk_unknown'),
    (activity(cells=[*BASE, ('other', 'submit = ll.commit')]), 'indirect_sdk'),
])
def test_broken_notebook(source, expected):
    assert expected in kinds(source)


@pytest.mark.parametrize('key', [
    KEY.replace('def generate(seed)', 'def generate()'), KEY.replace('check(draw, answer)', 'check(answer)'),
    KEY.replace('mutants =', 'names ='), KEY.replace('{"reversed": None}', '["same", "same"]'),
    'def syntax error',
])
def test_bad_sidecar_interface(key):
    assert 'key_interface' in kinds(activity(), key)


def test_missing_key_and_mask_value():
    assert 'missing_key' in kinds(activity(), None)
    assert 'key_interface' in kinds(activity(cells=[*BASE, ('masking', "ll.mask('control', 'forward')")]))


@pytest.mark.parametrize('field', [
    'activity_sha256', 'key_sha256', 'coverage', 'states', 'cells', 'accepted', 'publication', 'execution_receipts',
    'independent_oracles', 'screenshots',
])
def test_stale_missing_or_fabricated_manifest(field):
    source = activity()
    manifest = static_manifest(inspect_contract(source, KEY), source.encode(), KEY.encode())
    broken = deepcopy(manifest)
    if field == 'coverage':
        broken[field].pop()
    else:
        broken[field] = 'invented'
    assert check_manifest(manifest, json.dumps(broken).encode())[0]['kind'] == 'manifest_mismatch'


def test_contract_cli_never_imports_key_or_client(tmp_path, monkeypatch):
    from learnloop.cli import app
    from learnloop.notebook_authoring import contract_check

    marker = tmp_path / 'executed'
    trap = f'__import__("pathlib").Path({str(marker)!r}).touch()'
    path = tmp_path / 'activity.py'
    path.write_text(activity(cells=[*BASE, ('trap', trap)]))
    (tmp_path / 'key.py').write_text(KEY + trap)
    captured = {}
    monkeypatch.setattr(contract_check, 'write_reports',
                        lambda out, scope, report, summary, manifest: captured.update(report=report, manifest=manifest))
    args = ['notebook', 'check', str(path), '--scope', 'contract', '--out', str(tmp_path / 'report')]
    runner = CliRunner()
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    assert captured['report']['execution_performed'] is False
    (tmp_path / 'manifest.json').write_text('{}')
    result = runner.invoke(app, args)
    assert result.exit_code == 1 and 'failed' in result.output
    assert not marker.exists()
    (tmp_path / 'key.py').unlink()
    (tmp_path / 'key.py').symlink_to(path)
    result = runner.invoke(app, args)
    assert result.exit_code == 2


def test_answer_read_and_duplicate_gate_findings():
    assert not kinds(activity(cells=[*BASE, ('later', 'visible = difference')]))
    assert 'precommit_reveal' in kinds(activity(cells=[*BASE, ('leak', 'shown = guess.value')]))
    cells = [BASE[0], ('prediction', BASE[1][1] + '\n' + BASE[1][1]), *BASE[2:]]
    assert 'duplicate_commit' in kinds(activity(cells=cells))


def test_contract_cli_writes_revision_bound_reports(tmp_path):
    from learnloop.cli import app

    with external_report_directory() as out:
        path = tmp_path / 'activity.py'
        path.write_text(activity())
        (tmp_path / 'key.py').write_text(KEY)
        runner = CliRunner()
        args = ['notebook', 'check', str(path), '--scope', 'contract', '--out']
        result = runner.invoke(app, [*args, str(out)])
        assert result.exit_code == 0, result.output
        assert sorted(p.name for p in out.iterdir()) == ['contract.json', 'contract.txt', 'manifest.json']
        assert (out / 'contract.txt').read_text() == result.output
        report = json.loads((out / 'contract.json').read_bytes())
        assert report['contract_status'] == 'passed' and not report['accepted']
        (tmp_path / 'manifest.json').write_bytes((out / 'manifest.json').read_bytes())
        path.write_text(activity().replace('switch = True', 'switch = False'))
        result = runner.invoke(app, [*args, str(out / 'edited')])
        assert result.exit_code == 1, result.output
        findings = json.loads((out / 'edited/contract.json').read_bytes())['findings']
        assert [f['kind'] for f in findings] == ['manifest_mismatch']


def test_writer_keeps_held_reveal_across_edit(tmp_path):
    from learnloop.notebook_authoring.cell_writer import edit_cell, write_cells
    from learnloop.notebook_authoring.marimo_adapter import inspect_cells
    cells = [(c['name'], c['code']) for c in inspect_cells(activity())['cells']]
    path = write_cells(tmp_path, cells, held=['comparison'])
    assert not kinds(path.read_text())
    edit_cell(tmp_path, 'control', 'switch = False')
    assert not kinds(path.read_text())


def test_manifest_cannot_be_reused_after_client_or_key_edit():
    first = activity()
    report = inspect_contract(first, KEY)
    original = json.dumps(static_manifest(report, first.encode(), KEY.encode())).encode()
    for client, key in ((first.replace('switch = True', 'switch = False'), KEY), (first, KEY + '\n')):
        current = static_manifest(inspect_contract(client, key), client.encode(), key.encode())
        assert check_manifest(current, original)[0]['kind'] == 'manifest_mismatch'
