from abc import ABCMeta
from typing import List

__all__ = ['ContractMixin', 'StateMixin', 'ActionStateMixin', 'TransitionStateMixin', 'CompositeStateMixin',
           'HistoryStateMixin', 'BasicState', 'CompoundState', 'OrthogonalState', 'ShallowHistoryState',
           'DeepHistoryState', 'FinalState', 'Transition']


class ContractMixin(metaclass=ABCMeta):
    """
    Mixin with a contract: preconditions, postconditions and invariants.
    """

    def __init__(self) -> None:
        self.preconditions = []  # type: List[str]
        self.postconditions = []  # type: List[str]
        self.invariants = []  # type: List[str]

    def __eq__(self, other):
        if isinstance(other, ContractMixin):
            return (
                self.preconditions == other.preconditions
                and self.postconditions == other.postconditions
                and self.invariants == other.invariants
            )
        else:
            return NotImplemented


class StateMixin(metaclass=ABCMeta):
    """
    State element with a name.

    :param name: name of the state
    """

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self):
        return self._name

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.name)

    def __eq__(self, other):
        if isinstance(other, StateMixin):
            return self.name == other.name
        else:
            return NotImplemented

    def __hash__(self):
        return hash(self.name)


class ActionStateMixin(metaclass=ABCMeta):
    """
    State that can define actions on entry and on exit.

    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    """

    def __init__(self, on_entry: str=None, on_exit: str=None) -> None:
        self.on_entry = on_entry
        self.on_exit = on_exit

    def __eq__(self, other):
        if isinstance(other, ActionStateMixin):
            return (
                self.on_entry == other.on_exit
                and self.on_exit == other.on_exit
            )
        else:
            return NotImplemented


class TransitionStateMixin(metaclass=ABCMeta):
    """
    A simple state can host transitions
    """

    def __eq__(self, other):
        return isinstance(other, TransitionStateMixin)


class CompositeStateMixin(metaclass=ABCMeta):
    """
    Composite state can have children states.
    """

    def __eq__(self, other):
        return isinstance(other, CompositeStateMixin)


class HistoryStateMixin(metaclass=ABCMeta):
    """
    History state has a memory that can be resumed.

    :param memory: name of the initial state
    """

    def __init__(self, memory: str=None) -> None:
        self.memory = memory

    def __eq__(self, other):
        if isinstance(other, HistoryStateMixin):
            return self.memory == other.memory
        else:
            return NotImplemented


class BasicState(ContractMixin, StateMixin, ActionStateMixin, TransitionStateMixin):
    """
    A basic state, with a name, transitions, actions, etc. but no child state.

    :param name: name of this state
    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    """

    def __init__(self, name: str, on_entry: str=None, on_exit: str=None) -> None:
        ContractMixin.__init__(self)
        StateMixin.__init__(self, name)
        ActionStateMixin.__init__(self, on_entry, on_exit)
        TransitionStateMixin.__init__(self)

    def __eq__(self, other):
        if isinstance(other, BasicState):
            return (
                ContractMixin.__eq__(self, other)
                and StateMixin.__eq__(self, other)
                and ActionStateMixin.__eq__(self, other)
                and TransitionStateMixin.__eq__(self, other)
            )
        else:
            return NotImplemented


class CompoundState(ContractMixin, StateMixin, ActionStateMixin, TransitionStateMixin, CompositeStateMixin):
    """
    Compound states must have children states.

    :param name: name of this state
    :param initial: name of the initial state
    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    """

    def __init__(self, name: str, initial: str=None, on_entry: str=None, on_exit: str=None) -> None:
        ContractMixin.__init__(self)
        StateMixin.__init__(self, name)
        ActionStateMixin.__init__(self, on_entry, on_exit)
        TransitionStateMixin.__init__(self)
        CompositeStateMixin.__init__(self)
        self.initial = initial

    def __eq__(self, other):
        if isinstance(other, CompoundState):
            return (
                ContractMixin.__eq__(self, other)
                and StateMixin.__eq__(self, other)
                and ActionStateMixin.__eq__(self, other)
                and TransitionStateMixin.__eq__(self, other)
                and CompositeStateMixin.__eq__(self, other)
            )
        else:
            return NotImplemented


class OrthogonalState(ContractMixin, StateMixin, ActionStateMixin, TransitionStateMixin, CompositeStateMixin):
    """
    Orthogonal states run their children simultaneously.

    :param name: name of this state
    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    """

    def __init__(self, name: str, on_entry: str=None, on_exit: str=None) -> None:
        ContractMixin.__init__(self)
        StateMixin.__init__(self, name)
        ActionStateMixin.__init__(self, on_entry, on_exit)
        TransitionStateMixin.__init__(self)
        CompositeStateMixin.__init__(self)

    def __eq__(self, other):
        if isinstance(other, OrthogonalState):
            return (
                ContractMixin.__eq__(self, other)
                and StateMixin.__eq__(self, other)
                and ActionStateMixin.__eq__(self, other)
                and TransitionStateMixin.__eq__(self, other)
                and CompositeStateMixin.__eq__(self, other)
            )
        else:
            return NotImplemented


class ShallowHistoryState(ContractMixin, StateMixin, ActionStateMixin, HistoryStateMixin):
    """
    A shallow history state resumes the execution of its parent.
    It activates the latest visited state of its parent.

    :param name: name of this state
    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    :param memory: name of the initial state
    """
    def __init__(self, name: str, on_entry: str=None, on_exit: str=None, memory: str=None) -> None:
        ContractMixin.__init__(self)
        StateMixin.__init__(self, name)
        ActionStateMixin.__init__(self, on_entry, on_exit)
        HistoryStateMixin.__init__(self, memory)

    def __eq__(self, other):
        if isinstance(other, ShallowHistoryState):
            return (
                ContractMixin.__eq__(self, other)
                and StateMixin.__eq__(self, other)
                and ActionStateMixin.__eq__(self, other)
                and HistoryStateMixin.__eq__(self, other)
            )
        else:
            return NotImplemented


class DeepHistoryState(ContractMixin, StateMixin, ActionStateMixin, HistoryStateMixin):
    """
    A deep history state resumes the execution of its parent, and of every nested
    active states in its parent.

    :param name: name of this state
    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    :param memory: name of the initial state
    """
    def __init__(self, name: str, on_entry: str=None, on_exit: str=None, memory: str=None) -> None:
        ContractMixin.__init__(self)
        StateMixin.__init__(self, name)
        ActionStateMixin.__init__(self, on_entry, on_exit)
        HistoryStateMixin.__init__(self, memory)

    def __eq__(self, other):
        if isinstance(other, DeepHistoryState):
            return (
                ContractMixin.__eq__(self, other)
                and StateMixin.__eq__(self, other)
                and ActionStateMixin.__eq__(self, other)
                and HistoryStateMixin.__eq__(self, other)
            )
        else:
            return NotImplemented


class FinalState(ContractMixin, StateMixin, ActionStateMixin):
    """
    Final state has NO transition and is used to detect state machine termination.

    :param name: name of this state
    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    """

    def __init__(self, name: str, on_entry: str = None, on_exit: str = None) -> None:
        ContractMixin.__init__(self)
        StateMixin.__init__(self, name)
        ActionStateMixin.__init__(self, on_entry, on_exit)

    def __eq__(self, other):
        if isinstance(other, FinalState):
            return (
                ContractMixin.__eq__(self, other)
                and StateMixin.__eq__(self, other)
                and ActionStateMixin.__eq__(self, other)
            )
        else:
            return NotImplemented


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
    :param priority: priority (default to 0)
    """

    LOW_PRIORITY = -1
    DEFAULT_PRIORITY = 0
    HIGH_PRIORITY = 1

    def __init__(self, source: str, target: str=None, event: str=None, guard: str=None, action: str=None, priority=None) -> None:
        ContractMixin.__init__(self)
        self._source = source
        self._target = target
        self.event = event
        self.guard = guard
        self.action = action
        self.priority = 0 if priority is None else priority

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
        if isinstance(other, Transition):
            return (
                ContractMixin.__eq__(self, other)
                and self.source == other.source
                and self.target == other.target
                and self.event == other.event
                and self.guard == other.guard
                and self.action == other.action
                and self.priority == other.priority
            )
        else:
            return NotImplemented

    def __repr__(self):
        return 'Transition({!r}, {!r}, event={!r})'.format(self.source, self.target, self.event)

    def __str__(self):
        return '{} -> {}{} [{}] -> {}'.format(
            self.source,
            '' if self.priority == 0 else '{}:'.format(self.priority),
            self.event,
            self.guard,
            self.target if self.target else ''
        )

    def __hash__(self):
        return hash(self.source)
