import unittest
from sismic import io
from sismic import model
from sismic import exceptions


class TraversalTests(unittest.TestCase):
    def setUp(self):
        self.sc = io.import_from_yaml(open('tests/yaml/composite.yaml'))

    def test_ancestors(self):
        self.assertEqual(self.sc.ancestors_for('s2'), ['root'])
        self.assertEqual(self.sc.ancestors_for('s1a'), ['s1', 'root'])
        self.assertEqual(self.sc.ancestors_for('s1b1'), ['s1b', 's1', 'root'])

    def test_descendants(self):
        self.assertEqual(self.sc.descendants_for('s2'), [])
        s1 = self.sc.descendants_for('s1')
        self.assertTrue('s1a' in s1)
        self.assertTrue('s1b' in s1)
        self.assertTrue('s1b1' in s1)
        self.assertTrue('s1b2' in s1)
        self.assertTrue(len(s1) == 4)

    def test_depth(self):
        self.assertEqual(self.sc.depth_for('root'), 1)
        self.assertEqual(self.sc.depth_for('s1'), 2)
        self.assertEqual(self.sc.depth_for('s1a'), 3)
        self.assertEqual(self.sc.depth_for('s1b1'), 4)
        self.assertEqual(self.sc.depth_for('s2'), 2)
        self.assertEqual(self.sc.depth_for('s1b2'), 4)

    def test_lca(self):
        self.assertEqual(self.sc.least_common_ancestor('s1', 's2'), 'root')
        self.assertEqual(self.sc.least_common_ancestor('s1', 's1a'), 'root')
        self.assertEqual(self.sc.least_common_ancestor('s1a', 's1b'), 's1')
        self.assertEqual(self.sc.least_common_ancestor('s1a', 's1b1'), 's1')

    def test_leaf(self):
        self.assertEqual(self.sc.leaf_for([]), [])
        self.assertEqual(self.sc.leaf_for(['s1']), ['s1'])
        self.assertEqual(self.sc.leaf_for(['s1', 's2']), ['s1', 's2'])
        self.assertEqual(self.sc.leaf_for(['s1', 's1b1', 's2']), ['s1b1', 's2'])
        self.assertEqual(self.sc.leaf_for(['s1', 's1b', 's1b1']), ['s1b1'])

    def test_events(self):
        self.assertEqual(self.sc.events_for(), ['click', 'close', 'validate'])
        self.assertEqual(self.sc.events_for('s1b1'), ['validate'])
        self.assertEqual(self.sc.events_for(['s1b1', 's1b']), ['click', 'validate'])

    def test_name_collision(self):
        root = model.CompoundState('root', 'a')
        sc = model.Statechart('test')
        sc.add_state(root, None)
        s1 = model.BasicState('a')
        s2 = model.BasicState('a')
        sc.add_state(s1, parent='root')
        with self.assertRaises(exceptions.InvalidStatechartError):
            sc.add_state(s2, parent='root')

    def test_root_already_defined(self):
        root = model.CompoundState('root', 'a')
        sc = model.Statechart('test')
        sc.add_state(root, None)
        with self.assertRaises(exceptions.InvalidStatechartError):
            sc.add_state(root, None)

    def test_transitions_to_unknown_state(self):
        yaml = """
        statechart:
          name: test
          initial state:
            name: root
            initial: s1
            states:
              - name: s1
                transitions:
                  - target: s2
        """
        with self.assertRaises(exceptions.InvalidStatechartError) as cm:
            io.import_from_yaml(yaml)

    def test_history_not_in_compound(self):
        yaml = """
        statechart:
          name: test
          initial state:
            name: root
            initial: s1
            states:
              - name: s1
                parallel states:
                 - name: s2
                   type: shallow history
        """
        with self.assertRaises(exceptions.InvalidStatechartError) as cm:
            io.import_from_yaml(yaml)