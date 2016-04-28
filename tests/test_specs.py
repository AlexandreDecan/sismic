import unittest
from sismic.testing.specs import declared_variables, code_for, infer_types
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
        values = {'x': 'builtins_int'}

        values.update(self.base)
        self.assertDictEqual(infer_types(code), values)

    def test_invalid_python(self):
        with self.assertRaises(ValueError):
            _ = infer_types('@#@M%pqŝ')

    def test_impossible_inference(self):
        with self.assertRaises(ValueError):
            _ = infer_types('x = None\nx.a = 1')