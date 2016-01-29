import unittest
from sismic import io
from sismic.interpreter import Interpreter, run_in_background
from sismic import exceptions
from sismic.code import DummyEvaluator
from sismic.model import Event, InternalEvent


class RunInBackgroundTests(unittest.TestCase):
    def test_run_in_background(self):
        sc = io.import_from_yaml(open('tests/yaml/simple.yaml'))
        intp = Interpreter(sc)
        task = run_in_background(intp, 0.001)
        intp.queue(Event('goto s2'))
        intp.queue(Event('goto final'))
        task.join()
        self.assertTrue(intp.final)


class SimulatorSimpleTests(unittest.TestCase):
    def test_init(self):
        sc = io.import_from_yaml(open('tests/yaml/simple.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)
        self.assertEqual(interpreter.configuration, ['root', 's1'])
        self.assertFalse(interpreter.final)

    def test_simple_configuration(self):
        sc = io.import_from_yaml(open('tests/yaml/simple.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)
        interpreter.execute_once()  # Should do nothing!
        self.assertEqual(interpreter.configuration, ['root', 's1'])
        interpreter.queue(Event('goto s2'))
        interpreter.execute_once()
        self.assertEqual(interpreter.configuration, ['root', 's2'])
        interpreter.execute_once()
        self.assertEqual(interpreter.configuration, ['root', 's3'])

    def test_simple_entered(self):
        sc = io.import_from_yaml(open('tests/yaml/simple.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)
        interpreter.queue(Event('goto s2'))
        self.assertEqual(interpreter.execute_once().entered_states, ['s2'])
        interpreter.queue(Event('goto final'))
        self.assertEqual(interpreter.execute_once().entered_states, ['s3'])
        self.assertEqual(interpreter.execute_once().entered_states, ['final'])
        self.assertEqual(interpreter.configuration, [])
        self.assertTrue(interpreter.final)

    def test_simple_final(self):
        sc = io.import_from_yaml(open('tests/yaml/simple.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)
        interpreter.queue(Event('goto s2')).queue(Event('goto final'))
        interpreter.execute()
        self.assertTrue(interpreter.final)


class InternalTests(unittest.TestCase):
    def setUp(self):
        self.sc = io.import_from_yaml(open('tests/yaml/internal.yaml'))
        self.interpreter = Interpreter(self.sc)

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
        sc = io.import_from_yaml(open('tests/yaml/nondeterministic.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)

        with self.assertRaises(exceptions.NonDeterminismError):
            interpreter.execute_once()


class SimulatorHistoryTests(unittest.TestCase):
    def test_init(self):
        sc = io.import_from_yaml(open('tests/yaml/history.yaml'))
        Interpreter(sc, DummyEvaluator)
        self.assertTrue(True)

    def test_memory(self):
        sc = io.import_from_yaml(open('tests/yaml/history.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)

        interpreter.queue(Event('next')).execute_once()
        self.assertEqual(sorted(interpreter.configuration), ['loop', 'root', 's2'])

        step = interpreter.queue(Event('pause')).execute_once()
        self.assertEqual(step.exited_states, ['s2', 'loop'])
        self.assertEqual(sorted(interpreter.configuration), ['pause', 'root'])

    def test_resume_memory(self):
        sc = io.import_from_yaml(open('tests/yaml/history.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)

        interpreter.queue(Event('next')).queue(Event('pause')).queue(Event('continue'))
        steps = interpreter.execute()
        step = steps[-1]

        self.assertEqual(step.entered_states, ['loop', 'loop.H', 's2'])
        self.assertEqual(step.exited_states, ['pause', 'loop.H'])
        self.assertEqual(sorted(interpreter.configuration), ['loop', 'root', 's2'])

    def test_after_memory(self):
        sc = io.import_from_yaml(open('tests/yaml/history.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)

        interpreter.queue(Event('next')).queue(Event('pause')).queue(Event('continue'))
        interpreter.queue(Event('next')).queue(Event('next'))
        interpreter.execute()
        self.assertEqual(sorted(interpreter.configuration), ['loop', 'root', 's1'])

        interpreter.queue(Event('pause')).queue(Event('stop'))
        interpreter.execute()
        self.assertTrue(interpreter.final)


class SimulatorDeepHistoryTests(unittest.TestCase):
    def test_deep_memory(self):
        sc = io.import_from_yaml(open('tests/yaml/deep_history.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)

        interpreter.queue(Event('next1')).queue(Event('next2'))
        interpreter.execute()
        self.assertEqual(sorted(interpreter.configuration), ['active', 'concurrent_processes', 'process_1', 'process_2', 'root', 's12', 's22'])

        interpreter.queue(Event('error1'))
        interpreter.execute()
        self.assertEqual(interpreter.configuration, ['root', 'pause'])
        self.assertEqual(sorted(interpreter._memory['active.H*']), ['concurrent_processes', 'process_1', 'process_2', 's12', 's22'])

        interpreter.queue(Event('continue'))
        interpreter.execute()
        self.assertEqual(sorted(interpreter.configuration), ['active', 'concurrent_processes', 'process_1',
                                                           'process_2', 'root', 's12', 's22'])

    def test_entered_order(self):
        sc = io.import_from_yaml(open('tests/yaml/deep_history.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)

        interpreter.queue(Event('next1')).queue(Event('next2')).queue(Event('pause'))
        step = interpreter.execute()[-1]

        self.assertEqual(step.entered_states, ['pause'])
        self.assertEqual(sorted(interpreter.configuration), ['pause', 'root'])

        step = interpreter.queue(Event('continue')).execute_once()
        self.assertTrue(step.entered_states.index('active') < step.entered_states.index('active.H*'))
        self.assertTrue(step.entered_states.index('active.H*') < step.entered_states.index('concurrent_processes'))
        self.assertTrue(step.entered_states.index('concurrent_processes') < step.entered_states.index('process_1'))
        self.assertTrue(step.entered_states.index('concurrent_processes') < step.entered_states.index('process_2'))
        self.assertTrue(step.entered_states.index('process_1') < step.entered_states.index('s12'))
        self.assertTrue(step.entered_states.index('process_2') < step.entered_states.index('s22'))

        interpreter.queue(Event('next1')).queue(Event('next2')).execute()
        self.assertTrue(interpreter.final)

    def test_exited_order(self):
        sc = io.import_from_yaml(open('tests/yaml/deep_history.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)

        interpreter.queue(Event('next1')).queue(Event('next2')).queue(Event('pause'))
        step = interpreter.execute()[-1]

        self.assertEqual(step.exited_states, ['s12', 's22', 'process_1', 'process_2', 'concurrent_processes', 'active'])
        self.assertEqual(sorted(interpreter.configuration), ['pause', 'root'])

        step = interpreter.queue(Event('continue')).execute_once()
        self.assertEqual(step.exited_states, ['pause', 'active.H*'])

        interpreter.queue(Event('next1')).queue(Event('next2')).execute()
        self.assertTrue(interpreter.final)


class InfiniteExecutionTests(unittest.TestCase):
    def setUp(self):
        self.sc = io.import_from_yaml(open('tests/yaml/infinite.yaml'))
        self.interpreter = Interpreter(self.sc)

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
        self.sc = io.import_from_yaml(open('tests/yaml/parallel.yaml'))
        self.interpreter = Interpreter(self.sc)

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
        self.sc = io.import_from_yaml(open('tests/yaml/nested_parallel.yaml'))
        self.interpreter = Interpreter(self.sc)
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
        sc = io.import_from_yaml(open('tests/yaml/simple.yaml'))
        self.interpreter = Interpreter(sc)

    def test_bind(self):
        other_sc = io.import_from_yaml(open('tests/yaml/simple.yaml'))
        other_interpreter = Interpreter(other_sc)

        self.interpreter.bind(other_interpreter)
        self.assertEqual(self.interpreter._bound, [other_interpreter.queue])

        self.interpreter.queue(InternalEvent('test'))
        self.assertTrue(self.interpreter._events.pop(), Event('test'))
        self.assertTrue(other_interpreter._events.pop(), Event('test'))

    def test_bind_callable(self):
        other_sc = io.import_from_yaml(open('tests/yaml/simple.yaml'))
        other_interpreter = Interpreter(other_sc)

        self.interpreter.bind(other_interpreter.queue)
        self.assertEqual(self.interpreter._bound, [other_interpreter.queue])

        self.interpreter.queue(InternalEvent('test'))
        self.assertTrue(self.interpreter._events.pop(), Event('test'))
        self.assertTrue(other_interpreter._events.pop(), Event('test'))