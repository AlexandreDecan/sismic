from sismic.bdd import map_action, map_assertion


map_action('I open the door', 'I send event door_opened')
map_action('I close the door', 'I send event door_closed')
map_action('I place an item in the oven', 'I send event item_placed')
map_action('I press increase timer button {time} times', 'I repeat "I send event timer_inc" {time} times')
map_action('I press increase power button', 'I send event power_inc')
map_action('I press start button', 'I send event cooking_start')
map_action('I press stop button', 'I send event cooking_stop')
map_action('{tick} seconds elapsed', 'I repeat "I send event timer_tick" {tick} times')

map_assertion('Heating turns on', 'Event heating_on is fired')
map_assertion('Heating does not turn on', 'Event heating_on is not fired')
map_assertion('heating turns off', 'Event heating_off is fired')
map_assertion('lamp turns on', 'Event lamp_switch_on is fired')
map_assertion('lamp turns off', 'Event lamp_switch_off is fired')
