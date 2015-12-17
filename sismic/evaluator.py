import copy
from .model import Event, Transition, StateMixin


class Evaluator:
    """
    Base class for any evaluator.

    An instance of this class defines what can be done with piece of codes
    contained in a statechart (condition, action, etc.).

    Notice that the execute_* methods are called at each step, even if there is no
    code to execute. This allows the evaluator to keep track of the states that are
    entered or exited, and of the transitions that are processed.

    :param interpreter: the interpreter that will use this evaluator,
        is expected to be an ``Interpreter`` instance
    :param initial_context: an optional dictionary to populate the context
    """

    def __init__(self, interpreter=None, initial_context: dict = None):
        self._context = initial_context if initial_context else {}
        self._interpreter = interpreter

    @property
    def context(self) -> dict:
        """
        The context of this evaluator. A context is a dict-like mapping between
        variables and values that is expected to be exposed when the code is evaluated.
        """
        return self._context

    def _evaluate_code(self, code: str, additional_context: dict = None) -> bool:
        """
        Generic method to evaluate a piece of code. This method is a fallback if one of
        the other evaluate_* methods is not overridden.

        :param code: code to evaluate
        :param additional_context: an optional additional context
        :return: truth value of *code*
        """
        raise NotImplementedError()

    def _execute_code(self, code: str, additional_context: dict = None):
        """
        Generic method to execute a piece of code. This method is a fallback if one
        of the other execute_* methods is not overridden.

        :param code: code to execute
        :param additional_context: an optional additional context
        """
        raise NotImplementedError()

    def evaluate_guard(self, transition: Transition, event: Event) -> bool:
        """
        Evaluate the guard for given transition.

        :param transition: the considered transition
        :param event: instance of ``Event`` if any
        :return: truth value of *code*
        """
        if transition.guard:
            return self._evaluate_code(transition.guard, {'event': event})

    def execute_action(self, transition: Transition, event: Event) -> bool:
        """
        Execute the action for given transition.
        This method is called for every transition that is processed, even those with no ``action``.

        :param transition: the considered transition
        :param event: instance of ``Event`` if any
        :return: truth value of *code*
        """
        if transition.action:
            return self._execute_code(transition.action, {'event': event})

    def execute_onentry(self, state: StateMixin):
        """
        Execute the on entry action for given state.
        This method is called for every state that is entered, even those with no ``on_entry``.

        :param state: the considered state
        """
        if getattr(state, 'on_entry', None):
            return self._execute_code(state.on_entry)

    def execute_onexit(self, state: StateMixin):
        """
        Execute the on exit action for given state.
        This method is called for every state that is exited, even those with no ``on_exit``.

        :param state: the considered state
        """
        if getattr(state, 'on_exit', None):
            return self._execute_code(state.on_exit)

    def evaluate_preconditions(self, obj, event: Event = None) -> list:
        """
        Evaluate the preconditions for given object (either a ``ActionStateMixin`` or a
        ``Transition``) and return a list of conditions that are not satisfied.
        :param obj: the considered state or transition
        :param event: an optional ``Event`` instance, in the case of a transition
        :return: list of unsatisfied conditions
        """
        event_d = {'event': event} if isinstance(obj, Transition) else None
        return filter(lambda c: not self._evaluate_code(c, event_d), getattr(obj, 'preconditions', []))

    def evaluate_invariants(self, obj, event: Event = None) -> list:
        """
        Evaluate the invariants for given object (either a ``ActionStateMixin`` or a
        ``Transition``) and return a list of conditions that are not satisfied.
        :param obj: the considered state or transition
        :param event: an optional ``Event`` instance, in the case of a transition
        :return: list of unsatisfied conditions
        """
        event_d = {'event': event} if isinstance(obj, Transition) else None
        return filter(lambda c: not self._evaluate_code(c, event_d), getattr(obj, 'invariants', []))

    def evaluate_postconditions(self, obj, event: Event = None) -> list:
        """
        Evaluate the postconditions for given object (either a ``ActionStateMixin`` or a
        ``Transition``) and return a list of conditions that are not satisfied.
        :param obj: the considered state or transition
        :param event: an optional ``Event`` instance, in the case of a transition
        :return: list of unsatisfied conditions
        """
        event_d = {'event': event} if isinstance(obj, Transition) else None
        return filter(lambda c: not self._evaluate_code(c, event_d), getattr(obj, 'postconditions', []))


class DummyEvaluator(Evaluator):
    """
    A dummy evaluator that does nothing and evaluates every condition to True.
    """

    @property
    def context(self):
        return dict()

    def _evaluate_code(self, code: str, additional_context: dict = None) -> bool:
        return True

    def _execute_code(self, code: str, additional_context: dict = None):
        return


class PythonEvaluator(Evaluator):
    """
    Evaluator that interprets Python code.

    Depending on the method that is called, the context can expose additional values:

     - On code execution
        - A ``send`` function that takes an ``Event`` (also exposed) and fires an internal event with.
        - If the code is related to a transition, the ``event`` that fires the transition is exposed.
     - On code evaluation
        - An ``active(name) -> bool`` Boolean function that takes a state name and return ``True`` if and only
          if this state is currently active, ie. it is in the active configuration of the ``Interpreter`` instance
          that makes use of this evaluator.
        - If the code is related to a transition, the ``event`` that fires the transition is exposed.
     - On guard evaluation
        - An ``after(sec) -> bool`` Boolean function that returns ``True`` if and only if the source state
          was entered more than *sec* seconds ago. The time is evaluated according to Interpreter's clock.
        - A ``idle(sec) -> bool`` Boolean function that returns ``True`` if and only if the source state
          did not fire a transition for more than *sec* ago. The time is evaluated according to Interpreter's clock.
     - On postcondition or invariant:
        - A variable ``__old__`` that has an attribute ``x`` for every ``x`` in the context when either the state
          was entered (if the condition involves a state) or the transition was processed (if the condition
          involves a transition). The value of ``__old__.x`` is a shallow copy of ``x`` at that time.

    Unless you override its entry in the context, the ``__builtins__`` of Python are automatically exposed.
    This implies you can use nearly everything from Python in your code.

    If an exception occurred while executing or evaluating a piece of code, it is propagated by the
    evaluator.

    :param interpreter: the interpreter that will use this evaluator,
        is expected to be an ``Interpreter`` instance
    :param initial_context: a dictionary that will be used as ``__locals__``
    """

    def __init__(self, interpreter=None, initial_context: dict = None):
        super().__init__(interpreter, initial_context)
        self._memory = {}  # Associate to each state or transition the context on state entry and transition action
        self._idle_time = {}  # Associate a timer to each state name (idle timer)
        self._entry_time = {}  # Associate a timer to each state name (entry timer)

    def _evaluate_code(self, code: str, additional_context: dict = None) -> bool:
        """
        Evaluate given code using Python.

        :param code: code to evaluate
        :param additional_context: an optional additional context
        :return: truth value of *code*
        """
        if not code:
            return True

        exposed_context = {'active': lambda s: s in self._interpreter.configuration}
        exposed_context.update(additional_context if additional_context else {})

        try:
            return eval(code, exposed_context, self._context)
        except Exception as e:
            raise type(e)('The above exception occurred while evaluating:\n{}'.format(code)) from e

    def _execute_code(self, code: str, additional_context: dict = None):
        """
        Execute given code using Python.

        :param code: code to execute
        :param additional_context: an optional additional context
        """
        if not code:
            return

        exposed_context = {'Event': Event,
                           'send': lambda ev: self._interpreter.send(ev, internal=True)}
        exposed_context.update(additional_context if additional_context else {})

        try:
            exec(code, exposed_context, self._context)
        except Exception as e:
            raise type(e)('The above exception occurred while executing:\n{}'.format(code)) from e

    class FrozenContext:
        """
        A shallow copy of a context. The keys of the underlying context are
        exposed as attributes.
        """

        def __init__(self, context: dict):
            self.__frozencontext = {k: copy.copy(v) for k, v in context.items()}

        def __getattr__(self, item):
            return self.__frozencontext[item]

    def evaluate_guard(self, transition: Transition, event: Event) -> bool:
        if transition.guard:
            context = {
                'event': event,
                'after': lambda i: self._interpreter.time - i >= self._entry_time[transition.from_state],
                'idle': lambda i: self._interpreter.time - i >= self._idle_time[transition.from_state]
            }
            return self._evaluate_code(transition.guard, context)

    def execute_onentry(self, state: StateMixin):
        # Set memory
        self._memory[id(state)] = PythonEvaluator.FrozenContext(self._context)

        # Set timer
        self._entry_time[state.name] = self._interpreter.time
        self._idle_time[state.name] = self._interpreter.time

        super().execute_onentry(state)

    def execute_action(self, transition: Transition, event: Event):
        # Set memory
        self._memory[id(transition)] = PythonEvaluator.FrozenContext(self._context)
        # Set timer
        self._idle_time[transition.from_state] = self._interpreter.time

        super().execute_action(transition, event)

    def evaluate_postconditions(self, obj, event: Event = None):
        context = {'event': event} if isinstance(obj, Transition) else {}
        context['__old__'] = (self._memory.get(id(obj), None))

        return filter(lambda c: not self._evaluate_code(c, context), getattr(obj, 'postconditions', []))

    def evaluate_invariants(self, obj, event: Event = None):
        context = {'event': event} if isinstance(obj, Transition) else {}
        context['__old__'] = (self._memory.get(id(obj), None))

        return filter(lambda c: not self._evaluate_code(c, context), getattr(obj, 'invariants', []))
