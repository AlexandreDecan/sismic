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
        self.sequential_statechart = Statechart('tested_statechart')
        initial_state = CompoundState('initial_state', initial='a_state')
        a_state = BasicState('a_state')
        b_state = BasicState('b_state')
        self.sequential_statechart.add_state(initial_state, None)
        self.sequential_statechart.add_state(a_state, 'initial_state')
        self.sequential_statechart.add_state(b_state, 'initial_state')
        self.sequential_statechart.add_transition(Transition(source='a_state', target='b_state', event='event'))

    def generic_test(self,
                     tested_statechart: Statechart,
                     events: list,
                     property: Condition,
                     expected_success: bool,
                     expected_failure: bool):
        from sismic.interpreter import log_trace
        tester_statechart = Statechart('tester_statechart')

        tester_statechart.add_state(OrthogonalState('parallel_state'), None)
        tester_statechart.add_state(CompoundState('testing_area', initial='property'), parent='parallel_state')
        tester_statechart.add_state(BasicState('success_state'), parent='testing_area')
        tester_statechart.add_state(BasicState('failure_state'), parent='testing_area')

        property.add_to(tester_statechart,
                        id='property',
                        parent_id='testing_area',
                        status_id='parallel_state',
                        success_id='success_state',
                        failure_id='failure_state')

        tester_interpreter = Interpreter(tester_statechart)

        self.assertFalse('success_state' in tester_interpreter.configuration)
        self.assertFalse('failure_state' in tester_interpreter.configuration)

        tested_interpreter = Interpreter(tested_statechart)
        trace = log_trace(tested_interpreter)

        for event in events:
            tested_interpreter.queue(event)

        tested_interpreter.execute()

        story = teststory_from_trace(trace)
        story.tell(tester_interpreter)

        self.assertEqual(expected_success, 'success_state' in tester_interpreter.configuration)
        self.assertEqual(expected_failure, 'failure_state' in tester_interpreter.configuration)

    def test_enter_state_right(self):
        self.generic_test(self.sequential_statechart, [Event('event')], EnterState('b_state'), True, False)

    def test_enter_state_wrong(self):
        self.generic_test(self.sequential_statechart, [Event('event')], EnterState('foo'), False, False)

    def test_enter_any_state_right(self):
        self.generic_test(self.sequential_statechart, [Event('event')], EnterAnyState(), True, False)

    def test_exit_state_right(self):
        self.generic_test(self.sequential_statechart, [Event('event')], ExitState('a_state'), True, False)

    def test_exit_state_wrong(self):
        self.generic_test(self.sequential_statechart, [Event('event')], ExitState('b_state'), False, False)

    def test_exit_any_state_right(self):
        self.generic_test(self.sequential_statechart, [Event('event')], ExitAnyState(), True, False)

    def test_exit_any_state_wrong(self):
        self.generic_test(self.sequential_statechart, [Event('foo')], ExitAnyState(), False, False)

    def test_check_guard_success(self):
        statechart = Statechart('statechart')
        statechart.add_state(OrthogonalState('parallel_state'), parent=None)

        initial_state = CompoundState('initial_state', initial='condition')
        statechart.add_state(initial_state, parent='parallel_state')

        statechart.add_state(BasicState('success'), parent='initial_state')
        statechart.add_state(BasicState('failure'), parent='initial_state')

        CheckGuard('x == 1').add_to(statechart=statechart,
                                    id='condition',
                                    parent_id='initial_state',
                                    status_id='parallel_state',
                                    success_id='success',
                                    failure_id='failure')

        interpreter = Interpreter(statechart)
        self.assertFalse('success' in interpreter.configuration)
        self.assertFalse('failure' in interpreter.configuration)

        interpreter.execute()
        self.assertFalse('success' in interpreter.configuration)
        self.assertFalse('failure' in interpreter.configuration)

        interpreter.context['x'] = 1
        interpreter.queue(Event(Condition.END_STEP_EVENT))

        interpreter.execute()
        self.assertTrue('success' in interpreter.configuration)
        self.assertFalse('failure' in interpreter.configuration)

    def test_check_guard_failure(self):
        statechart = Statechart('statechart')
        statechart.add_state(OrthogonalState('parallel_state'), parent=None)

        initial_state = CompoundState('initial_state', initial='condition')
        statechart.add_state(initial_state, parent='parallel_state')
        statechart.add_state(BasicState('success'), parent='initial_state')
        statechart.add_state(BasicState('failure'), parent='initial_state')

        CheckGuard('x == 1').add_to(statechart=statechart,
                                    id='condition',
                                    parent_id='initial_state',
                                    status_id='parallel_state',
                                    success_id='success',
                                    failure_id='failure')

        interpreter = Interpreter(statechart)
        self.assertFalse('success' in interpreter.configuration)
        self.assertFalse('failure' in interpreter.configuration)

        interpreter.execute()
        self.assertFalse('success' in interpreter.configuration)
        self.assertFalse('failure' in interpreter.configuration)

        interpreter.context['x'] = 42
        interpreter.queue(Event(Condition.END_STEP_EVENT))

        interpreter.execute()
        self.assertFalse('success' in interpreter.configuration)
        self.assertTrue('failure' in interpreter.configuration)

    def test_consume_event_success(self):
        self.generic_test(self.sequential_statechart, [Event('foo')], ConsumeEvent('foo'), True, False)

    def test_consume_event_failure(self):
        self.generic_test(self.sequential_statechart, [Event('bar')], ConsumeEvent('foo'), False, False)

    def test_consume_any_event(self):
        self.generic_test(self.sequential_statechart, [Event('foo')], ConsumeAnyEvent(), True, False)

    def test_execution_started(self):
        self.generic_test(self.sequential_statechart, [Event('foo')], ExecutionStart(), True, False)

    def test_execution_stopped(self):
        self.generic_test(self.sequential_statechart, [Event('foo')], ExecutionStop(), True, False)

    def test_start_step_started(self):
        self.generic_test(self.sequential_statechart, [Event('foo')], StartStep(), True, False)

    def test_step_end_started(self):
        self.generic_test(self.sequential_statechart, [Event('foo')], ExecutionStop(), True, False)

    def test_transition_process_failure_started(self):
        self.generic_test(self.sequential_statechart, [Event('foo')], TransitionProcess(), False, False)

    def test_transition_process_any_started(self):
        self.generic_test(self.sequential_statechart, [Event('event')], TransitionProcess(), True, False)

    def test_transition_process_right_event(self):
        self.generic_test(self.sequential_statechart,
                          [Event('event')],
                          TransitionProcess(event='event'),
                          True,
                          False)

    def test_transition_processn_wrong_event(self):
        self.generic_test(self.sequential_statechart,
                          [Event('event')],
                          TransitionProcess(event='foo'),
                          False,
                          False)

    def test_transition_process_right_source(self):
        self.generic_test(self.sequential_statechart,
                          [Event('event')],
                          TransitionProcess(source='a_state'),
                          True,
                          False)

    def test_transition_process_wrong_source(self):
        self.generic_test(self.sequential_statechart,
                          [Event('event')],
                          TransitionProcess(source='foo'),
                          False,
                          False)

    def test_transition_process_right_target(self):
        self.generic_test(self.sequential_statechart,
                          [Event('event')],
                          TransitionProcess(target='b_state'),
                          True,
                          False)

    def test_transition_process_wrong_target(self):
        self.generic_test(self.sequential_statechart,
                          [Event('event')],
                          TransitionProcess(target='foo'),
                          False,
                          False)

    def test_transition_process_right_eventless(self):
        self.sequential_statechart.remove_transition(Transition(source='a_state', target='b_state', event='event'))
        self.sequential_statechart.add_transition(Transition(source='a_state', target='b_state'))

        self.generic_test(self.sequential_statechart,
                          [Event('event')],
                          TransitionProcess(event=''),
                          True,
                          False)

    def test_transition_process_wrong_eventless(self):
        self.generic_test(self.sequential_statechart,
                          [Event('event')],
                          TransitionProcess(event=''),
                          False,
                          False)

    def test_active_state_right(self):
        self.sequential_statechart.remove_transition(Transition(source='a_state', target='b_state', event='event'))

        self.generic_test(self.sequential_statechart,
                          [Event('event')],
                          Then(ConsumeEvent('event'), ActiveState(state='a_state')),
                          True,
                          False)

    def test_active_state_wrong(self):
        self.sequential_statechart.remove_transition(Transition(source='a_state', target='b_state', event='event'))

        self.generic_test(self.sequential_statechart,
                          [Event('event')],
                          Then(ConsumeEvent('event'), ActiveState(state='b_state')),
                          False,
                          True)

    def test_inactive_state_right(self):
        self.sequential_statechart.remove_transition(Transition(source='a_state', target='b_state', event='event'))

        self.generic_test(self.sequential_statechart,
                          [Event('event')],
                          Then(ConsumeEvent('event'), InactiveState(state='b_state')),
                          True,
                          False)

    def test_inactive_state_wrong(self):
        self.sequential_statechart.remove_transition(Transition(source='a_state', target='b_state', event='event'))

        self.generic_test(self.sequential_statechart,
                          [Event('event')],
                          Then(ConsumeEvent('event'), InactiveState(state='a_state')),
                          False,
                          True)

    def test_before_right(self):
        self.generic_test(self.sequential_statechart,
                          [Event('event')],
                          Before(EnterState('a_state'), EnterState('b_state')),
                          True,
                          False)

    def test_true_before_false_right(self):
        self.generic_test(self.sequential_statechart,
                          [Event('event')],
                          Before(EnterState('a_state'), FalseCondition()),
                          True,
                          False)

    def test_true_before_undetermined_right(self):
        self.generic_test(self.sequential_statechart,
                          [Event('event')],
                          Before(EnterState('a_state'), UndeterminedCondition()),
                          True,
                          False)

    def test_before_wrong(self):
        self.generic_test(self.sequential_statechart,
                          [Event('event')],
                          Before(EnterState('b_state'), EnterState('a_state')),
                          False,
                          True)

    def test_before_false_right(self):
        self.generic_test(self.sequential_statechart,
                          [Event('event')],
                          Before(EnterState('b_state'), FalseCondition()),
                          True,
                          False)

    def test_before_undetermined_right(self):
        self.generic_test(self.sequential_statechart,
                          [Event('event')],
                          Before(EnterState('b_state'), UndeterminedCondition()),
                          True,
                          False)


class PropertyReprTest(unittest.TestCase):
    def test_enter_state_repr(self):
        self.assertEqual('EnterState("foo")', EnterState('foo').__repr__())

    def test_enter_any_state_repr(self):
        self.assertEqual('EnterAnyState()', EnterAnyState().__repr__())

    def test_exit_state_repr(self):
        self.assertEqual('ExitState("foo")', ExitState('foo').__repr__())

    def test_exit_any_state_repr(self):
        self.assertEqual('ExitAnyState()', ExitAnyState().__repr__())

    def test_check_guard_repr(self):
        self.assertEqual('CheckGuard("foo")', CheckGuard('foo').__repr__())

    def test_consume_repr(self):
        self.assertEqual('ConsumeEvent("foo")', ConsumeEvent('foo').__repr__())

    def test_consume_any_repr(self):
        self.assertEqual('ConsumeAnyEvent()', ConsumeAnyEvent().__repr__())

    def test_execution_start_repr(self):
        self.assertEqual('ExecutionStart()', ExecutionStart().__repr__())

    def test_execution_stop_repr(self):
        self.assertEqual('ExecutionStop()', ExecutionStop().__repr__())

    def test_step_start_repr(self):
        self.assertEqual('StartStep()', StartStep().__repr__())

    def test_step_stop_repr(self):
        self.assertEqual('EndStep()', EndStep().__repr__())

    def test_transition_process_empty_repr(self):
        self.assertEqual('TransitionProcess(None, None, None)', TransitionProcess().__repr__())

    def test_transition_process_source_repr(self):
        self.assertEqual('TransitionProcess("foo", None, None)', TransitionProcess(source='foo').__repr__())

    def test_transition_process_target_repr(self):
        self.assertEqual('TransitionProcess(None, "foo", None)', TransitionProcess(target='foo').__repr__())

    def test_transition_process_event_repr(self):
        self.assertEqual('TransitionProcess(None, None, "foo")', TransitionProcess(event='foo').__repr__())

    def test_active_state_repr(self):
        self.assertEqual('ActiveState("foo")', ActiveState('foo').__repr__())

    def test_inactive_state_repr(self):
        self.assertEqual('InactiveState("foo")', InactiveState('foo').__repr__())


class OperatorsTest(unittest.TestCase):
    def generic_test(self, condition: Condition, success_expected: bool, failure_expected: bool, delay: int = 0):
        statechart = Statechart('test')
        parallel_state = OrthogonalState('parallel_state')
        statechart.add_state(parallel_state, parent=None)

        initial_state = CompoundState('initial_state', initial='Cond')
        statechart.add_state(initial_state, "parallel_state")

        statechart.add_state(BasicState('success'), 'initial_state')
        statechart.add_state(BasicState('failure'), 'initial_state')

        condition.add_to(statechart=statechart,
                         id='Cond',
                         parent_id='initial_state',
                         status_id=parallel_state,
                         success_id='success',
                         failure_id='failure')

        interpreter = Interpreter(statechart)

        self.assertFalse('success' in interpreter.configuration)
        self.assertFalse('failure' in interpreter.configuration)

        interpreter.execute()

        interpreter.time += delay
        interpreter.queue(Event(Condition.END_STEP_EVENT))
        interpreter.queue(Event(Condition.END_STEP_EVENT))
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

    def test_at_least_once(self):
        self.assertEqual(AtLeastOnce(True, TrueCondition(), FalseCondition()).__repr__(),
                         'AtLeastOnce(True, TrueCondition(), FalseCondition())')


class TemporalTests(unittest.TestCase):
    def setUp(self):
        self.story = [Event(Condition.END_STEP_EVENT), Event(Condition.END_STEP_EVENT), Event('execution stopped')]

    def generic_temporal_test(self, expression: TemporalExpression, story: list, accept_after: bool):
        # Todo: convert the story list into a 'real' story that can be told to an interpreter
        statechart = expression.generate_statechart()
        interpreter = Interpreter(statechart)

        for event in story:
            interpreter.queue(event)

        interpreter.execute()

        self.assertEqual(len(interpreter.configuration) == 0, accept_after)

    def test_first_time_required_true_true(self):
        self.generic_temporal_test(FirstTime(True, TrueCondition(), TrueCondition()),
                                   self.story,
                                   True)

    def test_first_time_required_true_false(self):
        self.generic_temporal_test(FirstTime(True, TrueCondition(), FalseCondition()),
                                   self.story,
                                   False)

    def test_first_time_required_true_undetermined(self):
        self.generic_temporal_test(FirstTime(True, TrueCondition(), UndeterminedCondition()),
                                   self.story,
                                   False)

    def test_first_time_required_false_true(self):
        self.generic_temporal_test(FirstTime(True, FalseCondition(), TrueCondition()),
                                   self.story,
                                   True)

    def test_first_time_required_false_false(self):
        self.generic_temporal_test(FirstTime(True, FalseCondition(), FalseCondition()),
                                   self.story,
                                   True)

    def test_first_time_required_false_undetermined(self):
        self.generic_temporal_test(FirstTime(True, FalseCondition(), UndeterminedCondition()),
                                   self.story,
                                   True)

    def test_first_time_required_undetermined_true(self):
        self.generic_temporal_test(FirstTime(True, UndeterminedCondition(), TrueCondition()),
                                   self.story,
                                   True)

    def test_first_time_required_undetermined_false(self):
        self.generic_temporal_test(FirstTime(True, UndeterminedCondition(), FalseCondition()),
                                   self.story,
                                   True)

    def test_first_time_required_undetermined_undetermined(self):
        self.generic_temporal_test(FirstTime(True, UndeterminedCondition(), UndeterminedCondition()),
                                   self.story,
                                   True)

    def test_first_time_forbidden_true_true(self):
        self.generic_temporal_test(FirstTime(False, TrueCondition(), TrueCondition()),
                                   self.story,
                                   False)

    def test_first_time_forbidden_true_false(self):
        self.generic_temporal_test(FirstTime(False, TrueCondition(), FalseCondition()),
                                   self.story,
                                   True)

    def test_first_time_forbidden_true_undetermined(self):
        self.generic_temporal_test(FirstTime(False, TrueCondition(), UndeterminedCondition()),
                                   self.story,
                                   True)

    def test_first_time_forbidden_false_true(self):
        self.generic_temporal_test(FirstTime(False, FalseCondition(), TrueCondition()),
                                   self.story,
                                   False)

    def test_first_time_forbidden_false_false(self):
        self.generic_temporal_test(FirstTime(False, FalseCondition(), FalseCondition()),
                                   self.story,
                                   False)

    def test_first_time_forbidden_false_undetermined(self):
        self.generic_temporal_test(FirstTime(False, FalseCondition(), UndeterminedCondition()),
                                   self.story,
                                   False)

    def test_first_time_forbidden_undetermined_true(self):
        self.generic_temporal_test(FirstTime(False, UndeterminedCondition(), TrueCondition()),
                                   self.story,
                                   False)

    def test_first_time_forbidden_undetermined_false(self):
        self.generic_temporal_test(FirstTime(False, UndeterminedCondition(), FalseCondition()),
                                   self.story,
                                   False)

    def test_first_time_forbidden_undetermined_undetermined(self):
        self.generic_temporal_test(FirstTime(False, UndeterminedCondition(), UndeterminedCondition()),
                                   self.story,
                                   False)
    
    def test_last_time_required_true_true(self):
        self.generic_temporal_test(LastTime(True, TrueCondition(), TrueCondition()),
                                   self.story,
                                   True)

    def test_last_time_required_true_false(self):
        self.generic_temporal_test(LastTime(True, TrueCondition(), FalseCondition()),
                                   self.story,
                                   False)

    def test_last_time_required_true_undetermined(self):
        self.generic_temporal_test(LastTime(True, TrueCondition(), UndeterminedCondition()),
                                   self.story,
                                   False)

    def test_last_time_required_false_true(self):
        self.generic_temporal_test(LastTime(True, FalseCondition(), TrueCondition()),
                                   self.story,
                                   True)

    def test_last_time_required_false_false(self):
        self.generic_temporal_test(LastTime(True, FalseCondition(), FalseCondition()),
                                   self.story,
                                   True)

    def test_last_time_required_false_undetermined(self):
        self.generic_temporal_test(LastTime(True, FalseCondition(), UndeterminedCondition()),
                                   self.story,
                                   True)

    def test_last_time_required_undetermined_true(self):
        self.generic_temporal_test(LastTime(True, UndeterminedCondition(), TrueCondition()),
                                   self.story,
                                   True)

    def test_last_time_required_undetermined_false(self):
        self.generic_temporal_test(LastTime(True, UndeterminedCondition(), FalseCondition()),
                                   self.story,
                                   True)

    def test_last_time_required_undetermined_undetermined(self):
        self.generic_temporal_test(LastTime(True, UndeterminedCondition(), UndeterminedCondition()),
                                   self.story,
                                   True)

    def test_last_time_forbidden_true_true(self):
        self.generic_temporal_test(LastTime(False, TrueCondition(), TrueCondition()),
                                   self.story,
                                   False)

    def test_last_time_forbidden_true_false(self):
        self.generic_temporal_test(LastTime(False, TrueCondition(), FalseCondition()),
                                   self.story,
                                   True)

    def test_last_time_forbidden_true_undetermined(self):
        self.generic_temporal_test(LastTime(False, TrueCondition(), UndeterminedCondition()),
                                   self.story,
                                   True)

    def test_last_time_forbidden_false_true(self):
        self.generic_temporal_test(LastTime(False, FalseCondition(), TrueCondition()),
                                   self.story,
                                   False)

    def test_last_time_forbidden_false_false(self):
        self.generic_temporal_test(LastTime(False, FalseCondition(), FalseCondition()),
                                   self.story,
                                   False)

    def test_last_time_forbidden_false_undetermined(self):
        self.generic_temporal_test(LastTime(False, FalseCondition(), UndeterminedCondition()),
                                   self.story,
                                   False)

    def test_last_time_forbidden_undetermined_true(self):
        self.generic_temporal_test(LastTime(False, UndeterminedCondition(), TrueCondition()),
                                   self.story,
                                   False)

    def test_last_time_forbidden_undetermined_false(self):
        self.generic_temporal_test(LastTime(False, UndeterminedCondition(), FalseCondition()),
                                   self.story,
                                   False)

    def test_last_time_forbidden_undetermined_undetermined(self):
        self.generic_temporal_test(LastTime(False, UndeterminedCondition(), UndeterminedCondition()),
                                   self.story,
                                   False)
    
    def test_every_time_required_true_true(self):
        self.generic_temporal_test(EveryTime(True, TrueCondition(), TrueCondition()),
                                   self.story,
                                   True)

    def test_every_time_required_true_false(self):
        self.generic_temporal_test(EveryTime(True, TrueCondition(), FalseCondition()),
                                   self.story,
                                   False)

    def test_every_time_required_true_undetermined(self):
        self.generic_temporal_test(EveryTime(True, TrueCondition(), UndeterminedCondition()),
                                   self.story,
                                   False)

    def test_every_time_required_false_true(self):
        self.generic_temporal_test(EveryTime(True, FalseCondition(), TrueCondition()),
                                   self.story,
                                   True)

    def test_every_time_required_false_false(self):
        self.generic_temporal_test(EveryTime(True, FalseCondition(), FalseCondition()),
                                   self.story,
                                   True)

    def test_every_time_required_false_undetermined(self):
        self.generic_temporal_test(EveryTime(True, FalseCondition(), UndeterminedCondition()),
                                   self.story,
                                   True)

    def test_every_time_required_undetermined_true(self):
        self.generic_temporal_test(EveryTime(True, UndeterminedCondition(), TrueCondition()),
                                   self.story,
                                   True)

    def test_every_time_required_undetermined_false(self):
        self.generic_temporal_test(EveryTime(True, UndeterminedCondition(), FalseCondition()),
                                   self.story,
                                   True)

    def test_every_time_required_undetermined_undetermined(self):
        self.generic_temporal_test(EveryTime(True, UndeterminedCondition(), UndeterminedCondition()),
                                   self.story,
                                   True)

    def test_every_time_forbidden_true_true(self):
        self.generic_temporal_test(EveryTime(False, TrueCondition(), TrueCondition()),
                                   self.story,
                                   False)

    def test_every_time_forbidden_true_false(self):
        self.generic_temporal_test(EveryTime(False, TrueCondition(), FalseCondition()),
                                   self.story,
                                   True)

    def test_every_time_forbidden_true_undetermined(self):
        self.generic_temporal_test(EveryTime(False, TrueCondition(), UndeterminedCondition()),
                                   self.story,
                                   True)

    def test_every_time_forbidden_false_true(self):
        self.generic_temporal_test(EveryTime(False, FalseCondition(), TrueCondition()),
                                   self.story,
                                   False)

    def test_every_time_forbidden_false_false(self):
        self.generic_temporal_test(EveryTime(False, FalseCondition(), FalseCondition()),
                                   self.story,
                                   False)

    def test_every_time_forbidden_false_undetermined(self):
        self.generic_temporal_test(EveryTime(False, FalseCondition(), UndeterminedCondition()),
                                   self.story,
                                   False)

    def test_every_time_forbidden_undetermined_true(self):
        self.generic_temporal_test(EveryTime(False, UndeterminedCondition(), TrueCondition()),
                                   self.story,
                                   False)

    def test_every_time_forbidden_undetermined_false(self):
        self.generic_temporal_test(EveryTime(False, UndeterminedCondition(), FalseCondition()),
                                   self.story,
                                   False)

    def test_every_time_forbidden_undetermined_undetermined(self):
        self.generic_temporal_test(EveryTime(False, UndeterminedCondition(), UndeterminedCondition()),
                                   self.story,
                                   False)

    def test_at_least_once_required_true_true(self):
        self.generic_temporal_test(AtLeastOnce(True, TrueCondition(), TrueCondition()),
                                   self.story,
                                   True)

    def test_at_least_once_required_true_false(self):
        self.generic_temporal_test(AtLeastOnce(True, TrueCondition(), FalseCondition()),
                                   self.story,
                                   False)

    def test_at_least_once_required_true_undetermined(self):
        self.generic_temporal_test(AtLeastOnce(True, TrueCondition(), UndeterminedCondition()),
                                   self.story,
                                   False)

    def test_at_least_once_required_false_true(self):
        self.generic_temporal_test(AtLeastOnce(True, FalseCondition(), TrueCondition()),
                                   self.story,
                                   True)

    def test_at_least_once_required_false_false(self):
        self.generic_temporal_test(AtLeastOnce(True, FalseCondition(), FalseCondition()),
                                   self.story,
                                   True)

    def test_at_least_once_required_false_undetermined(self):
        self.generic_temporal_test(AtLeastOnce(True, FalseCondition(), UndeterminedCondition()),
                                   self.story,
                                   True)

    def test_at_least_once_required_undetermined_true(self):
        self.generic_temporal_test(AtLeastOnce(True, UndeterminedCondition(), TrueCondition()),
                                   self.story,
                                   True)

    def test_at_least_once_required_undetermined_false(self):
        self.generic_temporal_test(AtLeastOnce(True, UndeterminedCondition(), FalseCondition()),
                                   self.story,
                                   True)

    def test_at_least_once_required_undetermined_undetermined(self):
        self.generic_temporal_test(AtLeastOnce(True, UndeterminedCondition(), UndeterminedCondition()),
                                   self.story,
                                   True)

    def test_at_least_once_forbidden_true_true(self):
        self.generic_temporal_test(AtLeastOnce(False, TrueCondition(), TrueCondition()),
                                   self.story,
                                   False)

    def test_at_least_once_forbidden_true_false(self):
        self.generic_temporal_test(AtLeastOnce(False, TrueCondition(), FalseCondition()),
                                   self.story,
                                   True)

    def test_at_least_once_forbidden_true_undetermined(self):
        self.generic_temporal_test(AtLeastOnce(False, TrueCondition(), UndeterminedCondition()),
                                   self.story,
                                   True)

    def test_at_least_once_forbidden_false_true(self):
        self.generic_temporal_test(AtLeastOnce(False, FalseCondition(), TrueCondition()),
                                   self.story,
                                   False)

    def test_at_least_once_forbidden_false_false(self):
        self.generic_temporal_test(AtLeastOnce(False, FalseCondition(), FalseCondition()),
                                   self.story,
                                   False)

    def test_at_least_once_forbidden_false_undetermined(self):
        self.generic_temporal_test(AtLeastOnce(False, FalseCondition(), UndeterminedCondition()),
                                   self.story,
                                   False)

    def test_at_least_once_forbidden_undetermined_true(self):
        self.generic_temporal_test(AtLeastOnce(False, UndeterminedCondition(), TrueCondition()),
                                   self.story,
                                   False)

    def test_at_least_once_forbidden_undetermined_false(self):
        self.generic_temporal_test(AtLeastOnce(False, UndeterminedCondition(), FalseCondition()),
                                   self.story,
                                   False)

    def test_at_least_once_forbidden_undetermined_undetermined(self):
        self.generic_temporal_test(AtLeastOnce(False, UndeterminedCondition(), UndeterminedCondition()),
                                   self.story,
                                   False)