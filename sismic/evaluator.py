from .model import Event


class Evaluator:
    """
    Base class for any evaluator.

    An instance of this class defines what can be done with piece of codes
    contained in a statechart (condition, action, etc.).
    """

    @property
    def context(self) -> dict:
        """
        The context of this evaluator. A context is a dict-like mapping between
        variables and values that is expected to be exposed through
        ``evaluate_condition`` and ``execute_action``.
        """
        raise NotImplementedError()

    def evaluate_condition(self, condition: str, event: Event) -> bool:
        """
        Evaluate the condition of a guarded transition.

        :param condition: A one-line Boolean expression
        :param event: The event (if any) that could fire the transition.
        :return: True or False
        """
        raise NotImplementedError()

    def execute_action(self, action: str, event: Event=None) -> list:
        """
        Execute given action (multi-lines code) and return a (possibly empty) list
        of internal events to be considered by a statechart simulator.

        :param action: A (possibly multi-lined) code to execute.
        :param event: an ``Event`` instance in case of a transition action.
        :return: A possibly empty list of ``Event`` instances
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
        return []


class PythonEvaluator(Evaluator):
    """
    Evaluator that interprets Python code.

    An initial context can be provided, as a dictionary (will be used as ``__locals__``).
    Unless overridden, the context also exposes:

     - The ``__builtins__`` of Python,
     - The ``Event`` class and,
     - A ``send`` method that takes ``Event`` instances and send them to the statechart.

    When one of ``evaluate_condition`` or ``execute_action`` method is called with an event parameter,
    it is also exposed by the context through the key ``event``.

    :param initial_context: a dictionary that will be used as ``__locals__``
    """

    def __init__(self, initial_context: dict=None):
        self._context = {
            'Event': Event,
            'send': self._send_event
        }
        if initial_context:
            for key, value in initial_context.items():
                self._context[key] = value

        self._events = []  # List of events that need to be fired

    def _send_event(self, event: Event):
        self._events.append(event)

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
        :param event: The event (if any) that could fire the transition.
        :return: True or False
        """
        self._context['event'] = event
        try:
            return eval(condition, {}, self._context)
        except Exception as e:
            raise type(e)('The above exception occurred while evaluating:\n{}'.format(condition)) from e

    def execute_action(self, action: str, event: Event=None) -> list:
        """
        Execute given action (multi-lines code) and return a (possibly empty) list
        of internal events to be considered by a statechart simulator.

        :param action: A (possibly multi-lined) code to execute.
        :param event: an ``Event`` instance in case of a transition action.
        :return: A possibly empty list of ``Event`` instances
        """
        self._events = []  # Reset
        self._context['event'] = event

        try:
            exec(action, {}, self._context)
        except Exception as e:
            raise type(e)('The above exception occurred while executing:\n{}'.format(action)) from e
        return self._events


