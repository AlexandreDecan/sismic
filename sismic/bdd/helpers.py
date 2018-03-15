from behave import given, when, then
from typing import Union, List


__all__ = ['map_action', 'map_assertion']


def map_action(new_step: str, existing_step_or_steps: Union[str, List]) -> None:
    """
    Map a new given/when step to one of many existing one(s).
    Parameters are propagated to the original step as well.
    You can provide more than on "step_to_execute" if you want to alias several steps by a single one.

    Examples:

     - map_action('I open door', 'I send event open_door')
     - map_action('Event {name} has to be sent', 'I send event {name}')
     - map_action('I do two things', ['First thing to do', 'Second thing to do'])

    :param new_step: New step, without the "given" or "when" keyword.
    :param existing_step_or_steps: existing step, without the "given" or "when" keyword. Could be a list of steps.
    """
    if not isinstance(existing_step_or_steps, str):
        existing_step_or_steps = '\nand '.join(existing_step_or_steps)

    @given(new_step)
    def _(context, **kwargs):
        context.execute_steps('Given ' + existing_step_or_steps.format(**kwargs))

    @when(new_step)
    def _(context, **kwargs):
        context.execute_steps('When ' + existing_step_or_steps.format(**kwargs))


def map_assertion(new_step: str, existing_step_or_steps: Union[str, List]) -> None:
    """
    Map a new "then" step to one of many existing one(s).
    Parameters are propagated to the original step as well.
    You can provide more than on "step_to_execute" if you want to alias several steps by a single one.

    map_assertion('door is open', 'state door open is active')
    map_assertion('{x} seconds elapsed', 'I wait for {x} seconds')
    map_assertion('assert two things', ['first thing to assert', 'second thing to assert'])

    :param new_step: New step, without the "then" keyword
    :param existing_step_or_steps: existing step, without "then" keyword. Could be a list of steps.
    """
    if not isinstance(existing_step_or_steps, str):
        existing_step_or_steps = '\nand '.join(existing_step_or_steps)

    @then(new_step)
    def _(context, **kwargs):
        context.execute_steps('Then ' + existing_step_or_steps.format(**kwargs))

