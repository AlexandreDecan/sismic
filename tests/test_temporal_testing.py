import unittest
from sismic.temporal_testing import Enter, Exit, And, Or, FalseCondition, TrueCondition, Condition
from sismic.interpreter import Interpreter
from sismic.model import Event, Statechart, CompoundState, BasicState, Transition
from sismic.testing import teststory_from_trace
from sismic.io.text import export_to_tree

class TemporalTests(unittest.TestCase):
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

    def generic_test(self, condition: Condition, success_expected: bool, failure_expected: bool):
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

        self.sequential_interpreter.execute()
        trace = self.sequential_interpreter.trace
        story = teststory_from_trace(trace)
        story.tell(interpreter)

        self.assertEqual(success_expected, 'success' in interpreter.configuration)
        self.assertEqual(failure_expected, 'failure' in interpreter.configuration)

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

    def test_and(self):
        """
        Tests if a is exited AND b is entered.
        """

        statechart = Statechart('test')
        initial_state = CompoundState('initial_state', initial='And')
        and_state = And(Enter('b_state'), Exit('a_state'))

        statechart.add_state(initial_state, None)

        success_state = BasicState('success')
        statechart.add_state(success_state, 'initial_state')

        failure_state = BasicState('failure')
        statechart.add_state(failure_state, 'initial_state')

        and_state.add_to(statechart=statechart, id='And', parent_id='initial_state',
                         success_state_id='success', failure_state_id='failure')
        interpreter = Interpreter(statechart)

        self.assertFalse('success' in interpreter.configuration)
        self.assertFalse('failure' in interpreter.configuration)

        self.sequential_interpreter.execute()
        trace = self.sequential_interpreter.trace
        story = teststory_from_trace(trace)
        story.tell(interpreter)

        self.assertTrue('success' in interpreter.configuration)
        self.assertFalse('failure' in interpreter.configuration)

    def test_true_and_true(self):
        self.generic_test(And(TrueCondition(), TrueCondition()), True, False)

    def test_true_and_false(self):
        self.generic_test(And(TrueCondition(), FalseCondition()), False, True)

    def test_false_and_true(self):
        self.generic_test(And(FalseCondition(), TrueCondition()), False, True)

    def test_false_and_false(self):
        self.generic_test(And(FalseCondition(), FalseCondition()), False, True)

    def test_or(self):
        """
        Tests if a is exited OR b is entered.
        """

        statechart = Statechart('test')
        initial_state = CompoundState('initial_state', initial='Or')
        statechart.add_state(initial_state, None)

        or_state = Or(Enter('b_state'), Exit('a_state'))

        success_state = BasicState('success')
        statechart.add_state(success_state, 'initial_state')

        failure_state = BasicState('failure')
        statechart.add_state(failure_state, 'initial_state')

        or_state.add_to(statechart=statechart, id='Or', parent_id='initial_state',
                        success_state_id='success', failure_state_id='failure')

        interpreter = Interpreter(statechart)

        self.assertFalse('success' in interpreter.configuration)
        self.assertFalse('failure' in interpreter.configuration)

        self.sequential_interpreter.execute()
        trace = self.sequential_interpreter.trace
        story = teststory_from_trace(trace)
        story.tell(interpreter)

        self.assertTrue('success' in interpreter.configuration)
        self.assertFalse('failure' in interpreter.configuration)

    def test_true_or_true(self):
        self.generic_test(Or(TrueCondition(), TrueCondition()), True, False)

    def test_true_or_false(self):
        self.generic_test(Or(TrueCondition(), FalseCondition()), True, False)

    def test_false_or_true(self):
        self.generic_test(Or(FalseCondition(), TrueCondition()), True, False)

    def test_false_or_false(self):
        self.generic_test(Or(FalseCondition(), FalseCondition()), False, True)



