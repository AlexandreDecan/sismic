import unittest
from pyss import io


class ImportFromYamlTests(unittest.TestCase):
    def test_simple(self):
        content = open('../examples/simple/simple.yaml')
        sm =io.import_from_yaml(content)
        self.assertTrue(sm.validate())

    def test_composite(self):
        content = open('../examples/simple/composite.yaml')
        sm = io.import_from_yaml(content)
        self.assertTrue(sm.validate())

    def test_history(self):
        content = open('../examples/simple/history.yaml')
        sm = io.import_from_yaml(content)
        self.assertTrue(sm.validate())

    def test_actions(self):
        content = open('../examples/simple/actions.yaml')
        sm = io.import_from_yaml(content)
        self.assertTrue(sm.validate())


class ExportToDictTests(unittest.TestCase):
    def test_simple(self):
        io.export_to_dict(io.import_from_yaml(open('../examples/simple/simple.yaml')))

    def test_composite(self):
        io.export_to_dict(io.import_from_yaml(open('../examples/simple/composite.yaml')))

    def test_history(self):
        io.export_to_dict(io.import_from_yaml(open('../examples/simple/history.yaml')))

    def test_actions(self):
        io.export_to_dict(io.import_from_yaml(open('../examples/simple/actions.yaml')))
