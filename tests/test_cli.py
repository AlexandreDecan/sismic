import unittest
from pyss import cli


class CommandLineInterfaceTests(unittest.TestCase):
    def test_execute(self):
        class DataTemp:
            infile = open('examples/concrete/history.yaml')
            events = ['next', 'pause']
            verbosity = 3
            python = False

        output = cli._cli_execute(DataTemp)
        self.assertTrue(len(output) > 0)

    def test_validate(self):
        class DataTemp:
            infile = open('examples/concrete/history.yaml')

        output = cli._cli_validate(DataTemp)
        self.assertTrue(len(output) > 0)

