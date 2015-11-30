import unittest
from pyss import load


class LoadFromYAMLTests(unittest.TestCase):
    def test_simple(self):
        content = open('../examples/simple.yaml')
        load.from_yaml(content)

    def test_composite(self):
        content = open('../examples/composite.yaml')
        load.from_yaml(content)

    def test_history(self):
        content = open('../examples/history.yaml')
        load.from_yaml(content)