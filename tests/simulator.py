import unittest
from pyss import io
from pyss.simulator import Simulator, MicroStep
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
        simulator.execute()
        self.assertEqual(simulator.configuration, ['s1'])
        simulator.fire_event(Event('goto s2'))
        simulator.execute()
        self.assertEqual(simulator.configuration, ['s2'])
        simulator.execute()
        self.assertEqual(simulator.configuration, ['s3'])

    def test_simple_iterator(self):
        sm = io.import_from_yaml(open('../examples/simple.yaml'))
        simulator = Simulator(sm)
        simulator.fire_event(Event('goto s2'))
        simulator.fire_event(Event('goto final'))
        for _ in simulator:
            pass
        self.assertEqual(simulator.configuration, ['final'])
        self.assertFalse(simulator.running)

        simulator = Simulator(sm)
        steps = iter(simulator)
        next(steps)
        steps.send(Event('goto s2'))
        steps.send(Event('goto final'))
        for _ in simulator:
            pass
        self.assertEqual(simulator.configuration, ['final'])
        self.assertFalse(simulator.running)

    def test_simple_infinite_run(self):
        sm = io.import_from_yaml(open('../examples/simple.yaml'))
        simulator = Simulator(sm)
        steps = iter(simulator)
        next(steps)
        steps.send(Event('goto s2'))
        with self.assertRaises(RuntimeError):
            for _ in simulator:
                pass


