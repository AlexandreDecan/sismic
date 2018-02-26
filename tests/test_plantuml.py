import os
import unittest

from sismic.io import import_from_yaml
from sismic.io.plantuml import export_to_plantuml


class ExportToPlantumlTests(unittest.TestCase):
    def setUp(self):
        files_t = ['actions', 'composite', 'deep_history', 'infinite', 'internal', 'nested_parallel',
                   'nondeterministic', 'parallel', 'simple', 'timer']
        files_e = ['elevator/elevator', 'elevator/elevator_contract', 'microwave/microwave',
                   'elevator/tester_elevator_7th_floor_never_reached', 'elevator/tester_elevator_moves_after_10s', 'writer_options']

        self.files = []
        for filename in files_t:
            with open(os.path.join('tests', 'yaml', filename + '.yaml')) as f:
                self.files.append(('\n'.join(f.readlines()), filename))
        for filename in files_e:
            with open(os.path.join('docs', 'examples', filename + '.yaml')) as f:
                self.files.append(('\n'.join(f.readlines()), filename))

    def test_export(self):
        for f, filename in self.files:
            with self.subTest(filename=filename):
                sc_1 = import_from_yaml(f)
                export_to_plantuml(sc_1)