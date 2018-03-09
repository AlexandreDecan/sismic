import argparse
import os
import shutil
import sys
import tempfile

from typing import List, Mapping
from behave import __main__ as behave_main  # type: ignore


# IMPORTANT: This file needs to be COMPLETELY refactored. Shame on me!


DEFAULT_STEPS_CONTENT = """
from sismic.testing.steps import *
"""

ENVIRONMENT = {
    'import': [],
    'before_scenario': [],
    'after_scenario': [],
    'before_feature': [],
    'after_feature': [],
    'before_step': [],
    'after_step': [],
    'content': [],
}  # type: Mapping[str, List[str]]


def execute_behave(statechart: str,
                   features: List[str],
                   steps: List[str],
                   properties: List[str],
                   coverage: bool,
                   debug_on_error: bool,
                   parameters: List[str]) -> int:
    # Create temporary directory
    with tempfile.TemporaryDirectory() as tempdir:
        # Move statechart inside
        _, statechart_filename = os.path.split(statechart)
        shutil.copy(statechart, os.path.join(tempdir, statechart_filename))

        # Move features inside
        for feature in features:
            _, feature_filename = os.path.split(feature)
            shutil.copy(feature, os.path.join(tempdir, feature_filename))

        # Move property statecharts inside, if any
        for prop in properties if properties else []:
            _, property_filename = os.path.split(prop)
            shutil.copy(prop, os.path.join(tempdir, property_filename))

        ENVIRONMENT['import'].append('from behave.model import Step')
        ENVIRONMENT['before_scenario'].append(
            "context.execute_steps('Given I import a statechart from {path}')"
            .format(path=os.path.join(tempdir, statechart_filename).replace('\\', '\\\\'))
        )

        if properties:
            for property_sc in properties:
                _, property_filename = os.path.split(property_sc)
                ENVIRONMENT['before_scenario'].append(
                    "context.execute_steps('Given I bind property statechart {path}')"
                    .format(path=os.path.join(tempdir, property_filename).replace('\\', '\\\\'))
                )

        if coverage:
            ENVIRONMENT['import'].append('from itertools import chain')
            ENVIRONMENT['import'].append('from collections import Counter')

            ENVIRONMENT['content'].append("""
def states_coverage(states, entered):
    entered_stats = Counter(entered)
    coverage_stat = len(entered_stats.keys()) / len(states)

    print('State coverage: {:.2%}'.format(coverage_stat))
    print('Entered states:',
          ' | '.join(('{} ({})'.format(k, v) for k, v in entered_stats.most_common())))
    print('Remaining states:',
          ' | '.join((str(s) for s in sorted(set(states).difference(entered_stats.keys())))))

def transitions_coverage(transitions, processed):
    processed_stats = Counter(processed)
    coverage_stat = len(processed_stats.keys()) / len(transitions)

    print('Transition coverage: {:.2%}'.format(coverage_stat))
    print('Processed transitions:', ' | '.join(('{} ({})'.format(k, v) for k, v in processed_stats.most_common())))

""")

            ENVIRONMENT['after_scenario'].extend([
                'trace = context._steps',
                'context._traces.append(trace)',
                'print()',
                'states_coverage(context._interpreter.statechart.states, chain.from_iterable([step.entered_states for step in trace]))',
                'transitions_coverage(context._interpreter.statechart.transitions, chain.from_iterable(([step.transitions for step in trace])))',
                'print()',
            ])

            ENVIRONMENT['before_feature'].append('context._traces = []')

            ENVIRONMENT['after_feature'].extend([
                'trace = list(chain.from_iterable(context._traces))',
                'print()',
                'print("Aggregated coverage data")',
                'print("------------------------")',
                'states_coverage(context._interpreter.statechart.states, chain.from_iterable([step.entered_states for step in trace]))',
                'transitions_coverage(context._interpreter.statechart.transitions, chain.from_iterable(([step.transitions for step in trace])))',
                'print()',
            ])

        if debug_on_error:
            ENVIRONMENT['after_step'].extend([
                'if step.status == "failed":',
                '    try:',
                '        import ipdb',
                '        ipdb.post_mortem(step.exc_traceback)',
                '    except ImportError:',
                '        import pdb',
                '        pdb.post_mortem(step.exc_traceback)',
            ])

        # Create an environment file
        with open(os.path.join(tempdir, 'environment.py'), 'w') as environment:
            environment.write('\n'.join(ENVIRONMENT['import']))
            environment.write('\n')

            environment.write('\n'.join(ENVIRONMENT['content']))
            environment.write('\n')

            for key in ['before_scenario', 'after_scenario', 'before_feature', 'after_feature', 'before_step', 'after_step']:
                content = ENVIRONMENT[key]
                if len(content) > 0:
                    param_name = key.split('_')[-1]
                    environment.write('def {}(context, {}):\n'.format(key, param_name))
                    environment.write('\n'.join(['    ' + line for line in content]))
                    environment.write('\n')

        # Create a steps subdirectory
        os.mkdir(os.path.join(tempdir, 'steps'))

        # Create steps file
        with open(os.path.join(tempdir, 'steps', '__steps.py'), 'w') as f_step:
            f_step.write(DEFAULT_STEPS_CONTENT)

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


def main() -> int:
    parser = argparse.ArgumentParser(prog='sismic-behave',
                                     description='Command-line utility to execute Gherkin feature files using Behave.\n'
                                                 'Additional parameters will be passed to Behave.')

    parser.add_argument('statechart', metavar='statechart', type=str,
                        help='A YAML file describing a statechart')
    parser.add_argument('--features', metavar='features', nargs='+', type=str, required=True,
                        help='A list of files containing features')
    parser.add_argument('--steps', metavar='steps', nargs='+', type=str,
                        help='A list of files containing steps implementation')
    parser.add_argument('--properties', metavar='properties', nargs='+', type=str,
                        help='A list of filepaths pointing to YAML property statecharts. They will be checked at runtime following a fail fast approach.')
    parser.add_argument('--coverage', action='store_true', default=False,
                        help='Display coverage data')
    parser.add_argument('--show-steps', action='store_true', default=False,
                        help='Display a list of available steps (equivalent to Behave\'s --steps parameter')
    parser.add_argument('--debug-on-error', action='store_true', default=False,
                        help='Drop in a debugger in case of step failure (ipdb if available)')

    args, parameters = parser.parse_known_args()
    if args.show_steps:
        parameters.append('--steps')
    return execute_behave(args.statechart, args.features, args.steps, args.properties, args.coverage, args.debug_on_error, parameters)


if __name__ == '__main__':
    sys.exit(main())
