from functools import partial

import copy
from sismic.code import Evaluator
from sismic.model import Event, InternalEvent, Transition, StateMixin
from sismic.exceptions import CodeEvaluationError

__all__ = ['PythonEvaluator']


class FrozenContext:
    """
    A shallow copy of a context. The keys of the underlying context are
    exposed as attributes.
    """

    def __init__(self, context: dict):
        self.__frozencontext = {k: copy.copy(v) for k, v in context.items()}

    def __getattr__(self, item):
        return self.__frozencontext[item]


class PythonEvaluator(Evaluator):
    """
    Evaluator that interprets Python code.

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

    Unless you override its entry in the context, the *__builtins__* of Python are automatically exposed.
    This implies you can use nearly everything from Python in your code.

    If an exception occurred while executing or evaluating a piece of code, it is propagated by the
    evaluator.

    :param interpreter: the interpreter that will use this evaluator,
        is expected to be an *Interpreter* instance
    :param initial_context: a dictionary that will be used as *__locals__*
    """

    def __init__(self, interpreter=None, initial_context: dict = None):
        super().__init__(interpreter, initial_context)
        self._memory = {}  # Associate to each state or transition the context on state entry and transition action
        self._idle_time = {}  # Associate a timer to each state name (idle timer)
        self._entry_time = {}  # Associate a timer to each state name (entry timer)

    def __set_memory(self, obj):
        """
        Freeze current context and associate it to given *obj*.

        :param obj: *StateMixin* or *Transition*
        """
        self._memory[id(obj)] = FrozenContext(self._context)

    def __get_memory(self, obj):
        """
        Return frozen context for given *obj*.

        :param obj: *StateMixin* or *Transition*
        :return: an instance of *FrozenContext*
        """
        return self._memory.get(id(obj), {})

    def __send(self, name: str, **kwargs):
        """
        Add an internal event to interpreter queue.

        :param name: name of the event
        :param kwargs: additional event parameters
        """
        self._interpreter.queue(InternalEvent(name, **kwargs))

    def __active(self, name: str):
        """
        Return True if given state name is active.
        :param name: name of a state
        """
        return name in self._interpreter.configuration

    def __after(self, name: str, seconds: float):
        """
        Return True if given state was entered more than *seconds* ago.
        :param name:
        :param seconds:
        :return:
        """
        return self._interpreter.time - seconds >= self._entry_time[name]

    def __idle(self, name: str, seconds: float):
        """
        Return True if given state was the target of a transition more than *seconds* ago.
        :param name:
        :param seconds:
        :return:
        """
        return self._interpreter.time - seconds >= self._idle_time[name]

    def _evaluate_code(self, code: str, additional_context: dict = None) -> bool:
        """
        Evaluate given code using Python.

        :param code: code to evaluate
        :param additional_context: an optional additional context
        :return: truth value of *code*
        """
        if not code:
            return True

        exposed_context = {
            'active': self.__active,
            'time': self._interpreter.time,
        }
        exposed_context.update(additional_context if additional_context else {})

        try:
            return eval(code, exposed_context, self._context)
        except Exception as e:
            raise CodeEvaluationError('The above exception occurred while evaluating:\n{}'.format(code)) from e

    def _execute_code(self, code: str, additional_context: dict = None):
        """
        Execute given code using Python.

        :param code: code to execute
        :param additional_context: an optional additional context
        """
        if not code:
            return

        exposed_context = {
            'active': self.__active,
            'time': self._interpreter.time,
            'send': self.__send,
        }
        exposed_context.update(additional_context if additional_context else {})

        try:
            exec(code, exposed_context, self._context)
        except Exception as e:
            raise CodeEvaluationError('The above exception occurred while executing:\n{}'.format(code)) from e

    def evaluate_guard(self, transition: Transition, event: Event) -> bool:
        if transition.guard:
            context = {
                'event': event,
                'after': partial(self.__after, transition.source),
                'idle': partial(self.__idle, transition.source),
            }
            return self._evaluate_code(transition.guard, context)

    def execute_onentry(self, state: StateMixin):
        # Set memory
        self.__set_memory(state)

        # Set timer
        self._entry_time[state.name] = self._interpreter.time
        self._idle_time[state.name] = self._interpreter.time

        super().execute_onentry(state)

    def execute_action(self, transition: Transition, event: Event):
        # Set memory
        self.__set_memory(transition)

        # Set timer
        self._idle_time[transition.source] = self._interpreter.time

        super().execute_action(transition, event)

    def evaluate_postconditions(self, obj, event: Event = None):
        context = {'event': event} if isinstance(obj, Transition) else {}
        context['__old__'] = self.__get_memory(obj)

        return filter(lambda c: not self._evaluate_code(c, context), getattr(obj, 'postconditions', []))

    def evaluate_invariants(self, obj, event: Event = None):
        context = {'event': event} if isinstance(obj, Transition) else {}
        context['__old__'] = self.__get_memory(obj)

        return filter(lambda c: not self._evaluate_code(c, context), getattr(obj, 'invariants', []))
