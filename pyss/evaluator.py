from .model import Event


class Evaluator:
    """
    Base class for any evaluator.

    An instance of this class defines what can be done with piece of codes
    contained in a statechart (condition, action, etc.).
    """

    @property
    def context(self):
        """
        Return the context of this evaluator. A context is a mapping between
        variables and values that is expected to be exposed through
        ``evaluate_condition`` and ``execute_action``.

        :return dict: A dict-like mapping.
        """
        raise NotImplementedError()

    def evaluate_condition(self, condition, event=None):
        """
        Evaluate the condition of a guarded transition.

        :param str condition: A one-line Boolean expression
        :param Event event: The event (if any) that could fire the transition.
        :return bool: The result of the evaluation of the condition
        """
        raise NotImplementedError()

    def execute_action(self, action, event=None):
        """
        Execute given action (multi-lines code) and return a (possibly empty) list
        of internal events to be considered by a statechart simulator.

        :param str action: A (possibly multi-lined) code to execute.
        :param Event event: an ``Event`` instance in case of a transition action.
        :return list of Event: A (possibly empty) list of events sent while the execution
        """
        raise NotImplementedError()


class DummyEvaluator(Evaluator):
    """
    A dummy evaluator that does nothing and evaluates every condition to True.
    """

    @property
    def context(self):
        return dict()

    def evaluate_condition(self, condition, event=None):
        return True

    def execute_action(self, action, event=None):
        return []


class PythonEvaluator(Evaluator):
    """
    Evaluator that interprets Python code.

    An initial context can be provided, as a dictionary (will be used as ``__locals__``).
    This context will be updated with ``__builtins__``, Event and with ``send()``, a function that
    receive an ``Event`` instance that will be fired on the state machine.

    When ``evaluate_condition`` or ``execute_action`` is called with an Event, this event
    will be added to the context, as ``{'event': event_instance}``.
    """

    def __init__(self, initial_context=None):
        """
        :param dict initial_context: a dictionary that will be used as __locals__
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
    def context(self):
        """
        The context of this evaluator.

        :return dict: a mapping between variable name and value (a dict-like structure).
        """
        return self._context

    def evaluate_condition(self, condition, event=None):
        self._context['event'] = event
        return eval(condition, {'__builtins__': __builtins__}, self._context)

    def execute_action(self, action, event=None):
        self._events = []  # Reset
        self._context['event'] = event
        exec(action, {'__builtins__': __builtins__}, self._context)
        return self._events

