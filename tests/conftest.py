from pathlib import Path

import pytest

from sismic.interpreter import Interpreter
from sismic.io import import_from_yaml


@pytest.fixture()
def docs_dir() -> Path:
    return Path(__file__).parents[1] / "docs"


@pytest.fixture()
def tests_dir() -> Path:
    return Path(__file__).parent


@pytest.fixture(params=[False, True], ids=["no contract", "contract"])
def elevator(request, docs_dir):
    if request.param:
        sc = import_from_yaml(filepath=docs_dir / "examples/elevator/elevator_contract.yaml")
    else:
        sc = import_from_yaml(filepath=docs_dir / "examples/elevator/elevator.yaml")

    return Interpreter(sc)


@pytest.fixture
def remote_elevator(elevator, docs_dir):
    sc = import_from_yaml(filepath=docs_dir / "examples/elevator/elevator_buttons.yaml")
    remote = Interpreter(sc)
    remote.bind(elevator)
    return remote


@pytest.fixture
def writer(docs_dir):
    sc = import_from_yaml(filepath=docs_dir / "examples/writer_options.yaml")
    return Interpreter(sc)


@pytest.fixture(params=[False, True], ids=["no contract", "contract"])
def microwave(request, docs_dir):
    if request.param:
        sc = import_from_yaml(
            filepath=docs_dir / "examples/microwave/microwave_with_contracts.yaml",
        )
    else:
        sc = import_from_yaml(filepath=docs_dir / "examples/microwave/microwave.yaml")
    return Interpreter(sc)


@pytest.fixture
def simple_statechart(tests_dir):
    return import_from_yaml(filepath=tests_dir / "yaml/simple.yaml")


@pytest.fixture
def composite_statechart(tests_dir):
    return import_from_yaml(filepath=tests_dir / "yaml/composite.yaml")


@pytest.fixture
def deep_history_statechart(tests_dir):
    return import_from_yaml(filepath=tests_dir / "yaml/deep_history.yaml")


@pytest.fixture
def final_statechart(tests_dir):
    return import_from_yaml(filepath=tests_dir / "yaml/final.yaml")


@pytest.fixture
def infinite_statechart(tests_dir):
    return import_from_yaml(filepath=tests_dir / "yaml/infinite.yaml")


@pytest.fixture
def parallel_statechart(tests_dir):
    return import_from_yaml(filepath=tests_dir / "yaml/parallel.yaml")


@pytest.fixture
def nested_parallel_statechart(tests_dir):
    return import_from_yaml(filepath=tests_dir / "yaml/nested_parallel.yaml")


@pytest.fixture
def nondeterministic_statechart(tests_dir):
    return import_from_yaml(filepath=tests_dir / "yaml/nondeterministic.yaml")


@pytest.fixture
def history_statechart(tests_dir):
    return import_from_yaml(filepath=tests_dir / "yaml/history.yaml")


@pytest.fixture
def internal_statechart(tests_dir):
    return import_from_yaml(filepath=tests_dir / "yaml/internal.yaml")


@pytest.fixture
def priority_statechart(tests_dir):
    return import_from_yaml(filepath=tests_dir / "yaml/priority.yaml")


@pytest.fixture(
    params=[
        "actions",
        "composite",
        "history",
        "deep_history",
        "final",
        "infinite",
        "internal",
        "priority",
        "nested_parallel",
        "nondeterministic",
        "parallel",
        "simple",
        "timer",
    ],
)
def example_from_tests(request, tests_dir):
    return import_from_yaml(filepath=(tests_dir / "yaml" / request.param).with_suffix(".yaml"))


@pytest.fixture(
    params=[
        "elevator/elevator",
        "elevator/elevator_contract",
        "microwave/microwave",
        "elevator/tester_elevator_7th_floor_never_reached",
        "elevator/tester_elevator_moves_after_10s",
        "writer_options",
    ],
)
def example_from_docs(request, docs_dir):
    return import_from_yaml(filepath=(docs_dir / "examples" / request.param).with_suffix(".yaml"))
