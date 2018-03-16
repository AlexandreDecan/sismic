import pytest

from sismic import code
from sismic.code.python import Context, FrozenContext
from sismic.exceptions import CodeEvaluationError
from sismic.interpreter import Interpreter, Event, InternalEvent
from sismic.io import import_from_yaml


def test_dummy_evaluator(mocker):
        interpreter = mocker.MagicMock(name='interpreter')
        evaluator = code.DummyEvaluator(interpreter=interpreter)

        assert evaluator._evaluate_code('blablabla') is True
        assert evaluator._evaluate_code('False') is True
        assert evaluator.context == {}

        assert evaluator._execute_code('blablabla') == []
        assert evaluator.context == {}


class TestNestedContext:
    @pytest.fixture
    def context(self):
        return Context()

    def test_empty(self, context):
        assert len(context) == 0

    def test_insert_root(self, context):
        context['a'] = 1
        assert len(context) == 1
        assert context['a'] == 1

    def test_delete_root(self, context):
        context['a'] = 1
        del context['a']
        assert len(context) == 0

    def test_insert_nested(self, context):
        nested = context.new_child()
        nested['a'] = 1
        assert nested['a'] == 1
        assert len(context.map) == 0
        assert len(nested.map) == 1

    def test_update_nested(self, context):
        nested_1 = context.new_child()
        nested_2 = context.new_child()

        # Nested variable is not accessible in parent or sibling
        nested_2['c'] = 1
        with pytest.raises(KeyError):
            _ = context['c']
        with pytest.raises(KeyError):
            _ = nested_1['c']
        assert nested_2['c'] == 1

        # Variable is propagated to nested states
        context['a'] = 1
        assert context['a'] == 1
        assert nested_1['a'] == 1
        assert nested_2['a'] == 1

        # Siblings have separate context
        nested_1['b'] = 2
        nested_2['b'] = 3
        assert nested_1['b'] == 2
        assert nested_2['b'] == 3

        # Nested contexts can affect parent context
        nested_1['a'] = 3
        assert context['a'] == 3
        assert nested_2['a'] == 3
        assert nested_2['a'] == 3

        nested_2['a'] = 4
        assert context['a'] == 4
        assert nested_1['a'] == 4
        assert nested_2['a'] == 4

        # Parent context is independent from nested ones
        context['b'] = 4
        assert nested_1['b'] == 2
        assert nested_2['b'] == 3
        assert context['b'] == 4


def test_frozen_context():
    context = {'a': 1, 'b': 2}

    freeze = FrozenContext(context)
    assert len(freeze) == 2
    assert freeze.a == 1
    assert freeze.b == 2

    context['a'] = 2
    assert freeze.a == 1


class TestPythonEvaluator:
    @pytest.fixture
    def evaluator(self, mocker):
        context = {
            'x': 1,
            'y': 2,
            'z': 3
        }

        interpreter = mocker.MagicMock(name='Interpreter')
        interpreter.time = 0
        interpreter.queue = mocker.MagicMock(return_value=None)
        interpreter.statechart = mocker.MagicMock()
        interpreter.configuration = []

        return code.PythonEvaluator(interpreter, initial_context=context)

    @pytest.fixture
    def interpreter(self, evaluator):
        return evaluator._interpreter

    def test_condition(self, evaluator):
        assert evaluator._evaluate_code('True')
        assert not evaluator._evaluate_code('False')
        assert evaluator._evaluate_code('1 == 1')
        assert evaluator._evaluate_code('x == 1')
        with pytest.raises(CodeEvaluationError):
            evaluator._evaluate_code('a')

    def test_condition_on_event(self, evaluator):
        assert evaluator._evaluate_code('event.data[\'a\'] == 1', additional_context={'event': Event('test', a=1)})
        assert evaluator._evaluate_code('event.name == \'test\'', additional_context={'event': Event('test')})

    def test_execution(self, evaluator):
        evaluator._execute_code('a = 1')
        assert evaluator.context['a'] == 1
        evaluator._execute_code('x = 2')
        assert evaluator.context['x'] == 2

    def test_invalid_condition(self, evaluator):
        with pytest.raises(CodeEvaluationError):
            evaluator._evaluate_code('x.y')

    def test_invalid_action(self, evaluator):
        with pytest.raises(CodeEvaluationError):
            evaluator._execute_code('x = x.y')

    def test_send(self, evaluator):
        events = evaluator._execute_code('send("hello")')
        assert events == [InternalEvent('hello')]

    def test_no_event_raised_by_preamble(self, interpreter, evaluator):
        interpreter.statechart.preamble = 'send("test")'
        with pytest.raises(CodeEvaluationError):
            evaluator.execute_statechart(interpreter.statechart)

    def test_add_variable_in_context(self, evaluator):
        evaluator._execute_code('a = 1\nassert a == 1', context=evaluator.context)
        assert evaluator._evaluate_code('a == 1', context={'a': 1})

    @pytest.mark.skip('http://stackoverflow.com/questions/32894942/listcomp-unable-to-access-locals-defined-in-code-called-by-exec-if-nested-in-fun')
    def test_access_outer_scope(self, evaluator):
        evaluator._execute_code('d = [x for x in range(10) if x!=a]', context=Context({'a': 1}))


class TestPythonEvaluatorWithNestedContext:
    @pytest.fixture
    def interpreter(self):
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

        return Interpreter(import_from_yaml(statechart))

    def test_initialization(self, interpreter):
        assert interpreter.context.get('x') == 1
        assert interpreter.context.get('y') == 1

        with pytest.raises(KeyError):
            _ = interpreter.context['z']

        with pytest.raises(KeyError):
            _ = interpreter.context['a']

    def test_global_context(self, interpreter):
        interpreter.execute()

        assert interpreter.context.get('x') == 2
        assert interpreter.context.get('y') == 2

        with pytest.raises(KeyError):
            _ = interpreter.context['z']

        with pytest.raises(KeyError):
            _ = interpreter.context['a']

    def test_nested_context(self, interpreter):
        interpreter.execute()

        context = interpreter._evaluator.context_for('s1')
        assert context.get('x') == 2
        assert context.get('y') == 2
        assert context.get('z') == 2

        with pytest.raises(KeyError):
            _ = context['a']

