import unittest
from sismic import evaluator
from sismic.model import Event


class PythonEvaluatorTests(unittest.TestCase):
    def setUp(self):
        context = {
            'x': 1,
            'y': 2,
            'z': 3
        }
        self.e = evaluator.PythonEvaluator(None, context)

    def test_condition(self):
        self.assertTrue(self.e._evaluate_code(None, 'True'))
        self.assertFalse(self.e._evaluate_code(None, 'False'))
        self.assertTrue(self.e._evaluate_code(None, '1 == 1'))
        self.assertTrue(self.e._evaluate_code(None, 'x == 1'))
        with self.assertRaises(Exception):
            self.e._evaluate_code(None, 'a')

    def test_condition_on_event(self):
        self.assertTrue(self.e._evaluate_code(None, 'event.data[\'a\'] == 1', Event('test', {'a': 1})))
        self.assertTrue(self.e._evaluate_code(None, 'event.name == \'test\'', Event('test')))

    def test_execution(self):
        self.e._execute_code(None, 'a = 1')
        self.assertEqual(self.e.context['a'], 1)
        self.e._execute_code(None, 'x = 2')
        self.assertEqual(self.e.context['x'], 2)

    def test_invalid_condition(self):
        with self.assertRaises(AttributeError):
            self.e._evaluate_code(None, 'x.y')

    def test_invalid_action(self):
        with self.assertRaises(AttributeError):
            self.e._execute_code(None, 'x = x.y')