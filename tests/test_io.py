import unittest
from sismic import io


class ImportFromYamlTests(unittest.TestCase):
    def test_yaml_tests(self):
        io.import_from_yaml(open('tests/yaml/actions.yaml'))
        io.import_from_yaml(open('tests/yaml/composite.yaml'))
        io.import_from_yaml(open('tests/yaml/deep_history.yaml'))
        io.import_from_yaml(open('tests/yaml/history.yaml'))
        io.import_from_yaml(open('tests/yaml/infinite.yaml'))
        io.import_from_yaml(open('tests/yaml/internal.yaml'))
        io.import_from_yaml(open('tests/yaml/nested_parallel.yaml'))
        io.import_from_yaml(open('tests/yaml/nondeterministic.yaml'))
        io.import_from_yaml(open('tests/yaml/parallel.yaml'))
        io.import_from_yaml(open('tests/yaml/simple.yaml'))
        io.import_from_yaml(open('tests/yaml/timer.yaml'))

    def test_examples(self):
        io.import_from_yaml(open('examples/elevator.yaml'))
        io.import_from_yaml(open('examples/elevator_contract.yaml'))
        io.import_from_yaml(open('examples/microwave.yaml'))
        io.import_from_yaml(open('examples/tester_elevator_7th_floor_never_reached.yaml'))
        io.import_from_yaml(open('examples/tester_elevator_moves_after_10s.yaml'))
        io.import_from_yaml(open('examples/writer_options.yaml'))


class ExportToDictYAMLTests(unittest.TestCase):
    def test_yaml_tests(self):
        io.export_to_yaml(io.import_from_yaml(open('tests/yaml/actions.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('tests/yaml/composite.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('tests/yaml/deep_history.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('tests/yaml/history.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('tests/yaml/infinite.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('tests/yaml/internal.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('tests/yaml/nested_parallel.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('tests/yaml/nondeterministic.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('tests/yaml/parallel.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('tests/yaml/simple.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('tests/yaml/timer.yaml')))

    def test_examples(self):
        io.export_to_yaml(io.import_from_yaml(open('examples/elevator.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('examples/elevator_contract.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('examples/microwave.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('examples/tester_elevator_7th_floor_never_reached.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('examples/tester_elevator_moves_after_10s.yaml')))
        io.export_to_yaml(io.import_from_yaml(open('examples/writer_options.yaml')))