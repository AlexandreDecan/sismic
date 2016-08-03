from types import CodeType
from functools import partial
from typing import Dict, Iterator, cast, Any, Mapping, MutableMapping, List, Callable
from itertools import chain
import collections
import copy

from .evaluator import Evaluator
from sismic.model import Event, InternalEvent, Transition, StateMixin, Statechart
from sismic.exceptions import CodeEvaluationError
from .sequence import build_sequence, Sequence

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

    def __getitem__(self, key):
        return self.__frozencontext[key]

    def __len__(self):
        return len(self.__frozencontext)

    def __iter__(self):
        return iter(self.__frozencontext)


class Context(collections.MutableMapping):
    """
    Nested context (for dealing with scopes).

    Borrowed and corrected from http://code.activestate.com/recipes/577434/

    :param data: Optional initial dict
    :param parent: Parent context, if any
    """

    __slots__ = ['parent', 'map', 'maps']

    def __init__(self, data: Mapping = None, parent: 'Context' = None) -> None:
        self.parent = parent
        self.map = cast(MutableMapping, data) if data else {}
        self.maps = [self.map]
        if parent is not None:
            self.maps += parent.maps

    def new_child(self, data: Mapping = None) -> 'Context':
        """
        Create and return a nested context.

        :param data: Optional initial dict
        :return: A nested context
        """
        return Context(data, self)

    @property
    def root(self) -> 'Context':
        """
        :return: Root context
        """
        return self if self.parent is None else self.parent.root

    def __getitem__(self, key):
        m = self.map
        for m in self.maps:
            if key in m:
                break
        return m[key]

    def __setitem__(self, key, value) -> None:
        for m in self.maps:
            if key in m:
                m[key] = value
                return
        self.map[key] = value

    def __delitem__(self, key) -> None:
        for m in self.maps:
            if key in m:
                del m[key]
                return
        del self.map[key]

    def __len__(self) -> int:
        return len(set(*chain(m.keys() for m in self.maps)))

    def __iter__(self):
        return chain.from_iterable(self.maps)

    def __contains__(self, key) -> bool:
        return any(key in m for m in self.maps)

    def __repr__(self) -> str:
        return ' -> '.join(map(repr, self.maps))


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

    Each piece of code is executed with (a partially isolated) local context.
    Every state and every transition has a specific execution context.
    The code associated with a state is executed in a local context which is composed of local variables and every
    variable that is defined in the context of the parent state (and so one until the root context is reached).
    The context of a transition is built upon the context of its source state.
    The specific context of a state is available through the *context_for* method of a PythonEvaluator.

    :param interpreter: the interpreter that will use this evaluator,
        is expected to be an *Interpreter* instance
    :param initial_context: a dictionary that will be used as *__locals__*
    """

    def __init__(self, interpreter=None, *, initial_context: Mapping[str, Any]=None) -> None:
        super().__init__(interpreter, initial_context=initial_context)

        self._context = Context(initial_context)
        self._interpreter = interpreter

        # Memory and entry time
        self._memory = {}  # type: Dict[int, Mapping]
        self._entry_time = {}  # type: Dict[str, float]
        self._idle_time = {}  # type: Dict[str, float]

        # Precompiled code
        self._evaluable_code = {}  # type: Dict[str, CodeType]
        self._executable_code = {}  # type: Dict[str, CodeType]

        # Contexts
        self._contexts = {}  # type: Dict[str, Context]
        if getattr(interpreter, 'statechart', None) is not None:
            # Initialize nested contexts
            sc = self._interpreter.statechart  # type: Statechart

            self._contexts[sc.root] = self._context.new_child()
            for name in sc.descendants_for(sc.root):
                parent_name = sc.parent_for(name)
                self._contexts[name] = self._contexts[parent_name].new_child()

        # Intercept sent and received events
        self._sents_events = []  # type: List[Event]
        if self._interpreter is not None:
            self._interpreter.bind(self._sents_events.append)
        self._received_event = None  # type: Event

    @property
    def context(self) -> Mapping:
        context = dict(self._context)
        for state, mapping in self._contexts.items():
            for key, value in mapping.map.items():
                context['{}.{}'.format(state, key)] = value
        return context

    def on_step_starts(self, event: Event = None) -> None:
        """
        Called each time the interpreter starts a macro step.

        :param event: Optional processed event
        """
        self._sents_events.clear()
        self._received_event = event

    def context_for(self, name: str) -> Context:
        """
        Context object for given state name.

        :param name: State name
        :return: Context object
        """
        return self._contexts[name]

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
        return any((name == e.name for e in self._sents_events))

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

    def _evaluate_code(self, code: str, *, additional_context: Mapping = None, context: Mapping = None) -> bool:
        """
        Evaluate given code using Python.

        :param code: code to evaluate
        :param additional_context: an optional additional context
        :param context: the current context for this piece of code
        :return: truth value of *code*
        """
        if not code:
            return True
        if context is None:
            context = self._context

        compiled_code = self._evaluable_code.get(code, None)
        if compiled_code is None:
            compiled_code = self._evaluable_code.setdefault(code, compile(code, '<string>', 'eval'))

        exposed_context = {
            'active': self._active,
            'time': self._interpreter.time,
        }
        exposed_context.update(additional_context if additional_context is not None else {})

        try:
            return eval(compiled_code, exposed_context, context)  # type: ignore
        except Exception as e:
            raise CodeEvaluationError('The above exception occurred while evaluating:\n{}'.format(code)) from e

    def _execute_code(self, code: str, *, additional_context: Mapping = None, context: Mapping = None) -> List[Event]:
        """
        Execute given code using Python.

        :param code: code to execute
        :param additional_context: an optional additional context
        :param context: the current context for this piece of code
        :return: a list of sent events
        """
        if not code:
            return []
        if context is None:
            context = self._context

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
            exec(compiled_code, exposed_context, context)  # type: ignore
            return sent_events
        except Exception as e:
            raise CodeEvaluationError('The above exception occurred while executing:\n{}'.format(code)) from e

    def execute_statechart(self, statechart: Statechart) -> List[Event]:
        """
        Execute the initial code of a statechart.
        This method is called at the very beginning of the execution.

        :param statechart: statechart to consider
        :return: a list of sent events
        """
        if statechart.preamble:
            return self._execute_code(statechart.preamble, context=self._context)
        else:
            return []

    def evaluate_guard(self, transition: Transition, event: Event) -> bool:
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
        return self._evaluate_code(getattr(transition, 'guard', None),
                                   context=self._contexts[transition.source].new_child(),
                                   additional_context=additional_context)

    def execute_action(self, transition: Transition, event: Event) -> List[Event]:
        """
        Execute the action for given transition.
        This method is called for every transition that is processed, even those with no *action*.

        :param transition: the considered transition
        :param event: instance of *Event* if any
        :return: a list of sent events
        """
        self._idle_time[transition.source] = self._interpreter.time

        return self._execute_code(getattr(transition, 'action', None),
                                  context=self._contexts[transition.source].new_child(),
                                  additional_context={'event': event})

    def execute_onentry(self, state: StateMixin) -> List[Event]:
        """
        Execute the on entry action for given state.
        This method is called for every state that is entered, even those with no *on_entry*.

        :param state: the considered state
        :return: a list of sent events
        """
        self._entry_time[state.name] = self._interpreter.time
        self._idle_time[state.name] = self._interpreter.time

        return self._execute_code(getattr(state, 'on_entry', None), context=self._contexts[state.name])

    def execute_onexit(self, state: StateMixin) -> List[Event]:
        """
        Execute the on exit action for given state.
        This method is called for every state that is exited, even those with no *on_exit*.

        :param state: the considered state
        :return: a list of sent events
        """
        return self._execute_code(getattr(state, 'on_exit', None), context=self._contexts[state.name])

    def evaluate_preconditions(self, obj, event: Event = None) -> Iterator[str]:
        """
        Evaluate the preconditions for given object (either a *StateMixin* or a
        *Transition*) and return a list of conditions that are not satisfied.

        :param obj: the considered state or transition
        :param event: an optional *Event* instance, in the case of a transition
        :return: list of unsatisfied conditions
        """
        state_name = obj.source if isinstance(obj, Transition) else obj.name
        context = self._contexts[state_name]

        additional_context = {'event': event} if isinstance(obj, Transition) else {}
        additional_context.update({
            'received': self._received,
            'sent': self._sent
        })

        # Only needed if there is an invariant, a postcondition or a sequential condition
        if len(getattr(obj, 'invariants', [])) > 0 or len(getattr(obj, 'postconditions', [])) > 0 or len(
                getattr(obj, 'sequences', [])) > 0:
            self._memory[id(obj)] = FrozenContext(context)

        return filter(
            lambda c: not self._evaluate_code(c, context=context, additional_context=additional_context),
            getattr(obj, 'preconditions', [])
        )

    def evaluate_invariants(self, obj, event: Event = None) -> Iterator[str]:
        """
        Evaluate the invariants for given object (either a *StateMixin* or a
        *Transition*) and return a list of conditions that are not satisfied.

        :param obj: the considered state or transition
        :param event: an optional *Event* instance, in the case of a transition
        :return: list of unsatisfied conditions
        """
        state_name = obj.source if isinstance(obj, Transition) else obj.name
        context = self._contexts[state_name]

        additional_context = {'event': event} if isinstance(obj, Transition) else {}  # type: Dict[str, Any]
        additional_context.update({
            '__old__': self._memory.get(id(obj), None),
            'after': partial(self._after, state_name),
            'idle': partial(self._idle, state_name),
            'received': self._received,
            'sent': self._sent,
        })

        return filter(
            lambda c: not self._evaluate_code(c, context=context, additional_context=additional_context),
            getattr(obj, 'invariants', [])
        )

    def evaluate_postconditions(self, obj, event: Event = None) -> Iterator[str]:
        """
        Evaluate the postconditions for given object (either a *StateMixin* or a
        *Transition*) and return a list of conditions that are not satisfied.

        :param obj: the considered state or transition
        :param event: an optional *Event* instance, in the case of a transition
        :return: list of unsatisfied conditions
        """
        state_name = obj.source if isinstance(obj, Transition) else obj.name
        context = self._contexts[state_name]

        additional_context = {'event': event} if isinstance(obj, Transition) else {}  # type: Dict[str, Any]
        additional_context.update({
            '__old__': self._memory.get(id(obj), None),
            'after': partial(self._after, state_name),
            'idle': partial(self._idle, state_name),
            'received': self._received,
            'sent': self._sent,
        })

        return filter(
            lambda c: not self._evaluate_code(c, context=context, additional_context=additional_context),
            getattr(obj, 'postconditions', [])
        )

    def _evaluate_sequential_conditions_for_state(self, state: StateMixin, code: str) -> bool:
        context = self._contexts[state.name]

        additional_context = {
            '__old__': self._memory.get(id(state), None),
            'after': partial(self._after, state.name),
            'idle': partial(self._idle, state.name),
            'received': self._received,
            'sent': self._sent,
        }
        return self._evaluate_code(code, context=context, additional_context=additional_context)

    def initialize_sequential_conditions(self, state: StateMixin) -> None:
        """
        Initialize sequential conditions.

        :param state: for given state.
        """
        condition_mapping = {}  # type: Dict[str, Sequence]
        func = cast(Callable[[str], bool], partial(self._evaluate_sequential_conditions_for_state, state))

        for condition in getattr(state, 'sequences', []):
            condition_mapping[condition] = build_sequence(condition, func)

        self._condition_sequences[state.name] = condition_mapping
