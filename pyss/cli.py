from io import StringIO
import traceback

from .simulator import Simulator
from .evaluator import PythonEvaluator, DummyEvaluator
from .io import import_from_yaml
from .model import Event


def _cli_validate(args):
    s = StringIO()

    try:
        sc = import_from_yaml(args.infile)
    except Exception as e:
        print('Statechart cannot be validated: invalid YAML format. Exception was:', file=s)
        print(e, file=s)
        traceback.print_exc(file=s)

        return s.getvalue()
    try:
        sc.validate()
        print('Statechart validates.', file=s)
    except Exception as e:
        print('Statechart does not validate. Exception was:', file=s)
        print(e, file=s)
        traceback.print_exc(file=s)

    return s.getvalue()


def _cli_execute(args):
    s = StringIO()

    sc = import_from_yaml(args.infile)
    simulator = Simulator(sc, DummyEvaluator() if args.nocode else PythonEvaluator())

    if args.verbosity >= 1:
        print('Initial configuration: ' + ', '.join(simulator.configuration), file=s)

    for event in args.events:
        simulator.send(Event(event))
    if args.verbosity >= 2:
        print('Events sent: ' + ', '.join(args.events), file=s)

    for i, step in enumerate(simulator):
        if args.verbosity >= 1:
            print('Step {} - '.format(i+1), file=s, end='')
        if args.verbosity >= 2:
            print('Considered event: {}'.format(step.event), file=s)
        if args.verbosity >= 1:
            print('Transition: ' + str(step.transition), file=s)
        if args.verbosity >= 3:
            print('Exited states: ' + ', '.join(step.exited_states), file=s)
            print('Entered states: ' + ', '.join(step.entered_states), file=s)
        if args.verbosity >= 2:
            print('Configuration: ' + ', '.join(simulator.configuration), file=s)

    print('Final: {}'.format(not simulator.running), file=s)
    return s.getvalue()
