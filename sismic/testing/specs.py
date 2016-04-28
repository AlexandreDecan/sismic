import redbaron
from baron.parser import ParsingError

from mypy import build as mypybuild
from typing import List, Union, Dict

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


def declared_variables(code: str) -> OrderedDict:
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
    variables = OrderedDict()

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
        return [element.preamble]
    elif isinstance(element, Transition):
        return code_for(statechart, statechart.state_for(element.source)) + [element.action]
    elif isinstance(element, StateMixin):
        on_entry = getattr(element, 'on_entry', None)
        parent = statechart.parent_for(element.name)
        if parent is None:
            return code_for(statechart, statechart) + [on_entry] if on_entry else code_for(statechart, statechart)
        else:
            return code_for(statechart, statechart.state_for(parent)) + [on_entry] if on_entry \
                else code_for(statechart, statechart.state_for(parent))
    else:
        raise ValueError('Unsupported type %s for %s' % (type(element), element))


def infer_types(code: str) -> Dict[str, str]:
    """
    Return a mapping between variables and their inferred type (using mypy).

    :param code: A piece of code
    :return: Mapping between variables and types (as str)
    :raise: ValueError if code is malformed or if unable to infer something
    """
    source = mypybuild.BuildSource(None, None, code)
    try:
        result = mypybuild.build([source], target=1)
    except mypybuild.CompileError as e:
        raise ValueError('Invalid Python code in "%s"' % code) from e

    return {var: str(val.type) for var, val in result.files['__main__'].names.items()}


if __name__ == '__main__':
    from sismic.io import import_from_yaml

    with open('../../docs/examples/elevator.yaml') as f:
        sc = import_from_yaml(f)

    code_lines = code_for(sc, sc.transitions_from('floorSelecting')[0])
    default_types = infer_types('\n'.join(PYTHON_EVALUATOR_STUBS))
    inferred_types = infer_types('\n'.join(PYTHON_EVALUATOR_STUBS + code_lines))

    for k, v in inferred_types.items():
        if k not in default_types:
            print(k, '->', v)


# Infer sent events
# Infer parameters of received events
# Infer parameters of sent events