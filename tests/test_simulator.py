import unittest
from pyss import io
from pyss.simulator import Simulator
from pyss.evaluator import PythonEvaluator
from pyss.model import Event


class SimulatorTest(unittest.TestCase):
    def test_init(self):
        sc = io.import_from_yaml(open('examples/simple/simple.yaml'))
        simulator = Simulator(sc)
        self.assertFalse(simulator.running)
        steps = simulator.start()
        self.assertEqual(len(steps), 1)
        self.assertTrue(simulator.running)

    def test_simple(self):
        sc = io.import_from_yaml(open('examples/simple/simple.yaml'))
        simulator = Simulator(sc)

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
        sc = io.import_from_yaml(open('examples/simple/simple.yaml'))
        simulator = Simulator(sc)
        simulator.send(Event('goto s2'))
        simulator.send(Event('goto final'))
        simulator.start()
        while simulator.execute():
            pass
        self.assertEqual(simulator.configuration, ['final'])
        self.assertFalse(simulator.running)

    def test_simple_iterator_final(self):
        sc = io.import_from_yaml(open('examples/simple/simple.yaml'))
        simulator = Simulator(sc)
        simulator.send(Event('goto s2'))
        simulator.send(Event('goto final'))
        simulator.start()
        for steps in simulator:
            pass
        self.assertEqual(simulator.configuration, ['final'])
        self.assertFalse(simulator.running)

    def test_elevator(self):
        sc = io.import_from_yaml(open('examples/concrete/elevator.yaml'))
        evaluator = PythonEvaluator()
        simulator = Simulator(sc, evaluator)
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
        sc = io.import_from_yaml(open('examples/simple/nondeterministic.yaml'))
        simulator = Simulator(sc)
        simulator.start()
        with self.assertRaises(Warning):
            simulator.execute()

    def test_history(self):
        sc = io.import_from_yaml(open('examples/concrete/history.yaml'))
        simulator = Simulator(sc)
        simulator.start()
        self.assertEqual(sorted(simulator.configuration), ['loop', 's1'])
        simulator.send(Event('stop')).execute()
        self.assertEqual(sorted(simulator.configuration), ['loop', 's1'])
        simulator.send(Event('next')).execute()
        self.assertEqual(sorted(simulator.configuration), ['loop', 's2'])
        simulator.send(Event('pause')).execute()
        self.assertEqual(sorted(simulator.configuration), ['pause'])
        simulator.send(Event('continue')).execute()
        self.assertEqual(sorted(simulator.configuration), ['loop', 's2'])
        simulator.send(Event('next')).execute()
        simulator.send(Event('next')).execute()
        self.assertEqual(sorted(simulator.configuration), ['loop', 's1'])
        simulator.send(Event('pause')).execute()
        simulator.send(Event('stop')).execute()
        self.assertFalse(simulator.running)

    def test_deep_history(self):
        sc = io.import_from_yaml(open('examples/concrete/deep_history.yaml'))
        simulator = Simulator(sc)
        simulator.start()
        base_states = ['active', 'concurrent_processes', 'process_1', 'process_2']
        self.assertEqual(sorted(simulator.configuration), base_states + ['s11', 's21'])
        simulator.send(Event('next1')).execute()
        simulator.send(Event('next2')).execute()
        self.assertEqual(sorted(simulator.configuration), base_states + ['s12', 's22'])
        simulator.send(Event('pause')).execute()
        self.assertEqual(sorted(simulator.configuration), ['pause'])
        simulator.send(Event('continue')).execute()
        self.assertEqual(sorted(simulator.configuration), base_states + ['s12', 's22'])
        simulator.send(Event('next1')).execute()
        simulator.send(Event('next2')).execute()
        self.assertFalse(simulator.running)