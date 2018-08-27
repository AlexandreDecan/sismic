import os
import shutil
import tempfile

from typing import Union, List, Callable
from behave import given, when, then
from behave.__main__ import run_behave
from behave.configuration import Configuration

from ..interpreter import Interpreter
from ..model import Statechart


__all__ = ['map_action', 'map_assertion', 'execute_bdd']


def map_action(step_text: str, existing_step_or_steps: Union[str, List[str]]) -> None:
    """
    Map new "given"/"when" steps to one or many existing one(s).
    Parameters are propagated to the original step(s) as well, as expected.

    Examples:

     - map_action('I open door', 'I send event open_door')
     - map_action('Event {name} has to be sent', 'I send event {name}')
     - map_action('I do two things', ['First thing to do', 'Second thing to do'])

    :param step_text: Text of the new step, without the "given" or "when" keyword.
    :param existing_step_or_steps: existing step, without the "given" or "when" keyword. Could be a list of steps.
    """
    if not isinstance(existing_step_or_steps, str):
        existing_step_or_steps = '\nand '.join(existing_step_or_steps)

    @given(step_text)
    def _(context, **kwargs):
        context.execute_steps('Given ' + existing_step_or_steps.format(**kwargs))

    @when(step_text)
    def _(context, **kwargs):
        context.execute_steps('When ' + existing_step_or_steps.format(**kwargs))


def map_assertion(step_text: str, existing_step_or_steps: Union[str, List[str]]) -> None:
    """
    Map a new "then" step to one or many existing one(s).
    Parameters are propagated to the original step(s) as well, as expected.

    map_assertion('door is open', 'state door open is active')
    map_assertion('{x} seconds elapsed', 'I wait for {x} seconds')
    map_assertion('assert two things', ['first thing to assert', 'second thing to assert'])

    :param step_text: Text of the new step, without the "then" keyword.
    :param existing_step_or_steps: existing step, without "then" keyword. Could be a list of steps.
    """
    if not isinstance(existing_step_or_steps, str):
        existing_step_or_steps = '\nand '.join(existing_step_or_steps)

    @then(step_text)
    def _(context, **kwargs):
        context.execute_steps('Then ' + existing_step_or_steps.format(**kwargs))


def execute_bdd(statechart: Statechart,
                feature_filepaths: List[str],
                *,
                step_filepaths: List[str]=None,
                property_statecharts: List[Statechart]=None,
                interpreter_klass: Callable[[Statechart], Interpreter]=Interpreter,
                debug_on_error: bool=False,
                behave_parameters: List[str]=None) -> int:
    """
    Execute BDD tests for a statechart.

    :param statechart: statechart to test
    :param feature_filepaths: list of filepaths to feature files.
    :param step_filepaths: list of filepaths to step definitions.
    :param property_statecharts: list of property statecharts
    :param interpreter_klass: a callable that accepts a statechart and an optional clock and returns an Interpreter
    :param debug_on_error: set to True to drop to (i)pdb in case of error.
    :param behave_parameters: additional CLI parameters used by Behave (see http://behave.readthedocs.io/en/latest/behave.html#command-line-arguments)
    :return: exit code of behave CLI.
    """
    # Default values
    step_filepaths = step_filepaths if step_filepaths else []
    property_statecharts = property_statecharts if property_statecharts else []
    behave_parameters = behave_parameters if behave_parameters else []

    # If debug_on_error, disable captured stdout, otherwise it hangs
    if debug_on_error and '--capture' not in behave_parameters:
        behave_parameters.append('--no-capture')

    # Create temporary directory to put everything inside
    with tempfile.TemporaryDirectory() as tempdir:
        # Create configuration for Behave
        config = Configuration(behave_parameters)

        # Paths to features
        config.paths = feature_filepaths

        # Copy environment
        with open(os.path.join(tempdir, 'environment.py'), 'w') as environment:
            environment.write('from sismic.bdd.environment import *')

        # Path to environment
        config.environment_file = os.path.join(tempdir, 'environment.py')

        # Add predefined steps
        os.mkdir(os.path.join(tempdir, 'steps'))
        with open(os.path.join(tempdir, 'steps', '__steps.py'), 'w') as step:
            step.write('from sismic.bdd.steps import *')

        # Copy provided steps, if any
        for step_filepath in step_filepaths:
            shutil.copy(step_filepath, os.path.join(tempdir, 'steps', os.path.split(step_filepath)[-1]))

        # Path to steps
        config.steps_dir = os.path.join(tempdir, 'steps')

        # Put statechart and properties in user data
        config.update_userdata({
            'statechart': statechart,
            'interpreter_klass': interpreter_klass,
            'property_statecharts': property_statecharts,
            'debug_on_error': debug_on_error,
        })

        # Run behave
        return run_behave(config)
