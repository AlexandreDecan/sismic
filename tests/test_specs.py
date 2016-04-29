import unittest
from sismic.testing.specs import declared_variables, code_for, infer_types, sent_events, attributes_for
from sismic.io import import_from_yaml


class DeclaredVariablesTests(unittest.TestCase):
    def test_empty_code(self):
        self.assertEqual(declared_variables('').items(), {}.items())

    def test_single_assignment(self):
        codes = [
            ('x = 1', {'x': '1'}),
            ('x = y', {'x': 'y'}),
            ('x = x', {'x': 'x'}),
            ('x = lambda z: p(1,2,3) + 4', {'x': 'lambda z: p(1,2,3) + 4'}),
        ]
        for code, result in codes:
            self.assertEqual(declared_variables(code), result)

    def test_commented_assignment(self):
        self.assertEqual(declared_variables('# x = 1'), {})

    def test_multiple_assignments(self):
        self.assertEqual(declared_variables('x = y = 1'), {'x': 'y = 1', 'y': '1'})

    def test_invalid_assignment(self):
        codes = [
            'x =',
            'x = @',
            'x = #',
        ]
        for code in codes:
            with self.assertRaises(ValueError):
                self.assertEqual(declared_variables(code), {})

    def test_tuple_assignment(self):
        codes = [
            ('x = 1, 2', {'x': '1, 2'}),
            ('x, y = 1, 2', {'x': '1', 'y': '2'}),
            ('x, y, z = 1, 2, 3', {'x': '1', 'y': '2', 'z': '3'}),
        ]
        for code, result in codes:
            self.assertEqual(declared_variables(code), result)


class CodeForTests(unittest.TestCase):
    def setUp(self):
        with open('docs/examples/elevator.yaml') as f:
            self.sc = import_from_yaml(f)

    def test_statechart_code(self):
        self.assertEqual(code_for(self.sc, self.sc), [self.sc.preamble])

    def test_composition(self):
        state = self.sc.state_for('movingUp')
        code = code_for(self.sc, state)
        self.assertEqual(code[0], self.sc.preamble)
        self.assertEqual(code[1], state.on_entry)

    def test_transition(self):
        transition = self.sc.transitions_from('floorSelecting')[0]
        code = code_for(self.sc, transition)
        self.assertEqual(code[0], self.sc.preamble)
        self.assertEqual(code[1], transition.action)


class InferTypesTest(unittest.TestCase):
    base = {
        '__builtins__': 'None',
        '__doc__': 'builtins.str',
        '__file__': 'builtins.str',
        '__name__': 'builtins.str',
        '__package__': 'builtins.str',
    }

    def test_empty(self):
        code = ''
        values = {}

        values.update(self.base)
        self.assertDictEqual(infer_types(code), values)

    def test_simple(self):
        code = 'x = 1'
        values = {'x': 'builtins.int'}

        values.update(self.base)
        self.assertDictEqual(infer_types(code), values)

    def test_invalid_python(self):
        with self.assertRaises(ValueError):
            _ = infer_types('@#@M%pqŝ')

    def test_impossible_inference(self):
        with self.assertRaises(ValueError):
            _ = infer_types('x = None\nx.a = 1')

    def test_incompatible_types(self):
        with self.assertRaises(ValueError):
            _ = infer_types('x = 1\ny = "hello"\nz = x + y')

    def test_fake_initial_context(self):
        code = 'x = locals().get("x", None)'
        values = {'x': 'Any'}

        values.update(self.base)
        self.assertDictEqual(infer_types(code), values)


class SentEventsTests(unittest.TestCase):
    def make_call(self, name, **kwargs):
        if kwargs:
            param = ', ' + ', '.join(['%s=%s' % (k, v) for k, v in kwargs.items()])
        else:
            param = ''
        return 'send(\'%s\'%s)' % (name, param)

    def test_simple(self):
        call = self.make_call('a')
        self.assertDictEqual(sent_events(call), {'a': [{}]})

    def test_arguments(self):
        call = self.make_call('a', x=1, y=2)
        self.assertDictEqual(sent_events(call), {'a': [{'x': '1', 'y': '2'}]})

    def test_multiple_calls(self):
        call_1 = self.make_call('a', x=1)
        call_2 = self.make_call('a', y=2)
        self.assertDictEqual(sent_events(call_1 + ', ' + call_2),
                             {'a': [{'x': '1'}, {'y': '2'}]})

    def test_multiple_events(self):
        call_1 = self.make_call('a', x=1)
        call_2 = self.make_call('b', x=2)
        self.assertDictEqual(sent_events(call_1 + ', ' + call_2),
                             {'a': [{'x': '1'}], 'b': [{'x': '2'}]})


class AttributesForTests(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(attributes_for('x.y = a.b', 'a'), {'b'})
        self.assertEqual(attributes_for('x.y = a.b', 'x'), {'y'})
        self.assertEqual(attributes_for('x.y = a.b', 'y'), set())
        self.assertEqual(attributes_for('x.y = x.z', 'x'), {'y', 'z'})

    def test_composite(self):
        self.assertEqual(attributes_for('x.y.z', 'y'), set())
        self.assertEqual(attributes_for('x.y.z', 'x.y'), set())
        self.assertEqual(attributes_for('x.y.z', 'x'), {'y'})
