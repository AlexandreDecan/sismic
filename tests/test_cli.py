import unittest
from pyss import _cli_execute


class CommandLineInterfaceTests(unittest.TestCase):
    def test_execute(self):
        class DataTemp:
            infile = open('examples/concrete/history.yaml')
            events = ['next', 'pause']
            verbosity = 3
            python = False

        output = _cli_execute(DataTemp)
        self.assertTrue(len(output) > 0)
