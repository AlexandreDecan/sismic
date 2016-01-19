from sismic.exceptions import StatechartError

__all__ = ['Event', 'InternalEvent',
           'ContractMixin', 'StateMixin', 'ActionStateMixin', 'TransitionStateMixin', 'CompositeStateMixin', 'HistoryStateMixin',
           'BasicState', 'CompoundState', 'OrthogonalState', 'ShallowHistoryState', 'DeepHistoryState', 'FinalState',
           'Transition',
           'Statechart',
           'MicroStep', 'MacroStep']


class Event:
    """
    Simple event with a name and (optionally) some data.
    Unless the attribute already exists, each key from *data* is exposed as an attribute
    of this class.

    :param name: Name of the event
    :param data: additional data (mapping, dict-like)
    """

    def __init__(self, name: str, **additional_parameters):
        self.name = name
        self.data = additional_parameters

    def __eq__(self, other):
        return isinstance(other, Event) and \
               self.name == other.name and \
               self.data == other.data

    def __getattr__(self, attr):
        try:
            return self.data[attr]
        except:
            raise AttributeError('{} has no attribute {}'.format(self, attr))

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        if self.data:
            return '{}({}, {})'.format(self.__class__.__name__, self.name, ', '.join('{}={}'.format(k, v) for k,v in self.data.items()))
        else:
            return '{}({})'.format(self.__class__.__name__, self.name)


class InternalEvent(Event):
    """
    Subclass of Event that represents an internal event.
    """
    pass


class ContractMixin:
    """
    Mixin with a contract: preconditions, postconditions and invariants.
    """

    def __init__(self):
        self.preconditions = []
        self.postconditions = []
        self.invariants = []


class StateMixin:
    """
    State element with a name.

    :param name: name of the state
    """

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.name)

    def __eq__(self, other):
        return isinstance(other, StateMixin) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


class ActionStateMixin:
    """
    State that can define actions on entry and on exit.

    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    """

    def __init__(self, on_entry: str = None, on_exit: str = None):
        self.on_entry = on_entry
        self.on_exit = on_exit


class TransitionStateMixin:
    """
    A simple state can host transitions
    """
    pass


class CompositeStateMixin:
    """
    Composite state can have children states.
    """
    pass


class HistoryStateMixin:
    """
    History state has a memory that can be resumed.

    :param memory: name of the initial state
    """

    def __init__(self, memory: str = None):
        self.memory = memory


class BasicState(ContractMixin, StateMixin, ActionStateMixin, TransitionStateMixin):
    """
    A basic state, with a name, transitions, actions, etc. but no child state.

    :param name: name of this state
    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    """

    def __init__(self, name: str, on_entry: str = None, on_exit: str = None):
        ContractMixin.__init__(self)
        StateMixin.__init__(self, name)
        ActionStateMixin.__init__(self, on_entry, on_exit)
        TransitionStateMixin.__init__(self)


class CompoundState(ContractMixin, StateMixin, ActionStateMixin, TransitionStateMixin, CompositeStateMixin):
    """
    Compound states must have children states.

    :param name: name of this state
    :param initial: name of the initial state
    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    """

    def __init__(self, name: str, initial: str = None, on_entry: str = None, on_exit: str = None):
        ContractMixin.__init__(self)
        StateMixin.__init__(self, name)
        ActionStateMixin.__init__(self, on_entry, on_exit)
        TransitionStateMixin.__init__(self)
        CompositeStateMixin.__init__(self)
        self.initial = initial


class OrthogonalState(ContractMixin, StateMixin, ActionStateMixin, TransitionStateMixin, CompositeStateMixin):
    """
    Orthogonal states run their children simultaneously.

    :param name: name of this state
    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    """

    def __init__(self, name: str, on_entry: str = None, on_exit: str = None):
        ContractMixin.__init__(self)
        StateMixin.__init__(self, name)
        ActionStateMixin.__init__(self, on_entry, on_exit)
        TransitionStateMixin.__init__(self)
        CompositeStateMixin.__init__(self)


class ShallowHistoryState(ContractMixin, StateMixin, ActionStateMixin, HistoryStateMixin):
    """
    A shallow history state resumes the execution of its parent.
    It activates the latest visited state of its parent.

    :param name: name of this state
    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    :param memory: name of the initial state
    """
    def __init__(self, name: str, on_entry: str=None, on_exit: str=None, memory: str=None):
        ContractMixin.__init__(self)
        StateMixin.__init__(self, name)
        ActionStateMixin.__init__(self, on_entry, on_exit)
        HistoryStateMixin.__init__(self, memory)


class DeepHistoryState(ContractMixin, StateMixin, ActionStateMixin, HistoryStateMixin):
    """
    A deep history state resumes the execution of its parent, and of every nested
    active states in its parent.

    :param name: name of this state
    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    :param memory: name of the initial state
    """
    def __init__(self, name: str, on_entry: str=None, on_exit: str=None, memory: str=None):
        ContractMixin.__init__(self)
        StateMixin.__init__(self, name)
        ActionStateMixin.__init__(self, on_entry, on_exit)
        HistoryStateMixin.__init__(self, memory)


class FinalState(ContractMixin, StateMixin, ActionStateMixin):
    """
    Final state has NO transition and is used to detect state machine termination.

    :param name: name of this state
    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    """

    def __init__(self, name: str, on_entry: str = None, on_exit: str = None):
        ContractMixin.__init__(self)
        StateMixin.__init__(self, name)
        ActionStateMixin.__init__(self, on_entry, on_exit)


class Transition(ContractMixin):
    """
    Represent a transition from a source state to a target state.

    A transition can be eventless (no event) or internal (no target).
    A condition (code as string) can be specified as a guard.

    :param source: name of the source state
    :param target: name of the target state (if transition is not internal)
    :param event: event name (if any)
    :param guard: condition as code (if any)
    :param action: action as code (if any)
    """

    def __init__(self, source: str, target: str = None, event: str = None, guard: str = None, action: str = None):
        ContractMixin.__init__(self)
        self._source = source
        self._target = target
        self.event = event
        self.guard = guard
        self.action = action

    @property
    def source(self):
        return self._source

    @property
    def target(self):
        return self._target

    @property
    def internal(self):
        """
        Boolean indicating whether this transition is an internal transition.
        """
        return self._target is None

    @property
    def eventless(self):
        """
        Boolean indicating whether this transition is an eventless transition.
        """
        return self.event is None

    def __eq__(self, other):
        return (isinstance(other, Transition) and
                self.source == other.source and
                self.target == other.target and
                self.event == other.event and
                self.guard == other.guard and
                self.action == other.action)

    def __repr__(self):
        return 'Transition({0}, {1}, {2})'.format(self.source, self.target, self.event)

    def __str__(self):
        return '{} [{}] -> '.format(self.source, self.event, self.target if self.target else '')

    def __hash__(self):
        return hash(self.source)


class Statechart:
    """
    Python structure for a statechart

    :param name: Name of this statechart
    :param description: optional description
    :param preamble: code to execute to bootstrap the statechart
    """

    def __init__(self, name: str, description: str=None, preamble: str=None):
        self.name = name
        self.description = description
        self._preamble = preamble

        self._states = {}  # name -> State object
        self._parent = {}  # name -> parent.name
        self._children = {}  # name -> list of names
        self._transitions = []  # list of Transition objects

        self._root = None  # Root state

    @property
    def root(self):
        """
        Root state name
        """
        return self._root.name

    @property
    def preamble(self):
        """
        Preamble code
        """
        return self._preamble

    ########## STATES ##########

    @property
    def states(self):
        """
        List of state names in lexicographic order.
        """
        return sorted(self._states.keys())

    def add_state(self, state: StateMixin, parent):
        """
        Register given state. This method also register the given state
        to its parent.

        :param state: state to add
        :param parent: name of its parent
        :raise StatechartError:
        """
        # Check name unicity
        if state.name in self._states.keys():
            raise StatechartError('State {} already exists!'.format(state))

        if not parent:
            # Check root state
            if self._root:
                raise StatechartError('Root is already defined, {} should declare an existing parent state'.format(state))
            self._root = state
        else:
            parent_state = self.state_for(parent)

            # Check that parent exists
            if not parent_state:
                raise StatechartError('Parent "{}" of {} does not exist!'.format(parent, state))

            # Check that parent is a CompositeStateMixin.
            if not isinstance(parent_state, CompositeStateMixin):
                raise StatechartError('{} cannot be used as a parent for {}'.format(parent_state, state))

            # If state is an HistoryState, its parent must be a CompoundState
            if isinstance(state, HistoryStateMixin) and not isinstance(parent_state, CompoundState):
                raise StatechartError('{} cannot be used as a parent for {}'.format(parent_state, state))

        # Save state
        self._states[state.name] = state
        self._parent[state.name] = parent

        if parent:
            self._children.setdefault(parent, []).append(state.name)

    def remove_state(self, name: str):
        """
        Remove given state.

        The transitions that involve this state will be removed too.
        If the state is the target of an *initial* or *memory* property, their value will be set to None.
        If the state has children, they will be removed too.

        :param name: name of a state
        :raise StatechartError:
        """
        state = self.state_for(name)

        # Remove children
        for child in self.children_for(state.name):
            self.remove_state(child)

        # Remove transitions
        for transition in list(self.transitions):  # Make a copy!
            if transition.source == state.name or transition.target == state.name:
                self.remove_transition(transition)

        # Remove compoundstate's initial and historystate's memory
        for other_name, other_state in self._states.items():
            if isinstance(other_state, CompoundState):
                other_state.initial = None
            elif isinstance(other_state, HistoryStateMixin):
                other_state.memory = None

        # Remove state
        try:
            self._children.pop(name)
        except KeyError:
            pass
        try:
            self._parent.pop(name)
        except KeyError:
            pass

        self._states.pop(name)

        if self.root == state.name:
            self._root = None

    def rename_state(self, old_name: str, new_name: str):
        """
        Change state name, and adapt transitions, initial state, memory, etc.

        :param old_name: old name of the state
        :param new_name: new name of the state
        """
        if old_name == new_name:
            return
        if new_name in self._states:
            raise StatechartError('State {} already exists!'.format(new_name))
        state = self._states[old_name]

        # Change transitions
        for transition in self.transitions:
            if transition.source == old_name:
                if transition.internal:
                    transition.target = new_name
                transition._source = new_name

            if transition.target == old_name:
                transition._target = new_name

        for other_state in self._states.values():
            # Change initial (CompoundState)
            if isinstance(other_state, CompoundState):
                if other_state.initial == old_name:
                    other_state.initial = new_name

            # Change memory (HistoryState)
            if isinstance(other_state, HistoryStateMixin):
                if other_state.memory == old_name:
                    other_state.memory = new_name

            # Adapt parent
            if self._parent[other_state.name] == old_name:
                self._parent[other_state.name] = new_name

        # Rename
        state._name = new_name
        self._states[new_name] = self._states.pop(old_name)
        try:
            self._children[new_name] = self._children.pop(old_name)
        except KeyError:
            pass

    def state_for(self, name: str) -> StateMixin:
        """
        Return the state instance that has given name.

        :param name: a state name
        :return: a *StateMixin* that has the same name or None
        :raise StatechartError: if state does not exist
        """
        try:
            return self._states[name]
        except KeyError as e:
            raise StatechartError('State {} does not exist'.format(name)) from e

    def parent_for(self, name: str) -> str:
        """
        Return the name of the parent of given state name.

        :param name: a state name
        :return: its parent name, or None.
        :raise StatechartError: if state does not exist
        """
        try:
            return self._parent[name]
        except KeyError as e:
            raise StatechartError('State {} does not exist'.format(name)) from e

    def children_for(self, name: str) -> list:
        """
        Return the names of the children of the given state.

        :param name: a state name
        :return: a (possibly empty) list of children
        :raise StatechartError: if state does not exist
        """
        self.state_for(name)  # Raise StatechartError if state does not exist

        return self._children.get(name, [])

    def ancestors_for(self, name: str) -> list:
        """
        Return an ordered list of ancestors for the given state.
        Ancestors are ordered by decreasing depth.

        :param state: name of the state
        :return: state's ancestors
        :raise StatechartError: if state does not exist
        """
        self.state_for(name)  # Raise StatechartError if state does not exist

        ancestors = []
        parent = self._parent[name]
        while parent:
            ancestors.append(parent)
            parent = self._parent[parent]
        return ancestors

    def descendants_for(self, name: str) -> list:
        """
        Return an ordered list of descendants for the given state.
        Descendants are ordered by increasing depth.

        :param name: name of the state
        :return: state's descendants
        :raise StatechartError: if state does not exist
        """
        self.state_for(name)  # Raise StatechartError if state does not exist

        descendants = []
        states_to_consider = [name]
        while states_to_consider:
            name = states_to_consider.pop(0)
            for child in self.children_for(name):
                states_to_consider.append(child)
                descendants.append(child)
        return descendants

    def depth_for(self, name: str) -> int:
        """
        Return the depth of given state (1-indexed).

        :param name: name of the state
        :return: state depth
        :raise StatechartError: if state does not exist
        """
        self.state_for(name)  # Raise StatechartError if state does not exist

        ancestors = self.ancestors_for(name)
        return len(ancestors) + 1

    def least_common_ancestor(self, name_first: str, name_second: str) -> str:
        """
        Return the deepest common ancestor for *s1* and *s2*, or *None* if
        there is no common ancestor except root (top-level) state.

        :param name_first: name of first state
        :param name_second: name of second state
        :return: name of deepest common ancestor or *None*
        :raise StatechartError: if state does not exist
        """
        self.state_for(name_first)  # Raise StatechartError if state does not exist
        self.state_for(name_second)

        s1_anc = self.ancestors_for(name_first)
        s2_anc = self.ancestors_for(name_second)
        for state in s1_anc:
            if state in s2_anc:
                return state

    def leaf_for(self, names: list) -> list:
        """
        Return the leaves of *names*.

        Considering the list of states names in *states*, return a list containing each
        element of *states* such that this element has no descendant in *states*.
        In other words, this method returns the leaves from the given list of states.

        :param names: a list of names
        :return: the names of the leaves in *states*
        :raise StatechartError: if state does not exist
        """
        [self.state_for(s) for s in names]  # Raise StatechartError if state does not exist

        leaves = []
        # TODO: Need a more efficient way to compute this set
        for state in names:
            keep = True
            for descendant in self.descendants_for(state):
                if descendant in names:
                    keep = False
                    break
            if keep:
                leaves.append(state)
        return leaves

    ########## TRANSITIONS ##########

    @property
    def transitions(self):
        """
        List of available transitions
        """
        return list(self._transitions)

    def add_transition(self, transition: Transition):
        """
        Register given transition and register it on the source state

        :param transition: transition to add
        :raise StatechartError:
        """
        # Check that source state is known
        if not transition.source in self._states:
            raise StatechartError('Unknown source state for {}'.format(transition))

        from_state = self.state_for(transition.source)
        # Check that source state is a TransactionStateMixin
        if not isinstance(from_state, TransitionStateMixin):
            raise StatechartError('Cannot add {} on {}'.format(transition, from_state))

        # Check either internal OR target state is known
        if transition.target is not None and transition.target not in self._states:
            raise StatechartError('Unknown target state for {}'.format(transition))

        self._transitions.append(transition)

    def remove_transition(self, transition: Transition):
        """
        Remove given transitions.

        :param transition: a *Transition* instance
        :raise StatechartError: if transition is not registered
        """
        try:
            self._transitions.remove(transition)
        except ValueError:
            raise StatechartError('Transition {} does not exist'.format(transition))

    def rotate_transition(self, transition: Transition, **kwargs):
        """
        Rotate given transition.

        You MUST specify either *new_source* (a valid state name) or *new_target* (a valid state name or None)
        or both.

        :param transition: a *Transition* instance
        :param new_source: a state name
        :param new_target: a state name or None
        :raise StatechartError: if transition or state do not exist.
        """
        # Check that either new_source or new_target is set
        if 'new_source' not in kwargs and 'new_target' not in kwargs:
            raise ValueError('You must at least specify the new source or new target')

        # Check that transition exists
        if transition not in self._transitions:
            raise StatechartError('Unknown transition {}'.format(transition))

        # Rotate using source
        if 'new_source' in kwargs:
            new_source_state = self.state_for(kwargs['new_source'])
            if not isinstance(new_source_state, TransitionStateMixin):
                raise StatechartError('{} can not have transitions'.format(new_source_state))
            transition._source = new_source_state.name

        # Rotate using target
        if 'new_target' in kwargs:
            if kwargs['new_target'] is None:
                transition._target = None
            else:
                new_target_state = self.state_for(kwargs['new_target'])
                transition._target = new_target_state.name

    def transitions_from(self, source: str) -> list:
        """
        Return the list of transitions whose source is given name.

        :param source: name of source state
        :return: a list of *Transition* instances
        :raise StatechartError: if state does not exist
        """
        self.state_for(source)  # Raise StatechartError if state does not exist

        transitions = []
        for transition in self._transitions:
            if transition.source == source:
                transitions.append(transition)
        return transitions

    def transitions_to(self, target: str) -> list:
        """
        Return the list of transitions whose target is given name.
        Internal transitions are returned too.

        :param target: name of target state
        :return: a list of *Transition* instances
        :raise StatechartError: if state does not exist
        """
        self.state_for(target)  # Raise StatechartError if state does not exist

        transitions = []
        for transition in self._transitions:
            if transition.target == target or (transition.target is None and transition.source == target):
                transitions.append(transition)
        return transitions

    def transitions_with(self, event: str) -> list:
        """
        Return the list of transitions that can be triggered by given event name.

        :param event: name of the event
        :return: a list of *Transition* instances
        """
        transitions = []
        for transition in self._transitions:
            if transition.event == event:
                transitions.append(transition)
        return transitions

    ########## EVENTS ##########

    def events_for(self, name_or_names=None) -> list:
        """
        Return a list containing the name of every event that guards a transition in this statechart.

        If *name_or_names* is specified, it must be the name of a state (or a list of such names).
        Only transitions that have a source state from this list will be considered.
        By default, the list contains all the states.

        :param name_or_names: *None*, a state name or a list of state names.
        :return: A list of event names
        """
        if name_or_names is None:
            states = self._states.keys()
        elif isinstance(name_or_names, str):
            states = [name_or_names]
        else:
            states = name_or_names

        names = set()
        for state in states:
            for transition in self.transitions_from(state):
                if transition.event:
                    names.add(transition.event)
        return sorted(names)

    ########## TOOLS ##########

    def _validate_compoundstate_initial(self):
        """
        Checks that every *CompoundState*'s initial state refer to one of its children
        :raise StatechartError:
        """
        for name, state in self._states.items():
            if isinstance(state, CompoundState) and state.initial:
                if not state.initial in self._states:
                    raise StatechartError('Initial state {} of {} does not exist'.format(state.initial, state))
                if not state.initial in self.children_for(name):
                    raise StatechartError('Initial state {} of {} must be a child state'.format(state.initial, state))

    def _validate_historystate_memory(self):
        """
        Checks that every *HistoryStateMixin*'s memory refer to one of its parent's children

        :raise StatechartError:
        """
        for name, state in self._states.items():
            if isinstance(state, HistoryStateMixin) and state.memory:
                if not state.memory in self._states:
                    raise StatechartError('Initial memory {} of {} does not exist'.format(state.memory, state))
                if not state.memory in self.children_for(self.parent_for(name)):
                    raise StatechartError('Initial memory {} of {} must be a child of its parent'.format(state.memory, state))

    def validate(self):
        """
        Checks that every *CompoundState*'s initial state refer to one of its children
        Checks that every *HistoryStateMixin*'s memory refer to one of its parent's children

        :raise StatechartError:
        """
        self._validate_compoundstate_initial()
        self._validate_historystate_memory()


class MicroStep:
    """
    Create a micro step.

    A step consider *event*, takes a *transition* and results in a list
    of *entered_states* and a list of *exited_states*.
    Order in the two lists is REALLY important!

    :param event: Event or None in case of eventless transition
    :param transition: a *Transition* or None if no processed transition
    :param entered_states: possibly empty list of entered states
    :param exited_states: possibly empty list of exited states
    """

    def __init__(self, event: Event = None, transition: Transition = None,
                 entered_states: list = None, exited_states: list = None):
        self.event = event
        self.transition = transition if transition else []
        self.entered_states = entered_states if entered_states else []
        self.exited_states = exited_states if exited_states else []

    def __repr__(self):
        return 'MicroStep({}, {}, >{}, <{})'.format(self.event, self.transition, self.entered_states, self.exited_states)


class MacroStep:
    """
    A macro step is a list of micro steps.

    :param time: the time at which this step was executed
    :param steps: a list of *MicroStep* instances
    """

    def __init__(self, time: int, steps: list):
        self._time = time
        self._steps = steps

    @property
    def steps(self):
        """
        List of micro steps
        """
        return self._steps

    @property
    def time(self):
        """
        Time at which this step was executed.
        """
        return self._time

    @property
    def event(self) -> Event:
        """
        Event (or *None*) that were consumed.
        """
        for step in self._steps:
            if step.event:
                return step.event
        return None

    @property
    def transitions(self) -> list:
        """
        A (possibly empty) list of transitions that were triggered.
        """
        return [step.transition for step in self._steps if step.transition]

    @property
    def entered_states(self) -> list:
        """
        List of the states names that were entered.
        """
        states = []
        for step in self._steps:
            states += step.entered_states
        return states

    @property
    def exited_states(self) -> list:
        """
        List of the states names that were exited.
        """
        states = []
        for step in self._steps:
            states += step.exited_states
        return states

    def __repr__(self):
        return 'MacroStep@{}({}, {}, >{}, <{})'.format(round(self.time, 3), self.event, self.transitions,
                                                       self.entered_states, self.exited_states)
