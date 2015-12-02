import unittest
from pyss import io


class ImportFromYamlTests(unittest.TestCase):
    def test_simple(self):
        content = open('../examples/simple.yaml')
        sm =io.import_from_yaml(content)
        self.assertTrue(sm.valid)

    def test_composite(self):
        content = open('../examples/composite.yaml')
        sm = io.import_from_yaml(content)
        self.assertTrue(sm.valid)

    def test_history(self):
        content = open('../examples/history.yaml')
        sm = io.import_from_yaml(content)
        self.assertTrue(sm.valid)

    def test_actions(self):
        content = open('../examples/actions.yaml')
        sm = io.import_from_yaml(content)
        self.assertTrue(sm.valid)


class ExportToDictTests(unittest.TestCase):
    def test_simple(self):
        io.export_to_dict(io.import_from_yaml(open('../examples/simple.yaml')))

    def test_composite(self):
        io.export_to_dict(io.import_from_yaml(open('../examples/composite.yaml')))

    def test_history(self):
        io.export_to_dict(io.import_from_yaml(open('../examples/history.yaml')))

    def test_actions(self):
        io.export_to_dict(io.import_from_yaml(open('../examples/actions.yaml')))
