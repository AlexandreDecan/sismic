import unittest
from sismic import cli


class CommandArgs:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class CommandLineInterfaceTests(unittest.TestCase):
    def test_execute(self):
        args = CommandArgs(
            infile=open('examples/concrete/history.yaml'),
            events=['next', 'pause'],
            verbosity=3,
            nocode=False,
            maxsteps=-1,
            silentcontract=False,
        )

        output = cli.cli_execute(args)
        self.assertTrue(len(output) > 0)

    def test_parametrized_event(self):
        args = CommandArgs(
            infile=open('examples/simple/simple.yaml'),
            events=['goto s2:a=1:b=True:c=\'blabla\'', 'goto final'],
            verbosity=0,
            nocode=False,
            maxsteps=-1,
            silentcontract=False,
        )

        output = cli.cli_execute(args)
        self.assertEqual(output.strip(), 'Final: True')

    def test_infinite(self):
        args = CommandArgs(
            infile=open('examples/simple/infinite.yaml'),
            events=[],
            verbosity=0,
            nocode=False,
            maxsteps=-1,
            silentcontract=False,
        )
        output = cli.cli_execute(args)
        self.assertEqual(output.strip(), 'Final: True')

    def test_limited_infinite(self):
        args = CommandArgs(
            infile=open('examples/simple/infinite.yaml'),
            events=[],
            verbosity=0,
            nocode=False,
            maxsteps=10,
            silentcontract=False,
        )

        output = cli.cli_execute(args)
        self.assertEqual(output.strip(), 'Final: False')

    def test_validate(self):
        args = CommandArgs(
            infile=open('examples/concrete/history.yaml')
        )

        output = cli.cli_validate(args)
        self.assertTrue(len(output) > 0)

    def test_testing_succeeded(self):
        args = CommandArgs(
            infile=open('examples/concrete/elevator.yaml'),
            tests=[open('examples/tester/elevator/closed_doors_while_moving.yaml'),
                   open('examples/tester/elevator/destination_reached.yaml')],
            events=['floorSelected:floor=4'],
            nocode=False,
            maxsteps=-1,
            silentcontract=False,
        )
        output = cli.cli_test(args)
        self.assertEqual(output.strip(), 'All tests passed')

    def test_testing_failed(self):
        args = CommandArgs(
            infile=open('examples/concrete/elevator.yaml'),
            tests=[open('examples/tester/elevator/closed_doors_while_moving.yaml'),
                   open('examples/tester/elevator/never_go_7th_floor.yaml')],
            events=['floorSelected:floor=7'],
            nocode=False,
            maxsteps=-1,
            silentcontract=False,
        )
        output = cli.cli_test(args)
        self.assertNotEqual(output.strip(), 'All tests passed')
