import unittest
from pyss import cli


class CommandLineInterfaceTests(unittest.TestCase):
    def test_execute(self):
        class DataTemp:
            infile = open('examples/concrete/history.yaml')
            events = ['next', 'pause']
            verbosity = 3
            nocode = False
            maxsteps = -1

        output = cli.cli_execute(DataTemp)
        self.assertTrue(len(output) > 0)

    def test_infinite(self):
        class DataTemp:
            infile = open('examples/simple/infinite.yaml')
            events = []
            verbosity = 0
            nocode = False
            maxsteps = -1

        output = cli.cli_execute(DataTemp)
        self.assertEqual(output.strip(), 'Final: True')

    def test_limited_infinite(self):
        class DataTemp:
            infile = open('examples/simple/infinite.yaml')
            events = []
            verbosity = 0
            nocode = False
            maxsteps = 10

        output = cli.cli_execute(DataTemp)
        self.assertEqual(output.strip(), 'Final: False')

    def test_validate(self):
        class DataTemp:
            infile = open('examples/concrete/history.yaml')

        output = cli.cli_validate(DataTemp)
        self.assertTrue(len(output) > 0)

