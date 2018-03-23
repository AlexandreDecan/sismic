import argparse
import sys

from ..io import import_from_yaml
from .wrappers import execute_bdd


def cli(args=None) -> int:
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

    args, parameters = parser.parse_known_args(args)
    if args.show_steps:
        parameters.append('--steps')

    statechart = import_from_yaml(filepath=args.statechart)

    property_statecharts = []
    for property_statechart in args.properties or []:
        property_statecharts.append(import_from_yaml(filepath=property_statechart))

    return execute_bdd(
        statechart,
        args.features,
        step_filepaths=args.steps,
        property_statecharts=property_statecharts,
        debug_on_error=args.debug_on_error,
        behave_parameters=parameters
    )


if __name__ == '__main__':
    sys.exit(cli())