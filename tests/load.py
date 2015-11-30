import unittest
from pyss import load


class LoadStateMachineTests(unittest.TestCase):
    def test_from_yaml(self):
        content = open('../examples/simple.yaml')
        load.from_yaml(content)

    def test_from_json(self):
        content = open('../examples/simple.json')
        load.from_json(content)