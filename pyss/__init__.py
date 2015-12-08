__description__ = 'Python Statechart Simulator'
__version__ = '0.3.10'
__url__ = 'https://github.com/AlexandreDecan/PySS/'
__author__ = 'Alexandre Decan'
__email__ = 'alexandre.decan@lexpage.net'
__licence__ = 'LGPL3'


# "Export" most used elements
from . import model
from . import simulator
from . import evaluator
from . import io


def _parse_args():  # pragma: no cover
    from .cli import _cli_execute, _cli_validate
    import argparse

    description = '{d} v{v} by {a}'.format(d=__description__, v=__version__, a=__author__)

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
    else:
        parser.print_help()