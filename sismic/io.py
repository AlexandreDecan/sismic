import yaml
from collections import OrderedDict
from .model import Event, Transition, StateChart, BasicState, CompoundState, OrthogonalState, HistoryState, FinalState
from .model import StateMixin, ActionStateMixin, TransitionStateMixin, CompositeStateMixin


def import_from_yaml(data: str) -> StateChart:
    """
    Import a statechart from a YAML representation.

    :param data: string or any equivalent object
    :return: a StateChart instance
    """
    return import_from_dict(yaml.load(data)['statechart'])


def import_from_dict(data: dict) -> StateChart:
    """
    Import a statechart from a (set of nested) dictionary.

    :param data: dict-like structure
    :return: a StateChart instance
    """
    sc = StateChart(data['name'], data['initial'], data.get('on entry', None))

    # Preconditions, postconditions and invariants
    for condition in data.get('contract', []):
        if condition.get('pre', None):
            sc.preconditions.append(condition['pre'])
        elif condition.get('post', None):
            sc.postconditions.append(condition['post'])
        elif condition.get('inv', None):
            sc.invariants.append(condition['inv'])

    states_to_add = []  # list of (state, parent) to be added
    for state in data['states']:
        states_to_add.append((state, None))

    # Add states
    while states_to_add:
        state_d, parent_name = states_to_add.pop()

        # Create and register state
        try:
            state = _state_from_dict(state_d)
        except Exception as e:
            raise ValueError('An exception occurred while trying to parse:\n {1}\n\nException:\n{0}'.format(e, state_d))
        sc.register_state(state, parent_name)

        # Register transitions if any
        for transition_d in state_d.get('transitions', []):
            try:
                transition = _transition_from_dict(state.name, transition_d)
            except Exception as e:
                raise ValueError('An exception occurred while trying to parse transitions in {2}:\n {1}\n\nException:\n{0}'.format(e, transition_d, state.name))
            sc.register_transition(transition)

        # Register substates
        for substate in state_d.get('states', state_d.get('parallel states', [])):
            states_to_add.append((substate, state.name))

    return sc


def _transition_from_dict(state_name: str, transition_d: dict) -> Transition:
    """
    Return a Transition instance from given dict.

    :param state: name of the state in which the transition is defined
    :param transition_d: a dictionary containing transition data
    :return: an instance of Transition
    """
    event = transition_d.get('event', None)
    if event:
        event = Event(event)
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
    # Guess the type of state
    if state_d.get('type', None) == 'final':
        # Final pseudo state
        name = state_d.get('name')
        on_entry = state_d.get('on entry', None)
        on_exit = state_d.get('on exit', None)
        state = FinalState(name, on_entry, on_exit)
    elif state_d.get('type', None) == 'shallow history':
        # Shallow history pseudo state
        state = HistoryState(state_d['name'], state_d.get('initial'), deep=False)
    elif state_d.get('type', None) == 'deep history':
        # Deep history pseudo state
        state = HistoryState(state_d['name'], state_d.get('initial'), deep=True)
    else:
        name = state_d.get('name')
        on_entry = state_d.get('on entry', None)
        on_exit = state_d.get('on exit', None)
        if 'states' in state_d:  # Compound state
            initial = state_d.get('initial', None)
            state = CompoundState(name, initial, on_entry, on_exit)
        elif 'parallel states' in state_d:  # Orthogonal state
            state = OrthogonalState(name, on_entry, on_exit)
        else:
            # Simple state
            state = BasicState(name, on_entry, on_exit)

    # Preconditions, postconditions and invariants
    for condition in state_d.get('contract', []):
        if condition.get('before', None):
            state.preconditions.append(condition['before'])
        elif condition.get('after', None):
            state.postconditions.append(condition['after'])
        elif condition.get('always', None):
            state.invariants.append(condition['always'])
    return state


def export_to_yaml(statechart: StateChart) -> str:
    """
    Export given StateChart instance to YAML

    :param statechart:
    :return: A textual YAML representation
    """
    return yaml.dump(export_to_dict(statechart, ordered=False),
                     width=1000, default_flow_style=False, default_style='"')


def export_to_dict(statechart: StateChart, ordered=True) -> dict:
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
            d['event'] = el.event.name
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
