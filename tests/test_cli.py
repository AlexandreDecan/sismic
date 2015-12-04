import unittest
from pyss import execute_cli


class CLITests(unittest.TestCase):
    def test_simple(self):
        output = execute_cli(open('examples/simple/simple.yaml'), 'dummy', 3, ['click'])
        self.assertEqual(output[-1], 'Final: False\n')
