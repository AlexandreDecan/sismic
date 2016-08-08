import unittest
from sismic import io
from sismic.interpreter import Interpreter
from sismic.interpreter.helpers import run_in_background, log_trace, coverage_from_trace
from sismic import exceptions
from sismic.code import DummyEvaluator
from sismic.model import Event, InternalEvent, MacroStep, MicroStep, Transition

from collections import Counter


class LogTraceTests(unittest.TestCase):
    def setUp(self):
        with open('docs/examples/elevator/elevator.yaml') as f:
            sc = io.import_from_yaml(f)
        self.tested = Interpreter(sc)
        self.steps = log_trace(self.tested)

    def test_empty_trace(self):
        self.assertEqual(self.steps, [])

    def test_nonempty_trace(self):
        self.tested.queue(Event('floorSelected', floor=4)).execute()
        self.assertTrue(len(self.steps) > 0)

    def test_log_content(self):
        self.tested.queue(Event('floorSelected', floor=4))
        steps = self.tested.execute()
        self.assertSequenceEqual(self.steps, steps)


class RunInBackgroundTests(unittest.TestCase):
    def test_run_in_background(self):
        with open('tests/yaml/simple.yaml') as f:
            sc = io.import_from_yaml(f)
        interpreter = Interpreter(sc)
        task = run_in_background(interpreter, 0.001)
        interpreter.queue(Event('goto s2'))
        interpreter.queue(Event('goto final'))
        task.join()
        self.assertTrue(interpreter.final)


class CoverageFromTraceTests(unittest.TestCase):
    def test_empty_trace(self):
        self.assertEqual(coverage_from_trace([]), (Counter(), Counter()))

    def test_single_step(self):
        trace = [MacroStep(0, steps=[
            MicroStep(entered_states=['a', 'b', 'c'], transition=Transition('x')),
            MicroStep(entered_states=['a', 'b'], transition=Transition('x')),
            MicroStep(entered_states=['a']),
            MicroStep(entered_states=[])
        ])]
        self.assertEqual(coverage_from_trace(trace), (Counter(a=3, b=2, c=1), Counter({Transition('x'): 2})))

    def test_multiple_steps(self):
        trace = [MacroStep(0, steps=[
            MicroStep(entered_states=['a', 'b', 'c'], transition=Transition('x')),
            MicroStep(entered_states=['a', 'b'], transition=Transition('x')),
            MicroStep(entered_states=['a']),
            MicroStep(entered_states=[])
        ])]

        trace.extend(trace)
        self.assertEqual(coverage_from_trace(trace), (Counter(a=6, b=4, c=2), Counter({Transition('x'): 4})))


class SimulatorSimpleTests(unittest.TestCase):
    def setUp(self):
        with open('tests/yaml/simple.yaml') as f:
            sc = io.import_from_yaml(f)
        self.interpreter = Interpreter(sc, evaluator_klass=DummyEvaluator)
        # Stabilization
        self.interpreter.execute_once()

    def test_init(self):
        self.assertEqual(self.interpreter.configuration, ['root', 's1'])
        self.assertFalse(self.interpreter.final)

    def test_queue(self):
        self.interpreter.queue(Event('e1'))
        self.assertEqual(self.interpreter._select_event(), Event('e1'))

        self.interpreter.queue(InternalEvent('e1'))
        self.assertEqual(self.interpreter._select_event(), InternalEvent('e1'))

        with self.assertRaises(ValueError):
            self.interpreter.queue('e1')

    def test_simple_configuration(self):
        self.interpreter.execute_once()  # Should do nothing!
        self.assertEqual(self.interpreter.configuration, ['root', 's1'])
        self.interpreter.queue(Event('goto s2'))
        self.interpreter.execute_once()
        self.assertEqual(self.interpreter.configuration, ['root', 's2'])
        self.interpreter.execute_once()
        self.assertEqual(self.interpreter.configuration, ['root', 's3'])

    def test_simple_entered(self):
        self.interpreter.queue(Event('goto s2'))
        self.assertEqual(self.interpreter.execute_once().entered_states, ['s2'])
        self.interpreter.queue(Event('goto final'))
        self.assertEqual(self.interpreter.execute_once().entered_states, ['s3'])
        self.assertEqual(self.interpreter.execute_once().entered_states, ['final'])
        self.assertEqual(self.interpreter.configuration, [])
        self.assertTrue(self.interpreter.final)

    def test_simple_final(self):
        self.interpreter.queue(Event('goto s2')).queue(Event('goto final'))
        self.interpreter.execute()
        self.assertTrue(self.interpreter.final)


class InternalTests(unittest.TestCase):
    def setUp(self):
        with open('tests/yaml/internal.yaml') as f:
            self.sc = io.import_from_yaml(f)
        self.interpreter = Interpreter(self.sc)
        # Stabilization
        self.interpreter.execute_once()

    def testInternalSent(self):
        step = self.interpreter.execute_once()
        self.assertEqual(step.event.name, 'next')

    def testInternalBeforeExternal(self):
        self.interpreter.queue(Event('not_next'))
        step = self.interpreter.execute_once()
        self.assertEqual(step.event.name, 'next')

        step = self.interpreter.execute_once()
        self.assertEqual(step.event, None)
        self.assertEqual(step.entered_states, ['s2'])

        step = self.interpreter.execute_once()
        self.assertEqual(step.event.name, 'not_next')

    def testActiveGuard(self):
        self.interpreter.execute()
        self.assertTrue(self.interpreter.final)


class SimulatorNonDeterminismTests(unittest.TestCase):
    def test_nondeterminism(self):
        with open('tests/yaml/nondeterministic.yaml') as f:
            sc = io.import_from_yaml(f)
        interpreter = Interpreter(sc, evaluator_klass=DummyEvaluator)
        # Stabilization
        interpreter.execute_once()

        with self.assertRaises(exceptions.NonDeterminismError):
            interpreter.execute_once()


class SimulatorHistoryTests(unittest.TestCase):
    def setUp(self):
        with open('tests/yaml/history.yaml') as f:
            sc = io.import_from_yaml(f)
        self.interpreter = Interpreter(sc, evaluator_klass=DummyEvaluator)
        # Stabilization
        self.interpreter.execute_once()

    def test_memory(self):
        self.interpreter.queue(Event('next')).execute_once()
        self.assertEqual(sorted(self.interpreter.configuration), ['loop', 'root', 's2'])

        step = self.interpreter.queue(Event('pause')).execute_once()
        self.assertEqual(step.exited_states, ['s2', 'loop'])
        self.assertEqual(sorted(self.interpreter.configuration), ['pause', 'root'])

    def test_resume_memory(self):
        self.interpreter.queue(Event('next')).queue(Event('pause')).queue(Event('continue'))
        steps = self.interpreter.execute()
        step = steps[-1]

        self.assertEqual(step.entered_states, ['loop', 'loop.H', 's2'])
        self.assertEqual(step.exited_states, ['pause', 'loop.H'])
        self.assertEqual(sorted(self.interpreter.configuration), ['loop', 'root', 's2'])

    def test_after_memory(self):
        self.interpreter.queue(Event('next')).queue(Event('pause')).queue(Event('continue'))
        self.interpreter.queue(Event('next')).queue(Event('next'))
        self.interpreter.execute()
        self.assertEqual(sorted(self.interpreter.configuration), ['loop', 'root', 's1'])

        self.interpreter.queue(Event('pause')).queue(Event('stop'))
        self.interpreter.execute()
        self.assertTrue(self.interpreter.final)


class SimulatorDeepHistoryTests(unittest.TestCase):
    def setUp(self):
        with open('tests/yaml/deep_history.yaml') as f:
            sc = io.import_from_yaml(f)
        self.interpreter = Interpreter(sc, evaluator_klass=DummyEvaluator)
        # Stabilization
        self.interpreter.execute_once()

    def test_deep_memory(self):
        self.interpreter.queue(Event('next1')).queue(Event('next2'))
        self.interpreter.execute()
        self.assertEqual(sorted(self.interpreter.configuration), ['active', 'concurrent_processes', 'process_1', 'process_2', 'root', 's12', 's22'])

        self.interpreter.queue(Event('error1'))
        self.interpreter.execute()
        self.assertEqual(self.interpreter.configuration, ['root', 'pause'])
        self.assertEqual(sorted(self.interpreter._memory['active.H*']), ['concurrent_processes', 'process_1', 'process_2', 's12', 's22'])

        self.interpreter.queue(Event('continue'))
        self.interpreter.execute()
        self.assertEqual(sorted(self.interpreter.configuration), ['active', 'concurrent_processes', 'process_1',
                                                           'process_2', 'root', 's12', 's22'])

    def test_entered_order(self):
        self.interpreter.queue(Event('next1')).queue(Event('next2')).queue(Event('pause'))
        step = self.interpreter.execute()[-1]

        self.assertEqual(step.entered_states, ['pause'])
        self.assertEqual(sorted(self.interpreter.configuration), ['pause', 'root'])

        step = self.interpreter.queue(Event('continue')).execute_once()
        self.assertTrue(step.entered_states.index('active') < step.entered_states.index('active.H*'))
        self.assertTrue(step.entered_states.index('active.H*') < step.entered_states.index('concurrent_processes'))
        self.assertTrue(step.entered_states.index('concurrent_processes') < step.entered_states.index('process_1'))
        self.assertTrue(step.entered_states.index('concurrent_processes') < step.entered_states.index('process_2'))
        self.assertTrue(step.entered_states.index('process_1') < step.entered_states.index('s12'))
        self.assertTrue(step.entered_states.index('process_2') < step.entered_states.index('s22'))

        self.interpreter.queue(Event('next1')).queue(Event('next2')).execute()
        self.assertTrue(self.interpreter.final)

    def test_exited_order(self):
        self.interpreter.queue(Event('next1')).queue(Event('next2')).queue(Event('pause'))
        step = self.interpreter.execute()[-1]

        self.assertEqual(step.exited_states, ['s12', 's22', 'process_1', 'process_2', 'concurrent_processes', 'active'])
        self.assertEqual(sorted(self.interpreter.configuration), ['pause', 'root'])

        step = self.interpreter.queue(Event('continue')).execute_once()
        self.assertEqual(step.exited_states, ['pause', 'active.H*'])

        self.interpreter.queue(Event('next1')).queue(Event('next2')).execute()
        self.assertTrue(self.interpreter.final)


class InfiniteExecutionTests(unittest.TestCase):
    def setUp(self):
        with open('tests/yaml/infinite.yaml') as f:
            sc = io.import_from_yaml(f)
        self.interpreter = Interpreter(sc)
        # Stabilization
        self.interpreter.execute_once()

    def test_three_steps(self):
        self.assertEqual(self.interpreter.configuration, ['root', 's1'])
        self.interpreter.execute_once()
        self.assertEqual(self.interpreter.configuration, ['root', 's2'])
        self.interpreter.execute_once()
        self.assertEqual(self.interpreter.configuration, ['root', 's1'])
        self.interpreter.execute_once()
        self.assertEqual(self.interpreter.configuration, ['root', 's2'])
        self.assertEqual(self.interpreter.context['x'], 2)  # x is incremented in s1.on_entry

    def test_auto_three_steps(self):
        self.interpreter.execute(max_steps=3)

        self.assertEqual(self.interpreter.configuration, ['root', 's2'])
        self.assertEqual(self.interpreter.context['x'], 2)  # x is incremented in s1.on_entry

    def test_auto_stop(self):
        self.interpreter.execute()

        self.assertTrue(self.interpreter.final)
        self.assertEqual(self.interpreter.context['x'], 100)


class ParallelExecutionTests(unittest.TestCase):
    def setUp(self):
        with open('tests/yaml/parallel.yaml') as f:
            sc = io.import_from_yaml(f)
        self.interpreter = Interpreter(sc)
        # Stabilization
        self.interpreter.execute_once()

    def test_concurrent_transitions(self):
        step = self.interpreter.queue(Event('nextA')).execute_once()

        self.assertEqual(self.interpreter.configuration, ['root', 's1', 'p1', 'p2', 'a1', 'a2'])
        self.assertLess(step.exited_states.index('initial1'), step.exited_states.index('initial2'))
        self.assertLess(step.entered_states.index('a1'), step.entered_states.index('a2'))

    def test_concurrent_transitions_nested_target(self):
        self.interpreter.queue(Event('nextA')).queue(Event('reset1'))
        self.interpreter.execute()

        self.assertEqual(self.interpreter.configuration, ['root', 's1', 'p1', 'p2', 'a2', 'initial1'])

    def test_unnested_transitions(self):
        self.interpreter.queue(Event('nextA')).queue(Event('nextA'))
        self.interpreter.execute()

        self.assertEqual(self.interpreter.configuration, ['root', 's1', 'p1', 'p2', 'a2', 'initial1'])

    def test_unnested_transitions_2(self):
        self.interpreter.queue(Event('nextA')).queue(Event('nextB'))
        self.interpreter.execute()

        self.assertEqual(self.interpreter.configuration, ['root', 's1', 'p1', 'p2', 'b1', 'b2'])

    def test_conflicting_transitions(self):
        self.interpreter.queue(Event('nextA')).queue(Event('nextB')).queue(Event('conflict1'))
        self.interpreter.execute_once()
        self.interpreter.execute_once()

        with self.assertRaises(exceptions.ConflictingTransitionsError):
            self.interpreter.execute_once()

    def test_conflicting_transitions_2(self):
        self.interpreter.queue(Event('nextA')).queue(Event('nextB')).queue(Event('conflict2'))
        self.interpreter.execute_once()
        self.interpreter.execute_once()

        with self.assertRaises(exceptions.ConflictingTransitionsError):
            self.interpreter.execute_once()


class NestedParallelExecutionTests(unittest.TestCase):
    def setUp(self):
        with open('tests/yaml/nested_parallel.yaml') as f:
            sc = io.import_from_yaml(f)
        self.interpreter = Interpreter(sc)
        # Stabilization
        self.interpreter.execute_once()
        self.common_states = ['root', 's1', 'p1', 'p2', 'r1', 'r2', 'r3', 'r4']

    def test_initial(self):
        self.assertEqual(self.interpreter.configuration, self.common_states + ['i1', 'i2', 'i3', 'i4'])

    def test_parallel_order(self):
        self.interpreter.queue(Event('next'))
        step = self.interpreter.execute_once()

        self.assertEqual(self.interpreter.configuration, self.common_states + ['j1', 'j2', 'j3', 'j4'])
        self.assertEqual(step.exited_states, ['i1', 'i2', 'i3', 'i4'])
        self.assertEqual(step.entered_states, ['j1', 'j2', 'j3', 'j4'])
        self.assertEqual([t.source for t in step.transitions], ['i1', 'i2', 'i3', 'i4'])

    def test_partial_parallel_order(self):
        self.interpreter.queue(Event('next')).queue(Event('click'))
        self.interpreter.execute_once()
        step = self.interpreter.execute_once()

        self.assertEqual(self.interpreter.configuration, self.common_states + ['j1', 'j3', 'k2', 'k4'])
        self.assertEqual(step.exited_states, ['j2', 'j4'])
        self.assertEqual(step.entered_states, ['k2', 'k4'])
        self.assertEqual([t.source for t in step.transitions], ['j2', 'j4'])

    def test_partial_unnested_transition(self):
        self.interpreter.queue(Event('next')).queue(Event('reset'))
        self.interpreter.execute_once()
        step = self.interpreter.execute_once()

        self.assertEqual(self.interpreter.configuration, self.common_states + ['i1', 'i2', 'i3', 'i4'])
        self.assertLess(step.exited_states.index('r2'), step.exited_states.index('r4'))
        self.assertLess(step.exited_states.index('p1'), step.exited_states.index('p2'))
        self.assertLess(step.exited_states.index('r2'), step.exited_states.index('p1'))
        self.assertLess(step.exited_states.index('r4'), step.exited_states.index('p2'))
        self.assertLess(step.entered_states.index('p1'), step.entered_states.index('p2'))
        self.assertLess(step.entered_states.index('p1'), step.entered_states.index('r1'))
        self.assertLess(step.entered_states.index('p1'), step.entered_states.index('r2'))
        self.assertLess(step.entered_states.index('r1'), step.entered_states.index('p2'))
        self.assertLess(step.entered_states.index('r2'), step.entered_states.index('p2'))
        self.assertLess(step.entered_states.index('p2'), step.entered_states.index('r3'))
        self.assertLess(step.entered_states.index('p2'), step.entered_states.index('r4'))
        self.assertEqual([t.source for t in step.transitions], ['r2', 'r4'])

    def test_name_order(self):
        self.interpreter.queue(Event('next')).queue(Event('click')).queue(Event('next')).queue(Event('next'))
        self.interpreter.execute_once()
        self.interpreter.execute_once()
        self.interpreter.execute_once()

        self.assertEqual(self.interpreter.configuration, self.common_states + ['k1', 'k3', 'x', 'y'])

        step = self.interpreter.execute_once()
        self.assertLess(step.exited_states.index('k1'), step.exited_states.index('k3'))
        self.assertLess(step.exited_states.index('k3'), step.exited_states.index('x'))
        self.assertLess(step.exited_states.index('x'), step.exited_states.index('y'))
        self.assertEqual(self.interpreter.configuration, self.common_states + ['k1', 'x', 'y', 'z'])
        self.assertLess(step.entered_states.index('k1'), step.entered_states.index('z'))
        self.assertLess(step.entered_states.index('z'), step.entered_states.index('x'))
        self.assertLess(step.entered_states.index('x'), step.entered_states.index('y'))

        self.assertEqual([t.source for t in step.transitions], ['k1', 'k3', 'x', 'y'])

        step = self.interpreter.queue(Event('next')).execute_once()

        self.assertLess(step.exited_states.index('k1'), step.exited_states.index('x'))
        self.assertLess(step.exited_states.index('x'), step.exited_states.index('y'))
        self.assertLess(step.exited_states.index('y'), step.exited_states.index('z'))
        self.assertEqual(self.interpreter.configuration, self.common_states + ['k1', 'x', 'y', 'z'])
        self.assertLess(step.entered_states.index('k1'), step.entered_states.index('x'))
        self.assertLess(step.entered_states.index('x'), step.entered_states.index('y'))
        self.assertLess(step.entered_states.index('y'), step.entered_states.index('z'))

        self.assertEqual([t.source for t in step.transitions], ['k1', 'x', 'y', 'z'])


class BindTests(unittest.TestCase):
    def setUp(self):
        with open('tests/yaml/simple.yaml') as f:
            sc = io.import_from_yaml(f)
        self.interpreter = Interpreter(sc)
        # Stabilization
        self.interpreter.execute_once()

    def test_bind(self):
        with open('tests/yaml/simple.yaml') as f:
            other_sc = io.import_from_yaml(f)
        other_interpreter = Interpreter(other_sc)

        self.interpreter.bind(other_interpreter)
        self.assertIn(other_interpreter.queue, self.interpreter._bound)

        self.interpreter.raise_event(InternalEvent('test'))
        self.assertTrue(self.interpreter._internal_events.pop(), Event('test'))
        self.assertTrue(other_interpreter._external_events.pop(), Event('test'))

    def test_bind_callable(self):
        with open('tests/yaml/simple.yaml') as f:
            other_sc = io.import_from_yaml(f)
        other_interpreter = Interpreter(other_sc)

        self.interpreter.bind(other_interpreter.queue)
        self.assertIn(other_interpreter.queue, self.interpreter._bound)

        self.interpreter.raise_event(InternalEvent('test'))
        self.assertTrue(self.interpreter._internal_events.pop(), Event('test'))
        self.assertTrue(other_interpreter._external_events.pop(), Event('test'))