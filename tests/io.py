import unittest
from pyss import io


class LoadFromYAMLTests(unittest.TestCase):
    def test_simple(self):
        content = open('../examples/simple.yaml')
        io.import_from_yaml(content)

    def test_composite(self):
        content = open('../examples/composite.yaml')
        io.import_from_yaml(content)

    def test_history(self):
        content = open('../examples/history.yaml')
        io.import_from_yaml(content)

    def test_actions(self):
        content = open('../examples/actions.yaml')
        io.import_from_yaml(content)