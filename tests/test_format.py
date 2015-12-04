import unittest
from pyss import format


class ImportFromYamlTests(unittest.TestCase):
    def test_simple(self):
        content = open('examples/simple/simple.yaml')
        sc =format.import_from_yaml(content)
        self.assertTrue(sc.validate())

    def test_composite(self):
        content = open('examples/simple/composite.yaml')
        sc = format.import_from_yaml(content)
        self.assertTrue(sc.validate())

    def test_history(self):
        content = open('examples/concrete/history.yaml')
        sc = format.import_from_yaml(content)
        self.assertTrue(sc.validate())

    def test_actions(self):
        content = open('examples/simple/actions.yaml')
        sc = format.import_from_yaml(content)
        self.assertTrue(sc.validate())

    def test_elevator(self):
        content = open('examples/concrete/elevator.yaml')
        sc = format.import_from_yaml(content)
        self.assertTrue(sc.validate())


class ExportToDictTests(unittest.TestCase):
    def test_simple(self):
        format.export_to_dict(format.import_from_yaml(open('examples/simple/simple.yaml')))

    def test_composite(self):
        format.export_to_dict(format.import_from_yaml(open('examples/simple/composite.yaml')))

    def test_history(self):
        format.export_to_dict(format.import_from_yaml(open('examples/concrete/history.yaml')))

    def test_actions(self):
        format.export_to_dict(format.import_from_yaml(open('examples/simple/actions.yaml')))
