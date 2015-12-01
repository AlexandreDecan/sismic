import unittest
from pyss import load
from pyss.simulator import Simulator, Step


class SimulatorTest(unittest.TestCase):
    def setUp(self):
        self.sm = load.from_yaml(open('../examples/simple.yaml'))
        self.simulator = Simulator(self.sm)

    def test_init(self):
        self.assertFalse(self.simulator.running)
        self.simulator._configuration.add(self.simulator._sm.initial)
        self.assertIsNone(self.simulator._stabilize_step())
        self.assertTrue(self.simulator.running)

