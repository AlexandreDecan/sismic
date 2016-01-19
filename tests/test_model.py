import unittest
from sismic import io
from sismic import model
from sismic import exceptions


class TraversalTests(unittest.TestCase):
    def setUp(self):
        self.sc = io.import_from_yaml(open('tests/yaml/composite.yaml'))

    def test_parent(self):
        self.assertEqual(self.sc.parent_for('s2'), 'root')
        self.assertEqual(self.sc.parent_for('root'), None)
        with self.assertRaises(exceptions.StatechartError):
            self.sc.parent_for('unknown')

    def test_children(self):
        self.assertEqual(sorted(self.sc.children_for('root')), ['s1', 's2'])
        self.assertEqual(self.sc.children_for('s1b2'), [])

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
        with self.assertRaises(exceptions.StatechartError):
            sc.add_state(s2, parent='root')

    def test_root_already_defined(self):
        root = model.CompoundState('root', 'a')
        sc = model.Statechart('test')
        sc.add_state(root, None)
        with self.assertRaises(exceptions.StatechartError):
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
        with self.assertRaises(exceptions.StatechartError) as cm:
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
        with self.assertRaises(exceptions.StatechartError) as cm:
            io.import_from_yaml(yaml)


class TransitionsTests(unittest.TestCase):
    def setUp(self):
        self.sc = io.import_from_yaml(open('tests/yaml/internal.yaml'))

    def test_transitions_from(self):
        self.assertEqual(self.sc.transitions_from('root'), [])
        self.assertEqual(len(self.sc.transitions_from('active')), 2)
        self.assertEqual(len(self.sc.transitions_from('s1')), 1)

        nb_transitions = 0
        for transition in self.sc.transitions:
            if transition.source == 'unknown':
                nb_transitions += 1
        self.assertEqual(nb_transitions, 0)

        for transition in self.sc.transitions_from('active'):
            self.assertEqual(transition.source, 'active')

    def test_transitions_to(self):
        self.assertEqual(self.sc.transitions_to('root'), [])
        self.assertEqual(len(self.sc.transitions_to('s1')), 1)
        self.assertEqual(len(self.sc.transitions_to('s2')), 2)

        nb_transitions = 0
        for transition in self.sc.transitions:
            if transition.source == 'unknown':
                nb_transitions += 1
        self.assertEqual(nb_transitions, 0)

        for transition in self.sc.transitions_from('s2'):
            self.assertEqual(transition.target, 's2')

        with self.assertRaises(exceptions.StatechartError):
            self.sc.add_transition(model.Transition('s2'))

        self.sc.add_transition(model.Transition('s1'))
        self.assertEqual(len(self.sc.transitions_to('s1')), 2)

    def test_transitions_with(self):
        self.assertEqual(len(self.sc.transitions_with('next')), 1)
        self.assertEqual(len(self.sc.transitions_with('unknown')), 0)


class RemovalTests(unittest.TestCase):
    def setUp(self):
        self.sc = io.import_from_yaml(open('tests/yaml/internal.yaml'))

    def test_remove_transitions(self):
        transitions = self.sc.transitions
        for transition in transitions:
            self.sc.remove_transition(transition)
        self.assertEqual(len(self.sc.transitions), 0)

        with self.assertRaises(exceptions.StatechartError):
            self.sc.remove_transition(None)

    def test_remove_states(self):
        self.sc.remove_state('active')

        self.assertTrue('active' not in self.sc.states)
        nb_transitions = 0
        for transition in self.sc.transitions:
            if transition.source == 'active':
                nb_transitions += 1
        self.assertEqual(nb_transitions, 0)

        nb_transitions = 0
        for transition in self.sc.transitions:
            if transition.target == 'active':
                nb_transitions += 1
        self.assertEqual(nb_transitions, 0)

        with self.assertRaises(exceptions.StatechartError):
            self.sc.remove_state('unknown')

        with self.assertRaises(exceptions.StatechartError):
            self.sc.remove_state('s2')

        self.sc.remove_state('s1')
        self.sc.remove_state('s2')


class RenameStateTests(unittest.TestCase):
    def setUp(self):
        self.sc = io.import_from_yaml(open('tests/yaml/internal.yaml'))

    def test_unknown(self):
        with self.assertRaises(KeyError):
            self.sc.rename_state('unknown', 's3')

    def test_rename_with_self(self):
        with self.assertRaises(exceptions.StatechartError):
            self.sc.rename_state('s2', 's2')

    def test_rename_with_existing(self):
        with self.assertRaises(exceptions.StatechartError):
            self.sc.rename_state('s2', 's1')

    def test_rename(self):
        self.sc.rename_state('active', 's3')
        self.assertTrue('s3' in self.sc.states)
        self.assertFalse('active' in self.sc.states)

    def test_rename_with_transitions(self):
        self.sc.rename_state('s1', 's3')

        self.assertTrue('s1' not in self.sc.states)
        self.assertTrue('s3' in self.sc.states)

        nb_transitions = 0
        for transition in self.sc.transitions:
            if transition.source == 's1':
                nb_transitions += 1
        self.assertEqual(nb_transitions, 0)

        nb_transitions = 0
        for transition in self.sc.transitions:
            if transition.target == 's1':
                nb_transitions += 1
        self.assertEqual(nb_transitions, 0)

        self.assertTrue(len(self.sc.transitions_from('s3')), 1)
        self.assertTrue(len(self.sc.transitions_to('s2')), 1)

    def test_rename_with_initial(self):
        self.sc.rename_state('active', 's3')
        self.assertEqual(self.sc.state_for('root').initial, 's3')