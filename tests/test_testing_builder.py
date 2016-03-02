import unittest

from sismic.interpreter import Interpreter
from sismic.model import Event
from sismic.stories import Story
from sismic.testing import teststory_from_trace
from sismic.testing.builder import *


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

        property.add_to_statechart(tester_statechart,
                                   condition_state='property',
                                   parent_state='testing_area',
                                   status_state='parallel_state',
                                   success_state='success_state',
                                   failure_state='failure_state')

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

    def test_condition_success(self):
        for (event, condition) in [
            ('event', EnterState('b_state')),
            ('event', EnterState('foo', 'b_state', 'bar')),
            ('event', EnterAnyState()),
            ('event', ExitState('a_state')),
            ('event', ExitState('foo', 'a_state', 'bar')),
            ('event', ExitAnyState()),
            ('foo', ConsumeEvent('foo')),
            ('foo', ConsumeEvent('foo', 'bar')),
            ('foo', ConsumeAnyEvent()),
            ('foo', ConsumeAnyEventBut('bar')),
            ('foo', ConsumeAnyEventBut('bar', 'baz')),
            ('foo', StartExecution()),
            ('foo', StopExecution()),
            ('foo', StartStep()),
            ('foo', StopExecution()),
            ('event', TransitionProcess()),
            ('event', TransitionProcess(event='event')),
            ('event', TransitionProcess(source='a_state')),
            ('event', TransitionProcess(target='b_state')),
            ('event', Before(EnterState('a_state'), EnterState('b_state'))),
            ('event', Before(EnterState('a_state'), FalseCondition())),
            ('event', Before(EnterState('a_state'), UndeterminedCondition())),
            ('event', Before(EnterState('b_state'), FalseCondition())),
            ('event', Before(EnterState('b_state'), UndeterminedCondition()))
        ]:
            with self.subTest(condition=condition):
                self.generic_test(self.sequential_statechart, [Event(event)], condition, True, False)

    def test_condition_failure(self):
        for (event, condition) in [
            ('event', Before(EnterState('b_state'), EnterState('a_state'))),
        ]:
            with self.subTest(condition=condition):
                self.generic_test(self.sequential_statechart, [Event(event)], condition, False, True)

    def test_condition_undetermined(self):
        for (event, condition) in [
            ('event', EnterState('foo')),
            ('event', ExitState('b_state')),
            ('foo', ExitAnyState()),
            ('bar', ConsumeEvent('foo')),
            ('foo', TransitionProcess()),
            ('event', TransitionProcess(event='foo')),
            ('event', TransitionProcess(source='foo')),
            ('event', TransitionProcess(target='foo')),
            ('event', TransitionProcess(event='')),

        ]:
            with self.subTest(condition=condition):
                self.generic_test(self.sequential_statechart, [Event(event)], condition, False, False)

    def test_check_guard_success(self):
        statechart = Statechart('statechart')
        statechart.add_state(OrthogonalState('parallel_state'), parent=None)

        initial_state = CompoundState('initial_state', initial='condition')
        statechart.add_state(initial_state, parent='parallel_state')

        statechart.add_state(BasicState('success'), parent='initial_state')
        statechart.add_state(BasicState('failure'), parent='initial_state')

        CheckGuard('x == 1').add_to_statechart(statechart=statechart,
                                               condition_state='condition',
                                               parent_state='initial_state',
                                               status_state='parallel_state',
                                               success_state='success',
                                               failure_state='failure')

        interpreter = Interpreter(statechart)
        interpreter.context['x'] = 1

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

        CheckGuard('x == 1').add_to_statechart(statechart=statechart,
                                               condition_state='condition',
                                               parent_state='initial_state',
                                               status_state='parallel_state',
                                               success_state='success',
                                               failure_state='failure')

        interpreter = Interpreter(statechart)
        interpreter.context['x'] = 42

        interpreter.execute()
        self.assertFalse('success' in interpreter.configuration)
        self.assertTrue('failure' in interpreter.configuration)

    def test_consume_any_event_but_wrong(self):
        self.generic_test(self.sequential_statechart, [], ConsumeAnyEventBut('foo'), False, False)

    def test_transition_process_right_eventless(self):
        self.sequential_statechart.remove_transition(Transition(source='a_state', target='b_state', event='event'))
        self.sequential_statechart.add_transition(Transition(source='a_state', target='b_state'))

        self.generic_test(self.sequential_statechart,
                          [Event('event')],
                          TransitionProcess(event=''),
                          True,
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


class OperatorsTest(unittest.TestCase):
    def generic_test(self, condition: Condition, success_expected: bool, failure_expected: bool, delay: int = 0):
        statechart = Statechart('test')
        parallel_state = OrthogonalState('parallel_state')
        statechart.add_state(parallel_state, parent=None)

        initial_state = CompoundState('initial_state', initial='Cond')
        statechart.add_state(initial_state, "parallel_state")

        statechart.add_state(BasicState('success'), 'initial_state')
        statechart.add_state(BasicState('failure'), 'initial_state')

        condition.add_to_statechart(statechart=statechart,
                                    condition_state='Cond',
                                    parent_state='initial_state',
                                    status_state='parallel_state',
                                    success_state='success',
                                    failure_state='failure')

        interpreter = Interpreter(statechart)

        self.assertFalse('success' in interpreter.configuration)
        self.assertFalse('failure' in interpreter.configuration)

        interpreter.execute()

        interpreter.time += delay
        interpreter.queue(Event(Condition.STEP_ENDED_EVENT))
        interpreter.queue(Event(Condition.STEP_ENDED_EVENT))
        interpreter.execute()

        self.assertEqual(success_expected, 'success' in interpreter.configuration)
        self.assertEqual(failure_expected, 'failure' in interpreter.configuration)

    def test_operator_success(self):
        for condition in [
            And(TrueCondition(), TrueCondition()),
            Or(TrueCondition(), TrueCondition()),
            Or(TrueCondition(), FalseCondition()),
            Or(FalseCondition(), TrueCondition()),
            Or(TrueCondition(), UndeterminedCondition()),
            Or(UndeterminedCondition(), TrueCondition()),
            Not(FalseCondition()),
            Then(TrueCondition(), TrueCondition()),
            Xor(TrueCondition(), FalseCondition()),
            Xor(FalseCondition(), TrueCondition()),
            Before(TrueCondition(), FalseCondition()),
            Before(TrueCondition(), UndeterminedCondition()),
            During(TrueCondition(), 0, 10),
            IfElse(TrueCondition(), TrueCondition(), TrueCondition()),
            IfElse(TrueCondition(), TrueCondition(), FalseCondition()),
            IfElse(TrueCondition(), TrueCondition(), UndeterminedCondition()),
            IfElse(FalseCondition(), TrueCondition(), TrueCondition()),
            IfElse(FalseCondition(), FalseCondition(), TrueCondition())
        ]:
            with self.subTest(condition=condition):
                self.generic_test(condition, True, False)

    def test_operator_failure(self):
        for condition in [
            And(TrueCondition(), FalseCondition()),
            And(FalseCondition(), TrueCondition()),
            And(FalseCondition(), FalseCondition()),
            And(FalseCondition(), UndeterminedCondition()),
            And(UndeterminedCondition(), FalseCondition()),
            Or(FalseCondition(), FalseCondition()),
            Not(TrueCondition()),
            Then(TrueCondition(), FalseCondition()),
            Then(FalseCondition(), FalseCondition()),
            Then(FalseCondition(), TrueCondition()),
            Then(FalseCondition(), UndeterminedCondition()),
            Xor(TrueCondition(), TrueCondition()),
            Xor(FalseCondition(), FalseCondition()),
            Before(FalseCondition(), TrueCondition()),
            Before(FalseCondition(), FalseCondition()),
            Before(UndeterminedCondition(), TrueCondition()),
            Before(FalseCondition(), UndeterminedCondition()),
            During(TrueCondition(), 5, 10),
            During(FalseCondition(), 0, 10),
            During(FalseCondition(), 5, 10),
            IfElse(TrueCondition(), FalseCondition(), TrueCondition()),
            IfElse(TrueCondition(), FalseCondition(), FalseCondition()),
            IfElse(TrueCondition(), FalseCondition(), UndeterminedCondition()),
            IfElse(FalseCondition(), TrueCondition(), FalseCondition()),
            IfElse(FalseCondition(), FalseCondition(), FalseCondition()),
            IfElse(UndeterminedCondition(), FalseCondition(), FalseCondition())  # fail-fast
        ]:
            with self.subTest(condition=condition):
                self.generic_test(condition, False, True)

    def test_operator_undetermined(self):
        for condition in [
            And(TrueCondition(), UndeterminedCondition()),
            And(UndeterminedCondition(), TrueCondition()),
            And(UndeterminedCondition(), UndeterminedCondition()),
            Or(FalseCondition(), UndeterminedCondition()),
            Or(UndeterminedCondition(), FalseCondition()),
            Or(UndeterminedCondition(), UndeterminedCondition()),
            Not(UndeterminedCondition()),
            Then(TrueCondition(), UndeterminedCondition()),
            Then(UndeterminedCondition(), TrueCondition()),
            Then(UndeterminedCondition(), FalseCondition()),
            Then(UndeterminedCondition(), UndeterminedCondition()),
            Xor(TrueCondition(), UndeterminedCondition()),
            Xor(FalseCondition(), UndeterminedCondition()),
            Xor(UndeterminedCondition(), TrueCondition()),
            Xor(UndeterminedCondition(), FalseCondition()),
            Xor(UndeterminedCondition(), UndeterminedCondition()),
            Before(UndeterminedCondition(), FalseCondition()),
            Before(UndeterminedCondition(), UndeterminedCondition()),
            During(UndeterminedCondition(), 0, 10),
            During(UndeterminedCondition(), 5, 10),
            IfElse(TrueCondition(), UndeterminedCondition(), TrueCondition()),
            IfElse(TrueCondition(), UndeterminedCondition(), FalseCondition()),
            IfElse(TrueCondition(), UndeterminedCondition(), UndeterminedCondition()),
            IfElse(FalseCondition(), TrueCondition(), UndeterminedCondition()),
            IfElse(FalseCondition(), FalseCondition(), UndeterminedCondition()),
            IfElse(UndeterminedCondition(), TrueCondition(), TrueCondition()),
            IfElse(UndeterminedCondition(), TrueCondition(), FalseCondition()),
            IfElse(UndeterminedCondition(), TrueCondition(), UndeterminedCondition()),
            IfElse(UndeterminedCondition(), FalseCondition(), TrueCondition()),
            IfElse(UndeterminedCondition(), TrueCondition(), UndeterminedCondition()),
            IfElse(UndeterminedCondition(), UndeterminedCondition(), TrueCondition()),
            IfElse(UndeterminedCondition(), UndeterminedCondition(), FalseCondition()),
            IfElse(UndeterminedCondition(), UndeterminedCondition(), UndeterminedCondition())
        ]:
            with self.subTest(condition=condition):
                self.generic_test(condition, False, False)

    def test_during_delayed_true_instant(self):
        self.generic_test(During(DelayedTrueCondition(2), 0, 10), True, False, 3)

    def test_during_delayed_true_delay(self):
        self.generic_test(During(DelayedTrueCondition(7), 5, 10), True, False, 10)

    def test_during_delayed_false_instant(self):
        self.generic_test(During(DelayedFalseCondition(2), 0, 10), False, True, 3)

    def test_during_delayed_false_delay(self):
        self.generic_test(During(DelayedFalseCondition(7), 5, 10), False, True, 10)

    def test_delayed_true(self):
        self.generic_test(DelayedTrueCondition(2), False, False, 0)
        self.generic_test(DelayedTrueCondition(2), True, False, 5)

    def test_delayed_false(self):
        self.generic_test(DelayedFalseCondition(2), False, False, 0)
        self.generic_test(DelayedFalseCondition(2), False, True, 5)


class ConditionOperatorTests(unittest.TestCase):
    def test_generic(self):
        for a, b in [
            ((~ TrueCondition()), Not(TrueCondition())),
            ((TrueCondition() & FalseCondition()), And(TrueCondition(), FalseCondition())),
            ((TrueCondition() | FalseCondition()), Or(TrueCondition(), FalseCondition())),
            ((TrueCondition() ^ FalseCondition()), Xor(TrueCondition(), FalseCondition())),
            ((TrueCondition().then(FalseCondition())), Then(TrueCondition(), FalseCondition()))
        ]:
            with self.subTest(a=a, b=b):
                self.assertEqual(a.__repr__(), b.__repr__())


class ReprTest(unittest.TestCase):
    def test_operators(self):
        for condition in [
            'TrueCondition()',
            'FalseCondition()',
            'UndeterminedCondition()',
            'And(TrueCondition(), FalseCondition())',
            'Or(TrueCondition(), FalseCondition())',
            'Not(TrueCondition())',
            'Xor(TrueCondition(), FalseCondition())',
            'Before(TrueCondition(), FalseCondition())',
            'Then(TrueCondition(), FalseCondition())',
            'During(TrueCondition(), 10, 42)',
            'DelayedTrueCondition(42)',
            'DelayedFalseCondition(42)',
            'IfElse(TrueCondition(), TrueCondition(), FalseCondition())',
            'DelayedCondition(TrueCondition(), 42)',
            'SynchronousCondition(TrueCondition())'
        ]:
            with self.subTest(condition=condition):
                instance = eval(condition)
                self.assertEqual(condition, instance.__repr__())

    def test_properties(self):
        for condition in [
            "EnterState('foo')",
            "EnterState('foo', 'bar')",
            'EnterAnyState()',
            "ExitState('foo')",
            "ExitState('foo', 'bar')",
            'ExitAnyState()',
            'CheckGuard("foo")',
            "ConsumeEvent('foo')",
            "ConsumeEvent('foo', 'bar')",
            'ConsumeAnyEvent()',
            "ConsumeAnyEventBut('foo')",
            "ConsumeAnyEventBut('foo', 'bar')",
            'StartExecution()',
            'StopExecution()',
            'StartStep()',
            'EndStep()',
            'TransitionProcess()',
            'TransitionProcess(source="foo")',
            'TransitionProcess(target="foo")',
            'TransitionProcess(event="foo")',
            'InactiveState("foo")',
            'ActiveState("foo")'
        ]:
            with self.subTest(condition=condition):
                instance = eval(condition)
                self.assertEqual(condition, instance.__repr__())

    def test_temporal_expression(self):
        for expected, condition in [
            ('FirstTime(True, TrueCondition(), FalseCondition())', FirstTime(True, TrueCondition(), FalseCondition())),
            ('LastTime(True, TrueCondition(), FalseCondition())', LastTime(True, TrueCondition(), FalseCondition())),
            ('EveryTime(True, TrueCondition(), FalseCondition())', EveryTime(True, TrueCondition(), FalseCondition())),
            ('AtLeastOnce(True, TrueCondition(), FalseCondition())', AtLeastOnce(True, TrueCondition(), FalseCondition())),
        ]:
            with self.subTest(expected=expected, condition=condition):
                self.assertEqual(expected, condition.__repr__())


class TemporalTests(unittest.TestCase):
    def setUp(self):
        self.story = [Event(Condition.STEP_ENDED_EVENT), Event(Condition.STEP_ENDED_EVENT), Event('execution stopped')]

    def generic_temporal_test(self, expression: TemporalExpression, story: list, accept_after: bool):
        statechart = expression.generate_statechart()
        interpreter = Interpreter(statechart)

        Story(story).tell(interpreter)
        interpreter.execute()

        self.assertEqual(len(interpreter.configuration) == 0, accept_after)

    def test_temporal_success(self):
        for condition in [
            FirstTime(True, TrueCondition(), TrueCondition()),
            FirstTime(True, FalseCondition(), TrueCondition()),
            FirstTime(True, FalseCondition(), FalseCondition()),
            FirstTime(True, FalseCondition(), UndeterminedCondition()),
            FirstTime(True, UndeterminedCondition(), TrueCondition()),
            FirstTime(True, UndeterminedCondition(), FalseCondition()),
            FirstTime(True, UndeterminedCondition(), UndeterminedCondition()),
            FirstTime(False, TrueCondition(), FalseCondition()),
            FirstTime(False, TrueCondition(), UndeterminedCondition()),
            LastTime(True, TrueCondition(), TrueCondition()),
            LastTime(True, FalseCondition(), TrueCondition()),
            LastTime(True, FalseCondition(), FalseCondition()),
            LastTime(True, UndeterminedCondition(), TrueCondition()),
            LastTime(True, FalseCondition(), UndeterminedCondition()),
            LastTime(True, UndeterminedCondition(), FalseCondition()),
            LastTime(True, UndeterminedCondition(), UndeterminedCondition()),
            LastTime(False, TrueCondition(), FalseCondition()),
            LastTime(False, TrueCondition(), UndeterminedCondition()),
            EveryTime(True, TrueCondition(), TrueCondition()),
            EveryTime(True, FalseCondition(), TrueCondition()),
            EveryTime(True, FalseCondition(), FalseCondition()),
            EveryTime(True, FalseCondition(), UndeterminedCondition()),
            EveryTime(True, UndeterminedCondition(), FalseCondition()),
            EveryTime(True, UndeterminedCondition(), TrueCondition()),
            EveryTime(True, UndeterminedCondition(), UndeterminedCondition()),
            EveryTime(False, TrueCondition(), FalseCondition()),
            EveryTime(False, TrueCondition(), UndeterminedCondition()),
            AtLeastOnce(True, TrueCondition(), TrueCondition()),
            AtLeastOnce(True, FalseCondition(), TrueCondition()),
            AtLeastOnce(True, FalseCondition(), FalseCondition()),
            AtLeastOnce(True, UndeterminedCondition(), TrueCondition()),
            AtLeastOnce(True, FalseCondition(), UndeterminedCondition()),
            AtLeastOnce(True, UndeterminedCondition(), FalseCondition()),
            AtLeastOnce(True, UndeterminedCondition(), UndeterminedCondition()),
            AtLeastOnce(False, TrueCondition(), FalseCondition()),
            AtLeastOnce(False, TrueCondition(), UndeterminedCondition()),

        ]:
            with self.subTest(condition=condition):
                self.generic_temporal_test(condition, self.story, True)

    def test_temporal_failure(self):
        for condition in [
            FirstTime(True, TrueCondition(), FalseCondition()),
            FirstTime(True, TrueCondition(), UndeterminedCondition()),
            FirstTime(False, TrueCondition(), TrueCondition()),
            FirstTime(False, FalseCondition(), TrueCondition()),
            FirstTime(False, FalseCondition(), FalseCondition()),
            FirstTime(False, FalseCondition(), UndeterminedCondition()),
            FirstTime(False, UndeterminedCondition(), TrueCondition()),
            FirstTime(False, UndeterminedCondition(), FalseCondition()),
            FirstTime(False, UndeterminedCondition(), UndeterminedCondition()),
            LastTime(True, TrueCondition(), FalseCondition()),
            LastTime(True, TrueCondition(), UndeterminedCondition()),
            LastTime(False, TrueCondition(), TrueCondition()),
            LastTime(False, FalseCondition(), TrueCondition()),
            LastTime(False, FalseCondition(), FalseCondition()),
            LastTime(False, FalseCondition(), UndeterminedCondition()),
            LastTime(False, UndeterminedCondition(), TrueCondition()),
            LastTime(False, UndeterminedCondition(), FalseCondition()),
            LastTime(False, UndeterminedCondition(), UndeterminedCondition()),
            EveryTime(True, TrueCondition(), FalseCondition()),
            EveryTime(True, TrueCondition(), UndeterminedCondition()),
            EveryTime(False, TrueCondition(), TrueCondition()),
            EveryTime(False, FalseCondition(), TrueCondition()),
            EveryTime(False, FalseCondition(), FalseCondition()),
            EveryTime(False, FalseCondition(), UndeterminedCondition()),
            EveryTime(False, UndeterminedCondition(), TrueCondition()),
            EveryTime(False, UndeterminedCondition(), FalseCondition()),
            EveryTime(False, UndeterminedCondition(), UndeterminedCondition()),
            AtLeastOnce(True, TrueCondition(), FalseCondition()),
            AtLeastOnce(True, TrueCondition(), UndeterminedCondition()),
            AtLeastOnce(False, TrueCondition(), TrueCondition()),
            AtLeastOnce(False, FalseCondition(), TrueCondition()),
            AtLeastOnce(False, FalseCondition(), FalseCondition()),
            AtLeastOnce(False, FalseCondition(), UndeterminedCondition()),
            AtLeastOnce(False, UndeterminedCondition(), TrueCondition()),
            AtLeastOnce(False, UndeterminedCondition(), FalseCondition()),
            AtLeastOnce(False, UndeterminedCondition(), UndeterminedCondition())
        ]:
            with self.subTest(condition=condition):
                self.generic_temporal_test(condition, self.story, False)
