"""Coverage is measured against the installed public APIs, independently of the extractor."""
import ast
from hashlib import sha256
from importlib import metadata
import inspect
import json
from pathlib import Path
import tomllib

import pytest

from learnloop.notebook_authoring.cards import build_cards
from learnloop.notebook_authoring.catalog import Catalog
from learnloop.notebook_authoring.examples import index_demo, search_examples
from learnloop.notebook_authoring.marimo_adapter import _parser_pin
from tests.notebook_authoring_helpers import notebook

pytest.importorskip('marimo')
ROOT = Path(__file__).resolve().parents[1]


def test_every_public_export_has_a_card_or_reason():
    catalog = build_cards()
    import marimo as mo
    import wigglystuff
    public = {*wigglystuff.__all__, *('mo.ui.' + name for name in mo.ui.__all__)}
    cards, excluded = catalog['cards'], catalog['exclusions']
    assert public <= cards.keys() | excluded.keys()
    assert not cards.keys() & excluded.keys()
    assert all(reason.strip() for reason in excluded.values())
    for name in public & cards.keys():
        card = cards[name]
        assert card['signature'], name
        dist = metadata.distribution(card['source'].split('/')[0])
        assert card['source_sha256'] == sha256(dist.locate_file(card['source']).read_bytes()).hexdigest()
    card = cards['TangleLatex']
    assert 'latex' in card['signature'] and 'parameters' in card['signature']
    assert 'values' in card['synced_traits']
    assert card['doc'] and card['typed_alternative']
    assert 'steps' in cards['CellTour']['synced_traits']
    assert cards['GamepadWidget']['signature'] == str(inspect.signature(wigglystuff.GamepadWidget))
    assert 'chat' in cards['mo.ui.chat']['source']
    assert cards['mo.ui.altair_chart']['requires'] == ['altair']


def test_pin_bump_includes_environment_lock_notices_and_parser():
    pins = build_cards()['pins']
    project = tomllib.loads((ROOT / 'pyproject.toml').read_text())
    assert sorted(f'{n}=={v}' for n, v in pins.items()) == sorted(project['project']['optional-dependencies']['notebook'])
    assert _parser_pin() == pins['marimo']
    locked = tomllib.loads((ROOT / 'uv.lock').read_text())['package']
    notices = (ROOT / 'LICENSES.txt').read_text()
    for name, version in pins.items():
        assert any(p['name'] == name and p['version'] == version for p in locked)
        assert f'{name} {version}' in notices


def test_slice_keeps_ancestors_and_reads_and_search_budget():
    source = notebook(('imports', 'from wigglystuff import Matrix as Grid'),
                      ('unrelated', 'z = 40'), ('input_grid', 'grid = Grid()'),
                      ('report', 'values = grid.value'))
    rows = index_demo(source, 'synthetic/grid.py', 'test', {'Matrix': {'import_path': 'wigglystuff.Matrix'}})
    last = rows[-1]
    assert last['tools'] == ['Matrix'] and last['execution'] == 'pending'
    assert len(last['ancestors']) == 3
    assert [cell['name'] for cell in last['ancestors']] == ['imports', 'input_grid', 'report']
    assert last['ancestors'][-1]['code'] == last['code']
    assert last['lines'] == 3
    assert len(search_examples(rows, 'grid', widget='Matrix', k=1, line_budget=1)) == 1
    assert not search_examples(rows, 'grid', k=2, line_budget=0)


def test_static_folder_includes_installed_examples(tmp_path):
    catalog = Catalog()
    rows = list(catalog.examples.values())
    assert any('mo.ui.slider' in row['tools'] for row in rows)
    assert any('CellTour' in row['tools'] for row in rows)
    row = next(row for row in rows if 'CellTour' in row['tools'])
    assert catalog.read_example(row['id']) == row['ancestors']
    ast.parse(catalog.read_example(row['id'], expand='demo'))
    out = tmp_path / 'export'
    catalog.export(out)
    index = json.loads((out / 'index.json').read_text())
    assert json.loads((out / index['cards']['CellTour']['file']).read_text()) == catalog.read_card('CellTour')
    assert json.loads((out / index['slices'][row['id']]['file']).read_text()) == row
    with pytest.raises(FileExistsError):
        catalog.export(out)


def test_next_pin_changes_the_parser_admission_message(monkeypatch):
    from learnloop.notebook_authoring import marimo_adapter
    pin = '0.0.0+synthetic'
    monkeypatch.setattr(metadata, 'requires', lambda name: [f"marimo=={pin}; extra == 'notebook'"])
    with pytest.raises(marimo_adapter.NotebookDependencyError) as exc:
        marimo_adapter.inspect_structure('')
    assert f'marimo=={pin}' in str(exc.value)


def test_one_entry_adds_a_tool_with_its_extraction_gaps(monkeypatch):
    from learnloop.notebook_authoring.tool_notes import TOOL_NOTES
    monkeypatch.setitem(TOOL_NOTES, 'choice-demo', {
        'api_source': ('wigglystuff.tangle', 'TangleChoice'), 'typed_alternative': 'Type the selected choice.',
    })
    card = build_cards()['cards']['choice-demo']
    assert 'choices' in card['signature'] and 'choice' in card['synced_traits']
    assert card['typed_alternative'] == 'Type the selected choice.'
    demo = notebook(('imports', 'from wigglystuff.tangle import TangleChoice as Choice'),
                    ('pick', 'choice = Choice()'))
    rows = index_demo(demo, 'synthetic/choice.py', 'test', {'choice-demo': card})
    assert rows[-1]['tools'] == ['choice-demo']
