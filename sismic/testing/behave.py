import tempfile
import shutil
import os
import subprocess
import argparse


DEFAULT_STEPS_CONTENT = """
from sismic.testing.steps import *
"""

DEFAULT_ENVIRONMENT_CONTENT = """
from behave.model import Step
def before_scenario(context, scenario):
  context.execute_steps('Given I import a statechart from {path}')
"""


def execute_behave(statechart, features, parameters):
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
            environment.write(DEFAULT_ENVIRONMENT_CONTENT.format(path=os.path.join(tempdir, statechart_filename)))

        # Create a steps subdirectory
        os.mkdir(os.path.join(tempdir, 'steps'))

        # Create steps file
        with open(os.path.join(tempdir, 'steps', 'steps.py'), 'w') as step:
            step.write(DEFAULT_STEPS_CONTENT)

        # Execute behave
        subprocess.call(['behave'] + parameters, cwd=tempdir)


def main():
    parser = argparse.ArgumentParser(prog='sismic-behave',
                                     description='Command-line utility to execute Gherkin feature files using Behave.\n'
                                                 'Additional parameters will be passed to Behave.')

    parser.add_argument('statechart', metavar='statechart', type=str,
                        help='A YAML file describing a statechart')
    parser.add_argument('--features', metavar='features', nargs='+', type=str,
                        help='A list of files containing features')

    args, parameters = parser.parse_known_args()
    execute_behave(args.statechart, args.features, parameters)


if __name__ == '__main__':
    main()