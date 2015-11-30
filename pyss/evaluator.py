from pyss.statemachine import Event


class Evaluator:
    """
    Base class for any Evaluator.

    An instance of this class defines what can be done with piece of codes
    contained in a state machine (condition, action, etc.).
    """
    def evaluate_condition(self, condition: str, event: Event) -> bool:
        """
        Evaluate given condition and return True or False.
        :param condition: code (as string) to evaluate
        :param event: event (if any) for this transition
        :return: True or False
        """
        raise NotImplementedError()

    def execute_action(self, action: str, event: Event=None) -> list:
        """
        Execute given action and return a (possibly empty) list of Event to fire.
        :param action: code (as string) to execute
        :param event: event (if action is a transition action)
        :return: list of events to fire.
        """
        raise NotImplementedError()


class DummyEvaluator(Evaluator):
    """
    A dummy evaluator that does nothing and evaluates every condition to True.
    """

    def evaluate_condition(self, condition: str, event: Event):
        return True

    def execute_action(self, action: str, event: Event=None):
        return []


class PythonEvaluator(Evaluator):
    """
    Evaluator that interprets Python code.

    An initial context can be provided, as a dictionary (will be used as __locals__).
    This context will be updated with __builtins__, Event and with fire_event, a function that
    receive an Event instance that will be fired on the state machine.

    When evaluate_condition or execute_action is called with an Event, this event
    will be added to the context, as {'event': event_instance}.
    """

    def __init__(self, initial_context: dict=None):
        """
        :param initial_context: a dictionary that will be used as __locals__
        """
        self.context = {
            'Event': Event,
            'fire_event': self._fire_event
        }
        if initial_context:
            self.context.update(initial_context)

        self.events = []  # List of events that need to be fired

    def _fire_event(self, event: Event):
        self.events.append(event)

    def evaluate_condition(self, condition: str, event: Event=None):
        """
        Evaluate given condition using `eval()`.
        It is expected that condition is a one-line expression whose value is a Boolean.
        :param condition: one-line condition whose value is a Boolean
        :param event: Event instance (if any) on the transition
        """
        self.context['event'] = event
        return eval(condition, {'__builtins__': __builtins__}, self.context)

    def execute_action(self, action: str, event: Event=None) -> list:
        """
        Execute given action using `exec()` and thus accepts action defining on multiple
        lines and using statements.
        Return a list of Event's to be considered by the state machine.
        :param action: code (as string) to execute
        :param event: Event instance (in case of transition action).
        :return: a list of Event instances
        """
        self.events = []
        self.context['event'] = event
        exec(action, {'__builtins__': __builtins__}, self.context)
        return self.events

