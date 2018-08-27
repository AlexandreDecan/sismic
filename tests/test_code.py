import pytest

from sismic import code
from sismic.code.python import FrozenContext
from sismic.exceptions import CodeEvaluationError
from sismic.interpreter import Event, InternalEvent, MetaEvent


def test_dummy_evaluator(mocker):
        interpreter = mocker.MagicMock(name='interpreter')
        evaluator = code.DummyEvaluator(interpreter=interpreter)

        assert evaluator._evaluate_code('blablabla') is True
        assert evaluator._evaluate_code('False') is True
        assert evaluator.context == {}

        assert evaluator._execute_code('blablabla') == []
        assert evaluator.context == {}


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

    def test_setdefault(self, evaluator):
        evaluator._execute_code('setdefault("x", 2)')
        assert evaluator.context['x'] == 1

        evaluator._execute_code('b = setdefault("a", 0)')
        assert evaluator.context['a'] == 0
        assert evaluator.context['b'] == 0

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

    def test_send_with_delay(self, evaluator):
        events = evaluator._execute_code('send("hello", delay=5)')
        event = events[0]
        assert event == Event('hello', delay=5)
        
    def test_notify(self, evaluator):
        events = evaluator._execute_code('notify("hello", x=1, y="world")')
        assert events == [MetaEvent('hello', x=1, y='world')]

    def test_no_event_raised_by_preamble(self, interpreter, evaluator):
        interpreter.statechart.preamble = 'send("test")'
        with pytest.raises(CodeEvaluationError):
            evaluator.execute_statechart(interpreter.statechart)

    def test_add_variable_in_context(self, evaluator):
        evaluator._execute_code('a = 1\nassert a == 1', additional_context=evaluator.context)
        assert evaluator._evaluate_code('a == 1', additional_context={'a': 1})

    @pytest.mark.xfail(reason='http://stackoverflow.com/questions/32894942/listcomp-unable-to-access-locals-defined-in-code-called-by-exec-if-nested-in-fun and possibly fixed with https://bugs.python.org/issue3692')
    def test_access_outer_scope(self, evaluator):
        evaluator._execute_code('d = [x for x in range(10) if x != a]', additional_context={'a': 1})
