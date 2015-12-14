from io import StringIO
import traceback

from .interpreter import Interpreter
from .evaluator import PythonEvaluator, DummyEvaluator
from .io import import_from_yaml
from .model import Event
from .checker import TesterConfiguration


def parse_event(event_str: str) -> Event:
    """
    Parse a string to identify an event name and (optionally) additional parameter.

    :param event_str: expects name[\:key=value[\:key=value[...]]]
    :return: The constructed ``Event`` instance
    """
    if ':' in event_str:
        name, *args = event_str.split(':')
        data = {}
        for arg in args:
            arg_name, arg_value = arg.split('=', 1)
            data[arg_name] = eval(arg_value, {}, {})
        return Event(name, data)
    else:
        return Event(event_str)


def cli_validate(args):
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


def cli_execute(args):
    s = StringIO()

    sc = import_from_yaml(args.infile)
    simulator = Interpreter(sc, DummyEvaluator if args.nocode else PythonEvaluator)

    if args.verbosity >= 1:
        print('Initial configuration: ' + ', '.join(simulator.configuration), file=s)

    for event in args.events:
        simulator.send(parse_event(event))
    if args.verbosity >= 2:
        print('Events sent: ' + ', '.join(args.events), file=s)

    for i, step in enumerate(simulator.execute(args.maxsteps)):
        if args.verbosity >= 1:
            print('Step {} - '.format(i+1), file=s, end='')
        if args.verbosity >= 2:
            print('Considered event: {}'.format(step.event), file=s)
        if args.verbosity >= 1:
            print('Transitions: ' + str(step.transitions), file=s)
        if args.verbosity >= 3:
            print('Exited states: ' + ', '.join(step.exited_states), file=s)
            print('Entered states: ' + ', '.join(step.entered_states), file=s)
        if args.verbosity >= 2:
            print('Configuration: ' + ', '.join(simulator.configuration), file=s)

    print('Final: {}'.format(not simulator.running), file=s)
    return s.getvalue()


def cli_test(args):
    s = StringIO()

    sc = import_from_yaml(args.infile)
    tests = [import_from_yaml(test) for test in args.tests]
    events = [parse_event(name) for name in args.events]

    config = TesterConfiguration(sc, evaluator_klass=DummyEvaluator if args.nocode else PythonEvaluator)
    for test in tests:
        config.add_test(test)

    tester = config.build_tester(events)

    try:
        tester.execute(args.maxsteps)
        tester.stop()
    except AssertionError as e:
        print(e.args, file=s)
    else:
        print('All tests passed', file=s)

    return s.getvalue()


