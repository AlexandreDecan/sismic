import unittest
from unittest.mock import MagicMock
from sismic import code
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


class PythonEvaluatorTests(unittest.TestCase):
    def setUp(self):
        context = {
            'x': 1,
            'y': 2,
            'z': 3
        }

        interpreter = MagicMock(name='Interpreter')
        interpreter.time = MagicMock(return_value=0)
        interpreter.queue = MagicMock(return_value=None)
        interpreter.configuration = MagicMock(return_value=[])

        self.evaluator = code.PythonEvaluator(interpreter=interpreter, initial_context=context)
        self.interpreter = interpreter

    def test_condition(self):
        self.assertTrue(self.evaluator._evaluate_code('True'))
        self.assertFalse(self.evaluator._evaluate_code('False'))
        self.assertTrue(self.evaluator._evaluate_code('1 == 1'))
        self.assertTrue(self.evaluator._evaluate_code('x == 1'))
        with self.assertRaises(Exception):
            self.evaluator._evaluate_code('a')

    def test_condition_on_event(self):
        self.assertTrue(self.evaluator._evaluate_code('event.data[\'a\'] == 1', {'event': Event('test', a=1)}))
        self.assertTrue(self.evaluator._evaluate_code('event.name == \'test\'', {'event': Event('test')}))

    def test_execution(self):
        self.evaluator._execute_code('a = 1')
        self.assertEqual(self.evaluator.context['a'], 1)
        self.evaluator._execute_code('x = 2')
        self.assertEqual(self.evaluator.context['x'], 2)

    def test_invalid_condition(self):
        with self.assertRaises(exceptions.CodeEvaluationError):
            self.evaluator._evaluate_code('x.y')

    def test_invalid_action(self):
        with self.assertRaises(exceptions.CodeEvaluationError):
            self.evaluator._execute_code('x = x.y')

    def test_send(self):
        self.evaluator._execute_code('send("hello")')
        self.interpreter.queue.assert_called_with(InternalEvent('hello'))