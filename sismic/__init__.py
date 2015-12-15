# "Export" most used elements
from . import evaluator, io, model, interpreter, checker


__description__ = 'Sismic Interactive State Machine Interpreter and Checker'
__version__ = '0.8.1'
__url__ = 'https://github.com/AlexandreDecan/sismic/'
__author__ = 'Alexandre Decan'
__email__ = 'alexandre.decan@lexpage.net'
__licence__ = 'LGPL3'


def _parse_args():  # pragma: no cover
    from .cli import cli_execute, cli_validate, cli_test
    import argparse

    description = '{d} v{v} (by {a} -- {u})'.format(d=__description__, v=__version__, a=__author__, u=__url__)

    parser = argparse.ArgumentParser(prog='sismic', description=description)
    subparsers = parser.add_subparsers(title='subcommands', dest='subcommand')
    execute_parser = subparsers.add_parser('execute', help='execute a statechart')
    execute_parser.add_argument('infile',
                                type=argparse.FileType('r'),
                                help='A YAML file describing a statechart')
    execute_parser.add_argument('-v', '--verbosity',
                                help='set output verbosity: -v displays transitions, -vv displays events and configurations, and -vvv displays states',
                                default=0,
                                action='count')
    execute_parser.add_argument('--no-code',
                                action='store_true',
                                dest='nocode',
                                help='Ignore code to be evaluated and executed in the statechart')
    execute_parser.add_argument('-l', '--limit',
                                dest='maxsteps',
                                type=int,
                                help='limit the number of steps to given number, to prevent infinite loops',
                                default=-1)
    execute_parser.add_argument('--events',
                                help='send events to the statechart simulation, eg. name[:key=value[:key=value]]',
                                nargs='*',
                                metavar='EVENT',
                                default=[])

    validate_parser = subparsers.add_parser('validate', help='validate a statechart')
    validate_parser.add_argument('infile',
                                 type=argparse.FileType('r'),
                                 help='A YAML file describing a statechart')

    test_parser = subparsers.add_parser('test', help='test a statechart')
    test_parser.add_argument('infile',
                             type=argparse.FileType('r'),
                             help='A YAML file describing a statechart')
    test_parser.add_argument('--tests',
                             type=argparse.FileType('r'),
                             nargs='+',
                             required=True,
                             help='YAML file describing a statechart tester')
    test_parser.add_argument('--no-code',
                             action='store_true',
                             dest='nocode',
                             help='Ignore code to be evaluated and executed in the statechart')
    test_parser.add_argument('-l', '--limit',
                             dest='maxsteps',
                             type=int,
                             help='limit the number of steps to given number, to prevent infinite loops',
                             default=-1)
    test_parser.add_argument('--events',
                             help='send events to the statechart simulation, eg. name[:key=value[:key=value]]',
                             nargs='*',
                             metavar='EVENT',
                             default=[])

    args = parser.parse_args()

    if args.subcommand == 'execute':
        print(cli_execute(args))
    elif args.subcommand == 'validate':
        print(cli_validate(args))
    elif args.subcommand == 'test':
        print(cli_test(args))
    else:
        parser.print_help()