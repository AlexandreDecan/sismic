import unittest
from unittest.mock import MagicMock

from sismic.io import import_from_yaml
from sismic.interpreter import Interpreter, Event, MetaEvent, InternalEvent
from sismic.exceptions import PropertyStatechartError


class InterpreterMetaEventTests(unittest.TestCase):
    def setUp(self):
        with open('docs/examples/microwave/microwave.yaml') as f:
            self.interpreter = Interpreter(import_from_yaml(f))

        # Create mock for property
        self.property = MagicMock(name='Interpreter', spec=Interpreter)
        self.property.queue = MagicMock(return_value=None)
        self.property.execute = MagicMock(return_value=None)
        self.property.final = False
        self.property.time = 0

        # Bind it
        self.interpreter.bind_property(self.property)

    def test_synchronised_time(self):
        self.assertEqual(self.interpreter.time, self.property.time)
        self.interpreter.time += 10
        self.assertEqual(self.interpreter.time, self.property.time)

    def test_empty_step(self):
        self.interpreter.execute()
        self.assertEqual(self.property.queue.call_args_list[0][0][0], MetaEvent('step started'))
        self.assertEqual(self.property.queue.call_args_list[-1][0][0], MetaEvent('step ended'))

        for call in self.property.queue.call_args_list:
            self.assertIsInstance(call[0][0], MetaEvent)

    def test_event_sent(self):
        # Add send to a state
        state = self.interpreter.statechart.state_for('door closed')
        state.on_entry = 'send("test")'

        self.interpreter.execute()

        self.assertIn(
            MetaEvent('event sent', event=InternalEvent('test')),
            [x[0][0] for x in self.property.queue.call_args_list]
        )

    def test_trace(self):
        self.interpreter.queue(Event('door_opened'))
        self.interpreter.execute()

        call_list = [
            MetaEvent('step started'),
            MetaEvent('state entered', state='controller'),
            MetaEvent('state entered', state='door closed'),
            MetaEvent('state entered', state='closed without item'),
            MetaEvent('step ended'),

            MetaEvent('step started'),
            MetaEvent('event consumed', event=Event('door_opened')),
            MetaEvent('state exited', state='closed without item'),
            MetaEvent('state exited', state='door closed'),
            MetaEvent('transition processed', source='closed without item', target='opened without item', event=Event('door_opened')),
            MetaEvent('state entered', state='door opened'),
            MetaEvent('state entered', state='opened without item'),
            MetaEvent('event sent', event=InternalEvent('lamp_switch_on')),
            MetaEvent('step ended')
        ]

        for i, call in enumerate(call_list):
            effective_call = self.property.queue.call_args_list[i][0][0]

            self.assertIsInstance(effective_call, MetaEvent)
            self.assertEqual(call.name, effective_call.name)

            for param in ['state', 'source', 'target', 'event']:
                if param in call.data:
                    self.assertEqual(effective_call.data[param], call.data[param])

    def test_final(self):
        self.interpreter.execute()
        self.assertFalse(self.property.final)

        self.property.final = True
        self.assertTrue(self.property.final)

        with self.assertRaises(PropertyStatechartError):
            self.interpreter.execute()

