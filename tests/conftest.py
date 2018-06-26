import os
import pytest

from sismic.io import import_from_yaml
from sismic.interpreter import Interpreter



@pytest.fixture(params=[False, True], ids=['no contract', 'contract'])
def elevator(request):
    if request.param:
        sc = import_from_yaml(filepath='docs/examples/elevator/elevator_contract.yaml')
    else:
        sc = import_from_yaml(filepath='docs/examples/elevator/elevator.yaml')

    return Interpreter(sc)


@pytest.fixture
def remote_elevator(elevator):
    sc = import_from_yaml(filepath='docs/examples/elevator/elevator_buttons.yaml')
    remote = Interpreter(sc)
    remote.bind(elevator)
    return remote


@pytest.fixture
def writer():
    sc = import_from_yaml(filepath='docs/examples/writer_options.yaml')
    return Interpreter(sc)


@pytest.fixture(params=[False, True], ids=['no contract', 'contract'])
def microwave(request):
    if request.param:
        sc = import_from_yaml(filepath='docs/examples/microwave/microwave_with_contracts.yaml')
    else:
        sc = import_from_yaml(filepath='docs/examples/microwave/microwave.yaml')
    return Interpreter(sc)


@pytest.fixture
def simple_statechart():
    return import_from_yaml(filepath='tests/yaml/simple.yaml')


@pytest.fixture
def composite_statechart():
    return import_from_yaml(filepath='tests/yaml/composite.yaml')


@pytest.fixture
def deep_history_statechart():
    return import_from_yaml(filepath='tests/yaml/deep_history.yaml')


@pytest.fixture
def final_statechart():
    return import_from_yaml(filepath='tests/yaml/final.yaml')


@pytest.fixture
def infinite_statechart():
    return import_from_yaml(filepath='tests/yaml/infinite.yaml')


@pytest.fixture
def parallel_statechart():
    return import_from_yaml(filepath='tests/yaml/parallel.yaml')


@pytest.fixture
def nested_parallel_statechart():
    return import_from_yaml(filepath='tests/yaml/nested_parallel.yaml')


@pytest.fixture
def nondeterministic_statechart():
    return import_from_yaml(filepath='tests/yaml/nondeterministic.yaml')


@pytest.fixture
def history_statechart():
    return import_from_yaml(filepath='tests/yaml/history.yaml')


@pytest.fixture
def internal_statechart():
    return import_from_yaml(filepath='tests/yaml/internal.yaml')


@pytest.fixture
def priority_statechart():
    return import_from_yaml(filepath='tests/yaml/priority.yaml')


@pytest.fixture(params=['actions', 'composite', 'deep_history', 'final', 'infinite', 'internal', 'priority',
                        'nested_parallel', 'nondeterministic', 'parallel', 'simple', 'timer'])
def example_from_tests(request):
    return import_from_yaml(filepath=os.path.join('tests', 'yaml', request.param + '.yaml'))


@pytest.fixture(params=['elevator/elevator', 'elevator/elevator_contract', 'microwave/microwave',
                        'elevator/tester_elevator_7th_floor_never_reached', 'elevator/tester_elevator_moves_after_10s',
                        'writer_options'])
def example_from_docs(request):
    return import_from_yaml(filepath=os.path.join('docs', 'examples', request.param + '.yaml'))
