from .model import Event
from .simulator import MicroStep, Simulator
from .evaluator import DummyEvaluator, PythonEvaluator
from .format import import_from_yaml


__description__ = 'Python Statechart Simulator'
__version__ = '0.3.3'
__url__ = 'https://github.com/AlexandreDecan/PySS/'
__author__ = 'Alexandre Decan'
__email__ = 'alexandre.decan@lexpage.net'
__licence__ = 'LGPL3'


def main():  # pragma: no cover
    import argparse
    description = '{d} v{v} by {a}'.format(d=__description__, v=__version__, a=__author__)

    parser = argparse.ArgumentParser(prog='pyss', description=description)
    subparsers = parser.add_subparsers(title='subcommands')
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

    args = parser.parse_args()
    if 'execute' in args:
        print(_cli_execute(args))


def _cli_execute(args):
    import io
    s = io.StringIO()

    sc = import_from_yaml(args.infile)
    simulator = Simulator(sc, PythonEvaluator() if args.python else DummyEvaluator())

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
