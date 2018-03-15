from sismic.bdd.steps import action_alias, assertion_alias


action_alias('I open the door', 'I send event door_opened')
action_alias('I close the door', 'I send event door_closed')
action_alias('I place an item in the oven', 'I send event item_placed')
action_alias('I press increase timer button {time} times', 'I repeat "I send event timer_inc" {time} times')
action_alias('I press increase power button', 'I send event power_inc')
action_alias('I press start button', 'I send event cooking_start')
action_alias('{tick} seconds elapsed', 'I repeat "I send event timer_tick" {tick} times')

assertion_alias('Heating turns on', 'Event heating_on is fired')
assertion_alias('Heating does not turn on', 'Event heating_on is not fired')
assertion_alias('heating turns off', 'Event heating_off is fired')
assertion_alias('lamp turns on', 'Event lamp_switch_on is fired')
assertion_alias('lamp turns off', 'Event lamp_switch_off is fired')
