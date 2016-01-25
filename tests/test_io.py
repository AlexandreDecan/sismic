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

class ExportToTreeTests(unittest.TestCase):

    def setUp(self):
        files_t = ['actions', 'composite', 'deep_history', 'infinite', 'internal', 'nested_parallel',
                   'nondeterministic', 'parallel', 'simple', 'timer']

        self.results = [
            ['root', '   s1', '   s2', '   s3'],
            ['root', '   s1', '      s1a', '      s1b', '         s1b1', '         s1b2', '   s2'],
            ['root', '   active', '      active.H*', '      concurrent_processes', '         process_1',
             '            s11', '            s12', '            s13', '         process_2', '            s21',
             '            s22', '            s23', '   pause', '   stop'],
            ['root', '   s1', '   s2', '   stop'],
            ['root', '   active', '   s1', '   s2'],
            ['root', '   s1', '      p1', '         r1', '            i1', '            j1', '            k1',
             '         r2', '            i2', '            j2', '            k2', '            y', '      p2',
             '         r3', '            i3', '            j3', '            k3', '            z', '         r4',
             '            i4', '            j4', '            k4', '            x'],
            ['root', '   s1', '   s2', '   s3'],
            ['root', '   s1', '      p1', '         a1', '         b1', '         c1', '         initial1', '      p2',
             '         a2', '         b2', '         c2', '         initial2'],
            ['root', '   final', '   s1', '   s2', '   s3'],
            ['root', '   s1', '   s2', '   s3', '   s4']
        ]

        self.files = []
        for filename in files_t:
            with open(os.path.join('tests', 'yaml', filename + '.yaml')) as f:
                self.files.append('\n'.join(f.readlines()))

    def test_export(self):
        from sismic.io.text import export_to_tree

        for f, r in zip(self.files, self.results):
            statechart = io.import_from_yaml(f)
            self.assertEquals(export_to_tree(statechart), r)
