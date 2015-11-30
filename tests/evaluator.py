import unittest
from pyss import evaluator
from pyss.statemachine import Event


class PythonEvaluatorTests(unittest.TestCase):
    def setUp(self):
        context = {
            'x': 1,
            'y': 2,
            'z': 3
        }
        self.e = evaluator.PythonEvaluator(context)

    def test_condition(self):
        self.assertTrue(self.e.evaluate_condition('True'))
        self.assertFalse(self.e.evaluate_condition('False'))
        self.assertTrue(self.e.evaluate_condition('1 == 1'))
        self.assertTrue(self.e.evaluate_condition('x == 1'))
        try:
            self.assertTrue(self.e.evaluate_condition('a'))
        except Exception as e:
            pass
        else:
            self.assertTrue(False, 'invalid code should fail!')

    def test_condition_on_event(self):
        self.assertTrue(self.e.evaluate_condition('event.data[\'a\'] == 1', Event('test', {'a': 1})))
        self.assertTrue(self.e.evaluate_condition('event.name == \'test\'', Event('test')))

    def test_execution(self):
        self.e.execute_action('a = 1')
        self.assertEqual(self.e.context['a'], 1)
        self.e.execute_action('x = 2')
        self.assertEqual(self.e.context['x'], 2)

    def test_execution_fire_event(self):
        events = self.e.execute_action('fire_event(Event(\'test\'))')
        self.assertEqual(events, [Event('test')])

