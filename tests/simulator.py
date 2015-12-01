import unittest
from pyss import load
from pyss.simulator import Simulator, Step
from pyss.statemachine import Event


class SimulatorTest(unittest.TestCase):
    def test_init(self):
        sm = load.from_yaml(open('../examples/simple.yaml'))
        simulator = Simulator(sm)
        self.assertFalse(simulator.running)
        steps = simulator.start()
        self.assertEqual(len(steps), 1)
        self.assertTrue(simulator.running)

    def test_simple(self):
        sm = load.from_yaml(open('../examples/simple.yaml'))
        simulator = Simulator(sm)
        steps = []
        steps += simulator.start()
        self.assertEqual(simulator.configuration, ['s1'])
        steps += simulator.macrostep()
        self.assertEqual(simulator.configuration, ['s1'])
        simulator.fire_event(Event('click'))
        steps += simulator.macrostep()
        self.assertEqual(simulator.configuration, ['s2'])
        steps += simulator.macrostep()
        self.assertEqual(simulator.configuration, ['s3'])
        for step in steps:
            print(step)