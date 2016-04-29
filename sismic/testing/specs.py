import redbaron  # type: ignore
from baron.parser import ParsingError  # type: ignore

import mypy.build  # type: ignore
from typing import List, Union, Dict, Set

from collections import OrderedDict

from sismic.model import Statechart, Transition, StateMixin


PYTHON_EVALUATOR_STUBS = [
    'def send(name: str, **kwargs) -> None: ...',
    'time = 0.0  # type: float',
    'def active(name: str) -> bool: ...',
    'def after(time: float) -> bool: ...',
    'def idle(time: float) -> bool: ...',
    'class Event:\n'
    '    def __getattr__(self, attr): ...\n'
    'event = Event()',
]


def declared_variables(code: str) -> Dict[str, str]:
    """
    Given a piece of code, return an OrderedDict that associates to each
    declared variable in the code its assigned value.
    While 'a, b = 1, 2' is supported, assignments like 'a, b = range(2)' are not.

    :param code: A piece of Python code
    :return: An ordered dict
    :raise: ValueError if code is malformed
    """
    try:
        red = redbaron.RedBaron(code)
    except ParsingError as e:
        raise ValueError('Invalid Python code in "%s"' % code) from e
    variables = OrderedDict()  # type: OrderedDict[str, str]

    for assignment in red.find_all('AssignmentNode'):
        target, value = assignment.target, assignment.value
        if target.type == 'name':
            # variable = value
            variables.setdefault(target.dumps(), value.dumps())
        elif target.type == 'tuple':
            if value.type == 'tuple':
                # v1, v2, ... = val1, val2, ...
                for var, val in zip(target, value):
                    variables.setdefault(var.dumps(), val.dumps())
            else:
                # v1, v2 = iterable
                for var in target:
                    variables.setdefault(var.dumps(), None)
    return variables


def code_for(statechart: Statechart, element: Union[Statechart, Transition, StateMixin]) -> List[str]:
    """
    Return a list of codes for given element in given statechart.
    The list is composed of every piece of code that should be executed when
    reaching a given element (either a statechart, a state or a transition).

    :param statechart: Statechart to consider
    :param element: Either a statechart, a state or a transition
    :return: A list of codes
    """
    if isinstance(element, Statechart):
        preamble = element.preamble if element.preamble else ''
        return [preamble]
    elif isinstance(element, Transition):
        action = element.action if element.action else ''
        return code_for(statechart, statechart.state_for(element.source)) + [action]
    elif isinstance(element, StateMixin):
        on_entry = getattr(element, 'on_entry', None)  # Can also exists with None
        on_entry = on_entry if on_entry else ''
        parent = statechart.parent_for(element.name)
        if parent is None:
            return code_for(statechart, statechart) + [on_entry]
        else:
            return code_for(statechart, statechart.state_for(parent)) + [on_entry]
    else:
        raise ValueError('Unsupported type %s for %s' % (type(element), element))


def infer_types(code: str) -> Dict[str, str]:
    """
    Return a mapping between variables and their inferred type (using mypy).

    :param code: A piece of code
    :return: Mapping between variables and types (as str)
    :raise: ValueError if code is malformed or if unable to infer something
    """
    source = mypy.build.BuildSource(None, None, code)
    try:
        result = mypy.build.build([source], target=1)
    except mypy.build.CompileError as e:
        raise ValueError('%s\nin: \n%s' % ('\n'.join(e.messages), code)) from e

    return {var: str(val.type) for var, val in result.files['__main__'].names.items()}


def infer_types_for(statechart: Statechart, element: Union[Statechart, Transition, StateMixin]) -> Dict[str, str]:
    codes = [''] + code_for(statechart, element)

    i = len(codes) - 1

    while i >= 1:
        limited_code = '\n'.join(codes[i:])
        try:
            types = infer_types(limited_code)

            # Remove variables from parent
            returned_types = dict()
            variables = declared_variables(codes[-1])
            parent_variables = declared_variables('\n'.join(codes[:-1]))
            for key in variables:
                if key not in parent_variables:
                    returned_types[key] = types[key]

            return returned_types
        except ValueError:
            i -= 1
    return None


def attributes_for(code: str, obj_name: str) -> Set[str]:
    """
    Find and return every attribute that is accessed on given object name.

    :param code: a piece of Python code
    :param obj_name: the name of the object to look for.
    :return: A list of accessed attributes
    """
    try:
        red = redbaron.RedBaron(code)
    except ParsingError as e:
        raise ValueError('Invalid Python code in "%s"' % code) from e

    attributes = set()
    for node in red.find_all('Atomtrailers', lambda n: n.name.value == obj_name):
        attributes.add(node[1].value)
    return attributes


def sent_events(code: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Try to identify calls to *send* in given piece of Python code and return
    a list of identified events, with parameters and values.

    Example: "send('floorSelected', floor=4)" will return
    {'floorSelected': [{'floor': '4'}]}.

    Example: "send('a', x=1), send('a', y=2)" will return
    {'a': [{'x': '1'}, {'y': '2'}]}

    :param code: A piece of Python code
    :return: A mapping {event_name: [{param: value}]}
    :raise: ValueError if code is malformed
    """
    try:
        red = redbaron.RedBaron(code)
    except ParsingError as e:
        raise ValueError('Invalid Python code in "%s"' % code) from e

    events = {}  # type: Dict[str, List[Dict[str, str]]]
    for call_node in red.find_all('Call', lambda n: n.previous.type == 'name' and n.previous.value == 'send'):
        event_name_node = call_node.find('CallArgument', lambda n: n.target is None and n.value.type == 'string')
        if event_name_node is None:
            continue
        event_name = event_name_node.value.value[1:-1]

        event_arguments = {}

        argument_nodes = call_node.find_all('CallArgument', lambda n: n.target is not None)
        for argument_node in argument_nodes:
            event_arguments[argument_node.name.value] = argument_node.value.value

        events.setdefault(event_name, []).append(event_arguments)
    return events


# Infer parameters type of sent events (infer "floor = 4" in current potential context)