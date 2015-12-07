import argparse
import io
import traceback

import pyss


def parse_args():  # pragma: no cover
    description = '{d} v{v} by {a}'.format(d=pyss.__description__, v=pyss.__version__, a=pyss.__author__)

    parser = argparse.ArgumentParser(prog='pyss', description=description)
    subparsers = parser.add_subparsers(title='subcommands', dest='subcommand')
    execute_parser = subparsers.add_parser('execute', help='execute a statechart')
    execute_parser.add_argument('infile',
                                type=argparse.FileType('r'),
                                help='A YAML file describing a statechart')
    execute_parser.add_argument('--python',
                                action='store_true',
                                help='use Python to execute and evaluate the actions and conditions.')
    execute_parser.add_argument('-v', '--verbosity',
                                help='set output verbosity: -v displays transitions, -vv displays events and configurations, and -vvv displays states',
                                default=0,
                                action='count')
    execute_parser.add_argument('--events',
                                help='send events to the statechart simulation',
                                nargs='*',
                                metavar='EVENT',
                                default=[])

    validate_parser = subparsers.add_parser('validate', help='validate a statechart')
    validate_parser.add_argument('infile',
                                type=argparse.FileType('r'),
                                help='A YAML file describing a statechart')

    args = parser.parse_args()

    if args.subcommand == 'execute':
        print(_cli_execute(args))
    elif args.subcommand == 'validate':
        print(_cli_validate(args))


def _cli_validate(args):
    s = io.StringIO()

    try:
        sc = pyss.io.import_from_yaml(args.infile)
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
    s = io.StringIO()

    sc = pyss.io.import_from_yaml(args.infile)
    simulator = pyss.simulator.Simulator(sc, pyss.evaluator.PythonEvaluator() if args.python else pyss.evaluator.DummyEvaluator())

    if args.verbosity >= 1:
        print('Initial configuration: ' + ', '.join(simulator.configuration), file=s)

    for event in args.events:
        simulator.send(pyss.model.Event(event))
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
