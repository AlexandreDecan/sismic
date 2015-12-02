import yaml
from collections import OrderedDict
from pyss.statemachine import Event, Transition, StateMachine, BasicState, CompoundState, OrthogonalState, HistoryState, FinalState
from pyss.statemachine import StateMixin, ActionStateMixin, TransitionStateMixin, CompositeStateMixin


def import_from_yaml(data) -> StateMachine:
    """
    Import a state machine from a YAML representation.
    :param data: string or any equivalent object
    :return: a StateMachine instance
    """
    return import_from_dict(yaml.load(data)['statemachine'])


def import_from_dict(data: dict) -> StateMachine:
    """
    Import a state machine from a (set of nested) dictionary.
    :param data: dict-like structure
    :return: a StateMachine instance
    """
    sm = StateMachine(data['name'], data['initial'], data.get('on entry', None))

    states_to_add = []  # list of (state, parent) to be added
    for state in data['states']:
        states_to_add.append((state, None))

    # Add states
    while states_to_add:
        state_d, parent_name = states_to_add.pop()

        # Create and register state
        # TODO: Catch exception and provide details about the "parsing" error
        state = _state_from_dict(state_d)
        sm.register_state(state, parent_name)

        # Register transitions if any
        for transition_d in state_d.get('transitions', []):
            # TODO: Catch exception and provide details about the "parsing" error
            transition = _transition_from_dict(state.name, transition_d)
            sm.register_transition(transition)

        # Register substates
        for substate in state_d.get('states', []):
            states_to_add.append((substate, state.name))

    return sm


def _transition_from_dict(state_name: str, transition_d: dict) -> Transition:
    """
    Return a Transition instance from given dict.
    :param state: name of the state in which the transition is defined
    :param transition_d: a dictionary containing transition data
    :return: an instance of Transition
    """
    to_state = transition_d.get('target', None)
    event = transition_d.get('event', None)
    if event:
        event = Event(event)
    condition = transition_d.get('guard', None)
    action = transition_d.get('action', None)
    return Transition(state_name, to_state, event, condition, action)


def _state_from_dict(state_d: dict) -> StateMixin:
    """
    Return the appropriate type of state from given dict.
    :param state_d: a dictionary containing state data
    :return: a specialized instance of State
    """
    # Guess the type of state
    if state_d.get('type', None) == 'final':
        # Final pseudo state
        state = FinalState(state_d['name'])
    elif state_d.get('type', None) == 'history':
        # History pseudo state
        state = HistoryState(state_d['name'], state_d.get('initial'), state_d.get('deep', False))
    else:
        name = state_d.get('name')
        on_entry = state_d.get('on entry', None)
        on_exit = state_d.get('on exit', None)
        if 'states' in state_d:  # Compound state
            initial = state_d['initial']
            state = CompoundState(name, initial, on_entry, on_exit)
        elif 'orthogonal states' in state_d: #
            state = OrthogonalState(name, on_entry, on_exit)
        else:
            # Simple state
            state = BasicState(name, on_entry, on_exit)
    return state


def export_to_dict(statemachine: StateMachine) -> dict:
    """
    Export given StateMachine instance to a dict.
    :param statemachine: a StateMachine instance
    :return: a dict that can be used in `import_from_dict`
    """
    sm = statemachine  # alias
    d = OrderedDict()
    d['name'] = sm.name
    d['initial'] = sm.initial
    d['states'] = sm.children
    if sm.on_entry:
        d['on entry'] = sm.on_entry

    statelist_to_expand = [d['states']]
    while statelist_to_expand:
        statelist = statelist_to_expand.pop()
        for i, state in enumerate(statelist):
            statelist[i] = _export_element_to_dict(sm.states[state])
            new_statelist = statelist[i].get('states', statelist[i].get('orthogonal states', []))
            if len(new_statelist) > 0:
                statelist_to_expand.append(new_statelist)
    return {'statemachine': d}


def _export_element_to_dict(el) -> dict:
    """
    Export an element (State, Transition, etc.) to a dict.
    Is used in `export_to_dict` to generate a global representation.
    :param el: an instance of `statemachine.*`
    :return: a dict
    """
    d = OrderedDict()
    if isinstance(el, Event):
        d['name'] = el.name
    if isinstance(el, Transition):
        if not el.internal:
            d['target'] = el.to_state
        if not el.eventless:
            d['event'] = _export_element_to_dict(el.event)
        if el.condition:
            d['guard'] = el.condition
        if el.action:
            d['action'] = el.action
    if isinstance(el, StateMixin):
        d['name'] = el.name
    if isinstance(el, CompoundState):
        d['initial'] = el.initial
    if isinstance(el, ActionStateMixin):
        if el.on_entry:
            d['on entry'] = el.on_entry
        if el.on_exit:
            d['on exit'] = el.on_exit
    if isinstance(el, TransitionStateMixin):
        if len(el.transitions) > 0:
            d['transitions'] = [_export_element_to_dict(t) for t in el.transitions]
    if isinstance(el, CompositeStateMixin):
        if isinstance(el, OrthogonalState):
            d['orthogonal states'] = el.children
        else:
            d['states'] = el.children
    if isinstance(el, HistoryState):
        d['type'] = 'history'
        if el.initial:
            d['initial'] = el.initial
        if el.deep:
            d['deep'] = True
    if isinstance(el, FinalState):
        d['type'] = 'final'
    return d