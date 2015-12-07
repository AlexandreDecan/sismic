import unittest
from pyss import io


class ImportFromYamlTests(unittest.TestCase):
    def test_simple(self):
        content = open('examples/simple/simple.yaml')
        sc =io.import_from_yaml(content)
        self.assertTrue(sc.validate())

    def test_composite(self):
        content = open('examples/simple/composite.yaml')
        sc = io.import_from_yaml(content)
        self.assertTrue(sc.validate())

    def test_history(self):
        content = open('examples/concrete/history.yaml')
        sc = io.import_from_yaml(content)
        self.assertTrue(sc.validate())

    def test_actions(self):
        content = open('examples/simple/actions.yaml')
        sc = io.import_from_yaml(content)
        self.assertTrue(sc.validate())

    def test_elevator(self):
        content = open('examples/concrete/elevator.yaml')
        sc = io.import_from_yaml(content)
        self.assertTrue(sc.validate())


class ExportToDictYAMLTests(unittest.TestCase):
    def test_simple(self):
        io.export_to_dict(io.import_from_yaml(open('examples/simple/simple.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('examples/simple/simple.yaml')))

    def test_composite(self):
        io.export_to_dict(io.import_from_yaml(open('examples/simple/composite.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('examples/simple/composite.yaml')))

    def test_history(self):
        io.export_to_dict(io.import_from_yaml(open('examples/concrete/history.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('examples/concrete/history.yaml')))

    def test_actions(self):
        io.export_to_dict(io.import_from_yaml(open('examples/simple/actions.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('examples/simple/actions.yaml')))

