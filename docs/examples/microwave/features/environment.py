from os.path import dirname, join
from sismic.io.yaml import import_from_yaml
from sismic.bdd.environment import setup_behave_context
from sismic.interpreter.default import Interpreter


def setup_application(context, state_def) -> Interpreter:
    with open(state_def) as f:
        sc = import_from_yaml(f)
    return Interpreter(sc)


def before_all(context):
    statechart_dir = dirname(dirname(__file__))
    state_def = join(statechart_dir, 'microwave.yaml')
    setup_behave_context(
        context,
        statechart_path=state_def,
        interpreter_klass=lambda statechart: setup_application(context, state_def),
    )
