import tempfile
import shutil
import os
import sys
import argparse
from behave import __main__ as behave_main  # type: ignore

DEFAULT_STEPS_CONTENT = """
from sismic.testing.steps import *
"""

DEFAULT_ENVIRONMENT_CONTENT = """
from behave.model import Step

def before_scenario(context, scenario):
    context.execute_steps('Given I import a statechart from {{path}}')
"""

COVERAGE_ENVIRONMENT_CONTENT = """
from itertools import chain
from collections import Counter


def states_coverage(states, entered):
    entered_stats = Counter(entered)
    coverage_stat = len(entered_stats.keys()) / len(states)

    print('State coverage: {:.2%}'.format(coverage_stat))
    print('Entered states:', ' | '.join(('{} ({})'.format(k, v) for k, v in entered_stats.most_common())))
    print('Remaining states:', ' | '.join((str(s) for s in sorted(set(states).difference(entered_stats.keys())))))


def transitions_coverage(transitions, processed):
    processed_stats = Counter(processed)
    coverage_stat = len(processed_stats.keys()) / len(transitions)

    print('Transition coverage: {:.2%}'.format(coverage_stat))
    print('Processed transitions:', ' | '.join(('{} ({})'.format(k, v) for k, v in processed_stats.most_common())))


def after_scenario(context, scenario):
    trace = context._steps
    context._traces.append(trace)

    print()
    states_coverage(context._interpreter.statechart.states,
                    chain.from_iterable([step.entered_states for step in trace]))
    transitions_coverage(context._interpreter.statechart.transitions,
                         chain.from_iterable(([step.transitions for step in trace])))
    print()


def before_feature(context, feature):
    context._traces = []


def after_feature(context, feature):
    trace = list(chain.from_iterable(context._traces))
    print()
    print('Aggregated coverage data')
    print('------------------------')
    states_coverage(context._interpreter.statechart.states,
                    chain.from_iterable([step.entered_states for step in trace]))
    transitions_coverage(context._interpreter.statechart.transitions,
                         chain.from_iterable(([step.transitions for step in trace])))
    print()
"""


def execute_behave(statechart, features, steps, coverage, parameters) -> None:
    # Create temporary directory
    with tempfile.TemporaryDirectory() as tempdir:
        # Move statechart inside
        _, statechart_filename = os.path.split(statechart)
        shutil.copy(statechart, os.path.join(tempdir, statechart_filename))

        # Move features inside
        for feature in features:
            _, feature_filename = os.path.split(feature)
            shutil.copy(feature, os.path.join(tempdir, feature_filename))

        # Create an environment file
        with open(os.path.join(tempdir, 'environment.py'), 'w') as environment:
            content = DEFAULT_ENVIRONMENT_CONTENT
            if coverage:
                content += COVERAGE_ENVIRONMENT_CONTENT
            environment.write(content.replace('{{path}}', os.path.join(tempdir, statechart_filename)))

        # Create a steps subdirectory
        os.mkdir(os.path.join(tempdir, 'steps'))

        # Create steps file
        with open(os.path.join(tempdir, 'steps', '__steps.py'), 'w') as step:
            step.write(DEFAULT_STEPS_CONTENT)

        # Copy steps files
        for step in steps if steps else []:
            _, filename = os.path.split(step)
            shutil.copy(step, os.path.join(tempdir, 'steps', filename))

        # Execute behave
        # subprocess.call(['behave'] + parameters, cwd=tempdir)
        cwd = os.getcwd()
        os.chdir(tempdir)
        exit_code = behave_main.main(parameters)
        os.chdir(cwd)
        return exit_code


def main() -> None:
    parser = argparse.ArgumentParser(prog='sismic-behave',
                                     description='Command-line utility to execute Gherkin feature files using Behave.\n'
                                                 'Additional parameters will be passed to Behave.')

    parser.add_argument('statechart', metavar='statechart', type=str,
                        help='A YAML file describing a statechart')
    parser.add_argument('--features', metavar='features', nargs='+', type=str, required=True,
                        help='A list of files containing features')
    parser.add_argument('--steps', metavar='steps', nargs='+', type=str,
                        help='A list of files containing steps implementation')
    parser.add_argument('--coverage', action='store_true', default=False,
                        help='Display coverage data')
    parser.add_argument('--show-steps', action='store_true', default=False,
                        help='Display a list of available steps (equivalent to Behave\'s --steps parameter')

    args, parameters = parser.parse_known_args()
    if args.show_steps:
        parameters.append('--steps')
    return execute_behave(args.statechart, args.features, args.steps, args.coverage, parameters)


if __name__ == '__main__':
    sys.exit(main())
