from behave import given, when, then
from typing import Union, List


__all__ = ['map_action', 'map_assertion']


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

