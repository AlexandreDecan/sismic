import unittest
from sismic import io


class ImportFromYamlTests(unittest.TestCase):
    def test_simple(self):
        content = open('tests/yaml/simple.yaml')
        sc =io.import_from_yaml(content)
        self.assertTrue(sc.validate())

    def test_composite(self):
        content = open('tests/yaml/composite.yaml')
        sc = io.import_from_yaml(content)
        self.assertTrue(sc.validate())

    def test_history(self):
        content = open('tests/yaml/history.yaml')
        sc = io.import_from_yaml(content)
        self.assertTrue(sc.validate())

    def test_actions(self):
        content = open('tests/yaml/actions.yaml')
        sc = io.import_from_yaml(content)
        self.assertTrue(sc.validate())

    def test_elevator(self):
        content = open('examples/elevator.yaml')
        sc = io.import_from_yaml(content)
        self.assertTrue(sc.validate())

    def test_contract(self):
        content = open('examples/elevator_contract.yaml')
        sc = io.import_from_yaml(content)
        self.assertTrue(sc.validate())


class ExportToDictYAMLTests(unittest.TestCase):
    def test_simple(self):
        io.export_to_yaml(io.import_from_yaml(open('tests/yaml/simple.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('tests/yaml/simple.yaml')))

    def test_composite(self):
        io.export_to_yaml(io.import_from_yaml(open('tests/yaml/composite.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('tests/yaml/composite.yaml')))

    def test_history(self):
        io.export_to_yaml(io.import_from_yaml(open('tests/yaml/history.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('tests/yaml/history.yaml')))

    def test_actions(self):
        io.export_to_yaml(io.import_from_yaml(open('tests/yaml/actions.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('tests/yaml/actions.yaml')))

    def test_contract(self):
        io.export_to_yaml(io.import_from_yaml(open('examples/elevator.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('examples/elevator.yaml')))
