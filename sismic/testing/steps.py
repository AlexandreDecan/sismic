from behave import given, when, then  # type: ignore
from sismic.io import import_from_yaml
from sismic.interpreter import Interpreter
from sismic.interpreter.helpers import log_trace
from sismic.model import Event


# #################### GENERAL PURPOSE
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


# #################### CONFIGURATION
def _execute_statechart(context, force_execution=False, execute_once=False):
    if context._automatic_execution or force_execution:
        if execute_once:
            context._interpreter.execute_once()
        else:
            context._interpreter.execute()


@given('I disable automatic execution')
def disable_automatic_execution(context):
    context._automatic_execution = False


@given('I enable automatic execution')
def enable_automatic_execution(context):
    context._automatic_execution = True


@given('I import a statechart from {path}')
@when('I import a statechart from {path}')
def load_statechart(context, path):
    with open(path) as f:
        context._statechart = import_from_yaml(f)
    context._interpreter = Interpreter(context._statechart)
    context._steps = log_trace(context._interpreter)

    context._automatic_execution = True

    context._events = []
    context._interpreter.bind(context._events.append)

    _execute_statechart(context, force_execution=True, execute_once=True)


@given('I execute the statechart')
@when('I execute the statechart')
def execute_statechart(context):
    _execute_statechart(context, force_execution=True)


@given('I execute once the statechart')
@when('I execute once the statechart')
def execute_once_statechart(context):
    _execute_statechart(context, force_execution=True, execute_once=True)


# #################### STATECHART
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
    context._interpreter.queue(event)
    _execute_statechart(context)


@given('I wait {seconds:g} seconds')
@given('I wait {seconds:g} second')
@when('I wait {seconds:g} seconds')
@when('I wait {seconds:g} second')
def wait_seconds_once(context, seconds):
    context._interpreter.time += seconds
    _execute_statechart(context)


@given('I wait {seconds:g} seconds {repeat:d} times')
@given('I wait {seconds:g} second {repeat:d} times')
@when('I wait {seconds:g} seconds {repeat:d} times')
@when('I wait {seconds:g} second {repeat:d} times')
def wait_seconds(context, seconds, repeat):
    for _ in range(repeat):
        wait_seconds_once(context, seconds)


@given('I set variable {variable_name} to {value}')
def set_variable(context, variable_name, value):
    context._interpreter.context[variable_name] = eval(value, {}, {})


@then('state {state_name} should be active')
def state_is_active(context, state_name):
    assert state_name in context._statechart.states, 'Unknown state {}'.format(state_name)
    assert state_name in context._interpreter.configuration, 'State {} is not active'.format(state_name)


@then('state {state_name} should not be active')
def state_is_not_active(context, state_name):
    assert state_name in context._statechart.states, 'Unknown state {}'.format(state_name)
    assert state_name not in context._interpreter.configuration, 'State {} is active'.format(state_name)


@then('event {event_name} should be fired')
@then('event {event_name} should be fired with {parameter}={value}')
def event_is_received(context, event_name, parameter=None, value=None):
    parameters = {}
    if context.table:
        for row in context.table:
            parameters[row['parameter']] = eval(row['value'], {}, {})

    if parameter and value:
        parameters[parameter] = eval(value)

    for event in context._events:
        if event.name == event_name:
            matching_parameters = True
            for key, value in parameters.items():
                if getattr(event, key, None) != value:
                    matching_parameters = False
                    break
            if matching_parameters:
                return

    assert False, 'No matching event fired for {} with {} in {}'.format(event_name, parameters, context._events)


@then('event {event_name} should not be fired')
def event_is_not_received(context, event_name):
    for event in context._events:
        if event.name == event_name:
            assert False, 'Event {} was raised'.format(event)


@then('no event should be fired')
def no_event_received(context):
    assert len(context._events) == 0, 'Sent events: {}'.format(context._events)


@then('variable {variable_name} should be defined')
def variable_is_defined(context, variable_name):
    assert variable_name in context._interpreter.context, '{} is not defined'.format(variable_name)


@then('the value of {variable_name} should be {value}')
def variable_equals_value(context, variable_name, value):
    variable_is_defined(context, variable_name)
    value = eval(value, {}, {})
    context_value = context._interpreter.context[variable_name]
    assert context_value == value, 'Variable {} equals {} != {}'.format(variable_name, context_value, value)


@then('expression {expression} should hold')
def expression_holds(context, expression):
    assert context._interpreter._evaluator._evaluate_code(expression), '{} does not hold'.format(expression)


@then('the statechart is in a final configuration')
def final_configuration(context):
    assert context._interpreter.final, \
        'The statechart is not in a final configuration: {}'.format(context._interpreter.configuration)