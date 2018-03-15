from sismic.bdd.steps import action_alias, assertion_alias


action_alias('I open the door', 'I send event door_opened')
action_alias('I close the door', 'I send event door_closed')
action_alias('I power up the microwave', 'I do nothing')
action_alias('I place an item', 'I send event item_placed')
action_alias('I increase the cooking duration', 'I send event input_timer_inc')
action_alias('I press the start button', 'I send event input_cooking_start')

assertion_alias('Heating should be on', 'State cooking mode is active')
assertion_alias('Heating should not be on', 'State cooking mode is not active')
assertion_alias('Heating should turn on', 'Event heating_on is fired')
assertion_alias('Heating should not turn on', 'Event heating_on is not fired')
assertion_alias('Heating should turn off', 'Event heating_off is fired')
