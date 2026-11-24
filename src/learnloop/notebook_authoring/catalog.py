"""Generate the owner-side static folder: python -m learnloop.notebook_authoring.catalog NEW_DIR."""
from __future__ import annotations

import argparse
from hashlib import sha256
from importlib import metadata
import json
import os
from pathlib import Path

from learnloop.notebook_authoring.cards import build_cards
from learnloop.notebook_authoring.examples import index_demo, installed_demos, search_examples
from learnloop.notebook_authoring.marimo_adapter import inspect_demos
from learnloop.notebook_authoring.scratch import directory_fd


class Catalog:
    def __init__(self):
        data = build_cards()
        self.cards = data['cards']
        self.pins = data['pins']
        self.exclusions = data['exclusions']
        self.demos = {}
        self.examples = {}
        demos = list(installed_demos(self.pins, self.cards))
        graphs = inspect_demos([source for _, _, source in demos])
        for (path, version, source), graph in zip(demos, graphs, strict=True):
            self.demos[path] = source
            for row in index_demo(source, path, version, self.cards, graph=graph):
                self.examples[row['id']] = row

    def read_card(self, name):
        return self.cards[name]

    def search_examples(self, query, *, widget=None, k, line_budget):
        return search_examples(self.examples.values(), query, widget=widget, k=k, line_budget=line_budget)

    def read_example(self, example_id, expand='ancestors'):
        row = self.examples[example_id]
        if expand == 'demo':
            return self.demos[row['demo']]
        if expand == 'ancestors':
            return row['ancestors']
        raise ValueError('Choose ancestors or demo.')

    def export(self, out: Path):
        """Create a new folder; index.json is written last so partial exports are recognizable."""
        if not out.name or out.name in {'.', '..'}:
            raise ValueError('Choose a fresh catalog directory.')
        with directory_fd(out.parent) as parent:
            os.mkdir(out.name, mode=0o700, dir_fd=parent)
            fd = os.open(out.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY, dir_fd=parent)
        try:
            def put(name, value):
                dest = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
                with os.fdopen(dest, 'w', encoding='utf-8') as handle:
                    json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
                    handle.write('\n')

            card_index = {}
            for name, card in sorted(self.cards.items()):
                filename = f'card-{name}.json'
                put(filename, card)
                card_index[name] = {'file': filename, 'purpose': (card.get('doc') or name).splitlines()[0]}
            slices = {}
            for row in self.examples.values():
                filename = 'slice-' + sha256(row['id'].encode()).hexdigest() + '.json'
                put(filename, row)
                slices[row['id']] = {'file': filename, 'purpose': row['purpose'], 'tools': row['tools']}
            put('demos.json', self.demos)
            notices = {}
            sources = {card['source'].partition('/')[0] for card in self.cards.values()
                       if '/' in card.get('source', '')}
            for package in sorted(sources | self.pins.keys()):
                dist = metadata.distribution(package)
                notices[package] = {
                    'version': dist.version,
                    'licenses': {str(path): dist.locate_file(path).read_text(encoding='utf-8')
                                 for path in dist.files or () if 'licenses' in path.parts},
                }
            put('licenses.json', notices)
            put('index.json', dict(pins=self.pins, cards=card_index, exclusions=self.exclusions,
                                   slices=slices, execution='pending'))
        finally:
            os.close(fd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('out', type=Path)
    Catalog().export(parser.parse_args().out)
