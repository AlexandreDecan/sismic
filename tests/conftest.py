import os
import pytest

from sismic.io import import_from_yaml
from sismic.interpreter import Interpreter


@pytest.fixture(params=[False, True], ids=['no contract', 'contract'])
def elevator(request):
    if request.param:
        filepath = '../docs/examples/elevator/elevator_contract.yaml'
    else:
        filepath = '../docs/examples/elevator/elevator.yaml'
    with open(filepath) as f:
        sc = import_from_yaml(f)
    return Interpreter(sc)


@pytest.fixture
def remote_elevator(elevator):
    with open('../docs/examples/elevator/elevator_buttons.yaml') as f:
        sc = import_from_yaml(f)
    remote = Interpreter(sc)
    remote.bind(elevator)
    return remote


@pytest.fixture
def writer():
    with open('../docs/examples/writer_options.yaml') as f:
        sc = import_from_yaml(f)
    return Interpreter(sc)


@pytest.fixture(params=[False, True], ids=['no contract', 'contract'])
def microwave(request):
    if request.param:
        filepath = '../docs/examples/microwave/microwave_with_contracts.yaml'
    else:
        filepath = '../docs/examples/microwave/microwave.yaml'
    with open(filepath) as f:
        sc = import_from_yaml(f)
    return Interpreter(sc)


@pytest.fixture
def tests_statecharts():
    files = ['actions', 'composite', 'deep_history', 'infinite', 'internal',
             'nested_parallel', 'nondeterministic', 'parallel', 'simple', 'timer']

    statecharts = []
    for filename in files:
        with open(os.path.join('yaml', filename + '.yaml')) as f:
            statecharts.append(import_from_yaml(f))
    return statecharts


@pytest.fixture
def docs_statecharts():
    files = ['elevator/elevator', 'elevator/elevator_contract', 'microwave/microwave',
                 'elevator/tester_elevator_7th_floor_never_reached', 'elevator/tester_elevator_moves_after_10s', 'writer_options']

    statecharts = []
    for filename in files:
        with open(os.path.join('..', 'docs', 'examples', filename + '.yaml')) as f:
            statecharts.append(import_from_yaml(f))
    return statecharts
