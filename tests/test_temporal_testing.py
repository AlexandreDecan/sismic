import unittest
from sismic.temporal_testing import Enter, Exit, And, Or, FalseCondition, TrueCondition
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

    def test_enter(self):
        test_statechart = Statechart('test')
        test_initial_state = CompoundState('initial_state', initial='Enter')
        enter_state = Enter('b_state')
        out_state = BasicState('out')
        test_statechart.add_state(test_initial_state, None)
        test_statechart.add_state(out_state, 'initial_state')
        enter_state.add_to(test_statechart, 'Enter', 'initial_state', 'out')
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
        enter_state.add_to(test_statechart, 'Enter', 'initial_state', 'out')
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
        out_state = BasicState('out')
        statechart.add_state(initial_state, None)
        statechart.add_state(out_state, 'initial_state')
        and_state.add_to(statechart=statechart, id='And', parent_id='initial_state', success_state_id='out')
        interpreter = Interpreter(statechart)

        self.assertFalse('out' in interpreter.configuration)

        self.sequential_interpreter.execute()
        trace = self.sequential_interpreter.trace
        story = teststory_from_trace(trace)
        story.tell(interpreter)

        self.assertTrue('out' in interpreter.configuration)

    def test_and_with_false(self):
        """
        Tests if (a is exited AND False) is not satisfied .
        """

        statechart = Statechart('test')
        initial_state = CompoundState('initial_state', initial='And')
        and_state = And(Enter('b_state'), FalseCondition())
        out_state = BasicState('out')
        statechart.add_state(initial_state, None)
        statechart.add_state(out_state, 'initial_state')
        and_state.add_to(statechart=statechart, id='And', parent_id='initial_state', success_state_id='out')
        interpreter = Interpreter(statechart)

        self.assertFalse('out' in interpreter.configuration)

        self.sequential_interpreter.execute()
        trace = self.sequential_interpreter.trace
        story = teststory_from_trace(trace)
        story.tell(interpreter)

        self.assertFalse('out' in interpreter.configuration)

    def test_true_and_true(self):
        """
        Tests if (a is exited AND False) is not satisfied .
        """

        statechart = Statechart('test')
        initial_state = CompoundState('initial_state', initial='And')
        and_state = And(TrueCondition(), TrueCondition())
        out_state = BasicState('out')
        statechart.add_state(initial_state, None)
        statechart.add_state(out_state, 'initial_state')
        and_state.add_to(statechart=statechart, id='And', parent_id='initial_state', success_state_id='out')
        interpreter = Interpreter(statechart)

        self.assertFalse('out' in interpreter.configuration)

        self.sequential_interpreter.execute()
        trace = self.sequential_interpreter.trace
        story = teststory_from_trace(trace)
        story.tell(interpreter)

        self.assertTrue('out' in interpreter.configuration)

    def test_true_and_false(self):
        """
        Tests if (a is exited AND False) is not satisfied .
        """

        statechart = Statechart('test')
        initial_state = CompoundState('initial_state', initial='And')
        and_state = And(TrueCondition(), FalseCondition())
        out_state = BasicState('out')
        statechart.add_state(initial_state, None)
        statechart.add_state(out_state, 'initial_state')
        and_state.add_to(statechart=statechart, id='And', parent_id='initial_state', success_state_id='out')
        interpreter = Interpreter(statechart)

        self.assertFalse('out' in interpreter.configuration)

        self.sequential_interpreter.execute()
        trace = self.sequential_interpreter.trace
        story = teststory_from_trace(trace)
        story.tell(interpreter)

        self.assertFalse('out' in interpreter.configuration)

    def test_false_and_true(self):
        """
        Tests if (a is exited AND False) is not satisfied .
        """

        statechart = Statechart('test')
        initial_state = CompoundState('initial_state', initial='And')
        and_state = And(FalseCondition(), TrueCondition())
        out_state = BasicState('out')
        statechart.add_state(initial_state, None)
        statechart.add_state(out_state, 'initial_state')
        and_state.add_to(statechart=statechart, id='And', parent_id='initial_state', success_state_id='out')
        interpreter = Interpreter(statechart)

        self.assertFalse('out' in interpreter.configuration)

        self.sequential_interpreter.execute()
        trace = self.sequential_interpreter.trace
        story = teststory_from_trace(trace)
        story.tell(interpreter)

        self.assertFalse('out' in interpreter.configuration)

    def test_false_and_false(self):
        """
        Tests if (a is exited AND False) is not satisfied .
        """

        statechart = Statechart('test')
        initial_state = CompoundState('initial_state', initial='And')
        and_state = And(FalseCondition(), FalseCondition())
        out_state = BasicState('out')
        statechart.add_state(initial_state, None)
        statechart.add_state(out_state, 'initial_state')
        and_state.add_to(statechart=statechart, id='And', parent_id='initial_state', success_state_id='out')
        interpreter = Interpreter(statechart)

        self.assertFalse('out' in interpreter.configuration)

        self.sequential_interpreter.execute()
        trace = self.sequential_interpreter.trace
        story = teststory_from_trace(trace)
        story.tell(interpreter)

        self.assertFalse('out' in interpreter.configuration)

    def test_or(self):
        """
        Tests if a is exited OR b is entered.
        """

        statechart = Statechart('test')
        initial_state = CompoundState('initial_state', initial='And')
        and_state = Or(Enter('b_state'), Exit('a_state'))
        out_state = BasicState('out')
        statechart.add_state(initial_state, None)
        statechart.add_state(out_state, 'initial_state')
        and_state.add_to(statechart=statechart, id='And', parent_id='initial_state', success_state_id='out')
        interpreter = Interpreter(statechart)

        self.assertFalse('out' in interpreter.configuration)

        self.sequential_interpreter.execute()
        trace = self.sequential_interpreter.trace
        story = teststory_from_trace(trace)
        story.tell(interpreter)

        self.assertTrue('out' in interpreter.configuration)

    def test_true_or_true(self):
        statechart = Statechart('test')
        initial_state = CompoundState('initial_state', initial='And')
        and_state = Or(TrueCondition(), TrueCondition())
        out_state = BasicState('out')
        statechart.add_state(initial_state, None)
        statechart.add_state(out_state, 'initial_state')
        and_state.add_to(statechart=statechart, id='And', parent_id='initial_state', success_state_id='out')
        interpreter = Interpreter(statechart)

        self.assertFalse('out' in interpreter.configuration)

        self.sequential_interpreter.execute()
        trace = self.sequential_interpreter.trace
        story = teststory_from_trace(trace)
        story.tell(interpreter)

        self.assertTrue('out' in interpreter.configuration)

    def test_true_or_false(self):
        statechart = Statechart('test')
        initial_state = CompoundState('initial_state', initial='And')
        and_state = Or(TrueCondition(), FalseCondition())
        out_state = BasicState('out')
        statechart.add_state(initial_state, None)
        statechart.add_state(out_state, 'initial_state')
        and_state.add_to(statechart=statechart, id='And', parent_id='initial_state', success_state_id='out')
        interpreter = Interpreter(statechart)

        self.assertFalse('out' in interpreter.configuration)

        self.sequential_interpreter.execute()
        trace = self.sequential_interpreter.trace
        story = teststory_from_trace(trace)
        story.tell(interpreter)

        self.assertTrue('out' in interpreter.configuration)

    def test_false_or_true(self):
        statechart = Statechart('test')
        initial_state = CompoundState('initial_state', initial='And')
        and_state = Or(FalseCondition(), TrueCondition())
        out_state = BasicState('out')
        statechart.add_state(initial_state, None)
        statechart.add_state(out_state, 'initial_state')
        and_state.add_to(statechart=statechart, id='And', parent_id='initial_state', success_state_id='out')
        interpreter = Interpreter(statechart)

        self.assertFalse('out' in interpreter.configuration)

        self.sequential_interpreter.execute()
        trace = self.sequential_interpreter.trace
        story = teststory_from_trace(trace)
        story.tell(interpreter)

        self.assertTrue('out' in interpreter.configuration)

    def test_false_or_false(self):
        statechart = Statechart('test')
        initial_state = CompoundState('initial_state', initial='And')
        and_state = Or(FalseCondition(), FalseCondition())
        out_state = BasicState('out')
        statechart.add_state(initial_state, None)
        statechart.add_state(out_state, 'initial_state')
        and_state.add_to(statechart=statechart, id='And', parent_id='initial_state', success_state_id='out')
        interpreter = Interpreter(statechart)

        self.assertFalse('out' in interpreter.configuration)

        self.sequential_interpreter.execute()
        trace = self.sequential_interpreter.trace
        story = teststory_from_trace(trace)
        story.tell(interpreter)

        self.assertFalse('out' in interpreter.configuration)



