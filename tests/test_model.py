import unittest
from sismic import io
from sismic import model


class TraversalTests(unittest.TestCase):
    def setUp(self):
        self.sc = io.import_from_yaml(open('tests/yaml/composite.yaml'))

    def test_ancestors(self):
        self.assertEqual(self.sc.ancestors_for('s2'), [])
        self.assertEqual(self.sc.ancestors_for('s1a'), ['s1'])
        self.assertEqual(self.sc.ancestors_for('s1b1'), ['s1b', 's1'])

    def test_descendants(self):
        self.assertEqual(self.sc.descendants_for('s2'), [])
        s1 = self.sc.descendants_for('s1')
        self.assertTrue('s1a' in s1)
        self.assertTrue('s1b' in s1)
        self.assertTrue('s1b1' in s1)
        self.assertTrue('s1b2' in s1)
        self.assertTrue(len(s1) == 4)

    def test_depth(self):
        self.assertEqual(self.sc.depth_of(None), 0)
        self.assertEqual(self.sc.depth_of('s1'), 1)
        self.assertEqual(self.sc.depth_of('s1a'), 2)
        self.assertEqual(self.sc.depth_of('s1b1'), 3)
        self.assertEqual(self.sc.depth_of('s2'), 1)
        self.assertEqual(self.sc.depth_of('s1b2'), 3)

    def test_lca(self):
        self.assertEqual(self.sc.least_common_ancestor('s1', 's2'), None)
        self.assertEqual(self.sc.least_common_ancestor('s1', 's1a'), None)
        self.assertEqual(self.sc.least_common_ancestor('s1a', 's1b'), 's1')
        self.assertEqual(self.sc.least_common_ancestor('s1a', 's1b1'), 's1')

    def test_leaf(self):
        self.assertEqual(self.sc.leaf_for([]), [])
        self.assertEqual(self.sc.leaf_for(['s1']), ['s1'])
        self.assertEqual(self.sc.leaf_for(['s1', 's2']), ['s1', 's2'])
        self.assertEqual(self.sc.leaf_for(['s1', 's1b1', 's2']), ['s1b1', 's2'])
        self.assertEqual(self.sc.leaf_for(['s1', 's1b', 's1b1']), ['s1b1'])

    def test_events(self):
        self.assertEqual(self.sc.events(), ['click', 'close', 'validate'])
        self.assertEqual(self.sc.events('s1b1'), ['validate'])
        self.assertEqual(self.sc.events(['s1b1', 's1b']), ['click', 'validate'])

    def test_name_collision(self):
        sc = model.StateChart('test', 'initial')
        s1 = model.BasicState('a')
        s2 = model.BasicState('a')
        sc.register_state(s1, parent=None)
        with self.assertRaises(ValueError):
            sc.register_state(s2, parent=None)


class ValidateTests(unittest.TestCase):
    def test_c1(self):
        yaml = """
        statechart:
          name: test
          initial: s1
          states:
            - name: s1
              transitions:
               - target: s2
        """
        with self.assertRaises(AssertionError) as cm:
            io.import_from_yaml(yaml)
        self.assertTrue(cm.exception.args[0].startswith('C1.'))

    def test_c2_2(self):
        yaml = """
        statechart:
          name: test
          initial: s1
          states:
            - name: s1
              parallel states:
               - name: s2
                 type: shallow history
        """
        with self.assertRaises(AssertionError) as cm:
            io.import_from_yaml(yaml)
        self.assertTrue(cm.exception.args[0].startswith('C2.'))

        yaml = """
        statechart:
          name: test
          initial: s1
          states:
            - name: s1
            - name: s2
              type: shallow history
        """
        with self.assertRaises(AssertionError) as cm:
            io.import_from_yaml(yaml)
        self.assertTrue(cm.exception.args[0].startswith('C2.'))

    def test_c3(self):
        yaml = """
        statechart:
          name: test
          initial: s2
          states:
            - name: s1
              states:
                - name: s2
        """
        with self.assertRaises(AssertionError) as cm:
            io.import_from_yaml(yaml)
        self.assertTrue(cm.exception.args[0].startswith('C3.'))

    def test_c3_2(self):
        yaml = """
        statechart:
          name: test
          initial: s1
          states:
            - name: s1
              initial: s2
              states:
                - name: s3
            - name: s2
        """
        with self.assertRaises(AssertionError) as cm:
            io.import_from_yaml(yaml)
        self.assertTrue(cm.exception.args[0].startswith('C3.'))

    def test_c4(self):
        yaml = """
        statechart:
          name: test
          initial: s1
          states:
            - name: s1
              states:
                - name: s2
        """
        statechart = io.import_from_yaml(yaml)
        statechart.states['s1']._children = []
        with self.assertRaises(AssertionError) as cm:
            statechart.validate()
        self.assertTrue(cm.exception.args[0].startswith('C4.'))

    def test_c5(self):
        yaml = """
        statechart:
          name: test
          initial: s1
          states:
            - name: s1
              transitions:
               - target: s1
        """
        statechart = io.import_from_yaml(yaml)
        statechart.transitions[0].to_state = None
        with self.assertRaises(AssertionError) as cm:
            statechart.validate()
        self.assertTrue(cm.exception.args[0].startswith('C5.'))

    def test_c6(self):
        yaml = """
        statechart:
          name: test
          initial: s1
          states:
            - name: s1
              states:
                - name: s3
            - name: s2
              transitions:
                - target: s1
        """
        with self.assertRaises(AssertionError) as cm:
            io.import_from_yaml(yaml)
        self.assertTrue(cm.exception.args[0].startswith('C6.'))