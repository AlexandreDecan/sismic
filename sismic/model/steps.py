from .elements import Transition
from .events import Event

__all__ = ['MicroStep', 'MacroStep']


class MicroStep:
    """
    Create a micro step.

    A step consider *event*, takes a *transition* and results in a list
    of *entered_states* and a list of *exited_states*.
    Order in the two lists is REALLY important!

    :param event: Event or None in case of eventless transition
    :param transition: a *Transition* or None if no processed transition
    :param entered_states: possibly empty list of entered states
    :param exited_states: possibly empty list of exited states
    """

    def __init__(self, event: Event = None, transition: Transition = None,
                 entered_states: list = None, exited_states: list = None):
        self.event = event
        self.transition = transition if transition else []
        self.entered_states = entered_states if entered_states else []
        self.exited_states = exited_states if exited_states else []

    def __repr__(self):
        return 'MicroStep({}, {}, >{}, <{})'.format(self.event, self.transition, self.entered_states, self.exited_states)

    def __eq__(self, other):
        return (isinstance(other, MicroStep) and
                self.event == other.event and
                self.transition == other.transition and
                self.entered_states == other.entered_states and
                self.exited_states == other.exited_states)


class MacroStep:
    """
    A macro step is a list of micro steps.

    :param time: the time at which this step was executed
    :param steps: a list of *MicroStep* instances
    """

    def __init__(self, time: int, steps: list):
        self._time = time
        self._steps = steps

    @property
    def steps(self):
        """
        List of micro steps
        """
        return self._steps

    @property
    def time(self):
        """
        Time at which this step was executed.
        """
        return self._time

    @property
    def event(self) -> Event:
        """
        Event (or *None*) that were consumed.
        """
        for step in self._steps:
            if step.event:
                return step.event
        return None

    @property
    def transitions(self) -> list:
        """
        A (possibly empty) list of transitions that were triggered.
        """
        return [step.transition for step in self._steps if step.transition]

    @property
    def entered_states(self) -> list:
        """
        List of the states names that were entered.
        """
        states = []
        for step in self._steps:
            states += step.entered_states
        return states

    @property
    def exited_states(self) -> list:
        """
        List of the states names that were exited.
        """
        states = []
        for step in self._steps:
            states += step.exited_states
        return states

    def __repr__(self):
        return 'MacroStep@{}({}, {}, >{}, <{})'.format(round(self.time, 3), self.event, self.transitions,
                                                       self.entered_states, self.exited_states)

    def __eq__(self, other):
        return (isinstance(other, MacroStep) and
                self.time == other.time and
                self.steps == other.steps)