import unittest
from pyss import _execute_cli


class CommandLineInterfaceTests(unittest.TestCase):
    def test_execute(self):
        class DataTemp:
            infile = open('examples/concrete/history.yaml')
            events = ['next', 'pause']
            verbosity = 3
            python = False

        output = _execute_cli(DataTemp)
        self.assertTrue(len(output) > 0)
