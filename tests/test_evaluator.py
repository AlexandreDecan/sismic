import unittest
from unittest.mock import MagicMock
from sismic import code
from sismic.code.python import Context, FrozenContext


class DummyEvaluatorTests(unittest.TestCase):
    def setUp(self):
        interpreter = MagicMock(name='interpreter')
        self.evaluator = code.DummyEvaluator(interpreter=interpreter)

    def test_condition(self):
        self.assertTrue(self.evaluator._evaluate_code('blablabla'))
        self.assertTrue(self.evaluator._evaluate_code('False'))

        self.assertEqual(self.evaluator.context, {})

    def test_execution(self):
        self.assertIsNone(self.evaluator._execute_code('blablabla'))

        self.assertEqual(self.evaluator.context, {})


class FrozenContextTests(unittest.TestCase):
    def setUp(self):
        self.context = {'a': 1, 'b': 2}

    def test_freeze(self):
        freeze = FrozenContext(self.context)
        self.assertEqual(len(freeze), 2)
        self.assertEqual(freeze.a, 1)
        self.assertEqual(freeze.b, 2)

    def test_freeze_is_frozen(self):
        freeze = FrozenContext(self.context)
        self.context['a'] = 2
        self.assertEqual(freeze.a, 1)


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.context = Context()

    def test_empty(self):
        self.assertEqual(0, len(self.context))

    def test_insert_root(self):
        self.context['a'] = 1
        self.assertEqual(1, self.context['a'])

    def test_delete_root(self):
        self.context['a'] = 1
        del self.context['a']
        self.assertEqual(0, len(self.context))

    def test_insert_nested(self):
        nested = self.context.new_child()
        nested['a'] = 1
        self.assertEqual(1, nested['a'])
        self.assertEqual(0, len(self.context.map))
        self.assertEqual(1, len(nested.map))

    def test_update_nested(self):
        nested_1 = self.context.new_child()
        nested_2 = self.context.new_child()

        # Nested variable is not accessible in parent or sibling
        nested_2['c'] = 1
        with self.assertRaises(KeyError):
            _ = self.context['c']
        with self.assertRaises(KeyError):
            _ = nested_1['c']
        self.assertEqual(1, nested_2['c'])

        # Variable is propagated to nested states
        self.context['a'] = 1
        self.assertEqual(1, self.context['a'])
        self.assertEqual(1, nested_1['a'])
        self.assertEqual(1, nested_2['a'])

        # Siblings have separate context
        nested_1['b'] = 2
        nested_2['b'] = 3
        self.assertEqual(2, nested_1['b'])
        self.assertEqual(3, nested_2['b'])

        # Nested contexts can affect parent context
        nested_1['a'] = 3
        self.assertEqual(3, self.context['a'])
        self.assertEqual(3, nested_2['a'])
        self.assertEqual(3, nested_2['a'])
        nested_2['a'] = 4
        self.assertEqual(4, self.context['a'])
        self.assertEqual(4, nested_1['a'])
        self.assertEqual(4, nested_2['a'])

        # Parent context is independant from nested ones
        self.context['b'] = 4
        self.assertEqual(2, nested_1['b'])
        self.assertEqual(3, nested_2['b'])
        self.assertEqual(4, self.context['b'])