from behave import given, when, then  # type: ignore
from ..interpreter import Event

__all__ = ['action_alias', 'assertion_alias']


def action_alias(step, step_to_execute) -> None:
    """
    Create an alias of a predefined "given"/"when" step.
    Example: action_alias('I open door', 'I send event open_door')

    :param step: New step, without the "given" or "when" keyword.
    :param step_to_execute: existing step, without the "given" or "when" keyword
    """
    @given(step)
    def _(context):
        context.execute_steps('Given ' + step_to_execute)

    @when(step)
    def _(context):
        context.execute_steps('When ' + step_to_execute)


def assertion_alias(step, step_to_execute) -> None:
    """
    Create an alias of a predefined "then" step.
    Example: assertion_alias('door is open', 'state door open is active')

    :param step: New step, without the "then" keyword
    :param step_to_execute: existing step, without "then" keyword
    """
    @then(step)
    def _(context):
        context.execute_steps('Then ' + step_to_execute)


@given('I do nothing')
@when('I do nothing')
def do_nothing(context):
    pass


@given('I reproduce "{scenario}"')
@when('I reproduce "{scenario}"')
def reproduce_scenario(context, scenario):
    current_feature = context.feature
    for included_scenario in current_feature.scenarios:
        if included_scenario.name == scenario:
            steps = ['{} {}'.format(s.step_type, s.name) for s in included_scenario.steps]
            context.execute_steps('\n'.join(steps))
            return
    assert False, 'Unknown scenario {}.'.format(scenario)


@given('I repeat step "{step}" {repeat:d} times')
@when('I repeat step "{step}" {repeat:d} times')
def repeat_step(context, step, repeat):
    keyword = step.split(' ', 1)[0].lower()
    assert keyword in ['given', 'when', 'and', 'but', 'then'], \
        'Step {} should start with a supported keyword'.format(step)

    for _ in range(repeat):
        context.execute_steps(step)


@given('I send event {event_name}')
@given('I send event {event_name} with {parameter}={value}')
@when('I send event {event_name}')
@when('I send event {event_name} with {parameter}={value}')
def send_event(context, event_name, parameter=None, value=None):
    parameters = {}
    if context.table:
        for row in context.table:
            parameters[row['parameter']] = eval(row['value'], {}, {})

    if parameter and value:
        parameters[parameter] = eval(value)

    event = Event(event_name, **parameters)
    context.interpreter.queue(event)


@given('I wait {seconds:g} seconds')
@given('I wait {seconds:g} second')
@when('I wait {seconds:g} seconds')
@when('I wait {seconds:g} second')
def wait(context, seconds):
    context.interpreter.time += seconds


@then('state {name} is entered')
def state_is_entered(context, name):
    for macrostep in context._monitored_trace:
        if name in macrostep.entered_states:
            return
    assert False, 'State {} is not entered'.format(name)


@then('state {name} is not entered')
def state_is_entered(context, name):
    for macrostep in context._monitored_trace:
        if name in macrostep.entered_states:
            assert False, 'State {} is entered'.format(name)


@then('state {name} is exited')
def state_is_exited(context, name):
    for macrostep in context._monitored_trace:
        if name in macrostep.exited_states:
            return
    assert False, 'State {} is not exited'.format(name)


@then('state {name} is not exited')
def state_is_exited(context, name):
    for macrostep in context._monitored_trace:
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

    for macrostep in context._monitored_trace:
        for event in macrostep.sent_events:
            if event.name == name:
                matching_parameters = True
                for key, value in parameters.items():
                    if getattr(event, key, None) != value:
                        matching_parameters = False
                        break
                if matching_parameters:
                    return
    assert False, 'Event {} is not fired with parameters {}'.format(name, parameters)


@then('event {name} is not fired')
def event_is_not_fired(context, name):
    for macrostep in context._monitored_trace:
        for event in macrostep.sent_events:
            assert event.name != name, 'Event {} is fired'.format(name)


@then('no event is fired')
def no_event_is_fired(context):
    for macrostep in context._monitored_trace:
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

