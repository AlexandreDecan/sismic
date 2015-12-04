from .model import Event
from .simulator import MicroStep, Simulator
from .evaluator import DummyEvaluator, PythonEvaluator
from .format import import_from_yaml

__description__ = 'Python Statechart Simulator'
__version__ = '0.2.0'
__url__ = 'https://github.com/AlexandreDecan/PySS/'
__author__ = 'Alexandre Decan'
__email__ = 'alexandre.decan@lexpage.net'
__licence__ = 'LGPL3'


def execute_cli(infile, evaluator, verbosity, events):
    output = []
    sc = import_from_yaml(infile)
    evaluator = PythonEvaluator() if evaluator == 'python' else DummyEvaluator()
    simulator = Simulator(sc, evaluator)
    simulator.start()

    if verbosity >= 1:
        output.append('Initial configuration: ' + str(simulator.configuration) + '\n')

    for event in events:
        event = Event(event)
        simulator.send(event)
        if verbosity >= 2:
            output.append('Event sent: ' + str(event) + '\n')

    for step in simulator:
        if verbosity >= 1:
            output.append('-- ')
        if verbosity >= 2:
            output.append('Event consumed: ' + str(step.event) + '\n')
        if verbosity >= 3:
            output.append('Transition: ' + str(step.transition) + '\n')
        if verbosity >= 1:
            output.append('Configuration: ' + str(simulator.configuration) + '\n')

    output.append('Final: {}'.format(not simulator.running) + '\n')
    return output


def main():  # pragma: no cover
    import argparse
    description = '{d} v{v} by {a}'.format(d=__description__, v=__version__, a=__author__)

    parser = argparse.ArgumentParser(prog='pyss', description=description)
    parser.add_argument('infile',
                        type=argparse.FileType('r'),
                        help='A YAML file describing a statechart')
    parser.add_argument('--evaluator',
                        default='dummy',
                        help='Evaluator to use for code',
                        choices=['python', 'dummy'])
    parser.add_argument('-v',
                        help='Level of details, -v ads configurations, -vv adds events, -vvv adds transitions',
                        default=0,
                        action='count')
    parser.add_argument('--events',
                        help='A list of event names',
                        nargs='*',
                        default=[])

    args = parser.parse_args()
    print(''.join(execute_cli(args.infile, args.evaluator, args.v, args.events)))
