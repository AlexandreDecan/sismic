from .model import Event
from .simulator import MicroStep, Simulator
from .evaluator import DummyEvaluator, PythonEvaluator
from .io import import_from_yaml


__description__ = 'Python Statechart Simulator'
__version__ = '0.1.0'
__url__ = 'https://github.com/AlexandreDecan/PySS/'
__author__ = 'Alexandre Decan'
__email__ = 'alexandre.decan@lexpage.net'
__licence__ = 'LGPL3'


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('infile',
                        type=argparse.FileType('r'),
                        help='A YAML file describing a statechart')
    parser.add_argument('--evaluator',
                        default='dummy',
                        help='Evaluator to use for code',
                        choices=['python', 'dummy'])
    parser.add_argument('-v',
                        help='Level of details, -v shows configurations, -vv shows events, -vvv shows transitions',
                        default=0,
                        action='count')
    parser.add_argument('--events',
                        help='A list of event names',
                        nargs='*',
                        default=[])

    args = parser.parse_args()

    sc = import_from_yaml(args.infile)
    evaluator = PythonEvaluator() if args.evaluator == 'python' else DummyEvaluator()
    simulator = Simulator(sc, evaluator)
    simulator.start()

    if args.v >= 1:
        print('Initial configuration: ' + str(simulator.configuration))

    for event in args.events:
        event = Event(event)
        simulator.send(event)
        if args.v >= 2:
            print('Event sent: ' + str(event))

    for step in simulator:
        if args.v >= 1:
            print('-- ', end='')
        if args.v >= 2:
            print('Event consumed: ' + str(step.event))
        if args.v >= 3:
            print('Transition: ' + str(step.transition))
        if args.v >= 1:
            print('Configuration: ' + str(simulator.configuration))

    print('Final: {}'.format(not simulator.running))

