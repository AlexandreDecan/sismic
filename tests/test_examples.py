import unittest
from sismic import io
from sismic.interpreter import Interpreter
from sismic.model import Event


class SimulatorElevatorTests(unittest.TestCase):
    def test_init(self):
        sc = io.import_from_yaml(open('docs/examples/elevator.yaml'))
        interpreter = Interpreter(sc)

        self.assertEqual(len(interpreter.configuration), 5)

    def test_floor_selection(self):
        sc = io.import_from_yaml(open('docs/examples/elevator.yaml'))
        interpreter = Interpreter(sc)

        interpreter.queue(Event('floorSelected', floor=4)).execute_once()
        self.assertEqual(interpreter._evaluator.context['destination'], 4)
        interpreter.execute_once()
        self.assertEqual(sorted(interpreter.configuration), ['active', 'doorsClosed', 'floorListener', 'floorSelecting', 'movingElevator'])

    def test_doorsOpen(self):
        sc = io.import_from_yaml(open('docs/examples/elevator.yaml'))
        interpreter = Interpreter(sc)

        interpreter.queue(Event('floorSelected', floor=4))
        interpreter.execute()
        self.assertEqual(interpreter._evaluator.context['current'], 4)
        interpreter.time += 10
        interpreter.execute()

        self.assertTrue('doorsOpen' in interpreter.configuration)
        self.assertEqual(interpreter._evaluator.context['current'], 0)


class WriterExecutionTests(unittest.TestCase):
    def setUp(self):
        self.sc = io.import_from_yaml(open('docs/examples/writer_options.yaml'))
        self.interpreter = Interpreter(self.sc)

    def test_output(self):
        scenario = [
             Event('keyPress', key='bonjour '),
             Event('toggle'),
             Event('keyPress', key='a '),
             Event('toggle'),
             Event('toggle_bold'),
             Event('keyPress', key='tous !'),
             Event('leave')
        ]

        for event in scenario:
            self.interpreter.queue(event)

        self.interpreter.execute()

        self.assertTrue(self.interpreter.final)
        self.assertEqual(self.interpreter.context['output'], ['bonjour ', '[b]', '[i]', 'a ', '[/b]', '[/i]', '[b]', 'tous !', '[/b]'])


class RemoteElevatorTests(unittest.TestCase):
    def setUp(self):
        self.elevator = Interpreter(io.import_from_yaml(open('docs/examples/elevator.yaml')))
        self.buttons = Interpreter(io.import_from_yaml(open('docs/examples/elevator_buttons.yaml')))
        self.buttons.bind(self.elevator)

    def test_button(self):
        self.assertEqual(self.elevator.context['current'], 0)

        self.buttons.queue(Event('button_2_pushed'))
        self.buttons.execute()

        event = self.elevator._events.pop()
        self.assertEqual(event.name, 'floorSelected')
        self.assertEqual(event.data['floor'], 2)

        self.buttons.queue(Event('button_2_pushed'))
        self.buttons.execute()
        self.elevator.execute()

        self.assertEqual(self.elevator.context['current'], 2)

    def test_button_0_on_groundfloor(self):
        self.assertEqual(self.elevator.context['current'], 0)

        self.buttons.queue(Event('button_0_pushed'))
        self.buttons.execute()
        self.elevator.execute()

        self.assertEqual(self.elevator.context['current'], 0)
