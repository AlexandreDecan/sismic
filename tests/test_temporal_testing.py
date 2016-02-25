import unittest
from sismic.temporal_testing import *
from sismic.interpreter import Interpreter
from sismic.model import Event, Statechart, CompoundState, BasicState, Transition
from sismic.testing import teststory_from_trace


class UniqueIdProviderTest(unittest.TestCase):
    def test_same_provider_same_element(self):
        provider = UniqueIdProvider()
        self.assertEqual(provider('foo'), provider('foo'))

    def test_same_provider_different_elements(self):
        provider = UniqueIdProvider()
        self.assertNotEqual(provider('foo'), provider('bar'))

    def test_different_providers_same_element(self):
        provider_a = UniqueIdProvider()
        provider_b = UniqueIdProvider()
        self.assertNotEqual(provider_a('foo'), provider_b('foo'))

    def test_different_providers_different_elements(self):
        provider_a = UniqueIdProvider()
        provider_b = UniqueIdProvider()
        self.assertNotEqual(provider_a('foo'), provider_b('bar'))


class PropertiesTests(unittest.TestCase):
    def setUp(self):
        self.sequential_statechart = Statechart('sequential')
        initial_state = CompoundState('initial_state', initial='a_state')
        a_state = BasicState('a_state')
        b_state = BasicState('b_state')
        self.sequential_statechart.add_state(initial_state, None)
        self.sequential_statechart.add_state(a_state, 'initial_state')
        self.sequential_statechart.add_state(b_state, 'initial_state')
        self.sequential_statechart.add_transition(Transition(source='a_state', target='b_state', event='event'))
        self.sequential_interpreter = Interpreter(self.sequential_statechart)

    def test_enter(self):
        from sismic.interpreter import log_trace

        tester = Statechart('test')
        test_initial_state = CompoundState('initial_state', initial='Enter')
        enter_state = Enter('b_state')
        out_state = BasicState('out')
        tester.add_state(test_initial_state, None)
        tester.add_state(out_state, 'initial_state')
        enter_state.add_to(tester, 'Enter', 'initial_state', 'out', None)
        test_interpreter = Interpreter(tester)

        self.assertFalse('out' in test_interpreter.configuration)

        trace = log_trace(self.sequential_interpreter)

        self.sequential_interpreter.queue(Event('event'))
        self.sequential_interpreter.execute()

        story = teststory_from_trace(trace)
        story.tell(test_interpreter)

        self.assertTrue('out' in test_interpreter.configuration)

    def test_exit(self):
        from sismic.interpreter import log_trace

        tester = Statechart('test')
        test_initial_state = CompoundState('initial_state', initial='Exit')
        exit_state = Exit('a_state')
        out_state = BasicState('out')
        tester.add_state(test_initial_state, None)
        tester.add_state(out_state, 'initial_state')
        exit_state.add_to(tester, 'Exit', 'initial_state', 'out', None)
        test_interpreter = Interpreter(tester)

        self.assertFalse('out' in test_interpreter.configuration)

        trace = log_trace(self.sequential_interpreter)

        self.sequential_interpreter.queue(Event('event'))
        self.sequential_interpreter.execute()

        story = teststory_from_trace(trace)
        story.tell(test_interpreter)

        self.assertTrue('out' in test_interpreter.configuration)

    def test_check_guard_success(self):
        statechart = Statechart('statechart')
        initial_state = CompoundState('initial_state', initial='condition')
        statechart.add_state(initial_state, parent=None)
        statechart.add_state(BasicState('success'), parent='initial_state')
        statechart.add_state(BasicState('failure'), parent='initial_state')

        CheckGuard('x == 1').add_to(statechart=statechart,
                                    id='condition',
                                    parent_id='initial_state',
                                    success_id='success',
                                    failure_id='failure')

        interpreter = Interpreter(statechart)
        self.assertFalse('success' in interpreter.configuration)
        self.assertFalse('failure' in interpreter.configuration)

        interpreter.execute()
        self.assertFalse('success' in interpreter.configuration)
        self.assertFalse('failure' in interpreter.configuration)

        interpreter.context['x'] = 1
        interpreter.queue(Event('step ended'))

        interpreter.execute()
        self.assertTrue('success' in interpreter.configuration)
        self.assertFalse('failure' in interpreter.configuration)

    def test_check_guard_failure(self):
        statechart = Statechart('statechart')
        initial_state = CompoundState('initial_state', initial='condition')
        statechart.add_state(initial_state, parent=None)
        statechart.add_state(BasicState('success'), parent='initial_state')
        statechart.add_state(BasicState('failure'), parent='initial_state')

        CheckGuard('x == 1').add_to(statechart=statechart,
                                    id='condition',
                                    parent_id='initial_state',
                                    success_id='success',
                                    failure_id='failure')

        interpreter = Interpreter(statechart)
        self.assertFalse('success' in interpreter.configuration)
        self.assertFalse('failure' in interpreter.configuration)

        interpreter.execute()
        self.assertFalse('success' in interpreter.configuration)
        self.assertFalse('failure' in interpreter.configuration)

        interpreter.context['x'] = 42
        interpreter.queue(Event('step ended'))

        interpreter.execute()
        self.assertFalse('success' in interpreter.configuration)
        self.assertTrue('failure' in interpreter.configuration)

    def test_consume_event_success(self):
        from sismic.interpreter import log_trace

        tester = Statechart('test')
        test_initial_state = CompoundState('initial_state', initial='condition')
        success_state = BasicState('success')
        tester.add_state(test_initial_state, None)
        tester.add_state(success_state, 'initial_state')
        ConsumeEvent('foo').add_to(statechart=tester,
                                 id='condition',
                                 parent_id='initial_state',
                                 success_id='success',
                                 failure_id=None)
        test_interpreter = Interpreter(tester)

        self.assertFalse('success' in test_interpreter.configuration)

        trace = log_trace(self.sequential_interpreter)

        self.sequential_interpreter.queue(Event('foo'))
        self.sequential_interpreter.execute()

        story = teststory_from_trace(trace)
        story.tell(test_interpreter)

        self.assertTrue('success' in test_interpreter.configuration)

    def test_consume_event_failure(self):
        from sismic.interpreter import log_trace

        tester = Statechart('test')
        test_initial_state = CompoundState('initial_state', initial='condition')
        success_state = BasicState('success')
        tester.add_state(test_initial_state, None)
        tester.add_state(success_state, 'initial_state')
        ConsumeEvent('foo').add_to(statechart=tester,
                                 id='condition',
                                 parent_id='initial_state',
                                 success_id='success',
                                 failure_id=None)
        test_interpreter = Interpreter(tester)

        self.assertFalse('success' in test_interpreter.configuration)

        trace = log_trace(self.sequential_interpreter)

        self.sequential_interpreter.queue(Event('bar'))
        self.sequential_interpreter.execute()

        story = teststory_from_trace(trace)
        story.tell(test_interpreter)

        self.assertFalse('success' in test_interpreter.configuration)

    def test_consume_any_event(self):
        from sismic.interpreter import log_trace

        tester = Statechart('test')
        test_initial_state = CompoundState('initial_state', initial='condition')
        success_state = BasicState('success')
        tester.add_state(test_initial_state, None)
        tester.add_state(success_state, 'initial_state')
        ConsumeAnyEvent().add_to(statechart=tester,
                                 id='condition',
                                 parent_id='initial_state',
                                 success_id='success',
                                 failure_id=None)
        test_interpreter = Interpreter(tester)

        self.assertFalse('success' in test_interpreter.configuration)

        trace = log_trace(self.sequential_interpreter)

        self.sequential_interpreter.queue(Event('foo'))
        self.sequential_interpreter.execute()

        story = teststory_from_trace(trace)
        story.tell(test_interpreter)

        self.assertTrue('success' in test_interpreter.configuration)

    def test_execution_started(self):
        from sismic.interpreter import log_trace

        tester = Statechart('test')
        test_initial_state = CompoundState('initial_state', initial='condition')
        success_state = BasicState('success')
        tester.add_state(test_initial_state, None)
        tester.add_state(success_state, 'initial_state')
        ExecutionStart().add_to(statechart=tester,
                                 id='condition',
                                 parent_id='initial_state',
                                 success_id='success',
                                 failure_id=None)
        test_interpreter = Interpreter(tester)

        self.assertFalse('success' in test_interpreter.configuration)

        trace = log_trace(self.sequential_interpreter)

        self.sequential_interpreter.execute()

        story = teststory_from_trace(trace)
        story.tell(test_interpreter)

        self.assertTrue('success' in test_interpreter.configuration)

    def test_step_start_started(self):
        from sismic.interpreter import log_trace

        tester = Statechart('test')
        test_initial_state = CompoundState('initial_state', initial='condition')
        success_state = BasicState('success')
        tester.add_state(test_initial_state, None)
        tester.add_state(success_state, 'initial_state')
        StepStart().add_to(statechart=tester,
                           id='condition',
                           parent_id='initial_state',
                           success_id='success',
                           failure_id=None)
        test_interpreter = Interpreter(tester)

        self.assertFalse('success' in test_interpreter.configuration)

        trace = log_trace(self.sequential_interpreter)

        self.sequential_interpreter.queue(Event('foo'))
        self.sequential_interpreter.execute()

        story = teststory_from_trace(trace)
        story.tell(test_interpreter)

        self.assertTrue('success' in test_interpreter.configuration)


class PropertyReprTest(unittest.TestCase):
    def test_enter_repr(self):
        self.assertEqual(Enter('foo').__repr__(), 'Enter("foo")')

    def test_exit_repr(self):
        self.assertEqual(Exit('foo').__repr__(), 'Exit("foo")')

    def test_check_guard_repr(self):
        self.assertEqual(CheckGuard('foo').__repr__(), 'CheckGuard("foo")')

    def test_consume_repr(self):
        self.assertEqual(ConsumeEvent('foo').__repr__(), 'ConsumeEvent("foo")')

    def test_consume_any_repr(self):
        self.assertEqual(ConsumeAnyEvent().__repr__(), 'ConsumeAnyEvent()')

    def test_execution_start_repr(self):
        self.assertEqual(ExecutionStart().__repr__(), 'ExecutionStart()')

    def test_step_start_repr(self):
        self.assertEqual(StepStart().__repr__(), 'StepStart()')


class OperatorsTest(unittest.TestCase):
    def generic_test(self, condition: Condition, success_expected: bool, failure_expected: bool, delay: int = 0):
        statechart = Statechart('test')
        initial_state = CompoundState('initial_state', initial='Cond')
        statechart.add_state(initial_state, None)

        success_state = BasicState('success')
        statechart.add_state(success_state, 'initial_state')

        failure_state = BasicState('failure')
        statechart.add_state(failure_state, 'initial_state')

        condition.add_to(statechart=statechart,
                         id='Cond',
                         parent_id='initial_state',
                         success_id='success',
                         failure_id='failure')

        interpreter = Interpreter(statechart)

        self.assertFalse('success' in interpreter.configuration)
        self.assertFalse('failure' in interpreter.configuration)

        interpreter.execute()

        interpreter.time += delay
        interpreter.queue(Event('step ended'))
        interpreter.queue(Event('step ended'))
        interpreter.execute()

        self.assertEqual(success_expected, 'success' in interpreter.configuration)
        self.assertEqual(failure_expected, 'failure' in interpreter.configuration)

    def test_true_and_true(self):
        self.generic_test(And(TrueCondition(), TrueCondition()), True, False)

    def test_true_and_false(self):
        self.generic_test(And(TrueCondition(), FalseCondition()), False, True)

    def test_false_and_true(self):
        self.generic_test(And(FalseCondition(), TrueCondition()), False, True)

    def test_false_and_false(self):
        self.generic_test(And(FalseCondition(), FalseCondition()), False, True)

    def test_true_and_undertermined(self):
        self.generic_test(And(TrueCondition(), UndeterminedCondition()), False, False)

    def test_false_and_undertermined(self):
        self.generic_test(And(FalseCondition(), UndeterminedCondition()), False, True)

    def test_undertermined_and_true(self):
        self.generic_test(And(UndeterminedCondition(), TrueCondition()), False, False)

    def test_undertermined_and_false(self):
        self.generic_test(And(UndeterminedCondition(), FalseCondition()), False, True)

    def test_undertermined_and_undertermined(self):
        self.generic_test(And(UndeterminedCondition(), UndeterminedCondition()), False, False)

    def test_true_or_true(self):
        self.generic_test(Or(TrueCondition(), TrueCondition()), True, False)

    def test_true_or_false(self):
        self.generic_test(Or(TrueCondition(), FalseCondition()), True, False)

    def test_false_or_true(self):
        self.generic_test(Or(FalseCondition(), TrueCondition()), True, False)

    def test_false_or_false(self):
        self.generic_test(Or(FalseCondition(), FalseCondition()), False, True)

    def test_true_or_undetermined(self):
        self.generic_test(Or(TrueCondition(), UndeterminedCondition()), True, False)

    def test_false_or_undetermined(self):
        self.generic_test(Or(FalseCondition(), UndeterminedCondition()), False, False)

    def test_undetermined_or_true(self):
        self.generic_test(Or(UndeterminedCondition(), TrueCondition()), True, False)

    def test_undetermined_or_false(self):
        self.generic_test(Or(UndeterminedCondition(), FalseCondition()), False, False)

    def test_undetermined_or_undetermined(self):
        self.generic_test(Or(UndeterminedCondition(), UndeterminedCondition()), False, False)

    def test_not_true(self):
        self.generic_test(Not(TrueCondition()), False, True)

    def test_not_false(self):
        self.generic_test(Not(FalseCondition()), True, False)

    def test_not_undetermined(self):
        self.generic_test(Not(UndeterminedCondition()), False, False)

    def test_true_then_true(self):
        self.generic_test(Then(TrueCondition(), TrueCondition()), True, False)

    def test_true_then_false(self):
        self.generic_test(Then(TrueCondition(), FalseCondition()), False, True)

    def test_true_then_undetermined(self):
        self.generic_test(Then(TrueCondition(), UndeterminedCondition()), False, False)

    def test_false_then_true(self):
        self.generic_test(Then(FalseCondition(), TrueCondition()), False, True)

    def test_false_then_false(self):
        self.generic_test(Then(FalseCondition(), FalseCondition()), False, True)

    def test_false_then_undetermined(self):
        self.generic_test(Then(FalseCondition(), UndeterminedCondition()), False, True)

    def test_undetermined_then_true(self):
        self.generic_test(Then(UndeterminedCondition(), TrueCondition()), False, False)

    def test_undetermined_then_false(self):
        self.generic_test(Then(UndeterminedCondition(), FalseCondition()), False, False)

    def test_undetermined_then_undetermined(self):
        self.generic_test(Then(UndeterminedCondition(), UndeterminedCondition()), False, False)

    def test_true_xor_true(self):
        self.generic_test(Xor(TrueCondition(), TrueCondition()), False, True)

    def test_true_xor_false(self):
        self.generic_test(Xor(TrueCondition(), FalseCondition()), True, False)

    def test_true_xor_undetermined(self):
        self.generic_test(Xor(TrueCondition(), UndeterminedCondition()), False, False)

    def test_false_xor_true(self):
        self.generic_test(Xor(FalseCondition(), TrueCondition()), True, False)

    def test_false_xor_false(self):
        self.generic_test(Xor(FalseCondition(), FalseCondition()), False, True)

    def test_false_xor_undetermined(self):
        self.generic_test(Xor(FalseCondition(), UndeterminedCondition()), False, False)

    def test_undetermined_xor_true(self):
        self.generic_test(Xor(UndeterminedCondition(), TrueCondition()), False, False)

    def test_undetermined_xor_false(self):
        self.generic_test(Xor(UndeterminedCondition(), FalseCondition()), False, False)

    def test_undetermined_xor_undetermined(self):
        self.generic_test(Xor(UndeterminedCondition(), UndeterminedCondition()), False, False)

    def test_true_before_true(self):
        self.generic_test(Before(TrueCondition(), TrueCondition()), False, True)

    def test_true_before_false(self):
        self.generic_test(Before(TrueCondition(), FalseCondition()), True, False)

    def test_true_before_undetermined(self):
        self.generic_test(Before(TrueCondition(), UndeterminedCondition()), True, False)

    def test_false_before_true(self):
        self.generic_test(Before(FalseCondition(), TrueCondition()), False, True)

    def test_false_before_false(self):
        self.generic_test(Before(FalseCondition(), FalseCondition()), False, True)

    def test_false_before_undetermined(self):
        self.generic_test(Before(FalseCondition(), UndeterminedCondition()), False, True)

    def test_undetermined_before_true(self):
        self.generic_test(Before(UndeterminedCondition(), TrueCondition()), False, True)

    def test_undetermined_before_false(self):
        self.generic_test(Before(UndeterminedCondition(), FalseCondition()), False, False)

    def test_undetermined_before_undetermined(self):
        self.generic_test(Before(UndeterminedCondition(), UndeterminedCondition()), False, False)

    def test_intime_true_instant(self):
        self.generic_test(During(TrueCondition(), 0, 10), True, False)

    def test_intime_true_delay(self):
        self.generic_test(During(TrueCondition(), 5, 10), False, True)

    def test_intime_false_instant(self):
        self.generic_test(During(FalseCondition(), 0, 10), False, True)

    def test_intime_false_delay(self):
        self.generic_test(During(FalseCondition(), 5, 10), False, True)

    def test_intime_undetermined_instant(self):
        self.generic_test(During(UndeterminedCondition(), 0, 10), False, False)

    def test_intime_undetermined_delay(self):
        self.generic_test(During(UndeterminedCondition(), 5, 10), False, False)

    def test_intime_delayed_true_instant(self):
        self.generic_test(During(DelayedTrueCondition(2), 0, 10), True, False, 3)

    def test_intime_delayed_true_delay(self):
        self.generic_test(During(DelayedTrueCondition(7), 5, 10), True, False, 10)

    def test_intime_delayed_false_instant(self):
        self.generic_test(During(DelayedFalseCondition(2), 0, 10), False, True, 3)

    def test_intime_delayed_false_delay(self):
        self.generic_test(During(DelayedFalseCondition(7), 5, 10), False, True, 10)

    def test_delayed_true(self):
        self.generic_test(DelayedTrueCondition(2), False, False, 0)
        self.generic_test(DelayedTrueCondition(2), True, False, 5)

    def test_delayed_false(self):
        self.generic_test(DelayedFalseCondition(2), False, False, 0)
        self.generic_test(DelayedFalseCondition(2), False, True, 5)

    def test_if_true_then_true_else_true(self):
        self.generic_test(IfElse(TrueCondition(), TrueCondition(), TrueCondition()), True, False)

    def test_if_true_then_true_else_false(self):
        self.generic_test(IfElse(TrueCondition(), TrueCondition(), FalseCondition()), True, False)

    def test_if_true_then_true_else_undetermined(self):
        self.generic_test(IfElse(TrueCondition(), TrueCondition(), UndeterminedCondition()), True, False)

    def test_if_true_then_false_else_true(self):
        self.generic_test(IfElse(TrueCondition(), FalseCondition(), TrueCondition()), False, True)

    def test_if_true_then_false_else_false(self):
        self.generic_test(IfElse(TrueCondition(), FalseCondition(), FalseCondition()), False, True)

    def test_if_true_then_false_else_undetermined(self):
        self.generic_test(IfElse(TrueCondition(), FalseCondition(), UndeterminedCondition()), False, True)

    def test_if_true_then_undetermined_else_true(self):
        self.generic_test(IfElse(TrueCondition(), UndeterminedCondition(), TrueCondition()), False, False)

    def test_if_true_then_undetermined_else_false(self):
        self.generic_test(IfElse(TrueCondition(), UndeterminedCondition(), FalseCondition()), False, False)

    def test_if_true_then_undetermined_else_undetermined(self):
        self.generic_test(IfElse(TrueCondition(), UndeterminedCondition(), UndeterminedCondition()), False, False)

    def test_if_false_then_true_else_true(self):
        self.generic_test(IfElse(FalseCondition(), TrueCondition(), TrueCondition()), True, False)

    def test_if_false_then_true_else_false(self):
        self.generic_test(IfElse(FalseCondition(), TrueCondition(), FalseCondition()), False, True)

    def test_if_false_then_true_else_undetermined(self):
        self.generic_test(IfElse(FalseCondition(), TrueCondition(), UndeterminedCondition()), False, False)

    def test_if_false_then_false_else_true(self):
        self.generic_test(IfElse(FalseCondition(), FalseCondition(), TrueCondition()), True, False)

    def test_if_false_then_false_else_false(self):
        self.generic_test(IfElse(FalseCondition(), FalseCondition(), FalseCondition()), False, True)

    def test_if_false_then_false_else_undetermined(self):
        self.generic_test(IfElse(FalseCondition(), FalseCondition(), UndeterminedCondition()), False, False)

    def test_if_undetermined_then_true_else_true(self):
        self.generic_test(IfElse(UndeterminedCondition(), TrueCondition(), TrueCondition()), False, False)

    def test_if_undetermined_then_true_else_false(self):
        self.generic_test(IfElse(UndeterminedCondition(), TrueCondition(), FalseCondition()), False, False)

    def test_if_undetermined_then_true_else_undetermined(self):
        self.generic_test(IfElse(UndeterminedCondition(), TrueCondition(), UndeterminedCondition()), False, False)

    def test_if_undetermined_then_false_else_true(self):
        self.generic_test(IfElse(UndeterminedCondition(), FalseCondition(), TrueCondition()), False, False)

    def test_if_undetermined_then_false_else_false(self):
        self.generic_test(IfElse(UndeterminedCondition(), FalseCondition(), FalseCondition()), False, True)
        # Fail-fast

    def test_if_undetermined_then_false_else_undetermined(self):
        self.generic_test(IfElse(UndeterminedCondition(), TrueCondition(), UndeterminedCondition()), False, False)

    def test_if_undetermined_then_undetermined_else_true(self):
        self.generic_test(IfElse(UndeterminedCondition(), UndeterminedCondition(), TrueCondition()), False, False)

    def test_if_undetermined_then_undetermined_else_false(self):
        self.generic_test(IfElse(UndeterminedCondition(), UndeterminedCondition(), FalseCondition()), False, False)

    def test_if_undetermined_then_undetermined_else_undetermined(self):
        self.generic_test(IfElse(UndeterminedCondition(), UndeterminedCondition(), UndeterminedCondition()),
                          False,
                          False)


class ConditionOperatorTests(unittest.TestCase):
    def test_invert(self):
        self.assertEqual((~ TrueCondition()).__repr__(), Not(TrueCondition()).__repr__())

    def test_and(self):
        self.assertEqual((TrueCondition() & FalseCondition()).__repr__(),
                         And(TrueCondition(), FalseCondition()).__repr__())

    def test_or(self):
        self.assertEqual((TrueCondition() | FalseCondition()).__repr__(),
                         Or(TrueCondition(), FalseCondition()).__repr__())

    def test_xor(self):
        self.assertEqual((TrueCondition() ^ FalseCondition()).__repr__(),
                         Xor(TrueCondition(), FalseCondition()).__repr__())

    def test_then(self):
        self.assertEqual((TrueCondition().then(FalseCondition())).__repr__(),
                         Then(TrueCondition(), FalseCondition()).__repr__())


class OperatorsReprTests(unittest.TestCase):
    def test_true_repr(self):
        self.assertEqual(TrueCondition().__repr__(), 'TrueCondition()')

    def test_false_repr(self):
        self.assertEqual(FalseCondition().__repr__(), 'FalseCondition()')

    def test_undetermined_repr(self):
        self.assertEqual(UndeterminedCondition().__repr__(), 'UndeterminedCondition()')

    def test_and_repr(self):
        self.assertEqual(And(TrueCondition(), FalseCondition()).__repr__(), 'And(TrueCondition(), FalseCondition())')

    def test_or_repr(self):
        self.assertEqual(Or(TrueCondition(), FalseCondition()).__repr__(), 'Or(TrueCondition(), FalseCondition())')

    def test_not_repr(self):
        self.assertEqual(Not(TrueCondition()).__repr__(), 'Not(TrueCondition())')

    def test_xor_repr(self):
        self.assertEqual(Xor(TrueCondition(), FalseCondition()).__repr__(), 'Xor(TrueCondition(), FalseCondition())')

    def test_before_repr(self):
        self.assertEqual(Before(TrueCondition(), FalseCondition()).__repr__(),
                         'Before(TrueCondition(), FalseCondition())')

    def test_then_repr(self):
        self.assertEqual(Then(TrueCondition(), FalseCondition()).__repr__(), 'Then(TrueCondition(), FalseCondition())')

    def test_during_repr(self):
        self.assertEqual(During(TrueCondition(), 10, 42).__repr__(),
                         'During(TrueCondition(), 10, 42)')

    def test_delayed_true_repr(self):
        self.assertEqual(DelayedTrueCondition(42).__repr__(), 'DelayedTrueCondition(42)')

    def test_delayed_false_repr(self):
        self.assertEqual(DelayedFalseCondition(42).__repr__(), 'DelayedFalseCondition(42)')

    def test_if_else_repr(self):
        self.assertEqual(IfElse(TrueCondition(), TrueCondition(), FalseCondition()).__repr__(),
                         'IfElse(TrueCondition(), TrueCondition(), FalseCondition())')

    def test_delayed_condition_repr(self):
        self.assertEqual(DelayedCondition(TrueCondition(), 42).__repr__(),
                         'DelayedCondition(TrueCondition(), 42)')


class TemporalExpressionReprTest(unittest.TestCase):
    def test_first_time(self):
        self.assertEqual(FirstTime(True, TrueCondition(), FalseCondition()).__repr__(),
                         'FirstTime(True, TrueCondition(), FalseCondition())')

    def test_last_time(self):
        self.assertEqual(LastTime(True, TrueCondition(), FalseCondition()).__repr__(),
                         'LastTime(True, TrueCondition(), FalseCondition())')

    def test_every_time(self):
        self.assertEqual(EveryTime(True, TrueCondition(), FalseCondition()).__repr__(),
                         'EveryTime(True, TrueCondition(), FalseCondition())')


class TemporalTests(unittest.TestCase):
    def setUp(self):
        self.story = [Event('step ended'), Event('step ended'), Event('execution stopped')]

    def generic_temporal_test(self, statechart: Statechart, story: list, accept_after: bool):
        # Todo: convert the story list into a 'real' story that can be told to an interpreter

        interpreter = Interpreter(statechart)
        for event in story:
            interpreter.queue(event)

        interpreter.execute()
        self.assertEquals(accept_after, len(interpreter.configuration) == 0)

    def test_first_time_required_true_true(self):
        self.generic_temporal_test(FirstTime(True, TrueCondition(), TrueCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_first_time_required_true_false(self):
        self.generic_temporal_test(FirstTime(True, TrueCondition(), FalseCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_first_time_required_true_undetermined(self):
        self.generic_temporal_test(FirstTime(True, TrueCondition(), UndeterminedCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_first_time_required_false_true(self):
        self.generic_temporal_test(FirstTime(True, FalseCondition(), TrueCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_first_time_required_false_false(self):
        self.generic_temporal_test(FirstTime(True, FalseCondition(), FalseCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_first_time_required_false_undetermined(self):
        self.generic_temporal_test(FirstTime(True, FalseCondition(), UndeterminedCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_first_time_required_undetermined_true(self):
        self.generic_temporal_test(FirstTime(True, UndeterminedCondition(), TrueCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_first_time_required_undetermined_false(self):
        self.generic_temporal_test(FirstTime(True, UndeterminedCondition(), FalseCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_first_time_required_undetermined_undetermined(self):
        self.generic_temporal_test(FirstTime(True, UndeterminedCondition(), UndeterminedCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_first_time_forbidden_true_true(self):
        self.generic_temporal_test(FirstTime(False, TrueCondition(), TrueCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_first_time_forbidden_true_false(self):
        self.generic_temporal_test(FirstTime(False, TrueCondition(), FalseCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_first_time_forbidden_true_undetermined(self):
        self.generic_temporal_test(FirstTime(False, TrueCondition(), UndeterminedCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_first_time_forbidden_false_true(self):
        self.generic_temporal_test(FirstTime(False, FalseCondition(), TrueCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_first_time_forbidden_false_false(self):
        self.generic_temporal_test(FirstTime(False, FalseCondition(), FalseCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_first_time_forbidden_false_undetermined(self):
        self.generic_temporal_test(FirstTime(False, FalseCondition(), UndeterminedCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_first_time_forbidden_undetermined_true(self):
        self.generic_temporal_test(FirstTime(False, UndeterminedCondition(), TrueCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_first_time_forbidden_undetermined_false(self):
        self.generic_temporal_test(FirstTime(False, UndeterminedCondition(), FalseCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_first_time_forbidden_undetermined_undetermined(self):
        self.generic_temporal_test(FirstTime(False, UndeterminedCondition(), UndeterminedCondition()).generate_statechart(),
                                   self.story,
                                   False)
    
    def test_last_time_required_true_true(self):
        self.generic_temporal_test(LastTime(True, TrueCondition(), TrueCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_last_time_required_true_false(self):
        self.generic_temporal_test(LastTime(True, TrueCondition(), FalseCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_last_time_required_true_undetermined(self):
        self.generic_temporal_test(LastTime(True, TrueCondition(), UndeterminedCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_last_time_required_false_true(self):
        self.generic_temporal_test(LastTime(True, FalseCondition(), TrueCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_last_time_required_false_false(self):
        self.generic_temporal_test(LastTime(True, FalseCondition(), FalseCondition()).generate_statechart(),
                                   [Event('step ended'), Event('execution stopped')],
                                   True)

    def test_last_time_required_false_undetermined(self):
        self.generic_temporal_test(LastTime(True, FalseCondition(), UndeterminedCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_last_time_required_undetermined_true(self):
        self.generic_temporal_test(LastTime(True, UndeterminedCondition(), TrueCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_last_time_required_undetermined_false(self):
        self.generic_temporal_test(LastTime(True, UndeterminedCondition(), FalseCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_last_time_required_undetermined_undetermined(self):
        self.generic_temporal_test(LastTime(True, UndeterminedCondition(), UndeterminedCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_last_time_forbidden_true_true(self):
        self.generic_temporal_test(LastTime(False, TrueCondition(), TrueCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_last_time_forbidden_true_false(self):
        self.generic_temporal_test(LastTime(False, TrueCondition(), FalseCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_last_time_forbidden_true_undetermined(self):
        self.generic_temporal_test(LastTime(False, TrueCondition(), UndeterminedCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_last_time_forbidden_false_true(self):
        self.generic_temporal_test(LastTime(False, FalseCondition(), TrueCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_last_time_forbidden_false_false(self):
        self.generic_temporal_test(LastTime(False, FalseCondition(), FalseCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_last_time_forbidden_false_undetermined(self):
        self.generic_temporal_test(LastTime(False, FalseCondition(), UndeterminedCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_last_time_forbidden_undetermined_true(self):
        self.generic_temporal_test(LastTime(False, UndeterminedCondition(), TrueCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_last_time_forbidden_undetermined_false(self):
        self.generic_temporal_test(LastTime(False, UndeterminedCondition(), FalseCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_last_time_forbidden_undetermined_undetermined(self):
        self.generic_temporal_test(LastTime(False, UndeterminedCondition(), UndeterminedCondition()).generate_statechart(),
                                   self.story,
                                   False)
    
    def test_every_time_required_true_true(self):
        self.generic_temporal_test(LastTime(True, TrueCondition(), TrueCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_every_time_required_true_false(self):
        self.generic_temporal_test(LastTime(True, TrueCondition(), FalseCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_every_time_required_true_undetermined(self):
        self.generic_temporal_test(LastTime(True, TrueCondition(), UndeterminedCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_every_time_required_false_true(self):
        self.generic_temporal_test(LastTime(True, FalseCondition(), TrueCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_every_time_required_false_false(self):
        self.generic_temporal_test(LastTime(True, FalseCondition(), FalseCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_every_time_required_false_undetermined(self):
        self.generic_temporal_test(LastTime(True, FalseCondition(), UndeterminedCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_every_time_required_undetermined_true(self):
        self.generic_temporal_test(LastTime(True, UndeterminedCondition(), TrueCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_every_time_required_undetermined_false(self):
        self.generic_temporal_test(LastTime(True, UndeterminedCondition(), FalseCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_every_time_required_undetermined_undetermined(self):
        self.generic_temporal_test(LastTime(True, UndeterminedCondition(), UndeterminedCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_every_time_forbidden_true_true(self):
        self.generic_temporal_test(LastTime(False, TrueCondition(), TrueCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_every_time_forbidden_true_false(self):
        self.generic_temporal_test(LastTime(False, TrueCondition(), FalseCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_every_time_forbidden_true_undetermined(self):
        self.generic_temporal_test(LastTime(False, TrueCondition(), UndeterminedCondition()).generate_statechart(),
                                   self.story,
                                   True)

    def test_every_time_forbidden_false_true(self):
        self.generic_temporal_test(LastTime(False, FalseCondition(), TrueCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_every_time_forbidden_false_false(self):
        self.generic_temporal_test(LastTime(False, FalseCondition(), FalseCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_every_time_forbidden_false_undetermined(self):
        self.generic_temporal_test(LastTime(False, FalseCondition(), UndeterminedCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_every_time_forbidden_undetermined_true(self):
        self.generic_temporal_test(LastTime(False, UndeterminedCondition(), TrueCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_every_time_forbidden_undetermined_false(self):
        self.generic_temporal_test(LastTime(False, UndeterminedCondition(), FalseCondition()).generate_statechart(),
                                   self.story,
                                   False)

    def test_every_time_forbidden_undetermined_undetermined(self):
        self.generic_temporal_test(LastTime(False, UndeterminedCondition(), UndeterminedCondition()).generate_statechart(),
                                   self.story,
                                   False)

    
