from behave import given, when, then  # type: ignore
from ..interpreter import Event
from .. import testing


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
            parameters[row['parameter'].strip()] = eval(row['value'].strip(), {}, {})

    if parameter and value:
        parameters[parameter.strip()] = eval(value.strip(), {}, {})

    context.interpreter.queue(name, **parameters)


@given('I wait {seconds:g} seconds')
@given('I wait {seconds:g} second')
@when('I wait {seconds:g} seconds')
@when('I wait {seconds:g} second')
def wait(context, seconds):
    context.interpreter.clock.time += seconds


@then('state {name} is entered')
def state_is_entered(context, name):
    # Check that state exists
    context.interpreter.statechart.state_for(name)

    test = testing.state_is_entered(context.monitored_trace, name)
    assert test, 'State {} is not entered'.format(name)


@then('state {name} is not entered')
def state_is_not_entered(context, name):
    # Check that state exists
    context.interpreter.statechart.state_for(name)

    test = not testing.state_is_entered(context.monitored_trace, name)
    assert test, 'State {} is entered'.format(name)


@then('state {name} is exited')
def state_is_exited(context, name):
    # Check that state exists
    context.interpreter.statechart.state_for(name)

    test = testing.state_is_exited(context.monitored_trace, name)
    assert test, 'State {} is not exited'.format(name)


@then('state {name} is not exited')
def state_is_not_exited(context, name):
    # Check that state exists
    context.interpreter.statechart.state_for(name)

    test = not testing.state_is_exited(context.monitored_trace, name)
    assert test, 'State {} is exited'.format(name)


@then('state {name} is active')
def state_is_active(context, name):
    # Check that state exists
    context.interpreter.statechart.state_for(name)

    assert name in context.interpreter.configuration, 'State {} is not active'.format(name)


@then('state {name} is not active')
def state_is_not_active(context, name):
    # Check that state exists
    context.interpreter.statechart.state_for(name)

    assert name not in context.interpreter.configuration, 'State {} is active'.format(name)


@then('event {name} is fired')
@then('event {name} is fired with {parameter}={value}')
def event_is_fired(context, name, parameter=None, value=None):
    parameters = {}

    for row in context.table if context.table else []:
        parameters[row['parameter'].strip()] = eval(row['value'].strip(), {}, {})

    if parameter and value:
        parameters[parameter.strip()] = eval(value.strip(), {}, {})

    test = testing.event_is_fired(context.monitored_trace, name, parameters)

    if len(parameters) == 0:
        assert test, 'Event {} is not fired'.format(name)
    else:
        assert test, 'Event {} is not fired with parameters {}'.format(name, parameters)


@then('event {name} is not fired')
def event_is_not_fired(context, name):
    test = not testing.event_is_fired(context.monitored_trace, name)
    assert test, 'Event {} is fired'.format(name)


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
    assert testing.expression_holds(context.interpreter, expression), 'Expression {} does not holds'.format(expression)


@then('expression {expression} does not hold')
def expression_does_not_hold(context, expression):
    assert not testing.expression_holds(context.interpreter, expression), 'Expression {} holds'.format(expression)


@then('statechart is in a final configuration')
def final_configuration(context):
    assert context.interpreter.final, 'Statechart is not in a final configuration: {}'.format(', '.join(context.interpreter.configuration))


@then('statechart is not in a final configuration')
def not_final_configuration(context):
    assert not context.interpreter.final, 'Statechart is in a final configuration: {}'.format(', '.join(context.interpreter.configuration))

