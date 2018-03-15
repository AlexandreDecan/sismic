import argparse
import os
import shutil
import sys
import tempfile

from behave import __main__ as behave_main  # type: ignore
from typing import List

__all__ = ['execute_behave']


def main() -> int:
    parser = argparse.ArgumentParser(prog='sismic-bdd',
                                     description='Command-line utility to execute Gherkin feature files using Behave.\n'
                                                 'Extra parameters will be passed to Behave.')

    parser.add_argument('statechart', metavar='statechart', type=str,
                        help='A YAML file describing a statechart')
    parser.add_argument('--features', metavar='features', nargs='+', type=str, required=True,
                        help='A list of files containing features')
    parser.add_argument('--steps', metavar='steps', nargs='+', type=str,
                        help='A list of files containing steps implementation')
    parser.add_argument('--properties', metavar='properties', nargs='+', type=str,
                        help='A list of filepaths pointing to YAML property statecharts. They will be checked at runtime following a fail fast approach.')
    parser.add_argument('--show-steps', action='store_true', default=False,
                        help='Display a list of available steps (equivalent to Behave\'s --steps parameter')
    parser.add_argument('--debug-on-error', action='store_true', default=False,
                        help='Drop in a debugger in case of step failure (ipdb if available)')

    args, parameters = parser.parse_known_args()
    if args.show_steps:
        parameters.append('--steps')
    return execute_behave(
        args.statechart,
        args.features,
        steps=args.steps,
        properties=args.properties,
        debug_on_error=args.debug_on_error,
        parameters=parameters
    )


def execute_behave(statechart: str, features: List[str], *,
                   steps: List[str]=None,
                   properties: List[str]=None,
                   debug_on_error: bool=False,
                   parameters: List[str]=None) -> int:
    """
    Set an temporary directory to execute Behave with support for Sismic.

    :param statechart: filepath to the statechart (in YAML).
    :param features: list of filepaths to feature files.
    :param steps: list of filepaths to step definitions.
    :param properties: list of filepaths to property statecharts (in YAML).
    :param debug_on_error: set to True to drop to (i)pdb in case of error.
    :param parameters: additional parameters that will be provided to behave CLI.
    :return: exit code of behave CLI.
    """
    # Default values
    steps = steps if steps else []
    properties = properties if properties else []
    parameters = parameters if parameters else []

    # Create temporary directory
    with tempfile.TemporaryDirectory() as tempdir:
        # Move statechart
        _, statechart_filename = os.path.split(statechart)
        shutil.copy(statechart, os.path.join(tempdir, statechart_filename))
        parameters.append('-D statechart={}'.format(statechart_filename))

        # Move features inside
        for feature in features:
            _, feature_filename = os.path.split(feature)
            shutil.copy(feature, os.path.join(tempdir, feature_filename))

        # Move property statecharts
        if properties:
            property_filenames = []
            for property_statechart in properties if properties else []:
                _, property_filename = os.path.split(property_statechart)
                property_filenames.append(property_filename)
                shutil.copy(property_statechart, os.path.join(tempdir, property_filename))
            parameters.append('-D properties={}'.format(';'.join(property_filenames)))

        # Debug on error
        if debug_on_error:
            parameters.append('-D debug_on_error=True')

        # Create environment file
        with open(os.path.join(tempdir, 'environment.py'), 'w') as environment:
            environment.write('from sismic.bdd.environment import *')

        # Create step directory
        os.mkdir(os.path.join(tempdir, 'steps'))

        # Add predefined steps
        with open(os.path.join(tempdir, 'steps', '__steps.py'), 'w') as step:
            step.write('from sismic.bdd.steps import *')

        # Copy provided steps
        for step in steps if steps else []:
            _, step_filename = os.path.split(step)
            shutil.copy(step, os.path.join(tempdir, 'steps', step_filename))

        # Execute behave in this directory
        cwd = os.getcwd()
        os.chdir(tempdir)
        exit_code = behave_main.main(parameters)
        os.chdir(cwd)

        return exit_code


if __name__ == '__main__':
    sys.exit(main())
