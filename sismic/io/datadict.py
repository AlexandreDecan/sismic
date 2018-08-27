from collections import OrderedDict
from typing import Any, List, Mapping, MutableMapping, Optional, Tuple, cast

from ..exceptions import StatechartError
from ..model import (ActionStateMixin, BasicState, CompositeStateMixin,
                     CompoundState, DeepHistoryState, FinalState,
                     OrthogonalState, ShallowHistoryState, Statechart,
                     StateMixin, Transition, TransitionStateMixin)

__all__ = ['import_from_dict', 'export_to_dict']


def import_from_dict(data: Mapping[str, Any]) -> Statechart:
    data = data['statechart']

    statechart = Statechart(name=data['name'],
                            description=data.get('description', None),
                            preamble=data.get('preamble', None))

    states = []  # (StateMixin instance, parent name)
    transitions = []  # Transition instances
    # (State dict, parent name)
    data_to_consider = [(data['root state'], None)]  # type: List[Tuple[Mapping[str, Any], Optional[str]]]

    while data_to_consider:
        state_data, parent_name = data_to_consider.pop()

        # Get state
        try:
            state = _import_state_from_dict(state_data)
        except StatechartError:
            raise
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
                transition = _import_transition_from_dict(state.name, transition_data)
            except StatechartError:
                raise
            except Exception as e:
                raise StatechartError('Unable to load given YAML') from e
            transitions.append(transition)

    # Register on statechart
    for state, parent in states:
        statechart.add_state(state, parent)
    for transition in transitions:
        statechart.add_transition(transition)

    return statechart


def _import_transition_from_dict(state_name: str, transition_d: Mapping[str, Any]) -> Transition:
    """
    Return a Transition instance from given dict.

    :param state_name: name of the state in which the transition is defined
    :param transition_d: a dictionary containing transition data
    :return: an instance of Transition
    """
    event = transition_d.get('event', None)
    guard = transition_d.get('guard', None)
    action = transition_d.get('action', None)
    priority = transition_d.get('priority', None)

    if priority == 'low':
        priority = Transition.LOW_PRIORITY
    elif priority == 'high':
        priority = Transition.HIGH_PRIORITY

    transition = Transition(
        state_name,
        transition_d.get('target', None),
        event.strip() if event else None,
        guard.strip() if guard else None,
        action.strip() if action else None,
        priority,
    )

    # Preconditions, postconditions and invariants
    for condition in transition_d.get('contract', []):
        if condition.get('before', None):
            transition.preconditions.append(condition['before'].strip())
        elif condition.get('after', None):
            transition.postconditions.append(condition['after'].strip())
        elif condition.get('always', None):
            transition.invariants.append(condition['always'].strip())

    return transition


def _import_state_from_dict(state_d: Mapping[str, Any]) -> StateMixin:
    """
    Return the appropriate type of state from given dict.

    :param state_d: a dictionary containing state data
    :return: a specialized instance of State
    """
    name = state_d['name']  # type: str
    stype = state_d.get('type', None)

    on_entry = state_d.get('on entry', None)  # type: Optional[str]
    on_entry = on_entry.strip() if on_entry else None
    on_exit = state_d.get('on exit', None)  # type: Optional[str]
    on_exit = on_exit.strip() if on_exit else None

    state = None  # type: Any

    if stype == 'final':
        state = FinalState(name, on_entry=on_entry, on_exit=on_exit)
    elif stype == 'shallow history':
        state = ShallowHistoryState(name, on_entry=on_entry, on_exit=on_exit, memory=state_d.get('memory', None))
    elif stype == 'deep history':
        state = DeepHistoryState(name, on_entry=on_entry, on_exit=on_exit, memory=state_d.get('memory', None))
    elif stype is None:
        substates = state_d.get('states', None)
        parallel_substates = state_d.get('parallel states', None)

        if substates and parallel_substates:
            raise StatechartError('{} cannot declare both a "states" and a "parallel states" property'.format(name))
        elif substates:
            state = CompoundState(name, initial=state_d.get('initial', None), on_entry=on_entry, on_exit=on_exit)
        elif parallel_substates:
            state = OrthogonalState(name, on_entry=on_entry, on_exit=on_exit)
        else:
            state = BasicState(name, on_entry=on_entry, on_exit=on_exit)
    else:
        raise StatechartError('Unknown type {} for state {}'.format(stype, name))

    # Preconditions, postconditions and invariants
    for condition in state_d.get('contract', []):
        if condition.get('before', None):
            state.preconditions.append(condition['before'].strip())
        elif condition.get('after', None):
            state.postconditions.append(condition['after'].strip())
        elif condition.get('always', None):
            state.invariants.append(condition['always'].strip())
    return state


def export_to_dict(statechart: Statechart, ordered=True) -> Mapping[str, Any]:
    """
    Export given StateChart instance to a dict.

    :param statechart: a StateChart instance
    :param ordered: set to True to use an ordereddict instead of a dict
    :return: a dict that can be used in *_import_from_dict*
    """
    d = OrderedDict() if ordered else {}  # type: MutableMapping
    d['name'] = statechart.name
    if statechart.description:
        d['description'] = statechart.description
    if statechart.preamble:
        d['preamble'] = statechart.preamble

    d['root state'] = _export_state_to_dict(statechart, statechart.root, ordered)

    return {'statechart': d}


def _export_state_to_dict(statechart: Statechart, state_name: str, ordered=True) -> Mapping[str, Any]:
    data = OrderedDict() if ordered else {}

    state = statechart.state_for(state_name)

    data['name'] = state.name
    if isinstance(state, ShallowHistoryState):
        data['type'] = 'shallow history'
        if state.memory:
            data['memory'] = state.memory
    elif isinstance(state, DeepHistoryState):
        data['type'] = 'deep history'
        if state.memory:
            data['memory'] = state.memory
    elif isinstance(state, FinalState):
        data['type'] = 'final'

    if isinstance(state, ActionStateMixin):
        if state.on_entry:
            data['on entry'] = state.on_entry
        if state.on_exit:
            data['on exit'] = state.on_exit

    if isinstance(state, CompoundState):
        if state.initial:
            data['initial'] = state.initial

    preconditions = getattr(state, 'preconditions', [])
    postconditions = getattr(state, 'postconditions', [])
    invariants = getattr(state, 'invariants', [])
    if preconditions or postconditions or invariants:
        conditions = []
        for condition in preconditions:
            conditions.append({'before': condition})
        for condition in postconditions:
            conditions.append({'after': condition})
        for condition in invariants:
            conditions.append({'always': condition})
        data['contract'] = conditions

    if isinstance(state, TransitionStateMixin):
        # event, guard, target, action
        transitions = statechart.transitions_from(cast(StateMixin, state).name)
        if len(transitions) > 0:
            data['transitions'] = []

            for transition in transitions:
                transition_data = OrderedDict() if ordered else {}
                if transition.event:
                    transition_data['event'] = transition.event
                if transition.guard:
                    transition_data['guard'] = transition.guard
                if transition.target:
                    transition_data['target'] = transition.target
                if transition.action:
                    transition_data['action'] = transition.action
                if transition.priority != Transition.DEFAULT_PRIORITY:
                    if transition.priority == Transition.LOW_PRIORITY:
                        priority = 'low'
                    elif transition.priority == Transition.HIGH_PRIORITY:
                        priority = 'high'
                    else:
                        priority = transition.priority
                    transition_data['priority'] = priority

                preconditions = getattr(transition, 'preconditions', [])
                postconditions = getattr(transition, 'postconditions', [])
                invariants = getattr(transition, 'invariants', [])
                if preconditions or postconditions or invariants:
                    conditions = []
                    for condition in preconditions:
                        conditions.append({'before': condition})
                    for condition in postconditions:
                        conditions.append({'after': condition})
                    for condition in invariants:
                        conditions.append({'always': condition})
                    transition_data['contract'] = conditions

                data['transitions'].append(transition_data)

    if isinstance(state, CompositeStateMixin):
        children = statechart.children_for(cast(StateMixin, state).name)
        children_data = [_export_state_to_dict(statechart, child, ordered) for child in children]

        if isinstance(state, CompoundState):
            data['states'] = children_data
        elif isinstance(state, OrthogonalState):
            data['parallel states'] = children_data

    return data