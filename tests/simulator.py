import unittest
from pyss import io
from pyss.simulator import Simulator
from pyss.evaluator import PythonEvaluator
from pyss.statemachine import Event


class SimulatorTest(unittest.TestCase):
    def test_init(self):
        sm = io.import_from_yaml(open('../examples/simple.yaml'))
        simulator = Simulator(sm)
        self.assertFalse(simulator.running)
        steps = simulator.start()
        self.assertEqual(len(steps), 1)
        self.assertTrue(simulator.running)

    def test_simple(self):
        sm = io.import_from_yaml(open('../examples/simple.yaml'))
        simulator = Simulator(sm)

        simulator.start()
        self.assertEqual(simulator.configuration, ['s1'])
        simulator.execute()  # Should do nothing!
        self.assertEqual(simulator.configuration, ['s1'])
        simulator.send(Event('goto s2'))
        simulator.execute()
        self.assertEqual(simulator.configuration, ['s2'])
        simulator.execute()
        self.assertEqual(simulator.configuration, ['s3'])

    def test_simple_final(self):
        sm = io.import_from_yaml(open('../examples/simple.yaml'))
        simulator = Simulator(sm)
        simulator.send(Event('goto s2'))
        simulator.send(Event('goto final'))
        simulator.start()
        while simulator.execute():
            pass
        self.assertEqual(simulator.configuration, ['final'])
        self.assertFalse(simulator.running)

    def test_simple_iterator_final(self):
        sm = io.import_from_yaml(open('../examples/simple.yaml'))
        simulator = Simulator(sm)
        simulator.send(Event('goto s2'))
        simulator.send(Event('goto final'))
        simulator.start()
        for steps in simulator:
            pass
        self.assertEqual(simulator.configuration, ['final'])
        self.assertFalse(simulator.running)

    def test_elevator(self):
        sm = io.import_from_yaml(open('../examples/elevator.yaml'))
        evaluator = PythonEvaluator()
        simulator = Simulator(sm, evaluator)
        with self.assertRaises(Exception):
            simulator.execute()

        simulator.start()
        self.assertEqual(len(simulator.configuration), 5)

        simulator.send(Event('floorSelected', {'floor': 4}))
        simulator.execute()
        self.assertEqual(evaluator.context['destination'], 4)

        simulator.execute()
        self.assertTrue('doorsClosed' in simulator.configuration)

        while simulator.execute():
            pass
        self.assertTrue('doorsOpen' in simulator.configuration)
        self.assertEqual(simulator._evaluator.context['current'], 4)

        simulator.send(Event('after10s'))
        while simulator.execute():
            pass
        self.assertTrue('doorsOpen' in simulator.configuration)
        self.assertEqual(simulator._evaluator.context['current'], 0)

    def test_nondeterminism(self):
        sm = io.import_from_yaml(open('../examples/nondeterministic.yaml'))
        sm.validate()  # Shouldn't raise anything
        simulator = Simulator(sm)
        simulator.start()
        with self.assertRaises(Warning):
            simulator.execute()

