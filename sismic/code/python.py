from types import CodeType
from functools import partial
from typing import Dict, Iterator, cast, Any, Mapping, MutableMapping
from itertools import chain
import collections
import copy

from .evaluator import Evaluator
from sismic.model import Event, InternalEvent, Transition, StateMixin, Statechart
from sismic.exceptions import CodeEvaluationError

__all__ = ['PythonEvaluator']


class FrozenContext(collections.Mapping):
    """
    A shallow copy of a context. The keys of the underlying context are
    exposed as attributes.
    """
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
    def __init__(self, data: Mapping=None, parent: 'Context'=None) -> None:
        self.parent = parent
        self.map = cast(MutableMapping, data) if data else {}
        self.maps = [self.map]
        if parent is not None:
            self.maps += parent.maps

    def new_child(self, data: Mapping=None) -> 'Context':
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


class PythonEvaluator(Evaluator):
    """
    A code evaluator that understands Python.

    Depending on the method that is called, the context can expose additional values:

    - Always:
        - A *time* value that represents the current time exposed by the interpreter.
        - An *active(name) -> bool* Boolean function that takes a state name and return *True* if and only
          if this state is currently active, ie. it is in the active configuration of the ``Interpreter`` instance
          that makes use of this evaluator.
    - On code execution:
        - A *send(name, **kwargs)* function that takes an event name and additional keyword parameters and fires
          an internal event with.
        - If the code is related to a transition, the *event* that fires the transition is exposed.
    - On code evaluation:
        - If the code is related to a transition, the *event* that fires the transition is exposed.
    - On guard evaluation:
        - An *after(sec) -> bool* Boolean function that returns *True* if and only if the source state
          was entered more than *sec* seconds ago. The time is evaluated according to Interpreter's clock.
        - A *idle(sec) -> bool* Boolean function that returns *True* if and only if the source state
          did not fire a transition for more than *sec* ago. The time is evaluated according to Interpreter's clock.
    - On postcondition or invariant:
        - A variable *__old__* that has an attribute *x* for every *x* in the context when either the state
          was entered (if the condition involves a state) or the transition was processed (if the condition
          involves a transition). The value of *__old__.x* is a shallow copy of *x* at that time.

    If an exception occurred while executing or evaluating a piece of code, it is propagated by the
    evaluator.

    Each piece of code is executed with (a partially isolated) local context.
    Every state and every transition has a specific evaluation context.
    The code associated with a state is executed in a local context which is composed of local variables and every
    variable that is defined in the context of the parent state. The context of a transition is built upon the context
    of its source state.

    :param interpreter: the interpreter that will use this evaluator,
        is expected to be an *Interpreter* instance
    :param initial_context: a dictionary that will be used as *__locals__*
    """

    def __init__(self, interpreter=None, *, initial_context: Mapping=None) -> None:
        super().__init__()

        self._context = Context(initial_context)
        self._interpreter = interpreter

        self.__memory = {}  # type: Dict[int, Mapping]
        self.__entry_time = {}  # type: Dict[str, float]
        self.__idle_time = {}  # type: Dict[str, float]

        self.__evaluable_code = {}  # type: Dict[str, CodeType]
        self.__executable_code = {}  # type: Dict[str, CodeType]
        self.__contexts = {}  # type: Dict[str, Context]

        if getattr(interpreter, 'statechart', None) is not None:
            # Initialize nested contexts
            sc = self._interpreter.statechart  # type: Statechart

            self.__contexts[sc.root] = self._context.new_child()
            for name in sc.descendants_for(sc.root):
                parent_name = sc.parent_for(name)
                self.__contexts[name] = self.__contexts[parent_name].new_child()

    @property
    def context(self) -> Context:
        return self._context

    def context_for(self, name: str) -> Context:
        """
        Context object for given state name.
        :param name: State name
        :return: Context object
        """
        return self.__contexts[name]

    def __send(self, name: str, **kwargs):
        """
        Add an internal event to interpreter queue.

        :param name: name of the event
        :param kwargs: additional event parameters
        """
        self._interpreter.queue(InternalEvent(name, **kwargs))

    def __active(self, name: str) -> bool:
        """
        Return True if given state name is active.

        :param name: name of a state
        :return: True if given state name is active.
        """
        return name in self._interpreter.configuration

    def __after(self, name: str, seconds: float) -> bool:
        """
        Return True if given state was entered more than *seconds* ago.

        :param name: name of a state
        :param seconds: elapsed time
        :return: True if given state was entered more than *seconds* ago.
        """
        return self._interpreter.time - seconds >= self.__entry_time[name]

    def __idle(self, name: str, seconds: float) -> bool:
        """
        Return True if given state was the target of a transition more than *seconds* ago.

        :param name: name of a state
        :param seconds: elapsed time
        :return: True if given state was the target of a transition more than *seconds* ago.
        """
        return self._interpreter.time - seconds >= self.__idle_time[name]

    def _evaluate_code(self, code: str, *, additional_context: Mapping=None, context: Context=None) -> bool:
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

        compiled_code = self.__evaluable_code.get(code, None)
        if compiled_code is None:
            compiled_code = self.__evaluable_code.setdefault(code, compile(code, '<string>', 'eval'))

        exposed_context = {
            'active': self.__active,
            'time': self._interpreter.time,
        }
        exposed_context.update(additional_context if additional_context is not None else {})

        try:
            return eval(compiled_code, exposed_context, context)  # type: ignore
        except Exception as e:
            raise CodeEvaluationError('The above exception occurred while evaluating:\n{}'.format(code)) from e

    def _execute_code(self, code: str, *, additional_context: Mapping=None, context: Context=None) -> None:
        """
        Execute given code using Python.

        :param code: code to execute
        :param additional_context: an optional additional context
        :param context: the current context for this piece of code
        """
        if not code:
            return
        if context is None:
            context = self._context

        compiled_code = self.__executable_code.get(code, None)
        if compiled_code is None:
            compiled_code = self.__executable_code.setdefault(code, compile(code, '<string>', 'exec'))

        exposed_context = {
            'active': self.__active,
            'time': self._interpreter.time,
            'send': self.__send,
        }
        exposed_context.update(additional_context if additional_context is not None else {})

        try:
            exec(compiled_code, exposed_context, context)  # type: ignore
        except Exception as e:
            raise CodeEvaluationError('The above exception occurred while executing:\n{}'.format(code)) from e

    def execute_statechart(self, statechart: Statechart) -> None:
        """
        Execute the initial code of a statechart.
        This method is called at the very beginning of the execution.

        :param statechart: statechart to consider
        """
        if statechart.preamble:
            self._execute_code(statechart.preamble,
                               context=self._context)

    def evaluate_guard(self, transition: Transition, event: Event) -> bool:
        """
        Evaluate the guard for given transition.

        :param transition: the considered transition
        :param event: instance of *Event* if any
        :return: truth value of *code*
        """
        additional_context = {
            'event': event,
            'after': partial(self.__after, transition.source),
            'idle': partial(self.__idle, transition.source),
        }
        return self._evaluate_code(getattr(transition, 'guard', None),
                                   context=self.__contexts[transition.source].new_child(),
                                   additional_context=additional_context)

    def execute_action(self, transition: Transition, event: Event) -> None:
        """
        Execute the action for given transition.
        This method is called for every transition that is processed, even those with no *action*.

        :param transition: the considered transition
        :param event: instance of *Event* if any
        """
        self.__idle_time[transition.source] = self._interpreter.time

        self._execute_code(getattr(transition, 'action', None),
                           context=self.__contexts[transition.source].new_child(),
                           additional_context={'event': event})

    def execute_onentry(self, state: StateMixin) -> None:
        """
        Execute the on entry action for given state.
        This method is called for every state that is entered, even those with no *on_entry*.

        :param state: the considered state
        """
        self.__entry_time[state.name] = self._interpreter.time
        self.__idle_time[state.name] = self._interpreter.time

        self._execute_code(getattr(state, 'on_entry', None),
                           context=self.__contexts[state.name])

    def execute_onexit(self, state: StateMixin) -> None:
        """
        Execute the on exit action for given state.
        This method is called for every state that is exited, even those with no *on_exit*.

        :param state: the considered state
        """
        self._execute_code(getattr(state, 'on_exit', None),
                           context=self.__contexts[state.name])

    def evaluate_preconditions(self, obj, event: Event=None) -> Iterator[str]:
        """
        Evaluate the preconditions for given object (either a *StateMixin* or a
        *Transition*) and return a list of conditions that are not satisfied.

        :param obj: the considered state or transition
        :param event: an optional *Event* instance, in the case of a transition
        :return: list of unsatisfied conditions
        """
        state_name = obj.source if isinstance(obj, Transition) else obj.name
        context = self.__contexts[state_name]

        additional_context = {'event': event} if isinstance(obj, Transition) else {}

        # Only needed if there is an invariant or a postcondition
        if len(getattr(obj, 'invariants', [])) > 0 or len(getattr(obj, 'postconditions', [])) > 0:
            self.__memory[id(obj)] = FrozenContext(context)

        return filter(
            lambda c: not self._evaluate_code(c, context=context, additional_context=additional_context),
            getattr(obj, 'preconditions', [])
        )

    def evaluate_invariants(self, obj, event: Event=None) -> Iterator[str]:
        """
        Evaluate the invariants for given object (either a *StateMixin* or a
        *Transition*) and return a list of conditions that are not satisfied.

        :param obj: the considered state or transition
        :param event: an optional *Event* instance, in the case of a transition
        :return: list of unsatisfied conditions
        """
        state_name = obj.source if isinstance(obj, Transition) else obj.name
        context = self.__contexts[state_name]

        additional_context = {'event': event} if isinstance(obj, Transition) else {}  # type: Dict[str, Any]
        additional_context.update({'__old__': self.__memory.get(id(obj), None)})

        return filter(
            lambda c: not self._evaluate_code(c, context=context, additional_context=additional_context),
            getattr(obj, 'invariants', [])
        )

    def evaluate_postconditions(self, obj, event: Event=None) -> Iterator[str]:
        """
        Evaluate the postconditions for given object (either a *StateMixin* or a
        *Transition*) and return a list of conditions that are not satisfied.

        :param obj: the considered state or transition
        :param event: an optional *Event* instance, in the case of a transition
        :return: list of unsatisfied conditions
        """
        state_name = obj.source if isinstance(obj, Transition) else obj.name
        context = self.__contexts[state_name]

        additional_context = {'event': event} if isinstance(obj, Transition) else {}  # type: Dict[str, Any]
        additional_context.update({'__old__': self.__memory.get(id(obj), None)})

        return filter(
            lambda c: not self._evaluate_code(c, context=context, additional_context=additional_context),
            getattr(obj, 'postconditions', [])
        )