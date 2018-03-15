from behave import given, when, then  # type: ignore
from typing import Union, List

from ..interpreter import Event

__all__ = ['action_alias', 'assertion_alias']


def action_alias(step: str, step_to_execute: Union[str, List]) -> None:
    """
    Create an alias of a predefined "given"/"when" step. For example:
    action_alias('I open door', 'I send event open_door')

    Parameters are propagated to the original step as well. For example:
    action_alias('Event {name} has to be sent', 'I send event {name}')

    You can provide more than on "step_to_execute" if you want to alias several steps by a single one.

    :param step: New step, without the "given" or "when" keyword.
    :param step_to_execute: existing step, without the "given" or "when" keyword. Could be a list of steps.
    """
    step_to_execute = step_to_execute if isinstance(step_to_execute, str) else '\nand '.join(step_to_execute)

    @given(step)
    def _(context, **kwargs):
        context.execute_steps('Given ' + step_to_execute.format(**kwargs))

    @when(step)
    def _(context, **kwargs):
        context.execute_steps('When ' + step_to_execute.format(**kwargs))


def assertion_alias(step: str, step_to_execute: Union[str, List]) -> None:
    """
    Create an alias of a predefined "then" step. For example:
    assertion_alias('door is open', 'state door open is active')

    Parameters are propagated to the original step as well. For example:
    assertion_alias('{x} seconds elapsed', 'I wait for {x} seconds')

    You can provide more than on "step_to_execute" if you want to alias several steps by a single one.

    :param step: New step, without the "then" keyword
    :param step_to_execute: existing step, without "then" keyword. Could be a list of steps.
    """
    step_to_execute = step_to_execute if isinstance(step_to_execute, str) else '\nand '.join(step_to_execute)

    @then(step)
    def _(context, **kwargs):
        context.execute_steps('Then ' + step_to_execute.format(**kwargs))


@given('I do nothing')
@when('I do nothing')
def do_nothing(context):
    pass


@given('I reproduce "{scenario}"')
def reproduce_scenario(context, scenario, *, keyword='Given'):
    current_feature = context.feature
    for included_scenario in current_feature.scenarios:
        if included_scenario.name == scenario:
            for step in included_scenario.steps:
                if step.step_type in ['given', 'when']:
                    context.execute_steps('{} {}'.format(keyword, step.name))
            return
    assert False, 'Unknown scenario {}.'.format(scenario)


@when('I reproduce "{scenario}"')
def _reproduce_scenario(context, scenario):
    return reproduce_scenario(context, scenario, keyword='When')


@given('I repeat "{step}" {repeat:d} times')
def repeat_step(context, step, repeat, *, keyword='Given'):
    for _ in range(repeat):
        context.execute_steps('{} {}'.format(keyword, step))


@when('I repeat "{step}" {repeat:d} times')
def _repeat_step(context, step, repeat):
    return repeat_step(context, step, repeat, keyword='When')


@given('I send event {name}')
@given('I send event {name} with {parameter}={value}')
@when('I send event {name}')
@when('I send event {name} with {parameter}={value}')
def send_event(context, name, parameter=None, value=None):
    parameters = {}
    if context.table:
        for row in context.table:
            parameters[row['parameter']] = eval(row['value'], {}, {})

    if parameter and value:
        parameters[parameter] = eval(value)

    event = Event(name, **parameters)
    context.interpreter.queue(event)


@given('I wait {seconds:g} seconds')
@given('I wait {seconds:g} second')
@when('I wait {seconds:g} seconds')
@when('I wait {seconds:g} second')
def wait(context, seconds):
    context.interpreter.time += seconds


@then('state {name} is entered')
def state_is_entered(context, name):
    for macrostep in context.monitored_trace:
        if name in macrostep.entered_states:
            return
    assert False, 'State {} is not entered'.format(name)


@then('state {name} is not entered')
def state_is_entered(context, name):
    for macrostep in context.monitored_trace:
        if name in macrostep.entered_states:
            assert False, 'State {} is entered'.format(name)


@then('state {name} is exited')
def state_is_exited(context, name):
    for macrostep in context.monitored_trace:
        if name in macrostep.exited_states:
            return
    assert False, 'State {} is not exited'.format(name)


@then('state {name} is not exited')
def state_is_exited(context, name):
    for macrostep in context.monitored_trace:
        if name in macrostep.exited_states:
            assert False, 'State {} is exited'.format(name)


@then('state {name} is active')
def state_is_active(context, name):
    assert name in context.interpreter.configuration, 'State {} is not active'.format(name)


@then('state {name} is not active')
def state_is_not_active(context, name):
    assert name not in context.interpreter.configuration, 'State {} is active'.format(name)


@then('event {name} is fired')
@then('event {name} is fired with {parameter}={value}')
def event_is_fired(context, name, parameter=None, value=None):
    parameters = {}

    for row in context.table if context.table else []:
        parameters[row['parameter']] = eval(row['value'], {}, {})

    if parameter and value:
        parameters[parameter] = eval(value)

    for macrostep in context.monitored_trace:
        for event in macrostep.sent_events:
            if event.name == name:
                matching_parameters = True
                for key, value in parameters.items():
                    if getattr(event, key, None) != value:
                        matching_parameters = False
                        break
                if matching_parameters:
                    return
    if len(parameters) == 0:
        assert False, 'Event {} is not fired'.format(name)
    else:
        assert False, 'Event {} is not fired with parameters {}'.format(name, parameters)


@then('event {name} is not fired')
def event_is_not_fired(context, name):
    for macrostep in context.monitored_trace:
        for event in macrostep.sent_events:
            assert event.name != name, 'Event {} is fired'.format(name)


@then('no event is fired')
def no_event_is_fired(context):
    for macrostep in context.monitored_trace:
        if len(macrostep.sent_events) > 0:
            if len(macrostep.sent_events) > 1:
                assert False, 'Events {} are fired'.format(', '.join([e.name for e in macrostep.sent_events]))
            else:
                assert False, 'Event {} is fired'.format(macrostep.sent_events[0].name)


@then('variable {variable} equals {value}')
def variable_equals(context, variable, value):
    assert variable in context.interpreter.context, 'Variable {} is not defined'.format(variable)

    current_value = context.interpreter.context[variable]
    expected_value = eval(value, {}, {})
    assert current_value == expected_value, 'Variable {} equals {}, not {}'.format(variable, current_value, expected_value)


@then('variable {variable} does not equal {value}')
def variable_does_not_equal(context, variable, value):
    assert variable in context.interpreter.context, 'Variable {} is not defined'.format(variable)

    current_value = context.interpreter.context[variable]
    expected_value = eval(value, {}, {})
    assert current_value != expected_value, 'Variable {} equals {}'.format(variable, current_value)


@then('expression {expression} holds')
def expression_holds(context, expression):
    assert context.interpreter._evaluator._evaluate_code(expression), 'Expression {} does not hold'.format(expression)


@then('expression {expression} does not hold')
def expression_does_not_hold(context, expression):
    assert not context.interpreter._evaluator._evaluate_code(expression), 'Expression {} holds'.format(expression)


@then('statechart is in a final configuration')
def final_configuration(context):
    assert context.interpreter.final, 'Statechart is not in a final configuration: {}'.format(', '.join(context.interpreter.configuration))


@then('statechart is not in a final configuration')
def final_configuration(context):
    assert not context.interpreter.final, 'Statechart is in a final configuration: {}'.format(', '.join(context.interpreter.configuration))

