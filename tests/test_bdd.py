import pytest

import os

from sismic.exceptions import StatechartError
from sismic.interpreter import Event
from sismic.bdd import steps, execute_bdd
from sismic.bdd.__main__ import cli
from sismic.io import import_from_yaml


def test_elevator(elevator):
    assert 0 == execute_bdd(
        elevator.statechart,
        [os.path.join('docs', 'examples', 'elevator', 'elevator.feature')]
    )


class TestMicrowave:
    @pytest.fixture
    def property_statecharts(self):
        statecharts = []
        for filename in ['heating_off_property', 'heating_on_property', 'heating_property']:
            with open(os.path.join('docs', 'examples', 'microwave', filename+'.yaml')) as f:
                statecharts.append(import_from_yaml(f))
        return statecharts

    def test_microwave(self, microwave):
        assert 0 == execute_bdd(
            microwave.statechart,
            [os.path.join('docs', 'examples', 'microwave', 'heating.feature')]
        )

    def test_microwave_with_properties(self, microwave, property_statecharts):
        assert 0 == execute_bdd(
            microwave.statechart,
            [os.path.join('docs', 'examples', 'microwave', 'heating.feature')],
            property_statecharts=property_statecharts
        )

    def test_microwave_with_steps(self, microwave):
        features = ['cooking_human', 'lighting_human', 'safety_human']

        assert 0 == execute_bdd(
            microwave.statechart,
            [os.path.join('docs', 'examples', 'microwave', f+'.feature') for f in features],
            step_filepaths=[os.path.join('docs', 'examples', 'microwave', 'steps.py')],
        )

    def test_microwave_with_steps_and_properties(self, microwave, property_statecharts):
        features = ['cooking_human', 'lighting_human', 'safety_human']

        assert 0 == execute_bdd(
            microwave.statechart,
            [os.path.join('docs', 'examples', 'microwave', f+'.feature') for f in features],
            step_filepaths=[os.path.join('docs', 'examples', 'microwave', 'steps.py')],
            property_statecharts=property_statecharts
        )


def test_cli():
    assert 0 == cli([
        'docs/examples/microwave/microwave.yaml',
        '--features', 'docs/examples/microwave/heating.feature', 'docs/examples/microwave/cooking_human.feature', 'docs/examples/microwave/lighting_human.feature', 'docs/examples/microwave/safety_human.feature',
        '--steps', 'docs/examples/microwave/steps.py',
        '--properties', 'docs/examples/microwave/heating_on_property.yaml', 'docs/examples/microwave/heating_off_property.yaml'
    ])


class TestSteps:
    @pytest.fixture
    def context(self, mocker):
        context = mocker.MagicMock(name='context')

        context.interpreter = mocker.MagicMock(name='interpreter')
        context.interpreter.queue = mocker.MagicMock(name='queue')
        context.interpreter.context = {'x': 1}

        def state_for(name):
            if name == 'unknown state':
                raise StatechartError()
            else:
                return mocker.DEFAULT

        context.interpreter.statechart.state_for = mocker.MagicMock(side_effect=state_for)
        context.execute_steps = mocker.MagicMock(name='execute_steps')
        context.monitored_trace = []

        return context

    @pytest.fixture
    def trace(self, mocker):
        macrostep = mocker.MagicMock()
        macrostep.entered_states = ['a', 'b', 'c']
        macrostep.exited_states = ['x', 'y', 'z']
        macrostep.sent_events = [Event('e1'), Event('e2'), Event('e3')]

        return [macrostep]

    def test_do_nothing(self, context):
        steps.do_nothing(context)
        context.interpreter.queue.assert_not_called()

    def test_repeat_step(self, context):
        steps.repeat_step(context, 'blabla', 3)
        assert context.execute_steps.call_count == 3
        context.execute_steps.assert_called_with('Given blabla')

    def test_send_event(self, context):
        steps.send_event(context, 'event_name')
        context.interpreter.queue.assert_called_with('event_name')

    def test_send_event_with_parameter(self, context):
        steps.send_event(context, 'event_name', 'x', '1')
        context.interpreter.queue.assert_called_with('event_name', x=1)

    def test_wait(self, context):
        context.interpreter.clock.time = 0
        steps.wait(context, 3)
        assert context.interpreter.clock.time == 3
        
        steps.wait(context, 6)
        assert context.interpreter.clock.time == 9

    def test_state_is_entered(self, context, trace):
        context.monitored_trace = []
        with pytest.raises(AssertionError):
            steps.state_is_entered(context, 'state')

        context.monitored_trace = trace
        steps.state_is_entered(context, 'a')
        steps.state_is_entered(context, 'b')
        steps.state_is_entered(context, 'c')
        with pytest.raises(AssertionError):
            steps.state_is_entered(context, 'state')
        with pytest.raises(StatechartError):
            steps.state_is_entered(context, 'unknown state')

    def test_state_is_not_entered(self, context, trace):
        context.monitored_trace = []
        steps.state_is_not_entered(context, 'state')

        context.monitored_trace = trace
        with pytest.raises(AssertionError):
            steps.state_is_not_entered(context, 'a')
        steps.state_is_not_entered(context, 'state')
        with pytest.raises(StatechartError):
            steps.state_is_entered(context, 'unknown state')

    def test_state_is_exited(self, context, trace):
        context.monitored_trace = []
        with pytest.raises(AssertionError):
            steps.state_is_exited(context, 'state')

        context.monitored_trace = trace
        steps.state_is_exited(context, 'x')
        steps.state_is_exited(context, 'y')
        steps.state_is_exited(context, 'z')
        with pytest.raises(AssertionError):
            steps.state_is_entered(context, 'state')
        with pytest.raises(StatechartError):
            steps.state_is_entered(context, 'unknown state')

    def test_state_is_not_exited(self, context, trace):
        context.monitored_trace = []
        steps.state_is_not_exited(context, 'state')

        context.monitored_trace = trace
        with pytest.raises(AssertionError):
            steps.state_is_not_exited(context, 'x')
        steps.state_is_not_exited(context, 'state')
        with pytest.raises(StatechartError):
            steps.state_is_entered(context, 'unknown state')

    def test_state_is_active(self, context):
        context.interpreter.configuration = []
        with pytest.raises(AssertionError):
            steps.state_is_active(context, 'state')

        context.interpreter.configuration = ['a', 'b', 'c']
        steps.state_is_active(context, 'a')
        steps.state_is_active(context, 'b')
        steps.state_is_active(context, 'c')
        with pytest.raises(AssertionError):
            steps.state_is_active(context, 'state')
        with pytest.raises(StatechartError):
            steps.state_is_entered(context, 'unknown state')

    def test_state_is_not_active(self, context):
        context.interpreter.configuration = []

        steps.state_is_not_active(context, 'state')

        context.interpreter.configuration = ['a', 'b', 'c']
        with pytest.raises(AssertionError):
            steps.state_is_not_active(context, 'a')

        steps.state_is_not_active(context, 'state')
        with pytest.raises(StatechartError):
            steps.state_is_entered(context, 'unknown state')

    def test_event_is_fired(self, context, trace):
        context.monitored_trace = []
        with pytest.raises(AssertionError):
            steps.event_is_fired(context, 'event')

        context.monitored_trace = trace
        steps.event_is_fired(context, 'e1')
        steps.event_is_fired(context, 'e2')
        steps.event_is_fired(context, 'e3')

        with pytest.raises(AssertionError):
            steps.event_is_fired(context, 'event')

    def test_event_is_fired_with_parameter(self, context, trace):
        context.monitored_trace = trace
        context.monitored_trace[0].sent_events = [Event('e1', x=1)]

        steps.event_is_fired(context, 'e1')

        with pytest.raises(AssertionError):
            steps.event_is_fired(context, 'event')

        with pytest.raises(AssertionError):
            steps.event_is_fired(context, 'e1', 'x', '2')

        steps.event_is_fired(context, 'e1', 'x', '1')

    def test_event_is_not_fired(self, context, trace):
        context.monitored_trace = []

        steps.event_is_not_fired(context, 'event')

        context.monitored_trace = trace
        with pytest.raises(AssertionError):
            steps.event_is_not_fired(context, 'e1')

        steps.event_is_not_fired(context, 'event')

    def test_no_event_is_fired(self, context, trace):
        context.monitored_trace = []
        steps.no_event_is_fired(context)

        context.monitored_trace = trace
        with pytest.raises(AssertionError):
            steps.no_event_is_fired(context)

    def test_variable_equals(self, context):
        steps.variable_equals(context, 'x', '1')

        with pytest.raises(AssertionError):
            steps.variable_equals(context, 'y', '1')

        with pytest.raises(AssertionError):
            steps.variable_equals(context, 'x', '2')

    def test_variable_does_not_equal(self, context):
        steps.variable_does_not_equal(context, 'x', '2')

        with pytest.raises(AssertionError):
            steps.variable_does_not_equal(context, 'x', '1')

        with pytest.raises(AssertionError):
            steps.variable_does_not_equal(context, 'y', '1')

    def test_final_configuration(self, context):
        context.interpreter.final = True
        steps.final_configuration(context)

        context.interpreter.final = False
        with pytest.raises(AssertionError):
            steps.final_configuration(context)

    def test_not_final_configuration(self, context):
        context.interpreter.final = False
        steps.not_final_configuration(context)

        context.interpreter.final = True
        with pytest.raises(AssertionError):
            steps.not_final_configuration(context)
