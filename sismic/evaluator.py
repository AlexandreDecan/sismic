from .model import Event, Transition, StateMixin


class Evaluator:
    """
    Base class for any evaluator.

    An instance of this class defines what can be done with piece of codes
    contained in a statechart (condition, action, etc.).

    :param interpreter: the interpreter that will use this evaluator,
        is expected to be an ``Interpreter`` instance
    :param initial_context: an optional dictionary to populate the context
    """
    def __init__(self, interpreter=None, initial_context: dict=None):
        self._context = initial_context if initial_context else {}
        self._interpreter = interpreter

    @property
    def context(self) -> dict:
        """
        The context of this evaluator. A context is a dict-like mapping between
        variables and values that is expected to be exposed when the code is evaluated.
        """
        return self._context

    def _evaluate_code(self, obj, code: str, event: Event=None) -> bool:
        """
        Generic method to evaluate a piece of code. This method is a fallback if one of
        the ev_* methods is not overridden.

        :param obj: involved object (``Transition`` or ``StateMixin`` instance)
        :param code: code to evaluate
        :param event: instance of ``Event`` if any
        :return: truth value of *code*
        """
        raise NotImplementedError()

    def _execute_code(self, obj, code: str, event: Event=None):
        """
        Generic method to execute a piece of code. This method is a fallback if one
        of the ex_* methods is not overridden.

        :param obj: involved object (``Transition`` or ``StateMixin`` instance)
        :param code: code to execute
        :param event: instance of ``Event``, if any
        """
        raise NotImplementedError()

    def ev_transition_guard(self, obj: Transition, code: str, event: Event) -> bool:
        """
        Evaluate the guard (*code*) for given transition *obj*.

        :param obj: instance of ``Transition``
        :param code: code to evaluate
        :param event: instance of ``Event`` if any
        :return: truth value of *code*
        """
        return self._evaluate_code(obj, code, event)

    def ev_transition_precondition(self, obj: Transition, code: str, event: Event) -> bool:
        """
        Evaluate the precondition (*code*) for given transition *obj*.

        :param obj: instance of ``Transition``
        :param code: code to evaluate
        :param event: instance of ``Event`` if any
        :return: truth value of *code*
        """
        return self._evaluate_code(obj, code, event)

    def ev_tansition_invariant(self, obj: Transition, code: str, event: Event) -> bool:
        """
        Evaluate the invariant (*code*) for given transition *obj*.

        :param obj: instance of ``Transition``
        :param code: code to evaluate
        :param event: instance of ``Event`` if any
        :return: truth value of *code*
        """
        return self._evaluate_code(obj, code, event)

    def ev_transition_postcondition(self, obj: Transition, code: str, event: Event) -> bool:
        """
        Evaluate the postcondition (*code*) for given transition *obj*.

        :param obj: instance of ``Transition``
        :param code: code to evaluate
        :param event: instance of ``Event`` if any
        :return: truth value of *code*
        """
        return self._evaluate_code(obj, code, event)

    def ex_transition_action(self, obj: Transition, code: str, event: Event) -> bool:
        """
        Execute the action (*code*) for given transition *obj*.

        :param obj: instance of ``Transition``
        :param code: code to evaluate
        :param event: instance of ``Event`` if any
        :return: truth value of *code*
        """
        return self._execute_code(obj, code, event)

    def ex_state_onentry(self, obj: StateMixin, code: str) -> bool:
        """
        Execute the on entry action (*code*) for given state *obj*.

        :param obj: instance of ``StateMixin``
        :param code: code to evaluate
        """
        return self._execute_code(obj, code)

    def ex_state_onexit(self, obj: StateMixin, code: str) -> bool:
        """
        Execute the on exit action (*code*) for given state *obj*.

        :param obj: instance of ``StateMixin``
        :param code: code to evaluate
        """
        return self._execute_code(obj, code)

    def ev_state_precondition(self, obj: StateMixin, code: str) -> bool:
        """
        Evaluate the precondition (*code*) for given state *obj*.

        :param obj: instance of ``StateMixin``
        :param code: code to evaluate
        :return: truth value of *code*
        """
        return self._evaluate_code(obj, code)

    def ev_state_invariant(self, obj: StateMixin, code: str) -> bool:
        """
        Evaluate the invariant (*code*) for given state *obj*.

        :param obj: instance of ``Transition``
        :param code: code to evaluate
        :return: truth value of *code*
        """
        return self._evaluate_code(obj, code)

    def ev_state_postcondition(self, obj: StateMixin, code: str) -> bool:
        """
        Evaluate the postcondition (*code*) for given state *obj*.

        :param obj: instance of ``Transition``
        :param code: code to evaluate
        :return: truth value of *code*
        """
        return self._evaluate_code(obj, code)


class DummyEvaluator(Evaluator):
    """
    A dummy evaluator that does nothing and evaluates every condition to True.
    """

    @property
    def context(self):
        return dict()

    def _evaluate_code(self, obj, code: str, event: Event=None):
        """
        Return True.
        """
        return True

    def _execute_code(self, obj, code: str, event: Event=None):
        """
        Do nothing
        """
        pass


class PythonEvaluator(Evaluator):
    """
    Evaluator that interprets Python code.

    Depending on the method that is called, the context can expose additional values:

     - On code execution
        - A ``send`` function that takes an ``Event`` (also exposed) and fires an internal event with.
        - If the code is related to a transition, the ``event`` that fires the transition is exposed.
     - On code evaluation
        - An ``active(name) --> bool`` Boolean function that takes a state name and return ``True`` if and only
          if this state is currently active, ie. it is in the active configuration of the ``Interpreter`` instance
          that makes use of this evaluator.
        - If the code is related to a transition, the ``event`` that fires the transition is exposed.

    Unless you override its entry in the context, the ``__builtins__`` of Python are automatically exposed.
    This implies you can use nearly everything from Python in your code.

    If an exception occurred while executing or evaluating a piece of code, it is propagated by the
    evaluator.

    :param interpreter: the interpreter that will use this evaluator,
        is expected to be an ``Interpreter`` instance
    :param initial_context: a dictionary that will be used as ``__locals__``
    """

    def __init__(self, interpreter=None, initial_context: dict=None):
        super().__init__(interpreter, initial_context)

        # Extra context
        self._ev_context = {'active': lambda s: s in interpreter.configuration}
        self._ex_context = {'Event': Event,
                            'send': lambda e: interpreter.send(e, internal=True)}

    def _evaluate_code(self, obj, code: str, event: Event=None, additional_context: dict=None) -> bool:
        """
        Evaluate given code using Python.

        :param obj: involved object (``Transition`` or ``StateMixin`` instance)
        :param code: code to evaluate
        :param event: instance of ``Event`` if any
        :param additional_context: an optional additional context
        :return: truth value of *code*
        """
        global_context = {'event': event} if event else {}
        global_context.update(self._ev_context)
        if additional_context:
            global_context.update(additional_context)

        try:
            return eval(code, global_context, self._context)
        except Exception as e:
            raise type(e)('The above exception occurred in {} while evaluating:\n{}'.format(obj, code)) from e

    def _execute_code(self, obj, code: str, event: Event=None, additional_context: dict=None):
        """
        Execute given code using Python.

        :param obj: involved object (``Transition`` or ``StateMixin`` instance)
        :param code: code to execute
        :param event: instance of ``Event``, if any
        :param additional_context: an optional additional context
        """
        global_context = {'event': event} if event else {}
        global_context.update(self._ex_context)
        if additional_context:
            global_context.update(additional_context)

        try:
            exec(code, global_context, self._context)
        except Exception as e:
            raise type(e)('The above exception occurred in {} while executing:\n{}'.format(obj, code)) from e


