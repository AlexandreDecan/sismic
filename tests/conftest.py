import os
import pytest

from sismic.io import import_from_yaml
from sismic.interpreter import Interpreter


@pytest.fixture(params=[False, True], ids=['no contract', 'contract'])
def elevator(request):
    if request.param:
        filepath = 'docs/examples/elevator/elevator_contract.yaml'
    else:
        filepath = 'docs/examples/elevator/elevator.yaml'
    with open(filepath) as f:
        sc = import_from_yaml(f)
    return Interpreter(sc)


@pytest.fixture
def remote_elevator(elevator):
    with open('docs/examples/elevator/elevator_buttons.yaml') as f:
        sc = import_from_yaml(f)
    remote = Interpreter(sc)
    remote.bind(elevator)
    return remote


@pytest.fixture
def writer():
    with open('docs/examples/writer_options.yaml') as f:
        sc = import_from_yaml(f)
    return Interpreter(sc)


@pytest.fixture(params=[False, True], ids=['no contract', 'contract'])
def microwave(request):
    if request.param:
        filepath = 'docs/examples/microwave/microwave_with_contracts.yaml'
    else:
        filepath = 'docs/examples/microwave/microwave.yaml'
    with open(filepath) as f:
        sc = import_from_yaml(f)
    return Interpreter(sc)


@pytest.fixture
def simple_statechart():
    with open('tests/yaml/simple.yaml') as f:
        statechart = import_from_yaml(f)
    return statechart


@pytest.fixture
def composite_statechart():
    with open('tests/yaml/composite.yaml') as f:
        statechart = import_from_yaml(f)
    return statechart


@pytest.fixture
def deep_history_statechart():
    with open('tests/yaml/deep_history.yaml') as f:
        statechart = import_from_yaml(f)
    return statechart


@pytest.fixture
def infinite_statechart():
    with open('tests/yaml/infinite.yaml') as f:
        statechart = import_from_yaml(f)
    return statechart


@pytest.fixture
def parallel_statechart():
    with open('tests/yaml/parallel.yaml') as f:
        statechart = import_from_yaml(f)
    return statechart


@pytest.fixture
def nested_parallel_statechart():
    with open('tests/yaml/nested_parallel.yaml') as f:
        statechart = import_from_yaml(f)
    return statechart


@pytest.fixture
def nondeterministic_statechart():
    with open('tests/yaml/nondeterministic.yaml') as f:
        statechart = import_from_yaml(f)
    return statechart


@pytest.fixture
def history_statechart():
    with open('tests/yaml/history.yaml') as f:
        statechart = import_from_yaml(f)
    return statechart


@pytest.fixture
def composite_statechart():
    with open('tests/yaml/composite.yaml') as f:
        statechart = import_from_yaml(f)
    return statechart


@pytest.fixture
def internal_statechart():
    with open('tests/yaml/internal.yaml') as f:
        statechart = import_from_yaml(f)
    return statechart


@pytest.fixture(params=['actions', 'composite', 'deep_history', 'infinite', 'internal',
                        'nested_parallel', 'nondeterministic', 'parallel', 'simple', 'timer'])
def example_from_tests(request):
    with open(os.path.join('tests', 'yaml', request.param + '.yaml')) as f:
        statechart = import_from_yaml(f)
    return statechart


@pytest.fixture(params=['elevator/elevator', 'elevator/elevator_contract', 'microwave/microwave',
                        'elevator/tester_elevator_7th_floor_never_reached', 'elevator/tester_elevator_moves_after_10s',
                        'writer_options'])
def example_from_docs(request):
    with open(os.path.join('docs', 'examples', request.param + '.yaml')) as f:
        statechart = import_from_yaml(f)
    return statechart
