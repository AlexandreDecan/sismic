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
