from .model import Event


class Evaluator:
    """
    Base class for any Evaluator.

    An instance of this class defines what can be done with piece of codes
    contained in a statechart (condition, action, etc.).
    """

    @property
    def context(self) -> dict:
        """
        Return the context of this Evaluator. A context is a mapping between
        variables and values that is expected to be exposed through
        ``evaluate_condition`` and ``execute_action``.

        :return: A dict-like mapping.
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

    An initial context can be provided, as a dictionary (will be used as __locals__).
    This context will be updated with __builtins__, Event and with send(), a function that
    receive an Event instance that will be fired on the state machine.

    When evaluate_condition or execute_action is called with an Event, this event
    will be added to the context, as {'event': event_instance}.
    """

    def __init__(self, initial_context: dict=None):
        """
        :param initial_context: a dictionary that will be used as __locals__
        """
        self._context = {
            'Event': Event,
            'send': self._send_event
        }
        if initial_context:
            self._context.update(initial_context)

        self._events = []  # List of events that need to be fired

    def _send_event(self, event: Event):
        self._events.append(event)

    @property
    def context(self) -> dict:
        return self._context

    def evaluate_condition(self, condition: str, event: Event=None) -> bool:
        """
        Evaluate given condition using ``eval()``.
        It is expected that condition is a one-line expression whose value is a Boolean.

        :param condition: one-line condition whose value is a Boolean
        :param event: Event instance (if any) on the transition
        """
        self._context['event'] = event
        return eval(condition, {'__builtins__': __builtins__}, self._context)

    def execute_action(self, action: str, event: Event=None) -> list:
        """
        Execute given action using ``exec()`` and thus accepts action defining on multiple
        lines and using statements.
        Return a list of Event's to be considered by the state machine.

        :param action: code (as string) to execute_once
        :param event: Event instance (in case of transition action).
        :return: a list of Event instances
        """
        self._events = []  # Reset
        self._context['event'] = event
        exec(action, {'__builtins__': __builtins__}, self._context)
        return self._events

