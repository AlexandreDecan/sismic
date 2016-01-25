import os
import unittest
from sismic import io


class ImportFromYamlTests(unittest.TestCase):
    def test_yaml_tests(self):
        files = ['actions', 'composite', 'deep_history', 'infinite', 'internal', 'nested_parallel',
                 'nondeterministic', 'parallel', 'simple', 'timer']
        for f in files:
            with self.subTest(filename=f):
                io.import_from_yaml(open(os.path.join('tests', 'yaml', f+'.yaml')))

    def test_examples(self):
        files = ['elevator', 'elevator_contract', 'microwave', 'tester_elevator_7th_floor_never_reached',
                 'tester_elevator_moves_after_10s', 'writer_options']
        for f in files:
            with self.subTest(filename=f):
                io.import_from_yaml(open(os.path.join('docs', 'examples', f+'.yaml')))


class ExportToDictYAMLTests(unittest.TestCase):
    def setUp(self):
        files_t = ['actions', 'composite', 'deep_history', 'infinite', 'internal', 'nested_parallel',
                 'nondeterministic', 'parallel', 'simple', 'timer']
        files_e = ['elevator', 'elevator_contract', 'microwave', 'tester_elevator_7th_floor_never_reached',
                 'tester_elevator_moves_after_10s', 'writer_options']

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
                sc_1 = io.import_from_yaml(f)
                ex_1 = io.export_to_yaml(sc_1)

    def test_export_valid(self):
        for f, filename in self.files:
            with self.subTest(filename=filename):
                sc_1 = io.import_from_yaml(f)
                ex_1 = io.export_to_yaml(sc_1)
                sc_2 = io.import_from_yaml(ex_1)

                self.assertTrue(sc_2.validate())