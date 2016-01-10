import os
import unittest
from sismic import io


class ImportFromYamlTests(unittest.TestCase):
    def test_yaml_tests(self):
        files = ['actions', 'composite', 'deep_history', 'infinite', 'internal', 'nested_parallel',
                 'nondeterministic', 'parallel', 'simple', 'timer']
        for f in files:
            io.import_from_yaml(open(os.path.join('tests', 'yaml', f+'.yaml')))

    def test_examples(self):
        files = ['elevator', 'elevator_contract', 'microwave', 'tester_elevator_7th_floor_never_reached',
                 'tester_elevator_moves_after_10s', 'writer_options']
        for f in files:
            io.import_from_yaml(open(os.path.join('docs', 'examples', f+'.yaml')))


class ExportToDictYAMLTests(unittest.TestCase):
    def test_yaml_tests(self):
        files = ['actions', 'composite', 'deep_history', 'infinite', 'internal', 'nested_parallel',
                 'nondeterministic', 'parallel', 'simple', 'timer']
        for f in files:
            d = io.export_to_yaml(io.import_from_yaml(open(os.path.join('tests', 'yaml', f+'.yaml'))))
            # check
            io.import_from_yaml(d)

    def test_examples(self):
        files = ['elevator', 'elevator_contract', 'microwave', 'tester_elevator_7th_floor_never_reached',
                 'tester_elevator_moves_after_10s', 'writer_options']
        for f in files:
            d = io.export_to_yaml(io.import_from_yaml(open(os.path.join('docs', 'examples', f+'.yaml'))))
            # check
            io.import_from_yaml(d)