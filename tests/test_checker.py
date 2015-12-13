import unittest
from sismic import io
from sismic.model import Event
from sismic.checker import TesterConfiguration


class ElevatorTests(unittest.TestCase):
    def setUp(self):
        self.sc = io.import_from_yaml(open('examples/concrete/elevator.yaml'))
        self.tests = {
            'destination_reached': io.import_from_yaml(open('examples/tester/elevator/destination_reached.yaml')),
            'closed_doors_while_moving': io.import_from_yaml(open('examples/tester/elevator/closed_doors_while_moving.yaml')),
            'never_go_7th_floor': io.import_from_yaml(open('examples/tester/elevator/never_go_7th_floor.yaml')),
        }
        self.scenarios = {
            '4th floor': [Event('floorSelected', data={'floor': 4})],
            '7th floor': [Event('floorSelected', data={'floor': 7})],
        }
        self.tester = TesterConfiguration(self.sc)

    def test_destination_reached(self):
        self.tester.add_test(self.tests['destination_reached'])
        with self.tester.build_tester(self.scenarios['4th floor']) as tester:
            tester.execute()

    def test_doors_closed_while_moving(self):
        self.tester.add_test(self.tests['closed_doors_while_moving'])
        with self.tester.build_tester(self.scenarios['4th floor']) as tester:
            tester.execute()

    def test_never_go_underground(self):
        self.tester.add_test(self.tests['never_go_7th_floor'])

        with self.assertRaises(AssertionError):
            with self.tester.build_tester(self.scenarios['7th floor']) as tester:
                tester.execute()
