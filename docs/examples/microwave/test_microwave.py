import unittest
from sismic.io import import_from_yaml
from sismic.interpreter import Interpreter


class MicrowaveTests(unittest.TestCase):
    def setUp(self):
        with open('microwave.yaml') as f:
            sc = import_from_yaml(f)

        self.oven = Interpreter(sc)
        self.oven.execute_once()

    def test_no_heating_when_door_is_not_closed(self):
        self.oven.queue('door_opened', 'item_placed', 'timer_inc')
        self.oven.execute()

        self.oven.queue('cooking_start')
        
        for step in iter(self.oven.execute_once, None):
            for event in step.sent_events:
                self.assertNotEqual(event.name, 'heating_on')
        
        self.assertNotIn('cooking_mode', self.oven.configuration)

    def test_increase_timer(self):
        self.oven.queue('door_opened', 'item_placed', 'door_closed')
    
        events = 10 * ['timer_inc']    
        self.oven.queue(*events)
        self.oven.execute()
        
        self.assertEqual(self.oven.context['timer'], 10)
