import unittest
from pyss import io
from pyss.simulator import Simulator
from pyss.evaluator import PythonEvaluator
from pyss.model import Event


class SimulatorSimpleTest(unittest.TestCase):
    def test_init(self):
        sc = io.import_from_yaml(open('examples/simple/simple.yaml'))
        simulator = Simulator(sc)
        self.assertEqual(simulator.configuration, ['s1'])
        self.assertTrue(simulator.running)

    def test_simple_configuration(self):
        sc = io.import_from_yaml(open('examples/simple/simple.yaml'))
        simulator = Simulator(sc)
        simulator.execute_once()  # Should do nothing!
        self.assertEqual(simulator.configuration, ['s1'])
        simulator.send(Event('goto s2'))
        simulator.execute_once()
        self.assertEqual(simulator.configuration, ['s2'])
        simulator.execute_once()
        self.assertEqual(simulator.configuration, ['s3'])

    def test_simple_entered(self):
        sc = io.import_from_yaml(open('examples/simple/simple.yaml'))
        simulator = Simulator(sc)
        simulator.send(Event('goto s2'))
        self.assertEqual(simulator.execute_once().entered_states, ['s2'])
        simulator.send(Event('goto final'))
        self.assertEqual(simulator.execute_once().entered_states, ['s3'])
        self.assertEqual(simulator.execute_once().entered_states, ['final'])
        self.assertEqual(simulator.configuration, ['final'])

    def test_simple_final(self):
        sc = io.import_from_yaml(open('examples/simple/simple.yaml'))
        simulator = Simulator(sc)
        simulator.send(Event('goto s2')).send(Event('goto final'))
        simulator.execute()
        self.assertFalse(simulator.running)


class SimulatorElevatorTests(unittest.TestCase):
    def test_init(self):
        sc = io.import_from_yaml(open('examples/concrete/elevator.yaml'))
        simulator = Simulator(sc, PythonEvaluator())

        self.assertEqual(len(simulator.configuration), 5)

    def test_floor_selection(self):
        sc = io.import_from_yaml(open('examples/concrete/elevator.yaml'))
        simulator = Simulator(sc, PythonEvaluator())

        simulator.send(Event('floorSelected', {'floor': 4})).execute_once()
        self.assertEqual(simulator._evaluator.context['destination'], 4)
        simulator.execute_once()
        self.assertEqual(sorted(simulator.configuration), ['active', 'doorsClosed', 'floorListener', 'floorSelecting', 'movingElevator'])

    def test_doorsOpen(self):
        sc = io.import_from_yaml(open('examples/concrete/elevator.yaml'))
        simulator = Simulator(sc, PythonEvaluator())

        simulator.send(Event('floorSelected', {'floor': 4}))
        simulator.execute()
        self.assertEqual(simulator._evaluator.context['current'], 4)
        simulator.send(Event('after10s'))
        simulator.execute()

        self.assertTrue('doorsOpen' in simulator.configuration)
        self.assertEqual(simulator._evaluator.context['current'], 0)


class SimulatorNonDeterminismTests(unittest.TestCase):
    def test_nondeterminism(self):
        sc = io.import_from_yaml(open('examples/simple/nondeterministic.yaml'))
        simulator = Simulator(sc)

        with self.assertRaises(Warning):
            simulator.execute_once()


class SimulatorHistoryTests(unittest.TestCase):
    def test_init(self):
        sc = io.import_from_yaml(open('examples/concrete/history.yaml'))
        simulator = Simulator(sc)

    def test_memory(self):
        sc = io.import_from_yaml(open('examples/concrete/history.yaml'))
        simulator = Simulator(sc)

        simulator.send(Event('next')).execute_once()
        self.assertEqual(sorted(simulator.configuration), ['loop', 's2'])

        step = simulator.send(Event('pause')).execute_once()
        self.assertEqual(step.exited_states, ['s2', 'loop'])
        self.assertEqual(sorted(simulator.configuration), ['pause'])

    def test_resume_memory(self):
        sc = io.import_from_yaml(open('examples/concrete/history.yaml'))
        simulator = Simulator(sc)

        simulator.send(Event('next')).send(Event('pause')).send(Event('continue'))
        steps = simulator.execute()
        step = steps[-1]

        self.assertEqual(step.entered_states, ['loop', 'loop.H', 's2'])
        self.assertEqual(step.exited_states, ['pause', 'loop.H'])
        self.assertEqual(sorted(simulator.configuration), ['loop', 's2'])

    def test_after_memory(self):
        sc = io.import_from_yaml(open('examples/concrete/history.yaml'))
        simulator = Simulator(sc)

        simulator.send(Event('next')).send(Event('pause')).send(Event('continue'))
        simulator.send(Event('next')).send(Event('next'))
        simulator.execute()
        self.assertEqual(sorted(simulator.configuration), ['loop', 's1'])

        simulator.send(Event('pause')).send(Event('stop'))
        simulator.execute()
        self.assertFalse(simulator.running)


class SimulatorDeepHistoryTests(unittest.TestCase):
    def test_deep_memory(self):
        sc = io.import_from_yaml(open('examples/concrete/deep_history.yaml'))
        simulator = Simulator(sc)

        simulator.send(Event('next1')).send(Event('next2'))
        simulator.execute()
        self.assertEqual(sorted(simulator.configuration), ['active', 'concurrent_processes', 'process_1', 'process_2', 's12', 's22'])

        simulator.send(Event('error1'))
        simulator.execute()
        self.assertEqual(simulator.configuration, ['pause'])
        self.assertEqual(sorted(sc.states['active.H*'].memory), ['concurrent_processes', 'process_1', 'process_2', 's12', 's22'])

        simulator.send(Event('continue'))
        simulator.execute()
        self.assertEqual(sorted(simulator.configuration), ['active', 'concurrent_processes', 'process_1',
                                                           'process_2', 's12', 's22'])

    def test_entered_order(self):
        sc = io.import_from_yaml(open('examples/concrete/deep_history.yaml'))
        simulator = Simulator(sc)

        simulator.send(Event('next1')).send(Event('next2')).send(Event('pause'))
        step = simulator.execute()[-1]

        self.assertEqual(step.entered_states, ['pause'])
        self.assertEqual(sorted(simulator.configuration), ['pause'])

        step = simulator.send(Event('continue')).execute_once()
        self.assertTrue(step.entered_states.index('active') < step.entered_states.index('active.H*'))
        self.assertTrue(step.entered_states.index('active.H*') < step.entered_states.index('concurrent_processes'))
        self.assertTrue(step.entered_states.index('concurrent_processes') < step.entered_states.index('process_1'))
        self.assertTrue(step.entered_states.index('concurrent_processes') < step.entered_states.index('process_2'))
        self.assertTrue(step.entered_states.index('process_1') < step.entered_states.index('s12'))
        self.assertTrue(step.entered_states.index('process_2') < step.entered_states.index('s22'))

        simulator.send(Event('next1')).send(Event('next2')).execute()
        self.assertFalse(simulator.running)

    def test_exited_order(self):
        sc = io.import_from_yaml(open('examples/concrete/deep_history.yaml'))
        simulator = Simulator(sc)

        simulator.send(Event('next1')).send(Event('next2')).send(Event('pause'))
        step = simulator.execute()[-1]

        self.assertEqual(step.exited_states, ['s12', 's22', 'process_1', 'process_2', 'concurrent_processes', 'active'])
        self.assertEqual(sorted(simulator.configuration), ['pause'])

        step = simulator.send(Event('continue')).execute_once()
        self.assertEqual(step.exited_states, ['pause', 'active.H*'])

        simulator.send(Event('next1')).send(Event('next2')).execute()
        self.assertFalse(simulator.running)


class InfiniteExecutionTests(unittest.TestCase):
    def setUp(self):
        self.sc = io.import_from_yaml(open('examples/simple/infinite.yaml'))
        self.sim = Simulator(self.sc, PythonEvaluator())

    def test_three_steps(self):
        self.assertEqual(self.sim.configuration, ['s1'])
        self.sim.execute_once()
        self.assertEqual(self.sim.configuration, ['s2'])
        self.sim.execute_once()
        self.assertEqual(self.sim.configuration, ['s1'])
        self.sim.execute_once()
        self.assertEqual(self.sim.configuration, ['s2'])
        self.assertEqual(self.sim._evaluator.context['x'], 2)  # x is incremented in s1.on_entry

    def test_auto_three_steps(self):
        self.sim.execute(max_steps=3)
        self.assertEqual(self.sim.configuration, ['s2'])
        self.assertEqual(self.sim._evaluator.context['x'], 2)  # x is incremented in s1.on_entry

    def test_auto_stop(self):
        self.sim.execute()
        self.assertFalse(self.sim.running)
        self.assertEqual(self.sim._evaluator.context['x'], 100)

