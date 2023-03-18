import pytest
import pickle

from collections import Counter

from sismic.exceptions import ExecutionError, NonDeterminismError, ConflictingTransitionsError
from sismic.code import DummyEvaluator
from sismic.interpreter import Interpreter, Event, InternalEvent
from sismic.helpers import coverage_from_trace, log_trace, run_in_background
from sismic.model import Transition, MacroStep, MicroStep, MetaEvent
from sismic import testing


class TestInterpreterWithSimple:
    @pytest.fixture()
    def interpreter(self, simple_statechart):
        interpreter = Interpreter(simple_statechart, evaluator_klass=DummyEvaluator)

        # Stabilization
        interpreter.execute_once()

        return interpreter

    def test_init(self, interpreter):
        assert interpreter.configuration == ['root', 's1']
        assert not interpreter.final

    def test_time(self, interpreter):
        assert interpreter.time == 0

        interpreter.clock.time += 10
        # No execution means no new time value
        assert interpreter.time == 0  

        interpreter.execute()
        assert interpreter.time == 10

    def test_deprecated_time(self, interpreter):
        with pytest.warns(DeprecationWarning):
            interpreter.time += 1
            assert interpreter.time == 0
            assert interpreter.clock.time == 1

    def test_queue(self, interpreter):
        interpreter.queue('e1')
        assert interpreter._select_event(consume=True) == Event('e1')

        interpreter.queue('e3')
        assert interpreter._select_event(consume=True) == Event('e3')

        interpreter.queue('e4').queue('e5')
        assert interpreter._select_event(consume=True) == Event('e4')
        assert interpreter._select_event(consume=True) == Event('e5')

        interpreter.queue('e6', 'e7', 'e8')
        assert interpreter._select_event(consume=True) == Event('e6')
        assert interpreter._select_event(consume=True) == Event('e7')
        assert interpreter._select_event(consume=True) == Event('e8')

    def test_simple_configuration(self, interpreter):
        assert interpreter.execute_once() is None  # Should do nothing!

        interpreter.queue('goto s2').execute_once()

        assert interpreter.configuration == ['root', 's2']

        interpreter.execute_once()
        assert interpreter.configuration == ['root', 's3']

    def test_simple_entered(self, interpreter):
        interpreter.queue('goto s2')
        assert interpreter.execute_once().entered_states == ['s2']

        interpreter.queue('goto final')
        assert interpreter.execute_once().entered_states == ['s3']
        assert interpreter.execute_once().entered_states == ['final']
        assert interpreter.configuration == []
        assert interpreter.final

    def test_simple_final(self, interpreter):
        interpreter.queue('goto s2').queue('goto final').execute()
        assert interpreter.final


class TestInterpreterWithInternal:
    @pytest.fixture
    def interpreter(self, internal_statechart):
        interpreter = Interpreter(internal_statechart)

        # Stabilization
        interpreter.execute_once()

        return interpreter

    def test_sent(self, interpreter):
        step = interpreter.execute_once()

        assert step.event.name == 'next'

    def test_internal_before_external(self, interpreter):
        assert interpreter.queue('not_next').execute_once().event.name == 'next'

        step = interpreter.execute_once()
        assert step.event is None
        assert step.entered_states == ['s2']

        assert interpreter.execute_once().event.name == 'not_next'

    def test_active_guard(self, interpreter):
        interpreter.execute()
        assert interpreter.final


class TestInterpreterWithFinal:
    @pytest.fixture()
    def interpreter(self, final_statechart):
        return Interpreter(final_statechart, evaluator_klass=DummyEvaluator)

    def test_not_final(self, interpreter):
        assert 'root' not in interpreter.configuration
        assert not interpreter.final

    def test_root_when_not_final(self, interpreter):
        interpreter.execute()
        assert interpreter.configuration == ['root', 'a']
        assert not interpreter.final

    def test_when_root_child_is_final(self, interpreter):
        interpreter.queue('root-final').execute()
        assert interpreter.configuration == []
        assert interpreter.final

    def test_when_root_child_is_not_final(self, interpreter):
        interpreter.queue('b').execute()
        assert interpreter.configuration == ['root', 'b']
        assert not interpreter.final

    def test_when_nested_child_is_final(self, interpreter):
        interpreter.queue('c').execute()
        assert interpreter.configuration == ['root', 'c', 'nested-final']
        assert not interpreter.final

    def test_with_parallel_states(self, interpreter):
        interpreter.queue('parallel').execute()
        assert interpreter.configuration == ['root', 'parallel', 'p1', 'p2', 'p1a', 'p2a']
        assert not interpreter.final

        interpreter.queue('p1-final').execute()
        assert interpreter.configuration == ['root', 'parallel', 'p1', 'p2', 'p1-final', 'p2a']
        assert not interpreter.final

        interpreter.queue('p2-final').execute()
        assert interpreter.configuration == ['root', 'parallel', 'p1', 'p2', 'p1-final', 'p2-final']
        assert not interpreter.final


class TestInterpreterWithNonDeterministic:
    @pytest.fixture()
    def interpreter(self, nondeterministic_statechart):
        interpreter = Interpreter(nondeterministic_statechart, evaluator_klass=DummyEvaluator)

        # Stabilization
        interpreter.execute_once()

        return interpreter

    def test_nondeterminism(self, interpreter):
        with pytest.raises(NonDeterminismError):
            interpreter.execute_once()


class TestInterpreterWithHistory:
    @pytest.fixture()
    def interpreter(self, history_statechart):
        interpreter = Interpreter(history_statechart, evaluator_klass=DummyEvaluator)

        # Stabilization
        interpreter.execute_once()

        return interpreter

    def test_memory(self, interpreter):
        interpreter.queue('next').execute_once()
        assert interpreter.configuration == ['root', 'loop', 's2']

        step = interpreter.queue('pause').execute_once()
        assert step.exited_states == ['s2', 'loop']
        assert interpreter.configuration == ['root', 'pause']

    def test_resume_memory(self, interpreter):
        interpreter.queue('next', 'pause', 'continue')
        last_step = interpreter.execute()[-1]

        assert last_step.entered_states == ['loop', 'loop.H', 's2']
        assert last_step.exited_states == ['pause', 'loop.H']
        assert interpreter.configuration == ['root', 'loop', 's2']

    def test_after_memory(self, interpreter):
        interpreter.queue('next', 'pause', 'continue', 'next', 'next').execute()

        assert interpreter.configuration == ['root', 'loop', 's1']

        interpreter.queue('pause', 'stop').execute()
        assert interpreter.final


class TestInterpreterWithDeephistory:
    @pytest.fixture()
    def interpreter(self, deep_history_statechart):
        interpreter = Interpreter(deep_history_statechart, evaluator_klass=DummyEvaluator)

        # Stabilization
        interpreter.execute_once()

        return interpreter

    def test_deep_memory(self, interpreter):
        interpreter.queue('next1', 'next2').execute()
        assert set(interpreter.configuration) == {'active', 'concurrent_processes', 'process_1',
                                                  'process_2', 'root', 's12', 's22'}

        interpreter.queue('error1').execute()
        assert interpreter.configuration == ['root', 'pause']
        assert set(interpreter._memory['active.H*']) == {'concurrent_processes', 'process_1', 'process_2',
                                                         's12', 's22'}

        interpreter.queue('continue').execute()
        assert set(interpreter.configuration) == {'active', 'concurrent_processes', 'process_1',
                                                  'process_2', 'root', 's12', 's22'}

    def test_entered_order(self, interpreter):
        interpreter.queue('next1', 'next2', 'pause')
        last_step = interpreter.execute()[-1]

        assert last_step.entered_states == ['pause']
        assert interpreter.configuration == ['root', 'pause']

        step = interpreter.queue('continue').execute_once()

        assert step.entered_states.index('active') < step.entered_states.index('active.H*')
        assert step.entered_states.index('active.H*') < step.entered_states.index('concurrent_processes')
        assert step.entered_states.index('concurrent_processes') < step.entered_states.index('process_1')
        assert step.entered_states.index('concurrent_processes') < step.entered_states.index('process_2')
        assert step.entered_states.index('process_1') < step.entered_states.index('s12')
        assert step.entered_states.index('process_2') < step.entered_states.index('s22')

        interpreter.queue('next1', 'next2').execute()
        assert 's13' in interpreter.configuration and 's23' in interpreter.configuration
        assert not interpreter.final

    def test_exited_order(self, interpreter):
        interpreter.queue('next1', 'next2', 'pause')
        last_step = interpreter.execute()[-1]

        assert last_step.exited_states == ['s12', 's22', 'process_1', 'process_2', 'concurrent_processes', 'active']
        assert interpreter.configuration == ['root', 'pause']

        step = interpreter.queue('continue').execute_once()
        assert step.exited_states == ['pause', 'active.H*']

        interpreter.queue('next1', 'next2').execute()
        assert 's13' in interpreter.configuration and 's23' in interpreter.configuration
        assert not interpreter.final


class TestInterpreterWithInfinite:
    @pytest.fixture()
    def interpreter(self, infinite_statechart):
        interpreter = Interpreter(infinite_statechart)

        # Stabilization
        interpreter.execute_once()

        return interpreter

    def test_three_steps(self, interpreter):
        assert interpreter.configuration == ['root', 's1']
        interpreter.execute_once()
        assert interpreter.configuration == ['root', 's2']
        interpreter.execute_once()
        assert interpreter.configuration == ['root', 's1']
        interpreter.execute_once()
        assert interpreter.configuration == ['root', 's2']

        # x is incremented in s1.on_entry
        assert interpreter.context['x'] == 2

    def test_auto_three_steps(self, interpreter):
        interpreter.execute(max_steps=3)
        assert interpreter.configuration == ['root', 's2']

        # x is incremented in s1.on_entry
        assert interpreter.context['x'] == 2

    def test_auto_stop(self, interpreter):
        interpreter.execute()

        assert interpreter.final
        assert interpreter.context['x'] == 100


class TestInterpreterWithParallel:
    @pytest.fixture()
    def interpreter(self, parallel_statechart):
        interpreter = Interpreter(parallel_statechart, evaluator_klass=DummyEvaluator)

        # Stabilization
        interpreter.execute_once()

        return interpreter

    def test_concurrent_transitions(self, interpreter):
        step = interpreter.queue('nextA').execute_once()

        assert interpreter.configuration == ['root', 's1', 'p1', 'p2', 'a1', 'a2']
        assert step.exited_states.index('initial1') < step.exited_states.index('initial2')
        assert step.entered_states.index('a1') < step.entered_states.index('a2')

    def test_concurrent_transitions_nested_target(self, interpreter):
        interpreter.queue('nextA', 'reset1').execute()

        assert interpreter.configuration == ['root', 's1', 'p1', 'p2', 'a2', 'initial1']

    def test_unnested_transitions(self, interpreter):
        interpreter.queue('nextA', 'nextA').execute()
        assert interpreter.configuration == ['root', 's1', 'p1', 'p2', 'a2', 'initial1']

    def test_unnested_transitions_2(self, interpreter):
        interpreter.queue('nextA', 'nextB').execute()

        assert interpreter.configuration == ['root', 's1', 'p1', 'p2', 'b1', 'b2']

    def test_conflicting_transitions(self, interpreter):
        interpreter.queue('nextA', 'nextB', 'conflict1')
        interpreter.execute_once()
        interpreter.execute_once()

        with pytest.raises(ConflictingTransitionsError):
            interpreter.execute_once()

    def test_conflicting_transitions_2(self, interpreter):
        interpreter.queue('nextA', 'nextB', 'conflict2')
        interpreter.execute_once()
        interpreter.execute_once()

        with pytest.raises(ConflictingTransitionsError):
            interpreter.execute_once()


class TestInterpreterWithNestedParallel:
    common_states = ['root', 's1', 'p1', 'p2', 'r1', 'r2', 'r3', 'r4']

    @pytest.fixture()
    def interpreter(self, nested_parallel_statechart):
        interpreter = Interpreter(nested_parallel_statechart, evaluator_klass=DummyEvaluator)

        # Stabilization
        interpreter.execute_once()

        return interpreter

    def test_initial(self, interpreter):
        assert interpreter.configuration == self.common_states + ['i1', 'i2', 'i3', 'i4']

    def test_parallel_order(self, interpreter):
        step = interpreter.queue('next').execute_once()

        assert interpreter.configuration == self.common_states + ['j1', 'j2', 'j3', 'j4']
        assert step.exited_states == ['i1', 'i2', 'i3', 'i4']
        assert step.entered_states == ['j1', 'j2', 'j3', 'j4']
        assert [t.source for t in step.transitions] == ['i1', 'i2', 'i3', 'i4']

    def test_partial_parallel_order(self, interpreter):
        interpreter.queue('next', 'click')
        interpreter.execute_once()
        step = interpreter.execute_once()

        assert interpreter.configuration == self.common_states + ['j1', 'j3', 'k2', 'k4']
        assert step.exited_states == ['j2', 'j4']
        assert step.entered_states == ['k2', 'k4']
        assert [t.source for t in step.transitions] == ['j2', 'j4']

    def test_partial_unnested_transition(self, interpreter):
        interpreter.queue('next', 'reset')
        interpreter.execute_once()
        step = interpreter.execute_once()

        assert interpreter.configuration == self.common_states + ['i1', 'i2', 'i3', 'i4']
        assert step.exited_states.index('r2') < step.exited_states.index('r4')
        assert step.exited_states.index('p1') < step.exited_states.index('p2')
        assert step.exited_states.index('r2') < step.exited_states.index('p1')
        assert step.exited_states.index('r4') < step.exited_states.index('p2')
        assert step.entered_states.index('p1') < step.entered_states.index('p2')
        assert step.entered_states.index('p1') < step.entered_states.index('r1')
        assert step.entered_states.index('p1') < step.entered_states.index('r2')
        assert step.entered_states.index('r1') < step.entered_states.index('p2')
        assert step.entered_states.index('r2') < step.entered_states.index('p2')
        assert step.entered_states.index('p2') < step.entered_states.index('r3')
        assert step.entered_states.index('p2') < step.entered_states.index('r4')
        assert [t.source for t in step.transitions] == ['r2', 'r4']

    def test_name_order(self, interpreter):
        interpreter.queue('next', 'click', 'next', 'next')
        interpreter.execute_once()
        interpreter.execute_once()
        interpreter.execute_once()

        assert interpreter.configuration == self.common_states + ['k1', 'k3', 'x', 'y']

        step = interpreter.execute_once()
        assert step.exited_states.index('k1') < step.exited_states.index('k3')
        assert step.exited_states.index('k3') < step.exited_states.index('x')
        assert step.exited_states.index('x') < step.exited_states.index('y')
        assert interpreter.configuration == self.common_states + ['k1', 'x', 'y', 'z']
        assert step.entered_states.index('k1') < step.entered_states.index('z')
        assert step.entered_states.index('z') < step.entered_states.index('x')
        assert step.entered_states.index('x') < step.entered_states.index('y')

        assert [t.source for t in step.transitions] == ['k1', 'k3', 'x', 'y']

        step = interpreter.queue('next').execute_once()

        assert step.exited_states.index('k1') < step.exited_states.index('x')
        assert step.exited_states.index('x') < step.exited_states.index('y')
        assert step.exited_states.index('y') < step.exited_states.index('z')
        assert interpreter.configuration == self.common_states + ['k1', 'x', 'y', 'z']
        assert step.entered_states.index('k1') < step.entered_states.index('x')
        assert step.entered_states.index('x') < step.entered_states.index('y')
        assert step.entered_states.index('y') < step.entered_states.index('z')

        assert [t.source for t in step.transitions] == ['k1', 'x', 'y', 'z']


class TestTransitionPriority:
    @pytest.fixture()
    def interpreter(self, priority_statechart):
        interpreter = Interpreter(priority_statechart, evaluator_klass=DummyEvaluator)
        interpreter.execute_once()
        assert interpreter.configuration == ['root', 'a']
        return interpreter

    def test_high_has_priority(self, interpreter):
        interpreter.execute_once()
        assert interpreter.configuration == ['root', 'b']
                
    def test_eventless_first(self, interpreter):
        interpreter.execute_once()
        interpreter.queue('e')
        interpreter.execute_once()
        assert interpreter.configuration == ['root', 'a']  # not ['root', 'c']

    def test_conflicting_priorities(self, interpreter):
        # Remove "high", stick with two "normal"
        for transition in interpreter._statechart.transitions:
            if transition.source == 'a' and transition.priority == 1:
                interpreter._statechart.remove_transition(transition)
                break

        with pytest.raises(NonDeterminismError):
            interpreter.execute_once()

    def test_event_high_has_priority(self, interpreter):
        # Remove automatic transitions from b
        for transition in interpreter._statechart.transitions:
            if transition.source == 'b' and transition.event is None:
                interpreter._statechart.remove_transition(transition)
                break

        interpreter.execute_once()
        interpreter.queue('e')
        interpreter.execute_once()
        assert interpreter.configuration == ['root', 'c']


class TestLogTrace:
    @pytest.fixture(autouse=True)
    def setup(self, elevator):
        self.steps = log_trace(elevator)

    def test_empty_trace(self, elevator):
        assert self.steps == []

    def test_nonempty_trace(self, elevator):
        elevator.queue('floorSelected', floor=4).execute()
        assert len(self.steps) > 0

    def test_log_content(self, elevator):
        steps = elevator.queue('floorSelected', floor=4).execute()
        assert steps == self.steps


def test_run_in_background(elevator):
    from time import sleep

    with pytest.warns(DeprecationWarning):
        task = run_in_background(elevator, 0.001)
    elevator.queue('floorSelected', floor=4)

    sleep(0.01)

    task.stop()

    assert elevator.context['current'] == 4
    assert elevator.time == 0


class TestCoverageFromTrace:
    def test_empty_trace(self):
        assert coverage_from_trace([]) == {'entered states': Counter(), 'exited states': Counter(), 'processed transitions': Counter()}

    def test_single_step(self):
        trace = [MacroStep(0, steps=[
            MicroStep(entered_states=['a', 'b', 'c'], exited_states=['b'], transition=Transition('x')),
            MicroStep(entered_states=['a', 'b'], exited_states=['c'], transition=Transition('x')),
            MicroStep(entered_states=['a']),
            MicroStep(entered_states=[])
        ])]

        expected = {
            'entered states': Counter(a=3, b=2, c=1),
            'exited states': Counter(b=1, c=1),
            'processed transitions': Counter({Transition('x'): 2})
        }

        assert coverage_from_trace(trace) == expected

    def test_multiple_steps(self):
        trace = [MacroStep(0, steps=[
            MicroStep(entered_states=['a', 'b', 'c'], exited_states=['b'], transition=Transition('x')),
            MicroStep(entered_states=['a', 'b'], exited_states=['c'],  transition=Transition('x')),
            MicroStep(entered_states=['a']),
            MicroStep(entered_states=[])
        ])]

        trace.extend(trace)

        expected = {
            'entered states': Counter(a=6, b=4, c=2),
            'exited states': Counter(b=2, c=2),
            'processed transitions': Counter({Transition('x'): 4})
        }

        assert coverage_from_trace(trace) == expected


class TestInterpreterBinding:
    @pytest.fixture()
    def interpreter(self, simple_statechart):
        i1 = Interpreter(simple_statechart, evaluator_klass=DummyEvaluator)
        i2 = Interpreter(simple_statechart, evaluator_klass=DummyEvaluator)

        # Stabilization
        i1.execute_once(), i2.execute_once()

        return i1, i2

    def test_bind(self, interpreter):
        i1, i2 = interpreter

        x = i1.bind(i2)
        assert x in i1._listeners

        i1._raise_event(InternalEvent('test'))
        assert i1._select_event(consume=False) == Event('test')
        assert isinstance(i1._select_event(consume=False), InternalEvent)
        assert i2._select_event(consume=False) == Event('test')
        assert not isinstance(i2._select_event(consume=False), InternalEvent)

    def test_bind_callable(self, interpreter):
        i1, i2 = interpreter

        x = i1.bind(i2.queue)
        assert x in i1._listeners

        i1._raise_event(InternalEvent('test'))

        assert i1._select_event(consume=False) == Event('test')
        assert isinstance(i1._select_event(consume=False), InternalEvent)
        assert i2._select_event(consume=False) == Event('test')
        assert not isinstance(i2._select_event(consume=False), InternalEvent)

    def test_metaevent(self, interpreter):
        i1, i2 = interpreter

        i1.bind(i2.queue)

        i1._raise_event(MetaEvent('test'))

        assert i1._select_event(consume=False) is None
        assert i2._select_event(consume=False) is None

    def test_event(self, interpreter):
        i1, i2 = interpreter

        i1.bind(i2.queue)

        with pytest.raises(ValueError):
            i1._raise_event(Event('test'))

        assert i1._select_event(consume=False) is None
        assert i2._select_event(consume=False) is None


def test_interpreter_is_serialisable(microwave):
    microwave.queue(
        'door_opened',
        'item_placed',
        'door_closed',
        'timer_inc',
        'timer_inc',
        'cooking_start'
        'timer_tick',
    ).execute()

    dumped = pickle.dumps(microwave)
    n_microwave = pickle.loads(dumped)

    assert microwave.configuration == n_microwave.configuration
    assert microwave.context == n_microwave.context


class TestEventQueue:
    @pytest.fixture()
    def interpreter(self, simple_statechart):
        interpreter = Interpreter(simple_statechart, evaluator_klass=DummyEvaluator)

        # Stabilization
        interpreter.execute_once()

        return interpreter

    def test_delay(self, interpreter):
        interpreter.queue('test1', delay=1)
        interpreter.queue('test2', delay=-1)
        interpreter.queue('test3', delay=0)
        
        interpreter._time += 10
        
        event = interpreter._select_event(consume=True)
        assert event == Event('test2', delay=-1)
        event = interpreter._select_event(consume=True)
        assert event == Event('test3', delay=0)
        event = interpreter._select_event(consume=True)
        assert event == Event('test1', delay=1)

    def test_consume_order(self, interpreter):
        interpreter.queue('test3', delay=2)
        interpreter.queue('test1', delay=0)
        interpreter.queue('test2', delay=1)
        interpreter.queue('test4', delay=2)
        interpreter.queue('test5', delay=3)
                
        event = interpreter._select_event(consume=True)
        assert event == Event('test1', delay=0)
        assert interpreter._select_event(consume=True) is None
        
        interpreter._time = 1
        event = interpreter._select_event(consume=True)
        assert event == Event('test2', delay=1)
        assert interpreter._select_event(consume=True) is None
        
        interpreter._time = 2
        event = interpreter._select_event(consume=True)
        assert event == Event('test3', delay=2)
        event = interpreter._select_event(consume=True)
        assert event == Event('test4', delay=2)
        assert interpreter._select_event(consume=True) is None

    def test_internal_first(self, interpreter):
        interpreter.queue('test1', delay=0)
        interpreter._raise_event(InternalEvent('test2'))
        interpreter.queue('test3', delay=2)
        
        event = interpreter._select_event()
        assert isinstance(event, InternalEvent) and event == Event('test2')

        interpreter._time = 2
        event = interpreter._select_event(consume=True)
        assert isinstance(event, InternalEvent) and event == Event('test2')

        interpreter._raise_event(InternalEvent('test4'))
        # Queue is (0, test1) ; (2, test3) ; (2, test4) but test4 is internal
        
        event = interpreter._select_event(consume=True)
        assert isinstance(event, InternalEvent) and event == Event('test4')
        event = interpreter._select_event(consume=True)
        assert event == Event('test1', delay=0)
        event = interpreter._select_event(consume=True)
        assert event == Event('test3', delay=2)
        
        
    