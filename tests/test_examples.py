import unittest
from sismic import io
from sismic.interpreter import Interpreter
from sismic.model import Event


class SimulatorElevatorTests(unittest.TestCase):
    def test_init(self):
        sc = io.import_from_yaml(open('examples/elevator.yaml'))
        interpreter = Interpreter(sc)

        self.assertEqual(len(interpreter.configuration), 5)

    def test_floor_selection(self):
        sc = io.import_from_yaml(open('examples/elevator.yaml'))
        interpreter = Interpreter(sc)

        interpreter.send(Event('floorSelected', {'floor': 4})).execute_once()
        self.assertEqual(interpreter._evaluator.context['destination'], 4)
        interpreter.execute_once()
        self.assertEqual(sorted(interpreter.configuration), ['active', 'doorsClosed', 'floorListener', 'floorSelecting', 'movingElevator'])

    def test_doorsOpen(self):
        sc = io.import_from_yaml(open('examples/elevator.yaml'))
        interpreter = Interpreter(sc)

        interpreter.send(Event('floorSelected', {'floor': 4}))
        interpreter.execute()
        self.assertEqual(interpreter._evaluator.context['current'], 4)
        interpreter.time += 10
        interpreter.execute()

        self.assertTrue('doorsOpen' in interpreter.configuration)
        self.assertEqual(interpreter._evaluator.context['current'], 0)


class WriterExecutionTests(unittest.TestCase):
    def setUp(self):
        self.sc = io.import_from_yaml(open('examples/writer_options.yaml'))
        self.interpreter = Interpreter(self.sc)

    def test_output(self):
        scenario = [
             Event('keyPress', {'key': 'bonjour '}),
             Event('toggle'),
             Event('keyPress', {'key': 'a '}),
             Event('toggle'),
             Event('toggle_bold'),
             Event('keyPress', {'key': 'tous !'}),
             Event('leave')
        ]

        for event in scenario:
            self.interpreter.send(event)

        self.interpreter.execute()

        self.assertTrue(self.interpreter.final)
        self.assertEqual(self.interpreter.evaluator.context['output'], ['bonjour ', '[b]', '[i]', 'a ', '[/b]', '[/i]', '[b]', 'tous !', '[/b]'])
