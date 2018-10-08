import collections
import copy
from functools import partial
from typing import Any, Dict, Iterator, List, Mapping, Optional

from . import Evaluator
from ..model import (Event, StateMixin, Transition)

__all__ = ['EnhancedEvaluatorMixin']


class FrozenContext(collections.Mapping):
    """
    A shallow copy of a context. The keys of the underlying context are
    exposed as attributes.
    """
    __slots__ = ['__frozencontext']

    def __init__(self, context: Mapping) -> None:
        self.__frozencontext = {k: copy.copy(v) for k, v in context.items()}

    def __getattr__(self, item):
        try:
            return self.__frozencontext[item]
        except KeyError:
            raise AttributeError('{} has no attribute {}'.format(self, item))

    def __getstate__(self):
        return self.__frozencontext

    def __setstate__(self, state):
        self.__frozencontext = state

    def __getitem__(self, key):
        return self.__frozencontext[key]

    def __len__(self):
        return len(self.__frozencontext)

    def __iter__(self):
        return iter(self.__frozencontext)


class EnhancedEvaluatorMixin():
    """
    Enhances the Evaluator Class with additional capabilitesself.


    Depending on the method that is called, the context can expose additional values:

    - On both code execution and code evaluation:
        - A *time: float* value that represents the current time exposed by interpreter clock.
        - An *active(name: str) -> bool* Boolean function that takes a state name and return *True* if and only
          if this state is currently active, ie. it is in the active configuration of the ``Interpreter`` instance
          that makes use of this evaluator.
    - On code execution:
        - A *send(name: str, **kwargs) -> None* function that takes an event name and additional keyword parameters and
          raises an internal event with it. Raised events are propagated to bound statecharts as external events and
          to the current statechart as internal event. If delay is provided, a delayed event is created.
        - A *notify(name: str, **kwargs) -> None* function that takes an event name and additional keyword parameters and
          raises a meta-event with it. Meta-events are only sent to bound property statecharts.
        - If the code is related to a transition, the *event: Event* that fires the transition is exposed.
        - A *setdefault(name:str, value: Any) -> Any* function that defines and returns variable *name* in
          the global scope if it is not yet defined.
    - On guard or contract evaluation:
        - If the code is related to a transition, the *event: Event* that fires the transition is exposed.
    - On guard or contract (except preconditions) evaluation:
        - An *after(sec: float) -> bool* Boolean function that returns *True* if and only if the source state
          was entered more than *sec* seconds ago. The time is evaluated according to Interpreter's clock.
        - A *idle(sec: float) -> bool* Boolean function that returns *True* if and only if the source state
          did not fire a transition for more than *sec* ago. The time is evaluated according to Interpreter's clock.
    - On contract (except preconditions) evaluation:
        - A variable *__old__* that has an attribute *x* for every *x* in the context when either the state
          was entered (if the condition involves a state) or the transition was processed (if the condition
          involves a transition). The value of *__old__.x* is a shallow copy of *x* at that time.
    - On contract evaluation:
        - A *sent(name: str) -> bool* function that takes an event name and return True if an event with the same name
          was sent during the current step.
        - A *received(name: str) -> bool* function  that takes an event name and return True if an event with the
          same name is currently processed in this step.


    Note: This class does not implement all required methods and properties
        of the base Evaluator Class. Those methods and properites should be
        implemented in a Class derived from this Class.
    """

    def __init__(self, interpreter=None, *, initial_context=None):
        super().__init__(interpreter, initial_context=initial_context)

        self._context = {}  # type: Dict[str, Any]
        self._context.update(initial_context if initial_context else {})
        self._interpreter = interpreter

        # Memory and entry time
        self._memory = {}  # type: Dict[int, Mapping]
        self._entry_time = {}  # type: Dict[str, float]
        self._idle_time = {}  # type: Dict[str, float]

        # Intercept sent and received events
        self._sent_events = []  # type: List[Event]
        if self._interpreter is not None:
            self._interpreter.bind(self._sent_events.append)
        self._received_event = None  # type: Optional[Event]

    @property
    def context(self) -> Mapping:
        return self._context

    def on_step_starts(self, event: Optional[Event]=None) -> None:
        """
        Called each time the interpreter starts a macro step.

        :param event: Optional processed event
        """
        self._sent_events.clear()
        self._received_event = event

    def _setdefault(self, name: str, value: Any) -> Any:
        """
        Define and return variable "name".

        :param name: name of the variable
        :param value: value to use for that variable, if not defined
        :return: value of the variable
        """
        return self._context.setdefault(name, value)

    def _received(self, name: str) -> bool:
        """
        :param name: name of an event
        :return: True if given event name was received in current step.
        """
        return getattr(self._received_event, 'name', None) == name

    def _sent(self, name: str) -> bool:
        """
        :param name: name of an event
        :return: True if given event name was sent during this step.
        """
        return any((name == e.name for e in self._sent_events))

    def _active(self, name: str) -> bool:
        """
        Return True if given state name is active.

        :param name: name of a state
        :return: True if given state name is active.
        """
        return name in self._interpreter.configuration

    def _after(self, name: str, seconds: float) -> bool:
        """
        Return True if given state was entered more than *seconds* ago.

        :param name: name of a state
        :param seconds: elapsed time
        :return: True if given state was entered more than *seconds* ago.
        """
        return self._interpreter.time - seconds >= self._entry_time[name]

    def _idle(self, name: str, seconds: float) -> bool:
        """
        Return True if given state was the target of a transition more than *seconds* ago.

        :param name: name of a state
        :param seconds: elapsed time
        :return: True if given state was the target of a transition more than *seconds* ago.
        """
        return self._interpreter.time - seconds >= self._idle_time[name]

    def evaluate_guard(self, transition: Transition, event: Optional[Event]=None) -> bool:
        """
        Evaluate the guard for given transition.

        :param transition: the considered transition
        :param event: instance of *Event* if any
        :return: truth value of *code*
        """
        additional_context = {
            'event': event,
            'after': partial(self._after, transition.source),
            'idle': partial(self._idle, transition.source),
        }
        return self._evaluate_code(getattr(transition, 'guard', None), additional_context=additional_context)

    def execute_action(self, transition: Transition, event: Optional[Event]=None) -> List[Event]:
        """
        Execute the action for given transition.
        This method is called for every transition that is processed, even those with no *action*.

        :param transition: the considered transition
        :param event: instance of *Event* if any
        :return: a list of sent events
        """
        execution = self._execute_code(getattr(transition, 'action', None), additional_context={'event': event})

        self._idle_time[transition.source] = self._interpreter.time

        return execution

    def execute_on_entry(self, state: StateMixin) -> List[Event]:
        """
        Execute the on entry action for given state.
        This method is called for every state that is entered, even those with no *on_entry*.

        :param state: the considered state
        :return: a list of sent events
        """
        execution = self._execute_code(getattr(state, 'on_entry', None))

        self._entry_time[state.name] = self._interpreter.time
        self._idle_time[state.name] = self._interpreter.time

        return execution

    def evaluate_preconditions(self, obj, event: Optional[Event]=None) -> Iterator[str]:
        """
        Evaluate the preconditions for given object (either a *StateMixin* or a
        *Transition*) and return a list of conditions that are not satisfied.

        :param obj: the considered state or transition
        :param event: an optional *Event* instance, in the case of a transition
        :return: list of unsatisfied conditions
        """
        additional_context = {'event': event} if isinstance(obj, Transition) else {}  # type: Dict[str, Any]
        additional_context.update({
            'received': self._received,
            'sent': self._sent
        })  # type: ignore

        # Only needed if there is an invariant, a postcondition or a sequential condition
        if len(getattr(obj, 'invariants', [])) > 0 or len(getattr(obj, 'postconditions', [])) > 0:
            self._memory[id(obj)] = FrozenContext(self._context)

        return filter(
            lambda c: not self._evaluate_code(c, additional_context=additional_context),
            getattr(obj, 'preconditions', [])
        )

    def evaluate_invariants(self, obj, event: Optional[Event]=None) -> Iterator[str]:
        """
        Evaluate the invariants for given object (either a *StateMixin* or a
        *Transition*) and return a list of conditions that are not satisfied.

        :param obj: the considered state or transition
        :param event: an optional *Event* instance, in the case of a transition
        :return: list of unsatisfied conditions
        """
        state_name = obj.source if isinstance(obj, Transition) else obj.name

        additional_context = {'event': event} if isinstance(obj, Transition) else {}  # type: Dict[str, Any]
        additional_context.update({
            '__old__': self._memory.get(id(obj), None),
            'after': partial(self._after, state_name),
            'idle': partial(self._idle, state_name),
            'received': self._received,
            'sent': self._sent,
        })

        return filter(
            lambda c: not self._evaluate_code(c, additional_context=additional_context),
            getattr(obj, 'invariants', [])
        )

    def evaluate_postconditions(self, obj, event: Optional[Event]=None) -> Iterator[str]:
        """
        Evaluate the postconditions for given object (either a *StateMixin* or a
        *Transition*) and return a list of conditions that are not satisfied.

        :param obj: the considered state or transition
        :param event: an optional *Event* instance, in the case of a transition
        :return: list of unsatisfied conditions
        """
        state_name = obj.source if isinstance(obj, Transition) else obj.name

        additional_context = {'event': event} if isinstance(obj, Transition) else {}  # type: Dict[str, Any]
        additional_context.update({
            '__old__': self._memory.get(id(obj), None),
            'after': partial(self._after, state_name),
            'idle': partial(self._idle, state_name),
            'received': self._received,
            'sent': self._sent,
        })

        return filter(
            lambda c: not self._evaluate_code(c, additional_context=additional_context),
            getattr(obj, 'postconditions', [])
        )

    def __getstate__(self):
        attributes = self.__dict__.copy()
        return attributes
