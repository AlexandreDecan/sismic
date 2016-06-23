from .elements import Transition
from .events import Event

from typing import List


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
    :param sent_events: a possibly empty list of events that are sent during the step
    """

    __slots__ = ['event', 'transition', 'entered_states', 'exited_states', 'sent_events']

    def __init__(self, event: Event=None, transition: Transition=None, entered_states: List[str]=None,
                 exited_states: List[str]=None, sent_events: List[Event]=None) -> None:
        self.event = event
        self.transition = transition
        self.entered_states = entered_states if entered_states else []  # type: List[str]
        self.exited_states = exited_states if exited_states else []  # type: List[str]
        self.sent_events = sent_events if sent_events else []  # type: List[Event]

    def __repr__(self):
        return 'MicroStep({}, {}, >{}, <{})'.format(self.event, self.transition,
                                                    self.entered_states, self.exited_states)


class MacroStep:
    """
    A macro step is a list of micro steps.

    :param time: the time at which this step was executed
    :param steps: a list of *MicroStep* instances
    """

    def __init__(self, time: float, steps: List[MicroStep]) -> None:
        self._time = time
        self._steps = steps

    __slots__ = ['_time', '_steps']

    @property
    def steps(self) -> List[MicroStep]:
        """
        List of micro steps
        """
        return self._steps

    @property
    def time(self) -> float:
        """
        Time at which this step was executed.
        """
        return self._time

    @property
    def event(self) -> Event:
        """
        Event (or *None*) that was consumed.
        """
        for step in self._steps:
            if step.event:
                return step.event
        return None

    @property
    def transitions(self) -> List[Transition]:
        """
        A (possibly empty) list of transitions that were triggered.
        """
        return [step.transition for step in self._steps if step.transition]

    @property
    def entered_states(self) -> List[str]:
        """
        List of the states names that were entered.
        """
        states = []  # type: List[str]
        for step in self._steps:
            states += step.entered_states
        return states

    @property
    def exited_states(self) -> List[str]:
        """
        List of the states names that were exited.
        """
        states = []  # type: List[str]
        for step in self._steps:
            states += step.exited_states
        return states

    @property
    def sent_events(self) -> List[Event]:
        """
        List of events that were sent during this step.
        """
        events = []
        for step in self._steps:
            for event in step.sent_events:
                events.append(event)
        return events

    def __repr__(self):
        return 'MacroStep@{}({}, {}, >{}, <{})'.format(round(self.time, 3), self.event, self.transitions,
                                                       self.entered_states, self.exited_states)
