import unittest
from unittest.mock import MagicMock
from sismic import code
from sismic.code.python import Context
from sismic import exceptions
from sismic.model import Event, InternalEvent


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
        nested = self.context.new_child()
        self.context['a'] = 1
        nested['b'] = 2
        self.assertEqual(1, self.context.map['a'])
        self.assertEqual(2, nested.map['b'])

        nested['a'] = 3
        self.assertEqual(3, self.context['a'])

        self.context['b'] = 4
        self.assertEqual(2, nested['b'])
        self.assertEqual(4, self.context['b'])