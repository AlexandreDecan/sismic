import redbaron
from baron.parser import ParsingError
from mypy import build as mypybuild
from typing import List, Union, cast
from collections import OrderedDict

from sismic.model import Statechart, Transition, StateMixin


PYTHON_EVALUATOR_STUBS = [
    'def send(name: str, **kwargs) -> None: ...',
    'time = ...  # type: float',
    'def active(name: str) -> bool: ...',
    'def after(time: int) -> bool: ...',
    'def idle(time: int) -> bool: ...',
    'from sismic.model import Event\nevent = ...  # type: Event'
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
        raise ValueError(e)
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

"""
import redbaron
line = 'x = 1\nf(1, 2)\nsend("floorSelected", n=4)\nf(send("floorChosen", n=3))'
red = redbaron.RedBaron(line)
red.find_all('AtomTrailersNode', value=lambda v: v.find_all('NameNode', value='send', recursive=False))
"""

"""
from mypy.main import build as mypyb

preprocessor = 'from typing import Callable\ndef send(name: str, **args): pass\ndef f(func: Callable[..., None]): pass\ndef g(a:int, b:int): pass'
line = 'x = 1\ng(1, 2)\nsend("floorSelected", n=4)\nf(send("floorChosen", n=x))'

source = mypyb.BuildSource(None, None, preprocessor + '\n' + line)
result = mypyb.build([source], target=1)

for name, node in result.files['__main__'].names.items():
    print(name, '///', node.type)
"""


"""

- List received events
  - Infer parameter type from transition guard and transition action
- List sent events using RedBaron
  - Infer parameter type from call context
- List contracts
  - Stronger state preconditions can be inferred from incoming transitions (inv + post)
  - State invariants can be inferred from ancestors (inv)
  - Stronger state postconditions can be inferred from outgoing transitions (pre + inv)
  - Weaker transition preconditions can be inferred from source state (post)
  - Weaker transition postconditions can be inferred from target state (pre)
  - Infer context types
- Check contracts:
  - Check if state/transition contracts are compatible (see above for the strength relation)
- Infer contracts:
  - State: Pre + on entry satisfies inv
  - State: inv + on exit satisfies post
  - Transition: pre + guard + action (+ inv) satisfies inv
  - ... need to think about all that stuff

"""