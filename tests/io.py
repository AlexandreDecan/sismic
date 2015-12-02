import unittest
from pyss import io


class ImportFromYamlTests(unittest.TestCase):
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


class ExportToDictTests(unittest.TestCase):
    def test_simple(self):
        io.export_to_dict(io.import_from_yaml(open('../examples/simple.yaml')))

    def test_composite(self):
        io.export_to_dict(io.import_from_yaml(open('../examples/composite.yaml')))

    def test_history(self):
        io.export_to_dict(io.import_from_yaml(open('../examples/history.yaml')))

    def test_actions(self):
        io.export_to_dict(io.import_from_yaml(open('../examples/actions.yaml')))
