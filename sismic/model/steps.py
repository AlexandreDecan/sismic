from .elements import Transition
from .events import Event

__all__ = ["MacroStep", "MicroStep"]


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

    __slots__ = ["entered_states", "event", "exited_states", "sent_events", "transition"]

    def __init__(
        self,
        event: Event | None = None,
        transition: Transition | None = None,
        entered_states: list[str] | None = None,
        exited_states: list[str] | None = None,
        sent_events: list[Event] | None = None,
    ) -> None:
        self.event = event
        self.transition = transition
        self.entered_states: list[str] = entered_states if entered_states else []
        self.exited_states: list[str] = exited_states if exited_states else []
        self.sent_events: list[Event] = sent_events if sent_events else []

    def __repr__(self):
        params = []
        if self.event:
            params.append(f"event={self.event!r}")
        if self.transition:
            params.append(f"transition={self.transition!r}")
        if self.entered_states:
            params.append(f"entered_states={self.entered_states!r}")
        if self.exited_states:
            params.append(f"exited_states={self.exited_states!r}")
        if self.sent_events:
            params.append(f"sent_events={self.sent_events!r}")
        return "{}({})".format(self.__class__.__name__, ", ".join(params))


class MacroStep:
    """
    A macro step is a list of micro steps.

    :param time: the time at which this step was executed
    :param steps: a list of *MicroStep* instances
    """

    def __init__(self, time: float, steps: list[MicroStep]) -> None:
        self._time = time
        self._steps = steps

    __slots__ = ["_steps", "_time"]

    @property
    def steps(self) -> list[MicroStep]:
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
    def event(self) -> Event | None:
        """
        Event (or *None*) that was consumed.
        """
        for step in self._steps:
            if step.event:
                return step.event
        return None

    @property
    def transitions(self) -> list[Transition]:
        """
        A (possibly empty) list of transitions that were triggered.
        """
        return [step.transition for step in self._steps if step.transition]

    @property
    def entered_states(self) -> list[str]:
        """
        List of the states names that were entered.
        """
        return [state for step in self._steps for state in step.entered_states]

    @property
    def exited_states(self) -> list[str]:
        """
        List of the states names that were exited.
        """
        return [state for step in self._steps for state in step.exited_states]

    @property
    def sent_events(self) -> list[Event]:
        """
        List of events that were sent during this step.
        """
        return [event for step in self._steps for event in step.sent_events]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.time!r}, {self._steps!r})"

    def __str__(self):
        return f"Step@{round(self.time, 3)}({self.event}, {self.transitions}, >{self.entered_states}, <{self.exited_states})"
