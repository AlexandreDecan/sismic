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