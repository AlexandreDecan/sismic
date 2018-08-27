from typing import Union, Optional, List, Any, Mapping
from .interpreter import Interpreter
from .model import MacroStep, Transition


__all__ = [
    'state_is_entered', 'state_is_exited',
    'event_is_fired', 'event_is_consumed',
    'transition_is_processed',
    'expression_holds',
]

MacroSteps = Union[MacroStep, List[MacroStep]]


def state_is_entered(steps: MacroSteps, name: str) -> bool:
    """
    Holds if state was entered during given steps.

    :param steps: a macrostep or list of macrosteps
    :param name: name of a state
    :return: given state was entered
    """
    steps = steps if isinstance(steps, list) else [steps]
    for step in steps:
        if name in step.entered_states:
            return True
    return False


def state_is_exited(steps: MacroSteps, name: str) -> bool:
    """
    Holds if state was exited during given steps.

    :param steps: a macrostep or list of macrosteps
    :param name: name of a state
    :return: given state was exited
    """
    steps = steps if isinstance(steps, list) else [steps]
    for step in steps:
        if name in step.exited_states:
            return True
    return False


def event_is_fired(steps: MacroSteps, name: Optional[str], parameters: Mapping[str, Any]=None) -> bool:
    """
    Holds if an event was fired during given steps.

    If name is None, this function looks for any event.
    If parameters are provided, their values are compared with the respective
    attribute of the event. Not *all* parameters have to be provided, as only
    the ones that are provided are actually compared.

    :param steps: a macrostep or list of macrosteps
    :param name: name of an event
    :param parameters: additional parameters
    :return: event was fired
    """
    steps = steps if isinstance(steps, list) else [steps]
    parameters = dict() if parameters is None else parameters

    for step in steps:
        for event in step.sent_events:
            if name is None or event.name == name:
                matching_parameters = True
                for key, value in parameters.items():
                    if getattr(event, key, None) != value:
                        matching_parameters = False
                        break
                if matching_parameters:
                    return True
    return False


def event_is_consumed(steps: MacroSteps, name: Optional[str], parameters: Mapping[str, Any]=None) -> bool:
    """
    Holds if an event was consumed during given steps.

    If name is None, this function looks for any event.
    If parameters are provided, their values are compared with the respective
    attribute of the event. Not *all* parameters have to be provided, as only
    the ones that are provided are actually compared.

    :param steps: a macrostep or list of macrosteps
    :param name: name of an event
    :param parameters: additional parameters
    :return: event was consumed
    """
    steps = steps if isinstance(steps, list) else [steps]
    parameters = dict() if parameters is None else parameters

    for step in steps:
        if step.event is None:
            continue

        if name is None or step.event.name == name:
            matching_parameters = True
            for key, value in parameters.items():
                if getattr(step.event, key, None) != value:
                    matching_parameters = False
                    break
            if matching_parameters:
                return True
    return False


def transition_is_processed(steps: MacroSteps, transition: Optional[Transition]=None) -> bool:
    """
    Holds if a transition was processed during given steps.

    If no transition is provided, this function looks for any transition.

    :param steps: a macrostep or list of macrosteps
    :param transition: a transition
    :return: transition was processed
    """
    steps = steps if isinstance(steps, list) else [steps]

    if transition is None:
        for step in steps:
            if len(step.transitions) > 0:
                return True
        return False
    else:
        for step in steps:
            if transition in step.transitions:
                return True
        return False


def expression_holds(interpreter: Interpreter, expression: str) -> bool:
    """
    Holds if given expression holds.

    :param interpreter: current interpreter
    :param expression: expression to evaluate
    :return: expression holds
    """
    return interpreter._evaluator._evaluate_code(expression)

