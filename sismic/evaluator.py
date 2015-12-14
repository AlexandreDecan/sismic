from .model import Event


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
        variables and values that is expected to be exposed through
        ``evaluate_condition`` and ``execute_action``.
        """
        return self._context

    def evaluate_condition(self, condition: str, event: Event) -> bool:
        """
        Evaluate the condition of a guarded transition.

        :param condition: A one-line Boolean expression
        :param event: The event (if any) that could fire the transition.
        :return: True or False
        """
        raise NotImplementedError()

    def execute_action(self, action: str, event: Event=None):
        """
        Execute given action (multi-lines code).

        :param action: A (possibly multi-lined) code to execute.
        :param event: an ``Event`` instance in case of a transition action.
        """
        raise NotImplementedError()


class DummyEvaluator(Evaluator):
    """
    A dummy evaluator that does nothing and evaluates every condition to True.
    """

    @property
    def context(self):
        return dict()

    def evaluate_condition(self, condition: str, event: Event):
        return True

    def execute_action(self, action: str, event: Event=None):
        pass


class PythonEvaluator(Evaluator):
    """
    Evaluator that interprets Python code.

    When one of ``evaluate_condition`` or ``execute_action`` method is called with an event parameter,
    it is also exposed by the context through the key ``event``.

    The context always contains the following entries:

     - send: a function that takes an Event, used to generate internal events
     - Event: class Event
     - active: a Boolean function that takes a state name and return True iff state is active

    :param interpreter: the interpreter that will use this evaluator,
        is expected to be an ``Interpreter`` instance
    :param initial_context: a dictionary that will be used as ``__locals__``
    """

    def __init__(self, interpreter=None, initial_context: dict=None):
        super().__init__(interpreter, initial_context)

        # Add Event to the context
        self._context['Event'] = Event

        # Add send to the context
        self._context['send'] = lambda e: interpreter.send(e, internal=True)

        # Add active to the context
        self._context['active'] = lambda s: s in interpreter.configuration

    @property
    def context(self) -> dict:
        """
        The context of this evaluator. A context is a dict-like mapping between
        variables and values that is expected to be exposed through
        ``evaluate_condition`` and ``execute_action``.
        """
        return self._context

    def evaluate_condition(self, condition: str, event: Event=None) -> bool:
        """
        Evaluate the condition of a guarded transition.

        :param condition: A one-line Boolean expression
        :param event: The event (if any) that could fire the transition. This event is exposed to the code.
        :return: True or False
        """
        self._context['event'] = event

        try:
            return eval(condition, {}, self._context)
        except Exception as e:
            raise type(e)('The above exception occurred while evaluating:\n{}'.format(condition)) from e

    def execute_action(self, action: str, event: Event=None):
        """
        Execute given action (multi-lines code).

        :param action: A (possibly multi-lined) code to execute.
        :param event: an ``Event`` instance in case of a transition action. This event is exposed to the code.
        """
        self._context['event'] = event

        try:
            exec(action, {}, self._context)
        except Exception as e:
            raise type(e)('The above exception occurred while executing:\n{}'.format(action)) from e


