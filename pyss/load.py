import yaml
import pyss.statemachine as statemachine


def from_yaml(data):
    return from_dict(yaml.load(data)['statemachine'])


def from_dict(data: dict):
    sm = statemachine.StateMachine(data['name'], data['initial'], data.get('execute', None))

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


def _transition_from_dict(state_name: str, transition_d: dict):
    """
    Return a Transition instance from given dict.
    :param state: name of the state in which the transition is defined
    :param transition_d: a dictionary containing transition data
    :return: an instance of Transition
    """
    to_state = transition_d.get('target', None)
    event = transition_d.get('event', None)
    if event:
        event = statemachine.Event(event)
    condition = transition_d.get('condition', None)
    action = transition_d.get('action', None)
    return statemachine.Transition(state_name, to_state, event, condition, action)


def _state_from_dict(state_d: dict):
    """
    Return the appropriate type of state from given dict.
    :param state_d: a dictionary containing state data
    :return: a specialized instance of State
    """
    # Guess the type of state
    if state_d.get('type', None) == 'final':
        # Final pseudo state
        state = statemachine.FinalState(state_d['name'])
    elif state_d.get('type', None) == 'history':
        # History pseudo state
        state = statemachine.HistoryState(state_d['name'], state_d.get('initial'), state_d.get('deep', False))
    else:
        name = state_d.get('name')
        on_entry = state_d.get('on_entry', None)
        on_exit = state_d.get('on_exit', None)
        if 'states' in state_d:  # Composite state
            if state_d.get('orthogonal', False):  # Orthogonal state
                state = statemachine.OrthogonalState(name, on_entry, on_exit)
            else:
                initial = state_d['initial']
                state = statemachine.CompositeState(name, initial, on_entry, on_exit)
        else:
            # Simple state
            state = statemachine.SimpleState(name, on_entry, on_exit)
    return state
