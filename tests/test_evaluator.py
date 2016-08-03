import unittest
from unittest.mock import MagicMock
from sismic import code
from sismic.model import Event, InternalEvent
from sismic.code.python import Context, FrozenContext
from sismic.exceptions import CodeEvaluationError, SequentialConditionError

from sismic.io import import_from_yaml
from sismic.interpreter import Interpreter


class DummyEvaluatorTests(unittest.TestCase):
    def setUp(self):
        interpreter = MagicMock(name='interpreter')
        self.evaluator = code.DummyEvaluator(interpreter=interpreter)

    def test_condition(self):
        self.assertTrue(self.evaluator._evaluate_code('blablabla'))
        self.assertTrue(self.evaluator._evaluate_code('False'))

        self.assertEqual(self.evaluator.context, {})

    def test_execution(self):
        self.assertEqual(self.evaluator._execute_code('blablabla'), [])

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

        # Parent context is independent from nested ones
        self.context['b'] = 4
        self.assertEqual(2, nested_1['b'])
        self.assertEqual(3, nested_2['b'])
        self.assertEqual(4, self.context['b'])


class PythonEvaluatorTests(unittest.TestCase):
    def setUp(self):
        context = {
            'x': 1,
            'y': 2,
            'z': 3
        }

        interpreter = MagicMock(name='Interpreter')
        interpreter.time = 0
        interpreter.queue = MagicMock(return_value=None)
        interpreter.statechart = MagicMock()
        interpreter.configuration = []

        self.evaluator = code.PythonEvaluator(interpreter, initial_context=context)
        self.interpreter = interpreter

    def test_condition(self):
        self.assertTrue(self.evaluator._evaluate_code('True'))
        self.assertFalse(self.evaluator._evaluate_code('False'))
        self.assertTrue(self.evaluator._evaluate_code('1 == 1'))
        self.assertTrue(self.evaluator._evaluate_code('x == 1'))
        with self.assertRaises(Exception):
            self.evaluator._evaluate_code('a')

    def test_condition_on_event(self):
        self.assertTrue(self.evaluator._evaluate_code('event.data[\'a\'] == 1', additional_context={'event': Event('test', a=1)}))
        self.assertTrue(self.evaluator._evaluate_code('event.name == \'test\'', additional_context={'event': Event('test')}))

    def test_execution(self):
        self.evaluator._execute_code('a = 1')
        self.assertEqual(self.evaluator.context['a'], 1)
        self.evaluator._execute_code('x = 2')
        self.assertEqual(self.evaluator.context['x'], 2)

    def test_invalid_condition(self):
        with self.assertRaises(CodeEvaluationError):
            self.evaluator._evaluate_code('x.y')

    def test_invalid_action(self):
        with self.assertRaises(CodeEvaluationError):
            self.evaluator._execute_code('x = x.y')

    def test_send(self):
        events = self.evaluator._execute_code('send("hello")')
        self.assertEqual(events, [InternalEvent('hello')])

    def test_add_variable_in_context(self):
        self.evaluator._execute_code('a = 1\nassert a == 1', context=self.evaluator.context)
        self.assertTrue(self.evaluator._evaluate_code('a == 1', context={'a': 1}))

    @unittest.skip('http://stackoverflow.com/questions/32894942/listcomp-unable-to-access-locals-defined-in-code-called-by-exec-if-nested-in-fun')
    def test_access_outer_scope(self):
        self.evaluator._execute_code('d = [x for x in range(10) if x!=a]', context=Context({'a': 1}))


class PythonEvaluatorNestedContextTests(unittest.TestCase):
    def setUp(self):
        statechart = """
        statechart:
          name: test
          preamble: x = y = 1
          root state:
            name: root
            initial: s1
            states:
             - name: s1
               on entry: x, z = 2, 1
               transitions:
                - target: s2
                  guard: y == 1
                  action: a, z, y = 2, 2, 2
             - name: s2
        """
        sc = import_from_yaml(statechart)
        self.intp = Interpreter(sc)

    def test_initialization(self):
        self.assertEqual(self.intp.context.get('x'), 1)
        self.assertEqual(self.intp.context.get('y'), 1)
        with self.assertRaises(KeyError):
            _ = self.intp.context['z']
        with self.assertRaises(KeyError):
            _ = self.intp.context['a']

    def test_global_context(self):
        self.intp.execute()

        self.assertEqual(self.intp.context.get('x'), 2)
        self.assertEqual(self.intp.context.get('y'), 2)
        with self.assertRaises(KeyError):
            _ = self.intp.context['z']
        with self.assertRaises(KeyError):
            _ = self.intp.context['a']

    def test_nested_context(self):
        self.intp.execute()

        s1 = self.intp._evaluator.context_for('s1')
        self.assertEqual(s1['x'], 2)
        self.assertEqual(s1['y'], 2)
        self.assertEqual(s1['z'], 2)
        with self.assertRaises(KeyError):
            _ = s1['a']


class PythonEvaluatorSequenceConditionTests(unittest.TestCase):
    def setUp(self):
        self.sc = import_from_yaml("""
        statechart:
          name: test contract
          root state:
            name: root
            on entry: x = 1
            initial: s0
            states:
             - name: s0
               initial: s1
               transitions:
               - event: end
                 target: root
               states:
               - name: s1
                 transitions:
                   - target: s2
                     action: x = 2
                     event: e
               - name: s2
        """)

        self.root = self.sc.state_for('root')  # Will never be exited
        self.s0 = self.sc.state_for('s0')  # Will be exited on "end"
        self.s1 = self.sc.state_for('s1')  # Entered, and then exited on e.
        self.s2 = self.sc.state_for('s2')  # Entered when e
        self.intp = Interpreter(self.sc)

    def test_single_condition(self):
        self.root.sequences.append('"True"')
        self.intp.execute()

    def test_access_context(self):
        self.root.sequences.append('"x == 1"')
        self.intp.execute()

    def test_access_nested_context(self):
        self.s0.sequences.append('"x == 1" -> "x == 2"')
        self.intp.queue(Event('e')).queue(Event('end'))
        self.intp.execute()

    def test_fails_fast(self):
        self.s0.sequences.append('Failure')
        with self.assertRaises(SequentialConditionError):
            self.intp.execute()

    def test_fails_on_exit(self):
        self.s0.sequences.append('"x == 1" -> "x == 2" -> "x == 3"')
        self.intp.queue(Event('e'))
        self.intp.execute()
        self.intp.queue(Event('end'))
        with self.assertRaises(SequentialConditionError):
            self.intp.execute()

