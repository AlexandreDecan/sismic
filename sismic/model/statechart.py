from copy import deepcopy
from typing import Callable, Dict, Iterable, List, Optional, Union, cast

from ..exceptions import StatechartError

from .elements import (CompositeStateMixin, CompoundState, HistoryStateMixin,
                       StateMixin, Transition, TransitionStateMixin)

__all__ = ['Statechart']


class Statechart:
    """
    Python structure for a statechart

    :param name: Name of this statechart
    :param description: optional description
    :param preamble: code to execute to bootstrap the statechart
    """

    def __init__(self, name: str, description: str=None, preamble: str=None) -> None:
        self.name = name
        self.description = description
        self._preamble = preamble

        self._states = {}  # type: Dict[str, StateMixin]
        self._parent = {}  # type: Dict[str, Optional[str]]
        self._children = {}  # type: Dict[Optional[str], List[str]]
        self._transitions = []  # type: List[Transition]

        self._children[None] = []  # Root state

    @property
    def root(self) -> Optional[str]:
        """
        Root state name
        """
        for name, parent in self._parent.items():
            if parent is None:
                return name
        return None

    @property
    def preamble(self):
        """
        Preamble code
        """
        return self._preamble

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.name)

    # ######### STATES ##########

    @property
    def states(self):
        """
        List of state names in lexicographic order.
        """
        return sorted(self._states.keys())

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

    def parent_for(self, name: str) -> Optional[str]:
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

    def children_for(self, name: str) -> List[str]:
        """
        Return the names of the children of the given state.

        :param name: a state name
        :return: a (possibly empty) list of children
        :raise StatechartError: if state does not exist
        """
        self.state_for(name)  # Raise StatechartError if state does not exist

        return self._children[name]

    def ancestors_for(self, name: str) -> List[str]:
        """
        Return an ordered list of ancestors for the given state.
        Ancestors are ordered by decreasing depth.

        :param name: name of the state
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

    def descendants_for(self, name: str) -> List[str]:
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

    def least_common_ancestor(self, name_first: str, name_second: str) -> Optional[str]:
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
        return None

    def leaf_for(self, names: Iterable[str]) -> List[str]:
        """
        Return the leaves of *names*.

        Considering the list of states names in *names*, return a list containing each
        element of *names* such that this element has no descendant in *names*.

        :param names: a list of state names
        :return: the names of the leaves in *names*
        :raise StatechartError: if a state does not exist
        """
        leaves = []  # type: List[str]
        names = set(names)  # Lookups in set are more efficient

        for name in names:
            for descendant in self.descendants_for(name):  # Raise a StatechartError if it does not exist!
                if descendant in names:
                    break
            else:  # no break occurs
                leaves.append(name)
        return leaves

    # ######### TRANSITIONS ##########

    @property
    def transitions(self):
        """
        List of available transitions
        """
        return list(self._transitions)

    def add_transition(self, transition: Transition) -> None:
        """
        Register given transition and register it on the source state

        :param transition: transition to add
        :raise StatechartError:
        """
        # Check that source state is known
        try:
            from_state = self.state_for(transition.source)
        except StatechartError as e:
            raise StatechartError('Unknown source state for {}'.format(transition)) from e

        # Check that source state is a TransactionStateMixin
        if not isinstance(from_state, TransitionStateMixin):
            raise StatechartError('Cannot add {} on {}'.format(transition, from_state))

        # Check either internal OR target state is known
        if transition.target is not None and transition.target not in self._states:
            raise StatechartError('Unknown target state for {}'.format(transition))

        self._transitions.append(transition)

    def remove_transition(self, transition: Transition) -> None:
        """
        Remove given transitions.

        :param transition: a *Transition* instance
        :raise StatechartError: if transition is not registered
        """
        try:
            self._transitions.remove(transition)
        except ValueError:
            raise StatechartError('Transition {} does not exist'.format(transition))

    def rotate_transition(self, transition: Transition, new_source: str='', new_target: Optional[str]='') -> None:
        """
        Rotate given transition.

        You MUST specify either *new_source* (a valid state name) or *new_target* (a valid state name or None) or both.

        :param transition: a *Transition* instance
        :param new_source: a state name
        :param new_target: a state name or None
        :raise StatechartError: if given transition or a given state does not exist.
        """
        # Check that either new_source or new_target is set
        if new_source == new_target == '':
            raise ValueError('You must at least specify the new source or new target')

        # Check that transition exists
        if transition not in self._transitions:
            raise StatechartError('Unknown transition {}'.format(transition))

        # Rotate using source
        if new_source != '':
            new_source_state = self.state_for(new_source)
            if not isinstance(new_source_state, TransitionStateMixin):
                raise StatechartError('{} cannot have transitions'.format(new_source_state))
            assert isinstance(new_source_state, StateMixin)
            transition._source = new_source_state.name

        # Rotate using target
        if new_target != '':
            if new_target is None:
                transition._target = None
            else:
                new_target_state = self.state_for(new_target)
                transition._target = new_target_state.name

    def transitions_from(self, source: str) -> List[Transition]:
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

    def transitions_to(self, target: str) -> List[Transition]:
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

    def transitions_with(self, event: str) -> List[Transition]:
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

    # ######### EVENTS ##########

    def events_for(self, name_or_names: Union[str, List[str]]=None) -> List[str]:
        """
        Return a list containing the name of every event that guards a transition in this statechart.

        If *name_or_names* is specified, it must be the name of a state (or a list of such names).
        Only transitions that have a source state from this list will be considered.
        By default, the list contains all the states.

        :param name_or_names: *None*, a state name or a list of state names.
        :return: A list of event names
        """
        if name_or_names is None:
            states = list(self._states.keys())
        elif isinstance(name_or_names, str):
            states = [name_or_names]
        else:
            states = name_or_names

        states = cast(List[str], states)
        names = set()
        for state in states:
            for transition in self.transitions_from(state):
                if transition.event:
                    names.add(transition.event)
        return sorted(names)

    # ######### STRUCTURAL CHANGES ##########

    def add_state(self, state: StateMixin, parent: Optional[str]) -> None:
        """
        Add given state (a *StateMixin* instance) on given parent (its name as an *str*).
        If given state should be use as a root state, set *parent* to None.

        :param state: state to add
        :param parent: name of its parent, or None
        :raise StatechartError:
        """
        # Check state has a name
        if state.name is None:
            raise StatechartError('State {} must have a name'.format(state))

        # Check name unicity
        if state.name in self._states.keys():
            raise StatechartError('State {} already exists!'.format(state))

        if not parent:
            # Check root state
            if self.root:
                raise StatechartError('Root already defined, {} should declare an existing parent state'.format(state))
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
        self._children[state.name] = []
        self._children[parent].append(state.name)

    def remove_state(self, name: str) -> None:
        """
        Remove given state.

        The transitions that involve this state will also be removed.
        If the state is the target of an *initial* or *memory* property, their value will be set to None.
        If the state has children, they will be removed too.

        :param name: name of a state
        :raise StatechartError:
        """
        state = self.state_for(name)

        # Remove children
        for child in list(self.children_for(state.name)):
            self.remove_state(child)

        # Remove transitions
        for transition in list(self.transitions):  # Make a copy!
            if transition.source == state.name or transition.target == state.name:
                self.remove_transition(transition)

        # Remove compoundstate's initial and historystate's memory
        for o_state in self._states.values():
            if isinstance(o_state, CompoundState):
                o_state.initial = None
            elif isinstance(o_state, HistoryStateMixin):
                o_state.memory = None

        # Remove state
        self._states.pop(name)
        parent = self._parent.pop(name)
        self._children.pop(name)

        self._children[parent].remove(name)

    def rename_state(self, old_name: str, new_name: str) -> None:
        """
        Change state name, and adapt transitions, initial state, memory, etc.

        :param old_name: old name of the state
        :param new_name: new name of the state
        """
        if old_name == new_name:
            return
        if new_name in self._states:
            raise StatechartError('State {} already exists!'.format(new_name))

        # Check state exists
        state = self.state_for(old_name)

        # Change transitions
        for transition in self.transitions:
            if transition.source == old_name:
                if transition.internal:
                    transition._target = new_name
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

        # Adapt structures
        parent_name = self._parent[old_name]
        self._children[parent_name].remove(old_name)
        self._children[parent_name].append(new_name)

        self._states[new_name] = self._states.pop(old_name)
        self._parent[new_name] = self._parent.pop(old_name)
        self._children[new_name] = self._children.pop(old_name)

        # Rename state!
        state._name = new_name

    def move_state(self, name: str, new_parent: str) -> None:
        """
        Move given state (and its children) such that its new parent is *new_parent*.

        Notice that a state cannot be moved inside itself or inside one of its descendants.
        If the state to move is the target of an *initial* or *memory* property of its parent,
        this property will be set to None. The same occurs if given state is an history state.

        :param name: name of the state to move
        :param new_parent: name of the new parent
        """
        # Check that both states exist
        state = self.state_for(name)
        self.state_for(new_parent)

        # Check that parent is not a descendant (or self) of given state
        if new_parent in [name] + self.descendants_for(name):
            raise StatechartError('State {} cannot be moved into itself or one of its descendants.'.format(state))

        # Change its parent and register state as a child
        old_parent = self.parent_for(name)
        self._parent[name] = new_parent
        self._children[old_parent].remove(name)
        self._children.setdefault(new_parent, []).append(name)

        # Check memory property
        if isinstance(state, HistoryStateMixin):
            state.memory = None

        for other_state in self._states.values():
            # Change initial (CompoundState)
            if isinstance(other_state, CompoundState):
                if other_state.initial == name:
                    other_state.initial = None

            # Change memory (HistoryState)
            if isinstance(other_state, HistoryStateMixin):
                if other_state.memory == name:
                    other_state.memory = None

    def copy_from_statechart(self, statechart: 'Statechart', *, source: str, replace: str,
                             renaming_func: Callable[[str], str]=lambda s: s) -> None:
        """
        Copy (a part of) given *statechart* into current one.

        Copy *source* state, all its descendants and all involved transitions from *statechart* into current statechart.
        The *source* state will override *replace* state (but will be renamed to *replace*), and all its descendants in
        *statechart* will be copied into current statechart.
        All the transitions that are involved in the process must be fully contained in *source* state (ie. for all
        transition T: S->T, if S (resp. T) is a descendant-or-self of *source*, then T (resp. S) must be
        a descendant-or-self of *source*).

        If necessary, callable *renaming_func* can be provided. This function should accept a (state) name and return a
        (new state) name. Use *renaming_func* to avoid conflicting names in target statechart.

        :param statechart: Source statechart from which states will be copied.
        :param source: Name of the source state.
        :param replace: Name of the target state. Should refer to a StateMixin with no child.
        :param renaming_func: Optional callable to resolve conflicting names.
        """
        if len(self.children_for(replace)) > 0:
            raise StatechartError('State {} cannot be replaced while it has children.'.format(replace))

        statechart_copy = deepcopy(statechart)  # type: Statechart

        # Rename and copy states
        statechart_copy.rename_state(source, replace)
        source_name = replace  # For lisibility
        self._states[replace] = statechart_copy.state_for(source_name)
        for name in statechart_copy.descendants_for(source_name):
            new_name = renaming_func(name)
            # May raise a StatechartError if names collides in source statechart.
            # Possible workaround: first rename all states to uid, then rename to new names
            statechart_copy.rename_state(name, new_name)
            self.add_state(statechart_copy.state_for(new_name), statechart_copy.parent_for(new_name))

        # Copy transitions
        for name in [source_name] + statechart_copy.descendants_for(source_name):
            transitions = set(statechart_copy.transitions_from(name) + statechart_copy.transitions_to(name))
            for transition in transitions:
                try:
                    self.add_transition(transition)
                except StatechartError as e:
                    raise StatechartError('Cannot copy {} because transition {} is not contained in {}'.
                                          format(transition.source, transition, source)) from e

    # ######### VALIDATION ##########

    def _validate_compoundstate_initial(self) -> bool:
        """
        Checks that every *CompoundState*'s initial state refer to one of its children

        :return: True
        :raise StatechartError:
        """
        for name, state in self._states.items():
            if isinstance(state, CompoundState) and state.initial:
                if state.initial not in self._states:
                    raise StatechartError('Initial state {} of {} does not exist'.format(state.initial, state))
                if state.initial not in self.children_for(name):
                    raise StatechartError('Initial state {} of {} must be a child state'.format(state.initial, state))
        return True

    def _validate_historystate_memory(self) -> bool:
        """
        Checks that every *HistoryStateMixin*'s memory refer to one of its parent's children, except itself.

        :return: True
        :raise StatechartError:
        """
        for name, state in self._states.items():
            if isinstance(state, HistoryStateMixin):
                memory = state.memory
                if memory is None:
                    continue
                if memory == name:
                    raise StatechartError('Initial memory {} of {} cannot target itself'.format(state.memory, state))
                if memory not in self._states:
                    raise StatechartError('Initial memory {} of {} does not exist'.format(state.memory, state))
                if state.memory not in self.children_for(self.parent_for(name)):
                    raise StatechartError(
                        'Initial memory {} of {} must be a parent\'s child'.format(state.memory, state)
                    )
        return True

    def validate(self) -> bool:
        """
        Checks that every *CompoundState*'s initial state refer to one of its children
        Checks that every *HistoryStateMixin*'s memory refer to one of its parent's children

        :return: True
        :raise StatechartError:
        """
        self._validate_compoundstate_initial()
        self._validate_historystate_memory()

        return True
