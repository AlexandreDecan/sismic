import yaml
import os

from pykwalify.core import Core
from sismic.model import Transition, Statechart, BasicState, CompoundState, OrthogonalState, ShallowHistoryState, \
    DeepHistoryState, FinalState, StateMixin
from sismic.exceptions import StatechartError

__all__ = ['import_from_yaml']


SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.yaml')


def import_from_yaml(statechart: str, ignore_schema: bool=False, ignore_validation: bool=False) -> Statechart:
    """
    Import a statechart from a YAML representation.
    YAML is first validated against *io.SCHEMA_PATH*, and resulting statechart is validated
    using its *validate* method.

    :param statechart: string or any equivalent object
    :param ignore_schema: set to *True* to disable yaml validation.
    :param ignore_validation: set to *True* to disable statechart validation.
    :return: a *StateChart* instance
    """
    data = yaml.load(statechart)
    if not ignore_schema:
        checker = Core(source_data=data, schema_files=[SCHEMA_PATH])
        checker.validate(raise_exception=True)

    data = data['statechart']

    statechart = Statechart(name=data['name'],
                            description=data.get('description', None),
                            preamble=data.get('preamble', None))

    states = []  # (StateMixin instance, parent name)
    transitions = []  # Transition instances
    data_to_consider = []  # (State dict, parent name)

    data_to_consider.append((data['initial state'], None))

    while data_to_consider:
        state_data, parent_name = data_to_consider.pop()

        # Get state
        try:
            state = _state_from_dict(state_data)
        except Exception as e:
            raise StatechartError('Unable to load given YAML') from e
        states.append((state, parent_name))

        # Get substates
        if isinstance(state, CompoundState):
            for substate_data in state_data['states']:
                data_to_consider.append((substate_data, state.name))
        elif isinstance(state, OrthogonalState):
            for substate_data in state_data['parallel states']:
                data_to_consider.append((substate_data, state.name))

        # Get transition(s)
        for transition_data in state_data.get('transitions', []):
            try:
                transition = _transition_from_dict(state.name, transition_data)
            except Exception as e:
                raise StatechartError('Unable to load given YAML') from e
            transitions.append(transition)

    # Register on statechart
    for state, parent in states:
        statechart.add_state(state, parent)
    for transition in transitions:
        statechart.add_transition(transition)

    if not ignore_validation:
        statechart.validate()

    return statechart


def _transition_from_dict(state_name: str, transition_d: dict) -> Transition:
    """
    Return a Transition instance from given dict.

    :param state_name: name of the state in which the transition is defined
    :param transition_d: a dictionary containing transition data
    :return: an instance of Transition
    """
    event = transition_d.get('event', None)
    transition = Transition(state_name, transition_d.get('target', None), event,
                            transition_d.get('guard', None), transition_d.get('action', None))

    # Preconditions, postconditions and invariants
    for condition in transition_d.get('contract', []):
        if condition.get('before', None):
            transition.preconditions.append(condition['before'])
        elif condition.get('after', None):
            transition.postconditions.append(condition['after'])
        elif condition.get('always', None):
            transition.invariants.append(condition['always'])

    return transition


def _state_from_dict(state_d: dict) -> StateMixin:
    """
    Return the appropriate type of state from given dict.

    :param state_d: a dictionary containing state data
    :return: a specialized instance of State
    """
    name = state_d.get('name')
    type = state_d.get('type', None)
    on_entry = state_d.get('on entry', None)
    on_exit = state_d.get('on exit', None)

    if type == 'final':
        state = FinalState(name, on_entry=on_entry, on_exit=on_exit)
    elif type == 'shallow history':
        state = ShallowHistoryState(name, on_entry=on_entry, on_exit=on_exit, memory=state_d.get('memory', None))
    elif type == 'deep history':
        state = DeepHistoryState(name, on_entry=on_entry, on_exit=on_exit, memory=state_d.get('memory', None))
    elif type == None:
        substates = state_d.get('states', None)
        parallel_substates = state_d.get('parallel states', None)

        if substates:
            state = CompoundState(name, initial=state_d.get('initial', None), on_entry=on_entry, on_exit=on_exit)
        elif parallel_substates:
            state = OrthogonalState(name, on_entry=on_entry, on_exit=on_exit)
        else:
            state = BasicState(name, on_entry=on_entry, on_exit=on_exit)
    else:
        raise StatechartError('Unknown type {} for state {}'.format(type, name))

    # Preconditions, postconditions and invariants
    for condition in state_d.get('contract', []):
        if condition.get('before', None):
            state.preconditions.append(condition['before'])
        elif condition.get('after', None):
            state.postconditions.append(condition['after'])
        elif condition.get('always', None):
            state.invariants.append(condition['always'])
    return state


'''
def export_to_yaml(statechart: Statechart) -> str:
    """
    Export given StateChart instance to YAML

    :param statechart:
    :return: A textual YAML representation
    """
    return yaml.dump(_export_to_dict(statechart, ordered=False),
                     width=1000, default_flow_style=False, default_style='"')


def _export_to_dict(statechart: Statechart, ordered=True) -> dict:
    """
    Export given StateChart instance to a dict.

    :param statechart: a StateChart instance
    :param ordered: set to True to use OrderedDict instead
    :return: a dict that can be used in ``import_from_dict``
    """
    d = OrderedDict() if ordered else dict()
    d['name'] = statechart.name
    d['initial'] = statechart.initial
    d['states'] = statechart.children
    if statechart.on_entry:
        d['on entry'] = statechart.on_entry

    preconditions = getattr(statechart, 'preconditions', [])
    postconditions = getattr(statechart, 'postconditions', [])
    invariants = getattr(statechart, 'invariants', [])
    if preconditions or postconditions or invariants:
        conditions = []
        for condition in preconditions:
            conditions.append({'before': condition})
        for condition in postconditions:
            conditions.append({'after': condition})
        for condition in invariants:
            conditions.append({'always': condition})
        d['contract'] = conditions

    statelist_to_expand = [d['states']]
    while statelist_to_expand:
        statelist = statelist_to_expand.pop()
        for i, state in enumerate(statelist):
            statelist[i] = _export_element_to_dict(statechart.states[state], ordered)
            new_statelist = statelist[i].get('states', statelist[i].get('parallel states', []))
            if len(new_statelist) > 0:
                statelist_to_expand.append(new_statelist)
    return {'statechart': d}


def _export_element_to_dict(el, ordered=False) -> dict:
    """
    Export an element (State, Transition, etc.) to a dict.
    Is used in ``export_to_dict`` to generate a global representation.

    :param el: an instance of ``model.*``
    :param ordered: set to True to use OrderedDict instead of dict
    :return: a dict
    """
    d = OrderedDict() if ordered else dict()

    if isinstance(el, Transition):
        if not el.internal:
            d['target'] = el.to_state
        if not el.eventless:
            d['event'] = el.event
        if el.guard:
            d['guard'] = el.guard
        if el.action:
            d['action'] = el.action
    if isinstance(el, StateMixin):
        d['name'] = el.name
    if isinstance(el, CompoundState):
        if el.initial:
            d['initial'] = el.initial
    if isinstance(el, ActionStateMixin):
        if el.on_entry:
            d['on entry'] = el.on_entry
        if el.on_exit:
            d['on exit'] = el.on_exit

    preconditions = getattr(el, 'preconditions', [])
    postconditions = getattr(el, 'postconditions', [])
    invariants = getattr(el, 'invariants', [])
    if preconditions or postconditions or invariants:
        conditions = []
        for condition in preconditions:
            conditions.append({'before': condition})
        for condition in postconditions:
            conditions.append({'after': condition})
        for condition in invariants:
            conditions.append({'always': condition})
        d['contract'] = conditions

    if isinstance(el, TransitionStateMixin):
        if len(el.transitions) > 0:
            d['transitions'] = [_export_element_to_dict(t) for t in el.transitions]
    if isinstance(el, CompositeStateMixin):
        if isinstance(el, OrthogonalState):
            d['parallel states'] = el.children
        else:
            d['states'] = el.children
    if isinstance(el, HistoryState):
        if el.deep:
            d['type'] = 'deep history'
        else:
            d['type'] = 'shallow history'
        if el.initial:
            d['initial'] = el.initial
    if isinstance(el, FinalState):
        d['type'] = 'final'
    return d
'''