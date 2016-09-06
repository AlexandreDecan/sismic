import os
import unittest
from sismic import io, exceptions
from schema import SchemaError


class ImportFromYamlParserTests(unittest.TestCase):
    def check_type(self, name):
        yaml = ('statechart:'
                '\n  name: ' + str(name) +
                '\n  preamble: Nothing'
                '\n  root state:'
                '\n    name: s1')

        item = io.import_from_yaml(yaml).name
        self.assertIsInstance(item, str, msg=type(item))

    def test_parser_conversion(self):
        self.check_type(1)
        self.check_type(-1)
        self.check_type(1.0)
        self.check_type('yes')
        self.check_type('True')
        self.check_type('no')
        self.check_type('')

        self.check_type([])
        self.check_type([1, 2])
        self.check_type({})
        self.check_type({1: 1})


class ImportFromYamlTests(unittest.TestCase):
    def test_yaml_tests(self):
        files = ['actions', 'composite', 'deep_history', 'infinite', 'internal', 'nested_parallel',
                 'nondeterministic', 'parallel', 'simple', 'timer']
        for filename in files:
            with self.subTest(filename=filename):
                with open(os.path.join('tests', 'yaml', filename + '.yaml')) as f:
                    io.import_from_yaml(f)

    def test_examples(self):
        files = ['elevator/elevator', 'elevator/elevator_contract', 'microwave/microwave',
                 'elevator/tester_elevator_7th_floor_never_reached', 'elevator/tester_elevator_moves_after_10s', 'writer_options']
        for filename in files:
            with self.subTest(filename=filename):
                with open(os.path.join('docs', 'examples', filename + '.yaml')) as f:
                    io.import_from_yaml(f)

    def test_transitions_to_unknown_state(self):
        yaml = """
        statechart:
          name: test
          root state:
            name: root
            initial: s1
            states:
              - name: s1
                transitions:
                  - target: s2
        """
        with self.assertRaises(exceptions.StatechartError) as cm:
            io.import_from_yaml(yaml)
        self.assertIn('Unknown target state', str(cm.exception))

    def test_history_not_in_compound(self):
        yaml = """
        statechart:
          name: test
          root state:
            name: root
            initial: s1
            states:
              - name: s1
                parallel states:
                 - name: s2
                   type: shallow history
        """
        with self.assertRaises(exceptions.StatechartError) as cm:
            io.import_from_yaml(yaml)
        self.assertIn('cannot be used as a parent for', str(cm.exception))

    def test_declare_both_states_and_parallel_states(self):
        yaml = """
        statechart:
          name: test
          root state:
            name: root
            initial: s1
            states:
              - name: s1
            parallel states:
              - name: s2
        """

        with self.assertRaises(exceptions.StatechartError) as cm:
            io.import_from_yaml(yaml)
        self.assertIn('root cannot declare both a "states" and a "parallel states" property', str(cm.exception))


class ExportToDictYAMLTests(unittest.TestCase):
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
                sc_1 = io.import_from_yaml(f)
                io.export_to_yaml(sc_1)

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

        self.files = []
        for filename in files_t:
            with open(os.path.join('tests', 'yaml', filename + '.yaml')) as f:
                self.files.append((filename, io.import_from_yaml(f)))

    def test_output(self):
        results = [
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

        for (filename, statechart), r in zip(self.files, results):
            with self.subTest(filename=filename):
                self.assertEqual(io.text.export_to_tree(statechart), r)

    def test_all_states_are_exported(self):
        for filename, statechart in self.files:
            with self.subTest(filename=filename):
                result = set(io.text.export_to_tree(statechart, spaces=0))
                expected = set(statechart.states)
                self.assertSetEqual(result, expected)

    def test_indentation_is_correct(self):
        for filename, statechart in self.files:
            with self.subTest(filename=filename):
                result = sorted(io.text.export_to_tree(statechart, spaces=1))

                for r in result:
                    name = r.lstrip()
                    depth = statechart.depth_for(name)
                    spaces = len(r) - len(name)
                    self.assertEqual(depth - 1, spaces)
