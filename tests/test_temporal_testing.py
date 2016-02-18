import unittest
from sismic.temporal_testing import *
from sismic.temporal_testing import *
from sismic.interpreter import Interpreter
from sismic.model import Event, Statechart, CompoundState, BasicState, Transition
from sismic.testing import teststory_from_trace
from sismic.temporal_testing import prepare_first_time_expression


class PropertiesTests(unittest.TestCase):
    def setUp(self):
        self.sequential_statechart = Statechart("sequential")
        initial_state = CompoundState('initial_state', initial='a_state')
        a_state = BasicState('a_state')
        b_state = BasicState('b_state')
        self.sequential_statechart.add_state(initial_state, None)
        self.sequential_statechart.add_state(a_state, 'initial_state')
        self.sequential_statechart.add_state(b_state, 'initial_state')
        self.sequential_statechart.add_transition(Transition(source='a_state', target='b_state', event='event'))
        self.sequential_interpreter = Interpreter(self.sequential_statechart)
        self.sequential_interpreter.queue(Event('event'))

    def test_enter(self):
        test_statechart = Statechart('test')
        test_initial_state = CompoundState('initial_state', initial='Enter')
        enter_state = Enter('b_state')
        out_state = BasicState('out')
        test_statechart.add_state(test_initial_state, None)
        test_statechart.add_state(out_state, 'initial_state')
        enter_state.add_to(test_statechart, 'Enter', 'initial_state', 'out', None)
        test_interpreter = Interpreter(test_statechart)

        self.assertFalse('out' in test_interpreter.configuration)

        self.sequential_interpreter.execute()
        trace = self.sequential_interpreter.trace
        story = teststory_from_trace(trace)
        story.tell(test_interpreter)

        self.assertTrue('out' in test_interpreter.configuration)

    def test_exit(self):
        test_statechart = Statechart('test')
        test_initial_state = CompoundState('initial_state', initial='Enter')
        enter_state = Enter('b_state')
        out_state = BasicState('out')
        test_statechart.add_state(test_initial_state, None)
        test_statechart.add_state(out_state, 'initial_state')
        enter_state.add_to(test_statechart, 'Enter', 'initial_state', 'out', None)
        test_interpreter = Interpreter(test_statechart)

        self.assertFalse('out' in test_interpreter.configuration)

        self.sequential_interpreter.execute()
        trace = self.sequential_interpreter.trace
        story = teststory_from_trace(trace)
        story.tell(test_interpreter)

        self.assertTrue('out' in test_interpreter.configuration)


class OperatorsTest(unittest.TestCase):
    def generic_test(self, condition: Condition, success_expected: bool, failure_expected: bool, delay: int = 0):

        statechart = Statechart('test')
        initial_state = CompoundState('initial_state', initial='Cond')
        statechart.add_state(initial_state, None)

        success_state = BasicState('success')
        statechart.add_state(success_state, 'initial_state')

        failure_state = BasicState('failure')
        statechart.add_state(failure_state, 'initial_state')

        condition.add_to(statechart=statechart, id='Cond', parent_id='initial_state',
                         success_state_id='success', failure_state_id='failure')

        interpreter = Interpreter(statechart)

        self.assertFalse('success' in interpreter.configuration)
        self.assertFalse('failure' in interpreter.configuration)

        interpreter.time += delay
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
        self.generic_test(InTime(TrueCondition(), 0, 10), True, False)

    def test_intime_true_delay(self):
        self.generic_test(InTime(TrueCondition(), 5, 10), False, True)

    def test_intime_false_instant(self):
        self.generic_test(InTime(FalseCondition(), 0, 10), False, True)

    def test_intime_false_delay(self):
        self.generic_test(InTime(FalseCondition(), 5, 10), False, True)

    def test_intime_undetermined_instant(self):
        self.generic_test(InTime(UndeterminedCondition(), 0, 10), False, False)

    def test_intime_undetermined_delay(self):
        self.generic_test(InTime(UndeterminedCondition(), 5, 10), False, False)

    def test_intime_delayed_true_instant(self):
        self.generic_test(InTime(DelayedTrueCondition(2), 0, 10), True, False, 3)

    def test_intime_delayed_true_delay(self):
        self.generic_test(InTime(DelayedTrueCondition(7), 5, 10), True, False, 10)

    def test_intime_delayed_false_instant(self):
        self.generic_test(InTime(DelayedFalseCondition(2), 0, 10), False, True, 3)

    def test_intime_delayed_false_delay(self):
        self.generic_test(InTime(DelayedFalseCondition(7), 5, 10), False, True, 10)

    def test_delayed_true(self):
        self.generic_test(DelayedTrueCondition(2), False, False, 0)
        self.generic_test(DelayedTrueCondition(2), True, False, 5)

    def test_delayed_true(self):
        self.generic_test(DelayedFalseCondition(2), False, False, 0)
        self.generic_test(DelayedFalseCondition(2), False, True, 5)


class TemporalTests(unittest.TestCase):

    def generic_temporal_test(self, statechart: Statechart, story: list, accept_before: bool, accept_after: bool):
        # Todo: convert the story list into a 'real' story that can be told to an interpreter

        interpreter = Interpreter(statechart)
        self.assertEquals(accept_before, len(interpreter.configuration) == 0)
        for event in story:
            interpreter.queue(event)

        interpreter.execute()
        print(interpreter.configuration)
        self.assertEquals(accept_after, len(interpreter.configuration) == 0)

    def test_first_time_required_true_true(self):
        self.generic_temporal_test(prepare_first_time_expression(True, TrueCondition(), TrueCondition()),
                              [Event('stopped')],
                              False,
                              True)

    def test_first_time_required_true_false(self):
        self.generic_temporal_test(prepare_first_time_expression(True, TrueCondition(), FalseCondition()),
                              [Event('stopped')],
                              False,
                              False)

    def test_first_time_required_true_undetermined(self):
        self.generic_temporal_test(prepare_first_time_expression(True, TrueCondition(), UndeterminedCondition()),
                              [Event('stopped')],
                              False,
                              False)

    def test_first_time_required_false_true(self): # TODO
        self.generic_temporal_test(prepare_first_time_expression(True, FalseCondition(), TrueCondition()),
                              [Event('stopped')],
                              False,
                              False)

    def test_first_time_required_false_false(self): # TODO
        self.generic_temporal_test(prepare_first_time_expression(True, FalseCondition(), FalseCondition()),
                              [Event('stopped')],
                              False,
                              False)

    def test_first_time_required_false_undetermined(self): # TODO
        self.generic_temporal_test(prepare_first_time_expression(True, FalseCondition(), UndeterminedCondition()),
                              [Event('stopped')],
                              False,
                              False)

    def test_first_time_required_undetermined_true(self):
        self.generic_temporal_test(prepare_first_time_expression(True, UndeterminedCondition(), TrueCondition()),
                              [Event('stopped')],
                              False,
                              True)

    def test_first_time_required_undetermined_false(self):
        self.generic_temporal_test(prepare_first_time_expression(True, UndeterminedCondition(), FalseCondition()),
                              [Event('stopped')],
                              False,
                              True)

    def test_first_time_required_undetermined_undetermined(self):
        self.generic_temporal_test(prepare_first_time_expression(True, UndeterminedCondition(), UndeterminedCondition()),
                              [Event('stopped')],
                              False,
                              True)






