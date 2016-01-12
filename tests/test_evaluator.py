import unittest
from sismic import code
from sismic.model import Event


class PythonEvaluatorTests(unittest.TestCase):
    def setUp(self):
        context = {
            'x': 1,
            'y': 2,
            'z': 3
        }
        self.e = code.PythonEvaluator(initial_context=context)

    def test_condition(self):
        self.assertTrue(self.e._evaluate_code('True'))
        self.assertFalse(self.e._evaluate_code('False'))
        self.assertTrue(self.e._evaluate_code('1 == 1'))
        self.assertTrue(self.e._evaluate_code('x == 1'))
        with self.assertRaises(Exception):
            self.e._evaluate_code('a')

    def test_condition_on_event(self):
        self.assertTrue(self.e._evaluate_code('event.data[\'a\'] == 1', {'event': Event('test', a=1)}))
        self.assertTrue(self.e._evaluate_code('event.name == \'test\'', {'event': Event('test')}))

    def test_execution(self):
        self.e._execute_code('a = 1')
        self.assertEqual(self.e.context['a'], 1)
        self.e._execute_code('x = 2')
        self.assertEqual(self.e.context['x'], 2)

    def test_invalid_condition(self):
        with self.assertRaises(AttributeError):
            self.e._evaluate_code('x.y')

    def test_invalid_action(self):
        with self.assertRaises(AttributeError):
            self.e._execute_code('x = x.y')