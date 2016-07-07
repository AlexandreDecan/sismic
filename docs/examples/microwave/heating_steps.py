from sismic.testing import steps
from behave import given, when, then
  
@given('I open the door')
@when('I open the door')
def open_the_door(context):
    return steps.send_event(context, 'door_opened')


@given('I close the door')
@when('I close the door')
def close_the_door(context):
    return steps.send_event(context, 'door_closed')


@when('I power up the microwave')
def power_up_microwave(context):
    return steps.do_nothing(context)


@given('I place an item')
@when('I place an item')
def place_an_item(context):
    return steps.send_event(context, 'item_placed')


@given('I increase the cooking duration')
def increase_cooking_duration(context):
    return steps.send_event(context, 'input_timer_inc')


@when('I press the start button')
def press_start_button(context):
    return steps.send_event(context, 'input_cooking_start')


@then('heating should be on')
def heating_is_active(context):
    return steps.state_is_active(context, 'cooking mode')


@then('heating should not be on')
def heating_not_active(context):
    return steps.state_is_not_active(context, 'cooking mode')


@then('heating should turn on')
def heating_on_is_sent(context):
    return steps.event_is_received(context, 'heating_on')


@then('heating should not turn on')
def heating_on_is_not_sent(context):
    return steps.event_is_not_received(context, 'heating_on')


@then('heating should turn off')
def heating_off_is_sent(context):
    return steps.event_is_received(context, 'heating_off')