import unittest
from sismic import io
from sismic.interpreter import Interpreter, run_in_background
from sismic.evaluator import DummyEvaluator
from sismic.model import Event, Transition, StateChart, StateMixin
from sismic.model import PreconditionFailed, PostconditionFailed, InvariantFailed


class RunInBackgroundTests(unittest.TestCase):
    def test_run_in_background(self):
        sc = io.import_from_yaml(open('examples/simple/simple.yaml'))
        intp = Interpreter(sc)
        task = run_in_background(intp, 0.001)
        intp.send(Event('goto s2'))
        intp.send(Event('goto final'))
        task.join()
        self.assertTrue(intp.final)


class SimulatorSimpleTests(unittest.TestCase):
    def test_init(self):
        sc = io.import_from_yaml(open('examples/simple/simple.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)
        self.assertEqual(interpreter.configuration, ['s1'])
        self.assertFalse(interpreter.final)

    def test_simple_configuration(self):
        sc = io.import_from_yaml(open('examples/simple/simple.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)
        interpreter.execute_once()  # Should do nothing!
        self.assertEqual(interpreter.configuration, ['s1'])
        interpreter.send(Event('goto s2'))
        interpreter.execute_once()
        self.assertEqual(interpreter.configuration, ['s2'])
        interpreter.execute_once()
        self.assertEqual(interpreter.configuration, ['s3'])

    def test_simple_entered(self):
        sc = io.import_from_yaml(open('examples/simple/simple.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)
        interpreter.send(Event('goto s2'))
        self.assertEqual(interpreter.execute_once().entered_states, ['s2'])
        interpreter.send(Event('goto final'))
        self.assertEqual(interpreter.execute_once().entered_states, ['s3'])
        self.assertEqual(interpreter.execute_once().entered_states, ['final'])
        self.assertEqual(interpreter.configuration, [])
        self.assertTrue(interpreter.final)

    def test_simple_final(self):
        sc = io.import_from_yaml(open('examples/simple/simple.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)
        interpreter.send(Event('goto s2')).send(Event('goto final'))
        interpreter.execute()
        self.assertTrue(interpreter.final)


class InternalTests(unittest.TestCase):
    def setUp(self):
        self.sc = io.import_from_yaml(open('examples/simple/internal.yaml'))
        self.interpreter = Interpreter(self.sc)

    def testInternalSent(self):
        step = self.interpreter.execute_once()
        self.assertEqual(step.event.name, 'next')

    def testInternalBeforeExternal(self):
        self.interpreter.send(Event('not_next'))
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


class SimulatorElevatorTests(unittest.TestCase):
    def test_init(self):
        sc = io.import_from_yaml(open('examples/concrete/elevator.yaml'))
        interpreter = Interpreter(sc)

        self.assertEqual(len(interpreter.configuration), 5)

    def test_floor_selection(self):
        sc = io.import_from_yaml(open('examples/concrete/elevator.yaml'))
        interpreter = Interpreter(sc)

        interpreter.send(Event('floorSelected', {'floor': 4})).execute_once()
        self.assertEqual(interpreter._evaluator.context['destination'], 4)
        interpreter.execute_once()
        self.assertEqual(sorted(interpreter.configuration), ['active', 'doorsClosed', 'floorListener', 'floorSelecting', 'movingElevator'])

    def test_doorsOpen(self):
        sc = io.import_from_yaml(open('examples/concrete/elevator.yaml'))
        interpreter = Interpreter(sc)

        interpreter.send(Event('floorSelected', {'floor': 4}))
        interpreter.execute()
        self.assertEqual(interpreter._evaluator.context['current'], 4)
        interpreter.time += 10
        interpreter.execute()

        self.assertTrue('doorsOpen' in interpreter.configuration)
        self.assertEqual(interpreter._evaluator.context['current'], 0)


class SimulatorNonDeterminismTests(unittest.TestCase):
    def test_nondeterminism(self):
        sc = io.import_from_yaml(open('examples/simple/nondeterministic.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)

        with self.assertRaises(Warning):
            interpreter.execute_once()


class SimulatorHistoryTests(unittest.TestCase):
    def test_init(self):
        sc = io.import_from_yaml(open('examples/concrete/history.yaml'))
        Interpreter(sc, DummyEvaluator)

    def test_memory(self):
        sc = io.import_from_yaml(open('examples/concrete/history.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)

        interpreter.send(Event('next')).execute_once()
        self.assertEqual(sorted(interpreter.configuration), ['loop', 's2'])

        step = interpreter.send(Event('pause')).execute_once()
        self.assertEqual(step.exited_states, ['s2', 'loop'])
        self.assertEqual(sorted(interpreter.configuration), ['pause'])

    def test_resume_memory(self):
        sc = io.import_from_yaml(open('examples/concrete/history.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)

        interpreter.send(Event('next')).send(Event('pause')).send(Event('continue'))
        steps = interpreter.execute()
        step = steps[-1]

        self.assertEqual(step.entered_states, ['loop', 'loop.H', 's2'])
        self.assertEqual(step.exited_states, ['pause', 'loop.H'])
        self.assertEqual(sorted(interpreter.configuration), ['loop', 's2'])

    def test_after_memory(self):
        sc = io.import_from_yaml(open('examples/concrete/history.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)

        interpreter.send(Event('next')).send(Event('pause')).send(Event('continue'))
        interpreter.send(Event('next')).send(Event('next'))
        interpreter.execute()
        self.assertEqual(sorted(interpreter.configuration), ['loop', 's1'])

        interpreter.send(Event('pause')).send(Event('stop'))
        interpreter.execute()
        self.assertTrue(interpreter.final)


class SimulatorDeepHistoryTests(unittest.TestCase):
    def test_deep_memory(self):
        sc = io.import_from_yaml(open('examples/concrete/deep_history.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)

        interpreter.send(Event('next1')).send(Event('next2'))
        interpreter.execute()
        self.assertEqual(sorted(interpreter.configuration), ['active', 'concurrent_processes', 'process_1', 'process_2', 's12', 's22'])

        interpreter.send(Event('error1'))
        interpreter.execute()
        self.assertEqual(interpreter.configuration, ['pause'])
        self.assertEqual(sorted(interpreter._memory['active.H*']), ['concurrent_processes', 'process_1', 'process_2', 's12', 's22'])

        interpreter.send(Event('continue'))
        interpreter.execute()
        self.assertEqual(sorted(interpreter.configuration), ['active', 'concurrent_processes', 'process_1',
                                                           'process_2', 's12', 's22'])

    def test_entered_order(self):
        sc = io.import_from_yaml(open('examples/concrete/deep_history.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)

        interpreter.send(Event('next1')).send(Event('next2')).send(Event('pause'))
        step = interpreter.execute()[-1]

        self.assertEqual(step.entered_states, ['pause'])
        self.assertEqual(sorted(interpreter.configuration), ['pause'])

        step = interpreter.send(Event('continue')).execute_once()
        self.assertTrue(step.entered_states.index('active') < step.entered_states.index('active.H*'))
        self.assertTrue(step.entered_states.index('active.H*') < step.entered_states.index('concurrent_processes'))
        self.assertTrue(step.entered_states.index('concurrent_processes') < step.entered_states.index('process_1'))
        self.assertTrue(step.entered_states.index('concurrent_processes') < step.entered_states.index('process_2'))
        self.assertTrue(step.entered_states.index('process_1') < step.entered_states.index('s12'))
        self.assertTrue(step.entered_states.index('process_2') < step.entered_states.index('s22'))

        interpreter.send(Event('next1')).send(Event('next2')).execute()
        self.assertTrue(interpreter.final)

    def test_exited_order(self):
        sc = io.import_from_yaml(open('examples/concrete/deep_history.yaml'))
        interpreter = Interpreter(sc, DummyEvaluator)

        interpreter.send(Event('next1')).send(Event('next2')).send(Event('pause'))
        step = interpreter.execute()[-1]

        self.assertEqual(step.exited_states, ['s12', 's22', 'process_1', 'process_2', 'concurrent_processes', 'active'])
        self.assertEqual(sorted(interpreter.configuration), ['pause'])

        step = interpreter.send(Event('continue')).execute_once()
        self.assertEqual(step.exited_states, ['pause', 'active.H*'])

        interpreter.send(Event('next1')).send(Event('next2')).execute()
        self.assertTrue(interpreter.final)


class InfiniteExecutionTests(unittest.TestCase):
    def setUp(self):
        self.sc = io.import_from_yaml(open('examples/simple/infinite.yaml'))
        self.interpreter = Interpreter(self.sc)

    def test_three_steps(self):
        self.assertEqual(self.interpreter.configuration, ['s1'])
        self.interpreter.execute_once()
        self.assertEqual(self.interpreter.configuration, ['s2'])
        self.interpreter.execute_once()
        self.assertEqual(self.interpreter.configuration, ['s1'])
        self.interpreter.execute_once()
        self.assertEqual(self.interpreter.configuration, ['s2'])
        self.assertEqual(self.interpreter._evaluator.context['x'], 2)  # x is incremented in s1.on_entry

    def test_auto_three_steps(self):
        self.interpreter.execute(max_steps=3)

        self.assertEqual(self.interpreter.configuration, ['s2'])
        self.assertEqual(self.interpreter._evaluator.context['x'], 2)  # x is incremented in s1.on_entry

    def test_auto_stop(self):
        self.interpreter.execute()

        self.assertTrue(self.interpreter.final)
        self.assertEqual(self.interpreter._evaluator.context['x'], 100)


class ParallelExecutionTests(unittest.TestCase):
    def setUp(self):
        self.sc = io.import_from_yaml(open('examples/simple/test_parallel.yaml'))
        self.interpreter = Interpreter(self.sc)

    def test_concurrent_transitions(self):
        step = self.interpreter.send(Event('nextA')).execute_once()

        self.assertEqual(self.interpreter.configuration, ['s1', 'p1', 'p2', 'a1', 'a2'])
        self.assertLess(step.exited_states.index('initial1'), step.exited_states.index('initial2'))
        self.assertLess(step.entered_states.index('a1'), step.entered_states.index('a2'))

    def test_concurrent_transitions_nested_target(self):
        self.interpreter.send(Event('nextA')).send(Event('reset1'))
        self.interpreter.execute()

        self.assertEqual(self.interpreter.configuration, ['s1', 'p1', 'p2', 'a2', 'initial1'])

    def test_unnested_transitions(self):
        self.interpreter.send(Event('nextA')).send(Event('nextA'))
        self.interpreter.execute()

        self.assertEqual(self.interpreter.configuration, ['s1', 'p1', 'p2', 'a2', 'initial1'])

    def test_unnested_transitions_2(self):
        self.interpreter.send(Event('nextA')).send(Event('nextB'))
        self.interpreter.execute()

        self.assertEqual(self.interpreter.configuration, ['s1', 'p1', 'p2', 'b1', 'b2'])

    def test_conflicting_transitions(self):
        self.interpreter.send(Event('nextA')).send(Event('nextB')).send(Event('conflict1'))
        self.interpreter.execute_once()
        self.interpreter.execute_once()

        with self.assertRaises(Warning):
            self.interpreter.execute_once()

    def test_conflicting_transitions_2(self):
        self.interpreter.send(Event('nextA')).send(Event('nextB')).send(Event('conflict2'))
        self.interpreter.execute_once()
        self.interpreter.execute_once()

        with self.assertRaises(Warning):
            self.interpreter.execute_once()


class NestedParallelExecutionTests(unittest.TestCase):
    def setUp(self):
        self.sc = io.import_from_yaml(open('examples/simple/test_nested_parallel.yaml'))
        self.interpreter = Interpreter(self.sc)
        self.common_states = ['s1', 'p1', 'p2', 'r1', 'r2', 'r3', 'r4']

    def test_initial(self):
        self.assertEqual(self.interpreter.configuration, self.common_states + ['i1', 'i2', 'i3', 'i4'])

    def test_parallel_order(self):
        self.interpreter.send(Event('next'))
        step = self.interpreter.execute_once()

        self.assertEqual(self.interpreter.configuration, self.common_states + ['j1', 'j2', 'j3', 'j4'])
        self.assertEqual(step.exited_states, ['i1', 'i2', 'i3', 'i4'])
        self.assertEqual(step.entered_states, ['j1', 'j2', 'j3', 'j4'])
        self.assertEqual([t.from_state for t in step.transitions], ['i1', 'i2', 'i3', 'i4'])

    def test_partial_parallel_order(self):
        self.interpreter.send(Event('next')).send(Event('click'))
        self.interpreter.execute_once()
        step = self.interpreter.execute_once()

        self.assertEqual(self.interpreter.configuration, self.common_states + ['j1', 'j3', 'k2', 'k4'])
        self.assertEqual(step.exited_states, ['j2', 'j4'])
        self.assertEqual(step.entered_states, ['k2', 'k4'])
        self.assertEqual([t.from_state for t in step.transitions], ['j2', 'j4'])

    def test_partial_unnested_transition(self):
        self.interpreter.send(Event('next')).send(Event('reset'))
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
        self.assertEqual([t.from_state for t in step.transitions], ['r2', 'r4'])

    def test_name_order(self):
        self.interpreter.send(Event('next')).send(Event('click')).send(Event('next')).send(Event('next'))
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

        self.assertEqual([t.from_state for t in step.transitions], ['k1', 'k3', 'x', 'y'])

        step = self.interpreter.send(Event('next')).execute_once()

        self.assertLess(step.exited_states.index('k1'), step.exited_states.index('x'))
        self.assertLess(step.exited_states.index('x'), step.exited_states.index('y'))
        self.assertLess(step.exited_states.index('y'), step.exited_states.index('z'))
        self.assertEqual(self.interpreter.configuration, self.common_states + ['k1', 'x', 'y', 'z'])
        self.assertLess(step.entered_states.index('k1'), step.entered_states.index('x'))
        self.assertLess(step.entered_states.index('x'), step.entered_states.index('y'))
        self.assertLess(step.entered_states.index('y'), step.entered_states.index('z'))

        self.assertEqual([t.from_state for t in step.transitions], ['k1', 'x', 'y', 'z'])


class WriterExecutionTests(unittest.TestCase):
    def setUp(self):
        self.sc = io.import_from_yaml(open('examples/concrete/writer_options.yaml'))
        self.interpreter = Interpreter(self.sc)

    def test_output(self):
        scenario = [
             Event('keyPress', {'key': 'bonjour '}),
             Event('toggle'),
             Event('keyPress', {'key': 'a '}),
             Event('toggle'),
             Event('toggle_bold'),
             Event('keyPress', {'key': 'tous !'}),
             Event('leave')
        ]

        for event in scenario:
            self.interpreter.send(event)

        self.interpreter.execute()

        self.assertTrue(self.interpreter.final)
        self.assertEqual(self.interpreter.evaluator.context['output'], ['bonjour ', '[b]', '[i]', 'a ', '[/b]', '[/i]', '[b]', 'tous !', '[/b]'])


class ElevatorContractTests(unittest.TestCase):
    def setUp(self):
        self.sc = io.import_from_yaml(open('examples/contract/elevator.yaml'))
        self.interpreter = Interpreter(self.sc)

    def test_no_error(self):
        self.interpreter.send(Event('floorSelected', {'floor': 4}))
        self.interpreter.execute()
        self.assertFalse(self.interpreter.final)

    def test_state_precondition(self):
        self.sc.states['movingUp'].preconditions.append('False')
        self.interpreter.send(Event('floorSelected', {'floor': 4}))
        with self.assertRaises(PreconditionFailed) as cm:
            self.interpreter.execute()
        self.assertTrue(isinstance(cm.exception.obj, StateMixin))

    def test_state_postcondition(self):
        self.sc.states['movingUp'].postconditions.append('False')
        self.interpreter.send(Event('floorSelected', {'floor': 4}))
        with self.assertRaises(PostconditionFailed) as cm:
            self.interpreter.execute()
        self.assertTrue(isinstance(cm.exception.obj, StateMixin))

    def test_state_invariant(self):
        self.sc.states['movingUp'].invariants.append('False')
        self.interpreter.send(Event('floorSelected', {'floor': 4}))
        with self.assertRaises(InvariantFailed) as cm:
            self.interpreter.execute()
        self.assertTrue(isinstance(cm.exception.obj, StateMixin))

    def test_transition_precondition(self):
        self.sc.states['floorSelecting'].transitions[0].preconditions.append('False')
        self.interpreter.send(Event('floorSelected', {'floor': 4}))
        with self.assertRaises(PreconditionFailed) as cm:
            self.interpreter.execute()
        self.assertTrue(isinstance(cm.exception.obj, Transition))

    def test_transition_postcondition(self):
        self.sc.states['floorSelecting'].transitions[0].postconditions.append('False')
        self.interpreter.send(Event('floorSelected', {'floor': 4}))
        with self.assertRaises(PostconditionFailed) as cm:
            self.interpreter.execute()
        self.assertTrue(isinstance(cm.exception.obj, Transition))

    def test_statechart_precondition(self):
        self.sc.preconditions.append('False')
        with self.assertRaises(PreconditionFailed) as cm:
            self.interpreter = Interpreter(self.sc)
        self.assertTrue(isinstance(cm.exception.obj, StateChart))

    def test_statechart_postcondition(self):
        sc = io.import_from_yaml(open('examples/simple/simple.yaml'))
        sc.postconditions.append('False')
        interpreter = Interpreter(sc)
        interpreter.send(Event('goto s2')).send(Event('goto final'))
        with self.assertRaises(PostconditionFailed) as cm:
            interpreter.execute()
        self.assertTrue(isinstance(cm.exception.obj, StateChart))

    def test_statechart_invariant(self):
        self.sc.invariants.append('False')
        self.interpreter.send(Event('floorSelected', {'floor': 4}))
        with self.assertRaises(InvariantFailed) as cm:
            self.interpreter.execute()
        self.assertTrue(isinstance(cm.exception.obj, StateChart))

    def test_do_not_raise(self):
        self.sc.invariants.append('False')
        interpreter = Interpreter(self.sc, silent_contract=True)
        interpreter.send(Event('floorSelected', {'floor': 4}))
        interpreter.execute()
        self.assertTrue(len(interpreter.failed_conditions) > 0)