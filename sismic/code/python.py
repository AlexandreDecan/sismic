import collections
import copy
from functools import partial
from types import CodeType
from typing import Any, Callable, Dict, Iterator, List, Mapping, Optional

from . import Evaluator
from ..exceptions import CodeEvaluationError
from ..model import Statechart, StateMixin, Transition, Event, InternalEvent

__all__ = ['PythonEvaluator']


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


def create_send_function(event_list: List[Event]) -> Callable[..., None]:
    """
    Create and return a callable that takes a name and additional parameters, builds an InternalEvent,
    and add it into given *event_list*.

    :param event_list: list to complement
    :return: the newly created function
    """

    def send(name, **kwargs):
        event = InternalEvent(name, **kwargs)
        event_list.append(event)

    return send


class PythonEvaluator(Evaluator):
    """
    A code evaluator that understands Python.

    Depending on the method that is called, the context can expose additional values:

    - On both code execution and code evaluation:
        - A *time: float* value that represents the current time exposed by the interpreter.
        - An *active(name: str) -> bool* Boolean function that takes a state name and return *True* if and only
          if this state is currently active, ie. it is in the active configuration of the ``Interpreter`` instance
          that makes use of this evaluator.
    - On code execution:
        - A *send(name: str, **kwargs) -> None* function that takes an event name and additional keyword parameters and
          raises an internal event with it.
        - If the code is related to a transition, the *event: Event* that fires the transition is exposed.
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

    If an exception occurred while executing or evaluating a piece of code, it is propagated by the
    evaluator.

    :param interpreter: the interpreter that will use this evaluator,
        is expected to be an *Interpreter* instance
    :param initial_context: a dictionary that will be used as *__locals__*
    """

    def __init__(self, interpreter=None, *, initial_context: Mapping[str, Any]=None) -> None:
        super().__init__(interpreter, initial_context=initial_context)

        self._context = {} if initial_context is None else initial_context  # type: Mapping[str, Any]
        self._interpreter = interpreter

        # Memory and entry time
        self._memory = {}  # type: Dict[int, Mapping]
        self._entry_time = {}  # type: Dict[str, float]
        self._idle_time = {}  # type: Dict[str, float]

        # Precompiled code
        self._evaluable_code = {}  # type: Dict[str, CodeType]
        self._executable_code = {}  # type: Dict[str, CodeType]

        # Intercept sent and received events
        self._sent_events = []  # type: List[Event]
        if self._interpreter is not None:
            self._interpreter.bind(self._sent_events.append)
        self._received_event = None  # type: Event

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

    def _evaluate_code(self, code: str, *, additional_context: Mapping=None) -> bool:
        """
        Evaluate given code using Python.

        :param code: code to evaluate
        :param additional_context: an optional additional context
        :return: truth value of *code*
        """
        if not code:
            return True

        compiled_code = self._evaluable_code.get(code, None)
        if compiled_code is None:
            compiled_code = self._evaluable_code.setdefault(code, compile(code, '<string>', 'eval'))

        exposed_context = {
            'active': self._active,
            'time': self._interpreter.time,
        }
        exposed_context.update(additional_context if additional_context is not None else {})

        try:
            return eval(compiled_code, exposed_context, self._context)  # type: ignore
        except Exception as e:
            raise CodeEvaluationError('The above exception occurred while evaluating:\n{}'.format(code)) from e

    def _execute_code(self, code: str, *, additional_context: Mapping=None) -> List[Event]:
        """
        Execute given code using Python.

        :param code: code to execute
        :param additional_context: an optional additional context
        :return: a list of sent events
        """
        if not code:
            return []

        compiled_code = self._executable_code.get(code, None)
        if compiled_code is None:
            compiled_code = self._executable_code.setdefault(code, compile(code, '<string>', 'exec'))

        # Handle sent events
        sent_events = []  # type: List[Event]

        exposed_context = {
            'active': self._active,
            'send': create_send_function(sent_events),
            'time': self._interpreter.time,
        }
        exposed_context.update(additional_context if additional_context is not None else {})

        try:
            exec(compiled_code, exposed_context, self._context)  # type: ignore
            return sent_events
        except Exception as e:
            raise CodeEvaluationError('The above exception occurred while executing:\n{}'.format(code)) from e

    def execute_statechart(self, statechart: Statechart):
        """
        Execute the initial code of a statechart.
        This method is called at the very beginning of the execution.

        :param statechart: statechart to consider
        """
        if statechart.preamble:
            events = self._execute_code(statechart.preamble)
            if len(events) > 0:
                raise CodeEvaluationError('Events cannot be raised by statechart preamble')

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
        self._idle_time[transition.source] = self._interpreter.time

        return self._execute_code(getattr(transition, 'action', None), additional_context={'event': event})

    def execute_on_entry(self, state: StateMixin) -> List[Event]:
        """
        Execute the on entry action for given state.
        This method is called for every state that is entered, even those with no *on_entry*.

        :param state: the considered state
        :return: a list of sent events
        """
        self._entry_time[state.name] = self._interpreter.time
        self._idle_time[state.name] = self._interpreter.time

        return self._execute_code(getattr(state, 'on_entry', None))

    def execute_on_exit(self, state: StateMixin) -> List[Event]:
        """
        Execute the on exit action for given state.
        This method is called for every state that is exited, even those with no *on_exit*.

        :param state: the considered state
        :return: a list of sent events
        """
        return self._execute_code(getattr(state, 'on_exit', None))

    def evaluate_preconditions(self, obj, event: Optional[Event]=None) -> Iterator[str]:
        """
        Evaluate the preconditions for given object (either a *StateMixin* or a
        *Transition*) and return a list of conditions that are not satisfied.

        :param obj: the considered state or transition
        :param event: an optional *Event* instance, in the case of a transition
        :return: list of unsatisfied conditions
        """
        state_name = obj.source if isinstance(obj, Transition) else obj.name

        additional_context = {'event': event} if isinstance(obj, Transition) else {}
        additional_context.update({
            'received': self._received,
            'sent': self._sent
        })  # type: ignore

        # Only needed if there is an invariant, a postcondition or a sequential condition
        if len(getattr(obj, 'invariants', [])) > 0 or len(getattr(obj, 'postconditions', [])) > 0 or len(
                getattr(obj, 'sequences', [])) > 0:
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
        attributes['_executable_code'] = dict()  # Code fragment cannot be pickled
        attributes['_evaluable_code'] = dict()  # Code fragment cannot be pickled
        return attributes
